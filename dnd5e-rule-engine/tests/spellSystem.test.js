/**
 * Spell System Tests
 */

import { jest } from '@jest/globals';
import SpellSystem from '../src/spells/SpellSystem.js';
import { Character, ABILITIES } from '../src/types/index.js';
import { getSpell } from '../src/spells/SpellData.js';

describe('SpellSystem', () => {
  let spellSystem;
  let wizard;
  let fighter;

  beforeEach(() => {
    spellSystem = new SpellSystem();

    wizard = new Character({
      id: 'wizard-1',
      name: 'Merlin',
      class: 'wizard',
      level: 5,
      abilities: {
        intelligence: 18,
        constitution: 14,
        dexterity: 12
      },
      skills: {
        arcana: { proficient: true }
      }
    });

    fighter = new Character({
      id: 'fighter-1',
      name: 'Conan',
      class: 'fighter',
      level: 5,
      abilities: {
        strength: 18,
        constitution: 16,
        dexterity: 14
      }
    });

    // Initialize spell slots for wizard
    spellSystem.initializeSpellSlots(wizard.id, {
      ability: 'intelligence',
      level: 5,
      class: 'wizard'
    });
  });

  describe('initializeSpellSlots', () => {
    test('should initialize spell slots for spellcaster', () => {
      const spellSlots = spellSystem.getSpellSlots(wizard.id);

      expect(spellSlots.ability).toBe('intelligence');
      expect(spellSlots.level).toBe(5);
      expect(spellSlots.class).toBe('wizard');
      expect(spellSlots.slots[1]).toBe(4); // Wizard gets 4 1st level slots at level 5
      expect(spellSlots.slots[2]).toBe(3); // 3 2nd level slots
      expect(spellSlots.slots[3]).toBe(2); // 2 3rd level slots
      expect(spellSlots.used[1]).toBe(0);
      expect(spellSlots.used[2]).toBe(0);
      expect(spellSlots.used[3]).toBe(0);
    });

    test('should handle different classes correctly', () => {
      spellSystem.initializeSpellSlots(fighter.id, {
        ability: 'wisdom',
        level: 1,
        class: 'paladin'
      });

      const spellSlots = spellSystem.getSpellSlots(fighter.id);
      expect(spellSlots.ability).toBe('wisdom');
      expect(spellSlots.class).toBe('paladin');
    });
  });

  describe('castSpell', () => {
    test('should cast simple damage spell', () => {
      const fireBolt = getSpell('fire bolt');
      const result = spellSystem.castSpell(wizard, fireBolt);

      expect(result.success).toBe(true);
      expect(result.caster).toBe('Merlin');
      expect(result.spell).toBe('Fire Bolt');
      expect(result.level).toBe(0); // Cantrip
      expect(result.saveDC).toBe(14); // 8 + 4 int mod + 3 proficiency
      expect(result.attackBonus).toBe(7); // 4 int mod + 3 proficiency
      expect(result.spellSlotUsed).toBe(false); // Cantrip doesn't use slot
    });

    test('should cast leveled spell', () => {
      const fireball = getSpell('fireball');
      const result = spellSystem.castSpell(wizard, fireball);

      expect(result.success).toBe(true);
      expect(result.spell).toBe('Fireball');
      expect(result.level).toBe(3); // 3rd level spell
      expect(result.spellSlotUsed).toBe(true);
      expect(result.effect.type).toBe('damage');
      expect(result.effect.damageType).toBe('fire');
    });

    test('should handle spell with target', () => {
      const fireball = getSpell('fireball');
      const result = spellSystem.castSpell(wizard, fireball, {
        target: fighter,
        spellLevel: 3
      });

      expect(result.effect.target).toBe('Conan');
      expect(result.effect.save).toBeDefined();
      expect(result.effect.damageRoll).toBeDefined();
    });

    test('should handle healing spells', () => {
      const cureWounds = getSpell('cure wounds');
      wizard.hitPoints.current = 25;

      const result = spellSystem.castSpell(wizard, cureWounds, {
        target: wizard
      });

      expect(result.effect.type).toBe('healing');
      expect(result.effect.target).toBe('Merlin');
      expect(result.effect.healing).toBeGreaterThan(0);
      expect(result.effect.originalHP).toBe(25);
      expect(result.effect.newHP).toBeGreaterThan(25);
    });

    test('should handle spells with concentration', () => {
      const fly = getSpell('fly');
      const result = spellSystem.castSpell(wizard, fly, {
        target: wizard
      });

      expect(result.concentration).toBe(true);
      expect(spellSystem.hasConcentrationSpell(wizard.id)).toBe(true);
      expect(spellSystem.getConcentrationSpell(wizard.id).name).toBe('Fly');
    });

    test('should prevent casting when already concentrating', () => {
      // Cast first concentration spell
      const fly = getSpell('fly');
      spellSystem.castSpell(wizard, fly, { target: wizard });

      // Try to cast second concentration spell
      const haste = getSpell('haste');
      const result = spellSystem.castSpell(wizard, haste, { target: wizard });

      expect(result.success).toBe(false);
      expect(result.reason).toBe('Already concentrating on another spell');
    });

    test('should consume spell slots', () => {
      const fireball = getSpell('fireball');
      const initialSlots = spellSystem.getSpellSlots(wizard.id);

      spellSystem.castSpell(wizard, fireball);

      const updatedSlots = spellSystem.getSpellSlots(wizard.id);
      expect(updatedSlots.used[3]).toBe(initialSlots.used[3] + 1);
    });

    test('should handle insufficient spell slots', () => {
      // Use up all 3rd level slots
      spellSystem.consumeSpellSlot(wizard.id, 3);
      spellSystem.consumeSpellSlot(wizard.id, 3);

      const fireball = getSpell('fireball');
      const result = spellSystem.castSpell(wizard, fireball);

      expect(result.success).toBe(false);
      expect(result.reason).toBe('No spell slots available for level 3');
    });

    test('should handle ritual casting', () => {
      const detectMagic = getSpell('detect magic');
      const result = spellSystem.castSpell(wizard, detectMagic, {
        ritual: true
      });

      expect(result.success).toBe(true);
      expect(result.ritual).toBe(true);
      expect(result.spellSlotUsed).toBe(false);
    });

    test('should handle higher level casting', () => {
      const fireball = getSpell('fireball');
      const result = spellSystem.castSpell(wizard, fireball, {
        spellLevel: 4,
        target: fighter
      });

      expect(result.level).toBe(4);
      expect(result.higherLevel).toBe(true);
      // Fireball does 1d6 extra damage per level above 3rd
      expect(result.effect.damageRoll.expression).toBe('9d6'); // 8d6 base + 1d6 higher level
    });

    test('should reject casting for non-spellcaster', () => {
      const fireBolt = getSpell('fire bolt');
      const result = spellSystem.castSpell(fighter, fireBolt);

      expect(result.success).toBe(false);
      expect(result.reason).toBe('Character has no spellcasting ability');
    });
  });

  describe('executeSpellEffect', () => {
    test('should handle damage spells with saves', () => {
      const fireball = getSpell('fireball');
      const result = spellSystem.executeSpellEffect(wizard, fireball, fighter, {
        spellLevel: 3,
        saveDC: 14
      });

      expect(result.type).toBe('damage');
      expect(result.damageType).toBe('fire');
      expect(result.save).toBeDefined();
      expect(typeof result.save.success).toBe('boolean');
      expect(result.damageRoll).toBeDefined();
    });

    test('should handle attack roll spells', () => {
      const scorchingRay = getSpell('scorching ray');
      const result = spellSystem.executeSpellEffect(wizard, scorchingRay, fighter, {
        spellLevel: 2,
        attackBonus: 7
      });

      expect(result.type).toBe('attack_roll');
      expect(result.attackRoll).toBeDefined();
      expect(typeof result.attackRoll.hit).toBe('boolean');
      if (result.attackRoll.hit) {
        expect(result.damage).toBeDefined();
      }
    });

    test('should handle save or effect spells', () => {
      const charmPerson = getSpell('charm person');
      const result = spellSystem.executeSpellEffect(wizard, charmPerson, fighter, {
        spellLevel: 1,
        saveDC: 14
      });

      expect(result.type).toBe('save_or_effect');
      expect(result.save).toBeDefined();
      if (!result.save.success) {
        expect(result.effect).toBeDefined();
      }
    });

    test('should handle utility spells', () => {
      const mageHand = getSpell('mage hand');
      const result = spellSystem.executeSpellEffect(wizard, mageHand, null, {
        spellLevel: 0
      });

      expect(result.type).toBe('utility');
      expect(result.effect).toBeDefined();
    });

    test('should handle illusion spells', () => {
      const invisibility = getSpell('invisibility');
      const result = spellSystem.executeSpellEffect(wizard, invisibility, fighter, {
        spellLevel: 2,
        saveDC: 14
      });

      expect(result.type).toBe('illusion');
      expect(result.perceived).toBeDefined();
    });
  });

  describe('calculateSaveDC', () => {
    test('should calculate correct save DC', () => {
      const saveDC = spellSystem.calculateSaveDC(wizard, 'intelligence');

      expect(saveDC).toBe(14); // 8 + 4 int mod + 3 proficiency
    });

    test('should handle different abilities', () => {
      // Add charisma modifier to simulate sorcerer
      wizard.abilities.charisma = 16;
      const saveDC = spellSystem.calculateSaveDC(wizard, 'charisma');

      expect(saveDC).toBe(13); // 8 + 3 cha mod + 3 proficiency
    });
  });

  describe('calculateSpellAttackBonus', () => {
    test('should calculate correct attack bonus', () => {
      const attackBonus = spellSystem.calculateSpellAttackBonus(wizard, 'intelligence');

      expect(attackBonus).toBe(7); // 4 int mod + 3 proficiency
    });
  });

  describe('handleConcentrationCheck', () => {
    beforeEach(() => {
      // Set up concentration spell
      const fly = getSpell('fly');
      spellSystem.castSpell(wizard, fly, { target: wizard });
    });

    test('should pass concentration check with low damage', () => {
      const result = spellSystem.handleConcentrationCheck(wizard, 5);

      expect(result.hasConcentration).toBe(true);
      expect(result.check.success).toBe(true);
      expect(result.check.concentrationBroken).toBeUndefined();
    });

    test('should handle concentration failure', () => {
      // Mock Constitution save failure
      jest.spyOn(Math, 'random').mockReturnValue(0.1); // Low roll

      const result = spellSystem.handleConcentrationCheck(wizard, 25);

      expect(result.hasConcentration).toBe(true);
      expect(result.check.success).toBe(false);
      expect(result.check.concentrationBroken).toBe(true);
      expect(spellSystem.hasConcentrationSpell(wizard.id)).toBe(false);

      jest.restoreAllMocks();
    });

    test('should handle character without concentration', () => {
      spellSystem.breakConcentration(wizard.id);
      const result = spellSystem.handleConcentrationCheck(wizard, 25);

      expect(result.hasConcentration).toBe(false);
    });
  });

  describe('restoreSpellSlots', () => {
    test('should restore all spell slots', () => {
      // Use some spell slots
      spellSystem.consumeSpellSlot(wizard.id, 1);
      spellSystem.consumeSpellSlot(wizard.id, 3);

      // Restore
      spellSystem.restoreSpellSlots(wizard.id);

      const spellSlots = spellSystem.getSpellSlots(wizard.id);
      expect(spellSlots.used[1]).toBe(0);
      expect(spellSlots.used[2]).toBe(0);
      expect(spellSlots.used[3]).toBe(0);
    });
  });

  describe('concentration management', () => {
    test('should set concentration spell', () => {
      const fly = getSpell('fly');
      spellSystem.setConcentrationSpell(wizard.id, fly);

      expect(spellSystem.hasConcentrationSpell(wizard.id)).toBe(true);
      expect(spellSystem.getConcentrationSpell(wizard.id)).toBe(fly);
    });

    test('should break concentration', () => {
      const fly = getSpell('fly');
      spellSystem.setConcentrationSpell(wizard.id, fly);

      const brokenSpell = spellSystem.breakConcentration(wizard.id);

      expect(spellSystem.hasConcentrationSpell(wizard.id)).toBe(false);
      expect(brokenSpell).toBe(fly);
    });

    test('should handle breaking non-existent concentration', () => {
      const result = spellSystem.breakConcentration(wizard.id);
      expect(result).toBeUndefined();
    });
  });
});