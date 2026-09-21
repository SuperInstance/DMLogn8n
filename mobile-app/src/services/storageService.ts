import AsyncStorage from '@react-native-async-storage/async-storage';
import { User, Character, Campaign, Session } from '../types';

export class StorageService {
  private static instance: StorageService;
  private isInitialized: boolean = false;

  private constructor() {}

  static getInstance(): StorageService {
    if (!StorageService.instance) {
      StorageService.instance = new StorageService();
    }
    return StorageService.instance;
  }

  async initialize(): Promise<void> {
    try {
      // Test AsyncStorage availability
      await AsyncStorage.setItem('test_key', 'test_value');
      await AsyncStorage.removeItem('test_key');

      this.isInitialized = true;
      console.log('Storage service initialized');
    } catch (error) {
      console.error('Failed to initialize storage service:', error);
      this.isInitialized = false;
    }
  }

  // Authentication data
  async storeAuthToken(token: string): Promise<void> {
    try {
      await AsyncStorage.setItem('auth_token', token);
    } catch (error) {
      console.error('Failed to store auth token:', error);
      throw error;
    }
  }

  async getAuthToken(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem('auth_token');
    } catch (error) {
      console.error('Failed to get auth token:', error);
      return null;
    }
  }

  async clearAuthData(): Promise<void> {
    try {
      await AsyncStorage.multiRemove(['auth_token', 'user_data', 'refresh_token']);
    } catch (error) {
      console.error('Failed to clear auth data:', error);
      throw error;
    }
  }

  // User data
  async storeUserData(user: User): Promise<void> {
    try {
      await AsyncStorage.setItem('user_data', JSON.stringify(user));
    } catch (error) {
      console.error('Failed to store user data:', error);
      throw error;
    }
  }

  async getUserData(): Promise<User | null> {
    try {
      const userData = await AsyncStorage.getItem('user_data');
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error('Failed to get user data:', error);
      return null;
    }
  }

  // Character data
  async storeCharacter(character: Character): Promise<void> {
    try {
      const key = `character_${character.id}`;
      await AsyncStorage.setItem(key, JSON.stringify(character));

      // Update character index
      const index = await this.getCharacterIndex();
      if (!index.includes(character.id)) {
        index.push(character.id);
        await AsyncStorage.setItem('character_index', JSON.stringify(index));
      }
    } catch (error) {
      console.error('Failed to store character:', error);
      throw error;
    }
  }

  async getCharacter(characterId: string): Promise<Character | null> {
    try {
      const key = `character_${characterId}`;
      const characterData = await AsyncStorage.getItem(key);
      return characterData ? JSON.parse(characterData) : null;
    } catch (error) {
      console.error('Failed to get character:', error);
      return null;
    }
  }

  async getAllCharacters(): Promise<Character[]> {
    try {
      const index = await this.getCharacterIndex();
      const characters: Character[] = [];

      for (const id of index) {
        const character = await this.getCharacter(id);
        if (character) {
          characters.push(character);
        }
      }

      return characters;
    } catch (error) {
      console.error('Failed to get all characters:', error);
      return [];
    }
  }

  async deleteCharacter(characterId: string): Promise<void> {
    try {
      const key = `character_${characterId}`;
      await AsyncStorage.removeItem(key);

      // Update character index
      const index = await this.getCharacterIndex();
      const updatedIndex = index.filter(id => id !== characterId);
      await AsyncStorage.setItem('character_index', JSON.stringify(updatedIndex));
    } catch (error) {
      console.error('Failed to delete character:', error);
      throw error;
    }
  }

  private async getCharacterIndex(): Promise<string[]> {
    try {
      const index = await AsyncStorage.getItem('character_index');
      return index ? JSON.parse(index) : [];
    } catch (error) {
      console.error('Failed to get character index:', error);
      return [];
    }
  }

  // Campaign data
  async storeCampaign(campaign: Campaign): Promise<void> {
    try {
      const key = `campaign_${campaign.id}`;
      await AsyncStorage.setItem(key, JSON.stringify(campaign));

      // Update campaign index
      const index = await this.getCampaignIndex();
      if (!index.includes(campaign.id)) {
        index.push(campaign.id);
        await AsyncStorage.setItem('campaign_index', JSON.stringify(index));
      }
    } catch (error) {
      console.error('Failed to store campaign:', error);
      throw error;
    }
  }

  async getCampaign(campaignId: string): Promise<Campaign | null> {
    try {
      const key = `campaign_${campaignId}`;
      const campaignData = await AsyncStorage.getItem(key);
      return campaignData ? JSON.parse(campaignData) : null;
    } catch (error) {
      console.error('Failed to get campaign:', error);
      return null;
    }
  }

  async getAllCampaigns(): Promise<Campaign[]> {
    try {
      const index = await this.getCampaignIndex();
      const campaigns: Campaign[] = [];

      for (const id of index) {
        const campaign = await this.getCampaign(id);
        if (campaign) {
          campaigns.push(campaign);
        }
      }

      return campaigns;
    } catch (error) {
      console.error('Failed to get all campaigns:', error);
      return [];
    }
  }

  async deleteCampaign(campaignId: string): Promise<void> {
    try {
      const key = `campaign_${campaignId}`;
      await AsyncStorage.removeItem(key);

      // Update campaign index
      const index = await this.getCampaignIndex();
      const updatedIndex = index.filter(id => id !== campaignId);
      await AsyncStorage.setItem('campaign_index', JSON.stringify(updatedIndex));
    } catch (error) {
      console.error('Failed to delete campaign:', error);
      throw error;
    }
  }

  private async getCampaignIndex(): Promise<string[]> {
    try {
      const index = await AsyncStorage.getItem('campaign_index');
      return index ? JSON.parse(index) : [];
    } catch (error) {
      console.error('Failed to get campaign index:', error);
      return [];
    }
  }

  // Session data
  async storeSession(session: Session): Promise<void> {
    try {
      const key = `session_${session.id}`;
      await AsyncStorage.setItem(key, JSON.stringify(session));

      // Update session index
      const index = await this.getSessionIndex();
      if (!index.includes(session.id)) {
        index.push(session.id);
        await AsyncStorage.setItem('session_index', JSON.stringify(index));
      }
    } catch (error) {
      console.error('Failed to store session:', error);
      throw error;
    }
  }

  async getSession(sessionId: string): Promise<Session | null> {
    try {
      const key = `session_${sessionId}`;
      const sessionData = await AsyncStorage.getItem(key);
      return sessionData ? JSON.parse(sessionData) : null;
    } catch (error) {
      console.error('Failed to get session:', error);
      return null;
    }
  }

  async getAllSessions(): Promise<Session[]> {
    try {
      const index = await this.getSessionIndex();
      const sessions: Session[] = [];

      for (const id of index) {
        const session = await this.getSession(id);
        if (session) {
          sessions.push(session);
        }
      }

      return sessions;
    } catch (error) {
      console.error('Failed to get all sessions:', error);
      return [];
    }
  }

  private async getSessionIndex(): Promise<string[]> {
    try {
      const index = await AsyncStorage.getItem('session_index');
      return index ? JSON.parse(index) : [];
    } catch (error) {
      console.error('Failed to get session index:', error);
      return [];
    }
  }

  // Settings and preferences
  async storeSetting(key: string, value: any): Promise<void> {
    try {
      await AsyncStorage.setItem(`setting_${key}`, JSON.stringify(value));
    } catch (error) {
      console.error(`Failed to store setting ${key}:`, error);
      throw error;
    }
  }

  async getSetting(key: string, defaultValue?: any): Promise<any> {
    try {
      const value = await AsyncStorage.getItem(`setting_${key}`);
      return value ? JSON.parse(value) : defaultValue;
    } catch (error) {
      console.error(`Failed to get setting ${key}:`, error);
      return defaultValue;
    }
  }

  // App preferences
  async storePreferences(preferences: any): Promise<void> {
    try {
      await AsyncStorage.setItem('app_preferences', JSON.stringify(preferences));
    } catch (error) {
      console.error('Failed to store preferences:', error);
      throw error;
    }
  }

  async getPreferences(): Promise<any> {
    try {
      const preferences = await AsyncStorage.getItem('app_preferences');
      return preferences ? JSON.parse(preferences) : {};
    } catch (error) {
      console.error('Failed to get preferences:', error);
      return {};
    }
  }

  // Cache management
  async clearCache(): Promise<void> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter(key => key.startsWith('cache_'));

      if (cacheKeys.length > 0) {
        await AsyncStorage.multiRemove(cacheKeys);
        console.log(`Cleared ${cacheKeys.length} cache entries`);
      }
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  }

  async getStorageInfo(): Promise<{
    totalKeys: number;
    approximateSize: string;
    lastCleanup: string | null;
  }> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const totalKeys = keys.length;

      // Estimate size (this is approximate)
      let totalSize = 0;
      for (const key of keys.slice(0, 10)) { // Sample first 10 keys
        const value = await AsyncStorage.getItem(key);
        if (value) {
          totalSize += (key.length + value.length) * 2; // Rough estimate
        }
      }

      const approximateSize = this.formatBytes(totalSize * (keys.length / 10));

      const lastCleanup = await this.getSetting('last_cleanup', null);

      return {
        totalKeys,
        approximateSize,
        lastCleanup,
      };
    } catch (error) {
      console.error('Failed to get storage info:', error);
      return {
        totalKeys: 0,
        approximateSize: '0 B',
        lastCleanup: null,
      };
    }
  }

  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // Biometric settings
  async setBiometricEnabled(enabled: boolean): Promise<void> {
    await this.storeSetting('biometric_enabled', enabled);
  }

  async isBiometricEnabled(): Promise<boolean> {
    return await this.getSetting('biometric_enabled', false);
  }

  // Backup and restore
  async exportData(): Promise<{
    user: User | null;
    characters: Character[];
    campaigns: Campaign[];
    sessions: Session[];
    preferences: any;
  }> {
    try {
      const user = await this.getUserData();
      const characters = await this.getAllCharacters();
      const campaigns = await this.getAllCampaigns();
      const sessions = await this.getAllSessions();
      const preferences = await this.getPreferences();

      return {
        user,
        characters,
        campaigns,
        sessions,
        preferences,
      };
    } catch (error) {
      console.error('Failed to export data:', error);
      throw error;
    }
  }

  async importData(data: {
    user?: User;
    characters?: Character[];
    campaigns?: Campaign[];
    sessions?: Session[];
    preferences?: any;
  }): Promise<void> {
    try {
      if (data.user) {
        await this.storeUserData(data.user);
      }

      if (data.characters) {
        for (const character of data.characters) {
          await this.storeCharacter(character);
        }
      }

      if (data.campaigns) {
        for (const campaign of data.campaigns) {
          await this.storeCampaign(campaign);
        }
      }

      if (data.sessions) {
        for (const session of data.sessions) {
          await this.storeSession(session);
        }
      }

      if (data.preferences) {
        await this.storePreferences(data.preferences);
      }

      console.log('Data imported successfully');
    } catch (error) {
      console.error('Failed to import data:', error);
      throw error;
    }
  }

  getIsInitialized(): boolean {
    return this.isInitialized;
  }
}