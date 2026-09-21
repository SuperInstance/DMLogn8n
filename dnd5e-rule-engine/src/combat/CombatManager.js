/**
 * Combat Management System
 */

import { ABILITIES, CONDITIONS, Character, Combat } from '../types/index.js';
import { DiceRoller } from '../core/DiceRoller.js';
import { RuleEngine } from '../core/RuleEngine.js';

export class CombatManager {
  constructor(ruleEngine) {
    this.ruleEngine = ruleEngine;
    this.combatEncounters = new Map();
    this.combatLog = new Map();
  }

  /**
   * Create a new combat encounter
   * @param {string} encounterId - Unique identifier
   * @param {object} options - Combat options
   * @returns {Combat} New combat encounter
   */
  createCombat(encounterId, options = {}) {
    const combat = new Combat(encounterId);
    combat.environment = options.environment || {};
    combat.rules = options.rules || {};
    this.combatEncounters.set(encounterId, combat);
    this.combatLog.set(encounterId, []);
    return combat;
  }

  /**
   * Add participant to combat
   * @param {string} encounterId - Combat encounter ID
   * @param {Character} character - Character to add
   * @param {number} initiative - Initiative score (optional)
   * @param {object} options - Additional options
   */
  addParticipant(encounterId, character, initiative = null, options = {}) {
    const combat = this.combatEncounters.get(encounterId);
    if (!combat) {
      throw new Error(`Combat encounter ${encounterId} not found`);
    }

    // Check if character is already in combat
    const existingParticipant = combat.participants.find(p => p.id === character.id);
    if (existingParticipant) {
      throw new Error(`${character.name} is already in combat ${encounterId}`);
    }

    // Roll initiative if not provided
    const finalInitiative = initiative !== null ? initiative : this.rollInitiative(character, options);

    const participant = {
      character,
      initiative: finalInitiative,
      id: character.id,
      team: options.team || 'neutral',
      position: options.position || { x: 0, y: 0 },
      ready: options.ready || false,
      delay: options.delay || false,
      reactions: {
        used: 0,
        max: 1
      },
      bonusActions: {
        used: 0,
        max: 1
      },
      movement: {
        used: 0,
        max: character.speed
      }
    };

    combat.participants.push(participant);
    combat.updateTurnOrder();

    this.logCombatAction(encounterId, {
      type: 'participant_added',
      character: character.name,
      initiative: finalInitiative,
      timestamp: new Date()
    });

    return participant;
  }

  /**
   * Roll initiative for a character
   * @param {Character} character - Character to roll for
   * @param {object} options - Initiative options
   * @returns {number} Initiative score
   */
  rollInitiative(character, options = {}) {
    const { advantage = 0, bonus = 0 } = options;
    const dexterityMod = character.getAbilityModifier(ABILITIES.DEXTERITY);
    const roll = DiceRoller.rollD20(advantage);
    return roll.total + dexterityMod + bonus;
  }

  /**
   * Start combat encounter
   * @param {string} encounterId - Combat encounter ID
   * @returns {object} Combat start information
   */
  startCombat(encounterId) {
    const combat = this.combatEncounters.get(encounterId);
    if (!combat) {
      throw new Error(`Combat encounter ${encounterId} not found`);
    }

    if (combat.participants.length === 0) {
      throw new Error('Cannot start combat with no participants');
    }

    combat.start();
    combat.currentTurn = 0;
    combat.round = 1;

    // Apply surprise round if applicable
    const surpriseResult = this.handleSurpriseRound(combat);

    this.logCombatAction(encounterId, {
      type: 'combat_started',
      round: combat.round,
      participants: combat.participants.map(p => ({
        name: p.character.name,
        initiative: p.initiative,
        surprised: p.surprised
      })),
      timestamp: new Date()
    });

    return {
      combatId: encounterId,
      round: combat.round,
      turnOrder: combat.turnOrder,
      currentTurn: this.getCurrentParticipant(encounterId),
      surprise: surpriseResult
    };
  }

  /**
   * Handle surprise round mechanics
   * @param {Combat} combat - Combat encounter
   * @returns {object} Surprise result
   */
  handleSurpriseRound(combat) {
    // Determine surprised participants (simplified - in real game, this would involve perception checks)
    const surprisedParticipants = combat.participants.filter(p => p.surprised);

    if (surprisedParticipants.length === 0) {
      return { hasSurprise: false };
    }

    // Surprise round: only non-surprised participants can act
    surprisedParticipants.forEach(p => {
      p.hasActed = true; // Skip their first turn
    });

    return {
      hasSurprise: true,
      surprised: surprisedParticipants.map(p => p.character.name)
    };
  }

  /**
   * Get current participant in combat
   * @param {string} encounterId - Combat encounter ID
   * @returns {object|null} Current participant
   */
  getCurrentParticipant(encounterId) {
    const combat = this.combatEncounters.get(encounterId);
    if (!combat || !combat.active || combat.turnOrder.length === 0) {
      return null;
    }

    const currentId = combat.turnOrder[combat.currentTurn];
    const participant = combat.participants.find(p => p.id === currentId);

    if (!participant) {
      return null;
    }

    return {
      ...participant,
      round: combat.round,
      turnIndex: combat.currentTurn
    };
  }

  /**
   * Move to next turn in combat
   * @param {string} encounterId - Combat encounter ID
   * @returns {object} Next turn information
   */
  nextTurn(encounterId) {
    const combat = this.combatEncounters.get(encounterId);
    if (!combat || !combat.active) {
      throw new Error(`Combat encounter ${encounterId} not active`);
    }

    // Reset current participant's turn resources
    const currentParticipant = this.getCurrentParticipant(encounterId);
    if (currentParticipant) {
      this.resetTurnResources(currentParticipant);
    }

    // Move to next turn
    combat.currentTurn = (combat.currentTurn + 1) % combat.turnOrder.length;

    // Check if new round started
    let newRound = false;
    if (combat.currentTurn === 0) {
      combat.round++;
      newRound = true;
      this.handleNewRound(combat);
    }

    const nextParticipant = this.getCurrentParticipant(encounterId);

    this.logCombatAction(encounterId, {
      type: 'turn_change',
      from: currentParticipant?.character?.name,
      to: nextParticipant?.character?.name,
      round: combat.round,
      timestamp: new Date()
    });

    return {
      round: combat.round,
      newRound,
      currentTurn: nextParticipant,
      combatState: this.getCombatState(encounterId)
    };
  }

  /**
   * Handle start of new round
   * @param {Combat} combat - Combat encounter
   */
  handleNewRound(combat) {
    // Reset certain resources for all participants
    combat.participants.forEach(participant => {
      participant.reactions.used = 0;
      participant.bonusActions.used = 0;
      participant.movement.used = 0;
      participant.ready = false;
      participant.delay = false;

      // Handle ongoing effects and conditions
      this.handleOngoingEffects(participant);
    });
  }

  /**
   * Reset turn resources for a participant
   * @param {object} participant - Combat participant
   */
  resetTurnResources(participant) {
    participant.movement.used = 0;
    participant.bonusActions.used = 0;
    participant.hasActed = false;
  }

  /**
   * Handle ongoing effects on a participant
   * @param {object} participant - Combat participant
   */
  handleOngoingEffects(participant) {
    const character = participant.character;

    // Handle condition effects
    character.conditions.forEach(condition => {
      this.handleConditionEffect(character, condition);
    });

    // Handle regeneration effects
    if (character.features?.some(f => f.type === 'regeneration')) {
      const regenAmount = character.features
        .filter(f => f.type === 'regeneration')
        .reduce((sum, f) => sum + (f.amount || 0), 0);
      character.heal(regenAmount);
    }
  }

  /**
   * Handle specific condition effects
   * @param {Character} character - Character with condition
   * @param {string} condition - Condition name
   */
  handleConditionEffect(character, condition) {
    switch (condition) {
      case CONDITIONS.POISONED:
        // Poison damage at start of turn
        break;
      case CONDITIONS.BURNING:
        // Fire damage at start of turn
        break;
      case CONDITIONS.REGEN:
        // Regeneration at start of turn
        break;
      // Add other condition effects as needed
    }
  }

  /**
   * Perform an attack in combat
   * @param {string} encounterId - Combat encounter ID
   * @param {string} attackerId - Attacker character ID
   * @param {string} defenderId - Defender character ID
   * @param {object} options - Attack options
   * @returns {object} Attack result
   */
  performAttack(encounterId, attackerId, defenderId, options = {}) {
    const combat = this.combatEncounters.get(encounterId);
    if (!combat) {
      throw new Error(`Combat encounter ${encounterId} not found`);
    }

    const attacker = combat.participants.find(p => p.id === attackerId);
    const defender = combat.participants.find(p => p.id === defenderId);

    if (!attacker || !defender) {
      throw new Error('Attacker or defender not found in combat');
    }

    // Check if it's the attacker's turn
    const currentTurn = this.getCurrentParticipant(encounterId);
    if (currentTurn?.id !== attackerId) {
      throw new Error('It is not the attacker\'s turn');
    }

    // Check if attacker can act
    if (attacker.character.hasCondition(CONDITIONS.INCAPACITATED) ||
        attacker.character.hasCondition(CONDITIONS.STUNNED) ||
        attacker.character.hasCondition(CONDITIONS.UNCONSCIOUS)) {
      throw new Error('Attacker cannot act due to conditions');
    }

    // Perform the attack
    const attackResult = this.ruleEngine.attackRoll(
      attacker.character,
      defender.character,
      options.attackType || 'melee',
      options.advantage || 0,
      options.bonus || 0
    );

    // Apply damage if hit
    let damageResult = null;
    if (attackResult.hit) {
      damageResult = this.ruleEngine.rollDamage(
        attacker.character,
        options.damageExpression || '1d8',
        options.damageType || 'slashing',
        attackResult.critical,
        options.damageBonus || 0
      );

      const damageApplication = this.ruleEngine.applyDamage(
        defender.character,
        damageResult.total,
        damageResult.damageType,
        attackResult.critical
      );

      damageResult.application = damageApplication;
    }

    // Check for opportunity attacks
    this.checkOpportunityAttacks(encounterId, attacker, defender, options);

    const result = {
      type: 'combat_attack',
      attacker: attacker.character.name,
      defender: defender.character.name,
      attack: attackResult,
      damage: damageResult,
      timestamp: new Date()
    };

    this.logCombatAction(encounterId, result);
    return result;
  }

  /**
   * Check for opportunity attacks
   * @param {string} encounterId - Combat encounter ID
   * @param {object} attacker - Moving character
   * @param {object} defender - Target character
   * @param {object} options - Movement options
   */
  checkOpportunityAttacks(encounterId, attacker, defender, options) {
    const combat = this.combatEncounters.get(encounterId);
    const threateningEnemies = combat.participants.filter(p => {
      if (p.id === attackerId) return false;
      if (p.team === attacker.team) return false;
      if (p.reactions.used >= p.reactions.max) return false;

      // Check if within melee range (simplified)
      const distance = this.calculateDistance(p.position, attacker.position);
      return distance <= 5; // 5 feet melee range
    });

    threateningEnemies.forEach(enemy => {
      // Opportunity attack would be triggered here
      // Implementation would depend on specific combat rules
    });
  }

  /**
   * Calculate distance between two positions
   * @param {object} pos1 - First position {x, y}
   * @param {object} pos2 - Second position {x, y}
   * @returns {number} Distance in feet
   */
  calculateDistance(pos1, pos2) {
    const dx = pos2.x - pos1.x;
    const dy = pos2.y - pos1.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  /**
   * Handle movement in combat
   * @param {string} encounterId - Combat encounter ID
   * @param {string} characterId - Moving character ID
   * @param {object} newPosition - New position {x, y}
   * @param {object} options - Movement options
   * @returns {object} Movement result
   */
  performMovement(encounterId, characterId, newPosition, options = {}) {
    const combat = this.combatEncounters.get(encounterId);
    const participant = combat.participants.find(p => p.id === characterId);

    if (!participant) {
      throw new Error(`Character ${characterId} not found in combat`);
    }

    const currentPosition = participant.position;
    const distance = this.calculateDistance(currentPosition, newPosition);
    const availableMovement = participant.movement.max - participant.movement.used;

    // Check for difficult terrain
    let movementCost = distance;
    if (options.difficultTerrain) {
      movementCost *= 2;
    }

    if (movementCost > availableMovement) {
      throw new Error(`Not enough movement: need ${movementCost}, have ${availableMovement}`);
    }

    // Update position and movement used
    participant.position = newPosition;
    participant.movement.used += movementCost;

    // Check for opportunity attacks
    this.checkOpportunityAttacks(encounterId, participant, null, {
      movement: true,
      fromPosition: currentPosition,
      toPosition: newPosition
    });

    const result = {
      type: 'combat_movement',
      character: participant.character.name,
      from: currentPosition,
      to: newPosition,
      distance: movementCost,
      movementRemaining: availableMovement - movementCost,
      timestamp: new Date()
    };

    this.logCombatAction(encounterId, result);
    return result;
  }

  /**
   * End combat encounter
   * @param {string} encounterId - Combat encounter ID
   * @param {string} reason - Reason for ending combat
   * @returns {object} Combat end summary
   */
  endCombat(encounterId, reason = 'combat_complete') {
    const combat = this.combatEncounters.get(encounterId);
    if (!combat) {
      throw new Error(`Combat encounter ${encounterId} not found`);
    }

    combat.end();

    const summary = {
      combatId: encounterId,
      reason,
      rounds: combat.round,
      participants: combat.participants.map(p => ({
        name: p.character.name,
        team: p.team,
        finalHP: p.character.hitPoints.current,
        conditions: p.character.conditions
      })),
      combatLog: this.combatLog.get(encounterId) || [],
      endedAt: new Date()
    };

    this.combatEncounters.delete(encounterId);
    this.combatLog.delete(encounterId);

    return summary;
  }

  /**
   * Get current combat state
   * @param {string} encounterId - Combat encounter ID
   * @returns {object} Combat state
   */
  getCombatState(encounterId) {
    const combat = this.combatEncounters.get(encounterId);
    if (!combat) {
      return null;
    }

    return {
      combatId: encounterId,
      active: combat.active,
      round: combat.round,
      turnOrder: combat.turnOrder,
      currentTurn: combat.currentTurn,
      currentParticipant: this.getCurrentParticipant(encounterId),
      participants: combat.participants.map(p => ({
        id: p.id,
        name: p.character.name,
        team: p.team,
        initiative: p.initiative,
        hp: p.character.hitPoints.current,
        maxHP: p.character.hitPoints.maximum,
        conditions: p.character.conditions,
        position: p.position,
        movementRemaining: p.movement.max - p.movement.used,
        reactionsRemaining: p.reactions.max - p.reactions.used
      })),
      environment: combat.environment
    };
  }

  /**
   * Log combat action
   * @param {string} encounterId - Combat encounter ID
   * @param {object} action - Action to log
   */
  logCombatAction(encounterId, action) {
    const log = this.combatLog.get(encounterId) || [];
    log.push(action);
    this.combatLog.set(encounterId, log);
  }

  /**
   * Get combat log
   * @param {string} encounterId - Combat encounter ID
   * @returns {Array} Combat log
   */
  getCombatLog(encounterId) {
    return this.combatLog.get(encounterId) || [];
  }
}

export default CombatManager;