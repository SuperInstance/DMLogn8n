"""
Character Manager - Manages character state, actions, and AI behavior.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import random

from ..database.models import Character
from ..database.database import get_db

logger = logging.getLogger(__name__)

@dataclass
class CharacterStats:
    """Character statistics."""
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

@dataclass
class CharacterCombat:
    """Character combat information."""
    armor_class: int = 10
    initiative: int = 0
    speed: int = 30
    current_hp: int = 10
    max_hp: int = 10
    current_mp: int = 0
    max_mp: int = 0
    temporary_hp: int = 0

@dataclass
class CharacterInfo:
    """Character information."""
    id: str
    name: str
    description: str
    level: int = 1
    class_name: str = ""
    race: str = ""
    background: str = ""
    alignment: str = "Neutral"
    experience_points: int = 0

class CharacterManager:
    """Manages character state and behavior."""

    def __init__(self, character_id: str):
        self.character_id = character_id
        self.character_info: Optional[CharacterInfo] = None
        self.character_stats: Optional[CharacterStats] = None
        self.character_combat: Optional[CharacterCombat] = None
        self.inventory: List[Dict] = []
        self.spells: List[Dict] = []
        self.abilities: List[Dict] = []
        self.human_override_enabled = False
        self.human_override_reason = ""
        self.last_activity = datetime.now()
        self.current_location = "Unknown"
        self.status_effects: List[Dict] = []
        self.ai_personality: Dict = {}
        self.action_history: List[Dict] = []

    async def initialize(self):
        """Initialize the character manager."""
        logger.info(f"Initializing character manager for {self.character_id}")

        # Load character from database
        await self._load_character()

        if not self.character_info:
            # Create default character if not found
            await self._create_default_character()

        # Initialize AI personality
        await self._initialize_ai_personality()

        logger.info(f"Character manager initialized for {self.character_info.name}")

    async def _load_character(self):
        """Load character data from database."""
        try:
            db = next(get_db())
            character = db.query(Character).filter(Character.id == self.character_id).first()

            if character:
                self.character_info = CharacterInfo(
                    id=character.id,
                    name=character.name,
                    description=character.description or "",
                    level=character.level,
                    class_name=character.class_name or "",
                    race=character.race or "",
                    background=character.attributes.get("background", ""),
                    alignment=character.attributes.get("alignment", "Neutral"),
                    experience_points=character.attributes.get("experience_points", 0)
                )

                # Load stats
                attributes = character.attributes or {}
                self.character_stats = CharacterStats(
                    strength=attributes.get("strength", 10),
                    dexterity=attributes.get("dexterity", 10),
                    constitution=attributes.get("constitution", 10),
                    intelligence=attributes.get("intelligence", 10),
                    wisdom=attributes.get("wisdom", 10),
                    charisma=attributes.get("charisma", 10)
                )

                # Load combat info
                self.character_combat = CharacterCombat(
                    armor_class=attributes.get("armor_class", 10),
                    initiative=attributes.get("initiative", 0),
                    speed=attributes.get("speed", 30),
                    current_hp=character.current_hp or attributes.get("max_hp", 10),
                    max_hp=character.max_hp or attributes.get("max_hp", 10),
                    current_mp=character.current_mp or 0,
                    max_mp=character.max_mp or 0,
                    temporary_hp=attributes.get("temporary_hp", 0)
                )

                # Load other data
                self.inventory = character.inventory or []
                self.spells = character.spells or []
                self.abilities = character.abilities or []
                self.current_location = character.attributes.get("location", "Unknown")
                self.status_effects = character.attributes.get("status_effects", [])

        except Exception as e:
            logger.error(f"Failed to load character {self.character_id}: {str(e)}")

    async def _create_default_character(self):
        """Create a default character."""
        self.character_info = CharacterInfo(
            id=self.character_id,
            name=f"Character {self.character_id[:8]}",
            description="A mysterious character awaiting definition",
            level=1,
            class_name="Adventurer",
            race="Human"
        )

        self.character_stats = CharacterStats()
        self.character_combat = CharacterCombat()

    async def _initialize_ai_personality(self):
        """Initialize AI personality based on character info."""
        if not self.character_info:
            return

        # Generate personality traits based on race, class, and background
        personality_traits = []

        # Race-based traits
        race_traits = {
            "Human": ["adaptable", "ambitious", "versatile"],
            "Elf": ["graceful", "perceptive", "patient"],
            "Dwarf": ["resilient", "stubborn", "loyal"],
            "Halfling": ["cheerful", "curious", "brave"],
            "Dragonborn": ["proud", "honorable", "fierce"],
            "Gnome": ["inventive", "curious", "playful"]
        }

        if self.character_info.race in race_traits:
            personality_traits.extend(race_traits[self.character_info.race])

        # Class-based traits
        class_traits = {
            "Fighter": ["brave", "disciplined", "protective"],
            "Wizard": ["studious", "curious", "methodical"],
            "Rogue": ["cunning", "observant", "independent"],
            "Cleric": ["devout", "compassionate", "wise"],
            "Ranger": ["patient", "resourceful", "independent"],
            "Bard": ["charismatic", "creative", "adaptable"]
        }

        if self.character_info.class_name in class_traits:
            personality_traits.extend(class_traits[self.character_info.class_name])

        self.ai_personality = {
            "traits": personality_traits,
            "speech_style": self._generate_speech_style(),
            "decision_making": "balanced",  # can be: aggressive, defensive, diplomatic, chaotic
            "risk_tolerance": "moderate",
            "social_approach": "neutral",
            "preferred_actions": self._generate_preferred_actions()
        }

    def _generate_speech_style(self) -> str:
        """Generate speech style based on character attributes."""
        if self.character_info.class_name == "Wizard":
            return "formal and articulate"
        elif self.character_info.class_name == "Rogue":
            return "cunning and concise"
        elif self.character_info.class_name == "Bard":
            return "eloquent and dramatic"
        else:
            return "casual and direct"

    def _generate_preferred_actions(self) -> List[str]:
        """Generate preferred actions based on character class and stats."""
        actions = []

        if self.character_stats.strength >= 14:
            actions.extend(["attack", "intimidate", "protect"])
        if self.character_stats.dexterity >= 14:
            actions.extend(["sneak", "dodge", "aimed_shot"])
        if self.character_stats.intelligence >= 14:
            actions.extend(["analyze", "cast_spell", "investigate"])
        if self.character_stats.wisdom >= 14:
            actions.extend(["heal", "perceive", "advise"])
        if self.character_stats.charisma >= 14:
            actions.extend(["persuade", "negotiate", "inspire"])

        if not actions:
            actions = ["observe", "wait", "follow"]

        return actions

    async def get_character_info(self) -> Dict[str, Any]:
        """Get complete character information."""
        return {
            "info": asdict(self.character_info) if self.character_info else {},
            "stats": asdict(self.character_stats) if self.character_stats else {},
            "combat": asdict(self.character_combat) if self.character_combat else {},
            "inventory": self.inventory,
            "spells": self.spells,
            "abilities": self.abilities,
            "current_location": self.current_location,
            "status_effects": self.status_effects,
            "human_override_enabled": self.human_override_enabled,
            "last_activity": self.last_activity.isoformat(),
            "ai_personality": self.ai_personality
        }

    async def get_character_state(self) -> Dict[str, Any]:
        """Get current character state."""
        if not self.character_combat:
            return {}

        return {
            "hp": self.character_combat.current_hp,
            "max_hp": self.character_combat.max_hp,
            "mp": self.character_combat.current_mp,
            "max_mp": self.character_combat.max_mp,
            "ac": self.character_combat.armor_class,
            "status": "healthy" if self.character_combat.current_hp > 0 else "unconscious",
            "location": self.current_location,
            "effects": self.status_effects
        }

    async def perform_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a character action."""
        self.last_activity = datetime.now()

        action_type = action.get("type", "unknown")
        action_data = action.get("data", {})

        logger.info(f"Character {self.character_id} performing action: {action_type}")

        # Add to action history
        action_record = {
            "type": action_type,
            "data": action_data,
            "timestamp": datetime.now().isoformat(),
            "human_initiated": self.human_override_enabled
        }
        self.action_history.append(action_record)

        # Keep history limited
        if len(self.action_history) > 100:
            self.action_history = self.action_history[-50:]

        result = await self._execute_action(action_type, action_data)

        # Update database if needed
        await self._save_if_needed()

        return result

    async def _execute_action(self, action_type: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific action."""
        if action_type == "move":
            return await self._action_move(action_data)
        elif action_type == "attack":
            return await self._action_attack(action_data)
        elif action_type == "cast_spell":
            return await self._action_cast_spell(action_data)
        elif action_type == "use_item":
            return await self._action_use_item(action_data)
        elif action_type == "talk":
            return await self._action_talk(action_data)
        elif action_type == "rest":
            return await self._action_rest(action_data)
        else:
            return {"status": "error", "message": f"Unknown action type: {action_type}"}

    async def _action_move(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle movement action."""
        destination = data.get("destination", "Unknown")
        self.current_location = destination

        return {
            "status": "success",
            "message": f"{self.character_info.name} moves to {destination}",
            "new_location": destination
        }

    async def _action_attack(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle attack action."""
        target = data.get("target", "Unknown target")
        weapon = data.get("weapon", "unarmed")

        # Simple attack roll (d20 + strength modifier)
        strength_mod = (self.character_stats.strength - 10) // 2 if self.character_stats else 0
        attack_roll = random.randint(1, 20) + strength_mod

        return {
            "status": "success",
            "message": f"{self.character_info.name} attacks {target} with {weapon}",
            "attack_roll": attack_roll,
            "damage": random.randint(1, 6) + strength_mod
        }

    async def _action_cast_spell(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle spell casting action."""
        spell = data.get("spell", "Unknown spell")
        target = data.get("target", "Unknown target")

        if not self.character_combat or self.character_combat.current_mp < 1:
            return {"status": "error", "message": "Not enough MP to cast spell"}

        self.character_combat.current_mp -= 1

        return {
            "status": "success",
            "message": f"{self.character_info.name} casts {spell} at {target}",
            "spell": spell,
            "mp_remaining": self.character_combat.current_mp
        }

    async def _action_use_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle item usage action."""
        item = data.get("item", "Unknown item")

        return {
            "status": "success",
            "message": f"{self.character_info.name} uses {item}",
            "item": item
        }

    async def _action_talk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle talking action."""
        message = data.get("message", "")
        target = data.get("target", "everyone")

        return {
            "status": "success",
            "message": f"{self.character_info.name} says: {message}",
            "target": target,
            "speech": message
        }

    async def _action_rest(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resting action."""
        if self.character_combat:
            # Restore some HP and MP
            hp_restored = min(random.randint(1, 6), self.character_combat.max_hp - self.character_combat.current_hp)
            self.character_combat.current_hp += hp_restored

            if self.character_combat.max_mp > 0:
                mp_restored = min(random.randint(1, 4), self.character_combat.max_mp - self.character_combat.current_mp)
                self.character_combat.current_mp += mp_restored
            else:
                mp_restored = 0

            return {
                "status": "success",
                "message": f"{self.character_info.name} rests and recovers",
                "hp_restored": hp_restored,
                "mp_restored": mp_restored
            }

        return {"status": "success", "message": f"{self.character_info.name} rests"}

    async def update_state(self, state_update: Dict[str, Any]) -> Dict[str, Any]:
        """Update character state."""
        self.last_activity = datetime.now()

        if "hp" in state_update and self.character_combat:
            self.character_combat.current_hp = min(state_update["hp"], self.character_combat.max_hp)

        if "mp" in state_update and self.character_combat:
            self.character_combat.current_mp = min(state_update["mp"], self.character_combat.max_mp)

        if "location" in state_update:
            self.current_location = state_update["location"]

        if "status_effects" in state_update:
            self.status_effects = state_update["status_effects"]

        await self._save_if_needed()

        return {"status": "success", "message": "Character state updated"}

    async def send_chat_message(self, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a chat message."""
        message = chat_data.get("message", "")
        channel = chat_data.get("channel", "general")

        self.last_activity = datetime.now()

        return {
            "character_id": self.character_id,
            "character_name": self.character_info.name if self.character_info else "Unknown",
            "message": message,
            "channel": channel,
            "timestamp": datetime.now().isoformat()
        }

    async def enable_human_override(self, override_data: Dict[str, Any]):
        """Enable human override."""
        self.human_override_enabled = True
        self.human_override_reason = override_data.get("reason", "Manual control")
        logger.info(f"Human override enabled for {self.character_id}: {self.human_override_reason}")

    async def disable_human_override(self):
        """Disable human override."""
        self.human_override_enabled = False
        self.human_override_reason = ""
        logger.info(f"Human override disabled for {self.character_id}")

    async def is_human_override_enabled(self) -> bool:
        """Check if human override is enabled."""
        return self.human_override_enabled

    def get_last_activity(self) -> str:
        """Get last activity timestamp."""
        return self.last_activity.isoformat()

    async def _save_if_needed(self):
        """Save character to database if changes need to be persisted."""
        try:
            db = next(get_db())
            character = db.query(Character).filter(Character.id == self.character_id).first()

            if character:
                # Update combat stats
                if self.character_combat:
                    character.current_hp = self.character_combat.current_hp
                    character.max_hp = self.character_combat.max_hp
                    character.current_mp = self.character_combat.current_mp
                    character.max_mp = self.character_combat.max_mp

                # Update attributes
                attributes = character.attributes or {}
                attributes.update({
                    "location": self.current_location,
                    "status_effects": self.status_effects,
                    "last_activity": self.last_activity.isoformat()
                })

                character.attributes = attributes
                db.commit()

        except Exception as e:
            logger.error(f"Failed to save character {self.character_id}: {str(e)}")

    async def ai_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make an AI decision based on current context."""
        if self.human_override_enabled:
            return {"decision": "wait", "reason": "Human override active"}

        # Simple AI logic based on personality and context
        if "combat" in context and context["combat"]:
            return await self._ai_combat_decision(context)
        elif "social" in context and context["social"]:
            return await self._ai_social_decision(context)
        else:
            return await self._ai_exploration_decision(context)

    async def _ai_combat_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make AI combat decision."""
        if not self.character_combat or self.character_combat.current_hp < self.character_combat.max_hp * 0.3:
            return {"decision": "defend", "reason": "Low health"}

        # Choose action based on preferred actions and abilities
        if self.character_stats and self.character_stats.strength >= 14:
            return {"decision": "attack", "reason": "Strong character prefers offense"}
        elif self.spells and self.character_combat and self.character_combat.current_mp > 0:
            return {"decision": "cast_spell", "reason": "Has spells available"}
        else:
            return {"decision": "attack", "reason": "Default combat action"}

    async def _ai_social_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make AI social decision."""
        if self.character_stats and self.character_stats.charisma >= 14:
            return {"decision": "persuade", "reason": "Charismatic character prefers diplomacy"}
        else:
            return {"decision": "observe", "reason": "Observing situation"}

    async def _ai_exploration_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make AI exploration decision."""
        if self.character_stats and self.character_stats.wisdom >= 14:
            return {"decision": "investigate", "reason": "Wise character prefers caution"}
        else:
            return {"decision": "explore", "reason": "Default exploration action"}