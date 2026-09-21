/**
 * Ability Checks System
 */

import { ABILITIES } from '../types/index.js';
import { DiceRoller } from '../core/DiceRoller.js';

export class AbilityChecks {
  /**
   * Perform a standard ability check
   * @param {Character} character - Character making the check
   * @param {string} ability - Ability to check
   * @param {number} dc - Difficulty class
   * @param {object} options - Additional options
   * @returns {object} Check result
   */
  static performCheck(character, ability, dc, options = {}) {
    const {
      advantage = 0,
      bonus = 0,
      contextualBonus = 0,
      expertiseDie = null,
      reliableTalent = false,
      jackOfAllTrades = false
    } = options;

    // Validate ability
    if (!Object.values(ABILITIES).includes(ability)) {
      throw new Error(`Invalid ability: ${ability}`);
    }

    // Calculate base modifier
    const abilityModifier = character.getAbilityModifier(ability);
    let totalBonus = abilityModifier + bonus + contextualBonus;

    // Apply jack of all trades (half proficiency rounded down)
    if (jackOfAllTrades && !character.skills?.[ability]?.proficient) {
      totalBonus += Math.floor(character.proficiencyBonus / 2);
    }

    // Roll the dice
    const roll = DiceRoller.rollD20(advantage);

    // Apply reliable talent (treat rolls below 10 as 10)
    let adjustedRoll = roll.total;
    if (reliableTalent && adjustedRoll < 10) {
      adjustedRoll = 10;
    }

    // Add expertise die if available
    let expertiseResult = null;
    if (expertiseDie) {
      expertiseResult = DiceRoller.rollExpression(expertiseDie);
      totalBonus += expertiseResult.total;
    }

    const total = adjustedRoll + totalBonus;
    const success = total >= dc;

    return {
      type: 'ability_check',
      character: character.name,
      ability,
      dc,
      roll,
      adjustedRoll,
      bonus: totalBonus,
      contextualBonus,
      expertiseResult,
      total,
      success,
      critical: roll.isCritical,
      fumble: roll.isFumble,
      degreeOfSuccess: this.calculateDegreeOfSuccess(total, dc),
      reliableTalent: reliableTalent && roll.total < 10
    };
  }

  /**
   * Perform a contested ability check
   * @param {Character} character1 - First character
   * @param {string} ability1 - First character's ability
   * @param {Character} character2 - Second character
   * @param {string} ability2 - Second character's ability
   * @param {object} options - Additional options
   * @returns {object} Contest result
   */
  static performContest(character1, ability1, character2, ability2, options = {}) {
    const {
      advantage1 = 0,
      advantage2 = 0,
      bonus1 = 0,
      bonus2 = 0
    } = options;

    const check1 = this.performCheck(character1, ability1, 0, {
      advantage: advantage1,
      bonus: bonus1,
      ...options
    });

    const check2 = this.performCheck(character2, ability2, 0, {
      advantage: advantage2,
      bonus: bonus2,
      ...options
    });

    const winner = check1.total > check2.total ? character1.name :
                   check2.total > check1.total ? character2.name : 'tie';

    return {
      type: 'contested_ability_check',
      contestant1: {
        character: character1.name,
        ability: ability1,
        result: check1
      },
      contestant2: {
        character: character2.name,
        ability: ability2,
        result: check2
      },
      winner,
      margin: Math.abs(check1.total - check2.total)
    };
  }

  /**
   * Calculate degree of success for an ability check
   * @param {number} total - Total roll result
   * @param {number} dc - Difficulty class
   * @returns {string} Degree of success
   */
  static calculateDegreeOfSuccess(total, dc) {
    const difference = total - dc;

    if (difference >= 10) return 'critical_success';
    if (difference >= 5) return 'success';
    if (difference >= 0) return 'partial_success';
    if (difference >= -5) return 'failure';
    return 'critical_failure';
  }

  /**
   * Get ability check description
   * @param {string} ability - Ability name
   * @returns {object} Ability information
   */
  static getAbilityInfo(ability) {
    const abilityData = {
      [ABILITIES.STRENGTH]: {
        name: 'Strength',
        description: 'Measures physical power, athletic training, and force exerted',
        examples: ['Breaking down doors', 'Climbing', 'Jumping', 'Swimming']
      },
      [ABILITIES.DEXTERITY]: {
        name: 'Dexterity',
        description: 'Measures agility, reflexes, and balance',
        examples: ['Acrobatics', 'Sleight of hand', 'Stealth', 'Ranged attacks']
      },
      [ABILITIES.CONSTITUTION]: {
        name: 'Constitution',
        description: 'Measures health, stamina, and vital force',
        examples: ['Endurance', 'Resisting poison', 'Holding breath']
      },
      [ABILITIES.INTELLIGENCE]: {
        name: 'Intelligence',
        description: 'Measures reasoning, memory, and analytical ability',
        examples: ['Recalling lore', 'Solving puzzles', 'Investigation']
      },
      [ABILITIES.WISDOM]: {
        name: 'Wisdom',
        description: 'Measures perception, intuition, and insight',
        examples: ['Perception', 'Insight', 'Survival', 'Medicine']
      },
      [ABILITIES.CHARISMA]: {
        name: 'Charisma',
        description: 'Measures force of personality, persuasiveness, and leadership',
        examples: ['Performance', 'Persuasion', 'Deception', 'Intimidation']
      }
    };

    return abilityData[ability] || null;
  }

  /**
   * Calculate suggested DC for ability checks
   * @param {string} difficulty - Difficulty level
   * @returns {number} Suggested DC
   */
  static getSuggestedDC(difficulty) {
    const dcMap = {
      'very_easy': 5,
      'easy': 10,
      'medium': 15,
      'hard': 20,
      'very_hard': 25,
      'nearly_impossible': 30
    };

    return dcMap[difficulty] || 15;
  }

  /**
   * Generate ability check modifiers based on situation
   * @param {string} situation - Situation description
   * @returns {object} Modifiers and bonuses
   */
  static getSituationalModifiers(situation) {
    const modifiers = {
      'favorable_conditions': { advantage: 1, description: 'Favorable conditions' },
      'unfavorable_conditions': { advantage: -1, description: 'Unfavorable conditions' },
      'circumstance_bonus': { bonus: 2, description: 'Circumstance bonus' },
      'circumstance_penalty': { bonus: -2, description: 'Circumstance penalty' },
      'enhanced_ability': { bonus: 5, description: 'Enhanced ability' },
      'impaired_ability': { bonus: -5, description: 'Impaired ability' }
    };

    return modifiers[situation] || { bonus: 0, description: 'No special modifiers' };
  }
}

export default AbilityChecks;