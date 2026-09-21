#!/usr/bin/env python3
"""
Memory BCI System - Memory Interface for Recording/Replaying Experiences
Advanced brain-computer interface for capturing, storing, and replaying neural
experiences, enabling users to record and relive memories within the game world.

This module implements sophisticated algorithms for detecting memory-related
neural patterns, creating a bidirectional memory interface between users and
the virtual environment.
"""

import numpy as np
import pandas as pd
import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import deque
import threading
from concurrent.futures import ThreadPoolExecutor
import queue
import pickle
import os
import sqlite3
from datetime import datetime, timedelta

# Machine Learning Libraries
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

# Signal Processing
from scipy import signal
from scipy.fft import fft, fftfreq
from scipy.stats import entropy
from scipy.spatial.distance import cosine
import cv2

# Local imports
from .neural_interface import ProcessedSignal, NeuralSignal
from .thought_detector import ThoughtPattern
from .emotional_bc import EmotionalPattern

class MemoryType(Enum):
    """Types of memories that can be recorded"""
    EPISODIC = "episodic"  # Personal experiences and events
    SEMANTIC = "semantic"  # Facts and knowledge
    PROCEDURAL = "procedural"  # Skills and how-to knowledge
    WORKING = "working"  # Short-term memory
    LONG_TERM = "long_term"  # Consolidated long-term memory
    SENSORY = "sensory"  # Sensory experiences
    EMOTIONAL = "emotional"  # Emotional memories
    SPATIAL = "spatial"  # Spatial navigation and locations
    DECLARATIVE = "declarative"  # Explicit memories
    IMPLICIT = "implicit"  # Unconscious memories

class MemoryOperation(Enum):
    """Memory operations"""
    RECORD = "record"
    REPLAY = "replay"
    RECALL = "recall"
    RECOGNIZE = "recognize"
    FORGET = "forget"
    CONSOLIDATE = "consolidate"
    REINFORCE = "reinforce"
    MODIFY = "modify"
    SEARCH = "search"
    ASSOCIATE = "associate"

class MemoryState(Enum):
    """Memory states during recording/replay"""
    ENCODING = "encoding"  # Recording new memory
    CONSOLIDATION = "consolidation"  # Strengthening memory
    RETRIEVAL = "retrieval"  # Recalling existing memory
    RECONSOLIDATION = "reconsolidation"  # Modifying existing memory
    DECAY = "decay"  # Memory weakening
    ENHANCEMENT = "enhancement"  # Memory strengthening

@dataclass
class MemorySignature:
    """Neural signature of a memory"""
    timestamp: float
    memory_type: MemoryType
    neural_pattern: np.ndarray
    frequency_features: Dict[str, float]
    connectivity_pattern: np.ndarray
    emotional_context: Optional[Dict[str, float]]
    spatial_context: Optional[Dict[str, Any]]
    semantic_tags: List[str]
    confidence: float
    duration: float
    metadata: Dict[str, Any]

@dataclass
class MemoryEngram:
    """Complete memory engram (memory trace)"""
    memory_id: str
    user_id: str
    created_at: float
    last_accessed: float
    memory_type: MemoryType
    title: str
    description: str
    signatures: List[MemorySignature]
    emotional_profile: Dict[str, float]
    importance_score: float
    retrieval_count: int
    associations: List[str]  # Associated memory IDs
    context_data: Dict[str, Any]
    replay_data: Optional[Dict[str, Any]]
    consolidation_level: float

@dataclass
class MemoryOperation:
    """Memory operation result"""
    timestamp: float
    operation_type: MemoryOperation
    memory_id: Optional[str]
    success: bool
    confidence: float
    neural_similarity: float
    emotional_match: float
    contextual_relevance: float
    response_data: Dict[str, Any]
    metadata: Dict[str, Any]

class MemoryFeatureExtractor:
    """Extract memory-relevant features from neural signals"""

    def __init__(self):
        self.frequency_bands = {
            'delta': (0.5, 4),
            'theta': (4, 8),
            'alpha': (8, 13),
            'beta': (13, 30),
            'gamma': (30, 100),
            'high_gamma': (100, 200)
        }
        self.memory_related_frequencies = {
            'theta_gamma_coupling': (4, 8, 40, 100),  # Memory encoding
            'spindle_activity': (11, 16),  # Memory consolidation
            'ripple_activity': (80, 250),  # Memory replay
        }

    def extract_memory_features(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Extract comprehensive memory features"""
        features = {}

        # Frequency-based memory indicators
        features.update(self._extract_frequency_memory_features(processed_signal))

        # Connectivity-based memory indicators
        features.update(self._extract_connectivity_memory_features(processed_signal))

        # Complexity-based memory indicators
        features.update(self._extract_complexity_memory_features(processed_signal))

        # Temporal dynamics for memory
        features.update(self._extract_temporal_memory_features(processed_signal))

        # Oscillatory coupling
        features.update(self._extract_oscillatory_coupling(processed_signal))

        return features

    def _extract_frequency_memory_features(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Extract frequency-based memory indicators"""
        brain_waves = processed_signal.brain_waves
        features = {}

        # Theta-gamma coupling indicator (memory encoding)
        theta_power = brain_waves.get('THETA', 0)
        gamma_power = brain_waves.get('GAMMA', 0)
        features['theta_gamma_ratio'] = gamma_power / (theta_power + 1e-10)
        features['theta_power'] = theta_power
        features['gamma_power'] = gamma_power

        # Alpha power (memory suppression/inhibition)
        alpha_power = brain_waves.get('ALPHA', 0)
        features['alpha_suppression'] = 1 - (alpha_power / (alpha_power + theta_power + 1e-10))

        # Beta power (working memory)
        beta_power = brain_waves.get('BETA', 0)
        features['working_memory_load'] = beta_power / (beta_power + alpha_power + 1e-10)

        # High gamma (memory retrieval)
        high_gamma = brain_waves.get('HIGH_GAMMA', 0)
        features['retrieval_strength'] = high_gamma / (high_gamma + beta_power + 1e-10)

        # Delta activity (consolidation)
        delta_power = brain_waves.get('DELTA', 0)
        features['consolidation_index'] = delta_power / (delta_power + theta_power + 1e-10)

        # Memory complexity index
        total_power = sum(brain_waves.values())
        if total_power > 0:
            power_ratios = [power/total_power for power in brain_waves.values()]
            features['memory_complexity'] = entropy(power_ratios + 1e-10)
        else:
            features['memory_complexity'] = 0

        # Memory encoding vs retrieval balance
        features['encoding_retrieval_balance'] = (theta_power + alpha_power) / (beta_power + gamma_power + 1e-10)

        return features

    def _extract_connectivity_memory_features(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Extract connectivity-based memory indicators"""
        signal_data = processed_signal.filtered_signal
        features = {}

        if signal_data.shape[1] > 1:
            # Functional connectivity (memory networks)
            coherence_matrix = []
            for i in range(min(6, signal_data.shape[1])):
                for j in range(i+1, min(6, signal_data.shape[1])):
                    f, Cxy = signal.coherence(
                        signal_data[:, i], signal_data[:, j],
                        fs=250, nperseg=128
                    )
                    coherence_matrix.append(np.mean(Cxy))

            if coherence_matrix:
                features['mean_connectivity'] = np.mean(coherence_matrix)
                features['connectivity_stability'] = 1 - np.std(coherence_matrix)
                features['memory_network_strength'] = np.mean([c for c in coherence_matrix if c > 0.5])

            # Phase synchronization (memory binding)
            analytic_signal = signal.hilbert(signal_data, axis=0)
            instantaneous_phase = np.unwrap(np.angle(analytic_signal), axis=0)

            phase_lock_values = []
            for i in range(min(4, signal_data.shape[1])):
                for j in range(i+1, min(4, signal_data.shape[1])):
                    phase_diff = instantaneous_phase[:, i] - instantaneous_phase[:, j]
                    plv = np.abs(np.mean(np.exp(1j * phase_diff)))
                    phase_lock_values.append(plv)

            if phase_lock_values:
                features['phase_synchronization'] = np.mean(phase_lock_values)
                features['memory_binding_strength'] = np.max(phase_lock_values)

            # Cross-frequency coupling
            theta_phase = self._extract_phase(signal_data, 4, 8)
            gamma_amplitude = self._extract_amplitude(signal_data, 40, 100)

            if theta_phase is not None and gamma_amplitude is not None:
                # Calculate modulation index
                coupling_strength = self._calculate_modulation_index(theta_phase, gamma_amplitude)
                features['theta_gamma_coupling'] = coupling_strength

        return features

    def _extract_complexity_memory_features(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Extract complexity-based memory indicators"""
        signal_data = processed_signal.filtered_signal
        features = {}

        # Sample entropy (memory stability)
        for ch in range(min(3, signal_data.shape[1])):
            entropy_val = self._sample_entropy(signal_data[:, ch])
            features[f'memory_entropy_ch_{ch}'] = entropy_val

        # Fractal dimension (memory complexity)
        for ch in range(min(3, signal_data.shape[1])):
            fd = self._fractal_dimension(signal_data[:, ch])
            features[f'memory_fractal_ch_{ch}'] = fd

        # Lempel-Ziv complexity (information content)
        for ch in range(min(2, signal_data.shape[1])):
            lz_complexity = self._lempel_ziv_complexity(signal_data[:, ch])
            features[f'memory_lz_complexity_ch_{ch}'] = lz_complexity

        # Memory organization (pattern regularity)
        if len(features) >= 3:
            entropy_values = [v for k, v in features.items() if 'memory_entropy' in k]
            features['memory_organization'] = 1 / (1 + np.std(entropy_values))

        return features

    def _extract_temporal_memory_features(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Extract temporal dynamics of memory processing"""
        signal_data = processed_signal.filtered_signal
        features = {}

        # Memory decay/growth patterns
        window_size = 50
        if len(signal_data) > window_size * 2:
            windows = [
                signal_data[i:i+window_size]
                for i in range(0, len(signal_data)-window_size, window_size//2)
            ]

            window_powers = [np.mean(np.var(window, axis=0)) for window in windows]
            if len(window_powers) > 1:
                # Calculate trend (positive = memory strengthening, negative = decay)
                trend = np.polyfit(range(len(window_powers)), window_powers, 1)[0]
                features['memory_trend'] = trend / (np.mean(window_powers) + 1e-10)

        # Memory consolidation patterns
        autocorr_values = []
        for ch in range(min(2, signal_data.shape[1])):
            autocorr = np.correlate(signal_data[:, ch], signal_data[:, ch], mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            if len(autocorr) > 10:
                autocorr_values.append(autocorr[5] / autocorr[0])  # 5-lag correlation

        if autocorr_values:
            features['memory_consistency'] = np.mean(autocorr_values)

        # Memory replay signatures
        replay_features = self._detect_replay_signatures(signal_data)
        features.update(replay_features)

        return features

    def _extract_oscillatory_coupling(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Extract oscillatory coupling features for memory"""
        signal_data = processed_signal.filtered_signal
        features = {}

        # Sleep spindle detection (memory consolidation)
        spindle_features = self._detect_sleep_spindles(signal_data)
        features.update(spindle_features)

        # Sharp-wave ripple detection (memory replay)
        ripple_features = self._detect_sharp_wave_ripples(signal_data)
        features.update(ripple_features)

        return features

    def _extract_phase(self, signal_data: np.ndarray, low_freq: float, high_freq: float) -> Optional[np.ndarray]:
        """Extract instantaneous phase from frequency band"""
        try:
            # Bandpass filter
            nyquist = 250 / 2
            if high_freq < nyquist:
                b, a = signal.butter(4, [low_freq/nyquist, high_freq/nyquist], btype='band')
                filtered = signal.filtfilt(b, a, signal_data, axis=0)

                # Extract phase using Hilbert transform
                analytic_signal = signal.hilbert(filtered, axis=0)
                instantaneous_phase = np.unwrap(np.angle(analytic_signal), axis=0)

                return instantaneous_phase
        except Exception as e:
            logging.warning(f"Phase extraction failed: {e}")

        return None

    def _extract_amplitude(self, signal_data: np.ndarray, low_freq: float, high_freq: float) -> Optional[np.ndarray]:
        """Extract instantaneous amplitude from frequency band"""
        try:
            # Bandpass filter
            nyquist = 250 / 2
            if high_freq < nyquist:
                b, a = signal.butter(4, [low_freq/nyquist, high_freq/nyquist], btype='band')
                filtered = signal.filtfilt(b, a, signal_data, axis=0)

                # Extract amplitude using Hilbert transform
                analytic_signal = signal.hilbert(filtered, axis=0)
                instantaneous_amplitude = np.abs(analytic_signal)

                return instantaneous_amplitude
        except Exception as e:
            logging.warning(f"Amplitude extraction failed: {e}")

        return None

    def _calculate_modulation_index(self, phase: np.ndarray, amplitude: np.ndarray) -> float:
        """Calculate phase-amplitude coupling modulation index"""
        try:
            if phase is None or amplitude is None:
                return 0.0

            # Bin phase and calculate mean amplitude per bin
            n_bins = 18
            phase_bins = np.linspace(-np.pi, np.pi, n_bins + 1)
            binned_amplitude = []

            for i in range(n_bins):
                mask = (phase >= phase_bins[i]) & (phase < phase_bins[i + 1])
                if np.any(mask):
                    binned_amplitude.append(np.mean(amplitude[mask]))
                else:
                    binned_amplitude.append(0)

            binned_amplitude = np.array(binned_amplitude)

            # Calculate modulation index (Kullback-Leibler divergence)
            p = binned_amplitude / (np.sum(binned_amplitude) + 1e-10)
            q = np.ones(len(p)) / len(p)  # Uniform distribution

            # KL divergence
            mi = np.sum(p * np.log((p + 1e-10) / (q + 1e-10)))

            # Normalize by log(n_bins)
            mi_normalized = mi / np.log(len(p))

            return mi_normalized

        except Exception as e:
            logging.warning(f"Modulation index calculation failed: {e}")
            return 0.0

    def _detect_replay_signatures(self, signal_data: np.ndarray) -> Dict[str, float]:
        """Detect memory replay signatures in neural signal"""
        features = {}

        # Look for high-frequency bursts (sharp-wave ripples)
        high_freq_power = self._band_power(signal_data, 80, 250)
        features['ripple_power'] = high_freq_power

        # Look for temporal compression patterns
        temporal_compression = self._calculate_temporal_compression(signal_data)
        features['temporal_compression'] = temporal_compression

        return features

    def _detect_sleep_spindles(self, signal_data: np.ndarray) -> Dict[str, float]:
        """Detect sleep spindle activity (memory consolidation)"""
        features = {}

        # Spindle frequency band (11-16 Hz)
        spindle_power = self._band_power(signal_data, 11, 16)
        features['spindle_activity'] = spindle_power

        # Spindle density (number of spindle events per time)
        spindle_events = self._count_spindle_events(signal_data)
        duration_seconds = signal_data.shape[0] / 250
        features['spindle_density'] = spindle_events / duration_seconds

        return features

    def _detect_sharp_wave_ripples(self, signal_data: np.ndarray) -> Dict[str, float]:
        """Detect sharp-wave ripple activity (memory replay)"""
        features = {}

        # Ripple frequency band (80-250 Hz)
        ripple_power = self._band_power(signal_data, 80, 250)
        features['ripple_activity'] = ripple_power

        # Sharp-wave detection (low-frequency component)
        sharp_wave_power = self._band_power(signal_data, 0.5, 5)
        features['sharp_wave_activity'] = sharp_wave_power

        # Co-occurrence of sharp waves and ripples
        features['sharp_wave_ripple_coupling'] = (
            sharp_wave_power * ripple_power / (sharp_wave_power + ripple_power + 1e-10)
        )

        return features

    def _band_power(self, signal_data: np.ndarray, low_freq: float, high_freq: float) -> float:
        """Calculate power in specific frequency band"""
        try:
            sampling_rate = 250
            fft_vals = fft(signal_data, axis=0)
            freqs = fftfreq(signal_data.shape[0], 1/sampling_rate)
            power_spectrum = np.abs(fft_vals) ** 2

            # Find frequency indices for band
            band_indices = np.where((freqs >= low_freq) & (freqs <= high_freq))[0]
            if len(band_indices) > 0:
                return np.mean(power_spectrum[band_indices])
        except Exception as e:
            logging.warning(f"Band power calculation failed: {e}")

        return 0.0

    def _count_spindle_events(self, signal_data: np.ndarray) -> int:
        """Count spindle events in signal"""
        try:
            # Apply spindle band filter
            nyquist = 250 / 2
            b, a = signal.butter(4, [11/nyquist, 16/nyquist], btype='band')
            spindle_signal = signal.filtfilt(b, a, signal_data, axis=0)

            # Calculate envelope
            envelope = np.abs(signal.hilbert(spindle_signal, axis=0))

            # Threshold for spindle detection
            threshold = np.mean(envelope) + 2 * np.std(envelope)

            # Find events above threshold
            events = 0
            above_threshold = envelope > threshold

            # Count separate events
            for ch in range(min(2, signal_data.shape[1])):
                channel_events = 0
                in_event = False
                for point in above_threshold[:, ch]:
                    if point and not in_event:
                        channel_events += 1
                        in_event = True
                    elif not point:
                        in_event = False
                events += channel_events

            return events

        except Exception as e:
            logging.warning(f"Spindle event counting failed: {e}")
            return 0

    def _calculate_temporal_compression(self, signal_data: np.ndarray) -> float:
        """Calculate temporal compression in neural patterns"""
        try:
            # Divide signal into segments and calculate similarity
            segment_length = 50
            if signal_data.shape[0] < segment_length * 3:
                return 0.0

            segments = []
            for i in range(0, signal_data.shape[0] - segment_length, segment_length//2):
                segment = signal_data[i:i+segment_length]
                segments.append(np.mean(segment, axis=0))

            if len(segments) < 2:
                return 0.0

            # Calculate pairwise similarities
            similarities = []
            for i in range(len(segments)):
                for j in range(i+1, len(segments)):
                    similarity = 1 - cosine(segments[i], segments[j] + 1e-10)
                    similarities.append(similarity)

            # Temporal compression indicated by high similarity
            return np.mean(similarities) if similarities else 0.0

        except Exception as e:
            logging.warning(f"Temporal compression calculation failed: {e}")
            return 0.0

    def _sample_entropy(self, signal: np.ndarray, m: int = 2, r: float = None) -> float:
        """Calculate sample entropy"""
        if r is None:
            r = 0.2 * np.std(signal)

        N = len(signal)
        if N < m + 1:
            return 0

        def _count_matches(data, m):
            patterns = [data[i:i+m] for i in range(N-m+1)]
            matches = 0
            for i in range(len(patterns)):
                for j in range(i+1, len(patterns)):
                    if np.max(np.abs(patterns[i] - patterns[j])) <= r:
                        matches += 1
            return matches

        B = _count_matches(signal, m)
        A = _count_matches(signal, m+1)

        if B == 0 or A == 0:
            return 0

        return -np.log(A / B)

    def _fractal_dimension(self, signal: np.ndarray) -> float:
        """Calculate fractal dimension using Higuchi's method"""
        N = len(signal)
        k_max = min(10, N // 4)

        if k_max < 2:
            return 1.0

        L = []
        for k in range(1, k_max + 1):
            Lk = 0
            for m in range(k):
                indices = np.arange(1, int(np.floor((N - m) / k)), dtype=int) * k + m
                if len(indices) < 2:
                    continue
                sum_diff = np.sum(np.abs(np.diff(signal[indices])))
                Lk += sum_diff * (N - 1) / ((len(indices) - 1) * k)

            if k > 0:
                L.append(Lk / k)

        if len(L) < 2:
            return 1.0

        k_vals = np.arange(1, len(L) + 1)
        coeffs = np.polyfit(np.log(k_vals), np.log(L), 1)
        return coeffs[0]

    def _lempel_ziv_complexity(self, signal: np.ndarray) -> float:
        """Calculate Lempel-Ziv complexity"""
        # Convert signal to binary (above/below mean)
        binary_signal = (signal > np.mean(signal)).astype(int)
        binary_str = ''.join(binary_signal.astype(str))

        # Lempel-Ziv algorithm
        n = len(binary_str)
        complexity = 0
        i = 0
        vocabulary = set()

        while i < n:
            # Find longest new substring
            longest_new = ""
            for j in range(i + 1, n + 1):
                substring = binary_str[i:j]
                if substring not in vocabulary:
                    longest_new = substring
                    break

            if longest_new:
                vocabulary.add(longest_new)
                complexity += 1
                i += len(longest_new)
            else:
                i += 1

        # Normalize complexity
        if n > 0:
            complexity = complexity / n

        return complexity

class MemoryClassifier:
    """Memory classification and detection system"""

    def __init__(self):
        self.feature_extractor = MemoryFeatureExtractor()
        self.memory_types = [mt.value for mt in MemoryType]
        self.models = self._initialize_models()
        self.scalers = {}
        self.is_trained = False

    def _initialize_models(self) -> Dict[str, Any]:
        """Initialize memory classification models"""
        return {
            'memory_type_classifier': self._build_memory_type_model(),
            'memory_strength_estimator': self._build_strength_model(),
            'novelty_detector': self._build_novelty_model()
        }

    def _build_memory_type_model(self) -> keras.Model:
        """Build model for memory type classification"""
        # Determine input size
        dummy_signal = self._create_dummy_signal()
        dummy_features = self.feature_extractor.extract_memory_features(dummy_signal)
        input_size = len(dummy_features)

        model = keras.Sequential([
            layers.Input(shape=(input_size,)),
            layers.Dense(128, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            layers.Dense(64, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(len(self.memory_types), activation='softmax')
        ])

        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )

        return model

    def _build_strength_model(self) -> keras.Model:
        """Build model for memory strength estimation"""
        dummy_signal = self._create_dummy_signal()
        dummy_features = self.feature_extractor.extract_memory_features(dummy_signal)
        input_size = len(dummy_features)

        model = keras.Sequential([
            layers.Input(shape=(input_size,)),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(16, activation='relu'),
            layers.Dense(1, activation='sigmoid')  # 0 to 1 strength
        ])

        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model

    def _build_novelty_model(self) -> keras.Model:
        """Build autoencoder for novelty detection"""
        dummy_signal = self._create_dummy_signal()
        dummy_features = self.feature_extractor.extract_memory_features(dummy_signal)
        input_size = len(dummy_features)

        # Autoencoder architecture
        encoder = keras.Sequential([
            layers.Input(shape=(input_size,)),
            layers.Dense(64, activation='relu'),
            layers.Dense(32, activation='relu'),
            layers.Dense(16, activation='relu')  # Latent representation
        ])

        decoder = keras.Sequential([
            layers.Input(shape=(16,)),
            layers.Dense(32, activation='relu'),
            layers.Dense(64, activation='relu'),
            layers.Dense(input_size, activation='linear')
        ])

        autoencoder = keras.Model(inputs=encoder.input, outputs=decoder(encoder.output))
        autoencoder.compile(optimizer='adam', loss='mse')

        return {
            'autoencoder': autoencoder,
            'encoder': encoder,
            'decoder': decoder
        }

    def _create_dummy_signal(self) -> ProcessedSignal:
        """Create dummy processed signal"""
        from .neural_interface import BrainWave

        dummy_data = np.random.randn(250, 8)
        brain_waves = {wave.name.lower(): np.random.rand() for wave in BrainWave}

        return ProcessedSignal(
            timestamp=time.time(),
            raw_signal=dummy_data,
            filtered_signal=dummy_data,
            features={},
            brain_waves=brain_waves,
            signal_quality=0.8,
            noise_level=0.1
        )

    def train(self, training_data: List[Tuple[ProcessedSignal, MemoryType, float]]) -> Dict[str, Any]:
        """Train memory classification models"""
        training_results = {}

        # Extract features and labels
        X = []
        y_types = []
        y_strengths = []

        for signal, memory_type, strength in training_data:
            features = self.feature_extractor.extract_memory_features(signal)
            X.append(features)
            y_types.append(memory_type.value)
            y_strengths.append(strength)

        X = np.array(X)
        y_types_array = np.array(y_types)
        y_strengths_array = np.array(y_strengths)

        # Encode memory types
        self.type_encoder = LabelEncoder()
        y_types_encoded = self.type_encoder.fit_transform(y_types_array)
        y_types_categorical = keras.utils.to_categorical(y_types_encoded)

        # Split data
        X_train, X_val, y_train, y_val, y_strength_train, y_strength_val = train_test_split(
            X, y_types_encoded, y_strengths_array,
            test_size=0.2, random_state=42, stratify=y_types_encoded
        )

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        self.scalers['features'] = scaler

        # Train memory type classifier
        print("Training memory type classifier...")
        history_type = self.models['memory_type_classifier'].fit(
            X_train_scaled, keras.utils.to_categorical(y_train),
            validation_data=(X_val_scaled, keras.utils.to_categorical(y_val)),
            epochs=50,
            batch_size=32,
            callbacks=[
                keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True)
            ],
            verbose=1
        )
        training_results['memory_type'] = history_type.history

        # Train memory strength estimator
        print("Training memory strength estimator...")
        history_strength = self.models['memory_strength_estimator'].fit(
            X_train_scaled, y_strength_train,
            validation_data=(X_val_scaled, y_strength_val),
            epochs=50,
            batch_size=32,
            callbacks=[
                keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True)
            ],
            verbose=1
        )
        training_results['memory_strength'] = history_strength.history

        # Train novelty detector (autoencoder)
        print("Training novelty detector...")
        history_novelty = self.models['novelty_detector']['autoencoder'].fit(
            X_train_scaled, X_train_scaled,
            validation_data=(X_val_scaled, X_val_scaled),
            epochs=100,
            batch_size=32,
            callbacks=[
                keras.callbacks.EarlyStopping(patience=15, restore_best_weights=True)
            ],
            verbose=1
        )
        training_results['novelty'] = history_novelty.history

        self.is_trained = True
        return training_results

    def classify_memory(self, processed_signal: ProcessedSignal) -> Tuple[MemoryType, float, float]:
        """Classify memory type and strength"""
        if not self.is_trained:
            raise RuntimeError("Models must be trained before classification")

        # Extract features
        features = self.feature_extractor.extract_memory_features(processed_signal)
        features_array = np.array([features])

        # Scale features
        features_scaled = self.scalers['features'].transform(features_array)

        # Classify memory type
        type_probs = self.models['memory_type_classifier'].predict(features_scaled, verbose=0)[0]
        type_idx = np.argmax(type_probs)
        type_confidence = type_probs[type_idx]
        memory_type = MemoryType(self.type_encoder.inverse_transform([type_idx])[0])

        # Estimate memory strength
        strength = self.models['memory_strength_estimator'].predict(features_scaled, verbose=0)[0][0]
        strength = np.clip(strength, 0, 1)

        return memory_type, type_confidence, strength

    def detect_novelty(self, processed_signal: ProcessedSignal) -> float:
        """Detect novelty of memory pattern"""
        if not self.is_trained:
            return 0.5  # Default medium novelty

        # Extract features
        features = self.feature_extractor.extract_memory_features(processed_signal)
        features_array = np.array([features])

        # Scale features
        features_scaled = self.scalers['features'].transform(features_array)

        # Reconstruct with autoencoder
        reconstructed = self.models['novelty_detector']['autoencoder'].predict(features_scaled, verbose=0)

        # Calculate reconstruction error
        reconstruction_error = np.mean((features_scaled - reconstructed) ** 2)

        # Normalize novelty score (higher error = more novel)
        novelty_score = np.tanh(reconstruction_error * 10)  # Scale and squash to 0-1

        return float(novelty_score)

    def save_models(self, directory: str):
        """Save trained models"""
        import os
        os.makedirs(directory, exist_ok=True)

        # Save Keras models
        self.models['memory_type_classifier'].save(os.path.join(directory, 'memory_type_model.h5'))
        self.models['memory_strength_estimator'].save(os.path.join(directory, 'memory_strength_model.h5'))
        self.models['novelty_detector']['autoencoder'].save(os.path.join(directory, 'novelty_autoencoder.h5'))

        # Save metadata
        import pickle
        metadata = {
            'memory_types': self.memory_types,
            'is_trained': self.is_trained,
            'type_encoder': self.type_encoder
        }

        with open(os.path.join(directory, 'metadata.pkl'), 'wb') as f:
            pickle.dump(metadata, f)

        # Save scalers
        with open(os.path.join(directory, 'scalers.pkl'), 'wb') as f:
            pickle.dump(self.scalers, f)

    def load_models(self, directory: str):
        """Load trained models"""
        import os
        import pickle

        # Load Keras models
        self.models['memory_type_classifier'] = keras.models.load_model(os.path.join(directory, 'memory_type_model.h5'))
        self.models['memory_strength_estimator'] = keras.models.load_model(os.path.join(directory, 'memory_strength_model.h5'))
        self.models['novelty_detector']['autoencoder'] = keras.models.load_model(os.path.join(directory, 'novelty_autoencoder.h5'))

        # Load metadata
        with open(os.path.join(directory, 'metadata.pkl'), 'rb') as f:
            metadata = pickle.load(f)

        self.type_encoder = metadata['type_encoder']
        self.is_trained = metadata['is_trained']

        # Load scalers
        with open(os.path.join(directory, 'scalers.pkl'), 'rb') as f:
            self.scalers = pickle.load(f)

class MemoryDatabase:
    """Database for storing and retrieving memory engrams"""

    def __init__(self, db_path: str = "memory_database.db"):
        self.db_path = db_path
        self.connection = None
        self._initialize_database()

    def _initialize_database(self):
        """Initialize database tables"""
        self.connection = sqlite3.connect(self.db_path)
        cursor = self.connection.cursor()

        # Create memory engrams table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_engrams (
                memory_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at REAL NOT NULL,
                last_accessed REAL NOT NULL,
                memory_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                emotional_profile TEXT,
                importance_score REAL,
                retrieval_count INTEGER DEFAULT 0,
                consolidation_level REAL DEFAULT 0.0,
                context_data TEXT,
                replay_data TEXT
            )
        ''')

        # Create memory signatures table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_signatures (
                signature_id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                neural_pattern BLOB,
                frequency_features TEXT,
                connectivity_pattern BLOB,
                emotional_context TEXT,
                spatial_context TEXT,
                semantic_tags TEXT,
                confidence REAL,
                duration REAL,
                metadata TEXT,
                FOREIGN KEY (memory_id) REFERENCES memory_engrams (memory_id)
            )
        ''')

        # Create memory associations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_associations (
                association_id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id_1 TEXT NOT NULL,
                memory_id_2 TEXT NOT NULL,
                association_strength REAL,
                association_type TEXT,
                created_at REAL NOT NULL,
                FOREIGN KEY (memory_id_1) REFERENCES memory_engrams (memory_id),
                FOREIGN KEY (memory_id_2) REFERENCES memory_engrams (memory_id)
            )
        ''')

        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_user ON memory_engrams (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_engrams (memory_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_engrams (created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_signature_memory ON memory_signatures (memory_id)')

        self.connection.commit()

    def store_memory_engram(self, engram: MemoryEngram) -> bool:
        """Store a memory engram in the database"""
        try:
            cursor = self.connection.cursor()

            # Store main engram
            cursor.execute('''
                INSERT OR REPLACE INTO memory_engrams
                (memory_id, user_id, created_at, last_accessed, memory_type, title,
                 description, emotional_profile, importance_score, retrieval_count,
                 consolidation_level, context_data, replay_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                engram.memory_id,
                engram.user_id,
                engram.created_at,
                engram.last_accessed,
                engram.memory_type.value,
                engram.title,
                engram.description,
                json.dumps(engram.emotional_profile),
                engram.importance_score,
                engram.retrieval_count,
                engram.consolidation_level,
                json.dumps(engram.context_data),
                json.dumps(engram.replay_data) if engram.replay_data else None
            ))

            # Store signatures
            for signature in engram.signatures:
                cursor.execute('''
                    INSERT INTO memory_signatures
                    (memory_id, timestamp, neural_pattern, frequency_features,
                     connectivity_pattern, emotional_context, spatial_context,
                     semantic_tags, confidence, duration, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    engram.memory_id,
                    signature.timestamp,
                    pickle.dumps(signature.neural_pattern),
                    json.dumps(signature.frequency_features),
                    pickle.dumps(signature.connectivity_pattern),
                    json.dumps(signature.emotional_context),
                    json.dumps(signature.spatial_context),
                    json.dumps(signature.semantic_tags),
                    signature.confidence,
                    signature.duration,
                    json.dumps(signature.metadata)
                ))

            # Store associations
            for associated_id in engram.associations:
                cursor.execute('''
                    INSERT INTO memory_associations
                    (memory_id_1, memory_id_2, association_strength, association_type, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    engram.memory_id,
                    associated_id,
                    0.5,  # Default association strength
                    'auto',  # Default association type
                    time.time()
                ))

            self.connection.commit()
            return True

        except Exception as e:
            logging.error(f"Failed to store memory engram: {e}")
            self.connection.rollback()
            return False

    def retrieve_memory_engram(self, memory_id: str) -> Optional[MemoryEngram]:
        """Retrieve a memory engram from the database"""
        try:
            cursor = self.connection.cursor()

            # Get main engram data
            cursor.execute('''
                SELECT memory_id, user_id, created_at, last_accessed, memory_type,
                       title, description, emotional_profile, importance_score,
                       retrieval_count, consolidation_level, context_data, replay_data
                FROM memory_engrams
                WHERE memory_id = ?
            ''', (memory_id,))

            row = cursor.fetchone()
            if not row:
                return None

            # Get signatures
            cursor.execute('''
                SELECT timestamp, neural_pattern, frequency_features, connectivity_pattern,
                       emotional_context, spatial_context, semantic_tags, confidence,
                       duration, metadata
                FROM memory_signatures
                WHERE memory_id = ?
                ORDER BY timestamp
            ''', (memory_id,))

            signature_rows = cursor.fetchall()
            signatures = []

            for sig_row in signature_rows:
                signature = MemorySignature(
                    timestamp=sig_row[0],
                    memory_type=MemoryType(row[4]),  # Will be updated below
                    neural_pattern=pickle.loads(sig_row[1]),
                    frequency_features=json.loads(sig_row[2]),
                    connectivity_pattern=pickle.loads(sig_row[3]),
                    emotional_context=json.loads(sig_row[4]) if sig_row[4] else None,
                    spatial_context=json.loads(sig_row[5]) if sig_row[5] else None,
                    semantic_tags=json.loads(sig_row[6]) if sig_row[6] else [],
                    confidence=sig_row[7],
                    duration=sig_row[8],
                    metadata=json.loads(sig_row[9]) if sig_row[9] else {}
                )
                signatures.append(signature)

            # Get associations
            cursor.execute('''
                SELECT memory_id_2
                FROM memory_associations
                WHERE memory_id_1 = ?
            ''', (memory_id,))

            association_rows = cursor.fetchall()
            associations = [row[0] for row in association_rows]

            # Update last accessed time
            cursor.execute('''
                UPDATE memory_engrams
                SET last_accessed = ?, retrieval_count = retrieval_count + 1
                WHERE memory_id = ?
            ''', (time.time(), memory_id))

            self.connection.commit()

            # Create engram object
            engram = MemoryEngram(
                memory_id=row[0],
                user_id=row[1],
                created_at=row[2],
                last_accessed=row[3],
                memory_type=MemoryType(row[4]),
                title=row[5],
                description=row[6] if row[6] else "",
                signatures=signatures,
                emotional_profile=json.loads(row[7]) if row[7] else {},
                importance_score=row[8],
                retrieval_count=row[9] + 1,  # Increment for this access
                associations=associations,
                context_data=json.loads(row[11]) if row[11] else {},
                replay_data=json.loads(row[12]) if row[12] else None,
                consolidation_level=row[10]
            )

            return engram

        except Exception as e:
            logging.error(f"Failed to retrieve memory engram: {e}")
            return None

    def search_memories(self, user_id: str, memory_type: MemoryType = None,
                       limit: int = 10) -> List[str]:
        """Search for memories matching criteria"""
        try:
            cursor = self.connection.cursor()

            query = '''
                SELECT memory_id FROM memory_engrams
                WHERE user_id = ?
            '''
            params = [user_id]

            if memory_type:
                query += ' AND memory_type = ?'
                params.append(memory_type.value)

            query += ' ORDER BY importance_score DESC, last_accessed DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [row[0] for row in rows]

        except Exception as e:
            logging.error(f"Memory search failed: {e}")
            return []

    def get_similar_memories(self, memory_signature: MemorySignature,
                           user_id: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Find memories with similar neural signatures"""
        try:
            cursor = self.connection.cursor()

            # Get all signatures for user
            cursor.execute('''
                SELECT memory_id, neural_pattern, frequency_features
                FROM memory_signatures
                WHERE memory_id IN (
                    SELECT memory_id FROM memory_engrams WHERE user_id = ?
                )
            ''', (user_id,))

            rows = cursor.fetchall()
            similarities = []

            for row in rows:
                other_memory_id = row[0]
                other_pattern = pickle.loads(row[1])
                other_features = json.loads(row[2])

                # Calculate similarity
                pattern_similarity = 1 - cosine(
                    memory_signature.neural_pattern.flatten(),
                    other_pattern.flatten()
                )

                # Feature similarity
                feature_similarity = self._calculate_feature_similarity(
                    memory_signature.frequency_features,
                    other_features
                )

                # Combined similarity
                combined_similarity = (pattern_similarity + feature_similarity) / 2
                similarities.append((other_memory_id, combined_similarity))

            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:limit]

        except Exception as e:
            logging.error(f"Similar memory search failed: {e}")
            return []

    def _calculate_feature_similarity(self, features1: Dict[str, float],
                                    features2: Dict[str, float]) -> float:
        """Calculate similarity between feature dictionaries"""
        common_keys = set(features1.keys()) & set(features2.keys())
        if not common_keys:
            return 0.0

        similarities = []
        for key in common_keys:
            val1 = features1.get(key, 0)
            val2 = features2.get(key, 0)
            if val1 == 0 and val2 == 0:
                similarities.append(1.0)
            else:
                similarity = 1 - abs(val1 - val2) / (abs(val1) + abs(val2) + 1e-10)
                similarities.append(similarity)

        return np.mean(similarities)

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()

class MemoryBCI:
    """Main memory BCI system"""

    def __init__(self, db_path: str = "memory_database.db",
                 model_directory: str = "memory_models"):
        self.db = MemoryDatabase(db_path)
        self.classifier = MemoryClassifier()
        self.model_directory = model_directory
        self.is_initialized = False

        # Real-time processing
        self.memory_queue = asyncio.Queue()
        self.operation_queue = asyncio.Queue()
        self.is_running = False

        # Current recording state
        self.recording_active = False
        self.current_memory_id = None
        self.current_signatures = []

        # Callbacks
        self.memory_callbacks = []
        self.operation_callbacks = []

        # Metrics
        self.metrics = {
            'memories_recorded': 0,
            'memories_retrieved': 0,
            'recording_time': 0,
            'retrieval_time': 0,
            'memory_types': {},
            'average_confidence': deque(maxlen=100),
            'operation_success_rate': deque(maxlen=100)
        }

        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> bool:
        """Initialize the memory BCI system"""
        try:
            # Try to load existing models
            if os.path.exists(self.model_directory):
                try:
                    self.classifier.load_models(self.model_directory)
                    self.logger.info("Loaded existing memory models")
                except Exception as e:
                    self.logger.warning(f"Could not load existing models: {e}")
                    self.classifier.is_trained = False

            self.is_initialized = True
            self.logger.info("Memory BCI system initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize memory BCI: {e}")
            return False

    async def train_classifier(self, training_data: List[Tuple[ProcessedSignal, MemoryType, float]]) -> bool:
        """Train the memory classifier"""
        try:
            if not self.is_initialized:
                await self.initialize()

            if len(training_data) < 20:
                self.logger.error("Insufficient training data (minimum 20 samples)")
                return False

            # Train classifier
            self.logger.info(f"Training memory classifier with {len(training_data)} samples")
            training_results = self.classifier.train(training_data)

            # Save trained models
            self.classifier.save_models(self.model_directory)

            self.logger.info("Memory classifier training completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Training failed: {e}")
            return False

    async def start_memory_recording(self, user_id: str, memory_type: MemoryType,
                                   title: str, description: str = "") -> Optional[str]:
        """Start recording a new memory"""
        if self.recording_active:
            self.logger.warning("Memory recording already active")
            return None

        try:
            # Generate unique memory ID
            memory_id = f"memory_{user_id}_{int(time.time())}_{np.random.randint(1000, 9999)}"

            # Initialize recording state
            self.recording_active = True
            self.current_memory_id = memory_id
            self.current_signatures = []
            self.recording_start_time = time.time()

            self.logger.info(f"Started recording memory: {memory_id} ({memory_type.value})")

            # Create initial engram entry (will be updated when recording stops)
            initial_engram = MemoryEngram(
                memory_id=memory_id,
                user_id=user_id,
                created_at=time.time(),
                last_accessed=time.time(),
                memory_type=memory_type,
                title=title,
                description=description,
                signatures=[],
                emotional_profile={},
                importance_score=0.5,
                retrieval_count=0,
                associations=[],
                context_data={},
                replay_data=None,
                consolidation_level=0.0
            )

            # Store initial engram
            success = self.db.store_memory_engram(initial_engram)
            if not success:
                self.recording_active = False
                self.current_memory_id = None
                return None

            return memory_id

        except Exception as e:
            self.logger.error(f"Failed to start memory recording: {e}")
            self.recording_active = False
            self.current_memory_id = None
            return None

    async def stop_memory_recording(self) -> Optional[str]:
        """Stop current memory recording and save the engram"""
        if not self.recording_active or not self.current_memory_id:
            self.logger.warning("No active memory recording")
            return None

        try:
            self.recording_active = False
            recording_duration = time.time() - self.recording_start_time

            # Retrieve the initial engram
            engram = self.db.retrieve_memory_engram(self.current_memory_id)
            if not engram:
                self.logger.error("Could not retrieve engram for finalization")
                return None

            # Update engram with collected signatures
            engram.signatures = self.current_signatures.copy()

            # Calculate importance score based on recording quality
            if self.current_signatures:
                avg_confidence = np.mean([sig.confidence for sig in self.current_signatures])
                engram.importance_score = min(1.0, avg_confidence * (recording_duration / 10.0))  # Normalize by duration

            # Update metrics
            self.metrics['memories_recorded'] += 1
            self.metrics['recording_time'] += recording_duration
            memory_type = engram.memory_type.value
            self.metrics['memory_types'][memory_type] = self.metrics['memory_types'].get(memory_type, 0) + 1

            # Store updated engram
            success = self.db.store_memory_engram(engram)

            # Reset recording state
            memory_id = self.current_memory_id
            self.current_memory_id = None
            self.current_signatures = []

            self.logger.info(f"Stopped recording memory: {memory_id} (duration: {recording_duration:.2f}s)")

            return memory_id if success else None

        except Exception as e:
            self.logger.error(f"Failed to stop memory recording: {e}")
            self.recording_active = False
            self.current_memory_id = None
            self.current_signatures = []
            return None

    async def recall_memory(self, memory_id: str) -> Optional[MemoryOperation]:
        """Recall a specific memory"""
        try:
            start_time = time.time()

            # Retrieve engram from database
            engram = self.db.retrieve_memory_engram(memory_id)
            if not engram:
                return MemoryOperation(
                    timestamp=start_time,
                    operation_type=MemoryOperation.RECALL,
                    memory_id=memory_id,
                    success=False,
                    confidence=0.0,
                    neural_similarity=0.0,
                    emotional_match=0.0,
                    contextual_relevance=0.0,
                    response_data={'error': 'Memory not found'},
                    metadata={}
                )

            # Create replay operation
            operation = MemoryOperation(
                timestamp=start_time,
                operation_type=MemoryOperation.RECALL,
                memory_id=memory_id,
                success=True,
                confidence=engram.importance_score,
                neural_similarity=0.8,  # Placeholder
                emotional_match=0.7,   # Placeholder
                contextual_relevance=0.9,  # Placeholder
                response_data={
                    'engram': asdict(engram),
                    'replay_duration': len(engram.signatures) * 1.0,  # 1 second per signature
                    'consolidation_level': engram.consolidation_level
                },
                metadata={'retrieval_time': time.time() - start_time}
            )

            # Update metrics
            self.metrics['memories_retrieved'] += 1
            self.metrics['retrieval_time'] += time.time() - start_time

            await self.operation_queue.put(operation)

            self.logger.info(f"Recalled memory: {memory_id}")
            return operation

        except Exception as e:
            self.logger.error(f"Failed to recall memory: {e}")
            return MemoryOperation(
                timestamp=time.time(),
                operation_type=MemoryOperation.RECALL,
                memory_id=memory_id,
                success=False,
                confidence=0.0,
                neural_similarity=0.0,
                emotional_match=0.0,
                contextual_relevance=0.0,
                response_data={'error': str(e)},
                metadata={}
            )

    async def recognize_memory(self, processed_signal: ProcessedSignal,
                              user_id: str) -> Optional[MemoryOperation]:
        """Recognize if current neural pattern matches stored memories"""
        try:
            if not self.classifier.is_trained:
                return None

            start_time = time.time()

            # Classify memory type and strength
            memory_type, confidence, strength = self.classifier.classify_memory(processed_signal)

            # Create current signature
            features = self.classifier.feature_extractor.extract_memory_features(processed_signal)
            current_signature = MemorySignature(
                timestamp=processed_signal.timestamp,
                memory_type=memory_type,
                neural_pattern=processed_signal.filtered_signal,
                frequency_features=features,
                connectivity_pattern=np.corrcoef(processed_signal.filtered_signal.T),
                emotional_context=None,
                spatial_context=None,
                semantic_tags=[],
                confidence=confidence,
                duration=1.0,
                metadata={}
            )

            # Search for similar memories
            similar_memories = self.db.get_similar_memories(current_signature, user_id, limit=5)

            if similar_memories and similar_memories[0][1] > 0.7:  # High similarity threshold
                best_match_id, similarity = similar_memories[0]

                operation = MemoryOperation(
                    timestamp=start_time,
                    operation_type=MemoryOperation.RECOGNIZE,
                    memory_id=best_match_id,
                    success=True,
                    confidence=confidence,
                    neural_similarity=similarity,
                    emotional_match=0.8,  # Placeholder
                    contextual_relevance=0.9,  # Placeholder
                    response_data={
                        'recognized_memory_id': best_match_id,
                        'similarity_score': similarity,
                        'other_candidates': similar_memories[1:3]
                    },
                    metadata={'processing_time': time.time() - start_time}
                )

                await self.operation_queue.put(operation)
                return operation

            # No strong match found
            return MemoryOperation(
                timestamp=start_time,
                operation_type=MemoryOperation.RECOGNIZE,
                memory_id=None,
                success=False,
                confidence=confidence,
                neural_similarity=similar_memories[0][1] if similar_memories else 0.0,
                emotional_match=0.0,
                contextual_relevance=0.0,
                response_data={'message': 'No matching memory found'},
                metadata={}
            )

        except Exception as e:
            self.logger.error(f"Memory recognition failed: {e}")
            return None

    async def add_neural_data(self, processed_signal: ProcessedSignal):
        """Add neural data for memory processing"""
        if self.recording_active and self.current_memory_id:
            # Classify the signal
            if self.classifier.is_trained:
                memory_type, confidence, strength = self.classifier.classify_memory(processed_signal)
            else:
                memory_type = MemoryType.EPISODIC
                confidence = 0.5
                strength = 0.5

            # Create memory signature
            features = self.classifier.feature_extractor.extract_memory_features(processed_signal)
            signature = MemorySignature(
                timestamp=processed_signal.timestamp,
                memory_type=memory_type,
                neural_pattern=processed_signal.filtered_signal.copy(),
                frequency_features=features,
                connectivity_pattern=np.corrcoef(processed_signal.filtered_signal.T),
                emotional_context=None,
                spatial_context=None,
                semantic_tags=[],
                confidence=confidence,
                duration=1.0,
                metadata={'strength': strength}
            )

            self.current_signatures.append(signature)

            # Update metrics
            self.metrics['average_confidence'].append(confidence)

        # Also add to processing queue for recognition
        await self.memory_queue.put(processed_signal)

    async def start_memory_processing(self):
        """Start real-time memory processing"""
        if not self.is_initialized:
            raise RuntimeError("System must be initialized")

        self.is_running = True
        self.logger.info("Starting real-time memory processing")

        # Start processing loop
        asyncio.create_task(self._memory_processing_loop())

    async def stop_memory_processing(self):
        """Stop real-time memory processing"""
        self.is_running = False
        self.logger.info("Stopping memory processing")

    async def _memory_processing_loop(self):
        """Main memory processing loop"""
        while self.is_running:
            try:
                # Get neural signal from queue
                processed_signal = await asyncio.wait_for(
                    self.memory_queue.get(), timeout=1.0
                )

                # Perform memory recognition if not recording
                if not self.recording_active and self.classifier.is_trained:
                    # Get user ID from context (in real implementation, would be passed in)
                    user_id = "default_user"  # Placeholder

                    recognition_result = await self.recognize_memory(processed_signal, user_id)
                    if recognition_result and recognition_result.success:
                        # Trigger callbacks
                        for callback in self.memory_callbacks:
                            try:
                                await callback(recognition_result)
                            except Exception as e:
                                self.logger.error(f"Memory callback error: {e}")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Memory processing loop error: {e}")

    def add_memory_callback(self, callback: Callable[[MemoryOperation], None]):
        """Add callback for memory operation events"""
        self.memory_callbacks.append(callback)

    def add_operation_callback(self, callback: Callable[[MemoryOperation], None]):
        """Add callback for memory operation results"""
        self.operation_callbacks.append(callback)

    def get_memory_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of user's memories"""
        try:
            # Get recent memories
            recent_memory_ids = self.db.search_memories(user_id, limit=10)
            recent_memories = []

            for memory_id in recent_memory_ids:
                engram = self.db.retrieve_memory_engram(memory_id)
                if engram:
                    recent_memories.append({
                        'memory_id': memory_id,
                        'title': engram.title,
                        'type': engram.memory_type.value,
                        'created_at': engram.created_at,
                        'importance': engram.importance_score,
                        'retrieval_count': engram.retrieval_count
                    })

            # Memory type distribution
            memory_types = {}
            for memory_id in self.db.search_memories(user_id, limit=1000):
                engram = self.db.retrieve_memory_engram(memory_id)
                if engram:
                    mem_type = engram.memory_type.value
                    memory_types[mem_type] = memory_types.get(mem_type, 0) + 1

            return {
                'total_memories': len(recent_memory_ids),
                'recent_memories': recent_memories,
                'memory_type_distribution': memory_types,
                'average_importance': np.mean([m['importance'] for m in recent_memories]) if recent_memories else 0
            }

        except Exception as e:
            self.logger.error(f"Failed to get memory summary: {e}")
            return {}

    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        return {
            'memories_recorded': self.metrics['memories_recorded'],
            'memories_retrieved': self.metrics['memories_retrieved'],
            'total_recording_time': self.metrics['recording_time'],
            'total_retrieval_time': self.metrics['retrieval_time'],
            'memory_type_distribution': dict(self.metrics['memory_types']),
            'average_confidence': np.mean(list(self.metrics['average_confidence'])) if self.metrics['average_confidence'] else 0,
            'is_running': self.is_running,
            'is_recording': self.recording_active,
            'current_memory_id': self.current_memory_id,
            'classifier_trained': self.classifier.is_trained,
            'queue_sizes': {
                'memory_queue': self.memory_queue.qsize(),
                'operation_queue': self.operation_queue.qsize()
            }
        }

    async def cleanup(self):
        """Cleanup resources"""
        await self.stop_memory_processing()
        if self.recording_active:
            await self.stop_memory_recording()
        self.db.close()

# Main interface for external use
async def create_memory_bci(db_path: str = "memory_database.db",
                          model_directory: str = "memory_models") -> MemoryBCI:
    """Create and initialize a memory BCI system"""
    memory_bci = MemoryBCI(db_path, model_directory)
    success = await memory_bci.initialize()

    if not success:
        raise RuntimeError("Failed to initialize memory BCI system")

    return memory_bci

if __name__ == "__main__":
    # Example usage
    async def main():
        # Create memory BCI
        memory_bci = await create_memory_bci()

        # Add callbacks
        def on_memory_recognized(operation):
            if operation.success:
                print(f"Memory recognized: {operation.memory_id} "
                      f"(similarity: {operation.neural_similarity:.2f})")

        memory_bci.add_memory_callback(on_memory_recognized)

        # Start memory processing
        await memory_bci.start_memory_processing()

        # Start recording a memory
        memory_id = await memory_bci.start_memory_recording(
            user_id="example_user",
            memory_type=MemoryType.EPISODIC,
            title="Beautiful sunset experience",
            description="Recording neural patterns while watching a sunset"
        )

        if memory_id:
            print(f"Started recording memory: {memory_id}")

            # Simulate some neural data
            from .neural_interface import create_neural_interface

            neural_interface = await create_neural_interface("simulator")
            await neural_interface.calibrate(duration=5.0)

            # Process signals while recording
            for _ in range(20):
                signal = neural_interface.get_latest_signal()
                if signal:
                    await memory_bci.add_neural_data(signal)
                await asyncio.sleep(0.1)

            # Stop recording
            recorded_id = await memory_bci.stop_memory_recording()
            print(f"Stopped recording memory: {recorded_id}")

            # Recall the memory
            recall_result = await memory_bci.recall_memory(recorded_id)
            if recall_result and recall_result.success:
                print(f"Memory recalled successfully")

            # Get memory summary
            summary = memory_bci.get_memory_summary("example_user")
            print(f"Memory summary: {summary}")

            # Get metrics
            metrics = memory_bci.get_metrics()
            print(f"System metrics: {metrics}")

            await neural_interface.shutdown()

        # Cleanup
        await memory_bci.cleanup()

    asyncio.run(main())