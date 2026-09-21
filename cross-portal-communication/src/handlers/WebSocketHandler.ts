import WebSocket from 'ws';
import { v4 as uuidv4 } from 'uuid';
import {
  WebSocketClient,
  User,
  UserRole,
  PortalType,
  Message,
  MessageType
} from '@/types';
import { EventEmitter } from 'events';
import { Logger } from '@/utils/logger';
import config from '@/config/config';

export interface WebSocketMessage {
  type: string;
  data?: any;
  id?: string;
  timestamp?: number;
}

export interface ClientHeartbeat {
  clientId: string;
  timestamp: number;
  ping: number;
}

export class WebSocketHandler extends EventEmitter {
  private wss: WebSocket.Server;
  private clients: Map<string, WebSocketClient>;
  private heartbeatInterval: NodeJS.Timeout;
  private logger: Logger;
  private pendingAuth: Map<string, { ws: WebSocket; timeout: NodeJS.Timeout }>;
  private authTimeout: number = 30000; // 30 seconds

  constructor() {
    super();
    this.clients = new Map();
    this.pendingAuth = new Map();
    this.logger = new Logger('WebSocketHandler');

    this.initializeServer();
    this.setupEventHandlers();
    this.startHeartbeat();
  }

  private initializeServer(): void {
    this.wss = new WebSocket.Server({
      port: config.wsPort,
      maxPayload: config.messaging.maxMessageSize,
      verifyClient: this.verifyClient.bind(this)
    });

    this.logger.info(`WebSocket server initialized on port ${config.wsPort}`);
  }

  private verifyClient(info: any): boolean {
    // Basic verification - can be enhanced with IP whitelisting, rate limiting, etc.
    return true;
  }

  private setupEventHandlers(): void {
    this.wss.on('connection', this.handleConnection.bind(this));
    this.wss.on('error', this.handleServerError.bind(this));

    this.on('messageReceived', this.handleMessage.bind(this));
    this.on('clientAuthenticated', this.handleClientAuthenticated.bind(this));
    this.on('clientDisconnected', this.handleClientDisconnected.bind(this));
  }

  private handleConnection(ws: WebSocket, request: any): void {
    const clientId = uuidv4();
    const clientInfo = {
      ip: request.socket.remoteAddress,
      userAgent: request.headers['user-agent']
    };

    this.logger.info(`New WebSocket connection: ${clientId} from ${clientInfo.ip}`);

    // Store pending connection
    const authTimeout = setTimeout(() => {
      this.rejectPendingClient(clientId);
    }, this.authTimeout);

    this.pendingAuth.set(clientId, { ws, timeout: authTimeout });

    // Setup message handlers
    ws.on('message', (data: WebSocket.Data) => {
      this.handleRawMessage(clientId, data, clientInfo);
    });

    ws.on('close', (code: number, reason: string) => {
      this.handleDisconnection(clientId, code, reason);
    });

    ws.on('error', (error: Error) => {
      this.logger.error(`WebSocket error for client ${clientId}: ${error.message}`);
      this.handleDisconnection(clientId, 1006, 'WebSocket error');
    });

    ws.on('pong', () => {
      this.handlePong(clientId);
    });

    // Send authentication challenge
    this.sendMessage(ws, {
      type: 'auth_challenge',
      data: {
        clientId,
        timestamp: Date.now(),
        serverVersion: '1.0.0'
      }
    });
  }

  private handleRawMessage(clientId: string, data: WebSocket.Data, clientInfo: any): void {
    try {
      const message: WebSocketMessage = JSON.parse(data.toString());
      message.timestamp = Date.now();

      this.logger.debug(`Message received from ${clientId}: ${message.type}`);

      // Check if client is authenticated
      if (!this.clients.has(clientId) && message.type !== 'auth_response') {
        this.logger.warn(`Unauthenticated message from ${clientId}: ${message.type}`);
        return;
      }

      this.emit('messageReceived', { clientId, message, clientInfo });
    } catch (error) {
      this.logger.error(`Invalid message format from ${clientId}: ${error.message}`);
    }
  }

  private handleMessage(event: { clientId: string; message: WebSocketMessage; clientInfo: any }): void {
    const { clientId, message, clientInfo } = event;

    switch (message.type) {
      case 'auth_response':
        this.handleAuthentication(clientId, message.data, clientInfo);
        break;

      case 'chat_message':
        this.handleChatMessage(clientId, message.data);
        break;

      case 'channel_join':
        this.handleChannelJoin(clientId, message.data);
        break;

      case 'channel_leave':
        this.handleChannelLeave(clientId, message.data);
        break;

      case 'heartbeat':
        this.handleHeartbeat(clientId, message.data);
        break;

      case 'subscribe_events':
        this.handleEventSubscription(clientId, message.data);
        break;

      case 'unsubscribe_events':
        this.handleEventUnsubscription(clientId, message.data);
        break;

      case 'get_history':
        this.handleHistoryRequest(clientId, message.data);
        break;

      case 'typing_start':
        this.handleTypingStart(clientId, message.data);
        break;

      case 'typing_stop':
        this.handleTypingStop(clientId, message.data);
        break;

      default:
        this.logger.warn(`Unknown message type: ${message.type} from ${clientId}`);
    }
  }

  private async handleAuthentication(
    clientId: string,
    authData: any,
    clientInfo: any
  ): Promise<void> {
    try {
      const pending = this.pendingAuth.get(clientId);
      if (!pending) {
        return;
      }

      // Validate authentication data
      if (!authData.token || !authData.userId) {
        this.rejectPendingClient(clientId, 'Invalid authentication data');
        return;
      }

      // Verify token with security manager
      const securityContext = await this.emit('validateToken', authData.token);
      if (!securityContext) {
        this.rejectPendingClient(clientId, 'Invalid token');
        return;
      }

      // Create user object
      const user: User = {
        id: authData.userId,
        username: authData.username || `User_${authData.userId}`,
        role: authData.role || UserRole.PLAYER,
        portal: authData.portal || PortalType.PLAYER_PORTAL,
        characterId: authData.characterId,
        permissions: authData.permissions || [],
        isOnline: true,
        lastSeen: new Date(),
        sessionId: authData.sessionId || uuidv4()
      };

      // Create WebSocket client
      const wsClient: WebSocketClient = {
        id: clientId,
        userId: user.id,
        user,
        socket: pending.ws,
        isAlive: true,
        lastPing: new Date(),
        subscriptions: [],
        rateLimitCount: 0,
        rateLimitReset: new Date(Date.now() + 900000) // 15 minutes
      };

      // Clear pending authentication
      clearTimeout(pending.timeout);
      this.pendingAuth.delete(clientId);

      // Register client
      this.clients.set(clientId, wsClient);

      this.logger.info(`Client authenticated: ${user.username} (${user.id})`);

      // Send success response
      this.sendMessage(wsClient.socket, {
        type: 'auth_success',
        data: {
          clientId,
          user: {
            id: user.id,
            username: user.username,
            role: user.role,
            portal: user.portal
          },
          serverTime: Date.now()
        }
      });

      this.emit('clientAuthenticated', wsClient);

    } catch (error) {
      this.logger.error(`Authentication error for ${clientId}: ${error.message}`);
      this.rejectPendingClient(clientId, 'Authentication failed');
    }
  }

  private rejectPendingClient(clientId: string, reason: string = 'Authentication timeout'): void {
    const pending = this.pendingAuth.get(clientId);
    if (pending) {
      clearTimeout(pending.timeout);
      this.pendingAuth.delete(clientId);

      this.sendMessage(pending.ws, {
        type: 'auth_error',
        data: { reason }
      });

      pending.ws.close(1008, reason);
      this.logger.warn(`Client ${clientId} rejected: ${reason}`);
    }
  }

  private handleChatMessage(clientId: string, data: any): void {
    const client = this.clients.get(clientId);
    if (!client) {
      return;
    }

    const message: Partial<Message> = {
      type: MessageType.CHAT,
      channel: data.channel,
      sender: client.userId,
      recipients: data.recipients || [],
      content: data.content,
      metadata: data.metadata || {},
      timestamp: new Date()
    };

    this.emit('chatMessage', { client, message });
  }

  private handleChannelJoin(clientId: string, data: any): void {
    const client = this.clients.get(clientId);
    if (!client) {
      return;
    }

    this.emit('channelJoin', { client, channelId: data.channelId });
  }

  private handleChannelLeave(clientId: string, data: any): void {
    const client = this.clients.get(clientId);
    if (!client) {
      return;
    }

    this.emit('channelLeave', { client, channelId: data.channelId });
  }

  private handleHeartbeat(clientId: string, data: any): void {
    const client = this.clients.get(clientId);
    if (!client) {
      return;
    }

    client.isAlive = true;
    client.lastPing = new Date();

    this.sendMessage(client.socket, {
      type: 'heartbeat_response',
      data: {
        timestamp: Date.now(),
        serverTime: Date.now()
      }
    });
  }

  private handlePong(clientId: string): void {
    const client = this.clients.get(clientId);
    if (client) {
      client.isAlive = true;
    }
  }

  private handleEventSubscription(clientId: string, data: any): void {
    const client = this.clients.get(clientId);
    if (!client) {
      return;
    }

    const eventTypes = data.eventTypes || [];
    client.subscriptions = [...new Set([...client.subscriptions, ...eventTypes])];

    this.emit('eventSubscription', { client, eventTypes });
  }

  private handleEventUnsubscription(clientId: string, data: any): void {
    const client = this.clients.get(clientId);
    if (!client) {
      return;
    }

    const eventTypes = data.eventTypes || [];
    client.subscriptions = client.subscriptions.filter(
      sub => !eventTypes.includes(sub)
    );

    this.emit('eventUnsubscription', { client, eventTypes });
  }

  private handleHistoryRequest(clientId: string, data: any): void {
    const client = this.clients.get(clientId);
    if (!client) {
      return;
    }

    this.emit('historyRequest', {
      client,
      channelId: data.channelId,
      limit: data.limit || 50,
      before: data.before ? new Date(data.before) : undefined,
      after: data.after ? new Date(data.after) : undefined
    });
  }

  private handleTypingStart(clientId: string, data: any): void {
    const client = this.clients.get(clientId);
    if (!client) {
      return;
    }

    this.emit('typingStart', { client, channelId: data.channelId });
  }

  private handleTypingStop(clientId: string, data: any): void {
    const client = this.clients.get(clientId);
    if (!client) {
      return;
    }

    this.emit('typingStop', { client, channelId: data.channelId });
  }

  private handleClientAuthenticated(client: WebSocketClient): void {
    this.logger.info(`Client authenticated: ${client.user.username}`);

    // Join default channels based on user role
    this.emit('joinDefaultChannels', client);
  }

  private handleClientDisconnected(clientId: string, code: number, reason: string): void {
    const client = this.clients.get(clientId);
    if (client) {
      this.logger.info(`Client disconnected: ${client.user.username} (${code}: ${reason})`);
      this.clients.delete(clientId);
      this.emit('clientDisconnected', client);
    }

    // Clean up pending authentication
    const pending = this.pendingAuth.get(clientId);
    if (pending) {
      clearTimeout(pending.timeout);
      this.pendingAuth.delete(clientId);
    }
  }

  private handleDisconnection(clientId: string, code: number, reason: string): void {
    this.handleClientDisconnected(clientId, code, reason);
  }

  private handleServerError(error: Error): void {
    this.logger.error(`WebSocket server error: ${error.message}`);
  }

  // Message Broadcasting
  public sendMessage(ws: WebSocket, message: WebSocketMessage): void {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    }
  }

  public sendToClient(clientId: string, message: WebSocketMessage): boolean {
    const client = this.clients.get(clientId);
    if (client && client.socket.readyState === WebSocket.OPEN) {
      this.sendMessage(client.socket, message);
      return true;
    }
    return false;
  }

  public broadcast(message: WebSocketMessage, filter?: (client: WebSocketClient) => boolean): number {
    let sentCount = 0;

    for (const client of this.clients.values()) {
      if (client.socket.readyState === WebSocket.OPEN) {
        if (!filter || filter(client)) {
          this.sendMessage(client.socket, message);
          sentCount++;
        }
      }
    }

    return sentCount;
  }

  public broadcastToRole(role: UserRole, message: WebSocketMessage): number {
    return this.broadcast(message, client => client.user.role === role);
  }

  public broadcastToPortal(portal: PortalType, message: WebSocketMessage): number {
    return this.broadcast(message, client => client.user.portal === portal);
  }

  public broadcastToChannel(channelId: string, message: WebSocketMessage): number {
    return this.broadcast(message, client =>
      client.subscriptions.includes(`channel:${channelId}`)
    );
  }

  public sendToClients(clientIds: string[], message: WebSocketMessage): number {
    let sentCount = 0;

    for (const clientId of clientIds) {
      if (this.sendToClient(clientId, message)) {
        sentCount++;
      }
    }

    return sentCount;
  }

  // Heartbeat Management
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      this.checkClientHeartbeats();
    }, config.wsHeartbeatInterval);
  }

  private checkClientHeartbeats(): void {
    const now = new Date();
    const timeout = new Date(now.getTime() + config.wsHeartbeatInterval);

    for (const [clientId, client] of this.clients.entries()) {
      if (!client.isAlive) {
        this.logger.warn(`Client ${clientId} failed heartbeat check, terminating connection`);
        client.socket.terminate();
        this.clients.delete(clientId);
        continue;
      }

      client.isAlive = false;

      // Send ping
      if (client.socket.readyState === WebSocket.OPEN) {
        client.socket.ping();
      }
    }
  }

  // Client Management
  public getClient(clientId: string): WebSocketClient | undefined {
    return this.clients.get(clientId);
  }

  public getClientByUserId(userId: string): WebSocketClient | undefined {
    for (const client of this.clients.values()) {
      if (client.userId === userId) {
        return client;
      }
    }
    return undefined;
  }

  public getAllClients(): WebSocketClient[] {
    return Array.from(this.clients.values());
  }

  public getClientsByRole(role: UserRole): WebSocketClient[] {
    return Array.from(this.clients.values()).filter(client => client.user.role === role);
  }

  public getClientsByPortal(portal: PortalType): WebSocketClient[] {
    return Array.from(this.clients.values()).filter(client => client.user.portal === portal);
  }

  public getConnectedUserIds(): string[] {
    return Array.from(this.clients.values()).map(client => client.userId);
  }

  public isUserConnected(userId: string): boolean {
    return this.getClientByUserId(userId) !== undefined;
  }

  // Statistics
  public getStatistics(): {
    totalConnections: number;
    connectionsByRole: Record<UserRole, number>;
    connectionsByPortal: Record<PortalType, number>;
    averageConnectionsPerMinute: number;
    messagesPerMinute: number;
  } {
    const clients = Array.from(this.clients.values());

    const connectionsByRole = {} as Record<UserRole, number>;
    const connectionsByPortal = {} as Record<PortalType, number>;

    for (const client of clients) {
      connectionsByRole[client.user.role] = (connectionsByRole[client.user.role] || 0) + 1;
      connectionsByPortal[client.user.portal] = (connectionsByPortal[client.user.portal] || 0) + 1;
    }

    return {
      totalConnections: clients.length,
      connectionsByRole,
      connectionsByPortal,
      averageConnectionsPerMinute: 0, // Would need tracking over time
      messagesPerMinute: 0 // Would need message counting
    };
  }

  // Server Management
  public shutdown(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }

    // Close all client connections
    for (const [clientId, client] of this.clients.entries()) {
      client.socket.close(1001, 'Server shutdown');
    }

    // Close pending connections
    for (const [clientId, pending] of this.pendingAuth.entries()) {
      clearTimeout(pending.timeout);
      pending.ws.close(1001, 'Server shutdown');
    }

    // Close server
    this.wss.close(() => {
      this.logger.info('WebSocket server shutdown complete');
    });

    this.clients.clear();
    this.pendingAuth.clear();
  }
}