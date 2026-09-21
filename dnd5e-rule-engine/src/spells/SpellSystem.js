/**
 * Comprehensive Spell System for D&D 5e
 */

import { SPELL_LEVELS, MAGIC_SCHOOLS, CONDITIONS } from '../types/index.js';
import { DiceRoller } from '../core/DiceRoller.js';
import { SavingThrows } from '../mechanics/SavingThrows.js';

export class SpellSystem {
  constructor() {
    this.spellSlots = new Map(); // characterId -> spellSlots
    this.concentrationSpells = new Map(); // characterId -> concentration spell
    this.spellEffects = new Map(); // characterId -> active spell effects
  }

  /**
   * Initialize spell slots for a character
   * @param {string} characterId - Character identifier
   * @param {object} spellcasting - Spellcasting ability and level info
   */
  initializeSpellSlots(characterId, spellcasting) {
    const { ability, level, class: characterClass } = spellcasting;

    // Calculate spell slots based on class and level
    const slots = this.calculateSpellSlots(characterClass, level);

    this.spellSlots.set(characterId, {
      ability,
      level,
      class: characterClass,
      slots,
      used: Object.fromEntries(Object.keys(slots).map(level => [level, 0]))
    });
  }

  /**
   * Calculate spell slots for a character class and level
   * @param {string} characterClass - Character class
   * @param {number} level - Character level
   * @returns {object} Spell slots per level
   */
  calculateSpellSlots(characterClass, level) {
    // Simplified spell slot calculation - full implementation would be class-specific
    const slots = { 0: [] }; // Cantrips are unlimited

    if (level < 1) return slots;

    // Basic spell slot progression (simplified)
    if (characterClass === 'wizard' || characterClass === 'sorcerer' || characterClass === 'warlock') {
      if (level >= 1) slots[1] = [2, 3, 4, 4, 4, 4, 4, 4, 4, 4][Math.min(level - 1, 9)] || 4;
      if (level >= 3) slots[2] = [0, 0, 2, 3, 3, 3, 3, 3, 3, 3][Math.min(level - 1, 9)] || 3;
      if (level >= 5) slots[3] = [0, 0, 0, 2, 3, 3, 3, 3, 3, 3][Math.min(level - 1, 9)] || 3;
      if (level >= 7) slots[4] = [0, 0, 0, 0, 1, 2, 3, 3, 3, 3][Math.min(level - 1, 9)] || 3;
      if (level >= 9) slots[5] = [0, 0, 0, 0, 0, 1, 2, 2, 2, 2][Math.min(level - 1, 9)] || 2;
      if (level >= 11) slots[6] = [0, 0, 0, 0, 0, 0, 1, 1, 2, 2][Math.min(level - 1, 9)] || 2;
      if (level >= 13) slots[7] = [0, 0, 0, 0, 0, 0, 0, 1, 1, 1][Math.min(level - 1, 9)] || 1;
      if (level >= 15) slots[8] = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1][Math.min(level - 1, 9)] || 1;
      if (level >= 17) slots[9] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 1][Math.min(level - 1, 9)] || 1;
    }

    return slots;
  }

  /**
   * Cast a spell
   * @param {Character} caster - Character casting the spell
   * @param {object} spell - Spell being cast
   * @param {object} options - Casting options
   * @returns {object} Spell casting result
   */
  castSpell(caster, spell, options = {}) {
    const {
      spellLevel = spell.level,
      target = null,
      metamagic = null,
      ritual = false,
      higherLevel = false
    } = options;

    // Validate casting ability
    const spellcastingData = this.spellSlots.get(caster.id);
    if (!spellcastingData) {
      return {
        success: false,
        reason: 'Character has no spellcasting ability'
      };
    }

    // Check if character can cast this spell
    if (!this.canCastSpell(caster, spell)) {
      return {
        success: false,
        reason: 'Character cannot cast this spell'
      };
    }

    // Check spell slot availability (except for cantrips and rituals)
    if (spellLevel > 0 && !ritual) {
      if (!this.hasSpellSlot(caster.id, spellLevel)) {
        return {
          success: false,
          reason: `No spell slots available for level ${spellLevel}`
        };
      }
    }

    // Check concentration
    if (spell.concentration && this.hasConcentrationSpell(caster.id)) {
      return {
        success: false,
        reason: 'Already concentrating on another spell'
      };
    }

    // Calculate spell save DC
    const saveDC = this.calculateSaveDC(caster, spellcastingData.ability);

    // Calculate spell attack bonus
    const attackBonus = this.calculateSpellAttackBonus(caster, spellcastingData.ability);

    // Consume spell slot
    if (spellLevel > 0 && !ritual) {
      this.consumeSpellSlot(caster.id, spellLevel);
    }

    // Handle concentration
    if (spell.concentration) {
      this.setConcentrationSpell(caster.id, spell);
    }

    // Perform spell effects
    const spellEffect = this.executeSpellEffect(caster, spell, target, {
      spellLevel,
      saveDC,
      attackBonus,
      metamagic,
      higherLevel
    });

    const result = {
      success: true,
      caster: caster.name,
      spell: spell.name,
      level: spellLevel,
      school: spell.school,
      castingTime: spell.castingTime,
      range: spell.range,
      components: spell.components,
      duration: spell.duration,
      concentration: spell.concentration,
      ritual: ritual,
      saveDC,
      attackBonus,
      effect: spellEffect,
      spellSlotUsed: spellLevel > 0 && !ritual,
      higherLevel
    };

    return result;
  }

  /**
   * Check if character can cast a spell
   * @param {Character} caster - Character to check
   * @param {object} spell - Spell to check
   * @returns {boolean} Whether character can cast the spell
   */
  canCastSpell(caster, spell) {
    // Check if spell is in character's spell list
    const characterSpells = caster.spells?.known || [];
    return characterSpells.some(knownSpell => knownSpell.name === spell.name);
  }

  /**
   * Check if character has available spell slot
   * @param {string} characterId - Character identifier
   * @param {number} spellLevel - Spell level to check
   * @returns {boolean} Whether spell slot is available
   */
  hasSpellSlot(characterId, spellLevel) {
    const spellSlots = this.spellSlots.get(characterId);
    if (!spellSlots) return false;

    const available = spellSlots.slots[spellLevel] || 0;
    const used = spellSlots.used[spellLevel] || 0;
    return used < available;
  }

  /**
   * Consume a spell slot
   * @param {string} characterId - Character identifier
   * @param {number} spellLevel - Spell level to consume
   */
  consumeSpellSlot(characterId, spellLevel) {
    const spellSlots = this.spellSlots.get(characterId);
    if (spellSlots) {
      spellSlots.used[spellLevel] = (spellSlots.used[spellLevel] || 0) + 1;
    }
  }

  /**
   * Calculate spell save DC
   * @param {Character} caster - Spell caster
   * @param {string} ability - Spellcasting ability
   * @returns {number} Spell save DC
   */
  calculateSaveDC(caster, ability) {
    const abilityModifier = caster.getAbilityModifier(ability);
    return 8 + abilityModifier + caster.proficiencyBonus;
  }

  /**
   * Calculate spell attack bonus
   * @param {Character} caster - Spell caster
   * @param {string} ability - Spellcasting ability
   * @returns {number} Spell attack bonus
   */
  calculateSpellAttackBonus(caster, ability) {
    const abilityModifier = caster.getAbilityModifier(ability);
    return abilityModifier + caster.proficiencyBonus;
  }

  /**
   * Execute spell effects based on spell type
   * @param {Character} caster - Spell caster
   * @param {object} spell - Spell being cast
   * @param {Character} target - Spell target
   * @param {object} options - Spell execution options
   * @returns {object} Spell effect result
   */
  executeSpellEffect(caster, spell, target, options) {
    const { saveDC, attackBonus, spellLevel, higherLevel } = options;

    switch (spell.effectType) {
      case 'damage':
        return this.executeDamageSpell(caster, spell, target, { saveDC, attackBonus, spellLevel, higherLevel });
      case 'healing':
        return this.executeHealingSpell(caster, spell, target, { spellLevel, higherLevel });
      case 'save_or_effect':
        return this.executeSaveOrEffectSpell(caster, spell, target, { saveDC, spellLevel });
      case 'attack_roll':
        return this.executeAttackRollSpell(caster, spell, target, { attackBonus, spellLevel });
      case 'utility':
        return this.executeUtilitySpell(caster, spell, target, { spellLevel });
      case 'summoning':
        return this.executeSummoningSpell(caster, spell, { spellLevel });
      case 'illusion':
        return this.executeIllusionSpell(caster, spell, target, { saveDC, spellLevel });
      default:
        return { type: 'unknown', description: 'Spell effect type not implemented' };
    }
  }

  /**
   * Execute damage spell
   * @param {Character} caster - Spell caster
   * @param {object} spell - Damage spell
   * @param {Character} target - Spell target
   * @param {object} options - Execution options
   * @returns {object} Damage result
   */
  executeDamageSpell(caster, spell, target, options) {
    const { saveDC, spellLevel, higherLevel } = options;
    const result = {
      type: 'damage',
      spell: spell.name,
      target: target?.name,
      damageType: spell.damageType,
      damage: 0,
      save: null,
      hit: false
    };

    // Roll damage
    let damageExpression = spell.damage;
    if (higherLevel && spell.higherLevelDamage) {
      // Add additional damage dice for higher level casting
      const extraDice = spellLevel - spell.level;
      if (extraDice > 0) {
        const baseDice = damageExpression.match(/(\d+)d(\d+)/);
        if (baseDice) {
          const newNumDice = parseInt(baseDice[1]) + extraDice;
          damageExpression = damageExpression.replace(/\d+d/, `${newNumDice}d`);
        }
      }
    }

    const damageRoll = DiceRoller.rollExpression(damageExpression);
    let totalDamage = damageRoll.total;

    // Check for saving throw
    if (spell.save && target) {
      const save = SavingThrows.performSave(target, spell.save, saveDC);
      result.save = save;

      if (save.success) {
        // Half damage on successful save (unless specified otherwise)
        totalDamage = Math.floor(totalDamage / (spell.halfDamageOnSave ? 2 : 1));
      } else {
        result.hit = true;
      }
    } else if (target) {
      // No save, automatic hit
      result.hit = true;
    }

    // Apply damage if target exists
    if (target && totalDamage > 0) {
      const damageApplication = this.applyDamage(target, totalDamage, spell.damageType);
      result.damageApplication = damageApplication;
    }

    result.damage = totalDamage;
    result.damageRoll = damageRoll;

    return result;
  }

  /**
   * Execute healing spell
   * @param {Character} caster - Spell caster
   * @param {object} spell - Healing spell
   * @param {Character} target - Spell target
   * @param {object} options - Execution options
   * @returns {object} Healing result
   */
  executeHealingSpell(caster, spell, target, options) {
    const { spellLevel } = options;
    const result = {
      type: 'healing',
      spell: spell.name,
      target: target?.name,
      healing: 0
    };

    if (!target) {
      result.reason = 'No target specified for healing spell';
      return result;
    }

    // Roll healing
    let healingExpression = spell.healing;
    if (spellLevel > spell.level && spell.higherLevelHealing) {
      const extraHealing = (spellLevel - spell.level) * spell.higherLevelHealing;
      healingExpression += ` + ${extraHealing}`;
    }

    const healingRoll = DiceRoller.rollExpression(healingExpression);
    const totalHealing = healingRoll.total;

    // Apply healing
    const originalHP = target.hitPoints.current;
    target.heal(totalHealing);

    result.healing = totalHealing;
    result.healingRoll = healingRoll;
    result.originalHP = originalHP;
    result.newHP = target.hitPoints.current;
    result.actualHealing = target.hitPoints.current - originalHP;

    return result;
  }

  /**
   * Execute save or effect spell
   * @param {Character} caster - Spell caster
   * @param {object} spell - Spell with save effect
   * @param {Character} target - Spell target
   * @param {object} options - Execution options
   * @returns {object} Save or effect result
   */
  executeSaveOrEffectSpell(caster, spell, target, options) {
    const { saveDC } = options;
    const result = {
      type: 'save_or_effect',
      spell: spell.name,
      target: target?.name,
      effect: null,
      save: null
    };

    if (!target) {
      result.reason = 'No target specified for save or effect spell';
      return result;
    }

    // Perform saving throw
    const save = SavingThrows.performSave(target, spell.save, saveDC);
    result.save = save;

    if (!save.success) {
      // Apply spell effect
      result.effect = this.applySpellEffect(target, spell.effect);
    } else {
      result.effect = 'Saved against spell effect';
    }

    return result;
  }

  /**
   * Execute attack roll spell
   * @param {Character} caster - Spell caster
   * @param {object} spell - Attack roll spell
   * @param {Character} target - Spell target
   * @param {object} options - Execution options
   * @returns {object} Attack roll result
   */
  executeAttackRollSpell(caster, spell, target, options) {
    const { attackBonus } = options;
    const result = {
      type: 'attack_roll',
      spell: spell.name,
      target: target?.name,
      attackRoll: null,
      hit: false,
      damage: 0
    };

    if (!target) {
      result.reason = 'No target specified for attack roll spell';
      return result;
    }

    // Make spell attack roll
    const attackRoll = DiceRoller.rollD20();
    const total = attackRoll.total + attackBonus;
    const hit = total >= target.armorClass;

    result.attackRoll = {
      roll: attackRoll,
      bonus: attackBonus,
      total,
      targetAC: target.armorClass,
      hit,
      critical: attackRoll.isCritical
    };

    if (hit) {
      // Roll damage
      const damageRoll = DiceRoller.rollExpression(spell.damage);
      let damage = damageRoll.total;

      if (attackRoll.isCritical) {
        // Critical hit - double damage dice
        const critDamageRoll = DiceRoller.rollExpression(spell.damage);
        damage = damageRoll.total + critDamageRoll.total;
      }

      const damageApplication = this.applyDamage(target, damage, spell.damageType);
      result.damage = damage;
      result.damageRoll = damageRoll;
      result.damageApplication = damageApplication;
    }

    return result;
  }

  /**
   * Execute utility spell
   * @param {Character} caster - Spell caster
   * @param {object} spell - Utility spell
   * @param {Character} target - Spell target
   * @param {object} options - Execution options
   * @returns {object} Utility result
   */
  executeUtilitySpell(caster, spell, target, options) {
    return {
      type: 'utility',
      spell: spell.name,
      target: target?.name,
      effect: spell.description,
      description: `${spell.name} cast successfully`
    };
  }

  /**
   * Execute summoning spell
   * @param {Character} caster - Spell caster
   * @param {object} spell - Summoning spell
   * @param {object} options - Execution options
   * @returns {object} Summoning result
   */
  executeSummoningSpell(caster, spell, options) {
    // This would interface with a creature/monster system
    return {
      type: 'summoning',
      spell: spell.name,
      creature: spell.summons,
      duration: spell.duration,
      description: `${spell.summons} summoned by ${caster.name}`
    };
  }

  /**
   * Execute illusion spell
   * @param {Character} caster - Spell caster
   * @param {object} spell - Illusion spell
   * @param {Character} target - Spell target
   * @param {object} options - Execution options
   * @returns {object} Illusion result
   */
  executeIllusionSpell(caster, spell, target, options) {
    const result = {
      type: 'illusion',
      spell: spell.name,
      target: target?.name,
      illusion: spell.illusionType,
      perceived: false
    };

    if (target && spell.save) {
      const save = SavingThrows.performSave(target, spell.save, options.saveDC);
      result.save = save;
      result.perceived = !save.success;
    } else {
      result.perceived = true;
    }

    return result;
  }

  /**
   * Apply damage to target
   * @param {Character} target - Target character
   * @param {number} amount - Damage amount
   * @param {string} damageType - Type of damage
   * @returns {object} Damage application result
   */
  applyDamage(target, amount, damageType) {
    const originalHP = target.hitPoints.current;
    target.takeDamage(amount);

    return {
      originalHP,
      newHP: target.hitPoints.current,
      damageDealt: originalHP - target.hitPoints.current,
      damageType
    };
  }

  /**
   * Apply spell effect to target
   * @param {Character} target - Target character
   * @param {object} effect - Effect to apply
   * @returns {string} Effect description
   */
  applySpellEffect(target, effect) {
    if (effect.type === 'condition') {
      target.addCondition(effect.condition);
      return `${target.name} is now ${effect.condition}`;
    } else if (effect.type === 'damage') {
      const damageApplication = this.applyDamage(target, effect.amount, effect.damageType);
      return `${target.name} takes ${damageApplication.damageDealt} ${effect.damageType} damage`;
    } else {
      return `Applied ${effect.type} effect to ${target.name}`;
    }
  }

  /**
   * Handle concentration checks
   * @param {Character} caster - Character concentrating
   * @param {number} damage - Damage taken
   * @returns {object} Concentration check result
   */
  handleConcentrationCheck(caster, damage) {
    if (!this.hasConcentrationSpell(caster.id)) {
      return { hasConcentration: false };
    }

    const dc = Math.max(10, Math.floor(damage / 2));
    const save = SavingThrows.performSave(caster, 'constitution', dc);

    if (!save.success) {
      this.breakConcentration(caster.id);
      save.concentrationBroken = true;
    }

    return {
      hasConcentration: true,
      concentrationSpell: this.getConcentrationSpell(caster.id),
      check: save
    };
  }

  /**
   * Check if character has concentration spell
   * @param {string} characterId - Character identifier
   * @returns {boolean} Whether character has concentration spell
   */
  hasConcentrationSpell(characterId) {
    return this.concentrationSpells.has(characterId);
  }

  /**
   * Get concentration spell for character
   * @param {string} characterId - Character identifier
   * @returns {object|null} Concentration spell or null
   */
  getConcentrationSpell(characterId) {
    return this.concentrationSpells.get(characterId) || null;
  }

  /**
   * Set concentration spell for character
   * @param {string} characterId - Character identifier
   * @param {object} spell - Concentration spell
   */
  setConcentrationSpell(characterId, spell) {
    this.concentrationSpells.set(characterId, spell);
  }

  /**
   * Break concentration for character
   * @param {string} characterId - Character identifier
   */
  breakConcentration(characterId) {
    const spell = this.concentrationSpells.get(characterId);
    this.concentrationSpells.delete(characterId);
    return spell;
  }

  /**
   * Restore spell slots (for long rest)
   * @param {string} characterId - Character identifier
   */
  restoreSpellSlots(characterId) {
    const spellSlots = this.spellSlots.get(characterId);
    if (spellSlots) {
      Object.keys(spellSlots.used).forEach(level => {
        spellSlots.used[level] = 0;
      });
    }
  }

  /**
   * Get spell slot information for character
   * @param {string} characterId - Character identifier
   * @returns {object} Spell slot information
   */
  getSpellSlots(characterId) {
    return this.spellSlots.get(characterId) || null;
  }
}

export default SpellSystem;