#!/usr/bin/env python3
"""
File System Backup Scheduler - Handles backup operations for files and directories

This scheduler manages backups for application files, user uploads, logs,
configuration files, and other file-based data used by the DMLogn8n platform.
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
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import yaml
import tarfile
import zipfile
import magic
from cryptography.fernet import Fernet

# Import backup service types
from backup_service import BackupMetadata, BackupType, BackupStatus, EncryptionManager

logger = logging.getLogger(__name__)

class FileType(Enum):
    """File types for backup classification"""
    APPLICATION = "application"
    USER_UPLOADS = "user_uploads"
    LOGS = "logs"
    MODELS = "models"
    CONFIGURATION = "configuration"
    TEMPORARY = "temporary"
    CACHE = "cache"
    STATIC = "static"

class CompressionType(Enum):
    """Compression types"""
    GZIP = "gzip"
    BZIP2 = "bzip2"
    XZ = "xz"
    ZIP = "zip"
    NONE = "none"

class BackupMethod(Enum):
    """File backup methods"""
    FULL_ARCHIVE = "full_archive"
    INCREMENTAL_SYNC = "incremental_sync"
    RSYNC_MIRROR = "rsync_mirror"
    SNAPSHOT = "snapshot"

@dataclass
class FileBackupConfig:
    """File backup configuration"""
    name: str
    source_path: str
    file_type: str
    backup_method: str
    compression: str = "gzip"
    compression_level: int = 6
    exclude_patterns: List[str] = None
    include_patterns: List[str] = None
    max_size_mb: Optional[int] = None
    follow_symlinks: bool = False
    preserve_permissions: bool = True
    preserve_timestamps: bool = True
    checksum_verification: bool = True
    encryption_enabled: bool = True
    split_large_files: bool = False
    split_size_mb: int = 1024

@dataclass
class FileBackupResult:
    """File backup operation result"""
    backup_name: str
    source_path: str
    backup_method: str
    archive_files: List[str]
    total_files: int
    total_directories: int
    size_bytes: int
    compressed_size_bytes: int
    checksum: str
    excluded_files: List[str]
    errors: List[str]
    metadata: Dict[str, Any]

class FileScheduler:
    """File system backup scheduler implementation"""

    def __init__(self, backup_service):
        self.backup_service = backup_service
        self.config = self.load_file_config()
        self.encryption_manager = EncryptionManager()
        self.last_backup_times = {}
        self.file_checksum_cache = {}
        self.existing_files_cache = {}

    def load_file_config(self) -> Dict[str, Any]:
        """Load file backup configuration"""
        config_path = "/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/config/files.yaml"

        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load file config: {e}")
            return self.get_default_file_config()

    def get_default_file_config(self) -> Dict[str, Any]:
        """Get default file backup configuration"""
        return {
            'file_backups': {
                'application_files': FileBackupConfig(
                    name='application_files',
                    source_path='/home/activeloguser/DMLogn8n',
                    file_type=FileType.APPLICATION.value,
                    backup_method=BackupMethod.FULL_ARCHIVE.value,
                    compression=CompressionType.GZIP.value,
                    compression_level=6,
                    exclude_patterns=[
                        '*.tmp', '*.log', '*.cache', '__pycache__',
                        '.git', '.venv', 'venv', 'node_modules',
                        '.pytest_cache', '.coverage', 'htmlcov'
                    ],
                    include_patterns=['*.py', '*.js', '*.yaml', '*.json', '*.md'],
                    follow_symlinks=False,
                    preserve_permissions=True,
                    preserve_timestamps=True,
                    checksum_verification=True,
                    encryption_enabled=True
                ),
                'user_uploads': FileBackupConfig(
                    name='user_uploads',
                    source_path='/home/activeloguser/DMLogn8n/uploads',
                    file_type=FileType.USER_UPLOADS.value,
                    backup_method=BackupMethod.INCREMENTAL_SYNC.value,
                    compression=CompressionType.GZIP.value,
                    compression_level=9,
                    exclude_patterns=['*.tmp', 'temp/*'],
                    follow_symlinks=False,
                    preserve_permissions=True,
                    preserve_timestamps=True,
                    checksum_verification=True,
                    encryption_enabled=True,
                    split_large_files=True,
                    split_size_mb=512
                ),
                'log_files': FileBackupConfig(
                    name='log_files',
                    source_path='/home/activeloguser/DMLogn8n/logs',
                    file_type=FileType.LOGS.value,
                    backup_method=BackupMethod.FULL_ARCHIVE.value,
                    compression=CompressionType.GZIP.value,
                    compression_level=9,
                    exclude_patterns=['*.tmp', 'current/*'],
                    include_patterns=['*.log', '*.json'],
                    max_size_mb=10240,  # 10GB max
                    checksum_verification=False,  # Skip for logs
                    encryption_enabled=True
                ),
                'model_files': FileBackupConfig(
                    name='model_files',
                    source_path='/home/activeloguser/DMLogn8n/models',
                    file_type=FileType.MODELS.value,
                    backup_method=BackupMethod.RSYNC_MIRROR.value,
                    compression=CompressionType.NONE.value,  # Don't compress model files
                    exclude_patterns=['*.tmp', 'cache/*', 'temp/*'],
                    include_patterns=['*.pkl', '*.h5', '*.pt', '*.pth', '*.bin', '*.onnx'],
                    checksum_verification=True,
                    encryption_enabled=True,
                    split_large_files=True,
                    split_size_mb=2048
                ),
                'static_files': FileBackupConfig(
                    name='static_files',
                    source_path='/home/activeloguser/DMLogn8n/static',
                    file_type=FileType.STATIC.value,
                    backup_method=BackupMethod.FULL_ARCHIVE.value,
                    compression=CompressionType.GZIP.value,
                    compression_level=6,
                    exclude_patterns=['*.cache', '.well-known/*'],
                    checksum_verification=True,
                    encryption_enabled=False  # Static files typically don't need encryption
                )
            },
            'backup_settings': {
                'parallel_backups': True,
                'max_parallel_jobs': 2,
                'timeout_seconds': 7200,  # 2 hours
                'retry_attempts': 3,
                'retry_delay_seconds': 60,
                'progress_reporting': True,
                'progress_interval_seconds': 30,
                'disk_space_threshold_gb': 10,
                'verify_disk_space': True
            },
            'retention_settings': {
                'daily_retention_days': 7,
                'weekly_retention_weeks': 4,
                'monthly_retention_months': 12,
                'yearly_retention_years': 3,
                'keep_recent_versions': 5
            },
            'notification_settings': {
                'notify_on_large_files': True,
                'large_file_threshold_mb': 100,
                'notify_on_errors': True,
                'progress_notifications': False
            }
        }

    async def execute_backup(self, backup_metadata: BackupMetadata, backup_type: BackupType) -> Dict[str, Any]:
        """Execute file system backup operation"""
        logger.info(f"Starting file system backup: {backup_metadata.backup_id}")

        start_time = time.time()
        backup_results = []
        temp_dir = tempfile.mkdtemp(prefix=f"file_backup_{backup_metadata.backup_id}_")

        try:
            # Verify available disk space
            if self.config['backup_settings']['verify_disk_space']:
                await self.verify_disk_space(temp_dir)

            # Get file configs to backup based on source path and backup type
            file_configs = self.get_file_configs_for_backup(backup_metadata.source_path, backup_type)

            # Execute backups in parallel if enabled
            if self.config['backup_settings']['parallel_backups']:
                backup_results = await self.execute_parallel_backups(
                    file_configs, backup_type, temp_dir, backup_metadata
                )
            else:
                backup_results = await self.execute_sequential_backups(
                    file_configs, backup_type, temp_dir, backup_metadata
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

            # Update last backup times and file cache
            for result in backup_results:
                backup_name = result['backup_name']
                self.last_backup_times[backup_name] = datetime.now(timezone.utc)
                await self.update_file_checksum_cache(result)

            # Clean up temporary directory
            shutil.rmtree(temp_dir)

            duration = time.time() - start_time
            logger.info(f"File system backup completed in {duration:.2f}s: {backup_metadata.backup_id}")

            return {
                'size_bytes': total_size,
                'compressed_size_bytes': compressed_size,
                'checksum': checksum,
                'storage_path': storage_path,
                'backup_results': backup_results,
                'duration_seconds': duration,
                'metadata': {
                    'file_backups_count': len(backup_results),
                    'total_files_backed_up': sum(r['total_files'] for r in backup_results),
                    'total_directories_backed_up': sum(r['total_directories'] for r in backup_results),
                    'backup_method': 'parallel' if self.config['backup_settings']['parallel_backups'] else 'sequential'
                }
            }

        except Exception as e:
            logger.error(f"File system backup failed: {backup_metadata.backup_id} - {e}")
            # Clean up temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise

    def get_file_configs_for_backup(self, source_path: str, backup_type: BackupType) -> List[FileBackupConfig]:
        """Get list of file configurations to backup"""
        file_configs = []

        for name, config in self.config['file_backups'].items():
            if isinstance(config, dict):
                config = FileBackupConfig(**config)

            # Filter by source path if specified
            if source_path and not self.matches_source_path(config, source_path):
                continue

            # For incremental backups, check if we have a recent full backup
            if backup_type == BackupType.INCREMENTAL:
                if config.backup_method not in [BackupMethod.INCREMENTAL_SYNC.value, BackupMethod.RSYNC_MIRROR.value]:
                    logger.warning(f"Backup method {config.backup_method} doesn't support incremental for {config.name}")
                    continue

                last_backup_time = self.last_backup_times.get(config.name)
                if not last_backup_time:
                    logger.warning(f"No full backup found for {config.name}, skipping incremental")
                    continue

            file_configs.append(config)

        return file_configs

    def matches_source_path(self, config: FileBackupConfig, source_path: str) -> bool:
        """Check if file config matches source path filter"""
        # Check if source path is within or equal to config source path
        config_path = os.path.abspath(config.source_path)
        filter_path = os.path.abspath(source_path)

        return filter_path.startswith(config_path) or config_path.startswith(filter_path)

    async def execute_parallel_backups(self, file_configs: List[FileBackupConfig],
                                     backup_type: BackupType, temp_dir: str,
                                     backup_metadata: BackupMetadata) -> List[Dict[str, Any]]:
        """Execute file backups in parallel"""
        max_parallel = self.config['backup_settings']['max_parallel_jobs']
        semaphore = asyncio.Semaphore(max_parallel)

        async def backup_single_file_config(file_config: FileBackupConfig):
            async with semaphore:
                return await self.backup_single_file_config(
                    file_config, backup_type, temp_dir, backup_metadata
                )

        tasks = [backup_single_file_config(config) for config in file_configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log errors
        backup_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"File backup failed for {file_configs[i].name}: {result}")
            else:
                backup_results.append(result)

        return backup_results

    async def execute_sequential_backups(self, file_configs: List[FileBackupConfig],
                                       backup_type: BackupType, temp_dir: str,
                                       backup_metadata: BackupMetadata) -> List[Dict[str, Any]]:
        """Execute file backups sequentially"""
        backup_results = []

        for file_config in file_configs:
            try:
                result = await self.backup_single_file_config(
                    file_config, backup_type, temp_dir, backup_metadata
                )
                backup_results.append(result)
            except Exception as e:
                logger.error(f"File backup failed for {file_config.name}: {e}")

        return backup_results

    async def backup_single_file_config(self, file_config: FileBackupConfig, backup_type: BackupType,
                                      temp_dir: str, backup_metadata: BackupMetadata) -> Dict[str, Any]:
        """Backup a single file configuration"""
        logger.info(f"Backing up file config: {file_config.name}")

        # Check if source path exists
        if not os.path.exists(file_config.source_path):
            raise Exception(f"Source path does not exist: {file_config.source_path}")

        retry_count = 0
        max_retries = self.config['backup_settings']['retry_attempts']

        while retry_count <= max_retries:
            try:
                if file_config.backup_method == BackupMethod.FULL_ARCHIVE.value:
                    result = await self.backup_full_archive(file_config, backup_type, temp_dir, backup_metadata)
                elif file_config.backup_method == BackupMethod.INCREMENTAL_SYNC.value:
                    result = await self.backup_incremental_sync(file_config, backup_type, temp_dir, backup_metadata)
                elif file_config.backup_method == BackupMethod.RSYNC_MIRROR.value:
                    result = await self.backup_rsync_mirror(file_config, backup_type, temp_dir, backup_metadata)
                elif file_config.backup_method == BackupMethod.SNAPSHOT.value:
                    result = await self.backup_snapshot(file_config, backup_type, temp_dir, backup_metadata)
                else:
                    raise ValueError(f"Unsupported backup method: {file_config.backup_method}")

                logger.info(f"File backup completed: {file_config.name}")
                return result

            except Exception as e:
                retry_count += 1
                if retry_count <= max_retries:
                    delay = self.config['backup_settings']['retry_delay_seconds']
                    logger.warning(f"File backup failed for {file_config.name}, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    raise

    async def backup_full_archive(self, file_config: FileBackupConfig, backup_type: BackupType,
                                temp_dir: str, backup_metadata: BackupMetadata) -> Dict[str, Any]:
        """Create full archive backup"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        archive_name = f"{file_config.name}_{backup_type.value}_{timestamp}"
        archive_path = os.path.join(temp_dir, f"{archive_name}.tar")

        # Build tar command
        cmd = ['tar', '-cf', archive_path]

        # Add compression
        if file_config.compression == CompressionType.GZIP.value:
            cmd.insert(1, '-z')
            archive_path += '.gz'
        elif file_config.compression == CompressionType.BZIP2.value:
            cmd.insert(1, '-j')
            archive_path += '.bz2'
        elif file_config.compression == CompressionType.XZ.value:
            cmd.insert(1, '-J')
            archive_path += '.xz'

        # Add options
        if file_config.preserve_permissions:
            cmd.append('-p')
        if file_config.preserve_timestamps:
            cmd.append('--preserve-permissions')

        # Add exclude patterns
        if file_config.exclude_patterns:
            for pattern in file_config.exclude_patterns:
                cmd.extend(['--exclude', pattern])

        # Add source path
        cmd.append(file_config.source_path)

        # Execute tar command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"tar command failed: {stderr.decode()}")

        # Get archive statistics
        total_files, total_directories = await self.count_files_in_archive(archive_path)
        size_bytes = await self.get_uncompressed_size(file_config.source_path, file_config)
        compressed_size_bytes = os.path.getsize(archive_path)

        # Check if archive exceeds maximum size
        if file_config.max_size_mb and (compressed_size_bytes / (1024 * 1024)) > file_config.max_size_mb:
            logger.warning(f"Archive size {compressed_size_bytes} bytes exceeds maximum {file_config.max_size_mb}MB")

        # Split large files if enabled
        archive_files = [os.path.basename(archive_path)]
        if file_config.split_large_files and compressed_size_bytes > (file_config.split_size_mb * 1024 * 1024):
            split_files = await self.split_large_file(archive_path, file_config.split_size_mb)
            archive_files.extend([os.path.basename(f) for f in split_files])
            # Remove original large file
            os.remove(archive_path)

        # Calculate checksum
        if archive_files:
            primary_file = os.path.join(temp_dir, archive_files[0])
            checksum = self.calculate_file_checksum(primary_file)
        else:
            checksum = ""

        # Encrypt backup if enabled
        if file_config.encryption_enabled:
            encrypted_files = []
            for archive_file in archive_files:
                file_path = os.path.join(temp_dir, archive_file)
                encrypted_path = file_path + '.enc'
                encrypted_data, key_id = self.encryption_manager.encrypt_data(
                    open(file_path, 'rb').read()
                )
                with open(encrypted_path, 'wb') as f:
                    f.write(encrypted_data)
                os.remove(file_path)
                encrypted_files.append(os.path.basename(encrypted_path))
            archive_files = encrypted_files

        return {
            'backup_name': file_config.name,
            'source_path': file_config.source_path,
            'backup_method': BackupMethod.FULL_ARCHIVE.value,
            'archive_files': archive_files,
            'total_files': total_files,
            'total_directories': total_directories,
            'size_bytes': size_bytes,
            'compressed_size_bytes': compressed_size_bytes,
            'checksum': checksum,
            'excluded_files': file_config.exclude_patterns or [],
            'errors': [],
            'metadata': {
                'compression': file_config.compression,
                'compression_level': file_config.compression_level,
                'file_type': file_config.file_type,
                'split_files': len(archive_files) > 1
            }
        }

    async def backup_incremental_sync(self, file_config: FileBackupConfig, backup_type: BackupType,
                                    temp_dir: str, backup_metadata: BackupMetadata) -> Dict[str, Any]:
        """Create incremental sync backup"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(temp_dir, f"{file_config.name}_{backup_type.value}_{timestamp}")
        os.makedirs(backup_dir, exist_ok=True)

        # Get list of changed files since last backup
        changed_files = await self.get_changed_files(file_config, backup_type)

        if not changed_files:
            logger.info(f"No changed files found for {file_config.name}")
            return {
                'backup_name': file_config.name,
                'source_path': file_config.source_path,
                'backup_method': BackupMethod.INCREMENTAL_SYNC.value,
                'archive_files': [],
                'total_files': 0,
                'total_directories': 0,
                'size_bytes': 0,
                'compressed_size_bytes': 0,
                'checksum': "",
                'excluded_files': [],
                'errors': [],
                'metadata': {
                    'incremental_type': 'no_changes',
                    'file_type': file_config.file_type
                }
            }

        # Copy changed files
        copied_files = []
        for file_info in changed_files:
            src_path = file_info['path']
            rel_path = os.path.relpath(src_path, file_config.source_path)
            dst_path = os.path.join(backup_dir, rel_path)

            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src_path, dst_path)
            copied_files.append(rel_path)

        # Create archive of changed files
        archive_path = backup_dir + '.tar.gz'
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(backup_dir, arcname=os.path.basename(backup_dir))

        # Calculate statistics
        total_files = len(copied_files)
        total_directories = len(set(os.path.dirname(f) for f in copied_files))
        size_bytes = sum(os.path.getsize(os.path.join(backup_dir, f)) for f in copied_files)
        compressed_size_bytes = os.path.getsize(archive_path)

        # Calculate checksum
        checksum = self.calculate_file_checksum(archive_path)

        # Clean up temporary directory
        shutil.rmtree(backup_dir)

        return {
            'backup_name': file_config.name,
            'source_path': file_config.source_path,
            'backup_method': BackupMethod.INCREMENTAL_SYNC.value,
            'archive_files': [os.path.basename(archive_path)],
            'total_files': total_files,
            'total_directories': total_directories,
            'size_bytes': size_bytes,
            'compressed_size_bytes': compressed_size_bytes,
            'checksum': checksum,
            'excluded_files': file_config.exclude_patterns or [],
            'errors': [],
            'metadata': {
                'incremental_type': 'changed_files',
                'changed_files_count': len(changed_files),
                'file_type': file_config.file_type
            }
        }

    async def backup_rsync_mirror(self, file_config: FileBackupConfig, backup_type: BackupType,
                                temp_dir: str, backup_metadata: BackupMetadata) -> Dict[str, Any]:
        """Create rsync mirror backup"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        mirror_dir = os.path.join(temp_dir, f"{file_config.name}_mirror_{timestamp}")

        # Build rsync command
        cmd = [
            'rsync', '-avh',
            '--delete',
            '--delete-excluded'
        ]

        # Add exclude patterns
        if file_config.exclude_patterns:
            for pattern in file_config.exclude_patterns:
                cmd.extend(['--exclude', pattern])

        # Add source and destination
        cmd.extend([file_config.source_path + '/', mirror_dir])

        # Execute rsync command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"rsync command failed: {stderr.decode()}")

        # Parse rsync output for statistics
        rsync_output = stdout.decode()
        total_files, total_directories = self.parse_rsync_stats(rsync_output)

        # Create archive
        archive_path = mirror_dir + '.tar.gz'
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(mirror_dir, arcname=os.path.basename(mirror_dir))

        # Calculate size and checksum
        size_bytes = await self.calculate_directory_size(mirror_dir)
        compressed_size_bytes = os.path.getsize(archive_path)
        checksum = self.calculate_file_checksum(archive_path)

        # Clean up mirror directory
        shutil.rmtree(mirror_dir)

        return {
            'backup_name': file_config.name,
            'source_path': file_config.source_path,
            'backup_method': BackupMethod.RSYNC_MIRROR.value,
            'archive_files': [os.path.basename(archive_path)],
            'total_files': total_files,
            'total_directories': total_directories,
            'size_bytes': size_bytes,
            'compressed_size_bytes': compressed_size_bytes,
            'checksum': checksum,
            'excluded_files': file_config.exclude_patterns or [],
            'errors': [],
            'metadata': {
                'rsync_stats': rsync_output,
                'file_type': file_config.file_type
            }
        }

    async def backup_snapshot(self, file_config: FileBackupConfig, backup_type: BackupType,
                            temp_dir: str, backup_metadata: BackupMetadata) -> Dict[str, Any]:
        """Create snapshot backup using filesystem snapshots"""
        # This would implement filesystem snapshot functionality
        # For now, fall back to full archive
        logger.warning(f"Snapshot backup not implemented for {file_config.name}, falling back to full archive")
        return await self.backup_full_archive(file_config, backup_type, temp_dir, backup_metadata)

    async def create_backup_archive(self, backup_results: List[Dict[str, Any]],
                                  temp_dir: str, backup_metadata: BackupMetadata) -> str:
        """Create consolidated backup archive"""
        archive_name = f"files_backup_{backup_metadata.backup_id}.tar.gz"
        archive_path = os.path.join(temp_dir, archive_name)

        # Create manifest file
        manifest_path = os.path.join(temp_dir, 'manifest.json')
        manifest = {
            'backup_id': backup_metadata.backup_id,
            'backup_type': backup_metadata.backup_type,
            'created_at': backup_metadata.created_at.isoformat(),
            'file_backups': backup_results,
            'total_size': sum(r['size_bytes'] for r in backup_results),
            'total_compressed_size': sum(r['compressed_size_bytes'] for r in backup_results),
            'total_files': sum(r['total_files'] for r in backup_results),
            'total_directories': sum(r['total_directories'] for r in backup_results)
        }

        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2, default=str)

        # Create archive
        with tarfile.open(archive_path, 'w:gz') as tar:
            # Add all backup files
            for result in backup_results:
                for archive_file in result['archive_files']:
                    file_path = os.path.join(temp_dir, archive_file)
                    if os.path.exists(file_path):
                        tar.add(file_path, arcname=archive_file)

            # Add manifest
            tar.add(manifest_path, arcname='manifest.json')

        return archive_path

    async def get_changed_files(self, file_config: FileBackupConfig, backup_type: BackupType) -> List[Dict[str, Any]]:
        """Get list of files changed since last backup"""
        last_backup_time = self.last_backup_times.get(file_config.name)
        if not last_backup_time:
            # Full backup - return all files
            return await self.get_all_files(file_config)

        changed_files = []
        cache_key = f"{file_config.name}:{file_config.source_path}"

        for root, dirs, files in os.walk(file_config.source_path, followlinks=file_config.follow_symlinks):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, file_config.source_path)

                # Check exclude patterns
                if self.matches_exclude_patterns(rel_path, file_config.exclude_patterns):
                    continue

                # Check include patterns
                if file_config.include_patterns and not self.matches_include_patterns(rel_path, file_config.include_patterns):
                    continue

                try:
                    file_stat = os.stat(file_path)
                    file_mtime = datetime.fromtimestamp(file_stat.st_mtime, timezone.utc)

                    # Check if file was modified since last backup
                    if file_mtime > last_backup_time:
                        # Calculate checksum
                        checksum = self.calculate_file_checksum(file_path)
                        cached_checksum = self.file_checksum_cache.get(cache_key, {}).get(rel_path)

                        # Check if file content changed
                        if not cached_checksum or checksum != cached_checksum:
                            changed_files.append({
                                'path': file_path,
                                'relative_path': rel_path,
                                'mtime': file_mtime,
                                'size': file_stat.st_size,
                                'checksum': checksum
                            })

                except (OSError, IOError) as e:
                    logger.warning(f"Error processing file {file_path}: {e}")

        return changed_files

    async def get_all_files(self, file_config: FileBackupConfig) -> List[Dict[str, Any]]:
        """Get all files for backup"""
        all_files = []

        for root, dirs, files in os.walk(file_config.source_path, followlinks=file_config.follow_symlinks):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, file_config.source_path)

                # Check exclude patterns
                if self.matches_exclude_patterns(rel_path, file_config.exclude_patterns):
                    continue

                # Check include patterns
                if file_config.include_patterns and not self.matches_include_patterns(rel_path, file_config.include_patterns):
                    continue

                try:
                    file_stat = os.stat(file_path)
                    file_mtime = datetime.fromtimestamp(file_stat.st_mtime, timezone.utc)
                    checksum = self.calculate_file_checksum(file_path) if file_config.checksum_verification else ""

                    all_files.append({
                        'path': file_path,
                        'relative_path': rel_path,
                        'mtime': file_mtime,
                        'size': file_stat.st_size,
                        'checksum': checksum
                    })

                except (OSError, IOError) as e:
                    logger.warning(f"Error processing file {file_path}: {e}")

        return all_files

    def matches_exclude_patterns(self, file_path: str, patterns: List[str]) -> bool:
        """Check if file matches any exclude patterns"""
        if not patterns:
            return False

        import fnmatch
        return any(fnmatch.fnmatch(file_path, pattern) for pattern in patterns)

    def matches_include_patterns(self, file_path: str, patterns: List[str]) -> bool:
        """Check if file matches any include patterns"""
        if not patterns:
            return True

        import fnmatch
        return any(fnmatch.fnmatch(file_path, pattern) for pattern in patterns)

    async def count_files_in_archive(self, archive_path: str) -> Tuple[int, int]:
        """Count files and directories in archive"""
        cmd = ['tar', '-tf', archive_path]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, _ = await process.communicate()
        if process.returncode != 0:
            return 0, 0

        files = stdout.decode().strip().split('\n')
        total_files = len(f for f in files if f and not f.endswith('/'))
        total_directories = len(f for f in files if f and f.endswith('/'))

        return total_files, total_directories

    async def get_uncompressed_size(self, path: str, file_config: FileBackupConfig) -> int:
        """Get uncompressed size of files to be backed up"""
        total_size = 0

        for root, dirs, files in os.walk(path, followlinks=file_config.follow_symlinks):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, path)

                # Check exclude patterns
                if self.matches_exclude_patterns(rel_path, file_config.exclude_patterns):
                    continue

                # Check include patterns
                if file_config.include_patterns and not self.matches_include_patterns(rel_path, file_config.include_patterns):
                    continue

                try:
                    total_size += os.path.getsize(file_path)
                except (OSError, IOError):
                    pass

        return total_size

    async def calculate_directory_size(self, directory: str) -> int:
        """Calculate total size of directory"""
        total_size = 0

        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                except (OSError, IOError):
                    pass

        return total_size

    def parse_rsync_stats(self, rsync_output: str) -> Tuple[int, int]:
        """Parse rsync statistics from output"""
        total_files = 0
        total_directories = 0

        for line in rsync_output.split('\n'):
            if 'Number of files:' in line:
                # Extract number from line like "Number of files: 1,234 (reg: 1,200, dir: 34)"
                parts = line.split(':')[1].strip()
                file_part = parts.split('(')[0].strip()
                total_files = int(file_part.replace(',', ''))
            elif 'Number of created files:' in line:
                # This might give us directory count
                pass

        return total_files, total_directories

    async def split_large_file(self, file_path: str, split_size_mb: int) -> List[str]:
        """Split large file into smaller chunks"""
        split_size_bytes = split_size_mb * 1024 * 1024
        base_name = file_path
        chunk_files = []

        # Use split command
        cmd = ['split', '-b', str(split_size_bytes), file_path, f"{base_name}.part_"]
        process = await asyncio.create_subprocess_exec(*cmd)
        await process.communicate()

        if process.returncode == 0:
            # Find generated chunk files
            dir_name = os.path.dirname(file_path)
            for file in os.listdir(dir_name):
                if file.startswith(os.path.basename(file_path) + '.part_'):
                    chunk_files.append(os.path.join(dir_name, file))

        return chunk_files

    async def verify_disk_space(self, temp_dir: str):
        """Verify sufficient disk space for backup"""
        stat = shutil.disk_usage(temp_dir)
        free_space_gb = stat.free / (1024 ** 3)
        threshold_gb = self.config['backup_settings']['disk_space_threshold_gb']

        if free_space_gb < threshold_gb:
            raise Exception(f"Insufficient disk space: {free_space_gb:.2f}GB available, {threshold_gb}GB required")

    def calculate_file_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    async def update_file_checksum_cache(self, result: Dict[str, Any]):
        """Update file checksum cache after successful backup"""
        backup_name = result['backup_name']
        file_config = self.config['file_backups'][backup_name]

        if isinstance(file_config, dict):
            file_config = FileBackupConfig(**file_config)

        cache_key = f"{backup_name}:{file_config.source_path}"
        self.file_checksum_cache[cache_key] = {}

        # Rebuild checksum cache for all files
        for root, dirs, files in os.walk(file_config.source_path, followlinks=file_config.follow_symlinks):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, file_config.source_path)

                try:
                    checksum = self.calculate_file_checksum(file_path)
                    self.file_checksum_cache[cache_key][rel_path] = checksum
                except (OSError, IOError):
                    pass

    def get_backup_status(self, backup_name: str) -> Dict[str, Any]:
        """Get backup status for a specific file configuration"""
        last_backup = self.last_backup_times.get(backup_name)

        return {
            'backup_name': backup_name,
            'last_backup_time': last_backup.isoformat() if last_backup else None,
            'backup_enabled': backup_name in self.config['file_backups'],
            'source_path': self.config['file_backups'][backup_name].get('source_path', '')
        }

    def get_all_backup_status(self) -> Dict[str, Any]:
        """Get backup status for all file configurations"""
        status = {}
        for backup_name in self.config['file_backups']:
            status[backup_name] = self.get_backup_status(backup_name)
        return status