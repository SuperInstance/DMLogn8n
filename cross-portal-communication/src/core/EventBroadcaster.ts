import {
  GameEventMessage,
  CombatEventMessage,
  CharacterUpdateMessage,
  WorldUpdateMessage,
  SystemNotificationMessage,
  DMDirectiveMessage,
  Message,
  MessageType,
  MessagePriority,
  ChannelType
} from '@/types';
import { v4 as uuidv4 } from 'uuid';
import { EventEmitter } from 'events';
import { Logger } from '@/utils/logger';

export interface GameEvent {
  id: string;
  type: string;
  timestamp: Date;
  source: string;
  data: any;
  affectedEntities: string[];
  priority: MessagePriority;
  channel: ChannelType;
}

export interface CombatEvent {
  id: string;
  combatType: string;
  timestamp: Date;
  participants: string[];
  combatData: {
    initiator: string;
    target?: string;
    action: string;
    result: any;
    damage?: number;
    effects?: string[];
  };
  location: string;
  priority: MessagePriority;
}

export interface CharacterEvent {
  id: string;
  characterId: string;
  eventType: string;
  timestamp: Date;
  eventData: any;
  source: string;
  priority: MessagePriority;
}

export interface WorldEvent {
  id: string;
  worldId: string;
  eventType: string;
  timestamp: Date;
  eventData: any;
  location?: string;
  affectedPlayers: string[];
  priority: MessagePriority;
}

export class EventBroadcaster extends EventEmitter {
  private eventSubscriptions: Map<string, Set<string>>;
  private eventHistory: GameEvent[];
  private combatHistory: CombatEvent[];
  private characterHistory: CharacterEvent[];
  private worldHistory: WorldEvent[];
  private logger: Logger;
  private maxHistorySize: number;

  constructor() {
    super();
    this.eventSubscriptions = new Map();
    this.eventHistory = [];
    this.combatHistory = [];
    this.characterHistory = [];
    this.worldHistory = [];
    this.logger = new Logger('EventBroadcaster');
    this.maxHistorySize = 1000;

    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    // Game state change handlers
    this.on('gameStateChanged', this.handleGameStateChanged.bind(this));
    this.on('combatStarted', this.handleCombatStarted.bind(this));
    this.on('combatEnded', this.handleCombatEnded.bind(this));
    this.on('characterAction', this.handleCharacterAction.bind(this));
    this.on('worldChanged', this.handleWorldChanged.bind(this));
    this.on('dmDirective', this.handleDMDirective.bind(this));
    this.on('systemNotification', this.handleSystemNotification.bind(this));
  }

  // Game State Change Broadcasting
  public broadcastGameStateChanged(
    source: string,
    changes: any,
    affectedEntities: string[] = [],
    priority: MessagePriority = MessagePriority.NORMAL
  ): void {
    const event: GameEvent = {
      id: uuidv4(),
      type: 'game_state_changed',
      timestamp: new Date(),
      source,
      data: changes,
      affectedEntities,
      priority,
      channel: ChannelType.PARTY
    };

    this.addToHistory(event, this.eventHistory);
    this.emit('gameStateChanged', event);
    this.notifySubscribers(event);
  }

  private handleGameStateChanged(event: GameEvent): void {
    const message: GameEventMessage = {
      id: uuidv4(),
      type: MessageType.GAME_EVENT,
      priority: event.priority,
      channel: event.channel,
      sender: 'system',
      recipients: event.affectedEntities,
      content: `Game state changed: ${JSON.stringify(event.data)}`,
      metadata: {
        eventId: event.id,
        source: event.source,
        changes: event.data
      },
      timestamp: event.timestamp,
      encrypted: false,
      eventType: event.type,
      eventData: event.data,
      affectedCharacters: event.affectedEntities
    };

    this.emit('messageCreated', message);
  }

  // Combat Event Broadcasting
  public broadcastCombatEvent(
    combatType: string,
    participants: string[],
    combatData: any,
    location: string,
    priority: MessagePriority = MessagePriority.HIGH
  ): void {
    const event: CombatEvent = {
      id: uuidv4(),
      combatType,
      timestamp: new Date(),
      participants,
      combatData,
      location,
      priority
    };

    this.addToHistory(event, this.combatHistory);
    this.emit('combatEvent', event);
    this.notifySubscribers(event);
  }

  public broadcastAttack(
    initiator: string,
    target: string,
    action: string,
    result: any,
    damage?: number,
    effects?: string[],
    location: string = 'unknown'
  ): void {
    const combatData = {
      initiator,
      target,
      action,
      result,
      damage,
      effects
    };

    this.broadcastCombatEvent(
      'attack',
      [initiator, target],
      combatData,
      location,
      MessagePriority.HIGH
    );
  }

  public broadcastSpellCast(
    caster: string,
    spell: string,
    targets: string[],
    result: any,
    effects?: string[],
    location: string = 'unknown'
  ): void {
    const combatData = {
      initiator: caster,
      targets,
      action: `cast_${spell}`,
      result,
      effects
    };

    this.broadcastCombatEvent(
      'spell',
      [caster, ...targets],
      combatData,
      location,
      MessagePriority.HIGH
    );
  }

  private handleCombatStarted(event: CombatEvent): void {
    const message: CombatEventMessage = {
      id: uuidv4(),
      type: MessageType.COMBAT_EVENT,
      priority: event.priority,
      channel: ChannelType.COMBAT,
      sender: 'system',
      recipients: event.participants,
      content: `Combat started at ${event.location}`,
      metadata: {
        eventId: event.id,
        location: event.location
      },
      timestamp: event.timestamp,
      encrypted: false,
      combatType: event.combatType,
      combatData: event.combatData,
      participants: event.participants
    };

    this.emit('messageCreated', message);
  }

  private handleCombatEnded(event: CombatEvent): void {
    const message: CombatEventMessage = {
      id: uuidv4(),
      type: MessageType.COMBAT_EVENT,
      priority: MessagePriority.NORMAL,
      channel: ChannelType.COMBAT,
      sender: 'system',
      recipients: event.participants,
      content: `Combat ended at ${event.location}`,
      metadata: {
        eventId: event.id,
        location: event.location
      },
      timestamp: event.timestamp,
      encrypted: false,
      combatType: 'combat_ended',
      combatData: event.combatData,
      participants: event.participants
    };

    this.emit('messageCreated', message);
  }

  // Character Action Broadcasting
  public broadcastCharacterAction(
    characterId: string,
    action: string,
    data: any,
    source: string = 'character',
    priority: MessagePriority = MessagePriority.NORMAL
  ): void {
    const event: CharacterEvent = {
      id: uuidv4(),
      characterId,
      eventType: action,
      timestamp: new Date(),
      eventData: data,
      source,
      priority
    };

    this.addToHistory(event, this.characterHistory);
    this.emit('characterAction', event);
    this.notifySubscribers(event);
  }

  public broadcastCharacterMovement(
    characterId: string,
    fromLocation: string,
    toLocation: string,
    path?: any[]
  ): void {
    this.broadcastCharacterAction(
      characterId,
      'movement',
      { fromLocation, toLocation, path },
      'character',
      MessagePriority.LOW
    );
  }

  public broadcastCharacterInteraction(
    characterId: string,
    target: string,
    interaction: string,
    result: any
  ): void {
    this.broadcastCharacterAction(
      characterId,
      'interaction',
      { target, interaction, result },
      'character',
      MessagePriority.NORMAL
    );
  }

  private handleCharacterAction(event: CharacterEvent): void {
    const message: CharacterUpdateMessage = {
      id: uuidv4(),
      type: MessageType.CHARACTER_UPDATE,
      priority: event.priority,
      channel: ChannelType.CHARACTER,
      sender: event.source,
      recipients: [event.characterId],
      content: `Character ${event.characterId} performed ${event.eventType}`,
      metadata: {
        eventId: event.id,
        characterId: event.characterId
      },
      timestamp: event.timestamp,
      encrypted: false,
      characterId: event.characterId,
      updateType: 'action',
      updateData: event.eventData
    };

    this.emit('messageCreated', message);
  }

  // World State Broadcasting
  public broadcastWorldChange(
    worldId: string,
    changeType: string,
    data: any,
    location?: string,
    affectedPlayers: string[] = [],
    priority: MessagePriority = MessagePriority.NORMAL
  ): void {
    const event: WorldEvent = {
      id: uuidv4(),
      worldId,
      eventType: changeType,
      timestamp: new Date(),
      eventData: data,
      location,
      affectedPlayers,
      priority
    };

    this.addToHistory(event, this.worldHistory);
    this.emit('worldChanged', event);
    this.notifySubscribers(event);
  }

  public broadcastEnvironmentChange(
    worldId: string,
    environment: string,
    location: string,
    affectedPlayers: string[]
  ): void {
    this.broadcastWorldChange(
      worldId,
      'environment',
      { environment },
      location,
      affectedPlayers,
      MessagePriority.NORMAL
    );
  }

  public broadcastWeatherChange(
    worldId: string,
    weather: string,
    location?: string,
    affectedPlayers: string[] = []
  ): void {
    this.broadcastWorldChange(
      worldId,
      'weather',
      { weather },
      location,
      affectedPlayers,
      MessagePriority.LOW
    );
  }

  public broadcastTimeChange(
    worldId: string,
    timeOfDay: string,
    affectedPlayers: string[]
  ): void {
    this.broadcastWorldChange(
      worldId,
      'time',
      { timeOfDay },
      undefined,
      affectedPlayers,
      MessagePriority.LOW
    );
  }

  private handleWorldChanged(event: WorldEvent): void {
    const message: WorldUpdateMessage = {
      id: uuidv4(),
      type: MessageType.WORLD_UPDATE,
      priority: event.priority,
      channel: ChannelType.PARTY,
      sender: 'system',
      recipients: event.affectedPlayers,
      content: `World changed: ${event.eventType}`,
      metadata: {
        eventId: event.id,
        worldId: event.worldId,
        location: event.location
      },
      timestamp: event.timestamp,
      encrypted: false,
      worldId: event.worldId,
      updateType: event.eventType as any,
      updateData: event.eventData
    };

    this.emit('messageCreated', message);
  }

  // DM Directive Broadcasting
  public broadcastDMDirective(
    dmId: string,
    directive: string,
    directiveType: 'command' | 'suggestion' | 'ruling' | 'announcement',
    targetPlayers?: string[],
    priority: MessagePriority = MessagePriority.HIGH
  ): void {
    const message: DMDirectiveMessage = {
      id: uuidv4(),
      type: MessageType.DM_DIRECTIVE,
      priority,
      channel: ChannelType.DM_WHISPER,
      sender: dmId,
      recipients: targetPlayers || [],
      content: directive,
      metadata: {
        dmId,
        directiveType
      },
      timestamp: new Date(),
      encrypted: false,
      directiveType,
      directive,
      targetPlayers
    };

    this.emit('messageCreated', message);
    this.emit('dmDirective', { dmId, directive, directiveType, targetPlayers });
  }

  private handleDMDirective(event: any): void {
    this.logger.info(`DM directive broadcasted: ${event.directive}`);
  }

  // System Notification Broadcasting
  public broadcastSystemNotification(
    title: string,
    description: string,
    notificationType: 'info' | 'warning' | 'error' | 'success',
    targetUsers?: string[],
    actionable: boolean = false
  ): void {
    const message: SystemNotificationMessage = {
      id: uuidv4(),
      type: MessageType.SYSTEM_NOTIFICATION,
      priority: notificationType === 'error' ? MessagePriority.CRITICAL : MessagePriority.NORMAL,
      channel: ChannelType.SYSTEM,
      sender: 'system',
      recipients: targetUsers || [],
      content: description,
      metadata: {
        title,
        actionable
      },
      timestamp: new Date(),
      encrypted: false,
      notificationType,
      title,
      description,
      actionable
    };

    this.emit('messageCreated', message);
    this.emit('systemNotification', { title, description, notificationType, targetUsers });
  }

  private handleSystemNotification(event: any): void {
    this.logger.info(`System notification: ${event.title} - ${event.description}`);
  }

  // Event Subscription Management
  public subscribeToEvents(clientId: string, eventTypes: string[]): void {
    for (const eventType of eventTypes) {
      if (!this.eventSubscriptions.has(eventType)) {
        this.eventSubscriptions.set(eventType, new Set());
      }
      this.eventSubscriptions.get(eventType)!.add(clientId);
    }

    this.logger.debug(`Client ${clientId} subscribed to events: ${eventTypes.join(', ')}`);
  }

  public unsubscribeFromEvents(clientId: string, eventTypes?: string[]): void {
    if (eventTypes) {
      for (const eventType of eventTypes) {
        const subscribers = this.eventSubscriptions.get(eventType);
        if (subscribers) {
          subscribers.delete(clientId);
          if (subscribers.size === 0) {
            this.eventSubscriptions.delete(eventType);
          }
        }
      }
    } else {
      // Unsubscribe from all events
      for (const subscribers of this.eventSubscriptions.values()) {
        subscribers.delete(clientId);
      }
    }

    this.logger.debug(`Client ${clientId} unsubscribed from events`);
  }

  private notifySubscribers(event: any): void {
    const eventType = event.type || event.eventType || event.combatType;
    const subscribers = this.eventSubscriptions.get(eventType);

    if (subscribers) {
      for (const clientId of subscribers) {
        this.emit('notifySubscriber', { clientId, event });
      }
    }
  }

  // Event History Management
  private addToHistory<T>(event: T, history: T[]): void {
    history.push(event);

    // Maintain maximum history size
    if (history.length > this.maxHistorySize) {
      history.shift();
    }
  }

  public getEventHistory(eventType: string, limit: number = 100): any[] {
    switch (eventType) {
      case 'game':
        return this.eventHistory.slice(-limit);
      case 'combat':
        return this.combatHistory.slice(-limit);
      case 'character':
        return this.characterHistory.slice(-limit);
      case 'world':
        return this.worldHistory.slice(-limit);
      default:
        return [];
    }
  }

  public searchEvents(
    eventType: string,
    filters: {
      startTime?: Date;
      endTime?: Date;
      source?: string;
      affectedEntities?: string[];
    } = {},
    limit: number = 100
  ): any[] {
    let history: any[] = [];

    switch (eventType) {
      case 'game':
        history = this.eventHistory;
        break;
      case 'combat':
        history = this.combatHistory;
        break;
      case 'character':
        history = this.characterHistory;
        break;
      case 'world':
        history = this.worldHistory;
        break;
      default:
        return [];
    }

    let filtered = history;

    if (filters.startTime) {
      filtered = filtered.filter(event => event.timestamp >= filters.startTime!);
    }

    if (filters.endTime) {
      filtered = filtered.filter(event => event.timestamp <= filters.endTime!);
    }

    if (filters.source) {
      filtered = filtered.filter(event => event.source === filters.source);
    }

    if (filters.affectedEntities && filters.affectedEntities.length > 0) {
      filtered = filtered.filter(event => {
        const eventEntities = event.affectedEntities || event.participants || [event.characterId];
        return filters.affectedEntities!.some(entity => eventEntities.includes(entity));
      });
    }

    return filtered.slice(-limit);
  }

  public clearHistory(eventType?: string): void {
    if (eventType) {
      switch (eventType) {
        case 'game':
          this.eventHistory = [];
          break;
        case 'combat':
          this.combatHistory = [];
          break;
        case 'character':
          this.characterHistory = [];
          break;
        case 'world':
          this.worldHistory = [];
          break;
      }
      this.logger.info(`Cleared ${eventType} event history`);
    } else {
      this.eventHistory = [];
      this.combatHistory = [];
      this.characterHistory = [];
      this.worldHistory = [];
      this.logger.info('Cleared all event history');
    }
  }

  public getStatistics(): {
    totalEvents: number;
    gameEvents: number;
    combatEvents: number;
    characterEvents: number;
    worldEvents: number;
    subscribers: number;
  } {
    return {
      totalEvents: this.eventHistory.length + this.combatHistory.length +
                  this.characterHistory.length + this.worldHistory.length,
      gameEvents: this.eventHistory.length,
      combatEvents: this.combatHistory.length,
      characterEvents: this.characterHistory.length,
      worldEvents: this.worldHistory.length,
      subscribers: Array.from(this.eventSubscriptions.values())
        .reduce((total, set) => total + set.size, 0)
    };
  }
}