#!/usr/bin/env python3
"""
DMLogn8n Master Configuration Management - Centralized Configuration System
Manages all platform configuration with environment-specific overrides and validation
"""

import asyncio
import json
import os
import yaml
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging
import aiofiles
from pathlib import Path
import hashlib
from cryptography.fernet import Fernet
import base64

class ConfigScope(Enum):
    GLOBAL = "global"
    SYSTEM = "system"
    SERVICE = "service"
    USER = "user"
    ENVIRONMENT = "environment"

class ConfigFormat(Enum):
    JSON = "json"
    YAML = "yaml"
    ENV = "env"
    ENCRYPTED = "encrypted"

class ConfigEnvironment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

@dataclass
class ConfigSchema:
    key: str
    config_type: str  # string, integer, boolean, list, dict, password, etc.
    required: bool = True
    default_value: Any = None
    description: str = ""
    validation_func: Optional[Callable] = None
    sensitive: bool = False
    scope: ConfigScope = ConfigScope.GLOBAL
    environment_overrides: Dict[ConfigEnvironment, Any] = field(default_factory=dict)
    allowed_values: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    regex_pattern: Optional[str] = None

@dataclass
class ConfigChange:
    key: str
    old_value: Any
    new_value: Any
    changed_by: str
    timestamp: float
    environment: ConfigEnvironment
    scope: ConfigScope

class ConfigMaster:
    """
    Master configuration management system with validation, encryption, and environment support
    """

    def __init__(self, initial_config: Dict[str, Any] = None, environment: ConfigEnvironment = ConfigEnvironment.DEVELOPMENT):
        self.environment = environment
        self.logger = logging.getLogger('ConfigMaster')

        # Configuration storage
        self.config_data: Dict[str, Any] = initial_config or {}
        self.schemas: Dict[str, ConfigSchema] = {}
        self.change_history: List[ConfigChange] = []

        # Encryption
        self.encryption_key: Optional[bytes] = None
        self.cipher_suite: Optional[Fernet] = None

        # File paths
        self.config_dir = "/home/activeloguser/DMLogn8n/config"
        self.global_config_file = f"{self.config_dir}/global.json"
        self.env_config_file = f"{self.config_dir}/{environment.value}.json"
        self.schema_file = f"{self.config_dir}/schemas.json"
        self.secrets_file = f"{self.config_dir}/secrets.encrypted"
        self.change_log_file = f"{self.config_dir}/changes.json"

        # Watchers
        self.config_watchers: List[Callable] = []
        self.file_watcher_task: Optional[asyncio.Task] = None

        # Validation
        self.validation_errors: List[str] = []

    async def initialize(self):
        """Initialize the configuration master"""
        self.logger.info(f"Initializing ConfigMaster for environment: {self.environment.value}")

        # Ensure config directory exists
        await aiofiles.os.makedirs(self.config_dir, exist_ok=True)

        # Initialize encryption
        await self._initialize_encryption()

        # Load configuration files
        await self._load_configuration()

        # Load schemas
        await self._load_schemas()

        # Validate configuration
        await self._validate_all_configuration()

        # Load change history
        await self._load_change_history()

        # Start file watcher
        await self._start_file_watcher()

        self.logger.info("ConfigMaster initialized successfully")

    async def get(self, key: str, default: Any = None, scope: ConfigScope = None) -> Any:
        """Get configuration value with scope resolution"""
        # Resolve in order: environment > global > default
        value = None

        # Try environment-specific config first
        env_key = f"{self.environment.value}.{key}"
        if env_key in self.config_data:
            value = self.config_data[env_key]
        elif key in self.config_data:
            value = self.config_data[key]
        else:
            value = default

        # Check if value is encrypted and decrypt if needed
        if isinstance(value, str) and value.startswith('encrypted:'):
            value = await self._decrypt_value(value[10:])  # Remove 'encrypted:' prefix

        return value

    async def set(self, key: str, value: Any, scope: ConfigScope = ConfigScope.GLOBAL, changed_by: str = "system"):
        """Set configuration value with validation and logging"""
        # Validate against schema
        await self._validate_value(key, value)

        # Get old value for change tracking
        old_value = await self.get(key)

        # Encrypt if sensitive
        schema = self.schemas.get(key)
        if schema and schema.sensitive:
            value = f"encrypted:{await self._encrypt_value(value)}"

        # Set the value
        config_key = f"{self.environment.value}.{key}" if scope == ConfigScope.ENVIRONMENT else key
        self.config_data[config_key] = value

        # Record change
        change = ConfigChange(
            key=key,
            old_value=old_value,
            new_value=value,
            changed_by=changed_by,
            timestamp=datetime.now().timestamp(),
            environment=self.environment,
            scope=scope
        )
        self.change_history.append(change)

        # Save configuration
        await self._save_configuration()

        # Notify watchers
        await self._notify_watchers(key, old_value, value)

        # Publish change event if event bus is available
        await self._publish_change_event(change)

        self.logger.info(f"Configuration changed: {key} = {value} (by {changed_by})")

    async def update(self, updates: Dict[str, Any], scope: ConfigScope = ConfigScope.GLOBAL, changed_by: str = "system"):
        """Update multiple configuration values"""
        for key, value in updates.items():
            await self.set(key, value, scope, changed_by)

    async def register_schema(self, schema: ConfigSchema):
        """Register a configuration schema"""
        self.schemas[schema.key] = schema

        # Validate existing value
        current_value = await self.get(schema.key)
        if current_value is not None:
            await self._validate_value(schema.key, current_value)

        self.logger.info(f"Registered schema for: {schema.key}")

    async def validate_configuration(self) -> List[str]:
        """Validate all configuration against schemas"""
        self.validation_errors.clear()

        for key, schema in self.schemas.items():
            value = await self.get(key)
            if value is not None:
                await self._validate_value(key, value)

        return self.validation_errors.copy()

    async def get_environment_config(self, environment: ConfigEnvironment) -> Dict[str, Any]:
        """Get configuration for a specific environment"""
        env_config = {}
        prefix = f"{environment.value}."

        for key, value in self.config_data.items():
            if key.startswith(prefix):
                env_key = key[len(prefix):]
                env_config[env_key] = value

        return env_config

    async def set_environment_config(self, environment: ConfigEnvironment, config: Dict[str, Any], changed_by: str = "system"):
        """Set configuration for a specific environment"""
        for key, value in config.items():
            config_key = f"{environment.value}.{key}"
            self.config_data[config_key] = value

        await self._save_configuration()

        self.logger.info(f"Updated {environment.value} configuration with {len(config)} items")

    async def export_configuration(self, include_secrets: bool = False, format: ConfigFormat = ConfigFormat.JSON) -> str:
        """Export configuration to specified format"""
        config_to_export = {}

        for key, value in self.config_data.items():
            # Skip encrypted values unless explicitly requested
            if not include_secrets and isinstance(value, str) and value.startswith('encrypted:'):
                continue

            # Decrypt if needed
            if isinstance(value, str) and value.startswith('encrypted:'):
                try:
                    value = await self._decrypt_value(value[10:])
                except:
                    value = "[ENCRYPTED]"

            config_to_export[key] = value

        if format == ConfigFormat.JSON:
            return json.dumps(config_to_export, indent=2)
        elif format == ConfigFormat.YAML:
            return yaml.dump(config_to_export, default_flow_style=False)
        elif format == ConfigFormat.ENV:
            env_lines = []
            for key, value in config_to_export.items():
                if isinstance(value, str):
                    env_lines.append(f"{key}={value}")
                else:
                    env_lines.append(f"{key}={json.dumps(value)}")
            return "\n".join(env_lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    async def import_configuration(self, config_data: Union[str, Dict[str, Any]], format: ConfigFormat = ConfigFormat.JSON, merge: bool = True, changed_by: str = "import"):
        """Import configuration from specified format"""
        if isinstance(config_data, str):
            if format == ConfigFormat.JSON:
                config_dict = json.loads(config_data)
            elif format == ConfigFormat.YAML:
                config_dict = yaml.safe_load(config_data)
            elif format == ConfigFormat.ENV:
                config_dict = {}
                for line in config_data.strip().split('\n'):
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.split('=', 1)
                        try:
                            config_dict[key.strip()] = json.loads(value.strip())
                        except:
                            config_dict[key.strip()] = value.strip()
            else:
                raise ValueError(f"Unsupported import format: {format}")
        else:
            config_dict = config_data

        if not merge:
            self.config_data.clear()

        # Validate and set values
        for key, value in config_dict.items():
            await self.set(key, value, changed_by=changed_by)

        self.logger.info(f"Imported {len(config_dict)} configuration items")

    async def backup_configuration(self, backup_name: str = None) -> str:
        """Create a backup of current configuration"""
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}"

        backup_file = f"{self.config_dir}/backups/{backup_name}.json"
        await aiofiles.os.makedirs(f"{self.config_dir}/backups", exist_ok=True)

        backup_data = {
            'environment': self.environment.value,
            'config_data': self.config_data,
            'schemas': {k: {
                'key': v.key,
                'config_type': v.config_type,
                'required': v.required,
                'default_value': v.default_value,
                'description': v.description,
                'sensitive': v.sensitive,
                'scope': v.scope.value,
                'allowed_values': v.allowed_values,
                'min_value': v.min_value,
                'max_value': v.max_value,
                'regex_pattern': v.regex_pattern
            } for k, v in self.schemas.items()},
            'change_history': [
                {
                    'key': c.key,
                    'old_value': c.old_value,
                    'new_value': c.new_value,
                    'changed_by': c.changed_by,
                    'timestamp': c.timestamp,
                    'environment': c.environment.value,
                    'scope': c.scope.value
                }
                for c in self.change_history[-100:]  # Last 100 changes
            ],
            'backup_timestamp': datetime.now().isoformat()
        }

        async with aiofiles.open(backup_file, 'w') as f:
            await f.write(json.dumps(backup_data, indent=2))

        self.logger.info(f"Configuration backed up to: {backup_file}")
        return backup_file

    async def restore_configuration(self, backup_file: str, merge: bool = False):
        """Restore configuration from backup"""
        async with aiofiles.open(backup_file, 'r') as f:
            backup_data = json.loads(await f.read())

        if not merge:
            self.config_data.clear()
            self.schemas.clear()
            self.change_history.clear()

        # Restore configuration
        self.config_data.update(backup_data['config_data'])

        # Restore schemas
        for schema_data in backup_data['schemas'].values():
            schema = ConfigSchema(
                key=schema_data['key'],
                config_type=schema_data['config_type'],
                required=schema_data['required'],
                default_value=schema_data['default_value'],
                description=schema_data['description'],
                sensitive=schema_data['sensitive'],
                scope=ConfigScope(schema_data['scope']),
                allowed_values=schema_data['allowed_values'],
                min_value=schema_data['min_value'],
                max_value=schema_data['max_value'],
                regex_pattern=schema_data['regex_pattern']
            )
            self.schemas[schema.key] = schema

        # Restore change history
        for change_data in backup_data['change_history']:
            change = ConfigChange(
                key=change_data['key'],
                old_value=change_data['old_value'],
                new_value=change_data['new_value'],
                changed_by=change_data['changed_by'],
                timestamp=change_data['timestamp'],
                environment=ConfigEnvironment(change_data['environment']),
                scope=ConfigScope(change_data['scope'])
            )
            self.change_history.append(change)

        await self._save_configuration()
        self.logger.info(f"Configuration restored from: {backup_file}")

    def add_watcher(self, callback: Callable):
        """Add a configuration change watcher"""
        self.config_watchers.append(callback)

    def remove_watcher(self, callback: Callable):
        """Remove a configuration change watcher"""
        if callback in self.config_watchers:
            self.config_watchers.remove(callback)

    async def _initialize_encryption(self):
        """Initialize encryption for sensitive values"""
        try:
            # Try to load existing key
            key_file = f"{self.config_dir}/.encryption_key"
            if await aiofiles.os.path.exists(key_file):
                async with aiofiles.open(key_file, 'rb') as f:
                    self.encryption_key = await f.read()
            else:
                # Generate new key
                self.encryption_key = Fernet.generate_key()
                async with aiofiles.open(key_file, 'wb') as f:
                    await f.write(self.encryption_key)
                # Set file permissions to read-only for owner
                os.chmod(key_file, 0o600)

            self.cipher_suite = Fernet(self.encryption_key)
            self.logger.info("Encryption initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            self.encryption_key = None
            self.cipher_suite = None

    async def _encrypt_value(self, value: Any) -> str:
        """Encrypt a sensitive value"""
        if not self.cipher_suite:
            raise RuntimeError("Encryption not available")

        # Convert to JSON string for consistent encryption
        json_value = json.dumps(value)
        encrypted_bytes = self.cipher_suite.encrypt(json_value.encode())
        return base64.b64encode(encrypted_bytes).decode()

    async def _decrypt_value(self, encrypted_value: str) -> Any:
        """Decrypt a sensitive value"""
        if not self.cipher_suite:
            raise RuntimeError("Encryption not available")

        encrypted_bytes = base64.b64decode(encrypted_value.encode())
        decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
        json_value = decrypted_bytes.decode()
        return json.loads(json_value)

    async def _load_configuration(self):
        """Load configuration from files"""
        # Load global configuration
        if await aiofiles.os.path.exists(self.global_config_file):
            async with aiofiles.open(self.global_config_file, 'r') as f:
                global_config = json.loads(await f.read())
                self.config_data.update(global_config)

        # Load environment-specific configuration
        if await aiofiles.os.path.exists(self.env_config_file):
            async with aiofiles.open(self.env_config_file, 'r') as f:
                env_config = json.loads(await f.read())
                self.config_data.update(env_config)

        # Load environment variables
        await self._load_environment_variables()

        self.logger.info(f"Loaded configuration with {len(self.config_data)} items")

    async def _load_environment_variables(self):
        """Load configuration from environment variables"""
        env_prefix = "DMLOG_"
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                # Try to parse as JSON, fallback to string
                try:
                    parsed_value = json.loads(value)
                    self.config_data[config_key] = parsed_value
                except:
                    self.config_data[config_key] = value

    async def _load_schemas(self):
        """Load configuration schemas"""
        if await aiofiles.os.path.exists(self.schema_file):
            async with aiofiles.open(self.schema_file, 'r') as f:
                schemas_data = json.loads(await f.read())

            for schema_data in schemas_data:
                schema = ConfigSchema(
                    key=schema_data['key'],
                    config_type=schema_data['config_type'],
                    required=schema_data.get('required', True),
                    default_value=schema_data.get('default_value'),
                    description=schema_data.get('description', ''),
                    sensitive=schema_data.get('sensitive', False),
                    scope=ConfigScope(schema_data.get('scope', 'global')),
                    allowed_values=schema_data.get('allowed_values'),
                    min_value=schema_data.get('min_value'),
                    max_value=schema_data.get('max_value'),
                    regex_pattern=schema_data.get('regex_pattern')
                )
                self.schemas[schema.key] = schema

        # Register default schemas
        await self._register_default_schemas()

    async def _register_default_schemas(self):
        """Register default configuration schemas"""
        default_schemas = [
            ConfigSchema(
                key="database.host",
                config_type="string",
                required=True,
                default_value="localhost",
                description="Database host",
                scope=ConfigScope.SYSTEM
            ),
            ConfigSchema(
                key="database.port",
                config_type="integer",
                required=True,
                default_value=5432,
                description="Database port",
                scope=ConfigScope.SYSTEM,
                min_value=1,
                max_value=65535
            ),
            ConfigSchema(
                key="database.password",
                config_type="password",
                required=True,
                description="Database password",
                scope=ConfigScope.SYSTEM,
                sensitive=True
            ),
            ConfigSchema(
                key="api.port",
                config_type="integer",
                required=True,
                default_value=8000,
                description="API server port",
                scope=ConfigScope.SYSTEM,
                min_value=1,
                max_value=65535
            ),
            ConfigSchema(
                key="log_level",
                config_type="string",
                required=True,
                default_value="INFO",
                description="Logging level",
                scope=ConfigScope.GLOBAL,
                allowed_values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            ),
            ConfigSchema(
                key="debug_mode",
                config_type="boolean",
                required=False,
                default_value=False,
                description="Enable debug mode",
                scope=ConfigScope.GLOBAL
            )
        ]

        for schema in default_schemas:
            if schema.key not in self.schemas:
                self.schemas[schema.key] = schema

    async def _validate_value(self, key: str, value: Any):
        """Validate a configuration value against its schema"""
        if key not in self.schemas:
            return  # No schema to validate against

        schema = self.schemas[key]

        # Type validation
        if schema.config_type == "string" and not isinstance(value, str):
            raise ValueError(f"Configuration {key} must be a string")
        elif schema.config_type == "integer" and not isinstance(value, int):
            raise ValueError(f"Configuration {key} must be an integer")
        elif schema.config_type == "float" and not isinstance(value, (int, float)):
            raise ValueError(f"Configuration {key} must be a number")
        elif schema.config_type == "boolean" and not isinstance(value, bool):
            raise ValueError(f"Configuration {key} must be a boolean")
        elif schema.config_type == "list" and not isinstance(value, list):
            raise ValueError(f"Configuration {key} must be a list")
        elif schema.config_type == "dict" and not isinstance(value, dict):
            raise ValueError(f"Configuration {key} must be a dictionary")

        # Value validation
        if schema.allowed_values and value not in schema.allowed_values:
            raise ValueError(f"Configuration {key} must be one of {schema.allowed_values}")

        if schema.min_value is not None and isinstance(value, (int, float)):
            if value < schema.min_value:
                raise ValueError(f"Configuration {key} must be >= {schema.min_value}")

        if schema.max_value is not None and isinstance(value, (int, float)):
            if value > schema.max_value:
                raise ValueError(f"Configuration {key} must be <= {schema.max_value}")

        if schema.regex_pattern and isinstance(value, str):
            import re
            if not re.match(schema.regex_pattern, value):
                raise ValueError(f"Configuration {key} does not match pattern {schema.regex_pattern}")

        # Custom validation
        if schema.validation_func:
            if asyncio.iscoroutinefunction(schema.validation_func):
                await schema.validation_func(value)
            else:
                schema.validation_func(value)

    async def _validate_all_configuration(self):
        """Validate all configuration values"""
        for key, schema in self.schemas.items():
            value = await self.get(key)

            if value is None:
                if schema.required:
                    error_msg = f"Required configuration {key} is missing"
                    self.validation_errors.append(error_msg)
                elif schema.default_value is not None:
                    await self.set(key, schema.default_value, changed_by="validation")
            else:
                try:
                    await self._validate_value(key, value)
                except ValueError as e:
                    error_msg = f"Configuration {key} validation failed: {str(e)}"
                    self.validation_errors.append(error_msg)

        if self.validation_errors:
            self.logger.error(f"Configuration validation failed with {len(self.validation_errors)} errors")
            for error in self.validation_errors:
                self.logger.error(f"  - {error}")

    async def _save_configuration(self):
        """Save configuration to files"""
        # Separate global and environment-specific configs
        global_config = {}
        env_config = {}

        for key, value in self.config_data.items():
            if '.' in key and key.split('.')[0] in [env.value for env in ConfigEnvironment]:
                env_config[key] = value
            else:
                global_config[key] = value

        # Save global configuration
        async with aiofiles.open(self.global_config_file, 'w') as f:
            await f.write(json.dumps(global_config, indent=2))

        # Save environment configuration
        async with aiofiles.open(self.env_config_file, 'w') as f:
            await f.write(json.dumps(env_config, indent=2))

        # Save schemas
        schemas_data = []
        for schema in self.schemas.values():
            schema_dict = {
                'key': schema.key,
                'config_type': schema.config_type,
                'required': schema.required,
                'default_value': schema.default_value,
                'description': schema.description,
                'sensitive': schema.sensitive,
                'scope': schema.scope.value,
                'allowed_values': schema.allowed_values,
                'min_value': schema.min_value,
                'max_value': schema.max_value,
                'regex_pattern': schema.regex_pattern
            }
            schemas_data.append(schema_dict)

        async with aiofiles.open(self.schema_file, 'w') as f:
            await f.write(json.dumps(schemas_data, indent=2))

        # Save change history
        await self._save_change_history()

    async def _load_change_history(self):
        """Load change history from file"""
        try:
            if await aiofiles.os.path.exists(self.change_log_file):
                async with aiofiles.open(self.change_log_file, 'r') as f:
                    changes_data = json.loads(await f.read())

                for change_data in changes_data:
                    change = ConfigChange(
                        key=change_data['key'],
                        old_value=change_data['old_value'],
                        new_value=change_data['new_value'],
                        changed_by=change_data['changed_by'],
                        timestamp=change_data['timestamp'],
                        environment=ConfigEnvironment(change_data['environment']),
                        scope=ConfigScope(change_data['scope'])
                    )
                    self.change_history.append(change)

        except Exception as e:
            self.logger.error(f"Error loading change history: {e}")

    async def _save_change_history(self):
        """Save change history to file"""
        try:
            changes_data = []
            for change in self.change_history[-1000:]:  # Keep last 1000 changes
                change_dict = {
                    'key': change.key,
                    'old_value': change.old_value,
                    'new_value': change.new_value,
                    'changed_by': change.changed_by,
                    'timestamp': change.timestamp,
                    'environment': change.environment.value,
                    'scope': change.scope.value
                }
                changes_data.append(change_dict)

            async with aiofiles.open(self.change_log_file, 'w') as f:
                await f.write(json.dumps(changes_data, indent=2))

        except Exception as e:
            self.logger.error(f"Error saving change history: {e}")

    async def _start_file_watcher(self):
        """Start file watcher for configuration changes"""
        self.file_watcher_task = asyncio.create_task(self._watch_config_files())

    async def _watch_config_files(self):
        """Watch configuration files for external changes"""
        last_modified = {}

        while True:
            try:
                config_files = [self.global_config_file, self.env_config_file, self.schema_file]
                reload_needed = False

                for file_path in config_files:
                    if await aiofiles.os.path.exists(file_path):
                        stat = await aiofiles.os.stat(file_path)
                        current_modified = stat.st_mtime

                        if file_path not in last_modified:
                            last_modified[file_path] = current_modified
                        elif current_modified > last_modified[file_path]:
                            last_modified[file_path] = current_modified
                            reload_needed = True

                if reload_needed:
                    self.logger.info("Configuration files changed externally, reloading...")
                    await self._load_configuration()
                    await self._validate_all_configuration()
                    await self._notify_watchers("*", "EXTERNAL_RELOAD", "EXTERNAL_RELOAD")

                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                self.logger.error(f"Error in file watcher: {e}")
                await asyncio.sleep(10)

    async def _notify_watchers(self, key: str, old_value: Any, new_value: Any):
        """Notify all configuration watchers"""
        for watcher in self.config_watchers:
            try:
                if asyncio.iscoroutinefunction(watcher):
                    await watcher(key, old_value, new_value)
                else:
                    await asyncio.get_event_loop().run_in_executor(
                        None, watcher, key, old_value, new_value
                    )
            except Exception as e:
                self.logger.error(f"Error notifying config watcher: {e}")

    async def _publish_change_event(self, change: ConfigChange):
        """Publish configuration change event"""
        # This would integrate with the event bus if available
        # For now, just log the change
        self.logger.info(f"Config change: {change.key} by {change.changed_by}")

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration"""
        return {
            'environment': self.environment.value,
            'total_config_items': len(self.config_data),
            'total_schemas': len(self.schemas),
            'validation_errors': len(self.validation_errors),
            'change_history_size': len(self.change_history),
            'watchers_count': len(self.config_watchers),
            'sensitive_configs': sum(1 for s in self.schemas.values() if s.sensitive),
            'required_configs': sum(1 for s in self.schemas.values() if s.required),
            'config_by_scope': {
                scope.value: sum(1 for s in self.schemas.values() if s.scope == scope)
                for scope in ConfigScope
            }
        }

    def get_recent_changes(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent configuration changes"""
        recent_changes = self.change_history[-limit:]
        return [
            {
                'key': change.key,
                'old_value': change.old_value,
                'new_value': change.new_value,
                'changed_by': change.changed_by,
                'timestamp': change.timestamp,
                'environment': change.environment.value,
                'scope': change.scope.value,
                'datetime': datetime.fromtimestamp(change.timestamp).isoformat()
            }
            for change in recent_changes
        ]