"""
Test utilities and helper functions for DMLogn8n testing.
"""

import asyncio
import time
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Union
import functools
import inspect
import logging
from contextlib import asynccontextmanager

# Configure test logging
test_logger = logging.getLogger('dmlogn8n_tests')
test_logger.setLevel(logging.INFO)

class TestTimer:
    """Context manager for timing test operations."""

    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = time.time()
        test_logger.info(f"Starting {self.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        test_logger.info(f"Completed {self.name} in {self.duration:.3f}s")

    def get_duration(self) -> float:
        """Get the duration of the timed operation."""
        return self.duration if self.duration is not None else 0.0

class AsyncTestTimer:
    """Async context manager for timing async test operations."""

    def __init__(self, name: str = "async_operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None

    async def __aenter__(self):
        self.start_time = time.time()
        test_logger.info(f"Starting {self.name}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        test_logger.info(f"Completed {self.name} in {self.duration:.3f}s")

    def get_duration(self) -> float:
        """Get the duration of the timed operation."""
        return self.duration if self.duration is not None else 0.0

class RetryHelper:
    """Helper for retrying test operations with backoff."""

    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor

    async def retry_async(self, func: Callable, *args, **kwargs) -> Any:
        """Retry an async function with exponential backoff."""
        last_exception = None
        delay = self.base_delay

        for attempt in range(1, self.max_attempts + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.max_attempts:
                    break

                test_logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s...")
                await asyncio.sleep(delay)
                delay *= self.backoff_factor

        raise last_exception

    def retry_sync(self, func: Callable, *args, **kwargs) -> Any:
        """Retry a synchronous function with exponential backoff."""
        last_exception = None
        delay = self.base_delay

        for attempt in range(1, self.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.max_attempts:
                    break

                test_logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s...")
                time.sleep(delay)
                delay *= self.backoff_factor

        raise last_exception

class AssertionHelper:
    """Helper methods for complex test assertions."""

    @staticmethod
    def assert_within_range(value: Union[int, float], min_val: Union[int, float],
                           max_val: Union[int, float], message: str = None):
        """Assert that a value is within the specified range."""
        assert min_val <= value <= max_val, message or f"Value {value} not in range [{min_val}, {max_val}]"

    @staticmethod
    def assert_close_to(value: Union[int, float], expected: Union[int, float],
                       tolerance: Union[int, float] = 0.1, message: str = None):
        """Assert that a value is close to the expected value within tolerance."""
        diff = abs(value - expected)
        assert diff <= tolerance, message or f"Value {value} not within {tolerance} of {expected} (diff: {diff})"

    @staticmethod
    def assert_list_contains_all(actual_list: List[Any], expected_items: List[Any], message: str = None):
        """Assert that all expected items are present in the actual list."""
        missing_items = [item for item in expected_items if item not in actual_list]
        assert not missing_items, message or f"Missing items in list: {missing_items}"

    @staticmethod
    def assert_dicts_match_subdict(actual_dict: Dict[str, Any], expected_subdict: Dict[str, Any],
                                  message: str = None):
        """Assert that actual dict contains all key-value pairs from expected subdict."""
        missing_keys = []
        mismatched_values = []

        for key, expected_value in expected_subdict.items():
            if key not in actual_dict:
                missing_keys.append(key)
            elif actual_dict[key] != expected_value:
                mismatched_values.append((key, actual_dict[key], expected_value))

        error_parts = []
        if missing_keys:
            error_parts.append(f"Missing keys: {missing_keys}")
        if mismatched_values:
            error_parts.append(f"Mismatched values: {mismatched_values}")

        assert not error_parts, message or f"Dictionary mismatch: {'; '.join(error_parts)}"

    @staticmethod
    def assert_timestamp_recent(timestamp: str, max_age_seconds: int = 60, message: str = None):
        """Assert that a timestamp is recent (within specified age)."""
        try:
            parsed_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            age_seconds = (datetime.utcnow() - parsed_time.replace(tzinfo=None)).total_seconds()
            assert age_seconds <= max_age_seconds, message or f"Timestamp {timestamp} is {age_seconds}s old (max: {max_age_seconds}s)"
        except Exception as e:
            raise AssertionError(f"Invalid timestamp format: {e}")

class MockResponse:
    """Mock HTTP response for testing."""

    def __init__(self, status_code: int = 200, data: Any = None, headers: Dict[str, str] = None):
        self.status_code = status_code
        self.data = data
        self.headers = headers or {}
        self.content = json.dumps(data).encode() if data else b''

    async def json(self):
        """Return JSON response data."""
        return self.data

    async def text(self):
        """Return text response data."""
        return json.dumps(self.data) if self.data else ''

    def raise_for_status(self):
        """Raise an exception if the response indicates an error."""
        if 400 <= self.status_code < 600:
            raise Exception(f"HTTP {self.status_code}: {self.data}")

class WebSocketTestHelper:
    """Helper for testing WebSocket functionality."""

    def __init__(self):
        self.messages = []
        self.connected = False

    async def connect(self, url: str):
        """Mock WebSocket connection."""
        self.connected = True
        test_logger.info(f"Connected to WebSocket: {url}")

    async def disconnect(self):
        """Mock WebSocket disconnection."""
        self.connected = False
        test_logger.info("Disconnected from WebSocket")

    async def send(self, event: str, data: Any):
        """Mock sending a WebSocket message."""
        if not self.connected:
            raise ConnectionError("WebSocket not connected")

        message = {
            'event': event,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.messages.append(message)
        test_logger.info(f"Sent WebSocket message: {event}")

    async def receive(self, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Mock receiving a WebSocket message."""
        if not self.messages:
            return None

        # Return oldest message
        message = self.messages.pop(0)
        test_logger.info(f"Received WebSocket message: {message['event']}")
        return message

    async def wait_for_message(self, event: str, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Wait for a specific event type."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            for i, message in enumerate(self.messages):
                if message['event'] == event:
                    return self.messages.pop(i)
            await asyncio.sleep(0.01)

        return None

    def clear_messages(self):
        """Clear all stored messages."""
        self.messages.clear()

class DatabaseTestHelper:
    """Helper for database-related testing."""

    @staticmethod
    async def assert_table_exists(db_connection, table_name: str):
        """Assert that a database table exists."""
        result = await db_connection.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
            table_name
        )
        assert result, f"Table {table_name} does not exist"

    @staticmethod
    async def assert_record_count(db_connection, table_name: str, expected_count: int,
                                 where_clause: str = None):
        """Assert the number of records in a table."""
        query = f"SELECT COUNT(*) FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"

        actual_count = await db_connection.fetchval(query)
        assert actual_count == expected_count, f"Expected {expected_count} records in {table_name}, found {actual_count}"

    @staticmethod
    async def assert_record_exists(db_connection, table_name: str, condition: str):
        """Assert that a record matching the condition exists."""
        query = f"SELECT EXISTS (SELECT FROM {table_name} WHERE {condition})"
        exists = await db_connection.fetchval(query)
        assert exists, f"No record found in {table_name} matching: {condition}"

    @staticmethod
    def generate_test_record(table_name: str, **fields) -> Dict[str, Any]:
        """Generate a test record for the specified table."""
        base_record = {
            'id': str(uuid.uuid4()),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        base_record.update(fields)
        return base_record

class PerformanceTestHelper:
    """Helper for performance testing."""

    def __init__(self):
        self.measurements = []

    @asynccontextmanager
    async def measure(self, operation_name: str):
        """Context manager for measuring operation performance."""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage()

            measurement = {
                'operation': operation_name,
                'duration': end_time - start_time,
                'memory_delta': end_memory - start_memory,
                'timestamp': datetime.utcnow().isoformat()
            }
            self.measurements.append(measurement)
            test_logger.info(f"Performance: {operation_name} took {measurement['duration']:.3f}s")

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.measurements:
            return {}

        durations = [m['duration'] for m in self.measurements]
        memory_deltas = [m['memory_delta'] for m in self.measurements]

        return {
            'total_operations': len(self.measurements),
            'duration_stats': {
                'total': sum(durations),
                'average': sum(durations) / len(durations),
                'min': min(durations),
                'max': max(durations)
            },
            'memory_stats': {
                'total_delta': sum(memory_deltas),
                'average_delta': sum(memory_deltas) / len(memory_deltas),
                'min_delta': min(memory_deltas),
                'max_delta': max(memory_deltas)
            },
            'operations': self.measurements
        }

class ParallelTestHelper:
    """Helper for parallel/concurrent testing."""

    @staticmethod
    async def run_concurrent_operations(operations: List[Callable], max_concurrency: int = None) -> List[Any]:
        """Run operations concurrently with optional concurrency limit."""
        if max_concurrency is None or max_concurrency >= len(operations):
            # No limit, run all at once
            return await asyncio.gather(*[op() for op in operations])

        # Run with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrency)

        async def limited_operation(operation):
            async with semaphore:
                return await operation()

        return await asyncio.gather(*[limited_operation(op) for op in operations])

    @staticmethod
    async def test_parallel_behavior(operation_count: int, operation_factory: Callable) -> Dict[str, Any]:
        """Test parallel behavior of operations created by factory."""
        operations = [operation_factory(i) for i in range(operation_count)]

        start_time = time.time()
        results = await asyncio.gather(*[op() for op in operations])
        end_time = time.time()

        return {
            'operation_count': operation_count,
            'total_time': end_time - start_time,
            'average_time_per_operation': (end_time - start_time) / operation_count,
            'successful_operations': sum(1 for r in results if r is not None),
            'failed_operations': sum(1 for r in results if r is None),
            'results': results
        }

class TestDataValidator:
    """Validator for test data integrity."""

    @staticmethod
    def validate_agent_data(agent_data: Dict[str, Any]) -> bool:
        """Validate agent data structure."""
        required_fields = ['agent_id', 'name', 'type', 'level', 'attributes']

        for field in required_fields:
            if field not in agent_data:
                test_logger.error(f"Missing required field in agent data: {field}")
                return False

        # Validate attributes structure
        if not isinstance(agent_data.get('attributes'), dict):
            test_logger.error("Agent attributes must be a dictionary")
            return False

        required_attributes = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        for attr in required_attributes:
            if attr not in agent_data['attributes']:
                test_logger.error(f"Missing required attribute: {attr}")
                return False

        return True

    @staticmethod
    def validate_session_data(session_data: Dict[str, Any]) -> bool:
        """Validate session data structure."""
        required_fields = ['session_id', 'name', 'dungeon_master_id', 'status']

        for field in required_fields:
            if field not in session_data:
                test_logger.error(f"Missing required field in session data: {field}")
                return False

        valid_statuses = ['waiting', 'active', 'paused', 'completed']
        if session_data['status'] not in valid_statuses:
            test_logger.error(f"Invalid session status: {session_data['status']}")
            return False

        return True

    @staticmethod
    def validate_event_data(event_data: Dict[str, Any]) -> bool:
        """Validate event data structure."""
        required_fields = ['event_id', 'session_id', 'event_type', 'timestamp']

        for field in required_fields:
            if field not in event_data:
                test_logger.error(f"Missing required field in event data: {field}")
                return False

        # Validate timestamp format
        try:
            datetime.fromisoformat(event_data['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            test_logger.error(f"Invalid timestamp format: {event_data['timestamp']}")
            return False

        return True

class TestEnvironmentHelper:
    """Helper for managing test environment."""

    @staticmethod
    def is_ci_environment() -> bool:
        """Check if running in CI environment."""
        import os
        return bool(os.getenv('CI') or os.getenv('GITHUB_ACTIONS') or os.getenv('JENKINS_URL'))

    @staticmethod
    def get_test_database_url() -> str:
        """Get test database URL."""
        import os
        return os.getenv('TEST_DATABASE_URL', 'postgresql://localhost/test_dmlogn8n')

    @staticmethod
    def get_test_redis_url() -> str:
        """Get test Redis URL."""
        import os
        return os.getenv('TEST_REDIS_URL', 'redis://localhost:6379/15')

    @staticmethod
    def skip_if_no_internet():
        """Decorator to skip test if no internet connection."""
        def decorator(test_func):
            def wrapper(*args, **kwargs):
                try:
                    import urllib.request
                    urllib.request.urlopen('http://www.google.com', timeout=1)
                    return test_func(*args, **kwargs)
                except:
                    pytest.skip("No internet connection")
            return wrapper
        return decorator

    @staticmethod
    def skip_if_slow():
        """Decorator to skip slow tests in CI."""
        def decorator(test_func):
            def wrapper(*args, **kwargs):
                if TestEnvironmentHelper.is_ci_environment():
                    pytest.skip("Skipping slow test in CI environment")
                return test_func(*args, **kwargs)
            return wrapper
        return decorator

# Decorators for common test patterns
def with_timeout(timeout_seconds: float):
    """Decorator to add timeout to test functions."""
    def decorator(test_func):
        if inspect.iscoroutinefunction(test_func):
            @functools.wraps(test_func)
            async def async_wrapper(*args, **kwargs):
                return await asyncio.wait_for(test_func(*args, **kwargs), timeout=timeout_seconds)
            return async_wrapper
        else:
            @functools.wraps(test_func)
            def sync_wrapper(*args, **kwargs):
                # For sync functions, we can't easily add timeout without threading
                return test_func(*args, **kwargs)
            return sync_wrapper
    return decorator

def log_test_performance(operation_name: str):
    """Decorator to log test performance."""
    def decorator(test_func):
        if inspect.iscoroutinefunction(test_func):
            @functools.wraps(test_func)
            async def async_wrapper(*args, **kwargs):
                with AsyncTestTimer(f"{operation_name} - {test_func.__name__}"):
                    return await test_func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(test_func)
            def sync_wrapper(*args, **kwargs):
                with TestTimer(f"{operation_name} - {test_func.__name__}"):
                    return test_func(*args, **kwargs)
            return sync_wrapper
    return decorator

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """Decorator to retry test functions on failure."""
    def decorator(test_func):
        @functools.wraps(test_func)
        async def async_wrapper(*args, **kwargs):
            retry_helper = RetryHelper(max_attempts, delay)
            return await retry_helper.retry_async(test_func, *args, **kwargs)
        return async_wrapper
    return decorator