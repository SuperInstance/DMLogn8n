"""
DM Portal Server - Provides comprehensive dungeon master tools and game management.
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

from .world_manager import WorldManager
from .encounter_designer import EncounterDesigner
from .event_injector import EventInjector
from .character_monitor import CharacterMonitor
from .game_state_manager import GameStateManager
from ..gateway.config import settings

logger = logging.getLogger(__name__)

class DMPortalServer:
    """Server for the Dungeon Master portal."""

    def __init__(self, port: int = 9501):
        self.port = port
        self.app = FastAPI(
            title="DM Portal Server",
            description="Dungeon Master portal for game management and world editing",
            version="1.0.0"
        )
        self.world_manager = WorldManager()
        self.encounter_designer = EncounterDesigner()
        self.event_injector = EventInjector()
        self.character_monitor = CharacterMonitor()
        self.game_state_manager = GameStateManager()
        self.active_connections: Dict[str, WebSocket] = {}
        self.setup_routes()

    def setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "portal_type": "dm",
                "port": self.port,
                "status": "active",
                "timestamp": datetime.now().isoformat(),
                "features": [
                    "World Management",
                    "Encounter Designer",
                    "Event Injection",
                    "Character Monitoring",
                    "Game State Management"
                ]
            }

        @self.app.get("/status")
        async def get_status():
            """Get portal status."""
            return await self.get_portal_status()

        # World Management Routes
        @self.app.get("/world")
        async def get_world():
            """Get current world state."""
            return await self.world_manager.get_world_state()

        @self.app.post("/world/update")
        async def update_world(world_data: Dict[str, Any]):
            """Update world state."""
            try:
                result = await self.world_manager.update_world(world_data)
                await self.broadcast_event("world_updated", result)
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to update world: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/world/location/create")
        async def create_location(location_data: Dict[str, Any]):
            """Create a new location."""
            try:
                result = await self.world_manager.create_location(location_data)
                await self.broadcast_event("location_created", result)
                return {"status": "success", "location": result}
            except Exception as e:
                logger.error(f"Failed to create location: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/world/locations")
        async def get_locations():
            """Get all locations."""
            return await self.world_manager.get_locations()

        # Encounter Designer Routes
        @self.app.get("/encounters")
        async def get_encounters():
            """Get all encounters."""
            return await self.encounter_designer.get_encounters()

        @self.app.post("/encounters/create")
        async def create_encounter(encounter_data: Dict[str, Any]):
            """Create a new encounter."""
            try:
                result = await self.encounter_designer.create_encounter(encounter_data)
                await self.broadcast_event("encounter_created", result)
                return {"status": "success", "encounter": result}
            except Exception as e:
                logger.error(f"Failed to create encounter: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/encounters/{encounter_id}/start")
        async def start_encounter(encounter_id: str):
            """Start an encounter."""
            try:
                result = await self.encounter_designer.start_encounter(encounter_id)
                await self.broadcast_event("encounter_started", result)
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to start encounter: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/encounters/{encounter_id}/end")
        async def end_encounter(encounter_id: str):
            """End an encounter."""
            try:
                result = await self.encounter_designer.end_encounter(encounter_id)
                await self.broadcast_event("encounter_ended", result)
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to end encounter: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # Event Injection Routes
        @self.app.post("/events/inject")
        async def inject_event(event_data: Dict[str, Any]):
            """Inject a game event."""
            try:
                result = await self.event_injector.inject_event(event_data)
                await self.broadcast_event("event_injected", result)
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to inject event: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/events/pending")
        async def get_pending_events():
            """Get pending events."""
            return await self.event_injector.get_pending_events()

        @self.app.post("/events/{event_id}/resolve")
        async def resolve_event(event_id: str, resolution: Dict[str, Any]):
            """Resolve an event."""
            try:
                result = await self.event_injector.resolve_event(event_id, resolution)
                await self.broadcast_event("event_resolved", result)
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to resolve event: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # Character Monitoring Routes
        @self.app.get("/characters")
        async def get_characters():
            """Get all characters."""
            return await self.character_monitor.get_characters()

        @self.app.get("/characters/{character_id}")
        async def get_character(character_id: str):
            """Get specific character information."""
            return await self.character_monitor.get_character(character_id)

        @self.app.post("/characters/{character_id}/update")
        async def update_character(character_id: str, update_data: Dict[str, Any]):
            """Update character information."""
            try:
                result = await self.character_monitor.update_character(character_id, update_data)
                await self.broadcast_event("character_updated", result)
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to update character: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/characters/{character_id}/message")
        async def send_character_message(character_id: str, message_data: Dict[str, Any]):
            """Send a message to a character."""
            try:
                result = await self.character_monitor.send_message(character_id, message_data)
                await self.broadcast_event("character_message_sent", result)
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to send character message: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # Game State Management Routes
        @self.app.get("/game/state")
        async def get_game_state():
            """Get current game state."""
            return await self.game_state_manager.get_state()

        @self.app.post("/game/state/update")
        async def update_game_state(state_update: Dict[str, Any]):
            """Update game state."""
            try:
                result = await self.game_state_manager.update_state(state_update)
                await self.broadcast_event("game_state_updated", result)
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to update game state: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/game/backup")
        async def create_backup():
            """Create a game state backup."""
            try:
                result = await self.game_state_manager.create_backup()
                return {"status": "success", "backup": result}
            except Exception as e:
                logger.error(f"Failed to create backup: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/game/restore")
        async def restore_backup(backup_id: str):
            """Restore from backup."""
            try:
                result = await self.game_state_manager.restore_backup(backup_id)
                await self.broadcast_event("game_restored", result)
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Failed to restore backup: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        # Utility Routes
        @self.app.get("/logs")
        async def get_logs(limit: int = 100):
            """Get system logs."""
            return await self._get_system_logs(limit)

        @self.app.post("/broadcast")
        async def broadcast_to_all(broadcast_data: Dict[str, Any]):
            """Broadcast message to all connected clients."""
            await self.broadcast_event("dm_broadcast", broadcast_data)
            return {"status": "success", "message": "Broadcast sent"}

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time communication."""
            await self.handle_websocket(websocket)

        # Serve static files
        self.app.mount("/static", StaticFiles(directory="static"), name="static")

    async def handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection."""
        await websocket.accept()

        session_id = f"dm_{datetime.now().timestamp()}"
        self.active_connections[session_id] = websocket

        logger.info(f"DM WebSocket connection established: {session_id}")

        try:
            # Send initial state
            initial_state = await self._get_initial_state()
            await websocket.send_text(json.dumps({
                "type": "initial_state",
                "state": initial_state,
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
            logger.info(f"DM WebSocket connection closed: {session_id}")

    async def handle_websocket_message(self, websocket: WebSocket, session_id: str, message: str):
        """Handle a WebSocket message."""
        try:
            data = json.loads(message)

            message_type = data.get("type")

            if message_type == "request_update":
                update_type = data.get("update_type")
                await self._handle_update_request(websocket, update_type)

            elif message_type == "world_edit":
                await self._handle_world_edit(websocket, data.get("edit_data", {}))

            elif message_type == "encounter_action":
                await self._handle_encounter_action(websocket, data.get("action_data", {}))

            elif message_type == "character_action":
                await self._handle_character_action(websocket, data.get("action_data", {}))

            elif message_type == "game_control":
                await self._handle_game_control(websocket, data.get("control_data", {}))

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

    async def _handle_update_request(self, websocket: WebSocket, update_type: str):
        """Handle update requests from client."""
        if update_type == "world":
            data = await self.world_manager.get_world_state()
        elif update_type == "characters":
            data = await self.character_monitor.get_characters()
        elif update_type == "encounters":
            data = await self.encounter_designer.get_encounters()
        elif update_type == "game_state":
            data = await self.game_state_manager.get_state()
        else:
            data = {"error": f"Unknown update type: {update_type}"}

        await websocket.send_text(json.dumps({
            "type": "update_response",
            "update_type": update_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }))

    async def _handle_world_edit(self, websocket: WebSocket, edit_data: Dict[str, Any]):
        """Handle world edit requests."""
        try:
            result = await self.world_manager.process_edit(edit_data)
            await self.broadcast_event("world_edited", result)

            await websocket.send_text(json.dumps({
                "type": "edit_result",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"World edit failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))

    async def _handle_encounter_action(self, websocket: WebSocket, action_data: Dict[str, Any]):
        """Handle encounter action requests."""
        try:
            result = await self.encounter_designer.process_action(action_data)
            await self.broadcast_event("encounter_action_processed", result)

            await websocket.send_text(json.dumps({
                "type": "action_result",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Encounter action failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))

    async def _handle_character_action(self, websocket: WebSocket, action_data: Dict[str, Any]):
        """Handle character action requests."""
        try:
            character_id = action_data.get("character_id")
            action = action_data.get("action")

            result = await self.character_monitor.process_action(character_id, action)
            await self.broadcast_event("character_action_processed", result)

            await websocket.send_text(json.dumps({
                "type": "action_result",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Character action failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))

    async def _handle_game_control(self, websocket: WebSocket, control_data: Dict[str, Any]):
        """Handle game control requests."""
        try:
            action = control_data.get("action")

            if action == "pause":
                result = await self.game_state_manager.pause_game()
            elif action == "resume":
                result = await self.game_state_manager.resume_game()
            elif action == "reset":
                result = await self.game_state_manager.reset_game()
            elif action == "save":
                result = await self.game_state_manager.save_game()
            else:
                result = {"error": f"Unknown control action: {action}"}

            await self.broadcast_event("game_control_action", result)

            await websocket.send_text(json.dumps({
                "type": "control_result",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Game control failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))

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

    async def _get_initial_state(self) -> Dict[str, Any]:
        """Get initial state for new connections."""
        return {
            "world": await self.world_manager.get_world_state(),
            "characters": await self.character_monitor.get_characters(),
            "encounters": await self.encounter_designer.get_encounters(),
            "game_state": await self.game_state_manager.get_state(),
            "pending_events": await self.event_injector.get_pending_events()
        }

    async def _get_system_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get system logs."""
        # This would integrate with a proper logging system
        return [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": "DM Portal System operational",
                "source": "dm_portal"
            }
        ]

    async def get_portal_status(self) -> Dict[str, Any]:
        """Get portal status."""
        return {
            "portal_type": "dm",
            "port": self.port,
            "active_connections": len(self.active_connections),
            "world_manager_status": await self.world_manager.get_status(),
            "encounter_designer_status": await self.encounter_designer.get_status(),
            "character_monitor_status": await self.character_monitor.get_status(),
            "game_state_status": await self.game_state_manager.get_status(),
            "timestamp": datetime.now().isoformat()
        }

    async def start_server(self):
        """Start the DM portal server."""
        logger.info(f"Starting DM portal server on port {self.port}")

        # Initialize all managers
        await self.world_manager.initialize()
        await self.encounter_designer.initialize()
        await self.event_injector.initialize()
        await self.character_monitor.initialize()
        await self.game_state_manager.initialize()

        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)

        await server.serve()

async def create_dm_portal(port: int = 9501) -> DMPortalServer:
    """Create and start a DM portal."""
    server = DMPortalServer(port)
    return server