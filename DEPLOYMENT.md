# DMLog Deployment Guide

This guide covers deploying DMLog to various environments including local development, production, AWS EC2, and NVIDIA Jetson devices.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Deployment Environments](#deployment-environments)
4. [Configuration](#configuration)
5. [Monitoring](#monitoring)
6. [Backup and Restore](#backup-and-restore)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Python** 3.11+
- **Git**

### Optional Software

- **Node.js** 18+ (for frontend development)
- **PostgreSQL** client tools
- **Redis** CLI tools

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4GB | 8GB+ |
| Storage | 20GB | 50GB+ SSD |
| Network | 10 Mbps | 100 Mbps+ |

## Quick Start

### Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd DMLog

# Deploy to development
./deploy.sh development
```

This will:
- Set up the development environment
- Build and start all services
- Run database migrations
- Start the API server and monitoring tools

Access points:
- **API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9090

## Deployment Environments

### 1. Development

Deploy the full stack with hot-reload enabled:

```bash
./deploy.sh development [version]
```

Features:
- Hot-reload for backend
- Debug mode enabled
- All monitoring tools included
- Verbose logging

### 2. Production

Deploy optimized for production:

```bash
./deploy.sh production [version]
```

Features:
- Optimized Docker images
- Production settings
- Limited debug output
- Security headers
- Resource limits

### 3. AWS EC2

Deploy to an AWS EC2 instance:

```bash
./deploy.sh aws-ec2 [version] <host> [user]
```

Example:
```bash
./deploy.sh aws-ec2 latest ec2-user@ec2-18-191-123-45.us-east-2.compute.amazonaws.com
```

Requirements:
- EC2 instance with Docker support
- SSH access with key pair
- Security group allowing ports 80, 443, 8000

### 4. NVIDIA Jetson

Deploy to NVIDIA Jetson for AI workloads:

```bash
./deploy.sh jetson [version]
```

Features:
- GPU acceleration support
- Optimized for ARM64
- AI/ML tools included

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key settings:

```env
# Application
APP_NAME=DMLog
DEBUG=false
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dmlog

# Redis
REDIS_URL=redis://host:6379/0

# Vector Database
QDRANT_URL=http://host:6333

# API Keys
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=https://yourdomain.com
```

### Database Configuration

The application uses PostgreSQL with async connection pooling. Update the `DATABASE_URL` in your `.env` file:

```
postgresql+asyncpg://username:password@hostname:5432/database_name
```

### Redis Configuration

Redis is used for caching and session storage:

```
redis://hostname:6379/database_number
```

## Monitoring

### Health Checks

The application provides multiple health endpoints:

- Simple: `/api/v1/health/simple`
- Detailed: `/api/v1/health`
- Component: `/api/v1/health/components`

### Metrics

Prometheus metrics are exposed at `/metrics`

Key metrics:
- HTTP request count and duration
- Database query performance
- Cache hit rates
- System resource usage

### Grafana Dashboards

Grafana is included with pre-configured dashboards:

- System Overview
- Application Performance
- Database Metrics
- Cache Performance

Access: http://localhost:3001 (admin/admin)

## Docker Compose Files

### Development (`docker-compose.dev.yml`)

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: dmlog
      POSTGRES_USER: dmlog
      POSTGRES_PASSWORD: password
    volumes:
      - ../data/postgres:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - ../data/redis:/data

  backend:
    build:
      context: ../../source_code/backend
      dockerfile: Dockerfile.dev
    volumes:
      - ../../source_code/backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      - DEBUG=true
```

### Production (`docker-compose.prod.yml`)

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: dmlog
      POSTGRES_USER: dmlog
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  backend:
    image: dmlog-backend:${VERSION}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    environment:
      - DEBUG=false
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
```

## Backup and Restore

### Create Backup

```bash
./deploy.sh backup
```

This creates:
- Database dump (SQL)
- Redis snapshot
- Application data
- Compressed archive in `backups/`

### Restore from Backup

```bash
./deploy.sh restore backup_20240122_143022.tar.gz
```

### Automated Backups

Set up cron jobs for automated backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/DMLog/deploy.sh backup
```

## SSL/TLS Configuration

### Using Let's Encrypt

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/
```

Update `nginx.conf` to use SSL certificates.

### Using Self-Signed Certificates

For development:

```bash
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes
```

## Scaling

### Horizontal Scaling

Use Docker Swarm or Kubernetes:

```bash
# Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.prod.yml dmlog

# Kubernetes
kubectl apply -f k8s/
```

### Database Scaling

1. **Read Replicas**: Configure read replicas for better read performance
2. **Connection Pooling**: Adjust pool size in settings
3. **Index Optimization**: Add database indexes for common queries

### Cache Scaling

1. **Redis Cluster**: Set up Redis cluster for high availability
2. **Cache Warming**: Implement cache warming strategies
3. **Cache Policies**: Adjust TTL values based on usage

## Security

### Production Security Checklist

- [ ] Change default passwords
- [ ] Update SECRET_KEY
- [ ] Configure HTTPS
- [ ] Set up firewall rules
- [ ] Enable security headers
- [ ] Configure rate limiting
- [ ] Set up log monitoring
- [ ] Regular security updates
- [ ] Backup encryption
- [ ] Network segmentation

### Docker Security

```bash
# Run containers as non-root
user: 1000:1000

# Read-only filesystem
read_only: true

# Resource limits
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```bash
# Check database status
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Test connection
docker exec -it dmlog-postgres psql -U dmlog -d dmlog
```

#### 2. Redis Connection Failed

```bash
# Check Redis status
docker-compose ps redis

# Test connection
docker exec -it dmlog-redis redis-cli ping
```

#### 3. High Memory Usage

```bash
# Check resource usage
docker stats

# Clean up unused containers
docker system prune -a
```

#### 4. Slow API Response

```bash
# Check logs
docker-compose logs backend

# Monitor database queries
# Enable query logging in .env
LOG_LEVEL=DEBUG
```

### Performance Tuning

1. **Database**: Enable query caching, add indexes
2. **Redis**: Increase memory limit, use Redis Cluster
3. **Application**: Adjust worker count, enable gzip
4. **Network**: Use CDN, enable HTTP/2

## Logs

### Viewing Logs

```bash
# All services
./deploy.sh logs

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Log Levels

Configure in `.env`:

```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json
```

## Updates

### Updating the Application

```bash
# Pull latest changes
git pull

# Redeploy
./deploy.sh production

# Or specific version
./deploy.sh production 1.1.0
```

### Zero-Downtime Updates

For production:

```bash
# Build new image
docker build -t dmlog-backend:new .

# Update running container
docker service update dmlog_backend --image dmlog-backend:new
```

## Support

For support:
1. Check the [troubleshooting guide](#troubleshooting)
2. Review logs for error messages
3. Check GitHub Issues
4. Contact the development team

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to DMLog.