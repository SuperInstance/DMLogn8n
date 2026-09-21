"""
Druid Class AI Module
Nature magic, wild shaping, and environmental adaptation
"""

from typing import Dict, Any, List
from game_state import GameState
from .base_class_ai import BaseClassAI, ClassAbility


class DruidAI(BaseClassAI):
    """Druid-specific AI with nature and shapeshifting focus"""

    def _initialize_class_data(self) -> None:
        """Initialize Druid-specific abilities and preferences"""
        self.combat_preferences = {
            "preferred_range": "versatile",
            "wild_shape_priority": 0.8,
            "nature_magic": 0.9,
            "environmental_adaptation": 0.8,
            "summoning": 0.7
        }

        self.role_preferences = {
            "spellcaster": 0.8,
            "support": 0.7,
            "damage_dealer": 0.6,
            "scout": 0.7,
            "summoner": 0.8
        }

        self.resource_management = {
            "spell_efficiency": 0.7,
            "wild_shape_timing": 0.8,
            "summoning_priority": 0.6
        }

        self.abilities = [
            ClassAbility(
                name="wild_shape",
                type="active",
                cooldown=1,  # Limited uses
                resource_cost={"wild_shape_charge": 1},
                description="Transform into animal form",
                tactical_value=0.8
            ),
            ClassAbility(
                name="druidic_spells",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Access to nature-based spells",
                tactical_value=0.8
            ),
            ClassAbility(
                name="spell_preparation",
                type="active",
                cooldown=1,
                resource_cost={},
                description="Prepare nature spells",
                tactical_value=0.6
            )
        ]

        for ability in self.abilities:
            self.ability_effectiveness[ability.name] = 0.7

    def get_action_recommendations(self, state: GameState) -> List[str]:
        """Get Druid-specific action recommendations"""
        recommendations = []

        if state.combat_status:
            recommendations.extend(self._get_combat_recommendations(state))
        else:
            recommendations.extend(self._get_peacetime_recommendations(state))

        return recommendations

    def _get_combat_recommendations(self, state: GameState) -> List[str]:
        """Get combat-specific recommendations"""
        recommendations = []
        health_ratio = state.resources.get("health_ratio", 1.0)

        # Wild Shape usage
        if self.can_use_ability("wild_shape"):
            if health_ratio < 0.6:
                recommendations.append("wild_shape_defensive")
            elif health_ratio > 0.7:
                recommendations.append("wild_shape_offensive")

        # Nature spells
        recommendations.append("cast_nature_spells")
        if state.environment.get("enemies_grouped", False):
            recommendations.append("cast_area_nature_spell")
        if state.environment.get("allies_injured", False):
            recommendations.append("cast_healing_nature_spell")

        # Summoning
        if len(state.allies) < 3 and self.can_use_ability("summon_animals"):
            recommendations.append("summon_natural_allies")

        return recommendations

    def _get_peacetime_recommendations(self, state: GameState) -> List[str]:
        """Get non-combat recommendations"""
        recommendations = [
            "communicate_with_nature",
            "gather_herbs",
            "wild_shape_exploration",
            "prepare_nature_spells"
        ]
        return recommendations

    def evaluate_situation(self, state: GameState) -> Dict[str, Any]:
        """Evaluate current situation from Druid perspective"""
        return {
            "wild_shape_opportunity": 0.7,
            "nature_magic_value": 0.8,
            "environmental_advantage": 0.6
        }

    def learn_from_outcome(self, action: str, outcome: Dict[str, Any]) -> None:
        """Learn from action outcomes"""
        super().learn_from_outcome(action, outcome)