import React, { useState, useRef } from 'react';
import {
  View,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  TouchableWithoutFeedback,
  Keyboard,
  Alert,
} from 'react-native';
import {
  Text,
  Input,
  Button,
  SocialIcon,
  CheckBox,
  Icon,
} from 'react-native-elements';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useTheme } from '@react-navigation/native';
import { useDispatch } from 'react-redux';
import { login } from '../../store/slices/authSlice';
import { BiometricService } from '../../services/biometrics';
import { AuthStackParamList } from '../../navigation/AuthNavigator';
import { validateEmail, validatePassword } from '../../utils/validation';

type LoginScreenNavigationProp = NativeStackNavigationProp<AuthStackParamList, 'Login'>;

const LoginScreen: React.FC = () => {
  const navigation = useNavigation<LoginScreenNavigationProp>();
  const theme = useTheme();
  const dispatch = useDispatch();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [biometricAvailable, setBiometricAvailable] = useState(false);

  const passwordRef = useRef<Input>(null);

  React.useEffect(() => {
    checkBiometricAvailability();
  }, []);

  const checkBiometricAvailability = async () => {
    try {
      const isAvailable = await BiometricService.isAvailable();
      setBiometricAvailable(isAvailable);
    } catch (error) {
      console.error('Biometric check failed:', error);
    }
  };

  const handleInputChange = (field: string, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (!validatePassword(formData.password)) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleLogin = async () => {
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    try {
      const result = await dispatch(
        login({
          email: formData.email,
          password: formData.password,
          rememberMe: formData.rememberMe,
        })
      );

      if (login.rejected.match(result)) {
        Alert.alert('Login Failed', result.payload as string);
      }
    } catch (error) {
      Alert.alert('Login Failed', 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBiometricLogin = async () => {
    try {
      const result = await BiometricService.authenticate({
        promptMessage: 'Login with Biometrics',
        fallbackPromptMessage: 'Use password instead',
      });

      if (result.success) {
        // Dispatch biometric login action
        setIsLoading(true);
        const loginResult = await dispatch(
          login({
            biometricToken: result.token,
            rememberMe: true,
          })
        );

        if (login.rejected.match(loginResult)) {
          Alert.alert('Biometric Login Failed', loginResult.payload as string);
        }
      } else {
        Alert.alert('Biometric Authentication Failed', result.error || 'Unknown error');
      }
    } catch (error) {
      Alert.alert('Biometric Error', 'Failed to authenticate with biometrics');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSocialLogin = async (provider: 'google' | 'apple') => {
    // Implement social login logic
    Alert.alert('Coming Soon', `${provider} login will be available soon`);
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
        <View style={styles.content}>
          {/* Logo and Title */}
          <View style={styles.header}>
            <Text h1 style={[styles.title, { color: theme.colors.text }]}>
              Welcome Back
            </Text>
            <Text style={[styles.subtitle, { color: theme.colors.textSecondary }]}>
              Sign in to continue your adventure
            </Text>
          </View>

          {/* Login Form */}
          <View style={styles.form}>
            <Input
              label="Email"
              placeholder="Enter your email"
              value={formData.email}
              onChangeText={(value) => handleInputChange('email', value)}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              returnKeyType="next"
              onSubmitEditing={() => passwordRef.current?.focus()}
              errorMessage={errors.email}
              inputStyle={{ color: theme.colors.text }}
              labelStyle={{ color: theme.colors.textSecondary }}
              placeholderTextColor={theme.colors.textSecondary}
              leftIcon={
                <Icon
                  name="mail-outline"
                  type="ionicon"
                  color={theme.colors.textSecondary}
                />
              }
            />

            <Input
              ref={passwordRef}
              label="Password"
              placeholder="Enter your password"
              value={formData.password}
              onChangeText={(value) => handleInputChange('password', value)}
              secureTextEntry={!showPassword}
              returnKeyType="done"
              onSubmitEditing={handleLogin}
              errorMessage={errors.password}
              inputStyle={{ color: theme.colors.text }}
              labelStyle={{ color: theme.colors.textSecondary }}
              placeholderTextColor={theme.colors.textSecondary}
              leftIcon={
                <Icon
                  name="lock-closed-outline"
                  type="ionicon"
                  color={theme.colors.textSecondary}
                />
              }
              rightIcon={
                <Icon
                  name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                  type="ionicon"
                  color={theme.colors.textSecondary}
                  onPress={() => setShowPassword(!showPassword)}
                />
              }
            />

            <View style={styles.options}>
              <CheckBox
                title="Remember me"
                checked={formData.rememberMe}
                onPress={() => handleInputChange('rememberMe', !formData.rememberMe)}
                containerStyle={styles.checkboxContainer}
                textStyle={{ color: theme.colors.text }}
                checkedColor={theme.colors.primary}
              />

              <Button
                type="clear"
                title="Forgot Password?"
                onPress={() => navigation.navigate('ForgotPassword')}
                titleStyle={{
                  color: theme.colors.primary,
                  fontSize: 14,
                }}
              />
            </View>

            <Button
              title="Sign In"
              onPress={handleLogin}
              loading={isLoading}
              disabled={isLoading}
              buttonStyle={[
                styles.loginButton,
                { backgroundColor: theme.colors.primary },
              ]}
              titleStyle={styles.loginButtonText}
            />

            {biometricAvailable && (
              <Button
                type="outline"
                title="Sign in with Biometrics"
                onPress={handleBiometricLogin}
                disabled={isLoading}
                buttonStyle={[
                  styles.biometricButton,
                  { borderColor: theme.colors.primary },
                ]}
                titleStyle={[
                  styles.biometricButtonText,
                  { color: theme.colors.primary },
                ]}
                icon={
                  <Icon
                    name="finger-print-outline"
                    type="ionicon"
                    color={theme.colors.primary}
                    size={20}
                  />
                }
              />
            )}
          </View>

          {/* Social Login */}
          <View style={styles.socialSection}>
            <Text style={[styles.orText, { color: theme.colors.textSecondary }]}>
              Or continue with
            </Text>

            <View style={styles.socialButtons}>
              <SocialIcon
                type="google"
                onPress={() => handleSocialLogin('google')}
                style={styles.socialButton}
              />
              {Platform.OS === 'ios' && (
                <SocialIcon
                  type="apple"
                  onPress={() => handleSocialLogin('apple')}
                  style={styles.socialButton}
                />
              )}
            </View>
          </View>

          {/* Sign Up Link */}
          <View style={styles.footer}>
            <Text style={[styles.footerText, { color: theme.colors.textSecondary }]}>
              Don't have an account?{' '}
            </Text>
            <Button
              type="clear"
              title="Sign Up"
              onPress={() => navigation.navigate('Register')}
              titleStyle={{
                color: theme.colors.primary,
                fontWeight: '600',
              }}
            />
          </View>
        </View>
      </TouchableWithoutFeedback>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 60,
    paddingBottom: 32,
    justifyContent: 'space-between',
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
  },
  form: {
    flex: 1,
    justifyContent: 'center',
  },
  options: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginVertical: 16,
  },
  checkboxContainer: {
    backgroundColor: 'transparent',
    borderWidth: 0,
    padding: 0,
    margin: 0,
  },
  loginButton: {
    borderRadius: 12,
    paddingVertical: 16,
    marginTop: 8,
  },
  loginButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  biometricButton: {
    borderRadius: 12,
    paddingVertical: 16,
    marginTop: 16,
    borderWidth: 2,
  },
  biometricButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  socialSection: {
    marginTop: 32,
  },
  orText: {
    textAlign: 'center',
    fontSize: 14,
    marginBottom: 16,
  },
  socialButtons: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
  },
  socialButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 32,
  },
  footerText: {
    fontSize: 14,
  },
});

export default LoginScreen;