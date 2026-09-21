"""
Comprehensive Error Handling and Recovery System for DMLogn8n Multi-Agent Platform

This package provides enterprise-grade error handling capabilities including:
- Circuit breaker pattern implementation
- Retry mechanisms with exponential backoff
- Error classification and routing
- Graceful degradation strategies
- Error recovery automation
- Error monitoring and alerting
"""

from .circuit_breaker import CircuitBreaker, CircuitState
from .retry_handler import RetryHandler, BackoffStrategy
from .error_classifier import ErrorClassifier, ErrorSeverity, ErrorCategory
from .recovery_manager import RecoveryManager, RecoveryAction
from .middleware import ErrorHandlingMiddleware
from .monitoring import ErrorMonitor, AlertManager
from .decorators import (
    with_circuit_breaker,
    with_retry,
    with_error_handling,
    circuit_breaker,
    retry,
    error_handler
)

__version__ = "1.0.0"
__author__ = "DMLogn8n Development Team"

__all__ = [
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitState",

    # Retry Handler
    "RetryHandler",
    "BackoffStrategy",

    # Error Classifier
    "ErrorClassifier",
    "ErrorSeverity",
    "ErrorCategory",

    # Recovery Manager
    "RecoveryManager",
    "RecoveryAction",

    # Middleware
    "ErrorHandlingMiddleware",

    # Monitoring
    "ErrorMonitor",
    "AlertManager",

    # Decorators
    "with_circuit_breaker",
    "with_retry",
    "with_error_handling",
    "circuit_breaker",
    "retry",
    "error_handler"
]