"""
Character Portal Server - Manages individual character portals with terminal emulation.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from .character_manager import CharacterManager
from .terminal_emulator import TerminalEmulator
from .character_state import CharacterState
from ..gateway.config import settings

logger = logging.getLogger(__name__)

class CharacterPortalServer:
    """Server for individual character portals."""

    def __init__(self, port: int, character_id: str):
        self.port = port
        self.character_id = character_id
        self.app = FastAPI(
            title=f"Character Portal - {character_id}",
            description=f"Portal for character {character_id}",
            version="1.0.0"
        )
        self.character_manager = CharacterManager(character_id)
        self.terminal_emulator = TerminalEmulator(character_id)
        self.active_connections: Dict[str, WebSocket] = {}
        self.setup_routes()

    def setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/")
        async def root():
            """Root endpoint."""
            character_state = await self.character_manager.get_character_state()
            return {
                "character_id": self.character_id,
                "portal_type": "character",
                "port": self.port,
                "status": "active",
                "character": character_state,
                "timestamp": datetime.now().isoformat()
            }

        @self.app.get("/status")
        async def get_status():
            """Get portal status."""
            return await self.get_portal_status()

        @self.app.get("/character")
        async def get_character():
            """Get character information."""
            return await self.character_manager.get_character_info()

        @self.app.post("/character/action")
        async def perform_action(action: Dict[str, Any]):
            """Perform a character action."""
            try:
                result = await self.character_manager.perform_action(action)
                await self.broadcast_event("character_action", {
                    "action": action,
                    "result": result,
                    "character_id": self.character_id
                })
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to perform action: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/character/state")
        async def update_character_state(state_update: Dict[str, Any]):
            """Update character state."""
            try:
                result = await self.character_manager.update_state(state_update)
                await self.broadcast_event("character_update", {
                    "state_update": state_update,
                    "result": result,
                    "character_id": self.character_id
                })
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to update character state: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/character/chat")
        async def send_chat_message(chat_data: Dict[str, Any]):
            """Send a chat message from character."""
            try:
                message = await self.character_manager.send_chat_message(chat_data)
                await self.broadcast_event("character_message", {
                    "message": message,
                    "character_id": self.character_id
                })
                return {"status": "success", "message": message}
            except Exception as e:
                logger.error(f"Failed to send chat message: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/terminal/command")
        async def execute_terminal_command(command_data: Dict[str, Any]):
            """Execute a terminal command."""
            try:
                command = command_data.get("command", "")
                result = await self.terminal_emulator.execute_command(command)

                await self.broadcast_event("terminal_output", {
                    "command": command,
                    "output": result,
                    "character_id": self.character_id,
                    "timestamp": datetime.now().isoformat()
                })

                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to execute terminal command: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/terminal/history")
        async def get_terminal_history():
            """Get terminal command history."""
            return await self.terminal_emulator.get_history()

        @self.app.post("/override/human")
        async def human_override(override_data: Dict[str, Any]):
            """Allow human override for character control."""
            try:
                await self.character_manager.enable_human_override(override_data)
                await self.broadcast_event("human_override_enabled", {
                    "character_id": self.character_id,
                    "reason": override_data.get("reason", "Manual control")
                })
                return {"status": "success", "message": "Human override enabled"}
            except Exception as e:
                logger.error(f"Failed to enable human override: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/override/disable")
        async def disable_human_override():
            """Disable human override."""
            try:
                await self.character_manager.disable_human_override()
                await self.broadcast_event("human_override_disabled", {
                    "character_id": self.character_id
                })
                return {"status": "success", "message": "Human override disabled"}
            except Exception as e:
                logger.error(f"Failed to disable human override: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time communication."""
            await self.handle_websocket(websocket)

        # Serve static files
        self.app.mount("/static", StaticFiles(directory="static"), name="static")

    async def handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection."""
        await websocket.accept()

        session_id = f"{self.character_id}_{datetime.now().timestamp()}"
        self.active_connections[session_id] = websocket

        logger.info(f"WebSocket connection established for {self.character_id}: {session_id}")

        try:
            # Send initial character state
            character_state = await self.character_manager.get_character_state()
            await websocket.send_text(json.dumps({
                "type": "initial_state",
                "character": character_state,
                "portal_info": await self.get_portal_status(),
                "timestamp": datetime.now().isoformat()
            }))

            # Handle messages
            while True:
                try:
                    message = await websocket.receive_text()
                    await self.handle_websocket_message(websocket, session_id, message)
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {str(e)}")
                    break

        except Exception as e:
            logger.error(f"WebSocket error for {session_id}: {str(e)}")
        finally:
            if session_id in self.active_connections:
                del self.active_connections[session_id]
            logger.info(f"WebSocket connection closed: {session_id}")

    async def handle_websocket_message(self, websocket: WebSocket, session_id: str, message: str):
        """Handle a WebSocket message."""
        try:
            data = json.loads(message)

            message_type = data.get("type")

            if message_type == "terminal_command":
                command = data.get("command", "")
                result = await self.terminal_emulator.execute_command(command)

                await websocket.send_text(json.dumps({
                    "type": "terminal_output",
                    "command": command,
                    "output": result,
                    "timestamp": datetime.now().isoformat()
                }))

                await self.broadcast_event("terminal_command", {
                    "command": command,
                    "output": result,
                    "character_id": self.character_id
                }, exclude_session=session_id)

            elif message_type == "character_action":
                result = await self.character_manager.perform_action(data.get("action", {}))
                await websocket.send_text(json.dumps({
                    "type": "action_result",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }))

                await self.broadcast_event("character_action", {
                    "action": data.get("action"),
                    "result": result,
                    "character_id": self.character_id
                }, exclude_session=session_id)

            elif message_type == "chat_message":
                message_data = data.get("message", {})
                result = await self.character_manager.send_chat_message(message_data)
                await websocket.send_text(json.dumps({
                    "type": "chat_sent",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }))

                await self.broadcast_event("character_message", {
                    "message": result,
                    "character_id": self.character_id
                })

            elif message_type == "heartbeat":
                await websocket.send_text(json.dumps({
                    "type": "heartbeat_response",
                    "timestamp": datetime.now().isoformat()
                }))

            else:
                logger.warning(f"Unknown WebSocket message type: {message_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from WebSocket: {message}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {str(e)}")

    async def broadcast_event(self, event_type: str, data: Dict[str, Any], exclude_session: Optional[str] = None):
        """Broadcast an event to all connected clients."""
        message = {
            "type": "event",
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        disconnected_sessions = []

        for session_id, websocket in self.active_connections.items():
            if exclude_session and session_id == exclude_session:
                continue

            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send event to {session_id}: {str(e)}")
                disconnected_sessions.append(session_id)

        # Remove disconnected sessions
        for session_id in disconnected_sessions:
            if session_id in self.active_connections:
                del self.active_connections[session_id]

    async def get_portal_status(self) -> Dict[str, Any]:
        """Get portal status."""
        return {
            "character_id": self.character_id,
            "port": self.port,
            "active_connections": len(self.active_connections),
            "human_override_enabled": await self.character_manager.is_human_override_enabled(),
            "terminal_active": self.terminal_emulator.is_active(),
            "last_activity": self.character_manager.get_last_activity(),
            "timestamp": datetime.now().isoformat()
        }

    async def start_server(self):
        """Start the character portal server."""
        logger.info(f"Starting character portal server for {self.character_id} on port {self.port}")

        # Initialize character manager
        await self.character_manager.initialize()

        # Start terminal emulator
        await self.terminal_emulator.start()

        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)

        await server.serve()

async def create_character_portal(character_id: str, port: int) -> CharacterPortalServer:
    """Create and start a character portal."""
    server = CharacterPortalServer(port, character_id)
    return server