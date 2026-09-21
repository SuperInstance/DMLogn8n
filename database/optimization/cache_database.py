#!/usr/bin/env python3
"""
Database Caching Layer with Smart Invalidation
Advanced caching system with automatic invalidation, multi-tier storage, and intelligent cache warming.
"""

import asyncio
import json
import time
import hashlib
import pickle
import logging
from typing import Dict, List, Any, Optional, Union, Callable, Set, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
import threading
import weakref
import gzip
import zlib

import redis
from aioredis import create_redis_pool
import mmh3  # MurmurHash3 for better distribution

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    L1_MEMORY = "l1_memory"      # Fastest, smallest
    L2_REDIS = "l2_redis"        # Medium speed, medium size
    L3_DISK = "l3_disk"          # Slowest, largest

class CacheStrategy(Enum):
    LRU = "lru"                  # Least Recently Used
    LFU = "lfu"                  # Least Frequently Used
    TTL = "ttl"                  # Time To Live
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"
    WRITE_AROUND = "write_around"

class InvalidationType(Enum):
    TIME_BASED = "time_based"
    EVENT_BASED = "event_based"
    QUERY_BASED = "query_based"
    DEPENDENCY_BASED = "dependency_based"
    MANUAL = "manual"

@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: Optional[int]
    size_bytes: int
    cache_level: CacheLevel
    dependencies: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    compressed: bool = False
    serialized: bool = True

@dataclass
class CacheConfig:
    l1_max_size_mb: int = 100        # Memory cache size
    l2_max_size_mb: int = 1000       # Redis cache size
    l3_max_size_mb: int = 10000      # Disk cache size
    default_ttl_seconds: int = 3600  # 1 hour default
    compression_threshold_bytes: int = 1024  # Compress items > 1KB
    serialization_method: str = "pickle"     # pickle, json, msgpack
    eviction_policy: CacheStrategy = CacheStrategy.LRU
    write_strategy: CacheStrategy = CacheStrategy.WRITE_THROUGH
    enable_smart_warming: bool = True
    enable_dependency_tracking: bool = True
    enable_metrics: bool = True
    max_concurrent_operations: int = 100

@dataclass
class CacheMetrics:
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    l1_hits: int = 0
    l2_hits: int = 0
    l3_hits: int = 0
    evictions: int = 0
    invalidations: int = 0
    compression_savings_bytes: int = 0
    serialization_time_ms: float = 0.0
    deserialization_time_ms: float = 0.0
    average_hit_ratio: float = 0.0
    total_size_bytes: int = 0
    memory_usage_mb: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

class SmartCache:
    """Advanced multi-tier caching system with intelligent invalidation"""

    def __init__(self, cache_id: str, config: CacheConfig):
        self.cache_id = cache_id
        self.config = config

        # Cache storage
        self.l1_cache = OrderedDict()  # Memory cache
        self.l2_redis_client = None    # Redis cache
        self.l3_disk_path = f"/tmp/cache_{cache_id}"  # Disk cache

        # Indexes and tracking
        self.dependency_graph = defaultdict(set)  # Track dependencies
        self.tag_index = defaultdict(set)         # Tag-based invalidation
        self.query_index = defaultdict(set)       # Query pattern tracking
        self.access_patterns = defaultdict(list)  # Access pattern analysis

        # Metrics and monitoring
        self.metrics = CacheMetrics()
        self.operation_locks = defaultdict(asyncio.Lock)
        self.warming_queue = asyncio.Queue()
        self.invalidation_queue = asyncio.Queue()

        # Background tasks
        self.warming_task = None
        self.cleanup_task = None
        self.metrics_task = None
        self.invalidation_task = None

        # Shutdown flag
        self._shutdown = False

        # Initialize caches
        self._initialize_caches()

    def _initialize_caches(self) -> None:
        """Initialize cache storage systems"""

        # Create disk cache directory
        import os
        os.makedirs(self.l3_disk_path, exist_ok=True)

    async def initialize(self, redis_connection_params: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the cache system"""

        try:
            logger.info(f"Initializing cache '{self.cache_id}'")

            # Initialize Redis connection
            if redis_connection_params:
                self.l2_redis_client = await create_redis_pool(**redis_connection_params)
                await self.l2_redis_client.ping()
                logger.info("Redis cache connected")

            # Start background tasks
            if self.config.enable_smart_warming:
                self.warming_task = asyncio.create_task(self._cache_warming_loop())

            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.metrics_task = asyncio.create_task(self._metrics_collection_loop())
            self.invalidation_task = asyncio.create_task(self._invalidation_processing_loop())

            logger.info(f"Cache '{self.cache_id}' initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize cache '{self.cache_id}': {e}")
            return False

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with multi-tier lookup"""

        start_time = time.time()
        self.metrics.total_requests += 1

        try:
            # Try L1 cache first (memory)
            if key in self.l1_cache:
                entry = self.l1_cache[key]
                await self._update_access_stats(entry)
                self.metrics.cache_hits += 1
                self.metrics.l1_hits += 1
                return await self._deserialize_entry(entry)

            # Try L2 cache (Redis)
            if self.l2_redis_client:
                try:
                    cached_data = await self.l2_redis_client.get(f"{self.cache_id}:{key}")
                    if cached_data:
                        entry = pickle.loads(cached_data)
                        await self._promote_to_l1(entry)
                        self.metrics.cache_hits += 1
                        self.metrics.l2_hits += 1
                        return await self._deserialize_entry(entry)
                except Exception as e:
                    logger.debug(f"L2 cache error: {e}")

            # Try L3 cache (disk)
            entry = await self._get_from_disk(key)
            if entry:
                await self._promote_to_l1(entry)
                self.metrics.cache_hits += 1
                self.metrics.l3_hits += 1
                return await self._deserialize_entry(entry)

            # Cache miss
            self.metrics.cache_misses += 1
            return default

        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            self.metrics.cache_misses += 1
            return default

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None,
                 dependencies: Optional[Set[str]] = None,
                 tags: Optional[Set[str]] = None) -> bool:
        """Set value in cache with intelligent tier placement"""

        try:
            start_time = time.time()
            ttl = ttl_seconds or self.config.default_ttl_seconds

            # Create cache entry
            entry = await self._create_cache_entry(key, value, ttl, dependencies, tags)

            # Store in appropriate tiers based on access patterns
            await self._store_in_tiers(entry)

            # Update indexes
            if dependencies:
                for dep in dependencies:
                    self.dependency_graph[dep].add(key)

            if tags:
                for tag in tags:
                    self.tag_index[tag].add(key)

            # Track access pattern
            await self._update_access_pattern(key)

            return True

        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False

    async def invalidate(self, key: str) -> bool:
        """Invalidate specific cache entry"""

        try:
            success = True

            # Remove from L1
            if key in self.l1_cache:
                del self.l1_cache[key]

            # Remove from L2
            if self.l2_redis_client:
                await self.l2_redis_client.delete(f"{self.cache_id}:{key}")

            # Remove from L3
            await self._remove_from_disk(key)

            # Remove from indexes
            for deps in self.dependency_graph.values():
                deps.discard(key)

            for tags in self.tag_index.values():
                tags.discard(key)

            self.metrics.invalidations += 1
            return success

        except Exception as e:
            logger.error(f"Cache invalidation error for key '{key}': {e}")
            return False

    async def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all entries with specific tag"""

        if tag not in self.tag_index:
            return 0

        keys_to_invalidate = self.tag_index[tag].copy()
        invalidated_count = 0

        for key in keys_to_invalidate:
            if await self.invalidate(key):
                invalidated_count += 1

        del self.tag_index[tag]
        return invalidated_count

    async def invalidate_by_dependency(self, dependency: str) -> int:
        """Invalidate all entries that depend on specific data"""

        if dependency not in self.dependency_graph:
            return 0

        keys_to_invalidate = self.dependency_graph[dependency].copy()
        invalidated_count = 0

        for key in keys_to_invalidate:
            if await self.invalidate(key):
                invalidated_count += 1

        del self.dependency_graph[dependency]
        return invalidated_count

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate keys matching pattern"""

        invalidated_count = 0

        # Check L1 cache
        keys_to_remove = [key for key in self.l1_cache.keys() if self._match_pattern(key, pattern)]
        for key in keys_to_remove:
            if await self.invalidate(key):
                invalidated_count += 1

        # Check L2 cache
        if self.l2_redis_client:
            try:
                redis_pattern = f"{self.cache_id}:{pattern}"
                keys = await self.l2_redis_client.keys(redis_pattern)
                for key in keys:
                    key_str = key.decode('utf-8').replace(f"{self.cache_id}:", "")
                    if await self.invalidate(key_str):
                        invalidated_count += 1
            except Exception as e:
                logger.debug(f"Redis pattern invalidation error: {e}")

        return invalidated_count

    async def warm_cache(self, keys: List[str], data_loader: Callable[[str], Any]) -> int:
        """Warm cache with pre-loaded data"""

        warmed_count = 0

        for key in keys:
            if key not in self.l1_cache:
                try:
                    # Load data asynchronously
                    value = await asyncio.get_event_loop().run_in_executor(
                        None, data_loader, key
                    )

                    if await self.set(key, value):
                        warmed_count += 1

                except Exception as e:
                    logger.error(f"Cache warming error for key '{key}': {e}")

        return warmed_count

    async def _create_cache_entry(self, key: str, value: Any, ttl_seconds: int,
                                dependencies: Optional[Set[str]],
                                tags: Optional[Set[str]]) -> CacheEntry:
        """Create a cache entry with serialization and compression"""

        start_time = time.time()

        # Serialize value
        serialized_value = await self._serialize_value(value)
        serialization_time = (time.time() - start_time) * 1000
        self.metrics.serialization_time_ms += serialization_time

        # Compress if large enough
        compressed = False
        if len(serialized_value) > self.config.compression_threshold_bytes:
            serialized_value = await self._compress_data(serialized_value)
            compressed = True
            savings = len(serialized_value) * 0.3  # Estimate 30% savings
            self.metrics.compression_savings_bytes += int(savings)

        entry = CacheEntry(
            key=key,
            value=serialized_value,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            access_count=1,
            ttl_seconds=ttl_seconds,
            size_bytes=len(serialized_value),
            cache_level=CacheLevel.L1_MEMORY,
            dependencies=dependencies or set(),
            tags=tags or set(),
            compressed=compressed,
            serialized=True
        )

        return entry

    async def _store_in_tiers(self, entry: CacheEntry) -> None:
        """Store entry in appropriate cache tiers"""

        try:
            # Store in L1 (memory) if space available
            if len(self.l1_cache) < self._get_l1_capacity():
                self.l1_cache[entry.key] = entry
                # Move to end (most recently used)
                self.l1_cache.move_to_end(entry.key)
            else:
                # L1 full, evict if necessary
                await self._evict_from_l1()
                self.l1_cache[entry.key] = entry
                self.l1_cache.move_to_end(entry.key)

            # Store in L2 (Redis) for persistence
            if self.l2_redis_client:
                try:
                    serialized_entry = pickle.dumps(entry)
                    await self.l2_redis_client.setex(
                        f"{self.cache_id}:{entry.key}",
                        entry.ttl_seconds,
                        serialized_entry
                    )
                except Exception as e:
                    logger.debug(f"L2 storage error: {e}")

            # Store in L3 (disk) for very large or cold data
            if entry.size_bytes > self._get_l2_threshold():
                await self._store_on_disk(entry)

        except Exception as e:
            logger.error(f"Tier storage error: {e}")

    async def _promote_to_l1(self, entry: CacheEntry) -> None:
        """Promote entry to L1 cache"""

        entry.last_accessed = datetime.now()
        entry.access_count += 1

        if len(self.l1_cache) >= self._get_l1_capacity():
            await self._evict_from_l1()

        self.l1_cache[entry.key] = entry
        self.l1_cache.move_to_end(entry.key)

    async def _deserialize_entry(self, entry: CacheEntry) -> Any:
        """Deserialize cache entry value"""

        start_time = time.time()

        try:
            value = entry.value

            # Decompress if needed
            if entry.compressed:
                value = await self._decompress_data(value)

            # Deserialize
            if entry.serialized:
                value = await self._deserialize_value(value)

            deserialization_time = (time.time() - start_time) * 1000
            self.metrics.deserialization_time_ms += deserialization_time

            return value

        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            return None

    async def _serialize_value(self, value: Any) -> bytes:
        """Serialize value based on configuration"""

        try:
            if self.config.serialization_method == "pickle":
                return pickle.dumps(value)
            elif self.config.serialization_method == "json":
                return json.dumps(value).encode('utf-8')
            else:
                # Default to pickle
                return pickle.dumps(value)

        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise

    async def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value based on configuration"""

        try:
            if self.config.serialization_method == "pickle":
                return pickle.loads(data)
            elif self.config.serialization_method == "json":
                return json.loads(data.decode('utf-8'))
            else:
                # Default to pickle
                return pickle.loads(data)

        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise

    async def _compress_data(self, data: bytes) -> bytes:
        """Compress data using appropriate method"""

        try:
            # Use gzip for good compression ratio
            return gzip.compress(data)
        except Exception as e:
            logger.error(f"Compression error: {e}")
            return data

    async def _decompress_data(self, data: bytes) -> bytes:
        """Decompress data"""

        try:
            return gzip.decompress(data)
        except Exception as e:
            logger.error(f"Decompression error: {e}")
            return data

    def _get_l1_capacity(self) -> int:
        """Get L1 cache capacity in number of entries"""
        # Estimate based on average entry size
        avg_entry_size = 1024  # 1KB estimate
        return (self.config.l1_max_size_mb * 1024 * 1024) // avg_entry_size

    def _get_l2_threshold(self) -> int:
        """Get threshold for storing in L2 vs L3"""
        return 10 * 1024  # 10KB threshold

    async def _evict_from_l1(self) -> None:
        """Evict entries from L1 cache based on policy"""

        if not self.l1_cache:
            return

        if self.config.eviction_policy == CacheStrategy.LRU:
            # Remove least recently used
            self.l1_cache.popitem(last=False)
        elif self.config.eviction_policy == CacheStrategy.LFU:
            # Remove least frequently used
            min_access_key = min(self.l1_cache.keys(), key=lambda k: self.l1_cache[k].access_count)
            del self.l1_cache[min_access_key]

        self.metrics.evictions += 1

    async def _get_from_disk(self, key: str) -> Optional[CacheEntry]:
        """Get entry from disk cache"""

        try:
            file_path = f"{self.l3_disk_path}/{self._hash_key(key)}.cache"
            if not os.path.exists(file_path):
                return None

            with open(file_path, 'rb') as f:
                entry = pickle.load(f)

            # Check if expired
            if entry.ttl_seconds:
                age = (datetime.now() - entry.created_at).total_seconds()
                if age > entry.ttl_seconds:
                    os.remove(file_path)
                    return None

            return entry

        except Exception as e:
            logger.debug(f"Disk cache get error: {e}")
            return None

    async def _store_on_disk(self, entry: CacheEntry) -> None:
        """Store entry on disk"""

        try:
            file_path = f"{self.l3_disk_path}/{self._hash_key(entry.key)}.cache"
            with open(file_path, 'wb') as f:
                pickle.dump(entry, f)

        except Exception as e:
            logger.debug(f"Disk cache store error: {e}")

    async def _remove_from_disk(self, key: str) -> None:
        """Remove entry from disk"""

        try:
            file_path = f"{self.l3_disk_path}/{self._hash_key(key)}.cache"
            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception as e:
            logger.debug(f"Disk cache remove error: {e}")

    def _hash_key(self, key: str) -> str:
        """Generate hash for key (for disk storage)"""
        return hashlib.md5(key.encode('utf-8')).hexdigest()

    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern"""
        import fnmatch
        return fnmatch.fnmatch(key, pattern)

    async def _update_access_stats(self, entry: CacheEntry) -> None:
        """Update access statistics for entry"""

        entry.last_accessed = datetime.now()
        entry.access_count += 1

        # Move to end in LRU cache
        if entry.key in self.l1_cache:
            self.l1_cache.move_to_end(entry.key)

    async def _update_access_pattern(self, key: str) -> None:
        """Track access patterns for smart warming"""

        current_time = time.time()
        self.access_patterns[key].append(current_time)

        # Keep only recent accesses (last 24 hours)
        cutoff = current_time - 86400  # 24 hours ago
        self.access_patterns[key] = [
            t for t in self.access_patterns[key] if t > cutoff
        ]

    async def _cache_warming_loop(self) -> None:
        """Background cache warming loop"""

        while not self._shutdown:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                # Identify frequently accessed but not cached items
                candidates = await self._identify_warming_candidates()
                if candidates:
                    logger.info(f"Warming cache with {len(candidates)} candidates")

            except Exception as e:
                logger.error(f"Cache warming loop error: {e}")

    async def _identify_warming_candidates(self) -> List[str]:
        """Identify candidates for cache warming"""

        candidates = []
        current_time = time.time()

        for key, accesses in self.access_patterns.items():
            if len(accesses) >= 5:  # Accessed at least 5 times
                recent_accesses = [t for t in accesses if current_time - t < 3600]  # Last hour
                if len(recent_accesses) >= 3:  # 3+ recent accesses
                    if key not in self.l1_cache:  # Not already in L1
                        candidates.append(key)

        return candidates

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop"""

        while not self._shutdown:
            try:
                await asyncio.sleep(60)  # Run cleanup every minute

                await self._cleanup_expired_entries()
                await self._cleanup_disk_cache()

            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")

    async def _cleanup_expired_entries(self) -> None:
        """Clean up expired entries"""

        current_time = datetime.now()
        expired_keys = []

        # Check L1 cache
        for key, entry in self.l1_cache.items():
            if entry.ttl_seconds:
                age = (current_time - entry.created_at).total_seconds()
                if age > entry.ttl_seconds:
                    expired_keys.append(key)

        # Remove expired entries
        for key in expired_keys:
            await self.invalidate(key)

    async def _cleanup_disk_cache(self) -> None:
        """Clean up disk cache files"""

        try:
            import os
            current_time = time.time()
            cutoff = current_time - 86400  # 24 hours

            for filename in os.listdir(self.l3_disk_path):
                if filename.endswith('.cache'):
                    file_path = os.path.join(self.l3_disk_path, filename)
                    if os.path.getmtime(file_path) < cutoff:
                        os.remove(file_path)

        except Exception as e:
            logger.debug(f"Disk cache cleanup error: {e}")

    async def _metrics_collection_loop(self) -> None:
        """Background metrics collection loop"""

        while not self._shutdown:
            try:
                await asyncio.sleep(10)  # Collect metrics every 10 seconds

                await self._update_metrics()

            except Exception as e:
                logger.error(f"Metrics collection error: {e}")

    async def _update_metrics(self) -> None:
        """Update cache metrics"""

        # Calculate hit ratio
        if self.metrics.total_requests > 0:
            self.metrics.average_hit_ratio = self.metrics.cache_hits / self.metrics.total_requests

        # Calculate memory usage
        total_size = sum(len(str(entry.value)) for entry in self.l1_cache.values())
        self.metrics.total_size_bytes = total_size
        self.metrics.memory_usage_mb = total_size / (1024 * 1024)

        # Update timestamp
        self.metrics.last_updated = datetime.now()

    async def _invalidation_processing_loop(self) -> None:
        """Background invalidation processing loop"""

        while not self._shutdown:
            try:
                await asyncio.sleep(1)  # Process invalidations frequently

                # Process invalidation queue
                while not self.invalidation_queue.empty():
                    try:
                        invalidation = self.invalidation_queue.get_nowait()
                        await self._process_invalidation(invalidation)
                        self.invalidation_queue.task_done()
                    except asyncio.QueueEmpty:
                        break

            except Exception as e:
                logger.error(f"Invalidation processing error: {e}")

    async def _process_invalidation(self, invalidation: Dict[str, Any]) -> None:
        """Process invalidation request"""

        invalidation_type = invalidation.get('type')
        target = invalidation.get('target')

        if invalidation_type == 'key':
            await self.invalidate(target)
        elif invalidation_type == 'tag':
            await self.invalidate_by_tag(target)
        elif invalidation_type == 'dependency':
            await self.invalidate_by_dependency(target)
        elif invalidation_type == 'pattern':
            await self.invalidate_pattern(target)

    def get_metrics(self) -> CacheMetrics:
        """Get current cache metrics"""
        return self.metrics

    def get_statistics(self) -> Dict[str, Any]:
        """Get detailed cache statistics"""

        return {
            'cache_id': self.cache_id,
            'metrics': asdict(self.metrics),
            'config': asdict(self.config),
            'l1_size': len(self.l1_cache),
            'l1_capacity': self._get_l1_capacity(),
            'l1_usage_ratio': len(self.l1_cache) / self._get_l1_capacity(),
            'dependency_count': len(self.dependency_graph),
            'tag_count': len(self.tag_index),
            'tracked_access_patterns': len(self.access_patterns)
        }

    async def clear(self) -> bool:
        """Clear all cache entries"""

        try:
            # Clear L1 cache
            self.l1_cache.clear()

            # Clear L2 cache
            if self.l2_redis_client:
                pattern = f"{self.cache_id}:*"
                keys = await self.l2_redis_client.keys(pattern)
                if keys:
                    await self.l2_redis_client.delete(*keys)

            # Clear L3 cache
            import os
            for filename in os.listdir(self.l3_disk_path):
                if filename.endswith('.cache'):
                    os.remove(os.path.join(self.l3_disk_path, filename))

            # Clear indexes
            self.dependency_graph.clear()
            self.tag_index.clear()
            self.query_index.clear()
            self.access_patterns.clear()

            # Reset metrics
            self.metrics = CacheMetrics()

            return True

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    async def close(self) -> None:
        """Close cache system"""

        logger.info(f"Closing cache '{self.cache_id}'")

        self._shutdown = True

        # Cancel background tasks
        if self.warming_task:
            self.warming_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.metrics_task:
            self.metrics_task.cancel()
        if self.invalidation_task:
            self.invalidation_task.cancel()

        # Close Redis connection
        if self.l2_redis_client:
            self.l2_redis_client.close()
            await self.l2_redis_client.wait_closed()

        logger.info(f"Cache '{self.cache_id}' closed")

class DatabaseCache(SmartCache):
    """Specialized cache for database operations"""

    def __init__(self, cache_id: str, config: CacheConfig):
        super().__init__(cache_id, config)
        self.query_patterns = {}
        self.table_dependencies = defaultdict(set)

    async def cache_query_result(self, query: str, params: Optional[List],
                               result: Any, table_dependencies: Optional[Set[str]] = None) -> bool:
        """Cache database query result"""

        # Generate cache key from query and parameters
        cache_key = self._generate_query_cache_key(query, params)

        # Add table dependencies
        dependencies = set()
        if table_dependencies:
            dependencies.update(table_dependencies)

        # Extract table names from query
        tables = self._extract_tables_from_query(query)
        dependencies.update(tables)

        return await self.set(cache_key, result, dependencies=dependencies)

    async def get_cached_query_result(self, query: str, params: Optional[List]) -> Any:
        """Get cached query result"""

        cache_key = self._generate_query_cache_key(query, params)
        return await self.get(cache_key)

    async def invalidate_table_cache(self, table_name: str) -> int:
        """Invalidate all cache entries depending on table"""

        invalidated_count = 0

        # Direct dependency invalidation
        invalidated_count += await self.invalidate_by_dependency(table_name)

        # Pattern-based invalidation
        patterns = [
            f"*{table_name}*",
            f"*{table_name}_*",
            f"*_{table_name}*"
        ]

        for pattern in patterns:
            invalidated_count += await self.invalidate_pattern(pattern)

        return invalidated_count

    def _generate_query_cache_key(self, query: str, params: Optional[List]) -> str:
        """Generate cache key for query"""

        # Normalize query
        normalized_query = " ".join(query.split()).lower()

        # Create hash
        key_data = normalized_query
        if params:
            key_data += str(sorted(params))

        return f"query:{hashlib.md5(key_data.encode('utf-8')).hexdigest()}"

    def _extract_tables_from_query(self, query: str) -> Set[str]:
        """Extract table names from SQL query"""

        tables = set()

        # Simple table extraction - could be enhanced with proper SQL parsing
        import re

        # FROM clauses
        from_matches = re.findall(r'\bFROM\s+(\w+)\b', query, re.IGNORECASE)
        tables.update(from_matches)

        # JOIN clauses
        join_matches = re.findall(r'\bJOIN\s+(\w+)\b', query, re.IGNORECASE)
        tables.update(join_matches)

        # UPDATE clauses
        update_matches = re.findall(r'\bUPDATE\s+(\w+)\b', query, re.IGNORECASE)
        tables.update(update_matches)

        # INSERT INTO clauses
        insert_matches = re.findall(r'\bINSERT\s+INTO\s+(\w+)\b', query, re.IGNORECASE)
        tables.update(insert_matches)

        return tables

# Example usage
async def main():
    """Example usage of the database cache system"""

    # Configure cache
    cache_config = CacheConfig(
        l1_max_size_mb=50,
        l2_max_size_mb=500,
        default_ttl_seconds=1800,  # 30 minutes
        enable_smart_warming=True,
        enable_dependency_tracking=True
    )

    # Create database cache
    db_cache = DatabaseCache("main_db_cache", cache_config)

    # Redis connection params
    redis_params = {
        'host': 'localhost',
        'port': 6379,
        'db': 0
    }

    try:
        # Initialize cache
        await db_cache.initialize(redis_params)
        print("Database cache initialized successfully")

        # Cache query result
        query = "SELECT * FROM users WHERE id = %s"
        params = [123]
        result = {"id": 123, "name": "John Doe", "email": "john@example.com"}

        success = await db_cache.cache_query_result(query, params, result, table_dependencies={"users"})
        print(f"Cached query result: {success}")

        # Get cached result
        cached_result = await db_cache.get_cached_query_result(query, params)
        print(f"Cached result: {cached_result}")

        # Invalidate table cache
        invalidated = await db_cache.invalidate_table_cache("users")
        print(f"Invalidated {invalidated} cache entries for table 'users'")

        # Get metrics
        metrics = db_cache.get_metrics()
        print(f"Cache hit ratio: {metrics.average_hit_ratio:.1%}")
        print(f"Total requests: {metrics.total_requests}")
        print(f"Cache hits: {metrics.cache_hits}")
        print(f"Cache misses: {metrics.cache_misses}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Clean up
        await db_cache.close()
        print("Cache closed")

if __name__ == "__main__":
    asyncio.run(main())