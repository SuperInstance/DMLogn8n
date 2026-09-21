import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import compression from 'compression'
import morgan from 'morgan'
import dotenv from 'dotenv'
import database from '../database/index.js'
import questRoutes from './questRoutes.js'
import playerRoutes from './playerRoutes.js'

// Load environment variables
dotenv.config()

const app = express()
const PORT = process.env.PORT || 3001

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  crossOriginEmbedderPolicy: false
}))

// CORS configuration
const corsOptions = {
  origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}

app.use(cors(corsOptions))

// General middleware
app.use(compression())
app.use(express.json({ limit: '10mb' }))
app.use(express.urlencoded({ extended: true, limit: '10mb' }))

// Logging middleware
if (process.env.NODE_ENV !== 'test') {
  app.use(morgan('combined'))
} else {
  app.use(morgan('dev'))
}

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    const dbHealth = await database.healthCheck()

    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
      database: dbHealth,
      uptime: process.uptime()
    })
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error.message
    })
  }
})

// API routes
app.use('/api/quests', questRoutes)
app.use('/api/players', playerRoutes)

// API documentation endpoint
app.get('/api', (req, res) => {
  res.json({
    name: 'Dynamic Quest Generator API',
    version: '1.0.0',
    description: 'AI-driven dynamic quest generation system for DMlogn8n',
    endpoints: {
      quests: {
        base: '/api/quests',
        methods: ['GET', 'POST', 'PUT', 'DELETE'],
        description: 'Quest management operations'
      },
      players: {
        base: '/api/players',
        methods: ['GET', 'POST', 'PUT', 'DELETE'],
        description: 'Player management operations'
      },
      health: {
        base: '/health',
        methods: ['GET'],
        description: 'API health check'
      }
    },
    documentation: '/api/docs',
    version: '1.0.0'
  })
})

// API info endpoint
app.get('/api/info', (req, res) => {
  res.json({
    name: 'Dynamic Quest Generator API',
    version: process.env.npm_package_version || '1.0.0',
    environment: process.env.NODE_ENV || 'development',
    nodeVersion: process.version,
    platform: process.platform,
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    features: {
      aiGeneration: process.env.OPENAI_API_KEY ? 'enabled' : 'disabled',
      n8nIntegration: process.env.N8N_WEBHOOK_URL ? 'enabled' : 'disabled',
      database: database.isConnectionActive() ? 'connected' : 'disconnected'
    }
  })
})

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    message: 'Route not found',
    path: req.originalUrl,
    method: req.method,
    availableEndpoints: [
      '/health',
      '/api',
      '/api/info',
      '/api/quests',
      '/api/players'
    ]
  })
})

// Global error handler
app.use((error, req, res, next) => {
  console.error('Global error handler:', error)

  // Don't leak error details in production
  const message = process.env.NODE_ENV === 'production'
    ? 'Internal server error'
    : error.message

  res.status(error.status || 500).json({
    success: false,
    message,
    error: process.env.NODE_ENV === 'development' ? error.stack : undefined,
    timestamp: new Date().toISOString(),
    path: req.path,
    method: req.method
  })
})

// Graceful shutdown handling
const gracefulShutdown = async (signal) => {
  console.log(`\nReceived ${signal}. Starting graceful shutdown...`)

  try {
    // Close database connection
    await database.close()
    console.log('Database connection closed')

    // Close server
    server.close(() => {
      console.log('Server closed')
      process.exit(0)
    })

    // Force close after 10 seconds
    setTimeout(() => {
      console.error('Could not close connections in time, forcefully shutting down')
      process.exit(1)
    }, 10000)

  } catch (error) {
    console.error('Error during graceful shutdown:', error)
    process.exit(1)
  }
}

// Start server
const startServer = async () => {
  try {
    // Initialize database
    await database.initialize()

    // Start HTTP server
    const server = app.listen(PORT, () => {
      console.log(`🚀 Dynamic Quest Generator API running on port ${PORT}`)
      console.log(`📚 API Documentation: http://localhost:${PORT}/api`)
      console.log(`🏥 Health Check: http://localhost:${PORT}/health`)
      console.log(`📊 API Info: http://localhost:${PORT}/api/info`)
      console.log(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`)

      if (process.env.NODE_ENV === 'development') {
        console.log('\n📋 Available Endpoints:')
        console.log('  GET  /health                          - Health check')
        console.log('  GET  /api                             - API overview')
        console.log('  GET  /api/info                        - API information')
        console.log('  GET  /api/quests                      - List quests')
        console.log('  POST /api/quests/generate             - Generate quest')
        console.log('  GET  /api/players                     - List players')
        console.log('  POST /api/players                     - Create player')
        console.log('  GET  /api/players/:id/quests/recommendations - Get recommendations')
      }
    })

    // Set server timeout
    server.timeout = 30000 // 30 seconds

    // Handle graceful shutdown
    process.on('SIGTERM', () => gracefulShutdown('SIGTERM'))
    process.on('SIGINT', () => gracefulShutdown('SIGINT'))

    // Handle uncaught exceptions
    process.on('uncaughtException', (error) => {
      console.error('Uncaught Exception:', error)
      gracefulShutdown('uncaughtException')
    })

    // Handle unhandled promise rejections
    process.on('unhandledRejection', (reason, promise) => {
      console.error('Unhandled Rejection at:', promise, 'reason:', reason)
      gracefulShutdown('unhandledRejection')
    })

    return server

  } catch (error) {
    console.error('Failed to start server:', error)
    process.exit(1)
  }
}

// Start server if this file is run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  startServer()
}

export { app, startServer }
export default app