import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { fetchCharacters } from '../../store/slices/characterSlice';
import { fetchCampaigns } from '../../store/slices/campaignSlice';
import { fetchNotifications } from '../../store/slices/notificationSlice';
import { RootState } from '../../store';
import { useTheme } from '../../hooks/useTheme';
import { hapticService } from '../../services/hapticService';
import { CharacterCard } from '../../components/CharacterCard';
import { CampaignCard } from '../../components/CampaignCard';
import { NotificationCard } from '../../components/NotificationCard';
import { QuickActions } from '../../components/QuickActions';
import { LoadingSpinner } from '../../components/LoadingSpinner';

const HomeScreen: React.FC = () => {
  const dispatch = useDispatch();
  const navigation = useNavigation();
  const theme = useTheme();

  const {
    user,
    characters,
    campaigns,
    notifications,
    isLoading,
  } = useSelector((state: RootState) => ({
    user: state.auth.user,
    characters: state.characters.characters.slice(0, 3), // Show first 3 characters
    campaigns: state.campaigns.campaigns.slice(0, 3), // Show first 3 campaigns
    notifications: state.notifications.notifications.slice(0, 5), // Show first 5 notifications
    isLoading: state.characters.isLoading || state.campaigns.isLoading || state.notifications.isLoading,
  }));

  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      await Promise.all([
        dispatch(fetchCharacters()).unwrap(),
        dispatch(fetchCampaigns()).unwrap(),
        dispatch(fetchNotifications()).unwrap(),
      ]);
    } catch (error) {
      console.error('Failed to load initial data:', error);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    hapticService.light();
    await loadInitialData();
    setRefreshing(false);
  };

  const handleCharacterPress = (characterId: string) => {
    hapticService.selection();
    // Navigate to character details
    navigation.navigate('CharacterDetails' as never, { characterId } as never);
  };

  const handleCampaignPress = (campaignId: string) => {
    hapticService.selection();
    // Navigate to campaign details
    navigation.navigate('CampaignDetails' as never, { campaignId } as never);
  };

  const handleNotificationPress = (notificationId: string) => {
    hapticService.selection();
    // Navigate to notification details or mark as read
  };

  const navigateToAllCharacters = () => {
    hapticService.selection();
    navigation.navigate('Characters' as never);
  };

  const navigateToAllCampaigns = () => {
    hapticService.selection();
    navigation.navigate('Campaigns' as never);
  };

  const navigateToAllNotifications = () => {
    hapticService.selection();
    navigation.navigate('Notifications' as never);
  };

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={handleRefresh}
          tintColor={theme.colors.primary}
        />
      }
      contentContainerStyle={styles.content}
    >
      {/* Welcome Header */}
      <View style={styles.header}>
        <View>
          <Text style={[styles.welcomeText, { color: theme.colors.textSecondary }]}>
            Welcome back,
          </Text>
          <Text style={[styles.usernameText, { color: theme.colors.text }]}>
            {user?.username || 'Adventurer'}
          </Text>
        </View>
        <TouchableOpacity
          style={[styles.profileButton, { backgroundColor: theme.colors.surface }]}
          onPress={() => navigation.navigate('Profile' as never)}
        >
          <Icon name="person" size={24} color={theme.colors.primary} />
        </TouchableOpacity>
      </View>

      {/* Quick Actions */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          Quick Actions
        </Text>
        <QuickActions />
      </View>

      {/* Active Characters */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            Your Characters
          </Text>
          {characters.length > 3 && (
            <TouchableOpacity onPress={navigateToAllCharacters}>
              <Text style={[styles.seeAllText, { color: theme.colors.primary }]}>
                See All
              </Text>
            </TouchableOpacity>
          )}
        </View>
        {characters.length > 0 ? (
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {characters.map((character) => (
              <View key={character.id} style={styles.characterCard}>
                <CharacterCard
                  character={character}
                  onPress={() => handleCharacterPress(character.id)}
                />
              </View>
            ))}
          </ScrollView>
        ) : (
          <View style={[styles.emptyState, { backgroundColor: theme.colors.surface }]}>
            <Icon name="people-outline" size={48} color={theme.colors.textSecondary} />
            <Text style={[styles.emptyStateText, { color: theme.colors.textSecondary }]}>
              No characters yet
            </Text>
            <TouchableOpacity
              style={[styles.createButton, { backgroundColor: theme.colors.primary }]}
              onPress={() => navigation.navigate('CharacterCreate' as never)}
            >
              <Text style={styles.createButtonText}>Create Character</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      {/* Active Campaigns */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            Active Campaigns
          </Text>
          {campaigns.length > 3 && (
            <TouchableOpacity onPress={navigateToAllCampaigns}>
              <Text style={[styles.seeAllText, { color: theme.colors.primary }]}>
                See All
              </Text>
            </TouchableOpacity>
          )}
        </View>
        {campaigns.length > 0 ? (
          campaigns.map((campaign) => (
            <View key={campaign.id} style={styles.campaignCard}>
              <CampaignCard
                campaign={campaign}
                onPress={() => handleCampaignPress(campaign.id)}
              />
            </View>
          ))
        ) : (
          <View style={[styles.emptyState, { backgroundColor: theme.colors.surface }]}>
            <Icon name="explore-outline" size={48} color={theme.colors.textSecondary} />
            <Text style={[styles.emptyStateText, { color: theme.colors.textSecondary }]}>
              No active campaigns
            </Text>
            <TouchableOpacity
              style={[styles.createButton, { backgroundColor: theme.colors.primary }]}
              onPress={() => navigation.navigate('CampaignBrowser' as never)}
            >
              <Text style={styles.createButtonText}>Browse Campaigns</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      {/* Recent Notifications */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            Recent Notifications
          </Text>
          {notifications.length > 0 && (
            <TouchableOpacity onPress={navigateToAllNotifications}>
              <Text style={[styles.seeAllText, { color: theme.colors.primary }]}>
                See All
              </Text>
            </TouchableOpacity>
          )}
        </View>
        {notifications.length > 0 ? (
          notifications.map((notification) => (
            <View key={notification.id} style={styles.notificationCard}>
              <NotificationCard
                notification={notification}
                onPress={() => handleNotificationPress(notification.id)}
              />
            </View>
          ))
        ) : (
          <View style={[styles.emptyState, { backgroundColor: theme.colors.surface }]}>
            <Icon name="notifications-none" size={48} color={theme.colors.textSecondary} />
            <Text style={[styles.emptyStateText, { color: theme.colors.textSecondary }]}>
              No new notifications
            </Text>
          </View>
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  welcomeText: {
    fontSize: 16,
  },
  usernameText: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  profileButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
  },
  seeAllText: {
    fontSize: 14,
    fontWeight: '500',
  },
  characterCard: {
    marginRight: 12,
  },
  campaignCard: {
    marginBottom: 12,
  },
  notificationCard: {
    marginBottom: 8,
  },
  emptyState: {
    padding: 32,
    borderRadius: 12,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 16,
    marginTop: 12,
    marginBottom: 20,
  },
  createButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  createButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
});

export default HomeScreen;