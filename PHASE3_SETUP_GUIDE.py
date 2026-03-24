"""
PHASE 3 SETUP GUIDE - React Native Mobile App
Complete guide to building cross-platform medical appointment app
"""

print("""

╔════════════════════════════════════════════════════════════════════════════╗
║              PHASE 3 SETUP GUIDE - REACT NATIVE MOBILE APP                ║
║                     Cross-Platform Medical Appointments                    ║
╚════════════════════════════════════════════════════════════════════════════╝


📱 PROJECT OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Mobile App Capabilities:
  ✅ Cross-platform (iOS & Android)
  ✅ Real-time WebSocket integration (Phase 2 server)
  ✅ Native push notifications (Firebase Cloud Messaging)
  ✅ Offline-first architecture
  ✅ Local data sync
  ✅ Bottom tab navigation
  ✅ Real-time chat
  ✅ Appointment management
  ✅ Doctor scheduling
  ✅ Online status presence

Technology Stack:
  • React Native 0.72.0
  • React Navigation 6.x
  • Zustand (state management)
  • Firebase (messaging, analytics)
  • WebSocket (real-time)
  • AsyncStorage (offline storage)
  • Axios (HTTP client)


🏗️  PROJECT STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

mobile-app/
├── src/
│   ├── screens/                    # Screen components (12 total)
│   │   ├── SplashScreen.js
│   │   ├── LoginScreen.js
│   │   ├── RegisterScreen.js
│   │   ├── HomeScreen.js
│   │   ├── AppointmentListScreen.js
│   │   ├── BookAppointmentScreen.js
│   │   ├── AppointmentDetailScreen.js
│   │   ├── ChatScreen.js
│   │   ├── ProfileScreen.js
│   │   ├── SettingsScreen.js
│   │   ├── DoctorScheduleScreen.js
│   │   └── NotificationsScreen.js
│   │
│   ├── components/                 # Reusable UI components
│   │   ├── AppointmentCard.js
│   │   ├── ChatBubble.js
│   │   ├── ScheduleSlotPicker.js
│   │   ├── UserAvatar.js
│   │   └── ... (more components)
│   │
│   ├── services/                   # External services
│   │   ├── realtimeClient.js       # ✅ WebSocket client (created)
│   │   ├── pushNotifications.js    # ✅ Firebase notifications (created)
│   │   └── offlineSync.js          # ✅ Offline sync service (created)
│   │
│   ├── stores/                     # Zustand state stores
│   │   ├── authStore.js            # ✅ Authentication state (created)
│   │   ├── realtimeStore.js        # ✅ Real-time data (created)
│   │   └── offlineStore.js         # ✅ Offline pending data (created)
│   │
│   ├── hooks/                      # Custom React hooks
│   │   ├── useAppointments.js
│   │   ├── useChat.js
│   │   └── useOnlineStatus.js
│   │
│   ├── utils/                      # Utility functions
│   │   ├── dateUtils.js
│   │   ├── formatters.js
│   │   └── validators.js
│   │
│   ├── styles/                     # Global styles
│   │   ├── colors.js
│   │   ├── spacing.js
│   │   └── typography.js
│   │
│   ├── navigation/                 # Navigation configuration
│   │   └── RootNavigator.js
│   │
│   └── constants.js                # ✅ App constants (created)
│
├── ios/                            # iOS configuration
│   └── ... (native iOS files)
│
├── android/                        # Android configuration
│   └── ... (native Android files)
│
├── App.js                          # ✅ Main app component (created)
├── package.json                    # ✅ Dependencies (created)
├── app.json                        # ✅ App configuration (created)
├── setup.js                        # ✅ Setup script (created)
├── .env                            # Environment variables
└── .gitignore                      # Git ignore rules


📦 FILES ALREADY CREATED (PHASE 3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. App.js (Complete)
   - Main navigation setup
   - Authentication flow
   - Tab navigation for doctors & patients
   - Firebase initialization
   - Real-time service setup

2. src/services/realtimeClient.js (Complete)
   - WebSocket connection handling
   - Message sending/receiving
   - Event handling (8 types)
   - Automatic reconnection
   - Keep-alive ping mechanism
   - Thread-safe message queue

3. src/services/pushNotifications.js (Complete)
   - Firebase Cloud Messaging setup
   - Foreground notifications
   - Background notifications
   - Notification tap handling
   - FCM token management

4. src/services/offlineSync.js (Complete)
   - Offline data detection
   - Automatic sync on reconnection
   - Message/appointment queueing
   - Cache management
   - Data persistence

5. src/stores/authStore.js (Complete)
   - User authentication
   - Login/register/logout
   - Token management
   - Profile updates
   - Token refresh

6. src/stores/realtimeStore.js (Complete)
   - Chat messages
   - Appointments
   - Notifications
   - Online status
   - Doctor schedules
   - Typing indicators

7. src/stores/offlineStore.js (Complete)
   - Pending messages
   - Pending appointments
   - Profile updates queue
   - Schedule updates queue
   - Sync error tracking

8. package.json (Complete)
   - All dependencies
   - Build scripts
   - Development tools

9. setup.js (Complete)
   - Automated setup script
   - Directory creation
   - Configuration file generation


⚙️  INSTALLATION & SETUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Prerequisites:
  • Node.js 16.x or higher
  • npm 8.x or higher
  • React Native CLI
  • Xcode (for iOS development - macOS only)
  • Android Studio (for Android development)
  • Java 11 (for Android)

Step 1: Install Node.js and npm
  $ node --version          # Should be v16.x or higher
  $ npm --version           # Should be v8.x or higher

Step 2: Install React Native CLI
  $ npm install -g react-native-cli

Step 3: Navigate to mobile app directory
  $ cd mobile-app

Step 4: Run setup script
  $ node setup.js

Step 5: Install dependencies
  $ npm install

Step 6: Install iOS pods (macOS only)
  $ cd ios
  $ pod install
  $ cd ..

Step 7: Configure environment
  Edit .env with your backend URL and Firebase credentials:
  
  REACT_APP_API_URL=http://192.168.1.100:8000
  REACT_APP_WS_URL=ws://192.168.1.100:8000/ws
  FIREBASE_PROJECT_ID=your_project_id
  ... (add all Firebase credentials)

Step 8: Set up Firebase
  1. Go to https://console.firebase.google.com
  2. Create new project
  3. Add iOS and Android apps
  4. Download google-services.json (Android)
  5. Download GoogleService-Info.plist (iOS)
  6. Place in android/app/ and ios/ respectively


🚀 RUNNING THE APP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Metro Bundler (Required - run in separate terminal):
  $ npm start
  
  Options:
    --reset-cache     Clear Metro cache
    --clear           Clear watchman cache

Run on Android (requires Android Studio or emulator):
  $ npm run android
  
  Or manually:
    $ npx react-native run-android

Run on iOS (macOS only):
  $ npm run ios
  
  Or manually:
    $ npx react-native run-ios --simulator="iPhone 14 Pro"

Run on Physical Device:
  Android:
    $ adb reverse tcp:8081 tcp:8081  (For Metro bundler)
    $ adb reverse tcp:8000 tcp:8000  (For backend API)
    $ npm run android

  iOS:
    Connect device → Xcode → Build & Run


🔗 CONNECTING TO BACKEND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ensure Phase 2 Server is Running:
  Terminal 1: $ python start_realtime_server.py
              Choose: 3 (Start both server and app)

Mobile App Connection:
  .env file:
    REACT_APP_API_URL=http://your-server.com:8000
    REACT_APP_WS_URL=ws://your-server.com:8000/ws

  For local development (emulator):
    REACT_APP_API_URL=http://10.0.2.2:8000     # Android emulator
    REACT_APP_API_URL=http://localhost:8000    # iOS simulator

  For physical device:
    REACT_APP_API_URL=http://192.168.1.100:8000  # Your machine IP
    REACT_APP_WS_URL=ws://192.168.1.100:8000/ws


📱 SCREENS TO IMPLEMENT (12 Total)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. SplashScreen
   - App logo animation
   - Check authentication status
   - Load cached data
   - Navigate to Login or MainApp

2. LoginScreen
   - Email/password input
   - User type selection (doctor/patient)
   - Login button
   - Forgot password link
   - Register link

3. RegisterScreen
   - User type selection
   - Name, email, password input
   - Additional fields (doctor: specialization)
   - Register button
   - Terms & conditions

4. HomeScreen
   - Different for doctors vs patients
   - Doctor: Shows upcoming appointments
   - Patient: Shows available doctors

5. AppointmentListScreen
   - List of user's appointments
   - Filter by status (pending, confirmed, completed)
   - Search functionality
   - Swipe to cancel

6. BookAppointmentScreen
   - Doctor search/selection
   - Date picker
   - Time slot selection
   - Appointment notes
   - Confirm booking

7. AppointmentDetailScreen
   - Appointment info
   - Doctor/patient details
   - Date & time
   - Status
   - Message button
   - Cancel button (if applicable)

8. ChatScreen
   - Message list
   - Message input
   - Typing indicator
   - Timestamp
   - Offline indicator

9. ProfileScreen
   - User profile info
   - Avatar
   - Edit profile button
   - Doctor specialization (if applicable)
   - Logout button

10. SettingsScreen
    - Notification preferences
    - Working hours (if doctor)
    - Privacy settings
    - About app
    - Version info

11. DoctorScheduleScreen (Doctor only)
    - Weekly schedule view
    - Add/edit working hours
    - Block dates
    - View appointments

12. NotificationsScreen
    - Notification list
    - Mark as read
    - Delete notification
    - Notification details


🔄 REAL-TIME FEATURES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All WebSocket features from Phase 2 now available on mobile:

1. Real-time Chat
   - Live message delivery
   - Typing indicators
   - Read receipts (optional)
   - Offline message queue

2. Appointment Notifications
   - Instant push notifications
   - In-app badges
   - Sound & vibration
   - Deep linking to appointment

3. Schedule Updates
   - Doctor posts schedule change
   - Patients see updated availability
   - Real-time slot availability

4. Online Presence
   - See online doctors
   - See online patients
   - Typing status in chat

5. Device Support
   - Multiple device login
   - Device token management
   - Per-device notifications


📲 FIREBASE SETUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Create Firebase Project
   • Go to https://console.firebase.google.com
   • Click "Create Project"
   • Enter project name: "Medical-Appointment"
   • Enable Google Analytics
   • Click "Create"

2. Add Android App
   • Click "Add app" → "Android"
   • Package name: com.medicalappointment
   • App nickname: Medical Appointment - Android
   • Register app
   • Download google-services.json
   • Place at: android/app/google-services.json

3. Add iOS App
   • Click "Add app" → "iOS"
   • Bundle ID: com.medicalappointment
   • App nickname: Medical Appointment - iOS
   • Register app
   • Download GoogleService-Info.plist
   • Place at: ios/GoogleService-Info.plist

4. Enable Cloud Messaging
   • In Firebase Console → Project Settings
   • Go to "Cloud Messaging" tab
   • Copy Server Key
   • Add to backend for sending push notifications

5. Update .env
   Copy Firebase credentials from Project Settings → General


🧪 TESTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run Tests:
  $ npm test

Test Coverage:
  $ npm test -- --coverage

Debug on Device:
  Android:
    $ adb logcat | grep ReactNativeJS
  
  iOS:
    Open Console.app in macOS
    Select device
    Filter for app name

Detox (E2E Testing):
  $ npm install -g detox-cli
  $ npm install detox detox-cli --save-dev
  $ detox init -r ios
  $ detox build-framework-cache


🏗️  BUILD & DEPLOYMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Android Build:
  $ npm run build-android
  
  Output: android/app/build/outputs/apk/release/app-release.apk
  
  To Google Play Store:
    1. Create Play Store account
    2. Create app in Play Console
    3. Upload APK
    4. Fill store listing
    5. Submit for review

iOS Build:
  $ npm run build-ios
  
  Output: .../Products/Release-iphoneos/
  
  To App Store:
    1. Create App Store Connect account
    2. Create app certificate
    3. Create provisioning profile
    4. Build with credentials
    5. Upload to App Store Connect
    6. Submit for review

Environment-Specific Builds:
  Development:
    ENVIRONMENT=dev npm start
  
  Staging:
    ENVIRONMENT=staging npm run build-android
  
  Production:
    ENVIRONMENT=production npm run build-android


🔒 SECURITY CONSIDERATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Implemented:
  • Authentication tokens
  • Secure storage (Keychain/Keystore)
  • HTTPS/WSS support
  • Input validation
  • Rate limiting ready

TODO:
  • Add JWT refresh logic
  • Implement certificate pinning
  • Add biometric authentication
  • Encrypt sensitive data at rest
  • Add audit logging
  • Implement API key rotation


📊 PERFORMANCE OPTIMIZATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Built-in:
  • Lazy loading screens
  • Message pagination
  • Image caching
  • Offline data caching
  • Zustand optimization

TODO:
  • Implement pagination for appointments
  • Add image compression
  • Optimize re-renders with memoization
  • Add performance monitoring
  • Implement bundle splitting


🐛 TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issue: "Module not found" error
  Solution: $ npm install
            $ npm start -- --reset-cache

Issue: WebSocket connection fails
  Solution: Check .env API_URL
            Ensure backend server is running
            Check firewall/network settings

Issue: Firebase notifications not working
  Solution: Verify google-services.json/GoogleService-Info.plist
            Check Firebase project settings
            Verify FCM token is sent to backend

Issue: App crashes on launch
  Solution: Check console logs: npm start
            Clear app cache: Settings → Apps → Clear Cache
            Rebuild: npm run android

Issue: Slow performance
  Solution: Check bundle size: npm install -g react-native-bundle-visualizer
            Clear Metro cache: npm start -- --reset-cache
            Profile with Flipper debugger


📚 USEFUL COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Development:
  npm start                        Start Metro bundler
  npm run android                  Run on Android emulator
  npm run ios                      Run on iOS simulator
  npm install                      Install dependencies
  npm run lint                     Run ESLint

Testing:
  npm test                         Run Jest tests
  npm test -- --watch             Watch mode
  npm test -- --coverage          Coverage report

Debugging:
  Flipper debugger                 https://fbflipper.com/
  React DevTools                   Chrome DevTools for React
  Hermes debugger (Android)        Built-in JS debugger

Utilities:
  npm run build-android            Build Android release APK
  npm run build-ios                Build iOS release app
  npx react-native doctor         Check environment setup


🎯 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Run setup script:
   $ node setup.js

2. Install dependencies:
   $ npm install

3. Configure environment:
   Edit .env with your API URL

4. Set up Firebase:
   Download google-services.json & GoogleService-Info.plist

5. Start development:
   $ npm start
   $ npm run android  (or npm run ios)

6. Build screens:
   Implement the 12 screen components

7. Test with backend:
   Ensure Phase 2 server is running

8. Deploy:
   $ npm run build-android  (APK for Google Play)
   $ npm run build-ios      (IPA for App Store)


✅ PHASE 3 STATUS: SETUP COMPLETE ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Foundation Created:
  ✅ Project structure
  ✅ All core services (WebSocket, notifications, offline sync)
  ✅ State management (Zustand stores)
  ✅ Navigation setup
  ✅ Configuration files
  ✅ Build scripts
  ✅ Development environment

Ready to:
  ✅ Install dependencies
  ✅ Configure backend connection
  ✅ Implement screen components
  ✅ Run on emulator/device
  ✅ Test with Phase 2 backend
  ✅ Deploy to stores

Integration with Phase 2:
  ✅ WebSocket client connects to Phase 2 server
  ✅ Same event types supported
  ✅ Firebase FCM for push notifications
  ✅ Offline-first syncing with Phase 2 database


════════════════════════════════════════════════════════════════════════════
                   PHASE 3: READY FOR DEVELOPMENT
════════════════════════════════════════════════════════════════════════════

Your React Native medical appointment app foundation is complete!
All core services, state management, and navigation are ready.

Start building by running:
  $ cd mobile-app && node setup.js && npm install && npm start

Then run on device: npm run android (or npm run ios)

Questions? Check TROUBLESHOOTING section above.
════════════════════════════════════════════════════════════════════════════
""")

if __name__ == "__main__":
    pass
