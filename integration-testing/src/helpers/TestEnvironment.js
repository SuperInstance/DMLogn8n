/**
 * Test Environment Manager
 *
 * Handles setup and teardown of test environments including:
 * - Database connections and seeding
 * - Mock server startup/shutdown
 * - Service discovery and health checks
 * - Environment isolation
 */

const { MongoMemoryServer } = require('mongodb-memory-server')
const Redis = require('ioredis')
const mongoose = require('mongoose')
const { Pool } = require('pg')
const { EventEmitter } = require('events')
const { config, getDatabaseString } = require('../../config/test-config')
const logger = require('../utils/logger')

class TestEnvironment extends EventEmitter {
  constructor(options = {}) {
    super()

    this.options = {
      autoStart: true,
      useInMemoryDatabases: true,
      cleanupOnExit: true,
      ...options
    }

    this.state = {
      databases: {},
      mockServers: {},
      services: {},
      healthChecks: {},
      isReady: false
    }

    this.mongoServer = null
    this.postgresPool = null
    this.redisClient = null
    this.cleanupTasks = []
  }

  /**
   * Initialize the test environment
   */
  async initialize() {
    try {
      logger.info('Initializing test environment...')

      // Setup cleanup on process exit
      if (this.options.cleanupOnExit) {
        process.on('exit', () => this.cleanup())
        process.on('SIGINT', () => this.cleanup())
        process.on('SIGTERM', () => this.cleanup())
      }

      // Initialize databases
      await this.initializeDatabases()

      // Start mock servers if enabled
      if (config.mockServers.enabled) {
        await this.startMockServers()
      }

      // Perform health checks on real services
      await this.performHealthChecks()

      this.state.isReady = true
      this.emit('ready')
      logger.info('Test environment initialized successfully')

    } catch (error) {
      logger.error('Failed to initialize test environment:', error)
      this.emit('error', error)
      throw error
    }
  }

  /**
   * Initialize database connections
   */
  async initializeDatabases() {
    logger.debug('Initializing database connections...')

    // MongoDB
    if (this.options.useInMemoryDatabases) {
      this.mongoServer = await MongoMemoryServer.create()
      const mongoUri = this.mongoServer.getUri()
      await mongoose.connect(mongoUri, config.databases.mongodb.options)
      logger.debug(`MongoDB in-memory server started at: ${mongoUri}`)
    } else {
      await mongoose.connect(getDatabaseString('mongodb'), config.databases.mongodb.options)
      logger.debug('Connected to external MongoDB')
    }
    this.state.databases.mongodb = mongoose.connection

    // PostgreSQL
    try {
      const pgConfig = config.databases.postgresql
      this.postgresPool = new Pool({
        host: pgConfig.host,
        port: pgConfig.port,
        database: pgConfig.database,
        user: pgConfig.username,
        password: pgConfig.password,
        max: pgConfig.options.max,
        idleTimeoutMillis: pgConfig.options.idleTimeoutMillis,
        connectionTimeoutMillis: pgConfig.options.connectionTimeoutMillis
      })

      // Test connection
      const client = await this.postgresPool.connect()
      await client.query('SELECT NOW()')
      client.release()

      this.state.databases.postgresql = this.postgresPool
      logger.debug('PostgreSQL connection established')
    } catch (error) {
      logger.warn('PostgreSQL not available, skipping:', error.message)
    }

    // Redis
    try {
      const redisConfig = config.databases.redis
      this.redisClient = new Redis({
        host: redisConfig.host,
        port: redisConfig.port,
        db: redisConfig.db,
        password: redisConfig.password,
        connectTimeout: redisConfig.options.connectTimeout,
        lazyConnect: redisConfig.options.lazyConnect,
        maxRetriesPerRequest: redisConfig.options.maxRetriesPerRequest
      })

      await this.redisClient.connect()
      this.state.databases.redis = this.redisClient
      logger.debug('Redis connection established')
    } catch (error) {
      logger.warn('Redis not available, skipping:', error.message)
    }

    logger.info('Database connections initialized')
  }

  /**
   * Start mock servers
   */
  async startMockServers() {
    logger.debug('Starting mock servers...')

    const MockServer = require('../mocks/MockServer')
    const mockServices = [
      'aiDialogue',
      'arena',
      'crafting',
      'guild',
      'quest',
      'voice',
      'weather'
    ]

    for (const serviceName of mockServices) {
      try {
        const serviceConfig = config.services[serviceName]
        const mockServer = new MockServer({
          name: serviceName,
          port: this.getAvailablePort(),
          ...serviceConfig,
          ...config.mockServers
        })

        await mockServer.start()
        this.state.mockServers[serviceName] = mockServer
        logger.debug(`Mock server for ${serviceName} started on port ${mockServer.port}`)
      } catch (error) {
        logger.error(`Failed to start mock server for ${serviceName}:`, error)
      }
    }

    logger.info('Mock servers started')
  }

  /**
   * Perform health checks on services
   */
  async performHealthChecks() {
    logger.debug('Performing health checks on services...')

    const services = ['n8n', 'aiDialogue', 'arena', 'crafting', 'guild', 'quest', 'voice', 'weather']

    for (const serviceName of services) {
      try {
        const isHealthy = await this.checkServiceHealth(serviceName)
        this.state.healthChecks[serviceName] = {
          healthy: isHealthy,
          lastCheck: new Date(),
          error: null
        }

        if (isHealthy) {
          logger.debug(`Service ${serviceName} is healthy`)
        } else {
          logger.warn(`Service ${serviceName} is not available`)
        }
      } catch (error) {
        this.state.healthChecks[serviceName] = {
          healthy: false,
          lastCheck: new Date(),
          error: error.message
        }
        logger.warn(`Health check failed for ${serviceName}:`, error.message)
      }
    }

    logger.info('Health checks completed')
  }

  /**
   * Check health of a specific service
   */
  async checkServiceHealth(serviceName) {
    const axios = require('axios')
    const serviceConfig = config.services[serviceName]

    if (!serviceConfig) {
      return false
    }

    try {
      const url = `${serviceConfig.protocol}://${serviceConfig.host}:${serviceConfig.port}/health`
      const response = await axios.get(url, { timeout: 5000 })
      return response.status === 200
    } catch (error) {
      // Check if mock server is available
      if (this.state.mockServers[serviceName]) {
        return this.state.mockServers[serviceName].isRunning()
      }
      return false
    }
  }

  /**
   * Seed test data
   */
  async seedData(dataType, count = 1) {
    const dataSeeder = require('./DataSeeder')
    const seeder = new dataSeeder(this.state.databases)

    switch (dataType) {
      case 'users':
        return await seeder.seedUsers(count)
      case 'characters':
        return await seeder.seedCharacters(count)
      case 'guilds':
        return await seeder.seedGuilds(count)
      case 'quests':
        return await seeder.seedQuests(count)
      case 'all':
        await seeder.seedAll()
        break
      default:
        throw new Error(`Unknown data type: ${dataType}`)
    }
  }

  /**
   * Clear all test data
   */
  async clearData() {
    logger.debug('Clearing test data...')

    // Clear MongoDB collections
    if (this.state.databases.mongodb) {
      const collections = await mongoose.connection.db.collections()
      for (const collection of collections) {
        await collection.deleteMany({})
      }
    }

    // Clear PostgreSQL tables
    if (this.state.databases.postgresql) {
      const client = await this.postgresPool.connect()
      try {
        await client.query('TRUNCATE TABLE users, characters, guilds, quests RESTART IDENTITY CASCADE')
      } finally {
        client.release()
      }
    }

    // Clear Redis
    if (this.state.databases.redis) {
      await this.redisClient.flushdb()
    }

    logger.info('Test data cleared')
  }

  /**
   * Get available port for mock servers
   */
  getAvailablePort() {
    const net = require('net')

    return new Promise((resolve, reject) => {
      const server = net.createServer()
      server.listen(0, () => {
        const port = server.address().port
        server.close(() => resolve(port))
      })
      server.on('error', reject)
    })
  }

  /**
   * Get database connection
   */
  getDatabase(type) {
    return this.state.databases[type]
  }

  /**
   * Get mock server
   */
  getMockServer(serviceName) {
    return this.state.mockServers[serviceName]
  }

  /**
   * Get service health status
   */
  getServiceHealth(serviceName) {
    return this.state.healthChecks[serviceName]
  }

  /**
   * Check if environment is ready
   */
  isReady() {
    return this.state.isReady
  }

  /**
   * Wait for environment to be ready
   */
  async waitForReady(timeout = 60000) {
    if (this.state.isReady) {
      return true
    }

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error('Test environment not ready within timeout'))
      }, timeout)

      this.once('ready', () => {
        clearTimeout(timer)
        resolve(true)
      })

      this.once('error', (error) => {
        clearTimeout(timer)
        reject(error)
      })
    })
  }

  /**
   * Take snapshot of current state
   */
  async takeSnapshot() {
    const snapshot = {
      timestamp: new Date(),
      databases: {},
      services: { ...this.state.healthChecks }
    }

    // MongoDB snapshot
    if (this.state.databases.mongodb) {
      const collections = await mongoose.connection.db.collections()
      snapshot.databases.mongodb = {}

      for (const collection of collections) {
        const count = await collection.countDocuments()
        snapshot.databases.mongodb[collection.collectionName] = count
      }
    }

    // Redis snapshot
    if (this.state.databases.redis) {
      snapshot.databases.redis = await this.redisClient.dbsize()
    }

    return snapshot
  }

  /**
   * Restore from snapshot
   */
  async restoreSnapshot(snapshot) {
    // Implementation for restoring state from snapshot
    logger.info('Restoring environment from snapshot')
  }

  /**
   * Cleanup resources
   */
  async cleanup() {
    logger.info('Cleaning up test environment...')

    // Clear data
    await this.clearData()

    // Stop mock servers
    for (const [serviceName, mockServer] of Object.entries(this.state.mockServers)) {
      try {
        await mockServer.stop()
        logger.debug(`Stopped mock server for ${serviceName}`)
      } catch (error) {
        logger.warn(`Failed to stop mock server for ${serviceName}:`, error.message)
      }
    }

    // Close database connections
    if (this.state.databases.mongodb) {
      await mongoose.disconnect()
    }

    if (this.postgresPool) {
      await this.postgresPool.end()
    }

    if (this.redisClient) {
      await this.redisClient.quit()
    }

    // Stop MongoDB memory server
    if (this.mongoServer) {
      await this.mongoServer.stop()
    }

    // Execute cleanup tasks
    for (const task of this.cleanupTasks) {
      try {
        await task()
      } catch (error) {
        logger.warn('Cleanup task failed:', error.message)
      }
    }

    this.state.isReady = false
    logger.info('Test environment cleaned up')
  }

  /**
   * Add cleanup task
   */
  addCleanupTask(task) {
    this.cleanupTasks.push(task)
  }
}

module.exports = TestEnvironment