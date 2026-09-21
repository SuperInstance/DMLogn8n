#!/usr/bin/env python3
"""
Advanced Emotional Engine for DMLogn8n AI Agents

This module implements sophisticated emotional intelligence and personality simulation
that enables AI agents to experience, express, and manage emotions in a human-like
manner. The system includes dynamic emotional states, personality traits, mood
regulation, and social-emotional intelligence.

Key Features:
- Multi-dimensional emotional state modeling
- Personality trait simulation (Big Five, OCEAN)
- Mood regulation and emotional homeostasis
- Emotional expression and recognition
- Social cognition and empathy
- Emotional memory and learning
- Stress and fatigue modeling
- Adaptive emotional responses
"""

import asyncio
import json
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
import time
import math
import random
from collections import deque, defaultdict
import copy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmotionType(Enum):
    """Basic emotion types based on Plutchik's model"""
    JOY = "joy"
    TRUST = "trust"
    FEAR = "fear"
    SURPRISE = "surprise"
    SADNESS = "sadness"
    DISGUST = "disgust"
    ANGER = "anger"
    ANTICIPATION = "anticipation"

class PersonalityTrait(Enum):
    """Big Five personality traits (OCEAN)"""
    OPENNESS = "openness"  # Openness to experience
    CONSCIENTIOUSNESS = "conscientiousness"  # Conscientiousness
    EXTRAVERSION = "extraversion"  # Extraversion
    AGREEABLENESS = "agreeableness"  # Agreeableness
    NEUROTICISM = "neuroticism"  # Neuroticism

class MoodState(Enum):
    """Overall mood states"""
    HAPPY = "happy"
    CALM = "calm"
    ENERGETIC = "energetic"
    ANXIOUS = "anxious"
    SAD = "sad"
    IRRITATED = "irritated"
    EXCITED = "excited"
    STRESSED = "stressed"

@dataclass
class EmotionalState:
    """Represents current emotional state"""
    emotions: Dict[EmotionType, float] = field(default_factory=dict)
    mood: MoodState = MoodState.CALM
    valence: float = 0.0  # Positive-negative dimension
    arousal: float = 0.0  # High-low activation dimension
    dominance: float = 0.0  # Control-submission dimension
    intensity: float = 0.0  # Overall emotional intensity
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Personality:
    """Represents personality traits"""
    traits: Dict[PersonalityTrait, float] = field(default_factory=dict)
    temperament: str = "balanced"  # choleric, sanguine, melancholic, phlegmatic
    coping_style: str = "adaptive"  # adaptive, maladaptive, avoidant
    emotional_regulation: float = 0.5  # Ability to regulate emotions
    expressiveness: float = 0.5  # Tendency to express emotions
    empathy: float = 0.5  # Ability to understand others' emotions

@dataclass
class EmotionalExperience:
    """Represents an emotional experience"""
    trigger: str
    emotion: EmotionType
    intensity: float
    context: Dict[str, Any]
    response: str
    outcome: str
    timestamp: datetime
    learned_associations: List[str] = field(default_factory=list)

class EmotionalNetwork(nn.Module):
    """Neural network for emotional processing"""

    def __init__(self, input_dim: int = 128, hidden_dim: int = 256, emotion_dim: int = 8):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.emotion_dim = emotion_dim

        # Input processing
        self.input_processor = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )

        # Emotional processing layers
        self.emotion_encoder = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, emotion_dim),
            nn.Tanh()
        )

        # Valence-arousal-dominance prediction
        self.vad_predictor = nn.Sequential(
            nn.Linear(hidden_dim + emotion_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 3),
            nn.Tanh()
        )

        # Emotional regulation
        self.regulation_network = nn.Sequential(
            nn.Linear(hidden_dim + emotion_dim + 3, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, emotion_dim),
            nn.Sigmoid()
        )

        # Personality modulation
        self.personality_modulation = nn.Sequential(
            nn.Linear(5, hidden_dim),  # 5 personality traits
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh()
        )

    def forward(self, inputs, personality_traits=None):
        """Process emotional inputs"""
        # Process inputs
        processed = self.input_processor(inputs)

        # Apply personality modulation if provided
        if personality_traits is not None:
            personality_effect = self.personality_modulation(personality_traits)
            processed = processed + personality_effect

        # Encode emotions
        emotions = self.emotion_encoder(processed)

        # Predict VAD values
        emotion_vad = torch.cat([processed, emotions], dim=-1)
        vad_values = self.vad_predictor(emotion_vad)

        # Apply emotional regulation
        regulation_input = torch.cat([processed, emotions, vad_values], dim=-1)
        regulated_emotions = self.regulation_network(regulation_input)

        return emotions, vad_values, regulated_emotions

class EmotionalMemory:
    """Memory system for emotional experiences"""

    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.experiences = deque(maxlen=capacity)
        self.emotional_associations = defaultdict(list)
        self.trauma_threshold = 0.8
        self.traumatic_experiences = []

    def add_experience(self, experience: EmotionalExperience):
        """Add an emotional experience to memory"""
        self.experiences.append(experience)

        # Create associations
        self.emotional_associations[experience.emotion].append(experience)

        # Check for traumatic experiences
        if experience.intensity >= self.trauma_threshold:
            self.traumatic_experiences.append(experience)

    def retrieve_similar_experiences(self, emotion: EmotionType,
                                  context: Dict[str, Any] = None) -> List[EmotionalExperience]:
        """Retrieve similar emotional experiences"""
        similar_experiences = self.emotional_associations[emotion]

        if context:
            # Filter by context similarity
            filtered = []
            for exp in similar_experiences:
                similarity = self._calculate_context_similarity(exp.context, context)
                if similarity > 0.5:
                    filtered.append((exp, similarity))

            # Sort by similarity
            filtered.sort(key=lambda x: x[1], reverse=True)
            return [exp for exp, _ in filtered[:10]]

        return list(similar_experiences)[-10:]  # Last 10 experiences

    def _calculate_context_similarity(self, context1: Dict, context2: Dict) -> float:
        """Calculate similarity between two contexts"""
        if not context1 or not context2:
            return 0.0

        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0

        similarity_sum = 0.0
        for key in common_keys:
            if context1[key] == context2[key]:
                similarity_sum += 1.0
            elif isinstance(context1[key], (int, float)) and isinstance(context2[key], (int, float)):
                # Numerical similarity
                max_val = max(abs(context1[key]), abs(context2[key]))
                if max_val > 0:
                    similarity_sum += 1.0 - (abs(context1[key] - context2[key]) / max_val)

        return similarity_sum / len(common_keys)

class MoodRegulator:
    """System for regulating mood and emotional homeostasis"""

    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        self.homeostasis_target = 0.0  # Target emotional balance
        self.regulation_strategies = {
            'cognitive_reappraisal': self._cognitive_reappraisal,
            'distraction': self._distraction,
            'problem_solving': self._problem_solving,
            'social_support': self._social_support,
            'acceptance': self._acceptance
        }
        self.current_strategy = None
        self.regulation_history = []

    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            'regulation_threshold': 0.7,  # When to start regulation
            'regulation_strength': 0.3,  # How much to regulate
            'strategy_preference': 'cognitive_reappraisal',
            'max_regulation_attempts': 3
        }

    def should_regulate(self, emotional_state: EmotionalState) -> bool:
        """Check if emotional regulation is needed"""
        return (abs(emotional_state.valence) > self.config['regulation_threshold'] or
                abs(emotional_state.arousal) > self.config['regulation_threshold'] or
                emotional_state.intensity > self.config['regulation_threshold'])

    def regulate_emotion(self, emotional_state: EmotionalState,
                        personality: Personality) -> EmotionalState:
        """Apply emotional regulation"""
        if not self.should_regulate(emotional_state):
            return emotional_state

        # Select regulation strategy based on personality
        strategy_name = self._select_strategy(personality)
        self.current_strategy = strategy_name

        # Apply regulation
        regulated_state = self.regulation_strategies[strategy_name](emotional_state, personality)

        # Record regulation attempt
        self.regulation_history.append({
            'strategy': strategy_name,
            'before': copy.deepcopy(emotional_state),
            'after': copy.deepcopy(regulated_state),
            'timestamp': datetime.now()
        })

        return regulated_state

    def _select_strategy(self, personality: Personality) -> str:
        """Select regulation strategy based on personality"""
        # Strategy selection based on personality traits
        if personality.traits.get(PersonalityTrait.NEUROTICISM, 0.5) > 0.7:
            return 'acceptance'
        elif personality.traits.get(PersonalityTrait.CONSCIENTIOUSNESS, 0.5) > 0.7:
            return 'problem_solving'
        elif personality.traits.get(PersonalityTrait.EXTRAVERSION, 0.5) > 0.7:
            return 'social_support'
        elif personality.traits.get(PersonalityTrait.OPENNESS, 0.5) > 0.7:
            return 'cognitive_reappraisal'
        else:
            return self.config['strategy_preference']

    def _cognitive_reappraisal(self, state: EmotionalState, personality: Personality) -> EmotionalState:
        """Cognitive reappraisal strategy"""
        regulated = copy.deepcopy(state)

        # Reduce intensity and adjust valence
        regulation_factor = self.config['regulation_strength']
        regulated.intensity *= (1 - regulation_factor)
        regulated.valence *= (1 - regulation_factor * 0.5)
        regulated.arousal *= (1 - regulation_factor * 0.3)

        return regulated

    def _distraction(self, state: EmotionalState, personality: Personality) -> EmotionalState:
        """Distraction strategy"""
        regulated = copy.deepcopy(state)

        # Shift attention away from emotion
        regulation_factor = self.config['regulation_strength']
        for emotion in regulated.emotions:
            regulated.emotions[emotion] *= (1 - regulation_factor)

        regulated.intensity *= (1 - regulation_factor * 0.8)

        return regulated

    def _problem_solving(self, state: EmotionalState, personality: Personality) -> EmotionalState:
        """Problem-solving strategy"""
        regulated = copy.deepcopy(state)

        # Focus on solving the problem causing the emotion
        regulation_factor = self.config['regulation_strength']
        regulated.arousal *= (1 - regulation_factor * 0.2)  # Reduce arousal slightly
        regulated.dominance *= (1 + regulation_factor * 0.3)  # Increase control

        return regulated

    def _social_support(self, state: EmotionalState, personality: Personality) -> EmotionalState:
        """Social support strategy"""
        regulated = copy.deepcopy(state)

        # Seeking social connection
        regulation_factor = self.config['regulation_strength']
        regulated.valence *= (1 + regulation_factor * 0.2)  # Improve mood
        regulated.intensity *= (1 - regulation_factor * 0.4)

        return regulated

    def _acceptance(self, state: EmotionalState, personality: Personality) -> EmotionalState:
        """Acceptance strategy"""
        regulated = copy.deepcopy(state)

        # Accept the emotion without judgment
        regulation_factor = self.config['regulation_strength']
        regulated.arousal *= (1 - regulation_factor * 0.6)  # Calm arousal
        # Keep valence and intensity as they are

        return regulated

class EmpathyEngine:
    """Engine for understanding and responding to others' emotions"""

    def __init__(self):
        self.emotion_recognition_model = None  # Would be trained model
        self.perspective_taking_ability = 0.5
        self.emotional_contagion_susceptibility = 0.3
        self.cultural_emotion_understanding = {}

    def recognize_emotions(self, input_data: Dict[str, Any]) -> Dict[EmotionType, float]:
        """Recognize emotions from input (text, facial expressions, etc.)"""
        # Simplified emotion recognition
        emotions = {}

        # Text-based emotion recognition
        if 'text' in input_data:
            text = input_data['text'].lower()

            # Simple keyword-based emotion detection
            emotion_keywords = {
                EmotionType.JOY: ['happy', 'joy', 'excited', 'glad', 'wonderful'],
                EmotionType.SADNESS: ['sad', 'unhappy', 'depressed', 'melancholy', 'blue'],
                EmotionType.ANGER: ['angry', 'mad', 'furious', 'irritated', 'annoyed'],
                EmotionType.FEAR: ['afraid', 'scared', 'terrified', 'anxious', 'worried'],
                EmotionType.SURPRISE: ['surprised', 'amazed', 'shocked', 'astonished'],
                EmotionType.DISGUST: ['disgusted', 'revolted', 'repulsed'],
                EmotionType.TRUST: ['trust', 'confident', 'secure'],
                EmotionType.ANTICIPATION: ['excited', 'eager', 'looking forward', 'expecting']
            }

            for emotion, keywords in emotion_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text) / len(keywords)
                emotions[emotion] = min(score, 1.0)

        return emotions

    def simulate_empathy(self, other_emotions: Dict[EmotionType, float],
                        context: Dict[str, Any]) -> Dict[EmotionType, float]:
        """Simulate empathic response to others' emotions"""
        empathic_emotions = {}

        # Emotional contagion
        for emotion, intensity in other_emotions.items():
            contagion_strength = intensity * self.emotional_contagion_susceptibility
            empathic_emotions[emotion] = contagion_strength

        # Perspective taking - consider how you would feel in their situation
        if self.perspective_taking_ability > 0.5:
            # Add complementary emotions based on context
            if EmotionType.SADNESS in other_emotions and other_emotions[EmotionType.SADNESS] > 0.5:
                empathic_emotions[EmotionType.TRUST] = 0.3  # Offering support

            if EmotionType.FEAR in other_emotions and other_emotions[EmotionType.FEAR] > 0.5:
                empathic_emotions[EmotionType.TRUST] = 0.4  # Offering safety

        return empathic_emotions

class EmotionalEngine:
    """
    Advanced Emotional Engine for AI Agents

    This class implements a comprehensive emotional system that enables AI agents
    to experience, express, and manage emotions in a human-like manner.
    """

    def __init__(self, agent_id: str, config: Optional[Dict] = None):
        self.agent_id = agent_id
        self.config = config or self._default_config()

        # Core components
        self.emotional_network = EmotionalNetwork()
        self.emotional_memory = EmotionalMemory()
        self.mood_regulator = MoodRegulator(self.config.get('mood_regulation', {}))
        self.empathy_engine = EmpathyEngine()

        # Current state
        self.current_emotional_state = EmotionalState()
        self.personality = self._create_default_personality()

        # History and tracking
        self.emotional_history = deque(maxlen=1000)
        self.mood_history = deque(maxlen=100)
        self.stress_level = 0.0
        self.fatigue_level = 0.0

        # Learning and adaptation
        self.emotional_learning_rate = 0.1
        self.personality_adaptation_rate = 0.01

        # Performance metrics
        self.metrics = {
            'total_emotional_experiences': 0,
            'regulation_attempts': 0,
            'successful_regulations': 0,
            'average_emotional_intensity': 0.0,
            'emotional_volatility': 0.0,
            'empathy_accuracy': 0.0,
            'stress_events': 0
        }

        # Threading
        self.processing_lock = threading.Lock()
        self.background_tasks = set()

        logger.info(f"Emotional Engine initialized for agent {agent_id}")

    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            'emotional_decay_rate': 0.1,
            'stress_threshold': 0.8,
            'fatigue_threshold': 0.7,
            'max_emotional_intensity': 1.0,
            'mood_update_frequency': 60,  # seconds
            'enable_learning': True,
            'enable_personality_adaptation': True,
            'cultural_context': 'western'
        }

    def _create_default_personality(self) -> Personality:
        """Create default personality"""
        return Personality(
            traits={
                PersonalityTrait.OPENNESS: 0.5,
                PersonalityTrait.CONSCIENTIOUSNESS: 0.5,
                PersonalityTrait.EXTRAVERSION: 0.5,
                PersonalityTrait.AGREEABLENESS: 0.5,
                PersonalityTrait.NEUROTICISM: 0.5
            },
            temperament="balanced",
            coping_style="adaptive",
            emotional_regulation=0.5,
            expressiveness=0.5,
            empathy=0.5
        )

    def process_emotional_stimulus(self, stimulus: Dict[str, Any]) -> EmotionalState:
        """Process an emotional stimulus and update emotional state"""
        with self.processing_lock:
            # Extract features from stimulus
            features = self._extract_stimulus_features(stimulus)

            # Process through neural network
            if isinstance(features, np.ndarray):
                features_tensor = torch.FloatTensor(features).unsqueeze(0)
            else:
                features_tensor = torch.zeros(1, 128)  # Default input

            personality_tensor = torch.FloatTensor([
                self.personality.traits[PersonalityTrait.OPENNESS],
                self.personality.traits[PersonalityTrait.CONSCIENTIOUSNESS],
                self.personality.traits[PersonalityTrait.EXTRAVERSION],
                self.personality.traits[PersonalityTrait.AGREEABLENESS],
                self.personality.traits[PersonalityTrait.NEUROTICISM]
            ]).unsqueeze(0)

            emotions_tensor, vad_tensor, regulated_tensor = self.emotional_network(
                features_tensor, personality_tensor
            )

            # Convert tensors to emotions
            new_emotions = self._tensor_to_emotions(emotions_tensor[0])
            vad_values = vad_tensor[0].tolist()
            regulated_emotions = self._tensor_to_emotions(regulated_tensor[0])

            # Update emotional state
            self._update_emotional_state(new_emotions, vad_values, regulated_emotions)

            # Apply mood regulation if needed
            if self.mood_regulator.should_regulate(self.current_emotional_state):
                self.current_emotional_state = self.mood_regulator.regulate_emotion(
                    self.current_emotional_state, self.personality
                )
                self.metrics['regulation_attempts'] += 1

            # Update stress and fatigue
            self._update_stress_fatigue(stimulus)

            # Store emotional experience
            self._store_emotional_experience(stimulus, new_emotions)

            # Add to history
            self.emotional_history.append(copy.deepcopy(self.current_emotional_state))
            self._update_mood_history()

            # Update metrics
            self._update_metrics()

            return copy.deepcopy(self.current_emotional_state)

    def _extract_stimulus_features(self, stimulus: Dict[str, Any]) -> np.ndarray:
        """Extract features from emotional stimulus"""
        features = np.zeros(128)  # Default feature vector

        # Text features
        if 'text' in stimulus:
            text = stimulus['text']
            # Simple text encoding (in practice, would use proper embeddings)
            text_hash = hash(text) % 1000
            features[:32] = np.array([float(c) / 255.0 for c in text[:32]] + [0.0] * (32 - min(32, len(text))))

        # Emotional valence features
        if 'valence' in stimulus:
            features[32] = stimulus['valence']

        # Context features
        if 'context' in stimulus:
            context_features = list(stimulus['context'].values())
            for i, value in enumerate(context_features[:10]):
                if isinstance(value, (int, float)):
                    features[33 + i] = value

        return features

    def _tensor_to_emotions(self, tensor: torch.Tensor) -> Dict[EmotionType, float]:
        """Convert neural network output to emotion dictionary"""
        emotion_values = tensor.tolist()
        emotions = {}

        emotion_types = list(EmotionType)
        for i, emotion_type in enumerate(emotion_types):
            if i < len(emotion_values):
                emotions[emotion_type] = max(0.0, min(1.0, (emotion_values[i] + 1.0) / 2.0))

        return emotions

    def _update_emotional_state(self, new_emotions: Dict[EmotionType, float],
                              vad_values: List[float], regulated_emotions: Dict[EmotionType, float]):
        """Update current emotional state"""
        # Blend new emotions with existing state
        alpha = self.emotional_learning_rate

        for emotion_type in EmotionType:
            if emotion_type in new_emotions:
                current_val = self.current_emotional_state.emotions.get(emotion_type, 0.0)
                new_val = new_emotions[emotion_type]
                regulated_val = regulated_emotions.get(emotion_type, new_val)

                # Blend with regulation influence
                blended_val = current_val * (1 - alpha) + regulated_val * alpha
                self.current_emotional_state.emotions[emotion_type] = blended_val

        # Update VAD values
        self.current_emotional_state.valence = vad_values[0]
        self.current_emotional_state.arousal = vad_values[1]
        self.current_emotional_state.dominance = vad_values[2]

        # Calculate overall intensity
        self.current_emotional_state.intensity = np.mean(list(self.current_emotional_state.emotions.values()))

        # Update mood
        self.current_emotional_state.mood = self._determine_mood()

        # Update timestamp
        self.current_emotional_state.timestamp = datetime.now()

    def _determine_mood(self) -> MoodState:
        """Determine current mood based on emotional state"""
        emotions = self.current_emotional_state.emotions
        valence = self.current_emotional_state.valence
        arousal = self.current_emotional_state.arousal

        # Mood determination logic
        if emotions.get(EmotionType.JOY, 0) > 0.6:
            if arousal > 0.5:
                return MoodState.ENERGETIC
            else:
                return MoodState.HAPPY
        elif emotions.get(EmotionType.FEAR, 0) > 0.6:
            if arousal > 0.7:
                return MoodState.ANXIOUS
            else:
                return MoodState.STRESSED
        elif emotions.get(EmotionType.ANGER, 0) > 0.6:
            return MoodState.IRRITATED
        elif emotions.get(EmotionType.SADNESS, 0) > 0.6:
            return MoodState.SAD
        elif emotions.get(EmotionType.ANTICIPATION, 0) > 0.6:
            return MoodState.EXCITED
        elif valence > 0.3 and arousal < 0.3:
            return MoodState.CALM
        else:
            return MoodState.CALM

    def _update_stress_fatigue(self, stimulus: Dict[str, Any]):
        """Update stress and fatigue levels"""
        # Stress increases with high arousal negative emotions
        negative_arousal = (
            self.current_emotional_state.emotions.get(EmotionType.FEAR, 0) +
            self.current_emotional_state.emotions.get(EmotionType.ANGER, 0) +
            self.current_emotional_state.emotions.get(EmotionType.SADNESS, 0)
        )

        stress_increase = negative_arousal * self.current_emotional_state.arousal * 0.1
        self.stress_level = min(1.0, self.stress_level + stress_increase)

        # Fatigue increases with high emotional intensity over time
        fatigue_increase = self.current_emotional_state.intensity * 0.05
        self.fatigue_level = min(1.0, self.fatigue_level + fatigue_increase)

        # Check for stress events
        if self.stress_level > self.config['stress_threshold']:
            self.metrics['stress_events'] += 1

        # Natural recovery
        self.stress_level *= 0.98  # Slow decay
        self.fatigue_level *= 0.99  # Slow decay

    def _store_emotional_experience(self, stimulus: Dict[str, Any], emotions: Dict[EmotionType, float]):
        """Store emotional experience in memory"""
        # Find dominant emotion
        dominant_emotion = max(emotions.items(), key=lambda x: x[1]) if emotions else (EmotionType.JOY, 0.0)

        experience = EmotionalExperience(
            trigger=str(stimulus.get('trigger', 'unknown')),
            emotion=dominant_emotion[0],
            intensity=dominant_emotion[1],
            context=stimulus.get('context', {}),
            response=str(stimulus.get('response', '')),
            outcome=str(stimulus.get('outcome', '')),
            timestamp=datetime.now()
        )

        self.emotional_memory.add_experience(experience)
        self.metrics['total_emotional_experiences'] += 1

    def _update_mood_history(self):
        """Update mood history"""
        self.mood_history.append({
            'mood': self.current_emotional_state.mood,
            'valence': self.current_emotional_state.valence,
            'arousal': self.current_emotional_state.arousal,
            'intensity': self.current_emotional_state.intensity,
            'timestamp': datetime.now()
        })

    def _update_metrics(self):
        """Update performance metrics"""
        if self.emotional_history:
            # Average emotional intensity
            intensities = [state.intensity for state in self.emotional_history]
            self.metrics['average_emotional_intensity'] = np.mean(intensities)

            # Emotional volatility
            if len(intensities) > 1:
                self.metrics['emotional_volatility'] = np.std(intensities)

        # Regulation success rate
        if self.metrics['regulation_attempts'] > 0:
            success_rate = 1.0 - (self.stress_level + self.fatigue_level) / 2
            self.metrics['successful_regulations'] = int(
                self.metrics['regulation_attempts'] * success_rate
            )

    def express_emotion(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate emotional expression"""
        if not self.personality.expressiveness > 0.3:
            return {'expression': 'neutral', 'confidence': 0.9}

        # Determine expression based on current emotional state
        dominant_emotion = max(
            self.current_emotional_state.emotions.items(),
            key=lambda x: x[1]
        ) if self.current_emotional_state.emotions else (EmotionType.JOY, 0.0)

        # Generate expression based on personality and emotion
        expression = self._generate_emotional_expression(dominant_emotion[0], dominant_emotion[1])

        return {
            'expression': expression,
            'emotion': dominant_emotion[0].value,
            'intensity': dominant_emotion[1],
            'confidence': self.personality.expressiveness,
            'mood': self.current_emotional_state.mood.value,
            'valence': self.current_emotional_state.valence,
            'arousal': self.current_emotional_state.arousal
        }

    def _generate_emotional_expression(self, emotion: EmotionType, intensity: float) -> str:
        """Generate emotional expression based on personality"""
        expressions = {
            EmotionType.JOY: ["happy", "pleased", "delighted", "excited", "joyful"],
            EmotionType.TRUST: ["trusting", "confident", "secure", "reassured"],
            EmotionType.FEAR: ["afraid", "scared", "worried", "anxious", "concerned"],
            EmotionType.SURPRISE: ["surprised", "amazed", "astonished", "shocked"],
            EmotionType.SADNESS: ["sad", "unhappy", "melancholy", "downcast"],
            EmotionType.DISGUST: ["disgusted", "repulsed", "revolted"],
            EmotionType.ANGER: ["angry", "irritated", "annoyed", "frustrated", "upset"],
            EmotionType.ANTICIPATION: ["eager", "expectant", "looking forward", "hopeful"]
        }

        base_expressions = expressions.get(emotion, ["neutral"])

        # Modulate based on personality
        if self.personality.expressiveness > 0.7:
            # High expressiveness - more intense expressions
            if intensity > 0.7:
                return f"very {random.choice(base_expressions)}"
            else:
                return random.choice(base_expressions)
        else:
            # Low expressiveness - more subtle expressions
            return f"somewhat {random.choice(base_expressions)}"

    def recognize_emotions_in_others(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Recognize emotions in others using empathy engine"""
        recognized_emotions = self.empathy_engine.recognize_emotions(input_data)

        # Generate empathic response
        empathic_emotions = self.empathy_engine.simulate_empathy(recognized_emotions, {})

        return {
            'recognized_emotions': {e.value: i for e, i in recognized_emotions.items()},
            'empathic_response': {e.value: i for e, i in empathic_emotions.items()},
            'confidence': self.personality.empathy
        }

    def adapt_personality(self, feedback: Dict[str, float]):
        """Adapt personality based on feedback"""
        if not self.config.get('enable_personality_adaptation', True):
            return

        # Simple personality adaptation based on feedback
        if 'emotional_stability' in feedback:
            target = feedback['emotional_stability']
            current = 1.0 - self.personality.traits[PersonalityTrait.NEUROTICISM]
            adjustment = (target - current) * self.personality_adaptation_rate
            self.personality.traits[PersonalityTrait.NEUROTICISM] -= adjustment

        if 'social_engagement' in feedback:
            target = feedback['social_engagement']
            current = self.personality.traits[PersonalityTrait.EXTRAVERSION]
            adjustment = (target - current) * self.personality_adaptation_rate
            self.personality.traits[PersonalityTrait.EXTRAVERSION] += adjustment

        # Ensure traits stay within valid range
        for trait in PersonalityTrait:
            self.personality.traits[trait] = max(0.0, min(1.0, self.personality.traits[trait]))

    def decay_emotions(self):
        """Apply emotional decay over time"""
        decay_rate = self.config['emotional_decay_rate']

        for emotion_type in EmotionType:
            if emotion_type in self.current_emotional_state.emotions:
                self.current_emotional_state.emotions[emotion_type] *= (1 - decay_rate)

        # Update intensity and mood
        self.current_emotional_state.intensity = np.mean(list(self.current_emotional_state.emotions.values()))
        self.current_emotional_state.mood = self._determine_mood()
        self.current_emotional_state.timestamp = datetime.now()

    def get_emotional_summary(self) -> Dict[str, Any]:
        """Get comprehensive emotional state summary"""
        return {
            'agent_id': self.agent_id,
            'timestamp': datetime.now().isoformat(),
            'current_emotions': {e.value: i for e, i in self.current_emotional_state.emotions.items()},
            'current_mood': self.current_emotional_state.mood.value,
            'vad_values': {
                'valence': self.current_emotional_state.valence,
                'arousal': self.current_emotional_state.arousal,
                'dominance': self.current_emotional_state.dominance
            },
            'intensity': self.current_emotional_state.intensity,
            'stress_level': self.stress_level,
            'fatigue_level': self.fatigue_level,
            'personality': {
                trait.value: value for trait, value in self.personality.traits.items()
            },
            'personality_details': {
                'temperament': self.personality.temperament,
                'coping_style': self.personality.coping_style,
                'emotional_regulation': self.personality.emotional_regulation,
                'expressiveness': self.personality.expressiveness,
                'empathy': self.personality.empathy
            },
            'metrics': self.metrics,
            'regulation_history_length': len(self.mood_regulator.regulation_history),
            'emotional_experiences_count': len(self.emotional_memory.experiences)
        }

    def save_emotional_state(self, filepath: str):
        """Save emotional state to file"""
        state = {
            'agent_id': self.agent_id,
            'config': self.config,
            'current_emotional_state': {
                'emotions': {e.value: i for e, i in self.current_emotional_state.emotions.items()},
                'mood': self.current_emotional_state.mood.value,
                'valence': self.current_emotional_state.valence,
                'arousal': self.current_emotional_state.arousal,
                'dominance': self.current_emotional_state.dominance,
                'intensity': self.current_emotional_state.intensity,
                'timestamp': self.current_emotional_state.timestamp.isoformat()
            },
            'personality': {
                'traits': {trait.value: value for trait, value in self.personality.traits.items()},
                'temperament': self.personality.temperament,
                'coping_style': self.personality.coping_style,
                'emotional_regulation': self.personality.emotional_regulation,
                'expressiveness': self.personality.expressiveness,
                'empathy': self.personality.empathy
            },
            'stress_level': self.stress_level,
            'fatigue_level': self.fatigue_level,
            'metrics': self.metrics,
            'timestamp': datetime.now().isoformat()
        }

        with open(filepath, 'wb') as f:
            import pickle
            pickle.dump(state, f)

        logger.info(f"Emotional state saved to {filepath}")

    def load_emotional_state(self, filepath: str):
        """Load emotional state from file"""
        try:
            with open(filepath, 'rb') as f:
                import pickle
                state = pickle.load(f)

            self.agent_id = state['agent_id']
            self.config = state['config']

            # Restore emotional state
            es = state['current_emotional_state']
            self.current_emotional_state = EmotionalState(
                emotions={EmotionType(k): v for k, v in es['emotions'].items()},
                mood=MoodState(es['mood']),
                valence=es['valence'],
                arousal=es['arousal'],
                dominance=es['dominance'],
                intensity=es['intensity'],
                timestamp=datetime.fromisoformat(es['timestamp'])
            )

            # Restore personality
            p = state['personality']
            self.personality = Personality(
                traits={PersonalityTrait(k): v for k, v in p['traits'].items()},
                temperament=p['temperament'],
                coping_style=p['coping_style'],
                emotional_regulation=p['emotional_regulation'],
                expressiveness=p['expressiveness'],
                empathy=p['empathy']
            )

            self.stress_level = state['stress_level']
            self.fatigue_level = state['fatigue_level']
            self.metrics = state['metrics']

            logger.info(f"Emotional state loaded from {filepath}")

        except Exception as e:
            logger.error(f"Error loading emotional state: {e}")

    async def start_emotional_decay(self):
        """Start background emotional decay process"""
        async def decay_loop():
            while True:
                try:
                    self.decay_emotions()
                    await asyncio.sleep(60)  # Decay every minute
                except Exception as e:
                    logger.error(f"Error in emotional decay: {e}")
                    await asyncio.sleep(60)

        task = asyncio.create_task(decay_loop())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

        logger.info("Started emotional decay process")

    def stop_background_tasks(self):
        """Stop background tasks"""
        for task in self.background_tasks:
            task.cancel()
        self.background_tasks.clear()
        logger.info("Stopped emotional engine background tasks")

# Utility functions for integration
async def create_emotional_engine(agent_id: str, config: Optional[Dict] = None) -> EmotionalEngine:
    """Factory function to create and initialize emotional engine"""
    engine = EmotionalEngine(agent_id, config)
    await engine.start_emotional_decay()
    return engine

def benchmark_emotional_performance(emotional_engine: EmotionalEngine,
                                   test_stimuli: List[Dict]) -> Dict:
    """Benchmark emotional engine performance"""
    import time

    start_time = time.time()
    responses = []

    for stimulus in test_stimuli:
        response_start = time.time()
        emotional_state = emotional_engine.process_emotional_stimulus(stimulus)
        expression = emotional_engine.express_emotion()
        response_time = time.time() - response_start

        responses.append({
            'stimulus': stimulus,
            'emotional_state': emotional_state,
            'expression': expression,
            'response_time': response_time
        })

    total_time = time.time() - start_time

    return {
        'total_time': total_time,
        'stimuli_processed': len(test_stimuli),
        'average_response_time': total_time / len(test_stimuli),
        'responses': responses,
        'final_metrics': emotional_engine.metrics,
        'final_state': emotional_engine.get_emotional_summary()
    }

if __name__ == "__main__":
    # Example usage
    async def main():
        # Create emotional engine
        config = {
            'emotional_decay_rate': 0.05,
            'stress_threshold': 0.7,
            'enable_learning': True,
            'enable_personality_adaptation': True
        }

        emotional_engine = await create_emotional_engine("test_agent", config)

        # Set personality
        emotional_engine.personality.traits[PersonalityTrait.EXTRAVERSION] = 0.8
        emotional_engine.personality.traits[PersonalityTrait.AGREEABLENESS] = 0.7
        emotional_engine.personality.expressiveness = 0.9

        # Test emotional processing
        stimuli = [
            {
                'trigger': 'positive_feedback',
                'text': 'You did a great job!',
                'valence': 0.8,
                'context': {'situation': 'work', 'success': True}
            },
            {
                'trigger': 'challenging_task',
                'text': 'This is really difficult',
                'valence': -0.3,
                'context': {'situation': 'work', 'difficulty': 'high'}
            },
            {
                'trigger': 'social_interaction',
                'text': 'I enjoy talking with you',
                'valence': 0.6,
                'context': {'situation': 'social', 'positive': True}
            }
        ]

        for stimulus in stimuli:
            emotional_state = emotional_engine.process_emotional_stimulus(stimulus)
            expression = emotional_engine.express_emotion()

            print(f"\nStimulus: {stimulus['trigger']}")
            print(f"Emotional state: {emotional_state.mood.value}")
            print(f"Dominant emotions: {max(emotional_state.emotions.items(), key=lambda x: x[1])}")
            print(f"Expression: {expression['expression']}")
            print(f"Stress level: {emotional_engine.stress_level:.2f}")

        # Test emotion recognition
        input_data = {
            'text': 'I am feeling very happy and excited today!',
            'context': {'mood': 'positive'}
        }
        recognized = emotional_engine.recognize_emotions_in_others(input_data)
        print(f"\nRecognized emotions: {recognized}")

        # Test personality adaptation
        feedback = {
            'emotional_stability': 0.8,
            'social_engagement': 0.9
        }
        emotional_engine.adapt_personality(feedback)

        # Get emotional summary
        summary = emotional_engine.get_emotional_summary()
        print("\nEmotional engine summary:")
        print(json.dumps(summary, indent=2, default=str))

        # Save state
        emotional_engine.save_emotional_state("/tmp/test_emotional_state.pkl")

        # Stop background tasks
        emotional_engine.stop_background_tasks()

    asyncio.run(main())