import { AppState, AppStateStatus } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { offlineService } from './offlineService';
import { networkService } from './networkService';
import { store } from '../store';

class BackgroundSyncService {
  private appStateSubscription: any = null;
  private syncInterval: NodeJS.Timeout | null = null;
  private isInitialized = false;

  initialize(): void {
    if (this.isInitialized) return;

    this.setupAppStateListener();
    this.setupPeriodicSync();
    this.isInitialized = true;

    console.log('Background sync service initialized');
  }

  private setupAppStateListener(): void {
    this.appStateSubscription = AppState.addEventListener(
      'change',
      this.handleAppStateChange.bind(this),
    );
  }

  private handleAppStateChange(nextAppState: AppStateStatus): void {
    if (nextAppState === 'active') {
      console.log('App became active, checking for sync...');
      this.performBackgroundSync();
    } else if (nextAppState === 'background') {
      console.log('App went to background');
      this.cleanupSyncInterval();
    }
  }

  private setupPeriodicSync(): void {
    const state = store.getState();
    const backgroundSyncEnabled = state.settings?.settings?.sync?.backgroundSync;

    if (backgroundSyncEnabled) {
      // Sync every 5 minutes when app is active
      this.syncInterval = setInterval(() => {
        this.performBackgroundSync();
      }, 5 * 60 * 1000);
    }
  }

  private async performBackgroundSync(): Promise<void> {
    try {
      // Check if we have network connection
      const isConnected = await networkService.getCurrentConnectionStatus();
      if (!isConnected) {
        console.log('No network connection, skipping background sync');
        return;
      }

      // Check if sync should only happen on WiFi
      const state = store.getState();
      const wifiOnly = state.settings?.settings?.sync?.wifiOnly;

      if (wifiOnly) {
        const isWifi = await networkService.isWifiConnection();
        if (!isWifi) {
          console.log('Not on WiFi, skipping background sync');
          return;
        }
      }

      // Initialize offline database
      await offlineService.initializeDatabase();

      // Perform sync
      const result = await offlineService.syncActions();

      if (result.success) {
        console.log('Background sync completed successfully');
        if (result.pendingActions.length > 0) {
          console.warn(`${result.pendingActions.length} actions still pending`);
        }

        // Update last sync time
        await this.updateLastSyncTime();
      } else {
        console.error('Background sync failed');
      }
    } catch (error) {
      console.error('Background sync error:', error);
    }
  }

  private async updateLastSyncTime(): Promise<void> {
    try {
      await AsyncStorage.setItem('lastSyncTime', new Date().toISOString());
    } catch (error) {
      console.error('Failed to update last sync time:', error);
    }
  }

  async getLastSyncTime(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem('lastSyncTime');
    } catch (error) {
      console.error('Failed to get last sync time:', error);
      return null;
    }
  }

  async forceSync(): Promise<{ success: boolean; pendingActions: number }> {
    try {
      await offlineService.initializeDatabase();
      const result = await offlineService.syncActions();

      if (result.success) {
        await this.updateLastSyncTime();
      }

      return {
        success: result.success,
        pendingActions: result.pendingActions.length,
      };
    } catch (error) {
      console.error('Force sync error:', error);
      return {
        success: false,
        pendingActions: 0,
      };
    }
  }

  private cleanupSyncInterval(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }

  cleanup(): void {
    this.cleanupSyncInterval();

    if (this.appStateSubscription) {
      this.appStateSubscription.remove();
      this.appStateSubscription = null;
    }

    this.isInitialized = false;
  }
}

export const backgroundSyncService = new BackgroundSyncService();

export const setupBackgroundSync = (): void => {
  backgroundSyncService.initialize();
};