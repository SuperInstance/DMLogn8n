#!/usr/bin/env python3
"""
Adaptive Response Generator for D&D Agents
Integrates fine-tuned models with inference for personalized responses
"""

import json
import logging
import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import numpy as np

# Import from our modules
from agent_dnd_lora_trainer import CharacterExperience
from strategic_pattern_analyzer import StrategicPatternAnalyzer, StrategyRecommendation
from personalized_model_manager import PersonalizedModelManager, AgentProfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/logs/response_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ResponseStyle(Enum):
    """Different response styles for various situations"""
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    STRATEGIC = "strategic"
    SOCIAL = "social"
    CAUTIOUS = "cautious"
    IMPULSIVE = "impulsive"
    ANALYTICAL = "analytical"

@dataclass
class ResponseContext:
    """Context information for response generation"""
    agent_id: str
    current_situation: str
    game_state: Dict[str, Any]
    available_actions: List[str]
    nearby_characters: List[str]
    environment: Dict[str, Any]
    urgency_level: int  # 1-10
    stakes: str  # "low", "medium", "high", "critical"

@dataclass
class GeneratedResponse:
    """Generated response with metadata"""
    response_text: str
    confidence: float
    response_style: ResponseStyle
    reasoning: str
    strategic_considerations: List[str]
    risk_assessment: str
    expected_outcomes: List[str]
    alternative_responses: List[str]
    generation_time_ms: int
    model_confidence: float
    pattern_influence: float
    timestamp: datetime

@dataclass
class ResponseMetrics:
    """Metrics for response quality and effectiveness"""
    response_id: str
    agent_id: str
    situation_hash: str
    response_text: str
    success_score: float  # 0.0 to 1.0
    player_satisfaction: float  # 0.0 to 1.0
    strategic_effectiveness: float  # 0.0 to 1.0
    response_time_ms: int
    confidence_alignment: float  # How well confidence matched actual success
    feedback_received: List[str]
    timestamp: datetime

class AdaptiveResponseGenerator:
    """
    Generates adaptive responses using fine-tuned models and strategic patterns
    """

    def __init__(self, model_manager: PersonalizedModelManager):
        self.model_manager = model_manager
        self.pattern_analyzer = model_manager.pattern_analyzer

        # Response generation configuration
        self.response_templates = self._load_response_templates()
        self.style_adaptations = self._load_style_adaptations()
        self.situation_classifiers = self._load_situation_classifiers()

        # Response history and learning
        self.response_history: Dict[str, List[GeneratedResponse]] = {}
        self.response_metrics: Dict[str, List[ResponseMetrics]] = {}
        self.performance_tracker: Dict[str, Dict] = {}

        # Ensure directories exist
        Path("/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/data/responses").mkdir(parents=True, exist_ok=True)
        Path("/home/activeloguser/DMlogn8n/agent-intelligence-system/lora-adaptation/data/metrics").mkdir(parents=True, exist_ok=True)

        logger.info("Adaptive Response Generator initialized")

    def _load_response_templates(self) -> Dict[str, Dict]:
        """Load response templates for different situations"""
        return {
            "combat": {
                "aggressive": [
                    "I charge forward with {weapon} ready!",
                    "Time to show them what {class} can do!",
                    "For glory and victory! Attack!",
                    "No mercy for our enemies!"
                ],
                "defensive": [
                    "I take a defensive stance and prepare for their attack.",
                    "Protecting my allies is the priority.",
                    "Let them come to us - we'll be ready.",
                    "Shield wall formation, everyone!"
                ],
                "strategic": [
                    "Let's analyze their weaknesses first.",
                    "I'll position myself for maximum advantage.",
                    "Coordinated attack on my signal.",
                    "Feint left, attack right."
                ]
            },
            "social": {
                "diplomatic": [
                    "Perhaps we can find a peaceful solution to this.",
                    "I believe we can reach an agreement that benefits everyone.",
                    "Let's discuss this like reasonable beings.",
                    "There must be a way to resolve this without conflict."
                ],
                "intimidating": [
                    "You would do well to reconsider your position.",
                    "I suggest you think carefully about your next words.",
                    "My patience has its limits, as does my mercy.",
                    "You don't want to see me angry."
                ],
                "persuasive": [
                    "If you consider the situation carefully, you'll see I'm right.",
                    "This course of action benefits us all in the long run.",
                    "Trust me, I have experience in these matters.",
                    "Let me explain why this is the best path forward."
                ]
            },
            "exploration": {
                "cautious": [
                    "I proceed carefully, checking for traps and dangers.",
                    "Let me scout ahead before we move forward.",
                    "Something doesn't feel right about this place.",
                    "Better to be safe than sorry."
                ],
                "curious": [
                    "What fascinating secrets does this place hold?",
                    "I must investigate this unusual phenomenon.",
                    "There's something here worth exploring further.",
                    "Adventure awaits around every corner!"
                ],
                "methodical": [
                    "I'll systematically search this area.",
                    "Let's document everything we find.",
                    "There's a pattern here if we look closely enough.",
                    "Careful examination reveals the truth."
                ]
            }
        }

    def _load_style_adaptations(self) -> Dict[str, Dict]:
        """Load style-specific response adaptations"""
        return {
            "aggressive": {
                "keywords": ["attack", "charge", "destroy", "defeat", "conquer"],
                "tone": "bold, decisive, action-oriented",
                "response_patterns": ["I will...", "Let's...", "Time to...", "We must..."],
                "risk_preference": 0.8
            },
            "defensive": {
                "keywords": ["protect", "defend", "guard", "shield", "survive"],
                "tone": "cautious, protective, security-focused",
                "response_patterns": ["We should...", "Better to...", "Let's ensure...", "First we..."],
                "risk_preference": 0.3
            },
            "strategic": {
                "keywords": ["plan", "analyze", "coordinate", "optimize", "position"],
                "tone": "analytical, thoughtful, methodical",
                "response_patterns": ["We need to...", "The best approach is...", "Consider this...", "We should..."],
                "risk_preference": 0.5
            },
            "social": {
                "keywords": ["talk", "negotiate", "persuade", "diplomacy", "allies"],
                "tone": "charismatic, cooperative, relationship-focused",
                "response_patterns": ["Perhaps we can...", "Have you considered...", "I suggest...", "Let's..."],
                "risk_preference": 0.4
            }
        }

    def _load_situation_classifiers(self) -> Dict[str, List[str]]:
        """Load keywords for situation classification"""
        return {
            "combat": ["fight", "battle", "attack", "combat", "enemy", "monster", "weapon", "damage"],
            "social": ["talk", "negotiate", "persuade", "diplomacy", "conversation", "relationship", "trust"],
            "exploration": ["explore", "search", "investigate", "discover", "trap", "puzzle", "mystery", "treasure"],
            "puzzle": ["solve", "figure out", "puzzle", "riddle", "mechanism", "pattern", "logic"],
            "survival": ["survive", "danger", "threat", "escape", "hide", "endure", "resource"],
            "magic": ["spell", "magic", "arcane", "ritual", "enchantment", "supernatural"]
        }

    async def generate_response(self, context: ResponseContext,
                               force_style: Optional[ResponseStyle] = None,
                               max_length: int = 150) -> GeneratedResponse:
        """
        Generate an adaptive response based on context and agent's learned patterns

        Args:
            context: Response context information
            force_style: Force a specific response style
            max_length: Maximum response length

        Returns:
            Generated response with metadata
        """
        try:
            start_time = datetime.now()

            # Get agent profile
            agent_profile = self.model_manager.agent_profiles.get(context.agent_id)
            if not agent_profile:
                raise ValueError(f"Agent {context.agent_id} not found")

            # Determine optimal response style
            response_style = force_style or self._determine_response_style(context, agent_profile)

            # Build enhanced prompt
            enhanced_prompt = await self._build_enhanced_prompt(context, agent_profile, response_style)

            # Generate base response using personalized model
            base_response = await self.model_manager.generate_response(
                context.agent_id, enhanced_prompt, max_length, use_patterns=True
            )

            # Post-process and enhance response
            final_response = await self._post_process_response(
                base_response, context, agent_profile, response_style
            )

            # Create generated response object
            generated_response = GeneratedResponse(
                response_text=final_response["text"],
                confidence=final_response["confidence"],
                response_style=response_style,
                reasoning=final_response["reasoning"],
                strategic_considerations=final_response["strategic_considerations"],
                risk_assessment=final_response["risk_assessment"],
                expected_outcomes=final_response["expected_outcomes"],
                alternative_responses=final_response["alternative_responses"],
                generation_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                model_confidence=final_response["model_confidence"],
                pattern_influence=final_response["pattern_influence"],
                timestamp=datetime.now()
            )

            # Store response in history
            self._store_response(context.agent_id, generated_response)

            logger.info(f"Generated response for agent {context.agent_id} in {generated_response.generation_time_ms}ms")
            return generated_response

        except Exception as e:
            logger.error(f"Failed to generate response for agent {context.agent_id}: {str(e)}")
            # Return fallback response
            return self._generate_fallback_response(context)

    def _determine_response_style(self, context: ResponseContext, profile: AgentProfile) -> ResponseStyle:
        """Determine the best response style based on context and agent personality"""
        style_scores = {}

        # Base style from agent profile
        base_style = profile.playstyle.lower()
        style_scores[base_style] = 0.5

        # Analyze situation context
        situation_lower = context.current_situation.lower()

        # Check situation type
        for situation_type, keywords in self.situation_classifiers.items():
            if any(keyword in situation_lower for keyword in keywords):
                if situation_type == "combat":
                    style_scores["aggressive"] = style_scores.get("aggressive", 0) + 0.3
                    style_scores["defensive"] = style_scores.get("defensive", 0) + 0.2
                elif situation_type == "social":
                    style_scores["social"] = style_scores.get("social", 0) + 0.4
                elif situation_type == "exploration":
                    style_scores["cautious"] = style_scores.get("cautious", 0) + 0.3
                    style_scores["analytical"] = style_scores.get("analytical", 0) + 0.2

        # Consider urgency level
        if context.urgency_level >= 8:
            style_scores["impulsive"] = style_scores.get("impulsive", 0) + 0.3
            style_scores["aggressive"] = style_scores.get("aggressive", 0) + 0.2
        elif context.urgency_level <= 3:
            style_scores["strategic"] = style_scores.get("strategic", 0) + 0.3
            style_scores["analytical"] = style_scores.get("analytical", 0) + 0.2

        # Consider stakes
        if context.stakes == "critical":
            style_scores["defensive"] = style_scores.get("defensive", 0) + 0.2
            style_scores["strategic"] = style_scores.get("strategic", 0) + 0.2

        # Choose highest scoring style
        if style_scores:
            best_style = max(style_scores, key=style_scores.get)
            try:
                return ResponseStyle(best_style)
            except ValueError:
                # If style is not in enum, default to strategic
                return ResponseStyle.STRATEGIC

        return ResponseStyle.STRATEGIC  # Default

    async def _build_enhanced_prompt(self, context: ResponseContext, profile: AgentProfile,
                                   style: ResponseStyle) -> str:
        """Build an enhanced prompt incorporating context, profile, and style"""
        # Base character context
        base_prompt = f"""
You are {profile.character_name}, a Level {profile.level} {profile.character_class}.
Your personality traits: {', '.join(profile.personality_traits)}.
Your playstyle: {profile.playstyle}.

Current situation: {context.current_situation}
Urgency level (1-10): {context.urgency_level}
Stakes: {context.stakes}

Available actions: {', '.join(context.available_actions)}
Nearby characters: {', '.join(context.nearby_characters)}
Environment: {json.dumps(context.environment, indent=2)}

Your response should reflect your character's personality and the current situation.
"""

        # Add style-specific guidance
        style_info = self.style_adaptations.get(style.value, {})
        if style_info:
            base_prompt += f"""
Response style: {style.value}
Tone: {style_info.get('tone', 'neutral')}
Approach: {', '.join(style_info.get('response_patterns', []))}
"""

        # Add strategic context from patterns
        try:
            recommendations = await self.pattern_analyzer.get_strategy_recommendations(
                context.agent_id, context.current_situation,
                {
                    "class": profile.character_class,
                    "level": profile.level,
                    "skills": profile.skills
                }
            )

            if recommendations:
                top_rec = recommendations[0]
                base_prompt += f"""
Strategic advice: {top_rec.recommended_strategy}
Success probability: {top_rec.success_probability:.1%}
Risk assessment: {top_rec.risk_assessment}
"""
        except Exception as e:
            logger.warning(f"Failed to get strategy recommendations: {str(e)}")

        # Add response request
        base_prompt += "\n\nHow do you respond to this situation? Provide a brief, in-character response:"

        return base_prompt.strip()

    async def _post_process_response(self, base_response: str, context: ResponseContext,
                                    profile: AgentProfile, style: ResponseStyle) -> Dict[str, Any]:
        """Post-process and enhance the base response"""
        try:
            # Clean up response
            cleaned_response = self._clean_response_text(base_response)

            # Ensure it's in character
            character_response = self._ensure_in_character(cleaned_response, profile, style)

            # Generate reasoning
            reasoning = self._generate_reasoning(context, profile, style)

            # Generate strategic considerations
            strategic_considerations = await self._generate_strategic_considerations(context, profile)

            # Assess risk
            risk_assessment = self._assess_risk(context, style)

            # Predict outcomes
            expected_outcomes = self._predict_outcomes(context, character_response)

            # Generate alternatives
            alternative_responses = self._generate_alternative_responses(context, profile, style)

            # Calculate confidence scores
            model_confidence = self._calculate_model_confidence(context, character_response)
            pattern_influence = self._calculate_pattern_influence(context, profile)

            return {
                "text": character_response,
                "confidence": min(1.0, (model_confidence + pattern_influence) / 2),
                "reasoning": reasoning,
                "strategic_considerations": strategic_considerations,
                "risk_assessment": risk_assessment,
                "expected_outcomes": expected_outcomes,
                "alternative_responses": alternative_responses,
                "model_confidence": model_confidence,
                "pattern_influence": pattern_influence
            }

        except Exception as e:
            logger.error(f"Failed to post-process response: {str(e)}")
            return {
                "text": base_response,
                "confidence": 0.5,
                "reasoning": "Standard response based on current situation",
                "strategic_considerations": ["Assess the situation", "Consider available options"],
                "risk_assessment": "Moderate risk",
                "expected_outcomes": ["Uncertain outcome"],
                "alternative_responses": [],
                "model_confidence": 0.5,
                "pattern_influence": 0.0
            }

    def _clean_response_text(self, text: str) -> str:
        """Clean up response text"""
        # Remove common artifacts
        text = re.sub(r'^(How do you respond|Your response|I would|I will):\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\n+', ' ', text)  # Replace newlines with spaces
        text = text.strip()

        # Ensure it's a proper response
        if not text:
            return "I assess the situation carefully..."

        return text

    def _ensure_in_character(self, response: str, profile: AgentProfile, style: ResponseStyle) -> str:
        """Ensure response matches character personality"""
        # Check if response aligns with character traits
        response_lower = response.lower()
        style_info = self.style_adaptations.get(style.value, {})

        # Add character-appropriate elements if needed
        if profile.character_class.lower() == "wizard" and "magic" not in response_lower:
            response = response.replace("I", "As a wizard, I")
        elif profile.character_class.lower() == "fighter" and "fight" not in response_lower:
            response = response.replace("We", "We warriors")

        # Ensure response style consistency
        if style_info and style_info.get("keywords"):
            has_keyword = any(keyword in response_lower for keyword in style_info["keywords"])
            if not has_keyword and len(response) < 100:  # Only modify short responses
                # Add a style-appropriate element
                if style == ResponseStyle.AGGRESSIVE:
                    response += " Time for action!"
                elif style == ResponseStyle.DEFENSIVE:
                    response += " We must be careful."
                elif style == ResponseStyle.STRATEGIC:
                    response += " Let me think this through."

        return response

    def _generate_reasoning(self, context: ResponseContext, profile: AgentProfile, style: ResponseStyle) -> str:
        """Generate reasoning for the response choice"""
        reasoning_parts = []

        # Character-based reasoning
        reasoning_parts.append(f"As a {profile.character_class}, my natural approach is {profile.playstyle}")

        # Situation-based reasoning
        if context.urgency_level >= 7:
            reasoning_parts.append("The high urgency requires decisive action")
        elif context.stakes == "critical":
            reasoning_parts.append("The critical stakes demand careful consideration")

        # Style-based reasoning
        if style == ResponseStyle.AGGRESSIVE:
            reasoning_parts.append("Taking the initiative gives us the advantage")
        elif style == ResponseStyle.DEFENSIVE:
            reasoning_parts.append("Protecting myself and my allies is paramount")
        elif style == ResponseStyle.STRATEGIC:
            reasoning_parts.append("A well-planned approach maximizes our chances of success")
        elif style == ResponseStyle.SOCIAL:
            reasoning_parts.append("Diplomacy and cooperation are the best path forward")

        return "; ".join(reasoning_parts)

    async def _generate_strategic_considerations(self, context: ResponseContext, profile: AgentProfile) -> List[str]:
        """Generate strategic considerations for the current situation"""
        considerations = []

        # Basic situational awareness
        considerations.append("Assess the immediate threats and opportunities")

        # Character-specific considerations
        if profile.character_class.lower() in ["wizard", "sorcerer"]:
            considerations.append("Consider magical resources and spell availability")
        elif profile.character_class.lower() in ["fighter", "barbarian"]:
            considerations.append("Evaluate combat positioning and tactical advantages")
        elif profile.character_class.lower() in ["rogue", "ranger"]:
            considerations.append("Look for stealth and surprise opportunities")

        # Environment-based considerations
        if context.environment.get("terrain") == "confined":
            considerations.append("Limited space affects movement and area effects")
        elif context.environment.get("lighting") == "dark":
            considerations.append("Darkness provides opportunities and challenges")

        # Social considerations
        if len(context.nearby_characters) > 2:
            considerations.append("Multiple allies present for coordinated action")

        return considerations[:5]  # Return top 5 considerations

    def _assess_risk(self, context: ResponseContext, style: ResponseStyle) -> str:
        """Assess the risk level of the current approach"""
        base_risk = 0.5  # Medium risk by default

        # Adjust based on situation
        if context.urgency_level >= 8:
            base_risk += 0.2
        if context.stakes == "critical":
            base_risk += 0.3
        if len(context.available_actions) < 3:
            base_risk += 0.1

        # Adjust based on style
        style_risk = {
            ResponseStyle.AGGRESSIVE: 0.3,
            ResponseStyle.DEFENSIVE: -0.2,
            ResponseStyle.STRATEGIC: -0.1,
            ResponseStyle.SOCIAL: 0.0,
            ResponseStyle.CAUTIOUS: -0.3,
            ResponseStyle.IMPULSIVE: 0.4,
            ResponseStyle.ANALYTICAL: -0.1
        }

        final_risk = max(0.0, min(1.0, base_risk + style_risk.get(style, 0)))

        if final_risk <= 0.3:
            return "Low risk - cautious approach recommended"
        elif final_risk <= 0.7:
            return "Moderate risk - standard precautions advised"
        else:
            return "High risk - careful planning essential"

    def _predict_outcomes(self, context: ResponseContext, response: str) -> List[str]:
        """Predict likely outcomes of the chosen response"""
        outcomes = []

        # Analyze response content
        response_lower = response.lower()

        if any(word in response_lower for word in ["attack", "fight", "charge"]):
            outcomes.append("Likely combat engagement")
            outcomes.append("Potential for injury to self or allies")
        elif any(word in response_lower for word in ["talk", "negotiate", "diplomacy"]):
            outcomes.append("Potential for peaceful resolution")
            outcomes.append("Relationship building opportunity")

        if any(word in response_lower for word in ["careful", "check", "investigate"]):
            outcomes.append("Information gathering likely")
            outcomes.append("Reduced risk of surprise")

        # Consider context
        if context.urgency_level >= 7:
            outcomes.append("Time-sensitive results")

        return outcomes[:3]  # Return top 3 outcomes

    def _generate_alternative_responses(self, context: ResponseContext, profile: AgentProfile,
                                       style: ResponseStyle) -> List[str]:
        """Generate alternative response options"""
        alternatives = []

        # Alternative style responses
        alternative_styles = [s for s in ResponseStyle if s != style]

        for alt_style in alternative_styles[:2]:  # Generate 2 alternatives
            style_info = self.style_adaptations.get(alt_style.value, {})
            if style_info and style_info.get("response_patterns"):
                pattern = style_info["response_patterns"][0]
                alternative = f"{pattern} approach the situation differently."
                alternatives.append(alternative)

        # Action-based alternatives
        if "attack" not in context.current_situation.lower():
            alternatives.append("Consider a more direct approach")
        if "talk" not in context.current_situation.lower():
            alternatives.append("Try diplomacy first")

        return alternatives[:3]  # Return top 3 alternatives

    def _calculate_model_confidence(self, context: ResponseContext, response: str) -> float:
        """Calculate confidence in the model's response"""
        confidence = 0.7  # Base confidence

        # Adjust based on response length and quality
        if 10 <= len(response.split()) <= 50:  # Good length
            confidence += 0.1

        # Adjust based on situation complexity
        if context.urgency_level <= 5 and context.stakes != "critical":
            confidence += 0.1

        return min(1.0, confidence)

    def _calculate_pattern_influence(self, context: ResponseContext, profile: AgentProfile) -> float:
        """Calculate how much pattern analysis influenced the response"""
        # Check if agent has relevant patterns
        patterns = self.pattern_analyzer.pattern_cache.get(context.agent_id, [])

        if not patterns:
            return 0.0

        # Simple heuristic based on pattern count and relevance
        relevance_score = min(1.0, len(patterns) / 10.0)
        return relevance_score * 0.8  # Scale to max 0.8

    def _store_response(self, agent_id: str, response: GeneratedResponse):
        """Store response in history"""
        if agent_id not in self.response_history:
            self.response_history[agent_id] = []

        self.response_history[agent_id].append(response)

        # Keep only recent responses (last 100)
        if len(self.response_history[agent_id]) > 100:
            self.response_history[agent_id] = self.response_history[agent_id][-100:]

    def _generate_fallback_response(self, context: ResponseContext) -> GeneratedResponse:
        """Generate a fallback response when main generation fails"""
        fallback_text = "I need to consider this situation carefully before acting."

        return GeneratedResponse(
            response_text=fallback_text,
            confidence=0.3,
            response_style=ResponseStyle.CAUTIOUS,
            reasoning="Fallback response due to generation error",
            strategic_considerations=["Standard precautions advised"],
            risk_assessment="Unknown risk",
            expected_outcomes=["Uncertain"],
            alternative_responses=[],
            generation_time_ms=0,
            model_confidence=0.3,
            pattern_influence=0.0,
            timestamp=datetime.now()
        )

    async def provide_feedback(self, response_id: str, agent_id: str,
                             success_score: float, feedback_text: str) -> bool:
        """
        Provide feedback on a generated response for learning

        Args:
            response_id: ID of the response to feedback on
            agent_id: Agent identifier
            success_score: How successful the response was (0.0 to 1.0)
            feedback_text: Qualitative feedback

        Returns:
            True if feedback was recorded, False otherwise
        """
        try:
            # Find the response in history
            response_history = self.response_history.get(agent_id, [])
            target_response = None

            for response in response_history:
                if str(hash(response.response_text)) == response_id:
                    target_response = response
                    break

            if not target_response:
                logger.warning(f"Response {response_id} not found for agent {agent_id}")
                return False

            # Create metrics record
            metrics = ResponseMetrics(
                response_id=response_id,
                agent_id=agent_id,
                situation_hash=str(hash(target_response.timestamp)),
                response_text=target_response.response_text,
                success_score=success_score,
                player_satisfaction=0.0,  # Could be provided separately
                strategic_effectiveness=success_score,  # Use success as proxy for now
                response_time_ms=target_response.generation_time_ms,
                confidence_alignment=abs(target_response.confidence - success_score),
                feedback_received=[feedback_text],
                timestamp=datetime.now()
            )

            # Store metrics
            if agent_id not in self.response_metrics:
                self.response_metrics[agent_id] = []

            self.response_metrics[agent_id].append(metrics)

            # Create experience for learning
            experience = CharacterExperience(
                agent_id=agent_id,
                session_id=f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                situation="Response feedback session",
                action=target_response.response_text,
                outcome=feedback_text,
                success_score=success_score,
                reward=success_score * 100,  # Convert to reward
                context={
                    "response_style": target_response.response_style.value,
                    "confidence": target_response.confidence,
                    "generation_time_ms": target_response.generation_time_ms
                },
                skills_used=[],  # Would need to be determined
                character_class="",  # Would get from profile
                level=1,  # Would get from profile
                emotional_valence=0.0,  # Would need to be determined
                strategic_importance=0.8  # Feedback is important for learning
            )

            # Add experience to model manager for learning
            await self.model_manager.add_experience(experience)

            logger.info(f"Recorded feedback for response {response_id}, success score: {success_score}")
            return True

        except Exception as e:
            logger.error(f"Failed to provide feedback: {str(e)}")
            return False

    def get_response_analytics(self, agent_id: str, days: int = 7) -> Dict[str, Any]:
        """Get analytics on response generation for an agent"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            # Get recent responses
            recent_responses = [
                r for r in self.response_history.get(agent_id, [])
                if r.timestamp > cutoff_date
            ]

            # Get recent metrics
            recent_metrics = [
                m for m in self.response_metrics.get(agent_id, [])
                if m.timestamp > cutoff_date
            ]

            if not recent_responses:
                return {"error": "No recent responses found"}

            # Calculate analytics
            total_responses = len(recent_responses)
            avg_confidence = np.mean([r.confidence for r in recent_responses])
            avg_generation_time = np.mean([r.generation_time_ms for r in recent_responses])

            # Style distribution
            style_counts = {}
            for response in recent_responses:
                style = response.response_style.value
                style_counts[style] = style_counts.get(style, 0) + 1

            # Success metrics (if available)
            success_metrics = {}
            if recent_metrics:
                avg_success = np.mean([m.success_score for m in recent_metrics])
                success_metrics = {
                    "avg_success_score": avg_success,
                    "total_feedback": len(recent_metrics),
                    "avg_confidence_alignment": np.mean([m.confidence_alignment for m in recent_metrics])
                }

            return {
                "agent_id": agent_id,
                "period_days": days,
                "total_responses": total_responses,
                "avg_confidence": avg_confidence,
                "avg_generation_time_ms": avg_generation_time,
                "style_distribution": style_counts,
                "success_metrics": success_metrics,
                "pattern_influence_avg": np.mean([r.pattern_influence for r in recent_responses]),
                "most_common_style": max(style_counts, key=style_counts.get) if style_counts else None
            }

        except Exception as e:
            logger.error(f"Failed to get response analytics for agent {agent_id}: {str(e)}")
            return {"error": str(e)}

# Main execution for testing
if __name__ == "__main__":
    async def main():
        from personalized_model_manager import PersonalizedModelManager

        # Create model manager and response generator
        model_manager = PersonalizedModelManager()
        response_generator = AdaptiveResponseGenerator(model_manager)

        # Register a test agent
        character_info = {
            "name": "Aria Swiftblade",
            "class": "Rogue",
            "level": 8,
            "skills": ["stealth", "perception", "deception"],
            "traits": ["cunning", "agile", "cautious"]
        }

        await model_manager.register_agent("test_rogue_001", character_info)

        # Create test context
        context = ResponseContext(
            agent_id="test_rogue_001",
            current_situation="You discover a trapped treasure chest in an ancient dungeon",
            game_state={"health": 85, "position": "dungeon_chamber"},
            available_actions=["disarm_trap", "force_open", "search_for_mechanism", "leave_it"],
            nearby_characters=["Gandalf the Wizard", "Thorin the Fighter"],
            environment={"lighting": "dim", "terrain": "stone", "traps": "detected"},
            urgency_level=3,
            stakes="medium"
        )

        # Generate response
        response = await response_generator.generate_response(context)

        print(f"Generated Response: {response.response_text}")
        print(f"Style: {response.response_style.value}")
        print(f"Confidence: {response.confidence:.2f}")
        print(f"Reasoning: {response.reasoning}")

    asyncio.run(main())