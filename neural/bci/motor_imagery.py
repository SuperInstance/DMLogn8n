#!/usr/bin/env python3
"""
Motor Imagery System - Control System Through Imagined Movements
Advanced brain-computer interface for controlling game characters and actions
through imagined movements and motor intentions.

This module implements sophisticated algorithms for detecting motor imagery
patterns, enabling users to control virtual environments through thought alone,
including movement, actions, and complex motor sequences.
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
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
import torch.optim as optim

# Signal Processing
from scipy import signal
from scipy.fft import fft, fftfreq
from scipy.stats import entropy
import cv2

# Local imports
from .neural_interface import ProcessedSignal, NeuralSignal
from .thought_detector import ThoughtPattern

class MotorAction(Enum):
    """Types of motor actions that can be controlled"""
    # Basic movements
    WALK_FORWARD = "walk_forward"
    WALK_BACKWARD = "walk_backward"
    WALK_LEFT = "walk_left"
    WALK_RIGHT = "walk_right"
    RUN_FORWARD = "run_forward"
    JUMP = "jump"
    CROUCH = "crouch"
    CRAWL = "crawl"

    # Upper body actions
    PUNCH = "punch"
    KICK = "kick"
    GRAB = "grab"
    THROW = "throw"
    PUSH = "push"
    PULL = "pull"

    # Fine motor control
    POINT = "point"
    WAVE = "wave"
    NOD = "nod"
    SHAKE_HEAD = "shake_head"

    # Complex sequences
    DANCE = "dance"
    FIGHT_SEQUENCE = "fight_sequence"
    CLIMB = "climb"
    SWIM = "swim"

class BodyPart(Enum):
    """Body parts for motor imagery classification"""
    LEFT_HAND = "left_hand"
    RIGHT_HAND = "right_hand"
    LEFT_FOOT = "left_foot"
    RIGHT_FOOT = "right_foot"
    TONGUE = "tongue"
    HEAD = "head"
    TORSO = "torso"
    BOTH_HANDS = "both_hands"
    BOTH_FEET = "both_feet"

class ImageryType(Enum):
    """Types of motor imagery"""
    KINESTHETIC = "kinesthetic"  # Feeling the movement
    VISUAL = "visual"  # Seeing the movement
    MIXED = "mixed"  # Combination of both

@dataclass
class MotorImageryPattern:
    """Detected motor imagery pattern"""
    timestamp: float
    action: MotorAction
    body_part: BodyPart
    imagery_type: ImageryType
    confidence: float
    intensity: float
    duration: float
    neural_signature: np.ndarray
    spatial_pattern: Dict[str, float]
    frequency_features: Dict[str, float]
    metadata: Dict[str, Any]

@dataclass
class MotorCommand:
    """Executable motor command for game control"""
    timestamp: float
    action: MotorAction
    parameters: Dict[str, Any]
    confidence: float
    urgency: float
    target_coordinates: Optional[Tuple[float, float, float]]
    execution_time: Optional[float]

class CSPFeatureExtractor:
    """Common Spatial Pattern feature extraction for motor imagery"""

    def __init__(self, num_components: int = 4):
        self.num_components = num_components
        self.csp_filters = {}
        self.spatial_patterns = {}
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Fit CSP filters to training data"""
        classes = np.unique(y)
        self.csp_filters = {}
        self.spatial_patterns = {}

        for i, class_label in enumerate(classes):
            # Get data for this class
            class_data = X[y == class_label]

            # Calculate covariance matrix
            cov_matrix = self._calculate_covariance_matrix(class_data)

            # Store for CSP computation
            if class_label not in self.csp_filters:
                self.csp_filters[class_label] = cov_matrix

        # Compute CSP filters between classes
        if len(classes) >= 2:
            self._compute_csp_filters(classes)

        self.is_fitted = True

    def _calculate_covariance_matrix(self, data: np.ndarray) -> np.ndarray:
        """Calculate covariance matrix for EEG data"""
        # data shape: (trials, channels, time)
        covariances = []

        for trial in data:
            # Normalize data
            trial = trial - np.mean(trial, axis=1, keepdims=True)

            # Calculate covariance
            cov = np.cov(trial)
            if cov.shape == ():
                cov = np.array([[cov]])

            covariances.append(cov)

        # Average covariance across trials
        avg_cov = np.mean(covariances, axis=0)
        return avg_cov

    def _compute_csp_filters(self, classes: np.ndarray) -> None:
        """Compute CSP filters between classes"""
        if len(classes) < 2:
            return

        # Get covariance matrices for two classes
        class1, class2 = classes[0], classes[1]
        cov1 = self.csp_filters[class1]
        cov2 = self.csp_filters[class2]

        # Solve generalized eigenvalue problem
        try:
            # Regularize matrices
            cov1_reg = cov1 + 0.01 * np.eye(cov1.shape[0])
            cov2_reg = cov2 + 0.01 * np.eye(cov2.shape[0])

            # Compute generalized eigenvalues and eigenvectors
            eigenvalues, eigenvectors = self._generalized_eigendecomp(cov1_reg, cov2_reg)

            # Sort eigenvectors by eigenvalues
            sorted_indices = np.argsort(eigenvalues)[::-1]
            sorted_vectors = eigenvectors[:, sorted_indices]

            # Select CSP filters (first and last components)
            filters = np.vstack([
                sorted_vectors[:, :self.num_components//2].T,
                sorted_vectors[:, -self.num_components//2:].T
            ])

            self.spatial_patterns['csp_filters'] = filters

        except Exception as e:
            logging.warning(f"CSP computation failed: {e}")
            # Fallback to simple spatial filtering
            self.spatial_patterns['csp_filters'] = np.eye(cov1.shape[0])[:self.num_components]

    def _generalized_eigendecomp(self, A: np.ndarray, B: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Solve generalized eigenvalue problem A*v = lambda*B*v"""
        try:
            # Whiten B
            eigenvalues_B, eigenvectors_B = np.linalg.eigh(B)
            D = np.diag(1.0 / np.sqrt(eigenvalues_B + 1e-10))
            P = eigenvectors_B @ D @ eigenvectors_B.T

            # Transform A
            A_transformed = P @ A @ P.T

            # Standard eigenvalue decomposition
            eigenvalues, eigenvectors = np.linalg.eigh(A_transformed)

            # Transform back
            eigenvectors = P.T @ eigenvectors

            return eigenvalues, eigenvectors

        except Exception as e:
            logging.warning(f"Generalized eigendecomposition failed: {e}")
            # Fallback to standard eigenvalue decomposition
            eigenvalues, eigenvectors = np.linalg.eigh(A)
            return eigenvalues, eigenvectors

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform data using CSP filters"""
        if not self.is_fitted or 'csp_filters' not in self.spatial_patterns:
            return X

        filters = self.spatial_patterns['csp_filters']

        # Apply CSP filters to each trial
        transformed = []
        for trial in X:
            # Apply spatial filters
            csp_features = filters @ trial
            transformed.append(csp_features)

        return np.array(transformed)

    def extract_features(self, X: np.ndarray) -> np.ndarray:
        """Extract CSP features from EEG data"""
        if not self.is_fitted:
            # Fallback to simple variance features
            return np.array([np.var(trial, axis=1) for trial in X])

        # Transform with CSP
        csp_data = self.transform(X)

        # Extract log-variance features
        features = []
        for trial in csp_data:
            # Log-variance of each component
            log_var = np.log(np.var(trial, axis=1) + 1e-10)
            features.append(log_var)

        return np.array(features)

class MotorImageryClassifier:
    """Advanced motor imagery classification system"""

    def __init__(self, num_channels: int, num_actions: int):
        self.num_channels = num_channels
        self.num_actions = num_actions
        self.csp_extractor = CSPFeatureExtractor()
        self.models = self._initialize_models()
        self.scalers = {}
        self.is_trained = False

    def _initialize_models(self) -> Dict[str, Any]:
        """Initialize multiple classification models"""
        return {
            'cnn_lstm': self._build_cnn_lstm_model(),
            'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'svm': SVC(kernel='rbf', probability=True, random_state=42),
            'ensemble_weights': np.ones(3) / 3
        }

    def _build_cnn_lstm_model(self) -> keras.Model:
        """Build CNN-LSTM model for spatiotemporal feature extraction"""
        input_shape = (self.num_channels, 250, 1)  # channels, timepoints, features

        # Input layer
        inputs = layers.Input(shape=input_shape)

        # CNN layers for spatial feature extraction
        x = layers.Conv2D(32, (self.num_channels, 3), activation='relu', padding='same')(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.Conv2D(64, (1, 5), activation='relu', padding='same')(x)
        x = layers.BatchNormalization()(x)
        x = layers.MaxPooling2D((1, 2))(x)
        x = layers.Dropout(0.3)(x)

        # Reshape for LSTM
        x = layers.Reshape((-1, 64))(x)

        # LSTM layers for temporal modeling
        x = layers.LSTM(128, return_sequences=True)(x)
        x = layers.Dropout(0.3)(x)
        x = layers.LSTM(64)(x)
        x = layers.Dropout(0.3)(x)

        # Dense layers
        x = layers.Dense(128, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.4)(x)
        x = layers.Dense(64, activation='relu')(x)
        x = layers.Dropout(0.3)(x)

        # Output layer
        outputs = layers.Dense(self.num_actions, activation='softmax')(x)

        model = keras.Model(inputs=inputs, outputs=outputs)
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )

        return model

    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray = None, y_val: np.ndarray = None) -> Dict[str, Any]:
        """Train motor imagery classifiers"""
        training_results = {}

        # Prepare data for CNN-LSTM
        X_cnn_lstm = self._prepare_cnn_lstm_data(X_train)
        y_cnn_lstm = keras.utils.to_categorical(y_train, num_classes=self.num_actions)

        # Train CNN-LSTM model
        print("Training CNN-LSTM model...")
        history = self.models['cnn_lstm'].fit(
            X_cnn_lstm, y_cnn_lstm,
            validation_data=(self._prepare_cnn_lstm_data(X_val),
                           keras.utils.to_categorical(y_val, num_classes=self.num_actions)) if X_val is not None else None,
            epochs=50,
            batch_size=32,
            callbacks=[
                keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
                keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5)
            ],
            verbose=1
        )
        training_results['cnn_lstm'] = history.history

        # Train CSP-based models
        print("Training CSP feature extractor...")
        self.csp_extractor.fit(X_train, y_train)

        # Extract CSP features
        X_csp = self.csp_extractor.extract_features(X_train)

        # Scale features
        scaler = StandardScaler()
        X_csp_scaled = scaler.fit_transform(X_csp)
        self.scalers['csp'] = scaler

        # Train Random Forest
        print("Training Random Forest...")
        self.models['random_forest'].fit(X_csp_scaled, y_train)

        # Train SVM
        print("Training SVM...")
        self.models['svm'].fit(X_csp_scaled, y_train)

        # Calculate ensemble weights
        if X_val is not None:
            self._calculate_ensemble_weights(X_val, y_val)

        self.is_trained = True
        return training_results

    def _prepare_cnn_lstm_data(self, X: np.ndarray) -> np.ndarray:
        """Prepare data for CNN-LSTM model"""
        # Add channel dimension
        return X.reshape(X.shape[0], X.shape[1], X.shape[2], 1)

    def _calculate_ensemble_weights(self, X_val: np.ndarray, y_val: np.ndarray):
        """Calculate optimal ensemble weights based on validation performance"""
        scores = []

        # CNN-LSTM performance
        X_cnn_lstm = self._prepare_cnn_lstm_data(X_val)
        y_pred_cnn_lstm = self.models['cnn_lstm'].predict(X_cnn_lstm, verbose=0)
        accuracy_cnn_lstm = accuracy_score(y_val, np.argmax(y_pred_cnn_lstm, axis=1))
        scores.append(accuracy_cnn_lstm)

        # CSP-RF performance
        X_csp = self.csp_extractor.extract_features(X_val)
        X_csp_scaled = self.scalers['csp'].transform(X_csp)
        accuracy_rf = self.models['random_forest'].score(X_csp_scaled, y_val)
        scores.append(accuracy_rf)

        # CSP-SVM performance
        accuracy_svm = self.models['svm'].score(X_csp_scaled, y_val)
        scores.append(accuracy_svm)

        # Normalize weights
        scores = np.array(scores)
        self.models['ensemble_weights'] = scores / np.sum(scores)

        print(f"Ensemble weights: CNN-LSTM: {self.models['ensemble_weights'][0]:.3f}, "
              f"RF: {self.models['ensemble_weights'][1]:.3f}, "
              f"SVM: {self.models['ensemble_weights'][2]:.3f}")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict motor imagery class probabilities"""
        if not self.is_trained:
            raise RuntimeError("Models must be trained before prediction")

        # CNN-LSTM prediction
        X_cnn_lstm = self._prepare_cnn_lstm_data(X)
        pred_cnn_lstm = self.models['cnn_lstm'].predict(X_cnn_lstm, verbose=0)[0]

        # CSP-based predictions
        X_csp = self.csp_extractor.extract_features(X)
        X_csp_scaled = self.scalers['csp'].transform(X_csp)

        pred_rf = self.models['random_forest'].predict_proba(X_csp_scaled)[0]
        pred_svm = self.models['svm'].predict_proba(X_csp_scaled)[0]

        # Ensemble prediction
        ensemble_pred = (
            self.models['ensemble_weights'][0] * pred_cnn_lstm +
            self.models['ensemble_weights'][1] * pred_rf +
            self.models['ensemble_weights'][2] * pred_svm
        )

        return ensemble_pred

    def save_models(self, directory: str):
        """Save trained models"""
        import os
        os.makedirs(directory, exist_ok=True)

        # Save CNN-LSTM model
        self.models['cnn_lstm'].save(os.path.join(directory, 'cnn_lstm_model.h5'))

        # Save traditional models
        import pickle
        with open(os.path.join(directory, 'random_forest.pkl'), 'wb') as f:
            pickle.dump(self.models['random_forest'], f)
        with open(os.path.join(directory, 'svm.pkl'), 'wb') as f:
            pickle.dump(self.models['svm'], f)

        # Save CSP extractor and scalers
        with open(os.path.join(directory, 'csp_extractor.pkl'), 'wb') as f:
            pickle.dump(self.csp_extractor, f)
        with open(os.path.join(directory, 'scalers.pkl'), 'wb') as f:
            pickle.dump(self.scalers, f)

        # Save metadata
        metadata = {
            'num_channels': self.num_channels,
            'num_actions': self.num_actions,
            'ensemble_weights': self.models['ensemble_weights'],
            'is_trained': self.is_trained
        }
        with open(os.path.join(directory, 'metadata.pkl'), 'wb') as f:
            pickle.dump(metadata, f)

    def load_models(self, directory: str):
        """Load trained models"""
        import os
        import pickle

        # Load CNN-LSTM model
        self.models['cnn_lstm'] = keras.models.load_model(os.path.join(directory, 'cnn_lstm_model.h5'))

        # Load traditional models
        with open(os.path.join(directory, 'random_forest.pkl'), 'rb') as f:
            self.models['random_forest'] = pickle.load(f)
        with open(os.path.join(directory, 'svm.pkl'), 'rb') as f:
            self.models['svm'] = pickle.load(f)

        # Load CSP extractor and scalers
        with open(os.path.join(directory, 'csp_extractor.pkl'), 'rb') as f:
            self.csp_extractor = pickle.load(f)
        with open(os.path.join(directory, 'scalers.pkl'), 'rb') as f:
            self.scalers = pickle.load(f)

        # Load metadata
        with open(os.path.join(directory, 'metadata.pkl'), 'rb') as f:
            metadata = pickle.load(f)

        self.models['ensemble_weights'] = metadata['ensemble_weights']
        self.is_trained = True

class MotorImageryDetector:
    """Main motor imagery detection system"""

    def __init__(self, model_directory: str = "motor_models"):
        self.model_directory = model_directory
        self.classifier = None
        self.action_mapping = {}
        self.is_initialized = False

        # Real-time processing
        self.detection_queue = asyncio.Queue()
        self.command_queue = asyncio.Queue()
        self.is_running = False

        # Callbacks
        self.command_callbacks = []

        # Metrics
        self.metrics = {
            'commands_generated': 0,
            'confidence_scores': deque(maxlen=100),
            'detection_times': deque(maxlen=100),
            'action_counts': {},
            'false_positives': 0
        }

        self.logger = logging.getLogger(__name__)

    async def initialize(self, actions: List[MotorAction] = None) -> bool:
        """Initialize the motor imagery detector"""
        try:
            # Default actions if not provided
            if actions is None:
                actions = [
                    MotorAction.WALK_FORWARD,
                    MotorAction.WALK_BACKWARD,
                    MotorAction.WALK_LEFT,
                    MotorAction.WALK_RIGHT,
                    MotorAction.JUMP,
                    MotorAction.CROUCH,
                    MotorAction.PUNCH,
                    MotorAction.GRAB
                ]

            # Create action mapping
            self.action_mapping = {action: i for i, action in enumerate(actions)}

            # Initialize classifier
            self.classifier = MotorImageryClassifier(
                num_channels=8,  # Default number of channels
                num_actions=len(actions)
            )

            # Try to load existing models
            if os.path.exists(self.model_directory):
                try:
                    self.classifier.load_models(self.model_directory)
                    self.logger.info("Loaded existing motor imagery models")
                except Exception as e:
                    self.logger.warning(f"Could not load existing models: {e}")
                    self.classifier.is_trained = False

            self.is_initialized = True
            self.logger.info("Motor imagery detector initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize motor imagery detector: {e}")
            return False

    async def train_detector(self, training_data: List[Tuple[ProcessedSignal, MotorAction]]) -> bool:
        """Train the motor imagery detector"""
        try:
            if not self.is_initialized:
                await self.initialize()

            if len(training_data) < 20:
                self.logger.error("Insufficient training data (minimum 20 samples)")
                return False

            # Prepare training data
            X = []
            y = []

            for signal, action in training_data:
                # Extract signal segment for motor imagery
                signal_segment = self._extract_motor_imagery_segment(signal)
                if signal_segment is not None:
                    X.append(signal_segment)
                    y.append(self.action_mapping[action])

            if len(X) < 20:
                self.logger.error("Insufficient valid training segments")
                return False

            X = np.array(X)
            y = np.array(y)

            # Split data
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )

            # Train classifier
            self.logger.info(f"Training detector with {len(X_train)} samples")
            training_results = self.classifier.train(X_train, y_train, X_val, y_val)

            # Save trained models
            self.classifier.save_models(self.model_directory)

            self.logger.info("Motor imagery detector training completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Training failed: {e}")
            return False

    def _extract_motor_imagery_segment(self, processed_signal: ProcessedSignal) -> Optional[np.ndarray]:
        """Extract segment suitable for motor imagery detection"""
        signal_data = processed_signal.filtered_signal

        # Ensure we have enough data (typically 2-4 seconds)
        min_length = 500  # 2 seconds at 250 Hz
        if signal_data.shape[0] < min_length:
            return None

        # Extract the most recent segment
        segment = signal_data[-min_length:]

        # Additional preprocessing for motor imagery
        segment = self._preprocess_motor_imagery(segment)

        return segment

    def _preprocess_motor_imagery(self, signal_data: np.ndarray) -> np.ndarray:
        """Preprocess signal specifically for motor imagery"""
        # Bandpass filter for motor imagery frequencies (8-30 Hz)
        from scipy.signal import butter, filtfilt
        nyquist = 250 / 2
        b, a = butter(4, [8/nyquist, 30/nyquist], btype='band')
        filtered = filtfilt(b, a, signal_data, axis=0)

        # Notch filter for power line noise
        b_notch, a_notch = signal.iirnotch(50, 30, 250)
        filtered = signal.filtfilt(b_notch, a_notch, filtered, axis=0)

        return filtered

    async def start_detection(self):
        """Start real-time motor imagery detection"""
        if not self.is_initialized or not self.classifier.is_trained:
            raise RuntimeError("Detector must be initialized and trained")

        self.is_running = True
        self.logger.info("Starting real-time motor imagery detection")

        # Start detection loop
        asyncio.create_task(self._detection_loop())

    async def stop_detection(self):
        """Stop real-time motor imagery detection"""
        self.is_running = False
        self.logger.info("Stopping motor imagery detection")

    async def _detection_loop(self):
        """Main detection loop"""
        while self.is_running:
            try:
                # Get signal from queue
                processed_signal = await asyncio.wait_for(
                    self.detection_queue.get(), timeout=1.0
                )

                # Detect motor imagery
                start_time = time.time()
                motor_pattern = await self._detect_motor_imagery(processed_signal)
                detection_time = time.time() - start_time

                if motor_pattern:
                    # Update metrics
                    self.metrics['confidence_scores'].append(motor_pattern.confidence)
                    self.metrics['detection_times'].append(detection_time)

                    # Update action counts
                    action = motor_pattern.action.value
                    self.metrics['action_counts'][action] = \
                        self.metrics['action_counts'].get(action, 0) + 1

                    # Convert to command
                    command = self._convert_to_command(motor_pattern)
                    if command:
                        await self.command_queue.put(command)

                        # Update metrics
                        self.metrics['commands_generated'] += 1

                        # Trigger callbacks
                        for callback in self.command_callbacks:
                            try:
                                await callback(command)
                            except Exception as e:
                                self.logger.error(f"Callback error: {e}")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Detection loop error: {e}")

    async def _detect_motor_imagery(self, processed_signal: ProcessedSignal) -> Optional[MotorImageryPattern]:
        """Detect motor imagery pattern from processed signal"""
        try:
            # Extract segment
            signal_segment = self._extract_motor_imagery_segment(processed_signal)
            if signal_segment is None:
                return None

            # Add batch dimension
            signal_segment = signal_segment[np.newaxis, ...]

            # Predict action
            probabilities = self.classifier.predict(signal_segment)
            top_idx = np.argmax(probabilities)
            confidence = probabilities[top_idx]

            # Confidence threshold
            if confidence < 0.6:  # Configurable threshold
                return None

            # Get action
            action = list(self.action_mapping.keys())[top_idx]

            # Determine body part and imagery type
            body_part = self._determine_body_part(action, processed_signal)
            imagery_type = self._determine_imagery_type(processed_signal)

            # Extract features
            neural_signature = signal_segment[0]
            spatial_pattern = self._extract_spatial_features(processed_signal)
            frequency_features = self._extract_frequency_features(processed_signal)

            return MotorImageryPattern(
                timestamp=processed_signal.timestamp,
                action=action,
                body_part=body_part,
                imagery_type=imagery_type,
                confidence=float(confidence),
                intensity=self._calculate_intensity(processed_signal),
                duration=1.0,  # Default duration
                neural_signature=neural_signature,
                spatial_pattern=spatial_pattern,
                frequency_features=frequency_features,
                metadata={
                    'probability_distribution': {
                        list(self.action_mapping.keys())[i]: float(prob)
                        for i, prob in enumerate(probabilities)
                    }
                }
            )

        except Exception as e:
            self.logger.error(f"Motor imagery detection failed: {e}")
            return None

    def _determine_body_part(self, action: MotorAction, processed_signal: ProcessedSignal) -> BodyPart:
        """Determine which body part is being imagined"""
        # This would use more sophisticated analysis in practice
        action_body_map = {
            MotorAction.WALK_FORWARD: BodyPart.BOTH_FEET,
            MotorAction.WALK_BACKWARD: BodyPart.BOTH_FEET,
            MotorAction.WALK_LEFT: BodyPart.LEFT_FOOT,
            MotorAction.WALK_RIGHT: BodyPart.RIGHT_FOOT,
            MotorAction.JUMP: BodyPart.BOTH_FEET,
            MotorAction.PUNCH: BodyPart.RIGHT_HAND,
            MotorAction.GRAB: BodyPart.RIGHT_HAND,
            MotorAction.KICK: BodyPart.RIGHT_FOOT,
            MotorAction.POINT: BodyPart.RIGHT_HAND,
            MotorAction.WAVE: BodyPart.RIGHT_HAND,
        }

        return action_body_map.get(action, BodyPart.TORSO)

    def _determine_imagery_type(self, processed_signal: ProcessedSignal) -> ImageryType:
        """Determine type of motor imagery"""
        # This would analyze the signal characteristics
        # For now, default to kinesthetic
        return ImageryType.KINESTHETIC

    def _extract_spatial_features(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Extract spatial features from neural signal"""
        signal_data = processed_signal.filtered_signal
        features = {}

        # Channel-wise power
        channel_powers = np.mean(signal_data ** 2, axis=0)
        for i, power in enumerate(channel_powers):
            features[f'channel_{i}_power'] = power

        # Inter-hemispheric asymmetry
        if signal_data.shape[1] >= 4:
            left_channels = signal_data[:, :signal_data.shape[1]//2]
            right_channels = signal_data[:, signal_data.shape[1]//2:]

            left_power = np.mean(left_channels ** 2)
            right_power = np.mean(right_channels ** 2)

            asymmetry = (left_power - right_power) / (left_power + right_power + 1e-10)
            features['interhemispheric_asymmetry'] = asymmetry

        return features

    def _extract_frequency_features(self, processed_signal: ProcessedSignal) -> Dict[str, float]:
        """Extract frequency domain features"""
        features = {}
        brain_waves = processed_signal.brain_waves

        # Motor-relevant frequency bands
        features['mu_power'] = brain_waves.get('ALPHA', 0)  # Mu rhythm (8-12 Hz)
        features['beta_power'] = brain_waves.get('BETA', 0)  # Beta rhythm (13-30 Hz)
        features['low_gamma_power'] = brain_waves.get('GAMMA', 0)  # Low gamma

        # Event-related desynchronization (ERD) measures
        # In practice, this would compare to baseline
        features['mu_erd'] = 1.0 - brain_waves.get('ALPHA', 0) / 0.5  # Normalized
        features['beta_ers'] = brain_waves.get('BETA', 0) / 0.5  # Normalized

        return features

    def _calculate_intensity(self, processed_signal: ProcessedSignal) -> float:
        """Calculate intensity of motor imagery"""
        # Use signal power and frequency features
        brain_waves = processed_signal.brain_waves
        total_power = sum(brain_waves.values())

        if total_power == 0:
            return 0.5

        # Weight motor-relevant frequencies
        motor_power = brain_waves.get('BETA', 0) + brain_waves.get('GAMMA', 0)
        intensity = motor_power / total_power

        return np.clip(intensity, 0, 1)

    def _convert_to_command(self, pattern: MotorImageryPattern) -> Optional[MotorCommand]:
        """Convert motor imagery pattern to executable command"""
        # Map action to command parameters
        action_params = {
            MotorAction.WALK_FORWARD: {'speed': 1.0, 'direction': 'forward'},
            MotorAction.WALK_BACKWARD: {'speed': 1.0, 'direction': 'backward'},
            MotorAction.WALK_LEFT: {'speed': 1.0, 'direction': 'left'},
            MotorAction.WALK_RIGHT: {'speed': 1.0, 'direction': 'right'},
            MotorAction.RUN_FORWARD: {'speed': 2.0, 'direction': 'forward'},
            MotorAction.JUMP: {'height': 1.0, 'duration': 0.5},
            MotorAction.CROUCH: {'duration': 1.0},
            MotorAction.PUNCH: {'force': 1.0, 'direction': 'forward'},
            MotorAction.KICK: {'force': 1.0, 'direction': 'forward'},
            MotorAction.GRAB: {'duration': 0.5, 'reach': 1.0},
            MotorAction.THROW: {'force': 1.0, 'direction': 'forward'},
            MotorAction.POINT: {'duration': 0.3},
            MotorAction.WAVE: {'duration': 1.0},
        }

        params = action_params.get(pattern.action, {})

        return MotorCommand(
            timestamp=pattern.timestamp,
            action=pattern.action,
            parameters=params,
            confidence=pattern.confidence,
            urgency=pattern.intensity,
            target_coordinates=None,
            execution_time=None
        )

    async def add_signal(self, processed_signal: ProcessedSignal):
        """Add processed signal for motor imagery detection"""
        if self.is_running:
            await self.detection_queue.put(processed_signal)

    async def get_latest_command(self) -> Optional[MotorCommand]:
        """Get the most recent motor command"""
        try:
            while not self.command_queue.empty():
                self.latest_command = self.command_queue.get_nowait()
            return self.latest_command
        except (asyncio.QueueEmpty, AttributeError):
            return None

    def add_command_callback(self, callback: Callable[[MotorCommand], None]):
        """Add callback for motor command events"""
        self.command_callbacks.append(callback)

    def get_metrics(self) -> Dict[str, Any]:
        """Get detection metrics"""
        return {
            'commands_generated': self.metrics['commands_generated'],
            'average_confidence': np.mean(list(self.metrics['confidence_scores'])) if self.metrics['confidence_scores'] else 0,
            'average_detection_time': np.mean(list(self.metrics['detection_times'])) if self.metrics['detection_times'] else 0,
            'action_distribution': dict(self.metrics['action_counts']),
            'false_positive_rate': self.metrics['false_positives'] / max(1, self.metrics['commands_generated']),
            'is_running': self.is_running,
            'is_trained': self.classifier.is_trained if self.classifier else False,
            'queue_sizes': {
                'detection_queue': self.detection_queue.qsize(),
                'command_queue': self.command_queue.qsize()
            }
        }

class MotorImageryTrainer:
    """Training system for motor imagery detection"""

    def __init__(self):
        self.training_data = []
        self.current_action = None
        self.recording = False
        self.trial_duration = 4.0  # seconds per trial
        self.trials_per_action = 20

    async def start_training_session(self, actions: List[MotorAction],
                                   user_interface: bool = True) -> Dict[str, Any]:
        """Start a guided training session"""
        session_data = {
            'start_time': time.time(),
            'actions': actions,
            'trials_completed': 0,
            'total_trials': len(actions) * self.trials_per_action,
            'collected_data': []
        }

        print(f"Starting motor imagery training session")
        print(f"Actions to train: {[action.value for action in actions]}")
        print(f"Trials per action: {self.trials_per_action}")
        print(f"Total trials: {session_data['total_trials']}")

        if user_interface:
            print("\nTraining Instructions:")
            print("1. For each action, you will see a prompt")
            print("2. When you see 'IMAGINE', imagine performing the action")
            print("3. When you see 'REST', relax and clear your mind")
            print("4. Each trial lasts 4 seconds")
            print("5. Try to be consistent in your imagery")

        # Train each action
        for action in actions:
            action_data = await self._train_action(action, self.trials_per_action)
            session_data['collected_data'].extend(action_data)
            session_data['trials_completed'] += len(action_data)

        session_data['end_time'] = time.time()
        session_data['duration'] = session_data['end_time'] - session_data['start_time']

        print(f"\nTraining session completed!")
        print(f"Total duration: {session_data['duration']:.1f} seconds")
        print(f"Triials completed: {session_data['trials_completed']}")

        return session_data

    async def _train_action(self, action: MotorAction, num_trials: int) -> List[Tuple[Any, MotorAction]]:
        """Train a specific motor imagery action"""
        action_data = []

        print(f"\nTraining action: {action.value}")
        print(f"Get ready for {num_trials} trials")

        for trial in range(num_trials):
            print(f"\nTrial {trial + 1}/{num_trials}")

            # Rest period
            print("REST - Clear your mind and relax")
            await asyncio.sleep(2)

            # Imagery period
            print(f"IMAGINE - Imagine {action.value}")
            start_time = time.time()

            # Collect data during imagery period
            trial_data = []
            while time.time() - start_time < self.trial_duration:
                # In a real implementation, this would collect actual neural data
                # For now, simulate data collection
                await asyncio.sleep(0.1)

            print("REST - Relax")
            await asyncio.sleep(2)

            # Store trial (in real implementation, would store actual neural data)
            # For now, we'll store a placeholder
            trial_data.append(f"trial_{trial}_{action.value}")
            action_data.append((trial_data, action))

        print(f"Completed {num_trials} trials for {action.value}")
        return action_data

    def simulate_training_data(self, actions: List[MotorAction],
                             trials_per_action: int = 20) -> List[Tuple[ProcessedSignal, MotorAction]]:
        """Generate simulated training data for testing"""
        training_data = []

        for action in actions:
            for trial in range(trials_per_action):
                # Create simulated processed signal
                signal_data = self._generate_simulated_motor_signal(action)
                processed_signal = self._create_simulated_processed_signal(signal_data)
                training_data.append((processed_signal, action))

        return training_data

    def _generate_simulated_motor_signal(self, action: MotorAction) -> np.ndarray:
        """Generate simulated neural signal for specific motor action"""
        # Base signal parameters
        duration = 4.0  # seconds
        sampling_rate = 250
        num_channels = 8
        num_samples = int(duration * sampling_rate)

        time_points = np.linspace(0, duration, num_samples)
        signal_data = np.zeros((num_samples, num_channels))

        # Generate action-specific patterns
        for ch in range(num_channels):
            # Base oscillations
            signal_data[:, ch] = (
                0.5 * np.sin(2 * np.pi * 10 * time_points) +  # Alpha
                0.3 * np.sin(2 * np.pi * 20 * time_points) +  # Beta
                0.1 * np.random.randn(num_samples)            # Noise
            )

            # Add motor imagery specific features
            if action in [MotorAction.WALK_FORWARD, MotorAction.WALK_BACKWARD,
                         MotorAction.WALK_LEFT, MotorAction.WALK_RIGHT]:
                # Walking imagery - increased beta in motor areas
                signal_data[:, ch] += 0.4 * np.sin(2 * np.pi * 18 * time_points)
            elif action in [MotorAction.PUNCH, MotorAction.KICK]:
                # Action imagery - increased gamma
                signal_data[:, ch] += 0.3 * np.sin(2 * np.pi * 40 * time_points)
            elif action == MotorAction.JUMP:
                # Jump imagery - complex pattern
                signal_data[:, ch] += 0.2 * np.sin(2 * np.pi * 15 * time_points)

            # Channel-specific modulation
            signal_data[:, ch] *= (1 + 0.2 * ch / num_channels)

        return signal_data

    def _create_simulated_processed_signal(self, signal_data: np.ndarray) -> ProcessedSignal:
        """Create simulated processed signal"""
        from .neural_interface import BrainWave

        # Calculate brain wave powers
        brain_waves = {}
        for wave in BrainWave:
            low, high, _ = wave.value
            from scipy.signal import butter, filtfilt
            nyquist = 250 / 2
            if high < nyquist:
                b, a = butter(4, [low/nyquist, high/nyquist], btype='band')
                band_signal = filtfilt(b, a, signal_data, axis=0)
                power = np.mean(band_signal ** 2)
                brain_waves[wave.name.lower()] = power

        return ProcessedSignal(
            timestamp=time.time(),
            raw_signal=signal_data,
            filtered_signal=signal_data,
            features={},
            brain_waves=brain_waves,
            signal_quality=0.8,
            noise_level=0.1
        )

# Main interface for external use
async def create_motor_imagery_detector(actions: List[MotorAction] = None,
                                      model_directory: str = "motor_models") -> MotorImageryDetector:
    """Create and initialize a motor imagery detector"""
    detector = MotorImageryDetector(model_directory)
    success = await detector.initialize(actions)

    if not success:
        raise RuntimeError("Failed to initialize motor imagery detector")

    return detector

if __name__ == "__main__":
    # Example usage
    async def main():
        # Create detector
        actions = [
            MotorAction.WALK_FORWARD,
            MotorAction.WALK_LEFT,
            MotorAction.WALK_RIGHT,
            MotorAction.JUMP
        ]

        detector = await create_motor_imagery_detector(actions)

        # Create trainer and generate simulated data
        trainer = MotorImageryTrainer()
        training_data = trainer.simulate_training_data(actions, trials_per_action=10)

        # Train detector
        print("Training motor imagery detector...")
        success = await detector.train_detector(training_data)

        if success:
            print("Training successful!")

            # Add callback
            def on_motor_command(command):
                print(f"Motor command: {command.action.value} "
                      f"(confidence: {command.confidence:.2f})")

            detector.add_command_callback(on_motor_command)

            # Start detection
            await detector.start_detection()

            # Simulate some signals
            from .neural_interface import create_neural_interface

            neural_interface = await create_neural_interface("simulator")
            await neural_interface.calibrate(duration=5.0)

            # Process signals for a while
            for _ in range(20):
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