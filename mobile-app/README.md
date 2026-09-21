# DMlogn8n Mobile App

A comprehensive mobile application for Dungeons & Dragons campaign management, built with React Native and Expo. This app brings the full D&D experience to mobile devices with touch-optimized interfaces, AR features, offline capabilities, and seamless synchronization.

## 🎯 Features

### Core Features
- **Touch-Optimized Character Sheets** - Intuitive swipe navigation and gesture controls
- **Mobile Dice Roller** - Haptic feedback and realistic physics simulation
- **Combat Tracker** - Initiative management and health tracking
- **AR Miniature Scanner** - Camera integration for digital miniatures
- **Voice Chat Integration** - Hands-free voice commands and communication
- **Offline Mode** - Full functionality without internet connection
- **Push Notifications** - Game alerts, turn reminders, and party updates
- **Cloud Synchronization** - Seamless data sync across all devices

### Advanced Features
- **AI-Powered DM Assistant** - Encounter balancing and storytelling help
- **Real-Time Collaboration** - Live party updates and shared sessions
- **Biometric Authentication** - Secure login with Face ID/fingerprint
- **Tablet Optimization** - Enhanced experience for larger screens
- **Accessibility Support** - Screen reader, high contrast, and voice control

## 🏗️ Architecture

### Technology Stack
- **Framework**: React Native 0.73+ with Expo 50+
- **Navigation**: React Navigation 6
- **State Management**: Redux Toolkit with Zustand
- **Database**: SQLite with WatermelonDB for offline storage
- **Authentication**: Biometric integration with secure storage
- **Real-time**: WebSocket connections for live updates
- **AR/VR**: Three.js with WebXR support
- **Notifications**: Expo Notifications (FCM/APNS)
- **Audio**: Custom sound engine with speech synthesis

### Project Structure
```
mobile-app/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── common/         # Shared components
│   │   ├── forms/          # Form components
│   │   └── ar/             # AR-specific components
│   ├── screens/            # Screen components
│   │   ├── auth/           # Authentication screens
│   │   ├── characters/     # Character management
│   │   ├── campaigns/      # Campaign screens
│   │   ├── dice/           # Dice roller
│   │   ├── combat/         # Combat tracker
│   │   ├── ar/             # AR scanner
│   │   ├── voice/          # Voice chat
│   │   ├── chat/           # Messaging
│   │   └── settings/       # App settings
│   ├── navigation/         # Navigation configuration
│   ├── services/           # Business logic services
│   │   ├── authService.ts
│   │   ├── syncService.ts
│   │   ├── notificationService.ts
│   │   ├── hapticsService.ts
│   │   ├── audioService.ts
│   │   ├── voiceService.ts
│   │   ├── arService.ts
│   │   ├── diceService.ts
│   │   └── storageService.ts
│   ├── store/              # Redux store
│   │   ├── slices/         # Feature slices
│   │   └── hooks.ts        # Redux hooks
│   ├── types/              # TypeScript definitions
│   │   ├── index.ts
│   │   ├── sync.ts
│   │   ├── ar.ts
│   │   └── navigation.ts
│   ├── theme/              # Theme and styling
│   │   └── theme.ts
│   └── utils/              # Utility functions
├── assets/                 # Static assets
│   ├── images/
│   ├── sounds/
│   ├── models/             # 3D models for AR
│   └── fonts/
├── App.tsx                 # Main app component
├── app.json               # Expo configuration
├── package.json           # Dependencies
├── babel.config.js        # Babel configuration
└── metro.config.js        # Metro bundler config
```

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn
- Expo CLI (`npm install -g @expo/cli`)
- Physical iOS/Android device for testing AR features

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dmlogn8n/mobile-app.git
   cd mobile-app
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Start the development server**
   ```bash
   npm start
   # or
   expo start
   ```

4. **Run on device/simulator**
   ```bash
   # iOS
   npm run ios

   # Android
   npm run android

   # Web (limited features)
   npm run web
   ```

### Environment Configuration

Create a `.env` file in the root directory:

```env
# API Configuration
API_BASE_URL=https://api.dmlogn8n.com/v1
WEBSOCKET_URL=wss://api.dmlogn8n.com/ws

# Authentication
JWT_SECRET=your-jwt-secret-here
ENCRYPTION_KEY=your-encryption-key-here

# External Services
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Push Notifications (optional)
EXPO_PUSH_NOTIFICATION_KEY=your-expo-push-key

# Analytics (optional)
AMPLITUDE_API_KEY=your-amplitude-key
```

## 📱 Key Features

### Character Sheets
- **Touch gestures** for quick navigation between sections
- **Voice commands** for skill checks and actions
- **Real-time health tracking** with animated health bars
- **Swipe-based tabs** for abilities, equipment, and spells
- **Quick actions** for common tasks (rest, level up, etc.)

### Dice Roller
- **Realistic 3D dice physics** with haptic feedback
- **Custom dice skins** and animations
- **Voice-controlled rolling** ("Roll perception check")
- **Critical hit/fumble animations** with special effects
- **Roll history** with detailed statistics
- **Shake-to-roll** functionality

### AR Scanner
- **Camera-based miniature detection** for physical to digital conversion
- **Real-time AR placement** on real tables and surfaces
- **Gesture controls** for positioning and scaling
- **Multi-marker scenes** with environmental effects
- **Photo and video capture** of AR sessions
- **Social sharing** of AR scenes

### Combat Tracker
- **Initiative management** with automatic sorting
- **Visual health bars** with damage/healing animations
- **Condition tracking** with color-coded status effects
- **Turn notifications** with haptic feedback
- **Quick damage/healing** buttons with type selection
- **Combat statistics** and round tracking

### Offline Mode
- **Full offline functionality** for all core features
- **Intelligent sync** when connection is restored
- **Conflict resolution** for simultaneous edits
- **Local storage** of all character and campaign data
- **Background sync** queue management

## 🔧 Development

### Code Style
- **TypeScript** for type safety
- **ESLint** and **Prettier** for consistent formatting
- **Husky** for pre-commit hooks
- **Conventional commits** for changelog generation

### Testing
```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

### Building for Production
```bash
# Development build
npm run build:development

# Preview build
npm run build:preview

# Production build
npm run build:production
```

### Deployment
```bash
# Build for all platforms
eas build --profile production --platform all

# Submit to app stores
eas submit --profile production

# Create preview build
eas build --profile preview --platform all
```

## 🎨 UI/UX Guidelines

### Design System
- **Dark theme** optimized for gaming sessions
- **D&D-inspired color palette** with gold and brass accents
- **Touch-optimized components** with proper sizing
- **Consistent spacing** using 8dp grid system
- **Custom typography** with fantasy-themed fonts

### Accessibility
- **Screen reader support** (VoiceOver, TalkBack)
- **Voice control** integration for hands-free operation
- **High contrast modes** for visual impairments
- **Adjustable text sizes** for readability
- **Haptic feedback** for non-visual interactions

### Performance Optimizations
- **60 FPS animations** with native drivers
- **Lazy loading** for character assets
- **Image optimization** with WebP format
- **Background sync** for non-critical operations
- **Memory pooling** for frequent allocations

## 🔐 Security

### Authentication
- **Biometric authentication** (Face ID, Touch ID, fingerprint)
- **Secure token storage** with device keychain
- **Session management** with automatic refresh
- **Two-factor authentication** support
- **Device authorization** and management

### Data Protection
- **End-to-end encryption** for sensitive character data
- **Local database encryption** with SQLite cipher
- **Secure API communication** with certificate pinning
- **Audit logging** for all data access
- **GDPR compliance** features

## 📊 Analytics & Monitoring

### Performance Monitoring
- **Crash reporting** with detailed stack traces
- **Performance metrics** (load times, memory usage)
- **User behavior tracking** (with privacy controls)
- **Real-time error monitoring**
- **A/B testing** framework integration

### Business Analytics
- **User engagement** metrics
- **Feature usage** statistics
- **Session duration** tracking
- **Retention and churn** analysis
- **Revenue attribution** for premium features

## 🔄 Synchronization

### Offline-First Architecture
- **Local-first data storage** with SQLite
- **Operational transformation** for conflict resolution
- **Background sync** queue management
- **Delta synchronization** for efficient updates
- **Real-time collaboration** with WebSockets

### Cloud Storage
- **Automatic backups** to cloud storage
- **Version history** for characters and campaigns
- **Cross-device synchronization** with conflict resolution
- **Share links** for campaign collaboration
- **Import/export** functionality

## 🎮 Game Integration

### D&D 5e Support
- **Complete ruleset** implementation
- **Official character sheet** compatibility
- **Spell database** with descriptions and mechanics
- **Monster stat blocks** with AI-generated content
- **Magic item database** with properties and effects

### DM Tools
- **AI-powered encounter** balancing
- **Random encounter** generation
- **Campaign timeline** management
- **NPC relationship** tracking
- **World building** tools and templates

## 🚀 Future Roadmap

### Phase 1 (Current - Q1 2024)
- ✅ Core mobile app with character management
- ✅ Dice roller with haptic feedback
- ✅ Offline mode with sync
- ✅ Push notifications
- ✅ AR scanner basics

### Phase 2 (Q2 2024)
- 🔄 Voice chat integration
- 🔄 Advanced AR features
- 🔄 Mobile DM tools
- 🔄 Enhanced combat tracker
- 🔄 Multi-language support

### Phase 3 (Q3 2024)
- ⏳ AI-powered storytelling
- ⏳ Custom content marketplace
- ⏳ Integration with Roll20/Foundry
- ⏳ Advanced analytics
- ⏳ Gamification features

### Phase 4 (Q4 2024)
- ⏳ Console applications
- ⏳ VR/AR headset support
- ⏳ Tabletop holographic displays
- ⏳ AI dungeon master assistant
- ⏳ Global multiplayer features

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style Requirements
- Follow TypeScript strict mode
- Use conventional commit messages
- Write tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.dmlogn8n.com](https://docs.dmlogn8n.com)
- **Discord Community**: [discord.gg/dmlogn8n](https://discord.gg/dmlogn8n)
- **Bug Reports**: [GitHub Issues](https://github.com/dmlogn8n/mobile-app/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/dmlogn8n/mobile-app/discussions)

## 🏆 Acknowledgments

- **Expo Team** for the amazing React Native framework
- **React Native Community** for excellent libraries
- **D&D Beyond** for inspiration on character management
- **Roll20** for pioneering digital tabletop gaming
- **Foundry VTT** for advanced DM tools inspiration

---

Made with ❤️ by the DMlogn8n Team

*Bringing the magic of D&D to mobile devices everywhere*