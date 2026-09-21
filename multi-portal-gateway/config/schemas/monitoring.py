"""
Monitoring configuration schemas for DMLogn8n multi-agent platform.
"""

from typing import Dict, List, Optional, Union, Any, Literal
from pydantic import BaseModel, Field, validator, RootModel
from enum import Enum
import secrets


class MetricType(str, Enum):
    """Types of metrics to collect."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class LogLevel(str, Enum):
    """Log levels."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"
    TRACE = "trace"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class MonitoringBackend(str, Enum):
    """Monitoring backends."""
    PROMETHEUS = "prometheus"
    DATADOG = "datadog"
    NEW_RELIC = "new_relic"
    GRAFANA = "grafana"
    CLOUDWATCH = "cloudwatch"
    STACKDRIVER = "stackdriver"
    CUSTOM = "custom"


class LogFormat(str, Enum):
    """Log formats."""
    JSON = "json"
    PLAIN_TEXT = "plain_text"
    STRUCTURED = "structured"
    ELASTIC = "elastic"


class MetricDefinition(BaseModel):
    """Metric definition configuration."""
    name: str = Field(..., description="Metric name")
    type: MetricType = Field(..., description="Metric type")
    description: str = Field(..., description="Metric description")
    labels: Dict[str, str] = Field(default_factory=dict, description="Metric labels")
    unit: Optional[str] = Field(default=None, description="Metric unit")
    buckets: Optional[List[float]] = Field(default=None, description="Histogram buckets")
    quantiles: Optional[List[float]] = Field(default=None, description="Summary quantiles")
    enabled: bool = Field(default=True, description="Whether this metric is enabled")
    collection_interval: int = Field(default=60, ge=1, description="Collection interval in seconds")

    @validator('name')
    def validate_name(cls, v):
        """Validate metric name."""
        if not v or not v.strip():
            raise ValueError("Metric name cannot be empty")
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Metric name must contain only alphanumeric characters, underscores, and hyphens")
        return v.strip()

    @validator('buckets')
    def validate_buckets(cls, v):
        """Validate histogram buckets are sorted."""
        if v and sorted(v) != v:
            raise ValueError("Histogram buckets must be in ascending order")
        return v

    @validator('quantiles')
    def validate_quantiles(cls, v):
        """Validate summary quantiles are between 0 and 1."""
        if v and any(q <= 0 or q >= 1 for q in v):
            raise ValueError("Quantiles must be between 0 and 1")
        return v


class PrometheusConfig(BaseModel):
    """Prometheus monitoring configuration."""
    port: int = Field(default=9090, ge=1, le=65535, description="Prometheus server port")
    metrics_path: str = Field(default="/metrics", description="Metrics endpoint path")
    push_gateway: Optional[str] = Field(default=None, description="Push gateway URL")
    push_interval: int = Field(default=60, ge=1, description="Push interval in seconds")
    job_name: str = Field(default="dmlogn8n", description="Prometheus job name")
    instance_name: Optional[str] = Field(default=None, description="Instance name")
    custom_metrics: Dict[str, MetricDefinition] = Field(default_factory=dict, description="Custom metrics")

    @validator('push_gateway')
    def validate_push_gateway_url(cls, v):
        """Validate push gateway URL format."""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError("Push gateway URL must start with http:// or https://")
        return v


class DatadogConfig(BaseModel):
    """Datadog monitoring configuration."""
    api_key: str = Field(..., description="Datadog API key")
    app_key: Optional[str] = Field(default=None, description="Datadog application key")
    site: str = Field(default="datadoghq.com", description="Datadog site")
    hostname: Optional[str] = Field(default=None, description="Hostname to report")
    tags: List[str] = Field(default_factory=list, description="Global tags")
    metrics_batch_size: int = Field(default=100, ge=1, description="Metrics batch size")
    metrics_flush_interval: int = Field(default=15, ge=1, description="Metrics flush interval in seconds")
    enable_distribution_metrics: bool = Field(default=True, description="Enable distribution metrics")
    histogram_percentiles: List[float] = Field(
        default=[0.5, 0.75, 0.9, 0.95, 0.99],
        description="Histogram percentiles"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: LogLevel = Field(default=LogLevel.INFO, description="Default log level")
    format: LogFormat = Field(default=LogFormat.JSON, description="Log format")
    file_path: Optional[str] = Field(default=None, description="Log file path")
    max_file_size: str = Field(default="100MB", description="Maximum log file size")
    max_files: int = Field(default=10, ge=1, description="Maximum number of log files")
    compression: str = Field(default="gzip", description="Log compression format")
    console_output: bool = Field(default=True, description="Enable console output")
    structured_logging: bool = Field(default=True, description="Enable structured logging")
    include_timestamps: bool = Field(default=True, description="Include timestamps in logs")
    include_hostname: bool = Field(default=False, description="Include hostname in logs")
    include_process_id: bool = Field(default=False, description="Include process ID in logs")

    # Logger-specific configurations
    loggers: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Logger-specific settings")
    handlers: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Log handlers")
    formatters: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Log formatters")

    # Advanced settings
    async_logging: bool = Field(default=False, description="Enable async logging")
    buffer_size: int = Field(default=1024, ge=1, description="Async log buffer size")
    flush_interval: int = Field(default=5, ge=1, description="Flush interval in seconds")

    @validator('max_file_size')
    def validate_file_size(cls, v):
        """Validate file size format."""
        import re
        pattern = r'^\d+[KMGT]?B?$'
        if not re.match(pattern, v.upper()):
            raise ValueError("File size must be in format like '100MB', '1GB', etc.")
        return v.upper()


class HealthCheck(BaseModel):
    """Health check configuration."""
    enabled: bool = Field(default=True, description="Enable health checks")
    port: int = Field(default=8080, ge=1, le=65535, description="Health check server port")
    path: str = Field(default="/health", description="Health check endpoint path")
    check_interval: int = Field(default=30, ge=1, description="Check interval in seconds")
    timeout: int = Field(default=5, ge=1, description="Health check timeout in seconds")
    failure_threshold: int = Field(default=3, ge=1, description="Failure threshold before marking unhealthy")
    success_threshold: int = Field(default=2, ge=1, description="Success threshold for recovery")

    # Component checks
    checks: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Component health checks")
    dependencies: List[str] = Field(default_factory=list, description="Required dependencies")

    @validator('checks')
    def validate_checks(cls, v):
        """Validate health check configurations."""
        for name, check in v.items():
            if 'type' not in check:
                raise ValueError(f"Health check '{name}' must specify a type")
            if 'endpoint' not in check and 'command' not in check:
                raise ValueError(f"Health check '{name}' must specify either endpoint or command")
        return v


class AlertRule(BaseModel):
    """Alert rule configuration."""
    name: str = Field(..., description="Alert rule name")
    description: str = Field(..., description="Alert description")
    condition: str = Field(..., description="Alert condition (PromQL or equivalent)")
    severity: AlertSeverity = Field(default=AlertSeverity.MEDIUM, description="Alert severity")
    for_duration: str = Field(default="5m", description="Alert duration before firing")
    labels: Dict[str, str] = Field(default_factory=dict, description="Alert labels")
    annotations: Dict[str, str] = Field(default_factory=dict, description="Alert annotations")
    enabled: bool = Field(default=True, description="Whether this alert rule is enabled")

    # Notification settings
    notifications: List[str] = Field(default_factory=list, description="Notification channels")
    cooldown: str = Field(default="1h", description="Alert cooldown period")

    @validator('for_duration', 'cooldown')
    def validate_duration(cls, v):
        """Validate duration format."""
        import re
        pattern = r'^\d+[smhd]$'
        if not re.match(pattern, v.lower()):
            raise ValueError("Duration must be in format like '5m', '1h', '1d'")
        return v.lower()


class NotificationChannel(BaseModel):
    """Notification channel configuration."""
    name: str = Field(..., description="Channel name")
    type: Literal["email", "slack", "webhook", "pagerduty", "sms", "discord", "teams"] = Field(
        ..., description="Channel type"
    )
    enabled: bool = Field(default=True, description="Whether this channel is enabled")

    # Channel-specific settings
    settings: Dict[str, Any] = Field(default_factory=dict, description="Channel-specific settings")

    # Rate limiting
    rate_limit: Optional[Dict[str, Any]] = Field(default=None, description="Rate limiting settings")

    @validator('name')
    def validate_name(cls, v):
        """Validate channel name."""
        if not v or not v.strip():
            raise ValueError("Channel name cannot be empty")
        return v.strip()


class MonitoringConfig(BaseModel):
    """Main monitoring configuration."""
    enabled: bool = Field(default=True, description="Enable monitoring")
    backend: MonitoringBackend = Field(default=MonitoringBackend.PROMETHEUS, description="Monitoring backend")
    namespace: str = Field(default="dmlogn8n", description="Metrics namespace")
    service_name: str = Field(default="dmlogn8n", description="Service name")
    version: str = Field(default="1.0.0", description="Service version")
    environment: str = Field(default="development", description="Environment name")

    # Backend-specific configurations
    prometheus: Optional[PrometheusConfig] = Field(default=None, description="Prometheus configuration")
    datadog: Optional[DatadogConfig] = Field(default=None, description="Datadog configuration")

    # Core components
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging configuration")
    health_check: HealthCheck = Field(default_factory=HealthCheck, description="Health check configuration")

    # Metrics and alerts
    metrics: Dict[str, MetricDefinition] = Field(default_factory=dict, description="Custom metrics")
    alert_rules: Dict[str, AlertRule] = Field(default_factory=dict, description="Alert rules")
    notification_channels: Dict[str, NotificationChannel] = Field(
        default_factory=dict, description="Notification channels"
    )

    # Advanced settings
    sample_rate: float = Field(default=1.0, ge=0.0, le=1.0, description="Metrics sampling rate")
    retention_period: str = Field(default="7d", description="Metrics retention period")
    batch_size: int = Field(default=100, ge=1, description="Metrics batch size")
    flush_interval: int = Field(default=15, ge=1, description="Metrics flush interval in seconds")

    # Performance monitoring
    performance_monitoring: bool = Field(default=True, description="Enable performance monitoring")
    trace_collection: bool = Field(default=True, description="Enable trace collection")
    error_tracking: bool = Field(default=True, description="Enable error tracking")

    @validator('retention_period')
    def validate_retention_period(cls, v):
        """Validate retention period format."""
        import re
        pattern = r'^\d+[smhdw]$'
        if not re.match(pattern, v.lower()):
            raise ValueError("Retention period must be in format like '7d', '1w', '24h'")
        return v.lower()

    def get_backend_config(self) -> Union[PrometheusConfig, DatadogConfig]:
        """Get backend-specific configuration."""
        if self.backend == MonitoringBackend.PROMETHEUS:
            return self.prometheus or PrometheusConfig()
        elif self.backend == MonitoringBackend.DATADOG:
            if not self.datadog:
                raise ValueError("Datadog configuration required when using Datadog backend")
            return self.datadog
        else:
            raise ValueError(f"Unsupported monitoring backend: {self.backend}")


class SystemMonitoring(BaseModel):
    """System-level monitoring configuration."""
    cpu_monitoring: bool = Field(default=True, description="Monitor CPU usage")
    memory_monitoring: bool = Field(default=True, description="Monitor memory usage")
    disk_monitoring: bool = Field(default=True, description="Monitor disk usage")
    network_monitoring: bool = Field(default=True, description="Monitor network usage")
    process_monitoring: bool = Field(default=True, description="Monitor process metrics")

    # Thresholds
    cpu_threshold: float = Field(default=80.0, ge=0.0, le=100.0, description="CPU usage warning threshold (%)")
    memory_threshold: float = Field(default=80.0, ge=0.0, le=100.0, description="Memory usage warning threshold (%)")
    disk_threshold: float = Field(default=85.0, ge=0.0, le=100.0, description="Disk usage warning threshold (%)")

    # Collection intervals
    system_metrics_interval: int = Field(default=60, ge=1, description="System metrics collection interval (seconds)")
    process_metrics_interval: int = Field(default=30, ge=1, description="Process metrics collection interval (seconds)")

    # Specific processes to monitor
    monitored_processes: List[str] = Field(default_factory=list, description="Specific processes to monitor")
    exclude_processes: List[str] = Field(default_factory=list, description="Processes to exclude from monitoring")


# Predefined monitoring configurations
class MonitoringPresets:
    """Predefined monitoring configurations."""

    @staticmethod
    def development() -> MonitoringConfig:
        """Development environment monitoring configuration."""
        return MonitoringConfig(
            backend=MonitoringBackend.PROMETHEUS,
            environment="development",
            prometheus=PrometheusConfig(port=9090),
            logging=LoggingConfig(
                level=LogLevel.DEBUG,
                format=LogFormat.PLAIN_TEXT,
                console_output=True
            ),
            health_check=HealthCheck(
                port=8080,
                check_interval=30
            ),
            sample_rate=0.1,
            performance_monitoring=True,
            trace_collection=False
        )

    @staticmethod
    def production() -> MonitoringConfig:
        """Production environment monitoring configuration."""
        return MonitoringConfig(
            backend=MonitoringBackend.PROMETHEUS,
            environment="production",
            prometheus=PrometheusConfig(
                port=9090,
                job_name="dmlogn8n_production"
            ),
            logging=LoggingConfig(
                level=LogLevel.INFO,
                format=LogFormat.JSON,
                file_path="/var/log/dmlogn8n/app.log",
                max_file_size="1GB",
                max_files=30,
                compression="gzip",
                console_output=False,
                async_logging=True
            ),
            health_check=HealthCheck(
                port=8080,
                check_interval=15,
                failure_threshold=2
            ),
            sample_rate=1.0,
            retention_period="30d",
            performance_monitoring=True,
            trace_collection=True,
            error_tracking=True
        )

    @staticmethod
    def high_security() -> MonitoringConfig:
        """High-security environment monitoring configuration."""
        return MonitoringConfig(
            backend=MonitoringBackend.DATADOG,
            environment="production",
            datadog=DatadogConfig(
                api_key="${DATADOG_API_KEY}",
                app_key="${DATADOG_APP_KEY}",
                site="datadoghq.com",
                tags=["environment:production", "security:high"]
            ),
            logging=LoggingConfig(
                level=LogLevel.WARNING,
                format=LogFormat.JSON,
                file_path="/var/log/dmlogn8n/secure.log",
                max_file_size="500MB",
                max_files=90,
                compression="gzip",
                console_output=False,
                async_logging=True,
                structured_logging=True
            ),
            health_check=HealthCheck(
                port=8080,
                check_interval=10,
                failure_threshold=1,
                timeout=3
            ),
            sample_rate=1.0,
            retention_period="90d",
            performance_monitoring=True,
            trace_collection=True,
            error_tracking=True
        )