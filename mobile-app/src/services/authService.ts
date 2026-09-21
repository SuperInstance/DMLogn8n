import AsyncStorage from '@react-native-async-storage/async-storage';
import ReactNativeBiometrics from 'react-native-biometrics';
import { User } from '../types';

const API_BASE_URL = __DEV__ ? 'http://localhost:3000/api' : 'https://api.dmlogn8n.com';

class AuthService {
  private biometrics = new ReactNativeBiometrics();

  async login(email: string, password: string): Promise<{ user: User; accessToken: string; refreshToken: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Login failed');
      }

      const data = await response.json();

      // Store tokens
      await AsyncStorage.setItem('accessToken', data.accessToken);
      await AsyncStorage.setItem('refreshToken', data.refreshToken);

      return data;
    } catch (error) {
      throw error;
    }
  }

  async register(userData: { username: string; email: string; password: string }): Promise<{ user: User; accessToken: string; refreshToken: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Registration failed');
      }

      const data = await response.json();

      // Store tokens
      await AsyncStorage.setItem('accessToken', data.accessToken);
      await AsyncStorage.setItem('refreshToken', data.refreshToken);

      return data;
    } catch (error) {
      throw error;
    }
  }

  async biometricLogin(): Promise<{ user: User; accessToken: string; refreshToken: string }> {
    try {
      // Check if biometrics is available
      const { available, biometryType } = await this.biometrics.isSensorAvailable();

      if (!available) {
        throw new Error('Biometric authentication not available');
      }

      // Get stored user credentials for biometric login
      const biometricKeyId = await AsyncStorage.getItem('biometricKeyId');
      if (!biometricKeyId) {
        throw new Error('No biometric credentials found');
      }

      // Authenticate with biometrics
      const { success } = await this.biometrics.simplePrompt({
        promptMessage: 'Authenticate to access DMlogn8n',
        cancelButtonText: 'Cancel',
      });

      if (!success) {
        throw new Error('Biometric authentication cancelled');
      }

      // Get stored tokens
      const accessToken = await AsyncStorage.getItem('accessToken');
      const refreshToken = await AsyncStorage.getItem('refreshToken');
      const userData = await AsyncStorage.getItem('user');

      if (!accessToken || !refreshToken || !userData) {
        throw new Error('No stored credentials found');
      }

      const user = JSON.parse(userData);
      return { user, accessToken, refreshToken };
    } catch (error) {
      throw error;
    }
  }

  async setupBiometricAuth(userId: string): Promise<boolean> {
    try {
      const { available, biometryType } = await this.biometrics.isSensorAvailable();

      if (!available) {
        return false;
      }

      // Create biometric keys
      const { publicKey } = await this.biometrics.createKeys();

      // Store the key identifier for this user
      await AsyncStorage.setItem('biometricKeyId', publicKey);
      await AsyncStorage.setItem('biometricUserId', userId);

      return true;
    } catch (error) {
      console.error('Failed to setup biometric auth:', error);
      return false;
    }
  }

  async refreshToken(refreshToken: string): Promise<{ accessToken: string; refreshToken: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();

      // Store new tokens
      await AsyncStorage.setItem('accessToken', data.accessToken);
      await AsyncStorage.setItem('refreshToken', data.refreshToken);

      return data;
    } catch (error) {
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      // Clear stored tokens
      await AsyncStorage.removeItem('accessToken');
      await AsyncStorage.removeItem('refreshToken');
      await AsyncStorage.removeItem('user');
      await AsyncStorage.removeItem('biometricKeyId');
      await AsyncStorage.removeItem('biometricUserId');
    } catch (error) {
      console.error('Logout error:', error);
    }
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      const token = await AsyncStorage.getItem('accessToken');
      if (!token) return null;

      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        return null;
      }

      const user = await response.json();
      return user;
    } catch (error) {
      console.error('Get current user error:', error);
      return null;
    }
  }

  async getStoredTokens(): Promise<{ accessToken: string | null; refreshToken: string | null }> {
    try {
      const accessToken = await AsyncStorage.getItem('accessToken');
      const refreshToken = await AsyncStorage.getItem('refreshToken');
      return { accessToken, refreshToken };
    } catch (error) {
      console.error('Get stored tokens error:', error);
      return { accessToken: null, refreshToken: null };
    }
  }

  async isBiometricEnabled(): Promise<boolean> {
    try {
      const biometricKeyId = await AsyncStorage.getItem('biometricKeyId');
      return !!biometricKeyId;
    } catch (error) {
      return false;
    }
  }
}

export const authService = new AuthService();