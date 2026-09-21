"""
Circuit Breaker Pattern Implementation

Provides circuit breaker functionality to prevent cascading failures
and provide fast failure when services are experiencing issues.
"""

import time
import threading
import logging
from enum import Enum
from typing import Callable, Any, Optional, Dict, List
from dataclasses import dataclass, field
from collections import deque
import asyncio

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Circuit is open, calls fail fast
    HALF_OPEN = "HALF_OPEN"  # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5                    # Number of failures before opening
    recovery_timeout: float = 60.0               # Seconds to wait before trying recovery
    expected_exception: type = Exception         # Exception type to count as failure
    success_threshold: int = 3                   # Successes needed to close circuit
    timeout: float = 10.0                        # Call timeout in seconds
    max_concurrent_calls: int = 100              # Maximum concurrent calls
    sliding_window_size: int = 100               # Size of sliding window for metrics
    reset_timeout: Optional[float] = None        # Auto-reset timeout (None = manual)
    name: str = "default"                        # Circuit breaker name


@dataclass
class CallMetrics:
    """Metrics for circuit breaker calls."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    timeouts: int = 0
    concurrent_calls: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    failure_rate: float = 0.0
    recent_failures: deque = field(default_factory=lambda: deque(maxlen=100))
    recent_successes: deque = field(default_factory=lambda: deque(maxlen=100))


class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors."""
    pass


class CircuitOpenError(CircuitBreakerError):
    """Raised when circuit is open."""
    pass


class CallTimeoutError(CircuitBreakerError):
    """Raised when call times out."""
    pass


class MaxConcurrentCallsError(CircuitBreakerError):
    """Raised when maximum concurrent calls exceeded."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation with state management and metrics.

    Prevents cascading failures by:
    1. Tracking failures and opening circuit when threshold exceeded
    2. Providing fast failure when circuit is open
    3. Testing recovery with half-open state
    4. Providing comprehensive metrics and monitoring
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.metrics = CallMetrics()
        self._lock = threading.RLock()
        self._last_state_change = time.time()
        self._half_open_calls = 0

        logger.info(f"Circuit breaker '{config.name}' initialized with state: {self.state.value}")

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitOpenError: If circuit is open
            MaxConcurrentCallsError: If max concurrent calls exceeded
            CallTimeoutError: If call times out
            Exception: Original exception from function call
        """
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    self.metrics.total_calls += 1
                    logger.warning(f"Circuit '{self.config.name}' is OPEN - rejecting call")
                    raise CircuitOpenError(f"Circuit '{self.config.name}' is open")

            if self.metrics.concurrent_calls >= self.config.max_concurrent_calls:
                self.metrics.total_calls += 1
                logger.warning(f"Circuit '{self.config.name}' max concurrent calls exceeded")
                raise MaxConcurrentCallsError(f"Maximum concurrent calls ({self.config.max_concurrent_calls}) exceeded")

            self.metrics.concurrent_calls += 1
            self.metrics.total_calls += 1

        start_time = time.time()

        try:
            # Execute with timeout
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: func(*args, **kwargs)
                )
                # Simulate timeout for synchronous functions
                execution_time = time.time() - start_time
                if execution_time > self.config.timeout:
                    raise CallTimeoutError(f"Call exceeded timeout of {self.config.timeout}s")

            # Record success
            with self._lock:
                self.metrics.successful_calls += 1
                self.metrics.concurrent_calls -= 1
                self.metrics.last_success_time = time.time()
                self.metrics.recent_successes.append(time.time())
                self._update_failure_rate()

                if self.state == CircuitState.HALF_OPEN:
                    self._half_open_calls += 1
                    if self._half_open_calls >= self.config.success_threshold:
                        self._transition_to_closed()

            logger.debug(f"Circuit '{self.config.name}' call successful")
            return result

        except Exception as e:
            # Record failure
            with self._lock:
                self.metrics.failed_calls += 1
                self.metrics.concurrent_calls -= 1
                self.metrics.last_failure_time = time.time()
                self.metrics.recent_failures.append(time.time())
                self._update_failure_rate()

                # Check if this is a timeout
                if "timeout" in str(e).lower():
                    self.metrics.timeouts += 1

                # Check if we should count this as a circuit breaker failure
                if isinstance(e, self.config.expected_exception):
                    if self.state == CircuitState.HALF_OPEN:
                        self._transition_to_open()
                    elif self.state == CircuitState.CLOSED:
                        if self._should_open_circuit():
                            self._transition_to_open()

            logger.error(f"Circuit '{self.config.name}' call failed: {e}")
            raise

    def force_open(self) -> None:
        """Force circuit to open state."""
        with self._lock:
            if self.state != CircuitState.OPEN:
                self._transition_to_open()
                logger.info(f"Circuit '{self.config.name}' forced open")

    def force_close(self) -> None:
        """Force circuit to closed state."""
        with self._lock:
            if self.state != CircuitState.CLOSED:
                self._transition_to_closed()
                logger.info(f"Circuit '{self.config.name}' forced closed")

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.metrics = CallMetrics()
            self._last_state_change = time.time()
            self._half_open_calls = 0
            logger.info(f"Circuit '{self.config.name}' reset")

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self.state

    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics."""
        with self._lock:
            return {
                "state": self.state.value,
                "total_calls": self.metrics.total_calls,
                "successful_calls": self.metrics.successful_calls,
                "failed_calls": self.metrics.failed_calls,
                "timeouts": self.metrics.timeouts,
                "concurrent_calls": self.metrics.concurrent_calls,
                "failure_rate": self.metrics.failure_rate,
                "last_failure_time": self.metrics.last_failure_time,
                "last_success_time": self.metrics.last_success_time,
                "last_state_change": self._last_state_change,
                "uptime_seconds": time.time() - self._last_state_change
            }

    def _should_open_circuit(self) -> bool:
        """Check if circuit should be opened based on failure threshold."""
        return self.metrics.failed_calls >= self.config.failure_threshold

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset based on timeout."""
        if self.metrics.last_failure_time is None:
            return False

        time_since_failure = time.time() - self.metrics.last_failure_time
        return time_since_failure >= self.config.recovery_timeout

    def _update_failure_rate(self) -> None:
        """Update failure rate based on recent calls."""
        if self.metrics.total_calls == 0:
            self.metrics.failure_rate = 0.0
            return

        # Calculate failure rate over sliding window
        recent_time = time.time() - self.config.sliding_window_size
        recent_failures = sum(1 for t in self.metrics.recent_failures if t > recent_time)
        recent_successes = sum(1 for t in self.metrics.recent_successes if t > recent_time)
        recent_total = recent_failures + recent_successes

        if recent_total > 0:
            self.metrics.failure_rate = recent_failures / recent_total
        else:
            self.metrics.failure_rate = 0.0

    def _transition_to_open(self) -> None:
        """Transition circuit to open state."""
        self.state = CircuitState.OPEN
        self._last_state_change = time.time()
        self._half_open_calls = 0
        logger.warning(f"Circuit '{self.config.name}' transitioned to OPEN")

    def _transition_to_half_open(self) -> None:
        """Transition circuit to half-open state."""
        self.state = CircuitState.HALF_OPEN
        self._last_state_change = time.time()
        self._half_open_calls = 0
        logger.info(f"Circuit '{self.config.name}' transitioned to HALF_OPEN")

    def _transition_to_closed(self) -> None:
        """Transition circuit to closed state."""
        self.state = CircuitState.CLOSED
        self._last_state_change = time.time()
        self._half_open_calls = 0
        logger.info(f"Circuit '{self.config.name}' transitioned to CLOSED")


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()

    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """
        Get or create circuit breaker.

        Args:
            name: Circuit breaker name
            config: Configuration for new breaker (optional)

        Returns:
            CircuitBreaker instance
        """
        with self._lock:
            if name not in self._breakers:
                if config is None:
                    config = CircuitBreakerConfig(name=name)
                self._breakers[name] = CircuitBreaker(config)
                logger.info(f"Created new circuit breaker '{name}'")

            return self._breakers[name]

    def remove_breaker(self, name: str) -> bool:
        """Remove circuit breaker from registry."""
        with self._lock:
            if name in self._breakers:
                del self._breakers[name]
                logger.info(f"Removed circuit breaker '{name}'")
                return True
            return False

    def get_all_breakers(self) -> Dict[str, CircuitBreaker]:
        """Get all registered circuit breakers."""
        with self._lock:
            return self._breakers.copy()

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all circuit breakers."""
        with self._lock:
            return {name: breaker.get_metrics() for name, breaker in self._breakers.items()}

    def force_open_all(self) -> None:
        """Force all circuit breakers to open."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.force_open()

    def force_close_all(self) -> None:
        """Force all circuit breakers to close."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.force_close()

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()


# Global circuit breaker registry
circuit_breaker_registry = CircuitBreakerRegistry()