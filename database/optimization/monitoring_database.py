#!/usr/bin/env python3
"""
Database Performance Monitoring System
Real-time monitoring and analytics for PostgreSQL, MongoDB, Redis with comprehensive metrics collection.
"""

import asyncio
import json
import time
import logging
import psutil
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict, deque
from datetime import datetime, timedelta
import statistics
import threading
import queue
import numpy as np

import psycopg2
import psycopg2.extras
import pymongo
from asyncpg import create_pool
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class MonitoringCategory(Enum):
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    RESOURCE_USAGE = "resource_usage"
    QUERY_ANALYTICS = "query_analytics"
    CONNECTION_HEALTH = "connection_health"
    REPLICATION_STATUS = "replication_status"
    BACKUP_STATUS = "backup_status"

@dataclass
class Metric:
    name: str
    value: float
    metric_type: MetricType
    category: MonitoringCategory
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""

@dataclass
class Alert:
    id: str
    name: str
    severity: AlertSeverity
    message: str
    metric_name: str
    threshold: float
    current_value: float
    triggered_at: datetime
    resolved_at: Optional[datetime]
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

@dataclass
class QueryPerformance:
    query_hash: str
    query_text: str
    execution_count: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    rows_returned: int
    rows_examined: int
    index_usage: bool
    timestamp: datetime
    database: str

@dataclass
class DatabaseSnapshot:
    timestamp: datetime
    database_type: str
    database_name: str
    metrics: Dict[str, Metric]
    active_connections: int
    total_connections: int
    cache_hit_ratio: float
    slow_queries_count: int
    lock_wait_time_ms: float
    replication_lag_seconds: float
    disk_usage_mb: float
    memory_usage_mb: float
    cpu_usage_percent: float

@dataclass
class MonitoringConfiguration:
    collection_interval_seconds: int = 30
    retention_hours: int = 24 * 7  # 1 week
    alert_cooldown_minutes: int = 5
    enable_query_monitoring: bool = True
    enable_slow_query_detection: bool = True
    slow_query_threshold_ms: int = 1000
    enable_connection_monitoring: bool = True
    enable_resource_monitoring: bool = True
    enable_replication_monitoring: bool = True
    max_metrics_per_category: int = 1000
    enable_real_time_alerts: bool = True
    alert_webhook_url: Optional[str] = None

class DatabaseMonitor:
    """Comprehensive database monitoring system"""

    def __init__(self, database_type: str, connection_params: Dict[str, Any],
                 config: Optional[MonitoringConfiguration] = None):
        self.database_type = database_type.lower()
        self.connection_params = connection_params
        self.config = config or MonitoringConfiguration()

        # Storage
        self.metrics_history = defaultdict(lambda: deque(maxlen=self.config.retention_hours * 120))  # 2 per minute
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.query_performance = deque(maxlen=10000)
        self.snapshots = deque(maxlen=self.config.retention_hours * 120)

        # Monitoring state
        self.is_monitoring = False
        self.monitoring_task = None
        self.alert_processing_task = None
        self.cleanup_task = None

        # Performance tracking
        self.baseline_metrics = {}
        self.performance_trends = defaultdict(list)
        self.anomaly_detection = {}

        # Alert system
        self.alert_rules = self._initialize_alert_rules()
        self.alert_cooldowns = {}

        # Statistics
        self.monitoring_stats = {
            'metrics_collected': 0,
            'alerts_triggered': 0,
            'alerts_resolved': 0,
            'slow_queries_detected': 0,
            'uptime_seconds': 0,
            'last_collection': None
        }

    async def start_monitoring(self) -> bool:
        """Start database monitoring"""

        try:
            logger.info(f"Starting database monitoring for {self.database_type}")

            # Initialize baseline metrics
            await self._establish_baseline()

            # Start monitoring tasks
            self.is_monitoring = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.alert_processing_task = asyncio.create_task(self._alert_processing_loop())
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())

            logger.info(f"Database monitoring started for {self.database_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            return False

    async def stop_monitoring(self) -> None:
        """Stop database monitoring"""

        logger.info("Stopping database monitoring")

        self.is_monitoring = False

        # Cancel tasks
        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.alert_processing_task:
            self.alert_processing_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()

        logger.info("Database monitoring stopped")

    async def collect_metrics(self) -> DatabaseSnapshot:
        """Collect current database metrics"""

        try:
            timestamp = datetime.now()

            if self.database_type == 'postgresql':
                snapshot = await self._collect_postgresql_metrics(timestamp)
            elif self.database_type == 'mongodb':
                snapshot = await self._collect_mongodb_metrics(timestamp)
            elif self.database_type == 'redis':
                snapshot = await self._collect_redis_metrics(timestamp)
            else:
                raise ValueError(f"Unsupported database type: {self.database_type}")

            # Store snapshot
            self.snapshots.append(snapshot)

            # Update metrics history
            for metric in snapshot.metrics.values():
                self.metrics_history[metric.name].append(metric)

            # Update statistics
            self.monitoring_stats['metrics_collected'] += len(snapshot.metrics)
            self.monitoring_stats['last_collection'] = timestamp

            # Detect anomalies
            await self._detect_anomalies(snapshot)

            return snapshot

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            raise

    async def _collect_postgresql_metrics(self, timestamp: datetime) -> DatabaseSnapshot:
        """Collect PostgreSQL metrics"""

        conn = await create_pool(**self.connection_params)
        metrics = {}

        async with conn.acquire() as connection:
            # Performance metrics
            performance_queries = {
                'active_connections': "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'",
                'total_connections': "SELECT count(*) FROM pg_stat_activity",
                'cache_hit_ratio': """
                    SELECT round(sum(blks_hit)::float / (sum(blks_hit) + sum(blks_read)), 4) * 100
                    FROM pg_stat_database WHERE datname = current_database()
                """,
                'transactions_per_second': """
                    SELECT (xact_commit + xact_rollback)
                    FROM pg_stat_database WHERE datname = current_database()
                """,
                'database_size_mb': """
                    SELECT round(pg_database_size(current_database()) / 1024.0 / 1024.0)
                """,
                'lock_waits': "SELECT count(*) FROM pg_locks WHERE granted = false",
                'long_running_queries': """
                    SELECT count(*) FROM pg_stat_activity
                    WHERE state = 'active' AND query_start < now() - interval '30 seconds'
                """,
                'autovacuum_count': "SELECT count(*) FROM pg_stat_activity WHERE query LIKE '%autovacuum%'",
                'index_usage_ratio': """
                    SELECT round(sum(idx_scan)::float / NULLIF(sum(idx_scan + seq_scan), 0), 4) * 100
                    FROM pg_stat_user_tables
                """,
                'deadlock_count': """
                    SELECT count(*) FROM pg_stat_database WHERE datname = current_database()
                """
            }

            for name, query in performance_queries.items():
                try:
                    value = await connection.fetchval(query)
                    if value is not None:
                        metrics[name] = Metric(
                            name=name,
                            value=float(value),
                            metric_type=MetricType.GAUGE,
                            category=MonitoringCategory.PERFORMANCE,
                            timestamp=timestamp,
                            unit=self._get_metric_unit(name),
                            description=self._get_metric_description(name)
                        )
                except Exception as e:
                    logger.debug(f"Failed to collect metric {name}: {e}")

            # Resource metrics
            resource_metrics = await self._collect_system_metrics()

            # Query performance metrics
            if self.config.enable_query_monitoring:
                await self._collect_postgresql_query_metrics(connection, timestamp)

        return DatabaseSnapshot(
            timestamp=timestamp,
            database_type='postgresql',
            database_name=self.connection_params.get('database', 'unknown'),
            metrics=metrics,
            active_connections=int(metrics.get('active_connections', Metric('', 0, MetricType.GAUGE, MonitoringCategory.PERFORMANCE, timestamp)).value),
            total_connections=int(metrics.get('total_connections', Metric('', 0, MetricType.GAUGE, MonitoringCategory.PERFORMANCE, timestamp)).value),
            cache_hit_ratio=metrics.get('cache_hit_ratio', Metric('', 0, MetricType.GAUGE, MonitoringCategory.PERFORMANCE, timestamp)).value,
            slow_queries_count=int(metrics.get('long_running_queries', Metric('', 0, MetricType.GAUGE, MonitoringCategory.PERFORMANCE, timestamp)).value),
            lock_wait_time_ms=metrics.get('lock_waits', Metric('', 0, MetricType.GAUGE, MonitoringCategory.PERFORMANCE, timestamp)).value,
            replication_lag_seconds=0.0,  # Would collect from replication status
            disk_usage_mb=metrics.get('database_size_mb', Metric('', 0, MetricType.GAUGE, MonitoringCategory.RESOURCE_USAGE, timestamp)).value,
            memory_usage_mb=resource_metrics.get('memory_mb', 0),
            cpu_usage_percent=resource_metrics.get('cpu_percent', 0)
        )

    async def _collect_mongodb_metrics(self, timestamp: datetime) -> DatabaseSnapshot:
        """Collect MongoDB metrics"""

        client = pymongo.MongoClient(**self.connection_params)
        admin_db = client.admin
        metrics = {}

        try:
            # Get server status
            server_status = admin_db.command("serverStatus")

            # Extract metrics
            metric_data = {
                'active_connections': server_status.get('connections', {}).get('current', 0),
                'total_connections': server_status.get('connections', {}).get('totalCreated', 0),
                'operations_per_second': server_status.get('opcounters', {}).get('insert', 0) / 60,  # Simplified
                'query_executors_per_sec': server_status.get('metrics', {}).get('query', {}).get('executor', {}).get('scannedObjectsPerSecond', 0),
                'cache_hit_ratio': self._calculate_mongodb_cache_hit_ratio(server_status),
                'memory_usage_mb': server_status.get('mem', {}).get('resident', 0),
                'page_faults_per_sec': server_status.get('extra_info', {}).get('page_faults', 0) / 60,
                'document_operations_per_sec': self._calculate_mongodb_ops_per_sec(server_status),
                'index_usage_ratio': self._calculate_mongodb_index_usage_ratio(admin_db),
                'network_bytes_in': server_status.get('network', {}).get('bytesIn', 0),
                'network_bytes_out': server_status.get('network', {}).get('bytesOut', 0)
            }

            for name, value in metric_data.items():
                metrics[name] = Metric(
                    name=name,
                    value=float(value),
                    metric_type=MetricType.GAUGE,
                    category=MonitoringCategory.PERFORMANCE,
                    timestamp=timestamp,
                    unit=self._get_metric_unit(name),
                    description=self._get_metric_description(name)
                )

            # Get database stats
            db_stats = admin_db.command("dbStats")
            metrics['database_size_mb'] = Metric(
                name='database_size_mb',
                value=float(db_stats.get('dataSize', 0) / (1024 * 1024)),
                metric_type=MetricType.GAUGE,
                category=MonitoringCategory.RESOURCE_USAGE,
                timestamp=timestamp,
                unit='MB',
                description='Database size in megabytes'
            )

            # Query performance metrics
            if self.config.enable_query_monitoring:
                await self._collect_mongodb_query_metrics(admin_db, timestamp)

        except Exception as e:
            logger.error(f"Failed to collect MongoDB metrics: {e}")

        # System metrics
        resource_metrics = await self._collect_system_metrics()

        return DatabaseSnapshot(
            timestamp=timestamp,
            database_type='mongodb',
            database_name=self.connection_params.get('database', 'unknown'),
            metrics=metrics,
            active_connections=int(metrics.get('active_connections', Metric('', 0, MetricType.GAUGE, MonitoringCategory.PERFORMANCE, timestamp)).value),
            total_connections=int(metrics.get('total_connections', Metric('', 0, MetricType.GAUGE, MonitoringCategory.PERFORMANCE, timestamp)).value),
            cache_hit_ratio=metrics.get('cache_hit_ratio', Metric('', 0, MetricType.GAUGE, MonitoringCategory.PERFORMANCE, timestamp)).value,
            slow_queries_count=0,  # Would need profiler enabled
            lock_wait_time_ms=0.0,
            replication_lag_seconds=0.0,  # Would collect from replica set status
            disk_usage_mb=metrics.get('database_size_mb', Metric('', 0, MetricType.GAUGE, MonitoringCategory.RESOURCE_USAGE, timestamp)).value,
            memory_usage_mb=resource_metrics.get('memory_mb', 0),
            cpu_usage_percent=resource_metrics.get('cpu_percent', 0)
        )

    async def _collect_redis_metrics(self, timestamp: datetime) -> DatabaseSnapshot:
        """Collect Redis metrics"""

        redis_client = redis.Redis(**self.connection_params)
        metrics = {}

        try:
            # Get Redis info
            info = redis_client.info()

            # Extract metrics
            metric_data = {
                'connected_clients': info.get('connected_clients', 0),
                'total_connections_received': info.get('total_connections_received', 0),
                'operations_per_second': info.get('instantaneous_ops_per_sec', 0),
                'hit_ratio': (info.get('keyspace_hits', 0) / max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0))) * 100,
                'memory_usage_mb': info.get('used_memory', 0) / (1024 * 1024),
                'memory_peak_mb': info.get('used_memory_peak', 0) / (1024 * 1024),
                'expired_keys': info.get('expired_keys', 0),
                'evicted_keys': info.get('evicted_keys', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'total_net_input_bytes': info.get('total_net_input_bytes', 0),
                'total_net_output_bytes': info.get('total_net_output_bytes', 0)
            }

            for name, value in metric_data.items():
                metrics[name] = Metric(
                    name=name,
                    value=float(value),
                    metric_type=MetricType.GAUGE if 'per_sec' not in name else MetricType.COUNTER,
                    category=MonitoringCategory.PERFORMANCE,
                    timestamp=timestamp,
                    unit=self._get_metric_unit(name),
                    description=self._get_metric_description(name)
                )

            # Memory fragmentation ratio
            if info.get('used_memory_rss', 0) > 0:
                frag_ratio = info.get('used_memory_rss', 0) / info.get('used_memory', 1)
                metrics['memory_fragmentation_ratio'] = Metric(
                    name='memory_fragmentation_ratio',
                    value=frag_ratio,
                    metric_type=MetricType.GAUGE,
                    category=MonitoringCategory.RESOURCE_USAGE,
                    timestamp=timestamp,
                    unit='ratio',
                    description='Memory fragmentation ratio'
                )

        except Exception as e:
            logger.error(f"Failed to collect Redis metrics: {e}")

        # System metrics
        resource_metrics = await self._collect_system_metrics()

        return DatabaseSnapshot(
            timestamp=timestamp,
            database_type='redis',
            database_name=str(self.connection_params.get('db', 0)),
            metrics=metrics,
            active_connections=int(metrics.get('connected_clients', Metric('', 0, MetricType.GAUGE, MonitoringCategory.PERFORMANCE, timestamp)).value),
            total_connections=int(metrics.get('total_connections_received', Metric('', 0, MetricType.COUNTER, MonitoringCategory.CONNECTION_HEALTH, timestamp)).value),
            cache_hit_ratio=metrics.get('hit_ratio', Metric('', 0, MetricType.GAUGE, MonitoringCategory.PERFORMANCE, timestamp)).value,
            slow_queries_count=0,
            lock_wait_time_ms=0.0,
            replication_lag_seconds=0.0,
            disk_usage_mb=0.0,  # Redis doesn't use disk in the same way
            memory_usage_mb=resource_metrics.get('memory_mb', 0),
            cpu_usage_percent=resource_metrics.get('cpu_percent', 0)
        )

    async def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect system-level metrics"""

        try:
            return {
                'memory_mb': psutil.virtual_memory().used / (1024 * 1024),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'load_average': psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0,
                'network_io_read_mb': psutil.net_io_counters().bytes_recv / (1024 * 1024),
                'network_io_write_mb': psutil.net_io_counters().bytes_sent / (1024 * 1024)
            }
        except Exception as e:
            logger.debug(f"Failed to collect system metrics: {e}")
            return {}

    async def _collect_postgresql_query_metrics(self, connection, timestamp: datetime) -> None:
        """Collect PostgreSQL query performance metrics"""

        try:
            query = """
            SELECT query, calls, total_time, mean_time, min_time, max_time, rows, 100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
            FROM pg_stat_statements
            WHERE calls > 0
            ORDER BY total_time DESC
            LIMIT 100
            """

            rows = await connection.fetch(query)

            for row in rows:
                query_hash = hashlib.md5(row['query'].encode()).hexdigest()[:16]

                query_perf = QueryPerformance(
                    query_hash=query_hash,
                    query_text=row['query'],
                    execution_count=row['calls'],
                    total_time_ms=row['total_time'],
                    avg_time_ms=row['mean_time'],
                    min_time_ms=row['min_time'],
                    max_time_ms=row['max_time'],
                    rows_returned=row['rows'],
                    rows_examined=0,  # Not available in pg_stat_statements
                    index_usage=row['hit_percent'] > 50,
                    timestamp=timestamp,
                    database=self.connection_params.get('database', 'unknown')
                )

                self.query_performance.append(query_perf)

                # Check for slow queries
                if row['mean_time'] > self.config.slow_query_threshold_ms:
                    self.monitoring_stats['slow_queries_detected'] += 1

                    # Trigger alert for slow query
                    await self._trigger_slow_query_alert(query_perf)

        except Exception as e:
            logger.debug(f"Failed to collect PostgreSQL query metrics: {e}")

    async def _collect_mongodb_query_metrics(self, admin_db, timestamp: datetime) -> None:
        """Collect MongoDB query performance metrics"""

        try:
            # This would require MongoDB profiler to be enabled
            pass
        except Exception as e:
            logger.debug(f"Failed to collect MongoDB query metrics: {e}")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""

        while self.is_monitoring:
            try:
                start_time = time.time()

                # Collect metrics
                await self.collect_metrics()

                # Update uptime
                self.monitoring_stats['uptime_seconds'] += self.config.collection_interval_seconds

                # Sleep until next collection
                elapsed = time.time() - start_time
                sleep_time = max(0, self.config.collection_interval_seconds - elapsed)
                await asyncio.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.config.collection_interval_seconds)

    async def _alert_processing_loop(self) -> None:
        """Alert processing loop"""

        while self.is_monitoring:
            try:
                await asyncio.sleep(60)  # Check alerts every minute

                # Process alert rules
                if self.config.enable_real_time_alerts:
                    await self._process_alert_rules()

            except Exception as e:
                logger.error(f"Alert processing loop error: {e}")

    async def _cleanup_loop(self) -> None:
        """Cleanup old data loop"""

        while self.is_monitoring:
            try:
                await asyncio.sleep(3600)  # Run cleanup every hour

                # Clean up old metrics
                cutoff_time = datetime.now() - timedelta(hours=self.config.retention_hours)

                for metric_name, metric_deque in self.metrics_history.items():
                    while metric_deque and metric_deque[0].timestamp < cutoff_time:
                        metric_deque.popleft()

                # Clean up old alerts
                while self.alert_history and self.alert_history[0].triggered_at < cutoff_time:
                    self.alert_history.popleft()

            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")

    async def _establish_baseline(self) -> None:
        """Establish performance baseline"""

        logger.info("Establishing performance baseline")

        try:
            # Collect initial metrics
            for _ in range(5):  # Collect 5 samples
                await self.collect_metrics()
                await asyncio.sleep(10)

            # Calculate baseline values
            for metric_name, metric_deque in self.metrics_history.items():
                if len(metric_deque) >= 3:
                    values = [m.value for m in metric_deque]
                    self.baseline_metrics[metric_name] = {
                        'mean': statistics.mean(values),
                        'median': statistics.median(values),
                        'std': statistics.stdev(values) if len(values) > 1 else 0,
                        'min': min(values),
                        'max': max(values)
                    }

            logger.info(f"Baseline established for {len(self.baseline_metrics)} metrics")

        except Exception as e:
            logger.error(f"Failed to establish baseline: {e}")

    async def _detect_anomalies(self, snapshot: DatabaseSnapshot) -> None:
        """Detect anomalies in current metrics"""

        for metric_name, metric in snapshot.metrics.items():
            if metric_name in self.baseline_metrics:
                baseline = self.baseline_metrics[metric_name]

                # Simple statistical anomaly detection
                if baseline['std'] > 0:
                    z_score = abs(metric.value - baseline['mean']) / baseline['std']

                    if z_score > 3:  # 3 sigma rule
                        await self._trigger_anomaly_alert(metric, z_score)

    async def _process_alert_rules(self) -> None:
        """Process alert rules and trigger alerts"""

        current_time = datetime.now()

        for rule_name, rule in self.alert_rules.items():
            try:
                # Check cooldown
                if rule_name in self.alert_cooldowns:
                    if current_time - self.alert_cooldowns[rule_name] < timedelta(minutes=self.config.alert_cooldown_minutes):
                        continue

                # Get current metric value
                metric_name = rule['metric']
                if metric_name not in self.metrics_history or not self.metrics_history[metric_name]:
                    continue

                current_metric = self.metrics_history[metric_name][-1]
                current_value = current_metric.value

                # Check threshold
                triggered = False
                if rule['operator'] == '>':
                    triggered = current_value > rule['threshold']
                elif rule['operator'] == '<':
                    triggered = current_value < rule['threshold']
                elif rule['operator'] == '=':
                    triggered = current_value == rule['threshold']

                if triggered:
                    await self._trigger_alert(
                        metric_name,
                        rule['severity'],
                        rule['message'].format(value=current_value, threshold=rule['threshold']),
                        rule['threshold'],
                        current_value
                    )

                    # Set cooldown
                    self.alert_cooldowns[rule_name] = current_time

            except Exception as e:
                logger.error(f"Error processing alert rule {rule_name}: {e}")

    async def _trigger_alert(self, metric_name: str, severity: AlertSeverity,
                           message: str, threshold: float, current_value: float) -> None:
        """Trigger an alert"""

        alert_id = str(uuid.uuid4())
        alert = Alert(
            id=alert_id,
            name=f"{metric_name}_alert",
            severity=severity,
            message=message,
            metric_name=metric_name,
            threshold=threshold,
            current_value=current_value,
            triggered_at=datetime.now(),
            resolved_at=None
        )

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.monitoring_stats['alerts_triggered'] += 1

        logger.warning(f"Alert triggered: {message}")

        # Send webhook if configured
        if self.config.alert_webhook_url:
            await self._send_alert_webhook(alert)

    async def _trigger_slow_query_alert(self, query_perf: QueryPerformance) -> None:
        """Trigger alert for slow query"""

        await self._trigger_alert(
            metric_name='slow_query',
            severity=AlertSeverity.WARNING,
            message=f"Slow query detected: {query_perf.avg_time_ms:.1f}ms average execution time",
            threshold=self.config.slow_query_threshold_ms,
            current_value=query_perf.avg_time_ms
        )

    async def _trigger_anomaly_alert(self, metric: Metric, z_score: float) -> None:
        """Trigger alert for anomaly detection"""

        await self._trigger_alert(
            metric_name=f"anomaly_{metric.name}",
            severity=AlertSeverity.WARNING,
            message=f"Anomaly detected in {metric.name}: z-score = {z_score:.1f}",
            threshold=3.0,
            current_value=z_score
        )

    async def _send_alert_webhook(self, alert: Alert) -> None:
        """Send alert via webhook"""

        try:
            import aiohttp

            payload = {
                'alert_id': alert.id,
                'name': alert.name,
                'severity': alert.severity.value,
                'message': alert.message,
                'metric_name': alert.metric_name,
                'threshold': alert.threshold,
                'current_value': alert.current_value,
                'triggered_at': alert.triggered_at.isoformat()
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.alert_webhook_url, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Failed to send alert webhook: {response.status}")

        except Exception as e:
            logger.error(f"Failed to send alert webhook: {e}")

    def _initialize_alert_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize default alert rules"""

        return {
            'high_cpu_usage': {
                'metric': 'cpu_usage_percent',
                'threshold': 80,
                'operator': '>',
                'severity': AlertSeverity.WARNING,
                'message': 'High CPU usage: {value:.1f}% (threshold: {threshold}%)'
            },
            'high_memory_usage': {
                'metric': 'memory_usage_mb',
                'threshold': 1024,  # 1GB
                'operator': '>',
                'severity': AlertSeverity.WARNING,
                'message': 'High memory usage: {value:.1f}MB (threshold: {threshold}MB)'
            },
            'low_cache_hit_ratio': {
                'metric': 'cache_hit_ratio',
                'threshold': 90,
                'operator': '<',
                'severity': AlertSeverity.WARNING,
                'message': 'Low cache hit ratio: {value:.1f}% (threshold: {threshold}%)'
            },
            'too_many_connections': {
                'metric': 'active_connections',
                'threshold': 100,
                'operator': '>',
                'severity': AlertSeverity.CRITICAL,
                'message': 'Too many active connections: {value} (threshold: {threshold})'
            },
            'slow_query_detected': {
                'metric': 'slow_queries_count',
                'threshold': 0,
                'operator': '>',
                'severity': AlertSeverity.WARNING,
                'message': 'Slow queries detected: {value}'
            }
        }

    def _calculate_mongodb_cache_hit_ratio(self, server_status: Dict[str, Any]) -> float:
        """Calculate MongoDB cache hit ratio"""
        try:
            wired_tiger = server_status.get('wiredTiger', {})
            block_manager = wired_tiger.get('block-manager', {})

            reads = block_manager.get('blocks read', 0)
            cache_reads = block_manager.get('blocks read from cache', 0)

            if reads + cache_reads > 0:
                return (cache_reads / (reads + cache_reads)) * 100
            return 0.0
        except:
            return 0.0

    def _calculate_mongodb_ops_per_sec(self, server_status: Dict[str, Any]) -> float:
        """Calculate MongoDB operations per second"""
        try:
            opcounters = server_status.get('opcounters', {})
            total_ops = sum(opcounters.values())
            uptime = server_status.get('uptimeMillis', 1) / 1000

            return total_ops / uptime if uptime > 0 else 0.0
        except:
            return 0.0

    def _calculate_mongodb_index_usage_ratio(self, admin_db) -> float:
        """Calculate MongoDB index usage ratio"""
        try:
            # This would require collection stats aggregation
            return 85.0  # Simplified
        except:
            return 0.0

    def _get_metric_unit(self, metric_name: str) -> str:
        """Get unit for metric"""
        units = {
            'active_connections': 'count',
            'total_connections': 'count',
            'cache_hit_ratio': '%',
            'operations_per_second': 'ops/sec',
            'memory_usage_mb': 'MB',
            'cpu_usage_percent': '%',
            'disk_usage_percent': '%'
        }
        return units.get(metric_name, '')

    def _get_metric_description(self, metric_name: str) -> str:
        """Get description for metric"""
        descriptions = {
            'active_connections': 'Number of active database connections',
            'total_connections': 'Total number of connections',
            'cache_hit_ratio': 'Percentage of cache hits',
            'operations_per_second': 'Operations per second',
            'memory_usage_mb': 'Memory usage in megabytes',
            'cpu_usage_percent': 'CPU usage percentage'
        }
        return descriptions.get(metric_name, '')

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current database metrics"""

        if not self.snapshots:
            return {}

        latest_snapshot = self.snapshots[-1]

        return {
            'timestamp': latest_snapshot.timestamp.isoformat(),
            'database_type': latest_snapshot.database_type,
            'database_name': latest_snapshot.database_name,
            'active_connections': latest_snapshot.active_connections,
            'total_connections': latest_snapshot.total_connections,
            'cache_hit_ratio': latest_snapshot.cache_hit_ratio,
            'slow_queries_count': latest_snapshot.slow_queries_count,
            'memory_usage_mb': latest_snapshot.memory_usage_mb,
            'cpu_usage_percent': latest_snapshot.cpu_usage_percent,
            'disk_usage_mb': latest_snapshot.disk_usage_mb
        }

    def get_alerts(self, include_resolved: bool = False) -> List[Dict[str, Any]]:
        """Get alerts"""

        alerts = []

        # Active alerts
        for alert in self.active_alerts.values():
            alerts.append({
                'id': alert.id,
                'name': alert.name,
                'severity': alert.severity.value,
                'message': alert.message,
                'metric_name': alert.metric_name,
                'threshold': alert.threshold,
                'current_value': alert.current_value,
                'triggered_at': alert.triggered_at.isoformat(),
                'acknowledged': alert.acknowledged
            })

        # Resolved alerts (if requested)
        if include_resolved:
            for alert in self.alert_history:
                if alert.resolved_at:
                    alerts.append({
                        'id': alert.id,
                        'name': alert.name,
                        'severity': alert.severity.value,
                        'message': alert.message,
                        'metric_name': alert.metric_name,
                        'threshold': alert.threshold,
                        'current_value': alert.current_value,
                        'triggered_at': alert.triggered_at.isoformat(),
                        'resolved_at': alert.resolved_at.isoformat(),
                        'acknowledged': alert.acknowledged
                    })

        return alerts

    def get_query_performance(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get query performance data"""

        queries = list(self.query_performance)[-limit:]

        return [
            {
                'query_hash': q.query_hash,
                'query_text': q.query_text[:100] + '...' if len(q.query_text) > 100 else q.query_text,
                'execution_count': q.execution_count,
                'avg_time_ms': q.avg_time_ms,
                'max_time_ms': q.max_time_ms,
                'rows_returned': q.rows_returned,
                'index_usage': q.index_usage,
                'timestamp': q.timestamp.isoformat()
            }
            for q in queries
        ]

    def get_monitoring_report(self) -> Dict[str, Any]:
        """Get comprehensive monitoring report"""

        return {
            'monitoring_stats': self.monitoring_stats,
            'current_metrics': self.get_current_metrics(),
            'active_alerts_count': len(self.active_alerts),
            'total_alerts_count': len(self.alert_history),
            'slow_queries_count': self.monitoring_stats['slow_queries_detected'],
            'baseline_metrics_count': len(self.baseline_metrics),
            'metrics_tracked': len(self.metrics_history),
            'uptime_hours': self.monitoring_stats['uptime_seconds'] / 3600,
            'last_collection': self.monitoring_stats['last_collection'].isoformat() if self.monitoring_stats['last_collection'] else None
        }

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""

        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now()
            return True

        return False

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""

        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved_at = datetime.now()
            self.monitoring_stats['alerts_resolved'] += 1

            # Remove from active alerts
            del self.active_alerts[alert_id]
            return True

        return False

# Example usage
async def main():
    """Example usage of the database monitoring system"""

    # PostgreSQL example
    pg_connection_params = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'password',
        'database': 'test_db'
    }

    config = MonitoringConfiguration(
        collection_interval_seconds=30,
        enable_real_time_alerts=True,
        slow_query_threshold_ms=500
    )

    monitor = DatabaseMonitor('postgresql', pg_connection_params, config)

    try:
        # Start monitoring
        success = await monitor.start_monitoring()
        if success:
            print("Database monitoring started successfully")

            # Let it run for a few minutes
            await asyncio.sleep(120)

            # Get current metrics
            current_metrics = monitor.get_current_metrics()
            print(f"\nCurrent metrics:")
            for key, value in current_metrics.items():
                if key not in ['timestamp']:
                    print(f"  {key}: {value}")

            # Get alerts
            alerts = monitor.get_alerts()
            print(f"\nActive alerts: {len(alerts)}")
            for alert in alerts:
                print(f"  {alert['severity'].upper()}: {alert['message']}")

            # Get query performance
            query_perf = monitor.get_query_performance(limit=5)
            print(f"\nTop 5 slowest queries:")
            for query in query_perf:
                print(f"  {query['avg_time_ms']:.1f}ms - {query['query_text'][:50]}...")

            # Get monitoring report
            report = monitor.get_monitoring_report()
            print(f"\nMonitoring report:")
            print(f"  Uptime: {report['uptime_hours']:.1f} hours")
            print(f"  Metrics collected: {report['monitoring_stats']['metrics_collected']}")
            print(f"  Alerts triggered: {report['monitoring_stats']['alerts_triggered']}")
            print(f"  Slow queries detected: {report['slow_queries_count']}")

        else:
            print("Failed to start database monitoring")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Stop monitoring
        await monitor.stop_monitoring()
        print("Database monitoring stopped")

if __name__ == "__main__":
    asyncio.run(main())