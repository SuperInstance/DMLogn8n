# Deployment Guide

## Table of Contents
1. [Environment Setup](#environment-setup)
2. [Database Configuration](#database-configuration)
3. [Application Configuration](#application-configuration)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Environment Variables](#environment-variables)
7. [Monitoring & Logging](#monitoring--logging)
8. [Security Considerations](#security-considerations)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)

## Environment Setup

### Prerequisites
- Node.js 18.0.0 or higher
- MongoDB 4.4 or higher
- Redis 6.0 or higher (for caching)
- OpenAI API key (for AI generation)
- n8n instance (for workflow automation)

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB SSD
- Network: 100 Mbps

**Recommended:**
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 50GB+ SSD
- Network: 1 Gbps

## Database Configuration

### MongoDB Setup

**Production MongoDB Atlas:**
```bash
# Create cluster via MongoDB Atlas console
# Set up network access
# Create database user
# Get connection string
```

**Self-hosted MongoDB:**
```bash
# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Create database and user
mongo
> use dmlogn8n-quests
> db.createUser({
    user: "questuser",
    pwd: "secure_password",
    roles: [
        { role: "readWrite", db: "dmlogn8n-quests" }
    ]
})
```

### Redis Setup (Optional)
```bash
# Install Redis
sudo apt-get install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
# Set password and other security settings

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

## Application Configuration

### Production Environment File
Create `.env.production`:
```env
# Server Configuration
NODE_ENV=production
PORT=3001

# Database
MONGODB_URI=mongodb://questuser:secure_password@mongodb-server:27017/dmlogn8n-quests?authSource=admin
REDIS_URL=redis://redis-server:6379

# AI Configuration
OPENAI_API_KEY=your_production_openai_key
OPENAI_MODEL=gpt-4
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=4000

# Security
JWT_SECRET=your_very_secure_jwt_secret_at_least_32_characters
CORS_ORIGIN=https://your-domain.com
BCRYPT_ROUNDS=12

# External Services
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook
N8N_API_KEY=your_n8n_api_key

# Logging
LOG_LEVEL=info
LOG_FILE=/var/log/quest-generator/app.log

# Performance
MAX_CONCURRENT_QUESTS=100
QUEST_CACHE_TTL=300
PLAYER_CACHE_TTL=600

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30000
```

## Docker Deployment

### Dockerfile
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001

# Build application
RUN npm run build

# Production stage
FROM node:18-alpine AS production

WORKDIR /app

# Install production dependencies
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Copy built application
COPY --from=builder /app/src ./src
COPY --from=builder /app/config ./config
COPY --from=builder /app/node_modules ./node_modules

# Create logs directory
RUN mkdir -p /var/log/quest-generator

# Change ownership
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001
RUN chown -R nodejs:nodejs /app /var/log/quest-generator

USER nodejs

EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3001/health', (res) => { process.exit(res.statusCode === 200 ? 0 : 1) })"

CMD ["node", "src/index.js"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=production
      - MONGODB_URI=mongodb://mongo:27017/dmlogn8n-quests
      - REDIS_URL=redis://redis:6379
    depends_on:
      - mongo
      - redis
    volumes:
      - ./logs:/var/log/quest-generator
      - ./.env.production:/app/.env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  mongo:
    image: mongo:6.0
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=secure_mongo_password
      - MONGO_INITDB_DATABASE=dmlogn8n-quests
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf:ro
    command: redis-server /usr/local/etc/redis/redis.conf
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped

volumes:
  mongo_data:
  redis_data:
```

### Deployment Commands
```bash
# Build and start services
docker-compose up -d --build

# View logs
docker-compose logs -f app

# Scale application
docker-compose up -d --scale app=3

# Update deployment
docker-compose pull
docker-compose up -d
```

## Cloud Deployment

### AWS Deployment

**EC2 Instance Setup:**
```bash
# Launch EC2 instance (Ubuntu 22.04 LTS)
# Security groups: allow 80, 443, 3001

# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
git clone <your-repo-url>
cd dynamic-quest-generator

# Configure environment
cp .env.example .env.production
nano .env.production

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

**AWS ECS Deployment:**
```json
{
  "family": "quest-generator",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "quest-generator",
      "image": "your-ecr-repo/quest-generator:latest",
      "portMappings": [
        {
          "containerPort": 3001,
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
          "name": "MONGODB_URI",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:quest-generator/mongodb"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/quest-generator",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Platform

**Cloud Run Deployment:**
```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT-ID/quest-generator

# Deploy to Cloud Run
gcloud run deploy quest-generator \
  --image gcr.io/PROJECT-ID/quest-generator \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars NODE_ENV=production \
  --set-secrets MONGODB_URI=quest-generator-mongodb:latest
```

### Azure Container Instances

```bash
# Create resource group
az group create --name quest-generator-rg --location eastus

# Deploy container
az container create \
  --resource-group quest-generator-rg \
  --name quest-generator \
  --image your-registry/quest-generator:latest \
  --cpu 1 \
  --memory 2 \
  --ports 3001 \
  --environment-variables NODE_ENV=production \
  --secure-environment-variables MONGODB_URI=$MONGODB_URI
```

## Environment Variables

### Required Variables
```env
# Database
MONGODB_URI=mongodb://localhost:27017/dmlogn8n-quests

# AI
OPENAI_API_KEY=your_openai_api_key

# Security
JWT_SECRET=your_jwt_secret_here
CORS_ORIGIN=http://localhost:3000
```

### Optional Variables
```env
# Server
PORT=3001
NODE_ENV=development

# Caching
REDIS_URL=redis://localhost:6379

# AI Configuration
OPENAI_MODEL=gpt-4-turbo-preview
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=4000

# n8n Integration
N8N_WEBHOOK_URL=http://localhost:5678/webhook
N8N_API_KEY=your_n8n_api_key

# Features
ENABLE_SOCIAL_FEATURES=true
ENABLE_ACHIEVEMENTS=true
ENABLE_GUILD_SYSTEM=true
ENABLE_DYNAMIC_DIFFICULTY=true

# Quest Generation
MAX_QUESTS_PER_PLAYER=50
QUEST_COOLDOWN_HOURS=1
DIFFICULTY_SCALING=true
PERSONALIZATION_ENABLED=true

# Logging
LOG_LEVEL=info
LOG_FILE=logs/quest-generator.log
```

## Monitoring & Logging

### Application Logging
```javascript
// Use Winston for structured logging
import winston from 'winston'

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'quest-generator' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
})
```

### Prometheus Metrics
```javascript
import client from 'prom-client'

// Create metrics
const httpRequestDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code']
})

const questGenerationCounter = new client.Counter({
  name: 'quests_generated_total',
  help: 'Total number of quests generated',
  labelNames: ['type', 'method']
})

// Expose metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', client.register.contentType)
  res.end(await client.register.metrics())
})
```

### Health Checks
```javascript
app.get('/health', async (req, res) => {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    checks: {}
  }

  try {
    // Database health
    await mongoose.connection.db.admin().ping()
    health.checks.database = { status: 'healthy' }
  } catch (error) {
    health.checks.database = { status: 'unhealthy', error: error.message }
    health.status = 'unhealthy'
  }

  // Redis health (if configured)
  if (redisClient) {
    try {
      await redisClient.ping()
      health.checks.redis = { status: 'healthy' }
    } catch (error) {
      health.checks.redis = { status: 'unhealthy', error: error.message }
    }
  }

  const statusCode = health.status === 'healthy' ? 200 : 503
  res.status(statusCode).json(health)
})
```

## Security Considerations

### Environment Security
```bash
# Secure environment files
chmod 600 .env.production
chown app:app .env.production

# Use secrets management
# AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault
```

### API Security
```javascript
// Rate limiting
import rateLimit from 'express-rate-limit'

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP'
})

app.use('/api/', limiter)

// Input validation
import { body, validationResult } from 'express-validator'

app.post('/api/quests/generate', [
  body('playerId').notEmpty().isMongoId(),
  body('questType').optional().isIn(QUEST_TYPES)
], (req, res) => {
  const errors = validationResult(req)
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() })
  }
  // Process request
})
```

### Database Security
```javascript
// Use connection pooling and SSL
const mongoOptions = {
  maxPoolSize: 10,
  serverSelectionTimeoutMS: 5000,
  socketTimeoutMS: 45000,
  ssl: process.env.NODE_ENV === 'production',
  sslValidate: true,
  sslCA: fs.readFileSync('/path/to/ca.pem')
}

await mongoose.connect(uri, mongoOptions)
```

## Performance Optimization

### Database Optimization
```javascript
// Create indexes
db.quests.createIndex({ "assignedTo": 1, "state": 1 })
db.quests.createIndex({ "type": 1, "difficulty": 1 })
db.quests.createIndex({ "tags": 1 })
db.players.createIndex({ "userId": 1 }, { unique: true })
db.players.createIndex({ "stats.level": 1 })

// Use aggregation for complex queries
const pipeline = [
  { $match: { assignedTo: playerId, state: "in_progress" } },
  { $lookup: { from: "players", localField: "assignedTo", foreignField: "_id", as: "player" } },
  { $project: { title: 1, difficulty: 1, "player.username": 1 } }
]
const quests = await Quest.aggregate(pipeline)
```

### Caching Strategy
```javascript
import Redis from 'redis'

const redis = Redis.createClient(process.env.REDIS_URL)

// Cache quest data
const cacheQuest = async (questId, questData, ttl = 300) => {
  await redis.setex(`quest:${questId}`, ttl, JSON.stringify(questData))
}

const getCachedQuest = async (questId) => {
  const cached = await redis.get(`quest:${questId}`)
  return cached ? JSON.parse(cached) : null
}
```

### Connection Pooling
```javascript
// HTTP/2 for better performance
import spdy from 'spdy'

const options = {
  key: fs.readFileSync('./server.key'),
  cert: fs.readFileSync('./server.crt')
}

spdy.createServer(options, app).listen(443)
```

## Troubleshooting

### Common Issues

**Database Connection Issues:**
```bash
# Check MongoDB connection
mongo mongodb://username:password@host:port/database

# Check logs
tail -f /var/log/mongodb/mongod.log

# Test from application
node -e "require('./src/database').initialize()"
```

**Memory Issues:**
```bash
# Monitor memory usage
docker stats
top -p $(pgrep node)

# Check for memory leaks
node --inspect src/index.js
# Use Chrome DevTools Memory tab
```

**Performance Issues:**
```bash
# Profile application
node --prof src/index.js
node --prof-process isolate-*.log > processed.txt

# Monitor queries
db.setProfilingLevel(2)
db.system.profile.find().sort({ ts: -1 }).limit(5)
```

### Log Analysis
```bash
# Error logs
tail -f logs/error.log | grep ERROR

# Access logs
tail -f logs/access.log | awk '{print $1, $7, $9}'

# Quest generation logs
grep "quest generated" logs/combined.log | wc -l
```

### Health Monitoring
```bash
# Check application health
curl -f http://localhost:3001/health

# Monitor system resources
htop
iotop
nethogs
```

### Backup and Recovery
```bash
# Database backup
mongodump --uri="$MONGODB_URI" --out=/backup/$(date +%Y%m%d)

# Restore backup
mongorestore --uri="$MONGODB_URI" /backup/20240120

# Application backup
tar -czf backup-$(date +%Y%m%d).tar.gz .
```

### Scaling Issues
```bash
# Check connection limits
db.serverStatus().connections

# Monitor slow queries
db.setProfilingLevel(1, { slowms: 100 })
db.system.profile.find().millis > 100

# Scale horizontally
docker-compose up -d --scale app=3
```

For additional support, check the application logs and create an issue in the GitHub repository.