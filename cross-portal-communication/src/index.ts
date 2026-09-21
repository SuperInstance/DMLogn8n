import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import { MessageRouter } from './core/MessageRouter';
import { EventBroadcaster } from './core/EventBroadcaster';
import { DataSyncManager } from './core/DataSyncManager';
import { ChannelManager } from './core/ChannelManager';
import { SecurityManager } from './core/SecurityManager';
import { WebSocketHandler } from './handlers/WebSocketHandler';
import { RedisService } from './services/RedisService';
import { MessagePersistenceService } from './services/MessagePersistenceService';
import { PortalIntegrationService } from './integration/PortalIntegrationService';
import { Logger } from './utils/logger';
import config from './config/config';

export class CrossPortalCommunicationSystem {
  private app: express.Application;
  private messageRouter: MessageRouter;
  private eventBroadcaster: EventBroadcaster;
  private dataSyncManager: DataSyncManager;
  private channelManager: ChannelManager;
  private securityManager: SecurityManager;
  private webSocketHandler: WebSocketHandler;
  private redisService: RedisService;
  private persistenceService: MessagePersistenceService;
  private portalIntegration: PortalIntegrationService;
  private logger: Logger;
  private isShuttingDown: boolean = false;

  constructor() {
    this.logger = new Logger('CrossPortalCommunicationSystem');
    this.app = express();

    this.initializeCoreComponents();
    this.initializeServices();
    this.setupExpress();
    this.setupEventIntegrations();
    this.startHealthChecks();
  }

  private initializeCoreComponents(): void {
    this.logger.info('Initializing core components...');

    this.messageRouter = new MessageRouter();
    this.eventBroadcaster = new EventBroadcaster();
    this.dataSyncManager = new DataSyncManager();
    this.channelManager = new ChannelManager();
    this.securityManager = new SecurityManager();
    this.webSocketHandler = new WebSocketHandler();
    this.redisService = new RedisService();
    this.persistenceService = new MessagePersistenceService();
    this.portalIntegration = new PortalIntegrationService();

    this.logger.info('Core components initialized');
  }

  private initializeServices(): void {
    this.logger.info('Initializing services...');

    // Wait for Redis and MongoDB to be ready
    this.waitForServices();
  }

  private async waitForServices(): Promise<void> {
    const maxWaitTime = 30000; // 30 seconds
    const startTime = Date.now();

    while (Date.now() - startTime < maxWaitTime) {
      if (this.redisService.isReady() && this.persistenceService.isReady()) {
        this.logger.info('All services are ready');
        return;
      }

      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    this.logger.error('Services failed to initialize within timeout');
    throw new Error('Service initialization timeout');
  }

  private setupExpress(): void {
    this.logger.info('Setting up Express server...');

    // Security middleware
    this.app.use(helmet());
    this.app.use(cors({
      origin: Object.values(config.portals),
      credentials: true
    }));
    this.app.use(compression({
      level: config.performance.compressionLevel
    }));

    // Body parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // Request logging
    this.app.use((req, res, next) => {
      this.logger.debug(`${req.method} ${req.path} - ${req.ip}`);
      next();
    });

    // API routes
    this.setupRoutes();

    // Error handling
    this.app.use(this.handleErrors.bind(this));

    // 404 handling
    this.app.use((req, res) => {
      res.status(404).json({
        error: 'Not Found',
        message: `Route ${req.method} ${req.path} not found`
      });
    });
  }

  private setupRoutes(): void {
    this.logger.info('Setting up API routes...');

    // Health check endpoint
    this.app.get('/health', this.handleHealthCheck.bind(this));

    // API status endpoint
    this.app.get('/status', this.handleStatusCheck.bind(this));

    // Authentication endpoint
    this.app.post('/api/auth', this.handleAuthentication.bind(this));

    // Message endpoints
    this.app.post('/api/messages', this.authenticateMiddleware.bind(this), this.handleSendMessage.bind(this));
    this.app.get('/api/messages', this.authenticateMiddleware.bind(this), this.handleGetMessages.bind(this));
    this.app.get('/api/messages/:messageId', this.authenticateMiddleware.bind(this), this.handleGetMessage.bind(this));

    // Channel endpoints
    this.app.get('/api/channels', this.authenticateMiddleware.bind(this), this.handleGetChannels.bind(this));
    this.app.post('/api/channels', this.authenticateMiddleware.bind(this), this.handleCreateChannel.bind(this));
    this.app.post('/api/channels/:channelId/join', this.authenticateMiddleware.bind(this), this.handleJoinChannel.bind(this));
    this.app.post('/api/channels/:channelId/leave', this.authenticateMiddleware.bind(this), this.handleLeaveChannel.bind(this));
    this.app.get('/api/channels/:channelId/messages', this.authenticateMiddleware.bind(this), this.handleGetChannelMessages.bind(this));

    // Webhook endpoints for portal integration
    this.app.post('/webhook/:portalType', this.handleWebhook.bind(this));

    // Admin endpoints
    this.app.get('/api/admin/statistics', this.authenticateMiddleware.bind(this), this.requireRole.bind(this, 'dm'), this.handleGetStatistics.bind(this));
    this.app.get('/api/admin/audit-logs', this.authenticateMiddleware.bind(this), this.requireRole.bind(this, 'dm'), this.handleGetAuditLogs.bind(this));
    this.app.post('/api/admin/broadcast', this.authenticateMiddleware.bind(this), this.requireRole.bind(this, 'dm'), this.handleBroadcastMessage.bind(this));
  }

  private setupEventIntegrations(): void {
    this.logger.info('Setting up event integrations...');

    // Message routing events
    this.messageRouter.on('messageDelivered', this.handleMessageDelivered.bind(this));
    this.messageRouter.on('clientRegistered', this.handleClientRegistered.bind(this));
    this.messageRouter.on('clientUnregistered', this.handleClientUnregistered.bind(this));

    // Event broadcasting events
    this.eventBroadcaster.on('messageCreated', this.handleEventMessageCreated.bind(this));
    this.eventBroadcaster.on('notifySubscriber', this.handleEventNotification.bind(this));

    // Data sync events
    this.dataSyncManager.on('messageCreated', this.handleSyncMessageCreated.bind(this));
    this.dataSyncManager.on('conflictDetected', this.handleSyncConflict.bind(this));

    // Channel events
    this.channelManager.on('messageSent', this.handleChannelMessage.bind(this));
    this.channelManager.on('userJoined', this.handleChannelJoin.bind(this));
    this.channelManager.on('userLeft', this.handleChannelLeave.bind(this));

    // Security events
    this.securityManager.on('securityEvent', this.handleSecurityEvent.bind(this));

    // WebSocket events
    this.webSocketHandler.on('messageReceived', this.handleWebSocketMessage.bind(this));
    this.webSocketHandler.on('clientAuthenticated', this.handleWebSocketClientAuth.bind(this));
    this.webSocketHandler.on('clientDisconnected', this.handleWebSocketClientDisconnect.bind(this));

    // Redis events
    this.redisService.on('redisReady', this.handleRedisReady.bind(this));
    this.redisService.on('redisError', this.handleRedisError.bind(this));

    // Portal integration events
    this.portalIntegration.on('portalConnected', this.handlePortalConnected.bind(this));
    this.portalIntegration.on('portalDisconnected', this.handlePortalDisconnected.bind(this));
    this.portalIntegration.on('webhookReceived', this.handlePortalWebhook.bind(this));

    this.logger.info('Event integrations setup complete');
  }

  // Route Handlers
  private async handleHealthCheck(req: express.Request, res: express.Response): Promise<void> {
    try {
      const health = await this.performHealthCheck();
      res.status(health.healthy ? 200 : 503).json(health);
    } catch (error) {
      res.status(503).json({
        healthy: false,
        error: 'Health check failed',
        timestamp: new Date()
      });
    }
  }

  private async handleStatusCheck(req: express.Request, res: express.Response): Promise<void> {
    const status = {
      system: 'running',
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      timestamp: new Date(),
      services: {
        redis: this.redisService.isReady(),
        mongodb: this.persistenceService.isReady(),
        websockets: this.webSocketHandler.getStatistics().totalConnections > 0
      },
      statistics: {
        messages: this.messageRouter.getStatistics(),
        events: this.eventBroadcaster.getStatistics(),
        channels: this.channelManager.getOverallStatistics(),
        security: this.securityManager.getSecurityStatistics(),
        portals: this.portalIntegration.getPortalStatistics()
      }
    };

    res.json(status);
  }

  private async handleAuthentication(req: express.Request, res: express.Response): Promise<void> {
    try {
      const { username, password } = req.body;
      const clientIp = req.ip;
      const userAgent = req.get('User-Agent');

      const result = await this.securityManager.authenticateUser(
        username,
        password,
        clientIp,
        userAgent
      );

      if (result.success) {
        res.json({
          success: true,
          token: result.token,
          user: {
            id: result.user?.id,
            username: result.user?.username,
            role: result.user?.role,
            portal: result.user?.portal
          }
        });
      } else {
        res.status(401).json({
          success: false,
          error: result.error
        });
      }
    } catch (error) {
      this.logger.error(`Authentication error: ${error.message}`);
      res.status(500).json({
        success: false,
        error: 'Authentication failed'
      });
    }
  }

  private async handleSendMessage(req: express.Request, res: express.Response): Promise<void> {
    try {
      const securityContext = req.securityContext;
      const { channel, content, recipients, metadata } = req.body;

      const message = {
        id: require('crypto').randomUUID(),
        type: 'chat' as any,
        priority: 1 as any,
        channel,
        sender: securityContext.userId,
        recipients: recipients || [],
        content,
        metadata: metadata || {},
        timestamp: new Date(),
        encrypted: false
      };

      // Authorize message
      const authorized = await this.securityManager.authorizeMessage(securityContext, message);
      if (!authorized) {
        res.status(403).json({ error: 'Message not authorized' });
        return;
      }

      // Route message
      const routed = await this.messageRouter.routeMessage(message);
      if (routed) {
        res.json({ success: true, messageId: message.id });
      } else {
        res.status(500).json({ error: 'Failed to route message' });
      }
    } catch (error) {
      this.logger.error(`Send message error: ${error.message}`);
      res.status(500).json({ error: 'Failed to send message' });
    }
  }

  private async handleGetMessages(req: express.Request, res: express.Response): Promise<void> {
    try {
      const { channel, type, limit = 50, offset = 0 } = req.query;

      const filter = {
        channel: channel as string,
        type: type as string,
        limit: parseInt(limit as string),
        offset: parseInt(offset as string)
      };

      const messages = this.messageRouter.searchMessages(filter);
      res.json({ messages });
    } catch (error) {
      this.logger.error(`Get messages error: ${error.message}`);
      res.status(500).json({ error: 'Failed to get messages' });
    }
  }

  private async handleGetMessage(req: express.Request, res: express.Response): Promise<void> {
    try {
      const { messageId } = req.params;
      const message = await this.persistenceService.getMessage(messageId);

      if (!message) {
        res.status(404).json({ error: 'Message not found' });
        return;
      }

      res.json({ message });
    } catch (error) {
      this.logger.error(`Get message error: ${error.message}`);
      res.status(500).json({ error: 'Failed to get message' });
    }
  }

  private async handleGetChannels(req: express.Request, res: express.Response): Promise<void> {
    try {
      const securityContext = req.securityContext;
      const channels = this.channelManager.getAccessibleChannels(
        securityContext.userId,
        securityContext.role
      );

      res.json({ channels });
    } catch (error) {
      this.logger.error(`Get channels error: ${error.message}`);
      res.status(500).json({ error: 'Failed to get channels' });
    }
  }

  private async handleCreateChannel(req: express.Request, res: express.Response): Promise<void> {
    try {
      const securityContext = req.securityContext;
      const channelConfig = req.body;

      // Check if user can create channels
      if (!this.securityManager.hasPermission(securityContext, 'channel', 'create')) {
        res.status(403).json({ error: 'Permission denied' });
        return;
      }

      const channel = this.channelManager.createChannel(channelConfig);
      await this.persistenceService.saveChannel(channel);

      res.json({ success: true, channel });
    } catch (error) {
      this.logger.error(`Create channel error: ${error.message}`);
      res.status(500).json({ error: 'Failed to create channel' });
    }
  }

  private async handleJoinChannel(req: express.Request, res: express.Response): Promise<void> {
    try {
      const securityContext = req.securityContext;
      const { channelId } = req.params;

      const user = {
        id: securityContext.userId,
        username: securityContext.username || '',
        role: securityContext.role,
        portal: securityContext.portal || 'player-portal' as any,
        permissions: securityContext.permissions,
        isOnline: true,
        lastSeen: new Date(),
        sessionId: securityContext.sessionId
      };

      const success = this.channelManager.joinChannel(channelId, user);

      if (success) {
        res.json({ success: true });
      } else {
        res.status(400).json({ error: 'Failed to join channel' });
      }
    } catch (error) {
      this.logger.error(`Join channel error: ${error.message}`);
      res.status(500).json({ error: 'Failed to join channel' });
    }
  }

  private async handleLeaveChannel(req: express.Request, res: express.Response): Promise<void> {
    try {
      const securityContext = req.securityContext;
      const { channelId } = req.params;

      const success = this.channelManager.leaveChannel(channelId, securityContext.userId);

      if (success) {
        res.json({ success: true });
      } else {
        res.status(400).json({ error: 'Failed to leave channel' });
      }
    } catch (error) {
      this.logger.error(`Leave channel error: ${error.message}`);
      res.status(500).json({ error: 'Failed to leave channel' });
    }
  }

  private async handleGetChannelMessages(req: express.Request, res: express.Response): Promise<void> {
    try {
      const { channelId } = req.params;
      const { limit = 50, before, after } = req.query;

      const messages = this.channelManager.getChannelMessages(
        channelId,
        parseInt(limit as string),
        before ? new Date(before as string) : undefined,
        after ? new Date(after as string) : undefined
      );

      res.json({ messages });
    } catch (error) {
      this.logger.error(`Get channel messages error: ${error.message}`);
      res.status(500).json({ error: 'Failed to get channel messages' });
    }
  }

  private async handleWebhook(req: express.Request, res: express.Response): Promise<void> {
    try {
      const { portalType } = req.params;
      const webhook = req.body;

      const success = this.portalIntegration.handleIncomingWebhook({
        ...webhook,
        portal: portalType as any
      });

      if (success) {
        res.json({ success: true });
      } else {
        res.status(400).json({ error: 'Invalid webhook' });
      }
    } catch (error) {
      this.logger.error(`Webhook error: ${error.message}`);
      res.status(500).json({ error: 'Webhook processing failed' });
    }
  }

  private async handleGetStatistics(req: express.Request, res: express.Response): Promise<void> {
    try {
      const statistics = {
        messages: this.messageRouter.getStatistics(),
        events: this.eventBroadcaster.getStatistics(),
        channels: this.channelManager.getOverallStatistics(),
        security: this.securityManager.getSecurityStatistics(),
        sync: this.dataSyncManager.getStatistics(),
        websockets: this.webSocketHandler.getStatistics(),
        redis: this.redisService.getSubscriptions(),
        portals: this.portalIntegration.getPortalStatistics()
      };

      res.json({ statistics });
    } catch (error) {
      this.logger.error(`Get statistics error: ${error.message}`);
      res.status(500).json({ error: 'Failed to get statistics' });
    }
  }

  private async handleGetAuditLogs(req: express.Request, res: express.Response): Promise<void> {
    try {
      const { userId, action, resource, startTime, endTime, limit = 100 } = req.query;

      const logs = await this.persistenceService.getAuditLogs(
        userId as string,
        action as string,
        resource as string,
        startTime ? new Date(startTime as string) : undefined,
        endTime ? new Date(endTime as string) : undefined,
        parseInt(limit as string)
      );

      res.json({ logs });
    } catch (error) {
      this.logger.error(`Get audit logs error: ${error.message}`);
      res.status(500).json({ error: 'Failed to get audit logs' });
    }
  }

  private async handleBroadcastMessage(req: express.Request, res: express.Response): Promise<void> {
    try {
      const securityContext = req.securityContext;
      const { message, options } = req.body;

      const success = await this.messageRouter.broadcastMessage(message, options);

      if (success) {
        res.json({ success: true });
      } else {
        res.status(500).json({ error: 'Failed to broadcast message' });
      }
    } catch (error) {
      this.logger.error(`Broadcast message error: ${error.message}`);
      res.status(500).json({ error: 'Failed to broadcast message' });
    }
  }

  // Event Handlers
  private async handleMessageDelivered(message: any): Promise<void> {
    // Save to persistence
    await this.persistenceService.saveMessage(message);

    // Publish to Redis
    await this.redisService.publishMessage(message);

    // Send to portals
    await this.portalIntegration.broadcastMessageToAllPortals(message);
  }

  private handleClientRegistered(client: any): void {
    this.logger.info(`Client registered: ${client.userId}`);
    this.dataSyncManager.requestFullSync(client.userId);
  }

  private handleClientUnregistered(client: any): void {
    this.logger.info(`Client unregistered: ${client.userId}`);
  }

  private handleEventMessageCreated(message: any): void {
    this.messageRouter.routeMessage(message);
  }

  private handleEventNotification(event: any): void {
    this.webSocketHandler.sendToClient(event.clientId, {
      type: 'event',
      data: event.event
    });
  }

  private handleSyncMessageCreated(message: any): void {
    this.messageRouter.routeMessage(message);
  }

  private handleSyncConflict(event: any): void {
    this.logger.warn(`Sync conflict detected: ${event.message.id}`);
  }

  private handleChannelMessage(event: any): void {
    this.messageRouter.routeMessage(event.message);
  }

  private handleChannelJoin(event: any): void {
    this.logger.info(`User ${event.userId} joined channel ${event.channelId}`);
  }

  private handleChannelLeave(event: any): void {
    this.logger.info(`User ${event.userId} left channel ${event.channelId}`);
  }

  private handleSecurityEvent(auditLog: any): void {
    this.persistenceService.saveAuditLog(auditLog);
  }

  private handleWebSocketMessage(event: any): void {
    // Handle WebSocket messages through the appropriate handlers
    this.logger.debug(`WebSocket message: ${event.message.type}`);
  }

  private handleWebSocketClientAuth(client: any): void {
    this.logger.info(`WebSocket client authenticated: ${client.user.username}`);
    this.messageRouter.registerClient(client);
  }

  private handleWebSocketClientDisconnect(client: any): void {
    this.logger.info(`WebSocket client disconnected: ${client.user.username}`);
    this.messageRouter.unregisterClient(client.id);
  }

  private handleRedisReady(): void {
    this.logger.info('Redis service is ready');
  }

  private handleRedisError(error: any): void {
    this.logger.error(`Redis error: ${error.message}`);
  }

  private handlePortalConnected(portalType: any): void {
    this.logger.info(`Portal connected: ${portalType}`);
  }

  private handlePortalDisconnected(portalType: any): void {
    this.logger.warn(`Portal disconnected: ${portalType}`);
  }

  private handlePortalWebhook(webhook: any): void {
    this.logger.debug(`Portal webhook: ${webhook.type}`);
  }

  // Middleware
  private async authenticateMiddleware(req: express.Request, res: express.Response, next: express.NextFunction): Promise<void> {
    try {
      const token = req.headers.authorization?.replace('Bearer ', '');
      if (!token) {
        res.status(401).json({ error: 'No token provided' });
        return;
      }

      const securityContext = await this.securityManager.validateToken(token);
      if (!securityContext) {
        res.status(401).json({ error: 'Invalid token' });
        return;
      }

      (req as any).securityContext = securityContext;
      next();
    } catch (error) {
      this.logger.error(`Authentication middleware error: ${error.message}`);
      res.status(401).json({ error: 'Authentication failed' });
    }
  }

  private async requireRole(role: string, req: express.Request, res: express.Response, next: express.NextFunction): Promise<void> {
    const securityContext = (req as any).securityContext;

    if (!securityContext || securityContext.role !== role) {
      res.status(403).json({ error: 'Insufficient permissions' });
      return;
    }

    next();
  }

  private handleErrors(error: any, req: express.Request, res: express.Response, next: express.NextFunction): void {
    this.logger.error(`Unhandled error: ${error.message}`, { stack: error.stack });

    res.status(500).json({
      error: 'Internal server error',
      message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong'
    });
  }

  private startHealthChecks(): void {
    // Periodic health checks
    setInterval(async () => {
      if (!this.isShuttingDown) {
        await this.performHealthCheck();
      }
    }, 60000); // Every minute
  }

  private async performHealthCheck(): Promise<{ healthy: boolean; details: any }> {
    const checks = {
      redis: this.redisService.isReady(),
      mongodb: this.persistenceService.isReady(),
      websockets: true, // WebSocket server health check can be added
      portals: true
    };

    const portalHealth = await this.portalIntegration.performHealthCheck();
    checks.portals = portalHealth.healthy;

    const healthy = Object.values(checks).every(check => check === true);

    if (!healthy) {
      this.logger.warn('System health check failed', { checks, portalHealth });
    }

    return {
      healthy,
      details: {
        services: checks,
        portalHealth
      }
    };
  }

  // Public Methods
  public async start(): Promise<void> {
    try {
      this.logger.info('Starting Cross-Portal Communication System...');

      // Start Express server
      this.app.listen(config.port, config.host, () => {
        this.logger.info(`HTTP server listening on ${config.host}:${config.port}`);
      });

      // Connect to all portals
      await this.portalIntegration.connectToAllPortals();

      this.logger.info('Cross-Portal Communication System started successfully');
    } catch (error) {
      this.logger.error(`Failed to start system: ${error.message}`);
      throw error;
    }
  }

  public async shutdown(): Promise<void> {
    if (this.isShuttingDown) {
      return;
    }

    this.isShuttingDown = true;
    this.logger.info('Shutting down Cross-Portal Communication System...');

    try {
      // Shutdown in reverse order
      await this.portalIntegration.shutdown();
      this.webSocketHandler.shutdown();
      this.messageRouter.shutdown();
      this.dataSyncManager.shutdown();
      await this.redisService.shutdown();
      await this.persistenceService.disconnect();

      this.logger.info('Cross-Portal Communication System shutdown complete');
    } catch (error) {
      this.logger.error(`Error during shutdown: ${error.message}`);
    }
  }
}

// Start the system if this file is run directly
if (require.main === module) {
  const system = new CrossPortalCommunicationSystem();

  // Graceful shutdown handling
  process.on('SIGTERM', async () => {
    console.log('SIGTERM received, shutting down gracefully...');
    await system.shutdown();
    process.exit(0);
  });

  process.on('SIGINT', async () => {
    console.log('SIGINT received, shutting down gracefully...');
    await system.shutdown();
    process.exit(0);
  });

  // Start the system
  system.start().catch(error => {
    console.error('Failed to start system:', error);
    process.exit(1);
  });
}

export default CrossPortalCommunicationSystem;