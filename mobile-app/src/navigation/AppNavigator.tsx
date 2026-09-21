import React, { useEffect } from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useSelector, useDispatch } from 'react-redux';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { useAppSelector } from '../store/hooks';

// Import screens
import LoginScreen from '../screens/auth/LoginScreen';
import RegisterScreen from '../screens/auth/RegisterScreen';
import OnboardingScreen from '../screens/onboarding/OnboardingScreen';
import DashboardScreen from '../screens/dashboard/DashboardScreen';
import CharacterListScreen from '../screens/characters/CharacterListScreen';
import CharacterDetailScreen from '../screens/characters/CharacterDetailScreen';
import CharacterCreateScreen from '../screens/characters/CharacterCreateScreen';
import CampaignListScreen from '../screens/campaigns/CampaignListScreen';
import CampaignDetailScreen from '../screens/campaigns/CampaignDetailScreen';
import SessionScreen from '../screens/sessions/SessionScreen';
import DiceRollerScreen from '../screens/dice/DiceRollerScreen';
import VoiceChatScreen from '../screens/voice/VoiceChatScreen';
import ARScannerScreen from '../screens/ar/ARScannerScreen';
import SettingsScreen from '../screens/settings/SettingsScreen';
import CombatTrackerScreen from '../screens/combat/CombatTrackerScreen';
import ChatScreen from '../screens/chat/ChatScreen';

// Import types
import { RootStackParamList, TabParamList } from '../types/navigation';

// Import actions
import { initializeApp } from '../store/slices/appSlice';
import { restoreAuth } from '../store/slices/authSlice';

const Stack = createStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<TabParamList>();

// Auth stack for unauthenticated users
const AuthStack = () => {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        cardStyle: { backgroundColor: '#2C1810' },
      }}
      initialRouteName="Login"
    >
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
    </Stack.Navigator>
  );
};

// Main app tabs for authenticated users
const MainTabs = () => {
  const { colors } = require('../theme/theme');

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;

          switch (route.name) {
            case 'Dashboard':
              iconName = 'dashboard';
              break;
            case 'Characters':
              iconName = 'people';
              break;
            case 'Campaigns':
              iconName = 'campaign';
              break;
            case 'Dice':
              iconName = 'casino';
              break;
            case 'Session':
              iconName = 'play-circle';
              break;
            case 'AR':
              iconName = 'view-in-ar';
              break;
            case 'Chat':
              iconName = 'chat';
              break;
            case 'Settings':
              iconName = 'settings';
              break;
            default:
              iconName = 'help';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.primary + '30',
          height: 60,
          paddingBottom: 5,
          paddingTop: 5,
        },
        headerStyle: {
          backgroundColor: colors.background,
          borderBottomColor: colors.primary + '30',
          borderBottomWidth: 1,
        },
        headerTintColor: colors.text,
        headerTitleStyle: {
          fontFamily: 'Cinzel-Regular',
          fontWeight: '600',
        },
      })}
    >
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{ title: 'Dashboard' }}
      />
      <Tab.Screen
        name="Characters"
        component={CharacterListScreen}
        options={{ title: 'Characters' }}
      />
      <Tab.Screen
        name="Campaigns"
        component={CampaignListScreen}
        options={{ title: 'Campaigns' }}
      />
      <Tab.Screen
        name="Dice"
        component={DiceRollerScreen}
        options={{ title: 'Dice Roller' }}
      />
      <Tab.Screen
        name="Session"
        component={SessionScreen}
        options={{ title: 'Session' }}
      />
      <Tab.Screen
        name="AR"
        component={ARScannerScreen}
        options={{ title: 'AR Scanner' }}
      />
      <Tab.Screen
        name="Chat"
        component={ChatScreen}
        options={{ title: 'Chat' }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{ title: 'Settings' }}
      />
    </Tab.Navigator>
  );
};

// Main stack navigator
const AppNavigator = () => {
  const dispatch = useDispatch();
  const { isAuthenticated, isInitialized } = useAppSelector(state => state.auth);
  const { showOnboarding } = useAppSelector(state => state.app);

  useEffect(() => {
    // Initialize app and restore auth state
    const initialize = async () => {
      try {
        // Restore auth from storage
        const authData = await require('../services/storageService').getAuthData();
        if (authData) {
          dispatch(restoreAuth(authData));
        }

        // Initialize app
        dispatch(initializeApp());
      } catch (error) {
        console.error('Failed to initialize app:', error);
        dispatch(initializeApp());
      }
    };

    initialize();
  }, [dispatch]);

  // Show loading screen while initializing
  if (!isInitialized) {
    return null;
  }

  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        cardStyle: { backgroundColor: '#2C1810' },
      }}
    >
      {showOnboarding ? (
        <Stack.Screen name="Onboarding" component={OnboardingScreen} />
      ) : isAuthenticated ? (
        <>
          <Stack.Screen name="MainTabs" component={MainTabs} options={{ headerShown: false }} />
          <Stack.Screen
            name="CharacterDetail"
            component={CharacterDetailScreen}
            options={{
              title: 'Character Details',
              headerShown: true,
            }}
          />
          <Stack.Screen
            name="CharacterCreate"
            component={CharacterCreateScreen}
            options={{
              title: 'Create Character',
              headerShown: true,
            }}
          />
          <Stack.Screen
            name="CampaignDetail"
            component={CampaignDetailScreen}
            options={{
              title: 'Campaign Details',
              headerShown: true,
            }}
          />
          <Stack.Screen
            name="VoiceChat"
            component={VoiceChatScreen}
            options={{
              title: 'Voice Chat',
              headerShown: true,
            }}
          />
          <Stack.Screen
            name="CombatTracker"
            component={CombatTrackerScreen}
            options={{
              title: 'Combat Tracker',
              headerShown: true,
            }}
          />
        </>
      ) : (
        <Stack.Screen name="Auth" component={AuthStack} />
      )}
    </Stack.Navigator>
  );
};

export default AppNavigator;