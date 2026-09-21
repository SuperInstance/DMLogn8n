/**
 * Main D&D 5e Rule Engine
 */

import { DiceRoller } from './DiceRoller.js';
import {
  ABILITIES,
  SKILLS,
  CONDITIONS,
  Character,
  RollResult,
  Combat
} from '../types/index.js';

export class RuleEngine {
  constructor() {
    this.combatEncounters = new Map();
    this.globalRules = {
      criticalHitDamage: 2,
      exhaustionMaxLevel: 6,
      deathSaveSuccessCount: 3,
      deathSaveFailureCount: 3
    };
  }

  /**
   * Perform an ability check
   * @param {Character} character - Character making the check
   * @param {string} ability - Ability being checked
   * @param {number} dc - Difficulty class
   * @param {number} advantage - Advantage state
   * @param {number} bonus - Additional bonus
   * @returns {object} Check result
   */
  abilityCheck(character, ability, dc, advantage = 0, bonus = 0) {
    if (!Object.values(ABILITIES).includes(ability)) {
      throw new Error(`Invalid ability: ${ability}`);
    }

    const modifier = character.getAbilityModifier(ability);
    const totalBonus = modifier + bonus;
    const roll = DiceRoller.rollD20(advantage);

    const result = {
      type: 'ability_check',
      ability,
      character: character.name,
      dc,
      roll,
      bonus: totalBonus,
      total: roll.total + totalBonus,
      success: (roll.total + totalBonus) >= dc,
      critical: roll.isCritical,
      fumble: roll.isFumble
    };

    // Apply condition effects
    this.applyConditionEffects(character, result);

    return result;
  }

  /**
   * Perform a skill check
   * @param {Character} character - Character making the check
   * @param {string} skill - Skill being checked
   * @param {number} dc - Difficulty class
   * @param {number} advantage - Advantage state
   * @param {number} bonus - Additional bonus
   * @returns {object} Check result
   */
  skillCheck(character, skill, dc, advantage = 0, bonus = 0) {
    if (!Object.values(SKILLS).includes(skill)) {
      throw new Error(`Invalid skill: ${skill}`);
    }

    const skillBonus = character.getSkillBonus(skill);
    const totalBonus = skillBonus + bonus;
    const roll = DiceRoller.rollD20(advantage);

    const result = {
      type: 'skill_check',
      skill,
      ability: character.getSkillAbility(skill),
      character: character.name,
      dc,
      roll,
      bonus: totalBonus,
      total: roll.total + totalBonus,
      success: (roll.total + totalBonus) >= dc,
      critical: roll.isCritical,
      fumble: roll.isFumble
    };

    // Apply condition effects
    this.applyConditionEffects(character, result);

    return result;
  }

  /**
   * Perform a saving throw
   * @param {Character} character - Character making the save
   * @param {string} ability - Saving throw ability
   * @param {number} dc - Difficulty class
   * @param {number} advantage - Advantage state
   * @param {number} bonus - Additional bonus
   * @returns {object} Save result
   */
  savingThrow(character, ability, dc, advantage = 0, bonus = 0) {
    if (!Object.values(ABILITIES).includes(ability)) {
      throw new Error(`Invalid ability for saving throw: ${ability}`);
    }

    const modifier = character.getAbilityModifier(ability);
    const proficiencyBonus = this.getSavingThrowProficiency(character, ability);
    const totalBonus = modifier + proficiencyBonus + bonus;
    const roll = DiceRoller.rollD20(advantage);

    const result = {
      type: 'saving_throw',
      ability,
      character: character.name,
      dc,
      roll,
      bonus: totalBonus,
      total: roll.total + totalBonus,
      success: (roll.total + totalBonus) >= dc,
      critical: roll.isCritical,
      fumble: roll.isFumble
    };

    // Apply condition effects
    this.applyConditionEffects(character, result);

    return result;
  }

  /**
   * Perform an attack roll
   * @param {Character} attacker - Attacking character
   * @param {Character} defender - Defending character
   * @param {string} attackType - 'melee' or 'ranged'
   * @param {number} advantage - Advantage state
   * @param {number} bonus - Additional bonus
   * @returns {object} Attack result
   */
  attackRoll(attacker, defender, attackType = 'melee', advantage = 0, bonus = 0) {
    const ability = attackType === 'ranged' ? ABILITIES.DEXTERITY : ABILITIES.STRENGTH;
    const modifier = attacker.getAbilityModifier(ability);
    const proficiencyBonus = attacker.proficiencyBonus;
    const totalBonus = modifier + proficiencyBonus + bonus;

    const roll = DiceRoller.rollD20(advantage);
    const ac = defender.armorClass;
    const total = roll.total + totalBonus;

    const result = {
      type: 'attack_roll',
      attacker: attacker.name,
      defender: defender.name,
      attackType,
      roll,
      bonus: totalBonus,
      total,
      targetAC: ac,
      hit: total >= ac,
      critical: roll.isCritical,
      fumble: roll.isFumble
    };

    // Apply condition effects
    this.applyConditionEffects(attacker, result);
    this.applyCoverEffects(defender, result);

    return result;
  }

  /**
   * Roll damage for an attack
   * @param {Character} attacker - Attacking character
   * @param {string} damageExpression - Damage dice expression
   * @param {string} damageType - Type of damage
   * @param {boolean} critical - Whether this is a critical hit
   * @param {number} bonus - Damage bonus
   * @returns {object} Damage result
   */
  rollDamage(attacker, damageExpression, damageType, critical = false, bonus = 0) {
    const damageRoll = DiceRoller.rollDamage(damageExpression, critical);
    const totalDamage = damageRoll.total + bonus;

    return {
      type: 'damage',
      attacker: attacker.name,
      damageExpression,
      damageType,
      damageRoll,
      bonus,
      total: totalDamage,
      critical
    };
  }

  /**
   * Apply damage to a character
   * @param {Character} target - Target character
   * @param {number} amount - Damage amount
   * @param {string} damageType - Type of damage
   * @param {boolean} critical - Whether this was a critical hit
   * @returns {object} Damage application result
   */
  applyDamage(target, amount, damageType, critical = false) {
    const originalHP = target.hitPoints.current;
    const originalTemp = target.hitPoints.temporary;

    // Check for damage resistance/immunity/vulnerability
    let finalAmount = this.calculateDamageReduction(target, amount, damageType);

    target.takeDamage(finalAmount);

    const result = {
      target: target.name,
      amount,
      damageType,
      reducedAmount: finalAmount,
      originalHP,
      originalTemp,
      newHP: target.hitPoints.current,
      newTempHP: target.hitPoints.temporary,
      damageTaken: originalHP - target.hitPoints.current,
      tempHPConsumed: originalTemp - target.hitPoints.temporary,
      critical,
      knockedUnconscious: target.hasCondition(CONDITIONS.UNCONSCIOUS)
    };

    return result;
  }

  /**
   * Create a new combat encounter
   * @param {string} encounterId - Unique identifier for the encounter
   * @returns {Combat} New combat encounter
   */
  createCombat(encounterId) {
    const combat = new Combat(encounterId);
    this.combatEncounters.set(encounterId, combat);
    return combat;
  }

  /**
   * Get a combat encounter by ID
   * @param {string} encounterId - Combat encounter ID
   * @returns {Combat|null} Combat encounter or null
   */
  getCombat(encounterId) {
    return this.combatEncounters.get(encounterId) || null;
  }

  /**
   * End a combat encounter
   * @param {string} encounterId - Combat encounter ID
   */
  endCombat(encounterId) {
    const combat = this.combatEncounters.get(encounterId);
    if (combat) {
      combat.end();
      this.combatEncounters.delete(encounterId);
    }
  }

  /**
   * Calculate saving throw proficiency bonus
   * @param {Character} character - Character to check
   * @param {string} ability - Ability being saved with
   * @returns {number} Proficiency bonus
   */
  getSavingThrowProficiency(character, ability) {
    // Check for class features that grant proficiency
    const hasProficiency = character.features?.some(feature =>
      feature.type === 'saving_throw_proficiency' &&
      feature.ability === ability
    ) || false;

    return hasProficiency ? character.proficiencyBonus : 0;
  }

  /**
   * Apply condition effects to a roll result
   * @param {Character} character - Character with conditions
   * @param {object} result - Roll result to modify
   */
  applyConditionEffects(character, result) {
    // Blinded - disadvantage on attack rolls, automatic fail on sight-based checks
    if (character.hasCondition(CONDITIONS.BLINDED)) {
      if (result.type === 'attack_roll') {
        result.blindedPenalty = true;
        if (result.advantage > 0) {
          result.advantage = 0; // Cancels advantage
        } else {
          result.advantage = -1; // Adds disadvantage
        }
      }
    }

    // Deafened - disadvantage on perception checks
    if (character.hasCondition(CONDITIONS.DEAFENED) && result.skill === SKILLS.PERCEPTION) {
      result.deafenedPenalty = true;
      result.advantage = -1;
    }

    // Frightened - disadvantage on ability checks while source is visible
    if (character.hasCondition(CONDITIONS.FRIGHTENED)) {
      result.frightenedPenalty = true;
      result.advantage = -1;
    }

    // Poisoned - disadvantage on attack rolls and ability checks
    if (character.hasCondition(CONDITIONS.POISONED)) {
      if (result.type === 'attack_roll' || result.type === 'ability_check' || result.type === 'skill_check') {
        result.poisonedPenalty = true;
        result.advantage = -1;
      }
    }

    // Restrained - disadvantage on Dexterity saving throws
    if (character.hasCondition(CONDITIONS.RESTRAINED) && result.ability === ABILITIES.DEXTERITY) {
      result.restrainedPenalty = true;
      result.advantage = -1;
    }

    // Stunned - automatic failure on saving throws
    if (character.hasCondition(CONDITIONS.STUNNED) && result.type === 'saving_throw') {
      result.stunnedPenalty = true;
      result.success = false;
    }
  }

  /**
   * Apply cover effects to an attack
   * @param {Character} defender - Defending character
   * @param {object} result - Attack result to modify
   */
  applyCoverEffects(defender, result) {
    // This would be enhanced with position data from combat system
    // For now, basic implementation
    if (defender.cover === 'half') {
      result.cover = 'half';
      result.targetAC += 2;
      result.hit = result.total >= result.targetAC;
    } else if (defender.cover === 'three-quarters') {
      result.cover = 'three-quarters';
      result.targetAC += 3;
      result.hit = result.total >= result.targetAC;
    } else if (defender.cover === 'full') {
      result.cover = 'full';
      result.hit = false;
      result.reason = 'Full cover';
    }
  }

  /**
   * Calculate damage reduction from resistances/immunities
   * @param {Character} target - Target character
   * @param {number} amount - Original damage amount
   * @param {string} damageType - Type of damage
   * @returns {number} Reduced damage amount
   */
  calculateDamageReduction(target, amount, damageType) {
    let reducedAmount = amount;

    // Check for immunity
    if (target.immunities?.includes(damageType)) {
      reducedAmount = 0;
    }
    // Check for resistance
    else if (target.resistances?.includes(damageType)) {
      reducedAmount = Math.floor(amount / 2);
    }
    // Check for vulnerability
    else if (target.vulnerabilities?.includes(damageType)) {
      reducedAmount = amount * 2;
    }

    return reducedAmount;
  }

  /**
   * Validate a character's data against D&D 5e rules
   * @param {Character} character - Character to validate
   * @returns {object} Validation result
   */
  validateCharacter(character) {
    const errors = [];
    const warnings = [];

    // Validate ability scores
    for (const [ability, score] of Object.entries(character.abilities)) {
      if (score < 1 || score > 20) {
        errors.push(`Invalid ${ability} score: ${score} (must be 1-20)`);
      }
    }

    // Validate hit points
    if (character.hitPoints.current < 0) {
      errors.push('Current hit points cannot be negative');
    }
    if (character.hitPoints.current > character.hitPoints.maximum) {
      warnings.push('Current hit points exceed maximum');
    }

    // Validate proficiency bonus
    const expectedProficiency = Math.ceil(character.level / 4) + 1;
    if (character.proficiencyBonus !== expectedProficiency) {
      warnings.push(`Proficiency bonus is ${character.proficiencyBonus}, expected ${expectedProficiency} for level ${character.level}`);
    }

    // Validate AC
    if (character.armorClass < 1) {
      errors.push('Armor class cannot be less than 1');
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }
}

export default RuleEngine;