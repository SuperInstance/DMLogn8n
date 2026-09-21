#!/usr/bin/env python3
"""
Emotion Enhancer - More nuanced emotional responses for AI agents

This module enhances AI emotional intelligence, providing nuanced emotional
responses, empathy detection, and emotionally appropriate communication.
"""

import json
import time
import re
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict

class EmotionType(Enum):
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    LOVE = "love"
    OPTIMISM = "optimism"
    PESSIMISM = "pessimism"
    ANXIETY = "anxiety"
    RELIEF = "relief"
    PRIDE = "pride"
    GRATITUDE = "gratitude"
    EXCITEMENT = "excitement"
    CONFUSION = "confusion"
    FRUSTRATION = "frustration"
    DISAPPOINTMENT = "disappointment"
    SATISFACTION = "satisfaction"

class EmotionalTone(Enum):
    SUPPORTIVE = "supportive"
    EMPATHETIC = "empathetic"
    ENCOURAGING = "encouraging"
    COMFORTING = "comforting"
    ENTHUSIASTIC = "enthusiastic"
    CALM = "calm"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    RESPECTFUL = "respectful"
    UNDERSTANDING = "understanding"

class EmotionalIntensity(Enum):
    VERY_LOW = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9

@dataclass
class EmotionalState:
    """Represents an emotional state."""
    primary_emotion: EmotionType
    secondary_emotions: List[Tuple[EmotionType, float]]
    intensity: EmotionalIntensity
    confidence: float
    context: Dict[str, Any] = field(default_factory=dict)
    triggers: List[str] = field(default_factory=list)
    duration: float = 0.0

@dataclass
class EmotionalResponse:
    """Enhanced emotional response."""
    content: str
    emotional_tone: EmotionalTone
    empathy_level: float
    appropriateness_score: float
    emotional_indicators: List[str]
    supportive_elements: List[str]
    validation_phrases: List[str]

class EmotionEnhancer:
    """
    Advanced emotion enhancement system for AI agents.

    Features:
    - Emotion detection from text
    - Empathetic response generation
    - Emotional context awareness
    - Mood tracking and adaptation
    - Emotional intelligence metrics
    - Culturally sensitive emotional responses
    - Emotional support strategies
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.emotional_history = []
        self.user_emotional_profiles = defaultdict(dict)
        self.emotion_lexicon = self._load_emotion_lexicon()
        self.empathy_patterns = self._load_empathy_patterns()
        self.cultural_contexts = self._load_cultural_contexts()

        # Configuration
        self.empathy_threshold = 0.6
        self.emotional_intensity_threshold = 0.5
        self.context_sensitivity_enabled = True
        self.emotional_contagion_enabled = True

        # Emotional adaptation
        self.emotional_learning_rate = 0.1
        self.emotion_decay_rate = 0.95

        # Response templates
        self.emotional_responses = self._load_emotional_response_templates()
        self.support_phrases = self._load_support_phrases()

        # Logging
        self.logger = logging.getLogger(f"emotion_enhancer_{agent_id}")

    def enhance_emotional_response(self, user_input: str, current_response: str,
                                 user_context: Dict[str, Any] = None,
                                 agent_context: Dict[str, Any] = None) -> Tuple[str, EmotionalResponse]:
        """
        Enhance AI response with emotional intelligence and empathy.

        Args:
            user_input: User's input message
            current_response: AI's current response
            user_context: User's emotional context
            agent_context: Agent's emotional context

        Returns:
            Tuple of (enhanced_response, emotional_response_metadata)
        """
        # Detect user's emotional state
        user_emotion = self._detect_emotion(user_input, user_context)

        # Analyze current emotional appropriateness
        emotional_analysis = self._analyze_emotional_appropriateness(
            current_response, user_emotion, user_context
        )

        # Generate enhanced emotional response
        enhanced_response = self._generate_emotional_response(
            current_response, user_emotion, emotional_analysis, user_context, agent_context
        )

        # Create emotional response metadata
        emotional_response = self._create_emotional_response_metadata(
            enhanced_response, user_emotion, emotional_analysis
        )

        # Update emotional history
        self._update_emotional_history(user_input, enhanced_response, user_emotion)

        # Update user emotional profile
        self._update_user_emotional_profile(user_context, user_emotion)

        return enhanced_response, emotional_response

    def _detect_emotion(self, text: str, context: Dict[str, Any] = None) -> EmotionalState:
        """Detect emotional state from text and context."""
        # Initialize emotion scores
        emotion_scores = {emotion: 0.0 for emotion in EmotionType}

        # Text-based emotion detection
        text_emotions = self._detect_emotions_from_text(text)
        for emotion, score in text_emotions.items():
            emotion_scores[emotion] += score

        # Context-based emotion detection
        if context:
            context_emotions = self._detect_emotions_from_context(context)
            for emotion, score in context_emotions.items():
                emotion_scores[emotion] += score * 0.8  # Lower weight for context

        # Find primary emotion
        primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        primary_emotion_type = primary_emotion[0]
        primary_score = primary_emotion[1]

        # Find secondary emotions
        secondary_emotions = [
            (emotion, score) for emotion, score in emotion_scores.items()
            if emotion != primary_emotion_type and score > 0.2
        ]
        secondary_emotions.sort(key=lambda x: x[1], reverse=True)
        secondary_emotions = secondary_emotions[:3]  # Top 3 secondary

        # Determine intensity
        intensity = self._determine_emotional_intensity(primary_score, text)

        # Calculate confidence
        confidence = self._calculate_emotion_confidence(emotion_scores)

        # Identify triggers
        triggers = self._identify_emotional_triggers(text, context)

        return EmotionalState(
            primary_emotion=primary_emotion_type,
            secondary_emotions=secondary_emotions,
            intensity=intensity,
            confidence=confidence,
            context=context or {},
            triggers=triggers
        )

    def _detect_emotions_from_text(self, text: str) -> Dict[EmotionType, float]:
        """Detect emotions from text content."""
        emotion_scores = defaultdict(float)
        text_lower = text.lower()

        # Use emotion lexicon
        for word in text_lower.split():
            if word in self.emotion_lexicon:
                for emotion, score in self.emotion_lexicon[word].items():
                    emotion_scores[emotion] += score

        # Pattern-based detection
        patterns = {
            EmotionType.JOY: [r'\bhappy\b', r'\bexcited\b', r'\bgreat\b', r'\bwonderful\b'],
            EmotionType.SADNESS: [r'\bsad\b', r'\bdepressed\b', r'\bunhappy\b', r'\bdown\b'],
            EmotionType.ANGER: [r'\bangry\b', r'\bmad\b', r'\bfrustrated\b', r'\bannoyed\b'],
            EmotionType.FEAR: [r'\bscared\b', r'\bafraid\b', r'\bworried\b', r'\banxious\b'],
            EmotionType.SURPRISE: [r'\bsurprised\b', r'\bshocked\b', r'\bamazed\b', r'\bunexpected\b'],
            EmotionType.CONFUSION: [r'\bconfused\b', r'\bunclear\b', r'\bdon\'t understand\b', r'\buncertain\b'],
            EmotionType.EXCITEMENT: [r'\bexcited\b', r'\bcan\'t wait\b', r'\blooking forward\b', r'\bthrilled\b'],
            EmotionType.GRATITUDE: [r'\bthank\b', r'\bgrateful\b', r'\bappreciate\b', r'\bthanks\b']
        }

        for emotion, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, text_lower):
                    emotion_scores[emotion] += 0.3

        # Normalize scores
        max_score = max(emotion_scores.values()) if emotion_scores else 1.0
        if max_score > 0:
            for emotion in emotion_scores:
                emotion_scores[emotion] /= max_score

        return dict(emotion_scores)

    def _detect_emotions_from_context(self, context: Dict[str, Any]) -> Dict[EmotionType, float]:
        """Detect emotions from contextual information."""
        emotion_scores = defaultdict(float)

        # Previous emotional state
        if 'previous_emotion' in context:
            prev_emotion = context['previous_emotion']
            if isinstance(prev_emotion, EmotionType):
                emotion_scores[prev_emotion] += 0.4

        # Life events or situations
        if 'situation' in context:
            situation = context['situation'].lower()
            situation_emotions = {
                'achievement': {EmotionType.JOY: 0.7, EmotionType.PRIDE: 0.6},
                'loss': {EmotionType.SADNESS: 0.8, EmotionType.DISAPPOINTMENT: 0.6},
                'conflict': {EmotionType.ANGER: 0.7, EmotionType.FRUSTRATION: 0.6},
                'challenge': {EmotionType.ANXIETY: 0.6, EmotionType.DETERMINATION: 0.5},
                'celebration': {EmotionType.JOY: 0.8, EmotionType.EXCITEMENT: 0.7}
            }

            for key, emotions in situation_emotions.items():
                if key in situation:
                    for emotion, score in emotions.items():
                        emotion_scores[emotion] += score

        # Physical state indicators
        if 'physical_state' in context:
            physical = context['physical_state'].lower()
            if 'tired' in physical:
                emotion_scores[EmotionType.FATIGUE] = 0.6
            elif 'energetic' in physical:
                emotion_scores[EmotionType.JOY] = 0.4

        return dict(emotion_scores)

    def _determine_emotional_intensity(self, score: float, text: str) -> EmotionalIntensity:
        """Determine emotional intensity from score and text."""
        # Count intensity indicators
        text_lower = text.lower()
        intensity_indicators = {
            'very': 0.2, 'extremely': 0.3, 'incredibly': 0.3,
            'really': 0.1, 'quite': 0.1, 'absolutely': 0.2,
            'totally': 0.2, 'completely': 0.2
        }

        intensity_boost = sum(intensity_indicators.get(word, 0) for word in text_lower.split())
        total_score = min(score + intensity_boost, 1.0)

        if total_score >= 0.8:
            return EmotionalIntensity.VERY_HIGH
        elif total_score >= 0.6:
            return EmotionalIntensity.HIGH
        elif total_score >= 0.4:
            return EmotionalIntensity.MEDIUM
        elif total_score >= 0.2:
            return EmotionalIntensity.LOW
        else:
            return EmotionalIntensity.VERY_LOW

    def _calculate_emotion_confidence(self, emotion_scores: Dict[EmotionType, float]) -> float:
        """Calculate confidence in emotion detection."""
        if not emotion_scores:
            return 0.0

        scores = list(emotion_scores.values())
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)

        # Higher confidence when there's a clear winner
        confidence = (max_score - avg_score) / max_score if max_score > 0 else 0.0
        return min(confidence, 1.0)

    def _identify_emotional_triggers(self, text: str, context: Dict[str, Any]) -> List[str]:
        """Identify triggers for detected emotions."""
        triggers = []
        text_lower = text.lower()

        # Common emotional triggers
        trigger_patterns = {
            'work_stress': [r'\bwork\b', r'\bjob\b', r'\bboss\b', r'\bdeadline\b'],
            'relationship': [r'\brelationship\b', r'\bfamily\b', r'\bfriend\b', r'\bpartner\b'],
            'health': [r'\bhealth\b', r'\bsick\b', r'\bpain\b', r'\bdoctor\b'],
            'financial': [r'\bmoney\b', r'\bbill\b', r'\bcost\b', r'\bfinancial\b'],
            'achievement': [r'\bsuccess\b', r'\bachieve\b', r'\baccomplish\b', r'\bcompleted\b'],
            'failure': [r'\bfail\b', r'\bmistake\b', r'\berror\b', r'\bwrong\b']
        }

        for trigger, patterns in trigger_patterns.items():
            if any(re.search(pattern, text_lower) for pattern in patterns):
                triggers.append(trigger)

        # Context-based triggers
        if context:
            if 'recent_events' in context:
                triggers.extend(context['recent_events'])

        return triggers

    def _analyze_emotional_appropriateness(self, response: str, user_emotion: EmotionalState,
                                         user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze emotional appropriateness of current response."""
        analysis = {
            'current_tone': self._detect_response_tone(response),
            'empathy_score': self._calculate_empathy_score(response, user_emotion),
            'validation_score': self._calculate_validation_score(response, user_emotion),
            'appropriateness_score': 0.0,
            'recommendations': []
        }

        # Calculate overall appropriateness
        analysis['appropriateness_score'] = (
            analysis['empathy_score'] * 0.4 +
            analysis['validation_score'] * 0.4 +
            self._calculate_tone_appropriateness(analysis['current_tone'], user_emotion) * 0.2
        )

        # Generate recommendations
        if analysis['empathy_score'] < 0.6:
            analysis['recommendations'].append("Add more empathetic language")
        if analysis['validation_score'] < 0.6:
            analysis['recommendations'].append("Validate user's feelings")
        if analysis['appropriateness_score'] < 0.5:
            analysis['recommendations'].append("Adjust emotional tone to match user's state")

        return analysis

    def _generate_emotional_response(self, current_response: str, user_emotion: EmotionalState,
                                   emotional_analysis: Dict[str, Any], user_context: Dict[str, Any],
                                   agent_context: Dict[str, Any]) -> str:
        """Generate emotionally enhanced response."""
        enhanced_response = current_response

        # Add empathetic opening if needed
        if emotional_analysis['empathy_score'] < self.empathy_threshold:
            empathetic_opening = self._generate_empathetic_opening(user_emotion)
            enhanced_response = f"{empathetic_opening} {enhanced_response}"

        # Add validation phrases
        if emotional_analysis['validation_score'] < 0.6:
            validation_phrase = self._generate_validation_phrase(user_emotion)
            enhanced_response = f"{enhanced_response} {validation_phrase}"

        # Add supportive elements for negative emotions
        if user_emotion.primary_emotion in [EmotionType.SADNESS, EmotionType.ANGER, EmotionType.FEAR, EmotionType.ANXIETY]:
            support_element = self._generate_support_element(user_emotion)
            enhanced_response = f"{enhanced_response} {support_element}"

        # Adjust tone based on user emotion
        enhanced_response = self._adjust_emotional_tone(enhanced_response, user_emotion)

        # Add cultural sensitivity if enabled
        if self.context_sensitivity_enabled and user_context:
            enhanced_response = self._add_cultural_sensitivity(enhanced_response, user_context)

        return enhanced_response

    def _generate_empathetic_opening(self, user_emotion: EmotionalState) -> str:
        """Generate empathetic opening phrase."""
        openings = {
            EmotionType.SADNESS: [
                "I can see this is really difficult for you.",
                "It sounds like you're going through a tough time.",
                "I'm sorry you're feeling this way."
            ],
            EmotionType.ANGER: [
                "I understand your frustration.",
                "It makes sense that you're feeling angry.",
                "I can see why this would upset you."
            ],
            EmotionType.FEAR: [
                "That sounds really scary.",
                "I understand why you're feeling afraid.",
                "It's completely normal to feel scared in this situation."
            ],
            EmotionType.CONFUSION: [
                "I can see why this is confusing.",
                "That does sound complicated.",
                "I understand why you're having trouble with this."
            ],
            EmotionType.EXCITEMENT: [
                "That sounds wonderful!",
                "I can feel your excitement!",
                "How exciting for you!"
            ]
        }

        emotion_openings = openings.get(user_emotion.primary_emotion, [
            "I understand how you're feeling.",
            "I hear what you're saying.",
            "I appreciate you sharing this with me."
        ])

        return emotion_openings[0] if emotion_openings else "I understand."

    def _generate_validation_phrase(self, user_emotion: EmotionalState) -> str:
        """Generate validation phrase for user's emotions."""
        validations = {
            EmotionType.SADNESS: "Your feelings are completely valid.",
            EmotionType.ANGER: "You have every right to feel angry about this.",
            EmotionType.FEAR: "It's okay to feel scared.",
            EmotionType.CONFUSION: "It makes sense that you're confused.",
            EmotionType.JOY: "You deserve to feel this happy!",
            EmotionType.EXCITEMENT: "Your excitement is wonderful!"
        }

        return validations.get(user_emotion.primary_emotion, "Your feelings are valid.")

    def _generate_support_element(self, user_emotion: EmotionalState) -> str:
        """Generate supportive element for negative emotions."""
        support_elements = {
            EmotionType.SADNESS: [
                "Remember that difficult times don't last forever.",
                "Be gentle with yourself during this time.",
                "You're stronger than you might feel right now."
            ],
            EmotionType.ANGER: [
                "Taking a moment to breathe might help.",
                "Your anger is telling you something important.",
                "Finding healthy ways to express this anger is important."
            ],
            EmotionType.FEAR: [
                "You don't have to face this alone.",
                "Taking small steps can help overcome fear.",
                "Remember times when you've been brave before."
            ],
            EmotionType.ANXIETY: [
                "Deep breathing can help calm your mind.",
                "Focus on what you can control right now.",
                "This feeling will pass, even if it doesn't feel like it now."
            ]
        }

        elements = support_elements.get(user_emotion.primary_emotion, [
            "I'm here to support you.",
            "You've got this.",
            "Things will get better."
        ])

        return elements[0] if elements else "I'm here for you."

    def _adjust_emotional_tone(self, response: str, user_emotion: EmotionalState) -> str:
        """Adjust emotional tone of response to match user's state."""
        adjusted_response = response

        # Adjust for high intensity emotions
        if user_emotion.intensity in [EmotionalIntensity.HIGH, EmotionalIntensity.VERY_HIGH]:
            if user_emotion.primary_emotion in [EmotionType.SADNESS, EmotionType.FEAR]:
                adjusted_response = self._soften_tone(adjusted_response)
            elif user_emotion.primary_emotion == EmotionType.ANGER:
                adjusted_response = self._calm_tone(adjusted_response)

        # Adjust for low intensity emotions
        elif user_emotion.intensity in [EmotionalIntensity.LOW, EmotionalIntensity.VERY_LOW]:
            if user_emotion.primary_emotion == EmotionType.JOY:
                adjusted_response = self._enthuse_tone(adjusted_response)

        return adjusted_response

    def _soften_tone(self, response: str) -> str:
        """Soften the tone of the response."""
        softening_phrases = [
            "I want you to know that ",
            "Please remember that ",
            "It's important to ",
            "Gently "
        ]

        # Replace harsh words
        harsh_to_soft = {
            r'\bmust\b': 'might consider',
            r'\bshould\b': 'could',
            r'\bhave to\b': 'might want to',
            r'\bneed to\b': 'it could help to'
        }

        for harsh, soft in harsh_to_soft.items():
            response = re.sub(harsh, soft, response, flags=re.IGNORECASE)

        return response

    def _calm_tone(self, response: str) -> str:
        """Calm the tone of the response."""
        calming_phrases = [
            "Let's take a deep breath and ",
            "When you're ready, we can ",
            "There's no rush to ",
            "It's okay to take your time and "
        ]

        # Add calming element
        if len(response.split()) > 10:  # Only for longer responses
            response = f"{calming_phrases[0]} {response.lower()}"

        return response

    def _enthuse_tone(self, response: str) -> str:
        """Add enthusiasm to the response."""
        enthusiastic_words = [
            "wonderful", "fantastic", "great", "excellent", "amazing"
        ]

        # Replace neutral words with enthusiastic ones
        neutral_to_enthusiastic = {
            r'\bgood\b': 'wonderful',
            r'\bnice\b': 'fantastic',
            r'\bokay\b': 'great'
        }

        for neutral, enthusiastic in neutral_to_enthusiastic.items():
            response = re.sub(neutral, enthusiastic, response, flags=re.IGNORECASE)

        return response

    def _add_cultural_sensitivity(self, response: str, user_context: Dict[str, Any]) -> str:
        """Add cultural sensitivity to response."""
        # Simplified cultural sensitivity
        if user_context.get('cultural_background') == 'high_context':
            # Add indirect language for high-context cultures
            response = f"Perhaps {response.lower()}"
        elif user_context.get('cultural_background') == 'low_context':
            # Add directness for low-context cultures
            response = response.replace("might", "should")
            response = response.replace("perhaps", "definitely")

        return response

    def _detect_response_tone(self, response: str) -> EmotionalTone:
        """Detect emotional tone of response."""
        response_lower = response.lower()

        tone_indicators = {
            EmotionalTone.EMPATHETIC: ['understand', 'feel', 'sorry', 'empathize'],
            EmotionalTone.ENCOURAGING: ['can', 'will', 'able', 'capable', 'believe'],
            EmotionalTone.COMFORTING: ['okay', 'safe', 'here', 'support', 'care'],
            EmotionalTone.ENTHUSIASTIC: ['excited', 'wonderful', 'fantastic', 'great'],
            EmotionalTone.CALM: ['breathe', 'relax', 'peaceful', 'calm'],
            EmotionalTone.PROFESSIONAL: ['according', 'research', 'data', 'professional'],
            EmotionalTone.FRIENDLY: ['friend', 'buddy', 'pal', 'together']
        }

        tone_scores = defaultdict(int)
        for tone, indicators in tone_indicators.items():
            for indicator in indicators:
                if indicator in response_lower:
                    tone_scores[tone] += 1

        if tone_scores:
            return max(tone_scores.items(), key=lambda x: x[1])[0]
        else:
            return EmotionalTone.PROFESSIONAL

    def _calculate_empathy_score(self, response: str, user_emotion: EmotionalState) -> float:
        """Calculate empathy score of response."""
        empathy_indicators = [
            'understand', 'feel', 'sorry', 'empathize', 'relate',
            'imagine', 'sense', 'appreciate', 'recognize'
        ]

        response_lower = response.lower()
        empathy_count = sum(1 for indicator in empathy_indicators if indicator in response_lower)

        # Check for emotion-specific empathy
        emotion_specific_empathy = {
            EmotionType.SADNESS: ['sorry for your loss', 'difficult time'],
            EmotionType.ANGER: ['frustrating', 'understand your anger'],
            EmotionType.FEAR: ['scary', 'understand your fear'],
            EmotionType.JOY: ['happy for you', 'wonderful news']
        }

        specific_phrases = emotion_specific_empathy.get(user_emotion.primary_emotion, [])
        specific_count = sum(1 for phrase in specific_phrases if phrase in response_lower)

        # Calculate score
        base_score = (empathy_count * 0.1 + specific_count * 0.3)
        return min(base_score, 1.0)

    def _calculate_validation_score(self, response: str, user_emotion: EmotionalState) -> float:
        """Calculate validation score of response."""
        validation_indicators = [
            'valid', 'normal', 'okay', 'makes sense', 'understandable',
            'reasonable', 'justified', 'right to feel'
        ]

        response_lower = response.lower()
        validation_count = sum(1 for indicator in validation_indicators if indicator in response_lower)

        # Check for emotion-specific validation
        emotion_specific_validation = {
            EmotionType.SADNESS: ['okay to be sad', 'normal to feel this way'],
            EmotionType.ANGER: ['right to be angry', 'understandable frustration'],
            EmotionType.FEAR: ['normal to be scared', 'okay to feel afraid']
        }

        specific_phrases = emotion_specific_validation.get(user_emotion.primary_emotion, [])
        specific_count = sum(1 for phrase in specific_phrases if phrase in response_lower)

        # Calculate score
        base_score = (validation_count * 0.15 + specific_count * 0.4)
        return min(base_score, 1.0)

    def _calculate_tone_appropriateness(self, response_tone: EmotionalTone, user_emotion: EmotionalState) -> float:
        """Calculate how appropriate the response tone is for user emotion."""
        appropriate_tones = {
            EmotionType.SADNESS: [EmotionalTone.EMPATHETIC, EmotionalTone.COMFORTING, EmotionalTone.SUPPORTIVE],
            EmotionType.ANGER: [EmotionalTone.CALM, EmotionalTone.EMPATHETIC, EmotionalTone.UNDERSTANDING],
            EmotionType.FEAR: [EmotionalTone.COMFORTING, EmotionalTone.CALM, EmotionalTone.SUPPORTIVE],
            EmotionType.JOY: [EmotionalTone.ENTHUSIASTIC, EmotionalTone.FRIENDLY, EmotionalTone.ENCOURAGING],
            EmotionType.CONFUSION: [EmotionalTone.PATIENT, EmotionalTone.EMPATHETIC, EmotionalTone.SUPPORTIVE],
            EmotionType.EXCITEMENT: [EmotionalTone.ENTHUSIASTIC, EmotionalTone.FRIENDLY, EmotionalTone.ENCOURAGING]
        }

        expected_tones = appropriate_tones.get(user_emotion.primary_emotion, [EmotionalTone.PROFESSIONAL])
        return 1.0 if response_tone in expected_tones else 0.5

    def _create_emotional_response_metadata(self, response: str, user_emotion: EmotionalState,
                                          emotional_analysis: Dict[str, Any]) -> EmotionalResponse:
        """Create metadata for emotional response."""
        # Extract emotional indicators from response
        emotional_indicators = self._extract_emotional_indicators(response)

        # Extract supportive elements
        supportive_elements = self._extract_supportive_elements(response)

        # Extract validation phrases
        validation_phrases = self._extract_validation_phrases(response)

        return EmotionalResponse(
            content=response,
            emotional_tone=emotional_analysis['current_tone'],
            empathy_level=emotional_analysis['empathy_score'],
            appropriateness_score=emotional_analysis['appropriateness_score'],
            emotional_indicators=emotional_indicators,
            supportive_elements=supportive_elements,
            validation_phrases=validation_phrases
        )

    def _update_emotional_history(self, user_input: str, response: str, user_emotion: EmotionalState):
        """Update emotional interaction history."""
        interaction = {
            'timestamp': time.time(),
            'user_input': user_input,
            'response': response,
            'detected_emotion': user_emotion,
            'agent_id': self.agent_id
        }

        self.emotional_history.append(interaction)

        # Keep history manageable
        if len(self.emotional_history) > 1000:
            self.emotional_history = self.emotional_history[-1000:]

    def _update_user_emotional_profile(self, user_context: Dict[str, Any], user_emotion: EmotionalState):
        """Update user's emotional profile for better personalization."""
        if not user_context or 'user_id' not in user_context:
            return

        user_id = user_context['user_id']
        profile = self.user_emotional_profiles[user_id]

        # Update emotion frequency
        emotion_key = user_emotion.primary_emotion.value
        profile['emotion_frequency'] = profile.get('emotion_frequency', {})
        profile['emotion_frequency'][emotion_key] = profile['emotion_frequency'].get(emotion_key, 0) + 1

        # Update typical intensity
        profile['typical_intensity'] = profile.get('typical_intensity', EmotionalIntensity.MEDIUM)
        if user_emotion.intensity.value > profile['typical_intensity'].value:
            profile['typical_intensity'] = user_emotion.intensity

        # Update common triggers
        profile['common_triggers'] = profile.get('common_triggers', [])
        for trigger in user_emotion.triggers:
            if trigger not in profile['common_triggers']:
                profile['common_triggers'].append(trigger)

    def get_emotional_insights(self, user_id: str = None) -> Dict[str, Any]:
        """Get emotional intelligence insights."""
        insights = {
            'agent_id': self.agent_id,
            'total_interactions': len(self.emotional_history),
            'emotion_detection_accuracy': self._calculate_emotion_accuracy(),
            'empathy_performance': self._calculate_empathy_performance(),
            'common_emotions': self._get_common_emotions(),
            'emotional_patterns': self._analyze_emotional_patterns()
        }

        if user_id:
            user_profile = self.user_emotional_profiles.get(user_id, {})
            insights['user_profile'] = user_profile

        return insights

    # Helper methods for loading data
    def _load_emotion_lexicon(self) -> Dict[str, Dict[EmotionType, float]]:
        """Load emotion word lexicon."""
        return {
            'happy': {EmotionType.JOY: 0.9},
            'sad': {EmotionType.SADNESS: 0.9},
            'angry': {EmotionType.ANGER: 0.9},
            'scared': {EmotionType.FEAR: 0.8},
            'afraid': {EmotionType.FEAR: 0.8},
            'surprised': {EmotionType.SURPRISE: 0.8},
            'excited': {EmotionType.EXCITEMENT: 0.8},
            'confused': {EmotionType.CONFUSION: 0.8},
            'frustrated': {EmotionType.ANGER: 0.7, EmotionType.FRUSTRATION: 0.8},
            'grateful': {EmotionType.GRATITUDE: 0.9},
            'proud': {EmotionType.PRIDE: 0.8},
            'disappointed': {EmotionType.DISAPPOINTMENT: 0.8},
            'anxious': {EmotionType.ANXIETY: 0.8},
            'worried': {EmotionType.ANXIETY: 0.7},
            'relieved': {EmotionType.RELIEF: 0.8},
            'satisfied': {EmotionType.SATISFACTION: 0.8}
        }

    def _load_empathy_patterns(self) -> Dict[EmotionType, List[str]]:
        """Load empathy response patterns."""
        return {
            EmotionType.SADNESS: [
                "I'm sorry you're feeling this way",
                "That sounds really difficult",
                "I can understand why you feel sad"
            ],
            EmotionType.ANGER: [
                "I understand your frustration",
                "It makes sense that you're angry",
                "I can see why this would upset you"
            ],
            EmotionType.FEAR: [
                "That sounds really scary",
                "I understand why you're afraid",
                "It's okay to feel scared"
            ],
            EmotionType.JOY: [
                "That's wonderful!",
                "I'm so happy for you",
                "That sounds amazing"
            ]
        }

    def _load_cultural_contexts(self) -> Dict[str, Dict[str, Any]]:
        """Load cultural context information."""
        return {
            'high_context': {
                'communication_style': 'indirect',
                'emotional_expression': 'subtle',
                'support_preference': 'gentle'
            },
            'low_context': {
                'communication_style': 'direct',
                'emotional_expression': 'explicit',
                'support_preference': 'action-oriented'
            }
        }

    def _load_emotional_response_templates(self) -> Dict[EmotionType, List[str]]:
        """Load emotional response templates."""
        return {
            EmotionType.SADNESS: [
                "I'm here to support you through this difficult time.",
                "Your feelings are valid, and it's okay to feel sad.",
                "Remember that tough times don't last forever."
            ],
            EmotionType.ANGER: [
                "I understand your anger and I'm here to help.",
                "Your feelings are justified, and let's work through this.",
                "Taking a moment to breathe might help clarify things."
            ],
            EmotionType.FEAR: [
                "You don't have to face this fear alone.",
                "It's completely normal to feel scared in this situation.",
                "Together, we can find ways to manage this fear."
            ],
            EmotionType.JOY: [
                "Your happiness is wonderful to see!",
                "I'm so glad to hear you're feeling joyful.",
                "This moment of joy is well-deserved!"
            ]
        }

    def _load_support_phrases(self) -> Dict[EmotionType, List[str]]:
        """Load support phrases for different emotions."""
        return {
            EmotionType.SADNESS: [
                "Be gentle with yourself.",
                "This feeling will pass.",
                "You're stronger than you feel right now."
            ],
            EmotionType.ANGER: [
                "Your anger is valid.",
                "Expressing anger constructively is healthy.",
                "Your feelings matter."
            ],
            EmotionType.FEAR: [
                "You are safe.",
                "This feeling is temporary.",
                "You've overcome challenges before."
            ],
            EmotionType.CONFUSION: [
                "It's okay not to have all the answers.",
                "Confusion is part of learning.",
                "We can figure this out together."
            ]
        }

    def _extract_emotional_indicators(self, response: str) -> List[str]:
        """Extract emotional indicators from response."""
        indicators = []
        emotion_words = [
            'understand', 'feel', 'empathize', 'relate', 'appreciate',
            'happy', 'sad', 'angry', 'scared', 'excited', 'confused'
        ]

        for word in emotion_words:
            if word in response.lower():
                indicators.append(word)

        return indicators

    def _extract_supportive_elements(self, response: str) -> List[str]:
        """Extract supportive elements from response."""
        elements = []
        support_phrases = [
            'here for you', 'support', 'help', 'together', 'safe',
            'understand', 'care', 'listen'
        ]

        for phrase in support_phrases:
            if phrase in response.lower():
                elements.append(phrase)

        return elements

    def _extract_validation_phrases(self, response: str) -> List[str]:
        """Extract validation phrases from response."""
        phrases = []
        validation_words = [
            'valid', 'normal', 'okay', 'understandable', 'reasonable',
            'makes sense', 'right to feel', 'justified'
        ]

        for word in validation_words:
            if word in response.lower():
                phrases.append(word)

        return phrases

    def _calculate_emotion_accuracy(self) -> float:
        """Calculate emotion detection accuracy."""
        # Simplified - would be based on user feedback
        return 0.85

    def _calculate_empathy_performance(self) -> float:
        """Calculate empathy performance score."""
        if not self.emotional_history:
            return 0.0

        # Calculate average empathy score from recent interactions
        recent_interactions = self.emotional_history[-50:]
        empathy_scores = []

        for interaction in recent_interactions:
            # This would be calculated from actual response analysis
            empathy_scores.append(0.78)  # Placeholder

        return sum(empathy_scores) / len(empathy_scores) if empathy_scores else 0.0

    def _get_common_emotions(self) -> List[Dict[str, Any]]:
        """Get most common emotions detected."""
        emotion_counts = defaultdict(int)
        for interaction in self.emotional_history:
            emotion = interaction['detected_emotion'].primary_emotion
            emotion_counts[emotion] += 1

        common_emotions = [
            {'emotion': emotion.value, 'count': count}
            for emotion, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        return common_emotions

    def _analyze_emotional_patterns(self) -> Dict[str, Any]:
        """Analyze emotional patterns over time."""
        if len(self.emotional_history) < 10:
            return {'message': 'Insufficient data for pattern analysis'}

        # Time-based patterns
        recent_emotions = [interaction['detected_emotion'].primary_emotion
                          for interaction in self.emotional_history[-20:]]
        early_emotions = [interaction['detected_emotion'].primary_emotion
                         for interaction in self.emotional_history[:20]]

        recent_distribution = {emotion: recent_emotions.count(emotion) for emotion in set(recent_emotions)}
        early_distribution = {emotion: early_emotions.count(emotion) for emotion in set(early_emotions)}

        return {
            'recent_emotion_distribution': recent_distribution,
            'early_emotion_distribution': early_distribution,
            'emotional_trend': 'improving' if len(recent_emotions) > len(early_emotions) else 'stable'
        }

# Example usage and testing
if __name__ == "__main__":
    # Create emotion enhancer
    enhancer = EmotionEnhancer("test_agent_1")

    # Test emotional enhancement
    user_input = "I'm feeling really sad about what happened yesterday"
    ai_response = "That sounds difficult. I'm here to help."
    user_context = {'user_id': 'user123', 'situation': 'personal_loss'}

    enhanced_response, emotional_response = enhancer.enhance_emotional_response(
        user_input, ai_response, user_context
    )

    print("Original response:", ai_response)
    print("Enhanced response:", enhanced_response)
    print("Emotional tone:", emotional_response.emotional_tone.value)
    print("Empathy level:", emotional_response.empathy_level)
    print("Appropriateness score:", emotional_response.appropriateness_score)

    # Get emotional insights
    insights = enhancer.get_emotional_insights()
    print("\nEmotional Insights:", json.dumps(insights, indent=2))