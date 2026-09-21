# DMLogn8n Feature Flag and A/B Testing System

A comprehensive, production-ready feature flag and A/B testing system for the DMLogn8n multi-agent platform. This system provides real-time feature flag management, sophisticated A/B testing capabilities, user segmentation, and statistical analysis.

## 🚀 Features

### Core Functionality
- **Real-time Feature Flag Management** - Instant flag updates via WebSocket
- **Advanced A/B Testing** - Statistical significance testing, early stopping, multiple traffic allocation strategies
- **User Segmentation** - Behavioral, demographic, and ML-based segmentation
- **Statistical Analytics** - Comprehensive analysis with confidence intervals and power analysis
- **Multi-platform SDKs** - Python, JavaScript, and Unity SDKs
- **Interactive Dashboard** - Web-based management interface with real-time updates
- **Production-ready** - Comprehensive error handling, logging, monitoring, and health checks

### Key Capabilities
- **Feature Flags**: Boolean, string, number, and JSON flags with multiple rollout strategies
- **A/B Testing**: Support for multiple variants, statistical tests, and automated analysis
- **User Segmentation**: Rule-based segments with ML clustering capabilities
- **Analytics**: Real-time metrics, statistical significance, and performance monitoring
- **Gradual Rollout**: Percentage-based, user-list, segment-based, and automatic rollouts
- **Integration**: Easy integration with existing systems via REST APIs and SDKs

## 📁 Project Structure

```
feature_flags/
├── feature_flag_service.py      # Main feature flag management service
├── experiment_manager.py        # A/B test experiment management
├── segmentation.py              # User segmentation and targeting
├── analytics.py                 # Statistical analysis and significance testing
├── dashboard.py                 # Web-based management dashboard
├── error_handling.py            # Production-ready error handling and logging
├── sdk/                         # Client SDKs
│   ├── python_sdk.py           # Python SDK
│   ├── javascript_sdk.js       # JavaScript SDK
│   └── unity_sdk.cs            # Unity SDK
├── templates/                   # Dashboard HTML templates
├── static/                      # Static assets for dashboard
└── README.md                    # This file

../feature_flags/configs/        # Experiment configurations
├── ai_model_experiments.yaml   # AI model testing configurations
├── dialogue_experiments.yaml   # Dialogue system experiments
├── combat_mechanics.yaml      # Combat system experiments
└── ui_experiments.yaml         # User interface experiments
```

## 🛠️ Installation and Setup

### Prerequisites

- Python 3.8+
- Redis server
- Node.js (for dashboard)
- Unity (for Unity SDK)

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Core dependencies
pip install fastapi uvicorn redis aioredis
pip install numpy pandas scipy scikit-learn
pip install plotly matplotlib seaborn
pip install structlog sentry-sdk prometheus-client
pip install tenacity aiohttp websockets
pip install pydantic python-multipart
```

### 2. Setup Redis

```bash
# Start Redis server
redis-server

# Or using Docker
docker run -d -p 6379:6379 redis:latest
```

### 3. Start the Services

```bash
# Start Feature Flag Service (port 8001)
cd /home/activeloguser/DMLogn8n/multi-portal-gateway/feature_flags
python feature_flag_service.py

# Start Dashboard (port 8002)
python dashboard.py

# Or use the startup script
./start_services.sh
```

### 4. Access the Dashboard

Open your browser and navigate to:
- Dashboard: `http://localhost:8002`
- API Documentation: `http://localhost:8001/docs`

## 📖 Usage Examples

### Python SDK

```python
from feature_flags.sdk.python_sdk import DMLogn8nSDK, FeatureFlags

# Initialize SDK
sdk = DMLogn8nSDK(
    api_base_url="http://localhost:8001",
    user_id="user123",
    context={
        "level": 25,
        "is_premium": True,
        "platform": "web"
    }
)

await sdk.initialize()

# Use convenience wrapper
flags = FeatureFlags(sdk)

# Check feature flags
if await flags.is_voice_chat_enabled():
    print("Voice chat is enabled!")

# Get AI model to use
ai_model = await flags.get_ai_model()
print(f"Using AI model: {ai_model}")

# Get experiment assignment
assignment = await sdk.get_experiment_assignment("exp_ai_model_comparison")
if assignment:
    print(f"User in variant: {assignment.variant.variant_name}")
```

### JavaScript SDK

```javascript
import { DMLogn8nSDK, FeatureFlags } from './javascript_sdk.js';

// Initialize SDK
const sdk = new DMLogn8nSDK({
    apiBaseUrl: 'http://localhost:8001',
    userId: 'user123',
    context: {
        level: 25,
        is_premium: true,
        platform: 'web'
    },
    enableStreaming: true,
    debug: true
});

// Use convenience wrapper
const flags = new FeatureFlags(sdk);

// Check feature flags
async function checkFeatures() {
    const voiceEnabled = await flags.isVoiceChatEnabled();
    console.log('Voice chat enabled:', voiceEnabled);

    const aiModel = await flags.getAIModel();
    console.log('Using AI model:', aiModel);
}

// Set up real-time updates
sdk.addFlagChangeHandler('voice_chat_enabled', (flagValue) => {
    console.log('Voice chat flag changed:', flagValue.value);
    updateUI(flagValue.value);
});
```

### Unity SDK

```csharp
using DMLogn8n.FeatureFlags;

// Add SDK to GameObject
public class GameManager : MonoBehaviour
{
    public DMLogn8nSDK featureFlagSDK;

    void Start()
    {
        // Set user context
        featureFlagSDK.SetUser("user123", new Dictionary<string, object>
        {
            ["level"] = 25,
            ["is_premium"] = true,
            ["platform"] = "unity"
        });

        // Check features
        CheckFeatures();
    }

    async void CheckFeatures()
    {
        var flags = new FeatureFlags(featureFlagSDK);

        // Check if voice chat is enabled
        bool voiceEnabled = await flags.IsVoiceChatEnabled();
        Debug.Log($"Voice chat enabled: {voiceEnabled}");

        // Get AI model
        string aiModel = await flags.GetAIModel();
        Debug.Log($"Using AI model: {aiModel}");
    }
}
```

### Direct API Usage

```python
import requests

# Evaluate a feature flag
response = requests.post("http://localhost:8001/evaluate", json={
    "user_id": "user123",
    "flag_name": "voice_chat_enabled",
    "context": {
        "level": 25,
        "is_premium": True
    }
})

if response.status_code == 200:
    result = response.json()
    print(f"Flag value: {result['value']}")
```

## 🔧 Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379

# Service Configuration
ENVIRONMENT=production
API_BASE_URL=http://localhost:8001
DASHBOARD_URL=http://localhost:8002

# Monitoring and Logging
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO
METRICS_PORT=8000

# SDK Configuration
SDK_KEY=your-sdk-key
CACHE_TTL=300
ENABLE_STREAMING=true
```

### Experiment Configuration

The system uses YAML configuration files for experiments. See the `/configs` directory for examples:

```yaml
exp_ai_model_comparison:
  name: "AI Model Comparison Test"
  description: "Compare different AI models for dialogue generation"

  variants:
    - id: "control_gpt4"
      name: "GPT-4 (Control)"
      traffic_percentage: 50.0
      config:
        model: "gpt-4"
        temperature: 0.7

    - id: "variant_claude"
      name: "Claude (Variant)"
      traffic_percentage: 50.0
      config:
        model: "claude-3-sonnet"
        temperature: 0.8

  metrics:
    - id: "dialogue_quality_score"
      target_value: "higher"
      statistical_test: "t_test"
```

## 📊 Analytics and Monitoring

### Metrics

The system exposes Prometheus metrics on port 8000:
- `feature_flag_errors_total` - Total error count by severity and category
- `feature_flag_evaluations_total` - Total flag evaluations
- `feature_flag_experiments_total` - Total experiments run
- `feature_flag_response_time_seconds` - Response time histograms

### Health Checks

```bash
# Check service health
curl http://localhost:8001/health

# Check dashboard health
curl http://localhost:8002/health
```

### Error Tracking

- **Sentry Integration** - Automatic error reporting to Sentry
- **Structured Logging** - JSON-formatted logs with correlation IDs
- **Performance Monitoring** - Automatic performance threshold monitoring
- **Circuit Breakers** - Resilient operation handling

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_feature_flag_service.py

# Run with coverage
python -m pytest --cov=feature_flags tests/
```

### Integration Tests

```bash
# Run integration tests
python -m pytest tests/integration/

# Test with Redis
python -m pytest tests/test_redis_integration.py
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load tests
locust -f tests/load_test.py --host=http://localhost:8001
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8001 8002

CMD ["python", "feature_flag_service.py"]
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: feature-flags
spec:
  replicas: 3
  selector:
    matchLabels:
      app: feature-flags
  template:
    metadata:
      labels:
        app: feature-flags
    spec:
      containers:
      - name: feature-flags
        image: your-registry/feature-flags:latest
        ports:
        - containerPort: 8001
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
```

### Production Considerations

1. **Redis Cluster** - Use Redis Cluster for high availability
2. **Load Balancing** - Use Nginx or similar for load balancing
3. **Monitoring** - Set up comprehensive monitoring and alerting
4. **Backups** - Regular Redis backups and configuration backups
5. **Security** - Use HTTPS, authentication, and rate limiting

## 🔒 Security

### Authentication

- SDK Key Authentication
- JWT Token Support
- Rate Limiting per API key

### Data Protection

- User data anonymization
- Secure flag evaluations
- Audit logging

### Access Control

- Role-based access control
- Feature flag permissions
- Experiment access controls

## 📚 API Reference

### Feature Flags

#### Evaluate Flag
```http
POST /evaluate
Content-Type: application/json

{
    "user_id": "user123",
    "flag_name": "voice_chat_enabled",
    "context": {
        "level": 25,
        "is_premium": true
    }
}
```

#### Get All Flags
```http
GET /flags
Authorization: Bearer your-sdk-key
```

#### Create Flag
```http
POST /flags
Authorization: Bearer your-sdk-key
Content-Type: application/json

{
    "name": "new_feature",
    "description": "A new feature flag",
    "flag_type": "boolean",
    "default_value": false,
    "rollout_strategy": "percentage",
    "rollout_percentage": 10.0
}
```

### Experiments

#### Get All Experiments
```http
GET /experiments
Authorization: Bearer your-sdk-key
```

#### Start Experiment
```http
POST /experiments/{experiment_id}/start
Authorization: Bearer your-sdk-key
```

#### Get Experiment Results
```http
GET /experiments/{experiment_id}/results
Authorization: Bearer your-sdk-key
```

### Analytics

#### Analyze Experiment
```http
POST /analytics/experiment/{experiment_id}
Authorization: Bearer your-sdk-key
Content-Type: application/json

{
    "metric_ids": ["dialogue_quality_score", "response_time"],
    "confidence_level": 0.95,
    "include_effect_size": true,
    "include_power_analysis": true
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd feature_flags

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Start development services
python -m pytest tests/conftest.py
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: See this README and inline code documentation
- **Issues**: Create an issue on GitHub
- **Email**: support@dmlogn8n.com
- **Discord**: Join our Discord community

## 🔗 Related Projects

- [DMLogn8n Core Platform](../)
- [Character System](../character-system/)
- [Dialogue Manager](../dialogue-manager/)
- [Combat System](../combat-system/)

---

Built with ❤️ for the DMLogn8n multi-agent platform