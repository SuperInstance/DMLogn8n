#!/usr/bin/env python3
"""
Advanced Multi-Layer Cache Manager for DMLogn8n Platform
Intelligent caching strategies with L1/L2/L3 layers, cache warming, and optimization
"""

import asyncio
import json
import logging
import pickle
import time
import threading
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import hashlib
import zlib
import weakref

# Cache backend libraries
try:
    import redis
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import pymemcache
    MEMCACHED_AVAILABLE = True
except ImportError:
    MEMCACHED_AVAILABLE = False

logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    """Cache hierarchy levels"""
    L1_MEMORY = "l1_memory"      # In-memory cache (fastest)
    L2_LOCAL_DISK = "l2_local_disk"  # Local disk cache
    L3_DISTRIBUTED = "l3_distributed"  # Redis/Memcached
    L4_DATABASE = "l4_database"  # Database as cache

class CachePolicy(Enum):
    """Cache eviction policies"""
    LRU = "lru"                # Least Recently Used
    LFU = "lfu"                # Least Frequently Used
    TTL = "ttl"                # Time To Live
    FIFO = "fifo"              # First In, First Out
    ADAPTIVE = "adaptive"      # Adaptive based on access patterns

class CacheStrategy(Enum):
    """Caching strategies"""
    WRITE_THROUGH = "write_through"    # Write to cache and backend
    WRITE_BEHIND = "write_behind"      # Write to cache, async to backend
    WRITE_AROUND = "write_around"      # Write directly to backend
    REFRESH_AHEAD = "refresh_ahead"    # Pre-populate cache
    CACHE_ASIDE = "cache_aside"        # Application manages cache

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    ttl_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    compressed: bool = False
    version: int = 1

    @property
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl_seconds is None:
            return False
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """Get age of entry in seconds"""
        return (datetime.now() - self.created_at).total_seconds()

@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    size_bytes: int = 0
    entry_count: int = 0
    hit_rate: float = 0.0
    miss_rate: float = 0.0

    @property
    def total_requests(self) -> int:
        return self.hits + self.misses

    def update_rates(self):
        """Update hit and miss rates"""
        if self.total_requests > 0:
            self.hit_rate = self.hits / self.total_requests
            self.miss_rate = self.misses / self.total_requests

class CacheBackend(ABC):
    """Abstract cache backend interface"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value with optional TTL"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value by key"""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries"""
        pass

    @abstractmethod
    async def size(self) -> int:
        """Get cache size in bytes"""
        pass

    @abstractmethod
    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        pass

class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend with LRU eviction"""

    def __init__(self, max_size_mb: int = 100, max_entries: int = 10000, policy: CachePolicy = CachePolicy.LRU):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_entries = max_entries
        self.policy = policy

        self.cache = OrderedDict()
        self.stats = CacheStats()
        self.lock = threading.RLock()
        self.total_size = 0

    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        with self.lock:
            if key not in self.cache:
                self.stats.misses += 1
                self.stats.update_rates()
                return None

            entry = self.cache[key]

            # Check TTL
            if entry.is_expired:
                del self.cache[key]
                self.total_size -= entry.size_bytes
                self.stats.misses += 1
                self.stats.update_rates()
                return None

            # Update access info
            entry.last_accessed = datetime.now()
            entry.access_count += 1

            # Move to end for LRU
            if self.policy == CachePolicy.LRU:
                self.cache.move_to_end(key)

            self.stats.hits += 1
            self.stats.update_rates()
            return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache"""
        with self.lock:
            # Calculate size
            try:
                size_bytes = len(pickle.dumps(value))
            except:
                size_bytes = len(str(value).encode())

            # Check if entry already exists
            if key in self.cache:
                old_entry = self.cache[key]
                self.total_size -= old_entry.size_bytes
            else:
                # Check capacity
                while (len(self.cache) >= self.max_entries or
                       self.total_size + size_bytes > self.max_size_bytes):
                    if not self._evict():
                        break

            # Create new entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                ttl_seconds=ttl,
                size_bytes=size_bytes
            )

            self.cache[key] = entry
            self.total_size += size_bytes
            self.stats.sets += 1

            return True

    async def delete(self, key: str) -> bool:
        """Delete entry from memory cache"""
        with self.lock:
            if key not in self.cache:
                return False

            entry = self.cache.pop(key)
            self.total_size -= entry.size_bytes
            self.stats.deletes += 1
            return True

    async def clear(self) -> bool:
        """Clear memory cache"""
        with self.lock:
            self.cache.clear()
            self.total_size = 0
            self.stats = CacheStats()
            return True

    async def size(self) -> int:
        """Get cache size in bytes"""
        return self.total_size

    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        import fnmatch
        with self.lock:
            return [key for key in self.cache.keys() if fnmatch.fnmatch(key, pattern)]

    def _evict(self) -> bool:
        """Evict entries based on policy"""
        if not self.cache:
            return False

        if self.policy == CachePolicy.LRU:
            # Remove least recently used
            key, entry = self.cache.popitem(last=False)
        elif self.policy == CachePolicy.LFU:
            # Remove least frequently used
            key = min(self.cache.keys(), key=lambda k: self.cache[k].access_count)
            entry = self.cache.pop(key)
        elif self.policy == CachePolicy.FIFO:
            # Remove first inserted
            key, entry = self.cache.popitem(last=False)
        else:
            # Default to LRU
            key, entry = self.cache.popitem(last=False)

        self.total_size -= entry.size_bytes
        self.stats.evictions += 1
        return True

class RedisCacheBackend(CacheBackend):
    """Redis cache backend"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0,
                 password: Optional[str] = None, prefix: str = "dmlog_cache:"):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.prefix = prefix

        self.client = None
        self.async_client = None
        self.stats = CacheStats()

    async def _ensure_connection(self):
        """Ensure Redis connection is established"""
        if self.client is None:
            if REDIS_AVAILABLE:
                self.client = aioredis.from_url(
                    f"redis://{self.host}:{self.port}/{self.db}",
                    password=self.password,
                    decode_responses=False
                )
            else:
                raise RuntimeError("Redis library not available")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        await self._ensure_connection()
        try:
            redis_key = f"{self.prefix}{key}"
            data = await self.client.get(redis_key)

            if data is None:
                self.stats.misses += 1
                self.stats.update_rates()
                return None

            # Deserialize
            try:
                value = pickle.loads(data)
                self.stats.hits += 1
                self.stats.update_rates()
                return value
            except:
                # Fallback to string
                value = data.decode('utf-8') if isinstance(data, bytes) else data
                self.stats.hits += 1
                self.stats.update_rates()
                return value

        except Exception as e:
            logger.error(f"Redis get error: {e}")
            self.stats.misses += 1
            self.stats.update_rates()
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis"""
        await self._ensure_connection()
        try:
            redis_key = f"{self.prefix}{key}"

            # Serialize
            try:
                data = pickle.dumps(value)
            except:
                data = str(value).encode('utf-8')

            # Set with optional TTL
            if ttl:
                result = await self.client.setex(redis_key, ttl, data)
            else:
                result = await self.client.set(redis_key, data)

            self.stats.sets += 1
            return result

        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        await self._ensure_connection()
        try:
            redis_key = f"{self.prefix}{key}"
            result = await self.client.delete(redis_key)
            self.stats.deletes += 1
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def clear(self) -> bool:
        """Clear all keys with prefix"""
        await self._ensure_connection()
        try:
            pattern = f"{self.prefix}*"
            keys = await self.client.keys(pattern)
            if keys:
                await self.client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False

    async def size(self) -> int:
        """Get approximate memory usage"""
        await self._ensure_connection()
        try:
            info = await self.client.info('memory')
            return info.get('used_memory', 0)
        except Exception as e:
            logger.error(f"Redis size error: {e}")
            return 0

    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        await self._ensure_connection()
        try:
            redis_pattern = f"{self.prefix}{pattern}"
            keys = await self.client.keys(redis_pattern)
            # Remove prefix
            return [key.decode('utf-8').replace(self.prefix, '', 1)
                   for key in keys if isinstance(key, bytes)]
        except Exception as e:
            logger.error(f"Redis keys error: {e}")
            return []

class DiskCacheBackend(CacheBackend):
    """Local disk cache backend"""

    def __init__(self, cache_dir: str = "/tmp/dmlog_cache", max_size_mb: int = 1000):
        self.cache_dir = cache_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.stats = CacheStats()

        import os
        os.makedirs(cache_dir, exist_ok=True)

    def _get_file_path(self, key: str) -> str:
        """Get file path for key"""
        # Use hash to avoid filesystem issues
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return f"{self.cache_dir}/{key_hash}.cache"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache"""
        import os

        file_path = self._get_file_path(key)
        if not os.path.exists(file_path):
            self.stats.misses += 1
            self.stats.update_rates()
            return None

        try:
            with open(file_path, 'rb') as f:
                data = f.read()

            # Check if file is too old (simple TTL check)
            file_time = os.path.getmtime(file_path)
            if time.time() - file_time > 3600:  # 1 hour default TTL
                os.remove(file_path)
                self.stats.misses += 1
                self.stats.update_rates()
                return None

            # Deserialize
            try:
                value = pickle.loads(data)
                self.stats.hits += 1
                self.stats.update_rates()
                return value
            except:
                # Fallback to string
                value = data.decode('utf-8')
                self.stats.hits += 1
                self.stats.update_rates()
                return value

        except Exception as e:
            logger.error(f"Disk cache get error: {e}")
            self.stats.misses += 1
            self.stats.update_rates()
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in disk cache"""
        try:
            # Serialize
            try:
                data = pickle.dumps(value)
            except:
                data = str(value).encode('utf-8')

            file_path = self._get_file_path(key)

            # Check size limit
            import os
            if self._get_total_size() + len(data) > self.max_size_bytes:
                self._cleanup_old_files()

            with open(file_path, 'wb') as f:
                f.write(data)

            self.stats.sets += 1
            return True

        except Exception as e:
            logger.error(f"Disk cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from disk cache"""
        import os

        file_path = self._get_file_path(key)
        if os.path.exists(file_path):
            os.remove(file_path)
            self.stats.deletes += 1
            return True
        return False

    async def clear(self) -> bool:
        """Clear disk cache"""
        import os
        import shutil

        try:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
            self.stats = CacheStats()
            return True
        except Exception as e:
            logger.error(f"Disk cache clear error: {e}")
            return False

    async def size(self) -> int:
        """Get total cache size in bytes"""
        return self._get_total_size()

    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        # This is inefficient for disk cache - would need an index
        import os
        import fnmatch

        keys = []
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.cache'):
                # Would need to maintain a key-to-file mapping
                pass
        return keys

    def _get_total_size(self) -> int:
        """Get total size of cache directory"""
        import os

        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(self.cache_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
        except:
            pass
        return total_size

    def _cleanup_old_files(self):
        """Clean up old files to make space"""
        import os
        import time

        files = []
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.cache'):
                filepath = os.path.join(self.cache_dir, filename)
                files.append((filepath, os.path.getmtime(filepath)))

        # Sort by modification time (oldest first)
        files.sort(key=lambda x: x[1])

        # Delete old files until under limit
        for filepath, _ in files:
            if self._get_total_size() <= self.max_size_bytes * 0.8:  # Leave 20% buffer
                break
            try:
                os.remove(filepath)
                self.stats.evictions += 1
            except:
                pass

class CacheManager:
    """Multi-layer cache manager with intelligent routing and optimization"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.cache_layers = {}
        self.cache_stats = defaultdict(CacheStats)
        self.warming_queue = asyncio.Queue()
        self.background_tasks = set()

        # Initialize cache layers
        self._initialize_cache_layers()

        # Cache warming and optimization
        self.auto_warming = self.config.get('auto_warming', True)
        self.optimization_interval = self.config.get('optimization_interval', 300)  # 5 minutes

        # Compression settings
        self.compression_enabled = self.config.get('compression_enabled', True)
        self.compression_threshold = self.config.get('compression_threshold', 1024)  # bytes

        # Background tasks
        self.background_running = False

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'layers': {
                'l1_memory': {
                    'enabled': True,
                    'max_size_mb': 100,
                    'max_entries': 10000,
                    'policy': 'lru'
                },
                'l2_disk': {
                    'enabled': True,
                    'cache_dir': '/tmp/dmlog_cache',
                    'max_size_mb': 1000
                },
                'l3_redis': {
                    'enabled': False,
                    'host': 'localhost',
                    'port': 6379,
                    'db': 0
                }
            },
            'strategy': 'cache_aside',
            'auto_warming': True,
            'optimization_interval': 300,
            'compression_enabled': True,
            'compression_threshold': 1024,
            'warming_patterns': [
                'user:*',
                'config:*',
                'session:*'
            ]
        }

    def _initialize_cache_layers(self):
        """Initialize cache backends"""
        layers_config = self.config.get('layers', {})

        # L1 Memory Cache
        if layers_config.get('l1_memory', {}).get('enabled', True):
            l1_config = layers_config['l1_memory']
            self.cache_layers[CacheLevel.L1_MEMORY] = MemoryCacheBackend(
                max_size_mb=l1_config.get('max_size_mb', 100),
                max_entries=l1_config.get('max_entries', 10000),
                policy=CachePolicy(l1_config.get('policy', 'lru'))
            )

        # L2 Disk Cache
        if layers_config.get('l2_disk', {}).get('enabled', True):
            l2_config = layers_config['l2_disk']
            self.cache_layers[CacheLevel.L2_LOCAL_DISK] = DiskCacheBackend(
                cache_dir=l2_config.get('cache_dir', '/tmp/dmlog_cache'),
                max_size_mb=l2_config.get('max_size_mb', 1000)
            )

        # L3 Redis Cache
        if layers_config.get('l3_redis', {}).get('enabled', False):
            l3_config = layers_config['l3_redis']
            self.cache_layers[CacheLevel.L3_DISTRIBUTED] = RedisCacheBackend(
                host=l3_config.get('host', 'localhost'),
                port=l3_config.get('port', 6379),
                db=l3_config.get('db', 0)
            )

        logger.info(f"Initialized {len(self.cache_layers)} cache layers")

    async def get(self, key: str, level: Optional[CacheLevel] = None) -> Optional[Any]:
        """Get value from cache with layer fallback"""
        start_time = time.time()

        # Determine search order
        if level:
            search_levels = [level]
        else:
            search_levels = [
                CacheLevel.L1_MEMORY,
                CacheLevel.L2_LOCAL_DISK,
                CacheLevel.L3_DISTRIBUTED
            ]

        # Try each layer
        for cache_level in search_levels:
            if cache_level not in self.cache_layers:
                continue

            backend = self.cache_layers[cache_level]
            try:
                value = await backend.get(key)
                if value is not None:
                    # Cache hit - promote to higher layers if needed
                    await self._promote_to_higher_layers(key, value, cache_level)

                    self.cache_stats[cache_level].hits += 1
                    self.cache_stats[cache_level].update_rates()

                    logger.debug(f"Cache hit: {key} from {cache_level.value}")
                    return value

            except Exception as e:
                logger.error(f"Error getting from {cache_level.value}: {e}")

        # Cache miss in all layers
        for cache_level in search_levels:
            if cache_level in self.cache_layers:
                self.cache_stats[cache_level].misses += 1
                self.cache_stats[cache_level].update_rates()

        logger.debug(f"Cache miss: {key}")
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None,
                 levels: Optional[List[CacheLevel]] = None) -> bool:
        """Set value in specified cache layers"""
        start_time = time.time()

        # Determine which layers to use
        if levels is None:
            levels = list(self.cache_layers.keys())

        # Apply compression if enabled and value is large enough
        if self.compression_enabled and self._should_compress(value):
            value = self._compress_value(value)
            key = f"{key}:compressed"

        success = True
        for cache_level in levels:
            if cache_level not in self.cache_layers:
                continue

            backend = self.cache_layers[cache_level]
            try:
                result = await backend.set(key, value, ttl)
                if not result:
                    success = False
                    logger.warning(f"Failed to set in {cache_level.value}: {key}")
                else:
                    self.cache_stats[cache_level].sets += 1

            except Exception as e:
                logger.error(f"Error setting in {cache_level.value}: {e}")
                success = False

        logger.debug(f"Cache set: {key} in {len(levels)} layers")
        return success

    async def delete(self, key: str) -> bool:
        """Delete key from all cache layers"""
        success = True
        for cache_level, backend in self.cache_layers.items():
            try:
                result = await backend.delete(key)
                if result:
                    self.cache_stats[cache_level].deletes += 1
            except Exception as e:
                logger.error(f"Error deleting from {cache_level.value}: {e}")
                success = False

        logger.debug(f"Cache delete: {key}")
        return success

    async def clear(self, level: Optional[CacheLevel] = None) -> bool:
        """Clear cache layer(s)"""
        if level:
            if level in self.cache_layers:
                backend = self.cache_layers[level]
                return await backend.clear()
            return False
        else:
            # Clear all layers
            success = True
            for cache_level, backend in self.cache_layers.items():
                try:
                    result = await backend.clear()
                    if not result:
                        success = False
                except Exception as e:
                    logger.error(f"Error clearing {cache_level.value}: {e}")
                    success = False
            return success

    async def _promote_to_higher_layers(self, key: str, value: Any, source_level: CacheLevel):
        """Promote cached value to higher cache layers"""
        # Define promotion hierarchy
        hierarchy = [
            CacheLevel.L1_MEMORY,
            CacheLevel.L2_LOCAL_DISK,
            CacheLevel.L3_DISTRIBUTED
        ]

        source_index = hierarchy.index(source_level) if source_level in hierarchy else -1

        # Promote to higher priority layers
        for i, target_level in enumerate(hierarchy):
            if i <= source_index:  # Skip same and lower levels
                continue

            if target_level in self.cache_layers:
                try:
                    backend = self.cache_layers[target_level]
                    await backend.set(key, value)
                    logger.debug(f"Promoted {key} to {target_level.value}")
                except Exception as e:
                    logger.error(f"Error promoting to {target_level.value}: {e}")

    def _should_compress(self, value: Any) -> bool:
        """Check if value should be compressed"""
        try:
            size = len(pickle.dumps(value))
            return size > self.compression_threshold
        except:
            return len(str(value).encode()) > self.compression_threshold

    def _compress_value(self, value: Any) -> bytes:
        """Compress value"""
        try:
            serialized = pickle.dumps(value)
            return zlib.compress(serialized)
        except:
            return zlib.compress(str(value).encode())

    def _decompress_value(self, compressed_data: bytes) -> Any:
        """Decompress value"""
        try:
            decompressed = zlib.decompress(compressed_data)
            return pickle.loads(decompressed)
        except:
            return zlib.decompress(compressed_data).decode('utf-8')

    async def warm_cache(self, patterns: List[str], data_loader: Callable[[str], Any]):
        """Warm cache with data matching patterns"""
        logger.info(f"Starting cache warming for {len(patterns)} patterns")

        for pattern in patterns:
            try:
                # Get keys matching pattern from lowest layer
                if CacheLevel.L3_DISTRIBUTED in self.cache_layers:
                    backend = self.cache_layers[CacheLevel.L3_DISTRIBUTED]
                    keys = await backend.keys(pattern)
                else:
                    keys = []  # Would need to implement pattern matching for other layers

                # Load and cache data
                for key in keys:
                    value = await data_loader(key)
                    if value is not None:
                        await self.set(key, value)

                logger.info(f"Warmed cache for pattern: {pattern}")

            except Exception as e:
                logger.error(f"Error warming cache for pattern {pattern}: {e}")

    def start_background_tasks(self):
        """Start background optimization tasks"""
        if self.background_running:
            return

        self.background_running = True

        # Cache optimization task
        optimization_task = asyncio.create_task(self._optimization_loop())
        self.background_tasks.add(optimization_task)

        # Cache warming task
        if self.auto_warming:
            warming_task = asyncio.create_task(self._warming_loop())
            self.background_tasks.add(warming_task)

        logger.info("Background cache tasks started")

    def stop_background_tasks(self):
        """Stop background tasks"""
        self.background_running = False

        for task in self.background_tasks:
            task.cancel()

        if self.background_tasks:
            asyncio.gather(*self.background_tasks, return_exceptions=True)

        self.background_tasks.clear()
        logger.info("Background cache tasks stopped")

    async def _optimization_loop(self):
        """Background cache optimization loop"""
        while self.background_running:
            try:
                await self._optimize_caches()
                await asyncio.sleep(self.optimization_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(60)

    async def _warming_loop(self):
        """Background cache warming loop"""
        while self.background_running:
            try:
                patterns = self.config.get('warming_patterns', [])
                if patterns:
                    # Would need a data_loader implementation
                    pass

                await asyncio.sleep(3600)  # Run every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in warming loop: {e}")
                await asyncio.sleep(300)

    async def _optimize_caches(self):
        """Optimize cache performance"""
        logger.debug("Running cache optimization")

        # Analyze hit rates and adjust policies
        for cache_level, backend in self.cache_layers.items():
            stats = self.cache_stats[cache_level]

            if stats.total_requests > 100:  # Minimum requests for analysis
                hit_rate = stats.hit_rate

                if hit_rate < 0.5:  # Low hit rate
                    logger.warning(f"Low hit rate for {cache_level.value}: {hit_rate:.2%}")

                    # Suggest optimizations
                    if cache_level == CacheLevel.L1_MEMORY:
                        logger.info("Consider increasing L1 cache size or reviewing access patterns")
                    elif cache_level == CacheLevel.L2_LOCAL_DISK:
                        logger.info("Consider increasing L2 cache size or improving disk I/O")

        # Clean up expired entries
        await self._cleanup_expired_entries()

    async def _cleanup_expired_entries(self):
        """Clean up expired cache entries"""
        for cache_level, backend in self.cache_layers.items():
            try:
                # Different cleanup strategies based on backend type
                if isinstance(backend, MemoryCacheBackend):
                    # Memory cache handles TTL automatically
                    pass
                elif isinstance(backend, DiskCacheBackend):
                    # Disk cache would need cleanup implementation
                    pass

            except Exception as e:
                logger.error(f"Error cleaning up {cache_level.value}: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = {
            'layers': {},
            'overall': {
                'total_hits': sum(s.hits for s in self.cache_stats.values()),
                'total_misses': sum(s.misses for s in self.cache_stats.values()),
                'total_sets': sum(s.sets for s in self.cache_stats.values()),
                'total_deletes': sum(s.deletes for s in self.cache_stats.values()),
                'total_evictions': sum(s.evictions for s in self.cache_stats.values())
            }
        }

        # Calculate overall hit rate
        total_requests = (stats['overall']['total_hits'] + stats['overall']['total_misses'])
        if total_requests > 0:
            stats['overall']['hit_rate'] = stats['overall']['total_hits'] / total_requests
        else:
            stats['overall']['hit_rate'] = 0.0

        # Per-layer statistics
        for cache_level, backend in self.cache_layers.items():
            layer_stats = self.cache_stats[cache_level]
            stats['layers'][cache_level.value] = {
                'hits': layer_stats.hits,
                'misses': layer_stats.misses,
                'hit_rate': layer_stats.hit_rate,
                'sets': layer_stats.sets,
                'deletes': layer_stats.deletes,
                'evictions': layer_stats.evictions
            }

            # Get size information
            try:
                size = asyncio.run(backend.size())
                stats['layers'][cache_level.value]['size_bytes'] = size
            except:
                stats['layers'][cache_level.value]['size_bytes'] = 0

        return stats

    async def export_cache_data(self, output_file: str):
        """Export cache data for analysis or migration"""
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'config': self.config,
                'stats': self.get_cache_stats(),
                'layers': {}
            }

            # Export data from each layer
            for cache_level, backend in self.cache_layers.items():
                if isinstance(backend, MemoryCacheBackend):
                    # Export memory cache data
                    layer_data = {}
                    for key, entry in backend.cache.items():
                        layer_data[key] = {
                            'created_at': entry.created_at.isoformat(),
                            'last_accessed': entry.last_accessed.isoformat(),
                            'access_count': entry.access_count,
                            'size_bytes': entry.size_bytes,
                            'ttl_seconds': entry.ttl_seconds
                        }
                    export_data['layers'][cache_level.value] = layer_data

            # Save to file
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Cache data exported to {output_file}")

        except Exception as e:
            logger.error(f"Error exporting cache data: {e}")

# Cache decorator
def cached(cache_manager: CacheManager, ttl: Optional[int] = None,
          levels: Optional[List[CacheLevel]] = None, key_func: Optional[Callable] = None):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__module__}.{func.__qualname__}:{hashlib.md5(str(args + tuple(sorted(kwargs.items()))).encode()).hexdigest()}"

            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache_manager.set(cache_key, result, ttl, levels)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, run in executor
            return asyncio.run(async_wrapper(*args, **kwargs))

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize cache manager
        cache_manager = CacheManager({
            'layers': {
                'l1_memory': {
                    'enabled': True,
                    'max_size_mb': 10,
                    'max_entries': 100
                },
                'l2_disk': {
                    'enabled': True,
                    'max_size_mb': 100
                }
            },
            'auto_warming': True
        })

        # Start background tasks
        cache_manager.start_background_tasks()

        try:
            # Example caching
            await cache_manager.set("user:123", {"name": "John", "email": "john@example.com"}, ttl=3600)

            # Get from cache
            user_data = await cache_manager.get("user:123")
            print(f"User data: {user_data}")

            # Get cache statistics
            stats = cache_manager.get_cache_stats()
            print(f"Cache stats: {json.dumps(stats, indent=2)}")

            # Example with decorator
            @cached(cache_manager, ttl=300)
            async def expensive_function(x: int, y: int) -> int:
                """Simulate expensive computation"""
                await asyncio.sleep(1)  # Simulate work
                return x * y

            # First call - should compute
            start = time.time()
            result1 = await expensive_function(5, 10)
            time1 = time.time() - start

            # Second call - should use cache
            start = time.time()
            result2 = await expensive_function(5, 10)
            time2 = time.time() - start

            print(f"First call: {result1} ({time1:.3f}s)")
            print(f"Second call: {result2} ({time2:.3f}s)")

            await asyncio.sleep(5)

        finally:
            # Cleanup
            cache_manager.stop_background_tasks()
            await cache_manager.clear()

    # Run example
    asyncio.run(main())