/**
 * D&D 5e Rule Engine - Main Entry Point
 */

import RuleEngine from './core/RuleEngine.js';
import CombatManager from './combat/CombatManager.js';
import SpellSystem from './spells/SpellSystem.js';
import ConditionSystem from './conditions/ConditionSystem.js';
import CharacterFeatures from './features/CharacterFeatures.js';
import { Character, ABILITIES, SKILLS, CONDITIONS, DAMAGE_TYPES } from './types/index.js';
import { DiceRoller } from './core/DiceRoller.js';

// Import and start API server if this is run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  import('./api/server.js');
}

/**
 * D&D 5e Rule Engine - Complete rules implementation
 */
export class DnD5eRuleEngine {
  constructor() {
    this.ruleEngine = new RuleEngine();
    this.combatManager = new CombatManager(this.ruleEngine);
    this.spellSystem = new SpellSystem();
    this.conditionSystem = new ConditionSystem();
    this.characterFeatures = new CharacterFeatures();
    this.characters = new Map();
  }

  /**
   * Create a new character
   * @param {object} characterData - Character data
   * @returns {Character} Created character
   */
  createCharacter(characterData) {
    const character = new Character(characterData);

    // Apply class features
    if (characterData.class) {
      this.characterFeatures.applyClassFeatures(
        character,
        characterData.class,
        characterData.level || 1,
        characterData.choices || {}
      );
    }

    // Apply racial traits
    if (characterData.race) {
      this.characterFeatures.applyRacialTraits(
        character,
        characterData.race,
        characterData.racialChoices || {}
      );
    }

    // Apply feats
    if (characterData.feats) {
      characterData.feats.forEach(feat => {
        this.characterFeatures.applyFeat(character, feat.name, feat.choices || {});
      });
    }

    // Initialize spell slots
    if (characterData.spellcasting) {
      this.spellSystem.initializeSpellSlots(character.id, characterData.spellcasting);
    }

    this.characters.set(character.id, character);
    return character;
  }

  /**
   * Get character by ID
   * @param {string} characterId - Character identifier
   * @returns {Character|null} Character or null
   */
  getCharacter(characterId) {
    return this.characters.get(characterId) || null;
  }

  /**
   * Perform ability check
   * @param {string} characterId - Character ID
   * @param {string} ability - Ability to check
   * @param {number} dc - Difficulty class
   * @param {object} options - Check options
   * @returns {object} Check result
   */
  abilityCheck(characterId, ability, dc, options = {}) {
    const character = this.getCharacter(characterId);
    if (!character) {
      throw new Error('Character not found');
    }

    return this.ruleEngine.abilityCheck(character, ability, dc, options.advantage, options.bonus);
  }

  /**
   * Perform skill check
   * @param {string} characterId - Character ID
   * @param {string} skill - Skill to check
   * @param {number} dc - Difficulty class
   * @param {object} options - Check options
   * @returns {object} Check result
   */
  async skillCheck(characterId, skill, dc, options = {}) {
    const character = this.getCharacter(characterId);
    if (!character) {
      throw new Error('Character not found');
    }

    const { SkillChecks } = await import('./mechanics/SkillChecks.js');
    return SkillChecks.performCheck(character, skill, dc, options);
  }

  /**
   * Perform saving throw
   * @param {string} characterId - Character ID
   * @param {string} ability - Ability for save
   * @param {number} dc - Difficulty class
   * @param {object} options - Save options
   * @returns {object} Save result
   */
  async savingThrow(characterId, ability, dc, options = {}) {
    const character = this.getCharacter(characterId);
    if (!character) {
      throw new Error('Character not found');
    }

    const { SavingThrows } = await import('./mechanics/SavingThrows.js');
    return SavingThrows.performSave(character, ability, dc, options);
  }

  /**
   * Create combat encounter
   * @param {string} encounterId - Encounter identifier
   * @param {object} options - Combat options
   * @returns {object} Combat creation result
   */
  createCombat(encounterId, options = {}) {
    return this.combatManager.createCombat(encounterId, options);
  }

  /**
   * Start combat
   * @param {string} encounterId - Encounter ID
   * @returns {object} Combat start result
   */
  startCombat(encounterId) {
    return this.combatManager.startCombat(encounterId);
  }

  /**
   * Add participant to combat
   * @param {string} encounterId - Encounter ID
   * @param {string} characterId - Character ID
   * @param {number} initiative - Initiative score
   * @param {object} options - Additional options
   * @returns {object} Participant addition result
   */
  addCombatParticipant(encounterId, characterId, initiative = null, options = {}) {
    const character = this.getCharacter(characterId);
    if (!character) {
      throw new Error('Character not found');
    }

    return this.combatManager.addParticipant(encounterId, character, initiative, options);
  }

  /**
   * Perform attack in combat
   * @param {string} encounterId - Encounter ID
   * @param {string} attackerId - Attacker ID
   * @param {string} defenderId - Defender ID
   * @param {object} options - Attack options
   * @returns {object} Attack result
   */
  performAttack(encounterId, attackerId, defenderId, options = {}) {
    return this.combatManager.performAttack(encounterId, attackerId, defenderId, options);
  }

  /**
   * Cast spell
   * @param {string} characterId - Character ID
   * @param {string} spellName - Spell name
   * @param {object} options - Casting options
   * @returns {object} Spell casting result
   */
  async castSpell(characterId, spellName, options = {}) {
    const character = this.getCharacter(characterId);
    if (!character) {
      throw new Error('Character not found');
    }

    const { getSpell } = await import('./spells/SpellData.js');
    const spell = getSpell(spellName);

    if (!spell) {
      throw new Error('Spell not found');
    }

    return this.spellSystem.castSpell(character, spell, options);
  }

  /**
   * Apply condition to character
   * @param {string} characterId - Character ID
   * @param {string} condition - Condition to apply
   * @param {object} options - Condition options
   * @returns {object} Condition application result
   */
  applyCondition(characterId, condition, options = {}) {
    const character = this.getCharacter(characterId);
    if (!character) {
      throw new Error('Character not found');
    }

    return this.conditionSystem.applyCondition(character, condition, options);
  }

  /**
   * Remove condition from character
   * @param {string} characterId - Character ID
   * @param {string} condition - Condition to remove
   * @param {object} options - Removal options
   * @returns {object} Condition removal result
   */
  removeCondition(characterId, condition, options = {}) {
    const character = this.getCharacter(characterId);
    if (!character) {
      throw new Error('Character not found');
    }

    return this.conditionSystem.removeCondition(character, condition, options);
  }

  /**
   * Roll dice
   * @param {string} expression - Dice expression
   * @returns {object} Roll result
   */
  rollDice(expression) {
    return DiceRoller.rollExpression(expression);
  }

  /**
   * Roll d20
   * @param {number} advantage - Advantage state
   * @returns {object} Roll result
   */
  rollD20(advantage = 0) {
    return DiceRoller.rollD20(advantage);
  }

  /**
   * Get engine statistics
   * @returns {object} Engine statistics
   */
  getStats() {
    return {
      characters: this.characters.size,
      activeCombats: this.combatManager.combatEncounters.size,
      activeConditions: this.conditionSystem.activeConditions.size,
      activeSpells: this.spellSystem.concentrationSpells.size,
      version: '1.0.0'
    };
  }

  /**
   * Validate character data
   * @param {string} characterId - Character ID
   * @returns {object} Validation result
   */
  validateCharacter(characterId) {
    const character = this.getCharacter(characterId);
    if (!character) {
      throw new Error('Character not found');
    }

    return this.ruleEngine.validateCharacter(character);
  }
}

// Export main classes and utilities
export {
  Character,
  RuleEngine,
  CombatManager,
  SpellSystem,
  ConditionSystem,
  CharacterFeatures,
  DiceRoller,
  ABILITIES,
  SKILLS,
  CONDITIONS,
  DAMAGE_TYPES
};

// Export default engine
export default DnD5eRuleEngine;