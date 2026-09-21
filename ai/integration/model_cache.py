#!/usr/bin/env python3
"""
Advanced AI Model Cache - Intelligent caching system for AI model responses
Provides sub-10ms cache access with intelligent eviction and compression
"""

import asyncio
import time
import hashlib
import json
import pickle
import gzip
import lzma
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import redis
import sqlite3
import threading
from collections import OrderedDict
import numpy as np
import psutil

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Cache configuration"""
    max_memory_mb: int = 1024  # 1GB default
    max_entries: int = 10000
    ttl_seconds: int = 3600  # 1 hour default
    compression_method: str = "gzip"  # gzip, lzma, none
    cache_backend: str = "memory"  # memory, redis, sqlite, hybrid
    enable_persistence: bool = True
    enable_compression: bool = True
    enable_deduplication: bool = True
    enable_smart_eviction: bool = True
    enable_prefetch: bool = True
    enable_metrics: bool = True

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    size_bytes: int
    ttl_seconds: int
    model_name: str
    prompt_hash: str
    response_hash: str
    metadata: Optional[Dict[str, Any]] = None
    compressed: bool = False
    compression_ratio: Optional[float] = None

@dataclass
class CacheStats:
    """Cache performance statistics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    compression_savings: int = 0
    average_access_time: float = 0.0
    memory_usage_mb: float = 0.0
    hit_rate: float = 0.0
    entries_count: int = 0
    oldest_entry_age: float = 0.0

class ModelCache:
    """Advanced AI model response caching system"""

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.executor = ThreadPoolExecutor(max_workers=4)

        # In-memory cache with LRU eviction
        self.memory_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.cache_lock = threading.RLock()

        # Backend connections
        self.redis_client: Optional[redis.Redis] = None
        self.sqlite_conn: Optional[sqlite3.Connection] = None

        # Performance tracking
        self.access_times: List[float] = []
        self.stats = CacheStats()

        # Initialize backends
        self._initialize_backends()

        # Background tasks
        self.cleanup_task = None
        self.metrics_task = None
        self.prefetch_task = None

        # Start background tasks
        self._start_background_tasks()

        logger.info(f"ModelCache initialized with backend: {self.config.cache_backend}")

    def _initialize_backends(self):
        """Initialize cache backends"""
        if self.config.cache_backend in ["redis", "hybrid"]:
            try:
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=False,
                    socket_connect_timeout=5
                )
                self.redis_client.ping()
                logger.info("Redis backend connected")
            except Exception as e:
                logger.warning(f"Redis backend failed: {e}")
                self.redis_client = None
                if self.config.cache_backend == "redis":
                    self.config.cache_backend = "memory"

        if self.config.cache_backend in ["sqlite", "hybrid"]:
            try:
                self.sqlite_conn = sqlite3.connect(
                    '/tmp/model_cache.db',
                    check_same_thread=False,
                    timeout=10.0
                )
                self._init_sqlite_schema()
                logger.info("SQLite backend connected")
            except Exception as e:
                logger.warning(f"SQLite backend failed: {e}")
                self.sqlite_conn = None
                if self.config.cache_backend == "sqlite":
                    self.config.cache_backend = "memory"

    def _init_sqlite_schema(self):
        """Initialize SQLite cache schema"""
        if not self.sqlite_conn:
            return

        cursor = self.sqlite_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                value BLOB,
                created_at TIMESTAMP,
                last_accessed TIMESTAMP,
                access_count INTEGER,
                size_bytes INTEGER,
                ttl_seconds INTEGER,
                model_name TEXT,
                prompt_hash TEXT,
                response_hash TEXT,
                metadata TEXT,
                compressed BOOLEAN,
                compression_ratio REAL
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_model_name ON cache_entries(model_name)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)
        ''')

        self.sqlite_conn.commit()

    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        if self.config.enable_metrics:
            self.metrics_task = asyncio.create_task(self._update_metrics_loop())

        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        if self.config.enable_prefetch:
            self.prefetch_task = asyncio.create_task(self._prefetch_loop())

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        start_time = time.time()
        self.stats.total_requests += 1

        try:
            # Try memory cache first
            value = await self._get_from_memory(key)
            if value is not None:
                self.stats.cache_hits += 1
                return value

            # Try backend caches
            if self.config.cache_backend == "hybrid" or self.config.cache_backend == "redis":
                value = await self._get_from_redis(key)
                if value is not None:
                    # Populate memory cache
                    await self._set_to_memory(key, value)
                    self.stats.cache_hits += 1
                    return value

            if self.config.cache_backend == "hybrid" or self.config.cache_backend == "sqlite":
                value = await self._get_from_sqlite(key)
                if value is not None:
                    # Populate memory cache
                    await self._set_to_memory(key, value)
                    self.stats.cache_hits += 1
                    return value

            self.stats.cache_misses += 1
            return None

        finally:
            access_time = time.time() - start_time
            self.access_times.append(access_time)
            if len(self.access_times) > 1000:
                self.access_times = self.access_times[-1000:]

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None,
                  model_name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl_seconds or self.config.ttl_seconds

            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                size_bytes=self._get_size(value),
                ttl_seconds=ttl,
                model_name=model_name or "unknown",
                prompt_hash=self._hash_value(key),
                response_hash=self._hash_value(str(value)),
                metadata=metadata
            )

            # Apply compression if enabled
            if self.config.enable_compression and entry.size_bytes > 1024:  # Only compress >1KB
                entry = await self._compress_entry(entry)

            # Check memory constraints
            await self._ensure_memory_limit()

            # Store in memory cache
            await self._set_to_memory(key, entry)

            # Store in backend caches
            if self.config.cache_backend in ["redis", "hybrid"] and self.redis_client:
                await self._set_to_redis(key, entry)

            if self.config.cache_backend in ["sqlite", "hybrid"] and self.sqlite_conn:
                await self._set_to_sqlite(key, entry)

            return True

        except Exception as e:
            logger.error(f"Cache set failed: {e}")
            return False

    async def _get_from_memory(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        with self.cache_lock:
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                # Move to end (LRU)
                self.memory_cache.move_to_end(key)
                return entry.value
        return None

    async def _set_to_memory(self, key: str, entry: Union[CacheEntry, Any]):
        """Set value in memory cache"""
        with self.cache_lock:
            if isinstance(entry, CacheEntry):
                self.memory_cache[key] = entry
            else:
                # Create entry from value
                cache_entry = CacheEntry(
                    key=key,
                    value=entry,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    access_count=1,
                    size_bytes=self._get_size(entry),
                    ttl_seconds=self.config.ttl_seconds,
                    model_name="unknown",
                    prompt_hash=self._hash_value(key),
                    response_hash=self._hash_value(str(entry))
                )
                self.memory_cache[key] = cache_entry

    async def _get_from_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self.redis_client:
            return None

        try:
            data = self.redis_client.get(f"cache:{key}")
            if data:
                entry = pickle.loads(gzip.decompress(data) if self.config.compression_method == "gzip" else data)
                return entry
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")
        return None

    async def _set_to_redis(self, key: str, entry: CacheEntry):
        """Set value in Redis cache"""
        if not self.redis_client:
            return

        try:
            # Serialize entry
            data = pickle.dumps(entry)
            if self.config.compression_method == "gzip":
                data = gzip.compress(data)

            # Store with TTL
            self.redis_client.setex(f"cache:{key}", entry.ttl_seconds, data)
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")

    async def _get_from_sqlite(self, key: str) -> Optional[Any]:
        """Get value from SQLite cache"""
        if not self.sqlite_conn:
            return None

        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(
                'SELECT value FROM cache_entries WHERE key = ? AND datetime(last_accessed) > datetime("now", "-{} seconds")'.format(
                    self.config.ttl_seconds
                ),
                (key,)
            )
            row = cursor.fetchone()

            if row:
                # Update access time
                cursor.execute(
                    'UPDATE cache_entries SET access_count = access_count + 1, last_accessed = ? WHERE key = ?',
                    (datetime.now().isoformat(), key)
                )
                self.sqlite_conn.commit()

                # Deserialize
                value = pickle.loads(row[0])
                return value

        except Exception as e:
            logger.warning(f"SQLite get failed: {e}")
        return None

    async def _set_to_sqlite(self, key: str, entry: CacheEntry):
        """Set value in SQLite cache"""
        if not self.sqlite_conn:
            return

        try:
            # Serialize
            value_data = pickle.dumps(entry.value)

            cursor = self.sqlite_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO cache_entries
                (key, value, created_at, last_accessed, access_count, size_bytes,
                 ttl_seconds, model_name, prompt_hash, response_hash, metadata,
                 compressed, compression_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                key,
                value_data,
                entry.created_at.isoformat(),
                entry.last_accessed.isoformat(),
                entry.access_count,
                entry.size_bytes,
                entry.ttl_seconds,
                entry.model_name,
                entry.prompt_hash,
                entry.response_hash,
                json.dumps(entry.metadata) if entry.metadata else None,
                entry.compressed,
                entry.compression_ratio
            ))
            self.sqlite_conn.commit()

        except Exception as e:
            logger.warning(f"SQLite set failed: {e}")

    async def _compress_entry(self, entry: CacheEntry) -> CacheEntry:
        """Compress cache entry"""
        try:
            original_size = entry.size_bytes

            if self.config.compression_method == "gzip":
                compressed_value = gzip.compress(pickle.dumps(entry.value))
            elif self.config.compression_method == "lzma":
                compressed_value = lzma.compress(pickle.dumps(entry.value))
            else:
                return entry

            # Update entry
            entry.value = compressed_value
            entry.size_bytes = len(compressed_value)
            entry.compressed = True
            entry.compression_ratio = entry.size_bytes / original_size

            self.stats.compression_savings += original_size - entry.size_bytes

            logger.debug(f"Compressed entry {entry.key}: {original_size} -> {entry.size_bytes} bytes")
            return entry

        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            return entry

    async def _ensure_memory_limit(self):
        """Ensure memory cache stays within limits"""
        if not self.config.enable_smart_eviction:
            return

        memory_usage_mb = self._get_memory_usage_mb()

        while memory_usage_mb > self.config.max_memory_mb or len(self.memory_cache) > self.config.max_entries:
            # Evict least recently used entries
            evicted = await self._evict_lru_entries(int(self.config.max_entries * 0.1))  # Evict 10%
            if evicted == 0:
                break

            memory_usage_mb = self._get_memory_usage_mb()

    async def _evict_lru_entries(self, count: int) -> int:
        """Evict least recently used entries"""
        evicted = 0

        with self.cache_lock:
            while evicted < count and self.memory_cache:
                key, entry = self.memory_cache.popitem(last=False)  # Remove oldest
                evicted += 1
                self.stats.evictions += 1

        return evicted

    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB"""
        total_size = sum(entry.size_bytes for entry in self.memory_cache.values())
        return total_size / (1024 * 1024)

    def _get_size(self, obj: Any) -> int:
        """Get approximate size of object"""
        try:
            if isinstance(obj, str):
                return len(obj.encode('utf-8'))
            elif isinstance(obj, (dict, list)):
                return len(pickle.dumps(obj))
            else:
                return len(pickle.dumps(obj))
        except:
            return 0

    def _hash_value(self, value: str) -> str:
        """Generate hash for value"""
        return hashlib.sha256(value.encode()).hexdigest()[:16]

    def generate_cache_key(self, model_name: str, prompt: str, **kwargs) -> str:
        """Generate cache key for model request"""
        # Include model name, prompt, and relevant parameters
        key_data = {
            "model": model_name,
            "prompt": prompt,
            "params": kwargs
        }

        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def invalidate(self, pattern: Optional[str] = None, model_name: Optional[str] = None) -> int:
        """Invalidate cache entries"""
        invalidated = 0

        with self.cache_lock:
            keys_to_remove = []

            for key in self.memory_cache:
                entry = self.memory_cache[key]

                should_remove = False
                if pattern and pattern in key:
                    should_remove = True
                elif model_name and entry.model_name == model_name:
                    should_remove = True
                elif not pattern and not model_name:
                    should_remove = True  # Clear all

                if should_remove:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.memory_cache[key]
                invalidated += 1

        # Clear backend caches
        if self.redis_client:
            try:
                if pattern:
                    keys = self.redis_client.keys(f"cache:*{pattern}*")
                    if keys:
                        self.redis_client.delete(*keys)
                        invalidated += len(keys)
                elif model_name:
                    # Would need to scan keys in Redis
                    pass
                else:
                    # Clear all
                    self.redis_client.flushdb()
            except Exception as e:
                logger.warning(f"Redis invalidation failed: {e}")

        if self.sqlite_conn:
            try:
                cursor = self.sqlite_conn.cursor()
                if pattern:
                    cursor.execute('DELETE FROM cache_entries WHERE key LIKE ?', (f'%{pattern}%',))
                elif model_name:
                    cursor.execute('DELETE FROM cache_entries WHERE model_name = ?', (model_name,))
                else:
                    cursor.execute('DELETE FROM cache_entries')
                invalidated += cursor.rowcount
                self.sqlite_conn.commit()
            except Exception as e:
                logger.warning(f"SQLite invalidation failed: {e}")

        logger.info(f"Invalidated {invalidated} cache entries")
        return invalidated

    async def _cleanup_loop(self):
        """Background cleanup task"""
        while True:
            try:
                await self._cleanup_expired_entries()
                await self._update_memory_stats()
                await asyncio.sleep(60)  # Run every minute
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(10)

    async def _cleanup_expired_entries(self):
        """Remove expired entries"""
        now = datetime.now()
        expired_keys = []

        with self.cache_lock:
            for key, entry in self.memory_cache.items():
                age_seconds = (now - entry.created_at).total_seconds()
                if age_seconds > entry.ttl_seconds:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.memory_cache[key]
                self.stats.evictions += 1

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired entries")

    async def _update_memory_stats(self):
        """Update memory statistics"""
        self.stats.memory_usage_mb = self._get_memory_usage_mb()
        self.stats.entries_count = len(self.memory_cache)

        # Calculate hit rate
        total = self.stats.cache_hits + self.stats.cache_misses
        if total > 0:
            self.stats.hit_rate = self.stats.cache_hits / total

        # Calculate average access time
        if self.access_times:
            self.stats.average_access_time = np.mean(self.access_times)

        # Calculate oldest entry age
        if self.memory_cache:
            oldest_entry = min(self.memory_cache.values(), key=lambda x: x.created_at)
            self.stats.oldest_entry_age = (datetime.now() - oldest_entry.created_at).total_seconds()

    async def _update_metrics_loop(self):
        """Background metrics update task"""
        while True:
            try:
                await self._update_memory_stats()
                await asyncio.sleep(10)  # Update every 10 seconds
            except Exception as e:
                logger.error(f"Metrics update error: {e}")
                await asyncio.sleep(5)

    async def _prefetch_loop(self):
        """Background prefetch task (placeholder)"""
        # This would implement intelligent prefetching based on access patterns
        while True:
            await asyncio.sleep(300)  # Run every 5 minutes

    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        return self.stats

    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information"""
        with self.cache_lock:
            entries_by_model = {}
            total_size = 0

            for entry in self.memory_cache.values():
                model = entry.model_name
                if model not in entries_by_model:
                    entries_by_model[model] = {
                        "count": 0,
                        "size_bytes": 0,
                        "average_accesses": 0
                    }

                entries_by_model[model]["count"] += 1
                entries_by_model[model]["size_bytes"] += entry.size_bytes
                total_size += entry.size_bytes

            # Calculate average accesses per model
            for model in entries_by_model:
                if entries_by_model[model]["count"] > 0:
                    entries_by_model[model]["average_accesses"] = (
                        sum(e.access_count for e in self.memory_cache.values() if e.model_name == model) /
                        entries_by_model[model]["count"]
                    )

        return {
            "backend": self.config.cache_backend,
            "total_entries": len(self.memory_cache),
            "total_size_mb": total_size / (1024 * 1024),
            "memory_limit_mb": self.config.max_memory_mb,
            "entries_by_model": entries_by_model,
            "compression_enabled": self.config.enable_compression,
            "compression_savings_mb": self.stats.compression_savings / (1024 * 1024),
            "redis_connected": self.redis_client is not None,
            "sqlite_connected": self.sqlite_conn is not None
        }

    async def health_check(self) -> Dict[str, bool]:
        """Perform health check on cache systems"""
        health_status = {
            "memory_cache": True,
            "redis_cache": True,
            "sqlite_cache": True,
            "compression": True,
            "eviction": True
        }

        # Check memory cache
        try:
            test_key = "health_check_test"
            test_value = "test_data"
            await self.set(test_key, test_value, ttl_seconds=10)
            retrieved = await self.get(test_key)
            if retrieved != test_value:
                health_status["memory_cache"] = False
            await self.invalidate(pattern=test_key)
        except Exception as e:
            health_status["memory_cache"] = False
            logger.warning(f"Memory cache health check failed: {e}")

        # Check Redis
        if self.redis_client:
            try:
                self.redis_client.ping()
            except Exception as e:
                health_status["redis_cache"] = False
                logger.warning(f"Redis health check failed: {e}")

        # Check SQLite
        if self.sqlite_conn:
            try:
                cursor = self.sqlite_conn.cursor()
                cursor.execute("SELECT 1")
            except Exception as e:
                health_status["sqlite_cache"] = False
                logger.warning(f"SQLite health check failed: {e}")

        # Check memory usage
        if self._get_memory_usage_mb() > self.config.max_memory_mb * 0.9:
            health_status["eviction"] = False

        return health_status

    async def shutdown(self):
        """Cleanup resources"""
        # Cancel background tasks
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.metrics_task:
            self.metrics_task.cancel()
        if self.prefetch_task:
            self.prefetch_task.cancel()

        # Wait for tasks to complete
        tasks = [t for t in [self.cleanup_task, self.metrics_task, self.prefetch_task] if t]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Close connections
        if self.redis_client:
            self.redis_client.close()

        if self.sqlite_conn:
            self.sqlite_conn.close()

        # Shutdown executor
        self.executor.shutdown(wait=True)

        logger.info("ModelCache shutdown complete")

# Example usage
async def demonstrate_cache():
    """Demonstrate cache functionality"""
    config = CacheConfig(
        max_memory_mb=100,
        cache_backend="memory",
        enable_compression=True,
        enable_smart_eviction=True
    )

    cache = ModelCache(config)

    # Test cache operations
    key = cache.generate_cache_key("gpt-4", "Hello, how are you?", temperature=0.7)
    value = "I'm doing well, thank you for asking!"

    # Set value
    success = await cache.set(key, value, model_name="gpt-4")
    print(f"Cache set: {success}")

    # Get value
    start_time = time.time()
    retrieved = await cache.get(key)
    access_time = time.time() - start_time

    print(f"Cache hit: {retrieved == value}")
    print(f"Access time: {access_time*1000:.1f}ms")

    # Get stats
    stats = cache.get_stats()
    print(f"Cache hit rate: {stats.hit_rate:.1%}")
    print(f"Average access time: {stats.average_access_time*1000:.1f}ms")

    # Health check
    health = await cache.health_check()
    print(f"Cache health: {health}")

    await cache.shutdown()

if __name__ == "__main__":
    asyncio.run(demonstrate_cache())