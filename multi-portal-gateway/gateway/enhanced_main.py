"""
Enhanced Multi-Portal Gateway - Orchestrates Entire D&D Agent System
Integrates all components: character terminals, AI transparency, coder bots, living world
"""
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from .character_portal import CharacterPortal, PortalManager
from .message_router import MessageRouter
from .ai_transparency import AITransparency
from .coder_bot import CoderBot
from .memory_system import MemoryManager
from .living_world import LivingWorld

logger = logging.getLogger(__name__)

class EnhancedDnDGateway:
    """Enhanced Gateway for D&D Agent Arena with full human-AI interaction"""

    def __init__(self):
        self.portal_manager = PortalManager("http://localhost:8001")
        self.message_router = MessageRouter()
        self.ai_transparency = AITransparency()
        self.coder_bot = CoderBot(
            model_endpoint="http://localhost:11434/api/generate",
            api_key="your-glm4-key"
        )
        self.memory_manager = MemoryManager()
        self.living_world = LivingWorld()

        # Game state
        self.active_sessions: Dict[str, Dict] = {}
        self.world_state = {}
        self.player_connections: Set[str] = set()
        self.dm_connections: Set[str] = set()

    async def start(self):
        """Start the enhanced gateway"""
        logger.info("Starting Enhanced D&D Multi-Portal Gateway")

        # Initialize all systems
        await self.initialize_systems()

        # Start WebSocket server for routing
        server = await self.start_websocket_server()

        logger.info("Enhanced gateway started successfully")

    async def initialize_systems(self):
        """Initialize all connected systems"""
        # Load existing game state
        await self.load_game_state()

        # Initialize AI transparency
        await self.ai_transparency.initialize()

        # Initialize memory manager
        await self.memory_manager.initialize()

        # Initialize living world
        await self.living_world.initialize()

    async def start_websocket_server(self):
        """Start main WebSocket server"""
        import websockets

        async def handle_client(websocket, path):
            """Handle incoming WebSocket connections"""
            connection_id = str(uuid.uuid4())

            try:
                if path.startswith("/ws/characters/"):
                    # Character portal connection
                    character_id = path.split("/")[-1]
                    await self.handle_character_connection(connection_id, websocket, character_id)

                elif path.startswith("/ws/players/"):
                    # Player connection
                    await self.handle_player_connection(connection_id, websocket)

                elif path.startswith("/ws/dm/"):
                    # DM connection
                    await self.handle_dm_connection(connection_id, websocket)

                else:
                    logger.warning(f"Unknown path: {path}")
                    await websocket.close()

            except Exception as e:
                logger.error(f"Error handling client: {e}")
                await websocket.close()

        return await websockets.serve("localhost", 8001, handle_client)

    async def handle_character_connection(self, connection_id: str, websocket, character_id: str):
        """Handle character portal connection"""
        # Create character portal
        port = await self.portal_manager.create_character_portal(character_id)

        if port is None:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "No available ports for character"
            }))
            return

        # Store connection
        self.active_sessions[connection_id] = {
            "type": "character",
            "character_id": character_id,
            "port": port,
            "websocket": websocket,
            "control_mode": "agent",
            "observers": set()
        }

        # Start character portal in background
        asyncio.create_task(self.portal_manager.create_character_portal(character_id))

        await websocket.send(json.dumps({
            "type": "connected",
            "message": f"Character {character_id} connected on port {port}",
            "character_id": character_id,
            "port": port,
            "control_modes": ["agent", "human", "hybrid"],
            "features": {
                "terminal": True,
                "inventory": True,
                "stats": True,
                "ai_transparency": True
            }
        }))

    async def handle_player_connection(self, connection_id: str, websocket):
        """Handle player connection to game"""
        self.player_connections.add(connection_id)

        # Get available characters to observe
        observable_characters = await self.get_observable_characters()

        self.active_sessions[connection_id] = {
            "type": "player",
            "websocket": websocket,
            "observable_characters": observable_characters,
            "viewing_character": None,
            "active_quests": []
        }

        await websocket.send(json.dumps({
            "type": "connected",
            "message": "Connected to D&D game as player",
            "features": {
                "character_list": list(observable_characters.keys()),
                "observe_ai": True,
                "quest_tracking": True
            }
        }))

    async def handle_dm_connection(self, connection_id: str, websocket):
        """Handle DM connection"""
        self.dm_connections.add(connection_id)

        self.active_sessions[connection_id] = {
            "type": "dm",
            "websocket": websocket,
            "controlled_regions": set(),
            "world_editing": True,
            "encounter_control": True,
            "player_management": True
        }

        await websocket.send(json.dumps({
            "type": "connected",
            "message": "Connected as Dungeon Master",
            "features": {
                "world_editor": True,
                "encounter_builder": True,
                "quest_generator": True,
                "player_tools": True,
                "ai_control": True
            }
        }))

    async def handle_character_message(self, connection_id: str, message: Dict):
        """Route message from character portal"""
        session_info = self.active_sessions.get(connection_id)
        if not session_info:
            return

        character_id = session_info["character_id"]

        # Determine message type and route
        if message.get("type") == "thought":
            # AI thought process - make transparent
            await self.ai_transparency.start_thought_process(
                character_id,
                message.get("situation", {}),
                message.get("options", [])
            )
        elif message.get("type") == "action":
            # Character action - process through living world
            await self.living_world.process_action(character_id, message)
        elif message.get("type") == "speech":
            # Dialogue - broadcast to nearby
            await self.message_router.handle_dialogue(
                session_info,
                message.get("content", ""),
                message.get("emotion", "neutral")
            )
        elif message.get("type") == "coder_request":
            # Request to coder bot
            await self.message_router.handle_coder_request(
                session_info,
                message.get("request_type", "automation"),
                message.get("parameters", {})
            )

    async def process_message(self, connection_id: str, message: Dict):
        """Process and route message appropriately"""
        msg_type = message.get("type", "text")
        sender_info = self.active_sessions.get(connection_id)

        if not sender_info:
            logger.warning(f"Message from unknown connection: {connection_id}")
            return

        # Use message router for complex routing
        await self.message_router.route_message(
            sender_info["character_id"] or sender_info.get("player_id", "Unknown"),
            message,
            connection_id
        )

    async def get_observable_characters(self) -> Dict[str, Dict]:
        """Get list of characters players can observe"""
        # This would return characters with AI transparency enabled
        observable = {}

        for session_id, session in self.active_sessions.items():
            if session["type"] == "character":
                char_id = session["character_id"]
                # Check if character has transparency enabled
                memory_system = await self.memory_manager.get_character_memory(char_id)
                if memory_system:
                    observable[char_id] = {
                        "name": char_id,
                        "location": "Unknown",  # Would get from world state
                        "transparency_enabled": True,
                        "thought_process_visible": True
                    }

        return observable

    async def load_game_state(self):
        """Load persistent game state"""
        # This would load from database
        logger.info("Loading game state...")
        # Placeholder implementation
        self.world_state = {
            "regions": {},
            "active_quests": {},
            "global_events": [],
            "time": datetime.utcnow().isoformat()
        }

    async def save_game_state(self):
        """Save current game state"""
        # This would save to database
        logger.info("Saving game state...")
        # Placeholder implementation

    async def run_game_loop(self):
        """Main game loop processing"""
        logger.info("Starting game loop...")

        while True:
            try:
                # Process world events
                await self.living_world.process_tick()

                # Update AI processes
                await self.ai_transparency.update_all_processes()

                # Memory consolidation
                await self.memory_manager.consolidate_all_memories()

                # Save state periodically
                await asyncio.sleep(60)  # Save every minute

            except Exception as e:
                logger.error(f"Error in game loop: {e}")
                await asyncio.sleep(5)

# Game coordinator class
class GameCoordinator:
    """Coordinates all systems together"""

    def __init__(self):
        self.gateway = EnhancedDnDGateway()
        self.game_loop_task = None

    async def start(self):
        """Start the entire coordinated system"""
        logger.info("Starting D&D Agent Arena Coordinator")

        # Start gateway
        await self.gateway.start()

        # Start game loop
        self.game_loop_task = asyncio.create_task(self.gateway.run_game_loop())

        logger.info("All systems started successfully")

    async def stop(self):
        """Stop all systems gracefully"""
        logger.info("Stopping D&D Agent Arena...")

        if self.game_loop_task:
            self.game_loop_task.cancel()

        logger.info("All systems stopped")

# Export main classes
__all__ = [
    "EnhancedDnDGateway",
    "CharacterPortal",
    "PortalManager",
    "MessageRouter",
    "AITransparency",
    "CoderBot",
    "MemoryManager",
    "LivingWorld",
    "GameCoordinator"
]