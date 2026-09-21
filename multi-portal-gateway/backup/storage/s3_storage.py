#!/usr/bin/env python3
"""
S3 Storage Backend - AWS S3-based backup storage with cross-region replication

This storage backend provides AWS S3 storage with lifecycle management,
cross-region replication, encryption, and advanced features for backup files.
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
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
import multipart
from concurrent.futures import ThreadPoolExecutor
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class S3StorageStatus(Enum):
    """S3 storage status"""
    AVAILABLE = "available"
    UNAUTHORIZED = "unauthorized"
    REGION_UNAVAILABLE = "region_unavailable"
    BUCKET_NOT_FOUND = "bucket_not_found"
    ERROR = "error"

class S3StorageClass(Enum):
    """S3 storage classes"""
    STANDARD = "STANDARD"
    REDUCED_REDUNDANCY = "REDUCED_REDUNDANCY"
    STANDARD_IA = "STANDARD_IA"
    ONEZONE_IA = "ONEZONE_IA"
    INTELLIGENT_TIERING = "INTELLIGENT_TIERING"
    GLACIER = "GLACIER"
    DEEP_ARCHIVE = "DEEP_ARCHIVE"
    OUTPOSTS = "OUTPOSTS"

class ServerSideEncryption(Enum):
    """S3 server-side encryption options"""
    NONE = "none"
    AES256 = "AES256"
    AWS_KMS = "aws:kms"
    AWS_KMS_DSSE = "aws:kms:dsse"

@dataclass
class S3StorageConfig:
    """S3 storage configuration"""
    bucket_name: str
    region: str = "us-east-1"
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None
    storage_class: str = "STANDARD"
    server_side_encryption: str = "AES256"
    kms_key_id: Optional[str] = None
    bucket_prefix: str = "backups/"
    multipart_threshold_mb: int = 64
    multipart_chunksize_mb: int = 16
    max_concurrency: int = 10
    cross_region_replication: bool = False
    replication_regions: List[str] = None
    lifecycle_management: bool = True
    lifecycle_days_standard: int = 30
    lifecycle_days_ia: int = 90
    lifecycle_days_glacier: int = 365
    versioning: bool = True
    access_logging: bool = True
    request_payment: str = "requester"  # requester or bucket_owner
    metadata_database: str = "s3_storage.db"
    connection_timeout_seconds: int = 60
    read_timeout_seconds: int = 300
    retry_attempts: int = 3
    retry_delay_seconds: int = 5

@dataclass
class S3UploadResult:
    """S3 upload operation result"""
    bucket: str
    key: str
    etag: str
    version_id: Optional[str]
    size_bytes: int
    storage_class: str
    encryption: str
    upload_time_seconds: float
    multipart_id: Optional[str]

class S3Storage:
    """AWS S3 storage backend for backups"""

    def __init__(self, config: Dict[str, Any]):
        if isinstance(config, dict):
            self.config = S3StorageConfig(**config)
        else:
            self.config = config

        self.s3_client = None
        self.s3_resource = None
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrency)
        self.status = S3StorageStatus.INITIALIZING
        self.encryption_manager = None

        # Initialize S3 client and resources
        self.init_s3_client()
        self.init_encryption_manager()
        self.init_bucket()
        self.init_lifecycle()
        self.init_replication()

        logger.info(f"S3 storage backend initialized: {self.config.bucket_name} in {self.config.region}")

    def init_s3_client(self):
        """Initialize S3 client with configuration"""
        try:
            # Configure botocore
            botocore_config = Config(
                region_name=self.config.region,
                connect_timeout=self.config.connection_timeout_seconds,
                read_timeout=self.config.read_timeout_seconds,
                max_pool_connections=self.config.max_concurrency,
                retries={
                    'max_attempts': self.config.retry_attempts,
                    'mode': 'adaptive'
                }
            )

            # Create S3 client
            session = boto3.Session(
                aws_access_key_id=self.config.access_key_id,
                aws_secret_access_key=self.config.secret_access_key,
                aws_session_token=self.config.session_token,
                region_name=self.config.region
            )

            self.s3_client = session.client('s3', config=botocore_config)
            self.s3_resource = session.resource('s3', config=botocore_config)

            # Test connection
            self.s3_client.head_bucket(Bucket=self.config.bucket_name)
            self.status = S3StorageStatus.AVAILABLE

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                self.status = S3StorageStatus.BUCKET_NOT_FOUND
                logger.error(f"S3 bucket not found: {self.config.bucket_name}")
            elif error_code == '403':
                self.status = S3StorageStatus.UNAUTHORIZED
                logger.error(f"S3 access denied: {self.config.bucket_name}")
            else:
                self.status = S3StorageStatus.ERROR
                logger.error(f"S3 client initialization failed: {e}")
        except NoCredentialsError:
            self.status = S3StorageStatus.UNAUTHORIZED
            logger.error("AWS credentials not found")
        except Exception as e:
            self.status = S3StorageStatus.ERROR
            logger.error(f"S3 initialization failed: {e}")

    def init_encryption_manager(self):
        """Initialize encryption manager"""
        if self.config.server_side_encryption == ServerSideEncryption.AWS_KMS.value:
            from backup_service import EncryptionManager
            self.encryption_manager = EncryptionManager()

    def init_bucket(self):
        """Initialize S3 bucket with proper configuration"""
        if self.status != S3StorageStatus.AVAILABLE:
            return

        try:
            # Enable versioning if configured
            if self.config.versioning:
                self.s3_client.put_bucket_versioning(
                    Bucket=self.config.bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
                logger.info("S3 bucket versioning enabled")

            # Enable access logging if configured
            if self.config.access_logging:
                log_bucket = f"{self.config.bucket_name}-logs"
                try:
                    self.s3_client.put_bucket_logging(
                        Bucket=self.config.bucket_name,
                        BucketLoggingStatus={
                            'LoggingEnabled': {
                                'TargetBucket': log_bucket,
                                'TargetPrefix': 'access-logs/'
                            }
                        }
                    )
                    logger.info("S3 bucket access logging enabled")
                except ClientError as e:
                    logger.warning(f"Failed to enable access logging: {e}")

        except Exception as e:
            logger.error(f"Failed to initialize bucket configuration: {e}")

    def init_lifecycle(self):
        """Initialize S3 bucket lifecycle management"""
        if not self.config.lifecycle_management or self.status != S3StorageStatus.AVAILABLE:
            return

        try:
            lifecycle_rules = [
                {
                    'ID': 'StandardToIA',
                    'Status': 'Enabled',
                    'Transitions': [
                        {
                            'Days': self.config.lifecycle_days_standard,
                            'StorageClass': S3StorageClass.STANDARD_IA.value
                        }
                    ]
                },
                {
                    'ID': 'StandardToGlacier',
                    'Status': 'Enabled',
                    'Transitions': [
                        {
                            'Days': self.config.lifecycle_days_ia,
                            'StorageClass': S3StorageClass.GLACIER.value
                        }
                    ]
                },
                {
                    'ID': 'ExpiredObjects',
                    'Status': 'Enabled',
                    'Expiration': {
                        'Days': self.config.lifecycle_days_glacier
                    }
                }
            ]

            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.config.bucket_name,
                LifecycleConfiguration={'Rules': lifecycle_rules}
            )
            logger.info("S3 bucket lifecycle management configured")

        except Exception as e:
            logger.error(f"Failed to configure lifecycle management: {e}")

    def init_replication(self):
        """Initialize cross-region replication"""
        if not self.config.cross_region_replication or not self.config.replication_regions:
            return

        try:
            # Create IAM role for replication (if needed)
            replication_role = self.get_or_create_replication_role()

            # Configure replication
            replication_config = {
                'Role': replication_role,
                'Rules': []
            }

            for region in self.config.replication_regions:
                dest_bucket = f"{self.config.bucket_name}-{region}"
                rule = {
                    'ID': f'ReplicateTo{region}',
                    'Status': 'Enabled',
                    'Prefix': self.config.bucket_prefix,
                    'Destination': {
                        'Bucket': f'arn:aws:s3:::{dest_bucket}',
                        'StorageClass': self.config.storage_class,
                        'Account': self.get_account_id()
                    }
                }
                replication_config['Rules'].append(rule)

            self.s3_client.put_bucket_replication(
                Bucket=self.config.bucket_name,
                ReplicationConfiguration=replication_config
            )
            logger.info(f"S3 cross-region replication configured for regions: {self.config.replication_regions}")

        except Exception as e:
            logger.error(f"Failed to configure cross-region replication: {e}")

    def get_or_create_replication_role(self) -> str:
        """Get or create IAM role for S3 replication"""
        # This is a simplified implementation
        # In production, you would create and manage proper IAM roles
        role_arn = os.getenv('S3_REPLICATION_ROLE_ARN')
        if role_arn:
            return role_arn

        # Fallback to using existing EC2 instance role or create one
        logger.warning("S3 replication role not configured, using default role")
        return "arn:aws:iam::account:role/s3-replication-role"

    def get_account_id(self) -> str:
        """Get AWS account ID"""
        try:
            sts_client = boto3.client('sts')
            return sts_client.get_caller_identity()['Account']
        except:
            return "unknown"

    async def upload_backup(self, local_file_path: str, backup_id: str) -> str:
        """Upload backup to S3"""
        logger.info(f"Uploading backup {backup_id} to S3")

        if self.status != S3StorageStatus.AVAILABLE:
            raise Exception(f"S3 storage not available: {self.status.value}")

        try:
            # Generate S3 key
            s3_key = self.generate_s3_key(backup_id, local_file_path)

            # Get file size
            file_size = os.path.getsize(local_file_path)
            multipart_threshold = self.config.multipart_threshold_mb * 1024 * 1024

            # Choose upload method
            if file_size > multipart_threshold:
                result = await self.upload_multipart(local_file_path, s3_key, backup_id)
            else:
                result = await self.upload_single(local_file_path, s3_key, backup_id)

            # Log upload result
            logger.info(f"Backup uploaded successfully: {backup_id} -> s3://{self.config.bucket_name}/{s3_key}")
            return f"s3://{self.config.bucket_name}/{s3_key}"

        except Exception as e:
            logger.error(f"Failed to upload backup {backup_id}: {e}")
            raise

    async def upload_single(self, local_file_path: str, s3_key: str, backup_id: str) -> S3UploadResult:
        """Upload file using single-part upload"""
        start_time = time.time()

        # Prepare upload arguments
        upload_args = {
            'Bucket': self.config.bucket_name,
            'Key': s3_key,
            'StorageClass': self.config.storage_class
        }

        # Add encryption
        if self.config.server_side_encryption != ServerSideEncryption.NONE.value:
            upload_args['ServerSideEncryption'] = self.config.server_side_encryption
            if self.config.server_side_encryption == ServerSideEncryption.AWS_KMS.value:
                upload_args['SSEKMSKeyId'] = self.config.kms_key_id

        # Add metadata
        upload_args['Metadata'] = {
            'backup_id': backup_id,
            'upload_time': datetime.now(timezone.utc).isoformat(),
            'original_filename': os.path.basename(local_file_path)
        }

        # Calculate file checksum
        file_hash = self.calculate_file_hash(local_file_path)
        upload_args['Metadata']['file_hash'] = file_hash

        # Execute upload
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.executor,
            lambda: self.s3_client.upload_file(
                local_file_path,
                self.config.bucket_name,
                s3_key,
                ExtraArgs={k: v for k, v in upload_args.items() if k not in ['Bucket', 'Key']}
            )
        )

        # Get object information
        head_response = await loop.run_in_executor(
            self.executor,
            lambda: self.s3_client.head_object(Bucket=self.config.bucket_name, Key=s3_key)
        )

        upload_time = time.time() - start_time

        return S3UploadResult(
            bucket=self.config.bucket_name,
            key=s3_key,
            etag=head_response['ETag'].strip('"'),
            version_id=head_response.get('VersionId'),
            size_bytes=head_response['ContentLength'],
            storage_class=head_response.get('StorageClass', self.config.storage_class),
            encryption=head_response.get('ServerSideEncryption', 'none'),
            upload_time_seconds=upload_time,
            multipart_id=None
        )

    async def upload_multipart(self, local_file_path: str, s3_key: str, backup_id: str) -> S3UploadResult:
        """Upload file using multipart upload"""
        start_time = time.time()
        chunk_size = self.config.multipart_chunksize_mb * 1024 * 1024

        # Initiate multipart upload
        create_args = {
            'Bucket': self.config.bucket_name,
            'Key': s3_key,
            'StorageClass': self.config.storage_class,
            'Metadata': {
                'backup_id': backup_id,
                'upload_time': datetime.now(timezone.utc).isoformat(),
                'original_filename': os.path.basename(local_file_path),
                'multipart_upload': 'true'
            }
        }

        # Add encryption
        if self.config.server_side_encryption != ServerSideEncryption.NONE.value:
            create_args['ServerSideEncryption'] = self.config.server_side_encryption
            if self.config.server_side_encryption == ServerSideEncryption.AWS_KMS.value:
                create_args['SSEKMSKeyId'] = self.config.kms_key_id

        loop = asyncio.get_event_loop()
        create_response = await loop.run_in_executor(
            self.executor,
            lambda: self.s3_client.create_multipart_upload(**create_args)
        )

        upload_id = create_response['UploadId']
        parts = []

        try:
            # Upload parts
            with open(local_file_path, 'rb') as f:
                part_number = 1
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    part_response = await loop.run_in_executor(
                        self.executor,
                        lambda: self.s3_client.upload_part(
                            Bucket=self.config.bucket_name,
                            Key=s3_key,
                            PartNumber=part_number,
                            UploadId=upload_id,
                            Body=chunk
                        )
                    )

                    parts.append({
                        'ETag': part_response['ETag'],
                        'PartNumber': part_number
                    })

                    part_number += 1

            # Complete multipart upload
            complete_args = {
                'Bucket': self.config.bucket_name,
                'Key': s3_key,
                'UploadId': upload_id,
                'MultipartUpload': {'Parts': parts}
            }

            complete_response = await loop.run_in_executor(
                self.executor,
                lambda: self.s3_client.complete_multipart_upload(**complete_args)
            )

            # Get object information
            head_response = await loop.run_in_executor(
                self.executor,
                lambda: self.s3_client.head_object(Bucket=self.config.bucket_name, Key=s3_key)
            )

            upload_time = time.time() - start_time

            return S3UploadResult(
                bucket=self.config.bucket_name,
                key=s3_key,
                etag=complete_response['ETag'].strip('"'),
                version_id=head_response.get('VersionId'),
                size_bytes=head_response['ContentLength'],
                storage_class=head_response.get('StorageClass', self.config.storage_class),
                encryption=head_response.get('ServerSideEncryption', 'none'),
                upload_time_seconds=upload_time,
                multipart_id=upload_id
            )

        except Exception as e:
            # Abort multipart upload on error
            try:
                await loop.run_in_executor(
                    self.executor,
                    lambda: self.s3_client.abort_multipart_upload(
                        Bucket=self.config.bucket_name,
                        Key=s3_key,
                        UploadId=upload_id
                    )
                )
            except:
                pass
            raise

    async def download_backup(self, storage_path: str, local_destination: str) -> str:
        """Download backup from S3"""
        logger.info(f"Downloading backup from S3: {storage_path}")

        if self.status != S3StorageStatus.AVAILABLE:
            raise Exception(f"S3 storage not available: {self.status.value}")

        try:
            # Parse S3 path
            bucket, key = self.parse_s3_path(storage_path)

            # Create destination directory
            os.makedirs(os.path.dirname(local_destination), exist_ok=True)

            # Download file
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                lambda: self.s3_client.download_file(bucket, key, local_destination)
            )

            logger.info(f"Backup downloaded successfully: {storage_path} -> {local_destination}")
            return local_destination

        except Exception as e:
            logger.error(f"Failed to download backup {storage_path}: {e}")
            raise

    async def delete_backup(self, storage_path: str) -> bool:
        """Delete backup from S3"""
        logger.info(f"Deleting backup from S3: {storage_path}")

        if self.status != S3StorageStatus.AVAILABLE:
            return False

        try:
            # Parse S3 path
            bucket, key = self.parse_s3_path(storage_path)

            # Delete object
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                lambda: self.s3_client.delete_object(Bucket=bucket, Key=key)
            )

            logger.info(f"Backup deleted successfully: {storage_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete backup {storage_path}: {e}")
            return False

    def parse_s3_path(self, s3_path: str) -> Tuple[str, str]:
        """Parse S3 path into bucket and key"""
        if not s3_path.startswith('s3://'):
            raise ValueError(f"Invalid S3 path format: {s3_path}")

        # Remove s3:// prefix
        path_without_prefix = s3_path[5:]
        parts = path_without_prefix.split('/', 1)

        if len(parts) != 2:
            raise ValueError(f"Invalid S3 path format: {s3_path}")

        return parts[0], parts[1]

    def generate_s3_key(self, backup_id: str, local_file_path: str) -> str:
        """Generate S3 object key"""
        # Generate date-based path
        now = datetime.now(timezone.utc)
        date_path = now.strftime("%Y/%m/%d")

        # Get original filename
        original_filename = os.path.basename(local_file_path)

        # Generate key
        key = f"{self.config.bucket_prefix}{date_path}/{backup_id}_{original_filename}"

        # Clean key (remove double slashes, etc.)
        key = key.replace('//', '/')

        return key

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    async def list_backups(self, prefix: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List backups in S3 bucket"""
        if self.status != S3StorageStatus.AVAILABLE:
            return []

        try:
            # Set prefix
            list_prefix = prefix or self.config.bucket_prefix

            # List objects
            loop = asyncio.get_event_loop()
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(
                Bucket=self.config.bucket_name,
                Prefix=list_prefix,
                MaxKeys=limit
            )

            backups = []
            async for page in self.async_generator(paginator):
                for obj in page.get('Contents', []):
                    backup_info = {
                        'key': obj['Key'],
                        'size_bytes': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'etag': obj['ETag'].strip('"'),
                        'storage_class': obj.get('StorageClass', 'STANDARD'),
                        'url': f"s3://{self.config.bucket_name}/{obj['Key']}"
                    }

                    # Get object metadata
                    try:
                        head_response = await loop.run_in_executor(
                            self.executor,
                            lambda: self.s3_client.head_object(
                                Bucket=self.config.bucket_name,
                                Key=obj['Key']
                            )
                        )
                        backup_info['metadata'] = head_response.get('Metadata', {})
                        backup_info['version_id'] = head_response.get('VersionId')
                    except:
                        pass

                    backups.append(backup_info)

                    if len(backups) >= limit:
                        break

                if len(backups) >= limit:
                    break

            return backups

        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []

    async def async_generator(self, paginator):
        """Async wrapper for boto3 paginator"""
        loop = asyncio.get_event_loop()
        for page in paginator:
            yield page

    async def get_backup_info(self, storage_path: str) -> Dict[str, Any]:
        """Get detailed backup information"""
        if self.status != S3StorageStatus.AVAILABLE:
            return {}

        try:
            bucket, key = self.parse_s3_path(storage_path)

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                lambda: self.s3_client.head_object(Bucket=bucket, Key=key)
            )

            return {
                'key': key,
                'size_bytes': response['ContentLength'],
                'last_modified': response['LastModified'],
                'etag': response['ETag'].strip('"'),
                'content_type': response.get('ContentType'),
                'storage_class': response.get('StorageClass', 'STANDARD'),
                'server_side_encryption': response.get('ServerSideEncryption'),
                'kms_key_id': response.get('SSEKMSKeyId'),
                'metadata': response.get('Metadata', {}),
                'version_id': response.get('VersionId'),
                'url': storage_path
            }

        except Exception as e:
            logger.error(f"Failed to get backup info: {e}")
            return {}

    def get_storage_status(self) -> Dict[str, Any]:
        """Get S3 storage status"""
        status_info = {
            'status': self.status.value,
            'bucket_name': self.config.bucket_name,
            'region': self.config.region,
            'storage_class': self.config.storage_class,
            'encryption': self.config.server_side_encryption,
            'versioning_enabled': self.config.versioning,
            'lifecycle_management': self.config.lifecycle_management,
            'cross_region_replication': self.config.cross_region_replication
        }

        # Add bucket metrics if available
        if self.status == S3StorageStatus.AVAILABLE:
            try:
                # Get bucket location
                location = self.s3_client.get_bucket_location(Bucket=self.config.bucket_name)
                status_info['bucket_location'] = location.get('LocationConstraint') or 'us-east-1'

                # Get bucket size (approximate)
                total_size = 0
                total_objects = 0
                paginator = self.s3_client.get_paginator('list_objects_v2')
                for page in paginator.paginate(Bucket=self.config.bucket_name):
                    for obj in page.get('Contents', []):
                        total_size += obj['Size']
                        total_objects += 1

                status_info['total_size_gb'] = total_size / (1024**3)
                status_info['total_objects'] = total_objects

            except Exception as e:
                logger.warning(f"Failed to get bucket metrics: {e}")

        return status_info

    async def copy_backup(self, source_path: str, destination_key: str, storage_class: Optional[str] = None) -> bool:
        """Copy backup to another location within S3"""
        if self.status != S3StorageStatus.AVAILABLE:
            return False

        try:
            source_bucket, source_key = self.parse_s3_path(source_path)

            copy_args = {
                'Bucket': self.config.bucket_name,
                'Key': destination_key,
                'CopySource': {
                    'Bucket': source_bucket,
                    'Key': source_key
                }
            }

            if storage_class:
                copy_args['StorageClass'] = storage_class
            else:
                copy_args['StorageClass'] = self.config.storage_class

            if self.config.server_side_encryption != ServerSideEncryption.NONE.value:
                copy_args['ServerSideEncryption'] = self.config.server_side_encryption
                if self.config.server_side_encryption == ServerSideEncryption.AWS_KMS.value:
                    copy_args['SSEKMSKeyId'] = self.config.kms_key_id

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                lambda: self.s3_client.copy_object(**copy_args)
            )

            logger.info(f"Backup copied successfully: {source_path} -> {destination_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to copy backup {source_path}: {e}")
            return False

    async def restore_from_glacier(self, storage_path: str, tier: str = "Standard") -> bool:
        """Initiate restore from Glacier storage"""
        if self.status != S3StorageStatus.AVAILABLE:
            return False

        try:
            bucket, key = self.parse_s3_path(storage_path)

            restore_args = {
                'Bucket': bucket,
                'Key': key,
                'RestoreRequest': {
                    'Days': 30,  # Restore for 30 days
                    'GlacierJobParameters': {
                        'Tier': tier  # Expedited, Standard, or Bulk
                    }
                }
            }

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                lambda: self.s3_client.restore_object(**restore_args)
            )

            logger.info(f"Glacier restore initiated: {storage_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to initiate Glacier restore {storage_path}: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)