# DMlogn8n Cross-Platform Sync System

A comprehensive, real-time synchronization system for DMlogn8n that provides universal save game synchronization across all platforms (web, mobile, desktop, VR).

## 🌟 Features

### Universal Save System
- **Multi-Platform Support**: Web, iOS, Android, Windows, macOS, Linux, Oculus Quest, HTC Vive
- **Automatic Cloud Sync**: Seamless synchronization with conflict resolution
- **Offline Capability**: Full offline functionality with automatic sync when reconnected
- **Character Data Preservation**: Complete character state synchronization
- **Campaign State Sync**: Chapter, scene, quest, and world state preservation

### Real-Time Synchronization
- **WebSocket Connections**: Instant updates across all connected devices
- **Optimistic Locking**: Prevents concurrent edit conflicts
- **Delta Sync**: Efficient data transfer using difference detection
- **Version Control**: Complete version history with rollback capability

### Platform Integration
- **Web App**: localStorage and IndexedDB integration
- **React Native**: AsyncStorage with background sync
- **Desktop**: File system sync with automatic backup
- **VR/AR**: State preservation with platform-specific optimizations
- **API Access**: RESTful API for third-party integrations

### Data Management
- **PostgreSQL**: Structured data with ACID compliance
- **Redis**: Real-time sync state and caching
- **AWS S3**: Large asset storage with CDN
- **Encryption**: End-to-end encryption for sensitive data

### Conflict Resolution
- **Last-Write-Wins**: Simple timestamp-based resolution
- **Manual Resolution**: User interface for complex conflicts
- **Merge Strategies**: Automatic merging for compatible data
- **Audit Trail**: Complete change history and rollback capability

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │  Mobile Client  │    │ Desktop Client  │
│                 │    │                 │    │                 │
│ WebSocket       │    │ AsyncStorage    │    │ File System     │
│ localStorage     │    │ Background Sync │    │ Auto Backup     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │     Sync API Server      │
                    │                           │
                    │ WebSocket Gateway        │
                    │ REST API                 │
                    │ Conflict Resolution       │
                    │ Audit Trail              │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │      Data Layer          │
                    │                           │
                    │ PostgreSQL (Structured)  │
                    │ Redis (Real-time)        │
                    │ S3 (Assets)              │
                    └───────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Node.js 16+
- PostgreSQL 13+
- Redis 6+
- AWS Account (for S3 storage)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/dmlogn8n/cross-platform-sync.git
cd cross-platform-sync
```

2. **Install dependencies**
```bash
npm install
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Setup database**
```bash
# Create PostgreSQL database
createdb dmlogn8n_sync

# Run database migrations
npm run migrate
```

5. **Start services**
```bash
# Start Redis (if not running)
redis-server

# Start the sync server
npm start
```

### Configuration

#### Environment Variables

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dmlogn8n_sync
DB_USER=dmlogn8n
DB_PASSWORD=your_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_S3_BUCKET=dmlogn8n-sync-assets

# JWT Configuration
JWT_SECRET=your_jwt_secret_key

# API Configuration
API_PORT=3000
CORS_ORIGIN=https://yourdomain.com
```

#### Database Setup

Run the database schema creation script:

```bash
psql -d dmlogn8n_sync -f database/01-universal-save-schema.sql
psql -d dmlogn8n_sync -f database/02-redis-sync-state.sql
```

## 📱 Client Integration

### Web Client

```javascript
import { DMLogn8nWebSync } from './clients/web/web-sync-client.js';

const syncClient = new DMLogn8nWebSync({
    apiEndpoint: 'https://api.dmlogn8n.com/sync',
    wsEndpoint: 'wss://ws.dmlogn8n.com',
    authToken: 'your-jwt-token',
    autoSync: true,
    syncInterval: 30000 // 30 seconds
});

// Save game data
await syncClient.saveGame({
    saveGameId: 'save-123',
    campaignName: 'The Dragon\'s Quest',
    characterName: 'Aragorn',
    characters: [{
        name: 'Aragorn',
        level: 15,
        experiencePoints: 25000
    }],
    campaignState: {
        chapter: 3,
        scene: 'dragon_lair',
        flags: { dragon_defeated: false }
    }
});

// Load game data
const saveData = await syncClient.loadGame('save-123');
```

### React Native Client

```javascript
import ReactNativeSyncClient from './clients/mobile/react-native-sync-client.js';

const syncClient = new ReactNativeSyncClient({
    apiEndpoint: 'https://api.dmlogn8n.com/sync',
    authToken: 'your-jwt-token',
    backgroundSync: true,
    pushNotifications: true
});

// Enable background sync
syncClient.startAutoSync();

// Handle app state changes
import { AppState } from 'react-native';

AppState.addEventListener('change', (nextAppState) => {
    if (nextAppState === 'active') {
        syncClient.processSyncQueue();
    }
});
```

### Electron Client

```javascript
const { ipcMain } = require('electron');
const ElectronSyncClient = require('./clients/desktop/electron-sync-client.js');

const syncClient = new ElectronSyncClient({
    apiEndpoint: 'https://api.dmlogn8n.com/sync',
    authToken: 'your-jwt-token',
    saveDirectory: path.join(app.getPath('userData'), 'saves'),
    watchFileChanges: true
});

// Setup IPC handlers
ipcMain.handle('sync:save-game', async (event, saveData) => {
    return await syncClient.saveGame(saveData);
});

// Handle power management
powerMonitor.on('resume', () => {
    syncClient.connectWebSocket();
});
```

## 🔧 n8n Workflows

The system includes comprehensive n8n workflows for automation:

### Auto-Sync Workflow
- **Trigger**: Every 5 minutes
- **Process**: Detect pending syncs, process them with retry logic
- **File**: `workflows/save-sync/auto-sync-workflow.json`

### Conflict Resolution Workflow
- **Trigger**: Webhook on conflict detection
- **Process**: Analyze conflicts, attempt auto-resolution, notify users
- **File**: `workflows/conflict-resolution/conflict-resolution-workflow.json`

### Real-Time Sync Workflow
- **Trigger**: Redis subscription to sync channels
- **Process**: Broadcast updates to connected clients, send push notifications
- **File**: `workflows/real-time-sync/real-time-sync-workflow.json`

### Asset Management Workflow
- **Trigger**: File upload events
- **Process**: Validate assets, store in S3, update metadata
- **File**: `workflows/asset-management/asset-sync-workflow.json`

## 📊 Monitoring & Analytics

### Sync Metrics
```javascript
const metrics = syncClient.getMetrics();
console.log({
    totalConnections: metrics.totalConnections,
    activeConnections: metrics.activeConnections,
    messagesSent: metrics.messagesSent,
    conflictsDetected: metrics.conflictsDetected,
    averageSyncTime: metrics.averageSyncTime
});
```

### Database Analytics
```sql
-- Sync performance analysis
SELECT
    DATE_TRUNC('day', started_at) as sync_date,
    COUNT(*) as total_syncs,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000) as avg_sync_time_ms,
    COUNT(*) FILTER (WHERE status = 'synced') as successful_syncs,
    COUNT(*) FILTER (WHERE status = 'error') as failed_syncs
FROM sync_operations
WHERE started_at >= NOW() - INTERVAL '30 days'
GROUP BY sync_date
ORDER BY sync_date DESC;
```

### Conflict Analytics
```sql
-- Conflict resolution statistics
SELECT
    conflict_type,
    resolution_strategy,
    COUNT(*) as conflict_count,
    AVG(EXTRACT(EPOCH FROM (resolved_at - detected_at)) / 60) as avg_resolution_time_minutes
FROM sync_conflicts
WHERE detected_at >= NOW() - INTERVAL '30 days'
GROUP BY conflict_type, resolution_strategy
ORDER BY conflict_count DESC;
```

## 🔒 Security

### Data Encryption
- **In Transit**: TLS 1.3 for all API communications
- **At Rest**: AES-256 encryption for sensitive data
- **End-to-End**: Optional client-side encryption for highly sensitive saves

### Authentication
- **JWT Tokens**: Secure token-based authentication
- **Platform Verification**: Device and platform validation
- **Rate Limiting**: Prevent abuse and protect against DDoS

### Audit Trail
- **Complete Logging**: All operations logged with timestamps
- **Compliance**: GDPR and CCPA compliant data handling
- **Integrity Verification**: Cryptographic hashes for data integrity

## 🚀 Deployment

### Docker Deployment

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

```yaml
# docker-compose.yml
version: '3.8'

services:
  sync-api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DB_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=dmlogn8n_sync
      - POSTGRES_USER=dmlogn8n
      - POSTGRES_PASSWORD=your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    command: redis-server --requirepass your_redis_password
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dmlogn8n-sync-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dmlogn8n-sync-api
  template:
    metadata:
      labels:
        app: dmlogn8n-sync-api
    spec:
      containers:
      - name: api
        image: dmlogn8n/sync-api:latest
        ports:
        - containerPort: 3000
        env:
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: host
        - name: REDIS_HOST
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: host
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### AWS Deployment

```yaml
# serverless.yml
service: dmlogn8n-sync

provider:
  name: aws
  runtime: nodejs18.x
  region: us-east-1
  environment:
    DB_HOST: ${ssm:/dmlogn8n/db/host}
    REDIS_HOST: ${ssm:/dmlogn8n/redis/host}

functions:
  sync:
    handler: api/sync-api.handler
    events:
      - http:
          path: /sync/{proxy+}
          method: ANY
          cors: true
```

## 🧪 Testing

### Unit Tests
```bash
# Run unit tests
npm test

# Run with coverage
npm run test:coverage
```

### Integration Tests
```bash
# Run integration tests
npm run test:integration

# Run API tests
npm run test:api
```

### Load Testing
```bash
# Run load tests with Artillery
artillery run load-tests/sync-api.yml
```

## 📈 Performance Optimization

### Database Optimization
- **Indexing**: Optimized indexes for frequently queried fields
- **Connection Pooling**: Efficient database connection management
- **Query Optimization**: Analyzed and optimized slow queries

### Caching Strategy
- **Redis Caching**: Frequently accessed save data cached in Redis
- **CDN Integration**: Static assets served through CDN
- **Browser Caching**: Appropriate cache headers for API responses

### Sync Optimization
- **Delta Sync**: Only transfer changed data
- **Compression**: Compress large save files
- **Batching**: Group multiple sync operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Full documentation](https://docs.dmlogn8n.com/sync)
- **API Reference**: [API docs](https://api.dmlogn8n.com/docs)
- **Issues**: [GitHub Issues](https://github.com/dmlogn8n/cross-platform-sync/issues)
- **Discord**: [Community Discord](https://discord.gg/dmlogn8n)

## 🗺️ Roadmap

### Version 1.1 (Q1 2024)
- [ ] Enhanced mobile sync performance
- [ ] Additional conflict resolution strategies
- [ ] Improved analytics dashboard
- [ ] Multi-language support

### Version 1.2 (Q2 2024)
- [ ] Real-time collaboration features
- [ ] Advanced conflict visualization
- [ ] Custom sync rules engine
- [ ] Enterprise SSO integration

### Version 2.0 (Q3 2024)
- [ ] AI-powered conflict resolution
- [ ] Predictive sync algorithms
- [ ] Advanced analytics and ML insights
- [ ] Blockchain-based save verification

---

**Built with ❤️ for the DMlogn8n community**