"""
Bard Class AI Module
Musical inspiration, social manipulation, and versatile support
"""

from typing import Dict, Any, List
from game_state import GameState
from .base_class_ai import BaseClassAI, ClassAbility


class BardAI(BaseClassAI):
    """Bard-specific AI with social and musical focus"""

    def _initialize_class_data(self) -> None:
        """Initialize Bard-specific abilities and preferences"""
        self.combat_preferences = {
            "preferred_range": "support",
            "inspiration_priority": 0.9,
            "social_manipulation": 0.8,
            "versatility": 0.9,
            "performance_flair": 0.7
        }

        self.role_preferences = {
            "support": 0.9,
            "face": 1.0,
            "spellcaster": 0.7,
            "damage_dealer": 0.5,
            "party_morale": 0.9
        }

        self.resource_management = {
            "inspiration_efficiency": 0.8,
            "spell_slot_management": 0.7,
            "performance_timing": 0.8
        }

        # Bard abilities
        self.abilities = [
            ClassAbility(
                name="bardic_inspiration",
                type="active",
                cooldown=0,
                resource_cost={"inspiration_die": 1},
                description="Inspire ally with bonus die",
                tactical_value=0.8
            ),
            ClassAbility(
                name="jack_of_all_trades",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Add half proficiency bonus to all ability checks",
                tactical_value=0.6
            ),
            ClassAbility(
                name="song_of_rest",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Extra healing during short rests",
                tactical_value=0.5
            ),
            ClassAbility(
                name="expertise",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Double proficiency bonus in selected skills",
                tactical_value=0.7
            )
        ]

        # Initialize ability effectiveness
        for ability in self.abilities:
            self.ability_effectiveness[ability.name] = 0.7

    def get_action_recommendations(self, state: GameState) -> List[str]:
        """Get Bard-specific action recommendations"""
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
        allies_count = len(state.allies)

        # Bardic Inspiration usage
        if self.can_use_ability("bardic_inspiration"):
            struggling_ally = self._find_struggling_ally(state)
            if struggling_ally:
                recommendations.append(f"inspire_{struggling_ally}")
            elif state.environment.get("critical_moment", False):
                recommendations.append("use_bardic_inspiration")

        # Support spells
        if allies_count > 0:
            recommendations.append("buff_allies")
            recommendations.append("cast_heroism")
            recommendations.append("use_fascinating_performance")

        # Debuff enemies
        recommendations.append("debuff_enemies")
        recommendations.append("cast_dissonant_whispers")
        recommendations.append("use_vicious_mockery")

        # Defensive positioning
        if health_ratio < 0.5:
            recommendations.append("defensive_positioning")
            recommendations.append("use_stealth_if_needed")

        # Crowd control
        if state.environment.get("multiple_enemies", False):
            recommendations.append("cast_hypnotic_pattern")
            recommendations.append("use_performance_magic")

        # Musical inspiration
        if health_ratio > 0.6:
            recommendations.append("inspiring_performance")
            recommendations.append("maintain_morale")

        return recommendations

    def _get_peacetime_recommendations(self, state: GameState) -> List[str]:
        """Get non-combat recommendations"""
        recommendations = []

        # Social situations
        if state.environment.get("social_situation", False):
            recommendations.append("lead_negotiations")
            recommendations.append("use_diplomacy")
            recommendations.append("performance_for_influence")

        # Information gathering
        recommendations.append("gather_information")
        recommendations.append("use_social_skills")

        # Entertainment and morale
        recommendations.append("raise_morale")
        recommendations.append("performance")

        # Support activities
        recommendations.append("assist_party_members")
        recommendations.append("provide_advice")

        return recommendations

    def _find_struggling_ally(self, state: GameState) -> str:
        """Find ally who needs inspiration"""
        party_health = state.resources.get("party_health", {})
        for ally, health in party_health.items():
            if health < 0.6:
                return ally
        return None

    def evaluate_situation(self, state: GameState) -> Dict[str, Any]:
        """Evaluate current situation from Bard perspective"""
        evaluation = {
            "social_opportunity": 0.0,
            "inspiration_need": 0.0,
            "performance_value": 0.0,
            "support_priority": 0.0,
            "versatility_need": 0.0
        }

        if state.combat_status:
            health_ratio = state.resources.get("health_ratio", 1.0)
            allies_count = len(state.allies)

            # Inspiration need
            if allies_count > 0:
                party_health = state.resources.get("party_health", {})
                if party_health:
                    avg_health = sum(party_health.values()) / len(party_health)
                    if avg_health < 0.6:
                        evaluation["inspiration_need"] = 0.8

            # Support priority
            if allies_count > 2:
                evaluation["support_priority"] = 0.9
            elif state.environment.get("party_needs_buff", False):
                evaluation["support_priority"] = 0.8

            # Performance value
            if state.environment.get("morale_low", False):
                evaluation["performance_value"] = 0.9

        else:
            # Social opportunities
            if state.environment.get("social_situation", False):
                evaluation["social_opportunity"] = 0.9
            if state.environment.get("negotiation_needed", False):
                evaluation["social_opportunity"] = 0.9

            # Versatility need
            if state.environment.get("complex_problem", False):
                evaluation["versatility_need"] = 0.8

        return evaluation

    def learn_from_outcome(self, action: str, outcome: Dict[str, Any]) -> None:
        """Learn from action outcomes with Bard-specific insights"""
        super().learn_from_outcome(action, outcome)

        # Learn inspiration effectiveness
        if "inspire" in action.lower():
            inspiration_success = outcome.get("ally_succeeded", False)
            if inspiration_success:
                self.combat_preferences["inspiration_priority"] = min(1.0,
                    self.combat_preferences["inspiration_priority"] + 0.04)

        # Learn social effectiveness
        if any(word in action.lower() for word in ["negotiate", "diplomacy", "persuade"]):
            social_success = outcome.get("social_success", False)
            if social_success:
                self.combat_preferences["social_manipulation"] = min(1.0,
                    self.combat_preferences["social_manipulation"] + 0.03)

        # Learn performance effectiveness
        if "performance" in action.lower():
            audience_response = outcome.get("audience_response", 0)
            if audience_response > 0.7:
                self.combat_preferences["performance_flair"] = min(1.0,
                    self.combat_preferences["performance_flair"] + 0.05)