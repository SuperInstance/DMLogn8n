#!/usr/bin/env python3
"""
Advanced API Request Optimization System
Optimizes request processing for sub-50ms response times
"""

import asyncio
import time
import json
import logging
import hashlib
import re
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
import aioredis
import aiohttp
from fastapi import Request, Response, HTTPException
from fastapi.routing import APIRoute
from pydantic import BaseModel, validator
import orjson
import uvloop
import cython

# Configure ultra-high-performance logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

@dataclass
class RequestMetrics:
    """Request performance metrics"""
    request_id: str
    start_time: float
    end_time: float
    processing_time: float
    size_bytes: int
    method: str
    path: str
    status_code: int
    cache_hit: bool = False
    optimized: bool = False

@dataclass
class OptimizationConfig:
    """Configuration for request optimization"""
    enable_request_validation_cache: bool = True
    enable_response_compression: bool = True
    enable_connection_pooling: bool = True
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    validation_cache_ttl: int = 3600
    connection_pool_size: int = 100
    max_concurrent_requests: int = 1000
    enable_request_deduplication: bool = True
    deduplication_window: int = 100  # milliseconds

class RequestValidatorCache:
    """High-performance request validation caching"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = None
        self.redis_url = redis_url
        self.local_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0

    async def initialize(self):
        """Initialize Redis connection"""
        self.redis = await aioredis.from_url(self.redis_url, decode_responses=False)

    def _generate_cache_key(self, request_data: Dict[str, Any]) -> str:
        """Generate cache key for request validation"""
        key_data = json.dumps(request_data, sort_keys=True)
        return f"req_val:{hashlib.sha256(key_data.encode()).hexdigest()}"

    async def get_validation_result(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached validation result"""
        cache_key = self._generate_cache_key(request_data)

        # Check local cache first
        if cache_key in self.local_cache:
            self.cache_hits += 1
            return self.local_cache[cache_key]

        # Check Redis cache
        if self.redis:
            try:
                cached_result = await self.redis.get(cache_key)
                if cached_result:
                    result = orjson.loads(cached_result)
                    self.local_cache[cache_key] = result
                    self.cache_hits += 1
                    return result
            except Exception as e:
                logger.error(f"Redis cache error: {e}")

        self.cache_misses += 1
        return None

    async def cache_validation_result(self, request_data: Dict[str, Any], result: Dict[str, Any], ttl: int = 3600):
        """Cache validation result"""
        cache_key = self._generate_cache_key(request_data)

        # Store in local cache
        self.local_cache[cache_key] = result

        # Store in Redis cache
        if self.redis:
            try:
                await self.redis.setex(cache_key, ttl, orjson.dumps(result))
            except Exception as e:
                logger.error(f"Redis cache set error: {e}")

class RequestDeduplicator:
    """Request deduplication for identical concurrent requests"""

    def __init__(self, window_ms: int = 100):
        self.window_ms = window_ms
        self.pending_requests: Dict[str, List[asyncio.Future]] = defaultdict(list)
        self.request_timestamps: Dict[str, float] = {}

    def _generate_request_key(self, request: Request) -> str:
        """Generate unique key for request deduplication"""
        key_data = f"{request.method}:{request.url}:{hash(str(request.query_params))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def deduplicate_request(self, request: Request, handler: Callable) -> Any:
        """Deduplicate identical concurrent requests"""
        request_key = self._generate_request_key(request)
        current_time = time.time() * 1000  # Convert to milliseconds

        # Clean old requests
        self._cleanup_old_requests(current_time)

        # Check if identical request is already processing
        if request_key in self.request_timestamps:
            if current_time - self.request_timestamps[request_key] < self.window_ms:
                # Create future for this request
                future = asyncio.Future()
                self.pending_requests[request_key].append(future)

                try:
                    # Wait for the original request to complete
                    result = await future
                    return result
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Deduplicated request failed: {e}")

        # Mark this request as processing
        self.request_timestamps[request_key] = current_time

        try:
            # Process the request
            result = await handler(request)

            # Resolve all waiting requests with the same result
            for future in self.pending_requests[request_key]:
                if not future.done():
                    future.set_result(result)

            return result

        except Exception as e:
            # Reject all waiting requests
            for future in self.pending_requests[request_key]:
                if not future.done():
                    future.set_exception(e)
            raise e

        finally:
            # Cleanup
            self.pending_requests[request_key].clear()
            if request_key in self.request_timestamps:
                del self.request_timestamps[request_key]

    def _cleanup_old_requests(self, current_time: float):
        """Clean up old request timestamps"""
        old_keys = [
            key for key, timestamp in self.request_timestamps.items()
            if current_time - timestamp > self.window_ms * 2
        ]
        for key in old_keys:
            del self.request_timestamps[key]
            if key in self.pending_requests:
                del self.pending_requests[key]

class RequestOptimizer:
    """High-performance request optimization engine"""

    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.validator_cache = RequestValidatorCache()
        self.deduplicator = RequestDeduplicator(self.config.deduplication_window)
        self.metrics_collector = defaultdict(list)
        self.connection_pool = None
        self.executor = ThreadPoolExecutor(max_workers=50)

        # Pre-compiled regex patterns for performance
        self.sanitization_patterns = {
            'sql_injection': re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)", re.IGNORECASE),
            'xss': re.compile(r"<script|javascript:|on\w+\s*=", re.IGNORECASE),
            'path_traversal': re.compile(r"\.\./|\.\.\\\"),
            'command_injection': re.compile(r"[;&|`$(){}[\]\\]")
        }

    async def initialize(self):
        """Initialize optimizer components"""
        await self.validator_cache.initialize()

        # Initialize connection pool
        if self.config.enable_connection_pooling:
            connector = aiohttp.TCPConnector(
                limit=self.config.connection_pool_size,
                limit_per_host=20,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            self.connection_pool = aiohttp.ClientSession(connector=connector)

    async def optimize_request(self, request: Request, handler: Callable) -> Response:
        """Optimize incoming request processing"""
        start_time = time.perf_counter()
        request_id = self._generate_request_id()

        try:
            # Pre-processing optimizations
            await self._pre_process_request(request)

            # Request deduplication
            if self.config.enable_request_deduplication:
                result = await self.deduplicator.deduplicate_request(request, handler)
            else:
                result = await handler(request)

            # Post-processing optimizations
            optimized_response = await self._post_process_response(result, request)

            # Record metrics
            processing_time = (time.perf_counter() - start_time) * 1000  # Convert to milliseconds
            self._record_metrics(request_id, request, optimized_response, processing_time)

            return optimized_response

        except Exception as e:
            logger.error(f"Request optimization error: {e}")
            raise HTTPException(status_code=500, detail="Request processing failed")

    async def _pre_process_request(self, request: Request):
        """Pre-process request for optimization"""
        # Size validation
        content_length = request.headers.get("content-length", "0")
        if int(content_length) > self.config.max_request_size:
            raise HTTPException(status_code=413, detail="Request too large")

        # Fast validation using cache
        if self.config.enable_request_validation_cache:
            request_data = {
                "method": request.method,
                "path": str(request.url),
                "headers": dict(request.headers),
                "query_params": dict(request.query_params)
            }

            cached_validation = await self.validator_cache.get_validation_result(request_data)
            if not cached_validation:
                # Perform validation and cache result
                validation_result = await self._validate_request_fast(request)
                await self.validator_cache.cache_validation_result(
                    request_data,
                    validation_result,
                    self.config.validation_cache_ttl
                )

    async def _validate_request_fast(self, request: Request) -> Dict[str, Any]:
        """Fast request validation"""
        validation_result = {"valid": True, "errors": []}

        # Quick header validation
        suspicious_headers = ['user-agent', 'referer', 'x-forwarded-for']
        for header in suspicious_headers:
            if header in request.headers:
                value = request.headers[header]
                if any(pattern.search(value) for pattern in self.sanitization_patterns.values()):
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Suspicious {header} header")

        # Quick query parameter validation
        for param, value in request.query_params.items():
            if any(pattern.search(value) for pattern in self.sanitization_patterns.values()):
                validation_result["valid"] = False
                validation_result["errors"].append(f"Suspicious query parameter: {param}")

        return validation_result

    async def _post_process_response(self, response: Response, request: Request) -> Response:
        """Post-process response for optimization"""
        # Add performance headers
        response.headers["X-Response-Time"] = f"{time.perf_counter():.3f}"
        response.headers["X-Cache-Status"] = "MISS"  # Will be updated by caching system

        # Compression will be handled by compression engine
        if self.config.enable_response_compression:
            response.headers["Vary"] = "Accept-Encoding"

        return response

    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return str(uuid.uuid4())

    def _record_metrics(self, request_id: str, request: Request, response: Response, processing_time: float):
        """Record request metrics"""
        metrics = RequestMetrics(
            request_id=request_id,
            start_time=0,  # Will be set by monitoring system
            end_time=0,    # Will be set by monitoring system
            processing_time=processing_time,
            size_bytes=len(str(response.body)) if hasattr(response, 'body') else 0,
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code
        )

        self.metrics_collector[request.method].append(metrics)

        # Keep only last 1000 metrics per method
        if len(self.metrics_collector[request.method]) > 1000:
            self.metrics_collector[request.method] = self.metrics_collector[request.method][-1000:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {}

        for method, metrics_list in self.metrics_collector.items():
            if not metrics_list:
                continue

            processing_times = [m.processing_time for m in metrics_list]
            stats[method] = {
                "total_requests": len(metrics_list),
                "avg_processing_time": sum(processing_times) / len(processing_times),
                "min_processing_time": min(processing_times),
                "max_processing_time": max(processing_times),
                "p95_processing_time": sorted(processing_times)[int(len(processing_times) * 0.95)],
                "p99_processing_time": sorted(processing_times)[int(len(processing_times) * 0.99)],
                "cache_hit_rate": self.validator_cache.cache_hits / (self.validator_cache.cache_hits + self.validator_cache.cache_misses) * 100
            }

        return stats

    async def cleanup(self):
        """Cleanup resources"""
        if self.connection_pool:
            await self.connection_pool.close()
        self.executor.shutdown(wait=True)

# FastAPI middleware integration
class OptimizedRoute(APIRoute):
    """Optimized API route with performance enhancements"""

    def __init__(self, *args, optimizer: RequestOptimizer = None, **kwargs):
        self.optimizer = optimizer or RequestOptimizer()
        super().__init__(*args, **kwargs)

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            return await self.optimizer.optimize_request(request, original_route_handler)

        return custom_route_handler

# Utility functions
def create_fastapi_app_with_optimization() -> 'FastAPI':
    """Create FastAPI app with request optimization"""
    from fastapi import FastAPI

    app = FastAPI()
    optimizer = RequestOptimizer()

    @app.on_event("startup")
    async def startup_event():
        await optimizer.initialize()

    @app.on_event("shutdown")
    async def shutdown_event():
        await optimizer.cleanup()

    @app.get("/performance/stats")
    async def get_performance_stats():
        return optimizer.get_performance_stats()

    return app, optimizer

if __name__ == "__main__":
    # Example usage
    import uvicorn

    app, optimizer = create_fastapi_app_with_optimization()

    # Example optimized endpoint
    @app.get("/api/fast")
    async def fast_endpoint():
        return {"message": "This is optimized for speed!", "timestamp": time.time()}

    uvicorn.run(app, host="0.0.0.0", port=8000)