"""
Living World System - Dynamic Game State Evolution
The world changes and evolves based on player and agent actions
"""
import asyncio
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ChangeType(Enum):
    COMBAT = "combat"
    EXPLORATION = "exploration"
    SOCIAL = "social"
    QUEST = "quest"
    WORLD_EDIT = "world_edit"
    ITEM_CREATION = "item_creation"
    CRAFTING = "crafting"
    ECONOMIC = "economic"

class WorldEvent:
    """A change to the world state"""

    def __init__(self, change_type: ChangeType, actor_id: str, location: str,
                 old_state: Dict, new_state: Dict, description: str):
        self.id = str(uuid.uuid4())
        self.change_type = change_type
        self.actor_id = actor_id
        self.location = location
        self.old_state = old_state
        self.new_state = new_state
        self.description = description
        self.timestamp = datetime.utcnow()
        self.impact_score = self.calculate_impact()
        self.propagation_radius = self.calculate_propagation()
        self.permanent = change_type in [ChangeType.WORLD_EDIT, ChangeType.ITEM_CREATION]

    def calculate_impact(self) -> float:
        """Calculate how significant this change is"""
        if self.change_type == ChangeType.COMBAT:
            return 0.5  # Minor combat changes
        elif self.change_type == ChangeType.QUEST:
            return 1.0  # Quest completion affects area
        elif self.change_type == ChangeType.WORLD_EDIT:
            return 2.0  # World edits are significant
        elif self.change_type == ChangeType.ECONOMIC:
            return 1.5  # Economic changes affect regions
        else:
            return 0.3

    def calculate_propagation(self) -> int:
        """How far this change spreads"""
        if self.permanent:
            return 50  # Permanent changes propagate far
        elif self.impact_score > 1.5:
            return 20
        elif self.impact_score > 1.0:
            return 10
        else:
            return 5

class LivingWorld:
    """Manages the dynamic game world that evolves"""

    def __init__(self):
        self.regions: Dict[str, Region] = {}  # world regions
        self.locations: Dict[str, Location] = {}  # specific places
        self.npcs: Dict[str, NPC] = {}  # living NPCs
        self.quests: Dict[str, Quest] = {}  # active quests
        self.world_history: List[WorldEvent] = []
        self.propagation_queue: List[WorldEvent] = []
        self.evolution_rules = self.load_evolution_rules()

    async def initialize_world(self):
        """Initialize the living world"""
        logger.info("Initializing Living World system")

        # Load or create initial world state
        await self.load_world_state()
        await self.spawn_initial_npcs()
        await self.generate_dynamic_quests()

    async def process_action(self, actor_id: str, action: Dict, location: str):
        """Process an action that changes the world"""
        location = self.get_or_create_location(location)

        # Determine action type
        action_type = self.classify_action(action)

        # Get current state
        old_state = self.get_current_state(location, actor_id)

        # Apply action effects
        new_state = await self.apply_action_effects(actor_id, action, location, old_state)

        # Create world event
        world_event = WorldEvent(
            change_type=action_type,
            actor_id=actor_id,
            location=location,
            old_state=old_state,
            new_state=new_state,
            description=self.generate_event_description(action, action_type, new_state)
        )

        # Record the change
        await self.record_world_event(world_event)

        # Propagate changes to connected areas
        await self.propagate_changes(world_event)

        # Update dependent systems
        await self.update_dependent_systems(world_event)

    def classify_action(self, action: Dict) -> ChangeType:
        """Classify action type for world changes"""
        action_name = action.get("action", "").lower()

        if any(word in action_name for word in ["attack", "damage", "kill", "destroy"]):
            return ChangeType.COMBAT
        elif any(word in action_name for word in ["explore", "discover", "search"]):
            return ChangeType.EXPLORATION
        elif any(word in action_name for word in ["talk", "persuade", "trade", "quest"]):
            return ChangeType.SOCIAL
        elif action_name.startswith("quest_"):
            return ChangeType.QUEST
        elif any(word in action_name for word in ["create", "build", "craft", "enchant"]):
            return ChangeType.ITEM_CREATION
        elif any(word in action_name for word in ["sell", "buy", "trade"]):
            return ChangeType.ECONOMIC
        else:
            return ChangeType.WORLD_EDIT

    async def apply_action_effects(self, actor_id: str, action: Dict, location: str, old_state: Dict) -> Dict:
        """Apply effects of an action to world state"""
        new_state = old_state.copy()
        effects = []

        action_name = action.get("action", "")

        if action_name in ["attack"]:
            # Combat effects
            target = action.get("target", None)
            if target:
                effects.append(f"Damaged {target}")
                if actor_id in new_state.get("allies", []):
                    new_state["allies"].remove(target)
                if target in new_state.get("enemies", []):
                    new_state["enemies"].remove(target)

        elif action_name in ["talk"]:
            # Social effects
            npc = action.get("target", None)
            if npc:
                relationship = new_state.get("relationships", {}).get(npc, 0)
                new_state["relationships"][npc] = min(100, relationship + 5)

        elif action_name in ["create", "build"]:
            # Creation effects
            item = action.get("item", "unknown_item")
            if actor_id not in new_state.get("inventory", []):
                new_state["inventory"] = [item]

        # Apply all effects to state
        for effect in effects:
            new_state["recent_effects"].append(f"{actor_id}: {effect}")

        # Update actor stats
        await self.update_actor_stats(actor_id, action)

        return new_state

    def generate_event_description(self, action: Dict, change_type: ChangeType, state: Dict) -> str:
        """Generate narrative description of world event"""
        actor_id = action.get("actor_id", "Unknown")
        action_name = action.get("action", "did something")

        templates = {
            ChangeType.COMBAT: f"{actor_id} engaged in combat",
            ChangeType.EXPLORATION: f"{actor_id} discovered something new",
            ChangeType.SOCIAL: f"{actor_id} {action_name}",
            ChangeType.QUEST: f"{actor_id} completed a quest",
            ChangeType.WORLD_EDIT: f"{actor_id} changed the world",
            ChangeType.ITEM_CREATION: f"{actor_id} created {action.get('item', 'something')}",
            ChangeType.ECONOMIC: f"{actor_id} performed an economic action"
        }

        return templates.get(change_type, f"Unknown event occurred")

    async def record_world_event(self, event: WorldEvent):
        """Record a world event in history"""
        self.world_history.append(event)

        # Keep history manageable
        if len(self.world_history) > 10000:
            self.world_history = self.world_history[-5000:]

        # Log significant events
        if event.impact_score > 1.5:
            logger.info(f"Significant world event: {event.description}")

    async def propagate_changes(self, event: WorldEvent):
        """Propagate changes to nearby areas and NPCs"""
        location = self.locations.get(event.location)
        if not location:
            return

        # Notify nearby locations
        for nearby_location_id in location.connected_areas:
            nearby_location = self.locations.get(nearby_location_id)
            if nearby_location and nearby_location.distance <= event.propagation_radius:
                await self.update_location_knowledge(nearby_location_id, event)

        # Update NPC reactions
        for npc_id in location.npcs:
            npc = self.npcs.get(npc_id)
            if npc and self.should_npc_react(npc, event):
                await self.update_npc_state(npc_id, event)

    async def update_dependent_systems(self, event: WorldEvent):
        """Update quests, NPCs, and other systems"""
        # Update active quests in area
        await self.update_local_quests(event)

        # Update AI agent knowledge
        if event.actor_id:
            await self.update_agent_knowledge(event.actor_id, event)

    async def spawn_initial_npcs(self):
        """Create initial NPCs"""
        # Create some starting NPCs
        npcs_to_create = [
            {
                "id": "town_crier",
                "name": "Town Crier",
                "type": "information",
                "personality": "helpful",
                "location": "town_square"
            },
            {
                "id": "merchant_guildmaster",
                "name": "Guildmaster",
                "type": "merchant",
                "personality": "business_savvy",
                "location": "market_district"
            },
            {
                "id": "old_wiseman",
                "name": "Elara the Wise",
                "type": "quest_giver",
                "personality": "mysterious",
                "location": "wizard_tower"
            }
        ]

        for npc_data in npcs_to_create:
            self.npcs[npc_data["id"]] = NPC(**npc_data)

    def should_npc_react(self, npc: 'NPC', event: WorldEvent) -> bool:
        """Determine if NPC should react to event"""
        # NPCs react to events in their area or related to them
        if npc.location == event.location:
            return True
        if event.actor_id in npc.relationships:
            return True
        if event.change_type in [ChangeType.COMBAT, ChangeType.SOCIAL]:
            return True
        return False

    def load_evolution_rules(self) -> Dict:
        """Load world evolution rules"""
        return {
            "combat_casualties": True,  # NPCs can die
            "resource_depletion": True,  # Resources can be exhausted
            "npc_evolution": True,  # NPCs can learn and change
            "player_influence": True,  # Players can change world permanently
            "seasonal_changes": True,  # World changes with seasons
            "disaster_events": True  # Random disasters can occur
        }

    async def generate_dynamic_quests(self):
        """Generate new quests based on world state"""
        # Analyze current world conditions
        for region in self.regions.values():
            if region.should_generate_quest():
                quest = await self.create_quest_for_region(region)
                self.quests[quest.id] = quest

    async def create_quest_for_region(self, region: 'Region') -> 'Quest':
        """Create a quest appropriate for a region"""
        return Quest(
            id=str(uuid.uuid4()),
            region_id=region.id,
            title=f"Help {region.name}",
            description=f"Something troubles {region.name}",
            objectives=[
                {
                    "type": "investigate",
                    "description": "Find source of trouble"
                },
                {
                    "type": "combat",
                    "description": "Deal with threat"
                }
            ],
            rewards=self.calculate_quest_rewards(region),
            difficulty=self.calculate_quest_difficulty(region)
        )

    def calculate_quest_rewards(self, region: 'Region') -> Dict:
        """Calculate appropriate quest rewards"""
        return {
            "experience": 100 * region.danger_level,
            "gold": 50 * region.danger_level,
            "items": self.generate_region_items(region)
        }

    def calculate_quest_difficulty(self, region: 'Region') -> str:
        """Calculate quest difficulty based on region"""
        if region.danger_level < 3:
            return "easy"
        elif region.danger_level < 7:
            return "medium"
        else:
            return "hard"

    async def update_location_knowledge(self, location_id: str, event: WorldEvent):
        """Update what NPCs know about a location"""
        location = self.locations.get(location_id)
        if not location:
            return

        # Add event to location's known history
        location.known_events.append({
            "event_id": event.id,
            "type": event.change_type.value,
            "description": event.description,
            "timestamp": event.timestamp
        })

    async def update_npc_state(self, npc_id: str, event: WorldEvent):
        """Update NPC's state based on world events"""
        npc = self.npcs.get(npc_id)
        if not npc:
            return

        # NPCs learn from events
        if event.change_type == ChangeType.COMBAT:
            npc.combat_experience += 1
        elif event.change_type == ChangeType.SOCIAL:
            npc.social_experience += 1

        # Update NPC goals based on events
        await self.update_npc_goals(npc_id)

    async def update_agent_knowledge(self, agent_id: str, event: WorldEvent):
        """Update AI agent's knowledge about the world"""
        # This would integrate with the agent's memory system
        # Record that this agent caused this change
        knowledge = {
            "event_id": event.id,
            "change_type": event.change_type.value,
            "location": event.location,
            "outcome": "success",
            "timestamp": event.timestamp
        }

        # Store in agent's knowledge base
        logger.info(f"Updating knowledge for agent {agent_id}: {knowledge}")

    def get_or_create_location(self, location_id: str) -> 'Location':
        """Get existing location or create new one"""
        if location_id in self.locations:
            return self.locations[location_id]

        # Create new location
        new_location = Location(
            id=location_id,
            name="Unknown Location",
            description="A newly discovered place",
            connected_areas=[],
            npcs=[],
            known_events=[],
            danger_level=1.0
        )

        self.locations[location_id] = new_location
        return new_location

class Region:
    """World region with properties"""

    def __init__(self, region_id: str, name: str):
        self.id = region_id
        self.name = name
        self.locations: Set[str] = set()
        self.danger_level = 1.0
        self.wealth_level = 1.0
        self.stability = 100

    def should_generate_quest(self) -> bool:
        """Check if region should generate new quest"""
        return len(self.quests_active) < 5 and self.stability > 50

class Location:
    """Specific location in the world"""

    def __init__(self, location_id: str):
        self.id = location_id
        self.name = ""
        self.description = ""
        self.connected_areas: List[str] = []
        self.npcs: List[str] = []
        self.known_events: List[Dict] = []
        self.danger_level = 1.0
        self.resources: Dict[str, int] = {}
        self.discovered_by: Set[str] = set()

class NPC:
    """Living Non-Player Character"""

    def __init__(self, npc_id: str, name: str, npc_type: str, personality: str, location: str):
        self.id = npc_id
        self.name = name
        self.type = npc_type
        self.personality = personality
        self.location = location
        self.combat_experience = 0
        self.social_experience = 0
        self.relationships: Dict[str, int] = {}  # relationship_value with other entities
        self.known_players: Set[str] = set()
        self.current_goal = ""
        self.inventory: List[str] = []
        self.quests_active: List[str] = []

class Quest:
    """Dynamic quest that changes based on world state"""

    def __init__(self, quest_id: str, region_id: str, title: str, description: str):
        self.id = quest_id
        self.region_id = region_id
        self.title = title
        self.description = description
        self.objectives: List[Dict] = []
        self.rewards: Dict = {}
        self.difficulty = "medium"
        self.active = True
        self.completed_by: Set[str] = set()
        self.failed_attempts: int = 0