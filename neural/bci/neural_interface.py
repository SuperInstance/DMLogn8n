#!/usr/bin/env python3
"""
Neural Interface - Core BCI Signal Processing and Interpretation System
The bridge between human consciousness and the digital realm.

This module handles the fundamental signal processing pipeline for brain-computer
interfaces, supporting multiple hardware platforms and providing real-time neural
signal interpretation for thought-based control of game environments.
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

# BCI Platform Libraries
try:
    import pyOpenBCI
    OPENBCI_AVAILABLE = True
except ImportError:
    OPENBCI_AVAILABLE = False

try:
    import emotiv
    EMOTIV_AVAILABLE = True
except ImportError:
    EMOTIV_AVAILABLE = False

try:
    import neurosky
    NEUROSKY_AVAILABLE = True
except ImportError:
    NEUROSKY_AVAILABLE = False

# Signal Processing Libraries
from scipy import signal
from scipy.fft import fft, fftfreq
import sklearn.preprocessing as preprocessing
from sklearn.decomposition import PCA
from sklearn.feature_extraction import DictVectorizer

# Local imports
from .bc_security import NeuralSecurity

class BCIPlatform(Enum):
    """Supported BCI hardware platforms"""
    OPENBCI = "openbci"
    EMOTIV = "emotiv"
    NEUROSKY = "neurosky"
    SIMULATOR = "simulator"

class SignalType(Enum):
    """Types of neural signals"""
    EEG = "eeg"  # Electroencephalography
    ECOG = "ecog"  # Electrocorticography
    EMG = "emg"  # Electromyography
    EOG = "eog"  # Electrooculography
    MECPG = "mecpg"  # Micro-electrocorticography

class BrainWave(Enum):
    """Brain wave frequency bands"""
    DELTA = (0.5, 4, "Delta waves - Deep sleep, meditation")
    THETA = (4, 8, "Theta waves - Deep relaxation, creativity")
    ALPHA = (8, 13, "Alpha waves - Relaxed awareness, meditation")
    BETA = (13, 30, "Beta waves - Active thinking, focus")
    GAMMA = (30, 100, "Gamma waves - Higher processing, insight")
    HIGH_GAMMA = (100, 200, "High Gamma - Cognitive processing")

@dataclass
class NeuralSignal:
    """Neural signal data structure"""
    timestamp: float
    platform: BCIPlatform
    channels: np.ndarray
    sampling_rate: float
    signal_type: SignalType
    metadata: Dict[str, Any]

@dataclass
class ProcessedSignal:
    """Processed neural signal with features"""
    timestamp: float
    raw_signal: np.ndarray
    filtered_signal: np.ndarray
    features: Dict[str, float]
    brain_waves: Dict[str, float]
    signal_quality: float
    noise_level: float

@dataclass
class BCICalibration:
    """BCI calibration data"""
    user_id: str
    platform: BCIPlatform
    baseline_patterns: Dict[str, np.ndarray]
    noise_profile: np.ndarray
    channel_config: Dict[str, Any]
    created_at: float
    last_updated: float

class SignalProcessor:
    """Advanced neural signal processing engine"""

    def __init__(self, sampling_rate: float = 250, num_channels: int = 8):
        self.sampling_rate = sampling_rate
        self.num_channels = num_channels
        self.filter_bank = self._create_filter_bank()
        self.feature_extractor = FeatureExtractor()
        self.quality_assessor = SignalQualityAssessor()

    def _create_filter_bank(self) -> Dict[str, Any]:
        """Create a bank of digital filters for signal processing"""
        nyquist = self.sampling_rate / 2
        filters = {}

        # Bandpass filters for brain waves
        for wave in BrainWave:
            low, high, _ = wave.value
            if high > nyquist:
                high = nyquist * 0.95
            filters[wave.name] = signal.butter(
                4, [low/nyquist, high/nyquist],
                btype='band', analog=False
            )

        # Notch filter for power line noise (50/60 Hz)
        power_line_freq = 50  # Can be adjusted for different regions
        filters['notch'] = signal.iirnotch(
            power_line_freq, 30, self.sampling_rate
        )

        # High-pass filter to remove DC drift
        filters['highpass'] = signal.butter(
            4, 0.5/nyquist, btype='high', analog=False
        )

        return filters

    def preprocess_signal(self, signal_data: np.ndarray) -> np.ndarray:
        """Apply preprocessing filters to neural signal"""
        filtered = signal_data.copy()

        # Remove DC drift
        b, a = self.filter_bank['highpass']
        filtered = signal.filtfilt(b, a, filtered, axis=0)

        # Remove power line noise
        b, a = self.filter_bank['notch']
        filtered = signal.filtfilt(b, a, filtered, axis=0)

        # Remove artifacts (blink, muscle movement) using ICA
        filtered = self._remove_artifacts(filtered)

        return filtered

    def _remove_artifacts(self, signal_data: np.ndarray) -> np.ndarray:
        """Remove artifacts using Independent Component Analysis"""
        try:
            from sklearn.decomposition import FastICA

            # Apply ICA to separate components
            ica = FastICA(n_components=min(10, signal_data.shape[1]),
                         random_state=42)
            components = ica.fit_transform(signal_data)

            # Identify and remove artifact components
            # (This is a simplified version - real implementation would be more sophisticated)
            artifact_indices = self._identify_artifact_components(components)

            # Reconstruct signal without artifact components
            components[:, artifact_indices] = 0
            cleaned = ica.inverse_transform(components)

            return cleaned

        except Exception as e:
            logging.warning(f"Artifact removal failed: {e}")
            return signal_data

    def _identify_artifact_components(self, components: np.ndarray) -> List[int]:
        """Identify components that represent artifacts"""
        # Simplified artifact detection based on statistical properties
        artifact_indices = []

        for i in range(components.shape[1]):
            comp = components[:, i]

            # High amplitude or sharp transitions suggest artifacts
            amplitude = np.max(np.abs(comp))
            gradient = np.max(np.abs(np.gradient(comp)))

            if amplitude > 5 * np.std(comp) or gradient > np.percentile(np.abs(np.gradient(comp)), 95):
                artifact_indices.append(i)

        return artifact_indices

    def extract_features(self, signal_data: np.ndarray) -> Dict[str, float]:
        """Extract features from processed neural signal"""
        features = {}

        # Frequency domain features
        features.update(self._extract_frequency_features(signal_data))

        # Time domain features
        features.update(self._extract_time_features(signal_data))

        # Connectivity features (between channels)
        features.update(self._extract_connectivity_features(signal_data))

        # Entropy and complexity measures
        features.update(self._extract_complexity_features(signal_data))

        return features

    def _extract_frequency_features(self, signal_data: np.ndarray) -> Dict[str, float]:
        """Extract frequency domain features"""
        features = {}

        # Power spectral density for each brain wave band
        for wave in BrainWave:
            low, high, _ = wave.value
            b, a = self.filter_bank[wave.name]
            band_signal = signal.filtfilt(b, a, signal_data, axis=0)

            # Calculate band power
            power = np.mean(band_signal ** 2, axis=0)
            features[f"{wave.name.lower()}_power"] = np.mean(power)
            features[f"{wave.name.lower()}_power_std"] = np.std(power)

        # Spectral edge frequency (frequency below which 85% of power lies)
        fft_vals = fft(signal_data, axis=0)
        freqs = fftfreq(signal_data.shape[0], 1/self.sampling_rate)
        power_spectrum = np.abs(fft_vals) ** 2

        cumsum_power = np.cumsum(power_spectrum, axis=0)
        total_power = cumsum_power[-1, :]
        edge_freq_idx = np.argmax(cumsum_power >= 0.85 * total_power, axis=0)

        features['spectral_edge_freq'] = np.mean(freqs[edge_freq_idx])

        return features

    def _extract_time_features(self, signal_data: np.ndarray) -> Dict[str, float]:
        """Extract time domain features"""
        features = {}

        # Basic statistics
        features['mean_amplitude'] = np.mean(signal_data)
        features['std_amplitude'] = np.std(signal_data)
        features['rms'] = np.sqrt(np.mean(signal_data ** 2))

        # Hjorth parameters (activity, mobility, complexity)
        diff1 = np.diff(signal_data, axis=0)
        diff2 = np.diff(diff1, axis=0)

        # Activity (variance)
        features['hjorth_activity'] = np.var(signal_data, axis=0).mean()

        # Mobility (mean frequency)
        features['hjorth_mobility'] = np.sqrt(
            np.var(diff1, axis=0) / np.var(signal_data, axis=0)
        ).mean()

        # Complexity (change in frequency)
        features['hjorth_complexity'] = (
            np.sqrt(np.var(diff2, axis=0) / np.var(diff1, axis=0)) /
            np.sqrt(np.var(diff1, axis=0) / np.var(signal_data, axis=0))
        ).mean()

        # Zero crossings
        features['zero_crossings'] = np.mean(
            np.sum(np.diff(np.sign(signal_data), axis=0) != 0, axis=0)
        )

        return features

    def _extract_connectivity_features(self, signal_data: np.ndarray) -> Dict[str, float]:
        """Extract connectivity features between channels"""
        features = {}

        if signal_data.shape[1] > 1:
            # Coherence matrix
            from scipy.signal import coherence

            coherence_matrix = []
            for i in range(signal_data.shape[1]):
                for j in range(i+1, signal_data.shape[1]):
                    f, Cxy = coherence(
                        signal_data[:, i], signal_data[:, j],
                        fs=self.sampling_rate, nperseg=256
                    )
                    coherence_matrix.append(np.mean(Cxy))

            features['mean_coherence'] = np.mean(coherence_matrix)
            features['max_coherence'] = np.max(coherence_matrix)

            # Correlation matrix
            corr_matrix = np.corrcoef(signal_data.T)
            # Remove diagonal (self-correlation)
            np.fill_diagonal(corr_matrix, 0)
            features['mean_correlation'] = np.mean(np.abs(corr_matrix))
            features['max_correlation'] = np.max(np.abs(corr_matrix))

        return features

    def _extract_complexity_features(self, signal_data: np.ndarray) -> Dict[str, float]:
        """Extract entropy and complexity features"""
        features = {}

        # Approximate entropy
        features['approximate_entropy'] = self._approximate_entropy(signal_data).mean()

        # Sample entropy
        features['sample_entropy'] = self._sample_entropy(signal_data).mean()

        # Fractal dimension
        features['fractal_dimension'] = self._fractal_dimension(signal_data).mean()

        return features

    def _approximate_entropy(self, signal_data: np.ndarray, m: int = 2, r: float = None) -> np.ndarray:
        """Calculate approximate entropy"""
        if r is None:
            r = 0.2 * np.std(signal_data, axis=0)

        def _apen_single_channel(channel_data):
            N = len(channel_data)

            def _phi(m):
                patterns = np.array([channel_data[i:i+m] for i in range(N-m+1)])
                C = np.sum(
                    np.max(np.abs(patterns[:, None] - patterns[None, :]), axis=2) <= r,
                    axis=1
                ) / (N - m + 1)
                return np.mean(np.log(C))

            return _phi(m) - _phi(m + 1)

        return np.array([
            _apen_single_channel(signal_data[:, i])
            for i in range(signal_data.shape[1])
        ])

    def _sample_entropy(self, signal_data: np.ndarray, m: int = 2, r: float = None) -> np.ndarray:
        """Calculate sample entropy"""
        if r is None:
            r = 0.2 * np.std(signal_data, axis=0)

        def _sampen_single_channel(channel_data):
            N = len(channel_data)

            def _count_matches(m):
                patterns = np.array([channel_data[i:i+m] for i in range(N-m+1)])
                distances = np.max(np.abs(patterns[:, None] - patterns[None, :]), axis=2)
                return np.sum(distances <= r) - (N - m + 1)

            B = _count_matches(m)
            A = _count_matches(m + 1)

            if B == 0 or A == 0:
                return 0

            return -np.log(A / B)

        return np.array([
            _sampen_single_channel(signal_data[:, i])
            for i in range(signal_data.shape[1])
        ])

    def _fractal_dimension(self, signal_data: np.ndarray) -> np.ndarray:
        """Calculate fractal dimension using Higuchi's method"""
        def _higuchi_fd(channel_data, k_max=10):
            N = len(channel_data)
            L = []

            for k in range(1, k_max + 1):
                Lk = 0
                for m in range(k):
                    # Create k-length subsequence
                    idx = np.arange(1, int(np.floor((N - m) / k)), dtype=int) * k + m
                    if len(idx) < 2:
                        continue

                    # Calculate length
                    sum_diff = np.sum(np.abs(np.diff(channel_data[idx])))
                    Lk += sum_diff * (N - 1) / ((len(idx) - 1) * k)

                L.append(Lk / k)

            # Fit log-log regression
            k_vals = np.arange(1, k_max + 1)
            log_k = np.log(k_vals)
            log_L = np.log(L)

            # Linear regression
            coeffs = np.polyfit(log_k, log_L, 1)
            return coeffs[0]

        return np.array([
            _higuchi_fd(signal_data[:, i])
            for i in range(signal_data.shape[1])
        ])

class SignalQualityAssessor:
    """Assess the quality of neural signals in real-time"""

    def __init__(self):
        self.quality_thresholds = {
            'signal_to_noise': 3.0,
            'line_noise_threshold': 0.1,
            'artifact_threshold': 0.2,
            'connection_quality': 0.8
        }

    def assess_quality(self, signal_data: np.ndarray, sampling_rate: float) -> float:
        """Assess overall signal quality (0.0 to 1.0)"""
        quality_scores = []

        # Signal-to-noise ratio
        snr_score = self._assess_snr(signal_data)
        quality_scores.append(snr_score)

        # Line noise assessment
        line_noise_score = self._assess_line_noise(signal_data, sampling_rate)
        quality_scores.append(line_noise_score)

        # Artifact detection
        artifact_score = self._assess_artifacts(signal_data)
        quality_scores.append(artifact_score)

        # Stationarity
        stationarity_score = self._assess_stationarity(signal_data)
        quality_scores.append(stationarity_score)

        return np.mean(quality_scores)

    def _assess_snr(self, signal_data: np.ndarray) -> float:
        """Assess signal-to-noise ratio"""
        # Calculate signal power
        signal_power = np.var(signal_data, axis=0)

        # Estimate noise power (high-frequency content)
        from scipy.signal import butter, filtfilt
        nyquist = 250 / 2  # Assuming 250 Hz sampling
        b, a = butter(4, 40/nyquist, btype='high')
        high_freq = filtfilt(b, a, signal_data, axis=0)
        noise_power = np.var(high_freq, axis=0)

        # Calculate SNR in dB
        snr_db = 10 * np.log10(signal_power / (noise_power + 1e-10))

        # Convert to 0-1 scale (assuming good SNR is > 20 dB)
        return np.clip((snr_db.mean() - 0) / 20, 0, 1)

    def _assess_line_noise(self, signal_data: np.ndarray, sampling_rate: float) -> float:
        """Assess power line noise contamination"""
        from scipy.signal import periodogram

        # Compute power spectral density
        freqs, psd = periodogram(signal_data, fs=sampling_rate, axis=0)

        # Find power line frequency components (50 Hz and harmonics)
        power_line_freqs = [50, 100, 150]  # Fundamental and harmonics

        total_power = np.sum(psd, axis=0)
        line_power = 0

        for freq in power_line_freqs:
            if freq < freqs[-1]:
                # Find nearest frequency bin
                idx = np.argmin(np.abs(freqs - freq))
                # Power in narrow band around frequency
                band_idx = np.where(np.abs(freqs - freq) < 2)[0]
                line_power += np.sum(psd[band_idx], axis=0)

        # Line noise ratio
        line_noise_ratio = np.mean(line_power / (total_power + 1e-10))

        # Convert to quality score (lower is better)
        return np.clip(1 - (line_noise_ratio / self.quality_thresholds['line_noise_threshold']), 0, 1)

    def _assess_artifacts(self, signal_data: np.ndarray) -> float:
        """Assess presence of artifacts"""
        artifact_indicators = []

        # High amplitude peaks
        amplitude_threshold = 5 * np.std(signal_data)
        peaks = np.sum(np.abs(signal_data) > amplitude_threshold, axis=0)
        artifact_indicators.append(peaks.mean() / len(signal_data))

        # Sudden jumps (high gradient)
        gradient = np.gradient(signal_data, axis=0)
        jump_threshold = 5 * np.std(gradient)
        jumps = np.sum(np.abs(gradient) > jump_threshold, axis=0)
        artifact_indicators.append(jumps.mean() / len(gradient))

        # Flat segments (loss of signal)
        flat_segments = np.sum(np.std(np.abs(np.diff(signal_data, axis=0)), axis=0) < 0.01)
        artifact_indicators.append(flat_segments.mean() / signal_data.shape[1])

        # Combine indicators
        artifact_score = np.mean(artifact_indicators)

        # Convert to quality score
        return np.clip(1 - (artifact_score / self.quality_thresholds['artifact_threshold']), 0, 1)

    def _assess_stationarity(self, signal_data: np.ndarray) -> float:
        """Assess signal stationarity"""
        # Split signal into windows and compare statistics
        window_size = len(signal_data) // 10
        windows = [signal_data[i:i+window_size] for i in range(0, len(signal_data)-window_size, window_size)]

        if len(windows) < 2:
            return 1.0

        # Compare mean and variance across windows
        means = [np.mean(w) for w in windows]
        variances = [np.var(w) for w in windows]

        mean_cv = np.std(means) / (np.mean(np.abs(means)) + 1e-10)
        var_cv = np.std(variances) / (np.mean(variances) + 1e-10)

        # Stationarity score (lower coefficient of variation is better)
        stationarity = 1 - np.mean([mean_cv, var_cv]) / 2
        return np.clip(stationarity, 0, 1)

class FeatureExtractor:
    """Extract meaningful features from neural signals"""

    def __init__(self):
        self.scaler = preprocessing.StandardScaler()
        self.pca = PCA(n_components=0.95)  # Keep 95% of variance

    def extract_all_features(self, signal_data: np.ndarray, sampling_rate: float) -> Dict[str, float]:
        """Extract comprehensive feature set"""
        features = {}

        # Time domain features
        features.update(self._extract_time_features(signal_data))

        # Frequency domain features
        features.update(self._extract_frequency_features(signal_data, sampling_rate))

        # Connectivity features
        features.update(self._extract_connectivity_features(signal_data))

        # Nonlinear features
        features.update(self._extract_nonlinear_features(signal_data))

        return features

    def _extract_time_features(self, signal_data: np.ndarray) -> Dict[str, float]:
        """Extract time-domain features"""
        features = {}

        # Basic statistical features
        features['mean'] = np.mean(signal_data)
        features['std'] = np.std(signal_data)
        features['var'] = np.var(signal_data)
        features['rms'] = np.sqrt(np.mean(signal_data ** 2))
        features['skewness'] = self._skewness(signal_data)
        features['kurtosis'] = self._kurtosis(signal_data)

        # Peak features
        features['peak_to_peak'] = np.ptp(signal_data)
        features['max_amplitude'] = np.max(np.abs(signal_data))

        # Zero crossing rate
        features['zero_crossing_rate'] = np.mean([
            np.sum(np.diff(np.sign(signal_data[:, i])) != 0) / len(signal_data)
            for i in range(signal_data.shape[1])
        ])

        return features

    def _extract_frequency_features(self, signal_data: np.ndarray, sampling_rate: float) -> Dict[str, float]:
        """Extract frequency-domain features"""
        features = {}

        # FFT-based features
        fft_vals = fft(signal_data, axis=0)
        freqs = fftfreq(signal_data.shape[0], 1/sampling_rate)
        power_spectrum = np.abs(fft_vals) ** 2

        # Spectral centroid
        features['spectral_centroid'] = np.sum(freqs[:, None] * power_spectrum, axis=0) / np.sum(power_spectrum, axis=0)
        features['spectral_centroid'] = np.mean(features['spectral_centroid'])

        # Spectral bandwidth
        features['spectral_bandwidth'] = np.sqrt(
            np.sum(((freqs[:, None] - features['spectral_centroid']) ** 2) * power_spectrum, axis=0) /
            np.sum(power_spectrum, axis=0)
        )
        features['spectral_bandwidth'] = np.mean(features['spectral_bandwidth'])

        # Spectral rolloff (frequency below which 85% of energy is contained)
        cumsum_power = np.cumsum(power_spectrum, axis=0)
        total_power = cumsum_power[-1, :]
        rolloff_idx = np.argmax(cumsum_power >= 0.85 * total_power[:, None], axis=0)
        features['spectral_rolloff'] = np.mean(freqs[rolloff_idx])

        return features

    def _extract_connectivity_features(self, signal_data: np.ndarray) -> Dict[str, float]:
        """Extract connectivity features between channels"""
        features = {}

        if signal_data.shape[1] > 1:
            # Correlation-based features
            corr_matrix = np.corrcoef(signal_data.T)

            # Remove diagonal elements
            np.fill_diagonal(corr_matrix, 0)

            features['mean_correlation'] = np.mean(np.abs(corr_matrix))
            features['max_correlation'] = np.max(np.abs(corr_matrix))
            features['correlation_entropy'] = -np.sum(
                np.abs(corr_matrix) * np.log(np.abs(corr_matrix) + 1e-10)
            ) / 2

            # Phase synchronization
            analytic_signal = signal.hilbert(signal_data, axis=0)
            instantaneous_phase = np.unwrap(np.angle(analytic_signal), axis=0)

            phase_lock_values = []
            for i in range(signal_data.shape[1]):
                for j in range(i+1, signal_data.shape[1]):
                    phase_diff = instantaneous_phase[:, i] - instantaneous_phase[:, j]
                    plv = np.abs(np.mean(np.exp(1j * phase_diff)))
                    phase_lock_values.append(plv)

            features['mean_phase_locking'] = np.mean(phase_lock_values)
            features['max_phase_locking'] = np.max(phase_lock_values)

        return features

    def _extract_nonlinear_features(self, signal_data: np.ndarray) -> Dict[str, float]:
        """Extract nonlinear and complexity features"""
        features = {}

        # Entropy measures
        features['sample_entropy'] = np.mean([
            self._sample_entropy(signal_data[:, i])
            for i in range(signal_data.shape[1])
        ])

        features['approximate_entropy'] = np.mean([
            self._approximate_entropy(signal_data[:, i])
            for i in range(signal_data.shape[1])
        ])

        # Fractal dimension
        features['fractal_dimension'] = np.mean([
            self._higuchi_fractal_dimension(signal_data[:, i])
            for i in range(signal_data.shape[1])
        ])

        # Hurst exponent (long-range correlation)
        features['hurst_exponent'] = np.mean([
            self._hurst_exponent(signal_data[:, i])
            for i in range(signal_data.shape[1])
        ])

        return features

    def _skewness(self, signal_data: np.ndarray) -> float:
        """Calculate skewness of signal"""
        return np.mean([
            np.mean(((signal_data[:, i] - np.mean(signal_data[:, i])) /
                    (np.std(signal_data[:, i]) + 1e-10)) ** 3)
            for i in range(signal_data.shape[1])
        ])

    def _kurtosis(self, signal_data: np.ndarray) -> float:
        """Calculate kurtosis of signal"""
        return np.mean([
            np.mean(((signal_data[:, i] - np.mean(signal_data[:, i])) /
                    (np.std(signal_data[:, i]) + 1e-10)) ** 4) - 3
            for i in range(signal_data.shape[1])
        ])

    def _sample_entropy(self, channel_data: np.ndarray, m: int = 2, r: float = None) -> float:
        """Calculate sample entropy"""
        if r is None:
            r = 0.2 * np.std(channel_data)

        N = len(channel_data)
        patterns_m = np.array([channel_data[i:i+m] for i in range(N-m+1)])
        patterns_m1 = np.array([channel_data[i:i+m+1] for i in range(N-m)])

        def _count_matches(patterns):
            matches = 0
            for i in range(len(patterns)):
                for j in range(i+1, len(patterns)):
                    if np.max(np.abs(patterns[i] - patterns[j])) <= r:
                        matches += 1
            return matches

        B = _count_matches(patterns_m)
        A = _count_matches(patterns_m1)

        if B == 0 or A == 0:
            return 0

        return -np.log(A / B)

    def _approximate_entropy(self, channel_data: np.ndarray, m: int = 2, r: float = None) -> float:
        """Calculate approximate entropy"""
        if r is None:
            r = 0.2 * np.std(channel_data)

        N = len(channel_data)

        def _phi(m):
            patterns = np.array([channel_data[i:i+m] for i in range(N-m+1)])
            C = np.zeros(len(patterns))

            for i in range(len(patterns)):
                C[i] = np.sum(np.max(np.abs(patterns - patterns[i]), axis=1) <= r) / (N - m + 1)

            return np.mean(np.log(C + 1e-10))

        return _phi(m) - _phi(m + 1)

    def _higuchi_fractal_dimension(self, channel_data: np.ndarray, k_max: int = 10) -> float:
        """Calculate fractal dimension using Higuchi's method"""
        N = len(channel_data)
        L = []

        for k in range(1, k_max + 1):
            Lk = 0
            for m in range(k):
                idx = np.arange(1, int(np.floor((N - m) / k)), dtype=int) * k + m
                if len(idx) < 2:
                    continue

                sum_diff = np.sum(np.abs(np.diff(channel_data[idx])))
                Lk += sum_diff * (N - 1) / ((len(idx) - 1) * k)

            if k > 0:
                L.append(Lk / k)

        if len(L) < 2:
            return 1.0

        # Linear regression on log-log plot
        k_vals = np.arange(1, len(L) + 1)
        log_k = np.log(k_vals)
        log_L = np.log(L)

        coeffs = np.polyfit(log_k, log_L, 1)
        return coeffs[0]

    def _hurst_exponent(self, channel_data: np.ndarray) -> float:
        """Calculate Hurst exponent"""
        N = len(channel_data)
        max_k = N // 4

        if max_k < 4:
            return 0.5

        R_S = []

        for k in range(4, max_k + 1, 4):
            # Divide data into chunks of size k
            chunks = [channel_data[i:i+k] for i in range(0, N - k + 1, k)]

            chunk_RS = []
            for chunk in chunks:
                if len(chunk) < 2:
                    continue

                # Remove mean
                chunk = chunk - np.mean(chunk)

                # Cumulative sum
                cumsum = np.cumsum(chunk)

                # Range
                R = np.max(cumsum) - np.min(cumsum)

                # Standard deviation
                S = np.std(chunk)

                if S > 0:
                    chunk_RS.append(R / S)

            if chunk_RS:
                R_S.append(np.mean(chunk_RS))

        if len(R_S) < 2:
            return 0.5

        # Log-log regression
        k_vals = np.arange(4, 4 * len(R_S) + 1, 4)
        log_k = np.log(k_vals)
        log_RS = np.log(R_S)

        coeffs = np.polyfit(log_k, log_RS, 1)
        return coeffs[0]

class NeuralInterface:
    """Main neural interface system connecting BCI hardware to AI agents"""

    def __init__(self, platform: BCIPlatform = BCIPlatform.SIMULATOR):
        self.platform = platform
        self.processor = SignalProcessor()
        self.quality_assessor = SignalQualityAssessor()
        self.feature_extractor = FeatureExtractor()
        self.security = NeuralSecurity()

        # Real-time processing components
        self.signal_buffer = deque(maxlen=1000)
        self.feature_buffer = deque(maxlen=100)
        self.processing_queue = queue.Queue()
        self.result_queue = queue.Queue()

        # Threading
        self.is_running = False
        self.acquisition_thread = None
        self.processing_thread = None

        # Calibration
        self.calibration_data = None
        self.is_calibrated = False

        # Callbacks
        self.signal_callbacks = []
        self.feature_callbacks = []
        self.quality_callbacks = []

        # Metrics
        self.metrics = {
            'signals_processed': 0,
            'features_extracted': 0,
            'quality_scores': deque(maxlen=100),
            'processing_times': deque(maxlen=100),
            'errors': deque(maxlen=100)
        }

        self.logger = logging.getLogger(__name__)

    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        """Initialize the neural interface"""
        try:
            self.logger.info(f"Initializing neural interface for platform: {self.platform}")

            # Initialize platform-specific hardware
            if self.platform == BCIPlatform.OPENBCI and OPENBCI_AVAILABLE:
                success = await self._init_openbci(config)
            elif self.platform == BCIPlatform.EMOTIV and EMOTIV_AVAILABLE:
                success = await self._init_emotiv(config)
            elif self.platform == BCIPlatform.NEUROSKY and NEUROSKY_AVAILABLE:
                success = await self._init_neurosky(config)
            elif self.platform == BCIPlatform.SIMULATOR:
                success = await self._init_simulator(config)
            else:
                self.logger.warning(f"Platform {self.platform} not available, using simulator")
                self.platform = BCIPlatform.SIMULATOR
                success = await self._init_simulator(config)

            if success:
                # Initialize security
                await self.security.initialize()

                # Start processing threads
                self._start_processing()

                self.logger.info("Neural interface initialized successfully")
                return True
            else:
                self.logger.error("Failed to initialize neural interface")
                return False

        except Exception as e:
            self.logger.error(f"Error initializing neural interface: {e}")
            return False

    async def _init_openbci(self, config: Dict[str, Any]) -> bool:
        """Initialize OpenBCI connection"""
        try:
            # OpenBCI-specific initialization
            # This would connect to actual OpenBCI hardware
            self.logger.info("Initializing OpenBCI connection")
            return True
        except Exception as e:
            self.logger.error(f"OpenBCI initialization failed: {e}")
            return False

    async def _init_emotiv(self, config: Dict[str, Any]) -> bool:
        """Initialize Emotiv connection"""
        try:
            # Emotiv-specific initialization
            self.logger.info("Initializing Emotiv connection")
            return True
        except Exception as e:
            self.logger.error(f"Emotiv initialization failed: {e}")
            return False

    async def _init_neurosky(self, config: Dict[str, Any]) -> bool:
        """Initialize NeuroSky connection"""
        try:
            # NeuroSky-specific initialization
            self.logger.info("Initializing NeuroSky connection")
            return True
        except Exception as e:
            self.logger.error(f"NeuroSky initialization failed: {e}")
            return False

    async def _init_simulator(self, config: Dict[str, Any]) -> bool:
        """Initialize BCI simulator"""
        try:
            self.simulator_config = config or {}
            self.simulator_config.update({
                'sampling_rate': 250,
                'num_channels': 8,
                'noise_level': 0.1,
                'signal_types': ['eeg', 'emg']
            })
            self.logger.info("Initializing BCI simulator")
            return True
        except Exception as e:
            self.logger.error(f"Simulator initialization failed: {e}")
            return False

    def _start_processing(self):
        """Start real-time processing threads"""
        self.is_running = True

        # Signal acquisition thread
        self.acquisition_thread = threading.Thread(target=self._acquisition_loop)
        self.acquisition_thread.daemon = True
        self.acquisition_thread.start()

        # Signal processing thread
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def _acquisition_loop(self):
        """Main signal acquisition loop"""
        while self.is_running:
            try:
                # Acquire signal from platform
                signal_data = self._acquire_signal()

                if signal_data is not None:
                    timestamp = time.time()

                    # Create neural signal object
                    neural_signal = NeuralSignal(
                        timestamp=timestamp,
                        platform=self.platform,
                        channels=signal_data,
                        sampling_rate=self.processor.sampling_rate,
                        signal_type=SignalType.EEG,
                        metadata={}
                    )

                    # Add to buffer
                    self.signal_buffer.append(neural_signal)

                    # Queue for processing
                    self.processing_queue.put(neural_signal)

                time.sleep(1/self.processor.sampling_rate)

            except Exception as e:
                self.logger.error(f"Signal acquisition error: {e}")
                self.metrics['errors'].append({
                    'timestamp': time.time(),
                    'type': 'acquisition',
                    'error': str(e)
                })

    def _acquire_signal(self) -> Optional[np.ndarray]:
        """Acquire signal data from current platform"""
        if self.platform == BCIPlatform.SIMULATOR:
            return self._simulate_signal()
        else:
            # Would acquire from real hardware
            return None

    def _simulate_signal(self) -> np.ndarray:
        """Simulate neural signal data"""
        config = self.simulator_config
        num_channels = config['num_channels']
        noise_level = config['noise_level']

        # Generate realistic EEG-like signal
        t = np.linspace(0, 1, int(config['sampling_rate']))
        signal_data = np.zeros((len(t), num_channels))

        for ch in range(num_channels):
            # Base oscillations (brain waves)
            signal_data[:, ch] = (
                0.5 * np.sin(2 * np.pi * 10 * t) +  # Alpha wave
                0.3 * np.sin(2 * np.pi * 20 * t) +  # Beta wave
                0.2 * np.sin(2 * np.pi * 5 * t)     # Theta wave
            )

            # Add channel-specific characteristics
            signal_data[:, ch] += 0.1 * ch * np.sin(2 * np.pi * 2 * t)

            # Add noise
            signal_data[:, ch] += noise_level * np.random.randn(len(t))

        return signal_data

    def _processing_loop(self):
        """Main signal processing loop"""
        while self.is_running:
            try:
                # Get signal from queue
                neural_signal = self.processing_queue.get(timeout=1.0)

                # Process signal
                processed_signal = self._process_signal(neural_signal)

                if processed_signal:
                    # Add to results
                    self.result_queue.put(processed_signal)

                    # Update metrics
                    self.metrics['signals_processed'] += 1
                    self.metrics['features_extracted'] += 1

                    # Trigger callbacks
                    self._trigger_callbacks(processed_signal)

            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Signal processing error: {e}")
                self.metrics['errors'].append({
                    'timestamp': time.time(),
                    'type': 'processing',
                    'error': str(e)
                })

    def _process_signal(self, neural_signal: NeuralSignal) -> Optional[ProcessedSignal]:
        """Process neural signal and extract features"""
        try:
            start_time = time.time()

            # Preprocess signal
            filtered_signal = self.processor.preprocess_signal(neural_signal.channels)

            # Assess quality
            quality = self.quality_assessor.assess_quality(
                filtered_signal,
                neural_signal.sampling_rate
            )
            self.metrics['quality_scores'].append(quality)

            # Extract features
            features = self.feature_extractor.extract_all_features(
                filtered_signal,
                neural_signal.sampling_rate
            )

            # Extract brain wave powers
            brain_waves = self._extract_brain_waves(filtered_signal)

            # Calculate noise level
            noise_level = self._estimate_noise_level(filtered_signal)

            # Create processed signal
            processed_signal = ProcessedSignal(
                timestamp=neural_signal.timestamp,
                raw_signal=neural_signal.channels,
                filtered_signal=filtered_signal,
                features=features,
                brain_waves=brain_waves,
                signal_quality=quality,
                noise_level=noise_level
            )

            # Update processing time
            processing_time = time.time() - start_time
            self.metrics['processing_times'].append(processing_time)

            return processed_signal

        except Exception as e:
            self.logger.error(f"Signal processing failed: {e}")
            return None

    def _extract_brain_waves(self, signal_data: np.ndarray) -> Dict[str, float]:
        """Extract power in different brain wave bands"""
        brain_waves = {}

        for wave in BrainWave:
            low, high, _ = wave.value
            b, a = self.processor.filter_bank[wave.name]
            band_signal = signal.filtfilt(b, a, signal_data, axis=0)
            power = np.mean(band_signal ** 2)
            brain_waves[wave.name.lower()] = power

        return brain_waves

    def _estimate_noise_level(self, signal_data: np.ndarray) -> float:
        """Estimate noise level in signal"""
        # High-frequency power as noise estimate
        from scipy.signal import butter, filtfilt
        nyquist = self.processor.sampling_rate / 2
        b, a = butter(4, 40/nyquist, btype='high')
        high_freq = filtfilt(b, a, signal_data, axis=0)
        noise_power = np.mean(high_freq ** 2)
        return noise_power

    def _trigger_callbacks(self, processed_signal: ProcessedSignal):
        """Trigger registered callbacks"""
        for callback in self.signal_callbacks:
            try:
                callback(processed_signal)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")

        for callback in self.feature_callbacks:
            try:
                callback(processed_signal.features)
            except Exception as e:
                self.logger.error(f"Feature callback error: {e}")

        for callback in self.quality_callbacks:
            try:
                callback(processed_signal.signal_quality)
            except Exception as e:
                self.logger.error(f"Quality callback error: {e}")

    def add_signal_callback(self, callback: Callable[[ProcessedSignal], None]):
        """Add callback for processed signals"""
        self.signal_callbacks.append(callback)

    def add_feature_callback(self, callback: Callable[[Dict[str, float]], None]):
        """Add callback for extracted features"""
        self.feature_callbacks.append(callback)

    def add_quality_callback(self, callback: Callable[[float], None]):
        """Add callback for signal quality"""
        self.quality_callbacks.append(callback)

    async def calibrate(self, duration: float = 60.0) -> bool:
        """Calibrate the neural interface for the user"""
        try:
            self.logger.info(f"Starting calibration for {duration} seconds")

            # Collect baseline data
            baseline_data = []
            start_time = time.time()

            while time.time() - start_time < duration:
                if not self.result_queue.empty():
                    processed_signal = self.result_queue.get()
                    if processed_signal.signal_quality > 0.7:  # Good quality signals only
                        baseline_data.append(processed_signal)
                await asyncio.sleep(0.1)

            if len(baseline_data) < 10:
                self.logger.error("Insufficient quality data for calibration")
                return False

            # Create calibration profile
            self.calibration_data = self._create_calibration_profile(baseline_data)
            self.is_calibrated = True

            self.logger.info("Calibration completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Calibration failed: {e}")
            return False

    def _create_calibration_profile(self, baseline_data: List[ProcessedSignal]) -> BCICalibration:
        """Create calibration profile from baseline data"""
        # Extract baseline patterns
        baseline_features = [s.features for s in baseline_data]
        baseline_brain_waves = [s.brain_waves for s in baseline_data]

        # Calculate averages and standard deviations
        avg_features = {}
        std_features = {}

        for key in baseline_features[0].keys():
            values = [f[key] for f in baseline_features]
            avg_features[key] = np.mean(values)
            std_features[key] = np.std(values)

        avg_brain_waves = {}
        std_brain_waves = {}

        for key in baseline_brain_waves[0].keys():
            values = [b[key] for b in baseline_brain_waves]
            avg_brain_waves[key] = np.mean(values)
            std_brain_waves[key] = np.std(values)

        return BCICalibration(
            user_id="default",  # Would get from user system
            platform=self.platform,
            baseline_patterns={
                'features': avg_features,
                'brain_waves': avg_brain_waves,
                'features_std': std_features,
                'brain_waves_std': std_brain_waves
            },
            noise_profile=np.array([s.noise_level for s in baseline_data]),
            channel_config={
                'num_channels': self.processor.num_channels,
                'sampling_rate': self.processor.sampling_rate
            },
            created_at=time.time(),
            last_updated=time.time()
        )

    def get_latest_signal(self) -> Optional[ProcessedSignal]:
        """Get the most recent processed signal"""
        try:
            while not self.result_queue.empty():
                self.latest_signal = self.result_queue.get_nowait()
            return self.latest_signal
        except (queue.Empty, AttributeError):
            return None

    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        return {
            'signals_processed': self.metrics['signals_processed'],
            'features_extracted': self.metrics['features_extracted'],
            'average_quality': np.mean(list(self.metrics['quality_scores'])) if self.metrics['quality_scores'] else 0,
            'average_processing_time': np.mean(list(self.metrics['processing_times'])) if self.metrics['processing_times'] else 0,
            'error_count': len(self.metrics['errors']),
            'is_calibrated': self.is_calibrated,
            'platform': self.platform.value,
            'buffer_sizes': {
                'signal_buffer': len(self.signal_buffer),
                'feature_buffer': len(self.feature_buffer),
                'processing_queue': self.processing_queue.qsize(),
                'result_queue': self.result_queue.qsize()
            }
        }

    async def shutdown(self):
        """Shutdown the neural interface"""
        self.logger.info("Shutting down neural interface")

        self.is_running = False

        # Wait for threads to finish
        if self.acquisition_thread:
            self.acquisition_thread.join(timeout=5.0)
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)

        # Clear buffers
        self.signal_buffer.clear()
        self.feature_buffer.clear()

        # Shutdown security
        await self.security.shutdown()

        self.logger.info("Neural interface shutdown complete")

# Main interface for external access
async def create_neural_interface(platform: str = "simulator", config: Dict[str, Any] = None) -> NeuralInterface:
    """Create and initialize a neural interface"""
    platform_enum = BCIPlatform(platform.lower())
    interface = NeuralInterface(platform_enum)

    success = await interface.initialize(config)
    if not success:
        raise RuntimeError("Failed to initialize neural interface")

    return interface

if __name__ == "__main__":
    # Example usage
    async def main():
        interface = await create_neural_interface("simulator")

        # Add callbacks
        def on_signal(processed_signal):
            print(f"Signal quality: {processed_signal.signal_quality:.2f}")
            print(f"Brain waves: {processed_signal.brain_waves}")

        def on_features(features):
            print(f"Features: {len(features)} extracted")

        interface.add_signal_callback(on_signal)
        interface.add_feature_callback(on_features)

        # Calibrate
        await interface.calibrate(duration=10.0)

        # Run for a while
        await asyncio.sleep(5.0)

        # Get metrics
        metrics = interface.get_metrics()
        print(f"Metrics: {metrics}")

        # Shutdown
        await interface.shutdown()

    asyncio.run(main())