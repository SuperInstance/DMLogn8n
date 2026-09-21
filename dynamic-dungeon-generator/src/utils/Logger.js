/**
 * Logger Utility
 * Centralized logging system with multiple output options
 */

const winston = require('winston');
const path = require('path');
const fs = require('fs');

class Logger {
  constructor(config = {}) {
    this.config = {
      level: config.level || 'info',
      file_enabled: config.file_enabled !== false,
      console_enabled: config.console_enabled !== false,
      max_file_size: config.max_file_size || '10MB',
      max_files: config.max_files || 5,
      log_directory: config.log_directory || path.join(__dirname, '../../logs'),
      ...config
    };

    this.logger = this.createLogger();
  }

  /**
   * Create winston logger instance
   */
  createLogger() {
    const transports = [];

    // Console transport
    if (this.config.console_enabled) {
      transports.push(
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.timestamp(),
            winston.format.printf(({ timestamp, level, message, ...meta }) => {
              const metaStr = Object.keys(meta).length ? JSON.stringify(meta, null, 2) : '';
              return `${timestamp} [${level}]: ${message} ${metaStr}`;
            })
          )
        })
      );
    }

    // File transport
    if (this.config.file_enabled) {
      // Ensure log directory exists
      if (!fs.existsSync(this.config.log_directory)) {
        fs.mkdirSync(this.config.log_directory, { recursive: true });
      }

      transports.push(
        new winston.transports.File({
          filename: path.join(this.config.log_directory, 'error.log'),
          level: 'error',
          maxsize: this.parseSize(this.config.max_file_size),
          maxFiles: this.config.max_files,
          format: winston.format.combine(
            winston.format.timestamp(),
            winston.format.json()
          )
        }),
        new winston.transports.File({
          filename: path.join(this.config.log_directory, 'combined.log'),
          maxsize: this.parseSize(this.config.max_file_size),
          maxFiles: this.config.max_files,
          format: winston.format.combine(
            winston.format.timestamp(),
            winston.format.json()
          )
        })
      );
    }

    // Create logger
    const logger = winston.createLogger({
      level: this.config.level,
      transports,
      exitOnError: false
    });

    // Handle uncaught exceptions
    logger.exceptions.handle(
      new winston.transports.File({
        filename: path.join(this.config.log_directory, 'exceptions.log')
      })
    );

    return logger;
  }

  /**
   * Parse size string to bytes
   */
  parseSize(sizeStr) {
    const units = {
      'B': 1,
      'KB': 1024,
      'MB': 1024 * 1024,
      'GB': 1024 * 1024 * 1024
    };

    const match = sizeStr.match(/^(\d+)(B|KB|MB|GB)$/i);
    if (!match) {
      return 10 * 1024 * 1024; // Default 10MB
    }

    const [, size, unit] = match;
    return parseInt(size) * (units[unit.toUpperCase()] || 1);
  }

  /**
   * Log methods
   */
  error(message, meta = {}) {
    this.logger.error(message, meta);
  }

  warn(message, meta = {}) {
    this.logger.warn(message, meta);
  }

  info(message, meta = {}) {
    this.logger.info(message, meta);
  }

  debug(message, meta = {}) {
    this.logger.debug(message, meta);
  }

  verbose(message, meta = {}) {
    this.logger.verbose(message, meta);
  }

  /**
   * Log dungeon generation start
   */
  logGenerationStart(params) {
    this.info('Dungeon generation started', {
      algorithm: params.algorithm,
      theme: params.theme,
      dimensions: {
        width: params.width,
        height: params.height,
        floors: params.floors
      },
      difficulty: params.difficulty,
      playerLevel: params.playerLevel,
      seed: params.seed
    });
  }

  /**
   * Log dungeon generation completion
   */
  logGenerationComplete(params, stats, duration) {
    this.info('Dungeon generation completed', {
      generationId: params.generationId,
      duration: `${duration}ms`,
      statistics: stats,
      floors: params.floors
    });
  }

  /**
   * Log dungeon generation error
   */
  logGenerationError(params, error) {
    this.error('Dungeon generation failed', {
      generationId: params.generationId,
      algorithm: params.algorithm,
      theme: params.theme,
      error: {
        message: error.message,
        stack: error.stack
      }
    });
  }

  /**
   * Log API request
   */
  logApiRequest(req, res, duration) {
    this.info('API Request', {
      method: req.method,
      url: req.url,
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      statusCode: res.statusCode,
      duration: `${duration}ms`
    });
  }

  /**
   * Log performance metrics
   */
  logPerformance(operation, duration, metadata = {}) {
    this.info('Performance metric', {
      operation,
      duration: `${duration}ms`,
      ...metadata
    });
  }

  /**
   * Create child logger with additional context
   */
  child(context) {
    return {
      error: (message, meta = {}) => this.error(message, { ...context, ...meta }),
      warn: (message, meta = {}) => this.warn(message, { ...context, ...meta }),
      info: (message, meta = {}) => this.info(message, { ...context, ...meta }),
      debug: (message, meta = {}) => this.debug(message, { ...context, ...meta }),
      verbose: (message, meta = {}) => this.verbose(message, { ...context, ...meta })
    };
  }

  /**
   * Set log level
   */
  setLevel(level) {
    this.config.level = level;
    this.logger.level = level;
    this.logger.transports.forEach(transport => {
      if (transport.level) {
        transport.level = level;
      }
    });
  }

  /**
   * Get current log level
   */
  getLevel() {
    return this.config.level;
  }

  /**
   * Add custom transport
   */
  addTransport(transport) {
    this.logger.add(transport);
  }

  /**
   * Remove transport
   */
  removeTransport(transport) {
    this.logger.remove(transport);
  }

  /**
   * Get log stats
   */
  getStats() {
    return {
      level: this.config.level,
      transports: this.logger.transports.length,
      file_enabled: this.config.file_enabled,
      console_enabled: this.config.console_enabled,
      log_directory: this.config.log_directory
    };
  }

  /**
   * Rotate logs manually
   */
  rotateLogs() {
    this.logger.transports.forEach(transport => {
      if (transport instanceof winston.transports.File) {
        transport.rotate();
      }
    });
  }

  /**
   * Clear logs
   */
  clearLogs() {
    if (fs.existsSync(this.config.log_directory)) {
      const files = fs.readdirSync(this.config.log_directory);
      for (const file of files) {
        if (file.endsWith('.log')) {
          fs.unlinkSync(path.join(this.config.log_directory, file));
        }
      }
    }
  }

  /**
   * Query logs
   */
  queryLogs(options = {}) {
    const {
      level,
      since,
      until,
      limit = 100,
      offset = 0,
      search
    } = options;

    // This is a simplified implementation
    // In a production environment, you might want to use a proper log query system
    return new Promise((resolve, reject) => {
      try {
        const logFile = path.join(this.config.log_directory, 'combined.log');
        if (!fs.existsSync(logFile)) {
          return resolve({ logs: [], total: 0 });
        }

        const content = fs.readFileSync(logFile, 'utf8');
        const lines = content.split('\n').filter(line => line.trim());

        let logs = lines.map(line => {
          try {
            return JSON.parse(line);
          } catch {
            return { message: line, timestamp: new Date().toISOString(), level: 'info' };
          }
        });

        // Apply filters
        if (level) {
          logs = logs.filter(log => log.level === level);
        }

        if (search) {
          logs = logs.filter(log =>
            JSON.stringify(log).toLowerCase().includes(search.toLowerCase())
          );
        }

        if (since) {
          const sinceDate = new Date(since);
          logs = logs.filter(log => new Date(log.timestamp) >= sinceDate);
        }

        if (until) {
          const untilDate = new Date(until);
          logs = logs.filter(log => new Date(log.timestamp) <= untilDate);
        }

        const total = logs.length;
        logs = logs.slice(offset, offset + limit);

        resolve({ logs, total });
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Export logs to file
   */
  exportLogs(filePath, options = {}) {
    return this.queryLogs(options).then(({ logs }) => {
      const exportData = {
        exported_at: new Date().toISOString(),
        export_options: options,
        total_logs: logs.length,
        logs
      };

      fs.writeFileSync(filePath, JSON.stringify(exportData, null, 2));
      return { success: true, file_path: filePath, count: logs.length };
    });
  }
}

module.exports = Logger;