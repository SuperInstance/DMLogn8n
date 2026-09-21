/**
 * API Integration Tests
 *
 * Validates integration between all DMlogn8n system APIs:
 * - Cross-service communication
 * - Data consistency across services
 * - Authentication and authorization
 * - Rate limiting and throttling
 * - Error handling and propagation
 * - API version compatibility
 */

const request = require('supertest')
const { TestEnvironment } = require('../../src/helpers/TestEnvironment')
const { PerformanceMonitor, testLogger } = require('../../src/utils/logger')
const { config, buildServiceUrl } = require('../../config/test-config')
const { expect } = require('chai')

describe('API Integration Tests', function() {
  this.timeout(config.timeouts.integration)

  let testEnv
  let perfMonitor
  let users = {}
  let tokens = {}
  let characters = {}
  let guilds = {}

  before(async function() {
    this.timeout(60000)

    perfMonitor = new PerformanceMonitor('api-integration')
    perfMonitor.startTimer('test-setup')

    testEnv = new TestEnvironment({
      autoStart: true,
      useInMemoryDatabases: true,
      cleanupOnExit: true
    })

    await testEnv.initialize()
    await testEnv.waitForReady()

    // Seed test data
    await testEnv.seedData('users', 10)
    await testEnv.seedData('characters', 20)
    await testEnv.seedData('guilds', 5)

    perfMonitor.endTimer('test-setup')
  })

  after(async function() {
    this.timeout(30000)

    perfMonitor.startTimer('test-cleanup')
    await testEnv.cleanup()

    const summary = perfMonitor.getSummary()
    console.log('\n=== API Integration Test Performance ===')
    console.log(JSON.stringify(summary, null, 2))

    perfMonitor.endTimer('test-cleanup')
  })

  describe('Authentication and Authorization Integration', function() {
    it('should authenticate users and provide consistent tokens across services', async function() {
      perfMonitor.startTimer('cross-service-auth')

      // Register user in main system
      const userResponse = await request(buildServiceUrl('n8n', '/api/users'))
        .post('/register')
        .send({
          username: 'integrationuser',
          email: 'integration@test.com',
          password: 'password123',
          roles: ['player']
        })
        .expect(201)

      users.integration = userResponse.body

      // Authenticate and get token
      const authResponse = await request(buildServiceUrl('n8n', '/api/auth'))
        .post('/login')
        .send({
          email: 'integration@test.com',
          password: 'password123'
        })
        .expect(200)

      tokens.integration = authResponse.body.token

      // Verify token works across all services
      const services = ['aiDialogue', 'arena', 'crafting', 'guild', 'quest', 'voice', 'weather']

      for (const service of services) {
        const response = await request(buildServiceUrl(service, '/api/auth'))
          .get('/verify')
          .set('Authorization', `Bearer ${tokens.integration}`)
          .expect(200)

        expect(response.body).to.have.property('valid', true)
        expect(response.body).to.have.property('userId')
        expect(response.body.userId).to.equal(users.integration.id)
      }

      perfMonitor.endTimer('cross-service-auth')
    })

    it('should handle role-based authorization consistently', async function() {
      perfMonitor.startTimer('role-based-authorization')

      // Create admin user
      const adminResponse = await request(buildServiceUrl('n8n', '/api/users'))
        .post('/register')
        .send({
          username: 'integrationadmin',
          email: 'admin@test.com',
          password: 'password123',
          roles: ['admin']
        })
        .expect(201)

      const adminAuthResponse = await request(buildServiceUrl('n8n', '/api/auth'))
        .post('/login')
        .send({
          email: 'admin@test.com',
          password: 'password123'
        })
        .expect(200)

      const adminToken = adminAuthResponse.body.token

      // Test admin access to restricted endpoints
      const adminEndpoints = [
        { service: 'n8n', path: '/api/admin/users' },
        { service: 'arena', path: '/api/admin/matches' },
        { service: 'guild', path: '/api/admin/guilds' }
      ]

      for (const endpoint of adminEndpoints) {
        const response = await request(buildServiceUrl(endpoint.service, endpoint.path))
          .get('/')
          .set('Authorization', `Bearer ${adminToken}`)
          .expect(200)

        expect(response.body).to.be.an('object')
      }

      // Test that regular user cannot access admin endpoints
      for (const endpoint of adminEndpoints) {
        await request(buildServiceUrl(endpoint.service, endpoint.path))
          .get('/')
          .set('Authorization', `Bearer ${tokens.integration}`)
          .expect(403)
      }

      perfMonitor.endTimer('role-based-authorization')
    })
  })

  describe('Character Data Consistency', function() {
    it('should maintain character consistency across services', async function() {
      perfMonitor.startTimer('character-consistency')

      // Create character
      const characterResponse = await request(buildServiceUrl('aiDialogue', '/api/characters'))
        .post('/')
        .set('Authorization', `Bearer ${tokens.integration}`)
        .send({
          name: 'Gandalf Stormrider',
          race: 'human',
          class: 'wizard',
          level: 10,
          abilities: {
            strength: 8,
            dexterity: 14,
            constitution: 12,
            intelligence: 18,
            wisdom: 16,
            charisma: 14
          }
        })
        .expect(201)

      characters.gandalf = characterResponse.body

      // Verify character exists in all services
      const services = ['n8n', 'aiDialogue', 'arena', 'crafting', 'guild', 'quest']

      for (const service of services) {
        const response = await request(buildServiceUrl(service, '/api/characters'))
          .get(`/${characters.gandalf.id}`)
          .set('Authorization', `Bearer ${tokens.integration}`)
          .expect(200)

        expect(response.body).to.have.property('id', characters.gandalf.id)
        expect(response.body).to.have.property('name', 'Gandalf Stormrider')
        expect(response.body).to.have.property('level', 10)
        expect(response.body.abilities).to.have.property('intelligence', 18)
      }

      perfMonitor.endTimer('character-consistency')
    })

    it('should synchronize character progression across services', async function() {
      perfMonitor.startTimer('character-progression-sync')

      // Update character level
      const updateResponse = await request(buildServiceUrl('n8n', '/api/characters'))
        .put(`/${characters.gandalf.id}`)
        .set('Authorization', `Bearer ${tokens.integration}`)
        .send({
          level: 11,
          experience: 10000,
          abilities: {
            ...characters.gandalf.abilities,
            intelligence: 19 // Level up bonus
          }
        })
        .expect(200)

      // Verify update propagated to all services
      const services = ['aiDialogue', 'arena', 'crafting', 'guild', 'quest']
      const syncPromises = services.map(service =>
        request(buildServiceUrl(service, '/api/characters'))
          .get(`/${characters.gandalf.id}`)
          .set('Authorization', `Bearer ${tokens.integration}`)
      )

      const responses = await Promise.all(syncPromises)

      for (const response of responses) {
        expect(response.body).to.have.property('level', 11)
        expect(response.body).to.have.property('experience', 10000)
        expect(response.body.abilities).to.have.property('intelligence', 19)
      }

      perfMonitor.endTimer('character-progression-sync')
    })
  })

  describe('Guild System Integration', function() {
    it('should create guild and integrate with member services', async function() {
      perfMonitor.startTimer('guild-creation-integration')

      // Create guild
      const guildResponse = await request(buildServiceUrl('guild', '/api/guilds'))
        .post('/')
        .set('Authorization', `Bearer ${tokens.integration}`)
        .send({
          name: 'Integration Test Guild',
          tag: 'ITEST',
          description: 'A guild for testing cross-service integration',
          type: 'adventuring'
        })
        .expect(201)

      guilds.testGuild = guildResponse.body

      // Verify guild exists in related services
      const arenaResponse = await request(buildServiceUrl('arena', '/api/guilds'))
        .get(`/${guilds.testGuild.id}`)
        .set('Authorization', `Bearer ${tokens.integration}`)
        .expect(200)

      expect(arenaResponse.body).to.have.property('id', guilds.testGuild.id)
      expect(arenaResponse.body).to.have.property('name', 'Integration Test Guild')

      perfMonitor.endTimer('guild-creation-integration')
    })

    it('should integrate guild membership with character services', async function() {
      perfMonitor.startTimer('guild-membership-integration')

      // Join guild with character
      const joinResponse = await request(buildServiceUrl('guild', '/api/guilds'))
        .post(`/${guilds.testGuild.id}/join`)
        .set('Authorization', `Bearer ${tokens.integration}`)
        .send({
          characterId: characters.gandalf.id
        })
        .expect(200)

      expect(joinResponse.body).to.have.property('success', true)

      // Verify character guild membership in other services
      const characterGuildResponse = await request(buildServiceUrl('arena', '/api/characters'))
        .get(`/${characters.gandalf.id}/guild`)
        .set('Authorization', `Bearer ${tokens.integration}`)
        .expect(200)

      expect(characterGuildResponse.body).to.have.property('guildId', guilds.testGuild.id)
      expect(characterGuildResponse.body).to.have.property('guildName', 'Integration Test Guild')

      perfMonitor.endTimer('guild-membership-integration')
    })
  })

  describe('Quest System Integration', function() {
    it('should generate quests based on character data', async function() {
      perfMonitor.startTimer('quest-generation-integration')

      const questRequest = {
        characterId: characters.gandalf.id,
        preferences: {
          types: ['magical', 'exploration'],
          difficulty: 'medium'
        },
        context: {
          location: 'Neverwinter',
          guildAffiliation: guilds.testGuild.id,
          recentActivities: ['completed-tutorial', 'joined-guild']
        }
      }

      const questResponse = await request(buildServiceUrl('quest', '/api/generation'))
        .post('/generate')
        .set('Authorization', `Bearer ${tokens.integration}`)
        .send(questRequest)
        .expect(200)

      expect(questResponse.body).to.have.property('id')
      expect(questResponse.body).to.have.property('title')
      expect(questResponse.body).to.have.property('objectives')
      expect(questResponse.body).to.have.property('level', 11) // Character's level

      // Assign quest to character
      const assignResponse = await request(buildServiceUrl('quest', '/api/quests'))
        .post(`/${questResponse.body.id}/assign`)
        .set('Authorization', `Bearer ${tokens.integration}`)
        .send({
          characterId: characters.gandalf.id
        })
        .expect(200)

      expect(assignResponse.body).to.have.property('assigned', true)

      perfMonitor.endTimer('quest-generation-integration')
    })

    it('should track quest progress across services', async function() {
      perfMonitor.startTimer('quest-progress-integration')

      // Get active quests
      const questsResponse = await request(buildServiceUrl('quest', '/api/quests'))
        .get('/active')
        .set('Authorization', `Bearer ${tokens.integration}`)
        .expect(200)

      expect(questsResponse.body.quests).to.be.an('array')
      expect(questsResponse.body.quests.length).to.be.above(0)

      const activeQuest = questsResponse.body.quests[0]

      // Update quest progress
      const progressResponse = await request(buildServiceUrl('quest', '/api/quests'))
        .post(`/${activeQuest.id}/progress`)
        .set('Authorization', `Bearer ${tokens.integration}`)
        .send({
          objectiveType: 'explore',
          target: 'ancient-ruins',
          quantity: 1
        })
        .expect(200)

      expect(progressResponse.body).to.have.property('updated', true)

      // Verify progress reflected in character service
      const characterQuestResponse = await request(buildServiceUrl('n8n', '/api/characters'))
        .get(`/${characters.gandalf.id}/quests`)
        .set('Authorization', `Bearer ${tokens.integration}`)
        .expect(200)

      const characterQuest = characterQuestResponse.body.quests.find(q => q.id === activeQuest.id)
      expect(characterQuest).to.exist
      expect(characterQuest.progress).to.exist

      perfMonitor.endTimer('quest-progress-integration')
    })
  })

  describe('AI Services Integration', function() {
    it('should integrate dialogue generation with character personality', async function() {
      perfMonitor.startTimer('ai-dialogue-integration')

      // Get character details for context
      const characterResponse = await request(buildServiceUrl('aiDialogue', '/api/characters'))
        .get(`/${characters.gandalf.id}`)
        .set('Authorization', `Bearer ${tokens.integration}`)
        .expect(200)

      // Generate contextual dialogue
      const dialogueResponse = await request(buildServiceUrl('aiDialogue', '/api/conversation'))
        .post('/generate')
        .send({
          characterId: characters.gandalf.id,
          context: 'meeting-new-adventurers-in-tavern',
          mood: 'wise-and-friendly',
          situation: 'potential-quest-giver',
          personality: characterResponse.body.personality
        })
        .expect(200)

      expect(dialogueResponse.body).to.have.property('dialogue')
      expect(dialogueResponse.body).to.have.property('emotion')
      expect(dialogueResponse.body).to.have.property('actions')

      // Generate voice synthesis for the dialogue
      const voiceResponse = await request(buildServiceUrl('voice', '/api/voice'))
        .post('/synthesize')
        .send({
          text: dialogueResponse.body.dialogue,
          voiceId: 'wise-old-wizard',
          emotion: dialogueResponse.body.emotion,
          characterProfile: {
            race: 'human',
            class: 'wizard',
            age: 'elderly'
          }
        })
        .expect(200)

      expect(voiceResponse.body).to.have.property('audioUrl')
      expect(voiceResponse.body).to.have.property('duration')

      perfMonitor.endTimer('ai-dialogue-integration')
    })

    it('should provide consistent emotion analysis across services', async function() {
      perfMonitor.startTimer('emotion-analysis-integration')

      const textSamples = [
        'I am excited about this new adventure!',
        'This dungeon seems dangerous and scary.',
        'Your incompetence is infuriating!',
        'What a beautiful and peaceful morning.'
      ]

      const emotionResponses = []

      for (const text of textSamples) {
        const response = await request(buildServiceUrl('aiDialogue', '/api/emotion'))
          .post('/analyze')
          .send({
            text,
            characterId: characters.gandalf.id,
            context: 'general-conversation'
          })
          .expect(200)

        emotionResponses.push(response.body)
      }

      // Verify emotion detection is consistent
      expect(emotionResponses).to.have.length(4)
      expect(emotionResponses[0].emotion).to.equal('joy')
      expect(emotionResponses[1].emotion).to.equal('fear')
      expect(emotionResponses[2].emotion).to.equal('anger')
      expect(emotionResponses[3].emotion).to.equal('joy')

      // Verify emotions influence voice synthesis
      const voicePromises = emotionResponses.map(emotion =>
        request(buildServiceUrl('voice', '/api/voice'))
          .post('/synthesize')
          .send({
            text: 'Test message',
            voiceId: 'default',
            emotion: emotion.emotion,
            intensity: emotion.intensity
          })
      )

      const voiceResults = await Promise.all(voicePromises)

      for (const result of voiceResults) {
        expect(result.body).to.have.property('audioUrl')
      }

      perfMonitor.endTimer('emotion-analysis-integration')
    })
  })

  describe('Arena System Integration', function() {
    it('should integrate character stats with matchmaking', async function() {
      perfMonitor.startTimer('arena-matchmaking-integration')

      // Get character stats from main service
      const characterResponse = await request(buildServiceUrl('n8n', '/api/characters'))
        .get(`/${characters.gandalf.id}`)
        .set('Authorization', `Bearer ${tokens.integration}`)
        .expect(200)

      // Join arena queue
      const matchmakingResponse = await request(buildServiceUrl('arena', '/api/matchmaking'))
        .post('/join')
        .set('Authorization', `Bearer ${tokens.integration}`)
        .send({
          characterId: characters.gandalf.id,
          gameMode: 'duel',
          preferences: {
            skillRange: 'similar',
            allowCrossFaction: true
          }
        })
        .expect(200)

      expect(matchmakingResponse.body).to.have.property('matchId')
      expect(matchmakingResponse.body).to.have.property('estimatedWaitTime')

      // Verify matchmaking considered character level
      const matchmakingStatusResponse = await request(buildServiceUrl('arena', '/api/matchmaking'))
        .get(`/status/${matchmakingResponse.body.matchId}`)
        .set('Authorization', `Bearer ${tokens.integration}`)
        .expect(200)

      expect(matchmakingStatusResponse.body).to.have.property('characterLevel', 11)

      perfMonitor.endTimer('arena-matchmaking-integration')
    })

    it('should integrate guild affiliation with arena teams', async function() {
      perfMonitor.startTimer('arena-guild-integration')

      // Create guild team match
      const guildMatchResponse = await request(buildServiceUrl('arena', '/api/matchmaking'))
        .post('/guild-match')
        .set('Authorization', `Bearer ${tokens.integration}`)
        .send({
          guildId: guilds.testGuild.id,
          gameMode: 'team-battle',
          teamSize: 3
        })
        .expect(200)

      expect(guildMatchResponse.body).to.have.property('matchId')
      expect(guildMatchResponse.body).to.have.property('teamComposition')

      // Verify guild members are prioritized for team formation
      const teamResponse = await request(buildServiceUrl('arena', '/api/matches'))
        .get(`/${guildMatchResponse.body.matchId}/teams`)
        .set('Authorization', `Bearer ${tokens.integration}`)
        .expect(200)

      expect(teamResponse.body).to.have.property('teams')
      expect(teamResponse.body.teams).to.be.an('array')

      perfMonitor.endTimer('arena-guild-integration')
    })
  })

  describe('Weather System Integration', function() {
    it('should integrate weather effects with gameplay systems', async function() {
      perfMonitor.startTimer('weather-gameplay-integration')

      const location = 'Neverwinter Forest'

      // Get current weather
      const weatherResponse = await request(buildServiceUrl('weather', '/api/weather'))
        .get(`/current/${encodeURIComponent(location)}`)
        .expect(200)

      expect(weatherResponse.body).to.have.property('current')
      expect(weatherResponse.body.current).to.have.property('condition')

      // Get weather effects for gameplay
      const effectsResponse = await request(buildServiceUrl('weather', '/api/weather'))
        .get(`/effects/${encodeURIComponent(location)}`)
        .expect(200)

      expect(effectsResponse.body).to.have.property('gameplayEffects')
      expect(effectsResponse.body).to.have.property('magicalEffects')

      // Apply weather effects to combat system
      const combatResponse = await request(buildServiceUrl('arena', '/api/combat'))
        .post('/apply-weather')
        .set('Authorization', `Bearer ${tokens.integration}`)
        .send({
          location,
          weather: weatherResponse.body.current,
          effects: effectsResponse.body.gameplayEffects
        })
        .expect(200)

      expect(combatResponse.body).to.have.property('modified', true)
      expect(combatResponse.body).to.have.property('appliedEffects')

      perfMonitor.endTimer('weather-gameplay-integration')
    })
  })

  describe('Crafting System Integration', function() {
    it('should integrate crafting with character inventory', async function() {
      perfMonitor.startTimer('crafting-inventory-integration')

      // Get character inventory
      const inventoryResponse = await request(buildServiceUrl('n8n', '/api/characters'))
        .get(`/${characters.gandalf.id}/inventory`)
        .set('Authorization', `Bearer ${tokens.integration}`)
        .expect(200)

      // Get crafting recipes available to character
      const recipesResponse = await request(buildServiceUrl('crafting', '/api/recipes'))
        .get('/available')
        .set('Authorization', `Bearer ${tokens.integration}`)
        .send({
          characterId: characters.gandalf.id,
          level: 11,
          profession: 'alchemy'
        })
        .expect(200)

      expect(recipesResponse.body).to.have.property('recipes')
      expect(recipesResponse.body.recipes).to.be.an('array')

      // Craft an item
      const craftResponse = await request(buildServiceUrl('crafting', '/api/crafting'))
        .post('/craft')
        .set('Authorization', `Bearer ${tokens.integration}`)
        .send({
          characterId: characters.gandalf.id,
          recipeId: recipesResponse.body.recipes[0].id,
          quantity: 1
        })
        .expect(200)

      expect(craftResponse.body).to.have.property('success', true)
      expect(craftResponse.body).to.have.property('items')

      // Verify item added to character inventory
      const updatedInventoryResponse = await request(buildServiceUrl('n8n', '/api/characters'))
        .get(`/${characters.gandalf.id}/inventory`)
        .set('Authorization', `Bearer ${tokens.integration}`)
        .expect(200)

      expect(updatedInventoryResponse.body.items.length).to.be.above(inventoryResponse.body.items.length)

      perfMonitor.endTimer('crafting-inventory-integration')
    })
  })

  describe('Cross-Service Error Handling', function() {
    it('should handle service unavailability gracefully', async function() {
      perfMonitor.startTimer('error-handling-integration')

      // Simulate service failure by using invalid endpoint
      try {
        await request(buildServiceUrl('nonexistent', '/api/test'))
          .get('/')
          .timeout(5000)
          .expect(404)
      } catch (error) {
        expect(error.code).to.equal('ECONNREFUSED')
      }

      // Test graceful degradation when dependent service is unavailable
      const degradedResponse = await request(buildServiceUrl('n8n', '/api/characters'))
        .get(`/${characters.gandalf.id}/enhanced-profile`)
        .set('Authorization', `Bearer ${tokens.integration}`)
        .expect(200)

      expect(degradedResponse.body).to.have.property('basicProfile')
      expect(degradedResponse.body).to.have.property('enhancedFeatures', 'unavailable')

      perfMonitor.endTimer('error-handling-integration')
    })

    it('should propagate consistent error messages across services', async function() {
      perfMonitor.startTimer('error-message-consistency')

      // Test validation errors
      const invalidCharacterData = {
        name: '', // Invalid
        race: 'invalid-race',
        class: 'wizard',
        level: -1 // Invalid
      }

      const services = ['n8n', 'aiDialogue', 'arena']

      for (const service of services) {
        const response = await request(buildServiceUrl(service, '/api/characters'))
          .post('/')
          .set('Authorization', `Bearer ${tokens.integration}`)
          .send(invalidCharacterData)
          .expect(400)

        expect(response.body).to.have.property('error')
        expect(response.body).to.have.property('validationErrors')
        expect(response.body.validationErrors).to.be.an('array')
      }

      perfMonitor.endTimer('error-message-consistency')
    })
  })

  describe('Performance and Rate Limiting', function() {
    it('should enforce consistent rate limiting across services', async function() {
      perfMonitor.startTimer('rate-limiting-integration')

      const requests = []

      // Send rapid requests to trigger rate limiting
      for (let i = 0; i < 20; i++) {
        requests.push(
          request(buildServiceUrl('n8n', '/api/characters'))
            .get(`/${characters.gandalf.id}`)
            .set('Authorization', `Bearer ${tokens.integration}`)
        )
      }

      const responses = await Promise.allSettled(requests)

      // Some requests should be rate limited
      const rateLimitedResponses = responses.filter(r =>
        r.status === 'fulfilled' && r.value.status === 429
      )

      expect(rateLimitedResponses.length).to.be.above(0)

      // Verify rate limit headers
      if (rateLimitedResponses.length > 0) {
        const rateLimitResponse = rateLimitedResponses[0].value
        expect(rateLimitResponse.headers).to.have.property('x-ratelimit-limit')
        expect(rateLimitResponse.headers).to.have.property('x-ratelimit-remaining')
        expect(rateLimitResponse.headers).to.have.property('x-ratelimit-reset')
      }

      perfMonitor.endTimer('rate-limiting-integration')
    })
  })

  describe('Data Consistency Validation', function() {
    it('should maintain data consistency across service boundaries', async function() {
      perfMonitor.startTimer('cross-service-data-consistency')

      // Update character in main service
      const updateData = {
        gold: 5000,
        experience: 15000,
        level: 12,
        abilities: {
          ...characters.gandalf.abilities,
          wisdom: 17
        }
      }

      await request(buildServiceUrl('n8n', '/api/characters'))
        .put(`/${characters.gandalf.id}`)
        .set('Authorization', `Bearer ${tokens.integration}`)
        .send(updateData)
        .expect(200)

      // Verify consistency across all services
      const services = ['aiDialogue', 'arena', 'crafting', 'guild', 'quest']
      const consistencyPromises = services.map(service =>
        request(buildServiceUrl(service, '/api/characters'))
          .get(`/${characters.gandalf.id}`)
          .set('Authorization', `Bearer ${tokens.integration}`)
      )

      const responses = await Promise.all(consistencyPromises)

      for (const response of responses) {
        expect(response.body).to.have.property('gold', 5000)
        expect(response.body).to.have.property('experience', 15000)
        expect(response.body).to.have.property('level', 12)
        expect(response.body.abilities).to.have.property('wisdom', 17)
      }

      perfMonitor.endTimer('cross-service-data-consistency')
    })
  })
})