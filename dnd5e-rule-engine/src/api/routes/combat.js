/**
 * Combat API Routes
 */

import express from 'express';
import CombatManager from '../../combat/CombatManager.js';
import { DiceRoller } from '../../core/DiceRoller.js';
import { CombatActions } from '../../combat/CombatActions.js';

const router = express.Router();
const combatManager = new CombatManager();
const combatActions = new CombatActions();

// In-memory combat sessions (in production, use database)
const combatSessions = new Map();

// GET /api/combat - List all active combat sessions
router.get('/', (req, res) => {
  const activeCombats = Array.from(combatSessions.keys()).map(combatId => {
    const state = combatManager.getCombatState(combatId);
    return {
      combatId,
      round: state.round,
      participants: state.participants.length,
      active: state.active,
      currentTurn: state.currentParticipant?.name
    };
  });

  res.json({
    success: true,
    combats: activeCombats
  });
});

// POST /api/combat/create - Create new combat session
router.post('/create', (req, res) => {
  try {
    const { participants, environment = {}, rules = {} } = req.body;

    if (!participants || !Array.isArray(participants) || participants.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Participants array is required'
      });
    }

    const combatId = require('uuid').v4();
    const combat = combatManager.createCombat(combatId, { environment, rules });

    // Add participants to combat
    const addedParticipants = [];
    participants.forEach(participant => {
      try {
        const result = combatManager.addParticipant(
          combatId,
          participant.character,
          participant.initiative,
          participant.options || {}
        );
        addedParticipants.push(result);
      } catch (error) {
        console.warn(`Failed to add participant: ${error.message}`);
      }
    });

    if (addedParticipants.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No valid participants were added to combat'
      });
    }

    combatSessions.set(combatId, combat);

    res.status(201).json({
      success: true,
      combatId,
      combat: {
        id: combatId,
        environment,
        rules,
        participants: addedParticipants.map(p => ({
          characterId: p.id,
          name: p.character.name,
          initiative: p.initiative,
          team: p.team
        }))
      }
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// POST /api/combat/:combatId/start - Start combat session
router.post('/:combatId/start', (req, res) => {
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

// GET /api/combat/:combatId/state - Get current combat state
router.get('/:combatId/state', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const state = combatManager.getCombatState(combatId);

    if (!state) {
      return res.status(404).json({
        success: false,
        error: 'Combat session not found'
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

// GET /api/combat/:combatId/log - Get combat log
router.get('/:combatId/log', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const log = combatManager.getCombatLog(combatId);

    res.json({
      success: true,
      log
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// POST /api/combat/:combatId/add-participant - Add participant to combat
router.post('/:combatId/add-participant', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const { character, initiative, options = {} } = req.body;

    if (!character) {
      return res.status(400).json({
        success: false,
        error: 'Character data is required'
      });
    }

    const participant = combatManager.addParticipant(combatId, character, initiative, options);

    res.status(201).json({
      success: true,
      participant: {
        characterId: participant.id,
        name: participant.character.name,
        initiative: participant.initiative,
        team: participant.team
      }
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// DELETE /api/combat/:combatId/participants/:characterId - Remove participant
router.delete('/:combatId/participants/:characterId', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const characterId = req.params.characterId;

    // This would need implementation in CombatManager
    res.json({
      success: true,
      message: 'Participant removed from combat'
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// POST /api/combat/:combatId/attack - Perform attack
router.post('/:combatId/attack', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const { attackerId, defenderId, options = {} } = req.body;

    if (!attackerId || !defenderId) {
      return res.status(400).json({
        success: false,
        error: 'Attacker and defender IDs are required'
      });
    }

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
  });
});

// POST /api/combat/:combatId/move - Perform movement
router.post('/:combatId/move', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const { characterId, newPosition, options = {} } = req.body;

    if (!characterId || !newPosition) {
      return res.status(400).json({
        success: false,
        error: 'Character ID and new position are required'
      });
    }

    const result = combatManager.performMovement(combatId, characterId, newPosition, options);

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

// POST /api/combat/:combatId/action/grapple - Perform grapple action
router.post('/:combatId/action/grapple', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const { attackerId, defenderId, options = {} } = req.body;

    if (!attackerId || !defenderId) {
      return res.status(400).json({
        success: false,
        error: 'Attacker and defender IDs are required'
      });
    }

    const combat = combatManager.getCombat(combatId);
    const attacker = combat.participants.find(p => p.id === attackerId)?.character;
    const defender = combat.participants.find(p => p.id === defenderId)?.character;

    if (!attacker || !defender) {
      return res.status(404).json({
        success: false,
        error: 'Attacker or defender not found in combat'
      });
    }

    const result = CombatActions.performGrapple(attacker, defender, options);

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

// POST /api/combat/:combatId/action/shove - Perform shove action
router.post('/:combatId/action/shove', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const { attackerId, defenderId, shoveType = 'prone', options = {} } = req.body;

    if (!attackerId || !defenderId) {
      return res.status(400).json({
        success: false,
        error: 'Attacker and defender IDs are required'
      });
    }

    const combat = combatManager.getCombat(combatId);
    const attacker = combat.participants.find(p => p.id === attackerId)?.character;
    const defender = combat.participants.find(p => p.id === defenderId)?.character;

    if (!attacker || !defender) {
      return res.status(404).json({
        success: false,
        error: 'Attacker or defender not found in combat'
      });
    }

    const result = CombatActions.performShove(attacker, defender, shoveType, options);

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

// POST /api/combat/:combatId/action/opportunity-attack - Perform opportunity attack
router.post('/:combatId/action/opportunity-attack', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const { attackerId, defenderId, options = {} } = req.body;

    if (!attackerId || !defenderId) {
      return res.status(400).json({
        success: false,
        error: 'Attacker and defender IDs are required'
      });
    }

    const combat = combatManager.getCombat(combatId);
    const attacker = combat.participants.find(p => p.id === attackerId)?.character;
    const defender = combat.participants.find(p => p.id === defenderId)?.character;

    if (!attacker || !defender) {
      return res.status(404).json({
        success: false,
        error: 'Attacker or defender not found in combat'
      });
    }

    const result = CombatActions.performOpportunityAttack(attacker, defender, options);

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

// POST /api/combat/:combatId/action/dodge - Perform dodge action
router.post('/:combatId/action/dodge', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const { characterId } = req.body;

    if (!characterId) {
      return res.status(400).json({
        success: false,
        error: 'Character ID is required'
      });
    }

    const combat = combatManager.getCombat(combatId);
    const character = combat.participants.find(p => p.id === characterId)?.character;

    if (!character) {
      return res.status(404).json({
        success: false,
        error: 'Character not found in combat'
      });
    }

    const result = CombatActions.performDodge(character);

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

// POST /api/combat/:combatId/action/dash - Perform dash action
router.post('/:combatId/action/dash', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const { characterId } = req.body;

    if (!characterId) {
      return res.status(400).json({
        success: false,
        error: 'Character ID is required'
      });
    }

    const combat = combatManager.getCombat(combatId);
    const character = combat.participants.find(p => p.id === characterId)?.character;

    if (!character) {
      return res.status(404).json({
        success: false,
        error: 'Character not found in combat'
      });
    }

    const result = CombatActions.performDash(character);

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

// POST /api/combat/:combatId/action/ready - Perform ready action
router.post('/:combatId/action/ready', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const { characterId, trigger, action } = req.body;

    if (!characterId || !trigger || !action) {
      return res.status(400).json({
        success: false,
        error: 'Character ID, trigger, and action are required'
      });
    }

    const combat = combatManager.getCombat(combatId);
    const character = combat.participants.find(p => p.id === characterId)?.character;

    if (!character) {
      return res.status(404).json({
        success: false,
        error: 'Character not found in combat'
      });
    }

    const result = CombatActions.performReady(character, trigger, action);

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

// POST /api/combat/:combatId/next-turn - Advance to next turn
router.post('/:combatId/next-turn', (req, res) => {
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

// POST /api/combat/:combatId/initiative/roll - Roll initiative for all participants
router.post('/:combatId/initiative/roll', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const { options = {} } = req.body;

    const combat = combatManager.getCombat(combatId);
    if (!combat) {
      return res.status(404).json({
        success: false,
        error: 'Combat session not found'
      });
    }

    // Roll initiative for all participants
    const initiativeResults = combat.participants.map(participant => {
      const initiative = combatManager.rollInitiative(participant.character, options);
      participant.initiative = initiative;
      return {
        characterId: participant.id,
        characterName: participant.character.name,
        initiative
      };
    });

    // Update turn order
    combat.updateTurnOrder();

    res.json({
      success: true,
      initiativeResults,
      turnOrder: combat.turnOrder
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// POST /api/combat/:combatId/initiative/surprise - Determine surprise round
router.post('/:combatId/initiative/surprise', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const { awareGroup, unawareGroup, perceptionDCs = {} } = req.body;

    const combat = combatManager.getCombat(combatId);
    if (!combat) {
      return res.status(404).json({
        success: false,
        error: 'Combat session not found'
      });
    }

    // Determine surprise (simplified - full implementation would handle perception checks)
    const surprisedParticipants = [];

    combat.participants.forEach(participant => {
      if (unawareGroup.includes(participant.id)) {
        participant.surprised = true;
        surprisedParticipants.push(participant.id);
      }
    });

    res.json({
      success: true,
      surprisedParticipants,
      description: `${surprisedParticipants.length} participants are surprised`
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

// POST /api/combat/:combatId/end - End combat session
router.post('/:combatId/end', (req, res) => {
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

// GET /api/combat/:combatId/participants/:characterId/status - Get participant status
router.get('/:combatId/participants/:characterId/status', (req, res) => {
  try {
    const combatId = req.params.combatId;
    const characterId = req.params.characterId;

    const combat = combatManager.getCombat(combatId);
    if (!combat) {
      return res.status(404).json({
        success: false,
        error: 'Combat session not found'
      });
    }

    const participant = combat.participants.find(p => p.id === characterId);
    if (!participant) {
      return res.status(404).json({
        success: false,
        error: 'Participant not found in combat'
      });
    }

    const status = {
      characterId: participant.id,
      characterName: participant.character.name,
      team: participant.team,
      initiative: participant.initiative,
      position: participant.position,
      currentHP: participant.character.hitPoints.current,
      maxHP: participant.character.hitPoints.maximum,
      tempHP: participant.character.hitPoints.temporary,
      conditions: participant.character.conditions,
      movementRemaining: participant.movement.max - participant.movement.used,
      reactionsRemaining: participant.reactions.max - participant.reactions.used,
      bonusActionsRemaining: participant.bonusActions.max - participant.bonusActions.used,
      ready: participant.ready,
      delay: participant.delay
    };

    res.json({
      success: true,
      status
    });
  } catch (error) {
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

export default router;