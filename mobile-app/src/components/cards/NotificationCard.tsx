import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { Notification } from '../../types';
import { useTheme } from '../../hooks/useTheme';

interface NotificationCardProps {
  notification: Notification;
  onPress: () => void;
}

export const NotificationCard: React.FC<NotificationCardProps> = ({
  notification,
  onPress,
}) => {
  const theme = useTheme();

  const getNotificationIcon = () => {
    switch (notification.type) {
      case 'combat_turn':
        return 'sports-kabaddi';
      case 'dm_message':
        return 'chat';
      case 'party_invite':
        return 'group-add';
      case 'achievement':
        return 'emoji-events';
      case 'script_deploy':
        return 'code';
      default:
        return 'notifications';
    }
  };

  const getNotificationColor = () => {
    switch (notification.type) {
      case 'combat_turn':
        return theme.colors.warning;
      case 'dm_message':
        return theme.colors.info;
      case 'party_invite':
        return theme.colors.primary;
      case 'achievement':
        return theme.colors.success;
      case 'script_deploy':
        return theme.colors.secondary;
      default:
        return theme.colors.textSecondary;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInMins = Math.floor(diffInMs / 60000);
    const diffInHours = Math.floor(diffInMs / 3600000);
    const diffInDays = Math.floor(diffInMs / 86400000);

    if (diffInMins < 1) {
      return 'Just now';
    } else if (diffInMins < 60) {
      return `${diffInMins}m ago`;
    } else if (diffInHours < 24) {
      return `${diffInHours}h ago`;
    } else {
      return `${diffInDays}d ago`;
    }
  };

  return (
    <TouchableOpacity
      style={[
        styles.container,
        {
          backgroundColor: notification.isRead ? theme.colors.surface : theme.colors.background,
          borderColor: theme.colors.border,
          borderLeftColor: getNotificationColor(),
          borderLeftWidth: notification.isRead ? 1 : 4,
        },
      ]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      {/* Icon */}
      <View style={styles.iconSection}>
        <View
          style={[
            styles.iconContainer,
            { backgroundColor: getNotificationColor() + '20' },
          ]}
        >
          <Icon
            name={getNotificationIcon()}
            size={20}
            color={getNotificationColor()}
          />
        </View>
      </View>

      {/* Content */}
      <View style={styles.contentSection}>
        <View style={styles.headerRow}>
          <Text
            style={[
              styles.notificationTitle,
              {
                color: theme.colors.text,
                fontWeight: notification.isRead ? 'normal' : '600',
              },
            ]}
            numberOfLines={1}
          >
            {notification.title}
          </Text>
          <Text
            style={[styles.timestamp, { color: theme.colors.textSecondary }]}
          >
            {formatTimestamp(notification.createdAt)}
          </Text>
        </View>

        <Text
          style={[
            styles.notificationMessage,
            { color: theme.colors.textSecondary },
          ]}
          numberOfLines={2}
        >
          {notification.message}
        </Text>

        {!notification.isRead && (
          <View style={styles.unreadIndicator}>
            <View
              style={[
                styles.unreadDot,
                { backgroundColor: getNotificationColor() },
              ]}
            />
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    padding: 16,
    borderRadius: 8,
    borderWidth: 1,
    marginVertical: 2,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  iconSection: {
    marginRight: 12,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  contentSection: {
    flex: 1,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 4,
  },
  notificationTitle: {
    fontSize: 16,
    flex: 1,
    marginRight: 8,
  },
  timestamp: {
    fontSize: 12,
  },
  notificationMessage: {
    fontSize: 14,
    lineHeight: 20,
  },
  unreadIndicator: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 8,
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
});