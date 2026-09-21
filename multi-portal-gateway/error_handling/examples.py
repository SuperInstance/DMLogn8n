"""
Integration Examples and Usage Patterns

Demonstrates how to integrate the error handling system with various
components and use cases in the DMLogn8n multi-agent platform.
"""

import asyncio
import time
import random
from typing import Optional

from . import (
    CircuitBreakerConfig, RetryConfig, BackoffStrategy,
    with_circuit_breaker, with_retry, with_error_handling, resilient,
    circuit_breaker, retry, error_handler
)
from .circuit_breaker import circuit_breaker_registry
from .retry_handler import retry_handler_registry
from .monitoring import error_monitor, EmailNotificationChannel, SlackNotificationChannel
from .error_classifier import ErrorCategory, ErrorSeverity
from .recovery_manager import recovery_manager
from .middleware import create_error_handling_middleware


# ============================================================================
# EXAMPLE 1: Basic Circuit Breaker Usage
# ============================================================================

@with_circuit_breaker(
    CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        name="ai_model_api"
    )
)
async def call_ai_model(prompt: str) -> str:
    """
    Example: AI model API call with circuit breaker protection.
    """
    # Simulate API call that might fail
    if random.random() < 0.3:  # 30% chance of failure
        raise ConnectionError("AI model service unavailable")

    await asyncio.sleep(0.5)  # Simulate network latency
    return f"AI response to: {prompt}"


# ============================================================================
# EXAMPLE 2: Retry with Exponential Backoff
# ============================================================================

@with_retry(
    RetryConfig(
        max_attempts=3,
        base_delay=1.0,
        backoff_strategy=BackoffStrategy.EXPONENTIAL,
        jitter=True
    )
)
async def unreliable_database_query(query: str) -> dict:
    """
    Example: Database query with retry logic.
    """
    # Simulate database that sometimes fails
    if random.random() < 0.4:  # 40% chance of failure
        raise TimeoutError("Database query timeout")

    await asyncio.sleep(0.2)
    return {"query": query, "results": ["data1", "data2"]}


# ============================================================================
# EXAMPLE 3: Comprehensive Error Handling
# ============================================================================

@with_error_handling(
    circuit_breaker=CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60.0,
        timeout=10.0
    ),
    retry=RetryConfig(
        max_attempts=3,
        base_delay=2.0,
        backoff_strategy=BackoffStrategy.EXPONENTIAL
    ),
    monitor=True,
    auto_recovery=True,
    fallback=lambda e, *args, **kwargs: {"fallback": "Using cached data"}
)
async def external_service_api_call(endpoint: str) -> dict:
    """
    Example: Comprehensive error handling for external service calls.
    """
    # Simulate external API call
    if random.random() < 0.2:  # 20% chance of failure
        raise ConnectionError(f"Failed to connect to {endpoint}")

    await asyncio.sleep(1.0)
    return {"endpoint": endpoint, "data": "external_data"}


# ============================================================================
# EXAMPLE 4: Shorthand Decorators
# ============================================================================

@resilient(max_attempts=3, failure_threshold=4)
async def critical_system_operation(data: dict) -> bool:
    """
    Example: Using the resilient shorthand decorator.
    """
    if random.random() < 0.25:  # 25% chance of failure
        raise RuntimeError("System operation failed")

    await asyncio.sleep(0.3)
    return True


@circuit_breaker(failure_threshold=3, recovery_timeout=30.0)
async def network_request(url: str) -> str:
    """
    Example: Simple circuit breaker decorator.
    """
    if random.random() < 0.3:
        raise ConnectionError("Network unreachable")

    return f"Response from {url}"


@retry(max_attempts=2, base_delay=0.5)
async def temporary_operation() -> int:
    """
    Example: Simple retry decorator.
    """
    if random.random() < 0.5:
        raise ValueError("Temporary failure")

    return 42


# ============================================================================
# EXAMPLE 5: Error Handling with Fallback
# ============================================================================

@error_handler(
    exception_types=[ConnectionError, TimeoutError],
    fallback=lambda e, url, *args, **kwargs: {"cached": f"Cached response for {url}"}
)
async def get_user_data(user_id: int, url: str) -> dict:
    """
    Example: Error handling with fallback to cached data.
    """
    if random.random() < 0.3:
        raise ConnectionError("User service unavailable")

    await asyncio.sleep(0.5)
    return {"user_id": user_id, "name": f"User {user_id}"}


# ============================================================================
# EXAMPLE 6: Class-based Error Handling
# ============================================================================

class AgentService:
    """
    Example: Service class with integrated error handling.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.circuit_breaker = circuit_breaker_registry.get_breaker(
            f"agent_{agent_id}",
            CircuitBreakerConfig(failure_threshold=3, name=f"agent_{agent_id}")
        )
        self.retry_handler = retry_handler_registry.get_handler(
            f"agent_{agent_id}",
            RetryConfig(max_attempts=2, name=f"agent_{agent_id}")
        )

    @with_circuit_breaker(name="agent_communication")
    async def communicate_with_agent(self, message: str) -> str:
        """
        Agent communication with circuit breaker protection.
        """
        if random.random() < 0.2:
            raise ConnectionError(f"Agent {self.agent_id} not responding")

        await asyncio.sleep(0.1)
        return f"Agent {self.agent_id}: Received '{message}'"

    @resilient(max_attempts=2, failure_threshold=3)
    async def process_task(self, task_data: dict) -> dict:
        """
        Task processing with comprehensive error handling.
        """
        if random.random() < 0.15:
            raise RuntimeError("Task processing failed")

        await asyncio.sleep(0.3)
        return {"task_id": task_data.get("id"), "status": "completed"}


# ============================================================================
# EXAMPLE 7: Custom Recovery Actions
# ============================================================================

class AIOperationError(Exception):
    """Custom error for AI operations."""
    pass


async def restart_ai_service(error_info, context):
    """Custom recovery action for AI service failures."""
    print(f"Restarting AI service due to: {error_info.message}")
    await asyncio.sleep(2)  # Simulate restart time
    return {"status": "restarted", "service": "ai_service"}


# Register custom recovery action
from .recovery_manager import RecoveryAction, RecoveryActionType

ai_recovery_action = RecoveryAction(
    name="restart_ai_service_custom",
    action_type=RecoveryActionType.CUSTOM,
    description="Custom AI service restart",
    applicable_categories=[ErrorCategory.AI_MODEL],
    parameters={"service_name": "ai_service"}
)

recovery_manager.register_action(ai_recovery_action)


@with_error_handling(
    auto_recovery=True,
    error_context={"component": "ai_processor"}
)
async def ai_processing_operation(input_data: str) -> str:
    """
    Example: AI operation with custom recovery.
    """
    if random.random() < 0.2:
        raise AIOperationError("AI model processing failed")

    await asyncio.sleep(0.8)
    return f"Processed: {input_data}"


# ============================================================================
# EXAMPLE 8: Integration with Web Frameworks
# ============================================================================

# FastAPI Integration Example
def setup_fastapi_error_handling(app):
    """
    Example: Setting up error handling for FastAPI application.
    """
    from .middleware import FastAPIErrorHandlingMiddleware

    # Create error handling middleware
    error_middleware = FastAPIErrorHandlingMiddleware(
        app,
        include_traceback=True,
        auto_recovery=True,
        log_errors=True
    )

    return error_middleware


# Flask Integration Example
def setup_flask_error_handling(app):
    """
    Example: Setting up error handling for Flask application.
    """
    from .middleware import FlaskErrorHandlingMiddleware

    # Add error handling to Flask app
    middleware = FlaskErrorHandlingMiddleware(app)

    return middleware


# ============================================================================
# EXAMPLE 9: Monitoring and Alerting Setup
# ============================================================================

def setup_monitoring_and_alerting():
    """
    Example: Setting up comprehensive monitoring and alerting.
    """
    # Start error monitoring
    error_monitor.start_monitoring(interval=60.0)

    # Add notification channels (example configurations)
    # Note: Replace with actual configuration
    try:
        # Email notifications
        email_channel = EmailNotificationChannel(
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            username="alerts@example.com",
            password="app_password",
            from_email="alerts@example.com",
            to_emails=["admin@example.com", "ops@example.com"]
        )
        error_monitor.alert_manager.add_notification_channel("email", email_channel)

        # Slack notifications
        slack_channel = SlackNotificationChannel(
            webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
            channel="#alerts"
        )
        error_monitor.alert_manager.add_notification_channel("slack", slack_channel)

    except Exception as e:
        print(f"Failed to setup notification channels: {e}")
        print("Please configure actual notification settings")


# ============================================================================
# EXAMPLE 10: Component-Specific Configuration
# ============================================================================

class DatabaseManager:
    """
    Example: Database manager with specialized error handling.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

        # Create database-specific circuit breaker
        self.db_circuit_breaker = circuit_breaker_registry.get_breaker(
            "database",
            CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=30.0,
                timeout=10.0,
                name="database"
            )
        )

        # Create database-specific retry handler
        self.db_retry_handler = retry_handler_registry.get_handler(
            "database",
            RetryConfig(
                max_attempts=3,
                base_delay=0.5,
                backoff_strategy=BackoffStrategy.EXPONENTIAL,
                name="database"
            )
        )

    @with_circuit_breaker(
        CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60.0,
            name="database_queries"
        )
    )
    async def execute_query(self, query: str) -> list:
        """
        Database query execution with circuit breaker.
        """
        if random.random() < 0.1:  # 10% chance of failure
            raise TimeoutError("Database query timeout")

        await asyncio.sleep(0.2)
        return [{"row": 1}, {"row": 2}]

    @with_retry(
        RetryConfig(
            max_attempts=2,
            base_delay=1.0,
            backoff_strategy=BackoffStrategy.LINEAR
        )
    )
    async def connect_to_database(self) -> bool:
        """
        Database connection with retry logic.
        """
        if random.random() < 0.2:  # 20% chance of failure
            raise ConnectionError("Cannot connect to database")

        await asyncio.sleep(0.5)
        return True


# ============================================================================
# EXAMPLE 11: Dashboard Integration
# ============================================================================

async def get_error_dashboard_data():
    """
    Example: Getting data for error monitoring dashboard.
    """
    dashboard_data = error_monitor.get_dashboard_data(time_window=3600.0)  # Last hour

    return {
        "total_errors": dashboard_data["snapshot"]["total_errors"],
        "errors_by_category": dashboard_data["snapshot"]["errors_by_category"],
        "errors_by_severity": dashboard_data["snapshot"]["errors_by_severity"],
        "recovery_rate": dashboard_data["snapshot"]["recovery_rate"],
        "recent_alerts": dashboard_data["recent_alerts"],
        "active_circuit_breakers": dashboard_data["snapshot"]["active_circuit_breakers"],
        "open_circuits": dashboard_data["snapshot"]["open_circuits"]
    }


# ============================================================================
# EXAMPLE 12: Testing and Demonstration
# ============================================================================

async def demonstrate_error_handling():
    """
    Example function to demonstrate error handling capabilities.
    """
    print("=== DMLogn8n Error Handling Demonstration ===\n")

    # Setup monitoring
    setup_monitoring_and_alerting()

    # Test 1: Circuit breaker
    print("1. Testing Circuit Breaker:")
    try:
        for i in range(10):
            result = await call_ai_model(f"Test message {i}")
            print(f"   Success: {result}")
    except Exception as e:
        print(f"   Circuit breaker opened: {e}")

    print("\n2. Testing Retry Logic:")
    try:
        result = await unreliable_database_query("SELECT * FROM users")
        print(f"   Query succeeded: {result}")
    except Exception as e:
        print(f"   All retries failed: {e}")

    print("\n3. Testing Comprehensive Error Handling:")
    try:
        result = await external_service_api_call("https://api.example.com/data")
        print(f"   API call succeeded: {result}")
    except Exception as e:
        print(f"   API call failed: {e}")

    print("\n4. Testing Resilient Operations:")
    try:
        result = await critical_system_operation({"id": 123})
        print(f"   Operation succeeded: {result}")
    except Exception as e:
        print(f"   Operation failed: {e}")

    print("\n5. Error Dashboard Data:")
    dashboard = await get_error_dashboard_data()
    print(f"   Total errors (last hour): {dashboard['total_errors']}")
    print(f"   Active circuit breakers: {dashboard['active_circuit_breakers']}")
    print(f"   Recovery rate: {dashboard['recovery_rate']:.2%}")

    print("\n=== Demonstration Complete ===")


if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demonstrate_error_handling())