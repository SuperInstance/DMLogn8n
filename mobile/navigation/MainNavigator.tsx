import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { Icon } from 'react-native-elements';
import { useTheme } from '@react-navigation/native';
import DashboardScreen from '../screens/DashboardScreen';
import CharactersScreen from '../screens/CharactersScreen';
import SessionsScreen from '../screens/SessionsScreen';
import ChatScreen from '../screens/ChatScreen';
import FriendsScreen from '../screens/FriendsScreen';
import ProfileScreen from '../screens/ProfileScreen';
import SettingsScreen from '../screens/SettingsScreen';
import CharacterDetailScreen from '../screens/CharacterDetailScreen';
import SessionDetailScreen from '../screens/SessionDetailScreen';
import CreateCharacterScreen from '../screens/CreateCharacterScreen';
import CreateSessionScreen from '../screens/CreateSessionScreen';
import FriendProfileScreen from '../screens/FriendProfileScreen';
import NotificationScreen from '../screens/NotificationScreen';

export type MainTabParamList = {
  Dashboard: undefined;
  Characters: undefined;
  Sessions: undefined;
  Chat: undefined;
  Friends: undefined;
};

export type MainStackParamList = {
  MainTabs: undefined;
  Profile: { userId?: string };
  Settings: undefined;
  CharacterDetail: { characterId: string };
  CreateCharacter: undefined;
  SessionDetail: { sessionId: string };
  CreateSession: undefined;
  FriendProfile: { userId: string };
  Notifications: undefined;
};

const Tab = createBottomTabNavigator<MainTabParamList>();
const Stack = createStackNavigator<MainStackParamList>();

const TabNavigator: React.FC = () => {
  const theme = useTheme();

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;

          switch (route.name) {
            case 'Dashboard':
              iconName = focused ? 'home' : 'home-outline';
              break;
            case 'Characters':
              iconName = focused ? 'people' : 'people-outline';
              break;
            case 'Sessions':
              iconName = focused ? 'game-controller' : 'game-controller-outline';
              break;
            case 'Chat':
              iconName = focused ? 'chatbubble' : 'chatbubble-outline';
              break;
            case 'Friends':
              iconName = focused ? 'person' : 'person-outline';
              break;
            default:
              iconName = 'help-outline';
          }

          return <Icon name={iconName} type="ionicon" size={size} color={color} />;
        },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textSecondary,
        tabBarStyle: {
          backgroundColor: theme.colors.tabBar,
          borderTopColor: theme.colors.border,
          borderTopWidth: 1,
          height: 60,
          paddingBottom: 8,
          paddingTop: 8,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '500',
        },
        headerShown: false,
        tabBarHideOnKeyboard: true,
      })}
    >
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{
          title: 'Home',
          tabBarLabel: 'Home',
        }}
      />
      <Tab.Screen
        name="Characters"
        component={CharactersScreen}
        options={{
          title: 'Characters',
          tabBarLabel: 'Characters',
        }}
      />
      <Tab.Screen
        name="Sessions"
        component={SessionsScreen}
        options={{
          title: 'Games',
          tabBarLabel: 'Games',
        }}
      />
      <Tab.Screen
        name="Chat"
        component={ChatScreen}
        options={{
          title: 'Chat',
          tabBarLabel: 'Chat',
        }}
      />
      <Tab.Screen
        name="Friends"
        component={FriendsScreen}
        options={{
          title: 'Friends',
          tabBarLabel: 'Friends',
        }}
      />
    </Tab.Navigator>
  );
};

const MainNavigator: React.FC = () => {
  const theme = useTheme();

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: theme.colors.background,
          borderBottomWidth: 0,
          elevation: 0,
          shadowOpacity: 0,
        },
        headerTintColor: theme.colors.text,
        headerTitleStyle: {
          fontFamily: 'System',
          fontSize: 18,
          fontWeight: '600',
        },
        headerBackTitleVisible: false,
        gestureEnabled: true,
        cardStyle: {
          backgroundColor: theme.colors.background,
        },
        presentation: 'modal',
      }}
    >
      <Stack.Screen
        name="MainTabs"
        component={TabNavigator}
        options={{
          headerShown: false,
        }}
      />
      <Stack.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          title: 'Profile',
          headerShown: true,
        }}
      />
      <Stack.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          title: 'Settings',
          headerShown: true,
        }}
      />
      <Stack.Screen
        name="CharacterDetail"
        component={CharacterDetailScreen}
        options={{
          title: 'Character Details',
          headerShown: true,
        }}
      />
      <Stack.Screen
        name="CreateCharacter"
        component={CreateCharacterScreen}
        options={{
          title: 'Create Character',
          headerShown: true,
          presentation: 'modal',
        }}
      />
      <Stack.Screen
        name="SessionDetail"
        component={SessionDetailScreen}
        options={{
          title: 'Game Details',
          headerShown: true,
        }}
      />
      <Stack.Screen
        name="CreateSession"
        component={CreateSessionScreen}
        options={{
          title: 'Create Game',
          headerShown: true,
          presentation: 'modal',
        }}
      />
      <Stack.Screen
        name="FriendProfile"
        component={FriendProfileScreen}
        options={{
          title: 'Friend Profile',
          headerShown: true,
        }}
      />
      <Stack.Screen
        name="Notifications"
        component={NotificationScreen}
        options={{
          title: 'Notifications',
          headerShown: true,
        }}
      />
    </Stack.Navigator>
  );
};

export default MainNavigator;