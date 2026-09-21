import { Server as SocketIOServer } from 'socket.io';
import { Server as HTTPServer } from 'http';
import { authenticateSocket } from '../middleware/socket-auth';
import { LearningDataService } from '../services/learning-data-service';

export class LearningStreamServer {
  private io: SocketIOServer;
  private learningDataService: LearningDataService;
  private agentSubscriptions: Map<string, Set<string>> = new Map(); // agentId -> Set of socketIds

  constructor(httpServer: HTTPServer) {
    this.io = new SocketIOServer(httpServer, {
      cors: {
        origin: process.env.FRONTEND_URL || "http://localhost:3000",
        methods: ["GET", "POST"]
      }
    });

    this.learningDataService = new LearningDataService();
    this.setupMiddleware();
    this.setupEventHandlers();
  }

  private setupMiddleware() {
    // Authentication middleware for all socket connections
    this.io.use(authenticateSocket);
  }

  private setupEventHandlers() {
    this.io.on('connection', (socket) => {
      console.log(`User ${socket.user?.username} connected to learning stream`);

      // Handle subscription to agent learning data
      socket.on('subscribe_agent', async (data) => {
        try {
          const { agentId } = data;

          if (!agentId) {
            socket.emit('error', { message: 'Agent ID is required' });
            return;
          }

          // Add socket to agent subscription list
          if (!this.agentSubscriptions.has(agentId)) {
            this.agentSubscriptions.set(agentId, new Set());
          }
          this.agentSubscriptions.get(agentId)!.add(socket.id);

          // Join agent-specific room
          socket.join(`agent:${agentId}`);

          // Send current learning metrics
          const currentMetrics = await this.learningDataService.getLearningMetrics(
            agentId,
            'session',
            socket.user?.id
          );

          if (currentMetrics) {
            socket.emit('initial_data', {
              type: 'metrics_update',
              data: currentMetrics,
              timestamp: new Date()
            });
          }

          console.log(`User ${socket.user?.username} subscribed to agent ${agentId}`);

        } catch (error) {
          console.error('Error handling agent subscription:', error);
          socket.emit('error', { message: 'Failed to subscribe to agent' });
        }
      });

      // Handle unsubscription from agent learning data
      socket.on('unsubscribe_agent', (data) => {
        const { agentId } = data;

        if (agentId) {
          // Remove socket from agent subscription list
          const subscriptions = this.agentSubscriptions.get(agentId);
          if (subscriptions) {
            subscriptions.delete(socket.id);
            if (subscriptions.size === 0) {
              this.agentSubscriptions.delete(agentId);
            }
          }

          // Leave agent-specific room
          socket.leave(`agent:${agentId}`);

          console.log(`User ${socket.user?.username} unsubscribed from agent ${agentId}`);
        }
      });

      // Handle ping for connection health check
      socket.on('ping', () => {
        socket.emit('pong', { timestamp: new Date() });
      });

      // Handle disconnect
      socket.on('disconnect', () => {
        console.log(`User ${socket.user?.username} disconnected from learning stream`);

        // Clean up agent subscriptions
        this.agentSubscriptions.forEach((subscriptions, agentId) => {
          subscriptions.delete(socket.id);
          if (subscriptions.size === 0) {
            this.agentSubscriptions.delete(agentId);
          }
        });
      });
    });
  }

  // Public methods to broadcast updates
  public broadcastMetricsUpdate(agentId: string, metrics: any) {
    this.io.to(`agent:${agentId}`).emit('metrics_update', {
      type: 'metric_update',
      data: metrics,
      timestamp: new Date(),
      agentId
    });
  }

  public broadcastMilestoneAchieved(agentId: string, milestone: any) {
    this.io.to(`agent:${agentId}`).emit('milestone_achieved', {
      type: 'milestone_achieved',
      data: milestone,
      timestamp: new Date(),
      agentId
    });
  }

  public broadcastSessionComplete(agentId: string, sessionData: any) {
    this.io.to(`agent:${agentId}`).emit('session_complete', {
      type: 'session_complete',
      data: sessionData,
      timestamp: new Date(),
      agentId
    });
  }

  public broadcastAlert(agentId: string, alert: any) {
    this.io.to(`agent:${agentId}`).emit('alert', {
      type: 'alert',
      data: alert,
      timestamp: new Date(),
      agentId
    });
  }

  // Method to simulate real-time updates (for testing/demo)
  public startSimulatedUpdates(agentId: string) {
    const interval = setInterval(async () => {
      try {
        const metrics = await this.learningDataService.getLearningMetrics(agentId, 'session');
        if (metrics) {
          // Simulate small changes in metrics
          const updatedMetrics = {
            ...metrics,
            intelligenceMetrics: {
              ...metrics.intelligenceMetrics,
              currentIQ: metrics.intelligenceMetrics.currentIQ + (Math.random() - 0.3) * 0.5,
              learningVelocity: Math.max(0, metrics.intelligenceMetrics.learningVelocity + (Math.random() - 0.5) * 0.01)
            }
          };

          this.broadcastMetricsUpdate(agentId, updatedMetrics);
        }
      } catch (error) {
        console.error('Error in simulated update:', error);
      }
    }, 5000); // Update every 5 seconds

    // Store interval ID for cleanup
    (this as any).simulationIntervals = (this as any).simulationIntervals || new Map();
    (this as any).simulationIntervals.set(agentId, interval);
  }

  public stopSimulatedUpdates(agentId: string) {
    const intervals = (this as any).simulationIntervals as Map<string, NodeJS.Timeout>;
    if (intervals && intervals.has(agentId)) {
      clearInterval(intervals.get(agentId)!);
      intervals.delete(agentId);
    }
  }

  // Get connection statistics
  public getStats() {
    return {
      connectedClients: this.io.engine.clientsCount,
      agentSubscriptions: Object.fromEntries(
        Array.from(this.agentSubscriptions.entries()).map(([agentId, subscriptions]) => [
          agentId,
          subscriptions.size
        ])
      )
    };
  }
}