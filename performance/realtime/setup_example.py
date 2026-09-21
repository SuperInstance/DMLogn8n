#!/usr/bin/env python3
"""
Example setup and usage of the Real-time Performance Optimization System
Demonstrates how to integrate all optimization components
"""

import asyncio
import time
from performance.realtime import (
    # Core systems
    latency_optimizer, cache_accelerator, async_processor,
    websocket_optimizer, query_optimizer, memory_manager,
    realtime_profiler, connection_pool_manager,

    # Decorators
    low_latency, realtime_optimized, hot_path,
    fast_cache, ultra_fast_cache, optimize_async,
    critical_async, memory_efficient, track_memory,
    profile_function, track_performance,

    # Utilities
    run_optimized, parallel_execute, get_memory_usage,
    get_performance_report
)

class DMLogn8nPerformanceSetup:
    """Complete performance optimization setup for DMLogn8n"""

    def __init__(self):
        self.setup_complete = False

    async def initialize(self):
        """Initialize all performance optimization systems"""
        print("🚀 Initializing DMLogn8n Performance Optimization System...")

        # Start async processor
        print("   Starting async processor...")
        await async_processor.start()

        # Start WebSocket optimizer
        print("   Starting WebSocket optimizer...")
        await websocket_optimizer.start()

        # Setup connection pools
        print("   Setting up connection pools...")
        self._setup_connection_pools()

        # Configure cache accelerator
        print("   Configuring cache accelerator...")
        self._configure_cache_accelerator()

        # Configure memory manager
        print("   Configuring memory manager...")
        self._configure_memory_manager()

        # Configure profiler
        print("   Configuring real-time profiler...")
        self._configure_profiler()

        # Setup performance thresholds
        print("   Setting performance thresholds...")
        self._setup_performance_thresholds()

        self.setup_complete = True
        print("✅ Performance optimization system initialized successfully!")

    def _setup_connection_pools(self):
        """Setup database and service connection pools"""
        # Database pool (high performance)
        from performance.realtime.connection_pool import ConnectionConfig
        db_config = ConnectionConfig(
            min_connections=10,
            max_connections=100,
            connection_timeout=2.0,
            idle_timeout=600.0,
            health_check_interval=15.0
        )
        connection_pool_manager.create_pool("database", "database", db_config)

        # HTTP API pool
        api_config = ConnectionConfig(
            min_connections=5,
            max_connections=50,
            connection_timeout=1.0,
            idle_timeout=300.0
        )
        connection_pool_manager.create_pool("api", "http", api_config)

        # Cache pool
        cache_config = ConnectionConfig(
            min_connections=3,
            max_connections=30,
            connection_timeout=0.5,
            idle_timeout=180.0
        )
        connection_pool_manager.create_pool("cache", "http", cache_config)

    def _configure_cache_accelerator(self):
        """Configure multi-layer caching"""
        from performance.realtime.cache_accelerator import CacheConfig
        config = CacheConfig(
            l1_max_size=1000,      # Ultra-fast cache
            l2_max_size=10000,     # Fast cache
            l3_max_size=50000,     # Medium cache
            memory_ttl=60.0,       # 1 minute default
            enable_prewarming=True,
            prewarm_interval=30.0,
            enable_compression=True,
            compression_threshold=1024
        )

        # Apply configuration (would need to reinitialize with config)
        cache_accelerator.config = config

    def _configure_memory_manager(self):
        """Configure memory management"""
        # Set memory limits
        memory_manager.max_memory_mb = 2048.0  # 2GB limit

        # Configure garbage collection
        memory_manager.gc_thresholds = [1000, 100, 10]

        # Create memory pools for different use cases
        memory_manager._create_default_pools()

    def _configure_profiler(self):
        """Configure real-time profiling"""
        # Enable continuous monitoring
        realtime_profiler.enable_continuous_profiling = True

        # Set sample interval
        realtime_profiler.sample_interval = 1.0

    def _setup_performance_thresholds(self):
        """Setup performance alert thresholds"""
        # Response time thresholds
        realtime_profiler.set_threshold("response_time", "warning", 100.0)   # 100ms
        realtime_profiler.set_threshold("response_time", "error", 500.0)     # 500ms
        realtime_profiler.set_threshold("response_time", "critical", 1000.0) # 1s

        # Memory usage thresholds
        realtime_profiler.set_threshold("memory_usage", "warning", 75.0)    # 75%
        realtime_profiler.set_threshold("memory_usage", "error", 90.0)      # 90%
        realtime_profiler.set_threshold("memory_usage", "critical", 95.0)   # 95%

        # CPU usage thresholds
        realtime_profiler.set_threshold("cpu_usage", "warning", 70.0)       # 70%
        realtime_profiler.set_threshold("cpu_usage", "error", 85.0)         # 85%
        realtime_profiler.set_threshold("cpu_usage", "critical", 95.0)      # 95%

    async def shutdown(self):
        """Shutdown all performance optimization systems"""
        print("🛑 Shutting down performance optimization system...")

        async_processor.stop()
        websocket_optimizer.stop()
        memory_manager.shutdown()
        realtime_profiler.shutdown()

        connection_pool_manager.close_all()
        print("✅ Performance optimization system shutdown complete!")

# Example optimized functions demonstrating usage
class ExampleDMLogn8nService:
    """Example service demonstrating all optimization techniques"""

    @low_latency("user_lookup")
    @fast_cache(ttl=300)
    @profile_function()
    async def get_user(self, user_id: int):
        """Optimized user lookup with caching and profiling"""
        # Simulate database lookup
        await asyncio.sleep(0.01)  # Simulate 10ms database call
        return {"id": user_id, "name": f"User {user_id}"}

    @critical_async
    @realtime_optimized
    @track_performance("emergency_response")
    async def emergency_notification(self, message: str):
        """Critical emergency response with highest priority"""
        # Simulate emergency processing
        await asyncio.sleep(0.001)  # Simulate 1ms processing
        return {"status": "sent", "message": message}

    @optimize_async()
    @memory_efficient(max_size_mb=50)
    @track_memory("data_processing")
    async def process_large_dataset(self, data_size: int):
        """Memory-efficient large dataset processing"""
        # Simulate data processing
        data = list(range(data_size))

        # Process in chunks to be memory efficient
        chunk_size = 1000
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            # Process chunk
            await asyncio.sleep(0.001)  # Simulate processing

        return {"processed_items": len(data)}

    @profile_database()
    @optimize_query
    async def complex_query(self, filters: dict):
        """Optimized database query"""
        # Simulate complex database query
        await asyncio.sleep(0.05)  # Simulate 50ms query
        return {"results": [f"Item {i}" for i in range(10)], "count": 10}

    @ultra_fast_cache(ttl=60)
    @hot_path
    def system_configuration(self):
        """Hot path system configuration"""
        # Simulate configuration loading
        time.sleep(0.001)  # Simulate 1ms load
        return {"setting1": "value1", "setting2": "value2"}

    async def batch_process_users(self, user_ids: list):
        """Batch processing with parallel execution"""
        # Create tasks for parallel processing
        tasks = [self.get_user(user_id) for user_id in user_ids]

        # Execute in parallel with controlled concurrency
        results = await parallel_execute(tasks, max_concurrency=10)
        return results

    async def websocket_broadcast(self, channel: str, message: dict):
        """Optimized WebSocket broadcasting"""
        await websocket_optimizer.broadcast_to_channel(channel, message)

# Performance monitoring and reporting
class PerformanceMonitor:
    """Monitor and report system performance"""

    def __init__(self):
        self.service = ExampleDMLogn8nService()

    async def run_performance_test(self):
        """Run comprehensive performance test"""
        print("🧪 Running performance test...")

        # Test individual functions
        await self._test_user_lookup()
        await self._test_emergency_response()
        await self._test_large_dataset_processing()
        await self._test_complex_query()
        await self._test_batch_processing()
        await self._test_websocket_broadcast()

        # Generate performance report
        await self._generate_performance_report()

    async def _test_user_lookup(self):
        """Test user lookup performance"""
        print("   Testing user lookup...")
        start_time = time.time()

        # Test multiple user lookups
        for i in range(100):
            await self.service.get_user(i)

        duration = time.time() - start_time
        avg_time = (duration / 100) * 1000
        print(f"   ✅ User lookup: {avg_time:.2f}ms average")

    async def _test_emergency_response(self):
        """Test emergency response performance"""
        print("   Testing emergency response...")
        start_time = time.time()

        # Test emergency notifications
        for i in range(10):
            await self.service.emergency_notification(f"Emergency {i}")

        duration = time.time() - start_time
        avg_time = (duration / 10) * 1000
        print(f"   ✅ Emergency response: {avg_time:.2f}ms average")

    async def _test_large_dataset_processing(self):
        """Test large dataset processing"""
        print("   Testing large dataset processing...")
        start_time = time.time()

        # Process dataset of 10,000 items
        result = await self.service.process_large_dataset(10000)

        duration = time.time() - start_time
        print(f"   ✅ Large dataset processing: {duration:.2f}s for {result['processed_items']} items")

    async def _test_complex_query(self):
        """Test complex query performance"""
        print("   Testing complex query...")
        start_time = time.time()

        # Execute complex query
        result = await self.service.complex_query({"filter": "test"})

        duration = time.time() - start_time
        print(f"   ✅ Complex query: {duration * 1000:.2f}ms")

    async def _test_batch_processing(self):
        """Test batch processing performance"""
        print("   Testing batch processing...")
        start_time = time.time()

        # Batch process 50 users
        user_ids = list(range(50))
        results = await self.service.batch_process_users(user_ids)

        duration = time.time() - start_time
        avg_time = (duration / 50) * 1000
        print(f"   ✅ Batch processing: {avg_time:.2f}ms average per user")

    async def _test_websocket_broadcast(self):
        """Test WebSocket broadcasting"""
        print("   Testing WebSocket broadcast...")
        start_time = time.time()

        # Broadcast message to channel
        await self.service.websocket_broadcast("updates", {"type": "test", "data": "performance test"})

        duration = time.time() - start_time
        print(f"   ✅ WebSocket broadcast: {duration * 1000:.2f}ms")

    async def _generate_performance_report(self):
        """Generate comprehensive performance report"""
        print("\n📊 Generating Performance Report...")
        print("=" * 60)

        # Get system performance report
        report = get_performance_report()

        # Print summary
        print(f"📈 Performance Summary:")
        print(f"   Total functions profiled: {report['summary']['total_functions_profiled']}")
        print(f"   Total metrics collected: {report['summary']['total_metrics']}")
        print(f"   Active alerts: {report['summary']['active_alerts']}")

        # Print top slow functions
        if report['top_slow_functions']:
            print(f"\n🐌 Top Slow Functions:")
            for i, func in enumerate(report['top_slow_functions'][:5], 1):
                print(f"   {i}. {func['name']}: {func['avg_time_ms']:.2f}ms avg")

        # Print recent alerts
        if report['recent_alerts']:
            print(f"\n🚨 Recent Alerts:")
            for alert in report['recent_alerts'][:3]:
                print(f"   {alert['level'].upper()}: {alert['message']}")

        # Print system metrics
        print(f"\n💻 System Metrics:")
        for name, metric in report['system_metrics'].items():
            print(f"   {name}: {metric['value']:.2f} {metric['unit']}")

        # Print connection pool stats
        print(f"\n🔗 Connection Pool Stats:")
        pool_stats = connection_pool_manager.get_all_stats()
        for pool_name, stats in pool_stats.items():
            print(f"   {pool_name}: {stats['active_connections']} active, "
                  f"{stats['pool_efficiency']:.1f}% efficiency")

        # Print memory stats
        print(f"\n🧠 Memory Stats:")
        memory_report = memory_manager.get_memory_report()
        memory_metrics = memory_report['current_metrics']
        print(f"   Process memory: {memory_metrics['process_memory_mb']:.1f}MB")
        print(f"   Memory pressure: {memory_metrics['memory_pressure']}")
        print(f"   Objects tracked: {memory_report['leak_detection']['tracked_objects']}")

        # Print async processor stats
        print(f"\n⚡ Async Processor Stats:")
        async_stats = async_processor.get_performance_stats()
        print(f"   Tasks completed: {async_stats['completed_tasks']}")
        print(f"   Tasks per second: {async_stats['tasks_per_second']:.1f}")
        print(f"   Worker utilization: {async_stats['worker_utilization']:.1f}%")

        print("=" * 60)

# Main execution function
async def main():
    """Main demonstration function"""
    print("🎯 DMLogn8n Real-time Performance Optimization Demo")
    print("=" * 60)

    # Initialize performance system
    setup = DMLogn8nPerformanceSetup()
    await setup.initialize()

    try:
        # Run performance tests
        monitor = PerformanceMonitor()
        await monitor.run_performance_test()

        # Keep system running for demonstration
        print("\n⏰ Performance optimization system running...")
        print("   Press Ctrl+C to stop")

        # Simulate some ongoing work
        for i in range(30):  # Run for 30 seconds
            await asyncio.sleep(1)
            if i % 10 == 0:  # Report every 10 seconds
                print(f"   System running... ({i+1}/30s)")

    except KeyboardInterrupt:
        print("\n👋 Shutting down...")

    finally:
        # Shutdown performance system
        await setup.shutdown()

if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())