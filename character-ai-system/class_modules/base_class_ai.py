"""
Base class AI module
Defines common interface and functionality for all class-specific AI
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass

from character_profile import CharacterProfile
from game_state import GameState


@dataclass
class ClassAbility:
    """Represents a class-specific ability"""
    name: str
    type: str  # 'passive', 'active', 'spell', 'feature'
    cooldown: int  # rounds
    resource_cost: Dict[str, float]
    description: str
    tactical_value: float  # 0-1 scale


class BaseClassAI(ABC):
    """Base class for all class-specific AI modules"""

    def __init__(self, character_profile: CharacterProfile):
        self.profile = character_profile
        self.class_name = character_profile.character_class
        self.level = character_profile.level

        # Class abilities
        self.abilities: List[ClassAbility] = []
        self.ability_cooldowns: Dict[str, int] = {}

        # Class-specific preferences
        self.combat_preferences = {}
        self.role_preferences = {}
        self.resource_management = {}

        # Learning data
        self.ability_effectiveness: Dict[str, float] = {}
        self.situation_patterns: List[Dict[str, Any]] = []

        # Initialize class-specific data
        self._initialize_class_data()

    @abstractmethod
    def _initialize_class_data(self) -> None:
        """Initialize class-specific abilities and preferences"""
        pass

    @abstractmethod
    def get_action_recommendations(self, state: GameState) -> List[str]:
        """Get class-specific action recommendations"""
        pass

    @abstractmethod
    def evaluate_situation(self, state: GameState) -> Dict[str, Any]:
        """Evaluate current situation from class perspective"""
        pass

    def update_cooldowns(self) -> None:
        """Update ability cooldowns"""
        for ability_name in self.ability_cooldowns:
            if self.ability_cooldowns[ability_name] > 0:
                self.ability_cooldowns[ability_name] -= 1

    def can_use_ability(self, ability_name: str) -> bool:
        """Check if ability can be used"""
        if ability_name not in self.ability_cooldowns:
            return True
        return self.ability_cooldowns[ability_name] == 0

    def use_ability(self, ability_name: str) -> bool:
        """Use an ability and set cooldown"""
        if not self.can_use_ability(ability_name):
            return False

        # Find ability and set cooldown
        for ability in self.abilities:
            if ability.name == ability_name:
                self.ability_cooldowns[ability_name] = ability.cooldown
                return True

        return False

    def learn_from_outcome(self, action: str, outcome: Dict[str, Any]) -> None:
        """Learn from action outcomes"""
        success = outcome.get("success", False)
        effectiveness = outcome.get("effectiveness", 0.5)

        # Update ability effectiveness
        if action in self.ability_effectiveness:
            # Weighted average
            current = self.ability_effectiveness[action]
            new_value = (current * 0.8 + effectiveness * 0.2)
            self.ability_effectiveness[action] = new_value
        else:
            self.ability_effectiveness[action] = effectiveness

        # Store situation pattern for learning
        pattern = {
            "action": action,
            "outcome": success,
            "effectiveness": effectiveness,
            "situation": outcome.get("situation", {})
        }
        self.situation_patterns.append(pattern)

        # Keep only recent patterns
        if len(self.situation_patterns) > 50:
            self.situation_patterns = self.situation_patterns[-50:]

    def update_goals(self, goals: List[str]) -> None:
        """Update current goals"""
        # Can be overridden by subclasses for goal-specific behavior
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get current status of class AI"""
        return {
            "class_name": self.class_name,
            "level": self.level,
            "abilities_count": len(self.abilities),
            "available_abilities": [name for name in self.ability_cooldowns if self.ability_cooldowns[name] == 0],
            "learned_patterns": len(self.situation_patterns),
            "effectiveness_ratings": self.ability_effectiveness
        }