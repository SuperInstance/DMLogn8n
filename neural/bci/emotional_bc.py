#!/usr/bin/env python3
"""
Emotional BCI System - Emotion Detection and AI Response System
Advanced brain-computer interface for detecting emotional states and enabling
AI characters to respond empathetically to user emotions.

This module implements sophisticated algorithms for detecting and interpreting
emotional states from neural signals, creating a bidirectional emotional
communication channel between users and AI agents.
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

# Machine Learning Libraries
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA

# Signal Processing
from scipy import signal
from scipy.stats import entropy
from scipy.fft import fft, fftfreq
import cv2

# Local imports
from .neural_interface import ProcessedSignal, BrainWave
from .thought_detector import ThoughtPattern

class EmotionType(Enum):
    """Primary emotion categories based on dimensional models"""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"
    LOVE = "love"
    EXCITEMENT = "excitement"
    CALM = "calm"
    ANXIETY = "anxiety"
    HOPE = "hope"

class EmotionalDimension(Enum):
    """Emotional dimensions for valence-arousal model"""
    VALENCE = "valence"  # Positive to negative
    AROUSAL = "arousal"  # Calm to excited
    DOMINANCE = "dominance"  # Submissive to dominant

class EmotionalState(Enum):
    """Complex emotional states combining multiple emotions"""
    HAPPY = "happy"           # High valence, high arousal
    CALM = "calm"             # High valence, low arousal
    SAD = "sad"               # Low valence, low arousal
    ANGRY = "angry"           # Low valence, high arousal
    FEARFUL = "fearful"       # Low valence, high arousal
    SURPRISED = "surprised"   # High arousal, variable valence
    DISGUSTED = "disgusted"   # Low valence, moderate arousal
    EXCITED = "excited"       # High valence, high arousal
    ANXIOUS = "anxious"       # Low valence, moderate-high arousal
    CONTENT = "content"       # High valence, low arousal
    BORED = "bored"           # Low valence, low arousal
    FOCUSED = "focused"       # Moderate valence, moderate arousal

class EmotionalIntensity(Enum):
    """Intensity levels for emotional states"""
    VERY_LOW = 0.1
    LOW = 0.3
    MODERATE = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9

@dataclass
class EmotionalPattern:
    """Detected emotional pattern from neural signals"""
    timestamp: float
    primary_emotion: EmotionType
    emotional_state: EmotionalState
    valence: float  # -1 to 1
    arousal: float  # -1 to 1
    dominance: float  # -1 to 1
    intensity: EmotionalIntensity
    confidence: float
    neural_signature: np.ndarray
    frequency_features: Dict[str, float]
    asymmetry_features: Dict[str, float]
    physiological_correlates: Dict[str, float]
    metadata: Dict[str, Any]

@dataclass
class EmotionalResponse:
    """AI response to detected user emotion"""
    timestamp: float
    user_emotion: EmotionalPattern
    response_type: str
    response_content: Dict[str, Any]
    empathy_level: float
    appropriateness_score: float
    suggested_actions: List[str]
    dialogue_suggestions: List[str]
    character_adjustments: Dict[str, Any]

class EmotionalFeatureExtractor:
    """Extract emotion-relevant features from neural signals"""

    def __init__(self):
        self.frequency_bands = {
            'theta': (4, 8),
            'alpha': (8, 13),
            'beta': (13, 30),
            'gamma': (30, 100),
            'high_gamma': (100, 200)
        }
        self.asymmetry_pairs = [
            ('frontal_left', 'frontal_right'),
            ('temporal_left', 'temporal_right'),
            ('parietal_left', 'parietal_right'),
            ('central_left', 'central_right')
        ]

    def extract_emotional_features(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Extract comprehensive emotional features"""
        features = {}

        # Frequency-based emotional indicators
        features.update(self._extract_frequency_emotions(processed_signal))

        # Asymmetry-based emotional indicators
        features.update(self._extract_asymmetry_emotions(processed_signal))

        # Complexity-based emotional indicators
        features.update(self._extract_complexity_emotions(processed_signal))

        # Connectivity-based emotional indicators
        features.update(self._extract_connectivity_emotions(processed_signal))

        # Temporal dynamics
        features.update(self._extract_temporal_emotions(processed_signal))

        return features

    def _extract_frequency_emotions(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Extract frequency-based emotional indicators"""
        brain_waves = processed_signal.brain_waves
        features = {}

        # Frontal alpha asymmetry (approach/avoidance motivation)
        alpha_left = brain_waves.get('ALPHA', 0) * 0.5  # Simulated left hemisphere
        alpha_right = brain_waves.get('ALPHA', 0) * 0.5  # Simulated right hemisphere
        frontal_asymmetry = (alpha_right - alpha_left) / (alpha_left + alpha_right + 1e-10)
        features['frontal_alpha_asymmetry'] = frontal_asymmetry

        # Approach motivation (positive valence indicator)
        features['approach_motivation'] = max(0, frontal_asymmetry)

        # Avoidance motivation (negative valence indicator)
        features['avoidance_motivation'] = max(0, -frontal_asymmetry)

        # Arousal indicators
        beta_power = brain_waves.get('BETA', 0)
        theta_power = brain_waves.get('THETA', 0)
        alpha_power = brain_waves.get('ALPHA', 0)

        # High beta indicates high arousal
        features['arousal_beta'] = beta_power / (beta_power + alpha_power + 1e-10)

        # Theta/beta ratio (cognitive vs emotional processing)
        features['theta_beta_ratio'] = theta_power / (beta_power + 1e-10)

        # Gamma activity (emotional intensity)
        gamma_power = brain_waves.get('GAMMA', 0)
        features['emotional_intensity'] = gamma_power / (gamma_power + beta_power + 1e-10)

        # Alpha power (relaxation)
        features['relaxation_index'] = alpha_power / (alpha_power + beta_power + 1e-10)

        # Emotional complexity (multiple frequency bands)
        total_power = sum(brain_waves.values())
        if total_power > 0:
            entropy_values = [power/total_power for power in brain_waves.values()]
            features['emotional_complexity'] = entropy(entropy_values + 1e-10)
        else:
            features['emotional_complexity'] = 0

        return features

    def _extract_asymmetry_emotions(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Extract hemispheric asymmetry emotional indicators"""
        signal_data = processed_signal.filtered_signal
        features = {}

        if signal_data.shape[1] >= 4:
            # Split hemispheres
            left_channels = signal_data[:, :signal_data.shape[1]//2]
            right_channels = signal_data[:, signal_data.shape[1]//2:]

            # Calculate power in each hemisphere
            left_power = np.mean(left_channels ** 2)
            right_power = np.mean(right_channels ** 2)

            # Overall asymmetry
            asymmetry = (left_power - right_power) / (left_power + right_power + 1e-10)
            features['hemispheric_asymmetry'] = asymmetry

            # Frequency-specific asymmetry
            for band_name, (low, high) in self.frequency_bands.items():
                # Apply bandpass filter
                nyquist = 250 / 2
                if high < nyquist:
                    b, a = signal.butter(4, [low/nyquist, high/nyquist], btype='band')
                    left_filtered = signal.filtfilt(b, a, left_channels, axis=0)
                    right_filtered = signal.filtfilt(b, a, right_channels, axis=0)

                    left_band_power = np.mean(left_filtered ** 2)
                    right_band_power = np.mean(right_filtered ** 2)

                    band_asymmetry = (left_band_power - right_band_power) / (left_band_power + right_band_power + 1e-10)
                    features[f'{band_name}_asymmetry'] = band_asymmetry

        return features

    def _extract_complexity_emotions(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Extract complexity-based emotional indicators"""
        signal_data = processed_signal.filtered_signal
        features = {}

        # Sample entropy (emotional stability)
        for ch in range(min(3, signal_data.shape[1])):
            entropy_val = self._sample_entropy(signal_data[:, ch])
            features[f'entropy_ch_{ch}'] = entropy_val

        # Fractal dimension (emotional complexity)
        for ch in range(min(3, signal_data.shape[1])):
            fd = self._fractal_dimension(signal_data[:, ch])
            features[f'fractal_dim_ch_{ch}'] = fd

        # Hurst exponent (emotional persistence)
        for ch in range(min(3, signal_data.shape[1])):
            hurst = self._hurst_exponent(signal_data[:, ch])
            features[f'hurst_ch_{ch}'] = hurst

        # Emotional regulation capacity (variability in entropy)
        if len(features) >= 3:
            entropy_values = [v for k, v in features.items() if 'entropy' in k]
            features['emotional_regulation'] = 1 - np.std(entropy_values)

        return features

    def _extract_connectivity_emotions(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Extract connectivity-based emotional indicators"""
        signal_data = processed_signal.filtered_signal
        features = {}

        if signal_data.shape[1] > 1:
            # Coherence analysis
            coherence_matrix = []
            for i in range(min(4, signal_data.shape[1])):
                for j in range(i+1, min(4, signal_data.shape[1])):
                    f, Cxy = signal.coherence(
                        signal_data[:, i], signal_data[:, j],
                        fs=250, nperseg=128
                    )
                    coherence_matrix.append(np.mean(Cxy))

            if coherence_matrix:
                features['mean_coherence'] = np.mean(coherence_matrix)
                features['coherence_stability'] = 1 - np.std(coherence_matrix)

                # Emotional integration (high coherence during strong emotions)
                features['emotional_integration'] = np.mean([c for c in coherence_matrix if c > 0.5])

            # Phase synchronization
            analytic_signal = signal.hilbert(signal_data, axis=0)
            instantaneous_phase = np.unwrap(np.angle(analytic_signal), axis=0)

            phase_lock_values = []
            for i in range(min(3, signal_data.shape[1])):
                for j in range(i+1, min(3, signal_data.shape[1])):
                    phase_diff = instantaneous_phase[:, i] - instantaneous_phase[:, j]
                    plv = np.abs(np.mean(np.exp(1j * phase_diff)))
                    phase_lock_values.append(plv)

            if phase_lock_values:
                features['phase_synchronization'] = np.mean(phase_lock_values)

        return features

    def _extract_temporal_emotions(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Extract temporal dynamics of emotional processing"""
        signal_data = processed_signal.filtered_signal
        features = {}

        # Rate of change (emotional lability)
        gradient = np.gradient(signal_data, axis=0)
        features['emotional_lability'] = np.mean(np.abs(gradient))

        # Autocorrelation (emotional persistence)
        for ch in range(min(2, signal_data.shape[1])):
            autocorr = np.correlate(signal_data[:, ch], signal_data[:, ch], mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            autocorr = autocorr / autocorr[0] if autocorr[0] != 0 else autocorr
            features[f'autocorr_lag1_ch_{ch}'] = autocorr[1] if len(autocorr) > 1 else 0

        # Emotional transitions (variability in signal characteristics)
        window_size = 50
        if len(signal_data) > window_size * 2:
            windows = [
                signal_data[i:i+window_size]
                for i in range(0, len(signal_data)-window_size, window_size)
            ]

            window_features = []
            for window in windows:
                window_features.append(np.mean(np.var(window, axis=0)))

            if len(window_features) > 1:
                features['emotional_transitions'] = np.std(window_features)

        return features

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

    def _hurst_exponent(self, signal: np.ndarray) -> float:
        """Calculate Hurst exponent"""
        N = len(signal)
        max_k = N // 4

        if max_k < 4:
            return 0.5

        R_S = []
        for k in range(4, max_k + 1, 4):
            chunks = [signal[i:i+k] for i in range(0, N - k + 1, k)]
            chunk_RS = []

            for chunk in chunks:
                if len(chunk) < 2:
                    continue
                chunk = chunk - np.mean(chunk)
                cumsum = np.cumsum(chunk)
                R = np.max(cumsum) - np.min(cumsum)
                S = np.std(chunk)
                if S > 0:
                    chunk_RS.append(R / S)

            if chunk_RS:
                R_S.append(np.mean(chunk_RS))

        if len(R_S) < 2:
            return 0.5

        k_vals = np.arange(4, 4 * len(R_S) + 1, 4)
        coeffs = np.polyfit(np.log(k_vals), np.log(R_S), 1)
        return coeffs[0]

class EmotionClassifier:
    """Advanced emotion classification system"""

    def __init__(self, num_emotions: int = 12):
        self.num_emotions = num_emotions
        self.feature_extractor = EmotionalFeatureExtractor()
        self.models = self._initialize_models()
        self.scalers = {}
        self.dimension_models = self._initialize_dimension_models()
        self.is_trained = False

        # Emotion mapping
        self.emotion_labels = [e.value for e in EmotionType]
        self.state_labels = [s.value for s in EmotionalState]

    def _initialize_models(self) -> Dict[str, Any]:
        """Initialize emotion classification models"""
        return {
            'deep_emotion': self._build_deep_emotion_model(),
            'random_forest': RandomForestClassifier(n_estimators=200, random_state=42),
            'gradient_boost': GradientBoostingClassifier(n_estimators=150, random_state=42),
            'ensemble_weights': np.ones(3) / 3
        }

    def _build_deep_emotion_model(self) -> keras.Model:
        """Build deep neural network for emotion classification"""
        # Determine input size from feature extractor
        dummy_signal = self._create_dummy_signal()
        dummy_features = self.feature_extractor.extract_emotional_features(dummy_signal)
        input_size = len(dummy_features)

        model = keras.Sequential([
            layers.Input(shape=(input_size,)),

            # Dense layers with batch normalization
            layers.Dense(256, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),

            layers.Dense(128, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),

            layers.Dense(64, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),

            # Attention mechanism for emotional features
            layers.Dense(32, activation='tanh'),
            layers.Dense(32, activation='sigmoid'),
            layers.Multiply(),

            layers.Dense(16, activation='relu'),

            # Output layer for emotion classification
            layers.Dense(self.num_emotions, activation='softmax')
        ])

        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy', 'top_k_categorical_accuracy']
        )

        return model

    def _initialize_dimension_models(self) -> Dict[str, Any]:
        """Initialize models for emotional dimensions (valence, arousal, dominance)"""
        return {
            'valence': self._build_dimension_model(),
            'arousal': self._build_dimension_model(),
            'dominance': self._build_dimension_model()
        }

    def _build_dimension_model(self) -> keras.Model:
        """Build model for emotional dimension prediction"""
        dummy_signal = self._create_dummy_signal()
        dummy_features = self.feature_extractor.extract_emotional_features(dummy_signal)
        input_size = len(dummy_features)

        model = keras.Sequential([
            layers.Input(shape=(input_size,)),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(1, activation='tanh')  # Output -1 to 1
        ])

        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model

    def _create_dummy_signal(self) -> ProcessedSignal:
        """Create dummy processed signal for feature extraction"""
        from .neural_interface import BrainWave

        dummy_data = np.random.randn(250, 8)  # 1 second of 8-channel data
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

    def train(self, training_data: List[Tuple[ProcessedSignal, EmotionType]],
              dimension_data: List[Tuple[ProcessedSignal, Dict[str, float]]] = None) -> Dict[str, Any]:
        """Train emotion classification models"""
        training_results = {}

        # Extract features and labels
        X = []
        y = []

        for signal, emotion in training_data:
            features = self.feature_extractor.extract_emotional_features(signal)
            X.append(features)
            y.append(emotion.value)

        X = np.array(X)
        y = np.array(y)

        # Encode labels
        self.label_encoder = LabelEncoder()
        y_encoded = self.label_encoder.fit_transform(y)
        y_categorical = keras.utils.to_categorical(y_encoded)

        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        self.scalers['emotion'] = scaler

        # Train deep emotion model
        print("Training deep emotion model...")
        history = self.models['deep_emotion'].fit(
            X_train_scaled, keras.utils.to_categorical(y_train),
            validation_data=(X_val_scaled, keras.utils.to_categorical(y_val)),
            epochs=100,
            batch_size=32,
            callbacks=[
                keras.callbacks.EarlyStopping(patience=15, restore_best_weights=True),
                keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=8)
            ],
            verbose=1
        )
        training_results['deep_emotion'] = history.history

        # Train traditional models
        print("Training Random Forest...")
        self.models['random_forest'].fit(X_train_scaled, y_train)

        print("Training Gradient Boosting...")
        self.models['gradient_boost'].fit(X_train_scaled, y_train)

        # Calculate ensemble weights
        self._calculate_ensemble_weights(X_val_scaled, y_val)

        # Train dimension models if data provided
        if dimension_data:
            print("Training emotional dimension models...")
            dimension_results = self._train_dimension_models(dimension_data)
            training_results['dimensions'] = dimension_results

        self.is_trained = True
        return training_results

    def _train_dimension_models(self, dimension_data: List[Tuple[ProcessedSignal, Dict[str, float]]]) -> Dict[str, Any]:
        """Train models for valence, arousal, and dominance prediction"""
        results = {}

        # Extract features
        X = []
        dimensions = {'valence': [], 'arousal': [], 'dominance': []}

        for signal, dims in dimension_data:
            features = self.feature_extractor.extract_emotional_features(signal)
            X.append(features)
            for dim in ['valence', 'arousal', 'dominance']:
                dimensions[dim].append(dims.get(dim, 0))

        X = np.array(X)

        # Scale features
        if 'emotion' in self.scalers:
            X_scaled = self.scalers['emotion'].transform(X)
        else:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            self.scalers['emotion'] = scaler

        # Train each dimension model
        for dim in ['valence', 'arousal', 'dominance']:
            y_dim = np.array(dimensions[dim])

            print(f"Training {dim} model...")
            history = self.dimension_models[dim].fit(
                X_scaled, y_dim,
                validation_split=0.2,
                epochs=50,
                batch_size=32,
                callbacks=[
                    keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True)
                ],
                verbose=1
            )
            results[dim] = history.history

        return results

    def _calculate_ensemble_weights(self, X_val: np.ndarray, y_val: np.ndarray):
        """Calculate optimal ensemble weights based on validation performance"""
        scores = []

        # Deep model performance
        y_pred_deep = self.models['deep_emotion'].predict(X_val, verbose=0)
        accuracy_deep = accuracy_score(y_val, np.argmax(y_pred_deep, axis=1))
        scores.append(accuracy_deep)

        # Random Forest performance
        accuracy_rf = self.models['random_forest'].score(X_val, y_val)
        scores.append(accuracy_rf)

        # Gradient Boosting performance
        accuracy_gb = self.models['gradient_boost'].score(X_val, y_val)
        scores.append(accuracy_gb)

        # Normalize weights
        scores = np.array(scores)
        self.models['ensemble_weights'] = scores / np.sum(scores)

        print(f"Ensemble weights: Deep: {self.models['ensemble_weights'][0]:.3f}, "
              f"RF: {self.models['ensemble_weights'][1]:.3f}, "
              f"GB: {self.models['ensemble_weights'][2]:.3f}")

    def predict_emotion(self, processed_signal: ProcessedSignal) -> Tuple[EmotionType, float, np.ndarray]:
        """Predict emotion and confidence from neural signal"""
        if not self.is_trained:
            raise RuntimeError("Models must be trained before prediction")

        # Extract features
        features = self.feature_extractor.extract_emotional_features(processed_signal)
        features_array = np.array([features])

        # Scale features
        if 'emotion' in self.scalers:
            features_scaled = self.scalers['emotion'].transform(features_array)
        else:
            features_scaled = features_array

        # Get predictions from all models
        ensemble_predictions = np.zeros(self.num_emotions)

        # Deep model prediction
        try:
            pred_deep = self.models['deep_emotion'].predict(features_scaled, verbose=0)[0]
            ensemble_predictions += pred_deep * self.models['ensemble_weights'][0]
        except Exception as e:
            print(f"Deep model prediction failed: {e}")

        # Random Forest prediction
        try:
            pred_rf = self.models['random_forest'].predict_proba(features_scaled)[0]
            ensemble_predictions += pred_rf * self.models['ensemble_weights'][1]
        except Exception as e:
            print(f"Random Forest prediction failed: {e}")

        # Gradient Boosting prediction
        try:
            pred_gb = self.models['gradient_boost'].predict_proba(features_scaled)[0]
            ensemble_predictions += pred_gb * self.models['ensemble_weights'][2]
        except Exception as e:
            print(f"Gradient Boosting prediction failed: {e}")

        # Normalize predictions
        if np.sum(ensemble_predictions) > 0:
            ensemble_predictions = ensemble_predictions / np.sum(ensemble_predictions)

        # Get top prediction
        top_idx = np.argmax(ensemble_predictions)
        confidence = ensemble_predictions[top_idx]
        predicted_emotion_label = self.label_encoder.inverse_transform([top_idx])[0]
        predicted_emotion = EmotionType(predicted_emotion_label)

        return predicted_emotion, confidence, ensemble_predictions

    def predict_dimensions(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Predict emotional dimensions"""
        if not all(model.trained for model in self.dimension_models.values()):
            # Return default values if models not trained
            return {'valence': 0.0, 'arousal': 0.0, 'dominance': 0.0}

        # Extract features
        features = self.feature_extractor.extract_emotional_features(processed_signal)
        features_array = np.array([features])

        # Scale features
        if 'emotion' in self.scalers:
            features_scaled = self.scalers['emotion'].transform(features_array)
        else:
            features_scaled = features_array

        dimensions = {}
        for dim in ['valence', 'arousal', 'dominance']:
            try:
                pred = self.dimension_models[dim].predict(features_scaled, verbose=0)[0]
                dimensions[dim] = np.clip(pred, -1, 1)
            except Exception as e:
                print(f"Dimension {dim} prediction failed: {e}")
                dimensions[dim] = 0.0

        return dimensions

    def save_models(self, directory: str):
        """Save trained models"""
        import os
        os.makedirs(directory, exist_ok=True)

        # Save deep models
        self.models['deep_emotion'].save(os.path.join(directory, 'deep_emotion_model.h5'))
        for dim, model in self.dimension_models.items():
            model.save(os.path.join(directory, f'{dim}_model.h5'))

        # Save traditional models
        import pickle
        with open(os.path.join(directory, 'random_forest.pkl'), 'wb') as f:
            pickle.dump(self.models['random_forest'], f)
        with open(os.path.join(directory, 'gradient_boost.pkl'), 'wb') as f:
            pickle.dump(self.models['gradient_boost'], f)

        # Save metadata
        metadata = {
            'emotion_labels': self.emotion_labels,
            'state_labels': self.state_labels,
            'ensemble_weights': self.models['ensemble_weights'],
            'is_trained': self.is_trained,
            'label_encoder': self.label_encoder
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

        # Load deep models
        self.models['deep_emotion'] = keras.models.load_model(os.path.join(directory, 'deep_emotion_model.h5'))
        for dim in ['valence', 'arousal', 'dominance']:
            if os.path.exists(os.path.join(directory, f'{dim}_model.h5')):
                self.dimension_models[dim] = keras.models.load_model(os.path.join(directory, f'{dim}_model.h5'))

        # Load traditional models
        with open(os.path.join(directory, 'random_forest.pkl'), 'rb') as f:
            self.models['random_forest'] = pickle.load(f)
        with open(os.path.join(directory, 'gradient_boost.pkl'), 'rb') as f:
            self.models['gradient_boost'] = pickle.load(f)

        # Load metadata
        with open(os.path.join(directory, 'metadata.pkl'), 'rb') as f:
            metadata = pickle.load(f)

        self.models['ensemble_weights'] = metadata['ensemble_weights']
        self.is_trained = metadata['is_trained']
        self.label_encoder = metadata['label_encoder']

        # Load scalers
        with open(os.path.join(directory, 'scalers.pkl'), 'rb') as f:
            self.scalers = pickle.load(f)

class EmotionalResponseGenerator:
    """Generate AI responses to detected user emotions"""

    def __init__(self):
        self.response_templates = self._load_response_templates()
        self.emotion_action_mapping = self._load_emotion_action_mapping()
        self.empathy_models = self._initialize_empathy_models()

    def _load_response_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load response templates for different emotions"""
        return {
            'joy': {
                'greetings': ["I can see you're feeling happy! That's wonderful!", "Your joy is contagious!", "You seem to be in great spirits!"],
                'actions': ["Let's celebrate together!", "Time for something fun!", "Want to share your happiness?"],
                'dialogue': ["Tell me what's making you so happy!", "I love seeing you this joyful!", "Your happiness brightens everything!"],
                'character_adjustments': {
                    'animation': 'bounce',
                    'voice_tone': 'upbeat',
                    'movement_speed': 'fast',
                    'gesture': 'wave'
                }
            },
            'sadness': {
                'greetings': ["I can see you're feeling down. I'm here for you.", "You seem sad - want to talk about it?", "I notice you're feeling low."],
                'actions': ["Let me comfort you.", "Would you like a hug?", "I'm here to support you."],
                'dialogue': ["It's okay to feel sad sometimes.", "I'm here to listen if you want to talk.", "Your feelings are valid."],
                'character_adjustments': {
                    'animation': 'gentle',
                    'voice_tone': 'soft',
                    'movement_speed': 'slow',
                    'gesture': 'pat'
                }
            },
            'anger': {
                'greetings': ["I can see you're feeling angry. Let's work through this.", "You seem upset - what's wrong?", "I notice you're angry."],
                'actions': ["Let's find a constructive way to express this.", "Take a deep breath with me.", "Want to talk about what's bothering you?"],
                'dialogue': ["It's understandable to feel angry sometimes.", "Let's find a solution together.", "I'm here to help you calm down."],
                'character_adjustments': {
                    'animation': 'calm',
                    'voice_tone': 'measured',
                    'movement_speed': 'slow',
                    'gesture': 'open_palm'
                }
            },
            'fear': {
                'greetings': ["I can see you're feeling scared. You're safe with me.", "You seem afraid - I'm here to protect you.", "Don't worry, I'm here for you."],
                'actions': ["Let me protect you.", "Stay close to me.", "We're safe together."],
                'dialogue': ["You're safe here.", "I won't let anything harm you.", "Take comfort in my presence."],
                'character_adjustments': {
                    'animation': 'protective',
                    'voice_tone': 'reassuring',
                    'movement_speed': 'slow',
                    'gesture': 'shield'
                }
            },
            'surprise': {
                'greetings': ["Wow! You seem surprised!", "I can see you're amazed!", "What a surprising moment!"],
                'actions': ["Let's explore this together!", "Want to investigate what happened?", "This is exciting!"],
                'dialogue': ["That's incredible!", "I'm surprised too!", "What an unexpected turn!"],
                'character_adjustments': {
                    'animation': 'alert',
                    'voice_tone': 'excited',
                    'movement_speed': 'normal',
                    'gesture': 'point'
                }
            },
            'neutral': {
                'greetings': ["How are you feeling today?", "You seem calm and collected.", "Everything alright?"],
                'actions': ["How can I help you today?", "What would you like to do?", "I'm here for whatever you need."],
                'dialogue': ["It's good to see you.", "How can I make your day better?", "I'm here to assist you."],
                'character_adjustments': {
                    'animation': 'idle',
                    'voice_tone': 'neutral',
                    'movement_speed': 'normal',
                    'gesture': 'nod'
                }
            }
        }

    def _load_emotion_action_mapping(self) -> Dict[str, List[str]]:
        """Map emotions to appropriate actions"""
        return {
            'joy': ['celebrate', 'dance', 'sing', 'play', 'explore'],
            'sadness': ['comfort', 'listen', 'support', 'hug', 'soothe'],
            'anger': ['calm', 'mediate', 'solve', 'protect', 'defuse'],
            'fear': ['protect', 'reassure', 'guide', 'comfort', 'empower'],
            'surprise': ['investigate', 'explore', 'discover', 'learn', 'share'],
            'disgust': ['clean', 'avoid', 'protect', 'heal', 'transform'],
            'love': ['connect', 'share', 'support', 'care', 'nurture'],
            'excitement': ['energize', 'motivate', 'lead', 'inspire', 'encourage'],
            'calm': ['maintain', 'balance', 'peace', 'meditate', 'relax'],
            'anxiety': ['reassure', 'ground', 'focus', 'breathe', 'stabilize'],
            'hope': ['encourage', 'inspire', 'guide', 'support', 'believe']
        }

    def _initialize_empathy_models(self) -> Dict[str, Any]:
        """Initialize empathy assessment models"""
        return {
            'empathy_thresholds': {
                'low': 0.3,
                'medium': 0.6,
                'high': 0.8
            },
            'response_intensity_mapping': {
                0.1: 'minimal',
                0.3: 'gentle',
                0.5: 'moderate',
                0.7: 'strong',
                0.9: 'intense'
            }
        }

    def generate_response(self, emotional_pattern: EmotionalPattern,
                         context: Dict[str, Any] = None) -> EmotionalResponse:
        """Generate appropriate response to detected emotion"""
        emotion = emotional_pattern.primary_emotion.value
        intensity = emotional_pattern.intensity.value

        # Get response template
        if emotion not in self.response_templates:
            emotion = 'neutral'

        template = self.response_templates[emotion]

        # Calculate empathy level
        empathy_level = self._calculate_empathy_level(emotional_pattern)

        # Select appropriate responses based on intensity
        response_type = self._select_response_type(emotion, intensity)
        response_content = self._select_response_content(template, response_type, intensity)

        # Calculate appropriateness score
        appropriateness_score = self._calculate_appropriateness(emotional_pattern, context)

        # Generate suggested actions
        suggested_actions = self._generate_suggested_actions(emotion, intensity, context)

        # Generate dialogue suggestions
        dialogue_suggestions = self._generate_dialogue_suggestions(template, intensity)

        # Character adjustments
        character_adjustments = self._adjust_character_response(template, intensity)

        return EmotionalResponse(
            timestamp=time.time(),
            user_emotion=emotional_pattern,
            response_type=response_type,
            response_content=response_content,
            empathy_level=empathy_level,
            appropriateness_score=appropriateness_score,
            suggested_actions=suggested_actions,
            dialogue_suggestions=dialogue_suggestions,
            character_adjustments=character_adjustments
        )

    def _calculate_empathy_level(self, emotional_pattern: EmotionalPattern) -> float:
        """Calculate empathy level based on emotional pattern"""
        # Base empathy from confidence and intensity
        base_empathy = emotional_pattern.confidence * emotional_pattern.intensity.value

        # Adjust based on emotional complexity
        complexity = len(emotional_pattern.frequency_features)
        complexity_factor = min(1.0, complexity / 10)

        # Adjust based on valence (higher empathy for negative emotions)
        valence_adjustment = 1.0
        if emotional_pattern.valence < -0.5:  # Strong negative emotion
            valence_adjustment = 1.2
        elif emotional_pattern.valence > 0.5:  # Strong positive emotion
            valence_adjustment = 1.1

        empathy_level = base_empathy * complexity_factor * valence_adjustment
        return np.clip(empathy_level, 0, 1)

    def _select_response_type(self, emotion: str, intensity: float) -> str:
        """Select appropriate response type based on emotion and intensity"""
        if intensity < 0.3:
            return 'acknowledge'
        elif intensity < 0.7:
            return 'support'
        else:
            return 'intervene'

    def _select_response_content(self, template: Dict[str, Any],
                                response_type: str, intensity: float) -> Dict[str, Any]:
        """Select response content based on template and intensity"""
        content = {}

        # Select greeting based on intensity
        greetings = template['greetings']
        if intensity > 0.7:
            content['greeting'] = greetings[0]  # Most appropriate
        elif intensity > 0.4:
            content['greeting'] = greetings[1] if len(greetings) > 1 else greetings[0]
        else:
            content['greeting'] = greetings[-1] if len(greetings) > 2 else greetings[0]

        # Select action based on response type
        if response_type == 'acknowledge':
            content['action'] = 'acknowledge_emotion'
        elif response_type == 'support':
            actions = template['actions']
            content['action'] = actions[0] if actions else 'be_present'
        else:  # intervene
            content['action'] = 'provide_intensive_support'

        # Select dialogue
        dialogues = template['dialogue']
        content['dialogue'] = dialogues[min(int(intensity * len(dialogues)), len(dialogues)-1)]

        return content

    def _calculate_appropriateness(self, emotional_pattern: EmotionalPattern,
                                 context: Dict[str, Any] = None) -> float:
        """Calculate appropriateness score for the response"""
        base_appropriateness = emotional_pattern.confidence

        # Adjust based on emotional intensity
        intensity_factor = 1.0
        if emotional_pattern.intensity.value < 0.3:
            intensity_factor = 0.8  # Less intense emotions require gentler responses
        elif emotional_pattern.intensity.value > 0.8:
            intensity_factor = 0.9  # Very intense emotions require careful handling

        # Adjust based on context
        context_factor = 1.0
        if context:
            # Consider social context
            if context.get('social_situation') == 'public':
                context_factor *= 0.8  # More reserved in public
            elif context.get('social_situation') == 'private':
                context_factor *= 1.2  # More expressive in private

            # Consider relationship
            if context.get('relationship') == 'close':
                context_factor *= 1.1
            elif context.get('relationship') == 'formal':
                context_factor *= 0.9

        appropriateness = base_appropriateness * intensity_factor * context_factor
        return np.clip(appropriateness, 0, 1)

    def _generate_suggested_actions(self, emotion: str, intensity: float,
                                   context: Dict[str, Any] = None) -> List[str]:
        """Generate suggested actions based on emotion and context"""
        base_actions = self.emotion_action_mapping.get(emotion, ['be_present'])

        # Filter actions based on intensity
        if intensity < 0.4:
            # Gentle actions for low intensity
            filtered_actions = [a for a in base_actions if a in ['comfort', 'listen', 'support', 'be_present']]
        elif intensity > 0.8:
            # More active support for high intensity
            filtered_actions = [a for a in base_actions if a in ['protect', 'defuse', 'intervene', 'guide']]
        else:
            filtered_actions = base_actions

        # Context-specific adjustments
        if context:
            if context.get('environment') == 'safe':
                filtered_actions.append('express_freely')
            elif context.get('environment') == 'challenging':
                filtered_actions.append('provide_security')

        return filtered_actions[:3]  # Return top 3 suggestions

    def _generate_dialogue_suggestions(self, template: Dict[str, Any],
                                     intensity: float) -> List[str]:
        """Generate dialogue suggestions based on template and intensity"""
        base_dialogues = template['dialogue']

        # Adjust dialogue based on intensity
        if intensity > 0.7:
            # More direct and supportive for high intensity
            return base_dialogues[:2] if len(base_dialogues) >= 2 else base_dialogues
        elif intensity < 0.4:
            # More gentle and observational for low intensity
            return base_dialogues[-2:] if len(base_dialogues) >= 2 else base_dialogues
        else:
            return base_dialogues

    def _adjust_character_response(self, template: Dict[str, Any],
                                 intensity: float) -> Dict[str, Any]:
        """Adjust character response parameters based on emotion and intensity"""
        adjustments = template['character_adjustments'].copy()

        # Adjust animation speed based on intensity
        if intensity > 0.7:
            adjustments['animation_speed'] = 'fast'
        elif intensity < 0.4:
            adjustments['animation_speed'] = 'slow'
        else:
            adjustments['animation_speed'] = 'normal'

        # Adjust voice volume based on intensity
        if intensity > 0.8:
            adjustments['voice_volume'] = 'loud' if adjustments['voice_tone'] == 'upbeat' else 'firm'
        elif intensity < 0.3:
            adjustments['voice_volume'] = 'soft'
        else:
            adjustments['voice_volume'] = 'normal'

        # Add intensity-based modifiers
        adjustments['response_intensity'] = intensity
        adjustments['urgency_level'] = 'high' if intensity > 0.7 else 'normal'

        return adjustments

class EmotionalBCI:
    """Main emotional BCI system"""

    def __init__(self, model_directory: str = "emotion_models"):
        self.model_directory = model_directory
        self.classifier = None
        self.response_generator = EmotionalResponseGenerator()
        self.is_initialized = False

        # Real-time processing
        self.emotion_queue = asyncio.Queue()
        self.response_queue = asyncio.Queue()
        self.is_running = False

        # Callbacks
        self.emotion_callbacks = []
        self.response_callbacks = []

        # Metrics
        self.metrics = {
            'emotions_detected': 0,
            'responses_generated': 0,
            'confidence_scores': deque(maxlen=100),
            'empathy_levels': deque(maxlen=100),
            'emotion_counts': {},
            'response_times': deque(maxlen=100)
        }

        # Emotional state tracking
        self.emotional_history = deque(maxlen=100)
        self.current_emotional_state = None

        self.logger = logging.getLogger(__name__)

    async def initialize(self, num_emotions: int = 12) -> bool:
        """Initialize the emotional BCI system"""
        try:
            # Initialize classifier
            self.classifier = EmotionClassifier(num_emotions)

            # Try to load existing models
            if os.path.exists(self.model_directory):
                try:
                    self.classifier.load_models(self.model_directory)
                    self.logger.info("Loaded existing emotion models")
                except Exception as e:
                    self.logger.warning(f"Could not load existing models: {e}")
                    self.classifier.is_trained = False

            self.is_initialized = True
            self.logger.info("Emotional BCI system initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize emotional BCI: {e}")
            return False

    async def train_classifier(self, training_data: List[Tuple[ProcessedSignal, EmotionType]],
                             dimension_data: List[Tuple[ProcessedSignal, Dict[str, float]]] = None) -> bool:
        """Train the emotion classifier"""
        try:
            if not self.is_initialized:
                await self.initialize()

            if len(training_data) < 20:
                self.logger.error("Insufficient training data (minimum 20 samples)")
                return False

            # Train classifier
            self.logger.info(f"Training emotion classifier with {len(training_data)} samples")
            training_results = self.classifier.train(training_data, dimension_data)

            # Save trained models
            self.classifier.save_models(self.model_directory)

            self.logger.info("Emotion classifier training completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Training failed: {e}")
            return False

    async def start_emotion_detection(self):
        """Start real-time emotion detection"""
        if not self.is_initialized or not self.classifier.is_trained:
            raise RuntimeError("System must be initialized and trained")

        self.is_running = True
        self.logger.info("Starting real-time emotion detection")

        # Start processing loop
        asyncio.create_task(self._emotion_detection_loop())

    async def stop_emotion_detection(self):
        """Stop real-time emotion detection"""
        self.is_running = False
        self.logger.info("Stopping emotion detection")

    async def _emotion_detection_loop(self):
        """Main emotion detection loop"""
        while self.is_running:
            try:
                # Get neural signal from queue
                processed_signal = await asyncio.wait_for(
                    self.emotion_queue.get(), timeout=1.0
                )

                # Detect emotion
                start_time = time.time()
                emotional_pattern = await self._detect_emotion(processed_signal)
                detection_time = time.time() - start_time

                if emotional_pattern:
                    # Update metrics
                    self.metrics['emotions_detected'] += 1
                    self.metrics['confidence_scores'].append(emotional_pattern.confidence)
                    self.metrics['response_times'].append(detection_time)

                    # Update emotion counts
                    emotion = emotional_pattern.primary_emotion.value
                    self.metrics['emotion_counts'][emotion] = \
                        self.metrics['emotion_counts'].get(emotion, 0) + 1

                    # Update emotional history
                    self.emotional_history.append(emotional_pattern)
                    self.current_emotional_state = emotional_pattern

                    # Generate response
                    response = self.response_generator.generate_response(emotional_pattern)
                    await self.response_queue.put(response)

                    # Update metrics
                    self.metrics['responses_generated'] += 1
                    self.metrics['empathy_levels'].append(response.empathy_level)

                    # Trigger callbacks
                    for callback in self.emotion_callbacks:
                        try:
                            await callback(emotional_pattern)
                        except Exception as e:
                            self.logger.error(f"Emotion callback error: {e}")

                    for callback in self.response_callbacks:
                        try:
                            await callback(response)
                        except Exception as e:
                            self.logger.error(f"Response callback error: {e}")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Emotion detection loop error: {e}")

    async def _detect_emotion(self, processed_signal: ProcessedSignal) -> Optional[EmotionalPattern]:
        """Detect emotional pattern from neural signal"""
        try:
            # Predict emotion
            emotion, confidence, probability_distribution = self.classifier.predict_emotion(processed_signal)

            # Predict emotional dimensions
            dimensions = self.classifier.predict_dimensions(processed_signal)

            # Determine intensity
            intensity = self._determine_emotional_intensity(
                confidence, dimensions['arousal'], processed_signal
            )

            # Determine emotional state
            emotional_state = self._determine_emotional_state(emotion, dimensions)

            # Extract features
            neural_signature = processed_signal.filtered_signal.flatten()
            frequency_features = processed_signal.brain_waves
            asymmetry_features = self._extract_asymmetry_features(processed_signal)
            physiological_correlates = self._estimate_physiological_correlates(processed_signal)

            return EmotionalPattern(
                timestamp=processed_signal.timestamp,
                primary_emotion=emotion,
                emotional_state=emotional_state,
                valence=dimensions['valence'],
                arousal=dimensions['arousal'],
                dominance=dimensions['dominance'],
                intensity=intensity,
                confidence=confidence,
                neural_signature=neural_signature,
                frequency_features=frequency_features,
                asymmetry_features=asymmetry_features,
                physiological_correlates=physiological_correlates,
                metadata={
                    'probability_distribution': {
                        self.classifier.label_encoder.inverse_transform([i])[0]: float(prob)
                        for i, prob in enumerate(probability_distribution)
                    }
                }
            )

        except Exception as e:
            self.logger.error(f"Emotion detection failed: {e}")
            return None

    def _determine_emotional_intensity(self, confidence: float, arousal: float,
                                     processed_signal: ProcessedSignal) -> EmotionalIntensity:
        """Determine emotional intensity from multiple indicators"""
        # Base intensity from arousal
        arousal_intensity = (abs(arousal) + 1) / 2  # Convert from -1:1 to 0:1

        # Adjust based on confidence
        confidence_factor = confidence

        # Adjust based on signal features
        brain_waves = processed_signal.brain_waves
        total_power = sum(brain_waves.values())
        intensity_features = []

        # High beta and gamma indicate high intensity
        if total_power > 0:
            beta_ratio = brain_waves.get('BETA', 0) / total_power
            gamma_ratio = brain_waves.get('GAMMA', 0) / total_power
            intensity_features.append(beta_ratio + gamma_ratio)

        # Combine intensity measures
        if intensity_features:
            feature_intensity = np.mean(intensity_features)
            combined_intensity = (arousal_intensity * confidence_factor * feature_intensity) ** 0.5
        else:
            combined_intensity = arousal_intensity * confidence_factor

        # Map to emotional intensity enum
        if combined_intensity < 0.2:
            return EmotionalIntensity.VERY_LOW
        elif combined_intensity < 0.4:
            return EmotionalIntensity.LOW
        elif combined_intensity < 0.6:
            return EmotionalIntensity.MODERATE
        elif combined_intensity < 0.8:
            return EmotionalIntensity.HIGH
        else:
            return EmotionalIntensity.VERY_HIGH

    def _determine_emotional_state(self, emotion: EmotionType, dimensions: Dict[str, float]) -> EmotionalState:
        """Determine complex emotional state from emotion and dimensions"""
        valence = dimensions['valence']
        arousal = dimensions['arousal']

        # Map emotion and dimensions to emotional state
        if emotion == EmotionType.JOY:
            if arousal > 0.5:
                return EmotionalState.EXCITED
            else:
                return EmotionalState.HAPPY
        elif emotion == EmotionType.SADNESS:
            if arousal > 0.5:
                return EmotionalState.ANXIOUS
            else:
                return EmotionalState.SAD
        elif emotion == EmotionType.ANGER:
            return EmotionalState.ANGRY
        elif emotion == EmotionType.FEAR:
            return EmotionalState.FEARFUL
        elif emotion == EmotionType.SURPRISE:
            return EmotionalState.SURPRISED
        elif emotion == EmotionType.DISGUST:
            return EmotionalState.DISGUSTED
        elif emotion == EmotionType.LOVE:
            if arousal > 0.5:
                return EmotionalState.EXCITED
            else:
                return EmotionalState.HAPPY
        elif emotion == EmotionType.CALM:
            if valence > 0:
                return EmotionalState.CONTENT
            else:
                return EmotionalState.BORED
        else:
            return EmotionalState.NEUTRAL

    def _extract_asymmetry_features(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Extract asymmetry features for emotional processing"""
        signal_data = processed_signal.filtered_signal
        features = {}

        if signal_data.shape[1] >= 2:
            # Frontal asymmetry
            left_hemisphere = signal_data[:, :signal_data.shape[1]//2]
            right_hemisphere = signal_data[:, signal_data.shape[1]//2:]

            left_power = np.mean(left_hemisphere ** 2)
            right_power = np.mean(right_hemisphere ** 2)

            asymmetry = (left_power - right_power) / (left_power + right_power + 1e-10)
            features['frontal_asymmetry'] = asymmetry

        return features

    def _estimate_physiological_correlates(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Estimate physiological correlates of emotion"""
        # These would normally be measured with additional sensors
        # For now, estimate from EEG features
        brain_waves = processed_signal.brain_waves

        correlates = {}

        # Heart rate estimation (linked to arousal)
        beta_power = brain_waves.get('BETA', 0)
        correlates['heart_rate'] = 70 + beta_power * 30  # 70-100 BPM range

        # Skin conductance (linked to emotional intensity)
        total_power = sum(brain_waves.values())
        if total_power > 0:
            correlates['skin_conductance'] = (brain_waves.get('GAMMA', 0) / total_power) * 10
        else:
            correlates['skin_conductance'] = 0.5

        # Respiration rate (linked to relaxation/arousal)
        alpha_power = brain_waves.get('ALPHA', 0)
        correlates['respiration_rate'] = 12 + (1 - alpha_power) * 8  # 12-20 breaths/min

        return correlates

    async def add_neural_data(self, processed_signal: ProcessedSignal):
        """Add neural data for emotion detection"""
        if self.is_running:
            await self.emotion_queue.put(processed_signal)

    async def get_latest_emotion(self) -> Optional[EmotionalPattern]:
        """Get the most recent detected emotion"""
        return self.current_emotional_state

    async def get_latest_response(self) -> Optional[EmotionalResponse]:
        """Get the most recent generated response"""
        try:
            while not self.response_queue.empty():
                self.latest_response = self.response_queue.get_nowait()
            return self.latest_response
        except (asyncio.QueueEmpty, AttributeError):
            return None

    def add_emotion_callback(self, callback: Callable[[EmotionalPattern], None]):
        """Add callback for emotion detection events"""
        self.emotion_callbacks.append(callback)

    def add_response_callback(self, callback: Callable[[EmotionalResponse], None]):
        """Add callback for emotional response events"""
        self.response_callbacks.append(callback)

    def get_emotional_summary(self, window_size: int = 50) -> Dict[str, Any]:
        """Get summary of recent emotional activity"""
        if not self.emotional_history:
            return {}

        recent_emotions = list(self.emotional_history)[-window_size:]

        # Calculate statistics
        emotion_counts = {}
        valence_values = []
        arousal_values = []
        intensity_values = []

        for emotion in recent_emotions:
            # Count emotions
            emotion_name = emotion.primary_emotion.value
            emotion_counts[emotion_name] = emotion_counts.get(emotion_name, 0) + 1

            # Collect dimensional values
            valence_values.append(emotion.valence)
            arousal_values.append(emotion.arousal)
            intensity_values.append(emotion.intensity.value)

        return {
            'dominant_emotion': max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else 'neutral',
            'emotion_distribution': emotion_counts,
            'average_valence': np.mean(valence_values) if valence_values else 0,
            'average_arousal': np.mean(arousal_values) if arousal_values else 0,
            'average_intensity': np.mean(intensity_values) if intensity_values else 0,
            'emotional_stability': 1 - np.std(valence_values) if len(valence_values) > 1 else 1,
            'sample_count': len(recent_emotions)
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        return {
            'emotions_detected': self.metrics['emotions_detected'],
            'responses_generated': self.metrics['responses_generated'],
            'average_confidence': np.mean(list(self.metrics['confidence_scores'])) if self.metrics['confidence_scores'] else 0,
            'average_empathy': np.mean(list(self.metrics['empathy_levels'])) if self.metrics['empathy_levels'] else 0,
            'average_response_time': np.mean(list(self.metrics['response_times'])) if self.metrics['response_times'] else 0,
            'emotion_distribution': dict(self.metrics['emotion_counts']),
            'is_running': self.is_running,
            'is_trained': self.classifier.is_trained if self.classifier else False,
            'queue_sizes': {
                'emotion_queue': self.emotion_queue.qsize(),
                'response_queue': self.response_queue.qsize()
            }
        }

# Main interface for external use
async def create_emotional_bci(num_emotions: int = 12,
                             model_directory: str = "emotion_models") -> EmotionalBCI:
    """Create and initialize an emotional BCI system"""
    emotional_bci = EmotionalBCI(model_directory)
    success = await emotional_bci.initialize(num_emotions)

    if not success:
        raise RuntimeError("Failed to initialize emotional BCI system")

    return emotional_bci

if __name__ == "__main__":
    # Example usage
    async def main():
        # Create emotional BCI
        emotional_bci = await create_emotional_bci()

        # Add callbacks
        def on_emotion_detected(emotional_pattern):
            print(f"Emotion detected: {emotional_pattern.primary_emotion.value} "
                  f"(confidence: {emotional_pattern.confidence:.2f}, "
                  f"valence: {emotional_pattern.valence:.2f}, "
                  f"arousal: {emotional_pattern.arousal:.2f})")

        def on_emotional_response(response):
            print(f"AI Response: {response.response_content.get('greeting', 'No greeting')}")

        emotional_bci.add_emotion_callback(on_emotion_detected)
        emotional_bci.add_response_callback(on_emotional_response)

        # Start emotion detection
        await emotional_bci.start_emotion_detection()

        # Simulate some neural data
        from .neural_interface import create_neural_interface

        neural_interface = await create_neural_interface("simulator")
        await neural_interface.calibrate(duration=5.0)

        # Process signals for a while
        for _ in range(20):
            signal = neural_interface.get_latest_signal()
            if signal:
                await emotional_bci.add_neural_data(signal)
            await asyncio.sleep(0.1)

        # Get emotional summary
        summary = emotional_bci.get_emotional_summary()
        print(f"Emotional summary: {summary}")

        # Get metrics
        metrics = emotional_bci.get_metrics()
        print(f"System metrics: {metrics}")

        # Stop emotion detection
        await emotional_bci.stop_emotion_detection()
        await neural_interface.shutdown()

    asyncio.run(main())