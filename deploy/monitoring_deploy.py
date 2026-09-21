#!/usr/bin/env python3
"""
Monitoring Deploy for DMLogn8n
Deployment monitoring and alerting system
"""

import os
import sys
import json
import time
import logging
import requests
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import psutil
import docker


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class Metric:
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str] = None
    timestamp: datetime = None
    description: str = ""


@dataclass
class Alert:
    id: str
    level: AlertLevel
    service: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class MonitoringRule:
    name: str
    metric_name: str
    condition: str
    threshold: float
    alert_level: AlertLevel
    service: str
    enabled: bool = True
    description: str = ""


class MonitoringDeploy:
    """Deployment monitoring and alerting system"""

    def __init__(self, environment: str):
        self.environment = environment
        self.logger = logging.getLogger(__name__)

        # Paths
        self.monitoring_dir = Path("/etc/dmlogn8n/monitoring")
        self.metrics_dir = Path("/var/lib/dmlogn8n/metrics")
        self.alerts_dir = Path("/var/lib/dmlogn8n/alerts")
        self.logs_dir = Path("/var/log/dmlogn8n/monitoring")

        # Ensure directories exist
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Docker client
        self.docker_client = None
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            self.logger.warning(f"Docker client not available: {e}")

        # Monitoring state
        self.is_running = False
        self.monitoring_thread = None
        self.metrics = {}
        self.alerts = []
        self.rules = self.get_monitoring_rules()

        # Configuration
        self.config = self.load_monitoring_config()

        # Alert callbacks
        self.alert_callbacks = []

    def load_monitoring_config(self) -> Dict[str, Any]:
        """Load monitoring configuration"""
        config_file = self.monitoring_dir / f"{self.environment}.json"

        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)

        # Default configuration
        default_config = {
            "enabled": True,
            "metrics_interval": 30,  # seconds
            "alert_interval": 60,    # seconds
            "retention_days": 30,
            "prometheus_enabled": self.environment != "development",
            "grafana_enabled": self.environment != "development",
            "alert_webhooks": [],
            "smtp_enabled": False,
            "slack_enabled": False,
            "discord_enabled": False
        }

        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)

        return default_config

    def get_monitoring_rules(self) -> List[MonitoringRule]:
        """Get monitoring rules"""
        return [
            # System resource rules
            MonitoringRule(
                name="cpu_usage_high",
                metric_name="system_cpu_usage",
                condition="greater_than",
                threshold=80.0,
                alert_level=AlertLevel.WARNING,
                service="system",
                description="High CPU usage detected"
            ),
            MonitoringRule(
                name="memory_usage_high",
                metric_name="system_memory_usage",
                condition="greater_than",
                threshold=85.0,
                alert_level=AlertLevel.WARNING,
                service="system",
                description="High memory usage detected"
            ),
            MonitoringRule(
                name="disk_usage_high",
                metric_name="system_disk_usage",
                condition="greater_than",
                threshold=90.0,
                alert_level=AlertLevel.ERROR,
                service="system",
                description="High disk usage detected"
            ),

            # Service-specific rules
            MonitoringRule(
                name="api_response_time_high",
                metric_name="api_response_time",
                condition="greater_than",
                threshold=5.0,
                alert_level=AlertLevel.WARNING,
                service="api",
                description="API response time is high"
            ),
            MonitoringRule(
                name="api_error_rate_high",
                metric_name="api_error_rate",
                condition="greater_than",
                threshold=5.0,
                alert_level=AlertLevel.ERROR,
                service="api",
                description="API error rate is high"
            ),
            MonitoringRule(
                name="n8n_workflow_failures",
                metric_name="n8n_workflow_failures",
                condition="greater_than",
                threshold=0.0,
                alert_level=AlertLevel.ERROR,
                service="n8n",
                description="N8N workflow failures detected"
            ),
            MonitoringRule(
                name="database_connection_failures",
                metric_name="database_connection_failures",
                condition="greater_than",
                threshold=0.0,
                alert_level=AlertLevel.CRITICAL,
                service="database",
                description="Database connection failures detected"
            ),
            MonitoringRule(
                name="container_restart_count",
                metric_name="container_restart_count",
                condition="greater_than",
                threshold=5.0,
                alert_level=AlertLevel.WARNING,
                service="containers",
                description="Container restart count is high"
            ),
        ]

    def collect_system_metrics(self) -> List[Metric]:
        """Collect system-level metrics"""
        metrics = []
        timestamp = datetime.now()

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics.append(Metric(
            name="system_cpu_usage",
            value=cpu_percent,
            metric_type=MetricType.GAUGE,
            timestamp=timestamp,
            description="System CPU usage percentage"
        ))

        # Memory usage
        memory = psutil.virtual_memory()
        metrics.append(Metric(
            name="system_memory_usage",
            value=memory.percent,
            metric_type=MetricType.GAUGE,
            timestamp=timestamp,
            description="System memory usage percentage"
        ))

        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        metrics.append(Metric(
            name="system_disk_usage",
            value=disk_percent,
            metric_type=MetricType.GAUGE,
            timestamp=timestamp,
            description="System disk usage percentage"
        ))

        # Network I/O
        network = psutil.net_io_counters()
        metrics.append(Metric(
            name="network_bytes_sent",
            value=network.bytes_sent,
            metric_type=MetricType.COUNTER,
            timestamp=timestamp,
            description="Network bytes sent"
        ))
        metrics.append(Metric(
            name="network_bytes_received",
            value=network.bytes_recv,
            metric_type=MetricType.COUNTER,
            timestamp=timestamp,
            description="Network bytes received"
        ))

        return metrics

    def collect_docker_metrics(self) -> List[Metric]:
        """Collect Docker container metrics"""
        metrics = []
        timestamp = datetime.now()

        if not self.docker_client:
            return metrics

        try:
            containers = self.docker_client.containers.list(all=True)

            for container in containers:
                if not container.name.startswith("dmlogn8n-"):
                    continue

                container_name = container.name.replace("dmlogn8n-", "")

                # Container status
                status = 1 if container.status == "running" else 0
                metrics.append(Metric(
                    name="container_status",
                    value=status,
                    metric_type=MetricType.GAUGE,
                    labels={"container": container_name},
                    timestamp=timestamp,
                    description=f"Container {container_name} status"
                ))

                # Container restart count
                restart_count = container.attrs.get("RestartCount", 0)
                metrics.append(Metric(
                    name="container_restart_count",
                    value=restart_count,
                    metric_type=MetricType.GAUGE,
                    labels={"container": container_name},
                    timestamp=timestamp,
                    description=f"Container {container_name} restart count"
                ))

                # Container resource usage (if running)
                if container.status == "running":
                    try:
                        stats = container.stats(stream=False)

                        # CPU usage
                        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                                   stats["precpu_stats"]["cpu_usage"]["total_usage"]
                        system_cpu_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                                         stats["precpu_stats"]["system_cpu_usage"]
                        cpu_percent = (cpu_delta / system_cpu_delta) * \
                                    len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"]) * 100

                        metrics.append(Metric(
                            name="container_cpu_usage",
                            value=cpu_percent,
                            metric_type=MetricType.GAUGE,
                            labels={"container": container_name},
                            timestamp=timestamp,
                            description=f"Container {container_name} CPU usage"
                        ))

                        # Memory usage
                        memory_usage = stats["memory_stats"]["usage"]
                        memory_limit = stats["memory_stats"]["limit"]
                        memory_percent = (memory_usage / memory_limit) * 100

                        metrics.append(Metric(
                            name="container_memory_usage",
                            value=memory_percent,
                            metric_type=MetricType.GAUGE,
                            labels={"container": container_name},
                            timestamp=timestamp,
                            description=f"Container {container_name} memory usage"
                        ))

                    except Exception as e:
                        self.logger.warning(f"Failed to get stats for container {container.name}: {e}")

        except Exception as e:
            self.logger.error(f"Failed to collect Docker metrics: {e}")

        return metrics

    def collect_service_metrics(self) -> List[Metric]:
        """Collect service-specific metrics"""
        metrics = []
        timestamp = datetime.now()

        # API health check and response time
        try:
            start_time = time.time()
            response = requests.get("http://localhost:8000/health", timeout=10)
            response_time = time.time() - start_time

            metrics.append(Metric(
                name="api_response_time",
                value=response_time,
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                description="API response time in seconds"
            ))

            metrics.append(Metric(
                name="api_status_code",
                value=response.status_code,
                metric_type=MetricType.GAUGE,
                labels={"endpoint": "/health"},
                timestamp=timestamp,
                description="API health endpoint status code"
            ))

            # API error rate (simplified - would need more sophisticated tracking)
            if response.status_code >= 400:
                metrics.append(Metric(
                    name="api_error_rate",
                    value=1.0,
                    metric_type=MetricType.GAUGE,
                    timestamp=timestamp,
                    description="API error rate"
                ))
            else:
                metrics.append(Metric(
                    name="api_error_rate",
                    value=0.0,
                    metric_type=MetricType.GAUGE,
                    timestamp=timestamp,
                    description="API error rate"
                ))

        except requests.exceptions.RequestException as e:
            self.logger.warning(f"API health check failed: {e}")
            metrics.append(Metric(
                name="api_error_rate",
                value=100.0,
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                description="API error rate"
            ))

        # N8N health check
        try:
            response = requests.get("http://localhost:5678/healthz", timeout=10)
            metrics.append(Metric(
                name="n8n_status_code",
                value=response.status_code,
                metric_type=MetricType.GAUGE,
                timestamp=timestamp,
                description="N8N health status"
            ))

        except requests.exceptions.RequestException as e:
            self.logger.warning(f"N8N health check failed: {e}")

        return metrics

    def collect_metrics(self):
        """Collect all metrics"""
        all_metrics = []

        # Collect system metrics
        all_metrics.extend(self.collect_system_metrics())

        # Collect Docker metrics
        all_metrics.extend(self.collect_docker_metrics())

        # Collect service metrics
        all_metrics.extend(self.collect_service_metrics())

        # Store metrics
        for metric in all_metrics:
            metric_key = f"{metric.name}_{metric.timestamp.isoformat()}"
            self.metrics[metric_key] = metric

        # Write metrics to file
        metrics_file = self.metrics_dir / f"metrics_{int(time.time())}.json"
        metrics_data = [asdict(m) for m in all_metrics]
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f, indent=2, default=str)

        # Clean up old metrics
        self.cleanup_old_metrics()

        self.logger.debug(f"Collected {len(all_metrics)} metrics")

    def evaluate_rules(self) -> List[Alert]:
        """Evaluate monitoring rules and generate alerts"""
        alerts = []
        timestamp = datetime.now()

        for rule in self.rules:
            if not rule.enabled:
                continue

            # Find the latest metric for this rule
            latest_metric = None
            for metric in self.metrics.values():
                if metric.name == rule.metric_name:
                    if latest_metric is None or metric.timestamp > latest_metric.timestamp:
                        latest_metric = metric

            if not latest_metric:
                continue

            # Evaluate condition
            triggered = False
            if rule.condition == "greater_than":
                triggered = latest_metric.value > rule.threshold
            elif rule.condition == "less_than":
                triggered = latest_metric.value < rule.threshold
            elif rule.condition == "equals":
                triggered = latest_metric.value == rule.threshold

            if triggered:
                # Check if we already have an active alert for this rule
                existing_alert = None
                for alert in self.alerts:
                    if not alert.resolved and alert.service == rule.service and rule.name in alert.message:
                        existing_alert = alert
                        break

                if not existing_alert:
                    # Create new alert
                    alert = Alert(
                        id=f"alert_{int(time.time())}_{rule.name}",
                        level=rule.alert_level,
                        service=rule.service,
                        message=f"{rule.name}: {rule.description}",
                        details={
                            "rule_name": rule.name,
                            "metric_name": rule.metric_name,
                            "current_value": latest_metric.value,
                            "threshold": rule.threshold,
                            "condition": rule.condition,
                            "metric_timestamp": latest_metric.timestamp.isoformat()
                        },
                        timestamp=timestamp
                    )
                    alerts.append(alert)
                    self.alerts.append(alert)

        # Resolve alerts that are no longer triggered
        for alert in self.alerts:
            if not alert.resolved:
                # Check if the condition is still active
                rule = next((r for r in self.rules if r.name in alert.message), None)
                if rule:
                    latest_metric = None
                    for metric in self.metrics.values():
                        if metric.name == rule.metric_name:
                            if latest_metric is None or metric.timestamp > latest_metric.timestamp:
                                latest_metric = metric

                    if latest_metric:
                        triggered = False
                        if rule.condition == "greater_than":
                            triggered = latest_metric.value > rule.threshold
                        elif rule.condition == "less_than":
                            triggered = latest_metric.value < rule.threshold
                        elif rule.condition == "equals":
                            triggered = latest_metric.value == rule.threshold

                        if not triggered:
                            alert.resolved = True
                            alert.resolved_at = datetime.now()

        return alerts

    def send_alert(self, alert: Alert):
        """Send alert notification"""
        self.logger.warning(f"ALERT [{alert.level.value.upper()}] {alert.service}: {alert.message}")

        # Call registered alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback failed: {e}")

        # Send to webhooks
        for webhook_url in self.config.get("alert_webhooks", []):
            try:
                response = requests.post(
                    webhook_url,
                    json=asdict(alert),
                    timeout=10
                )
                response.raise_for_status()
            except Exception as e:
                self.logger.error(f"Failed to send alert webhook: {e}")

        # Save alert to file
        alert_file = self.alerts_dir / f"{alert.id}.json"
        with open(alert_file, 'w') as f:
            json.dump(asdict(alert), f, indent=2, default=str)

    def monitoring_loop(self):
        """Main monitoring loop"""
        self.logger.info("Starting monitoring loop")

        last_metrics_time = 0
        last_alerts_time = 0

        while self.is_running:
            try:
                current_time = time.time()

                # Collect metrics
                if current_time - last_metrics_time >= self.config["metrics_interval"]:
                    self.collect_metrics()
                    last_metrics_time = current_time

                # Evaluate rules and send alerts
                if current_time - last_alerts_time >= self.config["alert_interval"]:
                    new_alerts = self.evaluate_rules()
                    for alert in new_alerts:
                        self.send_alert(alert)
                    last_alerts_time = current_time

                # Sleep for a short interval
                time.sleep(5)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)

    def setup_prometheus(self) -> bool:
        """Setup Prometheus monitoring"""
        try:
            if not self.config.get("prometheus_enabled", False):
                return True

            self.logger.info("Setting up Prometheus...")

            # Create Prometheus configuration
            prometheus_config = {
                "global": {
                    "scrape_interval": "30s",
                    "evaluation_interval": "30s"
                },
                "rule_files": [
                    "/etc/prometheus/rules/*.yml"
                ],
                "scrape_configs": [
                    {
                        "job_name": "dmlogn8n",
                        "static_configs": [
                            {
                                "targets": [
                                    "localhost:8000",  # API
                                    "localhost:3001",  # Character Coder
                                ]
                            }
                        ]
                    },
                    {
                        "job_name": "node-exporter",
                        "static_configs": [
                            {
                                "targets": ["localhost:9100"]
                            }
                        ]
                    }
                ]
            }

            prometheus_config_file = self.monitoring_dir / "prometheus.yml"
            with open(prometheus_config_file, 'w') as f:
                yaml.dump(prometheus_config, f)

            # Create alerting rules
            alert_rules = {
                "groups": [
                    {
                        "name": "dmlogn8n_alerts",
                        "rules": [
                            {
                                "alert": "HighCPUUsage",
                                "expr": "system_cpu_usage > 80",
                                "for": "5m",
                                "labels": {
                                    "severity": "warning"
                                },
                                "annotations": {
                                    "summary": "High CPU usage detected"
                                }
                            },
                            {
                                "alert": "HighMemoryUsage",
                                "expr": "system_memory_usage > 85",
                                "for": "5m",
                                "labels": {
                                    "severity": "warning"
                                },
                                "annotations": {
                                    "summary": "High memory usage detected"
                                }
                            }
                        ]
                    }
                ]
            }

            alert_rules_file = self.monitoring_dir / "alert_rules.yml"
            with open(alert_rules_file, 'w') as f:
                yaml.dump(alert_rules, f)

            self.logger.info("Prometheus configuration created")
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup Prometheus: {e}")
            return False

    def setup_grafana(self) -> bool:
        """Setup Grafana dashboards"""
        try:
            if not self.config.get("grafana_enabled", False):
                return True

            self.logger.info("Setting up Grafana dashboards...")

            # Create Grafana dashboard configuration
            dashboard = {
                "dashboard": {
                    "title": "DMLogn8n Monitoring",
                    "panels": [
                        {
                            "title": "System CPU Usage",
                            "type": "stat",
                            "targets": [
                                {
                                    "expr": "system_cpu_usage",
                                    "legendFormat": "CPU Usage %"
                                }
                            ]
                        },
                        {
                            "title": "System Memory Usage",
                            "type": "stat",
                            "targets": [
                                {
                                    "expr": "system_memory_usage",
                                    "legendFormat": "Memory Usage %"
                                }
                            ]
                        },
                        {
                            "title": "API Response Time",
                            "type": "graph",
                            "targets": [
                                {
                                    "expr": "api_response_time",
                                    "legendFormat": "Response Time"
                                }
                            ]
                        }
                    ],
                    "time": {
                        "from": "now-1h",
                        "to": "now"
                    },
                    "refresh": "30s"
                }
            }

            dashboard_file = self.monitoring_dir / "grafana_dashboard.json"
            with open(dashboard_file, 'w') as f:
                json.dump(dashboard, f, indent=2)

            self.logger.info("Grafana dashboard configuration created")
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup Grafana: {e}")
            return False

    def cleanup_old_metrics(self):
        """Clean up old metric files"""
        try:
            retention_days = self.config.get("retention_days", 30)
            cutoff_time = time.time() - (retention_days * 24 * 60 * 60)

            for metrics_file in self.metrics_dir.glob("metrics_*.json"):
                if metrics_file.stat().st_mtime < cutoff_time:
                    metrics_file.unlink()
                    self.logger.debug(f"Removed old metrics file: {metrics_file}")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old metrics: {e}")

    def start_monitoring(self):
        """Start the monitoring system"""
        if self.is_running:
            self.logger.warning("Monitoring is already running")
            return

        if not self.config.get("enabled", True):
            self.logger.info("Monitoring is disabled")
            return

        self.logger.info("Starting DMLogn8n monitoring system")
        self.is_running = True

        # Setup monitoring components
        self.setup_prometheus()
        self.setup_grafana()

        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.logger.info("Stopping monitoring system")
        self.is_running = False

        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)

    def setup_monitoring(self) -> bool:
        """Setup monitoring system for deployment"""
        try:
            self.logger.info(f"Setting up monitoring for {self.environment} environment")

            # Setup monitoring components
            if not self.setup_prometheus():
                return False

            if not self.setup_grafana():
                return False

            # Start monitoring if enabled
            if self.config.get("enabled", True):
                self.start_monitoring()

            self.logger.info("Monitoring setup completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup monitoring: {e}")
            return False

    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add alert callback function"""
        self.alert_callbacks.append(callback)

    def get_current_metrics(self) -> List[Metric]:
        """Get current metrics"""
        return list(self.metrics.values())

    def get_active_alerts(self) -> List[Alert]:
        """Get active (unresolved) alerts"""
        return [alert for alert in self.alerts if not alert.resolved]


def main():
    """Main entry point for monitoring setup"""
    import argparse

    parser = argparse.ArgumentParser(description="DMLogn8n Monitoring Deploy")
    parser.add_argument("environment", choices=["development", "staging", "production"],
                       help="Target environment")
    parser.add_argument("--action", choices=["setup", "start", "stop", "status"],
                       default="setup", help="Action to perform")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize monitoring deploy
    monitoring = MonitoringDeploy(args.environment)

    try:
        if args.action == "setup":
            success = monitoring.setup_monitoring()
        elif args.action == "start":
            monitoring.start_monitoring()
            success = True
        elif args.action == "stop":
            monitoring.stop_monitoring()
            success = True
        elif args.action == "status":
            if monitoring.is_running:
                print("✅ Monitoring is running")
                print(f"📊 Active alerts: {len(monitoring.get_active_alerts())}")
                print(f"📈 Current metrics: {len(monitoring.get_current_metrics())}")
            else:
                print("❌ Monitoring is not running")
            success = True
        else:
            success = False

        if success:
            print("✅ Monitoring operation completed successfully!")
            if args.action == "setup":
                print("📊 Prometheus: Enabled" if monitoring.config.get("prometheus_enabled") else "📊 Prometheus: Disabled")
                print("📈 Grafana: Enabled" if monitoring.config.get("grafana_enabled") else "📈 Grafana: Disabled")
            sys.exit(0)
        else:
            print("❌ Monitoring operation failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user")
        monitoring.stop_monitoring()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        monitoring.stop_monitoring()
        sys.exit(1)


if __name__ == "__main__":
    main()