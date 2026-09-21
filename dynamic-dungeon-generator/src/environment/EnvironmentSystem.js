/**
 * Environment System
 * Manages environmental effects, lighting, weather, and interactive elements
 */

const LightingEngine = require('./lighting/LightingEngine');
const WeatherSystem = require('./weather/WeatherSystem');
const InteractiveEnvironment = require('./interactive/InteractiveEnvironment');
const VisibilitySystem = require('./visibility/VisibilitySystem');
const EnvironmentalEffects = require('./effects/EnvironmentalEffects');

class EnvironmentSystem {
  constructor(config, logger) {
    this.config = config;
    this.logger = logger;

    // Initialize subsystems
    this.lightingEngine = new LightingEngine(config, logger);
    this.weatherSystem = new WeatherSystem(config, logger);
    this.interactiveEnvironment = new InteractiveEnvironment(config, logger);
    this.visibilitySystem = new VisibilitySystem(config, logger);
    this.environmentalEffects = new EnvironmentalEffects(config, logger);
  }

  /**
   * Setup environment for entire dungeon
   */
  async setup(dungeon, params = {}) {
    const { theme, onProgress = () => {} } = params;

    this.logger.info(`Setting up environment for ${theme} themed dungeon`);

    // Setup lighting
    onProgress({ stage: 'lighting', progress: 20 });
    await this.setupLighting(dungeon, theme);

    // Setup weather (if applicable)
    onProgress({ stage: 'weather', progress: 40 });
    await this.setupWeather(dungeon, theme);

    // Setup interactive elements
    onProgress({ stage: 'interactive', progress: 60 });
    await this.setupInteractiveElements(dungeon, theme);

    // Setup visibility system
    onProgress({ stage: 'visibility', progress: 80 });
    await this.setupVisibility(dungeon, theme);

    // Apply environmental effects
    onProgress({ stage: 'effects', progress: 100 });
    await this.applyEnvironmentalEffects(dungeon, theme);

    this.logger.info('Environment setup completed');
  }

  /**
   * Setup lighting system
   */
  async setupLighting(dungeon, theme) {
    for (let floorIndex = 0; floorIndex < dungeon.floors.length; floorIndex++) {
      const floor = dungeon.floors[floorIndex];

      // Calculate base lighting for the floor
      const floorLighting = this.lightingEngine.calculateFloorLighting(
        floor.grid,
        floor.theme || theme,
        floor.rooms,
        floor.corridors
      );

      floor.lighting = floorLighting;

      // Calculate room-specific lighting
      for (const room of floor.rooms) {
        room.lighting = this.lightingEngine.calculateRoomLighting(
          room,
          floorLighting.ambient
        );
      }

      // Calculate corridor lighting
      for (const corridor of floor.corridors) {
        corridor.lighting = this.lightingEngine.calculateCorridorLighting(
          corridor,
          floorLighting.ambient
        );
      }
    }
  }

  /**
   * Setup weather system (for outdoor or partially exposed dungeons)
   */
  async setupWeather(dungeon, theme) {
    // Check if theme supports weather
    const weatherSupported = this.weatherSystem.isWeatherSupported(theme);

    if (weatherSupported) {
      for (let floorIndex = 0; floorIndex < dungeon.floors.length; floorIndex++) {
        const floor = dungeon.floors[floorIndex];

        // Determine if floor has outdoor areas
        const outdoorAreas = this.identifyOutdoorAreas(floor);

        if (outdoorAreas.length > 0) {
          floor.weather = this.weatherSystem.generateWeather(theme, floor.difficulty);
          floor.outdoorAreas = outdoorAreas;
        } else {
          floor.weather = 'indoor';
          floor.outdoorAreas = [];
        }
      }
    } else {
      // No weather for underground dungeons
      dungeon.floors.forEach(floor => {
        floor.weather = 'none';
        floor.outdoorAreas = [];
      });
    }
  }

  /**
   * Setup interactive elements
   */
  async setupInteractiveElements(dungeon, theme) {
    for (let floorIndex = 0; floorIndex < dungeon.floors.length; floorIndex++) {
      const floor = dungeon.floors[floorIndex];

      // Generate interactive elements for this floor
      const interactiveElements = this.interactiveEnvironment.generateElements(
        floor,
        theme,
        dungeon.metadata.difficulty
      );

      floor.interactiveElements = interactiveElements;

      // Add destructible elements
      floor.destructibleElements = this.interactiveEnvironment.generateDestructibleElements(
        floor,
        theme
      );

      // Add secret passages
      floor.secretPassages = this.interactiveEnvironment.generateSecretPassages(
        floor,
        theme
      );
    }
  }

  /**
   * Setup visibility system
   */
  async setupVisibility(dungeon, theme) {
    for (let floorIndex = 0; floorIndex < dungeon.floors.length; floorIndex++) {
      const floor = dungeon.floors[floorIndex];

      // Calculate visibility layers
      floor.visibility = this.visibilitySystem.calculateVisibility(
        floor.grid,
        floor.lighting,
        theme
      );

      // Setup fog of war if enabled
      if (this.config.get('environment.fog_of_war', true)) {
        floor.fogOfWar = this.visibilitySystem.generateFogOfWar(floor.grid);
      }

      // Calculate line of sight from key points
      floor.lineOfSight = this.visibilitySystem.calculateLineOfSight(
        floor.grid,
        this.getImportantPoints(floor)
      );
    }
  }

  /**
   * Apply environmental effects
   */
  async applyEnvironmentalEffects(dungeon, theme) {
    for (let floorIndex = 0; floorIndex < dungeon.floors.length; floorIndex++) {
      const floor = dungeon.floors[floorIndex];

      // Apply theme-specific environmental effects
      floor.environmentalEffects = this.environmentalEffects.applyEffects(
        floor,
        theme,
        dungeon.metadata.difficulty
      );

      // Apply area-specific effects
      this.applyAreaSpecificEffects(floor, theme);
    }
  }

  /**
   * Identify outdoor areas in a floor
   */
  identifyOutdoorAreas(floor) {
    const outdoorAreas = [];
    const grid = floor.grid;

    // Look for areas that might be exposed to outside
    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[0].length; x++) {
        if (this.isOutdoorTile(grid, x, y)) {
          outdoorAreas.push({ x, y });
        }
      }
    }

    // Group adjacent outdoor tiles into areas
    return this.groupOutdoorAreas(outdoorAreas);
  }

  /**
   * Check if a tile is likely outdoor
   */
  isOutdoorTile(grid, x, y) {
    // Check if tile is on the edge
    if (x === 0 || x === grid[0].length - 1 || y === 0 || y === grid.length - 1) {
      return grid[y][x] === 'floor';
    }

    // Check for special outdoor tiles
    const outdoorTiles = ['outdoor_floor', 'courtyard', 'balcony', 'terrace'];
    return outdoorTiles.includes(grid[y][x]);
  }

  /**
   * Group outdoor tiles into areas
   */
  groupOutdoorAreas(tiles) {
    const areas = [];
    const visited = new Set();

    for (const tile of tiles) {
      const key = `${tile.x},${tile.y}`;
      if (!visited.has(key)) {
        const area = this.floodFillOutdoor(tiles, tile, visited);
        if (area.length > 0) {
          areas.push(area);
        }
      }
    }

    return areas;
  }

  /**
   * Flood fill for outdoor areas
   */
  floodFillOutdoor(tiles, start, visited) {
    const area = [];
    const queue = [start];
    const tileSet = new Set(tiles.map(t => `${t.x},${t.y}`));

    while (queue.length > 0) {
      const current = queue.shift();
      const key = `${current.x},${current.y}`;

      if (visited.has(key) || !tileSet.has(key)) continue;

      visited.add(key);
      area.push(current);

      // Check adjacent tiles
      for (const [dx, dy] of [[0, 1], [1, 0], [0, -1], [-1, 0]]) {
        const adjacent = { x: current.x + dx, y: current.y + dy };
        const adjacentKey = `${adjacent.x},${adjacent.y}`;

        if (!visited.has(adjacentKey) && tileSet.has(adjacentKey)) {
          queue.push(adjacent);
        }
      }
    }

    return area;
  }

  /**
   * Get important points for line of sight calculation
   */
  getImportantPoints(floor) {
    const points = [];

    // Add room centers
    for (const room of floor.rooms) {
      points.push({
        x: room.centerX,
        y: room.centerY,
        type: 'room_center',
        importance: room.type === 'boss' ? 3 : room.type === 'entrance' ? 2 : 1
      });
    }

    // Add corridor junctions
    const junctions = this.findCorridorJunctions(floor);
    for (const junction of junctions) {
      points.push({
        x: junction.x,
        y: junction.y,
        type: 'junction',
        importance: 2
      });
    }

    return points;
  }

  /**
   * Find corridor junctions
   */
  findCorridorJunctions(floor) {
    const junctions = [];
    const grid = floor.grid;

    for (let y = 1; y < grid.length - 1; y++) {
      for (let x = 1; x < grid[0].length - 1; x++) {
        if (grid[y][x] === 'floor') {
          let floorCount = 0;
          for (const [dx, dy] of [[0, 1], [1, 0], [0, -1], [-1, 0]]) {
            if (grid[y + dy][x + dx] === 'floor') {
              floorCount++;
            }
          }

          if (floorCount >= 3) {
            junctions.push({ x, y });
          }
        }
      }
    }

    return junctions;
  }

  /**
   * Apply area-specific effects
   */
  applyAreaSpecificEffects(floor, theme) {
    // Apply room-specific effects
    for (const room of floor.rooms) {
      room.areaEffects = this.environmentalEffects.getRoomEffects(room, theme);
    }

    // Apply corridor-specific effects
    for (const corridor of floor.corridors) {
      corridor.areaEffects = this.environmentalEffects.getCorridorEffects(corridor, theme);
    }
  }

  /**
   * Update environment dynamically
   */
  updateEnvironment(dungeon, deltaTime, playerActions = []) {
    // Update weather
    for (const floor of dungeon.floors) {
      if (floor.weather && floor.weather !== 'none') {
        this.weatherSystem.updateWeather(floor, deltaTime);
      }

      // Update lighting
      this.lightingEngine.updateLighting(floor, deltaTime);

      // Update interactive elements
      this.interactiveEnvironment.updateElements(floor, deltaTime, playerActions);

      // Update environmental effects
      this.environmentalEffects.updateEffects(floor, deltaTime);
    }
  }

  /**
   * Get environmental state at position
   */
  getEnvironmentState(dungeon, floorIndex, x, y) {
    const floor = dungeon.floors[floorIndex];
    if (!floor) return null;

    return {
      lighting: this.lightingEngine.getLightingAt(floor, x, y),
      visibility: this.visibilitySystem.getVisibilityAt(floor, x, y),
      weather: floor.weather,
      interactiveElements: this.interactiveEnvironment.getElementsAt(floor, x, y),
      environmentalEffects: this.environmentalEffects.getEffectsAt(floor, x, y)
    };
  }

  /**
   * Modify environment (for DM overrides)
   */
  modifyEnvironment(dungeon, floorIndex, modifications) {
    const floor = dungeon.floors[floorIndex];
    if (!floor) return false;

    let modified = false;

    if (modifications.lighting) {
      this.lightingEngine.modifyLighting(floor, modifications.lighting);
      modified = true;
    }

    if (modifications.weather) {
      this.weatherSystem.modifyWeather(floor, modifications.weather);
      modified = true;
    }

    if (modifications.interactiveElements) {
      this.interactiveEnvironment.modifyElements(floor, modifications.interactiveElements);
      modified = true;
    }

    if (modifications.effects) {
      this.environmentalEffects.modifyEffects(floor, modifications.effects);
      modified = true;
    }

    return modified;
  }

  /**
   * Export environment configuration
   */
  exportEnvironment(dungeon) {
    return {
      lighting: dungeon.floors.map(floor => floor.lighting),
      weather: dungeon.floors.map(floor => floor.weather),
      interactiveElements: dungeon.floors.map(floor => floor.interactiveElements),
      visibility: dungeon.floors.map(floor => floor.visibility),
      environmentalEffects: dungeon.floors.map(floor => floor.environmentalEffects)
    };
  }

  /**
   * Import environment configuration
   */
  importEnvironment(dungeon, environmentData) {
    for (let floorIndex = 0; floorIndex < dungeon.floors.length; floorIndex++) {
      const floor = dungeon.floors[floorIndex];
      const data = environmentData[floorIndex];

      if (data) {
        if (data.lighting) floor.lighting = data.lighting;
        if (data.weather) floor.weather = data.weather;
        if (data.interactiveElements) floor.interactiveElements = data.interactiveElements;
        if (data.visibility) floor.visibility = data.visibility;
        if (data.environmentalEffects) floor.environmentalEffects = data.environmentalEffects;
      }
    }
  }
}

module.exports = EnvironmentSystem;