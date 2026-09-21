#!/usr/bin/env python3
"""
ADAPTIVE REALITY AUDIO
Audio system that adapts to listener's biological and psychological state in real-time.
Creates personalized audio experiences based on biometric feedback and environmental context.
"""

import numpy as np
import librosa
import soundfile as sf
from scipy import signal
from scipy.fft import fft, ifft
import threading
import queue
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any, Union, Callable
import math
import json
from collections import deque
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AdaptiveRealityAudio")

class BioSensor(Enum):
    """Types of biological sensors"""
    HEART_RATE = "heart_rate"
    EEG = "eeg"
    GSR = "gsr"                  # Galvanic Skin Response
    RESPIRATION = "respiration"
    TEMPERATURE = "temperature"
    BLOOD_PRESSURE = "blood_pressure"
    PUPIL_DIAMETER = "pupil_diameter"
    FACIAL_EXPRESSION = "facial_expression"
    POSTURE = "posture"
    MOVEMENT = "movement"

class AdaptationStrategy(Enum):
    """Strategies for audio adaptation"""
    BIOLOGICAL = "biological"           # Adapt to biological signals
    PSYCHOLOGICAL = "psychological"     # Adapt to psychological state
    ENVIRONMENTAL = "environmental"     # Adapt to environment
    CONTEXTUAL = "contextual"           # Adapt to context
    PREDICTIVE = "predictive"           # Predict and adapt proactively
    LEARNING = "learning"              # Learn user preferences
    HYBRID = "hybrid"                  # Combine multiple strategies

class AdaptationMode(Enum):
    """Modes of adaptation"""
    GENTLE = "gentle"                  # Subtle, gradual adaptations
    RESPONSIVE = "responsive"           # Quick response to changes
    PROACTIVE = "proactive"            # Anticipatory adaptations
    BALANCED = "balanced"              # Balanced approach
    AGGRESSIVE = "aggressive"           # Strong, noticeable adaptations

@dataclass
class BioSignal:
    """Biological signal data"""
    sensor_type: BioSensor
    value: float
    timestamp: float
    quality: float                    # Signal quality (0-1)
    unit: str                        # Measurement unit
    confidence: float = 1.0          # Confidence in measurement

@dataclass
class PsychologicalState:
    """Psychological state of the listener"""
    attention_level: float           # 0-1
    stress_level: float              # 0-1
    emotional_valence: float         # -1 to 1
    arousal_level: float             # 0-1
    engagement_level: float          # 0-1
    cognitive_load: float            # 0-1
    mood_stability: float            # 0-1

@dataclass
class EnvironmentalContext:
    """Environmental context information"""
    location: Optional[str]          # GPS or semantic location
    time_of_day: float              # 0-24 hours
    noise_level: float              # dB
    lighting_level: float           # lux
    temperature: float              # Celsius
    humidity: float                 # Percentage
    activity_type: Optional[str]    # Current activity
    social_context: Optional[str]   # Alone, with friends, etc.

@dataclass
class AdaptationParameters:
    """Parameters for audio adaptation"""
    frequency_adjustment: float      # Frequency scaling
    amplitude_adjustment: float     # Amplitude scaling
    tempo_adjustment: float         # Tempo scaling
    timbre_modulation: float        # Timbre changes
    spatial_adjustment: float       # Spatial audio changes
    emotional_tint: float          # Emotional coloring
    complexity_level: float        # Complexity of audio

class BioSignalProcessor:
    """Processes and analyzes biological signals"""

    def __init__(self, sampling_rate: float = 100.0):
        self.sampling_rate = sampling_rate
        self.signal_buffers = {sensor: deque(maxlen=int(sampling_rate * 10))
                              for sensor in BioSensor}
        self.baseline_values = {}
        self.signal_quality_threshold = 0.6

    def process_signal(self, signal: BioSignal) -> Dict[str, float]:
        """Process individual biological signal"""
        # Store signal in buffer
        self.signal_buffers[signal.sensor_type].append(signal.value)

        # Calculate signal features
        features = self._extract_signal_features(signal)

        # Update baseline if needed
        self._update_baseline(signal.sensor_type, signal.value)

        return features

    def _extract_signal_features(self, signal: BioSignal) -> Dict[str, float]:
        """Extract features from biological signal"""
        features = {
            'current_value': signal.value,
            'quality': signal.quality,
            'confidence': signal.confidence
        }

        buffer = self.signal_buffers[signal.sensor_type]
        if len(buffer) > 10:
            # Statistical features
            features['mean'] = np.mean(buffer)
            features['std'] = np.std(buffer)
            features['min'] = np.min(buffer)
            features['max'] = np.max(buffer)

            # Trend features
            if len(buffer) >= 20:
                recent = list(buffer)[-10:]
                older = list(buffer)[-20:-10]
                features['trend'] = np.mean(recent) - np.mean(older)

            # Variability features
            features['variability'] = features['std'] / (features['mean'] + 1e-10)

            # Rate of change (for appropriate sensors)
            if signal.sensor_type in [BioSensor.HEART_RATE, BioSensor.RESPIRATION]:
                features['rate_of_change'] = self._calculate_rate_of_change(buffer)

        return features

    def _calculate_rate_of_change(self, buffer: deque) -> float:
        """Calculate rate of change for time-series data"""
        if len(buffer) < 2:
            return 0.0

        values = np.array(list(buffer))
        time_points = np.arange(len(values)) / self.sampling_rate

        # Simple linear regression to get trend
        if len(values) > 1:
            slope = np.polyfit(time_points, values, 1)[0]
            return slope
        return 0.0

    def _update_baseline(self, sensor: BioSensor, value: float):
        """Update baseline values for sensor"""
        if sensor not in self.baseline_values:
            self.baseline_values[sensor] = value
        else:
            # Exponential moving average for baseline
            alpha = 0.01  # Learning rate
            self.baseline_values[sensor] = (1 - alpha) * self.baseline_values[sensor] + alpha * value

    def get_psychological_state(self) -> PsychologicalState:
        """Estimate psychological state from biological signals"""
        # Heart rate variability indicates stress
        hr_features = self._extract_signal_features(BioSignal(BioSensor.HEART_RATE, 0, time.time(), 1.0, 'bpm'))
        stress_from_hr = self._estimate_stress_from_heart_rate(hr_features)

        # GSR indicates emotional arousal
        gsr_features = self._extract_signal_features(BioSensor(BioSensor.GSR, 0, time.time(), 1.0, 'µS'))
        arousal_from_gsr = self._estimate_arousal_from_gsr(gsr_features)

        # Respiration indicates calmness
        resp_features = self._extract_signal_features(BioSignal(BioSensor.RESPIRATION, 0, time.time(), 1.0, 'bpm'))
        calmness_from_resp = self._estimate_calmness_from_respiration(resp_features)

        # Combine into psychological state
        state = PsychologicalState(
            attention_level=0.7,  # Would need more sophisticated estimation
            stress_level=stress_from_hr,
            emotional_valence=0.0,  # Would need facial expression or other inputs
            arousal_level=arousal_from_gsr,
            engagement_level=0.6,   # Would need more complex analysis
            cognitive_load=self._estimate_cognitive_load(),
            mood_stability=1.0 - stress_from_hr
        )

        return state

    def _estimate_stress_from_heart_rate(self, hr_features: Dict[str, float]) -> float:
        """Estimate stress level from heart rate features"""
        if 'mean' not in hr_features:
            return 0.0

        hr = hr_features['mean']
        baseline = self.baseline_values.get(BioSensor.HEART_RATE, 70)

        # Stress increases heart rate
        if hr > baseline + 10:
            stress = min(1.0, (hr - baseline) / 40)
        elif hr < baseline - 10:
            stress = min(1.0, (baseline - hr) / 20) * 0.5  # Low HR can also indicate stress
        else:
            stress = 0.0

        # Consider variability
        if 'variability' in hr_features:
            # Low variability indicates higher stress
            stress *= (2.0 - hr_features['variability'])

        return np.clip(stress, 0, 1)

    def _estimate_arousal_from_gsr(self, gsr_features: Dict[str, float]) -> float:
        """Estimate arousal level from GSR features"""
        if 'mean' not in gsr_features:
            return 0.0

        gsr = gsr_features['mean']
        baseline = self.baseline_values.get(BioSensor.GSR, 1.0)

        # Higher GSR indicates higher arousal
        arousal = (gsr - baseline) / baseline
        return np.clip(arousal, 0, 1)

    def _estimate_calmness_from_respiration(self, resp_features: Dict[str, float]) -> float:
        """Estimate calmness from respiration features"""
        if 'mean' not in resp_features:
            return 0.5

        resp_rate = resp_features['mean']
        # Normal resting respiration is 12-20 breaths per minute
        optimal_rate = 16

        # Deviation from optimal indicates less calmness
        deviation = abs(resp_rate - optimal_rate) / optimal_rate
        calmness = 1.0 - min(deviation, 1.0)

        return calmness

    def _estimate_cognitive_load(self) -> float:
        """Estimate cognitive load from multiple signals"""
        # Simplified: combine heart rate and variability
        hr_features = self._extract_signal_features(BioSignal(BioSensor.HEART_RATE, 0, time.time(), 1.0, 'bpm'))

        cognitive_load = 0.5  # Default

        if 'mean' in hr_features and 'std' in hr_features:
            hr = hr_features['mean']
            hr_var = hr_features['std']
            baseline = self.baseline_values.get(BioSensor.HEART_RATE, 70)

            # Higher heart rate and lower variability indicate higher cognitive load
            hr_factor = min((hr - baseline) / baseline, 1.0)
            var_factor = 1.0 - min(hr_var / 10, 1.0)

            cognitive_load = (hr_factor + var_factor) / 2

        return np.clip(cognitive_load, 0, 1)

class EnvironmentAnalyzer:
    """Analyzes environmental context for adaptation"""

    def __init__(self):
        self.context_history = deque(maxlen=100)
        self.adaptation_history = deque(maxlen=50)

    def analyze_context(self, context: EnvironmentalContext) -> Dict[str, float]:
        """Analyze environmental context and return adaptation factors"""
        factors = {}

        # Time of day adaptations
        factors['circadian_influence'] = self._calculate_circadian_influence(context.time_of_day)

        # Noise level adaptations
        factors['noise_competition'] = self._calculate_noise_competition(context.noise_level)

        # Lighting adaptations
        factors['lighting_influence'] = self._calculate_lighting_influence(context.lighting_level)

        # Temperature adaptations
        factors['thermal_comfort'] = self._calculate_thermal_comfort(context.temperature)

        # Activity-based adaptations
        factors['activity_appropriateness'] = self._calculate_activity_appropriateness(context.activity_type)

        # Social context adaptations
        factors['social_factor'] = self._calculate_social_factor(context.social_context)

        # Store context
        self.context_history.append(context)

        return factors

    def _calculate_circadian_influence(self, time_of_day: float) -> float:
        """Calculate circadian rhythm influence on audio preferences"""
        # Morning (6-12): prefer energizing music
        # Afternoon (12-18): prefer moderate stimulation
        # Evening (18-22): prefer relaxing music
        # Night (22-6): prefer very calming music

        if 6 <= time_of_day < 12:
            return 0.8  # High energy preferred
        elif 12 <= time_of_day < 18:
            return 0.5  # Moderate energy
        elif 18 <= time_of_day < 22:
            return 0.3  # Lower energy
        else:
            return 0.1  # Very low energy

    def _calculate_noise_competition(self, noise_level: float) -> float:
        """Calculate how environmental noise affects audio needs"""
        # Higher noise levels may require different audio characteristics

        if noise_level < 30:  # Very quiet
            return 0.2  # Can use subtle audio
        elif noise_level < 50:  # Quiet
            return 0.4
        elif noise_level < 70:  # Moderate
            return 0.6
        else:  # Loud
            return 0.8  # Need more prominent audio

    def _calculate_lighting_influence(self, lighting_level: float) -> float:
        """Calculate lighting influence on audio preferences"""
        # Bright light: prefer more upbeat music
        # Dim light: prefer more calming music

        if lighting_level > 500:  # Bright
            return 0.7
        elif lighting_level > 100:  # Moderate
            return 0.5
        elif lighting_level > 10:  # Dim
            return 0.3
        else:  # Very dark
            return 0.2

    def _calculate_thermal_comfort(self, temperature: float) -> float:
        """Calculate thermal comfort influence"""
        # Optimal temperature: 20-22°C
        optimal_temp = 21

        deviation = abs(temperature - optimal_temp)
        comfort_factor = 1.0 - min(deviation / 10, 1.0)

        return comfort_factor

    def _calculate_activity_appropriateness(self, activity_type: Optional[str]) -> float:
        """Calculate how appropriate audio is for current activity"""
        activity_preferences = {
            'working': 0.3,      # Background music
            'exercising': 0.9,   # Energetic music
            'relaxing': 0.7,     # Calming music
            'socializing': 0.6,   # Social music
            'sleeping': 0.1,     # Very minimal
            'meditating': 0.2,    # Minimal/ambient
            None: 0.5            # Default
        }

        return activity_preferences.get(activity_type, 0.5)

    def _calculate_social_factor(self, social_context: Optional[str]) -> float:
        """Calculate social context influence"""
        social_factors = {
            'alone': 0.8,        # Can personalize fully
            'partner': 0.6,       # Consider partner
            'friends': 0.4,       # Group considerations
            'family': 0.5,        # Family appropriate
            'public': 0.2,        # Public space considerations
            None: 0.6            # Default
        }

        return social_factors.get(social_context, 0.6)

class AdaptationEngine:
    """Core adaptation engine that determines how to adapt audio"""

    def __init__(self):
        self.bio_processor = BioSignalProcessor()
        self.env_analyzer = EnvironmentAnalyzer()
        self.adaptation_rules = self._initialize_adaptation_rules()
        self.learning_model = self._initialize_learning_model()
        self.adaptation_history = deque(maxlen=100)

    def _initialize_adaptation_rules(self) -> Dict[str, Callable]:
        """Initialize adaptation rules"""
        return {
            'stress_based': self._stress_based_adaptation,
            'attention_based': self._attention_based_adaptation,
            'arousal_based': self._arousal_based_adaptation,
            'context_based': self._context_based_adaptation,
            'fatigue_based': self._fatigue_based_adaptation
        }

    def _initialize_learning_model(self) -> Dict[str, Any]:
        """Initialize simple learning model"""
        return {
            'user_preferences': {
                'preferred_tempo_range': (60, 120),
                'preferred_frequency_range': (200, 2000),
                'stress_sensitivity': 0.5,
                'adaptation_aggressiveness': 0.5
            },
            'adaptation_effectiveness': deque(maxlen=50),
            'learning_rate': 0.01
        }

    def calculate_adaptations(self, bio_signals: List[BioSignal],
                            psychological_state: PsychologicalState,
                            environmental_context: EnvironmentalContext) -> AdaptationParameters:
        """Calculate comprehensive audio adaptation parameters"""
        # Process biological signals
        for signal in bio_signals:
            self.bio_processor.process_signal(signal)

        # Analyze environment
        env_factors = self.env_analyzer.analyze_context(environmental_context)

        # Calculate adaptations using different rules
        adaptations = {}

        # Stress-based adaptation
        stress_adapt = self._stress_based_adaptation(psychological_state.stress_level)
        adaptations.update(stress_adapt)

        # Attention-based adaptation
        attention_adapt = self._attention_based_adaptation(psychological_state.attention_level)
        adaptations.update(attention_adapt)

        # Arousal-based adaptation
        arousal_adapt = self._arousal_based_adaptation(psychological_state.arousal_level)
        adaptations.update(arousal_adapt)

        # Context-based adaptation
        context_adapt = self._context_based_adaptation(env_factors)
        adaptations.update(context_adapt)

        # Cognitive load adaptation
        cognitive_adapt = self._cognitive_load_adaptation(psychological_state.cognitive_load)
        adaptations.update(cognitive_adapt)

        # Apply learning-based adjustments
        learned_adaptations = self._apply_learning_adjustments(adaptations)
        adaptations.update(learned_adaptations)

        # Create final adaptation parameters
        params = AdaptationParameters(
            frequency_adjustment=adaptations.get('frequency_adjustment', 1.0),
            amplitude_adjustment=adaptations.get('amplitude_adjustment', 1.0),
            tempo_adjustment=adaptations.get('tempo_adjustment', 1.0),
            timbre_modulation=adaptations.get('timbre_modulation', 0.0),
            spatial_adjustment=adaptations.get('spatial_adjustment', 1.0),
            emotional_tint=adaptations.get('emotional_tint', 0.0),
            complexity_level=adaptations.get('complexity_level', 0.5)
        )

        # Store adaptation
        self.adaptation_history.append({
            'timestamp': time.time(),
            'parameters': params,
            'psychological_state': psychological_state,
            'environmental_factors': env_factors
        })

        return params

    def _stress_based_adaptation(self, stress_level: float) -> Dict[str, float]:
        """Adapt audio based on stress level"""
        adaptations = {}

        if stress_level > 0.7:  # High stress
            adaptations['frequency_adjustment'] = 0.8  # Lower frequencies
            adaptations['amplitude_adjustment'] = 0.6  # Lower volume
            adaptations['tempo_adjustment'] = 0.7     # Slower tempo
            adaptations['emotional_tint'] = -0.5      # Calming emotional tone
            adaptations['complexity_level'] = 0.3     # Less complexity
        elif stress_level > 0.4:  # Moderate stress
            adaptations['frequency_adjustment'] = 0.9
            adaptations['amplitude_adjustment'] = 0.8
            adaptations['tempo_adjustment'] = 0.85
            adaptations['emotional_tint'] = -0.2
            adaptations['complexity_level'] = 0.5
        else:  # Low stress
            adaptations['frequency_adjustment'] = 1.1  # Higher frequencies
            adaptations['amplitude_adjustment'] = 1.0
            adaptations['tempo_adjustment'] = 1.0
            adaptations['emotional_tint'] = 0.1
            adaptations['complexity_level'] = 0.7

        return adaptations

    def _attention_based_adaptation(self, attention_level: float) -> Dict[str, float]:
        """Adapt audio based on attention level"""
        adaptations = {}

        if attention_level > 0.8:  # High attention - need focus
            adaptations['frequency_adjustment'] = 1.1  # Slightly higher frequencies
            adaptations['amplitude_adjustment'] = 0.7  # Lower volume to avoid distraction
            adaptations['complexity_level'] = 0.2      # Simple, non-distracting
            adaptations['spatial_adjustment'] = 0.8    # Narrow stereo image
        elif attention_level < 0.3:  # Low attention - need stimulation
            adaptations['frequency_adjustment'] = 1.0
            adaptations['amplitude_adjustment'] = 1.1   # Slightly higher volume
            adaptations['complexity_level'] = 0.8      # More engaging
            adaptations['spatial_adjustment'] = 1.2    # Wider stereo image
        else:  # Moderate attention
            adaptations['frequency_adjustment'] = 1.0
            adaptations['amplitude_adjustment'] = 1.0
            adaptations['complexity_level'] = 0.5
            adaptations['spatial_adjustment'] = 1.0

        return adaptations

    def _arousal_based_adaptation(self, arousal_level: float) -> Dict[str, float]:
        """Adapt audio based on arousal level"""
        adaptations = {}

        if arousal_level > 0.7:  # High arousal
            adaptations['tempo_adjustment'] = 1.2      # Faster tempo
            adaptations['frequency_adjustment'] = 1.1  # Brighter frequencies
            adaptations['amplitude_adjustment'] = 1.1  # Higher volume
            adaptations['emotional_tint'] = 0.3       # More positive
        elif arousal_level < 0.3:  # Low arousal
            adaptations['tempo_adjustment'] = 0.8      # Slower tempo
            adaptations['frequency_adjustment'] = 0.9  # Softer frequencies
            adaptations['amplitude_adjustment'] = 0.9  # Lower volume
            adaptations['emotional_tint'] = -0.2      # More calming
        else:  # Moderate arousal
            adaptations['tempo_adjustment'] = 1.0
            adaptations['frequency_adjustment'] = 1.0
            adaptations['amplitude_adjustment'] = 1.0
            adaptations['emotional_tint'] = 0.0

        return adaptations

    def _context_based_adaptation(self, env_factors: Dict[str, float]) -> Dict[str, float]:
        """Adapt audio based on environmental context"""
        adaptations = {}

        # Circadian influence
        circadian = env_factors.get('circadian_influence', 0.5)
        adaptations['tempo_adjustment'] = 0.7 + circadian * 0.6  # Scale tempo based on time

        # Noise competition
        noise_comp = env_factors.get('noise_competition', 0.5)
        adaptations['amplitude_adjustment'] = 0.8 + noise_comp * 0.4
        adaptations['frequency_adjustment'] = 1.2 - noise_comp * 0.3  # Compensate for noise

        # Lighting influence
        lighting = env_factors.get('lighting_influence', 0.5)
        adaptations['emotional_tint'] = (lighting - 0.5) * 0.4

        # Thermal comfort
        thermal = env_factors.get('thermal_comfort', 0.5)
        if thermal < 0.5:  # Uncomfortable temperature
            adaptations['amplitude_adjustment'] *= 0.9  # Reduce slightly
            adaptations['complexity_level'] = 0.3      # Simpler audio

        # Activity appropriateness
        activity = env_factors.get('activity_appropriateness', 0.5)
        adaptations['amplitude_adjustment'] *= activity

        return adaptations

    def _cognitive_load_adaptation(self, cognitive_load: float) -> Dict[str, float]:
        """Adapt audio based on cognitive load"""
        adaptations = {}

        if cognitive_load > 0.7:  # High cognitive load
            adaptations['complexity_level'] = 0.2      # Very simple
            adaptations['amplitude_adjustment'] = 0.6  # Background level
            adaptations['tempo_adjustment'] = 0.8     # Slower
            adaptations['spatial_adjustment'] = 0.7    # Narrow spatial image
        elif cognitive_load < 0.3:  # Low cognitive load
            adaptations['complexity_level'] = 0.8      # More engaging
            adaptations['amplitude_adjustment'] = 1.1  # Slightly louder
            adaptations['tempo_adjustment'] = 1.1     # Slightly faster
            adaptations['spatial_adjustment'] = 1.2    # Wider spatial image
        else:  # Moderate cognitive load
            adaptations['complexity_level'] = 0.5
            adaptations['amplitude_adjustment'] = 1.0
            adaptations['tempo_adjustment'] = 1.0
            adaptations['spatial_adjustment'] = 1.0

        return adaptations

    def _apply_learning_adjustments(self, adaptations: Dict[str, float]) -> Dict[str, float]:
        """Apply learned user preferences to adaptations"""
        user_prefs = self.learning_model['user_preferences']
        learned_adaptations = adaptations.copy()

        # Apply stress sensitivity
        stress_sensitivity = user_prefs.get('stress_sensitivity', 0.5)
        if 'frequency_adjustment' in learned_adaptations:
            # Adjust based on how stress-sensitive the user is
            learned_adaptations['frequency_adjustment'] = (
                1 + (learned_adaptations['frequency_adjustment'] - 1) * stress_sensitivity
            )

        # Apply adaptation aggressiveness
        aggressiveness = user_prefs.get('adaptation_aggressiveness', 0.5)
        for key in learned_adaptations:
            if key != 'emotional_tint':  # Don't scale emotional tint
                learned_adaptations[key] = (
                    1 + (learned_adaptations[key] - 1) * aggressiveness
                )

        return learned_adaptations

    def update_learning_model(self, adaptation_effectiveness: float):
        """Update learning model based on feedback"""
        self.learning_model['adaptation_effectiveness'].append(adaptation_effectiveness)

        # Simple learning: adjust user preferences based on effectiveness
        if len(self.learning_model['adaptation_effectiveness']) >= 5:
            recent_effectiveness = list(self.learning_model['adaptation_effectiveness'])[-5:]
            avg_effectiveness = np.mean(recent_effectiveness)

            if avg_effectiveness < 0.5:  # Adaptations not working well
                # Reduce aggressiveness
                current_aggressiveness = self.learning_model['user_preferences']['adaptation_aggressiveness']
                new_aggressiveness = max(0.1, current_aggressiveness - 0.05)
                self.learning_model['user_preferences']['adaptation_aggressiveness'] = new_aggressiveness
            elif avg_effectiveness > 0.8:  # Adaptations working well
                # Could increase aggressiveness slightly
                current_aggressiveness = self.learning_model['user_preferences']['adaptation_aggressiveness']
                new_aggressiveness = min(1.0, current_aggressiveness + 0.02)
                self.learning_model['user_preferences']['adaptation_aggressiveness'] = new_aggressiveness

class AdaptiveAudioProcessor:
    """Processes and adapts audio in real-time"""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.adaptation_engine = AdaptationEngine()
        self.current_adaptations = AdaptationParameters(1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.5)

        # Audio processing buffers
        self.audio_buffer = deque(maxlen=int(sample_rate * 10))  # 10 seconds
        self.adaptation_smooth_factor = 0.1  # How quickly to adapt

    def process_audio_chunk(self, audio_chunk: np.ndarray,
                          bio_signals: List[BioSignal],
                          psychological_state: PsychologicalState,
                          environmental_context: EnvironmentalContext) -> np.ndarray:
        """Process audio chunk with adaptive modifications"""
        # Calculate new adaptations
        new_adaptations = self.adaptation_engine.calculate_adaptations(
            bio_signals, psychological_state, environmental_context
        )

        # Smooth transitions between adaptations
        self.current_adaptations = self._smooth_adaptations(
            self.current_adaptations, new_adaptations
        )

        # Apply adaptations to audio
        processed_audio = self._apply_adaptations(audio_chunk, self.current_adaptations)

        # Store in buffer
        self.audio_buffer.extend(processed_audio)

        return processed_audio

    def _smooth_adaptations(self, current: AdaptationParameters,
                          target: AdaptationParameters) -> AdaptationParameters:
        """Smooth transition between adaptation states"""
        smoothed = AdaptationParameters(
            frequency_adjustment=(current.frequency_adjustment * (1 - self.adaptation_smooth_factor) +
                                target.frequency_adjustment * self.adaptation_smooth_factor),
            amplitude_adjustment=(current.amplitude_adjustment * (1 - self.adaptation_smooth_factor) +
                               target.amplitude_adjustment * self.adaptation_smooth_factor),
            tempo_adjustment=(current.tempo_adjustment * (1 - self.adaptation_smooth_factor) +
                            target.tempo_adjustment * self.adaptation_smooth_factor),
            timbre_modulation=(current.timbre_modulation * (1 - self.adaptation_smooth_factor) +
                             target.timbre_modulation * self.adaptation_smooth_factor),
            spatial_adjustment=(current.spatial_adjustment * (1 - self.adaptation_smooth_factor) +
                              target.spatial_adjustment * self.adaptation_smooth_factor),
            emotional_tint=(current.emotional_tint * (1 - self.adaptation_smooth_factor) +
                          target.emotional_tint * self.adaptation_smooth_factor),
            complexity_level=(current.complexity_level * (1 - self.adaptation_smooth_factor) +
                            target.complexity_level * self.adaptation_smooth_factor)
        )

        return smoothed

    def _apply_adaptations(self, audio: np.ndarray, adaptations: AdaptationParameters) -> np.ndarray:
        """Apply adaptation parameters to audio"""
        processed_audio = audio.copy()

        # Apply frequency adjustment (pitch shifting)
        if abs(adaptations.frequency_adjustment - 1.0) > 0.01:
            processed_audio = self._apply_frequency_adjustment(processed_audio, adaptations.frequency_adjustment)

        # Apply amplitude adjustment
        processed_audio *= adaptations.amplitude_adjustment

        # Apply tempo adjustment
        if abs(adaptations.tempo_adjustment - 1.0) > 0.01:
            processed_audio = self._apply_tempo_adjustment(processed_audio, adaptations.tempo_adjustment)

        # Apply timbre modulation
        if abs(adaptations.timbre_modulation) > 0.01:
            processed_audio = self._apply_timbre_modulation(processed_audio, adaptations.timbre_modulation)

        # Apply spatial adjustment
        if abs(adaptations.spatial_adjustment - 1.0) > 0.01:
            processed_audio = self._apply_spatial_adjustment(processed_audio, adaptations.spatial_adjustment)

        # Apply emotional tint
        if abs(adaptations.emotional_tint) > 0.01:
            processed_audio = self._apply_emotional_tint(processed_audio, adaptations.emotional_tint)

        # Apply complexity adjustment
        if abs(adaptations.complexity_level - 0.5) > 0.1:
            processed_audio = self._apply_complexity_adjustment(processed_audio, adaptations.complexity_level)

        # Normalize to prevent clipping
        if np.max(np.abs(processed_audio)) > 1.0:
            processed_audio = processed_audio / np.max(np.abs(processed_audio))

        return processed_audio

    def _apply_frequency_adjustment(self, audio: np.ndarray, factor: float) -> np.ndarray:
        """Apply frequency/pitch adjustment"""
        # Simplified pitch shifting using resampling
        if factor == 1.0:
            return audio

        # Resample for pitch shifting
        original_length = len(audio)
        new_length = int(original_length / factor)

        if new_length > 0:
            # Resample
            resampled = signal.resample(audio, new_length)

            # Pad or trim to original length
            if len(resampled) < original_length:
                padded = np.pad(resampled, (0, original_length - len(resampled)))
                return padded
            else:
                return resampled[:original_length]

        return audio

    def _apply_tempo_adjustment(self, audio: np.ndarray, factor: float) -> np.ndarray:
        """Apply tempo adjustment"""
        if factor == 1.0:
            return audio

        # Simple tempo adjustment using phase vocoder would be ideal
        # For now, use time-stretching with resampling
        original_length = len(audio)
        new_length = int(original_length * factor)

        if new_length > 0:
            stretched = signal.resample(audio, new_length)

            # Pad or trim to original length
            if len(stretched) < original_length:
                padded = np.pad(stretched, (0, original_length - len(stretched)))
                return padded
            else:
                return stretched[:original_length]

        return audio

    def _apply_timbre_modulation(self, audio: np.ndarray, modulation: float) -> np.ndarray:
        """Apply timbre modulation"""
        if modulation == 0.0:
            return audio

        # Apply spectral filtering for timbre changes
        fft_audio = fft(audio)
        frequencies = np.fft.fftfreq(len(audio), 1/self.sample_rate)

        # Create filter based on modulation
        if modulation > 0:
            # Brighten timbre - boost high frequencies
            filter_gain = 1 + 0.5 * modulation * (frequencies / (self.sample_rate/2))
        else:
            # Darken timbre - boost low frequencies
            filter_gain = 1 - 0.5 * abs(modulation) * (frequencies / (self.sample_rate/2))

        # Apply filter
        filtered_fft = fft_audio * filter_gain
        processed_audio = np.real(ifft(filtered_fft))

        return processed_audio

    def _apply_spatial_adjustment(self, audio: np.ndarray, adjustment: float) -> np.ndarray:
        """Apply spatial adjustment (stereo width)"""
        # For mono audio, create stereo effect
        if len(audio.shape) == 1:
            # Create stereo from mono
            stereo_audio = np.column_stack((audio, audio))
        else:
            stereo_audio = audio.copy()

        # Adjust stereo width
        if adjustment > 1.0:  # Widen
            mid = (stereo_audio[:, 0] + stereo_audio[:, 1]) / 2
            side = (stereo_audio[:, 0] - stereo_audio[:, 1]) / 2
            side_gain = (adjustment - 1.0) * 0.5

            stereo_audio[:, 0] = mid + side * (1 + side_gain)
            stereo_audio[:, 1] = mid - side * (1 + side_gain)
        elif adjustment < 1.0:  # Narrow
            width = adjustment
            stereo_audio[:, 0] = stereo_audio[:, 0] * width + stereo_audio[:, 1] * (1 - width) / 2
            stereo_audio[:, 1] = stereo_audio[:, 1] * width + stereo_audio[:, 0] * (1 - width) / 2

        return stereo_audio

    def _apply_emotional_tint(self, audio: np.ndarray, tint: float) -> np.ndarray:
        """Apply emotional tint to audio"""
        if tint == 0.0:
            return audio

        # Apply subtle harmonic changes based on emotional tint
        fft_audio = fft(audio)

        if tint > 0:
            # Positive emotion - enhance harmonics
            for harmonic in [2, 3, 5]:
                if len(fft_audio) > harmonic * 100:
                    fft_audio[harmonic * 100:(harmonic + 1) * 100] *= (1 + tint * 0.2)
        else:
            # Negative emotion - reduce harmonics
            for harmonic in [2, 3, 5]:
                if len(fft_audio) > harmonic * 100:
                    fft_audio[harmonic * 100:(harmonic + 1) * 100] *= (1 + tint * 0.3)

        processed_audio = np.real(ifft(fft_audio))
        return processed_audio

    def _apply_complexity_adjustment(self, audio: np.ndarray, complexity: float) -> np.ndarray:
        """Apply complexity adjustment"""
        if complexity == 0.5:
            return audio

        # Complexity affects spectral richness
        fft_audio = fft(audio)
        frequencies = np.fft.fftfreq(len(audio), 1/self.sample_rate)

        if complexity > 0.5:
            # Increase complexity - add harmonics
            for i in range(2, min(8, len(fft_audio) // 100)):
                start_freq = i * 100
                end_freq = min((i + 1) * 100, len(fft_audio))
                if end_freq > start_freq:
                    harmonic_strength = (complexity - 0.5) * 2 * (1 / i)
                    fft_audio[start_freq:end_freq] *= (1 + harmonic_strength * 0.3)
        else:
            # Decrease complexity - reduce harmonics
            reduction_factor = complexity * 2
            for i in range(2, min(8, len(fft_audio) // 100)):
                start_freq = i * 100
                end_freq = min((i + 1) * 100, len(fft_audio))
                if end_freq > start_freq:
                    fft_audio[start_freq:end_freq] *= reduction_factor

        processed_audio = np.real(ifft(fft_audio))
        return processed_audio

class AdaptiveRealityAudioSystem:
    """Main adaptive reality audio system"""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.audio_processor = AdaptiveAudioProcessor(sample_rate)

        # Data queues
        self.bio_signal_queue = queue.Queue()
        self.audio_input_queue = queue.Queue()
        self.audio_output_queue = queue.Queue()

        # System state
        self.is_running = False
        self.processing_thread = None

        # Current state tracking
        self.current_psychological_state = PsychologicalState(0.5, 0.3, 0.0, 0.5, 0.6, 0.4, 0.7)
        self.current_environmental_context = EnvironmentalContext(
            None, 12.0, 40.0, 500.0, 22.0, 50.0, 'working', 'alone'
        )

        # Performance monitoring
        self.performance_metrics = {
            'bio_signals_processed': 0,
            'audio_chunks_processed': 0,
            'adaptations_performed': 0,
            'average_processing_time': deque(maxlen=100)
        }

    def add_bio_signal(self, sensor_type: BioSensor, value: float,
                      quality: float = 1.0, unit: str = "", confidence: float = 1.0):
        """Add biological signal for processing"""
        signal = BioSignal(
            sensor_type=sensor_type,
            value=value,
            timestamp=time.time(),
            quality=quality,
            unit=unit,
            confidence=confidence
        )

        self.bio_signal_queue.put(signal)
        self.performance_metrics['bio_signals_processed'] += 1

    def add_audio_input(self, audio: np.ndarray):
        """Add audio input for adaptive processing"""
        self.audio_input_queue.put(audio)

    def update_environmental_context(self, context: EnvironmentalContext):
        """Update environmental context"""
        self.current_environmental_context = context

    def update_psychological_state(self, state: PsychologicalState):
        """Update psychological state estimate"""
        self.current_psychological_state = state

    def start_adaptive_processing(self):
        """Start adaptive audio processing"""
        self.is_running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()

        logger.info("Started adaptive reality audio processing")

    def stop_adaptive_processing(self):
        """Stop adaptive audio processing"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)

        logger.info("Stopped adaptive reality audio processing")

    def _processing_loop(self):
        """Main processing loop"""
        bio_signals_buffer = []
        last_bio_update = time.time()

        while self.is_running:
            start_time = time.time()

            # Collect bio signals
            try:
                while True:
                    signal = self.bio_signal_queue.get_nowait()
                    bio_signals_buffer.append(signal)
            except queue.Empty:
                pass

            # Update psychological state from bio signals
            if time.time() - last_bio_update > 1.0 and bio_signals_buffer:
                self.current_psychological_state = self.audio_processor.adaptation_engine.bio_processor.get_psychological_state()
                bio_signals_buffer = []
                last_bio_update = time.time()

            # Process audio if available
            try:
                audio_input = self.audio_input_queue.get_nowait()

                # Process with adaptations
                processed_audio = self.audio_processor.process_audio_chunk(
                    audio_input,
                    bio_signals_buffer[-5:] if bio_signals_buffer else [],
                    self.current_psychological_state,
                    self.current_environmental_context
                )

                self.audio_output_queue.put(processed_audio)
                self.performance_metrics['audio_chunks_processed'] += 1
                self.performance_metrics['adaptations_performed'] += 1

            except queue.Empty:
                pass

            # Update performance metrics
            processing_time = time.time() - start_time
            self.performance_metrics['average_processing_time'].append(processing_time)

            # Brief sleep to prevent busy waiting
            time.sleep(0.001)

    def get_processed_audio(self) -> Optional[np.ndarray]:
        """Get processed audio chunk"""
        try:
            return self.audio_output_queue.get_nowait()
        except queue.Empty:
            return None

    def get_current_adaptations(self) -> AdaptationParameters:
        """Get current adaptation parameters"""
        return self.audio_processor.current_adaptations

    def provide_feedback(self, effectiveness_score: float):
        """Provide feedback on adaptation effectiveness"""
        self.audio_processor.adaptation_engine.update_learning_model(effectiveness_score)

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'is_running': self.is_running,
            'psychological_state': self.current_psychological_state.__dict__,
            'environmental_context': self.current_environmental_context.__dict__,
            'current_adaptations': self.audio_processor.current_adaptations.__dict__,
            'performance_metrics': dict(self.performance_metrics),
            'learning_model': self.audio_processor.adaptation_engine.learning_model
        }

        if self.performance_metrics['average_processing_time']:
            status['performance_metrics']['average_processing_time'] = np.mean(
                self.performance_metrics['average_processing_time']
            )

        return status

def main():
    """Demonstration of Adaptive Reality Audio System"""
    print("ADAPTIVE REALITY AUDIO - Biologically-Responsive Audio System")
    print("=" * 70)

    # Initialize system
    system = AdaptiveRealityAudioSystem(sample_rate=44100)

    # Create test audio
    duration = 10.0
    sample_rate = 44100
    t = np.linspace(0, duration, int(duration * sample_rate))
    test_audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # Simple sine wave

    print("\nDemonstrating adaptive audio processing...")

    # Simulate changing biological and environmental conditions
    scenarios = [
        # (stress_level, attention_level, arousal_level, time_of_day, description)
        (0.2, 0.8, 0.6, 9.0, "Morning focus session"),
        (0.7, 0.4, 0.8, 14.0, "Stressful afternoon"),
        (0.1, 0.3, 0.3, 20.0, "Evening relaxation"),
        (0.5, 0.9, 0.7, 10.0, "High cognitive load work"),
        (0.8, 0.2, 0.9, 16.0, "High stress emergency")
    ]

    for stress, attention, arousal, time_of_day, description in scenarios:
        print(f"\nScenario: {description}")

        # Update psychological state
        psychological_state = PsychologicalState(
            attention_level=attention,
            stress_level=stress,
            emotional_valence=0.0,
            arousal_level=arousal,
            engagement_level=0.6,
            cognitive_load=0.5,
            mood_stability=1.0 - stress
        )
        system.update_psychological_state(psychological_state)

        # Update environmental context
        environmental_context = EnvironmentalContext(
            location="office",
            time_of_day=time_of_day,
            noise_level=45.0,
            lighting_level=500.0,
            temperature=22.0,
            humidity=50.0,
            activity_type="working",
            social_context="alone"
        )
        system.update_environmental_context(environmental_context)

        # Simulate biological signals
        heart_rate = 70 + stress * 30  # Stress increases heart rate
        system.add_bio_signal(BioSensor.HEART_RATE, heart_rate, quality=0.9, unit="bpm")

        gsr = 1.0 + arousal * 2.0  # Arousal increases GSR
        system.add_bio_signal(BioSensor.GSR, gsr, quality=0.8, unit="µS")

        # Process audio chunk
        audio_chunk = test_audio[:int(sample_rate * 2)]  # 2 second chunk
        system.add_audio_input(audio_chunk)

        # Get processed audio
        processed_chunk = system.get_processed_audio()
        if processed_chunk is not None:
            filename = f"/home/activeloguser/DMLogn8n/sensory/ultimate/adaptive_{description.replace(' ', '_')}.wav"
            sf.write(filename, processed_chunk, sample_rate)
            print(f"  Saved adaptive audio: {filename}")

        # Display adaptations
        adaptations = system.get_current_adaptations()
        print(f"  Frequency adjustment: {adaptations.frequency_adjustment:.2f}")
        print(f"  Amplitude adjustment: {adaptations.amplitude_adjustment:.2f}")
        print(f"  Tempo adjustment: {adaptations.tempo_adjustment:.2f}")
        print(f"  Emotional tint: {adaptations.emotional_tint:.2f}")
        print(f"  Complexity level: {adaptations.complexity_level:.2f}")

        time.sleep(0.5)  # Brief pause between scenarios

    # Start continuous adaptive processing
    print(f"\nStarting continuous adaptive processing...")
    system.start_adaptive_processing()

    # Simulate real-time operation
    for i in range(20):
        # Generate test audio
        audio_chunk = 0.3 * np.sin(2 * np.pi * (440 + i * 10) * np.linspace(0, 0.5, int(sample_rate * 0.5)))
        system.add_audio_input(audio_chunk)

        # Simulate varying bio signals
        stress = 0.3 + 0.2 * np.sin(i * 0.5)
        heart_rate = 70 + stress * 20
        system.add_bio_signal(BioSensor.HEART_RATE, heart_rate, quality=0.9, unit="bpm")

        # Get processed audio
        processed_chunk = system.get_processed_audio()
        if processed_chunk is not None and i % 5 == 0:
            print(f"  Processed chunk {i}: shape {processed_chunk.shape}")

        # Provide occasional feedback
        if i % 10 == 5:
            feedback = np.random.uniform(0.6, 0.9)  # Positive feedback
            system.provide_feedback(feedback)
            print(f"  Provided feedback: {feedback:.2f}")

        time.sleep(0.1)

    system.stop_adaptive_processing()

    # Collect real-time audio
    real_time_audio = []
    while True:
        chunk = system.get_processed_audio()
        if chunk is not None:
            real_time_audio.extend(chunk)
        else:
            break

    if real_time_audio:
        real_time_audio = np.array(real_time_audio)
        rt_file = "/home/activeloguser/DMLogn8n/sensory/ultimate/adaptive_realtime.wav"
        sf.write(rt_file, real_time_audio, sample_rate)
        print(f"Saved real-time adaptive audio: {rt_file}")

    # Display final system status
    status = system.get_system_status()
    print(f"\nFinal System Status:")
    print(f"Bio signals processed: {status['performance_metrics']['bio_signals_processed']}")
    print(f"Audio chunks processed: {status['performance_metrics']['audio_chunks_processed']}")
    print(f"Adaptations performed: {status['performance_metrics']['adaptations_performed']}")
    print(f"Average processing time: {status['performance_metrics'].get('average_processing_time', 0):.3f}s")

    current_state = status['psychological_state']
    print(f"\nFinal Psychological State:")
    print(f"  Stress level: {current_state['stress_level']:.2f}")
    print(f"  Attention level: {current_state['attention_level']:.2f}")
    print(f"  Arousal level: {current_state['arousal_level']:.2f}")

    current_adaptations = status['current_adaptations']
    print(f"\nFinal Adaptations:")
    print(f"  Frequency: {current_adaptations['frequency_adjustment']:.2f}")
    print(f"  Amplitude: {current_adaptations['amplitude_adjustment']:.2f}")
    print(f"  Tempo: {current_adaptations['tempo_adjustment']:.2f}")

    learning_model = status['learning_model']
    user_prefs = learning_model['user_preferences']
    print(f"\nLearned User Preferences:")
    print(f"  Adaptation aggressiveness: {user_prefs['adaptation_aggressiveness']:.2f}")
    print(f"  Stress sensitivity: {user_prefs['stress_sensitivity']:.2f}")

    print("\nADAPTIVE REALITY AUDIO COMPLETE!")
    print("This system creates truly personalized audio experiences that")
    print("adapt in real-time to your biological and psychological state,")
    print("providing the perfect soundtrack for every moment of your life.")

if __name__ == "__main__":
    main()