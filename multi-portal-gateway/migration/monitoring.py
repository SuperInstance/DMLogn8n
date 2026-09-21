#!/usr/bin/env python3
"""
Migration Monitoring and Progress Tracking
Real-time monitoring system for data migration operations
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import psutil
import threading
from collections import defaultdict, deque

from migration_engine import MigrationProgress, MigrationStatus

logger = logging.getLogger("migration_monitoring")

class MetricType(Enum):
    """Types of metrics collected"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Metric:
    """Single metric data point"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""

@dataclass
class Alert:
    """Alert notification"""
    id: str
    level: AlertLevel
    title: str
    message: str
    source: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_io: Dict[str, float]
    process_count: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class MigrationMetrics:
    """Migration-specific metrics"""
    migration_id: str
    records_per_second: float
    bytes_per_second: float
    error_rate: float
    success_rate: float
    estimated_completion: Optional[datetime]
    current_table: str
    phase: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class MetricsCollector:
    """Collects and stores metrics"""

    def __init__(self, max_metrics: int = 10000):
        self.metrics: deque = deque(maxlen=max_metrics)
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()

    def increment_counter(self, name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        with self.lock:
            self.counters[name] += value
            metric = Metric(
                name=name,
                value=self.counters[name],
                metric_type=MetricType.COUNTER,
                tags=tags or {}
            )
            self.metrics.append(metric)

    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric"""
        with self.lock:
            self.gauges[name] = value
            metric = Metric(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,
                tags=tags or {}
            )
            self.metrics.append(metric)

    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram value"""
        with self.lock:
            self.histograms[name].append(value)
            # Keep only last 1000 values per histogram
            if len(self.histograms[name]) > 1000:
                self.histograms[name] = self.histograms[name][-1000:]

            metric = Metric(
                name=name,
                value=value,
                metric_type=MetricType.HISTOGRAM,
                tags=tags or {}
            )
            self.metrics.append(metric)

    def record_timer(self, name: str, duration: float, tags: Dict[str, str] = None):
        """Record a timer value"""
        with self.lock:
            self.timers[name].append(duration)
            # Keep only last 1000 values per timer
            if len(self.timers[name]) > 1000:
                self.timers[name] = self.timers[name][-1000:]

            metric = Metric(
                name=name,
                value=duration,
                metric_type=MetricType.TIMER,
                unit="seconds",
                tags=tags or {}
            )
            self.metrics.append(metric)

    def get_recent_metrics(self, name: str, since: datetime = None, limit: int = 100) -> List[Metric]:
        """Get recent metrics for a specific name"""
        with self.lock:
            if since is None:
                since = datetime.now(timezone.utc) - timedelta(hours=1)

            filtered = [
                m for m in self.metrics
                if m.name == name and m.timestamp >= since
            ]
            return filtered[-limit:]

    def get_metric_summary(self, name: str, metric_type: MetricType = None) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        with self.lock:
            if metric_type == MetricType.HISTOGRAM and name in self.histograms:
                values = self.histograms[name]
                if values:
                    return {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "p50": self._percentile(values, 50),
                        "p95": self._percentile(values, 95),
                        "p99": self._percentile(values, 99)
                    }
            elif metric_type == MetricType.TIMER and name in self.timers:
                values = self.timers[name]
                if values:
                    return {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "p50": self._percentile(values, 50),
                        "p95": self._percentile(values, 95),
                        "p99": self._percentile(values, 99)
                    }
            elif name in self.counters:
                return {"value": self.counters[name]}
            elif name in self.gauges:
                return {"value": self.gauges[name]}

            return {}

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

class AlertManager:
    """Manages alert notifications"""

    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: List[Callable] = []
        self.alert_handlers: List[Callable] = []
        self.lock = threading.Lock()

    def add_alert_rule(self, rule_func: Callable):
        """Add an alert rule function"""
        self.alert_rules.append(rule_func)

    def add_alert_handler(self, handler_func: Callable):
        """Add an alert handler function"""
        self.alert_handlers.append(handler_func)

    def create_alert(self, level: AlertLevel, title: str, message: str, source: str,
                    tags: Dict[str, str] = None) -> Alert:
        """Create a new alert"""
        alert_id = f"{source}_{int(time.time())}"
        alert = Alert(
            id=alert_id,
            level=level,
            title=title,
            message=message,
            source=source,
            tags=tags or {}
        )

        with self.lock:
            self.alerts[alert_id] = alert

        # Send to handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

        return alert

    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        with self.lock:
            if alert_id in self.alerts:
                self.alerts[alert_id].resolved = True
                self.alerts[alert_id].resolved_at = datetime.now(timezone.utc)

    def get_active_alerts(self, level: AlertLevel = None) -> List[Alert]:
        """Get active alerts"""
        with self.lock:
            alerts = [
                alert for alert in self.alerts.values()
                if not alert.resolved
            ]

            if level:
                alerts = [a for a in alerts if a.level == level]

            return sorted(alerts, key=lambda a: a.timestamp, reverse=True)

class MigrationMonitor:
    """Main migration monitoring system"""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.active_migrations: Dict[str, MigrationProgress] = {}
        self.system_monitoring_enabled = True
        self.monitoring_interval = 5  # seconds
        self.monitoring_task = None
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)

        # Setup default alert rules
        self._setup_default_alert_rules()

        # Setup default alert handlers
        self._setup_default_alert_handlers()

    def _setup_default_alert_rules(self):
        """Setup default alert rules"""
        self.alert_manager.add_alert_rule(self._check_error_rate)
        self.alert_manager.add_alert_rule(self._check_performance)
        self.alert_manager.add_alert_rule(self._check_system_resources)

    def _setup_default_alert_handlers(self):
        """Setup default alert handlers"""
        self.alert_manager.add_alert_handler(self._log_alert)
        self.alert_manager.add_alert_handler(self._store_alert)

    def _log_alert(self, alert: Alert):
        """Log alert to console"""
        log_message = f"[{alert.level.value.upper()}] {alert.title}: {alert.message}"
        if alert.level == AlertLevel.CRITICAL:
            logger.critical(log_message)
        elif alert.level == AlertLevel.ERROR:
            logger.error(log_message)
        elif alert.level == AlertLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)

    def _store_alert(self, alert: Alert):
        """Store alert in metrics collector"""
        self.metrics_collector.increment_counter(
            "alerts_total",
            tags={"level": alert.level.value, "source": alert.source}
        )

    def _check_error_rate(self) -> Optional[Alert]:
        """Check for high error rates"""
        recent_metrics = self.metrics_collector.get_recent_metrics(
            "migration_errors",
            since=datetime.now(timezone.utc) - timedelta(minutes=5)
        )

        if recent_metrics:
            total_errors = sum(m.value for m in recent_metrics)
            if total_errors > 10:
                return self.alert_manager.create_alert(
                    level=AlertLevel.ERROR,
                    title="High Error Rate",
                    message=f"Detected {total_errors} errors in the last 5 minutes",
                    source="migration_monitor",
                    tags={"error_count": str(total_errors)}
                )

        return None

    def _check_performance(self) -> Optional[Alert]:
        """Check for performance issues"""
        recent_metrics = self.metrics_collector.get_recent_metrics(
            "migration_duration",
            since=datetime.now(timezone.utc) - timedelta(minutes=10)
        )

        if recent_metrics:
            avg_duration = sum(m.value for m in recent_metrics) / len(recent_metrics)
            if avg_duration > 30:  # 30 seconds threshold
                return self.alert_manager.create_alert(
                    level=AlertLevel.WARNING,
                    title="Slow Migration Performance",
                    message=f"Average operation duration: {avg_duration:.2f}s",
                    source="migration_monitor",
                    tags={"avg_duration": str(avg_duration)}
                )

        return None

    def _check_system_resources(self) -> Optional[Alert]:
        """Check system resource usage"""
        if not self.system_monitoring_enabled:
            return None

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        if cpu_percent > 90:
            return self.alert_manager.create_alert(
                level=AlertLevel.CRITICAL,
                title="High CPU Usage",
                message=f"CPU usage: {cpu_percent}%",
                source="system_monitor",
                tags={"cpu_percent": str(cpu_percent)}
            )

        if memory.percent > 90:
            return self.alert_manager.create_alert(
                level=AlertLevel.CRITICAL,
                title="High Memory Usage",
                message=f"Memory usage: {memory.percent}%",
                source="system_monitor",
                tags={"memory_percent": str(memory.percent)}
            )

        return None

    async def start_monitoring(self):
        """Start the monitoring loop"""
        if self.monitoring_task is None:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("Migration monitoring started")

    async def stop_monitoring(self):
        """Stop the monitoring loop"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
            logger.info("Migration monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                # Check system metrics
                if self.system_monitoring_enabled:
                    system_metrics = self._collect_system_metrics()
                    self._record_system_metrics(system_metrics)

                # Check active migrations
                await self._monitor_active_migrations()

                # Check alert rules
                for rule in self.alert_manager.alert_rules:
                    try:
                        alert = rule()
                        if alert:
                            logger.info(f"Alert generated: {alert.title}")
                    except Exception as e:
                        logger.error(f"Alert rule failed: {e}")

                await asyncio.sleep(self.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.monitoring_interval)

    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system performance metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        process_count = len(psutil.pids())

        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_gb=memory.used / (1024**3),
            memory_total_gb=memory.total / (1024**3),
            disk_usage_percent=disk.percent,
            disk_free_gb=disk.free / (1024**3),
            network_io={
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            },
            process_count=process_count
        )

    def _record_system_metrics(self, metrics: SystemMetrics):
        """Record system metrics"""
        self.metrics_collector.set_gauge("system_cpu_percent", metrics.cpu_percent)
        self.metrics_collector.set_gauge("system_memory_percent", metrics.memory_percent)
        self.metrics_collector.set_gauge("system_memory_used_gb", metrics.memory_used_gb)
        self.metrics_collector.set_gauge("system_disk_usage_percent", metrics.disk_usage_percent)
        self.metrics_collector.set_gauge("system_disk_free_gb", metrics.disk_free_gb)
        self.metrics_collector.set_gauge("system_process_count", metrics.process_count)

    async def _monitor_active_migrations(self):
        """Monitor active migrations"""
        for migration_id, progress in self.active_migrations.items():
            await self._update_migration_metrics(progress)

    async def _update_migration_metrics(self, progress: MigrationProgress):
        """Update migration-specific metrics"""
        if progress.total_records > 0 and progress.start_time:
            # Calculate records per second
            elapsed = (datetime.now(timezone.utc) - progress.start_time).total_seconds()
            if elapsed > 0:
                rps = progress.processed_records / elapsed
                self.metrics_collector.set_gauge(
                    "migration_records_per_second",
                    rps,
                    tags={"migration_id": progress.migration_id}
                )

            # Calculate success rate
            total = progress.processed_records + progress.failed_records
            if total > 0:
                success_rate = progress.processed_records / total * 100
                self.metrics_collector.set_gauge(
                    "migration_success_rate",
                    success_rate,
                    tags={"migration_id": progress.migration_id}
                )

        # Record phase changes
        self.metrics_collector.set_gauge(
            "migration_phase",
            1.0 if progress.status == MigrationStatus.COMPLETED else 0.0,
            tags={"migration_id": progress.migration_id, "status": progress.status.value}
        )

    async def update_progress(self, progress: MigrationProgress):
        """Update migration progress"""
        self.active_migrations[progress.migration_id] = progress

        # Record metrics
        self.metrics_collector.set_gauge(
            "migration_progress_percentage",
            (progress.processed_records / progress.total_records * 100) if progress.total_records > 0 else 0,
            tags={"migration_id": progress.migration_id, "table": progress.current_table or ""}
        )

        self.metrics_collector.set_gauge(
            "migration_total_records",
            progress.total_records,
            tags={"migration_id": progress.migration_id}
        )

        self.metrics_collector.set_gauge(
            "migration_processed_records",
            progress.processed_records,
            tags={"migration_id": progress.migration_id}
        )

        if progress.failed_records > 0:
            self.metrics_collector.increment_counter(
                "migration_errors",
                progress.failed_records,
                tags={"migration_id": progress.migration_id}
            )

        # Trigger callbacks
        for callback in self.callbacks.get("progress_update", []):
            try:
                await callback(progress)
            except Exception as e:
                logger.error(f"Progress callback failed: {e}")

    def add_callback(self, event: str, callback: Callable):
        """Add event callback"""
        self.callbacks[event].append(callback)

    def remove_callback(self, event: str, callback: Callable):
        """Remove event callback"""
        if callback in self.callbacks[event]:
            self.callbacks[event].remove(callback)

    def get_metrics_summary(self, since: datetime = None) -> Dict[str, Any]:
        """Get metrics summary"""
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(hours=1)

        summary = {
            "since": since.isoformat(),
            "counters": {},
            "gauges": {},
            "histograms": {},
            "timers": {}
        }

        # Get all metric names
        metric_names = set(m.name for m in self.metrics_collector.metrics if m.timestamp >= since)

        for name in metric_names:
            metric_summary = self.metrics_collector.get_metric_summary(name)
            if metric_summary:
                # Determine metric type
                if name in self.metrics_collector.counters:
                    summary["counters"][name] = metric_summary
                elif name in self.metrics_collector.gauges:
                    summary["gauges"][name] = metric_summary
                elif name in self.metrics_collector.histograms:
                    summary["histograms"][name] = metric_summary
                elif name in self.metrics_collector.timers:
                    summary["timers"][name] = metric_summary

        return summary

    def get_migration_status(self, migration_id: str = None) -> Dict[str, Any]:
        """Get migration status"""
        if migration_id:
            progress = self.active_migrations.get(migration_id)
            if progress:
                return asdict(progress)
            else:
                return {"error": "Migration not found"}
        else:
            return {
                "active_migrations": len(self.active_migrations),
                "migrations": {
                    mig_id: {
                        "status": progress.status.value,
                        "progress": (progress.processed_records / progress.total_records * 100) if progress.total_records > 0 else 0,
                        "current_table": progress.current_table,
                        "errors": len(progress.errors)
                    }
                    for mig_id, progress in self.active_migrations.items()
                }
            }

    def get_alerts_summary(self) -> Dict[str, Any]:
        """Get alerts summary"""
        active_alerts = self.alert_manager.get_active_alerts()
        alerts_by_level = defaultdict(int)

        for alert in active_alerts:
            alerts_by_level[alert.level.value] += 1

        return {
            "total_active": len(active_alerts),
            "by_level": dict(alerts_by_level),
            "recent_alerts": [
                {
                    "id": alert.id,
                    "level": alert.level.value,
                    "title": alert.title,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in active_alerts[:10]  # Last 10 alerts
            ]
        }

    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        if format.lower() == "json":
            summary = self.get_metrics_summary()
            return json.dumps(summary, indent=2, default=str)
        elif format.lower() == "prometheus":
            return self._export_prometheus_format()
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []

        # Export counters
        for name, value in self.metrics_collector.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")

        # Export gauges
        for name, value in self.metrics_collector.gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")

        return "\n".join(lines)

# Example usage and testing
async def test_migration_monitoring():
    """Test migration monitoring system"""
    monitor = MigrationMonitor()

    try:
        # Start monitoring
        await monitor.start_monitoring()

        # Simulate migration progress
        from migration_engine import MigrationProgress, MigrationStatus

        progress = MigrationProgress(
            migration_id="test_migration",
            status=MigrationStatus.MIGRATING,
            start_time=datetime.now(timezone.utc),
            total_records=1000,
            processed_records=0,
            failed_records=0,
            current_table="characters"
        )

        # Update progress over time
        for i in range(10):
            progress.processed_records = (i + 1) * 100
            progress.current_table = f"table_{i + 1}"
            await monitor.update_progress(progress)

            # Record some custom metrics
            monitor.metrics_collector.record_timer("operation_duration", 0.5 + i * 0.1)
            monitor.metrics_collector.increment_counter("operations_completed", 10)

            await asyncio.sleep(1)

        # Get summaries
        metrics_summary = monitor.get_metrics_summary()
        status = monitor.get_migration_status()
        alerts = monitor.get_alerts_summary()

        print("Metrics Summary:")
        print(json.dumps(metrics_summary, indent=2, default=str)[:500] + "...")

        print(f"\nMigration Status: {json.dumps(status, indent=2)}")
        print(f"Alerts Summary: {json.dumps(alerts, indent=2)}")

        # Test alert creation
        alert = monitor.alert_manager.create_alert(
            level=AlertLevel.WARNING,
            title="Test Alert",
            message="This is a test alert",
            source="test"
        )
        print(f"Created alert: {alert.title}")

    finally:
        await monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(test_migration_monitoring())