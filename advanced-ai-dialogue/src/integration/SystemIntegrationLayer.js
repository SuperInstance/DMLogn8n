const EventEmitter = require('events');
const axios = require('axios');
const { WebSocket } = require('ws');

class SystemIntegrationLayer extends EventEmitter {
  constructor(options = {}) {
    super();

    // Integration adapters
    this.adapters = {
      dndBeyond: null,
      roll20: null,
      foundry: null,
      discord: null,
      obsidian: null,
      fantasyGrounds: null,
      custom: new Map()
    };

    // Connection states
    this.connectionStates = new Map();

    // Configuration
    this.options = {
      autoReconnect: options.autoReconnect !== false,
      reconnectInterval: options.reconnectInterval || 5000,
      maxReconnectAttempts: options.maxReconnectAttempts || 5,
      timeout: options.timeout || 10000,
      enableWebhooks: options.enableWebhooks !== false,
      enableRealTimeSync: options.enableRealTimeSync !== false,
      encryptionKey: options.encryptionKey || null,
      ...options
    };

    // Event handlers
    this.eventHandlers = new Map();

    // Data transformers
    this.transformers = {
      character: new CharacterDataTransformer(),
      campaign: new CampaignDataTransformer(),
      conversation: new ConversationDataTransformer(),
      combat: new CombatDataTransformer(),
      inventory: new InventoryDataTransformer()
    };

    // Initialize integrations
    this.initializeIntegrations();

    // Start health monitoring
    this.startHealthMonitoring();
  }

  initializeIntegrations() {
    // Initialize D&D Beyond integration
    if (process.env.DND_BEYOND_API_KEY) {
      this.adapters.dndBeyond = new DNDBeyondAdapter({
        apiKey: process.env.DND_BEYOND_API_KEY,
        baseUrl: 'https://www.dndbeyond.com/api/v1',
        timeout: this.options.timeout
      });

      this.setupAdapterEventHandlers('dndBeyond', this.adapters.dndBeyond);
    }

    // Initialize Roll20 integration
    if (process.env.ROLL20_API_KEY && process.env.ROLL20_CAMPAIGN_ID) {
      this.adapters.roll20 = new Roll20Adapter({
        apiKey: process.env.ROLL20_API_KEY,
        campaignId: process.env.ROLL20_CAMPAIGN_ID,
        baseUrl: 'https://app.roll20.net/api/v1',
        timeout: this.options.timeout
      });

      this.setupAdapterEventHandlers('roll20', this.adapters.roll20);
    }

    // Initialize Foundry VTT integration
    if (process.env.FOUNDRY_URL && process.env.FOUNDRY_API_KEY) {
      this.adapters.foundry = new FoundryAdapter({
        url: process.env.FOUNDRY_URL,
        apiKey: process.env.FOUNDRY_API_KEY,
        timeout: this.options.timeout
      });

      this.setupAdapterEventHandlers('foundry', this.adapters.foundry);
    }

    // Initialize Discord integration
    if (process.env.DISCORD_BOT_TOKEN) {
      this.adapters.discord = new DiscordAdapter({
        botToken: process.env.DISCORD_BOT_TOKEN,
        clientId: process.env.DISCORD_CLIENT_ID,
        timeout: this.options.timeout
      });

      this.setupAdapterEventHandlers('discord', this.adapters.discord);
    }
  }

  setupAdapterEventHandlers(adapterName, adapter) {
    adapter.on('connected', () => {
      this.connectionStates.set(adapterName, { state: 'connected', lastPing: Date.now() });
      this.emit('adapterConnected', { adapter: adapterName, timestamp: new Date().toISOString() });
    });

    adapter.on('disconnected', () => {
      this.connectionStates.set(adapterName, { state: 'disconnected', lastPing: Date.now() });
      this.emit('adapterDisconnected', { adapter: adapterName, timestamp: new Date().toISOString() });

      if (this.options.autoReconnect) {
        this.scheduleReconnect(adapterName);
      }
    });

    adapter.on('dataReceived', (data) => {
      this.handleIncomingData(adapterName, data);
    });

    adapter.on('error', (error) => {
      this.emit('adapterError', { adapter: adapterName, error, timestamp: new Date().toISOString() });
    });
  }

  async handleIncomingData(adapterName, rawData) {
    try {
      // Transform data based on type
      const transformedData = await this.transformIncomingData(adapterName, rawData);

      // Emit transformed data
      this.emit('dataReceived', {
        source: adapterName,
        data: transformedData,
        originalData: rawData,
        timestamp: new Date().toISOString()
      });

      // Route to appropriate handlers
      this.routeDataToHandlers(adapterName, transformedData);

    } catch (error) {
      console.error(`Error handling data from ${adapterName}:`, error);
      this.emit('dataHandlingError', {
        source: adapterName,
        error: error.message,
        data: rawData,
        timestamp: new Date().toISOString()
      });
    }
  }

  async transformIncomingData(adapterName, rawData) {
    const adapter = this.adapters[adapterName];
    if (!adapter || !adapter.dataType) {
      return rawData;
    }

    switch (adapter.dataType) {
      case 'character':
        return this.transformers.character.transformFromAdapter(adapterName, rawData);
      case 'campaign':
        return this.transformers.campaign.transformFromAdapter(adapterName, rawData);
      case 'conversation':
        return this.transformers.conversation.transformFromAdapter(adapterName, rawData);
      case 'combat':
        return this.transformers.combat.transformFromAdapter(adapterName, rawData);
      case 'inventory':
        return this.transformers.inventory.transformFromAdapter(adapterName, rawData);
      default:
        return rawData;
    }
  }

  routeDataToHandlers(source, data) {
    // Route to specific event handlers
    const eventType = this.determineEventType(data);
    const handlers = this.eventHandlers.get(eventType) || [];

    handlers.forEach(handler => {
      try {
        handler(source, data);
      } catch (error) {
        console.error(`Error in event handler for ${eventType}:`, error);
      }
    });

    // Emit generic events
    this.emit(eventType, { source, data, timestamp: new Date().toISOString() });
  }

  determineEventType(data) {
    if (data.type) return data.type;
    if (data.character) return 'characterUpdate';
    if (data.combat) return 'combatUpdate';
    if (data.campaign) return 'campaignUpdate';
    if (data.conversation) return 'conversationUpdate';
    if (data.inventory) return 'inventoryUpdate';
    return 'genericData';
  }

  registerEventHandler(eventType, handler) {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, []);
    }
    this.eventHandlers.get(eventType).push(handler);
  }

  async sendData(adapterName, data, options = {}) {
    try {
      const adapter = this.adapters[adapterName];
      if (!adapter) {
        throw new Error(`Adapter ${adapterName} not found`);
      }

      if (!adapter.isConnected()) {
        throw new Error(`Adapter ${adapterName} is not connected`);
      }

      // Transform data for adapter
      const transformedData = await this.transformOutgoingData(adapterName, data);

      // Send data
      const result = await adapter.sendData(transformedData, options);

      this.emit('dataSent', {
        target: adapterName,
        data: transformedData,
        result,
        timestamp: new Date().toISOString()
      });

      return result;

    } catch (error) {
      console.error(`Error sending data to ${adapterName}:`, error);
      this.emit('dataSendError', {
        target: adapterName,
        error: error.message,
        data,
        timestamp: new Date().toISOString()
      });
      throw error;
    }
  }

  async transformOutgoingData(adapterName, data) {
    const adapter = this.adapters[adapterName];
    if (!adapter || !adapter.dataType) {
      return data;
    }

    switch (adapter.dataType) {
      case 'character':
        return this.transformers.character.transformToAdapter(adapterName, data);
      case 'campaign':
        return this.transformers.campaign.transformToAdapter(adapterName, data);
      case 'conversation':
        return this.transformers.conversation.transformToAdapter(adapterName, data);
      case 'combat':
        return this.transformers.combat.transformToAdapter(adapterName, data);
      case 'inventory':
        return this.transformers.inventory.transformToAdapter(adapterName, data);
      default:
        return data;
    }
  }

  async syncCharacterData(characterId, sourceAdapter, targetAdapters) {
    try {
      // Get character data from source
      const sourceAdapterInstance = this.adapters[sourceAdapter];
      if (!sourceAdapterInstance) {
        throw new Error(`Source adapter ${sourceAdapter} not found`);
      }

      const characterData = await sourceAdapterInstance.getCharacter(characterId);

      // Sync to target adapters
      const syncResults = [];
      for (const targetAdapter of targetAdapters) {
        try {
          const result = await this.sendData(targetAdapter, {
            type: 'character',
            action: 'sync',
            character: characterData
          });
          syncResults.push({ adapter: targetAdapter, success: true, result });
        } catch (error) {
          syncResults.push({ adapter: targetAdapter, success: false, error: error.message });
        }
      }

      this.emit('characterSyncCompleted', {
        characterId,
        source: sourceAdapter,
        targets: targetAdapters,
        results: syncResults,
        timestamp: new Date().toISOString()
      });

      return syncResults;

    } catch (error) {
      console.error('Error syncing character data:', error);
      throw error;
    }
  }

  async syncConversationData(conversationId, targetAdapters) {
    try {
      // This would integrate with the conversation manager
      const conversationManager = require('../core/ContextAwareConversationManager');
      const conversation = conversationManager.getConversation(conversationId);

      if (!conversation) {
        throw new Error(`Conversation ${conversationId} not found`);
      }

      const syncResults = [];
      for (const targetAdapter of targetAdapters) {
        try {
          const result = await this.sendData(targetAdapter, {
            type: 'conversation',
            action: 'sync',
            conversation: conversation
          });
          syncResults.push({ adapter: targetAdapter, success: true, result });
        } catch (error) {
          syncResults.push({ adapter: targetAdapter, success: false, error: error.message });
        }
      }

      this.emit('conversationSyncCompleted', {
        conversationId,
        targets: targetAdapters,
        results: syncResults,
        timestamp: new Date().toISOString()
      });

      return syncResults;

    } catch (error) {
      console.error('Error syncing conversation data:', error);
      throw error;
    }
  }

  async createWebhook(adapterName, endpoint, events) {
    if (!this.options.enableWebhooks) {
      throw new Error('Webhooks are disabled');
    }

    const adapter = this.adapters[adapterName];
    if (!adapter || !adapter.createWebhook) {
      throw new Error(`Adapter ${adapterName} does not support webhooks`);
    }

    try {
      const webhookUrl = `${this.options.webhookBaseUrl}/webhooks/${adapterName}/${endpoint}`;
      const webhook = await adapter.createWebhook(webhookUrl, events);

      this.emit('webhookCreated', {
        adapter: adapterName,
        endpoint,
        webhookUrl,
        events,
        webhook,
        timestamp: new Date().toISOString()
      });

      return webhook;

    } catch (error) {
      console.error(`Error creating webhook for ${adapterName}:`, error);
      throw error;
    }
  }

  async removeWebhook(adapterName, webhookId) {
    const adapter = this.adapters[adapterName];
    if (!adapter || !adapter.removeWebhook) {
      throw new Error(`Adapter ${adapterName} does not support webhooks`);
    }

    try {
      await adapter.removeWebhook(webhookId);

      this.emit('webhookRemoved', {
        adapter: adapterName,
        webhookId,
        timestamp: new Date().toISOString()
      });

    } catch (error) {
      console.error(`Error removing webhook for ${adapterName}:`, error);
      throw error;
    }
  }

  scheduleReconnect(adapterName) {
    const state = this.connectionStates.get(adapterName) || { attempts: 0 };

    if (state.attempts >= this.options.maxReconnectAttempts) {
      this.emit('reconnectFailed', {
        adapter: adapterName,
        attempts: state.attempts,
        timestamp: new Date().toISOString()
      });
      return;
    }

    setTimeout(async () => {
      try {
        const adapter = this.adapters[adapterName];
        if (adapter) {
          await adapter.connect();
          this.connectionStates.set(adapterName, {
            state: 'connecting',
            attempts: state.attempts + 1,
            lastAttempt: Date.now()
          });
        }
      } catch (error) {
        this.connectionStates.set(adapterName, {
          ...state,
          attempts: state.attempts + 1,
          lastAttempt: Date.now()
        });
        this.scheduleReconnect(adapterName);
      }
    }, this.options.reconnectInterval);
  }

  startHealthMonitoring() {
    setInterval(() => {
      this.checkAdapterHealth();
    }, 30000); // Check every 30 seconds
  }

  async checkAdapterHealth() {
    for (const [adapterName, adapter] of Object.entries(this.adapters)) {
      if (!adapter) continue;

      try {
        const isHealthy = await adapter.healthCheck();
        const currentState = this.connectionStates.get(adapterName) || {};

        this.connectionStates.set(adapterName, {
          ...currentState,
          healthy: isHealthy,
          lastHealthCheck: Date.now()
        });

        if (!isHealthy) {
          this.emit('adapterUnhealthy', {
            adapter: adapterName,
            timestamp: new Date().toISOString()
          });
        }

      } catch (error) {
        this.connectionStates.set(adapterName, {
          ...this.connectionStates.get(adapterName),
          healthy: false,
          lastHealthCheck: Date.now(),
          error: error.message
        });

        this.emit('adapterHealthCheckFailed', {
          adapter: adapterName,
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    }
  }

  getConnectionStatus() {
    const status = {};

    for (const [adapterName, state] of this.connectionStates) {
      status[adapterName] = {
        state: state.state || 'unknown',
        healthy: state.healthy !== false,
        lastPing: state.lastPing,
        lastHealthCheck: state.lastHealthCheck,
        attempts: state.attempts || 0,
        lastAttempt: state.lastAttempt
      };
    }

    return status;
  }

  async exportData(adapterName, dataType, filters = {}) {
    const adapter = this.adapters[adapterName];
    if (!adapter || !adapter.exportData) {
      throw new Error(`Adapter ${adapterName} does not support data export`);
    }

    try {
      const data = await adapter.exportData(dataType, filters);

      this.emit('dataExported', {
        adapter: adapterName,
        dataType,
        filters,
        recordCount: Array.isArray(data) ? data.length : 1,
        timestamp: new Date().toISOString()
      });

      return data;

    } catch (error) {
      console.error(`Error exporting data from ${adapterName}:`, error);
      throw error;
    }
  }

  async importData(adapterName, dataType, data, options = {}) {
    const adapter = this.adapters[adapterName];
    if (!adapter || !adapter.importData) {
      throw new Error(`Adapter ${adapterName} does not support data import`);
    }

    try {
      const result = await adapter.importData(dataType, data, options);

      this.emit('dataImported', {
        adapter: adapterName,
        dataType,
        recordCount: Array.isArray(data) ? data.length : 1,
        result,
        timestamp: new Date().toISOString()
      });

      return result;

    } catch (error) {
      console.error(`Error importing data to ${adapterName}:`, error);
      throw error;
    }
  }

  addCustomAdapter(name, adapter) {
    this.adapters.custom.set(name, adapter);
    this.setupAdapterEventHandlers(`custom_${name}`, adapter);
  }

  removeCustomAdapter(name) {
    const adapter = this.adapters.custom.get(name);
    if (adapter && adapter.disconnect) {
      adapter.disconnect();
    }
    this.adapters.custom.delete(name);
    this.connectionStates.delete(`custom_${name}`);
  }

  getAdapterCapabilities(adapterName) {
    const adapter = this.adapters[adapterName] || this.adapters.custom.get(adapterName);
    if (!adapter) return null;

    return {
      name: adapterName,
      type: adapter.type || 'unknown',
      version: adapter.version || '1.0.0',
      features: adapter.features || [],
      supportedDataTypes: adapter.supportedDataTypes || [],
      supportsWebhooks: adapter.createWebhook !== undefined,
      supportsRealTime: adapter.connect !== undefined,
      supportsImportExport: adapter.importData !== undefined
    };
  }

  getAllAdapterCapabilities() {
    const capabilities = {};

    Object.keys(this.adapters).forEach(name => {
      if (this.adapters[name]) {
        capabilities[name] = this.getAdapterCapabilities(name);
      }
    });

    this.adapters.custom.forEach((adapter, name) => {
      capabilities[`custom_${name}`] = this.getAdapterCapabilities(`custom_${name}`);
    });

    return capabilities;
  }

  async disconnectAll() {
    const disconnectPromises = [];

    Object.entries(this.adapters).forEach(([name, adapter]) => {
      if (adapter && adapter.disconnect) {
        disconnectPromises.push(
          adapter.disconnect().catch(error =>
            console.error(`Error disconnecting ${name}:`, error)
          )
        );
      }
    });

    this.adapters.custom.forEach((adapter, name) => {
      if (adapter && adapter.disconnect) {
        disconnectPromises.push(
          adapter.disconnect().catch(error =>
            console.error(`Error disconnecting custom_${name}:`, error)
          )
        );
      }
    });

    await Promise.allSettled(disconnectPromises);
  }

  // API Methods
  async testConnection(adapterName) {
    const adapter = this.adapters[adapterName] || this.adapters.custom.get(adapterName);
    if (!adapter) {
      throw new Error(`Adapter ${adapterName} not found`);
    }

    try {
      const result = await adapter.testConnection();
      return {
        adapter: adapterName,
        connected: result.connected,
        latency: result.latency,
        capabilities: this.getAdapterCapabilities(adapterName),
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return {
        adapter: adapterName,
        connected: false,
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }
}

// Adapter base class
class BaseAdapter extends EventEmitter {
  constructor(options = {}) {
    super();
    this.options = options;
    this.connected = false;
    this.reconnectAttempts = 0;
  }

  isConnected() {
    return this.connected;
  }

  async connect() {
    // Override in subclasses
    this.connected = true;
    this.emit('connected');
  }

  async disconnect() {
    // Override in subclasses
    this.connected = false;
    this.emit('disconnected');
  }

  async testConnection() {
    // Override in subclasses
    return { connected: this.connected, latency: 0 };
  }

  async healthCheck() {
    // Override in subclasses
    return this.connected;
  }

  async sendData(data, options = {}) {
    // Override in subclasses
    throw new Error('sendData not implemented');
  }

  async getCharacter(characterId) {
    // Override in subclasses
    throw new Error('getCharacter not implemented');
  }

  async createWebhook(url, events) {
    // Override in subclasses
    throw new Error('createWebhook not implemented');
  }

  async removeWebhook(webhookId) {
    // Override in subclasses
    throw new Error('removeWebhook not implemented');
  }

  async exportData(dataType, filters) {
    // Override in subclasses
    throw new Error('exportData not implemented');
  }

  async importData(dataType, data, options) {
    // Override in subclasses
    throw new Error('importData not implemented');
  }
}

// Data transformers
class CharacterDataTransformer {
  transformFromAdapter(adapterName, rawData) {
    // Transform character data from specific adapter format to standard format
    const standardCharacter = {
      id: rawData.id || rawData.character_id,
      name: rawData.name || rawData.character_name,
      race: rawData.race || this.normalizeRace(rawData.race_name),
      class: rawData.class || this.normalizeClass(rawData.class_name),
      level: rawData.level || rawData.character_level || 1,
      abilities: rawData.abilities || rawData.stats || {},
      skills: rawData.skills || {},
      equipment: rawData.equipment || rawData.inventory || [],
      background: rawData.background || {},
      source: adapterName,
      lastUpdated: new Date().toISOString()
    };

    return {
      type: 'character',
      character: standardCharacter,
      originalData: rawData
    };
  }

  transformToAdapter(adapterName, standardData) {
    // Transform standard character data to specific adapter format
    // This would be implemented based on each adapter's expected format
    return standardData;
  }

  normalizeRace(raceName) {
    const raceMap = {
      'human': 'human',
      'elf': 'elf',
      'dwarf': 'dwarf',
      'halfling': 'halfling',
      'dragonborn': 'dragonborn',
      'gnome': 'gnome',
      'half-elf': 'half-elf',
      'half-orc': 'half-orc',
      'tiefling': 'tiefling'
    };

    return raceMap[raceName?.toLowerCase()] || raceName || 'human';
  }

  normalizeClass(className) {
    const classMap = {
      'fighter': 'fighter',
      'wizard': 'wizard',
      'cleric': 'cleric',
      'rogue': 'rogue',
      'paladin': 'paladin',
      'ranger': 'ranger',
      'bard': 'bard',
      'druid': 'druid',
      'monk': 'monk',
      'warlock': 'warlock',
      'sorcerer': 'sorcerer',
      'barbarian': 'barbarian',
      'artificer': 'artificer'
    };

    return classMap[className?.toLowerCase()] || className || 'other';
  }
}

class CampaignDataTransformer {
  transformFromAdapter(adapterName, rawData) {
    return {
      type: 'campaign',
      campaign: {
        id: rawData.id || rawData.campaign_id,
        name: rawData.name || rawData.campaign_name,
        description: rawData.description || '',
        players: rawData.players || [],
        setting: rawData.setting || {},
        source: adapterName,
        lastUpdated: new Date().toISOString()
      },
      originalData: rawData
    };
  }

  transformToAdapter(adapterName, standardData) {
    return standardData;
  }
}

class ConversationDataTransformer {
  transformFromAdapter(adapterName, rawData) {
    return {
      type: 'conversation',
      conversation: {
        id: rawData.id || rawData.conversation_id,
        participants: rawData.participants || [],
        messages: rawData.messages || [],
        context: rawData.context || {},
        source: adapterName,
        lastUpdated: new Date().toISOString()
      },
      originalData: rawData
    };
  }

  transformToAdapter(adapterName, standardData) {
    return standardData;
  }
}

class CombatDataTransformer {
  transformFromAdapter(adapterName, rawData) {
    return {
      type: 'combat',
      combat: {
        id: rawData.id || rawData.combat_id,
        participants: rawData.participants || [],
        turnOrder: rawData.turn_order || [],
        currentTurn: rawData.current_turn || 0,
        state: rawData.state || 'active',
        source: adapterName,
        lastUpdated: new Date().toISOString()
      },
      originalData: rawData
    };
  }

  transformToAdapter(adapterName, standardData) {
    return standardData;
  }
}

class InventoryDataTransformer {
  transformFromAdapter(adapterName, rawData) {
    return {
      type: 'inventory',
      inventory: {
        characterId: rawData.character_id || rawData.characterId,
        items: rawData.items || [],
        currency: rawData.currency || {},
        weight: rawData.weight || 0,
        source: adapterName,
        lastUpdated: new Date().toISOString()
      },
      originalData: rawData
    };
  }

  transformToAdapter(adapterName, standardData) {
    return standardData;
  }
}

// Specific adapter implementations would go here
class DNDBeyondAdapter extends BaseAdapter {
  constructor(options) {
    super(options);
    this.type = 'dndBeyond';
    this.dataType = 'character';
    this.features = ['character_sync', 'inventory_sync', 'webhooks'];
  }

  // Implementation for D&D Beyond API
}

class Roll20Adapter extends BaseAdapter {
  constructor(options) {
    super(options);
    this.type = 'roll20';
    this.dataType = 'campaign';
    this.features = ['campaign_sync', 'character_sync', 'combat_tracking'];
  }

  // Implementation for Roll20 API
}

class FoundryAdapter extends BaseAdapter {
  constructor(options) {
    super(options);
    this.type = 'foundry';
    this.dataType = 'campaign';
    this.features = ['real_time_sync', 'character_sync', 'combat_tracking', 'webhooks'];
  }

  // Implementation for Foundry VTT API
}

class DiscordAdapter extends BaseAdapter {
  constructor(options) {
    super(options);
    this.type = 'discord';
    this.dataType = 'conversation';
    this.features = ['message_handling', 'voice_integration', 'webhooks'];
  }

  // Implementation for Discord Bot API
}

module.exports = {
  SystemIntegrationLayer,
  BaseAdapter,
  CharacterDataTransformer,
  CampaignDataTransformer,
  ConversationDataTransformer,
  CombatDataTransformer,
  InventoryDataTransformer
};