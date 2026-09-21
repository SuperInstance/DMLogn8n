/**
 * Undead Crypt Theme
 * Dark, haunted dungeon filled with undead creatures and necromantic energy
 */

class UndeadCryptTheme {
  constructor() {
    this.name = 'Undead Crypt';
    this.description = 'A haunted burial crypt filled with undead guardians and dark necromantic energy';
    this.difficulty = 3;
    this.environment = 'necromantic';
    this.recommendedLevel = 5;
    this.atmosphere = 'eerie';
  }

  get tileMapping() {
    return {
      wall: 'crypt_wall',
      floor: 'stone_crypt_floor',
      door: 'iron_door',
      special: [
        {
          tile: 'bone_wall',
          probability: 0.2,
          condition: (x, y) => Math.random() < 0.4
        },
        {
          tile: 'grave_floor',
          probability: 0.3,
          pattern: { type: 'checkerboard' }
        },
        {
          tile: 'blood_stain',
          probability: 0.25,
          condition: (x, y) => Math.random() < 0.3
        },
        {
          tile: 'ectoplasm_residue',
          probability: 0.15,
          condition: (x, y) => Math.random() < 0.2
        },
        {
          tile: 'rune_carved_wall',
          probability: 0.1,
          condition: (x, y) => Math.random() < 0.15
        }
      ]
    };
  }

  get roomTiles() {
    return {
      normal: ['crypt_floor', 'burial_chamber_floor'],
      entrance: ['gargoyled_entrance_floor'],
      boss: ['lich_throne_room_floor'],
      treasure: ['tomb_floor', 'sarcophagus_floor'],
      trap: ['cursed_floor', 'soul_trap_floor'],
      puzzle: ['rune_puzzle_floor'],
      secret: ['hidden_crypt_floor']
    };
  }

  get corridorTiles() {
    return {
      normal: ['narrow_crypt_corridor'],
      narrow: ['tomb_corridor'],
      wide: ['processional_corridor'],
      loop: ['circular_crypt_corridor']
    };
  }

  get decorations() {
    return {
      normal: [
        {
          type: 'candle',
          probability: 0.8,
          minCount: 2,
          maxCount: 4,
          properties: { flicker: true, color: 'blue' }
        },
        {
          type: 'skeleton',
          probability: 0.4,
          minCount: 1,
          maxCount: 3,
          properties: { animated: Math.random() < 0.3 }
        },
        {
          type: 'cobwebs',
          probability: 0.6,
          minCount: 0,
          maxCount: 4,
          properties: { thickness: 'heavy' }
        },
        {
          type: 'coffin',
          probability: 0.3,
          minCount: 0,
          maxCount: 2,
          properties: { open: Math.random() < 0.4 }
        }
      ],
      boss: [
        {
          type: 'lich_throne',
          probability: 0.9,
          minCount: 1,
          maxCount: 1,
          properties: { material: 'bone', empowered: true }
        },
        {
          type: 'soul_gem',
          probability: 0.7,
          minCount: 2,
          maxCount: 5,
          properties: { glowing: true, power: 'high' }
        },
        {
          type: 'necromantic_altar',
          probability: 0.8,
          minCount: 1,
          maxCount: 2,
          properties: { active: true }
        }
      ],
      treasure: [
        {
          type: 'sarcophagus',
          probability: 0.8,
          minCount: 1,
          maxCount: 3,
          properties: { sealed: true, trapped: 0.7 }
        },
        {
          type: 'bone_pile',
          probability: 0.6,
          minCount: 0,
          maxCount: 2,
          properties: { valuable: Math.random() < 0.4 }
        }
      ],
      trap: [
        {
          type: 'soul_trap',
          probability: 0.7,
          minCount: 1,
          maxCount: 2,
          properties: { damage: 'spiritual' }
        },
        {
          type: 'curse_trap',
          probability: 0.5,
          minCount: 0,
          maxCount: 1,
          properties: { curse_type: 'undeath' }
        },
        {
          type: 'skeleton_hands',
          probability: 0.6,
          minCount: 1,
          maxCount: 3,
          properties: { grasp: true }
        }
      ]
    };
  }

  get corridorDecorations() {
    return [
      {
        type: 'wall_sconse',
        probability: 0.6,
        maxCount: 5,
        properties: { light: 'blue_flame', height: 'wall' }
      },
      {
        type: 'hanging_chains',
        probability: 0.4,
        maxCount: 3,
        properties: { rusted: true, length: 'long' }
      },
      {
        type: 'bone_fragments',
        probability: 0.5,
        maxCount: 4,
        properties: { scattered: true }
      }
    ];
  }

  get lighting() {
    return {
      brightness: 0.3,
      color: '#6666ff',
      sources: [
        {
          type: 'candle',
          probability: 0.7,
          radius: 2,
          intensity: 0.6,
          color: '#9999ff'
        },
        {
          type: 'spirit_light',
          probability: 0.3,
          radius: 4,
          intensity: 0.4,
          color: '#ccccff'
        },
        {
          type: 'rune_glow',
          probability: 0.2,
          radius: 3,
          intensity: 0.5,
          color: '#ff99ff'
        }
      ]
    };
  }

  get lightSources() {
    return [
      {
        type: 'candle',
        probability: 0.6,
        radius: 2,
        intensity: 0.6,
        color: '#9999ff'
      },
      {
        type: 'will_o_wisp',
        probability: 0.3,
        radius: 3,
        intensity: 0.5,
        color: '#ccccff'
      }
    ];
  }

  get roomAtmosphere() {
    return {
      normal: 'haunted',
      entrance: 'foreboding',
      boss: 'terrifying',
      treasure: 'ancient_evil',
      trap: 'cursed',
      puzzle: 'mystical',
      secret: 'hidden_horror'
    };
  }

  get enemyTypes() {
    return [
      'skeleton_warrior',
      'zombie',
      'ghost',
      'specter',
      'wraith',
      'ghoul',
      'wight',
      'revenant',
      'mummy',
      'shadow',
      'bone_golem',
      'lich_minion'
    ];
  }

  get treasureTypes() {
    return [
      'ancient_coins',
      'bone_charms',
      'undead_weapons',
      'shadow_armor',
      'necromantic_scroll',
      'soul_gems',
      'cursed_rings',
      'ghost_dust',
      'grave_earth',
      'ectoplasm'
    ];
  }

  get trapTypes() {
    return [
      'soul_drain_trap',
      'curse_trap',
      'skeleton_ambush',
      'ghost_touch_trap',
      'necromantic_symbol',
      'death_rune_trap',
      'undead_rising_trap'
    ];
  }

  get puzzleTypes() {
    return [
      'rune_arrangement',
      'spirit_communication',
      'ancestral_knowledge',
      'death_symbol_puzzle',
      'soul_binding_ritual'
    ];
  }

  get ambientSounds() {
    return [
      'moaning_wind',
      'distant_screams',
      'chains_rattling',
      'whispering_spirits',
      'bone_cracking',
      'ectoplasm_drip',
      'soul_whisper'
    ];
  }

  get backgroundMusic() {
    return [
      'haunted_theme',
      'horror_ambience',
      'supernatural_tension',
      'gothic_horror',
      'spirit_requiem'
    ];
  }

  get difficultyModifiers() {
    return {
      enemyDamage: 1.3,
      trapDamage: 1.4,
      puzzleComplexity: 1.2,
      visibility: 0.5,
      environmentalHazards: 0.7
    };
  }

  // Theme-specific modifications
  modifyGrid(grid) {
    const modifiedGrid = grid.map(row => [...row]);

    // Add ectoplasmic residue
    for (let y = 1; y < grid.length - 1; y++) {
      for (let x = 1; x < grid[0].length - 1; x++) {
        if (grid[y][x] === 'crypt_floor' && Math.random() < 0.08) {
          modifiedGrid[y][x] = 'ectoplasmic_floor';
        }
      }
    }

    return modifiedGrid;
  }

  modifyRoom(room) {
    if (room.type === 'boss') {
      room.hasLichElements = true;
      room.soulEnergy = 'high';
      room.resurrectionPoints = 3;
    }

    if (room.type === 'treasure') {
      room.hasCurses = Math.random() < 0.8;
      room.guardianSpirit = Math.random() < 0.4;
    }

    return room;
  }

  modifyCorridor(corridor) {
    corridor.hauntingLevel = Math.floor(Math.random() * 3) + 1;
    corridor.spiritPresence = Math.random() < 0.6;
    return corridor;
  }
}

module.exports = UndeadCryptTheme;