import { createClient, RedisClientType } from 'redis';
import { Message, WebSocketClient, EventBroadcaster } from '@/types';
import { EventEmitter } from 'events';
import { Logger } from '@/utils/logger';
import config from '@/config/config';

export interface RedisMessage {
  id: string;
  type: string;
  channel: string;
  sender: string;
  recipients: string[];
  content: string;
  metadata: Record<string, any>;
  timestamp: number;
  priority: number;
  encrypted?: boolean;
}

export interface RedisEvent {
  id: string;
  type: string;
  data: any;
  timestamp: number;
  source: string;
  targets?: string[];
}

export interface RedisConfig {
  host: string;
  port: number;
  password?: string;
  db: number;
  maxRetriesPerRequest: number;
  retryDelayOnFailover: number;
  lazyConnect: boolean;
  keyPrefix: string;
}

export class RedisService extends EventEmitter {
  private publisher: RedisClientType;
  private subscriber: RedisClientType;
  private client: RedisClientType;
  private isPublisherReady: boolean = false;
  private isSubscriberReady: boolean = false;
  private isClientReady: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 10;
  private logger: Logger;
  private subscriptions: Map<string, Set<string>>;

  constructor() {
    super();
    this.subscriptions = new Map();
    this.logger = new Logger('RedisService');

    this.initializeRedis();
  }

  private async initializeRedis(): Promise<void> {
    try {
      // Create Redis clients
      this.publisher = createClient({
        socket: {
          host: config.redis.host,
          port: config.redis.port,
          reconnectStrategy: this.handleReconnect.bind(this)
        },
        password: config.redis.password,
        database: config.redis.db
      }) as RedisClientType;

      this.subscriber = createClient({
        socket: {
          host: config.redis.host,
          port: config.redis.port,
          reconnectStrategy: this.handleReconnect.bind(this)
        },
        password: config.redis.password,
        database: config.redis.db
      }) as RedisClientType;

      this.client = createClient({
        socket: {
          host: config.redis.host,
          port: config.redis.port,
          reconnectStrategy: this.handleReconnect.bind(this)
        },
        password: config.redis.password,
        database: config.redis.db
      }) as RedisClientType;

      // Setup event handlers
      this.setupClientEvents(this.publisher, 'Publisher');
      this.setupClientEvents(this.subscriber, 'Subscriber');
      this.setupClientEvents(this.client, 'Client');

      // Connect clients
      await this.publisher.connect();
      await this.subscriber.connect();
      await this.client.connect();

      this.logger.info('Redis service initialized successfully');
      this.emit('redisReady');

    } catch (error) {
      this.logger.error(`Failed to initialize Redis: ${error.message}`);
      this.emit('redisError', error);
    }
  }

  private setupClientEvents(client: RedisClientType, name: string): void {
    client.on('error', (error) => {
      this.logger.error(`Redis ${name} error: ${error.message}`);
      this.emit('redisError', error);
    });

    client.on('connect', () => {
      this.logger.info(`Redis ${name} connected`);
    });

    client.on('ready', () => {
      this.logger.info(`Redis ${name} ready`);
      switch (name) {
        case 'Publisher':
          this.isPublisherReady = true;
          break;
        case 'Subscriber':
          this.isSubscriberReady = true;
          break;
        case 'Client':
          this.isClientReady = true;
          break;
      }

      if (this.isPublisherReady && this.isSubscriberReady && this.isClientReady) {
        this.emit('redisReady');
      }
    });

    client.on('end', () => {
      this.logger.warn(`Redis ${name} connection ended`);
      switch (name) {
        case 'Publisher':
          this.isPublisherReady = false;
          break;
        case 'Subscriber':
          this.isSubscriberReady = false;
          break;
        case 'Client':
          this.isClientReady = false;
          break;
      }
    });

    client.on('reconnecting', () => {
      this.logger.info(`Redis ${name} reconnecting...`);
    });
  }

  private handleReconnect(retries: number): number | Error {
    this.logger.info(`Redis reconnection attempt ${retries}`);

    if (retries > this.maxReconnectAttempts) {
      return new Error('Max reconnection attempts reached');
    }

    return Math.min(retries * 100, 3000); // Exponential backoff, max 3 seconds
  }

  // Message Publishing
  public async publishMessage(message: Message): Promise<boolean> {
    if (!this.isPublisherReady) {
      this.logger.warn('Redis publisher not ready, message not published');
      return false;
    }

    try {
      const redisMessage: RedisMessage = {
        id: message.id,
        type: message.type,
        channel: message.channel,
        sender: message.sender,
        recipients: message.recipients,
        content: message.content,
        metadata: message.metadata,
        timestamp: message.timestamp.getTime(),
        priority: message.priority,
        encrypted: message.encrypted
      };

      const channelName = this.getChannelName('messages', message.channel);
      const result = await this.publisher.publish(
        channelName,
        JSON.stringify(redisMessage)
      );

      this.logger.debug(`Message published to Redis: ${message.id}, channel: ${channelName}, recipients: ${result}`);
      return result > 0;

    } catch (error) {
      this.logger.error(`Failed to publish message to Redis: ${error.message}`);
      return false;
    }
  }

  public async publishEvent(eventType: string, data: any, source: string, targets?: string[]): Promise<boolean> {
    if (!this.isPublisherReady) {
      this.logger.warn('Redis publisher not ready, event not published');
      return false;
    }

    try {
      const redisEvent: RedisEvent = {
        id: `${eventType}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: eventType,
        data,
        timestamp: Date.now(),
        source,
        targets
      };

      const channelName = this.getChannelName('events', eventType);
      const result = await this.publisher.publish(
        channelName,
        JSON.stringify(redisEvent)
      );

      this.logger.debug(`Event published to Redis: ${eventType}, channel: ${channelName}, recipients: ${result}`);
      return result > 0;

    } catch (error) {
      this.logger.error(`Failed to publish event to Redis: ${error.message}`);
      return false;
    }
  }

  public async publishDirectMessage(targetUserId: string, message: Message): Promise<boolean> {
    if (!this.isPublisherReady) {
      this.logger.warn('Redis publisher not ready, direct message not published');
      return false;
    }

    try {
      const redisMessage: RedisMessage = {
        id: message.id,
        type: message.type,
        channel: message.channel,
        sender: message.sender,
        recipients: [targetUserId],
        content: message.content,
        metadata: message.metadata,
        timestamp: message.timestamp.getTime(),
        priority: message.priority,
        encrypted: message.encrypted
      };

      const channelName = this.getChannelName('direct', targetUserId);
      const result = await this.publisher.publish(
        channelName,
        JSON.stringify(redisMessage)
      );

      this.logger.debug(`Direct message published to Redis: ${message.id}, target: ${targetUserId}, recipients: ${result}`);
      return result > 0;

    } catch (error) {
      this.logger.error(`Failed to publish direct message to Redis: ${error.message}`);
      return false;
    }
  }

  // Subscription Management
  public async subscribeToMessages(channel: string, callback: (message: RedisMessage) => void): Promise<boolean> {
    if (!this.isSubscriberReady) {
      this.logger.warn('Redis subscriber not ready, cannot subscribe to messages');
      return false;
    }

    try {
      const channelName = this.getChannelName('messages', channel);

      await this.subscriber.subscribe(channelName, (message) => {
        try {
          const redisMessage: RedisMessage = JSON.parse(message);
          callback(redisMessage);
        } catch (error) {
          this.logger.error(`Failed to parse Redis message: ${error.message}`);
        }
      });

      // Track subscription
      if (!this.subscriptions.has('messages')) {
        this.subscriptions.set('messages', new Set());
      }
      this.subscriptions.get('messages')!.add(channel);

      this.logger.debug(`Subscribed to messages channel: ${channelName}`);
      return true;

    } catch (error) {
      this.logger.error(`Failed to subscribe to messages channel ${channel}: ${error.message}`);
      return false;
    }
  }

  public async subscribeToEvents(eventType: string, callback: (event: RedisEvent) => void): Promise<boolean> {
    if (!this.isSubscriberReady) {
      this.logger.warn('Redis subscriber not ready, cannot subscribe to events');
      return false;
    }

    try {
      const channelName = this.getChannelName('events', eventType);

      await this.subscriber.subscribe(channelName, (message) => {
        try {
          const redisEvent: RedisEvent = JSON.parse(message);
          callback(redisEvent);
        } catch (error) {
          this.logger.error(`Failed to parse Redis event: ${error.message}`);
        }
      });

      // Track subscription
      if (!this.subscriptions.has('events')) {
        this.subscriptions.set('events', new Set());
      }
      this.subscriptions.get('events')!.add(eventType);

      this.logger.debug(`Subscribed to events channel: ${channelName}`);
      return true;

    } catch (error) {
      this.logger.error(`Failed to subscribe to events channel ${eventType}: ${error.message}`);
      return false;
    }
  }

  public async subscribeToDirectMessages(userId: string, callback: (message: RedisMessage) => void): Promise<boolean> {
    if (!this.isSubscriberReady) {
      this.logger.warn('Redis subscriber not ready, cannot subscribe to direct messages');
      return false;
    }

    try {
      const channelName = this.getChannelName('direct', userId);

      await this.subscriber.subscribe(channelName, (message) => {
        try {
          const redisMessage: RedisMessage = JSON.parse(message);
          callback(redisMessage);
        } catch (error) {
          this.logger.error(`Failed to parse Redis direct message: ${error.message}`);
        }
      });

      // Track subscription
      if (!this.subscriptions.has('direct')) {
        this.subscriptions.set('direct', new Set());
      }
      this.subscriptions.get('direct')!.add(userId);

      this.logger.debug(`Subscribed to direct messages for user: ${userId}`);
      return true;

    } catch (error) {
      this.logger.error(`Failed to subscribe to direct messages for user ${userId}: ${error.message}`);
      return false;
    }
  }

  public async unsubscribeFromMessages(channel: string): Promise<boolean> {
    if (!this.isSubscriberReady) {
      return false;
    }

    try {
      const channelName = this.getChannelName('messages', channel);
      await this.subscriber.unsubscribe(channelName);

      // Remove from tracking
      const messageSubs = this.subscriptions.get('messages');
      if (messageSubs) {
        messageSubs.delete(channel);
      }

      this.logger.debug(`Unsubscribed from messages channel: ${channelName}`);
      return true;

    } catch (error) {
      this.logger.error(`Failed to unsubscribe from messages channel ${channel}: ${error.message}`);
      return false;
    }
  }

  public async unsubscribeFromEvents(eventType: string): Promise<boolean> {
    if (!this.isSubscriberReady) {
      return false;
    }

    try {
      const channelName = this.getChannelName('events', eventType);
      await this.subscriber.unsubscribe(channelName);

      // Remove from tracking
      const eventSubs = this.subscriptions.get('events');
      if (eventSubs) {
        eventSubs.delete(eventType);
      }

      this.logger.debug(`Unsubscribed from events channel: ${channelName}`);
      return true;

    } catch (error) {
      this.logger.error(`Failed to unsubscribe from events channel ${eventType}: ${error.message}`);
      return false;
    }
  }

  public async unsubscribeFromDirectMessages(userId: string): Promise<boolean> {
    if (!this.isSubscriberReady) {
      return false;
    }

    try {
      const channelName = this.getChannelName('direct', userId);
      await this.subscriber.unsubscribe(channelName);

      // Remove from tracking
      const directSubs = this.subscriptions.get('direct');
      if (directSubs) {
        directSubs.delete(userId);
      }

      this.logger.debug(`Unsubscribed from direct messages for user: ${userId}`);
      return true;

    } catch (error) {
      this.logger.error(`Failed to unsubscribe from direct messages for user ${userId}: ${error.message}`);
      return false;
    }
  }

  // Cache Operations
  public async setCache(key: string, value: any, ttl?: number): Promise<boolean> {
    if (!this.isClientReady) {
      return false;
    }

    try {
      const serializedValue = JSON.stringify(value);
      const fullKey = this.getFullKey('cache', key);

      if (ttl) {
        await this.client.setEx(fullKey, ttl, serializedValue);
      } else {
        await this.client.set(fullKey, serializedValue);
      }

      this.logger.debug(`Cache set: ${fullKey}`);
      return true;

    } catch (error) {
      this.logger.error(`Failed to set cache ${key}: ${error.message}`);
      return false;
    }
  }

  public async getCache(key: string): Promise<any | null> {
    if (!this.isClientReady) {
      return null;
    }

    try {
      const fullKey = this.getFullKey('cache', key);
      const value = await this.client.get(fullKey);

      if (value) {
        return JSON.parse(value);
      }

      return null;

    } catch (error) {
      this.logger.error(`Failed to get cache ${key}: ${error.message}`);
      return null;
    }
  }

  public async deleteCache(key: string): Promise<boolean> {
    if (!this.isClientReady) {
      return false;
    }

    try {
      const fullKey = this.getFullKey('cache', key);
      const result = await this.client.del(fullKey);

      this.logger.debug(`Cache deleted: ${fullKey}, result: ${result}`);
      return result > 0;

    } catch (error) {
      this.logger.error(`Failed to delete cache ${key}: ${error.message}`);
      return false;
    }
  }

  // User Session Management
  public async setUserSession(userId: string, sessionData: any, ttl: number = 86400): Promise<boolean> {
    const sessionKey = `session:${userId}`;
    return this.setCache(sessionKey, sessionData, ttl);
  }

  public async getUserSession(userId: string): Promise<any | null> {
    const sessionKey = `session:${userId}`;
    return this.getCache(sessionKey);
  }

  public async deleteUserSession(userId: string): Promise<boolean> {
    const sessionKey = `session:${userId}`;
    return this.deleteCache(sessionKey);
  }

  // Presence Management
  public async setUserOnline(userId: string, portal: string): Promise<boolean> {
    const presenceKey = `presence:${userId}`;
    const presenceData = {
      userId,
      portal,
      lastSeen: Date.now(),
      status: 'online'
    };
    return this.setCache(presenceKey, presenceData, 300); // 5 minutes TTL
  }

  public async setUserOffline(userId: string): Promise<boolean> {
    const presenceKey = `presence:${userId}`;
    return this.deleteCache(presenceKey);
  }

  public async getOnlineUsers(): Promise<string[]> {
    if (!this.isClientReady) {
      return [];
    }

    try {
      const pattern = this.getFullKey('presence', '*');
      const keys = await this.client.keys(pattern);

      return keys.map(key => key.replace(this.getFullKey('presence', ''), ''));

    } catch (error) {
      this.logger.error(`Failed to get online users: ${error.message}`);
      return [];
    }
  }

  // Rate Limiting
  public async checkRateLimit(key: string, limit: number, windowMs: number): Promise<{ allowed: boolean; remaining: number; resetTime: number }> {
    if (!this.isClientReady) {
      return { allowed: true, remaining: limit, resetTime: Date.now() + windowMs };
    }

    try {
      const rateLimitKey = this.getFullKey('ratelimit', key);
      const now = Date.now();
      const windowStart = now - windowMs;

      // Remove old entries
      await this.client.zRemRangeByScore(rateLimitKey, 0, windowStart);

      // Count current entries
      const count = await this.client.zCard(rateLimitKey);

      if (count >= limit) {
        // Get oldest entry to determine reset time
        const oldest = await this.client.zRange(rateLimitKey, 0, 0);
        const resetTime = oldest.length > 0 ? parseInt(oldest[0]) + windowMs : now + windowMs;

        return {
          allowed: false,
          remaining: 0,
          resetTime
        };
      }

      // Add current request
      await this.client.zAdd(rateLimitKey, { score: now, value: now.toString() });
      await this.client.expire(rateLimitKey, Math.ceil(windowMs / 1000));

      return {
        allowed: true,
        remaining: limit - count - 1,
        resetTime: now + windowMs
      };

    } catch (error) {
      this.logger.error(`Failed to check rate limit for ${key}: ${error.message}`);
      return { allowed: true, remaining: limit, resetTime: Date.now() + windowMs };
    }
  }

  // Utility Methods
  private getChannelName(type: string, identifier: string): string {
    return `${config.redis.keyPrefix}${type}:${identifier}`;
  }

  private getFullKey(type: string, identifier: string): string {
    return `${config.redis.keyPrefix}${type}:${identifier}`;
  }

  // Statistics and Monitoring
  public async getRedisInfo(): Promise<any> {
    if (!this.isClientReady) {
      return null;
    }

    try {
      return await this.client.info();
    } catch (error) {
      this.logger.error(`Failed to get Redis info: ${error.message}`);
      return null;
    }
  }

  public async getMemoryUsage(): Promise<number> {
    if (!this.isClientReady) {
      return 0;
    }

    try {
      const info = await this.client.info('memory');
      const match = info.match(/used_memory:(\d+)/);
      return match ? parseInt(match[1]) : 0;
    } catch (error) {
      this.logger.error(`Failed to get Redis memory usage: ${error.message}`);
      return 0;
    }
  }

  public getSubscriptions(): Map<string, Set<string>> {
    return new Map(this.subscriptions);
  }

  public isReady(): boolean {
    return this.isPublisherReady && this.isSubscriberReady && this.isClientReady;
  }

  // Cleanup and Shutdown
  public async shutdown(): Promise<void> {
    this.logger.info('Shutting down Redis service...');

    try {
      if (this.publisher) {
        await this.publisher.quit();
      }
      if (this.subscriber) {
        await this.subscriber.quit();
      }
      if (this.client) {
        await this.client.quit();
      }

      this.subscriptions.clear();
      this.logger.info('Redis service shutdown complete');
    } catch (error) {
      this.logger.error(`Error during Redis shutdown: ${error.message}`);
    }
  }
}