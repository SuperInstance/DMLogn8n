"""
Encounter Designer - Design, create, and manage game encounters.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import random

logger = logging.getLogger(__name__)

class EncounterStatus(Enum):
    """Encounter status enumeration."""
    DESIGNING = "designing"
    READY = "ready"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

class EncounterType(Enum):
    """Encounter type enumeration."""
    COMBAT = "combat"
    SOCIAL = "social"
    EXPLORATION = "exploration"
    PUZZLE = "puzzle"
    SKILL_CHALLENGE = "skill_challenge"
    BOSS = "boss"
    RANDOM = "random"

@dataclass
class EncounterCreature:
    """Represents a creature in an encounter."""
    id: str
    name: str
    creature_type: str
    hp: int
    max_hp: int
    ac: int
    initiative: int = 0
    position: Dict[str, float] = None
    status: str = "active"
    abilities: List[Dict[str, Any]] = None
    ai_behavior: str = "default"
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.position is None:
            self.position = {"x": 0, "y": 0}
        if self.abilities is None:
            self.abilities = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class EncounterObjective:
    """Represents an objective in an encounter."""
    id: str
    description: str
    objective_type: str  # defeat, protect, retrieve, survive, etc.
    target: Optional[str] = None
    required_quantity: int = 1
    current_quantity: int = 0
    completed: bool = False
    failure_condition: Optional[str] = None

@dataclass
class Encounter:
    """Represents a game encounter."""
    id: str
    name: str
    description: str
    encounter_type: EncounterType
    difficulty: str  # easy, medium, hard, deadly
    status: EncounterStatus
    location: str
    creatures: List[EncounterCreature]
    objectives: List[EncounterObjective]
    environment: Dict[str, Any]
    rewards: Dict[str, Any]
    time_limit: Optional[int] = None
    turn_order: List[str] = None
    current_turn: int = 0
    round_number: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.turn_order is None:
            self.turn_order = []
        if self.metadata is None:
            self.metadata = {}

class EncounterDesigner:
    """Designs and manages game encounters."""

    def __init__(self):
        self.encounters: Dict[str, Encounter] = {}
        self.active_encounter: Optional[str] = None
        self.encounter_templates: Dict[str, Dict[str, Any]] = {}
        self.creature_templates: Dict[str, Dict[str, Any]] = {}
        self.is_initialized = False

    async def initialize(self):
        """Initialize the encounter designer."""
        logger.info("Initializing Encounter Designer...")

        # Load templates
        await self._load_encounter_templates()
        await self._load_creature_templates()

        self.is_initialized = True
        logger.info("Encounter Designer initialized")

    async def _load_encounter_templates(self):
        """Load encounter templates."""
        self.encounter_templates = {
            "goblin_ambush": {
                "name": "Goblin Ambush",
                "description": "A group of goblins attempts to ambush the party.",
                "encounter_type": EncounterType.COMBAT,
                "difficulty": "easy",
                "creatures": [
                    {"name": "Goblin", "creature_type": "goblin", "hp": 7, "ac": 15, "count": 3},
                    {"name": "Goblin Boss", "creature_type": "goblin_boss", "hp": 15, "ac": 16, "count": 1}
                ],
                "objectives": [
                    {"description": "Defeat all goblins", "objective_type": "defeat"}
                ],
                "environment": {"terrain": "forest", "visibility": "medium", "cover": "available"},
                "rewards": {"xp": 100, "gold": 25}
            },
            "social_negotiation": {
                "name": "Town Council Negotiation",
                "description": "Negotiate with the town council for support.",
                "encounter_type": EncounterType.SOCIAL,
                "difficulty": "medium",
                "creatures": [
                    {"name": "Mayor", "creature_type": "npc", "hp": 10, "ac": 10},
                    {"name": "Guard Captain", "creature_type": "npc", "hp": 15, "ac": 14},
                    {"name": "Merchant Guild Rep", "creature_type": "npc", "hp": 8, "ac": 12}
                ],
                "objectives": [
                    {"description": "Gain council support", "objective_type": "persuade", "target": "Mayor"},
                    {"description": "Secure funding", "objective_type": "negotiate", "target": "Merchant Guild Rep"}
                ],
                "environment": {"terrain": "town_hall", "visibility": "good", "atmosphere": "formal"},
                "rewards": {"xp": 150, "reputation": 10}
            },
            "ancient_puzzle": {
                "name": "Ancient Door Puzzle",
                "description": "Solve the ancient puzzle to unlock the door.",
                "encounter_type": EncounterType.PUZZLE,
                "difficulty": "hard",
                "creatures": [],
                "objectives": [
                    {"description": "Solve the riddle", "objective_type": "solve"},
                    {"description": "Unlock the door", "objective_type": "unlock"}
                ],
                "environment": {"terrain": "ancient_ruins", "visibility": "dim", "traps": "present"},
                "rewards": {"xp": 200, "artifact": "ancient_key"}
            }
        }

        logger.info(f"Loaded {len(self.encounter_templates)} encounter templates")

    async def _load_creature_templates(self):
        """Load creature templates."""
        self.creature_templates = {
            "goblin": {
                "name": "Goblin",
                "creature_type": "humanoid",
                "hp": 7,
                "ac": 15,
                "abilities": ["scimitar", "shortbow"],
                "ai_behavior": "aggressive",
                "challenge_rating": 0.25
            },
            "goblin_boss": {
                "name": "Goblin Boss",
                "creature_type": "humanoid",
                "hp": 15,
                "ac": 16,
                "abilities": ["scimitar", "leadership"],
                "ai_behavior": "tactical",
                "challenge_rating": 1
            },
            "orc": {
                "name": "Orc",
                "creature_type": "humanoid",
                "hp": 15,
                "ac": 13,
                "abilities": ["greataxe", "intimidation"],
                "ai_behavior": "berserker",
                "challenge_rating": 0.5
            },
            "skeleton": {
                "name": "Skeleton",
                "creature_type": "undead",
                "hp": 13,
                "ac": 13,
                "abilities": ["shortsword", "shortbow"],
                "ai_behavior": "mindless",
                "challenge_rating": 0.25
            },
            "wolf": {
                "name": "Wolf",
                "creature_type": "beast",
                "hp": 11,
                "ac": 13,
                "abilities": ["bite", "pack_tactics"],
                "ai_behavior": "pack_hunter",
                "challenge_rating": 0.25
            }
        }

        logger.info(f"Loaded {len(self.creature_templates)} creature templates")

    async def create_encounter(self, encounter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new encounter."""
        try:
            encounter_id = encounter_data.get("id", str(uuid.uuid4()))

            # Create creatures
            creatures = []
            for creature_data in encounter_data.get("creatures", []):
                if "count" in creature_data:
                    # Multiple creatures of same type
                    for i in range(creature_data["count"]):
                        creature = await self._create_creature_from_template(creature_data, i)
                        creatures.append(creature)
                else:
                    # Single creature
                    creature = await self._create_creature_from_template(creature_data)
                    creatures.append(creature)

            # Create objectives
            objectives = []
            for i, obj_data in enumerate(encounter_data.get("objectives", [])):
                objective = EncounterObjective(
                    id=str(uuid.uuid4()),
                    description=obj_data.get("description", ""),
                    objective_type=obj_data.get("objective_type", "defeat"),
                    target=obj_data.get("target"),
                    required_quantity=obj_data.get("required_quantity", 1),
                    current_quantity=0,
                    completed=False,
                    failure_condition=obj_data.get("failure_condition")
                )
                objectives.append(objective)

            # Create encounter
            encounter = Encounter(
                id=encounter_id,
                name=encounter_data.get("name", "Unknown Encounter"),
                description=encounter_data.get("description", ""),
                encounter_type=EncounterType(encounter_data.get("encounter_type", "combat")),
                difficulty=encounter_data.get("difficulty", "medium"),
                status=EncounterStatus.DESIGNING,
                location=encounter_data.get("location", "unknown"),
                creatures=creatures,
                objectives=objectives,
                environment=encounter_data.get("environment", {}),
                rewards=encounter_data.get("rewards", {}),
                time_limit=encounter_data.get("time_limit"),
                metadata=encounter_data.get("metadata", {})
            )

            self.encounters[encounter_id] = encounter

            logger.info(f"Created encounter: {encounter.name}")
            return self._encounter_to_dict(encounter)

        except Exception as e:
            logger.error(f"Failed to create encounter: {str(e)}")
            raise

    async def _create_creature_from_template(self, creature_data: Dict[str, Any], index: int = 0) -> EncounterCreature:
        """Create a creature from template or custom data."""
        template_name = creature_data.get("creature_type", "custom")

        if template_name in self.creature_templates:
            template = self.creature_templates[template_name]
            creature = EncounterCreature(
                id=str(uuid.uuid4()),
                name=f"{template['name']} {index + 1}" if index > 0 else template["name"],
                creature_type=template["creature_type"],
                hp=template["hp"],
                max_hp=template["hp"],
                ac=template["ac"],
                abilities=template.get("abilities", []),
                ai_behavior=template.get("ai_behavior", "default"),
                metadata={"challenge_rating": template.get("challenge_rating", 0.25)}
            )
        else:
            # Custom creature
            creature = EncounterCreature(
                id=str(uuid.uuid4()),
                name=creature_data.get("name", "Unknown Creature"),
                creature_type=creature_data.get("creature_type", "custom"),
                hp=creature_data.get("hp", 10),
                max_hp=creature_data.get("hp", 10),
                ac=creature_data.get("ac", 10),
                abilities=creature_data.get("abilities", []),
                ai_behavior=creature_data.get("ai_behavior", "default"),
                metadata=creature_data.get("metadata", {})
            )

        # Override with custom data
        for key, value in creature_data.items():
            if hasattr(creature, key) and key not in ["id", "creature_type"]:
                setattr(creature, key, value)

        return creature

    async def get_encounters(self) -> List[Dict[str, Any]]:
        """Get all encounters."""
        return [self._encounter_to_dict(encounter) for encounter in self.encounters.values()]

    async def get_encounter(self, encounter_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific encounter."""
        if encounter_id in self.encounters:
            return self._encounter_to_dict(self.encounters[encounter_id])
        return None

    def _encounter_to_dict(self, encounter: Encounter) -> Dict[str, Any]:
        """Convert encounter to dictionary."""
        return {
            "id": encounter.id,
            "name": encounter.name,
            "description": encounter.description,
            "encounter_type": encounter.encounter_type.value,
            "difficulty": encounter.difficulty,
            "status": encounter.status.value,
            "location": encounter.location,
            "creatures": [asdict(creature) for creature in encounter.creatures],
            "objectives": [asdict(obj) for obj in encounter.objectives],
            "environment": encounter.environment,
            "rewards": encounter.rewards,
            "time_limit": encounter.time_limit,
            "turn_order": encounter.turn_order,
            "current_turn": encounter.current_turn,
            "round_number": encounter.round_number,
            "metadata": encounter.metadata
        }

    async def start_encounter(self, encounter_id: str) -> Dict[str, Any]:
        """Start an encounter."""
        try:
            if encounter_id not in self.encounters:
                raise ValueError(f"Encounter {encounter_id} not found")

            encounter = self.encounters[encounter_id]

            if encounter.status != EncounterStatus.DESIGNING and encounter.status != EncounterStatus.READY:
                raise ValueError(f"Cannot start encounter in status: {encounter.status.value}")

            # Initialize encounter
            encounter.status = EncounterStatus.ACTIVE
            encounter.round_number = 1
            encounter.current_turn = 0

            # Roll initiative for all creatures
            await self._roll_initiative(encounter)

            # Set as active encounter
            self.active_encounter = encounter_id

            logger.info(f"Started encounter: {encounter.name}")
            return {
                "status": "success",
                "encounter": self._encounter_to_dict(encounter),
                "message": f"Encounter '{encounter.name}' has started!"
            }

        except Exception as e:
            logger.error(f"Failed to start encounter: {str(e)}")
            raise

    async def _roll_initiative(self, encounter: Encounter):
        """Roll initiative for all creatures in the encounter."""
        for creature in encounter.creatures:
            # Roll d20 + dexterity modifier (simplified)
            initiative_roll = random.randint(1, 20)
            creature.initiative = initiative_roll

        # Sort creatures by initiative
        encounter.creatures.sort(key=lambda c: c.initiative, reverse=True)

        # Set turn order
        encounter.turn_order = [creature.id for creature in encounter.creatures]

    async def end_encounter(self, encounter_id: str) -> Dict[str, Any]:
        """End an encounter."""
        try:
            if encounter_id not in self.encounters:
                raise ValueError(f"Encounter {encounter_id} not found")

            encounter = self.encounters[encounter_id]

            if encounter.status != EncounterStatus.ACTIVE:
                raise ValueError(f"Cannot end encounter in status: {encounter.status.value}")

            encounter.status = EncounterStatus.COMPLETED

            # Clear active encounter if this was it
            if self.active_encounter == encounter_id:
                self.active_encounter = None

            logger.info(f"Ended encounter: {encounter.name}")
            return {
                "status": "success",
                "encounter": self._encounter_to_dict(encounter),
                "message": f"Encounter '{encounter.name}' has ended!"
            }

        except Exception as e:
            logger.error(f"Failed to end encounter: {str(e)}")
            raise

    async def process_action(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an action in the active encounter."""
        try:
            if not self.active_encounter:
                return {"error": "No active encounter"}

            encounter = self.encounters[self.active_encounter]

            action_type = action_data.get("type")
            actor_id = action_data.get("actor_id")
            target_id = action_data.get("target_id")
            action_details = action_data.get("details", {})

            if action_type == "attack":
                result = await self._process_attack(encounter, actor_id, target_id, action_details)
            elif action_type == "move":
                result = await self._process_move(encounter, actor_id, action_details)
            elif action_type == "use_ability":
                result = await self._process_ability(encounter, actor_id, target_id, action_details)
            elif action_type == "end_turn":
                result = await self._process_end_turn(encounter, actor_id)
            else:
                result = {"error": f"Unknown action type: {action_type}"}

            # Check objectives
            await self._check_objectives(encounter)

            return result

        except Exception as e:
            logger.error(f"Failed to process action: {str(e)}")
            return {"error": str(e)}

    async def _process_attack(self, encounter: Encounter, attacker_id: str, target_id: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Process an attack action."""
        attacker = next((c for c in encounter.creatures if c.id == attacker_id), None)
        target = next((c for c in encounter.creatures if c.id == target_id), None)

        if not attacker or not target:
            return {"error": "Invalid attacker or target"}

        # Simple attack roll (d20 + strength modifier vs AC)
        attack_roll = random.randint(1, 20)
        damage = random.randint(1, 8)  # Simple damage dice

        hit = attack_roll >= target.ac

        if hit:
            target.hp -= damage
            if target.hp <= 0:
                target.status = "defeated"

        result = {
            "type": "attack",
            "attacker": attacker.name,
            "target": target.name,
            "attack_roll": attack_roll,
            "target_ac": target.ac,
            "damage": damage,
            "hit": hit,
            "target_hp": target.hp,
            "target_status": target.status
        }

        logger.info(f"Attack processed: {attacker.name} -> {target.name}, Hit: {hit}, Damage: {damage}")
        return result

    async def _process_move(self, encounter: Encounter, actor_id: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Process a move action."""
        actor = next((c for c in encounter.creatures if c.id == actor_id), None)

        if not actor:
            return {"error": "Invalid actor"}

        new_position = details.get("position", {"x": 0, "y": 0})
        actor.position = new_position

        result = {
            "type": "move",
            "actor": actor.name,
            "new_position": new_position
        }

        logger.info(f"Move processed: {actor.name} moved to {new_position}")
        return result

    async def _process_ability(self, encounter: Encounter, actor_id: str, target_id: Optional[str], details: Dict[str, Any]) -> Dict[str, Any]:
        """Process an ability use action."""
        actor = next((c for c in encounter.creatures if c.id == actor_id), None)

        if not actor:
            return {"error": "Invalid actor"}

        ability_name = details.get("ability_name", "unknown")

        result = {
            "type": "ability",
            "actor": actor.name,
            "ability": ability_name,
            "target": target_id,
            "description": f"{actor.name} used {ability_name}"
        }

        logger.info(f"Ability processed: {actor.name} used {ability_name}")
        return result

    async def _process_end_turn(self, encounter: Encounter, actor_id: str) -> Dict[str, Any]:
        """Process end of turn."""
        encounter.current_turn = (encounter.current_turn + 1) % len(encounter.turn_order)

        if encounter.current_turn == 0:
            encounter.round_number += 1

        result = {
            "type": "turn_end",
            "round": encounter.round_number,
            "next_turn": encounter.turn_order[encounter.current_turn] if encounter.turn_order else None
        }

        logger.info(f"Turn ended. Round {encounter.round_number}, Turn {encounter.current_turn}")
        return result

    async def _check_objectives(self, encounter: Encounter):
        """Check if any objectives are completed."""
        for objective in encounter.objectives:
            if objective.completed:
                continue

            if objective.objective_type == "defeat":
                # Check if all creatures are defeated
                defeated_count = sum(1 for c in encounter.creatures if c.status == "defeated")
                if defeated_count >= objective.required_quantity:
                    objective.completed = True

            elif objective.objective_type == "survive":
                # Check if survived for required rounds
                if encounter.round_number >= objective.required_quantity:
                    objective.completed = True

        # Check if encounter is complete
        if all(obj.completed for obj in encounter.objectives):
            encounter.status = EncounterStatus.COMPLETED
            self.active_encounter = None
            logger.info(f"Encounter {encounter.name} completed!")

    async def get_status(self) -> Dict[str, Any]:
        """Get encounter designer status."""
        return {
            "initialized": self.is_initialized,
            "total_encounters": len(self.encounters),
            "active_encounter": self.active_encounter,
            "templates_loaded": len(self.encounter_templates),
            "creature_templates_loaded": len(self.creature_templates)
        }