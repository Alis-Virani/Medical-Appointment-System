/**
 * Firebase Push Notifications Service
 * Handles FCM push notifications for iOS and Android
 */

import messaging from '@react-native-firebase/messaging';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { useRealtimeStore } from '../stores/realtimeStore';
import { Platform } from 'react-native';

const API_URL = 'http://your-server.com:8000';

class PushNotificationsService {
  constructor() {
    this.fcmToken = null;
    this.isInitialized = false;
  }

  /**
   * Initialize push notifications
   */
  async initialize() {
    if (this.isInitialized) return;

    try {
      // Request user permission
      const authStatus = await messaging().requestPermission();
      const enabled =
        authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
        authStatus === messaging.AuthorizationStatus.PROVISIONAL;

      if (!enabled) {
        console.warn('Notification permissions denied');
        return;
      }

      // Get FCM token
      await this.getFCMToken();

      // Handle foreground notifications
      this.handleForegroundMessages();

      // Handle notification when app is in background/terminated
      this.handleBackgroundMessages();

      // Handle notification tap
      this.handleNotificationTap();

      this.isInitialized = true;
      console.log('Push notifications initialized');
    } catch (error) {
      console.error('Push notifications initialization error:', error);
    }
  }

  /**
   * Get FCM token
   */
  async getFCMToken() {
    try {
      const token = await messaging().getToken();
      console.log('FCM Token:', token);

      this.fcmToken = token;

      // Save token locally
      await AsyncStorage.setItem('fcmToken', token);

      // Send token to backend
      await this.sendTokenToBackend(token);

      return token;
    } catch (error) {
      console.error('Error getting FCM token:', error);
    }
  }

  /**
   * Send FCM token to backend
   */
  async sendTokenToBackend(token) {
    try {
      const userId = await AsyncStorage.getItem('userId');
      
      if (userId) {
        await axios.post(`${API_URL}/api/user/${userId}/fcm-token`, {
          token,
          platform: Platform.OS,
          device_name: `${Platform.OS}_device`,
        });
      }
    } catch (error) {
      console.error('Error sending token to backend:', error);
    }
  }

  /**
   * Handle foreground notifications
   */
  handleForegroundMessages() {
    const unsubscribe = messaging().onMessage(async (remoteMessage) => {
      console.log('Foreground notification:', remoteMessage);

      const notification = {
        id: remoteMessage.messageId,
        title: remoteMessage.notification?.title || 'Notification',
        body: remoteMessage.notification?.body || '',
        data: remoteMessage.data || {},
        timestamp: new Date(),
        read: false,
        source: 'push',
      };

      // Add to notification store
      useRealtimeStore.getState().addNotification(notification);

      // Show local notification (using react-native-toast or custom alert)
      this.showLocalNotification(notification);
    });

    return unsubscribe;
  }

  /**
   * Handle background notifications
   */
  handleBackgroundMessages() {
    // Set up notification handler for when app is in background
    messaging().onBackgroundMessage(async (remoteMessage) => {
      console.log('Background notification:', remoteMessage);

      const notification = {
        id: remoteMessage.messageId,
        title: remoteMessage.notification?.title || 'Notification',
        body: remoteMessage.notification?.body || '',
        data: remoteMessage.data || {},
        timestamp: new Date(),
        read: false,
        source: 'push',
      };

      // Save to local storage for retrieval when app opens
      await this.saveNotificationLocally(notification);
    });
  }

  /**
   * Handle notification tap
   */
  handleNotificationTap() {
    // When app is terminated and user taps notification
    messaging().getInitialNotification().then((remoteMessage) => {
      if (remoteMessage) {
        console.log('App opened from notification:', remoteMessage);
        this.handleNotificationPress(remoteMessage.data);
      }
    });

    // When app is in background and user taps notification
    const unsubscribe = messaging().onNotificationOpenedApp((remoteMessage) => {
      console.log('Notification tapped:', remoteMessage);
      this.handleNotificationPress(remoteMessage.data);
    });

    return unsubscribe;
  }

  /**
   * Handle notification press
   */
  handleNotificationPress(data) {
    const { type, appointment_id, chat_id, user_id, doctor_id, patient_id } = data;

    // Navigate based on notification type
    useRealtimeStore.getState().setNotificationAction({
      type,
      appointment_id,
      chat_id,
      user_id,
      doctor_id,
      patient_id,
    });
  }

  /**
   * Show local notification
   */
  showLocalNotification(notification) {
    // This can be used to show local notifications even when push service isn't available
    console.log('Would show local notification:', notification);
  }

  /**
   * Save notification locally for retrieval when app opens
   */
  async saveNotificationLocally(notification) {
    try {
      const notificationsKey = 'savedNotifications';
      const existing = await AsyncStorage.getItem(notificationsKey);
      const notifications = existing ? JSON.parse(existing) : [];
      
      notifications.push(notification);
      
      // Keep only last 50 notifications
      if (notifications.length > 50) {
        notifications.shift();
      }

      await AsyncStorage.setItem(notificationsKey, JSON.stringify(notifications));
    } catch (error) {
      console.error('Error saving notification locally:', error);
    }
  }

  /**
   * Send notification to user via backend API
   */
  async sendNotificationToUser(userId, title, body, data = {}) {
    try {
      await axios.post(`${API_URL}/api/notify/${userId}`, {
        title,
        body,
        data,
      });
    } catch (error) {
      console.error('Error sending notification:', error);
    }
  }

  /**
   * Subscribe to topic
   */
  async subscribeToTopic(topic) {
    try {
      await messaging().subscribeToTopic(topic);
      console.log(`Subscribed to topic: ${topic}`);
    } catch (error) {
      console.error(`Error subscribing to topic ${topic}:`, error);
    }
  }

  /**
   * Unsubscribe from topic
   */
  async unsubscribeFromTopic(topic) {
    try {
      await messaging().unsubscribeFromTopic(topic);
      console.log(`Unsubscribed from topic: ${topic}`);
    } catch (error) {
      console.error(`Error unsubscribing from topic ${topic}:`, error);
    }
  }
}

// Singleton instance
let pushNotificationsInstance = null;

export function getPushNotificationsService() {
  if (!pushNotificationsInstance) {
    pushNotificationsInstance = new PushNotificationsService();
  }
  return pushNotificationsInstance;
}

export async function initializePushNotifications() {
  const service = getPushNotificationsService();
  await service.initialize();
  return service;
}

export default PushNotificationsService;
