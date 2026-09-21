#!/usr/bin/env python3
"""
Local Storage Backend - File system-based backup storage

This storage backend provides local file system storage with compression,
encryption, deduplication, and lifecycle management for backup files.
"""

import asyncio
import logging
import os
import shutil
import hashlib
import json
import gzip
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import sqlite3
import threading
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class StorageStatus(Enum):
    """Storage backend status"""
    AVAILABLE = "available"
    FULL = "full"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class CompressionType(Enum):
    """Compression algorithms"""
    GZIP = "gzip"
    BZIP2 = "bzip2"
    XZ = "xz"
    LZMA = "lzma"
    NONE = "none"

@dataclass
class LocalStorageConfig:
    """Local storage configuration"""
    base_path: str
    max_storage_gb: int = 1000
    compression_type: str = "gzip"
    compression_level: int = 6
    encryption_enabled: bool = True
    deduplication_enabled: bool = True
    retention_days: int = 90
    auto_cleanup: bool = True
    backup_structure: str = "date_based"  # date_based, hash_based, flat
    metadata_database: str = "local_storage.db"
    health_check_interval_seconds: int = 300

@dataclass
class StorageMetrics:
    """Storage metrics and statistics"""
    total_space_bytes: int
    used_space_bytes: int
    free_space_bytes: int
    total_files: int
    total_backups: int
    compression_ratio: float
    deduplication_ratio: float
    oldest_backup: Optional[datetime]
    newest_backup: Optional[datetime]

class LocalStorage:
    """Local file system storage backend for backups"""

    def __init__(self, config: Dict[str, Any]):
        if isinstance(config, dict):
            self.config = LocalStorageConfig(**config)
        else:
            self.config = config

        self.base_path = Path(self.config.base_path)
        self.metadata_db_path = self.base_path / self.config.metadata_database
        self.encryption_manager = None
        self.lock = threading.Lock()
        self.health_status = StorageStatus.AVAILABLE

        # Initialize storage
        self.init_storage()
        self.init_metadata_database()
        self.init_encryption_manager()

        # Start background tasks
        self.start_background_tasks()

        logger.info(f"Local storage backend initialized at: {self.base_path}")

    def init_storage(self):
        """Initialize storage directory structure"""
        # Create base directories
        directories = [
            self.base_path,
            self.base_path / "backups",
            self.base_path / "metadata",
            self.base_path / "temp",
            self.base_path / "chunks",  # For deduplication
            self.base_path / "indices"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            # Set appropriate permissions
            os.chmod(directory, 0o750)

        # Create retention directories if using date-based structure
        if self.config.backup_structure == "date_based":
            today = datetime.now(timezone.utc)
            date_dirs = [
                today.strftime("%Y/%m/%d"),  # Daily
                today.strftime("%Y/week_%W"),  # Weekly
                today.strftime("%Y/%m"),  # Monthly
            ]

            for date_dir in date_dirs:
                (self.base_path / "backups" / date_dir).mkdir(parents=True, exist_ok=True)

    def init_metadata_database(self):
        """Initialize metadata database"""
        with sqlite3.connect(self.metadata_db_path) as conn:
            # Backups table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    backup_id TEXT PRIMARY KEY,
                    original_filename TEXT NOT NULL,
                    storage_path TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    compressed_size_bytes INTEGER NOT NULL,
                    checksum TEXT NOT NULL,
                    compression_type TEXT NOT NULL,
                    encryption_key_id TEXT,
                    chunks_used TEXT,
                    created_at TIMESTAMP NOT NULL,
                    accessed_at TIMESTAMP,
                    retention_expires_at TIMESTAMP,
                    backup_type TEXT,
                    metadata TEXT,
                    tags TEXT
                )
            """)

            # Chunks table for deduplication
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_hash TEXT PRIMARY KEY,
                    chunk_path TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    reference_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP NOT NULL,
                    last_accessed TIMESTAMP
                )
            """)

            # Storage metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS storage_metrics (
                    id INTEGER PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    total_space_bytes INTEGER,
                    used_space_bytes INTEGER,
                    free_space_bytes INTEGER,
                    total_files INTEGER,
                    total_backups INTEGER,
                    compression_ratio REAL,
                    deduplication_ratio REAL
                )
            """)

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_backups_created_at ON backups(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_backups_retention ON backups(retention_expires_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_hash ON chunks(chunk_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_storage_metrics_timestamp ON storage_metrics(timestamp)")

    def init_encryption_manager(self):
        """Initialize encryption manager"""
        if self.config.encryption_enabled:
            from backup_service import EncryptionManager
            self.encryption_manager = EncryptionManager()

    def start_background_tasks(self):
        """Start background maintenance tasks"""
        if self.config.auto_cleanup:
            # Start cleanup thread
            cleanup_thread = threading.Thread(target=self.cleanup_worker, daemon=True)
            cleanup_thread.start()

        # Start health monitoring thread
        health_thread = threading.Thread(target=self.health_monitor_worker, daemon=True)
        health_thread.start()

    def cleanup_worker(self):
        """Background cleanup worker"""
        while True:
            try:
                self.cleanup_expired_backups()
                self.optimize_storage()
                time.sleep(3600)  # Run every hour
            except Exception as e:
                logger.error(f"Cleanup worker error: {e}")
                time.sleep(300)  # Retry after 5 minutes

    def health_monitor_worker(self):
        """Background health monitoring worker"""
        while True:
            try:
                self.check_storage_health()
                self.update_storage_metrics()
                time.sleep(self.config.health_check_interval_seconds)
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                self.health_status = StorageStatus.ERROR
                time.sleep(60)

    async def upload_backup(self, local_file_path: str, backup_id: str) -> str:
        """Upload backup to local storage"""
        logger.info(f"Uploading backup {backup_id} to local storage")

        try:
            # Check available space
            if not self.check_available_space(local_file_path):
                raise Exception("Insufficient storage space")

            # Generate storage path
            storage_path = self.generate_storage_path(backup_id, local_file_path)

            # Process and store backup
            final_path = await self.process_and_store_backup(
                local_file_path, storage_path, backup_id
            )

            # Record metadata
            await self.record_backup_metadata(
                backup_id, local_file_path, final_path
            )

            logger.info(f"Backup uploaded successfully: {backup_id} -> {final_path}")
            return final_path

        except Exception as e:
            logger.error(f"Failed to upload backup {backup_id}: {e}")
            raise

    async def download_backup(self, storage_path: str, local_destination: str) -> str:
        """Download backup from local storage"""
        logger.info(f"Downloading backup from {storage_path}")

        try:
            full_storage_path = self.base_path / storage_path

            if not full_storage_path.exists():
                raise Exception(f"Backup not found: {storage_path}")

            # Create destination directory
            os.makedirs(os.path.dirname(local_destination), exist_ok=True)

            # Download and restore if necessary
            await self.restore_backup_file(
                full_storage_path, local_destination, storage_path
            )

            # Update access time
            self.update_access_time(storage_path)

            logger.info(f"Backup downloaded successfully: {storage_path} -> {local_destination}")
            return local_destination

        except Exception as e:
            logger.error(f"Failed to download backup {storage_path}: {e}")
            raise

    async def delete_backup(self, storage_path: str) -> bool:
        """Delete backup from local storage"""
        logger.info(f"Deleting backup: {storage_path}")

        try:
            full_storage_path = self.base_path / storage_path

            if not full_storage_path.exists():
                logger.warning(f"Backup not found for deletion: {storage_path}")
                return False

            # Get backup metadata before deletion
            backup_metadata = self.get_backup_metadata(storage_path)

            # Delete the file
            if full_storage_path.is_file():
                full_storage_path.unlink()
            elif full_storage_path.is_dir():
                shutil.rmtree(full_storage_path)

            # Update chunks reference count if deduplication is enabled
            if self.config.deduplication_enabled and backup_metadata:
                await self.update_chunk_references(backup_metadata, decrement=True)

            # Remove from metadata database
            self.remove_backup_metadata(storage_path)

            logger.info(f"Backup deleted successfully: {storage_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete backup {storage_path}: {e}")
            return False

    async def process_and_store_backup(self, local_file_path: str, storage_path: str, backup_id: str) -> str:
        """Process backup file (compress, encrypt, deduplicate) and store"""
        temp_file = None

        try:
            # Create temporary file for processing
            temp_dir = self.base_path / "temp"
            temp_file = temp_dir / f"processing_{backup_id}_{int(time.time())}"

            # Step 1: Deduplication (if enabled)
            if self.config.deduplication_enabled:
                temp_file = await self.deduplicate_file(local_file_path, temp_file)
            else:
                shutil.copy2(local_file_path, temp_file)

            # Step 2: Compression (if enabled)
            if self.config.compression_type != CompressionType.NONE.value:
                compressed_file = temp_file.with_suffix(temp_file.suffix + '.compressed')
                await self.compress_file(temp_file, compressed_file)
                temp_file = compressed_file

            # Step 3: Encryption (if enabled)
            if self.config.encryption_enabled:
                encrypted_file = temp_file.with_suffix(temp_file.suffix + '.enc')
                await self.encrypt_file(temp_file, encrypted_file)
                temp_file = encrypted_file

            # Move to final storage location
            final_path = self.base_path / storage_path
            final_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(temp_file), str(final_path))

            return str(final_path.relative_to(self.base_path))

        finally:
            # Cleanup temporary files
            if temp_file and temp_file.exists():
                temp_file.unlink()

    async def deduplicate_file(self, source_file: Path, temp_file: Path) -> Path:
        """Deduplicate file using chunk-based deduplication"""
        chunk_size = 64 * 1024  # 64KB chunks
        chunk_hashes = []
        chunks_used = []

        with open(source_file, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                chunk_hash = hashlib.sha256(chunk).hexdigest()
                chunk_hashes.append(chunk_hash)

                # Check if chunk already exists
                chunk_path = await self.get_or_create_chunk(chunk, chunk_hash)
                chunks_used.append(chunk_hash)

        # Create file manifest
        manifest = {
            'chunks': chunk_hashes,
            'chunk_size': chunk_size,
            'original_size': source_file.stat().st_size
        }

        # Write manifest and reconstruct file
        with open(temp_file, 'wb') as f:
            # Write manifest header
            manifest_json = json.dumps(manifest).encode('utf-8')
            manifest_size = len(manifest_json)
            f.write(manifest_size.to_bytes(4, 'big'))
            f.write(manifest_json)

            # Write chunk data
            for chunk_hash in chunk_hashes:
                chunk_path = self.base_path / "chunks" / chunk_hash
                with open(chunk_path, 'rb') as chunk_file:
                    f.write(chunk_file.read())

        return temp_file

    async def get_or_create_chunk(self, chunk_data: bytes, chunk_hash: str) -> Path:
        """Get existing chunk or create new one"""
        chunk_path = self.base_path / "chunks" / chunk_hash

        if chunk_path.exists():
            # Update reference count
            with sqlite3.connect(self.metadata_db_path) as conn:
                conn.execute(
                    "UPDATE chunks SET reference_count = reference_count + 1, last_accessed = ? WHERE chunk_hash = ?",
                    (datetime.now(timezone.utc), chunk_hash)
                )
        else:
            # Create new chunk
            with open(chunk_path, 'wb') as f:
                f.write(chunk_data)

            with sqlite3.connect(self.metadata_db_path) as conn:
                conn.execute(
                    "INSERT INTO chunks (chunk_hash, chunk_path, size_bytes, reference_count, created_at, last_accessed) VALUES (?, ?, ?, ?, ?, ?)",
                    (chunk_hash, str(chunk_path), len(chunk_data), 1, datetime.now(timezone.utc), datetime.now(timezone.utc))
                )

        return chunk_path

    async def compress_file(self, source_file: Path, target_file: Path):
        """Compress file using configured compression type"""
        if self.config.compression_type == CompressionType.GZIP.value:
            with open(source_file, 'rb') as f_in:
                with gzip.open(target_file, 'wb', compresslevel=self.config.compression_level) as f_out:
                    shutil.copyfileobj(f_in, f_out)
        elif self.config.compression_type == CompressionType.BZIP2.value:
            import bz2
            with open(source_file, 'rb') as f_in:
                with bz2.open(target_file, 'wb', compresslevel=self.config.compression_level) as f_out:
                    shutil.copyfileobj(f_in, f_out)
        elif self.config.compression_type == CompressionType.XZ.value:
            import lzma
            with open(source_file, 'rb') as f_in:
                with lzma.open(target_file, 'wb', preset=self.config.compression_level) as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            # No compression
            shutil.copy2(source_file, target_file)

    async def encrypt_file(self, source_file: Path, target_file: Path):
        """Encrypt file using encryption manager"""
        if not self.encryption_manager:
            raise Exception("Encryption enabled but encryption manager not initialized")

        with open(source_file, 'rb') as f:
            data = f.read()

        encrypted_data, key_id = self.encryption_manager.encrypt_data(data)

        # Store key_id in file header
        with open(target_file, 'wb') as f:
            # Write key ID length and key ID
            key_id_bytes = key_id.encode('utf-8')
            f.write(len(key_id_bytes).to_bytes(2, 'big'))
            f.write(key_id_bytes)
            # Write encrypted data
            f.write(encrypted_data)

    async def restore_backup_file(self, storage_path: Path, destination: str, storage_id: str):
        """Restore backup file from storage (decompress, decrypt, deduplicate)"""
        temp_file = None

        try:
            temp_dir = self.base_path / "temp"
            temp_file = temp_dir / f"restore_{int(time.time())}"

            # Copy to temporary location for processing
            shutil.copy2(storage_path, temp_file)

            # Step 1: Decrypt (if encrypted)
            if self.is_file_encrypted(temp_file):
                decrypted_file = temp_file.with_suffix('.decrypted')
                await self.decrypt_file(temp_file, decrypted_file)
                temp_file = decrypted_file

            # Step 2: Decompress (if compressed)
            if self.is_file_compressed(temp_file):
                decompressed_file = temp_file.with_suffix('.decompressed')
                await self.decompress_file(temp_file, decompressed_file)
                temp_file = decompressed_file

            # Step 3: Restore from chunks (if deduplicated)
            if self.is_deduplicated_file(temp_file):
                restored_file = temp_file.with_suffix('.restored')
                await self.restore_from_chunks(temp_file, restored_file)
                temp_file = restored_file

            # Move to final destination
            shutil.move(str(temp_file), destination)

        finally:
            # Cleanup temporary files
            if temp_file and temp_file.exists():
                temp_file.unlink()

    def is_file_encrypted(self, file_path: Path) -> bool:
        """Check if file is encrypted"""
        try:
            with open(file_path, 'rb') as f:
                # Check if file starts with key ID length
                key_id_length_bytes = f.read(2)
                if len(key_id_length_bytes) == 2:
                    key_id_length = int.from_bytes(key_id_length_bytes, 'big')
                    if 0 < key_id_length <= 100:  # Reasonable key ID length
                        return True
            return False
        except:
            return False

    def is_file_compressed(self, file_path: Path) -> bool:
        """Check if file is compressed"""
        return file_path.suffix in ['.gz', '.bz2', '.xz', '.lzma']

    def is_deduplicated_file(self, file_path: Path) -> bool:
        """Check if file uses deduplication"""
        try:
            with open(file_path, 'rb') as f:
                # Read manifest size (first 4 bytes)
                manifest_size_bytes = f.read(4)
                if len(manifest_size_bytes) == 4:
                    manifest_size = int.from_bytes(manifest_size_bytes, 'big')
                    # Try to read and parse manifest
                    manifest_data = f.read(manifest_size)
                    manifest = json.loads(manifest_data.decode('utf-8'))
                    return 'chunks' in manifest
            return False
        except:
            return False

    async def decrypt_file(self, source_file: Path, target_file: Path):
        """Decrypt file using encryption manager"""
        if not self.encryption_manager:
            raise Exception("Encryption manager not initialized")

        with open(source_file, 'rb') as f:
            # Read key ID length and key ID
            key_id_length_bytes = f.read(2)
            key_id_length = int.from_bytes(key_id_length_bytes, 'big')
            key_id = f.read(key_id_length).decode('utf-8')

            # Read encrypted data
            encrypted_data = f.read()

        decrypted_data = self.encryption_manager.decrypt_data(encrypted_data, key_id)

        with open(target_file, 'wb') as f:
            f.write(decrypted_data)

    async def decompress_file(self, source_file: Path, target_file: Path):
        """Decompress file"""
        if source_file.suffix == '.gz':
            with gzip.open(source_file, 'rb') as f_in:
                with open(target_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        elif source_file.suffix == '.bz2':
            import bz2
            with bz2.open(source_file, 'rb') as f_in:
                with open(target_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        elif source_file.suffix == '.xz':
            import lzma
            with lzma.open(source_file, 'rb') as f_in:
                with open(target_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            # Unknown compression, copy as-is
            shutil.copy2(source_file, target_file)

    async def restore_from_chunks(self, source_file: Path, target_file: Path):
        """Restore file from deduplicated chunks"""
        with open(source_file, 'rb') as f:
            # Read manifest
            manifest_size_bytes = f.read(4)
            manifest_size = int.from_bytes(manifest_size_bytes, 'big')
            manifest_data = f.read(manifest_size)
            manifest = json.loads(manifest_data.decode('utf-8'))

        # Reconstruct file from chunks
        with open(target_file, 'wb') as f:
            for chunk_hash in manifest['chunks']:
                chunk_path = self.base_path / "chunks" / chunk_hash
                with open(chunk_path, 'rb') as chunk_file:
                    f.write(chunk_file.read())

        # Update chunk access times
        with sqlite3.connect(self.metadata_db_path) as conn:
            for chunk_hash in manifest['chunks']:
                conn.execute(
                    "UPDATE chunks SET last_accessed = ? WHERE chunk_hash = ?",
                    (datetime.now(timezone.utc), chunk_hash)
                )

    def generate_storage_path(self, backup_id: str, original_filename: str) -> str:
        """Generate storage path for backup"""
        if self.config.backup_structure == "date_based":
            now = datetime.now(timezone.utc)
            date_path = now.strftime("%Y/%m/%d")
            return f"backups/{date_path}/{backup_id}_{original_filename}"
        elif self.config.backup_structure == "hash_based":
            file_hash = hashlib.md5(backup_id.encode()).hexdigest()[:8]
            return f"backups/{file_hash[:2]}/{file_hash[2:4]}/{backup_id}_{original_filename}"
        else:  # flat
            return f"backups/{backup_id}_{original_filename}"

    def check_available_space(self, file_path: str) -> bool:
        """Check if enough space is available for file"""
        required_space = os.path.getsize(file_path)
        stat = shutil.disk_usage(self.base_path)

        # Reserve 10% of total space as buffer
        available_space = stat.free - (stat.total * 0.1)

        return available_space >= required_space

    def check_storage_health(self) -> StorageStatus:
        """Check storage health status"""
        try:
            stat = shutil.disk_usage(self.base_path)
            usage_percent = (stat.used / stat.total) * 100

            if usage_percent > 95:
                self.health_status = StorageStatus.FULL
            elif usage_percent > 90:
                logger.warning(f"Storage almost full: {usage_percent:.1f}%")
                self.health_status = StorageStatus.AVAILABLE
            else:
                self.health_status = StorageStatus.AVAILABLE

            # Check if storage is writable
            test_file = self.base_path / ".health_check"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except PermissionError:
                self.health_status = StorageStatus.ERROR
                logger.error("Storage is not writable")

            return self.health_status

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.health_status = StorageStatus.ERROR
            return self.health_status

    def update_storage_metrics(self):
        """Update storage metrics in database"""
        try:
            stat = shutil.disk_usage(self.base_path)

            # Count files and backups
            total_files = 0
            total_backups = 0
            total_size = 0
            compressed_size = 0

            backups_dir = self.base_path / "backups"
            if backups_dir.exists():
                for root, dirs, files in os.walk(backups_dir):
                    total_files += len(files)
                    for file in files:
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)

            # Get compression ratio from metadata
            compression_ratio = 1.0
            deduplication_ratio = 1.0

            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.execute("""
                    SELECT AVG(CAST(compressed_size_bytes AS FLOAT) / size_bytes) as avg_compression,
                           COUNT(*) as backup_count
                    FROM backups WHERE size_bytes > 0
                """)
                result = cursor.fetchone()
                if result and result[0]:
                    compression_ratio = result[0]
                    total_backups = result[1]

            metrics = {
                'total_space_bytes': stat.total,
                'used_space_bytes': stat.used,
                'free_space_bytes': stat.free,
                'total_files': total_files,
                'total_backups': total_backups,
                'compression_ratio': compression_ratio,
                'deduplication_ratio': deduplication_ratio
            }

            # Store in database
            with sqlite3.connect(self.metadata_db_path) as conn:
                conn.execute("""
                    INSERT INTO storage_metrics
                    (timestamp, total_space_bytes, used_space_bytes, free_space_bytes,
                     total_files, total_backups, compression_ratio, deduplication_ratio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (datetime.now(timezone.utc), **metrics))

        except Exception as e:
            logger.error(f"Failed to update storage metrics: {e}")

    def cleanup_expired_backups(self):
        """Clean up expired backups based on retention policy"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.config.retention_days)

            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.execute("""
                    SELECT backup_id, storage_path FROM backups
                    WHERE created_at < ? AND retention_expires_at < ?
                """, (cutoff_date, cutoff_date))

                expired_backups = cursor.fetchall()

                for backup_id, storage_path in expired_backups:
                    try:
                        full_path = self.base_path / storage_path
                        if full_path.exists():
                            if full_path.is_file():
                                full_path.unlink()
                            elif full_path.is_dir():
                                shutil.rmtree(full_path)

                        # Remove from database
                        conn.execute("DELETE FROM backups WHERE backup_id = ?", (backup_id,))
                        logger.info(f"Cleaned up expired backup: {backup_id}")

                    except Exception as e:
                        logger.error(f"Failed to cleanup backup {backup_id}: {e}")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    def optimize_storage(self):
        """Optimize storage by cleaning up unused chunks"""
        if not self.config.deduplication_enabled:
            return

        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                # Find chunks with reference count = 0
                cursor = conn.execute("""
                    SELECT chunk_hash, chunk_path FROM chunks
                    WHERE reference_count = 0
                """)

                unused_chunks = cursor.fetchall()

                for chunk_hash, chunk_path in unused_chunks:
                    try:
                        full_path = Path(chunk_path)
                        if full_path.exists():
                            full_path.unlink()

                        # Remove from database
                        conn.execute("DELETE FROM chunks WHERE chunk_hash = ?", (chunk_hash,))
                        logger.debug(f"Removed unused chunk: {chunk_hash}")

                    except Exception as e:
                        logger.error(f"Failed to remove chunk {chunk_hash}: {e}")

        except Exception as e:
            logger.error(f"Storage optimization failed: {e}")

    async def record_backup_metadata(self, backup_id: str, original_filename: str, storage_path: str):
        """Record backup metadata in database"""
        try:
            full_storage_path = self.base_path / storage_path
            file_stat = full_storage_path.stat()

            # Calculate checksum
            checksum = self.calculate_file_checksum(full_storage_path)

            # Get chunks used if deduplication
            chunks_used = None
            if self.config.deduplication_enabled and self.is_deduplicated_file(full_storage_path):
                chunks_used = self.get_chunks_used(full_storage_path)

            with sqlite3.connect(self.metadata_db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO backups
                    (backup_id, original_filename, storage_path, size_bytes, compressed_size_bytes,
                     checksum, compression_type, encryption_key_id, chunks_used, created_at,
                     accessed_at, retention_expires_at, backup_type, metadata, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    backup_id,
                    original_filename,
                    storage_path,
                    file_stat.st_size,
                    file_stat.st_size,  # Will be updated after compression
                    checksum,
                    self.config.compression_type,
                    None,  # encryption_key_id - to be implemented
                    json.dumps(chunks_used) if chunks_used else None,
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc) + timedelta(days=self.config.retention_days),
                    'full',  # backup_type
                    '{}',  # metadata
                    '{}'   # tags
                ))

        except Exception as e:
            logger.error(f"Failed to record backup metadata: {e}")

    def calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def get_chunks_used(self, file_path: Path) -> List[str]:
        """Get list of chunks used by deduplicated file"""
        try:
            with open(file_path, 'rb') as f:
                # Read manifest
                manifest_size_bytes = f.read(4)
                manifest_size = int.from_bytes(manifest_size_bytes, 'big')
                manifest_data = f.read(manifest_size)
                manifest = json.loads(manifest_data.decode('utf-8'))
                return manifest.get('chunks', [])
        except:
            return []

    def update_access_time(self, storage_path: str):
        """Update backup access time"""
        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                conn.execute(
                    "UPDATE backups SET accessed_at = ? WHERE storage_path = ?",
                    (datetime.now(timezone.utc), storage_path)
                )
        except Exception as e:
            logger.error(f"Failed to update access time: {e}")

    def get_backup_metadata(self, storage_path: str) -> Optional[Dict[str, Any]]:
        """Get backup metadata"""
        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM backups WHERE storage_path = ?
                """, (storage_path,))
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Failed to get backup metadata: {e}")
            return None

    def remove_backup_metadata(self, storage_path: str):
        """Remove backup metadata from database"""
        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                conn.execute("DELETE FROM backups WHERE storage_path = ?", (storage_path,))
        except Exception as e:
            logger.error(f"Failed to remove backup metadata: {e}")

    async def update_chunk_references(self, backup_metadata: Dict[str, Any], decrement: bool = False):
        """Update chunk reference counts"""
        if not backup_metadata or not backup_metadata.get('chunks_used'):
            return

        try:
            chunks_used = json.loads(backup_metadata['chunks_used'])
            operation = -1 if decrement else 1

            with sqlite3.connect(self.metadata_db_path) as conn:
                for chunk_hash in chunks_used:
                    conn.execute(
                        "UPDATE chunks SET reference_count = reference_count + ? WHERE chunk_hash = ?",
                        (operation, chunk_hash)
                    )

        except Exception as e:
            logger.error(f"Failed to update chunk references: {e}")

    def get_storage_metrics(self) -> StorageMetrics:
        """Get current storage metrics"""
        try:
            stat = shutil.disk_usage(self.base_path)

            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) as total_backups,
                           MIN(created_at) as oldest_backup,
                           MAX(created_at) as newest_backup
                    FROM backups
                """)
                result = cursor.fetchone()
                total_backups = result[0] if result else 0
                oldest_backup = datetime.fromisoformat(result[1]) if result and result[1] else None
                newest_backup = datetime.fromisoformat(result[2]) if result and result[2] else None

                # Count files
                total_files = 0
                backups_dir = self.base_path / "backups"
                if backups_dir.exists():
                    for root, dirs, files in os.walk(backups_dir):
                        total_files += len(files)

            return StorageMetrics(
                total_space_bytes=stat.total,
                used_space_bytes=stat.used,
                free_space_bytes=stat.free,
                total_files=total_files,
                total_backups=total_backups,
                compression_ratio=1.0,  # Calculate from actual data
                deduplication_ratio=1.0,  # Calculate from actual data
                oldest_backup=oldest_backup,
                newest_backup=newest_backup
            )

        except Exception as e:
            logger.error(f"Failed to get storage metrics: {e}")
            return StorageMetrics(0, 0, 0, 0, 0, 1.0, 1.0, None, None)

    def list_backups(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List backups in storage"""
        try:
            with sqlite3.connect(self.metadata_db_path) as conn:
                cursor = conn.execute("""
                    SELECT * FROM backups
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))

                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []

    def get_storage_status(self) -> Dict[str, Any]:
        """Get storage status information"""
        metrics = self.get_storage_metrics()
        health = self.check_storage_health()

        return {
            'status': health.value,
            'base_path': str(self.base_path),
            'metrics': {
                'total_space_gb': metrics.total_space_bytes / (1024**3),
                'used_space_gb': metrics.used_space_bytes / (1024**3),
                'free_space_gb': metrics.free_space_bytes / (1024**3),
                'usage_percent': (metrics.used_space_bytes / metrics.total_space_bytes) * 100,
                'total_files': metrics.total_files,
                'total_backups': metrics.total_backups,
                'compression_ratio': metrics.compression_ratio,
                'deduplication_ratio': metrics.deduplication_ratio
            },
            'configuration': {
                'compression_type': self.config.compression_type,
                'compression_level': self.config.compression_level,
                'encryption_enabled': self.config.encryption_enabled,
                'deduplication_enabled': self.config.deduplication_enabled,
                'retention_days': self.config.retention_days,
                'backup_structure': self.config.backup_structure
            }
        }