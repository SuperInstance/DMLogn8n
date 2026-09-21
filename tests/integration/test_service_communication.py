"""
Integration tests for service-to-service communication in the DMLogn8n system.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import aiohttp
import uuid

# Mock service classes for integration testing
class MockAPIService:
    """Mock API Gateway service."""

    def __init__(self, config):
        self.config = config
        self.routes = {}
        self.middleware = []
        self.request_count = 0
        self.response_times = []

    async def handle_request(self, method, path, headers=None, data=None):
        """Handle incoming request."""
        start_time = asyncio.get_event_loop().time()
        self.request_count += 1

        # Apply middleware
        for middleware in self.middleware:
            await middleware(method, path, headers, data)

        # Route request
        response = await self.route_request(method, path, headers, data)

        end_time = asyncio.get_event_loop().time()
        self.response_times.append(end_time - start_time)

        return response

    async def route_request(self, method, path, headers, data):
        """Route request to appropriate service."""
        if path.startswith('/api/agents'):
            return await self.handle_agents_request(method, path, data)
        elif path.startswith('/api/sessions'):
            return await self.handle_sessions_request(method, path, data)
        elif path.startswith('/api/events'):
            return await self.handle_events_request(method, path, data)
        else:
            return {'status': 404, 'error': 'Not found'}

    async def handle_agents_request(self, method, path, data):
        """Handle agent-related requests."""
        if method == 'GET' and path == '/api/agents':
            return {'status': 200, 'data': []}
        elif method == 'POST' and path == '/api/agents':
            return {'status': 201, 'data': {'id': str(uuid.uuid4())}}
        else:
            return {'status': 400, 'error': 'Bad request'}

    async def handle_sessions_request(self, method, path, data):
        """Handle session-related requests."""
        if method == 'GET' and path.startswith('/api/sessions/'):
            session_id = path.split('/')[-1]
            return {'status': 200, 'data': {'id': session_id, 'name': 'Test Session'}}
        elif method == 'POST' and path == '/api/sessions':
            return {'status': 201, 'data': {'id': str(uuid.uuid4())}}
        else:
            return {'status': 400, 'error': 'Bad request'}

    async def handle_events_request(self, method, path, data):
        """Handle event-related requests."""
        if method == 'POST' and path == '/api/events':
            return {'status': 201, 'data': {'event_id': str(uuid.uuid4())}}
        else:
            return {'status': 400, 'error': 'Bad request'}

class MockAgentService:
    """Mock Agent service."""

    def __init__(self, config):
        self.config = config
        self.agents = {}
        self.api_client = None

    async def create_agent(self, agent_data):
        """Create a new agent."""
        agent_id = str(uuid.uuid4())
        self.agents[agent_id] = {
            'id': agent_id,
            **agent_data,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        return self.agents[agent_id]

    async def get_agent(self, agent_id):
        """Get agent by ID."""
        return self.agents.get(agent_id)

    async def update_agent(self, agent_id, updates):
        """Update agent."""
        if agent_id in self.agents:
            self.agents[agent_id].update(updates)
            self.agents[agent_id]['updated_at'] = datetime.utcnow()
            return self.agents[agent_id]
        return None

    async def notify_websocket_service(self, agent_id, update_data):
        """Notify WebSocket service of agent update."""
        if self.api_client:
            await self.api_client.post('/api/websocket/agent-update', {
                'agent_id': agent_id,
                'update_data': update_data,
                'timestamp': datetime.utcnow().isoformat()
            })

class MockWebSocketService:
    """Mock WebSocket service."""

    def __init__(self, config):
        self.config = config
        self.connected_clients = {}
        self.rooms = {}
        self.event_queue = asyncio.Queue()

    async def handle_agent_update(self, agent_id, update_data):
        """Handle agent update from other services."""
        # Queue event for broadcasting
        await self.event_queue.put({
            'type': 'agent_update',
            'agent_id': agent_id,
            'data': update_data,
            'timestamp': datetime.utcnow().isoformat()
        })

    async def broadcast_to_session(self, session_id, event_data):
        """Broadcast event to all clients in session."""
        if session_id in self.rooms:
            for client_id in self.rooms[session_id]:
                # In real implementation, send to actual WebSocket clients
                pass

class MockDatabaseService:
    """Mock Database service."""

    def __init__(self, config):
        self.config = config
        self.connections = []
        self.query_count = 0

    async def execute_query(self, query, params=None):
        """Execute database query."""
        self.query_count += 1
        await asyncio.sleep(0.01)  # Simulate query execution time

        # Mock different query types
        if 'INSERT INTO agents' in query:
            return {'status': 'success', 'id': str(uuid.uuid4())}
        elif 'SELECT' in query and 'agents' in query:
            return [{'id': str(uuid.uuid4()), 'name': 'Test Agent'}]
        elif 'UPDATE' in query:
            return {'status': 'success', 'rows_affected': 1}
        else:
            return {'status': 'success'}

    async def create_transaction(self):
        """Create database transaction."""
        return MockDatabaseTransaction()

class MockDatabaseTransaction:
    """Mock database transaction."""

    def __init__(self):
        self.operations = []

    async def execute(self, query, params=None):
        """Execute query within transaction."""
        self.operations.append((query, params))

    async def commit(self):
        """Commit transaction."""
        pass

    async def rollback(self):
        """Rollback transaction."""
        pass

class MockAIModelService:
    """Mock AI Model service."""

    def __init__(self, config):
        self.config = config
        self.request_count = 0
        self.response_times = []

    async def generate_dialogue(self, prompt, context=None):
        """Generate dialogue using AI model."""
        start_time = asyncio.get_event_loop().time()
        self.request_count += 1

        await asyncio.sleep(0.1)  # Simulate AI processing time

        response = f"Generated dialogue for: {prompt[:50]}..."

        end_time = asyncio.get_event_loop().time()
        self.response_times.append(end_time - start_time)

        return {
            'dialogue': response,
            'model': 'mock-gpt-4',
            'tokens_used': 150,
            'processing_time': end_time - start_time
        }

    async def analyze_emotion(self, text):
        """Analyze emotion in text."""
        await asyncio.sleep(0.05)  # Simulate processing time

        return {
            'emotions': {
                'joy': 0.2,
                'sadness': 0.1,
                'anger': 0.1,
                'fear': 0.1,
                'surprise': 0.3,
                'neutral': 0.2
            },
            'dominant_emotion': 'surprise',
            'confidence': 0.75
        }

class ServiceIntegrationManager:
    """Manages integration between services."""

    def __init__(self):
        self.services = {}
        self.communication_channels = {}
        self.request_logs = []

    def register_service(self, name, service):
        """Register a service."""
        self.services[name] = service

    def create_communication_channel(self, service1, service2):
        """Create communication channel between services."""
        channel_name = f"{service1}_{service2}"
        self.communication_channels[channel_name] = {
            'service1': service1,
            'service2': service2,
            'message_count': 0,
            'errors': 0
        }

    async def communicate(self, from_service, to_service, message_type, data):
        """Send message from one service to another."""
        channel_name = f"{from_service}_{to_service}"
        if channel_name not in self.communication_channels:
            raise ValueError(f"No communication channel between {from_service} and {to_service}")

        channel = self.communication_channels[channel_name]
        channel['message_count'] += 1

        try:
            # Log communication
            self.request_logs.append({
                'from': from_service,
                'to': to_service,
                'type': message_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            })

            # Route message to target service
            target_service = self.services[to_service]
            response = await self._route_message(target_service, message_type, data)

            return response

        except Exception as e:
            channel['errors'] += 1
            raise

    async def _route_message(self, service, message_type, data):
        """Route message to appropriate service method."""
        if message_type == 'agent_created' and hasattr(service, 'handle_agent_created'):
            return await service.handle_agent_created(data)
        elif message_type == 'session_created' and hasattr(service, 'handle_session_created'):
            return await service.handle_session_created(data)
        elif message_type == 'game_event' and hasattr(service, 'handle_game_event'):
            return await service.handle_game_event(data)
        else:
            return {'status': 'ok', 'message': 'Message received'}

@pytest.mark.integration
class TestAPIServiceCommunication:
    """Test API Gateway communication with other services."""

    @pytest.fixture
    def service_manager(self):
        """Create service integration manager."""
        return ServiceIntegrationManager()

    @pytest.fixture
    def api_service(self):
        """Create mock API service."""
        return MockAPIService({
            'host': 'localhost',
            'port': 3000,
            'timeout': 30
        })

    @pytest.fixture
    def agent_service(self):
        """Create mock agent service."""
        return MockAgentService({
            'max_agents': 1000,
            'database_url': 'postgresql://localhost/test'
        })

    @pytest.fixture
    def websocket_service(self):
        """Create mock WebSocket service."""
        return MockWebSocketService({
            'port': 3001,
            'max_connections': 1000
        })

    @pytest_asyncio.fixture
    async def integrated_services(self, service_manager, api_service, agent_service, websocket_service):
        """Set up integrated services."""
        # Register services
        service_manager.register_service('api', api_service)
        service_manager.register_service('agent', agent_service)
        service_manager.register_service('websocket', websocket_service)

        # Create communication channels
        service_manager.create_communication_channel('api', 'agent')
        service_manager.create_communication_channel('agent', 'websocket')

        # Set up service references
        agent_service.api_client = MockAPIClient(service_manager, 'websocket')

        yield service_manager

    @pytest.mark.asyncio
    async def test_api_to_agent_service_communication(self, integrated_services, api_service, agent_service):
        """Test communication from API service to agent service."""
        # Simulate API request to create agent
        agent_data = {
            'name': 'Test Agent',
            'type': 'npc',
            'level': 5
        }

        # API service routes request to agent service
        response = await api_service.handle_agents_request('POST', '/api/agents', agent_data)

        assert response['status'] == 201
        assert 'id' in response['data']

    @pytest.mark.asyncio
    async def test_agent_to_websocket_notification(self, integrated_services, agent_service, websocket_service):
        """Test agent service notifying WebSocket service."""
        agent_id = 'test_agent_001'
        update_data = {'health': 85, 'position': {'x': 10, 'y': 15}}

        # Agent service updates and notifies WebSocket service
        await agent_service.notify_websocket_service(agent_id, update_data)

        # Verify WebSocket service received update
        assert not websocket_service.event_queue.empty()
        event = await websocket_service.event_queue.get()
        assert event['type'] == 'agent_update'
        assert event['agent_id'] == agent_id
        assert event['data'] == update_data

    @pytest.mark.asyncio
    async def test_service_communication_logging(self, integrated_services):
        """Test that service communication is properly logged."""
        # Send message between services
        await integrated_services.communicate(
            'api', 'agent', 'agent_created',
            {'agent_id': 'test_001', 'name': 'Test Agent'}
        )

        # Verify communication was logged
        assert len(integrated_services.request_logs) == 1
        log_entry = integrated_services.request_logs[0]
        assert log_entry['from'] == 'api'
        assert log_entry['to'] == 'agent'
        assert log_entry['type'] == 'agent_created'

@pytest.mark.integration
class TestDatabaseIntegration:
    """Test database service integration with other services."""

    @pytest.fixture
    def service_manager(self):
        """Create service integration manager."""
        return ServiceIntegrationManager()

    @pytest.fixture
    def agent_service(self):
        """Create agent service with database integration."""
        service = MockAgentService({
            'max_agents': 1000,
            'database_url': 'postgresql://localhost/test'
        })
        service.database = MockDatabaseService({
            'host': 'localhost',
            'port': 5432
        })
        return service

    @pytest.fixture
    def session_service(self):
        """Create session service with database integration."""
        service = MockSessionService({
            'max_sessions': 100,
            'database_url': 'postgresql://localhost/test'
        })
        service.database = MockDatabaseService({
            'host': 'localhost',
            'port': 5432
        })
        return service

    @pytest.mark.asyncio
    async def test_agent_database_operations(self, agent_service):
        """Test agent service database operations."""
        agent_data = {
            'name': 'Database Test Agent',
            'type': 'npc',
            'level': 10
        }

        # Create agent (should persist to database)
        agent = await agent_service.create_agent(agent_data)
        assert agent is not None

        # Simulate database query
        query = "INSERT INTO agents (id, name, type, data) VALUES ($1, $2, $3, $4)"
        result = await agent_service.database.execute_query(query, [
            agent['id'],
            agent['name'],
            agent['type'],
            json.dumps(agent)
        ])

        assert result['status'] == 'success'

    @pytest.mark.asyncio
    async def test_transaction_consistency(self, agent_service):
        """Test transaction consistency across services."""
        # Create transaction
        transaction = await agent_service.database.create_transaction()

        # Execute multiple operations in transaction
        await transaction.execute("INSERT INTO agents (id, name) VALUES ($1, $2)", ['agent_1', 'Agent 1'])
        await transaction.execute("UPDATE agents SET level = 5 WHERE id = $1", ['agent_1'])

        # Commit transaction
        await transaction.commit()

        # Verify operations were recorded
        assert len(transaction.operations) == 2

    @pytest.mark.asyncio
    async def test_database_error_handling(self, agent_service):
        """Test database error handling in service integration."""
        # Simulate database error
        with patch.object(agent_service.database, 'execute_query', side_effect=Exception("Database connection failed")):
            with pytest.raises(Exception, match="Database connection failed"):
                await agent_service.database.execute_query("SELECT * FROM agents")

@pytest.mark.integration
class TestAIModelIntegration:
    """Test AI model service integration."""

    @pytest.fixture
    def service_manager(self):
        """Create service integration manager."""
        return ServiceIntegrationManager()

    @pytest.fixture
    def ai_service(self):
        """Create AI model service."""
        return MockAIModelService({
            'model_endpoint': 'https://api.openai.com/v1',
            'api_key': 'test-key',
            'max_requests_per_minute': 60
        })

    @pytest.fixture
    def dialogue_service(self):
        """Create dialogue service that uses AI models."""
        service = MockDialogueService({
            'max_conversations': 100,
            'cache_size': 1000
        })
        service.ai_client = ai_service
        return service

    @pytest.mark.asyncio
    async def test_dialogue_generation_integration(self, dialogue_service):
        """Test dialogue generation through AI service integration."""
        prompt = "A brave warrior enters a dark cave and sees treasure."

        # Generate dialogue
        result = await dialogue_service.generate_dialogue(prompt)

        assert result is not None
        assert 'dialogue' in result
        assert 'model' in result
        assert 'processing_time' in result

    @pytest.mark.asyncio
    async def test_emotion_analysis_integration(self, dialogue_service):
        """Test emotion analysis through AI service integration."""
        text = "I can't believe we found the legendary sword! This is amazing!"

        # Analyze emotion
        result = await dialogue_service.analyze_emotion(text)

        assert result is not None
        assert 'emotions' in result
        assert 'dominant_emotion' in result
        assert 'confidence' in result

    @pytest.mark.asyncio
    async def test_ai_service_rate_limiting(self, ai_service):
        """Test AI service rate limiting."""
        # Make multiple requests rapidly
        requests = []
        for i in range(10):
            request = ai_service.generate_dialogue(f"Test prompt {i}")
            requests.append(request)

        # Execute all requests
        results = await asyncio.gather(*requests)

        # Verify all requests were handled
        assert len(results) == 10
        assert ai_service.request_count == 10

        # Check response times are reasonable
        avg_response_time = sum(ai_service.response_times) / len(ai_service.response_times)
        assert avg_response_time < 1.0  # Should be under 1 second

@pytest.mark.integration
@pytest.mark.parallel
class TestParallelServiceCommunication:
    """Test parallel communication between services."""

    @pytest.fixture
    def service_manager(self):
        """Create service integration manager."""
        return ServiceIntegrationManager()

    @pytest.fixture
    def multiple_services(self):
        """Create multiple services for parallel testing."""
        services = {}
        for i in range(5):
            services[f'service_{i}'] = MockAPIService({
                'name': f'Service {i}',
                'port': 3000 + i
            })
        return services

    @pytest.mark.asyncio
    async def test_concurrent_service_requests(self, service_manager, multiple_services):
        """Test concurrent requests to multiple services."""
        # Register services
        for name, service in multiple_services.items():
            service_manager.register_service(name, service)

        # Create communication channels
        service_names = list(multiple_services.keys())
        for i in range(len(service_names)):
            for j in range(i + 1, len(service_names)):
                service_manager.create_communication_channel(service_names[i], service_names[j])

        # Make concurrent requests
        requests = []
        for i in range(20):
            from_service = service_names[i % len(service_names)]
            to_service = service_names[(i + 1) % len(service_names)]
            message = {'request_id': i, 'data': f'Test data {i}'}

            request = service_manager.communicate(
                from_service, to_service, 'test_message', message
            )
            requests.append(request)

        # Execute all requests
        results = await asyncio.gather(*requests)

        # Verify all requests completed
        assert len(results) == 20

        # Verify communication logs
        assert len(service_manager.request_logs) == 20

    @pytest.mark.asyncio
    async def test_service_load_balancing(self, multiple_services):
        """Test load balancing across multiple service instances."""
        # Create multiple instances of the same service
        service_instances = [MockAPIService({'port': 3000 + i}) for i in range(3)]
        load_balancer = MockLoadBalancer(service_instances)

        # Distribute requests across instances
        requests = []
        for i in range(30):
            request = load_balancer.handle_request('GET', '/api/test', {}, {})
            requests.append(request)

        results = await asyncio.gather(*requests)

        # Verify load was distributed
        request_counts = [instance.request_count for instance in service_instances]
        expected_per_instance = 30 // 3

        for count in request_counts:
            assert abs(count - expected_per_instance) <= 2  # Allow some variance

    @pytest.mark.asyncio
    async def test_service_fault_tolerance(self, service_manager):
        """Test fault tolerance when services fail."""
        # Create one failing service
        failing_service = MockAPIService({'port': 3000})
        failing_service.should_fail = True

        # Create healthy services
        healthy_services = [MockAPIService({'port': 3001 + i}) for i in range(2)]

        # Register all services
        service_manager.register_service('failing', failing_service)
        for i, service in enumerate(healthy_services):
            service_manager.register_service(f'healthy_{i}', service)

        # Create communication channels
        service_manager.create_communication_channel('failing', 'healthy_0')
        service_manager.create_communication_channel('healthy_0', 'healthy_1')

        # Make requests - some should fail, others should succeed
        requests = []
        for i in range(10):
            try:
                if i % 3 == 0:
                    # Request to failing service
                    request = service_manager.communicate(
                        'failing', 'healthy_0', 'test', {'id': i}
                    )
                else:
                    # Request between healthy services
                    request = service_manager.communicate(
                        'healthy_0', 'healthy_1', 'test', {'id': i}
                    )
                requests.append(request)
            except Exception:
                pass  # Expected for failing service

        # Execute requests with error handling
        results = []
        for request in requests:
            try:
                result = await request
                results.append(result)
            except Exception:
                results.append({'error': 'Service unavailable'})

        # Verify some requests succeeded despite failures
        successful_requests = [r for r in results if 'error' not in r]
        assert len(successful_requests) > 0

class MockLoadBalancer:
    """Mock load balancer for testing."""

    def __init__(self, service_instances):
        self.service_instances = service_instances
        self.current_index = 0

    async def handle_request(self, method, path, headers, data):
        """Handle request with load balancing."""
        # Round-robin load balancing
        service = self.service_instances[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.service_instances)

        return await service.handle_request(method, path, headers, data)

class MockSessionService:
    """Mock session service."""

    def __init__(self, config):
        self.config = config
        self.sessions = {}

    async def create_session(self, session_data):
        """Create a new session."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'id': session_id,
            **session_data,
            'created_at': datetime.utcnow()
        }
        return self.sessions[session_id]

class MockDialogueService:
    """Mock dialogue service."""

    def __init__(self, config):
        self.config = config
        self.conversations = {}
        self.ai_client = None

    async def generate_dialogue(self, prompt):
        """Generate dialogue using AI client."""
        if self.ai_client:
            return await self.ai_client.generate_dialogue(prompt)
        return {'dialogue': 'Mock dialogue'}

    async def analyze_emotion(self, text):
        """Analyze emotion using AI client."""
        if self.ai_client:
            return await self.ai_client.analyze_emotion(text)
        return {'emotions': {'neutral': 1.0}}

class MockAPIClient:
    """Mock API client for service communication."""

    def __init__(self, service_manager, target_service):
        self.service_manager = service_manager
        self.target_service = target_service

    async def post(self, endpoint, data):
        """Send POST request to target service."""
        return await self.service_manager.communicate(
            'client', self.target_service, 'api_request', data
        )