/**
 * Dragon Lair Theme
 * Massive cavern system home to powerful dragons and their hoards
 */

class DragonLairTheme {
  constructor() {
    this.name = 'Dragon Lair';
    this.description = 'A vast volcanic cavern system inhabited by ancient dragons and filled with treasure';
    this.difficulty = 5;
    this.environment = 'volcanic';
    this.recommendedLevel = 10;
    this.atmosphere = 'intense';
  }

  get tileMapping() {
    return {
      wall: 'volcanic_rock',
      floor: 'obsidian_floor',
      door: 'massive_stone_door',
      special: [
        {
          tile: 'gold_vein',
          probability: 0.15,
          condition: (x, y) => Math.random() < 0.5
        },
        {
          tile: 'lava_crack',
          probability: 0.2,
          pattern: { type: 'diagonal', spacing: 4 }
        },
        {
          tile: 'dragon_scratch',
          probability: 0.25,
          condition: (x, y) => Math.random() < 0.4
        },
        {
          tile: 'treasure_glimmer',
          probability: 0.1,
          condition: (x, y) => Math.random() < 0.3
        },
        {
          tile: 'magma_pool',
          probability: 0.08,
          condition: (x, y) => Math.random() < 0.2
        },
        {
          tile: 'dragon_bones',
          probability: 0.05,
          condition: (x, y) => Math.random() < 0.1
        }
      ]
    };
  }

  get roomTiles() {
    return {
      normal: ['obsidian_floor', 'basalt_floor'],
      entrance: 'dragon_entrance_floor',
      boss: ['dragon_throne_floor', 'hoard_room_floor'],
      treasure: ['treasure_pile_floor', 'gem_encrusted_floor'],
      trap: ['pressure_trap_floor', 'fire_trap_floor'],
      puzzle: ['dragon_rune_floor'],
      secret: ['hidden_chamber_floor']
    };
  }

  get corridorTiles() {
    return {
      normal: ['volcanic_corridor'],
      narrow: ['dragon_passage'],
      wide: ['grand_cavern_corridor'],
      loop: ['circular_lair_corridor']
    };
  }

  get decorations() {
    return {
      normal: [
        {
          type: 'dragon_statue',
          probability: 0.4,
          minCount: 0,
          maxCount: 2,
          properties: { material: 'obsidian', size: 'medium' }
        },
        {
          type: 'treasure_pile',
          probability: 0.6,
          minCount: 0,
          maxCount: 3,
          properties: { value: 'moderate' }
        },
        {
          type: 'dragon_egg',
          probability: 0.2,
          minCount: 0,
          maxCount: 1,
          properties: { fertile: Math.random() < 0.3 }
        },
        {
          type: 'armor_rack',
          probability: 0.3,
          minCount: 0,
          maxCount: 2,
          properties: { style: 'dragon_scale' }
        }
      ],
      boss: [
        {
          type: 'dragon_throne',
          probability: 0.9,
          minCount: 1,
          maxCount: 1,
          properties: { material: 'gold', size: 'massive' }
        },
        {
          type: 'treasure_hoard',
          probability: 1.0,
          minCount: 3,
          maxCount: 8,
          properties: { value: 'immense', magical: true }
        },
        {
          type: 'dragon_nest',
          probability: 0.7,
          minCount: 1,
          maxCount: 2,
          properties: { occupied: false, size: 'large' }
        }
      ],
      treasure: [
        {
          type: 'treasure_chest',
          probability: 0.8,
          minCount: 2,
          maxCount: 5,
          properties: { locked: true, trapped: 0.9, material: 'dragon_bone' }
        },
        {
          type: 'gem_pile',
          probability: 0.7,
          minCount: 1,
          maxCount: 4,
          properties: { quality: 'flawless' }
        },
        {
          type: 'magic_weapon',
          probability: 0.5,
          minCount: 0,
          maxCount: 2,
          properties: { dragon_forged: true }
        }
      ],
      trap: [
        {
          type: 'fire_jet',
          probability: 0.8,
          minCount: 2,
          maxCount: 4,
          properties: { damage: 'high', trigger: 'pressure' }
        },
        {
          type: 'falling_rocks',
          probability: 0.6,
          minCount: 1,
          maxCount: 3,
          properties: { trigger: 'sound' }
        },
        {
          type: 'dragon_guardian',
          probability: 0.4,
          minCount: 0,
          maxCount: 1,
          properties: { type: 'skeletal', level: 'high' }
        }
      ]
    };
  }

  get corridorDecorations() {
    return [
      {
        type: 'torch_bracket',
        probability: 0.5,
        maxCount: 4,
        properties: { light: 'magical_fire', color: 'orange' }
      },
      {
        type: 'dragon_carving',
        probability: 0.3,
        maxCount: 3,
        properties: { style: 'ancient', condition: 'weathered' }
      },
      {
        type: 'gold_inlay',
        probability: 0.2,
        maxCount: 2,
        properties: { pattern: 'runes' }
      }
    ];
  }

  get lighting() {
    return {
      brightness: 0.6,
      color: '#ff6600',
      sources: [
        {
          type: 'magma_glow',
          probability: 0.6,
          radius: 5,
          intensity: 0.8,
          color: '#ff3300'
        },
        {
          type: 'treasure_glimmer',
          probability: 0.4,
          radius: 3,
          intensity: 0.6,
          color: '#ffcc00'
        },
        {
          type: 'dragon_fire',
          probability: 0.3,
          radius: 6,
          intensity: 0.9,
          color: '#ff6600'
        }
      ]
    };
  }

  get lightSources() {
    return [
      {
        type: 'magma_vent',
        probability: 0.4,
        radius: 5,
        intensity: 0.8,
        color: '#ff3300'
      },
      {
        type: 'glowing_crystal',
        probability: 0.3,
        radius: 4,
        intensity: 0.6,
        color: '#ff9900'
      }
    ];
  }

  get roomAtmosphere() {
    return {
      normal: 'volcanic_heat',
      entrance: 'foreboding_power',
      boss: 'overwhelming_presence',
      treasure: 'awe_inspiring',
      trap: 'deadly_heat',
      puzzle: 'ancient_wisdom',
      secret: 'hidden_power'
    };
  }

  get enemyTypes() {
    return [
      'dragon_whelp',
      'fire_elemental',
      'magma_elemental',
      'dragon_kin',
      'dragon_guardian',
      'ancient_dragon',
      'drake',
      'wyvern',
      'salamander',
      'fire_giant',
      'dragon_skeleton',
      'dragon_zombie'
    ];
  }

  get treasureTypes() {
    return [
      'dragon_gold',
      'magic_gems',
      'dragon_scale_armor',
      'flame_weapons',
      'ancient_artifacts',
      'dragon_pearls',
      'volcanic_glass',
      'dragon_tears',
      'fire_opals',
      'dragon_hearts',
      'legendary_weapons'
    ];
  }

  get trapTypes() {
    return [
      'fire_jet_trap',
      'lava_pit',
      'dragon_breath_trap',
      'falling_ceiling',
      'pressure_fire_trap',
      'magma_eruption',
      'dragon_alarm_trap'
    ];
  }

  get puzzleTypes() {
    return [
      'dragon_riddle',
      'fire_puzzle',
      'treasure_arrangement',
      'dragon_knowledge',
      'ancient_rune_mastery'
    ];
  }

  get ambientSounds() {
    return [
      'lava_bubbling',
      'dragon_roar_distant',
      'rock_cracking',
      'fire_crackling',
      'treasure_rustling',
      'dragon_breathing',
      'magma_flow'
    ];
  }

  get backgroundMusic() {
    return [
      'epic_dragon_theme',
      'volcanic_ambience',
      'powerful_presence',
      'ancient_power',
      'treasure_awe'
    ];
  }

  get difficultyModifiers() {
    return {
      enemyDamage: 1.6,
      trapDamage: 1.8,
      puzzleComplexity: 1.3,
      visibility: 0.6,
      environmentalHazards: 0.9
    };
  }

  // Theme-specific modifications
  modifyGrid(grid) {
    const modifiedGrid = grid.map(row => [...row]);

    // Add lava flows
    for (let y = 1; y < grid.length - 1; y++) {
      for (let x = 1; x < grid[0].length - 1; x++) {
        if (grid[y][x] === 'obsidian_floor' && Math.random() < 0.05) {
          modifiedGrid[y][x] = 'lava_crack_floor';
        }
      }
    }

    return modifiedGrid;
  }

  modifyRoom(room) {
    if (room.type === 'boss') {
      room.hasDragonLair = true;
      room.temperature = 'extreme';
      room.treasureValue = 'legendary';
      room.size = 'massive';
    }

    if (room.type === 'treasure') {
      room.hasDragonMagic = Math.random() < 0.8;
      room.guarded = true;
    }

    return room;
  }

  modifyCorridor(corridor) {
    corridor.temperature = Math.floor(Math.random() * 3) + 2; // 2-4 (warm to extreme)
    corridor.dragonPresence = Math.random() < 0.4;
    return corridor;
  }
}

module.exports = DragonLairTheme;