# DMLogn8n Health Check System

A comprehensive health monitoring and automated healing system for the DMLogn8n multi-agent platform. Provides multi-level health checks, dependency tracking, automated recovery, and SLA monitoring.

## Features

### Multi-Level Health Monitoring
- **Component-level**: Database, cache, message queues, filesystem, SSL certificates, network connectivity
- **Service-level**: API Gateway, Character Portal, Dialogue Service, N8N Workflow Engine
- **System-level**: CPU, memory, disk I/O, network interfaces, processes, temperature, Docker containers
- **Business-level**: User activity, game sessions, error rates, response times, character/dialogue generation

### Automated Healing & Recovery
- **Service Healing**: Automatic restart, configuration reload, state reset, rollback capabilities
- **Resource Healing**: Memory cleanup, disk space management, process optimization
- **Data Healing**: Database repair, cache recovery, data validation, backup restoration

### Advanced Analytics
- **Health Score Calculation**: Weighted scoring with trend analysis and confidence metrics
- **Dependency Graph**: Service dependency visualization and cascade failure detection
- **SLA Monitoring**: Uptime, response time, and error rate compliance tracking
- **Predictive Analytics**: Health trend prediction and volatility analysis

### Monitoring & Alerting
- **Multi-Channel Alerts**: Email, Slack, webhook notifications
- **Real-time Dashboard**: Web-based monitoring interface with live updates
- **Comprehensive APIs**: RESTful endpoints for external monitoring integration
- **Historical Analysis**: Health metrics storage and trend analysis

## Installation

### Prerequisites
- Python 3.8+
- Required packages (install via pip):
  ```
  pip install fastapi uvicorn psutil aiohttp asyncpg redis aiofiles jinja2 pydantic python-multipart
  ```

### Setup
1. Clone or navigate to the health system directory:
   ```bash
   cd /home/activeloguser/DMLogn8n/multi-portal-gateway/health
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create configuration file (optional):
   ```bash
   cp config.example.yaml config.yaml
   # Edit config.yaml with your settings
   ```

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://localhost:5432/dmlogn8n
HEALTH_DB_URL=sqlite:///health_data.db

# Cache
CACHE_HOST=localhost
CACHE_PORT=6379
CACHE_PASSWORD=your_password

# Message Queue
MQ_HOST=localhost
MQ_PORT=15672
MQ_USERNAME=guest
MQ_PASSWORD=guest

# Service URLs
API_GATEWAY_URL=http://localhost:8080
CHARACTER_PORTAL_URL=http://localhost:8081
DIALOGUE_SERVICE_URL=http://localhost:8082
N8N_URL=http://localhost:5678
N8N_API_KEY=your_n8n_api_key

# Alerting
ALERT_EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
ALERT_RECIPIENTS=admin@company.com,ops@company.com

SLACK_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_CHANNEL=#alerts

WEBHOOK_ENABLED=true
WEBHOOK_URL=https://your-webhook-endpoint.com/alerts
```

### Configuration File (config.yaml)
```yaml
max_workers: 10

checks:
  component:
    database:
      connection_string: "${DATABASE_URL}"
    cache:
      host: "${CACHE_HOST}"
      port: ${CACHE_PORT}
      password: "${CACHE_PASSWORD}"
    message_queue:
      host: "${MQ_HOST}"
      port: ${MQ_PORT}
      username: "${MQ_USERNAME}"
      password: "${MQ_PASSWORD}"

  service:
    api_gateway:
      base_url: "${API_GATEWAY_URL}"
      health_endpoint: "/health"
      timeout: 10
    # ... other services

healing:
  service:
    cooldown_minutes: 5
    max_retries: 3
  resource:
    cleanup_thresholds:
      disk_usage: 90
      memory_usage: 95

scoring:
  weights:
    component: 0.3
    service: 0.3
    system: 0.2
    business: 0.2
  thresholds:
    healthy: 90
    warning: 70
    degraded: 50

storage:
  type: "database"  # or "file"
  database:
    connection_string: "${HEALTH_DB_URL}"

alerting:
  enabled: true
  channels:
    email:
      enabled: true
      smtp_server: "${SMTP_SERVER}"
      smtp_port: ${SMTP_PORT}
      username: "${SMTP_USERNAME}"
      password: "${SMTP_PASSWORD}"
      recipients: ["admin@company.com"]

sla:
  min_uptime_percentage: 99.9
  max_response_time_ms: 1000
  max_error_rate_percentage: 1.0
```

## Usage

### Starting the Health Monitor
```bash
# Basic startup
python main.py

# With custom configuration
python main.py --config /path/to/config.yaml

# Custom host and port
python main.py --host 0.0.0.0 --port 8080

# With debug logging
python main.py --log-level DEBUG
```

### Accessing the Dashboard
- Main Dashboard: http://localhost:8000/
- Detailed View: http://localhost:8000/detailed
- Dependencies: http://localhost:8000/dependencies
- Trends: http://localhost:8000/trends
- API Documentation: http://localhost:8000/docs

### API Endpoints

#### Health Status
```bash
# Overall health status
curl http://localhost:8000/health

# Detailed health report
curl http://localhost:8000/health/detailed

# Specific service health
curl http://localhost:8000/health/service/api-gateway

# Health by level
curl http://localhost:8000/health/level/service
```

#### Manual Health Checks
```bash
# Trigger full health check
curl -X POST http://localhost:8000/health/check

# Check specific service
curl -X POST http://localhost:8000/health/check \
  -H "Content-Type: application/json" \
  -d '{"check_id": "api-gateway"}'
```

#### Health History
```bash
# Get last 24 hours of history
curl http://localhost:8000/health/history

# Get custom time range
curl http://localhost:8000/health/history?hours=48
```

#### Service Management
```bash
# Register new service
curl -X POST http://localhost:8000/health/services/register \
  -H "Content-Type: application/json" \
  -d '{
    "service_id": "new-service",
    "name": "New Service",
    "type": "api",
    "endpoint": "http://localhost:8083/health",
    "critical": true
  }'

# Unregister service
curl -X DELETE http://localhost:8000/health/services/new-service
```

## Architecture

### Core Components

1. **HealthService**: Main orchestration service
   - Schedules and executes health checks
   - Coordinates healing procedures
   - Manages service registry and dependencies

2. **Health Checkers**: Specialized health check implementations
   - `ComponentChecker`: Database, cache, message queue health
   - `ServiceChecker`: Application service health
   - `SystemChecker`: System resource health
   - `BusinessChecker`: Business metrics health

3. **Healers**: Automated recovery procedures
   - `ServiceHealer`: Service restart, configuration reload
   - `ResourceHealer`: Memory cleanup, disk management
   - `DataHealer`: Database repair, cache recovery

4. **Analytics**: Scoring and analysis
   - `HealthScorer`: Score calculation and trend analysis
   - `DependencyGraph`: Service dependency management
   - `AlertManager`: Multi-channel alerting

5. **Web Interface**: Dashboard and APIs
   - `HealthEndpoints`: REST API endpoints
   - `HealthDashboard`: Web-based monitoring interface

### Health Check Flow

1. **Scheduling**: Automatic execution on configurable intervals
2. **Execution**: Parallel health checks across all levels
3. **Analysis**: Score calculation and dependency checking
4. **Healing**: Automated recovery based on detected issues
5. **Storage**: Historical data persistence
6. **Alerting**: Notification of critical issues
7. **Reporting**: Dashboard updates and API responses

### Scoring System

The health scoring system uses weighted averages:

- **Component Health** (30%): Database, cache, message queues, etc.
- **Service Health** (30%): Application services and APIs
- **System Health** (20%): CPU, memory, disk, network
- **Business Health** (20%): User activity, error rates, response times

Score ranges:
- **90-100**: Healthy
- **70-89**: Warning
- **50-69**: Degraded
- **0-49**: Critical

## Customization

### Adding New Health Checks

1. Create a new checker class:
```python
class CustomChecker:
    async def check_health(self, check_id: str) -> HealthCheckResult:
        # Implement your health check logic
        return HealthCheckResult(
            check_id=check_id,
            check_name="Custom Check",
            level="component",
            status=HealthStatus.HEALTHY,
            message="Custom check passed"
        )
```

2. Register in the health service configuration
3. Add to the appropriate scheduler interval

### Adding New Healing Actions

1. Extend the appropriate healer class:
```python
class CustomHealer:
    async def heal_custom_issue(self, health_result: HealthCheckResult) -> List[HealingAction]:
        # Implement custom healing logic
        return [HealingAction(
            action_id="custom-heal",
            action_type="custom",
            target_service=health_result.check_id,
            description="Custom healing action",
            timestamp=datetime.now(),
            success=True,
            details={},
            duration_seconds=5
        )]
```

2. Integrate with the main health service

### Custom Alert Channels

1. Extend the AlertManager:
```python
async def _send_custom_alert(self, alert: Alert) -> bool:
    # Implement custom alert logic
    return True
```

2. Add channel configuration and routing

## Monitoring Integration

### Prometheus Metrics
Access metrics at `/metrics` endpoint for Prometheus integration:
```bash
curl http://localhost:8000/metrics
```

### Grafana Dashboard
Import the provided Grafana dashboard template for comprehensive visualization:
- Health score trends
- Service status overview
- Resource utilization
- Alert frequency

### External Monitoring
Use the health endpoints with external monitoring tools:
- Nagios/Icinga: HTTP check against `/health`
- Zabbix: JSON API integration
- DataDog: Custom metrics via API
- New Relic: Health check integration

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL environment variable
   - Verify database accessibility
   - Review connection pool settings

2. **High Memory Usage**
   - Check retention settings in storage configuration
   - Monitor alert history size
   - Adjust cleanup intervals

3. **Missing Health Data**
   - Verify service configurations
   - Check network connectivity
   - Review authentication settings

4. **Alert Not Working**
   - Validate alert channel configurations
   - Test channel endpoints
   - Check rate limiting settings

### Debug Mode
Enable debug logging:
```bash
python main.py --log-level DEBUG
```

Check logs:
```bash
tail -f /tmp/health_monitor.log
```

### Health Check Validation
Test individual health checks:
```bash
curl http://localhost:8000/health/check \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"check_id": "database"}'
```

## Performance Considerations

### Optimization Tips
1. **Adjust worker count** based on system resources
2. **Configure appropriate intervals** for different check types
3. **Enable database storage** for better performance
4. **Use retention policies** to limit data growth
5. **Optimize alert rate limits** to prevent spam

### Resource Requirements
- **Minimum**: 2 CPU cores, 4GB RAM, 10GB disk
- **Recommended**: 4 CPU cores, 8GB RAM, 50GB disk
- **High-load**: 8+ CPU cores, 16GB+ RAM, 100GB+ disk

## Security

### Authentication
Configure API authentication if required:
```yaml
security:
  enabled: true
  api_key: "your-secure-api-key"
  jwt_secret: "your-jwt-secret"
```

### Network Security
- Use HTTPS in production
- Configure firewall rules
- Limit API access to authorized networks
- Use VPN for remote access

### Data Protection
- Encrypt sensitive configuration data
- Use secure credential storage
- Implement audit logging
- Regular security updates

## Support

### Documentation
- API documentation: `/docs`
- OpenAPI spec: `/openapi.json`
- Health check guide: See individual check documentation

### Contributing
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

### License
This project is part of the DMLogn8n multi-agent platform.

---

For more information, see the [DMLogn8n documentation](../README.md) or contact the development team.