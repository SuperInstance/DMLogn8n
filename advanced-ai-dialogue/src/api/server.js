const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const { createServer } = require('http');
const { Server } = require('socket.io');
require('dotenv').config();

// Import components
const EmotionalIntelligenceEngine = require('../core/EmotionalIntelligenceEngine');
const ContextAwareConversationManager = require('../core/ContextAwareConversationManager');
const DynamicVoiceSynthesisEngine = require('../voice/DynamicVoiceSynthesisEngine');
const MultiLanguageSupportSystem = require('../translation/MultiLanguageSupportSystem');
const ConversationAnalyticsEngine = require('../analytics/ConversationAnalyticsEngine');

// Import routes
const emotionRoutes = require('./routes/emotion');
const conversationRoutes = require('./routes/conversation');
const voiceRoutes = require('./routes/voice');
const translationRoutes = require('./routes/translation');
const analyticsRoutes = require('./routes/analytics');

// Initialize Express app
const app = express();
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: process.env.CORS_ORIGIN || "*",
    methods: ["GET", "POST"]
  }
});

// Middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGIN || "*",
  credentials: true
}));
app.use(morgan('combined'));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Initialize core engines
const emotionalEngine = new EmotionalIntelligenceEngine({
  emotionDecayRate: 0.01,
  memoryLimit: 1000,
  contextWindowSize: 10,
  empathyThreshold: 0.6,
  adaptationRate: 0.1
});

const conversationManager = new ContextAwareConversationManager({
  maxConversations: 100,
  shortTermMemoryLimit: 50,
  longTermMemoryLimit: 1000,
  contextWindowSize: 10
});

const voiceEngine = new DynamicVoiceSynthesisEngine({
  defaultProvider: 'elevenlabs',
  cacheDirectory: './voice-cache',
  maxCacheSize: 1000,
  quality: 'high',
  enableEmotionalModulation: true
});

const translationEngine = new MultiLanguageSupportSystem({
  defaultProvider: 'google',
  cacheSize: 10000,
  enableContextPreservation: true,
  enableCulturalNuance: true,
  enableFantasyLanguageTranslation: true
});

const analyticsEngine = new ConversationAnalyticsEngine({
  dataRetentionDays: 365,
  aggregationInterval: 60000,
  enableRealTimeAnalysis: true,
  enablePredictiveAnalytics: true
});

// Make engines available globally
app.set('emotionalEngine', emotionalEngine);
app.set('conversationManager', conversationManager);
app.set('voiceEngine', voiceEngine);
app.set('translationEngine', translationEngine);
app.set('analyticsEngine', analyticsEngine);

// Health check endpoint
app.get('/health', (req, res) => {
  const healthStatus = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    engines: {
      emotional: emotionalEngine ? 'active' : 'inactive',
      conversation: conversationManager ? 'active' : 'inactive',
      voice: voiceEngine ? 'active' : 'inactive',
      translation: translationEngine ? 'active' : 'inactive',
      analytics: analyticsEngine ? 'active' : 'inactive'
    },
    memory: process.memoryUsage(),
    version: '1.0.0'
  };

  res.json(healthStatus);
});

// API Routes
app.use('/api/emotion', emotionRoutes);
app.use('/api/conversation', conversationRoutes);
app.use('/api/voice', voiceRoutes);
app.use('/api/translation', translationRoutes);
app.use('/api/analytics', analyticsRoutes);

// WebSocket connections
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  // Join conversation rooms
  socket.on('join-conversation', (conversationId) => {
    socket.join(conversationId);
    console.log(`Socket ${socket.id} joined conversation ${conversationId}`);
  });

  // Leave conversation rooms
  socket.on('leave-conversation', (conversationId) => {
    socket.leave(conversationId);
    console.log(`Socket ${socket.id} left conversation ${conversationId}`);
  });

  // Real-time emotion analysis
  socket.on('emotion-analyze', async (data) => {
    try {
      const result = await emotionalEngine.analyzeEmotion(
        data.text,
        data.speakerId,
        data.context || {}
      );

      socket.emit('emotion-result', {
        requestId: data.requestId,
        result,
        timestamp: new Date().toISOString()
      });

      // Broadcast to conversation room if provided
      if (data.conversationId) {
        socket.to(data.conversationId).emit('emotion-update', {
          speakerId: data.speakerId,
          emotionalState: result.emotionalState,
          timestamp: new Date().toISOString()
        });
      }
    } catch (error) {
      socket.emit('emotion-error', {
        requestId: data.requestId,
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }
  });

  // Real-time voice synthesis
  socket.on('voice-synthesize', async (data) => {
    try {
      const audioBuffer = await voiceEngine.synthesizeSpeechRealtime(
        data.text,
        data.voiceConfig,
        data.emotionalState || {},
        data.options || {}
      );

      socket.emit('voice-result', {
        requestId: data.requestId,
        audioBuffer: audioBuffer.audioBuffer.toString('base64'),
        processingTime: audioBuffer.processingTime,
        latencyMet: audioBuffer.latencyMet,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      socket.emit('voice-error', {
        requestId: data.requestId,
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }
  });

  // Real-time conversation updates
  socket.on('conversation-update', async (data) => {
    try {
      const result = await conversationManager.processMessage(
        data.conversationId,
        data.message,
        data.speakerId,
        data.additionalContext || {}
      );

      socket.emit('conversation-result', {
        requestId: data.requestId,
        result,
        timestamp: new Date().toISOString()
      });

      // Broadcast to conversation room
      socket.to(data.conversationId).emit('conversation-message', {
        message: data.message,
        speakerId: data.speakerId,
        context: result.context,
        suggestions: result.suggestions,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      socket.emit('conversation-error', {
        requestId: data.requestId,
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }
  });

  // Real-time translation
  socket.on('translate', async (data) => {
    try {
      const translation = await translationEngine.translateText(
        data.text,
        data.targetLanguage,
        data.sourceLanguage || 'auto',
        data.context || {}
      );

      socket.emit('translation-result', {
        requestId: data.requestId,
        translation,
        sourceLanguage: data.sourceLanguage || 'auto',
        targetLanguage: data.targetLanguage,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      socket.emit('translation-error', {
        requestId: data.requestId,
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }
  });

  // Analytics events
  socket.on('track-event', (data) => {
    analyticsEngine.emit('analyticsEvent', {
      ...data,
      socketId: socket.id,
      timestamp: new Date().toISOString()
    });
  });

  // Handle disconnection
  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Server error:', error);

  res.status(error.status || 500).json({
    error: {
      message: error.message || 'Internal server error',
      status: error.status || 500,
      timestamp: new Date().toISOString(),
      requestId: req.id || 'unknown'
    }
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: {
      message: 'Endpoint not found',
      status: 404,
      timestamp: new Date().toISOString(),
      path: req.originalUrl
    }
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');

  server.close(() => {
    console.log('HTTP server closed');

    // Stop engines
    if (voiceEngine) voiceEngine.stop();
    if (analyticsEngine) analyticsEngine.reset();

    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully');

  server.close(() => {
    console.log('HTTP server closed');

    // Stop engines
    if (voiceEngine) voiceEngine.stop();
    if (analyticsEngine) analyticsEngine.reset();

    process.exit(0);
  });
});

// Start server
const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Advanced AI Dialogue System server running on port ${PORT}`);
  console.log(`Health check available at: http://localhost:${PORT}/health`);
  console.log('WebSocket server ready for real-time connections');
});

module.exports = { app, server, io };