import React, { useEffect } from 'react';
import { useSelector } from 'react-redux';
import { createStackNavigator } from '@react-navigation/stack';
import { NavigationContainer } from '@react-navigation/native';
import { RootState } from '../store';
import AuthNavigator from './AuthNavigator';
import MainNavigator from './MainNavigator';
import GameNavigator from './GameNavigator';
import { useAppDispatch } from '../hooks/redux';
import { initializeApp, checkAuthStatus } from '../store/slices/authSlice';
import { initializeNotifications } from '../store/slices/notificationSlice';
import { initializeOfflineMode } from '../store/slices/offlineSlice';
import LoadingScreen from '../screens/LoadingScreen';

export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  Game: { sessionId: string };
  Loading: undefined;
};

const Stack = createStackNavigator<RootStackParamList>();

const AppNavigator: React.FC = () => {
  const dispatch = useAppDispatch();
  const { isAuthenticated, isInitialized, isLoading } = useSelector((state: RootState) => state.auth);
  const { currentSession } = useSelector((state: RootState) => state.game);

  useEffect(() => {
    dispatch(initializeApp());
    dispatch(checkAuthStatus());
    dispatch(initializeNotifications());
    dispatch(initializeOfflineMode());
  }, [dispatch]);

  if (!isInitialized || isLoading) {
    return <LoadingScreen />;
  }

  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerShown: false,
          animationTypeForReplace: 'push',
          animationEnabled: true,
          gestureEnabled: true,
        }}
        initialRouteName={isAuthenticated ? 'Main' : 'Auth'}
      >
        {!isAuthenticated ? (
          <Stack.Screen name="Auth" component={AuthNavigator} />
        ) : currentSession ? (
          <Stack.Screen name="Game" component={GameNavigator} />
        ) : (
          <Stack.Screen name="Main" component={MainNavigator} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;