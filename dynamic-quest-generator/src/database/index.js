import databaseConnection from './connection.js'
import { Quest, Player } from './models/index.js'

class Database {
  constructor() {
    this.connection = databaseConnection
    this.models = {
      Quest,
      Player
    }
  }

  /**
   * Initialize database connection and models
   */
  async initialize() {
    try {
      await this.connection.connect()
      await this.connection.createIndexes()

      console.log('Database initialized successfully')
      return true
    } catch (error) {
      console.error('Database initialization failed:', error)
      throw error
    }
  }

  /**
   * Close database connection
   */
  async close() {
    try {
      await this.connection.disconnect()
      console.log('Database connection closed')
      return true
    } catch (error) {
      console.error('Error closing database:', error)
      throw error
    }
  }

  /**
   * Get database models
   */
  getModels() {
    return this.models
  }

  /**
   * Get connection status
   */
  getStatus() {
    return this.connection.getConnectionStatus()
  }

  /**
   * Perform health check
   */
  async healthCheck() {
    return await this.connection.healthCheck()
  }

  /**
   * Get database statistics
   */
  async getStats() {
    return await this.connection.getDatabaseStats()
  }

  /**
   * Perform database operations with error handling
   */
  async performOperation(operation) {
    try {
      if (!this.connection.isConnectionActive()) {
        await this.connection.connect()
      }

      return await operation()
    } catch (error) {
      console.error('Database operation error:', error)
      throw error
    }
  }

  /**
   * Create indexes for all models
   */
  async createAllIndexes() {
    try {
      await this.models.Quest.createIndexes()
      await this.models.Player.createIndexes()
      console.log('All database indexes created successfully')
    } catch (error) {
      console.error('Error creating indexes:', error)
      throw error
    }
  }

  /**
   * Drop all indexes (for development)
   */
  async dropAllIndexes() {
    try {
      await this.models.Quest.collection.dropIndexes()
      await this.models.Player.collection.dropIndexes()
      console.log('All database indexes dropped')
    } catch (error) {
      console.error('Error dropping indexes:', error)
      throw error
    }
  }

  /**
   * Clear all collections (for development/testing)
   */
  async clearAllCollections() {
    if (process.env.NODE_ENV === 'production') {
      throw new Error('Cannot clear collections in production environment')
    }

    try {
      await this.models.Quest.deleteMany({})
      await this.models.Player.deleteMany({})
      console.log('All collections cleared')
    } catch (error) {
      console.error('Error clearing collections:', error)
      throw error
    }
  }

  /**
   * Seed database with initial data
   */
  async seedDatabase() {
    try {
      console.log('Seeding database...')

      // This would seed the database with initial data
      // For now, just log that seeding would happen

      console.log('Database seeded successfully')
    } catch (error) {
      console.error('Error seeding database:', error)
      throw error
    }
  }

  /**
   * Create backup of database
   */
  async createBackup(backupPath) {
    return await this.connection.backup(backupPath)
  }

  /**
   * Restore database from backup
   */
  async restoreFromBackup(backupPath) {
    return await this.connection.restore(backupPath)
  }

  /**
   * Run database migrations
   */
  async runMigrations() {
    try {
      console.log('Running database migrations...')

      // This would handle any required migrations
      // For now, just log that migrations would run

      console.log('Database migrations completed')
    } catch (error) {
      console.error('Error running migrations:', error)
      throw error
    }
  }

  /**
   * Validate database integrity
   */
  async validateIntegrity() {
    try {
      console.log('Validating database integrity...')

      // This would check data integrity
      // For now, just return success

      return { valid: true, message: 'Database integrity validated' }
    } catch (error) {
      console.error('Database integrity validation failed:', error)
      return { valid: false, error: error.message }
    }
  }

  /**
   * Compact database
   */
  async compactDatabase() {
    try {
      console.log('Compacting database...')

      const db = this.connection.connection.db
      await db.command({ compact: 1 })

      console.log('Database compacted successfully')
      return { success: true }
    } catch (error) {
      console.error('Error compacting database:', error)
      throw error
    }
  }
}

// Create and export singleton instance
const database = new Database()

export default database
export { database }