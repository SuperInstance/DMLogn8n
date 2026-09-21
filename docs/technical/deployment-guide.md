# DMLog Deployment Guide

## Overview

This comprehensive guide covers deploying DMLog in various environments, from local development to production cloud deployments. DMLog supports multiple deployment strategies including Docker, cloud services, and edge deployments.

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB
- Network: 100 Mbps

**Recommended Requirements:**
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 50GB+ SSD
- Network: 1 Gbps

**Software Requirements:**
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+ (for local development)
- Git
- OpenSSL (for certificate generation)

### Environment Setup

1. **Clone the Repository**
```bash
git clone https://github.com/dmlog/dmlog.git
cd dmlog
```

2. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Setup Scripts**
```bash
chmod +x setup.sh deploy.sh
./setup.sh
```

## Deployment Environments

### 1. Development Environment

**Purpose**: Local development and testing
**Configuration**: Single machine, debug mode enabled
**Database**: Local PostgreSQL and Redis containers

#### Quick Start
```bash
# Deploy development environment
./deploy.sh development

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Grafana: http://localhost:3001
```

#### Manual Development Setup

1. **Start Services**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

2. **Database Migrations**
```bash
docker-compose exec api alembic upgrade head
```

3. **Load Sample Data**
```bash
docker-compose exec api python scripts/load_sample_data.py
```

4. **Development Server**
```bash
# API Server
uvicorn source_code.backend.api_server_new:app --reload --host 0.0.0.0 --port 8000

# Frontend (if not using container)
cd source_code/frontend
python -m http.server 3000
```

#### Development Configuration

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./source_code:/app/source_code
    environment:
      - DEBUG=true
      - RELOAD=true
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: dmlog_dev
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev123
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes

volumes:
  postgres_dev_data:
```

### 2. Staging Environment

**Purpose**: Pre-production testing
**Configuration**: Production-like setup, reduced resources
**Database**: Managed database services recommended

#### Staging Deployment
```bash
# Deploy to staging
./deploy.sh staging

# Or with custom configuration
./deploy.sh staging staging-config.env
```

#### Staging Configuration

```yaml
# docker-compose.staging.yml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./production_env/nginx/staging.conf:/etc/nginx/nginx.conf
      - ./production_env/ssl:/etc/nginx/ssl
    depends_on:
      - api

  api:
    image: dmlog/api:staging
    environment:
      - ENVIRONMENT=staging
      - DEBUG=false
      - DATABASE_URL=${STAGING_DATABASE_URL}
      - REDIS_URL=${STAGING_REDIS_URL}
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: dmlog_staging
      POSTGRES_USER: staging
      POSTGRES_PASSWORD: ${STAGING_DB_PASSWORD}
    volumes:
      - postgres_staging_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_staging_data:/data
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.25'

volumes:
  postgres_staging_data:
  redis_staging_data:
```

### 3. Production Environment

**Purpose**: Live production deployment
**Configuration**: High availability, security hardening, monitoring
**Database**: Managed services with backups

#### Production Deployment
```bash
# Deploy to production
./deploy.sh production

# For high availability
./deploy.sh production-ha

# With SSL certificates
./deploy.sh production-ssl
```

#### Production Architecture

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./production_env/nginx/prod.conf:/etc/nginx/nginx.conf
      - ./production_env/ssl:/etc/nginx/ssl
      - nginx_logs:/var/log/nginx
    depends_on:
      - api
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'

  api:
    image: dmlog/api:latest
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - app_logs:/app/logs
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/simple"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - postgres_backups:/backups
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    command: |
      redis-server
      --appendonly yes
      --maxmemory 2gb
      --maxmemory-policy allkeys-lru
      --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '0.5'

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./production_env/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./production_env/grafana/provisioning:/etc/grafana/provisioning
      - ./production_env/grafana/dashboards:/var/lib/grafana/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    restart: unless-stopped

volumes:
  postgres_data:
  postgres_backups:
  redis_data:
  qdrant_data:
  prometheus_data:
  grafana_data:
  nginx_logs:
  app_logs:

networks:
  default:
    driver: bridge
```

## Cloud Deployment

### 1. AWS EC2 Deployment

#### Prerequisites
- AWS CLI installed and configured
- EC2 key pair created
- Security groups configured

#### Deployment Script
```bash
#!/bin/bash
# deploy-aws-ec2.sh

EC2_INSTANCE=$1
VERSION=${2:-latest}
SSH_KEY=${3:-~/.ssh/dmlog-key.pem}

if [ -z "$EC2_INSTANCE" ]; then
    echo "Usage: $0 <ec2-instance> [version] [ssh-key]"
    exit 1
fi

echo "Deploying DMLog $VERSION to $EC2_INSTANCE"

# Copy deployment files
scp -i "$SSH_KEY" deploy.sh "$EC2_INSTANCE":/tmp/
scp -i "$SSH_KEY" -r production_env/ "$EC2_INSTANCE":/tmp/
scp -i "$SSH_KEY" -r source_code/ "$EC2_INSTANCE":/tmp/

# Execute deployment
ssh -i "$SSH_KEY" "$EC2_INSTANCE" << 'EOF'
    cd /tmp
    chmod +x deploy.sh

    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        usermod -aG docker ec2-user
    fi

    # Install Docker Compose if not present
    if ! command -v docker-compose &> /dev/null; then
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi

    # Deploy production environment
    sudo ./deploy.sh production

    # Setup SSL with Let's Encrypt
    sudo yum install -y certbot python3-certbot-nginx
    sudo certbot --nginx -d yourdomain.com

    # Setup automatic renewal
    echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
EOF

echo "Deployment completed to $EC2_INSTANCE"
```

#### AWS EC2 Configuration

```yaml
# production_env/aws/ec2-user-data.yml
#cloud-config
packages:
  - docker
  - docker-compose
  - nginx
  - certbot
  - python3-certbot-nginx

runcmd:
  - systemctl enable docker
  - systemctl start docker
  - usermod -aG docker ec2-user
  - docker network create dmlog-network
  - cd /opt/dmlog
  - docker-compose -f docker-compose.prod.yml up -d
```

### 2. Google Cloud Platform Deployment

#### GKE Deployment
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dmlog

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: dmlog-config
  namespace: dmlog
data:
  DATABASE_URL: "postgresql://user:pass@postgres:5432/dmlog"
  REDIS_URL: "redis://redis:6379/0"
  ENVIRONMENT: "production"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: dmlog-secrets
  namespace: dmlog
type: Opaque
data:
  SECRET_KEY: <base64-encoded-secret>
  OPENAI_API_KEY: <base64-encoded-key>
  ANTHROPIC_API_KEY: <base64-encoded-key>

---
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dmlog-api
  namespace: dmlog
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dmlog-api
  template:
    metadata:
      labels:
        app: dmlog-api
    spec:
      containers:
      - name: api
        image: gcr.io/your-project/dmlog-api:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: dmlog-config
        - secretRef:
            name: dmlog-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health/simple
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health/components
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# k8s/api-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: dmlog-api-service
  namespace: dmlog
spec:
  selector:
    app: dmlog-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dmlog-ingress
  namespace: dmlog
  annotations:
    kubernetes.io/ingress.class: "gce"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.dmlog.com
    secretName: dmlog-tls
  rules:
  - host: api.dmlog.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: dmlog-api-service
            port:
              number: 80
```

#### GKE Deployment Commands
```bash
# Create cluster
gcloud container clusters create dmlog-cluster \
    --zone=us-central1-a \
    --num-nodes=3 \
    --machine-type=e2-standard-2 \
    --enable-autoscaling \
    --min-nodes=2 \
    --max-nodes=10

# Get credentials
gcloud container clusters get-credentials dmlog-cluster --zone=us-central1-a

# Deploy application
kubectl apply -f k8s/

# Setup monitoring
kubectl apply -f https://github.com/prometheus-operator/prometheus-operator/releases/download/v0.60.1/bundle.yaml
```

### 3. Microsoft Azure Deployment

#### Azure Container Instances
```bash
#!/bin/bash
# deploy-azure.sh

RESOURCE_GROUP="dmlog-rg"
LOCATION="eastus"
CONTAINER_REGISTRY="dmlogregistry"
CONTAINER_NAME="dmlog-api"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create container registry
az acr create --resource-group $RESOURCE_GROUP --name $CONTAINER_REGISTRY --sku Basic

# Build and push image
az acr build --registry $CONTAINER_REGISTRY --image dmlog-api:latest .

# Deploy container instance
az container create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --image $CONTAINER_REGISTRY.azurecr.io/dmlog-api:latest \
    --cpu 2 \
    --memory 4 \
    --ports 8000 \
    --environment-variables \
        DATABASE_URL=$DATABASE_URL \
        REDIS_URL=$REDIS_URL \
        SECRET_KEY=$SECRET_KEY \
    --secure-environment-variables \
        OPENAI_API_KEY=$OPENAI_API_KEY \
        ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# Get IP address
az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query "ipAddress.ip" --output tsv
```

## Edge Deployment

### 1. NVIDIA Jetson Deployment

#### Jetson Optimization
```bash
#!/bin/bash
# deploy-jetson.sh

echo "Deploying DMLog to NVIDIA Jetson"

# Install Docker for Jetson
if [ ! -f /etc/docker/daemon.json ]; then
    sudo mkdir -p /etc/docker
    sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}
EOF
    sudo systemctl restart docker
fi

# Deploy with GPU support
docker-compose -f docker-compose.jetson.yml up -d

# Setup monitoring for Jetson
./scripts/setup_jetson_monitoring.sh
```

#### Jetson Configuration
```yaml
# docker-compose.jetson.yml
version: '3.8'
services:
  api:
    image: dmlog/api:jetson
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - CUDA_VISIBLE_DEVICES=0
    volumes:
      - /tmp/argus_socket:/tmp/argus_socket
      - /dev/video0:/dev/video0
    deploy:
      resources:
        limits:
          memory: 6G
          cpus: '4.0'
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### 2. Raspberry Pi Deployment

#### Pi Optimization
```bash
#!/bin/bash
# deploy-raspberry-pi.sh

echo "Deploying DMLog to Raspberry Pi"

# Enable 64-bit kernel if not already
if [ $(uname -m) != "aarch64" ]; then
    echo "Please enable 64-bit kernel for optimal performance"
    exit 1
fi

# Use ARM64 images
export DOCKER_PLATFORM=linux/arm64

# Deploy with resource limits
docker-compose -f docker-compose.pi.yml up -d

# Setup monitoring for Pi
./scripts/setup_pi_monitoring.sh
```

#### Raspberry Pi Configuration
```yaml
# docker-compose.pi.yml
version: '3.8'
services:
  api:
    image: dmlog/api:arm64
    environment:
      - ENVIRONMENT=edge
      - MAX_WORKERS=2
      - CACHE_SIZE=100
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
    command: >
      postgres
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c work_mem=4MB
      -c maintenance_work_mem=64MB
    deploy:
      resources:
        limits:
          memory: 1.5G
          cpus: '1.5'

  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --maxmemory 512MB
      --maxmemory-policy allkeys-lru
      --save ""
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
```

## Database Management

### Database Migrations

#### Running Migrations
```bash
# Development
docker-compose exec api alembic upgrade head

# Production
./scripts/migrate.sh production

# Custom migration
alembic revision --autogenerate -m "Add new feature"
alembic upgrade head
```

#### Migration Script
```bash
#!/bin/bash
# scripts/migrate.sh

ENVIRONMENT=$1
VERSION=${2:-head}

if [ -z "$ENVIRONMENT" ]; then
    echo "Usage: $0 <environment> [version]"
    exit 1
fi

echo "Running migrations for $ENVIRONMENT environment"

case $ENVIRONMENT in
    "development")
        docker-compose exec api alembic upgrade $VERSION
        ;;
    "staging")
        docker-compose -f docker-compose.staging.yml exec api alembic upgrade $VERSION
        ;;
    "production")
        docker-compose -f docker-compose.prod.yml exec api alembic upgrade $VERSION
        ;;
    *)
        echo "Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

echo "Migrations completed"
```

### Database Backups

#### Automated Backups
```bash
#!/bin/bash
# scripts/backup_database.sh

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/dmlog_backup_$TIMESTAMP.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove old backups (keep last 30 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

#### Backup Schedule
```bash
# Add to crontab
# Daily backup at 2 AM
0 2 * * * /path/to/scripts/backup_database.sh

# Weekly backup on Sunday at 3 AM
0 3 * * 0 /path/to/scripts/full_backup.sh
```

### Database Restoration

#### Restoration Script
```bash
#!/bin/bash
# scripts/restore_database.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "Restoring database from $BACKUP_FILE"

# Stop API service
docker-compose stop api

# Restore database
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE | docker-compose exec -T postgres psql -U $POSTGRES_USER $POSTGRES_DB
else
    docker-compose exec -T postgres psql -U $POSTGRES_USER $POSTGRES_DB < $BACKUP_FILE
fi

# Start API service
docker-compose start api

echo "Database restoration completed"
```

## SSL/TLS Configuration

### Let's Encrypt Setup

#### Automated Certificate Setup
```bash
#!/bin/bash
# scripts/setup_ssl.sh

DOMAIN=$1
EMAIL=$2

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Usage: $0 <domain> <email>"
    exit 1
fi

echo "Setting up SSL for $DOMAIN"

# Install certbot
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --non-interactive

# Setup auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# Test renewal
sudo certbot renew --dry-run

echo "SSL setup completed for $DOMAIN"
```

#### Nginx SSL Configuration
```nginx
# production_env/nginx/ssl.conf
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Monitoring and Logging

### Prometheus Configuration

```yaml
# production_env/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'dmlog-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Grafana Dashboards

#### Import Dashboards
```bash
#!/bin/bash
# scripts/setup_grafana.sh

GRAFANA_URL="http://localhost:3001"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="admin"

# Import dashboards
curl -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
     -X POST \
     -H "Content-Type: application/json" \
     -d @production_env/grafana/dashboards/dmlog-overview.json \
     "$GRAFANA_URL/api/dashboards/db"

curl -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
     -X POST \
     -H "Content-Type: application/json" \
     -d @production_env/grafana/dashboards/database-performance.json \
     "$GRAFANA_URL/api/dashboards/db"

echo "Grafana dashboards imported"
```

## Security Hardening

### Security Checklist

```bash
#!/bin/bash
# scripts/security_check.sh

echo "Running security checks..."

# Check for open ports
nmap -sT -O localhost

# Check Docker security
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image dmlog/api:latest

# Check SSL certificates
ssl-cert-check -c yourdomain.com

# Check file permissions
find . -type f -perm /o+w -ls

# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

echo "Security checks completed"
```

### Security Headers

```nginx
# production_env/nginx/security.conf
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Check database status
docker-compose exec postgres pg_isready

# Check connection logs
docker-compose logs postgres

# Test connection from API container
docker-compose exec api python -c "
import asyncpg
import asyncio

async def test():
    conn = await asyncpg.connect('postgresql://user:pass@postgres:5432/dmlog')
    print('Database connection successful')
    await conn.close()

asyncio.run(test())
"
```

#### 2. Redis Connection Issues
```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis

# Test Redis connection
docker-compose exec api python -c "
import redis
r = redis.Redis(host='redis', port=6379, db=0)
print('Redis connection successful:', r.ping())
"
```

#### 3. SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/cert.pem -text -noout

# Test SSL configuration
sslscan yourdomain.com

# Renew certificate manually
sudo certbot renew --force-renewal
```

#### 4. Performance Issues
```bash
# Check resource usage
docker stats

# Check application logs
docker-compose logs api

# Profile application
docker-compose exec api python -m cProfile -o profile.stats scripts/profile_app.py

# Database performance
docker-compose exec postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"
```

### Log Analysis

#### Centralized Logging Setup
```yaml
# docker-compose.logging.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    volumes:
      - ./production_env/logstash/pipeline:/usr/share/logstash/pipeline
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

## Maintenance

### Regular Maintenance Tasks

```bash
#!/bin/bash
# scripts/maintenance.sh

echo "Running maintenance tasks..."

# Clean up Docker images
docker system prune -f

# Clean up old logs
find /var/log -name "*.log" -mtime +30 -delete

# Update dependencies
docker-compose pull

# Restart services if needed
docker-compose up -d

# Check health
curl -f http://localhost:8000/api/v1/health || echo "Health check failed"

echo "Maintenance completed"
```

### Update Process

```bash
#!/bin/bash
# scripts/update.sh

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

echo "Updating to version $VERSION"

# Backup current version
./scripts/backup_database.sh

# Pull new images
docker-compose pull

# Run migrations
docker-compose exec api alembic upgrade head

# Restart services
docker-compose up -d

# Verify update
curl -f http://localhost:8000/api/v1/health || {
    echo "Update failed, rolling back..."
    docker-compose rollback
    exit 1
}

echo "Update to $VERSION completed successfully"
```

This comprehensive deployment guide provides everything needed to deploy DMLog in various environments, from local development to production cloud deployments. The guide includes automation scripts, security configurations, monitoring setup, and troubleshooting procedures to ensure successful deployment and operation of the DMLog system.