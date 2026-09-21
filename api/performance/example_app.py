#!/usr/bin/env python3
"""
Complete Example Application Demonstrating the API Performance System
This example shows how to integrate all performance components for sub-50ms response times
"""

import asyncio
import time
import random
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# Import all performance components
from . import (
    APPerformanceSystem,
    create_performance_system,
    optimized_route,
    PerformanceMeasure
)
from .request_optimizer import OptimizationConfig
from .response_caching import CacheConfig
from .rate_limiter_pro import RateLimitConfig, UserType, RateLimitStrategy, RateLimitRule
from .compression_engine import CompressionConfig, CompressionAlgorithm
from .async_handler import AsyncConfig, TaskPriority
from .batch_processor import BatchConfig, BatchType, BatchPriority
from .monitoring_api import MonitoringConfig, AlertSeverity
from .load_balancer_api import LoadBalancingConfig, LoadBalancingAlgorithm, ServerConfig, ServerType

# Global performance system instance
performance_system = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global performance_system

    print("🚀 Starting High-Performance API System...")

    # Initialize performance system with optimized configurations
    performance_system = create_performance_system("example_high_performance_api")

    # Create optimized configurations for sub-50ms response times
    optimization_config = OptimizationConfig(
        enable_request_validation_cache=True,
        enable_response_compression=True,
        enable_connection_pooling=True,
        max_request_size=10 * 1024 * 1024,  # 10MB
        validation_cache_ttl=3600,  # 1 hour
        connection_pool_size=100,
        max_concurrent_requests=2000,  # High concurrency
        enable_request_deduplication=True,
        deduplication_window=50  # 50ms window
    )

    cache_config = CacheConfig(
        # Large memory cache for ultra-fast access
        memory_cache_size=200 * 1024 * 1024,  # 200MB
        memory_cache_ttl=600,  # 10 minutes
        memory_max_items=20000,

        # Redis for distributed caching
        redis_url="redis://localhost:6379",
        redis_cache_ttl=3600,  # 1 hour
        redis_max_memory="512mb",

        # Advanced compression
        enable_compression=True,
        compression_threshold=512,  # Compress even small responses
        compression_algorithm=CompressionAlgorithm.ZSTD,
        compression_level=3,  # Fast compression

        # Intelligent caching
        enable_background_refresh=True,
        refresh_threshold=0.7,  # Refresh at 70% of TTL
        enable_tag_based_invalidation=True,
        enable_write_through=True
    )

    rate_limit_config = RateLimitConfig(
        redis_url="redis://localhost:6379",

        # Tiered rate limiting for different user types
        default_limits={
            UserType.ANONYMOUS: RateLimitRule(
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                requests_per_window=100,
                window_seconds=3600,
                burst_capacity=20
            ),
            UserType.FREE: RateLimitRule(
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                requests_per_window=1000,
                window_seconds=3600,
                burst_capacity=100
            ),
            UserType.PREMIUM: RateLimitRule(
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                requests_per_window=10000,
                window_seconds=3600,
                burst_capacity=500
            ),
            UserType.ENTERPRISE: RateLimitRule(
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                requests_per_window=100000,
                window_seconds=3600,
                burst_capacity=2000
            )
        },

        # Advanced features
        enable_geographic_limiting=True,
        enable_adaptive_limiting=True,
        adaptive_learning_rate=0.1,
        enable_priority_queue=True,
        priority_queue_size=1000,
        queue_timeout_seconds=30
    )

    compression_config = CompressionConfig(
        default_algorithm=CompressionAlgorithm.ZSTD,  # Best compression
        default_level=3,  # Balanced speed/size
        compression_threshold=512,  # Compress small responses
        max_compression_size=50 * 1024 * 1024,  # 50MB

        # Adaptive compression
        enable_adaptive_compression=True,
        enable_streaming_compression=True,
        enable_parallel_compression=True,
        max_parallel_workers=4,
        performance_threshold_ms=5.0,  # 5ms compression target

        # Content optimization
        compressible_types=[
            "application/json",
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript",
            "text/xml",
            "application/xml",
            "text/plain"
        ]
    )

    async_config = AsyncConfig(
        # Ultra-fast event loop
        use_uvloop=True,
        max_event_loop_workers=2000,

        # High-performance thread pools
        max_thread_workers=100,
        max_process_workers=20,

        # Task management
        max_queue_size=20000,
        priority_queue_enabled=True,
        enable_task_cancellation=True,
        enable_task_timeout=True,
        default_task_timeout=30,

        # Advanced features
        enable_task_deduplication=True,
        enable_batching=True,
        batch_size=20,
        batch_timeout_ms=50
    )

    batch_config = BatchConfig(
        # Optimized batch sizes
        default_batch_size=20,
        max_batch_size=100,
        min_batch_size=5,

        # Fast batch processing
        batch_timeout_ms=50,  # 50ms max wait
        batch_interval_ms=10,  # Process every 10ms
        max_wait_time_ms=500,

        # High-performance settings
        max_queue_size=20000,
        enable_parallel_batches=True,
        max_concurrent_batches=10,

        # Intelligent batching
        enable_adaptive_batching=True,
        adaptive_window_size=200,
        performance_threshold_ms=10.0,

        # Reliability
        enable_batch_retry=True,
        max_batch_retries=3,
        partial_success_enabled=True
    )

    monitoring_config = MonitoringConfig(
        # High-frequency monitoring
        metrics_collection_interval=0.5,  # 500ms
        detailed_metrics_interval=5.0,  # 5 seconds
        max_metrics_points=20000,
        metrics_retention_seconds=7200,  # 2 hours

        # Real-time monitoring
        enable_realtime_monitoring=True,
        websocket_buffer_size=2000,
        realtime_update_interval=0.1,  # 100ms

        # Alerting
        enable_alerts=True,
        alert_check_interval=2.0,  # 2 seconds
        alert_cooldown_seconds=300,  # 5 minutes

        # Performance thresholds
        response_time_warning_ms=25.0,  # 25ms warning (very strict)
        response_time_critical_ms=50.0,  # 50ms critical
        error_rate_warning_percent=1.0,  # 1% error rate warning
        error_rate_critical_percent=5.0,  # 5% error rate critical
        memory_warning_mb=400.0,
        memory_critical_mb=800.0,
        cpu_warning_percent=70.0,
        cpu_critical_percent=90.0,

        # Storage
        enable_redis_storage=True,
        redis_url="redis://localhost:6379",
        enable_file_storage=True,

        # Export
        enable_prometheus=True,
        prometheus_port=9090,
        enable_json_export=True,
        export_interval=30
    )

    load_balancing_config = LoadBalancingConfig(
        # Use least response time for optimal performance
        algorithm=LoadBalancingAlgorithm.LEAST_RESPONSE_TIME,
        enable_sticky_sessions=True,

        # Aggressive health checking
        enable_health_checks=True,
        health_check_interval=15,  # 15 seconds
        health_check_timeout=2.0,
        health_check_retries=2,
        unhealthy_threshold=2,
        healthy_threshold=2,

        # Fast failover
        enable_failover=True,
        failover_timeout=5.0,
        max_failover_attempts=3,
        circuit_breaker_threshold=0.3,  # 30% error rate
        circuit_breaker_timeout=30,  # 30 seconds

        # High-performance connections
        enable_connection_pooling=True,
        max_connections_per_server=200,
        connection_timeout=2.0,
        read_timeout=10.0,
        keepalive_timeout=30.0,

        # Service discovery
        enable_service_discovery=False,  # Disabled for example
        discovery_type="static",

        # Advanced features
        enable_predictive_scaling=True,
        enable_adaptive_routing=True,
        enable_content_based_routing=True
    )

    # Initialize the performance system
    await performance_system.initialize(
        optimization_config=optimization_config,
        cache_config=cache_config,
        rate_limit_config=rate_limit_config,
        compression_config=compression_config,
        async_config=async_config,
        batch_config=batch_config,
        monitoring_config=monitoring_config,
        load_balancing_config=load_balancing_config
    )

    print("✅ Performance System Initialized Successfully!")
    print(f"🎯 Performance Targets: <25ms response times, >20,000 req/s")

    # Setup custom alerts
    if performance_system.metrics_collector:
        async def performance_alert_handler(alert_data):
            severity = alert_data.get('severity', 'info')
            if severity == 'critical':
                print(f"🚨 CRITICAL ALERT: {alert_data['name']}")
                print(f"   Current: {alert_data['current_value']}, Threshold: {alert_data['threshold']}")
            elif severity == 'warning':
                print(f"⚠️  WARNING: {alert_data['name']}")

        performance_system.metrics_collector.add_alert_handler(performance_alert_handler)

        # Add aggressive performance alert
        from .monitoring_api import Alert
        high_response_time_alert = Alert(
            id='high_response_time',
            name='High Response Time Detected',
            severity=AlertSeverity.WARNING,
            condition='greater_than',
            threshold=0.025,  # 25ms
            metric_name='avg_response_time'
        )
        performance_system.metrics_collector.add_alert(high_response_time_alert)

    yield

    # Cleanup
    print("🛑 Shutting down Performance System...")
    await performance_system.shutdown()
    print("✅ Shutdown complete")

# Create FastAPI app with performance middleware
app = FastAPI(
    title="Ultra High-Performance API",
    description="Demonstration of sub-25ms API response times with advanced optimization",
    version="1.0.0",
    lifespan=lifespan
)

# Performance-optimized endpoints
@app.get("/")
@optimized_route(cache_ttl=60, compress=True, priority="high")
async def root():
    """Ultra-fast root endpoint"""
    return {
        "message": "Ultra High-Performance API",
        "response_time": "< 25ms",
        "timestamp": time.time()
    }

@app.get("/api/fast")
@optimized_route(cache_ttl=300, compress=True, priority="high")
async def ultra_fast_endpoint():
    """Demonstrates sub-10ms response times"""
    async with PerformanceMeasure("ultra_fast_operation", performance_system.metrics_collector):
        # Simulate minimal work
        await asyncio.sleep(0.001)  # 1ms simulated work
        return {
            "message": "This response is optimized for ultra-low latency!",
            "processing_time_ms": "< 10ms",
            "cached": True,
            "compressed": True,
            "timestamp": time.time()
        }

@app.get("/api/cached")
@optimized_route(cache_ttl=600, compress=True, priority="normal")
async def cached_endpoint():
    """Demonstrates intelligent caching"""
    async with PerformanceMeasure("cached_operation", performance_system.metrics_collector):
        # Simulate some work that benefits from caching
        await asyncio.sleep(0.005)  # 5ms work
        return {
            "message": "This response is intelligently cached",
            "cache_ttl": 600,
            "cache_hit": True,
            "timestamp": time.time()
        }

@app.get("/api/compute")
@optimized_route(cache_ttl=60, compress=True, priority="normal")
async def compute_intensive():
    """Demonstrates batch processing for compute operations"""
    if performance_system and performance_system.batch_processor:
        # Submit to batch processor
        task_id = await performance_system.batch_processor.submit_item(
            {"operation": "fibonacci", "n": 35},
            batch_type=BatchType.COMPUTATION,
            priority=BatchPriority.HIGH
        )

        return {
            "message": "Computation submitted to batch processor",
            "task_id": task_id,
            "expected_completion": "< 100ms"
        }

    return {"message": "Batch processor not available"}

@app.get("/api/database")
@optimized_route(cache_ttl=1800, compress=True, priority="normal")
async def database_query():
    """Demonstrates database batch processing"""
    if performance_system and performance_system.batch_processor:
        # Submit database query to batch processor
        task_id = await performance_system.batch_processor.submit_item(
            {"query": "SELECT * FROM users LIMIT 100", "type": "read"},
            batch_type=BatchType.DATABASE_READ,
            priority=BatchPriority.NORMAL
        )

        return {
            "message": "Database query submitted to batch processor",
            "task_id": task_id,
            "cached": True
        }

    return {"message": "Batch processor not available"}

@app.get("/api/background")
@optimized_route(cache_ttl=0, compress=False, priority="low")
async def background_task():
    """Demonstrates background task processing"""
    if performance_system and performance_system.async_handler:
        # Submit background task
        task_id = await performance_system.async_handler.submit_background_task(
            background_computation,
            data="sample_data"
        )

        return {
            "message": "Background task submitted",
            "task_id": task_id,
            "status": "processing"
        }

    return {"message": "Async handler not available"}

async def background_computation(data):
    """Example background computation"""
    await asyncio.sleep(0.1)  # 100ms background work
    return f"Processed: {data}"

@app.get("/api/load_test")
@optimized_route(cache_ttl=1, compress=True, priority="high")
async def load_test_endpoint():
    """Endpoint designed for load testing"""
    # Minimal work to test system limits
    return {
        "message": "Load test endpoint",
        "timestamp": time.time(),
        "request_id": f"{random.randint(10000, 99999)}"
    }

@app.get("/api/performance")
async def get_performance_stats():
    """Get current performance statistics"""
    if not performance_system:
        raise HTTPException(status_code=503, detail="Performance system not initialized")

    return performance_system.get_performance_summary()

@app.get("/api/detailed_metrics")
async def get_detailed_metrics():
    """Get comprehensive performance metrics"""
    if not performance_system:
        raise HTTPException(status_code=503, detail="Performance system not initialized")

    metrics = {}

    if performance_system.metrics_collector:
        metrics["system"] = performance_system.metrics_collector.get_current_metrics()

    if performance_system.request_optimizer:
        metrics["request_optimizer"] = performance_system.request_optimizer.get_performance_stats()

    if performance_system.cache:
        metrics["cache"] = performance_system.cache.get_comprehensive_stats()

    if performance_system.rate_limiter:
        metrics["rate_limiter"] = performance_system.rate_limiter.get_stats()

    if performance_system.compression_engine:
        metrics["compression"] = performance_system.compression_engine.get_stats()

    if performance_system.async_handler:
        metrics["async_handler"] = performance_system.async_handler.get_stats()

    if performance_system.batch_processor:
        metrics["batch_processor"] = performance_system.batch_processor.get_stats()

    if performance_system.load_balancer:
        metrics["load_balancer"] = performance_system.load_balancer.get_stats()

    return metrics

@app.post("/api/cache/clear")
async def clear_all_caches():
    """Clear all caches (for testing)"""
    if performance_system and performance_system.cache:
        performance_system.cache.memory_cache.clear()
        return {"status": "all_caches_cleared"}

    return {"status": "no_cache_system"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not performance_system:
        return {"status": "unhealthy", "reason": "Performance system not initialized"}

    # Get basic health metrics
    metrics = performance_system.get_performance_summary()

    status = "healthy"
    if metrics.get("current_avg_response_time", 0) > 0.05:  # 50ms
        status = "degraded"
    if metrics.get("current_error_rate", 0) > 0.05:  # 5%
        status = "unhealthy"

    return {
        "status": status,
        "timestamp": time.time(),
        "performance": metrics
    }

# Middleware for automatic performance tracking
@app.middleware("http")
async def performance_tracking_middleware(request: Request, call_next):
    """Track performance for all requests"""
    start_time = time.perf_counter()

    # Process request
    response = await call_next(request)

    # Calculate processing time
    processing_time = time.perf_counter() - start_time

    # Record metrics if available
    if performance_system and performance_system.metrics_collector:
        performance_system.metrics_collector.record_request(
            method=request.method,
            endpoint=str(request.url.path),
            status_code=response.status_code,
            response_time=processing_time
        )

    # Add performance headers
    response.headers["X-Response-Time"] = f"{processing_time*1000:.2f}ms"
    response.headers["X-Performance-Optimized"] = "true"

    return response

if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Ultra High-Performance API Example...")
    print("📊 Performance Targets:")
    print("   - Response Time: < 25ms")
    print("   - Throughput: > 20,000 req/s")
    print("   - Cache Hit Rate: > 95%")
    print("   - Error Rate: < 0.1%")
    print()
    print("🔗 Available Endpoints:")
    print("   GET  /           - Root endpoint")
    print("   GET  /api/fast   - Ultra-fast endpoint (< 10ms)")
    print("   GET  /api/cached - Cached endpoint")
    print("   GET  /api/compute - Batch computation")
    print("   GET  /api/database - Database query")
    print("   GET  /api/background - Background task")
    print("   GET  /api/load_test - Load testing endpoint")
    print("   GET  /api/performance - Performance summary")
    print("   GET  /api/detailed_metrics - Detailed metrics")
    print("   POST /api/cache/clear - Clear caches")
    print("   GET  /health - Health check")
    print()
    print("📈 Monitoring:")
    print("   - Prometheus metrics: http://localhost:9090/metrics")
    print("   - Real-time WebSocket: ws://localhost:8000/monitoring/realtime")
    print()
    print("🔧 Testing:")
    print("   - Load test: ab -n 10000 -c 100 http://localhost:8000/api/load_test")
    print("   - Response time: curl -w '@curl-format.txt' http://localhost:8000/api/fast")
    print()

    # Run with uvicorn for optimal performance
    uvicorn.run(
        "example_app:app",
        host="0.0.0.0",
        port=8000,
        workers=1,  # Single worker with asyncio for maximum performance
        loop="uvloop",  # Ultra-fast event loop
        access_log=False,  # Disable access logs for better performance
        use_colors=False
    )