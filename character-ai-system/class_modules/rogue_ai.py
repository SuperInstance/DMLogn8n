"""
Rogue Class AI Module
Opportunity seeking, stealth optimization, and tactical advantage exploitation
"""

from typing import Dict, Any, List
from game_state import GameState
from .base_class_ai import BaseClassAI, ClassAbility


class RogueAI(BaseClassAI):
    """Rogue-specific AI with stealth and opportunistic combat focus"""

    def _initialize_class_data(self) -> None:
        """Initialize Rogue-specific abilities and preferences"""
        self.combat_preferences = {
            "preferred_range": "melee",
            "stealth_priority": 0.9,
            "opportunity_seeking": 0.9,
            "flanking_focus": 0.8,
            "precision_attacks": 0.8,
            "avoid_direct_confrontation": 0.7
        }

        self.role_preferences = {
            "scout": 0.9,
            "damage_dealer": 0.8,
            "support": 0.6,
            "trap_disarmer": 0.9,
            "infiltrator": 0.9
        }

        self.resource_management = {
            "sneak_attack_efficiency": 0.9,
            "cunning_action_priority": 0.8,
            "stealth_usage": 0.9
        }

        # Rogue abilities
        self.abilities = [
            ClassAbility(
                name="sneak_attack",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Extra damage when attacking with advantage or against flanked enemy",
                tactical_value=0.9
            ),
            ClassAbility(
                name="cunning_action",
                type="active",
                cooldown=0,
                resource_cost={"bonus_action": 1},
                description="Dash, Disengage, or Hide as a bonus action",
                tactical_value=0.8
            ),
            ClassAbility(
                name="uncanny_dodge",
                type="reaction",
                cooldown=0,
                resource_cost={"reaction": 1},
                description="Halve damage from an attack",
                tactical_value=0.7
            ),
            ClassAbility(
                name="thieves_cant",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Secret language with other rogues",
                tactical_value=0.3
            ),
            ClassAbility(
                name="thieves_reflexes",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Add proficiency bonus to initiative",
                tactical_value=0.6
            )
        ]

        # Initialize ability effectiveness
        for ability in self.abilities:
            self.ability_effectiveness[ability.name] = 0.7

    def get_action_recommendations(self, state: GameState) -> List[str]:
        """Get Rogue-specific action recommendations"""
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
        allies_count = len(state.allies)

        # Check for sneak attack opportunities
        if self._can_sneak_attack(state):
            recommendations.append("use_sneak_attack")
            recommendations.append("target_vulnerable_enemy")

        # Stealth and positioning
        if state.environment.get("cover_available", False):
            recommendations.append("use_stealth")
            recommendations.append("tactical_positioning")

        # Cunning action usage
        if health_ratio < 0.5:
            recommendations.append("use_disengage")
        elif self._has_advantage(state):
            recommendations.append("use_dash_to_flank")

        # Avoid direct confrontation when outnumbered
        if enemies_count > allies_count + 1:
            recommendations.append("strategic_retreat")
            recommendations.append("use_stealth")

        # Target priority
        if state.environment.get("enemy_spellcaster", False):
            recommendations.append("target_spellcaster")
        elif state.environment.get("enemy_leader", False):
            recommendations.append("target_leader")

        # Opportunistic attacks
        if state.environment.get("enemies_flatfooted", False):
            recommendations.append("opportunity_attack")

        # Uncanny Dodge for heavy damage situations
        if state.environment.get("incoming_heavy_damage", False):
            recommendations.append("use_uncanny_dodge")

        return recommendations

    def _get_peacetime_recommendations(self, state: GameState) -> List[str]:
        """Get non-combat recommendations"""
        recommendations = []

        # Stealth and scouting
        recommendations.append("maintain_stealth")
        recommendations.append("scout_ahead")

        # Trap and treasure detection
        recommendations.append("search_for_traps")
        recommendations.append("search_for_secrets")

        # Social infiltration
        if state.environment.get("social_situation", False):
            recommendations.append("social_infiltration")
            recommendations.append("gather_information")

        # Equipment preparation
        recommendations.append("prepare_tools")
        recommendations.append("sharpen_weapons")

        return recommendations

    def _can_sneak_attack(self, state: GameState) -> bool:
        """Check if sneak attack conditions are met"""
        # Check if enemy is flanked (has ally nearby)
        enemies_flanked = state.environment.get("enemies_flanked", False)

        # Check if have advantage
        has_advantage = state.environment.get("has_advantage", False)

        # Check if enemy is within 5 feet of ally and not incapacitated
        enemy_near_ally = state.environment.get("enemy_near_ally", False)

        return enemies_flanked or has_advantage or enemy_near_ally

    def _has_advantage(self, state: GameState) -> bool:
        """Check if character has advantage in current situation"""
        return state.environment.get("has_advantage", False)

    def evaluate_situation(self, state: GameState) -> Dict[str, Any]:
        """Evaluate current situation from Rogue perspective"""
        evaluation = {
            "stealth_opportunity": 0.0,
            "sneak_attack_opportunity": 0.0,
            "tactical_advantage": 0.0,
            "risk_assessment": 0.0,
            "opportunity_priority": 0.0
        }

        if state.combat_status:
            health_ratio = state.resources.get("health_ratio", 1.0)
            enemies_count = len(state.enemies)

            # Stealth opportunity
            if state.environment.get("cover_available", False):
                evaluation["stealth_opportunity"] = 0.8
            elif state.environment.get("darkness", False):
                evaluation["stealth_opportunity"] = 0.6

            # Sneak attack opportunity
            if self._can_sneak_attack(state):
                evaluation["sneak_attack_opportunity"] = 0.9
            elif enemies_count == 1:  # Single enemy easier to flank
                evaluation["sneak_attack_opportunity"] = 0.6

            # Tactical advantage
            if self._has_advantage(state):
                evaluation["tactical_advantage"] = 0.9
            elif state.environment.get("enemy_flanked", False):
                evaluation["tactical_advantage"] = 0.7

            # Risk assessment
            if health_ratio < 0.4:
                evaluation["risk_assessment"] = 0.8
            elif enemies_count > 3:
                evaluation["risk_assessment"] = 0.6

            # Opportunity priority
            if state.environment.get("enemy_spellcaster", False):
                evaluation["opportunity_priority"] = 0.9
            elif state.environment.get("enemy_weakened", False):
                evaluation["opportunity_priority"] = 0.8

        else:
            # Non-combat opportunities
            if state.environment.get("traps_present", False):
                evaluation["opportunity_priority"] = 0.9
            if state.environment.get("secrets_hidden", False):
                evaluation["opportunity_priority"] = 0.8
            if state.environment.get("social_gathering", False):
                evaluation["opportunity_priority"] = 0.7

        return evaluation

    def learn_from_outcome(self, action: str, outcome: Dict[str, Any]) -> None:
        """Learn from action outcomes with Rogue-specific insights"""
        super().learn_from_outcome(action, outcome)

        # Learn stealth effectiveness
        if "stealth" in action.lower():
            stealth_success = outcome.get("undetected", False)
            if stealth_success:
                self.combat_preferences["stealth_priority"] = min(1.0,
                    self.combat_preferences["stealth_priority"] + 0.05)

        # Learn opportunity patterns
        if "sneak_attack" in action.lower():
            sneak_success = outcome.get("sneak_successful", False)
            damage_dealt = outcome.get("damage", 0)
            if sneak_success and damage_dealt > 10:
                self.combat_preferences["opportunity_seeking"] = min(1.0,
                    self.combat_preferences["opportunity_seeking"] + 0.03)

        # Learn risk assessment
        if "direct_confrontation" in action.lower():
            direct_success = outcome.get("success", False)
            damage_taken = outcome.get("damage_taken", 0)
            if not direct_success or damage_taken > 15:
                self.combat_preferences["avoid_direct_confrontation"] = min(1.0,
                    self.combat_preferences["avoid_direct_confrontation"] + 0.05)