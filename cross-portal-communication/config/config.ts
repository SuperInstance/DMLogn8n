import dotenv from 'dotenv';

dotenv.config();

export const config = {
  // Server Configuration
  port: parseInt(process.env.PORT || '3001'),
  host: process.env.HOST || 'localhost',

  // WebSocket Configuration
  wsPort: parseInt(process.env.WS_PORT || '3002'),
  wsHeartbeatInterval: parseInt(process.env.WS_HEARTBEAT_INTERVAL || '30000'),
  wsMaxConnections: parseInt(process.env.WS_MAX_CONNECTIONS || '1000'),

  // Redis Configuration
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379'),
    password: process.env.REDIS_PASSWORD || undefined,
    db: parseInt(process.env.REDIS_DB || '0'),
    maxRetriesPerRequest: 3,
    retryDelayOnFailover: 100,
    lazyConnect: true,
    keyPrefix: 'cpc:',
  },

  // Database Configuration
  database: {
    uri: process.env.DATABASE_URI || 'mongodb://localhost:27017/cross-portal-comm',
    options: {
      useNewUrlParser: true,
      useUnifiedTopology: true,
      maxPoolSize: 10,
      serverSelectionTimeoutMS: 5000,
      socketTimeoutMS: 45000,
    }
  },

  // Security Configuration
  security: {
    jwtSecret: process.env.JWT_SECRET || 'your-super-secret-jwt-key-change-in-production',
    jwtExpiration: process.env.JWT_EXPIRATION || '24h',
    bcryptRounds: parseInt(process.env.BCRYPT_ROUNDS || '12'),
    encryptionKey: process.env.ENCRYPTION_KEY || 'your-32-character-encryption-key-123456',
    rateLimitWindowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '900000'), // 15 minutes
    rateLimitMax: parseInt(process.env.RATE_LIMIT_MAX || '100'),
  },

  // Message Configuration
  messaging: {
    maxMessageSize: parseInt(process.env.MAX_MESSAGE_SIZE || '1048576'), // 1MB
    messageHistoryLimit: parseInt(process.env.MESSAGE_HISTORY_LIMIT || '100'),
    priorityQueueSize: parseInt(process.env.PRIORITY_QUEUE_SIZE || '10000'),
    broadcastMaxTargets: parseInt(process.env.BROADCAST_MAX_TARGETS || '500'),
  },

  // Portal Configuration
  portals: {
    dmPortal: process.env.DM_PORTAL_URL || 'http://localhost:3000',
    playerPortal: process.env.PLAYER_PORTAL_URL || 'http://localhost:3001',
    coderPortal: process.env.CODER_PORTAL_URL || 'http://localhost:3002',
    combatPortal: process.env.COMBAT_PORTAL_URL || 'http://localhost:3003',
    characterPortal: process.env.CHARACTER_PORTAL_URL || 'http://localhost:3004',
  },

  // Logging Configuration
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    file: process.env.LOG_FILE || 'logs/cross-portal-comm.log',
    maxSize: process.env.LOG_MAX_SIZE || '20m',
    maxFiles: parseInt(process.env.LOG_MAX_FILES || '14'),
  },

  // Performance Configuration
  performance: {
    compressionLevel: parseInt(process.env.COMPRESSION_LEVEL || '6'),
    cacheTimeout: parseInt(process.env.CACHE_TIMEOUT || '300000'), // 5 minutes
    syncInterval: parseInt(process.env.SYNC_INTERVAL || '5000'), // 5 seconds
  }
};

// Environment-specific overrides
if (process.env.NODE_ENV === 'production') {
  config.logging.level = 'warn';
  config.wsHeartbeatInterval = 60000;
  config.messaging.priorityQueueSize = 50000;
} else if (process.env.NODE_ENV === 'development') {
  config.logging.level = 'debug';
  config.wsHeartbeatInterval = 10000;
}

export default config;