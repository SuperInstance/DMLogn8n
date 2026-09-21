"""
Configuration Management System for DMLogn8n Multi-Agent Platform

This package provides comprehensive configuration management capabilities including:
- Environment-specific configurations
- Dynamic configuration updates
- Configuration validation
- Secret management integration
- Configuration versioning and rollback
- Multi-service configuration coordination

Main Components:
- config_manager: Central configuration management service
- validator: Configuration validation framework
- watcher: File watcher for dynamic updates
- schemas: Pydantic-based configuration schemas
- environments: Environment-specific configuration files
- utils: Utility functions including secret management

Usage:
    from config import config_manager, config_watcher

    # Get configuration
    db_config = config_manager.get_database_config()
    model_config = config_manager.get_model_config("gpt4")

    # Watch for changes
    config_watcher.start()

    # Validate configuration
    results = config_manager.validate_configuration()
"""

from .config_manager import (
    ConfigManager,
    ConfigurationError,
    ConfigChangeEvent,
    ConfigVersion,
    ConfigMetadata,
    config_manager
)

from .validator import (
    ConfigValidator,
    ValidationResult,
    ValidationError
)

from .watcher import (
    ConfigFileWatcher,
    ConfigWatcherEvent,
    WatcherEventType,
    config_watcher,
    start_config_watcher,
    stop_config_watcher,
    add_config_watch_callback
)

# Import schemas
from .schemas.database import (
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

from .schemas.ai_models import (
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

from .schemas.monitoring import (
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

from .utils import (
    SecretManager,
    SecretBackend,
    EnvironmentVariableBackend,
    FileBackend,
    HashiCorpVaultBackend,
    AWSSecretsManagerBackend,
    SecretMetadata,
    secret_manager,
    get_secret,
    get_secrets,
    set_secret
)

# Version information
__version__ = "1.0.0"
__author__ = "DMLogn8n Team"
__description__ = "Configuration Management System for DMLogn8n Multi-Agent Platform"

# Convenience functions for common operations
def get_config(config_type: str, key: str = None, default=None):
    """Get configuration value."""
    return config_manager.get_config(config_type, key, default)


def get_database_config(name: str = None):
    """Get database configuration."""
    return config_manager.get_database_config(name)


def get_model_config(name: str):
    """Get AI model configuration."""
    return config_manager.get_model_config(name)


def get_monitoring_config():
    """Get monitoring configuration."""
    return config_manager.get_monitoring_config()


def set_config(config_type: str, key: str, value: Any, source: str = "manual"):
    """Set configuration value."""
    return config_manager.set_config(config_type, key, value, source)


def reload_configuration():
    """Reload configuration from files."""
    return config_manager.reload_configuration()


def validate_configuration():
    """Validate current configuration."""
    return config_manager.validate_configuration()


def start_config_watcher():
    """Start configuration file watcher."""
    return config_watcher.start()


def stop_config_watcher():
    """Stop configuration file watcher."""
    return config_watcher.stop()


def get_environment() -> str:
    """Get current environment."""
    return config_manager.get_environment()


# Export all public components
__all__ = [
    # Core classes
    'ConfigManager',
    'ConfigValidator',
    'ConfigFileWatcher',
    'SecretManager',

    # Global instances
    'config_manager',
    'config_watcher',
    'secret_manager',

    # Event and version classes
    'ConfigurationError',
    'ConfigChangeEvent',
    'ConfigVersion',
    'ConfigMetadata',
    'ValidationResult',
    'ValidationError',
    'ConfigWatcherEvent',
    'WatcherEventType',
    'SecretMetadata',

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
    'MonitoringPresets',

    # Secret management
    'SecretBackend',
    'EnvironmentVariableBackend',
    'FileBackend',
    'HashiCorpVaultBackend',
    'AWSSecretsManagerBackend',

    # Convenience functions
    'get_config',
    'get_database_config',
    'get_model_config',
    'get_monitoring_config',
    'set_config',
    'reload_configuration',
    'validate_configuration',
    'start_config_watcher',
    'stop_config_watcher',
    'get_environment',
    'get_secret',
    'get_secrets',
    'set_secret',

    # Package metadata
    '__version__',
    '__author__',
    '__description__'
]