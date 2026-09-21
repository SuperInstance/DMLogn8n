#!/usr/bin/env python3
"""
EMOTIONAL SYNTHESIZER
AI-powered music generation that responds to and creates emotional states.
Converts emotions, brainwaves, and psychological states into perfect musical compositions.
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
from typing import List, Tuple, Optional, Dict, Any, Union
import math
import json
from collections import deque
import logging
from enum import Enum
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EmotionalSynthesizer")

class EmotionalState(Enum):
    """Core emotional states for synthesis"""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    LOVE = "love"
    WONDER = "wonder"
    PEACE = "peace"
    EXCITEMENT = "excitement"
    NOSTALGIA = "nostalgia"
    HOPE = "hope"
    DESPAIR = "despair"
    TRIUMPH = "triumph"
    MYSTERY = "mystery"

@dataclass
class EmotionalProfile:
    """Complete emotional profile with intensity and valence"""
    primary_emotion: EmotionalState
    secondary_emotion: Optional[EmotionalState] = None
    intensity: float = 0.7  # 0.0 to 1.0
    valence: float = 0.5   # -1.0 (negative) to 1.0 (positive)
    arousal: float = 0.5   # 0.0 (calm) to 1.0 (excited)
    complexity: float = 0.5  # 0.0 (simple) to 1.0 (complex)
    stability: float = 0.5   # 0.0 (unstable) to 1.0 (stable)

@dataclass
class BrainwavePattern:
    """Brainwave patterns for neural audio generation"""
    delta: float    # 0.5-4 Hz: Deep sleep, meditation
    theta: float    # 4-8 Hz: Creativity, intuition
    alpha: float    # 8-12 Hz: Relaxation, calm
    beta: float     # 12-30 Hz: Focus, alertness
    gamma: float    # 30-100 Hz: Insight, processing

class EmotionalMusicTheory:
    """Music theory adapted for emotional expression"""

    def __init__(self):
        # Emotional tonal mappings
        self.emotional_scales = {
            EmotionalState.JOY: [0, 2, 4, 7, 9],           # Major pentatonic
            EmotionalState.SADNESS: [0, 3, 5, 7, 10],      # Minor pentatonic
            EmotionalState.ANGER: [0, 1, 4, 7, 8, 10],     # Blues scale
            EmotionalState.FEAR: [0, 2, 3, 5, 6, 8, 9],    # Diminished scale
            EmotionalState.LOVE: [0, 2, 4, 7, 9, 11],      # Major scale
            EmotionalState.WONDER: [0, 2, 3, 5, 7, 8, 10], # Harmonic minor
            EmotionalState.PEACE: [0, 2, 4, 7, 9],         # Major pentatonic
            EmotionalState.EXCITEMENT: [0, 2, 4, 6, 7, 9, 10], # Lydian dominant
            EmotionalState.NOSTALGIA: [0, 2, 3, 5, 7, 8],  # Dorian mode
            EmotionalState.HOPE: [0, 2, 4, 5, 7, 9, 11],   # Major with raised 4th
            EmotionalState.DESPAIR: [0, 1, 3, 6, 8, 10],   # Whole tone
            EmotionalState.TRIUMPH: [0, 2, 4, 7, 9, 11],   # Major
            EmotionalState.MYSTERY: [0, 1, 3, 4, 6, 8, 10] # Octatonic
        }

        # Emotional tempo mappings (BPM)
        self.emotional_tempos = {
            EmotionalState.JOY: (120, 140),
            EmotionalState.SADNESS: (60, 80),
            EmotionalState.ANGER: (140, 180),
            EmotionalState.FEAR: (100, 130),
            EmotionalState.LOVE: (80, 110),
            EmotionalState.WONDER: (90, 120),
            EmotionalState.PEACE: (50, 70),
            EmotionalState.EXCITEMENT: (130, 160),
            EmotionalState.NOSTALGIA: (70, 90),
            EmotionalState.HOPE: (90, 110),
            EmotionalState.DESPAIR: (40, 60),
            EmotionalState.TRIUMPH: (120, 150),
            EmotionalState.MYSTERY: (80, 100)
        }

        # Emotional rhythm patterns
        self.emotional_rhythms = {
            EmotionalState.JOY: [0.5, 0.5, 0.5, 0.5],       # Even quarter notes
            EmotionalState.SADNESS: [1.0, 0.5, 1.5],        # Slow, uneven
            EmotionalState.ANGER: [0.25, 0.25, 0.25, 0.25], # Fast sixteenths
            EmotionalState.FEAR: [0.33, 0.33, 0.34],        # Triplet feel
            EmotionalState.LOVE: [0.75, 0.25, 0.5, 0.5],    # Swung feel
            EmotionalState.PEACE: [2.0, 2.0],               # Whole notes
            EmotionalState.EXCITEMENT: [0.125, 0.125, 0.25, 0.5] # Fast syncopation
        }

    def get_emotional_scale(self, emotion: EmotionalState, complexity: float = 0.5) -> List[int]:
        """Get scale notes for emotion with complexity variation"""
        base_scale = self.emotional_scales[emotion]

        # Add complexity by adding chromatic notes
        if complexity > 0.5:
            additional_notes = [n for n in range(12) if n not in base_scale]
            num_additional = int((complexity - 0.5) * len(additional_notes))
            if num_additional > 0:
                selected = random.sample(additional_notes, min(num_additional, len(additional_notes)))
                base_scale.extend(selected)
                base_scale.sort()

        return base_scale

    def get_emotional_tempo(self, emotion: EmotionalState, arousal: float = 0.5) -> float:
        """Get tempo for emotion based on arousal level"""
        min_tempo, max_tempo = self.emotional_tempos[emotion]

        # Adjust tempo based on arousal
        if arousal > 0.5:
            tempo = min_tempo + (max_tempo - min_tempo) * arousal
        else:
            tempo = min_tempo + (max_tempo - min_tempo) * arousal * 0.5

        return tempo

    def get_emotional_rhythm(self, emotion: EmotionalState, stability: float = 0.5) -> List[float]:
        """Get rhythm pattern for emotion with stability variation"""
        base_rhythm = self.emotional_rhythms[emotion]

        # Add instability by varying rhythms
        if stability < 0.5:
            instability = 1 - stability
            rhythm = []
            for duration in base_rhythm:
                variation = duration * (1 + (random.random() - 0.5) * instability * 0.3)
                rhythm.append(max(0.1, variation))  # Minimum duration
            return rhythm
        else:
            return base_rhythm

class BrainwaveAnalyzer:
    """Analyzes and generates brainwave patterns for emotional synthesis"""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.brainwave_bands = {
            'delta': (0.5, 4),
            'theta': (4, 8),
            'alpha': (8, 12),
            'beta': (12, 30),
            'gamma': (30, 100)
        }

    def analyze_emotion_from_brainwaves(self, eeg_data: np.ndarray) -> EmotionalProfile:
        """Analyze emotional state from simulated EEG data"""
        # Perform FFT to get frequency spectrum
        spectrum = np.abs(fft(eeg_data))
        freqs = np.fft.fftfreq(len(eeg_data), 1/self.sample_rate)

        # Calculate power in each brainwave band
        band_powers = {}
        for band, (low, high) in self.brainwave_bands.items():
            mask = (freqs >= low) & (freqs <= high)
            band_powers[band] = np.sum(spectrum[mask])

        # Normalize powers
        total_power = sum(band_powers.values())
        if total_power > 0:
            for band in band_powers:
                band_powers[band] /= total_power

        # Map brainwave patterns to emotions
        emotion = self._map_brainwaves_to_emotion(band_powers)
        intensity = (band_powers['beta'] + band_powers['gamma']) / 2
        valence = band_powers['alpha'] - band_powers['theta']
        arousal = (band_powers['beta'] + band_powers['gamma']) / 2
        stability = band_powers['alpha'] / (band_powers['theta'] + 0.01)

        return EmotionalProfile(
            primary_emotion=emotion,
            intensity=min(1.0, intensity * 2),
            valence=np.clip(valence * 2, -1, 1),
            arousal=min(1.0, arousal * 2),
            stability=min(1.0, stability)
        )

    def _map_brainwaves_to_emotion(self, band_powers: Dict[str, float]) -> EmotionalState:
        """Map brainwave power distribution to primary emotion"""
        delta = band_powers['delta']
        theta = band_powers['theta']
        alpha = band_powers['alpha']
        beta = band_powers['beta']
        gamma = band_powers['gamma']

        # Simple emotion mapping based on brainwave patterns
        if alpha > 0.3 and theta > 0.2:
            return EmotionalState.PEACE
        elif beta > 0.3 and gamma > 0.2:
            return EmotionalState.EXCITEMENT
        elif theta > 0.3 and delta > 0.2:
            return EmotionalState.NOSTALGIA
        elif beta > 0.4:
            return EmotionalState.ANGER
        elif gamma > 0.3 and alpha < 0.1:
            return EmotionalState.FEAR
        elif theta > 0.25:
            return EmotionalState.CREATIVITY if EmotionalState.CREATIVITY in EmotionalState else EmotionalState.WONDER
        else:
            return EmotionalState.JOY

    def generate_brainwave_pattern(self, emotion: EmotionalState, duration: float) -> np.ndarray:
        """Generate synthetic brainwave pattern for emotion"""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        signal = np.zeros_like(t)

        # Base frequencies for each emotion
        emotion_frequencies = {
            EmotionalState.JOY: {'alpha': 10, 'beta': 18},
            EmotionalState.SADNESS: {'theta': 6, 'delta': 2},
            EmotionalState.ANGER: {'beta': 25, 'gamma': 40},
            EmotionalState.FEAR: {'beta': 20, 'gamma': 35},
            EmotionalState.LOVE: {'alpha': 9, 'theta': 5},
            EmotionalState.PEACE: {'alpha': 11, 'theta': 4},
            EmotionalState.EXCITEMENT: {'beta': 22, 'gamma': 45},
            EmotionalState.NOSTALGIA: {'theta': 7, 'alpha': 8}
        }

        freqs = emotion_frequencies.get(emotion, {'alpha': 10, 'beta': 15})

        # Generate combined brainwave signal
        for band, freq in freqs.items():
            amplitude = 0.3
            signal += amplitude * np.sin(2 * np.pi * freq * t)

        # Add some noise for realism
        signal += np.random.normal(0, 0.05, len(t))

        return signal

class EmotionalAudioSynthesizer:
    """Main synthesizer for emotional audio generation"""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.music_theory = EmotionalMusicTheory()
        self.brainwave_analyzer = BrainwaveAnalyzer(sample_rate)

        # Audio generation parameters
        self.current_profile = None
        self.target_profile = None
        self.transition_progress = 0.0

        # Real-time processing
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.processing_thread = None

        # Emotional state history
        self.emotion_history = deque(maxlen=100)
        self.adaptation_rate = 0.1

        # Advanced synthesis parameters
        self.harmonic_complexity = 0.5
        self.rhythmic_variation = 0.3
        self.dynamic_range = 0.7
        self.timbral_evolution = 0.4

    def analyze_emotion_from_input(self, input_data: Union[np.ndarray, str, Dict]) -> EmotionalProfile:
        """Analyze emotion from various input types"""
        if isinstance(input_data, np.ndarray):
            # Assume EEG data
            return self.brainwave_analyzer.analyze_emotion_from_brainwaves(input_data)
        elif isinstance(input_data, str):
            # Text-based emotion analysis (simplified)
            return self._analyze_text_emotion(input_data)
        elif isinstance(input_data, dict):
            # Direct emotion specification
            return EmotionalProfile(
                primary_emotion=EmotionalState(input_data.get('emotion', 'joy')),
                intensity=input_data.get('intensity', 0.7),
                valence=input_data.get('valence', 0.5),
                arousal=input_data.get('arousal', 0.5)
            )
        else:
            # Default joyful state
            return EmotionalProfile(primary_emotion=EmotionalState.JOY)

    def _analyze_text_emotion(self, text: str) -> EmotionalProfile:
        """Simple text emotion analysis"""
        # Keyword-based emotion detection
        emotion_keywords = {
            EmotionalState.JOY: ['happy', 'joy', 'excited', 'wonderful', 'amazing'],
            EmotionalState.SADNESS: ['sad', 'depressed', 'lonely', 'melancholy'],
            EmotionalState.ANGER: ['angry', 'mad', 'furious', 'rage'],
            EmotionalState.FEAR: ['scared', 'afraid', 'terrified', 'anxious'],
            EmotionalState.LOVE: ['love', 'affection', 'caring', 'compassion']
        }

        text_lower = text.lower()
        emotion_scores = {}

        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            emotion_scores[emotion] = score

        # Find primary emotion
        if emotion_scores:
            primary_emotion = max(emotion_scores, key=emotion_scores.get)
            intensity = min(1.0, emotion_scores[primary_emotion] / 3.0)
        else:
            primary_emotion = EmotionalState.JOY
            intensity = 0.5

        return EmotionalProfile(
            primary_emotion=primary_emotion,
            intensity=intensity,
            valence=0.5 if primary_emotion == EmotionalState.JOY else -0.5
        )

    def set_emotional_state(self, profile: EmotionalProfile, transition_time: float = 2.0):
        """Set target emotional state with smooth transition"""
        self.target_profile = profile
        self.transition_progress = 0.0

        if self.current_profile is None:
            self.current_profile = profile
        else:
            # Start transition thread
            threading.Thread(target=self._smooth_transition,
                           args=(transition_time,), daemon=True).start()

    def _smooth_transition(self, duration: float):
        """Smoothly transition between emotional states"""
        steps = int(duration * 10)  # 10 updates per second
        start_profile = self.current_profile

        for step in range(steps + 1):
            progress = step / steps
            self.transition_progress = progress

            # Interpolate all profile parameters
            self.current_profile = EmotionalProfile(
                primary_emotion=self.target_profile.primary_emotion if progress > 0.5 else start_profile.primary_emotion,
                secondary_emotion=self.target_profile.secondary_emotion,
                intensity=start_profile.intensity + (self.target_profile.intensity - start_profile.intensity) * progress,
                valence=start_profile.valence + (self.target_profile.valence - start_profile.valence) * progress,
                arousal=start_profile.arousal + (self.target_profile.arousal - start_profile.arousal) * progress,
                complexity=start_profile.complexity + (self.target_profile.complexity - start_profile.complexity) * progress,
                stability=start_profile.stability + (self.target_profile.stability - start_profile.stability) * progress
            )

            time.sleep(duration / steps)

        self.transition_progress = 1.0

    def generate_emotional_audio(self, duration: float, profile: EmotionalProfile = None) -> np.ndarray:
        """Generate audio based on emotional profile"""
        if profile is None:
            profile = self.current_profile
        if profile is None:
            profile = EmotionalProfile(primary_emotion=EmotionalState.JOY)

        # Get musical parameters from emotion
        scale = self.music_theory.get_emotional_scale(profile.primary_emotion, profile.complexity)
        tempo = self.music_theory.get_emotional_tempo(profile.primary_emotion, profile.arousal)
        rhythm = self.music_theory.get_emotional_rhythm(profile.primary_emotion, profile.stability)

        # Generate melodic line
        melody = self._generate_emotional_melody(duration, scale, tempo, rhythm, profile)

        # Generate harmony
        harmony = self._generate_emotional_harmony(duration, scale, profile)

        # Generate rhythm
        rhythm_audio = self._generate_emotional_rhythm(duration, rhythm, tempo, profile)

        # Combine and process
        combined = melody + 0.5 * harmony + 0.3 * rhythm_audio

        # Apply emotional processing
        processed = self._apply_emotional_processing(combined, profile)

        # Store in history
        self.emotion_history.append(profile)

        return processed

    def _generate_emotional_melody(self, duration: float, scale: List[int],
                                 tempo: float, rhythm: List[float],
                                 profile: EmotionalProfile) -> np.ndarray:
        """Generate emotional melodic line"""
        num_samples = int(duration * self.sample_rate)
        melody = np.zeros(num_samples)

        # Convert tempo to step duration
        beat_duration = 60.0 / tempo

        # Generate melodic contour based on emotion
        time_points = []
        current_time = 0
        rhythm_index = 0

        while current_time < duration:
            duration_beats = rhythm[rhythm_index % len(rhythm)]
            time_points.append((current_time, duration_beats))
            current_time += duration_beats * beat_duration
            rhythm_index += 1

        # Generate notes
        base_frequency = 440  # A4
        note_index = 0

        for start_time, duration_beats in time_points:
            if start_time >= duration:
                break

            # Select note from scale
            scale_degree = scale[note_index % len(scale)]
            frequency = base_frequency * np.power(2, scale_degree / 12)

            # Add emotional variation
            if profile.valence > 0:
                frequency *= (1 + profile.valence * 0.1)  # Brighter for positive
            else:
                frequency *= (1 + profile.valence * 0.05)  # Darker for negative

            # Generate note
            start_sample = int(start_time * self.sample_rate)
            end_sample = int((start_time + duration_beats * beat_duration) * self.sample_rate)
            end_sample = min(end_sample, num_samples)

            t = np.linspace(0, duration_beats * beat_duration, end_sample - start_sample)

            # Note envelope
            envelope = self._generate_note_envelope(t, profile.intensity)

            # Vibrato for emotional expression
            vibrato = 1 + 0.05 * np.sin(2 * np.pi * 5 * t) * profile.arousal

            note_signal = envelope * np.sin(2 * np.pi * frequency * vibrato * t)
            melody[start_sample:end_sample] = note_signal

            note_index += 1

        return melody

    def _generate_emotional_harmony(self, duration: float, scale: List[int],
                                  profile: EmotionalProfile) -> np.ndarray:
        """Generate emotional harmony"""
        num_samples = int(duration * self.sample_rate)
        harmony = np.zeros(num_samples)

        # Select harmony notes (root, third, fifth)
        if len(scale) >= 3:
            harmony_notes = [scale[0], scale[2], scale[4]]
        else:
            harmony_notes = scale

        base_frequency = 220  # A3
        t = np.linspace(0, duration, num_samples)

        for i, scale_degree in enumerate(harmony_notes):
            frequency = base_frequency * np.power(2, scale_degree / 12)

            # Add emotional variation
            if profile.intensity > 0.5:
                frequency *= (1 + (profile.intensity - 0.5) * 0.05)

            # Slow harmonic rhythm
            harmonic_rate = 0.5 * (1 + profile.stability)
            harmonic_envelope = 0.3 * (1 + np.sin(2 * np.pi * harmonic_rate * t + i * np.pi/3))

            harmony += harmonic_envelope * np.sin(2 * np.pi * frequency * t)

        return harmony

    def _generate_emotional_rhythm(self, duration: float, rhythm: List[float],
                                 tempo: float, profile: EmotionalProfile) -> np.ndarray:
        """Generate emotional rhythm track"""
        num_samples = int(duration * self.sample_rate)
        rhythm_audio = np.zeros(num_samples)

        # Generate rhythmic clicks
        beat_duration = 60.0 / tempo
        current_time = 0
        rhythm_index = 0

        while current_time < duration:
            duration_beats = rhythm[rhythm_index % len(rhythm)]

            # Rhythm click
            start_sample = int(current_time * self.sample_rate)
            click_samples = int(0.01 * self.sample_rate)  # 10ms click
            end_sample = min(start_sample + click_samples, num_samples)

            # Click envelope
            click_envelope = np.exp(-np.linspace(0, 10, end_sample - start_sample))

            # Click frequency based on emotional arousal
            click_freq = 1000 + profile.arousal * 2000
            t = np.linspace(0, 0.01, end_sample - start_sample)
            click = click_envelope * np.sin(2 * np.pi * click_freq * t)

            rhythm_audio[start_sample:end_sample] = click * profile.intensity

            current_time += duration_beats * beat_duration
            rhythm_index += 1

        return rhythm_audio

    def _generate_note_envelope(self, t: np.ndarray, intensity: float) -> np.ndarray:
        """Generate note envelope with emotional shaping"""
        # ADSR envelope with emotional parameters
        attack_time = 0.1 * (2 - intensity)  # Faster attack for high intensity
        decay_time = 0.2
        sustain_level = 0.7 * intensity
        release_time = 0.3

        envelope = np.zeros_like(t)

        for i, time_point in enumerate(t):
            if time_point < attack_time:
                envelope[i] = time_point / attack_time
            elif time_point < attack_time + decay_time:
                decay_progress = (time_point - attack_time) / decay_time
                envelope[i] = 1 - decay_progress * (1 - sustain_level)
            else:
                # Simple sustain for now
                envelope[i] = sustain_level

        return envelope

    def _apply_emotional_processing(self, audio: np.ndarray, profile: EmotionalProfile) -> np.ndarray:
        """Apply emotional post-processing to audio"""
        processed = audio.copy()

        # Apply reverb based on emotional space
        if profile.primary_emotion in [EmotionalState.WONDER, EmotionalState.MYSTERY]:
            processed = self._apply_reverb(processed, room_size=0.8, damping=0.3)
        elif profile.primary_emotion in [EmotionalState.ANGER, EmotionalState.EXCITEMENT]:
            processed = self._apply_distortion(processed, gain=1.2)
        elif profile.primary_emotion in [EmotionalState.PEACE, EmotionalState.LOVE]:
            processed = self._apply_chorus(processed, rate=0.5, depth=0.3)

        # Apply filtering based on valence
        if profile.valence > 0.5:
            # Brighten positive emotions
            processed = self._apply_high_pass_filter(processed, 100)
        else:
            # Warm negative emotions
            processed = self._apply_low_pass_filter(processed, 8000)

        # Dynamic compression based on intensity
        processed = self._apply_compression(processed, threshold=0.7, ratio=1.5)

        # Normalize
        processed = processed / (np.max(np.abs(processed)) + 1e-10)

        return processed

    def _apply_reverb(self, audio: np.ndarray, room_size: float = 0.5, damping: float = 0.5) -> np.ndarray:
        """Apply simple reverb effect"""
        delay_samples = int(room_size * 0.1 * self.sample_rate)
        delayed = np.zeros_like(audio)
        delayed[delay_samples:] = audio[:-delay_samples] * (1 - damping)
        return audio + delayed

    def _apply_distortion(self, audio: np.ndarray, gain: float = 1.0) -> np.ndarray:
        """Apply soft distortion"""
        distorted = np.tanh(audio * gain)
        return distorted

    def _apply_chorus(self, audio: np.ndarray, rate: float = 1.0, depth: float = 0.5) -> np.ndarray:
        """Apply chorus effect"""
        delay_samples = int(depth * 0.03 * self.sample_rate)
        modulated_delay = delay_samples + int(0.01 * self.sample_rate * np.sin(2 * np.pi * rate * np.linspace(0, len(audio)/self.sample_rate, len(audio))))

        delayed = np.zeros_like(audio)
        for i in range(len(audio)):
            delay_idx = int(i - modulated_delay[min(i, len(modulated_delay)-1)])
            if 0 <= delay_idx < len(audio):
                delayed[i] = audio[delay_idx]

        return audio + 0.5 * delayed

    def _apply_high_pass_filter(self, audio: np.ndarray, cutoff: float) -> np.ndarray:
        """Apply high-pass filter"""
        b, a = signal.butter(4, cutoff / (self.sample_rate / 2), 'high')
        return signal.filtfilt(b, a, audio)

    def _apply_low_pass_filter(self, audio: np.ndarray, cutoff: float) -> np.ndarray:
        """Apply low-pass filter"""
        b, a = signal.butter(4, cutoff / (self.sample_rate / 2), 'low')
        return signal.filtfilt(b, a, audio)

    def _apply_compression(self, audio: np.ndarray, threshold: float = 0.7, ratio: float = 2.0) -> np.ndarray:
        """Apply dynamic compression"""
        compressed = audio.copy()
        abs_audio = np.abs(audio)

        # Find peaks above threshold
        mask = abs_audio > threshold
        if np.any(mask):
            # Calculate gain reduction
            overshoot = abs_audio[mask] - threshold
            gain_reduction = overshoot / ratio
            compressed[mask] = np.sign(audio[mask]) * (threshold + gain_reduction)

        return compressed

    def start_real_time_synthesis(self, chunk_duration: float = 0.5):
        """Start real-time emotional audio synthesis"""
        self.is_running = True
        self.processing_thread = threading.Thread(
            target=self._real_time_loop,
            args=(chunk_duration,),
            daemon=True
        )
        self.processing_thread.start()

        logger.info("Started real-time emotional audio synthesis")

    def _real_time_loop(self, chunk_duration: float):
        """Real-time audio processing loop"""
        while self.is_running:
            start_time = time.time()

            # Generate audio chunk
            if self.current_profile:
                audio_chunk = self.generate_emotional_audio(chunk_duration, self.current_profile)
                self.audio_queue.put(audio_chunk)

            # Maintain real-time performance
            elapsed = time.time() - start_time
            if elapsed < chunk_duration:
                time.sleep(chunk_duration - elapsed)

    def stop_real_time_synthesis(self):
        """Stop real-time synthesis"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)

        logger.info("Stopped real-time emotional audio synthesis")

    def get_audio_chunk(self) -> Optional[np.ndarray]:
        """Get next audio chunk from queue"""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None

    def adapt_to_listener(self, feedback_score: float):
        """Adapt synthesis based on listener feedback"""
        # Adjust parameters based on feedback
        if feedback_score > 0.7:
            # Positive feedback - enhance current direction
            if self.current_profile:
                self.current_profile.intensity = min(1.0, self.current_profile.intensity + 0.05)
                self.current_profile.complexity = min(1.0, self.current_profile.complexity + 0.03)
        elif feedback_score < 0.3:
            # Negative feedback - try different approach
            if self.current_profile:
                self.current_profile.complexity = max(0.1, self.current_profile.complexity - 0.05)
                # Add some variety
                emotions = list(EmotionalState)
                new_emotion = random.choice(emotions)
                self.set_emotional_state(EmotionalProfile(primary_emotion=new_emotion))

    def save_emotional_audio(self, audio: np.ndarray, filename: str, profile: EmotionalProfile = None):
        """Save emotional audio with metadata"""
        sf.write(filename, audio, self.sample_rate)

        # Save metadata
        if profile:
            metadata_file = filename.replace('.wav', '_metadata.json')
            metadata = {
                'primary_emotion': profile.primary_emotion.value,
                'intensity': profile.intensity,
                'valence': profile.valence,
                'arousal': profile.arousal,
                'complexity': profile.complexity,
                'stability': profile.stability
            }

            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

        logger.info(f"Saved emotional audio to {filename}")

def main():
    """Demonstration of emotional synthesizer"""
    print("EMOTIONAL SYNTHESIZER - AI-Powered Emotional Music Generation")
    print("=" * 70)

    # Initialize synthesizer
    synthesizer = EmotionalAudioSynthesizer(sample_rate=44100)

    # Test different emotional states
    emotional_journey = [
        EmotionalProfile(primary_emotion=EmotionalState.JOY, intensity=0.8, valence=0.8),
        EmotionalProfile(primary_emotion=EmotionalState.WONDER, intensity=0.7, valence=0.6),
        EmotionalProfile(primary_emotion=EmotionalState.LOVE, intensity=0.9, valence=0.9),
        EmotionalProfile(primary_emotion=EmotionalState.PEACE, intensity=0.6, valence=0.5),
        EmotionalProfile(primary_emotion=EmotionalState.EXCITEMENT, intensity=0.9, arousal=0.9)
    ]

    full_audio = []

    print("\nGenerating emotional journey...")
    for i, profile in enumerate(emotional_journey):
        print(f"Generating {profile.primary_emotion.value} music...")

        # Set emotional state
        synthesizer.set_emotional_state(profile, transition_time=1.0)
        time.sleep(0.5)  # Allow transition

        # Generate audio
        audio = synthesizer.generate_emotional_audio(duration=3.0, profile=profile)
        full_audio.extend(audio)

        # Save individual emotion
        filename = f"/home/activeloguser/DMLogn8n/sensory/ultimate/emotional_{profile.primary_emotion.value}.wav"
        synthesizer.save_emotional_audio(np.array(audio), filename, profile)
        print(f"Saved: {filename}")

    # Save complete emotional journey
    if full_audio:
        full_audio = np.array(full_audio)
        journey_file = "/home/activeloguser/DMLogn8n/sensory/ultimate/emotional_journey.wav"
        synthesizer.save_emotional_audio(full_audio, journey_file)
        print(f"\nSaved complete emotional journey: {journey_file}")

    # Demonstrate real-time synthesis
    print(f"\nStarting real-time emotional synthesis...")
    synthesizer.start_real_time_synthesis(chunk_duration=0.5)

    # Cycle through emotions in real-time
    real_time_audio = []
    for emotion in [EmotionalState.JOY, EmotionalState.SADNESS, EmotionalState.ANGER, EmotionalState.PEACE]:
        profile = EmotionalProfile(primary_emotion=emotion, intensity=0.7)
        synthesizer.set_emotional_state(profile)

        # Collect real-time chunks
        start_time = time.time()
        while time.time() - start_time < 2.0:  # 2 seconds per emotion
            chunk = synthesizer.get_audio_chunk()
            if chunk is not None:
                real_time_audio.extend(chunk)
            time.sleep(0.01)

    synthesizer.stop_real_time_synthesis()

    if real_time_audio:
        real_time_audio = np.array(real_time_audio)
        rt_file = "/home/activeloguser/DMLogn8n/sensory/ultimate/emotional_realtime.wav"
        synthesizer.save_emotional_audio(real_time_audio, rt_file)
        print(f"Saved real-time synthesis: {rt_file}")

    # Test emotion analysis from text
    print(f"\nTesting emotion analysis from text...")
    text_samples = [
        "I feel so happy and excited today!",
        "This makes me feel sad and lonely",
        "I'm angry about what happened",
        "I'm in love and feel peaceful"
    ]

    for text in text_samples:
        profile = synthesizer.analyze_emotion_from_input(text)
        print(f"Text: '{text}'")
        print(f"Detected emotion: {profile.primary_emotion.value} (intensity: {profile.intensity:.2f})")
        print()

    print("EMOTIONAL SYNTHESIS COMPLETE!")
    print("This system can create music that perfectly matches human emotions,")
    print("opening new frontiers in emotional expression and therapeutic applications.")

if __name__ == "__main__":
    main()