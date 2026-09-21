/**
 * Rule Engine Tests
 */

import { jest } from '@jest/globals';
import RuleEngine from '../src/core/RuleEngine.js';
import { Character, ABILITIES, SKILLS } from '../src/types/index.js';

describe('RuleEngine', () => {
  let ruleEngine;
  let testCharacter;

  beforeEach(() => {
    ruleEngine = new RuleEngine();
    testCharacter = new Character({
      id: 'test-char-1',
      name: 'Test Character',
      class: 'fighter',
      level: 5,
      abilities: {
        strength: 16,
        dexterity: 14,
        constitution: 15,
        intelligence: 12,
        wisdom: 13,
        charisma: 10
      },
      skills: {
        athletics: { proficient: true },
        perception: { proficient: false },
        stealth: { proficient: true, expertise: true }
      }
    });
  });

  describe('abilityCheck', () => {
    test('should perform basic ability check', () => {
      const result = ruleEngine.abilityCheck(testCharacter, ABILITIES.STRENGTH, 15);

      expect(result.type).toBe('ability_check');
      expect(result.ability).toBe(ABILITIES.STRENGTH);
      expect(result.character).toBe('Test Character');
      expect(result.dc).toBe(15);
      expect(result.bonus).toBe(3); // +3 from strength 16
      expect(result.roll).toBeDefined();
      expect(result.total).toBeDefined();
      expect(typeof result.success).toBe('boolean');
    });

    test('should handle advantage correctly', () => {
      const result = ruleEngine.abilityCheck(testCharacter, ABILITIES.STRENGTH, 15, 1);

      expect(result.roll.advantage).toBe(1);
      expect(result.roll.rolls).toHaveLength(2);
    });

    test('should handle disadvantage correctly', () => {
      const result = ruleEngine.abilityCheck(testCharacter, ABILITIES.STRENGTH, 15, -1);

      expect(result.roll.advantage).toBe(-1);
      expect(result.roll.rolls).toHaveLength(2);
    });

    test('should apply additional bonus', () => {
      const result = ruleEngine.abilityCheck(testCharacter, ABILITIES.STRENGTH, 15, 0, 2);

      expect(result.bonus).toBe(5); // +3 strength + 2 bonus
    });

    test('should throw error for invalid ability', () => {
      expect(() => {
        ruleEngine.abilityCheck(testCharacter, 'invalid', 15);
      }).toThrow('Invalid ability: invalid');
    });
  });

  describe('skillCheck', () => {
    test('should perform basic skill check', () => {
      const result = ruleEngine.skillCheck(testCharacter, SKILLS.ATHLETICS, 20);

      expect(result.type).toBe('skill_check');
      expect(result.skill).toBe(SKILLS.ATHLETICS);
      expect(result.ability).toBe(ABILITIES.STRENGTH);
      expect(result.bonus).toBe(7); // +3 strength + 5 proficiency
    });

    test('should handle expertise correctly', () => {
      const result = ruleEngine.skillCheck(testCharacter, SKILLS.STEALTH, 15);

      expect(result.bonus).toBe(9); // +2 dexterity + 10 expertise
    });

    test('should handle non-proficient skills', () => {
      const result = ruleEngine.skillCheck(testCharacter, SKILLS.PERCEPTION, 15);

      expect(result.bonus).toBe(1); // +1 wisdom only
    });

    test('should throw error for invalid skill', () => {
      expect(() => {
        ruleEngine.skillCheck(testCharacter, 'invalid_skill', 15);
      }).toThrow('Invalid skill: invalid_skill');
    });
  });

  describe('savingThrow', () => {
    test('should perform basic saving throw', () => {
      const result = ruleEngine.savingThrow(testCharacter, ABILITIES.DEXTERITY, 14);

      expect(result.type).toBe('saving_throw');
      expect(result.ability).toBe(ABILITIES.DEXTERITY);
      expect(result.bonus).toBe(2); // +2 dexterity, no proficiency
    });

    test('should handle proficient saves', () => {
      // Add a feature that grants dexterity save proficiency
      testCharacter.features = [
        { type: 'saving_throw_proficiency', ability: ABILITIES.DEXTERITY }
      ];

      const result = ruleEngine.savingThrow(testCharacter, ABILITIES.DEXTERITY, 14);

      expect(result.bonus).toBe(7); // +2 dexterity + 5 proficiency
    });

    test('should handle death saves', () => {
      testCharacter.hitPoints.current = 0;
      testCharacter.addCondition('unconscious');

      const result = ruleEngine.savingThrow(testCharacter, 'death', 10, 0, 0, true);

      expect(result.type).toBe('saving_throw');
      expect(typeof result.success).toBe('boolean');
    });

    test('should handle legendary resistance', () => {
      const result = ruleEngine.savingThrow(testCharacter, ABILITIES.CONSTITUTION, 20, 0, 0, {
        legendaryResistance: true
      });

      expect(result.success).toBe(true);
      expect(result.legendaryResistance).toBe(true);
    });
  });

  describe('attackRoll', () => {
    let defender;

    beforeEach(() => {
      defender = new Character({
        id: 'test-defender',
        name: 'Test Defender',
        class: 'wizard',
        level: 5,
        abilities: {
          dexterity: 12,
          constitution: 14
        },
        armorClass: 15
      });
    });

    test('should perform basic attack roll', () => {
      const result = ruleEngine.attackRoll(testCharacter, defender, 'melee');

      expect(result.type).toBe('attack_roll');
      expect(result.attacker).toBe('Test Character');
      expect(result.defender).toBe('Test Defender');
      expect(result.attackType).toBe('melee');
      expect(result.bonus).toBe(8); // +3 strength + 5 proficiency
      expect(result.targetAC).toBe(15);
      expect(typeof result.hit).toBe('boolean');
    });

    test('should handle ranged attacks', () => {
      const result = ruleEngine.attackRoll(testCharacter, defender, 'ranged');

      expect(result.bonus).toBe(7); // +2 dexterity + 5 proficiency
    });

    test('should handle advantage/disadvantage', () => {
      const resultAdv = ruleEngine.attackRoll(testCharacter, defender, 'melee', 1);
      const resultDis = ruleEngine.attackRoll(testCharacter, defender, 'melee', -1);

      expect(resultAdv.roll.advantage).toBe(1);
      expect(resultDis.roll.advantage).toBe(-1);
    });

    test('should apply additional bonus', () => {
      const result = ruleEngine.attackRoll(testCharacter, defender, 'melee', 0, 2);

      expect(result.bonus).toBe(10); // +3 strength + 5 proficiency + 2 bonus
    });
  });

  describe('rollDamage', () => {
    test('should roll basic damage', () => {
      const result = ruleEngine.rollDamage(testCharacter, '1d8+3', 'slashing');

      expect(result.type).toBe('damage');
      expect(result.attacker).toBe('Test Character');
      expect(result.damageExpression).toBe('1d8+3');
      expect(result.damageType).toBe('slashing');
      expect(result.damageRoll).toBeDefined();
      expect(result.total).toBeGreaterThan(0);
    });

    test('should handle critical hits', () => {
      const result = ruleEngine.rollDamage(testCharacter, '1d8+3', 'slashing', true);

      expect(result.critical).toBe(true);
      expect(result.damageRoll.rolls).toHaveLength(2); // Double dice for crit
    });

    test('should apply damage bonus', () => {
      const result = ruleEngine.rollDamage(testCharacter, '1d8', 'slashing', false, 4);

      expect(result.bonus).toBe(4);
      expect(result.total).toBe(result.damageRoll.total + 4);
    });
  });

  describe('applyDamage', () => {
    test('should apply damage correctly', () => {
      const originalHP = testCharacter.hitPoints.current;
      const result = ruleEngine.applyDamage(testCharacter, 15, 'slashing');

      expect(result.target).toBe('Test Character');
      expect(result.amount).toBe(15);
      expect(result.damageType).toBe('slashing');
      expect(result.damageTaken).toBe(15);
      expect(testCharacter.hitPoints.current).toBe(originalHP - 15);
    });

    test('should handle temporary HP first', () => {
      testCharacter.hitPoints.temporary = 10;
      const originalHP = testCharacter.hitPoints.current;

      const result = ruleEngine.applyDamage(testCharacter, 15, 'slashing');

      expect(result.tempHPConsumed).toBe(10);
      expect(result.damageTaken).toBe(5);
      expect(testCharacter.hitPoints.current).toBe(originalHP - 5);
      expect(testCharacter.hitPoints.temporary).toBe(0);
    });

    test('should knock unconscious at 0 HP', () => {
      testCharacter.hitPoints.current = 10;
      const result = ruleEngine.applyDamage(testCharacter, 15, 'slashing');

      expect(result.knockedUnconscious).toBe(true);
      expect(testCharacter.hasCondition('unconscious')).toBe(true);
    });

    test('should handle damage resistance', () => {
      testCharacter.resistances = ['slashing'];
      const result = ruleEngine.applyDamage(testCharacter, 10, 'slashing');

      expect(result.reducedAmount).toBe(5); // Half damage
    });

    test('should handle damage immunity', () => {
      testCharacter.immunities = ['fire'];
      const result = ruleEngine.applyDamage(testCharacter, 10, 'fire');

      expect(result.reducedAmount).toBe(0);
    });

    test('should handle damage vulnerability', () => {
      testCharacter.vulnerabilities = ['cold'];
      const result = ruleEngine.applyDamage(testCharacter, 10, 'cold');

      expect(result.reducedAmount).toBe(20); // Double damage
    });
  });

  describe('validateCharacter', () => {
    test('should validate valid character', () => {
      const result = ruleEngine.validateCharacter(testCharacter);

      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    test('should detect invalid ability scores', () => {
      testCharacter.abilities.strength = 25; // Too high
      testCharacter.abilities.dexterity = 0; // Too low

      const result = ruleEngine.validateCharacter(testCharacter);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Invalid strength score: 25 (must be 1-20)');
      expect(result.errors).toContain('Invalid dexterity score: 0 (must be 1-20)');
    });

    test('should detect negative HP', () => {
      testCharacter.hitPoints.current = -5;

      const result = ruleEngine.validateCharacter(testCharacter);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Current hit points cannot be negative');
    });

    test('should detect HP exceeding maximum', () => {
      testCharacter.hitPoints.current = 100;
      testCharacter.hitPoints.maximum = 50;

      const result = ruleEngine.validateCharacter(testCharacter);

      expect(result.valid).toBe(true); // Still valid, but with warning
      expect(result.warnings).toContain('Current hit points exceed maximum');
    });

    test('should detect incorrect proficiency bonus', () => {
      testCharacter.proficiencyBonus = 10; // Wrong for level 5

      const result = ruleEngine.validateCharacter(testCharacter);

      expect(result.valid).toBe(true); // Still valid, but with warning
      expect(result.warnings).toContain('Proficiency bonus is 10, expected 3 for level 5');
    });

    test('should detect invalid AC', () => {
      testCharacter.armorClass = 0;

      const result = ruleEngine.validateCharacter(testCharacter);

      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Armor class cannot be less than 1');
    });
  });
});