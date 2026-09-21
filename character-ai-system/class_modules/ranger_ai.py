"""
Ranger Class AI Module
Wilderness expertise, tracking, and ranged combat
"""

from typing import Dict, Any, List
from game_state import GameState
from .base_class_ai import BaseClassAI, ClassAbility


class RangerAI(BaseClassAI):
    """Ranger-specific AI with wilderness and ranged combat focus"""

    def _initialize_class_data(self) -> None:
        """Initialize Ranger-specific abilities and preferences"""
        self.combat_preferences = {
            "preferred_range": "ranged",
            "tracking": 0.9,
            "wilderness_knowledge": 0.8,
            "favored_enemy_focus": 0.8,
            "exploration": 0.7
        }

        self.role_preferences = {
            "scout": 0.9,
            "ranged_damage": 0.8,
            "tracker": 0.9,
            "wilderness_guide": 0.8,
            "support": 0.6
        }

        self.resource_management = {
            "spell_efficiency": 0.7,
            "favored_enemy_priority": 0.8,
            "exploration_efficiency": 0.7
        }

        self.abilities = [
            ClassAbility(
                name="favored_enemy",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Advantage on tracking against favored enemies",
                tactical_value=0.7
            ),
            ClassAbility(
                name="natural_explorer",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Expertise in favored terrain",
                tactical_value=0.6
            ),
            ClassAbility(
                name="ranger_spells",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Access to nature-based spells",
                tactical_value=0.6
            )
        ]

        for ability in self.abilities:
            self.ability_effectiveness[ability.name] = 0.7

    def get_action_recommendations(self, state: GameState) -> List[str]:
        """Get Ranger-specific action recommendations"""
        recommendations = []

        if state.combat_status:
            recommendations.extend(self._get_combat_recommendations(state))
        else:
            recommendations.extend(self._get_peacetime_recommendations(state))

        return recommendations

    def _get_combat_recommendations(self, state: GameState) -> List[str]:
        """Get combat-specific recommendations"""
        recommendations = []

        # Ranged combat
        recommendations.append("maintain_ranged_position")
        recommendations.append("target_prioritized_enemies")

        # Favored enemy focus
        if state.environment.get("favored_enemy_present", False):
            recommendations.append("focus_favored_enemy")

        # Wilderness advantages
        if state.environment.get("natural_terrain", False):
            recommendations.append("use_terrain_advantage")

        # Spells
        recommendations.append("use_ranger_spells")
        if state.environment.get("allies_injured", False):
            recommendations.append("cast_healing_spell")

        return recommendations

    def _get_peacetime_recommendations(self, state: GameState) -> List[str]:
        """Get non-combat recommendations"""
        recommendations = [
            "track_creatures",
            "scout_wilderness",
            "identify_plants_animals",
            "navigate_terrain"
        ]
        return recommendations

    def evaluate_situation(self, state: GameState) -> Dict[str, Any]:
        """Evaluate current situation from Ranger perspective"""
        return {
            "tracking_opportunity": 0.8,
            "ranged_advantage": 0.7,
            "wilderness_benefit": 0.6
        }

    def learn_from_outcome(self, action: str, outcome: Dict[str, Any]) -> None:
        """Learn from action outcomes"""
        super().learn_from_outcome(action, outcome)