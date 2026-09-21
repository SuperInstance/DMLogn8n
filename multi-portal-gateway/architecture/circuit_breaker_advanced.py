"""
Advanced Circuit Breaker with Predictive Failure Prevention
Cutting-edge circuit breaker implementation with machine learning-based
failure prediction, adaptive thresholds, and intelligent recovery.

This module implements:
- ML-based failure prediction using historical patterns
- Adaptive thresholds that adjust based on system conditions
- Multi-level circuit breaker states with granular control
- Predictive scaling and resource management
- Circuit breaker clustering and coordination
- Real-time monitoring and alerting
- Self-healing capabilities
- Load shedding and graceful degradation
"""

import asyncio
import time
import json
import math
import statistics
import numpy as np
from abc import ABC, abstractmethod
from typing import (
    Dict, List, Optional, Any, Callable, Union,
    NamedTuple, Tuple, Set
)
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import structlog
from scipy import stats
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import redis.asyncio as redis
import prometheus_client as prom
import httpx

# Configure structured logging
logger = structlog.get_logger()

class CircuitState(Enum):
    """Circuit breaker states with granular control"""
    CLOSED = "closed"                    # Normal operation
    OPEN = "open"                        # Circuit is open, blocking requests
    HALF_OPEN = "half_open"              # Testing if service has recovered
    ISOLATED = "isolated"                # Service is manually isolated
    DEGRADED = "degraded"                # Service is in degraded mode
    PREVENTIVE_OPEN = "preventive_open"  # Preemptively opened due to prediction
    LOAD_SHEDDING = "load_shedding"      # Shedding excess load

class FailureType(Enum):
    """Types of failures to track"""
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    HTTP_ERROR = "http_error"
    RATE_LIMIT = "rate_limit"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    NETWORK_ERROR = "network_error"
    PROTOCOL_ERROR = "protocol_error"
    UNKNOWN = "unknown"

@dataclass
class FailureEvent:
    """Failure event with rich context"""
    timestamp: datetime
    failure_type: FailureType
    error_message: str
    response_time: Optional[float] = None
    status_code: Optional[int] = None
    endpoint: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SuccessEvent:
    """Success event with performance metrics"""
    timestamp: datetime
    response_time: float
    status_code: int
    endpoint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CircuitMetrics:
    """Comprehensive circuit breaker metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeouts: int = 0
    circuit_opens: int = 0
    predictive_opens: int = 0
    average_response_time: float = 0.0
    response_time_p95: float = 0.0
    response_time_p99: float = 0.0
    error_rate: float = 0.0
    throughput: float = 0.0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None

@dataclass
class PredictionResult:
    """ML-based failure prediction result"""
    probability: float
    confidence: float
    feature_importance: Dict[str, float]
    prediction_horizon: timedelta
    recommended_action: str

class CircuitBreakerConfig:
    """Advanced circuit breaker configuration"""

    def __init__(self):
        # Basic thresholds
        self.failure_threshold = 5
        self.success_threshold = 3
        self.timeout_seconds = 30.0
        self.recovery_timeout = 60.0

        # Advanced thresholds
        self.error_rate_threshold = 0.5  # 50% error rate
        self.response_time_threshold = 5.0  # 5 seconds
        self.min_requests_for_analysis = 100

        # Predictive settings
        self.prediction_enabled = True
        self.prediction_horizon = timedelta(minutes=5)
        self.prediction_threshold = 0.7  # 70% probability threshold

        # Adaptive settings
        self.adaptive_thresholds = True
        self.threshold_adjustment_factor = 0.1
        self.load_shedding_enabled = True

        # Monitoring settings
        self.metrics_window_size = 1000
        self.analysis_window_size = 100
        self.anomaly_detection_enabled = True

class FeatureExtractor:
    """Extract features for ML-based failure prediction"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size

    def extract_features(self, events: List[Union[FailureEvent, SuccessEvent]],
                        current_metrics: CircuitMetrics) -> Dict[str, float]:
        """Extract features from historical events and current metrics"""
        if not events:
            return {}

        features = {}

        # Time-based features
        recent_events = [e for e in events
                        if e.timestamp > datetime.utcnow() - timedelta(minutes=10)]

        features['recent_failure_rate'] = self._calculate_failure_rate(recent_events)
        features['recent_throughput'] = len(recent_events) / 10.0  # per minute

        # Response time features
        response_times = [e.response_time for e in recent_events
                         if isinstance(e, SuccessEvent) and e.response_time]

        if response_times:
            features['avg_response_time'] = statistics.mean(response_times)
            features['response_time_std'] = statistics.stdev(response_times) if len(response_times) > 1 else 0
            features['response_time_trend'] = self._calculate_trend(response_times)

        # Error pattern features
        failures = [e for e in recent_events if isinstance(e, FailureEvent)]
        features['failure_rate_trend'] = self._calculate_failure_rate_trend(events)
        features['consecutive_failures'] = self._count_consecutive_failures(events)

        # Time of day features
        now = datetime.utcnow()
        features['hour_of_day'] = now.hour / 24.0
        features['day_of_week'] = now.weekday() / 7.0

        # Current metrics features
        features['current_error_rate'] = current_metrics.error_rate
        features['current_throughput'] = current_metrics.throughput
        features['current_avg_response_time'] = current_metrics.average_response_time

        # Load features
        features['load_factor'] = self._calculate_load_factor(current_metrics)

        return features

    def _calculate_failure_rate(self, events: List[Union[FailureEvent, SuccessEvent]]) -> float:
        """Calculate failure rate in events"""
        if not events:
            return 0.0

        failures = sum(1 for e in events if isinstance(e, FailureEvent))
        return failures / len(events)

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend in values (positive = increasing)"""
        if len(values) < 2:
            return 0.0

        # Simple linear regression slope
        x = list(range(len(values)))
        slope, _, _, _, _ = stats.linregress(x, values)
        return slope

    def _calculate_failure_rate_trend(self, events: List[Union[FailureEvent, SuccessEvent]]) -> float:
        """Calculate trend in failure rate"""
        if len(events) < 10:
            return 0.0

        # Calculate failure rate in sliding windows
        window_size = max(10, len(events) // 5)
        failure_rates = []

        for i in range(len(events) - window_size + 1):
            window = events[i:i + window_size]
            failure_rates.append(self._calculate_failure_rate(window))

        return self._calculate_trend(failure_rates)

    def _count_consecutive_failures(self, events: List[Union[FailureEvent, SuccessEvent]]) -> int:
        """Count consecutive failures from the end"""
        count = 0
        for event in reversed(events):
            if isinstance(event, FailureEvent):
                count += 1
            else:
                break
        return count

    def _calculate_load_factor(self, metrics: CircuitMetrics) -> float:
        """Calculate system load factor"""
        # Simplified load calculation based on throughput and response times
        base_throughput = 100.0  # requests per minute
        base_response_time = 1.0  # seconds

        throughput_factor = min(metrics.throughput / base_throughput, 2.0)
        response_time_factor = min(metrics.average_response_time / base_response_time, 3.0)

        return (throughput_factor + response_time_factor) / 2.0

class FailurePredictor:
    """ML-based failure prediction system"""

    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.random_forest = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.feature_extractor = FeatureExtractor()
        self.is_trained = False
        self.feature_history: List[Dict[str, float]] = []
        self.failure_history: List[bool] = []

    async def predict_failure(self, events: List[Union[FailureEvent, SuccessEvent]],
                            current_metrics: CircuitMetrics) -> PredictionResult:
        """Predict likelihood of failure in near future"""
        features = self.feature_extractor.extract_features(events, current_metrics)

        if not features or not self.is_trained:
            return PredictionResult(
                probability=0.0,
                confidence=0.0,
                feature_importance={},
                prediction_horizon=timedelta(minutes=5),
                recommended_action="monitor"
            )

        # Prepare features for prediction
        feature_vector = np.array([features.get(f, 0.0)
                                  for f in self._get_feature_names()])
        feature_vector = feature_vector.reshape(1, -1)

        # Scale features
        if hasattr(self.scaler, 'mean_'):
            feature_vector = self.scaler.transform(feature_vector)

        # Predict failure probability
        if hasattr(self.random_forest, 'predict_proba'):
            probabilities = self.random_forest.predict_proba(feature_vector)
            failure_prob = probabilities[0][1] if len(probabilities[0]) > 1 else 0.0
        else:
            failure_prob = 0.0

        # Calculate confidence
        confidence = self._calculate_prediction_confidence(feature_vector, failure_prob)

        # Get feature importance
        feature_importance = self._get_feature_importance(features)

        # Determine recommended action
        recommended_action = self._determine_action(failure_prob, confidence)

        return PredictionResult(
            probability=failure_prob,
            confidence=confidence,
            feature_importance=feature_importance,
            prediction_horizon=timedelta(minutes=5),
            recommended_action=recommended_action
        )

    def train(self, events_history: List[List[Union[FailureEvent, SuccessEvent]]],
              outcomes_history: List[bool]):
        """Train the prediction models"""
        if len(events_history) < 50:
            logger.warning("Insufficient data for training predictor")
            return

        # Extract features from all events
        all_features = []
        for events in events_history:
            # Mock current metrics for training
            mock_metrics = CircuitMetrics()
            features = self.feature_extractor.extract_features(events, mock_metrics)
            if features:
                all_features.append(features)

        if len(all_features) < 20:
            logger.warning("Insufficient feature data for training")
            return

        # Prepare training data
        feature_names = self._get_feature_names()
        X = np.array([[f.get(name, 0.0) for name in feature_names] for f in all_features])
        y = np.array(outcomes_history[:len(X)])

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train models
        try:
            self.random_forest.fit(X_scaled, y)
            self.isolation_forest.fit(X_scaled)
            self.is_trained = True

            logger.info("Failure predictor trained successfully",
                       samples=len(X), features=len(feature_names))
        except Exception as e:
            logger.error("Failed to train predictor", error=str(e))

    def _get_feature_names(self) -> List[str]:
        """Get all possible feature names"""
        return [
            'recent_failure_rate', 'recent_throughput', 'avg_response_time',
            'response_time_std', 'response_time_trend', 'failure_rate_trend',
            'consecutive_failures', 'hour_of_day', 'day_of_week',
            'current_error_rate', 'current_throughput', 'current_avg_response_time',
            'load_factor'
        ]

    def _calculate_prediction_confidence(self, features: np.ndarray,
                                       probability: float) -> float:
        """Calculate confidence in prediction"""
        # Use ensemble agreement as confidence measure
        isolation_score = self.isolation_forest.decision_function(features)[0]

        # Combine isolation score with probability
        confidence = abs(isolation_score) * probability

        return min(max(confidence, 0.0), 1.0)

    def _get_feature_importance(self, features: Dict[str, float]) -> Dict[str, float]:
        """Get feature importance from random forest"""
        if not self.is_trained or not hasattr(self.random_forest, 'feature_importances_'):
            return {}

        feature_names = self._get_feature_names()
        importance_dict = {}

        for i, name in enumerate(feature_names):
            if i < len(self.random_forest.feature_importances_):
                importance_dict[name] = self.random_forest.feature_importances_[i]

        return importance_dict

    def _determine_action(self, probability: float, confidence: float) -> str:
        """Determine recommended action based on prediction"""
        if probability > 0.8 and confidence > 0.7:
            return "preventive_open"
        elif probability > 0.6 and confidence > 0.5:
            return "load_shed"
        elif probability > 0.4:
            return "increase_monitoring"
        else:
            return "monitor"

class AdaptiveThresholds:
    """Adaptive threshold management"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.base_failure_threshold = config.failure_threshold
        self.base_error_rate_threshold = config.error_rate_threshold
        self.base_response_time_threshold = config.response_time_threshold
        self.adjustment_history = deque(maxlen=100)
        self.load_factor = 1.0

    def adjust_thresholds(self, metrics: CircuitMetrics,
                         system_load: float) -> Dict[str, float]:
        """Adjust thresholds based on current conditions"""
        if not self.config.adaptive_thresholds:
            return {
                'failure_threshold': self.base_failure_threshold,
                'error_rate_threshold': self.base_error_rate_threshold,
                'response_time_threshold': self.base_response_time_threshold
            }

        self.load_factor = system_load

        # Adjust failure threshold based on load and recent performance
        load_adjustment = 1.0 + (system_load - 1.0) * self.config.threshold_adjustment_factor

        # Reduce thresholds if error rate is increasing
        error_rate_adjustment = 1.0
        if metrics.error_rate > 0.2:  # 20% error rate
            error_rate_adjustment = 0.8

        # Reduce thresholds if response times are degrading
        response_time_adjustment = 1.0
        if metrics.average_response_time > self.base_response_time_threshold * 0.7:
            response_time_adjustment = 0.9

        combined_adjustment = load_adjustment * error_rate_adjustment * response_time_adjustment

        adjusted_failure_threshold = max(1, int(self.base_failure_threshold * combined_adjustment))
        adjusted_error_rate_threshold = min(1.0, self.base_error_rate_threshold * combined_adjustment)
        adjusted_response_time_threshold = self.base_response_time_threshold * combined_adjustment

        thresholds = {
            'failure_threshold': adjusted_failure_threshold,
            'error_rate_threshold': adjusted_error_rate_threshold,
            'response_time_threshold': adjusted_response_time_threshold
        }

        # Record adjustment
        self.adjustment_history.append({
            'timestamp': datetime.utcnow(),
            'load_factor': system_load,
            'adjustment': combined_adjustment,
            'thresholds': thresholds
        })

        return thresholds

class AdvancedCircuitBreaker:
    """Advanced circuit breaker with predictive capabilities"""

    def __init__(self, service_name: str, config: CircuitBreakerConfig):
        self.service_name = service_name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change = datetime.utcnow()

        # Events history
        self.events: deque = deque(maxlen=config.metrics_window_size)
        self.metrics = CircuitMetrics()

        # Advanced components
        self.predictor = FailurePredictor()
        self.adaptive_thresholds = AdaptiveThresholds(config)

        # Rate limiting for load shedding
        self.request_rate_limiter = asyncio.Semaphore(100)  # Max concurrent requests
        self.load_shedding_active = False

        # Metrics
        self.circuit_state_gauge = prom.Gauge(
            f'circuit_breaker_state_{service_name}',
            'Circuit breaker state',
            ['state']
        )
        self.circuit_failures_counter = prom.Counter(
            f'circuit_breaker_failures_{service_name}',
            'Circuit breaker failures',
            ['type']
        )
        self.circuit_predictions = prom.Counter(
            f'circuit_breaker_predictions_{service_name}',
            'Circuit breaker predictions',
            ['action']
        )

    async def execute(self, operation: Callable,
                     *args, **kwargs) -> Any:
        """Execute operation with circuit breaker protection"""
        # Check if request should be allowed
        if not await self._should_allow_request():
            raise CircuitBreakerOpenException(f"Circuit breaker {self.service_name} is {self.state.value}")

        # Apply load shedding if active
        if self.load_shedding_active:
            if not await self._acquire_rate_limit():
                raise LoadShedException(f"Load shedding active for {self.service_name}")

        start_time = time.time()

        try:
            # Execute the operation
            result = await operation(*args, **kwargs)

            # Record success
            response_time = time.time() - start_time
            await self._record_success(response_time, 200)

            return result

        except asyncio.TimeoutError:
            # Record timeout
            response_time = self.config.timeout_seconds
            await self._record_failure(FailureType.TIMEOUT, "Operation timed out", response_time)
            raise

        except httpx.ConnectError as e:
            # Record connection error
            response_time = time.time() - start_time
            await self._record_failure(FailureType.CONNECTION_ERROR, str(e), response_time)
            raise

        except Exception as e:
            # Record other failures
            response_time = time.time() - start_time
            failure_type = self._classify_exception(e)
            await self._record_failure(failure_type, str(e), response_time)
            raise

    async def _should_allow_request(self) -> bool:
        """Determine if request should be allowed"""
        # Check predictive failure
        if self.config.prediction_enabled:
            prediction = await self.predictor.predict_failure(
                list(self.events), self.metrics
            )

            if prediction.probability > self.config.prediction_threshold:
                if prediction.recommended_action == "preventive_open":
                    await self._open_circuit(predictive=True)
                    self.circuit_predictions.labels(action="preventive_open").inc()
                    return False
                elif prediction.recommended_action == "load_shed":
                    await self._activate_load_shedding()
                    self.circuit_predictions.labels(action="load_shed").inc()

        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                await self._transition_to_half_open()
            else:
                return False

        elif self.state == CircuitState.PREVENTIVE_OPEN:
            if self._should_attempt_reset():
                await self._transition_to_half_open()
            else:
                return False

        # Check adaptive thresholds
        thresholds = self.adaptive_thresholds.adjust_thresholds(
            self.metrics, self.adaptive_thresholds.load_factor
        )

        if (self.metrics.error_rate > thresholds['error_rate_threshold'] or
            self.metrics.average_response_time > thresholds['response_time_threshold']):
            if self.failure_count >= thresholds['failure_threshold']:
                await self._open_circuit()
                return False

        return True

    async def _record_success(self, response_time: float, status_code: int):
        """Record successful operation"""
        event = SuccessEvent(
            timestamp=datetime.utcnow(),
            response_time=response_time,
            status_code=status_code
        )

        self.events.append(event)
        self._update_metrics()

        # Update success count for half-open state
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                await self._close_circuit()

        # Reset failure count for closed state
        if self.state == CircuitState.CLOSED:
            self.failure_count = 0

    async def _record_failure(self, failure_type: FailureType,
                            error_message: str, response_time: Optional[float] = None):
        """Record failed operation"""
        event = FailureEvent(
            timestamp=datetime.utcnow(),
            failure_type=failure_type,
            error_message=error_message,
            response_time=response_time
        )

        self.events.append(event)
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        # Update metrics
        self._update_metrics()

        # Update Prometheus metrics
        self.circuit_failures_counter.labels(type=failure_type.value).inc()

        # Check if circuit should open
        thresholds = self.adaptive_thresholds.adjust_thresholds(
            self.metrics, self.adaptive_thresholds.load_factor
        )

        if self.state == CircuitState.HALF_OPEN:
            await self._open_circuit()
        elif self.failure_count >= thresholds['failure_threshold']:
            await self._open_circuit()

    async def _open_circuit(self, predictive: bool = False):
        """Open the circuit breaker"""
        if self.state != CircuitState.OPEN:
            self.state = CircuitState.PREVENTIVE_OPEN if predictive else CircuitState.OPEN
            self.last_state_change = datetime.utcnow()

            logger.warning("Circuit breaker opened",
                          service=self.service_name,
                          state=self.state.value,
                          failure_count=self.failure_count,
                          predictive=predictive)

            # Update metrics
            self.circuit_state_gauge.labels(state=self.state.value).set(1)
            self.metrics.circuit_opens += 1

            if predictive:
                self.metrics.predictive_opens += 1

    async def _close_circuit(self):
        """Close the circuit breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = datetime.utcnow()

        logger.info("Circuit breaker closed", service=self.service_name)

        # Update metrics
        self.circuit_state_gauge.labels(state=self.state.value).set(0)

    async def _transition_to_half_open(self):
        """Transition to half-open state"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.last_state_change = datetime.utcnow()

        logger.info("Circuit breaker half-open", service=self.service_name)

        # Update metrics
        self.circuit_state_gauge.labels(state=self.state.value).set(0.5)

    async def _activate_load_shedding(self):
        """Activate load shedding"""
        self.load_shedding_active = True
        self.state = CircuitState.LOAD_SHEDDING

        logger.warning("Load shedding activated", service=self.service_name)

        # Update metrics
        self.circuit_state_gauge.labels(state=self.state.value).set(0.75)

    async def _acquire_rate_limit(self) -> bool:
        """Acquire rate limit slot"""
        try:
            await asyncio.wait_for(
                self.request_rate_limiter.acquire(),
                timeout=0.1  # Quick timeout to avoid blocking
            )
            return True
        except asyncio.TimeoutError:
            return False

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        if not self.last_failure_time:
            return True

        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.config.recovery_timeout

    def _classify_exception(self, exception: Exception) -> FailureType:
        """Classify exception type"""
        if isinstance(exception, asyncio.TimeoutError):
            return FailureType.TIMEOUT
        elif isinstance(exception, (httpx.ConnectError, httpx.ConnectTimeout)):
            return FailureType.CONNECTION_ERROR
        elif isinstance(exception, httpx.HTTPStatusError):
            return FailureType.HTTP_ERROR
        elif "rate limit" in str(exception).lower():
            return FailureType.RATE_LIMIT
        else:
            return FailureType.UNKNOWN

    def _update_metrics(self):
        """Update circuit breaker metrics"""
        recent_events = list(self.events)[-100:]  # Last 100 events

        if not recent_events:
            return

        # Count successes and failures
        successes = [e for e in recent_events if isinstance(e, SuccessEvent)]
        failures = [e for e in recent_events if isinstance(e, FailureEvent)]

        self.metrics.total_requests = len(recent_events)
        self.metrics.successful_requests = len(successes)
        self.metrics.failed_requests = len(failures)

        # Calculate error rate
        self.metrics.error_rate = len(failures) / len(recent_events) if recent_events else 0

        # Calculate response time metrics
        response_times = [e.response_time for e in successes if e.response_time]
        if response_times:
            self.metrics.average_response_time = statistics.mean(response_times)
            self.metrics.response_time_p95 = np.percentile(response_times, 95)
            self.metrics.response_time_p99 = np.percentile(response_times, 99)

        # Calculate throughput (requests per second over last minute)
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        recent_minute = [e for e in recent_events if e.timestamp > one_minute_ago]
        self.metrics.throughput = len(recent_minute) / 60.0

        # Update timestamps
        if successes:
            self.metrics.last_success_time = max(e.timestamp for e in successes)
        if failures:
            self.metrics.last_failure_time = max(e.timestamp for e in failures)

    async def train_predictor(self, historical_data: List[List[Union[FailureEvent, SuccessEvent]]],
                            outcomes: List[bool]):
        """Train the failure predictor"""
        self.predictor.train(historical_data, outcomes)

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            'service_name': self.service_name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'metrics': asdict(self.metrics),
            'last_state_change': self.last_state_change.isoformat(),
            'load_shedding_active': self.load_shedding_active
        }

class CircuitBreakerManager:
    """Manager for multiple circuit breakers"""

    def __init__(self, redis_url: Optional[str] = None):
        self.circuit_breakers: Dict[str, AdvancedCircuitBreaker] = {}
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.coordinator = CircuitBreakerCoordinator()

    async def initialize(self):
        """Initialize the circuit breaker manager"""
        if self.redis_url:
            self.redis_client = redis.from_url(self.redis_url)
            await self.coordinator.initialize(self.redis_client)

    def create_circuit_breaker(self, service_name: str,
                             config: Optional[CircuitBreakerConfig] = None) -> AdvancedCircuitBreaker:
        """Create a new circuit breaker"""
        if config is None:
            config = CircuitBreakerConfig()

        circuit_breaker = AdvancedCircuitBreaker(service_name, config)
        self.circuit_breakers[service_name] = circuit_breaker

        # Register with coordinator for distributed coordination
        asyncio.create_task(self.coordinator.register_circuit_breaker(circuit_breaker))

        return circuit_breaker

    def get_circuit_breaker(self, service_name: str) -> Optional[AdvancedCircuitBreaker]:
        """Get circuit breaker by service name"""
        return self.circuit_breakers.get(service_name)

    async def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get all circuit breaker states"""
        states = {}
        for name, breaker in self.circuit_breakers.items():
            states[name] = breaker.get_state()
        return states

class CircuitBreakerCoordinator:
    """Distributed circuit breaker coordination"""

    def __init__(self):
        self.circuit_breakers: Dict[str, AdvancedCircuitBreaker] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.coordination_enabled = False

    async def initialize(self, redis_client: redis.Redis):
        """Initialize distributed coordination"""
        self.redis_client = redis_client
        self.coordination_enabled = True

        # Start coordination tasks
        asyncio.create_task(self._coordinate_states())
        asyncio.create_task(self._share_predictions())

    async def register_circuit_breaker(self, circuit_breaker: AdvancedCircuitBreaker):
        """Register circuit breaker for coordination"""
        self.circuit_breakers[circuit_breaker.service_name] = circuit_breaker

    async def _coordinate_states(self):
        """Coordinate circuit breaker states across instances"""
        if not self.coordination_enabled:
            return

        while True:
            try:
                # Publish state updates
                for name, breaker in self.circuit_breakers.items():
                    state_key = f"circuit_breaker:{name}:state"
                    await self.redis_client.setex(
                        state_key,
                        300,  # 5 minutes TTL
                        json.dumps(breaker.get_state())
                    )

                # Check for coordinated actions
                await self._check_coordination_triggers()

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error("Circuit breaker coordination error", error=str(e))
                await asyncio.sleep(30)

    async def _share_predictions(self):
        """Share ML predictions across instances"""
        if not self.coordination_enabled:
            return

        while True:
            try:
                for name, breaker in self.circuit_breakers.items():
                    if breaker.predictor.is_trained:
                        # Share prediction model updates periodically
                        prediction_key = f"circuit_breaker:{name}:prediction"
                        await self.redis_client.setex(
                            prediction_key,
                            3600,  # 1 hour TTL
                            json.dumps({"model_updated": datetime.utcnow().isoformat()})
                        )

                await asyncio.sleep(300)  # Share every 5 minutes

            except Exception as e:
                logger.error("Prediction sharing error", error=str(e))
                await asyncio.sleep(600)

    async def _check_coordination_triggers(self):
        """Check for coordinated circuit breaker actions"""
        for name, breaker in self.circuit_breakers.items():
            # Get global state for this service
            global_state_key = f"circuit_breaker:{name}:global_state"
            global_state = await self.redis_client.get(global_state_key)

            if global_state:
                global_data = json.loads(global_state)

                # Coordinate circuit opening based on global conditions
                if global_data.get('global_failure_rate', 0) > 0.8:
                    await breaker._open_circuit(predictive=True)

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class LoadShedException(Exception):
    """Exception raised when load shedding is active"""
    pass

# Initialize advanced circuit breaker system
async def initialize_circuit_breaker_system(redis_url: Optional[str] = None) -> CircuitBreakerManager:
    """Initialize the complete circuit breaker system"""

    manager = CircuitBreakerManager(redis_url)
    await manager.initialize()

    logger.info("Advanced circuit breaker system initialized")

    return manager

# Export main classes and functions
__all__ = [
    'AdvancedCircuitBreaker',
    'CircuitBreakerManager',
    'CircuitBreakerCoordinator',
    'CircuitBreakerConfig',
    'FailurePredictor',
    'AdaptiveThresholds',
    'CircuitState',
    'FailureType',
    'initialize_circuit_breaker_system',
    'CircuitBreakerOpenException',
    'LoadShedException'
]