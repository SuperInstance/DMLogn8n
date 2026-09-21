import React, { useEffect } from 'react';
import { StatusBar, Platform } from 'react-native';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { store, persistor } from './store';
import AppNavigator from './navigation/AppNavigator';
import { setupNotificationListeners } from './services/notificationService';
import { setupNetworkListener } from './services/networkService';
import { setupBackgroundSync } from './services/backgroundSyncService';
import { useTheme } from './hooks/useTheme';
import { ThemeProvider } from './contexts/ThemeContext';
import { BiometricProvider } from './contexts/BiometricContext';
import { LocationProvider } from './contexts/LocationContext';
import { HapticProvider } from './contexts/HapticContext';

const AppContent = () => {
  const theme = useTheme();

  useEffect(() => {
    // Initialize app services
    const initializeServices = async () => {
      try {
        // Setup notification listeners
        await setupNotificationListeners();

        // Setup network listener
        setupNetworkListener();

        // Setup background sync
        setupBackgroundSync();

        console.log('App services initialized successfully');
      } catch (error) {
        console.error('Failed to initialize app services:', error);
      }
    };

    initializeServices();
  }, []);

  return (
    <>
      <StatusBar
        barStyle={Platform.OS === 'ios' ? 'light-content' : 'default'}
        backgroundColor={theme.colors.background}
        translucent={false}
      />
      <AppNavigator />
    </>
  );
};

const App = () => {
  return (
    <Provider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <ThemeProvider>
          <BiometricProvider>
            <LocationProvider>
              <HapticProvider>
                <AppContent />
              </HapticProvider>
            </LocationProvider>
          </BiometricProvider>
        </ThemeProvider>
      </PersistGate>
    </Provider>
  );
};

export default App;