"""
Sorcerer Class AI Module
Innate magic, metamagic, and bloodline powers
"""

from typing import Dict, Any, List
from game_state import GameState
from .base_class_ai import BaseClassAI, ClassAbility


class SorcererAI(BaseClassAI):
    """Sorcerer-specific AI with innate magic and metamagic focus"""

    def _initialize_class_data(self) -> None:
        """Initialize Sorcerer-specific abilities and preferences"""
        self.combat_preferences = {
            "preferred_range": "ranged",
            "metamagic_efficiency": 0.9,
            "bloodline_powers": 0.8,
            "innate_magic": 0.9,
            "spell_sculpting": 0.7
        }

        self.role_preferences = {
            "spellcaster": 0.9,
            "damage_dealer": 0.8,
            "support": 0.6,
            "battlefield_control": 0.7
        }

        self.resource_management = {
            "sorcery_point_efficiency": 0.8,
            "spell_slot_management": 0.7,
            "metamagic_timing": 0.8
        }

        self.sorcery_points = 3  # Example for level 5 sorcerer
        self.max_sorcery_points = 3

        self.abilities = [
            ClassAbility(
                name="metamagic",
                type="active",
                cooldown=0,
                resource_cost={"sorcery_points": 1},
                description="Modify spells with metamagic",
                tactical_value=0.9
            ),
            ClassAbility(
                name="flexible_casting",
                type="active",
                cooldown=0,
                resource_cost={"sorcery_points": 2},
                description="Create spell slots from sorcery points",
                tactical_value=0.7
            ),
            ClassAbility(
                name="bloodline_magic",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Access to bloodline-specific magic",
                tactical_value=0.8
            )
        ]

        for ability in self.abilities:
            self.ability_effectiveness[ability.name] = 0.7

    def get_action_recommendations(self, state: GameState) -> List[str]:
        """Get Sorcerer-specific action recommendations"""
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
        enemies_count = len(state.enemies)

        # Metamagic usage
        if self.sorcery_points >= 1:
            if state.environment.get("multiple_enemies", False):
                recommendations.append("use_twinned_spell")
            elif state.environment.get("cover_present", False):
                recommendations.append("use_subtle_spell")
            elif health_ratio < 0.5:
                recommendations.append("use_quicken_spell")

        # Bloodline powers
        recommendations.append("use_bloodline_powers")

        # Spell selection
        if enemies_count > 3:
            recommendations.append("cast_area_spell")
        else:
            recommendations.append("cast_single_target_spell")

        # Flexible casting when low on slots
        if self.sorcery_points >= 2:
            recommendations.append("flexible_casting_option")

        return recommendations

    def _get_peacetime_recommendations(self, state: GameState) -> List[str]:
        """Get non-combat recommendations"""
        recommendations = [
            "practice_bloodline_magic",
            "experiment_with_metamagic",
            "meditate_on_innate_power",
            "social_magic_usage"
        ]
        return recommendations

    def evaluate_situation(self, state: GameState) -> Dict[str, Any]:
        """Evaluate current situation from Sorcerer perspective"""
        return {
            "metamagic_opportunity": 0.8,
            "bloodline_advantage": 0.7,
            "innate_magic_value": 0.9
        }

    def use_sorcery_points(self, amount: int) -> bool:
        """Use sorcery points"""
        if self.sorcery_points >= amount:
            self.sorcery_points -= amount
            return True
        return False

    def learn_from_outcome(self, action: str, outcome: Dict[str, Any]) -> None:
        """Learn from action outcomes"""
        super().learn_from_outcome(action, outcome)