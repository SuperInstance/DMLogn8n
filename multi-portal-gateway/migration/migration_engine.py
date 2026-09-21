#!/usr/bin/env python3
"""
DMLogn8n Data Migration Engine
Comprehensive zero-downtime migration orchestration system
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
import uuid
import hashlib
import sys
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from dataclasses import dataclass, asdict
import yaml
from contextlib import asynccontextmanager

# Database connectors
try:
    import asyncpg
    import aioredis
    from motor.motor_asyncio import AsyncIOMotorClient
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
except ImportError as e:
    logging.warning(f"Some database connectors not available: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/migration_engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("migration_engine")

class MigrationStatus(Enum):
    """Migration execution status"""
    PENDING = "pending"
    PLANNING = "planning"
    VALIDATING = "validating"
    BACKING_UP = "backing_up"
    MIGRATING = "migrating"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    PAUSED = "paused"

class MigrationType(Enum):
    """Migration operation types"""
    SCHEMA = "schema"
    DATA = "data"
    INDEX = "index"
    CONFIGURATION = "configuration"
    FULL = "full"

class DatabaseType(Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    REDIS = "redis"
    MONGODB = "mongodb"
    QDRANT = "qdrant"

@dataclass
class MigrationConfig:
    """Migration configuration"""
    migration_id: str
    name: str
    description: str
    migration_type: MigrationType
    source_config: Dict[str, Any]
    target_config: Dict[str, Any]
    tables: List[str]
    batch_size: int = 1000
    max_parallel_workers: int = 4
    zero_downtime: bool = True
    validate_data: bool = True
    create_backup: bool = True
    dry_run: bool = False
    timeout_seconds: int = 3600
    retry_attempts: int = 3
    retry_delay: int = 5
    transformation_rules: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None

@dataclass
class MigrationProgress:
    """Migration progress tracking"""
    migration_id: str
    status: MigrationStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_table: Optional[str] = None
    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    current_batch: int = 0
    total_batches: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metrics is None:
            self.metrics = {}

@dataclass
class TableMigrationPlan:
    """Table-specific migration plan"""
    table_name: str
    source_type: DatabaseType
    target_type: DatabaseType
    row_count: int
    estimated_size_mb: float
    dependencies: List[str]
    transformation_required: bool
    index_rebuild_required: bool
    validation_queries: List[str]
    batch_strategy: str = "timestamp_based"
    key_column: str = "id"

class DatabaseConnector:
    """Abstract database connector"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.db_type = DatabaseType(config.get("type", "postgresql"))

    async def connect(self):
        """Establish database connection"""
        raise NotImplementedError

    async def disconnect(self):
        """Close database connection"""
        raise NotImplementedError

    async def test_connection(self) -> bool:
        """Test database connectivity"""
        raise NotImplementedError

    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get table structure and metadata"""
        raise NotImplementedError

    async def get_row_count(self, table_name: str) -> int:
        """Get total row count for table"""
        raise NotImplementedError

    async def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute a query and return results"""
        raise NotImplementedError

    async def backup_table(self, table_name: str, backup_path: str) -> bool:
        """Create table backup"""
        raise NotImplementedError

    async def restore_table(self, table_name: str, backup_path: str) -> bool:
        """Restore table from backup"""
        raise NotImplementedError

class PostgreSQLConnector(DatabaseConnector):
    """PostgreSQL database connector"""

    async def connect(self):
        try:
            self.connection = await asyncpg.connect(
                host=self.config["host"],
                port=self.config["port"],
                user=self.config["user"],
                password=self.config["password"],
                database=self.config["database"],
                command_timeout=self.config.get("timeout", 60)
            )
            logger.info(f"Connected to PostgreSQL: {self.config['database']}")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    async def disconnect(self):
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from PostgreSQL")

    async def test_connection(self) -> bool:
        try:
            await self.connection.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_name = $1
            ORDER BY ordinal_position
        """
        columns = await self.connection.fetch(query, table_name)

        # Get indexes
        index_query = """
            SELECT
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = $1
        """
        indexes = await self.connection.fetch(index_query, table_name)

        # Get row count
        count = await self.get_row_count(table_name)

        return {
            "columns": [dict(row) for row in columns],
            "indexes": [dict(row) for row in indexes],
            "row_count": count
        }

    async def get_row_count(self, table_name: str) -> int:
        try:
            return await self.connection.fetchval(f"SELECT COUNT(*) FROM {table_name}")
        except Exception as e:
            logger.error(f"Failed to get row count for {table_name}: {e}")
            return 0

    async def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        try:
            if params:
                result = await self.connection.fetch(query, *params.values())
            else:
                result = await self.connection.fetch(query)
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    async def backup_table(self, table_name: str, backup_path: str) -> bool:
        try:
            # Create backup using COPY command
            copy_query = f"COPY {table_name} TO '{backup_path}' WITH CSV HEADER"
            await self.connection.execute(copy_query)
            logger.info(f"Backed up table {table_name} to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup table {table_name}: {e}")
            return False

class RedisConnector(DatabaseConnector):
    """Redis database connector"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.db_type = DatabaseType.REDIS

    async def connect(self):
        try:
            self.connection = await aioredis.from_url(
                f"redis://{self.config['host']}:{self.config['port']}/{self.config.get('db', 0)}",
                password=self.config.get("password"),
                decode_responses=True
            )
            logger.info(f"Connected to Redis: {self.config['host']}:{self.config['port']}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from Redis")

    async def test_connection(self) -> bool:
        try:
            await self.connection.ping()
            return True
        except Exception:
            return False

    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        # Redis doesn't have tables, but we can get key patterns
        try:
            keys = await self.connection.keys(f"{table_name}:*")
            sample_keys = keys[:10]  # Sample first 10 keys

            key_info = {}
            for key in sample_keys:
                key_type = await self.connection.type(key)
                ttl = await self.connection.ttl(key)
                key_info[key] = {"type": key_type, "ttl": ttl}

            return {
                "key_pattern": f"{table_name}:*",
                "total_keys": len(keys),
                "sample_keys": key_info
            }
        except Exception as e:
            logger.error(f"Failed to get Redis info for {table_name}: {e}")
            return {}

    async def get_row_count(self, table_name: str) -> int:
        try:
            keys = await self.connection.keys(f"{table_name}:*")
            return len(keys)
        except Exception:
            return 0

    async def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        # Redis doesn't use SQL queries, but we can execute commands
        try:
            # Parse simple Redis commands
            parts = query.split()
            command = parts[0].upper()

            if command == "KEYS":
                pattern = parts[1] if len(parts) > 1 else "*"
                keys = await self.connection.keys(pattern)
                return [{"key": key} for key in keys]
            elif command == "GET":
                key = parts[1]
                value = await self.connection.get(key)
                return [{"key": key, "value": value}]
            else:
                logger.warning(f"Unsupported Redis command: {command}")
                return []
        except Exception as e:
            logger.error(f"Redis command execution failed: {e}")
            raise

    async def backup_table(self, table_name: str, backup_path: str) -> bool:
        try:
            keys = await self.connection.keys(f"{table_name}:*")
            backup_data = {}

            for key in keys:
                key_type = await self.connection.type(key)
                if key_type == "string":
                    backup_data[key] = await self.connection.get(key)
                elif key_type == "hash":
                    backup_data[key] = await self.connection.hgetall(key)
                elif key_type == "list":
                    backup_data[key] = await self.connection.lrange(key, 0, -1)
                elif key_type == "set":
                    backup_data[key] = await self.connection.smembers(key)

            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)

            logger.info(f"Backed up Redis data for {table_name} to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup Redis data for {table_name}: {e}")
            return False

class MigrationEngine:
    """Main migration orchestration engine"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or "migration_config.yaml"
        self.config = self._load_config()
        self.active_migrations: Dict[str, MigrationProgress] = {}
        self.connectors: Dict[str, DatabaseConnector] = {}
        self.backup_dir = Path("/tmp/migration_backups")
        self.backup_dir.mkdir(exist_ok=True)

        # Import sub-modules
        self.planner = None
        self.transformers = {}
        self.validators = {}
        self.monitoring = None
        self.rollback = None

        self._initialize_modules()

    def _load_config(self) -> Dict[str, Any]:
        """Load migration configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
            else:
                logger.warning(f"Config file {self.config_path} not found, using defaults")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "databases": {
                "source": {
                    "type": "postgresql",
                    "host": "localhost",
                    "port": 5432,
                    "user": "dmlog_user",
                    "password": "password",
                    "database": "dmlog_source"
                },
                "target": {
                    "type": "postgresql",
                    "host": "localhost",
                    "port": 5433,
                    "user": "dmlog_user",
                    "password": "password",
                    "database": "dmlog_target"
                }
            },
            "migration_settings": {
                "default_batch_size": 1000,
                "max_parallel_workers": 4,
                "timeout_seconds": 3600,
                "retry_attempts": 3,
                "retry_delay": 5
            }
        }

    def _initialize_modules(self):
        """Initialize migration sub-modules"""
        try:
            from .planner import MigrationPlanner
            from .monitoring import MigrationMonitor
            from .rollback import RollbackManager

            self.planner = MigrationPlanner()
            self.monitoring = MigrationMonitor()
            self.rollback = RollbackManager()

            # Initialize transformers
            from .transformers.schema_transformer import SchemaTransformer
            from .transformers.data_transformer import DataTransformer
            from .transformers.format_transformer import FormatTransformer

            self.transformers = {
                "schema": SchemaTransformer(),
                "data": DataTransformer(),
                "format": FormatTransformer()
            }

            # Initialize validators
            from .validators.data_validator import DataValidator
            from .validators.schema_validator import SchemaValidator
            from .validators.performance_validator import PerformanceValidator

            self.validators = {
                "data": DataValidator(),
                "schema": SchemaValidator(),
                "performance": PerformanceValidator()
            }

            logger.info("Migration modules initialized successfully")

        except ImportError as e:
            logger.warning(f"Some migration modules not available: {e}")

    def _get_connector(self, config: Dict[str, Any]) -> DatabaseConnector:
        """Get appropriate database connector"""
        db_type = config.get("type", "postgresql").lower()

        connector_key = hashlib.md5(
            json.dumps(config, sort_keys=True).encode()
        ).hexdigest()

        if connector_key not in self.connectors:
            if db_type == "postgresql":
                connector = PostgreSQLConnector(config)
            elif db_type == "redis":
                connector = RedisConnector(config)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")

            self.connectors[connector_key] = connector

        return self.connectors[connector_key]

    async def create_migration_plan(self, config: MigrationConfig) -> List[TableMigrationPlan]:
        """Create detailed migration plan"""
        logger.info(f"Creating migration plan for {config.name}")

        if not self.planner:
            # Fallback simple planning
            return await self._create_simple_plan(config)

        return await self.planner.create_plan(config)

    async def _create_simple_plan(self, config: MigrationConfig) -> List[TableMigrationPlan]:
        """Create simple migration plan without planner module"""
        plans = []
        source_connector = self._get_connector(config.source_config)

        await source_connector.connect()

        try:
            for table_name in config.tables:
                table_info = await source_connector.get_table_info(table_name)
                row_count = table_info.get("row_count", 0)

                # Estimate size (rough calculation)
                estimated_size = row_count * 0.001  # Assume 1KB per row

                plan = TableMigrationPlan(
                    table_name=table_name,
                    source_type=DatabaseType(config.source_config["type"]),
                    target_type=DatabaseType(config.target_config["type"]),
                    row_count=row_count,
                    estimated_size_mb=estimated_size,
                    dependencies=[],
                    transformation_required=config.source_config["type"] != config.target_config["type"],
                    index_rebuild_required=True,
                    validation_queries=[f"SELECT COUNT(*) FROM {table_name}"],
                    batch_strategy="id_based"
                )
                plans.append(plan)

        finally:
            await source_connector.disconnect()

        return plans

    async def execute_migration(self, config: MigrationConfig) -> MigrationProgress:
        """Execute migration with full orchestration"""
        migration_id = config.migration_id
        logger.info(f"Starting migration: {migration_id}")

        # Initialize progress tracking
        progress = MigrationProgress(
            migration_id=migration_id,
            status=MigrationStatus.PENDING,
            start_time=datetime.now(timezone.utc)
        )
        self.active_migrations[migration_id] = progress

        try:
            # Phase 1: Planning
            progress.status = MigrationStatus.PLANNING
            await self._update_progress(progress)

            plans = await self.create_migration_plan(config)
            logger.info(f"Created migration plan with {len(plans)} tables")

            # Phase 2: Validation
            if config.validate_data:
                progress.status = MigrationStatus.VALIDATING
                await self._update_progress(progress)
                await self._validate_migration_config(config, plans)

            # Phase 3: Backup
            if config.create_backup and not config.dry_run:
                progress.status = MigrationStatus.BACKING_UP
                await self._update_progress(progress)
                await self._create_backups(config, plans)

            # Phase 4: Migration
            progress.status = MigrationStatus.MIGRATING
            await self._update_progress(progress)

            if config.dry_run:
                logger.info("DRY RUN: Would migrate the following tables:")
                for plan in plans:
                    logger.info(f"  - {plan.table_name}: {plan.row_count} rows")
            else:
                await self._execute_migration_steps(config, plans, progress)

            # Phase 5: Verification
            progress.status = MigrationStatus.VERIFYING
            await self._update_progress(progress)
            await self._verify_migration(config, plans)

            # Complete
            progress.status = MigrationStatus.COMPLETED
            progress.end_time = datetime.now(timezone.utc)
            await self._update_progress(progress)

            logger.info(f"Migration {migration_id} completed successfully")
            return progress

        except Exception as e:
            logger.error(f"Migration {migration_id} failed: {e}")
            progress.status = MigrationStatus.FAILED
            progress.errors.append(str(e))
            progress.end_time = datetime.now(timezone.utc)
            await self._update_progress(progress)

            # Attempt rollback if configured
            if config.create_backup and not config.dry_run:
                logger.info(f"Attempting rollback for migration {migration_id}")
                await self._rollback_migration(config, progress)

            return progress

    async def _validate_migration_config(self, config: MigrationConfig, plans: List[TableMigrationPlan]):
        """Validate migration configuration and prerequisites"""
        logger.info("Validating migration configuration")

        # Test database connections
        source_connector = self._get_connector(config.source_config)
        target_connector = self._get_connector(config.target_config)

        await source_connector.connect()
        await target_connector.connect()

        try:
            # Test connectivity
            if not await source_connector.test_connection():
                raise Exception("Source database connection failed")
            if not await target_connector.test_connection():
                raise Exception("Target database connection failed")

            # Validate tables exist in source
            for plan in plans:
                source_info = await source_connector.get_table_info(plan.table_name)
                if not source_info:
                    raise Exception(f"Source table {plan.table_name} not found")

            logger.info("Migration configuration validation passed")

        finally:
            await source_connector.disconnect()
            await target_connector.disconnect()

    async def _create_backups(self, config: MigrationConfig, plans: List[TableMigrationPlan]):
        """Create backups of source data"""
        logger.info("Creating migration backups")

        source_connector = self._get_connector(config.source_config)
        await source_connector.connect()

        try:
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for plan in plans:
                backup_path = self.backup_dir / f"{plan.table_name}_{backup_timestamp}.csv"
                success = await source_connector.backup_table(plan.table_name, str(backup_path))

                if not success:
                    raise Exception(f"Failed to backup table {plan.table_name}")

                logger.info(f"Backed up {plan.table_name} to {backup_path}")

        finally:
            await source_connector.disconnect()

    async def _execute_migration_steps(self, config: MigrationConfig, plans: List[TableMigrationPlan], progress: MigrationProgress):
        """Execute the actual migration steps"""
        logger.info("Executing migration steps")

        source_connector = self._get_connector(config.source_config)
        target_connector = self._get_connector(config.target_config)

        await source_connector.connect()
        await target_connector.connect()

        try:
            for plan in plans:
                progress.current_table = plan.table_name
                progress.total_records = plan.row_count
                progress.processed_records = 0
                progress.failed_records = 0
                await self._update_progress(progress)

                await self._migrate_table(config, plan, source_connector, target_connector, progress)

                logger.info(f"Completed migration of {plan.table_name}")

        finally:
            await source_connector.disconnect()
            await target_connector.disconnect()

    async def _migrate_table(self, config: MigrationConfig, plan: TableMigrationPlan,
                           source_connector: DatabaseConnector, target_connector: DatabaseConnector,
                           progress: MigrationProgress):
        """Migrate a single table"""
        table_name = plan.table_name
        batch_size = config.batch_size

        logger.info(f"Migrating table {table_name} ({plan.row_count} rows)")

        # Calculate total batches
        progress.total_batches = (plan.row_count + batch_size - 1) // batch_size
        progress.current_batch = 0

        # Migrate in batches
        offset = 0
        while offset < plan.row_count:
            progress.current_batch += 1

            try:
                # Fetch batch from source
                batch_query = f"SELECT * FROM {table_name} ORDER BY {plan.key_column} LIMIT {batch_size} OFFSET {offset}"
                batch_data = await source_connector.execute_query(batch_query)

                if not batch_data:
                    break

                # Transform data if needed
                if plan.transformation_required and config.transformation_rules:
                    batch_data = await self._transform_data(batch_data, config.transformation_rules)

                # Insert into target
                await self._insert_batch(target_connector, table_name, batch_data)

                progress.processed_records += len(batch_data)
                await self._update_progress(progress)

                logger.debug(f"Migrated batch {progress.current_batch}/{progress.total_batches} for {table_name}")

                offset += batch_size

            except Exception as e:
                logger.error(f"Failed to migrate batch for {table_name}: {e}")
                progress.failed_records += batch_size
                progress.errors.append(f"Batch {progress.current_batch} failed: {str(e)}")

                if len(progress.errors) > config.retry_attempts:
                    raise Exception(f"Too many failed batches for {table_name}")

                # Retry logic
                await asyncio.sleep(config.retry_delay)

    async def _transform_data(self, data: List[Dict], rules: Dict[str, Any]) -> List[Dict]:
        """Transform data according to rules"""
        if not data:
            return data

        # Apply transformations based on rules
        transformed_data = []

        for record in data:
            transformed_record = record.copy()

            # Apply field transformations
            if "field_mappings" in rules:
                for old_field, new_field in rules["field_mappings"].items():
                    if old_field in transformed_record:
                        transformed_record[new_field] = transformed_record.pop(old_field)

            # Apply data type conversions
            if "type_conversions" in rules:
                for field, target_type in rules["type_conversions"].items():
                    if field in transformed_record:
                        try:
                            if target_type == "int":
                                transformed_record[field] = int(transformed_record[field])
                            elif target_type == "float":
                                transformed_record[field] = float(transformed_record[field])
                            elif target_type == "str":
                                transformed_record[field] = str(transformed_record[field])
                            elif target_type == "bool":
                                transformed_record[field] = bool(transformed_record[field])
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Failed to convert {field} to {target_type}: {e}")

            # Apply value transformations
            if "value_transformations" in rules:
                for field, transform_func in rules["value_transformations"].items():
                    if field in transformed_record:
                        # Simple transformations - in real implementation, this would be more sophisticated
                        if transform_func == "upper":
                            transformed_record[field] = str(transformed_record[field]).upper()
                        elif transform_func == "lower":
                            transformed_record[field] = str(transformed_record[field]).lower()
                        elif transform_func == "trim":
                            transformed_record[field] = str(transformed_record[field]).strip()

            transformed_data.append(transformed_record)

        return transformed_data

    async def _insert_batch(self, connector: DatabaseConnector, table_name: str, batch_data: List[Dict]):
        """Insert batch data into target table"""
        if not batch_data:
            return

        # For PostgreSQL, we'd use COPY for better performance
        # This is a simplified implementation
        for record in batch_data:
            columns = list(record.keys())
            values = list(record.values())
            placeholders = [f"${i+1}" for i in range(len(values))]

            query = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT DO NOTHING
            """

            await connector.execute_query(query, dict(zip(columns, values)))

    async def _verify_migration(self, config: MigrationConfig, plans: List[TableMigrationPlan]):
        """Verify migration success"""
        logger.info("Verifying migration results")

        source_connector = self._get_connector(config.source_config)
        target_connector = self._get_connector(config.target_config)

        await source_connector.connect()
        await target_connector.connect()

        try:
            for plan in plans:
                # Compare row counts
                source_count = await source_connector.get_row_count(plan.table_name)
                target_count = await target_connector.get_row_count(plan.table_name)

                if source_count != target_count:
                    raise Exception(f"Row count mismatch for {plan.table_name}: source={source_count}, target={target_count}")

                # Run validation queries
                for validation_query in plan.validation_queries:
                    try:
                        source_result = await source_connector.execute_query(validation_query)
                        target_result = await target_connector.execute_query(validation_query)

                        if source_result != target_result:
                            logger.warning(f"Validation query mismatch for {plan.table_name}: {validation_query}")

                    except Exception as e:
                        logger.warning(f"Validation query failed for {plan.table_name}: {e}")

                logger.info(f"Verification passed for {plan.table_name}")

        finally:
            await source_connector.disconnect()
            await target_connector.disconnect()

    async def _rollback_migration(self, config: MigrationConfig, progress: MigrationProgress):
        """Rollback failed migration"""
        if not self.rollback:
            logger.warning("Rollback module not available, skipping rollback")
            return

        try:
            await self.rollback.execute_rollback(config, progress)
            progress.status = MigrationStatus.ROLLED_BACK
            await self._update_progress(progress)
            logger.info(f"Rollback completed for migration {config.migration_id}")
        except Exception as e:
            logger.error(f"Rollback failed for migration {config.migration_id}: {e}")

    async def _update_progress(self, progress: MigrationProgress):
        """Update migration progress"""
        if self.monitoring:
            await self.monitoring.update_progress(progress)

        # Log progress
        progress_pct = 0
        if progress.total_records > 0:
            progress_pct = (progress.processed_records / progress.total_records) * 100

        logger.info(f"Migration {progress.migration_id} - {progress.status.value}: "
                   f"{progress.processed_records}/{progress.total_records} ({progress_pct:.1f}%)")

    async def get_migration_status(self, migration_id: str) -> Optional[MigrationProgress]:
        """Get migration status"""
        return self.active_migrations.get(migration_id)

    async def list_active_migrations(self) -> List[MigrationProgress]:
        """List all active migrations"""
        return list(self.active_migrations.values())

    async def cancel_migration(self, migration_id: str) -> bool:
        """Cancel active migration"""
        if migration_id in self.active_migrations:
            progress = self.active_migrations[migration_id]
            if progress.status in [MigrationStatus.PENDING, MigrationStatus.PLANNING, MigrationStatus.MIGRATING]:
                progress.status = MigrationStatus.FAILED
                progress.errors.append("Migration cancelled by user")
                await self._update_progress(progress)
                return True
        return False

    async def cleanup(self):
        """Cleanup resources"""
        for connector in self.connectors.values():
            try:
                await connector.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting connector: {e}")

        self.connectors.clear()
        logger.info("Migration engine cleanup completed")

# CLI interface
async def main():
    """Command line interface"""
    import argparse

    parser = argparse.ArgumentParser(description="DMLogn8n Migration Engine")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run")
    parser.add_argument("--migration-id", help="Specific migration ID")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    parser.add_argument("--list", action="store_true", help="List active migrations")

    args = parser.parse_args()

    engine = MigrationEngine(args.config)

    try:
        if args.status and args.migration_id:
            progress = await engine.get_migration_status(args.migration_id)
            if progress:
                print(json.dumps(asdict(progress), indent=2, default=str))
            else:
                print(f"Migration {args.migration_id} not found")

        elif args.list:
            migrations = await engine.list_active_migrations()
            for migration in migrations:
                print(f"{migration.migration_id}: {migration.status.value}")

        else:
            # Create sample migration config for demo
            config = MigrationConfig(
                migration_id=str(uuid.uuid4())[:8],
                name="Sample Migration",
                description="Sample data migration",
                migration_type=MigrationType.DATA,
                source_config={
                    "type": "postgresql",
                    "host": "localhost",
                    "port": 5432,
                    "user": "dmlog_user",
                    "password": "password",
                    "database": "dmlog_source"
                },
                target_config={
                    "type": "postgresql",
                    "host": "localhost",
                    "port": 5433,
                    "user": "dmlog_user",
                    "password": "password",
                    "database": "dmlog_target"
                },
                tables=["characters", "campaigns", "sessions"],
                dry_run=args.dry_run
            )

            progress = await engine.execute_migration(config)
            print(f"Migration completed with status: {progress.status.value}")

            if progress.errors:
                print("Errors:")
                for error in progress.errors:
                    print(f"  - {error}")

    finally:
        await engine.cleanup()

if __name__ == "__main__":
    asyncio.run(main())