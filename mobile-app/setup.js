#!/usr/bin/env node

/**
 * React Native Medical Appointment App - Setup Script
 * Complete project setup and initialization
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PROJECT_ROOT = __dirname;
const DIRECTORIES = [
  'src/screens',
  'src/components',
  'src/hooks',
  'src/utils',
  'src/styles',
  'src/navigation',
  'ios',
  'android',
];

const SCREEN_TEMPLATES = [
  'SplashScreen',
  'LoginScreen',
  'RegisterScreen',
  'HomeScreen',
  'AppointmentListScreen',
  'BookAppointmentScreen',
  'AppointmentDetailScreen',
  'ChatScreen',
  'ProfileScreen',
  'SettingsScreen',
  'DoctorScheduleScreen',
  'NotificationsScreen',
];

const COLORS = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  green: '\x1b[32m',
  blue: '\x1b[34m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
};

function log(message, color = 'reset') {
  console.log(`${COLORS[color]}${message}${COLORS.reset}`);
}

function createDirectories() {
  log('\n📁 Creating directories...', 'blue');
  DIRECTORIES.forEach((dir) => {
    const fullPath = path.join(PROJECT_ROOT, dir);
    if (!fs.existsSync(fullPath)) {
      fs.mkdirSync(fullPath, { recursive: true });
      log(`  ✓ ${dir}`, 'green');
    }
  });
}

function createProjectStructure() {
  log('\n📂 Setting up project structure...', 'blue');

  // Create .env file
  const envContent = `# Backend API
REACT_APP_API_URL=http://your-server.com:8000
REACT_APP_WS_URL=ws://your-server.com:8000/ws

# Firebase Configuration
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_firebase_auth_domain
FIREBASE_DATABASE_URL=your_firebase_database_url
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_STORAGE_BUCKET=your_firebase_storage_bucket
FIREBASE_MESSAGING_SENDER_ID=your_firebase_sender_id
FIREBASE_APP_ID=your_firebase_app_id

# App Configuration
APP_NAME=Medical Appointment
APP_VERSION=1.0.0
DEBUG=true
`;
  fs.writeFileSync(path.join(PROJECT_ROOT, '.env'), envContent);
  log('  ✓ .env file created', 'green');

  // Create .gitignore
  const gitignoreContent = `node_modules/
.env
.env.local
.DS_Store
*.log
build/
dist/
.gradle/
.idea/
*.xcworkspace/
Pods/
`;
  fs.writeFileSync(path.join(PROJECT_ROOT, '.gitignore'), gitignoreContent);
  log('  ✓ .gitignore created', 'green');

  // Create app.json
  const appJsonContent = {
    name: 'Medical Appointment',
    displayName: 'Medical Appointment',
    version: '1.0.0',
    newArchEnabled: true,
  };
  fs.writeFileSync(
    path.join(PROJECT_ROOT, 'app.json'),
    JSON.stringify(appJsonContent, null, 2)
  );
  log('  ✓ app.json created', 'green');
}

function createConfigFiles() {
  log('\n⚙️  Creating configuration files...', 'blue');

  // Create constants
  const constantsContent = `/**
 * App Constants
 */

export const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
export const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';

export const USER_TYPES = {
  DOCTOR: 'doctor',
  PATIENT: 'patient',
};

export const APPOINTMENT_STATUS = {
  PENDING: 'pending',
  CONFIRMED: 'confirmed',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
};

export const NOTIFICATION_TYPES = {
  APPOINTMENT: 'appointment',
  MESSAGE: 'message',
  REMINDER: 'reminder',
  EMERGENCY: 'emergency',
};

// Time slots configuration
export const TIME_SLOT_DURATION = 30; // minutes
export const WORKING_HOURS_START = 9; // 9 AM
export const WORKING_HOURS_END = 17; // 5 PM

// Cache TTL (in milliseconds)
export const CACHE_TTL = {
  DOCTORS: 3600000, // 1 hour
  APPOINTMENTS: 300000, // 5 minutes
  USER_PROFILE: 3600000, // 1 hour
  SCHEDULE: 1800000, // 30 minutes
};

export const COLORS = {
  PRIMARY: '#2196F3',
  PRIMARY_DARK: '#1976D2',
  SECONDARY: '#FF9800',
  SUCCESS: '#4CAF50',
  ERROR: '#F44336',
  WARNING: '#FFC107',
  INFO: '#00BCD4',
  LIGHT_GRAY: '#F5F5F5',
  DARK_GRAY: '#757575',
  BORDER: '#BDBDBD',
};

export const SIZES = {
  SMALL: 8,
  MEDIUM: 12,
  LARGE: 16,
  X_LARGE: 24,
};
`;
  fs.writeFileSync(path.join(PROJECT_ROOT, 'src/constants.js'), constantsContent);
  log('  ✓ constants.js created', 'green');
}

function displaySetupInstructions() {
  log('\n' + '='.repeat(70), 'bright');
  log('  🎉 REACT NATIVE PROJECT SETUP COMPLETE!', 'green');
  log('='.repeat(70) + '\n', 'bright');

  log('📋 Next Steps:', 'blue');
  log('');
  log('1. Install Project Dependencies:');
  log('   $ npm install', 'yellow');
  log('');
  log('2. Install iOS Dependencies (macOS only):');
  log('   $ cd ios && pod install && cd ..', 'yellow');
  log('');
  log('3. Set Up Firebase:');
  log('   - Create Firebase project at https://console.firebase.google.com', 'yellow');
  log('   - Update .env with Firebase credentials', 'yellow');
  log('   - Download google-services.json (Android) and GoogleService-Info.plist (iOS)', 'yellow');
  log('');
  log('4. Configure Backend URL:');
  log('   - Update REACT_APP_API_URL in .env', 'yellow');
  log('   - Update REACT_APP_WS_URL in .env', 'yellow');
  log('');
  log('5. Create Screen Components:');
  SCREEN_TEMPLATES.forEach((screen) => {
    log(`   src/screens/${screen}.js`, 'yellow');
  });
  log('');
  log('6. Run the App:');
  log('   $ npm start                    # Start Metro bundler', 'yellow');
  log('   $ npm run android              # Run on Android emulator', 'yellow');
  log('   $ npm run ios                  # Run on iOS simulator', 'yellow');
  log('');
  log('📚 Project Structure:', 'blue');
  log(`
  mobile-app/
  ├── src/
  │   ├── screens/          # Screen components
  │   ├── components/       # Reusable components
  │   ├── hooks/           # Custom React hooks
  │   ├── services/        # API & WebSocket services
  │   ├── stores/          # Zustand state stores
  │   ├── utils/           # Utility functions
  │   ├── styles/          # Global styles
  │   ├── navigation/      # Navigation setup
  │   └── constants.js     # App constants
  ├── ios/                 # iOS configuration
  ├── android/             # Android configuration
  ├── App.js              # Main app component
  ├── package.json        # Dependencies
  ├── app.json            # App configuration
  └── .env                # Environment variables
  `, 'blue');

  log('🔌 Key Files Already Created:', 'blue');
  log('  ✓ App.js                    - Main navigation and auth flow', 'green');
  log('  ✓ src/services/realtimeClient.js   - WebSocket implementation', 'green');
  log('  ✓ src/services/pushNotifications.js - Firebase push notifications', 'green');
  log('  ✓ src/services/offlineSync.js      - Offline-first data sync', 'green');
  log('  ✓ src/stores/authStore.js          - Authentication state', 'green');
  log('  ✓ src/stores/realtimeStore.js      - Real-time data state', 'green');
  log('  ✓ src/stores/offlineStore.js       - Offline data management', 'green');
  log('');

  log('📱 Features Included:', 'blue');
  log('  ✓ Real-time WebSocket integration', 'green');
  log('  ✓ Firebase push notifications', 'green');
  log('  ✓ Offline-first architecture', 'green');
  log('  ✓ Bottom tab navigation', 'green');
  log('  ✓ Authentication flow', 'green');
  log('  ✓ State management with Zustand', 'green');
  log('  ✓ Automatic reconnection', 'green');
  log('  ✓ Message queueing', 'green');
  log('  ✓ Chat system', 'green');
  log('  ✓ Appointment booking', 'green');
  log('  ✓ Notifications', 'green');
  log('');

  log('🚀 Deployment:', 'blue');
  log('  Android:');
  log('    $ npm run build-android', 'yellow');
  log('    Upload APK to Google Play Store', 'yellow');
  log('');
  log('  iOS:');
  log('    $ npm run build-ios', 'yellow');
  log('    Upload IPA to Apple App Store', 'yellow');
  log('');

  log('📞 Troubleshooting:', 'blue');
  log('  - Clear node_modules and reinstall: npm install', 'yellow');
  log('  - Reset Metro cache: npm start -- --reset-cache', 'yellow');
  log('  - Check Node version: node --version (need 16.x or higher)', 'yellow');
  log('  - Check npm version: npm --version', 'yellow');
  log('');

  log('='.repeat(70) + '\n', 'bright');
}

function main() {
  log('\n╔════════════════════════════════════════════════════════════════════╗', 'bright');
  log('║    React Native Medical Appointment App - Setup                    ║', 'bright');
  log('║    Phase 3: Mobile Development                                     ║', 'bright');
  log('╚════════════════════════════════════════════════════════════════════╝\n', 'bright');

  try {
    createDirectories();
    createProjectStructure();
    createConfigFiles();
    displaySetupInstructions();

    log('✅ Setup complete! Your mobile app is ready for development.', 'green');
  } catch (error) {
    log(`\n❌ Setup failed: ${error.message}`, 'red');
    process.exit(1);
  }
}

main();
