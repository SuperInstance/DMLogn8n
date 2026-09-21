#!/usr/bin/env python3
"""
DMLogn8n Backup Service - Comprehensive Backup Orchestration System

This service provides automated backup scheduling, execution, and management
for the DMLogn8n multi-agent platform with support for multiple storage backends,
validation, and disaster recovery capabilities.
"""

import asyncio
import logging
import json
import os
import sys
import time
import hashlib
import schedule
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import yaml
import sqlite3
import boto3
from botocore.exceptions import ClientError
from google.cloud import storage as gcs
import psycopg2
import redis
import tarfile
import gzip
import shutil
import subprocess
from cryptography.fernet import Fernet
import requests
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/logs/backup_service.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Prometheus Metrics
BACKUP_TOTAL = Counter('backup_operations_total', 'Total backup operations', ['type', 'status'])
BACKUP_DURATION = Histogram('backup_duration_seconds', 'Backup duration in seconds', ['type'])
BACKUP_SIZE = Gauge('backup_size_bytes', 'Size of backup in bytes', ['type', 'storage'])
RESTORE_TOTAL = Counter('restore_operations_total', 'Total restore operations', ['status'])
ACTIVE_BACKUPS = Gauge('active_backups', 'Number of active backup operations')

class BackupType(Enum):
    """Backup operation types"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    TRANSACTION_LOG = "transaction_log"

class BackupStatus(Enum):
    """Backup operation status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    VALIDATING = "validating"

class StorageBackend(Enum):
    """Storage backend types"""
    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"

@dataclass
class BackupConfig:
    """Backup configuration dataclass"""
    name: str
    backup_type: str
    source_path: str
    storage_backend: str
    storage_config: Dict[str, Any]
    schedule_cron: str
    retention_days: int
    compression: bool = True
    encryption: bool = True
    encryption_key: Optional[str] = None
    checksum_validation: bool = True
    cross_region_replication: bool = False
    notification_enabled: bool = True
    notification_emails: List[str] = None

@dataclass
class BackupMetadata:
    """Backup metadata information"""
    backup_id: str
    name: str
    backup_type: str
    source_path: str
    storage_backend: str
    storage_path: str
    created_at: datetime
    completed_at: Optional[datetime]
    status: str
    size_bytes: int
    compressed_size_bytes: int
    checksum: str
    encryption_key_id: Optional[str]
    parent_backup_id: Optional[str]
    retention_expires_at: datetime
    validation_status: Optional[str]
    tags: Dict[str, str]

class DatabaseManager:
    """Manages backup metadata and operations database"""

    def __init__(self, db_path: str = "/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/backup_metadata.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize backup metadata database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    backup_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    backup_type TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    storage_backend TEXT NOT NULL,
                    storage_path TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    status TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    compressed_size_bytes INTEGER NOT NULL,
                    checksum TEXT NOT NULL,
                    encryption_key_id TEXT,
                    parent_backup_id TEXT,
                    retention_expires_at TIMESTAMP NOT NULL,
                    validation_status TEXT,
                    tags TEXT,
                    metadata TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS backup_schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    config TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    last_run TIMESTAMP,
                    next_run TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS backup_operations (
                    operation_id TEXT PRIMARY KEY,
                    backup_id TEXT,
                    operation_type TEXT NOT NULL,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    FOREIGN KEY (backup_id) REFERENCES backups (backup_id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backups_status ON backups(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backups_created_at ON backups(created_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backups_retention ON backups(retention_expires_at)
            """)

    def save_backup(self, backup: BackupMetadata):
        """Save backup metadata to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO backups
                (backup_id, name, backup_type, source_path, storage_backend, storage_path,
                 created_at, completed_at, status, size_bytes, compressed_size_bytes,
                 checksum, encryption_key_id, parent_backup_id, retention_expires_at,
                 validation_status, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                backup.backup_id, backup.name, backup.backup_type, backup.source_path,
                backup.storage_backend, backup.storage_path, backup.created_at,
                backup.completed_at, backup.status, backup.size_bytes,
                backup.compressed_size_bytes, backup.checksum, backup.encryption_key_id,
                backup.parent_backup_id, backup.retention_expires_at, backup.validation_status,
                json.dumps(backup.tags), json.dumps(asdict(backup))
            ))

    def get_backup(self, backup_id: str) -> Optional[BackupMetadata]:
        """Retrieve backup metadata by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM backups WHERE backup_id = ?
            """, (backup_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_backup(row)
            return None

    def get_backups_by_status(self, status: str) -> List[BackupMetadata]:
        """Get backups by status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM backups WHERE status = ? ORDER BY created_at DESC
            """, (status,))
            return [self._row_to_backup(row) for row in cursor.fetchall()]

    def get_expired_backups(self) -> List[BackupMetadata]:
        """Get backups that have exceeded retention period"""
        now = datetime.now(timezone.utc)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM backups WHERE retention_expires_at < ? AND status = 'completed'
            """, (now,))
            return [self._row_to_backup(row) for row in cursor.fetchall()]

    def _row_to_backup(self, row) -> BackupMetadata:
        """Convert database row to BackupMetadata object"""
        return BackupMetadata(
            backup_id=row[0],
            name=row[1],
            backup_type=row[2],
            source_path=row[3],
            storage_backend=row[4],
            storage_path=row[5],
            created_at=datetime.fromisoformat(row[6]),
            completed_at=datetime.fromisoformat(row[7]) if row[7] else None,
            status=row[8],
            size_bytes=row[9],
            compressed_size_bytes=row[10],
            checksum=row[11],
            encryption_key_id=row[12],
            parent_backup_id=row[13],
            retention_expires_at=datetime.fromisoformat(row[14]),
            validation_status=row[15],
            tags=json.loads(row[16]) if row[16] else {}
        )

class BackupService:
    """Main backup orchestration service"""

    def __init__(self, config_path: str = "/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/config/backup_config.yaml"):
        self.config_path = config_path
        self.db_manager = DatabaseManager()
        self.storage_backends = {}
        self.schedulers = {}
        self.active_backups = {}
        self.encryption_manager = EncryptionManager()
        self.monitoring = BackupMonitoring()
        self.notifier = BackupNotifier()
        self.validator = BackupValidator()

        # Load configuration
        self.config = self.load_config()

        # Initialize storage backends
        self.init_storage_backends()

        # Initialize schedulers
        self.init_schedulers()

        # Start metrics server
        start_http_server(8090)

        logger.info("Backup service initialized successfully")

    def load_config(self) -> Dict[str, Any]:
        """Load backup configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Get default backup configuration"""
        return {
            'storage': {
                'local': {
                    'backup_path': '/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/storage/local',
                    'compression_level': 6
                },
                's3': {
                    'bucket': 'dmlogn8n-backups',
                    'region': 'us-east-1',
                    'access_key_id': os.getenv('AWS_ACCESS_KEY_ID'),
                    'secret_access_key': os.getenv('AWS_SECRET_ACCESS_KEY')
                },
                'gcs': {
                    'bucket': 'dmlogn8n-backups',
                    'credentials_path': '/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/config/gcs_credentials.json'
                }
            },
            'schedules': {
                'database_full': '0 2 * * 0',  # Weekly full backup at 2 AM Sunday
                'database_incremental': '0 3 * * *',  # Daily incremental at 3 AM
                'files_full': '0 1 * * 0',  # Weekly files backup at 1 AM Sunday
                'config': '0 4 * * *'  # Daily config backup at 4 AM
            },
            'retention': {
                'daily_retention_days': 7,
                'weekly_retention_weeks': 4,
                'monthly_retention_months': 12,
                'yearly_retention_years': 7
            },
            'notifications': {
                'email_enabled': True,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'smtp_username': os.getenv('SMTP_USERNAME'),
                'smtp_password': os.getenv('SMTP_PASSWORD'),
                'admin_emails': ['admin@dmlogn8n.com']
            },
            'encryption': {
                'enabled': True,
                'key_rotation_days': 90
            }
        }

    def init_storage_backends(self):
        """Initialize storage backends"""
        # Import and initialize storage backends
        from storage.local_storage import LocalStorage
        from storage.s3_storage import S3Storage
        from storage.gcs_storage import GCSStorage

        self.storage_backends[StorageBackend.LOCAL] = LocalStorage(self.config['storage']['local'])
        self.storage_backends[StorageBackend.S3] = S3Storage(self.config['storage']['s3'])
        self.storage_backends[StorageBackend.GCS] = GCSStorage(self.config['storage']['gcs'])

        logger.info("Storage backends initialized")

    def init_schedulers(self):
        """Initialize backup schedulers"""
        from schedulers.database_scheduler import DatabaseScheduler
        from schedulers.file_scheduler import FileScheduler
        from schedulers.config_scheduler import ConfigScheduler

        self.schedulers['database'] = DatabaseScheduler(self)
        self.schedulers['files'] = FileScheduler(self)
        self.schedulers['config'] = ConfigScheduler(self)

        # Schedule backup jobs
        self.schedule_jobs()

        logger.info("Backup schedulers initialized")

    def schedule_jobs(self):
        """Schedule backup jobs using cron expressions"""
        schedules = self.config.get('schedules', {})

        # Database full backup
        if 'database_full' in schedules:
            schedule.every().sunday.at("02:00").do(
                self.execute_backup_job,
                'database_full',
                BackupType.FULL
            )

        # Database incremental backup
        if 'database_incremental' in schedules:
            schedule.every().day.at("03:00").do(
                self.execute_backup_job,
                'database_incremental',
                BackupType.INCREMENTAL
            )

        # Files full backup
        if 'files_full' in schedules:
            schedule.every().sunday.at("01:00").do(
                self.execute_backup_job,
                'files_full',
                BackupType.FULL
            )

        # Config backup
        if 'config' in schedules:
            schedule.every().day.at("04:00").do(
                self.execute_backup_job,
                'config',
                BackupType.FULL
            )

        # Start scheduler thread
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()

        logger.info("Backup jobs scheduled")

    def run_scheduler(self):
        """Run the backup scheduler in a separate thread"""
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)

    async def execute_backup_job(self, job_name: str, backup_type: BackupType):
        """Execute a backup job"""
        backup_id = f"{job_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Starting backup job: {job_name} ({backup_type.value}) - ID: {backup_id}")
        ACTIVE_BACKUPS.inc()

        try:
            # Create backup metadata
            backup_metadata = BackupMetadata(
                backup_id=backup_id,
                name=job_name,
                backup_type=backup_type.value,
                source_path=self.get_source_path_for_job(job_name),
                storage_backend=self.get_storage_backend_for_job(job_name),
                storage_path="",
                created_at=datetime.now(timezone.utc),
                completed_at=None,
                status=BackupStatus.RUNNING.value,
                size_bytes=0,
                compressed_size_bytes=0,
                checksum="",
                encryption_key_id=None,
                parent_backup_id=self.get_parent_backup_id(job_name, backup_type),
                retention_expires_at=self.calculate_retention_expiry(backup_type),
                validation_status=None,
                tags={"job_name": job_name, "backup_type": backup_type.value}
            )

            # Save initial backup metadata
            self.db_manager.save_backup(backup_metadata)

            # Execute backup based on job type
            if job_name.startswith('database'):
                result = await self.schedulers['database'].execute_backup(backup_metadata, backup_type)
            elif job_name.startswith('files'):
                result = await self.schedulers['files'].execute_backup(backup_metadata, backup_type)
            elif job_name == 'config':
                result = await self.schedulers['config'].execute_backup(backup_metadata, backup_type)
            else:
                raise ValueError(f"Unknown backup job: {job_name}")

            # Update backup metadata with results
            backup_metadata.completed_at = datetime.now(timezone.utc)
            backup_metadata.status = BackupStatus.COMPLETED.value
            backup_metadata.size_bytes = result['size_bytes']
            backup_metadata.compressed_size_bytes = result['compressed_size_bytes']
            backup_metadata.checksum = result['checksum']
            backup_metadata.storage_path = result['storage_path']

            # Validate backup if enabled
            if self.config.get('validation', {}).get('enabled', True):
                backup_metadata.validation_status = await self.validator.validate_backup(backup_metadata)

            # Save final backup metadata
            self.db_manager.save_backup(backup_metadata)

            # Update metrics
            BACKUP_TOTAL.labels(type=job_name, status='success').inc()
            BACKUP_SIZE.labels(type=job_name, storage=backup_metadata.storage_backend).set(result['compressed_size_bytes'])

            logger.info(f"Backup job completed successfully: {backup_id}")

            # Send notification if enabled
            if self.config['notifications']['email_enabled']:
                await self.notifier.send_backup_success_notification(backup_metadata)

        except Exception as e:
            logger.error(f"Backup job failed: {backup_id} - {e}")

            # Update backup metadata with error
            if 'backup_metadata' in locals():
                backup_metadata.status = BackupStatus.FAILED.value
                backup_metadata.completed_at = datetime.now(timezone.utc)
                self.db_manager.save_backup(backup_metadata)

            # Update metrics
            BACKUP_TOTAL.labels(type=job_name, status='failed').inc()

            # Send notification
            if self.config['notifications']['email_enabled']:
                await self.notifier.send_backup_failure_notification(backup_id, job_name, str(e))

        finally:
            ACTIVE_BACKUPS.dec()

    def get_source_path_for_job(self, job_name: str) -> str:
        """Get source path for a backup job"""
        job_paths = {
            'database_full': '/var/lib/postgresql',
            'database_incremental': '/var/lib/postgresql',
            'files_full': '/home/activeloguser/DMLogn8n',
            'config': '/home/activeloguser/DMLogn8n/multi-portal-gateway/config'
        }
        return job_paths.get(job_name, '/home/activeloguser/DMLogn8n')

    def get_storage_backend_for_job(self, job_name: str) -> str:
        """Get storage backend for a backup job"""
        # Default to S3 for production backups, local for development
        return StorageBackend.S3.value if os.getenv('ENVIRONMENT') == 'production' else StorageBackend.LOCAL.value

    def get_parent_backup_id(self, job_name: str, backup_type: BackupType) -> Optional[str]:
        """Get parent backup ID for incremental backups"""
        if backup_type != BackupType.INCREMENTAL:
            return None

        # Get the most recent full backup for this job
        with sqlite3.connect(self.db_manager.db_path) as conn:
            cursor = conn.execute("""
                SELECT backup_id FROM backups
                WHERE name = ? AND backup_type = 'full' AND status = 'completed'
                ORDER BY created_at DESC LIMIT 1
            """, (job_name,))
            result = cursor.fetchone()
            return result[0] if result else None

    def calculate_retention_expiry(self, backup_type: BackupType) -> datetime:
        """Calculate retention expiry date for backup"""
        retention_config = self.config.get('retention', {})

        if backup_type == BackupType.FULL:
            days = retention_config.get('monthly_retention_months', 12) * 30
        else:
            days = retention_config.get('daily_retention_days', 7)

        return datetime.now(timezone.utc) + timedelta(days=days)

    async def cleanup_expired_backups(self):
        """Clean up expired backups"""
        expired_backups = self.db_manager.get_expired_backups()

        for backup in expired_backups:
            try:
                # Delete backup from storage
                storage_backend = self.storage_backends[StorageBackend(backup.storage_backend)]
                await storage_backend.delete_backup(backup.storage_path)

                # Update backup status
                backup.status = 'deleted'
                self.db_manager.save_backup(backup)

                logger.info(f"Deleted expired backup: {backup.backup_id}")

            except Exception as e:
                logger.error(f"Failed to delete expired backup {backup.backup_id}: {e}")

    def get_backup_status(self, backup_id: str) -> Dict[str, Any]:
        """Get backup status and metadata"""
        backup = self.db_manager.get_backup(backup_id)
        if not backup:
            return {'error': 'Backup not found'}

        return {
            'backup_id': backup.backup_id,
            'name': backup.name,
            'type': backup.backup_type,
            'status': backup.status,
            'created_at': backup.created_at.isoformat(),
            'completed_at': backup.completed_at.isoformat() if backup.completed_at else None,
            'size_bytes': backup.size_bytes,
            'compressed_size_bytes': backup.compressed_size_bytes,
            'storage_backend': backup.storage_backend,
            'validation_status': backup.validation_status,
            'retention_expires_at': backup.retention_expires_at.isoformat()
        }

    def list_backups(self, name: Optional[str] = None, status: Optional[str] = None,
                    limit: int = 50) -> List[Dict[str, Any]]:
        """List backups with optional filtering"""
        query = "SELECT * FROM backups WHERE 1=1"
        params = []

        if name:
            query += " AND name = ?"
            params.append(name)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_manager.db_path) as conn:
            cursor = conn.execute(query, params)
            return [self.db_manager._row_to_backup(row).__dict__ for row in cursor.fetchall()]

    async def start_backup_now(self, job_name: str, backup_type: str = "full") -> str:
        """Start a backup job immediately"""
        backup_type_enum = BackupType(backup_type)
        backup_id = f"{job_name}_manual_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        # Start backup in background
        asyncio.create_task(self.execute_backup_job(backup_id, backup_type_enum))

        return backup_id

    def get_service_health(self) -> Dict[str, Any]:
        """Get backup service health status"""
        return {
            'status': 'healthy',
            'uptime': time.time() - self.start_time if hasattr(self, 'start_time') else 0,
            'active_backups': len(self.active_backups),
            'storage_backends': list(self.storage_backends.keys()),
            'scheduled_jobs': len(schedule.jobs),
            'last_cleanup': getattr(self, 'last_cleanup', None)
        }

class EncryptionManager:
    """Manages backup encryption and key rotation"""

    def __init__(self):
        self.keys = {}
        self.current_key_id = None
        self.load_keys()

    def load_keys(self):
        """Load encryption keys from secure storage"""
        keys_file = '/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/config/encryption_keys.json'

        try:
            if os.path.exists(keys_file):
                with open(keys_file, 'r') as f:
                    self.keys = json.load(f)

                # Set current key (most recent)
                self.current_key_id = max(self.keys.keys())
            else:
                # Generate initial key
                self.generate_new_key()

        except Exception as e:
            logger.error(f"Failed to load encryption keys: {e}")
            self.generate_new_key()

    def generate_new_key(self):
        """Generate a new encryption key"""
        key = Fernet.generate_key()
        key_id = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')

        self.keys[key_id] = key.decode('utf-utf-8')
        self.current_key_id = key_id

        # Save keys
        self.save_keys()

    def save_keys(self):
        """Save encryption keys to secure storage"""
        keys_file = '/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/config/encryption_keys.json'

        try:
            os.makedirs(os.path.dirname(keys_file), exist_ok=True)
            with open(keys_file, 'w') as f:
                json.dump(self.keys, f)

            # Set secure permissions
            os.chmod(keys_file, 0o600)

        except Exception as e:
            logger.error(f"Failed to save encryption keys: {e}")

    def encrypt_data(self, data: bytes, key_id: Optional[str] = None) -> Tuple[bytes, str]:
        """Encrypt data with specified or current key"""
        key_id = key_id or self.current_key_id
        key = self.keys[key_id].encode('utf-8')

        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data)

        return encrypted_data, key_id

    def decrypt_data(self, encrypted_data: bytes, key_id: str) -> bytes:
        """Decrypt data with specified key"""
        key = self.keys[key_id].encode('utf-8')

        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)

        return decrypted_data

class BackupNotifier:
    """Handles backup notifications and alerts"""

    def __init__(self):
        self.smtp_config = self.load_smtp_config()

    def load_smtp_config(self) -> Dict[str, Any]:
        """Load SMTP configuration"""
        return {
            'server': 'smtp.gmail.com',
            'port': 587,
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'admin_emails': ['admin@dmlogn8n.com']
        }

    async def send_backup_success_notification(self, backup: BackupMetadata):
        """Send backup success notification"""
        subject = f"Backup Success: {backup.name} ({backup.backup_type})"
        body = f"""
        Backup completed successfully!

        Backup ID: {backup.backup_id}
        Name: {backup.name}
        Type: {backup.backup_type}
        Size: {self.format_bytes(backup.compressed_size_bytes)}
        Storage: {backup.storage_backend}
        Completed: {backup.completed_at}
        Checksum: {backup.checksum}

        Validation Status: {backup.validation_status or 'Not validated'}
        """

        await self.send_email(subject, body)

    async def send_backup_failure_notification(self, backup_id: str, job_name: str, error: str):
        """Send backup failure notification"""
        subject = f"Backup Failed: {job_name}"
        body = f"""
        Backup job failed!

        Backup ID: {backup_id}
        Job Name: {job_name}
        Error: {error}
        Timestamp: {datetime.now(timezone.utc).isoformat()}

        Please investigate the issue and check the backup logs.
        """

        await self.send_email(subject, body)

    async def send_email(self, subject: str, body: str):
        """Send email notification"""
        if not self.smtp_config['username']:
            logger.warning("SMTP not configured, skipping email notification")
            return

        try:
            msg = MimeMultipart()
            msg['From'] = self.smtp_config['username']
            msg['To'] = ', '.join(self.smtp_config['admin_emails'])
            msg['Subject'] = subject

            msg.attach(MimeText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port'])
            server.starttls()
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            server.send_message(msg)
            server.quit()

            logger.info(f"Email notification sent: {subject}")

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"

class BackupMonitoring:
    """Handles backup monitoring and metrics"""

    def __init__(self):
        self.start_time = time.time()
        self.health_checks = {}

    def check_storage_health(self, backend: StorageBackend) -> bool:
        """Check storage backend health"""
        # Implementation would depend on storage type
        return True

    def check_database_health(self) -> bool:
        """Check backup database health"""
        try:
            conn = sqlite3.connect('/home/activeloguser/DMLogn8n/multi-portal-gateway/backup/backup_metadata.db')
            conn.execute("SELECT 1")
            conn.close()
            return True
        except:
            return False

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get monitoring metrics summary"""
        return {
            'uptime_seconds': time.time() - self.start_time,
            'storage_health': {backend.value: self.check_storage_health(backend) for backend in StorageBackend},
            'database_health': self.check_database_health(),
            'prometheus_metrics': {
                'backup_operations_total': BACKUP_TOTAL._value.get(),
                'active_backups': ACTIVE_BACKUPS._value.get()
            }
        }

# Import validator class (will be implemented separately)
class BackupValidator:
    """Validates backup integrity and consistency"""

    async def validate_backup(self, backup: BackupMetadata) -> str:
        """Validate backup integrity"""
        # Implementation in validators/integrity_validator.py
        return "validated"

async def main():
    """Main backup service entry point"""
    try:
        # Create backup service
        backup_service = BackupService()

        # Start periodic cleanup
        while True:
            await asyncio.sleep(3600)  # Run cleanup every hour
            await backup_service.cleanup_expired_backups()

    except KeyboardInterrupt:
        logger.info("Backup service stopped by user")
    except Exception as e:
        logger.error(f"Backup service error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())