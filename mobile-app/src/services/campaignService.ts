import AsyncStorage from '@react-native-async-storage/async-storage';
import { Campaign } from '../types';

const API_BASE_URL = __DEV__ ? 'http://localhost:3000/api' : 'https://api.dmlogn8n.com';

class CampaignService {
  async getAllCampaigns(): Promise<Campaign[]> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/campaigns`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch campaigns');
      }

      return await response.json();
    } catch (error) {
      console.error('Get all campaigns error:', error);
      throw error;
    }
  }

  async getCampaign(campaignId: string): Promise<Campaign> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/campaigns/${campaignId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch campaign');
      }

      return await response.json();
    } catch (error) {
      console.error('Get campaign error:', error);
      throw error;
    }
  }

  async joinCampaign(campaignId: string): Promise<Campaign> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/campaigns/${campaignId}/join`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to join campaign');
      }

      return await response.json();
    } catch (error) {
      console.error('Join campaign error:', error);
      throw error;
    }
  }

  async leaveCampaign(campaignId: string): Promise<void> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/campaigns/${campaignId}/leave`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to leave campaign');
      }
    } catch (error) {
      console.error('Leave campaign error:', error);
      throw error;
    }
  }
}

export const campaignService = new CampaignService();