/**
 * Comprehensive Condition System for D&D 5e
 * Handles all 15 official conditions plus custom conditions
 */

import { CONDITIONS, ABILITIES, SKILLS } from '../types/index.js';

export class ConditionSystem {
  constructor() {
    this.activeConditions = new Map(); // characterId -> Set of conditions
    this.conditionTimers = new Map(); // characterId -> Map of condition -> duration
    this.conditionHistory = new Map(); // characterId -> Array of past conditions
  }

  /**
   * Apply a condition to a character
   * @param {Character} character - Target character
   * @param {string} condition - Condition to apply
   * @param {object} options - Condition options
   * @returns {object} Condition application result
   */
  applyCondition(character, condition, options = {}) {
    const { duration = null, source = 'unknown', saveEnd = false } = options;

    // Validate condition
    if (!this.isValidCondition(condition)) {
      throw new Error(`Invalid condition: ${condition}`);
    }

    // Check for immunity
    if (this.hasImmunity(character, condition)) {
      return {
        success: false,
        reason: `${character.name} is immune to ${condition}`,
        condition,
        character: character.name
      };
    }

    // Check if condition is already active
    if (character.hasCondition(condition)) {
      // For exhaustion, add levels
      if (condition === CONDITIONS.EXHAUSTION) {
        return this.updateExhaustionLevel(character, 1, options);
      }
      return {
        success: false,
        reason: `${character.name} already has ${condition}`,
        condition,
        character: character.name
      };
    }

    // Check for conflicting conditions
    const conflictResult = this.handleConditionConflicts(character, condition);
    if (conflictResult.conflict) {
      // Remove conflicting conditions
      conflictResult.removed.forEach(conflictCondition => {
        character.removeCondition(conflictCondition);
      });
    }

    // Apply the condition
    character.addCondition(condition);

    // Set up condition tracking
    if (!this.activeConditions.has(character.id)) {
      this.activeConditions.set(character.id, new Set());
    }
    this.activeConditions.get(character.id).add(condition);

    // Set duration if specified
    if (duration !== null) {
      this.setConditionDuration(character.id, condition, duration);
    }

    // Apply immediate effects
    const immediateEffects = this.applyImmediateEffects(character, condition);

    // Log condition application
    this.logConditionEvent(character.id, {
      type: 'condition_applied',
      condition,
      duration,
      source,
      timestamp: new Date(),
      immediateEffects
    });

    return {
      success: true,
      condition,
      character: character.name,
      effects: this.getConditionEffects(condition),
      immediateEffects,
      duration,
      conflictsResolved: conflictResult.conflict ? conflictResult.removed : []
    };
  }

  /**
   * Remove a condition from a character
   * @param {Character} character - Target character
   * @param {string} condition - Condition to remove
   * @param {object} options - Removal options
   * @returns {object} Condition removal result
   */
  removeCondition(character, condition, options = {}) {
    const { reason = 'manual', source = 'unknown' } = options;

    if (!character.hasCondition(condition)) {
      return {
        success: false,
        reason: `${character.name} does not have ${condition}`,
        condition,
        character: character.name
      };
    }

    // Remove the condition
    character.removeCondition(condition);

    // Update active conditions tracking
    if (this.activeConditions.has(character.id)) {
      this.activeConditions.get(character.id).delete(condition);
    }

    // Clear condition timer
    if (this.conditionTimers.has(character.id)) {
      this.conditionTimers.get(character.id).delete(condition);
    }

    // Apply removal effects
    const removalEffects = this.applyRemovalEffects(character, condition);

    // Log condition removal
    this.logConditionEvent(character.id, {
      type: 'condition_removed',
      condition,
      reason,
      source,
      timestamp: new Date(),
      removalEffects
    });

    return {
      success: true,
      condition,
      character: character.name,
      reason,
      removalEffects
    };
  }

  /**
   * Update condition durations (called at start of turn)
   * @param {string} characterId - Character identifier
   * @returns {Array} Array of expired conditions
   */
  updateConditionDurations(characterId) {
    const expiredConditions = [];
    const timers = this.conditionTimers.get(characterId);

    if (!timers) return expiredConditions;

    for (const [condition, duration] of timers.entries()) {
      const newDuration = duration - 1;

      if (newDuration <= 0) {
        // Condition expired
        expiredConditions.push(condition);
        timers.delete(condition);
      } else {
        // Update duration
        timers.set(condition, newDuration);
      }
    }

    return expiredConditions;
  }

  /**
   * Get condition effects and rules
   * @param {string} condition - Condition name
   * @returns {object} Condition effects
   */
  getConditionEffects(condition) {
    const effects = {
      [CONDITIONS.BLINDED]: {
        description: 'A blinded creature can\'t see and automatically fails any ability check that requires sight.',
        attackRolls: 'Disadvantage',
        perceptionChecks: 'Automatic failure',
        effects: [
          'Attack rolls have disadvantage',
          'Perception checks relying on sight automatically fail',
          'Can\'t see, making all visual stimuli impossible'
        ],
        removalConditions: ['Any effect that restores sight']
      },
      [CONDITIONS.CHARMED]: {
        description: 'A charmed creature can\'t attack the charmer or target the charmer with harmful abilities or magical effects.',
        socialInteractions: 'Advantage on social checks against charmer',
        restrictions: ['Can\'t attack charmer', 'Can\'t target charmer with harmful effects'],
        effects: [
          'Has disadvantage on attack rolls against charmer',
          'Charmer has advantage on social ability checks against charmed creature'
        ],
        removalConditions: ['Taking any damage', 'Charmer\'s hostile actions']
      },
      [CONDITIONS.DEAFENED]: {
        description: 'A deafened creature can\'t hear and automatically fails any ability check that requires hearing.',
        effects: [
          'Perception checks relying on hearing automatically fail',
          'Can\'t react to sound-based stimuli'
        ],
        removalConditions: ['Any effect that restores hearing']
      },
      [CONDITIONS.EXHAUSTION]: {
        description: 'Exhaustion is measured in six levels. Each level has cumulative effects.',
        levels: {
          1: 'Disadvantage on ability checks',
          2: 'Speed halved',
          3: 'Disadvantage on attack rolls and saving throws',
          4: 'Hit point maximum halved',
          5: 'Speed reduced to 0',
          6: 'Death'
        },
        effects: ['Cumulative penalties based on exhaustion level'],
        removalConditions: ['Long rest reduces level by 1']
      },
      [CONDITIONS.FRIGHTENED]: {
        description: 'A frightened creature has disadvantage on ability checks and attack rolls while the source of its fear is within line of sight.',
        effects: [
          'Disadvantage on ability checks while source is visible',
          'Disadvantage on attack rolls while source is visible',
          'Must use movement to move away from source'
        ],
        removalConditions: ['Source of fear is incapacitated', 'Source of fear is no longer visible']
      },
      [CONDITIONS.GRAPPLED]: {
        description: 'A grappled creature\'s speed becomes 0, and it can\'t benefit from any bonus to its speed.',
        effects: [
          'Speed becomes 0',
          'Can\'t benefit from any speed bonus',
          'Condition ends if grappler is incapacitated'
        ],
        removalConditions: ['Grappler incapacitated', 'Grappler\'s space no longer available', 'Escape action']
      },
      [CONDITIONS.INCAPACITATED]: {
        description: 'An incapacitated creature can\'t take actions or reactions.',
        effects: [
          'Can\'t take actions',
          'Can\'t take reactions'
        ],
        removalConditions: ['Varies by source of incapacitation']
      },
      [CONDITIONS.INVISIBLE]: {
        description: 'An invisible creature is impossible to see without the aid of magic or a special sense.',
        effects: [
          'Can\'t be seen without magic or special senses',
          'Attack rolls against creature have disadvantage',
          'Creature\'s attack rolls have advantage'
        ],
        removalConditions: ['Attacks', 'Casts spells', 'Forces saving throw', 'Moves within 5 feet of enemy']
      },
      [CONDITIONS.PARALYZED]: {
        description: 'A paralyzed creature is incapacitated and can\'t move or speak.',
        effects: [
          'Incapacitated (can\'t act)',
          'Can\'t move',
          'Can\'t speak',
          'Attack rolls against have advantage',
          'Automatic failure on Strength and Dexterity saving throws',
          'Any attack that hits is a critical hit'
        ],
        removalConditions: ['Varies by source of paralysis']
      },
      [CONDITIONS.PETRIFIED]: {
        description: 'A petrified creature is transformed, along with any nonmagical object it is wearing or carrying, into a solid inanimate substance.',
        effects: [
          'Weight increases by factor of ten',
          'Resistance to all damage',
          'Immune to poison and disease',
          'Incapacitated (can\'t act)',
          'Can\'t move or speak',
          'Attack rolls against have advantage',
          'Automatic failure on Strength and Dexterity saving throws'
        ],
        removalConditions: ['Greater restoration spell', 'Limited wish', 'Wish']
      },
      [CONDITIONS.POISONED]: {
        description: 'A poisoned creature has disadvantage on attack rolls and ability checks.',
        effects: [
          'Attack rolls have disadvantage',
          'Ability checks have disadvantage'
        ],
        removalConditions: ['Lesser/greater restoration', 'Neutralize poison', 'End of effect duration']
      },
      [CONDITIONS.PRONE]: {
        description: 'A prone creature is lying down.',
        effects: [
          'Attack rolls against prone creature have advantage if within 5 feet',
          'Attack rolls against prone creature have disadvantage if beyond 5 feet',
          'Creature has disadvantage on attack rolls'
        ],
        removalConditions: ['Creature spends half movement to stand up']
      },
      [CONDITIONS.RESTRAINED]: {
        description: 'A restrained creature\'s speed becomes 0, and it can\'t benefit from any bonus to its speed.',
        effects: [
          'Speed becomes 0',
          'Attack rolls have disadvantage',
          'Dexterity saving throws have disadvantage'
        ],
        removalConditions: ['Effect causing restraint ends']
      },
      [CONDITIONS.STUNNED]: {
        description: 'A stunned creature is incapacitated, can\'t move, and can speak only falteringly.',
        effects: [
          'Incapacitated (can\'t act)',
          'Can\'t move',
          'Automatic failure on Strength and Dexterity saving throws'
        ],
        removalConditions: ['End of effect duration']
      },
      [CONDITIONS.UNCONSCIOUS]: {
        description: 'An unconscious creature is incapacitated, can\'t move or speak, and is unaware of their surroundings.',
        effects: [
          'Incapacitated (can\'t act)',
          'Can\'t move or speak',
          'Aware of surroundings',
          'Attack rolls against have advantage',
          'Any attack that hits is a critical hit',
          'Makes death saving throws when not stable'
        ],
        removalConditions: ['Regains hit points', 'Stabilized']
      }
    };

    return effects[condition] || {
      description: 'Custom condition effect',
      effects: ['Custom condition effects apply']
    };
  }

  /**
   * Apply immediate effects when condition is applied
   * @param {Character} character - Target character
   * @param {string} condition - Applied condition
   * @returns {Array} Array of immediate effects
   */
  applyImmediateEffects(character, condition) {
    const effects = [];

    switch (condition) {
      case CONDITIONS.UNCONSCIOUS:
        // Drop anything being held
        effects.push('Drops held items');
        // Fall prone
        effects.push('Falls prone');
        if (!character.hasCondition(CONDITIONS.PRONE)) {
          character.addCondition(CONDITIONS.PRONE);
        }
        break;

      case CONDITIONS.PARALYZED:
      case CONDITIONS.STUNNED:
        // These conditions also make the creature incapacitated
        if (!character.hasCondition(CONDITIONS.INCAPACITATED)) {
          character.addCondition(CONDITIONS.INCAPACITATED);
          effects.push('Also gains Incapacitated condition');
        }
        break;

      case CONDITIONS.PETRIFIED:
        // Petrified creatures are also incapacitated
        if (!character.hasCondition(CONDITIONS.INCAPACITATED)) {
          character.addCondition(CONDITIONS.INCAPACITATED);
          effects.push('Also gains Incapacitated condition');
        }
        break;

      case CONDITIONS.PRONE:
        // Prone creatures can be targeted differently
        effects.push('Now vulnerable to melee attacks, harder to hit with ranged attacks');
        break;
    }

    return effects;
  }

  /**
   * Apply effects when condition is removed
   * @param {Character} character - Target character
   * @param {string} condition - Removed condition
   * @returns {Array} Array of removal effects
   */
  applyRemovalEffects(character, condition) {
    const effects = [];

    // Remove dependent conditions
    if (condition === CONDITIONS.UNCONSCIOUS) {
      character.removeCondition(CONDITIONS.PRONE);
      effects.push('No longer prone');
    }

    if ([CONDITIONS.PARALYZED, CONDITIONS.STUNNED, CONDITIONS.PETRIFIED].includes(condition)) {
      character.removeCondition(CONDITIONS.INCAPACITATED);
      effects.push('No longer incapacitated');
    }

    // Remove immunity effects
    if (condition === CONDITIONS.PETRIFIED) {
      effects.push('No longer immune to poison and disease');
      effects.push('No longer has damage resistance');
    }

    return effects;
  }

  /**
   * Handle condition conflicts (mutually exclusive conditions)
   * @param {Character} character - Target character
   * @param {string} newCondition - Condition being applied
   * @returns {object} Conflict resolution result
   */
  handleConditionConflicts(character, newCondition) {
    const conflicts = {
      [CONDITIONS.INVISIBLE]: [CONDITIONS.BLINDED, CONDITIONS.VISIBLE], // Custom visible condition
      [CONDITIONS.PETRIFIED]: [CONDITIONS.CHARMED, CONDITIONS.FRIGHTENED, CONDITIONS.POISONED],
      [CONDITIONS.UNCONSCIOUS]: [CONDITIONS.CHARMED, CONDITIONS.FRIGHTENED]
    };

    const conflictingConditions = conflicts[newCondition] || [];
    const removed = [];

    conflictingConditions.forEach(conflictCondition => {
      if (character.hasCondition(conflictCondition)) {
        character.removeCondition(conflictCondition);
        removed.push(conflictCondition);
      }
    });

    return {
      conflict: removed.length > 0,
      removed
    };
  }

  /**
   * Update exhaustion level
   * @param {Character} character - Target character
   * @param {number} change - Change in exhaustion level
   * @param {object} options - Update options
   * @returns {object} Update result
   */
  updateExhaustionLevel(character, change, options = {}) {
    const currentLevel = this.getExhaustionLevel(character);
    const newLevel = Math.max(0, Math.min(6, currentLevel + change));

    // Remove old exhaustion condition
    character.removeCondition(CONDITIONS.EXHAUSTION);

    if (newLevel === 0) {
      return {
        success: true,
        condition: CONDITIONS.EXHAUSTION,
        character: character.name,
        oldLevel: currentLevel,
        newLevel: 0,
        removed: true
      };
    }

    // Add new exhaustion level
    character.addCondition(CONDITIONS.EXHAUSTION);
    // Store exhaustion level as custom data (would need character data extension)
    character.exhaustionLevel = newLevel;

    // Check for death
    if (newLevel === 6) {
      character.hitPoints.current = 0;
      character.addCondition(CONDITIONS.UNCONSCIOUS);
      return {
        success: true,
        condition: CONDITIONS.EXHAUSTION,
        character: character.name,
        oldLevel: currentLevel,
        newLevel: 6,
        dead: true
      };
    }

    return {
      success: true,
      condition: CONDITIONS.EXHAUSTION,
      character: character.name,
      oldLevel: currentLevel,
      newLevel,
      effects: this.getConditionEffects(CONDITIONS.EXHAUSTION).levels[newLevel]
    };
  }

  /**
   * Get exhaustion level for character
   * @param {Character} character - Target character
   * @returns {number} Exhaustion level (0-6)
   */
  getExhaustionLevel(character) {
    return character.exhaustionLevel || 0;
  }

  /**
   * Check if character has immunity to condition
   * @param {Character} character - Target character
   * @param {string} condition - Condition to check
   * @returns {boolean} Whether character is immune
   */
  hasImmunity(character, condition) {
    // Check character's condition immunities
    return character.conditionImmunities?.includes(condition) || false;
  }

  /**
   * Set condition duration
   * @param {string} characterId - Character identifier
   * @param {string} condition - Condition name
   * @param {number} duration - Duration in rounds
   */
  setConditionDuration(characterId, condition, duration) {
    if (!this.conditionTimers.has(characterId)) {
      this.conditionTimers.set(characterId, new Map());
    }
    this.conditionTimers.get(characterId).set(condition, duration);
  }

  /**
   * Get conditions affecting a character
   * @param {string} characterId - Character identifier
   * @returns {Array} Array of active conditions
   */
  getCharacterConditions(characterId) {
    return Array.from(this.activeConditions.get(characterId) || []);
  }

  /**
   * Check if character is affected by specific condition
   * @param {string} characterId - Character identifier
   * @param {string} condition - Condition to check
   * @returns {boolean} Whether character has condition
   */
  hasCondition(characterId, condition) {
    return this.activeConditions.get(characterId)?.has(condition) || false;
  }

  /**
   * Get all conditions that affect ability checks
   * @param {string} characterId - Character identifier
   * @param {string} ability - Ability being checked
   * @returns {object} Condition modifiers
   */
  getAbilityCheckModifiers(characterId, ability) {
    const conditions = this.getCharacterConditions(characterId);
    const modifiers = {
      advantage: 0,
      disadvantage: 0,
      automaticFailure: false,
      effects: []
    };

    conditions.forEach(condition => {
      switch (condition) {
        case CONDITIONS.BLINDED:
          if (['perception', 'investigation'].includes(ability)) {
            modifiers.automaticFailure = true;
            modifiers.effects.push(`${condition}: Automatic failure on sight-based checks`);
          }
          break;

        case CONDITIONS.POISONED:
          modifiers.disadvantage += 1;
          modifiers.effects.push(`${condition}: Disadvantage on ability checks`);
          break;

        case CONDITIONS.FRIGHTENED:
          modifiers.disadvantage += 1;
          modifiers.effects.push(`${condition}: Disadvantage on ability checks`);
          break;

        case CONDITIONS.EXHAUSTION:
          const exhaustionLevel = 6; // Would get from character data
          if (exhaustionLevel >= 1) {
            modifiers.disadvantage += 1;
            modifiers.effects.push(`${condition} level ${exhaustionLevel}: Disadvantage on ability checks`);
          }
          break;
      }
    });

    return modifiers;
  }

  /**
   * Get conditions that affect attack rolls
   * @param {string} characterId - Character identifier
   * @param {boolean} isAttacker - Whether character is attacker or target
   * @returns {object} Attack roll modifiers
   */
  getAttackRollModifiers(characterId, isAttacker = true) {
    const conditions = this.getCharacterConditions(characterId);
    const modifiers = {
      advantage: 0,
      disadvantage: 0,
      effects: []
    };

    conditions.forEach(condition => {
      switch (condition) {
        case CONDITIONS.BLINDED:
        case CONDITIONS.POISONED:
        case CONDITIONS.RESTRAINED:
          if (isAttacker) {
            modifiers.disadvantage += 1;
            modifiers.effects.push(`${condition}: Disadvantage on attack rolls`);
          }
          break;

        case CONDITIONS.INVISIBLE:
          if (isAttacker) {
            modifiers.advantage += 1;
            modifiers.effects.push(`${condition}: Advantage on attack rolls`);
          } else {
            modifiers.disadvantage += 1;
            modifiers.effects.push(`${condition}: Disadvantage on attack rolls against`);
          }
          break;

        case CONDITIONS.PRONE:
          if (isAttacker) {
            modifiers.disadvantage += 1;
            modifiers.effects.push(`${condition}: Disadvantage on attack rolls`);
          }
          break;

        case CONDITIONS.FRIGHTENED:
          if (isAttacker) {
            modifiers.disadvantage += 1;
            modifiers.effects.push(`${condition}: Disadvantage on attack rolls`);
          }
          break;

        case CONDITIONS.EXHAUSTION:
          const exhaustionLevel = 6; // Would get from character data
          if (exhaustionLevel >= 3) {
            modifiers.disadvantage += 1;
            modifiers.effects.push(`${condition} level ${exhaustionLevel}: Disadvantage on attack rolls`);
          }
          break;
      }
    });

    return modifiers;
  }

  /**
   * Get conditions that affect saving throws
   * @param {string} characterId - Character identifier
   * @param {string} ability - Saving throw ability
   * @returns {object} Saving throw modifiers
   */
  getSavingThrowModifiers(characterId, ability) {
    const conditions = this.getCharacterConditions(characterId);
    const modifiers = {
      advantage: 0,
      disadvantage: 0,
      automaticFailure: false,
      effects: []
    };

    conditions.forEach(condition => {
      switch (condition) {
        case CONDITIONS.PARALYZED:
        case CONDITIONS.PETRIFIED:
        case CONDITIONS.STUNNED:
          if (ability === ABILITIES.STRENGTH || ability === ABILITIES.DEXTERITY) {
            modifiers.automaticFailure = true;
            modifiers.effects.push(`${condition}: Automatic failure on ${ability} saves`);
          }
          break;

        case CONDITIONS.RESTRAINED:
          if (ability === ABILITIES.DEXTERITY) {
            modifiers.disadvantage += 1;
            modifiers.effects.push(`${condition}: Disadvantage on Dexterity saves`);
          }
          break;

        case CONDITIONS.EXHAUSTION:
          const exhaustionLevel = 6; // Would get from character data
          if (exhaustionLevel >= 3) {
            modifiers.disadvantage += 1;
            modifiers.effects.push(`${condition} level ${exhaustionLevel}: Disadvantage on saving throws`);
          }
          break;
      }
    });

    return modifiers;
  }

  /**
   * Validate condition name
   * @param {string} condition - Condition to validate
   * @returns {boolean} Whether condition is valid
   */
  isValidCondition(condition) {
    return Object.values(CONDITIONS).includes(condition);
  }

  /**
   * Log condition event
   * @param {string} characterId - Character identifier
   * @param {object} event - Event data
   */
  logConditionEvent(characterId, event) {
    if (!this.conditionHistory.has(characterId)) {
      this.conditionHistory.set(characterId, []);
    }
    this.conditionHistory.get(characterId).push(event);
  }

  /**
   * Get condition history for character
   * @param {string} characterId - Character identifier
   * @returns {Array} Condition history
   */
  getConditionHistory(characterId) {
    return this.conditionHistory.get(characterId) || [];
  }

  /**
   * Clear all conditions for character
   * @param {string} characterId - Character identifier
   * @returns {Array} Array of cleared conditions
   */
  clearAllConditions(characterId) {
    const conditions = this.getCharacterConditions(characterId);

    this.activeConditions.delete(characterId);
    this.conditionTimers.delete(characterId);

    return conditions;
  }
}

export default ConditionSystem;