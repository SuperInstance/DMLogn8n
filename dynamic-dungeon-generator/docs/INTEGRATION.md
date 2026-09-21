# Integration Guide

Complete integration guide for connecting the Dynamic Dungeon Generator with other DMlogn8n systems and external services.

## Table of Contents
1. [System Architecture](#system-architecture)
2. [n8n Workflow Integration](#n8n-workflow-integration)
3. [Combat System Integration](#combat-system-integration)
4. [Quest Generator Integration](#quest-generator-integration)
5. [World State Management](#world-state-management)
6. [Real-time Updates](#real-time-updates)
7. [Database Integration](#database-integration)
8. [External Service Integration](#external-service-integration)
9. [Custom Middleware](#custom-middleware)
10. [Testing Integrations](#testing-integrations)

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   DM Dashboard  │◄──►│ Dungeon Generator │◄──►│  Combat System  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐              │
         └──────────────►│   n8n Workflows   │◄─────────────┘
                        └──────────────────┘
                                 │
                    ┌──────────────────┐
                    │ Quest Generator  │
                    └──────────────────┘
                                 │
                    ┌──────────────────┐
                    │ World State Mgmt  │
                    └──────────────────┘
```

## n8n Workflow Integration

### Setting up n8n

1. **Install n8n**
```bash
npm install n8n -g
n8n start
```

2. **Import Workflows**
- Navigate to n8n web interface
- Click "Import from file"
- Select workflow files from `/workflows/` directory

3. **Configure Webhooks**
- Set webhook URLs to point to your Dungeon Generator instance
- Example: `http://localhost:3001/webhook/dungeon-generate`

### Available Workflows

#### 1. Dungeon Generation Workflow
**File**: `/workflows/generation/dungeon-generation-workflow.json`

**Triggers**:
- Webhook trigger for generation requests
- Validation and error handling
- Integration with combat and quest systems

**Flow**:
1. Receive generation request
2. Validate parameters
3. Generate dungeon
4. Update world state
5. Generate related quests
6. Prepare combat encounters
7. Log generation event

**Configuration**:
```json
{
  "webhook": {
    "path": "dungeon-generate",
    "httpMethod": "POST"
  },
  "validation": {
    "enabled": true,
    "strictMode": false
  },
  "integrations": {
    "combatSystem": {
      "enabled": true,
      "url": "http://localhost:3002/api/combat"
    },
    "questGenerator": {
      "enabled": true,
      "url": "http://localhost:3003/api/quests"
    },
    "worldState": {
      "enabled": true,
      "url": "http://localhost:3004/api/world"
    }
  }
}
```

#### 2. Dungeon Monitoring Workflow
**File**: `/workflows/management/dungeon-monitoring-workflow.json`

**Schedule**: Every 15 minutes

**Monitoring Tasks**:
- Health checks
- Performance metrics
- Error tracking
- Automated cleanup

**Alerting**:
- Telegram notifications
- Email alerts
- Slack integration (configurable)

#### 3. DM Dashboard Integration
**File**: `/workflows/integration/dm-dashboard-integration.json`

**Actions**:
- Generate dungeons
- Modify existing dungeons
- Export in various formats
- Visualize dungeons
- List and manage dungeons

### Custom Workflow Creation

```javascript
// Example custom workflow node
{
  "parameters": {
    "url": "http://localhost:3001/api/dungeons/generate",
    "sendBody": true,
    "specifyBody": "json",
    "jsonBody": "={{$node[\"Webhook\"].json[\"body\"][\"parameters\"]}}",
    "options": {
      "timeout": 60000,
      "retry": {
        "enabled": true,
        "maxAttempts": 3
      }
    }
  },
  "name": "Generate Dungeon",
  "type": "n8n-nodes-base.httpRequest"
}
```

## Combat System Integration

### Preparing Combat Encounters

```javascript
/**
 * Send dungeon data to combat system for encounter preparation
 */
async function prepareCombatEncounters(dungeonId) {
  try {
    // Get dungeon data
    const dungeonResponse = await fetch(
      `http://localhost:3001/api/dungeons/${dungeonId}`
    );
    const dungeon = await dungeonResponse.json();

    // Prepare combat data
    const combatData = {
      dungeonId: dungeon.id,
      theme: dungeon.metadata.theme,
      difficulty: dungeon.metadata.difficulty,
      encounters: dungeon.floors.flatMap(floor =>
        floor.spawns.map(spawn => ({
          id: spawn.id,
          type: spawn.type,
          count: spawn.count || 1,
          floor: floor.floor,
          location: { x: spawn.x, y: spawn.y },
          difficulty: spawn.difficulty || dungeon.metadata.difficulty,
          ai: spawn.ai || 'default'
        }))
      ),
      bosses: dungeon.floors.flatMap(floor =>
        (floor.bosses || []).map(boss => ({
          id: boss.id,
          type: boss.type,
          floor: floor.floor,
          room: boss.room,
          mechanics: boss.mechanics || [],
          phases: boss.phases || 1,
          difficulty: boss.difficulty || dungeon.metadata.difficulty + 2
        }))
      ),
      environment: {
        lighting: dungeon.floors.map(floor => floor.lighting),
        weather: dungeon.floors.map(floor => floor.weather),
        hazards: dungeon.floors.flatMap(floor => floor.traps || [])
      }
    };

    // Send to combat system
    const combatResponse = await fetch(
      'http://localhost:3002/api/combat/prepare-encounters',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(combatData)
      }
    );

    return await combatResponse.json();

  } catch (error) {
    console.error('Failed to prepare combat encounters:', error);
    throw error;
  }
}
```

### Real-time Combat Updates

```javascript
/**
 * Listen for combat events and update dungeon state
 */
class CombatIntegration {
  constructor() {
    this.combatSocket = new WebSocket('ws://localhost:3002/combat-events');
    this.setupEventHandlers();
  }

  setupEventHandlers() {
    this.combatSocket.onmessage = (event) => {
      const combatEvent = JSON.parse(event.data);
      this.handleCombatEvent(combatEvent);
    };
  }

  async handleCombatEvent(event) {
    switch (event.type) {
      case 'encounter_started':
        await this.onEncounterStarted(event);
        break;
      case 'enemy_defeated':
        await this.onEnemyDefeated(event);
        break;
      case 'trap_triggered':
        await this.onTrapTriggered(event);
        break;
      case 'boss_defeated':
        await this.onBossDefeated(event);
        break;
    }
  }

  async onEncounterStarted(event) {
    // Update dungeon state to mark encounter as active
    await this.updateDungeonState(event.dungeonId, {
      encounterActive: event.encounterId,
      floor: event.floor,
      location: event.location
    });
  }

  async onEnemyDefeated(event) {
    // Remove defeated enemy from dungeon spawns
    await this.removeEnemyFromDungeon(event.dungeonId, event.enemyId);

    // Trigger any post-defeat events
    await this.triggerDefeatEvents(event.dungeonId, event.enemyId);
  }
}
```

## Quest Generator Integration

### Automatic Quest Generation

```javascript
/**
 * Generate quests based on dungeon content
 */
async function generateDungeonQuests(dungeonId, dungeonData) {
  try {
    const questData = {
      dungeonId: dungeonId,
      theme: dungeonData.metadata.theme,
      difficulty: dungeonData.metadata.difficulty,
      playerLevel: dungeonData.metadata.playerLevel,
      floors: dungeonData.dimensions.floors,
      rooms: dungeonData.statistics.totalRooms,
      enemies: dungeonData.floors.flatMap(floor => floor.spawns || []),
      bosses: dungeonData.floors.flatMap(floor => floor.bosses || []),
      treasures: dungeonData.floors.flatMap(floor => floor.loot || []),
      puzzles: dungeonData.floors.flatMap(floor => floor.puzzles || []),
      secrets: dungeonData.floors.flatMap(floor => floor.secrets || [])
    };

    // Generate main quest based on boss
    const mainQuests = await generateMainQuests(questData);

    // Generate side quests based on rooms and treasures
    const sideQuests = await generateSideQuests(questData);

    // Generate discovery quests for secrets
    const discoveryQuests = await generateDiscoveryQuests(questData);

    const allQuests = [...mainQuests, ...sideQuests, ...discoveryQuests];

    // Send quests to quest generator
    const questResponse = await fetch(
      'http://localhost:3003/api/quests/create-batch',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quests: allQuests,
          campaignId: dungeonData.metadata.campaignId
        })
      }
    );

    return await questResponse.json();

  } catch (error) {
    console.error('Failed to generate quests:', error);
    throw error;
  }
}

async function generateMainQuests(questData) {
  const quests = [];

  // Generate quest for each boss
  for (const boss of questData.bosses) {
    quests.push({
      type: 'boss_defeat',
      title: `Defeat the ${boss.type}`,
      description: `Venture into the dungeon and defeat the ${boss.type} on floor ${boss.floor}`,
      difficulty: boss.difficulty,
      location: { dungeonId: questData.dungeonId, floor: boss.floor, room: boss.room },
      objectives: [
        { type: 'defeat', target: boss.id, count: 1 }
      ],
      rewards: {
        experience: boss.difficulty * 1000,
        gold: boss.difficulty * 500,
        items: boss.loot || []
      },
      requirements: {
        minLevel: Math.max(1, questData.playerLevel - 2),
        partySize: Math.min(6, Math.max(2, Math.floor(boss.difficulty / 2)))
      }
    });
  }

  return quests;
}
```

### Quest Progress Tracking

```javascript
/**
 * Track quest progress based on dungeon events
 */
class QuestTracker {
  constructor() {
    this.activeQuests = new Map();
    this.setupProgressTracking();
  }

  setupProgressTracking() {
    // Listen to dungeon events
    this.dungeonEvents.on('enemy_defeated', (event) => {
      this.updateQuestProgress('enemy_defeat', event);
    });

    this.dungeonEvents.on('treasure_found', (event) => {
      this.updateQuestProgress('treasure_acquisition', event);
    });

    this.dungeonEvents.on('room_explored', (event) => {
      this.updateQuestProgress('exploration', event);
    });
  }

  async updateQuestProgress(objectiveType, event) {
    // Find relevant quests
    const relevantQuests = Array.from(this.activeQuests.values())
      .filter(quest => quest.objectives.some(obj => obj.type === objectiveType));

    for (const quest of relevantQuests) {
      const objective = quest.objectives.find(obj => obj.type === objectiveType);

      if (objective) {
        objective.progress = (objective.progress || 0) + 1;

        // Check if quest is complete
        if (objective.progress >= objective.count) {
          objective.completed = true;

          if (quest.objectives.every(obj => obj.completed)) {
            await this.completeQuest(quest.id);
          }
        }

        // Update quest in quest system
        await this.updateQuestInSystem(quest);
      }
    }
  }
}
```

## World State Management

### Updating World State

```javascript
/**
 * Update world state when dungeons are created or modified
 */
class WorldStateManager {
  constructor() {
    this.worldStateUrl = 'http://localhost:3004/api/world';
  }

  async onDungeonCreated(dungeon) {
    const worldUpdate = {
      type: 'dungeon_created',
      timestamp: new Date().toISOString(),
      data: {
        dungeonId: dungeon.id,
        name: this.generateDungeonName(dungeon),
        theme: dungeon.metadata.theme,
        difficulty: dungeon.metadata.difficulty,
        location: await this.assignDungeonLocation(dungeon),
        description: this.generateDungeonDescription(dungeon),
        rumors: this.generateDungeonRumors(dungeon)
      }
    };

    await this.sendWorldUpdate(worldUpdate);
  }

  async onDungeonModified(dungeon, modifications) {
    const worldUpdate = {
      type: 'dungeon_modified',
      timestamp: new Date().toISOString(),
      data: {
        dungeonId: dungeon.id,
        modifications: modifications,
        lastModified: new Date().toISOString()
      }
    };

    await this.sendWorldUpdate(worldUpdate);
  }

  async onDungeonExplored(dungeonId, explorationData) {
    const worldUpdate = {
      type: 'dungeon_explored',
      timestamp: new Date().toISOString(),
      data: {
        dungeonId: dungeonId,
        exploredRooms: explorationData.rooms,
        defeatedEnemies: explorationData.enemies,
        foundTreasure: explorationData.treasure,
        discoveredSecrets: explorationData.secrets,
        playerLevel: explorationData.playerLevel
      }
    };

    await this.sendWorldUpdate(worldUpdate);
  }

  async sendWorldUpdate(update) {
    try {
      const response = await fetch(this.worldStateUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(update)
      });

      if (!response.ok) {
        throw new Error(`World state update failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to update world state:', error);
      throw error;
    }
  }

  generateDungeonName(dungeon) {
    const themes = {
      classic: ['Ancient Crypt', 'Forgotten Temple', 'Abandoned Keep'],
      undeadCrypt: ['Crypt of Eternal Night', 'Necropolis of Doom', 'Tomb of the Damned'],
      dragonLair: ['Dragon\'s Peak', 'Inferno Caverns', 'The Scorched Lair'],
      wizardTower: ['Tower of Mysteries', 'Arcane Spire', 'Wizard\'s Retreat']
    };

    const names = themes[dungeon.metadata.theme] || themes.classic;
    return names[Math.floor(Math.random() * names.length)];
  }

  async assignDungeonLocation(dungeon) {
    // Get available locations from world state
    const locationsResponse = await fetch(`${this.worldStateUrl}/locations`);
    const { locations } = await locationsResponse.json();

    // Find suitable location based on theme and difficulty
    const suitableLocations = locations.filter(loc =>
      loc.type === 'dungeon' &&
      loc.difficulty === dungeon.metadata.difficulty &&
      loc.theme === dungeon.metadata.theme
    );

    if (suitableLocations.length > 0) {
      return suitableLocations[0];
    }

    // Create new location
    return await this.createDungeonLocation(dungeon);
  }

  async createDungeonLocation(dungeon) {
    const locationData = {
      name: this.generateDungeonName(dungeon),
      type: 'dungeon',
      theme: dungeon.metadata.theme,
      difficulty: dungeon.metadata.difficulty,
      coordinates: this.generateCoordinates(),
      description: this.generateDungeonDescription(dungeon),
      dungeonId: dungeon.id
    };

    const response = await fetch(`${this.worldStateUrl}/locations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(locationData)
    });

    return await response.json();
  }
}
```

## Real-time Updates

### WebSocket Integration

```javascript
/**
 * Real-time dungeon updates and notifications
 */
class RealtimeManager {
  constructor() {
    this.io = require('socket.io')(server, {
      cors: {
        origin: "*",
        methods: ["GET", "POST"]
      }
    });
    this.setupSocketHandlers();
  }

  setupSocketHandlers() {
    this.io.on('connection', (socket) => {
      console.log('Client connected:', socket.id);

      // Handle dungeon generation requests
      socket.on('generate-dungeon', async (params) => {
        try {
          socket.emit('generation-started');

          const dungeon = await this.dungeonGenerator.generate({
            ...params,
            onProgress: (progress) => {
              socket.emit('generation-progress', progress);
            }
          });

          socket.emit('generation-complete', dungeon);
        } catch (error) {
          socket.emit('generation-error', { message: error.message });
        }
      });

      // Handle real-time dungeon modifications
      socket.on('modify-dungeon', async (params) => {
        try {
          const result = await this.dungeonGenerator.modifyDungeon(params);
          socket.emit('dungeon-modified', result);

          // Notify other clients
          socket.broadcast.emit('dungeon-updated', {
            dungeonId: params.dungeonId,
            modifications: params.modifications,
            timestamp: new Date().toISOString()
          });
        } catch (error) {
          socket.emit('modification-error', { message: error.message });
        }
      });

      // Handle real-time combat updates
      socket.on('combat-event', (event) => {
        // Broadcast to all clients in the same session
        socket.to(event.sessionId).emit('combat-update', event);
      });

      // Handle room exploration
      socket.on('explore-room', async (data) => {
        const roomData = await this.getRoomData(data.dungeonId, data.roomId);
        socket.emit('room-data', roomData);

        // Notify other players
        socket.to(data.sessionId).emit('room-explored', {
          dungeonId: data.dungeonId,
          roomId: data.roomId,
          exploredBy: data.playerId
        });
      });

      socket.on('disconnect', () => {
        console.log('Client disconnected:', socket.id);
      });
    });
  }

  broadcastDungeonUpdate(dungeonId, update) {
    this.io.emit('dungeon-update', {
      dungeonId,
      update,
      timestamp: new Date().toISOString()
    });
  }

  broadcastCombatEvent(event) {
    this.io.emit('combat-event', event);
  }

  broadcastQuestUpdate(questId, update) {
    this.io.emit('quest-update', {
      questId,
      update,
      timestamp: new Date().toISOString()
    });
  }
}
```

### Event Bus Integration

```javascript
/**
 * Central event bus for system-wide communication
 */
class EventBus {
  constructor() {
    this.events = new Map();
    this.middlewares = [];
  }

  // Subscribe to events
  on(eventType, callback) {
    if (!this.events.has(eventType)) {
      this.events.set(eventType, []);
    }
    this.events.get(eventType).push(callback);
  }

  // Emit events
  async emit(eventType, data) {
    const callbacks = this.events.get(eventType) || [];

    // Apply middlewares
    let processedData = data;
    for (const middleware of this.middlewares) {
      processedData = await middleware(eventType, processedData);
    }

    // Execute callbacks
    const promises = callbacks.map(callback =>
      Promise.resolve(callback(processedData))
    );

    await Promise.all(promises);
  }

  // Add middleware
  use(middleware) {
    this.middlewares.push(middleware);
  }

  // Remove event listeners
  off(eventType, callback) {
    if (this.events.has(eventType)) {
      const callbacks = this.events.get(eventType);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }
}

// Usage example
const eventBus = new EventBus();

// Listen for dungeon generation
eventBus.on('dungeon:generated', async (dungeon) => {
  // Update world state
  await worldStateManager.onDungeonCreated(dungeon);

  // Generate quests
  await questGenerator.generateDungeonQuests(dungeon.id, dungeon);

  // Prepare combat encounters
  await combatSystem.prepareEncounters(dungeon);
});

// Listen for combat events
eventBus.on('combat:enemy_defeated', async (event) => {
  // Update dungeon state
  await dungeonManager.removeEnemy(event.dungeonId, event.enemyId);

  // Update quest progress
  await questTracker.updateProgress(event);

  // Check for triggered events
  await eventManager.checkTriggeredEvents(event);
});

// Add logging middleware
eventBus.use(async (eventType, data) => {
  console.log(`Event: ${eventType}`, data);
  return data;
});
```

## Database Integration

### MongoDB Integration

```javascript
/**
 * MongoDB integration for persistent dungeon storage
 */
class DungeonRepository {
  constructor() {
    this.MongoClient = require('mongodb').MongoClient;
    this.client = null;
    this.db = null;
    this.collection = null;
  }

  async connect() {
    this.client = new MongoClient(process.env.MONGODB_URI);
    await this.client.connect();
    this.db = this.client.db('dungeon_generator');
    this.collection = this.db.collection('dungeons');
  }

  async saveDungeon(dungeon) {
    try {
      const result = await this.collection.insertOne({
        ...dungeon,
        createdAt: new Date(),
        updatedAt: new Date()
      });
      return result.insertedId;
    } catch (error) {
      console.error('Failed to save dungeon:', error);
      throw error;
    }
  }

  async getDungeon(dungeonId) {
    try {
      const dungeon = await this.collection.findOne({ _id: dungeonId });
      return dungeon;
    } catch (error) {
      console.error('Failed to get dungeon:', error);
      throw error;
    }
  }

  async updateDungeon(dungeonId, updates) {
    try {
      const result = await this.collection.updateOne(
        { _id: dungeonId },
        {
          $set: {
            ...updates,
            updatedAt: new Date()
          }
        }
      );
      return result.modifiedCount > 0;
    } catch (error) {
      console.error('Failed to update dungeon:', error);
      throw error;
    }
  }

  async searchDungeons(query) {
    try {
      const dungeons = await this.collection
        .find(query)
        .sort({ createdAt: -1 })
        .limit(50)
        .toArray();
      return dungeons;
    } catch (error) {
      console.error('Failed to search dungeons:', error);
      throw error;
    }
  }

  async getDungeonStatistics() {
    try {
      const stats = await this.collection.aggregate([
        {
          $group: {
            _id: null,
            totalDungeons: { $sum: 1 },
            averageDifficulty: { $avg: '$metadata.difficulty' },
            popularThemes: { $push: '$metadata.theme' },
            averageGenerationTime: { $avg: '$generationTime' }
          }
        }
      ]).toArray();
      return stats[0] || {};
    } catch (error) {
      console.error('Failed to get statistics:', error);
      throw error;
    }
  }
}
```

### Redis Integration (Caching)

```javascript
/**
 * Redis integration for caching and session management
 */
class CacheManager {
  constructor() {
    this.redis = require('redis').createClient({
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379
    });
  }

  async cacheDungeon(dungeonId, dungeon, ttl = 3600) {
    const key = `dungeon:${dungeonId}`;
    await this.redis.setex(key, ttl, JSON.stringify(dungeon));
  }

  async getCachedDungeon(dungeonId) {
    const key = `dungeon:${dungeonId}`;
    const cached = await this.redis.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  async cacheGenerationProgress(sessionId, progress) {
    const key = `progress:${sessionId}`;
    await this.redis.setex(key, 300, JSON.stringify(progress));
  }

  async getGenerationProgress(sessionId) {
    const key = `progress:${sessionId}`;
    const cached = await this.redis.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  async cacheSessionData(sessionId, data) {
    const key = `session:${sessionId}`;
    await this.redis.setex(key, 7200, JSON.stringify(data));
  }

  async getSessionData(sessionId) {
    const key = `session:${sessionId}`;
    const cached = await this.redis.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  async invalidateCache(pattern) {
    const keys = await this.redis.keys(pattern);
    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
  }
}
```

## External Service Integration

### Discord Bot Integration

```javascript
/**
 * Discord bot for dungeon generation commands
 */
const { Client, GatewayIntentBits } = require('discord.js');

class DiscordDungeonBot {
  constructor(dungeonGenerator) {
    this.client = new Client({
      intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
      ]
    });
    this.dungeonGenerator = dungeonGenerator;
    this.setupCommands();
  }

  setupCommands() {
    this.client.on('messageCreate', async (message) => {
      if (!message.content.startsWith('!dungeon')) return;

      const args = message.content.slice(9).trim().split(' ');
      const command = args.shift().toLowerCase();

      switch (command) {
        case 'generate':
          await this.handleGenerateCommand(message, args);
          break;
        case 'list':
          await this.handleListCommand(message);
          break;
        case 'themes':
          await this.handleThemesCommand(message);
          break;
        case 'help':
          await this.handleHelpCommand(message);
          break;
      }
    });
  }

  async handleGenerateCommand(message, args) {
    try {
      const params = this.parseGenerationArgs(args);

      await message.reply('🏰 Generating your dungeon... This may take a moment!');

      const dungeon = await this.dungeonGenerator.generate(params);

      const embed = {
        title: '🏰 Dungeon Generated!',
        description: `A ${params.theme} dungeon has been created for you!`,
        fields: [
          { name: 'Theme', value: params.theme, inline: true },
          { name: 'Difficulty', value: params.difficulty.toString(), inline: true },
          { name: 'Floors', value: params.floors.toString(), inline: true },
          { name: 'Rooms', value: dungeon.statistics.totalRooms.toString(), inline: true },
          { name: 'Enemies', value: dungeon.statistics.totalEnemies.toString(), inline: true },
          { name: 'Treasures', value: dungeon.statistics.totalLoot.toString(), inline: true },
          { name: 'Dungeon ID', value: dungeon.id, inline: false }
        ],
        color: 0x00ff00,
        timestamp: new Date().toISOString()
      };

      await message.channel.send({ embeds: [embed] });

    } catch (error) {
      await message.reply(`❌ Error generating dungeon: ${error.message}`);
    }
  }

  parseGenerationArgs(args) {
    const params = {
      algorithm: 'roomCorridor',
      theme: 'classic',
      width: 50,
      height: 50,
      floors: 1,
      difficulty: 1,
      playerLevel: 1
    };

    for (let i = 0; i < args.length; i++) {
      const arg = args[i];
      const nextArg = args[i + 1];

      switch (arg) {
        case '--theme':
          if (nextArg) params.theme = nextArg;
          break;
        case '--difficulty':
          if (nextArg) params.difficulty = parseInt(nextArg);
          break;
        case '--floors':
          if (nextArg) params.floors = parseInt(nextArg);
          break;
        case '--algorithm':
          if (nextArg) params.algorithm = nextArg;
          break;
        case '--size':
          if (nextArg) {
            const [width, height] = nextArg.split('x').map(n => parseInt(n));
            if (width) params.width = width;
            if (height) params.height = height;
          }
          break;
      }
    }

    return params;
  }

  start() {
    this.client.login(process.env.DISCORD_TOKEN);
  }
}
```

## Testing Integrations

### Integration Tests

```javascript
/**
 * Integration tests for dungeon generator with external systems
 */
const request = require('supertest');
const app = require('../src/app');

describe('Dungeon Generator Integration', () => {
  let dungeonId;
  let combatSystemStub;
  let questGeneratorStub;
  let worldStateStub;

  beforeAll(() => {
    // Mock external services
    combatSystemStub = jest.fn();
    questGeneratorStub = jest.fn();
    worldStateStub = jest.fn();
  });

  test('should generate dungeon and integrate with combat system', async () => {
    const response = await request(app)
      .post('/api/dungeons/generate')
      .send({
        algorithm: 'roomCorridor',
        theme: 'classic',
        width: 50,
        height: 50,
        floors: 1,
        difficulty: 1,
        playerLevel: 1
      })
      .expect(200);

    dungeonId = response.body.dungeon.id;

    expect(response.body.success).toBe(true);
    expect(response.body.dungeon).toBeDefined();
    expect(response.body.dungeon.statistics.totalRooms).toBeGreaterThan(0);
  });

  test('should prepare combat encounters for generated dungeon', async () => {
    const combatData = {
      dungeonId: dungeonId,
      enemies: expect.any(Array),
      bosses: expect.any(Array)
    };

    // Mock combat system response
    combatSystemStub.mockResolvedValue({ success: true, encounters: [] });

    const result = await prepareCombatEncounters(dungeonId);

    expect(combatSystemStub).toHaveBeenCalledWith(
      expect.objectContaining({
        dungeonId: dungeonId
      })
    );
    expect(result.success).toBe(true);
  });

  test('should generate quests based on dungeon content', async () => {
    // Mock quest generator response
    questGeneratorStub.mockResolvedValue({
      success: true,
      quests: expect.any(Array)
    });

    const dungeon = await getDungeon(dungeonId);
    const result = await generateDungeonQuests(dungeonId, dungeon);

    expect(questGeneratorStub).toHaveBeenCalled();
    expect(result.quests).toBeDefined();
    expect(result.quests.length).toBeGreaterThan(0);
  });

  test('should update world state when dungeon is created', async () => {
    // Mock world state response
    worldStateStub.mockResolvedValue({ success: true });

    const dungeon = await getDungeon(dungeonId);
    const result = await updateWorldState('dungeon_created', dungeon);

    expect(worldStateStub).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'dungeon_created',
        data: expect.objectContaining({
          dungeonId: dungeonId
        })
      })
    );
    expect(result.success).toBe(true);
  });

  test('should handle real-time dungeon modifications', async (done) => {
    const WebSocket = require('ws');
    const ws = new WebSocket('ws://localhost:3001');

    ws.on('open', () => {
      // Send modification request
      ws.send(JSON.stringify({
        type: 'modify-dungeon',
        dungeonId: dungeonId,
        modifications: {
          lighting: { brightness: 0.8 }
        }
      }));
    });

    ws.on('message', (data) => {
      const response = JSON.parse(data);
      expect(response.type).toBe('dungeon-modified');
      ws.close();
      done();
    });
  });

  afterAll(async () => {
    // Cleanup
    await cleanupTestData();
  });
});

async function prepareCombatEncounters(dungeonId) {
  // Mock implementation
  return { success: true, encounters: [] };
}

async function generateDungeonQuests(dungeonId, dungeon) {
  // Mock implementation
  return { success: true, quests: [] };
}

async function updateWorldState(eventType, data) {
  // Mock implementation
  return { success: true };
}

async function getDungeon(dungeonId) {
  // Mock implementation
  return { id: dungeonId, metadata: {}, statistics: {} };
}

async function cleanupTestData() {
  // Cleanup test data
}
```

## Error Handling and Resilience

### Circuit Breaker Pattern

```javascript
/**
 * Circuit breaker for external service calls
 */
class CircuitBreaker {
  constructor(options = {}) {
    this.failureThreshold = options.failureThreshold || 5;
    this.resetTimeout = options.resetTimeout || 60000;
    this.monitoringPeriod = options.monitoringPeriod || 10000;

    this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
    this.failureCount = 0;
    this.lastFailureTime = null;
    this.successCount = 0;
  }

  async execute(operation) {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailureTime > this.resetTimeout) {
        this.state = 'HALF_OPEN';
        this.successCount = 0;
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  onSuccess() {
    this.failureCount = 0;
    if (this.state === 'HALF_OPEN') {
      this.successCount++;
      if (this.successCount >= 3) {
        this.state = 'CLOSED';
      }
    }
  }

  onFailure() {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.failureCount >= this.failureThreshold) {
      this.state = 'OPEN';
    }
  }
}

// Usage
const combatSystemCircuit = new CircuitBreaker({
  failureThreshold: 3,
  resetTimeout: 30000
});

async function callCombatSystem(data) {
  return await combatSystemCircuit.execute(async () => {
    const response = await fetch('http://localhost:3002/api/combat/prepare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error(`Combat system error: ${response.status}`);
    }

    return await response.json();
  });
}
```

## Support and Troubleshooting

### Common Integration Issues

1. **WebSocket Connection Failures**
   - Check firewall settings
   - Verify port availability
   - Ensure proper CORS configuration

2. **Database Connection Issues**
   - Verify connection strings
   - Check network connectivity
   - Ensure proper authentication

3. **n8n Workflow Failures**
   - Check webhook URLs
   - Verify API endpoints are accessible
   - Review workflow logs

4. **Memory Leaks**
   - Monitor memory usage
   - Implement proper cleanup
   - Use connection pooling

### Debug Mode

```javascript
// Enable debug logging
process.env.DEBUG = 'dungeon-generator:*';

// Enable performance monitoring
process.env.PROFILING = 'true';

// Enable detailed error reporting
process.env.VERBOSE_ERRORS = 'true';
```

This comprehensive integration guide provides everything needed to connect the Dynamic Dungeon Generator with other DMlogn8n systems and external services.