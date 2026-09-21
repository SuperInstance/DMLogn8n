#!/usr/bin/env python3
"""
Configuration Distributor for DMLogn8n Multi-Agent Platform

This module provides comprehensive configuration distribution including:
- Configuration storage and retrieval via Consul KV
- Configuration versioning and history tracking
- Configuration validation and schema enforcement
- Hot-reloading capabilities
- Environment-specific configurations
- Configuration encryption and security
"""

import asyncio
import json
import logging
import hashlib
import base64
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
import consul.aio
from cryptography.fernet import Fernet
import yaml
import jsonschema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfigScope(Enum):
    """Configuration scope levels"""
    GLOBAL = "global"
    DATACENTER = "datacenter"
    ENVIRONMENT = "environment"
    SERVICE = "service"
    SERVICE_TYPE = "service_type"
    INSTANCE = "instance"

class ConfigFormat(Enum):
    """Configuration format types"""
    JSON = "json"
    YAML = "yaml"
    ENV = "env"
    TOML = "toml"

@dataclass
class ConfigVersion:
    """Configuration version information"""
    version: str
    created_at: datetime
    created_by: str
    description: str
    checksum: str
    size_bytes: int
    parent_version: Optional[str] = None
    tags: List[str] = field(default_factory=list)

@dataclass
class ConfigSchema:
    """Configuration schema definition"""
    schema_id: str
    name: str
    version: str
    schema_definition: Dict[str, Any]
    required_fields: List[str] = field(default_factory=list)
    default_values: Dict[str, Any] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConfigEntry:
    """Configuration entry"""
    key: str
    value: Any
    scope: ConfigScope
    format: ConfigFormat
    schema_id: Optional[str] = None
    encrypted: bool = False
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class ConfigDistributor:
    """
    Configuration distribution system for DMLogn8n platform
    """

    def __init__(self, consul_manager, encryption_key: Optional[str] = None):
        self.consul_manager = consul_manager
        self.consul = consul_manager.consul
        self.schemas = {}
        self.config_cache = {}
        self.version_history = {}
        self.watchers = {}
        self.encryption_key = encryption_key
        self.cipher = Fernet(encryption_key.encode()) if encryption_key else None
        self.validation_handlers = {}
        self._shutdown = False

    async def register_schema(self, schema: ConfigSchema) -> bool:
        """Register a configuration schema"""
        try:
            self.schemas[schema.schema_id] = schema

            # Store schema in Consul KV
            schema_path = f"dmlogn8n/config/schemas/{schema.schema_id}"
            schema_data = asdict(schema)
            schema_data['registered_at'] = datetime.now().isoformat()

            await self.consul.kv.put(schema_path, json.dumps(schema_data))

            logger.info(f"Configuration schema registered: {schema.schema_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to register schema: {e}")
            return False

    async def store_config(self,
                         key: str,
                         value: Any,
                         scope: ConfigScope = ConfigScope.SERVICE,
                         format: ConfigFormat = ConfigFormat.JSON,
                         schema_id: Optional[str] = None,
                         encrypted: bool = False,
                         metadata: Optional[Dict[str, Any]] = None,
                         version_description: str = "") -> bool:
        """Store configuration in Consul KV"""
        try:
            # Validate configuration if schema provided
            if schema_id and schema_id in self.schemas:
                validation_result = await self.validate_config(value, schema_id)
                if not validation_result['valid']:
                    logger.error(f"Configuration validation failed: {validation_result['errors']}")
                    return False

            # Serialize value
            serialized_value = self._serialize_value(value, format)

            # Encrypt if required
            if encrypted and self.cipher:
                serialized_value = self._encrypt_value(serialized_value)

            # Calculate checksum
            checksum = hashlib.sha256(serialized_value.encode()).hexdigest()

            # Create configuration entry
            config_entry = ConfigEntry(
                key=key,
                value=value,
                scope=scope,
                format=format,
                schema_id=schema_id,
                encrypted=encrypted,
                metadata=metadata or {},
                version=self._generate_version(checksum)
            )

            # Build KV path
            kv_path = self._build_kv_path(key, scope)

            # Store configuration
            config_data = {
                'value': serialized_value,
                'format': format.value,
                'schema_id': schema_id,
                'encrypted': encrypted,
                'checksum': checksum,
                'metadata': config_entry.metadata,
                'version': config_entry.version,
                'created_at': config_entry.created_at.isoformat(),
                'updated_at': config_entry.updated_at.isoformat()
            }

            success = await self.consul.kv.put(kv_path, json.dumps(config_data))

            if success:
                # Update cache
                self.config_cache[key] = config_entry

                # Store version history
                await self._store_version_history(key, config_entry, version_description)

                # Notify watchers
                await self._notify_watchers(key, config_entry)

                logger.info(f"Configuration stored: {key}")
                return True
            else:
                logger.error(f"Failed to store configuration: {key}")
                return False

        except Exception as e:
            logger.error(f"Configuration store error: {e}")
            return False

    async def get_config(self,
                        key: str,
                        scope: Optional[ConfigScope] = None,
                        decrypt: bool = True) -> Optional[ConfigEntry]:
        """Retrieve configuration from Consul KV"""
        try:
            # Check cache first
            if key in self.config_cache:
                return self.config_cache[key]

            # Try different scopes if not specified
            scopes_to_try = [scope] if scope else list(ConfigScope)

            for try_scope in scopes_to_try:
                kv_path = self._build_kv_path(key, try_scope)

                _, data = await self.consul.kv.get(kv_path)
                if data:
                    return await self._deserialize_config_entry(data, decrypt)

            logger.warning(f"Configuration not found: {key}")
            return None

        except Exception as e:
            logger.error(f"Configuration retrieval error: {e}")
            return None

    async def get_config_value(self,
                              key: str,
                              default: Any = None,
                              scope: Optional[ConfigScope] = None) -> Any:
        """Get configuration value with default fallback"""
        try:
            config_entry = await self.get_config(key, scope)
            return config_entry.value if config_entry else default

        except Exception as e:
            logger.error(f"Failed to get config value: {e}")
            return default

    async def update_config(self,
                           key: str,
                           value: Any,
                           description: str = "Configuration update") -> bool:
        """Update existing configuration"""
        try:
            # Get current configuration
            current_config = await self.get_config(key)
            if not current_config:
                return await self.store_config(
                    key=key,
                    value=value,
                    scope=current_config.scope if current_config else ConfigScope.SERVICE,
                    format=current_config.format if current_config else ConfigFormat.JSON,
                    schema_id=current_config.schema_id if current_config else None,
                    encrypted=current_config.encrypted if current_config else False,
                    version_description=description
                )

            # Update configuration
            return await self.store_config(
                key=key,
                value=value,
                scope=current_config.scope,
                format=current_config.format,
                schema_id=current_config.schema_id,
                encrypted=current_config.encrypted,
                metadata=current_config.metadata,
                version_description=description
            )

        except Exception as e:
            logger.error(f"Configuration update error: {e}")
            return False

    async def delete_config(self, key: str, scope: Optional[ConfigScope] = None) -> bool:
        """Delete configuration"""
        try:
            # Delete from all scopes if not specified
            scopes_to_delete = [scope] if scope else list(ConfigScope)

            for delete_scope in scopes_to_delete:
                kv_path = self._build_kv_path(key, delete_scope)
                await self.consul.kv.delete(kv_path)

            # Remove from cache
            if key in self.config_cache:
                del self.config_cache[key]

            logger.info(f"Configuration deleted: {key}")
            return True

        except Exception as e:
            logger.error(f"Configuration delete error: {e}")
            return False

    async def validate_config(self, value: Any, schema_id: str) -> Dict[str, Any]:
        """Validate configuration against schema"""
        try:
            if schema_id not in self.schemas:
                return {
                    'valid': False,
                    'errors': [f"Schema not found: {schema_id}"]
                }

            schema = self.schemas[schema_id]

            # Validate using jsonschema
            try:
                jsonschema.validate(value, schema.schema_definition)
                return {'valid': True, 'errors': []}
            except jsonschema.ValidationError as e:
                return {
                    'valid': False,
                    'errors': [str(e)]
                }

        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"]
            }

    async def watch_config(self, key: str, callback: Callable) -> str:
        """Watch for configuration changes"""
        try:
            watcher_id = f"watcher_{key}_{int(asyncio.get_event_loop().time())}"
            self.watchers[watcher_id] = {
                'key': key,
                'callback': callback,
                'active': True
            }

            # Start watching task
            asyncio.create_task(self._watch_config_loop(watcher_id, key, callback))

            logger.info(f"Configuration watcher started: {watcher_id}")
            return watcher_id

        except Exception as e:
            logger.error(f"Failed to start config watcher: {e}")
            return ""

    async def stop_watching(self, watcher_id: str) -> bool:
        """Stop configuration watcher"""
        try:
            if watcher_id in self.watchers:
                self.watchers[watcher_id]['active'] = False
                del self.watchers[watcher_id]
                logger.info(f"Configuration watcher stopped: {watcher_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to stop config watcher: {e}")
            return False

    async def get_config_history(self, key: str, limit: int = 10) -> List[ConfigVersion]:
        """Get configuration version history"""
        try:
            history_path = f"dmlogn8n/config/history/{key}"
            _, data = await self.consul.kv.get(history_path)

            if data:
                history_data = json.loads(data['Value'].decode('utf-8'))
                versions = []

                for version_data in history_data[-limit:]:
                    version = ConfigVersion(
                        version=version_data['version'],
                        created_at=datetime.fromisoformat(version_data['created_at']),
                        created_by=version_data['created_by'],
                        description=version_data['description'],
                        checksum=version_data['checksum'],
                        size_bytes=version_data['size_bytes'],
                        parent_version=version_data.get('parent_version'),
                        tags=version_data.get('tags', [])
                    )
                    versions.append(version)

                return versions

            return []

        except Exception as e:
            logger.error(f"Failed to get config history: {e}")
            return []

    async def rollback_config(self, key: str, version: str) -> bool:
        """Rollback configuration to specific version"""
        try:
            # Get version history
            history = await self.get_config_history(key, limit=50)

            # Find target version
            target_version = None
            for v in history:
                if v.version == version:
                    target_version = v
                    break

            if not target_version:
                logger.error(f"Version not found: {version}")
                return False

            # Get backup data
            backup_path = f"dmlogn8n/config/backups/{key}/{version}"
            _, data = await self.consul.kv.get(backup_path)

            if not data:
                logger.error(f"Backup data not found for version: {version}")
                return False

            # Restore configuration
            backup_data = json.loads(data['Value'].decode('utf-8'))
            return await self.update_config(
                key=key,
                value=backup_data['value'],
                description=f"Rollback to version {version}"
            )

        except Exception as e:
            logger.error(f"Configuration rollback error: {e}")
            return False

    async def export_configs(self,
                           scope: Optional[ConfigScope] = None,
                           keys_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Export configurations"""
        try:
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'scope': scope.value if scope else 'all',
                'configurations': {}
            }

            # Get configurations
            if scope:
                base_path = f"dmlogn8n/config/{scope.value}"
            else:
                base_path = "dmlogn8n/config"

            _, keys = await self.consul.kv.get(base_path, keys=True, separator='/')

            if keys:
                for key in keys:
                    if not keys_filter or any(filter_key in key for filter_key in keys_filter):
                        config_entry = await self.get_config(key)
                        if config_entry:
                            export_data['configurations'][key] = asdict(config_entry)

            return export_data

        except Exception as e:
            logger.error(f"Configuration export error: {e}")
            return {}

    async def import_configs(self,
                           config_data: Dict[str, Any],
                           overwrite: bool = False) -> Dict[str, bool]:
        """Import configurations"""
        try:
            results = {}

            for key, config_dict in config_data.get('configurations', {}).items():
                try:
                    # Check if exists and overwrite is False
                    if not overwrite:
                        existing = await self.get_config(key)
                        if existing:
                            results[key] = False
                            continue

                    # Import configuration
                    success = await self.store_config(
                        key=key,
                        value=config_dict['value'],
                        scope=ConfigScope(config_dict['scope']),
                        format=ConfigFormat(config_dict['format']),
                        schema_id=config_dict.get('schema_id'),
                        encrypted=config_dict.get('encrypted', False),
                        metadata=config_dict.get('metadata', {}),
                        version_description="Imported configuration"
                    )

                    results[key] = success

                except Exception as e:
                    logger.error(f"Failed to import config {key}: {e}")
                    results[key] = False

            return results

        except Exception as e:
            logger.error(f"Configuration import error: {e}")
            return {}

    def _build_kv_path(self, key: str, scope: ConfigScope) -> str:
        """Build Consul KV path for configuration"""
        base_path = "dmlogn8n/config"
        return f"{base_path}/{scope.value}/{key}"

    def _serialize_value(self, value: Any, format: ConfigFormat) -> str:
        """Serialize value based on format"""
        if format == ConfigFormat.JSON:
            return json.dumps(value, indent=2)
        elif format == ConfigFormat.YAML:
            return yaml.dump(value, default_flow_style=False)
        elif format == ConfigFormat.ENV:
            if isinstance(value, dict):
                return '\n'.join([f"{k}={v}" for k, v in value.items()])
            else:
                return str(value)
        elif format == ConfigFormat.TOML:
            # Simple TOML serialization (consider using toml library for complex cases)
            if isinstance(value, dict):
                return '\n'.join([f"{k} = {json.dumps(v)}" for k, v in value.items()])
            else:
                return str(value)
        else:
            return str(value)

    def _encrypt_value(self, value: str) -> str:
        """Encrypt configuration value"""
        if not self.cipher:
            raise ValueError("Encryption key not provided")

        encrypted_data = self.cipher.encrypt(value.encode())
        return base64.b64encode(encrypted_data).decode()

    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt configuration value"""
        if not self.cipher:
            raise ValueError("Encryption key not provided")

        encrypted_data = base64.b64decode(encrypted_value.encode())
        decrypted_data = self.cipher.decrypt(encrypted_data)
        return decrypted_data.decode()

    def _generate_version(self, checksum: str) -> str:
        """Generate version string based on checksum and timestamp"""
        timestamp = int(datetime.now().timestamp())
        return f"v{timestamp}_{checksum[:8]}"

    async def _deserialize_config_entry(self, data: Dict[str, Any], decrypt: bool = True) -> ConfigEntry:
        """Deserialize configuration entry from Consul data"""
        try:
            config_data = json.loads(data['Value'].decode('utf-8'))

            # Deserialize value
            serialized_value = config_data['value']
            if config_data.get('encrypted', False) and decrypt:
                serialized_value = self._decrypt_value(serialized_value)

            # Parse value based on format
            format_type = ConfigFormat(config_data['format'])
            if format_type == ConfigFormat.JSON:
                value = json.loads(serialized_value)
            elif format_type == ConfigFormat.YAML:
                value = yaml.safe_load(serialized_value)
            elif format_type == ConfigFormat.ENV:
                # Parse environment format
                value = {}
                for line in serialized_value.split('\n'):
                    if '=' in line:
                        k, v = line.split('=', 1)
                        value[k.strip()] = v.strip()
            else:
                value = serialized_value

            return ConfigEntry(
                key="",  # Will be set by caller
                value=value,
                scope=ConfigScope(data['Key'].split('/')[-2]),  # Extract scope from path
                format=format_type,
                schema_id=config_data.get('schema_id'),
                encrypted=config_data.get('encrypted', False),
                version=config_data.get('version', '1.0.0'),
                metadata=config_data.get('metadata', {}),
                created_at=datetime.fromisoformat(config_data.get('created_at', datetime.now().isoformat())),
                updated_at=datetime.fromisoformat(config_data.get('updated_at', datetime.now().isoformat()))
            )

        except Exception as e:
            logger.error(f"Failed to deserialize config entry: {e}")
            raise

    async def _store_version_history(self, key: str, config_entry: ConfigEntry, description: str):
        """Store configuration version history"""
        try:
            # Calculate checksum
            serialized_value = self._serialize_value(config_entry.value, config_entry.format)
            checksum = hashlib.sha256(serialized_value.encode()).hexdigest()

            # Create version record
            version_record = {
                'version': config_entry.version,
                'created_at': config_entry.created_at.isoformat(),
                'created_by': 'config_distributor',
                'description': description,
                'checksum': checksum,
                'size_bytes': len(serialized_value.encode()),
                'parent_version': None  # Could track parent versions
            }

            # Store in history
            history_path = f"dmlogn8n/config/history/{key}"
            _, existing_data = await self.consul.kv.get(history_path)

            if existing_data:
                history = json.loads(existing_data['Value'].decode('utf-8'))
            else:
                history = []

            history.append(version_record)

            # Keep only last 50 versions
            if len(history) > 50:
                history = history[-50:]

            await self.consul.kv.put(history_path, json.dumps(history))

            # Store backup
            backup_path = f"dmlogn8n/config/backups/{key}/{config_entry.version}"
            backup_data = {
                'value': config_entry.value,
                'format': config_entry.format.value,
                'schema_id': config_entry.schema_id,
                'metadata': config_entry.metadata
            }
            await self.consul.kv.put(backup_path, json.dumps(backup_data))

        except Exception as e:
            logger.error(f"Failed to store version history: {e}")

    async def _notify_watchers(self, key: str, config_entry: ConfigEntry):
        """Notify configuration watchers of changes"""
        try:
            for watcher_id, watcher_info in self.watchers.items():
                if watcher_info['key'] == key and watcher_info['active']:
                    try:
                        await watcher_info['callback'](config_entry)
                    except Exception as e:
                        logger.error(f"Watcher notification error {watcher_id}: {e}")

        except Exception as e:
            logger.error(f"Failed to notify watchers: {e}")

    async def _watch_config_loop(self, watcher_id: str, key: str, callback: Callable):
        """Watch for configuration changes"""
        try:
            index = None
            last_value = None

            while not self._shutdown and watcher_id in self.watchers and self.watchers[watcher_id]['active']:
                try:
                    # Build path based on scope
                    path = f"dmlogn8n/config/{self.watchers[watcher_id]['scope']}/{key}"

                    # Use blocking query
                    index, data = await self.consul.kv.get(path, index=index, wait='30s')

                    if data:
                        current_value = data['Value']
                        if current_value != last_value:
                            # Configuration changed
                            config_entry = await self._deserialize_config_entry(data)
                            await callback(config_entry)
                            last_value = current_value

                except Exception as e:
                    logger.error(f"Config watch loop error {watcher_id}: {e}")
                    await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Config watch loop failed {watcher_id}: {e}")

    async def create_default_schemas(self):
        """Create default configuration schemas"""
        try:
            # Service configuration schema
            service_schema = ConfigSchema(
                schema_id="service_config",
                name="Service Configuration",
                version="1.0.0",
                schema_definition={
                    "type": "object",
                    "properties": {
                        "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                        "host": {"type": "string"},
                        "log_level": {"type": "string", "enum": ["debug", "info", "warning", "error"]},
                        "max_connections": {"type": "integer", "minimum": 1},
                        "timeout": {"type": "number", "minimum": 0}
                    },
                    "required": ["port", "host"]
                },
                required_fields=["port", "host"],
                default_values={
                    "log_level": "info",
                    "max_connections": 100,
                    "timeout": 30.0
                }
            )

            # Database configuration schema
            database_schema = ConfigSchema(
                schema_id="database_config",
                name="Database Configuration",
                version="1.0.0",
                schema_definition={
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                        "database": {"type": "string"},
                        "username": {"type": "string"},
                        "password": {"type": "string"},
                        "pool_size": {"type": "integer", "minimum": 1},
                        "ssl_mode": {"type": "string", "enum": ["disable", "require", "verify-full"]}
                    },
                    "required": ["host", "port", "database", "username", "password"]
                },
                required_fields=["host", "port", "database", "username", "password"],
                default_values={
                    "pool_size": 10,
                    "ssl_mode": "prefer"
                }
            )

            # Register schemas
            await self.register_schema(service_schema)
            await self.register_schema(database_schema)

            logger.info("Default configuration schemas created")

        except Exception as e:
            logger.error(f"Failed to create default schemas: {e}")

    async def shutdown(self):
        """Shutdown configuration distributor"""
        self._shutdown = True

        # Stop all watchers
        for watcher_id in list(self.watchers.keys()):
            await self.stop_watching(watcher_id)

        logger.info("Configuration distributor shutdown completed")

# Export main classes
__all__ = [
    'ConfigDistributor',
    'ConfigEntry',
    'ConfigSchema',
    'ConfigVersion',
    'ConfigScope',
    'ConfigFormat'
]