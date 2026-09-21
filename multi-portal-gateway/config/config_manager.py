"""
Main configuration management service for DMLogn8n multi-agent platform.
"""

import os
import json
import yaml
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime, timezone
from copy import deepcopy
from contextlib import contextmanager
import hashlib
import weakref

from .validator import ConfigValidator, ValidationResult
from .schemas.database import MultiDatabaseConfig, DatabaseConfig
from .schemas.ai_models import MultiModelConfig, ModelConfig
from .schemas.monitoring import MonitoringConfig


# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class ConfigVersion:
    """Configuration version information."""
    version: str
    timestamp: datetime
    checksum: str
    author: Optional[str] = None
    description: Optional[str] = None
    environment: str = "unknown"


@dataclass
class ConfigChangeEvent:
    """Configuration change event."""
    config_type: str
    old_value: Any
    new_value: Any
    timestamp: datetime
    source: str
    version: str


@dataclass
class ConfigMetadata:
    """Configuration metadata."""
    loaded_at: datetime
    source_file: Optional[Path] = None
    environment_variables: List[str] = field(default_factory=list)
    secrets: List[str] = field(default_factory=list)
    checksum: str = ""


class ConfigurationError(Exception):
    """Configuration-related errors."""
    pass


class ConfigManager:
    """Main configuration management service."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the configuration manager."""
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.logger = logging.getLogger(__name__)

        # Configuration storage
        self._configs: Dict[str, Any] = {}
        self._metadata: Dict[str, ConfigMetadata] = {}
        self._versions: List[ConfigVersion] = []
        self._change_listeners: Dict[str, List[Callable]] = {}
        self._validators: Dict[str, ConfigValidator] = {}

        # Threading
        self._config_lock = threading.RLock()
        self._change_listeners_lock = threading.Lock()

        # Paths
        self._config_dir = Path(__file__).parent
        self._environments_dir = self._config_dir / "environments"
        self._schemas_dir = self._config_dir / "schemas"

        # Initialize validator
        self._validator = ConfigValidator()

        # Settings
        self._auto_reload = os.getenv("CONFIG_AUTO_RELOAD", "true").lower() == "true"
        self._validate_on_load = os.getenv("CONFIG_VALIDATE_ON_LOAD", "true").lower() == "true"
        self._environment = os.getenv("ENVIRONMENT", "development")

        # Load initial configuration
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load initial configuration."""
        try:
            self.logger.info(f"Loading configuration for environment: {self._environment}")

            # Load environment-specific configuration
            config_file = self._environments_dir / f"{self._environment}.yaml"
            if config_file.exists():
                self._load_config_file(config_file)
            else:
                self.logger.warning(f"Environment config not found: {config_file}, using defaults")
                self._load_defaults()

            # Load override configuration if present
            override_file = self._config_dir.parent / "config_override.yaml"
            if override_file.exists():
                self.logger.info("Loading configuration overrides")
                self._load_config_file(override_file, override=True)

            # Load environment variable overrides
            self._load_environment_overrides()

            # Validate configuration if enabled
            if self._validate_on_load:
                self._validate_all_configs()

            self.logger.info("Configuration loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {str(e)}")
            raise ConfigurationError(f"Configuration loading failed: {str(e)}")

    def _load_config_file(self, file_path: Path, override: bool = False) -> None:
        """Load configuration from a file."""
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    config_data = json.load(f)
                else:
                    raise ValueError(f"Unsupported file format: {file_path.suffix}")

            if config_data is None:
                config_data = {}

            # Process environment variables in the config
            processed_data = self._process_environment_variables(config_data)

            # Store configuration
            with self._config_lock:
                if override:
                    self._deep_merge(self._configs, processed_data)
                else:
                    self._configs.update(processed_data)

                # Update metadata
                checksum = self._calculate_checksum(processed_data)
                for config_type in processed_data:
                    metadata = ConfigMetadata(
                        loaded_at=datetime.now(timezone.utc),
                        source_file=file_path,
                        environment_variables=self._find_env_variables(processed_data[config_type]),
                        secrets=self._find_secrets(processed_data[config_type]),
                        checksum=checksum
                    )
                    self._metadata[config_type] = metadata

                # Add version
                version = ConfigVersion(
                    version=f"v{len(self._versions) + 1}",
                    timestamp=datetime.now(timezone.utc),
                    checksum=checksum,
                    environment=self._environment,
                    description=f"Loaded from {file_path.name}"
                )
                self._versions.append(version)

            self.logger.debug(f"Loaded configuration from {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to load config file {file_path}: {str(e)}")
            raise ConfigurationError(f"Failed to load config file {file_path}: {str(e)}")

    def _load_defaults(self) -> None:
        """Load default configuration."""
        default_config = {
            "database": {
                "databases": {
                    "default": {
                        "name": "default",
                        "type": "sqlite",
                        "credentials": {
                            "username": "",
                            "password": "",
                            "host": "",
                            "port": 0,
                            "database": "./data/dmlogn8n.db"
                        },
                        "enabled": True
                    }
                },
                "default_database": "default"
            },
            "ai_models": {
                "models": {},
                "pools": {},
                "default_models": {},
                "global_settings": {}
            },
            "monitoring": {
                "enabled": True,
                "backend": "prometheus",
                "logging": {
                    "level": "info",
                    "format": "json",
                    "console_output": True
                }
            }
        }

        with self._config_lock:
            self._configs.update(default_config)

    def _load_environment_overrides(self) -> None:
        """Load configuration overrides from environment variables."""
        env_prefix = "DMLOGN8N_"
        env_overrides = {}

        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                # Convert DMLOGN8N_DATABASE__DEFAULT__TYPE -> database.default.type
                config_path = key[len(env_prefix):].lower().replace('__', '.')

                # Try to parse as JSON, fallback to string
                try:
                    parsed_value = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    parsed_value = value

                # Set nested value
                self._set_nested_value(env_overrides, config_path.split('.'), parsed_value)

        if env_overrides:
            with self._config_lock:
                self._deep_merge(self._configs, env_overrides)
            self.logger.info(f"Applied {len(env_overrides)} environment variable overrides")

    def _process_environment_variables(self, config_data: Any) -> Any:
        """Process environment variable substitutions in configuration."""
        if isinstance(config_data, dict):
            processed = {}
            for key, value in config_data.items():
                processed[key] = self._process_environment_variables(value)
            return processed
        elif isinstance(config_data, list):
            return [self._process_environment_variables(item) for item in config_data]
        elif isinstance(config_data, str) and config_data.startswith("${") and config_data.endswith("}"):
            env_var = config_data[2:-1]
            default_value = None

            # Handle default values: ${VAR:default_value}
            if ":" in env_var:
                env_var, default_value = env_var.split(":", 1)

            value = os.getenv(env_var, default_value)
            if value is None:
                raise ConfigurationError(f"Environment variable '{env_var}' not found and no default provided")

            # Try to parse as JSON, fallback to string
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return value
        else:
            return config_data

    def _validate_all_configs(self) -> None:
        """Validate all loaded configurations."""
        results = self._validator.validate_config_data(self._configs)

        for config_type, result in results.items():
            if not result.is_valid:
                error_messages = [f"{error.field}: {error.message}" for error in result.errors]
                raise ConfigurationError(
                    f"Configuration validation failed for {config_type}: " + "; ".join(error_messages)
                )

            if result.warnings:
                warning_messages = [f"{warning.field}: {warning.message}" for warning in result.warnings]
                self.logger.warning(
                    f"Configuration warnings for {config_type}: " + "; ".join(warning_messages)
                )

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Deep merge two dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _set_nested_value(self, data: Dict[str, Any], path: List[str], value: Any) -> None:
        """Set a nested value in a dictionary."""
        current = data
        for part in path[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[path[-1]] = value

    def _calculate_checksum(self, data: Any) -> str:
        """Calculate checksum for configuration data."""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def _find_env_variables(self, data: Any, path: str = "") -> List[str]:
        """Find all environment variable references in configuration."""
        env_vars = []
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                env_vars.extend(self._find_env_variables(value, current_path))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                env_vars.extend(self._find_env_variables(item, current_path))
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            env_var = data[2:-1].split(":")[0]  # Remove default value if present
            env_vars.append(env_var)
        return env_vars

    def _find_secrets(self, data: Any, path: str = "") -> List[str]:
        """Find all secret fields in configuration."""
        secrets = []
        secret_patterns = [
            'password', 'api_key', 'secret', 'token', 'credential',
            'private_key', 'auth_token', 'client_secret'
        ]

        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if any(pattern in key.lower() for pattern in secret_patterns):
                    secrets.append(current_path)
                else:
                    secrets.extend(self._find_secrets(value, current_path))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]" if path else f"[{i}]"
                secrets.extend(self._find_secrets(item, current_path))

        return secrets

    def _notify_change_listeners(self, config_type: str, old_value: Any, new_value: Any, source: str) -> None:
        """Notify configuration change listeners."""
        event = ConfigChangeEvent(
            config_type=config_type,
            old_value=deepcopy(old_value),
            new_value=deepcopy(new_value),
            timestamp=datetime.now(timezone.utc),
            source=source,
            version=self._versions[-1].version if self._versions else "unknown"
        )

        with self._change_listeners_lock:
            listeners = self._change_listeners.get(config_type, [])
            global_listeners = self._change_listeners.get("*", [])

            for listener in listeners + global_listeners:
                try:
                    listener(event)
                except Exception as e:
                    self.logger.error(f"Error in change listener: {str(e)}")

    # Public API

    def get_config(self, config_type: str, key: Optional[str] = None, default: Any = None) -> Any:
        """Get configuration value."""
        with self._config_lock:
            if config_type not in self._configs:
                return default

            config_data = self._configs[config_type]

            if key is None:
                return deepcopy(config_data)

            # Navigate to nested key
            keys = key.split('.')
            current = config_data
            for k in keys:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return default

            return deepcopy(current)

    def get_database_config(self, name: Optional[str] = None) -> DatabaseConfig:
        """Get database configuration."""
        db_config = self.get_config('database')
        if not db_config:
            raise ConfigurationError("Database configuration not found")

        multi_db_config = MultiDatabaseConfig(**db_config)
        return multi_db_config.get_database(name)

    def get_model_config(self, name: str) -> ModelConfig:
        """Get AI model configuration."""
        model_config = self.get_config('ai_models')
        if not model_config:
            raise ConfigurationError("AI model configuration not found")

        multi_model_config = MultiModelConfig(**model_config)
        return multi_model_config.get_model(name)

    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration."""
        monitoring_config = self.get_config('monitoring')
        if not monitoring_config:
            raise ConfigurationError("Monitoring configuration not found")

        return MonitoringConfig(**monitoring_config)

    def set_config(self, config_type: str, key: str, value: Any, source: str = "manual") -> None:
        """Set configuration value."""
        with self._config_lock:
            if config_type not in self._configs:
                self._configs[config_type] = {}

            old_value = self.get_config(config_type, key)

            # Set nested value
            self._set_nested_value(self._configs[config_type], key.split('.'), value)

            # Validate if enabled
            if self._validate_on_load:
                try:
                    results = self._validator.validate_config_data(self._configs)
                    if not results.get(config_type, ValidationResult(True, [], [])).is_valid:
                        raise ConfigurationError("Configuration validation failed")
                except Exception as e:
                    # Rollback on validation failure
                    if old_value is not None:
                        self._set_nested_value(self._configs[config_type], key.split('.'), old_value)
                    else:
                        # Remove the key if it didn't exist before
                        self._remove_nested_value(self._configs[config_type], key.split('.'))
                    raise ConfigurationError(f"Configuration validation failed: {str(e)}")

            # Update metadata
            checksum = self._calculate_checksum(self._configs[config_type])
            self._metadata[config_type] = ConfigMetadata(
                loaded_at=datetime.now(timezone.utc),
                environment_variables=self._find_env_variables(self._configs[config_type]),
                secrets=self._find_secrets(self._configs[config_type]),
                checksum=checksum
            )

            # Add version
            version = ConfigVersion(
                version=f"v{len(self._versions) + 1}",
                timestamp=datetime.now(timezone.utc),
                checksum=checksum,
                environment=self._environment,
                description=f"Updated {config_type}.{key} from {source}"
            )
            self._versions.append(version)

            # Notify listeners
            self._notify_change_listeners(config_type, old_value, value, source)

        self.logger.info(f"Configuration updated: {config_type}.{key} = {value}")

    def _remove_nested_value(self, data: Dict[str, Any], path: List[str]) -> None:
        """Remove a nested value from a dictionary."""
        if len(path) == 1:
            data.pop(path[0], None)
        else:
            if path[0] in data and isinstance(data[path[0]], dict):
                self._remove_nested_value(data[path[0]], path[1:])

    def add_change_listener(self, config_type: str, listener: Callable[[ConfigChangeEvent], None]) -> None:
        """Add a configuration change listener."""
        with self._change_listeners_lock:
            if config_type not in self._change_listeners:
                self._change_listeners[config_type] = []
            self._change_listeners[config_type].append(listener)

    def remove_change_listener(self, config_type: str, listener: Callable[[ConfigChangeEvent], None]) -> None:
        """Remove a configuration change listener."""
        with self._change_listeners_lock:
            if config_type in self._change_listeners:
                try:
                    self._change_listeners[config_type].remove(listener)
                except ValueError:
                    pass  # Listener not found

    def reload_configuration(self) -> None:
        """Reload configuration from files."""
        self.logger.info("Reloading configuration...")
        self._load_configuration()
        self.logger.info("Configuration reloaded successfully")

    def validate_configuration(self) -> Dict[str, ValidationResult]:
        """Validate current configuration."""
        return self._validator.validate_config_data(self._configs)

    def get_configuration_versions(self) -> List[ConfigVersion]:
        """Get configuration version history."""
        with self._config_lock:
            return deepcopy(self._versions)

    def rollback_to_version(self, version: str) -> None:
        """Rollback configuration to a specific version."""
        # This is a simplified implementation
        # In a production system, you'd want to store full configuration snapshots
        raise NotImplementedError("Configuration rollback not yet implemented")

    def export_configuration(self, file_path: Union[str, Path], include_secrets: bool = False) -> None:
        """Export current configuration to a file."""
        file_path = Path(file_path)

        with self._config_lock:
            config_copy = deepcopy(self._configs)

            if not include_secrets:
                # Mask secrets
                self._mask_secrets(config_copy)

            with open(file_path, 'w') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config_copy, f, default_flow_style=False, indent=2)
                elif file_path.suffix.lower() == '.json':
                    json.dump(config_copy, f, indent=2, default=str)
                else:
                    raise ValueError(f"Unsupported file format: {file_path.suffix}")

        self.logger.info(f"Configuration exported to {file_path}")

    def _mask_secrets(self, data: Any) -> None:
        """Mask secret values in configuration."""
        secret_patterns = [
            'password', 'api_key', 'secret', 'token', 'credential',
            'private_key', 'auth_token', 'client_secret'
        ]

        if isinstance(data, dict):
            for key, value in data.items():
                if any(pattern in key.lower() for pattern in secret_patterns):
                    data[key] = "********"
                else:
                    self._mask_secrets(value)
        elif isinstance(data, list):
            for item in data:
                self._mask_secrets(item)

    @contextmanager
    def transaction(self):
        """Configuration transaction context."""
        # Store current state
        original_configs = deepcopy(self._configs)
        original_metadata = deepcopy(self._metadata)

        try:
            yield
            # Validate on commit if enabled
            if self._validate_on_load:
                self._validate_all_configs()
        except Exception as e:
            # Rollback on error
            with self._config_lock:
                self._configs = original_configs
                self._metadata = original_metadata
            raise ConfigurationError(f"Configuration transaction failed: {str(e)}")

    def get_environment(self) -> str:
        """Get current environment."""
        return self._environment

    def is_auto_reload_enabled(self) -> bool:
        """Check if auto-reload is enabled."""
        return self._auto_reload

    def get_metadata(self, config_type: str) -> Optional[ConfigMetadata]:
        """Get configuration metadata."""
        with self._config_lock:
            return self._metadata.get(config_type)


# Global configuration manager instance
config_manager = ConfigManager()