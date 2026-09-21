/**
 * Core Dungeon Generator Class
 * Orchestrates all dungeon generation algorithms and systems
 */

const _ = require('lodash');
const { v4: uuidv4 } = require('uuid');

// Import algorithms
const CellularAutomata = require('../algorithms/CellularAutomata');
const BSPTree = require('../algorithms/BSPTree');
const RoomCorridor = require('../algorithms/RoomCorridor');
const OrganicGrowth = require('../algorithms/OrganicGrowth');

// Import systems
const ThemeManager = require('../themes/ThemeManager');
const EnvironmentSystem = require('../environment/EnvironmentSystem');
const ContentPopulator = require('../content/ContentPopulator');
const CustomizationEngine = require('../customization/CustomizationEngine');
const SpecialFeatures = require('../special-features/SpecialFeatures');

// Utils
const Grid = require('../utils/Grid');
const MathUtils = require('../utils/MathUtils');

class DungeonGenerator {
  constructor(config, logger) {
    this.config = config;
    this.logger = logger;

    // Initialize systems
    this.algorithms = {
      cellular: new CellularAutomata(config, logger),
      bsp: new BSPTree(config, logger),
      roomCorridor: new RoomCorridor(config, logger),
      organic: new OrganicGrowth(config, logger)
    };

    this.themeManager = new ThemeManager(config, logger);
    this.environmentSystem = new EnvironmentSystem(config, logger);
    this.contentPopulator = new ContentPopulator(config, logger);
    this.customizationEngine = new CustomizationEngine(config, logger);
    this.specialFeatures = new SpecialFeatures(config, logger);

    // Generation state
    this.currentGeneration = null;
    this.generationHistory = [];
  }

  /**
   * Main dungeon generation method
   */
  async generate(params = {}) {
    const {
      algorithm = 'roomCorridor',
      theme = 'classic',
      width = 50,
      height = 50,
      floors = 1,
      difficulty = 1,
      playerLevel = 1,
      seed = Math.random(),
      customRules = {},
      onProgress = () => {},
      ...options
    } = params;

    try {
      this.logger.info('Starting dungeon generation', {
        algorithm, theme, width, height, floors
      });

      // Set seed for reproducible generation
      MathUtils.setSeed(seed);

      const generationId = uuidv4();
      this.currentGeneration = { id: generationId, startTime: Date.now() };

      // Initialize dungeon structure
      const dungeon = this.initializeDungeon({
        width, height, floors, theme, difficulty, playerLevel, generationId
      });

      onProgress({ stage: 'initialization', progress: 5 });

      // Generate each floor
      for (let floor = 0; floor < floors; floor++) {
        onProgress({
          stage: 'floor-generation',
          floor: floor + 1,
          totalFloors: floors,
          progress: 10 + (floor / floors) * 30
        });

        const floorData = await this.generateFloor({
          floor: floor + 1,
          algorithm,
          width,
          height,
          theme,
          difficulty: difficulty + (floor * 0.2), // Scale difficulty per floor
          playerLevel,
          seed: seed + floor,
          options,
          customRules
        });

        dungeon.floors.push(floorData);
      }

      onProgress({ stage: 'content-population', progress: 50 });

      // Populate dungeon with content
      await this.populateDungeon(dungeon, {
        difficulty,
        playerLevel,
        theme,
        onProgress: (progress) => onProgress({
          stage: 'content-population',
          progress: 50 + progress * 0.3
        })
      });

      onProgress({ stage: 'environment-setup', progress: 80 });

      // Setup environment
      await this.setupEnvironment(dungeon, {
        theme,
        onProgress: (progress) => onProgress({
          stage: 'environment-setup',
          progress: 80 + progress * 0.15
        })
      });

      onProgress({ stage: 'special-features', progress: 95 });

      // Apply special features
      await this.applySpecialFeatures(dungeon, {
        difficulty,
        playerLevel,
        options,
        onProgress: (progress) => onProgress({
          stage: 'special-features',
          progress: 95 + progress * 0.05
        })
      });

      // Finalize dungeon
      const finalizedDungeon = this.finalizeDungeon(dungeon);

      // Store in history
      this.generationHistory.push({
        ...finalizedDungeon,
        generationTime: Date.now() - this.currentGeneration.startTime,
        timestamp: new Date().toISOString()
      });

      onProgress({ stage: 'complete', progress: 100 });

      this.logger.info('Dungeon generation completed', {
        generationId,
        floors: floors,
        time: Date.now() - this.currentGeneration.startTime
      });

      return finalizedDungeon;

    } catch (error) {
      this.logger.error('Dungeon generation failed', error);
      throw new Error(`Dungeon generation failed: ${error.message}`);
    }
  }

  /**
   * Initialize basic dungeon structure
   */
  initializeDungeon(params) {
    return {
      id: params.generationId,
      metadata: {
        theme: params.theme,
        difficulty: params.difficulty,
        playerLevel: params.playerLevel,
        createdAt: new Date().toISOString(),
        version: '1.0.0'
      },
      dimensions: {
        width: params.width,
        height: params.height,
        floors: params.floors
      },
      floors: [],
      connections: [],
      secrets: [],
      events: [],
      statistics: {
        totalRooms: 0,
        totalEnemies: 0,
        totalLoot: 0,
        totalTraps: 0
      }
    };
  }

  /**
   * Generate a single floor
   */
  async generateFloor(params) {
    const { algorithm, floor, ...floorParams } = params;

    // Get theme configuration
    const themeConfig = this.themeManager.getTheme(floorParams.theme);

    // Generate base layout using selected algorithm
    const algorithmInstance = this.algorithms[algorithm];
    if (!algorithmInstance) {
      throw new Error(`Unknown algorithm: ${algorithm}`);
    }

    const layout = await algorithmInstance.generate({
      ...floorParams,
      floor,
      themeConfig
    });

    // Apply theme-specific modifications
    const themedLayout = this.themeManager.applyTheme(layout, themeConfig);

    return {
      floor,
      grid: themedLayout.grid,
      rooms: themedLayout.rooms,
      corridors: themedLayout.corridors,
      theme: themeConfig,
      lighting: {},
      weather: null,
      environment: {},
      spawns: [],
      loot: [],
      traps: [],
      secrets: [],
      connections: []
    };
  }

  /**
   * Populate dungeon with enemies, loot, and interactive elements
   */
  async populateDungeon(dungeon, params) {
    await this.contentPopulator.populate(dungeon, params);
  }

  /**
   * Setup environment systems
   */
  async setupEnvironment(dungeon, params) {
    await this.environmentSystem.setup(dungeon, params);
  }

  /**
   * Apply special features and dynamic elements
   */
  async applySpecialFeatures(dungeon, params) {
    await this.specialFeatures.apply(dungeon, params);
  }

  /**
   * Finalize dungeon and prepare for export
   */
  finalizeDungeon(dungeon) {
    // Calculate statistics
    dungeon.statistics = this.calculateStatistics(dungeon);

    // Validate dungeon integrity
    this.validateDungeon(dungeon);

    // Add export metadata
    dungeon.exportMetadata = {
      exportedAt: new Date().toISOString(),
      format: 'DMlogn8n-v1.0',
      compatibility: ['combat-system', 'quest-generator', 'world-state']
    };

    return dungeon;
  }

  /**
   * Calculate dungeon statistics
   */
  calculateStatistics(dungeon) {
    const stats = {
      totalRooms: 0,
      totalCorridors: 0,
      totalEnemies: 0,
      totalLoot: 0,
      totalTraps: 0,
      totalSecrets: 0,
      averageRoomSize: 0,
      dungeonComplexity: 0
    };

    dungeon.floors.forEach(floor => {
      stats.totalRooms += floor.rooms.length;
      stats.totalCorridors += floor.corridors.length;
      stats.totalEnemies += floor.spawns.length;
      stats.totalLoot += floor.loot.length;
      stats.totalTraps += floor.traps.length;
      stats.totalSecrets += floor.secrets.length;
    });

    // Calculate complexity score
    stats.dungeonComplexity = this.calculateComplexity(dungeon);

    return stats;
  }

  /**
   * Calculate dungeon complexity score
   */
  calculateComplexity(dungeon) {
    let complexity = 0;

    dungeon.floors.forEach(floor => {
      // Room diversity
      complexity += floor.rooms.length * 10;

      // Corridor complexity
      complexity += floor.corridors.length * 5;

      // Enemy density
      complexity += floor.spawns.length * 15;

      // Trap density
      complexity += floor.traps.length * 20;

      // Secret areas
      complexity += floor.secrets.length * 25;
    });

    return Math.min(100, Math.round(complexity / dungeon.floors.length));
  }

  /**
   * Validate dungeon integrity
   */
  validateDungeon(dungeon) {
    // Ensure all floors are accessible
    if (dungeon.floors.length > 1 && dungeon.connections.length === 0) {
      this.logger.warn('Multi-floor dungeon has no connections between floors');
    }

    // Validate each floor
    dungeon.floors.forEach((floor, index) => {
      if (!floor.grid || floor.grid.length === 0) {
        throw new Error(`Floor ${index + 1} has invalid grid`);
      }
    });
  }

  /**
   * Modify existing dungeon
   */
  async modifyDungeon(params) {
    const { dungeonId, modifications, floor } = params;

    // Find dungeon in history
    const dungeon = this.generationHistory.find(d => d.id === dungeonId);
    if (!dungeon) {
      throw new Error(`Dungeon ${dungeonId} not found`);
    }

    // Apply modifications
    const modifiedDungeon = await this.customizationEngine.applyModifications(
      dungeon,
      modifications,
      floor
    );

    // Update history
    const index = this.generationHistory.findIndex(d => d.id === dungeonId);
    this.generationHistory[index] = modifiedDungeon;

    return modifiedDungeon;
  }

  /**
   * Get available themes
   */
  getAvailableThemes() {
    return this.themeManager.getAvailableThemes();
  }

  /**
   * Get available templates
   */
  getAvailableTemplates() {
    return this.customizationEngine.getTemplates();
  }

  /**
   * Get generation history
   */
  getGenerationHistory(limit = 10) {
    return this.generationHistory.slice(-limit);
  }

  /**
   * Clear generation history
   */
  clearHistory() {
    this.generationHistory = [];
    this.logger.info('Generation history cleared');
  }
}

module.exports = DungeonGenerator;