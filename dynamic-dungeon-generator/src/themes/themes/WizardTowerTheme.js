/**
 * Wizard Tower Theme
 * Magical tower filled with arcane wonders and mystical challenges
 */

class WizardTowerTheme {
  constructor() {
    this.name = 'Wizard Tower';
    this.description = 'A soaring magical tower filled with arcane experiments, enchanted guardians, and mystical puzzles';
    this.difficulty = 4;
    this.environment = 'magical';
    this.recommendedLevel = 8;
    this.atmosphere = 'mystical';
  }

  get tileMapping() {
    return {
      wall: 'magical_stone',
      floor: 'enchanted_floor',
      door: 'arcane_door',
      special: [
        {
          tile: 'rune_wall',
          probability: 0.3,
          condition: (x, y) => Math.random() < 0.5
        },
        {
          tile: 'magic_circle',
          probability: 0.2,
          pattern: { type: 'center', radius: 3 }
        },
        {
          tile: 'crystal_growth',
          probability: 0.15,
          condition: (x, y) => Math.random() < 0.4
        },
        {
          tile: 'floating_symbols',
          probability: 0.25,
          condition: (x, y) => Math.random() < 0.3
        },
        {
          tile: 'portal_rune',
          probability: 0.1,
          condition: (x, y) => Math.random() < 0.2
        }
      ]
    };
  }

  get roomTiles() {
    return {
      normal: ['marble_floor', 'mosaic_floor'],
      entrance: 'grand_entrance_floor',
      boss: ['archmage_sanctum_floor'],
      treasure: ['alchemical_lab_floor'],
      trap: ['trap_rune_floor'],
      puzzle: ['puzzle_pattern_floor'],
      secret: ['hidden_library_floor']
    };
  }

  get corridorTiles() {
    return {
      normal: 'enchanted_corridor',
      narrow: 'arcane_passage',
      wide: 'grand_hallway',
      loop: 'circular_tower_corridor'
    };
  }

  get decorations() {
    return {
      normal: [
        {
          type: 'crystal_ball',
          probability: 0.5,
          minCount: 1,
          maxCount: 2,
          properties: { glowing: true, scrying: Math.random() < 0.3 }
        },
        {
          type: 'bookshelf',
          probability: 0.6,
          minCount: 0,
          maxCount: 3,
          properties: { magical: true, ancient: Math.random() < 0.4 }
        },
        {
          type: 'potion_rack',
          probability: 0.4,
          minCount: 0,
          maxCount: 2,
          properties: { variety: 'magical' }
        },
        {
          type: 'arcane_symbol',
          probability: 0.7,
          minCount: 2,
          maxCount: 5,
          properties: { floating: true }
        }
      ],
      boss: [
        {
          type: 'archmage_throne',
          probability: 0.9,
          minCount: 1,
          maxCount: 1,
          properties: { material: 'star_metal', empowered: true }
        },
        {
          type: 'portal_frame',
          probability: 0.7,
          minCount: 1,
          maxCount: 2,
          properties: { active: false, destination: 'unknown' }
        },
        {
          type: 'power_orb',
          probability: 0.8,
          minCount: 3,
          maxCount: 6,
          properties: { elemental: 'arcane', floating: true }
        }
      ],
      treasure: [
        {
          type: 'magic_chest',
          probability: 0.8,
          minCount: 1,
          maxCount: 3,
          properties: { locked: true, magical_lock: true }
        },
        {
          type: 'scroll_rack',
          probability: 0.7,
          minCount: 2,
          maxCount: 4,
          properties: { power_level: 'high' }
        },
        {
          type: 'artifact_podium',
          probability: 0.5,
          minCount: 0,
          maxCount: 2,
          properties: { protected: true, glowing: true }
        }
      ],
      trap: [
        {
          type: 'magic_missile_trap',
          probability: 0.7,
          minCount: 1,
          maxCount: 3,
          properties: { element: 'arcane' }
        },
        {
          type: 'teleport_trap',
          probability: 0.4,
          minCount: 0,
          maxCount: 1,
          properties: { random_destination: true }
        },
        {
          type: 'rune_trap',
          probability: 0.6,
          minCount: 1,
          maxCount: 2,
          properties: { effect: 'paralysis' }
        }
      ]
    };
  }

  get lighting() {
    return {
      brightness: 0.7,
      color: '#9966ff',
      sources: [
        {
          type: 'magical_light',
          probability: 0.8,
          radius: 4,
          intensity: 0.8,
          color: '#9966ff'
        },
        {
          type: 'crystal_glow',
          probability: 0.5,
          radius: 3,
          intensity: 0.6,
          color: '#cc99ff'
        },
        {
          type: 'arcane_energy',
          probability: 0.3,
          radius: 5,
          intensity: 0.7,
          color: '#ff99ff'
        }
      ]
    };
  }

  get ambientSounds() {
    return [
      'magical_hum',
      'crystal_chime',
      'spell_whisper',
      'parchment_rustle',
      'arcane_crackle',
      'dimensional_echo'
    ];
  }

  get backgroundMusic() {
    return [
      'mystical_theme',
      'magical_ambience',
      'arcane_mystery',
      'wizard_tower_theme',
      'enchantment_music'
    ];
  }

  get difficultyModifiers() {
    return {
      enemyDamage: 1.4,
      trapDamage: 1.5,
      puzzleComplexity: 1.6,
      visibility: 0.8,
      environmentalHazards: 0.6
    };
  }
}

module.exports = WizardTowerTheme;