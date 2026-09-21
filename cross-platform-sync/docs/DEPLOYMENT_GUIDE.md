# DMlogn8n Cross-Platform Sync - Deployment Guide

This comprehensive guide covers deployment strategies for the DMlogn8n Cross-Platform Sync system across various environments and platforms.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Redis Configuration](#redis-configuration)
5. [Application Deployment](#application-deployment)
6. [Load Balancing](#load-balancing)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Security Hardening](#security-hardening)
9. [Backup and Recovery](#backup-and-recovery)
10. [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **Memory**: 4GB RAM
- **Storage**: 50GB SSD
- **Network**: 100 Mbps

#### Recommended Requirements
- **CPU**: 4+ cores
- **Memory**: 8GB+ RAM
- **Storage**: 100GB+ SSD
- **Network**: 1 Gbps

### Software Dependencies

- **Node.js**: 16.x or later
- **PostgreSQL**: 13.x or later
- **Redis**: 6.x or later
- **Nginx**: 1.18+ (for production)
- **Docker**: 20.x+ (optional)
- **Kubernetes**: 1.20+ (optional)

## 🌍 Environment Setup

### Development Environment

```bash
# Clone the repository
git clone https://github.com/dmlogn8n/cross-platform-sync.git
cd cross-platform-sync

# Install dependencies
npm install

# Setup environment variables
cp .env.example .env.development

# Start development services
docker-compose -f docker-compose.dev.yml up -d

# Run database migrations
npm run migrate

# Start development server
npm run dev
```

### Staging Environment

```bash
# Create staging environment file
cp .env.example .env.staging

# Configure staging variables
# DB_HOST=staging-db.example.com
# REDIS_HOST=staging-redis.example.com
# API_HOST=staging-api.dmlogn8n.com
# NODE_ENV=staging

# Build application
npm run build

# Deploy to staging
npm run deploy:staging
```

### Production Environment

```bash
# Create production environment file
cp .env.example .env.production

# Configure production variables with secure values
# Use AWS Parameter Store or HashiCorp Vault for secrets

# Build optimized application
npm run build:prod

# Deploy to production
npm run deploy:prod
```

## 🗄️ Database Configuration

### PostgreSQL Setup

#### Installation (Ubuntu/Debian)
```bash
# Update package lists
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE dmlogn8n_sync;
CREATE USER dmlogn8n WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE dmlogn8n_sync TO dmlogn8n;
ALTER USER dmlogn8n CREATEDB;
```

#### Configuration
```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/13/main/postgresql.conf

# Key settings to optimize:
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

#### Connection Pooling
```bash
# Create pgBouncer configuration
sudo apt install pgbouncer

# Configure pgbouncer
sudo nano /etc/pgbouncer/pgbouncer.ini

[databases]
dmlogn8n_sync = host=localhost port=5432 dbname=dmlogn8n_sync

[pgbouncer]
listen_port = 6432
listen_addr = 127.0.0.1
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
logfile = /var/log/pgbouncer/pgbouncer.log
admin_users = dmlogn8n
stats_users = stats, dmlogn8n
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 5
max_db_connections = 50
max_user_connections = 50
server_reset_query = DISCARD ALL
track_extra_parameters = application_name
```

#### Database Schema Setup
```bash
# Run schema creation
psql -h localhost -U dmlogn8n -d dmlogn8n_sync -f database/01-universal-save-schema.sql

# Create indexes for performance
psql -h localhost -U dmlogn8n -d dmlogn8n_sync -f database/indexes.sql

# Setup Row Level Security
psql -h localhost -U dmlogn8n -d dmlogn8n_sync -f database/rls.sql
```

### Backup Strategy
```bash
# Create backup script
cat > /usr/local/bin/backup-dmlogn8n.sh << 'EOF'
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/dmlogn8n"
DB_NAME="dmlogn8n_sync"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -h localhost -U dmlogn8n -d $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Remove backups older than 7 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/db_backup_$DATE.sql.gz"
EOF

# Make script executable
chmod +x /usr/local/bin/backup-dmlogn8n.sh

# Schedule daily backups
echo "0 2 * * * /usr/local/bin/backup-dmlogn8n.sh" | crontab -
```

## 🔴 Redis Configuration

### Installation
```bash
# Install Redis
sudo apt install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
```

### Production Configuration
```conf
# /etc/redis/redis.conf

# Network
bind 127.0.0.1
port 6379
protected-mode yes
requirepass your_secure_redis_password

# Memory
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# AOF (Append Only File)
appendonly yes
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log

# Performance
tcp-keepalive 300
timeout 0
tcp-backlog 511

# Security
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG "CONFIG_b835c3f8a5d2e7f1c6a9b4e0d7f3a2b1"
```

### Redis Cluster Setup (High Availability)
```bash
# Install Redis Cluster
sudo apt install redis-tools

# Create cluster configuration
cat > redis-cluster.conf << 'EOF'
port 7000
cluster-enabled yes
cluster-config-file nodes-7000.conf
cluster-node-timeout 5000
appendonly yes
appendfilename appendonly-7000.aof
dbfilename dump-7000.rdb
logfile /var/log/redis/redis-7000.log
EOF

# Setup multiple Redis instances
for port in 7000 7001 7002 7003 7004 7005; do
    mkdir -p /etc/redis/cluster
    cp redis-cluster.conf /etc/redis/cluster/redis-$port.conf
    sed -i "s/7000/$port/g" /etc/redis/cluster/redis-$port.conf
    redis-server /etc/redis/cluster/redis-$port.conf &
done

# Create cluster
redis-cli --cluster create \
  127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 \
  127.0.0.1:7003 127.0.0.1:7004 127.0.0.1:7005 \
  --cluster-replicas 1
```

## 🚀 Application Deployment

### Docker Deployment

#### Multi-stage Dockerfile
```dockerfile
# Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache python3 make g++

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM node:18-alpine AS production

# Install runtime dependencies
RUN apk add --no-cache dumb-init

# Create app user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S syncuser -u 1001

WORKDIR /app

# Copy built application
COPY --from=builder --chown=syncuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=syncuser:nodejs /app/dist ./dist
COPY --from=builder --chown=syncuser:nodejs /app/package*.json ./

# Create non-root user
USER syncuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node healthcheck.js

# Expose port
EXPOSE 3000

# Start application
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/sync-api.js"]
```

#### Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  sync-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DB_HOST=postgres
      - REDIS_HOST=redis
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/v1/sync/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:13-alpine
    environment:
      - POSTGRES_DB=dmlogn8n_sync
      - POSTGRES_USER=dmlogn8n
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dmlogn8n"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:6-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - sync-api
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes Deployment

#### Namespace and ConfigMaps
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dmlogn8n-sync
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: sync-config
  namespace: dmlogn8n-sync
data:
  NODE_ENV: "production"
  API_PORT: "3000"
  DB_HOST: "postgres-service"
  DB_PORT: "5432"
  DB_NAME: "dmlogn8n_sync"
  REDIS_HOST: "redis-service"
  REDIS_PORT: "6379"
```

#### Secrets
```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: sync-secrets
  namespace: dmlogn8n-sync
type: Opaque
data:
  DB_PASSWORD: <base64-encoded-password>
  REDIS_PASSWORD: <base64-encoded-password>
  JWT_SECRET: <base64-encoded-jwt-secret>
  AWS_ACCESS_KEY_ID: <base64-encoded-aws-key>
  AWS_SECRET_ACCESS_KEY: <base64-encoded-aws-secret>
```

#### Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sync-api
  namespace: dmlogn8n-sync
  labels:
    app: sync-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sync-api
  template:
    metadata:
      labels:
        app: sync-api
    spec:
      containers:
      - name: sync-api
        image: dmlogn8n/sync-api:latest
        ports:
        - containerPort: 3000
        envFrom:
        - configMapRef:
            name: sync-config
        - secretRef:
            name: sync-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/sync/health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/sync/health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]
```

#### Service
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: sync-api-service
  namespace: dmlogn8n-sync
spec:
  selector:
    app: sync-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: ClusterIP
```

#### Ingress
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sync-ingress
  namespace: dmlogn8n-sync
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - api.dmlogn8n.com
    secretName: dmlogn8n-tls
  rules:
  - host: api.dmlogn8n.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: sync-api-service
            port:
              number: 80
```

### AWS Deployment

#### ECS Task Definition
```json
{
  "family": "dmlogn8n-sync",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "sync-api",
      "image": "your-account.dkr.ecr.region.amazonaws.com/dmlogn8n-sync:latest",
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "NODE_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DB_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:dmlogn8n/db-password"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/dmlogn8n-sync",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:3000/api/v1/sync/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

#### Serverless Configuration
```yaml
# serverless.yml
service: dmlogn8n-sync

provider:
  name: aws
  runtime: nodejs18.x
  region: us-east-1
  stage: production
  environment:
    DB_HOST: ${ssm:/dmlogn8n/prod/db/host}
    REDIS_HOST: ${ssm:/dmlogn8n/prod/redis/host}

functions:
  api:
    handler: dist/lambda.handler
    events:
      - httpApi:
          path: /{proxy+}
          method: ANY
    timeout: 30
    memorySize: 512
    reservedConcurrency: 100

  websocket:
    handler: dist/websocket.handler
    events:
      - websocket:
          route: $connect
      - websocket:
          route: $disconnect
      - websocket:
          route: $default

resources:
  Resources:
    WebSocketApi:
      Type: AWS::ApiGatewayV2::Api
      Properties:
        Name: dmlogn8n-websocket
        ProtocolType: WEBSOCKET
```

## ⚖️ Load Balancing

### Nginx Configuration
```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream sync_api {
        least_conn;
        server sync-api-1:3000 max_fails=3 fail_timeout=30s;
        server sync-api-2:3000 max_fails=3 fail_timeout=30s;
        server sync-api-3:3000 max_fails=3 fail_timeout=30s;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=sync:10m rate=5r/s;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    server {
        listen 80;
        server_name api.dmlogn8n.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name api.dmlogn8n.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # API routes
        location /api/v1/sync/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://sync_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Timeouts
            proxy_connect_timeout 5s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # WebSocket routes
        location /ws {
            proxy_pass http://sync_api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket specific timeouts
            proxy_read_timeout 86400;
            proxy_send_timeout 86400;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

### AWS Application Load Balancer
```yaml
# alb-target-group.yaml
Resources:
  SyncAPITargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: dmlogn8n-sync-api
      Port: 3000
      Protocol: HTTP
      VpcId: !Ref VPC
      HealthCheckProtocol: HTTP
      HealthCheckPort: traffic-port
      HealthCheckPath: /api/v1/sync/health
      HealthCheckIntervalSeconds: 30
      HealthCheckTimeoutSeconds: 5
      HealthyThresholdCount: 3
      UnhealthyThresholdCount: 3
      Matcher:
        HttpCode: 200

  SyncLoadBalancer:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: dmlogn8n-sync-alb
      Scheme: internet-facing
      Type: application
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2
      SecurityGroups:
        - !Ref LoadBalancerSecurityGroup
```

## 📊 Monitoring and Logging

### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'dmlogn8n-sync-api'
    static_configs:
      - targets: ['sync-api:3000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

rule_files:
  - "dmlogn8n_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "DMlogn8n Sync Monitoring",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job=\"dmlogn8n-sync-api\"}[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Active Connections",
        "type": "stat",
        "targets": [
          {
            "expr": "websocket_connections_total"
          }
        ]
      },
      {
        "title": "Sync Operations",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(sync_operations_total[5m])",
            "legendFormat": "Sync Rate"
          }
        ]
      }
    ]
  }
}
```

### ELK Stack Configuration
```yaml
# logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "dmlogn8n-sync" {
    json {
      source => "message"
    }

    date {
      match => [ "timestamp", "ISO8601" ]
    }

    if [level] == "error" {
      mutate {
        add_tag => [ "error" ]
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "dmlogn8n-sync-%{+YYYY.MM.dd}"
  }
}
```

## 🔒 Security Hardening

### Environment Security
```bash
# Create non-root user for application
sudo useradd -r -s /bin/false dmlogn8n

# Set proper file permissions
sudo chown -R dmlogn8n:dmlogn8n /opt/dmlogn8n-sync
sudo chmod 750 /opt/dmlogn8n-sync

# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 3000/tcp  # Direct API access
sudo ufw enable
```

### Application Security
```javascript
// security/middleware.js
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const slowDown = require('express-slow-down');

// Security headers
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            scriptSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            imgSrc: ["'self'", "data:", "https:"]
        }
    },
    hsts: {
        maxAge: 31536000,
        includeSubDomains: true,
        preload: true
    }
}));

// Rate limiting
const apiLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // limit each IP to 100 requests per windowMs
    message: 'Too many requests from this IP'
});

const syncLimiter = rateLimit({
    windowMs: 1 * 60 * 1000, // 1 minute
    max: 10, // limit sync operations
    message: 'Too many sync operations'
});

// Apply rate limiters
app.use('/api/v1/sync', apiLimiter);
app.post('/api/v1/sync/sync', syncLimiter);

// Slow down suspicious requests
const speedLimiter = slowDown({
    windowMs: 15 * 60 * 1000,
    delayAfter: 50,
    delayMs: 500
});
```

### Database Security
```sql
-- Create limited user for application
CREATE USER dmlogn8n_app WITH PASSWORD 'secure_app_password';

-- Grant minimum required permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO dmlogn8n_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO dmlogn8n_app;

-- Create read-only user for analytics
CREATE USER dmlogn8n_readonly WITH PASSWORD 'secure_readonly_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dmlogn8n_readonly;

-- Enable Row Level Security
ALTER TABLE save_games ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_operations ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_conflicts ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY user_save_games ON save_games
    FOR ALL TO dmlogn8n_app
    USING (user_id = current_setting('app.current_user_id')::UUID);
```

## 💾 Backup and Recovery

### Automated Backup Script
```bash
#!/bin/bash
# backup.sh

set -e

BACKUP_DIR="/backup/dmlogn8n"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup
echo "Starting database backup..."
pg_dump -h localhost -U dmlogn8n -d dmlogn8n_sync \
    --format=custom \
    --compress=9 \
    --file="$BACKUP_DIR/db_backup_$DATE.dump"

# Redis backup
echo "Starting Redis backup..."
redis-cli --rdb "$BACKUP_DIR/redis_backup_$DATE.rdb"

# Application data backup
echo "Starting application data backup..."
tar -czf "$BACKUP_DIR/app_data_$DATE.tar.gz" \
    /opt/dmlogn8n-sync/data \
    /opt/dmlogn8n-sync/logs \
    /opt/dmlogn8n-sync/config

# Upload to AWS S3
echo "Uploading to S3..."
aws s3 sync "$BACKUP_DIR" s3://dmlogn8n-backups/$(date +%Y-%m-%d)/ \
    --delete \
    --storage-class IA

# Cleanup old backups
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -name "*_$DATE.*" -mtime +$RETENTION_DAYS -delete

# Verify backup
echo "Verifying backup..."
if pg_restore --list "$BACKUP_DIR/db_backup_$DATE.dump" > /dev/null; then
    echo "✅ Database backup verified"
else
    echo "❌ Database backup verification failed"
    exit 1
fi

echo "✅ Backup completed successfully: $BACKUP_DIR"
```

### Recovery Script
```bash
#!/bin/bash
# recover.sh

set -e

BACKUP_FILE=$1
RECOVERY_DIR="/tmp/dmlogn8n-recovery"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "Starting recovery from: $BACKUP_FILE"

# Create recovery directory
mkdir -p "$RECOVERY_DIR"

# Download from S3 if needed
if [[ $BACKUP_FILE == s3://* ]]; then
    echo "Downloading backup from S3..."
    aws s3 cp "$BACKUP_FILE" "$RECOVERY_DIR/"
    BACKUP_FILE=$(ls "$RECOVERY_DIR"/*.dump | head -1)
fi

# Stop application
echo "Stopping application..."
sudo systemctl stop dmlogn8n-sync

# Database recovery
echo "Recovering database..."
pg_restore -h localhost -U dmlogn8n -d dmlogn8n_sync \
    --clean --if-exists \
    --verbose "$BACKUP_FILE"

# Start application
echo "Starting application..."
sudo systemctl start dmlogn8n-sync

# Verify recovery
echo "Verifying recovery..."
sleep 10

if curl -f http://localhost:3000/api/v1/sync/health > /dev/null; then
    echo "✅ Recovery completed successfully"
else
    echo "❌ Recovery verification failed"
    exit 1
fi

# Cleanup
rm -rf "$RECOVERY_DIR"

echo "✅ Recovery completed"
```

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U dmlogn8n -d dmlogn8n_sync -c "SELECT 1;"

# Check logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

#### Redis Connection Issues
```bash
# Check Redis status
sudo systemctl status redis

# Test connection
redis-cli ping

# Check logs
sudo tail -f /var/log/redis/redis-server.log
```

#### Application Issues
```bash
# Check application logs
sudo journalctl -u dmlogn8n-sync -f

# Check process status
ps aux | grep node

# Check port availability
netstat -tlnp | grep :3000
```

#### Performance Issues
```bash
# Check system resources
htop
iotop
df -h

# Check database performance
psql -h localhost -U dmlogn8n -d dmlogn8n_sync -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;"

# Check Redis performance
redis-cli --latency-history -i 1
```

### Debug Mode
```bash
# Enable debug logging
export NODE_ENV=development
export DEBUG=dmlogn8n:*

# Start with debugger
node --inspect dist/sync-api.js
```

### Health Checks
```bash
# Comprehensive health check
#!/bin/bash
echo "=== DMlogn8n Sync Health Check ==="

# Check application
if curl -f http://localhost:3000/api/v1/sync/health > /dev/null; then
    echo "✅ API: Healthy"
else
    echo "❌ API: Unhealthy"
fi

# Check database
if pg_isready -h localhost -p 5432 -U dmlogn8n > /dev/null; then
    echo "✅ Database: Ready"
else
    echo "❌ Database: Not ready"
fi

# Check Redis
if redis-cli ping > /dev/null; then
    echo "✅ Redis: Connected"
else
    echo "❌ Redis: Not connected"
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 80 ]; then
    echo "✅ Disk: OK (${DISK_USAGE}% used)"
else
    echo "⚠️  Disk: High usage (${DISK_USAGE}% used)"
fi

# Check memory
MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ $MEMORY_USAGE -lt 80 ]; then
    echo "✅ Memory: OK (${MEMORY_USAGE}% used)"
else
    echo "⚠️  Memory: High usage (${MEMORY_USAGE}% used)"
fi

echo "=== Health Check Complete ==="
```

This deployment guide provides comprehensive instructions for deploying the DMlogn8n Cross-Platform Sync system across various environments, from development to production, with detailed configuration, monitoring, and troubleshooting guidance.