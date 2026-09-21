import AsyncStorage from '@react-native-async-storage/async-storage';
import { Character } from '../types';

const API_BASE_URL = __DEV__ ? 'http://localhost:3000/api' : 'https://api.dmlogn8n.com';

class CharacterService {
  async getAllCharacters(): Promise<Character[]> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/characters`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch characters');
      }

      return await response.json();
    } catch (error) {
      console.error('Get all characters error:', error);
      throw error;
    }
  }

  async getCharacter(characterId: string): Promise<Character> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/characters/${characterId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch character');
      }

      return await response.json();
    } catch (error) {
      console.error('Get character error:', error);
      throw error;
    }
  }

  async createCharacter(characterData: Omit<Character, 'id' | 'createdAt' | 'updatedAt'>): Promise<Character> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/characters`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(characterData),
      });

      if (!response.ok) {
        throw new Error('Failed to create character');
      }

      return await response.json();
    } catch (error) {
      console.error('Create character error:', error);
      throw error;
    }
  }

  async updateCharacter(characterId: string, data: Partial<Character>): Promise<Character> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/characters/${characterId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to update character');
      }

      return await response.json();
    } catch (error) {
      console.error('Update character error:', error);
      throw error;
    }
  }

  async deleteCharacter(characterId: string): Promise<void> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const response = await fetch(`${API_BASE_URL}/characters/${characterId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete character');
      }
    } catch (error) {
      console.error('Delete character error:', error);
      throw error;
    }
  }

  async uploadAvatar(characterId: string, imageUri: string): Promise<string> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) throw new Error('No authentication token');

      const formData = new FormData();

      // Get file info from URI
      const uriParts = imageUri.split('.');
      const fileType = uriParts[uriParts.length - 1];

      formData.append('avatar', {
        uri: imageUri,
        name: `character_${characterId}_avatar.${fileType}`,
        type: `image/${fileType}`,
      } as any);

      const response = await fetch(`${API_BASE_URL}/characters/${characterId}/avatar`, {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to upload avatar');
      }

      const data = await response.json();
      return data.avatarUrl;
    } catch (error) {
      console.error('Upload avatar error:', error);
      throw error;
    }
  }
}

export const characterService = new CharacterService();