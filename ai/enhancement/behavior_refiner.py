#!/usr/bin/env python3
"""
Behavior Refiner - Refines AI agent behaviors and personalities

This module enhances AI personality traits, behavioral consistency, and
adaptive behavior patterns based on user interactions and context.
"""

import json
import time
import math
import random
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

class PersonalityTrait(Enum):
    FRIENDLINESS = "friendliness"
    CREATIVITY = "creativity"
    INTELLIGENCE = "intelligence"
    EMPATHY = "empathy"
    HUMOR = "humor"
    PROFESSIONALISM = "professionalism"
    CONFIDENCE = "confidence"
    ENTHUSIASM = "enthusiasm"
    CURIOSITY = "curiosity"
    PATIENCE = "patience"

class BehaviorType(Enum):
    COMMUNICATION = "communication"
    PROBLEM_SOLVING = "problem_solving"
    SOCIAL = "social"
    LEARNING = "learning"
    ADAPTIVE = "adaptive"

@dataclass
class PersonalityProfile:
    """Represents AI agent personality profile."""
    traits: Dict[PersonalityTrait, float] = field(default_factory=dict)
    behavior_patterns: Dict[BehaviorType, List[str]] = field(default_factory=dict)
    adaptation_rate: float = 0.1
    consistency_threshold: float = 0.8

@dataclass
class BehaviorMetrics:
    """Metrics for behavior refinement performance."""
    consistency_score: float
    adaptation_score: float
    engagement_score: float
    personality_match: float
    response_variance: float

class BehaviorRefiner:
    """
    Advanced behavior refinement system for AI agents.

    Features:
    - Personality trait fine-tuning
    - Behavioral consistency enforcement
    - Adaptive behavior adjustment
    - Context-appropriate responses
    - Personality evolution tracking
    - Multi-dimensional behavior modeling
    """

    def __init__(self, agent_id: str, initial_profile: PersonalityProfile = None):
        self.agent_id = agent_id
        self.profile = initial_profile or self._create_default_profile()
        self.behavior_history = []
        self.adaptation_log = []
        self.personality_templates = self._load_personality_templates()
        self.behavior_patterns = self._load_behavior_patterns()

        # Configuration
        self.adaptation_enabled = True
        self.max_history_size = 1000
        self.personality_drift_threshold = 0.3

        # Learning parameters
        self.learning_rate = 0.05
        self.decay_factor = 0.95
        self.reinforcement_strength = 0.2

        # Logging
        self.logger = logging.getLogger(f"behavior_refiner_{agent_id}")

    def refine_behavior(self, user_input: str, current_response: str,
                       context: Dict[str, Any] = None,
                       feedback: Dict[str, float] = None) -> Tuple[str, BehaviorMetrics]:
        """
        Refine AI behavior based on context and feedback.

        Args:
            user_input: User's message
            current_response: AI's current response
            context: Interaction context
            feedback: User feedback scores (0-1)

        Returns:
            Tuple of (refined_response, behavior_metrics)
        """
        # Analyze current behavior
        current_behavior = self._analyze_behavior(current_response)

        # Apply personality refinement
        refined_response = self._apply_personality_refinement(current_response, context)

        # Ensure behavioral consistency
        refined_response = self._ensure_consistency(refined_response, context)

        # Apply adaptive adjustments
        if self.adaptation_enabled and feedback:
            refined_response = self._apply_adaptive_adjustments(refined_response, feedback)

        # Calculate behavior metrics
        metrics = self._calculate_behavior_metrics(current_response, refined_response, feedback)

        # Update behavior profile
        self._update_behavior_profile(user_input, refined_response, context, feedback)

        # Log interaction
        self._log_interaction(user_input, refined_response, metrics, feedback)

        return refined_response, metrics

    def _apply_personality_refinement(self, response: str, context: Dict[str, Any]) -> str:
        """Apply personality traits to refine response."""
        refined_response = response

        # Apply each personality trait
        for trait, value in self.profile.traits.items():
            refined_response = self._apply_trait(refined_response, trait, value, context)

        return refined_response

    def _apply_trait(self, response: str, trait: PersonalityTrait,
                    intensity: float, context: Dict[str, Any]) -> str:
        """Apply a specific personality trait to response."""
        if intensity < 0.3:  # Trait not strong enough to apply
            return response

        if trait == PersonalityTrait.FRIENDLINESS:
            return self._apply_friendliness(response, intensity)
        elif trait == PersonalityTrait.CREATIVITY:
            return self._apply_creativity(response, intensity)
        elif trait == PersonalityTrait.EMPATHY:
            return self._apply_empathy(response, intensity, context)
        elif trait == PersonalityTrait.HUMOR:
            return self._apply_humor(response, intensity)
        elif trait == PersonalityTrait.PROFESSIONALISM:
            return self._apply_professionalism(response, intensity)
        elif trait == PersonalityTrait.CONFIDENCE:
            return self._apply_confidence(response, intensity)
        elif trait == PersonalityTrait.ENTHUSIASM:
            return self._apply_enthusiasm(response, intensity)
        elif trait == PersonalityTrait.CURIOSITY:
            return self._apply_curiosity(response, intensity)
        elif trait == PersonalityTrait.PATIENCE:
            return self._apply_patience(response, intensity)

        return response

    def _apply_friendliness(self, response: str, intensity: float) -> str:
        """Apply friendliness trait to response."""
        friendly_elements = [
            "I'd be happy to help with that!",
            "That's a great question!",
            "I'm here to assist you.",
            "Thanks for asking!"
        ]

        # Add friendly opening
        if intensity > 0.7 and not response.startswith(('I', 'That', 'Thanks')):
            friendly_opening = random.choice(friendly_elements)
            response = f"{friendly_opening} {response}"

        # Add friendly language
        if intensity > 0.5:
            friendly_replacements = {
                r'\byou should\b': 'you might consider',
                r'\bit is\b': "it's really",
                r'\bthe answer is\b': 'here\'s what I found'
            }
            for formal, friendly in friendly_replacements.items():
                response = response.replace(formal, friendly)

        return response

    def _apply_creativity(self, response: str, intensity: float) -> str:
        """Apply creativity trait to response."""
        if intensity < 0.5:
            return response

        # Add creative analogies or metaphors
        creative_elements = [
            "Think of it like this:",
            "Here's an interesting way to look at it:",
            "You could imagine it as:",
            "Another perspective to consider is:"
        ]

        # Add creative language
        creative_replacements = {
            r'\bsimple\b': 'elegant',
            r'\bbasic\b': 'fundamental',
            r'\bimportant\b': 'crucial',
            r'\binteresting\b': 'fascinating'
        }

        for basic, creative in creative_replacements.items():
            response = response.replace(basic, creative)

        # Occasionally add creative framing
        if intensity > 0.7 and random.random() < 0.3:
            creative_frame = random.choice(creative_elements)
            response = f"{creative_frame} {response}"

        return response

    def _apply_empathy(self, response: str, intensity: float, context: Dict[str, Any]) -> str:
        """Apply empathy trait to response."""
        empathetic_elements = [
            "I understand that might be challenging.",
            "That sounds like a difficult situation.",
            "I appreciate you sharing that with me.",
            "Your perspective is valuable."
        ]

        # Check for negative emotions in context
        if context and context.get('user_emotion', '').lower() in ['frustrated', 'confused', 'worried']:
            if intensity > 0.6:
                empathetic_phrase = random.choice(empathetic_elements)
                response = f"{empathetic_phrase} {response}"

        # Add understanding language
        if intensity > 0.5:
            empathetic_replacements = {
                r'\byou need to\b': 'it might help to',
                r'\bthe problem is\b': 'I see the challenge is',
                r'\bthat\'s wrong\b': 'that\'s not quite right'
            }
            for direct, empathetic in empathetic_replacements.items():
                response = response.replace(direct, empathetic)

        return response

    def _apply_humor(self, response: str, intensity: float) -> str:
        """Apply humor trait to response."""
        if intensity < 0.5:
            return response

        light_humor = [
            "And don't worry, even AI's have to look things up sometimes!",
            "That's a classic brain-teaser, isn't it?",
            "I had to run a quick diagnostic on that one!",
            "Even my circuits needed an extra moment for that!"
        ]

        # Add light humor occasionally
        if intensity > 0.7 and random.random() < 0.2:
            humorous_addition = random.choice(light_humor)
            response = f"{response} {humorous_addition}"

        return response

    def _apply_professionalism(self, response: str, intensity: float) -> str:
        """Apply professionalism trait to response."""
        if intensity < 0.5:
            return response

        # Professional language replacements
        professional_replacements = {
            r'\byeah\b': 'yes',
            r'\bcool\b': 'excellent',
            r'\bgot it\b': 'understood',
            r'\bsure\b': 'certainly',
            r'\bthanks\b': 'thank you'
        }

        for casual, professional in professional_replacements.items():
            response = response.replace(casual, professional)

        # Add professional structure
        if intensity > 0.7:
            if not response.endswith(('.', '!', '?')):
                response += "."

        return response

    def _apply_confidence(self, response: str, intensity: float) -> str:
        """Apply confidence trait to response."""
        if intensity < 0.5:
            return response

        # Confident language
        confident_phrases = [
            "Based on my analysis,",
            "I can confirm that",
            "The optimal approach is",
            "I recommend"
        ]

        # Remove hesitant language
        hesitant_phrases = [
            "I think maybe",
            "It might be",
            "Perhaps",
            "I could be wrong, but"
        ]

        for hesitant in hesitant_phrases:
            response = response.replace(hesitant, "")

        # Add confident framing
        if intensity > 0.7 and random.random() < 0.3:
            confident_frame = random.choice(confident_phrases)
            response = f"{confident_frame} {response}"

        return response

    def _apply_enthusiasm(self, response: str, intensity: float) -> str:
        """Apply enthusiasm trait to response."""
        if intensity < 0.5:
            return response

        enthusiastic_elements = [
            "Great question!",
            "I love helping with this!",
            "This is really interesting!",
            "Excellent!"
        ]

        enthusiastic_replacements = {
            r'\bgood\b': 'fantastic',
            r'\bnice\b': 'wonderful',
            r'\binteresting\b': 'fascinating'
        }

        # Apply enthusiastic language
        for normal, enthusiastic in enthusiastic_replacements.items():
            response = response.replace(normal, enthusiastic)

        # Add enthusiastic opening
        if intensity > 0.7 and random.random() < 0.4:
            enthusiastic_phrase = random.choice(enthusiastic_elements)
            response = f"{enthusiastic_phrase} {response}"

        return response

    def _apply_curiosity(self, response: str, intensity: float) -> str:
        """Apply curiosity trait to response."""
        if intensity < 0.5:
            return response

        curious_questions = [
            "What aspect are you most curious about?",
            "Have you considered other approaches?",
            "What led you to this question?",
            "What's your take on this?"
        ]

        # Add curious follow-up
        if intensity > 0.6 and '?' not in response:
            curious_followup = random.choice(curious_questions)
            response = f"{response} {curious_followup}"

        return response

    def _apply_patience(self, response: str, intensity: float) -> str:
        """Apply patience trait to response."""
        if intensity < 0.5:
            return response

        patient_phrases = [
            "Take your time to explore this.",
            "It's completely fine to ask for clarification.",
            "We can work through this step by step.",
            "There's no rush in understanding this."
        ]

        # Add patient reassurance
        if intensity > 0.6:
            patient_reassurance = random.choice(patient_phrases)
            response = f"{response} {patient_reassurance}"

        return response

    def _ensure_consistency(self, response: str, context: Dict[str, Any]) -> str:
        """Ensure behavioral consistency with established patterns."""
        # Check against historical behavior patterns
        recent_behaviors = self.behavior_history[-10:] if self.behavior_history else []

        for behavior in recent_behaviors:
            consistency_score = self._calculate_consistency(response, behavior['response'])
            if consistency_score < self.profile.consistency_threshold:
                response = self._adjust_for_consistency(response, behavior)

        return response

    def _apply_adaptive_adjustments(self, response: str, feedback: Dict[str, float]) -> str:
        """Apply adaptive adjustments based on user feedback."""
        if not feedback:
            return response

        # Adapt personality traits based on feedback
        for trait_name, feedback_score in feedback.items():
            try:
                trait = PersonalityTrait(trait_name)
                current_value = self.profile.traits.get(trait, 0.5)
                adjustment = (feedback_score - 0.5) * self.reinforcement_strength
                new_value = max(0.0, min(1.0, current_value + adjustment))
                self.profile.traits[trait] = new_value
            except ValueError:
                continue

        # Apply adjustments to response
        return self._apply_personality_refinement(response, {})

    def _analyze_behavior(self, response: str) -> Dict[str, Any]:
        """Analyze current behavior patterns in response."""
        behavior_analysis = {
            'length': len(response),
            'sentiment': self._analyze_sentiment(response),
            'complexity': self._analyze_complexity(response),
            'formality': self._analyze_formality(response),
            'creativity': self._analyze_creativity(response)
        }

        return behavior_analysis

    def _calculate_behavior_metrics(self, original_response: str, refined_response: str,
                                  feedback: Dict[str, float]) -> BehaviorMetrics:
        """Calculate comprehensive behavior metrics."""
        # Consistency score
        consistency_score = self._calculate_overall_consistency(refined_response)

        # Adaptation score
        adaptation_score = self._calculate_adaptation_score(feedback)

        # Engagement score
        engagement_score = self._calculate_engagement_score(refined_response)

        # Personality match score
        personality_match = self._calculate_personality_match(refined_response)

        # Response variance
        response_variance = self._calculate_response_variance(original_response, refined_response)

        return BehaviorMetrics(
            consistency_score=consistency_score,
            adaptation_score=adaptation_score,
            engagement_score=engagement_score,
            personality_match=personality_match,
            response_variance=response_variance
        )

    def _update_behavior_profile(self, user_input: str, response: str,
                               context: Dict[str, Any], feedback: Dict[str, float]):
        """Update behavior profile based on new interaction."""
        # Store interaction
        interaction = {
            'timestamp': time.time(),
            'user_input': user_input,
            'response': response,
            'context': context,
            'feedback': feedback,
            'profile_snapshot': self.profile.traits.copy()
        }

        self.behavior_history.append(interaction)

        # Keep history manageable
        if len(self.behavior_history) > self.max_history_size:
            self.behavior_history = self.behavior_history[-self.max_history_size:]

        # Apply gradual personality evolution
        if feedback and self.adaptation_enabled:
            self._evolve_personality(feedback)

    def get_personality_insights(self) -> Dict[str, Any]:
        """Get insights into personality development and patterns."""
        if not self.behavior_history:
            return {'message': 'Insufficient data for personality analysis'}

        # Calculate trait trends
        trait_trends = self._calculate_trait_trends()

        # Identify dominant traits
        dominant_traits = self._get_dominant_traits()

        # Analyze adaptation patterns
        adaptation_patterns = self._analyze_adaptation_patterns()

        # Consistency analysis
        consistency_analysis = self._analyze_consistency_patterns()

        return {
            'current_personality': {trait.value: value for trait, value in self.profile.traits.items()},
            'dominant_traits': dominant_traits,
            'trait_trends': trait_trends,
            'adaptation_patterns': adaptation_patterns,
            'consistency_analysis': consistency_analysis,
            'total_interactions': len(self.behavior_history),
            'adaptation_enabled': self.adaptation_enabled
        }

    # Helper methods
    def _create_default_profile(self) -> PersonalityProfile:
        """Create default personality profile."""
        return PersonalityProfile(
            traits={
                PersonalityTrait.FRIENDLINESS: 0.7,
                PersonalityTrait.CREATIVITY: 0.6,
                PersonalityTrait.INTELLIGENCE: 0.8,
                PersonalityTrait.EMPATHY: 0.6,
                PersonalityTrait.HUMOR: 0.4,
                PersonalityTrait.PROFESSIONALISM: 0.7,
                PersonalityTrait.CONFIDENCE: 0.7,
                PersonalityTrait.ENTHUSIASM: 0.6,
                PersonalityTrait.CURIOSITY: 0.8,
                PersonalityTrait.PATIENCE: 0.8
            },
            adaptation_rate=0.1,
            consistency_threshold=0.8
        )

    def _load_personality_templates(self) -> Dict[str, Dict[str, float]]:
        """Load predefined personality templates."""
        return {
            'helpful_assistant': {
                'friendliness': 0.9,
                'empathy': 0.8,
                'patience': 0.9,
                'professionalism': 0.7
            },
            'creative_companion': {
                'creativity': 0.9,
                'enthusiasm': 0.8,
                'curiosity': 0.9,
                'humor': 0.7
            },
            'expert_advisor': {
                'intelligence': 0.9,
                'confidence': 0.9,
                'professionalism': 0.9,
                'creativity': 0.6
            },
            'friendly_tutor': {
                'friendliness': 0.9,
                'patience': 0.9,
                'empathy': 0.8,
                'enthusiasm': 0.7
            }
        }

    def _load_behavior_patterns(self) -> Dict[BehaviorType, List[str]]:
        """Load behavior pattern templates."""
        return {
            BehaviorType.COMMUNICATION: [
                'clear_explanation', 'empathetic_response', 'constructive_feedback',
                'clarifying_questions', 'encouraging_support'
            ],
            BehaviorType.PROBLEM_SOLVING: [
                'systematic_approach', 'creative_solutions', 'analytical_thinking',
                'practical_suggestions', 'step_by_step_guidance'
            ],
            BehaviorType.SOCIAL: [
                'active_listening', 'relationship_building', 'conflict_resolution',
                'collaboration', 'social_awareness'
            ],
            BehaviorType.LEARNING: [
                'curiosity_driven', 'knowledge_seeking', 'adaptation',
                'feedback_integration', 'continuous_improvement'
            ],
            BehaviorType.ADAPTIVE: [
                'context_awareness', 'flexible_responses', 'personalization',
                'situational_adjustment', 'user_preference_learning'
            ]
        }

    def _calculate_consistency(self, current: str, previous: str) -> float:
        """Calculate consistency score between two responses."""
        # Simple text similarity - can be enhanced with semantic analysis
        current_words = set(current.lower().split())
        previous_words = set(previous.lower().split())

        if not current_words or not previous_words:
            return 0.5

        intersection = current_words & previous_words
        union = current_words | previous_words

        jaccard_similarity = len(intersection) / len(union)
        return jaccard_similarity

    def _adjust_for_consistency(self, response: str, behavior: Dict[str, Any]) -> str:
        """Adjust response to maintain consistency with previous behavior."""
        # Simple adjustment - can be enhanced with more sophisticated logic
        return response

    def _calculate_overall_consistency(self, response: str) -> float:
        """Calculate overall consistency score."""
        if not self.behavior_history:
            return 1.0

        recent_behaviors = self.behavior_history[-5:]
        consistency_scores = []

        for behavior in recent_behaviors:
            consistency = self._calculate_consistency(response, behavior['response'])
            consistency_scores.append(consistency)

        return sum(consistency_scores) / len(consistency_scores)

    def _calculate_adaptation_score(self, feedback: Dict[str, float]) -> float:
        """Calculate adaptation score based on feedback."""
        if not feedback:
            return 0.5

        # Calculate positive feedback ratio
        positive_feedback = sum(1 for score in feedback.values() if score > 0.6)
        total_feedback = len(feedback)

        if total_feedback == 0:
            return 0.5

        return positive_feedback / total_feedback

    def _calculate_engagement_score(self, response: str) -> float:
        """Calculate engagement score of response."""
        engagement_indicators = ['you', 'your', 'question', 'help', 'together', 'let\'s']
        indicator_count = sum(1 for indicator in engagement_indicators if indicator in response.lower())

        # Normalize by response length
        word_count = len(response.split())
        if word_count == 0:
            return 0.0

        engagement_density = indicator_count / word_count
        return min(engagement_density * 5, 1.0)  # Scale to 0-1

    def _calculate_personality_match(self, response: str) -> float:
        """Calculate how well response matches intended personality."""
        # This would ideally use more sophisticated NLP analysis
        # For now, use basic heuristics
        match_score = 0.5  # Base score

        # Check for friendliness indicators
        if self.profile.traits.get(PersonalityTrait.FRIENDLINESS, 0) > 0.7:
            friendly_words = ['happy', 'glad', 'pleasure', 'delighted']
            if any(word in response.lower() for word in friendly_words):
                match_score += 0.2

        # Check for creativity indicators
        if self.profile.traits.get(PersonalityTrait.CREATIVITY, 0) > 0.7:
            creative_words = ['imagine', 'creative', 'innovative', 'unique']
            if any(word in response.lower() for word in creative_words):
                match_score += 0.2

        return min(match_score, 1.0)

    def _calculate_response_variance(self, original: str, refined: str) -> float:
        """Calculate variance between original and refined response."""
        if not original or not refined:
            return 0.0

        original_words = set(original.lower().split())
        refined_words = set(refined.lower().split())

        if not original_words:
            return 1.0

        # Calculate Jaccard distance
        intersection = original_words & refined_words
        union = original_words | refined_words

        similarity = len(intersection) / len(union)
        variance = 1 - similarity

        return variance

    def _evolve_personality(self, feedback: Dict[str, float]):
        """Evolve personality traits based on feedback."""
        for trait, current_value in self.profile.traits.items():
            # Get feedback for this trait if available
            trait_feedback = feedback.get(trait.value)
            if trait_feedback is not None:
                # Apply learning with decay
                adjustment = (trait_feedback - 0.5) * self.learning_rate
                new_value = current_value + adjustment

                # Apply bounds
                new_value = max(0.0, min(1.0, new_value))

                # Apply decay factor for gradual change
                self.profile.traits[trait] = (self.profile.traits[trait] * self.decay_factor +
                                            new_value * (1 - self.decay_factor))

    def _calculate_trait_trends(self) -> Dict[str, float]:
        """Calculate trends in personality trait development."""
        if len(self.behavior_history) < 10:
            return {}

        # Compare recent vs earlier trait values
        recent_interactions = self.behavior_history[-10:]
        early_interactions = self.behavior_history[:10]

        trait_trends = {}

        for trait in PersonalityTrait:
            recent_avg = sum(
                interaction['profile_snapshot'].get(trait, 0.5)
                for interaction in recent_interactions
            ) / len(recent_interactions)

            early_avg = sum(
                interaction['profile_snapshot'].get(trait, 0.5)
                for interaction in early_interactions
            ) / len(early_interactions)

            trait_trends[trait.value] = recent_avg - early_avg

        return trait_trends

    def _get_dominant_traits(self) -> List[str]:
        """Get dominant personality traits."""
        traits = sorted(self.profile.traits.items(), key=lambda x: x[1], reverse=True)
        return [trait.value for trait, value in traits[:3]]

    def _analyze_adaptation_patterns(self) -> Dict[str, Any]:
        """Analyze adaptation patterns over time."""
        if not self.behavior_history:
            return {}

        # Calculate adaptation frequency
        adaptations = [interaction for interaction in self.behavior_history
                      if interaction['feedback']]

        return {
            'total_adaptations': len(adaptations),
            'adaptation_frequency': len(adaptations) / len(self.behavior_history),
            'most_adapted_trait': self._get_most_adapted_trait()
        }

    def _analyze_consistency_patterns(self) -> Dict[str, Any]:
        """Analyze consistency patterns in behavior."""
        if len(self.behavior_history) < 5:
            return {}

        # Calculate average consistency scores
        consistency_scores = []
        for i in range(1, len(self.behavior_history)):
            current = self.behavior_history[i]['response']
            previous = self.behavior_history[i-1]['response']
            consistency = self._calculate_consistency(current, previous)
            consistency_scores.append(consistency)

        return {
            'average_consistency': sum(consistency_scores) / len(consistency_scores),
            'consistency_variance': self._calculate_variance(consistency_scores)
        }

    def _get_most_adapted_trait(self) -> Optional[str]:
        """Get the trait that has been adapted most frequently."""
        if not self.behavior_history:
            return None

        trait_adaptations = {}
        for interaction in self.behavior_history:
            if interaction['feedback']:
                for trait in interaction['feedback'].keys():
                    trait_adaptations[trait] = trait_adaptations.get(trait, 0) + 1

        if not trait_adaptations:
            return None

        return max(trait_adaptations.items(), key=lambda x: x[1])[0]

    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values."""
        if not values:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance

    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text (simplified)."""
        positive_words = ['good', 'great', 'excellent', 'wonderful', 'fantastic', 'amazing']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'difficult', 'problem']

        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())

        total_words = len(text.split())
        if total_words == 0:
            return 0.0

        sentiment = (positive_count - negative_count) / total_words
        return max(-1.0, min(1.0, sentiment))

    def _analyze_complexity(self, text: str) -> float:
        """Analyze complexity of text."""
        words = text.split()
        if not words:
            return 0.0

        # Simple complexity metrics
        avg_word_length = sum(len(word) for word in words) / len(words)
        sentence_count = text.count('.') + text.count('!') + text.count('?')
        avg_sentence_length = len(words) / max(sentence_count, 1)

        # Combine metrics
        complexity = (avg_word_length / 10) + (min(avg_sentence_length / 20, 1))
        return min(complexity, 1.0)

    def _analyze_formality(self, text: str) -> float:
        """Analyze formality level of text."""
        formal_indicators = ['therefore', 'furthermore', 'consequently', 'moreover', 'nevertheless']
        informal_indicators = ['yeah', 'cool', 'awesome', 'totally', 'definitely']

        formal_count = sum(1 for indicator in formal_indicators if indicator in text.lower())
        informal_count = sum(1 for indicator in informal_indicators if indicator in text.lower())

        total_indicators = formal_count + informal_count
        if total_indicators == 0:
            return 0.5  # Neutral

        return formal_count / total_indicators

    def _analyze_creativity(self, text: str) -> float:
        """Analyze creativity in text."""
        creative_indicators = ['imagine', 'innovative', 'creative', 'unique', 'original', 'inspire']
        creative_count = sum(1 for indicator in creative_indicators if indicator in text.lower())

        # Normalize by text length
        word_count = len(text.split())
        if word_count == 0:
            return 0.0

        creativity_density = creative_count / word_count
        return min(creativity_density * 10, 1.0)

    def _log_interaction(self, user_input: str, response: str, metrics: BehaviorMetrics,
                        feedback: Dict[str, float]):
        """Log interaction for analysis."""
        log_entry = {
            'timestamp': time.time(),
            'agent_id': self.agent_id,
            'user_input': user_input,
            'response': response,
            'metrics': {
                'consistency': metrics.consistency_score,
                'adaptation': metrics.adaptation_score,
                'engagement': metrics.engagement_score,
                'personality_match': metrics.personality_match,
                'response_variance': metrics.response_variance
            },
            'feedback': feedback,
            'profile': {trait.value: value for trait, value in self.profile.traits.items()}
        }

        self.adaptation_log.append(log_entry)

        # Keep log manageable
        if len(self.adaptation_log) > 500:
            self.adaptation_log = self.adaptation_log[-500:]

# Example usage and testing
if __name__ == "__main__":
    # Create behavior refiner
    refiner = BehaviorRefiner("test_agent_1")

    # Test behavior refinement
    user_input = "I'm struggling with this problem"
    ai_response = "You should try harder."
    feedback = {'empathy': 0.9, 'friendliness': 0.8, 'patience': 0.7}

    refined_response, metrics = refiner.refine_behavior(user_input, ai_response, feedback=feedback)

    print("Original response:", ai_response)
    print("Refined response:", refined_response)
    print("Metrics:", f"Consistency: {metrics.consistency_score:.2f}, "
                     f"Engagement: {metrics.engagement_score:.2f}, "
                     f"Personality Match: {metrics.personality_match:.2f}")

    # Get personality insights
    insights = refiner.get_personality_insights()
    print("\nPersonality Insights:", json.dumps(insights, indent=2))