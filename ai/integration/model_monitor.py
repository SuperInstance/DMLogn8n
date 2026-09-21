#!/usr/bin/env python3
"""
Advanced AI Model Monitor - Comprehensive performance monitoring and alerting
Provides real-time monitoring, quality assessment, and automated optimization
"""

import asyncio
import time
import json
import logging
import numpy as np
import psutil
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import aiohttp
import prometheus_client as prometheus

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """Types of metrics to monitor"""
    RESPONSE_TIME = "response_time"
    SUCCESS_RATE = "success_rate"
    ERROR_RATE = "error_rate"
    TOKEN_USAGE = "token_usage"
    COST = "cost"
    QUALITY_SCORE = "quality_score"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    GPU_USAGE = "gpu_usage"
    REQUEST_RATE = "request_rate"
    CACHE_HIT_RATE = "cache_hit_rate"

@dataclass
class MonitoringConfig:
    """Configuration for model monitoring"""
    models: List[str]
    monitoring_interval: float = 60.0  # seconds
    alert_thresholds: Dict[str, Dict[str, float]] = None
    enable_alerts: bool = True
    enable_logging: bool = True
    enable_metrics_export: bool = True
    metrics_port: int = 8000
    log_retention_days: int = 30
    alert_cooldown: int = 300  # seconds
    email_alerts: bool = False
    email_config: Optional[Dict[str, str]] = None
    webhook_url: Optional[str] = None

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    model_name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    unit: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Alert:
    """Alert definition"""
    alert_id: str
    model_name: str
    metric_type: MetricType
    severity: AlertSeverity
    message: str
    threshold: float
    actual_value: float
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class HealthCheck:
    """Health check result"""
    model_name: str
    status: str  # healthy, degraded, unhealthy
    response_time: float
    success_rate: float
    last_check: datetime
    issues: List[str]
    metrics: Dict[str, float]

class ModelMonitor:
    """Advanced AI model performance monitoring system"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Metrics storage
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.current_metrics: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []

        # Health status
        self.health_status: Dict[str, HealthCheck] = {}

        # Monitoring state
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.last_alert_times: Dict[str, datetime] = {}

        # Prometheus metrics
        self.prometheus_metrics = {}
        self._initialize_prometheus_metrics()

        # Statistics
        self.stats = {
            "total_requests": 0,
            "total_errors": 0,
            "total_alerts": 0,
            "average_response_time": 0.0,
            "uptime": datetime.now()
        }

        logger.info(f"ModelMonitor initialized for {len(config.models)} models")

    def _initialize_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        for model_name in self.config.models:
            # Response time histogram
            self.prometheus_metrics[f"{model_name}_response_time"] = prometheus.Histogram(
                f"{model_name}_response_time_seconds",
                f"Response time for {model_name}",
                buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
            )

            # Request counter
            self.prometheus_metrics[f"{model_name}_requests_total"] = prometheus.Counter(
                f"{model_name}_requests_total",
                f"Total requests for {model_name}"
            )

            # Error counter
            self.prometheus_metrics[f"{model_name}_errors_total"] = prometheus.Counter(
                f"{model_name}_errors_total",
                f"Total errors for {model_name}"
            )

            # Success rate gauge
            self.prometheus_metrics[f"{model_name}_success_rate"] = prometheus.Gauge(
                f"{model_name}_success_rate",
                f"Success rate for {model_name}"
            )

            # Quality score gauge
            self.prometheus_metrics[f"{model_name}_quality_score"] = prometheus.Gauge(
                f"{model_name}_quality_score",
                f"Quality score for {model_name}"
            )

        # System metrics
        self.prometheus_metrics["system_cpu_usage"] = prometheus.Gauge(
            "system_cpu_usage_percent",
            "System CPU usage percentage"
        )

        self.prometheus_metrics["system_memory_usage"] = prometheus.Gauge(
            "system_memory_usage_percent",
            "System memory usage percentage"
        )

    async def start_monitoring(self):
        """Start the monitoring service"""
        if self.monitoring_active:
            logger.warning("Monitoring is already active")
            return

        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        # Start Prometheus metrics server
        if self.config.enable_metrics_export:
            prometheus.start_http_server(self.config.metrics_port)
            logger.info(f"Prometheus metrics server started on port {self.config.metrics_port}")

        logger.info("Model monitoring started")

    async def stop_monitoring(self):
        """Stop the monitoring service"""
        self.monitoring_active = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Model monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect metrics for all models
                await asyncio.gather(
                    *[self._collect_model_metrics(model_name) for model_name in self.config.models],
                    return_exceptions=True
                )

                # Collect system metrics
                await self._collect_system_metrics()

                # Check for alerts
                if self.config.enable_alerts:
                    await self._check_alert_conditions()

                # Perform health checks
                await self._perform_health_checks()

                # Wait for next interval
                await asyncio.sleep(self.config.monitoring_interval)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)

    async def _collect_model_metrics(self, model_name: str):
        """Collect metrics for a specific model"""
        try:
            # In a real implementation, this would collect actual metrics from the model
            # For demonstration, we'll generate simulated metrics

            timestamp = datetime.now()

            # Simulate metrics collection
            metrics = {
                MetricType.RESPONSE_TIME: np.random.normal(0.5, 0.1),
                MetricType.SUCCESS_RATE: np.random.uniform(0.95, 1.0),
                MetricType.TOKEN_USAGE: np.random.normal(150, 30),
                MetricType.COST: np.random.normal(0.01, 0.002),
                MetricType.QUALITY_SCORE: np.random.uniform(0.8, 0.95),
                MetricType.REQUEST_RATE: np.random.normal(10, 2),
                MetricType.CACHE_HIT_RATE: np.random.uniform(0.6, 0.9)
            }

            # Store metrics
            for metric_type, value in metrics.items():
                metric = PerformanceMetric(
                    model_name=model_name,
                    metric_type=metric_type,
                    value=value,
                    timestamp=timestamp,
                    unit=self._get_metric_unit(metric_type)
                )

                self.metrics_history[f"{model_name}_{metric_type.value}"].append(metric)
                self.current_metrics[model_name][metric_type.value] = value

                # Update Prometheus metrics
                self._update_prometheus_metric(model_name, metric_type, value)

        except Exception as e:
            logger.error(f"Failed to collect metrics for {model_name}: {e}")

    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.prometheus_metrics["system_cpu_usage"].set(cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            self.prometheus_metrics["system_memory_usage"].set(memory.percent)

            # GPU usage (if available)
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    for i, gpu in enumerate(gpus):
                        gpu_metric = PerformanceMetric(
                            model_name=f"gpu_{i}",
                            metric_type=MetricType.GPU_USAGE,
                            value=gpu.load * 100,
                            timestamp=datetime.now(),
                            unit="percent"
                        )
                        self.metrics_history[f"gpu_{i}_gpu_usage"].append(gpu_metric)
            except ImportError:
                # GPUtil not available
                pass

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")

    async def _check_alert_conditions(self):
        """Check for alert conditions"""
        if not self.config.alert_thresholds:
            return

        current_time = datetime.now()

        for model_name in self.config.models:
            for metric_type_str, threshold in self.config.alert_thresholds.get(model_name, {}).items():
                try:
                    metric_type = MetricType(metric_type_str)
                    current_value = self.current_metrics[model_name].get(metric_type_str)

                    if current_value is None:
                        continue

                    # Check threshold based on metric type
                    alert_triggered = False
                    if metric_type in [MetricType.RESPONSE_TIME, MetricType.ERROR_RATE, MetricType.COST]:
                        # Higher values are worse
                        alert_triggered = current_value > threshold
                    else:
                        # Lower values are worse
                        alert_triggered = current_value < threshold

                    if alert_triggered:
                        await self._trigger_alert(
                            model_name=model_name,
                            metric_type=metric_type,
                            current_value=current_value,
                            threshold=threshold,
                            severity=self._determine_alert_severity(metric_type, current_value, threshold)
                        )

                except Exception as e:
                    logger.error(f"Error checking alert condition for {model_name}.{metric_type_str}: {e}")

    async def _trigger_alert(self, model_name: str, metric_type: MetricType,
                           current_value: float, threshold: float, severity: AlertSeverity):
        """Trigger an alert"""
        alert_id = hashlib.md5(
            f"{model_name}_{metric_type.value}_{current_value}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        # Check alert cooldown
        cooldown_key = f"{model_name}_{metric_type.value}"
        if cooldown_key in self.last_alert_times:
            time_since_last = datetime.now() - self.last_alert_times[cooldown_key]
            if time_since_last.total_seconds() < self.config.alert_cooldown:
                return

        # Create alert
        alert = Alert(
            alert_id=alert_id,
            model_name=model_name,
            metric_type=metric_type,
            severity=severity,
            message=self._generate_alert_message(model_name, metric_type, current_value, threshold),
            threshold=threshold,
            actual_value=current_value,
            timestamp=datetime.now()
        )

        # Store alert
        self.alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.last_alert_times[cooldown_key] = datetime.now()
        self.stats["total_alerts"] += 1

        logger.warning(f"Alert triggered: {alert.message}")

        # Send notifications
        await self._send_alert_notification(alert)

    def _determine_alert_severity(self, metric_type: MetricType, current_value: float, threshold: float) -> AlertSeverity:
        """Determine alert severity based on deviation from threshold"""
        if metric_type in [MetricType.RESPONSE_TIME, MetricType.ERROR_RATE]:
            ratio = current_value / threshold
        else:
            ratio = threshold / current_value

        if ratio > 3.0:
            return AlertSeverity.CRITICAL
        elif ratio > 2.0:
            return AlertSeverity.ERROR
        elif ratio > 1.5:
            return AlertSeverity.WARNING
        else:
            return AlertSeverity.INFO

    def _generate_alert_message(self, model_name: str, metric_type: MetricType,
                              current_value: float, threshold: float) -> str:
        """Generate alert message"""
        unit = self._get_metric_unit(metric_type)
        if metric_type in [MetricType.RESPONSE_TIME, MetricType.ERROR_RATE, MetricType.COST]:
            return f"Model {model_name} {metric_type.value.replace('_', ' ').title()} is too high: {current_value:.2f}{unit} (threshold: {threshold:.2f}{unit})"
        else:
            return f"Model {model_name} {metric_type.value.replace('_', ' ').title()} is too low: {current_value:.2f}{unit} (threshold: {threshold:.2f}{unit})"

    def _get_metric_unit(self, metric_type: MetricType) -> str:
        """Get unit for metric type"""
        unit_map = {
            MetricType.RESPONSE_TIME: "s",
            MetricType.SUCCESS_RATE: "%",
            MetricType.ERROR_RATE: "%",
            MetricType.TOKEN_USAGE: "tokens",
            MetricType.COST: "$",
            MetricType.QUALITY_SCORE: "score",
            MetricType.MEMORY_USAGE: "MB",
            MetricType.CPU_USAGE: "%",
            MetricType.GPU_USAGE: "%",
            MetricType.REQUEST_RATE: "req/s",
            MetricType.CACHE_HIT_RATE: "%"
        }
        return unit_map.get(metric_type, "")

    async def _send_alert_notification(self, alert: Alert):
        """Send alert notification"""
        try:
            # Send email notification
            if self.config.email_alerts and self.config.email_config:
                await self._send_email_alert(alert)

            # Send webhook notification
            if self.config.webhook_url:
                await self._send_webhook_alert(alert)

        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")

    async def _send_email_alert(self, alert: Alert):
        """Send email alert"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.config.email_config['sender']
            msg['To'] = self.config.email_config['recipient']
            msg['Subject'] = f"[{alert.severity.value.upper()}] AI Model Alert: {alert.model_name}"

            body = f"""
            Alert Details:
            - Model: {alert.model_name}
            - Metric: {alert.metric_type.value}
            - Severity: {alert.severity.value}
            - Message: {alert.message}
            - Threshold: {alert.threshold}
            - Actual Value: {alert.actual_value}
            - Timestamp: {alert.timestamp}

            Please investigate this issue promptly.
            """

            msg.attach(MimeText(body, 'plain'))

            # Send email (this is a simplified example)
            # In production, you'd use proper SMTP configuration
            logger.info(f"Email alert would be sent: {alert.message}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    async def _send_webhook_alert(self, alert: Alert):
        """Send webhook alert"""
        try:
            payload = {
                "alert_id": alert.alert_id,
                "model_name": alert.model_name,
                "metric_type": alert.metric_type.value,
                "severity": alert.severity.value,
                "message": alert.message,
                "threshold": alert.threshold,
                "actual_value": alert.actual_value,
                "timestamp": alert.timestamp.isoformat()
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent successfully: {alert.alert_id}")
                    else:
                        logger.warning(f"Webhook alert failed with status {response.status}")

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")

    async def _perform_health_checks(self):
        """Perform health checks on all models"""
        for model_name in self.config.models:
            try:
                health = await self._check_model_health(model_name)
                self.health_status[model_name] = health

            except Exception as e:
                logger.error(f"Health check failed for {model_name}: {e}")
                self.health_status[model_name] = HealthCheck(
                    model_name=model_name,
                    status="unhealthy",
                    response_time=0.0,
                    success_rate=0.0,
                    last_check=datetime.now(),
                    issues=[f"Health check failed: {str(e)}"],
                    metrics={}
                )

    async def _check_model_health(self, model_name: str) -> HealthCheck:
        """Check health of a specific model"""
        issues = []
        metrics = {}

        # Get current metrics
        current = self.current_metrics.get(model_name, {})

        # Response time check
        response_time = current.get(MetricType.RESPONSE_TIME.value, 0.0)
        metrics["response_time"] = response_time
        if response_time > 2.0:
            issues.append(f"High response time: {response_time:.2f}s")

        # Success rate check
        success_rate = current.get(MetricType.SUCCESS_RATE.value, 1.0) * 100
        metrics["success_rate"] = success_rate
        if success_rate < 95:
            issues.append(f"Low success rate: {success_rate:.1f}%")

        # Quality score check
        quality_score = current.get(MetricType.QUALITY_SCORE.value, 1.0)
        metrics["quality_score"] = quality_score
        if quality_score < 0.7:
            issues.append(f"Low quality score: {quality_score:.2f}")

        # Determine overall status
        if not issues:
            status = "healthy"
        elif len(issues) <= 2:
            status = "degraded"
        else:
            status = "unhealthy"

        return HealthCheck(
            model_name=model_name,
            status=status,
            response_time=response_time,
            success_rate=success_rate,
            last_check=datetime.now(),
            issues=issues,
            metrics=metrics
        )

    def _update_prometheus_metric(self, model_name: str, metric_type: MetricType, value: float):
        """Update Prometheus metric"""
        try:
            if metric_type == MetricType.RESPONSE_TIME:
                self.prometheus_metrics[f"{model_name}_response_time"].observe(value)
            elif metric_type == MetricType.SUCCESS_RATE:
                self.prometheus_metrics[f"{model_name}_success_rate"].set(value)
            elif metric_type == MetricType.QUALITY_SCORE:
                self.prometheus_metrics[f"{model_name}_quality_score"].set(value)
            # Add more metric updates as needed
        except KeyError:
            # Metric not found
            pass

    async def record_request(self, model_name: str, response_time: float,
                           success: bool, token_usage: int = 0, cost: float = 0.0,
                           quality_score: Optional[float] = None):
        """Record a model request"""
        try:
            timestamp = datetime.now()

            # Update statistics
            self.stats["total_requests"] += 1
            if not success:
                self.stats["total_errors"] += 1

            # Update average response time
            total_requests = self.stats["total_requests"]
            current_avg = self.stats["average_response_time"]
            new_avg = (current_avg * (total_requests - 1) + response_time) / total_requests
            self.stats["average_response_time"] = new_avg

            # Record individual metrics
            metrics_to_record = [
                (MetricType.RESPONSE_TIME, response_time),
                (MetricType.TOKEN_USAGE, token_usage),
                (MetricType.COST, cost)
            ]

            if success:
                metrics_to_record.append((MetricType.SUCCESS_RATE, 1.0))
            else:
                metrics_to_record.append((MetricType.ERROR_RATE, 1.0))

            if quality_score is not None:
                metrics_to_record.append((MetricType.QUALITY_SCORE, quality_score))

            for metric_type, value in metrics_to_record:
                metric = PerformanceMetric(
                    model_name=model_name,
                    metric_type=metric_type,
                    value=value,
                    timestamp=timestamp,
                    unit=self._get_metric_unit(metric_type)
                )
                self.metrics_history[f"{model_name}_{metric_type.value}"].append(metric)
                self.current_metrics[model_name][metric_type.value] = value

                # Update Prometheus metrics
                self._update_prometheus_metric(model_name, metric_type, value)

            # Update request counters
            if f"{model_name}_requests_total" in self.prometheus_metrics:
                self.prometheus_metrics[f"{model_name}_requests_total"].inc()

            if not success and f"{model_name}_errors_total" in self.prometheus_metrics:
                self.prometheus_metrics[f"{model_name}_errors_total"].inc()

        except Exception as e:
            logger.error(f"Failed to record request: {e}")

    def get_metrics(self, model_name: str, metric_type: Optional[MetricType] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> List[PerformanceMetric]:
        """Get metrics for a model"""
        metrics = []

        if metric_type:
            key = f"{model_name}_{metric_type.value}"
            if key in self.metrics_history:
                metrics.extend(self.metrics_history[key])
        else:
            # Get all metrics for the model
            for key, metric_list in self.metrics_history.items():
                if key.startswith(f"{model_name}_"):
                    metrics.extend(metric_list)

        # Filter by time range
        if start_time or end_time:
            filtered_metrics = []
            for metric in metrics:
                if start_time and metric.timestamp < start_time:
                    continue
                if end_time and metric.timestamp > end_time:
                    continue
                filtered_metrics.append(metric)
            metrics = filtered_metrics

        return sorted(metrics, key=lambda x: x.timestamp)

    def get_current_metrics(self, model_name: Optional[str] = None) -> Dict[str, Dict[str, float]]:
        """Get current metrics for all models or a specific model"""
        if model_name:
            return {model_name: self.current_metrics.get(model_name, {})}
        return {k: v.copy() for k, v in self.current_metrics.items()}

    def get_health_status(self, model_name: Optional[str] = None) -> Dict[str, HealthCheck]:
        """Get health status for all models or a specific model"""
        if model_name:
            return {model_name: self.health_status.get(model_name)}
        return self.health_status.copy()

    def get_active_alerts(self, model_name: Optional[str] = None) -> List[Alert]:
        """Get active (unresolved) alerts"""
        alerts = [alert for alert in self.alerts.values() if not alert.resolved]

        if model_name:
            alerts = [alert for alert in alerts if alert.model_name == model_name]

        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].acknowledged = True
            logger.info(f"Alert {alert_id} acknowledged")
            return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved = True
            logger.info(f"Alert {alert_id} resolved")
            return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        uptime = datetime.now() - self.stats["uptime"]
        error_rate = (
            self.stats["total_errors"] / self.stats["total_requests"]
            if self.stats["total_requests"] > 0 else 0.0
        )

        return {
            "total_requests": self.stats["total_requests"],
            "total_errors": self.stats["total_errors"],
            "total_alerts": self.stats["total_alerts"],
            "error_rate": error_rate,
            "average_response_time": self.stats["average_response_time"],
            "uptime_hours": uptime.total_seconds() / 3600,
            "models_monitored": len(self.config.models),
            "active_alerts": len(self.get_active_alerts()),
            "monitoring_active": self.monitoring_active
        }

    async def generate_report(self, model_name: Optional[str] = None,
                            start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate monitoring report"""
        end_time = end_time or datetime.now()
        start_time = start_time or (end_time - timedelta(hours=24))

        report = {
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "models": {}
        }

        models_to_include = [model_name] if model_name else self.config.models

        for model in models_to_include:
            # Get metrics for the period
            metrics = self.get_metrics(model, start_time=start_time, end_time=end_time)

            # Calculate statistics
            response_times = [m.value for m in metrics if m.metric_type == MetricType.RESPONSE_TIME]
            success_rates = [m.value for m in metrics if m.metric_type == MetricType.SUCCESS_RATE]
            quality_scores = [m.value for m in metrics if m.metric_type == MetricType.QUALITY_SCORE]
            costs = [m.value for m in metrics if m.metric_type == MetricType.COST]

            model_report = {
                "total_requests": len([m for m in metrics if m.metric_type == MetricType.RESPONSE_TIME]),
                "average_response_time": np.mean(response_times) if response_times else 0.0,
                "p95_response_time": np.percentile(response_times, 95) if response_times else 0.0,
                "average_success_rate": np.mean(success_rates) if success_rates else 1.0,
                "average_quality_score": np.mean(quality_scores) if quality_scores else 0.0,
                "total_cost": sum(costs) if costs else 0.0,
                "alerts": len([a for a in self.alert_history if a.model_name == model and start_time <= a.timestamp <= end_time])
            }

            report["models"][model] = model_report

        # Add system statistics
        report["system"] = self.get_statistics()

        return report

    async def export_metrics(self, format: str = "json", output_path: Optional[str] = None) -> Union[str, Dict]:
        """Export metrics data"""
        if format == "json":
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "current_metrics": self.get_current_metrics(),
                "health_status": {k: asdict(v) for k, v in self.health_status.items()},
                "active_alerts": [asdict(a) for a in self.get_active_alerts()],
                "statistics": self.get_statistics()
            }

            json_data = json.dumps(export_data, indent=2, default=str)

            if output_path:
                with open(output_path, 'w') as f:
                    f.write(json_data)
                logger.info(f"Metrics exported to {output_path}")

            return json_data

        elif format == "prometheus":
            # Return Prometheus metrics endpoint URL
            return f"http://localhost:{self.config.metrics_port}/metrics"

        else:
            raise ValueError(f"Unsupported export format: {format}")

    async def cleanup_old_data(self, retention_days: Optional[int] = None):
        """Clean up old monitoring data"""
        retention_days = retention_days or self.config.log_retention_days
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        # Clean up old metrics
        for key in list(self.metrics_history.keys()):
            metric_list = self.metrics_history[key]
            original_length = len(metric_list)

            # Filter old metrics
            filtered_metrics = deque(
                (m for m in metric_list if m.timestamp >= cutoff_date),
                maxlen=metric_list.maxlen
            )
            self.metrics_history[key] = filtered_metrics

            cleaned_count = original_length - len(filtered_metrics)
            if cleaned_count > 0:
                logger.debug(f"Cleaned {cleaned_count} old metrics for {key}")

        # Clean up old alerts
        original_alerts = len(self.alert_history)
        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_date
        ]
        cleaned_alerts = original_alerts - len(self.alert_history)

        if cleaned_alerts > 0:
            logger.info(f"Cleaned {cleaned_alerts} old alerts")

    async def shutdown(self):
        """Shutdown the monitoring service"""
        await self.stop_monitoring()
        self.executor.shutdown(wait=True)
        logger.info("ModelMonitor shutdown complete")

# Example usage
async def demonstrate_monitoring():
    """Demonstrate monitoring functionality"""
    config = MonitoringConfig(
        models=["gpt-4", "claude-3"],
        monitoring_interval=5.0,  # 5 seconds for demo
        alert_thresholds={
            "gpt-4": {
                "response_time": 1.0,
                "success_rate": 0.95,
                "quality_score": 0.8
            },
            "claude-3": {
                "response_time": 0.8,
                "success_rate": 0.97,
                "quality_score": 0.85
            }
        },
        enable_alerts=True,
        enable_metrics_export=True
    )

    monitor = ModelMonitor(config)
    await monitor.start_monitoring()

    # Simulate some requests
    for i in range(10):
        await monitor.record_request(
            model_name="gpt-4",
            response_time=np.random.normal(0.6, 0.1),
            success=np.random.random() > 0.1,
            token_usage=np.random.normal(100, 20),
            cost=np.random.normal(0.01, 0.002),
            quality_score=np.random.uniform(0.7, 0.95)
        )
        await asyncio.sleep(1)

    # Get statistics
    stats = monitor.get_statistics()
    print(f"Monitoring Statistics: {stats}")

    # Get health status
    health = monitor.get_health_status()
    print(f"Health Status: {health}")

    # Generate report
    report = await monitor.generate_report()
    print(f"Report generated with {len(report['models'])} models")

    await monitor.stop_monitoring()
    await monitor.shutdown()

if __name__ == "__main__":
    asyncio.run(demonstrate_monitoring())