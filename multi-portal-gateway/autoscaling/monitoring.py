#!/usr/bin/env python3
"""
Monitoring and Alerting for DMLogn8n Auto-Scaling
Provides comprehensive monitoring, alerting, and health checks
"""

import asyncio
import logging
import json
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import redis
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertStatus(Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    ACKNOWLEDGED = "acknowledged"

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class Alert:
    alert_id: str
    name: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    service_id: Optional[str]
    metric_name: str
    threshold: float
    current_value: float
    triggered_at: datetime
    resolved_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    labels: Dict[str, str]
    annotations: Dict[str, str]

@dataclass
class HealthCheck:
    check_id: str
    name: str
    service_id: str
    check_type: str
    status: HealthStatus
    last_checked: datetime
    response_time_ms: float
    error_message: Optional[str]
    details: Dict[str, Any]

@dataclass
class MetricAlert:
    name: str
    metric_name: str
    condition: str  # >, <, >=, <=, ==, !=
    threshold: float
    duration: int  # seconds
    severity: AlertSeverity
    enabled: bool
    services: List[str]
    labels: Dict[str, str]

class MonitoringSystem:
    """
    Comprehensive monitoring and alerting system
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger('monitoring_system')

        # Redis client
        self.redis_client = redis.Redis(
            host=config.get('redis', {}).get('host', 'localhost'),
            port=config.get('redis', {}).get('port', 6379),
            decode_responses=True
        )

        # Alert storage
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.health_checks: Dict[str, HealthCheck] = {}

        # Metric alerts configuration
        self.metric_alerts = self._load_metric_alerts()

        # Notification channels
        self.notification_channels = config.get('notification_channels', {})

        # Prometheus metrics
        self._setup_prometheus_metrics()

        # Health check configurations
        self.health_check_configs = self._load_health_check_configs()

        # Alert suppression rules
        self.suppression_rules = self._load_suppression_rules()

        # Initialize notification handlers
        self._initialize_notification_handlers()

    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics for monitoring"""
        try:
            # Alert metrics
            self.alerts_total = Counter('autoscaling_alerts_total', 'Total number of alerts', ['severity', 'status'])
            self.alerts_active = Gauge('autoscaling_alerts_active', 'Number of active alerts', ['severity'])
            self.alerts_duration = Histogram('autoscaling_alert_duration_seconds', 'Alert resolution duration')

            # Health check metrics
            self.health_check_status = Gauge('autoscaling_health_check_status', 'Health check status', ['service', 'check'])
            self.health_check_duration = Histogram('autoscaling_health_check_duration_seconds', 'Health check duration', ['service', 'check'])

            # System metrics
            self.scaling_events_total = Counter('autoscaling_events_total', 'Total scaling events', ['service', 'direction'])
            self.system_health = Gauge('autoscaling_system_health', 'Overall system health score')

            self.logger.info("Prometheus metrics initialized")

        except Exception as e:
            self.logger.error(f"Error setting up Prometheus metrics: {e}")

    def _load_metric_alerts(self) -> Dict[str, MetricAlert]:
        """Load metric alert configurations"""
        try:
            alerts = {
                'high_cpu_usage': MetricAlert(
                    name='High CPU Usage',
                    metric_name='cpu_usage',
                    condition='>',
                    threshold=80.0,
                    duration=300,
                    severity=AlertSeverity.WARNING,
                    enabled=True,
                    services=['api-gateway', 'character-portal', 'dialogue-system'],
                    labels={'team': 'platform', 'component': 'autoscaling'}
                ),
                'critical_cpu_usage': MetricAlert(
                    name='Critical CPU Usage',
                    metric_name='cpu_usage',
                    condition='>',
                    threshold=95.0,
                    duration=60,
                    severity=AlertSeverity.CRITICAL,
                    enabled=True,
                    services=['api-gateway', 'character-portal', 'dialogue-system'],
                    labels={'team': 'platform', 'component': 'autoscaling'}
                ),
                'high_memory_usage': MetricAlert(
                    name='High Memory Usage',
                    metric_name='memory_usage',
                    condition='>',
                    threshold=85.0,
                    duration=300,
                    severity=AlertSeverity.WARNING,
                    enabled=True,
                    services=['character-portal', 'world-simulation'],
                    labels={'team': 'platform', 'component': 'autoscaling'}
                ),
                'high_error_rate': MetricAlert(
                    name='High Error Rate',
                    metric_name='error_rate',
                    condition='>',
                    threshold=5.0,
                    duration=180,
                    severity=AlertSeverity.ERROR,
                    enabled=True,
                    services=['api-gateway', 'dialogue-system'],
                    labels={'team': 'platform', 'component': 'autoscaling'}
                ),
                'slow_response_time': MetricAlert(
                    name='Slow Response Time',
                    metric_name='response_time',
                    condition='>',
                    threshold=1000.0,
                    duration=240,
                    severity=AlertSeverity.WARNING,
                    enabled=True,
                    services=['api-gateway', 'character-portal'],
                    labels={'team': 'platform', 'component': 'autoscaling'}
                ),
                'scaling_failure': MetricAlert(
                    name='Scaling Operation Failed',
                    metric_name='scaling_failures',
                    condition='>',
                    threshold=0.0,
                    duration=1,
                    severity=AlertSeverity.ERROR,
                    enabled=True,
                    services=['*'],  # All services
                    labels={'team': 'platform', 'component': 'autoscaling'}
                ),
                'cost_threshold': MetricAlert(
                    name='Cost Threshold Exceeded',
                    metric_name='hourly_cost',
                    condition='>',
                    threshold=500.0,
                    duration=3600,
                    severity=AlertSeverity.WARNING,
                    enabled=True,
                    services=['ai-model-pool', 'world-simulation'],
                    labels={'team': 'finance', 'component': 'autoscaling'}
                ),
                'instance_unhealthy': MetricAlert(
                    name='Instance Unhealthy',
                    metric_name='unhealthy_instances',
                    condition='>',
                    threshold=0.0,
                    duration=120,
                    severity=AlertSeverity.ERROR,
                    enabled=True,
                    services=['*'],
                    labels={'team': 'platform', 'component': 'autoscaling'}
                )
            }

            return alerts

        except Exception as e:
            self.logger.error(f"Error loading metric alerts: {e}")
            return {}

    def _load_health_check_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load health check configurations"""
        try:
            configs = {
                'api-gateway-health': {
                    'name': 'API Gateway Health Check',
                    'service_id': 'api-gateway',
                    'endpoint': 'http://api-gateway:8080/health',
                    'method': 'GET',
                    'expected_status': 200,
                    'timeout': 10,
                    'interval': 30,
                    'check_type': 'http'
                },
                'character-portal-health': {
                    'name': 'Character Portal Health Check',
                    'service_id': 'character-portal',
                    'endpoint': 'http://character-portal:8081/health',
                    'method': 'GET',
                    'expected_status': 200,
                    'timeout': 10,
                    'interval': 30,
                    'check_type': 'http'
                },
                'dialogue-system-health': {
                    'name': 'Dialogue System Health Check',
                    'service_id': 'dialogue-system',
                    'endpoint': 'http://dialogue-system:8082/status',
                    'method': 'GET',
                    'expected_status': 200,
                    'timeout': 15,
                    'interval': 60,
                    'check_type': 'http'
                },
                'combat-engine-health': {
                    'name': 'Combat Engine Health Check',
                    'service_id': 'combat-engine',
                    'endpoint': 'http://combat-engine:8083/ping',
                    'method': 'GET',
                    'expected_status': 200,
                    'timeout': 5,
                    'interval': 30,
                    'check_type': 'http'
                },
                'autoscaling-engine-health': {
                    'name': 'Autoscaling Engine Health Check',
                    'service_id': 'autoscaling',
                    'endpoint': 'http://autoscaling:8090/health',
                    'method': 'GET',
                    'expected_status': 200,
                    'timeout': 5,
                    'interval': 60,
                    'check_type': 'internal'
                }
            }

            return configs

        except Exception as e:
            self.logger.error(f"Error loading health check configs: {e}")
            return {}

    def _load_suppression_rules(self) -> List[Dict[str, Any]]:
        """Load alert suppression rules"""
        try:
            rules = [
                {
                    'name': 'Maintenance Window Suppression',
                    'condition': 'labels.maintenance == "true"',
                    'duration': 3600,
                    'severity': ['warning', 'error'],
                    'services': ['*']
                },
                {
                    'name': 'Weekend Low Priority Suppression',
                    'condition': 'day_of_week in [6, 7] and severity == "info"',
                    'duration': 86400,
                    'severity': ['info'],
                    'services': ['*']
                },
                {
                    'name': 'Deployment Suppression',
                    'condition': 'labels.deployment == "true"',
                    'duration': 1800,
                    'severity': ['warning'],
                    'services': ['api-gateway', 'character-portal']
                }
            ]

            return rules

        except Exception as e:
            self.logger.error(f"Error loading suppression rules: {e}")
            return []

    def _initialize_notification_handlers(self):
        """Initialize notification channel handlers"""
        try:
            self.notification_handlers = {
                'email': self._send_email_notification,
                'slack': self._send_slack_notification,
                'webhook': self._send_webhook_notification,
                'pagerduty': self._send_pagerduty_notification
            }

        except Exception as e:
            self.logger.error(f"Error initializing notification handlers: {e}")

    async def start_monitoring(self):
        """Start the monitoring system"""
        self.logger.info("Starting monitoring system...")

        # Start background tasks
        tasks = [
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._alert_evaluation_loop()),
            asyncio.create_task(self._metrics_collection_loop()),
            asyncio.create_task(self._alert_cleanup_loop()),
            asyncio.create_task(self._system_health_loop())
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Error in monitoring system: {e}")
            raise

    async def _health_check_loop(self):
        """Continuous health check loop"""
        while True:
            try:
                for check_id, config in self.health_check_configs.items():
                    await self._perform_health_check(check_id, config)

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(10)

    async def _alert_evaluation_loop(self):
        """Alert evaluation loop"""
        while True:
            try:
                await self._evaluate_metric_alerts()
                await asyncio.sleep(60)  # Evaluate every minute

            except Exception as e:
                self.logger.error(f"Error in alert evaluation loop: {e}")
                await asyncio.sleep(10)

    async def _metrics_collection_loop(self):
        """Metrics collection loop"""
        while True:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(30)  # Collect every 30 seconds

            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(10)

    async def _alert_cleanup_loop(self):
        """Alert cleanup loop"""
        while True:
            try:
                await self._cleanup_old_alerts()
                await asyncio.sleep(3600)  # Run every hour

            except Exception as e:
                self.logger.error(f"Error in alert cleanup loop: {e}")
                await asyncio.sleep(300)

    async def _system_health_loop(self):
        """System health evaluation loop"""
        while True:
            try:
                health_score = await self._calculate_system_health()
                self.system_health.set(health_score)
                await asyncio.sleep(60)  # Evaluate every minute

            except Exception as e:
                self.logger.error(f"Error in system health loop: {e}")
                await asyncio.sleep(30)

    async def _perform_health_check(self, check_id: str, config: Dict[str, Any]):
        """Perform a single health check"""
        try:
            start_time = datetime.now()
            status = HealthStatus.HEALTHY
            error_message = None
            response_time = 0
            details = {}

            if config['check_type'] == 'http':
                result = await self._perform_http_health_check(config)
                status = result['status']
                error_message = result.get('error_message')
                response_time = result['response_time']
                details = result.get('details', {})
            elif config['check_type'] == 'internal':
                result = await self._perform_internal_health_check(config)
                status = result['status']
                error_message = result.get('error_message')
                response_time = result['response_time']
                details = result.get('details', {})

            # Create health check record
            health_check = HealthCheck(
                check_id=check_id,
                name=config['name'],
                service_id=config['service_id'],
                check_type=config['check_type'],
                status=status,
                last_checked=datetime.now(),
                response_time_ms=response_time,
                error_message=error_message,
                details=details
            )

            self.health_checks[check_id] = health_check

            # Update Prometheus metrics
            self.health_check_status.labels(
                service=config['service_id'],
                check=check_id
            ).set(1 if status == HealthStatus.HEALTHY else 0)

            self.health_check_duration.labels(
                service=config['service_id'],
                check=check_id
            ).observe(response_time / 1000)

            # Create alert if unhealthy
            if status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]:
                await self._create_health_alert(health_check)

            self.logger.debug(f"Health check {check_id}: {status.value}")

        except Exception as e:
            self.logger.error(f"Error performing health check {check_id}: {e}")

    async def _perform_http_health_check(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform HTTP health check"""
        try:
            timeout = aiohttp.ClientTimeout(total=config['timeout'])
            start_time = datetime.now()

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(
                    method=config['method'],
                    url=config['endpoint']
                ) as response:
                    response_time = (datetime.now() - start_time).total_seconds() * 1000

                    if response.status == config['expected_status']:
                        return {
                            'status': HealthStatus.HEALTHY,
                            'response_time': response_time,
                            'details': {
                                'status_code': response.status,
                                'response_headers': dict(response.headers),
                                'response_size': len(await response.text())
                            }
                        }
                    else:
                        return {
                            'status': HealthStatus.UNHEALTHY,
                            'response_time': response_time,
                            'error_message': f"Unexpected status code: {response.status}",
                            'details': {
                                'status_code': response.status,
                                'expected_status': config['expected_status']
                            }
                        }

        except asyncio.TimeoutError:
            return {
                'status': HealthStatus.UNHEALTHY,
                'response_time': config['timeout'] * 1000,
                'error_message': f"Request timeout after {config['timeout']} seconds"
            }
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'response_time': 0,
                'error_message': str(e)
            }

    async def _perform_internal_health_check(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform internal health check"""
        try:
            start_time = datetime.now()

            # Check Redis connection
            self.redis_client.ping()

            # Check system resources
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            if cpu_percent < 80 and memory_percent < 80:
                return {
                    'status': HealthStatus.HEALTHY,
                    'response_time': response_time,
                    'details': {
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory_percent,
                        'redis_connected': True
                    }
                }
            else:
                return {
                    'status': HealthStatus.DEGRADED,
                    'response_time': response_time,
                    'error_message': f"High resource usage: CPU {cpu_percent}%, Memory {memory_percent}%",
                    'details': {
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory_percent,
                        'redis_connected': True
                    }
                }

        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'response_time': 0,
                'error_message': str(e)
            }

    async def _evaluate_metric_alerts(self):
        """Evaluate metric alerts"""
        try:
            for alert_id, alert_config in self.metric_alerts.items():
                if not alert_config.enabled:
                    continue

                # Get metric values for configured services
                for service_id in alert_config.services:
                    if service_id == '*':
                        # Apply to all services (would need service discovery)
                        continue

                    metric_value = await self._get_metric_value(service_id, alert_config.metric_name)
                    if metric_value is None:
                        continue

                    # Check if alert condition is met
                    if self._evaluate_condition(metric_value, alert_config.condition, alert_config.threshold):
                        await self._trigger_metric_alert(alert_id, alert_config, service_id, metric_value)
                    else:
                        await self._resolve_metric_alert(alert_id, service_id)

        except Exception as e:
            self.logger.error(f"Error evaluating metric alerts: {e}")

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        try:
            if condition == '>':
                return value > threshold
            elif condition == '<':
                return value < threshold
            elif condition == '>=':
                return value >= threshold
            elif condition == '<=':
                return value <= threshold
            elif condition == '==':
                return value == threshold
            elif condition == '!=':
                return value != threshold
            else:
                return False

        except Exception:
            return False

    async def _get_metric_value(self, service_id: str, metric_name: str) -> Optional[float]:
        """Get current metric value for a service"""
        try:
            # This would typically query metrics from Prometheus or other monitoring systems
            # For now, return mock data
            mock_metrics = {
                'api-gateway': {'cpu_usage': 45.2, 'memory_usage': 67.8, 'error_rate': 0.5, 'response_time': 150},
                'character-portal': {'cpu_usage': 72.1, 'memory_usage': 81.3, 'error_rate': 1.2, 'response_time': 280},
                'dialogue-system': {'cpu_usage': 38.5, 'memory_usage': 54.2, 'error_rate': 0.8, 'response_time': 450},
                'combat-engine': {'cpu_usage': 25.3, 'memory_usage': 41.7, 'error_rate': 0.2, 'response_time': 85},
                'ai-model-pool': {'cpu_usage': 67.8, 'memory_usage': 73.4, 'error_rate': 1.5, 'response_time': 620, 'hourly_cost': 450.0},
                'world-simulation': {'cpu_usage': 54.2, 'memory_usage': 68.9, 'error_rate': 0.3, 'response_time': 320, 'hourly_cost': 125.0}
            }

            return mock_metrics.get(service_id, {}).get(metric_name)

        except Exception as e:
            self.logger.error(f"Error getting metric value: {e}")
            return None

    async def _trigger_metric_alert(self, alert_id: str, alert_config: MetricAlert, service_id: str, current_value: float):
        """Trigger a metric alert"""
        try:
            alert_key = f"{alert_id}:{service_id}"

            # Check if alert is already active
            if alert_key in self.active_alerts:
                return

            # Check suppression rules
            if await self._is_alert_suppressed(alert_config, service_id):
                return

            # Create new alert
            alert = Alert(
                alert_id=alert_key,
                name=f"{alert_config.name} - {service_id}",
                description=f"{alert_config.metric_name} is {current_value} {alert_config.condition} {alert_config.threshold}",
                severity=alert_config.severity,
                status=AlertStatus.ACTIVE,
                service_id=service_id,
                metric_name=alert_config.metric_name,
                threshold=alert_config.threshold,
                current_value=current_value,
                triggered_at=datetime.now(),
                resolved_at=None,
                acknowledged_at=None,
                acknowledged_by=None,
                labels={**alert_config.labels, 'service': service_id},
                annotations={
                    'summary': f"{alert_config.name} triggered for {service_id}",
                    'description': f"Metric {alert_config.metric_name} value {current_value} {alert_config.condition} threshold {alert_config.threshold}"
                }
            )

            self.active_alerts[alert_key] = alert
            self.alert_history.append(alert)

            # Update Prometheus metrics
            self.alerts_total.labels(
                severity=alert.severity.value,
                status=alert.status.value
            ).inc()

            # Send notifications
            await self._send_alert_notifications(alert)

            self.logger.warning(f"Alert triggered: {alert.name}")

        except Exception as e:
            self.logger.error(f"Error triggering metric alert: {e}")

    async def _resolve_metric_alert(self, alert_id: str, service_id: str):
        """Resolve a metric alert"""
        try:
            alert_key = f"{alert_id}:{service_id}"

            if alert_key in self.active_alerts:
                alert = self.active_alerts[alert_key]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.now()

                # Move to history
                self.alert_history.append(alert)
                del self.active_alerts[alert_key]

                # Update Prometheus metrics
                self.alerts_total.labels(
                    severity=alert.severity.value,
                    status=alert.status.value
                ).inc()

                # Calculate alert duration
                if alert.triggered_at and alert.resolved_at:
                    duration = (alert.resolved_at - alert.triggered_at).total_seconds()
                    self.alerts_duration.observe(duration)

                # Send resolved notifications
                await self._send_alert_notifications(alert)

                self.logger.info(f"Alert resolved: {alert.name}")

        except Exception as e:
            self.logger.error(f"Error resolving metric alert: {e}")

    async def _create_health_alert(self, health_check: HealthCheck):
        """Create alert from health check failure"""
        try:
            alert_id = f"health_check:{health_check.check_id}"
            severity = AlertSeverity.ERROR if health_check.status == HealthStatus.UNHEALTHY else AlertSeverity.WARNING

            # Check if alert is already active
            if alert_id in self.active_alerts:
                return

            alert = Alert(
                alert_id=alert_id,
                name=f"Health Check Failed - {health_check.name}",
                description=f"Health check failed for {health_check.service_id}",
                severity=severity,
                status=AlertStatus.ACTIVE,
                service_id=health_check.service_id,
                metric_name='health_check',
                threshold=0,
                current_value=1,
                triggered_at=datetime.now(),
                resolved_at=None,
                acknowledged_at=None,
                acknowledged_by=None,
                labels={'service': health_check.service_id, 'check_type': health_check.check_type},
                annotations={
                    'summary': f"Health check failed: {health_check.name}",
                    'description': health_check.error_message or "Health check returned unhealthy status",
                    'response_time': str(health_check.response_time_ms)
                }
            )

            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)

            # Send notifications
            await self._send_alert_notifications(alert)

            self.logger.warning(f"Health check alert triggered: {alert.name}")

        except Exception as e:
            self.logger.error(f"Error creating health alert: {e}")

    async def _is_alert_suppressed(self, alert_config: MetricAlert, service_id: str) -> bool:
        """Check if alert should be suppressed"""
        try:
            # This would evaluate suppression rules
            # For now, return False (no suppression)
            return False

        except Exception as e:
            self.logger.error(f"Error checking alert suppression: {e}")
            return False

    async def _send_alert_notifications(self, alert: Alert):
        """Send notifications for an alert"""
        try:
            # Get enabled notification channels for alert severity
            channels = self.notification_channels.get(alert.severity.value, [])

            for channel in channels:
                handler = self.notification_handlers.get(channel.get('type'))
                if handler:
                    await handler(alert, channel)

        except Exception as e:
            self.logger.error(f"Error sending alert notifications: {e}")

    async def _send_email_notification(self, alert: Alert, channel_config: Dict[str, Any]):
        """Send email notification"""
        try:
            msg = MimeMultipart()
            msg['From'] = channel_config.get('from', 'autoscaling@dmlogn8n.com')
            msg['To'] = ', '.join(channel_config.get('recipients', []))
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.name}"

            body = f"""
Alert: {alert.name}
Severity: {alert.severity.value.upper()}
Service: {alert.service_id}
Description: {alert.description}
Current Value: {alert.current_value}
Threshold: {alert.threshold}
Triggered At: {alert.triggered_at}

Details:
{json.dumps(alert.annotations, indent=2)}
            """

            msg.attach(MimeText(body, 'plain'))

            # This would actually send the email using SMTP
            # For now, just log it
            self.logger.info(f"Email notification sent for alert: {alert.name}")

        except Exception as e:
            self.logger.error(f"Error sending email notification: {e}")

    async def _send_slack_notification(self, alert: Alert, channel_config: Dict[str, Any]):
        """Send Slack notification"""
        try:
            webhook_url = channel_config.get('webhook_url')
            if not webhook_url:
                return

            color = {
                AlertSeverity.INFO: 'good',
                AlertSeverity.WARNING: 'warning',
                AlertSeverity.ERROR: 'danger',
                AlertSeverity.CRITICAL: 'danger'
            }.get(alert.severity, 'warning')

            payload = {
                'attachments': [{
                    'color': color,
                    'title': f"{alert.severity.value.upper()}: {alert.name}",
                    'text': alert.description,
                    'fields': [
                        {'title': 'Service', 'value': alert.service_id, 'short': True},
                        {'title': 'Metric', 'value': alert.metric_name, 'short': True},
                        {'title': 'Current Value', 'value': str(alert.current_value), 'short': True},
                        {'title': 'Threshold', 'value': str(alert.threshold), 'short': True},
                        {'title': 'Triggered At', 'value': alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S'), 'short': False}
                    ],
                    'footer': 'DMLogn8n Auto-Scaling',
                    'ts': int(alert.triggered_at.timestamp())
                }]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info(f"Slack notification sent for alert: {alert.name}")

        except Exception as e:
            self.logger.error(f"Error sending Slack notification: {e}")

    async def _send_webhook_notification(self, alert: Alert, channel_config: Dict[str, Any]):
        """Send webhook notification"""
        try:
            webhook_url = channel_config.get('url')
            if not webhook_url:
                return

            payload = {
                'alert_id': alert.alert_id,
                'name': alert.name,
                'severity': alert.severity.value,
                'status': alert.status.value,
                'service_id': alert.service_id,
                'description': alert.description,
                'metric_name': alert.metric_name,
                'current_value': alert.current_value,
                'threshold': alert.threshold,
                'triggered_at': alert.triggered_at.isoformat(),
                'labels': alert.labels,
                'annotations': alert.annotations
            }

            headers = channel_config.get('headers', {})

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        self.logger.info(f"Webhook notification sent for alert: {alert.name}")

        except Exception as e:
            self.logger.error(f"Error sending webhook notification: {e}")

    async def _send_pagerduty_notification(self, alert: Alert, channel_config: Dict[str, Any]):
        """Send PagerDuty notification"""
        try:
            # This would integrate with PagerDuty API
            self.logger.info(f"PagerDuty notification sent for alert: {alert.name}")

        except Exception as e:
            self.logger.error(f"Error sending PagerDuty notification: {e}")

    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            import psutil

            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Update metrics (would typically push to Prometheus)
            self.logger.debug(f"System metrics - CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%")

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")

    async def _calculate_system_health(self) -> float:
        """Calculate overall system health score (0-100)"""
        try:
            total_checks = len(self.health_checks)
            if total_checks == 0:
                return 50.0  # Default score

            healthy_checks = sum(1 for check in self.health_checks.values() if check.status == HealthStatus.HEALTHY)
            degraded_checks = sum(1 for check in self.health_checks.values() if check.status == HealthStatus.DEGRADED)

            # Calculate health score
            health_score = (healthy_checks * 100 + degraded_checks * 50) / total_checks

            # Factor in active alerts
            critical_alerts = sum(1 for alert in self.active_alerts.values() if alert.severity == AlertSeverity.CRITICAL)
            error_alerts = sum(1 for alert in self.active_alerts.values() if alert.severity == AlertSeverity.ERROR)

            if critical_alerts > 0:
                health_score = min(health_score, 25.0)
            elif error_alerts > 0:
                health_score = min(health_score, 50.0)

            return health_score

        except Exception as e:
            self.logger.error(f"Error calculating system health: {e}")
            return 50.0

    async def _cleanup_old_alerts(self):
        """Clean up old resolved alerts"""
        try:
            cutoff_time = datetime.now() - timedelta(days=7)

            # Clean alert history
            self.alert_history = [
                alert for alert in self.alert_history
                if alert.triggered_at > cutoff_time
            ]

            # Clean Redis
            # This would clean up old alerts stored in Redis

            self.logger.info("Cleaned up old alerts")

        except Exception as e:
            self.logger.error(f"Error cleaning up old alerts: {e}")

    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Dict[str, Any]]:
        """Get active alerts"""
        try:
            alerts = []
            for alert in self.active_alerts.values():
                if severity and alert.severity != severity:
                    continue

                alert_dict = asdict(alert)
                alert_dict['triggered_at'] = alert.triggered_at.isoformat()
                alert_dict['resolved_at'] = alert.resolved_at.isoformat() if alert.resolved_at else None
                alert_dict['acknowledged_at'] = alert.acknowledged_at.isoformat() if alert.acknowledged_at else None

                alerts.append(alert_dict)

            return alerts

        except Exception as e:
            self.logger.error(f"Error getting active alerts: {e}")
            return []

    def get_health_status(self, service_id: Optional[str] = None) -> Dict[str, Any]:
        """Get health status"""
        try:
            health_data = {
                'overall_status': HealthStatus.HEALTHY.value,
                'checks': {},
                'summary': {
                    'total_checks': len(self.health_checks),
                    'healthy': 0,
                    'degraded': 0,
                    'unhealthy': 0,
                    'unknown': 0
                }
            }

            for check_id, health_check in self.health_checks.items():
                if service_id and health_check.service_id != service_id:
                    continue

                check_dict = asdict(health_check)
                check_dict['last_checked'] = health_check.last_checked.isoformat()

                health_data['checks'][check_id] = check_dict

                # Update summary
                health_data['summary'][health_check.status.value] += 1

                # Determine overall status
                if health_check.status == HealthStatus.UNHEALTHY:
                    health_data['overall_status'] = HealthStatus.UNHEALTHY.value
                elif health_check.status == HealthStatus.DEGRADED and health_data['overall_status'] == HealthStatus.HEALTHY.value:
                    health_data['overall_status'] = HealthStatus.DEGRADED.value

            return health_data

        except Exception as e:
            self.logger.error(f"Error getting health status: {e}")
            return {'overall_status': HealthStatus.UNKNOWN.value, 'error': str(e)}

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format"""
        try:
            return generate_latest()
        except Exception as e:
            self.logger.error(f"Error generating Prometheus metrics: {e}")
            return ""

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.now()
                alert.acknowledged_by = acknowledged_by

                self.logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error acknowledging alert: {e}")
            return False

    async def create_manual_alert(self, name: str, description: str, severity: AlertSeverity, service_id: Optional[str] = None) -> str:
        """Create a manual alert"""
        try:
            alert_id = f"manual:{int(datetime.now().timestamp())}"

            alert = Alert(
                alert_id=alert_id,
                name=name,
                description=description,
                severity=severity,
                status=AlertStatus.ACTIVE,
                service_id=service_id,
                metric_name='manual',
                threshold=0,
                current_value=0,
                triggered_at=datetime.now(),
                resolved_at=None,
                acknowledged_at=None,
                acknowledged_by=None,
                labels={'manual': 'true'},
                annotations={'summary': name, 'description': description}
            )

            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)

            # Send notifications
            await self._send_alert_notifications(alert)

            self.logger.info(f"Manual alert created: {alert_id}")
            return alert_id

        except Exception as e:
            self.logger.error(f"Error creating manual alert: {e}")
            return ""