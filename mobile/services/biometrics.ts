import { Platform, Alert, NativeModules } from 'react-native';
import TouchID from 'react-native-touch-id';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiService } from './api';
import { BiometricConfig, BiometricResult } from '../types';
import { API_CONFIG } from '../constants/api';

class BiometricService {
  private static instance: BiometricService;
  private isInitialized: boolean = false;
  private availableBiometry: 'touchid' | 'faceid' | 'biometrics' | null = null;

  private constructor() {}

  static getInstance(): BiometricService {
    if (!BiometricService.instance) {
      BiometricService.instance = new BiometricService();
    }
    return BiometricService.instance;
  }

  // Initialize biometric service
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    try {
      await this.checkBiometricAvailability();
      this.isInitialized = true;
      console.log('Biometric service initialized');
    } catch (error) {
      console.error('Failed to initialize biometric service:', error);
    }
  }

  // Check if biometric authentication is available
  async isAvailable(): Promise<boolean> {
    try {
      const available = await TouchID.isSupported();
      return available;
    } catch (error) {
      console.error('Biometric availability check failed:', error);
      return false;
    }
  }

  // Check biometric availability and get type
  private async checkBiometricAvailability(): Promise<void> {
    try {
      const available = await this.isAvailable();
      if (available) {
        // Get the type of biometric authentication available
        if (Platform.OS === 'ios') {
          // On iOS, we can check for Face ID vs Touch ID
          const biometryType = await this.getBiometryType();
          this.availableBiometry = biometryType;
        } else {
          // On Android, we just use generic 'biometrics'
          this.availableBiometry = 'biometrics';
        }
      }
    } catch (error) {
      console.error('Failed to check biometric availability:', error);
      this.availableBiometry = null;
    }
  }

  // Get the type of biometric authentication
  private async getBiometryType(): Promise<'touchid' | 'faceid' | 'biometrics'> {
    try {
      if (Platform.OS === 'ios') {
        // Check if Face ID is available (iOS 11+)
        const deviceInfo = await this.getDeviceInfo();
        if (deviceInfo.hasFaceId) {
          return 'faceid';
        } else {
          return 'touchid';
        }
      } else {
        return 'biometrics';
      }
    } catch (error) {
      console.error('Failed to get biometry type:', error);
      return 'biometrics';
    }
  }

  // Get device information
  private async getDeviceInfo(): Promise<{ hasFaceId: boolean }> {
    try {
      // This would typically use react-native-device-info
      // For now, we'll make a simple check based on device model
      return { hasFaceId: false };
    } catch (error) {
      return { hasFaceId: false };
    }
  }

  // Authenticate with biometrics
  async authenticate(options: {
    promptMessage?: string;
    fallbackPromptMessage?: string;
    passcodeFallback?: boolean;
    maxAttempts?: number;
    timeout?: number;
  } = {}): Promise<BiometricResult> {
    const {
      promptMessage = 'Authenticate with Biometrics',
      fallbackPromptMessage = 'Use Passcode',
      passcodeFallback = true,
      maxAttempts = 3,
      timeout = 10000,
    } = options;

    try {
      if (!this.availableBiometry) {
        return {
          success: false,
          error: 'Biometric authentication not available on this device',
        };
      }

      const config: any = {
        title: promptMessage,
        imageColor: '#6200EE',
        imageErrorColor: '#F44336',
        sensorDescription: 'Touch sensor',
        sensorErrorDescription: 'Failed',
        cancelText: 'Cancel',
        fallbackLabel: fallbackPromptMessage,
        unifiedErrors: false,
        passcodeFallback,
      };

      if (Platform.OS === 'ios') {
        config.biometryType = this.availableBiometry;
        if (this.availableBiometry === 'faceid') {
          config.sensorDescription = 'Face ID sensor';
          config.sensorErrorDescription = 'Face ID failed';
        } else {
          config.sensorDescription = 'Touch ID sensor';
          config.sensorErrorDescription = 'Touch ID failed';
        }
      }

      const success = await TouchID.authenticate(promptMessage, config);

      if (success) {
        return {
          success: true,
          biometryType: this.availableBiometry,
        };
      } else {
        return {
          success: false,
          error: 'Authentication failed',
        };
      }

    } catch (error: any) {
      console.error('Biometric authentication failed:', error);

      let errorMessage = 'Biometric authentication failed';

      // Handle specific error codes
      if (error.name === 'LAErrorUserFallback') {
        errorMessage = 'User chose fallback authentication';
      } else if (error.name === 'LAErrorUserCancel') {
        errorMessage = 'User cancelled authentication';
      } else if (error.name === 'LAErrorSystemCancel') {
        errorMessage = 'System cancelled authentication';
      } else if (error.name === 'LAErrorPasscodeNotSet') {
        errorMessage = 'No passcode set on device';
      } else if (error.name === 'LAErrorTouchIDNotAvailable') {
        errorMessage = 'Touch ID not available on this device';
      } else if (error.name === 'LAErrorTouchIDNotEnrolled') {
        errorMessage = 'No fingerprints enrolled';
      } else if (error.name === 'LAErrorTouchIDLockout') {
        errorMessage = 'Touch ID locked out due to too many failed attempts';
      } else if (error.name === 'RCTTouchIDUnknownError') {
        errorMessage = 'Unknown Touch ID error';
      } else if (error.message) {
        errorMessage = error.message;
      }

      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  // Setup biometric authentication for user
  async setupBiometricAuth(userId: string, config?: Partial<BiometricConfig>): Promise<BiometricResult> {
    try {
      // First authenticate to ensure user is the device owner
      const authResult = await this.authenticate({
        promptMessage: 'Setup Biometric Authentication',
        fallbackPromptMessage: 'Use Password',
      });

      if (!authResult.success) {
        return authResult;
      }

      // Generate biometric token
      const biometricToken = await this.generateBiometricToken(userId);

      // Register biometric token with server
      const response = await apiService.post('/auth/biometric/setup', {
        userId,
        biometricToken,
        deviceInfo: {
          platform: Platform.OS,
          biometryType: this.availableBiometry,
        },
        config: {
          allowDeviceCredentials: true,
          authenticateTimeout: 10000,
          maxAttempts: 3,
          resetOnFailure: false,
          ...config,
        },
      });

      if (response.success) {
        // Store biometric token locally
        await this.storeBiometricToken(userId, biometricToken);

        // Mark biometric as enabled
        await AsyncStorage.setItem(API_CONFIG.STORAGE_KEYS.BIOMETRIC_ENABLED, 'true');

        return {
          success: true,
          biometryType: this.availableBiometry,
        };
      } else {
        return {
          success: false,
          error: response.error || 'Failed to setup biometric authentication',
        };
      }

    } catch (error: any) {
      console.error('Failed to setup biometric auth:', error);
      return {
        success: false,
        error: error.message || 'Failed to setup biometric authentication',
      };
    }
  }

  // Authenticate with stored biometric token
  async authenticateWithBiometric(userId: string): Promise<BiometricResult> {
    try {
      // Check if biometric is enabled
      const biometricEnabled = await AsyncStorage.getItem(API_CONFIG.STORAGE_KEYS.BIOMETRIC_ENABLED);
      if (!biometricEnabled) {
        return {
          success: false,
          error: 'Biometric authentication not enabled',
        };
      }

      // Get stored biometric token
      const biometricToken = await this.getStoredBiometricToken(userId);
      if (!biometricToken) {
        return {
          success: false,
          error: 'No biometric token found',
        };
      }

      // Authenticate with biometrics
      const authResult = await this.authenticate({
        promptMessage: 'Sign In with Biometrics',
        fallbackPromptMessage: 'Use Password',
      });

      if (!authResult.success) {
        return authResult;
      }

      // Verify biometric token with server
      const response = await apiService.post('/auth/biometric/verify', {
        userId,
        biometricToken,
        deviceInfo: {
          platform: Platform.OS,
          biometryType: this.availableBiometry,
        },
      });

      if (response.success) {
        // Update stored token if server provides new one
        if (response.data?.biometricToken) {
          await this.storeBiometricToken(userId, response.data.biometricToken);
        }

        return {
          success: true,
          biometryType: this.availableBiometry,
          token: response.data?.authToken,
        };
      } else {
        return {
          success: false,
          error: response.error || 'Biometric verification failed',
        };
      }

    } catch (error: any) {
      console.error('Failed to authenticate with biometric:', error);
      return {
        success: false,
        error: error.message || 'Biometric authentication failed',
      };
    }
  }

  // Generate biometric token
  private async generateBiometricToken(userId: string): Promise<string> {
    // This would typically use the device's secure storage or crypto APIs
    // For now, we'll generate a simple token
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2);
    return `bio_${userId}_${timestamp}_${random}`;
  }

  // Store biometric token securely
  private async storeBiometricToken(userId: string, token: string): Promise<void> {
    try {
      const key = `@biometric_token_${userId}`;
      await AsyncStorage.setItem(key, token);
    } catch (error) {
      console.error('Failed to store biometric token:', error);
      throw error;
    }
  }

  // Get stored biometric token
  private async getStoredBiometricToken(userId: string): Promise<string | null> {
    try {
      const key = `@biometric_token_${userId}`;
      return await AsyncStorage.getItem(key);
    } catch (error) {
      console.error('Failed to get stored biometric token:', error);
      return null;
    }
  }

  // Remove biometric authentication
  async removeBiometricAuth(userId: string): Promise<BiometricResult> {
    try {
      // Remove from server
      const response = await apiService.post('/auth/biometric/remove', {
        userId,
        deviceInfo: {
          platform: Platform.OS,
          biometryType: this.availableBiometry,
        },
      });

      // Remove local storage
      await AsyncStorage.removeItem(`@biometric_token_${userId}`);
      await AsyncStorage.removeItem(API_CONFIG.STORAGE_KEYS.BIOMETRIC_ENABLED);

      return {
        success: true,
      };

    } catch (error: any) {
      console.error('Failed to remove biometric auth:', error);
      return {
        success: false,
        error: error.message || 'Failed to remove biometric authentication',
      };
    }
  }

  // Check if biometric is enabled for user
  async isBiometricEnabled(userId?: string): Promise<boolean> {
    try {
      const biometricEnabled = await AsyncStorage.getItem(API_CONFIG.STORAGE_KEYS.BIOMETRIC_ENABLED);
      if (!biometricEnabled) {
        return false;
      }

      if (userId) {
        const token = await this.getStoredBiometricToken(userId);
        return !!token;
      }

      return true;
    } catch (error) {
      console.error('Failed to check biometric status:', error);
      return false;
    }
  }

  // Get biometric type
  getBiometricType(): 'touchid' | 'faceid' | 'biometrics' | null {
    return this.availableBiometry;
  }

  // Get biometric type display name
  getBiometricTypeName(): string {
    switch (this.availableBiometry) {
      case 'faceid':
        return 'Face ID';
      case 'touchid':
        return 'Touch ID';
      case 'biometrics':
        return 'Biometrics';
      default:
        return 'Biometric Authentication';
    }
  }

  // Check if biometric setup is required
  async isSetupRequired(userId: string): Promise<boolean> {
    try {
      const isAvailable = await this.isAvailable();
      if (!isAvailable) {
        return false;
      }

      const isEnabled = await this.isBiometricEnabled(userId);
      return !isEnabled;
    } catch (error) {
      console.error('Failed to check setup requirement:', error);
      return false;
    }
  }

  // Prompt user to setup biometric authentication
  async promptSetup(userId: string): Promise<boolean> {
    return new Promise((resolve) => {
      Alert.alert(
        'Enable Biometric Authentication',
        `Would you like to enable ${this.getBiometricTypeName()} for faster sign-in?`,
        [
          {
            text: 'Not Now',
            style: 'cancel',
            onPress: () => resolve(false),
          },
          {
            text: 'Enable',
            onPress: async () => {
              try {
                const result = await this.setupBiometricAuth(userId);
                resolve(result.success);
              } catch (error) {
                console.error('Setup failed:', error);
                resolve(false);
              }
            },
          },
        ],
        { cancelable: true }
      );
    });
  }

  // Validate biometric configuration
  validateConfig(config: Partial<BiometricConfig>): boolean {
    const {
      allowDeviceCredentials = true,
      authenticateTimeout = 10000,
      maxAttempts = 3,
      resetOnFailure = false,
    } = config;

    // Validate timeout (between 5 seconds and 60 seconds)
    if (authenticateTimeout < 5000 || authenticateTimeout > 60000) {
      return false;
    }

    // Validate max attempts (between 1 and 10)
    if (maxAttempts < 1 || maxAttempts > 10) {
      return false;
    }

    return true;
  }

  // Get biometric statistics
  async getBiometricStats(userId: string): Promise<{
    isEnabled: boolean;
    type: string | null;
    lastUsed?: string;
    setupDate?: string;
  }> {
    try {
      const isEnabled = await this.isBiometricEnabled(userId);
      const token = await this.getStoredBiometricToken(userId);

      // In a real implementation, you'd get these from server or local storage
      return {
        isEnabled,
        type: this.getBiometricTypeName(),
        lastUsed: undefined,
        setupDate: undefined,
      };
    } catch (error) {
      console.error('Failed to get biometric stats:', error);
      return {
        isEnabled: false,
        type: null,
      };
    }
  }

  // Cleanup
  cleanup(): void {
    this.isInitialized = false;
    this.availableBiometry = null;
    console.log('Biometric service cleaned up');
  }
}

// Create singleton instance
export const biometricService = BiometricService.getInstance();
export default biometricService;