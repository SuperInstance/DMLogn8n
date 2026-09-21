const { v4: uuidv4 } = require('uuid');
const _ = require('lodash');
const logger = require('../utils/logger');
const {
  CharacterType,
  SocketEvents,
  EventType,
  CombatStatus
} = require('../../shared/types');

// Active campaigns and their connected clients
const activeCampaigns = new Map();
const clientSessions = new Map();

// Game state management
const gameStates = new Map();

module.exports = (io, socket) => {
  const clientId = socket.id;

  // Client joins a campaign
  socket.on(SocketEvents.JOIN_CAMPAIGN, async (data) => {
    try {
      const { campaignId, userId, isDM } = data;

      if (!campaignId || !userId) {
        socket.emit('error', { message: 'Campaign ID and User ID are required' });
        return;
      }

      // Join campaign room
      socket.join(`campaign:${campaignId}`);

      // Track client session
      clientSessions.set(clientId, {
        campaignId,
        userId,
        isDM: isDM || false,
        joinedAt: new Date()
      });

      // Initialize campaign if not exists
      if (!activeCampaigns.has(campaignId)) {
        activeCampaigns.set(campaignId, {
          id: campaignId,
          clients: new Set(),
          gameState: initializeGameState(campaignId),
          lastActivity: new Date()
        });
      }

      const campaign = activeCampaigns.get(campaignId);
      campaign.clients.add(clientId);

      // Send current game state to client
      socket.emit(SocketEvents.GAME_STATE_UPDATE, campaign.gameState);

      // Notify other clients
      socket.to(`campaign:${campaignId}`).emit('client_joined', {
        userId,
        isDM: isDM || false,
        timestamp: new Date()
      });

      logger.info(`Client ${clientId} joined campaign ${campaignId} as ${isDM ? 'DM' : 'player'}`);

    } catch (error) {
      logger.error('Error in JOIN_CAMPAIGN:', error);
      socket.emit('error', { message: 'Failed to join campaign' });
    }
  });

  // Client leaves a campaign
  socket.on(SocketEvents.LEAVE_CAMPAIGN, (data) => {
    try {
      const session = clientSessions.get(clientId);
      if (!session) return;

      const { campaignId } = session;

      // Leave campaign room
      socket.leave(`campaign:${campaignId}`);

      // Remove from campaign
      const campaign = activeCampaigns.get(campaignId);
      if (campaign) {
        campaign.clients.delete(clientId);

        // Clean up campaign if no clients
        if (campaign.clients.size === 0) {
          activeCampaigns.delete(campaignId);
          gameStates.delete(campaignId);
        }
      }

      // Remove client session
      clientSessions.delete(clientId);

      // Notify remaining clients
      socket.to(`campaign:${campaignId}`).emit('client_left', {
        userId: session.userId,
        timestamp: new Date()
      });

      logger.info(`Client ${clientId} left campaign ${campaignId}`);

    } catch (error) {
      logger.error('Error in LEAVE_CAMPAIGN:', error);
    }
  });

  // Character action
  socket.on(SocketEvents.CHARACTER_ACTION, (data) => {
    try {
      const session = clientSessions.get(clientId);
      if (!session) {
        socket.emit('error', { message: 'Not connected to a campaign' });
        return;
      }

      const { campaignId } = session;
      const campaign = activeCampaigns.get(campaignId);
      if (!campaign) return;

      const action = {
        id: uuidv4(),
        characterId: data.characterId,
        type: data.type,
        description: data.description,
        targetId: data.targetId,
        position: data.position,
        result: data.result,
        timestamp: new Date(),
        userId: session.userId
      };

      // Update game state
      updateGameState(campaignId, 'characterAction', action);

      // Broadcast to all clients in campaign
      io.to(`campaign:${campaignId}`).emit(SocketEvents.CHARACTER_ACTION, action);

      logger.info(`Character action in campaign ${campaignId}:`, action);

    } catch (error) {
      logger.error('Error in CHARACTER_ACTION:', error);
      socket.emit('error', { message: 'Failed to process character action' });
    }
  });

  // Combat start
  socket.on(SocketEvents.COMBAT_START, (data) => {
    try {
      const session = clientSessions.get(clientId);
      if (!session || !session.isDM) {
        socket.emit('error', { message: 'DM privileges required' });
        return;
      }

      const { campaignId } = session;
      const combat = {
        id: uuidv4(),
        locationId: data.locationId,
        participants: data.participants || [],
        initiative: [],
        currentTurn: 0,
        round: 1,
        status: 'active',
        environment: data.environment || {},
        startedAt: new Date(),
        startedBy: session.userId
      };

      // Update game state
      updateGameState(campaignId, 'combatStart', combat);

      // Broadcast to all clients
      io.to(`campaign:${campaignId}`).emit(SocketEvents.COMBAT_START, combat);

      logger.info(`Combat started in campaign ${campaignId}`);

    } catch (error) {
      logger.error('Error in COMBAT_START:', error);
      socket.emit('error', { message: 'Failed to start combat' });
    }
  });

  // Initiative roll
  socket.on(SocketEvents.INITIATIVE_ROLL, (data) => {
    try {
      const session = clientSessions.get(clientId);
      if (!session) return;

      const { campaignId } = session;
      const { characterId, roll } = data;

      const initiativeEntry = {
        characterId,
        roll: roll || Math.floor(Math.random() * 20) + 1,
        modifier: data.modifier || 0,
        total: (roll || Math.floor(Math.random() * 20) + 1) + (data.modifier || 0),
        timestamp: new Date()
      };

      // Update game state
      updateGameState(campaignId, 'initiativeRoll', initiativeEntry);

      // Broadcast to all clients
      io.to(`campaign:${campaignId}`).emit(SocketEvents.INITIATIVE_ROLL, initiativeEntry);

    } catch (error) {
      logger.error('Error in INITIATIVE_ROLL:', error);
      socket.emit('error', { message: 'Failed to process initiative roll' });
    }
  });

  // DM: Inject event
  socket.on(SocketEvents.INJECT_EVENT, (data) => {
    try {
      const session = clientSessions.get(clientId);
      if (!session || !session.isDM) {
        socket.emit('error', { message: 'DM privileges required' });
        return;
      }

      const { campaignId } = session;
      const event = {
        id: uuidv4(),
        type: data.type || EventType.CUSTOM,
        title: data.title,
        description: data.description,
        trigger: data.trigger,
        effects: data.effects || [],
        conditions: data.conditions || [],
        once: data.once || false,
        active: true,
        injectedBy: session.userId,
        injectedAt: new Date(),
        triggeredAt: data.triggerImmediately ? new Date() : null
      };

      // Update game state
      updateGameState(campaignId, 'eventInjection', event);

      // Broadcast to all clients
      io.to(`campaign:${campaignId}`).emit(SocketEvents.INJECT_EVENT, event);

      logger.info(`Event injected in campaign ${campaignId}:`, event.title);

    } catch (error) {
      logger.error('Error in INJECT_EVENT:', error);
      socket.emit('error', { message: 'Failed to inject event' });
    }
  });

  // DM: Spawn creature
  socket.on(SocketEvents.SPAWN_CREATURE, (data) => {
    try {
      const session = clientSessions.get(clientId);
      if (!session || !session.isDM) {
        socket.emit('error', { message: 'DM privileges required' });
        return;
      }

      const { campaignId } = session;
      const creature = {
        id: uuidv4(),
        name: data.name,
        type: CharacterType.MONSTER,
        stats: data.stats || {},
        position: data.position || { x: 0, y: 0 },
        health: data.health || { current: 10, max: 10 },
        status: data.status || 'alive',
        conditions: data.conditions || [],
        abilities: data.abilities || [],
        spawnedBy: session.userId,
        spawnedAt: new Date()
      };

      // Update game state
      updateGameState(campaignId, 'creatureSpawn', creature);

      // Broadcast to all clients
      io.to(`campaign:${campaignId}`).emit(SocketEvents.SPAWN_CREATURE, creature);

      logger.info(`Creature spawned in campaign ${campaignId}:`, creature.name);

    } catch (error) {
      logger.error('Error in SPAWN_CREATURE:', error);
      socket.emit('error', { message: 'Failed to spawn creature' });
    }
  });

  // DM: Modify environment
  socket.on(SocketEvents.MODIFY_ENVIRONMENT, (data) => {
    try {
      const session = clientSessions.get(clientId);
      if (!session || !session.isDM) {
        socket.emit('error', { message: 'DM privileges required' });
        return;
      }

      const { campaignId } = session;
      const modification = {
        locationId: data.locationId,
        changes: data.changes,
        modifiedBy: session.userId,
        modifiedAt: new Date()
      };

      // Update game state
      updateGameState(campaignId, 'environmentModification', modification);

      // Broadcast to all clients
      io.to(`campaign:${campaignId}`).emit(SocketEvents.MODIFY_ENVIRONMENT, modification);

      logger.info(`Environment modified in campaign ${campaignId}`);

    } catch (error) {
      logger.error('Error in MODIFY_ENVIRONMENT:', error);
      socket.emit('error', { message: 'Failed to modify environment' });
    }
  });

  // Campaign save
  socket.on(SocketEvents.CAMPAIGN_SAVE, async (data) => {
    try {
      const session = clientSessions.get(clientId);
      if (!session || !session.isDM) {
        socket.emit('error', { message: 'DM privileges required' });
        return;
      }

      const { campaignId } = session;
      const campaign = activeCampaigns.get(campaignId);

      if (!campaign) {
        socket.emit('error', { message: 'Campaign not found' });
        return;
      }

      // Here you would save to database
      // For now, we'll just acknowledge
      socket.emit('campaign_saved', {
        campaignId,
        savedAt: new Date(),
        success: true
      });

      logger.info(`Campaign ${campaignId} saved`);

    } catch (error) {
      logger.error('Error in CAMPAIGN_SAVE:', error);
      socket.emit('error', { message: 'Failed to save campaign' });
    }
  });

  // Character position update
  socket.on('character_position_update', (data) => {
    try {
      const session = clientSessions.get(clientId);
      if (!session) return;

      const { campaignId } = session;
      const positionUpdate = {
        characterId: data.characterId,
        position: data.position,
        timestamp: new Date(),
        userId: session.userId
      };

      // Update game state
      updateGameState(campaignId, 'positionUpdate', positionUpdate);

      // Broadcast to other clients
      socket.to(`campaign:${campaignId}`).emit('character_position_update', positionUpdate);

    } catch (error) {
      logger.error('Error in character_position_update:', error);
    }
  });

  // Handle disconnect
  socket.on('disconnect', () => {
    try {
      const session = clientSessions.get(clientId);
      if (session) {
        const { campaignId } = session;

        // Remove from campaign
        const campaign = activeCampaigns.get(campaignId);
        if (campaign) {
          campaign.clients.delete(clientId);

          // Clean up campaign if no clients
          if (campaign.clients.size === 0) {
            activeCampaigns.delete(campaignId);
            gameStates.delete(campaignId);
          }
        }

        // Remove client session
        clientSessions.delete(clientId);

        // Notify remaining clients
        socket.to(`campaign:${campaignId}`).emit('client_left', {
          userId: session.userId,
          timestamp: new Date()
        });
      }

      logger.info(`Client ${clientId} disconnected`);

    } catch (error) {
      logger.error('Error in disconnect handler:', error);
    }
  });
};

// Helper functions
function initializeGameState(campaignId) {
  return {
    campaignId,
    characters: new Map(),
    locations: new Map(),
    events: [],
    combat: null,
    timeline: [],
    environment: {},
    sessionActive: false,
    lastUpdated: new Date()
  };
}

function updateGameState(campaignId, type, data) {
  const campaign = activeCampaigns.get(campaignId);
  if (!campaign) return;

  const gameState = campaign.gameState;

  switch (type) {
    case 'characterAction':
      gameState.timeline.push({
        type: 'character_action',
        data,
        timestamp: new Date()
      });
      break;

    case 'combatStart':
      gameState.combat = data;
      gameState.timeline.push({
        type: 'combat_start',
        data,
        timestamp: new Date()
      });
      break;

    case 'initiativeRoll':
      if (gameState.combat) {
        gameState.combat.initiative.push(data);
        gameState.combat.initiative.sort((a, b) => b.total - a.total);
      }
      break;

    case 'eventInjection':
      gameState.events.push(data);
      gameState.timeline.push({
        type: 'event_injected',
        data,
        timestamp: new Date()
      });
      break;

    case 'creatureSpawn':
      if (!gameState.characters) gameState.characters = new Map();
      gameState.characters.set(data.id, data);
      gameState.timeline.push({
        type: 'creature_spawned',
        data,
        timestamp: new Date()
      });
      break;

    case 'environmentModification':
      if (!gameState.environment) gameState.environment = {};
      gameState.environment[data.locationId] = {
        ...gameState.environment[data.locationId],
        ...data.changes,
        lastModified: data.modifiedAt
      };
      gameState.timeline.push({
        type: 'environment_modified',
        data,
        timestamp: new Date()
      });
      break;

    case 'positionUpdate':
      const character = gameState.characters.get(data.characterId);
      if (character) {
        character.position = data.position;
        character.updatedAt = data.timestamp;
      }
      break;
  }

  gameState.lastUpdated = new Date();
  campaign.lastActivity = new Date();
}

// Cleanup inactive campaigns
setInterval(() => {
  const now = new Date();
  for (const [campaignId, campaign] of activeCampaigns.entries()) {
    const inactiveTime = now - campaign.lastActivity;
    // Clean up campaigns inactive for more than 1 hour
    if (inactiveTime > 60 * 60 * 1000 && campaign.clients.size === 0) {
      activeCampaigns.delete(campaignId);
      gameStates.delete(campaignId);
      logger.info(`Cleaned up inactive campaign: ${campaignId}`);
    }
  }
}, 5 * 60 * 1000); // Check every 5 minutes