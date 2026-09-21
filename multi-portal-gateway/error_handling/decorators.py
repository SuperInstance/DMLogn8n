"""
Decorators for Easy Error Handling Integration

Provides convenient decorators for adding error handling capabilities
to functions and methods with minimal code changes.
"""

import functools
import time
import asyncio
import logging
import inspect
from typing import Callable, Any, Optional, Dict, List, Type, Union
from dataclasses import dataclass

from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, circuit_breaker_registry
from .retry_handler import RetryHandler, RetryConfig, retry_handler_registry
from .error_classifier import error_classification_system, ErrorContext
from .recovery_manager import recovery_manager
from .monitoring import error_monitor

logger = logging.getLogger(__name__)


@dataclass
class ErrorHandlingConfig:
    """Configuration for error handling decorators."""
    circuit_breaker: Optional[CircuitBreakerConfig] = None
    retry: Optional[RetryConfig] = None
    classify_error: bool = True
    monitor: bool = True
    auto_recovery: bool = False
    fallback: Optional[Callable] = None
    error_context: Optional[Dict[str, Any]] = None
    circuit_breaker_name: Optional[str] = None
    retry_handler_name: Optional[str] = None


def with_circuit_breaker(config: Optional[CircuitBreakerConfig] = None,
                        name: Optional[str] = None):
    """
    Decorator to add circuit breaker protection to a function.

    Args:
        config: Circuit breaker configuration
        name: Circuit breaker name (auto-generated if not provided)

    Example:
        @with_circuit_breaker(
            CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30.0,
                name="api_call"
            )
        )
        async def api_call():
            return await make_request()
    """
    def decorator(func: Callable) -> Callable:
        breaker_name = name or f"{func.__module__}.{func.__name__}"

        if config:
            breaker = circuit_breaker_registry.get_breaker(breaker_name, config)
        else:
            breaker = circuit_breaker_registry.get_breaker(breaker_name)

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await breaker.call(func, *args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return asyncio.run(breaker.call(func, *args, **kwargs))
            return sync_wrapper

    return decorator


def with_retry(config: Optional[RetryConfig] = None,
              name: Optional[str] = None):
    """
    Decorator to add retry logic to a function.

    Args:
        config: Retry configuration
        name: Retry handler name (auto-generated if not provided)

    Example:
        @with_retry(
            RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                backoff_strategy=BackoffStrategy.EXPONENTIAL
            )
        )
        async def unreliable_operation():
            return await perform_operation()
    """
    def decorator(func: Callable) -> Callable:
        handler_name = name or f"{func.__module__}.{func.__name__}"

        if config:
            handler = retry_handler_registry.get_handler(handler_name, config)
        else:
            handler = retry_handler_registry.get_handler(handler_name)

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await handler.execute_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return handler.execute(func, *args, **kwargs)
            return sync_wrapper

    return decorator


def with_error_handling(config: Optional[ErrorHandlingConfig] = None):
    """
    Comprehensive error handling decorator with multiple protection mechanisms.

    Args:
        config: Error handling configuration

    Example:
        @with_error_handling(
            ErrorHandlingConfig(
                circuit_breaker=CircuitBreakerConfig(failure_threshold=5),
                retry=RetryConfig(max_attempts=3),
                monitor=True,
                auto_recovery=True
            )
        )
        async def critical_service_call():
            return await service_call()
    """
    def decorator(func: Callable) -> Callable:
        handling_config = config or ErrorHandlingConfig()

        # Get circuit breaker if configured
        breaker = None
        if handling_config.circuit_breaker or handling_config.circuit_breaker_name:
            breaker_name = handling_config.circuit_breaker_name or f"{func.__module__}.{func.__name__}"
            if handling_config.circuit_breaker:
                breaker = circuit_breaker_registry.get_breaker(breaker_name, handling_config.circuit_breaker)
            else:
                breaker = circuit_breaker_registry.get_breaker(breaker_name)

        # Get retry handler if configured
        retry_handler = None
        if handling_config.retry or handling_config.retry_handler_name:
            handler_name = handling_config.retry_handler_name or f"{func.__module__}.{func.__name__}"
            if handling_config.retry:
                retry_handler = retry_handler_registry.get_handler(handler_name, handling_config.retry)
            else:
                retry_handler = retry_handler_registry.get_handler(handler_name)

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()

                try:
                    # Apply circuit breaker if configured
                    if breaker:
                        if retry_handler:
                            # Combine circuit breaker with retry
                            async def protected_call():
                                return await breaker.call(func, *args, **kwargs)
                            return await retry_handler.execute_async(protected_call)
                        else:
                            # Just circuit breaker
                            return await breaker.call(func, *args, **kwargs)
                    elif retry_handler:
                        # Just retry
                        return await retry_handler.execute_async(func, *args, **kwargs)
                    else:
                        # Direct call
                        return await func(*args, **kwargs)

                except Exception as e:
                    # Handle error
                    await _handle_decorator_error(
                        e, func, handling_config, start_time, args, kwargs
                    )

                    # Use fallback if available
                    if handling_config.fallback:
                        if inspect.iscoroutinefunction(handling_config.fallback):
                            return await handling_config.fallback(e, *args, **kwargs)
                        else:
                            return handling_config.fallback(e, *args, **kwargs)

                    # Re-raise if no fallback
                    raise

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()

                try:
                    # Apply circuit breaker if configured
                    if breaker:
                        if retry_handler:
                            # Combine circuit breaker with retry
                            def protected_call():
                                return asyncio.run(breaker.call(func, *args, **kwargs))
                            return retry_handler.execute(protected_call)
                        else:
                            # Just circuit breaker
                            return asyncio.run(breaker.call(func, *args, **kwargs))
                    elif retry_handler:
                        # Just retry
                        return retry_handler.execute(func, *args, **kwargs)
                    else:
                        # Direct call
                        return func(*args, **kwargs)

                except Exception as e:
                    # Handle error (synchronously)
                    asyncio.run(_handle_decorator_error(
                        e, func, handling_config, start_time, args, kwargs
                    ))

                    # Use fallback if available
                    if handling_config.fallback:
                        return handling_config.fallback(e, *args, **kwargs)

                    # Re-raise if no fallback
                    raise

            return sync_wrapper

    return decorator


async def _handle_decorator_error(exception: Exception,
                                 func: Callable,
                                 config: ErrorHandlingConfig,
                                 start_time: float,
                                 args: tuple,
                                 kwargs: dict) -> None:
    """Handle error in decorator context."""
    response_time = time.time() - start_time

    # Create error context
    error_context = {
        "component": func.__module__,
        "operation": func.__name__,
        "args_count": len(args),
        "kwargs_keys": list(kwargs.keys()),
        **(config.error_context or {})
    }

    # Classify error if enabled
    if config.classify_error:
        error_info, routing_decision = error_classification_system.classify_and_route(
            exception,
            error_context
        )

        # Attempt auto-recovery if enabled
        if config.auto_recovery and routing_decision.retry_recommended:
            try:
                applicable_actions = recovery_manager.get_applicable_actions(error_info)
                if applicable_actions:
                    await recovery_manager.execute_recovery(
                        applicable_actions[0].name,
                        error_info
                    )
            except Exception as recovery_error:
                logger.error(f"Auto-recovery failed: {recovery_error}")

    # Record for monitoring if enabled
    if config.monitor:
        error_monitor.record_error(
            error_info if config.classify_error else exception,
            response_time=response_time,
            recovery_attempted=config.auto_recovery,
            **error_context
        )


# Shorthand decorators for common patterns
def circuit_breaker(failure_threshold: int = 5,
                    recovery_timeout: float = 60.0,
                    name: Optional[str] = None):
    """Shorthand decorator for circuit breaker."""
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        name=name or "default"
    )
    return with_circuit_breaker(config)


def retry(max_attempts: int = 3,
          base_delay: float = 1.0,
          backoff_strategy=None,
          name: Optional[str] = None):
    """Shorthand decorator for retry."""
    from .retry_handler import BackoffStrategy

    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        backoff_strategy=backoff_strategy or BackoffStrategy.EXPONENTIAL,
        name=name or "default"
    )
    return with_retry(config)


def resilient(max_attempts: int = 3,
              failure_threshold: int = 5,
              recovery_timeout: float = 60.0,
              monitor: bool = True,
              auto_recovery: bool = True):
    """
    Shorthand decorator for resilient operations with both retry and circuit breaker.

    Example:
        @resilient(max_attempts=3, failure_threshold=5)
        async def external_api_call():
            return await api_client.request()
    """
    from .retry_handler import BackoffStrategy

    config = ErrorHandlingConfig(
        circuit_breaker=CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        ),
        retry=RetryConfig(
            max_attempts=max_attempts,
            base_delay=1.0,
            backoff_strategy=BackoffStrategy.EXPONENTIAL
        ),
        monitor=monitor,
        auto_recovery=auto_recovery
    )
    return with_error_handling(config)


def error_handler(exception_types: Union[Type[Exception], List[Type[Exception]]] = Exception,
                 fallback: Optional[Callable] = None,
                 log_error: bool = True):
    """
    Simple error handler decorator with exception filtering.

    Example:
        @error_handler(ValueError, fallback=lambda e, *args, **kwargs: None)
        def process_data(data):
            return data.validate()
    """
    if not isinstance(exception_types, list):
        exception_types = [exception_types]

    def decorator(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except tuple(exception_types) as e:
                    if log_error:
                        logger.error(f"Error in {func.__name__}: {e}")

                    if fallback:
                        if inspect.iscoroutinefunction(fallback):
                            return await fallback(e, *args, **kwargs)
                        else:
                            return fallback(e, *args, **kwargs)

                    raise
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except tuple(exception_types) as e:
                    if log_error:
                        logger.error(f"Error in {func.__name__}: {e}")

                    if fallback:
                        return fallback(e, *args, **kwargs)

                    raise
            return sync_wrapper

    return decorator


def monitor_performance(log_slow_calls: bool = True,
                       slow_threshold: float = 1.0):
    """
    Decorator to monitor function performance and log slow calls.

    Example:
        @monitor_performance(slow_threshold=0.5)
        async def database_query():
            return await db.execute(query)
    """
    def decorator(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    if log_slow_calls and duration > slow_threshold:
                        logger.warning(
                            f"Slow call: {func.__name__} took {duration:.2f}s "
                            f"(threshold: {slow_threshold}s)"
                        )
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    if log_slow_calls and duration > slow_threshold:
                        logger.warning(
                            f"Slow call: {func.__name__} took {duration:.2f}s "
                            f"(threshold: {slow_threshold}s)"
                        )
            return sync_wrapper

    return decorator


class ErrorHandlerMixin:
    """
    Mixin class to add error handling capabilities to any class.

    Example:
        class APIClient(ErrorHandlerMixin):
            @with_circuit_breaker()
            async def make_request(self, endpoint):
                return await self.session.get(endpoint)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._error_handlers: Dict[str, Callable] = {}
        self._error_context: Dict[str, Any] = {}

    def register_error_handler(self, error_type: Type[Exception], handler: Callable) -> None:
        """Register an error handler for a specific exception type."""
        self._error_handlers[error_type.__name__] = handler

    def set_error_context(self, **context) -> None:
        """Set default error context for this instance."""
        self._error_context.update(context)

    async def handle_error(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Any:
        """Handle an error using registered handlers."""
        handler = self._error_handlers.get(type(exception).__name__)

        if handler:
            error_context = {**self._error_context, **(context or {})}
            if inspect.iscoroutinefunction(handler):
                return await handler(exception, error_context)
            else:
                return handler(exception, error_context)

        # No handler found, re-raise
        raise exception


# Utility functions for creating decorators with custom configurations
def create_custom_decorator(name: str,
                          circuit_breaker_config: Optional[CircuitBreakerConfig] = None,
                          retry_config: Optional[RetryConfig] = None,
                          **kwargs) -> Callable:
    """
    Create a custom decorator with predefined configuration.

    Example:
        # Create a custom decorator for API calls
        api_call_decorator = create_custom_decorator(
            "api_call",
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=3),
            retry_config=RetryConfig(max_attempts=2)
        )

        @api_call_decorator
        async def external_api():
            return await http_client.get("/api/data")
    """
    config = ErrorHandlingConfig(
        circuit_breaker=circuit_breaker_config,
        retry=retry_config,
        **kwargs
    )

    def decorator(func: Callable) -> Callable:
        wrapper = with_error_handling(config)(func)
        wrapper._decorator_name = name  # Store decorator name for debugging
        return wrapper

    decorator.name = name
    return decorator