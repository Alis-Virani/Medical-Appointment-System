/**
 * Zustand Store for Offline Data
 * Manages pending data that needs to be synced when connection is restored
 */

import create from 'zustand';
import { v4 as uuidv4 } from 'uuid';

export const useOfflineStore = create((set, get) => ({
  // Pending data to sync
  messages: [],
  appointments: [],
  profileUpdates: [],
  scheduleUpdates: [],

  // Offline status
  isSyncing: false,
  lastSyncAttempt: null,
  syncErrors: [],

  // Actions

  /**
   * Add message to pending
   */
  addMessage: (message) => {
    set((state) => ({
      messages: [
        ...state.messages,
        {
          id: message.id || uuidv4(),
          ...message,
          addedOffline: true,
        },
      ],
    }));
  },

  /**
   * Remove message from pending
   */
  removeMessage: (messageId) => {
    set((state) => ({
      messages: state.messages.filter((msg) => msg.id !== messageId),
    }));
  },

  /**
   * Add appointment to pending
   */
  addAppointment: (appointment) => {
    set((state) => ({
      appointments: [
        ...state.appointments,
        {
          id: appointment.id || uuidv4(),
          ...appointment,
          addedOffline: true,
        },
      ],
    }));
  },

  /**
   * Remove appointment from pending
   */
  removeAppointment: (appointmentId) => {
    set((state) => ({
      appointments: state.appointments.filter((apt) => apt.id !== appointmentId),
    }));
  },

  /**
   * Add profile update to pending
   */
  addProfileUpdate: (update) => {
    set((state) => ({
      profileUpdates: [
        ...state.profileUpdates,
        {
          id: uuidv4(),
          ...update,
          addedOffline: true,
        },
      ],
    }));
  },

  /**
   * Remove profile update from pending
   */
  removeProfileUpdate: (updateId) => {
    set((state) => ({
      profileUpdates: state.profileUpdates.filter((update) => update.id !== updateId),
    }));
  },

  /**
   * Add schedule update to pending
   */
  addScheduleUpdate: (update) => {
    set((state) => ({
      scheduleUpdates: [
        ...state.scheduleUpdates,
        {
          id: uuidv4(),
          ...update,
          addedOffline: true,
        },
      ],
    }));
  },

  /**
   * Remove schedule update from pending
   */
  removeScheduleUpdate: (updateId) => {
    set((state) => ({
      scheduleUpdates: state.scheduleUpdates.filter((update) => update.id !== updateId),
    }));
  },

  /**
   * Set syncing status
   */
  setSyncing: (isSyncing) => set({ isSyncing }),

  /**
   * Record sync attempt
   */
  recordSyncAttempt: () => set({ lastSyncAttempt: new Date() }),

  /**
   * Add sync error
   */
  addSyncError: (error) => {
    set((state) => ({
      syncErrors: [
        ...state.syncErrors,
        {
          timestamp: new Date(),
          message: error.message || String(error),
        },
      ].slice(-50), // Keep last 50 errors
    }));
  },

  /**
   * Clear sync errors
   */
  clearSyncErrors: () => set({ syncErrors: [] }),

  /**
   * Get pending items count
   */
  getPendingItemsCount: () => {
    const state = get();
    return (
      state.messages.length +
      state.appointments.length +
      state.profileUpdates.length +
      state.scheduleUpdates.length
    );
  },

  /**
   * Get all pending data
   */
  getAllPendingData: () => ({
    messages: get().messages,
    appointments: get().appointments,
    profileUpdates: get().profileUpdates,
    scheduleUpdates: get().scheduleUpdates,
  }),

  /**
   * Clear all pending data (after successful sync)
   */
  clearAll: () =>
    set({
      messages: [],
      appointments: [],
      profileUpdates: [],
      scheduleUpdates: [],
      syncErrors: [],
      lastSyncAttempt: null,
    }),
}));
