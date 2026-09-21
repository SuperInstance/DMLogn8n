# DM World Builder Portal - Deployment Guide

## Overview
This guide covers deployment of the DM World Builder Portal, which consists of a Node.js backend server with WebSocket support and a React frontend.

## Prerequisites

### System Requirements
- Node.js 18.x or higher
- MongoDB 5.x or higher
- Redis (optional, for session storage)
- PM2 (for process management in production)

### Environment Variables
Copy the example environment file and configure your settings:

```bash
# Server
cp server/.env.example server/.env
```

Required variables:
```
NODE_ENV=production
PORT=5001
MONGODB_URI=mongodb://localhost:27017/dm-world-builder
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
CLIENT_URL=https://your-domain.com
OPENAI_API_KEY=your-openai-api-key-here
```

## Installation

### 1. Clone and Install Dependencies
```bash
git clone <repository-url>
cd dm-world-builder
npm run install-all
```

### 2. Database Setup
Ensure MongoDB is running and accessible:
```bash
# Start MongoDB (systemd)
sudo systemctl start mongod
sudo systemctl enable mongod

# Or using Docker
docker run -d -p 27017:27017 --name mongodb mongo:5.0
```

### 3. Build Frontend
```bash
cd client
npm run build
```

## Deployment Options

### Option 1: Traditional Server Deployment

#### Using PM2
```bash
# Install PM2 globally
npm install -g pm2

# Start the application
pm2 start server/index.js --name "dm-world-builder"

# Save PM2 configuration
pm2 save
pm2 startup
```

#### PM2 Configuration File
Create `ecosystem.config.js`:
```javascript
module.exports = {
  apps: [{
    name: 'dm-world-builder',
    script: 'server/index.js',
    instances: 'max',
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'production',
      PORT: 5001
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true
  }]
};
```

Start with:
```bash
pm2 start ecosystem.config.js
```

### Option 2: Docker Deployment

#### Dockerfile
```dockerfile
# Multi-stage build
FROM node:18-alpine AS builder

# Build backend
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Build frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/client
COPY client/package*.json ./
RUN npm ci
COPY client/ ./
RUN npm run build

# Production image
FROM node:18-alpine
WORKDIR /app

# Copy built backend
COPY --from=builder /app/node_modules ./node_modules
COPY server/ ./server/
COPY package*.json ./

# Copy built frontend
COPY --from=frontend-builder /app/client/build ./client/build

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001
USER nodejs

EXPOSE 5001

CMD ["node", "server/index.js"]
```

#### Docker Compose
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5001:5001"
    environment:
      - NODE_ENV=production
      - MONGODB_URI=mongodb://mongo:27017/dm-world-builder
    depends_on:
      - mongo
    restart: unless-stopped

  mongo:
    image: mongo:5.0
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  mongo_data:
```

Deploy with:
```bash
docker-compose up -d
```

### Option 3: Cloud Platform Deployment

#### Heroku
```bash
# Install Heroku CLI
# Login and create app
heroku login
heroku create your-app-name

# Set environment variables
heroku config:set NODE_ENV=production
heroku config:set MONGODB_URI=your-mongodb-url
heroku config:set JWT_SECRET=your-jwt-secret
heroku config:set OPENAI_API_KEY=your-openai-key

# Deploy
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

#### AWS (using Elastic Beanstalk)
1. Create AWS account and EB CLI setup
2. Initialize EB application:
```bash
eb init dm-world-builder
eb create production
```

#### Vercel (Frontend only)
```bash
# Deploy frontend to Vercel
cd client
npm install -g vercel
vercel --prod
```

## Nginx Configuration

For reverse proxy setup:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL configuration
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Frontend static files
    location / {
        root /path/to/client/build;
        try_files $uri $uri/ /index.html;
    }

    # API and WebSocket proxy
    location /api {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Socket.IO WebSocket
    location /socket.io/ {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## SSL/TLS Setup

### Let's Encrypt with Certbot
```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring and Logging

### Application Monitoring
```bash
# PM2 monitoring
pm2 monit

# View logs
pm2 logs dm-world-builder

# System monitoring
htop
iostat -x 1
```

### Log Management
Configure log rotation in `/etc/logrotate.d/dm-world-builder`:
```
/path/to/dm-world-builder/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 nodejs nodejs
    postrotate
        pm2 reloadLogs
    endscript
}
```

## Security Considerations

### 1. Environment Security
- Use strong, unique secrets
- Enable rate limiting (configured in the app)
- Set up firewall rules
- Regular security updates

### 2. Database Security
```javascript
// MongoDB security
- Enable authentication
- Use SSL/TLS connections
- Restrict network access
- Regular backups
```

### 3. Application Security
- Validate all inputs (Joi schemas included)
- Sanitize user data
- Implement CORS properly
- Use HTTPS only in production
- Set security headers

## Backup Strategy

### Database Backup
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mongodump --uri="mongodb://localhost:27017/dm-world-builder" --out="/backups/mongo_$DATE"
tar -czf "/backups/mongo_$DATE.tar.gz" "/backups/mongo_$DATE"
rm -rf "/backups/mongo_$DATE"
```

### File Backup
```bash
# Backup application files
rsync -av /path/to/dm-world-builder/ /backups/app_$(date +%Y%m%d)/
```

## Performance Optimization

### 1. Database Optimization
- Create indexes for frequent queries
- Use connection pooling
- Enable query caching
- Monitor slow queries

### 2. Application Optimization
- Enable gzip compression
- Use CDN for static assets
- Implement caching strategies
- Optimize WebSocket connections

### 3. Server Optimization
```bash
# System limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Kernel optimization
echo "net.core.somaxconn = 65536" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65536" >> /etc/sysctl.conf
sysctl -p
```

## Troubleshooting

### Common Issues

#### 1. WebSocket Connection Issues
- Check firewall settings
- Verify Nginx configuration
- Ensure proper SSL certificate setup
- Monitor connection limits

#### 2. Database Connection Errors
- Verify MongoDB is running
- Check connection string
- Review authentication settings
- Monitor connection pool

#### 3. High Memory Usage
- Monitor memory leaks
- Optimize garbage collection
- Check for memory-intensive operations
- Consider increasing server resources

### Debug Mode
```bash
# Run with debug logging
DEBUG=dm-world-builder:* npm start

# Check PM2 logs
pm2 logs --lines 100

# Monitor system resources
htop
iotop
```

## Maintenance

### Regular Tasks
1. **Weekly**: Review logs, check for errors
2. **Monthly**: Update dependencies, check security advisories
3. **Quarterly**: Performance review, backup verification
4. **Annually**: Security audit, infrastructure review

### Update Process
```bash
# Backup current version
pm2 stop dm-world-builder
cp -r /path/to/dm-world-builder /backups/backup_$(date +%Y%m%d)

# Update dependencies
npm update
cd client && npm update

# Restart application
pm2 start dm-world-builder
```

## Scaling Considerations

### Horizontal Scaling
- Use load balancer for multiple instances
- Implement session sharing (Redis)
- Database clustering
- Microservices architecture

### Vertical Scaling
- Increase server resources
- Optimize database performance
- Implement caching layers
- Monitor resource usage

This deployment guide provides comprehensive instructions for deploying the DM World Builder Portal in various environments. Choose the deployment option that best fits your infrastructure and requirements.