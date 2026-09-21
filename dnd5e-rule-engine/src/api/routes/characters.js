/**
 * Character API Routes
 */

import express from 'express';
import { Character } from '../../types/index.js';
import CharacterFeatures from '../../features/CharacterFeatures.js';
import SpellSystem from '../../spells/SpellSystem.js';

const router = express.Router();
const characterFeatures = new CharacterFeatures();
const spellSystem = new SpellSystem();

// In-memory character storage (in production, use database)
const characters = new Map();

// GET /api/characters - List all characters
router.get('/', (req, res) => {
  const { search, class: className, race, minLevel, maxLevel } = req.query;

  let characterList = Array.from(characters.values());

  // Apply filters
  if (search) {
    characterList = characterList.filter(char =>
      char.name.toLowerCase().includes(search.toLowerCase())
    );
  }

  if (className) {
    characterList = characterList.filter(char => char.class === className);
  }

  if (race) {
    characterList = characterList.filter(char => char.race === race);
  }

  if (minLevel) {
    characterList = characterList.filter(char => char.level >= parseInt(minLevel));
  }

  if (maxLevel) {
    characterList = characterList.filter(char => char.level <= parseInt(maxLevel));
  }

  res.json({
    success: true,
    characters: characterList.map(char => ({
      id: char.id,
      name: char.name,
      class: char.class,
      level: char.level,
      race: char.race,
      armorClass: char.armorClass,
      maxHP: char.hitPoints.maximum,
      currentHP: char.hitPoints.current,
      conditions: char.conditions.length
    }))
  });
});

// POST /api/characters - Create new character
router.post('/', (req, res) => {
  try {
    const characterData = {
      id: require('uuid').v4(),
      ...req.body
    };

    // Validate required fields
    const required = ['name', 'class', 'level'];
    const missing = required.filter(field => !characterData[field]);
    if (missing.length > 0) {
      return res.status(400).json({
        success: false,
        error: `Missing required fields: ${missing.join(', ')}`
      });
    }

    const character = new Character(characterData);

    // Apply class features
    if (characterData.class) {
      characterFeatures.applyClassFeatures(
        character,
        characterData.class,
        characterData.level || 1,
        characterData.choices || {}
      );
    }

    // Apply racial traits
    if (characterData.race) {
      characterFeatures.applyRacialTraits(
        character,
        characterData.race,
        characterData.racialChoices || {}
      );
    }

    // Apply feats
    if (characterData.feats) {
      characterData.feats.forEach(feat => {
        characterFeatures.applyFeat(character, feat.name, feat.choices || {});
      });
    }

    // Initialize spell slots
    if (characterData.spellcasting) {
      spellSystem.initializeSpellSlots(character.id, characterData.spellcasting);
    }

    characters.set(character.id, character);

    res.status(201).json({
      success: true,
      character: formatCharacterResponse(character)
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// GET /api/characters/:id - Get specific character
router.get('/:id', (req, res) => {
  const character = characters.get(req.params.id);

  if (!character) {
    return res.status(404).json({
      success: false,
      error: 'Character not found'
    });
  }

  res.json({
    success: true,
    character: formatCharacterResponse(character)
  });
});

// PUT /api/characters/:id - Update character
router.put('/:id', (req, res) => {
  const character = characters.get(req.params.id);

  if (!character) {
    return res.status(404).json({
      success: false,
      error: 'Character not found'
    });
  }

  try {
    // Validate updates
    const allowedUpdates = ['name', 'abilities', 'hitPoints', 'armorClass', 'conditions'];
    const updates = Object.keys(req.body);
    const invalidUpdates = updates.filter(key => !allowedUpdates.includes(key));

    if (invalidUpdates.length > 0) {
      return res.status(400).json({
        success: false,
        error: `Invalid updates: ${invalidUpdates.join(', ')}`
      });
    }

    // Apply updates
    Object.assign(character, req.body);

    res.json({
      success: true,
      character: formatCharacterResponse(character)
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// DELETE /api/characters/:id - Delete character
router.delete('/:id', (req, res) => {
  const character = characters.get(req.params.id);

  if (!character) {
    return res.status(404).json({
      success: false,
      error: 'Character not found'
    });
  }

  characters.delete(req.params.id);

  res.json({
    success: true,
    message: 'Character deleted successfully'
  });
});

// POST /api/characters/:id/rest/short - Short rest
router.post('/:id/rest/short', (req, res) => {
  const character = characters.get(req.params.id);

  if (!character) {
    return res.status(404).json({
      success: false,
      error: 'Character not found'
    });
  }

  try {
    // Restore hit points (if character has relevant features)
    let hpRestored = 0;
    if (character.features?.some(f => f.name === 'Second Wind')) {
      // This would be handled by character features system
    }

    // Restore spell slots for relevant classes (warlock, etc.)
    // This would be handled by spell system

    // Reset other short rest resources
    character.features?.forEach(feature => {
      if (feature.uses === 'shortRest') {
        feature.used = false;
      }
    });

    res.json({
      success: true,
      result: {
        hpRestored,
        spellSlotsRestored: [], // Would be calculated
        featuresReset: character.features?.filter(f => f.uses === 'shortRest') || []
      }
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// POST /api/characters/:id/rest/long - Long rest
router.post('/:id/rest/long', (req, res) => {
  const character = characters.get(req.params.id);

  if (!character) {
    return res.status(404).json({
      success: false,
      error: 'Character not found'
    });
  }

  try {
    // Restore all hit points
    const hpRestored = character.hitPoints.maximum - character.hitPoints.current;
    character.hitPoints.current = character.hitPoints.maximum;

    // Reduce exhaustion level by 1
    let exhaustionReduced = 0;
    if (character.exhaustionLevel > 0) {
      character.exhaustionLevel--;
      exhaustionReduced = 1;
      if (character.exhaustionLevel === 0) {
        character.removeCondition('exhaustion');
      }
    }

    // Restore spell slots
    spellSystem.restoreSpellSlots(character.id);

    // Reset long rest resources
    character.features?.forEach(feature => {
      if (feature.uses === 'longRest' || feature.uses === 'oncePerDay') {
        feature.used = false;
      }
    });

    res.json({
      success: true,
      result: {
        hpRestored,
        exhaustionReduced,
        spellSlotsRestored: spellSystem.getSpellSlots(character.id),
        featuresReset: character.features?.filter(f =>
          f.uses === 'longRest' || f.uses === 'oncePerDay'
        ) || []
      }
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// POST /api/characters/:id/level-up - Level up character
router.post('/:id/level-up', (req, res) => {
  const character = characters.get(req.params.id);

  if (!character) {
    return res.status(404).json({
      success: false,
      error: 'Character not found'
    });
  }

  try {
    const { choices = {} } = req.body;
    const oldLevel = character.level;
    character.level++;
    character.proficiencyBonus = Math.ceil(character.level / 4) + 1;

    // Apply new class features for the new level
    characterFeatures.applyClassFeatures(
      character,
      character.class,
      character.level,
      choices
    );

    res.json({
      success: true,
      result: {
        oldLevel,
        newLevel: character.level,
        newProficiencyBonus: character.proficiencyBonus,
        newFeatures: character.features?.filter(f =>
          f.level === character.level
        ) || []
      }
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// POST /api/characters/:id/damage - Apply damage to character
router.post('/:id/damage', (req, res) => {
  const character = characters.get(req.params.id);

  if (!character) {
    return res.status(404).json({
      success: false,
      error: 'Character not found'
    });
  }

  try {
    const { amount, damageType, critical = false } = req.body;

    if (typeof amount !== 'number' || amount < 0) {
      return res.status(400).json({
        success: false,
        error: 'Damage amount must be a non-negative number'
      });
    }

    const originalHP = character.hitPoints.current;
    const originalTempHP = character.hitPoints.temporary;

    character.takeDamage(amount);

    res.json({
      success: true,
      result: {
        damage: amount,
        damageType,
        critical,
        originalHP,
        newHP: character.hitPoints.current,
        originalTempHP,
        newTempHP: character.hitPoints.temporary,
        damageTaken: originalHP - character.hitPoints.current,
        tempHPConsumed: originalTempHP - character.hitPoints.temporary
      }
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// POST /api/characters/:id/heal - Heal character
router.post('/:id/heal', (req, res) => {
  const character = characters.get(req.params.id);

  if (!character) {
    return res.status(404).json({
      success: false,
      error: 'Character not found'
    });
  }

  try {
    const { amount } = req.body;

    if (typeof amount !== 'number' || amount < 0) {
      return res.status(400).json({
        success: false,
        error: 'Heal amount must be a non-negative number'
      });
    }

    const originalHP = character.hitPoints.current;
    character.heal(amount);

    res.json({
      success: true,
      result: {
        healAmount: amount,
        originalHP,
        newHP: character.hitPoints.current,
        actualHealing: character.hitPoints.current - originalHP
      }
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// GET /api/characters/:id/stats - Get character statistics
router.get('/:id/stats', (req, res) => {
  const character = characters.get(req.params.id);

  if (!character) {
    return res.status(404).json({
      success: false,
      error: 'Character not found'
    });
  }

  try {
    // Calculate character statistics
    const stats = {
      abilities: Object.entries(character.abilities).map(([name, score]) => ({
        name,
        score,
        modifier: Math.floor((score - 10) / 2)
      })),
      skills: Object.entries(character.skills || {}).map(([name, data]) => ({
        name,
        proficient: data.proficient || false,
        expertise: data.expertise || false,
        bonus: character.getSkillBonus(name)
      })),
      savingThrows: Object.values(character.abilities).map((_, index) => {
        const ability = Object.keys(character.abilities)[index];
        return {
          ability,
          proficient: character.savingThrowProficiencies?.includes(ability) || false,
          bonus: character.getAbilityModifier(ability) +
                 (character.savingThrowProficiencies?.includes(ability) ? character.proficiencyBonus : 0)
        };
      }),
      combat: {
        armorClass: character.armorClass,
        initiative: character.getAbilityModifier('dexterity'),
        speed: character.speed,
        hitPoints: character.hitPoints,
        conditions: character.conditions
      },
      spellcasting: spellSystem.getSpellSlots(character.id)
    };

    res.json({
      success: true,
      stats
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Format character for API response
 */
function formatCharacterResponse(character) {
  return {
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
    spellSlots: spellSystem.getSpellSlots(character.id),
    spellcasting: character.spellcasting
  };
}

export default router;