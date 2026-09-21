"""
Retry Mechanisms with Multiple Backoff Strategies

Provides flexible retry capabilities with various backoff strategies,
exception filtering, and comprehensive retry policies.
"""

import time
import random
import asyncio
import logging
import threading
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Any, Optional, List, Dict, Type, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class BackoffStrategy(Enum):
    """Available backoff strategies."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"
    FIBONACCI = "fibonacci"
    JITTER = "jitter"
    CUSTOM = "custom"


@dataclass
class RetryConfig:
    """Configuration for retry handler."""
    max_attempts: int = 3                           # Maximum number of retry attempts
    base_delay: float = 1.0                         # Base delay in seconds
    max_delay: float = 60.0                         # Maximum delay in seconds
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    backoff_multiplier: float = 2.0                 # Multiplier for exponential backoff
    jitter: bool = True                             # Add jitter to delays
    retryable_exceptions: List[Type[Exception]] = field(default_factory=lambda: [Exception])
    non_retryable_exceptions: List[Type[Exception]] = field(default_factory=list)
    on_retry_callback: Optional[Callable] = None    # Callback called on each retry
    on_success_callback: Optional[Callable] = None  # Callback called on success
    on_failure_callback: Optional[Callable] = None  # Callback called on final failure
    retry_condition: Optional[Callable[[Exception], bool]] = None  # Custom retry condition
    name: str = "default"                           # Retry handler name


@dataclass
class RetryAttempt:
    """Information about a retry attempt."""
    attempt_number: int
    delay: float
    exception: Optional[Exception]
    start_time: float
    end_time: Optional[float] = None


@dataclass
class RetryResult:
    """Result of retry operation."""
    success: bool
    result: Any
    total_attempts: int
    total_time: float
    attempts: List[RetryAttempt]
    final_exception: Optional[Exception]


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


class BackoffCalculator(ABC):
    """Abstract base class for backoff calculators."""

    @abstractmethod
    def calculate_delay(self, attempt: int, base_delay: float, max_delay: float) -> float:
        """Calculate delay for given attempt."""
        pass


class ExponentialBackoff(BackoffCalculator):
    """Exponential backoff strategy."""

    def __init__(self, multiplier: float = 2.0):
        self.multiplier = multiplier

    def calculate_delay(self, attempt: int, base_delay: float, max_delay: float) -> float:
        delay = base_delay * (self.multiplier ** (attempt - 1))
        return min(delay, max_delay)


class LinearBackoff(BackoffCalculator):
    """Linear backoff strategy."""

    def __init__(self, increment: float = 1.0):
        self.increment = increment

    def calculate_delay(self, attempt: int, base_delay: float, max_delay: float) -> float:
        delay = base_delay + (self.increment * (attempt - 1))
        return min(delay, max_delay)


class FixedBackoff(BackoffCalculator):
    """Fixed delay backoff strategy."""

    def calculate_delay(self, attempt: int, base_delay: float, max_delay: float) -> float:
        return min(base_delay, max_delay)


class FibonacciBackoff(BackoffCalculator):
    """Fibonacci sequence backoff strategy."""

    def __init__(self):
        self._fib_cache = {0: 0, 1: 1}

    def _fib(self, n: int) -> int:
        """Calculate Fibonacci number."""
        if n in self._fib_cache:
            return self._fib_cache[n]

        self._fib_cache[n] = self._fib(n - 1) + self._fib(n - 2)
        return self._fib_cache[n]

    def calculate_delay(self, attempt: int, base_delay: float, max_delay: float) -> float:
        delay = base_delay * self._fib(attempt)
        return min(delay, max_delay)


class JitterBackoff(BackoffCalculator):
    """Jitter backoff strategy with randomization."""

    def __init__(self, jitter_range: float = 0.1):
        self.jitter_range = jitter_range

    def calculate_delay(self, attempt: int, base_delay: float, max_delay: float) -> float:
        # Use exponential as base, then add jitter
        exponential = ExponentialBackoff()
        base = exponential.calculate_delay(attempt, base_delay, max_delay)

        # Add jitter: ±jitter_range of the base delay
        jitter_amount = base * self.jitter_range
        jittered = base + random.uniform(-jitter_amount, jitter_amount)

        return max(0, min(jittered, max_delay))


class RetryHandler:
    """
    Retry handler with multiple backoff strategies and comprehensive retry logic.

    Features:
    - Multiple backoff strategies (exponential, linear, fixed, fibonacci, jitter)
    - Exception filtering and custom retry conditions
    - Callbacks for retry events
    - Comprehensive metrics and logging
    - Async and sync function support
    """

    def __init__(self, config: RetryConfig):
        self.config = config
        self._backoff_calculator = self._create_backoff_calculator()
        self._lock = threading.RLock()

        logger.info(f"Retry handler '{config.name}' initialized with {config.backoff_strategy.value} backoff")

    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function with retry logic.

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            RetryError: If all retry attempts are exhausted
        """
        attempts = []
        start_time = time.time()

        for attempt in range(1, self.config.max_attempts + 1):
            attempt_start = time.time()

            try:
                # Execute the function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    # Run sync function in thread pool
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: func(*args, **kwargs)
                    )

                # Success!
                attempt_end = time.time()
                attempt_info = RetryAttempt(
                    attempt_number=attempt,
                    delay=0.0,
                    exception=None,
                    start_time=attempt_start,
                    end_time=attempt_end
                )
                attempts.append(attempt_info)

                total_time = time.time() - start_time

                if self.config.on_success_callback:
                    try:
                        await self._run_callback(
                            self.config.on_success_callback,
                            result, attempt, attempts
                        )
                    except Exception as callback_error:
                        logger.error(f"Success callback error: {callback_error}")

                logger.info(f"Retry handler '{self.config.name}' succeeded on attempt {attempt}")
                return result

            except Exception as e:
                attempt_end = time.time()

                # Check if we should retry this exception
                if not self._should_retry_exception(e):
                    logger.error(f"Retry handler '{self.config.name}' non-retryable exception: {e}")
                    raise

                # Record attempt
                attempt_info = RetryAttempt(
                    attempt_number=attempt,
                    delay=0.0,
                    exception=e,
                    start_time=attempt_start,
                    end_time=attempt_end
                )
                attempts.append(attempt_info)

                # Check if we have more attempts
                if attempt >= self.config.max_attempts:
                    total_time = time.time() - start_time

                    if self.config.on_failure_callback:
                        try:
                            await self._run_callback(
                                self.config.on_failure_callback,
                                e, attempts, total_time
                            )
                        except Exception as callback_error:
                            logger.error(f"Failure callback error: {callback_error}")

                    logger.error(f"Retry handler '{self.config.name}' exhausted all {self.config.max_attempts} attempts")
                    raise RetryError(f"All {self.config.max_attempts} retry attempts exhausted") from e

                # Calculate delay for next attempt
                delay = self._backoff_calculator.calculate_delay(
                    attempt, self.config.base_delay, self.config.max_delay
                )

                # Add jitter if enabled
                if self.config.jitter and not isinstance(self._backoff_calculator, JitterBackoff):
                    jitter = random.uniform(0.8, 1.2)
                    delay *= jitter

                attempt_info.delay = delay

                # Call retry callback
                if self.config.on_retry_callback:
                    try:
                        await self._run_callback(
                            self.config.on_retry_callback,
                            e, attempt, delay, attempts
                        )
                    except Exception as callback_error:
                        logger.error(f"Retry callback error: {callback_error}")

                logger.warning(
                    f"Retry handler '{self.config.name}' attempt {attempt} failed: {e}. "
                    f"Retrying in {delay:.2f} seconds"
                )

                # Wait before next attempt
                await asyncio.sleep(delay)

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute sync function with retry logic.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            RetryError: If all retry attempts are exhausted
        """
        # Run the async version in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.execute_async(func, *args, **kwargs))

    def _create_backoff_calculator(self) -> BackoffCalculator:
        """Create backoff calculator based on strategy."""
        if self.config.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            return ExponentialBackoff(self.config.backoff_multiplier)
        elif self.config.backoff_strategy == BackoffStrategy.LINEAR:
            return LinearBackoff()
        elif self.config.backoff_strategy == BackoffStrategy.FIXED:
            return FixedBackoff()
        elif self.config.backoff_strategy == BackoffStrategy.FIBONACCI:
            return FibonacciBackoff()
        elif self.config.backoff_strategy == BackoffStrategy.JITTER:
            return JitterBackoff()
        else:
            return ExponentialBackoff()

    def _should_retry_exception(self, exception: Exception) -> bool:
        """Check if exception should be retried."""
        # Check non-retryable exceptions first
        for non_retryable in self.config.non_retryable_exceptions:
            if isinstance(exception, non_retryable):
                return False

        # Check retryable exceptions
        for retryable in self.config.retryable_exceptions:
            if isinstance(exception, retryable):
                return True

        # Use custom retry condition if provided
        if self.config.retry_condition:
            try:
                return self.config.retry_condition(exception)
            except Exception as e:
                logger.error(f"Error in retry condition: {e}")
                return False

        # Default to retrying if no specific configuration
        return True

    async def _run_callback(self, callback: Callable, *args, **kwargs) -> None:
        """Run callback safely (sync or async)."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                # Run sync callback in thread pool
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: callback(*args, **kwargs)
                )
        except Exception as e:
            logger.error(f"Callback execution error: {e}")


class RetryHandlerRegistry:
    """Registry for managing multiple retry handlers."""

    def __init__(self):
        self._handlers: Dict[str, RetryHandler] = {}
        self._lock = threading.RLock()

    def get_handler(self, name: str, config: Optional[RetryConfig] = None) -> RetryHandler:
        """
        Get or create retry handler.

        Args:
            name: Handler name
            config: Configuration for new handler (optional)

        Returns:
            RetryHandler instance
        """
        with self._lock:
            if name not in self._handlers:
                if config is None:
                    config = RetryConfig(name=name)
                self._handlers[name] = RetryHandler(config)
                logger.info(f"Created new retry handler '{name}'")

            return self._handlers[name]

    def remove_handler(self, name: str) -> bool:
        """Remove retry handler from registry."""
        with self._lock:
            if name in self._handlers:
                del self._handlers[name]
                logger.info(f"Removed retry handler '{name}'")
                return True
            return False

    def get_all_handlers(self) -> Dict[str, RetryHandler]:
        """Get all registered retry handlers."""
        with self._lock:
            return self._handlers.copy()


# Global retry handler registry
retry_handler_registry = RetryHandlerRegistry()