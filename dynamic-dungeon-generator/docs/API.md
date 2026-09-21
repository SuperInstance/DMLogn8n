# Dynamic Dungeon Generator API Documentation

Complete REST API documentation for the Dynamic Dungeon Generator system.

## Base URL
```
http://localhost:3001/api
```

## Authentication
Currently no authentication is required for local development. Production deployments should implement appropriate authentication.

## Response Format

All responses follow this standard format:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "message": "Error description",
    "type": "error_type",
    "status": 400
  },
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

## Dungeons API

### Generate New Dungeon
```http
POST /api/dungeons/generate
```

#### Request Body
```json
{
  "algorithm": "roomCorridor",           // "cellular", "bsp", "roomCorridor", "organic"
  "theme": "classic",                    // Theme name
  "width": 50,                          // 10-200
  "height": 50,                         // 10-200
  "floors": 1,                          // 1-10
  "difficulty": 1,                       // 1-10
  "playerLevel": 1,                     // 1-20
  "seed": 12345,                        // Optional seed for reproducibility
  "customRules": {                      // Optional custom generation rules
    "roomDensity": 1.2,
    "enemyStrength": 0.8
  },
  "options": {                          // Algorithm-specific options
    "roomCount": { "min": 8, "max": 20 },
    "corridorWidth": 2
  }
}
```

#### Response
```json
{
  "success": true,
  "dungeon": {
    "id": "dungeon-uuid",
    "metadata": {
      "theme": "classic",
      "difficulty": 1,
      "playerLevel": 1,
      "createdAt": "2024-01-01T00:00:00.000Z",
      "version": "1.0.0"
    },
    "dimensions": {
      "width": 50,
      "height": 50,
      "floors": 1
    },
    "statistics": {
      "totalRooms": 8,
      "totalCorridors": 7,
      "totalEnemies": 12,
      "totalLoot": 6,
      "totalTraps": 4,
      "totalPuzzles": 2,
      "totalBosses": 1,
      "difficultyRating": 3,
      "estimatedPlayTime": 45
    },
    "floors": [
      {
        "floor": 1,
        "rooms": [...],
        "corridors": [...],
        "spawns": [...],
        "loot": [...],
        "traps": [...],
        "puzzles": [...],
        "bosses": [...],
        "lighting": {...},
        "environment": {...}
      }
    ]
  },
  "generatedAt": "2024-01-01T00:00:00.000Z"
}
```

### List All Dungeons
```http
GET /api/dungeons?limit=10&offset=0
```

#### Query Parameters
- `limit` (optional): Number of dungeons to return (default: 10)
- `offset` (optional): Offset for pagination (default: 0)
- `theme` (optional): Filter by theme
- `difficulty` (optional): Filter by difficulty
- `minFloors` (optional): Minimum number of floors
- `maxFloors` (optional): Maximum number of floors

#### Response
```json
{
  "success": true,
  "dungeons": [
    {
      "id": "dungeon-uuid",
      "metadata": {...},
      "dimensions": {...},
      "statistics": {...},
      "generationTime": 1500,
      "timestamp": "2024-01-01T00:00:00.000Z"
    }
  ],
  "total": 25
}
```

### Get Specific Dungeon
```http
GET /api/dungeons/{dungeonId}
```

#### Response
```json
{
  "success": true,
  "dungeon": {
    "id": "dungeon-uuid",
    "metadata": {...},
    "dimensions": {...},
    "statistics": {...},
    "floors": [
      {
        "floor": 1,
        "grid": [...],                    // 2D array of tile types
        "rooms": [...],
        "corridors": [...],
        "spawns": [...],
        "loot": [...],
        "traps": [...],
        "puzzles": [...],
        "bosses": [...],
        "lighting": {...},
        "environment": {...}
      }
    ],
    "generatedAt": "2024-01-01T00:00:00.000Z"
  }
}
```

### Get Dungeon Floor
```http
GET /api/dungeons/{dungeonId}/floor/{floorIndex}
```

#### Response
```json
{
  "success": true,
  "floor": {
    "floor": 1,
    "grid": [...],
    "rooms": [...],
    "corridors": [...],
    "spawns": [...],
    "loot": [...],
    "traps": [...],
    "puzzles": [...],
    "bosses": [...],
    "lighting": {...},
    "environment": {...}
  }
}
```

### Visualize Dungeon Floor
```http
GET /api/dungeons/{dungeonId}/visualize/{floorIndex}?format=ascii
```

#### Query Parameters
- `format`: `ascii` or `json` (default: `ascii`)

#### ASCII Response
```json
{
  "success": true,
  "dungeonId": "dungeon-uuid",
  "floor": 1,
  "format": "ascii",
  "visualization": "####################\n#..................#\n#..######.......#.#\n..."
}
```

#### JSON Response
```json
{
  "success": true,
  "dungeonId": "dungeon-uuid",
  "floor": 1,
  "format": "json",
  "visualization": {
    "dimensions": { "width": 50, "height": 50 },
    "tiles": [...],
    "rooms": [...],
    "corridors": [...]
  }
}
```

### Modify Dungeon
```http
POST /api/dungeons/{dungeonId}/modify
```

#### Request Body
```json
{
  "modifications": {
    "floor": 1,                           // Floor to modify (optional)
    "lighting": {                          // Lighting modifications
      "brightness": 0.8,
      "addSource": {
        "x": 25,
        "y": 25,
        "radius": 5,
        "intensity": 0.7,
        "color": "#ffcc00"
      }
    },
    "enemies": {                           // Enemy modifications
      "add": [
        {
          "type": "goblin",
          "x": 10,
          "y": 10,
          "count": 2
        }
      ],
      "remove": ["enemy-uuid-1"]
    },
    "loot": {                              // Loot modifications
      "add": [
        {
          "type": "chest",
          "x": 15,
          "y": 15,
          "contents": ["gold", "potion"]
        }
      ]
    },
    "traps": {                             // Trap modifications
      "add": [
        {
          "type": "pit",
          "x": 20,
          "y": 20,
          "damage": "2d6"
        }
      ]
    }
  }
}
```

#### Response
```json
{
  "success": true,
  "dungeon": { ... },                    // Updated dungeon
  "modifiedAt": "2024-01-01T00:00:00.000Z"
}
```

### Delete Dungeon
```http
DELETE /api/dungeons/{dungeonId}
```

#### Response
```json
{
  "success": true,
  "message": "Dungeon deleted successfully",
  "deletedAt": "2024-01-01T00:00:00.000Z"
}
```

### Validate Generation Parameters
```http
POST /api/dungeons/validate
```

#### Request Body
Same as generation request parameters.

#### Response
```json
{
  "success": true,
  "validation": {
    "valid": true,
    "warnings": [
      "Large dungeon size may impact generation performance"
    ],
    "errors": []
  }
}
```

## Themes API

### List All Themes
```http
GET /api/themes
```

#### Response
```json
{
  "success": true,
  "themes": [
    {
      "id": "classic",
      "name": "Classic Dungeon",
      "description": "Traditional stone dungeon with torches",
      "category": "traditional",
      "difficulty": 1,
      "environment": "underground",
      "recommendedLevel": 1
    },
    {
      "id": "undeadCrypt",
      "name": "Undead Crypt",
      "description": "Haunted burial crypt filled with undead",
      "category": "supernatural",
      "difficulty": 3,
      "environment": "necromantic",
      "recommendedLevel": 5
    }
  ]
}
```

### Get Theme Details
```http
GET /api/themes/{themeId}
```

#### Response
```json
{
  "success": true,
  "theme": {
    "id": "classic",
    "name": "Classic Dungeon",
    "description": "Traditional stone dungeon with torches",
    "category": "traditional",
    "difficulty": 1,
    "environment": "underground",
    "recommendedLevel": 1,
    "tileMapping": {...},
    "lighting": {...},
    "enemyTypes": [...],
    "treasureTypes": [...],
    "trapTypes": [...],
    "puzzleTypes": [...]
  }
}
```

### Get Themes by Category
```http
GET /api/themes?category=traditional
```

#### Query Parameters
- `category`: `traditional`, `supernatural`, `elemental`, `magical`, `creature`, `constructed`, `aquatic`
- `difficulty`: Filter by difficulty level (1-10)
- `environment`: Filter by environment type

## Algorithms API

### List All Algorithms
```http
GET /api/algorithms
```

#### Response
```json
{
  "success": true,
  "algorithms": [
    {
      "id": "cellular",
      "name": "Cellular Automata",
      "description": "Creates organic, cave-like dungeons",
      "bestFor": ["caves", "natural", "underground"],
      "complexity": "medium",
      "parameters": {...}
    },
    {
      "id": "bsp",
      "name": "Binary Space Partitioning",
      "description": "Creates structured, room-based dungeons",
      "bestFor": ["traditional", "structured", "room-based"],
      "complexity": "low",
      "parameters": {...}
    }
  ]
}
```

### Get Algorithm Details
```http
GET /api/algorithms/{algorithmId}
```

#### Response
```json
{
  "success": true,
  "algorithm": {
    "id": "roomCorridor",
    "name": "Room-Corridor",
    "description": "Creates classic dungeons with rooms and corridors",
    "bestFor": ["traditional", "classic", "room-based"],
    "complexity": "low",
    "defaultParameters": {
      "roomCount": { "min": 8, "max": 20 },
      "roomSize": { "min": 4, "max": 12 },
      "corridorWidth": 1,
      "loopProbability": 0.2,
      "deadEndProbability": 0.1
    },
    "supportedThemes": ["all"],
    "examples": [...]
  }
}
```

## Customization API

### Get Templates
```http
GET /api/customization/templates
```

#### Response
```json
{
  "success": true,
  "templates": [
    {
      "id": "quick-start",
      "name": "Quick Start",
      "description": "Basic template for new campaigns",
      "parameters": {
        "algorithm": "roomCorridor",
        "theme": "classic",
        "width": 50,
        "height": 50,
        "floors": 1,
        "difficulty": 1,
        "playerLevel": 1
      }
    }
  ]
}
```

### Create Custom Template
```http
POST /api/customization/templates
```

#### Request Body
```json
{
  "name": "My Template",
  "description": "Custom template for my campaign",
  "parameters": {
    "algorithm": "bsp",
    "theme": "dwarvenMines",
    "width": 60,
    "height": 60,
    "floors": 2,
    "difficulty": 3,
    "playerLevel": 5
  }
}
```

### Create Custom Theme
```http
POST /api/customization/themes
```

#### Request Body
```json
{
  "name": "My Custom Theme",
  "description": "A custom theme I created",
  "difficulty": 2,
  "environment": "mixed",
  "tileMapping": {
    "wall": "custom_wall",
    "floor": "custom_floor",
    "door": "custom_door"
  },
  "lighting": {
    "brightness": 0.5,
    "color": "#ffffff"
  }
}
```

## Export API

### Export Dungeon
```http
POST /api/export/dungeon/{dungeonId}
```

#### Request Body
```json
{
  "format": "json",                     // "json", "dm-notes", "player-map", "image"
  "options": {
    "includeContent": true,
    "includeGrid": true,
    "includeLighting": false
  }
}
```

#### Response
```json
{
  "success": true,
  "exportUrl": "https://api.example.com/exports/dungeon-uuid.json",
  "expiresAt": "2024-01-01T01:00:00.000Z"
}
```

### Import Dungeon
```http
POST /api/import/dungeon
```

#### Request Body
```json
{
  "format": "json",
  "data": { ... },                    // Dungeon data
  "options": {
    "validate": true,
    "overwrite": false
  }
}
```

## Integration API

### Get Content at Position
```http
GET /api/integration/dungeon/{dungeonId}/floor/{floorIndex}/content?x=10&y=15
```

#### Response
```json
{
  "success": true,
  "content": {
    "enemies": [...],
    "loot": [...],
    "traps": [...],
    "puzzles": [...],
    "bosses": [...],
    "storytelling": [...]
  }
}
```

### Prepare Combat Encounters
```http
POST /api/integration/dungeon/{dungeonId}/combat-prepare
```

#### Response
```json
{
  "success": true,
  "encounters": [
    {
      "id": "encounter-uuid",
      "floor": 1,
      "enemies": [...],
      "difficulty": 2,
      "recommendedParty": 4
    }
  ]
}
```

### Generate Quest Hooks
```http
POST /api/integration/dungeon/{dungeonId}/quest-hooks
```

#### Response
```json
{
  "success": true,
  "questHooks": [
    {
      "id": "quest-uuid",
      "title": "The Lost Artifact",
      "description": "Find the ancient artifact hidden in the dungeon",
      "difficulty": 2,
      "location": { "floor": 1, "room": "room-uuid" }
    }
  ]
}
```

## Health and Monitoring

### Health Check
```http
GET /api/health
```

#### Response
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "version": "1.0.0",
  "uptime": 3600,
  "memory": {
    "used": "150MB",
    "total": "512MB"
  },
  "statistics": {
    "totalDungeons": 150,
    "activeGenerations": 2,
    "averageGenerationTime": 1200
  }
}
```

### System Statistics
```http
GET /api/statistics
```

#### Response
```json
{
  "success": true,
  "statistics": {
    "totalDungeons": 150,
    "totalGenerations": 250,
    "averageGenerationTime": 1200,
    "popularThemes": [
      { "theme": "classic", "count": 45 },
      { "theme": "undeadCrypt", "count": 32 }
    ],
    "popularAlgorithms": [
      { "algorithm": "roomCorridor", "count": 89 },
      { "algorithm": "bsp", "count": 67 }
    ],
    "errorRate": 0.02,
    "uptime": 86400
  }
}
```

## Error Codes

| Status | Code | Description |
|--------|------|-------------|
| 400 | `invalid_parameters` | Invalid request parameters |
| 400 | `validation_error` | Parameter validation failed |
| 404 | `not_found` | Dungeon or resource not found |
| 429 | `rate_limit_exceeded` | Too many requests |
| 500 | `generation_error` | Dungeon generation failed |
| 500 | `internal_error` | Internal server error |

## Rate Limiting

- **Generation requests**: 10 per minute
- **Other requests**: 100 per minute
- **WebSocket connections**: 5 per IP

## WebSocket Events

### Connection
```javascript
const ws = new WebSocket('ws://localhost:3001');

// Generate dungeon with progress updates
ws.send(JSON.stringify({
  type: 'generate-dungeon',
  parameters: { ... }
}));

// Listen for progress
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

### Events

#### Generation Started
```json
{
  "type": "generation-started",
  "dungeonId": "dungeon-uuid",
  "parameters": { ... }
}
```

#### Generation Progress
```json
{
  "type": "generation-progress",
  "stage": "content-population",
  "progress": 75,
  "message": "Placing enemies and loot"
}
```

#### Generation Complete
```json
{
  "type": "generation-complete",
  "dungeon": { ... }
}
```

#### Generation Error
```json
{
  "type": "generation-error",
  "error": {
    "message": "Generation failed",
    "type": "generation_error"
  }
}
```

## SDK Examples

### JavaScript/Node.js
```javascript
const DungeonAPI = require('dungeon-generator-sdk');

const client = new DungeonAPI('http://localhost:3001/api');

// Generate dungeon
const dungeon = await client.dungeons.generate({
  algorithm: 'roomCorridor',
  theme: 'classic',
  width: 50,
  height: 50,
  difficulty: 1
});

// Get visualization
const visualization = await client.dungeons.visualize(
  dungeon.id,
  0,
  { format: 'ascii' }
);

console.log(visualization.visualization);
```

### Python
```python
import requests

client = DungeonAPI('http://localhost:3001/api')

# Generate dungeon
dungeon = client.dungeons.generate({
    'algorithm': 'roomCorridor',
    'theme': 'classic',
    'width': 50,
    'height': 50
})

# Get list of dungeons
dungeons = client.dungeons.list(limit=10)
```

## Support

For API support:
- Documentation: [Full API Guide](https://docs.example.com)
- Examples: [Code Examples](https://github.com/examples)
- Issues: [GitHub Issues](https://github.com/issues)
- Discord: [Community Support](https://discord.gg/support)