/**
 * API Integration Tests
 */

import request from 'supertest';
import app from '../src/api/server.js';

describe('API Endpoints', () => {
  let characterId;
  let combatId;

  describe('Health Check', () => {
    test('GET /api/health should return health status', async () => {
      const response = await request(app)
        .get('/api/health')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.status).toBe('healthy');
      expect(response.body.systems.ruleEngine).toBe('operational');
      expect(response.body.systems.combatManager).toBe('operational');
      expect(response.body.systems.spellSystem).toBe('operational');
      expect(response.body.systems.conditionSystem).toBe('operational');
      expect(response.body.systems.characterFeatures).toBe('operational');
    });
  });

  describe('Character Management', () => {
    test('POST /api/characters should create new character', async () => {
      const characterData = {
        name: 'Test Fighter',
        class: 'fighter',
        level: 3,
        race: 'human',
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
          intimidation: { proficient: true }
        }
      };

      const response = await request(app)
        .post('/api/characters')
        .send(characterData)
        .expect(201);

      expect(response.body.success).toBe(true);
      expect(response.body.character.name).toBe('Test Fighter');
      expect(response.body.character.class).toBe('fighter');
      expect(response.body.character.level).toBe(3);
      expect(response.body.character.abilities.strength).toBe(16);
      expect(response.body.character.proficiencyBonus).toBe(2);

      characterId = response.body.character.id;
    });

    test('GET /api/characters/:id should retrieve character', async () => {
      const response = await request(app)
        .get(`/api/characters/${characterId}`)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.character.id).toBe(characterId);
      expect(response.body.character.name).toBe('Test Fighter');
    });

    test('GET /api/characters should list characters', async () => {
      const response = await request(app)
        .get('/api/characters')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(Array.isArray(response.body.characters)).toBe(true);
      expect(response.body.characters.length).toBeGreaterThan(0);
    });

    test('PUT /api/characters/:id should update character', async () => {
      const updateData = {
        hitPoints: {
          current: 35,
          maximum: 35
        }
      };

      const response = await request(app)
        .put(`/api/characters/${characterId}`)
        .send(updateData)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.character.hitPoints.current).toBe(35);
    });

    test('POST /api/characters should validate required fields', async () => {
      const invalidData = {
        name: 'Invalid Character'
        // Missing class and level
      };

      const response = await request(app)
        .post('/api/characters')
        .send(invalidData)
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toContain('Missing required fields');
    });

    test('GET /api/characters/:id should return 404 for non-existent character', async () => {
      const response = await request(app)
        .get('/api/characters/non-existent-id')
        .expect(404);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toBe('Character not found');
    });
  });

  describe('Dice Rolling', () => {
    test('POST /api/roll/dice should roll dice expression', async () => {
      const response = await request(app)
        .post('/api/roll/dice')
        .send({ expression: '2d6+3' })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.result.expression).toBe('2d6+3');
      expect(response.body.result.numDice).toBe(2);
      expect(response.body.result.dieSize).toBe(6);
      expect(response.body.result.modifier).toBe(3);
      expect(response.body.result.total).toBeGreaterThanOrEqual(5); // 2 + 3
      expect(response.body.result.total).toBeLessThanOrEqual(15); // 12 + 3
      expect(response.body.result.rolls).toHaveLength(2);
    });

    test('POST /api/roll/dice should handle complex expressions', async () => {
      const response = await request(app)
        .post('/api/roll/dice')
        .send({ expression: '4d8+2d6+5' })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.result.total).toBeGreaterThan(0);
    });

    test('POST /api/roll/dice should validate expression', async () => {
      const response = await request(app)
        .post('/api/roll/dice')
        .send({ expression: 'invalid' })
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toContain('Invalid dice expression');
    });

    test('POST /api/roll/d20 should roll d20', async () => {
      const response = await request(app)
        .post('/api/roll/d20')
        .send({ advantage: 1 })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.result.advantage).toBe(1);
      expect(response.body.result.rolls).toHaveLength(2);
      expect(response.body.result.total).toBeGreaterThanOrEqual(1);
      expect(response.body.result.total).toBeLessThanOrEqual(20);
    });

    test('POST /api/roll/d20 should handle disadvantage', async () => {
      const response = await request(app)
        .post('/api/roll/d20')
        .send({ advantage: -1 })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.result.advantage).toBe(-1);
      expect(response.body.result.rolls).toHaveLength(2);
    });
  });

  describe('Ability Checks', () => {
    test('POST /api/rolls/ability-check should perform ability check', async () => {
      const response = await request(app)
        .post('/api/rolls/ability-check')
        .send({
          characterId,
          ability: 'strength',
          dc: 15
        })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.result.type).toBe('ability_check');
      expect(response.body.result.ability).toBe('strength');
      expect(response.body.result.dc).toBe(15);
      expect(typeof response.body.result.success).toBe('boolean');
      expect(response.body.result.bonus).toBe(3); // +3 from STR 16
    });

    test('POST /api/rolls/ability-check should handle advantage', async () => {
      const response = await request(app)
        .post('/api/rolls/ability-check')
        .send({
          characterId,
          ability: 'strength',
          dc: 15,
          advantage: 1
        })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.result.roll.advantage).toBe(1);
    });

    test('POST /api/rolls/ability-check should handle bonus', async () => {
      const response = await request(app)
        .post('/api/rolls/ability-check')
        .send({
          characterId,
          ability: 'strength',
          dc: 15,
          bonus: 2
        })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.result.bonus).toBe(5); // +3 STR + 2 bonus
    });
  });

  describe('Skill Checks', () => {
    test('POST /api/rolls/skill-check should perform skill check', async () => {
      const response = await request(app)
        .post('/api/rolls/skill-check')
        .send({
          characterId,
          skill: 'athletics',
          dc: 20
        })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.result.type).toBe('skill_check');
      expect(response.body.result.skill).toBe('athletics');
      expect(response.body.result.ability).toBe('strength');
      expect(response.body.result.bonus).toBe(5); // +3 STR + 2 proficiency
    });

    test('POST /api/rolls/skill-check should handle passive checks', async () => {
      const response = await request(app)
        .post('/api/rolls/skill-check')
        .send({
          characterId,
          skill: 'perception',
          dc: 15,
          passive: true
        })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.result.passive).toBe(true);
      expect(response.body.result.total).toBe(11); // 10 + 1 WIS modifier
    });
  });

  describe('Saving Throws', () => {
    test('POST /api/rolls/saving-throw should perform saving throw', async () => {
      const response = await request(app)
        .post('/api/rolls/saving-throw')
        .send({
          characterId,
          ability: 'constitution',
          dc: 14
        })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.result.type).toBe('saving_throw');
      expect(response.body.result.ability).toBe('constitution');
      expect(typeof response.body.result.success).toBe('boolean');
    });
  });

  describe('Combat System', () => {
    let goblinCharacterId;

    beforeEach(async () => {
      // Create a goblin character for combat testing
      const goblinResponse = await request(app)
        .post('/api/characters')
        .send({
          name: 'Goblin Scout',
          class: 'commoner',
          level: 1,
          abilities: {
            dexterity: 15,
            constitution: 12,
            strength: 8
          },
          armorClass: 15,
          hitPoints: { current: 7, maximum: 7 }
        });

      goblinCharacterId = goblinResponse.body.character.id;
    });

    test('POST /api/combat/create should create combat session', async () => {
      const response = await request(app)
        .post('/api/combat/create')
        .send({
          participants: [
            { characterId, initiative: 18 },
            { characterId: goblinCharacterId, initiative: 12 }
          ],
          environment: { terrain: 'forest' }
        })
        .expect(201);

      expect(response.body.success).toBe(true);
      expect(response.body.combatId).toBeDefined();
      expect(response.body.combat.participants).toHaveLength(2);

      combatId = response.body.combatId;
    });

    test('POST /api/combat/:combatId/start should start combat', async () => {
      // First create combat
      const createResponse = await request(app)
        .post('/api/combat/create')
        .send({
          participants: [
            { characterId, initiative: 18 },
            { characterId: goblinCharacterId, initiative: 12 }
          ]
        });

      combatId = createResponse.body.combatId;

      const response = await request(app)
        .post(`/api/combat/${combatId}/start`)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.result.round).toBe(1);
      expect(response.body.result.currentTurn.character.name).toBe('Test Fighter');
    });

    test('GET /api/combat/:combatId/state should return combat state', async () => {
      // Create and start combat first
      const createResponse = await request(app)
        .post('/api/combat/create')
        .send({
          participants: [
            { characterId, initiative: 18 },
            { characterId: goblinCharacterId, initiative: 12 }
          ]
        });

      combatId = createResponse.body.combatId;

      await request(app)
        .post(`/api/combat/${combatId}/start`);

      const response = await request(app)
        .get(`/api/combat/${combatId}/state`)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.state.active).toBe(true);
      expect(response.body.state.round).toBe(1);
      expect(response.body.state.participants).toHaveLength(2);
    });

    test('POST /api/combat/:combatId/attack should perform attack', async () => {
      // Create and start combat
      const createResponse = await request(app)
        .post('/api/combat/create')
        .send({
          participants: [
            { characterId, initiative: 18 },
            { characterId: goblinCharacterId, initiative: 12 }
          ]
        });

      combatId = createResponse.body.combatId;
      await request(app).post(`/api/combat/${combatId}/start`);

      const response = await request(app)
        .post(`/api/combat/${combatId}/attack`)
        .send({
          attackerId: characterId,
          defenderId: goblinCharacterId,
          options: {
            attackType: 'melee',
            damageExpression: '1d8+3',
            damageType: 'slashing'
          }
        })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.result.type).toBe('combat_attack');
      expect(response.body.result.attacker).toBe('Test Fighter');
      expect(response.body.result.defender).toBe('Goblin Scout');
      expect(response.body.result.attack).toBeDefined();
    });

    test('POST /api/combat/:combatId/next-turn should advance turn', async () => {
      // Create and start combat
      const createResponse = await request(app)
        .post('/api/combat/create')
        .send({
          participants: [
            { characterId, initiative: 18 },
            { characterId: goblinCharacterId, initiative: 12 }
          ]
        });

      combatId = createResponse.body.combatId;
      await request(app).post(`/api/combat/${combatId}/start`);

      const response = await request(app)
        .post(`/api/combat/${combatId}/next-turn`)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.result.currentTurn.character.name).toBe('Goblin Scout');
    });

    test('POST /api/combat/:combatId/end should end combat', async () => {
      // Create combat
      const createResponse = await request(app)
        .post('/api/combat/create')
        .send({
          participants: [
            { characterId, initiative: 18 },
            { characterId: goblinCharacterId, initiative: 12 }
          ]
        });

      combatId = createResponse.body.combatId;

      const response = await request(app)
        .post(`/api/combat/${combatId}/end`)
        .send({ reason: 'test_complete' })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.summary.reason).toBe('test_complete');
      expect(response.body.summary.participants).toHaveLength(2);
    });
  });

  describe('Spell System', () => {
    test('POST /api/spells/cast should cast spell', async () => {
      // Create a wizard character for spell testing
      const wizardResponse = await request(app)
        .post('/api/characters')
        .send({
          name: 'Test Wizard',
          class: 'wizard',
          level: 5,
          abilities: {
            intelligence: 18,
            constitution: 14
          },
          spellcasting: {
            ability: 'intelligence',
            level: 5,
            class: 'wizard'
          }
        });

      const wizardId = wizardResponse.body.character.id;

      const response = await request(app)
        .post('/api/spells/cast')
        .send({
          characterId: wizardId,
          spellName: 'fire bolt'
        })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.result.spell).toBe('Fire Bolt');
      expect(response.body.result.level).toBe(0); // Cantrip
      expect(response.body.result.spellSlotUsed).toBe(false);
    });

    test('GET /api/spells/search should find spells', async () => {
      const response = await request(app)
        .get('/api/spells/search?query=fire')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(Array.isArray(response.body.results)).toBe(true);
      expect(response.body.results.length).toBeGreaterThan(0);
      expect(response.body.results.some(spell => spell.name.includes('fire'))).toBe(true);
    });

    test('GET /api/spells/by-level/:level should get spells by level', async () => {
      const response = await request(app)
        .get('/api/spells/by-level/1')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(Array.isArray(response.body.spells)).toBe(true);
      expect(response.body.spells.every(spell => spell.level === 1)).toBe(true);
    });
  });

  describe('Condition System', () => {
    test('POST /api/conditions/apply should apply condition', async () => {
      const response = await request(app)
        .post('/api/conditions/apply')
        .send({
          characterId,
          condition: 'prone',
          options: { source: 'test' }
        })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.result.condition).toBe('prone');
      expect(response.body.result.character).toBe('Test Fighter');
    });

    test('DELETE /api/conditions/:characterId/:condition should remove condition', async () => {
      // First apply a condition
      await request(app)
        .post('/api/conditions/apply')
        .send({
          characterId,
          condition: 'frightened'
        });

      const response = await request(app)
        .delete(`/api/conditions/${characterId}/frightened`)
        .query({ reason: 'test_removal' })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.result.condition).toBe('frightened');
      expect(response.body.result.reason).toBe('test_removal');
    });

    test('GET /api/conditions/:characterId should list conditions', async () => {
      // Apply some conditions first
      await request(app)
        .post('/api/conditions/apply')
        .send({ characterId, condition: 'poisoned' });

      const response = await request(app)
        .get(`/api/conditions/${characterId}`)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(Array.isArray(response.body.conditions)).toBe(true);
      expect(response.body.conditions.length).toBeGreaterThan(0);
      expect(response.body.conditions[0].name).toBe('poisoned');
      expect(response.body.conditions[0].effects).toBeDefined();
    });
  });

  describe('Error Handling', () => {
    test('should handle 404 for unknown endpoints', async () => {
      const response = await request(app)
        .get('/api/unknown-endpoint')
        .expect(404);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toBe('Endpoint not found');
    });

    test('should handle invalid JSON', async () => {
      const response = await request(app)
        .post('/api/characters')
        .set('Content-Type', 'application/json')
        .send('invalid json')
        .expect(400);

      expect(response.body.success).toBe(false);
    });
  });

  describe('Character Validation', () => {
    test('GET /api/validate/character/:id should validate character', async () => {
      const response = await request(app)
        .get(`/api/validate/character/${characterId}`)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.validation.valid).toBe(true);
      expect(Array.isArray(response.body.validation.errors)).toBe(true);
      expect(Array.isArray(response.body.validation.warnings)).toBe(true);
    });
  });
});