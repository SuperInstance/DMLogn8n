# DMlogn8n Social Hub Deployment Guide
# =====================================

This comprehensive guide covers the deployment, configuration, and maintenance of the DMlogn8n Social Hub platform. The platform is designed to scale to 100,000+ users with real-time features, content moderation, and mobile-responsive design.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Architecture Overview](#architecture-overview)
3. [Quick Start](#quick-start)
4. [Detailed Installation](#detailed-installation)
5. [Configuration](#configuration)
6. [Database Setup](#database-setup)
7. [Redis Configuration](#redis-configuration)
8. [Load Balancer Setup](#load-balancer-setup)
9. [SSL/TLS Configuration](#ssltls-configuration)
10. [Environment Variables](#environment-variables)
11. [Docker Deployment](#docker-deployment)
12. [Kubernetes Deployment](#kubernetes-deployment)
13. [Monitoring and Logging](#monitoring-and-logging)
14. [Performance Optimization](#performance-optimization)
15. [Security Hardening](#security-hardening)
16. [Backup and Recovery](#backup-and-recovery)
17. [Scaling Strategies](#scaling-strategies)
18. [Maintenance Procedures](#maintenance-procedures)
19. [Troubleshooting](#troubleshooting)
20. [Testing and Validation](#testing-and-validation)

## System Requirements

### Minimum Requirements
- **CPU**: 4 cores (8+ recommended for production)
- **RAM**: 8GB (16GB+ recommended for production)
- **Storage**: 100GB SSD (500GB+ for production with media files)
- **Network**: 1Gbps (10Gbps recommended for high traffic)
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+

### Recommended Production Setup
- **Application Servers**: 3-6 instances (8 cores, 16GB RAM each)
- **Database Server**: 1 primary + 2 replicas (16 cores, 32GB RAM)
- **Redis Cluster**: 3 nodes (4 cores, 8GB RAM each)
- **Load Balancer**: 2 instances (4 cores, 8GB RAM each)
- **File Storage**: 1TB+ with CDN integration

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer  │────│   Load Balancer  │────│   Load Balancer  │
│   (Nginx/HAProxy)│    │   (Nginx/HAProxy)│    │   (Nginx/HAProxy)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
          ┌─────────────────────────────────────────────────────────┐
          │                  Application Layer                      │
          │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
          │  │API Node 1│  │API Node 2│  │API Node 3│  │API Node N│  │
          │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │
          │                                                         │
          │  ┌─────────────────────────────────────────────────────┐  │
          │  │           WebSocket Servers (Node.js)              │  │
          │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐          │  │
          │  │  │ WS Node 1│  │ WS Node 2│  │ WS Node 3│          │  │
          │  │  └─────────┘  └─────────┘  └─────────┘          │  │
          │  └─────────────────────────────────────────────────────┘  │
          └─────────────────────────────────────────────────────────┘
                                  │
          ┌─────────────────────────────────────────────────────────┐
          │                    Services Layer                       │
          │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
          │  │Notification  │  │  Content     │  │Achievement  │      │
          │  │   Service    │  │Moderation   │  │   Service   │      │
          │  └─────────────┘  └─────────────┘  └─────────────┘      │
          └─────────────────────────────────────────────────────────┘
                                  │
          ┌─────────────────────────────────────────────────────────┐
          │                     Data Layer                           │
          │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
          │  │ PostgreSQL   │  │    Redis     │  │  File Store │      │
          │  │  (Primary)   │  │   Cluster    │  │   (S3/NFS)  │      │
          │  └─────────────┘  └─────────────┘  └─────────────┘      │
          │  ┌─────────────┐  ┌─────────────┐                       │
          │  │ PostgreSQL   │  │ PostgreSQL   │                       │
          │  │ (Replica 1)  │  │ (Replica 2)  │                       │
          │  └─────────────┘  └─────────────┘                       │
          └─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/your-org/dmlogn8n-social-hub.git
cd dmlogn8n-social-hub
```

### 2. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Docker Quick Start
```bash
# Build and start all services
docker-compose up -d

# Run database migrations
docker-compose exec api python -m alembic upgrade head

# Create initial admin user
docker-compose exec api python scripts/create_admin.py
```

### 4. Access the Platform
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Admin Panel**: http://localhost:8000/admin

## Detailed Installation

### 1. System Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y postgresql postgresql-contrib redis-server
sudo apt install -y nginx supervisor
sudo apt install -y build-essential libpq-dev

# CentOS/RHEL
sudo yum update
sudo yum install -y python311 python311-devel
sudo yum install -y postgresql-server postgresql-contrib redis
sudo yum install -y nginx supervisor
sudo yum install -y gcc gcc-c++ libpq-devel
```

### 2. Python Environment
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements_social.txt
pip install -r requirements_test.txt
```

### 3. Database Setup
```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE dmlogn8n_social;
CREATE USER dmlogn8n WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE dmlogn8n_social TO dmlogn8n;
ALTER USER dmlogn8n CREATEDB;
\q
EOF

# Run migrations
python -m alembic upgrade head
```

### 4. Redis Setup
```bash
# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Configure Redis for clustering (if needed)
sudo nano /etc/redis/redis.conf
```

### 5. Application Setup
```bash
# Copy configuration files
cp config/settings.py.example config/settings.py
cp config/database.py.example config/database.py

# Set up environment variables
nano .env
```

### 6. Web Server Configuration
```bash
# Configure Nginx
sudo cp deployment/nginx/social-hub.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/social-hub.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Configure Supervisor
sudo cp deployment/supervisor/social-hub.conf /etc/supervisor/conf.d/
sudo supervisorctl reread
sudo supervisorctl update
```

## Configuration

### Environment Variables (.env)
```bash
# Application
APP_NAME=DMlogn8n Social Hub
APP_VERSION=1.0.0
APP_ENV=production
SECRET_KEY=your-super-secret-key-here
DEBUG=false

# Database
DATABASE_URL=postgresql://dmlogn8n:password@localhost:5432/dmlogn8n_social
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CLUSTER_NODES=redis://localhost:7000,redis://localhost:7001,redis://localhost:7002

# Security
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# File Storage
UPLOAD_DIR=/var/www/dmlogn8n/uploads
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,pdf,txt

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@dmlogn8n.com

# Push Notifications
FCM_SERVER_KEY=your-fcm-server-key
APNS_KEY_ID=your-apns-key-id
APNS_TEAM_ID=your-apns-team-id

# WebSocket
WEBSOCKET_PORT=8001
WEBSOCKET_HEARTBEAT_INTERVAL=30

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Monitoring
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_PORT=9090

# External Services
DISCORD_WEBHOOK_URL=your-discord-webhook
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret
```

### Database Configuration
```python
# config/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

DATABASE_URL = os.getenv("DATABASE_URL")
POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "20"))
MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "30"))

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=os.getenv("DEBUG", "false").lower() == "true"
)
```

### Nginx Configuration
```nginx
# /etc/nginx/sites-available/social-hub.conf
upstream api_backend {
    least_conn;
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 max_fails=3 fail_timeout=30s;
}

upstream websocket_backend {
    ip_hash;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name social.dmlogn8n.com www.social.dmlogn8n.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name social.dmlogn8n.com www.social.dmlogn8n.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/social.dmlogn8n.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/social.dmlogn8n.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    # API Routes
    location /api/ {
        limit_req zone=api;
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket Routes
    location /ws/ {
        proxy_pass http://websocket_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket timeouts
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # Static Files
    location /static/ {
        alias /var/www/dmlogn8n/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/dmlogn8n/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # File Upload Size
    client_max_body_size 10M;

    # Logging
    access_log /var/log/nginx/social-hub-access.log;
    error_log /var/log/nginx/social-hub-error.log;
}
```

## Database Setup

### PostgreSQL Configuration
```bash
# /etc/postgresql/14/main/postgresql.conf
# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Connection settings
max_connections = 200
listen_addresses = '*'

# Performance settings
random_page_cost = 1.1
effective_io_concurrency = 200

# WAL settings
wal_level = replica
max_wal_size = 1GB
min_wal_size = 80MB
checkpoint_completion_target = 0.9
```

### Database Creation and Permissions
```sql
-- Create databases
CREATE DATABASE dmlogn8n_social;
CREATE DATABASE dmlogn8n_social_test;

-- Create users
CREATE USER dmlogn8n_app WITH PASSWORD 'secure_app_password';
CREATE USER dmlogn8n_readonly WITH PASSWORD 'secure_readonly_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE dmlogn8n_social TO dmlogn8n_app;
GRANT CONNECT ON DATABASE dmlogn8n_social TO dmlogn8n_readonly;
GRANT USAGE ON SCHEMA public TO dmlogn8n_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dmlogn8n_readonly;

-- Create indexes for performance
CREATE INDEX CONCURRENTLY idx_social_users_username ON social_users(username);
CREATE INDEX CONCURRENTLY idx_social_users_email ON social_users(email);
CREATE INDEX CONCURRENTLY idx_friendships_user1 ON friendships(user1_id);
CREATE INDEX CONCURRENTLY idx_friendships_user2 ON friendships(user2_id);
CREATE INDEX CONCURRENTLY idx_forum_posts_created ON forum_posts(created_at DESC);
CREATE INDEX CONCURRENTLY idx_notifications_recipient ON notifications(recipient_id, created_at DESC);
```

### Database Backups
```bash
#!/bin/bash
# scripts/backup_database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/postgresql"
DB_NAME="dmlogn8n_social"

# Create backup directory
mkdir -p $BACKUP_DIR

# Full backup
pg_dump -h localhost -U dmlogn8n_app -d $DB_NAME | gzip > $BACKUP_DIR/${DB_NAME}_full_$DATE.sql.gz

# Schema backup
pg_dump -h localhost -U dmlogn8n_app -d $DB_NAME --schema-only > $BACKUP_DIR/${DB_NAME}_schema_$DATE.sql

# Clean up old backups (keep 7 days)
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete

echo "Backup completed: $DATE"
```

## Redis Configuration

### Redis Setup for Clustering
```bash
# redis-cluster.conf
port 7000
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
appendonly yes
appendfilename "appendonly.aof"
dbfilename "dump.rdb"
```

### Redis Sentinel Configuration
```bash
# sentinel.conf
port 26379
sentinel monitor mymaster 127.0.0.1 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel failover-timeout mymaster 10000
sentinel parallel-syncs mymaster 1
```

## Docker Deployment

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: ./source_code
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://dmlogn8n:password@db:5432/dmlogn8n_social
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    restart: unless-stopped

  websocket:
    build:
      context: ./source_code
      dockerfile: backend/Dockerfile.websocket
    ports:
      - "8001:8001"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=dmlogn8n_social
      - POSTGRES_USER=dmlogn8n
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deployment/nginx:/etc/nginx/conf.d
      - ./ssl:/etc/ssl/certs
      - ./static:/var/www/static
    depends_on:
      - api
      - websocket
    restart: unless-stopped

  worker:
    build:
      context: ./source_code
      dockerfile: backend/Dockerfile
    command: celery -A app.celery worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://dmlogn8n:password@db:5432/dmlogn8n_social
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Dockerfile for API
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements_social.txt .
RUN pip install --no-cache-dir -r requirements_social.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Kubernetes Deployment

### Namespace and ConfigMaps
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: dmlogn8n-social
---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: social-hub-config
  namespace: dmlogn8n-social
data:
  APP_ENV: "production"
  REDIS_URL: "redis://redis-service:6379/0"
  DATABASE_URL: "postgresql://dmlogn8n:password@postgres-service:5432/dmlogn8n_social"
```

### Deployment
```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: social-hub-api
  namespace: dmlogn8n-social
spec:
  replicas: 3
  selector:
    matchLabels:
      app: social-hub-api
  template:
    metadata:
      labels:
        app: social-hub-api
    spec:
      containers:
      - name: api
        image: dmlogn8n/social-hub-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            configMapKeyRef:
              name: social-hub-config
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: social-hub-config
              key: REDIS_URL
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Service and Ingress
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: social-hub-api-service
  namespace: dmlogn8n-social
spec:
  selector:
    app: social-hub-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: social-hub-ingress
  namespace: dmlogn8n-social
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - social.dmlogn8n.com
    secretName: social-hub-tls
  rules:
  - host: social.dmlogn8n.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: social-hub-api-service
            port:
              number: 80
```

## Monitoring and Logging

### Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'social-hub-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
```

### Grafana Dashboards
```json
{
  "dashboard": {
    "title": "Social Hub Metrics",
    "panels": [
      {
        "title": "Active Users",
        "type": "stat",
        "targets": [
          {
            "expr": "social_hub_active_users_total"
          }
        ]
      },
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"
          }
        ]
      }
    ]
  }
}
```

### ELK Stack for Logging
```yaml
# logging/logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "social-hub-api" {
    json {
      source => "message"
    }

    date {
      match => [ "timestamp", "ISO8601" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "social-hub-%{+YYYY.MM.dd}"
  }
}
```

## Performance Optimization

### Database Optimization
```sql
-- Partitioning for large tables
CREATE TABLE forum_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- other columns
) PARTITION BY RANGE (created_at);

-- Create partitions
CREATE TABLE forum_posts_2024_01 PARTITION OF forum_posts
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Materialized views for complex queries
CREATE MATERIALIZED VIEW trending_posts AS
SELECT
    p.id,
    p.title,
    (p.likes_count + p.comments_count * 2) as trending_score,
    p.created_at
FROM forum_posts p
WHERE p.created_at >= NOW() - INTERVAL '7 days'
ORDER BY trending_score DESC;

-- Refresh schedule
CREATE OR REPLACE FUNCTION refresh_trending_posts()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY trending_posts;
END;
$$ LANGUAGE plpgsql;
```

### Caching Strategy
```python
# Cache configuration
CACHE_CONFIG = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {"max_connections": 50}
        }
    },
    "user_profiles": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
        "TIMEOUT": 3600  # 1 hour
    },
    "activity_feed": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/3",
        "TIMEOUT": 300   # 5 minutes
    }
}
```

## Security Hardening

### Security Headers
```python
# Middleware for security headers
class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Security headers
        response['X-Frame-Options'] = 'DENY'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

        return response
```

### Input Validation
```python
# Content filtering
import re
from profanity_check import predict, predict_prob

class ContentFilter:
    def __init__(self):
        self.profanity_threshold = 0.8
        self.spam_patterns = [
            r'buy\s+now',
            r'click\s+here',
            r'free\s+money',
            r'http[s]?://\S+',
        ]

    def filter_content(self, content: str) -> str:
        # Check for profanity
        profanity_score = predict_prob([content])[0]
        if profanity_score > self.profanity_threshold:
            raise ValueError("Content contains inappropriate language")

        # Check for spam patterns
        for pattern in self.spam_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                raise ValueError("Content appears to be spam")

        # Additional filtering logic here
        return content
```

## Backup and Recovery

### Automated Backup Script
```bash
#!/bin/bash
# scripts/backup.sh

set -e

BACKUP_DIR="/var/backups/dmlogn8n-social"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

echo "Starting backup process..."

# Database backup
echo "Backing up PostgreSQL database..."
pg_dump -h localhost -U dmlogn8n_app -d dmlogn8n_social | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

# Redis backup
echo "Backing up Redis data..."
redis-cli --rdb $BACKUP_DIR/redis_$DATE.rdb

# File storage backup
echo "Backing up user files..."
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /var/www/dmlogn8n/uploads/

# Configuration backup
echo "Backing up configuration..."
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /etc/dmlogn8n/

# Cleanup old backups
echo "Cleaning up old backups..."
find $BACKUP_DIR -name "*.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.rdb" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed successfully!"
echo "Backup location: $BACKUP_DIR"

# Verify backup integrity
for file in $BACKUP_DIR/*_$DATE.*; do
    if [ -f "$file" ]; then
        echo "Verifying $file..."
        if [[ $file == *.gz ]]; then
            gzip -t "$file" || echo "Warning: $file may be corrupted"
        fi
    fi
done
```

### Recovery Script
```bash
#!/bin/bash
# scripts/recover.sh

set -e

BACKUP_FILE=$1
RESTORE_DIR="/tmp/dmlogn8n-restore"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "Starting recovery process..."

# Create restore directory
mkdir -p $RESTORE_DIR

# Extract backup
echo "Extracting backup..."
case $BACKUP_FILE in
    *.sql.gz)
        gunzip -c $BACKUP_FILE > $RESTORE_DIR/database.sql
        ;;
    *.rdb)
        cp $BACKUP_FILE $RESTORE_DIR/redis.rdb
        ;;
    *.tar.gz)
        tar -xzf $BACKUP_FILE -C $RESTORE_DIR
        ;;
esac

# Stop services
echo "Stopping services..."
sudo systemctl stop dmlogn8n-api
sudo systemctl stop redis
sudo systemctl stop nginx

# Restore database
if [ -f "$RESTORE_DIR/database.sql" ]; then
    echo "Restoring database..."
    sudo -u postgres psql -d dmlogn8n_social < $RESTORE_DIR/database.sql
fi

# Restore Redis
if [ -f "$RESTORE_DIR/redis.rdb" ]; then
    echo "Restoring Redis..."
    sudo systemctl stop redis
    sudo cp $RESTORE_DIR/redis.rdb /var/lib/redis/dump.rdb
    sudo chown redis:redis /var/lib/redis/dump.rdb
    sudo systemctl start redis
fi

# Restore files
if [ -d "$RESTORE_DIR/uploads" ]; then
    echo "Restoring user files..."
    sudo cp -r $RESTORE_DIR/uploads/* /var/www/dmlogn8n/uploads/
    sudo chown -R www-data:www-data /var/www/dmlogn8n/uploads/
fi

# Start services
echo "Starting services..."
sudo systemctl start dmlogn8n-api
sudo systemctl start nginx

# Verify services
echo "Verifying services..."
sudo systemctl status dmlogn8n-api
sudo systemctl status redis
sudo systemctl status nginx

# Cleanup
rm -rf $RESTORE_DIR

echo "Recovery completed successfully!"
```

## Scaling Strategies

### Horizontal Scaling
```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  api:
    image: dmlogn8n/social-hub-api:latest
    deploy:
      replicas: 5
      update_config:
        parallelism: 2
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### Auto-scaling Policy
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: social-hub-api-hpa
  namespace: dmlogn8n-social
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: social-hub-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Maintenance Procedures

### Daily Maintenance
```bash
#!/bin/bash
# scripts/daily_maintenance.sh

echo "Running daily maintenance tasks..."

# Database maintenance
echo "Running VACUUM and ANALYZE..."
sudo -u postgres psql -d dmlogn8n_social -c "VACUUM ANALYZE;"

# Update statistics
echo "Updating table statistics..."
sudo -u postgres psql -d dmlogn8n_social -c "ANALYZE;"

# Clean up old sessions
echo "Cleaning up old sessions..."
python scripts/cleanup_sessions.py

# Regenerate materialized views
echo "Regenerating materialized views..."
python scripts/refresh_materialized_views.py

# Check disk space
echo "Checking disk space..."
df -h

# Check service health
echo "Checking service health..."
curl -f http://localhost:8000/health || echo "API service is down!"
curl -f http://localhost:8001/health || echo "WebSocket service is down!"

echo "Daily maintenance completed."
```

### Weekly Maintenance
```bash
#!/bin/bash
# scripts/weekly_maintenance.sh

echo "Running weekly maintenance tasks..."

# Full database backup
echo "Running full database backup..."
./scripts/backup.sh

# Update system packages
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Check SSL certificates
echo "Checking SSL certificates..."
sudo certbot certificates
sudo certbot renew --dry-run

# Analyze query performance
echo "Analyzing slow queries..."
sudo -u postgres psql -d dmlogn8n_social -c "
SELECT query, mean_time, calls
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC
LIMIT 10;"

# Optimize database
echo "Optimizing database..."
sudo -u postgres psql -d dmlogn8n_social -c "REINDEX DATABASE dmlogn8n_social;"

echo "Weekly maintenance completed."
```

## Troubleshooting

### Common Issues and Solutions

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U dmlogn8n_app -d dmlogn8n_social -c "SELECT 1;"

# Check connection pool
netstat -an | grep 5432

# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

#### Redis Connection Issues
```bash
# Check Redis status
sudo systemctl status redis

# Test Redis connection
redis-cli ping

# Check Redis memory usage
redis-cli info memory

# View Redis logs
sudo tail -f /var/log/redis/redis-server.log
```

#### High CPU Usage
```bash
# Check CPU usage
top
htop

# Check process list
ps aux | grep python

# Profile application
python -m cProfile -o profile.stats scripts/profile_app.py
```

#### Memory Issues
```bash
# Check memory usage
free -h
top

# Check for memory leaks
valgrind --tool=memcheck python app.py

# Monitor PostgreSQL memory
sudo -u postgres psql -d dmlogn8n_social -c "
SELECT datname, numbackends, pg_size_pretty(pg_database_size(datname))
FROM pg_database;"
```

#### WebSocket Issues
```bash
# Check WebSocket service
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: test" \
     -H "Sec-WebSocket-Version: 13" \
     http://localhost:8001/ws/social/test_user

# Monitor WebSocket connections
netstat -an | grep :8001

# Check WebSocket logs
tail -f /var/log/dmlogn8n/websocket.log
```

## Testing and Validation

### Load Testing
```python
# tests/load_test.py
import asyncio
import aiohttp
import time

async def load_test():
    concurrent_users = 100
    requests_per_user = 10

    async with aiohttp.ClientSession() as session:
        tasks = []

        for user_id in range(concurrent_users):
            for _ in range(requests_per_user):
                task = session.get(f"http://localhost:8000/api/social/profile/me")
                tasks.append(task)

        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        end_time = time.time()

        successful = sum(1 for r in responses if r.status == 200)
        total_time = end_time - start_time

        print(f"Load Test Results:")
        print(f"  Total requests: {len(tasks)}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {len(tasks) - successful}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Requests/sec: {len(tasks) / total_time:.2f}")

if __name__ == "__main__":
    asyncio.run(load_test())
```

### Health Checks
```python
# tests/health_check.py
import requests
import sys

def health_check():
    services = {
        "API": "http://localhost:8000/health",
        "WebSocket": "http://localhost:8001/health",
        "Database": "http://localhost:8000/health/db",
        "Redis": "http://localhost:8000/health/redis"
    }

    all_healthy = True

    for service, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service}: Healthy")
            else:
                print(f"❌ {service}: Unhealthy (HTTP {response.status_code})")
                all_healthy = False
        except requests.RequestException as e:
            print(f"❌ {service}: Error - {e}")
            all_healthy = False

    return all_healthy

if __name__ == "__main__":
    if health_check():
        print("\nAll services are healthy! ✅")
        sys.exit(0)
    else:
        print("\nSome services are unhealthy! ❌")
        sys.exit(1)
```

This comprehensive deployment guide provides everything needed to deploy, configure, and maintain the DMlogn8n Social Hub platform in production. The platform is designed for scalability, security, and high availability, with extensive monitoring and maintenance procedures to ensure reliable operation.