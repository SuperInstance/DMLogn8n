#!/usr/bin/env python3
"""
DMLogn8n Feature Flag System Error Handling and Logging
Production-ready error handling, logging, and monitoring for the feature flag system
"""

import asyncio
import json
import logging
import sys
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import functools
import time
import uuid
from pathlib import Path

# Third-party imports
import structlog
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import sentry_sdk
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class ErrorSeverity(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    SYSTEM = "system"
    NETWORK = "network"
    DATABASE = "database"
    BUSINESS_LOGIC = "business_logic"
    USER_INPUT = "user_input"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMITING = "rate_limiting"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"

@dataclass
class ErrorContext:
    request_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    feature_flag: Optional[str] = None
    experiment_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    additional_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}

@dataclass
class ErrorDetails:
    error_id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    exception_type: str
    stack_trace: str
    context: ErrorContext
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    resolution_notes: Optional[str] = None

class FeatureFlagError(Exception):
    """Base exception for feature flag system errors"""
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.SYSTEM, severity: ErrorSeverity = ErrorSeverity.ERROR, context: ErrorContext = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context
        self.timestamp = datetime.utcnow()

class ValidationError(FeatureFlagError):
    """Raised when input validation fails"""
    def __init__(self, message: str, field: str = None, value: Any = None, context: ErrorContext = None):
        super().__init__(message, ErrorCategory.USER_INPUT, ErrorSeverity.WARNING, context)
        self.field = field
        self.value = value

class ConfigurationError(FeatureFlagError):
    """Raised when configuration is invalid"""
    def __init__(self, message: str, config_key: str = None, context: ErrorContext = None):
        super().__init__(message, ErrorCategory.SYSTEM, ErrorSeverity.ERROR, context)
        self.config_key = config_key

class DatabaseError(FeatureFlagError):
    """Raised when database operations fail"""
    def __init__(self, message: str, operation: str = None, table: str = None, context: ErrorContext = None):
        super().__init__(message, ErrorCategory.DATABASE, ErrorSeverity.ERROR, context)
        self.operation = operation
        self.table = table

class NetworkError(FeatureFlagError):
    """Raised when network operations fail"""
    def __init__(self, message: str, endpoint: str = None, status_code: int = None, context: ErrorContext = None):
        super().__init__(message, ErrorCategory.NETWORK, ErrorSeverity.WARNING, context)
        self.endpoint = endpoint
        self.status_code = status_code

class RateLimitError(FeatureFlagError):
    """Raised when rate limits are exceeded"""
    def __init__(self, message: str, limit: int = None, window: int = None, context: ErrorContext = None):
        super().__init__(message, ErrorCategory.RATE_LIMITING, ErrorSeverity.WARNING, context)
        self.limit = limit
        self.window = window

class PerformanceError(FeatureFlagError):
    """Raised when performance thresholds are exceeded"""
    def __init__(self, message: str, metric: str = None, threshold: float = None, actual_value: float = None, context: ErrorContext = None):
        super().__init__(message, ErrorCategory.PERFORMANCE, ErrorSeverity.WARNING, context)
        self.metric = metric
        self.threshold = threshold
        self.actual_value = actual_value

class ErrorHandler:
    """Centralized error handling and logging system"""

    def __init__(
        self,
        service_name: str = "feature-flags",
        environment: str = "development",
        sentry_dsn: str = None,
        log_level: str = "INFO",
        metrics_port: int = 8000,
        enable_structured_logging: bool = True,
        log_file_path: str = None
    ):
        self.service_name = service_name
        self.environment = environment
        self.sentry_dsn = sentry_dsn
        self.metrics_port = metrics_port
        self.enable_structured_logging = enable_structured_logging
        self.log_file_path = log_file_path

        # Error tracking
        self.error_history: List[ErrorDetails] = []
        self.error_counts: Dict[str, int] = {}
        self.error_handlers: Dict[type, List[Callable]] = {}

        # Metrics
        self._setup_metrics()

        # Logging
        self._setup_logging(log_level)

        # Sentry integration
        self._setup_sentry()

        # Performance monitoring
        self._setup_performance_monitoring()

    def _setup_metrics(self):
        """Setup Prometheus metrics"""
        self.error_counter = Counter(
            'feature_flag_errors_total',
            'Total number of errors in feature flag system',
            ['service', 'severity', 'category', 'component']
        )

        self.error_duration = Histogram(
            'feature_flag_error_duration_seconds',
            'Time spent handling errors',
            ['service', 'severity', 'category']
        )

        self.active_errors = Gauge(
            'feature_flag_active_errors',
            'Number of currently active errors',
            ['service']
        )

        self.resolution_time = Histogram(
            'feature_flag_error_resolution_time_seconds',
            'Time taken to resolve errors',
            ['service', 'category']
        )

    def _setup_logging(self, log_level: str):
        """Setup structured logging"""
        if self.enable_structured_logging:
            # Configure structlog
            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.PositionalArgumentsFormatter(),
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    structlog.processors.JSONRenderer()
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )

        # Configure standard logging
        log_level_int = getattr(logging, log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level_int,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                *([logging.FileHandler(self.log_file_path)] if self.log_file_path else [])
            ]
        )

        self.logger = structlog.get_logger(self.service_name)

        # Start metrics server
        if self.metrics_port:
            start_http_server(self.metrics_port)
            self.logger.info(f"Metrics server started on port {self.metrics_port}")

    def _setup_sentry(self):
        """Setup Sentry integration"""
        if self.sentry_dsn:
            sentry_sdk.init(
                dsn=self.sentry_dsn,
                environment=self.environment,
                integrations=[
                    RedisIntegration(),
                    FastApiIntegration(auto_enabling_integrations=False),
                ],
                traces_sample_rate=0.1,
                ignore_errors=[KeyboardInterrupt, SystemExit],
                before_send=self._before_sentry_send
            )
            self.logger.info("Sentry integration enabled")

    def _before_sentry_send(self, event, hint):
        """Filter and enhance Sentry events"""
        if 'exc_info' in hint:
            exception = hint['exc_info'][1]
            # Don't send certain exception types to Sentry
            if isinstance(exception, (ValidationError, RateLimitError)):
                return None

        # Add custom context
        event['tags'] = {
            'service': self.service_name,
            'environment': self.environment,
            **event.get('tags', {})
        }

        return event

    def _setup_performance_monitoring(self):
        """Setup performance monitoring"""
        self.performance_thresholds = {
            'flag_evaluation': 100,  # ms
            'database_query': 50,    # ms
            'api_request': 500,     # ms
            'cache_operation': 10   # ms
        }

    def handle_error(
        self,
        error: Exception,
        context: ErrorContext = None,
        additional_data: Dict[str, Any] = None
    ) -> ErrorDetails:
        """Handle and log an error"""
        start_time = time.time()

        # Create error details
        error_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()

        if context is None:
            context = ErrorContext(request_id=error_id)

        if additional_data:
            context.additional_data.update(additional_data)

        # Determine error details
        if isinstance(error, FeatureFlagError):
            severity = error.severity
            category = error.category
            message = error.message
        else:
            severity = ErrorSeverity.ERROR
            category = ErrorCategory.SYSTEM
            message = str(error)

        # Create error details object
        error_details = ErrorDetails(
            error_id=error_id,
            timestamp=timestamp,
            severity=severity,
            category=category,
            message=message,
            exception_type=type(error).__name__,
            stack_trace=traceback.format_exc(),
            context=context
        )

        # Log the error
        self._log_error(error_details)

        # Update metrics
        self._update_error_metrics(error_details)

        # Store error in history
        self._store_error(error_details)

        # Call custom error handlers
        self._call_error_handlers(error, error_details)

        # Track performance
        duration = time.time() - start_time
        self.error_duration.labels(
            service=self.service_name,
            severity=severity.value,
            category=category.value
        ).observe(duration)

        # Send to Sentry if critical
        if severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            self._send_to_sentry(error, error_details)

        return error_details

    def _log_error(self, error_details: ErrorDetails):
        """Log error using structured logging"""
        log_method = {
            ErrorSeverity.DEBUG: self.logger.debug,
            ErrorSeverity.INFO: self.logger.info,
            ErrorSeverity.WARNING: self.logger.warning,
            ErrorSeverity.ERROR: self.logger.error,
            ErrorSeverity.CRITICAL: self.logger.critical
        }.get(error_details.severity, self.logger.error)

        log_method(
            "error_occurred",
            error_id=error_details.error_id,
            severity=error_details.severity.value,
            category=error_details.category.value,
            message=error_details.message,
            exception_type=error_details.exception_type,
            component=error_details.context.component,
            operation=error_details.context.operation,
            user_id=error_details.context.user_id,
            feature_flag=error_details.context.feature_flag,
            experiment_id=error_details.context.experiment_id,
            **error_details.context.additional_data
        )

    def _update_error_metrics(self, error_details: ErrorDetails):
        """Update error metrics"""
        self.error_counter.labels(
            service=self.service_name,
            severity=error_details.severity.value,
            category=error_details.category.value,
            component=error_details.context.component or "unknown"
        ).inc()

        # Track active errors
        active_count = sum(1 for e in self.error_history if not e.resolved)
        self.active_errors.labels(service=self.service_name).set(active_count)

        # Track error counts by type
        error_key = f"{error_details.category.value}:{error_details.exception_type}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

    def _store_error(self, error_details: ErrorDetails):
        """Store error in history"""
        self.error_history.append(error_details)

        # Keep only recent errors (last 1000)
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]

    def _call_error_handlers(self, error: Exception, error_details: ErrorDetails):
        """Call custom error handlers"""
        error_type = type(error)
        if error_type in self.error_handlers:
            for handler in self.error_handlers[error_type]:
                try:
                    handler(error, error_details)
                except Exception as handler_error:
                    self.logger.error(
                        "error_handler_failed",
                        handler=str(handler),
                        handler_error=str(handler_error)
                    )

    def _send_to_sentry(self, error: Exception, error_details: ErrorDetails):
        """Send error to Sentry"""
        if self.sentry_dsn:
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag("error_id", error_details.error_id)
                scope.set_tag("component", error_details.context.component or "unknown")
                scope.set_tag("operation", error_details.context.operation or "unknown")
                scope.set_context("feature_flags", {
                    "feature_flag": error_details.context.feature_flag,
                    "experiment_id": error_details.context.experiment_id,
                    "user_id": error_details.context.user_id,
                    "request_id": error_details.context.request_id
                })
                scope.set_extra("error_category", error_details.category.value)
                scope.set_extra("error_severity", error_details.severity.value)

                sentry_sdk.capture_exception(error)

    def resolve_error(
        self,
        error_id: str,
        resolution_notes: str = None
    ) -> bool:
        """Mark an error as resolved"""
        for error in self.error_history:
            if error.error_id == error_id and not error.resolved:
                error.resolved = True
                error.resolution_time = datetime.utcnow()
                error.resolution_notes = resolution_notes

                # Update resolution time metric
                resolution_duration = (error.resolution_time - error.timestamp).total_seconds()
                self.resolution_time.labels(
                    service=self.service_name,
                    category=error.category.value
                ).observe(resolution_duration)

                self.logger.info(
                    "error_resolved",
                    error_id=error_id,
                    resolution_time=error.resolution_time.isoformat(),
                    resolution_notes=resolution_notes
                )
                return True

        return False

    def add_error_handler(self, exception_type: type, handler: Callable):
        """Add custom error handler for specific exception type"""
        if exception_type not in self.error_handlers:
            self.error_handlers[exception_type] = []
        self.error_handlers[exception_type].append(handler)

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)

        recent_errors = [e for e in self.error_history if e.timestamp >= last_hour]
        daily_errors = [e for e in self.error_history if e.timestamp >= last_day]

        active_errors = [e for e in self.error_history if not e.resolved]

        return {
            "total_errors": len(self.error_history),
            "active_errors": len(active_errors),
            "last_hour_errors": len(recent_errors),
            "last_day_errors": len(daily_errors),
            "error_counts_by_type": self.error_counts.copy(),
            "most_common_errors": sorted(
                self.error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

    def create_error_context(
        self,
        request_id: str = None,
        user_id: str = None,
        session_id: str = None,
        feature_flag: str = None,
        experiment_id: str = None,
        component: str = None,
        operation: str = None,
        **additional_data
    ) -> ErrorContext:
        """Create error context"""
        if request_id is None:
            request_id = str(uuid.uuid4())

        return ErrorContext(
            request_id=request_id,
            user_id=user_id,
            session_id=session_id,
            feature_flag=feature_flag,
            experiment_id=experiment_id,
            component=component,
            operation=operation,
            additional_data=additional_data
        )

    def check_performance_threshold(self, metric: str, value: float, context: ErrorContext = None):
        """Check if performance thresholds are exceeded"""
        if metric in self.performance_thresholds:
            threshold = self.performance_thresholds[metric]
            if value > threshold:
                self.handle_error(
                    PerformanceError(
                        f"Performance threshold exceeded for {metric}: {value}ms > {threshold}ms",
                        metric=metric,
                        threshold=threshold,
                        actual_value=value,
                        context=context
                    )
                )

# Decorators for error handling and monitoring
def monitor_errors(component: str = None):
    """Decorator to monitor errors in functions"""
    def decorator(func):
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = get_error_handler()
                context = error_handler.create_error_context(
                    component=component,
                    operation=f"{func.__module__}.{func.__name__}"
                )
                error_handler.handle_error(e, context)
                raise

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_handler = get_error_handler()
                context = error_handler.create_error_context(
                    component=component,
                    operation=f"{func.__module__}.{func.__name__}"
                )
                error_handler.handle_error(e, context)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

def monitor_performance(metric: str = None):
    """Decorator to monitor performance of functions"""
    def decorator(func):
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = (time.time() - start_time) * 1000  # Convert to ms
                error_handler = get_error_handler()
                error_handler.check_performance_threshold(
                    metric or func.__name__,
                    duration
                )

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = (time.time() - start_time) * 1000  # Convert to ms
                error_handler = get_error_handler()
                error_handler.check_performance_threshold(
                    metric or func.__name__,
                    duration
                )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

def retry_on_error(
    max_attempts: int = 3,
    wait_seconds: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """Decorator to retry functions on specific exceptions"""
    def decorator(func):
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=wait_seconds, max=10),
            retry=retry_if_exception_type(exceptions),
            reraise=True
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper
    return decorator

# Global error handler instance
_error_handler: ErrorHandler = None

def get_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

def initialize_error_handler(**kwargs):
    """Initialize global error handler"""
    global _error_handler
    _error_handler = ErrorHandler(**kwargs)
    return _error_handler

# Context manager for error handling
class ErrorContext:
    """Context manager for error handling with automatic context creation"""
    def __init__(
        self,
        component: str = None,
        operation: str = None,
        user_id: str = None,
        feature_flag: str = None,
        experiment_id: str = None,
        **additional_data
    ):
        self.component = component
        self.operation = operation
        self.user_id = user_id
        self.feature_flag = feature_flag
        self.experiment_id = experiment_id
        self.additional_data = additional_data
        self.error_handler = get_error_handler()
        self.context = None

    def __enter__(self):
        self.context = self.error_handler.create_error_context(
            component=self.component,
            operation=self.operation,
            user_id=self.user_id,
            feature_flag=self.feature_flag,
            experiment_id=self.experiment_id,
            **self.additional_data
        )
        return self.context

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error_handler.handle_error(exc_val, self.context)
        return False  # Don't suppress exceptions

# Health check functionality
class HealthChecker:
    """Health checking system for feature flag services"""

    def __init__(self, error_handler: ErrorHandler = None):
        self.error_handler = error_handler or get_error_handler()
        self.health_checks: Dict[str, Callable] = {}
        self.last_check_results: Dict[str, Dict[str, Any]] = {}

    def add_health_check(self, name: str, check_func: Callable):
        """Add a health check function"""
        self.health_checks[name] = check_func

    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_healthy = True

        for name, check_func in self.health_checks.items():
            try:
                start_time = time.time()
                result = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
                duration = time.time() - start_time

                health_status = {
                    "healthy": True,
                    "message": "OK",
                    "duration_seconds": duration,
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": result if isinstance(result, dict) else {}
                }
            except Exception as e:
                overall_healthy = False
                health_status = {
                    "healthy": False,
                    "message": str(e),
                    "duration_seconds": time.time() - start_time,
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {"error_type": type(e).__name__}
                }

                # Log the health check failure
                context = self.error_handler.create_error_context(
                    component="health_check",
                    operation=name
                )
                self.error_handler.handle_error(e, context)

            results[name] = health_status
            self.last_check_results[name] = health_status

        return {
            "healthy": overall_healthy,
            "checks": results,
            "timestamp": datetime.utcnow().isoformat()
        }

# Circuit breaker pattern for resilient operations
class CircuitBreaker:
    """Circuit breaker for resilient operations"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN")

            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise

        return wrapper

    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )

    def _on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

# Example usage and initialization
if __name__ == "__main__":
    # Initialize error handler
    error_handler = initialize_error_handler(
        service_name="feature-flags",
        environment="production",
        sentry_dsn="your-sentry-dsn-here",
        log_level="INFO",
        metrics_port=8000,
        enable_structured_logging=True,
        log_file_path="/var/log/feature-flags/app.log"
    )

    # Add custom error handlers
    def handle_database_error(error: DatabaseError, error_details: ErrorDetails):
        print(f"Database error occurred: {error.message}")
        # Implement database-specific error handling

    error_handler.add_error_handler(DatabaseError, handle_database_error)

    # Add health checks
    health_checker = HealthChecker(error_handler)

    def check_redis_connection():
        # Implement Redis connection check
        return {"status": "connected", "response_time_ms": 5}

    health_checker.add_health_check("redis", check_redis_connection)

    print("Error handling system initialized successfully")
    print(f"Error statistics: {error_handler.get_error_statistics()}")