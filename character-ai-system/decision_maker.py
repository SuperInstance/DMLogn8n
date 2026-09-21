"""
Strategic Decision Making System
Handles situation assessment, goal-oriented planning, and risk evaluation
"""

import random
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import math

from character_profile import CharacterProfile
from game_state import GameState


class DecisionType(Enum):
    """Types of decisions the AI can make"""
    COMBAT_ACTION = "combat_action"
    MOVEMENT = "movement"
    SOCIAL_INTERACTION = "social_interaction"
    ITEM_USAGE = "item_usage"
    SKILL_USAGE = "skill_usage"
    STRATEGIC_PLANNING = "strategic_planning"
    RETREAT = "retreat"
    COOPERATION = "cooperation"


class UrgencyLevel(Enum):
    """Urgency levels for decision making"""
    IMMEDIATE = 1    # Split-second decisions (combat)
    HIGH = 2         # Quick decisions needed
    MODERATE = 3     # Normal pace decisions
    LOW = 4          # Deliberate decisions


@dataclass
class SituationAssessment:
    """Assessment of current situation"""
    threat_level: float = 0.0  # 0-1 scale
    opportunity_level: float = 0.0  # 0-1 scale
    complexity: float = 0.0  # 0-1 scale
    time_pressure: float = 0.0  # 0-1 scale
    resource_availability: Dict[str, float] = field(default_factory=dict)
    environmental_factors: Dict[str, Any] = field(default_factory=dict)
    party_dynamics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionOption:
    """A possible decision option"""
    action_type: DecisionType
    action_name: str
    expected_outcome: Dict[str, float]
    risk_level: float
    resource_cost: Dict[str, float]
    success_probability: float
    alignment_score: float  # Alignment with personality and goals
    strategic_value: float  # Long-term strategic value


class StrategicDecisionMaker:
    """Core strategic decision making engine"""

    def __init__(self, character_profile: CharacterProfile):
        self.profile = character_profile
        self.current_state = GameState()
        self.current_goals: List[str] = []

        # Decision making parameters
        self.risk_tolerance = self._calculate_risk_tolerance()
        self.goal_priority_weights = self._initialize_goal_weights()
        self.decision_history: List[Dict[str, Any]] = []
        self.learning_rate = 0.1

        # Situation assessment
        self.current_assessment = SituationAssessment()

    def _calculate_risk_tolerance(self) -> float:
        """Calculate base risk tolerance based on character profile"""
        base_risk = 0.5

        # Class-based risk tolerance
        class_risk = {
            "Fighter": 0.6,
            "Rogue": 0.7,
            "Wizard": 0.4,
            "Cleric": 0.5,
            "Barbarian": 0.8,
            "Bard": 0.6,
            "Druid": 0.5,
            "Monk": 0.5,
            "Paladin": 0.6,
            "Ranger": 0.6,
            "Sorcerer": 0.5,
            "Warlock": 0.6
        }

        base_risk = class_risk.get(self.profile.character_class, 0.5)

        # Level adjustment - higher level characters are more risk-tolerant
        level_bonus = min(0.2, self.profile.level * 0.02)

        # Constitution affects physical risk tolerance
        con_bonus = (self.profile.constitution - 10) * 0.02

        return max(0.1, min(0.9, base_risk + level_bonus + con_bonus))

    def _initialize_goal_weights(self) -> Dict[str, float]:
        """Initialize goal priority weights"""
        return {
            "survival": 1.0,
            "party_survival": 0.9,
            "objective_completion": 0.8,
            "resource_efficiency": 0.6,
            "relationship_maintenance": 0.7,
            "personal_growth": 0.5,
            "strategic_advantage": 0.7
        }

    def update_state(self, new_state: GameState) -> None:
        """Update current game state"""
        self.current_state = new_state
        self._assess_situation()

    def update_goals(self, new_goals: List[str]) -> None:
        """Update current goals"""
        self.current_goals = new_goals

    def _assess_situation(self) -> None:
        """Assess current situation for decision making"""
        assessment = SituationAssessment()

        # Threat level assessment
        if self.current_state.combat_status:
            # Calculate threat based on enemy numbers and power
            enemy_count = len(self.current_state.enemies)
            assessment.threat_level = min(1.0, enemy_count * 0.2)

            # Adjust for character's current health
            health_ratio = self.current_state.resources.get("health_ratio", 1.0)
            assessment.threat_level += (1.0 - health_ratio) * 0.5
            assessment.threat_level = min(1.0, assessment.threat_level)
        else:
            assessment.threat_level = 0.1  # Minimal threat outside combat

        # Opportunity level assessment
        assessment.opportunity_level = self._assess_opportunities()

        # Complexity assessment
        assessment.complexity = self._assess_complexity()

        # Time pressure
        assessment.time_pressure = 0.8 if self.current_state.combat_status else 0.3

        # Resource availability
        assessment.resource_availability = self._assess_resources()

        # Environmental factors
        assessment.environmental_factors = self.current_state.environment

        # Party dynamics
        assessment.party_dynamics = self._assess_party_dynamics()

        self.current_assessment = assessment

    def _assess_opportunities(self) -> float:
        """Assess current opportunities"""
        opportunities = 0.0

        # Combat opportunities
        if self.current_state.combat_status:
            # Check for flanking opportunities
            if self.current_state.environment.get("can_flank", False):
                opportunities += 0.3

            # Check for weakened enemies
            if self.current_state.environment.get("enemies_weakened", False):
                opportunities += 0.4

            # Check for tactical advantages
            if self.current_state.environment.get("high_ground", False):
                opportunities += 0.2

        # Social opportunities
        if not self.current_state.combat_status:
            # Check for dialogue opportunities
            if self.current_state.environment.get("npc_present", False):
                opportunities += 0.3

            # Check for exploration opportunities
            if self.current_state.environment.get("unexplored_areas", False):
                opportunities += 0.2

        return min(1.0, opportunities)

    def _assess_complexity(self) -> float:
        """Assess situation complexity"""
        complexity = 0.0

        # Number of actors in situation
        total_actors = len(self.current_state.allies) + len(self.current_state.enemies)
        complexity += min(0.5, total_actors * 0.1)

        # Environmental complexity
        env_complexity = len(self.current_state.environment) * 0.05
        complexity += min(0.3, env_complexity)

        # Objective complexity
        if self.current_state.current_objective:
            if "complex" in self.current_state.current_objective.lower():
                complexity += 0.3
            elif "multi" in self.current_state.current_objective.lower():
                complexity += 0.2

        return min(1.0, complexity)

    def _assess_resources(self) -> Dict[str, float]:
        """Assess available resources"""
        return self.current_state.resources

    def _assess_party_dynamics(self) -> Dict[str, Any]:
        """Assess current party dynamics"""
        return {
            "party_size": len(self.current_state.allies),
            "party_health": self.current_state.resources.get("party_health_ratio", 1.0),
            "party_morale": self.current_state.resources.get("party_morale", 0.7),
            "roles_filled": self.current_state.resources.get("roles_filled", [])
        }

    def make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make a strategic decision based on current situation"""
        # Get urgency level
        urgency = self._determine_urgency()

        # Generate decision options
        options = self._generate_decision_options(context)

        # Evaluate options
        evaluated_options = self._evaluate_options(options, context)

        # Select best option
        best_option = self._select_best_option(evaluated_options, urgency)

        # Create decision
        decision = {
            "action": best_option.action_name,
            "action_type": best_option.action_type.value,
            "confidence": best_option.success_probability,
            "reasoning": self._generate_reasoning(best_option, context),
            "expected_outcome": best_option.expected_outcome,
            "risk_assessment": best_option.risk_level,
            "resource_cost": best_option.resource_cost,
            "urgency": urgency.value,
            "strategic_value": best_option.strategic_value
        }

        return decision

    def _determine_urgency(self) -> UrgencyLevel:
        """Determine urgency level for decision making"""
        if self.current_state.combat_status:
            health_ratio = self.current_state.resources.get("health_ratio", 1.0)
            if health_ratio < 0.3:
                return UrgencyLevel.IMMEDIATE
            else:
                return UrgencyLevel.HIGH
        elif self.current_assessment.threat_level > 0.7:
            return UrgencyLevel.HIGH
        elif self.current_assessment.complexity > 0.7:
            return UrgencyLevel.MODERATE
        else:
            return UrgencyLevel.LOW

    def _generate_decision_options(self, context: Dict[str, Any]) -> List[DecisionOption]:
        """Generate possible decision options"""
        options = []

        # Get personality bias
        personality_bias = context.get("personality_bias", {})
        class_recommendations = context.get("class_recommendations", [])

        # Combat options
        if self.current_state.combat_status:
            options.extend(self._generate_combat_options(personality_bias, class_recommendations))

        # Movement options
        options.extend(self._generate_movement_options())

        # Social options (if not in combat)
        if not self.current_state.combat_status:
            options.extend(self._generate_social_options(personality_bias))

        # Item usage options
        options.extend(self._generate_item_options())

        # Strategic options
        options.extend(self._generate_strategic_options())

        return options

    def _generate_combat_options(self, personality_bias: Dict[str, Any],
                                class_recommendations: List[str]) -> List[DecisionOption]:
        """Generate combat-specific options"""
        options = []

        # Attack option
        attack_option = DecisionOption(
            action_type=DecisionType.COMBAT_ACTION,
            action_name="attack_primary_target",
            expected_outcome={"damage": 0.7, "risk": 0.5},
            risk_level=0.6,
            resource_cost={"stamina": 0.2},
            success_probability=0.7,
            alignment_score=self._calculate_alignment_score("attack", personality_bias),
            strategic_value=0.6
        )
        options.append(attack_option)

        # Defensive option
        if self.current_assessment.threat_level > 0.6:
            defend_option = DecisionOption(
                action_type=DecisionType.COMBAT_ACTION,
                action_name="defensive_stance",
                expected_outcome={"protection": 0.8, "damage": 0.1},
                risk_level=0.2,
                resource_cost={"stamina": 0.1},
                success_probability=0.9,
                alignment_score=self._calculate_alignment_score("defend", personality_bias),
                strategic_value=0.7
            )
            options.append(defend_option)

        # Tactical options based on class recommendations
        for recommendation in class_recommendations[:3]:  # Limit to top 3
            tactical_option = DecisionOption(
                action_type=DecisionType.COMBAT_ACTION,
                action_name=recommendation,
                expected_outcome={"advantage": 0.6},
                risk_level=0.5,
                resource_cost={"stamina": 0.3},
                success_probability=0.6,
                alignment_score=self._calculate_alignment_score(recommendation, personality_bias),
                strategic_value=0.8
            )
            options.append(tactical_option)

        return options

    def _generate_movement_options(self) -> List[DecisionOption]:
        """Generate movement options"""
        options = []

        if self.current_state.combat_status:
            # Tactical movement
            move_option = DecisionOption(
                action_type=DecisionType.MOVEMENT,
                action_name="tactical_positioning",
                expected_outcome={"positioning": 0.8, "safety": 0.6},
                risk_level=0.3,
                resource_cost={"stamina": 0.15},
                success_probability=0.8,
                alignment_score=0.7,
                strategic_value=0.7
            )
            options.append(move_option)

        # Retreat option (high threat situations)
        if self.current_assessment.threat_level > 0.8:
            retreat_option = DecisionOption(
                action_type=DecisionType.RETREAT,
                action_name="strategic_retreat",
                expected_outcome={"survival": 0.9, "positioning": 0.4},
                risk_level=0.4,
                resource_cost={"stamina": 0.4},
                success_probability=0.7,
                alignment_score=0.6,
                strategic_value=0.9
            )
            options.append(retreat_option)

        return options

    def _generate_social_options(self, personality_bias: Dict[str, Any]) -> List[DecisionOption]:
        """Generate social interaction options"""
        options = []

        # Diplomatic approach
        if personality_bias.get("conflict") == "cooperative_diplomatic":
            diplomatic_option = DecisionOption(
                action_type=DecisionType.SOCIAL_INTERACTION,
                action_name="diplomatic_approach",
                expected_outcome={"relations": 0.8, "information": 0.6},
                risk_level=0.1,
                resource_cost={},
                success_probability=0.7,
                alignment_score=0.9,
                strategic_value=0.7
            )
            options.append(diplomatic_option)

        # Direct approach
        elif personality_bias.get("conflict") == "competitive_direct":
            direct_option = DecisionOption(
                action_type=DecisionType.SOCIAL_INTERACTION,
                action_name="direct_negotiation",
                expected_outcome={"relations": 0.5, "goals": 0.7},
                risk_level=0.4,
                resource_cost={},
                success_probability=0.6,
                alignment_score=0.8,
                strategic_value=0.6
            )
            options.append(direct_option)

        return options

    def _generate_item_options(self) -> List[DecisionOption]:
        """Generate item usage options"""
        options = []

        # Healing potion (if injured)
        health_ratio = self.current_state.resources.get("health_ratio", 1.0)
        if health_ratio < 0.7:
            heal_option = DecisionOption(
                action_type=DecisionType.ITEM_USAGE,
                action_name="use_healing_potion",
                expected_outcome={"health": 0.8},
                risk_level=0.1,
                resource_cost={"healing_potion": 1},
                success_probability=0.95,
                alignment_score=0.8,
                strategic_value=0.9
            )
            options.append(heal_option)

        return options

    def _generate_strategic_options(self) -> List[DecisionOption]:
        """Generate strategic planning options"""
        options = []

        if not self.current_state.combat_status:
            # Planning option
            plan_option = DecisionOption(
                action_type=DecisionType.STRATEGIC_PLANNING,
                action_name="assess_situation",
                expected_outcome={"information": 0.9, "planning": 0.8},
                risk_level=0.0,
                resource_cost={"time": 0.3},
                success_probability=0.9,
                alignment_score=0.7,
                strategic_value=0.8
            )
            options.append(plan_option)

        return options

    def _calculate_alignment_score(self, action: str, personality_bias: Dict[str, Any]) -> float:
        """Calculate how well an action aligns with personality"""
        base_score = 0.5

        # Adjust based on personality bias
        approach = personality_bias.get("approach", "balanced")
        planning = personality_bias.get("planning", "moderate")
        risk_preference = personality_bias.get("risk", "moderate")

        if action == "attack":
            if approach == "creative_experimental":
                base_score += 0.2
            if risk_preference == "bold_risk_tolerant":
                base_score += 0.3
            elif risk_preference == "cautious_risk_averse":
                base_score -= 0.2

        elif action == "defend":
            if risk_preference == "cautious_risk_averse":
                base_score += 0.3
            if planning == "detailed_strategic":
                base_score += 0.2

        elif action == "diplomatic_approach":
            if personality_bias.get("social") == "assertive_leading":
                base_score += 0.2
            if personality_bias.get("conflict") == "cooperative_diplomatic":
                base_score += 0.4

        return max(0.0, min(1.0, base_score))

    def _evaluate_options(self, options: List[DecisionOption],
                         context: Dict[str, Any]) -> List[DecisionOption]:
        """Evaluate and score decision options"""
        for option in options:
            # Calculate composite score
            option_score = 0.0

            # Success probability weight
            option_score += option.success_probability * 0.3

            # Alignment with personality
            option_score += option.alignment_score * 0.2

            # Strategic value
            option_score += option.strategic_value * 0.2

            # Risk assessment (adjusted for risk tolerance)
            risk_adjustment = 1.0 - abs(option.risk_level - self.risk_tolerance)
            option_score += risk_adjustment * 0.15

            # Resource efficiency
            resource_efficiency = 1.0 - sum(option.resource_cost.values()) / len(option.resource_cost) if option.resource_cost else 1.0
            option_score += resource_efficiency * 0.15

            # Store the composite score
            option.composite_score = option_score

        # Sort by composite score
        return sorted(options, key=lambda x: x.composite_score, reverse=True)

    def _select_best_option(self, evaluated_options: List[DecisionOption],
                           urgency: UrgencyLevel) -> DecisionOption:
        """Select the best option based on evaluation and urgency"""
        if not evaluated_options:
            # Create default option
            return DecisionOption(
                action_type=DecisionType.STRATEGIC_PLANNING,
                action_name="wait_and_assess",
                expected_outcome={"information": 0.5},
                risk_level=0.1,
                resource_cost={},
                success_probability=1.0,
                alignment_score=0.5,
                strategic_value=0.3
            )

        # Urgency affects selection
        if urgency == UrgencyLevel.IMMEDIATE:
            # Prefer immediate, high-success options
            immediate_options = [opt for opt in evaluated_options if opt.success_probability > 0.7]
            if immediate_options:
                return immediate_options[0]

        # Return highest scored option
        return evaluated_options[0]

    def _generate_reasoning(self, option: DecisionOption, context: Dict[str, Any]) -> str:
        """Generate reasoning for the selected option"""
        reasoning_parts = []

        # Primary reasoning
        if option.success_probability > 0.8:
            reasoning_parts.append("High success probability makes this choice reliable")
        elif option.strategic_value > 0.7:
            reasoning_parts.append("Strong strategic value for long-term goals")
        elif option.risk_level < 0.3:
            reasoning_parts.append("Low risk approach suitable for current situation")

        # Situational reasoning
        if self.current_state.combat_status:
            if option.action_type == DecisionType.COMBAT_ACTION:
                reasoning_parts.append("Direct action needed in combat situation")
        else:
            if option.action_type == DecisionType.SOCIAL_INTERACTION:
                reasoning_parts.append("Diplomatic approach favorable outside combat")

        # Resource-based reasoning
        if option.resource_cost:
            reasoning_parts.append("Resource cost acceptable for expected benefit")

        return " | ".join(reasoning_parts) if reasoning_parts else "Best available option given current constraints"

    def learn_from_outcome(self, action: str, outcome: Dict[str, Any]) -> None:
        """Learn from action outcomes to improve future decisions"""
        success = outcome.get("success", False)
        unexpected_factors = outcome.get("unexpected_factors", [])

        # Find similar past decisions
        similar_decisions = [d for d in self.decision_history if d.get("action") == action]

        if similar_decisions:
            # Update success probabilities based on outcome
            for decision in self.decision_history:
                if decision.get("action") == action:
                    current_prob = decision.get("success_probability", 0.5)
                    if success:
                        new_prob = min(1.0, current_prob + self.learning_rate)
                    else:
                        new_prob = max(0.0, current_prob - self.learning_rate)
                    decision["success_probability"] = new_prob

        # Adjust risk tolerance based on outcomes
        if success and outcome.get("risk_taken", 0) > self.risk_tolerance:
            self.risk_tolerance = min(0.9, self.risk_tolerance + 0.05)
        elif not success and outcome.get("risk_taken", 0) < self.risk_tolerance:
            self.risk_tolerance = max(0.1, self.risk_tolerance - 0.05)

    def get_decision_patterns(self) -> Dict[str, Any]:
        """Get analysis of decision patterns"""
        if not self.decision_history:
            return {"message": "Insufficient decision history"}

        # Analyze recent decisions
        recent_decisions = self.decision_history[-10:] if len(self.decision_history) >= 10 else self.decision_history

        action_types = {}
        success_rates = {}

        for decision in recent_decisions:
            action_type = decision.get("action_type", "unknown")
            success = decision.get("success", False)

            if action_type not in action_types:
                action_types[action_type] = 0
                success_rates[action_type] = {"total": 0, "success": 0}

            action_types[action_type] += 1
            success_rates[action_type]["total"] += 1
            if success:
                success_rates[action_type]["success"] += 1

        # Calculate success rates
        for action_type in success_rates:
            total = success_rates[action_type]["total"]
            successes = success_rates[action_type]["success"]
            success_rates[action_type]["rate"] = successes / total if total > 0 else 0

        return {
            "preferred_actions": action_types,
            "success_rates": success_rates,
            "total_decisions": len(self.decision_history),
            "risk_tolerance": self.risk_tolerance
        }