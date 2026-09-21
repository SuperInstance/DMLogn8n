#!/usr/bin/env python3
"""
Chaos Theory - Chaos theory and complexity science integration
Analyzes complex systems, detects chaos, models nonlinear dynamics, and identifies attractors
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
import json
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import logging

try:
    from scipy import stats, integrate, optimize
    from scipy.signal import find_peaks
    from scipy.fft import fft, ifft, fftfreq
    from sklearn.decomposition import PCA
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score
except ImportError:
    print("Warning: scipy/scikit-learn not available. Using simplified chaos analysis")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChaosType(Enum):
    """Types of chaotic behavior"""
    DETERMINISTIC_CHAOS = "deterministic_chaos"
    STOCHASTIC_CHAOS = "stochastic_chaos"
    EDGE_OF_CHAOS = "edge_of_chaos"
    SELF_ORGANIZED_CRITICALITY = "self_organized_criticality"
    STRANGE_ATTRACTOR = "strange_attractor"
    PERIOD_DOUBLING = "period_doubling"
    INTERMITTENCY = "intermittency"
    QUASI_PERIODICITY = "quasi_periodicity"


class SystemComplexity(Enum):
    """Complexity levels of systems"""
    SIMPLE = "simple"
    COMPLICATED = "complicated"
    COMPLEX = "complex"
    CHAOTIC = "chaotic"
    RANDOM = "random"


class AttractorType(Enum):
    """Types of attractors in dynamical systems"""
    FIXED_POINT = "fixed_point"
    LIMIT_CYCLE = "limit_cycle"
    STRANGE_ATTRACTOR = "strange_attractor"
    TORUS = "torus"
    REPELLOR = "repellor"


@dataclass
class ChaosMetrics:
    """Metrics for chaos analysis"""
    lyapunov_exponent: float
    correlation_dimension: float
    entropy: float
    hurst_exponent: float
    detrended_fluctuation: float
    recurrence_rate: float
    determinism: float
    laminarity: float
    predictability: float
    complexity_score: float


@dataclass
class Attractor:
    """Represents an attractor in the phase space"""
    attractor_id: str
    attractor_type: AttractorType
    center: List[float]
    radius: float
    strength: float
    basin_of_attraction: List[List[float]]
    dimension: int
    stability: float
    period: Optional[float] = None


@dataclass
class BifurcationPoint:
    """Represents a bifurcation point in system dynamics"""
    point_id: str
    parameter_value: float
    bifurcation_type: str
    before_state: SystemComplexity
    after_state: SystemComplexity
    critical_exponent: float
    hysteresis: bool = False


@dataclass
class ChaosAnalysis:
    """Results of chaos analysis"""
    analysis_id: str
    timestamp: datetime
    system_name: str
    data_series: np.ndarray
    time_series: List[datetime]
    complexity_level: SystemComplexity
    chaos_type: Optional[ChaosType]
    metrics: ChaosMetrics
    attractors: List[Attractor]
    bifurcations: List[BifurcationPoint]
    phase_space: np.ndarray
    recurrence_plot: np.ndarray
    predictability_horizon: float
    recommendations: List[str]


class LyapunovExponent:
    """Calculate Lyapunov exponents for chaos detection"""

    @staticmethod
    def calculate_largest_lyapunov(data: np.ndarray, max_time: int = 100,
                                  tolerance: float = 0.01) -> float:
        """Calculate the largest Lyapunov exponent"""
        try:
            if len(data) < max_time * 2:
                return 0.0  # Insufficient data

            # Rosenstein algorithm for largest Lyapunov exponent
            N = len(data)
            m = min(10, N // 10)  # Embedding dimension
            tau = 1  # Time delay
            dt = 1  # Time step

            # Reconstruct phase space
            embedded = LyapunovExponent._embed_data(data, m, tau)

            # Find nearest neighbors
            divergences = []
            for i in range(min(N - m * tau, max_time)):
                # Find nearest neighbor to point i (excluding temporal neighbors)
                distances = []
                for j in range(len(embedded)):
                    if abs(j - i) > m:  # Exclude temporal neighbors
                        dist = np.linalg.norm(embedded[i] - embedded[j])
                        distances.append((dist, j))

                if distances:
                    distances.sort()
                    nearest_dist, nearest_idx = distances[0]

                    # Track divergence
                    future_i = min(i + max_time, len(embedded) - 1)
                    future_j = min(nearest_idx + max_time, len(embedded) - 1)

                    if future_i < len(embedded) and future_j < len(embedded):
                        divergence = np.linalg.norm(embedded[future_i] - embedded[future_j])
                        if divergence > 0:
                            divergences.append(np.log(divergence / nearest_dist) / (dt * max_time))

            if divergences:
                return np.mean(divergences)
            else:
                return 0.0

        except Exception as e:
            logger.error(f"Error calculating Lyapunov exponent: {e}")
            return 0.0

    @staticmethod
    def _embed_data(data: np.ndarray, dimension: int, delay: int) -> np.ndarray:
        """Embed time series data in phase space"""
        N = len(data)
        embedded = np.zeros((N - (dimension - 1) * delay, dimension))

        for i in range(dimension):
            embedded[:, i] = data[i * delay:N - (dimension - 1 - i) * delay]

        return embedded


class CorrelationDimension:
    """Calculate correlation dimension for fractal analysis"""

    @staticmethod
    def calculate_correlation_dimension(data: np.ndarray, max_dimension: int = 10,
                                      scales: Optional[np.ndarray] = None) -> float:
        """Calculate correlation dimension using Grassberger-Procaccia algorithm"""
        try:
            if scales is None:
                scales = np.logspace(-3, 0, 20)

            # Embed data in different dimensions
            dimensions = range(2, min(max_dimension + 1, len(data) // 10))
            correlation_sums = []

            for dim in dimensions:
                embedded = CorrelationDimension._embed_data(data, dim, 1)
                n_points = len(embedded)

                if n_points < 100:
                    continue

                # Calculate correlation sum for different scales
                corr_sums = []
                for scale in scales:
                    count = 0
                    total_pairs = 0

                    # Sample pairs for efficiency
                    sample_size = min(1000, n_points * (n_points - 1) // 2)
                    indices_i = np.random.choice(n_points, sample_size, replace=True)
                    indices_j = np.random.choice(n_points, sample_size, replace=True)

                    for i, j in zip(indices_i, indices_j):
                        if i != j:
                            distance = np.linalg.norm(embedded[i] - embedded[j])
                            if distance < scale:
                                count += 1
                            total_pairs += 1

                    if total_pairs > 0:
                        corr_sums.append(count / total_pairs)

                correlation_sums.append(corr_sums)

            # Find scaling region and calculate slope
            if correlation_sums:
                # Use log-log plot to find scaling region
                log_scales = np.log(scales)
                log_correlations = [np.log(c) for c in correlation_sums[-1]]  # Use highest dimension

                # Find linear region
                valid_indices = [i for i in range(len(log_correlations))
                               if not np.isinf(log_correlations[i]) and not np.isnan(log_correlations[i])]

                if len(valid_indices) > 5:
                    slope, _ = np.polyfit([log_scales[i] for i in valid_indices],
                                        [log_correlations[i] for i in valid_indices], 1)
                    return max(0, min(10, slope))  # Constrain to reasonable range

            return 1.0  # Default for non-fractal systems

        except Exception as e:
            logger.error(f"Error calculating correlation dimension: {e}")
            return 1.0

    @staticmethod
    def _embed_data(data: np.ndarray, dimension: int, delay: int) -> np.ndarray:
        """Embed time series data"""
        N = len(data)
        embedded = np.zeros((N - (dimension - 1) * delay, dimension))

        for i in range(dimension):
            start_idx = i * delay
            end_idx = N - (dimension - 1 - i) * delay
            embedded[:, i] = data[start_idx:end_idx]

        return embedded


class RecurrenceAnalysis:
    """Perform recurrence analysis for chaos detection"""

    @staticmethod
    def calculate_recurrence_metrics(data: np.ndarray, embedding_dim: int = 3,
                                   delay: int = 1, threshold: Optional[float] = None) -> Dict[str, float]:
        """Calculate recurrence quantification analysis metrics"""
        try:
            # Embed the data
            embedded = RecurrenceAnalysis._embed_data(data, embedding_dim, delay)

            if len(embedded) < 10:
                return {"recurrence_rate": 0.0, "determinism": 0.0, "laminarity": 0.0, "entropy": 0.0}

            # Calculate distance matrix
            n = len(embedded)
            distance_matrix = np.zeros((n, n))

            for i in range(n):
                for j in range(i, n):
                    dist = np.linalg.norm(embedded[i] - embedded[j])
                    distance_matrix[i, j] = dist
                    distance_matrix[j, i] = dist

            # Set threshold if not provided
            if threshold is None:
                threshold = np.percentile(distance_matrix, 10)  # 10th percentile

            # Create recurrence plot
            recurrence_plot = distance_matrix < threshold

            # Calculate recurrence rate
            recurrence_rate = np.sum(recurrence_plot) / (n * n)

            # Calculate determinism (percentage of recurrence points that form diagonal lines)
            determinism = RecurrenceAnalysis._calculate_determinism(recurrence_plot)

            # Calculate laminarity (percentage of recurrence points that form vertical lines)
            laminarity = RecurrenceAnalysis._calculate_laminarity(recurrence_plot)

            # Calculate entropy
            entropy = RecurrenceAnalysis._calculate_entropy(recurrence_plot)

            return {
                "recurrence_rate": recurrence_rate,
                "determinism": determinism,
                "laminarity": laminarity,
                "entropy": entropy
            }

        except Exception as e:
            logger.error(f"Error calculating recurrence metrics: {e}")
            return {"recurrence_rate": 0.0, "determinism": 0.0, "laminarity": 0.0, "entropy": 0.0}

    @staticmethod
    def _embed_data(data: np.ndarray, dimension: int, delay: int) -> np.ndarray:
        """Embed time series data"""
        N = len(data)
        embedded = np.zeros((N - (dimension - 1) * delay, dimension))

        for i in range(dimension):
            embedded[:, i] = data[i * delay:N - (dimension - 1 - i) * delay]

        return embedded

    @staticmethod
    def _calculate_determinism(recurrence_plot: np.ndarray, min_line_length: int = 2) -> float:
        """Calculate determinism from diagonal line structures"""
        n = recurrence_plot.shape[0]
        diagonal_lines = []

        for offset in range(-n + 1, n):
            diagonal = np.diagonal(recurrence_plot, offset)
            line_lengths = RecurrenceAnalysis._find_line_lengths(diagonal, True)
            diagonal_lines.extend([l for l in line_lengths if l >= min_line_length])

        if diagonal_lines:
            points_in_lines = sum(l for l in diagonal_lines)
            total_points = np.sum(recurrence_plot)
            return points_in_lines / total_points if total_points > 0 else 0.0

        return 0.0

    @staticmethod
    def _calculate_laminarity(recurrence_plot: np.ndarray, min_line_length: int = 2) -> float:
        """Calculate laminarity from vertical line structures"""
        vertical_lines = []

        for col in range(recurrence_plot.shape[1]):
            column = recurrence_plot[:, col]
            line_lengths = RecurrenceAnalysis._find_line_lengths(column, True)
            vertical_lines.extend([l for l in line_lengths if l >= min_line_length])

        if vertical_lines:
            points_in_lines = sum(l for l in vertical_lines)
            total_points = np.sum(recurrence_plot)
            return points_in_lines / total_points if total_points > 0 else 0.0

        return 0.0

    @staticmethod
    def _find_line_lengths(sequence: np.ndarray, value: bool) -> List[int]:
        """Find lengths of consecutive true values in sequence"""
        lengths = []
        current_length = 0

        for val in sequence:
            if val == value:
                current_length += 1
            else:
                if current_length > 0:
                    lengths.append(current_length)
                current_length = 0

        if current_length > 0:
            lengths.append(current_length)

        return lengths

    @staticmethod
    def _calculate_entropy(recurrence_plot: np.ndarray) -> float:
        """Calculate Shannon entropy of recurrence plot"""
        # Create histogram of diagonal line lengths
        n = recurrence_plot.shape[0]
        line_lengths = []

        for offset in range(-n + 1, n):
            diagonal = np.diagonal(recurrence_plot, offset)
            lengths = RecurrenceAnalysis._find_line_lengths(diagonal, True)
            line_lengths.extend(lengths)

        if line_lengths:
            # Calculate probability distribution
            unique_lengths, counts = np.unique(line_lengths, return_counts=True)
            probabilities = counts / np.sum(counts)

            # Calculate Shannon entropy
            entropy = -np.sum(probabilities * np.log(probabilities + 1e-10))
            return entropy

        return 0.0


class AttractorDetector:
    """Detect and analyze attractors in dynamical systems"""

    @staticmethod
    def detect_attractors(data: np.ndarray, embedding_dim: int = 3) -> List[Attractor]:
        """Detect attractors in the phase space"""
        attractors = []

        try:
            # Embed data in phase space
            embedded = AttractorDetector._embed_data(data, embedding_dim, 1)

            if len(embedded) < 50:
                return attractors

            # Find clusters in phase space (potential attractors)
            clustering = DBSCAN(eps=np.std(embedded) * 0.1, min_samples=10)
            labels = clustering.fit_predict(embedded)

            # Analyze each cluster
            for label in np.unique(labels):
                if label == -1:  # Noise points
                    continue

                cluster_points = embedded[labels == label]
                center = np.mean(cluster_points, axis=0)
                radius = np.max(np.linalg.norm(cluster_points - center, axis=1))

                # Determine attractor type
                attractor_type = AttractorDetector._classify_attractor(cluster_points)

                # Calculate stability
                stability = AttractorDetector._calculate_stability(cluster_points)

                attractor = Attractor(
                    attractor_id=f"attractor_{label}_{datetime.now().timestamp()}",
                    attractor_type=attractor_type,
                    center=center.tolist(),
                    radius=float(radius),
                    strength=len(cluster_points) / len(embedded),
                    basin_of_attraction=[],  # Would need more analysis
                    dimension=embedding_dim,
                    stability=stability
                )

                attractors.append(attractor)

        except Exception as e:
            logger.error(f"Error detecting attractors: {e}")

        return attractors

    @staticmethod
    def _embed_data(data: np.ndarray, dimension: int, delay: int) -> np.ndarray:
        """Embed time series data"""
        N = len(data)
        embedded = np.zeros((N - (dimension - 1) * delay, dimension))

        for i in range(dimension):
            embedded[:, i] = data[i * delay:N - (dimension - 1 - i) * delay]

        return embedded

    @staticmethod
    def _classify_attractor(points: np.ndarray) -> AttractorType:
        """Classify the type of attractor based on point distribution"""
        if len(points) < 10:
            return AttractorType.FIXED_POINT

        # Calculate variance in each dimension
        variances = np.var(points, axis=0)

        # Fixed point: low variance in all dimensions
        if np.all(variances < 0.01):
            return AttractorType.FIXED_POINT

        # Limit cycle: periodic behavior
        # Check for periodicity by looking at distances from center
        center = np.mean(points, axis=0)
        distances = np.linalg.norm(points - center, axis=1)
        distance_var = np.var(distances)

        if distance_var < 0.1 * np.mean(distances):
            return AttractorType.LIMIT_CYCLE

        # Strange attractor: fractal structure
        # This is a simplified check - in practice would use more sophisticated methods
        return AttractorType.STRANGE_ATTRACTOR

    @staticmethod
    def _calculate_stability(points: np.ndarray) -> float:
        """Calculate stability measure for attractor"""
        if len(points) < 2:
            return 0.0

        # Calculate how tightly clustered the points are
        center = np.mean(points, axis=0)
        avg_distance = np.mean(np.linalg.norm(points - center, axis=1))
        max_distance = np.max(np.linalg.norm(points - center, axis=1))

        if max_distance > 0:
            stability = 1.0 - (avg_distance / max_distance)
        else:
            stability = 1.0

        return max(0.0, min(1.0, stability))


class ChaosAnalyzer:
    """Main chaos analysis system"""

    def __init__(self):
        self.lyapunov_calculator = LyapunovExponent()
        self.correlation_dim_calculator = CorrelationDimension()
        self.recurrence_analyzer = RecurrenceAnalysis()
        self.attractor_detector = AttractorDetector()
        self.analyses: List[ChaosAnalysis] = []

    async def analyze_system(self, system_name: str, data: np.ndarray,
                           timestamps: List[datetime]) -> ChaosAnalysis:
        """Perform comprehensive chaos analysis on a system"""
        try:
            logger.info(f"Starting chaos analysis for system: {system_name}")

            if len(data) != len(timestamps):
                raise ValueError("Data and timestamps must have same length")

            # Calculate chaos metrics
            metrics = await self._calculate_chaos_metrics(data)

            # Determine complexity level
            complexity_level = self._classify_complexity(metrics)

            # Determine chaos type
            chaos_type = self._identify_chaos_type(metrics)

            # Detect attractors
            attractors = self.attractor_detector.detect_attractors(data)

            # Create phase space reconstruction
            phase_space = self._create_phase_space(data)

            # Create recurrence plot
            recurrence_plot = self._create_recurrence_plot(data)

            # Calculate predictability horizon
            predictability_horizon = self._calculate_predictability_horizon(metrics)

            # Generate recommendations
            recommendations = self._generate_recommendations(metrics, complexity_level, chaos_type)

            # Create analysis object
            analysis = ChaosAnalysis(
                analysis_id=f"chaos_{system_name}_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                system_name=system_name,
                data_series=data,
                time_series=timestamps,
                complexity_level=complexity_level,
                chaos_type=chaos_type,
                metrics=metrics,
                attractors=attractors,
                bifurcations=[],  # Would need parameter variation analysis
                phase_space=phase_space,
                recurrence_plot=recurrence_plot,
                predictability_horizon=predictability_horizon,
                recommendations=recommendations
            )

            self.analyses.append(analysis)

            # Keep analyses manageable
            if len(self.analyses) > 100:
                self.analyses = self.analyses[-50:]

            logger.info(f"Chaos analysis completed for {system_name}: {complexity_level.value}")
            return analysis

        except Exception as e:
            logger.error(f"Error in chaos analysis: {e}")
            raise

    async def _calculate_chaos_metrics(self, data: np.ndarray) -> ChaosMetrics:
        """Calculate all chaos metrics"""
        # Lyapunov exponent
        lyapunov_exp = self.lyapunov_calculator.calculate_largest_lyapunov(data)

        # Correlation dimension
        corr_dim = self.correlation_dim_calculator.calculate_correlation_dimension(data)

        # Recurrence metrics
        recurrence_metrics = self.recurrence_analyzer.calculate_recurrence_metrics(data)

        # Approximate entropy
        entropy = self._calculate_sample_entropy(data)

        # Hurst exponent
        hurst_exp = self._calculate_hurst_exponent(data)

        # Detrended fluctuation analysis
        dfa = self._calculate_dfa(data)

        # Predictability (inverse of chaos)
        predictability = max(0, 1 - max(0, lyapunov_exp))

        # Complexity score (combination of metrics)
        complexity_score = self._calculate_complexity_score(lyapunov_exp, corr_dim, entropy, hurst_exp)

        return ChaosMetrics(
            lyapunov_exponent=lyapunov_exp,
            correlation_dimension=corr_dim,
            entropy=entropy,
            hurst_exponent=hurst_exp,
            detrended_fluctuation=dfa,
            recurrence_rate=recurrence_metrics["recurrence_rate"],
            determinism=recurrence_metrics["determinism"],
            laminarity=recurrence_metrics["laminarity"],
            predictability=predictability,
            complexity_score=complexity_score
        )

    def _classify_complexity(self, metrics: ChaosMetrics) -> SystemComplexity:
        """Classify system complexity based on metrics"""
        # Use a combination of metrics to classify complexity
        lyapunov = metrics.lyapunov_exponent
        corr_dim = metrics.correlation_dimension
        determinism = metrics.determinism

        # Simple classification rules
        if lyapunov > 0.1 and corr_dim > 2.5:
            return SystemComplexity.CHAOTIC
        elif lyapunov > 0.01 and determinism < 0.5:
            return SystemComplexity.COMPLEX
        elif corr_dim > 1.5:
            return SystemComplexity.COMPLICATED
        elif determinism > 0.8:
            return SystemComplexity.SIMPLE
        else:
            return SystemComplexity.RANDOM

    def _identify_chaos_type(self, metrics: ChaosMetrics) -> Optional[ChaosType]:
        """Identify specific type of chaos"""
        lyapunov = metrics.lyapunov_exponent
        entropy = metrics.entropy
        determinism = metrics.determinism

        if lyapunov > 0.1 and determinism < 0.3:
            return ChaosType.DETERMINISTIC_CHAOS
        elif entropy > 2.0 and determinism < 0.5:
            return ChaosType.STOCHASTIC_CHAOS
        elif lyapunov > 0.01 and lyapunov < 0.1:
            return ChaosType.EDGE_OF_CHAOS
        elif metrics.correlation_dimension > 3.0:
            return ChaosType.STRANGE_ATTRACTOR
        else:
            return None

    def _create_phase_space(self, data: np.ndarray, embedding_dim: int = 3) -> np.ndarray:
        """Create phase space reconstruction"""
        try:
            if len(data) < embedding_dim * 2:
                return np.array([])

            embedded = np.zeros((len(data) - embedding_dim + 1, embedding_dim))
            for i in range(embedding_dim):
                embedded[:, i] = data[i:len(data) - embedding_dim + 1 + i]

            return embedded
        except Exception as e:
            logger.error(f"Error creating phase space: {e}")
            return np.array([])

    def _create_recurrence_plot(self, data: np.ndarray) -> np.ndarray:
        """Create recurrence plot"""
        try:
            n = len(data)
            if n < 10:
                return np.zeros((n, n))

            # Simple recurrence plot based on distance threshold
            threshold = np.std(data) * 0.1
            recurrence_plot = np.zeros((n, n))

            for i in range(n):
                for j in range(n):
                    if abs(data[i] - data[j]) < threshold:
                        recurrence_plot[i, j] = 1

            return recurrence_plot
        except Exception as e:
            logger.error(f"Error creating recurrence plot: {e}")
            return np.zeros((len(data), len(data)))

    def _calculate_predictability_horizon(self, metrics: ChaosMetrics) -> float:
        """Calculate how far into the future the system is predictable"""
        if metrics.lyapunov_exponent <= 0:
            return float('inf')  # Fully predictable

        # Predictability horizon is inversely related to Lyapunov exponent
        horizon = 1.0 / metrics.lyapunov_exponent
        return min(horizon, 1000)  # Cap at reasonable value

    def _calculate_sample_entropy(self, data: np.ndarray, m: int = 2, r: float = None) -> float:
        """Calculate sample entropy"""
        try:
            if r is None:
                r = 0.2 * np.std(data)

            N = len(data)
            if N < m + 1:
                return 0.0

            def _maxdist(xi, xj, m):
                return max([abs(ua - va) for ua, va in zip(xi, xj)])

            def _phi(m):
                patterns = np.array([data[i:i + m] for i in range(N - m + 1)])
                C = np.zeros(N - m + 1)

                for i in range(N - m + 1):
                    template = patterns[i]
                    for j in range(N - m + 1):
                        if i != j:
                            if _maxdist(template, patterns[j], m) <= r:
                                C[i] += 1.0

                phi = (1.0 / (N - m + 1)) * np.sum(np.log(C / (N - m + 1.0)))
                return phi

            return _phi(m) - _phi(m + 1)

        except Exception as e:
            logger.error(f"Error calculating sample entropy: {e}")
            return 0.0

    def _calculate_hurst_exponent(self, data: np.ndarray) -> float:
        """Calculate Hurst exponent"""
        try:
            lags = range(2, min(20, len(data) // 2))
            tau = [np.sqrt(np.std(np.subtract(data[lag:], data[:-lag]))) for lag in lags]

            # Linear fit in log-log plot
            poly = np.polyfit(np.log(lags), np.log(tau), 1)
            hurst = poly[0] * 2.0

            return max(0, min(1, hurst))

        except Exception as e:
            logger.error(f"Error calculating Hurst exponent: {e}")
            return 0.5

    def _calculate_dfa(self, data: np.ndarray) -> float:
        """Calculate detrended fluctuation analysis"""
        try:
            n = len(data)
            if n < 10:
                return 0.0

            # Integrate the series
            integrated = np.cumsum(data - np.mean(data))

            # Calculate fluctuation for different window sizes
            window_sizes = range(4, min(n // 4, 20))
            fluctuations = []

            for window in window_sizes:
                # Divide into windows
                n_windows = n // window
                if n_windows < 2:
                    continue

                rms_values = []
                for i in range(n_windows):
                    start = i * window
                    end = start + window
                    segment = integrated[start:end]

                    # Fit linear trend
                    x = np.arange(window)
                    fit = np.polyfit(x, segment, 1)
                    trend = np.polyval(fit, x)

                    # Calculate RMS fluctuation
                    rms = np.sqrt(np.mean((segment - trend) ** 2))
                    rms_values.append(rms)

                if rms_values:
                    fluctuations.append(np.mean(rms_values))

            if fluctuations:
                # Calculate scaling exponent
                log_windows = np.log(window_sizes[:len(fluctuations)])
                log_fluctuations = np.log(fluctuations)
                slope, _ = np.polyfit(log_windows, log_fluctuations, 1)
                return slope

            return 0.5

        except Exception as e:
            logger.error(f"Error calculating DFA: {e}")
            return 0.5

    def _calculate_complexity_score(self, lyapunov: float, corr_dim: float,
                                   entropy: float, hurst: float) -> float:
        """Calculate overall complexity score"""
        # Normalize metrics to 0-1 range
        lyapunov_norm = min(1.0, lyapunov * 10)  # Lyapunov > 0.1 indicates chaos
        corr_dim_norm = min(1.0, corr_dim / 5.0)  # Correlation dimension > 5 is very complex
        entropy_norm = min(1.0, entropy / 3.0)    # Entropy > 3 is very complex
        hurst_norm = abs(hurst - 0.5) * 2       # Deviation from 0.5 indicates complexity

        # Weighted average
        complexity = (lyapunov_norm * 0.3 + corr_dim_norm * 0.25 +
                     entropy_norm * 0.25 + hurst_norm * 0.2)

        return complexity

    def _generate_recommendations(self, metrics: ChaosMetrics,
                                complexity: SystemComplexity,
                                chaos_type: Optional[ChaosType]) -> List[str]:
        """Generate recommendations based on chaos analysis"""
        recommendations = []

        if complexity == SystemComplexity.CHAOTIC:
            recommendations.extend([
                "System exhibits chaotic behavior - long-term prediction is impossible",
                "Focus on statistical properties rather than precise forecasting",
                "Implement robust control mechanisms to manage sensitivity to initial conditions",
                "Consider early warning systems for critical transitions"
            ])
        elif complexity == SystemComplexity.COMPLEX:
            recommendations.extend([
                "System shows complex adaptive behavior - monitor for emergent patterns",
                "Use ensemble forecasting approaches to account for uncertainty",
                "Identify and leverage self-organizing patterns",
                "Implement adaptive management strategies"
            ])
        elif complexity == SystemComplexity.EDGE_OF_CHAOS:
            recommendations.extend([
                "System operates at edge of chaos - optimal for innovation and adaptation",
                "Maintain balance between stability and flexibility",
                "Monitor for bifurcation points and critical transitions",
                "Exploit system's capacity for creative adaptation"
            ])
        elif complexity == SystemComplexity.SIMPLE:
            recommendations.extend([
                "System shows predictable behavior - traditional forecasting methods appropriate",
                "Focus on optimization and efficiency improvements",
                "Implement precise control mechanisms",
                "Monitor for signs of increasing complexity"
            ])

        # Specific recommendations based on metrics
        if metrics.lyapunov_exponent > 0.1:
            recommendations.append("High sensitivity to initial conditions detected - small perturbations can lead to large changes")

        if metrics.predictability < 0.3:
            recommendations.append("Low predictability - emphasize risk management over precise forecasting")

        if metrics.hurst_exponent > 0.65:
            recommendations.append("Persistent trends detected - current trends likely to continue")
        elif metrics.hurst_exponent < 0.35:
            recommendations.append("Anti-persistent behavior detected - trends likely to reverse")

        return recommendations[:5]  # Return top 5 recommendations

    def get_analysis_summary(self, system_name: str) -> Optional[Dict[str, Any]]:
        """Get summary of chaos analysis for a system"""
        for analysis in self.analyses:
            if analysis.system_name == system_name:
                return {
                    "system_name": system_name,
                    "analysis_timestamp": analysis.timestamp.isoformat(),
                    "complexity_level": analysis.complexity_level.value,
                    "chaos_type": analysis.chaos_type.value if analysis.chaos_type else None,
                    "lyapunov_exponent": analysis.metrics.lyapunov_exponent,
                    "correlation_dimension": analysis.metrics.correlation_dimension,
                    "predictability": analysis.metrics.predictability,
                    "complexity_score": analysis.metrics.complexity_score,
                    "predictability_horizon": analysis.predictability_horizon,
                    "num_attractors": len(analysis.attractors),
                    "top_recommendations": analysis.recommendations[:3]
                }
        return None


# Singleton instance
_chaos_analyzer = None

def get_chaos_analyzer() -> ChaosAnalyzer:
    """Get the singleton chaos analyzer instance"""
    global _chaos_analyzer
    if _chaos_analyzer is None:
        _chaos_analyzer = ChaosAnalyzer()
    return _chaos_analyzer


async def main():
    """Example usage of chaos theory analysis"""
    analyzer = get_chaos_analyzer()

    # Generate sample data from different systems
    systems = {
        "logistic_map": [],
        "lorenz_system": [],
        "random_walk": [],
        "sine_wave": []
    }

    # Generate time series
    np.random.seed(42)
    time_points = np.linspace(0, 50, 1000)

    # Logistic map (chaotic)
    x = 0.5
    r = 3.9  # Chaotic parameter
    for _ in range(1000):
        x = r * x * (1 - x)
        systems["logistic_map"].append(x)

    # Simulated Lorenz-like data
    t = time_points
    sigma, rho, beta = 10, 28, 8/3
    dt = 0.01
    x, y, z = 1, 1, 1
    for _ in range(1000):
        dx = sigma * (y - x) * dt
        dy = (x * (rho - z) - y) * dt
        dz = (x * y - beta * z) * dt
        x, y, z = x + dx, y + dy, z + dz
        systems["lorenz_system"].append(x)

    # Random walk
    steps = np.random.randn(1000)
    systems["random_walk"] = np.cumsum(steps).tolist()

    # Sine wave (periodic)
    systems["sine_wave"] = (3 * np.sin(2 * np.pi * 0.1 * time_points)).tolist()

    # Analyze each system
    timestamps = [datetime.now() - timedelta(minutes=i) for i in range(1000, 0, -1)]

    for system_name, data in systems.items():
        print(f"\nAnalyzing system: {system_name}")
        print("-" * 40)

        try:
            analysis = await analyzer.analyze_system(system_name, np.array(data), timestamps)

            print(f"Complexity Level: {analysis.complexity_level.value}")
            print(f"Chaos Type: {analysis.chaos_type.value if analysis.chaos_type else 'None'}")
            print(f"Lyapunov Exponent: {analysis.metrics.lyapunov_exponent:.4f}")
            print(f"Correlation Dimension: {analysis.metrics.correlation_dimension:.2f}")
            print(f"Predictability: {analysis.metrics.predictability:.2f}")
            print(f"Complexity Score: {analysis.metrics.complexity_score:.2f}")
            print(f"Predictability Horizon: {analysis.predictability_horizon:.2f} time units")
            print(f"Number of Attractors: {len(analysis.attractors)}")

            if analysis.recommendations:
                print("\nTop Recommendations:")
                for rec in analysis.recommendations[:3]:
                    print(f"  • {rec}")

        except Exception as e:
            print(f"Error analyzing {system_name}: {e}")


if __name__ == "__main__":
    asyncio.run(main())