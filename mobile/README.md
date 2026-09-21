# DMLogn8n Mobile Application

A comprehensive mobile application built with React Native and TypeScript that extends the DMLogn8n platform to mobile devices with full-featured gameplay, optimized performance, and mobile-specific features.

## 🚀 Features

### Core Gameplay
- **Full Game Experience**: Complete desktop functionality optimized for mobile
- **Touch Controls**: Intuitive gesture support and mobile-friendly UI
- **Real-time Multiplayer**: WebSocket-based real-time gameplay
- **Character Management**: Create, customize, and manage multiple characters
- **Game Sessions**: Join, create, and manage game sessions
- **Interactive Chat**: Real-time chat with reactions and attachments

### Mobile-Specific Features
- **Offline Mode**: Play without internet connection with automatic sync
- **Push Notifications**: Firebase/Apple push notifications for game events
- **Biometric Security**: Face ID/Touch ID authentication support
- **Background Sync**: Seamless cross-device synchronization
- **AR Features**: Camera integration for augmented reality gameplay
- **Location-based Elements**: GPS integration for location-aware features

### Performance & Security
- **Optimized Performance**: Smooth gameplay with 60 FPS target
- **Local Storage**: Efficient data management and caching
- **Secure Authentication**: JWT tokens with biometric support
- **Data Encryption**: Secure storage of sensitive information
- **Network Resilience**: Graceful handling of connectivity issues

## 📱 Platform Support

- **iOS**: iOS 12.0+ with iPhone and iPad support
- **Android**: Android 6.0+ (API level 23+) with responsive design
- **Cross-Platform**: Single codebase with platform-specific optimizations

## 🛠 Technology Stack

### Frontend
- **React Native**: 0.72.6 with native performance
- **TypeScript**: Full type safety and IntelliSense support
- **Redux Toolkit**: State management with Redux Persist
- **React Navigation**: 6.x with deep linking support
- **React Native Elements**: UI component library
- **React Native Reanimated**: 60 FPS animations

### Backend Services
- **Python**: Flask-based mobile API
- **Firebase**: Push notifications and analytics
- **WebSocket**: Real-time communication
- **Redis**: Session management and caching
- **PostgreSQL**: Primary database (configurable)

### Development Tools
- **Metro**: Fast bundling and hot reloading
- **ESLint + Prettier**: Code quality and formatting
- **Jest**: Unit and integration testing
- **Detox**: End-to-end testing
- **Flipper**: Debugging and performance monitoring

## 📁 Project Structure

```
mobile/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── CharacterCard.tsx
│   │   ├── ChatBubble.tsx
│   │   ├── ActionButton.tsx
│   │   └── GameMap.tsx
│   ├── screens/            # Screen components
│   │   ├── auth/           # Authentication screens
│   │   ├── game/           # Game-specific screens
│   │   ├── DashboardScreen.tsx
│   │   ├── CharactersScreen.tsx
│   │   └── ChatScreen.tsx
│   ├── navigation/         # Navigation configuration
│   │   ├── AppNavigator.tsx
│   │   ├── AuthNavigator.tsx
│   │   └── GameNavigator.tsx
│   ├── services/           # API and service layers
│   │   ├── api.ts          # API communication
│   │   ├── notifications.ts # Push notifications
│   │   ├── offline.ts      # Offline mode support
│   │   └── biometrics.ts   # Biometric auth
│   ├── store/              # Redux state management
│   │   ├── slices/         # Redux Toolkit slices
│   │   └── index.ts        # Store configuration
│   ├── hooks/              # Custom React hooks
│   ├── utils/              # Utility functions
│   ├── types/              # TypeScript type definitions
│   ├── constants/          # App constants
│   └── assets/             # Images, fonts, sounds
├── backend/                # Mobile backend services
│   ├── mobile_api.py       # Main API service
│   ├── push_service.py     # Push notifications
│   ├── offline_sync.py     # Offline synchronization
│   └── mobile_auth.py      # Authentication service
├── scripts/                # Build and deployment scripts
│   ├── build.sh           # Build automation
│   └── deploy.sh          # Deployment pipeline
└── __tests__/             # Test files
```

## 🚀 Getting Started

### Prerequisites

- Node.js 16+ and npm/yarn
- React Native CLI
- Xcode 14+ (for iOS development)
- Android Studio with Android SDK (for Android development)
- Python 3.8+ (for backend services)
- Redis server (for session management)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd DMLogn8n/mobile
   ```

2. **Install dependencies**
   ```bash
   npm install
   cd ios && pod install && cd ..
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start backend services**
   ```bash
   cd backend
   python mobile_api.py &
   python push_service.py &
   python offline_sync.py &
   python mobile_auth.py &
   cd ..
   ```

5. **Run the application**
   ```bash
   # iOS
   npm run ios

   # Android
   npm run android
   ```

### Development

#### Start Metro Bundler
```bash
npm start
```

#### Run Tests
```bash
# Unit tests
npm test

# E2E tests
npm run test:android  # Android
npm run test:ios      # iOS
```

#### Linting
```bash
npm run lint
npm run type-check
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# API Configuration
API_URL=https://api.dmlogn8n.com
WS_URL=wss://api.dmlogn8n.com

# Firebase
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_ANDROID_APP_ID=your-android-app-id
FIREBASE_IOS_APP_ID=your-ios-app-id

# Push Notifications
FIREBASE_SERVER_KEY=your-firebase-server-key
APNS_KEY_PATH=./certificates/apns.p8

# Authentication
JWT_SECRET_KEY=your-jwt-secret
JWT_REFRESH_SECRET_KEY=your-refresh-secret

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Build Configuration
ENVIRONMENT=development
BUILD_TYPE=Debug
```

### Platform-Specific Setup

#### iOS
1. Open `ios/DMLogn8n.xcworkspace` in Xcode
2. Configure signing certificates and provisioning profiles
3. Set up push notification capabilities
4. Add app icons and launch screens

#### Android
1. Open `android/` in Android Studio
2. Configure `android/app/build.gradle` with your signing configuration
3. Set up Firebase for Android
4. Add app icons and adaptive icons

## 📱 Building & Deployment

### Build Commands

```bash
# Build both platforms
npm run build

# Build iOS only
npm run build:ios

# Build Android only
npm run build:android

# Build for production
npm run build:production
```

### Automated Build Script

Use the comprehensive build script:

```bash
# Make executable
chmod +x scripts/build.sh

# Build with options
./scripts/build.sh --clean --test --build-type Release all
```

### Deployment

Deploy to different environments:

```bash
# Make executable
chmod +x scripts/deploy.sh

# Deploy to staging
./scripts/deploy.sh staging all

# Deploy to production
./scripts/deploy.sh production all
```

## 🧪 Testing

### Unit Tests
```bash
npm test
npm run test:watch
npm run test:coverage
```

### Integration Tests
```bash
npm run test:integration
```

### End-to-End Tests
```bash
npm run test:e2e
npm run test:android:emu
npm run test:ios:simulator
```

### Performance Testing
```bash
npm run test:performance
```

## 🎯 Features in Detail

### Offline Mode
- Automatic sync when connectivity is restored
- Conflict resolution with user-friendly interface
- Local caching of game data
- Graceful degradation of features

### Biometric Authentication
- Face ID support on iPhone X+
- Touch ID support on compatible devices
- Fingerprint authentication on Android
- Fallback to passcode authentication

### Push Notifications
- Game invitations and session updates
- Friend requests and social notifications
- Achievement unlocks and progress updates
- Custom notification sounds and actions

### Real-time Communication
- WebSocket-based real-time chat
- Message reactions and threading
- File sharing capabilities
- Voice chat integration (WebRTC)

### AR Features
- Camera integration for AR gameplay
- Location-based game elements
- QR code scanning for game items
- Image recognition for character cards

## 📊 Performance Optimization

### Rendering Performance
- 60 FPS target with React Native Reanimated
- Optimized list rendering with FlatList
- Image lazy loading and caching
- Memory leak prevention

### Network Optimization
- Request batching and deduplication
- Response caching strategies
- Offline-first data architecture
- Background sync optimization

### Bundle Size Optimization
- Code splitting with lazy loading
- Tree shaking for unused code
- Image compression and optimization
- Bundle analysis and monitoring

## 🔒 Security

### Authentication
- JWT token management with refresh tokens
- Biometric authentication with secure storage
- Session management with Redis
- Device registration and management

### Data Protection
- End-to-end encryption for sensitive data
- Secure local storage with encryption
- API request signing and validation
- Certificate pinning for API calls

### Privacy
- Granular permission handling
- Location data protection
- Biometric data isolation
- User data anonymization

## 🐛 Debugging

### Flipper Integration
```bash
# Install Flipper
npm install --save-dev react-native-flipper

# Start Flipper debugger
npx react-native run-android --variant=debug
npx react-native run-ios --configuration Debug
```

### Remote Debugging
```bash
# Enable remote debugging
npx react-native start --reset-cache

# Access debugger at http://localhost:8081/debugger-ui/
```

### Performance Monitoring
```bash
# Install performance tools
npm install --save-dev react-native-performance

# Generate performance report
npm run analyze-bundle
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- Follow TypeScript best practices
- Use ESLint and Prettier configurations
- Write comprehensive tests
- Document new features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Join our Discord community
- Email: support@dmlogn8n.com
- Documentation: https://docs.dmlogn8n.com

## 🗺 Roadmap

### Version 1.1
- Enhanced AR features
- Voice chat improvements
- Offline multiplayer mode
- Performance optimizations

### Version 1.2
- AI-powered character creation
- Advanced game master tools
- Cross-platform party system
- Expanded social features

### Version 2.0
- Full WebRTC implementation
- Advanced offline synchronization
- Machine learning recommendations
- Community marketplace

---

Built with ❤️ by the DMLogn8n Team