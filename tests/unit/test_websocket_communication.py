"""
Unit tests for WebSocket communication in the DMLogn8n system.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import socketio

# Mock WebSocket classes for testing
class MockSocketIOClient:
    """Mock Socket.IO client for testing."""

    def __init__(self, server_url):
        self.server_url = server_url
        self.connected = False
        self.rooms = set()
        self.event_handlers = {}
        self.sent_events = []
        self.received_events = []

    async def connect(self):
        """Connect to the server."""
        self.connected = True
        return True

    async def disconnect(self):
        """Disconnect from the server."""
        self.connected = False
        self.rooms.clear()
        return True

    async def emit(self, event_name, data, room=None):
        """Emit an event to the server."""
        event = {
            'event': event_name,
            'data': data,
            'room': room,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.sent_events.append(event)
        return True

    def on(self, event_name, handler):
        """Register event handler."""
        self.event_handlers[event_name] = handler

    def off(self, event_name, handler=None):
        """Remove event handler."""
        if event_name in self.event_handlers:
            del self.event_handlers[event_name]

    async def join_room(self, room_name):
        """Join a room."""
        if self.connected:
            self.rooms.add(room_name)
            return True
        return False

    async def leave_room(self, room_name):
        """Leave a room."""
        if room_name in self.rooms:
            self.rooms.remove(room_name)
            return True
        return False

    def simulate_server_event(self, event_name, data):
        """Simulate receiving an event from the server."""
        self.received_events.append({
            'event': event_name,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })

        if event_name in self.event_handlers:
            handler = self.event_handlers[event_name]
            if asyncio.iscoroutinefunction(handler):
                asyncio.create_task(handler(data))
            else:
                handler(data)

class MockWebSocketServer:
    """Mock WebSocket server for testing."""

    def __init__(self):
        self.clients = {}
        self.rooms = {}
        self.message_handlers = {}
        self.connected_clients = set()

    async def handle_connection(self, client_id, client):
        """Handle new client connection."""
        self.connected_clients.add(client_id)
        self.clients[client_id] = client

        # Simulate connection event
        await self.emit_to_client(client_id, 'connect', {
            'client_id': client_id,
            'timestamp': datetime.utcnow().isoformat()
        })

    async def handle_disconnection(self, client_id):
        """Handle client disconnection."""
        if client_id in self.connected_clients:
            self.connected_clients.remove(client_id)

        # Remove client from all rooms
        for room_name, room_clients in self.rooms.items():
            if client_id in room_clients:
                room_clients.remove(client_id)

        if client_id in self.clients:
            del self.clients[client_id]

    async def handle_join_room(self, client_id, room_name):
        """Handle client joining a room."""
        if room_name not in self.rooms:
            self.rooms[room_name] = set()

        self.rooms[room_name].add(client_id)

        # Notify room members
        await self.emit_to_room(room_name, 'user_joined', {
            'client_id': client_id,
            'room': room_name,
            'timestamp': datetime.utcnow().isoformat()
        }, exclude_client=client_id)

    async def handle_leave_room(self, client_id, room_name):
        """Handle client leaving a room."""
        if room_name in self.rooms and client_id in self.rooms[room_name]:
            self.rooms[room_name].remove(client_id)

            # Notify room members
            await self.emit_to_room(room_name, 'user_left', {
                'client_id': client_id,
                'room': room_name,
                'timestamp': datetime.utcnow().isoformat()
            })

    async def handle_client_message(self, client_id, event_name, data):
        """Handle message from client."""
        # Store message
        if client_id not in self.message_handlers:
            self.message_handlers[client_id] = []

        self.message_handlers[client_id].append({
            'event': event_name,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        })

        # Route to appropriate handler
        if event_name == 'join-room':
            await self.handle_join_room(client_id, data.get('room'))
        elif event_name == 'leave-room':
            await self.handle_leave_room(client_id, data.get('room'))
        elif event_name == 'broadcast':
            await self.emit_to_room(data.get('room'), data.get('event'), data.get('data'))
        else:
            # Echo back to client for testing
            await self.emit_to_client(client_id, f'{event_name}_response', {
                'original_data': data,
                'timestamp': datetime.utcnow().isoformat()
            })

    async def emit_to_client(self, client_id, event_name, data):
        """Emit event to specific client."""
        if client_id in self.clients:
            client = self.clients[client_id]
            client.simulate_server_event(event_name, data)

    async def emit_to_room(self, room_name, event_name, data, exclude_client=None):
        """Emit event to all clients in a room."""
        if room_name in self.rooms:
            for client_id in self.rooms[room_name]:
                if client_id != exclude_client:
                    await self.emit_to_client(client_id, event_name, data)

    async def broadcast(self, event_name, data):
        """Broadcast event to all connected clients."""
        for client_id in self.connected_clients:
            await self.emit_to_client(client_id, event_name, data)

class MockRealtimeService:
    """Mock real-time service for testing."""

    def __init__(self, websocket_server):
        self.server = websocket_server
        self.active_sessions = {}
        self.agent_states = {}

    async def handle_agent_update(self, session_id, agent_id, update_data):
        """Handle agent state update."""
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                'agents': {},
                'players': set(),
                'created_at': datetime.utcnow()
            }

        # Update agent state
        if agent_id not in self.active_sessions[session_id]['agents']:
            self.active_sessions[session_id]['agents'][agent_id] = {}

        self.active_sessions[session_id]['agents'][agent_id].update(update_data)
        self.active_sessions[session_id]['agents'][agent_id]['updated_at'] = datetime.utcnow()

        # Broadcast to session room
        await self.server.emit_to_room(f'session_{session_id}', 'agent_update', {
            'agent_id': agent_id,
            'session_id': session_id,
            'update_data': update_data,
            'timestamp': datetime.utcnow().isoformat()
        })

    async def handle_game_event(self, session_id, event_data):
        """Handle game event."""
        if session_id not in self.active_sessions:
            return

        # Broadcast event to session room
        await self.server.emit_to_room(f'session_{session_id}', 'game_event', {
            'session_id': session_id,
            'event_data': event_data,
            'timestamp': datetime.utcnow().isoformat()
        })

    async def handle_player_action(self, session_id, player_id, action_data):
        """Handle player action."""
        # Broadcast to session room
        await self.server.emit_to_room(f'session_{session_id}', 'player_action', {
            'session_id': session_id,
            'player_id': player_id,
            'action_data': action_data,
            'timestamp': datetime.utcnow().isoformat()
        })

@pytest.mark.unit
@pytest.mark.websocket
class TestWebSocketConnection:
    """Test cases for WebSocket connection management."""

    @pytest.fixture
    def mock_server(self):
        """Create mock WebSocket server."""
        return MockWebSocketServer()

    @pytest.fixture
    def mock_client(self):
        """Create mock WebSocket client."""
        return MockSocketIOClient('ws://localhost:3000')

    @pytest.mark.asyncio
    async def test_client_connection(self, mock_server, mock_client):
        """Test client connection to server."""
        client_id = 'test_client_001'

        # Connect client to server
        await mock_server.handle_connection(client_id, mock_client)
        await mock_client.connect()

        assert client_id in mock_server.connected_clients
        assert mock_client.connected
        assert mock_client.received_events[-1]['event'] == 'connect'

    @pytest.mark.asyncio
    async def test_client_disconnection(self, mock_server, mock_client):
        """Test client disconnection from server."""
        client_id = 'test_client_001'

        # Connect then disconnect
        await mock_server.handle_connection(client_id, mock_client)
        await mock_client.disconnect()
        await mock_server.handle_disconnection(client_id)

        assert client_id not in mock_server.connected_clients
        assert not mock_client.connected
        assert client_id not in mock_server.clients

    @pytest.mark.asyncio
    async def test_multiple_client_connections(self, mock_server):
        """Test multiple clients connecting simultaneously."""
        client_count = 10
        clients = {}

        # Create and connect multiple clients
        for i in range(client_count):
            client_id = f'test_client_{i:03d}'
            client = MockSocketIOClient('ws://localhost:3000')
            clients[client_id] = client

            await mock_server.handle_connection(client_id, client)
            await client.connect()

        assert len(mock_server.connected_clients) == client_count
        assert len(mock_server.clients) == client_count

        # Verify all clients received connection event
        for client_id, client in clients.items():
            assert client.connected
            assert client.received_events[-1]['event'] == 'connect'

    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, mock_server, mock_client):
        """Test complete connection lifecycle."""
        client_id = 'test_client_001'

        # Connect
        await mock_server.handle_connection(client_id, mock_client)
        await mock_client.connect()
        assert mock_client.connected

        # Disconnect
        await mock_client.disconnect()
        await mock_server.handle_disconnection(client_id)
        assert not mock_client.connected

        # Verify cleanup
        assert client_id not in mock_server.connected_clients
        assert client_id not in mock_server.clients

@pytest.mark.unit
@pytest.mark.websocket
class TestRoomManagement:
    """Test cases for WebSocket room management."""

    @pytest.fixture
    def mock_server(self):
        """Create mock WebSocket server."""
        return MockWebSocketServer()

    @pytest.fixture
    def mock_client(self):
        """Create mock WebSocket client."""
        return MockSocketIOClient('ws://localhost:3000')

    @pytest.mark.asyncio
    async def test_join_room_success(self, mock_server, mock_client):
        """Test successful room joining."""
        client_id = 'test_client_001'
        room_name = 'test_room_001'

        # Connect and join room
        await mock_server.handle_connection(client_id, mock_client)
        await mock_client.connect()
        await mock_client.join_room(room_name)
        await mock_server.handle_join_room(client_id, room_name)

        assert room_name in mock_server.rooms
        assert client_id in mock_server.rooms[room_name]
        assert room_name in mock_client.rooms

    @pytest.mark.asyncio
    async def test_leave_room_success(self, mock_server, mock_client):
        """Test successful room leaving."""
        client_id = 'test_client_001'
        room_name = 'test_room_001'

        # Connect, join, then leave room
        await mock_server.handle_connection(client_id, mock_client)
        await mock_client.connect()
        await mock_client.join_room(room_name)
        await mock_server.handle_join_room(client_id, room_name)

        await mock_client.leave_room(room_name)
        await mock_server.handle_leave_room(client_id, room_name)

        assert client_id not in mock_server.rooms.get(room_name, set())
        assert room_name not in mock_client.rooms

    @pytest.mark.asyncio
    async def test_multiple_clients_in_room(self, mock_server):
        """Test multiple clients joining the same room."""
        client_count = 5
        room_name = 'shared_room_001'
        clients = {}

        # Create and connect clients
        for i in range(client_count):
            client_id = f'client_{i:03d}'
            client = MockSocketIOClient('ws://localhost:3000')
            clients[client_id] = client

            await mock_server.handle_connection(client_id, client)
            await client.connect()
            await client.join_room(room_name)
            await mock_server.handle_join_room(client_id, room_name)

        # Verify all clients are in the room
        assert room_name in mock_server.rooms
        assert len(mock_server.rooms[room_name]) == client_count

        for client_id in clients:
            assert client_id in mock_server.rooms[room_name]
            assert room_name in clients[client_id].rooms

    @pytest.mark.asyncio
    async def test_client_disconnection_room_cleanup(self, mock_server, mock_client):
        """Test room cleanup when client disconnects."""
        client_id = 'test_client_001'
        room_name = 'test_room_001'

        # Connect, join room, then disconnect
        await mock_server.handle_connection(client_id, mock_client)
        await mock_client.connect()
        await mock_client.join_room(room_name)
        await mock_server.handle_join_room(client_id, room_name)

        # Verify client is in room
        assert client_id in mock_server.rooms[room_name]

        # Disconnect
        await mock_client.disconnect()
        await mock_server.handle_disconnection(client_id)

        # Verify room cleanup
        assert client_id not in mock_server.rooms.get(room_name, set())

@pytest.mark.unit
@pytest.mark.websocket
class TestMessageHandling:
    """Test cases for WebSocket message handling."""

    @pytest.fixture
    def mock_server(self):
        """Create mock WebSocket server."""
        return MockWebSocketServer()

    @pytest.fixture
    def mock_client(self):
        """Create mock WebSocket client."""
        return MockSocketIOClient('ws://localhost:3000')

    @pytest.mark.asyncio
    async def test_send_message_to_server(self, mock_server, mock_client):
        """Test sending message from client to server."""
        client_id = 'test_client_001'
        event_name = 'test_message'
        data = {'content': 'Hello, server!', 'timestamp': datetime.utcnow().isoformat()}

        # Connect and send message
        await mock_server.handle_connection(client_id, mock_client)
        await mock_client.connect()
        await mock_client.emit(event_name, data)
        await mock_server.handle_client_message(client_id, event_name, data)

        # Verify server received message
        assert client_id in mock_server.message_handlers
        messages = mock_server.message_handlers[client_id]
        assert len(messages) == 1
        assert messages[0]['event'] == event_name
        assert messages[0]['data'] == data

    @pytest.mark.asyncio
    async def test_receive_message_from_server(self, mock_server, mock_client):
        """Test receiving message from server."""
        client_id = 'test_client_001'
        event_name = 'server_message'
        data = {'content': 'Hello, client!', 'timestamp': datetime.utcnow().isoformat()}

        # Connect and receive message
        await mock_server.handle_connection(client_id, mock_client)
        await mock_client.connect()

        # Server sends message to client
        await mock_server.emit_to_client(client_id, event_name, data)

        # Verify client received message
        assert len(mock_client.received_events) > 0
        received = mock_client.received_events[-1]
        assert received['event'] == event_name
        assert received['data'] == data

    @pytest.mark.asyncio
    async def test_broadcast_to_room(self, mock_server):
        """Test broadcasting message to room."""
        client_count = 3
        room_name = 'broadcast_room'
        clients = {}
        sender_id = 'sender_001'

        # Create clients and join room
        for i in range(client_count):
            client_id = f'client_{i:03d}'
            client = MockSocketIOClient('ws://localhost:3000')
            clients[client_id] = client

            await mock_server.handle_connection(client_id, client)
            await client.connect()
            await client.join_room(room_name)
            await mock_server.handle_join_room(client_id, room_name)

        # Broadcast message to room (excluding sender)
        broadcast_data = {'message': 'Hello, room!', 'sender': sender_id}
        await mock_server.emit_to_room(room_name, 'broadcast', broadcast_data, exclude_client=sender_id)

        # Verify all clients except sender received message
        for client_id, client in clients.items():
            if client_id != sender_id:
                assert len(client.received_events) > 0
                received = client.received_events[-1]
                assert received['event'] == 'broadcast'
                assert received['data'] == broadcast_data

    @pytest.mark.asyncio
    async def test_event_handlers(self, mock_server, mock_client):
        """Test event handler registration and execution."""
        client_id = 'test_client_001'
        received_events = []

        # Define event handler
        async def custom_handler(data):
            received_events.append(data)

        # Connect and register handler
        await mock_server.handle_connection(client_id, mock_client)
        await mock_client.connect()
        mock_client.on('custom_event', custom_handler)

        # Simulate server event
        test_data = {'message': 'Custom event data'}
        mock_client.simulate_server_event('custom_event', test_data)

        # Wait for async handler
        await asyncio.sleep(0.01)

        # Verify handler was called
        assert len(received_events) == 1
        assert received_events[0] == test_data

    @pytest.mark.asyncio
    async def test_message_persistence(self, mock_server, mock_client):
        """Test message persistence in room."""
        client_id = 'test_client_001'
        room_name = 'persistent_room'

        # Connect and join room
        await mock_server.handle_connection(client_id, mock_client)
        await mock_client.connect()
        await mock_client.join_room(room_name)
        await mock_server.handle_join_room(client_id, room_name)

        # Send multiple messages
        messages = [
            {'event': 'message_1', 'data': {'content': 'First message'}},
            {'event': 'message_2', 'data': {'content': 'Second message'}},
            {'event': 'message_3', 'data': {'content': 'Third message'}}
        ]

        for msg in messages:
            await mock_client.emit(msg['event'], msg['data'])
            await mock_server.handle_client_message(client_id, msg['event'], msg['data'])

        # Verify message persistence
        assert len(mock_server.message_handlers[client_id]) == len(messages)
        for i, msg in enumerate(messages):
            stored_msg = mock_server.message_handlers[client_id][i]
            assert stored_msg['event'] == msg['event']
            assert stored_msg['data'] == msg['data']

@pytest.mark.unit
@pytest.mark.websocket
@pytest.mark.parallel
class TestParallelWebSocketOperations:
    """Test cases for parallel WebSocket operations."""

    @pytest.fixture
    def mock_server(self):
        """Create mock WebSocket server."""
        return MockWebSocketServer()

    @pytest.mark.asyncio
    async def test_concurrent_client_connections(self, mock_server):
        """Test concurrent client connections."""
        client_count = 50

        async def connect_client(client_id):
            client = MockSocketIOClient('ws://localhost:3000')
            await mock_server.handle_connection(client_id, client)
            await client.connect()
            return client

        # Connect clients concurrently
        tasks = [
            connect_client(f'client_{i:03d}')
            for i in range(client_count)
        ]

        clients = await asyncio.gather(*tasks)

        # Verify all clients connected successfully
        assert len(mock_server.connected_clients) == client_count
        assert len(clients) == client_count

        for client in clients:
            assert client.connected

    @pytest.mark.asyncio
    async def test_concurrent_room_operations(self, mock_server):
        """Test concurrent room operations."""
        client_count = 20
        room_count = 5
        clients = {}

        # Connect clients concurrently
        connect_tasks = []
        for i in range(client_count):
            client_id = f'client_{i:03d}'
            client = MockSocketIOClient('ws://localhost:3000')
            clients[client_id] = client

            task = mock_server.handle_connection(client_id, client)
            connect_tasks.append(task)

        await asyncio.gather(*connect_tasks)

        # Connect all clients
        for client in clients.values():
            await client.connect()

        # Join rooms concurrently
        join_tasks = []
        for i, client_id in enumerate(clients.keys()):
            room_name = f'room_{i % room_count}'
            client = clients[client_id]
            task = mock_server.handle_join_room(client_id, room_name)
            join_tasks.append(task)
            await client.join_room(room_name)

        await asyncio.gather(*join_tasks)

        # Verify room distribution
        for room_idx in range(room_count):
            room_name = f'room_{room_idx}'
            expected_clients = client_count // room_count
            assert len(mock_server.rooms.get(room_name, set())) == expected_clients

    @pytest.mark.asyncio
    async def test_concurrent_messaging(self, mock_server):
        """Test concurrent messaging in multiple rooms."""
        client_count = 15
        message_count_per_client = 10
        clients = {}

        # Setup clients and rooms
        for i in range(client_count):
            client_id = f'client_{i:03d}'
            client = MockSocketIOClient('ws://localhost:3000')
            clients[client_id] = client

            await mock_server.handle_connection(client_id, client)
            await client.connect()

            # Join different rooms
            room_name = f'room_{i % 3}'
            await client.join_room(room_name)
            await mock_server.handle_join_room(client_id, room_name)

        # Send messages concurrently
        message_tasks = []
        for client_id, client in clients.items():
            for msg_idx in range(message_count_per_client):
                event_name = f'message_{msg_idx}'
                data = {
                    'client_id': client_id,
                    'message_index': msg_idx,
                    'content': f'Concurrent message {msg_idx} from {client_id}'
                }

                task = mock_server.handle_client_message(client_id, event_name, data)
                message_tasks.append(task)

        await asyncio.gather(*message_tasks)

        # Verify all messages were processed
        total_messages = client_count * message_count_per_client
        processed_messages = sum(
            len(messages) for messages in mock_server.message_handlers.values()
        )
        assert processed_messages == total_messages

    @pytest.mark.asyncio
    async def test_high_frequency_messaging(self, mock_server):
        """Test high-frequency messaging performance."""
        client_count = 5
        messages_per_second = 100
        test_duration = 2.0  # seconds
        clients = {}

        # Setup clients
        for i in range(client_count):
            client_id = f'client_{i:03d}'
            client = MockSocketIOClient('ws://localhost:3000')
            clients[client_id] = client

            await mock_server.handle_connection(client_id, client)
            await client.connect()

        # High-frequency messaging
        async def send_high_frequency_messages(client_id, client):
            message_count = 0
            start_time = asyncio.get_event_loop().time()
            end_time = start_time + test_duration

            while asyncio.get_event_loop().time() < end_time:
                event_name = 'high_freq_message'
                data = {
                    'client_id': client_id,
                    'message_count': message_count,
                    'timestamp': datetime.utcnow().isoformat()
                }

                await client.emit(event_name, data)
                await mock_server.handle_client_message(client_id, event_name, data)
                message_count += 1

                # Rate limiting
                await asyncio.sleep(1.0 / messages_per_second)

            return message_count

        # Run high-frequency messaging for all clients
        tasks = [
            send_high_frequency_messages(client_id, client)
            for client_id, client in clients.items()
        ]

        message_counts = await asyncio.gather(*tasks)

        # Verify message counts
        expected_per_client = int(test_duration * messages_per_second)
        for count in message_counts:
            assert count >= expected_per_client * 0.9  # Allow 10% tolerance

        total_messages = sum(message_counts)
        processed_messages = sum(
            len(messages) for messages in mock_server.message_handlers.values()
        )
        assert processed_messages == total_messages

@pytest.mark.unit
@pytest.mark.websocket
class TestRealtimeService:
    """Test cases for real-time service integration."""

    @pytest.fixture
    def mock_server(self):
        """Create mock WebSocket server."""
        return MockWebSocketServer()

    @pytest.fixture
    def realtime_service(self, mock_server):
        """Create real-time service with mock server."""
        return MockRealtimeService(mock_server)

    @pytest.mark.asyncio
    async def test_agent_update_broadcast(self, mock_server, realtime_service):
        """Test agent update broadcasting to session."""
        session_id = 'test_session_001'
        agent_id = 'test_agent_001'
        update_data = {
            'health': 85,
            'position': {'x': 10, 'y': 15},
            'status': 'active'
        }

        # Handle agent update
        await realtime_service.handle_agent_update(session_id, agent_id, update_data)

        # Verify session was created and updated
        assert session_id in realtime_service.active_sessions
        assert agent_id in realtime_service.active_sessions[session_id]['agents']
        assert realtime_service.active_sessions[session_id]['agents'][agent_id]['health'] == 85

    @pytest.mark.asyncio
    async def test_game_event_broadcast(self, mock_server, realtime_service):
        """Test game event broadcasting to session."""
        session_id = 'test_session_001'
        event_data = {
            'type': 'combat',
            'attacker': 'agent_001',
            'defender': 'agent_002',
            'damage': 15,
            'description': 'Agent 001 attacks Agent 002 for 15 damage'
        }

        # Create session first
        realtime_service.active_sessions[session_id] = {
            'agents': {},
            'players': set(),
            'created_at': datetime.utcnow()
        }

        # Handle game event
        await realtime_service.handle_game_event(session_id, event_data)

        # Verify event was processed (in real implementation, would be broadcast to room)
        assert session_id in realtime_service.active_sessions

    @pytest.mark.asyncio
    async def test_player_action_broadcast(self, mock_server, realtime_service):
        """Test player action broadcasting to session."""
        session_id = 'test_session_001'
        player_id = 'player_001'
        action_data = {
            'type': 'move',
            'from': {'x': 10, 'y': 15},
            'to': {'x': 12, 'y': 17},
            'speed': 'normal'
        }

        # Create session first
        realtime_service.active_sessions[session_id] = {
            'agents': {},
            'players': set(),
            'created_at': datetime.utcnow()
        }

        # Handle player action
        await realtime_service.handle_player_action(session_id, player_id, action_data)

        # Verify action was processed
        assert session_id in realtime_service.active_sessions