"""
Barbarian Class AI Module
Rage-fueled combat, primal instincts, and physical dominance
"""

from typing import Dict, Any, List
from game_state import GameState
from .base_class_ai import BaseClassAI, ClassAbility


class BarbarianAI(BaseClassAI):
    """Barbarian-specific AI with rage and primal combat focus"""

    def _initialize_class_data(self) -> None:
        """Initialize Barbarian-specific abilities and preferences"""
        self.combat_preferences = {
            "preferred_range": "melee",
            "rage_priority": 0.9,
            "aggressive_style": 0.8,
            "physical_dominance": 0.8,
            "primal_instincts": 0.7,
            "intimidation": 0.6
        }

        self.role_preferences = {
            "front_line": 1.0,
            "damage_dealer": 0.9,
            "tank": 0.7,
            "intimidator": 0.8,
            "party_protector": 0.6
        }

        self.resource_management = {
            "rage_efficiency": 0.8,
            "reckless_attack_timing": 0.7,
            "strength_priority": 0.9
        }

        # Barbarian abilities
        self.abilities = [
            ClassAbility(
                name="rage",
                type="active",
                cooldown=1,  # Limited uses per day
                resource_cost={"rage_points": 1},
                description="Enter rage state for enhanced combat",
                tactical_value=0.9
            ),
            ClassAbility(
                name="reckless_attack",
                type="active",
                cooldown=0,
                resource_cost={"accuracy": -0.5},
                description="Attack with advantage but give advantage to enemies",
                tactical_value=0.7
            ),
            ClassAbility(
                name="danger_sense",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Advantage on Dexterity saves when not incapacitated",
                tactical_value=0.6
            ),
            ClassAbility(
                name="fast_movement",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Increased movement speed when not wearing heavy armor",
                tactical_value=0.5
            )
        ]

        self.rage_active = False
        self.rage_turns_remaining = 0

        # Initialize ability effectiveness
        for ability in self.abilities:
            self.ability_effectiveness[ability.name] = 0.7

    def get_action_recommendations(self, state: GameState) -> List[str]:
        """Get Barbarian-specific action recommendations"""
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

        # Rage activation
        if not self.rage_active and health_ratio > 0.3:
            if enemies_count > 0:
                recommendations.append("activate_rage")

        # Maintain rage
        if self.rage_active and self.rage_turns_remaining <= 2:
            recommendations.append("maintain_rage_position")

        # Aggressive attacks when raging
        if self.rage_active:
            recommendations.append("reckless_attack")
            recommendations.append("aggressive_advancement")

        # Target selection
        if state.environment.get("enemy_leader", False):
            recommendations.append("target_leader")
        elif state.environment.get("enemy_tank", False):
            recommendations.append("target_tank")

        # Intimidation
        if state.environment.get("social_combat", False):
            recommendations.append("intimidate_enemies")

        # Physical dominance
        if state.environment.get("grapple_opportunity", False):
            recommendations.append("use_grapple")
        if state.environment.get("shove_opportunity", False):
            recommendations.append("use_shove")

        # Defensive considerations
        if health_ratio < 0.4 and not self.rage_active:
            recommendations.append("defensive_positioning")
        elif health_ratio < 0.2:
            recommendations.append("strategic_retreat")

        return recommendations

    def _get_peacetime_recommendations(self, state: GameState) -> List[str]:
        """Get non-combat recommendations"""
        recommendations = []

        # Physical activities
        recommendations.append("physical_training")
        recommendations.append("maintain_equipment")

        # Social intimidation
        if state.environment.get("negotiation", False):
            recommendations.append("intimidation_tactic")

        # Exploration
        recommendations.append("scout_ahead")
        recommendations.append("break_obstacles")

        # Rest and recovery
        recommendations.append("rest_and_meditate")

        return recommendations

    def evaluate_situation(self, state: GameState) -> Dict[str, Any]:
        """Evaluate current situation from Barbarian perspective"""
        evaluation = {
            "rage_desirability": 0.0,
            "aggressive_opportunity": 0.0,
            "physical_challenge": 0.0,
            "intimidation_potential": 0.0,
            "survival_instinct": 0.0
        }

        if state.combat_status:
            health_ratio = state.resources.get("health_ratio", 1.0)
            enemies_count = len(state.enemies)

            # Rage desirability
            if not self.rage_active and health_ratio > 0.4:
                if enemies_count > 2:
                    evaluation["rage_desirability"] = 0.9
                elif enemies_count > 0:
                    evaluation["rage_desirability"] = 0.7

            # Aggressive opportunity
            if self.rage_active:
                evaluation["aggressive_opportunity"] = 0.9
            elif health_ratio > 0.6:
                evaluation["aggressive_opportunity"] = 0.6

            # Physical challenge
            if state.environment.get("large_enemy", False):
                evaluation["physical_challenge"] = 0.8
            elif state.environment.get("multiple_enemies", False):
                evaluation["physical_challenge"] = 0.6

            # Intimidation potential
            if state.environment.get("weaker_enemies", False):
                evaluation["intimidation_potential"] = 0.8

            # Survival instinct
            if health_ratio < 0.3:
                evaluation["survival_instinct"] = 0.9
            elif health_ratio < 0.5:
                evaluation["survival_instinct"] = 0.5

        return evaluation

    def activate_rage(self) -> bool:
        """Activate rage state"""
        if self.can_use_ability("rage") and not self.rage_active:
            self.rage_active = True
            self.rage_turns_remaining = 10  # Standard rage duration
            self.use_ability("rage")
            return True
        return False

    def update_rage_status(self) -> None:
        """Update rage status each turn"""
        if self.rage_active:
            self.rage_turns_remaining -= 1
            if self.rage_turns_remaining <= 0:
                self.rage_active = False

    def learn_from_outcome(self, action: str, outcome: Dict[str, Any]) -> None:
        """Learn from action outcomes with Barbarian-specific insights"""
        super().learn_from_outcome(action, outcome)

        # Learn rage effectiveness
        if "rage" in action.lower():
            rage_effectiveness = outcome.get("damage_dealt", 0) / 20  # Normalize
            damage_taken = outcome.get("damage_taken", 0)

            if rage_effectiveness > 0.7:
                self.combat_preferences["rage_priority"] = min(1.0,
                    self.combat_preferences["rage_priority"] + 0.03)

            if damage_taken < 10:  # Took minimal damage while raging
                self.combat_preferences["aggressive_style"] = min(1.0,
                    self.combat_preferences["aggressive_style"] + 0.02)

        # Learn intimidation effectiveness
        if "intimidate" in action.lower():
            intimidation_success = outcome.get("intimidation_successful", False)
            if intimidation_success:
                self.combat_preferences["intimidation"] = min(1.0,
                    self.combat_preferences["intimidation"] + 0.05)

    def get_status(self) -> Dict[str, Any]:
        """Get current status including rage state"""
        base_status = super().get_status()
        base_status.update({
            "rage_active": self.rage_active,
            "rage_turns_remaining": self.rage_turns_remaining
        })
        return base_status