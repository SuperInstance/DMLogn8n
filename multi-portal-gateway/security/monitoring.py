#!/usr/bin/env python3
"""
DMLogn8n Security Monitoring System
Real-time security monitoring and alerting
"""

import json
import logging
import asyncio
import time
import hashlib
import statistics
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import redis.asyncio as redis
import yaml
import aiofiles
import aiohttp
import psutil
from .waf import SecurityEvent as WAFCSecurityEvent
from .detector import ThreatAlert
from .security_manager import SecurityIncident

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MonitorType(Enum):
    REAL_TIME = "real_time"
    BATCH = "batch"
    PERIODIC = "periodic"
    ON_DEMAND = "on_demand"

class MetricType(Enum):
    SECURITY_EVENTS = "security_events"
    THREAT_ALERTS = "threat_alerts"
    VULNERABILITIES = "vulnerabilities"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    RESOURCE_USAGE = "resource_usage"
    AUTHENTICATION = "authentication"
    DATA_ACCESS = "data_access"

@dataclass
class SecurityMetric:
    metric_id: str
    metric_type: MetricType
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, Any] = None
    threshold: Optional[float] = None
    alert_triggered: bool = False

@dataclass
class SecurityAlert:
    alert_id: str
    title: str
    description: str
    severity: AlertSeverity
    source: str
    metric_id: Optional[str]
    threshold_value: float
    actual_value: float
    triggered_at: datetime
    resolved_at: Optional[datetime]
    tags: Dict[str, Any]
    recommendations: List[str]
    status: str = "active"

@dataclass
class MonitoringDashboard:
    dashboard_id: str
    title: str
    generated_at: datetime
    metrics: List[SecurityMetric]
    alerts: List[SecurityAlert]
    health_status: Dict[str, Any]
    summary: Dict[str, Any]

class SecurityMonitoring:
    """
    Real-time security monitoring and alerting system
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.redis_client = None
        self.active_alerts = {}
        self.metric_history = defaultdict(lambda: deque(maxlen=10000))
        self.alert_history = deque(maxlen=10000)
        self.dashboards = {}

        # Monitoring configuration
        self.enable_real_time_monitoring = self.config.get('enable_real_time_monitoring', True)
        self.alert_retention_days = self.config.get('alert_retention_days', 30)
        self.metric_retention_days = self.config.get('metric_retention_days', 7)
        self.alert_thresholds = self.config.get('alert_thresholds', {})
        self.dashboard_update_interval = self.config.get('dashboard_update_interval', 60)

        # Monitoring thresholds
        self.thresholds = {
            'security_events_rate': {
                'warning': 100,  # events per minute
                'critical': 500
            },
            'threat_alerts_rate': {
                'warning': 10,  # alerts per hour
                'critical': 50
            },
            'vulnerability_count': {
                'warning': 10,
                'critical': 50
            },
            'compliance_score': {
                'warning': 70,  # percentage
                'critical': 50
            },
            'cpu_usage': {
                'warning': 70,  # percentage
                'critical': 90
            },
            'memory_usage': {
                'warning': 80,
                'critical': 95
            },
            'disk_usage': {
                'warning': 85,
                'critical': 95
            },
            'response_time': {
                'warning': 1000,  # milliseconds
                'critical': 3000
            }
        }

        # Initialize metrics collectors
        self._initialize_metrics_collectors()

    async def initialize(self):
        """Initialize security monitoring components"""
        try:
            # Initialize Redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=12,  # Security monitoring specific DB
                decode_responses=True
            )

            # Load historical data
            await self._load_historical_data()

            # Start background tasks
            await self._start_background_tasks()

            logger.info("Security Monitoring initialized")

        except Exception as e:
            logger.error(f"Security Monitoring initialization failed: {e}")
            raise

    async def collect_metric(self, metric_type: MetricType, name: str, value: float,
                            unit: str = "", tags: Dict[str, Any] = None, threshold: float = None):
        """
        Collect security metric
        """
        try:
            metric_id = f"{metric_type.value}_{name}_{int(time.time())}"

            metric = SecurityMetric(
                metric_id=metric_id,
                metric_type=metric_type,
                name=name,
                value=value,
                unit=unit,
                timestamp=datetime.now(),
                tags=tags or {},
                threshold=threshold
            )

            # Check threshold
            if threshold is not None:
                config_threshold = self.thresholds.get(name)
                if config_threshold:
                    warning_threshold = config_threshold.get('warning')
                    critical_threshold = config_threshold.get('critical')

                    alert_triggered = False
                    alert_severity = None

                    if critical_threshold and value >= critical_threshold:
                        alert_triggered = True
                        alert_severity = AlertSeverity.CRITICAL
                    elif warning_threshold and value >= warning_threshold:
                        alert_triggered = True
                        alert_severity = AlertSeverity.HIGH

                    if alert_triggered:
                        await self._trigger_metric_alert(metric, alert_severity)
                        metric.alert_triggered = True

            # Store metric
            self.metric_history[metric_type].append(metric)

            # Store in Redis
            if self.redis_client:
                metric_data = asdict(metric)
                metric_data['timestamp'] = metric.timestamp.isoformat()

                await self.redis_client.lpush(
                    f"metrics:{metric_type.value}",
                    json.dumps(metric_data)
                )
                await self.redis_client.ltrim(f"metrics:{metric_type.value}", 0, 10000)

                # Store latest metric
                await self.redis_client.setex(
                    f"metric:latest:{metric_id}",
                    86400 * self.metric_retention_days,
                    json.dumps(metric_data)
                )

        except Exception as e:
            logger.error(f"Metric collection error: {e}")

    async def process_security_event(self, event: WAFCSecurityEvent):
        """
        Process security event from WAF
        """
        try:
            # Extract event metrics
            await self.collect_metric(
                MetricType.SECURITY_EVENTS,
                "event_rate",
                1.0,
                "events/min",
                {
                    'event_type': event.threat_type.value,
                    'severity': event.threat_level.value,
                    'source_ip': event.source_ip,
                    'action': event.action_taken.value
                }
            )

            # Check for event patterns
            await self._analyze_event_patterns(event)

        except Exception as e:
            logger.error(f"Security event processing error: {e}")

    async def process_threat_alert(self, threat_alert: ThreatAlert):
        """
        Process threat alert from detector
        """
        try:
            # Extract alert metrics
            await self.collect_metric(
                MetricType.THREAT_ALERTS,
                "threat_rate",
                1.0,
                "alerts/hour",
                {
                    'threat_type': threat_alert.threat_type.value,
                    'severity': threat_alert.severity.name,
                    'source_ip': threat_alert.source_ip,
                    'confidence': threat_alert.confidence
                }
            )

            # Create monitoring alert if high severity
            if threat_alert.severity.value >= 3:  # HIGH or CRITICAL
                await self._create_security_alert(
                    title=f"High Severity Threat: {threat_alert.threat_type.value}",
                    description=f"Threat detected: {threat_alert.description}",
                    severity=AlertSeverity.HIGH if threat_alert.severity.value == 3 else AlertSeverity.CRITICAL,
                    source="threat_detector",
                    threshold_value=1.0,
                    actual_value=threat_alert.confidence,
                    tags={
                        'threat_type': threat_alert.threat_type.value,
                        'source_ip': threat_alert.source_ip,
                        'threat_id': threat_alert.alert_id
                    },
                    recommendations=["Investigate threat immediately", "Review security logs", "Consider blocking source"]
                )

        except Exception as e:
            logger.error(f"Threat alert processing error: {e}")

    async def create_dashboard(self, dashboard_id: str, title: str) -> MonitoringDashboard:
        """
        Create security monitoring dashboard
        """
        try:
            dashboard = MonitoringDashboard(
                dashboard_id=dashboard_id,
                title=title,
                generated_at=datetime.now(),
                metrics=[],
                alerts=list(self.active_alerts.values()),
                health_status=await self._get_health_status(),
                summary=await self._get_monitoring_summary()
            )

            # Collect recent metrics
            for metric_type in MetricType:
                recent_metrics = list(self.metric_history[metric_type])[-100:]  # Last 100 metrics
                dashboard.metrics.extend(recent_metrics)

            # Store dashboard
            self.dashboards[dashboard_id] = dashboard

            # Store in Redis
            if self.redis_client:
                dashboard_data = asdict(dashboard)
                dashboard_data['generated_at'] = dashboard.generated_at.isoformat()
                dashboard_data['metrics'] = [asdict(m) for m in dashboard.metrics]
                dashboard_data['alerts'] = [asdict(a) for a in dashboard.alerts]

                await self.redis_client.setex(
                    f"dashboard:{dashboard_id}",
                    3600,  # 1 hour
                    json.dumps(dashboard_data)
                )

            logger.info(f"Created security dashboard: {dashboard_id}")
            return dashboard

        except Exception as e:
            logger.error(f"Dashboard creation error: {e}")
            raise

    async def get_real_time_metrics(self, metric_type: MetricType = None,
                                   time_window_minutes: int = 60) -> List[SecurityMetric]:
        """
        Get real-time metrics
        """
        try:
            cutoff_time = datetime.now() - timedelta(minutes=time_window)

            if metric_type:
                metrics = [
                    m for m in self.metric_history[metric_type]
                    if m.timestamp >= cutoff_time
                ]
            else:
                metrics = []
                for mtype in MetricType:
                    metrics.extend([
                        m for m in self.metric_history[mtype]
                        if m.timestamp >= cutoff_time
                    ])

            return sorted(metrics, key=lambda x: x.timestamp)

        except Exception as e:
            logger.error(f"Real-time metrics retrieval error: {e}")
            return []

    async def get_active_alerts(self) -> List[SecurityAlert]:
        """
        Get active security alerts
        """
        try:
            return list(self.active_alerts.values())

        except Exception as e:
            logger.error(f"Active alerts retrieval error: {e}")
            return []

    async def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve security alert
        """
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = "resolved"
                alert.resolved_at = datetime.now()

                # Move to history
                self.alert_history.append(alert)
                del self.active_alerts[alert_id]

                # Update in Redis
                if self.redis_client:
                    await self.redis_client.set(
                        f"alert_resolved:{alert_id}",
                        json.dumps(asdict(alert))
                    )
                    await self.redis_client.delete(f"alert_active:{alert_id}")

                logger.info(f"Alert resolved: {alert_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Alert resolution error: {e}")
            return False

    async def get_monitoring_summary(self) -> Dict[str, Any]:
        """
        Get monitoring summary statistics
        """
        try:
            summary = {
                'total_metrics': sum(len(history) for history in self.metric_history.values()),
                'active_alerts': len(self.active_alerts),
                'resolved_alerts_24h': len([
                    a for a in self.alert_history
                    if a.resolved_at and a.resolved_at >= datetime.now() - timedelta(hours=24)
                ]),
                'metric_types': {},
                'alert_severities': defaultdict(int),
                'system_health': await self._get_health_status()
            }

            # Count metrics by type
            for metric_type in MetricType:
                summary['metric_types'][metric_type.value] = len(self.metric_history[metric_type])

            # Count alerts by severity
            for alert in self.active_alerts.values():
                summary['alert_severities'][alert.severity.value] += 1

            return summary

        except Exception as e:
            logger.error(f"Monitoring summary error: {e}")
            return {}

    async def get_trend_analysis(self, metric_name: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get trend analysis for specific metric
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            # Find all metrics with matching name
            matching_metrics = []
            for metric_type in MetricType:
                matching_metrics.extend([
                    m for m in self.metric_history[metric_type]
                    if m.name == metric_name and m.timestamp >= cutoff_time
                ])

            if not matching_metrics:
                return {}

            # Calculate trends
            values = [m.value for m in matching_metrics]
            timestamps = [m.timestamp for m in matching_metrics]

            return {
                'metric_name': metric_name,
                'time_range_hours': hours,
                'total_points': len(values),
                'current_value': values[-1] if values else 0,
                'min_value': min(values),
                'max_value': max(values),
                'avg_value': statistics.mean(values),
                'trend_direction': 'up' if len(values) > 1 and values[-1] > values[-2] else 'down',
                'volatility': statistics.stdev(values) if len(values) > 1 else 0,
                'timestamps': [t.isoformat() for t in timestamps]
            }

        except Exception as e:
            logger.error(f"Trend analysis error: {e}")
            return {}

    # Private methods
    async def _trigger_metric_alert(self, metric: SecurityMetric, severity: AlertSeverity):
        """Trigger alert for metric threshold breach"""
        try:
            alert_id = hashlib.md5(f"{metric.metric_id}_{severity.value}_{int(time.time())}".encode()).hexdigest()[:16]

            alert = SecurityAlert(
                alert_id=alert_id,
                title=f"{severity.name.upper()} Alert: {metric.name}",
                description=f"Metric '{metric.name}' exceeded threshold of {metric.threshold} (current: {metric.value})",
                severity=severity,
                source="monitoring_system",
                metric_id=metric.metric_id,
                threshold_value=metric.threshold or 0,
                actual_value=metric.value,
                triggered_at=datetime.now(),
                resolved_at=None,
                tags=metric.tags or {},
                recommendations=self._generate_metric_recommendations(metric, severity),
                status="active"
            )

            self.active_alerts[alert_id] = alert

            # Store in Redis
            if self.redis_client:
                await self.redis_client.setex(
                    f"alert_active:{alert_id}",
                    86400 * self.alert_retention_days,
                    json.dumps(asdict(alert))
                )

            # Add to history
            self.alert_history.append(alert)

            logger.warning(f"Metric alert triggered: {alert.title}")

        except Exception as e:
            logger.error(f"Metric alert triggering error: {e}")

    async def _create_security_alert(self, title: str, description: str, severity: AlertSeverity,
                                   source: str, threshold_value: float, actual_value: float,
                                   tags: Dict[str, Any], recommendations: List[str]):
        """Create security alert"""
        try:
            alert_id = hashlib.md5(f"{title}_{int(time.time())}".encode()).hexdigest()[:16]

            alert = SecurityAlert(
                alert_id=alert_id,
                title=title,
                description=description,
                severity=severity,
                source=source,
                metric_id=None,
                threshold_value=threshold_value,
                actual_value=actual_value,
                triggered_at=datetime.now(),
                resolved_at=None,
                tags=tags,
                recommendations=recommendations,
                status="active"
            )

            self.active_alerts[alert_id] = alert

            # Store in Redis
            if self.redis_client:
                await self.redis_client.setex(
                    f"alert_active:{alert_id}",
                    86400 * self.alert_retention_days,
                    json.dumps(asdict(alert))
                )

            # Add to history
            self.alert_history.append(alert)

            logger.warning(f"Security alert created: {title}")

        except Exception as e:
            logger.error(f"Security alert creation error: {e}")

    async def _analyze_event_patterns(self, event: WAFCSecurityEvent):
        """Analyze security event patterns"""
        try:
            # Check for attack patterns
            if event.source_ip:
                ip_events = [
                    e for e in self.alert_history
                    if 'source_ip' in e.tags and e.tags['source_ip'] == event.source_ip
                ]

                if len(ip_events) > 10:  # Multiple alerts from same IP
                    await self._create_security_alert(
                        title=f"Repeat Offense Pattern from {event.source_ip}",
                        description=f"Multiple security events detected from IP {event.source_ip}",
                        severity=AlertSeverity.HIGH,
                        source="pattern_analysis",
                        threshold_value=10,
                        actual_value=len(ip_events),
                        tags={'source_ip': event.source_ip, 'pattern': 'repeat_offense'},
                        recommendations=["Block IP address", "Investigate attack patterns", "Increase monitoring"]
                    )

        except Exception as e:
            logger.error(f"Event pattern analysis error: {e}")

    def _generate_metric_recommendations(self, metric: SecurityMetric, severity: AlertSeverity) -> List[str]:
        """Generate recommendations for metric alert"""
        recommendations = []

        if metric.metric_type == MetricType.SECURITY_EVENTS:
            recommendations.extend([
                "Review security event logs",
                "Investigate potential security incident",
                "Consider adjusting WAF rules"
            ])
        elif metric.metric_type == MetricType.THREAT_ALERTS:
            recommendations.extend([
                "Review threat detection rules",
                "Investigate identified threats",
                "Update security controls"
            ])
        elif metric.metric_type == MetricType.VULNERABILITIES:
            recommendations.extend([
                "Address identified vulnerabilities",
                "Update affected systems",
                "Review patch management process"
            ])
        elif metric.metric_type == MetricType.COMPLIANCE:
            recommendations.extend([
                "Address compliance gaps",
                "Update compliance documentation",
                "Implement required controls"
            ])
        elif metric.metric_type == MetricType.RESOURCE_USAGE:
            if 'cpu' in metric.name.lower():
                recommendations.extend([
                    "Investigate high CPU usage",
                    "Scale resources if needed",
                    "Review performance optimization"
                ])
            elif 'memory' in metric.name.lower():
                recommendations.extend([
                    "Investigate memory leaks",
                    "Optimize memory usage",
                    "Add more memory if needed"
                ])
            elif 'disk' in metric.name.lower():
                recommendations.extend([
                    "Clean up disk space",
                    "Archive old data",
                    "Expand storage capacity"
                ])

        if severity == AlertSeverity.CRITICAL:
            recommendations.insert(0, "IMMEDIATE ACTION REQUIRED")
        elif severity == AlertSeverity.HIGH:
            recommendations.insert(0, "High priority - address within 1 hour")

        return recommendations

    async def _get_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        try:
            health_status = {
                'overall': 'healthy',
                'components': {},
                'last_check': datetime.now().isoformat()
            }

            # Check system resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent

            health_status['components']['cpu'] = {
                'status': 'healthy' if cpu_percent < 80 else 'warning' if cpu_percent < 95 else 'critical',
                'usage': cpu_percent,
                'unit': 'percent'
            }

            health_status['components']['memory'] = {
                'status': 'healthy' if memory_percent < 80 else 'warning' if memory_percent < 95 else 'critical',
                'usage': memory_percent,
                'unit': 'percent'
            }

            health_status['components']['disk'] = {
                'status': 'healthy' if disk_percent < 85 else 'warning' if disk_percent < 95 else 'critical',
                'usage': disk_percent,
                'unit': 'percent'
            }

            # Check active alerts
            critical_alerts = len([a for a in self.active_alerts.values() if a.severity == AlertSeverity.CRITICAL])
            high_alerts = len([a for a in self.active_alerts.values() if a.severity == AlertSeverity.HIGH])

            if critical_alerts > 0:
                health_status['overall'] = 'critical'
            elif high_alerts > 5:
                health_status['overall'] = 'warning'

            health_status['components']['alerts'] = {
                'status': 'healthy' if critical_alerts == 0 else 'warning' if critical_alerts < 5 else 'critical',
                'critical': critical_alerts,
                'high': high_alerts
            }

            return health_status

        except Exception as e:
            logger.error(f"Health status check error: {e}")
            return {'overall': 'unknown', 'error': str(e)}

    async def _get_monitoring_summary(self) -> Dict[str, Any]:
        """Get monitoring summary"""
        try:
            summary = {
                'active_dashboards': len(self.dashboards),
                'monitoring_enabled': self.enable_real_time_monitoring,
                'last_update': datetime.now().isoformat()
            }

            # Add metric counts
            for metric_type in MetricType:
                summary[f'metrics_{metric_type.value}'] = len(self.metric_history[metric_type])

            return summary

        except Exception as e:
            logger.error(f"Monitoring summary error: {e}")
            return {}

    def _initialize_metrics_collectors(self):
        """Initialize metrics collectors"""
        self.metrics_collectors = {
            'system_resources': self._collect_system_resources,
            'security_metrics': self._collect_security_metrics,
            'performance_metrics': self._collect_performance_metrics
        }

    async def _collect_system_resources(self):
        """Collect system resource metrics"""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                await self.collect_metric(
                    MetricType.RESOURCE_USAGE,
                    "cpu_usage",
                    cpu_percent,
                    "percent",
                    {"type": "system"}
                )

                # Memory usage
                memory = psutil.virtual_memory()
                await self.collect_metric(
                    MetricType.RESOURCE_USAGE,
                    "memory_usage",
                    memory.percent,
                    "percent",
                    {"type": "system", "total": memory.total, "available": memory.available}
                )

                # Disk usage
                disk = psutil.disk_usage('/')
                await self.collect_metric(
                    MetricType.RESOURCE_USAGE,
                    "disk_usage",
                    disk.percent,
                    "percent",
                    {"type": "system", "total": disk.total, "free": disk.free}
                )

                await asyncio.sleep(30)  # Collect every 30 seconds

            except Exception as e:
                logger.error(f"System resource collection error: {e}")
                await asyncio.sleep(60)

    async def _collect_security_metrics(self):
        """Collect security-related metrics"""
        while True:
            try:
                # Count active WAF events
                waf_events = len([
                    event for event in self.alert_history
                    if event.source == "waf" and event.triggered_at >= datetime.now() - timedelta(minutes=5)
                ])
                await self.collect_metric(
                    MetricType.SECURITY_EVENTS,
                    "waf_events_5min",
                    waf_events,
                    "events/5min",
                    {"type": "waf"}
                )

                await asyncio.sleep(60)  # Collect every minute

            except Exception as e:
                logger.error(f"Security metrics collection error: {e}")
                await asyncio.sleep(120)

    async def _collect_performance_metrics(self):
        """Collect performance metrics"""
        while True:
            try:
                # Network latency (placeholder)
                await self.collect_metric(
                    MetricType.PERFORMANCE,
                    "network_latency",
                    100.0,  # Placeholder value
                    "ms",
                    {"type": "network"}
                )

                await asyncio.sleep(120)  # Collect every 2 minutes

            except Exception as e:
                logger.error(f"Performance metrics collection error: {e}")
                await asyncio.sleep(240)

    async def _load_historical_data(self):
        """Load historical data from Redis"""
        try:
            if not self.redis_client:
                return

            # Load recent metrics
            for metric_type in MetricType:
                metric_data = await self.redis_client.lrange(f"metrics:{metric_type.value}", 0, 1000)
                for data in metric_data:
                    metric_dict = json.loads(data)
                    metric_dict['timestamp'] = datetime.fromisoformat(metric_dict['timestamp'])
                    metric_dict['metric_type'] = MetricType(metric_dict['metric_type'])
                    metric = SecurityMetric(**metric_dict)
                    self.metric_history[metric_type].append(metric)

            # Load active alerts
            alert_data = await self.redis_client.keys("alert_active:*")
            for key in alert_data:
                data = await self.redis_client.get(key)
                if data:
                    alert_dict = json.loads(data)
                    alert_dict['triggered_at'] = datetime.fromisoformat(alert_dict['triggered_at'])
                    if alert_dict.get('resolved_at'):
                        alert_dict['resolved_at'] = datetime.fromisoformat(alert_dict['resolved_at'])
                    alert_dict['severity'] = AlertSeverity(alert_dict['severity'])
                    alert = SecurityAlert(**alert_dict)
                    self.active_alerts[alert.alert_id] = alert

            logger.info(f"Loaded historical data: {sum(len(h) for h in self.metric_history.values())} metrics, {len(self.active_alerts)} active alerts")

        except Exception as e:
            logger.error(f"Historical data loading error: {e}")

    async def _start_background_tasks(self):
        """Start background monitoring tasks"""
        try:
            # Start metrics collectors
            for collector_name, collector in self.metrics_collectors.items():
                asyncio.create_task(collector())

            # Dashboard updates
            asyncio.create_task(self._periodic_dashboard_updates())

            # Alert cleanup
            asyncio.create_task(self._periodic_alert_cleanup())

            # Health checks
            asyncio.create_task(self._periodic_health_checks())

        except Exception as e:
            logger.error(f"Background tasks startup error: {e}")

    async def _periodic_dashboard_updates(self):
        """Periodically update dashboards"""
        while True:
            try:
                await asyncio.sleep(self.dashboard_update_interval)

                # Update existing dashboards
                for dashboard_id in list(self.dashboards.keys()):
                    await self.create_dashboard(dashboard_id, self.dashboards[dashboard_id].title)

            except Exception as e:
                logger.error(f"Dashboard update error: {e}")
                await asyncio.sleep(60)

    async def _periodic_alert_cleanup(self):
        """Clean up old alerts"""
        while True:
            try:
                await asyncio.sleep(3600 * 6)  # Every 6 hours

                cutoff_time = datetime.now() - timedelta(days=self.alert_retention_days)
                expired_alerts = [
                    alert_id for alert_id, alert in self.active_alerts.items()
                    if alert.triggered_at < cutoff_time
                ]

                for alert_id in expired_alerts:
                    await self.resolve_alert(alert_id)

                if expired_alerts:
                    logger.info(f"Cleaned up {len(expired_alerts)} expired alerts")

            except Exception as e:
                logger.error(f"Alert cleanup error: {e}")
                await asyncio.sleep(300)

    async def _periodic_health_checks(self):
        """Periodic health checks"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                # Perform health check
                health_status = await self._get_health_status()

                # Create alert if system unhealthy
                if health_status['overall'] in ['warning', 'critical']:
                    await self._create_security_alert(
                        title=f"System Health: {health_status['overall'].upper()}",
                        description=f"System health status is {health_status['overall']}",
                        severity=AlertSeverity.HIGH if health_status['overall'] == 'critical' else AlertSeverity.MEDIUM,
                        source="health_monitor",
                        threshold_value=100,
                        actual_value=0,
                        tags=health_status,
                        recommendations=["Investigate system health", "Check resource usage", "Review active alerts"]
                    )

            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(300)