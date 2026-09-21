# DMLogn8n Auto-Scaling System

A comprehensive, production-ready auto-scaling platform for the DMLogn8n multi-agent gaming platform. This system provides intelligent scaling across multiple environments with predictive analytics, cost optimization, and real-time monitoring.

## 🚀 Features

### Core Auto-Scaling
- **Horizontal Scaling**: Automatic scaling of services based on multiple metrics
- **Multi-Platform Support**: Kubernetes, Docker, and Cloud providers (AWS, Azure, GCP)
- **Custom Metrics**: Business-specific metrics for intelligent scaling decisions
- **Predictive Scaling**: Machine learning-based scaling predictions
- **Cost Optimization**: Cost-aware scaling decisions with budget management

### Scaling Strategies
- **Metric-Based**: CPU, memory, request rate, response time, error rate
- **Schedule-Based**: Time-based scaling for known traffic patterns
- **Event-Driven**: Responsive scaling based on system events
- **Predictive**: AI-powered scaling based on historical data
- **Cost-Based**: Scaling decisions optimized for cost efficiency

### Monitoring & Alerting
- **Real-time Monitoring**: Comprehensive health checks and metrics
- **Alert Management**: Multi-channel notifications (Slack, Email, PagerDuty)
- **Dashboard**: Prometheus metrics and Grafana integration
- **Audit Logs**: Complete scaling event history and audit trails

### Platform Support
- **Kubernetes**: Native HPA and custom controller support
- **Docker**: Docker Compose and container management
- **AWS**: EC2 Auto Scaling Groups, ECS, and Lambda
- **Azure**: VM Scale Sets and Container Instances
- **GCP**: Compute Engine and Cloud Run

## 📁 Architecture

```
autoscaling/
├── autoscaler.py              # Main auto-scaling engine
├── api.py                     # REST API server
├── monitoring.py              # Monitoring and alerting system
├── start.py                   # Platform startup script
├── config.yaml               # Configuration file
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── metrics/                  # Metrics collection and analysis
│   ├── custom_metrics.py     # Business metrics collection
│   ├── predictor.py          # Predictive scaling analytics
│   └── cost_optimizer.py     # Cost-based scaling decisions
├── policies/                 # Scaling policy management
│   ├── scale_policies.py     # Policy definitions and management
│   ├── schedule_scaling.py   # Time-based scaling
│   └── event_scaling.py      # Event-driven scaling
└── controllers/              # Platform scaling controllers
    ├── k8s_controller.py     # Kubernetes scaling controller
    ├── docker_controller.py   # Docker scaling controller
    └── cloud_controller.py    # Cloud provider scaling controller
```

## 🛠 Installation

### Prerequisites
- Python 3.9+
- Redis server
- Kubernetes cluster (optional)
- Docker (optional)
- Cloud provider accounts (optional)

### Quick Start

1. **Clone and Setup**
```bash
cd /home/activeloguser/DMLogn8n/multi-portal-gateway/autoscaling
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure**
```bash
# Copy and edit configuration
cp config.yaml config.local.yaml
# Edit config.local.yaml with your settings
```

4. **Start Redis**
```bash
docker run -d --name redis -p 6379:6379 redis:alpine
```

5. **Launch Platform**
```bash
python start.py --config config.local.yaml
```

### Docker Deployment

```bash
# Build image
docker build -t dmlogn8n-autoscaling .

# Run with configuration
docker run -d \
  --name autoscaling \
  -p 8090:8090 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  dmlogn8n-autoscaling
```

### Kubernetes Deployment

```bash
# Apply configurations
kubectl apply -f k8s/

# Check status
kubectl get pods -n dmlogn8n
```

## ⚙️ Configuration

### Main Configuration (`config.yaml`)

```yaml
# Global settings
global:
  environment: "production"
  region: "us-west-2"
  namespace: "dmlogn8n"

# Redis for caching and coordination
redis:
  host: "redis.autoscaling.svc.cluster.local"
  port: 6379

# Metrics collection
metrics:
  collection_interval: 30
  retention_period: 3600

# Predictive scaling
prediction:
  enabled: true
  model_path: "/models/scaling_predictor.pkl"
  confidence_threshold: 0.75

# Cost optimization
cost:
  enabled: true
  cost_threshold: 500  # $500 per hour
  strategy: "balanced"

# API server
api:
  enabled: true
  host: "0.0.0.0"
  port: 8090

# Monitoring
monitoring:
  enabled: true
  health_check_interval: 30
  notification_channels:
    slack:
      webhook_url: "${SLACK_WEBHOOK_URL}"
      channel: "#autoscaling-alerts"
```

### Service Configuration

Each service can be configured with specific scaling parameters:

```yaml
services:
  api-gateway:
    enabled: true
    service_type: "api_gateway"
    controller: "kubernetes"
    min_instances: 2
    max_instances: 10
    target_cpu: 65
    target_memory: 70
    custom_metrics:
      - "requests_per_second"
      - "response_time"
```

## 📊 API Usage

### Authentication

```bash
# Login
curl -X POST http://localhost:8090/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# Use token
curl -H "Authorization: Bearer <token>" \
  http://localhost:8090/api/services
```

### Scaling Operations

```bash
# Get service status
curl -H "Authorization: Bearer <token>" \
  http://localhost:8090/api/services/api-gateway

# Scale service
curl -X POST http://localhost:8090/api/services/api-gateway/scale \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"desired_instances": 8, "reason": "Manual scaling"}'
```

### Policy Management

```bash
# List policies
curl -H "Authorization: Bearer <token>" \
  http://localhost:8090/api/policies

# Create policy
curl -X POST http://localhost:8090/api/policies \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @policy-config.json
```

### Monitoring

```bash
# Get health status
curl -H "Authorization: Bearer <token>" \
  http://localhost:8090/api/monitoring/health

# Get alerts
curl -H "Authorization: Bearer <token>" \
  http://localhost:8090/api/monitoring/alerts

# Get metrics
curl http://localhost:8090/metrics
```

## 🔧 Policy Examples

### API Gateway Scaling Policy

```yaml
apiVersion: autoscaling.dmlogn8n/v1
kind: ScalingPolicy
metadata:
  name: api-gateway-scaling
spec:
  serviceId: "api-gateway"
  serviceType: "api_gateway"
  minInstances: 3
  maxInstances: 20
  targetMetrics:
    cpuUtilization: 65
    memoryUtilization: 70
    requestRate: 500
  scaleUpThresholds:
    cpuUtilization: 75
    requestRate: 700
    duration: 60
  scaleDownThresholds:
    cpuUtilization: 35
    requestRate: 200
    duration: 300
```

### Event-Driven Scaling

```yaml
eventTriggers:
  - name: "traffic-spike-response"
    eventType: "traffic_spike"
    condition: "requests_per_second > 2000"
    action: "immediate_scale_up"
    instances: 5
    cooldown: 600
```

## 📈 Monitoring & Metrics

### Prometheus Metrics

The system exposes metrics on port 8080:

- `autoscaling_events_total` - Total scaling events
- `autoscaling_alerts_active` - Active alerts by severity
- `autoscaling_system_health` - Overall system health score
- `autoscaling_health_check_status` - Health check results

### Health Checks

```bash
# System health
curl http://localhost:8090/health

# Detailed health status
curl http://localhost:8090/api/monitoring/health
```

### Alerting

Configure notifications in `config.yaml`:

```yaml
notifications:
  channels:
    - type: "slack"
      webhook_url: "${SLACK_WEBHOOK_URL}"
      severity_threshold: "warning"
    - type: "email"
      recipients: ["team@company.com"]
      severity_threshold: "error"
```

## 🤖 Predictive Scaling

The system uses machine learning to predict scaling needs:

### Features
- **Time Series Prediction**: LSTM and Prophet models
- **Anomaly Detection**: Isolation Forest for unusual patterns
- **Confidence Scoring**: Only scale when confidence > threshold
- **Continuous Learning**: Models retrain with new data

### Configuration

```yaml
prediction:
  enabled: true
  model_type: "lstm"
  confidence_threshold: 0.75
  prediction_window: 900  # 15 minutes
  training_data_window: 14  # days
```

## 💰 Cost Optimization

### Features
- **Budget Management**: Set and monitor cost thresholds
- **Resource Efficiency**: Optimize instance selection
- **Scheduled Scaling**: Cost-effective time-based scaling
- **Usage Analytics**: Detailed cost breakdowns

### Configuration

```yaml
cost:
  enabled: true
  strategy: "balanced"
  hourly_budget: 500
  cost_savings_threshold: 5
```

## 🔒 Security

### Authentication
- JWT-based authentication
- Role-based access control
- Session management
- API rate limiting

### Security Features
- Encrypted communications
- Audit logging
- Access control policies
- Secure credential management

## 🧪 Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Coverage report
pytest --cov=autoscaling tests/
```

### Dry Run Mode

```bash
python start.py --dry-run --config config.yaml
```

## 📚 Examples

See the `policies/examples/` directory for comprehensive scaling policy examples:

- `agent_pool_scaling.yaml` - AI model pool scaling
- `api_gateway_scaling.yaml` - API gateway scaling
- `database_scaling.yaml` - Database cluster scaling
- `event_driven_scaling.yaml` - Event-driven scaling configuration

## 🚨 Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   ```bash
   # Check Redis is running
   docker ps | grep redis
   # Check network connectivity
   telnet redis-host 6379
   ```

2. **Kubernetes Permission Errors**
   ```bash
   # Check service account permissions
   k auth can-i create horizontalpodautoscalers
   # Check RBAC configuration
   k get clusterrole autoscaling-engine
   ```

3. **Cloud Provider Authentication**
   ```bash
   # AWS
   aws sts get-caller-identity
   # Azure
   az account show
   # GCP
   gcloud auth list
   ```

### Debug Mode

```bash
python start.py --debug --log-level DEBUG
```

### Logs

```bash
# Platform logs
tail -f /var/log/autoscaling/platform.log

# Component logs
kubectl logs -n dmlogn8n -l app=autoscaling
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- **Documentation**: Check this README and inline code comments
- **Issues**: Create an issue on the project repository
- **Discussions**: Use the project discussion forum
- **Email**: platform-team@dmlogn8n.com

## 🔮 Roadmap

### Upcoming Features
- [ ] Multi-cloud deployment automation
- [ ] Advanced anomaly detection
- [ ] Custom dashboard integration
- [ ] GraphQL API support
- [ ] Terraform provider
- [ ] Helm charts
- [ ] Performance profiling
- [ ] Load testing integration

### Version History
- **v2.0** - Complete rewrite with advanced features
- **v1.5** - Added predictive scaling and cost optimization
- **v1.0** - Initial release with basic auto-scaling

---

**DMLogn8n Auto-Scaling System** - Intelligent scaling for modern applications.