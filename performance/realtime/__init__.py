#!/usr/bin/env python3
"""
Real-time Performance Optimization System for DMLogn8n
Complete performance optimization suite for ultra-fast, responsive applications
"""

from .latency_optimizer import (
    latency_optimizer,
    LatencyOptimizer,
    low_latency,
    realtime_optimized,
    hot_path
)

from .connection_pool import (
    connection_pool_manager,
    ConnectionPool,
    ConnectionPoolManager,
    setup_default_pools
)

from .cache_accelerator import (
    cache_accelerator,
    CacheAccelerator,
    fast_cache,
    ultra_fast_cache
)

from .async_processor import (
    async_processor,
    AsyncProcessor,
    optimize_async,
    high_priority_async,
    critical_async,
    run_optimized,
    parallel_execute
)

from .websocket_optimizer import (
    websocket_optimizer,
    WebSocketOptimizer,
    start_websocket_server,
    websocket_handler
)

from .query_optimizer import (
    query_optimizer,
    QueryOptimizer,
    optimize_query,
    analyze_slow_queries,
    get_index_recommendations
)

from .memory_manager import (
    memory_manager,
    MemoryManager,
    memory_efficient,
    track_memory,
    get_memory_usage,
    cleanup_memory,
    optimize_memory
)

from .profiler_realtime import (
    realtime_profiler,
    RealtimeProfiler,
    profile_function,
    profile_database,
    profile_cache,
    track_performance,
    start_profiling,
    stop_profiling,
    get_performance_report,
    record_metric
)

__version__ = "1.0.0"
__author__ = "DMLogn8n Performance Team"
__description__ = "Real-time performance optimization system for DMLogn8n"

# Export main classes and functions
__all__ = [
    # Core optimization systems
    'latency_optimizer',
    'cache_accelerator',
    'async_processor',
    'websocket_optimizer',
    'query_optimizer',
    'memory_manager',
    'realtime_profiler',

    # Connection management
    'connection_pool_manager',
    'setup_default_pools',

    # Decorators for easy optimization
    'low_latency',
    'realtime_optimized',
    'hot_path',
    'fast_cache',
    'ultra_fast_cache',
    'optimize_async',
    'high_priority_async',
    'critical_async',
    'optimize_query',
    'memory_efficient',
    'track_memory',
    'profile_function',
    'profile_database',
    'profile_cache',
    'track_performance',

    # Utility functions
    'run_optimized',
    'parallel_execute',
    'start_websocket_server',
    'analyze_slow_queries',
    'get_index_recommendations',
    'get_memory_usage',
    'cleanup_memory',
    'optimize_memory',
    'start_profiling',
    'stop_profiling',
    'get_performance_report',
    'record_metric'
]