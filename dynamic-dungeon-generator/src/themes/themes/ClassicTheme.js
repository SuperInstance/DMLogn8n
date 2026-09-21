/**
 * Classic Dungeon Theme
 * Traditional stone dungeon with torches and basic features
 */

class ClassicTheme {
  constructor() {
    this.name = 'Classic Dungeon';
    this.description = 'A traditional stone dungeon with torch-lit corridors and ancient stonework';
    this.difficulty = 1;
    this.environment = 'underground';
    this.recommendedLevel = 1;
    this.atmosphere = 'damp';
  }

  get tileMapping() {
    return {
      wall: 'stone_wall',
      floor: 'stone_floor',
      door: 'wooden_door',
      special: [
        {
          tile: 'cracked_wall',
          probability: 0.1,
          pattern: { type: 'perimeter', margin: 2 }
        },
        {
          tile: 'mossy_wall',
          probability: 0.15,
          condition: (x, y) => Math.random() < 0.3
        },
        {
          tile: 'wet_floor',
          probability: 0.2,
          pattern: { type: 'checkerboard' }
        }
      ]
    };
  }

  get roomTiles() {
    return {
      normal: ['stone_floor', 'flagstone_floor'],
      entrance: ['cobblestone_floor'],
      boss: ['polished_stone_floor'],
      treasure: ['marble_floor'],
      trap: ['pressure_plate_floor'],
      puzzle: ['runic_floor'],
      secret: ['hidden_door_floor']
    };
  }

  get corridorTiles() {
    return {
      normal: ['stone_floor'],
      narrow: ['tight_corridor_floor'],
      wide: ['spacious_corridor_floor'],
      loop: ['circular_corridor_floor']
    };
  }

  get decorations() {
    return {
      normal: [
        {
          type: 'torch',
          probability: 0.7,
          minCount: 1,
          maxCount: 3,
          properties: { brightness: 0.8, flicker: true }
        },
        {
          type: 'chains',
          probability: 0.3,
          minCount: 0,
          maxCount: 2,
          properties: { rusted: true }
        },
        {
          type: 'barrel',
          probability: 0.4,
          minCount: 0,
          maxCount: 3,
          properties: { contents: 'empty' }
        }
      ],
      boss: [
        {
          type: 'throne',
          probability: 0.8,
          minCount: 1,
          maxCount: 1,
          properties: { material: 'stone', occupied: false }
        },
        {
          type: 'banner',
          probability: 0.6,
          minCount: 0,
          maxCount: 2,
          properties: { faction: 'unknown', tattered: true }
        }
      ],
      treasure: [
        {
          type: 'chest',
          probability: 0.9,
          minCount: 1,
          maxCount: 3,
          properties: { locked: true, trapped: 0.3 }
        },
        {
          type: 'pile',
          probability: 0.5,
          minCount: 0,
          maxCount: 2,
          properties: { type: 'coins' }
        }
      ],
      trap: [
        {
          type: 'pressure_plate',
          probability: 0.8,
          minCount: 1,
          maxCount: 2,
          properties: { visible: false, triggered: false }
        },
        {
          type: 'tripwire',
          probability: 0.4,
          minCount: 0,
          maxCount: 1,
          properties: { visible: false }
        }
      ]
    };
  }

  get corridorDecorations() {
    return [
      {
        type: 'torch_sconce',
        probability: 0.5,
        maxCount: 4,
        properties: { height: 'wall', brightness: 0.6 }
      },
      {
        type: 'dripstone',
        probability: 0.2,
        maxCount: 2,
        properties: { type: 'stalactite' }
      }
    ];
  }

  get lighting() {
    return {
      brightness: 0.4,
      color: '#ff9966',
      sources: [
        {
          type: 'torch',
          probability: 0.7,
          radius: 3,
          intensity: 0.8,
          color: '#ff9966'
        },
        {
          type: 'bioluminescence',
          probability: 0.1,
          radius: 2,
          intensity: 0.3,
          color: '#99ff99'
        }
      ]
    };
  }

  get lightSources() {
    return [
      {
        type: 'torch',
        probability: 0.6,
        radius: 3,
        intensity: 0.8,
        color: '#ff9966'
      },
      {
        type: 'lantern',
        probability: 0.2,
        radius: 4,
        intensity: 0.9,
        color: '#ffffcc'
      }
    ];
  }

  get roomAtmosphere() {
    return {
      normal: 'damp_stone',
      entrance: 'musty',
      boss: 'oppressive',
      treasure: 'ancient',
      trap: 'tense',
      puzzle: 'mysterious',
      secret: 'hidden'
    };
  }

  get enemyTypes() {
    return [
      'goblin',
      'kobold',
      'skeleton',
      'rat_giant',
      'slime',
      'bat_giant',
      'spider',
      'zombie'
    ];
  }

  get treasureTypes() {
    return [
      'gold_coins',
      'silver_coins',
      'basic_weapons',
      'armor_leather',
      'potions_healing',
      'scrolls_common',
      'gems_cheap'
    ];
  }

  get trapTypes() {
    return [
      'pit_trap',
      'dart_trap',
      'spike_trap',
      'guillotine_trap',
      'collapsing_ceiling',
      'rolling_boulder'
    ];
  }

  get puzzleTypes() {
    return [
      'lever_puzzle',
      'pressure_plate_sequence',
      'riddle_door',
      'symbol_matching',
      'maze_path'
    ];
  }

  get ambientSounds() {
    return [
      'dripping_water',
      'distant_echoes',
      'wind_whistle',
      'rat_squeak',
      'torch_crackle'
    ];
  }

  get backgroundMusic() {
    return [
      'dungeon_ambience',
      'exploration_theme',
      'tension_buildup',
      'mystery_theme'
    ];
  }

  get difficultyModifiers() {
    return {
      enemyDamage: 1.0,
      trapDamage: 1.0,
      puzzleComplexity: 1.0,
      visibility: 0.7,
      environmentalHazards: 0.3
    };
  }

  // Theme-specific modifications
  modifyGrid(grid) {
    // Add some random cracks to walls
    const modifiedGrid = grid.map(row => [...row]);

    for (let y = 1; y < grid.length - 1; y++) {
      for (let x = 1; x < grid[0].length - 1; x++) {
        if (grid[y][x] === 'stone_wall' && Math.random() < 0.05) {
          modifiedGrid[y][x] = 'cracked_stone_wall';
        }
      }
    }

    return modifiedGrid;
  }

  modifyRoom(room) {
    // Add room-specific modifications
    if (room.type === 'boss') {
      room.hasThrone = true;
      room.height = Math.max(room.height, 8);
      room.width = Math.max(room.width, 8);
    }

    if (room.type === 'treasure') {
      room.hasTraps = Math.random() < 0.6;
    }

    return room;
  }

  modifyCorridor(corridor) {
    // Add corridor-specific modifications
    if (corridor.type === 'loop') {
      coridor.hasSecretPassage = Math.random() < 0.2;
    }

    return corridor;
  }
}

module.exports = ClassicTheme;