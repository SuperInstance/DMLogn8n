/**
 * Comprehensive Logging Utility for Integration Testing
 *
 * Provides structured logging with multiple output formats:
 * - Console output with colors and formatting
 * - File logging with rotation
 * - JSON structured logging
 * - Test-specific logging categories
 * - Performance metrics logging
 */

const winston = require('winston')
const path = require('path')
const fs = require('fs')
const { config } = require('../../config/test-config')

// Ensure log directory exists
const logDir = config.paths.logs
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true })
}

// Custom format for console output
const consoleFormat = winston.format.combine(
  winston.format.timestamp({ format: 'HH:mm:ss' }),
  winston.format.errors({ stack: true }),
  winston.format.colorize({ all: true }),
  winston.format.printf(({ level, message, timestamp, service, test, ...meta }) => {
    let log = `${timestamp} [${level}]`

    if (service) {
      log += ` [${service}]`
    }

    if (test) {
      log += ` [${test}]`
    }

    log += `: ${message}`

    // Add metadata
    if (Object.keys(meta).length > 0) {
      log += ` ${JSON.stringify(meta, null, 2)}`
    }

    return log
  })
)

// Custom format for file output
const fileFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.errors({ stack: true }),
  winston.format.json()
)

// Create logger instance
const logger = winston.createLogger({
  level: config.logging.level,
  format: fileFormat,
  defaultMeta: {
    service: 'integration-testing',
    environment: config.environment
  },
  transports: [
    // Console transport
    new winston.transports.Console({
      format: consoleFormat,
      silent: !config.logging.transports.console.enabled,
      colorize: config.logging.transports.console.colorize
    }),

    // General log file
    new winston.transports.File({
      filename: path.join(logDir, 'test.log'),
      maxsize: 10 * 1024 * 1024, // 10MB
      maxFiles: config.logging.transports.file.maxFiles,
      format: fileFormat,
      silent: !config.logging.transports.file.enabled
    }),

    // Error log file
    new winston.transports.File({
      filename: path.join(logDir, 'error.log'),
      level: 'error',
      maxsize: 10 * 1024 * 1024, // 10MB
      maxFiles: config.logging.transports.file.maxFiles,
      format: fileFormat,
      silent: !config.logging.transports.file.enabled
    }),

    // Performance log file
    new winston.transports.File({
      filename: path.join(logDir, 'performance.log'),
      level: 'debug',
      maxsize: 50 * 1024 * 1024, // 50MB
      maxFiles: 5,
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
      ),
      silent: !config.logging.transports.file.enabled
    })
  ],

  // Handle uncaught exceptions
  exceptionHandlers: [
    new winston.transports.File({
      filename: path.join(logDir, 'exceptions.log')
    })
  ],

  // Handle unhandled promise rejections
  rejectionHandlers: [
    new winston.transports.File({
      filename: path.join(logDir, 'rejections.log')
    })
  ]
})

// Test-specific logging methods
const testLogger = {
  /**
   * Log test start
   */
  testStart(testName, category = 'general') {
    logger.info(`▶️  Starting test: ${testName}`, {
      type: 'test-start',
      test: testName,
      category,
      timestamp: new Date().toISOString()
    })
  },

  /**
   * Log test completion
   */
  testEnd(testName, result, duration, category = 'general') {
    const status = result ? '✅ PASSED' : '❌ FAILED'
    logger.info(`${status} ${testName} (${duration}ms)`, {
      type: 'test-end',
      test: testName,
      category,
      result,
      duration,
      timestamp: new Date().toISOString()
    })
  },

  /**
   * Log test step
   */
  testStep(testName, step, category = 'general') {
    logger.debug(`📋 ${testName}: ${step}`, {
      type: 'test-step',
      test: testName,
      step,
      category,
      timestamp: new Date().toISOString()
    })
  },

  /**
   * Log assertion
   */
  assertion(testName, description, result, expected, actual) {
    const status = result ? '✅' : '❌'
    logger.debug(`${status} Assertion: ${description}`, {
      type: 'assertion',
      test: testName,
      description,
      result,
      expected,
      actual,
      timestamp: new Date().toISOString()
    })
  },

  /**
   * Log API request
   */
  apiRequest(method, url, statusCode, duration, requestData = null, responseData = null) {
    const status = statusCode >= 200 && statusCode < 300 ? '✅' : '❌'
    logger.info(`${status} ${method} ${url} (${statusCode}) - ${duration}ms`, {
      type: 'api-request',
      method,
      url,
      statusCode,
      duration,
      requestData,
      responseData,
      timestamp: new Date().toISOString()
    })
  },

  /**
   * Log WebSocket event
   */
  websocketEvent(event, direction, data, socketId) {
    logger.debug(`🔌 WebSocket ${direction}: ${event}`, {
      type: 'websocket-event',
      event,
      direction,
      data,
      socketId,
      timestamp: new Date().toISOString()
    })
  },

  /**
   * Log database operation
   */
  databaseOperation(operation, collection, duration, affected = null) {
    logger.debug(`🗄️  DB ${operation} on ${collection} (${duration}ms)`, {
      type: 'database-operation',
      operation,
      collection,
      duration,
      affected,
      timestamp: new Date().toISOString()
    })
  },

  /**
   * Log performance metric
   */
  performance(metric, value, unit, context = {}) {
    logger.info(`📊 Performance: ${metric} = ${value}${unit}`, {
      type: 'performance-metric',
      metric,
      value,
      unit,
      context,
      timestamp: new Date().toISOString()
    })
  },

  /**
   * Log memory usage
   */
  memoryUsage(testName = null) {
    const usage = process.memoryUsage()
    const formatted = {
      rss: `${Math.round(usage.rss / 1024 / 1024)}MB`,
      heapTotal: `${Math.round(usage.heapTotal / 1024 / 1024)}MB`,
      heapUsed: `${Math.round(usage.heapUsed / 1024 / 1024)}MB`,
      external: `${Math.round(usage.external / 1024 / 1024)}MB`
    }

    logger.debug(`💾 Memory usage: ${JSON.stringify(formatted)}`, {
      type: 'memory-usage',
      test: testName,
      usage,
      formatted,
      timestamp: new Date().toISOString()
    })

    return usage
  },

  /**
   * Log CPU usage
   */
  cpuUsage(testName = null) {
    const usage = process.cpuUsage()
    logger.debug(`🖥️  CPU usage: ${JSON.stringify(usage)}`, {
      type: 'cpu-usage',
      test: testName,
      usage,
      timestamp: new Date().toISOString()
    })

    return usage
  },

  /**
   * Log mock server event
   */
  mockServerEvent(serverName, event, data) {
    logger.debug(`🎭 Mock Server [${serverName}]: ${event}`, {
      type: 'mock-server-event',
      server: serverName,
      event,
      data,
      timestamp: new Date().toISOString()
    })
  },

  /**
   * Log test environment event
   */
  environmentEvent(event, data) {
    logger.info(`🏗️  Environment: ${event}`, {
      type: 'environment-event',
      event,
      data,
      timestamp: new Date().toISOString()
    })
  },

  /**
   * Log setup/teardown operation
   */
  setupOperation(operation, target, duration, success = true) {
    const status = success ? '✅' : '❌'
    logger.info(`${status} Setup ${operation}: ${target} (${duration}ms)`, {
      type: 'setup-operation',
      operation,
      target,
      duration,
      success,
      timestamp: new Date().toISOString()
    })
  },

  /**
   * Log data seeding
   */
  dataSeeding(type, count, duration) {
    logger.info(`🌱 Seeded ${count} ${type} records (${duration}ms)`, {
      type: 'data-seeding',
      dataType: type,
      count,
      duration,
      timestamp: new Date().toISOString()
    })
  },

  /**
   * Log error with context
   */
  error(message, error, context = {}) {
    logger.error(`❌ Error: ${message}`, {
      type: 'error',
      message,
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack
      },
      context,
      timestamp: new Date().toISOString()
    })
  },

  /**
   * Log warning
   */
  warning(message, context = {}) {
    logger.warn(`⚠️  Warning: ${message}`, {
      type: 'warning',
      message,
      context,
      timestamp: new Date().toISOString()
    })
  },

  /**
   * Log debug information
   */
  debug(message, context = {}) {
    logger.debug(message, {
      type: 'debug',
      message,
      context,
      timestamp: new Date().toISOString()
    })
  },

  /**
   * Log info
   */
  info(message, context = {}) {
    logger.info(message, {
      type: 'info',
      message,
      context,
      timestamp: new Date().toISOString()
    })
  }
}

// Performance monitor class
class PerformanceMonitor {
  constructor(testName) {
    this.testName = testName
    this.metrics = new Map()
    this.startTime = Date.now()
  }

  /**
   * Start timing an operation
   */
  startTimer(operation) {
    this.metrics.set(operation, {
      startTime: process.hrtime.bigint(),
      startMemory: process.memoryUsage()
    })
  }

  /**
   * End timing an operation and log the result
   */
  endTimer(operation) {
    const metric = this.metrics.get(operation)
    if (!metric) {
      return null
    }

    const endTime = process.hrtime.bigint()
    const endMemory = process.memoryUsage()
    const duration = Number(endTime - metric.startTime) / 1000000 // Convert to milliseconds

    const memoryDelta = {
      rss: endMemory.rss - metric.startMemory.rss,
      heapUsed: endMemory.heapUsed - metric.startMemory.heapUsed,
      heapTotal: endMemory.heapTotal - metric.startMemory.heapTotal
    }

    testLogger.performance(operation, duration, 'ms', {
      test: this.testName,
      memoryDelta
    })

    this.metrics.delete(operation)
    return { duration, memoryDelta }
  }

  /**
   * Measure async function execution time
   */
  async measureAsync(operation, fn) {
    this.startTimer(operation)
    try {
      const result = await fn()
      this.endTimer(operation)
      return result
    } catch (error) {
      this.endTimer(operation)
      throw error
    }
  }

  /**
   * Get test summary
   */
  getSummary() {
    const totalDuration = Date.now() - this.startTime
    const memoryUsage = process.memoryUsage()

    return {
      testName: this.testName,
      totalDuration,
      memoryUsage,
      timestamp: new Date().toISOString()
    }
  }
}

// Log analyzer utility
class LogAnalyzer {
  /**
   * Parse log file and extract metrics
   */
  static async analyzeLogFile(filePath) {
    const logs = []
    const metrics = {
      totalTests: 0,
      passedTests: 0,
      failedTests: 0,
      totalDuration: 0,
      averageDuration: 0,
      errors: [],
      warnings: [],
      performanceMetrics: []
    }

    try {
      const content = fs.readFileSync(filePath, 'utf8')
      const lines = content.split('\n').filter(line => line.trim())

      for (const line of lines) {
        try {
          const logEntry = JSON.parse(line)
          logs.push(logEntry)

          // Analyze different log types
          switch (logEntry.type) {
            case 'test-end':
              metrics.totalTests++
              if (logEntry.result) {
                metrics.passedTests++
              } else {
                metrics.failedTests++
              }
              metrics.totalDuration += logEntry.duration
              break

            case 'error':
              metrics.errors.push(logEntry)
              break

            case 'warning':
              metrics.warnings.push(logEntry)
              break

            case 'performance-metric':
              metrics.performanceMetrics.push(logEntry)
              break
          }
        } catch (parseError) {
          // Skip malformed lines
        }
      }

      metrics.averageDuration = metrics.totalTests > 0 ? metrics.totalDuration / metrics.totalTests : 0

      return metrics
    } catch (error) {
      throw new Error(`Failed to analyze log file: ${error.message}`)
    }
  }

  /**
   * Generate test report from logs
   */
  static generateReport(metrics) {
    return {
      summary: {
        totalTests: metrics.totalTests,
        passedTests: metrics.passedTests,
        failedTests: metrics.failedTests,
        passRate: metrics.totalTests > 0 ? (metrics.passedTests / metrics.totalTests * 100).toFixed(2) : 0,
        totalDuration: metrics.totalDuration,
        averageDuration: metrics.averageDuration.toFixed(2)
      },
      issues: {
        errors: metrics.errors.length,
        warnings: metrics.warnings.length
      },
      performance: {
        metricsCount: metrics.performanceMetrics.length,
        topSlowOperations: this.getTopSlowOperations(metrics.performanceMetrics)
      },
      generatedAt: new Date().toISOString()
    }
  }

  /**
   * Get top slow operations from performance metrics
   */
  static getTopSlowOperations(metrics) {
    return metrics
      .filter(m => m.unit === 'ms')
      .sort((a, b) => b.value - a.value)
      .slice(0, 10)
      .map(m => ({
        operation: m.metric,
        duration: m.value,
        test: m.context.test
      }))
  }
}

// Export logger and utilities
module.exports = {
  logger,
  testLogger,
  PerformanceMonitor,
  LogAnalyzer
}