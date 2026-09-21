/**
 * API Routes for Dynamic Dungeon Generator
 * RESTful endpoints for dungeon generation and management
 */

const express = require('express');
const router = express.Router();

// Import route modules
const dungeonRoutes = require('./dungeons');
const themeRoutes = require('./themes');
const algorithmRoutes = require('./algorithms');
const customizationRoutes = require('./customization');
const exportRoutes = require('./export');
const integrationRoutes = require('./integration');

// Health check
router.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: require('../../package.json').version
  });
});

// API information
router.get('/', (req, res) => {
  res.json({
    name: 'Dynamic Dungeon Generator API',
    version: require('../../package.json').version,
    description: 'Advanced procedural dungeon generation system',
    endpoints: {
      dungeons: '/api/dungeons',
      themes: '/api/themes',
      algorithms: '/api/algorithms',
      customization: '/api/customization',
      export: '/api/export',
      integration: '/api/integration'
    }
  });
});

// Mount route modules
router.use('/dungeons', dungeonRoutes);
router.use('/themes', themeRoutes);
router.use('/algorithms', algorithmRoutes);
router.use('/customization', customizationRoutes);
router.use('/export', exportRoutes);
router.use('/integration', integrationRoutes);

// Error handling middleware
router.use((error, req, res, next) => {
  console.error('API Error:', error);

  res.status(error.status || 500).json({
    error: {
      message: error.message || 'Internal server error',
      status: error.status || 500,
      timestamp: new Date().toISOString()
    }
  });
});

// 404 handler
router.use('*', (req, res) => {
  res.status(404).json({
    error: {
      message: 'Endpoint not found',
      status: 404,
      timestamp: new Date().toISOString()
    }
  });
});

module.exports = router;