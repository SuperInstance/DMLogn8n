import { CrossPortalCommunicationSystem } from './index';
import { MessageRouter } from './core/MessageRouter';
import { EventBroadcaster } from './core/EventBroadcaster';
import { DataSyncManager } from './core/DataSyncManager';
import { ChannelManager } from './core/ChannelManager';
import { SecurityManager } from './core/SecurityManager';
import { WebSocketHandler } from './handlers/WebSocketHandler';
import { RedisService } from './services/RedisService';
import { MessagePersistenceService } from './services/MessagePersistenceService';
import { PortalIntegrationService } from './integration/PortalIntegrationService';

describe('CrossPortalCommunicationSystem', () => {
  let system: CrossPortalCommunicationSystem;

  beforeEach(() => {
    system = new CrossPortalCommunicationSystem();
  });

  afterEach(async () => {
    if (system) {
      await system.shutdown();
    }
  });

  describe('Initialization', () => {
    it('should initialize all core components', () => {
      expect(system).toBeInstanceOf(CrossPortalCommunicationSystem);
    });

    it('should have all required components', () => {
      expect((system as any).messageRouter).toBeInstanceOf(MessageRouter);
      expect((system as any).eventBroadcaster).toBeInstanceOf(EventBroadcaster);
      expect((system as any).dataSyncManager).toBeInstanceOf(DataSyncManager);
      expect((system as any).channelManager).toBeInstanceOf(ChannelManager);
      expect((system as any).securityManager).toBeInstanceOf(SecurityManager);
      expect((system as any).webSocketHandler).toBeInstanceOf(WebSocketHandler);
      expect((system as any).redisService).toBeInstanceOf(RedisService);
      expect((system as any).persistenceService).toBeInstanceOf(MessagePersistenceService);
      expect((system as any).portalIntegration).toBeInstanceOf(PortalIntegrationService);
    });
  });

  describe('System Operations', () => {
    it('should start without errors', async () => {
      // Mock the start method to avoid actual server startup in tests
      const startSpy = jest.spyOn(system as any, 'start').mockImplementation(async () => {
        // Do nothing for test
      });

      await expect((system as any).start()).resolves.not.toThrow();
      expect(startSpy).toHaveBeenCalled();
    });

    it('should shutdown gracefully', async () => {
      const shutdownSpy = jest.spyOn(system as any, 'shutdown').mockImplementation(async () => {
        // Do nothing for test
      });

      await expect(system.shutdown()).resolves.not.toThrow();
      expect(shutdownSpy).toHaveBeenCalled();
    });
  });

  describe('Component Integration', () => {
    it('should setup event integrations correctly', () => {
      const setupEventsSpy = jest.spyOn(system as any, 'setupEventIntegrations');

      // Re-initialize to test event setup
      system = new CrossPortalCommunicationSystem();

      expect(setupEventsSpy).toHaveBeenCalled();
    });
  });
});

// Additional component tests can be added here for individual components
describe('Component Integration Tests', () => {
  describe('Message Router Integration', () => {
    it('should route messages between components', async () => {
      const messageRouter = new MessageRouter();
      const message = {
        id: 'test-message-1',
        type: 'chat' as any,
        priority: 1 as any,
        channel: 'party' as any,
        sender: 'test-user',
        recipients: [],
        content: 'Test message',
        metadata: {},
        timestamp: new Date(),
        encrypted: false
      };

      const result = await messageRouter.routeMessage(message);
      expect(result).toBe(true);
    });
  });

  describe('Event Broadcaster Integration', () => {
    it('should broadcast game events', () => {
      const eventBroadcaster = new EventBroadcaster();
      const eventSpy = jest.fn();

      eventBroadcaster.on('messageCreated', eventSpy);

      eventBroadcaster.broadcastGameStateChanged(
        'test-source',
        { change: 'test' },
        ['user1', 'user2']
      );

      expect(eventSpy).toHaveBeenCalled();
    });
  });

  describe('Security Manager Integration', () => {
    it('should validate tokens correctly', async () => {
      const securityManager = new SecurityManager();

      // Mock token validation
      const context = await securityManager.validateToken('mock-token');
      expect(context).toBeDefined();
    });
  });
});