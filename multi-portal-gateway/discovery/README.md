# DMLogn8n Service Discovery System

A comprehensive service discovery and coordination platform built on Consul for the DMLogn8n multi-agent platform. This system provides enterprise-grade service registration, health monitoring, configuration distribution, load balancing, and AI agent coordination capabilities.

## Architecture Overview

The service discovery system consists of several integrated components:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Discovery API Layer                         │
│                     (FastAPI/REST)                            │
├─────────────────────────────────────────────────────────────────┤
│  Consul Manager  │  Service Registry  │  Health Checker        │
│                  │                   │                        │
│  Config Distributor │ Load Balancer  │  Agent Coordinator     │
├─────────────────────────────────────────────────────────────────┤
│                      Consul Cluster                           │
│               (Service Discovery & KV Store)                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Consul Manager (`consul_manager.py`)
Main integration layer with Consul providing:
- Multi-datacenter support
- Distributed locking
- Event handling
- Session management
- Backup and recovery

### 2. Service Registry (`service_registry.py`)
Comprehensive service management featuring:
- Automatic service registration/deregistration
- Service metadata management
- Dependency tracking
- Service topology mapping
- Lifecycle management

### 3. Health Checker (`health_checker.py`)
Advanced health monitoring with:
- Custom health checks (HTTP, TCP, Script, Custom)
- Health metric collection
- Alerting and notifications
- Circuit breaker integration
- Health trend analysis

### 4. Configuration Distributor (`config_distributor.py`)
Enterprise configuration management:
- Multi-format configuration (JSON, YAML, ENV, TOML)
- Schema validation
- Versioning and rollback
- Encryption support
- Hot-reloading capabilities

### 5. Load Balancer (`load_balancer.py`)
Intelligent load balancing with:
- Multiple algorithms (Round Robin, Weighted, Least Connections, etc.)
- Circuit breaker pattern
- Health-aware routing
- Adaptive learning
- Session affinity

### 6. Agent Coordinator (`agent_coordinator.py`)
Specialized AI agent coordination:
- Agent lifecycle management
- Capability discovery and matching
- Task distribution and scheduling
- Agent collaboration sessions
- Performance monitoring

### 7. Discovery API (`discovery_api.py`)
RESTful API providing:
- Service registration/discovery endpoints
- Health check management
- Configuration operations
- Load balancing control
- Agent coordination
- Metrics and monitoring

## Installation and Setup

### Prerequisites
- Python 3.8+
- Consul 1.12+
- Redis (for caching)
- PostgreSQL (for persistent storage)

### Installation

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Setup Consul**
```bash
# Copy Consul configuration
cp discovery/consul/consul-config.json /etc/consul/consul.json

# Start Consul cluster
consul agent -config-dir=/etc/consul/
```

3. **Configure Environment**
```bash
export CONSUL_HOST=localhost
export CONSUL_PORT=8500
export CONSUL_TOKEN=your-consul-token
```

4. **Initialize Service Discovery**
```python
from discovery.consul_manager import ConsulManager, ConsulConfig
from discovery.discovery_api import DiscoveryAPI

# Initialize Consul manager
consul_config = ConsulConfig(
    host="localhost",
    port=8500,
    token="your-token"
)

# Create and initialize API
api = DiscoveryAPI()
await api.initialize(consul_config)
```

## Usage Examples

### Service Registration

```python
from discovery.service_registry import ServiceRegistration, ServiceMetadata, ServiceEndpoint, HealthCheck

# Create service registration
metadata = ServiceMetadata(
    service_id="my-service-1",
    service_name="my-service",
    service_type=ServiceType.API_GATEWAY,
    version="1.0.0",
    description="My awesome service",
    host="localhost",
    port=8080,
    owner="my-team"
)

endpoint = ServiceEndpoint(
    host="localhost",
    port=8080,
    health_endpoint="/health"
)

registration = ServiceRegistration(
    metadata=metadata,
    endpoint=endpoint,
    health_check=HealthCheck()
)

# Register service
success = await service_registry.register_service(registration)
```

### Health Check Configuration

```python
from discovery.health_checker import HealthCheckDefinition, CheckType

# Create health check
check_def = HealthCheckDefinition(
    check_id="my-service-health",
    name="My Service Health Check",
    service_id="my-service-1",
    check_type=CheckType.HTTP,
    target="http://localhost:8080/health",
    interval=10,
    timeout=3
)

# Register health check
await health_checker.register_check(check_def)
```

### Configuration Management

```python
# Store configuration
await config_distributor.store_config(
    key="my-service/database",
    value={
        "host": "localhost",
        "port": 5432,
        "database": "myapp"
    },
    scope=ConfigScope.SERVICE,
    format=ConfigFormat.JSON
)

# Retrieve configuration
config = await config_distributor.get_config("my-service/database")
```

### Load Balancer Setup

```python
from discovery.load_balancer import LoadBalancerConfig, LoadBalancingAlgorithm

# Register load balancer
config = LoadBalancerConfig(
    algorithm=LoadBalancingAlgorithm.LEAST_CONNECTIONS,
    service_name="my-service",
    enable_sticky_sessions=True
)

await load_balancer.register_load_balancer(config)

# Route request
success, response, error = await load_balancer.route_request(
    service_name="my-service",
    request_path="/api/users",
    method="GET"
)
```

### Agent Coordination

```python
from discovery.agent_coordinator import AgentDefinition, AgentCapability, AgentType

# Register AI agent
agent_def = AgentDefinition(
    agent_id="dialogue-agent-1",
    name="Dialogue Agent",
    agent_type=AgentType.DIALOGUE_AGENT,
    version="1.0.0",
    description="Natural language dialogue processor",
    capabilities=[
        AgentCapability(
            capability_id="nlp-processing",
            name="Natural Language Processing",
            description="Process and understand natural language"
        )
    ]
)

await agent_coordinator.register_agent(agent_def)

# Submit task
from discovery.agent_coordinator import AgentTask, TaskPriority

task = AgentTask(
    task_id="task-001",
    task_type="dialogue_generation",
    priority=TaskPriority.HIGH,
    payload={
        "context": "user wants to know about the story",
        "character": "Anna"
    }
)

task_id = await agent_coordinator.submit_task(task)
```

## API Reference

### Service Endpoints

- `POST /services/register` - Register a new service
- `POST /services/discover` - Discover services based on criteria
- `GET /services/{service_id}` - Get service details
- `DELETE /services/{service_id}` - Deregister service
- `GET /services/topology` - Get service topology

### Health Check Endpoints

- `POST /health/checks` - Register health check
- `GET /health/services/{service_id}` - Get service health
- `GET /health/cluster` - Get cluster health
- `POST /health/checks/{check_id}/execute` - Execute health check

### Configuration Endpoints

- `POST /config` - Store configuration
- `GET /config/{key}` - Get configuration
- `PUT /config/{key}` - Update configuration
- `DELETE /config/{key}` - Delete configuration
- `GET /config/{key}/history` - Get configuration history

### Load Balancer Endpoints

- `POST /loadbalancer` - Register load balancer
- `GET /loadbalancer/{service_name}/select` - Select instance
- `POST /loadbalancer/{service_name}/route` - Route request
- `GET /loadbalancer/{service_name}/metrics` - Get metrics

### Agent Coordination Endpoints

- `POST /agents` - Register agent
- `POST /agents/tasks` - Submit task
- `GET /agents/{agent_id}` - Get agent status
- `POST /agents/collaboration` - Start collaboration
- `POST /agents/collaboration/{session_id}/message` - Send message

## Configuration

### Consul Configuration

The main Consul configuration is located in `discovery/consul/consul-config.json`. Key settings include:

- **Datacenter configuration**: Multi-DC setup
- **ACL policies**: Security and access control
- **Service mesh**: Connect integration
- **Telemetry**: Metrics and monitoring
- **TLS**: Security configuration

### Service Definitions

Service definitions are stored in `discovery/consul/service-definitions/`:

- `api-gateway.json` - API Gateway service
- `character-portal.json` - Character portal agent
- `dialogue-system.json` - Dialogue system agent
- `postgresql.json` - PostgreSQL database
- `redis.json` - Redis cache
- `qdrant.json` - Vector database

### ACL Policies

Access control policies in `discovery/consul/acl-policies/`:

- `global-management.hcl` - Full administrative access
- `service-operator.hcl` - Service operator permissions
- `ai-agent.hcl` - AI agent access
- `monitoring-system.hcl` - Read-only monitoring access

## Security

### Authentication
- Consul ACL tokens for API authentication
- Role-based access control (RBAC)
- Service mesh mTLS for inter-service communication

### Encryption
- Configuration encryption at rest
- TLS for all network communication
- Gossip encryption for cluster communication

### Access Control
- Namespace isolation
- Partition segregation
- Fine-grained ACL policies

## Monitoring and Observability

### Metrics
- Prometheus integration
- Custom service metrics
- Performance monitoring
- Resource utilization tracking

### Logging
- Structured logging with correlation IDs
- Distributed tracing support
- Error tracking and alerting

### Health Monitoring
- Multi-level health checks
- Circuit breaker patterns
- Automated failover
- Recovery automation

## Scaling and High Availability

### Horizontal Scaling
- Multiple Consul agents
- Service mesh sidecars
- Load balancer instances
- Agent coordinator clustering

### Disaster Recovery
- Multi-datacenter replication
- Configuration backups
- Automated failover
- Data consistency guarantees

## Best Practices

### Service Registration
1. Use descriptive service names and metadata
2. Implement proper health checks
3. Set appropriate timeouts and intervals
4. Include capability information

### Health Checking
1. Define meaningful health check endpoints
2. Configure appropriate intervals
3. Implement graceful degradation
4. Monitor health check patterns

### Configuration Management
1. Use schema validation
2. Implement versioning
3. Test configuration changes
4. Monitor configuration drift

### Load Balancing
1. Choose appropriate algorithms
2. Monitor performance metrics
3. Implement circuit breakers
4. Consider session affinity needs

### Agent Coordination
1. Define clear capabilities
2. Implement proper error handling
3. Monitor agent performance
4. Use collaboration patterns effectively

## Troubleshooting

### Common Issues

**Service Registration Fails**
- Check Consul connectivity
- Verify ACL permissions
- Validate service definition
- Check network connectivity

**Health Checks Failing**
- Verify endpoint accessibility
- Check timeout configurations
- Review health check logic
- Monitor service logs

**Configuration Distribution Issues**
- Check KV store permissions
- Verify encryption keys
- Validate configuration format
- Check schema definitions

**Load Balancing Problems**
- Review algorithm configuration
- Check service instance health
- Monitor circuit breaker state
- Verify network connectivity

**Agent Coordination Issues**
- Validate agent capabilities
- Check task payload format
- Review collaboration sessions
- Monitor agent performance

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
```bash
black discovery/
flake8 discovery/
```

### Documentation
```bash
sphinx-build docs/ docs/_build/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the platform team
- Check the documentation
- Review the troubleshooting guide

---

**DMLogn8n Service Discovery System** - Enterprise-grade service discovery for AI-powered multi-agent platforms.