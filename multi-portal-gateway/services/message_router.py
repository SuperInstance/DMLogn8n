"""
Real-time Message Router - Routes messages between all portals
Handles WebSocket communication, game events, and cross-portal coordination
"""
import asyncio
import logging
import json
from typing import Dict, List, Set, Optional, Callable
from datetime import datetime
import websockets

logger = logging.getLogger(__name__)

class MessageRouter:
    """Routes messages between character portals, DM, and players"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # connection_id -> websocket
        self.character_ports: Dict[str, int] = {}  # character_id -> port
        self.dm_connection: Optional[WebSocket] = None
        self.game_events: List[Dict] = []
        self.event_handlers: Dict[str, Callable] = {}

    async def register_connection(self, connection_id: str, websocket: WebSocket,
                            character_id: Optional[str] = None, port: Optional[int] = None):
        """Register a new connection"""
        self.active_connections[connection_id] = {
            "websocket": websocket,
            "character_id": character_id,
            "port": port,
            "type": "character" if character_id else ("dm" if port == 9501 else "player"),
            "connected_at": datetime.utcnow(),
            "last_heartbeat": datetime.utcnow()
        }

        logger.info(f"Registered connection {connection_id} as {self.active_connections[connection_id]['type']}")

    async def unregister_connection(self, connection_id: str):
        """Unregister a connection"""
        if connection_id in self.active_connections:
            connection_info = self.active_connections[connection_id]
            logger.info(f"Unregistering {connection_info['type']} {connection_id}")
            del self.active_connections[connection_id]

    async def route_message(self, sender_id: str, message: Dict):
        """Route message to appropriate targets"""
        msg_type = message.get("type", "text")
        sender_info = self.active_connections.get(sender_id)

        if not sender_info:
            logger.warning(f"Message from unknown sender {sender_id}")
            return

        timestamp = datetime.utcnow().isoformat()

        if msg_type == "character_command":
            # Character action (e.g., attack, cast spell, talk)
            await self.handle_character_action(sender_info, message, timestamp)
        elif msg_type == "dialogue":
            # Roleplaying dialogue
            await self.handle_dialogue(sender_info, message, timestamp)
        elif msg_type == "dm_command":
            # DM actions (world editing, encounter control)
            await self.handle_dm_command(sender_info, message, timestamp)
        elif msg_type == "system_event":
            # Game system events (combat tick, status updates)
            await self.handle_system_event(sender_info, message, timestamp)
        elif msg_type == "private_message":
            # Private messages between characters/players
            await self.handle_private_message(sender_info, message, timestamp)
        elif msg_type == "area_broadcast":
            # Messages to characters in same area
            await self.handle_area_broadcast(sender_info, message, timestamp)
        elif msg_type == "coder_request":
            # Requests to coder bot
            await self.handle_coder_request(sender_info, message, timestamp)
        elif msg_type == "thought_process":
            # AI agent thinking process (transparency)
            await self.handle_thought_process(sender_info, message, timestamp)
        elif msg_type == "heartbeat":
            # Connection health check
            await self.handle_heartbeat(sender_info)
        else:
            logger.warning(f"Unknown message type: {msg_type}")

    async def handle_character_action(self, sender_info: Dict, message: Dict, timestamp: str):
        """Handle character actions (combat, movement, etc.)"""
        action = message.get("action", "")
        target = message.get("target", "")
        area = message.get("area", "current")

        # Broadcast to all characters in area
        area_message = {
            "type": "character_action",
            "sender": sender_info["character_id"],
            "action": action,
            "target": target,
            "area": area,
            "timestamp": timestamp
        }

        await self.broadcast_to_area(area, area_message)

        # Log for AI processing
        if sender_info["type"] == "character":
            await self.send_to_ai_processor(sender_info["character_id"], {
                "type": "action_request",
                "action": action,
                "context": {
                    "area": area,
                    "target": target,
                    "available_actions": await self.get_available_actions(sender_info["character_id"])
                },
                "timestamp": timestamp
            })

    async def handle_dialogue(self, sender_info: Dict, message: Dict, timestamp: str):
        """Handle roleplaying dialogue"""
        dialogue = message.get("dialogue", "")
        emotion = message.get("emotion", "neutral")
        style = message.get("style", "in_character")

        dialogue_message = {
            "type": "dialogue",
            "sender": sender_info["character_id"],
            "dialogue": dialogue,
            "emotion": emotion,
            "style": style,
            "timestamp": timestamp
        }

        # Broadcast to nearby characters
        await self.broadcast_to_nearby(sender_info, dialogue_message)

        # Process for AI learning
        if sender_info["type"] == "character":
            await self.send_to_ai_processor(sender_info["character_id"], {
                "type": "dialogue_event",
                "dialogue": dialogue,
                "emotion": emotion,
                "context": await self.get_dialogue_context(sender_info["character_id"]),
                "timestamp": timestamp
            })

    async def handle_dm_command(self, sender_info: Dict, message: Dict, timestamp: str):
        """Handle Dungeon Master commands"""
        command = message.get("command", "")
        parameters = message.get("parameters", {})

        if sender_info["type"] == "dm":
            # Execute DM command
            result = await self.execute_dm_command(command, parameters)

            # Broadcast results
            result_message = {
                "type": "dm_result",
                "command": command,
                "result": result,
                "timestamp": timestamp
            }
            await self.broadcast_to_all(result_message)

    async def handle_system_event(self, sender_info: Dict, message: Dict, timestamp: str):
        """Handle game system events (combat ticks, etc.)"""
        event_type = message.get("event_type", "")
        data = message.get("data", {})

        # Route to appropriate handlers
        if event_type == "combat_tick":
            await self.process_combat_tick(data)
        elif event_type == "status_update":
            await self.process_status_update(data)
        elif event_type == "world_change":
            await self.process_world_change(data)

    async def handle_private_message(self, sender_info: Dict, message: Dict, timestamp: str):
        """Handle private messages between characters"""
        recipient_id = message.get("recipient", "")
        content = message.get("content", "")

        # Send directly to recipient if connected
        for conn_id, conn_info in self.active_connections.items():
            if conn_info["character_id"] == recipient_id:
                private_message = {
                    "type": "private_message",
                    "sender": sender_info["character_id"],
                    "content": content,
                    "timestamp": timestamp
                }
                await self.send_to_connection(conn_id, private_message)
                break

    async def handle_area_broadcast(self, sender_info: Dict, message: Dict, timestamp: str):
        """Broadcast to all characters in the same area"""
        area = message.get("area", "")
        broadcast_content = message.get("content", "")

        for conn_id, conn_info in self.active_connections.items():
            if conn_info["type"] == "character":
                # Check if character is in area (would need location tracking)
                area_message = {
                    "type": "area_broadcast",
                    "area": area,
                    "sender": sender_info["character_id"],
                    "content": broadcast_content,
                    "timestamp": timestamp
                }
                await self.send_to_connection(conn_id, area_message)

    async def handle_coder_request(self, sender_info: Dict, message: Dict, timestamp: str):
        """Handle requests to the coder bot"""
        request_type = message.get("request_type", "")
        parameters = message.get("parameters", {})

        # Forward to coder bot service
        coder_request = {
            "type": "coder_request",
            "request_type": request_type,
            "parameters": parameters,
            "requester": sender_info["character_id"],
            "timestamp": timestamp
        }

        # Send to coder service (would connect to GLM-4.6)
        await self.forward_to_coder(coder_request)

    async def handle_thought_process(self, sender_info: Dict, message: Dict, timestamp: str):
        """Display AI agent's thought process for transparency"""
        thoughts = message.get("thoughts", [])
        confidence = message.get("confidence", 0.0)
        decision = message.get("decision", "")

        # Broadcast thought process to nearby players for transparency
        thought_message = {
            "type": "agent_thought_process",
            "character": sender_info["character_id"],
            "thoughts": thoughts,
            "confidence": confidence,
            "decision": decision,
            "reasoning": message.get("reasoning", ""),
            "timestamp": timestamp
        }

        await self.broadcast_to_nearby(sender_info, thought_message)

    async def handle_heartbeat(self, sender_info: Dict):
        """Handle connection health checks"""
        sender_info["last_heartbeat"] = datetime.utcnow()

        # Send pong response
        if "websocket" in sender_info:
            await sender_info["websocket"].send(json.dumps({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            }))

    async def broadcast_to_area(self, area: str, message: Dict):
        """Broadcast to all characters in specific area"""
        for conn_id, conn_info in self.active_connections.items():
            if conn_info["type"] == "character":
                # Would check character's current area
                await self.send_to_connection(conn_id, message)

    async def broadcast_to_nearby(self, sender_info: Dict, message: Dict):
        """Broadcast to nearby characters"""
        for conn_id, conn_info in self.active_connections.items():
            if conn_info["type"] in ["character", "player"]:
                distance = self.calculate_distance(sender_info, conn_info)
                if distance and distance < 10:  # Within "hearing" range
                    await self.send_to_connection(conn_id, message)

    async def broadcast_to_all(self, message: Dict):
        """Broadcast to all connected clients"""
        for conn_id in self.active_connections:
            await self.send_to_connection(conn_id, message)

    async def send_to_connection(self, conn_id: str, message: Dict):
        """Send message to specific connection"""
        if conn_id in self.active_connections:
            websocket = self.active_connections[conn_id]["websocket"]
            await websocket.send(json.dumps(message))

    async def send_to_ai_processor(self, character_id: str, message: Dict):
        """Send message to AI processing service"""
        # This would connect to the character's AI agent
        # Implementation depends on AI architecture
        logger.info(f"Sending AI processing request for {character_id}")

    async def forward_to_coder(self, coder_request: Dict):
        """Forward request to coder bot service"""
        # This would integrate with your GLM-4.6 coder
        logger.info(f"Forwarding coder request: {coder_request}")

    def calculate_distance(self, char1: Dict, char2: Dict) -> Optional[float]:
        """Calculate distance between two characters (simplified)"""
        # Would use actual position data
        return 10.0  # Placeholder

    async def get_available_actions(self, character_id: str) -> List[str]:
        """Get available actions for character"""
        # This would integrate with game engine
        return ["attack", "cast", "move", "talk", "use_item", "inspect"]

    async def get_dialogue_context(self, character_id: str) -> Dict:
        """Get context for dialogue generation"""
        # Would retrieve recent interactions, location, etc.
        return {"location": "tavern", "recent": ["talked to bard", " fought goblin"]}

# Event handlers (to be implemented)
    async def process_combat_tick(self, data: Dict):
        """Process combat tick event"""
        pass

    async def process_status_update(self, data: Dict):
        """Process status update event"""
        pass

    async def process_world_change(self, data: Dict):
        """Process world change event"""
        pass

    async def execute_dm_command(self, command: str, parameters: Dict) -> Dict:
        """Execute DM command"""
        return {"executed": True, "result": f"Command {command} executed"}