/**
 * Comprehensive Test Configuration for DMlogn8n Integration Testing
 *
 * This configuration file manages all test environments, service endpoints,
 * timeouts, and testing parameters for the integration testing suite.
 */

const path = require('path')
const os = require('os')

// Base configuration
const baseConfig = {
  // Test environment settings
  environment: process.env.TEST_ENV || 'development',

  // Service ports and endpoints
  services: {
    // Core DMlogn8n services
    n8n: {
      port: process.env.N8N_PORT || 5678,
      host: process.env.N8N_HOST || 'localhost',
      protocol: 'http',
      basePath: '/rest',
      webhookBase: '/webhook'
    },

    // AI Dialogue System
    aiDialogue: {
      port: process.env.AI_DIALOGUE_PORT || 3001,
      host: process.env.AI_DIALOGUE_HOST || 'localhost',
      protocol: 'http',
      endpoints: {
        emotion: '/api/emotion',
        conversation: '/api/conversation',
        voice: '/api/voice',
        translation: '/api/translation'
      }
    },

    // Multiplayer Arena
    arena: {
      port: process.env.ARENA_PORT || 3002,
      host: process.env.ARENA_HOST || 'localhost',
      protocol: 'http',
      websocketPort: process.env.ARENA_WS_PORT || 3003,
      endpoints: {
        matchmaking: '/api/matchmaking',
        arenas: '/api/arenas',
        ranking: '/api/ranking',
        spectators: '/api/spectators'
      }
    },

    // Advanced Crafting
    crafting: {
      port: process.env.CRAFTING_PORT || 3004,
      host: process.env.CRAFTING_HOST || 'localhost',
      protocol: 'http',
      endpoints: {
        recipes: '/api/recipes',
        materials: '/api/materials',
        professions: '/api/professions',
        crafting: '/api/crafting'
      }
    },

    // Guild Management
    guild: {
      port: process.env.GUILD_PORT || 3005,
      host: process.env.GUILD_HOST || 'localhost',
      protocol: 'http',
      endpoints: {
        guilds: '/api/guilds',
        alliances: '/api/alliances',
        events: '/api/events',
        banks: '/api/banks'
      }
    },

    // Quest Generator
    quest: {
      port: process.env.QUEST_PORT || 3006,
      host: process.env.QUEST_HOST || 'localhost',
      protocol: 'http',
      endpoints: {
        quests: '/api/quests',
        generation: '/api/generation',
        templates: '/api/templates',
        progress: '/api/progress'
      }
    },

    // Voice Synthesis
    voice: {
      port: process.env.VOICE_PORT || 3007,
      host: process.env.VOICE_HOST || 'localhost',
      protocol: 'http',
      endpoints: {
        synthesis: '/api/synthesis',
        cloning: '/api/cloning',
        emotions: '/api/emotions',
        languages: '/api/languages'
      }
    },

    // Weather System
    weather: {
      port: process.env.WEATHER_PORT || 3008,
      host: process.env.WEATHER_HOST || 'localhost',
      protocol: 'http',
      endpoints: {
        current: '/api/weather/current',
        forecast: '/api/weather/forecast',
        simulation: '/api/weather/simulation'
      }
    }
  },

  // Database configurations
  databases: {
    mongodb: {
      host: process.env.MONGO_HOST || 'localhost',
      port: process.env.MONGO_PORT || 27017,
      database: process.env.MONGO_TEST_DB || 'dmlogn8n_test',
      options: {
        useNewUrlParser: true,
        useUnifiedTopology: true,
        connectTimeoutMS: 10000,
        socketTimeoutMS: 45000,
        serverSelectionTimeoutMS: 30000
      }
    },

    postgresql: {
      host: process.env.PG_HOST || 'localhost',
      port: process.env.PG_PORT || 5432,
      database: process.env.PG_TEST_DB || 'dmlogn8n_test',
      username: process.env.PG_USER || 'test_user',
      password: process.env.PG_PASSWORD || 'test_password',
      options: {
        max: 20,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 2000
      }
    },

    redis: {
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379,
      db: process.env.REDIS_TEST_DB || 1,
      password: process.env.REDIS_PASSWORD || null,
      options: {
        connectTimeout: 10000,
        lazyConnect: true,
        maxRetriesPerRequest: 3
      }
    }
  },

  // Testing timeouts and limits
  timeouts: {
    default: 10000,
    api: 30000,
    websocket: 60000,
    database: 15000,
    fileOperations: 20000,
    aiProcessing: 120000,
    performance: 300000,
    e2e: 600000,
    scenario: 900000
  },

  // Performance testing parameters
  performance: {
    // Load testing
    loadTesting: {
      duration: 60, // seconds
      rampUp: 10, // seconds
      concurrentUsers: [10, 50, 100, 500, 1000],
      requestsPerSecond: [10, 50, 100, 500],

      // Response time thresholds (ms)
      thresholds: {
        p50: 200,
        p90: 500,
        p95: 1000,
        p99: 2000,
        max: 5000
      },

      // Error rate thresholds
      errorRate: {
        warning: 0.01, // 1%
        critical: 0.05  // 5%
      }
    },

    // WebSocket testing
    websocket: {
      maxConnections: 10000,
      messageRate: 100, // messages per second
      latencyThreshold: 100, // ms
      connectionTimeout: 5000 // ms
    },

    // Memory usage
    memory: {
      warningThreshold: 512 * 1024 * 1024, // 512MB
      criticalThreshold: 1024 * 1024 * 1024, // 1GB
      samplingInterval: 5000 // ms
    },

    // CPU usage
    cpu: {
      warningThreshold: 70, // percentage
      criticalThreshold: 90, // percentage
      samplingInterval: 5000 // ms
    }
  },

  // Test data generation
  testData: {
    // User generation
    users: {
      count: {
        small: 10,
        medium: 100,
        large: 1000,
        stress: 10000
      },
      types: ['player', 'dm', 'admin', 'spectator'],
      levels: [1, 5, 10, 15, 20]
    },

    // Character generation
    characters: {
      races: ['human', 'elf', 'dwarf', 'halfling', 'dragonborn', 'tiefling'],
      classes: ['fighter', 'wizard', 'cleric', 'rogue', 'ranger', 'paladin'],
      backgrounds: ['soldier', 'scholar', 'merchant', 'noble', 'folk-hero'],
      alignments: ['lawful-good', 'neutral-good', 'chaotic-good', 'lawful-neutral', 'true-neutral', 'chaotic-neutral', 'lawful-evil', 'neutral-evil', 'chaotic-evil']
    },

    // Guild generation
    guilds: {
      types: ['adventuring', 'crafting', 'social', 'military', 'scholarly'],
      sizes: {
        small: { min: 5, max: 20 },
        medium: { min: 21, max: 100 },
        large: { min: 101, max: 500 }
      }
    },

    // Quest generation
    quests: {
      types: ['kill', 'fetch', 'explore', 'escort', 'deliver', 'puzzle', 'social'],
      difficulties: ['trivial', 'easy', 'medium', 'hard', 'deadly', 'legendary'],
      rewards: {
        gold: { min: 10, max: 10000 },
        xp: { min: 50, max: 5000 },
        items: { min: 1, max: 5 }
      }
    }
  },

  // File paths and directories
  paths: {
    root: path.resolve(__dirname, '..'),
    src: path.resolve(__dirname, '..', 'src'),
    tests: path.resolve(__dirname, '..', 'tests'),
    fixtures: path.resolve(__dirname, '..', 'data', 'fixtures'),
    reports: path.resolve(__dirname, '..', 'reports'),
    coverage: path.resolve(__dirname, '..', 'coverage'),
    logs: path.resolve(__dirname, '..', 'logs'),
    temp: path.resolve(__dirname, '..', 'temp'),
    artifacts: path.resolve(__dirname, '..', 'artifacts')
  },

  // Logging configuration
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    format: 'combined',
    transports: {
      console: {
        enabled: true,
        colorize: true
      },
      file: {
        enabled: true,
        filename: 'test.log',
        maxSize: '10MB',
        maxFiles: 5
      }
    },
    categories: {
      test: { level: 'info' },
      performance: { level: 'debug' },
      database: { level: 'warn' },
      network: { level: 'error' }
    }
  },

  // Mock server configuration
  mockServers: {
    enabled: process.env.ENABLE_MOCK_SERVERS !== 'false',
    autoStart: process.env.AUTO_START_MOCKS !== 'false',
    ports: {
      start: 4000,
      end: 4100
    },
    latency: {
      min: 10,
      max: 500
    },
    errorRate: 0.01 // 1% random errors
  },

  // Reporting configuration
  reporting: {
    formats: ['html', 'json', 'junit', 'csv'],
    includeScreenshots: true,
    includeVideos: process.env.CI === 'true',
    includeNetworkLogs: true,
    includeConsoleLogs: true,
    retention: {
      days: 30,
      maxSize: '1GB'
    }
  },

  // CI/CD integration
  ci: {
    enabled: process.env.CI === 'true',
    parallel: process.env.CI_PARALLEL === 'true',
    shardCount: parseInt(process.env.CI_SHARD_COUNT) || 4,
    shardIndex: parseInt(process.env.CI_SHARD_INDEX) || 0,
    artifacts: {
      upload: true,
      paths: ['coverage', 'reports', 'artifacts']
    }
  },

  // Feature flags
  features: {
    e2eTests: process.env.ENABLE_E2E !== 'false',
    performanceTests: process.env.ENABLE_PERFORMANCE !== 'false',
    scenarioTests: process.env.ENABLE_SCENARIOS !== 'false',
    integrationTests: process.env.ENABLE_INTEGRATION !== 'false',
    visualTesting: process.env.ENABLE_VISUAL === 'true',
    accessibilityTesting: process.env.ENABLE_A11Y === 'true',
    securityTesting: process.env.ENABLE_SECURITY === 'true'
  },

  // System resources
  system: {
    maxCores: os.cpus().length,
    totalMemory: os.totalmem(),
    freeMemory: os.freemem(),
    platform: os.platform(),
    arch: os.arch()
  }
}

// Environment-specific overrides
const environmentConfigs = {
  development: {
    logging: {
      level: 'debug'
    },
    mockServers: {
      enabled: true,
      autoStart: true
    },
    timeouts: {
      default: 5000,
      aiProcessing: 60000
    }
  },

  test: {
    logging: {
      level: 'warn'
    },
    mockServers: {
      enabled: true,
      autoStart: true
    },
    reporting: {
      formats: ['json', 'junit']
    }
  },

  staging: {
    logging: {
      level: 'info'
    },
    mockServers: {
      enabled: false,
      autoStart: false
    },
    timeouts: {
      default: 15000,
      api: 45000
    }
  },

  production: {
    logging: {
      level: 'error'
    },
    mockServers: {
      enabled: false,
      autoStart: false
    },
    timeouts: {
      default: 30000,
      api: 60000
    },
    features: {
      e2eTests: false,
      performanceTests: false,
      scenarioTests: false
    }
  }
}

// Merge environment-specific configuration
const environment = baseConfig.environment
const envConfig = environmentConfigs[environment] || environmentConfigs.development
const config = mergeDeep(baseConfig, envConfig)

/**
 * Helper function to merge nested objects
 */
function mergeDeep(target, source) {
  const output = { ...target }

  if (isObject(target) && isObject(source)) {
    Object.keys(source).forEach(key => {
      if (isObject(source[key])) {
        if (!(key in target)) {
          Object.assign(output, { [key]: source[key] })
        } else {
          output[key] = mergeDeep(target[key], source[key])
        }
      } else {
        Object.assign(output, { [key]: source[key] })
      }
    })
  }

  return output
}

function isObject(item) {
  return item && typeof item === 'object' && !Array.isArray(item)
}

/**
 * Helper function to build service URLs
 */
function buildServiceUrl(service, path = '') {
  const svc = config.services[service]
  if (!svc) {
    throw new Error(`Unknown service: ${service}`)
  }

  return `${svc.protocol}://${svc.host}:${svc.port}${svc.basePath || ''}${path}`
}

/**
 * Helper function to build WebSocket URLs
 */
function buildWebSocketUrl(service, path = '') {
  const svc = config.services[service]
  if (!svc) {
    throw new Error(`Unknown service: ${service}`)
  }

  const wsPort = svc.websocketPort || svc.port
  const protocol = svc.protocol === 'https' ? 'wss' : 'ws'

  return `${protocol}://${svc.host}:${wsPort}${path}`
}

/**
 * Helper function to get database connection string
 */
function getDatabaseString(type) {
  const db = config.databases[type]
  if (!db) {
    throw new Error(`Unknown database type: ${type}`)
  }

  switch (type) {
    case 'mongodb':
      return `mongodb://${db.host}:${db.port}/${db.database}`
    case 'postgresql':
      return `postgresql://${db.username}:${db.password}@${db.host}:${db.port}/${db.database}`
    case 'redis':
      return `redis://${db.password ? `${db.password}@` : ''}${db.host}:${db.port}/${db.db}`
    default:
      throw new Error(`Unsupported database type: ${type}`)
  }
}

// Export configuration and helpers
module.exports = {
  config,
  buildServiceUrl,
  buildWebSocketUrl,
  getDatabaseString,
  mergeDeep
}