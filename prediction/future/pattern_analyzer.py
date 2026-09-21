#!/usr/bin/env python3
"""
Pattern Analyzer - Advanced pattern recognition across multiple data sources
Detects recurring patterns, anomalies, and correlations in game world data
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
import json
import asyncio
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import logging

try:
    from scipy import stats
    from scipy.signal import find_peaks, correlate
    from scipy.fft import fft, ifft, fftfreq
    from sklearn.cluster import DBSCAN, KMeans
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score
except ImportError:
    print("Warning: scipy/sklearn not available. Using simplified pattern analysis")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns that can be detected"""
    SEASONAL = "seasonal"
    CYCLICAL = "cyclical"
    TREND = "trend"
    ANOMALY = "anomaly"
    CORRELATION = "correlation"
    BURST = "burst"
    DECAY = "decay"
    OSCILLATION = "oscillation"
    PHASE_SHIFT = "phase_shift"


@dataclass
class Pattern:
    """Represents a detected pattern"""
    pattern_id: str
    pattern_type: PatternType
    confidence: float
    start_time: datetime
    end_time: datetime
    data_source: str
    parameters: Dict[str, Any]
    strength: float
    frequency: Optional[float] = None
    amplitude: Optional[float] = None
    phase: Optional[float] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Anomaly:
    """Represents a detected anomaly"""
    anomaly_id: str
    timestamp: datetime
    data_source: str
    anomaly_score: float
    severity: str  # low, medium, high, critical
    description: str
    affected_metrics: List[str]
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Correlation:
    """Represents a correlation between data sources"""
    correlation_id: str
    source_1: str
    source_2: str
    correlation_coefficient: float
    p_value: float
    lag: Optional[int] = None
    correlation_type: str = "pearson"  # pearson, spearman, kendall
    time_window: Optional[Tuple[datetime, datetime]] = None


class PatternDetector:
    """Base class for pattern detection algorithms"""

    def __init__(self, name: str):
        self.name = name
        self.min_pattern_length = 10
        self.confidence_threshold = 0.7

    def detect(self, data: np.ndarray, timestamps: List[datetime]) -> List[Pattern]:
        """Detect patterns in the provided data"""
        raise NotImplementedError

    def calculate_confidence(self, pattern_data: np.ndarray) -> float:
        """Calculate confidence score for detected pattern"""
        return 0.5


class SeasonalDetector(PatternDetector):
    """Detects seasonal patterns in time series data"""

    def __init__(self):
        super().__init__("seasonal_detector")
        self.seasonal_periods = [24, 168, 720]  # hours, days, weeks

    def detect(self, data: np.ndarray, timestamps: List[datetime]) -> List[Pattern]:
        """Detect seasonal patterns"""
        patterns = []

        if len(data) < self.min_pattern_length:
            return patterns

        try:
            # Decompose time series
            decomposition = self._decompose_series(data, timestamps)

            if decomposition is not None:
                trend, seasonal, residual = decomposition

                # Analyze seasonal component
                seasonal_strength = np.std(seasonal) / (np.std(data) + 1e-6)

                if seasonal_strength > 0.3:  # Significant seasonal component
                    # Find dominant frequency
                    fft_result = fft(seasonal)
                    frequencies = fftfreq(len(seasonal))
                    dominant_freq_idx = np.argmax(np.abs(fft_result[1:len(fft_result)//2])) + 1
                    dominant_freq = frequencies[dominant_freq_idx]

                    # Calculate period
                    if dominant_freq != 0:
                        period = 1.0 / abs(dominant_freq)
                        confidence = min(seasonal_strength, 0.95)

                        pattern = Pattern(
                            pattern_id=f"seasonal_{datetime.now().timestamp()}",
                            pattern_type=PatternType.SEASONAL,
                            confidence=confidence,
                            start_time=timestamps[0],
                            end_time=timestamps[-1],
                            data_source="unknown",
                            parameters={
                                "period": period,
                                "strength": seasonal_strength,
                                "dominant_frequency": dominant_freq
                            },
                            strength=seasonal_strength,
                            frequency=dominant_freq,
                            amplitude=np.max(np.abs(seasonal)),
                            duration=(timestamps[-1] - timestamps[0]).total_seconds()
                        )

                        patterns.append(pattern)

        except Exception as e:
            logger.error(f"Error in seasonal detection: {e}")

        return patterns

    def _decompose_series(self, data: np.ndarray, timestamps: List[datetime]) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        """Decompose time series into trend, seasonal, and residual components"""
        try:
            # Simple moving average for trend
            window = min(len(data) // 4, 30)
            if window < 3:
                return None

            trend = pd.Series(data).rolling(window=window, center=True).mean().fillna(method='bfill').fillna(method='ffill').values
            detrended = data - trend

            # Simple seasonal component using periodicity
            seasonal = np.zeros_like(data)
            for period in [24, 168, 720]:  # Try common periods
                if len(data) >= period * 2:
                    for i in range(period):
                        indices = np.arange(i, len(data), period)
                        if len(indices) > 0:
                            seasonal_values = detrended[indices]
                            seasonal_mean = np.mean(seasonal_values)
                            seasonal[indices] = seasonal_mean

            residual = data - trend - seasonal

            return trend, seasonal, residual

        except Exception as e:
            logger.error(f"Error decomposing series: {e}")
            return None


class AnomalyDetector(PatternDetector):
    """Detects anomalies in time series data"""

    def __init__(self):
        super().__init__("anomaly_detector")
        self.z_score_threshold = 3.0
        self.iqr_threshold = 1.5

    def detect_anomalies(self, data: np.ndarray, timestamps: List[datetime], data_source: str = "unknown") -> List[Anomaly]:
        """Detect anomalies in the data"""
        anomalies = []

        if len(data) < 5:
            return anomalies

        try:
            # Z-score based detection
            z_scores = np.abs(stats.zscore(data))
            anomaly_indices = np.where(z_scores > self.z_score_threshold)[0]

            for idx in anomaly_indices:
                severity = self._calculate_severity(z_scores[idx])
                anomaly = Anomaly(
                    anomaly_id=f"anomaly_{data_source}_{timestamps[idx].timestamp()}",
                    timestamp=timestamps[idx],
                    data_source=data_source,
                    anomaly_score=z_scores[idx],
                    severity=severity,
                    description=f"Z-score anomaly detected: {z_scores[idx]:.2f}",
                    affected_metrics=[data_source],
                    context={
                        "value": data[idx],
                        "z_score": z_scores[idx],
                        "method": "z_score"
                    }
                )
                anomalies.append(anomaly)

            # IQR based detection
            q1, q3 = np.percentile(data, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - self.iqr_threshold * iqr
            upper_bound = q3 + self.iqr_threshold * iqr

            iqr_anomalies = np.where((data < lower_bound) | (data > upper_bound))[0]
            for idx in iqr_anomalies:
                # Avoid duplicates
                if idx not in anomaly_indices:
                    severity = self._calculate_severity(abs(data[idx] - np.median(data)) / iqr)
                    anomaly = Anomaly(
                        anomaly_id=f"anomaly_iqr_{data_source}_{timestamps[idx].timestamp()}",
                        timestamp=timestamps[idx],
                        data_source=data_source,
                        anomaly_score=abs(data[idx] - np.median(data)) / iqr,
                        severity=severity,
                        description=f"IQR anomaly detected: value={data[idx]:.2f}",
                        affected_metrics=[data_source],
                        context={
                            "value": data[idx],
                            "iqr": iqr,
                            "method": "iqr"
                        }
                    )
                    anomalies.append(anomaly)

        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")

        return anomalies

    def _calculate_severity(self, score: float) -> str:
        """Calculate severity level based on anomaly score"""
        if score > 5.0:
            return "critical"
        elif score > 4.0:
            return "high"
        elif score > 3.0:
            return "medium"
        else:
            return "low"


class CorrelationAnalyzer:
    """Analyzes correlations between different data sources"""

    def __init__(self):
        self.correlation_cache = {}
        self.lag_range = 50  # Maximum lag to check

    def analyze_correlations(self, data_dict: Dict[str, Tuple[np.ndarray, List[datetime]]]) -> List[Correlation]:
        """Analyze correlations between all data sources"""
        correlations = []
        sources = list(data_dict.keys())

        for i, source_1 in enumerate(sources):
            for source_2 in sources[i+1:]:
                try:
                    correlation = self._calculate_correlation(
                        source_1, data_dict[source_1],
                        source_2, data_dict[source_2]
                    )
                    if correlation:
                        correlations.append(correlation)
                except Exception as e:
                    logger.error(f"Error calculating correlation between {source_1} and {source_2}: {e}")

        return correlations

    def _calculate_correlation(self, source_1: str, data_1: Tuple[np.ndarray, List[datetime]],
                             source_2: str, data_2: Tuple[np.ndarray, List[datetime]]) -> Optional[Correlation]:
        """Calculate correlation between two data sources"""
        try:
            values_1, timestamps_1 = data_1
            values_2, timestamps_2 = data_2

            # Align data by timestamps
            aligned_values = self._align_time_series(values_1, timestamps_1, values_2, timestamps_2)
            if aligned_values is None:
                return None

            aligned_1, aligned_2 = aligned_values

            if len(aligned_1) < 10:
                return None

            # Calculate Pearson correlation
            correlation_coeff, p_value = stats.pearsonr(aligned_1, aligned_2)

            # Check for lagged correlation
            best_correlation = correlation_coeff
            best_lag = 0

            for lag in range(1, min(self.lag_range, len(aligned_1) // 2)):
                if len(aligned_1) > lag:
                    lagged_correlation, lagged_p = stats.pearsonr(aligned_1[:-lag], aligned_2[lag:])
                    if abs(lagged_correlation) > abs(best_correlation):
                        best_correlation = lagged_correlation
                        best_lag = lag

            # Only return significant correlations
            if abs(best_correlation) > 0.3 and p_value < 0.05:
                correlation = Correlation(
                    correlation_id=f"corr_{source_1}_{source_2}_{datetime.now().timestamp()}",
                    source_1=source_1,
                    source_2=source_2,
                    correlation_coefficient=best_correlation,
                    p_value=p_value,
                    lag=best_lag if best_lag != 0 else None,
                    correlation_type="pearson",
                    time_window=(timestamps_1[0], timestamps_1[-1])
                )
                return correlation

        except Exception as e:
            logger.error(f"Error in correlation calculation: {e}")

        return None

    def _align_time_series(self, values_1: np.ndarray, timestamps_1: List[datetime],
                          values_2: np.ndarray, timestamps_2: List[datetime]) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Align two time series by timestamps"""
        try:
            # Convert to pandas for easier alignment
            df1 = pd.DataFrame({'timestamp': timestamps_1, 'value': values_1})
            df2 = pd.DataFrame({'timestamp': timestamps_2, 'value': values_2})

            # Merge on timestamp with nearest matching
            merged = pd.merge_asof(df1.sort_values('timestamp'),
                                 df2.sort_values('timestamp'),
                                 on='timestamp',
                                 direction='nearest',
                                 tolerance=pd.Timedelta('1 hour'))

            # Remove rows where no match was found
            merged = merged.dropna()

            if len(merged) < 10:
                return None

            return merged['value_x'].values, merged['value_y'].values

        except Exception as e:
            logger.error(f"Error aligning time series: {e}")
            return None


class CycleDetector(PatternDetector):
    """Detects cyclical patterns in data"""

    def __init__(self):
        super().__init__("cycle_detector")
        self.min_cycle_length = 5
        self.max_cycle_length = 100

    def detect(self, data: np.ndarray, timestamps: List[datetime]) -> List[Pattern]:
        """Detect cyclical patterns"""
        patterns = []

        if len(data) < self.min_cycle_length * 2:
            return patterns

        try:
            # Find peaks in the data
            peaks, properties = find_peaks(data, distance=self.min_cycle_length)

            if len(peaks) >= 2:
                # Calculate periods between peaks
                periods = np.diff(peaks)
                if len(periods) > 0:
                    avg_period = np.mean(periods)
                    period_std = np.std(periods)

                    # Check if periods are consistent (low standard deviation)
                    consistency = 1.0 - (period_std / (avg_period + 1e-6))

                    if consistency > 0.7:  # Consistent cycle detected
                        amplitude = np.mean(data[peaks]) - np.mean(data)
                        confidence = min(consistency, 0.9)

                        pattern = Pattern(
                            pattern_id=f"cycle_{datetime.now().timestamp()}",
                            pattern_type=PatternType.CYCLICAL,
                            confidence=confidence,
                            start_time=timestamps[peaks[0]],
                            end_time=timestamps[peaks[-1]],
                            data_source="unknown",
                            parameters={
                                "period": avg_period,
                                "period_std": period_std,
                                "consistency": consistency,
                                "num_cycles": len(peaks) - 1
                            },
                            strength=consistency,
                            frequency=1.0 / avg_period if avg_period > 0 else None,
                            amplitude=amplitude,
                            duration=(timestamps[-1] - timestamps[0]).total_seconds()
                        )

                        patterns.append(pattern)

        except Exception as e:
            logger.error(f"Error in cycle detection: {e}")

        return patterns


class TrendDetector(PatternDetector):
    """Detects trends in time series data"""

    def __init__(self):
        super().__init__("trend_detector")

    def detect(self, data: np.ndarray, timestamps: List[datetime]) -> List[Pattern]:
        """Detect trend patterns"""
        patterns = []

        if len(data) < self.min_pattern_length:
            return patterns

        try:
            # Calculate trend using linear regression
            x = np.arange(len(data))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, data)

            # Determine trend significance
            if abs(r_value) > 0.5 and p_value < 0.05:  # Significant trend
                trend_direction = "increasing" if slope > 0 else "decreasing"
                confidence = abs(r_value)

                # Calculate trend strength
                trend_strength = abs(slope) / (np.std(data) + 1e-6)

                pattern = Pattern(
                    pattern_id=f"trend_{datetime.now().timestamp()}",
                    pattern_type=PatternType.TREND,
                    confidence=confidence,
                    start_time=timestamps[0],
                    end_time=timestamps[-1],
                    data_source="unknown",
                    parameters={
                        "slope": slope,
                        "intercept": intercept,
                        "r_squared": r_value ** 2,
                        "p_value": p_value,
                        "direction": trend_direction
                    },
                    strength=trend_strength,
                    frequency=None,
                    amplitude=abs(slope * len(data)),
                    duration=(timestamps[-1] - timestamps[0]).total_seconds(),
                    metadata={"trend_direction": trend_direction}
                )

                patterns.append(pattern)

        except Exception as e:
            logger.error(f"Error in trend detection: {e}")

        return patterns


class PatternAnalyzer:
    """Main pattern analysis orchestrator"""

    def __init__(self):
        self.detectors = {
            "seasonal": SeasonalDetector(),
            "cycle": CycleDetector(),
            "trend": TrendDetector()
        }
        self.anomaly_detector = AnomalyDetector()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.pattern_history: List[Pattern] = []
        self.anomaly_history: List[Anomaly] = []
        self.correlation_history: List[Correlation] = []
        self.data_cache: Dict[str, Tuple[np.ndarray, List[datetime]]] = {}

    async def analyze_data(self, data_dict: Dict[str, Tuple[np.ndarray, List[datetime]]]) -> Dict[str, List]:
        """Analyze all data sources for patterns, anomalies, and correlations"""
        results = {
            "patterns": [],
            "anomalies": [],
            "correlations": []
        }

        try:
            # Detect patterns in each data source
            for source, (data, timestamps) in data_dict.items():
                if len(data) < 10:
                    continue

                # Run all pattern detectors
                for detector_name, detector in self.detectors.items():
                    try:
                        patterns = detector.detect(data, timestamps)
                        for pattern in patterns:
                            pattern.data_source = source
                        results["patterns"].extend(patterns)
                    except Exception as e:
                        logger.error(f"Error in {detector_name} detector: {e}")

                # Detect anomalies
                try:
                    anomalies = self.anomaly_detector.detect_anomalies(data, timestamps, source)
                    results["anomalies"].extend(anomalies)
                except Exception as e:
                    logger.error(f"Error in anomaly detection: {e}")

            # Analyze correlations between data sources
            if len(data_dict) > 1:
                try:
                    correlations = self.correlation_analyzer.analyze_correlations(data_dict)
                    results["correlations"].extend(correlations)
                except Exception as e:
                    logger.error(f"Error in correlation analysis: {e}")

            # Store results in history
            self.pattern_history.extend(results["patterns"])
            self.anomaly_history.extend(results["anomalies"])
            self.correlation_history.extend(results["correlations"])

            # Limit history size
            self._limit_history_size()

            logger.info(f"Pattern analysis complete: {len(results['patterns'])} patterns, "
                       f"{len(results['anomalies'])} anomalies, {len(results['correlations'])} correlations")

        except Exception as e:
            logger.error(f"Error in pattern analysis: {e}")

        return results

    def get_pattern_summary(self, time_window: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get summary of detected patterns"""
        patterns = self._filter_by_time_window(self.pattern_history, time_window)
        anomalies = self._filter_by_time_window(self.anomaly_history, time_window)
        correlations = self._filter_by_time_window(self.correlation_history, time_window)

        summary = {
            "total_patterns": len(patterns),
            "total_anomalies": len(anomalies),
            "total_correlations": len(correlations),
            "pattern_types": defaultdict(int),
            "anomaly_severity": defaultdict(int),
            "high_correlations": 0,
            "recent_patterns": []
        }

        # Summarize pattern types
        for pattern in patterns:
            summary["pattern_types"][pattern.pattern_type.value] += 1

        # Summarize anomaly severity
        for anomaly in anomalies:
            summary["anomaly_severity"][anomaly.severity] += 1

        # Count high correlations
        for correlation in correlations:
            if abs(correlation.correlation_coefficient) > 0.7:
                summary["high_correlations"] += 1

        # Recent patterns
        recent_patterns = sorted(patterns, key=lambda p: p.start_time, reverse=True)[:5]
        summary["recent_patterns"] = [
            {
                "type": p.pattern_type.value,
                "source": p.data_source,
                "confidence": p.confidence,
                "strength": p.strength
            }
            for p in recent_patterns
        ]

        return dict(summary)

    def get_active_patterns(self, source: Optional[str] = None) -> List[Pattern]:
        """Get currently active patterns"""
        current_time = datetime.now()
        active_patterns = []

        for pattern in self.pattern_history:
            # Check if pattern is still active
            time_since_end = current_time - pattern.end_time
            if time_since_end.total_seconds() < 3600:  # Active if ended within last hour
                if source is None or pattern.data_source == source:
                    active_patterns.append(pattern)

        return sorted(active_patterns, key=lambda p: p.confidence, reverse=True)

    def get_critical_anomalies(self, hours: int = 24) -> List[Anomaly]:
        """Get critical anomalies from recent hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        critical_anomalies = []

        for anomaly in self.anomaly_history:
            if anomaly.timestamp > cutoff_time and anomaly.severity in ["high", "critical"]:
                critical_anomalies.append(anomaly)

        return sorted(critical_anomalies, key=lambda a: a.anomaly_score, reverse=True)

    def _filter_by_time_window(self, items: List, time_window: Optional[Tuple[datetime, datetime]]) -> List:
        """Filter items by time window"""
        if time_window is None:
            return items

        start_time, end_time = time_window
        filtered = []

        for item in items:
            if hasattr(item, 'timestamp'):
                if start_time <= item.timestamp <= end_time:
                    filtered.append(item)
            elif hasattr(item, 'start_time'):
                if (start_time <= item.start_time <= end_time or
                    start_time <= item.end_time <= end_time):
                    filtered.append(item)

        return filtered

    def _limit_history_size(self):
        """Limit the size of history to prevent memory issues"""
        max_items = 10000

        if len(self.pattern_history) > max_items:
            self.pattern_history = self.pattern_history[-max_items//2:]

        if len(self.anomaly_history) > max_items:
            self.anomaly_history = self.anomaly_history[-max_items//2:]

        if len(self.correlation_history) > max_items:
            self.correlation_history = self.correlation_history[-max_items//2:]


# Singleton instance
_pattern_analyzer = None

def get_pattern_analyzer() -> PatternAnalyzer:
    """Get the singleton pattern analyzer instance"""
    global _pattern_analyzer
    if _pattern_analyzer is None:
        _pattern_analyzer = PatternAnalyzer()
    return _pattern_analyzer


async def main():
    """Example usage of the pattern analyzer"""
    analyzer = get_pattern_analyzer()

    # Generate sample data with different patterns
    np.random.seed(42)
    timestamps = [datetime.now() - timedelta(hours=i) for i in range(100, 0, -1)]

    # Seasonal pattern
    seasonal_data = 10 * np.sin(np.arange(100) * 2 * np.pi / 24) + np.random.randn(100) * 2

    # Trend data
    trend_data = np.arange(100) * 0.5 + np.random.randn(100) * 3

    # Random data with anomalies
    anomaly_data = np.random.randn(100)
    anomaly_data[50] = 10  # Add anomaly
    anomaly_data[75] = -8  # Add another anomaly

    sample_data = {
        "player_activity": (seasonal_data, timestamps),
        "market_prices": (trend_data, timestamps),
        "system_errors": (anomaly_data, timestamps)
    }

    # Analyze patterns
    print("Analyzing patterns...")
    results = await analyzer.analyze_data(sample_data)

    print(f"\nFound {len(results['patterns'])} patterns:")
    for pattern in results['patterns']:
        print(f"  {pattern.pattern_type.value} in {pattern.data_source}: "
              f"confidence={pattern.confidence:.3f}, strength={pattern.strength:.3f}")

    print(f"\nFound {len(results['anomalies'])} anomalies:")
    for anomaly in results['anomalies'][:5]:  # Show first 5
        print(f"  {anomaly.severity} anomaly in {anomaly.data_source} at {anomaly.timestamp}: "
              f"score={anomaly.anomaly_score:.3f}")

    print(f"\nFound {len(results['correlations'])} correlations:")
    for corr in results['correlations']:
        print(f"  {corr.source_1} ↔ {corr.source_2}: "
              f"r={corr.correlation_coefficient:.3f}, p={corr.p_value:.3f}")

    # Get summary
    summary = analyzer.get_pattern_summary()
    print(f"\nPattern Summary:")
    print(f"  Total patterns: {summary['total_patterns']}")
    print(f"  Total anomalies: {summary['total_anomalies']}")
    print(f"  Total correlations: {summary['total_correlations']}")


if __name__ == "__main__":
    asyncio.run(main())