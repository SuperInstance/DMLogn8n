"""
Portal System Integration
Connects Character AI System with the DM Portal for seamless operation
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

from character_ai import CharacterAI, CharacterProfile, GameState
from memory_system import MemoryType, MemoryImportance


@dataclass
class PortalEvent:
    """Event structure for portal communication"""
    event_type: str
    character_id: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str = "character_ai"


@dataclass
class PortalCharacterData:
    """Character data structure for portal synchronization"""
    character_id: str
    name: str
    class_name: str
    level: int
    current_health: int
    max_health: int
    current_mana: Optional[int] = None
    max_mana: Optional[int] = None
    status: str = "active"
    position: Dict[str, Any] = None
    inventory: List[Dict[str, Any]] = None
    active_effects: List[Dict[str, Any]] = None


class PortalIntegration:
    """Integration layer between Character AI and DM Portal"""

    def __init__(self, character_ai: CharacterAI, portal_websocket_url: str = None):
        self.character_ai = character_ai
        self.portal_websocket_url = portal_websocket_url
        self.websocket_connection = None

        # Event handling
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.event_queue: List[PortalEvent] = []

        # Synchronization state
        self.last_sync_time = datetime.now()
        self.sync_interval = 1.0  # seconds
        self.auto_sync_enabled = True

        # Portal data cache
        self.portal_state_cache: Dict[str, Any] = {}
        self.character_data_cache: Dict[str, PortalCharacterData] = {}

        # Logging
        self.logger = logging.getLogger(f"PortalIntegration_{character_ai.character_id}")

        # Initialize event handlers
        self._initialize_event_handlers()

    def _initialize_event_handlers(self) -> None:
        """Initialize default event handlers"""
        self.register_event_handler("state_update", self._handle_state_update)
        self.register_event_handler("combat_start", self._handle_combat_start)
        self.register_event_handler("combat_end", self._handle_combat_end)
        self.register_event_handler("dialogue_request", self._handle_dialogue_request)
        self.register_event_handler("decision_request", self._handle_decision_request)
        self.register_event_handler("social_interaction", self._handle_social_interaction)

    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def connect_to_portal(self) -> bool:
        """Connect to the DM Portal via WebSocket"""
        try:
            # This would implement actual WebSocket connection
            # For now, we'll simulate the connection
            self.logger.info(f"Connecting to portal at {self.portal_websocket_url}")

            # Simulate successful connection
            self.websocket_connection = "simulated_connection"

            # Send character registration
            await self._register_character_with_portal()

            self.logger.info("Successfully connected to DM Portal")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to portal: {e}")
            return False

    async def _register_character_with_portal(self) -> None:
        """Register character with the portal"""
        character_data = PortalCharacterData(
            character_id=self.character_ai.character_id,
            name=self.character_ai.profile.name,
            class_name=self.character_ai.profile.character_class,
            level=self.character_ai.profile.level,
            current_health=100,  # Would get from actual character data
            max_health=100,
            current_mana=50 if self.character_ai.profile.character_class in ["Wizard", "Sorcerer", "Warlock"] else None,
            max_mana=50 if self.character_ai.profile.character_class in ["Wizard", "Sorcerer", "Warlock"] else None
        )

        await self._send_to_portal("character_register", asdict(character_data))

    async def _send_to_portal(self, event_type: str, data: Dict[str, Any]) -> None:
        """Send data to the portal"""
        event = PortalEvent(
            event_type=event_type,
            character_id=self.character_ai.character_id,
            timestamp=datetime.now(),
            data=data
        )

        # In real implementation, this would send via WebSocket
        self.logger.info(f"Sending to portal: {event_type} - {data}")

        # Add to event queue for processing
        self.event_queue.append(event)

    async def process_portal_events(self) -> None:
        """Process events from the portal"""
        while self.event_queue:
            event = self.event_queue.pop(0)
            await self._process_event(event)

    async def _process_event(self, event: PortalEvent) -> None:
        """Process a single portal event"""
        handlers = self.event_handlers.get(event.event_type, [])

        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                self.logger.error(f"Error in event handler {handler} for event {event.event_type}: {e}")

    async def _handle_state_update(self, event: PortalEvent) -> None:
        """Handle state update from portal"""
        data = event.data

        # Update game state
        game_state = GameState(
            environment=data.get("environment", {}),
            allies=data.get("allies", []),
            enemies=data.get("enemies", []),
            current_objective=data.get("objective"),
            combat_status=data.get("combat_status", False),
            resources=data.get("resources", {}),
            time_info=data.get("time_info", {})
        )

        self.character_ai.update_state(game_state)

        # Generate AI response if needed
        if data.get("request_ai_action", False):
            await self._generate_and_send_ai_response()

    async def _handle_combat_start(self, event: PortalEvent) -> None:
        """Handle combat start event"""
        enemies = event.data.get("enemies", [])
        self.character_ai.current_state.combat_status = True
        self.character_ai.current_state.enemies = enemies

        # Generate combat dialogue
        dialogue = self.character_ai.generate_dialogue(
            context={"combat_status": True, "enemies": enemies},
            dialogue_type="combat"
        )

        await self._send_to_portal("character_dialogue", {
            "character_id": self.character_ai.character_id,
            "dialogue": dialogue,
            "context": "combat_start"
        })

    async def _handle_combat_end(self, event: PortalEvent) -> None:
        """Handle combat end event"""
        self.character_ai.current_state.combat_status = False
        self.character_ai.current_state.enemies = []

        # Process combat outcomes
        outcomes = event.data.get("outcomes", {})
        for action, outcome in outcomes.items():
            self.character_ai.learn_from_outcome(action, outcome)

        # Generate post-combat dialogue
        dialogue = self.character_ai.generate_dialogue(
            context={"combat_status": False, "outcomes": outcomes},
            dialogue_type="general"
        )

        await self._send_to_portal("character_dialogue", {
            "character_id": self.character_ai.character_id,
            "dialogue": dialogue,
            "context": "combat_end"
        })

    async def _handle_dialogue_request(self, event: PortalEvent) -> None:
        """Handle dialogue request from portal"""
        context = event.data.get("context", {})
        dialogue_type = event.data.get("dialogue_type", "general")

        # Generate dialogue
        dialogue = self.character_ai.generate_dialogue(
            context=context,
            dialogue_type=dialogue_type
        )

        await self._send_to_portal("character_dialogue", {
            "character_id": self.character_ai.character_id,
            "dialogue": dialogue,
            "context": context,
            "dialogue_type": dialogue_type
        })

    async def _handle_decision_request(self, event: PortalEvent) -> None:
        """Handle decision request from portal"""
        context = event.data.get("context", {})

        # Make decision
        decision = self.character_ai.make_decision(context)

        await self._send_to_portal("character_decision", {
            "character_id": self.character_ai.character_id,
            "decision": decision,
            "context": context
        })

    async def _handle_social_interaction(self, event: PortalEvent) -> None:
        """Handle social interaction event"""
        interaction_data = event.data

        # Process social interaction
        response = self.character_ai.handle_social_interaction(interaction_data)

        await self._send_to_portal("social_response", {
            "character_id": self.character_ai.character_id,
            "response": response,
            "interaction_id": interaction_data.get("interaction_id")
        })

    async def _generate_and_send_ai_response(self) -> None:
        """Generate and send AI response based on current state"""
        context = {
            "combat_status": self.character_ai.current_state.combat_status,
            "allies": self.character_ai.current_state.allies,
            "enemies": self.character_ai.current_state.enemies,
            "environment": self.character_ai.current_state.environment
        }

        if self.character_ai.current_state.combat_status:
            # Generate combat decision
            decision = self.character_ai.make_decision(context)
            await self._send_to_portal("combat_action", decision)
        else:
            # Generate general dialogue or action
            if context.get("social_situation", False):
                dialogue = self.character_ai.generate_dialogue(context, "social")
                await self._send_to_portal("character_dialogue", {
                    "dialogue": dialogue,
                    "context": "social"
                })

    async def sync_character_state(self) -> None:
        """Synchronize character state with portal"""
        if not self.auto_sync_enabled:
            return

        # Prepare character state data
        character_status = self.character_ai.get_character_status()

        sync_data = {
            "character_id": self.character_ai.character_id,
            "status": character_status,
            "timestamp": datetime.now().isoformat()
        }

        await self._send_to_portal("character_sync", sync_data)
        self.last_sync_time = datetime.now()

    async def send_memory_update(self, memory_type: str, content: Dict[str, Any]) -> None:
        """Send memory update to portal"""
        memory_data = {
            "character_id": self.character_ai.character_id,
            "memory_type": memory_type,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }

        await self._send_to_portal("memory_update", memory_data)

    async def send_learning_update(self, learning_data: Dict[str, Any]) -> None:
        """Send learning update to portal"""
        await self._send_to_portal("learning_update", {
            "character_id": self.character_ai.character_id,
            "learning_data": learning_data,
            "timestamp": datetime.now().isoformat()
        })

    def set_portal_callback(self, callback: Callable) -> None:
        """Set callback function for portal events"""
        self.register_event_handler("portal_callback", callback)

    def update_from_portal_data(self, portal_data: Dict[str, Any]) -> None:
        """Update character AI from portal data"""
        # Update character profile if needed
        if "character_profile" in portal_data:
            profile_data = portal_data["character_profile"]
            # Update profile fields that might have changed
            if "level" in profile_data:
                self.character_ai.profile.level = profile_data["level"]

        # Update game state
        if "game_state" in portal_data:
            state_data = portal_data["game_state"]
            game_state = GameState(
                environment=state_data.get("environment", {}),
                allies=state_data.get("allies", []),
                enemies=state_data.get("enemies", []),
                current_objective=state_data.get("objective"),
                combat_status=state_data.get("combat_status", False),
                resources=state_data.get("resources", {}),
                time_info=state_data.get("time_info", {})
            )
            self.character_ai.update_state(game_state)

        # Cache portal data
        self.portal_state_cache.update(portal_data)

    def get_portal_state(self) -> Dict[str, Any]:
        """Get current portal state cache"""
        return self.portal_state_cache.copy()

    def disconnect_from_portal(self) -> None:
        """Disconnect from the portal"""
        if self.websocket_connection:
            self.websocket_connection = None
            self.logger.info("Disconnected from DM Portal")

    async def run_integration_loop(self) -> None:
        """Main integration loop"""
        try:
            while self.websocket_connection:
                # Process queued events
                await self.process_portal_events()

                # Periodic sync
                if (datetime.now() - self.last_sync_time).total_seconds() > self.sync_interval:
                    await self.sync_character_state()

                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Error in integration loop: {e}")
            self.disconnect_from_portal()


class PortalIntegrationManager:
    """Manager for multiple character AI integrations"""

    def __init__(self):
        self.integrations: Dict[str, PortalIntegration] = {}
        self.default_portal_url = "ws://localhost:8765"  # Default portal WebSocket URL

    def add_character_integration(self, character_ai: CharacterAI, portal_url: str = None) -> PortalIntegration:
        """Add a character AI integration"""
        integration = PortalIntegration(
            character_ai=character_ai,
            portal_websocket_url=portal_url or self.default_portal_url
        )

        self.integrations[character_ai.character_id] = integration
        return integration

    def get_integration(self, character_id: str) -> Optional[PortalIntegration]:
        """Get integration for specific character"""
        return self.integrations.get(character_id)

    async def connect_all(self) -> Dict[str, bool]:
        """Connect all character integrations to portal"""
        results = {}

        for character_id, integration in self.integrations.items():
            results[character_id] = await integration.connect_to_portal()

        return results

    async def disconnect_all(self) -> None:
        """Disconnect all character integrations"""
        for integration in self.integrations.values():
            integration.disconnect_from_portal()

    async def broadcast_to_all(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast event to all character integrations"""
        for integration in self.integrations.values():
            await integration._send_to_portal(event_type, data)