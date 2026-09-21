/**
 * Dynamic Dungeon Generator - Main Entry Point
 * Advanced procedural dungeon generation system for DMlogn8n
 */

const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');
const winston = require('winston');

const DungeonGenerator = require('./core/DungeonGenerator');
const ConfigManager = require('./utils/ConfigManager');
const Logger = require('./utils/Logger');

// Initialize logger
const logger = new Logger();

// Initialize Express app
const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// Middleware
app.use(express.json({ limit: '50mb' }));
app.use(express.static(path.join(__dirname, '../public')));
app.use('/api', require('./api/routes'));

// Configuration
const config = new ConfigManager();
const PORT = process.env.PORT || config.get('server.port', 3001);

// Initialize Dungeon Generator
const dungeonGenerator = new DungeonGenerator(config, logger);

// Socket.IO handlers for real-time dungeon generation
io.on('connection', (socket) => {
  logger.info(`Client connected: ${socket.id}`);

  socket.on('generate-dungeon', async (params) => {
    try {
      logger.info(`Generating dungeon for client ${socket.id}`, params);

      // Send progress updates
      socket.emit('generation-started');

      const dungeon = await dungeonGenerator.generate({
        ...params,
        onProgress: (progress) => {
          socket.emit('generation-progress', progress);
        }
      });

      socket.emit('generation-complete', dungeon);
      logger.info(`Dungeon generation complete for client ${socket.id}`);
    } catch (error) {
      logger.error(`Dungeon generation failed for client ${socket.id}`, error);
      socket.emit('generation-error', { message: error.message });
    }
  });

  socket.on('modify-dungeon', async (params) => {
    try {
      const result = await dungeonGenerator.modifyDungeon(params);
      socket.emit('dungeon-modified', result);
    } catch (error) {
      socket.emit('modification-error', { message: error.message });
    }
  });

  socket.on('get-themes', () => {
    const themes = dungeonGenerator.getAvailableThemes();
    socket.emit('themes-list', themes);
  });

  socket.on('get-templates', () => {
    const templates = dungeonGenerator.getAvailableTemplates();
    socket.emit('templates-list', templates);
  });

  socket.on('disconnect', () => {
    logger.info(`Client disconnected: ${socket.id}`);
  });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: require('../package.json').version
  });
});

// Start server
server.listen(PORT, () => {
  logger.info(`Dynamic Dungeon Generator server running on port ${PORT}`);
  logger.info(`API available at http://localhost:${PORT}/api`);
  logger.info(`Socket.IO available for real-time generation`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

module.exports = {
  app,
  server,
  io,
  dungeonGenerator,
  logger
};