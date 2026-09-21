"""
Error Classification and Routing System

Provides intelligent error classification, categorization, and routing
to appropriate handlers and recovery strategies.
"""

import re
import traceback
import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Type, Any, Callable, Tuple
from dataclasses import dataclass, field
import inspect

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "LOW"           # Non-critical, can be ignored
    MEDIUM = "MEDIUM"     # Should be handled but not urgent
    HIGH = "HIGH"         # Requires immediate attention
    CRITICAL = "CRITICAL" # System-threatening, requires escalation


class ErrorCategory(Enum):
    """Error categories for classification."""
    NETWORK = "NETWORK"               # Network-related errors
    DATABASE = "DATABASE"             # Database errors
    AI_MODEL = "AI_MODEL"             # AI model API errors
    AUTHENTICATION = "AUTHENTICATION" # Authentication/authorization errors
    VALIDATION = "VALIDATION"         # Input validation errors
    RESOURCE = "RESOURCE"             # Resource exhaustion errors
    SYSTEM = "SYSTEM"                 # System-level errors
    BUSINESS = "BUSINESS"             # Business logic errors
    TIMEOUT = "TIMEOUT"               # Timeout errors
    CONCURRENCY = "CONCURRENCY"       # Concurrency/locking errors
    UNKNOWN = "UNKNOWN"               # Unclassified errors


class ErrorUrgency(Enum):
    """Error urgency levels for routing."""
    IMMEDIATE = "IMMEDIATE"    # Handle immediately
    HIGH = "HIGH"             # Handle with high priority
    NORMAL = "NORMAL"         # Normal priority
    LOW = "LOW"              # Low priority
    BATCH = "BATCH"          # Can be handled in batch


@dataclass
class ErrorInfo:
    """Comprehensive error information."""
    exception: Exception
    category: ErrorCategory
    severity: ErrorSeverity
    urgency: ErrorUrgency
    message: str
    traceback_str: str
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)
    component: Optional[str] = None
    operation: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    """Decision for error routing."""
    handler_name: str
    priority: int
    retry_recommended: bool
    escalate: bool
    notify_users: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ErrorClassifier(ABC):
    """Abstract base class for error classifiers."""

    @abstractmethod
    def classify(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """Classify an exception and return error info."""
        pass


class PatternClassifier(ErrorClassifier):
    """Classifier based on error message patterns."""

    def __init__(self):
        self._patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[ErrorCategory, List[Tuple[str, ErrorSeverity, ErrorUrgency]]]:
        """Initialize error classification patterns."""
        return {
            ErrorCategory.NETWORK: [
                (r'connection.*refused|connection.*reset|connection.*timeout', ErrorSeverity.HIGH, ErrorUrgency.IMMEDIATE),
                (r'dns.*resolution.*failed|host.*not.*found', ErrorSeverity.HIGH, ErrorUrgency.HIGH),
                (r'ssl.*error|tls.*error|certificate.*error', ErrorSeverity.HIGH, ErrorUrgency.HIGH),
                (r'http.*timeout|request.*timeout', ErrorSeverity.MEDIUM, ErrorUrgency.NORMAL),
                (r'rate.*limit|quota.*exceeded', ErrorSeverity.MEDIUM, ErrorUrgency.NORMAL),
                (r'network.*unreachable', ErrorSeverity.HIGH, ErrorUrgency.IMMEDIATE)
            ],
            ErrorCategory.DATABASE: [
                (r'deadlock|lock.*timeout', ErrorSeverity.HIGH, ErrorUrgency.HIGH),
                (r'connection.*pool.*exhausted|too.*many.*connections', ErrorSeverity.HIGH, ErrorUrgency.IMMEDIATE),
                (r'table.*not.*found|column.*not.*found', ErrorSeverity.MEDIUM, ErrorUrgency.NORMAL),
                (r'constraint.*violation|duplicate.*key', ErrorSeverity.MEDIUM, ErrorUrgency.NORMAL),
                (r'database.*connection.*failed', ErrorSeverity.CRITICAL, ErrorUrgency.IMMEDIATE),
                (r'transaction.*rollback|savepoint', ErrorSeverity.MEDIUM, ErrorUrgency.NORMAL)
            ],
            ErrorCategory.AI_MODEL: [
                (r'api.*rate.*limit|model.*overloaded', ErrorSeverity.MEDIUM, ErrorUrgency.NORMAL),
                (r'token.*limit.*exceeded|context.*length', ErrorSeverity.MEDIUM, ErrorUrgency.NORMAL),
                (r'model.*not.*available|service.*unavailable', ErrorSeverity.HIGH, ErrorUrgency.HIGH),
                (r'invalid.*prompt|malformed.*request', ErrorSeverity.LOW, ErrorUrgency.LOW),
                (r'quota.*exceeded|billing.*issue', ErrorSeverity.HIGH, ErrorUrgency.HIGH),
                (r'timeout.*response|inference.*timeout', ErrorSeverity.MEDIUM, ErrorUrgency.NORMAL)
            ],
            ErrorCategory.AUTHENTICATION: [
                (r'unauthorized|access.*denied', ErrorSeverity.MEDIUM, ErrorUrgency.HIGH),
                (r'token.*expired|invalid.*token', ErrorSeverity.MEDIUM, ErrorUrgency.HIGH),
                (r'insufficient.*permissions|forbidden', ErrorSeverity.MEDIUM, ErrorUrgency.HIGH),
                (r'invalid.*credentials|authentication.*failed', ErrorSeverity.MEDIUM, ErrorUrgency.HIGH),
                (r'session.*expired', ErrorSeverity.LOW, ErrorUrgency.NORMAL)
            ],
            ErrorCategory.VALIDATION: [
                (r'invalid.*input|malformed.*data', ErrorSeverity.LOW, ErrorUrgency.LOW),
                (r'missing.*required.*field', ErrorSeverity.LOW, ErrorUrgency.LOW),
                (r'value.*out.*of.*range', ErrorSeverity.LOW, ErrorUrgency.LOW),
                (r'type.*error|conversion.*error', ErrorSeverity.LOW, ErrorUrgency.LOW)
            ],
            ErrorCategory.RESOURCE: [
                (r'memory.*error|out.*of.*memory', ErrorSeverity.CRITICAL, ErrorUrgency.IMMEDIATE),
                (r'disk.*space.*full|storage.*exhausted', ErrorSeverity.CRITICAL, ErrorUrgency.IMMEDIATE),
                (r'cpu.*overload|system.*overload', ErrorSeverity.HIGH, ErrorUrgency.IMMEDIATE),
                (r'thread.*pool.*exhausted', ErrorSeverity.HIGH, ErrorUrgency.HIGH),
                (r'file.*descriptor.*limit', ErrorSeverity.HIGH, ErrorUrgency.HIGH)
            ],
            ErrorCategory.TIMEOUT: [
                (r'timeout|timed.*out', ErrorSeverity.MEDIUM, ErrorUrgency.NORMAL),
                (r'deadline.*exceeded', ErrorSeverity.MEDIUM, ErrorUrgency.NORMAL),
                (r'operation.*cancelled', ErrorSeverity.LOW, ErrorUrgency.LOW)
            ],
            ErrorCategory.CONCURRENCY: [
                (r'race.*condition|concurrent.*modification', ErrorSeverity.MEDIUM, ErrorUrgency.HIGH),
                (r'optimistic.*lock.*failed', ErrorSeverity.MEDIUM, ErrorUrgency.NORMAL),
                (r'pessimistic.*lock.*timeout', ErrorSeverity.HIGH, ErrorUrgency.HIGH)
            ],
            ErrorCategory.SYSTEM: [
                (r'permission.*denied|access.*denied', ErrorSeverity.HIGH, ErrorUrgency.HIGH),
                (r'file.*not.*found|directory.*not.*found', ErrorSeverity.MEDIUM, ErrorUrgency.NORMAL),
                (r'os.*error|system.*error', ErrorSeverity.HIGH, ErrorUrgency.HIGH),
                (r'signal.*received|interrupted', ErrorSeverity.MEDIUM, ErrorUrgency.NORMAL)
            ]
        }

    def classify(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """Classify exception based on message patterns."""
        error_message = str(exception).lower()
        exception_type = type(exception).__name__
        full_message = f"{exception_type}: {error_message}"

        # Default classification
        category = ErrorCategory.UNKNOWN
        severity = ErrorSeverity.MEDIUM
        urgency = ErrorUrgency.NORMAL

        # Check patterns for each category
        for cat, patterns in self._patterns.items():
            for pattern, sev, urg in patterns:
                if re.search(pattern, error_message) or re.search(pattern, exception_type.lower()):
                    category = cat
                    severity = sev
                    urgency = urg
                    break
            if category != ErrorCategory.UNKNOWN:
                break

        # Exception type based classification as fallback
        if category == ErrorCategory.UNKNOWN:
            category, severity, urgency = self._classify_by_exception_type(exception)

        return ErrorInfo(
            exception=exception,
            category=category,
            severity=severity,
            urgency=urgency,
            message=full_message,
            traceback_str=traceback.format_exc(),
            timestamp=time.time(),
            context=context or {}
        )

    def _classify_by_exception_type(self, exception: Exception) -> Tuple[ErrorCategory, ErrorSeverity, ErrorUrgency]:
        """Classify by exception type as fallback."""
        exception_type = type(exception).__name__

        if exception_type in ['ConnectionError', 'HTTPError', 'TimeoutError']:
            return ErrorCategory.NETWORK, ErrorSeverity.HIGH, ErrorUrgency.IMMEDIATE
        elif exception_type in ['DatabaseError', 'IntegrityError', 'OperationalError']:
            return ErrorCategory.DATABASE, ErrorSeverity.HIGH, ErrorUrgency.HIGH
        elif exception_type in ['ValidationError', 'ValueError', 'TypeError']:
            return ErrorCategory.VALIDATION, ErrorSeverity.LOW, ErrorUrgency.LOW
        elif exception_type in ['PermissionError', 'OSError']:
            return ErrorCategory.SYSTEM, ErrorSeverity.MEDIUM, ErrorUrgency.NORMAL
        elif exception_type in ['MemoryError', 'OverflowError']:
            return ErrorCategory.RESOURCE, ErrorSeverity.CRITICAL, ErrorUrgency.IMMEDIATE
        elif 'Timeout' in exception_type:
            return ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM, ErrorUrgency.NORMAL
        elif exception_type in ['ImportError', 'ModuleNotFoundError']:
            return ErrorCategory.SYSTEM, ErrorSeverity.HIGH, ErrorUrgency.IMMEDIATE

        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM, ErrorUrgency.NORMAL


class RuleBasedClassifier(ErrorClassifier):
    """Classifier based on configurable rules."""

    def __init__(self):
        self._rules: List[Callable[[Exception, Dict[str, Any]], Optional[ErrorInfo]]] = []

    def add_rule(self, rule: Callable[[Exception, Dict[str, Any]], Optional[ErrorInfo]]) -> None:
        """Add a classification rule."""
        self._rules.append(rule)

    def classify(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """Classify using configured rules."""
        context = context or {}

        # Apply rules in order
        for rule in self._rules:
            try:
                result = rule(exception, context)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Error in classification rule: {e}")

        # Fallback to pattern classifier
        fallback_classifier = PatternClassifier()
        return fallback_classifier.classify(exception, context)


class ErrorRouter:
    """Routes classified errors to appropriate handlers."""

    def __init__(self):
        self._routes: Dict[ErrorCategory, List[Callable]] = {}
        self._handlers: Dict[str, Callable] = {}
        self._default_handler: Optional[Callable] = None

    def register_handler(self, name: str, handler: Callable) -> None:
        """Register an error handler."""
        self._handlers[name] = handler
        logger.info(f"Registered error handler: {name}")

    def register_route(self, category: ErrorCategory, handler_name: str) -> None:
        """Register a route from error category to handler."""
        if category not in self._routes:
            self._routes[category] = []
        self._routes[category].append(handler_name)
        logger.info(f"Registered route: {category.value} -> {handler_name}")

    def set_default_handler(self, handler_name: str) -> None:
        """Set default handler for unclassified errors."""
        self._default_handler = handler_name

    def route(self, error_info: ErrorInfo) -> RoutingDecision:
        """Route error to appropriate handler."""
        # Get handlers for this category
        handlers = self._routes.get(error_info.category, [])

        if not handlers:
            if self._default_handler:
                handlers = [self._default_handler]
            else:
                # No handler found
                return RoutingDecision(
                    handler_name="none",
                    priority=0,
                    retry_recommended=False,
                    escalate=False
                )

        # Choose handler (simple round-robin for now)
        handler_name = handlers[0] if handlers else "none"

        # Determine routing decisions based on error properties
        priority = self._calculate_priority(error_info)
        retry_recommended = self._should_retry(error_info)
        escalate = self._should_escalate(error_info)
        notify_users = self._get_users_to_notify(error_info)
        actions = self._get_recommended_actions(error_info)

        return RoutingDecision(
            handler_name=handler_name,
            priority=priority,
            retry_recommended=retry_recommended,
            escalate=escalate,
            notify_users=notify_users,
            actions=actions,
            metadata={"category": error_info.category.value, "severity": error_info.severity.value}
        )

    def _calculate_priority(self, error_info: ErrorInfo) -> int:
        """Calculate routing priority based on error severity and urgency."""
        urgency_priority = {
            ErrorUrgency.IMMEDIATE: 100,
            ErrorUrgency.HIGH: 80,
            ErrorUrgency.NORMAL: 50,
            ErrorUrgency.LOW: 20,
            ErrorUrgency.BATCH: 10
        }

        severity_priority = {
            ErrorSeverity.CRITICAL: 100,
            ErrorSeverity.HIGH: 80,
            ErrorSeverity.MEDIUM: 50,
            ErrorSeverity.LOW: 20
        }

        return urgency_priority.get(error_info.urgency, 50) + severity_priority.get(error_info.severity, 50)

    def _should_retry(self, error_info: ErrorInfo) -> bool:
        """Determine if error should be retried."""
        # Don't retry certain categories
        no_retry_categories = {
            ErrorCategory.VALIDATION,
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.RESOURCE
        }

        if error_info.category in no_retry_categories:
            return False

        # Retry network and timeout errors
        retry_categories = {
            ErrorCategory.NETWORK,
            ErrorCategory.TIMEOUT,
            ErrorCategory.AI_MODEL
        }

        return error_info.category in retry_categories

    def _should_escalate(self, error_info: ErrorInfo) -> bool:
        """Determine if error should be escalated."""
        return error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]

    def _get_users_to_notify(self, error_info: ErrorInfo) -> List[str]:
        """Get list of users to notify for this error."""
        notify_users = []

        if error_info.severity == ErrorSeverity.CRITICAL:
            notify_users.extend(["admin", "ops_team"])
        elif error_info.severity == ErrorSeverity.HIGH:
            notify_users.append("ops_team")
        elif error_info.category == ErrorCategory.AI_MODEL:
            notify_users.append("ai_team")

        # Add user from context if available
        if error_info.context.get("notify_user"):
            notify_users.append(error_info.context["notify_user"])

        return list(set(notify_users))

    def _get_recommended_actions(self, error_info: ErrorInfo) -> List[str]:
        """Get recommended actions for this error."""
        actions = []

        if error_info.category == ErrorCategory.NETWORK:
            actions.extend(["check_connectivity", "verify_endpoint"])
        elif error_info.category == ErrorCategory.DATABASE:
            actions.extend(["check_connection", "verify_schema"])
        elif error_info.category == ErrorCategory.AI_MODEL:
            actions.extend(["check_model_status", "verify_quota"])
        elif error_info.category == ErrorCategory.RESOURCE:
            actions.extend(["monitor_resources", "scale_up"])
        elif error_info.severity == ErrorSeverity.CRITICAL:
            actions.append("emergency_response")

        return actions


class ErrorClassificationSystem:
    """Main error classification and routing system."""

    def __init__(self):
        self._classifier = PatternClassifier()
        self._router = ErrorRouter()
        self._handlers: Dict[str, Callable] = {}

    def set_classifier(self, classifier: ErrorClassifier) -> None:
        """Set the error classifier."""
        self._classifier = classifier

    def classify_and_route(self, exception: Exception, context: Optional[Dict[str, Any]] = None) -> Tuple[ErrorInfo, RoutingDecision]:
        """
        Classify an exception and determine routing.

        Returns:
            Tuple of (error_info, routing_decision)
        """
        # Classify the error
        error_info = self._classifier.classify(exception, context)

        # Add additional context
        if context:
            error_info.context.update(context)
            error_info.component = context.get("component")
            error_info.operation = context.get("operation")
            error_info.user_id = context.get("user_id")
            error_info.session_id = context.get("session_id")
            error_info.request_id = context.get("request_id")

        # Route the error
        routing_decision = self._router.route(error_info)

        logger.info(
            f"Error classified: {error_info.category.value} "
            f"({error_info.severity.value}) -> {routing_decision.handler_name}"
        )

        return error_info, routing_decision

    def register_handler(self, name: str, handler: Callable) -> None:
        """Register an error handler."""
        self._router.register_handler(name, handler)
        self._handlers[name] = handler

    def register_route(self, category: ErrorCategory, handler_name: str) -> None:
        """Register a route from error category to handler."""
        self._router.register_route(category, handler_name)

    def set_default_handler(self, handler_name: str) -> None:
        """Set default handler for unclassified errors."""
        self._router.set_default_handler(handler_name)


# Global error classification system
error_classification_system = ErrorClassificationSystem()