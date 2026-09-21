import AsyncStorage from '@react-native-async-storage/async-storage';
import { Combat, CombatParticipant } from '../types';

const API_BASE_URL = __DEV__ ? 'http://localhost:3000/api' : 'https://api.dmlogn8n.com';

class CombatService {
  async getActiveCombat(campaignId: string): Promise<Combat | null> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/campaigns/${campaignId}/combat/active`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.status === 404) {
        return null;
      }

      if (!response.ok) {
        throw new Error('Failed to fetch active combat');
      }

      return await response.json();
    } catch (error) {
      console.error('Get active combat error:', error);
      throw error;
    }
  }

  async startCombat(campaignId: string, participants: CombatParticipant[]): Promise<Combat> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/campaigns/${campaignId}/combat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ participants }),
      });

      if (!response.ok) {
        throw new Error('Failed to start combat');
      }

      return await response.json();
    } catch (error) {
      console.error('Start combat error:', error);
      throw error;
    }
  }

  async endCombat(combatId: string): Promise<void> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/combat/${combatId}/end`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to end combat');
      }
    } catch (error) {
      console.error('End combat error:', error);
      throw error;
    }
  }

  async nextTurn(combatId: string): Promise<Combat> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/combat/${combatId}/next-turn`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to advance turn');
      }

      return await response.json();
    } catch (error) {
      console.error('Next turn error:', error);
      throw error;
    }
  }

  async updateParticipant(combatId: string, participantId: string, data: Partial<CombatParticipant>): Promise<Combat> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/combat/${combatId}/participants/${participantId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to update participant');
      }

      return await response.json();
    } catch (error) {
      console.error('Update participant error:', error);
      throw error;
    }
  }
}

export const combatService = new CombatService();