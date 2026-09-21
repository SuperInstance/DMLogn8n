"""
Fighter Class AI Module
Tactical positioning, protection instincts, and martial combat expertise
"""

from typing import Dict, Any, List
from game_state import GameState
from .base_class_ai import BaseClassAI, ClassAbility


class FighterAI(BaseClassAI):
    """Fighter-specific AI with tactical combat focus"""

    def _initialize_class_data(self) -> None:
        """Initialize Fighter-specific abilities and preferences"""
        self.combat_preferences = {
            "preferred_range": "melee",
            "tactical_positioning": 0.8,
            "protection_instinct": 0.7,
            "combat_style": "balanced",
            "weapon_preference": "martial_weapons"
        }

        self.role_preferences = {
            "front_line": 0.9,
            "tank": 0.7,
            "damage_dealer": 0.8,
            "party_protector": 0.8
        }

        self.resource_management = {
            "stamina_efficiency": 0.7,
            "action_surge_priority": 0.9,
            "second_wind_threshold": 0.5
        }

        # Fighter abilities
        self.abilities = [
            ClassAbility(
                name="second_wind",
                type="active",
                cooldown=1,  # Once per short rest
                resource_cost={"bonus_action": 1},
                description="Regain hit points as a bonus action",
                tactical_value=0.8
            ),
            ClassAbility(
                name="action_surge",
                type="active",
                cooldown=1,  # Once per short rest
                resource_cost={"action_points": 1},
                description="Take an additional action on your turn",
                tactical_value=0.9
            ),
            ClassAbility(
                name="battle_master_manuver",
                type="active",
                cooldown=0,
                resource_cost={"superiority_die": 1},
                description="Use tactical maneuver to gain advantage",
                tactical_value=0.7
            ),
            ClassAbility(
                name="defensive_stance",
                type="active",
                cooldown=0,
                resource_cost={"action": 1},
                description="Take defensive stance for protection",
                tactical_value=0.6
            )
        ]

        # Initialize ability effectiveness
        for ability in self.abilities:
            self.ability_effectiveness[ability.name] = 0.6

    def get_action_recommendations(self, state: GameState) -> List[str]:
        """Get Fighter-specific action recommendations"""
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

        # Low health - use defensive abilities
        if health_ratio < 0.4 and self.can_use_ability("second_wind"):
            recommendations.append("use_second_wind")

        # Outnumbered - tactical positioning
        if enemies_count > allies_count:
            recommendations.append("defensive_positioning")
            recommendations.append("protect_ally")

        # Action Surge usage for critical moments
        if self.can_use_ability("action_surge"):
            if health_ratio < 0.3 or enemies_count > 3:
                recommendations.append("use_action_surge")

        # Protection instincts
        if allies_count > 0:
            weak_ally = self._find_weak_ally(state)
            if weak_ally:
                recommendations.append(f"protect_{weak_ally}")

        # Offensive recommendations
        if health_ratio > 0.6:
            recommendations.append("aggressive_attack")
            recommendations.append("tactical_positioning")

        # Battle Master maneuvers
        if self.can_use_ability("battle_master_manuver"):
            if state.environment.get("enemy_spellcaster", False):
                recommendations.append("use_disarming_attack")
            elif state.environment.get("enemy_leader", False):
                recommendations.append("use_menacing_attack")
            else:
                recommendations.append("use_precise_attack")

        return recommendations

    def _get_peacetime_recommendations(self, state: GameState) -> List[str]:
        """Get non-combat recommendations"""
        recommendations = []

        # Equipment maintenance
        recommendations.append("maintain_equipment")

        # Training and practice
        recommendations.append("practice_combat")

        # Tactical scouting
        if state.environment.get("dangerous_area", False):
            recommendations.append("strategic_scouting")

        # Party protection role
        if state.allies:
            recommendations.append("party_protection_plan")

        return recommendations

    def _find_weak_ally(self, state: GameState) -> str:
        """Find the most vulnerable ally"""
        weakest_ally = None
        lowest_health = 1.0

        party_health = state.resources.get("party_health", {})
        for ally, health in party_health.items():
            if health < lowest_health:
                lowest_health = health
                weakest_ally = ally

        return weakest_ally

    def evaluate_situation(self, state: GameState) -> Dict[str, Any]:
        """Evaluate current situation from Fighter perspective"""
        evaluation = {
            "combat_readiness": 0.8,
            "tactical_positioning_need": 0.0,
            "protection_priority": 0.0,
            "offensive_opportunity": 0.0,
            "defensive_need": 0.0
        }

        if state.combat_status:
            health_ratio = state.resources.get("health_ratio", 1.0)
            enemies_count = len(state.enemies)
            allies_count = len(state.allies)

            # Defensive need assessment
            if health_ratio < 0.5:
                evaluation["defensive_need"] = 0.8
            elif health_ratio < 0.7:
                evaluation["defensive_need"] = 0.5

            # Protection priority
            if allies_count > 0:
                evaluation["protection_priority"] = 0.7
                party_health = state.resources.get("party_health", {})
                avg_party_health = sum(party_health.values()) / len(party_health) if party_health else 1.0
                if avg_party_health < 0.6:
                    evaluation["protection_priority"] = 0.9

            # Offensive opportunity
            if health_ratio > 0.7:
                evaluation["offensive_opportunity"] = 0.8
            elif health_ratio > 0.5:
                evaluation["offensive_opportunity"] = 0.5

            # Tactical positioning need
            if enemies_count > 2 or state.environment.get("difficult_terrain", False):
                evaluation["tactical_positioning_need"] = 0.8

        return evaluation

    def learn_from_outcome(self, action: str, outcome: Dict[str, Any]) -> None:
        """Learn from action outcomes with Fighter-specific insights"""
        super().learn_from_outcome(action, outcome)

        # Learn combat patterns
        if outcome.get("combat", False):
            self._learn_combat_pattern(action, outcome)

        # Learn protection effectiveness
        if "protect" in action:
            protection_success = outcome.get("ally_protected", False)
            if protection_success:
                self.combat_preferences["protection_instinct"] = min(1.0,
                    self.combat_preferences["protection_instinct"] + 0.05)

    def _learn_combat_pattern(self, action: str, outcome: Dict[str, Any]) -> None:
        """Learn from combat-specific patterns"""
        effectiveness = outcome.get("effectiveness", 0.5)
        enemy_type = outcome.get("enemy_type", "unknown")

        # Store combat effectiveness by enemy type
        pattern_key = f"{action}_vs_{enemy_type}"
        if pattern_key not in self.ability_effectiveness:
            self.ability_effectiveness[pattern_key] = effectiveness
        else:
            # Update with weighted average
            current = self.ability_effectiveness[pattern_key]
            new_value = (current * 0.7 + effectiveness * 0.3)
            self.ability_effectiveness[pattern_key] = new_value