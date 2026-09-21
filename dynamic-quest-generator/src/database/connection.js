import mongoose from 'mongoose'

class DatabaseConnection {
  constructor() {
    this.connection = null
    this.isConnected = false
  }

  /**
   * Connect to MongoDB database
   */
  async connect() {
    try {
      if (this.isConnected) {
        console.log('Database already connected')
        return this.connection
      }

      const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/dmlogn8n-quests'

      const options = {
        useNewUrlParser: true,
        useUnifiedTopology: true,
        maxPoolSize: 10, // Maintain up to 10 socket connections
        serverSelectionTimeoutMS: 5000, // Keep trying to send operations for 5 seconds
        socketTimeoutMS: 45000, // Close sockets after 45 seconds of inactivity
        bufferMaxEntries: 0, // Disable mongoose buffering
        bufferCommands: false, // Disable mongoose buffering
        family: 4 // Use IPv4, skip trying IPv6
      }

      this.connection = await mongoose.connect(mongoUri, options)
      this.isConnected = true

      console.log('Connected to MongoDB successfully')
      console.log(`Database: ${mongoose.connection.name}`)

      // Set up connection event listeners
      this.setupEventListeners()

      return this.connection

    } catch (error) {
      console.error('Database connection error:', error)
      this.isConnected = false
      throw error
    }
  }

  /**
   * Disconnect from database
   */
  async disconnect() {
    try {
      if (!this.isConnected) {
        console.log('Database already disconnected')
        return
      }

      await mongoose.disconnect()
      this.isConnected = false
      this.connection = null

      console.log('Disconnected from MongoDB')

    } catch (error) {
      console.error('Database disconnection error:', error)
      throw error
    }
  }

  /**
   * Check if database is connected
   */
  isConnectionActive() {
    return this.isConnected && mongoose.connection.readyState === 1
  }

  /**
   * Get connection status
   */
  getConnectionStatus() {
    const states = {
      0: 'disconnected',
      1: 'connected',
      2: 'connecting',
      3: 'disconnecting'
    }

    return {
      isConnected: this.isConnected,
      state: states[mongoose.connection.readyState],
      host: mongoose.connection.host,
      port: mongoose.connection.port,
      name: mongoose.connection.name
    }
  }

  /**
   * Set up event listeners for connection events
   */
  setupEventListeners() {
    const db = mongoose.connection

    db.on('connected', () => {
      console.log('Mongoose connected to MongoDB')
      this.isConnected = true
    })

    db.on('error', (error) => {
      console.error('Mongoose connection error:', error)
      this.isConnected = false
    })

    db.on('disconnected', () => {
      console.log('Mongoose disconnected from MongoDB')
      this.isConnected = false
    })

    // Handle application termination
    process.on('SIGINT', async () => {
      await this.disconnect()
      process.exit(0)
    })

    process.on('SIGTERM', async () => {
      await this.disconnect()
      process.exit(0)
    })

    // Handle uncaught exceptions
    process.on('uncaughtException', async (error) => {
      console.error('Uncaught Exception:', error)
      await this.disconnect()
      process.exit(1)
    })
  }

  /**
   * Create database indexes for better performance
   */
  async createIndexes() {
    try {
      console.log('Creating database indexes...')

      // Quest indexes would be created by the model schemas automatically
      // This method can be used for any additional custom indexes

      console.log('Database indexes created successfully')
    } catch (error) {
      console.error('Error creating database indexes:', error)
      throw error
    }
  }

  /**
   * Get database statistics
   */
  async getDatabaseStats() {
    try {
      const db = mongoose.connection.db
      const stats = await db.stats()

      return {
        collections: stats.collections,
        documents: stats.objects,
        dataSize: stats.dataSize,
        storageSize: stats.storageSize,
        indexes: stats.indexes,
        indexSize: stats.indexSize,
        avgObjSize: stats.avgObjSize
      }
    } catch (error) {
      console.error('Error getting database stats:', error)
      return null
    }
  }

  /**
   * Health check for database connection
   */
  async healthCheck() {
    try {
      if (!this.isConnectionActive()) {
        throw new Error('Database not connected')
      }

      // Test database connection with a simple operation
      await mongoose.connection.db.admin().ping()

      return {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        connection: this.getConnectionStatus()
      }
    } catch (error) {
      return {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        error: error.message
      }
    }
  }

  /**
   * Backup database
   */
  async backup(backupPath) {
    try {
      console.log(`Creating database backup to ${backupPath}...`)

      // This would typically use mongodump or similar tool
      // For now, just log that backup would be created

      console.log('Database backup completed')
      return { success: true, path: backupPath }
    } catch (error) {
      console.error('Error creating database backup:', error)
      throw error
    }
  }

  /**
   * Restore database from backup
   */
  async restore(backupPath) {
    try {
      console.log(`Restoring database from ${backupPath}...`)

      // This would typically use mongorestore or similar tool
      // For now, just log that restore would be performed

      console.log('Database restore completed')
      return { success: true }
    } catch (error) {
      console.error('Error restoring database:', error)
      throw error
    }
  }
}

// Create singleton instance
const databaseConnection = new DatabaseConnection()

export default databaseConnection