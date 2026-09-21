/**
 * Combat Actions System
 */

import { ABILITIES, CONDITIONS } from '../types/index.js';
import { DiceRoller } from '../core/DiceRoller.js';

export class CombatActions {
  /**
   * Perform a grapple attempt
   * @param {Character} attacker - Attacking character
   * @param {Character} defender - Defending character
   * @param {object} options - Grapple options
   * @returns {object} Grapple result
   */
  static performGrapple(attacker, defender, options = {}) {
    const { advantage = 0, bonus = 0 } = options;

    // Check size constraints
    if (this.canGrapple(attacker, defender)) {
      return {
        type: 'grapple',
        success: false,
        reason: 'Size difference makes grapple impossible',
        attacker: attacker.name,
        defender: defender.name
      };
    }

    // Attacker makes athletics (strength) check
    const attackerRoll = DiceRoller.rollD20(advantage);
    const attackerBonus = attacker.getAbilityModifier(ABILITIES.STRENGTH) +
                         (attacker.skills?.athletics?.proficient ? attacker.proficiencyBonus : 0) +
                         bonus;
    const attackerTotal = attackerRoll.total + attackerBonus;

    // Defender makes athletics or acrobatics check (their choice)
    const defenderAbility = defender.getAbilityModifier(ABILITIES.STRENGTH) >=
                           defender.getAbilityModifier(ABILITIES.DEXTERITY) ?
                           ABILITIES.STRENGTH : ABILITIES.DEXTERITY;

    const defenderRoll = DiceRoller.rollD20();
    const defenderBonus = defender.getAbilityModifier(defenderAbility) +
                         (defender.skills?.[defenderAbility === ABILITIES.STRENGTH ? 'athletics' : 'acrobatics']?.proficient ?
                          defender.proficiencyBonus : 0);
    const defenderTotal = defenderRoll.total + defenderBonus;

    const success = attackerTotal >= defenderTotal;

    const result = {
      type: 'grapple',
      attacker: attacker.name,
      defender: defender.name,
      attackerRoll: {
        roll: attackerRoll,
        bonus: attackerBonus,
        total: attackerTotal,
        ability: ABILITIES.STRENGTH
      },
      defenderRoll: {
        roll: defenderRoll,
        bonus: defenderBonus,
        total: defenderTotal,
        ability: defenderAbility
      },
      success,
      difference: Math.abs(attackerTotal - defenderTotal)
    };

    if (success) {
      defender.addCondition(CONDITIONS.GRAPPLED);
      result.effect = `${defender.name} is grappled`;
    }

    return result;
  }

  /**
   * Perform a shove attempt
   * @param {Character} attacker - Attacking character
   * @param {Character} defender - Defending character
   * @param {string} shoveType - 'prone' or 'push'
   * @param {object} options - Shove options
   * @returns {object} Shove result
   */
  static performShove(attacker, defender, shoveType = 'prone', options = {}) {
    const { advantage = 0, bonus = 0, pushDistance = 5 } = options;

    // Attacker makes athletics (strength) check
    const attackerRoll = DiceRoller.rollD20(advantage);
    const attackerBonus = attacker.getAbilityModifier(ABILITIES.STRENGTH) +
                         (attacker.skills?.athletics?.proficient ? attacker.proficiencyBonus : 0) +
                         bonus;
    const attackerTotal = attackerRoll.total + attackerBonus;

    // Defender makes athletics (strength) or acrobatics (dexterity) check
    const defenderAbility = ABILITIES.STRENGTH; // Can choose, but athletics is common
    const defenderRoll = DiceRoller.rollD20();
    const defenderBonus = defender.getAbilityModifier(defenderAbility) +
                         (defender.skills?.athletics?.proficient ? defender.proficiencyBonus : 0);
    const defenderTotal = defenderRoll.total + defenderBonus;

    const success = attackerTotal >= defenderTotal;

    const result = {
      type: 'shove',
      attacker: attacker.name,
      defender: defender.name,
      shoveType,
      attackerRoll: {
        roll: attackerRoll,
        bonus: attackerBonus,
        total: attackerTotal,
        ability: ABILITIES.STRENGTH
      },
      defenderRoll: {
        roll: defenderRoll,
        bonus: defenderBonus,
        total: defenderTotal,
        ability: defenderAbility
      },
      success
    };

    if (success) {
      if (shoveType === 'prone') {
        defender.addCondition(CONDITIONS.PRONE);
        result.effect = `${defender.name} is knocked prone`;
      } else if (shoveType === 'push') {
        // This would need position data from combat system
        result.effect = `${defender.name} is pushed ${pushDistance} feet`;
        result.pushDistance = pushDistance;
      }
    }

    return result;
  }

  /**
   * Perform a disarm attempt
   * @param {Character} attacker - Attacking character
   * @param {Character} defender - Defending character
   * @param {object} options - Disarm options
   * @returns {object} Disarm result
   */
  static performDisarm(attacker, defender, options = {}) {
    const { advantage = 0, bonus = 0 } = options;

    // Check if defender is holding a weapon
    if (!defender.equippedWeapon) {
      return {
        type: 'disarm',
        success: false,
        reason: 'Target is not holding a weapon',
        attacker: attacker.name,
        defender: defender.name
      };
    }

    // Attacker makes attack roll vs defender's athletics/acrobatics
    const attackRoll = DiceRoller.rollD20(advantage);
    const attackBonus = attacker.getAbilityModifier(ABILITIES.DEXTERITY) +
                      attacker.proficiencyBonus + bonus;
    const attackTotal = attackRoll.total + attackBonus;

    const defenderAbility = ABILITIES.DEXTERITY;
    const defenseRoll = DiceRoller.rollD20();
    const defenseBonus = defender.getAbilityModifier(defenderAbility) +
                       (defender.skills?.acrobatics?.proficient ? defender.proficiencyBonus : 0);
    const defenseTotal = defenseRoll.total + defenseBonus;

    const success = attackTotal >= defenseTotal;

    const result = {
      type: 'disarm',
      attacker: attacker.name,
      defender: defender.name,
      attackRoll: {
        roll: attackRoll,
        bonus: attackBonus,
        total: attackTotal
      },
      defenseRoll: {
        roll: defenseRoll,
        bonus: defenseBonus,
        total: defenseTotal
      },
      success,
      weapon: defender.equippedWeapon
    };

    if (success) {
      // Weapon drops on the ground (would need position data)
      result.effect = `${defender.name} is disarmed of ${defender.equippedWeapon.name}`;
      // defender.equippedWeapon = null; // Would be handled by inventory system
    }

    return result;
  }

  /**
   * Perform a trip attempt
   * @param {Character} attacker - Attacking character
   * @param {Character} defender - Defending character
   * @param {object} options - Trip options
   * @returns {object} Trip result
   */
  static performTrip(attacker, defender, options = {}) {
    const { advantage = 0, bonus = 0 } = options;

    // Similar to shove, but specifically to make prone
    const result = this.performShove(attacker, defender, 'prone', options);
    result.type = 'trip';
    return result;
  }

  /**
   * Perform an opportunity attack
   * @param {Character} attacker - Attacking character
   * @param {Character} defender - Defending character
   * @param {object} options - Attack options
   * @returns {object} Opportunity attack result
   */
  static performOpportunityAttack(attacker, defender, options = {}) {
    const result = {
      type: 'opportunity_attack',
      attacker: attacker.name,
      defender: defender.name,
      reaction: true
    };

    // Check if attacker has reaction available
    if (attacker.reactionsUsed >= attacker.reactionsMax) {
      result.success = false;
      result.reason = 'No reactions available';
      return result;
    }

    // Perform the attack (simplified - using standard attack rules)
    const attackRoll = DiceRoller.rollD20(options.advantage || 0);
    const attackBonus = attacker.getAbilityModifier(ABILITIES.DEXTERITY) +
                      attacker.proficiencyBonus + (options.bonus || 0);
    const attackTotal = attackRoll.total + attackBonus;

    result.attackRoll = {
      roll: attackRoll,
      bonus: attackBonus,
      total: attackTotal,
      critical: attackRoll.isCritical
    };

    // Check if hit
    result.hit = attackTotal >= defender.armorClass;
    result.targetAC = defender.armorClass;

    if (result.hit) {
      // Roll damage
      const damageExpression = options.damageExpression || '1d8';
      const damageRoll = DiceRoller.rollExpression(damageExpression);
      const totalDamage = damageRoll.total + (options.damageBonus || 0);

      result.damage = {
        expression: damageExpression,
        roll: damageRoll,
        bonus: options.damageBonus || 0,
        total: totalDamage,
        type: options.damageType || 'slashing'
      };

      // Apply damage
      const originalHP = defender.hitPoints.current;
      defender.takeDamage(totalDamage);
      result.damageApplication = {
        originalHP,
        newHP: defender.hitPoints.current,
        damageDealt: originalHP - defender.hitPoints.current
      };
    }

    // Use reaction
    attacker.reactionsUsed += 1;
    result.reactionUsed = true;

    return result;
  }

  /**
   * Perform a dodge action
   * @param {Character} character - Character dodging
   * @returns {object} Dodge result
   */
  static performDodge(character) {
    const result = {
      type: 'dodge',
      character: character.name,
      effects: []
    };

    // Dodge action effects would be applied in combat system
    // Main effect: disadvantage on attack rolls against character until next turn
    result.effects.push('Disadvantage on attack rolls against you until your next turn');

    return result;
  }

  /**
   * Perform a dash action
   * @param {Character} character - Character dashing
   * @returns {object} Dash result
   */
  static performDash(character) {
    const result = {
      type: 'dash',
      character: character.name,
      additionalMovement: character.speed
    };

    // This would increase available movement in combat system
    return result;
  }

  /**
   * Perform a help action
   * @param {Character} helper - Character helping
   * @param {Character} recipient - Character receiving help
   * @param {string} actionType - Type of action being helped with
   * @returns {object} Help result
   */
  static performHelp(helper, recipient, actionType = 'ability_check') {
    const result = {
      type: 'help',
      helper: helper.name,
      recipient: recipient.name,
      actionType,
      effect: 'Advantage on next ability check or attack roll'
    };

    // This would set a flag on the recipient for their next action
    return result;
  }

  /**
   * Perform a ready action
   * @param {Character} character - Character readying action
   * @param {string} trigger - Trigger condition
   * @param {object} action - Action to perform
   * @returns {object} Ready result
   */
  static performReady(character, trigger, action) {
    const result = {
      type: 'ready',
      character: character.name,
      trigger,
      action,
      effect: 'Action will be performed when trigger occurs'
    };

    // This would set up the ready action in combat system
    return result;
  }

  /**
   * Perform a search action
   * @param {Character} character - Character searching
   * @param {object} options - Search options
   * @returns {object} Search result
   */
  static performSearch(character, options = {}) {
    const { area = 'immediate', lookingFor = 'hidden' } = options;

    // Passive perception check
    const passivePerception = 10 + character.getAbilityModifier(ABILITIES.WISDOM) +
                             (character.skills?.perception?.proficient ? character.proficiencyBonus : 0);

    const result = {
      type: 'search',
      character: character.name,
      area,
      lookingFor,
      passivePerception,
      activeSearch: true
    };

    // Could also allow active search with wisdom (perception) check
    if (options.active) {
      const searchRoll = DiceRoller.rollD20();
      const searchBonus = character.getAbilityModifier(ABILITIES.WISDOM) +
                        (character.skills?.perception?.proficient ? character.proficiencyBonus : 0);
      result.activeCheck = {
        roll: searchRoll,
        bonus: searchBonus,
        total: searchRoll.total + searchBonus
      };
    }

    return result;
  }

  /**
   * Check if attacker can grapple defender based on size
   * @param {Character} attacker - Attacking character
   * @param {Character} defender - Defending character
   * @returns {boolean} Whether grapple is possible
   */
  static canGrapple(attacker, defender) {
    // Simplified size check - would need actual size attributes
    const attackerSize = attacker.size || 'medium';
    const defenderSize = defender.size || 'medium';

    const sizeOrder = ['tiny', 'small', 'medium', 'large', 'huge', 'gargantuan'];
    const attackerIndex = sizeOrder.indexOf(attackerSize);
    const defenderIndex = sizeOrder.indexOf(defenderSize);

    // Can't grapple if defender is more than one size larger
    return (defenderIndex - attackerIndex) <= 1;
  }

  /**
   * Perform a two-weapon attack
   * @param {Character} attacker - Attacking character
   * @param {Character} defender - Defending character
   * @param {object} options - Attack options
   * @returns {object} Two-weapon attack result
   */
  static performTwoWeaponAttack(attacker, defender, options = {}) {
    const result = {
      type: 'two_weapon_attack',
      attacker: attacker.name,
      defender: defender.name,
      attacks: [],
      bonusAction: true
    };

    // Main hand attack
    const mainHandAttack = this.performSingleAttack(attacker, defender, {
      ...options,
      weapon: options.mainHandWeapon,
      attackType: 'melee'
    });
    result.attacks.push({ hand: 'main', ...mainHandAttack });

    // Off-hand attack (bonus action, no ability modifier to damage)
    if (mainHandAttack.hit || mainHandAttack.critical) {
      const offHandAttack = this.performSingleAttack(attacker, defender, {
        ...options,
        weapon: options.offHandWeapon,
        attackType: 'melee',
        bonusAction: true,
        noAbilityModToDamage: true
      });
      result.attacks.push({ hand: 'off', ...offHandAttack });
    }

    return result;
  }

  /**
   * Perform a single attack (helper function)
   * @param {Character} attacker - Attacking character
   * @param {Character} defender - Defending character
   * @param {object} options - Attack options
   * @returns {object} Attack result
   */
  static performSingleAttack(attacker, defender, options = {}) {
    const {
      weapon = null,
      attackType = 'melee',
      advantage = 0,
      bonus = 0,
      bonusAction = false,
      noAbilityModToDamage = false
    } = options;

    const attackRoll = DiceRoller.rollD20(advantage);
    const ability = attackType === 'ranged' ? ABILITIES.DEXTERITY : ABILITIES.STRENGTH;
    const attackBonus = attacker.getAbilityModifier(ability) +
                      attacker.proficiencyBonus + bonus;
    const attackTotal = attackRoll.total + attackBonus;

    const result = {
      roll: attackRoll,
      bonus: attackBonus,
      total: attackTotal,
      hit: attackTotal >= defender.armorClass,
      critical: attackRoll.isCritical,
      targetAC: defender.armorClass
    };

    if (result.hit) {
      const damageExpression = weapon?.damage || '1d6';
      const damageRoll = DiceRoller.rollExpression(damageExpression);
      let damageBonus = weapon?.damageBonus || bonus;

      if (!noAbilityModToDamage) {
        damageBonus += attacker.getAbilityModifier(ability);
      }

      if (result.critical) {
        // Critical hit - double damage dice
        const critRoll = DiceRoller.rollExpression(damageExpression);
        result.damage = {
          expression: damageExpression,
          rolls: [damageRoll, critRoll],
          bonus: damageBonus,
          total: damageRoll.total + critRoll.total + damageBonus,
          critical: true
        };
      } else {
        result.damage = {
          expression: damageExpression,
          roll: damageRoll,
          bonus: damageBonus,
          total: damageRoll.total + damageBonus,
          critical: false
        };
      }
    }

    return result;
  }
}

export default CombatActions;