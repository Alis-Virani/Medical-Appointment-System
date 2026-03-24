/**
 * Medical Appointment Mobile App - Main Entry Point
 * React Native app with WebSocket, Firebase, and offline-first support
 */

import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import AsyncStorage from '@react-native-async-storage/async-storage';
import messaging from '@react-native-firebase/messaging';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import MaterialIcons from 'react-native-vector-icons/MaterialIcons';

// Screens
import SplashScreen from './screens/SplashScreen';
import LoginScreen from './screens/LoginScreen';
import RegisterScreen from './screens/RegisterScreen';

import HomeScreen from './screens/HomeScreen';
import AppointmentListScreen from './screens/AppointmentListScreen';
import BookAppointmentScreen from './screens/BookAppointmentScreen';
import AppointmentDetailScreen from './screens/AppointmentDetailScreen';
import ChatScreen from './screens/ChatScreen';
import ProfileScreen from './screens/ProfileScreen';
import SettingsScreen from './screens/SettingsScreen';
import DoctorScheduleScreen from './screens/DoctorScheduleScreen';
import NotificationsScreen from './screens/NotificationsScreen';

// Store & Services
import { useAuthStore } from './stores/authStore';
import { useRealtimeStore } from './stores/realtimeStore';
import { initializeRealtimeClient } from './services/realtimeClient';
import { initializePushNotifications } from './services/pushNotifications';
import { initializeOfflineSync } from './services/offlineSync';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

/**
 * Auth Stack - Login/Register screens
 */
function AuthStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        animationEnabled: true,
      }}
    >
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen 
        name="Register" 
        component={RegisterScreen}
        options={{ cardStyle: { backgroundColor: '#fff' } }}
      />
    </Stack.Navigator>
  );
}

/**
 * Doctor Stack - Doctor-specific screens
 */
function DoctorStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: true,
        headerBackTitle: 'Back',
      }}
    >
      <Stack.Screen 
        name="DoctorHome" 
        component={HomeScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen 
        name="DoctorSchedule" 
        component={DoctorScheduleScreen}
        options={{ title: 'My Schedule' }}
      />
      <Stack.Screen 
        name="AppointmentDetail" 
        component={AppointmentDetailScreen}
        options={{ title: 'Appointment' }}
      />
      <Stack.Screen 
        name="Chat" 
        component={ChatScreen}
        options={({ route }) => ({
          title: route.params?.patientName || 'Chat',
        })}
      />
    </Stack.Navigator>
  );
}

/**
 * Patient Stack - Patient-specific screens
 */
function PatientStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: true,
        headerBackTitle: 'Back',
      }}
    >
      <Stack.Screen 
        name="PatientHome" 
        component={HomeScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen 
        name="MyAppointments" 
        component={AppointmentListScreen}
        options={{ title: 'My Appointments' }}
      />
      <Stack.Screen 
        name="BookAppointment" 
        component={BookAppointmentScreen}
        options={{ title: 'Book Appointment' }}
      />
      <Stack.Screen 
        name="AppointmentDetail" 
        component={AppointmentDetailScreen}
        options={{ title: 'Appointment' }}
      />
      <Stack.Screen 
        name="Chat" 
        component={ChatScreen}
        options={({ route }) => ({
          title: route.params?.doctorName || 'Chat',
        })}
      />
    </Stack.Navigator>
  );
}

/**
 * Main App Tabs - Tab navigation once authenticated
 */
function AppTabs() {
  const userType = useAuthStore(state => state.userType);

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarIcon: ({ focused, color, size }) => {
          let iconName = 'home';

          if (route.name === 'Home') iconName = 'home';
          else if (route.name === 'Appointments') iconName = 'calendar-today';
          else if (route.name === 'Chat') iconName = 'message';
          else if (route.name === 'Notifications') iconName = 'notifications';
          else if (route.name === 'Profile') iconName = 'person';

          return (
            <MaterialIcons 
              name={iconName} 
              size={size} 
              color={focused ? '#2196F3' : color}
            />
          );
        },
        tabBarActiveTintColor: '#2196F3',
        tabBarInactiveTintColor: '#999',
        tabBarStyle: { paddingBottom: 5, height: 60 },
      })}
    >
      <Tab.Screen 
        name="Home" 
        component={userType === 'doctor' ? DoctorStack : PatientStack}
        options={{ title: 'Home' }}
      />
      <Tab.Screen 
        name="Appointments" 
        component={AppointmentListScreen}
        options={{ title: 'Appointments' }}
      />
      <Tab.Screen 
        name="Chat" 
        component={ChatScreen}
        options={{ title: 'Messages' }}
      />
      <Tab.Screen 
        name="Notifications" 
        component={NotificationsScreen}
        options={{ 
          title: 'Notifications',
          listeners: ({ navigation }) => ({
            tabPress: e => {
              // Mark notifications as read when tapped
            },
          }),
        }}
      />
      <Tab.Screen 
        name="Profile" 
        component={ProfileScreen}
        options={{ title: 'Profile' }}
      />
    </Tab.Navigator>
  );
}

/**
 * Main App Component
 */
export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [userToken, setUserToken] = useState(null);
  
  const authStore = useAuthStore();
  const realtimeStore = useRealtimeStore();

  // Check if user is already logged in
  useEffect(() => {
    const bootstrapAsync = async () => {
      try {
        // Restore token/session
        const token = await AsyncStorage.getItem('authToken');
        const user = await AsyncStorage.getItem('user');
        
        if (token && user) {
          setUserToken(token);
          const userData = JSON.parse(user);
          authStore.setUser(userData);
          authStore.setToken(token);

          // Initialize real-time services
          await initializeRealtimeClient(userData.id, userData.type);
          await initializePushNotifications();
          await initializeOfflineSync();
        }
      } catch (e) {
        console.error('Failed to restore token:', e);
      } finally {
        setIsLoading(false);
      }
    };

    bootstrapAsync();
  }, []);

  // Set up Firebase push notifications
  useEffect(() => {
    const setupMessaging = async () => {
      try {
        // Request notification permission
        await messaging().requestPermission();
        
        // Get FCM token
        const token = await messaging().getToken();
        console.log('FCM Token:', token);
        
        // Handle foreground messages
        const unsubscribe = messaging().onMessage(async (remoteMessage) => {
          console.log('Foreground message:', remoteMessage);
          realtimeStore.addNotification({
            id: remoteMessage.messageId,
            title: remoteMessage.notification?.title,
            body: remoteMessage.notification?.body,
            data: remoteMessage.data,
            timestamp: new Date(),
            read: false,
          });
        });
        
        // Handle notification taps
        messaging().onNotificationOpenedApp((remoteMessage) => {
          console.log('Notification opened app:', remoteMessage);
          // Navigate to appropriate screen based on data
        });

        return unsubscribe;
      } catch (error) {
        console.error('Messaging setup error:', error);
      }
    };

    setupMessaging();
  }, []);

  // Show splash screen while loading
  if (isLoading) {
    return <SplashScreen />;
  }

  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          {userToken == null ? (
            <Stack.Group
              screenOptions={{
                animationEnabled: true,
                cardStyle: { backgroundColor: 'white' },
              }}
            >
              <Stack.Screen 
                name="Auth" 
                component={AuthStack}
                options={{
                  animationEnabled: false,
                  cardStyle: { backgroundColor: 'white' },
                }}
              />
            </Stack.Group>
          ) : (
            <Stack.Group screenOptions={{ animationEnabled: true }}>
              <Stack.Screen 
                name="MainApp" 
                component={AppTabs}
                options={{
                  animationEnabled: false,
                }}
              />
              <Stack.Screen 
                name="Settings" 
                component={SettingsScreen}
                options={{
                  cardStyle: { backgroundColor: 'white' },
                  animationEnabled: true,
                }}
              />
            </Stack.Group>
          )}
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
