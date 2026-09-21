"""
Character Portal Service - Individual Character Terminals
Provides isolated terminal environment for each character (ports 9000-9500)
"""
import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
import json
import uuid
from fastapi import WebSocket, WebSocketDisconnect
import websockets

logger = logging.getLogger(__name__)

class CharacterPortal:
    """Manages individual character terminal sessions"""

    def __init__(self, character_id: str, port: int, gateway_url: str):
        self.character_id = character_id
        self.port = port
        self.gateway_url = gateway_url
        self.websocket: Optional[WebSocket] = None
        self.connected_players: Set[str] = set()
        self.terminal_history: List[Dict] = []
        self.control_mode = "agent"  # agent, human, hybrid
        self.command_history: List[str] = []

    async def start_portal(self):
        """Start the character portal on assigned port"""
        logger.info(f"Starting character portal for {self.character_id} on port {self.port}")

        # WebSocket server for this character
        server = websockets.serve(
            lambda ws, path=self.handle_websocket_connection,
            host="localhost",
            port=self.port
        )

        logger.info(f"Character portal {self.character_id} listening on port {self.port}")
        await server

    async def handle_websocket_connection(self, websocket: WebSocket, path: str):
        """Handle incoming WebSocket connections"""
        connection_id = str(uuid.uuid4())

        try:
            # Register with main gateway
            await self.register_with_gateway(connection_id)

            # Send welcome message
            await websocket.send(json.dumps({
                "type": "system",
                "message": f"Connected to {self.character_id}'s terminal",
                "timestamp": datetime.utcnow().isoformat(),
                "character_id": self.character_id,
                "connection_id": connection_id
            }))

            # Handle messages
            async for message in websocket:
                await self.handle_message(websocket, connection_id, message)

        except WebSocketDisconnect:
            await self.unregister_from_gateway(connection_id)
            logger.info(f"Player disconnected from {self.character_id}")

    async def register_with_gateway(self, connection_id: str):
        """Register this portal with main gateway"""
        async with websockets.connect(f"{self.gateway_url}/ws/characters/{self.character_id}") as gateway_ws:
            register_msg = {
                "type": "register",
                "character_id": self.character_id,
                "port": self.port,
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            await gateway_ws.send(json.dumps(register_msg))

            # Listen for gateway messages
            async for message in gateway_ws:
                if message.get("type") == "broadcast":
                    await websocket.send(json.dumps({
                        "type": "broadcast",
                        "data": message.get("data"),
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                elif message.get("type") == "control":
                    await self.handle_control_message(message)

    async def unregister_from_gateway(self, connection_id: str):
        """Unregister from main gateway"""
        async with websockets.connect(f"{self.gateway_url}/ws/characters/{self.character_id}") as gateway_ws:
            unregister_msg = {
                "type": "unregister",
                "character_id": self.character_id,
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            await gateway_ws.send(json.dumps(unregister_msg))

    async def handle_message(self, websocket: WebSocket, connection_id: str, message_data: str):
        """Handle incoming messages from players"""
        try:
            data = json.loads(message_data)
            message_type = data.get("type", "text")

            # Add to history
            self.terminal_history.append({
                "type": message_type,
                "content": data.get("content", ""),
                "sender": "player",
                "timestamp": datetime.utcnow().isoformat(),
                "connection_id": connection_id
            })

            # Keep history manageable
            if len(self.terminal_history) > 1000:
                self.terminal_history = self.terminal_history[-500:]

            if message_type == "command":
                # Handle terminal commands
                await self.handle_command(websocket, connection_id, data)
            elif message_type == "control":
                # Handle control mode changes
                await self.handle_control_change(websocket, data)
            elif message_type == "thought":
                # Display agent thinking process
                await self.handle_thought_process(websocket, data)

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await websocket.send(json.dumps({
                "type": "error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }))

    async def handle_command(self, websocket: WebSocket, connection_id: str, data: Dict):
        """Handle terminal-style commands"""
        command = data.get("command", "").strip()
        args = data.get("args", [])

        # Add to command history
        self.command_history.append(command)

        # Process based on control mode
        if self.control_mode == "human":
            # Execute command directly
            result = await self.execute_command(command, args)
        elif self.control_mode == "agent":
            # Pass to AI decision engine
            result = await self.pass_to_agent_ai(command, args)
        elif self.control_mode == "hybrid":
            # Human oversight with AI assistance
            result = await self.hybrid_execution(command, args)
        else:
            result = {"error": "Invalid control mode"}

        # Send result
        await websocket.send(json.dumps({
            "type": "command_result",
            "command": command,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }))

    async def handle_control_change(self, websocket: WebSocket, data: Dict):
        """Handle changes to control mode"""
        new_mode = data.get("mode", "agent")
        if new_mode in ["agent", "human", "hybrid"]:
            self.control_mode = new_mode
            await websocket.send(json.dumps({
                "type": "control_mode_changed",
                "mode": new_mode,
                "message": f"Control mode changed to {new_mode}",
                "timestamp": datetime.utcnow().isoformat()
            }))

    async def handle_thought_process(self, websocket: WebSocket, data: Dict):
        """Display AI agent's thought process"""
        # This makes AI decisions transparent
        await websocket.send(json.dumps({
            "type": "agent_thought",
            "thought": data.get("thought", ""),
            "confidence": data.get("confidence", 0.0),
            "options_considered": data.get("options", []),
            "final_decision": data.get("decision", ""),
            "reasoning": data.get("reasoning", ""),
            "timestamp": datetime.utcnow().isoformat()
        }))

    async def execute_command(self, command: str, args: List[str]) -> Dict:
        """Execute command directly (human mode)"""
        # This would integrate with game engine
        return {
            "executed": True,
            "command": command,
            "args": args,
            "result": f"Executed: {command} {' '.join(args)}"
        }

    async def pass_to_agent_ai(self, command: str, args: List[str]) -> Dict:
        """Pass command to agent AI for processing"""
        # This would call the AI decision engine
        return {
            "processed_by": "agent_ai",
            "command": command,
            "args": args,
            "result": "Agent AI is processing..."
        }

    async def hybrid_execution(self, command: str, args: List[str]) -> Dict:
        """Execute with human oversight and AI assistance"""
        return {
            "processed_by": "hybrid_mode",
            "command": command,
            "human_input": True,
            "ai_assistance": True,
            "result": f"Hybrid execution: {command}"
        }

class PortalManager:
    """Manages all character portals"""

    def __init__(self, gateway_url: str):
        self.gateway_url = gateway_url
        self.active_portals: Dict[str, CharacterPortal] = {}
        self.port_pool = PortPool(start=9000, end=9500)

    async def create_character_portal(self, character_id: str) -> Optional[int]:
        """Create new portal for character"""
        if character_id in self.active_portals:
            logger.warning(f"Portal already exists for {character_id}")
            return None

        port = self.port_pool.allocate_port()
        if port is None:
            logger.error("No available ports for new character")
            return None

        portal = CharacterPortal(character_id, port, self.gateway_url)
        self.active_portals[character_id] = portal

        # Start portal in background
        asyncio.create_task(portal.start_portal())

        logger.info(f"Created portal for {character_id} on port {port}")
        return port

class PortPool:
    """Manages port allocation for character portals"""

    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end
        self.allocated_ports = set()

    def allocate_port(self) -> Optional[int]:
        """Allocate next available port"""
        for port in range(self.start, self.end + 1):
            if port not in self.allocated_ports:
                self.allocated_ports.add(port)
                return port
        return None

    def release_port(self, port: int):
        """Release allocated port"""
        self.allocated_ports.discard(port)