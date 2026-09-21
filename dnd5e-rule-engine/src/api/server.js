/**
 * D&D 5e Rule Engine API Server
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import dotenv from 'dotenv';
import { v4 as uuidv4 } from 'uuid';

import RuleEngine from '../core/RuleEngine.js';
import CombatManager from '../combat/CombatManager.js';
import SpellSystem from '../spells/SpellSystem.js';
import ConditionSystem from '../conditions/ConditionSystem.js';
import CharacterFeatures from '../features/CharacterFeatures.js';
import { Character } from '../types/index.js';

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json({ limit: '10mb' }));

// Initialize rule engine systems
const ruleEngine = new RuleEngine();
const combatManager = new CombatManager(ruleEngine);
const spellSystem = new SpellSystem();
const conditionSystem = new ConditionSystem();
const characterFeatures = new CharacterFeatures();

// In-memory character storage (in production, use a database)
const characters = new Map();
const combatSessions = new Map();

// Character management endpoints
app.post('/api/characters', (req, res) => {
  try {
    const characterData = {
      id: uuidv4(),
      ...req.body
    };

    const character = new Character(characterData);

    // Apply character features if provided
    if (characterData.class) {
      characterFeatures.applyClassFeatures(
        character,
        characterData.class,
        characterData.level || 1,
        characterData.choices || {}
      );
    }

    if (characterData.race) {
      characterFeatures.applyRacialTraits(
        character,
        characterData.race,
        characterData.racialChoices || {}
      );
    }

    // Apply feats if provided
    if (characterData.feats) {
      characterData.feats.forEach(feat => {
        characterFeatures.applyFeat(character, feat.name, feat.choices || {});
      });
    }

    // Initialize spell slots if character can cast spells
    if (characterData.spellcasting) {
      spellSystem.initializeSpellSlots(character.id, characterData.spellcasting);
    }

    characters.set(character.id, character);

    res.status(201).json({
      success: true,
      character: {
        id: character.id,
        name: character.name,
        class: character.class,
        level: character.level,
        race: character.race,
        abilities: character.abilities,
        skills: character.skills,
        proficiencyBonus: character.proficiencyBonus,
        armorClass: character.armorClass,
        hitPoints: character.hitPoints,
        conditions: character.conditions,
        features: character.features || [],
        feats: character.feats || []
      }
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

app.get('/api/characters/:id', (req, res) => {
  const character = characters.get(req.params.id);
  if (!character) {
    return res.status(404).json({
      success: false,
      error: 'Character not found'
    });
  }

  res.json({
    success: true,
    character: {
      id: character.id,
      name: character.name,
      class: character.class,
      level: character.level,
      race: character.race,
      abilities: character.abilities,
      skills: character.skills,
      proficiencyBonus: character.proficiencyBonus,
      armorClass: character.armorClass,
      hitPoints: character.hitPoints,
      conditions: character.conditions,
      features: character.features || [],
      feats: character.feats || [],
      spellSlots: spellSystem.getSpellSlots(character.id)
    }
  });
});

app.put('/api/characters/:id', (req, res) => {
  const character = characters.get(req.params.id);
  if (!character) {
    return res.status(404).json({
      success: false,
      error: 'Character not found'
    });
  }

  try {
    // Update character properties
    Object.assign(character, req.body);

    res.json({
      success: true,
      character: {
        id: character.id,
        name: character.name,
        abilities: character.abilities,
        hitPoints: character.hitPoints,
        conditions: character.conditions
      }
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// Ability checks endpoints
app.post('/api/rolls/ability-check', (req, res) => {
  try {
    const { characterId, ability, dc, advantage = 0, bonus = 0 } = req.body;

    const character = characters.get(characterId);
    if (!character) {
      return res.status(404).json({
        success: false,
        error: 'Character not found'
      });
    }

    const result = ruleEngine.abilityCheck(character, ability, dc, advantage, bonus);

    res.json({
      success: true,
      result
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/rolls/skill-check', (req, res) => {
  try {
    const { characterId, skill, dc, advantage = 0, bonus = 0, passive = false } = req.body;

    const character = characters.get(characterId);
    if (!character) {
      return res.status(404).json({
        success: false,
        error: 'Character not found'
      });
    }

    // Import SkillChecks dynamically
    const { SkillChecks } = await import('../mechanics/SkillChecks.js');
    let result;

    if (passive) {
      result = SkillChecks.performCheck(character, skill, dc, { passive });
    } else {
      result = SkillChecks.performCheck(character, skill, dc, { advantage, bonus });
    }

    res.json({
      success: true,
      result
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/rolls/saving-throw', (req, res) => {
  try {
    const { characterId, ability, dc, advantage = 0, bonus = 0, damageType = null } = req.body;

    const character = characters.get(characterId);
    if (!character) {
      return res.status(404).json({
        success: false,
        error: 'Character not found'
      });
    }

    // Import SavingThrows dynamically
    const { SavingThrows } = await import('../mechanics/SavingThrows.js');
    const result = SavingThrows.performSave(character, ability, dc, { advantage, bonus, damageType });

    res.json({
      success: true,
      result
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// Combat endpoints
app.post('/api/combat/create', (req, res) => {
  try {
    const { participants, environment = {}, rules = {} } = req.body;
    const combatId = uuidv4();

    const combat = combatManager.createCombat(combatId, { environment, rules });

    // Add participants to combat
    participants.forEach(participant => {
      const character = characters.get(participant.characterId);
      if (character) {
        combatManager.addParticipant(combatId, character, participant.initiative, participant.options || {});
      }
    });

    combatSessions.set(combatId, combat);

    res.status(201).json({
      success: true,
      combatId,
      participants: combat.participants.map(p => ({
        characterId: p.id,
        name: p.character.name,
        initiative: p.initiative
      }))
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/combat/:combatId/start', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const result = combatManager.startCombat(combatId);

    res.json({
      success: true,
      result
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

app.get('/api/combat/:combatId/state', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const state = combatManager.getCombatState(combatId);

    if (!state) {
      return res.status(404).json({
        success: false,
        error: 'Combat not found'
      });
    }

    res.json({
      success: true,
      state
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/combat/:combatId/attack', (req, res) => {
  try {
    const { combatId } = req.params;
    const { attackerId, defenderId, options = {} } = req.body;

    const result = combatManager.performAttack(combatId, attackerId, defenderId, options);

    res.json({
      success: true,
      result
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/combat/:combatId/next-turn', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const result = combatManager.nextTurn(combatId);

    res.json({
      success: true,
      result
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/combat/:combatId/end', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const { reason = 'combat_complete' } = req.body;

    const summary = combatManager.endCombat(combatId, reason);
    combatSessions.delete(combatId);

    res.json({
      success: true,
      summary
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// Spell endpoints
app.post('/api/spells/cast', (req, res) => {
  try {
    const { characterId, spellName, options = {} } = req.body;

    const character = characters.get(characterId);
    if (!character) {
      return res.status(404).json({
        success: false,
        error: 'Character not found'
      });
    }

    // Import spell data
    const { getSpell } = await import('../spells/SpellData.js');
    const spell = getSpell(spellName);

    if (!spell) {
      return res.status(404).json({
        success: false,
        error: 'Spell not found'
      });
    }

    const result = spellSystem.castSpell(character, spell, options);

    res.json({
      success: true,
      result
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

app.get('/api/spells/search', async (req, res) => {
  try {
    const { query } = req.query;

    if (!query) {
      return res.status(400).json({
        success: false,
        error: 'Search query required'
      });
    }

    const { searchSpells } = await import('../spells/SpellData.js');
    const results = searchSpells(query);

    res.json({
      success: true,
      results
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

app.get('/api/spells/by-level/:level', async (req, res) => {
  try {
    const level = parseInt(req.params.level);

    const { getSpellsByLevel } = await import('../spells/SpellData.js');
    const spells = getSpellsByLevel(level);

    res.json({
      success: true,
      spells
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// Condition endpoints
app.post('/api/conditions/apply', (req, res) => {
  try {
    const { characterId, condition, options = {} } = req.body;

    const character = characters.get(characterId);
    if (!character) {
      return res.status(404).json({
        success: false,
        error: 'Character not found'
      });
    }

    const result = conditionSystem.applyCondition(character, condition, options);

    res.json({
      success: true,
      result
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

app.delete('/api/conditions/:characterId/:condition', (req, res) => {
  try {
    const { characterId, condition } = req.params;
    const { reason = 'manual' } = req.query;

    const character = characters.get(characterId);
    if (!character) {
      return res.status(404).json({
        success: false,
        error: 'Character not found'
      });
    }

    const result = conditionSystem.removeCondition(character, condition, { reason });

    res.json({
      success: true,
      result
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

app.get('/api/conditions/:characterId', (req, res) => {
  try {
    const { characterId } = req.params;
    const conditions = conditionSystem.getCharacterConditions(characterId);

    const conditionDetails = conditions.map(condition => ({
      name: condition,
      effects: conditionSystem.getConditionEffects(condition)
    }));

    res.json({
      success: true,
      conditions: conditionDetails
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// Character features endpoints
app.post('/api/characters/:characterId/apply-class', (req, res) => {
  try {
    const { characterId } = req.params;
    const { className, level, choices = {} } = req.body;

    const character = characters.get(characterId);
    if (!character) {
      return res.status(404).json({
        success: false,
        error: 'Character not found'
      });
    }

    characterFeatures.applyClassFeatures(character, className, level, choices);

    res.json({
      success: true,
      character: {
        id: character.id,
        name: character.name,
        class: character.class,
        level: character.level,
        features: character.features || []
      }
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/characters/:characterId/apply-feat', (req, res) => {
  try {
    const { characterId } = req.params;
    const { featName, choices = {} } = req.body;

    const character = characters.get(characterId);
    if (!character) {
      return res.status(404).json({
        success: false,
        error: 'Character not found'
      });
    }

    characterFeatures.applyFeat(character, featName, choices);

    res.json({
      success: true,
      character: {
        id: character.id,
        name: character.name,
        feats: character.feats || []
      }
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// Utility endpoints
app.post('/api/roll/dice', (req, res) => {
  try {
    const { expression } = req.body;

    if (!expression) {
      return res.status(400).json({
        success: false,
        error: 'Dice expression required'
      });
    }

    // Import DiceRoller dynamically
    const { DiceRoller } = await import('../core/DiceRoller.js');
    const result = DiceRoller.rollExpression(expression);

    res.json({
      success: true,
      result
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/roll/d20', (req, res) => {
  try {
    const { advantage = 0 } = req.body;

    // Import DiceRoller dynamically
    const { DiceRoller } = await import('../core/DiceRoller.js');
    const result = DiceRoller.rollD20(advantage);

    res.json({
      success: true,
      result
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

app.get('/api/validate/character/:id', (req, res) => {
  try {
    const character = characters.get(req.params.id);
    if (!character) {
      return res.status(404).json({
        success: false,
        error: 'Character not found'
      });
    }

    const validation = ruleEngine.validateCharacter(character);

    res.json({
      success: true,
      validation
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    success: true,
    status: 'healthy',
    timestamp: new Date().toISOString(),
    systems: {
      ruleEngine: 'operational',
      combatManager: 'operational',
      spellSystem: 'operational',
      conditionSystem: 'operational',
      characterFeatures: 'operational'
    }
  });
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('API Error:', error);
  res.status(500).json({
    success: false,
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong'
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found'
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`D&D 5e Rule Engine API running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/api/health`);
});

export default app;