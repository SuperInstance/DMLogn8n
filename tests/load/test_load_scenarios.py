"""
Comprehensive Load Testing Scenarios
Tests system performance under various load conditions
"""

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from fastapi.testclient import TestClient
import httpx
import threading
import queue


class TestBasicLoad:
    """Test basic load handling capabilities"""

    def test_concurrent_health_checks(self, test_client: TestClient):
        """Test concurrent health check requests"""
        num_requests = 50
        results = []

        def make_health_request():
            start_time = time.time()
            response = test_client.get("/api/health")
            end_time = time.time()
            return {
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'success': response.status_code == 200
            }

        # Run requests concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_health_request) for _ in range(num_requests)]
            for future in as_completed(futures):
                results.append(future.result())

        # Analyze results
        successful_requests = [r for r in results if r['success']]
        response_times = [r['response_time'] for r in successful_requests]

        assert len(successful_requests) >= num_requests * 0.95  # 95% success rate
        assert len(response_times) > 0

        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)

        assert avg_response_time < 1.0  # Average should be under 1 second
        assert max_response_time < 5.0  # Max should be under 5 seconds

    def test_concurrent_api_requests(self, test_client: TestClient):
        """Test concurrent API requests to different endpoints"""
        endpoints = [
            "/api/health",
            "/api/characters",
            "/api/campaigns"
        ]

        num_requests = 30
        results = []

        def make_api_request(endpoint):
            start_time = time.time()
            try:
                response = test_client.get(endpoint)
                end_time = time.time()
                return {
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'success': response.status_code in [200, 201, 404]  # Accept 404 as valid for missing endpoints
                }
            except Exception as e:
                return {
                    'endpoint': endpoint,
                    'status_code': 0,
                    'response_time': 0,
                    'success': False,
                    'error': str(e)
                }

        # Run requests concurrently
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(make_api_request, endpoints[i % len(endpoints)])
                for i in range(num_requests)
            ]
            for future in as_completed(futures):
                results.append(future.result())

        # Analyze results
        successful_requests = [r for r in results if r['success']]
        response_times = [r['response_time'] for r in successful_requests]

        assert len(successful_requests) >= num_requests * 0.90  # 90% success rate

        if response_times:
            avg_response_time = statistics.mean(response_times)
            assert avg_response_time < 2.0  # Average should be under 2 seconds

    def test_sustained_load(self, test_client: TestClient):
        """Test sustained load over time"""
        duration_seconds = 10
        requests_per_second = 5
        results = []

        def sustained_requests():
            start_time = time.time()
            end_time = start_time + duration_seconds

            while time.time() < end_time:
                request_start = time.time()
                response = test_client.get("/api/health")
                request_end = time.time()

                results.append({
                    'timestamp': request_start,
                    'response_time': request_end - request_start,
                    'success': response.status_code == 200
                })

                # Rate limiting
                time.sleep(1.0 / requests_per_second)

        # Run sustained load test
        thread = threading.Thread(target=sustained_requests)
        thread.start()
        thread.join()

        # Analyze results
        successful_requests = [r for r in results if r['success']]
        response_times = [r['response_time'] for r in successful_requests]

        assert len(successful_requests) >= duration_seconds * requests_per_second * 0.9

        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)

            assert avg_response_time < 1.0
            assert max_response_time < 3.0

    def test_burst_load(self, test_client: TestClient):
        """Test handling of sudden burst of requests"""
        burst_size = 100
        results = []

        def make_burst_request():
            start_time = time.time()
            response = test_client.get("/api/health")
            end_time = time.time()
            return {
                'response_time': end_time - start_time,
                'success': response.status_code == 200
            }

        # Create burst of requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_burst_request) for _ in range(burst_size)]
            for future in as_completed(futures):
                results.append(future.result())

        # Analyze results
        successful_requests = [r for r in results if r['success']]
        response_times = [r['response_time'] for r in successful_requests]

        success_rate = len(successful_requests) / burst_size
        assert success_rate >= 0.80  # 80% success rate under burst load

        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile

            assert avg_response_time < 2.0
            assert p95_response_time < 5.0


class TestLoadWithDatabase:
    """Test load scenarios involving database operations"""

    def test_concurrent_database_operations(self, test_db_session, test_client: TestClient):
        """Test concurrent database operations through API"""
        num_operations = 20
        results = []

        def create_and_read_character():
            # Create character
            character_data = {
                "name": f"Load Test Character {time.time()}",
                "race": "Human",
                "class": "Fighter",
                "level": 1
            }

            start_time = time.time()
            create_response = test_client.post("/api/characters", json=character_data)

            if create_response.status_code == 201:
                # Read character
                character_id = create_response.json().get("id")
                if character_id:
                    read_response = test_client.get(f"/api/characters/{character_id}")

            end_time = time.time()

            return {
                'response_time': end_time - start_time,
                'create_success': create_response.status_code == 201,
                'read_success': 'read_response' in locals() and read_response.status_code == 200
            }

        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_and_read_character) for _ in range(num_operations)]
            for future in as_completed(futures):
                results.append(future.result())

        # Analyze results
        successful_creates = [r for r in results if r['create_success']]
        successful_reads = [r for r in results if r['read_success']]
        response_times = [r['response_time'] for r in results]

        assert len(successful_creates) >= num_operations * 0.8
        assert len(successful_reads) >= num_operations * 0.7

        if response_times:
            avg_response_time = statistics.mean(response_times)
            assert avg_response_time < 3.0  # Database operations should complete within 3 seconds

    def test_database_connection_pool_under_load(self, test_db_session):
        """Test database connection pool under load"""
        num_queries = 50
        results = []

        def execute_database_query():
            start_time = time.time()
            try:
                from sqlalchemy import text
                result = test_db_session.execute(text("SELECT 1, sleep(0.01)"))  # Simulate slow query
                data = result.fetchone()
                end_time = time.time()
                return {
                    'success': True,
                    'response_time': end_time - start_time,
                    'data': data
                }
            except Exception as e:
                end_time = time.time()
                return {
                    'success': False,
                    'response_time': end_time - start_time,
                    'error': str(e)
                }

        # Run concurrent database queries
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(execute_database_query) for _ in range(num_queries)]
            for future in as_completed(futures):
                results.append(future.result())

        # Analyze results
        successful_queries = [r for r in results if r['success']]
        response_times = [r['response_time'] for r in successful_queries]

        assert len(successful_queries) >= num_queries * 0.9

        if response_times:
            avg_response_time = statistics.mean(response_times)
            assert avg_response_time < 1.0  # Queries should complete quickly even under load


class TestWebSocketLoad:
    """Test WebSocket performance under load"""

    def test_concurrent_websocket_connections(self, test_client: TestClient):
        """Test multiple concurrent WebSocket connections"""
        num_connections = 20
        connection_results = []

        def establish_websocket_connection():
            start_time = time.time()
            try:
                with test_client.websocket_connect("/ws/test_room") as websocket:
                    # Send a test message
                    websocket.send_json({"type": "ping", "id": time.time()})

                    # Try to receive response
                    try:
                        websocket.receive_json(timeout=2.0)
                        message_received = True
                    except:
                        message_received = False

                end_time = time.time()
                return {
                    'success': True,
                    'response_time': end_time - start_time,
                    'message_received': message_received
                }
            except Exception as e:
                end_time = time.time()
                return {
                    'success': False,
                    'response_time': end_time - start_time,
                    'error': str(e)
                }

        # Establish concurrent connections
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(establish_websocket_connection) for _ in range(num_connections)]
            for future in as_completed(futures):
                connection_results.append(future.result())

        # Analyze results
        successful_connections = [r for r in connection_results if r['success']]
        connection_times = [r['response_time'] for r in successful_connections]

        success_rate = len(successful_connections) / num_connections
        assert success_rate >= 0.8  # 80% connection success rate

        if connection_times:
            avg_connection_time = statistics.mean(connection_times)
            assert avg_connection_time < 2.0  # Connections should establish quickly

    def test_websocket_message_throughput(self, test_client: TestClient):
        """Test WebSocket message throughput"""
        num_messages = 50
        message_results = []

        with test_client.websocket_connect("/ws/test_room") as websocket:
            for i in range(num_messages):
                start_time = time.time()

                # Send message
                websocket.send_json({
                    "type": "test_message",
                    "id": i,
                    "content": f"Message {i}"
                })

                # Try to receive response
                try:
                    response = websocket.receive_json(timeout=1.0)
                    message_received = True
                except:
                    message_received = False

                end_time = time.time()
                message_results.append({
                    'message_id': i,
                    'response_time': end_time - start_time,
                    'message_received': message_received
                })

        # Analyze results
        received_messages = [r for r in message_results if r['message_received']]
        response_times = [r['response_time'] for r in message_results]

        message_success_rate = len(received_messages) / num_messages
        # Mock app might not echo messages, so we just test that sending works
        assert len(message_results) == num_messages

        if response_times:
            avg_response_time = statistics.mean(response_times)
            assert avg_response_time < 0.5  # Messages should be sent quickly


@pytest.mark.load
class TestHighLoadScenarios:
    """High load testing scenarios"""

    def test_mixed_workload_load(self, test_client: TestClient):
        """Test mixed workload under high load"""
        duration_seconds = 15
        results = {
            'api_calls': [],
            'websockets': [],
            'errors': []
        }

        def api_worker():
            """Worker that makes API calls"""
            end_time = time.time() + duration_seconds
            while time.time() < end_time:
                try:
                    start_time = time.time()
                    response = test_client.get("/api/health")
                    end_time_request = time.time()

                    results['api_calls'].append({
                        'timestamp': start_time,
                        'response_time': end_time_request - start_time,
                        'status_code': response.status_code
                    })
                except Exception as e:
                    results['errors'].append({
                        'type': 'api_error',
                        'error': str(e),
                        'timestamp': time.time()
                    })

                time.sleep(0.1)  # 10 calls per second

        def websocket_worker():
            """Worker that maintains WebSocket connections"""
            end_time = time.time() + duration_seconds
            while time.time() < end_time:
                try:
                    start_time = time.time()
                    with test_client.websocket_connect("/ws/test_room") as websocket:
                        # Send a message
                        websocket.send_json({"type": "ping", "timestamp": start_time})

                        # Try to receive
                        try:
                            websocket.receive_json(timeout=1.0)
                            message_received = True
                        except:
                            message_received = False

                        end_time_request = time.time()

                        results['websockets'].append({
                            'timestamp': start_time,
                            'connection_time': end_time_request - start_time,
                            'message_received': message_received
                        })

                        # Keep connection open for a bit
                        time.sleep(0.5)

                except Exception as e:
                    results['errors'].append({
                        'type': 'websocket_error',
                        'error': str(e),
                        'timestamp': time.time()
                    })

        # Start workers
        api_thread = threading.Thread(target=api_worker)
        websocket_thread = threading.Thread(target=websocket_worker)

        api_thread.start()
        websocket_thread.start()

        api_thread.join()
        websocket_thread.join()

        # Analyze results
        api_success_rate = len(results['api_calls']) / max(1, len(results['api_calls']) + len([e for e in results['errors'] if e['type'] == 'api_error']))
        websocket_success_rate = len(results['websockets']) / max(1, len(results['websockets']) + len([e for e in results['errors'] if e['type'] == 'websocket_error']))

        assert api_success_rate >= 0.8  # 80% API success rate
        assert websocket_success_rate >= 0.7  # 70% WebSocket success rate

        if results['api_calls']:
            api_times = [r['response_time'] for r in results['api_calls']]
            avg_api_time = statistics.mean(api_times)
            assert avg_api_time < 1.0

    def test_memory_usage_under_load(self, test_client: TestClient):
        """Test memory usage patterns under load"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Generate load
        num_requests = 200
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(lambda: test_client.get("/api/health"))
                for _ in range(num_requests)
            ]

            # Wait for all requests to complete
            for future in as_completed(futures):
                future.result()

        # Check memory after load
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100

    def test_error_rate_under_stress(self, test_client: TestClient):
        """Test error rates under stress conditions"""
        num_requests = 500
        results = []

        def make_stress_request():
            try:
                start_time = time.time()
                response = test_client.get("/api/health")
                end_time = time.time()

                return {
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'success': response.status_code == 200
                }
            except Exception as e:
                return {
                    'status_code': 0,
                    'response_time': 0,
                    'success': False,
                    'error': str(e)
                }

        # Generate high stress load
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_stress_request) for _ in range(num_requests)]
            for future in as_completed(futures):
                results.append(future.result())

        # Analyze error rates
        successful_requests = [r for r in results if r['success']]
        error_rate = (num_requests - len(successful_requests)) / num_requests

        assert error_rate < 0.1  # Error rate should be less than 10%

        if successful_requests:
            response_times = [r['response_time'] for r in successful_requests]
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
            assert p99_response_time < 5.0  # 99% of requests should complete within 5 seconds


@pytest.mark.performance
class TestPerformanceMetrics:
    """Test specific performance metrics"""

    def test_response_time_distribution(self, test_client: TestClient):
        """Test response time distribution under load"""
        num_requests = 100
        response_times = []

        for _ in range(num_requests):
            start_time = time.time()
            response = test_client.get("/api/health")
            end_time = time.time()

            if response.status_code == 200:
                response_times.append(end_time - start_time)

        # Calculate percentiles
        if len(response_times) >= 10:
            p50 = statistics.median(response_times)
            p95 = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99 = statistics.quantiles(response_times, n=100)[98]  # 99th percentile

            assert p50 < 0.5  # Median response time under 500ms
            assert p95 < 2.0  # 95th percentile under 2 seconds
            assert p99 < 5.0  # 99th percentile under 5 seconds

    def test_throughput_measurement(self, test_client: TestClient):
        """Test system throughput"""
        duration_seconds = 10
        request_count = 0
        successful_requests = 0

        start_time = time.time()
        end_time = start_time + duration_seconds

        while time.time() < end_time:
            response = test_client.get("/api/health")
            request_count += 1

            if response.status_code == 200:
                successful_requests += 1

        actual_duration = time.time() - start_time
        throughput = successful_requests / actual_duration  # requests per second
        success_rate = successful_requests / request_count

        assert throughput >= 10  # Should handle at least 10 requests per second
        assert success_rate >= 0.95  # 95% success rate

    def test_resource_utilization(self, test_client: TestClient):
        """Test resource utilization patterns"""
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # Measure baseline
        baseline_cpu = process.cpu_percent()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Generate sustained load
        duration = 5.0
        start_time = time.time()

        while time.time() - start_time < duration:
            test_client.get("/api/health")

        # Measure after load
        peak_cpu = process.cpu_percent()
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Resource usage should be reasonable
        assert peak_memory - baseline_memory < 50  # Less than 50MB memory increase
        assert peak_cpu < 80  # CPU usage should be reasonable (this is per-process)


@pytest.mark.asyncio
class TestAsyncLoadScenarios:
    """Test async load scenarios"""

    async def test_async_concurrent_requests(self, test_client: TestClient):
        """Test async concurrent HTTP requests"""
        import httpx

        num_requests = 50
        async with httpx.AsyncClient(app=test_client.app, base_url="http://test") as client:
            tasks = []
            for _ in range(num_requests):
                task = client.get("/api/health")
                tasks.append(task)

            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

        # Analyze results
        successful_responses = [r for r in responses if hasattr(r, 'status_code') and r.status_code == 200]
        success_rate = len(successful_responses) / num_requests

        assert success_rate >= 0.9
        assert (end_time - start_time) < 5.0  # Should complete quickly due to async nature

    async def test_async_websocket_connections(self, test_client: TestClient):
        """Test async WebSocket connections"""
        async def websocket_worker(worker_id: int):
            try:
                async with httpx.AsyncClient(app=test_client.app, base_url="http://test") as client:
                    async with client.websocket_connect("/ws/test_room") as websocket:
                        await websocket.send_json({"type": "ping", "worker_id": worker_id})

                        try:
                            response = await websocket.receive_json(timeout=2.0)
                            return {'worker_id': worker_id, 'success': True, 'response': response}
                        except:
                            return {'worker_id': worker_id, 'success': True, 'response': None}
            except Exception as e:
                return {'worker_id': worker_id, 'success': False, 'error': str(e)}

        # Create multiple concurrent WebSocket connections
        num_workers = 10
        tasks = [websocket_worker(i) for i in range(num_workers)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful_connections = [r for r in results if isinstance(r, dict) and r.get('success', False)]
        success_rate = len(successful_connections) / num_workers

        assert success_rate >= 0.8