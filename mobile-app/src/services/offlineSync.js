/**
 * Offline-First Data Synchronization Service
 * Handles offline data storage and sync when connection is restored
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import axios from 'axios';
import dayjs from 'dayjs';
import { useOfflineStore } from '../stores/offlineStore';
import { useRealtimeStore } from '../stores/realtimeStore';

const API_URL = 'http://your-server.com:8000';

class OfflineSyncService {
  constructor() {
    this.isOnline = false;
    this.syncInProgress = false;
    this.unsubscribeNetInfo = null;
  }

  /**
   * Initialize offline sync service
   */
  async initialize() {
    try {
      // Check initial connectivity
      const state = await NetInfo.fetch();
      this.isOnline = state.isConnected;

      // Listen for connectivity changes
      this.unsubscribeNetInfo = NetInfo.addEventListener((state) => {
        this.isOnline = state.isConnected;
        
        if (state.isConnected) {
          console.log('Connection restored, syncing...');
          this.syncAllData();
        } else {
          console.log('Connection lost, working offline');
        }
      });

      console.log('Offline sync initialized');
    } catch (error) {
      console.error('Offline sync initialization error:', error);
    }
  }

  /**
   * Sync all offline data
   */
  async syncAllData() {
    if (this.syncInProgress) return;

    this.syncInProgress = true;
    useRealtimeStore.setState({ syncInProgress: true });

    try {
      await Promise.all([
        this.syncMessages(),
        this.syncAppointments(),
        this.syncProfileUpdates(),
        this.syncScheduleUpdates(),
      ]);

      console.log('All data synced successfully');
      useRealtimeStore.setState({ lastSync: new Date() });
    } catch (error) {
      console.error('Sync error:', error);
    } finally {
      this.syncInProgress = false;
      useRealtimeStore.setState({ syncInProgress: false });
    }
  }

  /**
   * Sync messages
   */
  async syncMessages() {
    try {
      const offlineStore = useOfflineStore.getState();
      const pendingMessages = offlineStore.messages || [];

      if (pendingMessages.length === 0) return;

      console.log(`Syncing ${pendingMessages.length} messages...`);

      const userId = useRealtimeStore.getState().user?.id;
      const authToken = await AsyncStorage.getItem('authToken');

      for (const message of pendingMessages) {
        try {
          await axios.post(
            `${API_URL}/api/messages`,
            {
              sender_id: message.sender_id,
              recipient_id: message.recipient_id,
              text: message.text,
              timestamp: message.timestamp,
            },
            {
              headers: { Authorization: `Bearer ${authToken}` },
            }
          );

          offlineStore.removeMessage(message.id);
        } catch (error) {
          console.error('Error syncing message:', error);
        }
      }
    } catch (error) {
      console.error('Message sync error:', error);
    }
  }

  /**
   * Sync appointments
   */
  async syncAppointments() {
    try {
      const offlineStore = useOfflineStore.getState();
      const pendingAppointments = offlineStore.appointments || [];

      if (pendingAppointments.length === 0) return;

      console.log(`Syncing ${pendingAppointments.length} appointments...`);

      const authToken = await AsyncStorage.getItem('authToken');

      for (const appointment of pendingAppointments) {
        try {
          const { id, ...data } = appointment;

          if (appointment.action === 'create') {
            await axios.post(
              `${API_URL}/api/appointments`,
              data,
              {
                headers: { Authorization: `Bearer ${authToken}` },
              }
            );
          } else if (appointment.action === 'update') {
            await axios.put(
              `${API_URL}/api/appointments/${id}`,
              data,
              {
                headers: { Authorization: `Bearer ${authToken}` },
              }
            );
          } else if (appointment.action === 'cancel') {
            await axios.delete(
              `${API_URL}/api/appointments/${id}`,
              {
                headers: { Authorization: `Bearer ${authToken}` },
              }
            );
          }

          offlineStore.removeAppointment(id);
        } catch (error) {
          console.error('Error syncing appointment:', error);
        }
      }
    } catch (error) {
      console.error('Appointment sync error:', error);
    }
  }

  /**
   * Sync profile updates
   */
  async syncProfileUpdates() {
    try {
      const offlineStore = useOfflineStore.getState();
      const pendingProfiles = offlineStore.profileUpdates || [];

      if (pendingProfiles.length === 0) return;

      console.log(`Syncing ${pendingProfiles.length} profile updates...`);

      const userId = useRealtimeStore.getState().user?.id;
      const authToken = await AsyncStorage.getItem('authToken');

      for (const profile of pendingProfiles) {
        try {
          await axios.put(
            `${API_URL}/api/users/${userId}`,
            profile,
            {
              headers: { Authorization: `Bearer ${authToken}` },
            }
          );

          offlineStore.removeProfileUpdate(profile.id);
        } catch (error) {
          console.error('Error syncing profile:', error);
        }
      }
    } catch (error) {
      console.error('Profile sync error:', error);
    }
  }

  /**
   * Sync schedule updates (for doctors)
   */
  async syncScheduleUpdates() {
    try {
      const offlineStore = useOfflineStore.getState();
      const pendingSchedules = offlineStore.scheduleUpdates || [];

      if (pendingSchedules.length === 0) return;

      console.log(`Syncing ${pendingSchedules.length} schedule updates...`);

      const userId = useRealtimeStore.getState().user?.id;
      const authToken = await AsyncStorage.getItem('authToken');

      for (const schedule of pendingSchedules) {
        try {
          await axios.put(
            `${API_URL}/api/doctors/${userId}/schedule`,
            schedule,
            {
              headers: { Authorization: `Bearer ${authToken}` },
            }
          );

          offlineStore.removeScheduleUpdate(schedule.id);
        } catch (error) {
          console.error('Error syncing schedule:', error);
        }
      }
    } catch (error) {
      console.error('Schedule sync error:', error);
    }
  }

  /**
   * Save message for offline
   */
  async saveMessageOffline(message) {
    try {
      useOfflineStore.getState().addMessage(message);
      console.log('Message saved for offline sync');
    } catch (error) {
      console.error('Error saving message offline:', error);
    }
  }

  /**
   * Save appointment for offline
   */
  async saveAppointmentOffline(appointment, action = 'create') {
    try {
      useOfflineStore.getState().addAppointment({
        ...appointment,
        action,
      });
      console.log('Appointment saved for offline sync');
    } catch (error) {
      console.error('Error saving appointment offline:', error);
    }
  }

  /**
   * Get offline status
   */
  getOfflineStatus() {
    return {
      isOnline: this.isOnline,
      syncInProgress: this.syncInProgress,
      lastSync: useRealtimeStore.getState().lastSync,
    };
  }

  /**
   * Cache data from API
   */
  async cacheData(key, data, ttl = 3600000) {
    try {
      const cacheData = {
        data,
        timestamp: Date.now(),
        ttl,
      };
      await AsyncStorage.setItem(`cache_${key}`, JSON.stringify(cacheData));
    } catch (error) {
      console.error('Error caching data:', error);
    }
  }

  /**
   * Retrieve cached data
   */
  async getCachedData(key) {
    try {
      const cached = await AsyncStorage.getItem(`cache_${key}`);
      if (!cached) return null;

      const { data, timestamp, ttl } = JSON.parse(cached);

      // Check if cache is expired
      if (Date.now() - timestamp > ttl) {
        await AsyncStorage.removeItem(`cache_${key}`);
        return null;
      }

      return data;
    } catch (error) {
      console.error('Error retrieving cached data:', error);
      return null;
    }
  }

  /**
   * Cleanup old cached data
   */
  async cleanupCache() {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter(key => key.startsWith('cache_'));

      for (const key of cacheKeys) {
        const cached = await AsyncStorage.getItem(key);
        if (!cached) continue;

        const { timestamp, ttl } = JSON.parse(cached);

        if (Date.now() - timestamp > ttl) {
          await AsyncStorage.removeItem(key);
        }
      }

      console.log('Cache cleanup completed');
    } catch (error) {
      console.error('Error cleaning up cache:', error);
    }
  }

  /**
   * Clear all offline data
   */
  async clearAllOfflineData() {
    try {
      const offlineStore = useOfflineStore.getState();
      offlineStore.clearAll();
      console.log('All offline data cleared');
    } catch (error) {
      console.error('Error clearing offline data:', error);
    }
  }

  /**
   * Cleanup
   */
  cleanup() {
    if (this.unsubscribeNetInfo) {
      this.unsubscribeNetInfo();
    }
  }
}

// Singleton instance
let offlineSyncInstance = null;

export function getOfflineSyncService() {
  if (!offlineSyncInstance) {
    offlineSyncInstance = new OfflineSyncService();
  }
  return offlineSyncInstance;
}

export async function initializeOfflineSync() {
  const service = getOfflineSyncService();
  await service.initialize();
  return service;
}

export default OfflineSyncService;
