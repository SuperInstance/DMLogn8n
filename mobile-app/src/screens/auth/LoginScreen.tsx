import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';

import { loginUser, loginWithBiometric, setBiometricEnabled } from '../../store/slices/authSlice';
import { RootState } from '../../store';
import { useTheme } from '../../hooks/useTheme';
import { hapticService } from '../../services/hapticService';
import { authService } from '../../services/authService';

type LoginScreenNavigationProp = StackNavigationProp<AuthStackParamList, 'Login'>;

interface AuthStackParamList {
  Login: undefined;
  Register: undefined;
  BiometricSetup: undefined;
}

const LoginScreen: React.FC = () => {
  const dispatch = useDispatch();
  const navigation = useNavigation<LoginScreenNavigationProp>();
  const theme = useTheme();

  const { isLoading, error, biometricEnabled } = useSelector((state: RootState) => state.auth);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showBiometricOption, setShowBiometricOption] = useState(false);

  useEffect(() => {
    checkBiometricAvailability();
  }, []);

  const checkBiometricAvailability = async () => {
    const isBiometricAvailable = await authService.isBiometricEnabled();
    setShowBiometricOption(isBiometricAvailable);
  };

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    hapticService.light();
    dispatch(loginUser({ email, password }))
      .unwrap()
      .catch((error) => {
        Alert.alert('Login Failed', error);
      });
  };

  const handleBiometricLogin = async () => {
    hapticService.medium();
    dispatch(loginWithBiometric())
      .unwrap()
      .catch((error) => {
        Alert.alert('Biometric Login Failed', error);
      });
  };

  const navigateToRegister = () => {
    hapticService.selection();
    navigation.navigate('Register');
  };

  const navigateToBiometricSetup = () => {
    hapticService.selection();
    navigation.navigate('BiometricSetup');
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.content}>
          {/* Logo and Title */}
          <View style={styles.header}>
            <Text style={[styles.title, { color: theme.colors.text }]}>
              DMlogn8n
            </Text>
            <Text style={[styles.subtitle, { color: theme.colors.textSecondary }]}>
              Your D&D Companion
            </Text>
          </View>

          {/* Login Form */}
          <View style={styles.form}>
            <TextInput
              style={[
                styles.input,
                {
                  backgroundColor: theme.colors.surface,
                  color: theme.colors.text,
                  borderColor: theme.colors.border,
                },
              ]}
              placeholder="Email"
              placeholderTextColor={theme.colors.textSecondary}
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
            />

            <TextInput
              style={[
                styles.input,
                {
                  backgroundColor: theme.colors.surface,
                  color: theme.colors.text,
                  borderColor: theme.colors.border,
                },
              ]}
              placeholder="Password"
              placeholderTextColor={theme.colors.textSecondary}
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              autoCapitalize="none"
            />

            {error && (
              <Text style={[styles.errorText, { color: theme.colors.error }]}>
                {error}
              </Text>
            )}

            <TouchableOpacity
              style={[
                styles.loginButton,
                {
                  backgroundColor: theme.colors.primary,
                  opacity: isLoading ? 0.7 : 1,
                },
              ]}
              onPress={handleLogin}
              disabled={isLoading}
            >
              {isLoading ? (
                <ActivityIndicator color="white" />
              ) : (
                <Text style={styles.loginButtonText}>Login</Text>
              )}
            </TouchableOpacity>

            {/* Biometric Login Option */}
            {showBiometricOption && (
              <TouchableOpacity
                style={[
                  styles.biometricButton,
                  {
                    backgroundColor: theme.colors.surface,
                    borderColor: theme.colors.border,
                  },
                ]}
                onPress={handleBiometricLogin}
              >
                <Text style={[styles.biometricButtonText, { color: theme.colors.primary }]}>
                  Login with Biometrics
                </Text>
              </TouchableOpacity>
            )}
          </View>

          {/* Footer Links */}
          <View style={styles.footer}>
            <TouchableOpacity onPress={navigateToRegister}>
              <Text style={[styles.linkText, { color: theme.colors.primary }]}>
                Don't have an account? Sign Up
              </Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={navigateToBiometricSetup}>
              <Text style={[styles.linkText, { color: theme.colors.primary }]}>
                Setup Biometric Login
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    paddingVertical: 32,
  },
  header: {
    alignItems: 'center',
    marginBottom: 48,
  },
  title: {
    fontSize: 48,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
  },
  form: {
    marginBottom: 32,
  },
  input: {
    height: 56,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 16,
    marginBottom: 16,
    fontSize: 16,
  },
  errorText: {
    textAlign: 'center',
    marginBottom: 16,
    fontSize: 14,
  },
  loginButton: {
    height: 56,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  loginButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  biometricButton: {
    height: 56,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
  },
  biometricButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  footer: {
    alignItems: 'center',
  },
  linkText: {
    fontSize: 14,
    marginBottom: 8,
    textDecorationLine: 'underline',
  },
});

export default LoginScreen;