import {
  Message,
  MessagePriority,
  WebSocketClient,
  Channel,
  MessageQueue,
  MessageFilter,
  BroadcastOptions,
  MessageStatistics
} from '@/types';
import { v4 as uuidv4 } from 'uuid';
import { EventEmitter } from 'events';
import { Logger } from '@/utils/logger';

export class MessageRouter extends EventEmitter {
  private queues: Map<MessagePriority, MessageQueue>;
  private clients: Map<string, WebSocketClient>;
  private channels: Map<string, Channel>;
  private messageHistory: Map<string, Message[]>;
  private statistics: MessageStatistics;
  private processingInterval: NodeJS.Timeout;
  private logger: Logger;

  constructor() {
    super();
    this.queues = new Map();
    this.clients = new Map();
    this.channels = new Map();
    this.messageHistory = new Map();
    this.logger = new Logger('MessageRouter');

    this.initializeQueues();
    this.initializeStatistics();
    this.startProcessing();
  }

  private initializeQueues(): void {
    Object.values(MessagePriority).forEach(priority => {
      if (typeof priority === 'number') {
        this.queues.set(priority, {
          priority,
          messages: [],
          maxSize: 10000,
          processing: false
        });
      }
    });
  }

  private initializeStatistics(): void {
    this.statistics = {
      totalMessages: 0,
      messagesByType: {} as any,
      messagesByChannel: {} as any,
      messagesByUser: {},
      averageMessageSize: 0,
      peakMessagesPerMinute: 0,
      activeChannels: 0,
      activeUsers: 0
    };
  }

  private startProcessing(): void {
    this.processingInterval = setInterval(() => {
      this.processQueues();
    }, 10); // Process every 10ms for low latency
  }

  public async routeMessage(message: Message): Promise<boolean> {
    try {
      // Validate message
      if (!this.validateMessage(message)) {
        this.logger.warn(`Invalid message rejected: ${message.id}`);
        return false;
      }

      // Assign ID if not present
      if (!message.id) {
        message.id = uuidv4();
      }

      // Set timestamp if not present
      if (!message.timestamp) {
        message.timestamp = new Date();
      }

      // Apply filters and permissions
      if (!this.checkMessagePermissions(message)) {
        this.logger.warn(`Message permission denied: ${message.id}`);
        return false;
      }

      // Add to appropriate priority queue
      const queue = this.queues.get(message.priority);
      if (queue && queue.messages.length < queue.maxSize) {
        queue.messages.push(message);
        this.updateStatistics(message);
        this.logger.debug(`Message queued: ${message.id}, priority: ${message.priority}`);
        return true;
      } else {
        this.logger.warn(`Queue full for priority ${message.priority}, dropping message: ${message.id}`);
        return false;
      }
    } catch (error) {
      this.logger.error(`Error routing message: ${error.message}`);
      return false;
    }
  }

  private validateMessage(message: Message): boolean {
    if (!message.type || !message.channel || !message.sender) {
      return false;
    }

    if (message.recipients && !Array.isArray(message.recipients)) {
      return false;
    }

    if (message.content && typeof message.content !== 'string') {
      return false;
    }

    return true;
  }

  private checkMessagePermissions(message: Message): boolean {
    const channel = this.channels.get(message.channel);
    if (!channel) {
      return false;
    }

    const senderClient = this.clients.get(message.sender);
    if (!senderClient) {
      return false;
    }

    // Check if sender has write permission for this channel
    return channel.permissions.write.includes(senderClient.user.role);
  }

  private async processQueues(): Promise<void> {
    // Process queues in priority order (highest first)
    const priorities = Array.from(this.queues.keys()).sort((a, b) => b - a);

    for (const priority of priorities) {
      const queue = this.queues.get(priority);
      if (!queue || queue.messages.length === 0 || queue.processing) {
        continue;
      }

      queue.processing = true;

      try {
        const message = queue.messages.shift();
        if (message) {
          await this.deliverMessage(message);
        }
      } catch (error) {
        this.logger.error(`Error processing queue for priority ${priority}: ${error.message}`);
      } finally {
        queue.processing = false;
      }
    }
  }

  private async deliverMessage(message: Message): Promise<void> {
    try {
      // Store in message history
      this.storeMessage(message);

      // Emit message delivery event
      this.emit('messageDelivered', message);

      // Broadcast to recipients
      await this.broadcastToRecipients(message);

      // Emit to Redis for cross-process communication
      this.emit('redisPublish', message);

      this.logger.debug(`Message delivered: ${message.id}`);
    } catch (error) {
      this.logger.error(`Error delivering message ${message.id}: ${error.message}`);
    }
  }

  private storeMessage(message: Message): void {
    const channelHistory = this.messageHistory.get(message.channel) || [];
    channelHistory.push(message);

    // Keep only last 100 messages per channel
    if (channelHistory.length > 100) {
      channelHistory.shift();
    }

    this.messageHistory.set(message.channel, channelHistory);
  }

  private async broadcastToRecipients(message: Message): Promise<void> {
    if (message.recipients && message.recipients.length > 0) {
      // Direct messaging
      for (const recipientId of message.recipients) {
        const client = this.clients.get(recipientId);
        if (client && client.isAlive) {
          this.sendToClient(client, message);
        }
      }
    } else {
      // Channel broadcasting
      const channel = this.channels.get(message.channel);
      if (channel) {
        for (const memberId of channel.members) {
          const client = this.clients.get(memberId);
          if (client && client.isAlive && client.id !== message.sender) {
            this.sendToClient(client, message);
          }
        }
      }
    }
  }

  private sendToClient(client: WebSocketClient, message: Message): void {
    try {
      // Check rate limiting
      if (this.isRateLimited(client)) {
        this.logger.warn(`Client ${client.userId} is rate limited`);
        return;
      }

      // Send message
      client.socket.send(JSON.stringify({
        type: 'message',
        data: message
      }));

      // Update rate limit
      this.updateRateLimit(client);
    } catch (error) {
      this.logger.error(`Error sending message to client ${client.userId}: ${error.message}`);
    }
  }

  private isRateLimited(client: WebSocketClient): boolean {
    const now = new Date();
    if (now > client.rateLimitReset) {
      client.rateLimitCount = 0;
      client.rateLimitReset = new Date(now.getTime() + 900000); // 15 minutes
    }

    return client.rateLimitCount >= 100; // 100 messages per 15 minutes
  }

  private updateRateLimit(client: WebSocketClient): void {
    client.rateLimitCount++;
  }

  public async broadcastMessage(message: Omit<Message, 'id' | 'timestamp'>, options: BroadcastOptions = {}): Promise<boolean> {
    // Determine recipients based on broadcast options
    let recipients: string[] = [];

    if (options.roles) {
      // Filter by roles
      for (const [clientId, client] of this.clients.entries()) {
        if (options.roles.includes(client.user.role) &&
            (!options.excludeUsers || !options.excludeUsers.includes(clientId))) {
          recipients.push(clientId);
        }
      }
    } else if (options.portals) {
      // Filter by portals
      for (const [clientId, client] of this.clients.entries()) {
        if (options.portals.includes(client.user.portal) &&
            (!options.excludeUsers || !options.excludeUsers.includes(clientId))) {
          recipients.push(clientId);
        }
      }
    } else {
      // Default to all connected clients
      for (const [clientId, client] of this.clients.entries()) {
        if (!options.excludeUsers || !options.excludeUsers.includes(clientId)) {
          recipients.push(clientId);
        }
      }
    }

    const fullMessage: Message = {
      ...message,
      id: uuidv4(),
      timestamp: new Date(),
      recipients
    };

    return this.routeMessage(fullMessage);
  }

  public registerClient(client: WebSocketClient): void {
    this.clients.set(client.id, client);
    this.statistics.activeUsers++;
    this.logger.info(`Client registered: ${client.userId}`);

    // Add client to default channels
    this.addClientToDefaultChannels(client);

    this.emit('clientRegistered', client);
  }

  public unregisterClient(clientId: string): void {
    const client = this.clients.get(clientId);
    if (client) {
      // Remove client from all channels
      this.removeClientFromAllChannels(client);

      this.clients.delete(clientId);
      this.statistics.activeUsers--;
      this.logger.info(`Client unregistered: ${client.userId}`);

      this.emit('clientUnregistered', client);
    }
  }

  private addClientToDefaultChannels(client: WebSocketClient): void {
    for (const [channelId, channel] of this.channels.entries()) {
      if (channel.permissions.read.includes(client.user.role)) {
        channel.members.push(client.id);
      }
    }
  }

  private removeClientFromAllChannels(client: WebSocketClient): void {
    for (const channel of this.channels.values()) {
      const index = channel.members.indexOf(client.id);
      if (index > -1) {
        channel.members.splice(index, 1);
      }
    }
  }

  public createChannel(channel: Channel): void {
    this.channels.set(channel.id, channel);
    this.statistics.activeChannels++;
    this.logger.info(`Channel created: ${channel.id}`);

    this.emit('channelCreated', channel);
  }

  public deleteChannel(channelId: string): void {
    if (this.channels.delete(channelId)) {
      this.statistics.activeChannels--;
      this.logger.info(`Channel deleted: ${channelId}`);

      this.emit('channelDeleted', channelId);
    }
  }

  public getChannelHistory(channelId: string, limit: number = 50): Message[] {
    const history = this.messageHistory.get(channelId) || [];
    return history.slice(-limit);
  }

  public searchMessages(filter: MessageFilter): Message[] {
    let results: Message[] = [];

    for (const messages of this.messageHistory.values()) {
      for (const message of messages) {
        if (this.matchesFilter(message, filter)) {
          results.push(message);
        }
      }
    }

    // Sort by timestamp (newest first)
    results.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

    // Apply pagination
    const offset = filter.offset || 0;
    const limit = filter.limit || 100;

    return results.slice(offset, offset + limit);
  }

  private matchesFilter(message: Message, filter: MessageFilter): boolean {
    if (filter.userId && message.sender !== filter.userId) {
      return false;
    }

    if (filter.channel && message.channel !== filter.channel) {
      return false;
    }

    if (filter.type && message.type !== filter.type) {
      return false;
    }

    if (filter.priority && message.priority !== filter.priority) {
      return false;
    }

    if (filter.dateRange) {
      const messageTime = message.timestamp.getTime();
      if (messageTime < filter.dateRange.start.getTime() ||
          messageTime > filter.dateRange.end.getTime()) {
        return false;
      }
    }

    if (filter.keywords && filter.keywords.length > 0) {
      const content = message.content.toLowerCase();
      const hasKeyword = filter.keywords.some(keyword =>
        content.includes(keyword.toLowerCase())
      );
      if (!hasKeyword) {
        return false;
      }
    }

    return true;
  }

  private updateStatistics(message: Message): void {
    this.statistics.totalMessages++;

    // Update type statistics
    this.statistics.messagesByType[message.type] =
      (this.statistics.messagesByType[message.type] || 0) + 1;

    // Update channel statistics
    this.statistics.messagesByChannel[message.channel] =
      (this.statistics.messagesByChannel[message.channel] || 0) + 1;

    // Update user statistics
    this.statistics.messagesByUser[message.sender] =
      (this.statistics.messagesByUser[message.sender] || 0) + 1;

    // Update average message size
    const messageSize = JSON.stringify(message).length;
    const totalSize = this.statistics.averageMessageSize * (this.statistics.totalMessages - 1) + messageSize;
    this.statistics.averageMessageSize = totalSize / this.statistics.totalMessages;
  }

  public getStatistics(): MessageStatistics {
    return { ...this.statistics };
  }

  public getQueueStatus(): Record<MessagePriority, number> {
    const status: Record<MessagePriority, number> = {} as any;

    for (const [priority, queue] of this.queues.entries()) {
      status[priority] = queue.messages.length;
    }

    return status;
  }

  public clearQueue(priority: MessagePriority): void {
    const queue = this.queues.get(priority);
    if (queue) {
      const cleared = queue.messages.length;
      queue.messages = [];
      this.logger.info(`Cleared queue for priority ${priority}, removed ${cleared} messages`);
    }
  }

  public shutdown(): void {
    if (this.processingInterval) {
      clearInterval(this.processingInterval);
    }

    // Clear all queues
    for (const priority of this.queues.keys()) {
      this.clearQueue(priority);
    }

    this.logger.info('MessageRouter shutdown complete');
  }
}