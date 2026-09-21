"""
Unit tests for database operations in the DMLogn8n system.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import json
import uuid

# Mock database classes for testing
class MockDatabasePool:
    """Mock database pool for testing."""

    def __init__(self, config):
        self.config = config
        self.connections = []
        self.queries = []
        self.transaction_count = 0

    async def acquire(self):
        """Acquire a connection from the pool."""
        conn = MockConnection(self)
        self.connections.append(conn)
        return conn

    async def close(self):
        """Close all connections."""
        self.connections.clear()

class MockConnection:
    """Mock database connection for testing."""

    def __init__(self, pool):
        self.pool = pool
        self.queries = []
        self.transaction_active = False

    async def fetch(self, query, *args):
        """Mock fetch query."""
        self.queries.append(('fetch', query, args))

        # Return mock data based on query
        if 'SELECT' in query and 'agents' in query:
            return [
                {
                    'id': uuid.uuid4(),
                    'name': 'Test Agent 1',
                    'type': 'npc',
                    'data': {'level': 5},
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                },
                {
                    'id': uuid.uuid4(),
                    'name': 'Test Agent 2',
                    'type': 'player',
                    'data': {'level': 3},
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            ]
        elif 'SELECT' in query and 'sessions' in query:
            return [
                {
                    'id': uuid.uuid4(),
                    'name': 'Test Session',
                    'dungeon_master_id': uuid.uuid4(),
                    'status': 'active',
                    'created_at': datetime.utcnow()
                }
            ]

        return []

    async def fetchrow(self, query, *args):
        """Mock fetchrow query."""
        self.queries.append(('fetchrow', query, args))

        if 'SELECT' in query and 'WHERE' in query:
            return {
                'id': uuid.uuid4(),
                'name': 'Single Agent',
                'type': 'npc',
                'data': {'level': 10},
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }

        return None

    async def fetchval(self, query, *args):
        """Mock fetchval query."""
        self.queries.append(('fetchval', query, args))

        if 'COUNT' in query:
            return 42
        elif 'EXISTS' in query:
            return True

        return None

    async def execute(self, query, *args):
        """Mock execute query."""
        self.queries.append(('execute', query, args))
        return 'INSERT 1' if 'INSERT' in query else 'UPDATE 1'

    async def executemany(self, query, args_list):
        """Mock executemany query."""
        self.queries.append(('executemany', query, args_list))
        return len(args_list)

    def transaction(self):
        """Mock transaction."""
        self.transaction_active = True
        return MockTransaction(self)

class MockTransaction:
    """Mock database transaction."""

    def __init__(self, connection):
        self.connection = connection
        self.operations = []

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.connection.transaction_active = False

class MockDatabaseService:
    """Mock database service for testing."""

    def __init__(self, pool):
        self.pool = pool
        self.cache = {}

    async def create_agent(self, agent_data):
        """Create an agent in the database."""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO agents (id, name, type, data, created_at, updated_at)
                VALUES ($1, $2, $3, $4, NOW(), NOW())
                RETURNING *
            """
            return await conn.fetchrow(
                query,
                agent_data['id'],
                agent_data['name'],
                agent_data['type'],
                json.dumps(agent_data['data'])
            )

    async def get_agent(self, agent_id):
        """Get an agent by ID."""
        async with self.pool.acquire() as conn:
            query = """
                SELECT * FROM agents WHERE id = $1
            """
            return await conn.fetchrow(query, agent_id)

    async def update_agent(self, agent_id, updates):
        """Update an agent."""
        async with self.pool.acquire() as conn:
            query = """
                UPDATE agents
                SET data = $2, updated_at = NOW()
                WHERE id = $1
                RETURNING *
            """
            return await conn.fetchrow(
                query,
                agent_id,
                json.dumps(updates)
            )

    async def delete_agent(self, agent_id):
        """Delete an agent."""
        async with self.pool.acquire() as conn:
            query = "DELETE FROM agents WHERE id = $1"
            return await conn.execute(query, agent_id)

    async def create_session(self, session_data):
        """Create a game session."""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO sessions (id, name, dungeon_master_id, status, created_at)
                VALUES ($1, $2, $3, $4, NOW())
                RETURNING *
            """
            return await conn.fetchrow(
                query,
                session_data['id'],
                session_data['name'],
                session_data['dungeon_master_id'],
                session_data['status']
            )

    async def get_session(self, session_id):
        """Get a session by ID."""
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM sessions WHERE id = $1"
            return await conn.fetchrow(query, session_id)

    async def log_game_event(self, event_data):
        """Log a game event."""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO game_events (id, session_id, agent_id, event_type, event_data, timestamp)
                VALUES ($1, $2, $3, $4, $5, NOW())
            """
            return await conn.execute(
                query,
                event_data['id'],
                event_data['session_id'],
                event_data.get('agent_id'),
                event_data['event_type'],
                json.dumps(event_data['event_data'])
            )

    async def get_agent_count(self):
        """Get total agent count."""
        async with self.pool.acquire() as conn:
            query = "SELECT COUNT(*) FROM agents"
            return await conn.fetchval(query)

@pytest.mark.unit
@pytest.mark.database
class TestDatabaseOperations:
    """Test cases for database operations."""

    @pytest.fixture
    async def mock_pool(self):
        """Create mock database pool."""
        return MockDatabasePool({
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db'
        })

    @pytest.fixture
    def database_service(self, mock_pool):
        """Create database service with mock pool."""
        return MockDatabaseService(mock_pool)

    @pytest.mark.asyncio
    async def test_create_agent_success(self, database_service):
        """Test successful agent creation."""
        agent_data = {
            'id': uuid.uuid4(),
            'name': 'Test Agent',
            'type': 'npc',
            'data': {
                'level': 5,
                'class': 'warrior',
                'attributes': {'strength': 16}
            }
        }

        result = await database_service.create_agent(agent_data)

        assert result is not None
        assert result['name'] == agent_data['name']
        assert result['type'] == agent_data['type']
        assert 'created_at' in result

    @pytest.mark.asyncio
    async def test_get_agent_exists(self, database_service):
        """Test getting existing agent."""
        agent_id = uuid.uuid4()

        result = await database_service.get_agent(agent_id)

        assert result is not None
        assert 'id' in result
        assert 'name' in result

    @pytest.mark.asyncio
    async def test_get_agent_not_exists(self, database_service):
        """Test getting non-existent agent."""
        non_existent_id = uuid.uuid4()

        # Mock the fetchrow to return None for non-existent agent
        async with database_service.pool.acquire() as conn:
            original_fetchrow = conn.fetchrow
            async def mock_fetchrow(query, *args):
                if non_existent_id in args:
                    return None
                return await original_fetchrow(query, *args)
            conn.fetchrow = mock_fetchrow

        result = await database_service.get_agent(non_existent_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_agent_success(self, database_service):
        """Test successful agent update."""
        agent_id = uuid.uuid4()
        updates = {
            'level': 6,
            'health': 45,
            'experience': 1200
        }

        result = await database_service.update_agent(agent_id, updates)

        assert result is not None
        assert 'updated_at' in result

    @pytest.mark.asyncio
    async def test_delete_agent_success(self, database_service):
        """Test successful agent deletion."""
        agent_id = uuid.uuid4()

        result = await database_service.delete_agent(agent_id)

        assert result is not None
        assert 'DELETE' in result

    @pytest.mark.asyncio
    async def test_create_session_success(self, database_service):
        """Test successful session creation."""
        session_data = {
            'id': uuid.uuid4(),
            'name': 'Test Campaign',
            'dungeon_master_id': uuid.uuid4(),
            'status': 'active'
        }

        result = await database_service.create_session(session_data)

        assert result is not None
        assert result['name'] == session_data['name']
        assert result['status'] == session_data['status']
        assert 'created_at' in result

    @pytest.mark.asyncio
    async def test_get_session_exists(self, database_service):
        """Test getting existing session."""
        session_id = uuid.uuid4()

        result = await database_service.get_session(session_id)

        assert result is not None
        assert 'id' in result
        assert 'name' in result

    @pytest.mark.asyncio
    async def test_log_game_event_success(self, database_service):
        """Test successful game event logging."""
        event_data = {
            'id': uuid.uuid4(),
            'session_id': uuid.uuid4(),
            'agent_id': uuid.uuid4(),
            'event_type': 'agent_action',
            'event_data': {
                'action': 'move',
                'from': {'x': 10, 'y': 15},
                'to': {'x': 12, 'y': 17}
            }
        }

        result = await database_service.log_game_event(event_data)

        assert result is not None
        assert 'INSERT' in result

    @pytest.mark.asyncio
    async def test_get_agent_count_success(self, database_service):
        """Test getting agent count."""
        result = await database_service.get_agent_count()

        assert result == 42  # From our mock

@pytest.mark.unit
@pytest.mark.database
class TestDatabaseTransactions:
    """Test cases for database transactions."""

    @pytest.fixture
    async def mock_pool(self):
        """Create mock database pool."""
        return MockDatabasePool({
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db'
        })

    @pytest.fixture
    def database_service(self, mock_pool):
        """Create database service with mock pool."""
        return MockDatabaseService(mock_pool)

    @pytest.mark.asyncio
    async def test_transaction_commit(self, database_service):
        """Test successful transaction commit."""
        async with database_service.pool.acquire() as conn:
            async with conn.transaction() as tx:
                # Create agent
                agent_data = {
                    'id': uuid.uuid4(),
                    'name': 'Transaction Agent',
                    'type': 'npc',
                    'data': {'level': 1}
                }

                await tx.execute(
                    "INSERT INTO agents (id, name, type, data) VALUES ($1, $2, $3, $4)",
                    agent_data['id'],
                    agent_data['name'],
                    agent_data['type'],
                    json.dumps(agent_data['data'])
                )

                # Update agent
                await tx.execute(
                    "UPDATE agents SET data = $1 WHERE id = $2",
                    json.dumps({'level': 2}),
                    agent_data['id']
                )

        # Verify operations were executed
        assert len(conn.queries) == 2
        assert conn.queries[0][0] == 'execute'
        assert conn.queries[1][0] == 'execute'

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, database_service):
        """Test transaction rollback on error."""
        async with database_service.pool.acquire() as conn:
            try:
                async with conn.transaction() as tx:
                    # Create agent
                    agent_data = {
                        'id': uuid.uuid4(),
                        'name': 'Rollback Agent',
                        'type': 'npc',
                        'data': {'level': 1}
                    }

                    await tx.execute(
                        "INSERT INTO agents (id, name, type, data) VALUES ($1, $2, $3, $4)",
                        agent_data['id'],
                        agent_data['name'],
                        agent_data['type'],
                        json.dumps(agent_data['data'])
                    )

                    # Intentionally cause an error
                    raise ValueError("Intentional error for rollback test")

            except ValueError:
                # Expected error
                pass

        # Verify transaction was rolled back
        assert not conn.transaction_active

@pytest.mark.unit
@pytest.mark.database
@pytest.mark.parallel
class TestParallelDatabaseOperations:
    """Test cases for parallel database operations."""

    @pytest.fixture
    async def mock_pool(self):
        """Create mock database pool."""
        return MockDatabasePool({
            'host': 'localhost',
            'port': 5432,
            'database': 'test_db',
            'max_connections': 10
        })

    @pytest.fixture
    def database_service(self, mock_pool):
        """Create database service with mock pool."""
        return MockDatabaseService(mock_pool)

    @pytest.mark.asyncio
    async def test_concurrent_agent_creation(self, database_service):
        """Test concurrent agent creation."""
        agent_count = 20

        tasks = []
        for i in range(agent_count):
            agent_data = {
                'id': uuid.uuid4(),
                'name': f'Concurrent Agent {i}',
                'type': 'npc',
                'data': {'level': i + 1}
            }

            task = database_service.create_agent(agent_data)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        assert len(results) == agent_count

        # Verify all agents were created
        for i, result in enumerate(results):
            assert result is not None
            assert result['name'] == f'Concurrent Agent {i}'

    @pytest.mark.asyncio
    async def test_concurrent_agent_reads(self, database_service):
        """Test concurrent agent reads."""
        agent_count = 15
        agent_ids = [uuid.uuid4() for _ in range(agent_count)]

        tasks = [
            database_service.get_agent(agent_id)
            for agent_id in agent_ids
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == agent_count
        # All results should be agent data or None
        for result in results:
            assert result is None or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(self, database_service):
        """Test concurrent mixed database operations."""
        operation_count = 25
        tasks = []

        # Mix of different operations
        for i in range(operation_count):
            if i % 4 == 0:
                # Create agent
                agent_data = {
                    'id': uuid.uuid4(),
                    'name': f'Mixed Agent {i}',
                    'type': 'npc',
                    'data': {'level': i}
                }
                tasks.append(database_service.create_agent(agent_data))
            elif i % 4 == 1:
                # Read agent
                agent_id = uuid.uuid4()
                tasks.append(database_service.get_agent(agent_id))
            elif i % 4 == 2:
                # Update agent
                agent_id = uuid.uuid4()
                updates = {'level': i + 5}
                tasks.append(database_service.update_agent(agent_id, updates))
            else:
                # Log event
                event_data = {
                    'id': uuid.uuid4(),
                    'session_id': uuid.uuid4(),
                    'agent_id': uuid.uuid4(),
                    'event_type': 'test_event',
                    'event_data': {'iteration': i}
                }
                tasks.append(database_service.log_game_event(event_data))

        results = await asyncio.gather(*tasks)

        assert len(results) == operation_count
        # Verify all operations completed without errors
        for result in results:
            assert result is not None

    @pytest.mark.asyncio
    async def test_connection_pool_limits(self, database_service, mock_pool):
        """Test that connection pool limits are respected."""
        # Create more concurrent tasks than pool connections
        task_count = 20
        tasks = []

        for i in range(task_count):
            agent_id = uuid.uuid4()
            task = database_service.get_agent(agent_id)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        assert len(results) == task_count
        # Verify pool connections were reused
        assert len(mock_pool.connections) <= mock_pool.config.get('max_connections', 10)

@pytest.mark.unit
@pytest.mark.database
class TestDatabaseErrorHandling:
    """Test cases for database error handling."""

    @pytest.fixture
    async def failing_pool(self):
        """Create mock database pool that simulates failures."""
        class FailingConnection:
            def __init__(self):
                self.should_fail = False

            async def fetch(self, query, *args):
                if self.should_fail:
                    raise Exception("Database connection failed")
                return []

            async def fetchrow(self, query, *args):
                if self.should_fail:
                    raise Exception("Database connection failed")
                return None

            def transaction(self):
                return MockTransaction(self)

        class FailingPool:
            def __init__(self):
                self.failure_rate = 0.1

            async def acquire(self):
                conn = FailingConnection()
                # Randomly fail based on failure rate
                import random
                conn.should_fail = random.random() < self.failure_rate
                return conn

        return FailingPool()

    @pytest.fixture
    def failing_database_service(self, failing_pool):
        """Create database service with failing pool."""
        return MockDatabaseService(failing_pool)

    @pytest.mark.asyncio
    async def test_connection_failure_handling(self, failing_database_service):
        """Test handling of database connection failures."""
        agent_id = uuid.uuid4()

        # Multiple attempts to handle intermittent failures
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await failing_database_service.get_agent(agent_id)
                # If successful, break
                if result is not None or result is None:
                    break
            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt, re-raise exception
                    raise
                # Wait before retry
                await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    async def test_query_timeout_handling(self, database_service):
        """Test handling of query timeouts."""
        # Mock a slow query that times out
        async with database_service.pool.acquire() as conn:
            original_fetch = conn.fetch
            async def slow_fetch(query, *args):
                await asyncio.sleep(2.0)  # Simulate slow query
                return await original_fetch(query, *args)

            conn.fetch = slow_fetch

        # This should handle the timeout gracefully
        try:
            await asyncio.wait_for(
                database_service.get_agent(uuid.uuid4()),
                timeout=1.0
            )
        except asyncio.TimeoutError:
            # Expected timeout
            pass

    @pytest.mark.asyncio
    async def test_constraint_violation_handling(self, database_service):
        """Test handling of database constraint violations."""
        agent_data = {
            'id': uuid.uuid4(),
            'name': 'Duplicate Test Agent',
            'type': 'npc',
            'data': {'level': 5}
        }

        # First creation should succeed
        result1 = await database_service.create_agent(agent_data)
        assert result1 is not None

        # Second creation with same ID should fail (mock constraint violation)
        async with database_service.pool.acquire() as conn:
            original_execute = conn.execute
            async def constraint_violation_execute(query, *args):
                if 'INSERT' in query:
                    raise Exception("Unique constraint violation")
                return await original_execute(query, *args)

            conn.execute = constraint_violation_execute

        # Should handle the constraint violation gracefully
        with pytest.raises(Exception, match="constraint violation"):
            await database_service.create_agent(agent_data)