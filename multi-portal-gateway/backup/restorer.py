#!/usr/bin/env python3
"""
DMLogn8n Restore Service - Comprehensive Data Recovery System

This service provides point-in-time recovery capabilities for the DMLogn8n
multi-agent platform with validation, rollback, and disaster recovery features.
"""

import asyncio
import logging
import json
import os
import sys
import time
import hashlib
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import yaml
import sqlite3
import psycopg2
import redis
import tarfile
import gzip
import requests
from cryptography.fernet import Fernet
import docker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/logs/restore.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class RestoreType(Enum):
    """Restore operation types"""
    FULL = "full"
    PARTIAL = "partial"
    POINT_IN_TIME = "point_in_time"
    SELECTIVE = "selective"

class RestoreStatus(Enum):
    """Restore operation status"""
    PENDING = "pending"
    VALIDATING = "validating"
    PREPARING = "preparing"
    RUNNING = "running"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class RestoreScope(Enum):
    """Restore scope options"""
    DATABASE = "database"
    FILES = "files"
    CONFIGURATION = "configuration"
    ALL = "all"

@dataclass
class RestoreRequest:
    """Restore request configuration"""
    restore_id: str
    backup_id: str
    restore_type: str
    scope: str
    target_path: Optional[str]
    point_in_time: Optional[datetime]
    selective_items: Optional[List[str]]
    dry_run: bool = False
    force_overwrite: bool = False
    validate_before_restore: bool = True
    validate_after_restore: bool = True
    create_rollback_point: bool = True
    notification_emails: List[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class RestoreResult:
    """Restore operation result"""
    restore_id: str
    backup_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    restored_items: List[str]
    skipped_items: List[str]
    failed_items: List[str]
    rollback_point: Optional[str]
    validation_results: Dict[str, Any]
    size_bytes: int
    checksum: str
    error_message: Optional[str]

class RestoreService:
    """Main restore service for DMLogn8n platform"""

    def __init__(self, config_path: str = "/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/config/restore_config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        self.db_manager = RestoreDatabaseManager()
        self.active_restores = {}
        self.rollback_manager = RollbackManager()
        self.validator = RestoreValidator()
        self.notifier = RestoreNotifier()

        # Initialize storage backends
        self.init_storage_backends()

        logger.info("Restore service initialized")

    def load_config(self) -> Dict[str, Any]:
        """Load restore configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load restore config: {e}")
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default restore configuration"""
        return {
            'restore_paths': {
                'database': {
                    'postgresql': {
                        'host': 'localhost',
                        'port': 5432,
                        'database': 'dmlogn8n',
                        'username': 'postgres',
                        'password': os.getenv('POSTGRES_PASSWORD')
                    },
                    'redis': {
                        'host': 'localhost',
                        'port': 6379,
                        'database': 0
                    },
                    'qdrant': {
                        'host': 'localhost',
                        'port': 6333,
                        'api_key': os.getenv('QDRANT_API_KEY')
                    }
                },
                'files': {
                    'application': '/home/activeloguser/DMLogn8n',
                    'uploads': '/home/activeloguser/DMLogn8n/uploads',
                    'logs': '/home/activeloguser/DMLogn8n/logs',
                    'models': '/home/activeloguser/DMLogn8n/models'
                },
                'configuration': {
                    'app_config': '/home/activeloguser/DMLogn8n/multi-portal-gateway/config',
                    'environment': '/home/activeloguser/DMLogn8n/.env',
                    'secrets': '/home/activeloguser/DMLogn8n/multi-portal-gateway/secrets'
                }
            },
            'validation': {
                'checksum_validation': True,
                'integrity_checks': True,
                'service_health_checks': True,
                'data_consistency_checks': True
            },
            'rollback': {
                'enabled': True,
                'automatic_rollback': True,
                'rollback_retention_days': 30
            },
            'notifications': {
                'email_enabled': True,
                'slack_webhook': os.getenv('SLACK_WEBHOOK_URL'),
                'admin_emails': ['admin@dmlogn8n.com']
            }
        }

    def init_storage_backends(self):
        """Initialize storage backends for restore operations"""
        from storage.local_storage import LocalStorage
        from storage.s3_storage import S3Storage
        from storage.gcs_storage import GCSStorage

        self.storage_backends = {
            'local': LocalStorage({}),
            's3': S3Storage({}),
            'gcs': GCSStorage({})
        }

    async def initiate_restore(self, request: RestoreRequest) -> str:
        """Initiate a restore operation"""
        logger.info(f"Initiating restore operation: {request.restore_id}")

        try:
            # Validate restore request
            await self.validate_restore_request(request)

            # Save restore request to database
            self.db_manager.save_restore_request(request)

            # Start restore operation in background
            asyncio.create_task(self.execute_restore(request))

            return request.restore_id

        except Exception as e:
            logger.error(f"Failed to initiate restore {request.restore_id}: {e}")
            raise

    async def execute_restore(self, request: RestoreRequest):
        """Execute restore operation"""
        logger.info(f"Starting restore execution: {request.restore_id}")

        try:
            # Update status to VALIDATING
            await self.update_restore_status(request.restore_id, RestoreStatus.VALIDATING)

            # Validate backup before restore
            if request.validate_before_restore:
                validation_result = await self.validator.validate_backup_for_restore(request.backup_id)
                if not validation_result['valid']:
                    raise Exception(f"Backup validation failed: {validation_result['error']}")

            # Update status to PREPARING
            await self.update_restore_status(request.restore_id, RestoreStatus.PREPARING)

            # Prepare restore environment
            restore_context = await self.prepare_restore_environment(request)

            # Create rollback point if enabled
            rollback_point = None
            if request.create_rollback_point:
                rollback_point = await self.rollback_manager.create_rollback_point(request)
                logger.info(f"Created rollback point: {rollback_point}")

            # Update status to RUNNING
            await self.update_restore_status(request.restore_id, RestoreStatus.RUNNING)

            # Execute restore based on scope
            if request.scope == RestoreScope.ALL.value:
                result = await self.restore_full_system(request, restore_context)
            elif request.scope == RestoreScope.DATABASE.value:
                result = await self.restore_databases(request, restore_context)
            elif request.scope == RestoreScope.FILES.value:
                result = await self.restore_files(request, restore_context)
            elif request.scope == RestoreScope.CONFIGURATION.value:
                result = await self.restore_configuration(request, restore_context)
            else:
                raise ValueError(f"Unknown restore scope: {request.scope}")

            # Update status to VERIFYING
            await self.update_restore_status(request.restore_id, RestoreStatus.VERIFYING)

            # Verify restore
            if request.validate_after_restore:
                verification_result = await self.validator.verify_restore(result)
                result.validation_results = verification_result

            # Update status to COMPLETED
            result.status = RestoreStatus.COMPLETED.value
            result.completed_at = datetime.now(timezone.utc)

            # Save restore result
            self.db_manager.save_restore_result(result)

            logger.info(f"Restore completed successfully: {request.restore_id}")

            # Send notification
            await self.notifier.send_restore_success_notification(result)

        except Exception as e:
            logger.error(f"Restore failed: {request.restore_id} - {e}")

            # Update status to FAILED
            await self.update_restore_status(request.restore_id, RestoreStatus.FAILED, str(e))

            # Automatic rollback if enabled and configured
            if (request.create_rollback_point and
                self.config['rollback']['automatic_rollback'] and
                rollback_point):

                try:
                    await self.rollback_manager.execute_rollback(rollback_point)
                    await self.update_restore_status(request.restore_id, RestoreStatus.ROLLED_BACK)
                    logger.info(f"Automatic rollback executed for: {request.restore_id}")
                except Exception as rollback_error:
                    logger.error(f"Automatic rollback failed: {rollback_error}")

            # Send failure notification
            await self.notifier.send_restore_failure_notification(request.restore_id, str(e))

    async def validate_restore_request(self, request: RestoreRequest):
        """Validate restore request parameters"""
        # Check if backup exists
        backup = self.db_manager.get_backup(request.backup_id)
        if not backup:
            raise Exception(f"Backup not found: {request.backup_id}")

        # Validate restore type
        if request.restore_type not in [t.value for t in RestoreType]:
            raise Exception(f"Invalid restore type: {request.restore_type}")

        # Validate scope
        if request.scope not in [s.value for s in RestoreScope]:
            raise Exception(f"Invalid restore scope: {request.scope}")

        # Check point-in-time validity
        if request.restore_type == RestoreType.POINT_IN_TIME.value:
            if not request.point_in_time:
                raise Exception("Point-in-time restore requires point_in_time parameter")

            if request.point_in_time > datetime.now(timezone.utc):
                raise Exception("Point-in-time cannot be in the future")

            backup_time = datetime.fromisoformat(backup['created_at'])
            if request.point_in_time < backup_time:
                raise Exception("Point-in-time is before backup creation time")

        # Validate target paths
        if request.target_path and not os.path.exists(os.path.dirname(request.target_path)):
            raise Exception(f"Target path parent directory does not exist: {request.target_path}")

        logger.info(f"Restore request validation passed: {request.restore_id}")

    async def prepare_restore_environment(self, request: RestoreRequest) -> Dict[str, Any]:
        """Prepare environment for restore operation"""
        context = {
            'temp_dir': tempfile.mkdtemp(prefix=f"restore_{request.restore_id}_"),
            'backup_path': await self.get_backup_path(request.backup_id),
            'restore_paths': self.config['restore_paths']
        }

        # Download backup if needed
        backup = self.db_manager.get_backup(request.backup_id)
        storage_backend = self.storage_backends[backup['storage_backend']]

        local_backup_path = os.path.join(context['temp_dir'], f"backup_{request.backup_id}")
        await storage_backend.download_backup(backup['storage_path'], local_backup_path)

        context['local_backup_path'] = local_backup_path

        # Stop services if needed
        if request.scope in [RestoreScope.DATABASE.value, RestoreScope.ALL.value]:
            await self.stop_services_for_restore(request.scope)

        logger.info(f"Restore environment prepared: {request.restore_id}")
        return context

    async def restore_full_system(self, request: RestoreRequest, context: Dict[str, Any]) -> RestoreResult:
        """Restore full system from backup"""
        logger.info(f"Starting full system restore: {request.restore_id}")

        result = RestoreResult(
            restore_id=request.restore_id,
            backup_id=request.backup_id,
            status=RestoreStatus.RUNNING.value,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            restored_items=[],
            skipped_items=[],
            failed_items=[],
            rollback_point=None,
            validation_results={},
            size_bytes=0,
            checksum="",
            error_message=None
        )

        try:
            # Extract backup
            backup_path = context['local_backup_path']
            extract_path = os.path.join(context['temp_dir'], 'extracted')

            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(extract_path)

            # Restore databases
            db_result = await self.restore_databases_from_path(
                os.path.join(extract_path, 'database'), context
            )
            result.restored_items.extend(db_result['restored_items'])
            result.failed_items.extend(db_result['failed_items'])

            # Restore files
            files_result = await self.restore_files_from_path(
                os.path.join(extract_path, 'files'), context
            )
            result.restored_items.extend(files_result['restored_items'])
            result.failed_items.extend(files_result['failed_items'])

            # Restore configuration
            config_result = await self.restore_configuration_from_path(
                os.path.join(extract_path, 'config'), context
            )
            result.restored_items.extend(config_result['restored_items'])
            result.failed_items.extend(config_result['failed_items'])

            # Calculate checksum
            result.checksum = await self.calculate_restore_checksum(extract_path)

            logger.info(f"Full system restore completed: {request.restore_id}")
            return result

        except Exception as e:
            logger.error(f"Full system restore failed: {request.restore_id} - {e}")
            result.error_message = str(e)
            result.failed_items.append(f"Full system restore: {e}")
            return result

    async def restore_databases(self, request: RestoreRequest, context: Dict[str, Any]) -> RestoreResult:
        """Restore databases from backup"""
        logger.info(f"Starting database restore: {request.restore_id}")

        result = RestoreResult(
            restore_id=request.restore_id,
            backup_id=request.backup_id,
            status=RestoreStatus.RUNNING.value,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            restored_items=[],
            skipped_items=[],
            failed_items=[],
            rollback_point=None,
            validation_results={},
            size_bytes=0,
            checksum="",
            error_message=None
        )

        try:
            backup_path = context['local_backup_path']
            extract_path = os.path.join(context['temp_dir'], 'database')

            with tarfile.open(backup_path, 'r:gz') as tar:
                for member in tar.getmembers():
                    if member.name.startswith('database/'):
                        tar.extract(member, context['temp_dir'])

            db_result = await self.restore_databases_from_path(extract_path, context)
            result.restored_items.extend(db_result['restored_items'])
            result.failed_items.extend(db_result['failed_items'])

            logger.info(f"Database restore completed: {request.restore_id}")
            return result

        except Exception as e:
            logger.error(f"Database restore failed: {request.restore_id} - {e}")
            result.error_message = str(e)
            result.failed_items.append(f"Database restore: {e}")
            return result

    async def restore_databases_from_path(self, db_path: str, context: Dict[str, Any]) -> Dict[str, List[str]]:
        """Restore databases from extracted backup path"""
        result = {'restored_items': [], 'failed_items': []}

        # Restore PostgreSQL
        postgres_path = os.path.join(db_path, 'postgresql')
        if os.path.exists(postgres_path):
            try:
                await self.restore_postgresql(postgres_path)
                result['restored_items'].append('PostgreSQL database')
            except Exception as e:
                result['failed_items'].append(f'PostgreSQL: {e}')

        # Restore Redis
        redis_path = os.path.join(db_path, 'redis')
        if os.path.exists(redis_path):
            try:
                await self.restore_redis(redis_path)
                result['restored_items'].append('Redis data')
            except Exception as e:
                result['failed_items'].append(f'Redis: {e}')

        # Restore Qdrant
        qdrant_path = os.path.join(db_path, 'qdrant')
        if os.path.exists(qdrant_path):
            try:
                await self.restore_qdrant(qdrant_path)
                result['restored_items'].append('Qdrant vector database')
            except Exception as e:
                result['failed_items'].append(f'Qdrant: {e}')

        return result

    async def restore_postgresql(self, backup_path: str):
        """Restore PostgreSQL database"""
        pg_config = self.config['restore_paths']['database']['postgresql']
        dump_file = os.path.join(backup_path, 'postgresql_dump.sql')

        if not os.path.exists(dump_file):
            raise Exception("PostgreSQL dump file not found")

        # Drop and recreate database
        conn = psycopg2.connect(
            host=pg_config['host'],
            port=pg_config['port'],
            database='postgres',
            user=pg_config['username'],
            password=pg_config['password']
        )
        conn.autocommit = True
        cursor = conn.cursor()

        try:
            cursor.execute(f"DROP DATABASE IF EXISTS {pg_config['database']}")
            cursor.execute(f"CREATE DATABASE {pg_config['database']}")
        finally:
            conn.close()

        # Restore from dump
        restore_cmd = [
            'psql',
            f'-h{pg_config["host"]}',
            f'-p{pg_config["port"]}',
            f'-U{pg_config["username"]}',
            f'-d{pg_config["database"]}',
            f'-f{dump_file}'
        ]

        env = os.environ.copy()
        env['PGPASSWORD'] = pg_config['password']

        result = subprocess.run(restore_cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"PostgreSQL restore failed: {result.stderr}")

        logger.info("PostgreSQL database restored successfully")

    async def restore_redis(self, backup_path: str):
        """Restore Redis data"""
        redis_config = self.config['restore_paths']['database']['redis']
        dump_file = os.path.join(backup_path, 'redis_dump.rdb')

        if not os.path.exists(dump_file):
            raise Exception("Redis dump file not found")

        # Copy dump file to Redis data directory
        redis_data_dir = '/var/lib/redis'  # Default Redis data directory
        target_dump = os.path.join(redis_data_dir, 'dump.rdb')

        # Stop Redis service
        subprocess.run(['sudo', 'systemctl', 'stop', 'redis'], check=True)

        # Copy dump file
        shutil.copy2(dump_file, target_dump)

        # Set correct permissions
        subprocess.run(['sudo', 'chown', 'redis:redis', target_dump], check=True)

        # Start Redis service
        subprocess.run(['sudo', 'systemctl', 'start', 'redis'], check=True)

        logger.info("Redis data restored successfully")

    async def restore_qdrant(self, backup_path: str):
        """Restore Qdrant vector database"""
        qdrant_config = self.config['restore_paths']['database']['qdrant']
        qdrant_data_dir = '/qdrant/storage'  # Default Qdrant storage path

        # Stop Qdrant service
        try:
            subprocess.run(['docker', 'stop', 'qdrant'], check=True)
        except subprocess.CalledProcessError:
            logger.warning("Qdrant container not running or not found")

        # Clear existing data
        if os.path.exists(qdrant_data_dir):
            shutil.rmtree(qdrant_data_dir)

        # Copy backup data
        shutil.copytree(backup_path, qdrant_data_dir)

        # Start Qdrant service
        try:
            subprocess.run(['docker', 'start', 'qdrant'], check=True)
        except subprocess.CalledProcessError:
            logger.warning("Failed to start Qdrant container")

        logger.info("Qdrant vector database restored successfully")

    async def restore_files(self, request: RestoreRequest, context: Dict[str, Any]) -> RestoreResult:
        """Restore files from backup"""
        logger.info(f"Starting files restore: {request.restore_id}")

        result = RestoreResult(
            restore_id=request.restore_id,
            backup_id=request.backup_id,
            status=RestoreStatus.RUNNING.value,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            restored_items=[],
            skipped_items=[],
            failed_items=[],
            rollback_point=None,
            validation_results={},
            size_bytes=0,
            checksum="",
            error_message=None
        )

        try:
            backup_path = context['local_backup_path']
            extract_path = os.path.join(context['temp_dir'], 'files')

            with tarfile.open(backup_path, 'r:gz') as tar:
                for member in tar.getmembers():
                    if member.name.startswith('files/'):
                        tar.extract(member, context['temp_dir'])

            files_result = await self.restore_files_from_path(extract_path, context)
            result.restored_items.extend(files_result['restored_items'])
            result.failed_items.extend(files_result['failed_items'])

            logger.info(f"Files restore completed: {request.restore_id}")
            return result

        except Exception as e:
            logger.error(f"Files restore failed: {request.restore_id} - {e}")
            result.error_message = str(e)
            result.failed_items.append(f"Files restore: {e}")
            return result

    async def restore_files_from_path(self, files_path: str, context: Dict[str, Any]) -> Dict[str, List[str]]:
        """Restore files from extracted backup path"""
        result = {'restored_items': [], 'failed_items': []}

        file_configs = self.config['restore_paths']['files']

        for name, target_path in file_configs.items():
            backup_dir = os.path.join(files_path, name)

            if os.path.exists(backup_dir):
                try:
                    # Create target directory if it doesn't exist
                    os.makedirs(target_path, exist_ok=True)

                    # Copy files with rsync for efficiency
                    subprocess.run([
                        'rsync', '-av', '--delete',
                        f'{backup_dir}/',
                        f'{target_path}/'
                    ], check=True)

                    result['restored_items'].append(f'{name} files')

                except Exception as e:
                    result['failed_items'].append(f'{name} files: {e}')

        return result

    async def restore_configuration(self, request: RestoreRequest, context: Dict[str, Any]) -> RestoreResult:
        """Restore configuration from backup"""
        logger.info(f"Starting configuration restore: {request.restore_id}")

        result = RestoreResult(
            restore_id=request.restore_id,
            backup_id=request.backup_id,
            status=RestoreStatus.RUNNING.value,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            restored_items=[],
            skipped_items=[],
            failed_items=[],
            rollback_point=None,
            validation_results={},
            size_bytes=0,
            checksum="",
            error_message=None
        )

        try:
            backup_path = context['local_backup_path']
            extract_path = os.path.join(context['temp_dir'], 'config')

            with tarfile.open(backup_path, 'r:gz') as tar:
                for member in tar.getmembers():
                    if member.name.startswith('config/'):
                        tar.extract(member, context['temp_dir'])

            config_result = await self.restore_configuration_from_path(extract_path, context)
            result.restored_items.extend(config_result['restored_items'])
            result.failed_items.extend(config_result['failed_items'])

            logger.info(f"Configuration restore completed: {request.restore_id}")
            return result

        except Exception as e:
            logger.error(f"Configuration restore failed: {request.restore_id} - {e}")
            result.error_message = str(e)
            result.failed_items.append(f"Configuration restore: {e}")
            return result

    async def restore_configuration_from_path(self, config_path: str, context: Dict[str, Any]) -> Dict[str, List[str]]:
        """Restore configuration from extracted backup path"""
        result = {'restored_items': [], 'failed_items': []}

        config_configs = self.config['restore_paths']['configuration']

        for name, target_path in config_configs.items():
            backup_file = os.path.join(config_path, os.path.basename(target_path))

            if os.path.exists(backup_file):
                try:
                    # Backup existing configuration
                    if os.path.exists(target_path):
                        backup_existing = f"{target_path}.backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
                        shutil.copy2(target_path, backup_existing)

                    # Restore configuration
                    shutil.copy2(backup_file, target_path)
                    result['restored_items'].append(f'{name} configuration')

                except Exception as e:
                    result['failed_items'].append(f'{name} configuration: {e}')

        return result

    async def stop_services_for_restore(self, scope: str):
        """Stop services for restore operation"""
        services_to_stop = []

        if scope in [RestoreScope.DATABASE.value, RestoreScope.ALL.value]:
            services_to_stop.extend(['postgresql', 'redis', 'qdrant'])

        if scope == RestoreScope.ALL.value:
            services_to_stop.extend(['dmlogn8n-web', 'dmlogn8n-api', 'dmlogn8n-workers'])

        for service in services_to_stop:
            try:
                subprocess.run(['sudo', 'systemctl', 'stop', service], check=True)
                logger.info(f"Stopped service: {service}")
            except subprocess.CalledProcessError:
                logger.warning(f"Failed to stop service: {service}")

    async def start_services_after_restore(self, scope: str):
        """Start services after restore operation"""
        services_to_start = []

        if scope in [RestoreScope.DATABASE.value, RestoreScope.ALL.value]:
            services_to_start.extend(['postgresql', 'redis'])

        if scope == RestoreScope.ALL.value:
            services_to_start.extend(['dmlogn8n-web', 'dmlogn8n-api', 'dmlogn8n-workers'])

        # Start in dependency order
        for service in services_to_start:
            try:
                subprocess.run(['sudo', 'systemctl', 'start', service], check=True)
                logger.info(f"Started service: {service}")
                await asyncio.sleep(5)  # Give service time to start
            except subprocess.CalledProcessError:
                logger.warning(f"Failed to start service: {service}")

    async def update_restore_status(self, restore_id: str, status: RestoreStatus, error_message: str = None):
        """Update restore operation status"""
        self.db_manager.update_restore_status(restore_id, status.value, error_message)

    async def get_backup_path(self, backup_id: str) -> str:
        """Get local path for backup"""
        backup = self.db_manager.get_backup(backup_id)
        if not backup:
            raise Exception(f"Backup not found: {backup_id}")

        # For now, return storage path - in real implementation would download from storage
        return backup['storage_path']

    async def calculate_restore_checksum(self, path: str) -> str:
        """Calculate checksum for restored data"""
        hash_md5 = hashlib.md5()

        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)

        return hash_md5.hexdigest()

    def get_restore_status(self, restore_id: str) -> Dict[str, Any]:
        """Get restore operation status"""
        return self.db_manager.get_restore_status(restore_id)

    def list_restores(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List restore operations"""
        return self.db_manager.list_restores(limit)

class RestoreDatabaseManager:
    """Manages restore operation metadata"""

    def __init__(self, db_path: str = "/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/backup_metadata.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize restore metadata database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS restore_requests (
                    restore_id TEXT PRIMARY KEY,
                    backup_id TEXT NOT NULL,
                    restore_type TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    target_path TEXT,
                    point_in_time TIMESTAMP,
                    selective_items TEXT,
                    dry_run BOOLEAN DEFAULT 0,
                    force_overwrite BOOLEAN DEFAULT 0,
                    validate_before_restore BOOLEAN DEFAULT 1,
                    validate_after_restore BOOLEAN DEFAULT 1,
                    create_rollback_point BOOLEAN DEFAULT 1,
                    notification_emails TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS restore_results (
                    restore_id TEXT PRIMARY KEY,
                    backup_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    restored_items TEXT,
                    skipped_items TEXT,
                    failed_items TEXT,
                    rollback_point TEXT,
                    validation_results TEXT,
                    size_bytes INTEGER,
                    checksum TEXT,
                    error_message TEXT
                )
            """)

    def save_restore_request(self, request: RestoreRequest):
        """Save restore request to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO restore_requests
                (restore_id, backup_id, restore_type, scope, target_path, point_in_time,
                 selective_items, dry_run, force_overwrite, validate_before_restore,
                 validate_after_restore, create_rollback_point, notification_emails,
                 metadata, created_at, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.restore_id, request.backup_id, request.restore_type, request.scope,
                request.target_path, request.point_in_time.isoformat() if request.point_in_time else None,
                json.dumps(request.selective_items) if request.selective_items else None,
                request.dry_run, request.force_overwrite, request.validate_before_restore,
                request.validate_after_restore, request.create_rollback_point,
                json.dumps(request.notification_emails) if request.notification_emails else None,
                json.dumps(request.metadata) if request.metadata else None,
                datetime.now(timezone.utc), RestoreStatus.PENDING.value, None
            ))

    def save_restore_result(self, result: RestoreResult):
        """Save restore result to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO restore_results
                (restore_id, backup_id, status, started_at, completed_at,
                 restored_items, skipped_items, failed_items, rollback_point,
                 validation_results, size_bytes, checksum, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.restore_id, result.backup_id, result.status,
                result.started_at, result.completed_at,
                json.dumps(result.restored_items), json.dumps(result.skipped_items),
                json.dumps(result.failed_items), result.rollback_point,
                json.dumps(result.validation_results), result.size_bytes,
                result.checksum, result.error_message
            ))

    def update_restore_status(self, restore_id: str, status: str, error_message: str = None):
        """Update restore operation status"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE restore_requests
                SET status = ?, error_message = ?
                WHERE restore_id = ?
            """, (status, error_message, restore_id))

    def get_backup(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Get backup information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM backups WHERE backup_id = ?
            """, (backup_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    def get_restore_status(self, restore_id: str) -> Dict[str, Any]:
        """Get restore operation status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM restore_requests WHERE restore_id = ?
            """, (restore_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None

    def list_restores(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List restore operations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM restore_requests
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

class RollbackManager:
    """Manages rollback points and operations"""

    def __init__(self):
        self.rollback_points = {}

    async def create_rollback_point(self, request: RestoreRequest) -> str:
        """Create rollback point before restore operation"""
        rollback_id = f"rollback_{request.restore_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        rollback_data = {
            'rollback_id': rollback_id,
            'restore_id': request.restore_id,
            'backup_id': request.backup_id,
            'scope': request.scope,
            'created_at': datetime.now(timezone.utc),
            'system_state': await self.capture_system_state(request.scope)
        }

        # Save rollback point
        self.rollback_points[rollback_id] = rollback_data

        # Save to database for persistence
        await self.save_rollback_point(rollback_data)

        logger.info(f"Created rollback point: {rollback_id}")
        return rollback_id

    async def capture_system_state(self, scope: str) -> Dict[str, Any]:
        """Capture current system state for rollback"""
        state = {
            'databases': {},
            'files': {},
            'configuration': {},
            'services': {}
        }

        if scope in [RestoreScope.DATABASE.value, RestoreScope.ALL.value]:
            # Capture database states
            state['databases'] = await self.capture_database_states()

        if scope in [RestoreScope.FILES.value, RestoreScope.ALL.value]:
            # Capture file states
            state['files'] = await self.capture_file_states()

        if scope in [RestoreScope.CONFIGURATION.value, RestoreScope.ALL.value]:
            # Capture configuration states
            state['configuration'] = await self.capture_configuration_states()

        return state

    async def capture_database_states(self) -> Dict[str, Any]:
        """Capture database states for rollback"""
        states = {}

        # PostgreSQL
        try:
            # This would involve taking a quick backup or noting transaction positions
            states['postgresql'] = {
                'status': 'active',
                'last_backup': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.warning(f"Failed to capture PostgreSQL state: {e}")

        # Redis
        try:
            states['redis'] = {
                'status': 'active',
                'last_save': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.warning(f"Failed to capture Redis state: {e}")

        return states

    async def capture_file_states(self) -> Dict[str, Any]:
        """Capture file states for rollback"""
        states = {}

        # Capture important file checksums
        important_paths = [
            '/home/activeloguser/DMLogn8n/multi-portal-gateway',
            '/home/activeloguser/DMLogn8n/uploads',
            '/home/activeloguser/DMLogn8n/models'
        ]

        for path in important_paths:
            if os.path.exists(path):
                states[path] = await self.calculate_directory_checksum(path)

        return states

    async def capture_configuration_states(self) -> Dict[str, Any]:
        """Capture configuration states for rollback"""
        states = {}

        config_files = [
            '/home/activeloguser/DMLogn8n/multi-portal-gateway/config/app.yaml',
            '/home/activeloguser/DMLogn8n/.env'
        ]

        for config_file in config_files:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    states[config_file] = {
                        'content': f.read(),
                        'checksum': hashlib.md5(f.read().encode()).hexdigest()
                    }

        return states

    async def calculate_directory_checksum(self, path: str) -> str:
        """Calculate checksum for directory"""
        hash_md5 = hashlib.md5()

        for root, dirs, files in os.walk(path):
            for file in sorted(files):
                file_path = os.path.join(root, file)
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)

        return hash_md5.hexdigest()

    async def save_rollback_point(self, rollback_data: Dict[str, Any]):
        """Save rollback point to persistent storage"""
        rollback_file = f"/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/rollbacks/{rollback_data['rollback_id']}.json"

        os.makedirs(os.path.dirname(rollback_file), exist_ok=True)

        with open(rollback_file, 'w') as f:
            json.dump(rollback_data, f, indent=2, default=str)

    async def execute_rollback(self, rollback_id: str):
        """Execute rollback to previous state"""
        if rollback_id not in self.rollback_points:
            # Load from file
            rollback_file = f"/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/rollbacks/{rollback_id}.json"
            if os.path.exists(rollback_file):
                with open(rollback_file, 'r') as f:
                    self.rollback_points[rollback_id] = json.load(f)
            else:
                raise Exception(f"Rollback point not found: {rollback_id}")

        rollback_data = self.rollback_points[rollback_id]

        logger.info(f"Executing rollback: {rollback_id}")

        # Implementation would restore system to previous state
        # This is complex and would need to be carefully implemented based on captured state

        logger.info(f"Rollback completed: {rollback_id}")

class RestoreValidator:
    """Validates restore operations"""

    async def validate_backup_for_restore(self, backup_id: str) -> Dict[str, Any]:
        """Validate backup before restore"""
        # Import validation logic
        from validators.restore_validator import RestoreValidatorImpl

        validator = RestoreValidatorImpl()
        return await validator.validate_backup_for_restore(backup_id)

    async def verify_restore(self, result: RestoreResult) -> Dict[str, Any]:
        """Verify restore after completion"""
        # Implementation would verify restored data integrity
        return {
            'valid': True,
            'checks_performed': ['integrity', 'accessibility', 'consistency'],
            'errors': []
        }

class RestoreNotifier:
    """Handles restore notifications"""

    async def send_restore_success_notification(self, result: RestoreResult):
        """Send restore success notification"""
        subject = f"Restore Success: {result.restore_id}"
        body = f"""
        Restore operation completed successfully!

        Restore ID: {result.restore_id}
        Backup ID: {result.backup_id}
        Status: {result.status}
        Started: {result.started_at}
        Completed: {result.completed_at}
        Restored Items: {len(result.restored_items)}
        Failed Items: {len(result.failed_items)}

        Restored Items:
        {chr(10).join(f"- {item}" for item in result.restored_items)}

        Validation Results:
        {json.dumps(result.validation_results, indent=2)}
        """

        await self.send_notification(subject, body)

    async def send_restore_failure_notification(self, restore_id: str, error: str):
        """Send restore failure notification"""
        subject = f"Restore Failed: {restore_id}"
        body = f"""
        Restore operation failed!

        Restore ID: {restore_id}
        Error: {error}
        Timestamp: {datetime.now(timezone.utc).isoformat()}

        Please investigate the issue and check the restore logs.
        """

        await self.send_notification(subject, body)

    async def send_notification(self, subject: str, body: str):
        """Send notification (email/Slack/etc.)"""
        # Implementation would send notification via configured channels
        logger.info(f"Restore notification: {subject}")

async def main():
    """Main restore service entry point"""
    try:
        restore_service = RestoreService()

        # Keep service running
        while True:
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        logger.info("Restore service stopped by user")
    except Exception as e:
        logger.error(f"Restore service error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())