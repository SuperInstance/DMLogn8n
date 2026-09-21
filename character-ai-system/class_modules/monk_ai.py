"""
Monk Class AI Module
Martial arts mastery, ki manipulation, and disciplined combat
"""

from typing import Dict, Any, List
from game_state import GameState
from .base_class_ai import BaseClassAI, ClassAbility


class MonkAI(BaseClassAI):
    """Monk-specific AI with martial arts and ki focus"""

    def _initialize_class_data(self) -> None:
        """Initialize Monk-specific abilities and preferences"""
        self.combat_preferences = {
            "preferred_range": "melee",
            "ki_efficiency": 0.9,
            "unarmed_combat": 0.8,
            "mobility": 0.8,
            "discipline": 0.9
        }

        self.role_preferences = {
            "damage_dealer": 0.8,
            "mobile_fighter": 0.9,
            "support": 0.5,
            "scout": 0.6
        }

        self.resource_management = {
            "ki_point_conservation": 0.8,
            "stunning_strike_timing": 0.7,
            "mobility_priority": 0.8
        }

        self.ki_points = 5  # Example for level 5 monk
        self.max_ki_points = 5

        self.abilities = [
            ClassAbility(
                name="stunning_strike",
                type="active",
                cooldown=0,
                resource_cost={"ki_points": 1},
                description="Stun target with martial strike",
                tactical_value=0.9
            ),
            ClassAbility(
                name="patient_defense",
                type="active",
                cooldown=0,
                resource_cost={"ki_points": 1},
                description="Dodge as bonus action",
                tactical_value=0.7
            ),
            ClassAbility(
                name="step_of_the_wind",
                type="active",
                cooldown=0,
                resource_cost={"ki_points": 1},
                description="Disengage and Dash as bonus action",
                tactical_value=0.6
            ),
            ClassAbility(
                name="flurry_of_blows",
                type="active",
                cooldown=0,
                resource_cost={"ki_points": 1},
                description="Two unarmed strikes as bonus action",
                tactical_value=0.8
            )
        ]

        for ability in self.abilities:
            self.ability_effectiveness[ability.name] = 0.7

    def get_action_recommendations(self, state: GameState) -> List[str]:
        """Get Monk-specific action recommendations"""
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

        # Stunning Strike on priority targets
        if self.ki_points >= 1:
            if state.environment.get("enemy_spellcaster", False):
                recommendations.append("use_stunning_strike")
            elif state.environment.get("enemy_leader", False):
                recommendations.append("use_stunning_strike")

        # Flurry of Blows
        if self.ki_points >= 2 and health_ratio > 0.5:
            recommendations.append("use_flurry_of_blows")

        # Defensive ki usage
        if health_ratio < 0.4 and self.ki_points >= 1:
            recommendations.append("use_patient_defense")

        # Mobility
        if enemies_count > 2:
            recommendations.append("use_step_of_the_wind")
            recommendations.append("mobile_positioning")

        # Unarmed combat
        recommendations.append("unarmed_strike_combo")
        recommendations.append("deflect_missiles")

        return recommendations

    def _get_peacetime_recommendations(self, state: GameState) -> List[str]:
        """Get non-combat recommendations"""
        recommendations = [
            "meditate",
            "practice_martial_arts",
            "maintain_discipline",
            "scout_with_mobility"
        ]
        return recommendations

    def evaluate_situation(self, state: GameState) -> Dict[str, Any]:
        """Evaluate current situation from Monk perspective"""
        return {
            "ki_efficiency_need": 0.8,
            "mobility_advantage": 0.7,
            "stun_opportunity": 0.6
        }

    def use_ki_points(self, amount: int) -> bool:
        """Use ki points"""
        if self.ki_points >= amount:
            self.ki_points -= amount
            return True
        return False

    def restore_ki_points(self, amount: int) -> None:
        """Restore ki points"""
        self.ki_points = min(self.max_ki_points, self.ki_points + amount)

    def learn_from_outcome(self, action: str, outcome: Dict[str, Any]) -> None:
        """Learn from action outcomes"""
        super().learn_from_outcome(action, outcome)

        # Learn ki efficiency
        if "ki" in action.lower():
            ki_efficiency = outcome.get("damage_per_ki", 0)
            if ki_efficiency > 15:
                self.resource_management["ki_point_conservation"] = min(1.0,
                    self.resource_management["ki_point_conservation"] + 0.03)