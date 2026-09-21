"""
Communication Bridge - Handles inter-portal communication and message routing.
"""

import asyncio
import uuid
import json
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from collections import defaultdict, deque

from .config import settings, EVENT_TYPES
from ..database.models import Portal, PortalMessage, PortalSession, WorldState
from ..database.database import get_db

logger = logging.getLogger(__name__)

class CommunicationBridge:
    """Handles communication between portals and message routing."""

    def __init__(self):
        self.bridge_connections: Dict[str, Any] = {}  # session_id -> connection
        self.message_queue = asyncio.Queue(maxsize=settings.BRIDGE_BUFFER_SIZE)
        self.message_history = deque(maxlen=settings.MESSAGE_HISTORY_SIZE)
        self.subscribers: Dict[str, Set[str]] = defaultdict(set)  # event_type -> set of session_ids
        self.portal_subscriptions: Dict[str, Set[str]] = defaultdict(set)  # portal_id -> set of event_types
        self.message_handlers: Dict[str, callable] = {}
        self.total_messages_sent = 0
        self.total_messages_received = 0
        self.running = False
        self.processing_task = None

    async def initialize(self):
        """Initialize the communication bridge."""
        logger.info("Initializing Communication Bridge...")
        self.running = True
        self.processing_task = asyncio.create_task(self._process_message_queue())
        await self._register_default_handlers()
        logger.info("Communication Bridge initialized")

    async def _register_default_handlers(self):
        """Register default message handlers."""
        self.register_handler("character_update", self._handle_character_update)
        self.register_handler("world_update", self._handle_world_update)
        self.register_handler("encounter_start", self._handle_encounter_start)
        self.register_handler("code_update", self._handle_code_update)

    def register_handler(self, event_type: str, handler: callable):
        """Register a handler for a specific event type."""
        self.message_handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")

    async def handle_bridge_connection(self, websocket):
        """Handle a bridge WebSocket connection."""
        session_id = str(uuid.uuid4())
        self.bridge_connections[session_id] = websocket

        logger.info(f"Bridge connection established: {session_id}")

        try:
            # Send welcome message
            await self._send_to_connection(websocket, {
                "type": "bridge_connected",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            })

            # Handle messages
            while True:
                try:
                    message = await websocket.receive_text()
                    await self._handle_bridge_message(session_id, message)
                except Exception as e:
                    logger.error(f"Error handling bridge message from {session_id}: {str(e)}")
                    break

        except Exception as e:
            logger.error(f"Bridge connection error for {session_id}: {str(e)}")
        finally:
            if session_id in self.bridge_connections:
                del self.bridge_connections[session_id]
            # Remove from all subscriptions
            for event_type in self.subscribers:
                self.subscribers[event_type].discard(session_id)

            logger.info(f"Bridge connection closed: {session_id}")

    async def _handle_bridge_message(self, session_id: str, message: str):
        """Handle a message from a bridge connection."""
        try:
            data = json.loads(message)
            self.total_messages_received += 1

            if data.get("type") == "subscribe":
                await self._handle_subscribe(session_id, data)
            elif data.get("type") == "unsubscribe":
                await self._handle_unsubscribe(session_id, data)
            elif data.get("type") == "broadcast":
                await self._handle_broadcast(session_id, data)
            else:
                logger.warning(f"Unknown message type from bridge {session_id}: {data.get('type')}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from bridge {session_id}: {message}")

    async def _handle_subscribe(self, session_id: str, data: Dict):
        """Handle subscription request."""
        event_types = data.get("event_types", [])
        portal_id = data.get("portal_id")

        for event_type in event_types:
            self.subscribers[event_type].add(session_id)
            if portal_id:
                self.portal_subscriptions[portal_id].add(event_type)

        await self._send_to_connection(
            self.bridge_connections[session_id],
            {
                "type": "subscription_confirmed",
                "event_types": event_types,
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"Session {session_id} subscribed to: {event_types}")

    async def _handle_unsubscribe(self, session_id: str, data: Dict):
        """Handle unsubscribe request."""
        event_types = data.get("event_types", [])

        for event_type in event_types:
            self.subscribers[event_type].discard(session_id)

        await self._send_to_connection(
            self.bridge_connections[session_id],
            {
                "type": "unsubscription_confirmed",
                "event_types": event_types,
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"Session {session_id} unsubscribed from: {event_types}")

    async def _handle_broadcast(self, session_id: str, data: Dict):
        """Handle broadcast request."""
        message = {
            "event_type": data.get("event_type"),
            "data": data.get("data", {}),
            "source_session": session_id,
            "timestamp": datetime.now().isoformat()
        }

        await self.broadcast_message(
            data.get("target_portals", []),
            data.get("event_type"),
            data.get("data", {}),
            data.get("source_portal")
        )

    async def handle_portal_message(self, portal_id: str, session_id: str, data: Dict):
        """Handle a message from a portal."""
        try:
            self.total_messages_received += 1

            # Create message record
            message_record = PortalMessage(
                id=str(uuid.uuid4()),
                portal_id=portal_id,
                message_type=data.get("type", "unknown"),
                event_type=data.get("event_type", "unknown"),
                data=data,
                source_portal=data.get("source_portal"),
                target_portals=data.get("target_portals", [])
            )

            # Save to database
            try:
                db = next(get_db())
                db.add(message_record)
                db.commit()
                db.refresh(message_record)
            except Exception as e:
                logger.error(f"Failed to save message to database: {str(e)}")

            # Add to queue for processing
            await self.message_queue.put({
                "id": message_record.id,
                "portal_id": portal_id,
                "session_id": session_id,
                "data": data,
                "timestamp": datetime.now()
            })

            # Add to history
            self.message_history.append({
                "id": message_record.id,
                "portal_id": portal_id,
                "event_type": data.get("event_type"),
                "data": data,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error handling portal message: {str(e)}")

    async def _process_message_queue(self):
        """Process messages from the queue."""
        while self.running:
            try:
                # Get message from queue with timeout
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )

                await self._process_message(message)

                self.message_queue.task_done()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing message queue: {str(e)}")
                await asyncio.sleep(0.1)

    async def _process_message(self, message: Dict):
        """Process a single message."""
        try:
            portal_id = message["portal_id"]
            session_id = message["session_id"]
            data = message["data"]
            event_type = data.get("event_type")

            # Handle event with registered handler
            if event_type in self.message_handlers:
                await self.message_handlers[event_type](message)

            # Broadcast to bridge subscribers
            await self._broadcast_to_bridge_subscribers(event_type, message)

            # Route to target portals
            target_portals = data.get("target_portals", [])
            if target_portals:
                await self._route_to_portals(target_portals, message)

            # Update message status
            try:
                db = next(get_db())
                db.query(PortalMessage).filter(PortalMessage.id == message["id"]).update({
                    "is_delivered": True,
                    "delivered_at": datetime.now()
                })
                db.commit()
            except Exception as e:
                logger.error(f"Failed to update message status: {str(e)}")

        except Exception as e:
            logger.error(f"Error processing message {message.get('id')}: {str(e)}")

    async def _broadcast_to_bridge_subscribers(self, event_type: str, message: Dict):
        """Broadcast message to bridge subscribers."""
        if event_type in self.subscribers:
            for session_id in self.subscribers[event_type]:
                if session_id in self.bridge_connections:
                    try:
                        await self._send_to_connection(
                            self.bridge_connections[session_id],
                            {
                                "type": "event",
                                "event_type": event_type,
                                "message": message,
                                "timestamp": datetime.now().isoformat()
                            }
                        )
                        self.total_messages_sent += 1
                    except Exception as e:
                        logger.error(f"Failed to send to bridge subscriber {session_id}: {str(e)}")

    async def _route_to_portals(self, target_portals: List[str], message: Dict):
        """Route message to specific portals."""
        # This would integrate with the portal manager to send messages to specific portals
        for portal_id in target_portals:
            logger.info(f"Routing message to portal {portal_id}: {message.get('id')}")

    async def broadcast_message(self, target_portals: List[str], event_type: str, data: Dict, source_portal: Optional[str] = None) -> Dict[str, Any]:
        """Broadcast a message to target portals."""
        message_id = str(uuid.uuid4())

        message = {
            "id": message_id,
            "event_type": event_type,
            "data": data,
            "source_portal": source_portal,
            "target_portals": target_portals,
            "timestamp": datetime.now().isoformat()
        }

        # Add to queue
        await self.message_queue.put(message)

        # Add to history
        self.message_history.append(message)

        self.total_messages_sent += 1

        return {
            "message_id": message_id,
            "status": "queued",
            "target_count": len(target_portals)
        }

    async def notify_portal_created(self, portal: Portal):
        """Notify subscribers that a portal was created."""
        await self.broadcast_message(
            [],
            "portal_created",
            {
                "portal_id": portal.id,
                "portal_type": portal.portal_type.value,
                "port": portal.port,
                "url": portal.url
            }
        )

    async def notify_portal_destroyed(self, portal: Portal):
        """Notify subscribers that a portal was destroyed."""
        await self.broadcast_message(
            [],
            "portal_destroyed",
            {
                "portal_id": portal.id,
                "portal_type": portal.portal_type.value
            }
        )

    # Default message handlers
    async def _handle_character_update(self, message: Dict):
        """Handle character update messages."""
        logger.info(f"Handling character update: {message['id']}")
        # This would update character state in the database

    async def _handle_world_update(self, message: Dict):
        """Handle world update messages."""
        logger.info(f"Handling world update: {message['id']}")
        # This would update world state

    async def _handle_encounter_start(self, message: Dict):
        """Handle encounter start messages."""
        logger.info(f"Handling encounter start: {message['id']}")
        # This would create a new encounter

    async def _handle_code_update(self, message: Dict):
        """Handle code update messages."""
        logger.info(f"Handling code update: {message['id']}")
        # This would handle code changes

    async def _send_to_connection(self, connection, message: Dict):
        """Send a message to a specific connection."""
        try:
            await connection.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to connection: {str(e)}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get communication bridge statistics."""
        return {
            "total_messages_sent": self.total_messages_sent,
            "total_messages_received": self.total_messages_received,
            "active_connections": len(self.bridge_connections),
            "queue_size": self.message_queue.qsize(),
            "history_size": len(self.message_history),
            "subscriptions": {
                event_type: len(subscribers)
                for event_type, subscribers in self.subscribers.items()
            }
        }

    async def get_message_history(self, limit: int = 50) -> List[Dict]:
        """Get recent message history."""
        return list(self.message_history)[-limit:]

    async def health_check(self) -> bool:
        """Check if communication bridge is healthy."""
        try:
            # Check if processing task is running
            if not self.running:
                return False

            # Check queue size
            if self.message_queue.qsize() > settings.BRIDGE_BUFFER_SIZE * 0.9:
                return False

            return True
        except Exception as e:
            logger.error(f"Communication bridge health check failed: {str(e)}")
            return False

    async def shutdown(self):
        """Shutdown the communication bridge."""
        logger.info("Shutting down Communication Bridge...")

        self.running = False

        # Cancel processing task
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        for connection in self.bridge_connections.values():
            try:
                await connection.close()
            except Exception as e:
                logger.error(f"Error closing bridge connection: {str(e)}")

        self.bridge_connections.clear()
        self.subscribers.clear()
        self.portal_subscriptions.clear()

        logger.info("Communication Bridge shutdown complete")