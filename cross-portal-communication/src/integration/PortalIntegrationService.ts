import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  PortalType,
  User,
  Message,
  Channel,
  WebSocketClient,
  MessageType,
  UserRole
} from '@/types';
import { EventEmitter } from 'events';
import { Logger } from '@/utils/logger';
import config from '@/config/config';

export interface PortalConfig {
  type: PortalType;
  url: string;
  apiKey: string;
  webhookEndpoint: string;
  apiEndpoint: string;
  heartbeatInterval: number;
  timeout: number;
}

export interface PortalStatus {
  type: PortalType;
  url: string;
  status: 'connected' | 'disconnected' | 'error';
  lastPing: Date;
  messageCount: number;
  errorCount: number;
  responseTime: number;
  uptime: number;
}

export interface PortalMessage {
  id: string;
  type: string;
  data: any;
  timestamp: Date;
  source: PortalType;
  target?: PortalType;
  priority: number;
}

export interface PortalWebhook {
  type: string;
  data: any;
  timestamp: Date;
  signature: string;
  portal: PortalType;
}

export class PortalIntegrationService extends EventEmitter {
  private portalConfigs: Map<PortalType, PortalConfig>;
  private portalConnections: Map<PortalType, AxiosInstance>;
  private portalStatuses: Map<PortalType, PortalStatus>;
  private heartbeatIntervals: Map<PortalType, NodeJS.Timeout>;
  private messageQueues: Map<PortalType, PortalMessage[]>;
  private webhookSecrets: Map<PortalType, string>;
  private logger: Logger;

  constructor() {
    super();
    this.portalConfigs = new Map();
    this.portalConnections = new Map();
    this.portalStatuses = new Map();
    this.heartbeatIntervals = new Map();
    this.messageQueues = new Map();
    this.webhookSecrets = new Map();
    this.logger = new Logger('PortalIntegrationService');

    this.initializePortalConfigs();
    this.setupEventHandlers();
  }

  private initializePortalConfigs(): void {
    const portals: PortalConfig[] = [
      {
        type: PortalType.DM_PORTAL,
        url: config.portals.dmPortal,
        apiKey: process.env.DM_PORTAL_API_KEY || 'dm-api-key',
        webhookEndpoint: '/webhook/dm',
        apiEndpoint: '/api',
        heartbeatInterval: 30000,
        timeout: 10000
      },
      {
        type: PortalType.PLAYER_PORTAL,
        url: config.portals.playerPortal,
        apiKey: process.env.PLAYER_PORTAL_API_KEY || 'player-api-key',
        webhookEndpoint: '/webhook/player',
        apiEndpoint: '/api',
        heartbeatInterval: 30000,
        timeout: 10000
      },
      {
        type: PortalType.CODER_PORTAL,
        url: config.portals.coderPortal,
        apiKey: process.env.CODER_PORTAL_API_KEY || 'coder-api-key',
        webhookEndpoint: '/webhook/coder',
        apiEndpoint: '/api',
        heartbeatInterval: 30000,
        timeout: 10000
      },
      {
        type: PortalType.COMBAT_PORTAL,
        url: config.portals.combatPortal,
        apiKey: process.env.COMBAT_PORTAL_API_KEY || 'combat-api-key',
        webhookEndpoint: '/webhook/combat',
        apiEndpoint: '/api',
        heartbeatInterval: 15000,
        timeout: 5000
      },
      {
        type: PortalType.CHARACTER_PORTAL,
        url: config.portals.characterPortal,
        apiKey: process.env.CHARACTER_PORTAL_API_KEY || 'character-api-key',
        webhookEndpoint: '/webhook/character',
        apiEndpoint: '/api',
        heartbeatInterval: 30000,
        timeout: 10000
      }
    ];

    for (const portalConfig of portals) {
      this.portalConfigs.set(portalConfig.type, portalConfig);
      this.initializePortalConnection(portalConfig);
      this.initializePortalStatus(portalConfig.type);
      this.messageQueues.set(portalConfig.type, []);
      this.webhookSecrets.set(portalConfig.type, process.env[`${portalConfig.type.toUpperCase()}_WEBHOOK_SECRET`] || 'default-secret');
    }
  }

  private initializePortalConnection(config: PortalConfig): void {
    const axiosInstance = axios.create({
      baseURL: config.url,
      timeout: config.timeout,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': config.apiKey,
        'User-Agent': 'Cross-Portal-Communication/1.0.0'
      }
    });

    // Setup request interceptor
    axiosInstance.interceptors.request.use(
      (request) => {
        this.logger.debug(`Sending request to ${config.type}: ${request.method?.toUpperCase()} ${request.url}`);
        return request;
      },
      (error) => {
        this.logger.error(`Request error for ${config.type}: ${error.message}`);
        return Promise.reject(error);
      }
    );

    // Setup response interceptor
    axiosInstance.interceptors.response.use(
      (response) => {
        this.logger.debug(`Received response from ${config.type}: ${response.status}`);
        this.updatePortalStatus(config.type, { responseTime: response.config.metadata?.responseTime || 0 });
        return response;
      },
      (error) => {
        this.logger.error(`Response error from ${config.type}: ${error.message}`);
        this.updatePortalStatus(config.type, { errorCount: 1 });
        return Promise.reject(error);
      }
    );

    this.portalConnections.set(config.type, axiosInstance);
  }

  private initializePortalStatus(portalType: PortalType): void {
    const config = this.portalConfigs.get(portalType)!;
    const status: PortalStatus = {
      type: portalType,
      url: config.url,
      status: 'disconnected',
      lastPing: new Date(),
      messageCount: 0,
      errorCount: 0,
      responseTime: 0,
      uptime: 0
    };

    this.portalStatuses.set(portalType, status);
  }

  private setupEventHandlers(): void {
    this.on('portalConnected', this.handlePortalConnected.bind(this));
    this.on('portalDisconnected', this.handlePortalDisconnected.bind(this));
    this.on('messageReceived', this.handlePortalMessage.bind(this));
    this.on('webhookReceived', this.handleWebhookReceived.bind(this));
  }

  // Portal Connection Management
  public async connectToPortal(portalType: PortalType): Promise<boolean> {
    const config = this.portalConfigs.get(portalType);
    const connection = this.portalConnections.get(portalType);

    if (!config || !connection) {
      this.logger.error(`Portal configuration not found for ${portalType}`);
      return false;
    }

    try {
      const response = await connection.get('/health');
      if (response.status === 200) {
        this.updatePortalStatus(portalType, { status: 'connected' });
        this.startHeartbeat(portalType);
        this.processMessageQueue(portalType);

        this.logger.info(`Connected to ${portalType} portal`);
        this.emit('portalConnected', portalType);
        return true;
      }
    } catch (error) {
      this.logger.error(`Failed to connect to ${portalType} portal: ${error.message}`);
      this.updatePortalStatus(portalType, { status: 'error' });
      return false;
    }

    return false;
  }

  public async disconnectFromPortal(portalType: PortalType): Promise<boolean> {
    const connection = this.portalConnections.get(portalType);
    if (!connection) {
      return false;
    }

    try {
      this.stopHeartbeat(portalType);
      this.updatePortalStatus(portalType, { status: 'disconnected' });

      this.logger.info(`Disconnected from ${portalType} portal`);
      this.emit('portalDisconnected', portalType);
      return true;
    } catch (error) {
      this.logger.error(`Error disconnecting from ${portalType} portal: ${error.message}`);
      return false;
    }
  }

  public async connectToAllPortals(): Promise<void> {
    for (const portalType of this.portalConfigs.keys()) {
      await this.connectToPortal(portalType);
    }
  }

  public async disconnectFromAllPortals(): Promise<void> {
    for (const portalType of this.portalConfigs.keys()) {
      await this.disconnectFromPortal(portalType);
    }
  }

  // Message Communication
  public async sendMessageToPortal(
    portalType: PortalType,
    message: Message
  ): Promise<boolean> {
    const connection = this.portalConnections.get(portalType);
    const status = this.portalStatuses.get(portalType);

    if (!connection || !status || status.status !== 'connected') {
      // Queue message for later delivery
      this.queueMessage(portalType, message);
      this.logger.warn(`Portal ${portalType} not connected, message queued`);
      return false;
    }

    try {
      const portalMessage: PortalMessage = {
        id: message.id,
        type: message.type,
        data: {
          content: message.content,
          channel: message.channel,
          sender: message.sender,
          recipients: message.recipients,
          metadata: message.metadata,
          timestamp: message.timestamp
        },
        timestamp: new Date(),
        source: 'cross-portal-comm',
        priority: message.priority
      };

      const startTime = Date.now();
      const response = await connection.post('/api/messages', portalMessage);
      const responseTime = Date.now() - startTime;

      if (response.status === 200) {
        this.updatePortalStatus(portalType, {
          messageCount: 1,
          responseTime
        });
        this.logger.debug(`Message sent to ${portalType}: ${message.id}`);
        return true;
      }
    } catch (error) {
      this.logger.error(`Failed to send message to ${portalType}: ${error.message}`);
      this.updatePortalStatus(portalType, { errorCount: 1 });
      this.queueMessage(portalType, message);
    }

    return false;
  }

  public async broadcastMessageToAllPortals(message: Message, excludePortal?: PortalType): Promise<number> {
    let successCount = 0;

    for (const portalType of this.portalConfigs.keys()) {
      if (excludePortal && portalType === excludePortal) {
        continue;
      }

      const success = await this.sendMessageToPortal(portalType, message);
      if (success) {
        successCount++;
      }
    }

    return successCount;
  }

  public async sendWebhookToPortal(
    portalType: PortalType,
    webhookType: string,
    data: any
  ): Promise<boolean> {
    const config = this.portalConfigs.get(portalType);
    const connection = this.portalConnections.get(portalType);

    if (!config || !connection) {
      return false;
    }

    try {
      const webhook: PortalWebhook = {
        type: webhookType,
        data,
        timestamp: new Date(),
        signature: this.generateWebhookSignature(data, this.webhookSecrets.get(portalType)!),
        portal: portalType
      };

      const response = await connection.post(config.webhookEndpoint, webhook);
      return response.status === 200;
    } catch (error) {
      this.logger.error(`Failed to send webhook to ${portalType}: ${error.message}`);
      return false;
    }
  }

  // Portal API Integration
  public async getUsersFromPortal(portalType: PortalType): Promise<User[]> {
    const connection = this.portalConnections.get(portalType);
    if (!connection) {
      return [];
    }

    try {
      const response = await connection.get('/api/users');
      return response.data.users || [];
    } catch (error) {
      this.logger.error(`Failed to get users from ${portalType}: ${error.message}`);
      return [];
    }
  }

  public async getChannelsFromPortal(portalType: PortalType): Promise<Channel[]> {
    const connection = this.portalConnections.get(portalType);
    if (!connection) {
      return [];
    }

    try {
      const response = await connection.get('/api/channels');
      return response.data.channels || [];
    } catch (error) {
      this.logger.error(`Failed to get channels from ${portalType}: ${error.message}`);
      return [];
    }
  }

  public async notifyPortalOfUserConnection(
    portalType: PortalType,
    user: User
  ): Promise<boolean> {
    return this.sendWebhookToPortal(portalType, 'user_connected', {
      user: {
        id: user.id,
        username: user.username,
        role: user.role,
        portal: user.portal
      },
      timestamp: new Date()
    });
  }

  public async notifyPortalOfUserDisconnection(
    portalType: PortalType,
    userId: string
  ): Promise<boolean> {
    return this.sendWebhookToPortal(portalType, 'user_disconnected', {
      userId,
      timestamp: new Date()
    });
  }

  // Heartbeat Management
  private startHeartbeat(portalType: PortalType): void {
    const config = this.portalConfigs.get(portalType);
    if (!config) {
      return;
    }

    const interval = setInterval(async () => {
      await this.sendHeartbeat(portalType);
    }, config.heartbeatInterval);

    this.heartbeatIntervals.set(portalType, interval);
  }

  private stopHeartbeat(portalType: PortalType): void {
    const interval = this.heartbeatIntervals.get(portalType);
    if (interval) {
      clearInterval(interval);
      this.heartbeatIntervals.delete(portalType);
    }
  }

  private async sendHeartbeat(portalType: PortalType): Promise<void> {
    const connection = this.portalConnections.get(portalType);
    if (!connection) {
      return;
    }

    try {
      const startTime = Date.now();
      const response = await connection.get('/api/heartbeat');
      const responseTime = Date.now() - startTime;

      if (response.status === 200) {
        this.updatePortalStatus(portalType, {
          lastPing: new Date(),
          responseTime,
          status: 'connected'
        });
      }
    } catch (error) {
      this.logger.warn(`Heartbeat failed for ${portalType}: ${error.message}`);
      this.updatePortalStatus(portalType, {
        status: 'error',
        errorCount: 1
      });
    }
  }

  // Message Queue Management
  private queueMessage(portalType: PortalType, message: Message): void {
    const queue = this.messageQueues.get(portalType);
    if (queue) {
      const portalMessage: PortalMessage = {
        id: message.id,
        type: message.type,
        data: message,
        timestamp: new Date(),
        source: 'cross-portal-comm',
        priority: message.priority
      };
      queue.push(portalMessage);

      // Keep queue size manageable
      if (queue.length > 100) {
        queue.shift(); // Remove oldest message
      }
    }
  }

  private async processMessageQueue(portalType: PortalType): Promise<void> {
    const queue = this.messageQueues.get(portalType);
    if (!queue || queue.length === 0) {
      return;
    }

    const connection = this.portalConnections.get(portalType);
    const status = this.portalStatuses.get(portalType);

    if (!connection || !status || status.status !== 'connected') {
      return;
    }

    // Process messages in priority order
    queue.sort((a, b) => b.priority - a.priority);

    const messagesToSend = [...queue];
    queue.length = 0; // Clear queue

    for (const portalMessage of messagesToSend) {
      try {
        const response = await connection.post('/api/messages', portalMessage);
        if (response.status === 200) {
          this.updatePortalStatus(portalType, { messageCount: 1 });
        } else {
          // Re-queue message if failed
          queue.push(portalMessage);
        }
      } catch (error) {
        this.logger.error(`Failed to send queued message to ${portalType}: ${error.message}`);
        // Re-queue message
        queue.push(portalMessage);
      }
    }
  }

  // Webhook Handling
  public handleIncomingWebhook(webhook: PortalWebhook): boolean {
    // Verify signature
    const secret = this.webhookSecrets.get(webhook.portal);
    if (!this.verifyWebhookSignature(webhook.data, webhook.signature, secret!)) {
      this.logger.warn(`Invalid webhook signature from ${webhook.portal}`);
      return false;
    }

    this.logger.debug(`Received webhook from ${webhook.portal}: ${webhook.type}`);
    this.emit('webhookReceived', webhook);
    return true;
  }

  private generateWebhookSignature(data: any, secret: string): string {
    const crypto = require('crypto');
    const payload = JSON.stringify(data);
    return crypto.createHmac('sha256', secret).update(payload).digest('hex');
  }

  private verifyWebhookSignature(data: any, signature: string, secret: string): boolean {
    const expectedSignature = this.generateWebhookSignature(data, secret);
    return signature === expectedSignature;
  }

  // Status Management
  private updatePortalStatus(portalType: PortalType, updates: Partial<PortalStatus>): void {
    const status = this.portalStatuses.get(portalType);
    if (status) {
      Object.assign(status, updates);
      this.emit('portalStatusUpdated', { portalType, status });
    }
  }

  public getPortalStatus(portalType: PortalType): PortalStatus | undefined {
    return this.portalStatuses.get(portalType);
  }

  public getAllPortalStatuses(): Map<PortalType, PortalStatus> {
    return new Map(this.portalStatuses);
  }

  // Event Handlers
  private handlePortalConnected(portalType: PortalType): void {
    this.logger.info(`Portal connected: ${portalType}`);
  }

  private handlePortalDisconnected(portalType: PortalType): void {
    this.logger.info(`Portal disconnected: ${portalType}`);
  }

  private handlePortalMessage(event: any): void {
    this.logger.debug(`Portal message received: ${event.portalType} - ${event.message.id}`);
  }

  private handleWebhookReceived(webhook: PortalWebhook): void {
    this.logger.debug(`Webhook received: ${webhook.portal} - ${webhook.type}`);

    // Process different webhook types
    switch (webhook.type) {
      case 'character_updated':
        this.emit('characterUpdate', webhook.data);
        break;
      case 'combat_event':
        this.emit('combatEvent', webhook.data);
        break;
      case 'world_state_changed':
        this.emit('worldStateChange', webhook.data);
        break;
      case 'user_action':
        this.emit('userAction', webhook.data);
        break;
      default:
        this.logger.warn(`Unknown webhook type: ${webhook.type}`);
    }
  }

  // Statistics and Monitoring
  public getPortalStatistics(): {
    totalPortals: number;
    connectedPortals: number;
    totalMessages: number;
    totalErrors: number;
    averageResponseTime: number;
    portalDetails: PortalStatus[];
  } {
    const statuses = Array.from(this.portalStatuses.values());
    const connectedCount = statuses.filter(s => s.status === 'connected').length;
    const totalMessages = statuses.reduce((sum, s) => sum + s.messageCount, 0);
    const totalErrors = statuses.reduce((sum, s) => sum + s.errorCount, 0);
    const avgResponseTime = statuses.reduce((sum, s) => sum + s.responseTime, 0) / statuses.length;

    return {
      totalPortals: statuses.length,
      connectedPortals: connectedCount,
      totalMessages,
      totalErrors,
      averageResponseTime: Math.round(avgResponseTime),
      portalDetails: statuses
    };
  }

  // Health Check
  public async performHealthCheck(): Promise<{
    healthy: boolean;
    portalStatuses: Record<PortalType, 'healthy' | 'unhealthy' | 'unknown'>;
    issues: string[];
  }> {
    const portalStatuses: Record<string, 'healthy' | 'unhealthy' | 'unknown'> = {};
    const issues: string[] = [];

    for (const [portalType, status] of this.portalStatuses.entries()) {
      if (status.status === 'connected') {
        portalStatuses[portalType] = 'healthy';
      } else if (status.status === 'error') {
        portalStatuses[portalType] = 'unhealthy';
        issues.push(`Portal ${portalType} has errors`);
      } else {
        portalStatuses[portalType] = 'unknown';
        issues.push(`Portal ${portalType} status unknown`);
      }

      // Check response time
      if (status.responseTime > 5000) {
        portalStatuses[portalType] = 'unhealthy';
        issues.push(`Portal ${portalType} response time too high: ${status.responseTime}ms`);
      }
    }

    const healthy = Object.values(portalStatuses).every(s => s === 'healthy');

    return {
      healthy,
      portalStatuses: portalStatuses as Record<PortalType, 'healthy' | 'unhealthy' | 'unknown'>,
      issues
    };
  }

  // Cleanup
  public shutdown(): void {
    this.logger.info('Shutting down portal integration service...');

    // Stop all heartbeats
    for (const [portalType] of this.heartbeatIntervals.entries()) {
      this.stopHeartbeat(portalType);
    }

    // Clear queues
    for (const queue of this.messageQueues.values()) {
      queue.length = 0;
    }

    this.portalConfigs.clear();
    this.portalConnections.clear();
    this.portalStatuses.clear();
    this.messageQueues.clear();
    this.webhookSecrets.clear();

    this.logger.info('Portal integration service shutdown complete');
  }
}