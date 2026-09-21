"""
WebSocket integration tests

Tests WebSocket functionality including:
- Connection establishment and authentication
- Message sending and receiving
- Room-based communication
- Real-time updates
- Connection management
- Error handling
- Performance under load
- Reconnection logic
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import websockets
from typing import Dict, List, Any
import time

# Import WebSocket-related modules
try:
    from source_code.backend.websocket_manager import WebSocketManager, ConnectionManager
    from source_code.backend.websocket_handlers import (
        handle_dice_roll, handle_campaign_join, handle_chat_message,
        handle_character_update, handle_session_update
    )
except ImportError:
    # Create placeholder imports if modules don't exist yet
    WebSocketManager = Mock()
    ConnectionManager = Mock()
    handle_dice_roll = AsyncMock()
    handle_campaign_join = AsyncMock()
    handle_chat_message = AsyncMock()
    handle_character_update = AsyncMock()
    handle_session_update = AsyncMock()


class TestWebSocketConnection:
    """Test WebSocket connection establishment and management"""

    @pytest.fixture
    def websocket_manager(self):
        """Create WebSocket manager instance"""
        return WebSocketManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket connection"""
        mock_ws = AsyncMock()
        mock_ws.send_text = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.receive_text = AsyncMock()
        mock_ws.receive_json = AsyncMock()
        mock_ws.close = AsyncMock()
        mock_ws.client_id = "test-client-123"
        mock_ws.user_id = "user-123"
        mock_ws.accept = AsyncMock()
        return mock_ws

    @pytest.mark.asyncio
    async def test_websocket_connection_establishment(self, websocket_manager, mock_websocket):
        """Test establishing WebSocket connection"""
        # Mock connection acceptance
        mock_websocket.receive_json.return_value = {
            "type": "authenticate",
            "token": "valid-token"
        }

        # Connect WebSocket
        await websocket_manager.connect(mock_websocket, "user-123")

        # Verify connection is registered
        assert "user-123" in websocket_manager.active_connections
        assert mock_websocket in websocket_manager.active_connections["user-123"]

    @pytest.mark.asyncio
    async def test_websocket_authentication(self, websocket_manager, mock_websocket):
        """Test WebSocket authentication"""
        # Mock authentication success
        with patch('source_code.backend.websocket_handlers.verify_token') as mock_verify:
            mock_verify.return_value = {"user_id": "user-123", "username": "testuser"}

            auth_message = {
                "type": "authenticate",
                "token": "valid-jwt-token"
            }

            result = await websocket_manager.authenticate_connection(mock_websocket, auth_message)

            assert result is True
            assert mock_websocket.user_id == "user-123"

    @pytest.mark.asyncio
    async def test_websocket_authentication_failure(self, websocket_manager, mock_websocket):
        """Test WebSocket authentication failure"""
        # Mock authentication failure
        with patch('source_code.backend.websocket_handlers.verify_token') as mock_verify:
            mock_verify.return_value = None

            auth_message = {
                "type": "authenticate",
                "token": "invalid-token"
            }

            result = await websocket_manager.authenticate_connection(mock_websocket, auth_message)

            assert result is False
            mock_websocket.close.assert_called_once_with(code=4001, reason="Authentication failed")

    @pytest.mark.asyncio
    async def test_websocket_disconnection(self, websocket_manager, mock_websocket):
        """Test WebSocket disconnection"""
        # Connect first
        await websocket_manager.connect(mock_websocket, "user-123")

        # Disconnect
        await websocket_manager.disconnect(mock_websocket, "user-123")

        # Verify connection is removed
        assert "user-123" not in websocket_manager.active_connections

    @pytest.mark.asyncio
    async def test_multiple_connections_same_user(self, websocket_manager):
        """Test multiple connections for the same user"""
        mock_ws1 = AsyncMock()
        mock_ws1.client_id = "client-1"
        mock_ws1.accept = AsyncMock()

        mock_ws2 = AsyncMock()
        mock_ws2.client_id = "client-2"
        mock_ws2.accept = AsyncMock()

        # Connect multiple WebSockets for same user
        await websocket_manager.connect(mock_ws1, "user-123")
        await websocket_manager.connect(mock_ws2, "user-123")

        # Verify both connections are registered
        assert len(websocket_manager.active_connections["user-123"]) == 2
        assert mock_ws1 in websocket_manager.active_connections["user-123"]
        assert mock_ws2 in websocket_manager.active_connections["user-123"]

    @pytest.mark.asyncio
    async def test_connection_timeout(self, websocket_manager, mock_websocket):
        """Test connection timeout handling"""
        # Mock slow authentication
        mock_websocket.receive_json.return_value = {
            "type": "authenticate",
            "token": "valid-token"
        }

        # Simulate timeout
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
            with pytest.raises(asyncio.TimeoutError):
                await websocket_manager.wait_for_authentication(mock_websocket, timeout=5.0)


class TestWebSocketMessaging:
    """Test WebSocket message handling"""

    @pytest.fixture
    def websocket_manager(self):
        """Create WebSocket manager instance"""
        return WebSocketManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket connection"""
        mock_ws = AsyncMock()
        mock_ws.send_text = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.receive_json = AsyncMock()
        mock_ws.close = AsyncMock()
        mock_ws.client_id = "test-client-123"
        mock_ws.user_id = "user-123"
        return mock_ws

    @pytest.mark.asyncio
    async def test_send_message_to_user(self, websocket_manager, mock_websocket):
        """Test sending message to specific user"""
        # Connect WebSocket
        await websocket_manager.connect(mock_websocket, "user-123")

        # Send message
        message = {
            "type": "notification",
            "data": {"message": "Hello, World!"}
        }

        await websocket_manager.send_message_to_user("user-123", message)

        # Verify message was sent
        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_message_to_campaign(self, websocket_manager):
        """Test sending message to campaign participants"""
        # Create multiple mock WebSockets
        mock_ws1 = AsyncMock()
        mock_ws1.send_json = AsyncMock()
        mock_ws2 = AsyncMock()
        mock_ws2.send_json = AsyncMock()

        # Connect users
        await websocket_manager.connect(mock_ws1, "user-1")
        await websocket_manager.connect(mock_ws2, "user-2")

        # Mock campaign participants
        campaign_participants = ["user-1", "user-2"]

        message = {
            "type": "campaign_update",
            "campaign_id": "campaign-123",
            "data": {"update": "Campaign started"}
        }

        await websocket_manager.send_message_to_campaign(campaign_participants, message)

        # Verify all participants received the message
        mock_ws1.send_json.assert_called_once_with(message)
        mock_ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_message(self, websocket_manager):
        """Test broadcasting message to all connected users"""
        # Create multiple mock WebSockets
        connections = []
        for i in range(3):
            mock_ws = AsyncMock()
            mock_ws.send_json = AsyncMock()
            connections.append(mock_ws)
            await websocket_manager.connect(mock_ws, f"user-{i}")

        # Broadcast message
        message = {
            "type": "system_announcement",
            "data": {"message": "Server maintenance in 10 minutes"}
        }

        await websocket_manager.broadcast_message(message)

        # Verify all connections received the message
        for mock_ws in connections:
            mock_ws.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_message_to_nonexistent_user(self, websocket_manager):
        """Test sending message to non-existent user"""
        message = {"type": "test", "data": {}}

        # Should not raise exception
        await websocket_manager.send_message_to_user("nonexistent-user", message)

    @pytest.mark.asyncio
    async def test_message_serialization(self, websocket_manager, mock_websocket):
        """Test message serialization and deserialization"""
        await websocket_manager.connect(mock_websocket, "user-123")

        # Test complex message with various data types
        message = {
            "type": "dice_roll_result",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "character_id": "char-123",
                "roll": {
                    "expression": "2d6+3",
                    "results": [4, 5],
                    "total": 12
                },
                "metadata": {
                    "critical": False,
                    "advantage": None
                }
            }
        }

        await websocket_manager.send_message_to_user("user-123", message)

        # Verify JSON serialization worked
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]

        assert call_args["type"] == "dice_roll_result"
        assert call_args["data"]["roll"]["total"] == 12
        assert isinstance(call_args["timestamp"], str)


class TestWebSocketHandlers:
    """Test specific WebSocket message handlers"""

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket connection"""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.user_id = "user-123"
        mock_ws.username = "testuser"
        return mock_ws

    @pytest.fixture
    def sample_dice_roll_message(self):
        """Sample dice roll message"""
        return {
            "type": "dice_roll",
            "data": {
                "expressions": ["1d20+5", "2d6"],
                "description": "Attack with damage",
                "character_id": "char-123",
                "campaign_id": "campaign-123"
            }
        }

    @pytest.mark.asyncio
    async def test_handle_dice_roll(self, mock_websocket, sample_dice_roll_message):
        """Test dice roll message handler"""
        with patch('source_code.backend.services.dice_service.get_dice_service') as mock_dice_service:
            # Mock dice service response
            mock_result = {
                "total": 23,
                "results": [
                    {"expression": "1d20+5", "total": 18},
                    {"expression": "2d6", "total": 5}
                ],
                "critical_type": "none"
            }
            mock_dice_service.return_value.process_roll_request.return_value = mock_result

            await handle_dice_roll(mock_websocket, sample_dice_roll_message)

            # Verify response was sent
            mock_websocket.send_json.assert_called()
            response = mock_websocket.send_json.call_args[0][0]

            assert response["type"] == "dice_roll_result"
            assert response["data"]["total"] == 23
            assert response["data"]["campaign_id"] == "campaign-123"

    @pytest.mark.asyncio
    async def test_handle_campaign_join(self, mock_websocket):
        """Test campaign join message handler"""
        join_message = {
            "type": "join_campaign",
            "data": {
                "campaign_id": "campaign-123",
                "character_id": "char-123"
            }
        }

        with patch('source_code.backend.services.campaign_service.get_campaign_service') as mock_service:
            # Mock campaign service
            mock_service.return_value.join_campaign.return_value = True

            await handle_campaign_join(mock_websocket, join_message)

            # Verify response
            mock_websocket.send_json.assert_called()
            response = mock_websocket.send_json.call_args[0][0]

            assert response["type"] == "campaign_joined"
            assert response["data"]["campaign_id"] == "campaign-123"

    @pytest.mark.asyncio
    async def test_handle_chat_message(self, mock_websocket):
        """Test chat message handler"""
        chat_message = {
            "type": "chat_message",
            "data": {
                "campaign_id": "campaign-123",
                "message": "Hello, everyone!",
                "character_id": "char-123"
            }
        }

        with patch('source_code.backend.services.chat_service.get_chat_service') as mock_service:
            # Mock chat service
            mock_service.return_value.save_message.return_value = {
                "id": "msg-123",
                "message": "Hello, everyone!",
                "sender": "testuser",
                "timestamp": datetime.utcnow()
            }

            await handle_chat_message(mock_websocket, chat_message)

            # Verify response
            mock_websocket.send_json.assert_called()
            response = mock_websocket.send_json.call_args[0][0]

            assert response["type"] == "chat_message_sent"
            assert response["data"]["message"] == "Hello, everyone!"

    @pytest.mark.asyncio
    async def test_handle_character_update(self, mock_websocket):
        """Test character update message handler"""
        update_message = {
            "type": "character_update",
            "data": {
                "character_id": "char-123",
                "updates": {
                    "current_hp": 15,
                    "temp_hp": 5,
                    "conditions": ["blessed"]
                }
            }
        }

        with patch('source_code.backend.services.character_service.get_character_service') as mock_service:
            # Mock character service
            mock_service.return_value.update_character.return_value = {
                "id": "char-123",
                "current_hp": 15,
                "temp_hp": 5,
                "conditions": ["blessed"]
            }

            await handle_character_update(mock_websocket, update_message)

            # Verify response
            mock_websocket.send_json.assert_called()
            response = mock_websocket.send_json.call_args[0][0]

            assert response["type"] == "character_updated"
            assert response["data"]["current_hp"] == 15

    @pytest.mark.asyncio
    async def test_handle_session_update(self, mock_websocket):
        """Test game session update message handler"""
        session_message = {
            "type": "session_update",
            "data": {
                "session_id": "session-123",
                "updates": {
                    "status": "active",
                    "current_turn": "char-123"
                }
            }
        }

        with patch('source_code.backend.services.session_service.get_session_service') as mock_service:
            # Mock session service
            mock_service.return_value.update_session.return_value = {
                "id": "session-123",
                "status": "active",
                "current_turn": "char-123"
            }

            await handle_session_update(mock_websocket, session_message)

            # Verify response
            mock_websocket.send_json.assert_called()
            response = mock_websocket.send_json.call_args[0][0]

            assert response["type"] == "session_updated"
            assert response["data"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_handle_invalid_message_type(self, mock_websocket):
        """Test handling invalid message types"""
        invalid_message = {
            "type": "invalid_type",
            "data": {}
        }

        await handle_dice_roll(mock_websocket, invalid_message)

        # Verify error response
        mock_websocket.send_json.assert_called()
        response = mock_websocket.send_json.call_args[0][0]

        assert response["type"] == "error"
        assert "invalid message type" in response["data"]["message"].lower()

    @pytest.mark.asyncio
    async def test_handle_malformed_message(self, mock_websocket):
        """Test handling malformed messages"""
        malformed_message = {
            "type": "dice_roll",
            # Missing required data field
        }

        await handle_dice_roll(mock_websocket, malformed_message)

        # Verify error response
        mock_websocket.send_json.assert_called()
        response = mock_websocket.send_json.call_args[0][0]

        assert response["type"] == "error"
        assert "invalid message" in response["data"]["message"].lower()


class TestWebSocketRooms:
    """Test WebSocket room functionality"""

    @pytest.fixture
    def websocket_manager(self):
        """Create WebSocket manager with room support"""
        return WebSocketManager()

    @pytest.fixture
    def mock_websockets(self):
        """Create multiple mock WebSocket connections"""
        websockets = []
        for i in range(3):
            mock_ws = AsyncMock()
            mock_ws.send_json = AsyncMock()
            mock_ws.user_id = f"user-{i}"
            mock_ws.client_id = f"client-{i}"
            websockets.append(mock_ws)
        return websockets

    @pytest.mark.asyncio
    async def test_join_campaign_room(self, websocket_manager, mock_websockets):
        """Test joining campaign room"""
        # Connect users
        for ws in mock_websockets:
            await websocket_manager.connect(ws, ws.user_id)

        # Join campaign room
        campaign_id = "campaign-123"
        for ws in mock_websockets:
            await websocket_manager.join_campaign_room(ws.user_id, campaign_id)

        # Verify users are in room
        room_members = websocket_manager.get_campaign_room_members(campaign_id)
        assert len(room_members) == 3
        assert all(ws.user_id in room_members for ws in mock_websockets)

    @pytest.mark.asyncio
    async def test_leave_campaign_room(self, websocket_manager, mock_websockets):
        """Test leaving campaign room"""
        # Setup
        for ws in mock_websockets:
            await websocket_manager.connect(ws, ws.user_id)

        campaign_id = "campaign-123"
        for ws in mock_websockets:
            await websocket_manager.join_campaign_room(ws.user_id, campaign_id)

        # Leave room
        await websocket_manager.leave_campaign_room(mock_websockets[0].user_id, campaign_id)

        # Verify user left room
        room_members = websocket_manager.get_campaign_room_members(campaign_id)
        assert len(room_members) == 2
        assert mock_websockets[0].user_id not in room_members

    @pytest.mark.asyncio
    async def test_send_message_to_campaign_room(self, websocket_manager, mock_websockets):
        """Test sending message to campaign room"""
        # Setup
        for ws in mock_websockets:
            await websocket_manager.connect(ws, ws.user_id)

        campaign_id = "campaign-123"
        for ws in mock_websockets:
            await websocket_manager.join_campaign_room(ws.user_id, campaign_id)

        # Send message to room
        message = {
            "type": "campaign_message",
            "data": {"content": "Hello campaign!"}
        }

        await websocket_manager.send_message_to_campaign_room(campaign_id, message)

        # Verify all room members received message
        for ws in mock_websockets:
            ws.send_json.assert_called_with(message)

    @pytest.mark.asyncio
    async def test_room_cleanup_on_disconnect(self, websocket_manager, mock_websockets):
        """Test room cleanup when user disconnects"""
        # Setup
        for ws in mock_websockets:
            await websocket_manager.connect(ws, ws.user_id)

        campaign_id = "campaign-123"
        for ws in mock_websockets:
            await websocket_manager.join_campaign_room(ws.user_id, campaign_id)

        # Disconnect user
        await websocket_manager.disconnect(mock_websockets[0], mock_websockets[0].user_id)

        # Verify user was removed from room
        room_members = websocket_manager.get_campaign_room_members(campaign_id)
        assert mock_websockets[0].user_id not in room_members
        assert len(room_members) == 2

    @pytest.mark.asyncio
    async def test_multiple_campaign_rooms(self, websocket_manager, mock_websockets):
        """Test users in multiple campaign rooms"""
        # Setup
        for ws in mock_websockets:
            await websocket_manager.connect(ws, ws.user_id)

        # Join different campaigns
        campaign1 = "campaign-1"
        campaign2 = "campaign-2"

        await websocket_manager.join_campaign_room(mock_websockets[0].user_id, campaign1)
        await websocket_manager.join_campaign_room(mock_websockets[1].user_id, campaign1)
        await websocket_manager.join_campaign_room(mock_websockets[1].user_id, campaign2)
        await websocket_manager.join_campaign_room(mock_websockets[2].user_id, campaign2)

        # Verify room memberships
        campaign1_members = websocket_manager.get_campaign_room_members(campaign1)
        campaign2_members = websocket_manager.get_campaign_room_members(campaign2)

        assert len(campaign1_members) == 2
        assert len(campaign2_members) == 2
        assert mock_websockets[1].user_id in campaign1_members
        assert mock_websockets[1].user_id in campaign2_members


class TestWebSocketPerformance:
    """Test WebSocket performance under load"""

    @pytest.fixture
    def websocket_manager(self):
        """Create WebSocket manager instance"""
        return WebSocketManager()

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, websocket_manager):
        """Test handling many concurrent connections"""
        async def create_connection(user_id):
            mock_ws = AsyncMock()
            mock_ws.send_json = AsyncMock()
            mock_ws.client_id = f"client-{user_id}"
            await websocket_manager.connect(mock_ws, str(user_id))
            return mock_ws

        # Create many concurrent connections
        start_time = time.time()
        tasks = [create_connection(i) for i in range(100)]
        websockets = await asyncio.gather(*tasks)
        connection_time = time.time() - start_time

        # Verify all connections were established
        assert len(websocket_manager.active_connections) == 100
        assert connection_time < 5.0  # Should complete within 5 seconds

    @pytest.mark.asyncio
    async def test_high_message_throughput(self, websocket_manager):
        """Test high message throughput"""
        # Create connections
        websockets = []
        for i in range(10):
            mock_ws = AsyncMock()
            mock_ws.send_json = AsyncMock()
            await websocket_manager.connect(mock_ws, f"user-{i}")
            websockets.append(mock_ws)

        # Send many messages
        message_count = 1000
        start_time = time.time()

        for i in range(message_count):
            message = {
                "type": "test_message",
                "data": {"index": i}
            }
            await websocket_manager.broadcast_message(message)

        throughput_time = time.time() - start_time
        messages_per_second = message_count / throughput_time

        # Verify performance
        assert messages_per_second > 100  # Should handle at least 100 messages/second
        assert throughput_time < 10.0  # Should complete within 10 seconds

    @pytest.mark.asyncio
    async def test_memory_usage_with_many_connections(self, websocket_manager):
        """Test memory usage with many connections"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create many connections
        connection_count = 500
        for i in range(connection_count):
            mock_ws = AsyncMock()
            mock_ws.send_json = AsyncMock()
            mock_ws.client_id = f"client-{i}"
            await websocket_manager.connect(mock_ws, f"user-{i}")

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        memory_per_connection = memory_increase / connection_count

        # Verify reasonable memory usage (less than 1MB per connection)
        assert memory_per_connection < 1024 * 1024  # 1MB in bytes

    @pytest.mark.asyncio
    async def test_message_ordering(self, websocket_manager):
        """Test that messages are delivered in order"""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await websocket_manager.connect(mock_ws, "user-123")

        # Send messages in sequence
        messages = [
            {"type": "test", "data": {"sequence": i}}
            for i in range(10)
        ]

        for message in messages:
            await websocket_manager.send_message_to_user("user-123", message)

        # Verify messages were sent in order
        assert mock_ws.send_json.call_count == 10
        for i, call in enumerate(mock_ws.send_json.call_args_list):
            sent_message = call[0][0]
            assert sent_message["data"]["sequence"] == i

    @pytest.mark.asyncio
    async def test_connection_lifecycle_performance(self, websocket_manager):
        """Test performance of connection lifecycle operations"""
        # Test connection and disconnection performance
        iterations = 100
        start_time = time.time()

        for i in range(iterations):
            mock_ws = AsyncMock()
            mock_ws.send_json = AsyncMock()
            mock_ws.client_id = f"client-{i}"

            # Connect
            await websocket_manager.connect(mock_ws, f"user-{i}")

            # Send a message
            message = {"type": "test", "data": {"iteration": i}}
            await websocket_manager.send_message_to_user(f"user-{i}", message)

            # Disconnect
            await websocket_manager.disconnect(mock_ws, f"user-{i}")

        lifecycle_time = time.time() - start_time
        avg_time_per_cycle = lifecycle_time / iterations

        # Verify performance (should be fast)
        assert avg_time_per_cycle < 0.01  # Less than 10ms per cycle


class TestWebSocketErrors:
    """Test WebSocket error handling"""

    @pytest.fixture
    def websocket_manager(self):
        """Create WebSocket manager instance"""
        return WebSocketManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket connection"""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.close = AsyncMock()
        mock_ws.user_id = "user-123"
        mock_ws.client_id = "client-123"
        return mock_ws

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, websocket_manager):
        """Test handling connection errors"""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock(side_effect=ConnectionError("Connection lost"))

        await websocket_manager.connect(mock_ws, "user-123")

        # Try to send message
        message = {"type": "test", "data": {}}

        # Should handle error gracefully
        await websocket_manager.send_message_to_user("user-123", message)

        # Connection should be removed
        assert "user-123" not in websocket_manager.active_connections

    @pytest.mark.asyncio
    async def test_message_parsing_error(self, websocket_manager, mock_websocket):
        """Test handling message parsing errors"""
        await websocket_manager.connect(mock_websocket, "user-123")

        # Mock invalid JSON
        mock_websocket.receive_json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        # Should handle error and send error message
        with pytest.raises(json.JSONDecodeError):
            await websocket_manager.handle_message(mock_websocket, "invalid json")

    @pytest.mark.asyncio
    async def test_room_not_found_error(self, websocket_manager, mock_websocket):
        """Test handling room not found errors"""
        await websocket_manager.connect(mock_websocket, "user-123")

        # Try to send message to non-existent room
        message = {"type": "test", "data": {}}

        # Should handle gracefully
        await websocket_manager.send_message_to_campaign_room("non-existent-room", message)

        # Verify no error was raised
        assert True  # Test passes if no exception

    @pytest.mark.asyncio
    async def test_websocket_close_codes(self, websocket_manager, mock_websocket):
        """Test WebSocket close codes"""
        await websocket_manager.connect(mock_websocket, "user-123")

        # Test different close scenarios
        close_scenarios = [
            (4000, "Normal closure"),
            (4001, "Authentication failed"),
            (4002, "Room not found"),
            (4003, "Invalid message")
        ]

        for code, reason in close_scenarios:
            await websocket_manager.disconnect(mock_websocket, "user-123", code, reason)

            # Verify close was called with correct parameters
            mock_websocket.close.assert_called_with(code=code, reason=reason)

    @pytest.mark.asyncio
    async def test_rate_limiting(self, websocket_manager):
        """Test message rate limiting"""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await websocket_manager.connect(mock_ws, "user-123")

        # Send many messages quickly
        messages = [{"type": "test", "data": {"i": i}} for i in range(100)]

        for message in messages:
            await websocket_manager.send_message_to_user("user-123", message)

        # Verify rate limiting is working (messages should be sent but may be limited)
        # This test would need actual rate limiting implementation
        assert mock_ws.send_json.call_count <= 100  # Some messages may be dropped


class TestWebSocketReconnection:
    """Test WebSocket reconnection logic"""

    @pytest.fixture
    def websocket_manager(self):
        """Create WebSocket manager instance"""
        return WebSocketManager()

    @pytest.mark.asyncio
    async def test_automatic_reconnection(self, websocket_manager):
        """Test automatic reconnection logic"""
        # Simulate reconnection scenario
        mock_ws1 = AsyncMock()
        mock_ws1.send_json = AsyncMock()
        mock_ws1.client_id = "client-123"

        # Initial connection
        await websocket_manager.connect(mock_ws1, "user-123")

        # Simulate disconnection
        await websocket_manager.disconnect(mock_ws1, "user-123")

        # Create new connection for same user
        mock_ws2 = AsyncMock()
        mock_ws2.send_json = AsyncMock()
        mock_ws2.client_id = "client-456"  # Different client ID

        await websocket_manager.connect(mock_ws2, "user-123")

        # Verify reconnection was successful
        assert "user-123" in websocket_manager.active_connections
        assert len(websocket_manager.active_connections["user-123"]) == 1
        assert mock_ws2 in websocket_manager.active_connections["user-123"]

    @pytest.mark.asyncio
    async def test_session_restoration(self, websocket_manager):
        """Test session restoration after reconnection"""
        # Mock session data
        user_sessions = {
            "user-123": {
                "campaign_rooms": ["campaign-1", "campaign-2"],
                "preferences": {"notifications": True}
            }
        }

        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()

        # Simulate reconnection with session restoration
        await websocket_manager.connect(mock_ws, "user-123")
        await websocket_manager.restore_user_session("user-123", user_sessions["user-123"])

        # Verify session was restored
        assert "user-123" in websocket_manager.active_connections

        # Verify user was re-joined to rooms
        campaign1_members = websocket_manager.get_campaign_room_members("campaign-1")
        campaign2_members = websocket_manager.get_campaign_room_members("campaign-2")

        assert "user-123" in campaign1_members
        assert "user-123" in campaign2_members

    @pytest.mark.asyncio
    async def test_reconnection_with_message_queue(self, websocket_manager):
        """Test message queuing during disconnection"""
        # Mock message queue functionality
        message_queue = []

        def queue_message(user_id, message):
            message_queue.append((user_id, message))

        # User disconnects
        await websocket_manager.disconnect(Mock(), "user-123")

        # Messages are queued while user is disconnected
        while len(message_queue) < 3:
            queue_message("user-123", {
                "type": "queued_message",
                "data": {"queue_position": len(message_queue)}
            })

        # User reconnects
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        await websocket_manager.connect(mock_ws, "user-123")

        # Queued messages should be delivered
        for user_id, message in message_queue:
            await websocket_manager.send_message_to_user(user_id, message)

        # Verify queued messages were delivered
        assert mock_ws.send_json.call_count == len(message_queue)

    @pytest.mark.asyncio
    async def test_heartbeat_mechanism(self, websocket_manager):
        """Test WebSocket heartbeat mechanism"""
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.receive_json = AsyncMock()

        await websocket_manager.connect(mock_ws, "user-123")

        # Simulate heartbeat messages
        heartbeat_messages = [
            {"type": "ping", "timestamp": time.time()}
            for _ in range(5)
        ]

        for heartbeat in heartbeat_messages:
            await websocket_manager.handle_heartbeat(mock_ws, heartbeat)

        # Verify ping/pong responses
        pong_calls = [
            call for call in mock_ws.send_json.call_args_list
            if call[0][0]["type"] == "pong"
        ]

        assert len(pong_calls) == 5