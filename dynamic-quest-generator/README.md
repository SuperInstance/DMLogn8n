# Dynamic Quest Generator for DMlogn8n

An AI-driven, personalized quest content generation system that creates dynamic, adaptive quests for tabletop RPG campaigns and digital game experiences.

## 🎯 Features

### Quest Generation Engine
- **AI-Driven Story Creation**: Uses advanced AI models to generate immersive, contextual storylines
- **Dynamic Objectives**: Generates quests with multiple objectives and branching paths
- **Adaptive Difficulty**: Automatically scales quest difficulty based on player skill and performance
- **Player Choice Integration**: Supports branching narratives with meaningful consequences
- **Multi-Branching Stories**: Creates complex questlines with multiple outcomes

### Quest Types
- **Main Story Quests**: Epic, campaign-defining adventures
- **Side Quests**: Optional adventures for character development
- **Daily & Weekly Quests**: Repeatable content with rotating objectives
- **Event-Based Quests**: Special limited-time quests tied to world events
- **Player-Generated Quests**: Quests created by players for others
- **Guild & Group Quests**: Cooperative challenges for parties

### Context Awareness
- **Player History Analysis**: Learns from completed quests and player preferences
- **Campaign World State**: Considers current world events and timeline
- **Character Progression**: Adapts to character level, class, and abilities
- **Party Composition**: Balances content based on group dynamics
- **Time & Location Context**: Creates relevant content based on setting

### Quest Customization
- **Personalized Objectives**: Tailors goals to player playstyle and preferences
- **Custom Rewards**: Generates appropriate loot and experience rewards
- **Difficulty Adjustment**: Scales challenges to match player skill level
- **Story Relevance**: Ensures content fits within campaign narrative
- **Moral Choices**: Includes ethical decisions with lasting consequences

### Quest Management
- **Progress Tracking**: Real-time quest progress monitoring
- **Dynamic Updates**: Quests evolve based on player actions
- **Social Features**: Share quests with friends and guild members
- **Achievement Integration**: Unlock rewards through quest completion
- **Replay & Alternate Paths**: Multiple ways to complete objectives

## 🏗️ Architecture

```
dynamic-quest-generator/
├── src/
│   ├── api/                    # REST API endpoints
│   │   ├── questRoutes.js     # Quest management routes
│   │   ├── playerRoutes.js    # Player management routes
│   │   └── index.js          # API server setup
│   ├── core/                  # Core quest generation logic
│   │   ├── QuestGenerationEngine.js  # Main quest generator
│   │   ├── QuestTemplateEngine.js    # Template-based generation
│   │   ├── DifficultyScaler.js       # Difficulty scaling system
│   │   └── RewardCalculator.js       # Reward calculation system
│   ├── ai/                    # AI integration
│   │   └── AIQuestGenerator.js       # OpenAI integration
│   ├── context/               # Player context analysis
│   │   └── ContextAnalyzer.js        # Player behavior analysis
│   ├── management/            # Quest lifecycle management
│   │   └── QuestManager.js           # Quest state management
│   ├── database/              # Database models and connection
│   │   ├── models/           # Mongoose schemas
│   │   │   ├── Quest.js     # Quest model
│   │   │   ├── Player.js    # Player model
│   │   │   └── index.js     # Model exports
│   │   ├── connection.js     # Database connection
│   │   └── index.js         # Database manager
│   ├── n8n-workflows/        # n8n automation workflows
│   │   ├── quest-generation-workflow.json
│   │   └── quest-progress-tracking-workflow.json
│   └── index.js              # Application entry point
├── config/
│   └── quest-config.js       # Quest configuration constants
├── docs/                     # Documentation
├── tests/                    # Test files
└── scripts/                  # Utility scripts
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18.0.0 or higher
- MongoDB 4.4 or higher
- OpenAI API key (for AI generation)
- n8n instance (for workflow automation)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd DMlogn8n/dynamic-quest-generator
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your configuration:
   ```env
   # Server Configuration
   PORT=3001
   NODE_ENV=development
   MONGODB_URI=mongodb://localhost:27017/dmlogn8n-quests

   # AI Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4-turbo-preview
   AI_TEMPERATURE=0.7
   AI_MAX_TOKENS=4000

   # n8n Integration
   N8N_WEBHOOK_URL=http://localhost:5678/webhook
   N8N_API_KEY=your_n8n_api_key

   # Security
   JWT_SECRET=your_jwt_secret_here
   CORS_ORIGIN=http://localhost:3000
   ```

4. **Start MongoDB**
   ```bash
   mongod
   ```

5. **Start the application**
   ```bash
   npm start
   ```

The API will be available at `http://localhost:3001`

## 📚 API Documentation

### Quest Endpoints

#### Generate a Quest
```http
POST /api/quests/generate
Content-Type: application/json

{
  "playerId": "player_id_here",
  "questType": "side_quest",
  "category": "combat",
  "difficulty": 3,
  "personalized": true,
  "forceAI": false
}
```

#### Get Player's Active Quests
```http
GET /api/quests/player/:playerId/active
```

#### Update Quest Progress
```http
POST /api/quests/:questId/progress
Content-Type: application/json

{
  "playerId": "player_id_here",
  "objectiveId": "obj_1",
  "progress": 5,
  "data": {
    "timeSpent": 1200000,
    "location": "forest_area"
  }
}
```

#### Complete a Quest
```http
POST /api/quests/:questId/complete
Content-Type: application/json

{
  "playerId": "player_id_here",
  "rating": 5,
  "feedback": "Great quest!",
  "choice": "peaceful_resolution"
}
```

### Player Endpoints

#### Create a Player
```http
POST /api/players
Content-Type: application/json

{
  "userId": "user_123",
  "username": "DragonSlayer42",
  "email": "player@example.com",
  "password": "securepassword",
  "character": {
    "name": "Aragorn",
    "class": "warrior",
    "race": "human",
    "background": "noble"
  }
}
```

#### Get Quest Recommendations
```http
GET /api/players/:playerId/quests/recommendations?count=5
```

#### Update Player Preferences
```http
POST /api/players/:playerId/preferences
Content-Type: application/json

{
  "types": {
    "combat": 0.8,
    "exploration": 0.6,
    "social": 0.3,
    "mystery": 0.7,
    "crafting": 0.2
  },
  "difficulty": {
    "preferred": 4,
    "adaptive": true
  },
  "questLength": "medium",
  "playStyle": "small_group"
}
```

## 🔧 Configuration

### Quest Types
```javascript
export const QUEST_TYPES = {
  MAIN_STORY: 'main_story',
  SIDE_QUEST: 'side_quest',
  DAILY: 'daily',
  WEEKLY: 'weekly',
  EVENT: 'event',
  PLAYER_GENERATED: 'player_generated',
  GUILD: 'guild',
  RAID: 'raid',
  TUTORIAL: 'tutorial',
  HIDDEN: 'hidden'
}
```

### Quest Categories
```javascript
export const CATEGORIES = {
  COMBAT: 'combat',
  EXPLORATION: 'exploration',
  SOCIAL: 'social',
  CRAFTING: 'crafting',
  MYSTERY: 'mystery',
  COLLECTION: 'collection',
  ESCORT: 'escort',
  DELIVERY: 'delivery',
  BOSS_BATTLE: 'boss_battle',
  DUNGEON: 'dungeon'
}
```

### Difficulty Levels
- **1 (Trivial)**: Very simple, tutorial-style content
- **2 (Easy)**: Straightforward challenges for beginners
- **3 (Normal)**: Balanced content for average players
- **4 (Hard)**: Challenging content requiring strategy
- **5 (Expert)**: Difficult content for experienced players
- **6 (Legendary)**: Very difficult, epic challenges
- **7 (Mythic)**: Extremely difficult, legendary content

## 🤖 AI Integration

The system uses OpenAI's GPT models for quest generation:

### AI Quest Generation Features
- **Dynamic Storytelling**: Creates unique narratives based on context
- **Character Dialogue**: Generates realistic NPC conversations
- **World Building**: Creates consistent lore and settings
- **Branching Narratives**: Designs multiple story paths
- **Adaptive Content**: Adjusts complexity based on player skill

### AI Prompt Engineering
The system uses carefully engineered prompts that include:
- Player context and preferences
- Quest requirements and constraints
- World state and campaign lore
- Difficulty and length parameters
- Safety and content guidelines

## 🔄 n8n Workflow Integration

### Quest Generation Workflow
- **Trigger**: Webhook receives quest generation request
- **Process**: AI or template-based quest creation
- **Validation**: Ensures quest meets quality standards
- **Storage**: Saves quest to database
- **Notification**: Alerts player of new quest

### Progress Tracking Workflow
- **Trigger**: Player updates quest progress
- **Validation**: Verifies progress updates are valid
- **State Management**: Updates quest and player states
- **Rewards**: Calculates and distributes rewards
- **Analytics**: Logs performance data

## 📊 Analytics & Metrics

### Quest Analytics
- Generation success rates
- AI vs template usage
- Player engagement metrics
- Completion rates by difficulty
- Average completion times

### Player Analytics
- Quest completion patterns
- Preference tracking
- Performance trends
- Skill progression
- Social interaction data

## 🛠️ Development

### Running Tests
```bash
npm test
```

### Code Quality
```bash
npm run lint
```

### Building for Production
```bash
npm run build
```

### Database Operations
```bash
# Migrate database
npm run migrate

# Seed database with sample data
npm run seed

# Clear all collections (development only)
npm run clean
```

## 🔒 Security Features

- **Input Validation**: Comprehensive validation of all inputs
- **SQL Injection Prevention**: Using parameterized queries
- **XSS Protection**: Content Security Policy headers
- **Rate Limiting**: Prevents abuse of API endpoints
- **Authentication**: JWT-based player authentication
- **Authorization**: Role-based access control

## 📈 Performance Optimizations

- **Database Indexing**: Optimized queries for common operations
- **Caching**: Redis-based caching for frequently accessed data
- **Connection Pooling**: Efficient database connection management
- **Async Operations**: Non-blocking processing throughout
- **Lazy Loading**: On-demand loading of related data

## 🐛 Troubleshooting

### Common Issues

**Quest Generation Fails**
- Check OpenAI API key is valid
- Verify internet connectivity
- Check API rate limits
- Review error logs for specific issues

**Database Connection Issues**
- Verify MongoDB is running
- Check connection string in .env
- Ensure proper network access
- Review MongoDB logs

**n8n Integration Problems**
- Verify webhook URLs are accessible
- Check API keys and authentication
- Review n8n workflow logs
- Test individual workflow nodes

### Debug Mode
Enable debug logging by setting:
```env
LOG_LEVEL=debug
NODE_ENV=development
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for providing the AI models that power quest generation
- n8n for the workflow automation platform
- MongoDB for the flexible database solution
- The RPG community for inspiration and feedback

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation in the `/docs` folder
- Review the FAQ for common questions
- Join our Discord community (link in repository)

---

**Dynamic Quest Generator** - Creating infinite adventures, one quest at a time. 🎲✨