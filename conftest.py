"""
Global pytest configuration and fixtures for DMLogn8n parallel multi-agent system testing.
"""

import asyncio
import json
import pytest
import logging
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any, Optional, Generator
import aiohttp
import socketio
import redis
import asyncpg
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration constants
TEST_CONFIG = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "user": "test_user",
        "password": "test_password",
        "database": "test_dmlogn8n"
    },
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 15  # Use dedicated test DB
    },
    "api": {
        "base_url": "http://localhost:3000",
        "timeout": 30
    },
    "websocket": {
        "url": "ws://localhost:3000",
        "timeout": 10
    },
    "performance": {
        "default_agent_count": 100,
        "stress_agent_count": 1000,
        "load_duration": 60,  # seconds
        "soak_duration": 3600,  # 1 hour
        "ramp_up_time": 30  # seconds
    }
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration to all tests."""
    return TEST_CONFIG

@pytest.fixture(scope="function")
async def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)

@pytest.fixture(scope="function")
async def mock_redis(test_config):
    """Create a mock Redis connection for testing."""
    redis_client = AsyncMock()

    # Mock common Redis operations
    redis_client.get.return_value = None
    redis_client.set.return_value = True
    redis_client.delete.return_value = 1
    redis_client.exists.return_value = False
    redis_client.expire.return_value = True
    redis_client.hget.return_value = None
    redis_client.hset.return_value = True
    redis_client.hgetall.return_value = {}
    redis_client.lpush.return_value = 1
    redis_client.rpop.return_value = None
    redis_client.llen.return_value = 0
    redis_client.publish.return_value = 1
    redis_client.subscribe.return_value = AsyncMock()

    yield redis_client

@pytest.fixture(scope="function")
async def mock_database():
    """Create a mock database connection for testing."""
    db_pool = AsyncMock()

    # Mock common database operations
    mock_connection = AsyncMock()
    mock_connection.fetch.return_value = []
    mock_connection.fetchrow.return_value = None
    mock_connection.fetchval.return_value = None
    mock_connection.execute.return_value = None
    mock_connection.executemany.return_value = None
    mock_connection.transaction.return_value.__aenter__.return_value = mock_connection
    mock_connection.transaction.return_value.__aexit__.return_value = None

    db_pool.acquire.return_value.__aenter__.return_value = mock_connection
    db_pool.acquire.return_value.__aexit__.return_value = None

    yield db_pool

@pytest.fixture(scope="function")
async def mock_aiohttp_session():
    """Create a mock aiohttp session for HTTP testing."""
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"status": "success"}
    mock_response.text.return_value = "success"

    mock_session.get.return_value.__aenter__.return_value = mock_response
    mock_session.post.return_value.__aenter__.return_value = mock_response
    mock_session.put.return_value.__aenter__.return_value = mock_response
    mock_session.delete.return_value.__aenter__.return_value = mock_response

    yield mock_session

@pytest.fixture(scope="function")
async def mock_socketio_client():
    """Create a mock Socket.IO client for WebSocket testing."""
    sio = AsyncMock()

    # Mock socket.io events
    sio.emit = AsyncMock()
    sio.on = MagicMock()
    sio.disconnect = AsyncMock()
    sio.connect = AsyncMock()

    yield sio

@pytest.fixture(scope="function")
def sample_agent_data():
    """Provide sample agent data for testing."""
    return {
        "agent_id": "test_agent_001",
        "name": "Test Agent",
        "type": "npc",
        "class": "warrior",
        "level": 5,
        "attributes": {
            "strength": 16,
            "dexterity": 14,
            "constitution": 15,
            "intelligence": 12,
            "wisdom": 13,
            "charisma": 11
        },
        "skills": ["athletics", "intimidation", "perception"],
        "equipment": ["longsword", "shield", "leather_armor"],
        "personality": {
            "traits": ["brave", "loyal"],
            "ideals": ["honor", "justice"],
            "bonds": ["family", "kingdom"],
            "flaws": ["reckless", "stubborn"]
        },
        "location": {
            "zone": "starting_area",
            "x": 10,
            "y": 15,
            "z": 0
        },
        "status": "active",
        "health": 45,
        "max_health": 50,
        "mana": 20,
        "max_mana": 20
    }

@pytest.fixture(scope="function")
def sample_game_session():
    """Provide sample game session data for testing."""
    return {
        "session_id": "test_session_001",
        "name": "Test Campaign",
        "description": "A test campaign for unit testing",
        "dungeon_master_id": "dm_001",
        "players": ["player_001", "player_002", "player_003"],
        "npcs": ["npc_001", "npc_002"],
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "settings": {
            "difficulty": "medium",
            "max_players": 6,
            "allow_pvp": False,
            "respawn_enabled": True,
            "save_frequency": 300  # seconds
        },
        "current_scene": {
            "scene_id": "scene_001",
            "name": "Starting Tavern",
            "description": "A cozy tavern where adventures begin",
            "environment": "indoor",
            "lighting": "dim"
        }
    }

@pytest.fixture(scope="function")
def parallel_agent_factory():
    """Factory to create multiple agents for parallel testing."""
    def create_agents(count: int, base_data: Optional[Dict] = None) -> List[Dict]:
        agents = []
        for i in range(count):
            agent_data = base_data.copy() if base_data else {}
            agent_data.update({
                "agent_id": f"parallel_agent_{i:04d}",
                "name": f"Parallel Agent {i}",
                "location": {
                    "zone": "test_zone",
                    "x": i % 100,
                    "y": (i // 100) % 100,
                    "z": 0
                }
            })
            agents.append(agent_data)
        return agents

    return create_agents

@pytest.fixture(scope="function")
async def performance_monitor():
    """Monitor performance during test execution."""
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.memory_usage = []
            self.cpu_usage = []
            self.request_counts = {}
            self.error_counts = {}

        async def start(self):
            self.start_time = datetime.utcnow()

        async def stop(self):
            self.end_time = datetime.utcnow()

        async def record_memory(self, usage: float):
            self.memory_usage.append((datetime.utcnow(), usage))

        async def record_cpu(self, usage: float):
            self.cpu_usage.append((datetime.utcnow(), usage))

        async def record_request(self, endpoint: str):
            self.request_counts[endpoint] = self.request_counts.get(endpoint, 0) + 1

        async def record_error(self, error_type: str):
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        def get_duration(self) -> float:
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time).total_seconds()
            return 0

        def get_stats(self) -> Dict[str, Any]:
            return {
                "duration": self.get_duration(),
                "total_requests": sum(self.request_counts.values()),
                "total_errors": sum(self.error_counts.values()),
                "memory_samples": len(self.memory_usage),
                "cpu_samples": len(self.cpu_usage),
                "requests_by_endpoint": self.request_counts,
                "errors_by_type": self.error_counts
            }

    monitor = PerformanceMonitor()
    yield monitor

@pytest.fixture(scope="function")
async def load_test_runner():
    """Run load tests with multiple concurrent agents."""
    class LoadTestRunner:
        def __init__(self):
            self.results = []
            self.errors = []

        async def run_concurrent_agents(self, agent_count: int, test_function, **kwargs):
            """Run test function concurrently for multiple agents."""
            tasks = []
            for i in range(agent_count):
                task = asyncio.create_task(
                    test_function(agent_id=f"load_test_agent_{i:04d}", **kwargs)
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.errors.append({"agent_id": f"load_test_agent_{i:04d}", "error": str(result)})
                else:
                    self.results.append({"agent_id": f"load_test_agent_{i:04d}", "result": result})

            return {
                "total_agents": agent_count,
                "successful_agents": len(self.results),
                "failed_agents": len(self.errors),
                "success_rate": len(self.results) / agent_count if agent_count > 0 else 0,
                "results": self.results,
                "errors": self.errors
            }

    runner = LoadTestRunner()
    yield runner

# Environment-specific fixtures
@pytest.fixture(scope="session")
def ci_environment():
    """Detect if running in CI environment."""
    return bool(os.getenv("CI") or os.getenv("GITHUB_ACTIONS"))

@pytest.fixture(scope="function")
def skip_slow_tests(ci_environment):
    """Skip slow tests in CI environment."""
    if ci_environment:
        pytest.skip("Skipping slow test in CI environment")

# Parallel processing fixtures
@pytest.fixture(scope="function")
async def parallel_processing_pool():
    """Create a pool for parallel processing tests."""
    import concurrent.futures

    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        yield executor

@pytest.fixture(scope="function")
async def mock_ai_models():
    """Mock AI model responses for testing."""
    class MockAIModels:
        @staticmethod
        async def generate_dialogue(prompt: str, context: Dict = None) -> str:
            return f"Generated dialogue for: {prompt[:50]}..."

        @staticmethod
        async def analyze_emotion(text: str) -> Dict[str, float]:
            return {
                "joy": 0.2,
                "sadness": 0.1,
                "anger": 0.1,
                "fear": 0.1,
                "surprise": 0.2,
                "neutral": 0.3
            }

        @staticmethod
        async def make_decision(context: Dict, options: List[str]) -> str:
            return options[0] if options else "default_action"

        @staticmethod
        async def generate_response(message: str, personality: Dict) -> str:
            return f"Response to: {message[:30]}..."

    return MockAIModels()

# Database fixtures for testing
@pytest.fixture(scope="function")
async def test_database_setup(mock_database):
    """Set up test database schema and data."""
    # Mock table creation
    await mock_database.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id UUID PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            data JSONB,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)

    await mock_database.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id UUID PRIMARY KEY,
            name TEXT NOT NULL,
            dungeon_master_id UUID NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)

    await mock_database.execute("""
        CREATE TABLE IF NOT EXISTS game_events (
            id UUID PRIMARY KEY,
            session_id UUID NOT NULL,
            agent_id UUID,
            event_type TEXT NOT NULL,
            event_data JSONB,
            timestamp TIMESTAMP DEFAULT NOW()
        )
    """)

    yield mock_database

# WebSocket testing utilities
@pytest.fixture(scope="function")
async def websocket_test_utils():
    """Utilities for WebSocket testing."""
    class WebSocketTestUtils:
        @staticmethod
        async def wait_for_event(sio_client, event_name: str, timeout: float = 5.0):
            """Wait for a specific WebSocket event."""
            event_received = asyncio.Event()
            event_data = None

            def handler(data):
                nonlocal event_data
                event_data = data
                event_received.set()

            sio_client.on(event_name, handler)

            try:
                await asyncio.wait_for(event_received.wait(), timeout=timeout)
                return event_data
            except asyncio.TimeoutError:
                raise TimeoutError(f"Event '{event_name}' not received within {timeout} seconds")
            finally:
                sio_client.off(event_name, handler)

    return WebSocketTestUtils()

# Cleanup fixtures
@pytest.fixture(scope="function", autouse=True)
async def cleanup_test_resources():
    """Clean up resources after each test."""
    yield
    # Add any cleanup logic here
    await asyncio.sleep(0.01)  # Small delay to allow cleanup

# Custom assertions
@pytest.fixture(scope="function")
def assert_parallel_behavior():
    """Custom assertions for parallel behavior testing."""
    class ParallelAssertions:
        @staticmethod
        def assert_concurrent_execution(results: List, min_concurrent: int):
            """Assert that operations were executed concurrently."""
            timestamps = [r.get("timestamp") for r in results if r.get("timestamp")]
            if len(timestamps) < min_concurrent:
                pytest.fail(f"Expected at least {min_concurrent} concurrent operations, got {len(timestamps)}")

        @staticmethod
        def assert_load_balanced(agent_loads: Dict[str, int], tolerance: float = 0.2):
            """Assert that load is reasonably balanced across agents."""
            if not agent_loads:
                pytest.fail("No agent load data provided")

            loads = list(agent_loads.values())
            avg_load = sum(loads) / len(loads)
            max_load = max(loads)
            min_load = min(loads)

            if max_load > avg_load * (1 + tolerance):
                pytest.fail(f"Load imbalance detected: max={max_load}, avg={avg_load:.2f}")
            if min_load < avg_load * (1 - tolerance):
                pytest.fail(f"Load imbalance detected: min={min_load}, avg={avg_load:.2f}")

        @staticmethod
        def assert_fault_tolerance(results: List, success_threshold: float = 0.95):
            """Assert that system maintains operation under fault conditions."""
            if not results:
                pytest.fail("No results to evaluate")

            success_count = sum(1 for r in results if r.get("success", False))
            success_rate = success_count / len(results)

            if success_rate < success_threshold:
                pytest.fail(f"Success rate {success_rate:.2f} below threshold {success_threshold}")

    return ParallelAssertions()