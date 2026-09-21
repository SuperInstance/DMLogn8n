# Installation and Setup Guide

This guide will walk you through installing and configuring the Advanced Crafting System for DMlogn8n.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [n8n Integration](#n8n-integration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **Node.js**: 16.0 or higher
- **npm**: 8.0 or higher
- **Memory**: 2GB RAM
- **Storage**: 500MB free space
- **Database**: MongoDB 4.4+ or PostgreSQL 12+

### Recommended Requirements
- **Node.js**: 18.0 or higher
- **Memory**: 4GB RAM
- **Storage**: 2GB free space
- **Database**: MongoDB 5.0+ with replica set
- **Redis**: 6.0+ for caching

### Optional Dependencies
- **n8n**: 0.200+ for workflow automation
- **Docker**: 20.10+ for containerized deployment
- **PM2**: Process manager for production

## Installation

### Step 1: Clone the Repository

```bash
# Clone the main repository
git clone https://github.com/your-org/DMlogn8n.git
cd DMlogn8n

# Navigate to the crafting system
cd advanced-crafting
```

### Step 2: Install Dependencies

```bash
# Install npm dependencies
npm install

# Install development dependencies
npm install --dev

# Verify installation
npm list
```

### Step 3: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

### Step 4: Database Setup

#### MongoDB (Recommended)

```bash
# Install MongoDB
# Ubuntu/Debian
sudo apt-get install -y mongodb

# macOS with Homebrew
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB
sudo systemctl start mongod
# or
brew services start mongodb/brew/mongodb-community
```

#### PostgreSQL

```bash
# Install PostgreSQL
# Ubuntu/Debian
sudo apt-get install -y postgresql postgresql-contrib

# macOS with Homebrew
brew install postgresql

# Start PostgreSQL
sudo systemctl start postgresql
# or
brew services start postgresql
```

### Step 5: Initialize Database

```bash
# Run database initialization script
npm run db:init

# Create initial collections and indexes
npm run db:migrate

# Load sample data (optional)
npm run db:seed
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Server Configuration
NODE_ENV=development
PORT=3000
HOST=localhost

# Database Configuration
DATABASE_URL=mongodb://localhost:27017/dmlogn8n_crafting
# or for PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost:5432/dmlogn8n_crafting

# Redis Configuration (for caching)
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key
JWT_EXPIRES_IN=7d

# n8n Integration
N8N_API_KEY=your-n8n-api-key
N8N_WEBHOOK_URL=http://localhost:5678/webhook

# External Services
NOTIFICATION_SERVICE_URL=https://your-notification-service.com
INVENTORY_SERVICE_URL=https://your-inventory-service.com

# File Storage
UPLOAD_PATH=./uploads
MAX_FILE_SIZE=10485760

# Security
CORS_ORIGIN=http://localhost:3000
RATE_LIMIT_WINDOW=60000
RATE_LIMIT_MAX=100

# Logging
LOG_LEVEL=info
LOG_FILE=./logs/crafting.log

# Email Configuration (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

### Application Configuration

Edit `config/crafting-config.js` to customize system behavior:

```javascript
module.exports = {
    // System settings
    system: {
        maxSkillLevel: 1000,
        baseExperienceMultiplier: 1.0,
        qualityDecayEnabled: true,
        socialFeaturesEnabled: true
    },

    // Database configuration
    database: {
        type: 'mongodb', // 'mongodb' or 'postgresql'
        url: process.env.DATABASE_URL,
        options: {
            useNewUrlParser: true,
            useUnifiedTopology: true,
            maxPoolSize: 20
        }
    },

    // n8n integration
    integration: {
        n8n: {
            enabled: true,
            webhookUrl: process.env.N8N_WEBHOOK_URL,
            apiKey: process.env.N8N_API_KEY
        }
    }
};
```

## Database Setup

### MongoDB Setup

#### Create Database and User

```javascript
// Connect to MongoDB
mongo

// Create database and user
use dmlogn8n_crafting
db.createUser({
    user: "crafting_user",
    pwd: "secure_password",
    roles: [
        { role: "readWrite", db: "dmlogn8n_crafting" }
    ]
})
```

#### Create Indexes

```javascript
// Connect to crafting database
use dmlogn8n_crafting

// Create indexes for performance
db.crafters.createIndex({ "id": 1 }, { unique: true })
db.recipes.createIndex({ "profession": 1, "requiredSkill": 1 })
db.materials.createIndex({ "type": 1, "quality": -1 })
db.orders.createIndex({ "status": 1, "createdAt": -1 })
db.competitions.createIndex({ "status": 1, "timeline.startDate": 1 })
```

### PostgreSQL Setup

#### Create Database and User

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE dmlogn8n_crafting;

-- Create user
CREATE USER crafting_user WITH PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE dmlogn8n_crafting TO crafting_user;

-- Connect to the database
\c dmlogn8n_crafting

-- Create schema
CREATE SCHEMA IF NOT EXISTS crafting;
```

#### Create Tables

```sql
-- Crafters table
CREATE TABLE crafters (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    skills JSONB,
    stats JSONB,
    resources JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recipes table
CREATE TABLE recipes (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    profession VARCHAR(100) NOT NULL,
    tier VARCHAR(50) NOT NULL,
    required_skill INTEGER NOT NULL,
    materials JSONB,
    base_properties JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Materials table
CREATE TABLE materials (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    quality INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    properties JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_crafters_skills ON crafters USING GIN (skills);
CREATE INDEX idx_recipes_profession ON recipes (profession, required_skill);
CREATE INDEX idx_materials_type ON materials (type, quality DESC);
```

## n8n Integration

### Install n8n

```bash
# Install n8n globally
npm install n8n -g

# Or run with Docker
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

### Import Workflows

1. Start n8n: `n8n start`
2. Open browser: `http://localhost:5678`
3. Import workflows from `workflows/n8n/` directory:
   - Click "Import from file"
   - Select `crafting-automation.json`
   - Configure webhook URLs and credentials

### Configure Webhooks

```javascript
// In your n8n workflow settings
const webhookConfig = {
    path: '/crafting-webhook',
    method: 'POST',
    responseMode: 'onReceived',
    options: {
        rawBody: true
    }
};

// Configure authentication
const authConfig = {
    type: 'httpHeaderAuth',
    name: 'API Key',
    properties: {
        name: 'X-API-Key',
        value: process.env.N8N_API_KEY
    }
};
```

### Test Integration

```bash
# Test webhook connection
curl -X POST http://localhost:5678/webhook/crafting-webhook \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-n8n-api-key" \
  -d '{
    "crafterId": "test_crafter",
    "recipeId": "dagger_basic",
    "materials": [{"id": "iron_ingot", "quantity": 2}]
  }'
```

## Testing

### Run Test Suite

```bash
# Run all tests
npm test

# Run specific test categories
npm run test:crafting
npm run test:materials
npm run test:social
npm run test:integration

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Manual Testing

```bash
# Start development server
npm run dev

# Test API endpoints
curl http://localhost:3000/api/health

# Test crafting
curl -X POST http://localhost:3000/api/craft \
  -H "Content-Type: application/json" \
  -d '{
    "crafterId": "test_crafter",
    "recipeId": "dagger_basic",
    "materials": [{"id": "iron_ingot", "quantity": 2}]
  }'
```

### Load Testing

```bash
# Install load testing tool
npm install -g artillery

# Run load test
artillery run load-test.yml

# Example load-test.yml
config:
  target: 'http://localhost:3000'
  phases:
    - duration: 60
      arrivalRate: 10

scenarios:
  - name: "Test crafting API"
    requests:
      - post:
          url: "/api/craft"
          json:
            crafterId: "test_crafter"
            recipeId: "dagger_basic"
            materials: [{"id": "iron_ingot", "quantity": 2}]
```

## Production Deployment

### Using PM2

```bash
# Install PM2
npm install -g pm2

# Create ecosystem file
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'crafting-system',
    script: './index.js',
    instances: 'max',
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'production',
      PORT: 3000
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true
  }]
};
EOF

# Start application
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 startup script
pm2 startup
```

### Using Docker

```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

```bash
# Build and run with Docker
docker build -t crafting-system .
docker run -p 3000:3000 --env-file .env crafting-system
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  crafting-system:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=mongodb://mongo:27017/dmlogn8n_crafting
      - REDIS_URL=redis://redis:6379
    depends_on:
      - mongo
      - redis

  mongo:
    image: mongo:5.0
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=password
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  mongo_data:
  n8n_data:
```

```bash
# Deploy with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f crafting-system
```

## Monitoring and Logging

### Application Monitoring

```javascript
// monitoring.js
const prometheus = require('prom-client');

// Create metrics
const craftingRequests = new prometheus.Counter({
    name: 'crafting_requests_total',
    help: 'Total number of crafting requests'
});

const craftingDuration = new prometheus.Histogram({
    name: 'crafting_duration_seconds',
    help: 'Time spent crafting items'
});

const materialHarvests = new prometheus.Counter({
    name: 'material_harvests_total',
    help: 'Total number of material harvests'
});

// Expose metrics endpoint
app.get('/metrics', async (req, res) => {
    res.set('Content-Type', prometheus.register.contentType);
    res.end(await prometheus.register.metrics());
});
```

### Log Management

```javascript
// logger.js
const winston = require('winston');

const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
    ),
    defaultMeta: { service: 'crafting-system' },
    transports: [
        new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
        new winston.transports.File({ filename: 'logs/combined.log' })
    ]
});

if (process.env.NODE_ENV !== 'production') {
    logger.add(new winston.transports.Console({
        format: winston.format.simple()
    }));
}

module.exports = logger;
```

## Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Check MongoDB connection
mongo --eval "db.adminCommand('ismaster')"

# Check PostgreSQL connection
psql -U postgres -h localhost -c "SELECT version();"

# Reset database
npm run db:reset
```

#### Port Conflicts

```bash
# Find process using port 3000
lsof -i :3000

# Kill process
kill -9 <PID>

# Use different port
PORT=3001 npm start
```

#### Memory Issues

```bash
# Increase Node.js memory limit
node --max-old-space-size=4096 index.js

# Monitor memory usage
node --inspect index.js
```

#### Permission Issues

```bash
# Fix file permissions
chmod +x scripts/*.sh

# Fix npm permissions
sudo chown -R $(whoami) ~/.npm
```

### Debug Mode

```bash
# Enable debug logging
DEBUG=crafting:* npm start

# Run with Node.js inspector
node --inspect index.js

# Use Chrome DevTools for debugging
chrome://inspect
```

### Health Checks

```javascript
// health-check.js
const healthCheck = async () => {
    const checks = {
        database: await checkDatabase(),
        redis: await checkRedis(),
        n8n: await checkN8n(),
        filesystem: await checkFilesystem()
    };

    const healthy = Object.values(checks).every(check => check.status === 'ok');

    return {
        status: healthy ? 'healthy' : 'unhealthy',
        timestamp: new Date().toISOString(),
        checks
    };
};
```

### Performance Optimization

```bash
# Enable production mode
export NODE_ENV=production

# Use cluster mode
pm2 start index.js -i max

# Optimize database queries
npm run db:optimize

# Clear cache
npm run cache:clear
```

## Support Resources

- **Documentation**: https://docs.dmlogn8n.com
- **GitHub Issues**: https://github.com/your-org/DMlogn8n/issues
- **Discord Community**: https://discord.gg/dmlogn8n
- **Email Support**: support@dmlogn8n.com

## Next Steps

After installation:

1. [Read the API documentation](./API.md)
2. [Check the examples directory](../examples/)
3. [Join our community](https://discord.gg/dmlogn8n)
4. [Contribute to the project](../CONTRIBUTING.md)