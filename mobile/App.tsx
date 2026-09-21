import React, { useEffect, useState } from 'react';
import { StatusBar, Platform, UIManager } from 'react-native';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { NavigationContainer } from '@react-navigation/native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ThemeProvider } from 'react-native-elements';
import { store, persistor } from './store';
import AppNavigator from './navigation/AppNavigator';
import { NotificationService } from './services/notifications';
import { OfflineService } from './services/offline';
import { BiometricService } from './services/biometrics';
import { useAppDispatch } from './hooks/redux';
import { initializeApp } from './store/slices/appSlice';
import { theme } from './constants/theme';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

const AppContent: React.FC = () => {
  const dispatch = useAppDispatch();
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    initializeServices();
  }, []);

  const initializeServices = async () => {
    try {
      // Initialize notification service
      await NotificationService.initialize();

      // Initialize offline service
      await OfflineService.initialize();

      // Initialize biometric service
      await BiometricService.initialize();

      // Initialize app state
      dispatch(initializeApp());

      setIsInitialized(true);
    } catch (error) {
      console.error('Failed to initialize app services:', error);
      setIsInitialized(true); // Continue even if some services fail
    }
  };

  if (!isInitialized) {
    return (
      <ThemeProvider theme={theme}>
        <SafeAreaProvider>
          <StatusBar barStyle="light-content" backgroundColor={theme.colors.primary} />
          {/* Add loading screen here */}
        </SafeAreaProvider>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <SafeAreaProvider>
        <NavigationContainer>
          <StatusBar
            barStyle="light-content"
            backgroundColor={theme.colors.primary}
            translucent={false}
          />
          <AppNavigator />
        </NavigationContainer>
      </SafeAreaProvider>
    </ThemeProvider>
  );
};

const App: React.FC = () => {
  return (
    <Provider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <AppContent />
      </PersistGate>
    </Provider>
  );
};

export default App;