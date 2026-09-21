/**
 * DM Intervention End-to-End Test
 *
 * This test validates Dungeon Master capabilities including:
 * - Real-time world editing and modification
 * - NPC control and dialogue management
 * - Dynamic encounter adjustment
 * - Environmental effects and weather control
 * - Player monitoring and intervention tools
 * - Campaign management and story progression
 */

const request = require('supertest')
const { io } = require('socket.io-client')
const { TestEnvironment } = require('../../src/helpers/TestEnvironment')
const { PerformanceMonitor } = require('../../src/utils/logger')
const { config } = require('../../config/test-config')
const { expect } = require('chai')

describe('DM Intervention E2E Test', function() {
  this.timeout(config.timeouts.e2e)

  let testEnv
  let perfMonitor
  let users = {}
  let sessions = {}
  let campaign = {}
  let websockets = {}
  let interventions = []

  before(async function() {
    this.timeout(60000)

    perfMonitor = new PerformanceMonitor('dm-intervention-e2e')
    perfMonitor.startTimer('test-setup')

    testEnv = new TestEnvironment({
      autoStart: true,
      useInMemoryDatabases: true,
      cleanupOnExit: true
    })

    await testEnv.initialize()
    await testEnv.waitForReady()

    // Seed data for testing
    await testEnv.seedData('users', 3)
    await testEnv.seedData('characters', 6)
    await testEnv.seedData('quests', 10)

    perfMonitor.endTimer('test-setup')
  })

  after(async function() {
    this.timeout(30000)

    perfMonitor.startTimer('test-cleanup')

    // Close WebSocket connections
    for (const ws of Object.values(websockets)) {
      if (ws && ws.connected) {
        ws.disconnect()
      }
    }

    await testEnv.cleanup()

    const summary = perfMonitor.getSummary()
    console.log('\n=== DM Intervention Test Performance ===')
    console.log(JSON.stringify(summary, null, 2))

    perfMonitor.endTimer('test-cleanup')
  })

  describe('DM Session Setup', function() {
    it('should create DM account and authenticate', async function() {
      perfMonitor.startTimer('dm-authentication')

      // Create DM user
      const dmResponse = await request('http://localhost:5678')
        .post('/api/users/register')
        .send({
          username: 'testdm',
          email: 'dm@test.com',
          password: 'password123',
          roles: ['dm']
        })
        .expect(201)

      users.dm = dmResponse.body

      // Authenticate DM
      const loginResponse = await request('http://localhost:5678')
        .post('/api/auth/login')
        .send({
          email: 'dm@test.com',
          password: 'password123'
        })
        .expect(200)

      sessions.dm = {
        token: loginResponse.body.token,
        user: loginResponse.body.user
      }

      expect(sessions.dm.user.roles).to.include('dm')

      perfMonitor.endTimer('dm-authentication')
    })

    it('should create player accounts and authenticate', async function() {
      perfMonitor.startTimer('player-authentication')

      const playerData = [
        { username: 'player1', email: 'player1@test.com' },
        { username: 'player2', email: 'player2@test.com' }
      ]

      for (const player of playerData) {
        // Register player
        const registerResponse = await request('http://localhost:5678')
          .post('/api/users/register')
          .send({
            ...player,
            password: 'password123',
            roles: ['player']
          })
          .expect(201)

        users[player.username] = registerResponse.body

        // Authenticate player
        const loginResponse = await request('http://localhost:5678')
          .post('/api/auth/login')
          .send({
            email: player.email,
            password: 'password123'
          })
          .expect(200)

        sessions[player.username] = {
          token: loginResponse.body.token,
          user: loginResponse.body.user
        }
      }

      perfMonitor.endTimer('player-authentication')
    })

    it('should establish WebSocket connections for all participants', async function() {
      perfMonitor.startTimer('websocket-connections')

      // Connect DM
      websockets.dm = io('http://localhost:5678', {
        transports: ['websocket'],
        auth: { token: sessions.dm.token }
      })
      await new Promise(resolve => websockets.dm.on('connect', resolve))

      // Connect players
      for (const username of ['player1', 'player2']) {
        const playerWs = io('http://localhost:5678', {
          transports: ['websocket'],
          auth: { token: sessions[username].token }
        })

        await new Promise(resolve => playerWs.on('connect', resolve))
        websockets[username] = playerWs
      }

      // Verify connections
      expect(websockets.dm.connected).to.be.true
      expect(websockets.player1.connected).to.be.true
      expect(websockets.player2.connected).to.be.true

      perfMonitor.endTimer('websocket-connections')
    })
  })

  describe('Campaign Creation and World Building', function() {
    it('should create a new campaign with custom world settings', async function() {
      perfMonitor.startTimer('campaign-creation')

      const campaignData = {
        name: 'The Curse of Strahd',
        description: 'A gothic horror adventure in the land of Barovia',
        setting: 'ravenloft',
        levelRange: { min: 3, max: 10 },
        maxPlayers: 4,
        worldSettings: {
          theme: 'gothic-horror',
          difficulty: 'challenging',
          deathRules: 'permadeath',
          restRules: 'standard'
        },
        customRules: {
          fearMechanics: true,
          madnessRules: true,
          supernaturalAtmosphere: true
        }
      }

      const response = await request('http://localhost:5678')
        .post('/api/campaigns')
        .set('Authorization', `Bearer ${sessions.dm.token}`)
        .send(campaignData)
        .expect(201)

      campaign = response.body
      expect(campaign).to.have.property('id')
      expect(campaign.worldSettings.theme).to.equal('gothic-horror')

      perfMonitor.endTimer('campaign-creation')
    })

    it('should populate world with locations and NPCs', async function() {
      perfMonitor.startTimer('world-population')

      const worldData = {
        locations: [
          {
            name: 'Barovia Village',
            description: 'A gloomy village nestled in the shadow of Castle Ravenloft',
            type: 'settlement',
            population: 200,
            notableFeatures: ['church', 'tavern', 'shop'],
            atmosphere: 'oppressive',
            weatherEffects: ['constant-fog', 'chilling-wind']
          },
          {
            name: 'Castle Ravenloft',
            description: 'The ancestral home of Strahd von Zarovich',
            type: 'dungeon',
            population: 50,
            notableFeatures: ['throne-room', 'dungeons', 'laboratory'],
            atmosphere: 'haunted',
            weatherEffects: ['magical-darkness', 'ghostly-presence']
          }
        ],
        npcs: [
          {
            name: 'Ismark the Lesser',
            role: 'village-leader',
            location: 'Barovia Village',
            personality: 'worried-but-determined',
            dialogueTree: 'greeting-quest-branching'
          },
          {
            name: 'Strahd von Zarovich',
            role: 'villain',
            location: 'Castle Ravenloft',
            personality: 'charismatic-but-evil',
            dialogueTree: 'menacing-dialogue'
          }
        ]
      }

      const response = await request('http://localhost:5678')
        .post(`/api/campaigns/${campaign.id}/world`)
        .set('Authorization', `Bearer ${sessions.dm.token}`)
        .send(worldData)
        .expect(200)

      expect(response.body).to.have.property('locations')
      expect(response.body).to.have.property('npcs')
      expect(response.body.locations).to.have.length(2)

      perfMonitor.endTimer('world-population')
    })
  })

  describe('Real-time World Editing', function() {
    it('should allow DM to add new locations during gameplay', async function() {
      perfMonitor.startTimer('dynamic-location-creation')

      const newLocation = {
        name: 'Forgotten Crypt',
        description: 'An ancient crypt unearthed by recent storms',
        type: 'dungeon',
        atmosphere: 'eerie',
        addedDuringPlay: true,
        secretEntrance: true
      }

      await new Promise(resolve => {
        websockets.dm.emit('world-add-location', newLocation)

        websockets.dm.on('location-added', (data) => {
          expect(data.location.name).to.equal(newLocation.name)
          expect(data.location.addedDuringPlay).to.be.true
          resolve()
        })
      })

      // Players should receive notification of new discovery
      for (const username of ['player1', 'player2']) {
        await new Promise(resolve => {
          websockets[username].on('location-discovered', (data) => {
            expect(data.name).to.equal('Forgotten Crypt')
            resolve()
          })
        })
      }

      interventions.push({
        type: 'location-creation',
        timestamp: new Date(),
        details: newLocation
      })

      perfMonitor.endTimer('dynamic-location-creation')
    })

    it('should allow DM to modify environmental conditions', async function() {
      perfMonitor.startTimer('environmental-modification')

      const environmentalChanges = {
        location: 'Barovia Village',
        weather: {
          condition: 'supernatural-storm',
          visibility: 'poor',
          effects: ['lightning', 'thunder', 'magical-rain'],
          duration: '1d6 hours'
        },
        atmosphere: {
          tension: 'high',
          supernaturalPresence: 'strong',
          ambientSounds: ['distant-screams', 'ghostly-whispers']
        },
        magicalEffects: [
          {
            type: 'fear-aura',
            radius: '100ft',
            saveDC: 13,
            effect: 'disadvantage on perception checks'
          }
        ]
      }

      await new Promise(resolve => {
        websockets.dm.emit('world-modify-environment', environmentalChanges)

        websockets.dm.on('environment-modified', (data) => {
          expect(data.weather.condition).to.equal('supernatural-storm')
          resolve()
        })
      })

      // Players should experience the environmental changes
      for (const username of ['player1', 'player2']) {
        await new Promise(resolve => {
          websockets[username].on('environment-changed', (data) => {
            expect(data.weather.condition).to.equal('supernatural-storm')
            expect(data.effects).to.include('lightning')
            resolve()
          })
        })
      }

      interventions.push({
        type: 'environmental-change',
        timestamp: new Date(),
        details: environmentalChanges
      })

      perfMonitor.endTimer('environmental-modification')
    })

    it('should spawn dynamic encounters based on player actions', async function() {
      perfMonitor.startTimer('dynamic-encounter-spawn')

      // Players enter dangerous area, DM spawns appropriate encounter
      const encounterData = {
        trigger: 'player-entered-forbidden-area',
        location: 'Castle Ravenloft - Crypt',
        enemies: [
          {
            name: 'Strahd Zombie',
            type: 'undead',
            count: 4,
            hp: 22,
            ac: 8,
            abilities: ['undead-fortitude', 'darkvision']
          },
          {
            name: 'Ghost',
            type: 'undead',
            count: 2,
            hp: 45,
            ac: 12,
            abilities: ['ethereal', 'possess', 'terrifying-visage']
          }
        ],
        environmentalHazards: ['desecrated-ground', 'haunting-presence'],
        loot: {
          gold: '2d8 x 10',
          items: ['ancient-jewelry', 'spell-scroll']
        }
      }

      await new Promise(resolve => {
        websockets.dm.emit('encounter-spawn', encounterData)

        websockets.dm.on('encounter-spawned', (data) => {
          expect(data.enemies).to.have.length(2)
          expect(data.enemies[0].name).to.equal('Strahd Zombie')
          resolve()
        })
      })

      // Players should see the encounter appear
      for (const username of ['player1', 'player2']) {
        await new Promise(resolve => {
          websockets[username].on('encounter-appeared', (data) => {
            expect(data.enemies).to.have.length.greaterThan(0)
            resolve()
          })
        })
      }

      interventions.push({
        type: 'dynamic-encounter',
        timestamp: new Date(),
        details: encounterData
      })

      perfMonitor.endTimer('dynamic-encounter-spawn')
    })
  })

  describe('NPC Control and Dialogue Management', function() {
    it('should allow DM to take control of NPCs', async function() {
      perfMonitor.startTimer('npc-control')

      const npcControl = {
        npcId: 'strahd-von-zarovich',
        action: 'take-control',
        motivation: 'test-players-resolve',
        dialogueIntent: 'menacing-but-charismatic'
      }

      await new Promise(resolve => {
        websockets.dm.emit('npc-control', npcControl)

        websockets.dm.on('npc-controlled', (data) => {
          expect(data.npcId).to.equal('strahd-von-zarovich')
          expect(data.controlledBy).to.equal('dm')
          resolve()
        })
      })

      interventions.push({
        type: 'npc-control',
        timestamp: new Date(),
        details: npcControl
      })

      perfMonitor.endTimer('npc-control')
    })

    it('should generate context-aware NPC dialogue', async function() {
      perfMonitor.startTimer('npc-dialogue-generation')

      const dialogueRequest = {
        npcId: 'strahd-von-zarovich',
        context: {
          playerActions: ['entered-throne-room', 'challenged-authority'],
          emotionalState: 'amused-but-dangerous',
          plotPoint: 'first-confrontation',
          playerRelationship: 'neutral-to-hostile'
        },
        tone: 'menacing-sophistication',
        objectives: ['intimidate', 'test-resolve', 'offer-temptation']
      }

      const dialogueResponse = await request('http://localhost:3001')
        .post('/api/conversation/generate')
        .send(dialogueRequest)
        .expect(200)

      expect(dialogueResponse.body).to.have.property('dialogue')
      expect(dialogueResponse.body).to.have.property('emotion')
      expect(dialogueResponse.body).to.have.property('actions')

      // Deliver dialogue through WebSocket
      await new Promise(resolve => {
        websockets.dm.emit('npc-speak', {
          npcId: 'strahd-von-zarovich',
          dialogue: dialogueResponse.body.dialogue,
          emotion: dialogueResponse.body.emotion,
          actions: dialogueResponse.body.actions
        })

        websockets.dm.on('npc-spoke', resolve)
      })

      // Players should receive the dialogue
      for (const username of ['player1', 'player2']) {
        await new Promise(resolve => {
          websockets[username].once('npc-dialogue', (data) => {
            expect(data.npcId).to.equal('strahd-von-zarovich')
            expect(data.dialogue).to.be.a('string')
            resolve()
          })
        })
      }

      interventions.push({
        type: 'npc-dialogue',
        timestamp: new Date(),
        details: dialogueResponse.body
      })

      perfMonitor.endTimer('npc-dialogue-generation')
    })

    it('should handle complex dialogue trees and player responses', async function() {
      perfMonitor.startTimer('dialogue-tree-interaction')

      // Player responds to NPC
      await new Promise(resolve => {
        websockets.player1.emit('player-response', {
          npcId: 'strahd-von-zarovich',
          response: 'We are here to end your tyranny, Strahd!',
          tone: 'defiant',
          action: 'challenge'
        })

        websockets.player1.on('dialogue-branch', (data) => {
          expect(data.branchId).to.exist
          expect(data.options).to.be.an('array')
          resolve()
        })
      })

      // DM selects dialogue branch
      const branchSelection = {
        branchId: 'strahd-amused-challenge',
        response: 'Amusing. You mortals always bring such entertainment to my eternal existence.',
        nextAction: 'offer-deal'
      }

      await new Promise(resolve => {
        websockets.dm.emit('select-dialogue-branch', branchSelection)
        websockets.dm.on('branch-selected', resolve)
      })

      interventions.push({
        type: 'dialogue-tree',
        timestamp: new Date(),
        details: branchSelection
      })

      perfMonitor.endTimer('dialogue-tree-interaction')
    })
  })

  describe('Dynamic Difficulty Adjustment', function() {
    it('should monitor player performance and adjust difficulty', async function() {
      perfMonitor.startTimer('difficulty-monitoring')

      const performanceData = {
        players: [
          {
            id: 'player1',
            health: '60%',
            resources: 'low',
            effectiveness: 'high',
            recentActions: ['successful-attacks', 'good-roleplay']
          },
          {
            id: 'player2',
            health: '30%',
            resources: 'critical',
            effectiveness: 'struggling',
            recentActions: ['missed-attacks', 'failed-saves']
          }
        ],
        encounterStatus: 'players-struggling',
        timeInCombat: 45, // minutes
        challengeRating: 'too-high'
      }

      const adjustmentResponse = await request('http://localhost:5678')
        .post(`/api/campaigns/${campaign.id}/difficulty/adjust`)
        .set('Authorization', `Bearer ${sessions.dm.token}`)
        .send(performanceData)
        .expect(200)

      expect(adjustmentResponse.body).to.have.property('recommendations')
      expect(adjustmentResponse.body).to.have.property('adjustments')

      const adjustments = adjustmentResponse.body.adjustments
      expect(adjustments).to.include.suggestions

      interventions.push({
        type: 'difficulty-adjustment',
        timestamp: new Date(),
        details: adjustments
      })

      perfMonitor.endTimer('difficulty-monitoring')
    })

    it('should apply difficulty changes in real-time', async function() {
      perfMonitor.startTimer('real-time-difficulty')

      const difficultyChanges = {
        type: 'reduce-challenge',
        modifications: [
          {
            target: 'enemy-health',
            change: 'reduce-by-25%',
            reason: 'player-struggling'
          },
          {
            target: 'add-bonus-action',
            change: 'healing-opportunity',
            reason: 'balance-encounter'
          }
        ]
      }

      await new Promise(resolve => {
        websockets.dm.emit('apply-difficulty-changes', difficultyChanges)

        websockets.dm.on('difficulty-changes-applied', (data) => {
          expect(data.modifications).to.have.length(2)
          resolve()
        })
      })

      // Players should notice changes
      for (const username of ['player1', 'player2']) {
        await new Promise(resolve => {
          websockets[username].once('combat-balanced', (data) => {
            expect(data.difficulty).to.equal('adjusted')
            resolve()
          })
        })
      }

      perfMonitor.endTimer('real-time-difficulty')
    })
  })

  describe('Story Progression and Plot Management', function() {
    it('should track story progression and milestones', async function() {
      perfMonitor.startTimer('story-tracking')

      const progressionData = {
        chapter: 'arrival-in-barovia',
        milestones: [
          {
            id: 'village-introduction',
            completed: true,
            timestamp: new Date(),
            impact: 'players-aware-of-danger'
          },
          {
            id: 'first-strahd-encounter',
            completed: true,
            timestamp: new Date(),
            impact: 'personal-villain-established'
          }
        ],
        consequences: [
          {
            type: 'world-change',
            description: 'Strahd now aware of player presence',
            effects: ['increased-patrols', 'magical-surveillance']
          },
          {
            type: 'npc-relationship',
            description: 'Ismark now trusts players',
            effects: ['information-sharing', 'potential-ally']
          }
        ]
      }

      const response = await request('http://localhost:5678')
        .post(`/api/campaigns/${campaign.id}/story/progression`)
        .set('Authorization', `Bearer ${sessions.dm.token}`)
        .send(progressionData)
        .expect(200)

      expect(response.body).to.have.property('chapterProgress')
      expect(response.body).to.have.property('unlockedContent')

      perfMonitor.endTimer('story-tracking')
    })

    it('should dynamically adjust story based on player choices', async function() {
      perfMonitor.startTimer('dynamic-story-adjustment')

      const playerChoice = {
        playerId: 'player1',
        choice: 'spare-the-npc',
        context: 'mercy-vs-revenge',
        impact: 'unexpected-compassion',
        consequences: {
          immediate: 'npc-becomes-ally',
          longTerm: 'reputation-as-merciful',
          branches: ['peaceful-resolution', 'unexpected-help']
        }
      }

      const storyAdjustment = await request('http://localhost:5678')
        .post(`/api/campaigns/${campaign.id}/story/adjust`)
        .set('Authorization', `Bearer ${sessions.dm.token}`)
        .send(playerChoice)
        .expect(200)

      expect(storyAdjustment.body).to.have.property('newQuests')
      expect(storyAdjustment.body).to.have.property('modifiedNPCs')
      expect(storyAdjustment.body).to.have.property('storyBranches')

      interventions.push({
        type: 'story-adjustment',
        timestamp: new Date(),
        details: storyAdjustment.body
      })

      perfMonitor.endTimer('dynamic-story-adjustment')
    })
  })

  describe('DM Tools and Utilities', function() {
    it('should provide comprehensive player monitoring', async function() {
      perfMonitor.startTimer('player-monitoring')

      const monitoringData = await request('http://localhost:5678')
        .get(`/api/campaigns/${campaign.id}/players/monitor`)
        .set('Authorization', `Bearer ${sessions.dm.token}`)
        .expect(200)

      expect(monitoringData.body).to.have.property('players')
      expect(monitoringData.body.players).to.be.an('array')

      for (const player of monitoringData.body.players) {
        expect(player).to.have.property('status')
        expect(player).to.have.property('connectionQuality')
        expect(player).to.have.property('activity')
      }

      perfMonitor.endTimer('player-monitoring')
    })

    it('should generate campaign analytics and insights', async function() {
      perfMonitor.startTimer('campaign-analytics')

      const analyticsResponse = await request('http://localhost:5678')
        .get(`/api/campaigns/${campaign.id}/analytics`)
        .set('Authorization', `Bearer ${sessions.dm.token}`)
        .expect(200)

      const analytics = analyticsResponse.body

      expect(analytics).to.have.property('sessionStats')
      expect(analytics).to.have.property('playerEngagement')
      expect(analytics).to.have.property('storyProgression')
      expect(analytics).to.have.property('combatBalance')
      expect(analytics).to.have.property('recommendations')

      // Validate analytics quality
      expect(analytics.sessionStats.totalTime).to.be.above(0)
      expect(analytics.playerEngagement.averageParticipation).to.be.within(0, 100)

      perfMonitor.endTimer('campaign-analytics')
    })

    it('should provide intervention history and rollback capability', async function() {
      perfMonitor.startTimer('intervention-history')

      const historyResponse = await request('http://localhost:5678')
        .get(`/api/campaigns/${campaign.id}/interventions`)
        .set('Authorization', `Bearer ${sessions.dm.token}`)
        .expect(200)

      expect(historyResponse.body).to.have.property('interventions')
      expect(historyResponse.body.interventions).to.be.an('array')

      // Verify our recorded interventions are present
      const interventionTypes = historyResponse.body.interventions.map(i => i.type)
      expect(interventionTypes).to.include.members([
        'location-creation',
        'environmental-change',
        'dynamic-encounter',
        'npc-control'
      ])

      perfMonitor.endTimer('intervention-history')
    })
  })

  describe('Campaign Conclusion and Export', function() {
    it('should save complete campaign state', async function() {
      perfMonitor.startTimer('campaign-save')

      const campaignState = {
        sessionSummary: {
          duration: 180, // minutes
          majorEvents: interventions.map(i => i.type),
          playerAchievements: ['survived-strahd', 'made-ally', 'completed-quest'],
          storyProgress: 'chapter-1-complete'
        },
        worldState: {
          locationsModified: 2,
          npcsChanged: 3,
          itemsCreated: 5,
          secretsDiscovered: 2
        },
        playerStates: {
          totalExperienceGained: 500,
          itemsAcquired: 3,
          relationshipsFormed: 2,
          traumasAcquired: 1
        }
      }

      const saveResponse = await request('http://localhost:5678')
        .post(`/api/campaigns/${campaign.id}/save`)
        .set('Authorization', `Bearer ${sessions.dm.token}`)
        .send(campaignState)
        .expect(200)

      expect(saveResponse.body).to.have.property('saveId')
      expect(saveResponse.body).to.have.property('timestamp')

      perfMonitor.endTimer('campaign-save')
    })

    it('should export campaign for future use', async function() {
      perfMonitor.startTimer('campaign-export')

      const exportOptions = {
        format: 'json',
        includePlayerData: true,
        includeInterventionHistory: true,
        includeAnalytics: true,
        compress: false
      }

      const exportResponse = await request('http://localhost:5678')
        .post(`/api/campaigns/${campaign.id}/export`)
        .set('Authorization', `Bearer ${sessions.dm.token}`)
        .send(exportOptions)
        .expect(200)

      expect(exportResponse.body).to.have.property('exportId')
      expect(exportResponse.body).to.have.property('downloadUrl')
      expect(exportResponse.body).to.have.property('size')

      perfMonitor.endTimer('campaign-export')
    })
  })

  describe('System Performance and Reliability', function() {
    it('should maintain performance under multiple DM interventions', async function() {
      perfMonitor.startTimer('performance-validation')

      // Simulate rapid successive interventions
      const rapidInterventions = [
        { type: 'spawn-enemy', data: { name: 'skeleton', count: 3 } },
        { type: 'change-weather', data: { condition: 'foggy' } },
        { type: 'add-clue', data: { description: 'mysterious-note' } },
        { type: 'trigger-event', data: { name: 'castle-bell-rings' } }
      ]

      const startTime = Date.now()

      for (const intervention of rapidInterventions) {
        await new Promise(resolve => {
          websockets.dm.emit('dm-intervention', intervention)
          websockets.dm.on('intervention-applied', resolve)
        })
      }

      const totalTime = Date.now() - startTime
      expect(totalTime).to.be.below(5000) // Should complete within 5 seconds

      perfMonitor.endTimer('performance-validation')
    })

    it('should handle DM disconnection gracefully', async function() {
      perfMonitor.startTimer('dm-disconnection-handling')

      // Disconnect DM
      websockets.dm.disconnect()

      // Players should receive notification
      for (const username of ['player1', 'player2']) {
        await new Promise(resolve => {
          websockets[username].once('dm-disconnected', (data) => {
            expect(data.message).to.include('DM has disconnected')
            resolve()
          })
        })
      }

      // Reconnect DM
      websockets.dm = io('http://localhost:5678', {
        transports: ['websocket'],
        auth: { token: sessions.dm.token }
      })

      await new Promise(resolve => websockets.dm.on('connect', resolve))

      // Players should receive reconnection notification
      for (const username of ['player1', 'player2']) {
        await new Promise(resolve => {
          websockets[username].once('dm-reconnected', resolve)
        })
      }

      perfMonitor.endTimer('dm-disconnection-handling')
    })
  })
})