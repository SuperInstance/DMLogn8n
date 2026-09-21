#!/usr/bin/env python3
"""
Messaging System Monitoring - Comprehensive monitoring and metrics collection.

This module provides monitoring capabilities including:
- Real-time metrics collection
- Performance monitoring
- Health checks
- Alert management
- Dashboard data aggregation
- Log analysis
- Resource monitoring
"""

import asyncio
import json
import logging
import time
import psutil
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import threading
import statistics

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class Metric:
    """Metric data structure."""
    name: str
    value: Union[int, float]
    metric_type: MetricType
    timestamp: float = field(default_factory=time.time)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Alert:
    """Alert data structure."""
    id: str
    name: str
    severity: AlertSeverity
    message: str
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    resolved_at: Optional[float] = None
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Health check result."""
    component: str
    status: HealthStatus
    message: str
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None


@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    load_average: Optional[List[float]] = None
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """Collects and manages metrics."""

    def __init__(self, retention_period: int = 3600):  # 1 hour
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.retention_period = retention_period
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric."""
        with self._lock:
            self.counters[name] += value
            self._record_metric(name, self.counters[name], MetricType.COUNTER, labels or {})

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric."""
        with self._lock:
            self.gauges[name] = value
            self._record_metric(name, value, MetricType.GAUGE, labels or {})

    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram metric."""
        with self._lock:
            self.histograms[name].append(value)
            # Keep only last 10000 values
            if len(self.histograms[name]) > 10000:
                self.histograms[name] = self.histograms[name][-10000:]

    def record_timer(self, name: str, duration_ms: float, labels: Dict[str, str] = None):
        """Record a timer metric."""
        with self._lock:
            self.timers[name].append(duration_ms)
            # Keep only last 10000 values
            if len(self.timers[name]) > 10000:
                self.timers[name] = self.timers[name][-10000:]

    def _record_metric(self, name: str, value: Union[int, float], metric_type: MetricType, labels: Dict[str, str]):
        """Record a metric with timestamp."""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels,
            timestamp=time.time()
        )
        key = f"{name}:{hash(frozenset(labels.items()))}"
        self.metrics[key].append(metric)

    def get_metric(self, name: str, labels: Dict[str, str] = None) -> List[Metric]:
        """Get metrics for a specific name and labels."""
        if labels:
            key = f"{name}:{hash(frozenset(labels.items()))}"
            return list(self.metrics.get(key, []))
        else:
            # Return all metrics with this name
            result = []
            for key, metrics in self.metrics.items():
                if key.startswith(f"{name}:"):
                    result.extend(metrics)
            return result

    def get_counter_value(self, name: str) -> int:
        """Get current counter value."""
        return self.counters.get(name, 0)

    def get_gauge_value(self, name: str) -> float:
        """Get current gauge value."""
        return self.gauges.get(name, 0.0)

    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics."""
        values = self.histograms.get(name, [])
        if not values:
            return {}

        return {
            "count": len(values),
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "p95": self._percentile(values, 0.95),
            "p99": self._percentile(values, 0.99)
        }

    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """Get timer statistics."""
        return self.get_histogram_stats(name)

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        current_time = time.time()
        cutoff_time = current_time - self.retention_period

        with self._lock:
            for key, metric_list in self.metrics.items():
                # Filter out old metrics
                while metric_list and metric_list[0].timestamp < cutoff_time:
                    metric_list.popleft()

    def get_all_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        with self._lock:
            summary = {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {},
                "timers": {}
            }

            for name in self.histograms:
                summary["histograms"][name] = self.get_histogram_stats(name)

            for name in self.timers:
                summary["timers"][name] = self.get_timer_stats(name)

            return summary


class AlertManager:
    """Manages alerts and notifications."""

    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: List[Dict[str, Any]] = []
        self.notification_handlers: List[Callable] = []
        self.alert_history: deque = deque(maxlen=1000)
        self._lock = threading.Lock()

    def add_alert_rule(self, name: str, condition: Callable, severity: AlertSeverity,
                      message_template: str, labels: Dict[str, str] = None):
        """Add an alert rule."""
        rule = {
            "name": name,
            "condition": condition,
            "severity": severity,
            "message_template": message_template,
            "labels": labels or {}
        }
        self.alert_rules.append(rule)

    def add_notification_handler(self, handler: Callable):
        """Add a notification handler."""
        self.notification_handlers.append(handler)

    def check_alert_rules(self, metrics_collector: MetricsCollector):
        """Check all alert rules against current metrics."""
        for rule in self.alert_rules:
            try:
                # Evaluate condition
                should_alert = rule["condition"](metrics_collector)

                alert_id = rule["name"]
                current_time = time.time()

                if should_alert:
                    if alert_id not in self.alerts:
                        # Create new alert
                        message = rule["message_template"].format(
                            **metrics_collector.get_all_metrics_summary()
                        )

                        alert = Alert(
                            id=alert_id,
                            name=rule["name"],
                            severity=rule["severity"],
                            message=message,
                            labels=rule["labels"]
                        )

                        with self._lock:
                            self.alerts[alert_id] = alert
                            self.alert_history.append(alert)

                        # Send notifications
                        self._send_notifications(alert)

                else:
                    # Resolve alert if it exists
                    if alert_id in self.alerts:
                        with self._lock:
                            self.alerts[alert_id].resolved = True
                            self.alerts[alert_id].resolved_at = current_time
                            self.alert_history.append(self.alerts[alert_id])
                            del self.alerts[alert_id]

                        # Send resolved notification
                        self._send_notifications(self.alerts[alert_id])

            except Exception as e:
                logger.error(f"Error checking alert rule {rule['name']}: {str(e)}")

    def _send_notifications(self, alert: Alert):
        """Send notifications for an alert."""
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in notification handler: {str(e)}")

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        with self._lock:
            return list(self.alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history."""
        with self._lock:
            return list(self.alert_history)[-limit:]

    def resolve_alert(self, alert_id: str):
        """Manually resolve an alert."""
        if alert_id in self.alerts:
            with self._lock:
                self.alerts[alert_id].resolved = True
                self.alerts[alert_id].resolved_at = time.time()
                self.alert_history.append(self.alerts[alert_id])
                del self.alerts[alert_id]

            self._send_notifications(self.alerts[alert_id])


class HealthChecker:
    """Manages health checks."""

    def __init__(self):
        self.health_checks: Dict[str, Callable] = {}
        self.health_results: Dict[str, HealthCheck] = {}
        self._lock = threading.Lock()

    def register_health_check(self, name: str, check_func: Callable):
        """Register a health check."""
        self.health_checks[name] = check_func

    async def run_health_check(self, name: str) -> HealthCheck:
        """Run a specific health check."""
        if name not in self.health_checks:
            return HealthCheck(
                component=name,
                status=HealthStatus.UNKNOWN,
                message="Health check not found"
            )

        start_time = time.time()
        try:
            check_func = self.health_checks[name]
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()

            duration_ms = (time.time() - start_time) * 1000

            if isinstance(result, tuple):
                status, message, details = result
            elif isinstance(result, dict):
                status = HealthStatus(result.get("status", "unknown"))
                message = result.get("message", "")
                details = result.get("details", {})
            else:
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = "Check passed" if result else "Check failed"
                details = {}

            health_check = HealthCheck(
                component=name,
                status=status,
                message=message,
                details=details,
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            health_check = HealthCheck(
                component=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check error: {str(e)}",
                duration_ms=duration_ms
            )

        with self._lock:
            self.health_results[name] = health_check

        return health_check

    async def run_all_health_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks."""
        results = {}
        tasks = []

        for name in self.health_checks:
            task = asyncio.create_task(self.run_health_check(name))
            tasks.append((name, task))

        for name, task in tasks:
            try:
                results[name] = await task
            except Exception as e:
                results[name] = HealthCheck(
                    component=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check execution error: {str(e)}"
                )

        return results

    def get_overall_health_status(self) -> HealthStatus:
        """Get overall health status."""
        with self._lock:
            if not self.health_results:
                return HealthStatus.UNKNOWN

            statuses = [check.status for check in self.health_results.values()]

            if all(status == HealthStatus.HEALTHY for status in statuses):
                return HealthStatus.HEALTHY
            elif any(status == HealthStatus.CRITICAL for status in statuses):
                return HealthStatus.CRITICAL
            elif any(status == HealthStatus.UNHEALTHY for status in statuses):
                return HealthStatus.UNHEALTHY
            else:
                return HealthStatus.DEGRADED

    def get_health_results(self) -> Dict[str, HealthCheck]:
        """Get current health check results."""
        with self._lock:
            return self.health_results.copy()


class SystemMonitor:
    """Monitors system resources."""

    def __init__(self):
        self.monitoring_enabled = True
        self.monitoring_interval = 30  # seconds
        self._monitor_task: Optional[asyncio.Task] = None
        self.system_metrics_history: deque = deque(maxlen=1000)

    async def start_monitoring(self):
        """Start system monitoring."""
        if not self.monitoring_enabled:
            return

        self._monitor_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """Stop system monitoring."""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_enabled:
            try:
                metrics = await self.collect_system_metrics()
                self.system_metrics_history.append(metrics)
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in system monitoring loop: {str(e)}")
                await asyncio.sleep(5)

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)

            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            disk_used_gb = disk.used / (1024 * 1024 * 1024)
            disk_free_gb = disk.free / (1024 * 1024 * 1024)

            # Network metrics
            network = psutil.net_io_counters()

            # Process count
            process_count = len(psutil.pids())

            # Load average (Unix only)
            load_avg = None
            if hasattr(psutil, 'getloadavg'):
                load_avg = list(psutil.getloadavg())

            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_used_gb=disk_used_gb,
                disk_free_gb=disk_free_gb,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                process_count=process_count,
                load_average=load_avg,
                timestamp=time.time()
            )

        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                disk_used_gb=0.0,
                disk_free_gb=0.0,
                network_bytes_sent=0,
                network_bytes_recv=0,
                process_count=0,
                timestamp=time.time()
            )

    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get most recent system metrics."""
        if self.system_metrics_history:
            return self.system_metrics_history[-1]
        return None

    def get_metrics_history(self, limit: int = 100) -> List[SystemMetrics]:
        """Get system metrics history."""
        return list(self.system_metrics_history)[-limit:]


class MonitoringDashboard:
    """Provides dashboard data aggregation."""

    def __init__(self, metrics_collector: MetricsCollector, alert_manager: AlertManager,
                 health_checker: HealthChecker, system_monitor: SystemMonitor):
        self.metrics_collector = metrics_collector
        self.alert_manager = alert_manager
        self.health_checker = health_checker
        self.system_monitor = system_monitor

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        return {
            "timestamp": time.time(),
            "metrics": self.metrics_collector.get_all_metrics_summary(),
            "alerts": {
                "active": [asdict(alert) for alert in self.alert_manager.get_active_alerts()],
                "total_active": len(self.alert_manager.get_active_alerts()),
                "critical_count": len([
                    a for a in self.alert_manager.get_active_alerts()
                    if a.severity == AlertSeverity.CRITICAL
                ])
            },
            "health": {
                "overall_status": self.health_checker.get_overall_health_status().value,
                "checks": {
                    name: {
                        "status": check.status.value,
                        "message": check.message,
                        "duration_ms": check.duration_ms,
                        "timestamp": check.timestamp
                    }
                    for name, check in self.health_checker.get_health_results().items()
                }
            },
            "system": {
                "current": asdict(self.system_monitor.get_current_metrics()) if self.system_monitor.get_current_metrics() else None,
                "history": [
                    asdict(metrics) for metrics in self.system_monitor.get_metrics_history(10)
                ]
            }
        }

    async def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        metrics_data = []

        # Counter metrics
        for name, value in self.metrics_collector.counters.items():
            metrics_data.append(f"dmlogn8n_counter_{name} {value}")

        # Gauge metrics
        for name, value in self.metrics_collector.gauges.items():
            metrics_data.append(f"dmlogn8n_gauge_{name} {value}")

        # Histogram metrics
        for name, stats in self.metrics_collector.histograms.items():
            if stats:
                metrics_data.append(f"dmlogn8n_histogram_{name}_sum {stats.get('sum', 0)}")
                metrics_data.append(f"dmlogn8n_histogram_{name}_count {stats.get('count', 0)}")
                metrics_data.append(f"dmlogn8n_histogram_{name}_mean {stats.get('mean', 0)}")

        # System metrics
        system_metrics = self.system_monitor.get_current_metrics()
        if system_metrics:
            metrics_data.append(f"dmlogn8n_system_cpu_percent {system_metrics.cpu_percent}")
            metrics_data.append(f"dmlogn8n_system_memory_percent {system_metrics.memory_percent}")
            metrics_data.append(f"dmlogn8n_system_disk_usage_percent {system_metrics.disk_usage_percent}")

        return "\n".join(metrics_data)


# Default notification handlers
def console_notification_handler(alert: Alert):
    """Simple console notification handler."""
    status = "RESOLVED" if alert.resolved else "ALERT"
    print(f"[{status.upper()}] {alert.name} ({alert.severity.value.upper()}): {alert.message}")
    if alert.resolved and alert.resolved_at:
        print(f"  Resolved at: {time.ctime(alert.resolved_at)}")


def log_notification_handler(alert: Alert):
    """Logging notification handler."""
    if alert.resolved:
        logger.info(f"Alert resolved: {alert.name} - {alert.message}")
    else:
        log_level = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.ERROR: logger.error,
            AlertSeverity.CRITICAL: logger.critical
        }.get(alert.severity, logger.info)

        log_level(f"Alert: {alert.name} ({alert.severity.value}) - {alert.message}")


# Global monitoring instance
_global_monitoring_instance = None


def get_monitoring_instance() -> 'MonitoringService':
    """Get or create the global monitoring instance."""
    global _global_monitoring_instance
    if _global_monitoring_instance is None:
        _global_monitoring_instance = MonitoringService()
    return _global_monitoring_instance


class MonitoringService:
    """Main monitoring service class."""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.health_checker = HealthChecker()
        self.system_monitor = SystemMonitor()
        self.dashboard = MonitoringDashboard(
            self.metrics_collector, self.alert_manager, self.health_checker, self.system_monitor
        )

        # Add default notification handlers
        self.alert_manager.add_notification_handler(console_notification_handler)
        self.alert_manager.add_notification_handler(log_notification_handler)

        # Add default alert rules
        self._setup_default_alert_rules()

        # Register default health checks
        self._setup_default_health_checks()

        self._monitoring_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the monitoring service."""
        await self.system_monitor.start_monitoring()
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Monitoring service started")

    async def stop(self):
        """Stop the monitoring service."""
        await self.system_monitor.stop_monitoring()
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Monitoring service stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while True:
            try:
                # Check alert rules
                self.alert_manager.check_alert_rules(self.metrics_collector)

                # Cleanup old metrics
                self.metrics_collector.cleanup_old_metrics()

                await asyncio.sleep(10)  # Check every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(5)

    def _setup_default_alert_rules(self):
        """Setup default alert rules."""
        # High error rate alert
        def high_error_rate(metrics: MetricsCollector) -> bool:
            total_errors = metrics.get_counter_value("messages_failed")
            total_messages = metrics.get_counter_value("messages_processed")
            if total_messages > 0:
                error_rate = total_errors / total_messages
                return error_rate > 0.05  # 5% error rate
            return False

        self.alert_manager.add_alert_rule(
            "high_error_rate",
            high_error_rate,
            AlertSeverity.ERROR,
            "High error rate detected: {error_rate:.2%}",
            {"component": "messaging"}
        )

        # System CPU usage alert
        def high_cpu_usage(metrics: MetricsCollector) -> bool:
            system_metrics = self.system_monitor.get_current_metrics()
            return system_metrics.cpu_percent > 80 if system_metrics else False

        self.alert_manager.add_alert_rule(
            "high_cpu_usage",
            high_cpu_usage,
            AlertSeverity.WARNING,
            "High CPU usage: {cpu_percent:.1f}%",
            {"component": "system"}
        )

        # System memory usage alert
        def high_memory_usage(metrics: MetricsCollector) -> bool:
            system_metrics = self.system_monitor.get_current_metrics()
            return system_metrics.memory_percent > 90 if system_metrics else False

        self.alert_manager.add_alert_rule(
            "high_memory_usage",
            high_memory_usage,
            AlertSeverity.CRITICAL,
            "High memory usage: {memory_percent:.1f}%",
            {"component": "system"}
        )

    def _setup_default_health_checks(self):
        """Setup default health checks."""
        # System health check
        async def system_health_check():
            try:
                system_metrics = self.system_monitor.get_current_metrics()
                if not system_metrics:
                    return HealthStatus.UNHEALTHY, "No system metrics available"

                if system_metrics.cpu_percent > 95 or system_metrics.memory_percent > 95:
                    return HealthStatus.UNHEALTHY, "System resources critically high"
                elif system_metrics.cpu_percent > 80 or system_metrics.memory_percent > 80:
                    return HealthStatus.DEGRADED, "System resources high"
                else:
                    return HealthStatus.HEALTHY, "System resources normal"

            except Exception as e:
                return HealthStatus.UNHEALTHY, f"System health check error: {str(e)}"

        self.health_checker.register_health_check("system", system_health_check)


# Export main classes
__all__ = [
    'MetricType',
    'AlertSeverity',
    'HealthStatus',
    'Metric',
    'Alert',
    'HealthCheck',
    'SystemMetrics',
    'MetricsCollector',
    'AlertManager',
    'HealthChecker',
    'SystemMonitor',
    'MonitoringDashboard',
    'MonitoringService',
    'get_monitoring_instance',
    'console_notification_handler',
    'log_notification_handler'
]