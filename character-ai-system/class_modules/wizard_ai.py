"""
Wizard Class AI Module
Spell management, tactical casting, and magical problem-solving
"""

from typing import Dict, Any, List
from game_state import GameState
from .base_class_ai import BaseClassAI, ClassAbility


class WizardAI(BaseClassAI):
    """Wizard-specific AI with spell management and tactical casting focus"""

    def _initialize_class_data(self) -> None:
        """Initialize Wizard-specific abilities and preferences"""
        self.combat_preferences = {
            "preferred_range": "ranged",
            "spell_efficiency": 0.9,
            "magical_preparation": 0.8,
            "crowd_control": 0.7,
            "buff_usage": 0.6,
            "avoid_melee": 0.9
        }

        self.role_preferences = {
            "spellcaster": 1.0,
            "crowd_control": 0.8,
            "support": 0.7,
            "area_damage": 0.9,
            "debunker": 0.7
        }

        self.resource_management = {
            "spell_slot_efficiency": 0.9,
            "cantrip_priority": 0.7,
            "high_slot_conservation": 0.8,
            "arcane_recovery_timing": 0.6
        }

        # Wizard abilities
        self.abilities = [
            ClassAbility(
                name="arcane_recovery",
                type="active",
                cooldown=1,  # Once per day
                resource_cost={},
                description="Recover spell slots during short rest",
                tactical_value=0.7
            ),
            ClassAbility(
                name="spell_mastery",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Cast certain spells without using spell slots",
                tactical_value=0.8
            ),
            ClassAbility(
                name="signature_spell",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Cast favorite spells without spell slots",
                tactical_value=0.9
            ),
            ClassAbility(
                name="ritual_casting",
                type="passive",
                cooldown=0,
                resource_cost={},
                description="Cast certain spells as rituals without using spell slots",
                tactical_value=0.6
            )
        ]

        # Spell effectiveness tracking
        self.spell_effectiveness: Dict[str, float] = {}
        self.spell_slots: Dict[int, int] = {
            1: 4, 2: 3, 3: 2, 4: 1  # Example for level 5 wizard
        }

        # Initialize ability effectiveness
        for ability in self.abilities:
            self.ability_effectiveness[ability.name] = 0.7

    def get_action_recommendations(self, state: GameState) -> List[str]:
        """Get Wizard-specific action recommendations"""
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

        # Spell conservation strategy
        if enemies_count <= 2:
            recommendations.append("use_cantrips")
        elif enemies_count <= 4:
            recommendations.append("use_low_level_spells")
        else:
            recommendations.append("use_area_spells")

        # Defensive casting
        if health_ratio < 0.5:
            recommendations.append("cast_defensive_spells")
            recommendations.append("maintain_distance")

        # Crowd control when outnumbered
        if enemies_count > allies_count:
            recommendations.append("cast_crowd_control")
            recommendations.append("use_debuff_spells")

        # High priority targets
        if state.environment.get("enemy_spellcaster", False):
            recommendations.append("counterspell_enemy")
            recommendations.append("cast_dispel_magic")

        # Buff allies when they're in trouble
        if allies_count > 0:
            party_health = state.resources.get("party_health", {})
            weak_allies = [ally for ally, health in party_health.items() if health < 0.6]
            if weak_allies:
                recommendations.append("buff_allies")

        # Area damage opportunities
        if state.environment.get("enemies_grouped", False):
            recommendations.append("cast_area_damage")

        # Utility spells
        if state.environment.get("difficult_terrain", False):
            recommendations.append("cast_utility_spells")

        # Emergency measures
        if health_ratio < 0.2:
            recommendations.append("use_escape_spells")
            recommendations.append("cast_misty_step")

        return recommendations

    def _get_peacetime_recommendations(self, state: GameState) -> List[str]:
        """Get non-combat recommendations"""
        recommendations = []

        # Magical preparation
        recommendations.append("prepare_spells")
        recommendations.append("study_spellbook")

        # Utility casting
        recommendations.append("cast_utility_spells")
        recommendations.append("use_ritual_casting")

        # Knowledge gathering
        recommendations.append("magical_research")
        recommendations.append("identify_items")

        # Strategic planning
        if state.environment.get("quest_objective", False):
            recommendations.append("plan_magical_approach")

        # Social situations
        if state.environment.get("social_situation", False):
            recommendations.append("use_enhancement_spells")
            recommendations.append("detect_magic_auras")

        return recommendations

    def evaluate_situation(self, state: GameState) -> Dict[str, Any]:
        """Evaluate current situation from Wizard perspective"""
        evaluation = {
            "spell_optimization": 0.0,
            "area_effect_opportunity": 0.0,
            "crowd_control_need": 0.0,
            "defensive_casting_need": 0.0,
            "utility_spell_value": 0.0
        }

        if state.combat_status:
            health_ratio = state.resources.get("health_ratio", 1.0)
            enemies_count = len(state.enemies)
            allies_count = len(state.allies)

            # Spell optimization (efficient use of resources)
            total_spell_slots = sum(self.spell_slots.values())
            if total_spell_slots < 3:
                evaluation["spell_optimization"] = 0.9
            elif total_spell_slots < 6:
                evaluation["spell_optimization"] = 0.6
            else:
                evaluation["spell_optimization"] = 0.3

            # Area effect opportunities
            if state.environment.get("enemies_grouped", False):
                evaluation["area_effect_opportunity"] = 0.9
            elif enemies_count > 3:
                evaluation["area_effect_opportunity"] = 0.7

            # Crowd control need
            if enemies_count > allies_count + 1:
                evaluation["crowd_control_need"] = 0.8
            elif state.environment.get("enemy_brute", False):
                evaluation["crowd_control_need"] = 0.6

            # Defensive casting need
            if health_ratio < 0.4:
                evaluation["defensive_casting_need"] = 0.9
            elif health_ratio < 0.6:
                evaluation["defensive_casting_need"] = 0.5

            # Utility spell value
            if state.environment.get("magical_obstacle", False):
                evaluation["utility_spell_value"] = 0.9
            elif state.environment.get("trapped_area", False):
                evaluation["utility_spell_value"] = 0.7

        else:
            # Non-combat magical opportunities
            if state.environment.get("magical_mystery", False):
                evaluation["utility_spell_value"] = 0.9
            if state.environment.get("social_advantage_needed", False):
                evaluation["utility_spell_value"] = 0.7

        return evaluation

    def learn_from_outcome(self, action: str, outcome: Dict[str, Any]) -> None:
        """Learn from action outcomes with Wizard-specific insights"""
        super().learn_from_outcome(action, outcome)

        # Learn spell effectiveness
        if "cast_" in action.lower():
            spell_name = action.replace("cast_", "").replace("_spell", "")
            effectiveness = outcome.get("effectiveness", 0.5)

            if spell_name in self.spell_effectiveness:
                # Weighted average update
                current = self.spell_effectiveness[spell_name]
                new_value = (current * 0.8 + effectiveness * 0.2)
                self.spell_effectiveness[spell_name] = new_value
            else:
                self.spell_effectiveness[spell_name] = effectiveness

        # Learn spell slot efficiency
        if outcome.get("spell_slot_used", 0) > 0:
            slot_level = outcome.get("spell_slot_used", 1)
            damage_dealt = outcome.get("damage", 0)
            enemies_affected = outcome.get("enemies_affected", 1)

            efficiency = (damage_dealt * enemies_affected) / (slot_level * 10)  # Normalized
            if efficiency > 0.8:
                self.resource_management["spell_slot_efficiency"] = min(1.0,
                    self.resource_management["spell_slot_efficiency"] + 0.02)

        # Learn situational awareness
        if outcome.get("melee_engaged", False):
            damage_taken = outcome.get("damage_taken", 0)
            if damage_taken > 15:
                self.combat_preferences["avoid_melee"] = min(1.0,
                    self.combat_preferences["avoid_melee"] + 0.05)

    def use_spell_slot(self, spell_level: int) -> bool:
        """Consume a spell slot of the given level"""
        if self.spell_slots.get(spell_level, 0) > 0:
            self.spell_slots[spell_level] -= 1
            return True
        return False

    def get_remaining_spell_slots(self) -> Dict[int, int]:
        """Get remaining spell slots by level"""
        return self.spell_slots.copy()

    def can_cast_spell(self, spell_level: int) -> bool:
        """Check if character can cast a spell of the given level"""
        return self.spell_slots.get(spell_level, 0) > 0