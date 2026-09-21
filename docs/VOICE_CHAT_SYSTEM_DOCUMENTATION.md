# DMlogn8n Voice Chat & Audio System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Installation & Deployment](#installation--deployment)
5. [API Documentation](#api-documentation)
6. [Client Integration](#client-integration)
7. [Configuration](#configuration)
8. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
9. [Security Considerations](#security-considerations)
10. [Performance Optimization](#performance-optimization)

## System Overview

The DMlogn8n Voice Chat & Audio System is a comprehensive, production-ready voice communication platform designed for immersive tabletop RPG experiences. It provides Discord-quality audio with advanced features including spatial audio, character voice modulation, dynamic music, and seamless n8n workflow integration.

### Key Features

- **WebRTC Voice Communication**: Low-latency peer-to-peer and SFU-mediated voice chat
- **Spatial Audio**: 3D positional audio based on character locations
- **Character Voice Modulation**: Unique voice profiles for different character types (Dwarves, Elves, Orcs, etc.)
- **Dynamic Music Management**: Adaptive music that responds to scene intensity and context
- **Sound Effects Library**: Comprehensive SFX library with real-time processing
- **Voice Recording & Playback**: Session recording for content creation
- **Push-to-Talk & Voice Activation**: Flexible audio input controls
- **n8n Integration**: Automated workflows for content processing and distribution
- **Quality Monitoring**: Real-time audio quality metrics and optimization

## Architecture

The system follows a microservices architecture with the following components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Web    │    │   Client Web    │    │   Client Web    │
│     Browser     │    │     Browser     │    │     Browser     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │     Nginx Proxy         │
                    │   (Load Balancer)       │
                    └─────────────┬─────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────▼─────────┐  ┌─────────▼─────────┐  ┌─────────▼─────────┐
│  Voice Chat      │  │  SFU Server       │  │  Integration     │
│  Server          │  │ (Media Router)    │  │  Layer           │
│  (Signaling)     │  │                   │  │  (n8n Workflows) │
└───────────────────┘  └───────────────────┘  └───────────────────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    Redis Cache           │
                    │  (Session Management)    │
                    └───────────────────────────┘

          ┌─────────────────┐  ┌─────────────────┐
          │ Sound Effects   │  │ Dynamic Music   │
          │ Library         │  │ Manager         │
          └─────────────────┘  └─────────────────┘
```

### Component Interactions

1. **Client → Voice Chat Server**: WebSocket connections for signaling and room management
2. **Client ↔ SFU Server**: WebRTC media streams for audio routing
3. **Integration Layer → n8n**: HTTP/webhook triggers for automated workflows
4. **All Services → Redis**: Shared session state and caching
5. **Nginx**: Load balancing and SSL termination

## Components

### 1. Voice Chat Server (Port 8001)

**Purpose**: Handles WebSocket signaling, room management, and session coordination.

**Key Features**:
- Room creation and management
- Participant authentication
- Spatial audio position tracking
- Character voice profile management
- Push-to-talk and voice activation controls

**API Endpoints**:
```
GET  /rooms                    - List public rooms
POST /rooms                    - Create new room
GET  /rooms/{id}               - Get room details
GET  /character-profiles       - Get character voice profiles
WS   /ws/voice/{room_id}       - WebSocket signaling
```

### 2. SFU Server (Port 8002)

**Purpose**: Selective Forwarding Unit for scalable multi-party audio routing.

**Key Features**:
- WebRTC media stream routing
- Audio quality optimization
- Bandwidth management
- Performance monitoring

**API Endpoints**:
```
POST /join                     - Join SFU session
POST /ice-candidate            - Handle ICE candidates
GET  /stats                    - Get SFU statistics
DELETE /participants/{id}      - Leave SFU session
WS   /ws/sfu/{room_id}         - SFU signaling
```

### 3. Sound Effects Library (Port 8003)

**Purpose**: Manages and processes sound effects with real-time capabilities.

**Key Features**:
- Sound file upload and processing
- Real-time audio effects application
- Sound mixing and composition
- Categorization and search

**API Endpoints**:
```
POST /sounds                   - Upload sound effect
GET  /sounds                   - Search sounds
GET  /sounds/{id}              - Get sound details
GET  /sounds/{id}/stream       - Stream audio
POST /sounds/random            - Get random sounds
POST /sounds/mix               - Create sound mix
```

### 4. Dynamic Music Manager (Port 8004)

**Purpose**: Adaptive music system that responds to game state and scene intensity.

**Key Features**:
- Dynamic composition based on mood/intensity
- Real-time music transitions
- Layer-based music mixing
- Game state integration

**API Endpoints**:
```
GET  /state                    - Get current music state
POST /state                    - Set music state
POST /tracks                   - Upload music track
GET  /tracks                   - List tracks
POST /adaptive/update          - Update adaptive parameters
POST /stream                   - Generate music stream
```

### 5. Voice Integration Layer (Port 8005)

**Purpose**: Integrates voice systems with n8n workflows for automation.

**Key Features**:
- Event-driven workflow triggers
- Content processing automation
- Session management integration
- Recording and transcription workflows

**API Endpoints**:
```
POST /sessions                 - Create voice session
DELETE /sessions/{id}          - End voice session
POST /workflows                - Register workflow
POST /content/process          - Process audio content
GET  /stats                    - Get integration statistics
```

## Installation & Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM
- 50GB+ storage space
- Ports: 80, 443, 3478, 49152-65535 (TURN)

### Quick Start

1. **Clone the Repository**:
```bash
git clone <repository-url>
cd DMlogn8n
```

2. **Deploy the System**:
```bash
./deploy-voice-system.sh deploy
```

3. **Verify Deployment**:
```bash
./deploy-voice-system.sh health
```

4. **Access Services**:
- Voice Chat API: http://localhost:8001
- Sound Effects: http://localhost:8003
- Dynamic Music: http://localhost:8004
- Integration: http://localhost:8005
- N8n Workflows: http://localhost:5678
- Grafana Dashboard: http://localhost:3000

### Environment Configuration

Create `.env` file with following variables:

```bash
# Security
TURN_USERNAME=dmlogn8n
TURN_PASSWORD=your-secure-password-here
N8N_ADMIN_PASSWORD=your-secure-n8n-password
GRAFANA_ADMIN_PASSWORD=your-secure-grafana-password

# External Services (Optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
S3_BUCKET_NAME=dmlogn8n-audio-storage

# Configuration
MAX_PARTICIPANTS_PER_ROOM=20
ENABLE_SPATIAL_AUDIO=true
AUTO_TRANSCRIBE_SESSIONS=true
```

## API Documentation

### Voice Chat Server API

#### Create Room

```http
POST /rooms
Content-Type: application/json

{
  "name": "Dungeon Adventure",
  "description": "Weekly D&D session",
  "max_participants": 8,
  "spatial_audio_enabled": true,
  "ambient_sound": "dungeon_ambient",
  "background_music": "adventure_theme"
}
```

**Response**:
```json
{
  "room": {
    "id": "room-uuid",
    "name": "Dungeon Adventure",
    "participants": [],
    "spatial_audio_enabled": true,
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

#### Join Room (WebSocket)

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/voice/room-uuid');

// Join message
ws.send(JSON.stringify({
  type: "join",
  data: {
    user_id: "user-123",
    username: "DragonSlayer99",
    character_profile: {
      character_id: "dwarf_male",
      name: "Thorin Stonehand"
    },
    voice_settings: {
      push_to_talk: true,
      voice_activation: false,
      input_volume: 1.0
    }
  }
}));
```

#### Update Position

```javascript
ws.send(JSON.stringify({
  type: "position_update",
  position: {
    x: 10.5,
    y: 5.2,
    z: 0.0
  }
}));
```

### Sound Effects Library API

#### Upload Sound Effect

```http
POST /sounds
Content-Type: multipart/form-data

file: [audio file]
name: "Fireball Explosion"
description: "Magical fireball impact sound"
category: "magic"
intensity: 4
tags: ["explosion", "fire", "magic"]
```

#### Search Sounds

```http
GET /sounds?query=explosion&category=magic&limit=10&offset=0
```

**Response**:
```json
{
  "sounds": [
    {
      "id": "sound-uuid",
      "name": "Fireball Explosion",
      "category": "magic",
      "duration": 2.5,
      "tags": ["explosion", "fire", "magic"],
      "waveformData": [0.1, 0.2, ...],
      "spectrumData": [0.5, 0.3, ...]
    }
  ],
  "total": 1
}
```

### Dynamic Music Manager API

#### Set Music State

```http
POST /state
Content-Type: application/json

{
  "mood": "combat",
  "intensity": 5,
  "transition_type": "crossfade",
  "fade_duration": 3.0
}
```

#### Update Adaptive Parameters

```http
POST /adaptive/update
Content-Type: application/json

{
  "in_combat": true,
  "enemy_count": 3,
  "health_percentage": 45,
  "area_type": "dungeon",
  "time_of_day": "night"
}
```

### Integration Layer API

#### Create Voice Session

```http
POST /sessions
Content-Type: application/json

{
  "name": "Session 42 - Dragon's Lair",
  "creator_id": "dm-123",
  "max_participants": 6,
  "auto_record": true,
  "auto_transcribe": true,
  "content_processing": ["transcription", "summarization"],
  "workflow_triggers": ["session-start", "recording-complete"]
}
```

**Response**:
```json
{
  "session_id": "session-uuid",
  "room_id": "room-uuid",
  "websocket_url": "ws://localhost:8001/ws/voice/room-uuid",
  "sfu_url": "ws://localhost:8002/ws/sfu/room-uuid"
}
```

## Client Integration

### JavaScript Client Library

```javascript
import { AudioProcessingPipeline } from './audio_processing_pipeline.js';
import { VoiceChatClient } from './voice-chat-client.js';

class DMlogn8nVoiceClient {
  constructor(options = {}) {
    this.audioPipeline = new AudioProcessingPipeline({
      spatialAudio: options.spatialAudio || true,
      voiceEffects: options.voiceEffects || true,
      pushToTalk: options.pushToTalk || false,
      onAudioLevelChange: options.onAudioLevelChange,
      onVoiceActivityStart: options.onVoiceActivityStart,
      onVoiceActivityStop: options.onVoiceActivityStop
    });

    this.voiceChat = new VoiceChatClient({
      serverUrl: options.serverUrl || 'ws://localhost:8001',
      sfuUrl: options.sfuUrl || 'ws://localhost:8002',
      onParticipantJoined: options.onParticipantJoined,
      onParticipantLeft: options.onParticipantLeft,
      onAudioReceived: options.onAudioReceived
    });

    this.setupEventHandlers();
  }

  async initialize() {
    await this.audioPipeline.initialize();
    await this.voiceChat.connect();
  }

  async joinSession(sessionId, userConfig) {
    // Start audio capture
    await this.audioPipeline.startCapture();

    // Join voice session
    await this.voiceChat.joinRoom(sessionId, userConfig);

    // Set character voice profile
    if (userConfig.characterProfile) {
      this.audioPipeline.setCharacterProfile(userConfig.characterProfile.character_id);
    }
  }

  updatePosition(position) {
    this.voiceChat.updatePosition(position);
    this.audioPipeline.updateListenerPosition(position);
  }

  setPushToTalk(enabled, key = ' ') {
    this.audioPipeline.pushToTalk.enabled = enabled;
    this.audioPipeline.pushToTalk.key = key;
  }

  async startRecording() {
    await this.audioPipeline.startRecording();
  }

  async stopRecording() {
    const recording = await this.audioPipeline.stopRecording();
    return recording;
  }

  playSoundEffect(soundId, options = {}) {
    // Fetch sound from library and play with spatial positioning
    fetch(`/api/sound-effects/${soundId}/stream`)
      .then(response => response.blob())
      .then(blob => {
        const audio = new Audio(URL.createObjectURL(blob));
        if (options.position) {
          this.audioPipeline.createSpatialAudioStream(
            audio.captureStream(),
            soundId,
            options.position
          );
        } else {
          audio.play();
        }
      });
  }

  disconnect() {
    this.voiceChat.disconnect();
    this.audioPipeline.cleanup();
  }

  setupEventHandlers() {
    this.voiceChat.on('participantJoined', (participant) => {
      console.log('Participant joined:', participant.username);
    });

    this.voiceChat.on('participantLeft', (participant) => {
      console.log('Participant left:', participant.username);
    });

    this.audioPipeline.on('voiceActivityStart', () => {
      this.voiceChat.setSpeaking(true);
    });

    this.audioPipeline.on('voiceActivityStop', () => {
      this.voiceChat.setSpeaking(false);
    });
  }
}

// Usage Example
const voiceClient = new DMlogn8nVoiceClient({
  spatialAudio: true,
  voiceEffects: true,
  pushToTalk: true,
  onParticipantJoined: (participant) => {
    updateParticipantList(participant);
  },
  onAudioLevelChange: (level) => {
    updateVolumeMeter(level);
  }
});

await voiceClient.initialize();

await voiceClient.joinSession('session-uuid', {
  user_id: 'user-123',
  username: 'PlayerOne',
  character_profile: {
    character_id: 'elf_male',
    name: 'Legolas Greenleaf'
  },
  voice_settings: {
    push_to_talk: true,
    input_volume: 0.8
  }
});
```

### React Component Example

```jsx
import React, { useState, useEffect, useRef } from 'react';
import { DMlogn8nVoiceClient } from './voice-client';

const VoiceChatPanel = ({ sessionId, user }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [participants, setParticipants] = useState([]);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const voiceClient = useRef(null);

  useEffect(() => {
    const initializeVoice = async () => {
      voiceClient.current = new DMlogn8nVoiceClient({
        onParticipantJoined: (participant) => {
          setParticipants(prev => [...prev, participant]);
        },
        onParticipantLeft: (participant) => {
          setParticipants(prev => prev.filter(p => p.id !== participant.id));
        },
        onAudioLevelChange: (level) => {
          setAudioLevel(level);
        },
        onVoiceActivityStart: () => {
          setIsSpeaking(true);
        },
        onVoiceActivityStop: () => {
          setIsSpeaking(false);
        }
      });

      await voiceClient.current.initialize();

      await voiceClient.current.joinSession(sessionId, {
        user_id: user.id,
        username: user.username,
        character_profile: user.character
      });

      setIsConnected(true);
    };

    initializeVoice();

    return () => {
      if (voiceClient.current) {
        voiceClient.current.disconnect();
      }
    };
  }, [sessionId, user]);

  const handlePositionUpdate = (x, y) => {
    if (voiceClient.current) {
      voiceClient.current.updatePosition({ x, y, z: 0 });
    }
  };

  const handlePushToTalk = (pressed) => {
    if (voiceClient.current) {
      voiceClient.current.setPushToTalk(pressed);
    }
  };

  return (
    <div className="voice-chat-panel">
      <div className="connection-status">
        <span className={`status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? 'Connected' : 'Connecting...'}
        </span>
      </div>

      <div className="participants">
        <h3>Participants ({participants.length})</h3>
        {participants.map(participant => (
          <div key={participant.id} className="participant">
            <span className="username">{participant.username}</span>
            {participant.is_speaking && <span className="speaking-indicator">🔊</span>}
          </div>
        ))}
      </div>

      <div className="audio-controls">
        <div className="volume-meter">
          <div
            className="volume-level"
            style={{ width: `${audioLevel * 100}%` }}
          />
        </div>

        <button
          className={`push-to-talk ${isSpeaking ? 'active' : ''}`}
          onMouseDown={() => handlePushToTalk(true)}
          onMouseUp={() => handlePushToTalk(false)}
          onTouchStart={() => handlePushToTalk(true)}
          onTouchEnd={() => handlePushToTalk(false)}
        >
          Push to Talk
        </button>
      </div>

      <div className="sound-effects">
        <h4>Sound Effects</h4>
        <button onClick={() => voiceClient.current?.playSoundEffect('fireball')}>
          🔥 Fireball
        </button>
        <button onClick={() => voiceClient.current?.playSoundEffect('heal')}>
          💚 Heal
        </button>
        <button onClick={() => voiceClient.current?.playSoundEffect('sword-swing')}>
          ⚔️ Sword
        </button>
      </div>
    </div>
  );
};

export default VoiceChatPanel;
```

## Configuration

### Voice Chat Server Configuration

```yaml
# config/voice-chat.yaml
server:
  host: "0.0.0.0"
  port: 8001
  max_participants_per_room: 20
  enable_spatial_audio: true

redis:
  host: "redis-voice"
  port: 6379
  db: 0

audio:
  sample_rate: 48000
  channels: 1
  bit_rate: 64000
  buffer_size: 960

spatial_audio:
  max_distance: 50.0
  rolloff_factor: 1.0
  reference_distance: 1.0

character_voices:
  dwarf_male:
    pitch_shift: -0.3
    formant_shift: 0.8
    reverb_wetness: 0.2

  elf_female:
    pitch_shift: 0.3
    formant_shift: 1.2
    reverb_wetness: 0.35
    high_pass_cutoff: 150
```

### SFU Server Configuration

```yaml
# config/sfu.yaml
server:
  host: "0.0.0.0"
  port: 8002
  max_concurrent_streams: 100

webrtc:
  ice_servers:
    - urls: "stun:localhost:3478"
    - urls: "turn:localhost:3478"
      username: "dmlogn8n"
      credential: "turn-password"

audio:
  enable_opus_dtx: true
  enable_opus_fec: true
  opus_complexity: 5

performance:
  worker_threads: 4
  max_queue_size: 1000
```

### Sound Effects Library Configuration

```yaml
# config/sound-effects.yaml
library:
  base_path: "/var/lib/dmlogn8n/sounds"
  max_file_size_mb: 100
  supported_formats: ["wav", "mp3", "ogg", "flac"]

processing:
  normalize_audio: true
  target_lufs: -23.0
  trim_silence: true
  generate_waveforms: true

cache:
  max_cache_size_mb: 1024
  cache_duration_hours: 24
```

### Dynamic Music Manager Configuration

```yaml
# config/dynamic-music.yaml
library:
  base_path: "/var/lib/dmlogn8n/music"
  max_concurrent_compositions: 10

adaptive:
  intensity_smoothing: 0.1
  mood_transition_threshold: 0.3
  combat_intensity_multiplier: 1.5

transitions:
  default_duration: 3.0
  default_type: "crossfade"
  max_concurrent_transitions: 2
```

## Monitoring & Troubleshooting

### Health Checks

All services expose health check endpoints:

```bash
# Check individual services
curl http://localhost:8001/  # Voice Chat
curl http://localhost:8002/  # SFU
curl http://localhost:8003/  # Sound Effects
curl http://localhost:8004/  # Dynamic Music
curl http://localhost:8005/  # Integration

# Check overall system
./deploy-voice-system.sh health
```

### Monitoring with Grafana

Access Grafana at `http://localhost:3000` with credentials:
- Username: admin
- Password: (configured during deployment)

**Key Dashboards**:
1. **System Overview**: Overall system health and performance
2. **Voice Chat Metrics**: Room usage, participant counts, audio quality
3. **SFU Performance**: Bandwidth usage, latency, packet loss
4. **Audio Processing**: CPU/memory usage, processing times

### Logging

Logs are stored in `./logs/` directory:

```bash
# View real-time logs
docker-compose -f docker-compose.voice.yml logs -f

# View specific service logs
docker-compose -f docker-compose.voice.yml logs -f voice-chat-server
docker-compose -f docker-compose.voice.yml logs -f voice-sfu-server

# View system logs
tail -f ./logs/voice-chat/voice_chat.log
tail -f ./logs/sfu/voice_sfu.log
```

### Common Issues

#### Audio Quality Problems

**Symptoms**: Choppy audio, high latency, poor quality

**Solutions**:
1. Check network connectivity and bandwidth
2. Verify TURN server configuration
3. Adjust audio quality settings in client
4. Check SFU performance metrics

```bash
# Check SFU performance
curl http://localhost:8002/stats

# Expected response:
{
  "average_latency_ms": 25.5,
  "packet_loss_rate": 0.01,
  "current_bandwidth_kbps": 128.5
}
```

#### Connection Issues

**Symptoms**: Unable to join rooms, WebSocket connection failures

**Solutions**:
1. Verify Nginx proxy configuration
2. Check firewall settings for ports 8001-8005
3. Ensure SSL certificates are valid (if using HTTPS)
4. Review browser console for WebRTC errors

#### Performance Issues

**Symptoms**: High CPU usage, memory leaks, slow response times

**Solutions**:
1. Monitor resource usage with Grafana
2. Check for memory leaks in voice processing
3. Optimize audio buffer sizes
4. Scale services by adding more instances

```bash
# Check resource usage
docker stats

# Scale services
docker-compose -f docker-compose.voice.yml up -d --scale voice-chat-server=3
```

## Security Considerations

### Authentication & Authorization

1. **API Authentication**: Implement JWT-based authentication for all API endpoints
2. **Room Access Control**: Verify user permissions before joining rooms
3. **WebRTC Security**: Use secure TURN servers with valid credentials

### Data Protection

1. **Encryption**: All communication should use HTTPS/WSS
2. **Data Storage**: Encrypt sensitive recordings and user data
3. **Privacy**: Implement data retention policies and user consent

### Network Security

1. **Firewall Configuration**: Only expose necessary ports
2. **Rate Limiting**: Implement rate limiting on API endpoints
3. **DDoS Protection**: Use reverse proxy with DDoS protection

```nginx
# Example Nginx rate limiting
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    server {
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
        }
    }
}
```

## Performance Optimization

### Audio Quality Optimization

1. **Adaptive Bitrate**: Adjust audio quality based on network conditions
2. **Echo Cancellation**: Enable echo cancellation for better audio quality
3. **Noise Suppression**: Implement AI-powered noise reduction

```javascript
// Example adaptive bitrate
const networkQuality = await navigator.connection.downlink;
let audioBitrate = 64000; // Default

if (networkQuality < 1) {
  audioBitrate = 32000; // Reduce for poor connections
} else if (networkQuality > 5) {
  audioBitrate = 128000; // Increase for good connections
}
```

### Scaling Strategies

1. **Horizontal Scaling**: Add more instances of voice servers
2. **Load Balancing**: Use Nginx or similar for load distribution
3. **Geographic Distribution**: Deploy servers in multiple regions

### Caching Strategies

1. **Redis Caching**: Cache frequently accessed data
2. **Audio File Caching**: Cache processed audio files
3. **CDN Integration**: Use CDN for static assets

```yaml
# Redis cache configuration
cache:
  sound_metadata: 24h    # Cache sound metadata for 24 hours
  user_sessions: 2h      # Cache user sessions for 2 hours
  room_data: 1h          # Cache room data for 1 hour
  audio_waveforms: 7d    # Cache waveforms for 7 days
```

---

## Support & Contributing

For technical support or to contribute to the project:

1. **Documentation**: Check the latest documentation at `/docs`
2. **Issues**: Report bugs and feature requests via GitHub Issues
3. **Community**: Join our Discord server for community support
4. **Contributing**: See `CONTRIBUTING.md` for development guidelines

## License

This project is licensed under the MIT License - see the LICENSE file for details.