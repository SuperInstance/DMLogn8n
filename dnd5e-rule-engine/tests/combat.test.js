/**
 * Combat System Tests
 */

import { jest } from '@jest/globals';
import CombatManager from '../src/combat/CombatManager.js';
import { Character, ABILITIES } from '../src/types/index.js';

describe('CombatManager', () => {
  let combatManager;
  let testCombatId;
  let fighter;
  let wizard;
  let goblin;

  beforeEach(() => {
    combatManager = new CombatManager();
    testCombatId = 'test-combat-1';

    fighter = new Character({
      id: 'fighter-1',
      name: 'Aragorn',
      class: 'fighter',
      level: 5,
      abilities: {
        strength: 18,
        dexterity: 14,
        constitution: 16
      },
      armorClass: 18,
      hitPoints: { current: 58, maximum: 58 },
      speed: 30
    });

    wizard = new Character({
      id: 'wizard-1',
      name: 'Gandalf',
      class: 'wizard',
      level: 5,
      abilities: {
        dexterity: 14,
        constitution: 14,
        intelligence: 18
      },
      armorClass: 12,
      hitPoints: { current: 32, maximum: 32 },
      speed: 30
    });

    goblin = new Character({
      id: 'goblin-1',
      name: 'Goblin Scout',
      class: 'commoner',
      level: 1,
      abilities: {
        dexterity: 15,
        constitution: 12
      },
      armorClass: 15,
      hitPoints: { current: 7, maximum: 7 },
      speed: 30
    });
  });

  describe('createCombat', () => {
    test('should create new combat encounter', () => {
      const combat = combatManager.createCombat(testCombatId, {
        environment: { terrain: 'forest', lighting: 'dim' },
        rules: { criticalHits: 'double' }
      });

      expect(combat.id).toBe(testCombatId);
      expect(combat.environment.terrain).toBe('forest');
      expect(combat.rules.criticalHits).toBe('double');
      expect(combat.participants).toHaveLength(0);
      expect(combat.active).toBe(false);
    });

    test('should store combat encounter', () => {
      const combat = combatManager.createCombat(testCombatId);
      const retrieved = combatManager.getCombat(testCombatId);

      expect(retrieved).toBe(combat);
    });
  });

  describe('addParticipant', () => {
    beforeEach(() => {
      combatManager.createCombat(testCombatId);
    });

    test('should add participant with initiative', () => {
      const participant = combatManager.addParticipant(testCombatId, fighter, 18, {
        team: 'heroes'
      });

      expect(participant.character).toBe(fighter);
      expect(participant.initiative).toBe(18);
      expect(participant.team).toBe('heroes');
      expect(participant.position).toEqual({ x: 0, y: 0 });
    });

    test('should roll initiative if not provided', () => {
      const participant = combatManager.addParticipant(testCombatId, wizard);

      expect(participant.initiative).toBeGreaterThan(0);
      expect(participant.initiative).toBeLessThanOrEqual(25); // 20 + max bonus
    });

    test('should update turn order when adding participants', () => {
      combatManager.addParticipant(testCombatId, fighter, 15);
      combatManager.addParticipant(testCombatId, wizard, 18);
      combatManager.addParticipant(testCombatId, goblin, 12);

      const combat = combatManager.getCombat(testCombatId);
      expect(combat.turnOrder).toEqual(['wizard-1', 'fighter-1', 'goblin-1']);
    });

    test('should throw error for non-existent combat', () => {
      expect(() => {
        combatManager.addParticipant('invalid-combat', fighter);
      }).toThrow('Combat encounter invalid-combat not found');
    });

    test('should throw error for duplicate participant', () => {
      combatManager.addParticipant(testCombatId, fighter);

      expect(() => {
        combatManager.addParticipant(testCombatId, fighter);
      }).toThrow('Aragorn is already in combat test-combat-1');
    });
  });

  describe('startCombat', () => {
    beforeEach(() => {
      combatManager.createCombat(testCombatId);
      combatManager.addParticipant(testCombatId, fighter, 18);
      combatManager.addParticipant(testCombatId, wizard, 12);
      combatManager.addParticipant(testCombatId, goblin, 15);
    });

    test('should start combat successfully', () => {
      const result = combatManager.startCombat(testCombatId);

      expect(result.combatId).toBe(testCombatId);
      expect(result.round).toBe(1);
      expect(result.currentTurn.character.name).toBe('Aragorn'); // Highest initiative
      expect(result.turnOrder).toEqual(['fighter-1', 'goblin-1', 'wizard-1']);
    });

    test('should handle surprise rounds', () => {
      // Mark goblin as surprised
      const combat = combatManager.getCombat(testCombatId);
      combat.participants.find(p => p.id === 'goblin-1').surprised = true;

      const result = combatManager.startCombat(testCombatId);

      expect(result.surprise.hasSurprise).toBe(true);
      expect(result.surprise.surprised).toContain('Goblin Scout');
    });

    test('should throw error for empty combat', () => {
      const emptyCombatId = 'empty-combat';
      combatManager.createCombat(emptyCombatId);

      expect(() => {
        combatManager.startCombat(emptyCombatId);
      }).toThrow('Cannot start combat with no participants');
    });
  });

  describe('getCurrentParticipant', () => {
    beforeEach(() => {
      combatManager.createCombat(testCombatId);
      combatManager.addParticipant(testCombatId, fighter, 18);
      combatManager.addParticipant(testCombatId, wizard, 12);
      combatManager.startCombat(testCombatId);
    });

    test('should return current participant', () => {
      const current = combatManager.getCurrentParticipant(testCombatId);

      expect(current.character.name).toBe('Aragorn');
      expect(current.round).toBe(1);
      expect(current.turnIndex).toBe(0);
    });

    test('should return null for non-existent combat', () => {
      const current = combatManager.getCurrentParticipant('invalid-combat');
      expect(current).toBeNull();
    });

    test('should return null for inactive combat', () => {
      combatManager.endCombat(testCombatId);
      const current = combatManager.getCurrentParticipant(testCombatId);
      expect(current).toBeNull();
    });
  });

  describe('nextTurn', () => {
    beforeEach(() => {
      combatManager.createCombat(testCombatId);
      combatManager.addParticipant(testCombatId, fighter, 18);
      combatManager.addParticipant(testCombatId, wizard, 12);
      combatManager.addParticipant(testCombatId, goblin, 15);
      combatManager.startCombat(testCombatId);
    });

    test('should advance to next turn', () => {
      const result = combatManager.nextTurn(testCombatId);

      expect(result.round).toBe(1); // Still same round
      expect(result.newRound).toBe(false);
      expect(result.currentTurn.character.name).toBe('Goblin Scout');
    });

    test('should handle round progression', () => {
      // Go through two turns to reach next round
      combatManager.nextTurn(testCombatId);
      const result = combatManager.nextTurn(testCombatId);

      expect(result.round).toBe(2);
      expect(result.newRound).toBe(true);
      expect(result.currentTurn.character.name).toBe('Aragorn'); // Back to start
    });

    test('should reset turn resources', () => {
      const combat = combatManager.getCombat(testCombatId);
      const currentParticipant = combat.participants.find(p => p.id === 'fighter-1');

      // Use some resources
      currentParticipant.movement.used = 15;
      currentParticipant.bonusActions.used = 1;

      combatManager.nextTurn(testCombatId);

      expect(currentParticipant.movement.used).toBe(0);
      expect(currentParticipant.bonusActions.used).toBe(0);
    });
  });

  describe('performAttack', () => {
    beforeEach(() => {
      combatManager.createCombat(testCombatId);
      combatManager.addParticipant(testCombatId, fighter, 18, { team: 'heroes' });
      combatManager.addParticipant(testCombatId, goblin, 15, { team: 'monsters' });
      combatManager.startCombat(testCombatId);
    });

    test('should perform successful attack', () => {
      // Mock high roll for guaranteed hit
      jest.spyOn(Math, 'random').mockReturnValue(0.95); // Roll 20

      const result = combatManager.performAttack(testCombatId, 'fighter-1', 'goblin-1', {
        attackType: 'melee',
        damageExpression: '1d8+4',
        damageType: 'slashing'
      });

      expect(result.type).toBe('combat_attack');
      expect(result.attacker).toBe('Aragorn');
      expect(result.defender).toBe('Goblin Scout');
      expect(result.attack.hit).toBe(true);
      expect(result.damage).toBeDefined();
      expect(result.damage.application).toBeDefined();

      jest.restoreAllMocks();
    });

    test('should handle missed attack', () => {
      // Mock low roll for guaranteed miss
      jest.spyOn(Math, 'random').mockReturnValue(0.05); // Roll 1

      const result = combatManager.performAttack(testCombatId, 'fighter-1', 'goblin-1', {
        attackType: 'melee'
      });

      expect(result.attack.hit).toBe(false);
      expect(result.damage).toBeNull();

      jest.restoreAllMocks();
    });

    test('should handle critical hits', () => {
      // Mock natural 20
      jest.spyOn(Math, 'random').mockReturnValue(0.995); // Roll 20

      const result = combatManager.performAttack(testCombatId, 'fighter-1', 'goblin-1', {
        attackType: 'melee',
        damageExpression: '1d8+4',
        damageType: 'slashing'
      });

      expect(result.attack.critical).toBe(true);
      expect(result.damage.critical).toBe(true);

      jest.restoreAllMocks();
    });

    test('should check turn order', () => {
      // Try to attack with character who doesn't have current turn
      expect(() => {
        combatManager.performAttack(testCombatId, 'goblin-1', 'fighter-1');
      }).toThrow('It is not the attacker\'s turn');
    });

    test('should check incapacitated condition', () => {
      fighter.addCondition('incapacitated');

      expect(() => {
        combatManager.performAttack(testCombatId, 'fighter-1', 'goblin-1');
      }).toThrow('Attacker cannot act due to conditions');
    });
  });

  describe('performMovement', () => {
    beforeEach(() => {
      combatManager.createCombat(testCombatId);
      combatManager.addParticipant(testCombatId, fighter, 18);
      combatManager.startCombat(testCombatId);
    });

    test('should move character within speed limit', () => {
      const result = combatManager.performMovement(testCombatId, 'fighter-1', { x: 15, y: 0 });

      expect(result.type).toBe('combat_movement');
      expect(result.character).toBe('Aragorn');
      expect(result.from).toEqual({ x: 0, y: 0 });
      expect(result.to).toEqual({ x: 15, y: 0 });
      expect(result.distance).toBe(15);
      expect(result.movementRemaining).toBe(15); // 30 speed - 15 used
    });

    test('should handle difficult terrain', () => {
      const result = combatManager.performMovement(testCombatId, 'fighter-1', { x: 15, y: 0 }, {
        difficultTerrain: true
      });

      expect(result.distance).toBe(30); // Doubled for difficult terrain
      expect(result.movementRemaining).toBe(0);
    });

    test('should prevent movement beyond speed limit', () => {
      expect(() => {
        combatManager.performMovement(testCombatId, 'fighter-1', { x: 40, y: 0 });
      }).toThrow('Not enough movement: need 40, have 30');
    });
  });

  describe('endCombat', () => {
    beforeEach(() => {
      combatManager.createCombat(testCombatId);
      combatManager.addParticipant(testCombatId, fighter, 18);
      combatManager.addParticipant(testCombatId, wizard, 12);
      combatManager.startCombat(testCombatId);
    });

    test('should end combat and provide summary', () => {
      const summary = combatManager.endCombat(testCombatId, 'victory');

      expect(summary.combatId).toBe(testCombatId);
      expect(summary.reason).toBe('victory');
      expect(summary.rounds).toBeGreaterThan(0);
      expect(summary.participants).toHaveLength(2);
      expect(summary.endedAt).toBeInstanceOf(Date);

      // Combat should be removed from active sessions
      expect(combatManager.getCombat(testCombatId)).toBeNull();
    });

    test('should handle combat with casualties', () => {
      // Damage wizard to 0 HP
      wizard.takeDamage(50);

      const summary = combatManager.endCombat(testCombatId);

      const wizardSummary = summary.participants.find(p => p.name === 'Gandalf');
      expect(wizardSummary.finalHP).toBe(0);
      expect(wizardSummary.conditions).toContain('unconscious');
    });
  });

  describe('getCombatState', () => {
    beforeEach(() => {
      combatManager.createCombat(testCombatId);
      combatManager.addParticipant(testCombatId, fighter, 18);
      combatManager.addParticipant(testCombatId, wizard, 12);
      combatManager.startCombat(testCombatId);
    });

    test('should return complete combat state', () => {
      const state = combatManager.getCombatState(testCombatId);

      expect(state.combatId).toBe(testCombatId);
      expect(state.active).toBe(true);
      expect(state.round).toBe(1);
      expect(state.turnOrder).toHaveLength(2);
      expect(state.currentTurn).toBeDefined();
      expect(state.participants).toHaveLength(2);
      expect(state.environment).toBeDefined();

      // Check participant data structure
      const fighterState = state.participants.find(p => p.name === 'Aragorn');
      expect(fighterState.hp).toBe(58);
      expect(fighterState.maxHP).toBe(58);
      expect(fighterState.movementRemaining).toBe(30);
      expect(fighterState.reactionsRemaining).toBe(1);
    });

    test('should return null for non-existent combat', () => {
      const state = combatManager.getCombatState('invalid-combat');
      expect(state).toBeNull();
    });
  });

  describe('getCombatLog', () => {
    beforeEach(() => {
      combatManager.createCombat(testCombatId);
      combatManager.addParticipant(testCombatId, fighter, 18);
      combatManager.startCombat(testCombatId);
    });

    test('should return combat log', () => {
      const log = combatManager.getCombatLog(testCombatId);

      expect(log).toBeInstanceOf(Array);
      expect(log.length).toBeGreaterThan(0);

      const startEvent = log.find(event => event.type === 'combat_started');
      expect(startEvent).toBeDefined();
      expect(startEvent.round).toBe(1);
    });

    test('should return empty array for non-existent combat', () => {
      const log = combatManager.getCombatLog('invalid-combat');
      expect(log).toEqual([]);
    });
  });
});