/**
 * Core type definitions for D&D 5e Rule Engine
 */

// Ability Scores
export const ABILITIES = {
  STRENGTH: 'strength',
  DEXTERITY: 'dexterity',
  CONSTITUTION: 'constitution',
  INTELLIGENCE: 'intelligence',
  WISDOM: 'wisdom',
  CHARISMA: 'charisma'
};

// Skills
export const SKILLS = {
  ATHLETICS: 'athletics',
  ACROBATICS: 'acrobatics',
  SLEIGHT_OF_HAND: 'sleight_of_hand',
  STEALTH: 'stealth',
  ARCANA: 'arcana',
  HISTORY: 'history',
  INVESTIGATION: 'investigation',
  NATURE: 'nature',
  RELIGION: 'religion',
  ANIMAL_HANDLING: 'animal_handling',
  INSIGHT: 'insight',
  MEDICINE: 'medicine',
  PERCEPTION: 'perception',
  SURVIVAL: 'survival',
  DECEPTION: 'deception',
  INTIMIDATION: 'intimidation',
  PERFORMANCE: 'performance',
  PERSUASION: 'persuasion'
};

// Conditions
export const CONDITIONS = {
  BLINDED: 'blinded',
  CHARMED: 'charmed',
  DEAFENED: 'deafened',
  EXHAUSTION: 'exhaustion',
  FRIGHTENED: 'frightened',
  GRAPPLED: 'grappled',
  INCAPACITATED: 'incapacitated',
  INVISIBLE: 'invisible',
  PARALYZED: 'paralyzed',
  PETRIFIED: 'petrified',
  POISONED: 'poisoned',
  PRONE: 'prone',
  RESTRAINED: 'restrained',
  STUNNED: 'stunned',
  UNCONSCIOUS: 'unconscious'
};

// Damage Types
export const DAMAGE_TYPES = {
  ACID: 'acid',
  BLUDGEONING: 'bludgeoning',
  COLD: 'cold',
  FIRE: 'fire',
  FORCE: 'force',
  LIGHTNING: 'lightning',
  NECROTIC: 'necrotic',
  PIERCING: 'piercing',
  POISON: 'poison',
  PSYCHIC: 'psychic',
  RADIANT: 'radiant',
  SLASHING: 'slashing',
  THUNDER: 'thunder'
};

// Magic Schools
export const MAGIC_SCHOOLS = {
  ABJURATION: 'abjuration',
  CONJURATION: 'conjuration',
  DIVINATION: 'divination',
  ENCHANTMENT: 'enchantment',
  EVOCATION: 'evocation',
  ILLUSION: 'illusion',
  NECROMANCY: 'necromancy',
  TRANSMUTATION: 'transmutation'
};

// Spell Levels
export const SPELL_LEVELS = {
  CANTRIP: 0,
  FIRST: 1,
  SECOND: 2,
  THIRD: 3,
  FOURTH: 4,
  FIFTH: 5,
  SIXTH: 6,
  SEVENTH: 7,
  EIGHTH: 8,
  NINTH: 9
};

// Base Character class
export class Character {
  constructor(data) {
    this.id = data.id;
    this.name = data.name;
    this.level = data.level || 1;
    this.class = data.class;
    this.race = data.race;
    this.abilities = data.abilities || {};
    this.skills = data.skills || {};
    this.proficiencyBonus = data.proficiencyBonus || this.calculateProficiencyBonus();
    this.armorClass = data.armorClass || 10;
    this.hitPoints = {
      current: data.hitPoints?.current || data.hitPoints?.maximum || 8,
      maximum: data.hitPoints?.maximum || 8,
      temporary: data.hitPoints?.temporary || 0
    };
    this.conditions = data.conditions || [];
    this.spells = data.spells || {};
    this.features = data.features || [];
    this.inventory = data.inventory || [];
    this.position = data.position || { x: 0, y: 0 };
    this.speed = data.speed || 30;
  }

  calculateProficiencyBonus() {
    return Math.ceil(this.level / 4) + 1;
  }

  getAbilityModifier(ability) {
    const score = this.abilities[ability] || 10;
    return Math.floor((score - 10) / 2);
  }

  getSkillBonus(skill) {
    const ability = this.getSkillAbility(skill);
    const modifier = this.getAbilityModifier(ability);
    const proficiency = this.skills[skill]?.proficient || 0;
    const expertise = this.skills[skill]?.expertise || false;
    const bonus = expertise ? this.proficiencyBonus * 2 : this.proficiencyBonus * proficiency;
    return modifier + bonus;
  }

  getSkillAbility(skill) {
    const skillAbilities = {
      [SKILLS.ATHLETICS]: ABILITIES.STRENGTH,
      [SKILLS.ACROBATICS]: ABILITIES.DEXTERITY,
      [SKILLS.SLEIGHT_OF_HAND]: ABILITIES.DEXTERITY,
      [SKILLS.STEALTH]: ABILITIES.DEXTERITY,
      [SKILLS.ARCANA]: ABILITIES.INTELLIGENCE,
      [SKILLS.HISTORY]: ABILITIES.INTELLIGENCE,
      [SKILLS.INVESTIGATION]: ABILITIES.INTELLIGENCE,
      [SKILLS.NATURE]: ABILITIES.INTELLIGENCE,
      [SKILLS.RELIGION]: ABILITIES.INTELLIGENCE,
      [SKILLS.ANIMAL_HANDLING]: ABILITIES.WISDOM,
      [SKILLS.INSIGHT]: ABILITIES.WISDOM,
      [SKILLS.MEDICINE]: ABILITIES.WISDOM,
      [SKILLS.PERCEPTION]: ABILITIES.WISDOM,
      [SKILLS.SURVIVAL]: ABILITIES.WISDOM,
      [SKILLS.DECEPTION]: ABILITIES.CHARISMA,
      [SKILLS.INTIMIDATION]: ABILITIES.CHARISMA,
      [SKILLS.PERFORMANCE]: ABILITIES.CHARISMA,
      [SKILLS.PERSUASION]: ABILITIES.CHARISMA
    };
    return skillAbilities[skill] || ABILITIES.STRENGTH;
  }

  hasCondition(condition) {
    return this.conditions.includes(condition);
  }

  addCondition(condition) {
    if (!this.hasCondition(condition)) {
      this.conditions.push(condition);
    }
  }

  removeCondition(condition) {
    this.conditions = this.conditions.filter(c => c !== condition);
  }

  takeDamage(amount) {
    // Remove temporary HP first
    const tempAbsorbed = Math.min(this.hitPoints.temporary, amount);
    this.hitPoints.temporary -= tempAbsorbed;
    const remainingDamage = amount - tempAbsorbed;

    // Apply remaining damage to current HP
    this.hitPoints.current = Math.max(0, this.hitPoints.current - remainingDamage);

    // Check for death saves
    if (this.hitPoints.current === 0) {
      this.addCondition(CONDITIONS.UNCONSCIOUS);
    }
  }

  heal(amount) {
    const maxHeal = this.hitPoints.maximum - this.hitPoints.current;
    this.hitPoints.current += Math.min(amount, maxHeal);

    // Remove unconscious condition if healed above 0
    if (this.hitPoints.current > 0) {
      this.removeCondition(CONDITIONS.UNCONSCIOUS);
    }
  }
}

// Roll result class
export class RollResult {
  constructor(dice, modifier = 0, advantage = 0, critical = false) {
    this.dice = dice;
    this.modifier = modifier;
    this.advantage = advantage; // -1 disadvantage, 0 normal, 1 advantage
    this.critical = critical;
    this.rolls = [];
    this.total = 0;
    this.natural20 = false;
    this.natural1 = false;
  }

  calculateTotal() {
    let rollValue = this.rolls[this.advantage > 0 ? Math.max(...this.rolls) : Math.min(...this.rolls)];
    this.total = rollValue + this.modifier;
    this.natural20 = this.rolls.includes(20);
    this.natural1 = this.rolls.includes(1);
    return this.total;
  }

  isCriticalSuccess() {
    return this.natural20 && !this.natural1;
  }

  isCriticalFailure() {
    return this.natural1 && !this.natural20;
  }
}

// Combat encounter class
export class Combat {
  constructor(id) {
    this.id = id;
    this.participants = [];
    this.currentTurn = 0;
    this.round = 1;
    this.turnOrder = [];
    this.active = false;
    this.environment = {};
  }

  addParticipant(character, initiative = null) {
    const participant = {
      character,
      initiative: initiative !== null ? initiative : this.rollInitiative(character),
      id: character.id
    };
    this.participants.push(participant);
    this.updateTurnOrder();
  }

  rollInitiative(character) {
    const dexterityMod = character.getAbilityModifier(ABILITIES.DEXTERITY);
    const roll = Math.floor(Math.random() * 20) + 1;
    return roll + dexterityMod;
  }

  updateTurnOrder() {
    this.turnOrder = [...this.participants]
      .sort((a, b) => b.initiative - a.initiative)
      .map(p => p.id);
  }

  getCurrentParticipant() {
    if (this.turnOrder.length === 0) return null;
    const currentId = this.turnOrder[this.currentTurn];
    return this.participants.find(p => p.id === currentId);
  }

  nextTurn() {
    this.currentTurn = (this.currentTurn + 1) % this.turnOrder.length;
    if (this.currentTurn === 0) {
      this.round++;
    }
  }

  start() {
    this.active = true;
    this.currentTurn = 0;
    this.round = 1;
  }

  end() {
    this.active = false;
  }
}

export default {
  ABILITIES,
  SKILLS,
  CONDITIONS,
  DAMAGE_TYPES,
  MAGIC_SCHOOLS,
  SPELL_LEVELS,
  Character,
  RollResult,
  Combat
};