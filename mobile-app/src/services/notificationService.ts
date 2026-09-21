import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Notification } from '../types';
import { HapticsService } from './hapticsService';

export class NotificationService {
  private static instance: NotificationService;
  private isInitialized: boolean = false;
  private pushToken: string | null = null;
  private notificationHandlers: Map<string, (notification: Notifications.Notification) => void> = new Map();

  private constructor() {}

  static getInstance(): NotificationService {
    if (!NotificationService.instance) {
      NotificationService.instance = new NotificationService();
    }
    return NotificationService.instance;
  }

  async initialize(): Promise<boolean> {
    try {
      // Configure notification handler
      Notifications.setNotificationHandler({
        handleNotification: async (notification) => {
          // Handle incoming notification
          await this.handleIncomingNotification(notification);

          return {
            shouldShowAlert: true,
            shouldPlaySound: true,
            shouldSetBadge: true,
          };
        },
        handleSuccess: (notificationId) => {
          console.log('Notification displayed successfully:', notificationId);
        },
        handleError: (error) => {
          console.error('Notification error:', error);
        },
      });

      // Request permissions
      const hasPermission = await this.requestPermissions();
      if (!hasPermission) {
        console.warn('Notification permissions not granted');
        return false;
      }

      // Get push token
      if (Device.isDevice) {
        const token = await this.getPushToken();
        if (token) {
          this.pushToken = token;
          await this.registerPushToken(token);
        }
      }

      this.isInitialized = true;
      console.log('Notification service initialized');
      return true;
    } catch (error) {
      console.error('Failed to initialize notification service:', error);
      return false;
    }
  }

  private async requestPermissions(): Promise<boolean> {
    try {
      if (Platform.OS === 'ios') {
        const { status } = await Notifications.requestPermissionsAsync();
        return status === 'granted';
      } else {
        const { status } = await Notifications.requestPermissionsAsync();
        return status === 'granted';
      }
    } catch (error) {
      console.error('Failed to request notification permissions:', error);
      return false;
    }
  }

  private async getPushToken(): Promise<string | null> {
    try {
      if (Platform.OS === 'android') {
        const { data } = await Notifications.getDevicePushTokenAsync();
        return data;
      } else {
        const { data } = await Notifications.getExpoPushTokenAsync();
        return data;
      }
    } catch (error) {
      console.error('Failed to get push token:', error);
      return null;
    }
  }

  private async registerPushToken(token: string): Promise<void> {
    try {
      const storedToken = await AsyncStorage.getItem('push_token');
      if (storedToken !== token) {
        // Register with backend
        const response = await fetch('https://api.dmlogn8n.com/v1/notifications/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${await AsyncStorage.getItem('auth_token')}`,
          },
          body: JSON.stringify({
            token,
            platform: Platform.OS,
            deviceId: await this.getDeviceId(),
          }),
        });

        if (response.ok) {
          await AsyncStorage.setItem('push_token', token);
          console.log('Push token registered successfully');
        } else {
          console.error('Failed to register push token:', response.status);
        }
      }
    } catch (error) {
      console.error('Failed to register push token:', error);
    }
  }

  private async getDeviceId(): Promise<string> {
    try {
      let deviceId = await AsyncStorage.getItem('device_id');
      if (!deviceId) {
        deviceId = `${Platform.OS}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        await AsyncStorage.setItem('device_id', deviceId);
      }
      return deviceId;
    } catch (error) {
      console.error('Failed to get device ID:', error);
      return 'unknown_device';
    }
  }

  async sendNotification(notification: Omit<Notification, 'id' | 'createdAt'>): Promise<void> {
    try {
      await Notifications.scheduleNotificationAsync({
        content: {
          title: notification.title,
          body: notification.body,
          data: notification.data,
          sound: 'default',
          badge: 1,
        },
        trigger: null, // Show immediately
      });
    } catch (error) {
      console.error('Failed to send notification:', error);
    }
  }

  async scheduleNotification(
    notification: Omit<Notification, 'id' | 'createdAt'>,
    trigger: Notifications.NotificationTriggerInput
  ): Promise<string> {
    try {
      const identifier = await Notifications.scheduleNotificationAsync({
        content: {
          title: notification.title,
          body: notification.body,
          data: notification.data,
          sound: 'default',
          badge: 1,
        },
        trigger,
      });

      return identifier;
    } catch (error) {
      console.error('Failed to schedule notification:', error);
      throw error;
    }
  }

  async scheduleSessionReminder(
    sessionId: string,
    sessionName: string,
    startTime: Date,
    leadTimeMinutes: number = 15
  ): Promise<string> {
    const triggerTime = new Date(startTime.getTime() - leadTimeMinutes * 60 * 1000);
    const now = new Date();

    if (triggerTime <= now) {
      // Session is starting soon or has already started
      await this.sendNotification({
        userId: 'current-user',
        type: 'session_reminder',
        title: 'Session Starting Soon',
        body: `Session "${sessionName}" starts in ${leadTimeMinutes} minutes!`,
        data: { sessionId, sessionName, startTime: startTime.toISOString() },
        isRead: false,
      });
      return 'immediate';
    }

    return await this.scheduleNotification(
      {
        userId: 'current-user',
        type: 'session_reminder',
        title: 'Session Starting Soon',
        body: `Session "${sessionName}" starts in ${leadTimeMinutes} minutes!`,
        data: { sessionId, sessionName, startTime: startTime.toISOString() },
        isRead: false,
      },
      {
        date: triggerTime,
      }
    );
  }

  async scheduleTurnAlert(
    sessionId: string,
    characterName: string,
    turnTime: Date
  ): Promise<string> {
    return await this.scheduleNotification(
      {
        userId: 'current-user',
        type: 'turn_alert',
        title: 'Your Turn!',
        body: `It's ${characterName}'s turn in the current session.`,
        data: { sessionId, characterName, turnTime: turnTime.toISOString() },
        isRead: false,
      },
      {
        date: turnTime,
      }
    );
  }

  async sendLevelUpNotification(characterName: string, newLevel: number): Promise<void> {
    await this.sendNotification({
      userId: 'current-user',
      type: 'level_up',
      title: 'Level Up!',
      body: `${characterName} has reached level ${newLevel}! 🎉`,
      data: { characterName, newLevel },
      isRead: false,
    });

    // Trigger haptic feedback
    await HapticsService.triggerLevelUp();
  }

  async sendPartyMessageNotification(
    message: string,
    senderName: string,
    campaignName: string
  ): Promise<void> {
    await this.sendNotification({
      userId: 'current-user',
      type: 'message',
      title: `${senderName} in ${campaignName}`,
      body: message,
      data: { senderName, campaignName, message },
      isRead: false,
    });

    // Trigger haptic feedback
    await HapticsService.notificationSuccess();
  }

  async sendDMNotification(title: string, body: string, campaignId: string): Promise<void> {
    await this.sendNotification({
      userId: 'current-user',
      type: 'dm_message',
      title: `DM Update - ${title}`,
      body,
      data: { campaignId },
      isRead: false,
    });

    // Trigger haptic feedback
    await HapticsService.notificationWarning();
  }

  async sendInviteNotification(campaignName: string, dmName: string): Promise<void> {
    await this.sendNotification({
      userId: 'current-user',
      type: 'invite',
      title: 'Campaign Invite',
      body: `${dmName} has invited you to join "${campaignName}"`,
      data: { campaignName, dmName },
      isRead: false,
    });
  }

  async cancelNotification(identifier: string): Promise<void> {
    try {
      await Notifications.cancelScheduledNotificationAsync(identifier);
    } catch (error) {
      console.error('Failed to cancel notification:', error);
    }
  }

  async dismissNotification(identifier: string): Promise<void> {
    try {
      await Notifications.dismissNotificationAsync(identifier);
    } catch (error) {
      console.error('Failed to dismiss notification:', error);
    }
  }

  async getBadgeCount(): Promise<number> {
    try {
      return await Notifications.getBadgeCountAsync();
    } catch (error) {
      console.error('Failed to get badge count:', error);
      return 0;
    }
  }

  async setBadgeCount(count: number): Promise<void> {
    try {
      await Notifications.setBadgeCountAsync(count);
    } catch (error) {
      console.error('Failed to set badge count:', error);
    }
  }

  async clearBadgeCount(): Promise<void> {
    try {
      await Notifications.setBadgeCountAsync(0);
    } catch (error) {
      console.error('Failed to clear badge count:', error);
    }
  }

  async getScheduledNotifications(): Promise<Notifications.NotificationRequest[]> {
    try {
      return await Notifications.getAllScheduledNotificationsAsync();
    } catch (error) {
      console.error('Failed to get scheduled notifications:', error);
      return [];
    }
  }

  async clearAllNotifications(): Promise<void> {
    try {
      await Notifications.dismissAllNotificationsAsync();
      await this.clearBadgeCount();
    } catch (error) {
      console.error('Failed to clear all notifications:', error);
    }
  }

  // Add notification handler for specific types
  addNotificationHandler(
    type: string,
    handler: (notification: Notifications.Notification) => void
  ): void {
    this.notificationHandlers.set(type, handler);
  }

  removeNotificationHandler(type: string): void {
    this.notificationHandlers.delete(type);
  }

  private async handleIncomingNotification(
    notification: Notifications.Notification
  ): Promise<void> {
    try {
      const notificationData = notification.request.content.data as any;
      const type = notificationData?.type;

      // Trigger haptic feedback based on notification type
      if (type === 'level_up') {
        await HapticsService.triggerLevelUp();
      } else if (type === 'turn_alert') {
        await HapticsService.triggerCombatTurn();
      } else if (type === 'session_reminder') {
        await HapticsService.notificationWarning();
      } else if (type === 'message') {
        await HapticsService.notificationSuccess();
      }

      // Call custom handler if registered
      if (type && this.notificationHandlers.has(type)) {
        const handler = this.notificationHandlers.get(type);
        if (handler) {
          handler(notification);
        }
      }

      console.log('Received notification:', type);
    } catch (error) {
      console.error('Failed to handle incoming notification:', error);
    }
  }

  // Setup notification response listener
  setupResponseListener(): void {
    Notifications.addNotificationResponseReceivedListener((response) => {
      const notification = response.notification;
      const action = response.actionIdentifier;
      const data = notification.request.content.data as any;

      console.log('Notification response received:', action, data);

      // Handle notification taps
      if (action === Notifications.DEFAULT_ACTION_IDENTIFIER) {
        this.handleNotificationTap(data);
      }
    });
  }

  private handleNotificationTap(data: any): void {
    // Navigate to appropriate screen based on notification type
    // This would typically dispatch navigation actions
    console.log('Notification tapped:', data);

    switch (data?.type) {
      case 'session_reminder':
      case 'turn_alert':
        // Navigate to session screen
        break;
      case 'message':
        // Navigate to chat screen
        break;
      case 'level_up':
        // Navigate to character screen
        break;
      case 'invite':
        // Navigate to invite screen
        break;
      default:
        // Navigate to dashboard
        break;
    }
  }

  getIsInitialized(): boolean {
    return this.isInitialized;
  }

  getPushToken(): string | null {
    return this.pushToken;
  }
}

// Export notification helper functions
export const createSessionReminder = async (
  sessionId: string,
  sessionName: string,
  startTime: Date
): Promise<string> => {
  const service = NotificationService.getInstance();
  return await service.scheduleSessionReminder(sessionId, sessionName, startTime);
};

export const createTurnAlert = async (
  sessionId: string,
  characterName: string,
  turnTime: Date
): Promise<string> => {
  const service = NotificationService.getInstance();
  return await service.scheduleTurnAlert(sessionId, characterName, turnTime);
};

export const sendLevelUpNotification = async (
  characterName: string,
  newLevel: number
): Promise<void> => {
  const service = NotificationService.getInstance();
  await service.sendLevelUpNotification(characterName, newLevel);
};

export const sendPartyMessageNotification = async (
  message: string,
  senderName: string,
  campaignName: string
): Promise<void> => {
  const service = NotificationService.getInstance();
  await service.sendPartyMessageNotification(message, senderName, campaignName);
};

export const sendDMNotification = async (
  title: string,
  body: string,
  campaignId: string
): Promise<void> => {
  const service = NotificationService.getInstance();
  await service.sendDMNotification(title, body, campaignId);
};

export const sendCampaignInvite = async (
  campaignName: string,
  dmName: string
): Promise<void> => {
  const service = NotificationService.getInstance();
  await service.sendInviteNotification(campaignName, dmName);
};