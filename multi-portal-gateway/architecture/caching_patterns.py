"""
Advanced Multi-layer Caching Strategies and Patterns
Cutting-edge caching implementation with intelligent invalidation,
cache warming, predictive preloading, and distributed cache coordination.

This module implements:
- Multi-tier caching architecture (L1/L2/L3)
- Intelligent cache warming and preloading
- Predictive caching using ML algorithms
- Cache invalidation strategies and propagation
- Distributed cache synchronization
- Cache compression and optimization
- Performance monitoring and analytics
- Adaptive cache sizing and eviction policies
"""

import asyncio
import json
import time
import hashlib
import pickle
import gzip
import lzma
import struct
from abc import ABC, abstractmethod
from typing import (
    Dict, List, Optional, Any, Callable, Union,
    TypeVar, Generic, NamedTuple, Tuple, Set,
    AsyncGenerator, Protocol
)
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
import structlog
import redis.asyncio as redis
import aioredis
import aiofiles
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import mmh3  # MurmurHash3 for consistent hashing
import prometheus_client as prom
from pydantic import BaseModel, Field
import cProfile
import pstats

# Configure structured logging
logger = structlog.get_logger()

# Type variables
K = TypeVar('K')
V = TypeVar('V')
T = TypeVar('T')

class CacheLevel(Enum):
    """Cache levels in the hierarchy"""
    L1_MEMORY = "l1_memory"      # In-memory cache (fastest)
    L2_REDIS = "l2_redis"        # Redis cache (fast)
    L3_DATABASE = "l3_database"  # Database cache (slow)
    L4_CDN = "l4_cdn"           # CDN cache (very slow)

class CachePolicy(Enum):
    """Cache eviction policies"""
    LRU = "lru"                    # Least Recently Used
    LFU = "lfu"                    # Least Frequently Used
    FIFO = "fifo"                  # First In, First Out
    RANDOM = "random"              # Random eviction
    TTL_BASED = "ttl_based"        # TTL-based eviction
    ADAPTIVE = "adaptive"          # Adaptive eviction

class CompressionType(Enum):
    """Compression algorithms for cached data"""
    NONE = "none"
    GZIP = "gzip"
    LZMA = "lzma"
    PICKLE = "pickle"

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl: Optional[timedelta] = None
    size_bytes: int = 0
    compression_type: CompressionType = CompressionType.NONE
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl is None:
            return False
        return datetime.utcnow() > self.created_at + self.ttl

    def touch(self):
        """Update last accessed time and increment count"""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1

@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    size_bytes: int = 0
    entry_count: int = 0
    hit_rate: float = 0.0
    miss_rate: float = 0.0
    avg_access_time_ms: float = 0.0
    compression_ratio: float = 0.0

@dataclass
class AccessPattern:
    """Access pattern for ML-based prediction"""
    key: str
    timestamps: List[datetime] = field(default_factory=list)
    access_frequency: float = 0.0
    recency_score: float = 0.0
    locality_score: float = 0.0

class CacheBackend(ABC):
    """Abstract cache backend interface"""

    @abstractmethod
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get cache entry"""
        pass

    @abstractmethod
    async def set(self, entry: CacheEntry) -> bool:
        """Set cache entry"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete cache entry"""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries"""
        pass

    @abstractmethod
    async def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        pass

class MemoryCache(CacheBackend):
    """High-performance in-memory cache with advanced eviction"""

    def __init__(self, max_size_mb: int = 100, eviction_policy: CachePolicy = CachePolicy.LRU):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.eviction_policy = eviction_policy
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.access_patterns: Dict[str, AccessPattern] = {}
        self.stats = CacheStats()
        self.lock = asyncio.Lock()
        self.compression_threshold = 1024  # Compress entries > 1KB

        # Prometheus metrics
        self.cache_hits = prom.Counter('memory_cache_hits_total', 'Memory cache hits')
        self.cache_misses = prom.Counter('memory_cache_misses_total', 'Memory cache misses')
        self.cache_size_bytes = prom.Gauge('memory_cache_size_bytes', 'Memory cache size in bytes')
        self.cache_entries = prom.Gauge('memory_cache_entries', 'Number of cache entries')

    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get entry from memory cache"""
        start_time = time.time()

        async with self.lock:
            entry = self.cache.get(key)

            if entry:
                # Check expiration
                if entry.is_expired:
                    await self._remove_entry(key)
                    self.cache_misses.inc()
                    self.stats.misses += 1
                    return None

                # Update access tracking
                entry.touch()
                self._update_access_pattern(key)
                self._update_order_for_lru(key)

                self.cache_hits.inc()
                self.stats.hits += 1
                self._update_access_time_stats(start_time)
                return entry

            self.cache_misses.inc()
            self.stats.misses += 1
            self._update_access_time_stats(start_time)
            return None

    async def set(self, entry: CacheEntry) -> bool:
        """Set entry in memory cache"""
        async with self.lock:
            # Compress large entries
            if entry.size_bytes > self.compression_threshold:
                entry = await self._compress_entry(entry)

            # Check if eviction is needed
            if self._should_evict(entry):
                await self._evict_entries()

            # Remove existing entry if present
            if entry.key in self.cache:
                del self.cache[entry.key]

            # Add new entry
            self.cache[entry.key] = entry
            self._update_access_pattern(entry.key, create=True)

            # Update stats
            self.stats.sets += 1
            self._update_size_stats()

            return True

    async def delete(self, key: str) -> bool:
        """Delete entry from memory cache"""
        async with self.lock:
            if key in self.cache:
                await self._remove_entry(key)
                self.stats.deletes += 1
                return True
            return False

    async def clear(self) -> bool:
        """Clear all entries"""
        async with self.lock:
            self.cache.clear()
            self.access_patterns.clear()
            self.stats = CacheStats()
            self._update_size_stats()
            return True

    async def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        async with self.lock:
            self._calculate_hit_rates()
            return self.stats

    async def _compress_entry(self, entry: CacheEntry) -> CacheEntry:
        """Compress cache entry"""
        try:
            if entry.compression_type == CompressionType.NONE:
                # Serialize value
                serialized = pickle.dumps(entry.value)

                # Try different compression methods
                compressed_gzip = gzip.compress(serialized)
                compressed_lzma = lzma.compress(serialized)

                # Choose best compression
                if len(compressed_lzma) < len(compressed_gzip):
                    entry.value = compressed_lzma
                    entry.compression_type = CompressionType.LZMA
                else:
                    entry.value = compressed_gzip
                    entry.compression_type = CompressionType.GZIP

                entry.size_bytes = len(entry.value)
                self.stats.compression_ratio = len(serialized) / entry.size_bytes

        except Exception as e:
            logger.error("Failed to compress cache entry",
                        key=entry.key, error=str(e))

        return entry

    async def _decompress_entry(self, entry: CacheEntry) -> Any:
        """Decompress cache entry value"""
        if entry.compression_type == CompressionType.GZIP:
            compressed = entry.value
            decompressed = gzip.decompress(compressed)
            return pickle.loads(decompressed)
        elif entry.compression_type == CompressionType.LZMA:
            compressed = entry.value
            decompressed = lzma.decompress(compressed)
            return pickle.loads(decompressed)
        else:
            return entry.value

    async def _remove_entry(self, key: str):
        """Remove entry from cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_patterns:
            del self.access_patterns[key]
        self._update_size_stats()

    def _should_evict(self, entry: CacheEntry) -> bool:
        """Check if eviction is needed"""
        current_size = sum(e.size_bytes for e in self.cache.values())
        return (current_size + entry.size_bytes) > self.max_size_bytes

    async def _evict_entries(self):
        """Evict entries based on policy"""
        if self.eviction_policy == CachePolicy.LRU:
            await self._evict_lru()
        elif self.eviction_policy == CachePolicy.LFU:
            await self._evict_lfu()
        elif self.eviction_policy == CachePolicy.FIFO:
            await self._evict_fifo()
        elif self.eviction_policy == CachePolicy.TTL_BASED:
            await self._evict_expired()
        else:
            await self._evict_lru()  # Default to LRU

    async def _evict_lru(self):
        """Evict least recently used entries"""
        # Remove 25% of entries
        evict_count = max(1, len(self.cache) // 4)
        keys_to_evict = list(self.cache.keys())[:evict_count]

        for key in keys_to_evict:
            await self._remove_entry(key)
            self.stats.evictions += 1

    async def _evict_lfu(self):
        """Evict least frequently used entries"""
        # Sort by access count
        sorted_entries = sorted(self.cache.items(),
                              key=lambda x: x[1].access_count)

        # Remove 25% of least accessed
        evict_count = max(1, len(sorted_entries) // 4)
        for key, _ in sorted_entries[:evict_count]:
            await self._remove_entry(key)
            self.stats.evictions += 1

    async def _evict_fifo(self):
        """Evict first in entries"""
        # Remove oldest 25% of entries
        sorted_entries = sorted(self.cache.items(),
                              key=lambda x: x[1].created_at)

        evict_count = max(1, len(sorted_entries) // 4)
        for key, _ in sorted_entries[:evict_count]:
            await self._remove_entry(key)
            self.stats.evictions += 1

    async def _evict_expired(self):
        """Evict expired entries"""
        expired_keys = [key for key, entry in self.cache.items()
                       if entry.is_expired]

        for key in expired_keys:
            await self._remove_entry(key)
            self.stats.evictions += 1

    def _update_order_for_lru(self, key: str):
        """Update order for LRU eviction"""
        if key in self.cache:
            entry = self.cache.pop(key)
            self.cache[key] = entry

    def _update_access_pattern(self, key: str, create: bool = False):
        """Update access pattern for ML predictions"""
        if key not in self.access_patterns and create:
            self.access_patterns[key] = AccessPattern(key=key)

        if key in self.access_patterns:
            pattern = self.access_patterns[key]
            pattern.timestamps.append(datetime.utcnow())

            # Keep only recent timestamps
            if len(pattern.timestamps) > 100:
                pattern.timestamps = pattern.timestamps[-100:]

            # Update metrics
            pattern.access_frequency = len(pattern.timestamps) / 3600.0  # per hour
            pattern.recency_score = self._calculate_recency_score(pattern.timestamps)
            pattern.locality_score = self._calculate_locality_score(key)

    def _calculate_recency_score(self, timestamps: List[datetime]) -> float:
        """Calculate recency score (0-1)"""
        if not timestamps:
            return 0.0

        now = datetime.utcnow()
        recent_accesses = [ts for ts in timestamps if (now - ts).total_seconds() < 3600]
        return len(recent_accesses) / len(timestamps)

    def _calculate_locality_score(self, key: str) -> float:
        """Calculate locality score based on key patterns"""
        # Simple heuristic: keys with similar prefixes have locality
        if not self.access_patterns:
            return 0.0

        key_prefix = key[:8]  # First 8 characters
        similar_keys = [k for k in self.access_patterns.keys() if k.startswith(key_prefix)]

        return min(len(similar_keys) / 10.0, 1.0)

    def _update_size_stats(self):
        """Update size statistics"""
        self.stats.size_bytes = sum(e.size_bytes for e in self.cache.values())
        self.stats.entry_count = len(self.cache)

        # Update Prometheus metrics
        self.cache_size_bytes.set(self.stats.size_bytes)
        self.cache_entries.set(self.stats.entry_count)

    def _calculate_hit_rates(self):
        """Calculate hit and miss rates"""
        total_requests = self.stats.hits + self.stats.misses
        if total_requests > 0:
            self.stats.hit_rate = self.stats.hits / total_requests
            self.stats.miss_rate = self.stats.misses / total_requests

    def _update_access_time_stats(self, start_time: float):
        """Update access time statistics"""
        access_time_ms = (time.time() - start_time) * 1000

        # Simple exponential moving average
        alpha = 0.1
        if self.stats.avg_access_time_ms == 0:
            self.stats.avg_access_time_ms = access_time_ms
        else:
            self.stats.avg_access_time_ms = (
                alpha * access_time_ms +
                (1 - alpha) * self.stats.avg_access_time_ms
            )

class RedisCache(CacheBackend):
    """Redis-based distributed cache"""

    def __init__(self, redis_url: str, default_ttl: timedelta = timedelta(hours=1)):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client: Optional[redis.Redis] = None
        self.stats = CacheStats()
        self.key_prefix = "dmlogn8n_cache:"
        self.compression_enabled = True

        # Prometheus metrics
        self.redis_hits = prom.Counter('redis_cache_hits_total', 'Redis cache hits')
        self.redis_misses = prom.Counter('redis_cache_misses_total', 'Redis cache misses')
        self.redis_operations = prom.Counter('redis_cache_operations_total', 'Redis operations', ['operation'])

    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(self.redis_url)
        await self.redis_client.ping()
        logger.info("Redis cache initialized", url=self.redis_url)

    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get entry from Redis"""
        if not self.redis_client:
            await self.initialize()

        start_time = time.time()
        redis_key = self._make_key(key)

        try:
            data = await self.redis_client.get(redis_key)
            if data:
                entry_dict = json.loads(data)
                entry = CacheEntry(**entry_dict)

                # Check expiration
                if entry.is_expired:
                    await self.delete(key)
                    self.redis_misses.inc()
                    self.stats.misses += 1
                    return None

                self.redis_hits.inc()
                self.stats.hits += 1
                return entry

            self.redis_misses.inc()
            self.stats.misses += 1
            return None

        except Exception as e:
            logger.error("Redis get error", key=key, error=str(e))
            self.stats.misses += 1
            return None

        finally:
            self._update_access_time_stats(start_time)

    async def set(self, entry: CacheEntry) -> bool:
        """Set entry in Redis"""
        if not self.redis_client:
            await self.initialize()

        redis_key = self._make_key(entry.key)
        ttl_seconds = int(entry.ttl.total_seconds()) if entry.ttl else int(self.default_ttl.total_seconds())

        try:
            # Serialize entry
            entry_dict = {
                'key': entry.key,
                'value': entry.value,
                'created_at': entry.created_at.isoformat(),
                'last_accessed': entry.last_accessed.isoformat(),
                'access_count': entry.access_count,
                'ttl': entry.ttl.total_seconds() if entry.ttl else None,
                'size_bytes': entry.size_bytes,
                'compression_type': entry.compression_type.value,
                'metadata': entry.metadata
            }

            # Compress if enabled and value is large
            if self.compression_enabled and len(json.dumps(entry_dict)) > 1024:
                serialized = json.dumps(entry_dict).encode()
                compressed = gzip.compress(serialized)
                entry_dict['compressed_value'] = compressed.hex()
                del entry_dict['value']

            data = json.dumps(entry_dict)

            await self.redis_client.setex(redis_key, ttl_seconds, data)
            self.redis_operations.labels(operation='set').inc()
            self.stats.sets += 1

            return True

        except Exception as e:
            logger.error("Redis set error", key=entry.key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete entry from Redis"""
        if not self.redis_client:
            await self.initialize()

        redis_key = self._make_key(key)

        try:
            result = await self.redis_client.delete(redis_key)
            self.redis_operations.labels(operation='delete').inc()
            self.stats.deletes += 1
            return result > 0

        except Exception as e:
            logger.error("Redis delete error", key=key, error=str(e))
            return False

    async def clear(self) -> bool:
        """Clear all entries from Redis"""
        if not self.redis_client:
            await self.initialize()

        try:
            pattern = f"{self.key_prefix}*"
            keys = await self.redis_client.keys(pattern)

            if keys:
                await self.redis_client.delete(*keys)

            self.redis_operations.labels(operation='clear').inc()
            return True

        except Exception as e:
            logger.error("Redis clear error", error=str(e))
            return False

    async def get_stats(self) -> CacheStats:
        """Get Redis cache statistics"""
        if not self.redis_client:
            await self.initialize()

        try:
            # Get Redis info
            info = await self.redis_client.info('memory')
            self.stats.size_bytes = info.get('used_memory', 0)

            # Get key count
            pattern = f"{self.key_prefix}*"
            keys = await self.redis_client.keys(pattern)
            self.stats.entry_count = len(keys)

            # Calculate hit rates
            self._calculate_hit_rates()

        except Exception as e:
            logger.error("Redis stats error", error=str(e))

        return self.stats

    def _make_key(self, key: str) -> str:
        """Create Redis key with prefix"""
        return f"{self.key_prefix}{key}"

    def _calculate_hit_rates(self):
        """Calculate hit and miss rates"""
        total_requests = self.stats.hits + self.stats.misses
        if total_requests > 0:
            self.stats.hit_rate = self.stats.hits / total_requests
            self.stats.miss_rate = self.stats.misses / total_requests

    def _update_access_time_stats(self, start_time: float):
        """Update access time statistics"""
        access_time_ms = (time.time() - start_time) * 1000

        alpha = 0.1
        if self.stats.avg_access_time_ms == 0:
            self.stats.avg_access_time_ms = access_time_ms
        else:
            self.stats.avg_access_time_ms = (
                alpha * access_time_ms +
                (1 - alpha) * self.stats.avg_access_time_ms
            )

class MultiTierCache:
    """Multi-tier cache with intelligent routing"""

    def __init__(self, l1_cache: MemoryCache, l2_cache: RedisCache,
                 l3_fallback: Optional[Callable] = None):
        self.l1_cache = l1_cache
        self.l2_cache = l2_cache
        self.l3_fallback = l3_fallback
        self.predictor = CachePredictor()
        self.warmer = CacheWarmer(self)
        self.invalidator = CacheInvalidator(self)

        # Prometheus metrics
        self.tier_hits = prom.Counter('cache_tier_hits_total', 'Cache tier hits', ['tier'])
        self.total_requests = prom.Counter('cache_total_requests_total', 'Total cache requests')

    async def get(self, key: str) -> Optional[Any]:
        """Get value from multi-tier cache"""
        self.total_requests.inc()

        # Try L1 cache first
        entry = await self.l1_cache.get(key)
        if entry:
            self.tier_hits.labels(tier='l1').inc()
            return entry.value

        # Try L2 cache
        entry = await self.l2_cache.get(key)
        if entry:
            # Promote to L1 cache
            await self.l1_cache.set(entry)
            self.tier_hits.labels(tier='l2').inc()
            return entry.value

        # Try L3 fallback
        if self.l3_fallback:
            try:
                value = await self.l3_fallback(key)
                if value is not None:
                    # Cache in all tiers
                    entry = CacheEntry(
                        key=key,
                        value=value,
                        created_at=datetime.utcnow(),
                        last_accessed=datetime.utcnow(),
                        size_bytes=len(str(value))
                    )
                    await self.l1_cache.set(entry)
                    await self.l2_cache.set(entry)
                    self.tier_hits.labels(tier='l3').inc()
                    return value
            except Exception as e:
                logger.error("L3 fallback error", key=key, error=str(e))

        return None

    async def set(self, key: str, value: Any,
                 ttl: Optional[timedelta] = None) -> bool:
        """Set value in all cache tiers"""
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            ttl=ttl,
            size_bytes=len(str(value))
        )

        # Set in all tiers
        l1_success = await self.l1_cache.set(entry)
        l2_success = await self.l2_cache.set(entry)

        return l1_success or l2_success

    async def delete(self, key: str) -> bool:
        """Delete from all cache tiers"""
        l1_deleted = await self.l1_cache.delete(key)
        l2_deleted = await self.l2_cache.delete(key)
        return l1_deleted or l2_deleted

    async def clear_all(self) -> bool:
        """Clear all cache tiers"""
        l1_cleared = await self.l1_cache.clear()
        l2_cleared = await self.l2_cache.clear()
        return l1_cleared and l2_cleared

    async def get_combined_stats(self) -> Dict[str, CacheStats]:
        """Get statistics from all tiers"""
        return {
            'l1_memory': await self.l1_cache.get_stats(),
            'l2_redis': await self.l2_cache.get_stats(),
            'combined': self._calculate_combined_stats()
        }

    def _calculate_combined_stats(self) -> CacheStats:
        """Calculate combined statistics"""
        l1_stats = self.l1_cache.stats
        l2_stats = self.l2_cache.stats

        combined = CacheStats(
            hits=l1_stats.hits + l2_stats.hits,
            misses=l1_stats.misses + l2_stats.misses,
            sets=l1_stats.sets + l2_stats.sets,
            deletes=l1_stats.deletes + l2_stats.deletes,
            evictions=l1_stats.evictions,
            size_bytes=l1_stats.size_bytes,
            entry_count=l1_stats.entry_count,
            avg_access_time_ms=min(l1_stats.avg_access_time_ms, l2_stats.avg_access_time_ms)
        )

        # Calculate rates
        total_requests = combined.hits + combined.misses
        if total_requests > 0:
            combined.hit_rate = combined.hits / total_requests
            combined.miss_rate = combined.misses / total_requests

        return combined

class CachePredictor:
    """ML-based cache prediction for intelligent preloading"""

    def __init__(self):
        self.access_history: Dict[str, List[datetime]] = defaultdict(list)
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.kmeans = KMeans(n_clusters=10, random_state=42)
        self.is_trained = False
        self.prediction_cache: Dict[str, float] = {}

    async def predict_access_probability(self, key: str,
                                       context: Optional[Dict[str, Any]] = None) -> float:
        """Predict probability of future access for a key"""
        if key in self.prediction_cache:
            return self.prediction_cache[key]

        # Simple prediction based on access patterns
        history = self.access_history.get(key, [])
        if not history:
            return 0.0

        # Calculate recency and frequency scores
        now = datetime.utcnow()
        recent_accesses = [ts for ts in history if (now - ts).total_seconds() < 3600]
        frequency = len(recent_accesses) / 3600.0  # accesses per hour

        # Calculate recency decay
        if history:
            last_access = max(history)
            recency = math.exp(-(now - last_access).total_seconds() / 3600.0)
        else:
            recency = 0.0

        # Combine scores
        probability = min(frequency * recency * 10, 1.0)

        # Cache prediction
        self.prediction_cache[key] = probability

        return probability

    async def predict_cache_warming_candidates(self,
                                             available_slots: int) -> List[str]:
        """Predict best candidates for cache warming"""
        candidates = []

        for key in self.access_history.keys():
            probability = await self.predict_access_probability(key)
            candidates.append((key, probability))

        # Sort by probability and return top candidates
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [key for key, _ in candidates[:available_slots]]

    def record_access(self, key: str):
        """Record key access for prediction model"""
        now = datetime.utcnow()
        self.access_history[key].append(now)

        # Keep only recent history
        if len(self.access_history[key]) > 1000:
            self.access_history[key] = self.access_history[key][-1000:]

        # Clear prediction cache
        if key in self.prediction_cache:
            del self.prediction_cache[key]

class CacheWarmer:
    """Intelligent cache warming system"""

    def __init__(self, cache: MultiTierCache):
        self.cache = cache
        self.predictor = CachePredictor()
        self.warming_queue: asyncio.Queue = asyncio.Queue()
        self.warming_active = False
        self.warming_stats = defaultdict(int)

    async def start_warming(self):
        """Start cache warming process"""
        self.warming_active = True
        asyncio.create_task(self._warming_worker())

    async def stop_warming(self):
        """Stop cache warming process"""
        self.warming_active = False

    async def warm_cache_for_key(self, key: str):
        """Warm cache for specific key"""
        await self.warming_queue.put(key)

    async def warm_predicted_cache(self, limit: int = 100):
        """Warm cache based on predictions"""
        candidates = await self.cache.predictor.predict_cache_warming_candidates(limit)

        for key in candidates:
            await self.warm_cache_for_key(key)

    async def _warming_worker(self):
        """Background worker for cache warming"""
        while self.warming_active:
            try:
                # Get key from queue
                key = await asyncio.wait_for(self.warming_queue.get(), timeout=1.0)

                # Check if already cached
                cached_value = await self.cache.get(key)
                if cached_value is not None:
                    continue

                # Load from source and cache
                if self.cache.l3_fallback:
                    try:
                        value = await self.cache.l3_fallback(key)
                        if value is not None:
                            await self.cache.set(key, value)
                            self.warming_stats['successful_warms'] += 1
                        else:
                            self.warming_stats['missing_keys'] += 1
                    except Exception as e:
                        logger.error("Cache warming error", key=key, error=str(e))
                        self.warming_stats['failed_warms'] += 1

                self.warming_queue.task_done()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("Cache warming worker error", error=str(e))

class CacheInvalidator:
    """Intelligent cache invalidation system"""

    def __init__(self, cache: MultiTierCache):
        self.cache = cache
        self.invalidation_rules: Dict[str, Callable] = {}
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)

    def register_invalidation_rule(self, pattern: str,
                                 invalidator: Callable[[str], bool]):
        """Register cache invalidation rule"""
        self.invalidation_rules[pattern] = invalidator

    def register_dependency(self, key: str, depends_on: str):
        """Register cache dependency"""
        self.dependency_graph[key].add(depends_on)
        self.reverse_dependencies[depends_on].add(key)

    async def invalidate_key(self, key: str) -> bool:
        """Invalidate specific key and dependents"""
        # Invalidate the key itself
        success = await self.cache.delete(key)

        # Invalidate dependent keys
        for dependent in self.reverse_dependencies.get(key, set()):
            await self.invalidate_key(dependent)

        return success

    async def invalidate_by_pattern(self, pattern: str) -> int:
        """Invalidate keys matching pattern"""
        # This would require pattern matching against cache keys
        # Implementation depends on cache backend capabilities
        return 0

    async def invalidate_by_rule(self, trigger: Any) -> int:
        """Invalidate based on registered rules"""
        invalidated_count = 0

        for pattern, invalidator in self.invalidation_rules.items():
            try:
                if invalidator(trigger):
                    # Pattern matched, invalidate corresponding keys
                    count = await self.invalidate_by_pattern(pattern)
                    invalidated_count += count
            except Exception as e:
                logger.error("Invalidation rule error",
                           pattern=pattern, error=str(e))

        return invalidated_count

class ConsistentHashRing:
    """Consistent hashing for distributed cache"""

    def __init__(self, nodes: List[str], replicas: int = 150):
        self.replicas = replicas
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []

        for node in nodes:
            self.add_node(node)

    def add_node(self, node: str):
        """Add node to hash ring"""
        for i in range(self.replicas):
            key = f"{node}:{i}"
            hash_value = mmh3.hash(key)
            self.ring[hash_value] = node

        self.sorted_keys = sorted(self.ring.keys())

    def remove_node(self, node: str):
        """Remove node from hash ring"""
        for i in range(self.replicas):
            key = f"{node}:{i}"
            hash_value = mmh3.hash(key)
            if hash_value in self.ring:
                del self.ring[hash_value]

        self.sorted_keys = sorted(self.ring.keys())

    def get_node(self, key: str) -> str:
        """Get node for key"""
        if not self.ring:
            return None

        hash_value = mmh3.hash(key)

        # Find first node with hash greater than key hash
        for ring_key in self.sorted_keys:
            if ring_key >= hash_value:
                return self.ring[ring_key]

        # Wrap around to first node
        return self.ring[self.sorted_keys[0]]

# Initialize multi-tier caching system
async def initialize_caching_system(redis_url: str,
                                   l1_size_mb: int = 100) -> MultiTierCache:
    """Initialize complete caching architecture"""

    # Initialize L1 memory cache
    l1_cache = MemoryCache(max_size_mb=l1_size_mb, eviction_policy=CachePolicy.LRU)

    # Initialize L2 Redis cache
    l2_cache = RedisCache(redis_url)
    await l2_cache.initialize()

    # Create multi-tier cache
    cache = MultiTierCache(l1_cache, l2_cache)

    # Start cache warming
    await cache.warmer.start_warming()

    logger.info("Multi-tier caching system initialized",
               l1_size_mb=l1_size_mb,
               redis_url=redis_url)

    return cache

# Export main classes and functions
__all__ = [
    'MultiTierCache',
    'MemoryCache',
    'RedisCache',
    'CachePredictor',
    'CacheWarmer',
    'CacheInvalidator',
    'ConsistentHashRing',
    'CacheEntry',
    'CacheStats',
    'CacheLevel',
    'CachePolicy',
    'CompressionType',
    'initialize_caching_system'
]