/**
 * Comprehensive Spell Database for D&D 5e
 */

import { SPELL_LEVELS, MAGIC_SCHOOLS } from '../types/index.js';

export const SPELL_DATABASE = {
  // Cantrips
  'fire bolt': {
    name: 'Fire Bolt',
    level: SPELL_LEVELS.CANTRIP,
    school: MAGIC_SCHOOLS.EVOCATION,
    castingTime: '1 action',
    range: '120 feet',
    components: ['V', 'S'],
    duration: 'Instantaneous',
    description: 'You hurl a mote of fire at a creature or object.',
    effectType: 'damage',
    damage: '1d10',
    damageType: 'fire',
    save: null,
    attackRoll: true,
    higherLevelDamage: '1d10'
  },
  'mage hand': {
    name: 'Mage Hand',
    level: SPELL_LEVELS.CANTRIP,
    school: MAGIC_SCHOOLS.CONJURATION,
    castingTime: '1 action',
    range: '30 feet',
    components: ['V', 'S'],
    duration: '1 minute',
    description: 'You create a spectral, floating hand.',
    effectType: 'utility',
    save: null,
    attackRoll: false
  },
  'prestidigitation': {
    name: 'Prestidigitation',
    level: SPELL_LEVELS.CANTRIP,
    school: MAGIC_SCHOOLS.TRANSMUTATION,
    castingTime: '1 action',
    range: '10 feet',
    components: ['V', 'S'],
    duration: 'Up to 1 hour',
    description: 'You perform a minor magical trick.',
    effectType: 'utility',
    save: null,
    attackRoll: false
  },

  // 1st Level Spells
  'fireball': {
    name: 'Fireball',
    level: SPELL_LEVELS.FIRST,
    school: MAGIC_SCHOOLS.EVOCATION,
    castingTime: '1 action',
    range: '150 feet',
    components: ['V', 'S', 'M'],
    duration: 'Instantaneous',
    description: 'A bright streak flashes from your pointing finger to a point you choose within range.',
    effectType: 'damage',
    damage: '8d6',
    damageType: 'fire',
    save: 'dexterity',
    halfDamageOnSave: true,
    area: '20-foot radius sphere',
    higherLevelDamage: '1d6',
    concentration: false
  },
  'magic missile': {
    name: 'Magic Missile',
    level: SPELL_LEVELS.FIRST,
    school: MAGIC_SCHOOLS.EVOCATION,
    castingTime: '1 action',
    range: '120 feet',
    components: ['V', 'S'],
    duration: 'Instantaneous',
    description: 'You create three glowing darts of magical force.',
    effectType: 'damage',
    damage: '3d4+3',
    damageType: 'force',
    save: null,
    attackRoll: false,
    higherLevelDamage: '1d4+1',
    concentration: false
  },
  'shield': {
    name: 'Shield',
    level: SPELL_LEVELS.FIRST,
    school: MAGIC_SCHOOLS.ABJURATION,
    castingTime: '1 reaction',
    range: 'Self',
    components: ['V', 'S'],
    duration: '1 round',
    description: 'An invisible barrier of magical force appears and protects you.',
    effectType: 'utility',
    save: null,
    attackRoll: false,
    concentration: false,
    defensive: true
  },
  'cure wounds': {
    name: 'Cure Wounds',
    level: SPELL_LEVELS.FIRST,
    school: MAGIC_SCHOOLS.EVOCATION,
    castingTime: '1 action',
    range: 'Touch',
    components: ['V', 'S'],
    duration: 'Instantaneous',
    description: 'A creature you touch regains hit points.',
    effectType: 'healing',
    healing: '1d8 + spellcasting ability modifier',
    save: null,
    attackRoll: false,
    higherLevelHealing: 8,
    concentration: false
  },
  'detect magic': {
    name: 'Detect Magic',
    level: SPELL_LEVELS.FIRST,
    school: MAGIC_SCHOOLS.DIVINATION,
    castingTime: '1 action',
    range: 'Self',
    components: ['V', 'S'],
    duration: 'Concentration, up to 10 minutes',
    description: 'For the duration, you sense the presence of magic within 30 feet of you.',
    effectType: 'utility',
    save: null,
    attackRoll: false,
    concentration: true
  },
  'bless': {
    name: 'Bless',
    level: SPELL_LEVELS.FIRST,
    school: MAGIC_SCHOOLS.ENCHANTMENT,
    castingTime: '1 action',
    range: '30 feet',
    components: ['V', 'S', 'M'],
    duration: 'Concentration, up to 1 minute',
    description: 'You bless up to three creatures of your choice within range.',
    effectType: 'utility',
    save: null,
    attackRoll: false,
    concentration: true,
    targets: 3
  },
  'burning hands': {
    name: 'Burning Hands',
    level: SPELL_LEVELS.FIRST,
    school: MAGIC_SCHOOLS.EVOCATION,
    castingTime: '1 action',
    range: 'Self (15-foot cone)',
    components: ['V', 'S'],
    duration: 'Instantaneous',
    description: 'As you hold your hands with thumbs touching and fingers spread, a thin sheet of flames shoots forth.',
    effectType: 'damage',
    damage: '3d6',
    damageType: 'fire',
    save: 'dexterity',
    halfDamageOnSave: true,
    area: '15-foot cone',
    higherLevelDamage: '1d6',
    concentration: false
  },
  'charm person': {
    name: 'Charm Person',
    level: SPELL_LEVELS.FIRST,
    school: MAGIC_SCHOOLS.ENCHANTMENT,
    castingTime: '1 action',
    range: '30 feet',
    components: ['V', 'S'],
    duration: '1 hour',
    description: 'You attempt to charm a humanoid you can see within range.',
    effectType: 'save_or_effect',
    save: 'wisdom',
    effect: {
      type: 'condition',
      condition: 'charmed',
      duration: '1 hour'
    },
    concentration: false
  },
  'hideous laughter': {
    name: 'Hideous Laughter',
    level: SPELL_LEVELS.FIRST,
    school: MAGIC_SCHOOLS.ENCHANTMENT,
    castingTime: '1 action',
    range: '30 feet',
    components: ['V', 'S', 'M'],
    duration: 'Concentration, up to 1 minute',
    description: 'A creature of your choice becomes incapacitated and can\'t stand up.',
    effectType: 'save_or_effect',
    save: 'wisdom',
    effect: {
      type: 'condition',
      condition: 'incapacitated',
      duration: '1 minute'
    },
    concentration: true
  },

  // 2nd Level Spells
  'misty step': {
    name: 'Misty Step',
    level: SPELL_LEVELS.SECOND,
    school: MAGIC_SCHOOLS.CONJURATION,
    castingTime: '1 bonus action',
    range: 'Self',
    components: ['V'],
    duration: 'Instantaneous',
    description: 'B briefly surrounded by silvery mist, you teleport up to 30 feet to an unoccupied space.',
    effectType: 'utility',
    save: null,
    attackRoll: false,
    concentration: false,
    teleport: 30
  },
  'scorching ray': {
    name: 'Scorching Ray',
    level: SPELL_LEVELS.SECOND,
    school: MAGIC_SCHOOLS.EVOCATION,
    castingTime: '1 action',
    range: '120 feet',
    components: ['V', 'S'],
    duration: 'Instantaneous',
    description: 'You create three rays of fire and hurl them at targets within range.',
    effectType: 'damage',
    damage: '2d6',
    damageType: 'fire',
    save: null,
    attackRoll: true,
    rays: 3,
    higherLevelDamage: '1d6',
    concentration: false
  },
  'invisibility': {
    name: 'Invisibility',
    level: SPELL_LEVELS.SECOND,
    school: MAGIC_SCHOOLS.ILLUSION,
    castingTime: '1 action',
    range: 'Touch',
    components: ['V', 'S', 'M'],
    duration: 'Concentration, up to 1 hour',
    description: 'A creature you touch becomes invisible until the spell ends.',
    effectType: 'utility',
    save: null,
    attackRoll: false,
    concentration: true,
    effect: {
      type: 'condition',
      condition: 'invisible'
    }
  },
  'see invisibility': {
    name: 'See Invisibility',
    level: SPELL_LEVELS.SECOND,
    school: MAGIC_SCHOOLS.DIVINATION,
    castingTime: '1 action',
    range: 'Self',
    components: ['V', 'S', 'M'],
    duration: '1 hour',
    description: 'For the duration, you see invisible creatures and objects as if they were visible.',
    effectType: 'utility',
    save: null,
    attackRoll: false,
    concentration: false
  },

  // 3rd Level Spells
  'lightning bolt': {
    name: 'Lightning Bolt',
    level: SPELL_LEVELS.THIRD,
    school: MAGIC_SCHOOLS.EVOCATION,
    castingTime: '1 action',
    range: 'Self (100-foot line)',
    components: ['V', 'S', 'M'],
    duration: 'Instantaneous',
    description: 'A stroke of lightning forms a line 100 feet long and 5 feet wide.',
    effectType: 'damage',
    damage: '8d6',
    damageType: 'lightning',
    save: 'dexterity',
    halfDamageOnSave: true,
    area: '100-foot line',
    higherLevelDamage: '1d6',
    concentration: false
  },
  'fireball (3rd level)': {
    name: 'Fireball',
    level: SPELL_LEVELS.THIRD,
    school: MAGIC_SCHOOLS.EVOCATION,
    castingTime: '1 action',
    range: '150 feet',
    components: ['V', 'S', 'M'],
    duration: 'Instantaneous',
    description: 'A bright streak flashes from your pointing finger to a point you choose within range.',
    effectType: 'damage',
    damage: '10d6',
    damageType: 'fire',
    save: 'dexterity',
    halfDamageOnSave: true,
    area: '20-foot radius sphere',
    higherLevelDamage: '1d6',
    concentration: false
  },
  'fly': {
    name: 'Fly',
    level: SPELL_LEVELS.THIRD,
    school: MAGIC_SCHOOLS.TRANSMUTATION,
    castingTime: '1 action',
    range: 'Touch',
    components: ['V', 'S', 'M'],
    duration: 'Concentration, up to 10 minutes',
    description: 'You touch a willing creature. The target gains a flying speed of 60 feet.',
    effectType: 'utility',
    save: null,
    attackRoll: false,
    concentration: true,
    effect: {
      type: 'movement',
      flySpeed: 60
    }
  },
  'revivify': {
    name: 'Revivify',
    level: SPELL_LEVELS.THIRD,
    school: MAGIC_SCHOOLS.NECROMANCY,
    castingTime: '1 action',
    range: 'Touch',
    components: ['V', 'S', 'M'],
    duration: 'Instantaneous',
    description: 'You touch a creature that has died within the last minute.',
    effectType: 'utility',
    save: null,
    attackRoll: false,
    concentration: false,
    resurrect: true
  },
  'dispel magic': {
    name: 'Dispel Magic',
    level: SPELL_LEVELS.THIRD,
    school: MAGIC_SCHOOLS.ABJURATION,
    castingTime: '1 action',
    range: '120 feet',
    components: ['V', 'S'],
    duration: 'Instantaneous',
    description: 'Choose one creature, object, or magical effect within range.',
    effectType: 'utility',
    save: null,
    attackRoll: false,
    concentration: false,
    dispel: true
  },
  'haste': {
    name: 'Haste',
    level: SPELL_LEVELS.THIRD,
    school: MAGIC_SCHOOLS.TRANSMUTATION,
    castingTime: '1 action',
    range: '30 feet',
    components: ['V', 'S', 'M'],
    duration: 'Concentration, up to 1 minute',
    description: 'Choose a willing creature that you can see within range.',
    effectType: 'utility',
    save: null,
    attackRoll: false,
    concentration: true,
    effect: {
      type: 'enhancement',
      speed: '+30 feet',
      AC: '+2',
      action: 'extra action'
    }
  },

  // 4th Level Spells
  'polymorph': {
    name: 'Polymorph',
    level: SPELL_LEVELS.FOURTH,
    school: MAGIC_SCHOOLS.TRANSMUTATION,
    castingTime: '1 action',
    range: '60 feet',
    components: ['V', 'S', 'M'],
    duration: 'Concentration, up to 1 hour',
    description: 'You transform a creature into a different beast.',
    effectType: 'utility',
    save: 'wisdom',
    concentration: true,
    transform: true
  },
  'greater invisibility': {
    name: 'Greater Invisibility',
    level: SPELL_LEVELS.FOURTH,
    school: MAGIC_SCHOOLS.ILLUSION,
    castingTime: '1 action',
    range: 'Touch',
    components: ['V', 'S', 'M'],
    duration: 'Concentration, up to 1 minute',
    description: 'You or a willing creature you touch becomes invisible.',
    effectType: 'utility',
    save: null,
    attackRoll: false,
    concentration: true,
    effect: {
      type: 'condition',
      condition: 'invisible',
      attacksWhileInvisible: true
    }
  },

  // 5th Level Spells
  'cone of cold': {
    name: 'Cone of Cold',
    level: SPELL_LEVELS.FIFTH,
    school: MAGIC_SCHOOLS.EVOCATION,
    castingTime: '1 action',
    range: 'Self (60-foot cone)',
    components: ['V', 'S', 'M'],
    duration: 'Instantaneous',
    description: 'A blast of cold air erupts from your hands.',
    effectType: 'damage',
    damage: '12d8',
    damageType: 'cold',
    save: 'constitution',
    halfDamageOnSave: true,
    area: '60-foot cone',
    higherLevelDamage: '1d8',
    concentration: false
  },
  'dominate person': {
    name: 'Dominate Person',
    level: SPELL_LEVELS.FIFTH,
    school: MAGIC_SCHOOLS.ENCHANTMENT,
    castingTime: '1 action',
    range: '60 feet',
    components: ['V', 'S'],
    duration: 'Concentration, up to 1 minute',
    description: 'You attempt to beguile a humanoid that you can see within range.',
    effectType: 'save_or_effect',
    save: 'wisdom',
    concentration: true,
    effect: {
      type: 'dominated',
      duration: '1 minute'
    }
  }
};

/**
 * Get spell by name
 * @param {string} name - Spell name
 * @returns {object|null} Spell data or null
 */
export function getSpell(name) {
  const normalizedName = name.toLowerCase().trim();
  return SPELL_DATABASE[normalizedName] || null;
}

/**
 * Get spells by level
 * @param {number} level - Spell level
 * @returns {Array} Array of spells
 */
export function getSpellsByLevel(level) {
  return Object.values(SPELL_DATABASE).filter(spell => spell.level === level);
}

/**
 * Get spells by school
 * @param {string} school - Magic school
 * @returns {Array} Array of spells
 */
export function getSpellsBySchool(school) {
  return Object.values(SPELL_DATABASE).filter(spell => spell.school === school);
}

/**
 * Search spells by name or description
 * @param {string} query - Search query
 * @returns {Array} Array of matching spells
 */
export function searchSpells(query) {
  const lowerQuery = query.toLowerCase();
  return Object.values(SPELL_DATABASE).filter(spell =>
    spell.name.toLowerCase().includes(lowerQuery) ||
    spell.description.toLowerCase().includes(lowerQuery)
  );
}

/**
 * Get all spell names
 * @returns {Array} Array of spell names
 */
export function getAllSpellNames() {
  return Object.keys(SPELL_DATABASE);
}

export default {
  SPELL_DATABASE,
  getSpell,
  getSpellsByLevel,
  getSpellsBySchool,
  searchSpells,
  getAllSpellNames
};