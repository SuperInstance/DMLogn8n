"""
Error Monitoring and Alerting System

Provides comprehensive monitoring of errors, metrics collection,
and alerting capabilities for the error handling system.
"""

import time
import threading
import logging
import json
import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from .error_classifier import ErrorInfo, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class MetricType(Enum):
    """Types of metrics to track."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class ErrorMetric:
    """Error metric data point."""
    timestamp: float
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    component: Optional[str]
    endpoint: Optional[str]
    user_id: Optional[str]
    recovery_attempted: bool
    recovery_successful: bool
    response_time: Optional[float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    """Alert rule definition."""
    name: str
    description: str
    condition: Callable[[Dict[str, Any]], bool]
    level: AlertLevel
    enabled: bool = True
    cooldown: float = 300.0  # Cooldown period in seconds
    last_triggered: Optional[float] = None
    notification_channels: List[str] = field(default_factory=list)


@dataclass
class Alert:
    """Alert instance."""
    id: str
    rule_name: str
    level: AlertLevel
    message: str
    timestamp: float
    resolved: bool = False
    resolved_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time."""
    timestamp: float
    total_errors: int
    errors_by_category: Dict[str, int]
    errors_by_severity: Dict[str, int]
    errors_by_component: Dict[str, int]
    recovery_rate: float
    avg_response_time: float
    active_circuit_breakers: int
    open_circuits: int


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert notification."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test notification channel connectivity."""
        pass


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel."""

    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str,
                 from_email: str, to_emails: List[str]):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via email."""
        try:
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[{alert.level.value}] {alert.rule_name}"

            body = f"""
Alert: {alert.rule_name}
Level: {alert.level.value}
Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.timestamp))}
Message: {alert.message}

Additional Information:
{json.dumps(alert.metadata, indent=2)}
            """

            msg.attach(MimeText(body, 'plain'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Email alert sent for {alert.rule_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False

    def test_connection(self) -> bool:
        """Test SMTP connection."""
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
            return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel."""

    def __init__(self, webhook_url: str, channel: Optional[str] = None):
        self.webhook_url = webhook_url
        self.channel = channel

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to Slack."""
        try:
            import aiohttp

            color_map = {
                AlertLevel.INFO: "good",
                AlertLevel.WARNING: "warning",
                AlertLevel.ERROR: "danger",
                AlertLevel.CRITICAL: "danger"
            }

            payload = {
                "attachments": [{
                    "color": color_map.get(alert.level, "warning"),
                    "title": f"Alert: {alert.rule_name}",
                    "text": alert.message,
                    "fields": [
                        {"title": "Level", "value": alert.level.value, "short": True},
                        {"title": "Time", "value": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.timestamp)), "short": True}
                    ],
                    "footer": "DMLogn8n Error Monitor",
                    "ts": int(alert.timestamp)
                }]
            }

            if self.channel:
                payload["channel"] = self.channel

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent for {alert.rule_name}")
                        return True
                    else:
                        logger.error(f"Slack alert failed: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False

    def test_connection(self) -> bool:
        """Test Slack webhook connection."""
        try:
            import requests

            payload = {"text": "Test message from DMLogn8n Error Monitor"}
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Slack webhook test failed: {e}")
            return False


class WebhookNotificationChannel(NotificationChannel):
    """Generic webhook notification channel."""

    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via webhook."""
        try:
            import aiohttp

            payload = asdict(alert)
            headers = {"Content-Type": "application/json", **self.headers}

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload, headers=headers) as response:
                    if 200 <= response.status < 300:
                        logger.info(f"Webhook alert sent for {alert.rule_name}")
                        return True
                    else:
                        logger.error(f"Webhook alert failed: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False

    def test_connection(self) -> bool:
        """Test webhook connection."""
        try:
            import requests

            test_payload = {"test": True, "message": "Test from DMLogn8n Error Monitor"}
            headers = {"Content-Type": "application/json", **self.headers}
            response = requests.post(self.webhook_url, json=test_payload, headers=headers, timeout=10)
            return 200 <= response.status < 300

        except Exception as e:
            logger.error(f"Webhook test failed: {e}")
            return False


class MetricsCollector:
    """Collects and manages error metrics."""

    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        self._metrics: deque = deque(maxlen=max_history_size)
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._lock = threading.RLock()

    def record_error(self, error_info: ErrorInfo, recovery_attempted: bool = False,
                    recovery_successful: bool = False, response_time: Optional[float] = None,
                    **metadata) -> None:
        """Record an error metric."""
        with self._lock:
            metric = ErrorMetric(
                timestamp=time.time(),
                error_id=f"ERR_{int(time.time() * 1000)}",
                category=error_info.category,
                severity=error_info.severity,
                component=error_info.context.get("component"),
                endpoint=error_info.context.get("operation"),
                user_id=error_info.context.get("user_id"),
                recovery_attempted=recovery_attempted,
                recovery_successful=recovery_successful,
                response_time=response_time,
                metadata=metadata
            )

            self._metrics.append(metric)
            self._counters[f"errors.{error_info.category.value}"] += 1
            self._counters[f"errors.{error_info.severity.value}"] += 1
            self._counters["errors.total"] += 1

            if response_time:
                self._timers["error.response_time"].append(response_time)

            logger.debug(f"Recorded error metric: {error_info.category.value}")

    def get_snapshot(self, time_window: Optional[float] = None) -> MetricSnapshot:
        """Get a snapshot of current metrics."""
        with self._lock:
            if not self._metrics:
                return MetricSnapshot(
                    timestamp=time.time(),
                    total_errors=0,
                    errors_by_category={},
                    errors_by_severity={},
                    errors_by_component={},
                    recovery_rate=0.0,
                    avg_response_time=0.0,
                    active_circuit_breakers=0,
                    open_circuits=0
                )

            # Filter metrics by time window if specified
            metrics = list(self._metrics)
            if time_window:
                cutoff_time = time.time() - time_window
                metrics = [m for m in metrics if m.timestamp >= cutoff_time]

            # Calculate statistics
            errors_by_category = defaultdict(int)
            errors_by_severity = defaultdict(int)
            errors_by_component = defaultdict(int)
            recovery_attempts = 0
            recovery_successes = 0
            response_times = []

            for metric in metrics:
                errors_by_category[metric.category.value] += 1
                errors_by_severity[metric.severity.value] += 1
                if metric.component:
                    errors_by_component[metric.component] += 1
                if metric.recovery_attempted:
                    recovery_attempts += 1
                if metric.recovery_successful:
                    recovery_successes += 1
                if metric.response_time:
                    response_times.append(metric.response_time)

            recovery_rate = recovery_successes / recovery_attempts if recovery_attempts > 0 else 0.0
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0

            return MetricSnapshot(
                timestamp=time.time(),
                total_errors=len(metrics),
                errors_by_category=dict(errors_by_category),
                errors_by_severity=dict(errors_by_severity),
                errors_by_component=dict(errors_by_component),
                recovery_rate=recovery_rate,
                avg_response_time=avg_response_time,
                active_circuit_breakers=self._counters.get("circuit_breakers.active", 0),
                open_circuits=self._counters.get("circuit_breakers.open", 0)
            )

    def get_counter(self, name: str) -> int:
        """Get counter value."""
        with self._lock:
            return self._counters.get(name, 0)

    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment counter."""
        with self._lock:
            self._counters[name] += value

    def set_gauge(self, name: str, value: float) -> None:
        """Set gauge value."""
        with self._lock:
            self._gauges[name] = value

    def get_gauge(self, name: str) -> Optional[float]:
        """Get gauge value."""
        with self._lock:
            return self._gauges.get(name)

    def record_timer(self, name: str, value: float) -> None:
        """Record timer value."""
        with self._lock:
            self._timers[name].append(value)

    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """Get timer statistics."""
        with self._lock:
            if name not in self._timers or not self._timers[name]:
                return {}

            values = list(self._timers[name])
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "p50": sorted(values)[len(values) // 2],
                "p95": sorted(values)[int(len(values) * 0.95)],
                "p99": sorted(values)[int(len(values) * 0.99)]
            }


class AlertManager:
    """Manages alert rules and notifications."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self._rules: Dict[str, AlertRule] = {}
        self._alerts: deque = deque(maxlen=1000)
        self._notification_channels: Dict[str, NotificationChannel] = {}
        self._lock = threading.RLock()

        # Register default alert rules
        self._register_default_rules()

    def _register_default_rules(self) -> None:
        """Register default alert rules."""
        default_rules = [
            AlertRule(
                name="high_error_rate",
                description="High error rate detected",
                condition=lambda metrics: metrics["total_errors"] > 100,
                level=AlertLevel.WARNING,
                cooldown=300.0
            ),
            AlertRule(
                name="critical_errors",
                description="Critical errors detected",
                condition=lambda metrics: metrics["errors_by_severity"].get("CRITICAL", 0) > 0,
                level=AlertLevel.CRITICAL,
                cooldown=60.0
            ),
            AlertRule(
                name="low_recovery_rate",
                description="Low recovery rate",
                condition=lambda metrics: metrics.get("recovery_rate", 1.0) < 0.5 and metrics["total_errors"] > 10,
                level=AlertLevel.ERROR,
                cooldown=600.0
            ),
            AlertRule(
                name="circuit_breaker_open",
                description="Circuit breakers are open",
                condition=lambda metrics: metrics.get("open_circuits", 0) > 0,
                level=AlertLevel.WARNING,
                cooldown=180.0
            ),
            AlertRule(
                name="slow_response_times",
                description="Slow error response times",
                condition=lambda metrics: metrics.get("avg_response_time", 0) > 5.0,
                level=AlertLevel.WARNING,
                cooldown=300.0
            )
        ]

        for rule in default_rules:
            self._rules[rule.name] = rule
            logger.info(f"Registered default alert rule: {rule.name}")

    def add_rule(self, rule: AlertRule) -> None:
        """Add alert rule."""
        with self._lock:
            self._rules[rule.name] = rule
            logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_name: str) -> bool:
        """Remove alert rule."""
        with self._lock:
            if rule_name in self._rules:
                del self._rules[rule_name]
                logger.info(f"Removed alert rule: {rule_name}")
                return True
            return False

    def add_notification_channel(self, name: str, channel: NotificationChannel) -> None:
        """Add notification channel."""
        with self._lock:
            self._notification_channels[name] = channel
            logger.info(f"Added notification channel: {name}")

    def evaluate_rules(self, time_window: float = 300.0) -> List[Alert]:
        """Evaluate all alert rules and return triggered alerts."""
        snapshot = self.metrics_collector.get_snapshot(time_window)
        metrics = asdict(snapshot)

        triggered_alerts = []

        with self._lock:
            for rule in self._rules.values():
                if not rule.enabled:
                    continue

                # Check cooldown
                if rule.last_triggered and (time.time() - rule.last_triggered) < rule.cooldown:
                    continue

                try:
                    if rule.condition(metrics):
                        # Create alert
                        alert = Alert(
                            id=f"ALERT_{int(time.time() * 1000)}",
                            rule_name=rule.name,
                            level=rule.level,
                            message=f"{rule.description}: {json.dumps(metrics, indent=2)}",
                            timestamp=time.time(),
                            metadata={"snapshot": snapshot}
                        )

                        self._alerts.append(alert)
                        triggered_alerts.append(alert)
                        rule.last_triggered = time.time()

                        # Send notifications
                        asyncio.create_task(self._send_notifications(alert))

                        logger.warning(f"Alert triggered: {rule.name}")

                except Exception as e:
                    logger.error(f"Error evaluating alert rule {rule.name}: {e}")

        return triggered_alerts

    async def _send_notifications(self, alert: Alert) -> None:
        """Send alert notifications."""
        rule = self._rules.get(alert.rule_name)
        if not rule:
            return

        for channel_name in rule.notification_channels:
            if channel_name in self._notification_channels:
                channel = self._notification_channels[channel_name]
                try:
                    await channel.send_alert(alert)
                except Exception as e:
                    logger.error(f"Failed to send notification via {channel_name}: {e}")

    def get_recent_alerts(self, limit: int = 100) -> List[Alert]:
        """Get recent alerts."""
        with self._lock:
            return list(self._alerts)[-limit:]

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark alert as resolved."""
        with self._lock:
            for alert in self._alerts:
                if alert.id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolved_at = time.time()
                    logger.info(f"Alert resolved: {alert_id}")
                    return True
            return False


class ErrorMonitor:
    """
    Main error monitoring system that coordinates metrics collection and alerting.

    Features:
    - Real-time error metrics collection
    - Configurable alert rules
    - Multiple notification channels
    - Performance monitoring
    - Historical data analysis
    """

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager(self.metrics_collector)
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

    def start_monitoring(self, interval: float = 60.0) -> None:
        """Start background monitoring."""
        with self._lock:
            if self._monitoring:
                logger.warning("Monitoring already started")
                return

            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                args=(interval,),
                daemon=True
            )
            self._monitor_thread.start()
            logger.info(f"Error monitoring started with {interval}s interval")

    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        with self._lock:
            if not self._monitoring:
                return

            self._monitoring = False
            if self._monitor_thread:
                self._monitor_thread.join(timeout=10)
            logger.info("Error monitoring stopped")

    def _monitor_loop(self, interval: float) -> None:
        """Background monitoring loop."""
        while self._monitoring:
            try:
                # Evaluate alert rules
                alerts = self.alert_manager.evaluate_rules()
                if alerts:
                    logger.info(f"Generated {len(alerts)} alerts")

                # Sleep until next evaluation
                time.sleep(interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)

    def record_error(self, error_info: ErrorInfo, **kwargs) -> None:
        """Record an error for monitoring."""
        self.metrics_collector.record_error(error_info, **kwargs)

    def get_dashboard_data(self, time_window: float = 3600.0) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        snapshot = self.metrics_collector.get_snapshot(time_window)
        recent_alerts = self.alert_manager.get_recent_alerts(20)

        return {
            "snapshot": asdict(snapshot),
            "recent_alerts": [asdict(alert) for alert in recent_alerts],
            "timer_stats": {
                "error_response_time": self.metrics_collector.get_timer_stats("error.response_time")
            },
            "counters": {
                "errors_total": self.metrics_collector.get_counter("errors.total"),
                "circuit_breakers_active": self.metrics_collector.get_counter("circuit_breakers.active"),
                "circuit_breakers_open": self.metrics_collector.get_counter("circuit_breakers.open")
            },
            "gauges": {
                "active_connections": self.metrics_collector.get_gauge("active_connections"),
                "memory_usage": self.metrics_collector.get_gauge("memory_usage")
            }
        }


# Global error monitor instance
error_monitor = ErrorMonitor()