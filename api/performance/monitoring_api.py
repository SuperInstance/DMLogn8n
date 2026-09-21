#!/usr/bin/env python3
"""
Advanced API Performance Monitoring System
Real-time performance monitoring with detailed metrics and alerts
"""

import asyncio
import time
import json
import logging
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from enum import Enum
import uuid
import statistics
import aiofiles
import aioredis
import numpy as np
from fastapi import FastAPI, Request, Response, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import orjson
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import websockets

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MonitoringLevel(Enum):
    """Monitoring detail levels"""
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"
    DEBUG = "debug"

@dataclass
class MonitoringConfig:
    """Configuration for monitoring system"""
    # Metrics collection
    metrics_retention_seconds: int = 3600  # 1 hour
    metrics_collection_interval: float = 1.0  # seconds
    detailed_metrics_interval: float = 10.0  # seconds
    max_metrics_points: int = 10000

    # Alerting
    enable_alerts: bool = True
    alert_check_interval: float = 5.0  # seconds
    alert_cooldown_seconds: int = 300  # 5 minutes

    # Performance thresholds
    response_time_warning_ms: float = 100.0
    response_time_critical_ms: float = 500.0
    error_rate_warning_percent: float = 5.0
    error_rate_critical_percent: float = 10.0
    memory_warning_mb: float = 512.0
    memory_critical_mb: float = 1024.0
    cpu_warning_percent: float = 80.0
    cpu_critical_percent: float = 95.0

    # Real-time monitoring
    enable_realtime_monitoring: bool = True
    websocket_buffer_size: int = 1000
    realtime_update_interval: float = 0.1  # seconds

    # Storage
    enable_redis_storage: bool = True
    redis_url: str = "redis://localhost:6379"
    enable_file_storage: bool = True
    storage_file_path: str = "/tmp/api_metrics.jsonl"

    # Export
    enable_prometheus: bool = True
    prometheus_port: int = 9090
    enable_json_export: bool = True
    export_interval: int = 60  # seconds

@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MetricSeries:
    """Time series of metric data"""
    name: str
    metric_type: MetricType
    points: deque = field(default_factory=lambda: deque(maxlen=10000))
    unit: str = ""
    description: str = ""

    def add_point(self, value: float, timestamp: float = None, labels: Dict[str, str] = None):
        """Add a data point"""
        point = MetricPoint(
            timestamp=timestamp or time.time(),
            value=value,
            labels=labels or {}
        )
        self.points.append(point)

    def get_recent(self, seconds: int = 60) -> List[MetricPoint]:
        """Get recent points within time window"""
        cutoff_time = time.time() - seconds
        return [p for p in self.points if p.timestamp >= cutoff_time]

    def get_stats(self, seconds: int = 60) -> Dict[str, float]:
        """Get statistics for recent points"""
        recent_points = self.get_recent(seconds)
        if not recent_points:
            return {}

        values = [p.value for p in recent_points]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": statistics.mean(values),
            "median": statistics.median(values),
            "p95": np.percentile(values, 95),
            "p99": np.percentile(values, 99),
            "sum": sum(values)
        }

@dataclass
class Alert:
    """Alert definition"""
    id: str
    name: str
    severity: AlertSeverity
    condition: str  # Expression to evaluate
    threshold: float
    metric_name: str
    enabled: bool = True
    cooldown_until: float = 0.0
    triggered_count: int = 0
    last_triggered: Optional[float] = None

@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""
    # Request metrics
    total_requests: int = 0
    requests_per_second: float = 0.0
    average_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0

    # Error metrics
    error_count: int = 0
    error_rate: float = 0.0
    status_codes: Dict[int, int] = field(default_factory=dict)

    # System metrics
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_mb: float = 0.0
    disk_usage_percent: float = 0.0
    network_io: Dict[str, float] = field(default_factory=dict)

    # Application metrics
    active_connections: int = 0
    queue_sizes: Dict[str, int] = field(default_factory=dict)
    cache_hit_rate: float = 0.0
    database_connections: int = 0

class MetricsCollector:
    """Advanced metrics collection system"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.metrics: Dict[str, MetricSeries] = {}
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)

        # Prometheus metrics
        if config.enable_prometheus:
            self._setup_prometheus_metrics()

        # Collection tasks
        self.collection_task: Optional[asyncio.Task] = None
        self.alert_task: Optional[asyncio.Task] = None
        self.export_task: Optional[asyncio.Task] = None

        # Alerts
        self.alerts: Dict[str, Alert] = {}
        self.alert_handlers: List[Callable] = []

        # WebSocket connections for real-time updates
        self.websocket_connections: Set[WebSocket] = set()

        # Storage
        self.redis: Optional[aioredis.Redis] = None

    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics"""
        self.prom_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        self.prom_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )
        self.prom_active_connections = Gauge(
            'active_connections',
            'Number of active connections'
        )
        self.prom_memory_usage = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes'
        )
        self.prom_cpu_usage = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage'
        )

    async def initialize(self):
        """Initialize metrics collector"""
        if self.config.enable_redis_storage:
            self.redis = await aioredis.from_url(self.config.redis_url)

        # Start collection tasks
        self.collection_task = asyncio.create_task(self._metrics_collection_loop())
        self.alert_task = asyncio.create_task(self._alert_check_loop())
        self.export_task = asyncio.create_task(self._export_loop())

        # Setup default alerts
        self._setup_default_alerts()

    async def shutdown(self):
        """Shutdown metrics collector"""
        if self.collection_task:
            self.collection_task.cancel()
        if self.alert_task:
            self.alert_task.cancel()
        if self.export_task:
            self.export_task.cancel()

        await asyncio.gather(
            self.collection_task,
            self.alert_task,
            self.export_task,
            return_exceptions=True
        )

    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Increment counter metric"""
        self.counters[name] += value
        self._ensure_metric_series(name, MetricType.COUNTER)
        self.metrics[name].add_point(self.counters[name], labels=labels)

        # Update Prometheus
        if hasattr(self, 'prom_requests_total') and name == 'requests_total':
            self.prom_requests_total.labels(
                method=labels.get('method', 'unknown'),
                endpoint=labels.get('endpoint', 'unknown'),
                status=labels.get('status', '200')
            ).inc(value)

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set gauge metric"""
        self.gauges[name] = value
        self._ensure_metric_series(name, MetricType.GAUGE)
        self.metrics[name].add_point(value, labels=labels)

        # Update Prometheus
        if hasattr(self, 'prom_memory_usage') and name == 'memory_mb':
            self.prom_memory_usage.set(value * 1024 * 1024)
        elif hasattr(self, 'prom_cpu_usage') and name == 'cpu_percent':
            self.prom_cpu_usage.set(value)

    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record histogram metric"""
        self.histograms[name].append(value)
        self._ensure_metric_series(name, MetricType.HISTOGRAM)
        self.metrics[name].add_point(value, labels=labels)

        # Update Prometheus
        if hasattr(self, 'prom_request_duration') and name == 'response_time':
            self.prom_request_duration.labels(
                method=labels.get('method', 'unknown'),
                endpoint=labels.get('endpoint', 'unknown')
            ).observe(value)

    def _ensure_metric_series(self, name: str, metric_type: MetricType):
        """Ensure metric series exists"""
        if name not in self.metrics:
            self.metrics[name] = MetricSeries(
                name=name,
                metric_type=metric_type,
                points=deque(maxlen=self.config.max_metrics_points)
            )

    def record_request(self, method: str, endpoint: str, status_code: int, response_time: float):
        """Record HTTP request metrics"""
        self.increment_counter('requests_total', 1.0, {
            'method': method,
            'endpoint': endpoint,
            'status': str(status_code)
        })

        self.record_histogram('response_time', response_time, {
            'method': method,
            'endpoint': endpoint
        })

        if status_code >= 400:
            self.increment_counter('errors_total', 1.0, {
                'method': method,
                'endpoint': endpoint,
                'status': str(status_code)
            })

    async def _metrics_collection_loop(self):
        """Main metrics collection loop"""
        while True:
            try:
                await self._collect_system_metrics()
                await self._collect_application_metrics()
                await self._broadcast_realtime_updates()
                await asyncio.sleep(self.config.metrics_collection_interval)
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(1.0)

    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        self.set_gauge('cpu_percent', cpu_percent)

        # Memory metrics
        memory = psutil.virtual_memory()
        self.set_gauge('memory_percent', memory.percent)
        self.set_gauge('memory_mb', memory.used / 1024 / 1024)

        # Disk metrics
        disk = psutil.disk_usage('/')
        self.set_gauge('disk_usage_percent', disk.percent)

        # Network metrics
        network = psutil.net_io_counters()
        self.set_gauge('network_bytes_sent', network.bytes_sent)
        self.set_gauge('network_bytes_recv', network.bytes_recv)

    async def _collect_application_metrics(self):
        """Collect application-level metrics"""
        # Calculate requests per second
        recent_requests = self.metrics.get('requests_total')
        if recent_requests:
            recent_points = recent_requests.get_recent(60)
            if len(recent_points) >= 2:
                time_diff = recent_points[-1].timestamp - recent_points[0].timestamp
                if time_diff > 0:
                    requests_diff = recent_points[-1].value - recent_points[0].value
                    rps = requests_diff / time_diff
                    self.set_gauge('requests_per_second', rps)

        # Calculate error rate
        total_requests = self.counters.get('requests_total', 0)
        total_errors = self.counters.get('errors_total', 0)
        if total_requests > 0:
            error_rate = (total_errors / total_requests) * 100
            self.set_gauge('error_rate', error_rate)

        # Response time statistics
        response_times = self.histograms.get('response_time', [])
        if response_times:
            self.set_gauge('avg_response_time', statistics.mean(response_times[-1000:]))
            if len(response_times) >= 100:
                self.set_gauge('p95_response_time', np.percentile(response_times[-1000:], 95))
                self.set_gauge('p99_response_time', np.percentile(response_times[-1000:], 99))

    async def _broadcast_realtime_updates(self):
        """Broadcast real-time metrics to WebSocket clients"""
        if not self.config.enable_realtime_monitoring:
            return

        if not self.websocket_connections:
            return

        # Prepare current metrics
        current_metrics = self.get_current_metrics()

        # Broadcast to all connected clients
        message = json.dumps({
            'type': 'metrics_update',
            'timestamp': time.time(),
            'data': current_metrics
        })

        disconnected = set()
        for ws in self.websocket_connections.copy():
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.add(ws)

        # Remove disconnected clients
        self.websocket_connections -= disconnected

    async def _alert_check_loop(self):
        """Alert checking loop"""
        while True:
            try:
                if self.config.enable_alerts:
                    await self._check_alerts()
                await asyncio.sleep(self.config.alert_check_interval)
            except Exception as e:
                logger.error(f"Alert check error: {e}")
                await asyncio.sleep(1.0)

    async def _check_alerts(self):
        """Check all alert conditions"""
        current_time = time.time()

        for alert in self.alerts.values():
            if not alert.enabled:
                continue

            # Check cooldown
            if current_time < alert.cooldown_until:
                continue

            # Get current metric value
            metric_series = self.metrics.get(alert.metric_name)
            if not metric_series or not metric_series.points:
                continue

            current_value = metric_series.points[-1].value

            # Evaluate condition
            triggered = False
            if alert.condition == 'greater_than':
                triggered = current_value > alert.threshold
            elif alert.condition == 'less_than':
                triggered = current_value < alert.threshold
            elif alert.condition == 'equals':
                triggered = current_value == alert.threshold

            if triggered:
                await self._trigger_alert(alert, current_value, current_time)

    async def _trigger_alert(self, alert: Alert, current_value: float, timestamp: float):
        """Trigger an alert"""
        alert.triggered_count += 1
        alert.last_triggered = timestamp
        alert.cooldown_until = timestamp + self.config.alert_cooldown_seconds

        alert_data = {
            'alert_id': alert.id,
            'name': alert.name,
            'severity': alert.severity.value,
            'metric': alert.metric_name,
            'threshold': alert.threshold,
            'current_value': current_value,
            'timestamp': timestamp,
            'triggered_count': alert.triggered_count
        }

        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert_data)
                else:
                    await asyncio.get_event_loop().run_in_executor(None, handler, alert_data)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")

        # Broadcast to WebSocket clients
        if self.websocket_connections:
            message = json.dumps({
                'type': 'alert',
                'data': alert_data
            })

            disconnected = set()
            for ws in self.websocket_connections.copy():
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.add(ws)

            self.websocket_connections -= disconnected

    async def _export_loop(self):
        """Metrics export loop"""
        while True:
            try:
                await self._export_metrics()
                await asyncio.sleep(self.config.export_interval)
            except Exception as e:
                logger.error(f"Export error: {e}")
                await asyncio.sleep(10)

    async def _export_metrics(self):
        """Export metrics to various formats"""
        # Export to Redis
        if self.config.enable_redis_storage and self.redis:
            await self._export_to_redis()

        # Export to file
        if self.config.enable_file_storage:
            await self._export_to_file()

    async def _export_to_redis(self):
        """Export metrics to Redis"""
        if not self.redis:
            return

        try:
            # Export current metrics snapshot
            current_metrics = self.get_current_metrics()
            await self.redis.setex(
                'api_metrics_current',
                self.config.metrics_retention_seconds,
                json.dumps(current_metrics)
            )

            # Export time series data (sampled)
            for name, series in self.metrics.items():
                recent_points = series.get_recent(300)  # Last 5 minutes
                if recent_points:
                    key = f'metrics_series:{name}'
                    data = [
                        {'timestamp': p.timestamp, 'value': p.value, 'labels': p.labels}
                        for p in recent_points
                    ]
                    await self.redis.setex(
                        key,
                        self.config.metrics_retention_seconds,
                        json.dumps(data)
                    )

        except Exception as e:
            logger.error(f"Redis export error: {e}")

    async def _export_to_file(self):
        """Export metrics to file"""
        try:
            current_metrics = self.get_current_metrics()
            export_data = {
                'timestamp': time.time(),
                'metrics': current_metrics
            }

            async with aiofiles.open(self.config.storage_file_path, 'a') as f:
                await f.write(json.dumps(export_data) + '\n')

        except Exception as e:
            logger.error(f"File export error: {e}")

    def _setup_default_alerts(self):
        """Setup default alert rules"""
        default_alerts = [
            Alert(
                id='high_response_time',
                name='High Response Time',
                severity=AlertSeverity.WARNING,
                condition='greater_than',
                threshold=self.config.response_time_warning_ms / 1000,
                metric_name='avg_response_time'
            ),
            Alert(
                id='critical_response_time',
                name='Critical Response Time',
                severity=AlertSeverity.CRITICAL,
                condition='greater_than',
                threshold=self.config.response_time_critical_ms / 1000,
                metric_name='avg_response_time'
            ),
            Alert(
                id='high_error_rate',
                name='High Error Rate',
                severity=AlertSeverity.WARNING,
                condition='greater_than',
                threshold=self.config.error_rate_warning_percent,
                metric_name='error_rate'
            ),
            Alert(
                id='high_memory_usage',
                name='High Memory Usage',
                severity=AlertSeverity.WARNING,
                condition='greater_than',
                threshold=self.config.memory_warning_mb,
                metric_name='memory_mb'
            ),
            Alert(
                id='high_cpu_usage',
                name='High CPU Usage',
                severity=AlertSeverity.WARNING,
                condition='greater_than',
                threshold=self.config.cpu_warning_percent,
                metric_name='cpu_percent'
            )
        ]

        for alert in default_alerts:
            self.alerts[alert.id] = alert

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current snapshot of all metrics"""
        return {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'request_metrics': self._get_request_metrics(),
            'system_metrics': self._get_system_metrics(),
            'alert_summary': self._get_alert_summary()
        }

    def _get_request_metrics(self) -> Dict[str, Any]:
        """Get request-related metrics"""
        return {
            'total_requests': int(self.counters.get('requests_total', 0)),
            'requests_per_second': self.gauges.get('requests_per_second', 0),
            'average_response_time': self.gauges.get('avg_response_time', 0),
            'p95_response_time': self.gauges.get('p95_response_time', 0),
            'p99_response_time': self.gauges.get('p99_response_time', 0),
            'error_rate': self.gauges.get('error_rate', 0),
            'total_errors': int(self.counters.get('errors_total', 0))
        }

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system-related metrics"""
        return {
            'cpu_percent': self.gauges.get('cpu_percent', 0),
            'memory_percent': self.gauges.get('memory_percent', 0),
            'memory_mb': self.gauges.get('memory_mb', 0),
            'disk_usage_percent': self.gauges.get('disk_usage_percent', 0),
            'network_bytes_sent': self.gauges.get('network_bytes_sent', 0),
            'network_bytes_recv': self.gauges.get('network_bytes_recv', 0)
        }

    def _get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary"""
        total_alerts = len(self.alerts)
        enabled_alerts = sum(1 for a in self.alerts.values() if a.enabled)
        triggered_today = sum(
            1 for a in self.alerts.values()
            if a.last_triggered and (time.time() - a.last_triggered) < 86400
        )

        return {
            'total_alerts': total_alerts,
            'enabled_alerts': enabled_alerts,
            'triggered_today': triggered_today,
            'active_alerts': len([a for a in self.alerts.values() if time.time() < a.cooldown_until])
        }

    def get_metric_history(self, metric_name: str, seconds: int = 3600) -> Dict[str, Any]:
        """Get historical data for a specific metric"""
        series = self.metrics.get(metric_name)
        if not series:
            return {}

        points = series.get_recent(seconds)
        return {
            'name': metric_name,
            'type': series.metric_type.value,
            'unit': series.unit,
            'description': series.description,
            'points': [
                {
                    'timestamp': p.timestamp,
                    'value': p.value,
                    'labels': p.labels
                }
                for p in points
            ],
            'stats': series.get_stats(seconds)
        }

    def add_alert_handler(self, handler: Callable):
        """Add custom alert handler"""
        self.alert_handlers.append(handler)

    def add_alert(self, alert: Alert):
        """Add custom alert"""
        self.alerts[alert.id] = alert

    def remove_alert(self, alert_id: str):
        """Remove alert"""
        self.alerts.pop(alert_id, None)

class MonitoringAPI:
    """FastAPI endpoints for monitoring"""

    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    def register_routes(self, app: FastAPI):
        """Register monitoring endpoints"""

        @app.get("/monitoring/metrics")
        async def get_metrics():
            """Get current metrics"""
            return self.collector.get_current_metrics()

        @app.get("/monitoring/metrics/{metric_name}")
        async def get_metric_history(metric_name: str, seconds: int = 3600):
            """Get metric history"""
            return self.collector.get_metric_history(metric_name, seconds)

        @app.get("/monitoring/alerts")
        async def get_alerts():
            """Get all alerts"""
            return {
                'alerts': [asdict(alert) for alert in self.collector.alerts.values()]
            }

        @app.post("/monitoring/alerts")
        async def create_alert(alert: Alert):
            """Create new alert"""
            self.collector.add_alert(alert)
            return {'status': 'created', 'alert_id': alert.id}

        @app.delete("/monitoring/alerts/{alert_id}")
        async def delete_alert(alert_id: str):
            """Delete alert"""
            self.collector.remove_alert(alert_id)
            return {'status': 'deleted'}

        @app.get("/monitoring/prometheus")
        async def prometheus_metrics():
            """Prometheus metrics endpoint"""
            if self.collector.config.enable_prometheus:
                return Response(generate_latest(), media_type="text/plain")
            else:
                raise HTTPException(status_code=404, detail="Prometheus metrics disabled")

        @app.websocket("/monitoring/realtime")
        async def websocket_endpoint(websocket: WebSocket):
            """Real-time metrics WebSocket"""
            await websocket.accept()
            self.collector.websocket_connections.add(websocket)

            try:
                # Send initial metrics
                current_metrics = self.collector.get_current_metrics()
                await websocket.send_text(json.dumps({
                    'type': 'initial_metrics',
                    'data': current_metrics
                }))

                # Keep connection alive
                while True:
                    try:
                        await websocket.receive_text()
                    except WebSocketDisconnect:
                        break
            except WebSocketDisconnect:
                pass
            finally:
                self.collector.websocket_connections.discard(websocket)

        @app.get("/monitoring/health")
        async def health_check():
            """Health check endpoint"""
            return {
                'status': 'healthy',
                'timestamp': time.time(),
                'metrics': {
                    'total_requests': int(self.collector.counters.get('requests_total', 0)),
                    'error_rate': self.collector.gauges.get('error_rate', 0),
                    'avg_response_time': self.collector.gauges.get('avg_response_time', 0),
                    'cpu_percent': self.collector.gauges.get('cpu_percent', 0),
                    'memory_mb': self.collector.gauges.get('memory_mb', 0)
                }
            }

# Middleware for automatic request monitoring
class MonitoringMiddleware:
    """FastAPI middleware for automatic request monitoring"""

    def __init__(self, app, collector: MetricsCollector):
        self.app = app
        self.collector = collector

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()

        # Process request
        await self.app(scope, receive, send)

        # Calculate metrics
        processing_time = time.perf_counter() - start_time

        # Record metrics (would need to extract method, endpoint, status from request/response)
        self.collector.record_request(
            method=scope.get('method', 'unknown'),
            endpoint=scope.get('path', 'unknown'),
            status_code=200,  # Would need to get actual status
            response_time=processing_time
        )

if __name__ == "__main__":
    # Example usage
    async def main():
        config = MonitoringConfig()
        collector = MetricsCollector(config)
        await collector.initialize()

        # Create FastAPI app
        app = FastAPI()
        monitoring_api = MonitoringAPI(collector)
        monitoring_api.register_routes(app)

        # Add middleware
        app.add_middleware(MonitoringMiddleware, collector=collector)

        # Add custom alert handler
        async def alert_handler(alert_data):
            print(f"ALERT: {alert_data['name']} - {alert_data['current_value']} (threshold: {alert_data['threshold']})")

        collector.add_alert_handler(alert_handler)

        # Simulate some metrics
        for i in range(10):
            collector.record_request('GET', '/api/test', 200, 0.1 + (i % 3) * 0.05)
            await asyncio.sleep(0.1)

        print("Current metrics:", collector.get_current_metrics())

        await collector.shutdown()

    asyncio.run(main())