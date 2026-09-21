import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { View, Badge } from 'react-native';

// Tab Screens
import HomeScreen from '../screens/HomeScreen';
import CharactersScreen from '../screens/CharactersScreen';
import CampaignsScreen from '../screens/CampaignsScreen';
import CombatScreen from '../screens/CombatScreen';
import MessagesScreen from '../screens/MessagesScreen';
import NotificationsScreen from '../screens/NotificationsScreen';

import { RootState } from '../store';
import { useTheme } from '../hooks/useTheme';

const Tab = createBottomTabNavigator();

const TabNavigator = () => {
  const theme = useTheme();
  const { unreadCount } = useSelector((state: RootState) => state.notifications);
  const { activeCombat } = useSelector((state: RootState) => state.combat);

  const getTabIcon = (focused: boolean, name: string, color: string) => {
    return <Icon name={name} size={24} color={color} />;
  };

  const NotificationBadge = () => {
    if (unreadCount === 0) return null;
    return (
      <View
        style={{
          position: 'absolute',
          right: -6,
          top: -3,
          backgroundColor: '#FF4444',
          borderRadius: 10,
          width: 20,
          height: 20,
          justifyContent: 'center',
          alignItems: 'center',
        }}
      >
        <Badge
          style={{
            fontSize: 10,
            color: 'white',
            fontWeight: 'bold',
          }}
        >
          {unreadCount > 99 ? '99+' : unreadCount}
        </Badge>
      </View>
    );
  };

  const CombatBadge = () => {
    if (!activeCombat?.isActive) return null;
    return (
      <View
        style={{
          position: 'absolute',
          right: -6,
          top: -3,
          backgroundColor: '#44FF44',
          borderRadius: 10,
          width: 12,
          height: 12,
        }}
      />
    );
  };

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;

          switch (route.name) {
            case 'Home':
              iconName = 'home';
              break;
            case 'Characters':
              iconName = 'people';
              break;
            case 'Campaigns':
              iconName = 'explore';
              break;
            case 'Combat':
              iconName = 'sports-kabaddi';
              break;
            case 'Messages':
              iconName = 'chat';
              break;
            case 'Notifications':
              iconName = 'notifications';
              break;
            default:
              iconName = 'help';
          }

          return (
            <View style={{ position: 'relative' }}>
              {getTabIcon(focused, iconName, color)}
              {route.name === 'Notifications' && <NotificationBadge />}
              {route.name === 'Combat' && <CombatBadge />}
            </View>
          );
        },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textSecondary,
        tabBarStyle: {
          backgroundColor: theme.colors.background,
          borderTopColor: theme.colors.border,
          height: 60,
          paddingBottom: 5,
          paddingTop: 5,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '500',
        },
        headerShown: false,
      })}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarLabel: 'Home',
        }}
      />
      <Tab.Screen
        name="Characters"
        component={CharactersScreen}
        options={{
          tabBarLabel: 'Characters',
        }}
      />
      <Tab.Screen
        name="Campaigns"
        component={CampaignsScreen}
        options={{
          tabBarLabel: 'Campaigns',
        }}
      />
      <Tab.Screen
        name="Combat"
        component={CombatScreen}
        options={{
          tabBarLabel: 'Combat',
        }}
      />
      <Tab.Screen
        name="Messages"
        component={MessagesScreen}
        options={{
          tabBarLabel: 'Messages',
        }}
      />
      <Tab.Screen
        name="Notifications"
        component={NotificationsScreen}
        options={{
          tabBarLabel: 'Alerts',
        }}
      />
    </Tab.Navigator>
  );
};

export default TabNavigator;