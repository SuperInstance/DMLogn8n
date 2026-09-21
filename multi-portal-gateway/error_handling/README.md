# DMLogn8n Error Handling and Recovery System

A comprehensive, enterprise-grade error handling and recovery system for the DMLogn8n multi-agent platform. This system provides circuit breaker patterns, retry mechanisms, error classification, automated recovery, and comprehensive monitoring.

## Features

### 🛡️ **Circuit Breaker Pattern**
- Prevents cascading failures
- Fast failure when services are unavailable
- Configurable failure thresholds and recovery timeouts
- Automatic state transitions (CLOSED → OPEN → HALF_OPEN)
- Comprehensive metrics and monitoring

### 🔄 **Retry Mechanisms**
- Multiple backoff strategies (exponential, linear, fixed, fibonacci, jitter)
- Configurable retry attempts and delays
- Exception filtering and custom retry conditions
- Callback support for retry events
- Async and sync function support

### 🎯 **Error Classification & Routing**
- Intelligent error classification based on patterns and types
- Category-based routing to appropriate handlers
- Severity and urgency assessment
- Context-aware error handling
- Custom classification rules

### 🔧 **Automated Recovery**
- Pre-configured recovery actions for common error types
- Service restart, cache clearing, resource management
- Extensible recovery action framework
- Recovery execution tracking and logging
- Manual override capabilities

### 📊 **Monitoring & Alerting**
- Real-time error metrics collection
- Configurable alert rules and thresholds
- Multiple notification channels (email, Slack, webhook)
- Dashboard integration with comprehensive metrics
- Historical data analysis

### 🎨 **Easy Integration**
- Decorators for minimal code changes
- Framework-specific middleware (FastAPI, Flask, Django)
- Component-specific configuration
- Mixin classes for class-based integration

## Quick Start

### Installation

```python
# Import the error handling system
from DMLogn8n.multi_portal_gateway.error_handling import (
    with_circuit_breaker, with_retry, with_error_handling, resilient,
    circuit_breaker, retry, error_monitor
)
```

### Basic Usage

```python
# 1. Simple circuit breaker
@with_circuit_breaker(failure_threshold=3, recovery_timeout=30.0)
async def api_call():
    return await external_service.request()

# 2. Retry with exponential backoff
@retry(max_attempts=3, base_delay=1.0)
async def database_query():
    return await db.execute(query)

# 3. Comprehensive error handling
@resilient(max_attempts=3, failure_threshold=5, monitor=True)
async def critical_operation():
    return await perform_operation()

# 4. Custom configuration
@with_error_handling(
    circuit_breaker=CircuitBreakerConfig(failure_threshold=5),
    retry=RetryConfig(max_attempts=3),
    auto_recovery=True
)
async def service_call():
    return await service.process()
```

### Monitoring Setup

```python
# Start monitoring
error_monitor.start_monitoring(interval=60.0)

# Get dashboard data
dashboard_data = error_monitor.get_dashboard_data()

# Setup alerts
from DMLogn8n.multi_portal_gateway.error_handling import (
    SlackNotificationChannel, EmailNotificationChannel
)

slack_channel = SlackNotificationChannel(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
)
error_monitor.alert_manager.add_notification_channel("slack", slack_channel)
```

## Architecture

### Core Components

1. **Circuit Breaker** (`circuit_breaker.py`)
   - State management (CLOSED, OPEN, HALF_OPEN)
   - Failure threshold and recovery timeout
   - Concurrent call limiting
   - Comprehensive metrics

2. **Retry Handler** (`retry_handler.py`)
   - Multiple backoff strategies
   - Exception filtering
   - Callback support
   - Async/sync compatibility

3. **Error Classifier** (`error_classifier.py`)
   - Pattern-based classification
   - Category and severity assessment
   - Context-aware routing
   - Custom classification rules

4. **Recovery Manager** (`recovery_manager.py`)
   - Automated recovery actions
   - Extensible action framework
   - Recovery execution tracking
   - Manual override support

5. **Monitoring System** (`monitoring.py`)
   - Real-time metrics collection
   - Alert rule evaluation
   - Multiple notification channels
   - Dashboard integration

6. **Middleware** (`middleware.py`)
   - Framework-specific implementations
   - Standardized error responses
   - Context extraction
   - Automatic recovery

7. **Decorators** (`decorators.py`)
   - Easy integration decorators
   - Shorthand decorators
   - Mixin classes
   - Custom decorator creation

## Configuration

### Environment Variables

```bash
# Circuit Breaker
ERROR_CB_FAILURE_THRESHOLD=5
ERROR_CB_RECOVERY_TIMEOUT=60.0
ERROR_CB_AUTO_RESET=true

# Retry
ERROR_RETRY_MAX_ATTEMPTS=3
ERROR_RETRY_BASE_DELAY=1.0
ERROR_RETRY_BACKOFF_STRATEGY=exponential

# Monitoring
ERROR_MONITORING_ENABLED=true
ERROR_ALERT_INTERVAL=60.0
ERROR_METRICS_RETENTION_HOURS=24

# Notifications
ERROR_NOTIFICATIONS_ENABLED=true
ERROR_RATE_LIMIT_MINUTES=5
```

### Configuration File

```json
{
  "circuit_breaker": {
    "default_failure_threshold": 5,
    "default_recovery_timeout": 60.0,
    "auto_reset_enabled": true
  },
  "retry": {
    "default_max_attempts": 3,
    "default_base_delay": 1.0,
    "default_backoff_strategy": "exponential"
  },
  "monitoring": {
    "enabled": true,
    "alert_evaluation_interval": 60.0,
    "metrics_retention_hours": 24
  },
  "notifications": {
    "enabled": true,
    "rate_limit_minutes": 5,
    "max_alerts_per_minute": 10
  }
}
```

## Error Categories

The system automatically classifies errors into these categories:

- **NETWORK**: Connection errors, timeouts, DNS failures
- **DATABASE**: Connection pool issues, deadlocks, schema errors
- **AI_MODEL**: API rate limits, model unavailability, token limits
- **AUTHENTICATION**: Authorization failures, token issues
- **VALIDATION**: Input validation errors, type errors
- **RESOURCE**: Memory exhaustion, disk space, CPU overload
- **SYSTEM**: File permissions, OS errors
- **BUSINESS**: Application logic errors
- **TIMEOUT**: Operation timeouts
- **CONCURRENCY**: Race conditions, lock timeouts

## Recovery Actions

Built-in recovery actions include:

- **Service Restart**: Automatically restart failed services
- **Circuit Breaker Reset**: Reset circuit breakers to closed state
- **Cache Clearing**: Clear application caches
- **Resource Management**: Memory cleanup, resource scaling
- **Diagnostics**: Run system diagnostics
- **Database Reconnection**: Reconnect to databases

## Integration Examples

### FastAPI Integration

```python
from DMLogn8n.multi_portal_gateway.error_handling.middleware import FastAPIErrorHandlingMiddleware

app = FastAPI()
error_middleware = FastAPIErrorHandlingMiddleware(
    app,
    include_traceback=True,
    auto_recovery=True
)
```

### Flask Integration

```python
from DMLogn8n.multi_portal_gateway.error_handling.middleware import FlaskErrorHandlingMiddleware

app = Flask(__name__)
FlaskErrorHandlingMiddleware(app)
```

### Django Integration

```python
from DMLogn8n.multi_portal_gateway.error_handling.middleware import DjangoErrorHandlingMiddleware

# Add to Django middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'DMLogn8n.multi_portal_gateway.error_handling.middleware.DjangoErrorHandlingMiddleware',
    # ... other middleware
]
```

## Monitoring Dashboard

The system provides comprehensive metrics for monitoring:

- Total error counts by category and severity
- Recovery success rates
- Circuit breaker states
- Response time distributions
- Alert history
- Component-specific metrics

Access dashboard data:

```python
dashboard_data = error_monitor.get_dashboard_data(time_window=3600.0)
```

## Best Practices

1. **Start Simple**: Use basic decorators initially, then add complexity as needed
2. **Monitor First**: Enable monitoring before adding complex recovery logic
3. **Configure Appropriately**: Adjust thresholds based on your system characteristics
4. **Test Thoroughly**: Test error scenarios in a controlled environment
5. **Document Configurations**: Keep configuration changes well-documented
6. **Monitor Performance**: Watch for performance impacts of error handling
7. **Update Regularly**: Review and update error handling rules as systems evolve

## Advanced Usage

### Custom Recovery Actions

```python
from DMLogn8n.multi_portal_gateway.error_handling.recovery_manager import RecoveryAction

custom_action = RecoveryAction(
    name="custom_recovery",
    action_type=RecoveryActionType.CUSTOM,
    description="Custom recovery logic",
    applicable_categories=[ErrorCategory.NETWORK]
)

recovery_manager.register_action(custom_action)
```

### Custom Error Classification

```python
from DMLogn8n.multi_portal_gateway.error_handling.error_classifier import RuleBasedClassifier

classifier = RuleBasedClassifier()

def custom_rule(exception, context):
    if "custom_error" in str(exception):
        return ErrorInfo(
            exception=exception,
            category=ErrorCategory.BUSINESS,
            severity=ErrorSeverity.HIGH,
            # ... other fields
        )
    return None

classifier.add_rule(custom_rule)
error_classification_system.set_classifier(classifier)
```

### Custom Notification Channels

```python
from DMLogn8n.multi_portal_gateway.error_handling.monitoring import NotificationChannel, Alert

class CustomNotificationChannel(NotificationChannel):
    async def send_alert(self, alert: Alert) -> bool:
        # Custom notification logic
        return True

    def test_connection(self) -> bool:
        return True

error_monitor.alert_manager.add_notification_channel("custom", CustomNotificationChannel())
```

## Contributing

When contributing to the error handling system:

1. Follow the existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for any API changes
4. Consider performance implications
5. Ensure backward compatibility when possible

## License

This error handling system is part of the DMLogn8n multi-agent platform.