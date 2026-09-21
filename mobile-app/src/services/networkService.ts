import NetInfo from '@react-native-community/netinfo';
import { store } from '../store';
import { setConnectionStatus } from '../store/slices/offlineSlice';
import { offlineService } from './offlineService';

class NetworkService {
  private unsubscribe: (() => void) | null = null;

  initialize(): void {
    this.setupNetworkListener();
  }

  private setupNetworkListener(): void {
    this.unsubscribe = NetInfo.addEventListener(state => {
      const isConnected = state.isConnected ?? false;

      // Update Redux store
      store.dispatch(setConnectionStatus(isConnected));

      // If connection is restored, attempt to sync offline actions
      if (isConnected) {
        this.handleConnectionRestored();
      }
    });
  }

  private async handleConnectionRestored(): Promise<void> {
    try {
      console.log('Connection restored, syncing offline actions...');

      // Initialize offline database if not already done
      await offlineService.initializeDatabase();

      // Sync pending actions
      const result = await offlineService.syncActions();

      if (result.success) {
        console.log('Offline actions synced successfully');
        if (result.pendingActions.length > 0) {
          console.warn(`${result.pendingActions.length} actions still pending sync`);
        }
      } else {
        console.error('Failed to sync some offline actions');
      }
    } catch (error) {
      console.error('Error handling connection restoration:', error);
    }
  }

  async getCurrentConnectionStatus(): Promise<boolean> {
    try {
      const state = await NetInfo.fetch();
      return state.isConnected ?? false;
    } catch (error) {
      console.error('Error getting connection status:', error);
      return false;
    }
  }

  async waitForConnection(timeout: number = 30000): Promise<boolean> {
    return new Promise((resolve) => {
      let timeoutId: NodeJS.Timeout;

      const checkConnection = async () => {
        const isConnected = await this.getCurrentConnectionStatus();
        if (isConnected) {
          clearTimeout(timeoutId);
          if (this.unsubscribe) {
            this.unsubscribe();
          }
          resolve(true);
        }
      };

      // Check immediately
      checkConnection();

      // Set up listener for connection changes
      this.unsubscribe = NetInfo.addEventListener(state => {
        if (state.isConnected) {
          clearTimeout(timeoutId);
          if (this.unsubscribe) {
            this.unsubscribe();
          }
          resolve(true);
        }
      });

      // Set timeout
      timeoutId = setTimeout(() => {
        if (this.unsubscribe) {
          this.unsubscribe();
        }
        resolve(false);
      }, timeout);
    });
  }

  async isWifiConnection(): Promise<boolean> {
    try {
      const state = await NetInfo.fetch();
      return state.type === NetInfo.NETWORK_TYPE_WIFI;
    } catch (error) {
      console.error('Error checking WiFi connection:', error);
      return false;
    }
  }

  getConnectionType(): string {
    // This would typically return the current connection type
    // Implementation depends on NetInfo configuration
    return 'unknown';
  }

  cleanup(): void {
    if (this.unsubscribe) {
      this.unsubscribe();
      this.unsubscribe = null;
    }
  }
}

export const networkService = new NetworkService();

export const setupNetworkListener = (): void => {
  networkService.initialize();
};