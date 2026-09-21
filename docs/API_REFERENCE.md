# DMlogn8n Voice System API Reference

## Base URLs

- Voice Chat Server: `http://localhost:8001`
- SFU Server: `http://localhost:8002`
- Sound Effects Library: `http://localhost:8003`
- Dynamic Music Manager: `http://localhost:8004`
- Integration Layer: `http://localhost:8005`

## Authentication

Most endpoints require authentication via Bearer token:

```http
Authorization: Bearer <jwt_token>
```

## Voice Chat Server API

### Rooms

#### List Public Rooms

```http
GET /rooms
```

**Response**:
```json
{
  "rooms": [
    {
      "id": "room-uuid",
      "name": "Dungeon Adventure",
      "description": "Weekly D&D session",
      "max_participants": 8,
      "current_participants": 5,
      "is_public": true,
      "spatial_audio_enabled": true,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### Create Room

```http
POST /rooms
Content-Type: application/json

{
  "name": "string (required)",
  "description": "string (optional)",
  "max_participants": "number (default: 20)",
  "is_public": "boolean (default: true)",
  "password": "string (optional)",
  "spatial_audio_enabled": "boolean (default: true)",
  "max_distance": "number (default: 50.0)",
  "ambient_sound": "string (optional)",
  "background_music": "string (optional)"
}
```

**Response**:
```json
{
  "room": {
    "id": "room-uuid",
    "name": "Dungeon Adventure",
    "description": "Weekly D&D session",
    "max_participants": 8,
    "is_public": true,
    "spatial_audio_enabled": true,
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

#### Get Room Details

```http
GET /rooms/{room_id}
```

**Response**:
```json
{
  "room": {
    "id": "room-uuid",
    "name": "Dungeon Adventure",
    "description": "Weekly D&D session",
    "max_participants": 8,
    "spatial_audio_enabled": true,
    "participants": [
      {
        "id": "participant-uuid",
        "user_id": "user-uuid",
        "username": "DragonSlayer99",
        "character_name": "Thorin Stonehand",
        "position": {"x": 10.5, "y": 5.2, "z": 0.0},
        "is_muted": false,
        "is_deafened": false,
        "is_speaking": false,
        "joined_at": "2024-01-01T12:05:00Z"
      }
    ]
  }
}
```

### Character Profiles

#### Get Character Profiles

```http
GET /character-profiles
```

**Response**:
```json
{
  "profiles": [
    {
      "character_id": "dwarf_male",
      "character_name": "Dwarf Male",
      "voice_effect": "dwarf_deep",
      "pitch_shift": -0.3,
      "formant_shift": 0.8,
      "reverb_wetness": 0.2,
      "low_pass_cutoff": 8000.0,
      "high_pass_cutoff": 100.0,
      "compression_ratio": 1.0,
      "compression_threshold": -20.0
    }
  ]
}
```

### WebSocket Connection

#### Connect to Room

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/voice/{room_id}');

// Join room
ws.send(JSON.stringify({
  "type": "join",
  "data": {
    "user_id": "user-uuid",
    "username": "DragonSlayer99",
    "character_profile": {
      "character_id": "dwarf_male",
      "character_name": "Thorin Stonehand"
    },
    "voice_settings": {
      "input_volume": 1.0,
      "output_volume": 1.0,
      "push_to_talk": false,
      "voice_activation": true,
      "activation_threshold": 0.02,
      "noise_suppression": true,
      "echo_cancellation": true,
      "auto_gain_control": true,
      "quality": "high"
    }
  }
}));
```

#### Update Position

```javascript
ws.send(JSON.stringify({
  "type": "position_update",
  "position": {
    "x": 10.5,
    "y": 5.2,
    "z": 0.0
  }
}));
```

#### Send Audio Packet

```javascript
ws.send(JSON.stringify({
  "type": "audio_packet",
  "packet": {
    "packet_id": "packet-uuid",
    "sender_id": "participant-uuid",
    "room_id": "room-uuid",
    "audio_data": "base64-encoded-audio",
    "sequence_number": 123,
    "position": {"x": 10.5, "y": 5.2, "z": 0.0},
    "is_speaking": true,
    "volume_level": 0.8
  }
}));
```

#### Toggle Mute

```javascript
ws.send(JSON.stringify({
  "type": "mute_toggle"
}));
```

#### Toggle Deafen

```javascript
ws.send(JSON.stringify({
  "type": "deafen_toggle"
}));
```

#### Received Messages

**Participant Joined**:
```json
{
  "type": "participant_joined",
  "participant": {
    "id": "participant-uuid",
    "user_id": "user-uuid",
    "username": "DragonSlayer99",
    "character_name": "Thorin Stonehand"
  }
}
```

**Participant Left**:
```json
{
  "type": "participant_left",
  "participant_id": "participant-uuid"
}
```

**Audio Packet**:
```json
{
  "type": "audio_packet",
  "packet": {
    "sender_id": "participant-uuid",
    "audio_data": "base64-encoded-audio",
    "position": {"x": 10.5, "y": 5.2, "z": 0.0},
    "volume_level": 0.8
  }
}
```

**Position Update**:
```json
{
  "type": "position_update",
  "participant_id": "participant-uuid",
  "position": {"x": 10.5, "y": 5.2, "z": 0.0}
}
```

## SFU Server API

### Session Management

#### Join SFU Session

```http
POST /join
Content-Type: application/json

{
  "participant_id": "participant-uuid",
  "room_id": "room-uuid",
  "offer_sdp": {
    "type": "offer",
    "sdp": "v=0\r\no=- 123456789 2 IN IP4 127.0.0.1\r\n..."
  }
}
```

**Response**:
```json
{
  "answer_sdp": {
    "type": "answer",
    "sdp": "v=0\r\no=- 987654321 2 IN IP4 127.0.0.1\r\n..."
  }
}
```

#### Handle ICE Candidate

```http
POST /ice-candidate
Content-Type: application/json

{
  "participant_id": "participant-uuid",
  "candidate": {
    "candidate": "candidate:1 1 UDP 2130706431 192.168.1.100 54400 typ host",
    "sdpMLineIndex": 0,
    "sdpMid": "0"
  }
}
```

#### Leave SFU Session

```http
DELETE /participants/{participant_id}
```

**Response**:
```json
{
  "status": "ok"
}
```

### Statistics

#### Get SFU Statistics

```http
GET /stats
```

**Response**:
```json
{
  "uptime_seconds": 3600,
  "current_participants": 5,
  "active_tracks": 10,
  "forwarding_tracks": 8,
  "total_packets_forwarded": 1000000,
  "total_bytes_forwarded": 50000000,
  "average_latency_ms": 25.5,
  "peak_concurrent_participants": 8,
  "current_bandwidth_kbps": 128.5,
  "packet_loss_rate": 0.01,
  "cpu_usage_percent": 15.2,
  "memory_usage_mb": 256.7
}
```

### WebSocket Connection

#### Connect to SFU

```javascript
const ws = new WebSocket('ws://localhost:8002/ws/sfu/{room_id}');

// Join session
ws.send(JSON.stringify({
  "type": "join",
  "participant_id": "participant-uuid",
  "offer_sdp": {
    "type": "offer",
    "sdp": "..."
  }
}));
```

#### Send ICE Candidate

```javascript
ws.send(JSON.stringify({
  "type": "ice_candidate",
  "candidate": {
    "candidate": "candidate:1 1 UDP 2130706431 192.168.1.100 54400 typ host",
    "sdpMLineIndex": 0
  }
}));
```

#### Leave Session

```javascript
ws.send(JSON.stringify({
  "type": "leave"
}));
```

## Sound Effects Library API

### Sound Management

#### Upload Sound

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

**Response**:
```json
{
  "sound": {
    "id": "sound-uuid",
    "name": "Fireball Explosion",
    "description": "Magical fireball impact sound",
    "filename": "sound-uuid.wav",
    "duration": 2.5,
    "file_size": 1024000,
    "sample_rate": 48000,
    "channels": 2,
    "format": "wav",
    "category": "magic",
    "intensity": 4,
    "rms_level": 0.75,
    "peak_level": 0.95,
    "waveformData": [0.1, 0.2, 0.15, ...],
    "spectrumData": [0.5, 0.3, 0.2, ...],
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

#### Search Sounds

```http
GET /sounds?query=explosion&category=magic&tags=fire,intensity&limit=10&offset=0
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
      "intensity": 4,
      "tags": ["explosion", "fire", "magic"],
      "waveformData": [0.1, 0.2, ...],
      "spectrumData": [0.5, 0.3, ...]
    }
  ],
  "total": 1
}
```

#### Get Sound Details

```http
GET /sounds/{sound_id}
```

**Response**:
```json
{
  "sound": {
    "id": "sound-uuid",
    "name": "Fireball Explosion",
    "description": "Magical fireball impact sound",
    "filename": "sound-uuid.wav",
    "duration": 2.5,
    "file_size": 1024000,
    "sample_rate": 48000,
    "channels": 2,
    "format": "wav",
    "category": "magic",
    "intensity": 4,
    "tags": ["explosion", "fire", "magic"],
    "rms_level": 0.75,
    "peak_level": 0.95,
    "spectral_centroid": 2500.5,
    "spectral_rolloff": 4000.2,
    "mfcc_features": [0.1, 0.2, ...],
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

#### Stream Sound

```http
GET /sounds/{sound_id}/stream?start_time=0.0&duration=5.0
```

**Response**: Audio file stream (audio/wav)

#### Get Random Sounds

```http
POST /sounds/random
Content-Type: application/json

{
  "category": "magic",
  "count": 3,
  "exclude_ids": ["sound-uuid-1", "sound-uuid-2"]
}
```

**Response**:
```json
{
  "sounds": [
    {
      "id": "sound-uuid-3",
      "name": "Lightning Strike",
      "category": "magic",
      "duration": 3.2
    }
  ]
}
```

### Sound Mixing

#### Create Sound Mix

```http
POST /sounds/mix
Content-Type: application/json

{
  "sound_ids": ["sound-uuid-1", "sound-uuid-2"],
  "name": "Combat Mix",
  "description": "Battle sounds combination",
  "config": {
    "0": {
      "volume": 0.8,
      "start_time": 0.0,
      "pan": -0.5
    },
    "1": {
      "volume": 0.6,
      "start_time": 1.5,
      "pan": 0.3
    }
  }
}
```

**Response**:
```json
{
  "mix_id": "mix-uuid"
}
```

### Real-time Effects

#### Apply Effects

```http
POST /sounds/{sound_id}/effects
Content-Type: application/json

{
  "pitch_shift": 2.0,
  "time_stretch": 1.2,
  "reverb": {
    "wetness": 0.3,
    "room_size": 0.5
  },
  "filter": {
    "type": "lowpass",
    "cutoff": 1000,
    "order": 5
  },
  "volume": 0.8
}
```

**Response**: Processed audio file stream (audio/wav)

### Statistics

#### Get Library Statistics

```http
GET /stats
```

**Response**:
```json
{
  "total_sounds": 150,
  "total_duration": 3600.0,
  "total_size_mb": 1024.5,
  "category_counts": {
    "magic": 45,
    "combat": 30,
    "ambient": 25,
    "nature": 20,
    "creatures": 30
  },
  "processing_queue_size": 5,
  "cache_hits": 1250,
  "cache_misses": 150
}
```

## Dynamic Music Manager API

### Music State

#### Get Current State

```http
GET /state
```

**Response**:
```json
{
  "mood": "combat",
  "intensity": 5,
  "tempo": 140.0,
  "active_tracks": ["track-uuid-1", "track-uuid-2"],
  "active_layers": {
    "layer-uuid-1": 0.8,
    "layer-uuid-2": 0.6
  },
  "volume": 1.0,
  "is_transitioning": false,
  "transition_progress": 1.0,
  "performance_stats": {
    "transitions_completed": 25,
    "average_transition_time": 2.5,
    "active_layers_count": 3,
    "cpu_usage": 10.2,
    "memory_usage_mb": 128.5
  }
}
```

#### Set Music State

```http
POST /state
Content-Type: application/json

{
  "mood": "combat",
  "intensity": 5,
  "transition_type": "crossfade",
  "fade_duration": 3.0,
  "target_tracks": ["track-uuid-1", "track-uuid-2"]
}
```

**Response**:
```json
{
  "status": "success"
}
```

### Music Tracks

#### Upload Track

```http
POST /tracks
Content-Type: multipart/form-data

file: [audio file]
name: "Battle Theme"
mood: "combat"
intensity: 5
loops: true
loop_start: 0.0
tags: ["epic", "orchestral"]
```

**Response**:
```json
{
  "track": {
    "id": "track-uuid",
    "name": "Battle Theme",
    "filename": "track-uuid.wav",
    "duration": 180.5,
    "mood": "combat",
    "intensity": 5,
    "tempo": 140.0,
    "key": "C minor",
    "time_signature": "4/4",
    "loops": true,
    "loop_start": 0.0,
    "beat_times": [0.0, 0.43, 0.86, ...]
  }
}
```

#### List Tracks

```http
GET /tracks
```

**Response**:
```json
{
  "tracks": [
    {
      "id": "track-uuid",
      "name": "Battle Theme",
      "mood": "combat",
      "intensity": 5,
      "duration": 180.5,
      "tempo": 140.0
    }
  ]
}
```

### Adaptive Music

#### Update Adaptive Parameters

```http
POST /adaptive/update
Content-Type: application/json

{
  "in_combat": true,
  "enemy_count": 3,
  "enemy_type": "boss",
  "is_exploring": false,
  "in_dialogue": false,
  "dialogue_type": "serious",
  "health_percentage": 45,
  "time_of_day": "night",
  "area_type": "dungeon",
  "scene_id": "scene-uuid"
}
```

**Response**:
```json
{
  "status": "success"
}
```

### Music Streaming

#### Generate Music Stream

```http
POST /stream?duration=30.0
Content-Type: application/json
```

**Response**: Mixed audio stream (audio/wav)

### Music Cues

#### Trigger Music Cue

```http
POST /cues/{cue_id}/trigger
Content-Type: application/json

{
  "context": {
    "scene_id": "scene-uuid",
    "player_health": 75,
    "enemy_presence": true
  }
}
```

**Response**:
```json
{
  "status": "success"
}
```

## Integration Layer API

### Voice Sessions

#### Create Voice Session

```http
POST /sessions
Content-Type: application/json

{
  "name": "Session 42 - Dragon's Lair",
  "description": "Epic dragon battle session",
  "creator_id": "dm-uuid",
  "max_participants": 6,
  "spatial_audio": true,
  "auto_record": true,
  "auto_transcribe": true,
  "content_processing": ["transcription", "summarization"],
  "workflow_triggers": ["session-start", "recording-complete"],
  "ambient_sound": "cave_ambient",
  "background_music": "dungeon_theme"
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

#### End Voice Session

```http
DELETE /sessions/{session_id}
```

**Response**:
```json
{
  "status": "success",
  "session_summary": {
    "session_id": "session-uuid",
    "name": "Session 42 - Dragon's Lair",
    "duration_seconds": 7200,
    "participant_count": 6,
    "recording_count": 3,
    "event_count": 45
  }
}
```

#### Get Session Details

```http
GET /sessions/{session_id}
```

**Response**:
```json
{
  "session_id": "session-uuid",
  "name": "Session 42 - Dragon's Lair",
  "created_at": "2024-01-01T19:00:00Z",
  "creator_id": "dm-uuid",
  "participants": [
    {
      "participant_id": "participant-uuid",
      "user_id": "user-uuid",
      "username": "DragonSlayer99",
      "joined_at": "2024-01-01T19:05:00Z",
      "duration_seconds": 3600
    }
  ],
  "recordings": [
    {
      "recording_id": "recording-uuid",
      "started_at": "2024-01-01T19:10:00Z",
      "duration_seconds": 1800,
      "file_size": 10240000
    }
  ],
  "events": [
    {
      "event_id": "event-uuid",
      "event_type": "participant_joined",
      "timestamp": "2024-01-01T19:05:00Z",
      "data": {}
    }
  ]
}
```

### Workflow Management

#### Register Workflow

```http
POST /workflows
Content-Type: application/json

{
  "name": "Session Recording Processor",
  "description": "Process session recordings for content creation",
  "trigger_type": "recording_complete",
  "trigger_conditions": {
    "session_type": "recorded",
    "min_duration": 300
  },
  "n8n_workflow_id": "n8n-workflow-uuid",
  "n8n_webhook_url": "http://n8n:5678/webhook/recording-processor",
  "active": true,
  "priority": 1,
  "retry_count": 3,
  "timeout_seconds": 600
}
```

**Response**:
```json
{
  "workflow": {
    "workflow_id": "workflow-uuid",
    "name": "Session Recording Processor",
    "trigger_type": "recording_complete",
    "active": true,
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

#### List Workflows

```http
GET /workflows
```

**Response**:
```json
{
  "workflows": [
    {
      "workflow_id": "workflow-uuid",
      "name": "Session Recording Processor",
      "trigger_type": "recording_complete",
      "active": true,
      "trigger_count": 15,
      "last_triggered": "2024-01-01T18:30:00Z"
    }
  ]
}
```

#### Manually Trigger Workflow

```http
POST /workflows/{workflow_id}/trigger
Content-Type: application/json

{
  "trigger_data": {
    "manual_trigger": true,
    "user_id": "dm-uuid"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "result": {
    "workflow_id": "workflow-uuid",
    "execution_id": "execution-uuid",
    "status": "running"
  }
}
```

### Content Processing

#### Process Audio Content

```http
POST /content/process
Content-Type: application/json

{
  "session_id": "session-uuid",
  "processing_type": "transcription",
  "input_data": {
    "recording_files": ["recording-uuid-1", "recording-uuid-2"],
    "participants": ["user-uuid-1", "user-uuid-2"],
    "languages": ["en"]
  }
}
```

**Response**:
```json
{
  "job_id": "job-uuid"
}
```

#### Get Processing Job Status

```http
GET /content/jobs/{job_id}
```

**Response**:
```json
{
  "job_id": "job-uuid",
  "status": "completed",
  "progress": 1.0,
  "result_data": {
    "transcription": "Full session transcription text...",
    "speaker_labels": [
      {"timestamp": 0, "speaker": "DragonSlayer99", "text": "I attack the dragon!"},
      {"timestamp": 5, "speaker": "DungeonMaster", "text": "Roll for initiative."}
    ],
    "summary": "The party engaged in an epic battle with a red dragon..."
  },
  "created_at": "2024-01-01T20:00:00Z",
  "started_at": "2024-01-01T20:00:05Z",
  "completed_at": "2024-01-01T20:05:30Z"
}
```

#### Content Processing Callback

```http
POST /content/callback/{job_id}
Content-Type: application/json

{
  "result_data": {
    "transcription": "Processed transcription text...",
    "summary": "Session summary...",
    "highlights": ["Epic moment 1", "Funny quote 2"]
  },
  "processing_time": 325.5
}
```

**Response**:
```json
{
  "status": "success"
}
```

### Statistics

#### Get Integration Statistics

```http
GET /stats
```

**Response**:
```json
{
  "events_processed": 1250,
  "workflows_triggered": 85,
  "content_jobs_completed": 42,
  "average_processing_time": 285.5,
  "error_count": 3,
  "active_sessions": 5,
  "pending_events": 2,
  "active_workflows": 12,
  "processing_jobs": 8
}
```

## Error Handling

All APIs return standard HTTP status codes:

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": {
      "field": "name",
      "issue": "This field is required"
    }
  }
}
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- Voice Chat API: 100 requests/minute per IP
- Sound Effects API: 50 uploads/hour per user
- Music API: 200 requests/minute per IP
- Integration API: 1000 requests/minute per IP

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## WebSocket Connection Limits

- Max concurrent connections per IP: 10
- Max participants per room: 20 (configurable)
- Connection timeout: 30 minutes
- Max message size: 64KB

## Data Formats

### Date/Time Format

All timestamps use ISO 8601 format:
```
2024-01-01T12:00:00Z
```

### Audio Formats

Supported audio formats:
- WAV (recommended for highest quality)
- MP3 (for compressed audio)
- OGG (for web optimization)
- FLAC (for lossless compression)

### Position Format

3D positions use floating-point coordinates:
```json
{
  "x": 10.5,
  "y": 5.2,
  "z": 0.0
}
```

Units are in meters, with Z representing height/elevation.