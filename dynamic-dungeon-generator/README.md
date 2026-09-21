# Dynamic Dungeon Generator for DMlogn8n

A comprehensive procedural dungeon generation system that creates infinite, unique dungeon experiences for tabletop RPG campaigns. Built with advanced algorithms, environmental storytelling, and seamless n8n integration.

## 🏰 Features

### Procedural Generation
- **Multiple Algorithms**: Cellular Automata, Binary Space Partitioning (BSP), Room-Corridor, and Organic Growth
- **Theme-Based Generation**: 20+ unique themes including Undead Crypts, Dragon Lairs, Wizard Towers, and more
- **Difficulty Scaling**: Adaptive difficulty that scales with player level
- **Multi-Floor Dungeons**: Complex multi-level dungeons with escalating challenges
- **Dynamic Trap Placement**: Intelligent trap and puzzle placement

### Environmental Variety
- **20+ Biome Types**: Each with unique properties and characteristics
- **Interactive Environments**: Destructible elements and interactive objects
- **Dynamic Lighting**: Real-time lighting and visibility systems
- **Weather Effects**: Environmental weather and atmospheric effects
- **Secret Areas**: Hidden passages and secret rooms

### Content Population
- **Intelligent Enemy Placement**: Smart enemy group composition and placement
- **Boss Encounters**: Unique boss mechanics and encounters
- **Themed Loot Distribution**: Contextually appropriate treasure rewards
- **Environmental Storytelling**: Narrative elements through dungeon placement
- **Dynamic Events**: Random encounters and events

### Customization Tools
- **DM Manual Override**: Complete control for dungeon masters
- **Template System**: Quick generation templates
- **Custom Content Import**: Import custom tiles and objects
- **Rule Variants**: House rules and custom rule sets
- **Export/Import**: Share dungeon designs

### Special Features
- **Time-Based Evolution**: Dungeons that evolve over time
- **Player Choice-Driven**: Dynamic path changes based on player decisions
- **Dynamic Difficulty**: Real-time difficulty adjustment
- **Social Creation**: Collaborative dungeon creation
- **Challenge Modes**: Speedrun and challenge modes

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd DMlogn8n/dynamic-dungeon-generator

# Install dependencies
npm install

# Start the server
npm start
```

### Basic Usage

```javascript
const DungeonGenerator = require('./src/core/DungeonGenerator');

// Create generator instance
const generator = new DungeonGenerator();

// Generate a dungeon
const dungeon = await generator.generate({
  algorithm: 'roomCorridor',
  theme: 'classic',
  width: 50,
  height: 50,
  floors: 1,
  difficulty: 1,
  playerLevel: 1
});

console.log('Generated dungeon:', dungeon.id);
```

### API Usage

```bash
# Generate a new dungeon
curl -X POST http://localhost:3001/api/dungeons/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "algorithm": "roomCorridor",
    "theme": "classic",
    "width": 50,
    "height": 50,
    "floors": 1,
    "difficulty": 1,
    "playerLevel": 1
  }'

# Get all dungeons
curl http://localhost:3001/api/dungeons

# Get specific dungeon
curl http://localhost:3001/api/dungeons/{dungeonId}

# Visualize dungeon floor
curl http://localhost:3001/api/dungeons/{dungeonId}/visualize/0?format=ascii
```

## 🎯 Algorithms

### Cellular Automata
Creates organic, cave-like dungeons using cellular automata rules. Perfect for natural caverns and underground systems.

**Key Features:**
- Organic, flowing layouts
- Natural cave formations
- Suitable for underground environments
- Creates interconnected cave systems

### Binary Space Partitioning (BSP)
Generates structured, room-based dungeons through recursive subdivision. Ideal for traditional dungeons with clear room layouts.

**Key Features:**
- Structured room layouts
- Hierarchical organization
- Predictable patterns
- Good for traditional dungeons

### Room-Corridor
Creates classic dungeons with separate rooms connected by corridors. The most traditional dungeon generation method.

**Key Features:**
- Traditional room-and-corridor layouts
- Flexible room sizes
- Multiple connection patterns
- Classic dungeon feel

### Organic Growth
Simulates natural growth patterns to create flowing, dungeon-like structures. Great for magical or living dungeons.

**Key Features:**
- Natural growth patterns
- Flowing, organic layouts
- Dynamic expansion
- Unique formations

## 🎨 Themes

### Traditional Themes
- **Classic**: Traditional stone dungeon with torches
- **Dwarven Mines**: Underground mining caves with dwarven craftsmanship
- **Elven Sanctuary**: Elegant elven underground sanctuaries
- **Abandoned Temple**: Forgotten religious temples

### Supernatural Themes
- **Undead Crypt**: Haunted burial crypts filled with undead
- **Shadow Realm**: Dark, shadowy dimensions
- **Fey Wild**: Magical, unpredictable fey realms
- **Infernal Portal**: Demonic and hellish environments

### Elemental Themes
- **Dragon Lair**: Massive volcanic caverns for dragons
- **Ice Cavern**: Frozen underground caverns
- **Volcanic Lair**: Lava-filled volcanic dungeons
- **Swamp Cave**: Murky, water-filled caves

### Magical Themes
- **Wizard Tower**: Magical towers filled with arcane wonders
- **Crystal Caves**: Dazzling caves filled with crystals
- **Ancient Library**: Forgotten libraries of knowledge

### Creature Themes
- **Goblin Warren**: Maze-like goblin habitats
- **Living Maze**: Biological, living dungeons
- **Poison Garden**: Toxic, dangerous environments

## 🔧 Configuration

### Server Configuration

```json
{
  "server": {
    "port": 3001,
    "host": "localhost"
  },
  "generation": {
    "defaultAlgorithm": "roomCorridor",
    "defaultTheme": "classic",
    "maxWidth": 200,
    "maxHeight": 200,
    "maxFloors": 10
  }
}
```

### Algorithm Parameters

```json
{
  "algorithms": {
    "roomCorridor": {
      "roomCount": { "min": 8, "max": 20 },
      "roomSize": { "min": 4, "max": 12 },
      "corridorWidth": 1,
      "loopProbability": 0.2,
      "deadEndProbability": 0.1
    },
    "cellular": {
      "initialFillProbability": 0.45,
      "birthLimit": 4,
      "deathLimit": 3,
      "iterations": 6
    }
  }
}
```

## 🔌 n8n Integration

### Available Workflows

1. **Dungeon Generation Workflow**: Automated dungeon generation with validation
2. **Dungeon Monitoring Workflow**: System health monitoring and alerting
3. **DM Dashboard Integration**: Integration with Dungeon Master dashboard

### Importing Workflows

1. Open n8n workflow editor
2. Click "Import from file"
3. Select workflow files from `/workflows/` directory
4. Configure webhook URLs and API endpoints

### Webhook Endpoints

- `POST /webhook/dungeon-generate` - Generate new dungeon
- `POST /webhook/dm-dashboard` - DM dashboard operations
- `POST /webhook/dungeon-monitor` - System monitoring

## 📚 API Documentation

### Endpoints

#### Dungeons
- `GET /api/dungeons` - List all dungeons
- `POST /api/dungeons/generate` - Generate new dungeon
- `GET /api/dungeons/:id` - Get specific dungeon
- `POST /api/dungeons/:id/modify` - Modify dungeon
- `DELETE /api/dungeons/:id` - Delete dungeon
- `GET /api/dungeons/:id/floor/:floorIndex` - Get floor
- `GET /api/dungeons/:id/visualize/:floorIndex` - Visualize floor

#### Themes
- `GET /api/themes` - List all themes
- `GET /api/themes/:themeId` - Get theme details

#### Algorithms
- `GET /api/algorithms` - List algorithms
- `GET /api/algorithms/:algorithmId` - Get algorithm info

### Response Format

```json
{
  "success": true,
  "dungeon": {
    "id": "unique-dungeon-id",
    "metadata": {
      "theme": "classic",
      "difficulty": 1,
      "playerLevel": 1,
      "createdAt": "2024-01-01T00:00:00.000Z"
    },
    "dimensions": {
      "width": 50,
      "height": 50,
      "floors": 1
    },
    "statistics": {
      "totalRooms": 8,
      "totalEnemies": 12,
      "totalLoot": 6,
      "totalTraps": 4
    },
    "floors": [...]
  }
}
```

## 🎮 Integration with DMlogn8n Systems

### Combat System Integration
```javascript
// Prepare combat encounters
const combatData = {
  dungeonId: dungeon.id,
  enemies: dungeon.floors.flatMap(floor => floor.spawns),
  bosses: dungeon.floors.flatMap(floor => floor.bosses),
  difficulty: dungeon.metadata.difficulty
};

// Send to combat system
await fetch('http://localhost:3002/api/combat/prepare', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(combatData)
});
```

### Quest Generator Integration
```javascript
// Generate quests based on dungeon
const questData = {
  dungeonId: dungeon.id,
  theme: dungeon.metadata.theme,
  difficulty: dungeon.metadata.difficulty,
  rooms: dungeon.statistics.totalRooms,
  floors: dungeon.dimensions.floors
};

// Send to quest generator
await fetch('http://localhost:3003/api/quests/generate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(questData)
});
```

### World State Integration
```javascript
// Update world state
const worldUpdate = {
  type: 'dungeon_created',
  dungeonId: dungeon.id,
  theme: dungeon.metadata.theme,
  difficulty: dungeon.metadata.difficulty,
  location: { x: 0, y: 0, z: 0 }
};

// Send to world state manager
await fetch('http://localhost:3004/api/world/update', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(worldUpdate)
});
```

## 🛠️ Customization

### Creating Custom Themes

```javascript
class CustomTheme {
  constructor() {
    this.name = 'My Custom Theme';
    this.description = 'A custom dungeon theme';
    this.difficulty = 2;
    this.environment = 'custom';
  }

  get tileMapping() {
    return {
      wall: 'custom_wall',
      floor: 'custom_floor',
      door: 'custom_door',
      special: [
        {
          tile: 'special_tile',
          probability: 0.1,
          pattern: { type: 'random' }
        }
      ]
    };
  }

  get lighting() {
    return {
      brightness: 0.6,
      color: '#ffcc00',
      sources: [...]
    };
  }
}
```

### Creating Custom Algorithms

```javascript
class CustomAlgorithm extends BaseAlgorithm {
  async generate(params) {
    // Implementation here
    return {
      grid: generatedGrid,
      rooms: rooms,
      corridors: corridors,
      features: features
    };
  }
}
```

## 📊 Performance

### Benchmarks
- **Small Dungeon** (50x50): ~500ms
- **Medium Dungeon** (100x100): ~2s
- **Large Dungeon** (200x200): ~8s

### Optimization Tips
- Use appropriate dungeon sizes
- Limit complexity for real-time generation
- Enable caching for repeated dungeons
- Use WebSocket for real-time updates

## 🐛 Troubleshooting

### Common Issues

1. **Slow Generation**
   - Reduce dungeon size
   - Simplify algorithm parameters
   - Enable caching

2. **Memory Issues**
   - Limit concurrent generations
   - Use smaller dungeons
   - Clear generation history

3. **Invalid Dungeons**
   - Check algorithm parameters
   - Validate theme compatibility
   - Review error logs

### Debug Mode

```javascript
// Enable debug logging
const config = new ConfigManager();
config.set('logging.level', 'debug');

// Enable performance profiling
config.set('performance.enable_profiling', true);
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

### Development Setup
```bash
# Install dependencies
npm install

# Run tests
npm test

# Start development server
npm run dev

# Run linting
npm run lint
```

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- n8n for workflow automation
- Procedural Content Generation community
- Tabletop RPG community for feedback
- DMlogn8n contributors

## 📞 Support

- **Documentation**: [Full API Docs](./docs/api.md)
- **Examples**: [Example Implementations](./examples/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discord**: [Community Discord](https://discord.gg/your-server)

---

**Dynamic Dungeon Generator** - Creating infinite adventures, one dungeon at a time. 🏰✨