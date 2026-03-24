/**
 * Real-Time WebSocket Client for React Native
 * Connects to backend WebSocket server for live updates
 */

import WebSocket from 'ws';
import * as Crypto from 'expo-crypto';
import { useRealtimeStore } from '../stores/realtimeStore';
import { useOfflineStore } from '../stores/offlineStore';

class RealtimeClient {
  constructor() {
    this.ws = null;
    this.userId = null;
    this.userType = null;
    this.url = 'ws://your-server.com:8000/ws';
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
    this.messageQueue = [];
    this.handlers = {};
    this.isConnecting = false;
    this.pingInterval = null;
  }

  /**
   * Connect to WebSocket server
   */
  async connect(userId, userType, authToken) {
    if (this.isConnecting || this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.isConnecting = true;
    this.userId = userId;
    this.userType = userType;

    try {
      console.log('Connecting to WebSocket:', this.url);
      
      this.ws = new WebSocket(
        `${this.url}/${userId}/${userType}`,
        [],
        {
          headers: {
            Authorization: `Bearer ${authToken}`,
            'X-User-ID': userId,
            'X-User-Type': userType,
          },
        }
      );

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.isConnecting = false;
        useRealtimeStore.setState({ connectionStatus: 'connected' });
        
        // Send initial connection message
        this.send('ping', { timestamp: new Date() });
        
        // Start keep-alive ping
        this.startKeepAlive();
        
        // Send any queued messages
        this.flushMessageQueue();
        
        // Emit connected event
        this.emit('connected', { userId, userType });
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('Message received:', message.type);
          this.handleMessage(message);
        } catch (error) {
          console.error('Message parsing error:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        useRealtimeStore.setState({ connectionStatus: 'error' });
        this.emit('error', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.isConnecting = false;
        useRealtimeStore.setState({ connectionStatus: 'disconnected' });
        this.stopKeepAlive();
        
        // Attempt reconnection
        this.attemptReconnect();
        this.emit('disconnected', {});
      };

    } catch (error) {
      console.error('Connection error:', error);
      this.isConnecting = false;
      useRealtimeStore.setState({ connectionStatus: 'error' });
      this.attemptReconnect();
    }
  }

  /**
   * Handle incoming messages
   */
  handleMessage(message) {
    const { type, data, sender_id, recipient_id, timestamp } = message;

    switch (type) {
      case 'chat_message':
        this.handleChatMessage(message);
        break;
      case 'appointment_created':
        this.handleAppointmentCreated(message);
        break;
      case 'appointment_updated':
        this.handleAppointmentUpdated(message);
        break;
      case 'appointment_cancelled':
        this.handleAppointmentCancelled(message);
        break;
      case 'schedule_change':
        this.handleScheduleChange(message);
        break;
      case 'doctor_online':
      case 'patient_online':
        this.handleUserOnline(message);
        break;
      case 'doctor_offline':
      case 'patient_offline':
        this.handleUserOffline(message);
        break;
      case 'typing':
        this.handleTyping(message);
        break;
      case 'notification':
        this.handleNotification(message);
        break;
      case 'pong':
        console.log('Keep-alive pong received');
        break;
      default:
        console.warn('Unknown message type:', type);
    }

    // Emit generic event
    this.emit(type, message);
  }

  /**
   * Handle chat messages
   */
  handleChatMessage(message) {
    const store = useRealtimeStore.getState();
    const offlineStore = useOfflineStore.getState();

    const chatMessage = {
      id: message.message_id || Crypto.randomUUID(),
      sender_id: message.sender_id,
      recipient_id: message.recipient_id,
      text: message.data.text,
      timestamp: message.timestamp || new Date(),
      read: false,
      type: 'received',
    };

    store.addChatMessage(chatMessage);
    
    // Add to local storage when offline
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      offlineStore.addMessage(chatMessage);
    }
  }

  /**
   * Handle appointment creation
   */
  handleAppointmentCreated(message) {
    const { data } = message;
    useRealtimeStore.getState().addNotification({
      id: message.message_id,
      type: 'appointment_created',
      title: 'New Appointment',
      body: `Appointment with ${data.doctor_name || 'Dr. ' + data.doctor_id}`,
      data,
      timestamp: new Date(),
      read: false,
    });
  }

  /**
   * Handle appointment updates
   */
  handleAppointmentUpdated(message) {
    const { data } = message;
    useRealtimeStore.getState().addNotification({
      id: message.message_id,
      type: 'appointment_updated',
      title: 'Appointment Updated',
      body: 'Your appointment has been updated',
      data,
      timestamp: new Date(),
      read: false,
    });
  }

  /**
   * Handle appointment cancellations
   */
  handleAppointmentCancelled(message) {
    const { data } = message;
    useRealtimeStore.getState().addNotification({
      id: message.message_id,
      type: 'appointment_cancelled',
      title: 'Appointment Cancelled',
      body: 'Your appointment has been cancelled',
      data,
      timestamp: new Date(),
      read: false,
    });
  }

  /**
   * Handle schedule changes
   */
  handleScheduleChange(message) {
    const { data } = message;
    useRealtimeStore.getState().updateDoctorSchedule(data);
  }

  /**
   * Handle user coming online
   */
  handleUserOnline(message) {
    const { sender_id, type } = message;
    useRealtimeStore.getState().setUserOnline(sender_id, true);
  }

  /**
   * Handle user going offline
   */
  handleUserOffline(message) {
    const { sender_id, type } = message;
    useRealtimeStore.getState().setUserOnline(sender_id, false);
  }

  /**
   * Handle typing indicator
   */
  handleTyping(message) {
    const { sender_id, data } = message;
    if (data.is_typing) {
      useRealtimeStore.getState().setUserTyping(sender_id, true);
      // Auto clear after 3 seconds
      setTimeout(() => {
        useRealtimeStore.getState().setUserTyping(sender_id, false);
      }, 3000);
    }
  }

  /**
   * Handle notifications
   */
  handleNotification(message) {
    const { data } = message;
    useRealtimeStore.getState().addNotification({
      id: message.message_id,
      title: data.title,
      body: data.body,
      data,
      timestamp: new Date(),
      read: false,
    });
  }

  /**
   * Send message to server
   */
  send(type, data) {
    const message = {
      type,
      data,
      user_id: this.userId,
      user_type: this.userType,
      timestamp: new Date().toISOString(),
    };

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      // Queue message if disconnected
      this.messageQueue.push(message);
    }
  }

  /**
   * Send chat message
   */
  sendChatMessage(recipientId, text) {
    this.send('chat_message', {
      recipient_id: recipientId,
      text,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Send typing indicator
   */
  sendTypingIndicator(recipientId, isTyping = true) {
    this.send('typing', {
      recipient_id: recipientId,
      is_typing: isTyping,
    });
  }

  /**
   * Send appointment notification
   */
  sendAppointmentUpdate(appointmentData, type = 'appointment_created') {
    this.send(type, appointmentData);
  }

  /**
   * Update doctor schedule
   */
  updateSchedule(scheduleData) {
    this.send('schedule_change', scheduleData);
  }

  /**
   * Keep alive mechanism
   */
  startKeepAlive() {
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send('ping', { timestamp: new Date().toISOString() });
      }
    }, 30000); // Every 30 seconds
  }

  stopKeepAlive() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * Flush queued messages
   */
  flushMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(message));
      }
    }
  }

  /**
   * Attempt to reconnect
   */
  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Maximum reconnection attempts reached');
      useRealtimeStore.setState({ connectionStatus: 'failed' });
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect(this.userId, this.userType, '');
    }, delay);
  }

  /**
   * Register event handler
   */
  on(event, handler) {
    if (!this.handlers[event]) {
      this.handlers[event] = [];
    }
    this.handlers[event].push(handler);
  }

  /**
   * Unregister event handler
   */
  off(event, handler) {
    if (this.handlers[event]) {
      this.handlers[event] = this.handlers[event].filter(h => h !== handler);
    }
  }

  /**
   * Emit event
   */
  emit(event, data) {
    if (this.handlers[event]) {
      this.handlers[event].forEach(handler => handler(data));
    }
  }

  /**
   * Disconnect
   */
  disconnect() {
    this.stopKeepAlive();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Singleton instance
let realtimeClientInstance = null;

export function getRealtimeClient() {
  if (!realtimeClientInstance) {
    realtimeClientInstance = new RealtimeClient();
  }
  return realtimeClientInstance;
}

export async function initializeRealtimeClient(userId, userType, authToken = '') {
  const client = getRealtimeClient();
  await client.connect(userId, userType, authToken);
  return client;
}

export default RealtimeClient;
