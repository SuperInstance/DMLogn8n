import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { setBiometricEnabled } from '../../store/slices/authSlice';
import { RootState } from '../../store';
import { useTheme } from '../../hooks/useTheme';
import { hapticService } from '../../services/hapticService';
import { authService } from '../../services/authService';

type BiometricSetupScreenNavigationProp = StackNavigationProp<AuthStackParamList, 'BiometricSetup'>;

interface AuthStackParamList {
  Login: undefined;
  Register: undefined;
  BiometricSetup: undefined;
}

const BiometricSetupScreen: React.FC = () => {
  const dispatch = useDispatch();
  const navigation = useNavigation<BiometricSetupScreenNavigationProp>();
  const theme = useTheme();

  const { user } = useSelector((state: RootState) => state.auth);

  const [isSettingUp, setIsSettingUp] = useState(false);
  const [isAvailable, setIsAvailable] = useState(false);
  const [biometryType, setBiometryType] = useState<string>('');

  useEffect(() => {
    checkBiometricAvailability();
  }, []);

  const checkBiometricAvailability = async () => {
    try {
      const ReactNativeBiometrics = require('react-native-biometrics').default;
      const rnBiometrics = new ReactNativeBiometrics();

      const { available, biometryType } = await rnBiometrics.isSensorAvailable();
      setIsAvailable(available);
      setBiometryType(biometryType || 'biometric');
    } catch (error) {
      console.error('Error checking biometric availability:', error);
      setIsAvailable(false);
    }
  };

  const handleSetupBiometric = async () => {
    if (!user) {
      Alert.alert('Error', 'Please login first');
      return;
    }

    setIsSettingUp(true);
    hapticService.medium();

    try {
      const success = await authService.setupBiometricAuth(user.id);

      if (success) {
        dispatch(setBiometricEnabled(true));
        Alert.alert(
          'Success',
          `${biometryType.charAt(0).toUpperCase() + biometryType.slice(1)} authentication enabled!`,
          [
            {
              text: 'OK',
              onPress: () => navigation.goBack(),
            },
          ]
        );
      } else {
        Alert.alert('Setup Failed', 'Unable to setup biometric authentication');
      }
    } catch (error) {
      Alert.alert('Setup Failed', 'An error occurred while setting up biometric authentication');
    } finally {
      setIsSettingUp(false);
    }
  };

  const handleSkip = () => {
    hapticService.selection();
    navigation.goBack();
  };

  const getBiometricIcon = () => {
    switch (biometryType.toLowerCase()) {
      case 'touchid':
        return 'fingerprint';
      case 'faceid':
        return 'face';
      case 'biometrics':
        return 'fingerprint';
      default:
        return 'security';
    }
  };

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.content}
    >
      <View style={styles.header}>
        <View style={[styles.iconContainer, { backgroundColor: theme.colors.primary + '20' }]}>
          <Icon
            name={getBiometricIcon()}
            size={64}
            color={theme.colors.primary}
          />
        </View>
        <Text style={[styles.title, { color: theme.colors.text }]}>
          Enable Biometric Login
        </Text>
        <Text style={[styles.subtitle, { color: theme.colors.textSecondary }]}>
          Use {biometryType.charAt(0).toUpperCase() + biometryType.slice(1)} for quick and secure access
        </Text>
      </View>

      {isAvailable ? (
        <View style={styles.content}>
          <View style={[styles.benefitsContainer, { backgroundColor: theme.colors.surface }]}>
            <Text style={[styles.benefitsTitle, { color: theme.colors.text }]}>
              Benefits:
            </Text>
            <View style={styles.benefitItem}>
              <Icon name="check-circle" size={20} color={theme.colors.primary} />
              <Text style={[styles.benefitText, { color: theme.colors.textSecondary }]}>
                Quick and secure login
              </Text>
            </View>
            <View style={styles.benefitItem}>
              <Icon name="check-circle" size={20} color={theme.colors.primary} />
              <Text style={[styles.benefitText, { color: theme.colors.textSecondary }]}>
                No need to remember passwords
              </Text>
            </View>
            <View style={styles.benefitItem}>
              <Icon name="check-circle" size={20} color={theme.colors.primary} />
              <Text style={[styles.benefitText, { color: theme.colors.textSecondary }]}>
                Enterprise-grade security
              </Text>
            </View>
          </View>

          <TouchableOpacity
            style={[
              styles.setupButton,
              {
                backgroundColor: theme.colors.primary,
                opacity: isSettingUp ? 0.7 : 1,
              },
            ]}
            onPress={handleSetupBiometric}
            disabled={isSettingUp}
          >
            {isSettingUp ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text style={styles.setupButtonText}>
                Enable {biometryType.charAt(0).toUpperCase() + biometryType.slice(1)} Login
              </Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity style={styles.skipButton} onPress={handleSkip}>
            <Text style={[styles.skipButtonText, { color: theme.colors.textSecondary }]}>
              Maybe Later
            </Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.notAvailableContainer}>
          <Icon name="error-outline" size={48} color={theme.colors.error} />
          <Text style={[styles.notAvailableTitle, { color: theme.colors.text }]}>
            Biometric Authentication Not Available
          </Text>
          <Text style={[styles.notAvailableText, { color: theme.colors.textSecondary }]}>
            Your device doesn't support biometric authentication or it's not enabled.
          </Text>
          <TouchableOpacity style={styles.skipButton} onPress={handleSkip}>
            <Text style={[styles.skipButtonText, { color: theme.colors.primary }]}>
              Continue
            </Text>
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flexGrow: 1,
    padding: 24,
  },
  header: {
    alignItems: 'center',
    marginBottom: 32,
  },
  iconContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  benefitsContainer: {
    padding: 20,
    borderRadius: 12,
    marginBottom: 32,
  },
  benefitsTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  benefitItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  benefitText: {
    fontSize: 16,
    marginLeft: 12,
  },
  setupButton: {
    height: 56,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  setupButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  skipButton: {
    paddingVertical: 12,
  },
  skipButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  notAvailableContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  notAvailableTitle: {
    fontSize: 20,
    fontWeight: '600',
    textAlign: 'center',
    marginTop: 16,
    marginBottom: 8,
  },
  notAvailableText: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 32,
  },
});

export default BiometricSetupScreen;