# DMLogn8n Real-Time Monitoring Dashboard

A comprehensive real-time monitoring system for the DMLogn8n multi-agent platform, providing insights into agent performance, system health, business metrics, and AI model operations.

## Features

### 🎯 Core Capabilities
- **Real-time metrics visualization** with live updates via WebSockets
- **Multi-agent performance monitoring** with detailed metrics
- **System health dashboards** for CPU, memory, disk, and network
- **Business KPIs tracking** including user activity and revenue
- **AI model performance metrics** with cost analysis
- **Database performance monitoring** with query analysis
- **Advanced alerting system** with multiple notification channels
- **Historical data analysis** with customizable time ranges

### 📊 Dashboard Sections

#### 1. **Overview Dashboard**
- Active users and sessions
- System resource usage (CPU, Memory, Disk)
- Active alerts summary
- Real-time performance charts
- Recent activity timeline

#### 2. **Agent Performance**
- Agent throughput and response times
- Error rates and success metrics
- Resource utilization per agent
- Agent status and health monitoring
- Performance comparison charts

#### 3. **System Health**
- CPU, Memory, Disk utilization
- Network I/O monitoring
- Temperature and sensor data
- Process monitoring
- System load analysis

#### 4. **Business Metrics**
- User engagement analytics
- Revenue and conversion tracking
- Session metrics and retention
- Content generation statistics
- Feature adoption rates

#### 5. **AI Model Monitoring**
- Model latency and accuracy
- Token usage and costs
- Resource utilization
- Model comparison metrics
- Quality scores

#### 6. **Alert Management**
- Real-time alert notifications
- Alert severity classification
- Alert acknowledgment and suppression
- Historical alert tracking
- Multiple notification channels (Email, Slack, Webhook)

#### 7. **Database Performance**
- Connection pool monitoring
- Query performance analysis
- Cache hit ratios
- Slow query detection
- Resource utilization

## Architecture

### 🏗️ System Components

```
DMLogn8n Monitoring System
├── dashboard_service.py      # Main service coordinator
├── collectors/               # Metrics collectors
│   ├── agent_metrics.py      # Agent performance collector
│   ├── system_metrics.py     # System resource collector
│   ├── business_metrics.py   # Business KPIs collector
│   └── database_metrics.py   # Database performance collector
├── dashboards/               # Grafana dashboard definitions
│   ├── agent_performance.json
│   ├── system_health.json
│   ├── user_activity.json
│   └── ai_model_metrics.json
├── alerting.py               # Alert management system
├── metrics_storage.py        # Time-series data storage
├── api.py                    # REST API endpoints
├── static/                   # Web assets
│   └── js/dashboard.js       # Frontend JavaScript
├── templates/                # HTML templates
│   └── dashboard.html        # Main dashboard UI
└── requirements.txt          # Python dependencies
```

### 🔧 Data Flow

1. **Metrics Collection**: Collectors gather data from various sources
2. **Storage**: Metrics stored in SQLite (long-term) and Redis (cache)
3. **Processing**: Real-time aggregation and analysis
4. **Alerting**: Rule-based alert evaluation and notification
5. **Visualization**: Web dashboard with live updates
6. **API**: RESTful endpoints for external integrations

## Installation

### Prerequisites
- Python 3.8+
- Redis (optional, for caching)
- Grafana (optional, for advanced dashboards)

### Quick Start

1. **Install Dependencies**
   ```bash
   cd /home/activeloguser/DMLogn8n/multi-portal-gateway/monitoring
   pip install -r requirements.txt
   ```

2. **Start Redis (Optional but Recommended)**
   ```bash
   redis-server
   ```

3. **Run the Dashboard Service**
   ```bash
   python dashboard_service.py
   ```

4. **Access the Dashboard**
   - Main Dashboard: http://localhost:8080
   - API Endpoints: http://localhost:8080/api/
   - WebSocket: ws://localhost:8080/ws

### Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "dashboard_service.py"]
```

Build and run:
```bash
docker build -t dmlogn8n-monitoring .
docker run -p 8080:8080 dmlogn8n-monitoring
```

## Configuration

### Environment Variables

```bash
# Database Configuration
SQLITE_PATH=metrics.db
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Alert Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@dmlogn8n.com
SMTP_PASSWORD=your_password
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Service Configuration
DASHBOARD_PORT=8080
LOG_LEVEL=INFO
METRICS_COLLECTION_INTERVAL=30
ALERT_EVALUATION_INTERVAL=60
```

### Custom Alert Rules

Add custom alert rules in `alerting.py`:

```python
custom_rule = AlertRule(
    id="custom_metric_high",
    name="Custom Metric High",
    description="Custom metric is above threshold",
    metric_name="your_custom_metric",
    condition=">",
    threshold=100.0,
    severity=AlertSeverity.WARNING,
    enabled=True,
    cooldown_period=300,
    evaluation_interval=60,
    tags={"component": "custom"},
    notification_channels=["email", "slack"]
)

alert_manager.rule_engine.add_rule(custom_rule)
```

## API Documentation

### REST Endpoints

#### Metrics
- `GET /api/metrics` - Get all metrics
- `GET /api/metrics/{metric_name}` - Get specific metric
- `GET /api/metrics/{metric_name}/latest` - Get latest value
- `POST /api/metrics` - Store metrics
- `GET /api/metrics/{metric_name}/aggregate` - Get aggregated metrics

#### Alerts
- `GET /api/alerts` - Get all alerts
- `GET /api/alerts/active` - Get active alerts
- `GET /api/alerts/history` - Get alert history
- `POST /api/alerts/{alert_id}/acknowledge` - Acknowledge alert
- `POST /api/alerts/{alert_id}/suppress` - Suppress alert

#### Dashboard
- `GET /api/dashboard/summary` - Dashboard summary
- `GET /api/dashboard/system` - System dashboard data
- `GET /api/dashboard/agents` - Agents dashboard data
- `GET /api/dashboard/business` - Business dashboard data

#### Export
- `GET /api/export/metrics/{metric_name}` - Export metrics (JSON/CSV)

#### Health
- `GET /api/health` - Health check

### WebSocket API

Connect to `ws://localhost:8080/ws` for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    switch(data.type) {
        case 'metrics_update':
            updateDashboard(data.data);
            break;
        case 'alert':
            showAlert(data.data);
            break;
    }
};
```

## Grafana Integration

### Import Dashboards

1. Open Grafana
2. Go to Dashboard → Import
3. Upload JSON files from `dashboards/` directory
4. Configure Prometheus data source

### Available Dashboards

- **Agent Performance**: Agent throughput, response times, error rates
- **System Health**: CPU, memory, disk, network metrics
- **User Activity**: User engagement, session metrics
- **AI Model Metrics**: Model performance, costs, accuracy

## Monitoring Metrics

### System Metrics
- `system_cpu_usage_percent` - CPU utilization percentage
- `system_memory_usage_percent` - Memory utilization percentage
- `system_disk_usage_percent` - Disk utilization percentage
- `system_network_bytes_sent` - Network bytes sent
- `system_network_bytes_recv` - Network bytes received

### Agent Metrics
- `agent_throughput_total` - Total requests processed
- `agent_response_time_seconds` - Response time histogram
- `agent_error_rate` - Error rate percentage
- `agent_memory_usage_bytes` - Memory usage in bytes
- `agent_cpu_usage_percent` - CPU usage percentage

### Business Metrics
- `active_users_total` - Currently active users
- `active_sessions_total` - Active game sessions
- `user_satisfaction_score` - User satisfaction rating
- `daily_revenue` - Daily revenue amount
- `conversion_rate_percent` - Conversion rate percentage

### AI Model Metrics
- `ai_model_average_latency_seconds` - Model response time
- `ai_model_accuracy_score` - Model accuracy rating
- `ai_model_cost_total` - Total model cost
- `ai_model_tokens_processed_total` - Tokens processed

## Alerting

### Alert Severity Levels
- **INFO**: Informational alerts
- **WARNING**: Warning conditions
- **ERROR**: Error conditions requiring attention
- **CRITICAL**: Critical conditions requiring immediate action

### Notification Channels
- **Email**: SMTP-based email notifications
- **Slack**: Slack webhook integration
- **Webhook**: HTTP webhook notifications
- **WebSocket**: Real-time browser notifications

### Default Alert Rules

1. **System Alerts**
   - CPU usage > 80%
   - Memory usage > 85%
   - Disk usage > 90%

2. **Agent Alerts**
   - Agent error rate > 5%
   - Agent response time > 2 seconds
   - Agent down/unresponsive

3. **Business Alerts**
   - Active users < 50
   - User satisfaction < 3.5

4. **AI Model Alerts**
   - Model latency > 5 seconds
   - Model accuracy < 3.0

## Performance Considerations

### Scaling
- Use Redis for caching to reduce database load
- Implement data retention policies for old metrics
- Consider horizontal scaling for high-volume deployments
- Use connection pooling for database connections

### Optimization
- Metrics collection interval: 30-60 seconds
- Alert evaluation interval: 60 seconds
- Data retention: 30 days (configurable)
- WebSocket connections: Limited to 1000 concurrent clients

## Troubleshooting

### Common Issues

1. **Dashboard Not Loading**
   - Check if the service is running on port 8080
   - Verify dependencies are installed
   - Check logs for error messages

2. **Missing Metrics**
   - Verify collectors are running
   - Check database connectivity
   - Review metric collection intervals

3. **Alerts Not Firing**
   - Verify alert rules are enabled
   - Check threshold values
   - Review notification channel configurations

4. **WebSocket Connection Issues**
   - Check firewall settings
   - Verify WebSocket endpoint accessibility
   - Review browser console for errors

### Logs

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check service logs:
```bash
tail -f dashboard.log
```

## Development

### Adding New Metrics

1. **Create Collector** (in `collectors/`):
   ```python
   class CustomMetricsCollector:
       async def collect_metrics(self):
           # Implementation
           pass
   ```

2. **Register Collector** (in `dashboard_service.py`):
   ```python
   custom_collector = CustomMetricsCollector()
   await custom_collector.start_collection()
   ```

3. **Add API Endpoint** (in `api.py`):
   ```python
   async def get_custom_metrics(request):
       # Implementation
       pass
   ```

### Adding New Dashboard Panels

1. **Update HTML Template** (in `templates/dashboard.html`)
2. **Add Chart Configuration** (in `static/js/dashboard.js`)
3. **Update API Data Source** (in `api.py`)

### Testing

Run tests:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=. tests/
```

## Security

### Authentication
- API key authentication (recommended)
- JWT token support
- Role-based access control

### Data Protection
- Encrypted connections (HTTPS/WSS)
- Input validation and sanitization
- Rate limiting on API endpoints

### Access Control
- Configure firewall rules
- Use reverse proxy (nginx/Apache)
- Implement IP whitelisting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This monitoring system is part of the DMLogn8n project and follows the same licensing terms.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

---

**DMLogn8n Monitoring Dashboard** - Comprehensive real-time monitoring for multi-agent platforms