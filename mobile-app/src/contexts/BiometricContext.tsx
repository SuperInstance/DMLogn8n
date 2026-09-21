import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

interface BiometricContextType {
  isAvailable: boolean;
  isEnabled: boolean;
  biometryType: string;
  isLoading: boolean;
  checkAvailability: () => Promise<void>;
  enableBiometric: (userId: string) => Promise<boolean>;
  disableBiometric: () => Promise<void>;
  authenticate: () => Promise<boolean>;
}

const BiometricContext = createContext<BiometricContextType | undefined>(undefined);

interface BiometricProviderProps {
  children: React.ReactNode;
}

export const BiometricProvider: React.FC<BiometricProviderProps> = ({ children }) => {
  const [isAvailable, setIsAvailable] = useState(false);
  const [isEnabled, setIsEnabled] = useState(false);
  const [biometryType, setBiometryType] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAvailability();
  }, []);

  const checkAvailability = async () => {
    try {
      setIsLoading(true);
      const ReactNativeBiometrics = require('react-native-biometrics').default;
      const rnBiometrics = new ReactNativeBiometrics();

      const { available, biometryType } = await rnBiometrics.isSensorAvailable();
      setIsAvailable(available);
      setBiometryType(biometryType || '');

      if (available) {
        const enabled = await authService.isBiometricEnabled();
        setIsEnabled(enabled);
      }
    } catch (error) {
      console.error('Error checking biometric availability:', error);
      setIsAvailable(false);
    } finally {
      setIsLoading(false);
    }
  };

  const enableBiometric = async (userId: string): Promise<boolean> => {
    try {
      const success = await authService.setupBiometricAuth(userId);
      if (success) {
        setIsEnabled(true);
      }
      return success;
    } catch (error) {
      console.error('Error enabling biometric:', error);
      return false;
    }
  };

  const disableBiometric = async (): Promise<void> => {
    try {
      await authService.logout();
      setIsEnabled(false);
    } catch (error) {
      console.error('Error disabling biometric:', error);
    }
  };

  const authenticate = async (): Promise<boolean> => {
    if (!isAvailable || !isEnabled) {
      return false;
    }

    try {
      await authService.biometricLogin();
      return true;
    } catch (error) {
      console.error('Biometric authentication failed:', error);
      return false;
    }
  };

  return (
    <BiometricContext.Provider
      value={{
        isAvailable,
        isEnabled,
        biometryType,
        isLoading,
        checkAvailability,
        enableBiometric,
        disableBiometric,
        authenticate,
      }}
    >
      {children}
    </BiometricContext.Provider>
  );
};

export const useBiometric = () => {
  const context = useContext(BiometricContext);
  if (!context) {
    throw new Error('useBiometric must be used within a BiometricProvider');
  }
  return context;
};