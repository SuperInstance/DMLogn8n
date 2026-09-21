#!/usr/bin/env python3
"""
Real-time Metrics Collection System
Collects and stores performance metrics during load testing
"""

import asyncio
import time
import json
import sqlite3
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
import logging
import statistics
import numpy as np
from prometheus_client import Counter, Histogram, Gauge, start_http_server

logger = logging.getLogger(__name__)

@dataclass
class RequestMetric:
    """Single request metric"""
    timestamp: datetime
    endpoint: str
    method: str
    status_code: int
    response_time: float  # milliseconds
    success: bool
    error_message: Optional[str]
    user_id: Optional[str]
    session_id: Optional[str]
    request_size: int
    response_size: int

@dataclass
class SystemMetric:
    """System resource metric"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_usage_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int
    process_count: int
    load_average: Optional[List[float]]  # Unix only

@dataclass
class DatabaseMetric:
    """Database performance metric"""
    timestamp: datetime
    operation_type: str
    table_name: str
    query_time: float  # milliseconds
    rows_affected: int
    success: bool
    error_message: Optional[str]

@dataclass
class CustomMetric:
    """Custom application metric"""
    timestamp: datetime
    metric_name: str
    metric_type: str  # counter, gauge, histogram
    value: float
    labels: Dict[str, str]
    unit: str

class MetricsCollector:
    """Collects and manages performance metrics during load testing"""

    def __init__(self, storage_path: str = "metrics.db", prometheus_port: int = 8000):
        self.storage_path = storage_path
        self.prometheus_port = prometheus_port
        self.collection_active = False
        self.collection_interval = 1.0  # seconds

        # In-memory buffers for real-time metrics
        self.request_buffer: deque = deque(maxlen=10000)
        self.system_buffer: deque = deque(maxlen=1000)
        self.database_buffer: deque = deque(maxlen=5000)
        self.custom_buffer: deque = deque(maxlen=5000)

        # Aggregated metrics
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "success_count": 0,
            "error_count": 0,
            "response_times": deque(maxlen=1000),
            "avg_response_time": 0,
            "min_response_time": float('inf'),
            "max_response_time": 0,
            "p95_response_time": 0,
            "p99_response_time": 0,
            "error_rate": 0,
            "throughput": 0
        })

        # Prometheus metrics
        self._setup_prometheus_metrics()

        # Database setup
        self._setup_database()

        # Collection tasks
        self.collection_tasks: List[asyncio.Task] = []

        # Callbacks for real-time processing
        self.metrics_callbacks: List[Callable] = []

    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics"""
        # Request metrics
        self.request_counter = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )

        self.request_duration = Histogram(
            'http_request_duration_ms',
            'HTTP request duration in milliseconds',
            ['method', 'endpoint']
        )

        self.active_connections = Gauge(
            'active_connections',
            'Number of active connections'
        )

        # System metrics
        self.cpu_usage = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage'
        )

        self.memory_usage = Gauge(
            'memory_usage_percent',
            'Memory usage percentage'
        )

        self.disk_usage = Gauge(
            'disk_usage_percent',
            'Disk usage percentage'
        )

        # Custom application metrics
        self.agent_tasks = Gauge(
            'active_agent_tasks',
            'Number of active agent tasks'
        )

        self.user_sessions = Gauge(
            'active_user_sessions',
            'Number of active user sessions'
        )

        self.combat_encounters = Gauge(
            'active_combat_encounters',
            'Number of active combat encounters'
        )

        self.dialogue_conversations = Gauge(
            'active_dialogue_conversations',
            'Number of active dialogue conversations'
        )

        # Start Prometheus HTTP server
        try:
            start_http_server(self.prometheus_port)
            logger.info(f"Prometheus metrics server started on port {self.prometheus_port}")
        except Exception as e:
            logger.warning(f"Failed to start Prometheus server: {e}")

    def _setup_database(self):
        """Setup SQLite database for metrics storage"""
        try:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()

            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS request_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    response_time REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    request_size INTEGER,
                    response_size INTEGER
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL NOT NULL,
                    memory_percent REAL NOT NULL,
                    memory_used_gb REAL NOT NULL,
                    memory_available_gb REAL NOT NULL,
                    disk_usage_percent REAL NOT NULL,
                    network_bytes_sent INTEGER NOT NULL,
                    network_bytes_recv INTEGER NOT NULL,
                    active_connections INTEGER NOT NULL,
                    process_count INTEGER NOT NULL,
                    load_average TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS database_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    query_time REAL NOT NULL,
                    rows_affected INTEGER NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    labels TEXT,
                    unit TEXT
                )
            ''')

            # Create indexes for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_request_timestamp ON request_metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_request_endpoint ON request_metrics(endpoint)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_timestamp ON system_metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_custom_timestamp ON custom_metrics(timestamp)')

            conn.commit()
            conn.close()

            logger.info(f"Metrics database initialized at {self.storage_path}")

        except Exception as e:
            logger.error(f"Failed to setup metrics database: {e}")
            raise

    def register_callback(self, callback: Callable):
        """Register callback for real-time metric processing"""
        self.metrics_callbacks.append(callback)

    async def record_request(self, endpoint: str, response_time: float, status_code: int, success: bool, **kwargs):
        """Record a request metric"""
        metric = RequestMetric(
            timestamp=datetime.now(timezone.utc),
            endpoint=endpoint,
            method=kwargs.get('method', 'GET'),
            status_code=status_code,
            response_time=response_time,
            success=success,
            error_message=kwargs.get('error_message'),
            user_id=kwargs.get('user_id'),
            session_id=kwargs.get('session_id'),
            request_size=kwargs.get('request_size', 0),
            response_size=kwargs.get('response_size', 0)
        )

        # Add to buffer
        self.request_buffer.append(metric)

        # Update aggregated stats
        self._update_endpoint_stats(endpoint, response_time, success)

        # Update Prometheus metrics
        self.request_counter.labels(
            method=metric.method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()

        self.request_duration.labels(
            method=metric.method,
            endpoint=endpoint
        ).observe(response_time)

        # Trigger callbacks
        for callback in self.metrics_callbacks:
            try:
                await callback('request', metric)
            except Exception as e:
                logger.error(f"Error in metrics callback: {e}")

    async def record_system_metric(self, metric_data: Dict[str, Any]):
        """Record a system metric"""
        metric = SystemMetric(
            timestamp=datetime.fromisoformat(metric_data['timestamp'].replace('Z', '+00:00')),
            cpu_percent=metric_data['cpu_percent'],
            memory_percent=metric_data['memory_percent'],
            memory_used_gb=metric_data['memory_used_gb'],
            memory_available_gb=metric_data['memory_available_gb'],
            disk_usage_percent=metric_data['disk_usage_percent'],
            network_bytes_sent=metric_data['network_bytes_sent'],
            network_bytes_recv=metric_data['network_bytes_recv'],
            active_connections=metric_data.get('active_connections', 0),
            process_count=metric_data.get('process_count', 0),
            load_average=metric_data.get('load_average')
        )

        # Add to buffer
        self.system_buffer.append(metric)

        # Update Prometheus metrics
        self.cpu_usage.set(metric.cpu_percent)
        self.memory_usage.set(metric.memory_percent)
        self.disk_usage.set(metric.disk_usage_percent)
        self.active_connections.set(metric.active_connections)

        # Trigger callbacks
        for callback in self.metrics_callbacks:
            try:
                await callback('system', metric)
            except Exception as e:
                logger.error(f"Error in metrics callback: {e}")

    async def record_database_metric(self, operation: str, table: str, query_time: float, success: bool, **kwargs):
        """Record a database metric"""
        metric = DatabaseMetric(
            timestamp=datetime.now(timezone.utc),
            operation_type=operation,
            table_name=table,
            query_time=query_time,
            rows_affected=kwargs.get('rows_affected', 0),
            success=success,
            error_message=kwargs.get('error_message')
        )

        # Add to buffer
        self.database_buffer.append(metric)

        # Trigger callbacks
        for callback in self.metrics_callbacks:
            try:
                await callback('database', metric)
            except Exception as e:
                logger.error(f"Error in metrics callback: {e}")

    async def record_custom_metric(self, name: str, value: float, metric_type: str = 'gauge', labels: Optional[Dict[str, str]] = None, unit: str = ''):
        """Record a custom metric"""
        metric = CustomMetric(
            timestamp=datetime.now(timezone.utc),
            metric_name=name,
            metric_type=metric_type,
            value=value,
            labels=labels or {},
            unit=unit
        )

        # Add to buffer
        self.custom_buffer.append(metric)

        # Update relevant Prometheus gauge
        if name == 'active_agent_tasks':
            self.agent_tasks.set(value)
        elif name == 'active_user_sessions':
            self.user_sessions.set(value)
        elif name == 'active_combat_encounters':
            self.combat_encounters.set(value)
        elif name == 'active_dialogue_conversations':
            self.dialogue_conversations.set(value)

        # Trigger callbacks
        for callback in self.metrics_callbacks:
            try:
                await callback('custom', metric)
            except Exception as e:
                logger.error(f"Error in metrics callback: {e}")

    def _update_endpoint_stats(self, endpoint: str, response_time: float, success: bool):
        """Update aggregated endpoint statistics"""
        stats = self.endpoint_stats[endpoint]
        stats['count'] += 1
        stats['response_times'].append(response_time)

        if success:
            stats['success_count'] += 1
        else:
            stats['error_count'] += 1

        # Update response time statistics
        if response_time < stats['min_response_time']:
            stats['min_response_time'] = response_time
        if response_time > stats['max_response_time']:
            stats['max_response_time'] = response_time

        # Calculate statistics
        if stats['response_times']:
            response_times = list(stats['response_times'])
            stats['avg_response_time'] = statistics.mean(response_times)
            stats['p95_response_time'] = np.percentile(response_times, 95)
            stats['p99_response_time'] = np.percentile(response_times, 99)

        # Calculate error rate
        stats['error_rate'] = (stats['error_count'] / stats['count'] * 100) if stats['count'] > 0 else 0

    async def start_collection(self, config: Dict[str, Any]):
        """Start metrics collection"""
        if self.collection_active:
            logger.warning("Metrics collection already active")
            return

        self.collection_active = True
        logger.info("Starting metrics collection")

        # Start collection tasks
        self.collection_tasks = [
            asyncio.create_task(self._collect_system_metrics()),
            asyncio.create_task(self._flush_buffers()),
            asyncio.create_task(self._update_aggregated_metrics())
        ]

    async def stop_collection(self):
        """Stop metrics collection"""
        if not self.collection_active:
            return

        logger.info("Stopping metrics collection")
        self.collection_active = False

        # Cancel collection tasks
        for task in self.collection_tasks:
            task.cancel()

        try:
            await asyncio.gather(*self.collection_tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error stopping collection tasks: {e}")

        # Final flush of buffers
        await self._flush_buffers()

        self.collection_tasks.clear()

    async def _collect_system_metrics(self):
        """Collect system metrics periodically"""
        while self.collection_active:
            try:
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=0.1)

                # Memory metrics
                memory = psutil.virtual_memory()

                # Disk metrics
                disk = psutil.disk_usage('/')

                # Network metrics
                network = psutil.net_io_counters()

                # Process metrics
                process_count = len(psutil.pids())

                # Load average (Unix only)
                load_average = None
                try:
                    load_average = list(psutil.getloadavg())
                except AttributeError:
                    # Windows doesn't have load average
                    pass

                metric_data = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_gb': memory.used / (1024**3),
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_usage_percent': (disk.used / disk.total) * 100,
                    'network_bytes_sent': network.bytes_sent,
                    'network_bytes_recv': network.bytes_recv,
                    'active_connections': len(psutil.net_connections()),
                    'process_count': process_count,
                    'load_average': load_average
                }

                await self.record_system_metric(metric_data)

            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")

            await asyncio.sleep(self.collection_interval)

    async def _flush_buffers(self):
        """Flush metric buffers to database"""
        while self.collection_active:
            try:
                await self._flush_request_buffer()
                await self._flush_system_buffer()
                await self._flush_database_buffer()
                await self._flush_custom_buffer()

            except Exception as e:
                logger.error(f"Error flushing buffers: {e}")

            await asyncio.sleep(5.0)  # Flush every 5 seconds

    async def _flush_request_buffer(self):
        """Flush request metrics to database"""
        if not self.request_buffer:
            return

        # Get metrics to flush
        metrics_to_flush = []
        while self.request_buffer:
            metrics_to_flush.append(self.request_buffer.popleft())

        if not metrics_to_flush:
            return

        # Insert into database
        try:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()

            for metric in metrics_to_flush:
                cursor.execute('''
                    INSERT INTO request_metrics (
                        timestamp, endpoint, method, status_code, response_time,
                        success, error_message, user_id, session_id, request_size, response_size
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metric.timestamp.isoformat(),
                    metric.endpoint,
                    metric.method,
                    metric.status_code,
                    metric.response_time,
                    metric.success,
                    metric.error_message,
                    metric.user_id,
                    metric.session_id,
                    metric.request_size,
                    metric.response_size
                ))

            conn.commit()
            conn.close()

            logger.debug(f"Flushed {len(metrics_to_flush)} request metrics to database")

        except Exception as e:
            logger.error(f"Error flushing request metrics: {e}")

    async def _flush_system_buffer(self):
        """Flush system metrics to database"""
        if not self.system_buffer:
            return

        metrics_to_flush = []
        while self.system_buffer:
            metrics_to_flush.append(self.system_buffer.popleft())

        if not metrics_to_flush:
            return

        try:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()

            for metric in metrics_to_flush:
                cursor.execute('''
                    INSERT INTO system_metrics (
                        timestamp, cpu_percent, memory_percent, memory_used_gb,
                        memory_available_gb, disk_usage_percent, network_bytes_sent,
                        network_bytes_recv, active_connections, process_count, load_average
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metric.timestamp.isoformat(),
                    metric.cpu_percent,
                    metric.memory_percent,
                    metric.memory_used_gb,
                    metric.memory_available_gb,
                    metric.disk_usage_percent,
                    metric.network_bytes_sent,
                    metric.network_bytes_recv,
                    metric.active_connections,
                    metric.process_count,
                    json.dumps(metric.load_average) if metric.load_average else None
                ))

            conn.commit()
            conn.close()

            logger.debug(f"Flushed {len(metrics_to_flush)} system metrics to database")

        except Exception as e:
            logger.error(f"Error flushing system metrics: {e}")

    async def _flush_database_buffer(self):
        """Flush database metrics to database"""
        if not self.database_buffer:
            return

        metrics_to_flush = []
        while self.database_buffer:
            metrics_to_flush.append(self.database_buffer.popleft())

        if not metrics_to_flush:
            return

        try:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()

            for metric in metrics_to_flush:
                cursor.execute('''
                    INSERT INTO database_metrics (
                        timestamp, operation_type, table_name, query_time,
                        rows_affected, success, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metric.timestamp.isoformat(),
                    metric.operation_type,
                    metric.table_name,
                    metric.query_time,
                    metric.rows_affected,
                    metric.success,
                    metric.error_message
                ))

            conn.commit()
            conn.close()

            logger.debug(f"Flushed {len(metrics_to_flush)} database metrics to database")

        except Exception as e:
            logger.error(f"Error flushing database metrics: {e}")

    async def _flush_custom_buffer(self):
        """Flush custom metrics to database"""
        if not self.custom_buffer:
            return

        metrics_to_flush = []
        while self.custom_buffer:
            metrics_to_flush.append(self.custom_buffer.popleft())

        if not metrics_to_flush:
            return

        try:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()

            for metric in metrics_to_flush:
                cursor.execute('''
                    INSERT INTO custom_metrics (
                        timestamp, metric_name, metric_type, value, labels, unit
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    metric.timestamp.isoformat(),
                    metric.metric_name,
                    metric.metric_type,
                    metric.value,
                    json.dumps(metric.labels),
                    metric.unit
                ))

            conn.commit()
            conn.close()

            logger.debug(f"Flushed {len(metrics_to_flush)} custom metrics to database")

        except Exception as e:
            logger.error(f"Error flushing custom metrics: {e}")

    async def _update_aggregated_metrics(self):
        """Update aggregated metrics periodically"""
        while self.collection_active:
            try:
                # Calculate throughput for each endpoint
                current_time = datetime.now(timezone.utc)
                window_start = current_time - timedelta(minutes=1)  # 1-minute window

                for endpoint, stats in self.endpoint_stats.items():
                    # Count requests in the last minute from buffer
                    recent_requests = sum(
                        1 for metric in self.request_buffer
                        if metric.endpoint == endpoint and metric.timestamp > window_start
                    )
                    stats['throughput'] = recent_requests  # requests per minute

            except Exception as e:
                logger.error(f"Error updating aggregated metrics: {e}")

            await asyncio.sleep(10.0)  # Update every 10 seconds

    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics"""
        current_time = datetime.now(timezone.utc)
        window_start = current_time - timedelta(minutes=5)  # 5-minute window

        # Recent request metrics
        recent_requests = [
            metric for metric in self.request_buffer
            if metric.timestamp > window_start
        ]

        # Calculate statistics
        total_requests = len(recent_requests)
        successful_requests = sum(1 for r in recent_requests if r.success)
        error_rate = ((total_requests - successful_requests) / total_requests * 100) if total_requests > 0 else 0

        response_times = [r.response_time for r in recent_requests]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = np.percentile(response_times, 95) if response_times else 0

        # System metrics
        recent_system = [
            metric for metric in self.system_buffer
            if metric.timestamp > window_start
        ]

        avg_cpu = statistics.mean([s.cpu_percent for s in recent_system]) if recent_system else 0
        avg_memory = statistics.mean([s.memory_percent for s in recent_system]) if recent_system else 0

        return {
            "timestamp": current_time.isoformat(),
            "window": "5 minutes",
            "requests": {
                "total": total_requests,
                "successful": successful_requests,
                "error_rate": error_rate,
                "avg_response_time": avg_response_time,
                "p95_response_time": p95_response_time,
                "requests_per_second": total_requests / 300  # 5 minutes = 300 seconds
            },
            "system": {
                "avg_cpu_percent": avg_cpu,
                "avg_memory_percent": avg_memory,
                "active_connections": recent_system[-1].active_connections if recent_system else 0
            },
            "endpoints": {
                endpoint: {
                    "count": stats['count'],
                    "avg_response_time": stats['avg_response_time'],
                    "error_rate": stats['error_rate'],
                    "throughput": stats['throughput']
                }
                for endpoint, stats in self.endpoint_stats.items()
            }
        }

    async def get_historical_metrics(self, start_time: datetime, end_time: datetime, endpoint: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get historical metrics from database"""
        try:
            conn = sqlite3.connect(self.storage_path)
            cursor = conn.cursor()

            query = '''
                SELECT * FROM request_metrics
                WHERE timestamp BETWEEN ? AND ?
            '''
            params = [start_time.isoformat(), end_time.isoformat()]

            if endpoint:
                query += ' AND endpoint = ?'
                params.append(endpoint)

            query += ' ORDER BY timestamp'

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Get column names
            column_names = [description[0] for description in cursor.description]

            # Convert to list of dictionaries
            metrics = []
            for row in rows:
                metric_dict = dict(zip(column_names, row))
                metrics.append(metric_dict)

            conn.close()
            return metrics

        except Exception as e:
            logger.error(f"Error retrieving historical metrics: {e}")
            return []

    def get_endpoint_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all endpoints"""
        summary = {}

        for endpoint, stats in self.endpoint_stats.items():
            summary[endpoint] = {
                "total_requests": stats['count'],
                "successful_requests": stats['success_count'],
                "error_rate": stats['error_rate'],
                "avg_response_time": stats['avg_response_time'],
                "min_response_time": stats['min_response_time'],
                "max_response_time": stats['max_response_time'],
                "p95_response_time": stats['p95_response_time'],
                "p99_response_time": stats['p99_response_time'],
                "current_throughput": stats['throughput']
            }

        return summary

    async def export_metrics(self, filename: str, format: str = 'json'):
        """Export metrics to file"""
        try:
            if format.lower() == 'json':
                await self._export_json(filename)
            elif format.lower() == 'csv':
                await self._export_csv(filename)
            else:
                raise ValueError(f"Unsupported format: {format}")

            logger.info(f"Metrics exported to {filename}")

        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            raise

    async def _export_json(self, filename: str):
        """Export metrics as JSON"""
        data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "real_time_metrics": await self.get_real_time_metrics(),
            "endpoint_summary": self.get_endpoint_summary(),
            "aggregated_metrics": {
                endpoint: dict(stats) for endpoint, stats in self.endpoint_stats.items()
            }
        }

        # Convert deque objects to lists for JSON serialization
        for endpoint_stats in data["aggregated_metrics"].values():
            if "response_times" in endpoint_stats:
                endpoint_stats["response_times"] = list(endpoint_stats["response_times"])

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    async def _export_csv(self, filename: str):
        """Export request metrics as CSV"""
        import csv

        # Get all request metrics from database
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=24)  # Last 24 hours

        metrics = await self.get_historical_metrics(start_time, end_time)

        if not metrics:
            logger.warning("No metrics to export")
            return

        # Write to CSV
        with open(filename, 'w', newline='') as csvfile:
            if metrics:
                fieldnames = metrics[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(metrics)

# Example usage
async def test_metrics_collector():
    """Test the metrics collector"""
    collector = MetricsCollector()

    # Register a callback
    async def metric_callback(metric_type: str, metric: Any):
        print(f"Received {metric_type} metric: {type(metric).__name__}")

    collector.register_callback(metric_callback)

    # Start collection
    await collector.start_collection({})

    # Simulate some metrics
    for i in range(10):
        await collector.record_request(
            f"/api/test/{i}", random.uniform(100, 500), 200, True
        )
        await asyncio.sleep(0.1)

    # Record custom metrics
    await collector.record_custom_metric("active_users", random.randint(10, 100))
    await collector.record_custom_metric("active_sessions", random.randint(5, 50))

    # Get real-time metrics
    real_time = await collector.get_real_time_metrics()
    print("\nReal-time metrics:")
    print(json.dumps(real_time, indent=2, default=str))

    # Get endpoint summary
    summary = collector.get_endpoint_summary()
    print("\nEndpoint summary:")
    print(json.dumps(summary, indent=2, default=str))

    # Stop collection
    await collector.stop_collection()

    # Export metrics
    await collector.export_metrics("test_metrics.json", "json")

if __name__ == "__main__":
    asyncio.run(test_metrics_collector())