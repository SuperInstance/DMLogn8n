/**
 * Mock Server for DMlogn8n Services
 *
 * Provides realistic mock implementations of all DMlogn8n services for testing:
 * - HTTP API endpoints with realistic responses
 * - WebSocket connections for real-time features
 * - Database operations with in-memory storage
 * - Authentication and authorization
 * - Error handling and edge cases
 */

const express = require('express')
const { Server } = require('socket.io')
const http = require('http')
const cors = require('cors')
const helmet = require('helmet')
const compression = require('compression')
const morgan = require('morgan')
const { EventEmitter } = require('events')
const faker = require('@faker-js/faker').faker
const { chance } = require('chance')
const logger = require('../utils/logger')

class MockServer extends EventEmitter {
  constructor(options = {}) {
    super()

    this.name = options.name || 'mock-service'
    this.port = options.port || 0
    this.protocol = options.protocol || 'http'
    this.host = options.host || 'localhost'
    this.latency = options.latency || { min: 10, max: 100 }
    this.errorRate = options.errorRate || 0.01
    this.endpoints = options.endpoints || {}

    this.app = express()
    this.server = null
    this.io = null
    this.isRunning = false

    // In-memory data storage
    this.storage = {
      users: new Map(),
      characters: new Map(),
      guilds: new Map(),
      quests: new Map(),
      sessions: new Map(),
      rooms: new Map(),
      messages: []
    }

    this.setupMiddleware()
    this.setupRoutes()
    this.setupWebSocket()
  }

  /**
   * Setup Express middleware
   */
  setupMiddleware() {
    // Security and performance middleware
    this.app.use(helmet())
    this.app.use(compression())
    this.app.use(cors({
      origin: '*',
      credentials: true
    }))

    // Logging
    this.app.use(morgan('combined', {
      stream: {
        write: (message) => logger.debug(`[${this.name}] ${message.trim()}`)
      }
    }))

    // Body parsing
    this.app.use(express.json({ limit: '10mb' }))
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }))

    // Custom middleware for latency simulation
    this.app.use((req, res, next) => {
      const delay = chance().integer({ min: this.latency.min, max: this.latency.max })
      setTimeout(() => next(), delay)
    })

    // Custom middleware for error simulation
    this.app.use((req, res, next) => {
      if (Math.random() < this.errorRate) {
        const errors = [
          { status: 500, message: 'Internal server error' },
          { status: 503, message: 'Service unavailable' },
          { status: 408, message: 'Request timeout' },
          { status: 429, message: 'Too many requests' }
        ]
        const error = chance().pickone(errors)
        return res.status(error.status).json({
          error: error.message,
          timestamp: new Date().toISOString(),
          requestId: req.id
        })
      }
      next()
    })

    // Request ID middleware
    this.app.use((req, res, next) => {
      req.id = faker.string.uuid()
      res.setHeader('X-Request-ID', req.id)
      next()
    })

    // Service-specific middleware
    this.app.use((req, res, next) => {
      req.service = this.name
      req.storage = this.storage
      next()
    })
  }

  /**
   * Setup service-specific routes
   */
  setupRoutes() {
    // Common routes for all services
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        service: this.name,
        version: '1.0.0',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        memory: process.memoryUsage()
      })
    })

    this.app.get('/info', (req, res) => {
      res.json({
        name: this.name,
        description: `Mock server for ${this.name}`,
        endpoints: Object.keys(this.endpoints),
        storage: {
          users: this.storage.users.size,
          characters: this.storage.characters.size,
          guilds: this.storage.guilds.size,
          quests: this.storage.quests.size,
          sessions: this.storage.sessions.size,
          rooms: this.storage.rooms.size,
          messages: this.storage.messages.length
        }
      })
    })

    // Service-specific routes
    this.setupServiceRoutes()

    // 404 handler
    this.app.use((req, res) => {
      res.status(404).json({
        error: 'Endpoint not found',
        path: req.path,
        method: req.method,
        service: this.name
      })
    })

    // Error handler
    this.app.use((err, req, res, next) => {
      logger.error(`[${this.name}] Error:`, err)
      res.status(500).json({
        error: 'Internal server error',
        message: err.message,
        requestId: req.id,
        timestamp: new Date().toISOString()
      })
    })
  }

  /**
   * Setup service-specific routes based on service type
   */
  setupServiceRoutes() {
    switch (this.name) {
      case 'aiDialogue':
        this.setupAIDialogueRoutes()
        break
      case 'arena':
        this.setupArenaRoutes()
        break
      case 'crafting':
        this.setupCraftingRoutes()
        break
      case 'guild':
        this.setupGuildRoutes()
        break
      case 'quest':
        this.setupQuestRoutes()
        break
      case 'voice':
        this.setupVoiceRoutes()
        break
      case 'weather':
        this.setupWeatherRoutes()
        break
      default:
        this.setupGenericRoutes()
    }
  }

  /**
   * AI Dialogue Service routes
   */
  setupAIDialogueRoutes() {
    // Emotion analysis
    this.app.post('/api/emotion/analyze', (req, res) => {
      const { text, characterId } = req.body
      const emotions = ['joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust', 'neutral']
      const emotion = chance().pickone(emotions)

      res.json({
        characterId,
        text,
        emotion,
        confidence: chance().floating({ min: 0.5, max: 1.0, fixed: 2 }),
        intensity: chance().floating({ min: 0.1, max: 1.0, fixed: 2 }),
        timestamp: new Date().toISOString()
      })
    })

    // Generate dialogue
    this.app.post('/api/conversation/generate', (req, res) => {
      const { context, characterId, mood, situation } = req.body

      setTimeout(() => {
        res.json({
          characterId,
          dialogue: faker.lorem.sentences(chance().integer({ min: 1, max: 5 })),
          emotion: chance().pickone(['happy', 'sad', 'angry', 'neutral', 'excited']),
          actions: chance().pickset(['smile', 'nod', 'gesture', 'pause', 'laugh'], chance().integer({ min: 0, max: 3 })),
          context,
          timestamp: new Date().toISOString()
        })
      }, chance().integer({ min: 500, max: 2000 }))
    })

    // Voice synthesis
    this.app.post('/api/voice/synthesize', (req, res) => {
      const { text, voiceId, emotion } = req.body

      setTimeout(() => {
        res.json({
          audioUrl: `/api/voice/audio/${faker.string.uuid()}.wav`,
          text,
          voiceId,
          emotion,
          duration: chance().integer({ min: 1000, max: 10000 }),
          sampleRate: 44100,
          timestamp: new Date().toISOString()
        })
      }, chance().integer({ min: 1000, max: 3000 }))
    })

    // Translation
    this.app.post('/api/translation/translate', (req, res) => {
      const { text, from, to } = req.body
      const languages = ['en', 'es', 'fr', 'de', 'ja', 'zh', 'ko', 'ru']

      res.json({
        originalText: text,
        translatedText: faker.lorem.sentences(chance().integer({ min: 1, max: 3 })),
        from: from || chance().pickone(languages),
        to: to || chance().pickone(languages),
        confidence: chance().floating({ min: 0.7, max: 1.0, fixed: 2 }),
        timestamp: new Date().toISOString()
      })
    })
  }

  /**
   * Multiplayer Arena Service routes
   */
  setupArenaRoutes() {
    // Matchmaking
    this.app.post('/api/matchmaking/join', (req, res) => {
      const { characterId, gameMode, preferences } = req.body
      const matchId = faker.string.uuid()

      setTimeout(() => {
        res.json({
          matchId,
          characterId,
          gameMode,
          status: 'searching',
          estimatedWaitTime: chance().integer({ min: 10, max: 120 }),
          position: chance().integer({ min: 1, max: 20 }),
          timestamp: new Date().toISOString()
        })
      }, chance().integer({ min: 5000, max: 30000 }))
    })

    // Get arena status
    this.app.get('/api/arenas/:arenaId/status', (req, res) => {
      const { arenaId } = req.params

      res.json({
        arenaId,
        status: chance().pickone(['waiting', 'in-progress', 'completed']),
        players: {
          current: chance().integer({ min: 2, max: 10 }),
          max: 10
        },
        spectators: chance().integer({ min: 0, max: 100 }),
        startTime: faker.date.recent(),
        duration: chance().integer({ min: 0, max: 3600 }),
        gameMode: chance().pickone(['deathmatch', 'capture-the-flag', 'battle-royale'])
      })
    })

    // Get rankings
    this.app.get('/api/ranking/leaderboard', (req, res) => {
      const { gameMode, limit = 50 } = req.query
      const leaderboard = []

      for (let i = 0; i < parseInt(limit); i++) {
        leaderboard.push({
          rank: i + 1,
          characterName: faker.internet.userName(),
          rating: chance().integer({ min: 800, max: 3000 }),
          wins: chance().integer({ min: 0, max: 1000 }),
          losses: chance().integer({ min: 0, max: 500 }),
          winRate: chance().floating({ min: 0.3, max: 0.9, fixed: 3 }),
          streak: chance().integer({ min: -10, max: 20 })
        })
      }

      res.json({
        gameMode,
        leaderboard,
        lastUpdated: new Date().toISOString()
      })
    })

    // Spectator stream
    this.app.get('/api/spectators/stream/:matchId', (req, res) => {
      const { matchId } = req.params

      res.json({
        matchId,
        streamUrl: `ws://localhost:${this.port}/spectator/${matchId}`,
        viewerCount: chance().integer({ min: 0, max: 1000 }),
        isLive: chance().bool(),
        commentary: {
          enabled: chance().bool(),
          language: chance().pickone(['en', 'es', 'fr', 'de'])
        }
      })
    })
  }

  /**
   * Crafting Service routes
   */
  setupCraftingRoutes() {
    // Get recipes
    this.app.get('/api/recipes', (req, res) => {
      const { profession, level } = req.query
      const recipes = []

      for (let i = 0; i < 20; i++) {
        recipes.push({
          id: faker.string.uuid(),
          name: `${chance().pickone(['Master', 'Expert', 'Apprentice'])} ${faker.word.adjective()} ${faker.word.noun()}`,
          profession: profession || chance().pickone(['blacksmithing', 'alchemy', 'enchanting', 'tailoring']),
          level: level || chance().integer({ min: 1, max: 20 }),
          difficulty: chance().pickone(['easy', 'medium', 'hard', 'expert']),
          materials: this.generateMaterials(),
          results: this.generateCraftingResults(),
          skillGain: chance().integer({ min: 1, max: 5 }),
          craftTime: chance().integer({ min: 1, max: 60 })
        })
      }

      res.json({ recipes })
    })

    // Craft item
    this.app.post('/api/crafting/craft', (req, res) => {
      const { recipeId, characterId, materials, quantity = 1 } = req.body

      setTimeout(() => {
        const success = chance().bool({ likelihood: 80 })
        const quality = success ? chance().pickone(['common', 'uncommon', 'rare', 'epic']) : 'failed'

        res.json({
          characterId,
          recipeId,
          quantity,
          success,
          quality,
          experience: success ? chance().integer({ min: 10, max: 100 }) : 5,
          items: success ? this.generateCraftingResults() : [],
          materials: materials,
          duration: chance().integer({ min: 1000, max: 10000 }),
          timestamp: new Date().toISOString()
        })
      }, chance().integer({ min: 1000, max: 5000 }))
    })

    // Get materials
    this.app.get('/api/materials', (req, res) => {
      const materials = this.generateMaterials()
      res.json({ materials })
    })
  }

  /**
   * Guild Management Service routes
   */
  setupGuildRoutes() {
    // Get guilds
    this.app.get('/api/guilds', (req, res) => {
      const guilds = []

      for (let i = 0; i < 10; i++) {
        guilds.push({
          id: faker.string.uuid(),
          name: `${faker.word.adjective()} ${faker.word.noun()}`,
          tag: faker.string.alphanumeric({ length: 5 }).toUpperCase(),
          description: faker.lorem.paragraph(),
          memberCount: chance().integer({ min: 5, max: 500 }),
          level: chance().integer({ min: 1, max: 25 }),
          faction: chance().pickone(['alliance', 'horde', 'neutral']),
          recruitmentOpen: chance().bool(),
          createdAt: faker.date.past({ years: 2 })
        })
      }

      res.json({ guilds })
    })

    // Create guild
    this.app.post('/api/guilds', (req, res) => {
      const { name, tag, description } = req.body

      const guild = {
        id: faker.string.uuid(),
        name,
        tag,
        description,
        leader: req.body.characterId,
        members: 1,
        level: 1,
        experience: 0,
        bank: {
          gold: chance().integer({ min: 1000, max: 10000 })
        },
        createdAt: new Date().toISOString()
      }

      this.storage.guilds.set(guild.id, guild)
      res.status(201).json(guild)
    })

    // Guild bank
    this.app.get('/api/guilds/:guildId/bank', (req, res) => {
      const { guildId } = req.params

      res.json({
        guildId,
        gold: chance().integer({ min: 5000, max: 500000 }),
        items: this.generateLoot(chance().integer({ min: 10, max: 100 })),
        transactions: this.generateBankTransactions(),
        lastActivity: faker.date.recent()
      })
    })
  }

  /**
   * Quest Generator Service routes
   */
  setupQuestRoutes() {
    // Generate quest
    this.app.post('/api/generation/generate', (req, res) => {
      const { characterLevel, preferences, location } = req.body

      setTimeout(() => {
        const quest = {
          id: faker.string.uuid(),
          title: `The ${faker.word.adjective()} ${faker.word.noun()}`,
          description: faker.lorem.paragraphs(2),
          level: characterLevel || chance().integer({ min: 1, max: 20 }),
          type: chance().pickone(['kill', 'fetch', 'explore', 'escort', 'deliver']),
          objectives: this.generateQuestObjectives(),
          rewards: {
            gold: chance().integer({ min: 100, max: 5000 }),
            experience: chance().integer({ min: 50, max: 2000 }),
            items: this.generateLoot(chance().integer({ min: 0, max: 3 }))
          },
          location: location || faker.location.city(),
          estimatedTime: chance().integer({ min: 15, max: 180 }),
          difficulty: chance().pickone(['easy', 'medium', 'hard', 'epic']),
          generatedAt: new Date().toISOString()
        }

        res.json(quest)
      }, chance().integer({ min: 1000, max: 3000 }))
    })

    // Get available quests
    this.app.get('/api/quests/available', (req, res) => {
      const { characterId, level } = req.query
      const quests = []

      for (let i = 0; i < 15; i++) {
        quests.push({
          id: faker.string.uuid(),
          title: faker.lorem.sentence(),
          level: level || chance().integer({ min: 1, max: 20 }),
          type: chance().pickone(['kill', 'fetch', 'explore', 'escort', 'deliver']),
          description: faker.lorem.paragraph(),
          rewards: {
            gold: chance().integer({ min: 100, max: 5000 }),
            experience: chance().integer({ min: 50, max: 2000 })
          },
          timeLimit: chance().integer({ min: 0, max: 7 * 24 }),
          repeatable: chance().bool()
        })
      }

      res.json({ quests })
    })
  }

  /**
   * Voice Synthesis Service routes
   */
  setupVoiceRoutes() {
    // Get available voices
    this.app.get('/api/voices', (req, res) => {
      const voices = []

      for (let i = 0; i < 20; i++) {
        voices.push({
          id: faker.string.uuid(),
          name: faker.person.fullName(),
          gender: chance().pickone(['male', 'female', 'neutral']),
          age: chance().pickone(['young', 'adult', 'mature', 'elderly']),
          accent: chance().pickone(['american', 'british', 'australian', 'none']),
          language: chance().pickone(['en-US', 'en-GB', 'es-ES', 'fr-FR', 'de-DE']),
          style: chance().pickone(['narrative', 'conversational', 'dramatic', 'casual'])
        })
      }

      res.json({ voices })
    })

    // Clone voice
    this.app.post('/api/cloning/clone', (req, res) => {
      const { audioFile, name } = req.body

      setTimeout(() => {
        res.json({
          voiceId: faker.string.uuid(),
          name,
          status: 'completed',
          quality: chance().pickone(['low', 'medium', 'high']),
          samples: chance().integer({ min: 5, max: 20 }),
          processingTime: chance().integer({ min: 30000, max: 300000 }),
          createdAt: new Date().toISOString()
        })
      }, chance().integer({ min: 30000, max: 120000 }))
    })
  }

  /**
   * Weather System Service routes
   */
  setupWeatherRoutes() {
    // Get current weather
    this.app.get('/api/weather/current/:location', (req, res) => {
      const { location } = req.params

      res.json({
        location,
        current: {
          temperature: chance().integer({ min: -20, max: 45 }),
          humidity: chance().integer({ min: 0, max: 100 }),
          windSpeed: chance().integer({ min: 0, max: 100 }),
          windDirection: chance().pickone(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']),
          precipitation: chance().integer({ min: 0, max: 100 }),
          visibility: chance().integer({ min: 1, max: 10 }),
          condition: chance().pickone(['clear', 'cloudy', 'rainy', 'stormy', 'snowy', 'foggy']),
          magicalEffects: chance().pickset(['arcane-storm', 'divine-blessing', 'planar-ripple', 'wild-magic'], chance().integer({ min: 0, max: 2 }))
        },
        lastUpdated: new Date().toISOString()
      })
    })

    // Get forecast
    this.app.get('/api/weather/forecast/:location', (req, res) => {
      const { location, days = 7 } = req.params
      const forecast = []

      for (let i = 0; i < parseInt(days); i++) {
        forecast.push({
          date: faker.date.future({ days: i + 1 }),
          high: chance().integer({ min: 10, max: 40 }),
          low: chance().integer({ min: -10, max: 25 }),
          condition: chance().pickone(['sunny', 'partly-cloudy', 'cloudy', 'rainy', 'stormy', 'snowy']),
          precipitation: chance().integer({ min: 0, max: 100 }),
          magicalEvents: chance().pickset(['meteor-shower', 'aurora', 'magical-fog', 'elemental-eruption'], chance().integer({ min: 0, max: 1 }))
        })
      }

      res.json({ location, forecast })
    })
  }

  /**
   * Generic routes for unknown services
   */
  setupGenericRoutes() {
    this.app.get('/api/status', (req, res) => {
      res.json({
        service: this.name,
        status: 'running',
        timestamp: new Date().toISOString()
      })
    })

    this.app.post('/api/process', (req, res) => {
      setTimeout(() => {
        res.json({
          processed: true,
          data: req.body,
          result: faker.lorem.words(5),
          timestamp: new Date().toISOString()
        })
      }, chance().integer({ min: 100, max: 1000 }))
    })
  }

  /**
   * Setup WebSocket functionality
   */
  setupWebSocket() {
    // Will be initialized when server starts
  }

  /**
   * Start the mock server
   */
  async start() {
    if (this.isRunning) {
      throw new Error(`Mock server ${this.name} is already running`)
    }

    return new Promise((resolve, reject) => {
      this.server = http.createServer(this.app)

      this.server.listen(this.port, this.host, (err) => {
        if (err) {
          return reject(err)
        }

        this.port = this.server.address().port
        this.isRunning = true

        // Initialize WebSocket
        this.io = new Server(this.server, {
          cors: {
            origin: '*',
            methods: ['GET', 'POST']
          }
        })

        this.setupWebSocketHandlers()

        logger.info(`Mock server ${this.name} started on ${this.protocol}://${this.host}:${this.port}`)
        this.emit('started', { port: this.port })
        resolve({ port: this.port })
      })
    })
  }

  /**
   * Setup WebSocket handlers
   */
  setupWebSocketHandlers() {
    this.io.on('connection', (socket) => {
      logger.debug(`[${this.name}] WebSocket client connected: ${socket.id}`)

      // Handle service-specific events
      this.handleWebSocketEvents(socket)

      // Generic handlers
      socket.on('ping', () => {
        socket.emit('pong', { timestamp: Date.now() })
      })

      socket.on('disconnect', () => {
        logger.debug(`[${this.name}] WebSocket client disconnected: ${socket.id}`)
      })
    })
  }

  /**
   * Handle service-specific WebSocket events
   */
  handleWebSocketEvents(socket) {
    switch (this.name) {
      case 'arena':
        this.setupArenaWebSocket(socket)
        break
      case 'aiDialogue':
        this.setupAIDialogueWebSocket(socket)
        break
      default:
        this.setupGenericWebSocket(socket)
    }
  }

  /**
   * Arena WebSocket handlers
   */
  setupArenaWebSocket(socket) {
    socket.on('join-match', (data) => {
      socket.join(`match-${data.matchId}`)
      socket.emit('match-joined', { matchId: data.matchId })
    })

    socket.on('leave-match', (data) => {
      socket.leave(`match-${data.matchId}`)
      socket.emit('match-left', { matchId: data.matchId })
    })

    // Simulate match events
    const matchEvents = setInterval(() => {
      if (socket.rooms.size > 1) {
        socket.emit('match-update', {
          type: chance().pickone(['score', 'elimination', 'power-up', 'zone-shrink']),
          data: faker.helpers.createCard()
        })
      }
    }, 5000)

    socket.on('disconnect', () => clearInterval(matchEvents))
  }

  /**
   * AI Dialogue WebSocket handlers
   */
  setupAIDialogueWebSocket(socket) {
    socket.on('start-conversation', (data) => {
      socket.emit('conversation-started', {
        conversationId: faker.string.uuid(),
        participants: data.participants
      })
    })

    socket.on('send-message', (data) => {
      setTimeout(() => {
        socket.emit('message-received', {
          id: faker.string.uuid(),
          speaker: data.characterId,
          text: faker.lorem.sentences(chance().integer({ min: 1, max: 3 })),
          emotion: chance().pickone(['happy', 'sad', 'angry', 'neutral']),
          timestamp: new Date().toISOString()
        })
      }, chance().integer({ min: 1000, max: 3000 }))
    })
  }

  /**
   * Generic WebSocket handlers
   */
  setupGenericWebSocket(socket) {
    socket.on('subscribe', (data) => {
      socket.join(data.channel)
      socket.emit('subscribed', { channel: data.channel })
    })

    socket.on('unsubscribe', (data) => {
      socket.leave(data.channel)
      socket.emit('unsubscribed', { channel: data.channel })
    })
  }

  /**
   * Stop the mock server
   */
  async stop() {
    if (!this.isRunning) {
      return
    }

    return new Promise((resolve) => {
      if (this.io) {
        this.io.close()
      }

      this.server.close(() => {
        this.isRunning = false
        logger.info(`Mock server ${this.name} stopped`)
        this.emit('stopped')
        resolve()
      })
    })
  }

  /**
   * Helper methods for generating mock data
   */
  generateMaterials() {
    const materials = []
    const count = chance().integer({ min: 1, max: 5 })

    for (let i = 0; i < count; i++) {
      materials.push({
        id: faker.string.uuid(),
        name: faker.word.adjective() + ' ' + faker.word.noun(),
        quantity: chance().integer({ min: 1, max: 10 }),
        quality: chance().pickone(['common', 'uncommon', 'rare', 'epic', 'legendary'])
      })
    }

    return materials
  }

  generateCraftingResults() {
    const results = []
    const count = chance().integer({ min: 1, max: 3 })

    for (let i = 0; i < count; i++) {
      results.push({
        id: faker.string.uuid(),
        name: faker.word.adjective() + ' ' + faker.word.noun(),
        quantity: chance().integer({ min: 1, max: 5 }),
        quality: chance().pickone(['common', 'uncommon', 'rare', 'epic']),
        stats: this.generateItemStats()
      })
    }

    return results
  }

  generateItemStats() {
    const stats = {}
    const statCount = chance().integer({ min: 1, max: 4 })

    for (let i = 0; i < statCount; i++) {
      const stat = chance().pickone(['power', 'defense', 'speed', 'health', 'mana'])
      stats[stat] = chance().integer({ min: 1, max: 50 })
    }

    return stats
  }

  generateLoot(count) {
    const loot = []

    for (let i = 0; i < count; i++) {
      loot.push({
        id: faker.string.uuid(),
        name: faker.word.adjective() + ' ' + faker.word.noun(),
        type: chance().pickone(['weapon', 'armor', 'consumable', 'material']),
        rarity: chance().pickone(['common', 'uncommon', 'rare', 'epic', 'legendary']),
        value: chance().integer({ min: 10, max: 10000 })
      })
    }

    return loot
  }

  generateBankTransactions() {
    const transactions = []

    for (let i = 0; i < 10; i++) {
      transactions.push({
        id: faker.string.uuid(),
        type: chance().pickone(['deposit', 'withdrawal']),
        amount: chance().integer({ min: 10, max: 10000 }),
        description: faker.lorem.sentence(),
        timestamp: faker.date.recent(),
        characterName: faker.internet.userName()
      })
    }

    return transactions
  }

  generateQuestObjectives() {
    const objectives = []
    const count = chance().integer({ min: 1, max: 4 })

    for (let i = 0; i < count; i++) {
      objectives.push({
        type: chance().pickone(['kill', 'collect', 'explore', 'escort']),
        target: faker.word.noun(),
        current: 0,
        required: chance().integer({ min: 1, max: 10 })
      })
    }

    return objectives
  }
}

module.exports = MockServer