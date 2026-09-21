import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import { API_CONFIG, OfflineData, PendingAction } from '../constants/api';
import { apiService } from './api';
import { store } from '../store';

interface SyncQueue {
  actions: PendingAction[];
  lastSyncTime: string;
  version: string;
}

interface OfflineCache {
  data: Record<string, any>;
  metadata: Record<string, {
    timestamp: string;
    expiresAt?: string;
    version: number;
  }>;
}

interface ConflictResolution {
  strategy: 'local' | 'remote' | 'merge' | 'prompt';
  resolvedAt: string;
}

class OfflineService {
  private static instance: OfflineService;
  private isOnline: boolean = true;
  private syncInProgress: boolean = false;
  private syncQueue: PendingAction[] = [];
  private offlineCache: OfflineCache;
  private conflictResolutions: Map<string, ConflictResolution> = new Map();
  private networkListeners: any[] = [];

  private constructor() {
    this.offlineCache = {
      data: {},
      metadata: {},
    };
  }

  static getInstance(): OfflineService {
    if (!OfflineService.instance) {
      OfflineService.instance = new OfflineService();
    }
    return OfflineService.instance;
  }

  // Initialize offline service
  async initialize(): Promise<void> {
    try {
      // Load offline data
      await this.loadOfflineData();

      // Setup network monitoring
      await this.setupNetworkMonitoring();

      // Start periodic sync attempts
      this.startPeriodicSync();

      console.log('Offline service initialized successfully');
    } catch (error) {
      console.error('Failed to initialize offline service:', error);
    }
  }

  // Network monitoring
  private async setupNetworkMonitoring(): Promise<void> {
    // Get initial network state
    const networkState = await NetInfo.fetch();
    this.isOnline = networkState.isConnected ?? false;

    // Listen for network changes
    const unsubscribe = NetInfo.addEventListener((state) => {
      const wasOffline = !this.isOnline;
      this.isOnline = state.isConnected ?? false;

      if (wasOffline && this.isOnline) {
        console.log('Network restored, starting sync');
        this.syncPendingActions();
      }
    });

    this.networkListeners.push(unsubscribe);
  }

  // Load offline data from storage
  private async loadOfflineData(): Promise<void> {
    try {
      const offlineDataString = await AsyncStorage.getItem(API_CONFIG.STORAGE_KEYS.OFFLINE_DATA);
      if (offlineDataString) {
        const offlineData: OfflineData = JSON.parse(offlineDataString);

        // Load sync queue
        const syncQueueString = await AsyncStorage.getItem('@sync_queue');
        if (syncQueueString) {
          const syncQueue: SyncQueue = JSON.parse(syncQueueString);
          this.syncQueue = syncQueue.actions;
        }
      }
    } catch (error) {
      console.error('Failed to load offline data:', error);
    }
  }

  // Save offline data to storage
  private async saveOfflineData(): Promise<void> {
    try {
      const syncQueue: SyncQueue = {
        actions: this.syncQueue,
        lastSyncTime: new Date().toISOString(),
        version: '1.0.0',
      };

      await AsyncStorage.setItem('@sync_queue', JSON.stringify(syncQueue));
    } catch (error) {
      console.error('Failed to save offline data:', error);
    }
  }

  // Cache data for offline use
  async cacheData(key: string, data: any, ttl?: number): Promise<void> {
    try {
      const timestamp = new Date().toISOString();
      const expiresAt = ttl ? new Date(Date.now() + ttl).toISOString() : undefined;

      this.offlineCache.data[key] = data;
      this.offlineCache.metadata[key] = {
        timestamp,
        expiresAt,
        version: 1,
      };

      // Save to persistent storage
      await AsyncStorage.setItem(`@cache_${key}`, JSON.stringify({
        data,
        metadata: this.offlineCache.metadata[key],
      }));

      console.log(`Cached data for key: ${key}`);
    } catch (error) {
      console.error(`Failed to cache data for key ${key}:`, error);
    }
  }

  // Get cached data
  async getCachedData(key: string): Promise<any | null> {
    try {
      // Check memory cache first
      if (this.offlineCache.data[key]) {
        const metadata = this.offlineCache.metadata[key];
        if (metadata) {
          // Check if data is still valid
          if (!metadata.expiresAt || new Date(metadata.expiresAt) > new Date()) {
            return this.offlineCache.data[key];
          } else {
            // Data expired, remove from cache
            delete this.offlineCache.data[key];
            delete this.offlineCache.metadata[key];
          }
        }
      }

      // Try to load from persistent storage
      const cachedString = await AsyncStorage.getItem(`@cache_${key}`);
      if (cachedString) {
        const cached = JSON.parse(cachedString);

        // Check if data is still valid
        if (!cached.metadata.expiresAt || new Date(cached.metadata.expiresAt) > new Date()) {
          this.offlineCache.data[key] = cached.data;
          this.offlineCache.metadata[key] = cached.metadata;
          return cached.data;
        } else {
          // Data expired, remove from storage
          await AsyncStorage.removeItem(`@cache_${key}`);
        }
      }

      return null;
    } catch (error) {
      console.error(`Failed to get cached data for key ${key}:`, error);
      return null;
    }
  }

  // Remove cached data
  async removeCachedData(key: string): Promise<void> {
    try {
      delete this.offlineCache.data[key];
      delete this.offlineCache.metadata[key];
      await AsyncStorage.removeItem(`@cache_${key}`);
    } catch (error) {
      console.error(`Failed to remove cached data for key ${key}:`, error);
    }
  }

  // Clear all cached data
  async clearCache(): Promise<void> {
    try {
      this.offlineCache = {
        data: {},
        metadata: {},
      };

      // Remove all cache items from storage
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter(key => key.startsWith('@cache_'));
      await AsyncStorage.multiRemove(cacheKeys);

      console.log('Cleared all cached data');
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  }

  // Queue action for when we're back online
  async queueAction(
    resource: string,
    action: 'create' | 'update' | 'delete',
    data: any,
    priority: 'low' | 'normal' | 'high' = 'normal'
  ): Promise<void> {
    try {
      const pendingAction: PendingAction = {
        id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: action,
        resource,
        data,
        timestamp: new Date().toISOString(),
        retryCount: 0,
        maxRetries: 3,
      };

      // Insert based on priority
      if (priority === 'high') {
        this.syncQueue.unshift(pendingAction);
      } else {
        this.syncQueue.push(pendingAction);
      }

      await this.saveOfflineData();

      // Try to sync immediately if online
      if (this.isOnline) {
        this.syncPendingActions();
      }

      console.log(`Queued ${action} action for resource: ${resource}`);
    } catch (error) {
      console.error('Failed to queue action:', error);
    }
  }

  // Queue API request
  async queueRequest(endpoint: string, options: any): Promise<void> {
    const method = options.method || 'GET';
    let actionType: 'create' | 'update' | 'delete';

    switch (method.toUpperCase()) {
      case 'POST':
        actionType = 'create';
        break;
      case 'PUT':
      case 'PATCH':
        actionType = 'update';
        break;
      case 'DELETE':
        actionType = 'delete';
        break;
      default:
        // GET requests don't need to be queued
        return;
    }

    await this.queueAction(endpoint, actionType, {
      endpoint,
      options,
    });
  }

  // Sync pending actions
  async syncPendingActions(): Promise<void> {
    if (this.syncInProgress || !this.isOnline || this.syncQueue.length === 0) {
      return;
    }

    this.syncInProgress = true;
    console.log(`Starting sync of ${this.syncQueue.length} pending actions`);

    try {
      const failedActions: PendingAction[] = [];

      for (const action of this.syncQueue) {
        try {
          const success = await this.executeAction(action);
          if (!success) {
            action.retryCount++;
            if (action.retryCount < action.maxRetries) {
              failedActions.push(action);
            } else {
              console.error(`Action failed after ${action.maxRetries} retries:`, action);
              // Handle failed action (show notification, etc.)
              this.handleFailedAction(action);
            }
          }
        } catch (error) {
          console.error('Error executing action:', error);
          action.retryCount++;
          if (action.retryCount < action.maxRetries) {
            failedActions.push(action);
          } else {
            this.handleFailedAction(action);
          }
        }
      }

      this.syncQueue = failedActions;
      await this.saveOfflineData();

      if (this.syncQueue.length === 0) {
        console.log('All pending actions synced successfully');
      } else {
        console.log(`${this.syncQueue.length} actions failed to sync, will retry later`);
      }

      // Update UI
      store.dispatch({
        type: 'offline/syncComplete',
        payload: {
          syncedCount: this.syncQueue.length - failedActions.length,
          failedCount: failedActions.length,
        },
      });

    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      this.syncInProgress = false;
    }
  }

  // Execute a single pending action
  private async executeAction(action: PendingAction): Promise<boolean> {
    try {
      const { resource, type, data } = action;

      // Extract endpoint and options if queued as request
      let endpoint: string;
      let options: any;

      if (data.endpoint) {
        endpoint = data.endpoint;
        options = data.options;
      } else {
        endpoint = resource;
        options = {
          method: type === 'create' ? 'POST' : type === 'update' ? 'PUT' : 'DELETE',
          body: data,
        };
      }

      // Check for conflicts before executing
      const hasConflict = await this.checkForConflict(action);
      if (hasConflict) {
        const resolution = await this.resolveConflict(action);
        if (resolution === 'skip') {
          return true; // Skip action
        }
      }

      // Execute the action
      const response = await apiService.request(endpoint, options);

      if (response.success) {
        // Update local cache with new data
        if (response.data) {
          await this.cacheData(endpoint, response.data);
        }
        return true;
      } else {
        console.error(`Action failed: ${response.error}`);
        return false;
      }

    } catch (error) {
      console.error('Error executing action:', error);
      return false;
    }
  }

  // Check for conflicts
  private async checkForConflict(action: PendingAction): Promise<boolean> {
    try {
      // This would check if the resource has been modified since we cached it
      // For now, we'll assume no conflicts
      return false;
    } catch (error) {
      console.error('Error checking for conflicts:', error);
      return false;
    }
  }

  // Resolve conflicts
  private async resolveConflict(action: PendingAction): Promise<'local' | 'remote' | 'merge' | 'skip'> {
    // Default strategy is to use local changes
    // In a real implementation, this might show a UI for user to choose
    return 'local';
  }

  // Handle failed action
  private handleFailedAction(action: PendingAction): void {
    // Show notification to user about failed action
    console.error('Action failed permanently:', action);

    // Store failed action for manual review
    store.dispatch({
      type: 'offline/actionFailed',
      payload: action,
    });
  }

  // Start periodic sync
  private startPeriodicSync(): void {
    setInterval(() => {
      if (this.isOnline && !this.syncInProgress) {
        this.syncPendingActions();
      }
    }, 60000); // Try to sync every minute
  }

  // Force sync all pending actions
  async forceSync(): Promise<void> {
    if (this.isOnline) {
      await this.syncPendingActions();
    } else {
      throw new Error('Device is offline');
    }
  }

  // Get sync status
  getSyncStatus(): {
    isOnline: boolean;
    pendingActions: number;
    syncInProgress: boolean;
    lastSyncTime?: string;
  } {
    return {
      isOnline: this.isOnline,
      pendingActions: this.syncQueue.length,
      syncInProgress: this.syncInProgress,
      lastSyncTime: store.getState().offline?.lastSyncTime,
    };
  }

  // Clear failed actions
  async clearFailedActions(): Promise<void> {
    this.syncQueue = this.syncQueue.filter(action => action.retryCount < action.maxRetries);
    await this.saveOfflineData();
  }

  // Retry failed actions
  async retryFailedActions(): Promise<void> {
    // Reset retry count for all actions and try again
    this.syncQueue.forEach(action => {
      action.retryCount = 0;
    });
    await this.syncPendingActions();
  }

  // Export offline data
  async exportOfflineData(): Promise<OfflineData> {
    return {
      characters: await this.getCachedData('characters') || [],
      inventory: await this.getCachedData('inventory') || [],
      achievements: await this.getCachedData('achievements') || [],
      gameSessions: await this.getCachedData('gameSessions') || [],
      chatMessages: await this.getCachedData('chatMessages') || [],
      lastSyncTime: new Date().toISOString(),
      pendingActions: this.syncQueue,
    };
  }

  // Import offline data
  async importOfflineData(data: OfflineData): Promise<void> {
    try {
      // Cache all imported data
      await Promise.all([
        this.cacheData('characters', data.characters),
        this.cacheData('inventory', data.inventory),
        this.cacheData('achievements', data.achievements),
        this.cacheData('gameSessions', data.gameSessions),
        this.cacheData('chatMessages', data.chatMessages),
      ]);

      // Import pending actions
      this.syncQueue = [...this.syncQueue, ...data.pendingActions];
      await this.saveOfflineData();

      console.log('Offline data imported successfully');
    } catch (error) {
      console.error('Failed to import offline data:', error);
      throw error;
    }
  }

  // Cleanup
  cleanup(): void {
    // Remove network listeners
    this.networkListeners.forEach(unsubscribe => {
      unsubscribe();
    });
    this.networkListeners = [];

    // Clear caches
    this.offlineCache = {
      data: {},
      metadata: {},
    };

    console.log('Offline service cleaned up');
  }
}

// Create singleton instance
export const offlineService = OfflineService.getInstance();
export default offlineService;