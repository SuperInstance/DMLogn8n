#!/usr/bin/env python3
"""
Alert Management System for DMLogn8n Monitoring
Handles alert rules, notifications, and escalation
"""

import asyncio
import json
import logging
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import aiosmtplib
from email.message import EmailMessage
import websockets

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """Alert status states"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    ACKNOWLEDGED = "acknowledged"

@dataclass
class AlertRule:
    """Alert rule definition"""
    id: str
    name: str
    description: str
    metric_name: str
    condition: str  # e.g., ">", "<", "==", "!=", "in", "not_in"
    threshold: float
    severity: AlertSeverity
    enabled: bool
    cooldown_period: int  # seconds
    evaluation_interval: int  # seconds
    tags: Dict[str, str]
    notification_channels: List[str]

@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule_id: str
    rule_name: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    current_value: float
    threshold: float
    metric_name: str
    timestamp: datetime
    resolved_timestamp: Optional[datetime]
    acknowledged_by: Optional[str]
    acknowledged_timestamp: Optional[datetime]
    labels: Dict[str, str]
    annotations: Dict[str, str]

@dataclass
class NotificationChannel:
    """Notification channel configuration"""
    id: str
    name: str
    type: str  # email, slack, webhook, websocket
    enabled: bool
    config: Dict[str, Any]
    rate_limit: int  # notifications per hour

class AlertRuleEngine:
    """Evaluates alert rules against metrics"""

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.load_default_rules()

    def load_default_rules(self):
        """Load default alert rules for the DMLogn8n system"""
        default_rules = [
            # System alerts
            AlertRule(
                id="system_cpu_high",
                name="High CPU Usage",
                description="System CPU usage is above threshold",
                metric_name="system_cpu_usage_percent",
                condition=">",
                threshold=80.0,
                severity=AlertSeverity.WARNING,
                enabled=True,
                cooldown_period=300,
                evaluation_interval=60,
                tags={"component": "system", "resource": "cpu"},
                notification_channels=["email", "slack"]
            ),
            AlertRule(
                id="system_memory_high",
                name="High Memory Usage",
                description="System memory usage is above threshold",
                metric_name="system_memory_usage_percent",
                condition=">",
                threshold=85.0,
                severity=AlertSeverity.WARNING,
                enabled=True,
                cooldown_period=300,
                evaluation_interval=60,
                tags={"component": "system", "resource": "memory"},
                notification_channels=["email", "slack"]
            ),
            AlertRule(
                id="system_disk_high",
                name="High Disk Usage",
                description="System disk usage is above threshold",
                metric_name="system_disk_usage_percent",
                condition=">",
                threshold=90.0,
                severity=AlertSeverity.CRITICAL,
                enabled=True,
                cooldown_period=600,
                evaluation_interval=120,
                tags={"component": "system", "resource": "disk"},
                notification_channels=["email", "slack", "webhook"]
            ),

            # Agent alerts
            AlertRule(
                id="agent_error_rate_high",
                name="High Agent Error Rate",
                description="Agent error rate is above threshold",
                metric_name="agent_error_rate",
                condition=">",
                threshold=0.05,
                severity=AlertSeverity.ERROR,
                enabled=True,
                cooldown_period=300,
                evaluation_interval=60,
                tags={"component": "agents", "metric": "error_rate"},
                notification_channels=["email", "slack"]
            ),
            AlertRule(
                id="agent_response_time_high",
                name="High Agent Response Time",
                description="Agent response time is above threshold",
                metric_name="agent_response_time_p95",
                condition=">",
                threshold=2.0,
                severity=AlertSeverity.WARNING,
                enabled=True,
                cooldown_period=300,
                evaluation_interval=60,
                tags={"component": "agents", "metric": "response_time"},
                notification_channels=["email"]
            ),
            AlertRule(
                id="agent_down",
                name="Agent Down",
                description="Agent is not responding",
                metric_name="agent_status",
                condition="!=",
                threshold="active",
                severity=AlertSeverity.CRITICAL,
                enabled=True,
                cooldown_period=600,
                evaluation_interval=30,
                tags={"component": "agents", "metric": "status"},
                notification_channels=["email", "slack", "webhook", "websocket"]
            ),

            # Business alerts
            AlertRule(
                id="user_activity_low",
                name="Low User Activity",
                description="Active users count is below threshold",
                metric_name="active_users_total",
                condition="<",
                threshold=50.0,
                severity=AlertSeverity.WARNING,
                enabled=True,
                cooldown_period=1800,
                evaluation_interval=300,
                tags={"component": "business", "metric": "user_activity"},
                notification_channels=["email"]
            ),
            AlertRule(
                id="user_satisfaction_low",
                name="Low User Satisfaction",
                description="User satisfaction score is below threshold",
                metric_name="user_satisfaction_score",
                condition="<",
                threshold=3.5,
                severity=AlertSeverity.ERROR,
                enabled=True,
                cooldown_period=3600,
                evaluation_interval=600,
                tags={"component": "business", "metric": "satisfaction"},
                notification_channels=["email", "slack"]
            ),

            # AI Model alerts
            AlertRule(
                id="ai_model_latency_high",
                name="High AI Model Latency",
                description="AI model response time is above threshold",
                metric_name="ai_model_average_latency_seconds",
                condition=">",
                threshold=5.0,
                severity=AlertSeverity.WARNING,
                enabled=True,
                cooldown_period=300,
                evaluation_interval=60,
                tags={"component": "ai", "metric": "latency"},
                notification_channels=["email"]
            ),
            AlertRule(
                id="ai_model_accuracy_low",
                name="Low AI Model Accuracy",
                description="AI model accuracy is below threshold",
                metric_name="ai_model_accuracy_score",
                condition="<",
                threshold=3.0,
                severity=AlertSeverity.ERROR,
                enabled=True,
                cooldown_period=1800,
                evaluation_interval=300,
                tags={"component": "ai", "metric": "accuracy"},
                notification_channels=["email", "slack"]
            ),

            # Database alerts
            AlertRule(
                id="database_connections_high",
                name="High Database Connections",
                description="Database connection count is above threshold",
                metric_name="database_active_connections",
                condition=">",
                threshold=80.0,
                severity=AlertSeverity.WARNING,
                enabled=True,
                cooldown_period=300,
                evaluation_interval=60,
                tags={"component": "database", "metric": "connections"},
                notification_channels=["email"]
            ),
            AlertRule(
                id="database_query_slow",
                name="Slow Database Queries",
                description="Database query response time is above threshold",
                metric_name="database_avg_response_time",
                condition=">",
                threshold=1.0,
                severity=AlertSeverity.WARNING,
                enabled=True,
                cooldown_period=300,
                evaluation_interval=60,
                tags={"component": "database", "metric": "response_time"},
                notification_channels=["email"]
            ),
        ]

        for rule in default_rules:
            self.rules[rule.id] = rule

    def add_rule(self, rule: AlertRule):
        """Add or update an alert rule"""
        self.rules[rule.id] = rule
        logger.info(f"Added/updated alert rule: {rule.name}")

    def remove_rule(self, rule_id: str):
        """Remove an alert rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")

    def get_rules_for_evaluation(self) -> List[AlertRule]:
        """Get all enabled rules that need evaluation"""
        return [rule for rule in self.rules.values() if rule.enabled]

class AlertManager:
    """Manages alert lifecycle and notifications"""

    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.rule_engine = AlertRuleEngine()
        self.notification_counters: Dict[str, int] = {}
        self.last_notification_time: Dict[str, datetime] = {}

        self.load_default_notification_channels()

    def load_default_notification_channels(self):
        """Load default notification channels"""
        default_channels = [
            NotificationChannel(
                id="email",
                name="Email Notifications",
                type="email",
                enabled=True,
                config={
                    "smtp_host": "smtp.gmail.com",
                    "smtp_port": 587,
                    "smtp_user": "alerts@dmlogn8n.com",
                    "smtp_password": "your_password",
                    "recipients": ["admin@dmlogn8n.com", "ops@dmlogn8n.com"]
                },
                rate_limit=10
            ),
            NotificationChannel(
                id="slack",
                name="Slack Notifications",
                type="slack",
                enabled=True,
                config={
                    "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
                    "channel": "#alerts",
                    "username": "DMLogn8n AlertBot"
                },
                rate_limit=20
            ),
            NotificationChannel(
                id="webhook",
                name="Webhook Notifications",
                type="webhook",
                enabled=True,
                config={
                    "url": "https://api.dmlogn8n.com/alerts/webhook",
                    "headers": {"Authorization": "Bearer your_token"}
                },
                rate_limit=30
            ),
            NotificationChannel(
                id="websocket",
                name="WebSocket Notifications",
                type="websocket",
                enabled=True,
                config={
                    "port": 8081,
                    "path": "/alerts"
                },
                rate_limit=100
            ),
        ]

        for channel in default_channels:
            self.notification_channels[channel.id] = channel

    async def evaluate_rules(self, metrics: Dict[str, Any]):
        """Evaluate all alert rules against current metrics"""
        rules = self.rule_engine.get_rules_for_evaluation()

        for rule in rules:
            try:
                await self.evaluate_rule(rule, metrics)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {e}")

    async def evaluate_rule(self, rule: AlertRule, metrics: Dict[str, Any]):
        """Evaluate a single alert rule"""
        if rule.metric_name not in metrics:
            return

        current_value = metrics[rule.metric_name]
        threshold = rule.threshold

        # Check if condition is met
        condition_met = self._evaluate_condition(current_value, rule.condition, threshold)

        alert_id = f"{rule.id}_{hash(str(metrics))}"

        if condition_met:
            # Check if alert already exists
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                # Update current value
                alert.current_value = current_value
                alert.timestamp = datetime.now()
            else:
                # Create new alert
                alert = Alert(
                    id=alert_id,
                    rule_id=rule.id,
                    rule_name=rule.name,
                    description=rule.description,
                    severity=rule.severity,
                    status=AlertStatus.ACTIVE,
                    current_value=current_value,
                    threshold=threshold,
                    metric_name=rule.metric_name,
                    timestamp=datetime.now(),
                    resolved_timestamp=None,
                    acknowledged_by=None,
                    acknowledged_timestamp=None,
                    labels=rule.tags,
                    annotations={
                        "summary": f"{rule.name}: {current_value} {rule.condition} {threshold}",
                        "description": f"{rule.description}. Current value: {current_value}"
                    }
                )

                self.active_alerts[alert_id] = alert
                self.alert_history.append(alert)

                # Send notifications
                await self.send_notifications(alert, rule)

                logger.warning(f"Alert triggered: {rule.name} - {current_value} {rule.condition} {threshold}")

        else:
            # Check if alert exists and should be resolved
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_timestamp = datetime.now()

                # Move from active to history
                del self.active_alerts[alert_id]
                self.alert_history.append(alert)

                # Send resolution notification
                await self.send_resolution_notification(alert, rule)

                logger.info(f"Alert resolved: {rule.name}")

    def _evaluate_condition(self, current_value: Any, condition: str, threshold: Any) -> bool:
        """Evaluate alert condition"""
        try:
            if condition == ">":
                return float(current_value) > float(threshold)
            elif condition == "<":
                return float(current_value) < float(threshold)
            elif condition == ">=":
                return float(current_value) >= float(threshold)
            elif condition == "<=":
                return float(current_value) <= float(threshold)
            elif condition == "==":
                return str(current_value) == str(threshold)
            elif condition == "!=":
                return str(current_value) != str(threshold)
            elif condition == "in":
                return current_value in threshold if isinstance(threshold, (list, tuple)) else False
            elif condition == "not_in":
                return current_value not in threshold if isinstance(threshold, (list, tuple)) else True
            else:
                logger.warning(f"Unknown condition: {condition}")
                return False
        except Exception as e:
            logger.error(f"Error evaluating condition {condition}: {e}")
            return False

    async def send_notifications(self, alert: Alert, rule: AlertRule):
        """Send notifications for an alert"""
        for channel_id in rule.notification_channels:
            if channel_id not in self.notification_channels:
                continue

            channel = self.notification_channels[channel_id]
            if not channel.enabled:
                continue

            # Check rate limit
            if not self._check_rate_limit(channel_id):
                continue

            try:
                if channel.type == "email":
                    await self._send_email_notification(alert, channel)
                elif channel.type == "slack":
                    await self._send_slack_notification(alert, channel)
                elif channel.type == "webhook":
                    await self._send_webhook_notification(alert, channel)
                elif channel.type == "websocket":
                    await self._send_websocket_notification(alert, channel)

                # Update rate limit counters
                self._update_rate_limit(channel_id)

            except Exception as e:
                logger.error(f"Error sending notification via {channel.type}: {e}")

    async def send_resolution_notification(self, alert: Alert, rule: AlertRule):
        """Send notification when alert is resolved"""
        # Similar to send_notifications but for resolution
        # Implementation would be similar with resolution message
        pass

    def _check_rate_limit(self, channel_id: str) -> bool:
        """Check if channel is within rate limit"""
        channel = self.notification_channels[channel_id]
        now = datetime.now()

        # Reset counter if it's been more than an hour
        if channel_id in self.last_notification_time:
            if (now - self.last_notification_time[channel_id]) > timedelta(hours=1):
                self.notification_counters[channel_id] = 0

        current_count = self.notification_counters.get(channel_id, 0)
        return current_count < channel.rate_limit

    def _update_rate_limit(self, channel_id: str):
        """Update rate limit counters"""
        self.notification_counters[channel_id] = self.notification_counters.get(channel_id, 0) + 1
        self.last_notification_time[channel_id] = datetime.now()

    async def _send_email_notification(self, alert: Alert, channel: NotificationChannel):
        """Send email notification"""
        config = channel.config

        msg = EmailMessage()
        msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.rule_name}"
        msg['From'] = config['smtp_user']
        msg['To'] = ', '.join(config['recipients'])

        body = f"""
Alert: {alert.rule_name}
Severity: {alert.severity.value.upper()}
Metric: {alert.metric_name}
Current Value: {alert.current_value}
Threshold: {alert.threshold}
Description: {alert.description}
Timestamp: {alert.timestamp.isoformat()}

Labels: {alert.labels}
Annotations: {alert.annotations}
        """

        msg.set_content(body)

        try:
            await aiosmtplib.send(
                msg,
                hostname=config['smtp_host'],
                port=config['smtp_port'],
                start_tls=True,
                username=config['smtp_user'],
                password=config['smtp_password']
            )
            logger.info(f"Email notification sent for alert: {alert.rule_name}")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            raise

    async def _send_slack_notification(self, alert: Alert, channel: NotificationChannel):
        """Send Slack notification"""
        config = channel.config

        color = {
            AlertSeverity.INFO: "good",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.ERROR: "danger",
            AlertSeverity.CRITICAL: "danger"
        }.get(alert.severity, "warning")

        payload = {
            "channel": config['channel'],
            "username": config['username'],
            "attachments": [
                {
                    "color": color,
                    "title": f"{alert.severity.value.upper()}: {alert.rule_name}",
                    "text": alert.description,
                    "fields": [
                        {
                            "title": "Metric",
                            "value": alert.metric_name,
                            "short": True
                        },
                        {
                            "title": "Current Value",
                            "value": str(alert.current_value),
                            "short": True
                        },
                        {
                            "title": "Threshold",
                            "value": str(alert.threshold),
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            "short": True
                        }
                    ]
                }
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(config['webhook_url'], json=payload) as response:
                if response.status == 200:
                    logger.info(f"Slack notification sent for alert: {alert.rule_name}")
                else:
                    raise Exception(f"Slack API returned status {response.status}")

    async def _send_webhook_notification(self, alert: Alert, channel: NotificationChannel):
        """Send webhook notification"""
        config = channel.config

        payload = {
            "alert_id": alert.id,
            "rule_name": alert.rule_name,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "metric": alert.metric_name,
            "current_value": alert.current_value,
            "threshold": alert.threshold,
            "description": alert.description,
            "timestamp": alert.timestamp.isoformat(),
            "labels": alert.labels,
            "annotations": alert.annotations
        }

        headers = config.get('headers', {})
        headers['Content-Type'] = 'application/json'

        async with aiohttp.ClientSession() as session:
            async with session.post(config['url'], json=payload, headers=headers) as response:
                if response.status == 200:
                    logger.info(f"Webhook notification sent for alert: {alert.rule_name}")
                else:
                    raise Exception(f"Webhook returned status {response.status}")

    async def _send_websocket_notification(self, alert: Alert, channel: NotificationChannel):
        """Send WebSocket notification to connected clients"""
        # This would integrate with the main dashboard service
        # Implementation depends on WebSocket server setup
        logger.info(f"WebSocket notification queued for alert: {alert.rule_name}")

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return self.alert_history[-limit:]

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_timestamp = datetime.now()
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")

    def suppress_alert(self, alert_id: str):
        """Suppress an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.SUPPRESSED
            logger.info(f"Alert {alert_id} suppressed")

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of current alert state"""
        active_count = len(self.active_alerts)
        severity_counts = {}
        for alert in self.active_alerts.values():
            severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1

        recent_alerts = [alert for alert in self.alert_history if alert.timestamp > datetime.now() - timedelta(hours=24)]

        return {
            "active_alerts": active_count,
            "severity_breakdown": severity_counts,
            "alerts_last_24h": len(recent_alerts),
            "last_updated": datetime.now().isoformat()
        }

class AlertingService:
    """Main alerting service that coordinates alert management"""

    def __init__(self):
        self.alert_manager = AlertManager()
        self.running = False

    async def start(self):
        """Start the alerting service"""
        self.running = True
        logger.info("Alerting service started")

        while self.running:
            try:
                # In a real implementation, this would get metrics from the metrics collector
                # For now, we'll simulate the process
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in alerting service: {e}")
                await asyncio.sleep(5)

    async def stop(self):
        """Stop the alerting service"""
        self.running = False
        logger.info("Alerting service stopped")

    async def process_metrics(self, metrics: Dict[str, Any]):
        """Process incoming metrics and evaluate alerts"""
        await self.alert_manager.evaluate_rules(metrics)