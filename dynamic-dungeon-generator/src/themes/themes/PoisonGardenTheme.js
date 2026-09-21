class PoisonGardenTheme {
  constructor() {
    this.name = 'PoisonGarden Theme';
    this.description = 'A PoisonGarden themed dungeon environment';
    this.difficulty = 3;
    this.environment = 'mixed';
    this.recommendedLevel = 5;
    this.atmosphere = 'mysterious';
  }

  get tileMapping() {
    return {
      wall: 'stone_wall',
      floor: 'stone_floor',
      door: 'wooden_door',
      special: []
    };
  }

  get roomTiles() {
    return {
      normal: ['stone_floor'],
      entrance: 'entrance_floor',
      boss: 'boss_floor',
      treasure: 'treasure_floor',
      trap: 'trap_floor',
      puzzle: 'puzzle_floor',
      secret: 'secret_floor'
    };
  }

  get corridorTiles() {
    return {
      normal: 'corridor_floor',
      narrow: 'narrow_corridor',
      wide: 'wide_corridor',
      loop: 'loop_corridor'
    };
  }

  get decorations() {
    return {
      normal: [],
      boss: [],
      treasure: [],
      trap: []
    };
  }

  get lighting() {
    return {
      brightness: 0.5,
      color: '#ffffff',
      sources: []
    };
  }

  get ambientSounds() {
    return ['ambient_sound'];
  }

  get backgroundMusic() {
    return ['background_music'];
  }

  get difficultyModifiers() {
    return {
      enemyDamage: 1.0,
      trapDamage: 1.0,
      puzzleComplexity: 1.0,
      visibility: 0.7,
      environmentalHazards: 0.5
    };
  }
}

module.exports = PoisonGardenTheme;
