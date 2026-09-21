# DMLogn8n Load Testing Framework

A comprehensive load testing framework designed specifically for the DMLogn8n multi-agent platform. This framework provides realistic simulation of AI agents, user behavior, combat systems, and dialogue interactions to identify performance bottlenecks and ensure system scalability.

## Features

### 🔥 Core Capabilities
- **Multi-scenario Load Testing**: Agent simulation, user journeys, combat stress testing, dialogue system testing
- **Real-time Behavior Simulation**: Realistic AI agent and user behavior patterns
- **Performance Metrics Collection**: Comprehensive metrics with real-time analysis
- **Intelligent Load Generation**: Dynamic load patterns with realistic timing
- **Bottleneck Identification**: Automated detection of performance issues
- **Baseline Comparison**: Performance regression detection and trend analysis
- **Continuous Integration**: CI/CD pipeline integration with automated testing

### 📊 Advanced Features
- **Interactive Dashboards**: Real-time performance monitoring dashboards
- **Comprehensive Reporting**: HTML, JSON, and API-compatible report formats
- **Capacity Planning**: System capacity analysis and scaling recommendations
- **Anomaly Detection**: Statistical anomaly detection with alerting
- **Resource Monitoring**: CPU, memory, disk, and network resource tracking
- **Multi-environment Support**: Development, staging, and production configurations

## Architecture

```
load_testing/
├── load_test_runner.py          # Main orchestration system
├── scenarios/                   # Load test scenarios
│   ├── agent_simulation.py      # AI agent behavior simulation
│   ├── user_journey.py          # User journey simulation
│   ├── combat_stress.py         # Combat engine stress testing
│   └── dialogue_load.py         # Dialogue system load testing
├── generators/                  # Load generation components
│   ├── agent_generator.py       # AI agent load generator
│   ├── user_generator.py        # User behavior generator
│   └── data_generator.py        # Realistic test data generation
├── metrics/                     # Performance metrics
│   ├── collector.py             # Real-time metrics collection
│   ├── analyzer.py              # Performance analysis and insights
│   └── comparator.py            # Baseline comparison and regression
├── reports/                     # Report generation
│   ├── html_reporter.py         # Interactive HTML reports
│   ├── json_reporter.py         # JSON API reports
│   └── dashboard.py             # Performance dashboards
└── requirements.txt             # Python dependencies
```

## Quick Start

### Installation

1. Install the framework dependencies:
```bash
cd /home/activeloguser/DMLogn8n/multi-portal-gateway/load_testing
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export TARGET_URL="http://localhost:8000"
export AGENT_AUTH_TOKEN="your-auth-token"
export CI_SESSION_COOKIE="your-session-cookie"
```

### Basic Usage

1. **Run a simple load test:**
```bash
python load_test_runner.py ../load_testing/configs/agent_load.yaml
```

2. **Run with specific configuration:**
```bash
python load_test_runner.py --config ../load_testing/configs/user_journey.yaml --concurrent
```

3. **Run stress testing:**
```bash
python load_test_runner.py ../load_testing/configs/stress_test.yaml
```

### Configuration

Load test configurations are defined in YAML files in the `configs/` directory:

- `agent_load.yaml` - AI agent load testing configurations
- `user_journey.yaml` - User journey and behavior testing
- `stress_test.yaml` - Extreme stress testing scenarios
- `continuous.yaml` - CI/CD pipeline integration

### Example Test Configuration

```yaml
tests:
  - name: "Agent Load Test"
    scenario: "agent_simulation"
    target_url: "http://localhost:8000"
    duration: 300  # 5 minutes
    users: 100
    spawn_rate: 10  # agents per second
    ramp_up: 30  # seconds
    ramp_down: 30  # seconds
    think_time: 1.0  # seconds between actions
    timeout: 30  # seconds
    headers:
      Content-Type: "application/json"
    auth:
      type: "bearer"
      token: "${AGENT_AUTH_TOKEN}"
    monitoring:
      metrics_interval: 5  # seconds
      system_monitoring: true
    reporting:
      generate_html: true
      generate_json: true
      generate_dashboard: true
```

## Test Scenarios

### Agent Simulation (`agent_simulation`)

Simulates multiple AI agents interacting with the platform:
- **DM Assistant**: Strategic thinking and narrative generation
- **NPC Agents**: Dynamic character behavior and dialogue
- **Combat Agents**: Tactical calculations and combat logic
- **World State Agents**: System state management and consistency

### User Journey (`user_journey`)

Simulates realistic user behavior patterns:
- **New Players**: Onboarding and tutorial flows
- **Regular Players**: Daily gameplay sessions
- **Power Users**: Advanced features and complex interactions
- **Social Players**: Multiplayer and community features

### Combat Stress (`combat_stress`)

Stress tests the combat engine with intense scenarios:
- **Mass Battles**: Large-scale combat encounters
- **Boss Fights**: Complex combat calculations
- **Arena Tournaments**: Simultaneous combat sessions
- **War Simulations**: Resource-intensive combat states

### Dialogue Load (`dialogue_load`)

Tests the dialogue system under conversation load:
- **Complex Conversations**: Multi-participant dialogues
- **Emotional Interactions**: AI-driven emotional responses
- **Memory-Intensive Dialogues**: Long conversation contexts
- **Rapid Response Scenarios**: Quick-paced dialogue exchanges

## Metrics and Monitoring

### Performance Metrics

The framework collects comprehensive metrics:

- **Request Metrics**: Response times, throughput, error rates
- **System Metrics**: CPU, memory, disk, network usage
- **Database Metrics**: Query performance, connection pool usage
- **Custom Metrics**: Application-specific performance indicators

### Real-time Monitoring

- **Live Dashboard**: Interactive performance dashboard
- **Prometheus Integration**: Metrics export for monitoring systems
- **Alert System**: Automatic alerting for performance issues
- **Trend Analysis**: Performance trend detection and forecasting

## Reporting

### HTML Reports

Interactive HTML reports with:
- Executive summary with health scores
- Interactive charts and visualizations
- Detailed test results and analysis
- Performance insights and recommendations
- Responsive design for mobile viewing

### JSON Reports

Machine-readable reports for API integration:
- Structured data format for automated processing
- CI/CD pipeline integration
- Performance regression detection
- Baseline comparison data

### Performance Dashboards

Real-time monitoring dashboards featuring:
- Live metrics visualization
- System health indicators
- Alert management
- Historical performance trends

## Advanced Features

### Baseline Management

- **Automatic Baseline Creation**: Generate performance baselines from successful tests
- **Regression Detection**: Identify performance regressions automatically
- **Trend Analysis**: Track performance trends over time
- **Capacity Planning**: Estimate system capacity and scaling needs

### Anomaly Detection

- **Statistical Analysis**: Advanced statistical methods for anomaly detection
- **Pattern Recognition**: Identify unusual performance patterns
- **Alert Integration**: Automatically generate alerts for anomalies
- **Root Cause Analysis**: Help identify causes of performance issues

### CI/CD Integration

- **Automated Testing**: Run performance tests in CI/CD pipelines
- **Quality Gates**: Define performance quality gates
- **Fail Fast**: Automatically fail builds on performance regressions
- **Artifact Management**: Store and manage test artifacts

## Best Practices

### Test Design

1. **Start Small**: Begin with simple scenarios and gradually increase complexity
2. **Realistic Scenarios**: Use realistic user behavior patterns
3. **Multiple Dimensions**: Test different aspects of the system separately
4. **Baseline First**: Establish performance baselines before making changes

### Load Patterns

1. **Ramp-up Gradually**: Avoid sudden load spikes that don't reflect real usage
2. **Include Think Time**: Realistic delays between user actions
3. **Vary Load Patterns**: Test different load patterns (constant, burst, spike)
4. **Test Duration**: Run tests long enough to identify steady-state performance

### Monitoring

1. **Monitor All Resources**: Track CPU, memory, disk, and network usage
2. **Collect Detailed Metrics**: Gather comprehensive performance data
3. **Set Realistic Thresholds**: Define appropriate alert thresholds
4. **Review Trends**: Analyze performance trends over time

## Troubleshooting

### Common Issues

1. **High Memory Usage**: Check for memory leaks in agent simulations
2. **Connection Timeouts**: Increase timeout values for complex scenarios
3. **Slow Test Execution**: Reduce think times or spawn rates
4. **Report Generation Errors**: Check disk space and permissions

### Performance Tuning

1. **Database Optimization**: Ensure database is properly indexed
2. **Connection Pooling**: Use appropriate connection pool sizes
3. **Resource Allocation**: Allocate sufficient resources for test execution
4. **Network Configuration**: Optimize network settings for high-throughput testing

## Contributing

1. **Code Style**: Follow Python PEP 8 style guidelines
2. **Testing**: Add unit tests for new features
3. **Documentation**: Update documentation for new functionality
4. **Examples**: Provide example configurations for new scenarios

## License

This load testing framework is part of the DMLogn8n project and follows the same license terms.

## Support

For support and questions:
- Check the documentation in the `/docs` directory
- Review example configurations in `/configs`
- Examine test results in `/reports`
- Monitor metrics via the built-in dashboard

---

**DMLogn8n Load Testing Framework** - Ensuring performance at scale for multi-agent platforms.