import express from 'express';
import { createServer } from 'http';
import { Server } from 'socket.io';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';

import { DatabaseService } from '@/services/database';
import { StreamingService } from '@/services/streaming';
import { OBSController } from '@/services/obs';
import { EngagementService } from '@/services/engagement';
import { ContentService } from '@/services/content';
import { MonetizationService } from '@/services/monetization';
import { AnalyticsService } from '@/services/analytics';

import apiRoutes from '@/routes/api';
import authRoutes from '@/routes/auth';
import streamingRoutes from '@/routes/streaming';
import overlaysRoutes from '@/routes/overlays';
import monetizationRoutes from '@/routes/monetization';

import { errorHandler } from '@/middleware/errorHandler';
import { logger } from '@/utils/logger';
import { validateApiKey } from '@/middleware/auth';

// Load environment variables
dotenv.config();

class StreamingPlatformServer {
  private app: express.Application;
  private server: any;
  private io: Server;
  private port: number;

  constructor() {
    this.app = express();
    this.server = createServer(this.app);
    this.io = new Server(this.server, {
      cors: {
        origin: process.env.ALLOWED_ORIGINS?.split(',') || "*",
        methods: ["GET", "POST"]
      }
    });
    this.port = parseInt(process.env.PORT || '3000');

    this.initializeServices();
    this.setupMiddleware();
    this.setupRoutes();
    this.setupSocketHandlers();
    this.setupErrorHandling();
  }

  private async initializeServices() {
    try {
      // Initialize database connection
      await DatabaseService.connect();
      logger.info('Database connected successfully');

      // Initialize core services
      await StreamingService.initialize();
      await OBSController.initialize();
      await EngagementService.initialize();
      await ContentService.initialize();
      await MonetizationService.initialize();
      await AnalyticsService.initialize();

      logger.info('All services initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize services:', error);
      process.exit(1);
    }
  }

  private setupMiddleware() {
    // Basic middleware
    this.app.use(cors());
    this.app.use(express.json({ limit: '50mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '50mb' }));

    // Serve static files
    this.app.use('/uploads', express.static(path.join(__dirname, '../uploads')));
    this.app.use('/overlays', express.static(path.join(__dirname, '../overlays')));

    // API key validation for public endpoints
    this.app.use('/api/webhooks', validateApiKey);
  }

  private setupRoutes() {
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        services: {
          database: DatabaseService.isConnected(),
          obs: OBSController.isConnected(),
          streaming: StreamingService.isReady()
        }
      });
    });

    // API routes
    this.app.use('/api/auth', authRoutes);
    this.app.use('/api/streaming', streamingRoutes);
    this.app.use('/api/overlays', overlaysRoutes);
    this.app.use('/api/monetization', monetizationRoutes);
    this.app.use('/api', apiRoutes);

    // WebSocket endpoint
    this.app.get('/socket.io', (req, res) => {
      res.send('WebSocket server running');
    });
  }

  private setupSocketHandlers() {
    this.io.on('connection', (socket) => {
      logger.info(`Client connected: ${socket.id}`);

      // Handle streaming controls
      socket.on('start-stream', async (data) => {
        try {
          const result = await StreamingService.startStream(data);
          socket.emit('stream-started', result);
          this.io.emit('stream-status', { status: 'live', ...result });
        } catch (error) {
          socket.emit('error', { message: error.message });
        }
      });

      socket.on('stop-stream', async () => {
        try {
          const result = await StreamingService.stopStream();
          socket.emit('stream-stopped', result);
          this.io.emit('stream-status', { status: 'offline' });
        } catch (error) {
          socket.emit('error', { message: error.message });
        }
      });

      // Handle OBS scene switching
      socket.on('switch-scene', async (sceneName) => {
        try {
          await OBSController.switchScene(sceneName);
          socket.emit('scene-switched', { scene: sceneName });
          this.io.emit('scene-update', { scene: sceneName });
        } catch (error) {
          socket.emit('error', { message: error.message });
        }
      });

      // Handle chat messages
      socket.on('chat-message', async (message) => {
        try {
          const processedMessage = await EngagementService.processMessage(message);
          this.io.emit('new-message', processedMessage);
        } catch (error) {
          socket.emit('error', { message: error.message });
        }
      });

      // Handle donations
      socket.on('donation', async (donation) => {
        try {
          const processedDonation = await MonetizationService.processDonation(donation);
          this.io.emit('donation-alert', processedDonation);
        } catch (error) {
          socket.emit('error', { message: error.message });
        }
      });

      // Handle dice rolls
      socket.on('roll-dice', async (data) => {
        try {
          const roll = await ContentService.rollDice(data);
          this.io.emit('dice-roll', roll);
        } catch (error) {
          socket.emit('error', { message: error.message });
        }
      });

      socket.on('disconnect', () => {
        logger.info(`Client disconnected: ${socket.id}`);
      });
    });
  }

  private setupErrorHandling() {
    this.app.use(errorHandler);

    // Handle unhandled promise rejections
    process.on('unhandledRejection', (reason, promise) => {
      logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
    });

    // Handle uncaught exceptions
    process.on('uncaughtException', (error) => {
      logger.error('Uncaught Exception:', error);
      process.exit(1);
    });

    // Graceful shutdown
    process.on('SIGTERM', this.gracefulShutdown.bind(this));
    process.on('SIGINT', this.gracefulShutdown.bind(this));
  }

  private async gracefulShutdown() {
    logger.info('Received shutdown signal, starting graceful shutdown...');

    try {
      // Stop all active streams
      await StreamingService.stopAllStreams();

      // Close database connections
      await DatabaseService.disconnect();

      // Close server
      this.server.close(() => {
        logger.info('Server closed');
        process.exit(0);
      });
    } catch (error) {
      logger.error('Error during graceful shutdown:', error);
      process.exit(1);
    }
  }

  public start() {
    this.server.listen(this.port, () => {
      logger.info(`🚀 D&D Streaming Platform server running on port ${this.port}`);
      logger.info(`📡 WebSocket server ready`);
      logger.info(`🎮 OBS Studio integration: ${process.env.OBS_WEBSOCKET_URL}`);
      logger.info(`🌐 API endpoints available at http://localhost:${this.port}/api`);
      logger.info(`📺 Overlay server: http://localhost:${this.port}/overlays`);
    });
  }
}

// Start the server
const server = new StreamingPlatformServer();
server.start();