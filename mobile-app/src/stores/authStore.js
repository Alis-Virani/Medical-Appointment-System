/**
 * Zustand Store for Authentication
 * Manages user authentication state
 */

import create from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const API_URL = 'http://your-server.com:8000';

export const useAuthStore = create((set, get) => ({
  // State
  user: null,
  token: null,
  isLoading: false,
  error: null,
  isAuthenticated: false,

  // Actions
  setUser: (user) => set({ user }),
  setToken: (token) => set({ token }),
  setIsLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),

  /**
   * Login
   */
  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.post(`${API_URL}/api/login`, {
        email,
        password,
      });

      const { token, user } = response.data;

      // Save to local storage
      await AsyncStorage.setItem('authToken', token);
      await AsyncStorage.setItem('user', JSON.stringify(user));

      set({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
      });

      return { success: true, user };
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Login failed';
      set({
        error: errorMessage,
        isLoading: false,
      });
      return { success: false, error: errorMessage };
    }
  },

  /**
   * Register
   */
  register: async (userData) => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.post(`${API_URL}/api/register`, userData);

      const { token, user } = response.data;

      // Save to local storage
      await AsyncStorage.setItem('authToken', token);
      await AsyncStorage.setItem('user', JSON.stringify(user));

      set({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
      });

      return { success: true, user };
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Registration failed';
      set({
        error: errorMessage,
        isLoading: false,
      });
      return { success: false, error: errorMessage };
    }
  },

  /**
   * Logout
   */
  logout: async () => {
    try {
      const token = get().token;
      
      // Notify backend
      if (token) {
        await axios.post(
          `${API_URL}/api/logout`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
      }

      // Clear local storage
      await AsyncStorage.removeItem('authToken');
      await AsyncStorage.removeItem('user');

      set({
        user: null,
        token: null,
        isAuthenticated: false,
      });

      return { success: true };
    } catch (error) {
      console.error('Logout error:', error);
      return { success: false };
    }
  },

  /**
   * Update user profile
   */
  updateProfile: async (updates) => {
    set({ isLoading: true, error: null });
    try {
      const token = get().token;
      const user = get().user;

      const response = await axios.put(
        `${API_URL}/api/users/${user.id}`,
        updates,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const updatedUser = { ...user, ...response.data };

      // Save to local storage
      await AsyncStorage.setItem('user', JSON.stringify(updatedUser));

      set({
        user: updatedUser,
        isLoading: false,
      });

      return { success: true, user: updatedUser };
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Profile update failed';
      set({
        error: errorMessage,
        isLoading: false,
      });
      return { success: false, error: errorMessage };
    }
  },

  /**
   * Refresh token
   */
  refreshToken: async () => {
    try {
      const token = get().token;

      const response = await axios.post(
        `${API_URL}/api/refresh-token`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const { token: newToken } = response.data;

      await AsyncStorage.setItem('authToken', newToken);
      set({ token: newToken });

      return { success: true };
    } catch (error) {
      console.error('Token refresh error:', error);
      return { success: false };
    }
  },

  /**
   * Get user type
   */
  userType: () => get().user?.type || 'patient',

  /**
   * Get user ID
   */
  userId: () => get().user?.id,
}));
