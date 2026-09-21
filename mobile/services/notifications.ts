import {
  Platform,
  PermissionsAndroid,
  Alert,
  DeviceEventEmitter,
  NativeEventEmitter,
  NativeModules,
} from 'react-native';
import PushNotification from 'react-native-push-notification';
import PushNotificationIOS from '@react-native-community/push-notification-ios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiService } from './api';
import { API_CONFIG, NotificationData } from '../constants/api';
import { store } from '../store';

interface NotificationConfig {
  channelId: string;
  channelName: string;
  importance: 'default' | 'high' | 'max';
  vibrate: boolean;
  sound: boolean;
  badge: boolean;
}

class NotificationService {
  private isInitialized: boolean = false;
  private pushToken: string | null = null;
  private notificationListeners: Map<string, any> = new Map();
  private eventEmitter: NativeEventEmitter;

  constructor() {
    // Create event emitter for custom notification events
    this.eventEmitter = new NativeEventEmitter(NativeModules.RNPushNotification || {});
  }

  // Initialize the notification service
  async initialize(): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    try {
      await this.requestPermissions();
      this.configureChannels();
      this.configureHandlers();
      await this.getPushToken();
      this.isInitialized = true;
      console.log('Notification service initialized successfully');
    } catch (error) {
      console.error('Failed to initialize notification service:', error);
    }
  }

  // Request notification permissions
  private async requestPermissions(): Promise<boolean> {
    if (Platform.OS === 'ios') {
      const result = await PushNotificationIOS.requestPermissions();
      return (
        result.alert ||
        result.badge ||
        result.sound
      );
    } else if (Platform.OS === 'android') {
      const granted = await PermissionsAndroid.request(
        PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS
      );
      return granted === PermissionsAndroid.RESULTS.GRANTED;
    }

    return false;
  }

  // Configure notification channels (Android)
  private configureChannels(): void {
    if (Platform.OS !== 'android') {
      return;
    }

    const channels: NotificationConfig[] = [
      {
        channelId: 'default',
        channelName: 'Default Notifications',
        importance: 'default',
        vibrate: true,
        sound: true,
        badge: true,
      },
      {
        channelId: 'game_events',
        channelName: 'Game Events',
        importance: 'high',
        vibrate: true,
        sound: true,
        badge: true,
      },
      {
        channelId: 'social_updates',
        channelName: 'Social Updates',
        importance: 'default',
        vibrate: true,
        sound: false,
        badge: true,
      },
      {
        channelId: 'system_messages',
        channelName: 'System Messages',
        importance: 'high',
        vibrate: true,
        sound: true,
        badge: true,
      },
      {
        channelId: 'chat_messages',
        channelName: 'Chat Messages',
        importance: 'default',
        vibrate: true,
        sound: false,
        badge: true,
      },
    ];

    channels.forEach(channel => {
      PushNotification.createChannel(
        {
          channelId: channel.channelId,
          channelName: channel.channelName,
          importance: channel.importance,
          vibrate: channel.vibrate,
          sound: channel.sound,
          playSound: channel.sound,
          enableVibrate: channel.vibrate,
        },
        (created) => {
          console.log(`Channel ${channel.channelId} created:`, created);
        }
      );
    });
  }

  // Configure notification handlers
  private configureHandlers(): void {
    PushNotification.configure({
      // Called when a notification is received
      onNotification: (notification) => {
        this.handleNotification(notification);
      },

      // Called when token is generated (iOS)
      onRegister: (token) => {
        this.handleTokenRefresh(token.token);
      },

      // Permissions
      permissions: {
        alert: true,
        badge: true,
        sound: true,
      },

      // Pop initial notification
      popInitialNotification: true,

      // Request permissions
      requestPermissions: Platform.OS === 'ios',
    });
  }

  // Handle incoming notifications
  private handleNotification(notification: any): void {
    console.log('Notification received:', notification);

    const { foreground, userInteraction, data, message, userInfo } = notification;

    if (foreground && !userInteraction) {
      // App is in foreground and notification was received
      this.emitEvent('notificationReceived', {
        id: notification.id,
        title: notification.title || message,
        body: notification.message || notification.body,
        data: data || userInfo,
      });

      // Show in-app notification or update UI
      this.showInAppNotification(notification);
    } else if (userInteraction) {
      // User tapped on notification
      this.handleNotificationPress(notification);
    }

    // Update badge count
    if (Platform.OS === 'ios' && notification.badge) {
      PushNotificationIOS.setApplicationIconBadgeNumber(notification.badge);
    }
  }

  // Handle notification press
  private handleNotificationPress(notification: any): void {
    const { data, userInfo } = notification;
    const notificationData = data || userInfo;

    this.emitEvent('notificationPressed', {
      id: notification.id,
      data: notificationData,
    });

    // Navigate based on notification type
    this.handleNotificationNavigation(notificationData);
  }

  // Handle navigation based on notification type
  private handleNotificationNavigation(data: any): void {
    if (!data) return;

    const { type, sessionId, characterId, userId, channelId } = data;

    // Dispatch navigation action to store
    switch (type) {
      case 'game_invite':
        store.dispatch({
          type: 'navigation/navigate',
          payload: {
            screen: 'SessionDetail',
            params: { sessionId },
          },
        });
        break;

      case 'character_update':
        store.dispatch({
          type: 'navigation/navigate',
          payload: {
            screen: 'CharacterDetail',
            params: { characterId },
          },
        });
        break;

      case 'friend_request':
        store.dispatch({
          type: 'navigation/navigate',
          payload: {
            screen: 'Friends',
          },
        });
        break;

      case 'chat_message':
        store.dispatch({
          type: 'navigation/navigate',
          payload: {
            screen: 'Chat',
            params: { channelId },
          },
        });
        break;

      case 'achievement':
        store.dispatch({
          type: 'navigation/navigate',
          payload: {
            screen: 'Profile',
            params: { userId },
          },
        });
        break;

      default:
        // Navigate to dashboard
        store.dispatch({
          type: 'navigation/navigate',
          payload: {
            screen: 'Dashboard',
          },
        });
        break;
    }
  }

  // Show in-app notification
  private showInAppNotification(notification: any): void {
    // This would integrate with your in-app notification system
    // For now, we'll emit an event that components can listen to
    this.emitEvent('inAppNotification', {
      id: notification.id,
      title: notification.title,
      body: notification.message || notification.body,
      data: notification.data || notification.userInfo,
    });
  }

  // Handle token refresh
  private async handleTokenRefresh(token: string): Promise<void> {
    try {
      this.pushToken = token;
      await AsyncStorage.setItem(API_CONFIG.STORAGE_KEYS.PUSH_TOKEN, token);

      // Register token with server
      await this.registerTokenWithServer(token);
      console.log('Push token registered:', token);
    } catch (error) {
      console.error('Failed to register push token:', error);
    }
  }

  // Get push token
  private async getPushToken(): Promise<void> {
    try {
      // Check if we already have a token
      const storedToken = await AsyncStorage.getItem(API_CONFIG.STORAGE_KEYS.PUSH_TOKEN);
      if (storedToken) {
        this.pushToken = storedToken;
        return;
      }

      // Request new token (this will trigger onRegister callback)
      if (Platform.OS === 'ios') {
        PushNotificationIOS.requestPermissions();
      }
    } catch (error) {
      console.error('Failed to get push token:', error);
    }
  }

  // Register token with server
  private async registerTokenWithServer(token: string): Promise<void> {
    try {
      const response = await apiService.post('/notifications/register', {
        token,
        platform: Platform.OS,
        appVersion: await this.getAppVersion(),
        deviceId: await this.getDeviceId(),
      });

      if (!response.success) {
        console.error('Failed to register token with server:', response.error);
      }
    } catch (error) {
      console.error('Failed to register token with server:', error);
    }
  }

  // Send local notification
  async sendLocalNotification(options: {
    id?: string;
    title: string;
    message: string;
    data?: any;
    channelId?: string;
    sound?: string;
    vibrate?: boolean;
    priority?: 'default' | 'high' | 'max';
    actions?: any[];
  }): Promise<void> {
    const {
      id = Date.now().toString(),
      title,
      message,
      data,
      channelId = 'default',
      sound,
      vibrate = true,
      priority = 'default',
      actions,
    } = options;

    PushNotification.localNotification({
      id,
      title,
      message,
      data,
      channelId,
      soundName: sound || 'default',
      playSound: !!sound,
      vibrate,
      priority,
      actions,
      userInfo: data,
    });
  }

  // Schedule notification
  async scheduleNotification(options: {
    id?: string;
    title: string;
    message: string;
    date: Date;
    data?: any;
    channelId?: string;
    repeatType?: 'minute' | 'hour' | 'day' | 'week' | 'month';
    allowWhileIdle?: boolean;
  }): Promise<void> {
    const {
      id = Date.now().toString(),
      title,
      message,
      date,
      data,
      channelId = 'default',
      repeatType,
      allowWhileIdle = false,
    } = options;

    PushNotification.localNotificationSchedule({
      id,
      title,
      message,
      date,
      data,
      channelId,
      repeatType,
      allowWhileIdle,
      userInfo: data,
    });
  }

  // Cancel notification
  cancelNotification(id: string): void {
    PushNotification.cancelLocalNotifications({ id });
  }

  // Cancel all notifications
  cancelAllNotifications(): void {
    PushNotification.cancelAllLocalNotifications();
  }

  // Get scheduled notifications
  async getScheduledNotifications(): Promise<any[]> {
    return new Promise((resolve) => {
      PushNotification.getScheduledLocalNotifications((notifications) => {
        resolve(notifications);
      });
    });
  }

  // Set badge count (iOS)
  setBadgeCount(count: number): void {
    if (Platform.OS === 'ios') {
      PushNotificationIOS.setApplicationIconBadgeNumber(count);
    }
  }

  // Clear badge count (iOS)
  clearBadgeCount(): void {
    if (Platform.OS === 'ios') {
      PushNotificationIOS.setApplicationIconBadgeNumber(0);
    }
  }

  // Get notification permissions status
  async getPermissionStatus(): Promise<boolean> {
    if (Platform.OS === 'ios') {
      const result = await PushNotificationIOS.checkPermissions();
      return result.alert || result.badge || result.sound;
    } else if (Platform.OS === 'android') {
      const granted = await PermissionsAndroid.check(
        PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS
      );
      return granted;
    }

    return false;
  }

  // Event emitters for component integration
  addEventListener(event: string, listener: any): void {
    this.notificationListeners.set(event, this.eventEmitter.addListener(event, listener));
  }

  removeEventListener(event: string): void {
    const listener = this.notificationListeners.get(event);
    if (listener) {
      listener.remove();
      this.notificationListeners.delete(event);
    }
  }

  private emitEvent(event: string, data: any): void {
    DeviceEventEmitter.emit(event, data);
  }

  // Utility methods
  private async getAppVersion(): Promise<string> {
    try {
      const version = await AsyncStorage.getItem(API_CONFIG.STORAGE_KEYS.APP_VERSION);
      return version || '1.0.0';
    } catch (error) {
      return '1.0.0';
    }
  }

  private async getDeviceId(): Promise<string> {
    try {
      const deviceId = await AsyncStorage.getItem(API_CONFIG.STORAGE_KEYS.DEVICE_ID);
      if (deviceId) return deviceId;

      const newDeviceId = `device_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      await AsyncStorage.setItem(API_CONFIG.STORAGE_KEYS.DEVICE_ID, newDeviceId);
      return newDeviceId;
    } catch (error) {
      return 'unknown-device';
    }
  }

  // Push notification types for different game events
  async notifyGameInvite(sessionId: string, sessionName: string, inviterName: string): Promise<void> {
    await this.sendLocalNotification({
      title: 'Game Invitation',
      message: `${inviterName} invited you to join "${sessionName}"`,
      data: {
        type: 'game_invite',
        sessionId,
        sessionName,
        inviterName,
      },
      channelId: 'game_events',
      priority: 'high',
    });
  }

  async notifyFriendRequest(fromUser: string): Promise<void> {
    await this.sendLocalNotification({
      title: 'Friend Request',
      message: `${fromUser} sent you a friend request`,
      data: {
        type: 'friend_request',
        fromUser,
      },
      channelId: 'social_updates',
    });
  }

  async notifyAchievementUnlocked(achievementName: string, description: string): Promise<void> {
    await this.sendLocalNotification({
      title: 'Achievement Unlocked!',
      message: `${achievementName}: ${description}`,
      data: {
        type: 'achievement',
        achievementName,
        description,
      },
      channelId: 'game_events',
      priority: 'high',
    });
  }

  async notifyChatMessage(channelName: string, senderName: string, message: string): Promise<void> {
    await this.sendLocalNotification({
      title: channelName,
      message: `${senderName}: ${message}`,
      data: {
        type: 'chat_message',
        channelName,
        senderName,
        message,
      },
      channelId: 'chat_messages',
      vibrate: false,
    });
  }

  async notifySessionUpdate(sessionName: string, update: string): Promise<void> {
    await this.sendLocalNotification({
      title: 'Session Update',
      message: `${sessionName}: ${update}`,
      data: {
        type: 'session_update',
        sessionName,
        update,
      },
      channelId: 'game_events',
    });
  }

  // Cleanup
  cleanup(): void {
    // Remove all event listeners
    this.notificationListeners.forEach((listener) => {
      listener.remove();
    });
    this.notificationListeners.clear();

    // Cancel all scheduled notifications
    this.cancelAllNotifications();

    this.isInitialized = false;
  }
}

// Create singleton instance
export const notificationService = new NotificationService();
export default notificationService;