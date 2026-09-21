"""
Configuration Management for Error Handling System

Provides centralized configuration management for all error handling components.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import json
import os

from .circuit_breaker import CircuitBreakerConfig
from .retry_handler import RetryConfig, BackoffStrategy
from .monitoring import AlertLevel


@dataclass
class CircuitBreakerSettings:
    """Global circuit breaker settings."""
    default_failure_threshold: int = 5
    default_recovery_timeout: float = 60.0
    default_success_threshold: int = 3
    default_timeout: float = 10.0
    default_max_concurrent_calls: int = 100
    auto_reset_enabled: bool = True
    auto_reset_interval: float = 300.0  # 5 minutes


@dataclass
class RetrySettings:
    """Global retry settings."""
    default_max_attempts: int = 3
    default_base_delay: float = 1.0
    default_max_delay: float = 60.0
    default_backoff_strategy: str = BackoffStrategy.EXPONENTIAL.value
    default_jitter: bool = True
    default_backoff_multiplier: float = 2.0


@dataclass
class MonitoringSettings:
    """Global monitoring settings."""
    enabled: bool = True
    metrics_retention_hours: int = 24
    alert_evaluation_interval: float = 60.0
    dashboard_refresh_interval: float = 30.0
    max_metrics_history: int = 10000
    max_alerts_history: int = 1000


@dataclass
class NotificationSettings:
    """Notification settings."""
    enabled: bool = True
    default_channels: List[str] = field(default_factory=list)
    rate_limit_minutes: int = 5
    max_alerts_per_minute: int = 10
    quiet_hours: Optional[Dict[str, int]] = None  # {"start": 22, "end": 7}


@dataclass
class RecoverySettings:
    """Recovery settings."""
    enabled: bool = True
    auto_recovery_enabled: bool = True
    recovery_timeout: float = 300.0  # 5 minutes
    max_recovery_attempts: int = 3
    recovery_cooldown: float = 600.0  # 10 minutes


@dataclass
class LoggingSettings:
    """Logging settings."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size_mb: int = 100
    backup_count: int = 5
    include_traceback: bool = False


@dataclass
class ErrorHandlingConfig:
    """Main error handling configuration."""
    circuit_breaker: CircuitBreakerSettings = field(default_factory=CircuitBreakerSettings)
    retry: RetrySettings = field(default_factory=RetrySettings)
    monitoring: MonitoringSettings = field(default_factory=MonitoringSettings)
    notifications: NotificationSettings = field(default_factory=NotificationSettings)
    recovery: RecoverySettings = field(default_factory=RecoverySettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)

    # Component-specific configurations
    component_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Environment-specific settings
    environment: str = "development"
    debug: bool = False


class ConfigManager:
    """Manages error handling configuration."""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self._config: Optional[ErrorHandlingConfig] = None

    def load_config(self) -> ErrorHandlingConfig:
        """Load configuration from file or environment."""
        if self._config:
            return self._config

        # Try to load from file
        if self.config_file and os.path.exists(self.config_file):
            self._config = self._load_from_file(self.config_file)
        else:
            # Load from environment variables and defaults
            self._config = self._load_from_environment()

        return self._config

    def _load_from_file(self, file_path: str) -> ErrorHandlingConfig:
        """Load configuration from JSON file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Parse configuration data
            circuit_breaker_data = data.get('circuit_breaker', {})
            retry_data = data.get('retry', {})
            monitoring_data = data.get('monitoring', {})
            notifications_data = data.get('notifications', {})
            recovery_data = data.get('recovery', {})
            logging_data = data.get('logging', {})

            return ErrorHandlingConfig(
                circuit_breaker=CircuitBreakerSettings(**circuit_breaker_data),
                retry=RetrySettings(**retry_data),
                monitoring=MonitoringSettings(**monitoring_data),
                notifications=NotificationSettings(**notifications_data),
                recovery=RecoverySettings(**recovery_data),
                logging=LoggingSettings(**logging_data),
                environment=data.get('environment', 'development'),
                debug=data.get('debug', False),
                component_configs=data.get('component_configs', {})
            )

        except Exception as e:
            raise ValueError(f"Failed to load configuration from {file_path}: {e}")

    def _load_from_environment(self) -> ErrorHandlingConfig:
        """Load configuration from environment variables."""
        return ErrorHandlingConfig(
            circuit_breaker=CircuitBreakerSettings(
                default_failure_threshold=int(os.getenv('ERROR_CB_FAILURE_THRESHOLD', 5)),
                default_recovery_timeout=float(os.getenv('ERROR_CB_RECOVERY_TIMEOUT', 60.0)),
                default_success_threshold=int(os.getenv('ERROR_CB_SUCCESS_THRESHOLD', 3)),
                default_timeout=float(os.getenv('ERROR_CB_TIMEOUT', 10.0)),
                auto_reset_enabled=os.getenv('ERROR_CB_AUTO_RESET', 'true').lower() == 'true',
                auto_reset_interval=float(os.getenv('ERROR_CB_RESET_INTERVAL', 300.0))
            ),
            retry=RetrySettings(
                default_max_attempts=int(os.getenv('ERROR_RETRY_MAX_ATTEMPTS', 3)),
                default_base_delay=float(os.getenv('ERROR_RETRY_BASE_DELAY', 1.0)),
                default_max_delay=float(os.getenv('ERROR_RETRY_MAX_DELAY', 60.0)),
                default_backoff_strategy=os.getenv('ERROR_RETRY_BACKOFF_STRATEGY', 'exponential'),
                default_jitter=os.getenv('ERROR_RETRY_JITTER', 'true').lower() == 'true',
                default_backoff_multiplier=float(os.getenv('ERROR_RETRY_MULTIPLIER', 2.0))
            ),
            monitoring=MonitoringSettings(
                enabled=os.getenv('ERROR_MONITORING_ENABLED', 'true').lower() == 'true',
                metrics_retention_hours=int(os.getenv('ERROR_METRICS_RETENTION_HOURS', 24)),
                alert_evaluation_interval=float(os.getenv('ERROR_ALERT_INTERVAL', 60.0)),
                dashboard_refresh_interval=float(os.getenv('ERROR_DASHBOARD_INTERVAL', 30.0))
            ),
            notifications=NotificationSettings(
                enabled=os.getenv('ERROR_NOTIFICATIONS_ENABLED', 'true').lower() == 'true',
                rate_limit_minutes=int(os.getenv('ERROR_RATE_LIMIT_MINUTES', 5)),
                max_alerts_per_minute=int(os.getenv('ERROR_MAX_ALERTS_PER_MINUTE', 10))
            ),
            recovery=RecoverySettings(
                enabled=os.getenv('ERROR_RECOVERY_ENABLED', 'true').lower() == 'true',
                auto_recovery_enabled=os.getenv('ERROR_AUTO_RECOVERY_ENABLED', 'true').lower() == 'true',
                recovery_timeout=float(os.getenv('ERROR_RECOVERY_TIMEOUT', 300.0)),
                max_recovery_attempts=int(os.getenv('ERROR_MAX_RECOVERY_ATTEMPTS', 3)),
                recovery_cooldown=float(os.getenv('ERROR_RECOVERY_COOLDOWN', 600.0))
            ),
            logging=LoggingSettings(
                level=os.getenv('ERROR_LOG_LEVEL', 'INFO'),
                include_traceback=os.getenv('ERROR_LOG_TRACEBACK', 'false').lower() == 'true'
            ),
            environment=os.getenv('ERROR_ENVIRONMENT', 'development'),
            debug=os.getenv('ERROR_DEBUG', 'false').lower() == 'true'
        )

    def save_config(self, config: ErrorHandlingConfig, file_path: Optional[str] = None) -> None:
        """Save configuration to file."""
        target_file = file_path or self.config_file
        if not target_file:
            raise ValueError("No file path specified for saving configuration")

        # Convert to dict
        config_dict = {
            'circuit_breaker': config.circuit_breaker.__dict__,
            'retry': config.retry.__dict__,
            'monitoring': config.monitoring.__dict__,
            'notifications': config.notifications.__dict__,
            'recovery': config.recovery.__dict__,
            'logging': config.logging.__dict__,
            'environment': config.environment,
            'debug': config.debug,
            'component_configs': config.component_configs
        }

        try:
            with open(target_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
        except Exception as e:
            raise ValueError(f"Failed to save configuration to {target_file}: {e}")

    def get_component_config(self, component_name: str) -> Dict[str, Any]:
        """Get configuration for a specific component."""
        config = self.load_config()
        return config.component_configs.get(component_name, {})

    def update_component_config(self, component_name: str, updates: Dict[str, Any]) -> None:
        """Update configuration for a specific component."""
        config = self.load_config()
        if component_name not in config.component_configs:
            config.component_configs[component_name] = {}
        config.component_configs[component_name].update(updates)


# Global config manager instance
config_manager = ConfigManager()