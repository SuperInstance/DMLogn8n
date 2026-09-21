#!/usr/bin/env python3
"""
Thought Detector - AI-Powered Thought Pattern Recognition System
Advanced neural network-based system for detecting and interpreting human thoughts.

This module implements sophisticated machine learning algorithms to recognize
thought patterns, intentions, and cognitive states from neural signals, enabling
direct mind-to-game communication and control.
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
import pickle
import os

# Machine Learning Libraries
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler, LabelEncoder

# Signal Processing
from scipy import signal
from scipy.stats import entropy

# Local imports
from .neural_interface import ProcessedSignal, NeuralSignal

class ThoughtType(Enum):
    """Categories of detectable thoughts"""
    COMMAND = "command"  # Intentional commands (move, jump, interact)
    EMOTION = "emotion"  # Emotional states
    ATTENTION = "attention"  # Focus and attention patterns
    MEMORY = "memory"  # Memory recall and recognition
    IMAGERY = "imagery"  # Visual and motor imagery
    COGNITIVE = "cognitive"  # General cognitive states
    INTENTION = "intention"  # Goal-directed intentions
    DECISION = "decision"  # Decision-making patterns

class ThoughtCategory(Enum):
    """Specific thought categories"""
    # Movement commands
    MOVE_FORWARD = "move_forward"
    MOVE_BACKWARD = "move_backward"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    JUMP = "jump"
    CROUCH = "crouch"
    INTERACT = "interact"
    ATTACK = "attack"
    DEFEND = "defend"

    # Cognitive states
    FOCUS = "focus"
    RELAX = "relax"
    MEDITATE = "meditate"
    THINK = "think"
    PLAN = "plan"
    SOLVE = "solve"
    CREATE = "create"
    ANALYZE = "analyze"

    # Emotional states
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    SURPRISED = "surprised"
    DISGUSTED = "disgusted"
    CALM = "calm"
    EXCITED = "excited"

    # Imagery
    VISUALIZE = "visualize"
    IMAGINE_MOVEMENT = "imagine_movement"
    RECALL_SCENE = "recall_scene"
    CREATE_IMAGE = "create_image"

    # Memory
    RECALL_MEMORY = "recall_memory"
    STORE_MEMORY = "store_memory"
    RECOGNIZE = "recognize"
    FORGET = "forget"

@dataclass
class ThoughtPattern:
    """Detected thought pattern with confidence"""
    timestamp: float
    thought_type: ThoughtType
    category: ThoughtCategory
    confidence: float
    probability_distribution: Dict[str, float]
    neural_signature: np.ndarray
    metadata: Dict[str, Any]

@dataclass
class ThoughtIntent:
    """Interpreted user intent from thought patterns"""
    timestamp: float
    intent: str
    parameters: Dict[str, Any]
    confidence: float
    urgency: float
    context: Dict[str, Any]

class FeatureEngineer:
    """Advanced feature engineering for thought detection"""

    def __init__(self):
        self.feature_cache = {}
        self.normalization_params = {}

    def extract_thought_features(self, processed_signal: ProcessedSignal) -> np.ndarray:
        """Extract features specifically optimized for thought detection"""
        features = []

        # Time-domain features for cognitive state
        features.extend(self._extract_cognitive_features(processed_signal))

        # Frequency-domain features for attention and focus
        features.extend(self._extract_attention_features(processed_signal))

        # Connectivity features for complex thoughts
        features.extend(self._extract_connectivity_features(processed_signal))

        # Nonlinear features for cognitive complexity
        features.extend(self._extract_complexity_features(processed_signal))

        # Temporal dynamics features
        features.extend(self._extract_temporal_features(processed_signal))

        return np.array(features)

    def _extract_cognitive_features(self, processed_signal: ProcessedSignal) -> List[float]:
        """Extract features related to cognitive states"""
        signal_data = processed_signal.filtered_signal
        features = []

        # Engagement index (Beta/Alpha ratio)
        beta_power = processed_signal.brain_waves.get('BETA', 0)
        alpha_power = processed_signal.brain_waves.get('ALPHA', 0)
        engagement_index = beta_power / (alpha_power + 1e-10)
        features.append(engagement_index)

        # Meditation index (Alpha/Theta ratio)
        theta_power = processed_signal.brain_waves.get('THETA', 0)
        meditation_index = alpha_power / (theta_power + 1e-10)
        features.append(meditation_index)

        # Cognitive load index (High Beta/Beta ratio)
        gamma_power = processed_signal.brain_waves.get('GAMMA', 0)
        cognitive_load = gamma_power / (beta_power + 1e-10)
        features.append(cognitive_load)

        # Focus index (Beta + Gamma / Alpha + Theta)
        focus_index = (beta_power + gamma_power) / (alpha_power + theta_power + 1e-10)
        features.append(focus_index)

        # Relaxation index (Alpha + Theta / Beta + Gamma)
        relaxation_index = (alpha_power + theta_power) / (beta_power + gamma_power + 1e-10)
        features.append(relaxation_index)

        # Creativity index (Theta + Gamma / Alpha + Beta)
        creativity_index = (theta_power + gamma_power) / (alpha_power + beta_power + 1e-10)
        features.append(creativity_index)

        return features

    def _extract_attention_features(self, processed_signal: ProcessedSignal) -> List[float]:
        """Extract features related to attention and focus"""
        signal_data = processed_signal.filtered_signal
        features = []

        # P300-like features (event-related potential components)
        features.extend(self._extract_erp_features(signal_data))

        # Steady-state visual evoked potentials (SSVEP)
        features.extend(self._extract_ssvep_features(signal_data))

        # Attention-related asymmetry
        features.extend(self._extract_asymmetry_features(signal_data))

        return features

    def _extract_erp_features(self, signal_data: np.ndarray) -> List[float]:
        """Extract event-related potential features"""
        features = []

        # Simulate ERP components (P300, N200, etc.)
        # In real implementation, these would be time-locked to events

        # P300-like component (positive deflection around 300ms)
        if len(signal_data) > 75:  # 300ms at 250Hz
            p300_window = signal_data[60:90]  # 240-360ms window
            p300_amplitude = np.mean(p300_window, axis=0)
            features.extend([
                np.mean(p300_amplitude),
                np.max(p300_amplitude),
                np.std(p300_amplitude)
            ])

        # N200-like component (negative deflection around 200ms)
        if len(signal_data) > 50:  # 200ms at 250Hz
            n200_window = signal_data[40:60]  # 160-240ms window
            n200_amplitude = np.mean(n200_window, axis=0)
            features.extend([
                np.mean(n200_amplitude),
                np.min(n200_amplitude),
                np.std(n200_amplitude)
            ])

        return features

    def _extract_ssvep_features(self, signal_data: np.ndarray) -> List[float]:
        """Extract steady-state visual evoked potential features"""
        features = []

        # Power at specific frequencies (SSVEP responses)
        sampling_rate = 250  # Assumed
        fft_vals = np.fft.fft(signal_data, axis=0)
        freqs = np.fft.fftfreq(signal_data.shape[0], 1/sampling_rate)
        power_spectrum = np.abs(fft_vals) ** 2

        # Check for common SSVEP frequencies (6-20 Hz)
        ssvep_freqs = [6, 7, 8, 9, 10, 12, 15, 18, 20]

        for freq in ssvep_freqs:
            # Find nearest frequency bin
            freq_idx = np.argmin(np.abs(freqs - freq))
            # Take power in narrow band around frequency
            band_width = 2
            band_indices = np.where(np.abs(freqs - freq) <= band_width)[0]
            band_power = np.mean(power_spectrum[band_indices], axis=0)
            features.append(np.mean(band_power))

        return features

    def _extract_asymmetry_features(self, signal_data: np.ndarray) -> List[float]:
        """Extract hemispheric asymmetry features"""
        features = []

        if signal_data.shape[1] >= 2:
            # Frontal asymmetry (often related to approach/avoidance)
            left_channels = signal_data[:, :signal_data.shape[1]//2]
            right_channels = signal_data[:, signal_data.shape[1]//2:]

            # Power asymmetry
            left_power = np.mean(left_channels ** 2)
            right_power = np.mean(right_channels ** 2)
            asymmetry = (left_power - right_power) / (left_power + right_power + 1e-10)
            features.append(asymmetry)

            # Alpha asymmetry (related to emotional valence)
            left_alpha = self._band_power(left_channels, 8, 13)
            right_alpha = self._band_power(right_channels, 8, 13)
            alpha_asymmetry = (left_alpha - right_alpha) / (left_alpha + right_alpha + 1e-10)
            features.append(alpha_asymmetry)

        return features

    def _band_power(self, signal_data: np.ndarray, low_freq: float, high_freq: float) -> float:
        """Calculate power in specific frequency band"""
        sampling_rate = 250
        fft_vals = np.fft.fft(signal_data, axis=0)
        freqs = np.fft.fftfreq(signal_data.shape[0], 1/sampling_rate)
        power_spectrum = np.abs(fft_vals) ** 2

        # Find frequency indices for band
        band_indices = np.where((freqs >= low_freq) & (freqs <= high_freq))[0]
        if len(band_indices) > 0:
            return np.mean(power_spectrum[band_indices])
        return 0

    def _extract_connectivity_features(self, processed_signal: ProcessedSignal) -> List[float]:
        """Extract connectivity features for complex thoughts"""
        signal_data = processed_signal.filtered_signal
        features = []

        if signal_data.shape[1] > 1:
            # Phase locking value
            analytic_signal = signal.hilbert(signal_data, axis=0)
            instantaneous_phase = np.unwrap(np.angle(analytic_signal), axis=0)

            phase_lock_values = []
            for i in range(signal_data.shape[1]):
                for j in range(i+1, signal_data.shape[1]):
                    phase_diff = instantaneous_phase[:, i] - instantaneous_phase[:, j]
                    plv = np.abs(np.mean(np.exp(1j * phase_diff)))
                    phase_lock_values.append(plv)

            if phase_lock_values:
                features.extend([
                    np.mean(phase_lock_values),
                    np.max(phase_lock_values),
                    np.std(phase_lock_values)
                ])

            # Coherence features
            coherence_matrix = []
            for i in range(min(4, signal_data.shape[1])):
                for j in range(i+1, min(4, signal_data.shape[1])):
                    f, Cxy = signal.coherence(
                        signal_data[:, i], signal_data[:, j],
                        fs=250, nperseg=128
                    )
                    coherence_matrix.append(np.mean(Cxy))

            if coherence_matrix:
                features.extend([
                    np.mean(coherence_matrix),
                    np.max(coherence_matrix),
                    np.std(coherence_matrix)
                ])

        return features

    def _extract_complexity_features(self, processed_signal: ProcessedSignal) -> List[float]:
        """Extract complexity and entropy features"""
        signal_data = processed_signal.filtered_signal
        features = []

        # Sample entropy (cognitive complexity)
        for ch in range(min(3, signal_data.shape[1])):
            entropy_val = self._sample_entropy(signal_data[:, ch])
            features.append(entropy_val)

        # Fractal dimension (cognitive processing)
        for ch in range(min(3, signal_data.shape[1])):
            fd = self._fractal_dimension(signal_data[:, ch])
            features.append(fd)

        # Hurst exponent (long-range correlation in thoughts)
        for ch in range(min(3, signal_data.shape[1])):
            hurst = self._hurst_exponent(signal_data[:, ch])
            features.append(hurst)

        return features

    def _extract_temporal_features(self, processed_signal: ProcessedSignal) -> List[float]:
        """Extract temporal dynamics features"""
        signal_data = processed_signal.filtered_signal
        features = []

        # Autocorrelation (temporal persistence)
        for ch in range(min(2, signal_data.shape[1])):
            autocorr = np.correlate(signal_data[:, ch], signal_data[:, ch], mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            # Normalize
            autocorr = autocorr / autocorr[0]
            # Features from autocorrelation
            features.extend([
                autocorr[1] if len(autocorr) > 1 else 0,  # Lag-1 correlation
                np.mean(autocorr[1:10]) if len(autocorr) > 10 else 0,  # Short-term correlation
            ])

        # Rate of change (cognitive dynamics)
        gradient = np.gradient(signal_data, axis=0)
        features.extend([
            np.mean(np.abs(gradient)),
            np.std(np.abs(gradient)),
            np.max(np.abs(gradient))
        ])

        # Variability (cognitive flexibility)
        rolling_std = pd.DataFrame(signal_data).rolling(window=10).std().fillna(0).values
        features.extend([
            np.mean(rolling_std),
            np.std(rolling_std)
        ])

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

        # Linear regression on log-log plot
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

class ThoughtModel:
    """Neural network model for thought classification"""

    def __init__(self, input_size: int, num_classes: int):
        self.input_size = input_size
        self.num_classes = num_classes
        self.model = self._build_model()
        self.is_trained = False

    def _build_model(self) -> keras.Model:
        """Build deep neural network for thought classification"""
        model = keras.Sequential([
            layers.Input(shape=(self.input_size,)),

            # Dense layers with batch normalization
            layers.Dense(512, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),

            layers.Dense(256, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),

            layers.Dense(128, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),

            # Attention mechanism
            layers.Dense(64, activation='tanh'),
            layers.Dense(64, activation='sigmoid'),

            layers.Dense(32, activation='relu'),

            # Output layer
            layers.Dense(self.num_classes, activation='softmax')
        ])

        # Compile model
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy', 'top_k_categorical_accuracy']
        )

        return model

    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray = None, y_val: np.ndarray = None,
              epochs: int = 100, batch_size: int = 32) -> Dict[str, Any]:
        """Train the thought classification model"""
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(patience=20, restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=10),
            keras.callbacks.ModelCheckpoint(
                'best_thought_model.h5',
                save_best_only=True,
                monitor='val_accuracy'
            )
        ]

        # Validation data
        validation_data = (X_val, y_val) if X_val is not None else None

        # Train model
        history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )

        self.is_trained = True
        return history.history

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Predict thought probabilities"""
        if not self.is_trained:
            raise RuntimeError("Model must be trained before prediction")

        # Ensure features are in correct shape
        if features.ndim == 1:
            features = features.reshape(1, -1)

        return self.model.predict(features, verbose=0)[0]

    def save_model(self, filepath: str):
        """Save trained model"""
        if self.is_trained:
            self.model.save(filepath)
        else:
            raise RuntimeError("Cannot save untrained model")

    def load_model(self, filepath: str):
        """Load trained model"""
        self.model = keras.models.load_model(filepath)
        self.is_trained = True

class EnsembleThoughtDetector:
    """Ensemble of models for robust thought detection"""

    def __init__(self, input_size: int, categories: List[str]):
        self.input_size = input_size
        self.categories = categories
        self.num_classes = len(categories)

        # Multiple models for ensemble
        self.models = {
            'deep_nn': ThoughtModel(input_size, self.num_classes),
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'gradient_boost': GradientBoostingClassifier(n_estimators=100, random_state=42),
            'svm': SVC(probability=True, random_state=42)
        }

        self.feature_engineer = FeatureEngineer()
        self.is_trained = False
        self.weights = np.ones(len(self.models)) / len(self.models)

    def train_ensemble(self, training_data: List[Tuple[ProcessedSignal, str]]) -> Dict[str, Any]:
        """Train ensemble of models"""
        # Extract features and labels
        X = []
        y = []

        for signal, label in training_data:
            features = self.feature_engineer.extract_thought_features(signal)
            X.append(features)
            y.append(label)

        X = np.array(X)
        y = np.array(y)

        # Encode labels
        self.label_encoder = LabelEncoder()
        y_encoded = self.label_encoder.fit_transform(y)
        y_categorical = keras.utils.to_categorical(y_encoded)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )

        # Train deep neural network
        print("Training Deep Neural Network...")
        history = self.models['deep_nn'].train(
            X_train, keras.utils.to_categorical(y_train),
            X_test, keras.utils.to_categorical(y_test)
        )

        # Train traditional ML models
        print("Training Random Forest...")
        self.models['random_forest'].fit(X_train, y_train)

        print("Training Gradient Boosting...")
        self.models['gradient_boost'].fit(X_train, y_train)

        print("Training SVM...")
        self.models['svm'].fit(X_train, y_train)

        # Evaluate ensemble weights based on validation performance
        self._calculate_ensemble_weights(X_test, y_test)

        self.is_trained = True

        return {
            'deep_nn_history': history,
            'ensemble_weights': self.weights
        }

    def _calculate_ensemble_weights(self, X_val: np.ndarray, y_val: np.ndarray):
        """Calculate optimal weights for ensemble based on validation performance"""
        scores = []

        # Get predictions from each model
        predictions = {}

        for name, model in self.models.items():
            if name == 'deep_nn':
                pred_probs = model.predict(X_val)
                pred_labels = np.argmax(pred_probs, axis=1)
            else:
                pred_labels = model.predict(X_val)
                pred_probs = model.predict_proba(X_val)

            accuracy = accuracy_score(y_val, pred_labels)
            scores.append(accuracy)
            predictions[name] = pred_probs

        # Calculate weights based on performance
        scores = np.array(scores)
        self.weights = scores / np.sum(scores)

        print(f"Ensemble weights: {dict(zip(self.models.keys(), self.weights))}")

    def detect_thought(self, processed_signal: ProcessedSignal) -> ThoughtPattern:
        """Detect thought pattern from processed neural signal"""
        if not self.is_trained:
            raise RuntimeError("Detector must be trained before use")

        # Extract features
        features = self.feature_engineer.extract_thought_features(processed_signal)

        # Get predictions from all models
        ensemble_predictions = np.zeros(self.num_classes)

        for name, model in self.models.items():
            try:
                if name == 'deep_nn':
                    pred = model.predict(features)
                else:
                    pred = model.predict_proba(features.reshape(1, -1))[0]

                # Apply model weight
                weight_idx = list(self.models.keys()).index(name)
                ensemble_predictions += pred * self.weights[weight_idx]

            except Exception as e:
                print(f"Error in model {name}: {e}")
                continue

        # Normalize predictions
        ensemble_predictions = ensemble_predictions / np.sum(ensemble_predictions)

        # Get top prediction
        top_idx = np.argmax(ensemble_predictions)
        confidence = ensemble_predictions[top_idx]
        predicted_label = self.label_encoder.inverse_transform([top_idx])[0]

        # Create probability distribution
        prob_distribution = {
            self.label_encoder.inverse_transform([i])[0]: ensemble_predictions[i]
            for i in range(len(ensemble_predictions))
        }

        # Determine thought type and category
        thought_type, thought_category = self._classify_thought(predicted_label)

        return ThoughtPattern(
            timestamp=processed_signal.timestamp,
            thought_type=thought_type,
            category=thought_category,
            confidence=float(confidence),
            probability_distribution=prob_distribution,
            neural_signature=features,
            metadata={
                'model_predictions': {
                    name: float(ensemble_predictions[top_idx])
                    for name in self.models.keys()
                }
            }
        )

    def _classify_thought(self, label: str) -> Tuple[ThoughtType, ThoughtCategory]:
        """Classify thought into type and category"""
        try:
            category = ThoughtCategory(label)
        except ValueError:
            # Default to cognitive if unknown
            category = ThoughtCategory.THINK

        # Determine type based on category
        if category in [ThoughtCategory.MOVE_FORWARD, ThoughtCategory.MOVE_BACKWARD,
                       ThoughtCategory.MOVE_LEFT, ThoughtCategory.MOVE_RIGHT,
                       ThoughtCategory.JUMP, ThoughtCategory.CROUCH,
                       ThoughtCategory.INTERACT, ThoughtCategory.ATTACK,
                       ThoughtCategory.DEFEND]:
            thought_type = ThoughtType.COMMAND
        elif category in [ThoughtCategory.HAPPY, ThoughtCategory.SAD,
                         ThoughtCategory.ANGRY, ThoughtCategory.FEARFUL,
                         ThoughtCategory.SURPRISED, ThoughtCategory.DISGUSTED,
                         ThoughtCategory.CALM, ThoughtCategory.EXCITED]:
            thought_type = ThoughtType.EMOTION
        elif category in [ThoughtCategory.FOCUS, ThoughtCategory.RELAX,
                         ThoughtCategory.MEDITATE]:
            thought_type = ThoughtType.ATTENTION
        elif category in [ThoughtCategory.RECALL_MEMORY, ThoughtCategory.STORE_MEMORY,
                         ThoughtCategory.RECOGNIZE, ThoughtCategory.FORGET]:
            thought_type = ThoughtType.MEMORY
        elif category in [ThoughtCategory.VISUALIZE, ThoughtCategory.IMAGINE_MOVEMENT,
                         ThoughtCategory.RECALL_SCENE, ThoughtCategory.CREATE_IMAGE]:
            thought_type = ThoughtType.IMAGERY
        elif category in [ThoughtCategory.THINK, ThoughtCategory.PLAN,
                         ThoughtCategory.SOLVE, ThoughtCategory.CREATE,
                         ThoughtCategory.ANALYZE]:
            thought_type = ThoughtType.COGNITIVE
        else:
            thought_type = ThoughtType.INTENTION

        return thought_type, category

    def save_ensemble(self, directory: str):
        """Save entire ensemble"""
        os.makedirs(directory, exist_ok=True)

        # Save deep learning model
        self.models['deep_nn'].save_model(os.path.join(directory, 'deep_nn.h5'))

        # Save traditional models
        for name, model in self.models.items():
            if name != 'deep_nn':
                with open(os.path.join(directory, f'{name}.pkl'), 'wb') as f:
                    pickle.dump(model, f)

        # Save metadata
        metadata = {
            'categories': self.categories,
            'weights': self.weights,
            'is_trained': self.is_trained,
            'label_encoder': self.label_encoder
        }

        with open(os.path.join(directory, 'metadata.pkl'), 'wb') as f:
            pickle.dump(metadata, f)

    def load_ensemble(self, directory: str):
        """Load entire ensemble"""
        # Load deep learning model
        self.models['deep_nn'].load_model(os.path.join(directory, 'deep_nn.h5'))

        # Load traditional models
        for name, model in self.models.items():
            if name != 'deep_nn':
                with open(os.path.join(directory, f'{name}.pkl'), 'rb') as f:
                    self.models[name] = pickle.load(f)

        # Load metadata
        with open(os.path.join(directory, 'metadata.pkl'), 'rb') as f:
            metadata = pickle.load(f)

        self.categories = metadata['categories']
        self.weights = metadata['weights']
        self.is_trained = metadata['is_trained']
        self.label_encoder = metadata['label_encoder']

class ThoughtDetector:
    """Main thought detection system"""

    def __init__(self, model_directory: str = "thought_models"):
        self.model_directory = model_directory
        self.detector = None
        self.is_initialized = False

        # Real-time processing
        self.detection_queue = asyncio.Queue()
        self.result_queue = asyncio.Queue()
        self.is_running = False

        # Callbacks
        self.detection_callbacks = []

        # Metrics
        self.metrics = {
            'thoughts_detected': 0,
            'confidence_scores': deque(maxlen=100),
            'detection_times': deque(maxlen=100),
            'category_counts': {}
        }

        self.logger = logging.getLogger(__name__)

    async def initialize(self, categories: List[str] = None) -> bool:
        """Initialize the thought detector"""
        try:
            # Default categories if not provided
            if categories is None:
                categories = [
                    # Movement commands
                    'move_forward', 'move_backward', 'move_left', 'move_right',
                    'jump', 'crouch', 'interact', 'attack', 'defend',

                    # Cognitive states
                    'focus', 'relax', 'meditate', 'think', 'plan',

                    # Emotional states
                    'happy', 'sad', 'calm', 'excited'
                ]

            # Initialize feature engineer to determine input size
            dummy_signal = self._create_dummy_signal()
            feature_engineer = FeatureEngineer()
            dummy_features = feature_engineer.extract_thought_features(dummy_signal)
            input_size = len(dummy_features)

            # Create ensemble detector
            self.detector = EnsembleThoughtDetector(input_size, categories)

            # Try to load existing models
            if os.path.exists(self.model_directory):
                try:
                    self.detector.load_ensemble(self.model_directory)
                    self.logger.info("Loaded existing thought detection models")
                except Exception as e:
                    self.logger.warning(f"Could not load existing models: {e}")
                    self.detector.is_trained = False

            self.is_initialized = True
            self.logger.info("Thought detector initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize thought detector: {e}")
            return False

    def _create_dummy_signal(self) -> ProcessedSignal:
        """Create dummy processed signal for feature engineering"""
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

    async def train_detector(self, training_data: List[Tuple[ProcessedSignal, str]]) -> bool:
        """Train the thought detector with labeled data"""
        try:
            if not self.is_initialized:
                await self.initialize()

            if len(training_data) < 10:
                self.logger.error("Insufficient training data (minimum 10 samples)")
                return False

            self.logger.info(f"Training detector with {len(training_data)} samples")

            # Train the ensemble
            training_results = self.detector.train_ensemble(training_data)

            # Save trained models
            self.detector.save_ensemble(self.model_directory)

            self.logger.info("Thought detector training completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Training failed: {e}")
            return False

    async def start_detection(self):
        """Start real-time thought detection"""
        if not self.is_initialized or not self.detector.is_trained:
            raise RuntimeError("Detector must be initialized and trained")

        self.is_running = True
        self.logger.info("Starting real-time thought detection")

        # Start detection loop
        asyncio.create_task(self._detection_loop())

    async def stop_detection(self):
        """Stop real-time thought detection"""
        self.is_running = False
        self.logger.info("Stopping thought detection")

    async def _detection_loop(self):
        """Main detection loop"""
        while self.is_running:
            try:
                # Get signal from queue
                processed_signal = await asyncio.wait_for(
                    self.detection_queue.get(), timeout=1.0
                )

                # Detect thought
                start_time = time.time()
                thought_pattern = self.detector.detect_thought(processed_signal)
                detection_time = time.time() - start_time

                # Update metrics
                self.metrics['thoughts_detected'] += 1
                self.metrics['confidence_scores'].append(thought_pattern.confidence)
                self.metrics['detection_times'].append(detection_time)

                # Update category counts
                category = thought_pattern.category.value
                self.metrics['category_counts'][category] = \
                    self.metrics['category_counts'].get(category, 0) + 1

                # Add metadata
                thought_pattern.metadata['detection_time'] = detection_time

                # Queue result
                await self.result_queue.put(thought_pattern)

                # Trigger callbacks
                for callback in self.detection_callbacks:
                    try:
                        await callback(thought_pattern)
                    except Exception as e:
                        self.logger.error(f"Callback error: {e}")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Detection loop error: {e}")

    async def add_signal(self, processed_signal: ProcessedSignal):
        """Add processed signal for thought detection"""
        if self.is_running:
            await self.detection_queue.put(processed_signal)

    async def get_latest_thought(self) -> Optional[ThoughtPattern]:
        """Get the most recent detected thought"""
        try:
            while not self.result_queue.empty():
                self.latest_thought = self.result_queue.get_nowait()
            return self.latest_thought
        except (asyncio.QueueEmpty, AttributeError):
            return None

    def add_detection_callback(self, callback: Callable[[ThoughtPattern], None]):
        """Add callback for thought detection events"""
        self.detection_callbacks.append(callback)

    def get_metrics(self) -> Dict[str, Any]:
        """Get detection metrics"""
        return {
            'thoughts_detected': self.metrics['thoughts_detected'],
            'average_confidence': np.mean(list(self.metrics['confidence_scores'])) if self.metrics['confidence_scores'] else 0,
            'average_detection_time': np.mean(list(self.metrics['detection_times'])) if self.metrics['detection_times'] else 0,
            'category_distribution': dict(self.metrics['category_counts']),
            'is_running': self.is_running,
            'is_trained': self.detector.is_trained if self.detector else False,
            'queue_sizes': {
                'detection_queue': self.detection_queue.qsize(),
                'result_queue': self.result_queue.qsize()
            }
        }

class ThoughtInterpreter:
    """Interpret detected thoughts into actionable intents"""

    def __init__(self):
        self.interpretation_rules = self._load_interpretation_rules()
        self.context_history = deque(maxlen=10)

    def _load_interpretation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load rules for interpreting thoughts into intents"""
        return {
            # Movement commands
            'move_forward': {
                'intent': 'move_character',
                'parameters': {'direction': 'forward', 'speed': 1.0},
                'urgency': 0.7,
                'context_required': ['character_position', 'environment']
            },
            'move_backward': {
                'intent': 'move_character',
                'parameters': {'direction': 'backward', 'speed': 1.0},
                'urgency': 0.7,
                'context_required': ['character_position']
            },
            'move_left': {
                'intent': 'move_character',
                'parameters': {'direction': 'left', 'speed': 1.0},
                'urgency': 0.7,
                'context_required': ['character_position']
            },
            'move_right': {
                'intent': 'move_character',
                'parameters': {'direction': 'right', 'speed': 1.0},
                'urgency': 0.7,
                'context_required': ['character_position']
            },
            'jump': {
                'intent': 'character_action',
                'parameters': {'action': 'jump', 'height': 1.0},
                'urgency': 0.8,
                'context_required': ['character_position', 'ground_state']
            },
            'interact': {
                'intent': 'interact_with_object',
                'parameters': {'action': 'interact'},
                'urgency': 0.6,
                'context_required': ['nearby_objects', 'character_position']
            },

            # Cognitive states
            'focus': {
                'intent': 'attention_state',
                'parameters': {'state': 'focused', 'intensity': 0.8},
                'urgency': 0.3,
                'context_required': ['current_task']
            },
            'relax': {
                'intent': 'attention_state',
                'parameters': {'state': 'relaxed', 'intensity': 0.7},
                'urgency': 0.2,
                'context_required': ['current_task']
            },
            'think': {
                'intent': 'cognitive_processing',
                'parameters': {'process': 'thinking', 'intensity': 0.6},
                'urgency': 0.4,
                'context_required': ['current_puzzle', 'available_information']
            },
            'plan': {
                'intent': 'strategic_planning',
                'parameters': {'process': 'planning', 'horizon': 'medium'},
                'urgency': 0.5,
                'context_required': ['objectives', 'resources']
            },

            # Emotional states
            'happy': {
                'intent': 'emotional_response',
                'parameters': {'emotion': 'happiness', 'intensity': 0.7},
                'urgency': 0.3,
                'context_required': ['recent_events', 'character_state']
            },
            'excited': {
                'intent': 'emotional_response',
                'parameters': {'emotion': 'excitement', 'intensity': 0.8},
                'urgency': 0.6,
                'context_required': ['upcoming_events', 'character_state']
            },
            'calm': {
                'intent': 'emotional_response',
                'parameters': {'emotion': 'calmness', 'intensity': 0.7},
                'urgency': 0.2,
                'context_required': ['environment', 'character_state']
            }
        }

    def interpret_thought(self, thought_pattern: ThoughtPattern,
                         context: Dict[str, Any] = None) -> Optional[ThoughtIntent]:
        """Interpret thought pattern into actionable intent"""
        category = thought_pattern.category.value

        # Check if we have interpretation rules for this category
        if category not in self.interpretation_rules:
            return None

        rule = self.interpretation_rules[category]

        # Check confidence threshold
        if thought_pattern.confidence < 0.5:  # Configurable threshold
            return None

        # Create intent
        intent = ThoughtIntent(
            timestamp=thought_pattern.timestamp,
            intent=rule['intent'],
            parameters=rule['parameters'].copy(),
            confidence=thought_pattern.confidence,
            urgency=rule['urgency'] * thought_pattern.confidence,
            context=context or {}
        )

        # Add thought metadata to context
        intent.context.update({
            'thought_type': thought_pattern.thought_type.value,
            'thought_category': thought_pattern.category.value,
            'probability_distribution': thought_pattern.probability_distribution
        })

        return intent

    def update_context(self, context: Dict[str, Any]):
        """Update interpretation context"""
        self.context_history.append({
            'timestamp': time.time(),
            'context': context.copy()
        })

# Main interface for external use
async def create_thought_detector(categories: List[str] = None,
                                model_directory: str = "thought_models") -> ThoughtDetector:
    """Create and initialize a thought detector"""
    detector = ThoughtDetector(model_directory)
    success = await detector.initialize(categories)

    if not success:
        raise RuntimeError("Failed to initialize thought detector")

    return detector

if __name__ == "__main__":
    # Example usage
    async def main():
        # Create detector
        detector = await create_thought_detector()

        # Add callback
        def on_thought_detected(thought_pattern):
            print(f"Thought detected: {thought_pattern.category.value} "
                  f"(confidence: {thought_pattern.confidence:.2f})")

        detector.add_detection_callback(on_thought_detected)

        # Start detection
        await detector.start_detection()

        # Simulate some signals (in real use, these would come from neural interface)
        from .neural_interface import create_neural_interface

        neural_interface = await create_neural_interface("simulator")
        await neural_interface.calibrate(duration=5.0)

        # Process signals for a while
        for _ in range(10):
            signal = neural_interface.get_latest_signal()
            if signal:
                await detector.add_signal(signal)
            await asyncio.sleep(0.1)

        # Get metrics
        metrics = detector.get_metrics()
        print(f"Detection metrics: {metrics}")

        # Stop detection
        await detector.stop_detection()
        await neural_interface.shutdown()

    asyncio.run(main())