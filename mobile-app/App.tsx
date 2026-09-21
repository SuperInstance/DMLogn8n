import React, { useEffect, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { Provider as PaperProvider } from 'react-native-paper';
import { Provider as ReduxProvider } from 'react-redux';
import { ThemeProvider } from '@rneui/themed';
import * as SplashScreen from 'expo-splash-screen';
import * as Notifications from 'expo-notifications';

import AppNavigator from './src/navigation/AppNavigator';
import { store } from './src/store/store';
import { useAppDispatch } from './src/store/hooks';
import { initializeApp } from './src/store/slices/appSlice';
import { theme } from './src/theme/theme';
import { setupNotifications } from './src/services/notificationService';
import { setupDatabase } from './src/services/databaseService';
import { ErrorBoundary } from './src/components/common/ErrorBoundary';
import { NetworkStatus } from './src/components/common/NetworkStatus';

// Configure notifications
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

// Keep the splash screen visible while we initialize the app
SplashScreen.preventAutoHideAsync();

function AppContent() {
  const dispatch = useAppDispatch();
  const [isAppReady, setIsAppReady] = useState(false);

  useEffect(() => {
    async function prepare() {
      try {
        // Initialize services
        await setupNotifications();
        await setupDatabase();

        // Initialize app state
        await dispatch(initializeApp()).unwrap();

        // Hide splash screen
        await SplashScreen.hideAsync();
        setIsAppReady(true);
      } catch (error) {
        console.error('Error initializing app:', error);
        await SplashScreen.hideAsync();
        setIsAppReady(true);
      }
    }

    prepare();
  }, [dispatch]);

  if (!isAppReady) {
    return null;
  }

  return (
    <NavigationContainer>
      <PaperProvider theme={theme}>
        <ThemeProvider theme={theme}>
          <ErrorBoundary>
            <NetworkStatus />
            <AppNavigator />
            <StatusBar style="light" backgroundColor="#2C1810" />
          </ErrorBoundary>
        </ThemeProvider>
      </PaperProvider>
    </NavigationContainer>
  );
}

export default function App() {
  return (
    <ReduxProvider store={store}>
      <AppContent />
    </ReduxProvider>
  );
}