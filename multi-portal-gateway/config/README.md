# DMLogn8n Configuration Management System

A comprehensive configuration management system for the DMLogn8n multi-agent platform that provides:

- **Environment-specific configurations** (dev, staging, prod)
- **Dynamic configuration updates** without restart
- **Configuration validation** and type checking with Pydantic
- **Secret management** integration with multiple backends
- **Configuration versioning** and rollback capabilities
- **Multi-service configuration** coordination
- **File watching** for hot-reloading
- **Comprehensive monitoring** and logging

## Features

### 🔧 Configuration Management
- Support for YAML and JSON configuration files
- Environment variable substitution with defaults
- Nested configuration with dot notation access
- Configuration validation with detailed error reporting
- Transaction-based configuration updates
- Configuration change notifications

### 🔒 Secret Management
- Multiple secret backends (Environment variables, File, HashiCorp Vault, AWS Secrets Manager)
- Secret caching with TTL
- Secret encryption for file-based storage
- Backend health checking and failover
- Secret versioning support

### 📊 Monitoring & Validation
- Real-time configuration validation
- Configuration change tracking and auditing
- Performance metrics for configuration operations
- Health checks for all configuration components
- Comprehensive error reporting and logging

### 🔄 Dynamic Updates
- File system watching for configuration changes
- Hot-reloading without application restart
- Configuration change events and callbacks
- Debounced updates to prevent rapid changes
- Rollback capabilities for failed updates

## Quick Start

### Installation

```bash
# Install required dependencies
pip install pydantic pyyaml watchdog cryptography
pip install hvac boto3  # Optional: for Vault and AWS Secrets Manager
```

### Basic Usage

```python
from config import config_manager, config_watcher

# Get configuration values
app_name = config_manager.get_config('app', 'name')
db_config = config_manager.get_database_config()
model_config = config_manager.get_model_config('gpt4')

# Start file watcher for dynamic updates
config_watcher.start()

# Set configuration values
config_manager.set_config('app', 'new_setting', 'value')

# Validate configuration
results = config_manager.validate_configuration()
```

### Environment Setup

Set the environment and load configuration:

```bash
export ENVIRONMENT=development
export SECRET_KEY=your-secret-key
export OPENAI_API_KEY=your-openai-key
```

## Configuration Structure

### Environment-Specific Configurations

The system supports multiple environments with dedicated configuration files:

- `environments/development.yaml` - Development environment
- `environments/staging.yaml` - Staging environment
- `environments/production.yaml` - Production environment

### Configuration Sections

#### Database Configuration
```yaml
database:
  databases:
    main:
      name: main
      type: postgresql
      credentials:
        username: "${DB_USERNAME}"
        password: "${DB_PASSWORD}"
        host: "${DB_HOST}"
        port: ${DB_PORT:5432}
        database: "${DB_NAME}"
      pool:
        min_connections: 5
        max_connections: 20
        connection_timeout: 10
      ssl:
        ssl_mode: require
```

#### AI Models Configuration
```yaml
ai_models:
  models:
    gpt4:
      name: gpt4
      provider: openai
      model_id: gpt-4-turbo-preview
      model_type: chat
      credentials:
        api_key: "${OPENAI_API_KEY}"
      parameters:
        temperature: 0.7
        max_tokens: 4096
      rate_limiting:
        requests_per_minute: 1000
      caching:
        enabled: true
        ttl_seconds: 3600
```

#### Monitoring Configuration
```yaml
monitoring:
  enabled: true
  backend: prometheus
  logging:
    level: INFO
    format: json
    file_path: /var/log/dmlogn8n/app.log
  health_check:
    enabled: true
    port: 8080
    path: /health
```

## Secret Management

### Supported Backends

1. **Environment Variables** (always available)
2. **Encrypted Files** (local storage with encryption)
3. **HashiCorp Vault** (enterprise secret management)
4. **AWS Secrets Manager** (cloud-based secret management)

### Configuration

```bash
# File-based secrets (encrypted)
export SECRETS_FILE_PATH="/path/to/secrets.enc"
export SECRETS_FILE_KEY="your-encryption-key"

# HashiCorp Vault
export VAULT_URL="https://vault.example.com"
export VAULT_TOKEN="your-vault-token"

# AWS Secrets Manager
export AWS_REGION="us-west-2"
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
```

### Usage

```python
from config import get_secret, set_secret, secret_manager

# Get secrets
api_key = get_secret('OPENAI_API_KEY')
db_password = get_secret('DB_PASSWORD')

# Set secrets (only in development/testing)
set_secret('NEW_SECRET', 'secret_value')

# Check backend health
health = secret_manager.health_check()
```

## Advanced Features

### Configuration Validation

The system validates all configurations against Pydantic schemas:

```python
from config import validate_configuration

# Validate all configurations
results = validate_configuration()

for config_type, result in results.items():
    if not result.is_valid:
        print(f"Errors in {config_type}:")
        for error in result.errors:
            print(f"  {error.field}: {error.message}")
```

### Dynamic Configuration Updates

```python
from config import config_manager

# Add change listener
def on_config_change(event):
    print(f"Configuration changed: {event.config_type}")

config_manager.add_change_listener('*', on_config_change)

# Update configuration
config_manager.set_config('app', 'setting', 'new_value')
```

### Configuration Transactions

```python
from config import config_manager

# Use transactions for atomic updates
with config_manager.transaction():
    config_manager.set_config('app', 'setting1', 'value1')
    config_manager.set_config('app', 'setting2', 'value2')
    # All changes rolled back if validation fails
```

### Configuration Export

```python
# Export current configuration
config_manager.export_configuration(
    'config_backup.yaml',
    include_secrets=False  # Don't include secrets in export
)
```

## Configuration Schemas

### Database Schema

- **DatabaseConfig**: Complete database configuration
- **MultiDatabaseConfig**: Multiple database configurations with clustering
- **ConnectionPool**: Database connection pool settings
- **SSLConfig**: SSL/TLS configuration
- **RetryConfig**: Database retry strategies

### AI Models Schema

- **ModelConfig**: Individual AI model configuration
- **MultiModelConfig**: Multiple model configurations with pooling
- **ModelCredentials**: Provider-specific credentials
- **ModelParameters**: Generation parameters
- **RateLimiting**: API rate limiting
- **CachingConfig**: Response caching settings

### Monitoring Schema

- **MonitoringConfig**: Complete monitoring configuration
- **LoggingConfig**: Logging configuration
- **HealthCheck**: Health check settings
- **MetricDefinition**: Custom metrics
- **AlertRule**: Alerting rules
- **NotificationChannel**: Notification channels

## Environment Variables

### Core Configuration
- `ENVIRONMENT`: Current environment (development, staging, production)
- `SECRET_KEY`: Application secret key
- `CONFIG_AUTO_RELOAD`: Enable automatic config reloading (default: true)
- `CONFIG_VALIDATE_ON_LOAD`: Validate configuration on load (default: true)

### Database
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD`
- `DB_SSL_*`: SSL certificate paths

### AI Models
- `OPENAI_API_KEY`, `OPENAI_ORG_ID`
- `ANTHROPIC_API_KEY`
- Model-specific API keys

### Monitoring
- `PROMETHEUS_PORT`, `PROMETHEUS_PATH`
- `LOG_LEVEL`, `LOG_FORMAT`
- `HEALTH_CHECK_PORT`, `HEALTH_CHECK_PATH`

## Security Considerations

1. **Secret Management**: Always use secure secret backends in production
2. **Encryption**: Enable file encryption for local secret storage
3. **Access Control**: Limit access to configuration files and secrets
4. **Audit Logging**: Enable audit logging for configuration changes
5. **SSL/TLS**: Use encrypted connections for all external services

## Monitoring and Troubleshooting

### Health Checks

```python
# Check configuration system health
health_status = secret_manager.health_check()
is_watcher_running = config_watcher.is_running()

# Get configuration statistics
stats = config_watcher.get_statistics()
```

### Logging

The system provides comprehensive logging:

```python
import logging

# Enable debug logging
logging.getLogger('config').setLevel(logging.DEBUG)

# Configuration changes are logged automatically
# Secret access is logged (without exposing values)
# Validation errors are logged with detailed information
```

### Common Issues

1. **Configuration not found**: Check environment and file paths
2. **Validation errors**: Review schema requirements and field types
3. **Secret access denied**: Verify backend credentials and permissions
4. **File watcher not working**: Check file permissions and paths

## Development

### Running Tests

```bash
# Install development dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# Run with coverage
pytest --cov=config tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This configuration management system is part of the DMLogn8n multi-agent platform.

## Support

For questions, issues, or contributions, please contact the DMLogn8n development team.