# DMLogn8n Master Integration System

The central nervous system of the DMLogn8n platform that orchestrates all components seamlessly.

## 🌟 Overview

The Master Integration System provides comprehensive coordination and management for the entire DMLogn8n platform, ensuring all services work together as one cohesive, reliable platform.

## 🏗️ Architecture

### Core Components

1. **Platform Orchestrator** (`platform_orchestrator.py`)
   - Master coordinator for the entire platform
   - Service lifecycle management
   - Dependency resolution and startup sequencing
   - Graceful shutdown and error handling

2. **Service Registry** (`service_registry.py`)
   - Global service discovery and registration
   - Health monitoring with automatic failover
   - Load balancing endpoint selection
   - Service metadata management

3. **Event Bus** (`event_bus.py`)
   - High-performance event-driven communication
   - Priority-based message queuing
   - Event filtering and routing
   - Persistent event storage

4. **Data Flow Manager** (`data_flow_manager.py`)
   - Central data coordination and routing
   - Data transformation and filtering
   - Stream processing capabilities
   - Performance monitoring

5. **Health Monitor** (`health_monitor_global.py`)
   - Comprehensive system health monitoring
   - Multi-type health checks (HTTP, TCP, process, etc.)
   - Alerting and notification system
   - Metrics collection and analysis

6. **Configuration Manager** (`config_master.py`)
   - Centralized configuration management
   - Environment-specific overrides
   - Sensitive data encryption
   - Configuration validation and schemas

7. **API Gateway** (`api_gateway_master.py`)
   - Central API gateway with advanced routing
   - Load balancing with multiple strategies
   - Authentication and authorization
   - Rate limiting and circuit breaking

8. **Startup Sequencer** (`startup_sequencer.py`)
   - Intelligent service startup orchestration
   - Dependency-aware service ordering
   - Health check validation
   - Automatic recovery and restart

## 🚀 Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p /home/activeloguser/DMLogn8n/{logs,data,config,config/backups}
```

### Starting the Platform

```bash
# Development mode
python start_platform.py

# Production mode
DMLOG_ENV=production python start_platform.py

# Staging mode
DMLOG_ENV=staging python start_platform.py
```

### Platform Endpoints

Once started, the platform provides these endpoints:

- **API Gateway**: http://localhost:8000
- **Health Check**: http://localhost:8000/gateway/health
- **Metrics**: http://localhost:8000/gateway/metrics
- **Status**: http://localhost:8000/gateway/status
- **Routes**: http://localhost:8000/gateway/routes

## 🔧 Configuration

### Environment Variables

```bash
# Platform environment
DMLOG_ENV=development|staging|production|testing

# Gateway configuration
API_GATEWAY_PORT=8000
API_GATEWAY_HOST=0.0.0.0

# Database configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=dmlogn8n

# Security
JWT_SECRET=your-secret-key
API_KEY_ENCRYPTION_KEY=your-encryption-key
```

### Configuration Files

- `config/global.json` - Global configuration
- `config/{environment}.json` - Environment-specific settings
- `config/schemas.json` - Configuration schemas
- `config/secrets.encrypted` - Encrypted secrets

## 📊 Monitoring and Observability

### Health Monitoring

The platform provides comprehensive health monitoring:

```bash
# Check overall health
curl http://localhost:8000/gateway/health

# Get detailed metrics
curl http://localhost:8000/gateway/metrics

# Check platform status
curl http://localhost:8000/gateway/status
```

### Logging

Logs are organized by component:

- `logs/platform.log` - Main platform logs
- `logs/orchestrator.log` - Orchestrator logs
- `logs/service_registry.log` - Service registry logs
- `logs/event_bus.log` - Event bus logs
- `logs/api_gateway.log` - API gateway logs

### Metrics

The platform collects comprehensive metrics:

- Request/response times
- Error rates and status codes
- Service health status
- Resource utilization
- Custom application metrics

## 🔐 Security

### Authentication

The API Gateway supports multiple authentication methods:

- **API Keys** - Simple key-based authentication
- **JWT Tokens** - JSON Web Token authentication
- **Basic Auth** - Username/password authentication
- **OAuth2** - OAuth 2.0 integration

### Authorization

- Role-based access control
- Service-level permissions
- Resource-based access control
- Rate limiting per client

### Encryption

- Sensitive configuration data encryption
- API key storage encryption
- JWT token signing
- TLS/SSL for all communications

## 🔄 Service Integration

### Adding New Services

1. **Register Service**:
```python
# Auto-registration via service registry
from service_registry import ServiceRegistryClient

async with ServiceRegistryClient() as client:
    service_id = await client.register(
        name="my-service",
        service_type="api_service",
        host="localhost",
        ports=[8080]
    )
```

2. **Health Check Endpoint**:
```python
# Implement health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

3. **Event Integration**:
```python
# Subscribe to events
from event_bus import EventBusClient

async with EventBusClient() as client:
    await client.subscribe("service.*", my_event_handler)
```

### Service Dependencies

Services can declare dependencies in their configuration:

```json
{
  "name": "web-service",
  "dependencies": [
    {"service_name": "database", "required": true},
    {"service_name": "cache", "required": false}
  ]
}
```

## 🚨 Troubleshooting

### Common Issues

1. **Port Conflicts**:
   - Check if ports are already in use
   - Modify configuration to use different ports
   - Ensure all services have unique ports

2. **Service Startup Failures**:
   - Check logs for specific error messages
   - Verify dependencies are running
   - Check configuration validity

3. **Health Check Failures**:
   - Verify health check endpoints are accessible
   - Check network connectivity
   - Review health check timeouts

4. **Performance Issues**:
   - Monitor resource utilization
   - Check for bottlenecks in service dependencies
   - Review load balancing configuration

### Debug Mode

Enable debug logging:

```bash
# Set log level to debug
export LOG_LEVEL=DEBUG
python start_platform.py
```

### Platform Diagnostics

Run comprehensive diagnostics:

```bash
# Get platform status
curl http://localhost:8000/gateway/status

# List all routes
curl http://localhost:8000/gateway/routes

# Get detailed metrics
curl http://localhost:8000/gateway/metrics
```

## 🛠️ Development

### Project Structure

```
DMLogn8n/master/
├── platform_orchestrator.py     # Main platform coordinator
├── service_registry.py           # Service discovery and registration
├── event_bus.py                  # Event-driven communication
├── data_flow_manager.py          # Data routing and transformation
├── health_monitor_global.py      # System health monitoring
├── config_master.py              # Configuration management
├── api_gateway_master.py         # Central API gateway
├── startup_sequencer.py          # Service startup orchestration
├── start_platform.py             # Main startup script
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

### Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=master --cov-report=html
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## 📚 API Reference

### Service Registry API

```python
# Register service
await service_registry.register(
    name="service-name",
    service_type="api_service",
    host="localhost",
    ports=[8080]
)

# Discover services
services = await service_registry.discover_services(
    name="service-name",
    healthy_only=True
)

# Get load-balanced endpoint
endpoint = await service_registry.get_load_balanced_endpoint(
    "service-name",
    strategy="round_robin"
)
```

### Event Bus API

```python
# Publish event
await event_bus.publish(
    event_type="user.created",
    data={"user_id": 123, "email": "user@example.com"},
    source="user-service"
)

# Subscribe to events
await event_bus.subscribe(
    event_pattern="user.*",
    callback=my_event_handler
)
```

### Configuration API

```python
# Get configuration value
value = await config_manager.get("database.host", "localhost")

# Set configuration value
await config_manager.set(
    key="api.port",
    value=8080,
    scope=ConfigScope.SYSTEM
)

# Register configuration schema
await config_manager.register_schema(
    ConfigSchema(
        key="database.port",
        config_type="integer",
        required=True,
        default_value=5432,
        min_value=1,
        max_value=65535
    )
)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the troubleshooting guide
- Review the API documentation
- Examine the logs for error details

---

**DMLogn8n Master Integration System** - Building a cohesive, reliable platform together. 🚀