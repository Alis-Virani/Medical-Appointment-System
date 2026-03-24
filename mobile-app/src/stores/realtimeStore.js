/**
 * Zustand Store for Real-Time Data
 * Manages WebSocket messages, appointments, online status, etc.
 */

import create from 'zustand';
import dayjs from 'dayjs';

export const useRealtimeStore = create((set, get) => ({
  // Connection state
  connectionStatus: 'disconnected', // disconnected | connecting | connected | error | failed
  lastSync: null,
  syncInProgress: false,

  // Chat messages
  messages: {}, // Organized by user ID: { userId: [messages] }
  unreadCount: 0,

  // Appointments
  appointments: [],
  appointmentUpdates: {},

  // Notifications
  notifications: [],
  notificationAction: null,

  // Online status
  onlineUsers: new Set(),
  userTypingStatus: {}, // { userId: isTyping }

  // Doctor schedule
  doctorSchedules: {}, // { doctorId: { workingHours, blockedDates } }

  // Actions

  /**
   * Set connection status
   */
  setConnectionStatus: (status) => set({ connectionStatus: status }),

  /**
   * Add chat message
   */
  addChatMessage: (message) => {
    set((state) => {
      const otherUserId = message.sender_id === get().user?.id 
        ? message.recipient_id 
        : message.sender_id;

      const key = [message.sender_id, message.recipient_id].sort().join('_');

      return {
        messages: {
          ...state.messages,
          [key]: [...(state.messages[key] || []), message],
        },
        unreadCount:
          message.type === 'received' && message.sender_id !== get().user?.id
            ? state.unreadCount + 1
            : state.unreadCount,
      };
    });
  },

  /**
   * Get messages with user
   */
  getMessagesWithUser: (userId) => {
    const key = [userId, get().user?.id].sort().join('_');
    return get().messages[key] || [];
  },

  /**
   * Mark messages as read
   */
  markMessagesAsRead: (userId) => {
    set((state) => {
      const key = [userId, get().user?.id].sort().join('_');
      const messages = state.messages[key] || [];
      
      const updated = messages.map((msg) => ({
        ...msg,
        read: true,
      }));

      return {
        messages: {
          ...state.messages,
          [key]: updated,
        },
        unreadCount: Math.max(0, state.unreadCount - messages.filter(m => !m.read).length),
      };
    });
  },

  /**
   * Clear all messages with user
   */
  clearMessagesWithUser: (userId) => {
    set((state) => {
      const key = [userId, get().user?.id].sort().join('_');
      const newMessages = { ...state.messages };
      delete newMessages[key];
      return { messages: newMessages };
    });
  },

  /**
   * Add appointment
   */
  addAppointment: (appointment) => {
    set((state) => ({
      appointments: [...state.appointments, appointment],
    }));
  },

  /**
   * Update appointment
   */
  updateAppointment: (appointmentId, updates) => {
    set((state) => ({
      appointments: state.appointments.map((apt) =>
        apt.id === appointmentId ? { ...apt, ...updates } : apt
      ),
    }));
  },

  /**
   * Remove appointment
   */
  removeAppointment: (appointmentId) => {
    set((state) => ({
      appointments: state.appointments.filter((apt) => apt.id !== appointmentId),
    }));
  },

  /**
   * Get appointments for date range
   */
  getAppointmentsForDateRange: (startDate, endDate) => {
    return get().appointments.filter((apt) => {
      const aptDate = dayjs(apt.date);
      return aptDate.isBetween(startDate, endDate, null, '[]');
    });
  },

  /**
   * Add notification
   */
  addNotification: (notification) => {
    set((state) => ({
      notifications: [notification, ...state.notifications].slice(0, 100),
    }));
  },

  /**
   * Mark notification as read
   */
  markNotificationAsRead: (notificationId) => {
    set((state) => ({
      notifications: state.notifications.map((notif) =>
        notif.id === notificationId ? { ...notif, read: true } : notif
      ),
    }));
  },

  /**
   * Remove notification
   */
  removeNotification: (notificationId) => {
    set((state) => ({
      notifications: state.notifications.filter((notif) => notif.id !== notificationId),
    }));
  },

  /**
   * Clear all notifications
   */
  clearAllNotifications: () => set({ notifications: [] }),

  /**
   * Get unread notifications
   */
  getUnreadNotifications: () => {
    return get().notifications.filter((notif) => !notif.read);
  },

  /**
   * Set notification action (navigation trigger)
   */
  setNotificationAction: (action) => set({ notificationAction: action }),

  /**
   * Set user online status
   */
  setUserOnline: (userId, isOnline) => {
    set((state) => {
      const onlineUsers = new Set(state.onlineUsers);
      if (isOnline) {
        onlineUsers.add(userId);
      } else {
        onlineUsers.delete(userId);
      }
      return { onlineUsers };
    });
  },

  /**
   * Check if user is online
   */
  isUserOnline: (userId) => {
    return get().onlineUsers.has(userId);
  },

  /**
   * Set user typing status
   */
  setUserTyping: (userId, isTyping) => {
    set((state) => ({
      userTypingStatus: {
        ...state.userTypingStatus,
        [userId]: isTyping,
      },
    }));
  },

  /**
   * Check if user is typing
   */
  isUserTyping: (userId) => {
    return get().userTypingStatus[userId] || false;
  },

  /**
   * Update doctor schedule
   */
  updateDoctorSchedule: (doctorId, scheduleData) => {
    set((state) => ({
      doctorSchedules: {
        ...state.doctorSchedules,
        [doctorId]: scheduleData,
      },
    }));
  },

  /**
   * Get doctor schedule
   */
  getDoctorSchedule: (doctorId) => {
    return get().doctorSchedules[doctorId];
  },

  /**
   * Get available slots for doctor
   */
  getAvailableSlots: (doctorId, date) => {
    const schedule = get().getDoctorSchedule(doctorId);
    if (!schedule) return [];

    const dayOfWeek = dayjs(date).format('dddd').toLowerCase();
    const workingHours = schedule.working_hours?.[dayOfWeek];

    if (!workingHours) return [];

    const appointments = get().appointments.filter(
      (apt) => apt.doctor_id === doctorId && dayjs(apt.date).isSame(date, 'day')
    );

    const slots = [];
    const startHour = parseInt(workingHours.start);
    const endHour = parseInt(workingHours.end);

    for (let hour = startHour; hour < endHour; hour++) {
      for (let minute of [0, 30]) {
        const slotTime = dayjs(date).hour(hour).minute(minute);
        const isBooked = appointments.some((apt) =>
          dayjs(apt.date).isSame(slotTime, 'minute')
        );

        if (!isBooked) {
          slots.push({
            time: slotTime.format('HH:mm'),
            datetime: slotTime.toISOString(),
          });
        }
      }
    }

    return slots;
  },

  /**
   * Clear all real-time data
   */
  clearAllData: () =>
    set({
      messages: {},
      appointments: [],
      notifications: [],
      onlineUsers: new Set(),
      userTypingStatus: {},
      doctorSchedules: {},
    }),
}));
