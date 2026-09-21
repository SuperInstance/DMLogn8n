"""
Error Handling Middleware for APIs

Provides comprehensive error handling middleware for web frameworks
including FastAPI, Flask, and generic WSGI applications.
"""

import json
import time
import traceback
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
import asyncio

from .error_classifier import error_classification_system, ErrorInfo
from .recovery_manager import recovery_manager
from .circuit_breaker import circuit_breaker_registry
from .retry_handler import retry_handler_registry

logger = logging.getLogger(__name__)


@dataclass
class ErrorContext:
    """Context information for error handling."""
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: float = 0.0
    additional_context: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_context is None:
            self.additional_context = {}
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class ErrorResponse:
    """Standardized error response structure."""
    error_id: str
    message: str
    error_type: str
    category: str
    severity: str
    timestamp: float
    request_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    retry_after: Optional[float] = None
    recoverable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        result = {
            "error_id": self.error_id,
            "message": self.message,
            "error_type": self.error_type,
            "category": self.category,
            "severity": self.severity,
            "timestamp": self.timestamp,
            "recoverable": self.recoverable
        }

        if self.request_id:
            result["request_id"] = self.request_id

        if self.details:
            result["details"] = self.details

        if self.retry_after:
            result["retry_after"] = self.retry_after

        return result


class ErrorHandlingMiddleware:
    """
    Base error handling middleware that can be adapted for different frameworks.
    """

    def __init__(self,
                 include_traceback: bool = False,
                 auto_recovery: bool = True,
                 log_errors: bool = True,
                 custom_handlers: Optional[Dict[str, Callable]] = None):
        self.include_traceback = include_traceback
        self.auto_recovery = auto_recovery
        self.log_errors = log_errors
        self.custom_handlers = custom_handlers or {}

    def handle_error(self,
                     exception: Exception,
                     context: ErrorContext) -> ErrorResponse:
        """
        Handle an error and return standardized error response.

        Args:
            exception: The exception that occurred
            context: Error context information

        Returns:
            ErrorResponse with standardized format
        """
        # Generate error ID
        error_id = f"ERR_{int(time.time() * 1000)}_{id(exception)}"

        # Classify the error
        error_info, routing_decision = error_classification_system.classify_and_route(
            exception,
            context={
                "component": context.endpoint,
                "operation": context.method,
                "user_id": context.user_id,
                "session_id": context.session_id,
                "request_id": context.request_id,
                **context.additional_context
            }
        )

        # Log the error
        if self.log_errors:
            self._log_error(error_info, context, error_id)

        # Attempt recovery if enabled
        recovery_result = None
        if self.auto_recovery and routing_decision.retry_recommended:
            recovery_result = self._attempt_recovery(error_info, routing_decision)

        # Create error response
        error_response = ErrorResponse(
            error_id=error_id,
            message=self._sanitize_message(str(exception)),
            error_type=type(exception).__name__,
            category=error_info.category.value,
            severity=error_info.severity.value,
            timestamp=time.time(),
            request_id=context.request_id,
            details=self._build_error_details(error_info, context, recovery_result),
            retry_after=self._calculate_retry_after(error_info),
            recoverable=routing_decision.retry_recommended
        )

        # Check for custom handlers
        custom_handler = self.custom_handlers.get(error_info.category.value)
        if custom_handler:
            try:
                custom_result = custom_handler(exception, context, error_response)
                if custom_result:
                    error_response = custom_result
            except Exception as handler_error:
                logger.error(f"Custom error handler failed: {handler_error}")

        return error_response

    def _log_error(self, error_info: ErrorInfo, context: ErrorContext, error_id: str) -> None:
        """Log the error with appropriate level."""
        log_message = (
            f"Error {error_id}: {error_info.message} | "
            f"Category: {error_info.category.value} | "
            f"Severity: {error_info.severity.value} | "
            f"Endpoint: {context.endpoint} | "
            f"Method: {context.method} | "
            f"User: {context.user_id}"
        )

        if error_info.severity.value == "CRITICAL":
            logger.critical(log_message)
        elif error_info.severity.value == "HIGH":
            logger.error(log_message)
        elif error_info.severity.value == "MEDIUM":
            logger.warning(log_message)
        else:
            logger.info(log_message)

        # Include traceback if enabled
        if self.include_traceback:
            logger.debug(f"Error {error_id} traceback:\n{error_info.traceback_str}")

    def _attempt_recovery(self, error_info: ErrorInfo, routing_decision) -> Optional[Dict[str, Any]]:
        """Attempt automatic recovery for the error."""
        try:
            # Get applicable recovery actions
            applicable_actions = recovery_manager.get_applicable_actions(error_info)

            if applicable_actions:
                # Execute the first applicable action
                action = applicable_actions[0]
                execution = asyncio.run(
                    recovery_manager.execute_recovery(action.name, error_info)
                )

                if execution.status.value == "SUCCESS":
                    return {
                        "recovery_action": action.name,
                        "recovery_status": execution.status.value,
                        "recovery_result": execution.result
                    }

        except Exception as recovery_error:
            logger.error(f"Recovery attempt failed: {recovery_error}")

        return None

    def _sanitize_message(self, message: str) -> str:
        """Sanitize error message for client consumption."""
        # Remove sensitive information
        sensitive_patterns = [
            r'password',
            r'token',
            r'key',
            r'secret',
            r'credential'
        ]

        sanitized = message
        for pattern in sensitive_patterns:
            sanitized = re.sub(f'{pattern}[=:]\s*\S+', f'{pattern}=***', sanitized, flags=re.IGNORECASE)

        # Limit length
        if len(sanitized) > 500:
            sanitized = sanitized[:497] + "..."

        return sanitized

    def _build_error_details(self, error_info: ErrorInfo, context: ErrorContext, recovery_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build detailed error information."""
        details = {
            "category": error_info.category.value,
            "severity": error_info.severity.value,
            "timestamp": error_info.timestamp,
            "endpoint": context.endpoint,
            "method": context.method
        }

        # Add recovery information if available
        if recovery_result:
            details["recovery"] = recovery_result

        # Add context information if not sensitive
        if context.additional_context:
            safe_context = {k: v for k, v in context.additional_context.items()
                          if not any(sensitive in k.lower() for sensitive in ['password', 'token', 'key', 'secret'])}
            if safe_context:
                details["context"] = safe_context

        return details

    def _calculate_retry_after(self, error_info: ErrorInfo) -> Optional[float]:
        """Calculate recommended retry-after time."""
        # Different retry times based on error category
        retry_times = {
            "NETWORK": 5.0,
            "AI_MODEL": 10.0,
            "DATABASE": 2.0,
            "TIMEOUT": 3.0,
            "RESOURCE": 30.0
        }

        return retry_times.get(error_info.category.value, 5.0)


class FastAPIErrorHandlingMiddleware(ErrorHandlingMiddleware):
    """FastAPI-specific error handling middleware."""

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

    async def __call__(self, scope, receive, send):
        """ASGI middleware call."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Create error context
        context = self._create_fastapi_context(scope)

        try:
            await self.app(scope, receive, send)
        except Exception as exception:
            # Handle the error
            error_response = self.handle_error(exception, context)

            # Send error response
            await self._send_fastapi_error_response(scope, send, error_response)

    def _create_fastapi_context(self, scope) -> ErrorContext:
        """Create error context from FastAPI scope."""
        headers = dict(scope.get("headers", []))

        return ErrorContext(
            request_id=headers.get(b"x-request-id", b"").decode(),
            user_id=headers.get(b"x-user-id", b"").decode(),
            session_id=headers.get(b"x-session-id", b"").decode(),
            endpoint=scope.get("path", ""),
            method=scope.get("method", ""),
            ip_address=scope.get("client", [""])[0],
            user_agent=headers.get(b"user-agent", b"").decode()
        )

    async def _send_fastapi_error_response(self, scope, send, error_response: ErrorResponse):
        """Send error response via ASGI."""
        status_code = self._get_status_code(error_response.category)

        response_body = json.dumps(error_response.to_dict()).encode('utf-8')

        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(response_body)).encode()),
            (b"x-error-id", error_response.error_id.encode())
        ]

        if error_response.retry_after:
            headers.append((b"retry-after", str(error_response.retry_after).encode()))

        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": headers
        })

        await send({
            "type": "http.response.body",
            "body": response_body
        })

    def _get_status_code(self, category: str) -> int:
        """Get HTTP status code based on error category."""
        status_codes = {
            "VALIDATION": 400,
            "AUTHENTICATION": 401,
            "BUSINESS": 422,
            "NETWORK": 502,
            "AI_MODEL": 503,
            "DATABASE": 500,
            "RESOURCE": 503,
            "SYSTEM": 500,
            "TIMEOUT": 408,
            "CONCURRENCY": 409,
            "UNKNOWN": 500
        }

        return status_codes.get(category, 500)


class FlaskErrorHandlingMiddleware(ErrorHandlingMiddleware):
    """Flask-specific error handling middleware."""

    def __init__(self, app=None, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize middleware with Flask app."""
        app.errorhandler(Exception)(self._handle_flask_error)
        self.app = app

    def _handle_flask_error(self, exception):
        """Handle Flask error."""
        from flask import request, jsonify

        # Create error context
        context = ErrorContext(
            request_id=request.headers.get('X-Request-ID'),
            user_id=request.headers.get('X-User-ID'),
            session_id=request.headers.get('X-Session-ID'),
            endpoint=request.endpoint,
            method=request.method,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        # Handle the error
        error_response = self.handle_error(exception, context)

        # Return JSON response
        status_code = self._get_status_code(error_response.category)
        return jsonify(error_response.to_dict()), status_code


class DjangoErrorHandlingMiddleware(ErrorHandlingMiddleware):
    """Django-specific error handling middleware."""

    def __init__(self, get_response, **kwargs):
        super().__init__(**kwargs)
        self.get_response = get_response

    def __call__(self, request):
        """Django middleware call."""
        # Create error context
        context = self._create_django_context(request)

        try:
            response = self.get_response(request)
            return response
        except Exception as exception:
            # Handle the error
            error_response = self.handle_error(exception, context)

            # Return Django response
            from django.http import JsonResponse
            status_code = self._get_status_code(error_response.category)
            return JsonResponse(error_response.to_dict(), status=status_code)

    def _create_django_context(self, request) -> ErrorContext:
        """Create error context from Django request."""
        return ErrorContext(
            request_id=request.META.get('HTTP_X_REQUEST_ID'),
            user_id=getattr(request, 'user', None).id if hasattr(request, 'user') and request.user.is_authenticated else None,
            session_id=request.session.session_key if hasattr(request, 'session') else None,
            endpoint=request.resolver_match.url_name if hasattr(request, 'resolver_match') else '',
            method=request.method,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )

    def _get_client_ip(self, request):
        """Get client IP address from Django request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class GenericWSGIErrorHandlingMiddleware(ErrorHandlingMiddleware):
    """Generic WSGI error handling middleware."""

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

    def __call__(self, environ, start_response):
        """WSGI application call."""
        # Create error context
        context = self._create_wsgi_context(environ)

        try:
            return self.app(environ, start_response)
        except Exception as exception:
            # Handle the error
            error_response = self.handle_error(exception, context)

            # Send error response
            return self._send_wsgi_error_response(start_response, error_response)

    def _create_wsgi_context(self, environ) -> ErrorContext:
        """Create error context from WSGI environ."""
        return ErrorContext(
            request_id=environ.get('HTTP_X_REQUEST_ID'),
            user_id=environ.get('HTTP_X_USER_ID'),
            session_id=environ.get('HTTP_X_SESSION_ID'),
            endpoint=environ.get('PATH_INFO', ''),
            method=environ.get('REQUEST_METHOD', ''),
            ip_address=environ.get('REMOTE_ADDR', ''),
            user_agent=environ.get('HTTP_USER_AGENT', '')
        )

    def _send_wsgi_error_response(self, start_response, error_response: ErrorResponse):
        """Send error response via WSGI."""
        status_code = self._get_status_code(error_response.category)
        status = f"{status_code} Error"

        response_body = json.dumps(error_response.to_dict())

        headers = [
            ('Content-Type', 'application/json'),
            ('Content-Length', str(len(response_body))),
            ('X-Error-ID', error_response.error_id)
        ]

        if error_response.retry_after:
            headers.append(('Retry-After', str(error_response.retry_after)))

        start_response(status, headers)
        return [response_body.encode('utf-8')]


def create_error_handling_middleware(framework: str, app=None, **kwargs):
    """
    Factory function to create framework-specific error handling middleware.

    Args:
        framework: Framework name ('fastapi', 'flask', 'django', 'wsgi')
        app: Application instance (if required)
        **kwargs: Additional configuration options

    Returns:
        Framework-specific middleware instance
    """
    if framework.lower() == 'fastapi':
        return FastAPIErrorHandlingMiddleware(app, **kwargs)
    elif framework.lower() == 'flask':
        return FlaskErrorHandlingMiddleware(app, **kwargs)
    elif framework.lower() == 'django':
        return DjangoErrorHandlingMiddleware(app, **kwargs)
    elif framework.lower() == 'wsgi':
        return GenericWSGIErrorHandlingMiddleware(app, **kwargs)
    else:
        raise ValueError(f"Unsupported framework: {framework}")


# Import re for pattern matching
import re