#!/usr/bin/env python3
"""
Cache Accelerator - Advanced Multi-Layer Caching System
Provides instant responses through intelligent caching strategies
"""

import asyncio
import time
import threading
import hashlib
import json
import pickle
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict, defaultdict
from concurrent.futures import ThreadPoolExecutor
import weakref
import logging
from functools import wraps
from abc import ABC, abstractmethod

@dataclass
class CacheConfig:
    """Configuration for cache layers"""
    # Memory cache settings
    memory_max_size: int = 10000
    memory_ttl: float = 300.0  # 5 minutes

    # L1 cache (ultra-fast, small)
    l1_max_size: int = 100
    l1_ttl: float = 60.0  # 1 minute

    # L2 cache (fast, medium)
    l2_max_size: int = 1000
    l2_ttl: float = 300.0  # 5 minutes

    # L3 cache (medium, large)
    l3_max_size: int = 10000
    l3_ttl: float = 1800.0  # 30 minutes

    # Cache warming
    enable_prewarming: bool = True
    prewarm_interval: float = 60.0
    prewarm_threshold: int = 5  # Minimum access count for prewarming

    # Cache invalidation
    enable_smart_invalidation: bool = True
    invalidation_check_interval: float = 10.0

    # Compression
    enable_compression: bool = True
    compression_threshold: int = 1024  # Compress items larger than 1KB

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_time: float
    last_accessed: float
    access_count: int = 0
    ttl: float = 300.0
    size_bytes: int = 0
    compressed: bool = False
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    @property
    def is_expired(self) -> bool:
        return time.time() - self.created_time > self.ttl

    @property
    def age(self) -> float:
        return time.time() - self.created_time

    def touch(self):
        """Update last accessed time and increment access count"""
        self.last_accessed = time.time()
        self.access_count += 1

class CacheLayer(ABC):
    """Abstract base class for cache layers"""

    def __init__(self, name: str, config: CacheConfig):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"CacheLayer-{name}")

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in cache"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass

    @abstractmethod
    async def clear(self):
        """Clear all cache entries"""
        pass

    @abstractmethod
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        pass

class MemoryCacheLayer(CacheLayer):
    """In-memory cache layer with LRU eviction"""

    def __init__(self, name: str, config: CacheConfig, max_size: int):
        super().__init__(name, config)
        self.max_size = max_size
        self._cache: OrderedDict = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }

    async def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]

                # Check if expired
                if entry.is_expired:
                    del self._cache[key]
                    self._stats['misses'] += 1
                    return None

                # Move to end (LRU)
                self._cache.move_to_end(key)
                entry.touch()
                self._stats['hits'] += 1
                return entry.value

            self._stats['misses'] += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        with self._lock:
            try:
                # Calculate size
                size_bytes = len(pickle.dumps(value))

                # Create entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_time=time.time(),
                    last_accessed=time.time(),
                    ttl=ttl or self.config.memory_ttl,
                    size_bytes=size_bytes
                )

                # Check if we need to evict
                while len(self._cache) >= self.max_size and key not in self._cache:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    self._stats['evictions'] += 1

                # Set entry
                self._cache[key] = entry
                self._stats['sets'] += 1
                return True

            except Exception as e:
                self.logger.error(f"Cache set error: {e}")
                return False

    async def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats['deletes'] += 1
                return True
            return False

    async def clear(self):
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> Dict:
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0

            return {
                **self._stats,
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate_percent': hit_rate,
                'memory_usage_mb': sum(entry.size_bytes for entry in self._cache.values()) / (1024 * 1024)
            }

class DistributedCacheLayer(CacheLayer):
    """Distributed cache layer (Redis/Cluster)"""

    def __init__(self, name: str, config: CacheConfig):
        super().__init__(name, config)
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
        # In real implementation, would connect to Redis/Cluster
        self._cache = {}

    async def get(self, key: str) -> Optional[Any]:
        try:
            # Simulate distributed cache lookup
            value = self._cache.get(key)
            if value:
                self._stats['hits'] += 1
                return pickle.loads(value)
            else:
                self._stats['misses'] += 1
                return None
        except Exception as e:
            self.logger.error(f"Distributed cache get error: {e}")
            self._stats['errors'] += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        try:
            serialized = pickle.dumps(value)
            self._cache[key] = serialized
            self._stats['sets'] += 1
            return True
        except Exception as e:
            self.logger.error(f"Distributed cache set error: {e}")
            self._stats['errors'] += 1
            return False

    async def delete(self, key: str) -> bool:
        try:
            if key in self._cache:
                del self._cache[key]
                self._stats['deletes'] += 1
                return True
            return False
        except Exception as e:
            self.logger.error(f"Distributed cache delete error: {e}")
            self._stats['errors'] += 1
            return False

    async def clear(self):
        self._cache.clear()

    def get_stats(self) -> Dict:
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        return {
            **self._stats,
            'hit_rate_percent': hit_rate,
            'size': len(self._cache)
        }

class CacheAccelerator:
    """Multi-layer cache accelerator with intelligent strategies"""

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()

        # Initialize cache layers
        self.l1_cache = MemoryCacheLayer("L1", self.config, self.config.l1_max_size)
        self.l2_cache = MemoryCacheLayer("L2", self.config, self.config.l2_max_size)
        self.l3_cache = MemoryCacheLayer("L3", self.config, self.config.l3_max_size)
        self.distributed_cache = DistributedCacheLayer("DISTRIBUTED", self.config)

        # Cache statistics
        self.global_stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'background_updates': 0,
            'prewarmed_keys': 0
        }

        # Cache warming data
        self.access_patterns: Dict[str, List[float]] = defaultdict(list)
        self.hot_keys: Dict[str, int] = defaultdict(int)

        # Background tasks
        self._running = True
        self._background_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cache_bg")

        # Start background tasks
        self._start_background_tasks()

        # Setup logging
        self.logger = logging.getLogger("CacheAccelerator")

    def _start_background_tasks(self):
        """Start background cache management tasks"""
        if self.config.enable_prewarming:
            threading.Thread(
                target=self._prewarm_loop,
                name="CachePrewarming",
                daemon=True
            ).start()

        if self.config.enable_smart_invalidation:
            threading.Thread(
                target=self._invalidation_loop,
                name="CacheInvalidation",
                daemon=True
            ).start()

        # Statistics collection
        threading.Thread(
            target=self._stats_collection_loop,
            name="CacheStats",
            daemon=True
        ).start()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (layered approach)"""
        self.global_stats['total_requests'] += 1
        start_time = time.time()

        try:
            # L1 Cache (fastest)
            value = await self.l1_cache.get(key)
            if value is not None:
                self.global_stats['cache_hits'] += 1
                self._record_access(key)
                return value

            # L2 Cache
            value = await self.l2_cache.get(key)
            if value is not None:
                self.global_stats['cache_hits'] += 1
                self._record_access(key)
                # Promote to L1
                await self.l1_cache.set(key, value, self.config.l1_ttl)
                return value

            # L3 Cache
            value = await self.l3_cache.get(key)
            if value is not None:
                self.global_stats['cache_hits'] += 1
                self._record_access(key)
                # Promote to higher layers
                await self.l2_cache.set(key, value, self.config.l2_ttl)
                await self.l1_cache.set(key, value, self.config.l1_ttl)
                return value

            # Distributed Cache
            value = await self.distributed_cache.get(key)
            if value is not None:
                self.global_stats['cache_hits'] += 1
                self._record_access(key)
                # Promote to all layers
                await self.l3_cache.set(key, value, self.config.l3_ttl)
                await self.l2_cache.set(key, value, self.config.l2_ttl)
                await self.l1_cache.set(key, value, self.config.l1_ttl)
                return value

            self.global_stats['cache_misses'] += 1
            return None

        except Exception as e:
            self.logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[float] = None,
                 tags: Optional[List[str]] = None) -> bool:
        """Set value in cache (all layers)"""
        try:
            # Determine TTL based on layer
            l1_ttl = ttl or self.config.l1_ttl
            l2_ttl = ttl or self.config.l2_ttl
            l3_ttl = ttl or self.config.l3_ttl

            # Set in all layers
            tasks = [
                self.l1_cache.set(key, value, l1_ttl),
                self.l2_cache.set(key, value, l2_ttl),
                self.l3_cache.set(key, value, l3_ttl),
                self.distributed_cache.set(key, value, ttl)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)

            return success_count > 0

        except Exception as e:
            self.logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from all cache layers"""
        try:
            tasks = [
                self.l1_cache.delete(key),
                self.l2_cache.delete(key),
                self.l3_cache.delete(key),
                self.distributed_cache.delete(key)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)

            return success_count > 0

        except Exception as e:
            self.logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate cache entries by tag"""
        # In real implementation, would track tags and invalidate accordingly
        invalidated_count = 0
        # Implementation would scan caches for entries with matching tags
        return invalidated_count

    def cache_function(self, ttl: Optional[float] = None,
                      key_func: Optional[Callable] = None,
                      tags: Optional[List[str]] = None):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"

                # Try to get from cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result

                # Execute function
                result = await func(*args, **kwargs)

                # Cache result
                await self.set(cache_key, result, ttl, tags)

                return result

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"

                # Try to get from cache (synchronously for simplicity)
                try:
                    loop = asyncio.get_event_loop()
                    cached_result = loop.run_until_complete(self.get(cache_key))
                    if cached_result is not None:
                        return cached_result
                except:
                    pass

                # Execute function
                result = func(*args, **kwargs)

                # Cache result
                try:
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(self.set(cache_key, result, ttl, tags))
                except:
                    pass

                return result

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator

    def _record_access(self, key: str):
        """Record key access for pattern analysis"""
        current_time = time.time()
        self.access_patterns[key].append(current_time)

        # Keep only recent access times
        if len(self.access_patterns[key]) > 100:
            self.access_patterns[key] = self.access_patterns[key][-50:]

        self.hot_keys[key] += 1

    async def prewarm_cache(self, keys: List[str], data_loader: Callable):
        """Prewarm cache with frequently accessed data"""
        self.logger.info(f"Prewarming {len(keys)} cache keys")

        for key in keys:
            try:
                # Check if already cached
                if await self.get(key) is not None:
                    continue

                # Load data
                data = await data_loader(key)
                if data is not None:
                    await self.set(key, data)
                    self.global_stats['prewarmed_keys'] += 1

            except Exception as e:
                self.logger.error(f"Prewarming error for key {key}: {e}")

    def _prewarm_loop(self):
        """Background cache prewarming loop"""
        while self._running:
            try:
                # Identify hot keys for prewarming
                hot_keys = [key for key, count in self.hot_keys.items()
                          if count >= self.config.prewarm_threshold]

                if hot_keys:
                    self.logger.info(f"Found {len(hot_keys)} hot keys for prewarming")
                    # In real implementation, would call appropriate data loaders
                    # asyncio.run(self.prewarm_cache(hot_keys, data_loader))

                time.sleep(self.config.prewarm_interval)

            except Exception as e:
                self.logger.error(f"Prewarming loop error: {e}")

    def _invalidation_loop(self):
        """Background cache invalidation loop"""
        while self._running:
            try:
                # Check for expired entries and clean them up
                current_time = time.time()

                # Clean up old access patterns
                for key in list(self.access_patterns.keys()):
                    if self.access_patterns[key]:
                        last_access = max(self.access_patterns[key])
                        if current_time - last_access > 3600:  # 1 hour
                            del self.access_patterns[key]
                            self.hot_keys.pop(key, None)

                time.sleep(self.config.invalidation_check_interval)

            except Exception as e:
                self.logger.error(f"Invalidation loop error: {e}")

    def _stats_collection_loop(self):
        """Background statistics collection loop"""
        while self._running:
            try:
                # Collect statistics and log periodically
                stats = self.get_comprehensive_stats()

                # Log summary
                if stats['total_requests'] > 0:
                    hit_rate = (stats['cache_hits'] / stats['total_requests']) * 100
                    self.logger.info(f"Cache stats - Hit rate: {hit_rate:.1f}%, "
                                   f"Total requests: {stats['total_requests']}")

                time.sleep(60)  # Log every minute

            except Exception as e:
                self.logger.error(f"Stats collection error: {e}")

    def get_comprehensive_stats(self) -> Dict:
        """Get comprehensive cache statistics"""
        stats = self.global_stats.copy()

        # Add layer-specific stats
        stats['layers'] = {
            'l1': self.l1_cache.get_stats(),
            'l2': self.l2_cache.get_stats(),
            'l3': self.l3_cache.get_stats(),
            'distributed': self.distributed_cache.get_stats()
        }

        # Calculate global hit rate
        if stats['total_requests'] > 0:
            stats['global_hit_rate_percent'] = (stats['cache_hits'] / stats['total_requests']) * 100
        else:
            stats['global_hit_rate_percent'] = 0

        # Add hot keys info
        stats['hot_keys_count'] = len(self.hot_keys)
        stats['access_patterns_count'] = len(self.access_patterns)

        return stats

    async def clear_all(self):
        """Clear all cache layers"""
        await asyncio.gather(
            self.l1_cache.clear(),
            self.l2_cache.clear(),
            self.l3_cache.clear(),
            self.distributed_cache.clear()
        )

    def shutdown(self):
        """Shutdown cache accelerator"""
        self._running = False
        self._background_executor.shutdown(wait=True)

# Global cache accelerator instance
cache_accelerator = CacheAccelerator()

# Convenience decorators
def fast_cache(ttl: Optional[float] = None, tags: Optional[List[str]] = None):
    """Fast caching decorator with optimal settings"""
    return cache_accelerator.cache_function(ttl=ttl or 60.0, tags=tags)

def ultra_fast_cache(ttl: Optional[float] = None, tags: Optional[List[str]] = None):
    """Ultra-fast caching for critical paths"""
    return cache_accelerator.cache_function(ttl=ttl or 30.0, tags=tags)

# Pre-configured cache strategies
def setup_cache_strategies():
    """Setup cache strategies for DMLogn8n"""
    # User session cache - ultra fast
    # Workflow data cache - fast
    # Template cache - medium
    # Configuration cache - long-term
    pass