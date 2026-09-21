"""
Unit tests for agent services in the DMLogn8n parallel multi-agent system.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import json

# Import the services we're testing
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

# Mock imports for testing
class MockAgentService:
    """Mock Agent Service for unit testing."""

    def __init__(self, config):
        self.config = config
        self.agents = {}
        self.agent_states = {}
        self.decision_queue = asyncio.Queue()
        self.action_queue = asyncio.Queue()

    async def create_agent(self, agent_data):
        """Create a new agent."""
        agent_id = agent_data.get('agent_id')
        if agent_id in self.agents:
            raise ValueError(f"Agent {agent_id} already exists")

        self.agents[agent_id] = {
            **agent_data,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'status': 'active'
        }
        self.agent_states[agent_id] = 'idle'

        return self.agents[agent_id]

    async def get_agent(self, agent_id):
        """Get agent by ID."""
        return self.agents.get(agent_id)

    async def update_agent(self, agent_id, updates):
        """Update agent data."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        self.agents[agent_id].update(updates)
        self.agents[agent_id]['updated_at'] = datetime.utcnow()

        return self.agents[agent_id]

    async def delete_agent(self, agent_id):
        """Delete an agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        del self.agents[agent_id]
        del self.agent_states[agent_id]

        return True

    async def make_decision(self, agent_id, context):
        """Make a decision for an agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        # Mock decision making logic
        decision = {
            'agent_id': agent_id,
            'action': 'wait',
            'target': None,
            'timestamp': datetime.utcnow().isoformat(),
            'reasoning': 'Mock decision for testing'
        }

        await self.decision_queue.put(decision)
        return decision

    async def execute_action(self, agent_id, action):
        """Execute an action for an agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        self.agent_states[agent_id] = 'acting'

        # Mock action execution
        result = {
            'agent_id': agent_id,
            'action': action,
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'effects': []
        }

        await self.action_queue.put(result)
        self.agent_states[agent_id] = 'idle'

        return result

class MockDecisionEngine:
    """Mock Decision Engine for testing."""

    def __init__(self, config):
        self.config = config
        self.decision_cache = {}
        self.processing_time = 0.1  # seconds

    async def evaluate_context(self, agent_id, context):
        """Evaluate context for decision making."""
        await asyncio.sleep(self.processing_time)  # Simulate processing time

        return {
            'agent_id': agent_id,
            'context_score': 0.8,
            'available_actions': ['move', 'attack', 'defend', 'wait'],
            'environmental_factors': ['visibility', 'terrain', 'allies_nearby'],
            'timestamp': datetime.utcnow().isoformat()
        }

    async def select_action(self, agent_id, evaluated_context, personality):
        """Select best action based on context and personality."""
        await asyncio.sleep(self.processing_time)

        # Simple action selection logic for testing
        if personality.get('brave', 0) > 0.7:
            selected_action = 'attack'
        elif personality.get('cautious', 0) > 0.7:
            selected_action = 'defend'
        else:
            selected_action = 'wait'

        return {
            'agent_id': agent_id,
            'selected_action': selected_action,
            'confidence': 0.85,
            'alternatives': ['move', 'wait'],
            'timestamp': datetime.utcnow().isoformat()
        }

@pytest.mark.unit
class TestAgentService:
    """Test cases for Agent Service."""

    @pytest.fixture
    def agent_service(self):
        """Create agent service instance for testing."""
        config = {
            'max_agents': 1000,
            'decision_timeout': 5.0,
            'action_timeout': 10.0
        }
        return MockAgentService(config)

    @pytest.fixture
    def sample_agent_data(self, sample_agent_data):
        """Provide sample agent data."""
        return sample_agent_data

    @pytest.mark.asyncio
    async def test_create_agent_success(self, agent_service, sample_agent_data):
        """Test successful agent creation."""
        result = await agent_service.create_agent(sample_agent_data)

        assert result['agent_id'] == sample_agent_data['agent_id']
        assert result['name'] == sample_agent_data['name']
        assert result['status'] == 'active'
        assert 'created_at' in result
        assert 'updated_at' in result

    @pytest.mark.asyncio
    async def test_create_agent_duplicate(self, agent_service, sample_agent_data):
        """Test creating duplicate agent raises error."""
        await agent_service.create_agent(sample_agent_data)

        with pytest.raises(ValueError, match="already exists"):
            await agent_service.create_agent(sample_agent_data)

    @pytest.mark.asyncio
    async def test_get_agent_exists(self, agent_service, sample_agent_data):
        """Test getting existing agent."""
        await agent_service.create_agent(sample_agent_data)

        result = await agent_service.get_agent(sample_agent_data['agent_id'])

        assert result is not None
        assert result['agent_id'] == sample_agent_data['agent_id']

    @pytest.mark.asyncio
    async def test_get_agent_not_exists(self, agent_service):
        """Test getting non-existent agent returns None."""
        result = await agent_service.get_agent('non_existent_agent')
        assert result is None

    @pytest.mark.asyncio
    async def test_update_agent_success(self, agent_service, sample_agent_data):
        """Test successful agent update."""
        await agent_service.create_agent(sample_agent_data)

        updates = {
            'health': 30,
            'status': 'injured'
        }

        result = await agent_service.update_agent(
            sample_agent_data['agent_id'],
            updates
        )

        assert result['health'] == 30
        assert result['status'] == 'injured'
        assert result['updated_at'] > result['created_at']

    @pytest.mark.asyncio
    async def test_update_agent_not_exists(self, agent_service):
        """Test updating non-existent agent raises error."""
        with pytest.raises(ValueError, match="not found"):
            await agent_service.update_agent('non_existent', {'health': 30})

    @pytest.mark.asyncio
    async def test_delete_agent_success(self, agent_service, sample_agent_data):
        """Test successful agent deletion."""
        await agent_service.create_agent(sample_agent_data)

        result = await agent_service.delete_agent(sample_agent_data['agent_id'])

        assert result is True
        assert await agent_service.get_agent(sample_agent_data['agent_id']) is None

    @pytest.mark.asyncio
    async def test_delete_agent_not_exists(self, agent_service):
        """Test deleting non-existent agent raises error."""
        with pytest.raises(ValueError, match="not found"):
            await agent_service.delete_agent('non_existent')

    @pytest.mark.asyncio
    async def test_make_decision_success(self, agent_service, sample_agent_data):
        """Test successful decision making."""
        await agent_service.create_agent(sample_agent_data)

        context = {
            'location': {'x': 10, 'y': 15},
            'nearby_allies': ['agent_002'],
            'nearby_enemies': ['enemy_001'],
            'objective': 'defend_position'
        }

        result = await agent_service.make_decision(
            sample_agent_data['agent_id'],
            context
        )

        assert result['agent_id'] == sample_agent_data['agent_id']
        assert 'action' in result
        assert 'timestamp' in result
        assert 'reasoning' in result

        # Check decision was queued
        assert not agent_service.decision_queue.empty()

    @pytest.mark.asyncio
    async def test_make_decision_agent_not_exists(self, agent_service):
        """Test decision making for non-existent agent raises error."""
        with pytest.raises(ValueError, match="not found"):
            await agent_service.make_decision('non_existent', {})

    @pytest.mark.asyncio
    async def test_execute_action_success(self, agent_service, sample_agent_data):
        """Test successful action execution."""
        await agent_service.create_agent(sample_agent_data)

        action = {
            'type': 'move',
            'target': {'x': 12, 'y': 17},
            'parameters': {'speed': 'normal'}
        }

        result = await agent_service.execute_action(
            sample_agent_data['agent_id'],
            action
        )

        assert result['agent_id'] == sample_agent_data['agent_id']
        assert result['success'] is True
        assert 'timestamp' in result
        assert 'effects' in result

        # Check agent state changes
        assert agent_service.agent_states[sample_agent_data['agent_id']] == 'idle'

    @pytest.mark.asyncio
    async def test_execute_action_agent_not_exists(self, agent_service):
        """Test action execution for non-existent agent raises error."""
        with pytest.raises(ValueError, match="not found"):
            await agent_service.execute_action('non_existent', {'type': 'move'})

@pytest.mark.unit
class TestDecisionEngine:
    """Test cases for Decision Engine."""

    @pytest.fixture
    def decision_engine(self):
        """Create decision engine instance for testing."""
        config = {
            'cache_size': 1000,
            'processing_timeout': 5.0,
            'parallel_processing': True
        }
        return MockDecisionEngine(config)

    @pytest.mark.asyncio
    async def test_evaluate_context_success(self, decision_engine):
        """Test successful context evaluation."""
        agent_id = 'test_agent_001'
        context = {
            'location': {'x': 10, 'y': 15},
            'health': 80,
            'nearby_allies': 2,
            'nearby_enemies': 1
        }

        result = await decision_engine.evaluate_context(agent_id, context)

        assert result['agent_id'] == agent_id
        assert 'context_score' in result
        assert isinstance(result['available_actions'], list)
        assert isinstance(result['environmental_factors'], list)
        assert 'timestamp' in result

    @pytest.mark.asyncio
    async def test_select_action_brave_personality(self, decision_engine):
        """Test action selection with brave personality."""
        agent_id = 'test_agent_001'
        evaluated_context = {
            'available_actions': ['attack', 'defend', 'wait']
        }
        personality = {
            'brave': 0.9,
            'cautious': 0.1
        }

        result = await decision_engine.select_action(
            agent_id,
            evaluated_context,
            personality
        )

        assert result['agent_id'] == agent_id
        assert result['selected_action'] == 'attack'
        assert 'confidence' in result
        assert isinstance(result['alternatives'], list)

    @pytest.mark.asyncio
    async def test_select_action_cautious_personality(self, decision_engine):
        """Test action selection with cautious personality."""
        agent_id = 'test_agent_001'
        evaluated_context = {
            'available_actions': ['attack', 'defend', 'wait']
        }
        personality = {
            'brave': 0.1,
            'cautious': 0.9
        }

        result = await decision_engine.select_action(
            agent_id,
            evaluated_context,
            personality
        )

        assert result['agent_id'] == agent_id
        assert result['selected_action'] == 'defend'

    @pytest.mark.asyncio
    async def test_select_action_balanced_personality(self, decision_engine):
        """Test action selection with balanced personality."""
        agent_id = 'test_agent_001'
        evaluated_context = {
            'available_actions': ['attack', 'defend', 'wait']
        }
        personality = {
            'brave': 0.5,
            'cautious': 0.5
        }

        result = await decision_engine.select_action(
            agent_id,
            evaluated_context,
            personality
        )

        assert result['agent_id'] == agent_id
        assert result['selected_action'] == 'wait'

@pytest.mark.unit
@pytest.mark.parallel
class TestParallelAgentProcessing:
    """Test cases for parallel agent processing capabilities."""

    @pytest.fixture
    def agent_service(self):
        """Create agent service instance for testing."""
        config = {
            'max_agents': 1000,
            'parallel_processing': True,
            'worker_count': 4
        }
        return MockAgentService(config)

    @pytest.mark.asyncio
    async def test_concurrent_agent_creation(self, agent_service, parallel_agent_factory):
        """Test creating multiple agents concurrently."""
        agent_count = 50
        agents = parallel_agent_factory(agent_count)

        # Create agents concurrently
        tasks = [
            agent_service.create_agent(agent_data)
            for agent_data in agents
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == agent_count

        # Verify all agents were created
        for i, result in enumerate(results):
            assert result['agent_id'] == agents[i]['agent_id']
            assert result['status'] == 'active'

    @pytest.mark.asyncio
    async def test_concurrent_decision_making(self, agent_service, parallel_agent_factory):
        """Test concurrent decision making for multiple agents."""
        agent_count = 20
        agents = parallel_agent_factory(agent_count)

        # Create agents first
        for agent_data in agents:
            await agent_service.create_agent(agent_data)

        # Make decisions concurrently
        context = {'test_context': True}
        tasks = [
            agent_service.make_decision(agent['agent_id'], context)
            for agent in agents
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == agent_count

        # Verify all decisions were made and queued
        for i, result in enumerate(results):
            assert result['agent_id'] == agents[i]['agent_id']
            assert 'action' in result

        assert agent_service.deciction_queue.qsize() == agent_count

    @pytest.mark.asyncio
    async def test_concurrent_action_execution(self, agent_service, parallel_agent_factory):
        """Test concurrent action execution for multiple agents."""
        agent_count = 15
        agents = parallel_agent_factory(agent_count)

        # Create agents first
        for agent_data in agents:
            await agent_service.create_agent(agent_data)

        # Execute actions concurrently
        action = {'type': 'test_action', 'parameters': {}}
        tasks = [
            agent_service.execute_action(agent['agent_id'], action)
            for agent in agents
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == agent_count

        # Verify all actions were executed
        for i, result in enumerate(results):
            assert result['agent_id'] == agents[i]['agent_id']
            assert result['success'] is True

    @pytest.mark.asyncio
    async def test_parallel_processing_limits(self, agent_service):
        """Test that parallel processing respects configured limits."""
        # Create service with low worker count
        limited_service = MockAgentService({'max_workers': 2})

        agent_count = 10
        agents = parallel_agent_factory(agent_count)

        # Monitor processing time to verify parallelism
        start_time = asyncio.get_event_loop().time()

        tasks = [
            limited_service.make_decision(
                agent['agent_id'],
                {'test': True}
            )
            for agent in agents
        ]

        results = await asyncio.gather(*tasks)

        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time

        assert len(results) == agent_count
        # Processing should be faster than sequential execution
        assert processing_time < agent_count * 0.5  # Allow some overhead

@pytest.mark.unit
@pytest.mark.agent
class TestAgentBehavior:
    """Test cases for agent behavior and logic."""

    @pytest.fixture
    def agent_service(self):
        """Create agent service instance for testing."""
        return MockAgentService({})

    @pytest.mark.asyncio
    async def test_agent_state_transitions(self, agent_service, sample_agent_data):
        """Test agent state transitions during execution."""
        await agent_service.create_agent(sample_agent_data)
        agent_id = sample_agent_data['agent_id']

        # Initial state should be idle
        assert agent_service.agent_states[agent_id] == 'idle'

        # Execute action should change state to acting, then back to idle
        action = {'type': 'test_action'}
        await agent_service.execute_action(agent_id, action)

        assert agent_service.agent_states[agent_id] == 'idle'

    @pytest.mark.asyncio
    async def test_agent_decision_queueing(self, agent_service, sample_agent_data):
        """Test that agent decisions are properly queued."""
        await agent_service.create_agent(sample_agent_data)

        # Make multiple decisions
        for i in range(5):
            await agent_service.make_decision(
                sample_agent_data['agent_id'],
                {'iteration': i}
            )

        # Verify all decisions are queued
        assert agent_service.decision_queue.qsize() == 5

        # Verify queue order
        for i in range(5):
            decision = await agent_service.decision_queue.get()
            assert decision['agent_id'] == sample_agent_data['agent_id']

    @pytest.mark.asyncio
    async def test_agent_error_handling(self, agent_service):
        """Test error handling for agent operations."""
        # Test operations on non-existent agent
        with pytest.raises(ValueError):
            await agent_service.get_agent('non_existent')

        with pytest.raises(ValueError):
            await agent_service.update_agent('non_existent', {})

        with pytest.raises(ValueError):
            await agent_service.delete_agent('non_existent')

        with pytest.raises(ValueError):
            await agent_service.make_decision('non_existent', {})

        with pytest.raises(ValueError):
            await agent_service.execute_action('non_existent', {})