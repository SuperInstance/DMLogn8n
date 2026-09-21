#!/usr/bin/env python3
"""
GCS Storage Backend - Google Cloud Storage-based backup storage

This storage backend provides Google Cloud Storage with lifecycle management,
encryption, cross-region replication, and advanced features for backup files.
"""

import asyncio
import logging
import os
import json
import time
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from google.cloud import storage
from google.api_core import retry
from google.api_core.exceptions import GoogleAPIError, NotFound, Forbidden
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
from concurrent.futures import ThreadPoolExecutor
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class GCSStorageStatus(Enum):
    """GCS storage status"""
    AVAILABLE = "available"
    UNAUTHORIZED = "unauthorized"
    BUCKET_NOT_FOUND = "bucket_not_found"
    QUOTA_EXCEEDED = "quota_exceeded"
    ERROR = "error"

class GCSStorageClass(Enum):
    """GCS storage classes"""
    STANDARD = "STANDARD"
    NEARLINE = "NEARLINE"
    COLDLINE = "COLDLINE"
    ARCHIVE = "ARCHIVE"

class GCSEncryptionMethod(Enum):
    """GCS encryption methods"""
    NONE = "none"
    SERVER_DEFAULT = "server_default"
   _CUSTOMER_MANAGED = "customer_managed"
    CMEK = "cmek"

@dataclass
class GCSStorageConfig:
    """GCS storage configuration"""
    bucket_name: str
    project_id: Optional[str] = None
    credentials_path: Optional[str] = None
    storage_class: str = "STANDARD"
    encryption_method: str = "server_default"
    encryption_key: Optional[str] = None
    bucket_prefix: str = "backups/"
    chunk_size_mb: int = 64
    max_concurrency: int = 10
    cross_region_replication: bool = False
    replication_regions: List[str] = None
    lifecycle_management: bool = True
    lifecycle_days_standard: int = 30
    lifecycle_days_nearline: int = 90
    lifecycle_days_coldline: int = 365
    versioning: bool = True
    uniform_bucket_level_access: bool = True
    retention_policy_days: Optional[int] = None
    logging_enabled: bool = True
    requester_pays: bool = False
    metadata_database: str = "gcs_storage.db"
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    timeout_seconds: int = 300

@dataclass
class GCSUploadResult:
    """GCS upload operation result"""
    bucket: str
    name: str
    etag: str
    generation: Optional[int]
    size_bytes: int
    storage_class: str
    encryption: str
    upload_time_seconds: float
    md5_hash: str
    crc32c: str

class GCSStorage:
    """Google Cloud Storage backend for backups"""

    def __init__(self, config: Dict[str, Any]):
        if isinstance(config, dict):
            self.config = GCSStorageConfig(**config)
        else:
            self.config = config

        self.client = None
        self.bucket = None
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrency)
        self.status = GCSStorageStatus.INITIALIZING
        self.encryption_manager = None

        # Initialize GCS client and resources
        self.init_gcs_client()
        self.init_encryption_manager()
        self.init_bucket()
        self.init_lifecycle()
        self.init_replication()

        logger.info(f"GCS storage backend initialized: {self.config.bucket_name}")

    def init_gcs_client(self):
        """Initialize GCS client with configuration"""
        try:
            # Set up credentials
            if self.config.credentials_path:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.config.credentials_path

            # Create client with retry configuration
            retry_strategy = retry.Retry(
                initial=self.config.retry_delay_seconds,
                maximum=self.config.retry_attempts,
                multiplier=2.0,
                deadline=self.config.timeout_seconds
            )

            if self.config.project_id:
                self.client = storage.Client(
                    project=self.config.project_id,
                    retry=retry_strategy
                )
            else:
                self.client = storage.Client(retry=retry_strategy)

            # Get bucket reference
            self.bucket = self.client.bucket(self.config.bucket_name)

            # Test connection
            self.bucket.reload()
            self.status = GCSStorageStatus.AVAILABLE

        except NotFound:
            self.status = GCSStorageStatus.BUCKET_NOT_FOUND
            logger.error(f"GCS bucket not found: {self.config.bucket_name}")
        except Forbidden:
            self.status = GCSStorageStatus.UNAUTHORIZED
            logger.error(f"GCS access denied: {self.config.bucket_name}")
        except DefaultCredentialsError:
            self.status = GCSStorageStatus.UNAUTHORIZED
            logger.error("GCP credentials not found")
        except Exception as e:
            self.status = GCSStorageStatus.ERROR
            logger.error(f"GCS client initialization failed: {e}")

    def init_encryption_manager(self):
        """Initialize encryption manager"""
        if self.config.encryption_method == GCSEncryptionMethod.CUSTOMER_MANAGED.value:
            from backup_service import EncryptionManager
            self.encryption_manager = EncryptionManager()

    def init_bucket(self):
        """Initialize GCS bucket with proper configuration"""
        if self.status != GCSStorageStatus.AVAILABLE:
            return

        try:
            # Enable versioning if configured
            if self.config.versioning and not self.bucket.versioning_enabled:
                self.bucket.patch(
                    versioning={'enabled': True}
                )
                logger.info("GCS bucket versioning enabled")

            # Set uniform bucket level access if configured
            if self.config.uniform_bucket_level_access:
                try:
                    self.bucket.iam_configuration.uniform_bucket_level_access_enabled = True
                    self.bucket.patch()
                    logger.info("GCS bucket uniform access enabled")
                except GoogleAPIError as e:
                    logger.warning(f"Failed to enable uniform bucket access: {e}")

            # Set retention policy if configured
            if self.config.retention_policy_days:
                retention_period = timedelta(days=self.config.retention_policy_days)
                self.bucket.retention_period = retention_period
                self.bucket.patch()
                logger.info(f"GCS bucket retention policy set to {self.config.retention_policy_days} days")

            # Enable logging if configured
            if self.config.logging_enabled:
                log_bucket = self.client.bucket(f"{self.config.bucket_name}-logs")
                try:
                    self.bucket.enable_logging(
                        log_bucket=log_bucket,
                        log_prefix='access-logs/'
                    )
                    logger.info("GCS bucket access logging enabled")
                except GoogleAPIError as e:
                    logger.warning(f"Failed to enable access logging: {e}")

        except Exception as e:
            logger.error(f"Failed to initialize bucket configuration: {e}")

    def init_lifecycle(self):
        """Initialize GCS bucket lifecycle management"""
        if not self.config.lifecycle_management or self.status != GCSStorageStatus.AVAILABLE:
            return

        try:
            lifecycle_rules = [
                {
                    'action': {
                        'type': 'SetStorageClass',
                        'storage_class': GCSStorageClass.NEARLINE.value
                    },
                    'condition': {
                        'age': self.config.lifecycle_days_standard
                    }
                },
                {
                    'action': {
                        'type': 'SetStorageClass',
                        'storage_class': GCSStorageClass.COLDLINE.value
                    },
                    'condition': {
                        'age': self.config.lifecycle_days_nearline
                    }
                },
                {
                    'action': {
                        'type': 'SetStorageClass',
                        'storage_class': GCSStorageClass.ARCHIVE.value
                    },
                    'condition': {
                        'age': self.config.lifecycle_days_coldline
                    }
                },
                {
                    'action': {
                        'type': 'Delete'
                    },
                    'condition': {
                        'age': max(self.config.lifecycle_days_coldline + 365, self.config.lifecycle_days_coldline * 2)
                    }
                }
            ]

            self.bucket.lifecycle_rules = lifecycle_rules
            self.bucket.patch()
            logger.info("GCS bucket lifecycle management configured")

        except Exception as e:
            logger.error(f"Failed to configure lifecycle management: {e}")

    def init_replication(self):
        """Initialize cross-region replication"""
        if not self.config.cross_region_replication or not self.config.replication_regions:
            return

        try:
            # GCS replication is typically configured at the organization level
            # This is a simplified implementation
            for region in self.config.replication_regions:
                replica_bucket_name = f"{self.config.bucket_name}-{region}"
                try:
                    replica_bucket = self.client.bucket(replica_bucket_name)
                    replica_bucket.reload()
                    logger.info(f"Replication bucket available: {replica_bucket_name}")
                except NotFound:
                    logger.warning(f"Replication bucket not found: {replica_bucket_name}")

        except Exception as e:
            logger.error(f"Failed to configure cross-region replication: {e}")

    async def upload_backup(self, local_file_path: str, backup_id: str) -> str:
        """Upload backup to GCS"""
        logger.info(f"Uploading backup {backup_id} to GCS")

        if self.status != GCSStorageStatus.AVAILABLE:
            raise Exception(f"GCS storage not available: {self.status.value}")

        try:
            # Generate GCS object name
            object_name = self.generate_object_name(backup_id, local_file_path)

            # Create blob
            blob = self.bucket.blob(object_name)

            # Configure blob properties
            blob.storage_class = self.config.storage_class

            # Set encryption
            if self.config.encryption_method == GCSEncryptionMethod.CUSTOMER_MANAGED.value:
                blob.encryption_key = self.config.encryption_key
            elif self.config.encryption_method == GCSEncryptionMethod.CMEK.value:
                blob.kms_key_name = self.config.encryption_key

            # Set metadata
            blob.metadata = {
                'backup_id': backup_id,
                'upload_time': datetime.now(timezone.utc).isoformat(),
                'original_filename': os.path.basename(local_file_path)
            }

            # Calculate file hash
            file_hash = self.calculate_file_hash(local_file_path)
            blob.metadata['file_hash'] = file_hash

            # Upload file
            start_time = time.time()
            loop = asyncio.get_event_loop()

            await loop.run_in_executor(
                self.executor,
                lambda: blob.upload_from_filename(local_file_path, timeout=self.config.timeout_seconds)
            )

            upload_time = time.time() - start_time

            # Reload blob to get updated information
            blob.reload()

            result = GCSUploadResult(
                bucket=self.config.bucket_name,
                name=object_name,
                etag=blob.etag,
                generation=blob.generation,
                size_bytes=blob.size,
                storage_class=blob.storage_class,
                encryption=self.config.encryption_method,
                upload_time_seconds=upload_time,
                md5_hash=blob.md5_hash,
                crc32c=blob.crc32c
            )

            # Log upload result
            logger.info(f"Backup uploaded successfully: {backup_id} -> gs://{self.config.bucket_name}/{object_name}")
            return f"gs://{self.config.bucket_name}/{object_name}"

        except Exception as e:
            logger.error(f"Failed to upload backup {backup_id}: {e}")
            raise

    async def download_backup(self, storage_path: str, local_destination: str) -> str:
        """Download backup from GCS"""
        logger.info(f"Downloading backup from GCS: {storage_path}")

        if self.status != GCSStorageStatus.AVAILABLE:
            raise Exception(f"GCS storage not available: {self.status.value}")

        try:
            # Parse GCS path
            bucket_name, object_name = self.parse_gcs_path(storage_path)

            # Create destination directory
            os.makedirs(os.path.dirname(local_destination), exist_ok=True)

            # Get blob reference
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_name)

            # Download file
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                lambda: blob.download_to_filename(local_destination, timeout=self.config.timeout_seconds)
            )

            logger.info(f"Backup downloaded successfully: {storage_path} -> {local_destination}")
            return local_destination

        except Exception as e:
            logger.error(f"Failed to download backup {storage_path}: {e}")
            raise

    async def delete_backup(self, storage_path: str) -> bool:
        """Delete backup from GCS"""
        logger.info(f"Deleting backup from GCS: {storage_path}")

        if self.status != GCSStorageStatus.AVAILABLE:
            return False

        try:
            # Parse GCS path
            bucket_name, object_name = self.parse_gcs_path(storage_path)

            # Get blob reference and delete
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_name)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                blob.delete
            )

            logger.info(f"Backup deleted successfully: {storage_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete backup {storage_path}: {e}")
            return False

    def parse_gcs_path(self, gcs_path: str) -> Tuple[str, str]:
        """Parse GCS path into bucket and object name"""
        if not gcs_path.startswith('gs://'):
            raise ValueError(f"Invalid GCS path format: {gcs_path}")

        # Remove gs:// prefix
        path_without_prefix = gcs_path[5:]
        parts = path_without_prefix.split('/', 1)

        if len(parts) != 2:
            raise ValueError(f"Invalid GCS path format: {gcs_path}")

        return parts[0], parts[1]

    def generate_object_name(self, backup_id: str, local_file_path: str) -> str:
        """Generate GCS object name"""
        # Generate date-based path
        now = datetime.now(timezone.utc)
        date_path = now.strftime("%Y/%m/%d")

        # Get original filename
        original_filename = os.path.basename(local_file_path)

        # Generate object name
        object_name = f"{self.config.bucket_prefix}{date_path}/{backup_id}_{original_filename}"

        # Clean object name (remove double slashes, etc.)
        object_name = object_name.replace('//', '/')

        return object_name

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    async def list_backups(self, prefix: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List backups in GCS bucket"""
        if self.status != GCSStorageStatus.AVAILABLE:
            return []

        try:
            # Set prefix
            list_prefix = prefix or self.config.bucket_prefix

            # List blobs
            loop = asyncio.get_event_loop()
            blobs = await loop.run_in_executor(
                self.executor,
                lambda: list(self.client.list_blobs(
                    self.bucket,
                    prefix=list_prefix,
                    max_results=limit
                ))
            )

            backups = []
            for blob in blobs:
                backup_info = {
                    'name': blob.name,
                    'size_bytes': blob.size,
                    'updated': blob.updated,
                    'created': blob.time_created,
                    'etag': blob.etag,
                    'storage_class': blob.storage_class,
                    'content_type': blob.content_type,
                    'generation': blob.generation,
                    'md5_hash': blob.md5_hash,
                    'crc32c': blob.crc32c,
                    'url': f"gs://{self.bucket.name}/{blob.name}",
                    'metadata': blob.metadata or {}
                }

                backups.append(backup_info)

            return backups

        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []

    async def get_backup_info(self, storage_path: str) -> Dict[str, Any]:
        """Get detailed backup information"""
        if self.status != GCSStorageStatus.AVAILABLE:
            return {}

        try:
            bucket_name, object_name = self.parse_gcs_path(storage_path)

            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_name)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                blob.reload
            )

            return {
                'name': blob.name,
                'size_bytes': blob.size,
                'updated': blob.updated,
                'created': blob.time_created,
                'etag': blob.etag,
                'content_type': blob.content_type,
                'storage_class': blob.storage_class,
                'generation': blob.generation,
                'md5_hash': blob.md5_hash,
                'crc32c': blob.crc32c,
                'metadata': blob.metadata or {},
                'url': storage_path,
                'customer_encryption': blob.customer_encryption
            }

        except Exception as e:
            logger.error(f"Failed to get backup info: {e}")
            return {}

    async def copy_backup(self, source_path: str, destination_name: str, storage_class: Optional[str] = None) -> bool:
        """Copy backup to another location within GCS"""
        if self.status != GCSStorageStatus.AVAILABLE:
            return False

        try:
            source_bucket_name, source_object_name = self.parse_gcs_path(source_path)

            source_bucket = self.client.bucket(source_bucket_name)
            source_blob = source_bucket.blob(source_object_name)

            destination_bucket = self.client.bucket(self.config.bucket_name)
            destination_blob = destination_bucket.blob(destination_name)

            # Set storage class
            if storage_class:
                destination_blob.storage_class = storage_class
            else:
                destination_blob.storage_class = self.config.storage_class

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                destination_blob.copy_from,
                source_blob
            )

            logger.info(f"Backup copied successfully: {source_path} -> {destination_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to copy backup {source_path}: {e}")
            return False

    async def compose_backup(self, source_paths: List[str], destination_name: str) -> bool:
        """Compose multiple objects into a single backup"""
        if self.status != GCSStorageStatus.AVAILABLE:
            return False

        try:
            # Get source blobs
            source_blobs = []
            for source_path in source_paths:
                bucket_name, object_name = self.parse_gcs_path(source_path)
                bucket = self.client.bucket(bucket_name)
                blob = bucket.blob(object_name)
                source_blobs.append(blob)

            # Create destination blob
            destination_bucket = self.client.bucket(self.config.bucket_name)
            destination_blob = destination_bucket.blob(destination_name)
            destination_blob.storage_class = self.config.storage_class

            # Compose objects
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                destination_blob.compose,
                source_blobs
            )

            logger.info(f"Backup composed successfully: {len(source_paths)} files -> {destination_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to compose backup: {e}")
            return False

    async def rotate_backup(self, storage_path: str, new_storage_class: str) -> bool:
        """Rotate backup to different storage class"""
        if self.status != GCSStorageStatus.AVAILABLE:
            return False

        try:
            bucket_name, object_name = self.parse_gcs_path(storage_path)

            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_name)

            # Update storage class
            blob.storage_class = new_storage_class
            blob.patch()

            logger.info(f"Backup storage class rotated: {storage_path} -> {new_storage_class}")
            return True

        except Exception as e:
            logger.error(f"Failed to rotate backup storage class {storage_path}: {e}")
            return False

    async def restore_from_archive(self, storage_path: str) -> bool:
        """Restore backup from archive storage"""
        if self.status != GCSStorageStatus.AVAILABLE:
            return False

        try:
            bucket_name, object_name = self.parse_gcs_path(storage_path)

            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(object_name)

            # Restore from archive
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                blob.restore
            )

            logger.info(f"Archive restore initiated: {storage_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to initiate archive restore {storage_path}: {e}")
            return False

    def get_storage_status(self) -> Dict[str, Any]:
        """Get GCS storage status"""
        status_info = {
            'status': self.status.value,
            'bucket_name': self.config.bucket_name,
            'project_id': self.client.project if self.client else None,
            'storage_class': self.config.storage_class,
            'encryption_method': self.config.encryption_method,
            'versioning_enabled': self.config.versioning,
            'lifecycle_management': self.config.lifecycle_management,
            'cross_region_replication': self.config.cross_region_replication
        }

        # Add bucket metrics if available
        if self.status == GCSStorageStatus.AVAILABLE and self.bucket:
            try:
                # Reload bucket to get current configuration
                self.bucket.reload()

                status_info.update({
                    'location': self.bucket.location,
                    'location_type': self.bucket.location_type,
                    'storage_class': self.bucket.storage_class,
                    'uniform_bucket_level_access_enabled': self.bucket.iam_configuration.uniform_bucket_level_access_enabled,
                    'retention_period_days': self.bucket.retention_period.days if self.bucket.retention_period else None
                })

                # Get bucket size (approximate)
                total_size = 0
                total_objects = 0

                for blob in self.client.list_blobs(self.bucket, max_results=1000):
                    total_size += blob.size
                    total_objects += 1

                status_info['total_size_gb'] = total_size / (1024**3)
                status_info['total_objects'] = total_objects

            except Exception as e:
                logger.warning(f"Failed to get bucket metrics: {e}")

        return status_info

    def get_bucket_info(self) -> Dict[str, Any]:
        """Get detailed bucket information"""
        if self.status != GCSStorageStatus.AVAILABLE or not self.bucket:
            return {}

        try:
            self.bucket.reload()
            bucket_info = {
                'name': self.bucket.name,
                'project_number': self.bucket.project_number,
                'location': self.bucket.location,
                'location_type': self.bucket.location_type,
                'storage_class': self.bucket.storage_class,
                'time_created': self.bucket.time_created,
                'updated': self.bucket.updated,
                'metageneration': self.bucket.metageneration,
                'owner': self.bucket.owner,
                'iam_configuration': {
                    'uniform_bucket_level_access_enabled': self.bucket.iam_configuration.uniform_bucket_level_access_enabled,
                    'public_access_prevention': self.bucket.iam_configuration.public_access_prevention
                },
                'encryption': self.bucket.default_kms_key_name if hasattr(self.bucket, 'default_kms_key_name') else None,
                'lifecycle_rules': [
                    {
                        'action': rule.action,
                        'condition': rule.condition,
                        'storage_class': rule.storage_class
                    } for rule in (self.bucket.lifecycle_rules or [])
                ]
            }

            if self.bucket.retention_period:
                bucket_info['retention_period_days'] = self.bucket.retention_period.days

            if hasattr(self.bucket, 'requester_pays'):
                bucket_info['requester_pays'] = self.bucket.requester_pays

            if hasattr(self.bucket, 'labels'):
                bucket_info['labels'] = self.bucket.labels

            return bucket_info

        except Exception as e:
            logger.error(f"Failed to get bucket info: {e}")
            return {}

    def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)