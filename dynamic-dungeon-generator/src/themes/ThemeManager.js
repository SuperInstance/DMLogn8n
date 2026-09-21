/**
 * Theme Manager
 * Manages dungeon themes and their visual/environmental characteristics
 */

const ClassicTheme = require('./themes/ClassicTheme');
const UndeadCryptTheme = require('./themes/UndeadCryptTheme');
const DragonLairTheme = require('./themes/DragonLairTheme');
const WizardTowerTheme = require('./themes/WizardTowerTheme');
const DwarvenMinesTheme = require('./themes/DwarvenMinesTheme');
const ElvenSanctuaryTheme = require('./themes/ElvenSanctuaryTheme');
const AbandonedTempleTheme = require('./themes/AbandonedTempleTheme');
const GoblinWarrenTheme = require('./themes/GoblinWarrenTheme');
const IceCavernTheme = require('./themes/IceCavernTheme');
const VolcanicLairTheme = require('./themes/VolcanicLairTheme');
const SwampCaveTheme = require('./themes/SwampCaveTheme');
const CrystalCavesTheme = require('./themes/CrystalCavesTheme');
const SunkenRuinsTheme = require('./themes/SunkenRuinsTheme');
const ShadowRealmTheme = require('./themes/ShadowRealmTheme');
const FeyWildTheme = require('./themes/FeyWildTheme');
const InfernalPortalTheme = require('./themes/InfernalPortalTheme');
const CelestialVaultTheme = require('./themes/CelestialVaultTheme');
const AncientLibraryTheme = require('./themes/AncientLibraryTheme');
const PoisonGardenTheme = require('./themes/PoisonGardenTheme');
const MechanicalLabyrinthTheme = require('./themes/MechanicalLabyrinthTheme');
const LivingMazeTheme = require('./themes/LivingMazeTheme');

class ThemeManager {
  constructor(config, logger) {
    this.config = config;
    this.logger = logger;

    // Initialize all themes
    this.themes = {
      classic: new ClassicTheme(),
      undeadCrypt: new UndeadCryptTheme(),
      dragonLair: new DragonLairTheme(),
      wizardTower: new WizardTowerTheme(),
      dwarvenMines: new DwarvenMinesTheme(),
      elvenSanctuary: new ElvenSanctuaryTheme(),
      abandonedTemple: new AbandonedTempleTheme(),
      goblinWarren: new GoblinWarrenTheme(),
      iceCavern: new IceCavernTheme(),
      volcanicLair: new VolcanicLairTheme(),
      swampCave: new SwampCaveTheme(),
      crystalCaves: new CrystalCavesTheme(),
      sunkenRuins: new SunkenRuinsTheme(),
      shadowRealm: new ShadowRealmTheme(),
      feyWild: new FeyWildTheme(),
      infernalPortal: new InfernalPortalTheme(),
      celestialVault: new CelestialVaultTheme(),
      ancientLibrary: new AncientLibraryTheme(),
      poisonGarden: new PoisonGardenTheme(),
      mechanicalLabyrinth: new MechanicalLabyrinthTheme(),
      livingMaze: new LivingMazeTheme()
    };

    // Theme categories for organization
    this.categories = {
      traditional: ['classic', 'dwarvenMines', 'elvenSanctuary', 'abandonedTemple'],
      supernatural: ['undeadCrypt', 'shadowRealm', 'feyWild', 'infernalPortal', 'celestialVault'],
      elemental: ['dragonLair', 'iceCavern', 'volcanicLair', 'swampCave'],
      magical: ['wizardTower', 'crystalCaves', 'ancientLibrary'],
      creature: ['goblinWarren', 'livingMaze', 'poisonGarden'],
      constructed: ['mechanicalLabyrinth'],
      aquatic: ['sunkenRuins']
    };
  }

  /**
   * Get theme by name
   */
  getTheme(themeName) {
    const theme = this.themes[themeName];
    if (!theme) {
      this.logger.warn(`Theme '${themeName}' not found, using classic theme`);
      return this.themes.classic;
    }
    return theme;
  }

  /**
   * Get all available themes
   */
  getAvailableThemes() {
    return Object.keys(this.themes).map(key => ({
      id: key,
      name: this.themes[key].name,
      description: this.themes[key].description,
      category: this.getThemeCategory(key),
      difficulty: this.themes[key].difficulty,
      environment: this.themes[key].environment,
      recommendedLevel: this.themes[key].recommendedLevel
    }));
  }

  /**
   * Get themes by category
   */
  getThemesByCategory(category) {
    const themeIds = this.categories[category] || [];
    return themeIds.map(id => ({
      id,
      name: this.themes[id].name,
      description: this.themes[id].description
    }));
  }

  /**
   * Get category for a theme
   */
  getThemeCategory(themeId) {
    for (const [category, themes] of Object.entries(this.categories)) {
      if (themes.includes(themeId)) {
        return category;
      }
    }
    return 'other';
  }

  /**
   * Get random theme based on criteria
   */
  getRandomTheme(criteria = {}) {
    const { category, difficulty, environment, playerLevel } = criteria;

    let candidateThemes = Object.keys(this.themes);

    // Filter by category
    if (category && this.categories[category]) {
      candidateThemes = candidateThemes.filter(id => this.categories[category].includes(id));
    }

    // Filter by difficulty
    if (difficulty) {
      candidateThemes = candidateThemes.filter(id => {
        const themeDifficulty = this.themes[id].difficulty;
        return Math.abs(themeDifficulty - difficulty) <= 2;
      });
    }

    // Filter by environment
    if (environment) {
      candidateThemes = candidateThemes.filter(id => {
        const themeEnvironment = this.themes[id].environment;
        return themeEnvironment === environment || themeEnvironment === 'mixed';
      });
    }

    // Filter by player level
    if (playerLevel) {
      candidateThemes = candidateThemes.filter(id => {
        const theme = this.themes[id];
        return playerLevel >= (theme.recommendedLevel - 5) &&
               playerLevel <= (theme.recommendedLevel + 10);
      });
    }

    if (candidateThemes.length === 0) {
      candidateThemes = ['classic']; // Fallback
    }

    const randomThemeId = candidateThemes[Math.floor(Math.random() * candidateThemes.length)];
    return this.themes[randomThemeId];
  }

  /**
   * Apply theme to dungeon layout
   */
  applyTheme(layout, theme) {
    this.logger.info(`Applying theme: ${theme.name}`);

    const themedLayout = {
      ...layout,
      grid: this.applyThemeToGrid(layout.grid, theme),
      rooms: layout.rooms.map(room => this.applyThemeToRoom(room, theme)),
      corridors: layout.corridors.map(corridor => this.applyThemeToCorridor(corridor, theme)),
      environment: theme.environment,
      atmosphere: theme.atmosphere,
      lighting: theme.lighting,
      sounds: theme.sounds,
      specialEffects: theme.specialEffects
    };

    return themedLayout;
  }

  /**
   * Apply theme to grid tiles
   */
  applyThemeToGrid(grid, theme) {
    const themedGrid = grid.map(row => [...row]);

    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < grid[0].length; x++) {
        const tile = grid[y][x];
        const themeTile = this.getThemeTile(tile, theme, x, y);
        themedGrid[y][x] = themeTile;
      }
    }

    // Apply theme-specific modifications
    if (theme.modifyGrid) {
      return theme.modifyGrid(themedGrid);
    }

    return themedGrid;
  }

  /**
   * Get themed tile based on base tile type
   */
  getThemeTile(baseTile, theme, x, y) {
    const tileMapping = theme.tileMapping;

    // Check for special tiles first
    if (tileMapping.special) {
      for (const special of tileMapping.special) {
        if (this.shouldPlaceSpecialTile(special, x, y, theme)) {
          return special.tile;
        }
      }
    }

    // Apply standard tile mapping
    return tileMapping[baseTile] || baseTile;
  }

  /**
   * Check if special tile should be placed
   */
  shouldPlaceSpecialTile(special, x, y, theme) {
    if (special.probability && Math.random() > special.probability) {
      return false;
    }

    if (special.pattern) {
      return this.matchesPattern(x, y, special.pattern);
    }

    if (special.condition) {
      return special.condition(x, y, theme);
    }

    return true;
  }

  /**
   * Check if position matches pattern
   */
  matchesPattern(x, y, pattern) {
    switch (pattern.type) {
      case 'checkerboard':
        return (x + y) % 2 === 0;
      case 'diagonal':
        return x % pattern.spacing === 0 || y % pattern.spacing === 0;
      case 'perimeter':
        return x < pattern.margin || y < pattern.margin;
      case 'center':
        const centerX = Math.floor(pattern.width / 2);
        const centerY = Math.floor(pattern.height / 2);
        const distance = Math.sqrt((x - centerX) ** 2 + (y - centerY) ** 2);
        return distance < pattern.radius;
      default:
        return false;
    }
  }

  /**
   * Apply theme to room
   */
  applyThemeToRoom(room, theme) {
    const themedRoom = {
      ...room,
      theme: theme.name,
      tiles: theme.roomTiles[room.type] || theme.roomTiles.normal,
      decorations: this.generateRoomDecorations(room, theme),
      lighting: this.calculateRoomLighting(room, theme),
      atmosphere: theme.roomAtmosphere[room.type] || theme.atmosphere
    };

    // Apply room type modifications
    if (theme.modifyRoom) {
      return theme.modifyRoom(themedRoom);
    }

    return themedRoom;
  }

  /**
   * Apply theme to corridor
   */
  applyThemeToCorridor(corridor, theme) {
    const themedCorridor = {
      ...corridor,
      theme: theme.name,
      tiles: theme.corridorTiles[corridor.type] || theme.corridorTiles.normal,
      decorations: this.generateCorridorDecorations(corridor, theme),
      lighting: theme.corridorLighting || theme.lighting
    };

    // Apply corridor type modifications
    if (theme.modifyCorridor) {
      return theme.modifyCorridor(themedCorridor);
    }

    return themedCorridor;
  }

  /**
   * Generate room decorations based on theme
   */
  generateRoomDecorations(room, theme) {
    const decorations = [];
    const decorationTypes = theme.decorations[room.type] || theme.decorations.normal;

    for (const decoType of decorationTypes) {
      if (Math.random() < decoType.probability) {
        const count = Math.floor(Math.random() * (decoType.maxCount - decoType.minCount + 1)) + decoType.minCount;

        for (let i = 0; i < count; i++) {
          const position = this.getRandomPositionInRoom(room);
          decorations.push({
            type: decoType.type,
            x: position.x,
            y: position.y,
            properties: decoType.properties || {}
          });
        }
      }
    }

    return decorations;
  }

  /**
   * Generate corridor decorations
   */
  generateCorridorDecorations(corridor, theme) {
    const decorations = [];
    const decorationTypes = theme.corridorDecorations || [];

    for (const decoType of decorationTypes) {
      if (Math.random() < decoType.probability) {
        // Place decorations along corridor path
        const interval = Math.max(1, Math.floor(corridor.path.length / decoType.maxCount));

        for (let i = interval; i < corridor.path.length; i += interval * 2) {
          const position = corridor.path[i];
          decorations.push({
            type: decoType.type,
            x: position.x,
            y: position.y,
            properties: decoType.properties || {}
          });
        }
      }
    }

    return decorations;
  }

  /**
   * Get random position within room
   */
  getRandomPositionInRoom(room) {
    const x = room.x + 1 + Math.floor(Math.random() * (room.width - 2));
    const y = room.y + 1 + Math.floor(Math.random() * (room.height - 2));
    return { x, y };
  }

  /**
   * Calculate room lighting
   */
  calculateRoomLighting(room, theme) {
    let baseLighting = theme.lighting.brightness;

    // Adjust for room type
    switch (room.type) {
      case 'entrance':
        baseLighting *= 1.2;
        break;
      case 'boss':
        baseLighting *= 0.7;
        break;
      case 'treasure':
        baseLighting *= 0.9;
        break;
      case 'secret':
        baseLighting *= 0.5;
        break;
    }

    // Adjust for room size
    const roomArea = room.width * room.height;
    if (roomArea > 100) {
      baseLighting *= 0.9; // Large rooms are darker
    } else if (roomArea < 25) {
      baseLighting *= 1.1; // Small rooms are brighter
    }

    return {
      brightness: Math.max(0, Math.min(1, baseLighting)),
      color: theme.lighting.color,
      sources: this.generateLightSources(room, theme)
    };
  }

  /**
   * Generate light sources in room
   */
  generateLightSources(room, theme) {
    const sources = [];

    if (theme.lightSources) {
      for (const sourceType of theme.lightSources) {
        if (Math.random() < sourceType.probability) {
          const position = this.getRandomPositionInRoom(room);
          sources.push({
            type: sourceType.type,
            x: position.x,
            y: position.y,
            radius: sourceType.radius,
            intensity: sourceType.intensity,
            color: sourceType.color
          });
        }
      }
    }

    return sources;
  }

  /**
   * Get theme-appropriate content suggestions
   */
  getContentSuggestions(theme) {
    return {
      enemies: theme.enemyTypes || [],
      treasures: theme.treasureTypes || [],
      traps: theme.trapTypes || [],
      puzzles: theme.puzzleTypes || [],
      ambientSounds: theme.ambientSounds || [],
      music: theme.backgroundMusic || []
    };
  }

  /**
   * Get theme-specific difficulty modifiers
   */
  getDifficultyModifiers(theme) {
    return {
      enemyDamage: theme.difficultyModifiers?.enemyDamage || 1.0,
      trapDamage: theme.difficultyModifiers?.trapDamage || 1.0,
      puzzleComplexity: theme.difficultyModifiers?.puzzleComplexity || 1.0,
      visibility: theme.difficultyModifiers?.visibility || 1.0,
      environmentalHazards: theme.difficultyModifiers?.environmentalHazards || 1.0
    };
  }

  /**
   * Blend multiple themes
   */
  blendThemes(themeNames, weights = null) {
    const themes = themeNames.map(name => this.getTheme(name));
    const blendedTheme = {
      name: `Blended: ${themeNames.join(' + ')}`,
      description: `A blend of ${themeNames.join(', ')}`,
      tileMapping: {},
      roomTiles: {},
      decorations: {},
      lighting: { brightness: 0.5, color: '#ffffff' },
      atmosphere: 'mixed'
    };

    // Simple weighted averaging of properties
    if (!weights) {
      weights = themeNames.map(() => 1 / themeNames.length);
    }

    for (let i = 0; i < themes.length; i++) {
      const weight = weights[i];
      const theme = themes[i];

      // Blend lighting
      if (theme.lighting) {
        blendedTheme.lighting.brightness = (blendedTheme.lighting.brightness || 0) +
          (theme.lighting.brightness || 0.5) * weight;
      }
    }

    return blendedTheme;
  }

  /**
   * Create custom theme
   */
  createCustomTheme(themeData) {
    const customTheme = {
      name: themeData.name,
      description: themeData.description,
      difficulty: themeData.difficulty || 1,
      environment: themeData.environment || 'mixed',
      tileMapping: themeData.tileMapping || {},
      roomTiles: themeData.roomTiles || {},
      corridorTiles: themeData.corridorTiles || {},
      decorations: themeData.decorations || {},
      lighting: themeData.lighting || { brightness: 0.5, color: '#ffffff' },
      atmosphere: themeData.atmosphere || 'neutral',
      custom: true
    };

    return customTheme;
  }
}

module.exports = ThemeManager;