# Advanced AI Dialogue System for DMlogn8n

A comprehensive, emotionally intelligent, context-aware conversation system designed specifically for D&D campaigns and role-playing games.

## 🎭 Overview

The Advanced AI Dialogue System creates believable, engaging conversations that enhance the storytelling experience in D&D campaigns. It combines emotional intelligence, context awareness, dynamic voice synthesis, and multi-language support to provide immersive NPC interactions.

## ✨ Key Features

### 🧠 Emotional Intelligence Engine
- **Real-time emotion detection and response**: Analyzes text for 8 primary emotions (happiness, sadness, anger, fear, surprise, disgust, trust, anticipation)
- **Mood tracking for NPCs and players**: Maintains emotional state history and calculates mood trajectories
- **Empathy simulation**: Generates empathetic responses based on detected emotions
- **Personality adaptation**: Adapts NPC personalities based on conversation history using the Big Five model
- **Cultural and racial dialogue patterns**: Supports D&D-specific racial patterns (Dwarvish, Elvish, Orcish, etc.)

### 🎯 Context-Aware Conversations
- **Memory of past conversations**: Short-term (50 messages) and long-term (1000 messages) memory
- **Environmental context awareness**: Considers location, time, weather, and atmosphere
- **Relationship dynamics**: Tracks trust, familiarity, and disposition between characters
- **Campaign knowledge integration**: Remembers campaign objectives, discoveries, and world state
- **Real-time world event awareness**: Integrates with world events for dynamic responses

### 🎙️ Dynamic Voice Synthesis
- **Multiple provider support**: ElevenLabs, Google Cloud TTS, Azure, AWS, and local TTS
- **Emotional tone modulation**: Adjusts pitch, speed, and volume based on emotional state
- **Accent and dialect preservation**: Maintains D&D racial accents (Nordic, Elvish, Orcish, Draconic)
- **Age-appropriate voice characteristics**: Young, adult, middle-aged, and old voice profiles
- **Real-time speech generation**: Low-latency synthesis for live gameplay

### 🌍 Multi-Language Support
- **Automatic translation with context preservation**: Translates while maintaining meaning and nuance
- **Cultural nuance understanding**: Adapts responses based on cultural context
- **D&D-specific terminology handling**: Preserves game terms in translation
- **Fantasy language support**: Includes translations for Dwarvish, Elvish, Orcish, and Draconic
- **Real-time translation**: Live translation for multi-language gaming groups

### 📊 Conversation Analytics
- **Sentiment analysis tracking**: Monitors emotional trends and conversation health
- **Relationship strength metrics**: Tracks how relationships evolve over time
- **Dialogue effectiveness scoring**: Measures conversation success and engagement
- **Player engagement monitoring**: Identifies participation patterns and engagement levels

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    API Layer                                    │
├─────────────────────────────────────────────────────────────────┤
│  Emotion Analysis  │  Conversation Mgmt  │  Voice Synthesis   │
├─────────────────────────────────────────────────────────────────┤
│              Context-Aware Conversation Manager                  │
├─────────────────────────────────────────────────────────────────┤
│   Emotional Intelligence Engine  │  Multi-Language Support     │
├─────────────────────────────────────────────────────────────────┤
│              Conversation Analytics Engine                      │
├─────────────────────────────────────────────────────────────────┤
│               System Integration Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  D&D Beyond  │  Roll20  │  Foundry  │  Discord  │  Custom APIs │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Node.js 16+
- MongoDB (for conversation storage)
- Redis (for caching and real-time data)
- Optional: ElevenLabs API key, Google Cloud credentials

### Installation

1. **Clone the repository**
```bash
cd /home/activeloguser/DMlogn8n/advanced-ai-dialogue
```

2. **Install dependencies**
```bash
npm install
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Start the system**
```bash
npm start
```

5. **Verify installation**
```bash
curl http://localhost:3000/health
```

### Basic Usage

```javascript
// Initialize the system
const dialogueSystem = require('./src/index.js');

// Analyze emotion in text
const emotionResult = await dialogueSystem.analyzeEmotion(
  "I'm so excited about this quest!",
  "player_123",
  { race: "elf", environment: "forest" }
);

// Generate context-aware response
const conversation = await dialogueManager.processMessage(
  "conv_abc123",
  "The dragon approaches! What should we do?",
  "player_123"
);

// Synthesize speech with emotion
const audio = await voiceEngine.synthesizeSpeech(
  "By my beard, I'll fight this dragon with honor!",
  { race: "dwarf", gender: "male", age: "old" },
  { anger: 0.8, trust: 0.7 }
);
```

## 🔧 Configuration

### Environment Variables

```bash
# Server Configuration
PORT=3000
NODE_ENV=development
CORS_ORIGIN=http://localhost:3000

# Database Configuration
MONGODB_URI=mongodb://localhost:27017/dmlogn8n-dialogue
REDIS_URL=redis://localhost:6379

# Voice Synthesis
ELEVENLABS_API_KEY=your_elevenlabs_api_key
GOOGLE_CLOUD_TTS_KEY=your_google_cloud_key
AZURE_SPEECH_KEY=your_azure_speech_key

# Translation Services
GOOGLE_TRANSLATE_API_KEY=your_google_translate_key
DEEPL_API_KEY=your_deepl_key

# Integration Services
DND_BEYOND_API_KEY=your_dnd_beyond_key
ROLL20_API_KEY=your_roll20_key
DISCORD_BOT_TOKEN=your_discord_token

# Security
JWT_SECRET=your_jwt_secret
ENCRYPTION_KEY=your_encryption_key
```

### System Configuration

```javascript
const config = {
  emotional: {
    emotionDecayRate: 0.01,
    memoryLimit: 1000,
    empathyThreshold: 0.6,
    adaptationRate: 0.1
  },
  conversation: {
    maxConversations: 100,
    shortTermMemoryLimit: 50,
    longTermMemoryLimit: 1000,
    contextWindowSize: 10
  },
  voice: {
    defaultProvider: 'elevenlabs',
    cacheDirectory: './voice-cache',
    maxCacheSize: 1000,
    quality: 'high'
  },
  translation: {
    defaultProvider: 'google',
    cacheSize: 10000,
    enableCulturalNuance: true
  },
  analytics: {
    dataRetentionDays: 365,
    aggregationInterval: 60000,
    enableRealTimeAnalysis: true
  }
};
```

## 📚 API Documentation

### Core Endpoints

#### Emotion Analysis
```http
POST /api/emotion/analyze
Content-Type: application/json

{
  "text": "I'm feeling excited about this adventure!",
  "speakerId": "player_123",
  "context": {
    "race": "elf",
    "environment": "forest",
    "previousMessages": [...]
  }
}
```

#### Conversation Management
```http
POST /api/conversation/process
Content-Type: application/json

{
  "conversationId": "conv_abc123",
  "message": "The dragon approaches!",
  "speakerId": "player_123",
  "additionalContext": {
    "location": "mountain_pass",
    "urgency": "high"
  }
}
```

#### Voice Synthesis
```http
POST /api/voice/synthesize
Content-Type: application/json

{
  "text": "By my beard, I'll fight with honor!",
  "voiceConfig": {
    "race": "dwarf",
    "gender": "male",
    "age": "old",
    "accent": "nordic"
  },
  "emotionalState": {
    "anger": 0.8,
    "trust": 0.7
  },
  "options": {
    "provider": "elevenlabs",
    "quality": "high"
  }
}
```

#### Translation
```http
POST /api/translation/translate
Content-Type: application/json

{
  "text": "The ancient dragon speaks in Draconic",
  "targetLanguage": "es",
  "sourceLanguage": "en",
  "context": {
    "fantasyLanguage": "draconic",
    "campaign": "dragons_descent"
  }
}
```

### WebSocket Events

#### Real-time Emotion Analysis
```javascript
socket.emit('emotion-analyze', {
  text: "I'm scared of the dark dungeon",
  speakerId: "player_123",
  conversationId: "conv_abc123",
  context: { location: "dungeon" }
});

socket.on('emotion-result', (data) => {
  console.log('Emotion analysis:', data.result);
});
```

#### Real-time Voice Synthesis
```javascript
socket.emit('voice-synthesize', {
  text: "Welcome, travelers!",
  voiceConfig: { race: "elf", gender: "female" },
  emotionalState: { happiness: 0.7 }
});

socket.on('voice-result', (data) => {
  // Play audio data
  const audio = new Audio(`data:audio/mp3;base64,${data.audioBuffer}`);
  audio.play();
});
```

## 🔌 n8n Workflows

The system includes pre-built n8n workflows for automation:

### Emotion Analysis Workflow
- **Trigger**: Webhook on new message
- **Process**: Analyze emotion and generate empathetic responses
- **Output**: Emotional state, suggested responses, analytics data

### Voice Synthesis Workflow
- **Trigger**: API call or WebSocket event
- **Process**: Synthesize speech with emotional modulation
- **Output**: Audio file or streaming data

### Conversation Management Workflow
- **Trigger**: New conversation or message
- **Process**: Context-aware message processing
- **Output**: Response suggestions, context updates, analytics

## 🎭 D&D Integration

### Supported Systems
- **D&D Beyond**: Character sync, inventory management
- **Roll20**: Campaign integration, combat tracking
- **Foundry VTT**: Real-time sync, world state
- **Discord**: Voice chat integration, message handling

### Character Voice Profiles

#### Dwarvish Voices
- **Male**: Deep, gravelly, Nordic accent
- **Female**: Warm, resonant, deliberate speech
- **Common phrases**: "By my beard!", "Stone and steel!", "Honor guides us"

#### Elvish Voices
- **Male**: Melodic, precise, ethereal tone
- **Female**: Crystalline, graceful, flowing speech
- **Common phrases**: "As the stars guide us.", "Nature's wisdom speaks."

#### Orcish Voices
- **Male**: Guttural, forceful, aggressive tone
- **Common phrases**: "Strength above all!", "No surrender!", "For the clan!"

### Fantasy Languages
The system supports translation and synthesis for:
- **Dwarvish**: Run script, resonant tones
- **Elvish**: Elvish script, melodic patterns
- **Draconic**: Ancient, powerful speech
- **Orcish**: Angular script, aggressive patterns

## 📊 Analytics and Monitoring

### Conversation Metrics
- **Engagement scoring**: Participant involvement and interaction quality
- **Emotional tracking**: Sentiment analysis and mood progression
- **Effectiveness measurement**: Goal achievement and communication clarity
- **Relationship dynamics**: Trust and familiarity evolution

### Performance Metrics
- **Response times**: Emotion analysis, voice synthesis, translation
- **Cache hit rates**: Audio cache, translation cache, context cache
- **Error rates**: Failed syntheses, translation errors, API failures
- **Resource usage**: Memory, CPU, storage utilization

### Health Endpoints
```bash
# System health
GET /health

# Detailed metrics
GET /api/analytics/metrics

# Performance data
GET /api/analytics/performance
```

## 🧪 Testing

### Running Tests
```bash
# Unit tests
npm test

# Integration tests
npm run test:integration

# Performance tests
npm run test:performance

# Coverage report
npm run test:coverage
```

### Test Categories
- **Unit Tests**: Individual component functionality
- **Integration Tests**: API endpoints and workflow integration
- **Performance Tests**: Load testing and benchmarking
- **E2E Tests**: Complete conversation flows

## 🛠️ Development

### Project Structure
```
├── src/
│   ├── core/                    # Core engines
│   │   ├── EmotionalIntelligenceEngine.js
│   │   └── ContextAwareConversationManager.js
│   ├── voice/                   # Voice synthesis
│   │   └── DynamicVoiceSynthesisEngine.js
│   ├── translation/            # Multi-language support
│   │   └── MultiLanguageSupportSystem.js
│   ├── analytics/              # Analytics engine
│   │   └── ConversationAnalyticsEngine.js
│   ├── api/                    # REST API
│   │   ├── server.js
│   │   └── routes/
│   ├── integration/            # External system integration
│   │   └── SystemIntegrationLayer.js
│   └── workflows/              # n8n workflows
├── config/                     # Configuration files
├── schemas/                    # JSON schemas
├── docs/                       # Documentation
├── tests/                      # Test files
└── examples/                   # Usage examples
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Code Style
- Use ESLint configuration
- Follow JavaScript Standard Style
- Add JSDoc comments for public methods
- Include error handling for all async operations

## 🔐 Security

### Data Protection
- **Encryption**: Sensitive data encrypted at rest
- **Authentication**: JWT-based API authentication
- **Authorization**: Role-based access control
- **Audit Logging**: All actions logged for security

### API Security
```javascript
// Secure API endpoints
app.use('/api', authMiddleware);
app.use('/api/admin', adminMiddleware);

// Rate limiting
const rateLimit = require('express-rate-limit');
app.use('/api', rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
}));
```

## 📈 Performance Optimization

### Caching Strategy
- **Audio Cache**: LRU cache for synthesized speech
- **Translation Cache**: Cache translations by content hash
- **Context Cache**: Short-term conversation context
- **Emotion Cache**: Emotional state calculations

### Optimization Tips
```javascript
// Enable caching
const cacheOptions = {
  audioCache: { maxSize: 1000, ttl: 3600000 },
  translationCache: { maxSize: 10000, ttl: 86400000 },
  contextCache: { maxSize: 100, ttl: 1800000 }
};

// Batch processing for efficiency
const results = await dialogueSystem.analyzeEmotionBatch([
  { text: "Hello", speakerId: "npc_1" },
  { text: "How are you?", speakerId: "npc_2" }
]);
```

## 🚨 Troubleshooting

### Common Issues

#### Voice Synthesis Fails
```bash
# Check API keys
echo $ELEVENLABS_API_KEY

# Test provider connection
curl -H "xi-api-key: $ELEVENLABS_API_KEY" \
     https://api.elevenlabs.io/v1/voices
```

#### Emotion Analysis Inaccurate
```javascript
// Adjust sensitivity
const emotionalEngine = new EmotionalIntelligenceEngine({
  empathyThreshold: 0.7,  // Increase for more empathy
  adaptationRate: 0.2     // Increase for faster adaptation
});
```

#### High Memory Usage
```javascript
// Reduce cache sizes
const config = {
  audioCache: { maxSize: 500 },     // Reduce from 1000
  conversationMemory: { limit: 500 } // Reduce from 1000
};
```

### Debug Mode
```bash
# Enable debug logging
DEBUG=dialogue:* npm start

# Performance profiling
npm run profile
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Documentation**: [Full API docs](docs/api.md)
- **Examples**: [Usage examples](examples/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Community**: [Discord Server](https://discord.gg/your-server)

## 🗺️ Roadmap

### Version 1.1 (Planned)
- [ ] Enhanced voice customization
- [ ] Additional fantasy languages
- [ ] Mobile app integration
- [ ] Advanced analytics dashboard

### Version 1.2 (Future)
- [ ] Machine learning model fine-tuning
- [ ] Voice cloning capabilities
- [ ] AR/VR integration
- [ ] Advanced combat dialogue

---

Built with ❤️ for the D&D community by the DMlogn8n team.