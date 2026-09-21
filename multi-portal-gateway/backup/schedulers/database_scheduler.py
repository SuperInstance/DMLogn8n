#!/usr/bin/env python3
"""
Database Backup Scheduler - Handles backup operations for all databases

This scheduler manages backups for PostgreSQL, Redis, Qdrant vector database,
and other data stores used by the DMLogn8n multi-agent platform.
"""

import asyncio
import logging
import os
import subprocess
import tempfile
import shutil
import json
import gzip
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import psycopg2
import redis
import requests
from cryptography.fernet import Fernet
import yaml

# Import backup service types
from backup_service import BackupMetadata, BackupType, BackupStatus, EncryptionManager

logger = logging.getLogger(__name__)

class DatabaseType(Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    REDIS = "redis"
    QDRANT = "qdrant"
    MONGODB = "mongodb"
    ELASTICSEARCH = "elasticsearch"

class BackupMethod(Enum):
    """Database backup methods"""
    LOGICAL_DUMP = "logical_dump"
    PHYSICAL_BACKUP = "physical_backup"
    SNAPSHOT = "snapshot"
    INCREMENTAL_WAL = "incremental_wal"

@dataclass
class DatabaseConfig:
    """Database configuration"""
    name: str
    type: str
    host: str
    port: int
    database: str
    username: str
    password: str
    additional_params: Dict[str, Any] = None
    backup_method: str = "logical_dump"
    backup_options: Dict[str, Any] = None

@dataclass
class DatabaseBackupResult:
    """Database backup operation result"""
    database_name: str
    backup_type: str
    backup_method: str
    dump_file: str
    size_bytes: int
    compressed_size_bytes: int
    checksum: str
    wal_files: List[str] = None
    snapshot_id: str = None
    metadata: Dict[str, Any] = None

class DatabaseScheduler:
    """Database backup scheduler implementation"""

    def __init__(self, backup_service):
        self.backup_service = backup_service
        self.config = self.load_database_config()
        self.encryption_manager = EncryptionManager()
        self.last_backup_times = {}

    def load_database_config(self) -> Dict[str, Any]:
        """Load database configuration"""
        config_path = "/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/config/databases.yaml"

        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load database config: {e}")
            return self.get_default_database_config()

    def get_default_database_config(self) -> Dict[str, Any]:
        """Get default database configuration"""
        return {
            'databases': {
                'postgresql_main': DatabaseConfig(
                    name='postgresql_main',
                    type=DatabaseType.POSTGRESQL.value,
                    host='localhost',
                    port=5432,
                    database='dmlogn8n',
                    username='postgres',
                    password=os.getenv('POSTGRES_PASSWORD'),
                    additional_params={
                        'sslmode': 'prefer',
                        'connect_timeout': 30
                    },
                    backup_method=BackupMethod.LOGICAL_DUMP.value,
                    backup_options={
                        'format': 'custom',
                        'compress_level': 6,
                        'jobs': 4,
                        'verbose': True
                    }
                ),
                'redis_cache': DatabaseConfig(
                    name='redis_cache',
                    type=DatabaseType.REDIS.value,
                    host='localhost',
                    port=6379,
                    database=0,
                    username=None,
                    password=os.getenv('REDIS_PASSWORD'),
                    backup_method=BackupMethod.SNAPSHOT.value,
                    backup_options={
                        'save_on_backup': True,
                        'copy_aof': True
                    }
                ),
                'qdrant_vectors': DatabaseConfig(
                    name='qdrant_vectors',
                    type=DatabaseType.QDRANT.value,
                    host='localhost',
                    port=6333,
                    database=None,
                    username=None,
                    password=os.getenv('QDRANT_API_KEY'),
                    backup_method=BackupMethod.SNAPSHOT.value,
                    backup_options={
                        'include_collections': ['agents', 'memories', 'embeddings'],
                        'snapshot_format': 'full'
                    }
                )
            },
            'backup_settings': {
                'parallel_backups': True,
                'max_parallel_jobs': 3,
                'timeout_seconds': 3600,
                'retry_attempts': 3,
                'retry_delay_seconds': 60,
                'pre_backup_commands': [
                    "SELECT pg_start_backup('dmlogn8n_backup', true);"
                ],
                'post_backup_commands': [
                    "SELECT pg_stop_backup();"
                ]
            },
            'retention_settings': {
                'daily_retention_days': 7,
                'weekly_retention_weeks': 4,
                'monthly_retention_months': 12,
                'wal_retention_days': 30
            }
        }

    async def execute_backup(self, backup_metadata: BackupMetadata, backup_type: BackupType) -> Dict[str, Any]:
        """Execute database backup operation"""
        logger.info(f"Starting database backup: {backup_metadata.backup_id}")

        start_time = time.time()
        backup_results = []
        temp_dir = tempfile.mkdtemp(prefix=f"db_backup_{backup_metadata.backup_id}_")

        try:
            # Get databases to backup based on backup type and source path
            databases = self.get_databases_for_backup(backup_metadata.source_path, backup_type)

            # Execute backups in parallel if enabled
            if self.config['backup_settings']['parallel_backups']:
                backup_results = await self.execute_parallel_backups(
                    databases, backup_type, temp_dir, backup_metadata
                )
            else:
                backup_results = await self.execute_sequential_backups(
                    databases, backup_type, temp_dir, backup_metadata
                )

            # Create consolidated backup archive
            archive_path = await self.create_backup_archive(
                backup_results, temp_dir, backup_metadata
            )

            # Calculate total size and checksum
            total_size = sum(r['size_bytes'] for r in backup_results)
            compressed_size = os.path.getsize(archive_path)
            checksum = self.calculate_file_checksum(archive_path)

            # Upload to storage backend
            storage_backend = self.backup_service.storage_backends[
                backup_metadata.storage_backend
            ]
            storage_path = await storage_backend.upload_backup(
                archive_path, backup_metadata.backup_id
            )

            # Update last backup times
            for db_result in backup_results:
                self.last_backup_times[db_result['database_name']] = datetime.now(timezone.utc)

            # Clean up temporary directory
            shutil.rmtree(temp_dir)

            duration = time.time() - start_time
            logger.info(f"Database backup completed in {duration:.2f}s: {backup_metadata.backup_id}")

            return {
                'size_bytes': total_size,
                'compressed_size_bytes': compressed_size,
                'checksum': checksum,
                'storage_path': storage_path,
                'backup_results': backup_results,
                'duration_seconds': duration,
                'metadata': {
                    'databases_backed_up': len(backup_results),
                    'backup_method': 'parallel' if self.config['backup_settings']['parallel_backups'] else 'sequential',
                    'temporary_directory': temp_dir
                }
            }

        except Exception as e:
            logger.error(f"Database backup failed: {backup_metadata.backup_id} - {e}")
            # Clean up temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise

    def get_databases_for_backup(self, source_path: str, backup_type: BackupType) -> List[DatabaseConfig]:
        """Get list of databases to backup"""
        databases = []

        # Get all configured databases
        for db_name, db_config in self.config['databases'].items():
            if isinstance(db_config, dict):
                db_config = DatabaseConfig(**db_config)

            # Filter by source path if specified
            if source_path and not self.matches_source_path(db_config, source_path):
                continue

            # For incremental backups, check if we have a recent full backup
            if backup_type == BackupType.INCREMENTAL:
                last_backup_time = self.last_backup_times.get(db_config.name)
                if not last_backup_time:
                    logger.warning(f"No full backup found for {db_config.name}, skipping incremental")
                    continue

            databases.append(db_config)

        return databases

    def matches_source_path(self, db_config: DatabaseConfig, source_path: str) -> bool:
        """Check if database matches source path filter"""
        # Simple path matching - can be enhanced
        if 'postgresql' in source_path and db_config.type == DatabaseType.POSTGRESQL.value:
            return True
        if 'redis' in source_path and db_config.type == DatabaseType.REDIS.value:
            return True
        if 'qdrant' in source_path and db_config.type == DatabaseType.QDRANT.value:
            return True
        return True  # Default to include if no specific filter

    async def execute_parallel_backups(self, databases: List[DatabaseConfig],
                                     backup_type: BackupType, temp_dir: str,
                                     backup_metadata: BackupMetadata) -> List[Dict[str, Any]]:
        """Execute database backups in parallel"""
        max_parallel = self.config['backup_settings']['max_parallel_jobs']
        semaphore = asyncio.Semaphore(max_parallel)

        async def backup_single_database(db_config: DatabaseConfig):
            async with semaphore:
                return await self.backup_single_database(
                    db_config, backup_type, temp_dir, backup_metadata
                )

        tasks = [backup_single_database(db_config) for db_config in databases]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log errors
        backup_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Database backup failed for {databases[i].name}: {result}")
            else:
                backup_results.append(result)

        return backup_results

    async def execute_sequential_backups(self, databases: List[DatabaseConfig],
                                       backup_type: BackupType, temp_dir: str,
                                       backup_metadata: BackupMetadata) -> List[Dict[str, Any]]:
        """Execute database backups sequentially"""
        backup_results = []

        for db_config in databases:
            try:
                result = await self.backup_single_database(
                    db_config, backup_type, temp_dir, backup_metadata
                )
                backup_results.append(result)
            except Exception as e:
                logger.error(f"Database backup failed for {db_config.name}: {e}")

        return backup_results

    async def backup_single_database(self, db_config: DatabaseConfig, backup_type: BackupType,
                                   temp_dir: str, backup_metadata: BackupMetadata) -> Dict[str, Any]:
        """Backup a single database"""
        logger.info(f"Backing up database: {db_config.name}")

        retry_count = 0
        max_retries = self.config['backup_settings']['retry_attempts']

        while retry_count <= max_retries:
            try:
                if db_config.type == DatabaseType.POSTGRESQL.value:
                    result = await self.backup_postgresql(db_config, backup_type, temp_dir, backup_metadata)
                elif db_config.type == DatabaseType.REDIS.value:
                    result = await self.backup_redis(db_config, backup_type, temp_dir, backup_metadata)
                elif db_config.type == DatabaseType.QDRANT.value:
                    result = await self.backup_qdrant(db_config, backup_type, temp_dir, backup_metadata)
                else:
                    raise ValueError(f"Unsupported database type: {db_config.type}")

                logger.info(f"Database backup completed: {db_config.name}")
                return result

            except Exception as e:
                retry_count += 1
                if retry_count <= max_retries:
                    delay = self.config['backup_settings']['retry_delay_seconds']
                    logger.warning(f"Database backup failed for {db_config.name}, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    raise

    async def backup_postgresql(self, db_config: DatabaseConfig, backup_type: BackupType,
                              temp_dir: str, backup_metadata: BackupMetadata) -> Dict[str, Any]:
        """Backup PostgreSQL database"""
        # Generate backup filename
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        dump_filename = f"{db_config.name}_{backup_type.value}_{timestamp}.dump"
        dump_path = os.path.join(temp_dir, dump_filename)

        # Build pg_dump command
        cmd = [
            'pg_dump',
            f'-h{db_config.host}',
            f'-p{db_config.port}',
            f'-U{db_config.username}',
            f'-d{db_config.database}',
            f'-F{db_config.backup_options.get("format", "c")}',
            f'-Z{db_config.backup_options.get("compress_level", 6)}',
            f'-j{db_config.backup_options.get("jobs", 2)}'
        ]

        # Add additional options
        if db_config.backup_options.get('verbose'):
            cmd.append('-v')

        if db_config.additional_params:
            for key, value in db_config.additional_params.items():
                if key == 'sslmode':
                    cmd.extend([f'--{key}', value])

        # Add output file
        cmd.extend(['-f', dump_path])

        # Set environment variables
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config.password

        # Execute pg_dump
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"pg_dump failed: {stderr.decode()}")

        # Get file size
        size_bytes = os.path.getsize(dump_path)

        # Calculate checksum
        checksum = self.calculate_file_checksum(dump_path)

        # For incremental backups, also backup WAL files
        wal_files = []
        if backup_type == BackupType.INCREMENTAL:
            wal_files = await self.backup_postgresql_wal(db_config, temp_dir, backup_metadata)

        # Encrypt backup if enabled
        if backup_service.config.get('encryption', {}).get('enabled', True):
            encrypted_path = dump_path + '.enc'
            encrypted_data, key_id = self.encryption_manager.encrypt_data(
                open(dump_path, 'rb').read()
            )
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
            os.remove(dump_path)
            dump_path = encrypted_path

        return {
            'database_name': db_config.name,
            'backup_type': backup_type.value,
            'backup_method': BackupMethod.LOGICAL_DUMP.value,
            'dump_file': os.path.basename(dump_path),
            'size_bytes': size_bytes,
            'compressed_size_bytes': os.path.getsize(dump_path),
            'checksum': checksum,
            'wal_files': wal_files,
            'metadata': {
                'pg_dump_version': await self.get_pg_dump_version(),
                'postgresql_version': await self.get_postgresql_version(db_config),
                'compression_level': db_config.backup_options.get('compress_level', 6)
            }
        }

    async def backup_postgresql_wal(self, db_config: DatabaseConfig, temp_dir: str,
                                  backup_metadata: BackupMetadata) -> List[str]:
        """Backup PostgreSQL WAL files for incremental backup"""
        wal_dir = os.path.join(temp_dir, 'wal')
        os.makedirs(wal_dir, exist_ok=True)

        # Get WAL directory from PostgreSQL
        conn = psycopg2.connect(
            host=db_config.host,
            port=db_config.port,
            database=db_config.database,
            user=db_config.username,
            password=db_config.password
        )

        try:
            with conn.cursor() as cursor:
                cursor.execute("SHOW pg_waldir;")
                wal_path = cursor.fetchone()[0]

                # Copy recent WAL files
                wal_files = []
                current_time = datetime.now(timezone.utc)
                cutoff_time = current_time - timedelta(hours=24)  # Last 24 hours

                for wal_file in os.listdir(wal_path):
                    if wal_file.endswith('.gz'):
                        file_path = os.path.join(wal_path, wal_file)
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path), timezone.utc)

                        if file_time > cutoff_time:
                            shutil.copy2(file_path, os.path.join(wal_dir, wal_file))
                            wal_files.append(wal_file)

                return wal_files

        finally:
            conn.close()

    async def backup_redis(self, db_config: DatabaseConfig, backup_type: BackupType,
                         temp_dir: str, backup_metadata: BackupMetadata) -> Dict[str, Any]:
        """Backup Redis database"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{db_config.name}_{backup_type.value}_{timestamp}.rdb"
        backup_path = os.path.join(temp_dir, backup_filename)

        # Connect to Redis
        r = redis.Redis(
            host=db_config.host,
            port=db_config.port,
            db=db_config.database,
            password=db_config.password,
            decode_responses=False
        )

        try:
            # Trigger save operation
            if db_config.backup_options.get('save_on_backup', True):
                r.save()

            # Wait for save to complete
            while r.lastsave() == r.info().get('rdb_last_save_time', 0):
                await asyncio.sleep(1)

            # Get RDB file path
            info = r.info()
            rdb_path = info.get('rdb_dbfilename', 'dump.rdb')

            # Copy RDB file to backup location
            # For Docker Redis, we might need to copy from container
            if os.getenv('REDIS_IN_DOCKER', 'false').lower() == 'true':
                # Copy from Docker container
                cmd = [
                    'docker', 'cp',
                    f"{os.getenv('REDIS_CONTAINER_NAME', 'redis')}:/data/{rdb_path}",
                    backup_path
                ]
                process = await asyncio.create_subprocess_exec(*cmd)
                await process.communicate()

                if process.returncode != 0:
                    raise Exception("Failed to copy RDB file from Docker container")
            else:
                # Copy from local filesystem
                shutil.copy2(rdb_path, backup_path)

            # Also backup AOF file if enabled and exists
            aof_files = []
            if db_config.backup_options.get('copy_aof', True):
                try:
                    aof_path = info.get('aof_current_rewrite_time_sec', None)
                    if aof_path:
                        aof_backup_path = backup_path.replace('.rdb', '.aof')
                        shutil.copy2(aof_path, aof_backup_path)
                        aof_files.append(os.path.basename(aof_backup_path))
                except Exception as e:
                    logger.warning(f"Failed to backup AOF file: {e}")

            # Get file size and checksum
            size_bytes = os.path.getsize(backup_path)
            checksum = self.calculate_file_checksum(backup_path)

            # Encrypt backup if enabled
            if backup_service.config.get('encryption', {}).get('enabled', True):
                encrypted_path = backup_path + '.enc'
                encrypted_data, key_id = self.encryption_manager.encrypt_data(
                    open(backup_path, 'rb').read()
                )
                with open(encrypted_path, 'wb') as f:
                    f.write(encrypted_data)
                os.remove(backup_path)
                backup_path = encrypted_path

            return {
                'database_name': db_config.name,
                'backup_type': backup_type.value,
                'backup_method': BackupMethod.SNAPSHOT.value,
                'dump_file': os.path.basename(backup_path),
                'size_bytes': size_bytes,
                'compressed_size_bytes': os.path.getsize(backup_path),
                'checksum': checksum,
                'aof_files': aof_files,
                'metadata': {
                    'redis_version': info.get('redis_version'),
                    'used_memory': info.get('used_memory'),
                    'connected_clients': info.get('connected_clients'),
                    'total_commands_processed': info.get('total_commands_processed')
                }
            }

        finally:
            r.close()

    async def backup_qdrant(self, db_config: DatabaseConfig, backup_type: BackupType,
                          temp_dir: str, backup_metadata: BackupMetadata) -> Dict[str, Any]:
        """Backup Qdrant vector database"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(temp_dir, f"{db_config.name}_{backup_type.value}_{timestamp}")
        os.makedirs(backup_dir, exist_ok=True)

        # Qdrant backup API endpoint
        api_url = f"http://{db_config.host}:{db_config.port}/snapshots"

        headers = {}
        if db_config.password:
            headers['api-key'] = db_config.password

        try:
            # Create snapshot
            snapshot_response = requests.post(api_url, headers=headers)
            snapshot_response.raise_for_status()

            snapshot_info = snapshot_response.json()
            snapshot_name = snapshot_info.get('name', f"snapshot_{timestamp}")

            # Download snapshot
            snapshot_url = f"{api_url}/{snapshot_name}"
            download_response = requests.get(snapshot_url, headers=headers, stream=True)
            download_response.raise_for_status()

            snapshot_path = os.path.join(backup_dir, f"{snapshot_name}.snapshot")
            with open(snapshot_path, 'wb') as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Also backup collection metadata
            collections_url = f"http://{db_config.host}:{db_config.port}/collections"
            collections_response = requests.get(collections_url, headers=headers)
            collections_response.raise_for_status()

            collections_data = collections_response.json()
            collections_path = os.path.join(backup_dir, "collections.json")
            with open(collections_path, 'w') as f:
                json.dump(collections_data, f, indent=2)

            # Create archive
            archive_path = backup_dir + '.tar.gz'
            with tarfile.open(archive_path, 'w:gz') as tar:
                tar.add(backup_dir, arcname=os.path.basename(backup_dir))

            # Calculate size and checksum
            size_bytes = sum(os.path.getsize(os.path.join(dirpath, filename))
                           for dirpath, dirnames, filenames in os.walk(backup_dir)
                           for filename in filenames)
            checksum = self.calculate_file_checksum(archive_path)

            # Clean up temporary directory
            shutil.rmtree(backup_dir)

            return {
                'database_name': db_config.name,
                'backup_type': backup_type.value,
                'backup_method': BackupMethod.SNAPSHOT.value,
                'dump_file': os.path.basename(archive_path),
                'size_bytes': size_bytes,
                'compressed_size_bytes': os.path.getsize(archive_path),
                'checksum': checksum,
                'snapshot_id': snapshot_name,
                'metadata': {
                    'qdrant_version': await self.get_qdrant_version(db_config),
                    'collections_count': len(collections_data.get('result', {}).get('collections', [])),
                    'snapshot_format': db_config.backup_options.get('snapshot_format', 'full')
                }
            }

        except requests.exceptions.RequestException as e:
            raise Exception(f"Qdrant backup failed: {e}")

    async def create_backup_archive(self, backup_results: List[Dict[str, Any]],
                                  temp_dir: str, backup_metadata: BackupMetadata) -> str:
        """Create consolidated backup archive"""
        archive_name = f"database_backup_{backup_metadata.backup_id}.tar.gz"
        archive_path = os.path.join(temp_dir, archive_name)

        # Create manifest file
        manifest_path = os.path.join(temp_dir, 'manifest.json')
        manifest = {
            'backup_id': backup_metadata.backup_id,
            'backup_type': backup_metadata.backup_type,
            'created_at': backup_metadata.created_at.isoformat(),
            'databases': backup_results,
            'total_size': sum(r['size_bytes'] for r in backup_results),
            'total_compressed_size': sum(r['compressed_size_bytes'] for r in backup_results)
        }

        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2, default=str)

        # Create archive
        with tarfile.open(archive_path, 'w:gz') as tar:
            # Add all backup files
            for result in backup_results:
                file_path = os.path.join(temp_dir, result['dump_file'])
                if os.path.exists(file_path):
                    tar.add(file_path, arcname=result['dump_file'])

                # Add WAL files if present
                if result.get('wal_files'):
                    wal_dir = os.path.join(temp_dir, 'wal')
                    if os.path.exists(wal_dir):
                        tar.add(wal_dir, arcname='wal')

                # Add AOF files if present
                if result.get('aof_files'):
                    for aof_file in result['aof_files']:
                        aof_path = os.path.join(temp_dir, aof_file)
                        if os.path.exists(aof_path):
                            tar.add(aof_path, arcname=aof_file)

            # Add manifest
            tar.add(manifest_path, arcname='manifest.json')

        return archive_path

    def calculate_file_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    async def get_pg_dump_version(self) -> str:
        """Get pg_dump version"""
        try:
            process = await asyncio.create_subprocess_exec(
                'pg_dump', '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            return stdout.decode().strip()
        except Exception:
            return "unknown"

    async def get_postgresql_version(self, db_config: DatabaseConfig) -> str:
        """Get PostgreSQL server version"""
        try:
            conn = psycopg2.connect(
                host=db_config.host,
                port=db_config.port,
                database=db_config.database,
                user=db_config.username,
                password=db_config.password
            )
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()[0]
                    return version.split(',')[0]
            finally:
                conn.close()
        except Exception:
            return "unknown"

    async def get_qdrant_version(self, db_config: DatabaseConfig) -> str:
        """Get Qdrant version"""
        try:
            api_url = f"http://{db_config.host}:{db_config.port}/health"
            headers = {}
            if db_config.password:
                headers['api-key'] = db_config.password

            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            return response.json().get('version', 'unknown')
        except Exception:
            return "unknown"

    def get_backup_status(self, database_name: str) -> Dict[str, Any]:
        """Get backup status for a specific database"""
        last_backup = self.last_backup_times.get(database_name)

        return {
            'database_name': database_name,
            'last_backup_time': last_backup.isoformat() if last_backup else None,
            'backup_enabled': database_name in self.config['databases'],
            'backup_method': self.config['databases'][database_name].get('backup_method', 'logical_dump')
        }

    def get_all_backup_status(self) -> Dict[str, Any]:
        """Get backup status for all databases"""
        status = {}
        for db_name in self.config['databases']:
            status[db_name] = self.get_backup_status(db_name)
        return status