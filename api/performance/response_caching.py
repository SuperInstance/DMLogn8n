#!/usr/bin/env python3
"""
Intelligent Response Caching System
Multi-tier caching with intelligent invalidation and compression
"""

import asyncio
import time
import json
import hashlib
import logging
import pickle
import gzip
import lzma
import zlib
from typing import Dict, List, Any, Optional, Callable, Union, Tuple, Set
from dataclasses import dataclass, asdict
from collections import OrderedDict, defaultdict
from enum import Enum
import weakref
import aioredis
import orjson
from fastapi import Request, Response
from fastapi.routing import APIRoute
import mmh3  # MurmurHash3 for fast hashing
import xxhash

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    """Cache levels for multi-tier strategy"""
    MEMORY = "memory"
    REDIS = "redis"
    DISTRIBUTED = "distributed"

class CompressionType(Enum):
    """Compression algorithms"""
    NONE = "none"
    GZIP = "gzip"
    LZMA = "lzma"
    ZLIB = "zlib"

@dataclass
class CacheConfig:
    """Configuration for caching system"""
    # Memory cache settings
    memory_cache_size: int = 100 * 1024 * 1024  # 100MB
    memory_cache_ttl: int = 300  # 5 minutes
    memory_max_items: int = 10000

    # Redis cache settings
    redis_url: str = "redis://localhost:6379"
    redis_cache_ttl: int = 3600  # 1 hour
    redis_max_memory: str = "256mb"

    # Compression settings
    enable_compression: bool = True
    compression_threshold: int = 1024  # 1KB
    compression_type: CompressionType = CompressionType.GZIP
    compression_level: int = 6

    # Cache invalidation
    enable_tag_based_invalidation: bool = True
    enable_time_based_invalidation: bool = True
    enable_version_based_invalidation: bool = True

    # Performance settings
    enable_background_refresh: bool = True
    refresh_threshold: float = 0.8  # Refresh when 80% of TTL expired
    enable_write_through: bool = True
    enable_write_behind: bool = False

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    expires_at: float
    access_count: int = 0
    last_accessed: float = 0
    size_bytes: int = 0
    compression_type: CompressionType = CompressionType.NONE
    tags: Set[str] = None
    version: int = 1
    etag: str = None
    content_type: str = "application/json"
    response_headers: Dict[str, str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = set()
        if self.response_headers is None:
            self.response_headers = {}
        if self.last_accessed == 0:
            self.last_accessed = time.time()

class MemoryCache:
    """High-performance LRU memory cache with size-based eviction"""

    def __init__(self, max_size: int, max_items: int, ttl: int):
        self.max_size = max_size
        self.max_items = max_items
        self.ttl = ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_size = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get entry from cache"""
        entry = self.cache.get(key)
        if not entry:
            self.misses += 1
            return None

        # Check TTL
        if time.time() > entry.expires_at:
            self._remove_entry(key)
            self.misses += 1
            return None

        # Update access information
        entry.access_count += 1
        entry.last_accessed = time.time()

        # Move to end (LRU)
        self.cache.move_to_end(key)
        self.hits += 1

        return entry

    def put(self, key: str, entry: CacheEntry):
        """Put entry in cache"""
        # Remove existing entry if present
        if key in self.cache:
            self._remove_entry(key)

        # Check if we need to evict entries
        while (self.current_size + entry.size_bytes > self.max_size or
               len(self.cache) >= self.max_items):
            if not self._evict_lru():
                break

        # Add new entry
        self.cache[key] = entry
        self.current_size += entry.size_bytes

    def remove(self, key: str) -> bool:
        """Remove entry from cache"""
        return self._remove_entry(key)

    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.current_size = 0

    def _remove_entry(self, key: str) -> bool:
        """Remove entry and update size"""
        entry = self.cache.pop(key, None)
        if entry:
            self.current_size -= entry.size_bytes
            return True
        return False

    def _evict_lru(self) -> bool:
        """Evict least recently used entry"""
        if not self.cache:
            return False

        oldest_key = next(iter(self.cache))
        self._remove_entry(oldest_key)
        self.evictions += 1
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "evictions": self.evictions,
            "current_size": self.current_size,
            "max_size": self.max_size,
            "items": len(self.cache),
            "max_items": self.max_items
        }

class RedisCache:
    """Redis-based distributed cache"""

    def __init__(self, redis_url: str, ttl: int, max_memory: str):
        self.redis_url = redis_url
        self.ttl = ttl
        self.max_memory = max_memory
        self.redis = None
        self.hits = 0
        self.misses = 0

    async def initialize(self):
        """Initialize Redis connection"""
        self.redis = await aioredis.from_url(
            self.redis_url,
            decode_responses=False,
            max_connections=20
        )

        # Configure Redis memory policy
        try:
            await self.redis.config_set("maxmemory", self.max_memory)
            await self.redis.config_set("maxmemory-policy", "allkeys-lru")
        except Exception as e:
            logger.error(f"Failed to configure Redis memory policy: {e}")

    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get entry from Redis"""
        if not self.redis:
            await self.initialize()

        try:
            data = await self.redis.get(f"cache:{key}")
            if data:
                entry = pickle.loads(data)

                # Check TTL
                if time.time() > entry.expires_at:
                    await self.remove(key)
                    self.misses += 1
                    return None

                self.hits += 1
                return entry
        except Exception as e:
            logger.error(f"Redis get error: {e}")

        self.misses += 1
        return None

    async def put(self, key: str, entry: CacheEntry):
        """Put entry in Redis"""
        if not self.redis:
            await self.initialize()

        try:
            data = pickle.dumps(entry)
            await self.redis.setex(f"cache:{key}", self.ttl, data)
        except Exception as e:
            logger.error(f"Redis put error: {e}")

    async def remove(self, key: str):
        """Remove entry from Redis"""
        if not self.redis:
            await self.initialize()

        try:
            await self.redis.delete(f"cache:{key}")
        except Exception as e:
            logger.error(f"Redis remove error: {e}")

    async def clear_by_pattern(self, pattern: str):
        """Clear entries by pattern"""
        if not self.redis:
            await self.initialize()

        try:
            keys = await self.redis.keys(f"cache:{pattern}")
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Redis clear pattern error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }

class CacheCompression:
    """Intelligent compression for cache entries"""

    @staticmethod
    def compress(data: bytes, compression_type: CompressionType, level: int = 6) -> Tuple[bytes, CompressionType]:
        """Compress data with specified algorithm"""
        if len(data) < 1024:  # Don't compress small data
            return data, CompressionType.NONE

        try:
            if compression_type == CompressionType.GZIP:
                return gzip.compress(data, level), CompressionType.GZIP
            elif compression_type == CompressionType.LZMA:
                return lzma.compress(data, preset=level), CompressionType.LZMA
            elif compression_type == CompressionType.ZLIB:
                return zlib.compress(data, level), CompressionType.ZLIB
        except Exception as e:
            logger.error(f"Compression error: {e}")

        return data, CompressionType.NONE

    @staticmethod
    def decompress(data: bytes, compression_type: CompressionType) -> bytes:
        """Decompress data"""
        try:
            if compression_type == CompressionType.GZIP:
                return gzip.decompress(data)
            elif compression_type == CompressionType.LZMA:
                return lzma.decompress(data)
            elif compression_type == CompressionType.ZLIB:
                return zlib.decompress(data)
        except Exception as e:
            logger.error(f"Decompression error: {e}")

        return data

class IntelligentCache:
    """Multi-tier intelligent caching system"""

    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.memory_cache = MemoryCache(
            self.config.memory_cache_size,
            self.config.memory_max_items,
            self.config.memory_cache_ttl
        )
        self.redis_cache = RedisCache(
            self.config.redis_url,
            self.config.redis_cache_ttl,
            self.config.redis_max_memory
        )
        self.compression = CacheCompression()
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)
        self.background_tasks = set()

    async def initialize(self):
        """Initialize cache components"""
        await self.redis_cache.initialize()

    def _generate_cache_key(self, request: Request, params: Dict[str, Any] = None) -> str:
        """Generate intelligent cache key"""
        # Use fast hash function
        key_components = [
            request.method,
            str(request.url),
            str(request.query_params),
            json.dumps(params or {}, sort_keys=True)
        ]

        key_data = "|".join(key_components).encode()
        # Use xxhash for faster hashing
        return xxhash.xxh64(key_data).hexdigest()

    def _generate_etag(self, data: Any) -> str:
        """Generate ETag for cache entry"""
        if isinstance(data, (str, bytes)):
            data_str = data
        else:
            data_str = json.dumps(data, sort_keys=True)

        return f'"{hashlib.md5(data_str.encode()).hexdigest()}"'

    async def get(self, request: Request, params: Dict[str, Any] = None) -> Optional[CacheEntry]:
        """Get cached response"""
        cache_key = self._generate_cache_key(request, params)

        # Try memory cache first
        entry = self.memory_cache.get(cache_key)
        if entry:
            # Background refresh if needed
            if self.config.enable_background_refresh:
                await self._schedule_background_refresh(cache_key, entry)
            return entry

        # Try Redis cache
        entry = await self.redis_cache.get(cache_key)
        if entry:
            # Decompress if needed
            if entry.compression_type != CompressionType.NONE:
                if isinstance(entry.value, bytes):
                    entry.value = self.compression.decompress(entry.value, entry.compression_type)
                    entry.compression_type = CompressionType.NONE

            # Store in memory cache
            self.memory_cache.put(cache_key, entry)

            # Background refresh if needed
            if self.config.enable_background_refresh:
                await self._schedule_background_refresh(cache_key, entry)

            return entry

        return None

    async def put(self, request: Request, response: Any, tags: Set[str] = None,
                  ttl: int = None, params: Dict[str, Any] = None) -> str:
        """Cache response with intelligent optimization"""
        cache_key = self._generate_cache_key(request, params)

        # Determine TTL
        if ttl is None:
            ttl = self.config.memory_cache_ttl

        expires_at = time.time() + ttl

        # Serialize response
        if isinstance(response, (dict, list)):
            serialized_data = orjson.dumps(response)
            content_type = "application/json"
        else:
            serialized_data = str(response).encode()
            content_type = "text/plain"

        # Compress if enabled and threshold met
        compression_type = CompressionType.NONE
        if (self.config.enable_compression and
            len(serialized_data) > self.config.compression_threshold):

            compressed_data, compression_type = self.compression.compress(
                serialized_data,
                self.config.compression_type,
                self.config.compression_level
            )

            # Use compressed data only if it's smaller
            if len(compressed_data) < len(serialized_data):
                serialized_data = compressed_data
            else:
                compression_type = CompressionType.NONE

        # Create cache entry
        entry = CacheEntry(
            key=cache_key,
            value=serialized_data,
            created_at=time.time(),
            expires_at=expires_at,
            size_bytes=len(serialized_data),
            compression_type=compression_type,
            tags=tags or set(),
            etag=self._generate_etag(response),
            content_type=content_type,
            response_headers={}
        )

        # Store in memory cache
        if self.config.enable_write_through:
            self.memory_cache.put(cache_key, entry)
            await self.redis_cache.put(cache_key, entry)
        else:
            self.memory_cache.put(cache_key, entry)

            if self.config.enable_write_behind:
                # Schedule background write to Redis
                asyncio.create_task(self.redis_cache.put(cache_key, entry))

        # Update tag index
        if tags and self.config.enable_tag_based_invalidation:
            for tag in tags:
                self.tag_index[tag].add(cache_key)

        return cache_key

    async def invalidate_by_tags(self, tags: Set[str]):
        """Invalidate cache entries by tags"""
        if not self.config.enable_tag_based_invalidation:
            return

        keys_to_remove = set()
        for tag in tags:
            keys_to_remove.update(self.tag_index.get(tag, set()))
            self.tag_index[tag].clear()

        # Remove from all cache levels
        for key in keys_to_remove:
            self.memory_cache.remove(key)
            await self.redis_cache.remove(key)

    async def invalidate_by_pattern(self, pattern: str):
        """Invalidate cache entries by pattern"""
        # This would require more sophisticated implementation
        # For now, we'll clear Redis cache by pattern
        await self.redis_cache.clear_by_pattern(pattern)

    async def _schedule_background_refresh(self, cache_key: str, entry: CacheEntry):
        """Schedule background refresh for expiring entries"""
        if not entry:
            return

        time_until_expiry = entry.expires_at - time.time()
        refresh_time = time_until_expiry * self.config.refresh_threshold

        if refresh_time > 0:
            # This would need to be integrated with the actual handler
            # For now, it's a placeholder for the refresh mechanism
            pass

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return {
            "memory_cache": self.memory_cache.get_stats(),
            "redis_cache": self.redis_cache.get_stats(),
            "config": asdict(self.config),
            "tag_index_size": len(self.tag_index)
        }

    async def cleanup(self):
        """Cleanup resources"""
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

# FastAPI middleware integration
class CacheMiddleware:
    """FastAPI middleware for intelligent caching"""

    def __init__(self, app, cache: IntelligentCache, cacheable_paths: List[str] = None):
        self.app = app
        self.cache = cache
        self.cacheable_paths = cacheable_paths or []

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Create request object
        request = Request(scope, receive)

        # Check if path is cacheable
        if not any(request.url.path.startswith(path) for path in self.cacheable_paths):
            await self.app(scope, receive, send)
            return

        # Check for cached response
        cached_entry = await self.cache.get(request)
        if cached_entry:
            # Create response from cache
            response_data = cached_entry.value
            if cached_entry.compression_type != CompressionType.NONE:
                response_data = self.cache.compression.decompress(
                    response_data,
                    cached_entry.compression_type
                )

            # Send cached response
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", cached_entry.content_type.encode()),
                    (b"cache-control", b"hit"),
                    (b"etag", cached_entry.etag.encode() if cached_entry.etag else b""),
                ],
            })

            await send({
                "type": "http.response.body",
                "body": response_data,
            })
            return

        # Process request and cache response
        # This would need integration with the actual FastAPI request handling
        await self.app(scope, receive, send)

# Decorator for caching function results
def cache_response(ttl: int = 300, tags: Set[str] = None, key_params: List[str] = None):
    """Decorator to cache function responses"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would need implementation to work with the cache system
            return await func(*args, **kwargs)
        return wrapper
    return decorator

if __name__ == "__main__":
    # Example usage
    async def main():
        cache = IntelligentCache()
        await cache.initialize()

        # Example caching
        from fastapi import FastAPI, Request

        app = FastAPI()

        @app.get("/api/data")
        @cache_response(ttl=600, tags={"data", "api"})
        async def get_data():
            return {"message": "This response is cached!", "timestamp": time.time()}

        # Add cache middleware
        app.add_middleware(CacheMiddleware, cache=cache, cacheable_paths=["/api/"])

    asyncio.run(main())