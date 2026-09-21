const winston = require('winston');
const path = require('path');

// Create logs directory if it doesn't exist
const fs = require('fs');
const logsDir = path.join(__dirname, '../logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

// Define log format
const logFormat = winston.format.combine(
  winston.format.timestamp({
    format: 'YYYY-MM-DD HH:mm:ss'
  }),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.prettyPrint()
);

// Create logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: logFormat,
  transports: [
    // Error log file
    new winston.transports.File({
      filename: path.join(logsDir, 'error.log'),
      level: 'error',
      maxsize: 5242880, // 5MB
      maxFiles: 5
    }),

    // Combined log file
    new winston.transports.File({
      filename: path.join(logsDir, 'combined.log'),
      maxsize: 5242880, // 5MB
      maxFiles: 5
    }),

    // Game events log
    new winston.transports.File({
      filename: path.join(logsDir, 'game-events.log'),
      level: 'info',
      maxsize: 5242880, // 5MB
      maxFiles: 10
    })
  ]
});

// Add console transport for development
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    )
  }));
}

// Create specialized game logger
const gameLogger = {
  characterAction: (campaignId, characterId, action, details = {}) => {
    logger.info('Character Action', {
      type: 'character_action',
      campaignId,
      characterId,
      action,
      details,
      timestamp: new Date().toISOString()
    });
  },

  combatEvent: (campaignId, combatId, event, details = {}) => {
    logger.info('Combat Event', {
      type: 'combat_event',
      campaignId,
      combatId,
      event,
      details,
      timestamp: new Date().toISOString()
    });
  },

  worldChange: (campaignId, changeType, details = {}) => {
    logger.info('World Change', {
      type: 'world_change',
      campaignId,
      changeType,
      details,
      timestamp: new Date().toISOString()
    });
  },

  playerConnect: (campaignId, userId, characterId) => {
    logger.info('Player Connected', {
      type: 'player_connect',
      campaignId,
      userId,
      characterId,
      timestamp: new Date().toISOString()
    });
  },

  playerDisconnect: (campaignId, userId, characterId) => {
    logger.info('Player Disconnected', {
      type: 'player_disconnect',
      campaignId,
      userId,
      characterId,
      timestamp: new Date().toISOString()
    });
  },

  dmAction: (campaignId, userId, action, details = {}) => {
    logger.info('DM Action', {
      type: 'dm_action',
      campaignId,
      userId,
      action,
      details,
      timestamp: new Date().toISOString()
    });
  },

  systemEvent: (campaignId, event, details = {}) => {
    logger.info('System Event', {
      type: 'system_event',
      campaignId,
      event,
      details,
      timestamp: new Date().toISOString()
    });
  },

  performanceMetric: (campaignId, metric, value) => {
    logger.info('Performance Metric', {
      type: 'performance',
      campaignId,
      metric,
      value,
      timestamp: new Date().toISOString()
    });
  },

  error: (campaignId, error, context = {}) => {
    logger.error('Game Error', {
      type: 'game_error',
      campaignId,
      error: error.message,
      stack: error.stack,
      context,
      timestamp: new Date().toISOString()
    });
  }
};

// Utility functions for log analysis
const analytics = {
  getActionCounts: async (campaignId, startDate, endDate) => {
    // This would typically query a database or log aggregation service
    // For now, it's a placeholder
    return {
      characterActions: 0,
      combatEvents: 0,
      worldChanges: 0,
      dmActions: 0
    };
  },

  getPlayerActivity: async (campaignId, startDate, endDate) => {
    // Placeholder for player activity analysis
    return {};
  },

  getPerformanceMetrics: async (campaignId, startDate, endDate) => {
    // Placeholder for performance metrics
    return {
      averageResponseTime: 0,
      peakConnections: 0,
      totalEvents: 0
    };
  }
};

module.exports = { logger, gameLogger, analytics };