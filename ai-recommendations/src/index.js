require('dotenv').config();

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const winston = require('winston');
const path = require('path');

// Import configurations and services
const DatabaseConfig = require('./config/database');
const RedisConfig = require('./config/redis');
const HybridRecommender = require('./ml/HybridRecommender');
const PlayerRecommendationService = require('./services/PlayerRecommendationService');
const DMRecommendationService = require('./services/DMRecommendationService');
const ContentDiscoveryService = require('./services/ContentDiscoveryService');
const PersonalizationEngine = require('./services/PersonalizationEngine');
const recommendationRoutes = require('./api/recommendationRoutes');

// Initialize Winston logger
const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
    ),
    defaultMeta: { service: 'ai-recommendations' },
    transports: [
        new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
        new winston.transports.File({ filename: 'logs/combined.log' })
    ]
});

if (process.env.NODE_ENV !== 'production') {
    logger.add(new winston.transports.Console({
        format: winston.format.simple()
    }));
}

// Create Express app
const app = express();

// Security middleware
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            scriptSrc: ["'self'"],
            imgSrc: ["'self'", "data:", "https:"],
            connectSrc: ["'self'"],
            fontSrc: ["'self'"],
            objectSrc: ["'none'"],
            mediaSrc: ["'self'"],
            frameSrc: ["'none'"],
        },
    },
}));

// CORS configuration
app.use(cors({
    origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));

// Compression middleware
app.use(compression());

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Request logging middleware
app.use((req, res, next) => {
    logger.info(`${req.method} ${req.path}`, {
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        timestamp: new Date().toISOString()
    });
    next();
});

// Initialize services
let databaseConfig, redisClient, hybridRecommender, playerService, dmService, discoveryService, personalizationEngine;

async function initializeServices() {
    try {
        logger.info('Initializing services...');

        // Initialize database
        databaseConfig = new DatabaseConfig();
        await databaseConfig.connect();
        await databaseConfig.createIndexes();

        // Initialize Redis
        redisClient = RedisConfig;
        await redisClient.connect();

        // Initialize ML and recommendation services
        hybridRecommender = new HybridRecommender({
            collaborative: {
                minInteractions: 5,
                similarityThreshold: 0.1,
                maxNeighbors: 50
            },
            contentBased: {
                minFeatureWeight: 0.01,
                maxFeatures: 1000,
                decayFactor: 0.95
            }
        });

        playerService = new PlayerRecommendationService(hybridRecommender, null);
        dmService = new DMRecommendationService(hybridRecommender, null);
        discoveryService = new ContentDiscoveryService(hybridRecommender, null, redisClient);
        personalizationEngine = new PersonalizationEngine(redisClient, hybridRecommender);

        // Load initial data and train models
        await loadInitialData();

        logger.info('All services initialized successfully');

    } catch (error) {
        logger.error('Failed to initialize services:', error);
        process.exit(1);
    }
}

async function loadInitialData() {
    try {
        logger.info('Loading initial data...');

        // Load sample interaction data
        const sampleInteractions = require('./data/samples/interactions.json');
        const sampleContent = require('./data/samples/content.json');

        // Initialize the hybrid recommender with sample data
        await hybridRecommender.initialize(sampleInteractions, sampleContent);

        logger.info(`Loaded ${sampleInteractions.length} interactions and ${sampleContent.length} content items`);

    } catch (error) {
        logger.warn('Could not load initial data, using empty datasets:', error);
        // Initialize with empty data if sample data is not available
        await hybridRecommender.initialize([], []);
    }
}

// Middleware to attach services to requests
app.use((req, res, next) => {
    req.databaseConfig = databaseConfig;
    req.redisClient = redisClient;
    req.hybridRecommender = hybridRecommender;
    req.playerRecommendationService = playerService;
    req.dmRecommendationService = dmService;
    req.contentDiscoveryService = discoveryService;
    req.personalizationEngine = personalizationEngine;
    next();
});

// Health check endpoint
app.get('/health', async (req, res) => {
    try {
        const health = {
            status: 'healthy',
            timestamp: new Date().toISOString(),
            uptime: process.uptime(),
            memory: process.memoryUsage(),
            services: {
                database: 'connected',
                redis: redisClient.isReady() ? 'connected' : 'disconnected'
            }
        };

        res.status(200).json(health);
    } catch (error) {
        logger.error('Health check failed:', error);
        res.status(503).json({
            status: 'unhealthy',
            timestamp: new Date().toISOString(),
            error: error.message
        });
    }
});

// API routes
app.use('/api/recommendations', recommendationRoutes);

// Serve static files for frontend
app.use(express.static(path.join(__dirname, '../public')));

// Catch-all handler for frontend routing
app.get('*', (req, res) => {
    if (req.path.startsWith('/api')) {
        return res.status(404).json({
            error: 'API endpoint not found',
            path: req.path
        });
    }

    // Serve index.html for all other routes (SPA support)
    res.sendFile(path.join(__dirname, '../public/index.html'));
});

// Error handling middleware
app.use((error, req, res, next) => {
    logger.error('Unhandled error:', error);

    if (res.headersSent) {
        return next(error);
    }

    res.status(error.status || 500).json({
        error: process.env.NODE_ENV === 'production' ? 'Internal server error' : error.message,
        ...(process.env.NODE_ENV !== 'production' && { stack: error.stack })
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        error: 'Not found',
        path: req.path,
        method: req.method
    });
});

// Graceful shutdown
async function gracefulShutdown(signal) {
    logger.info(`Received ${signal}, starting graceful shutdown...`);

    try {
        // Close server
        server.close(async () => {
            logger.info('HTTP server closed');

            // Disconnect services
            if (redisClient) {
                await redisClient.disconnect();
            }

            if (databaseConfig) {
                await databaseConfig.disconnect();
            }

            logger.info('All services disconnected');
            process.exit(0);
        });

        // Force shutdown after 30 seconds
        setTimeout(() => {
            logger.error('Forced shutdown after timeout');
            process.exit(1);
        }, 30000);

    } catch (error) {
        logger.error('Error during graceful shutdown:', error);
        process.exit(1);
    }
}

// Start server
const PORT = process.env.PORT || 3001;
const server = app.listen(PORT, async () => {
    logger.info(`AI Recommendations Server running on port ${PORT}`);
    logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);

    // Initialize services after server starts
    await initializeServices();

    // Setup periodic model retraining
    setInterval(async () => {
        try {
            logger.info('Starting periodic model retraining...');
            // Add model retraining logic here
            logger.info('Model retraining completed');
        } catch (error) {
            logger.error('Model retraining failed:', error);
        }
    }, 24 * 60 * 60 * 1000); // Retrain daily
});

// Handle process signals
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
    logger.error('Uncaught Exception:', error);
    gracefulShutdown('uncaughtException');
});

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
    logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
    gracefulShutdown('unhandledRejection');
});

module.exports = app;