"""
Paladin Class AI Module
Divine combat, healing, and righteous smiting
"""

from typing import Dict, Any, List
from game_state import GameState
from .base_class_ai import BaseClassAI, ClassAbility


class PaladinAI(BaseClassAI):
    """Paladin-specific AI with divine combat and healing focus"""

    def _initialize_class_data(self) -> None:
        """Initialize Paladin-specific abilities and preferences"""
        self.combat_preferences = {
            "preferred_range": "melee",
            "divine_smite": 0.9,
            "healing_priority": 0.7,
            "righteous_combat": 0.8,
            "protection": 0.8
        }

        self.role_preferences = {
            "front_line": 0.9,
            "damage_dealer": 0.8,
            "healer": 0.6,
            "party_protector": 0.9,
            "moral_leader": 0.8
        }

        self.resource_management = {
            "spell_slot_efficiency": 0.7,
            "smite_timing": 0.8,
            "lay_on_hands_priority": 0.9
        }

        self.lay_on_hands_pool = 25  # Example for level 5 paladin

        self.abilities = [
            ClassAbility(
                name="divine_smite",
                type="active",
                cooldown=0,
                resource_cost={"spell_slot": 1},
                description="Add radiant damage to melee attack",
                tactical_value=0.9
            ),
            ClassAbility(
                name="lay_on_hands",
                type="active",
                cooldown=0,
                resource_cost={"lay_on_hands_pool": 5},
                description="Heal with divine touch",
                tactical_value=0.8
            ),
            ClassAbility(
                name="divine_health",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Immunity to disease",
                tactical_value=0.3
            ),
            ClassAbility(
                name="aura_of_protection",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Allies gain saving throw bonus",
                tactical_value=0.7
            )
        ]

        for ability in self.abilities:
            self.ability_effectiveness[ability.name] = 0.7

    def get_action_recommendations(self, state: GameState) -> List[str]:
        """Get Paladin-specific action recommendations"""
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

        # Divine Smite on critical targets
        if state.environment.get("enemy_leader", False):
            recommendations.append("use_divine_smite")
        elif state.environment.get("undead_present", False):
            recommendations.append("use_divine_smite")

        # Lay on Hands
        critical_ally = self._find_critical_ally(state)
        if critical_ally and self.lay_on_hands_pool >= 5:
            recommendations.append(f"lay_on_hands_{critical_ally}")
        elif health_ratio < 0.3 and self.lay_on_hands_pool >= 5:
            recommendations.append("lay_on_hands_self")

        # Divine combat
        recommendations.append("righteous_attack")
        recommendations.append("protect_party_members")

        # Healing spells
        if state.environment.get("party_injured", False):
            recommendations.append("cast_healing_spells")

        return recommendations

    def _get_peacetime_recommendations(self, state: GameState) -> List[str]:
        """Get non-combat recommendations"""
        recommendations = [
            "maintain_holy_equipment",
            "pray_meditation",
            "provide_healing_to_needy",
            "moral_counseling"
        ]
        return recommendations

    def _find_critical_ally(self, state: GameState) -> str:
        """Find critically injured ally"""
        party_health = state.resources.get("party_health", {})
        for ally, health in party_health.items():
            if health < 0.3:
                return ally
        return None

    def evaluate_situation(self, state: GameState) -> Dict[str, Any]:
        """Evaluate current situation from Paladin perspective"""
        return {
            "smite_opportunity": 0.8,
            "healing_need": 0.7,
            "protection_priority": 0.9
        }

    def learn_from_outcome(self, action: str, outcome: Dict[str, Any]) -> None:
        """Learn from action outcomes"""
        super().learn_from_outcome(action, outcome)