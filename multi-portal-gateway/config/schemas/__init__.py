"""
Configuration schemas for DMLogn8n multi-agent platform.

This module contains Pydantic-based schemas for validating and structuring
configuration data across different components of the system.
"""

from .database import (
    DatabaseConfig,
    MultiDatabaseConfig,
    DatabaseType,
    SSLMode,
    DatabaseCredentials,
    SSLConfig,
    ConnectionPool,
    RetryConfig,
    DatabaseCluster,
    DatabasePresets
)

from .ai_models import (
    ModelConfig,
    MultiModelConfig,
    ModelProvider,
    ModelType,
    ModelCapability,
    ModelCredentials,
    ModelParameters,
    RateLimiting,
    CachingConfig,
    ModelPool,
    ModelPresets
)

from .monitoring import (
    MonitoringConfig,
    MetricType,
    LogLevel,
    AlertSeverity,
    MonitoringBackend,
    LogFormat,
    MetricDefinition,
    PrometheusConfig,
    DatadogConfig,
    LoggingConfig,
    HealthCheck,
    AlertRule,
    NotificationChannel,
    SystemMonitoring,
    MonitoringPresets
)

__all__ = [
    # Database schemas
    'DatabaseConfig',
    'MultiDatabaseConfig',
    'DatabaseType',
    'SSLMode',
    'DatabaseCredentials',
    'SSLConfig',
    'ConnectionPool',
    'RetryConfig',
    'DatabaseCluster',
    'DatabasePresets',

    # AI Model schemas
    'ModelConfig',
    'MultiModelConfig',
    'ModelProvider',
    'ModelType',
    'ModelCapability',
    'ModelCredentials',
    'ModelParameters',
    'RateLimiting',
    'CachingConfig',
    'ModelPool',
    'ModelPresets',

    # Monitoring schemas
    'MonitoringConfig',
    'MetricType',
    'LogLevel',
    'AlertSeverity',
    'MonitoringBackend',
    'LogFormat',
    'MetricDefinition',
    'PrometheusConfig',
    'DatadogConfig',
    'LoggingConfig',
    'HealthCheck',
    'AlertRule',
    'NotificationChannel',
    'SystemMonitoring',
    'MonitoringPresets'
]