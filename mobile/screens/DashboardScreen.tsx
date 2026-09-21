import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Alert,
  Dimensions,
} from 'react-native';
import {
  Text,
  Card,
  Button,
  Avatar,
  Badge,
  Icon,
  ListItem,
  Chip,
} from 'react-native-elements';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useTheme } from '@react-navigation/native';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store';
import {
  fetchUserData,
  fetchUserCharacters,
  fetchActiveSessions,
  fetchNotifications,
} from '../store/slices/userSlice';
import { GameSession, Character, Notification } from '../types';
import { formatDistanceToNow } from 'date-fns';
import Animated, {
  FadeIn,
  SlideInRight,
  SlideInLeft,
} from 'react-native-reanimated';

type DashboardScreenNavigationProp = NativeStackNavigationProp<any>;

const { width: screenWidth } = Dimensions.get('window');

const DashboardScreen: React.FC = () => {
  const navigation = useNavigation<DashboardScreenNavigationProp>();
  const theme = useTheme();
  const dispatch = useDispatch();

  const {
    user,
    characters,
    activeSessions,
    notifications,
    isLoading,
    error,
  } = useSelector((state: RootState) => state.user);

  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = useCallback(async () => {
    try {
      await Promise.all([
        dispatch(fetchUserData()),
        dispatch(fetchUserCharacters()),
        dispatch(fetchActiveSessions()),
        dispatch(fetchNotifications()),
      ]);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      Alert.alert('Error', 'Failed to load dashboard data');
    }
  }, [dispatch]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await loadDashboardData();
    } finally {
      setRefreshing(false);
    }
  }, [loadDashboardData]);

  const handleCharacterPress = (character: Character) => {
    navigation.navigate('CharacterDetail', { characterId: character.id });
  };

  const handleSessionPress = (session: GameSession) => {
    if (session.status === 'active') {
      navigation.navigate('Game', { sessionId: session.id });
    } else {
      navigation.navigate('SessionDetail', { sessionId: session.id });
    }
  };

  const handleNotificationPress = (notification: Notification) => {
    // Handle notification navigation based on type
    switch (notification.type) {
      case 'game_invite':
        navigation.navigate('SessionDetail', {
          sessionId: notification.data?.sessionId
        });
        break;
      case 'friend_request':
        navigation.navigate('Friends');
        break;
      case 'achievement':
        navigation.navigate('Profile');
        break;
      default:
        break;
    }
  };

  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case 'common': return theme.colors.common;
      case 'uncommon': return theme.colors.uncommon;
      case 'rare': return theme.colors.rare;
      case 'epic': return theme.colors.epic;
      case 'legendary': return theme.colors.legendary;
      default: return theme.colors.common;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return theme.colors.success;
      case 'away': return theme.colors.warning;
      case 'busy': return theme.colors.error;
      default: return theme.colors.textSecondary;
    }
  };

  if (error) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={styles.errorContainer}>
          <Icon
            name="alert-circle-outline"
            type="ionicon"
            size={64}
            color={theme.colors.error}
          />
          <Text style={[styles.errorText, { color: theme.colors.error }]}>
            {error}
          </Text>
          <Button
            title="Retry"
            onPress={loadDashboardData}
            buttonStyle={{
              backgroundColor: theme.colors.primary,
              borderRadius: 8,
              paddingHorizontal: 24,
            }}
          />
        </View>
      </View>
    );
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={handleRefresh}
          colors={[theme.colors.primary]}
          tintColor={theme.colors.primary}
        />
      }
      showsVerticalScrollIndicator={false}
    >
      {/* User Header */}
      <Animated.View
        entering={FadeIn.duration(500)}
        style={styles.headerSection}
      >
        <Card containerStyle={styles.headerCard}>
          <View style={styles.userHeader}>
            <Avatar
              size="large"
              rounded
              source={
                user?.avatar
                  ? { uri: user.avatar }
                  : require('../assets/images/default-avatar.png')
              }
              title={user?.displayName?.charAt(0) || 'U'}
              containerStyle={styles.avatarContainer}
            />
            <View style={styles.userInfo}>
              <Text h4 style={[styles.userName, { color: theme.colors.text }]}>
                {user?.displayName || 'Adventurer'}
              </Text>
              <Text style={[styles.userLevel, { color: theme.colors.textSecondary }]}>
                Level {user?.level || 1} • {user?.class || 'Hero'}
              </Text>
              <View style={styles.userStats}>
                <View style={styles.statItem}>
                  <Icon
                    name="star-outline"
                    type="ionicon"
                    size={16}
                    color={theme.colors.experience}
                  />
                  <Text style={[styles.statText, { color: theme.colors.experience }]}>
                    {user?.experience || 0} XP
                  </Text>
                </View>
                <View style={styles.statItem}>
                  <Icon
                    name="trophy-outline"
                    type="ionicon"
                    size={16}
                    color={theme.colors.warning}
                  />
                  <Text style={[styles.statText, { color: theme.colors.warning }]}>
                    {user?.achievements?.length || 0}
                  </Text>
                </View>
              </View>
            </View>
            <View style={styles.statusIndicator}>
              <Badge
                status="success"
                value=""
                containerStyle={styles.statusBadge}
              />
              <Text style={[styles.statusText, { color: theme.colors.success }]}>
                Online
              </Text>
            </View>
          </View>
        </Card>
      </Animated.View>

      {/* Quick Actions */}
      <Animated.View
        entering={SlideInRight.duration(500).delay(200)}
        style={styles.section}
      >
        <Text h5 style={[styles.sectionTitle, { color: theme.colors.text }]}>
          Quick Actions
        </Text>
        <View style={styles.quickActions}>
          <Button
            title="Create Character"
            type="outline"
            onPress={() => navigation.navigate('CreateCharacter')}
            buttonStyle={[
              styles.quickActionButton,
              { borderColor: theme.colors.primary },
            ]}
            titleStyle={{ color: theme.colors.primary }}
            icon={
              <Icon
                name="person-add-outline"
                type="ionicon"
                color={theme.colors.primary}
                size={20}
              />
            }
          />
          <Button
            title="Join Game"
            type="outline"
            onPress={() => navigation.navigate('Sessions')}
            buttonStyle={[
              styles.quickActionButton,
              { borderColor: theme.colors.secondary },
            ]}
            titleStyle={{ color: theme.colors.secondary }}
            icon={
              <Icon
                name="game-controller-outline"
                type="ionicon"
                color={theme.colors.secondary}
                size={20}
              />
            }
          />
        </View>
      </Animated.View>

      {/* Active Characters */}
      <Animated.View
        entering={SlideInLeft.duration(500).delay(300)}
        style={styles.section}
      >
        <View style={styles.sectionHeader}>
          <Text h5 style={[styles.sectionTitle, { color: theme.colors.text }]}>
            Your Characters
          </Text>
          <Button
            type="clear"
            title="View All"
            onPress={() => navigation.navigate('Characters')}
            titleStyle={{ color: theme.colors.primary }}
          />
        </View>

        {characters && characters.length > 0 ? (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.characterScroll}
          >
            {characters.slice(0, 5).map((character) => (
              <Card
                key={character.id}
                containerStyle={[
                  styles.characterCard,
                  { backgroundColor: theme.colors.surface },
                ]}
                onPress={() => handleCharacterPress(character)}
              >
                <Avatar
                  size="medium"
                  rounded
                  source={
                    character.appearance?.avatar
                      ? { uri: character.appearance.avatar }
                      : undefined
                  }
                  title={character.name.charAt(0)}
                  containerStyle={styles.characterAvatar}
                />
                <Text
                  style={[
                    styles.characterName,
                    { color: theme.colors.text },
                  ]}
                  numberOfLines={1}
                >
                  {character.name}
                </Text>
                <Text
                  style={[
                    styles.characterClass,
                    { color: theme.colors.textSecondary },
                  ]}
                  numberOfLines={1}
                >
                  {character.class.name} • Level {character.level}
                </Text>
                <View style={styles.characterStats}>
                  <View style={styles.healthBar}>
                    <View
                      style={[
                        styles.healthFill,
                        {
                          width: `${(character.health / character.maxHealth) * 100}%`,
                          backgroundColor: theme.colors.health,
                        },
                      ]}
                    />
                  </View>
                  <Text style={[styles.healthText, { color: theme.colors.textSecondary }]}>
                    {character.health}/{character.maxHealth}
                  </Text>
                </View>
              </Card>
            ))}
          </ScrollView>
        ) : (
          <Card containerStyle={styles.emptyCard}>
            <View style={styles.emptyContent}>
              <Icon
                name="people-outline"
                type="ionicon"
                size={48}
                color={theme.colors.textSecondary}
              />
              <Text style={[styles.emptyText, { color: theme.colors.textSecondary }]}>
                No characters yet
              </Text>
              <Button
                title="Create Your First Character"
                onPress={() => navigation.navigate('CreateCharacter')}
                buttonStyle={{
                  backgroundColor: theme.colors.primary,
                  borderRadius: 8,
                  marginTop: 16,
                }}
              />
            </View>
          </Card>
        )}
      </Animated.View>

      {/* Active Sessions */}
      <Animated.View
        entering={SlideInRight.duration(500).delay(400)}
        style={styles.section}
      >
        <View style={styles.sectionHeader}>
          <Text h5 style={[styles.sectionTitle, { color: theme.colors.text }]}>
            Active Games
          </Text>
          <Button
            type="clear"
            title="Browse"
            onPress={() => navigation.navigate('Sessions')}
            titleStyle={{ color: theme.colors.primary }}
          />
        </View>

        {activeSessions && activeSessions.length > 0 ? (
          activeSessions.slice(0, 3).map((session) => (
            <Card
              key={session.id}
              containerStyle={[
                styles.sessionCard,
                { backgroundColor: theme.colors.surface },
              ]}
              onPress={() => handleSessionPress(session)}
            >
              <ListItem containerStyle={styles.sessionItem}>
                <Avatar
                  size="medium"
                  rounded
                  title={session.name.charAt(0)}
                  containerStyle={styles.sessionAvatar}
                />
                <ListItem.Content>
                  <ListItem.Title style={[styles.sessionName, { color: theme.colors.text }]}>
                    {session.name}
                  </ListItem.Title>
                  <ListItem.Subtitle style={[styles.sessionDescription, { color: theme.colors.textSecondary }]}>
                    {session.description}
                  </ListItem.Subtitle>
                  <View style={styles.sessionMeta}>
                    <Chip
                      title={session.status}
                      type="outline"
                      size="sm"
                      buttonStyle={{
                        borderColor: getStatusColor(session.status),
                        backgroundColor: 'transparent',
                      }}
                      titleStyle={{ color: getStatusColor(session.status) }}
                    />
                    <Text style={[styles.sessionTime, { color: theme.colors.textSecondary }]}>
                      {formatDistanceToNow(new Date(session.updatedAt), { addSuffix: true })}
                    </Text>
                  </View>
                </ListItem.Content>
                {session.status === 'active' && (
                  <Badge
                    status="success"
                    value="LIVE"
                    containerStyle={styles.liveBadge}
                  />
                )}
              </ListItem>
            </Card>
          ))
        ) : (
          <Card containerStyle={styles.emptyCard}>
            <View style={styles.emptyContent}>
              <Icon
                name="game-controller-outline"
                type="ionicon"
                size={48}
                color={theme.colors.textSecondary}
              />
              <Text style={[styles.emptyText, { color: theme.colors.textSecondary }]}>
                No active games
              </Text>
              <Button
                title="Join a Game"
                onPress={() => navigation.navigate('Sessions')}
                buttonStyle={{
                  backgroundColor: theme.colors.primary,
                  borderRadius: 8,
                  marginTop: 16,
                }}
              />
            </View>
          </Card>
        )}
      </Animated.View>

      {/* Recent Notifications */}
      <Animated.View
        entering={SlideInLeft.duration(500).delay(500)}
        style={styles.section}
      >
        <View style={styles.sectionHeader}>
          <Text h5 style={[styles.sectionTitle, { color: theme.colors.text }]}>
            Recent Activity
          </Text>
          <Button
            type="clear"
            title="See All"
            onPress={() => navigation.navigate('Notifications')}
            titleStyle={{ color: theme.colors.primary }}
          />
        </View>

        {notifications && notifications.length > 0 ? (
          notifications.slice(0, 5).map((notification) => (
            <Card
              key={notification.id}
              containerStyle={[
                styles.notificationCard,
                { backgroundColor: theme.colors.surface },
              ]}
              onPress={() => handleNotificationPress(notification)}
            >
              <View style={styles.notificationItem}>
                <Icon
                  name={getNotificationIcon(notification.type)}
                  type="ionicon"
                  size={24}
                  color={getNotificationColor(notification.type)}
                />
                <View style={styles.notificationContent}>
                  <Text style={[styles.notificationTitle, { color: theme.colors.text }]}>
                    {notification.title}
                  </Text>
                  <Text
                    style={[
                      styles.notificationMessage,
                      { color: theme.colors.textSecondary },
                    ]}
                    numberOfLines={2}
                  >
                    {notification.body}
                  </Text>
                  <Text style={[styles.notificationTime, { color: theme.colors.textSecondary }]}>
                    {formatDistanceToNow(new Date(notification.timestamp), { addSuffix: true })}
                  </Text>
                </View>
                {!notification.read && (
                  <View style={[styles.unreadDot, { backgroundColor: theme.colors.primary }]} />
                )}
              </View>
            </Card>
          ))
        ) : (
          <Card containerStyle={styles.emptyCard}>
            <View style={styles.emptyContent}>
              <Icon
                name="notifications-outline"
                type="ionicon"
                size={48}
                color={theme.colors.textSecondary}
              />
              <Text style={[styles.emptyText, { color: theme.colors.textSecondary }]}>
                No recent activity
              </Text>
            </View>
          </Card>
        )}
      </Animated.View>

      <View style={styles.bottomSpacer} />
    </ScrollView>
  );
};

const getNotificationIcon = (type: string) => {
  switch (type) {
    case 'game_invite': return 'game-controller-outline';
    case 'friend_request': return 'person-add-outline';
    case 'achievement': return 'trophy-outline';
    case 'system': return 'information-circle-outline';
    default: return 'notifications-outline';
  }
};

const getNotificationColor = (type: string) => {
  switch (type) {
    case 'game_invite': return '#2196F3';
    case 'friend_request': return '#4CAF50';
    case 'achievement': return '#FFC107';
    case 'system': return '#9C27B0';
    default: return '#757575';
  }
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  headerSection: {
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  headerCard: {
    borderRadius: 16,
    padding: 20,
    backgroundColor: '#1E1E1E',
    borderWidth: 0,
  },
  userHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarContainer: {
    marginRight: 16,
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  userLevel: {
    fontSize: 16,
    marginBottom: 8,
  },
  userStats: {
    flexDirection: 'row',
    gap: 16,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statText: {
    fontSize: 14,
    fontWeight: '500',
  },
  statusIndicator: {
    alignItems: 'center',
  },
  statusBadge: {
    marginBottom: 4,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '500',
  },
  section: {
    paddingHorizontal: 16,
    marginTop: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
  },
  quickActions: {
    flexDirection: 'row',
    gap: 12,
  },
  quickActionButton: {
    flex: 1,
    borderRadius: 12,
    paddingVertical: 12,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  characterScroll: {
    paddingRight: 16,
  },
  characterCard: {
    width: screenWidth * 0.4,
    marginRight: 12,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 0,
  },
  characterAvatar: {
    marginBottom: 8,
  },
  characterName: {
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 4,
  },
  characterClass: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 8,
  },
  characterStats: {
    width: '100%',
    alignItems: 'center',
  },
  healthBar: {
    width: '100%',
    height: 4,
    backgroundColor: '#333',
    borderRadius: 2,
    marginBottom: 4,
  },
  healthFill: {
    height: '100%',
    borderRadius: 2,
  },
  healthText: {
    fontSize: 12,
  },
  sessionCard: {
    borderRadius: 12,
    padding: 0,
    marginBottom: 12,
    borderWidth: 0,
  },
  sessionItem: {
    padding: 16,
  },
  sessionAvatar: {
    marginRight: 12,
  },
  sessionName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  sessionDescription: {
    fontSize: 14,
    marginBottom: 8,
  },
  sessionMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sessionTime: {
    fontSize: 12,
  },
  liveBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
  },
  notificationCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    borderWidth: 0,
  },
  notificationItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  notificationContent: {
    flex: 1,
    marginLeft: 12,
  },
  notificationTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  notificationMessage: {
    fontSize: 14,
    marginBottom: 8,
  },
  notificationTime: {
    fontSize: 12,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginLeft: 8,
    marginTop: 6,
  },
  emptyCard: {
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
    borderWidth: 0,
  },
  emptyContent: {
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    marginTop: 12,
    marginBottom: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  errorText: {
    fontSize: 16,
    marginVertical: 16,
    textAlign: 'center',
  },
  bottomSpacer: {
    height: 32,
  },
});

export default DashboardScreen;