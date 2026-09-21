/**
 * Dungeon API Routes
 * Endpoints for dungeon generation, management, and retrieval
 */

const express = require('express');
const router = express.Router();
const { v4: uuidv4 } = require('uuid');

// Mock dungeon generator instance (in real app, would be injected)
let dungeonGenerator = null;

// Middleware to initialize dungeon generator
router.use((req, res, next) => {
  if (!dungeonGenerator) {
    // In a real implementation, this would be properly injected
    const DungeonGenerator = require('../../src/core/DungeonGenerator');
    const ConfigManager = require('../../src/utils/ConfigManager');
    const Logger = require('../../src/utils/Logger');

    const config = new ConfigManager();
    const logger = new Logger();
    dungeonGenerator = new DungeonGenerator(config, logger);
  }
  next();
});

/**
 * POST /api/dungeons/generate
 * Generate a new dungeon
 */
router.post('/generate', async (req, res) => {
  try {
    const params = {
      algorithm: req.body.algorithm || 'roomCorridor',
      theme: req.body.theme || 'classic',
      width: req.body.width || 50,
      height: req.body.height || 50,
      floors: req.body.floors || 1,
      difficulty: req.body.difficulty || 1,
      playerLevel: req.body.playerLevel || 1,
      seed: req.body.seed || Math.random(),
      customRules: req.body.customRules || {},
      ...req.body.options
    };

    const dungeon = await dungeonGenerator.generate({
      ...params,
      onProgress: (progress) => {
        // In a real implementation, this could be sent via WebSocket
        // For now, we'll just log it
        console.log('Generation progress:', progress);
      }
    });

    res.json({
      success: true,
      dungeon: {
        id: dungeon.id,
        metadata: dungeon.metadata,
        dimensions: dungeon.dimensions,
        statistics: dungeon.statistics,
        floors: dungeon.floors.map(floor => ({
          floor: floor.floor,
          rooms: floor.rooms,
          corridors: floor.corridors,
          spawns: floor.spawns || [],
          loot: floor.loot || [],
          traps: floor.traps || [],
          puzzles: floor.puzzles || [],
          bosses: floor.bosses || []
        }))
      },
      generatedAt: new Date().toISOString()
    });

  } catch (error) {
    console.error('Dungeon generation error:', error);
    res.status(500).json({
      success: false,
      error: {
        message: error.message,
        type: 'generation_error'
      }
    });
  }
});

/**
 * GET /api/dungeons
 * List all generated dungeons
 */
router.get('/', (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 10;
    const history = dungeonGenerator.getGenerationHistory(limit);

    const dungeons = history.map(dungeon => ({
      id: dungeon.id,
      metadata: dungeon.metadata,
      dimensions: dungeon.dimensions,
      statistics: dungeon.statistics,
      generationTime: dungeon.generationTime,
      timestamp: dungeon.timestamp
    }));

    res.json({
      success: true,
      dungeons,
      total: dungeons.length
    });

  } catch (error) {
    console.error('List dungeons error:', error);
    res.status(500).json({
      success: false,
      error: {
        message: error.message,
        type: 'list_error'
      }
    });
  }
});

/**
 * GET /api/dungeons/:id
 * Get specific dungeon by ID
 */
router.get('/:id', (req, res) => {
  try {
    const { id } = req.params;
    const history = dungeonGenerator.getGenerationHistory();

    const dungeon = history.find(d => d.id === id);

    if (!dungeon) {
      return res.status(404).json({
        success: false,
        error: {
          message: 'Dungeon not found',
          type: 'not_found'
        }
      });
    }

    res.json({
      success: true,
      dungeon: {
        id: dungeon.id,
        metadata: dungeon.metadata,
        dimensions: dungeon.dimensions,
        statistics: dungeon.statistics,
        floors: dungeon.floors.map(floor => ({
          floor: floor.floor,
          grid: floor.grid,
          rooms: floor.rooms,
          corridors: floor.corridors,
          spawns: floor.spawns || [],
          loot: floor.loot || [],
          traps: floor.traps || [],
          puzzles: floor.puzzles || [],
          bosses: floor.bosses || [],
          lighting: floor.lighting,
          environment: floor.environment
        })),
        generatedAt: dungeon.timestamp
      }
    });

  } catch (error) {
    console.error('Get dungeon error:', error);
    res.status(500).json({
      success: false,
      error: {
        message: error.message,
        type: 'get_error'
      }
    });
  }
});

/**
 * POST /api/dungeons/:id/modify
 * Modify an existing dungeon
 */
router.post('/:id/modify', async (req, res) => {
  try {
    const { id } = req.params;
    const modifications = req.body;

    const result = await dungeonGenerator.modifyDungeon({
      dungeonId: id,
      ...modifications
    });

    res.json({
      success: true,
      dungeon: result,
      modifiedAt: new Date().toISOString()
    });

  } catch (error) {
    console.error('Modify dungeon error:', error);
    res.status(500).json({
      success: false,
      error: {
        message: error.message,
        type: 'modification_error'
      }
    });
  }
});

/**
 * DELETE /api/dungeons/:id
 * Delete a dungeon from history
 */
router.delete('/:id', (req, res) => {
  try {
    const { id } = req.params;
    const history = dungeonGenerator.getGenerationHistory();

    const index = history.findIndex(d => d.id === id);
    if (index === -1) {
      return res.status(404).json({
        success: false,
        error: {
          message: 'Dungeon not found',
          type: 'not_found'
        }
      });
    }

    // Remove from history
    history.splice(index, 1);

    res.json({
      success: true,
      message: 'Dungeon deleted successfully',
      deletedAt: new Date().toISOString()
    });

  } catch (error) {
    console.error('Delete dungeon error:', error);
    res.status(500).json({
      success: false,
      error: {
        message: error.message,
        type: 'delete_error'
      }
    });
  }
});

/**
 * GET /api/dungeons/:id/floor/:floorIndex
 * Get specific floor of a dungeon
 */
router.get('/:id/floor/:floorIndex', (req, res) => {
  try {
    const { id, floorIndex } = req.params;
    const history = dungeonGenerator.getGenerationHistory();

    const dungeon = history.find(d => d.id === id);
    if (!dungeon) {
      return res.status(404).json({
        success: false,
        error: {
          message: 'Dungeon not found',
          type: 'not_found'
        }
      });
    }

    const floor = dungeon.floors[parseInt(floorIndex)];
    if (!floor) {
      return res.status(404).json({
        success: false,
        error: {
          message: 'Floor not found',
          type: 'not_found'
        }
      });
    }

    res.json({
      success: true,
      floor: {
        floor: floor.floor,
        grid: floor.grid,
        rooms: floor.rooms,
        corridors: floor.corridors,
        spawns: floor.spawns || [],
        loot: floor.loot || [],
        traps: floor.traps || [],
        puzzles: floor.puzzles || [],
        bosses: floor.bosses || [],
        lighting: floor.lighting,
        environment: floor.environment
      }
    });

  } catch (error) {
    console.error('Get floor error:', error);
    res.status(500).json({
      success: false,
      error: {
        message: error.message,
        type: 'get_floor_error'
      }
    });
  }
});

/**
 * GET /api/dungeons/:id/visualize/:floorIndex
 * Get visual representation of dungeon floor
 */
router.get('/:id/visualize/:floorIndex', (req, res) => {
  try {
    const { id, floorIndex } = req.params;
    const { format = 'ascii' } = req.query;

    const history = dungeonGenerator.getGenerationHistory();
    const dungeon = history.find(d => d.id === id);

    if (!dungeon) {
      return res.status(404).json({
        success: false,
        error: {
          message: 'Dungeon not found',
          type: 'not_found'
        }
      });
    }

    const floor = dungeon.floors[parseInt(floorIndex)];
    if (!floor) {
      return res.status(404).json({
        success: false,
        error: {
          message: 'Floor not found',
          type: 'not_found'
        }
      });
    }

    let visualization;

    if (format === 'ascii') {
      // ASCII visualization
      const Grid = require('../../src/utils/Grid');
      visualization = Grid.toString(floor.grid, {
        'stone_wall': '#',
        'stone_floor': '.',
        'wooden_door': '+',
        'treasure': '*',
        'enemy': 'E',
        'trap': '^'
      });
    } else if (format === 'json') {
      // JSON with coordinates
      visualization = {
        dimensions: {
          width: floor.grid[0].length,
          height: floor.grid.length
        },
        tiles: floor.grid.map((row, y) =>
          row.map((tile, x) => ({
            x, y, type: tile
          }))
        ),
        rooms: floor.rooms,
        corridors: floor.corridors
      };
    } else {
      return res.status(400).json({
        success: false,
        error: {
          message: 'Invalid format. Supported formats: ascii, json',
          type: 'invalid_format'
        }
      });
    }

    res.json({
      success: true,
      dungeonId: id,
      floor: parseInt(floorIndex),
      format,
      visualization
    });

  } catch (error) {
    console.error('Visualize floor error:', error);
    res.status(500).json({
      success: false,
      error: {
        message: error.message,
        type: 'visualization_error'
      }
    });
  }
});

/**
 * POST /api/dungeons/validate
 * Validate dungeon parameters
 */
router.post('/validate', (req, res) => {
  try {
    const params = req.body;

    const validation = {
      valid: true,
      warnings: [],
      errors: []
    };

    // Validate required parameters
    if (params.width && (params.width < 10 || params.width > 200)) {
      validation.errors.push('Width must be between 10 and 200');
      validation.valid = false;
    }

    if (params.height && (params.height < 10 || params.height > 200)) {
      validation.errors.push('Height must be between 10 and 200');
      validation.valid = false;
    }

    if (params.floors && (params.floors < 1 || params.floors > 10)) {
      validation.errors.push('Floors must be between 1 and 10');
      validation.valid = false;
    }

    if (params.difficulty && (params.difficulty < 1 || params.difficulty > 10)) {
      validation.errors.push('Difficulty must be between 1 and 10');
      validation.valid = false;
    }

    if (params.playerLevel && (params.playerLevel < 1 || params.playerLevel > 20)) {
      validation.errors.push('Player level must be between 1 and 20');
      validation.valid = false;
    }

    // Check for warnings
    if (params.width && params.height && params.width * params.height > 10000) {
      validation.warnings.push('Large dungeon size may impact generation performance');
    }

    if (params.floors && params.floors > 5) {
      validation.warnings.push('Multi-floor dungeons may take longer to generate');
    }

    res.json({
      success: true,
      validation
    });

  } catch (error) {
    console.error('Validation error:', error);
    res.status(500).json({
      success: false,
      error: {
        message: error.message,
        type: 'validation_error'
      }
    });
  }
});

module.exports = router;