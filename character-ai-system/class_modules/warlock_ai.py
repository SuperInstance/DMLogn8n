"""
Warlock Class AI Module
Pact magic, patron powers, and eldritch influence
"""

from typing import Dict, Any, List
from game_state import GameState
from .base_class_ai import BaseClassAI, ClassAbility


class WarlockAI(BaseClassAI):
    """Warlock-specific AI with pact magic and patron focus"""

    def _initialize_class_data(self) -> None:
        """Initialize Warlock-specific abilities and preferences"""
        self.combat_preferences = {
            "preferred_range": "ranged",
            "pact_magic": 0.9,
            "patron_powers": 0.8,
            "eldritch_blast": 0.9,
            "pact_utility": 0.7
        }

        self.role_preferences = {
            "spellcaster": 0.8,
            "damage_dealer": 0.9,
            "support": 0.5,
            "debuffer": 0.7
        }

        self.resource_management = {
            "spell_slot_regeneration": 0.9,
            "pact_usage_efficiency": 0.8,
            "invocation_priority": 0.7
        }

        self.pact_magic_slots = 2  # Warlocks have limited slots that recharge on short rest

        self.abilities = [
            ClassAbility(
                name="eldritch_blast",
                type="cantrip",
                cooldown=0,
                resource_cost={},
                description="Powerful eldritch beam attack",
                tactical_value=0.9
            ),
            ClassAbility(
                name="pact_magic",
                type="active",
                cooldown=1,  # Short rest recharge
                resource_cost={"pact_slot": 1},
                description="Cast spells using pact magic",
                tactical_value=0.8
            ),
            ClassAbility(
                name="patron_feature",
                type="active",
                cooldown=0,
                resource_cost={},
                description="Use patron-granted abilities",
                tactical_value=0.8
            )
        ]

        for ability in self.abilities:
            self.ability_effectiveness[ability.name] = 0.7

    def get_action_recommendations(self, state: GameState) -> List[str]:
        """Get Warlock-specific action recommendations"""
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

        # Eldritch Blast as primary damage
        recommendations.append("use_eldritch_blast")

        # Pact magic for crucial moments
        if self.pact_magic_slots > 0:
            if state.environment.get("critical_moment", False):
                recommendations.append("use_pact_magic")
            elif health_ratio < 0.4:
                recommendations.append("cast_pact_healing")

        # Patron powers
        recommendations.append("activate_patron_powers")

        # Utility invocations
        if state.environment.get("scouting_needed", False):
            recommendations.append("use_pact_utility")
        if state.environment.get("social_situation", False):
            recommendations.append("use_social_invocation")

        return recommendations

    def _get_peacetime_recommendations(self, state: GameState) -> List[str]:
        """Get non-combat recommendations"""
        recommendations = [
            "commune_with_patron",
            "practice_pact_magic",
            "use_pact_utilities",
            "gather_favor_with_patron"
        ]
        return recommendations

    def evaluate_situation(self, state: GameState) -> Dict[str, Any]:
        """Evaluate current situation from Warlock perspective"""
        return {
            "pact_magic_timing": 0.8,
            "patron_influence": 0.7,
            "eldritch_power": 0.9
        }

    def use_pact_slot(self) -> bool:
        """Use a pact magic slot"""
        if self.pact_magic_slots > 0:
            self.pact_magic_slots -= 1
            return True
        return False

    def regain_pact_slots(self) -> None:
        """Regain pact slots on short rest"""
        self.pact_magic_slots = 2

    def learn_from_outcome(self, action: str, outcome: Dict[str, Any]) -> None:
        """Learn from action outcomes"""
        super().learn_from_outcome(action, outcome)