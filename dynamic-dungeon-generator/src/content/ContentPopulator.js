/**
 * Content Populator
 * Intelligently places enemies, loot, traps, and other interactive content
 */

const EnemyPlacer = require('./enemies/EnemyPlacer');
const LootGenerator = require('./loot/LootGenerator');
const TrapPlacer = require('./traps/TrapPlacer');
const PuzzleGenerator = require('./puzzles/PuzzleGenerator');
const BossGenerator = require('./bosses/BossGenerator');
const EncounterBuilder = require('./encounters/EncounterBuilder');
const EnvironmentalStorytelling = require('./storytelling/EnvironmentalStorytelling');

class ContentPopulator {
  constructor(config, logger) {
    this.config = config;
    this.logger = logger;

    // Initialize content generators
    this.enemyPlacer = new EnemyPlacer(config, logger);
    this.lootGenerator = new LootGenerator(config, logger);
    this.trapPlacer = new TrapPlacer(config, logger);
    this.puzzleGenerator = new PuzzleGenerator(config, logger);
    this.bossGenerator = new BossGenerator(config, logger);
    this.encounterBuilder = new EncounterBuilder(config, logger);
    this.environmentalStorytelling = new EnvironmentalStorytelling(config, logger);
  }

  /**
   * Populate dungeon with content
   */
  async populate(dungeon, params = {}) {
    const { difficulty, playerLevel, theme, onProgress = () => {} } = params;

    this.logger.info(`Populating ${theme} themed dungeon with content`);

    // Calculate content budgets
    const contentBudget = this.calculateContentBudget(dungeon, difficulty, playerLevel);

    onProgress({ stage: 'enemies', progress: 20 });
    // Place enemies
    await this.placeEnemies(dungeon, contentBudget.enemies, difficulty, playerLevel, theme);

    onProgress({ stage: 'loot', progress: 40 });
    // Generate loot
    await this.generateLoot(dungeon, contentBudget.loot, difficulty, playerLevel, theme);

    onProgress({ stage: 'traps', progress: 60 });
    // Place traps
    await this.placeTraps(dungeon, contentBudget.traps, difficulty, playerLevel, theme);

    onProgress({ stage: 'puzzles', progress: 75 });
    // Generate puzzles
    await this.generatePuzzles(dungeon, contentBudget.puzzles, difficulty, playerLevel, theme);

    onProgress({ stage: 'bosses', progress: 85 });
    // Generate boss encounters
    await this.generateBosses(dungeon, contentBudget.bosses, difficulty, playerLevel, theme);

    onProgress({ stage: 'storytelling', progress: 95 });
    // Add environmental storytelling
    await this.addEnvironmentalStorytelling(dungeon, theme, difficulty);

    onProgress({ stage: 'complete', progress: 100 });

    // Update statistics
    this.updateDungeonStatistics(dungeon);

    this.logger.info('Content population completed');
  }

  /**
   * Calculate content budget based on dungeon size and difficulty
   */
  calculateContentBudget(dungeon, difficulty, playerLevel) {
    let totalArea = 0;
    let totalRooms = 0;
    let totalCorridors = 0;

    dungeon.floors.forEach(floor => {
      totalArea += floor.grid.length * floor.grid[0].length;
      totalRooms += floor.rooms.length;
      totalCorridors += floor.corridors.length;
    });

    // Base calculations
    const baseEnemyDensity = 0.05; // 5% of floor area
    const baseLootDensity = 0.03; // 3% of floor area
    const baseTrapDensity = 0.02; // 2% of floor area

    // Difficulty modifiers
    const difficultyMultiplier = 1 + (difficulty - 1) * 0.3;
    const levelMultiplier = 1 + (playerLevel - 1) * 0.1;

    // Calculate final budgets
    return {
      enemies: {
        total: Math.floor(totalArea * baseEnemyDensity * difficultyMultiplier),
        perRoom: Math.floor(totalRooms * 1.5 * difficultyMultiplier),
        perCorridor: Math.floor(totalCorridors * 0.8 * difficultyMultiplier)
      },
      loot: {
        total: Math.floor(totalArea * baseLootDensity * levelMultiplier),
        perRoom: Math.floor(totalRooms * 0.8 * levelMultiplier),
        quality: this.calculateLootQuality(difficulty, playerLevel)
      },
      traps: {
        total: Math.floor(totalArea * baseTrapDensity * difficultyMultiplier),
        perRoom: Math.floor(totalRooms * 0.6 * difficultyMultiplier),
        complexity: Math.min(5, Math.floor(difficulty))
      },
      puzzles: {
        total: Math.floor(totalRooms * 0.3 * difficultyMultiplier),
        complexity: Math.min(5, Math.floor(difficulty * 1.2))
      },
      bosses: {
        total: Math.floor(dungeon.floors.length * 0.8),
        difficulty: difficulty,
        powerLevel: this.calculateBossPowerLevel(difficulty, playerLevel)
      }
    };
  }

  /**
   * Calculate loot quality based on difficulty and player level
   */
  calculateLootQuality(difficulty, playerLevel) {
    const baseQuality = Math.min(5, Math.floor(playerLevel / 5) + 1);
    const difficultyBonus = Math.floor(difficulty * 0.5);
    return Math.min(5, baseQuality + difficultyBonus);
  }

  /**
   * Calculate boss power level
   */
  calculateBossPowerLevel(difficulty, playerLevel) {
    return Math.floor(playerLevel * 1.5 + difficulty * 10);
  }

  /**
   * Place enemies throughout the dungeon
   */
  async placeEnemies(dungeon, enemyBudget, difficulty, playerLevel, theme) {
    for (let floorIndex = 0; floorIndex < dungeon.floors.length; floorIndex++) {
      const floor = dungeon.floors[floorIndex];
      const floorDifficulty = difficulty + (floorIndex * 0.3); // Scale per floor

      // Place enemies in rooms
      const roomEnemies = this.enemyPlacer.placeEnemiesInRooms(
        floor.rooms,
        Math.floor(enemyBudget.perRoom / dungeon.floors.length),
        floorDifficulty,
        playerLevel,
        theme
      );

      // Place enemies in corridors
      const corridorEnemies = this.enemyPlacer.placeEnemiesInCorridors(
        floor.corridors,
        Math.floor(enemyBudget.perCorridor / dungeon.floors.length),
        floorDifficulty,
        playerLevel,
        theme
      );

      // Build encounters
      floor.spawns = await this.encounterBuilder.buildEncounters(
        [...roomEnemies, ...corridorEnemies],
        floor.rooms,
        floorDifficulty
      );

      floor.enemyPatrols = this.enemyPlacer.generatePatrols(
        floor.spawns,
        floor.corridors,
        theme
      );
    }
  }

  /**
   * Generate loot throughout the dungeon
   */
  async generateLoot(dungeon, lootBudget, difficulty, playerLevel, theme) {
    for (let floorIndex = 0; floorIndex < dungeon.floors.length; floorIndex++) {
      const floor = dungeon.floors[floorIndex];
      const floorDifficulty = difficulty + (floorIndex * 0.2);

      // Generate loot for rooms
      const roomLoot = await this.lootGenerator.generateRoomLoot(
        floor.rooms,
        Math.floor(lootBudget.perRoom / dungeon.floors.length),
        lootBudget.quality,
        floorDifficulty,
        playerLevel,
        theme
      );

      // Generate special loot for treasure rooms
      const treasureLoot = await this.lootGenerator.generateTreasureRoomLoot(
        floor.rooms.filter(r => r.type === 'treasure'),
        lootBudget.quality * 1.5,
        floorDifficulty,
        playerLevel,
        theme
      );

      // Generate hidden loot
      const hiddenLoot = await this.lootGenerator.generateHiddenLoot(
        floor,
        Math.floor(lootBudget.total * 0.2 / dungeon.floors.length),
        lootBudget.quality,
        theme
      );

      floor.loot = [...roomLoot, ...treasureLoot, ...hiddenLoot];

      // Generate quest items
      floor.questItems = await this.lootGenerator.generateQuestItems(
        floor,
        difficulty,
        theme
      );
    }
  }

  /**
   * Place traps throughout the dungeon
   */
  async placeTraps(dungeon, trapBudget, difficulty, playerLevel, theme) {
    for (let floorIndex = 0; floorIndex < dungeon.floors.length; floorIndex++) {
      const floor = dungeon.floors[floorIndex];
      const floorDifficulty = difficulty + (floorIndex * 0.25);

      // Place traps in rooms
      const roomTraps = await this.trapPlacer.placeRoomTraps(
        floor.rooms,
        Math.floor(trapBudget.perRoom / dungeon.floors.length),
        trapBudget.complexity,
        floorDifficulty,
        theme
      );

      // Place traps in corridors
      const corridorTraps = await this.trapPlacer.placeCorridorTraps(
        floor.corridors,
        Math.floor(trapBudget.total * 0.4 / dungeon.floors.length),
        trapBudget.complexity,
        theme
      );

      // Place environmental hazards
      const environmentalHazards = await this.trapPlacer.placeEnvironmentalHazards(
        floor,
        floorDifficulty,
        theme
      );

      floor.traps = [...roomTraps, ...corridorTraps, ...environmentalHazards];

      // Create trap combinations
      floor.trapCombinations = this.trapPlacer.createTrapCombinations(
        floor.traps,
        floor.rooms,
        theme
      );
    }
  }

  /**
   * Generate puzzles throughout the dungeon
   */
  async generatePuzzles(dungeon, puzzleBudget, difficulty, playerLevel, theme) {
    for (let floorIndex = 0; floorIndex < dungeon.floors.length; floorIndex++) {
      const floor = dungeon.floors[floorIndex];
      const floorDifficulty = difficulty + (floorIndex * 0.15);

      // Generate room puzzles
      const roomPuzzles = await this.puzzleGenerator.generateRoomPuzzles(
        floor.rooms.filter(r => r.type === 'puzzle' || r.type === 'secret'),
        Math.floor(puzzleBudget.total / dungeon.floors.length),
        puzzleBudget.complexity,
        floorDifficulty,
        playerLevel,
        theme
      );

      // Generate environmental puzzles
      const environmentalPuzzles = await this.puzzleGenerator.generateEnvironmentalPuzzles(
        floor,
        puzzleBudget.complexity,
        theme
      );

      // Generate riddle puzzles
      const riddlePuzzles = await this.puzzleGenerator.generateRiddlePuzzles(
        floor.rooms.filter(r => r.type === 'boss' || r.type === 'treasure'),
        floorDifficulty,
        theme
      );

      floor.puzzles = [...roomPuzzles, ...environmentalPuzzles, ...riddlePuzzles];

      // Create puzzle sequences
      floor.puzzleSequences = this.puzzleGenerator.createPuzzleSequences(
        floor.puzzles,
        floor.rooms
      );
    }
  }

  /**
   * Generate boss encounters
   */
  async generateBosses(dungeon, bossBudget, difficulty, playerLevel, theme) {
    for (let floorIndex = 0; floorIndex < dungeon.floors.length; floorIndex++) {
      const floor = dungeon.floors[floorIndex];
      const floorDifficulty = difficulty + (floorIndex * 0.4);

      // Find boss rooms
      const bossRooms = floor.rooms.filter(r => r.type === 'boss');

      for (const bossRoom of bossRooms) {
        // Generate boss encounter
        const boss = await this.bossGenerator.generateBoss(
          bossRoom,
          floorDifficulty,
          playerLevel,
          theme,
          bossBudget.powerLevel
        );

        // Generate boss minions
        const minions = await this.bossGenerator.generateMinions(
          bossRoom,
          boss,
          floorDifficulty,
          theme
        );

        // Generate boss mechanics
        const mechanics = await this.bossGenerator.generateBossMechanics(
          boss,
          bossRoom,
          theme
        );

        // Generate boss loot
        const bossLoot = await this.bossGenerator.generateBossLoot(
          boss,
          bossBudget.powerLevel,
          playerLevel,
          theme
        );

        floor.bosses = floor.bosses || [];
        floor.bosses.push({
          ...boss,
          room: bossRoom.id,
          minions,
          mechanics,
          loot: bossLoot,
          encounter: {
            phases: this.bossGenerator.createBossPhases(boss),
            triggers: this.bossGenerator.createBossTriggers(boss, bossRoom),
            rewards: bossLoot
          }
        });
      }
    }
  }

  /**
   * Add environmental storytelling elements
   */
  async addEnvironmentalStorytelling(dungeon, theme, difficulty) {
    for (let floorIndex = 0; floorIndex < dungeon.floors.length; floorIndex++) {
      const floor = dungeon.floors[floorIndex];

      // Generate story elements
      const storyElements = await this.environmentalStorytelling.generateStoryElements(
        floor,
        theme,
        difficulty
      );

      // Generate lore fragments
      const loreFragments = await this.environmentalStorytelling.generateLoreFragments(
        floor,
        theme
      );

      // Generate environmental clues
      const environmentalClues = await this.environmentalStorytelling.generateEnvironmentalClues(
        floor,
        theme
      );

      // Create narrative flow
      const narrativeFlow = this.environmentalStorytelling.createNarrativeFlow(
        floor,
        storyElements
      );

      floor.storytelling = {
        elements: storyElements,
        loreFragments,
        environmentalClues,
        narrativeFlow,
        theme: theme,
        atmosphere: this.calculateAtmosphere(floor, theme)
      };
    }
  }

  /**
   * Calculate atmosphere for floor
   */
  calculateAtmosphere(floor, theme) {
    const atmosphereFactors = {
      enemyDensity: floor.spawns.length / (floor.rooms.length + 1),
      trapDensity: floor.traps.length / (floor.rooms.length + 1),
      lootDensity: floor.loot.length / (floor.rooms.length + 1),
      puzzleComplexity: floor.puzzles.length > 0 ?
        floor.puzzles.reduce((sum, p) => sum + (p.complexity || 1), 0) / floor.puzzles.length : 0
    };

    let atmosphere = 'neutral';

    if (atmosphereFactors.enemyDensity > 2) atmosphere = 'dangerous';
    else if (atmosphereFactors.trapDensity > 1.5) atmosphere = 'treacherous';
    else if (atmosphereFactors.lootDensity > 2) atmosphere = 'rewarding';
    else if (atmosphereFactors.puzzleComplexity > 3) atmosphere = 'mysterious';

    return {
      primary: atmosphere,
      factors: atmosphereFactors,
      theme: theme
    };
  }

  /**
   * Update dungeon statistics
   */
  updateDungeonStatistics(dungeon) {
    dungeon.statistics = {
      totalRooms: 0,
      totalCorridors: 0,
      totalEnemies: 0,
      totalLoot: 0,
      totalTraps: 0,
      totalPuzzles: 0,
      totalBosses: 0,
      difficultyRating: 0,
      estimatedPlayTime: 0
    };

    dungeon.floors.forEach(floor => {
      dungeon.statistics.totalRooms += floor.rooms.length;
      dungeon.statistics.totalCorridors += floor.corridors.length;
      dungeon.statistics.totalEnemies += floor.spawns.length;
      dungeon.statistics.totalLoot += floor.loot.length;
      dungeon.statistics.totalTraps += floor.traps.length;
      dungeon.statistics.totalPuzzles += floor.puzzles.length;
      dungeon.statistics.totalBosses += (floor.bosses || []).length;
    });

    // Calculate difficulty rating
    dungeon.statistics.difficultyRating = this.calculateDifficultyRating(dungeon);

    // Estimate play time
    dungeon.statistics.estimatedPlayTime = this.estimatePlayTime(dungeon);
  }

  /**
   * Calculate overall difficulty rating
   */
  calculateDifficultyRating(dungeon) {
    const stats = dungeon.statistics;

    // Base calculation
    let rating = 0;
    rating += stats.totalEnemies * 0.1;
    rating += stats.totalTraps * 0.15;
    rating += stats.totalPuzzles * 0.2;
    rating += stats.totalBosses * 2.0;

    // Normalize to 1-10 scale
    return Math.min(10, Math.max(1, Math.round(rating / dungeon.floors.length)));
  }

  /**
   * Estimate play time in minutes
   */
  estimatePlayTime(dungeon) {
    const stats = dungeon.statistics;

    // Base time estimates per content type
    const timePerEnemy = 2; // minutes
    const timePerTrap = 1.5;
    const timePerPuzzle = 5;
    const timePerBoss = 15;
    const timePerRoom = 3; // exploration

    let totalMinutes = 0;
    totalMinutes += stats.totalEnemies * timePerEnemy;
    totalMinutes += stats.totalTraps * timePerTrap;
    totalMinutes += stats.totalPuzzles * timePerPuzzle;
    totalMinutes += stats.totalBosses * timePerBoss;
    totalMinutes += stats.totalRooms * timePerRoom;

    // Add buffer time
    totalMinutes *= 1.2;

    return Math.round(totalMinutes);
  }

  /**
   * Get content at specific position
   */
  getContentAt(dungeon, floorIndex, x, y) {
    const floor = dungeon.floors[floorIndex];
    if (!floor) return null;

    return {
      enemies: this.enemyPlacer.getEnemiesAt(floor, x, y),
      loot: this.lootGenerator.getLootAt(floor, x, y),
      traps: this.trapPlacer.getTrapsAt(floor, x, y),
      puzzles: this.puzzleGenerator.getPuzzlesAt(floor, x, y),
      bosses: this.bossGenerator.getBossesAt(floor, x, y),
      storytelling: this.environmentalStorytelling.getStoryAt(floor, x, y)
    };
  }

  /**
   * Modify content (for DM overrides)
   */
  modifyContent(dungeon, floorIndex, modifications) {
    const floor = dungeon.floors[floorIndex];
    if (!floor) return false;

    let modified = false;

    if (modifications.enemies) {
      this.enemyPlacer.modifyEnemies(floor, modifications.enemies);
      modified = true;
    }

    if (modifications.loot) {
      this.lootGenerator.modifyLoot(floor, modifications.loot);
      modified = true;
    }

    if (modifications.traps) {
      this.trapPlacer.modifyTraps(floor, modifications.traps);
      modified = true;
    }

    if (modifications.puzzles) {
      this.puzzleGenerator.modifyPuzzles(floor, modifications.puzzles);
      modified = true;
    }

    if (modifications.bosses) {
      this.bossGenerator.modifyBosses(floor, modifications.bosses);
      modified = true;
    }

    if (modified) {
      this.updateDungeonStatistics(dungeon);
    }

    return modified;
  }

  /**
   * Export content configuration
   */
  exportContent(dungeon) {
    return {
      enemies: dungeon.floors.map(floor => floor.spawns),
      loot: dungeon.floors.map(floor => floor.loot),
      traps: dungeon.floors.map(floor => floor.traps),
      puzzles: dungeon.floors.map(floor => floor.puzzles),
      bosses: dungeon.floors.map(floor => floor.bosses || []),
      storytelling: dungeon.floors.map(floor => floor.storytelling),
      statistics: dungeon.statistics
    };
  }

  /**
   * Import content configuration
   */
  importContent(dungeon, contentData) {
    for (let floorIndex = 0; floorIndex < dungeon.floors.length; floorIndex++) {
      const floor = dungeon.floors[floorIndex];
      const data = contentData[floorIndex];

      if (data) {
        if (data.enemies) floor.spawns = data.enemies;
        if (data.loot) floor.loot = data.loot;
        if (data.traps) floor.traps = data.traps;
        if (data.puzzles) floor.puzzles = data.puzzles;
        if (data.bosses) floor.bosses = data.bosses;
        if (data.storytelling) floor.storytelling = data.storytelling;
      }
    }

    this.updateDungeonStatistics(dungeon);
  }
}

module.exports = ContentPopulator;