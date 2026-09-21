#!/usr/bin/env python3
"""
Metrics Storage and Retrieval System for DMLogn8n Monitoring
Handles time-series data storage, aggregation, and querying
"""

import asyncio
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import redis
import aiofiles
import pandas as pd
import numpy as np
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

@dataclass
class MetricPoint:
    """Individual metric data point"""
    timestamp: datetime
    metric_name: str
    value: Union[float, int, str]
    labels: Dict[str, str]
    tags: Dict[str, str]

@dataclass
class MetricSeries:
    """Time series of metric points"""
    metric_name: str
    labels: Dict[str, str]
    points: List[MetricPoint]

class MetricsStorage:
    """Handles storage and retrieval of time-series metrics"""

    def __init__(self,
                 sqlite_path: str = "metrics.db",
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 redis_db: int = 0):
        self.sqlite_path = sqlite_path
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.redis_client = None
        self.init_databases()

    def init_databases(self):
        """Initialize SQLite and Redis databases"""
        self._init_sqlite()
        self._init_redis()

    def _init_sqlite(self):
        """Initialize SQLite database for long-term storage"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()

            # Create metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    labels TEXT,
                    tags TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp ON metrics(metric_name, timestamp)')

            # Create aggregated metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics_aggregated (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    aggregation_type TEXT NOT NULL,
                    time_bucket DATETIME NOT NULL,
                    value REAL NOT NULL,
                    count INTEGER NOT NULL,
                    min_value REAL,
                    max_value REAL,
                    sum_value REAL,
                    labels TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_agg_name_bucket ON metrics_aggregated(metric_name, time_bucket)')

            # Create alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    rule_name TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    current_value REAL,
                    threshold_value REAL,
                    description TEXT,
                    labels TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    resolved_at DATETIME,
                    acknowledged_at DATETIME,
                    acknowledged_by TEXT
                )
            ''')

            conn.commit()
            conn.close()
            logger.info("SQLite metrics database initialized")

        except Exception as e:
            logger.error(f"Error initializing SQLite database: {e}")
            raise

    def _init_redis(self):
        """Initialize Redis client for caching and real-time data"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Running without cache.")
            self.redis_client = None

    async def store_metric(self, metric_name: str, value: Union[float, int, str],
                          labels: Optional[Dict[str, str]] = None,
                          tags: Optional[Dict[str, str]] = None):
        """Store a single metric point"""
        try:
            timestamp = datetime.now()

            # Store in SQLite
            await self._store_metric_sqlite(timestamp, metric_name, value, labels, tags)

            # Store in Redis cache if available
            if self.redis_client:
                await self._store_metric_redis(timestamp, metric_name, value, labels, tags)

        except Exception as e:
            logger.error(f"Error storing metric {metric_name}: {e}")

    async def _store_metric_sqlite(self, timestamp: datetime, metric_name: str,
                                  value: Union[float, int, str],
                                  labels: Optional[Dict[str, str]],
                                  tags: Optional[Dict[str, str]]):
        """Store metric in SQLite database"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO metrics (timestamp, metric_name, value, labels, tags)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            timestamp,
            metric_name,
            float(value) if isinstance(value, (int, float)) else 0,
            json.dumps(labels) if labels else None,
            json.dumps(tags) if tags else None
        ))

        conn.commit()
        conn.close()

    async def _store_metric_redis(self, timestamp: datetime, metric_name: str,
                                 value: Union[float, int, str],
                                 labels: Optional[Dict[str, str]],
                                 tags: Optional[Dict[str, str]]):
        """Store metric in Redis cache"""
        try:
            # Create Redis key
            label_str = "_".join(f"{k}:{v}" for k, v in sorted(labels.items())) if labels else ""
            redis_key = f"metric:{metric_name}:{label_str}"

            # Store as a sorted set with timestamp as score
            score = timestamp.timestamp()
            self.redis_client.zadd(redis_key, {str(value): score})

            # Keep only last 1000 points per series
            self.redis_client.zremrangebyrank(redis_key, 0, -1001)

            # Set expiration (24 hours)
            self.redis_client.expire(redis_key, 86400)

            # Store latest value for quick access
            latest_key = f"latest:{metric_name}"
            latest_data = {
                "value": str(value),
                "timestamp": timestamp.isoformat(),
                "labels": labels or {}
            }
            self.redis_client.set(latest_key, json.dumps(latest_data), ex=3600)

        except Exception as e:
            logger.error(f"Error storing metric in Redis: {e}")

    async def store_metrics_batch(self, metrics: List[MetricPoint]):
        """Store multiple metrics in a batch"""
        try:
            # Store in SQLite batch
            await self._store_metrics_batch_sqlite(metrics)

            # Store in Redis batch if available
            if self.redis_client:
                await self._store_metrics_batch_redis(metrics)

        except Exception as e:
            logger.error(f"Error storing metrics batch: {e}")

    async def _store_metrics_batch_sqlite(self, metrics: List[MetricPoint]):
        """Store metrics batch in SQLite"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()

        data = []
        for metric in metrics:
            data.append((
                metric.timestamp,
                metric.metric_name,
                float(metric.value) if isinstance(metric.value, (int, float)) else 0,
                json.dumps(metric.labels) if metric.labels else None,
                json.dumps(metric.tags) if metric.tags else None
            ))

        cursor.executemany('''
            INSERT INTO metrics (timestamp, metric_name, value, labels, tags)
            VALUES (?, ?, ?, ?, ?)
        ''', data)

        conn.commit()
        conn.close()

    async def _store_metrics_batch_redis(self, metrics: List[MetricPoint]):
        """Store metrics batch in Redis"""
        try:
            pipe = self.redis_client.pipeline()

            for metric in metrics:
                label_str = "_".join(f"{k}:{v}" for k, v in sorted(metric.labels.items())) if metric.labels else ""
                redis_key = f"metric:{metric.metric_name}:{label_str}"

                score = metric.timestamp.timestamp()
                pipe.zadd(redis_key, {str(metric.value): score})

                # Keep only last 1000 points
                pipe.zremrangebyrank(redis_key, 0, -1001)
                pipe.expire(redis_key, 86400)

            await pipe.execute()

        except Exception as e:
            logger.error(f"Error storing metrics batch in Redis: {e}")

    async def get_metrics(self, metric_name: str,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         labels: Optional[Dict[str, str]] = None,
                         limit: int = 1000) -> List[MetricPoint]:
        """Retrieve metrics for a specific metric name"""
        try:
            # Try Redis first for recent data
            if self.redis_client and (not start_time or start_time > datetime.now() - timedelta(hours=24)):
                redis_metrics = await self._get_metrics_redis(metric_name, start_time, end_time, labels, limit)
                if redis_metrics:
                    return redis_metrics

            # Fall back to SQLite
            return await self._get_metrics_sqlite(metric_name, start_time, end_time, labels, limit)

        except Exception as e:
            logger.error(f"Error retrieving metrics {metric_name}: {e}")
            return []

    async def _get_metrics_redis(self, metric_name: str,
                               start_time: Optional[datetime],
                               end_time: Optional[datetime],
                               labels: Optional[Dict[str, str]],
                               limit: int) -> List[MetricPoint]:
        """Get metrics from Redis"""
        try:
            label_str = "_".join(f"{k}:{v}" for k, v in sorted(labels.items())) if labels else ""
            redis_key = f"metric:{metric_name}:{label_str}"

            # Get range of scores
            min_score = start_time.timestamp() if start_time else "-inf"
            max_score = end_time.timestamp() if end_time else "+inf"

            # Get data from Redis sorted set
            data = self.redis_client.zrangebyscore(redis_key, min_score, max_score, start=0, num=limit, withscores=True)

            metrics = []
            for value, score in data:
                timestamp = datetime.fromtimestamp(score)
                metrics.append(MetricPoint(
                    timestamp=timestamp,
                    metric_name=metric_name,
                    value=float(value),
                    labels=labels or {},
                    tags={}
                ))

            return sorted(metrics, key=lambda x: x.timestamp)

        except Exception as e:
            logger.error(f"Error getting metrics from Redis: {e}")
            return []

    async def _get_metrics_sqlite(self, metric_name: str,
                                start_time: Optional[datetime],
                                end_time: Optional[datetime],
                                labels: Optional[Dict[str, str]],
                                limit: int) -> List[MetricPoint]:
        """Get metrics from SQLite"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()

        query = '''
            SELECT timestamp, value, labels, tags
            FROM metrics
            WHERE metric_name = ?
        '''
        params = [metric_name]

        if start_time:
            query += ' AND timestamp >= ?'
            params.append(start_time)

        if end_time:
            query += ' AND timestamp <= ?'
            params.append(end_time)

        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        metrics = []
        for row in rows:
            timestamp = datetime.fromisoformat(row[0])
            value = row[1]
            labels_data = json.loads(row[2]) if row[2] else {}
            tags_data = json.loads(row[3]) if row[3] else {}

            metrics.append(MetricPoint(
                timestamp=timestamp,
                metric_name=metric_name,
                value=value,
                labels=labels_data,
                tags=tags_data
            ))

        return sorted(metrics, key=lambda x: x.timestamp)

    async def get_latest_value(self, metric_name: str,
                             labels: Optional[Dict[str, str]] = None) -> Optional[MetricPoint]:
        """Get the latest value for a metric"""
        try:
            # Try Redis first
            if self.redis_client:
                latest_key = f"latest:{metric_name}"
                data = self.redis_client.get(latest_key)
                if data:
                    latest_data = json.loads(data)
                    return MetricPoint(
                        timestamp=datetime.fromisoformat(latest_data["timestamp"]),
                        metric_name=metric_name,
                        value=latest_data["value"],
                        labels=latest_data.get("labels", {}),
                        tags={}
                    )

            # Fall back to SQLite
            return await self._get_latest_value_sqlite(metric_name, labels)

        except Exception as e:
            logger.error(f"Error getting latest value for {metric_name}: {e}")
            return None

    async def _get_latest_value_sqlite(self, metric_name: str,
                                     labels: Optional[Dict[str, str]]) -> Optional[MetricPoint]:
        """Get latest value from SQLite"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()

        query = '''
            SELECT timestamp, value, labels, tags
            FROM metrics
            WHERE metric_name = ?
            ORDER BY timestamp DESC
            LIMIT 1
        '''
        cursor.execute(query, [metric_name])
        row = cursor.fetchone()
        conn.close()

        if row:
            return MetricPoint(
                timestamp=datetime.fromisoformat(row[0]),
                metric_name=metric_name,
                value=row[1],
                labels=json.loads(row[2]) if row[2] else {},
                tags=json.loads(row[3]) if row[3] else {}
            )

        return None

    async def aggregate_metrics(self, metric_name: str,
                              aggregation_type: str,  # avg, min, max, sum, count
                              time_bucket: str,  # 1m, 5m, 1h, 1d
                              start_time: Optional[datetime] = None,
                              end_time: Optional[datetime] = None) -> List[MetricPoint]:
        """Get aggregated metrics"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()

            # Calculate time bucket interval in seconds
            bucket_seconds = self._parse_time_bucket(time_bucket)

            # Query for aggregated data
            query = f'''
                SELECT
                    datetime((strftime('%s', timestamp) / {bucket_seconds}) * {bucket_seconds}, 'unixepoch') as bucket,
                    {self._get_aggregation_sql(aggregation_type)},
                    COUNT(*) as count,
                    MIN(value) as min_value,
                    MAX(value) as max_value,
                    SUM(value) as sum_value
                FROM metrics
                WHERE metric_name = ?
            '''
            params = [metric_name]

            if start_time:
                query += ' AND timestamp >= ?'
                params.append(start_time)

            if end_time:
                query += ' AND timestamp <= ?'
                params.append(end_time)

            query += ' GROUP BY bucket ORDER BY bucket'

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            metrics = []
            for row in rows:
                bucket_time = datetime.fromisoformat(row[0])
                value = row[1]

                metrics.append(MetricPoint(
                    timestamp=bucket_time,
                    metric_name=f"{metric_name}_{aggregation_type}_{time_bucket}",
                    value=value,
                    labels={"aggregation": aggregation_type, "bucket": time_bucket},
                    tags={
                        "count": row[2],
                        "min": row[3],
                        "max": row[4],
                        "sum": row[5]
                    }
                ))

            return metrics

        except Exception as e:
            logger.error(f"Error aggregating metrics {metric_name}: {e}")
            return []

    def _parse_time_bucket(self, time_bucket: str) -> int:
        """Parse time bucket string to seconds"""
        if time_bucket.endswith('m'):
            return int(time_bucket[:-1]) * 60
        elif time_bucket.endswith('h'):
            return int(time_bucket[:-1]) * 3600
        elif time_bucket.endswith('d'):
            return int(time_bucket[:-1]) * 86400
        else:
            return 60  # Default to 1 minute

    def _get_aggregation_sql(self, aggregation_type: str) -> str:
        """Get SQL aggregation function"""
        if aggregation_type == "avg":
            return "AVG(value)"
        elif aggregation_type == "min":
            return "MIN(value)"
        elif aggregation_type == "max":
            return "MAX(value)"
        elif aggregation_type == "sum":
            return "SUM(value)"
        elif aggregation_type == "count":
            return "COUNT(*)"
        else:
            return "AVG(value)"  # Default to average

    async def get_metric_names(self) -> List[str]:
        """Get list of all metric names"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()

            cursor.execute('SELECT DISTINCT metric_name FROM metrics ORDER BY metric_name')
            rows = cursor.fetchall()
            conn.close()

            return [row[0] for row in rows]

        except Exception as e:
            logger.error(f"Error getting metric names: {e}")
            return []

    async def delete_old_metrics(self, days_to_keep: int = 30):
        """Delete old metrics to manage storage"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff_date,))
            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            logger.info(f"Deleted {deleted_count} old metric entries older than {days_to_keep} days")

        except Exception as e:
            logger.error(f"Error deleting old metrics: {e}")

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()

            # Get total metrics count
            cursor.execute('SELECT COUNT(*) FROM metrics')
            total_metrics = cursor.fetchone()[0]

            # Get oldest and newest timestamps
            cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM metrics')
            oldest, newest = cursor.fetchone()

            # Get table size
            cursor.execute("SELECT COUNT(*) * 8192 FROM metrics")  # Rough estimate
            estimated_size_bytes = cursor.fetchone()[0]

            conn.close()

            # Get Redis info if available
            redis_info = {}
            if self.redis_client:
                try:
                    info = self.redis_client.info()
                    redis_info = {
                        "connected_clients": info.get("connected_clients", 0),
                        "used_memory": info.get("used_memory", 0),
                        "used_memory_human": info.get("used_memory_human", "0B"),
                        "keyspace_hits": info.get("keyspace_hits", 0),
                        "keyspace_misses": info.get("keyspace_misses", 0)
                    }
                except Exception as e:
                    logger.error(f"Error getting Redis info: {e}")

            return {
                "sqlite": {
                    "total_metrics": total_metrics,
                    "oldest_timestamp": oldest,
                    "newest_timestamp": newest,
                    "estimated_size_bytes": estimated_size_bytes
                },
                "redis": redis_info,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}

    async def export_metrics(self, metric_name: str,
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           format: str = "json") -> str:
        """Export metrics to file"""
        try:
            metrics = await self.get_metrics(metric_name, start_time, end_time)

            if format.lower() == "json":
                return json.dumps([asdict(m) for m in metrics], indent=2, default=str)
            elif format.lower() == "csv":
                # Convert to pandas DataFrame and export to CSV
                df_data = []
                for m in metrics:
                    row = {
                        "timestamp": m.timestamp.isoformat(),
                        "metric_name": m.metric_name,
                        "value": m.value
                    }
                    row.update(m.labels)
                    row.update(m.tags)
                    df_data.append(row)

                df = pd.DataFrame(df_data)
                return df.to_csv(index=False)
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            raise