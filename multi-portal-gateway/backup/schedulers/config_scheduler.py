#!/usr/bin/env python3
"""
Configuration Backup Scheduler - Handles backup operations for configurations

This scheduler manages backups for application configurations, environment files,
secrets, certificates, and other configuration data used by the DMLogn8n platform.
"""

import asyncio
import logging
import os
import subprocess
import tempfile
import shutil
import json
import yaml
import time
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import tarfile
import zipfile
from cryptography.fernet import Fernet
import boto3
import kubernetes

# Import backup service types
from backup_service import BackupMetadata, BackupType, BackupStatus, EncryptionManager

logger = logging.getLogger(__name__)

class ConfigType(Enum):
    """Configuration types"""
    APPLICATION = "application"
    ENVIRONMENT = "environment"
    SECRETS = "secrets"
    CERTIFICATES = "certificates"
    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"

class ConfigFormat(Enum):
    """Configuration file formats"""
    YAML = "yaml"
    JSON = "json"
    ENV = "env"
    PROPERTIES = "properties"
    TOML = "toml"
    XML = "xml"
    BINARY = "binary"

class BackupMethod(Enum):
    """Configuration backup methods"""
    FILE_COPY = "file_copy"
    ARCHIVE = "archive"
    EXPORT = "export"
    SECRET_DUMP = "secret_dump"

@dataclass
class ConfigBackupConfig:
    """Configuration backup configuration"""
    name: str
    source_paths: List[str]
    config_type: str
    backup_method: str
    config_format: str = "yaml"
    encryption_required: bool = True
    version_control: bool = False
    git_repository: Optional[str] = None
    sensitive_data: bool = False
    backup_separately: bool = False
    validation_schema: Optional[str] = None
    transformation_scripts: List[str] = None
    exclude_patterns: List[str] = None

@dataclass
class ConfigBackupResult:
    """Configuration backup operation result"""
    backup_name: str
    config_type: str
    backup_method: str
    backup_files: List[str]
    total_configs: int
    size_bytes: int
    compressed_size_bytes: int
    checksum: str
    validation_results: Dict[str, Any]
    secrets_encrypted: bool
    metadata: Dict[str, Any]

class ConfigScheduler:
    """Configuration backup scheduler implementation"""

    def __init__(self, backup_service):
        self.backup_service = backup_service
        self.config = self.load_config_config()
        self.encryption_manager = EncryptionManager()
        self.last_backup_times = {}
        self.config_validator = ConfigValidator()

    def load_config_config(self) -> Dict[str, Any]:
        """Load configuration backup configuration"""
        config_path = "/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/config/config_backup.yaml"

        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config backup config: {e}")
            return self.get_default_config_config()

    def get_default_config_config(self) -> Dict[str, Any]:
        """Get default configuration backup settings"""
        return {
            'config_backups': {
                'application_config': ConfigBackupConfig(
                    name='application_config',
                    source_paths=[
                        '/home/activeloguser/DMLogn8n/multi-portal-gateway/config',
                        '/home/activeloguser/DMLogn8n/multi-portal-gateway/settings'
                    ],
                    config_type=ConfigType.APPLICATION.value,
                    backup_method=BackupMethod.ARCHIVE.value,
                    config_format=ConfigFormat.YAML.value,
                    encryption_required=False,
                    version_control=True,
                    git_repository='git@github.com:dmlogn8n/config-backup.git',
                    validation_schema='/home/activeloguser/DMLogn8n/multi-portal-gateway/schemas/config-schema.json'
                ),
                'environment_config': ConfigBackupConfig(
                    name='environment_config',
                    source_paths=[
                        '/home/activeloguser/DMLogn8n/.env',
                        '/home/activeloguser/DMLogn8n/multi-portal-gateway/.env.production',
                        '/home/activeloguser/DMLogn8n/multi-portal-gateway/.env.staging'
                    ],
                    config_type=ConfigType.ENVIRONMENT.value,
                    backup_method=BackupMethod.FILE_COPY.value,
                    config_format=ConfigFormat.ENV.value,
                    encryption_required=True,
                    sensitive_data=True,
                    backup_separately=True
                ),
                'secrets_config': ConfigBackupConfig(
                    name='secrets_config',
                    source_paths=[
                        '/home/activeloguser/DMLogn8n/multi-portal-gateway/secrets',
                        '/home/activeloguser/DMLogn8n/multi-portal-gateway/certs'
                    ],
                    config_type=ConfigType.SECRETS.value,
                    backup_method=BackupMethod.SECRET_DUMP.value,
                    encryption_required=True,
                    sensitive_data=True,
                    backup_separately=True,
                    exclude_patterns=['*.tmp', '*.bak', '.gitkeep']
                ),
                'kubernetes_config': ConfigBackupConfig(
                    name='kubernetes_config',
                    source_paths=[
                        '/home/activeloguser/DMLogn8n/multi-portal-gateway/k8s',
                        '/home/activeloguser/DMLogn8n/multi-portal-gateway/helm'
                    ],
                    config_type=ConfigType.KUBERNETES.value,
                    backup_method=BackupMethod.EXPORT.value,
                    config_format=ConfigFormat.YAML.value,
                    encryption_required=False,
                    version_control=True
                ),
                'docker_config': ConfigBackupConfig(
                    name='docker_config',
                    source_paths=[
                        '/home/activeloguser/DMLogn8n/multi-portal-gateway/docker',
                        '/home/activeloguser/DMLogn8n/multi-portal-gateway/docker-compose.yml'
                    ],
                    config_type=ConfigType.DOCKER.value,
                    backup_method=BackupMethod.ARCHIVE.value,
                    config_format=ConfigFormat.YAML.value,
                    encryption_required=False
                ),
                'database_config': ConfigBackupConfig(
                    name='database_config',
                    source_paths=[
                        '/home/activeloguser/DMLogn8n/multi-portal-gateway/database'
                    ],
                    config_type=ConfigType.DATABASE.value,
                    backup_method=BackupMethod.ARCHIVE.value,
                    config_format=ConfigFormat.YAML.value,
                    encryption_required=True,
                    sensitive_data=True
                ),
                'infrastructure_config': ConfigBackupConfig(
                    name='infrastructure_config',
                    source_paths=[
                        '/home/activeloguser/DMLogn8n/multi-portal-gateway/terraform',
                        '/home/activeloguser/DMLogn8n/multi-portal-gateway/ansible'
                    ],
                    config_type=ConfigType.INFRASTRUCTURE.value,
                    backup_method=BackupMethod.ARCHIVE.value,
                    config_format=ConfigFormat.YAML.value,
                    encryption_required=True,
                    version_control=True
                )
            },
            'backup_settings': {
                'parallel_backups': False,  # Configs are usually small, sequential is fine
                'timeout_seconds': 1800,  # 30 minutes
                'retry_attempts': 3,
                'retry_delay_seconds': 30,
                'validate_configs': True,
                'backup_sensitive_separately': True,
                'git_auto_commit': True,
                'git_commit_message_template': "Config backup {backup_id} - {timestamp}"
            },
            'security_settings': {
                'encrypt_sensitive_data': True,
                'use_aws_kms': True,
                'kms_key_id': os.getenv('AWS_KMS_KEY_ID'),
                'secrets_manager_regions': ['us-east-1', 'us-west-2'],
                'certificate_backup_enabled': True,
                'ssh_key_backup_enabled': True
            },
            'retention_settings': {
                'daily_retention_days': 30,
                'weekly_retention_weeks': 12,
                'monthly_retention_months': 24,
                'yearly_retention_years': 10,
                'keep_sensitive_versions': 90
            }
        }

    async def execute_backup(self, backup_metadata: BackupMetadata, backup_type: BackupType) -> Dict[str, Any]:
        """Execute configuration backup operation"""
        logger.info(f"Starting configuration backup: {backup_metadata.backup_id}")

        start_time = time.time()
        backup_results = []
        temp_dir = tempfile.mkdtemp(prefix=f"config_backup_{backup_metadata.backup_id}_")

        try:
            # Get config configs to backup based on source path and backup type
            config_configs = self.get_config_configs_for_backup(backup_metadata.source_path, backup_type)

            # Execute backups
            backup_results = await self.execute_config_backups(
                config_configs, backup_type, temp_dir, backup_metadata
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
            for result in backup_results:
                backup_name = result['backup_name']
                self.last_backup_times[backup_name] = datetime.now(timezone.utc)

                # Commit to version control if enabled
                await self.commit_to_version_control(result, backup_metadata)

            # Clean up temporary directory
            shutil.rmtree(temp_dir)

            duration = time.time() - start_time
            logger.info(f"Configuration backup completed in {duration:.2f}s: {backup_metadata.backup_id}")

            return {
                'size_bytes': total_size,
                'compressed_size_bytes': compressed_size,
                'checksum': checksum,
                'storage_path': storage_path,
                'backup_results': backup_results,
                'duration_seconds': duration,
                'metadata': {
                    'config_backups_count': len(backup_results),
                    'total_configs_backed_up': sum(r['total_configs'] for r in backup_results),
                    'sensitive_configs_count': sum(1 for r in backup_results if r.get('secrets_encrypted', False))
                }
            }

        except Exception as e:
            logger.error(f"Configuration backup failed: {backup_metadata.backup_id} - {e}")
            # Clean up temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise

    def get_config_configs_for_backup(self, source_path: str, backup_type: BackupType) -> List[ConfigBackupConfig]:
        """Get list of configuration configs to backup"""
        config_configs = []

        for name, config in self.config['config_backups'].items():
            if isinstance(config, dict):
                config = ConfigBackupConfig(**config)

            # Filter by source path if specified
            if source_path and not self.matches_source_path(config, source_path):
                continue

            config_configs.append(config)

        return config_configs

    def matches_source_path(self, config: ConfigBackupConfig, source_path: str) -> bool:
        """Check if config matches source path filter"""
        filter_path = os.path.abspath(source_path)

        for config_path in config.source_paths:
            config_abs_path = os.path.abspath(config_path)
            if filter_path.startswith(config_abs_path) or config_abs_path.startswith(filter_path):
                return True

        return False

    async def execute_config_backups(self, config_configs: List[ConfigBackupConfig],
                                   backup_type: BackupType, temp_dir: str,
                                   backup_metadata: BackupMetadata) -> List[Dict[str, Any]]:
        """Execute configuration backups"""
        backup_results = []

        for config_config in config_configs:
            try:
                result = await self.backup_single_config_config(
                    config_config, backup_type, temp_dir, backup_metadata
                )
                backup_results.append(result)
            except Exception as e:
                logger.error(f"Config backup failed for {config_config.name}: {e}")

        return backup_results

    async def backup_single_config_config(self, config_config: ConfigBackupConfig, backup_type: BackupType,
                                        temp_dir: str, backup_metadata: BackupMetadata) -> Dict[str, Any]:
        """Backup a single configuration config"""
        logger.info(f"Backing up config: {config_config.name}")

        retry_count = 0
        max_retries = self.config['backup_settings']['retry_attempts']

        while retry_count <= max_retries:
            try:
                if config_config.backup_method == BackupMethod.FILE_COPY.value:
                    result = await self.backup_file_copy(config_config, backup_type, temp_dir, backup_metadata)
                elif config_config.backup_method == BackupMethod.ARCHIVE.value:
                    result = await self.backup_archive(config_config, backup_type, temp_dir, backup_metadata)
                elif config_config.backup_method == BackupMethod.EXPORT.value:
                    result = await self.backup_export(config_config, backup_type, temp_dir, backup_metadata)
                elif config_config.backup_method == BackupMethod.SECRET_DUMP.value:
                    result = await self.backup_secret_dump(config_config, backup_type, temp_dir, backup_metadata)
                else:
                    raise ValueError(f"Unsupported backup method: {config_config.backup_method}")

                logger.info(f"Config backup completed: {config_config.name}")
                return result

            except Exception as e:
                retry_count += 1
                if retry_count <= max_retries:
                    delay = self.config['backup_settings']['retry_delay_seconds']
                    logger.warning(f"Config backup failed for {config_config.name}, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    raise

    async def backup_file_copy(self, config_config: ConfigBackupConfig, backup_type: BackupType,
                             temp_dir: str, backup_metadata: BackupMetadata) -> Dict[str, Any]:
        """Backup configuration files via direct copy"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(temp_dir, f"{config_config.name}_{timestamp}")
        os.makedirs(backup_dir, exist_ok=True)

        backup_files = []
        total_configs = 0
        total_size = 0

        for source_path in config_config.source_paths:
            if not os.path.exists(source_path):
                logger.warning(f"Source path does not exist: {source_path}")
                continue

            if os.path.isfile(source_path):
                # Single file backup
                dest_path = os.path.join(backup_dir, os.path.basename(source_path))
                shutil.copy2(source_path, dest_path)
                backup_files.append(os.path.basename(dest_path))
                total_configs += 1
                total_size += os.path.getsize(source_path)

            elif os.path.isdir(source_path):
                # Directory backup
                for root, dirs, files in os.walk(source_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, source_path)

                        # Check exclude patterns
                        if self.matches_exclude_patterns(rel_path, config_config.exclude_patterns):
                            continue

                        dest_path = os.path.join(backup_dir, rel_path)
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        shutil.copy2(file_path, dest_path)
                        backup_files.append(rel_path)
                        total_configs += 1
                        total_size += os.path.getsize(file_path)

        # Validate configs if enabled
        validation_results = {}
        if self.config['backup_settings']['validate_configs']:
            validation_results = await self.validate_backuped_configs(
                backup_dir, config_config
            )

        # Encrypt if required
        secrets_encrypted = False
        if config_config.encryption_required:
            secrets_encrypted = await self.encrypt_sensitive_configs(
                backup_dir, config_config
            )

        # Create archive
        archive_path = backup_dir + '.tar.gz'
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(backup_dir, arcname=os.path.basename(backup_dir))

        compressed_size = os.path.getsize(archive_path)
        checksum = self.calculate_file_checksum(archive_path)

        # Clean up temporary directory
        shutil.rmtree(backup_dir)

        return {
            'backup_name': config_config.name,
            'config_type': config_config.config_type,
            'backup_method': BackupMethod.FILE_COPY.value,
            'backup_files': [os.path.basename(archive_path)],
            'total_configs': total_configs,
            'size_bytes': total_size,
            'compressed_size_bytes': compressed_size,
            'checksum': checksum,
            'validation_results': validation_results,
            'secrets_encrypted': secrets_encrypted,
            'metadata': {
                'source_paths': config_config.source_paths,
                'config_format': config_config.config_format
            }
        }

    async def backup_archive(self, config_config: ConfigBackupConfig, backup_type: BackupType,
                           temp_dir: str, backup_metadata: BackupMetadata) -> Dict[str, Any]:
        """Backup configuration files via archive"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        archive_name = f"{config_config.name}_{backup_type.value}_{timestamp}.tar.gz"
        archive_path = os.path.join(temp_dir, archive_name)

        # Create archive
        with tarfile.open(archive_path, 'w:gz') as tar:
            for source_path in config_config.source_paths:
                if not os.path.exists(source_path):
                    logger.warning(f"Source path does not exist: {source_path}")
                    continue

                # Add to archive with relative path
                arcname = os.path.basename(source_path.rstrip('/'))
                tar.add(source_path, arcname=arcname, exclude=self._get_exclude_filter(config_config.exclude_patterns))

        # Get statistics
        total_configs, total_size = await self.count_files_in_archive(archive_path)
        compressed_size = os.path.getsize(archive_path)
        checksum = self.calculate_file_checksum(archive_path)

        # Validate if enabled
        validation_results = {}
        if self.config['backup_settings']['validate_configs']:
            temp_extract = tempfile.mkdtemp()
            try:
                with tarfile.open(archive_path, 'r:gz') as tar:
                    tar.extractall(temp_extract)
                validation_results = await self.validate_backuped_configs(
                    temp_extract, config_config
                )
            finally:
                shutil.rmtree(temp_extract)

        # Encrypt if required
        secrets_encrypted = False
        if config_config.encryption_required:
            encrypted_path = archive_path + '.enc'
            encrypted_data, key_id = self.encryption_manager.encrypt_data(
                open(archive_path, 'rb').read()
            )
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
            os.remove(archive_path)
            archive_path = encrypted_path
            secrets_encrypted = True

        return {
            'backup_name': config_config.name,
            'config_type': config_config.config_type,
            'backup_method': BackupMethod.ARCHIVE.value,
            'backup_files': [os.path.basename(archive_path)],
            'total_configs': total_configs,
            'size_bytes': total_size,
            'compressed_size_bytes': compressed_size,
            'checksum': checksum,
            'validation_results': validation_results,
            'secrets_encrypted': secrets_encrypted,
            'metadata': {
                'source_paths': config_config.source_paths,
                'config_format': config_config.config_format
            }
        }

    async def backup_export(self, config_config: ConfigBackupConfig, backup_type: BackupType,
                          temp_dir: str, backup_metadata: BackupMetadata) -> Dict[str, Any]:
        """Backup configuration via export (e.g., Kubernetes resources)"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(temp_dir, f"{config_config.name}_export_{timestamp}")
        os.makedirs(backup_dir, exist_ok=True)

        backup_files = []
        total_configs = 0
        total_size = 0

        if config_config.config_type == ConfigType.KUBERNETES.value:
            # Export Kubernetes resources
            await self.export_kubernetes_resources(backup_dir, config_config)
        elif config_config.config_type == ConfigType.DOCKER.value:
            # Export Docker configurations
            await self.export_docker_configs(backup_dir, config_config)
        else:
            # Default to file copy for other types
            return await self.backup_file_copy(config_config, backup_type, temp_dir, backup_metadata)

        # Count exported files
        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                file_path = os.path.join(root, file)
                total_configs += 1
                total_size += os.path.getsize(file_path)

        # Create archive
        archive_path = backup_dir + '.tar.gz'
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(backup_dir, arcname=os.path.basename(backup_dir))

        compressed_size = os.path.getsize(archive_path)
        checksum = self.calculate_file_checksum(archive_path)

        # Clean up temporary directory
        shutil.rmtree(backup_dir)

        return {
            'backup_name': config_config.name,
            'config_type': config_config.config_type,
            'backup_method': BackupMethod.EXPORT.value,
            'backup_files': [os.path.basename(archive_path)],
            'total_configs': total_configs,
            'size_bytes': total_size,
            'compressed_size_bytes': compressed_size,
            'checksum': checksum,
            'validation_results': {},
            'secrets_encrypted': config_config.encryption_required,
            'metadata': {
                'export_type': config_config.config_type,
                'source_paths': config_config.source_paths
            }
        }

    async def backup_secret_dump(self, config_config: ConfigBackupConfig, backup_type: BackupType,
                               temp_dir: str, backup_metadata: BackupMetadata) -> Dict[str, Any]:
        """Backup secrets and sensitive configuration"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(temp_dir, f"{config_config.name}_secrets_{timestamp}")
        os.makedirs(backup_dir, exist_ok=True)

        backup_files = []
        total_configs = 0
        total_size = 0

        # Dump secrets from various sources
        await self.dump_secrets_from_vault(backup_dir)
        await self.dump_secrets_from_aws(backup_dir)
        await self.dump_certificates(backup_dir)
        await self.dump_ssh_keys(backup_dir)

        # Copy other secret files
        for source_path in config_config.source_paths:
            if os.path.exists(source_path):
                if os.path.isfile(source_path):
                    dest_path = os.path.join(backup_dir, os.path.basename(source_path))
                    shutil.copy2(source_path, dest_path)
                    backup_files.append(os.path.basename(dest_path))
                    total_configs += 1
                    total_size += os.path.getsize(source_path)
                elif os.path.isdir(source_path):
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            if self.is_secret_file(file):
                                file_path = os.path.join(root, file)
                                rel_path = os.path.relpath(file_path, source_path)
                                dest_path = os.path.join(backup_dir, rel_path)
                                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                                shutil.copy2(file_path, dest_path)
                                backup_files.append(rel_path)
                                total_configs += 1
                                total_size += os.path.getsize(file_path)

        # Encrypt all secrets
        await self.encrypt_all_secrets(backup_dir)

        # Create encrypted archive
        archive_path = backup_dir + '.tar.gz'
        with tarfile.open(archive_path, 'w:gz') as tar:
            tar.add(backup_dir, arcname=os.path.basename(backup_dir))

        compressed_size = os.path.getsize(archive_path)
        checksum = self.calculate_file_checksum(archive_path)

        # Double encrypt sensitive backup
        encrypted_archive_path = archive_path + '.enc'
        encrypted_data, key_id = self.encryption_manager.encrypt_data(
            open(archive_path, 'rb').read()
        )
        with open(encrypted_archive_path, 'wb') as f:
            f.write(encrypted_data)
        os.remove(archive_path)

        # Clean up temporary directory
        shutil.rmtree(backup_dir)

        return {
            'backup_name': config_config.name,
            'config_type': config_config.config_type,
            'backup_method': BackupMethod.SECRET_DUMP.value,
            'backup_files': [os.path.basename(encrypted_archive_path)],
            'total_configs': total_configs,
            'size_bytes': total_size,
            'compressed_size_bytes': compressed_size,
            'checksum': checksum,
            'validation_results': {},
            'secrets_encrypted': True,
            'metadata': {
                'encryption_key_id': key_id,
                'secret_sources': ['vault', 'aws', 'certificates', 'ssh_keys', 'files']
            }
        }

    async def export_kubernetes_resources(self, backup_dir: str, config_config: ConfigBackupConfig):
        """Export Kubernetes resources"""
        try:
            # Initialize Kubernetes client
            kubernetes.config.load_kube_config()
            v1 = kubernetes.client.CoreV1Api()
            apps_v1 = kubernetes.client.AppsV1Api()

            # Export different resource types
            resource_types = [
                ('pods', v1.list_namespaced_pod),
                ('services', v1.list_namespaced_service),
                ('configmaps', v1.list_namespaced_config_map),
                ('secrets', v1.list_namespaced_secret),
                ('deployments', apps_v1.list_namespaced_deployment),
                ('statefulsets', apps_v1.list_namespaced_stateful_set)
            ]

            # Get namespaces (default to 'dmlogn8n' namespace)
            namespaces = ['dmlogn8n', 'default']

            for namespace in namespaces:
                for resource_type, list_func in resource_types:
                    try:
                        resources = list_func(namespace=namespace)
                        output_file = os.path.join(backup_dir, f"{namespace}_{resource_type}.yaml")

                        with open(output_file, 'w') as f:
                            for resource in resources.items:
                                # Convert Kubernetes object to YAML
                                yaml.dump(resource.to_dict(), f, default_flow_style=False)
                                f.write('---\n')

                    except Exception as e:
                        logger.warning(f"Failed to export {resource_type} from namespace {namespace}: {e}")

        except Exception as e:
            logger.error(f"Failed to export Kubernetes resources: {e}")

    async def export_docker_configs(self, backup_dir: str, config_config: ConfigBackupConfig):
        """Export Docker configurations"""
        try:
            # Export Docker Compose configurations
            for source_path in config_config.source_paths:
                if source_path.endswith('docker-compose.yml') or source_path.endswith('docker-compose.yaml'):
                    shutil.copy2(source_path, backup_dir)

            # Export running containers info
            cmd = ['docker', 'ps', '-a', '--format', 'json']
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                containers_info = stdout.decode()
                with open(os.path.join(backup_dir, 'docker_containers.json'), 'w') as f:
                    f.write(containers_info)

            # Export images list
            cmd = ['docker', 'images', '--format', 'json']
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                images_info = stdout.decode()
                with open(os.path.join(backup_dir, 'docker_images.json'), 'w') as f:
                    f.write(images_info)

        except Exception as e:
            logger.error(f"Failed to export Docker configurations: {e}")

    async def dump_secrets_from_vault(self, backup_dir: str):
        """Dump secrets from HashiCorp Vault"""
        try:
            # This would integrate with Vault API
            # Implementation depends on Vault configuration
            vault_addr = os.getenv('VAULT_ADDR')
            vault_token = os.getenv('VAULT_TOKEN')

            if vault_addr and vault_token:
                # Implement Vault API calls to dump secrets
                vault_file = os.path.join(backup_dir, 'vault_secrets.json')
                # Placeholder for Vault integration
                with open(vault_file, 'w') as f:
                    json.dump({"vault_secrets": "placeholder"}, f)

        except Exception as e:
            logger.warning(f"Failed to dump Vault secrets: {e}")

    async def dump_secrets_from_aws(self, backup_dir: str):
        """Dump secrets from AWS Secrets Manager"""
        try:
            session = boto3.Session()
            client = session.client('secretsmanager')

            # List all secrets
            secrets = []
            paginator = client.get_paginator('list_secrets')
            for page in paginator.paginate():
                secrets.extend(page['SecretList'])

            # Dump secret values
            secrets_data = {}
            for secret in secrets:
                try:
                    secret_value = client.get_secret_value(SecretId=secret['ARN'])
                    secrets_data[secret['Name']] = secret_value['SecretString']
                except Exception as e:
                    logger.warning(f"Failed to retrieve secret {secret['Name']}: {e}")

            with open(os.path.join(backup_dir, 'aws_secrets.json'), 'w') as f:
                json.dump(secrets_data, f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to dump AWS secrets: {e}")

    async def dump_certificates(self, backup_dir: str):
        """Dump SSL/TLS certificates"""
        try:
            cert_dir = os.path.join(backup_dir, 'certificates')
            os.makedirs(cert_dir, exist_ok=True)

            # Copy certificates from known locations
            cert_paths = [
                '/etc/ssl/certs',
                '/home/activeloguser/DMLogn8n/multi-portal-gateway/certs',
                '/etc/letsencrypt/live'
            ]

            for cert_path in cert_paths:
                if os.path.exists(cert_path):
                    dest_path = os.path.join(cert_dir, os.path.basename(cert_path.rstrip('/')))
                    if os.path.isdir(cert_path):
                        shutil.copytree(cert_path, dest_path, dirs_exist_ok=True)
                    else:
                        shutil.copy2(cert_path, dest_path)

        except Exception as e:
            logger.warning(f"Failed to dump certificates: {e}")

    async def dump_ssh_keys(self, backup_dir: str):
        """Dump SSH keys"""
        try:
            ssh_dir = os.path.join(backup_dir, 'ssh_keys')
            os.makedirs(ssh_dir, exist_ok=True)

            # Copy SSH keys from user's .ssh directory
            user_ssh_dir = os.path.expanduser('~/.ssh')
            if os.path.exists(user_ssh_dir):
                for file in os.listdir(user_ssh_dir):
                    if file.endswith('.pub') or file.startswith('id_'):
                        shutil.copy2(
                            os.path.join(user_ssh_dir, file),
                            os.path.join(ssh_dir, file)
                        )

        except Exception as e:
            logger.warning(f"Failed to dump SSH keys: {e}")

    def is_secret_file(self, filename: str) -> bool:
        """Check if file is likely to contain secrets"""
        secret_indicators = [
            'key', 'secret', 'password', 'credential', 'cert',
            'token', 'api_key', 'private', '.pem', '.key', '.crt'
        ]

        filename_lower = filename.lower()
        return any(indicator in filename_lower for indicator in secret_indicators)

    async def encrypt_all_secrets(self, backup_dir: str):
        """Encrypt all files in secrets backup directory"""
        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'rb') as f:
                        data = f.read()
                    encrypted_data, key_id = self.encryption_manager.encrypt_data(data)
                    with open(file_path + '.enc', 'wb') as f:
                        f.write(encrypted_data)
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Failed to encrypt secret file {file_path}: {e}")

    async def encrypt_sensitive_configs(self, backup_dir: str, config_config: ConfigBackupConfig) -> bool:
        """Encrypt sensitive configuration files"""
        encrypted_files = []

        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if self.is_secret_file(file):
                    try:
                        with open(file_path, 'rb') as f:
                            data = f.read()
                        encrypted_data, key_id = self.encryption_manager.encrypt_data(data)
                        with open(file_path + '.enc', 'wb') as f:
                            f.write(encrypted_data)
                        os.remove(file_path)
                        encrypted_files.append(file)
                    except Exception as e:
                        logger.warning(f"Failed to encrypt sensitive file {file_path}: {e}")

        return len(encrypted_files) > 0

    async def validate_backuped_configs(self, backup_dir: str, config_config: ConfigBackupConfig) -> Dict[str, Any]:
        """Validate backed up configuration files"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'validated_files': []
        }

        if not config_config.validation_schema:
            return validation_results

        try:
            # Load validation schema
            with open(config_config.validation_schema, 'r') as f:
                schema = json.load(f)

            # Validate each configuration file
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    if file.endswith(('.yaml', '.yml', '.json')):
                        file_path = os.path.join(root, file)
                        try:
                            validation_result = await self.config_validator.validate_file(
                                file_path, schema, config_config.config_format
                            )
                            validation_results['validated_files'].append({
                                'file': file,
                                'valid': validation_result['valid'],
                                'errors': validation_result.get('errors', [])
                            })

                            if not validation_result['valid']:
                                validation_results['valid'] = False
                                validation_results['errors'].extend([
                                    f"{file}: {error}" for error in validation_result.get('errors', [])
                                ])

                        except Exception as e:
                            validation_results['warnings'].append(f"Failed to validate {file}: {e}")

        except Exception as e:
            validation_results['warnings'].append(f"Configuration validation failed: {e}")

        return validation_results

    async def commit_to_version_control(self, result: Dict[str, Any], backup_metadata: BackupMetadata):
        """Commit backup to version control if enabled"""
        backup_name = result['backup_name']
        config_config = None

        # Find the config config for this backup
        for name, config in self.config['config_backups'].items():
            if isinstance(config, dict):
                config = ConfigBackupConfig(**config)
            if config.name == backup_name and config.version_control:
                config_config = config
                break

        if not config_config:
            return

        try:
            # Initialize git repository if needed
            git_dir = tempfile.mkdtemp(prefix=f"git_backup_{backup_name}_")

            # Clone or initialize repository
            if config_config.git_repository:
                cmd = ['git', 'clone', config_config.git_repository, git_dir]
                process = await asyncio.create_subprocess_exec(*cmd)
                await process.communicate()
            else:
                os.makedirs(git_dir)
                cmd = ['git', 'init']
                process = await asyncio.create_subprocess_exec(*cmd, cwd=git_dir)
                await process.communicate()

            # Copy backup files to git directory
            for backup_file in result['backup_files']:
                source_path = os.path.join(
                    os.path.dirname(backup_metadata.storage_path),
                    backup_file
                )
                dest_path = os.path.join(git_dir, backup_file)
                shutil.copy2(source_path, dest_path)

            # Add and commit files
            cmd = ['git', 'add', '.']
            process = await asyncio.create_subprocess_exec(*cmd, cwd=git_dir)
            await process.communicate()

            commit_message = self.config['backup_settings']['git_commit_message_template'].format(
                backup_id=backup_metadata.backup_id,
                timestamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            )

            cmd = ['git', 'commit', '-m', commit_message]
            process = await asyncio.create_subprocess_exec(*cmd, cwd=git_dir)
            await process.communicate()

            # Push to remote if repository is configured
            if config_config.git_repository:
                cmd = ['git', 'push']
                process = await asyncio.create_subprocess_exec(*cmd, cwd=git_dir)
                await process.communicate()

            # Clean up
            shutil.rmtree(git_dir)

            logger.info(f"Configuration backup committed to version control: {backup_name}")

        except Exception as e:
            logger.error(f"Failed to commit configuration backup to version control: {e}")

    async def create_backup_archive(self, backup_results: List[Dict[str, Any]],
                                  temp_dir: str, backup_metadata: BackupMetadata) -> str:
        """Create consolidated configuration backup archive"""
        archive_name = f"config_backup_{backup_metadata.backup_id}.tar.gz"
        archive_path = os.path.join(temp_dir, archive_name)

        # Create manifest file
        manifest_path = os.path.join(temp_dir, 'manifest.json')
        manifest = {
            'backup_id': backup_metadata.backup_id,
            'backup_type': backup_metadata.backup_type,
            'created_at': backup_metadata.created_at.isoformat(),
            'config_backups': backup_results,
            'total_size': sum(r['size_bytes'] for r in backup_results),
            'total_compressed_size': sum(r['compressed_size_bytes'] for r in backup_results),
            'total_configs': sum(r['total_configs'] for r in backup_results)
        }

        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2, default=str)

        # Create archive
        with tarfile.open(archive_path, 'w:gz') as tar:
            # Add all backup files
            for result in backup_results:
                for backup_file in result['backup_files']:
                    file_path = os.path.join(temp_dir, backup_file)
                    if os.path.exists(file_path):
                        tar.add(file_path, arcname=backup_file)

            # Add manifest
            tar.add(manifest_path, arcname='manifest.json')

        return archive_path

    async def count_files_in_archive(self, archive_path: str) -> Tuple[int, int]:
        """Count files and total size in archive"""
        total_files = 0
        total_size = 0

        with tarfile.open(archive_path, 'r:gz') as tar:
            for member in tar.getmembers():
                if member.isfile():
                    total_files += 1
                    total_size += member.size

        return total_files, total_size

    def _get_exclude_filter(self, exclude_patterns: List[str]):
        """Get exclude filter for tarfile"""
        if not exclude_patterns:
            return None

        def exclude_filter(tarinfo):
            import fnmatch
            return any(fnmatch.fnmatch(tarinfo.name, pattern) for pattern in exclude_patterns)

        return exclude_filter

    def matches_exclude_patterns(self, file_path: str, patterns: List[str]) -> bool:
        """Check if file matches any exclude patterns"""
        if not patterns:
            return False

        import fnmatch
        return any(fnmatch.fnmatch(file_path, pattern) for pattern in patterns)

    def calculate_file_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def get_backup_status(self, backup_name: str) -> Dict[str, Any]:
        """Get backup status for a specific configuration"""
        last_backup = self.last_backup_times.get(backup_name)

        return {
            'backup_name': backup_name,
            'last_backup_time': last_backup.isoformat() if last_backup else None,
            'backup_enabled': backup_name in self.config['config_backups'],
            'config_type': self.config['config_backups'][backup_name].get('config_type', '')
        }

    def get_all_backup_status(self) -> Dict[str, Any]:
        """Get backup status for all configurations"""
        status = {}
        for backup_name in self.config['config_backups']:
            status[backup_name] = self.get_backup_status(backup_name)
        return status

class ConfigValidator:
    """Configuration file validator"""

    async def validate_file(self, file_path: str, schema: Dict[str, Any], config_format: str) -> Dict[str, Any]:
        """Validate configuration file against schema"""
        result = {'valid': True, 'errors': []}

        try:
            if config_format in ['yaml', 'yml']:
                with open(file_path, 'r') as f:
                    data = yaml.safe_load(f)
            elif config_format == 'json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
            else:
                result['errors'].append(f"Unsupported config format: {config_format}")
                result['valid'] = False
                return result

            # Perform schema validation (basic implementation)
            if not isinstance(data, dict):
                result['errors'].append("Configuration must be a dictionary/object")
                result['valid'] = False

            # Add more sophisticated validation logic here
            # This could use jsonschema library for JSON schema validation

        except Exception as e:
            result['errors'].append(f"Validation error: {e}")
            result['valid'] = False

        return result