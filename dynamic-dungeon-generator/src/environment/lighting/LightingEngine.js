/**
 * Lighting Engine
 * Manages dynamic lighting, shadows, and illumination for dungeons
 */

const MathUtils = require('../../utils/MathUtils');

class LightingEngine {
  constructor(config, logger) {
    this.config = config;
    this.logger = logger;
    this.lightCache = new Map();
  }

  /**
   * Calculate lighting for an entire floor
   */
  calculateFloorLighting(grid, theme, rooms, corridors) {
    const width = grid[0].length;
    const height = grid.length;

    // Initialize lighting grid
    const lightingGrid = Array(height).fill().map(() =>
      Array(width).fill().map(() => ({
        brightness: 0,
        color: { r: 0, g: 0, b: 0 },
        sources: [],
        shadows: []
      }))
    );

    // Get theme base lighting
    const themeLighting = this.getThemeBaseLighting(theme);

    // Apply ambient lighting
    this.applyAmbientLighting(lightingGrid, themeLighting.ambient);

    // Apply room lighting
    for (const room of rooms) {
      this.applyRoomLighting(lightingGrid, room, themeLighting);
    }

    // Apply corridor lighting
    for (const corridor of corridors) {
      this.applyCorridorLighting(lightingGrid, corridor, themeLighting);
    }

    // Apply global light sources
    this.applyGlobalLightSources(lightingGrid, grid, themeLighting);

    // Calculate shadows
    this.calculateShadows(lightingGrid, grid);

    return {
      grid: lightingGrid,
      ambient: themeLighting.ambient,
      sources: this.extractLightSources(lightingGrid),
      globalBrightness: this.calculateGlobalBrightness(lightingGrid)
    };
  }

  /**
   * Get theme base lighting
   */
  getThemeBaseLighting(theme) {
    const themeConfig = this.config.get(`themes.${theme}`, {});

    return {
      ambient: {
        brightness: themeConfig.brightness || 0.4,
        color: this.parseColor(themeConfig.color || '#ffffff')
      },
      attenuation: themeConfig.lightAttenuation || 0.1,
      shadowIntensity: themeConfig.shadowIntensity || 0.7,
      lightSources: themeConfig.lightSources || []
    };
  }

  /**
   * Parse color string to RGB
   */
  parseColor(colorString) {
    const hex = colorString.replace('#', '');
    return {
      r: parseInt(hex.substr(0, 2), 16) / 255,
      g: parseInt(hex.substr(2, 2), 16) / 255,
      b: parseInt(hex.substr(4, 2), 16) / 255
    };
  }

  /**
   * Apply ambient lighting to grid
   */
  applyAmbientLighting(lightingGrid, ambient) {
    for (let y = 0; y < lightingGrid.length; y++) {
      for (let x = 0; x < lightingGrid[0].length; x++) {
        lightingGrid[y][x].brightness = ambient.brightness;
        lightingGrid[y][x].color = { ...ambient.color };
      }
    }
  }

  /**
   * Apply room lighting
   */
  applyRoomLighting(lightingGrid, room, themeLighting) {
    if (!room.lighting) return;

    // Room-specific light sources
    for (const source of room.lighting.sources || []) {
      this.applyLightSource(lightingGrid, source, themeLighting);
    }

    // Room-specific brightness modifier
    const roomModifier = room.lighting.brightness || 1.0;

    for (let y = room.y; y < room.y + room.height; y++) {
      for (let x = room.x; x < room.x + room.width; x++) {
        if (this.isInBounds(lightingGrid, x, y)) {
          lightingGrid[y][x].brightness *= roomModifier;

          // Apply room color tint
          if (room.lighting.color) {
            const roomColor = this.parseColor(room.lighting.color);
            this.blendColors(lightingGrid[y][x].color, roomColor, 0.3);
          }
        }
      }
    }
  }

  /**
   * Apply corridor lighting
   */
  applyCorridorLighting(lightingGrid, corridor, themeLighting) {
    if (!corridor.lighting) return;

    // Corridor light sources
    for (const source of corridor.lighting.sources || []) {
      this.applyLightSource(lightingGrid, source, themeLighting);
    }

    // Apply lighting along corridor path
    if (corridor.path) {
      for (const point of corridor.path) {
        if (this.isInBounds(lightingGrid, point.x, point.y)) {
          const currentLighting = lightingGrid[point.y][point.x];
          currentLighting.brightness = Math.min(1.0, currentLighting.brightness * 1.2);
        }
      }
    }
  }

  /**
   * Apply a light source to the grid
   */
  applyLightSource(lightingGrid, source, themeLighting) {
    const { x, y, radius, intensity, color } = source;
    const sourceColor = this.parseColor(color || '#ffffff');

    for (let dy = -radius; dy <= radius; dy++) {
      for (let dx = -radius; dx <= radius; dx++) {
        const gridX = x + dx;
        const gridY = y + dy;

        if (this.isInBounds(lightingGrid, gridX, gridY)) {
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance <= radius) {
            // Calculate falloff
            const falloff = Math.max(0, 1 - (distance / radius) * themeLighting.attenuation);
            const lightIntensity = intensity * falloff;

            // Add to existing lighting
            const currentLighting = lightingGrid[gridY][gridX];
            currentLighting.brightness = Math.min(1.0, currentLighting.brightness + lightIntensity);

            // Blend colors
            this.blendColors(currentLighting.color, sourceColor, lightIntensity * 0.5);

            // Track source
            currentLighting.sources.push({
              x, y,
              intensity: lightIntensity,
              color: sourceColor,
              distance
            });
          }
        }
      }
    }
  }

  /**
   * Apply global light sources (sunlight, moonlight, etc.)
   */
  applyGlobalLightSources(lightingGrid, grid, themeLighting) {
    // Check for outdoor areas
    const outdoorTiles = this.findOutdoorTiles(grid);

    for (const tile of outdoorTiles) {
      // Apply directional light
      const directionalLight = {
        x: tile.x,
        y: tile.y,
        radius: 10,
        intensity: themeLighting.ambient.brightness * 1.5,
        color: '#ffffcc' // Warm sunlight
      };

      this.applyLightSource(lightingGrid, directionalLight, themeLighting);
    }
  }

  /**
   * Find outdoor tiles
   */
  findOutdoorTiles(grid) {
    const outdoorTiles = [];
    const outdoorTileTypes = ['outdoor_floor', 'courtyard', 'balcony'];

    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[0].length; x++) {
        if (outdoorTileTypes.includes(grid[y][x])) {
          outdoorTiles.push({ x, y });
        }
      }
    }

    return outdoorTiles;
  }

  /**
   * Calculate shadows
   */
  calculateShadows(lightingGrid, grid) {
    // Find all light sources
    const lightSources = [];
    for (let y = 0; y < lightingGrid.length; y++) {
      for (let x = 0; x < lightingGrid[0].length; x++) {
        const cell = lightingGrid[y][x];
        for (const source of cell.sources) {
          if (source.intensity > 0.5) {
            lightSources.push({ ...source, gridX: x, gridY: y });
          }
        }
      }
    }

    // Cast shadows from walls
    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[0].length; x++) {
        if (grid[y][x] === 'wall' || grid[y][x].includes('wall')) {
          this.castShadowsFromObstacle(lightingGrid, x, y, lightSources, grid);
        }
      }
    }
  }

  /**
   * Cast shadows from an obstacle
   */
  castShadowsFromObstacle(lightingGrid, obstacleX, obstacleY, lightSources, grid) {
    for (const source of lightSources) {
      const shadowLength = 8;
      const dx = obstacleX - source.gridX;
      const dy = obstacleY - source.gridY;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance > 0 && distance < 15) {
        // Calculate shadow direction
        const shadowDirX = (dx / distance) * 2;
        const shadowDirY = (dy / distance) * 2;

        // Trace shadow path
        for (let i = 1; i <= shadowLength; i++) {
          const shadowX = Math.round(obstacleX + shadowDirX * i);
          const shadowY = Math.round(obstacleY + shadowDirY * i);

          if (this.isInBounds(lightingGrid, shadowX, shadowY)) {
            const shadowIntensity = (1 - i / shadowLength) * 0.5;
            const cell = lightingGrid[shadowY][shadowX];

            cell.brightness = Math.max(0, cell.brightness - shadowIntensity);
            cell.shadows.push({
              sourceX: source.x,
              sourceY: source.y,
              obstacleX,
              obstacleY,
              intensity: shadowIntensity
            });
          } else {
            break;
          }
        }
      }
    }
  }

  /**
   * Calculate room lighting (for individual rooms)
   */
  calculateRoomLighting(room, ambientLighting) {
    const lighting = {
      brightness: ambientLighting.brightness,
      color: { ...ambientLighting.color },
      sources: []
    };

    // Add room-specific light sources
    if (room.theme === 'dragonLair') {
      lighting.sources.push({
        type: 'magma',
        x: room.centerX,
        y: room.centerY,
        radius: 6,
        intensity: 0.8,
        color: '#ff6600'
      });
    } else if (room.theme === 'undeadCrypt') {
      lighting.sources.push({
        type: 'spirit',
        x: room.centerX,
        y: room.centerY,
        radius: 4,
        intensity: 0.4,
        color: '#9999ff'
      });
    }

    // Add torches for normal rooms
    if (room.type === 'normal' || room.type === 'entrance') {
      const torchCount = Math.floor(room.width / 5) + Math.floor(room.height / 5);
      for (let i = 0; i < torchCount; i++) {
        const torchPos = this.getRandomRoomPosition(room);
        lighting.sources.push({
          type: 'torch',
          x: torchPos.x,
          y: torchPos.y,
          radius: 3,
          intensity: 0.6,
          color: '#ff9966'
        });
      }
    }

    return lighting;
  }

  /**
   * Calculate corridor lighting
   */
  calculateCorridorLighting(corridor, ambientLighting) {
    const lighting = {
      brightness: ambientLighting.brightness * 0.8,
      color: { ...ambientLighting.color },
      sources: []
    };

    // Add lights along corridor
    if (corridor.path) {
      const interval = Math.max(1, Math.floor(corridor.path.length / 4));
      for (let i = interval; i < corridor.path.length; i += interval) {
        const point = corridor.path[i];
        lighting.sources.push({
          type: 'sconce',
          x: point.x,
          y: point.y,
          radius: 2,
          intensity: 0.5,
          color: '#ffcc66'
        });
      }
    }

    return lighting;
  }

  /**
   * Update lighting dynamically
   */
  updateLighting(floor, deltaTime) {
    // Animate light sources
    for (const source of floor.lighting.sources) {
      if (source.type === 'torch' || source.type === 'flame') {
        // Flickering effect
        source.intensity = 0.6 + Math.sin(Date.now() * 0.01) * 0.2;
      } else if (source.type === 'spirit') {
        // Pulsing effect
        source.intensity = 0.4 + Math.sin(Date.now() * 0.005) * 0.3;
      }
    }

    // Recalculate lighting grid if needed
    if (this.config.get('environment.dynamic_lighting', false)) {
      this.calculateFloorLighting(
        floor.grid,
        floor.theme,
        floor.rooms,
        floor.corridors
      );
    }
  }

  /**
   * Get lighting at specific position
   */
  getLightingAt(floor, x, y) {
    if (!floor.lighting || !floor.lighting.grid) {
      return { brightness: 0.5, color: { r: 1, g: 1, b: 1 } };
    }

    if (this.isInBounds(floor.lighting.grid, x, y)) {
      return floor.lighting.grid[y][x];
    }

    return { brightness: 0, color: { r: 0, g: 0, b: 0 } };
  }

  /**
   * Modify lighting (for DM overrides)
   */
  modifyLighting(floor, modifications) {
    if (!floor.lighting) return;

    if (modifications.ambient) {
      floor.lighting.ambient = { ...floor.lighting.ambient, ...modifications.ambient };
      this.applyAmbientLighting(floor.lighting.grid, floor.lighting.ambient);
    }

    if (modifications.addSource) {
      this.applyLightSource(floor.lighting.grid, modifications.addSource, floor.lighting);
    }

    if (modifications.removeSource) {
      this.removeLightSource(floor.lighting.grid, modifications.removeSource);
    }

    if (modifications.brightness) {
      this.setBrightness(floor.lighting.grid, modifications.brightness);
    }
  }

  /**
   * Remove light source
   */
  removeLightSource(lightingGrid, sourceToRemove) {
    // Find and remove the specific light source
    for (let y = 0; y < lightingGrid.length; y++) {
      for (let x = 0; x < lightingGrid[0].length; x++) {
        const cell = lightingGrid[y][x];
        cell.sources = cell.sources.filter(source =>
          source.x !== sourceToRemove.x || source.y !== sourceToRemove.y
        );
      }
    }
  }

  /**
   * Set brightness for entire floor
   */
  setBrightness(lightingGrid, brightness) {
    for (let y = 0; y < lightingGrid.length; y++) {
      for (let x = 0; x < lightingGrid[0].length; x++) {
        lightingGrid[y][x].brightness = brightness;
      }
    }
  }

  /**
   * Extract light sources from lighting grid
   */
  extractLightSources(lightingGrid) {
    const sources = new Map();

    for (let y = 0; y < lightingGrid.length; y++) {
      for (let x = 0; x < lightingGrid[0].length; x++) {
        const cell = lightingGrid[y][x];
        for (const source of cell.sources) {
          const key = `${source.x},${source.y}`;
          if (!sources.has(key)) {
            sources.set(key, source);
          }
        }
      }
    }

    return Array.from(sources.values());
  }

  /**
   * Calculate global brightness
   */
  calculateGlobalBrightness(lightingGrid) {
    let totalBrightness = 0;
    let cellCount = 0;

    for (let y = 0; y < lightingGrid.length; y++) {
      for (let x = 0; x < lightingGrid[0].length; x++) {
        if (lightingGrid[y][x].brightness > 0) {
          totalBrightness += lightingGrid[y][x].brightness;
          cellCount++;
        }
      }
    }

    return cellCount > 0 ? totalBrightness / cellCount : 0;
  }

  /**
   * Helper methods
   */
  isInBounds(grid, x, y) {
    return x >= 0 && x < grid[0].length && y >= 0 && y < grid.length;
  }

  blendColors(color1, color2, factor) {
    color1.r = color1.r * (1 - factor) + color2.r * factor;
    color1.g = color1.g * (1 - factor) + color2.g * factor;
    color1.b = color1.b * (1 - factor) + color2.b * factor;
  }

  getRandomRoomPosition(room) {
    return {
      x: room.x + 1 + Math.floor(Math.random() * (room.width - 2)),
      y: room.y + 1 + Math.floor(Math.random() * (room.height - 2))
    };
  }
}

module.exports = LightingEngine;