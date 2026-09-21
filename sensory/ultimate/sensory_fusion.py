#!/usr/bin/env python3
"""
SENSORY FUSION
Creates unified perceptual experiences by combining multiple sensory inputs.
Fuses sight, sound, touch, emotion, and other senses into cohesive audio experiences.
"""

import numpy as np
import librosa
import soundfile as sf
from scipy import signal
from scipy.fft import fft, ifft, fft2, ifft2
import threading
import queue
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any, Union, Set
import math
import cmath
from collections import deque
import logging
from enum import Enum
import json
import cv2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SensoryFusion")

class FusionStrategy(Enum):
    """Strategies for fusing multiple sensory inputs"""
    ADDITIVE = "additive"           # Simple additive combination
    MULTIPLICATIVE = "multiplicative" # Multiplicative interaction
    WEIGHTED = "weighted"           # Weighted combination
    HIERARCHICAL = "hierarchical"   # Hierarchical processing
    NEURAL = "neural"              # Neural network fusion
    SEMANTIC = "semantic"           # Semantic understanding fusion
    EMERGENT = "emergent"          # Emergent properties
    SYNTHETIC = "synthetic"        # Synthetic reconstruction

class PerceptualMode(Enum):
    """Different perceptual modes for fusion"""
    REALISTIC = "realistic"         # Real-world perceptual fusion
    SYNTHETIC = "synthetic"         # Artificial/synthetic experience
    ABSTRACT = "abstract"           # Abstract perceptual fusion
    SYMBOLIC = "symbolic"           # Symbolic representation
    IMMERSIVE = "immersive"         # Fully immersive experience
    DREAMLIKE = "dreamlike"         # Dream-like fusion
    ENHANCED = "enhanced"           # Enhanced human perception
    CROSS_MODAL = "cross_modal"     # Cross-modal mapping

@dataclass
class SensoryInput:
    """Individual sensory input for fusion"""
    data: Any
    modality: str                  # Type of sensory input
    confidence: float              # Confidence in input (0-1)
    timestamp: float              # Timestamp of input
    spatial_position: Optional[Tuple[float, float, float]] = None
    emotional_weight: float = 0.5  # Emotional significance
    semantic_content: Optional[Dict[str, Any]] = None

@dataclass
class FusionState:
    """Current state of sensory fusion"""
    active_modalities: Set[str]
    fusion_weights: Dict[str, float]
    coherence_level: float         # How coherent the fusion is (0-1)
    attention_focus: Optional[str] # Which modality has attention
    emotional_tone: float         # Overall emotional tone (-1 to 1)
    arousal_level: float          # Overall arousal level (0-1)
    complexity_index: float       # Complexity of fused experience (0-1)

@dataclass
class PerceptualObject:
    """Fused perceptual object from multiple senses"""
    object_id: str
    modality_contributions: Dict[str, float]
    fused_features: Dict[str, Any]
    spatial_location: Tuple[float, float, float]
    temporal_dynamics: np.ndarray
    emotional_significance: float
    semantic_meaning: str

class SensoryFeatureExtractor:
    """Extracts and aligns features from different sensory modalities"""

    def __init__(self):
        self.feature_dimensions = {
            'visual': {'color': 3, 'texture': 5, 'shape': 10, 'motion': 6},
            'auditory': {'pitch': 1, 'timbre': 8, 'rhythm': 4, 'loudness': 1},
            'tactile': {'pressure': 1, 'texture': 5, 'temperature': 1, 'vibration': 3},
            'olfactory': {'intensity': 1, 'quality': 10, 'pleasantness': 1},
            'emotional': {'valence': 1, 'arousal': 1, 'dominance': 1, 'complexity': 1},
            'semantic': {'category': 1, 'attributes': 5, 'relationships': 3}
        }

    def extract_aligned_features(self, sensory_input: SensoryInput) -> np.ndarray:
        """Extract and align features to common dimensional space"""
        modality = sensory_input.modality
        data = sensory_input.data

        # Extract modality-specific features
        if modality == 'visual':
            features = self._extract_visual_features(data)
        elif modality == 'auditory':
            features = self._extract_auditory_features(data)
        elif modality == 'tactile':
            features = self._extract_tactile_features(data)
        elif modality == 'olfactory':
            features = self._extract_olfactory_features(data)
        elif modality == 'emotional':
            features = self._extract_emotional_features(data)
        elif modality == 'semantic':
            features = self._extract_semantic_features(data)
        else:
            features = self._extract_generic_features(data)

        # Normalize and align to common space
        aligned_features = self._align_feature_space(features, modality)

        return aligned_features

    def _extract_visual_features(self, data: np.ndarray) -> np.ndarray:
        """Extract visual features"""
        features = []

        if isinstance(data, np.ndarray) and len(data.shape) >= 2:
            # Color features (dominant colors)
            if len(data.shape) == 3:
                # Simple color averaging
                mean_color = np.mean(data, axis=(0, 1))
                features.extend(mean_color / 255.0)  # Normalize to 0-1

            # Texture features (variance, edges)
            gray = cv2.cvtColor(data, cv2.COLOR_RGB2GRAY) if len(data.shape) == 3 else data
            texture_variance = np.var(gray)
            features.append(texture_variance / 1000)  # Normalize

            # Edge density
            edges = cv2.Canny(gray.astype(np.uint8), 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            features.append(edge_density)

            # Shape features (contours)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            features.append(len(contours) / 100)  # Normalize

            # Motion features (if video)
            if len(data.shape) == 4:
                motion_intensity = self._calculate_motion_intensity(data)
                features.append(motion_intensity / 100)  # Normalize

        # Pad or truncate to standard length
        target_length = 32
        if len(features) < target_length:
            features.extend([0] * (target_length - len(features)))
        else:
            features = features[:target_length]

        return np.array(features)

    def _extract_auditory_features(self, data: np.ndarray) -> np.ndarray:
        """Extract auditory features"""
        features = []

        if isinstance(data, np.ndarray):
            # Spectral features
            fft_result = fft(data)
            magnitude_spectrum = np.abs(fft_result[:len(fft_result)//2])

            # Spectral centroid (brightness)
            freqs = np.fft.fftfreq(len(data), 1/44100)[:len(fft_result)//2]
            spectral_centroid = np.sum(freqs * magnitude_spectrum) / (np.sum(magnitude_spectrum) + 1e-10)
            features.append(spectral_centroid / 5000)  # Normalize

            # Spectral rolloff
            cumsum = np.cumsum(magnitude_spectrum)
            rolloff_idx = np.where(cumsum >= 0.85 * cumsum[-1])[0]
            spectral_rolloff = freqs[rolloff_idx[0]] if len(rolloff_idx) > 0 else 0
            features.append(spectral_rolloff / 10000)  # Normalize

            # Zero crossing rate
            zero_crossings = np.sum(np.diff(np.signbit(data)))
            features.append(zero_crossings / len(data))

            # RMS energy
            rms_energy = np.sqrt(np.mean(data**2))
            features.append(rms_energy / 0.1)  # Normalize

            # MFCC-like features (simplified)
            mel_filters = self._create_mel_filterbank(13)
            mel_spectrum = np.dot(mel_filters, magnitude_spectrum)
            log_mel = np.log(mel_spectrum + 1e-10)
            features.extend(log_mel[:10] / 10)  # Take first 10 and normalize

        # Pad or truncate to standard length
        target_length = 32
        if len(features) < target_length:
            features.extend([0] * (target_length - len(features)))
        else:
            features = features[:target_length]

        return np.array(features)

    def _extract_tactile_features(self, data: Union[np.ndarray, Dict]) -> np.ndarray:
        """Extract tactile features"""
        features = []

        if isinstance(data, np.ndarray):
            # Pressure features
            mean_pressure = np.mean(data)
            features.append(mean_pressure / 100)  # Normalize

            # Texture features
            pressure_variance = np.var(data)
            features.append(pressure_variance / 1000)  # Normalize

            # Gradient features (texture roughness)
            if len(data.shape) >= 2:
                gradient_magnitude = np.mean(np.abs(np.gradient(data)))
                features.append(gradient_magnitude / 10)  # Normalize
            else:
                features.append(0)

            # Temporal features (if time series)
            if len(data.shape) >= 2 and data.shape[1] > 1:
                # Simple frequency content
                temporal_fft = fft(data, axis=1)
                temporal_energy = np.mean(np.abs(temporal_fft), axis=1)
                features.extend(temporal_energy[:10] / 100)  # Take first 10 and normalize

        elif isinstance(data, dict):
            # Structured tactile data
            features.append(data.get('pressure', 0) / 100)
            features.append(data.get('temperature', 20) / 50)  # Normalize around room temp
            features.append(data.get('vibration', 0) / 100)
            features.append(data.get('texture_roughness', 0) / 10)

        # Pad or truncate to standard length
        target_length = 32
        if len(features) < target_length:
            features.extend([0] * (target_length - len(features)))
        else:
            features = features[:target_length]

        return np.array(features)

    def _extract_olfactory_features(self, data: Dict) -> np.ndarray:
        """Extract olfactory features"""
        features = []

        # Intensity
        features.append(data.get('intensity', 0.5))

        # Quality components (simulated)
        quality_components = data.get('components', [0] * 10)
        features.extend(quality_components[:20])  # Take up to 20 components

        # Pleasantness
        features.append(data.get('pleasantness', 0.5))

        # Familiarity
        features.append(data.get('familiarity', 0.5))

        # Decay rate
        features.append(data.get('decay_rate', 0.1))

        # Pad or truncate to standard length
        target_length = 32
        if len(features) < target_length:
            features.extend([0] * (target_length - len(features)))
        else:
            features = features[:target_length]

        return np.array(features)

    def _extract_emotional_features(self, data: Dict) -> np.ndarray:
        """Extract emotional features"""
        features = []

        # Basic emotion dimensions
        features.append(data.get('valence', 0))      # -1 to 1
        features.append(data.get('arousal', 0))      # 0 to 1
        features.append(data.get('dominance', 0))    # 0 to 1

        # Specific emotions
        emotions = ['joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust']
        for emotion in emotions:
            features.append(data.get(emotion, 0))

        # Complex emotional features
        features.append(data.get('complexity', 0.5))
        features.append(data.get('intensity', 0.5))
        features.append(data.get('stability', 0.7))

        # Pad or truncate to standard length
        target_length = 32
        if len(features) < target_length:
            features.extend([0] * (target_length - len(features)))
        else:
            features = features[:target_length]

        return np.array(features)

    def _extract_semantic_features(self, data: Union[str, Dict]) -> np.ndarray:
        """Extract semantic features"""
        features = []

        if isinstance(data, str):
            # Simple text features (word count, sentiment, etc.)
            features.append(len(data.split()) / 100)  # Word count normalized
            features.append(len(data) / 1000)         # Character count normalized

            # Simple sentiment analysis (very basic)
            positive_words = ['good', 'happy', 'love', 'beautiful', 'wonderful']
            negative_words = ['bad', 'sad', 'hate', 'ugly', 'terrible']

            text_lower = data.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)

            sentiment = (positive_count - negative_count) / (len(text.split()) + 1)
            features.append(sentiment)

            # Category features (simplified)
            categories = ['person', 'place', 'thing', 'action', 'concept']
            for category in categories:
                features.append(1.0 if category in text_lower else 0.0)

        elif isinstance(data, dict):
            # Structured semantic data
            features.append(data.get('category_confidence', 0.5))
            features.append(data.get('attribute_count', 0) / 10)
            features.append(data.get('relationship_count', 0) / 5)
            features.append(data.get('abstraction_level', 0.5))

        # Pad or truncate to standard length
        target_length = 32
        if len(features) < target_length:
            features.extend([0] * (target_length - len(features)))
        else:
            features = features[:target_length]

        return np.array(features)

    def _extract_generic_features(self, data: Any) -> np.ndarray:
        """Extract generic features for unknown modalities"""
        features = []

        # Basic statistical features if it's numeric
        if isinstance(data, np.ndarray):
            features.append(np.mean(data) if len(data) > 0 else 0)
            features.append(np.var(data) if len(data) > 0 else 0)
            features.append(np.max(data) if len(data) > 0 else 0)
            features.append(np.min(data) if len(data) > 0 else 0)

        # Data type and size features
        features.append(hash(type(data).__name__) % 100 / 100)
        features.append(len(data) if hasattr(data, '__len__') else 1)
        features.append(0.5)  # Default confidence

        # Pad to standard length
        target_length = 32
        if len(features) < target_length:
            features.extend([0] * (target_length - len(features)))
        else:
            features = features[:target_length]

        return np.array(features)

    def _align_feature_space(self, features: np.ndarray, modality: str) -> np.ndarray:
        """Align features to common dimensional space"""
        # Normalize features to common range
        features = np.clip(features, -1, 1)

        # Apply modality-specific scaling
        if modality == 'visual':
            features *= 1.0  # Visual features keep original scale
        elif modality == 'auditory':
            features *= 1.2  # Auditory features slightly emphasized
        elif modality == 'emotional':
            features *= 1.5  # Emotional features strongly emphasized
        else:
            features *= 0.8  # Other modalities slightly de-emphasized

        return features

    def _calculate_motion_intensity(self, video: np.ndarray) -> float:
        """Calculate motion intensity in video"""
        if len(video) < 2:
            return 0

        motion_sum = 0
        for i in range(len(video) - 1):
            diff = cv2.absdiff(video[i], video[i + 1])
            motion_sum += np.sum(diff)

        return motion_sum / (len(video) - 1)

    def _create_mel_filterbank(self, num_filters: int) -> np.ndarray:
        """Create simple mel filterbank"""
        # Simplified mel filterbank
        fft_size = 1024
        mel_filters = np.zeros((num_filters, fft_size // 2))

        for i in range(num_filters):
            # Create triangular filter
            start = int(i * fft_size / (2 * num_filters))
            center = int((i + 1) * fft_size / (2 * num_filters))
            end = int((i + 2) * fft_size / (2 * num_filters))

            for j in range(start, min(end, fft_size // 2)):
                if j < center:
                    mel_filters[i, j] = (j - start) / (center - start)
                else:
                    mel_filters[i, j] = (end - j) / (end - center)

        return mel_filters

class MultiModalFuser:
    """Fuses multiple sensory inputs into unified perceptual experience"""

    def __init__(self):
        self.feature_extractor = SensoryFeatureExtractor()
        self.fusion_weights = {
            'visual': 0.3,
            'auditory': 0.3,
            'tactile': 0.15,
            'olfactory': 0.1,
            'emotional': 0.1,
            'semantic': 0.05
        }
        self.fusion_history = deque(maxlen=50)

    def fuse_sensory_inputs(self, inputs: List[SensoryInput],
                          strategy: FusionStrategy = FusionStrategy.WEIGHTED) -> FusionState:
        """Fuse multiple sensory inputs using specified strategy"""
        if not inputs:
            return FusionState(set(), {}, 0.0, None, 0.0, 0.0, 0.0)

        # Extract features from all inputs
        extracted_features = []
        active_modalities = set()
        input_weights = {}

        for input_data in inputs:
            features = self.feature_extractor.extract_aligned_features(input_data)
            extracted_features.append((features, input_data.confidence))
            active_modalities.add(input_data.modality)
            input_weights[input_data.modality] = input_data.confidence

        # Apply fusion strategy
        if strategy == FusionStrategy.ADDITIVE:
            fused_features = self._additive_fusion(extracted_features)
        elif strategy == FusionStrategy.MULTIPLICATIVE:
            fused_features = self._multiplicative_fusion(extracted_features)
        elif strategy == FusionStrategy.WEIGHTED:
            fused_features = self._weighted_fusion(extracted_features, input_weights)
        elif strategy == FusionStrategy.HIERARCHICAL:
            fused_features = self._hierarchical_fusion(extracted_features, inputs)
        elif strategy == FusionStrategy.NEURAL:
            fused_features = self._neural_fusion(extracted_features)
        elif strategy == FusionStrategy.SEMANTIC:
            fused_features = self._semantic_fusion(extracted_features, inputs)
        elif strategy == FusionStrategy.EMERGENT:
            fused_features = self._emergent_fusion(extracted_features)
        else:  # SYNTHETIC
            fused_features = self._synthetic_fusion(extracted_features)

        # Calculate fusion state properties
        coherence_level = self._calculate_coherence(extracted_features, fused_features)
        attention_focus = self._determine_attention_focus(inputs)
        emotional_tone = self._calculate_emotional_tone(inputs)
        arousal_level = self._calculate_arousal_level(inputs)
        complexity_index = self._calculate_complexity(extracted_features)

        # Create fusion state
        fusion_state = FusionState(
            active_modalities=active_modalities,
            fusion_weights=input_weights,
            coherence_level=coherence_level,
            attention_focus=attention_focus,
            emotional_tone=emotional_tone,
            arousal_level=arousal_level,
            complexity_index=complexity_index
        )

        # Store in history
        self.fusion_history.append(fusion_state)

        return fusion_state

    def _additive_fusion(self, features: List[Tuple[np.ndarray, float]]) -> np.ndarray:
        """Simple additive fusion of features"""
        if not features:
            return np.zeros(32)

        # Sum all features with confidence weighting
        fused = np.zeros_like(features[0][0])
        total_confidence = 0

        for feature_array, confidence in features:
            fused += feature_array * confidence
            total_confidence += confidence

        # Normalize by total confidence
        if total_confidence > 0:
            fused /= total_confidence

        return fused

    def _multiplicative_fusion(self, features: List[Tuple[np.ndarray, float]]) -> np.ndarray:
        """Multiplicative fusion (feature interaction)"""
        if not features:
            return np.zeros(32)

        # Start with identity
        fused = np.ones_like(features[0][0])

        for feature_array, confidence in features:
            # Use geometric mean with confidence weighting
            weighted_features = 1 + (feature_array - 1) * confidence
            fused *= weighted_features

        # Normalize
        fused = np.tanh(fused)  # Keep in reasonable range

        return fused

    def _weighted_fusion(self, features: List[Tuple[np.ndarray, float]],
                        input_weights: Dict[str, float]) -> np.ndarray:
        """Weighted fusion based on modality importance"""
        if not features:
            return np.zeros(32)

        fused = np.zeros_like(features[0][0])
        total_weight = 0

        # Combine confidence and modality weights
        for i, (feature_array, confidence) in enumerate(features):
            modality = list(input_weights.keys())[i] if i < len(input_weights) else 'unknown'
            modality_weight = self.fusion_weights.get(modality, 0.1)
            combined_weight = confidence * modality_weight

            fused += feature_array * combined_weight
            total_weight += combined_weight

        # Normalize
        if total_weight > 0:
            fused /= total_weight

        return fused

    def _hierarchical_fusion(self, features: List[Tuple[np.ndarray, float]],
                           inputs: List[SensoryInput]) -> np.ndarray:
        """Hierarchical fusion (emotional > visual > auditory > other)"""
        if not features:
            return np.zeros(32)

        # Define hierarchy
        hierarchy = {
            'emotional': 4,
            'visual': 3,
            'auditory': 2,
            'tactile': 1,
            'olfactory': 1,
            'semantic': 1
        }

        # Sort inputs by hierarchy
        sorted_inputs = sorted(inputs, key=lambda x: hierarchy.get(x.modality, 0), reverse=True)
        sorted_features = [f for f in sorted(zip(features, inputs), key=lambda x: hierarchy.get(x[1].modality, 0), reverse=True)]

        fused = np.zeros_like(features[0][0])
        total_weight = 0

        for (feature_array, confidence), input_data in sorted_features:
            modality = input_data.modality
            hierarchy_weight = hierarchy.get(modality, 1)
            combined_weight = confidence * hierarchy_weight

            fused += feature_array * combined_weight
            total_weight += combined_weight

        # Normalize
        if total_weight > 0:
            fused /= total_weight

        return fused

    def _neural_fusion(self, features: List[Tuple[np.ndarray, float]]) -> np.ndarray:
        """Neural network-based fusion (simplified)"""
        if not features:
            return np.zeros(32)

        # Stack features
        feature_matrix = np.stack([f[0] for f in features])
        confidence_weights = np.array([f[1] for f in features])

        # Simple neural fusion using learned weights
        # In practice, this would use a trained neural network
        hidden_weights = np.random.randn(len(features), 16) * 0.1
        output_weights = np.random.randn(16, 32) * 0.1

        # Apply confidence weighting
        weighted_features = feature_matrix * confidence_weights[:, np.newaxis]

        # Hidden layer
        hidden = np.tanh(np.dot(weighted_features.T, hidden_weights))

        # Output layer
        fused = np.tanh(np.dot(hidden, output_weights))

        return fused

    def _semantic_fusion(self, features: List[Tuple[np.ndarray, float]],
                        inputs: List[SensoryInput]) -> np.ndarray:
        """Semantic-based fusion using semantic content"""
        if not features:
            return np.zeros(32)

        # Look for semantic relationships
        semantic_groups = self._group_by_semantics(inputs)

        fused = np.zeros_like(features[0][0])
        total_weight = 0

        for group_inputs in semantic_groups:
            # Fuse within semantic group
            group_indices = [inputs.index(inp) for inp in group_inputs]
            group_features = [features[i] for i in group_indices]

            if group_features:
                group_fused = self._additive_fusion(group_features)
                group_weight = sum(inp.confidence for inp in group_inputs)

                fused += group_fused * group_weight
                total_weight += group_weight

        # Normalize
        if total_weight > 0:
            fused /= total_weight

        return fused

    def _emergent_fusion(self, features: List[Tuple[np.ndarray, float]]) -> np.ndarray:
        """Emergent fusion creating new properties"""
        if not features:
            return np.zeros(32)

        # Base fusion
        base_fused = self._additive_fusion(features)

        # Create emergent properties through non-linear interactions
        emergent = np.zeros_like(base_fused)

        for i in range(len(base_fused)):
            # Non-linear combination of feature interactions
            for j, (feature_array, confidence) in enumerate(features):
                if i < len(feature_array):
                    # Cross-modality interactions
                    for k, (other_array, other_confidence) in enumerate(features):
                        if j != k and i < len(other_array):
                            interaction = feature_array[i] * other_array[i] * confidence * other_confidence
                            emergent[i] += interaction * 0.1  # Scale down interactions

        # Combine base and emergent
        fused = base_fused + 0.3 * np.tanh(emergent)

        return fused

    def _synthetic_fusion(self, features: List[Tuple[np.ndarray, float]]) -> np.ndarray:
        """Synthetic reconstruction from features"""
        if not features:
            return np.zeros(32)

        # Use principal component analysis for synthetic reconstruction
        feature_matrix = np.stack([f[0] for f in features])
        confidence_weights = np.array([f[1] for f in features])

        # Compute weighted covariance
        weighted_features = feature_matrix * confidence_weights[:, np.newaxis]
        cov_matrix = np.cov(weighted_features.T)

        # Eigendecomposition for principal components
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)

        # Reconstruct using top components
        top_components = min(3, len(eigenvalues))
        reconstruction = np.zeros(feature_matrix.shape[1])

        for i in range(top_components):
            component_weight = eigenvalues[-(i+1)]  # Use largest eigenvalues
            component = eigenvectors[:, -(i+1)]
            reconstruction += component_weight * component

        # Normalize
        fused = np.tanh(reconstruction)

        return fused

    def _group_by_semantics(self, inputs: List[SensoryInput]) -> List[List[SensoryInput]]:
        """Group inputs by semantic content"""
        groups = []
        processed = set()

        for i, input1 in enumerate(inputs):
            if i in processed:
                continue

            group = [input1]
            processed.add(i)

            for j, input2 in enumerate(inputs):
                if j <= i or j in processed:
                    continue

                # Check semantic similarity
                if self._semantic_similarity(input1, input2) > 0.5:
                    group.append(input2)
                    processed.add(j)

            groups.append(group)

        return groups

    def _semantic_similarity(self, input1: SensoryInput, input2: SensoryInput) -> float:
        """Calculate semantic similarity between two inputs"""
        # Simple semantic similarity based on modality and content
        if input1.modality == input2.modality:
            modality_similarity = 1.0
        elif (input1.modality in ['visual', 'tactile'] and input2.modality in ['visual', 'tactile']):
            modality_similarity = 0.7  # Spatial modalities
        elif (input1.modality in ['auditory', 'olfactory'] and input2.modality in ['auditory', 'olfactory']):
            modality_similarity = 0.6  # Chemical/modal modalities
        else:
            modality_similarity = 0.3  # Cross-modal

        # Content similarity (simplified)
        content_similarity = 0.5  # Default

        # Temporal proximity
        temporal_similarity = 1.0 - min(abs(input1.timestamp - input2.timestamp) / 10.0, 1.0)

        # Overall similarity
        overall_similarity = (modality_similarity + content_similarity + temporal_similarity) / 3

        return overall_similarity

    def _calculate_coherence(self, features: List[Tuple[np.ndarray, float]],
                           fused_features: np.ndarray) -> float:
        """Calculate coherence of fusion"""
        if not features:
            return 0.0

        # Calculate average correlation between original features and fused result
        correlations = []
        for feature_array, confidence in features:
            correlation = np.corrcoef(feature_array, fused_features)[0, 1]
            if not np.isnan(correlation):
                correlations.append(abs(correlation) * confidence)

        return np.mean(correlations) if correlations else 0.0

    def _determine_attention_focus(self, inputs: List[SensoryInput]) -> Optional[str]:
        """Determine which modality has attention focus"""
        if not inputs:
            return None

        # Find input with highest confidence and emotional weight
        max_score = -1
        focus_modality = None

        for input_data in inputs:
            score = input_data.confidence * input_data.emotional_weight
            if score > max_score:
                max_score = score
                focus_modality = input_data.modality

        return focus_modality

    def _calculate_emotional_tone(self, inputs: List[SensoryInput]) -> float:
        """Calculate overall emotional tone"""
        emotional_sum = 0
        total_weight = 0

        for input_data in inputs:
            if input_data.modality == 'emotional' and isinstance(input_data.data, dict):
                valence = input_data.data.get('valence', 0)
                emotional_sum += valence * input_data.confidence
                total_weight += input_data.confidence

        return emotional_sum / total_weight if total_weight > 0 else 0.0

    def _calculate_arousal_level(self, inputs: List[SensoryInput]) -> float:
        """Calculate overall arousal level"""
        arousal_sum = 0
        total_weight = 0

        for input_data in inputs:
            if input_data.modality == 'emotional' and isinstance(input_data.data, dict):
                arousal = input_data.data.get('arousal', 0)
                arousal_sum += arousal * input_data.confidence
                total_weight += input_data.confidence

        return arousal_sum / total_weight if total_weight > 0 else 0.0

    def _calculate_complexity(self, features: List[Tuple[np.ndarray, float]]) -> float:
        """Calculate complexity of fused experience"""
        if not features:
            return 0.0

        # Calculate feature variance across modalities
        feature_matrix = np.stack([f[0] for f in features])
        feature_variance = np.var(feature_matrix, axis=0)

        # Average variance across all features
        avg_variance = np.mean(feature_variance)

        # Normalize to 0-1 range
        complexity = np.tanh(avg_variance)

        return complexity

class PerceptualAudioSynthesizer:
    """Synthesizes audio from fused perceptual experience"""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.fuser = MultiModalFuser()

    def synthesize_fused_experience(self, inputs: List[SensoryInput],
                                  fusion_strategy: FusionStrategy = FusionStrategy.WEIGHTED,
                                  perceptual_mode: PerceptualMode = PerceptualMode.REALISTIC,
                                  duration: float = 8.0) -> np.ndarray:
        """Synthesize audio from fused sensory experience"""
        # Fuse sensory inputs
        fusion_state = self.fuser.fuse_sensory_inputs(inputs, fusion_strategy)

        # Synthesize audio based on fusion state and perceptual mode
        if perceptual_mode == PerceptualMode.REALISTIC:
            audio = self._synthesize_realistic(fusion_state, inputs, duration)
        elif perceptual_mode == PerceptualMode.SYNTHETIC:
            audio = self._synthesize_synthetic(fusion_state, duration)
        elif perceptual_mode == PerceptualMode.ABSTRACT:
            audio = self._synthesize_abstract(fusion_state, duration)
        elif perceptual_mode == PerceptualMode.SYMBOLIC:
            audio = self._synthesize_symbolic(fusion_state, duration)
        elif perceptual_mode == PerceptualMode.IMMERSIVE:
            audio = self._synthesize_immersive(fusion_state, inputs, duration)
        elif perceptual_mode == PerceptualMode.DREAMLIKE:
            audio = self._synthesize_dreamlike(fusion_state, duration)
        elif perceptual_mode == PerceptualMode.ENHANCED:
            audio = self._synthesize_enhanced(fusion_state, inputs, duration)
        else:  # CROSS_MODAL
            audio = self._synthesize_cross_modal(fusion_state, inputs, duration)

        return audio

    def _synthesize_realistic(self, fusion_state: FusionState,
                            inputs: List[SensoryInput], duration: float) -> np.ndarray:
        """Synthesize realistic perceptual audio"""
        num_samples = int(duration * self.sample_rate)
        audio = np.zeros(num_samples)
        t = np.linspace(0, duration, num_samples)

        # Base audio from dominant modality
        if fusion_state.attention_focus:
            dominant_input = next((inp for inp in inputs if inp.modality == fusion_state.attention_focus), None)
            if dominant_input:
                audio = self._synthesize_modality_audio(dominant_input, t)

        # Add contributions from other modalities
        for input_data in inputs:
            if input_data.modality != fusion_state.attention_focus:
                contribution = self._synthesize_modality_audio(input_data, t)
                weight = fusion_state.fusion_weights.get(input_data.modality, 0.1)
                audio += contribution * weight * 0.5

        # Apply emotional modulation
        emotional_modulation = 1 + 0.3 * fusion_state.emotional_tone
        audio *= emotional_modulation

        # Apply arousal-based filtering
        if fusion_state.arousal_level > 0.5:
            # High arousal - more high frequencies
            b, a = signal.butter(4, 2000 / (self.sample_rate / 2), 'high')
            audio = signal.filtfilt(b, a, audio) * 0.3 + audio * 0.7
        else:
            # Low arousal - more low frequencies
            b, a = signal.butter(4, 500 / (self.sample_rate / 2), 'low')
            audio = signal.filtfilt(b, a, audio) * 0.3 + audio * 0.7

        # Normalize
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))

        return audio

    def _synthesize_synthetic(self, fusion_state: FusionState, duration: float) -> np.ndarray:
        """Synthesize artificial/synthetic experience"""
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples)
        audio = np.zeros(num_samples)

        # Create synthetic soundscape based on fusion properties
        complexity = fusion_state.complexity_index
        coherence = fusion_state.coherence_level

        # Base oscillators with complexity-based harmonics
        num_oscillators = int(2 + complexity * 8)
        for i in range(num_oscillators):
            frequency = 110 * (i + 1)  # Harmonic series
            amplitude = 1.0 / (i + 1)  # Decreasing amplitude
            phase = np.random.uniform(0, 2 * np.pi)

            oscillator = amplitude * np.sin(2 * np.pi * frequency * t + phase)
            audio += oscillator

        # Add coherence-based modulation
        coherence_modulation = 1 + coherence * 0.5 * np.sin(2 * np.pi * 2 * t)
        audio *= coherence_modulation

        # Add synthetic texture based on active modalities
        for modality in fusion_state.active_modalities:
            if modality == 'visual':
                # Add visual-like sweeping sounds
                sweep_freq = np.linspace(200, 2000, num_samples)
                sweep = np.sin(2 * np.pi * sweep_freq * t)
                audio += 0.1 * sweep
            elif modality == 'tactile':
                # Add tactile-like rhythmic patterns
                rhythm = np.sin(2 * np.pi * 8 * t) * (np.sin(2 * np.pi * 0.5 * t) > 0)
                audio += 0.15 * rhythm

        # Normalize
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))

        return audio

    def _synthesize_abstract(self, fusion_state: FusionState, duration: float) -> np.ndarray:
        """Synthesize abstract perceptual audio"""
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples)
        audio = np.zeros(num_samples)

        # Create abstract sound based on fusion state
        complexity = fusion_state.complexity_index

        # Use chaotic oscillators for abstract feeling
        for i in range(3):
            # Simple chaotic system (logistic map inspired)
            x = 0.5 + i * 0.1
            r = 3.5 + complexity * 0.5
            chaotic_signal = []

            for j in range(num_samples):
                x = r * x * (1 - x)
                if len(chaotic_signal) > 100:  # Use moving window
                    freq = 220 + 100 * np.mean(chaotic_signal[-100:])
                else:
                    freq = 220
                sample = np.sin(2 * np.pi * freq * t[j])
                chaotic_signal.append(sample)

            audio += 0.3 * np.array(chaotic_signal)

        # Add emotional coloring
        emotional_tone = fusion_state.emotional_tone
        if emotional_tone > 0:
            # Positive - higher frequencies
            audio = np.sin(audio * (1 + emotional_tone))
        else:
            # Negative - lower frequencies and distortion
            audio = np.tanh(audio * (1 - emotional_tone))

        # Normalize
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))

        return audio

    def _synthesize_symbolic(self, fusion_state: FusionState, duration: float) -> np.ndarray:
        """Synthesize symbolic representation audio"""
        num_samples = int(duration * self.sample_rate)
        audio = np.zeros(num_samples)
        t = np.linspace(0, duration, num_samples)

        # Create symbolic motifs based on active modalities
        motifs = []

        for modality in fusion_state.active_modalities:
            if modality == 'visual':
                # Visual motif - ascending arpeggio
                motif = self._create_arpeggio([220, 277, 330, 440], duration/4)
                motifs.append(motif)
            elif modality == 'auditory':
                # Auditory motif - rhythmic pattern
                motif = self._create_rhythmic_pattern(440, 0.125, duration/4)
                motifs.append(motif)
            elif modality == 'emotional':
                # Emotional motif - emotional contour
                emotion_freq = 330 + fusion_state.emotional_tone * 110
                motif = self._create_emotional_contour(emotion_freq, duration/4, fusion_state.emotional_tone)
                motifs.append(motif)
            else:
                # Generic motif
                motif = self._create_generic_motif(440, duration/4)
                motifs.append(motif)

        # Arrange motifs
        motif_duration = duration / len(motifs)
        for i, motif in enumerate(motifs):
            start_idx = int(i * motif_duration * self.sample_rate)
            end_idx = min(int((i + 1) * motif_duration * self.sample_rate), num_samples)

            if len(motif) > 0:
                # Resize motif to fit duration
                resized_motif = np.interp(
                    np.linspace(0, 1, end_idx - start_idx),
                    np.linspace(0, 1, len(motif)),
                    motif
                )
                audio[start_idx:end_idx] = resized_motif

        # Normalize
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))

        return audio

    def _synthesize_immersive(self, fusion_state: FusionState,
                            inputs: List[SensoryInput], duration: float) -> np.ndarray:
        """Synthesize fully immersive experience"""
        num_samples = int(duration * self.sample_rate)
        audio = np.zeros(num_samples)
        t = np.linspace(0, duration, num_samples)

        # Create immersive soundscape with multiple layers
        layers = []

        # Layer 1: Ambient foundation
        ambient_freq = 55  # Low foundation
        ambient = 0.3 * np.sin(2 * np.pi * ambient_freq * t)
        ambient *= (1 + 0.2 * np.sin(2 * np.pi * 0.1 * t))  # Slow modulation
        layers.append(ambient)

        # Layer 2: Dominant modality
        if fusion_state.attention_focus:
            dominant_input = next((inp for inp in inputs if inp.modality == fusion_state.attention_focus), None)
            if dominant_input:
                layer = self._synthesize_modality_audio(dominant_input, t)
                layers.append(layer * 0.5)

        # Layer 3: Emotional atmosphere
        emotional_freq = 110 + fusion_state.emotional_tone * 55
        emotional_layer = 0.2 * np.sin(2 * np.pi * emotional_freq * t)
        emotional_layer *= (1 + 0.3 * fusion_state.arousal_level * np.sin(2 * np.pi * 0.5 * t))
        layers.append(emotional_layer)

        # Layer 4: Complexity textures
        if fusion_state.complexity_index > 0.5:
            # Add textural layers
            for i in range(int(fusion_state.complexity_index * 3)):
                texture_freq = 440 * (1 + i * 0.5)
                texture = 0.1 * np.sin(2 * np.pi * texture_freq * t + i * np.pi/4)
                texture *= np.random.random(len(t)) * 0.5 + 0.5  # Random amplitude
                layers.append(texture)

        # Mix all layers
        for layer in layers:
            audio += layer

        # Apply spatial processing (simulated)
        spatial_modulation = 1 + 0.1 * np.sin(2 * np.pi * 0.2 * t)
        audio *= spatial_modulation

        # Normalize
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))

        return audio

    def _synthesize_dreamlike(self, fusion_state: FusionState, duration: float) -> np.ndarray:
        """Synthesize dream-like experience"""
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples)
        audio = np.zeros(num_samples)

        # Create dreamlike quality with shifting realities
        dream_states = 4
        state_duration = duration / dream_states

        for state in range(dream_states):
            start_idx = int(state * state_duration * self.sample_rate)
            end_idx = min(int((state + 1) * state_duration * self.sample_rate), num_samples)
            state_t = t[start_idx:end_idx]

            # Each dream state has different characteristics
            base_freq = 110 * (state + 1)
            dream_audio = 0.4 * np.sin(2 * np.pi * base_freq * state_t)

            # Add ethereal quality
            ethereal = 0.2 * np.sin(2 * np.pi * base_freq * 2 * state_t)
            ethereal *= np.sin(2 * np.pi * 0.3 * state_t)  # Slow pulsing
            dream_audio += ethereal

            # Add surreal elements
            if state % 2 == 0:
                # Add unexpected harmonics
                for harmonic in [3, 5, 7]:
                    dream_audio += 0.1 * np.sin(2 * np.pi * base_freq * harmonic * state_t)

            # Apply dream state transition
            if state > 0:
                transition_length = int(0.5 * self.sample_rate)  # 0.5 second transition
                transition_start = max(0, start_idx - transition_length)
                transition_end = end_idx
                transition_t = np.linspace(0, 1, transition_end - transition_start)

                # Cross-fade
                if transition_start > 0:
                    dream_audio[:transition_start] *= (1 - transition_t[:len(dream_audio[:transition_start])])

            audio[start_idx:end_idx] = dream_audio

        # Apply dream processing
        # Time stretching and compression effects
        dream_audio_processed = np.zeros_like(audio)
        for i in range(0, len(audio), 100):
            chunk = audio[i:i+100]
            # Random time stretch/compression
            stretch_factor = np.random.uniform(0.8, 1.2)
            stretched_chunk = np.interp(
                np.linspace(0, 1, int(len(chunk) * stretch_factor)),
                np.linspace(0, 1, len(chunk)),
                chunk
            )
            end_pos = min(i + len(stretched_chunk), len(dream_audio_processed))
            dream_audio_processed[i:end_pos] = stretched_chunk[:end_pos-i]

        audio = dream_audio_processed

        # Normalize
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))

        return audio

    def _synthesize_enhanced(self, fusion_state: FusionState,
                           inputs: List[SensoryInput], duration: float) -> np.ndarray:
        """Synthesize enhanced human perception"""
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples)
        audio = np.zeros(num_samples)

        # Start with realistic base
        base_audio = self._synthesize_realistic(fusion_state, inputs, duration)

        # Add enhanced layers
        # Enhanced frequency range
        enhanced_audio = base_audio.copy()

        # Add ultra-high frequencies (beyond normal hearing)
        ultra_high = 0.1 * np.sin(2 * np.pi * 20000 * t)  # 20 kHz
        enhanced_audio += ultra_high

        # Add sub-bass frequencies
        sub_bass = 0.2 * np.sin(2 * np.pi * 20 * t)  # 20 Hz
        enhanced_audio += sub_bass

        # Add micro-details (rapid modulations)
        micro_details = 0.05 * np.sin(2 * np.pi * 5000 * t)
        micro_details *= (1 + 0.5 * np.sin(2 * np.pi * 100 * t))
        enhanced_audio += micro_details

        # Enhance spatial resolution
        spatial_enhancement = 1 + 0.1 * np.sin(2 * np.pi * 1 * t)
        spatial_enhancement *= 1 + 0.05 * np.sin(2 * np.pi * 0.1 * t)
        enhanced_audio *= spatial_enhancement

        # Apply enhancement filtering
        # Boost presence frequencies (2-4 kHz)
        b, a = signal.butter(2, [2000, 4000], 'band', fs=self.sample_rate)
        presence = signal.filtfilt(b, a, enhanced_audio)
        enhanced_audio += 0.3 * presence

        # Normalize
        if np.max(np.abs(enhanced_audio)) > 0:
            enhanced_audio = enhanced_audio / np.max(np.abs(enhanced_audio))

        return enhanced_audio

    def _synthesize_cross_modal(self, fusion_state: FusionState,
                              inputs: List[SensoryInput], duration: float) -> np.ndarray:
        """Synthesize cross-modal mapping experience"""
        num_samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, num_samples)
        audio = np.zeros(num_samples)

        # Create cross-modal mappings
        for input_data in inputs:
            cross_modal_audio = self._map_to_cross_modal_audio(input_data, t)
            weight = fusion_state.fusion_weights.get(input_data.modality, 0.1)
            audio += cross_modal_audio * weight

        # Add cross-modal interaction effects
        if len(inputs) >= 2:
            # Create interaction between modalities
            interaction_audio = self._create_modality_interactions(inputs, t)
            audio += 0.3 * interaction_audio

        # Normalize
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio))

        return audio

    def _synthesize_modality_audio(self, input_data: SensoryInput, t: np.ndarray) -> np.ndarray:
        """Synthesize audio from single modality input"""
        modality = input_data.modality

        if modality == 'visual':
            return self._visual_to_audio(input_data.data, t)
        elif modality == 'auditory':
            return self._auditory_to_audio(input_data.data, t)
        elif modality == 'tactile':
            return self._tactile_to_audio(input_data.data, t)
        elif modality == 'emotional':
            return self._emotional_to_audio(input_data.data, t)
        else:
            return self._generic_to_audio(input_data.data, t)

    def _visual_to_audio(self, visual_data: Any, t: np.ndarray) -> np.ndarray:
        """Convert visual data to audio"""
        audio = np.zeros_like(t)

        if isinstance(visual_data, np.ndarray):
            # Use visual features to generate audio
            if len(visual_data.shape) >= 2:
                # Color to frequency
                if len(visual_data.shape) == 3:
                    mean_color = np.mean(visual_data, axis=(0, 1))
                    frequency = 220 + np.mean(mean_color)  # Map color to frequency
                else:
                    frequency = 440

                # Edge density to texture
                gray = cv2.cvtColor(visual_data, cv2.COLOR_RGB2GRAY) if len(visual_data.shape) == 3 else visual_data
                edges = cv2.Canny(gray.astype(np.uint8), 50, 150)
                edge_density = np.sum(edges > 0) / edges.size

                # Generate audio
                waveform = np.sin(2 * np.pi * frequency * t)
                texture = edge_density * np.random.normal(0, 0.1, len(t))
                audio = waveform + texture

        return audio

    def _auditory_to_audio(self, auditory_data: Any, t: np.ndarray) -> np.ndarray:
        """Process auditory data"""
        if isinstance(auditory_data, np.ndarray):
            return auditory_data[:len(t)] if len(auditory_data) >= len(t) else np.pad(auditory_data, (0, len(t) - len(auditory_data)))
        else:
            return np.zeros_like(t)

    def _tactile_to_audio(self, tactile_data: Any, t: np.ndarray) -> np.ndarray:
        """Convert tactile data to audio"""
        audio = np.zeros_like(t)

        if isinstance(tactile_data, np.ndarray):
            # Pressure to amplitude
            mean_pressure = np.mean(tactile_data)
            amplitude = min(mean_pressure / 100, 1.0)

            # Texture to frequency
            texture_freq = 100 + np.var(tactile_data)

            # Generate audio
            audio = amplitude * np.sin(2 * np.pi * texture_freq * t)

        return audio

    def _emotional_to_audio(self, emotional_data: Any, t: np.ndarray) -> np.ndarray:
        """Convert emotional data to audio"""
        audio = np.zeros_like(t)

        if isinstance(emotional_data, dict):
            valence = emotional_data.get('valence', 0)
            arousal = emotional_data.get('arousal', 0)

            # Map emotions to audio parameters
            base_freq = 220 + valence * 110  # Valence affects pitch
            amplitude = 0.3 + arousal * 0.5   # Arousal affects amplitude

            # Generate audio
            waveform = amplitude * np.sin(2 * np.pi * base_freq * t)

            # Add emotional tremolo
            tremolo_rate = 3 + abs(valence) * 5
            tremolo = 1 + 0.3 * np.sin(2 * np.pi * tremolo_rate * t)
            audio = waveform * tremolo

        return audio

    def _generic_to_audio(self, data: Any, t: np.ndarray) -> np.ndarray:
        """Convert generic data to audio"""
        # Default sine wave
        return 0.5 * np.sin(2 * np.pi * 440 * t)

    def _create_arpeggio(self, frequencies: List[float], duration: float) -> np.ndarray:
        """Create arpeggio from frequencies"""
        num_samples = int(duration * self.sample_rate)
        arpeggio = np.zeros(num_samples)
        t = np.linspace(0, duration, num_samples)

        notes_per_frequency = num_samples // len(frequencies)

        for i, freq in enumerate(frequencies):
            start_idx = i * notes_per_frequency
            end_idx = min((i + 1) * notes_per_frequency, num_samples)
            note_t = t[start_idx:end_idx]
            arpeggio[start_idx:end_idx] = np.sin(2 * np.pi * freq * note_t)

        return arpeggio

    def _create_rhythmic_pattern(self, frequency: float, rhythm_duration: float, total_duration: float) -> np.ndarray:
        """Create rhythmic pattern"""
        num_samples = int(total_duration * self.sample_rate)
        pattern = np.zeros(num_samples)
        t = np.linspace(0, total_duration, num_samples)

        rhythm_samples = int(rhythm_duration * self.sample_rate)
        num_beats = num_samples // rhythm_samples

        for i in range(num_beats):
            start_idx = i * rhythm_samples
            end_idx = min((i + 1) * rhythm_samples, num_samples)
            beat_t = t[start_idx:end_idx]
            pattern[start_idx:end_idx] = np.sin(2 * np.pi * frequency * beat_t)

        return pattern

    def _create_emotional_contour(self, frequency: float, duration: float, emotion: float) -> np.ndarray:
        """Create emotional contour"""
        num_samples = int(duration * self.sample_rate)
        contour = np.zeros(num_samples)
        t = np.linspace(0, duration, num_samples)

        # Create contour based on emotion
        if emotion > 0:
            # Positive emotion - rising contour
            freq_contour = frequency * (1 + 0.5 * emotion * t / duration)
        else:
            # Negative emotion - falling contour
            freq_contour = frequency * (1 + 0.5 * emotion * t / duration)

        # Generate contour
        phase = np.cumsum(2 * np.pi * freq_contour / self.sample_rate)
        contour = np.sin(phase)

        return contour

    def _create_generic_motif(self, frequency: float, duration: float) -> np.ndarray:
        """Create generic melodic motif"""
        num_samples = int(duration * self.sample_rate)
        motif = np.zeros(num_samples)
        t = np.linspace(0, duration, num_samples)

        # Simple melodic contour
        contour_freq = frequency * (1 + 0.3 * np.sin(2 * np.pi * 2 * t))
        motif = np.sin(2 * np.pi * contour_freq * t)

        return motif

    def _create_modality_interactions(self, inputs: List[SensoryInput], t: np.ndarray) -> np.ndarray:
        """Create interaction effects between modalities"""
        interaction_audio = np.zeros_like(t)

        # Find interacting modalities
        for i, input1 in enumerate(inputs):
            for j, input2 in enumerate(inputs[i+1:], i+1):
                # Create interaction based on modality combination
                interaction = self._create_single_interaction(input1, input2, t)
                interaction_audio += interaction

        return interaction_audio

    def _create_single_interaction(self, input1: SensoryInput, input2: SensoryInput, t: np.ndarray) -> np.ndarray:
        """Create interaction between two modalities"""
        # Simple interaction: sum of both modalities with modulation
        audio1 = self._synthesize_modality_audio(input1, t)
        audio2 = self._synthesize_modality_audio(input2, t)

        # Modulation based on confidence
        modulation = 1 + 0.2 * (input1.confidence - input2.confidence) * np.sin(2 * np.pi * 5 * t)

        interaction = (audio1 + audio2) * modulation * 0.5

        return interaction

class SensoryFusionSystem:
    """Main sensory fusion system"""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.synthesizer = PerceptualAudioSynthesizer(sample_rate)

        # Real-time processing
        self.input_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.processing_thread = None

        # System state
        self.current_fusion_state = None
        self.fusion_history = deque(maxlen=100)

        # Performance monitoring
        self.performance_metrics = {
            'sensory_inputs_processed': 0,
            'fusions_performed': 0,
            'active_modalities': set(),
            'average_processing_time': deque(maxlen=100)
        }

    def add_sensory_input(self, data: Any, modality: str, confidence: float = 1.0,
                         spatial_position: Optional[Tuple[float, float, float]] = None,
                         emotional_weight: float = 0.5,
                         semantic_content: Optional[Dict[str, Any]] = None):
        """Add sensory input for fusion"""
        sensory_input = SensoryInput(
            data=data,
            modality=modality,
            confidence=confidence,
            timestamp=time.time(),
            spatial_position=spatial_position,
            emotional_weight=emotional_weight,
            semantic_content=semantic_content
        )

        self.input_queue.put(sensory_input)
        self.performance_metrics['sensory_inputs_processed'] += 1
        self.performance_metrics['active_modalities'].add(modality)

        logger.info(f"Added {modality} sensory input with confidence {confidence:.2f}")

    def fuse_and_synthesize(self, fusion_strategy: FusionStrategy = FusionStrategy.WEIGHTED,
                          perceptual_mode: PerceptualMode = PerceptualMode.REALISTIC,
                          duration: float = 8.0) -> np.ndarray:
        """Fuse current sensory inputs and synthesize audio"""
        start_time = time.time()

        # Collect available inputs
        inputs = []
        while True:
            try:
                input_data = self.input_queue.get_nowait()
                inputs.append(input_data)
            except queue.Empty:
                break

        if not inputs:
            logger.warning("No sensory inputs available for fusion")
            return np.zeros(int(duration * self.sample_rate))

        # Synthesize fused experience
        audio = self.synthesizer.synthesize_fused_experience(
            inputs, fusion_strategy, perceptual_mode, duration
        )

        # Update fusion state
        self.current_fusion_state = self.synthesizer.fuser.fuse_sensory_inputs(inputs, fusion_strategy)
        self.fusion_history.append({
            'timestamp': time.time(),
            'fusion_state': self.current_fusion_state,
            'num_inputs': len(inputs),
            'strategy': fusion_strategy.value,
            'mode': perceptual_mode.value
        })

        # Update metrics
        processing_time = time.time() - start_time
        self.performance_metrics['fusions_performed'] += 1
        self.performance_metrics['average_processing_time'].append(processing_time)

        logger.info(f"Fused {len(inputs)} sensory inputs in {processing_time:.3f}s")

        return audio

    def start_real_time_fusion(self, chunk_duration: float = 3.0):
        """Start real-time sensory fusion"""
        self.is_running = True
        self.processing_thread = threading.Thread(
            target=self._real_time_fusion_loop,
            args=(chunk_duration,),
            daemon=True
        )
        self.processing_thread.start()

        logger.info("Started real-time sensory fusion")

    def _real_time_fusion_loop(self, chunk_duration: float):
        """Real-time fusion loop"""
        while self.is_running:
            start_time = time.time()

            # Synthesize audio chunk
            audio_chunk = self.fuse_and_synthesize(
                fusion_strategy=FusionStrategy.IMMERSIVE,
                perceptual_mode=PerceptualMode.ENHANCED,
                duration=chunk_duration
            )
            self.audio_queue.put(audio_chunk)

            # Maintain real-time performance
            elapsed = time.time() - start_time
            if elapsed < chunk_duration:
                time.sleep(chunk_duration - elapsed)

    def stop_real_time_fusion(self):
        """Stop real-time fusion"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)

        logger.info("Stopped real-time sensory fusion")

    def get_audio_chunk(self) -> Optional[np.ndarray]:
        """Get next audio chunk from queue"""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None

    def create_demo_fusion(self) -> np.ndarray:
        """Create demonstration of multi-sensory fusion"""
        print("Creating multi-sensory fusion demonstration...")

        # Add various sensory inputs
        # Visual input
        visual_data = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
        self.add_sensory_input(visual_data, 'visual', confidence=0.9, emotional_weight=0.7)

        # Emotional input
        emotional_data = {'valence': 0.8, 'arousal': 0.6, 'joy': 0.9}
        self.add_sensory_input(emotional_data, 'emotional', confidence=0.95, emotional_weight=1.0)

        # Tactile input
        tactile_data = np.random.normal(50, 10, (100,))  # Pressure sensor data
        self.add_sensory_input(tactile_data, 'tactile', confidence=0.8, emotional_weight=0.5)

        # Auditory input
        auditory_data = np.sin(2 * np.pi * 440 * np.linspace(0, 2, 88200))  # 2 seconds of 440 Hz
        self.add_sensory_input(auditory_data, 'auditory', confidence=0.85, emotional_weight=0.6)

        # Fuse and synthesize
        audio = self.fuse_and_synthesize(
            fusion_strategy=FusionStrategy.IMMERSIVE,
            perceptual_mode=PerceptualMode.ENHANCED,
            duration=10.0
        )

        return audio

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        status = {
            'current_fusion_state': None,
            'queue_sizes': {
                'input_queue': self.input_queue.qsize(),
                'audio_queue': self.audio_queue.qsize()
            },
            'is_running': self.is_running,
            'performance_metrics': dict(self.performance_metrics)
        }

        if self.current_fusion_state:
            status['current_fusion_state'] = {
                'active_modalities': list(self.current_fusion_state.active_modalities),
                'coherence_level': self.current_fusion_state.coherence_level,
                'attention_focus': self.current_fusion_state.attention_focus,
                'emotional_tone': self.current_fusion_state.emotional_tone,
                'arousal_level': self.current_fusion_state.arousal_level,
                'complexity_index': self.current_fusion_state.complexity_index
            }

        if self.performance_metrics['average_processing_time']:
            status['performance_metrics']['average_processing_time'] = np.mean(
                self.performance_metrics['average_processing_time']
            )

        return status

    def save_fused_audio(self, audio: np.ndarray, filename: str, metadata: Optional[Dict] = None):
        """Save fused audio with metadata"""
        sf.write(filename, audio, self.sample_rate)

        # Save metadata
        if metadata or self.current_fusion_state:
            metadata_file = filename.replace('.wav', '_fusion_metadata.json')
            fusion_data = {
                'fusion_state': self.current_fusion_state.__dict__ if self.current_fusion_state else None,
                'system_performance': self.get_system_status(),
                'custom_metadata': metadata or {}
            }

            with open(metadata_file, 'w') as f:
                json.dump(fusion_data, f, indent=2, default=str)

            logger.info(f"Saved fused audio with metadata to {filename}")

def main():
    """Demonstration of Sensory Fusion System"""
    print("SENSORY FUSION - Unified Perceptual Experience Creation")
    print("=" * 70)

    # Initialize system
    system = SensoryFusionSystem(sample_rate=44100)

    # Create demo fusion
    print("\nCreating multi-sensory fusion demonstration...")
    demo_audio = system.create_demo_fusion()

    # Save demo audio
    demo_file = "/home/activeloguser/DMLogn8n/sensory/ultimate/sensory_fusion_demo.wav"
    system.save_fused_audio(demo_audio, demo_file)
    print(f"Saved sensory fusion demo: {demo_file}")

    # Test different fusion strategies and modes
    strategies = [FusionStrategy.WEIGHTED, FusionStrategy.EMERGENT, FusionStrategy.IMMERSIVE]
    modes = [PerceptualMode.REALISTIC, PerceptualMode.DREAMLIKE, PerceptualMode.ENHANCED]

    print(f"\nTesting different fusion configurations...")

    for strategy in strategies:
        for mode in modes:
            print(f"  Testing {strategy.value} + {mode.value}...")

            # Add some sensory inputs
            visual_data = np.random.randint(0, 256, (30, 30, 3), dtype=np.uint8)
            system.add_sensory_input(visual_data, 'visual', confidence=0.8)

            emotional_data = {'valence': np.random.uniform(-0.5, 0.5), 'arousal': np.random.uniform(0.3, 0.9)}
            system.add_sensory_input(emotional_data, 'emotional', confidence=0.9)

            # Generate fused audio
            audio = system.fuse_and_synthesize(strategy, mode, duration=5.0)

            # Save audio
            filename = f"/home/activeloguser/DMLogn8n/sensory/ultimate/fusion_{strategy.value}_{mode.value}.wav"
            system.save_fused_audio(audio, filename)
            print(f"    Saved: {filename}")

    # Demonstrate real-time fusion
    print(f"\nStarting real-time sensory fusion...")
    system.start_real_time_fusion(chunk_duration=2.0)

    # Collect real-time audio
    real_time_audio = []
    start_time = time.time()
    while time.time() - start_time < 6.0:  # 6 seconds
        # Add simulated sensory inputs
        if np.random.random() < 0.3:
            modality = np.random.choice(['visual', 'emotional', 'tactile'])
            if modality == 'visual':
                data = np.random.randint(0, 256, (20, 20, 3), dtype=np.uint8)
            elif modality == 'emotional':
                data = {'valence': np.random.uniform(-1, 1), 'arousal': np.random.uniform(0, 1)}
            else:
                data = np.random.normal(50, 5, 50)

            system.add_sensory_input(data, modality, confidence=np.random.uniform(0.7, 1.0))

        # Get audio chunk
        chunk = system.get_audio_chunk()
        if chunk is not None:
            real_time_audio.extend(chunk)

        time.sleep(0.1)

    system.stop_real_time_fusion()

    if real_time_audio:
        real_time_audio = np.array(real_time_audio)
        rt_file = "/home/activeloguser/DMLogn8n/sensory/ultimate/sensory_fusion_realtime.wav"
        system.save_fused_audio(real_time_audio, rt_file)
        print(f"Saved real-time sensory fusion: {rt_file}")

    # Display system status
    status = system.get_system_status()
    print(f"\nSystem Status:")
    print(f"Sensory inputs processed: {status['performance_metrics']['sensory_inputs_processed']}")
    print(f"Fusions performed: {status['performance_metrics']['fusions_performed']}")
    print(f"Active modalities: {', '.join(status['performance_metrics']['active_modalities'])}")
    print(f"Average processing time: {status['performance_metrics'].get('average_processing_time', 0):.3f}s")

    if status['current_fusion_state']:
        fusion_state = status['current_fusion_state']
        print(f"\nCurrent Fusion State:")
        print(f"Active modalities: {', '.join(fusion_state['active_modalities'])}")
        print(f"Coherence level: {fusion_state['coherence_level']:.2f}")
        print(f"Attention focus: {fusion_state['attention_focus']}")
        print(f"Emotional tone: {fusion_state['emotional_tone']:.2f}")
        print(f"Arousal level: {fusion_state['arousal_level']:.2f}")
        print(f"Complexity index: {fusion_state['complexity_index']:.2f}")

    print("\nSENSORY FUSION COMPLETE!")
    print("This system can combine multiple sensory inputs into unified,")
    print("coherent perceptual experiences, creating entirely new forms of")
    print("audio that represent the integration of human senses.")

if __name__ == "__main__":
    main()