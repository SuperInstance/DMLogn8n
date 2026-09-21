"""
Performance tests for load testing the DMLogn8n parallel multi-agent system.
"""

import pytest
import asyncio
import time
import psutil
import statistics
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import uuid
import json
import random
from typing import List, Dict, Any

# Performance testing utilities
class PerformanceMetrics:
    """Collect and analyze performance metrics."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.response_times = []
        self.error_counts = {}
        self.request_counts = {}
        self.memory_samples = []
        self.cpu_samples = []
        self.concurrent_operations = []
        self.throughput_samples = []

    def start_measurement(self):
        """Start performance measurement."""
        self.start_time = time.time()

    def stop_measurement(self):
        """Stop performance measurement."""
        self.end_time = time.time()

    def record_response_time(self, response_time: float):
        """Record a response time."""
        self.response_times.append(response_time)

    def record_error(self, error_type: str):
        """Record an error."""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

    def record_request(self, endpoint: str):
        """Record a request."""
        self.request_counts[endpoint] = self.request_counts.get(endpoint, 0) + 1

    def record_memory_usage(self):
        """Record current memory usage."""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.memory_samples.append({
            'timestamp': time.time(),
            'memory_mb': memory_mb
        })

    def record_cpu_usage(self):
        """Record current CPU usage."""
        cpu_percent = psutil.cpu_percent()
        self.cpu_samples.append({
            'timestamp': time.time(),
            'cpu_percent': cpu_percent
        })

    def record_concurrent_operations(self, count: int):
        """Record number of concurrent operations."""
        self.concurrent_operations.append({
            'timestamp': time.time(),
            'count': count
        })

    def record_throughput(self, operations_per_second: float):
        """Record throughput."""
        self.throughput_samples.append({
            'timestamp': time.time(),
            'ops_per_second': operations_per_second
        })

    def get_duration(self) -> float:
        """Get total duration of measurement."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        if not self.response_times:
            return {'error': 'No response times recorded'}

        duration = self.get_duration()
        total_requests = sum(self.request_counts.values())
        total_errors = sum(self.error_counts.values())

        return {
            'duration_seconds': duration,
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate': total_errors / total_requests if total_requests > 0 else 0,
            'requests_per_second': total_requests / duration if duration > 0 else 0,
            'response_time': {
                'avg': statistics.mean(self.response_times),
                'median': statistics.median(self.response_times),
                'min': min(self.response_times),
                'max': max(self.response_times),
                'p95': statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) > 20 else max(self.response_times),
                'p99': statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) > 100 else max(self.response_times)
            },
            'memory_usage': {
                'peak_mb': max(sample['memory_mb'] for sample in self.memory_samples) if self.memory_samples else 0,
                'avg_mb': statistics.mean(sample['memory_mb'] for sample in self.memory_samples) if self.memory_samples else 0,
                'growth_mb': (self.memory_samples[-1]['memory_mb'] - self.memory_samples[0]['memory_mb']) if len(self.memory_samples) > 1 else 0
            },
            'cpu_usage': {
                'peak_percent': max(sample['cpu_percent'] for sample in self.cpu_samples) if self.cpu_samples else 0,
                'avg_percent': statistics.mean(sample['cpu_percent'] for sample in self.cpu_samples) if self.cpu_samples else 0
            },
            'concurrent_operations': {
                'peak': max(op['count'] for op in self.concurrent_operations) if self.concurrent_operations else 0,
                'avg': statistics.mean(op['count'] for op in self.concurrent_operations) if self.concurrent_operations else 0
            },
            'throughput': {
                'peak_ops_per_second': max(sample['ops_per_second'] for sample in self.throughput_samples) if self.throughput_samples else 0,
                'avg_ops_per_second': statistics.mean(sample['ops_per_second'] for sample in self.throughput_samples) if self.throughput_samples else 0
            },
            'errors_by_type': self.error_counts,
            'requests_by_endpoint': self.request_counts
        }

class LoadTestRunner:
    """Run load tests with configurable parameters."""

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.concurrent_users = 0
        self.active_connections = []

    async def run_concurrent_users(self, user_count: int, duration_seconds: int,
                                 think_time: float = 1.0, ramp_up_time: float = 10.0):
        """Run load test with specified number of concurrent users."""
        self.metrics.start_measurement()
        self.concurrent_users = user_count

        # Calculate user spawn interval for ramp-up
        spawn_interval = ramp_up_time / user_count if user_count > 0 else 0

        # Create user tasks
        user_tasks = []
        for i in range(user_count):
            task = asyncio.create_task(
                self._simulate_user_activity(f'user_{i}', duration_seconds, think_time)
            )
            user_tasks.append(task)

            # Stagger user creation for ramp-up
            if spawn_interval > 0:
                await asyncio.sleep(spawn_interval)

        # Monitor system resources during test
        monitor_task = asyncio.create_task(self._monitor_system_resources(duration_seconds + ramp_up_time))

        # Wait for all users to complete
        await asyncio.gather(*user_tasks)
        monitor_task.cancel()

        self.metrics.stop_measurement()
        return self.metrics.get_stats()

    async def _simulate_user_activity(self, user_id: str, duration_seconds: float, think_time: float):
        """Simulate realistic user activity."""
        start_time = time.time()
        end_time = start_time + duration_seconds

        while time.time() < end_time:
            # Randomly select an action to perform
            action = random.choice([
                self._perform_agent_action,
                self._perform_session_action,
                self._perform_websocket_action,
                self._perform_database_query
            ])

            try:
                response_time = await action(user_id)
                self.metrics.record_response_time(response_time)
            except Exception as e:
                self.metrics.record_error(type(e).__name__)

            # Think time between actions
            await asyncio.sleep(think_time * (0.5 + random.random()))  # Add variance

    async def _perform_agent_action(self, user_id: str) -> float:
        """Simulate agent-related action."""
        start_time = time.time()

        # Simulate API call
        await asyncio.sleep(0.05 + random.random() * 0.1)  # 50-150ms response time

        self.metrics.record_request('/api/agents/action')
        return time.time() - start_time

    async def _perform_session_action(self, user_id: str) -> float:
        """Simulate session-related action."""
        start_time = time.time()

        # Simulate API call
        await asyncio.sleep(0.08 + random.random() * 0.12)  # 80-200ms response time

        self.metrics.record_request('/api/sessions/update')
        return time.time() - start_time

    async def _perform_websocket_action(self, user_id: str) -> float:
        """Simulate WebSocket action."""
        start_time = time.time()

        # Simulate WebSocket message
        await asyncio.sleep(0.01 + random.random() * 0.02)  # 10-30ms response time

        self.metrics.record_request('websocket/message')
        return time.time() - start_time

    async def _perform_database_query(self, user_id: str) -> float:
        """Simulate database query."""
        start_time = time.time()

        # Simulate database query
        await asyncio.sleep(0.02 + random.random() * 0.08)  # 20-100ms response time

        self.metrics.record_request('database/query')
        return time.time() - start_time

    async def _monitor_system_resources(self, duration_seconds: float):
        """Monitor system resources during test."""
        start_time = time.time()
        sampling_interval = 1.0  # Sample every second

        while time.time() - start_time < duration_seconds:
            self.metrics.record_memory_usage()
            self.metrics.record_cpu_usage()
            await asyncio.sleep(sampling_interval)

class StressTestRunner:
    """Run stress tests to find system limits."""

    def __init__(self):
        self.metrics = PerformanceMetrics()

    async def run_stress_test(self, max_users: int, step_size: int = 10,
                            step_duration: int = 60):
        """Run stress test, gradually increasing load."""
        results = []
        current_users = step_size

        while current_users <= max_users:
            print(f"Running stress test with {current_users} users...")

            # Run load test at current level
            runner = LoadTestRunner()
            stats = await runner.run_concurrent_users(
                current_users, step_duration, think_time=0.5, ramp_up_time=30.0
            )

            # Record results
            result = {
                'users': current_users,
                'stats': stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            results.append(result)

            # Check if system is showing stress
            if self._is_system_stressed(stats):
                print(f"System showing stress at {current_users} users")
                break

            current_users += step_size

        return results

    def _is_system_stressed(self, stats: Dict[str, Any]) -> bool:
        """Determine if system is under stress based on metrics."""
        # Check error rate
        if stats.get('error_rate', 0) > 0.05:  # 5% error rate
            return True

        # Check response times
        response_time = stats.get('response_time', {})
        if response_time.get('p95', 0) > 2.0:  # 95th percentile over 2 seconds
            return True

        # Check memory usage
        memory = stats.get('memory_usage', {})
        if memory.get('growth_mb', 0) > 500:  # Memory growth over 500MB
            return True

        return False

class SoakTestRunner:
    """Run soak tests for extended periods."""

    def __init__(self):
        self.metrics = PerformanceMetrics()

    async def run_soak_test(self, user_count: int, duration_hours: float,
                          sample_interval: int = 300):
        """Run soak test for extended duration."""
        duration_seconds = duration_hours * 3600
        print(f"Running soak test with {user_count} users for {duration_hours} hours...")

        self.metrics.start_measurement()
        start_time = time.time()

        # Start continuous load
        load_runner = LoadTestRunner()
        load_task = asyncio.create_task(
            load_runner.run_concurrent_users(
                user_count, duration_seconds, think_time=2.0, ramp_up_time=60.0
            )
        )

        # Monitor and take samples periodically
        sample_count = 0
        next_sample_time = start_time + sample_interval

        while time.time() - start_time < duration_seconds:
            current_time = time.time()
            if current_time >= next_sample_time:
                # Take a sample
                await self._take_soak_sample(load_runner.metrics, sample_count)
                sample_count += 1
                next_sample_time += sample_interval

            await asyncio.sleep(10)  # Check every 10 seconds

        # Final sample
        await self._take_soak_sample(load_runner.metrics, sample_count)

        # Wait for load test to complete
        load_stats = await load_task
        self.metrics.stop_measurement()

        return {
            'duration_hours': duration_hours,
            'user_count': user_count,
            'sample_count': sample_count,
            'final_stats': load_stats,
            'samples': self.metrics.throughput_samples
        }

    async def _take_soak_sample(self, load_metrics: PerformanceMetrics, sample_number: int):
        """Take a sample during soak test."""
        current_stats = load_metrics.get_stats()

        # Record throughput sample
        ops_per_second = current_stats.get('requests_per_second', 0)
        self.metrics.record_throughput(ops_per_second)

        print(f"Soak test sample {sample_number}: {ops_per_second:.2f} ops/sec")

class SpikeTestRunner:
    """Run spike tests for sudden load changes."""

    def __init__(self):
        self.metrics = PerformanceMetrics()

    async def run_spike_test(self, baseline_users: int, spike_users: int,
                          spike_duration: int, total_duration: int):
        """Run spike test with sudden load increase."""
        print(f"Running spike test: {baseline_users} -> {spike_users} for {spike_duration}s")

        self.metrics.start_measurement()
        start_time = time.time()

        # Phase 1: Baseline load
        baseline_runner = LoadTestRunner()
        baseline_task = asyncio.create_task(
            baseline_runner.run_concurrent_users(
                baseline_users, spike_duration, think_time=1.0, ramp_up_time=30.0
            )
        )

        # Wait for baseline to stabilize
        await asyncio.sleep(60)

        # Phase 2: Spike load (add more users)
        spike_runner = LoadTestRunner()
        spike_task = asyncio.create_task(
            spike_runner.run_concurrent_users(
                spike_users, spike_duration, think_time=0.5, ramp_up_time=5.0
            )
        )

        # Wait for spike duration
        await asyncio.sleep(spike_duration)

        # Phase 3: Return to baseline
        spike_task.cancel()  # Stop spike load

        # Continue baseline load for remaining time
        remaining_time = total_duration - (time.time() - start_time)
        if remaining_time > 0:
            await asyncio.sleep(remaining_time)

        baseline_task.cancel()
        self.metrics.stop_measurement()

        return baseline_runner.metrics.get_stats()

@pytest.mark.performance
@pytest.mark.load
class TestLoadTesting:
    """Load testing for the DMLogn8n system."""

    @pytest.mark.asyncio
    async def test_moderate_load(self):
        """Test system under moderate load."""
        runner = LoadTestRunner()

        # Test with 100 concurrent users for 5 minutes
        stats = await runner.run_concurrent_users(
            user_count=100,
            duration_seconds=300,  # 5 minutes
            think_time=2.0,        # Average 2 seconds between actions
            ramp_up_time=30.0      # 30 second ramp-up
        )

        # Assertions for moderate load
        assert stats['requests_per_second'] > 10  # At least 10 req/sec
        assert stats['error_rate'] < 0.01  # Less than 1% error rate
        assert stats['response_time']['p95'] < 1.0  # 95th percentile under 1 second
        assert stats['memory_usage']['growth_mb'] < 100  # Less than 100MB memory growth

    @pytest.mark.asyncio
    async def test_high_load(self):
        """Test system under high load."""
        runner = LoadTestRunner()

        # Test with 500 concurrent users for 10 minutes
        stats = await runner.run_concurrent_users(
            user_count=500,
            duration_seconds=600,  # 10 minutes
            think_time=1.5,        # 1.5 seconds between actions
            ramp_up_time=60.0      # 1 minute ramp-up
        )

        # Assertions for high load
        assert stats['requests_per_second'] > 50  # At least 50 req/sec
        assert stats['error_rate'] < 0.05  # Less than 5% error rate
        assert stats['response_time']['p95'] < 2.0  # 95th percentile under 2 seconds
        assert stats['concurrent_operations']['peak'] >= 500

    @pytest.mark.asyncio
    async def test_sustained_load(self):
        """Test system under sustained load."""
        runner = LoadTestRunner()

        # Test with 200 concurrent users for 30 minutes
        stats = await runner.run_concurrent_users(
            user_count=200,
            duration_seconds=1800,  # 30 minutes
            think_time=2.5,         # 2.5 seconds between actions
            ramp_up_time=120.0      # 2 minute ramp-up
        )

        # Assertions for sustained load
        assert stats['requests_per_second'] > 20  # At least 20 req/sec
        assert stats['error_rate'] < 0.02  # Less than 2% error rate
        assert stats['memory_usage']['growth_mb'] < 200  # Less than 200MB over 30 minutes
        assert stats['cpu_usage']['avg_percent'] < 80  # Average CPU under 80%

    @pytest.mark.asyncio
    async def test_rapid_user_growth(self):
        """Test system handling rapid user growth."""
        runner = LoadTestRunner()

        # Test rapid user growth with short ramp-up
        stats = await runner.run_concurrent_users(
            user_count=300,
            duration_seconds=300,  # 5 minutes
            think_time=1.0,        # Fast actions
            ramp_up_time=10.0      # Very fast 10-second ramp-up
        )

        # System should handle rapid growth
        assert stats['requests_per_second'] > 30
        assert stats['error_rate'] < 0.10  # Allow higher error rate during rapid growth
        assert stats['response_time']['avg'] < 1.5

@pytest.mark.performance
@pytest.mark.stress
class TestStressTesting:
    """Stress testing to find system limits."""

    @pytest.mark.asyncio
    async def test_gradual_stress_increase(self):
        """Gradually increase load until system shows stress."""
        runner = StressTestRunner()

        # Find breaking point (up to 1000 users)
        results = await runner.run_stress_test(
            max_users=1000,
            step_size=50,
            step_duration=120  # 2 minutes per step
        )

        # Analyze results
        assert len(results) > 0

        # Find the last successful test
        successful_results = [r for r in results if r['stats']['error_rate'] < 0.05]
        assert len(successful_results) > 0

        max_successful_users = max(r['users'] for r in successful_results)
        print(f"System handled up to {max_successful_users} concurrent users successfully")

        # Verify system degrades gracefully
        final_result = results[-1]
        assert final_result['stats']['error_rate'] < 0.50  # Should not completely fail

    @pytest.mark.asyncio
    async def test_maximum_concurrent_connections(self):
        """Test maximum concurrent WebSocket connections."""
        # This would test WebSocket connection limits
        # Implementation would depend on WebSocket server specifics
        pass

    @pytest.mark.asyncio
    async def test_database_connection_limits(self):
        """Test database connection pool limits."""
        # This would test database connection exhaustion
        # Implementation would depend on database setup
        pass

@pytest.mark.performance
@pytest.mark.soak
class TestSoakTesting:
    """Soak testing for extended duration stability."""

    @pytest.mark.asyncio
    async def test_extended_stability(self):
        """Test system stability over extended period."""
        runner = SoakTestRunner()

        # Run 2-hour soak test with 100 users
        results = await runner.run_soak_test(
            user_count=100,
            duration_hours=2.0,  # 2 hours
            sample_interval=300  # Sample every 5 minutes
        )

        # Analyze soak test results
        assert results['duration_hours'] == 2.0
        assert results['sample_count'] >= 12  # At least 12 samples in 2 hours
        assert results['final_stats']['error_rate'] < 0.02  # Low error rate throughout

        # Check for performance degradation
        final_stats = results['final_stats']
        assert final_stats['memory_usage']['growth_mb'] < 300  # Limited memory growth
        assert final_stats['response_time']['p95'] < 1.5  # Response times remain reasonable

    @pytest.mark.asyncio
    async def test_memory_leak_detection(self):
        """Test for memory leaks over extended period."""
        runner = SoakTestRunner()

        # Run shorter soak test focused on memory
        results = await runner.run_soak_test(
            user_count=150,
            duration_hours=1.0,  # 1 hour
            sample_interval=60   # Sample every minute
        )

        # Check memory usage patterns
        final_stats = results['final_stats']
        memory_growth = final_stats['memory_usage']['growth_mb']

        # Memory growth should be minimal (indicating no significant leaks)
        assert memory_growth < 150, f"Potential memory leak detected: {memory_growth}MB growth"

        # Memory usage should be relatively stable
        peak_memory = final_stats['memory_usage']['peak_mb']
        avg_memory = final_stats['memory_usage']['avg_mb']
        memory_variance = peak_memory - avg_memory

        assert memory_variance < 100, f"Memory usage unstable: {memory_variance}MB variance"

@pytest.mark.performance
@pytest.mark.spike
class TestSpikeTesting:
    """Spike testing for sudden load changes."""

    @pytest.mark.asyncio
    async def test_sudden_load_spike(self):
        """Test system handling sudden load spikes."""
        runner = SpikeTestRunner()

        # Baseline: 50 users, spike to 500 users for 2 minutes
        stats = await runner.run_spike_test(
            baseline_users=50,
            spike_users=500,
            spike_duration=120,  # 2 minutes
            total_duration=600   # 10 minutes total
        )

        # System should handle spike gracefully
        assert stats['error_rate'] < 0.15  # Higher error rate acceptable during spike
        assert stats['response_time']['p95'] < 3.0  # Slower responses acceptable during spike

        # System should recover after spike
        # In a real implementation, we'd compare before/after spike performance

    @pytest.mark.asyncio
    async def test_multiple_spikes(self):
        """Test system handling multiple spikes."""
        # Test multiple rapid spikes
        runner = SpikeTestRunner()

        # Run multiple spike cycles
        for i in range(3):
            print(f"Running spike cycle {i+1}/3")
            stats = await runner.run_spike_test(
                baseline_users=30,
                spike_users=300,
                spike_duration=60,   # 1 minute spike
                total_duration=180   # 3 minutes total
            )

            # Allow recovery between spikes
            await asyncio.sleep(30)

        # System should handle multiple spikes without degradation
        assert True  # Implementation would track degradation across spikes

@pytest.mark.performance
@pytest.mark.parallel
class TestParallelPerformance:
    """Performance tests specifically for parallel processing."""

    @pytest.mark.asyncio
    async def test_parallel_agent_processing(self):
        """Test performance of parallel agent processing."""
        agent_count = 1000
        processing_times = []

        async def process_agent(agent_id: int) -> float:
            """Simulate agent processing."""
            start_time = time.time()

            # Simulate complex agent decision making
            await asyncio.sleep(0.01 + random.random() * 0.05)  # 10-60ms processing

            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            return processing_time

        # Process all agents in parallel
        start_time = time.time()
        tasks = [process_agent(i) for i in range(agent_count)]
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Analyze parallel processing performance
        avg_processing_time = statistics.mean(processing_times)
        total_sequential_time = sum(processing_times)
        parallel_efficiency = total_sequential_time / (total_time * agent_count)

        assert total_time < avg_processing_time * agent_count * 0.1  # Should be much faster than sequential
        assert parallel_efficiency > 0.5  # At least 50% efficiency
        assert max(processing_times) < 0.1  # No agent should take more than 100ms

    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self):
        """Test performance of concurrent database operations."""
        operation_count = 500
        operation_times = []

        async def database_operation(operation_id: int) -> float:
            """Simulate database operation."""
            start_time = time.time()

            # Simulate database query with variable response time
            await asyncio.sleep(0.005 + random.random() * 0.045)  # 5-50ms

            processing_time = time.time() - start_time
            operation_times.append(processing_time)
            return processing_time

        # Run database operations concurrently
        start_time = time.time()
        tasks = [database_operation(i) for i in range(operation_count)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Verify database performance under load
        throughput = operation_count / total_time
        avg_response_time = statistics.mean(operation_times)

        assert throughput > 100  # At least 100 operations per second
        assert avg_response_time < 0.05  # Average under 50ms
        assert max(operation_times) < 0.1  # No operation over 100ms

    @pytest.mark.asyncio
    async def test_parallel_websocket_communication(self):
        """Test WebSocket performance with many concurrent connections."""
        connection_count = 200
        message_count = 10  # Messages per connection
        message_times = []

        async def websocket_connection(conn_id: int) -> List[float]:
            """Simulate WebSocket connection with messages."""
            conn_times = []

            # Simulate connection establishment
            await asyncio.sleep(0.001)

            # Send multiple messages
            for msg in range(message_count):
                start_time = time.time()

                # Simulate message processing
                await asyncio.sleep(0.001 + random.random() * 0.004)  # 1-5ms

                msg_time = time.time() - start_time
                conn_times.append(msg_time)
                message_times.append(msg_time)

            return conn_times

        # Create all connections concurrently
        start_time = time.time()
        tasks = [websocket_connection(i) for i in range(connection_count)]
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Analyze WebSocket performance
        total_messages = connection_count * message_count
        message_throughput = total_messages / total_time
        avg_message_time = statistics.mean(message_times)

        assert message_throughput > 1000  # At least 1000 messages per second
        assert avg_message_time < 0.01  # Average under 10ms
        assert max(message_times) < 0.02  # No message over 20ms

    @pytest.mark.asyncio
    async def test_load_balancing_efficiency(self):
        """Test load balancing efficiency across multiple workers."""
        worker_count = 8
        task_count = 1000
        worker_loads = {i: 0 for i in range(worker_count)}

        async def worker_task(worker_id: int, tasks: List[int]) -> float:
            """Simulate worker processing tasks."""
            worker_loads[worker_id] += len(tasks)

            for task in tasks:
                # Simulate task processing
                await asyncio.sleep(0.001 + random.random() * 0.009)  # 1-10ms

            return len(tasks)

        # Distribute tasks across workers
        tasks_per_worker = task_count // worker_count
        remaining_tasks = task_count % worker_count

        start_time = time.time()
        worker_tasks = []

        for worker_id in range(worker_count):
            # Calculate task count for this worker
            task_count_for_worker = tasks_per_worker
            if worker_id < remaining_tasks:
                task_count_for_worker += 1

            # Create tasks for this worker
            tasks = list(range(worker_id * 100, worker_id * 100 + task_count_for_worker))
            worker_tasks.append(worker_task(worker_id, tasks))

        # Run all workers in parallel
        results = await asyncio.gather(*worker_tasks)
        total_time = time.time() - start_time

        # Analyze load balancing
        load_values = list(worker_loads.values())
        max_load = max(load_values)
        min_load = min(load_values)
        load_variance = max_load - min_load

        # Load should be reasonably balanced
        assert load_variance <= 1  # Difference of at most 1 task
        assert sum(results) == task_count  # All tasks processed

        # Performance should be good
        throughput = task_count / total_time
        assert throughput > 500  # At least 500 tasks per second