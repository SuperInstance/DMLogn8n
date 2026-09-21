/**
 * Saving Throws System
 */

import { ABILITIES, CONDITIONS } from '../types/index.js';
import { DiceRoller } from '../core/DiceRoller.js';

export class SavingThrows {
  /**
   * Perform a saving throw
   * @param {Character} character - Character making the save
   * @param {string} ability - Ability for the save
   * @param {number} dc - Difficulty class
   * @param {object} options - Additional options
   * @returns {object} Save result
   */
  static performSave(character, ability, dc, options = {}) {
    const {
      advantage = 0,
      bonus = 0,
      magicalResistance = false,
      legendaryResistance = false,
      deathSave = false,
      damageType = null
    } = options;

    // Validate ability
    if (!Object.values(ABILITIES).includes(ability)) {
      throw new Error(`Invalid ability for saving throw: ${ability}`);
    }

    const modifier = character.getAbilityModifier(ability);
    const proficiencyBonus = this.getProficiencyBonus(character, ability);
    let totalBonus = modifier + proficiencyBonus + bonus;

    // Apply magical resistance (advantage on saves vs magic)
    let finalAdvantage = advantage;
    if (magicalResistance && this.isMagicalEffect(damageType)) {
      finalAdvantage = Math.max(1, finalAdvantage);
    }

    // Legendary resistance - automatic success
    if (legendaryResistance) {
      return {
        type: 'saving_throw',
        character: character.name,
        ability,
        dc,
        legendaryResistance: true,
        success: true,
        total: dc + 1,
        description: 'Automatically succeeded due to legendary resistance'
      };
    }

    // Death saving throw special rules
    if (deathSave) {
      return this.performDeathSave(character, finalAdvantage);
    }

    // Regular saving throw
    const roll = DiceRoller.rollD20(finalAdvantage);
    const total = roll.total + totalBonus;
    const success = total >= dc;

    const result = {
      type: 'saving_throw',
      character: character.name,
      ability,
      dc,
      roll,
      bonus: totalBonus,
      total,
      success,
      critical: roll.isCritical,
      fumble: roll.isFumble,
      damageType,
      magicalResistance,
      degreeOfSuccess: this.calculateDegreeOfSuccess(total, dc)
    };

    // Apply special effects based on critical success/failure
    if (roll.isCritical) {
      result.criticalEffect = this.getCriticalSaveEffect(ability, success);
    }

    return result;
  }

  /**
   * Perform a death saving throw
   * @param {Character} character - Character making the death save
   * @param {number} advantage - Advantage state
   * @returns {object} Death save result
   */
  static performDeathSave(character, advantage = 0) {
    const roll = DiceRoller.rollD20(advantage);
    let result;

    if (roll.natural20) {
      // Natural 20 - regain 1 HP
      character.hitPoints.current = 1;
      character.removeCondition(CONDITIONS.UNCONSCIOUS);
      result = {
        type: 'death_save',
        character: character.name,
        roll,
        success: true,
        critical: true,
        effect: 'stabilized_with_1_hp',
        description: 'Natural 20! Character regains 1 hit point and is no longer unconscious.'
      };
    } else if (roll.natural1) {
      // Natural 1 - two failures
      result = {
        type: 'death_save',
        character: character.name,
        roll,
        success: false,
        critical: true,
        effect: 'two_failures',
        description: 'Natural 1! Character suffers two death save failures.'
      };
    } else if (roll.total >= 10) {
      // Success
      result = {
        type: 'death_save',
        character: character.name,
        roll,
        success: true,
        effect: 'success',
        description: 'Death save successful.'
      };
    } else {
      // Failure
      result = {
        type: 'death_save',
        character: character.name,
        roll,
        success: false,
        effect: 'failure',
        description: 'Death save failed.'
      };
    }

    return result;
  }

  /**
   * Get proficiency bonus for a specific ability save
   * @param {Character} character - Character to check
   * @param {string} ability - Ability for the save
   * @returns {number} Proficiency bonus
   */
  static getProficiencyBonus(character, ability) {
    // Check class features for saving throw proficiency
    const hasProficiency = character.features?.some(feature =>
      (feature.type === 'saving_throw_proficiency' && feature.ability === ability) ||
      (feature.type === 'all_saving_throws_proficient')
    ) || false;

    // Check for specific class features (like Cleric's Divine Magic)
    if (character.class === 'cleric' && ability === ABILITIES.WISDOM) {
      hasProficiency = true;
    }

    return hasProficiency ? character.proficiencyBonus : 0;
  }

  /**
   * Check if an effect is magical
   * @param {string} damageType - Damage type to check
   * @returns {boolean} Whether the effect is magical
   */
  static isMagicalEffect(damageType) {
    const magicalTypes = [
      'force', 'necrotic', 'psychic', 'radiant',
      'thunder', 'lightning', 'cold', 'fire'
    ];
    return magicalTypes.includes(damageType) || damageType?.includes('magic');
  }

  /**
   * Calculate degree of success for saving throws
   * @param {number} total - Total roll result
   * @param {number} dc - Difficulty class
   * @returns {string} Degree of success
   */
  static calculateDegreeOfSuccess(total, dc) {
    const difference = total - dc;

    if (difference >= 10) return 'overwhelming_success';
    if (difference >= 5) return 'moderate_success';
    if (difference >= 0) return 'success';
    if (difference >= -5) return 'failure';
    return 'critical_failure';
  }

  /**
   * Get special effects for critical saves
   * @param {string} ability - Ability used for save
   * @param {boolean} success - Whether save was successful
   * @returns {string} Critical effect description
   */
  static getCriticalSaveEffect(ability, success) {
    if (!success) {
      return 'critical_failure';
    }

    const criticalEffects = {
      [ABILITIES.STRENGTH]: 'resisted with incredible force',
      [ABILITIES.DEXTERITY]: 'easily evaded the effect',
      [ABILITIES.CONSTITUTION]: 'completely resisted the effect',
      [ABILITIES.INTELLIGENCE]: 'intellectually overcame the effect',
      [ABILITIES.WISDOM]: 'willpower completely resisted the effect',
      [ABILITIES.CHARISMA]: 'personality overwhelmed the effect'
    };

    return criticalEffects[ability] || 'critical_success';
  }

  /**
   * Perform a group saving throw
   * @param {Character[]} characters - Characters making the save
   * @param {string} ability - Ability for the save
   * @param {number} dc - Difficulty class
   * @param {object} options - Additional options
   * @returns {object} Group save result
   */
  static performGroupSave(characters, ability, dc, options = {}) {
    const results = characters.map(character =>
      this.performSave(character, ability, dc, options)
    );

    const successes = results.filter(result => result.success).length;
    const criticalSuccesses = results.filter(result => result.critical && result.success).length;
    const criticalFailures = results.filter(result => result.critical && !result.success).length;

    return {
      type: 'group_saving_throw',
      ability,
      dc,
      characters: characters.map(c => c.name),
      results,
      successes,
      failures: results.length - successes,
      criticalSuccesses,
      criticalFailures,
      successRate: (successes / results.length) * 100
    };
  }

  /**
   * Get saving throw information
   * @param {string} ability - Ability name
   * @returns {object} Save information
   */
  static getSaveInfo(ability) {
    const saveData = {
      [ABILITIES.STRENGTH]: {
        name: 'Strength Saving Throw',
        description: 'Resist effects that would physically restrain, move, or harm you',
        examples: ['Being grappled', 'Forced movement', 'Paralysis effects']
      },
      [ABILITIES.DEXTERITY]: {
        name: 'Dexterity Saving Throw',
        description: 'Dodge area effects and agile reflexes',
        examples: ['Fireball', 'Lightning bolt', 'Falling debris', 'Traps']
      },
      [ABILITIES.CONSTITUTION]: {
        name: 'Constitution Saving Throw',
        description: 'Endure physical stress and harmful effects',
        examples: ['Poison', 'Disease', 'Exhaustion', 'Endurance tests']
      },
      [ABILITIES.INTELLIGENCE]: {
        name: 'Intelligence Saving Throw',
        description: 'Resist mental effects that attack reason',
        examples: ['Illusions', 'Memory loss', 'Confusion effects']
      },
      [ABILITIES.WISDOM]: {
        name: 'Wisdom Saving Throw',
        description: 'Resist effects that attack willpower or perception',
        examples: ['Charm', 'Fright', 'Mind control', 'Deception']
      },
      [ABILITIES.CHARISMA]: {
        name: 'Charisma Saving Throw',
        description: 'Resist effects that attack personality or force of will',
        examples: ['Banishment', 'Possession', 'Personality-altering effects']
      }
    };

    return saveData[ability] || null;
  }

  /**
   * Get situational modifiers for saving throws
   * @param {string} situation - Situation description
   * @returns {object} Modifiers and description
   */
  static getSituationalModifiers(situation) {
    const modifiers = {
      'bless_spell': { bonus: 1d4, description: 'Bless spell bonus' },
      'bane_spell': { bonus: -1d4, description: 'Bane spell penalty' },
      'protection_from_evil': { advantage: 1, description: 'Advantage vs evil creatures' },
      'shield_spell': { bonus: 5, description: 'Shield spell bonus' },
      'resilient_feat': { proficiency: true, description: 'Resilient feat proficiency' },
      'war_caster': { advantage: 1, description: 'War Caster advantage on concentration saves' }
    };

    return modifiers[situation] || { bonus: 0, description: 'No special modifiers' };
  }

  /**
   * Calculate concentration save DC
   * @param {number} damageTaken - Amount of damage taken
   * @returns {number} Concentration save DC
   */
  static calculateConcentrationDC(damageTaken) {
    return Math.max(10, Math.floor(damageTaken / 2));
  }

  /**
   * Perform concentration save
   * @param {Character} character - Character maintaining concentration
   * @param {number} damageTaken - Damage taken
   * @param {object} options - Additional options
   * @returns {object} Concentration save result
   */
  static performConcentrationSave(character, damageTaken, options = {}) {
    const dc = this.calculateConcentrationDC(damageTaken);
    const result = this.performSave(character, ABILITIES.CONSTITUTION, dc, {
      ...options,
      concentration: true
    });

    result.concentration = {
      damageTaken,
      dc,
      maintained: result.success
    };

    if (!result.success) {
      // Remove concentration spell effects
      character.spells = character.spells?.filter(spell => !spell.concentration) || [];
    }

    return result;
  }
}

export default SavingThrows;