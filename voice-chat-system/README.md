# DMlogn8n Voice Chat System

A sophisticated real-time voice communication platform designed specifically for tabletop RPG gaming, featuring spatial audio, character voice customization, and deep integration with game systems.

## ✨ Features

### 🎯 Core Functionality
- **WebRTC Voice Infrastructure** - Peer-to-peer voice connections with SFU support
- **Low Latency Audio** - Optimized for <50ms latency
- **Cross-Platform Support** - Works on desktop and mobile devices
- **Scalable Architecture** - Supports small groups to large campaigns

### 🎵 3D Spatial Audio
- **Position-Based Audio** - Audio moves with character positions
- **Distance Attenuation** - Voice fades with distance
- **Environmental Acoustics** - Room size and reverb simulation
- **Doppler Effect** - Realistic audio movement
- **Environmental Effects** - Weather, terrain, and magical audio effects

### 🎭 Character Voice Customization
- **Race-Specific Voices** - Dwarvish, Elvish, Orcish, Draconic, and more
- **Voice Aging** - Young, adult, old, and ancient voice effects
- **Emotional Modulation** - Happy, sad, angry, fearful voice variations
- **Voice Cloning** - Consistent character voices across sessions
- **Real-Time Processing** - Apply effects during live conversation

### 🎤 Advanced Voice Features
- **Voice Activity Detection** - Automatic push-to-talk
- **Noise Suppression** - Background noise reduction
- **Echo Cancellation** - Clear audio in any environment
- **Speech-to-Text** - Real-time transcription
- **Voice Commands** - Control game actions with your voice
- **Translation Support** - Multi-language communication

### ⚔️ Game Systems Integration
- **Combat Audio** - Synchronized combat sound effects
- **Spell Audio Feedback** - Magical sound effects for spell casting
- **Ambient Sounds** - Dynamic environmental audio
- **Music Integration** - Adaptive music that responds to gameplay
- **Cross-Portal Sync** - Audio state synchronization between game areas

### 📱 Mobile Compatibility
- **Adaptive Quality** - Automatically adjusts to network conditions
- **Battery Optimization** - Power-efficient audio processing
- **Touch Controls** - Mobile-optimized interface
- **Background Mode** - Continue audio when app is backgrounded
- **Haptic Feedback** - Tactile responses to game events

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/dmlogn8n-voice-chat.git
cd dmlogn8n-voice-chat

# Install dependencies
npm install

# Start development server
npm run dev
```

### Basic Usage

```javascript
import { createVoiceChatSystem } from './src/index.js';

// Create voice chat system
const voiceChat = createVoiceChatSystem({
  spatialAudio: { enabled: true },
  voiceProcessing: { noiseSuppression: true }
});

// Initialize
await voiceChat.initialize();

// Connect to room
await voiceChat.connectToRoom('my-game-room', {
  url: 'wss://your-server.com'
});

// Start voice communication
voiceChat.startRecording();
```

### D&D Integration Example

```javascript
import { DNDVoiceIntegration } from './examples/dnd-game-integration.js';

const gameState = new DNDGameState(); // Your game state management
const voiceIntegration = new DNDVoiceIntegration(gameState);

await voiceIntegration.initialize('dungeon-session-42', {
  url: 'wss://voice.dmslogn8n.com',
  token: 'your-auth-token'
});

// Voice commands are now available!
// Say "roll initiative" to roll initiative
// Say "cast fireball" to open spell selection
```

## 📖 Documentation

- [API Documentation](./docs/API.md) - Complete API reference
- [Examples](./examples/) - Integration examples and demos
- [Architecture Guide](./docs/ARCHITECTURE.md) - System architecture overview
- [Mobile Guide](./docs/MOBILE.md) - Mobile-specific features

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Voice Chat System                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   WebRTC Core   │  │ Spatial Audio   │  │ Voice Processor │ │
│  │                 │  │                 │  │                 │ │
│  │ • P2P/ SFU      │  │ • 3D Positioning │  │ • Voice Effects │ │
│  │ • Low Latency   │  │ • Room Acoustics │  │ • Character     │ │
│  │ • Adaptive Bit  │  │ • Environmental  │  │   Voices        │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Game Integration│  │ Mobile Adapter  │  │ Audio Engine    │ │
│  │                 │  │                 │  │                 │ │
│  │ • Combat Audio  │  │ • Battery Opt.   │  │ • Web Audio API │ │
│  │ • Spell Sounds  │  │ • Touch Controls │  │ • Worklets      │ │
│  │ • Ambient Audio │  │ • Adaptation    │  │ • Effects       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🎮 Character Voices

The system includes race-specific voice transformations:

| Race | Voice Characteristics | Pitch | Formant | Resonance |
|------|----------------------|-------|---------|-----------|
| **Human** | Natural voice | 0 | 1.0 | 1.0 |
| **Dwarvish** | Deep, resonant | -0.3 | 0.8 | 1.2 |
| **Elvish** | Melodic, clear | +0.2 | 1.1 | 0.9 |
| **Orcish** | Guttural, harsh | -0.5 | 0.7 | 1.4 |
| **Draconic** | Majestic, powerful | +0.4 | 1.3 | 1.1 |
| **Halfling** | Cheerful, light | +0.3 | 1.15 | 0.95 |
| **Gnome** | Energetic, bright | +0.5 | 1.2 | 0.85 |
| **Undead** | Eerie, whispered | -0.8 | 0.6 | 1.6 |

## 🔧 Configuration

### Default Configuration

```javascript
const config = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' }
  ],
  audio: {
    sampleRate: 48000,
    channelCount: 2,
    maxLatency: 50
  },
  spatialAudio: {
    enabled: true,
    maxDistance: 100,
    roomSize: 'medium'
  },
  voiceProcessing: {
    noiseSuppression: true,
    echoCancellation: true,
    voiceActivityDetection: true
  },
  characterVoices: {
    // Race-specific voice parameters
  },
  gameIntegration: {
    syncWithCombat: true,
    spellAudioFeedback: true
  },
  mobile: {
    enabled: true,
    adaptiveBitrate: true,
    batteryOptimization: true
  }
};
```

### Factories

Pre-configured setups for different scenarios:

```javascript
import { VoiceChatFactory } from './src/index.js';

// Small group (2-4 players)
const smallGroup = VoiceChatFactory.createForSmallGroup();

// Large group (5+ players)
const largeGroup = VoiceChatFactory.createForLargeGroup();

// Mobile optimized
const mobile = VoiceChatFactory.createForMobile();

// Professional streaming
const streaming = VoiceChatFactory.createForStreaming();
```

## 🎵 Audio Features

### Spatial Audio
- **3D Positioning**: Audio positioned in 3D space
- **Distance Attenuation**: Volume decreases with distance
- **Room Acoustics**: Realistic reverberation
- **Environmental Effects**: Weather, terrain, magical effects

### Voice Processing
- **Real-time Effects**: Apply character voices during conversation
- **Noise Reduction**: Remove background noise
- **Echo Cancellation**: Prevent audio feedback
- **Auto Gain Control**: Balance volume levels

### Speech Recognition
- **Voice Commands**: Control game with voice
- **Transcription**: Real-time speech-to-text
- **Language Support**: Multiple languages
- **Custom Commands**: Define your own voice commands

## 📱 Mobile Features

### Adaptive Performance
- **Network Awareness**: Adjust quality based on connection
- **Battery Monitoring**: Optimize for battery life
- **Memory Management**: Efficient resource usage
- **Background Processing**: Continue audio when minimized

### Touch Interface
- **Push-to-Talk**: Touch and hold to speak
- **Gesture Controls**: Swipe actions for common tasks
- **Haptic Feedback**: Vibrations for game events
- **Responsive Design**: Works on all screen sizes

## 🎮 Game Integration

### D&D Support
- **Initiative Tracking**: Voice-activated initiative rolls
- **Spell Casting**: Audio feedback for spells
- **Combat Sounds**: Hit, miss, and critical effects
- **Character Voices**: Race-specific voice modulation

### Custom Integration
- **Event System**: React to game events
- **State Synchronization**: Keep audio in sync
- **Custom Sounds**: Add your own audio effects
- **Modular Architecture**: Use what you need

## 🔧 Development

### Building

```bash
# Development build
npm run build

# Production build
npm run build:prod

# Run tests
npm test

# Lint code
npm run lint
```

### Testing

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run integration tests
npm run test:integration
```

### Project Structure

```
├── src/
│   ├── core/                 # Core voice chat system
│   ├── webrtc/              # WebRTC implementation
│   ├── spatial-audio/       # 3D audio processing
│   ├── voice-processing/    # Voice effects and recognition
│   ├── game-integration/    # Game system integration
│   └── mobile/              # Mobile optimizations
├── tests/                   # Test suite
├── docs/                    # Documentation
├── examples/                # Usage examples
└── worklets/               # Audio processing worklets
```

## 🌐 Browser Compatibility

### Supported Browsers
- ✅ Chrome 88+
- ✅ Firefox 85+
- ✅ Safari 14+
- ✅ Edge 88+

### Required Features
- WebRTC (RTCPeerConnection)
- Web Audio API
- MediaDevices API
- AudioWorklet (for advanced features)

### Feature Detection

```javascript
import { checkCompatibility } from './src/index.js';

const compatibility = checkCompatibility();
if (!compatibility.isCompatible) {
  console.log('Some features may not be available:', compatibility.recommendations);
}
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🆘 Support

- 📖 [Documentation](./docs/)
- 🐛 [Issue Tracker](https://github.com/your-org/dmlogn8n-voice-chat/issues)
- 💬 [Discord Community](https://discord.gg/your-server)
- 📧 [Email Support](mailto:support@dmslogn8n.com)

## 🎯 Roadmap

### Version 1.1
- [ ] Enhanced voice cloning
- [ ] More character voices
- [ ] Improved mobile UI
- [ ] Additional spell effects

### Version 1.2
- [ ] AI-powered noise reduction
- [ ] Real-time translation
- [ ] Voice-based character creation
- [ ] Advanced audio analytics

### Version 2.0
- [ ] VR/AR support
- [ ] Custom audio workbench
- [ ] Plugin system
- [ ] Cloud-based voice profiles

---

**Built with ❤️ for the TTRPG community**

Transform your tabletop gaming experience with immersive, spatial audio that brings your campaigns to life!