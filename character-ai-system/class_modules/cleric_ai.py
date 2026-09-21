"""
Cleric Class AI Module
Healing prioritization, divine guidance, and support focus
"""

from typing import Dict, Any, List
from game_state import GameState
from .base_class_ai import BaseClassAI, ClassAbility


class ClericAI(BaseClassAI):
    """Cleric-specific AI with healing and support focus"""

    def _initialize_class_data(self) -> None:
        """Initialize Cleric-specific abilities and preferences"""
        self.combat_preferences = {
            "preferred_range": "melee_ranged",
            "healing_priority": 0.9,
            "divine_guidance": 0.8,
            "support_focus": 0.8,
            "undead_destruction": 0.7,
            "party_protection": 0.9
        }

        self.role_preferences = {
            "healer": 1.0,
            "support": 0.9,
            "tank": 0.6,
            "damage_dealer": 0.5,
            "party_leader": 0.7
        }

        self.resource_management = {
            "spell_slot_conservation": 0.7,
            "channel_divinity_timing": 0.8,
            "healing_efficiency": 0.9,
            "divine_intervention_priority": 1.0
        }

        # Cleric abilities
        self.abilities = [
            ClassAbility(
                name="channel_divinity",
                type="active",
                cooldown=1,  # Once per short rest
                resource_cost={},
                description="Use divine channeling for special effects",
                tactical_value=0.8
            ),
            ClassAbility(
                name="divine_intervention",
                type="active",
                cooldown=99,  # Very rare
                resource_cost={},
                description="Request direct divine aid",
                tactical_value=1.0
            ),
            ClassAbility(
                name="destroy_undead",
                type="active",
                cooldown=0,
                resource_cost={"channel_divinity": 1},
                description="Destroy undead creatures",
                tactical_value=0.9
            ),
            ClassAbility(
                name="preserve_life",
                type="active",
                cooldown=0,
                resource_cost={"channel_divinity": 1},
                description="Heal multiple allies",
                tactical_value=0.9
            )
        ]

        # Spell effectiveness tracking
        self.spell_effectiveness: Dict[str, float] = {}
        self.healing_priorities: Dict[str, float] = {}
        self.divine_favor = 0.5  # 0-1 scale of divine connection strength

        # Initialize ability effectiveness
        for ability in self.abilities:
            self.ability_effectiveness[ability.name] = 0.7

    def get_action_recommendations(self, state: GameState) -> List[str]:
        """Get Cleric-specific action recommendations"""
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

        # Healing priorities
        critical_ally = self._find_most_critical_ally(state)
        if critical_ally:
            recommendations.append(f"heal_{critical_ally}")
            recommendations.append("use_healing_spell")

        # Self-healing when critical
        if health_ratio < 0.3:
            recommendations.append("self_heal")
            recommendations.append("use_healing_word")

        # Support spells for allies
        if allies_count > 0:
            recommendations.append("buff_allies")
            recommendations.append("cast_bless")
            recommendations.append("cast_aid")

        # Offensive divine magic
        if health_ratio > 0.7 and allies_count > 0:
            recommendations.append("cast_offensive_spells")
            recommendations.append("use_spiritual_weapon")

        # Turn undead
        if state.environment.get("undead_present", False):
            recommendations.append("turn_undead")
            recommendations.append("use_divine_smite")

        # Channel Divinity usage
        if self.can_use_ability("channel_divinity"):
            if state.environment.get("multiple_injured_allies", False):
                recommendations.append("use_preserve_life")
            elif state.environment.get("undead_present", False):
                recommendations.append("use_destroy_undead")

        # Protective measures
        if state.environment.get("incoming_heavy_damage", False):
            recommendations.append("cast_shield_of_faith")
            recommendations.append("use_warding_bond")

        # Divine Intervention (emergency only)
        if health_ratio < 0.1 and self.can_use_ability("divine_intervention"):
            recommendations.append("request_divine_intervention")

        # Turn the tide
        if enemies_count > allies_count and health_ratio > 0.5:
            recommendations.append("cast_flame_strike")
            recommendations.append("use_divine_storm")

        return recommendations

    def _get_peacetime_recommendations(self, state: GameState) -> List[str]:
        """Get non-combat recommendations"""
        recommendations = []

        # Healing and recovery
        recommendations.append("heal_party")
        recommendations.append("prepare_healing_spells")

        # Divine guidance
        recommendations.append("seek_divine_guidance")
        recommendations.append("pray_meditation")

        # Support activities
        recommendations.append("bless_party")
        recommendations.append("perform_ritual")

        # Community service
        if state.environment.get("community_in_need", False):
            recommendations.append("provide_healing")
            recommendations.append("offer_divine_counsel")

        # Undead detection
        recommendations.append("detect_undead")
        recommendations.append("consecrate_area")

        # Preparation
        recommendations.append("prepare_spells")
        recommendations.append("maintain_holy_symbols")

        return recommendations

    def _find_most_critical_ally(self, state: GameState) -> str:
        """Find the ally most in need of healing"""
        most_critical = None
        lowest_health = 1.0

        party_health = state.resources.get("party_health", {})
        for ally, health in party_health.items():
            if health < lowest_health:
                lowest_health = health
                most_critical = ally

        return most_critical if lowest_health < 0.5 else None

    def evaluate_situation(self, state: GameState) -> Dict[str, Any]:
        """Evaluate current situation from Cleric perspective"""
        evaluation = {
            "healing_priority": 0.0,
            "support_need": 0.0,
            "divine_opportunity": 0.0,
            "protection_priority": 0.0,
            "offensive_opportunity": 0.0
        }

        if state.combat_status:
            health_ratio = state.resources.get("health_ratio", 1.0)
            enemies_count = len(state.enemies)
            allies_count = len(state.allies)

            # Healing priority assessment
            party_health = state.resources.get("party_health", {})
            if party_health:
                avg_party_health = sum(party_health.values()) / len(party_health)
                min_party_health = min(party_health.values())

                if min_party_health < 0.2:
                    evaluation["healing_priority"] = 1.0
                elif avg_party_health < 0.5:
                    evaluation["healing_priority"] = 0.8
                elif avg_party_health < 0.7:
                    evaluation["healing_priority"] = 0.5

            # Support need
            if allies_count > 2:
                evaluation["support_need"] = 0.8
            elif state.environment.get("party_debuffed", False):
                evaluation["support_need"] = 0.9

            # Divine opportunity
            if state.environment.get("undead_present", False):
                evaluation["divine_opportunity"] = 0.9
            elif state.environment.get("holy_ground", False):
                evaluation["divine_opportunity"] = 0.7

            # Protection priority
            if state.environment.get("party_in_danger", False):
                evaluation["protection_priority"] = 0.9
            elif enemies_count > allies_count:
                evaluation["protection_priority"] = 0.6

            # Offensive opportunity
            if health_ratio > 0.7 and state.environment.get("enemies_grouped", False):
                evaluation["offensive_opportunity"] = 0.7
            elif state.environment.get("unholy_enemies", False):
                evaluation["offensive_opportunity"] = 0.9

        else:
            # Non-combat healing needs
            party_health = state.resources.get("party_health", {})
            if party_health and any(health < 1.0 for health in party_health.values()):
                evaluation["healing_priority"] = 0.6

            # Community support opportunities
            if state.environment.get("sick_or_injured", False):
                evaluation["healing_priority"] = 0.9

        return evaluation

    def learn_from_outcome(self, action: str, outcome: Dict[str, Any]) -> None:
        """Learn from action outcomes with Cleric-specific insights"""
        super().learn_from_outcome(action, outcome)

        # Learn healing effectiveness
        if "heal" in action.lower():
            healing_effectiveness = outcome.get("health_restored", 0)
            target_critical = outcome.get("target_was_critical", False)

            if healing_effectiveness > 15 or target_critical:
                self.combat_preferences["healing_priority"] = min(1.0,
                    self.combat_preferences["healing_priority"] + 0.03)

        # Learn divine guidance effectiveness
        if "divine" in action.lower():
            divine_success = outcome.get("divine_favor_granted", False)
            if divine_success:
                self.divine_favor = min(1.0, self.divine_favor + 0.05)
                self.combat_preferences["divine_guidance"] = min(1.0,
                    self.combat_preferences["divine_guidance"] + 0.04)

        # Learn spell effectiveness
        if "cast_" in action.lower():
            spell_name = action.replace("cast_", "")
            effectiveness = outcome.get("effectiveness", 0.5)

            if spell_name in self.spell_effectiveness:
                current = self.spell_effectiveness[spell_name]
                new_value = (current * 0.8 + effectiveness * 0.2)
                self.spell_effectiveness[spell_name] = new_value
            else:
                self.spell_effectiveness[spell_name] = effectiveness

        # Learn from party outcomes
        if outcome.get("ally_saved", False):
            self.role_preferences["healer"] = min(1.0,
                self.role_preferences["healer"] + 0.02)
            self.combat_preferences["party_protection"] = min(1.0,
                self.combat_preferences["party_protection"] + 0.02)

    def update_healing_priorities(self, party_health: Dict[str, float]) -> None:
        """Update healing priorities based on party health status"""
        self.healing_priorities = party_health.copy()

    def get_divine_favor_level(self) -> float:
        """Get current level of divine favor"""
        return self.divine_favor

    def request_divine_guidance(self, situation: Dict[str, Any]) -> str:
        """Request divine guidance for a specific situation"""
        # Simple implementation based on divine favor level
        if self.divine_favor > 0.8:
            return "strong_divine_guidance_received"
        elif self.divine_favor > 0.5:
            return "moderate_divine_guidance_received"
        else:
            return "weak_divine_guidance_received"