/**
 * Dwarven Mines Theme
 * Ancient underground mines carved by dwarven craftsmen
 */

class DwarvenMinesTheme {
  constructor() {
    this.name = 'Dwarven Mines';
    this.description = 'Ancient underground mines filled with dwarven craftsmanship and mineral wealth';
    this.difficulty = 2;
    this.environment = 'underground';
    this.recommendedLevel = 3;
    this.atmosphere = 'earthy';
  }

  get tileMapping() {
    return {
      wall: 'dwarven_stone',
      floor: 'mine_floor',
      door: 'iron_door',
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

module.exports = DwarvenMinesTheme;