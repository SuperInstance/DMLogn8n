# DMLogn8n Deployment Automation System

A comprehensive deployment automation system that makes installing and running DMLogn8n effortless. This system handles everything from local development to production deployment with one-command deployment capabilities.

## 🚀 Quick Start

### One-Command Deployment

The fastest way to deploy DMLogn8n is using the quick deployment script:

```bash
# Deploy to development environment
./scripts/quick_deploy.sh -e development

# Deploy to production environment
./scripts/quick_deploy.sh -e production

# Deploy with options
./scripts/quick_deploy.sh -e production --skip-backup --verbose
```

### Manual Deployment

For more control over the deployment process:

```bash
# Initialize the deployment manager
python3 deployment_manager.py development

# Deploy to specific environment
python3 deployment_manager.py production --version latest
```

## 📁 System Architecture

The deployment system consists of the following components:

### Core Components

- **`deployment_manager.py`** - Master deployment coordinator that orchestrates the entire deployment process
- **`environment_setup.py`** - Automated environment configuration and dependency management
- **`service_deployer.py`** - Deploys all services with proper orchestration and startup sequences
- **`database_initializer.py`** - Sets up and initializes all databases with schemas and sample data
- **`config_generator.py`** - Generates environment-specific configurations
- **`health_check_deploy.py`** - Verifies deployment health and service functionality
- **`rollback_manager.py`** - Automated rollback capabilities for failed deployments
- **`monitoring_deploy.py`** - Deployment monitoring and alerting system

### Container Orchestration

- **`docker/docker-compose.yml`** - Docker Compose configuration for containerized deployment
- **`k8s/`** - Kubernetes manifests for production-grade deployment
- **`scripts/quick_deploy.sh`** - One-command deployment script

## 🌍 Multi-Environment Support

The system supports three environments:

### Development Environment
- **Purpose**: Local development and testing
- **Features**: Debug logging, hot reloading, sample data
- **URLs**:
  - Player Portal: http://localhost:3000
  - API: http://localhost:8000
  - N8N: http://localhost:5678

### Staging Environment
- **Purpose**: Pre-production testing
- **Features**: Production-like configuration, monitoring enabled
- **URLs**:
  - Player Portal: https://staging.dmlogn8n.com
  - API: https://staging-api.dmlogn8n.com
  - N8N: https://staging-n8n.dmlogn8n.com

### Production Environment
- **Purpose**: Live production deployment
- **Features**: Full monitoring, SSL certificates, security hardening
- **URLs**:
  - Player Portal: https://dmlogn8n.com
  - API: https://api.dmlogn8n.com
  - N8N: https://n8n.dmlogn8n.com

## 🔧 Configuration Management

### Environment Variables

The system uses environment-specific configuration files:

```bash
# Development
cp docker/.env.example docker/.env.development

# Staging
cp docker/.env.example docker/.env.staging

# Production
cp docker/.env.example docker/.env.production
```

### Generated Configurations

The system automatically generates:
- **Nginx configuration** with SSL and security headers
- **MySQL configuration** optimized for each environment
- **Redis configuration** with persistence and security
- **Supervisor configuration** for process management
- **Service-specific `.env` files** for each component

## 📊 Monitoring & Observability

### Health Checks

Comprehensive health checks include:
- **HTTP endpoint checks** for all services
- **Database connectivity checks** (MySQL, Redis)
- **Docker container health monitoring**
- **System resource monitoring** (CPU, memory, disk)
- **Network connectivity checks**

### Monitoring Stack

The system includes:
- **Prometheus** for metrics collection
- **Grafana** for visualization and dashboards
- **Node Exporter** for system metrics
- **Custom health check endpoints**
- **Alert management** with configurable thresholds

## 🛡️ Security Features

### Automated Security
- **SSL certificate management** with Let's Encrypt
- **Security headers** configured in Nginx
- **Firewall rules** for production environments
- **Secret management** with encrypted storage
- **Container security** with non-root users

### Backup & Recovery
- **Automated backups** before deployments
- **Database dumps** with point-in-time recovery
- **Configuration backups** for rollback
- **Retention policies** for backup management

## 🔄 Rollback Capabilities

The rollback system provides:
- **Automated rollback points** created before each deployment
- **Configuration restoration** from backups
- **Database restoration** from SQL dumps
- **Container state restoration**
- **Partial rollbacks** for specific components

## 📋 Deployment Commands

### Quick Deploy Script

```bash
# Basic deployment
./scripts/quick_deploy.sh -e <environment>

# With options
./scripts/quick_deploy.sh \
  -e production \
  --skip-backup \
  --skip-monitoring \
  --verbose

# Rollback
./scripts/quick_deploy.sh --rollback <deployment_id>

# Check status
./scripts/quick_deploy.sh --status
```

### Individual Components

```bash
# Environment setup
python3 environment_setup.py development

# Service deployment
python3 service_deployer.py development --action deploy

# Database initialization
python3 database_initializer.py development

# Configuration generation
python3 config_generator.py development

# Health checks
python3 health_check_deploy.py development

# Monitoring setup
python3 monitoring_deploy.py development --action setup

# Rollback management
python3 rollback_manager.py production --action rollback
```

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Check status
docker-compose -f docker/docker-compose.yml ps

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.yml down
```

### Service Management

```bash
# Restart specific service
docker-compose -f docker/docker-compose.yml restart api

# Scale services
docker-compose -f docker/docker-compose.yml up -d --scale api=3

# Update images
docker-compose -f docker/docker-compose.yml pull
docker-compose -f docker/docker-compose.yml up -d
```

## ☸️ Kubernetes Deployment

### Apply Kubernetes Manifests

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply configurations
kubectl apply -f k8s/configmaps.yaml
kubectl apply -f k8s/secrets.yaml

# Deploy databases
kubectl apply -f k8s/mysql-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml

# Deploy applications
kubectl apply -f k8s/n8n-deployment.yaml
kubectl apply -f k8s/api-deployment.yaml

# Setup ingress
kubectl apply -f k8s/ingress.yaml
```

### Monitor Deployment

```bash
# Check deployment status
kubectl get pods -n dmlogn8n

# View logs
kubectl logs -f deployment/api -n dmlogn8n

# Check services
kubectl get services -n dmlogn8n
```

## 📝 Logging & Debugging

### Log Locations

- **Application logs**: `/var/log/dmlogn8n/`
- **Deployment logs**: `/var/log/dmlogn8n/deployments/`
- **Health check logs**: `/var/log/dmlogn8n/health/`
- **Monitoring logs**: `/var/log/dmlogn8n/monitoring/`

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Set debug environment
export LOG_LEVEL=DEBUG

# Run deployment with debug
./scripts/quick_deploy.sh -e development --verbose
```

## 🔧 Customization

### Adding New Services

1. Update `service_deployer.py` with new service configuration
2. Add Docker image configuration to `docker-compose.yml`
3. Create Kubernetes manifests in `k8s/`
4. Update health checks in `health_check_deploy.py`
5. Add monitoring rules in `monitoring_deploy.py`

### Environment-Specific Configuration

Edit environment configurations in:
- `docker/.env.<environment>`
- `configs/<environment>.json`
- `monitoring/<environment>.json`

## 🚨 Troubleshooting

### Common Issues

1. **Port conflicts**: Check if ports are already in use
2. **Permission denied**: Ensure proper file permissions
3. **Docker issues**: Verify Docker daemon is running
4. **Database connection**: Check database credentials and connectivity
5. **SSL certificates**: Verify domain configuration and certificates

### Health Check Failures

```bash
# Run health checks manually
python3 health_check_deploy.py development

# Check specific service
python3 health_check_deploy.py development --check api_http

# Continuous monitoring
python3 health_check_deploy.py development --continuous
```

### Rollback Issues

```bash
# List rollback points
python3 rollback_manager.py production --action list

# Force rollback
python3 rollback_manager.py production --action rollback --rollback-type full

# Cleanup old rollbacks
python3 rollback_manager.py production --action cleanup --keep-count 5
```

## 📚 Advanced Usage

### Custom Deployment Scripts

```python
from deployment_manager import DeploymentManager, DeploymentConfig, Environment

config = DeploymentConfig(
    environment=Environment.PRODUCTION,
    version="v1.2.3",
    backup_enabled=True,
    monitoring_enabled=True,
    health_check_enabled=True,
    rollback_enabled=True,
    timeout_minutes=60
)

deployer = DeploymentManager(config)
success = deployer.deploy()
```

### API Integration

The deployment system can be integrated with CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Deploy DMLogn8n
  run: |
    python3 deployment_manager.py production \
      --version ${{ github.sha }} \
      --no-backup \
      --timeout 60
```

## 🤝 Contributing

When contributing to the deployment system:

1. **Test in development first** before staging/production
2. **Update documentation** for any new features
3. **Add health checks** for new services
4. **Include rollback capabilities** for new components
5. **Add monitoring** for new functionality

## 📄 License

This deployment automation system is part of the DMLogn8n project. See the main project license for details.

---

## 🆘 Support

For deployment issues:

1. Check the logs in `/var/log/dmlogn8n/deployments/`
2. Run health checks to identify problems
3. Use rollback if deployment fails
4. Check the troubleshooting section above

For additional support, create an issue in the project repository.