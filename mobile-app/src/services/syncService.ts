import NetInfo from '@react-native-community/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SyncQueueItem, SyncResult, ConflictResolution } from '../types/sync';

export class SyncService {
  private static instance: SyncService;
  private isOnline: boolean = true;
  private syncInProgress: boolean = false;
  private syncQueue: SyncQueueItem[] = [];
  private conflictResolution: ConflictResolution = 'prompt_user';
  private listeners: Array<(isOnline: boolean) => void> = [];

  private constructor() {}

  static getInstance(): SyncService {
    if (!SyncService.instance) {
      SyncService.instance = new SyncService();
    }
    return SyncService.instance;
  }

  async initialize(): Promise<void> {
    try {
      // Check initial network status
      const netInfo = await NetInfo.fetch();
      this.isOnline = netInfo.isConnected ?? false;

      // Listen for network changes
      NetInfo.addEventListener(state => {
        const wasOffline = !this.isOnline;
        this.isOnline = state.isConnected ?? false;

        if (wasOffline && this.isOnline) {
          // Came back online - start sync
          this.startSync();
        }

        // Notify listeners
        this.listeners.forEach(listener => listener(this.isOnline));
      });

      // Load sync queue from storage
      await this.loadSyncQueue();

      console.log('Sync service initialized, online:', this.isOnline);
    } catch (error) {
      console.error('Failed to initialize sync service:', error);
    }
  }

  async checkConnectivity(): Promise<boolean> {
    try {
      const netInfo = await NetInfo.fetch();
      this.isOnline = netInfo.isConnected ?? false;
      return this.isOnline;
    } catch (error) {
      console.error('Failed to check connectivity:', error);
      return false;
    }
  }

  setConflictResolution(resolution: ConflictResolution): void {
    this.conflictResolution = resolution;
  }

  addNetworkStatusListener(listener: (isOnline: boolean) => void): () => void {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  async addToSyncQueue(item: SyncQueueItem): Promise<void> {
    try {
      // Add timestamp if not present
      if (!item.timestamp) {
        item.timestamp = new Date().toISOString();
      }

      // Add unique ID if not present
      if (!item.id) {
        item.id = `${item.entityType}_${item.entityId}_${item.timestamp}_${Math.random().toString(36).substr(2, 9)}`;
      }

      this.syncQueue.push(item);

      // Save to storage
      await this.saveSyncQueue();

      // Try to sync immediately if online
      if (this.isOnline && !this.syncInProgress) {
        this.startSync();
      }

      console.log('Added to sync queue:', item.id);
    } catch (error) {
      console.error('Failed to add to sync queue:', error);
    }
  }

  async startSync(): Promise<void> {
    if (!this.isOnline || this.syncInProgress || this.syncQueue.length === 0) {
      return;
    }

    this.syncInProgress = true;

    try {
      console.log(`Starting sync with ${this.syncQueue.length} items`);

      // Sort queue by priority and timestamp
      const sortedQueue = [...this.syncQueue].sort((a, b) => {
        // First by priority
        const priorityOrder = { critical: 0, high: 1, normal: 2, low: 3, background: 4 };
        const aPriority = priorityOrder[a.priority] || 2;
        const bPriority = priorityOrder[b.priority] || 2;

        if (aPriority !== bPriority) {
          return aPriority - bPriority;
        }

        // Then by timestamp
        return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
      });

      const results: SyncResult[] = [];

      // Process items in batches
      const batchSize = 5;
      for (let i = 0; i < sortedQueue.length; i += batchSize) {
        const batch = sortedQueue.slice(i, i + batchSize);
        const batchResults = await this.processBatch(batch);
        results.push(...batchResults);

        // Remove successfully synced items
        const successfullySynced = batchResults.filter(r => r.success).map(r => r.itemId);
        this.syncQueue = this.syncQueue.filter(item => !successfullySynced.includes(item.id));

        // Save updated queue
        await this.saveSyncQueue();
      }

      console.log(`Sync completed: ${results.filter(r => r.success).length}/${results.length} items synced`);
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      this.syncInProgress = false;
    }
  }

  private async processBatch(items: SyncQueueItem[]): Promise<SyncResult[]> {
    const results: SyncResult[] = [];

    for (const item of items) {
      try {
        const result = await this.processSyncItem(item);
        results.push(result);

        // Add delay between items to avoid overwhelming the server
        await new Promise(resolve => setTimeout(resolve, 100));
      } catch (error) {
        console.error(`Failed to sync item ${item.id}:`, error);
        results.push({
          itemId: item.id,
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    }

    return results;
  }

  private async processSyncItem(item: SyncQueueItem): Promise<SyncResult> {
    try {
      // Make API call based on operation type
      const response = await this.makeApiCall(item);

      if (response.success) {
        return {
          itemId: item.id,
          success: true,
        };
      } else {
        // Check if it's a conflict
        if (response.conflict) {
          const resolution = await this.handleConflict(item, response.serverData);

          if (resolution.resolved) {
            return {
              itemId: item.id,
              success: true,
            };
          } else {
            return {
              itemId: item.id,
              success: false,
              error: 'Conflict could not be resolved',
            };
          }
        } else {
          return {
            itemId: item.id,
            success: false,
            error: response.error || 'Sync failed',
          };
        }
      }
    } catch (error) {
      return {
        itemId: item.id,
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  private async makeApiCall(item: SyncQueueItem): Promise<any> {
    const url = `https://api.dmlogn8n.com/v1/${item.entityType}/${item.entityId}`;
    const token = await AsyncStorage.getItem('auth_token');

    const options: RequestInit = {
      method: this.getHttpMethod(item.operation),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'X-Device-ID': await this.getDeviceId(),
      },
    };

    if (item.operation !== 'delete' && item.data) {
      options.body = JSON.stringify(item.data);
    }

    const response = await fetch(url, options);
    const responseData = await response.json();

    if (!response.ok) {
      if (response.status === 409) {
        // Conflict
        return {
          success: false,
          conflict: true,
          serverData: responseData,
        };
      }

      throw new Error(responseData.error || `HTTP ${response.status}`);
    }

    return {
      success: true,
      data: responseData,
    };
  }

  private async handleConflict(item: SyncQueueItem, serverData: any): Promise<{ resolved: boolean; resolution?: any }> {
    try {
      switch (this.conflictResolution) {
        case 'client_wins':
          // Force client version to server
          await this.forceClientVersion(item);
          return { resolved: true };

        case 'server_wins':
          // Accept server version, discard client changes
          return { resolved: false };

        case 'merge':
          // Attempt to merge changes
          const merged = await this.mergeData(item.data, serverData);
          if (merged) {
            await this.forceMergedVersion(item, merged);
            return { resolved: true, resolution: merged };
          } else {
            return { resolved: false };
          }

        case 'prompt_user':
          // In a real app, this would show a UI dialog
          // For now, default to client wins
          console.warn('Conflict detected, defaulting to client wins');
          await this.forceClientVersion(item);
          return { resolved: true };

        default:
          return { resolved: false };
      }
    } catch (error) {
      console.error('Failed to handle conflict:', error);
      return { resolved: false };
    }
  }

  private async forceClientVersion(item: SyncQueueItem): Promise<void> {
    const url = `https://api.dmlogn8n.com/v1/${item.entityType}/${item.entityId}`;
    const token = await AsyncStorage.getItem('auth_token');

    const options: RequestInit = {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'X-Device-ID': await this.getDeviceId(),
        'X-Force-Client-Version': 'true',
      },
      body: JSON.stringify(item.data),
    };

    const response = await fetch(url, options);

    if (!response.ok) {
      throw new Error(`Failed to force client version: ${response.status}`);
    }
  }

  private async forceMergedVersion(item: SyncQueueItem, mergedData: any): Promise<void> {
    const url = `https://api.dmlogn8n.com/v1/${item.entityType}/${item.entityId}`;
    const token = await AsyncStorage.getItem('auth_token');

    const options: RequestInit = {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'X-Device-ID': await this.getDeviceId(),
        'X-Merge-Version': 'true',
      },
      body: JSON.stringify(mergedData),
    };

    const response = await fetch(url, options);

    if (!response.ok) {
      throw new Error(`Failed to force merged version: ${response.status}`);
    }
  }

  private async mergeData(clientData: any, serverData: any): Promise<any | null> {
    try {
      // Simple merge strategy - in a real app, this would be more sophisticated
      const merged = { ...serverData, ...clientData };

      // Preserve server timestamps
      if (serverData.updatedAt) {
        merged.updatedAt = serverData.updatedAt;
      }

      // Merge nested objects
      for (const key in clientData) {
        if (clientData[key] && typeof clientData[key] === 'object' && !Array.isArray(clientData[key])) {
          if (serverData[key] && typeof serverData[key] === 'object') {
            merged[key] = { ...serverData[key], ...clientData[key] };
          }
        }
      }

      return merged;
    } catch (error) {
      console.error('Failed to merge data:', error);
      return null;
    }
  }

  private getHttpMethod(operation: string): string {
    switch (operation) {
      case 'create':
        return 'POST';
      case 'update':
        return 'PUT';
      case 'delete':
        return 'DELETE';
      default:
        return 'POST';
    }
  }

  private async getDeviceId(): Promise<string> {
    try {
      let deviceId = await AsyncStorage.getItem('device_id');
      if (!deviceId) {
        deviceId = `mobile_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        await AsyncStorage.setItem('device_id', deviceId);
      }
      return deviceId;
    } catch (error) {
      console.error('Failed to get device ID:', error);
      return 'unknown_device';
    }
  }

  private async loadSyncQueue(): Promise<void> {
    try {
      const queueData = await AsyncStorage.getItem('sync_queue');
      if (queueData) {
        this.syncQueue = JSON.parse(queueData);
        console.log(`Loaded ${this.syncQueue.length} items from sync queue`);
      }
    } catch (error) {
      console.error('Failed to load sync queue:', error);
      this.syncQueue = [];
    }
  }

  private async saveSyncQueue(): Promise<void> {
    try {
      await AsyncStorage.setItem('sync_queue', JSON.stringify(this.syncQueue));
    } catch (error) {
      console.error('Failed to save sync queue:', error);
    }
  }

  async clearSyncQueue(): Promise<void> {
    try {
      this.syncQueue = [];
      await AsyncStorage.removeItem('sync_queue');
      console.log('Sync queue cleared');
    } catch (error) {
      console.error('Failed to clear sync queue:', error);
    }
  }

  getSyncQueueLength(): number {
    return this.syncQueue.length;
  }

  getIsOnline(): boolean {
    return this.isOnline;
  }

  getIsSyncing(): boolean {
    return this.syncInProgress;
  }

  getSyncQueueItems(): SyncQueueItem[] {
    return [...this.syncQueue];
  }

  async removeSyncItem(itemId: string): Promise<void> {
    this.syncQueue = this.syncQueue.filter(item => item.id !== itemId);
    await this.saveSyncQueue();
  }

  async retryFailedItems(): Promise<void> {
    const failedItems = this.syncQueue.filter(item => item.retryCount > 0);
    console.log(`Retrying ${failedItems.length} failed items`);

    // Reset retry count and move to front of queue
    failedItems.forEach(item => {
      item.retryCount = 0;
    });

    this.syncQueue = [...failedItems, ...this.syncQueue.filter(item => item.retryCount === 0)];
    await this.saveSyncQueue();

    if (this.isOnline) {
      this.startSync();
    }
  }

  async forceSyncNow(): Promise<void> {
    if (!this.isOnline) {
      throw new Error('Cannot sync while offline');
    }

    if (this.syncInProgress) {
      throw new Error('Sync already in progress');
    }

    await this.startSync();
  }
}