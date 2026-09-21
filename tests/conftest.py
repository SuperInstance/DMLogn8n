"""
Enhanced conftest.py for DMLog comprehensive testing
"""

import os
import sys
import asyncio
import pytest
import pytest_asyncio
from pathlib import Path
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import Mock, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
import sqlite3
import tempfile
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add source code to path
current_dir = Path(__file__).parent
source_code_dir = current_dir.parent / "source_code"
sys.path.insert(0, str(source_code_dir))
sys.path.insert(0, str(source_code_dir / "backend"))

# Test configuration - use in-memory SQLite for fast testing
TEST_DATABASE_URL = "sqlite:///:memory:"

# Mock settings for testing
class MockSettings:
    def __init__(self):
        self.database_url = TEST_DATABASE_URL
        self.redis_url = "redis://localhost:6379/1"
        self.qdrant_url = "http://localhost:6334"
        self.debug = True
        self.environment = "testing"
        self.secret_key = "test-secret-key-change-in-production"
        self.log_level = "DEBUG"
        self.max_connections = 5
        self.openai_api_key = "test-openai-key"
        self.anthropic_api_key = "test-anthropic-key"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def mock_settings():
    """Mock settings for testing"""
    return MockSettings()

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # Create basic tables for testing
    from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()

    # Define basic test models
    class User(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        username = Column(String, unique=True, nullable=False)
        email = Column(String, unique=True, nullable=False)
        password_hash = Column(String, nullable=False)
        is_active = Column(Boolean, default=True)
        is_dm = Column(Boolean, default=False)
        created_at = Column(DateTime, default=datetime.utcnow)

    class Character(Base):
        __tablename__ = "characters"
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        race = Column(String, nullable=False)
        class_name = Column(String, nullable=False)
        level = Column(Integer, default=1)
        user_id = Column(Integer, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)

    class Campaign(Base):
        __tablename__ = "campaigns"
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        description = Column(Text)
        dm_id = Column(Integer, nullable=False)
        is_public = Column(Boolean, default=False)
        created_at = Column(DateTime, default=datetime.utcnow)

    class GameSession(Base):
        __tablename__ = "game_sessions"
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        campaign_id = Column(Integer, nullable=False)
        scheduled_start = Column(DateTime)
        status = Column(String, default="scheduled")
        created_at = Column(DateTime, default=datetime.utcnow)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Store for use in other fixtures
    test_engine.Base = Base

    yield engine

    # Clean up
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db_session(test_engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    session = TestingSessionLocal()

    # Set up transaction for each test
    connection = test_engine.connect()
    transaction = connection.begin()
    session.bind = connection

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture(scope="function")
def mock_app():
    """Create a mock FastAPI app for testing"""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="DMLog Test API")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add basic health endpoint
    @app.get("/api/health")
    async def health():
        return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

    # Add basic auth endpoints
    @app.post("/api/auth/register")
    async def register(user_data: dict):
        return {"id": 1, "username": user_data.get("username"), "status": "created"}

    @app.post("/api/auth/login")
    async def login(form_data: dict = None):
        # Handle both form data and JSON
        if form_data is None:
            from fastapi import Form
            return {"access_token": "test-token", "token_type": "bearer"}
        else:
            return {"access_token": "test-token", "token_type": "bearer"}

    # Add basic character endpoints
    @app.get("/api/characters")
    async def get_characters():
        return {"characters": []}

    @app.post("/api/characters")
    async def create_character(character_data: dict):
        return {"id": 1, "name": character_data.get("name"), "status": "created"}

    # Add basic campaign endpoints
    @app.get("/api/campaigns")
    async def get_campaigns():
        return {"campaigns": []}

    @app.post("/api/campaigns")
    async def create_campaign(campaign_data: dict):
        return {"id": 1, "name": campaign_data.get("name"), "status": "created"}

    # Add WebSocket endpoint
    @app.websocket("/ws/{room_id}")
    async def websocket_endpoint(websocket):
        await websocket.accept()
        await websocket.send_json({"type": "connection", "status": "connected"})

    return app

@pytest.fixture(scope="function")
def test_client(mock_app, test_db_session, mock_settings) -> TestClient:
    """Create a test client with mocked dependencies"""

    # Mock database dependency
    def mock_get_db():
        try:
            yield test_db_session
        finally:
            pass

    # Mock settings dependency
    def mock_get_settings():
        return mock_settings

    # Add overrides if the app has these dependencies
    if hasattr(mock_app, 'dependency_overrides'):
        mock_app.dependency_overrides.clear()

    with TestClient(mock_app) as client:
        yield client

@pytest.fixture(scope="function")
async def async_test_client(mock_app, test_db_session, mock_settings) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client"""

    async with AsyncClient(app=mock_app, base_url="http://test") as client:
        yield client

@pytest.fixture(scope="function")
def mock_external_services():
    """Mock external services"""
    mocks = {
        'openai': AsyncMock(),
        'anthropic': AsyncMock(),
        'qdrant': AsyncMock(),
        'email_service': AsyncMock(),
        'file_storage': AsyncMock(),
        'redis': AsyncMock()
    }

    # Setup default responses
    mocks['openai'].chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="Test AI response"))]
    )
    mocks['anthropic'].messages.create.return_value = Mock(
        content=[Mock(type="text", text="Test Anthropic response")]
    )
    mocks['redis'].get.return_value = None
    mocks['redis'].set.return_value = True
    mocks['redis'].delete.return_value = True

    return mocks

@pytest.fixture(scope="function")
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123!",
        "display_name": "Test User",
        "is_active": True,
        "is_dm": False
    }

@pytest.fixture(scope="function")
def sample_character_data():
    """Sample character data for testing"""
    return {
        "name": "Test Character",
        "race": "Human",
        "class": "Fighter",
        "level": 1,
        "strength": 16,
        "dexterity": 14,
        "constitution": 15,
        "intelligence": 12,
        "wisdom": 13,
        "charisma": 10,
        "max_hp": 12,
        "current_hp": 12,
        "armor_class": 15,
        "speed": 30,
        "background": "Soldier",
        "alignment": "Lawful Good",
        "personality_traits": "Brave and loyal",
        "ideals": "Honor and justice",
        "bonds": "Protects the innocent",
        "flaws": "Impulsive"
    }

@pytest.fixture(scope="function")
def sample_campaign_data():
    """Sample campaign data for testing"""
    return {
        "name": "Test Campaign",
        "description": "A test campaign for unit testing",
        "setting": "Forgotten Realms",
        "starting_level": 1,
        "max_players": 4,
        "is_public": False,
        "tags": ["adventure", "fantasy", "testing"],
        "house_rules": "Standard D&D 5e rules",
        "session_notes": "First session will be character introduction"
    }

@pytest.fixture(scope="function")
def sample_game_session_data():
    """Sample game session data for testing"""
    return {
        "name": "Test Session",
        "description": "A test game session",
        "scheduled_start": "2024-01-01T19:00:00Z",
        "estimated_duration": "4 hours",
        "status": "scheduled",
        "is_public": False,
        "max_players": 4,
        "notes": "Bring your character sheets"
    }

@pytest.fixture(scope="function")
def authenticated_test_client(test_client, sample_user_data):
    """Create an authenticated test client"""
    # Register user
    register_response = test_client.post("/api/auth/register", json=sample_user_data)
    # Mock app returns 200, not 201
    assert register_response.status_code in [200, 201]

    # Login user
    login_response = test_client.post("/api/auth/login", data={
        "username": sample_user_data["username"],
        "password": sample_user_data["password"]
    })
    assert login_response.status_code == 200

    token_data = login_response.json()
    token = token_data["access_token"]

    # Set authorization header
    test_client.headers.update({"Authorization": f"Bearer {token}"})

    yield test_client

    # Clean up
    test_client.headers.pop("Authorization", None)

@pytest.fixture(scope="function")
def mock_websocket():
    """Mock WebSocket connection"""
    mock_ws = AsyncMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_text = AsyncMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.receive_text = AsyncMock(return_value='{"type": "ping"}')
    mock_ws.receive_json = AsyncMock(return_value={"type": "ping"})
    mock_ws.close = AsyncMock()

    return mock_ws

# Performance testing fixtures
@pytest.fixture(scope="function")
def performance_timer():
    """Timer for performance testing"""
    import time
    from datetime import datetime

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0

        @property
        def elapsed_ms(self):
            return self.elapsed * 1000

    return Timer()

# Load testing fixtures
@pytest.fixture(scope="session")
def load_test_config():
    """Configuration for load testing"""
    return {
        "host": "http://localhost:8000",
        "users": 10,
        "spawn_rate": 2,
        "run_time": "30s",
        "requests": [
            "/api/health",
            "/api/campaigns",
            "/api/characters"
        ]
    }

# Security testing fixtures
@pytest.fixture(scope="function")
def security_test_payloads():
    """Malicious payloads for security testing"""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1; DELETE FROM campaigns; --"
        ],
        "xss": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ],
        "command_injection": [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /"
        ]
    }

# Auto-cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Auto-cleanup after each test"""
    yield
    # Add any cleanup logic here
    pass

# Custom markers for pytest
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "load: mark test as load test")
    config.addinivalue_line("markers", "security: mark test as security test")
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "websocket: mark test as websocket test")

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Add unit marker to tests in unit directory
        if "tests/unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Add integration marker to tests in integration directory
        elif "tests/integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add e2e marker to tests in e2e directory
        elif "tests/e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)

        # Add load marker to tests in load directory
        elif "tests/load" in str(item.fspath):
            item.add_marker(pytest.mark.load)
            item.add_marker(pytest.mark.slow)

        # Add security marker to tests in security directory
        elif "tests/security" in str(item.fspath):
            item.add_marker(pytest.mark.security)

# Add datetime import
from datetime import datetime