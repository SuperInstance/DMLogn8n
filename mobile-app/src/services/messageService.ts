import AsyncStorage from '@react-native-async-storage/async-storage';
import { Message } from '../types';

const API_BASE_URL = __DEV__ ? 'http://localhost:3000/api' : 'https://api.dmlogn8n.com';

class MessageService {
  async getCampaignMessages(campaignId: string): Promise<Message[]> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/campaigns/${campaignId}/messages`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch messages');
      }

      return await response.json();
    } catch (error) {
      console.error('Get campaign messages error:', error);
      throw error;
    }
  }

  async sendMessage(messageData: Omit<Message, 'id' | 'timestamp'>): Promise<Message> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(messageData),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      return await response.json();
    } catch (error) {
      console.error('Send message error:', error);
      throw error;
    }
  }

  async sendDiceRoll(diceData: {
    campaignId: string;
    dice: string;
    result: number;
    rolls: number[];
    modifier: number;
    total: number;
    reason: string;
    characterName?: string;
  }): Promise<Message> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/messages/dice-roll`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(diceData),
      });

      if (!response.ok) {
        throw new Error('Failed to send dice roll');
      }

      return await response.json();
    } catch (error) {
      console.error('Send dice roll error:', error);
      throw error;
    }
  }
}

export const messageService = new MessageService();