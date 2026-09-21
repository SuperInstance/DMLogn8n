import AsyncStorage from '@react-native-async-storage/async-storage';
import SQLite from 'react-native-sqlite-storage';
import { OfflineAction } from '../types';

SQLite.DEBUG(__DEV__);
SQLite.enablePromise(true);

class OfflineService {
  private database: SQLite.SQLiteDatabase | null = null;

  async initializeDatabase(): Promise<void> {
    try {
      this.database = await SQLite.openDatabase({
        name: 'DMlogn8nOffline.db',
        location: 'default',
      });

      await this.createTables();
      console.log('Offline database initialized');
    } catch (error) {
      console.error('Failed to initialize offline database:', error);
      throw error;
    }
  }

  private async createTables(): Promise<void> {
    if (!this.database) throw new Error('Database not initialized');

    const createOfflineActionsTable = `
      CREATE TABLE IF NOT EXISTS offline_actions (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        entity TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        data TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        is_synced INTEGER DEFAULT 0,
        retry_count INTEGER DEFAULT 0
      )
    `;

    await this.database.executeSql(createOfflineActionsTable);
  }

  async addAction(actionData: Omit<OfflineAction, 'id' | 'timestamp' | 'isSynced' | 'retryCount'>): Promise<OfflineAction> {
    if (!this.database) throw new Error('Database not initialized');

    const id = Date.now().toString();
    const timestamp = new Date().toISOString();

    const action: OfflineAction = {
      id,
      ...actionData,
      timestamp,
      isSynced: false,
      retryCount: 0,
    };

    const query = `
      INSERT INTO offline_actions (id, type, entity, entity_id, data, timestamp, is_synced, retry_count)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `;

    const params = [
      action.id,
      action.type,
      action.entity,
      action.entityId,
      JSON.stringify(action.data),
      action.timestamp,
      action.isSynced ? 1 : 0,
      action.retryCount,
    ];

    await this.database.executeSql(query, params);
    return action;
  }

  async getPendingActions(): Promise<OfflineAction[]> {
    if (!this.database) throw new Error('Database not initialized');

    const query = `
      SELECT * FROM offline_actions
      WHERE is_synced = 0
      ORDER BY timestamp ASC
    `;

    const [results] = await this.database.executeSql(query);
    const actions: OfflineAction[] = [];

    for (let i = 0; i < results.rows.length; i++) {
      const row = results.rows.item(i);
      actions.push({
        id: row.id,
        type: row.type,
        entity: row.entity,
        entityId: row.entity_id,
        data: JSON.parse(row.data),
        timestamp: row.timestamp,
        isSynced: row.is_synced === 1,
        retryCount: row.retry_count,
      });
    }

    return actions;
  }

  async markActionAsSynced(actionId: string): Promise<void> {
    if (!this.database) throw new Error('Database not initialized');

    const query = `
      UPDATE offline_actions
      SET is_synced = 1
      WHERE id = ?
    `;

    await this.database.executeSql(query, [actionId]);
  }

  async incrementRetryCount(actionId: string): Promise<void> {
    if (!this.database) throw new Error('Database not initialized');

    const query = `
      UPDATE offline_actions
      SET retry_count = retry_count + 1
      WHERE id = ?
    `;

    await this.database.executeSql(query, [actionId]);
  }

  async deleteSyncedActions(): Promise<void> {
    if (!this.database) throw new Error('Database not initialized');

    const query = `
      DELETE FROM offline_actions
      WHERE is_synced = 1
    `;

    await this.database.executeSql(query);
  }

  async retryAction(actionId: string): Promise<{ success: boolean; error?: string }> {
    try {
      const actions = await this.getPendingActions();
      const action = actions.find(a => a.id === actionId);

      if (!action) {
        return { success: false, error: 'Action not found' };
      }

      // Get auth token
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) {
        return { success: false, error: 'No auth token' };
      }

      // Sync the action based on its type and entity
      let success = false;
      const API_BASE_URL = __DEV__ ? 'http://localhost:3000/api' : 'https://api.dmlogn8n.com';

      switch (action.entity) {
        case 'character':
          if (action.type === 'create') {
            const response = await fetch(`${API_BASE_URL}/characters`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
              },
              body: JSON.stringify(action.data),
            });
            success = response.ok;
          } else if (action.type === 'update') {
            const response = await fetch(`${API_BASE_URL}/characters/${action.entityId}`, {
              method: 'PUT',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
              },
              body: JSON.stringify(action.data),
            });
            success = response.ok;
          }
          break;

        case 'message':
          if (action.type === 'create') {
            const response = await fetch(`${API_BASE_URL}/messages`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
              },
              body: JSON.stringify(action.data),
            });
            success = response.ok;
          }
          break;

        // Add more entity types as needed
        default:
          success = false;
      }

      if (success) {
        await this.markActionAsSynced(actionId);
        return { success: true };
      } else {
        await this.incrementRetryCount(actionId);
        return { success: false, error: 'Sync failed' };
      }
    } catch (error) {
      await this.incrementRetryCount(actionId);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  async syncActions(): Promise<{ success: boolean; pendingActions: OfflineAction[] }> {
    try {
      const pendingActions = await this.getPendingActions();

      for (const action of pendingActions) {
        if (action.retryCount >= 3) {
          // Skip actions that have failed too many times
          continue;
        }

        const result = await this.retryAction(action.id);
        if (!result.success) {
          console.warn(`Failed to sync action ${action.id}:`, result.error);
        }
      }

      const remainingActions = await this.getPendingActions();
      return { success: true, pendingActions: remainingActions };
    } catch (error) {
      console.error('Sync actions error:', error);
      const pendingActions = await this.getPendingActions();
      return { success: false, pendingActions };
    }
  }

  async clearSyncedActions(): Promise<void> {
    if (!this.database) throw new Error('Database not initialized');
    await this.deleteSyncedActions();
  }

  async cleanup(): Promise<void> {
    if (this.database) {
      await this.database.close();
      this.database = null;
    }
  }
}

export const offlineService = new OfflineService();