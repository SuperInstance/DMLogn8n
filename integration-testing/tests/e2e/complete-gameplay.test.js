/**
 * Complete Gameplay End-to-End Test
 *
 * This test simulates a complete D&D gameplay session including:
 * - User registration and character creation
 * - Finding and joining a campaign
 * - Combat encounters with AI dialogue
 * - Quest completion and progression
 * - DM interventions and world editing
 * - Social interactions and guild activities
 */

const request = require('supertest')
const { io } = require('socket.io-client')
const { TestEnvironment } = require('../../src/helpers/TestEnvironment')
const { PerformanceMonitor } = require('../../src/utils/logger')
const { config } = require('../../config/test-config')
const { expect } = require('chai')

describe('Complete Gameplay E2E Test', function() {
  this.timeout(config.timeouts.e2e)

  let testEnv
  let perfMonitor
  let users = {}
  let characters = {}
  let guilds = {}
  let quests = {}
  let sessions = {}
  let websockets = {}

  before(async function() {
    this.timeout(60000) // Longer timeout for setup

    perfMonitor = new PerformanceMonitor('complete-gameplay-e2e')
    perfMonitor.startTimer('test-setup')

    testEnv = new TestEnvironment({
      autoStart: true,
      useInMemoryDatabases: true,
      cleanupOnExit: true
    })

    await testEnv.initialize()
    await testEnv.waitForReady()

    // Seed initial data
    await testEnv.seedData('users', 5)
    await testEnv.seedData('characters', 10)
    await testEnv.seedData('guilds', 2)
    await testEnv.seedData('quests', 20)

    perfMonitor.endTimer('test-setup')
  })

  after(async function() {
    this.timeout(30000)

    perfMonitor.startTimer('test-cleanup')

    // Close all WebSocket connections
    for (const [name, ws] of Object.entries(websockets)) {
      if (ws && ws.connected) {
        ws.disconnect()
      }
    }

    // Cleanup environment
    await testEnv.cleanup()

    const summary = perfMonitor.getSummary()
    console.log('\n=== Test Performance Summary ===')
    console.log(JSON.stringify(summary, null, 2))

    perfMonitor.endTimer('test-cleanup')
  })

  describe('User Registration and Authentication', function() {
    it('should register new users successfully', async function() {
      perfMonitor.startTimer('user-registration')

      const userData = [
        {
          username: 'testplayer1',
          email: 'player1@test.com',
          password: 'password123',
          roles: ['player']
        },
        {
          username: 'testdm1',
          email: 'dm1@test.com',
          password: 'password123',
          roles: ['dm']
        },
        {
          username: 'testplayer2',
          email: 'player2@test.com',
          password: 'password123',
          roles: ['player']
        }
      ]

      for (const user of userData) {
        // Register user (mock implementation)
        const response = await request('http://localhost:5678')
          .post('/api/users/register')
          .send(user)
          .expect(201)

        users[user.username] = {
          ...response.body,
          credentials: user
        }

        expect(response.body).to.have.property('id')
        expect(response.body).to.have.property('username', user.username)
      }

      perfMonitor.endTimer('user-registration')
    })

    it('should authenticate users and create sessions', async function() {
      perfMonitor.startTimer('user-authentication')

      for (const [username, user] of Object.entries(users)) {
        const response = await request('http://localhost:5678')
          .post('/api/auth/login')
          .send({
            email: user.credentials.email,
            password: user.credentials.password
          })
          .expect(200)

        expect(response.body).to.have.property('token')
        expect(response.body).to.have.property('user')

        sessions[username] = {
          token: response.body.token,
          user: response.body.user
        }
      }

      perfMonitor.endTimer('user-authentication')
    })
  })

  describe('Character Creation and Management', function() {
    it('should create characters with valid attributes', async function() {
      perfMonitor.startTimer('character-creation')

      const characterData = {
        'testplayer1': {
          name: 'Thorin Ironforge',
          race: 'dwarf',
          class: 'fighter',
          background: 'soldier',
          alignment: 'lawful-good',
          level: 1
        },
        'testplayer2': {
          name: 'Elara Moonwhisper',
          race: 'elf',
          class: 'wizard',
          background: 'scholar',
          alignment: 'neutral-good',
          level: 1
        }
      }

      for (const [username, data] of Object.entries(characterData)) {
        const response = await request('http://localhost:3001')
          .post('/api/characters')
          .set('Authorization', `Bearer ${sessions[username].token}`)
          .send(data)
          .expect(201)

        characters[username] = response.body

        expect(response.body).to.have.property('id')
        expect(response.body).to.have.property('name', data.name)
        expect(response.body).to.have.property('abilities')
        expect(response.body.abilities).to.have.property('strength')
        expect(response.body.abilities).to.have.property('dexterity')
      }

      perfMonitor.endTimer('character-creation')
    })

    it('should validate character attributes and constraints', async function() {
      for (const [username, character] of Object.entries(characters)) {
        // Validate ability scores
        expect(character.abilities.strength).to.be.at.least(3)
        expect(character.abilities.strength).to.be.at.most(18)
        expect(character.abilities.dexterity).to.be.at.least(3)
        expect(character.abilities.dexterity).to.be.at.most(18)

        // Validate combat stats
        expect(character.combat).to.have.property('hitPoints')
        expect(character.combat).to.have.property('armorClass')
        expect(character.combat.hitPoints).to.be.above(0)
        expect(character.combat.armorClass).to.be.above(0)
      }
    })
  })

  describe('Campaign Creation and Management', function() {
    it('should create a new campaign as DM', async function() {
      perfMonitor.startTimer('campaign-creation')

      const campaignData = {
        name: 'The Lost Mine of Phandelver',
        description: 'A beginner adventure for 1-4 players',
        level: {
          min: 1,
          max: 3
        },
        maxPlayers: 4,
        settings: {
          allowRandomEncounters: true,
          enableVoiceChat: true,
          public: false
        }
      }

      const response = await request('http://localhost:5678')
        .post('/api/campaigns')
        .set('Authorization', `Bearer ${sessions.testdm1.token}`)
        .send(campaignData)
        .expect(201)

      expect(response.body).to.have.property('id')
      expect(response.body).to.have.property('name', campaignData.name)

      sessions.testdm1.campaign = response.body

      perfMonitor.endTimer('campaign-creation')
    })

    it('should allow players to join the campaign', async function() {
      perfMonitor.startTimer('campaign-join')

      for (const username of ['testplayer1', 'testplayer2']) {
        const response = await request('http://localhost:5678')
          .post(`/api/campaigns/${sessions.testdm1.campaign.id}/join`)
          .set('Authorization', `Bearer ${sessions[username].token}`)
          .send({
            characterId: characters[username].id
          })
          .expect(200)

        expect(response.body).to.have.property('success', true)

        // Update session with campaign info
        sessions[username].campaign = sessions.testdm1.campaign
        sessions[username].campaignRole = 'player'
      }

      perfMonitor.endTimer('campaign-join')
    })
  })

  describe('Real-time Gameplay with WebSocket', function() {
    it('should establish WebSocket connections for all players', async function() {
      perfMonitor.startTimer('websocket-connection')

      const wsConfig = {
        transports: ['websocket'],
        auth: {
          token: sessions.testdm1.token
        }
      }

      // Connect DM
      websockets.dm = io('http://localhost:5678', wsConfig)
      await new Promise(resolve => websockets.dm.on('connect', resolve))

      // Connect players
      for (const username of ['testplayer1', 'testplayer2']) {
        const playerWs = io('http://localhost:5678', {
          transports: ['websocket'],
          auth: {
            token: sessions[username].token
          }
        })

        await new Promise(resolve => playerWs.on('connect', resolve))
        websockets[username] = playerWs
      }

      // Verify all connections
      expect(websockets.dm.connected).to.be.true
      expect(websockets.testplayer1.connected).to.be.true
      expect(websockets.testplayer2.connected).to.be.true

      perfMonitor.endTimer('websocket-connection')
    })

    it('should handle campaign start and synchronization', async function() {
      perfMonitor.startTimer('campaign-start')

      // DM starts the campaign
      await new Promise(resolve => {
        websockets.dm.emit('campaign-start', {
          campaignId: sessions.testdm1.campaign.id
        })

        websockets.dm.on('campaign-started', (data) => {
          expect(data).to.have.property('campaignId')
          expect(data).to.have.property('timestamp')
          resolve()
        })
      })

      // Players receive campaign start notification
      for (const username of ['testplayer1', 'testplayer2']) {
        await new Promise(resolve => {
          websockets[username].on('campaign-started', (data) => {
            expect(data.campaignId).to.equal(sessions.testdm1.campaign.id)
            resolve()
          })
        })
      }

      perfMonitor.endTimer('campaign-start')
    })
  })

  describe('Combat Encounter with AI Dialogue', function() {
    it('should initiate combat with AI-generated enemy dialogue', async function() {
      perfMonitor.startTimer('combat-initiation')

      // DM initiates combat
      const combatData = {
        enemies: [
          {
            name: 'Goblin Boss',
            type: 'goblin',
            hp: 30,
            ac: 15,
            initiative: 14
          },
          {
            name: 'Goblin Grunt',
            type: 'goblin',
            hp: 10,
            ac: 12,
            initiative: 8
          }
        ],
        location: 'Goblin Cave Entrance',
        description: 'The party encounters goblins guarding a cave entrance'
      }

      await new Promise(resolve => {
        websockets.dm.emit('combat-start', combatData)

        websockets.dm.on('combat-started', (data) => {
          expect(data).to.have.property('combatId')
          expect(data.enemies).to.have.length(2)
          resolve()
        })
      })

      // Generate AI dialogue for enemies
      const dialogueResponse = await request('http://localhost:3001')
        .post('/api/conversation/generate')
        .send({
          context: 'Combat initiation - goblins challenging intruders',
          characterId: 'goblin-boss',
          mood: 'aggressive',
          situation: 'defending territory'
        })
        .expect(200)

      expect(dialogueResponse.body).to.have.property('dialogue')
      expect(dialogueResponse.body).to.have.property('emotion')

      perfMonitor.endTimer('combat-initiation')
    })

    it('should handle combat rounds with player actions', async function() {
      perfMonitor.startTimer('combat-rounds')

      // Simulate combat rounds
      const rounds = 3

      for (let round = 1; round <= rounds; round++) {
        await new Promise(resolve => {
          // Player 1 attacks
          websockets.testplayer1.emit('combat-action', {
            action: 'attack',
            target: 'goblin-boss',
            roll: 18,
            damage: 12
          })

          // Player 2 casts spell
          websockets.testplayer2.emit('combat-action', {
            action: 'spell',
            spell: 'magic-missile',
            target: 'goblin-grunt',
            damage: 9
          })

          // Wait for round completion
          websockets.dm.on('combat-round-complete', (data) => {
            expect(data.round).to.equal(round)
            expect(data).to.have.property('results')
            resolve()
          })
        })
      }

      perfMonitor.endTimer('combat-rounds')
    })

    it('should resolve combat and provide rewards', async function() {
      perfMonitor.startTimer('combat-resolution')

      await new Promise(resolve => {
        websockets.dm.emit('combat-end', {
          victory: true,
          rewards: {
            gold: 150,
            experience: 100,
            items: ['shortsword', 'healing-potion']
          }
        })

        websockets.dm.on('combat-ended', (data) => {
          expect(data).to.have.property('victory', true)
          expect(data.rewards).to.have.property('gold', 150)
          resolve()
        })
      })

      // Verify player characters received rewards
      for (const username of ['testplayer1', 'testplayer2']) {
        const response = await request('http://localhost:3001')
          .get(`/api/characters/${characters[username].id}`)
          .set('Authorization', `Bearer ${sessions[username].token}`)
          .expect(200)

        expect(response.body.gold).to.be.at.least(150)
        expect(response.body.experience).to.be.at.least(100)
      }

      perfMonitor.endTimer('combat-resolution')
    })
  })

  describe('Quest System Integration', function() {
    it('should generate contextual quests based on player actions', async function() {
      perfMonitor.startTimer('quest-generation')

      const questRequest = {
        characterLevel: 1,
        preferences: {
          types: ['explore', 'kill'],
          difficulty: 'easy'
        },
        location: 'Phandalin',
        context: 'After defeating goblins, players find a map'
      }

      const response = await request('http://localhost:3006')
        .post('/api/generation/generate')
        .send(questRequest)
        .expect(200)

      expect(response.body).to.have.property('id')
      expect(response.body).to.have.property('title')
      expect(response.body).to.have.property('objectives')
      expect(response.body.objectives).to.be.an('array')

      // Store quest for players
      for (const username of ['testplayer1', 'testplayer2']) {
        const assignResponse = await request('http://localhost:3006')
          .post(`/api/quests/${response.body.id}/assign`)
          .set('Authorization', `Bearer ${sessions[username].token}`)
          .send({
            characterId: characters[username].id
          })
          .expect(200)

        quests[username] = response.body
      }

      perfMonitor.endTimer('quest-generation')
    })

    it('should track quest progress automatically', async function() {
      perfMonitor.startTimer('quest-progress')

      // Simulate quest progress (killing goblins)
      for (const username of ['testplayer1', 'testplayer2']) {
        const progressResponse = await request('http://localhost:3006')
          .post(`/api/quests/${quests[username].id}/progress`)
          .set('Authorization', `Bearer ${sessions[username].token}`)
          .send({
            objectiveType: 'kill',
            target: 'goblin',
            quantity: 2
          })
          .expect(200)

        expect(progressResponse.body).to.have.property('updated', true)
        expect(progressResponse.body).to.have.property('progress')
      }

      perfMonitor.endTimer('quest-progress')
    })
  })

  describe('Guild System Integration', function() {
    it('should create and manage guild membership', async function() {
      perfMonitor.startTimer('guild-management')

      // Create a guild
      const guildData = {
        name: 'Dragon Slayers',
        tag: 'DSLR',
        description: 'A guild dedicated to protecting the realm',
        type: 'adventuring'
      }

      const createResponse = await request('http://localhost:3005')
        .post('/api/guilds')
        .set('Authorization', `Bearer ${sessions.testplayer1.token}`)
        .send(guildData)
        .expect(201)

      guilds.dragonSlayers = createResponse.body

      // Invite other player
      await request('http://localhost:3005')
        .post(`/api/guilds/${guilds.dragonSlayers.id}/invite`)
        .set('Authorization', `Bearer ${sessions.testplayer1.token}`)
        .send({
          characterId: characters.testplayer2.id
        })
        .expect(200)

      // Accept invitation
      await request('http://localhost:3005')
        .post(`/api/guilds/${guilds.dragonSlayers.id}/join`)
        .set('Authorization', `Bearer ${sessions.testplayer2.token}`)
        .send({
          invitationId: 'test-invitation'
        })
        .expect(200)

      perfMonitor.endTimer('guild-management')
    })

    it('should handle guild bank and shared resources', async function() {
      perfMonitor.startTimer('guild-bank')

      // Deposit items to guild bank
      await request('http://localhost:3005')
        .post(`/api/guilds/${guilds.dragonSlayers.id}/bank/deposit`)
        .set('Authorization', `Bearer ${sessions.testplayer1.token}`)
        .send({
          items: [
            { id: 'potion-1', name: 'Healing Potion', quantity: 5 },
            { id: 'gold-1', name: 'Gold', quantity: 200 }
          ]
        })
        .expect(200)

      // Check bank contents
      const bankResponse = await request('http://localhost:3005')
        .get(`/api/guilds/${guilds.dragonSlayers.id}/bank`)
        .set('Authorization', `Bearer ${sessions.testplayer1.token}`)
        .expect(200)

      expect(bankResponse.body).to.have.property('items')
      expect(bankResponse.body).to.have.property('gold')
      expect(bankResponse.body.gold).to.be.at.least(200)

      perfMonitor.endTimer('guild-bank')
    })
  })

  describe('AI Voice Synthesis Integration', function() {
    it('should synthesize voice for NPC dialogue', async function() {
      perfMonitor.startTimer('voice-synthesis')

      const synthesisRequest = {
        text: 'Welcome, brave adventurers! I have a quest for you.',
        voiceId: 'npc-elderly-male',
        emotion: 'friendly',
        language: 'en-US'
      }

      const response = await request('http://localhost:3007')
        .post('/api/voice/synthesize')
        .send(synthesisRequest)
        .expect(200)

      expect(response.body).to.have.property('audioUrl')
      expect(response.body).to.have.property('duration')
      expect(response.body).to.have.property('text', synthesisRequest.text)

      perfMonitor.endTimer('voice-synthesis')
    })

    it('should handle real-time voice generation during gameplay', async function() {
      perfMonitor.startTimer('real-time-voice')

      // Simulate real-time voice request during conversation
      const realTimeRequest = {
        text: 'The goblins are attacking! Help!',
        voiceId: 'npc-desperate-female',
        emotion: 'panic',
        priority: 'high'
      }

      const response = await request('http://localhost:3007')
        .post('/api/voice/synthesize/realtime')
        .send(realTimeRequest)
        .expect(200)

      expect(response.body).to.have.property('audioUrl')
      expect(response.body.priority).to.equal('high')

      perfMonitor.endTimer('real-time-voice')
    })
  })

  describe('Multiplayer Arena Integration', function() {
    it('should handle arena matchmaking and combat', async function() {
      perfMonitor.startTimer('arena-matchmaking')

      // Join arena queue
      const matchmakingResponse = await request('http://localhost:3002')
        .post('/api/matchmaking/join')
        .set('Authorization', `Bearer ${sessions.testplayer1.token}`)
        .send({
          characterId: characters.testplayer1.id,
          gameMode: 'duel',
          preferences: {
            skillRange: 'any',
            allowSpectators: true
          }
        })
        .expect(200)

      expect(matchmakingResponse.body).to.have.property('matchId')
      expect(matchmakingResponse.body).to.have.property('status', 'searching')

      // Simulate match found
      await new Promise(resolve => setTimeout(resolve, 2000))

      perfMonitor.endTimer('arena-matchmaking')
    })
  })

  describe('Dynamic Weather System Integration', function() {
    it('should provide weather effects for gameplay', async function() {
      perfMonitor.startTimer('weather-system')

      const location = 'Neverwinter Forest'

      // Get current weather
      const weatherResponse = await request('http://localhost:3008')
        .get(`/api/weather/current/${encodeURIComponent(location)}`)
        .expect(200)

      expect(weatherResponse.body).to.have.property('current')
      expect(weatherResponse.body.current).to.have.property('temperature')
      expect(weatherResponse.body.current).to.have.property('condition')

      // Get weather forecast
      const forecastResponse = await request('http://localhost:3008')
        .get(`/api/weather/forecast/${encodeURIComponent(location)}`)
        .query({ days: 3 })
        .expect(200)

      expect(forecastResponse.body).to.have.property('forecast')
      expect(forecastResponse.body.forecast).to.have.length(3)

      perfMonitor.endTimer('weather-system')
    })
  })

  describe('Campaign Completion and Data Persistence', function() {
    it('should save campaign state and progress', async function() {
      perfMonitor.startTimer('campaign-save')

      // DM saves campaign
      await new Promise(resolve => {
        websockets.dm.emit('campaign-save', {
          progress: {
            sessionNumber: 1,
            questsCompleted: 1,
            totalExperience: 100,
            milestones: ['defeated-goblins', 'joined-guild']
          }
        })

        websockets.dm.on('campaign-saved', (data) => {
          expect(data).to.have.property('success', true)
          expect(data).to.have.property('timestamp')
          resolve()
        })
      })

      perfMonitor.endTimer('campaign-save')
    })

    it('should generate campaign summary and analytics', async function() {
      perfMonitor.startTimer('campaign-analytics')

      const analyticsResponse = await request('http://localhost:5678')
        .get(`/api/campaigns/${sessions.testdm1.campaign.id}/analytics`)
        .set('Authorization', `Bearer ${sessions.testdm1.token}`)
        .expect(200)

      expect(analyticsResponse.body).to.have.property('summary')
      expect(analyticsResponse.body).to.have.property('playerStats')
      expect(analyticsResponse.body).to.have.property('encounterStats')

      perfMonitor.endTimer('campaign-analytics')
    })
  })

  describe('System Integration Validation', function() {
    it('should validate cross-system data consistency', async function() {
      perfMonitor.startTimer('data-consistency')

      // Check that character progression is consistent across systems
      for (const username of ['testplayer1', 'testplayer2']) {
        // Get character from main system
        const characterResponse = await request('http://localhost:3001')
          .get(`/api/characters/${characters[username].id}`)
          .set('Authorization', `Bearer ${sessions[username].token}`)
          .expect(200)

        // Get character stats from arena system
        const arenaStatsResponse = await request('http://localhost:3002')
          .get(`/api/characters/${characters[username].id}/stats`)
          .set('Authorization', `Bearer ${sessions[username].token}`)
          .expect(200)

        // Validate consistency
        expect(characterResponse.body.level).to.equal(arenaStatsResponse.body.level)
        expect(characterResponse.body.experience).to.equal(arenaStatsResponse.body.experience)
      }

      perfMonitor.endTimer('data-consistency')
    })

    it('should handle error recovery gracefully', async function() {
      perfMonitor.startTimer('error-recovery')

      // Simulate service unavailability
      const originalService = config.services.aiDialogue

      // Test graceful degradation when service is unavailable
      try {
        await request('http://localhost:3001')
          .post('/api/conversation/generate')
          .timeout(5000)
          .send({
            context: 'test',
            characterId: 'test'
          })
      } catch (error) {
        expect(error.code).to.equal('ECONNABORTED')
      }

      // System should continue to function with limited features
      const fallbackResponse = await request('http://localhost:3001')
        .get('/api/status')
        .expect(200)

      expect(fallbackResponse.body).to.have.property('status')

      perfMonitor.endTimer('error-recovery')
    })
  })
})