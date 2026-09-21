"""
Alert Management System

Handles sending alerts for various health conditions through multiple channels
including email, Slack, webhooks, and other notification systems.
"""

import asyncio
import smtplib
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass

@dataclass
class Alert:
    """Represents an alert message"""
    alert_id: str
    severity: str  # critical, warning, info
    title: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    service: Optional[str] = None
    channels: List[str] = None

    def __post_init__(self):
        if self.channels is None:
            self.channels = []

class AlertManager:
    """Manages alert sending through multiple channels"""

    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.enabled = config.get('enabled', True)
        self.channels = config.get('channels', {})
        self.alert_history: List[Alert] = []
        self.rate_limits: Dict[str, datetime] = {}
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def send_critical_alert(self, title: str, message: str, details: Dict[str, Any] = None) -> bool:
        """Send a critical alert"""
        if not self.enabled:
            return True

        alert = Alert(
            alert_id=f"critical-{datetime.now().timestamp()}",
            severity="critical",
            title=title,
            message=message,
            details=details or {},
            timestamp=datetime.now(),
            channels=["email", "slack", "webhook"]
        )

        return await self._send_alert(alert)

    async def send_warning_alert(self, title: str, message: str, details: Dict[str, Any] = None) -> bool:
        """Send a warning alert"""
        if not self.enabled:
            return True

        alert = Alert(
            alert_id=f"warning-{datetime.now().timestamp()}",
            severity="warning",
            title=title,
            message=message,
            details=details or {},
            timestamp=datetime.now(),
            channels=["slack", "webhook"]
        )

        return await self._send_alert(alert)

    async def send_info_alert(self, title: str, message: str, details: Dict[str, Any] = None) -> bool:
        """Send an informational alert"""
        if not self.enabled:
            return True

        alert = Alert(
            alert_id=f"info-{datetime.now().timestamp()}",
            severity="info",
            title=title,
            message=message,
            details=details or {},
            timestamp=datetime.now(),
            channels=["webhook"]
        )

        return await self._send_alert(alert)

    async def send_service_alert(self, service_id: str, status: str, message: str, details: Dict[str, Any] = None) -> bool:
        """Send a service-specific alert"""
        if not self.enabled:
            return True

        severity = "critical" if status == "critical" else "warning" if status == "degraded" else "info"

        alert = Alert(
            alert_id=f"service-{service_id}-{datetime.now().timestamp()}",
            severity=severity,
            title=f"Service Alert: {service_id}",
            message=message,
            details=details or {},
            timestamp=datetime.now(),
            service=service_id,
            channels=["email", "slack"] if severity == "critical" else ["slack"]
        )

        return await self._send_alert(alert)

    async def send_sla_violation_alert(self, sla_type: str, current_value: float, threshold: float, details: Dict[str, Any] = None) -> bool:
        """Send SLA violation alert"""
        if not self.enabled:
            return True

        title = f"SLA Violation: {sla_type}"
        message = f"SLA violation detected for {sla_type}. Current: {current_value}, Threshold: {threshold}"

        alert = Alert(
            alert_id=f"sla-{sla_type}-{datetime.now().timestamp()}",
            severity="warning",
            title=title,
            message=message,
            details=details or {},
            timestamp=datetime.now(),
            channels=["email", "slack"]
        )

        return await self._send_alert(alert)

    async def _send_alert(self, alert: Alert) -> bool:
        """Send alert through configured channels"""
        try:
            # Check rate limiting
            if not self._check_rate_limit(alert):
                self.logger.info(f"Alert rate limited: {alert.title}")
                return False

            # Store alert in history
            self.alert_history.append(alert)
            self._cleanup_alert_history()

            # Send through each configured channel
            success_count = 0
            total_channels = len(alert.channels)

            for channel in alert.channels:
                try:
                    if await self._send_to_channel(alert, channel):
                        success_count += 1
                        self.logger.debug(f"Alert sent successfully via {channel}")
                    else:
                        self.logger.warning(f"Failed to send alert via {channel}")
                except Exception as e:
                    self.logger.error(f"Error sending alert via {channel}: {e}")

            # Log overall result
            if success_count > 0:
                self.logger.info(f"Alert sent: {alert.title} ({success_count}/{total_channels} channels)")
                return True
            else:
                self.logger.error(f"Failed to send alert: {alert.title}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")
            return False

    async def _send_to_channel(self, alert: Alert, channel: str) -> bool:
        """Send alert to specific channel"""
        if channel == "email":
            return await self._send_email_alert(alert)
        elif channel == "slack":
            return await self._send_slack_alert(alert)
        elif channel == "webhook":
            return await self._send_webhook_alert(alert)
        else:
            self.logger.warning(f"Unknown alert channel: {channel}")
            return False

    async def _send_email_alert(self, alert: Alert) -> bool:
        """Send alert via email"""
        email_config = self.channels.get('email', {})
        if not email_config.get('enabled', False):
            return True  # Not an error if email is disabled

        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = email_config.get('sender', 'health-monitor@dmlogn8n.com')
            msg['To'] = ', '.join(email_config.get('recipients', []))
            msg['Subject'] = f"[{alert.severity.upper()}] {alert.title}"

            # Create email body
            body = self._create_email_body(alert)
            msg.attach(MIMEText(body, 'html'))

            # Send email
            smtp_server = email_config.get('smtp_server')
            smtp_port = email_config.get('smtp_port', 587)
            username = email_config.get('username')
            password = email_config.get('password')

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                if username and password:
                    server.login(username, password)
                server.send_message(msg)

            return True

        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False

    async def _send_slack_alert(self, alert: Alert) -> bool:
        """Send alert to Slack"""
        slack_config = self.channels.get('slack', {})
        if not slack_config.get('enabled', False):
            return True

        try:
            webhook_url = slack_config.get('webhook_url')
            if not webhook_url:
                self.logger.warning("Slack webhook URL not configured")
                return False

            # Create Slack message
            slack_message = self._create_slack_message(alert, slack_config)

            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.post(webhook_url, json=slack_message) as response:
                return response.status == 200

        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
            return False

    async def _send_webhook_alert(self, alert: Alert) -> bool:
        """Send alert via webhook"""
        webhook_config = self.channels.get('webhook', {})
        if not webhook_config.get('enabled', False):
            return True

        try:
            webhook_url = webhook_config.get('url')
            if not webhook_url:
                self.logger.warning("Webhook URL not configured")
                return False

            # Create webhook payload
            payload = {
                "alert_id": alert.alert_id,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "details": alert.details,
                "timestamp": alert.timestamp.isoformat(),
                "service": alert.service
            }

            if not self.session:
                self.session = aiohttp.ClientSession()

            headers = webhook_config.get('headers', {})
            async with self.session.post(webhook_url, json=payload, headers=headers) as response:
                return response.status == 200

        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
            return False

    def _create_email_body(self, alert: Alert) -> str:
        """Create HTML email body"""
        severity_colors = {
            "critical": "#dc3545",
            "warning": "#ffc107",
            "info": "#17a2b8"
        }

        color = severity_colors.get(alert.severity, "#6c757d")

        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; border-top: none; }}
                .details {{ margin-top: 20px; }}
                .footer {{ margin-top: 20px; font-size: 12px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{alert.title}</h2>
                <p>Severity: {alert.severity.upper()}</p>
            </div>
            <div class="content">
                <p><strong>Message:</strong> {alert.message}</p>
                <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                {f'<p><strong>Service:</strong> {alert.service}</p>' if alert.service else ''}

                <div class="details">
                    <h4>Details:</h4>
                    <pre>{json.dumps(alert.details, indent=2)}</pre>
                </div>
            </div>
            <div class="footer">
                <p>This alert was generated by DMLogn8n Health Monitor</p>
            </div>
        </body>
        </html>
        """

        return html_body

    def _create_slack_message(self, alert: Alert, slack_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create Slack message payload"""
        severity_colors = {
            "critical": "danger",
            "warning": "warning",
            "info": "good"
        }

        color = severity_colors.get(alert.severity, "good")
        channel = slack_config.get('channel', '#alerts')

        message = {
            "channel": channel,
            "username": "Health Monitor",
            "icon_emoji": ":warning:" if alert.severity == "critical" else ":information_source:",
            "attachments": [
                {
                    "color": color,
                    "title": alert.title,
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Severity",
                            "value": alert.severity.upper(),
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                            "short": True
                        }
                    ],
                    "footer": "DMLogn8n Health Monitor",
                    "ts": int(alert.timestamp.timestamp())
                }
            ]
        }

        if alert.service:
            message["attachments"][0]["fields"].append({
                "title": "Service",
                "value": alert.service,
                "short": True
            })

        if alert.details:
            # Add key details as fields
            for key, value in list(alert.details.items())[:5]:  # Limit to 5 key details
                if isinstance(value, (str, int, float, bool)):
                    message["attachments"][0]["fields"].append({
                        "title": key.replace('_', ' ').title(),
                        "value": str(value),
                        "short": True
                    })

        return message

    def _check_rate_limit(self, alert: Alert) -> bool:
        """Check if alert should be sent based on rate limiting"""
        # Rate limit by service and severity
        rate_key = f"{alert.service or 'global'}-{alert.severity}"

        # Different rate limits for different severities
        rate_limits = {
            "critical": timedelta(minutes=5),
            "warning": timedelta(minutes=15),
            "info": timedelta(hours=1)
        }

        rate_limit = rate_limits.get(alert.severity, timedelta(minutes=15))

        if rate_key in self.rate_limits:
            last_sent = self.rate_limits[rate_key]
            if datetime.now() - last_sent < rate_limit:
                return False

        # Update rate limit
        self.rate_limits[rate_key] = datetime.now()
        return True

    def _cleanup_alert_history(self):
        """Clean up old alert history"""
        # Keep last 1000 alerts
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-500:]

        # Clean up old rate limits
        current_time = datetime.now()
        expired_keys = [
            key for key, timestamp in self.rate_limits.items()
            if current_time - timestamp > timedelta(hours=24)
        ]
        for key in expired_keys:
            del self.rate_limits[key]

    async def test_alert_channels(self) -> Dict[str, bool]:
        """Test all alert channels"""
        test_alert = Alert(
            alert_id="test",
            severity="info",
            title="Test Alert",
            message="This is a test alert from the DMLogn8n Health Monitor",
            details={"test": True},
            timestamp=datetime.now(),
            channels=["email", "slack", "webhook"]
        )

        results = {}
        for channel in test_alert.channels:
            try:
                results[channel] = await self._send_to_channel(test_alert, channel)
            except Exception as e:
                self.logger.error(f"Test failed for {channel}: {e}")
                results[channel] = False

        return results

    def get_alert_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]

        stats = {
            "total_alerts": len(recent_alerts),
            "by_severity": {
                "critical": len([a for a in recent_alerts if a.severity == "critical"]),
                "warning": len([a for a in recent_alerts if a.severity == "warning"]),
                "info": len([a for a in recent_alerts if a.severity == "info"])
            },
            "by_service": {},
            "by_channel": {
                "email": 0,
                "slack": 0,
                "webhook": 0
            },
            "most_active_service": None,
            "time_period_hours": hours
        }

        # Count by service
        service_counts = {}
        for alert in recent_alerts:
            if alert.service:
                service_counts[alert.service] = service_counts.get(alert.service, 0) + 1

            # Count by channel
            for channel in alert.channels:
                if channel in stats["by_channel"]:
                    stats["by_channel"][channel] += 1

        stats["by_service"] = service_counts

        if service_counts:
            most_active = max(service_counts.items(), key=lambda x: x[1])
            stats["most_active_service"] = {
                "service": most_active[0],
                "alert_count": most_active[1]
            }

        return stats

    async def send_daily_summary(self) -> bool:
        """Send daily health summary"""
        try:
            stats = self.get_alert_statistics(hours=24)

            if stats["total_alerts"] == 0:
                return True  # No alerts, no summary needed

            # Create summary message
            summary_title = f"Daily Health Summary - {datetime.now().strftime('%Y-%m-%d')}"
            summary_message = f"""
            Total Alerts: {stats['total_alerts']}
            Critical: {stats['by_severity']['critical']}
            Warning: {stats['by_severity']['warning']}
            Info: {stats['by_severity']['info']}
            """

            if stats["most_active_service"]:
                summary_message += f"""
                Most Active Service: {stats['most_active_service']['service']} ({stats['most_active_service']['alert_count']} alerts)
                """

            # Send summary as info alert
            return await self.send_info_alert(summary_title, summary_message.strip(), stats)

        except Exception as e:
            self.logger.error(f"Failed to send daily summary: {e}")
            return False