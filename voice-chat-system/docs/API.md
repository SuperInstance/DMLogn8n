# DMlogn8n Voice Chat System API Documentation

## Overview

The DMlogn8n Voice Chat System is a sophisticated real-time voice communication platform designed specifically for tabletop RPG gaming. It provides spatial audio, character voice customization, and deep integration with game systems.

## Quick Start

```javascript
import { createVoiceChatSystem } from './src/index.js';

// Create voice chat system with default configuration
const voiceChat = createVoiceChatSystem();

// Initialize the system
await voiceChat.initialize();

// Connect to a voice room
await voiceChat.connectToRoom('my-game-room', {
  url: 'wss://your-server.com'
});

// Start voice communication
voiceChat.startRecording();
```

## Core API

### VoiceChatSystem

The main class that orchestrates all voice chat functionality.

#### Constructor

```javascript
new VoiceChatSystem(config)
```

**Parameters:**
- `config` (Object): Configuration object
  - `iceServers` (Array): STUN/TURN servers for WebRTC
  - `sampleRate` (Number): Audio sample rate (default: 48000)
  - `channelCount` (Number): Audio channels (default: 2)
  - `maxLatency` (Number): Maximum allowed latency in ms (default: 50)
  - `spatialAudio` (Object): Spatial audio configuration
  - `voiceProcessing` (Object): Voice processing settings
  - `gameIntegration` (Object): Game integration settings

#### Methods

##### `async initialize()`

Initialize all voice chat components.

```javascript
await voiceChat.initialize();
```

##### `async connectToRoom(roomId, serverConfig)`

Connect to a voice chat room.

```javascript
await voiceChat.connectToRoom('dungeon-session', {
  url: 'wss://voice.dmslogn8n.com',
  token: 'your-auth-token'
});
```

##### `updateParticipantPosition(participantId, position)`

Update a participant's position for spatial audio.

```javascript
voiceChat.updateParticipantPosition('player-1', {
  x: 10, y: 0, z: 5
});
```

##### `setParticipantVoiceCharacter(participantId, character)`

Apply character voice filter to a participant.

```javascript
voiceChat.setParticipantVoiceCharacter('player-1', 'dwarvish');
```

Available character types:
- `human`
- `dwarvish`
- `elvish`
- `orcish`
- `draconic`
- `halfling`
- `gnome`
- `undead`

##### `async startRecording()`

Start recording microphone input.

```javascript
await voiceChat.startRecording();
```

##### `stopRecording()`

Stop recording microphone input.

```javascript
voiceChat.stopRecording();
```

##### `getPerformanceMetrics()`

Get current performance metrics.

```javascript
const metrics = voiceChat.getPerformanceMetrics();
console.log(metrics);
// {
//   latency: 25,
//   packetLoss: 0.01,
//   audioQuality: 0.95,
//   cpuUsage: 0.3,
//   participantCount: 4
// }
```

##### `async disconnect()`

Disconnect from the voice room and cleanup resources.

```javascript
await voiceChat.disconnect();
```

##### `async destroy()`

Completely destroy the voice chat system.

```javascript
await voiceChat.destroy();
```

#### Events

Listen to system events using the `on` method.

```javascript
voiceChat.on('connectedToRoom', (data) => {
  console.log('Connected to room:', data.roomId);
});

voiceChat.on('participantJoined', (data) => {
  console.log('Participant joined:', data.participantId);
});

voiceChat.on('voiceActivity', (data) => {
  console.log('Voice activity:', data.isActive, 'Level:', data.level);
});

voiceChat.on('transcription', (data) => {
  console.log('Transcription:', data.text);
});
```

Available events:
- `initializationStarted`
- `initializationComplete`
- `initializationError`
- `connectingToRoom`
- `connectedToRoom`
- `connectionError`
- `participantJoined`
- `participantLeft`
- `streamAdded`
- `streamRemoved`
- `voiceActivity`
- `transcription`
- `spatialSourceCreated`
- `positionUpdate`
- `characterFilterApplied`
- `combatSoundPlayed`
- `spellCast`
- `disconnected`

## Spatial Audio

### SpatialAudioEngine

Handles 3D positioning and environmental audio effects.

#### Methods

##### `async createSpatialAudioSystem(sourceId, mediaStream)`

Create a spatial audio source for a participant.

```javascript
const spatialSource = await voiceChat.spatialAudioEngine.createSpatialAudioSystem(
  'player-1',
  mediaStream
);
```

##### `updateListenerPosition(position)`

Update the listener's (your) position.

```javascript
voiceChat.spatialAudioEngine.updateListenerPosition({
  x: 0, y: 0, z: 0
});
```

##### `setRoomSize(roomSize)`

Set the acoustic properties of the room.

```javascript
voiceChat.spatialAudioEngine.setRoomSize('large');
// Available: 'small', 'medium', 'large', 'hall', 'cave', 'forest'
```

##### `applyEnvironmentalEffect(sourceId, effectType, intensity)`

Apply environmental effects to a source.

```javascript
voiceChat.spatialAudioEngine.applyEnvironmentalEffect(
  'player-1',
  'underwater',
  0.8
);
```

## Voice Processing

### VoiceProcessor

Handles voice effects, character customization, and speech processing.

#### Methods

##### `setCharacterVoice(character)`

Set your own character voice.

```javascript
voiceChat.voiceProcessor.setCharacterVoice('elvish');
```

##### `setVoiceAge(age)`

Set voice age effect.

```javascript
voiceChat.voiceProcessor.setVoiceAge('old');
// Available: 'young', 'adult', 'middle', 'old', 'ancient'
```

##### `setEmotion(emotion)`

Set emotional modulation.

```javascript
voiceChat.voiceProcessor.setEmotion('happy');
// Available: 'neutral', 'happy', 'sad', 'angry', 'fearful', 'excited'
```

##### `mute()` / `unmute()`

Mute/unmute your microphone.

```javascript
voiceChat.voiceProcessor.mute();
voiceChat.voiceProcessor.unmute();
```

### SpeechTranscriber

Handles speech-to-text transcription.

#### Methods

##### `start()` / `stop()`

Start/stop transcription.

```javascript
voiceChat.voiceProcessor.speechTranscriber.start();
voiceChat.voiceProcessor.speechTranscriber.stop();
```

##### `setLanguage(language)`

Set transcription language.

```javascript
voiceChat.voiceProcessor.speechTranscriber.setLanguage('en-US');
```

##### `registerCommand(name, pattern, handler)`

Register voice commands.

```javascript
voiceChat.voiceProcessor.speechTranscriber.registerCommand(
  'rollDice',
  'roll\\s+(d\\d+)',
  (args) => {
    const dice = args[0];
    console.log(`Rolling ${dice}`);
  }
);
```

## Game Integration

### GameAudioIntegrator

Integrates voice chat with game systems.

#### Methods

##### `async initialize(audioContext)`

Initialize game audio integration.

```javascript
await voiceChat.gameIntegrator.initialize(voiceChat.state.audioContext);
```

##### `addCombatSoundEffects(effects, participants)`

Add combat sound effects.

```javascript
voiceChat.gameIntegrator.addCombatSoundEffects([
  { type: 'hit', intensity: 0.8, position: { x: 5, y: 0, z: 0 } }
], ['player-1', 'player-2']);
```

##### `addSpellAudio(spell, caster, target)`

Add spell casting audio.

```javascript
voiceChat.gameIntegrator.addSpellAudio(
  { name: 'fireball', school: 'evocation', duration: 2000 },
  { id: 'caster-1', position: { x: 0, y: 0, z: 0 } },
  { id: 'target-1', position: { x: 10, y: 0, z: 0 } }
);
```

### CombatSoundEffects

Manages combat-related audio.

#### Methods

##### `startCombat(participants)`

Start combat mode with enhanced audio.

```javascript
voiceChat.gameIntegrator.combatSoundEffects.startCombat(['player-1', 'player-2']);
```

##### `processCombatEvent(event)`

Process a combat event.

```javascript
voiceChat.gameIntegrator.combatSoundEffects.processCombatEvent({
  type: 'meleeAttack',
  attacker: { id: 'player-1', position: { x: 0, y: 0, z: 0 } },
  defender: { id: 'monster-1', position: { x: 5, y: 0, z: 0 } },
  damage: 15,
  critical: false
});
```

### SpellAudioProcessor

Handles magical spell audio.

#### Methods

##### `async castSpell(spellName, caster, target)`

Cast a spell with audio effects.

```javascript
await voiceChat.gameIntegrator.spellAudioProcessor.castSpell(
  'fireball',
  { id: 'wizard-1', position: { x: 0, y: 0, z: 0 } },
  { id: 'dragon-1', position: { x: 20, y: 0, z: 0 } }
);
```

##### `addSpellDefinition(name, definition)`

Add custom spell definition.

```javascript
voiceChat.gameIntegrator.spellAudioProcessor.addSpellDefinition('lightningBolt', {
  school: 'evocation',
  element: 'lightning',
  castingTime: 1500,
  soundProfile: {
    frequency: 300,
    harmonics: [1, 2, 3, 4],
    envelope: { attack: 0.01, decay: 0.1, sustain: 0.2, release: 0.3 },
    effects: ['electricity', 'crackle']
  }
});
```

## Mobile Compatibility

### MobileVoiceAdapter

Provides mobile-specific optimizations.

#### Methods

##### `async initialize()`

Initialize mobile adapter.

```javascript
await voiceChat.mobileAdapter.initialize();
```

##### `getAudioConstraints()`

Get mobile-optimized audio constraints.

```javascript
const constraints = voiceChat.mobileAdapter.getAudioConstraints();
```

##### `triggerHapticFeedback(pattern)`

Trigger haptic feedback.

```javascript
voiceChat.mobileAdapter.triggerHapticFeedback([10, 50, 10]); // Vibrate pattern
```

## Configuration

### Default Configuration

```javascript
const defaultConfig = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' }
  ],
  audio: {
    sampleRate: 48000,
    channelCount: 2,
    bufferSize: 4096,
    maxLatency: 50,
    bitrate: 128000
  },
  spatialAudio: {
    enabled: true,
    maxDistance: 100,
    rolloffFactor: 1.0,
    roomSize: 'medium',
    reverbLevel: 0.3,
    dopplerEffect: true
  },
  voiceProcessing: {
    noiseSuppression: true,
    echoCancellation: true,
    autoGainControl: true,
    voiceActivityDetection: true,
    compressionEnabled: true
  },
  characterVoices: {
    dwarvish: { pitch: -0.3, formantShift: 0.8, resonance: 1.2 },
    elvish: { pitch: 0.2, formantShift: 1.1, resonance: 0.9 },
    orcish: { pitch: -0.5, formantShift: 0.7, resonance: 1.4 },
    human: { pitch: 0, formantShift: 1.0, resonance: 1.0 },
    draconic: { pitch: 0.4, formantShift: 1.3, resonance: 1.1 }
  },
  gameIntegration: {
    syncWithCombat: true,
    spellAudioFeedback: true,
    ambientSounds: true,
    musicIntegration: true,
    crossPortalSync: true
  },
  mobile: {
    enabled: true,
    optimizedCodecs: true,
    adaptiveBitrate: true,
    batteryOptimization: true
  }
};
```

### Factories

Pre-configured factories for different use cases:

```javascript
import { VoiceChatFactory } from './src/index.js';

// Small group (2-4 players)
const smallGroupChat = VoiceChatFactory.createForSmallGroup();

// Large group (5+ players)
const largeGroupChat = VoiceChatFactory.createForLargeGroup();

// Mobile optimized
const mobileChat = VoiceChatFactory.createForMobile();

// Professional streaming
const streamingChat = VoiceChatFactory.createForStreaming();
```

## Error Handling

The voice chat system emits error events for various failure scenarios:

```javascript
voiceChat.on('transcriptionError', (error) => {
  console.error('Transcription failed:', error.message);
});

voiceChat.on('connectionError', (error) => {
  console.error('Connection failed:', error.message);
  // Implement reconnection logic
});

voiceChat.on('initializationError', (error) => {
  console.error('Initialization failed:', error.message);
  // Fallback to basic audio
});
```

## Browser Compatibility

### Supported Browsers
- Chrome 88+
- Firefox 85+
- Safari 14+
- Edge 88+

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

## Performance Optimization

### Monitoring Performance

```javascript
setInterval(() => {
  const metrics = voiceChat.getPerformanceMetrics();

  if (metrics.latency > 100) {
    console.warn('High latency detected:', metrics.latency);
  }

  if (metrics.audioQuality < 0.8) {
    console.warn('Poor audio quality:', metrics.audioQuality);
  }
}, 5000);
```

### Adaptive Quality

The system automatically adapts quality based on:
- Network conditions
- Battery level (mobile)
- CPU usage
- Memory usage

### Mobile Optimizations

- Reduced audio quality on low battery
- Adaptive bitrate based on network
- Suspended audio processing when backgrounded
- Touch-optimized controls

## Examples

### Basic Voice Chat Setup

```javascript
import { createVoiceChatSystem } from './src/index.js';

async function setupVoiceChat() {
  const voiceChat = createVoiceChatSystem({
    spatialAudio: { enabled: true },
    voiceProcessing: { noiseSuppression: true }
  });

  await voiceChat.initialize();
  await voiceChat.connectToRoom('my-dungeon', {
    url: 'wss://voice.dmslogn8n.com'
  });

  // Handle participants joining
  voiceChat.on('participantJoined', (data) => {
    console.log(`Player ${data.participantId} joined the voice chat`);
  });

  // Handle voice activity
  voiceChat.on('voiceActivity', (data) => {
    if (data.isActive) {
      // Show speaking indicator
      updateSpeakingIndicator(true, data.level);
    } else {
      updateSpeakingIndicator(false);
    }
  });

  return voiceChat;
}
```

### D&D Game Integration

```javascript
async function setupDNDVoiceChat() {
  const voiceChat = createVoiceChatSystem({
    gameIntegration: {
      syncWithCombat: true,
      spellAudioFeedback: true
    }
  });

  await voiceChat.initialize();
  await voiceChat.connectToRoom('dnd-session-42');

  // Initialize game audio
  await voiceChat.gameIntegrator.initialize(voiceChat.state.audioContext);

  // Set up character voices
  voiceChat.on('participantJoined', (data) => {
    const character = getCharacterForPlayer(data.participantId);
    if (character) {
      voiceChat.setParticipantVoiceCharacter(data.participantId, character.race);
    }
  });

  // Handle combat events
  gameState.on('combatStart', (combat) => {
    voiceChat.gameIntegrator.combatSoundEffects.startCombat(combat.participants);
  });

  gameState.on('spellCast', (spell) => {
    voiceChat.gameIntegrator.addSpellAudio(spell, spell.caster, spell.target);
  });

  return voiceChat;
}
```

### Mobile Voice Chat

```javascript
async function setupMobileVoiceChat() {
  const voiceChat = VoiceChatFactory.createForMobile({
    mobile: {
      batteryOptimization: true,
      adaptiveBitrate: true,
      hapticFeedback: true
    }
  });

  await voiceChat.initialize();
  await voiceChat.connectToRoom('mobile-game');

  // Set up touch controls
  const pushToTalkBtn = document.getElementById('push-to-talk');
  pushToTalkBtn.addEventListener('touchstart', () => {
    voiceChat.startRecording();
    voiceChat.mobileAdapter.triggerHapticFeedback(10);
  });

  pushToTalkBtn.addEventListener('touchend', () => {
    voiceChat.stopRecording();
  });

  // Monitor battery level
  voiceChat.mobileAdapter.on('batteryLevelChanged', (data) => {
    if (data.isLowPowerMode) {
      showLowPowerWarning();
    }
  });

  return voiceChat;
}
```

## Troubleshooting

### Common Issues

1. **Microphone Permission Denied**
   - Ensure HTTPS is used
   - Check browser permissions
   - Try getUserMedia directly first

2. **Audio Context Suspended**
   - User interaction required to start audio
   - Call resume() on user gesture

3. **High Latency**
   - Check network connection
   - Reduce audio quality
   - Move closer to router

4. **Echo Issues**
   - Use headphones
   - Enable echo cancellation
   - Reduce microphone gain

### Debug Mode

Enable debug logging:

```javascript
const voiceChat = createVoiceChatSystem({
  debug: true
});
```

This will log detailed information about:
- WebRTC connection state
- Audio processing metrics
- Spatial audio calculations
- Network performance

## Support

For additional support:
- Check the GitHub Issues
- Review the API documentation
- Test with the provided examples
- Use browser developer tools for debugging