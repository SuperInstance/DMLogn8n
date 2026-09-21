/**
 * Configuration Manager
 * Handles loading and managing configuration settings
 */

const fs = require('fs');
const path = require('path');

class ConfigManager {
  constructor(configPath = null) {
    this.configPath = configPath || path.join(__dirname, '../../config/config.json');
    this.config = this.loadConfig();
    this.watchers = new Map();
  }

  /**
   * Load configuration from file
   */
  loadConfig() {
    try {
      if (fs.existsSync(this.configPath)) {
        const configData = fs.readFileSync(this.configPath, 'utf8');
        return JSON.parse(configData);
      } else {
        // Create default config if it doesn't exist
        const defaultConfig = this.getDefaultConfig();
        this.saveConfig(defaultConfig);
        return defaultConfig;
      }
    } catch (error) {
      console.warn('Failed to load config, using defaults:', error.message);
      return this.getDefaultConfig();
    }
  }

  /**
   * Get default configuration
   */
  getDefaultConfig() {
    return {
      server: {
        port: 3001,
        host: 'localhost',
        cors: {
          origin: "*",
          methods: ["GET", "POST", "PUT", "DELETE"]
        }
      },
      generation: {
        defaultAlgorithm: 'roomCorridor',
        defaultTheme: 'classic',
        maxWidth: 200,
        maxHeight: 200,
        maxFloors: 10,
        timeout: 30000 // 30 seconds
      },
      algorithms: {
        cellular: {
          initialFillProbability: 0.45,
          birthLimit: 4,
          deathLimit: 3,
          iterations: 6,
          smoothingPasses: 2,
          minRegionSize: 50
        },
        bsp: {
          minRoomSize: 6,
          maxRoomSize: 15,
          minSplitSize: 10,
          maxSplitDepth: 8,
          corridorWidth: 2,
          connectionType: 'corridor'
        },
        roomCorridor: {
          roomCount: { min: 8, max: 20 },
          roomSize: { min: 4, max: 12 },
          corridorWidth: 1,
          loopProbability: 0.2,
          deadEndProbability: 0.1,
          specialRoomChance: 0.3
        },
        organic: {
          seedPoints: { min: 3, max: 8 },
          growthSteps: 150,
          growthRadius: { min: 1, max: 3 },
          branchingProbability: 0.15,
          deathProbability: 0.05,
          smoothingPasses: 3
        }
      },
      environment: {
        fog_of_war: true,
        dynamic_lighting: false,
        weather_enabled: true,
        interactive_elements: true,
        destructible_environment: false
      },
      content: {
        enemy_density: 0.05,
        loot_density: 0.03,
        trap_density: 0.02,
        boss_chance: 0.8,
        puzzle_chance: 0.3
      },
      performance: {
        cache_enabled: true,
        cache_size: 100,
        max_concurrent_generations: 5,
        enable_profiling: false
      },
      logging: {
        level: 'info',
        file_enabled: true,
        console_enabled: true,
        max_file_size: '10MB',
        max_files: 5
      },
      integration: {
        n8n_enabled: true,
        n8n_webhook_url: 'http://localhost:5678/webhook/dungeon-generator',
        combat_system_url: 'http://localhost:3002/api/combat',
        quest_generator_url: 'http://localhost:3003/api/quests',
        world_state_url: 'http://localhost:3004/api/world'
      }
    };
  }

  /**
   * Save configuration to file
   */
  saveConfig(config = this.config) {
    try {
      const configDir = path.dirname(this.configPath);
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }

      fs.writeFileSync(this.configPath, JSON.stringify(config, null, 2));
      this.config = config;
    } catch (error) {
      console.error('Failed to save config:', error.message);
    }
  }

  /**
   * Get configuration value
   */
  get(key, defaultValue = null) {
    const keys = key.split('.');
    let value = this.config;

    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        return defaultValue;
      }
    }

    return value;
  }

  /**
   * Set configuration value
   */
  set(key, value) {
    const keys = key.split('.');
    let current = this.config;

    for (let i = 0; i < keys.length - 1; i++) {
      const k = keys[i];
      if (!(k in current) || typeof current[k] !== 'object') {
        current[k] = {};
      }
      current = current[k];
    }

    const lastKey = keys[keys.length - 1];
    const oldValue = current[lastKey];
    current[lastKey] = value;

    // Notify watchers
    this.notifyWatchers(key, value, oldValue);

    return this;
  }

  /**
   * Update multiple configuration values
   */
  update(updates) {
    for (const [key, value] of Object.entries(updates)) {
      this.set(key, value);
    }
    return this;
  }

  /**
   * Reset configuration to defaults
   */
  reset() {
    this.config = this.getDefaultConfig();
    this.saveConfig();
    return this;
  }

  /**
   * Watch for configuration changes
   */
  watch(key, callback) {
    if (!this.watchers.has(key)) {
      this.watchers.set(key, new Set());
    }
    this.watchers.get(key).add(callback);
    return this;
  }

  /**
   * Stop watching configuration changes
   */
  unwatch(key, callback) {
    if (this.watchers.has(key)) {
      this.watchers.get(key).delete(callback);
      if (this.watchers.get(key).size === 0) {
        this.watchers.delete(key);
      }
    }
    return this;
  }

  /**
   * Notify watchers of configuration changes
   */
  notifyWatchers(key, newValue, oldValue) {
    // Notify exact key watchers
    if (this.watchers.has(key)) {
      for (const callback of this.watchers.get(key)) {
        try {
          callback(newValue, oldValue, key);
        } catch (error) {
          console.error('Config watcher error:', error);
        }
      }
    }

    // Notify parent key watchers
    const keyParts = key.split('.');
    for (let i = keyParts.length - 1; i > 0; i--) {
      const parentKey = keyParts.slice(0, i).join('.');
      if (this.watchers.has(parentKey)) {
        for (const callback of this.watchers.get(parentKey)) {
          try {
            callback(this.get(parentKey), oldValue, parentKey);
          } catch (error) {
            console.error('Config watcher error:', error);
          }
        }
      }
    }
  }

  /**
   * Validate configuration
   */
  validate() {
    const validation = {
      valid: true,
      warnings: [],
      errors: []
    };

    // Validate server configuration
    if (this.get('server.port') < 1 || this.get('server.port') > 65535) {
      validation.errors.push('Server port must be between 1 and 65535');
      validation.valid = false;
    }

    // Validate generation limits
    if (this.get('generation.maxWidth') < 10 || this.get('generation.maxWidth') > 1000) {
      validation.warnings.push('Max width should be between 10 and 1000');
    }

    if (this.get('generation.maxHeight') < 10 || this.get('generation.maxHeight') > 1000) {
      validation.warnings.push('Max height should be between 10 and 1000');
    }

    // Validate content densities
    if (this.get('content.enemy_density') < 0 || this.get('content.enemy_density') > 1) {
      validation.errors.push('Enemy density must be between 0 and 1');
      validation.valid = false;
    }

    if (this.get('content.loot_density') < 0 || this.get('content.loot_density') > 1) {
      validation.errors.push('Loot density must be between 0 and 1');
      validation.valid = false;
    }

    return validation;
  }

  /**
   * Export configuration
   */
  export() {
    return JSON.stringify(this.config, null, 2);
  }

  /**
   * Import configuration
   */
  import(configData) {
    try {
      const importedConfig = JSON.parse(configData);
      const validation = this.validateConfig(importedConfig);

      if (validation.valid) {
        this.config = importedConfig;
        this.saveConfig();
        return { success: true, validation };
      } else {
        return { success: false, validation };
      }
    } catch (error) {
      return {
        success: false,
        error: {
          message: 'Invalid JSON configuration',
          details: error.message
        }
      };
    }
  }

  /**
   * Validate imported configuration
   */
  validateConfig(config) {
    // Basic structure validation
    const requiredSections = ['server', 'generation', 'algorithms'];
    const validation = { valid: true, errors: [], warnings: [] };

    for (const section of requiredSections) {
      if (!config[section]) {
        validation.errors.push(`Missing required section: ${section}`);
        validation.valid = false;
      }
    }

    return validation;
  }

  /**
   * Get configuration schema
   */
  getSchema() {
    return {
      type: 'object',
      properties: {
        server: {
          type: 'object',
          properties: {
            port: { type: 'number', minimum: 1, maximum: 65535 },
            host: { type: 'string' }
          }
        },
        generation: {
          type: 'object',
          properties: {
            defaultAlgorithm: { type: 'string', enum: ['cellular', 'bsp', 'roomCorridor', 'organic'] },
            defaultTheme: { type: 'string' },
            maxWidth: { type: 'number', minimum: 10, maximum: 1000 },
            maxHeight: { type: 'number', minimum: 10, maximum: 1000 },
            maxFloors: { type: 'number', minimum: 1, maximum: 10 }
          }
        },
        algorithms: {
          type: 'object',
          properties: {
            cellular: { type: 'object' },
            bsp: { type: 'object' },
            roomCorridor: { type: 'object' },
            organic: { type: 'object' }
          }
        }
      }
    };
  }
}

module.exports = ConfigManager;