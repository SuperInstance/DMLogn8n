# Dynamic Quest Generator API Reference

## Base URL
```
http://localhost:3001/api
```

## Authentication
Currently, the API uses player ID-based authentication. Future versions will implement JWT tokens.

## Headers
```
Content-Type: application/json
Authorization: Bearer <token> (future implementation)
```

## Response Format
All API responses follow this format:
```json
{
  "success": true,
  "data": {},
  "message": "Operation completed successfully",
  "timestamp": "2024-01-20T10:00:00.000Z"
}
```

Error responses:
```json
{
  "success": false,
  "message": "Error description",
  "error": "Detailed error message",
  "timestamp": "2024-01-20T10:00:00.000Z"
}
```

## Quest Endpoints

### GET /quests
Retrieve quests with optional filtering and pagination.

**Query Parameters:**
- `page` (number, optional): Page number (default: 1)
- `limit` (number, optional): Items per page (default: 20, max: 100)
- `type` (string, optional): Filter by quest type
- `category` (string, optional): Filter by quest category
- `difficulty` (number, optional): Filter by difficulty (1-7)
- `state` (string, optional): Filter by quest state
- `playerId` (string, optional): Filter by assigned player
- `guildId` (string, optional): Filter by guild
- `tags` (string, optional): Filter by tags (comma-separated)
- `sortBy` (string, optional): Sort field (default: createdAt)
- `sortOrder` (string, optional): Sort direction (asc/desc, default: desc)

**Example Request:**
```http
GET /api/quests?type=side_quest&difficulty=3&page=1&limit=10
```

**Response:**
```json
{
  "success": true,
  "data": {
    "quests": [
      {
        "id": "quest_123",
        "title": "The Missing Merchant",
        "description": "A local merchant has gone missing...",
        "type": "side_quest",
        "category": "mystery",
        "difficulty": 3,
        "state": "active",
        "objectives": [],
        "rewards": {},
        "createdAt": "2024-01-20T10:00:00.000Z"
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 5,
      "totalQuests": 47,
      "hasNext": true,
      "hasPrev": false
    }
  }
}
```

### GET /quests/:questId
Retrieve a specific quest by ID.

**Path Parameters:**
- `questId` (string, required): Quest ID

**Example Request:**
```http
GET /api/quests/quest_123
```

### POST /quests
Create a new quest.

**Request Body:**
```json
{
  "title": "The Dragon's Lair",
  "description": "A fearsome dragon terrorizes the village...",
  "type": "side_quest",
  "category": "combat",
  "difficulty": 5,
  "levelRequirement": 15,
  "objectives": [
    {
      "title": "Defeat the Dragon",
      "description": "Slay the ancient dragon",
      "type": "kill",
      "target": "ancient_dragon",
      "required": 1
    }
  ],
  "rewards": {
    "base": [
      {
        "type": "experience",
        "amount": 1000,
        "description": "Dragon slayer experience"
      }
    ]
  }
}
```

### PUT /quests/:questId
Update an existing quest.

**Path Parameters:**
- `questId` (string, required): Quest ID

**Request Body:**
```json
{
  "title": "Updated Quest Title",
  "description": "Updated description",
  "difficulty": 4
}
```

### DELETE /quests/:questId
Delete a quest.

**Path Parameters:**
- `questId` (string, required): Quest ID

### POST /quests/generate
Generate a new quest using AI or templates.

**Request Body:**
```json
{
  "playerId": "player_123",
  "questType": "side_quest",
  "category": "exploration",
  "difficulty": 3,
  "personalized": true,
  "forceAI": false,
  "options": {
    "playerLevel": 12,
    "playerClass": "ranger",
    "preferences": {
      "combat": 0.6,
      "exploration": 0.8,
      "social": 0.4,
      "mystery": 0.7,
      "crafting": 0.2
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "quest": {
    "id": "ai_quest_456",
    "title": "The Forgotten Ruins",
    "description": "Ancient ruins have been discovered...",
    "type": "side_quest",
    "category": "exploration",
    "difficulty": 3,
    "objectives": [],
    "rewards": {},
    "estimatedTime": 45,
    "tags": ["ai-generated", "exploration"]
  }
}
```

### POST /quests/:questId/assign
Assign a quest to a player.

**Path Parameters:**
- `questId` (string, required): Quest ID

**Request Body:**
```json
{
  "playerId": "player_123"
}
```

### POST /quests/:questId/progress
Update quest progress.

**Path Parameters:**
- `questId` (string, required): Quest ID

**Request Body:**
```json
{
  "playerId": "player_123",
  "objectiveId": "obj_1",
  "progress": 5,
  "data": {
    "timeSpent": 1200000,
    "location": "forest_area",
    "choice": "peaceful_approach"
  }
}
```

### POST /quests/:questId/complete
Complete a quest.

**Path Parameters:**
- `questId` (string, required): Quest ID

**Request Body:**
```json
{
  "playerId": "player_123",
  "rating": 5,
  "feedback": "Great quest with interesting choices!",
  "choice": "peaceful_resolution"
}
```

### POST /quests/:questId/abandon
Abandon a quest.

**Path Parameters:**
- `questId` (string, required): Quest ID

**Request Body:**
```json
{
  "playerId": "player_123",
  "reason": "Too difficult"
}
```

### POST /quests/:questId/choice
Make a choice in a branching quest.

**Path Parameters:**
- `questId` (string, required): Quest ID

**Request Body:**
```json
{
  "playerId": "player_123",
  "objectiveId": "obj_2",
  "choiceId": "choice_peaceful"
}
```

### GET /quests/player/:playerId/active
Get a player's active quests.

**Path Parameters:**
- `playerId` (string, required): Player ID

### GET /quests/player/:playerId/history
Get a player's quest history.

**Path Parameters:**
- `playerId` (string, required): Player ID

**Query Parameters:**
- `page` (number, optional): Page number (default: 1)
- `limit` (number, optional): Items per page (default: 20, max: 50)
- `type` (string, optional): Filter by quest type
- `state` (string, optional): Filter by quest state

### GET /quests/player/:playerId/available
Get available quests for a player.

**Path Parameters:**
- `playerId` (string, required): Player ID

**Query Parameters:**
- `type` (string, optional): Filter by quest type
- `category` (string, optional): Filter by quest category
- `difficulty` (number, optional): Filter by difficulty (1-7)
- `limit` (number, optional): Maximum results (default: 10, max: 20)

### GET /quests/statistics
Get quest statistics.

**Query Parameters:**
- `timeframe` (string, optional): Time period (1h, 24h, 7d, 30d)
- `playerId` (string, optional): Filter by player

**Response:**
```json
{
  "success": true,
  "data": {
    "totalQuests": 150,
    "completedQuests": 120,
    "abandonedQuests": 15,
    "averageDifficulty": 3.2,
    "averageCompletionTime": 1800000,
    "totalRewards": 50000
  }
}
```

### GET /quests/search
Search quests.

**Query Parameters:**
- `q` (string, required): Search query
- `page` (number, optional): Page number (default: 1)
- `limit` (number, optional): Items per page (default: 20, max: 50)
- `type` (string, optional): Filter by quest type
- `category` (string, optional): Filter by quest category

**Example Request:**
```http
GET /api/quests/search?q=dragon&type=side_quest
```

## Player Endpoints

### GET /players
Retrieve players with optional filtering and pagination.

**Query Parameters:**
- `page` (number, optional): Page number (default: 1)
- `limit` (number, optional): Items per page (default: 20, max: 100)
- `level` (number, optional): Filter by player level
- `class` (string, optional): Filter by character class
- `guildId` (string, optional): Filter by guild
- `status` (string, optional): Filter by status (active, inactive, suspended, banned)
- `sortBy` (string, optional): Sort field (default: createdAt)
- `sortOrder` (string, optional): Sort direction (asc/desc, default: desc)

### GET /players/:playerId
Retrieve a specific player by ID.

**Path Parameters:**
- `playerId` (string, required): Player ID

**Response:**
```json
{
  "success": true,
  "data": {
    "_id": "player_123",
    "userId": "user_123",
    "username": "DragonSlayer42",
    "email": "player@example.com",
    "character": {
      "name": "Aragorn",
      "class": "warrior",
      "race": "human",
      "background": "noble",
      "level": 15,
      "experience": {
        "current": 2500,
        "total": 12500
      }
    },
    "stats": {
      "level": 15,
      "experience": {},
      "attributes": {
        "strength": 16,
        "dexterity": 14,
        "constitution": 15,
        "intelligence": 12,
        "wisdom": 13,
        "charisma": 14
      }
    },
    "questPreferences": {
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
      }
    },
    "createdAt": "2024-01-01T00:00:00.000Z"
  }
}
```

### POST /players
Create a new player.

**Request Body:**
```json
{
  "userId": "user_123",
  "username": "DragonSlayer42",
  "email": "player@example.com",
  "password": "securepassword123",
  "character": {
    "name": "Aragorn",
    "class": "warrior",
    "race": "human",
    "background": "noble",
    "alignment": "lawful_good"
  }
}
```

### PUT /players/:playerId
Update a player.

**Path Parameters:**
- `playerId` (string, required): Player ID

**Request Body:**
```json
{
  "username": "NewUsername",
  "character": {
    "name": "Updated Name"
  },
  "questPreferences": {
    "types": {
      "combat": 0.9,
      "exploration": 0.7
    }
  }
}
```

### DELETE /players/:playerId
Delete a player.

**Path Parameters:**
- `playerId` (string, required): Player ID

### GET /players/:playerId/quests/recommendations
Get personalized quest recommendations for a player.

**Path Parameters:**
- `playerId` (string, required): Player ID

**Query Parameters:**
- `count` (number, optional): Number of recommendations (default: 5, max: 10)

**Response:**
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "type": "combat",
        "category": "dungeon",
        "difficulty": 4,
        "estimatedTime": 45,
        "reasons": [
          "Matches your combat preference",
          "Suitable for your level",
          "Popular with similar players"
        ]
      }
    ]
  }
}
```

### GET /players/:playerId/analytics
Get player quest analytics.

**Path Parameters:**
- `playerId` (string, required): Player ID

**Query Parameters:**
- `timeframe` (string, optional): Time period (24h, 7d, 30d, all)

**Response:**
```json
{
  "success": true,
  "data": {
    "overview": {
      "totalQuests": 25,
      "completedQuests": 22,
      "completionRate": 88,
      "averageRating": 4.2,
      "totalPlayTime": 7200000
    },
    "performance": {
      "averageCompletionTime": 1800000,
      "favoriteQuestType": "side_quest",
      "favoriteDifficulty": 3
    },
    "progression": {
      "currentLevel": 15,
      "totalExperience": 12500,
      "achievements": 8
    }
  }
}
```

### POST /players/:playerId/preferences
Update player quest preferences.

**Path Parameters:**
- `playerId` (string, required): Player ID

**Request Body:**
```json
{
  "types": {
    "combat": 0.8,
    "exploration": 0.6,
    "social": 0.4,
    "mystery": 0.7,
    "crafting": 0.3
  },
  "difficulty": {
    "preferred": 4,
    "adaptive": true
  },
  "questLength": "medium",
  "playStyle": "small_group",
  "partySize": {
    "min": 2,
    "max": 4
  }
}
```

### GET /players/:playerId/achievements
Get player achievements.

**Path Parameters:**
- `playerId` (string, required): Player ID

**Response:**
```json
{
  "success": true,
  "data": {
    "unlocked": [
      {
        "id": "first_quest",
        "name": "First Steps",
        "description": "Complete your first quest",
        "category": "progression",
        "rarity": "common",
        "unlockedAt": "2024-01-02T10:00:00.000Z"
      }
    ],
    "available": [
      {
        "id": "dragon_slayer",
        "name": "Dragon Slayer",
        "description": "Defeat 5 dragons",
        "category": "combat",
        "rarity": "epic",
        "progress": 60,
        "unlocked": false
      }
    ]
  }
}
```

### POST /players/:playerId/achievements
Add an achievement to a player.

**Path Parameters:**
- `playerId` (string, required): Player ID

**Request Body:**
```json
{
  "id": "quest_master",
  "name": "Quest Master",
  "description": "Complete 100 quests",
  "category": "progression",
  "rarity": "legendary"
}
```

### GET /players/search
Search players.

**Query Parameters:**
- `q` (string, required): Search query
- `page` (number, optional): Page number (default: 1)
- `limit` (number, optional): Items per page (default: 20, max: 50)

## System Endpoints

### GET /health
System health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:00:00.000Z",
  "version": "1.0.0",
  "environment": "development",
  "database": {
    "status": "healthy",
    "isConnected": true,
    "state": "connected"
  },
  "uptime": 3600
}
```

### GET /api
API overview and endpoints.

### GET /api/info
API system information.

**Response:**
```json
{
  "name": "Dynamic Quest Generator API",
  "version": "1.0.0",
  "environment": "development",
  "nodeVersion": "v18.17.0",
  "platform": "linux",
  "uptime": 3600,
  "memory": {
    "rss": 134217728,
    "heapTotal": 67108864,
    "heapUsed": 45088768,
    "external": 2097152
  },
  "features": {
    "aiGeneration": "enabled",
    "n8nIntegration": "enabled",
    "database": "connected"
  }
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Validation failed |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource does not exist |
| 409 | Conflict - Resource already exists |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable - System maintenance |

## Rate Limiting

- Standard endpoints: 100 requests per minute
- Generation endpoints: 10 requests per minute
- Search endpoints: 50 requests per minute

## Quest Types

| Type | Description |
|------|-------------|
| `main_story` | Campaign-defining epic quests |
| `side_quest` | Optional character development quests |
| `daily` | Repeatable daily challenges |
| `weekly` | Weekly rotating content |
| `event` | Limited-time special quests |
| `player_generated` | Quests created by players |
| `guild` | Cooperative guild challenges |
| `raid` | Large group encounters |
| `tutorial` | Learning and introduction quests |
| `hidden` | Secret discoverable quests |

## Quest Categories

| Category | Description |
|----------|-------------|
| `combat` | Battle-focused challenges |
| `exploration` | Discovery and navigation |
| `social` | Interaction and relationship quests |
| `crafting` | Item creation and gathering |
| `mystery` | Investigation and puzzle-solving |
| `collection` | Gathering and collecting |
| `escort` | Protection and escort missions |
| `delivery` | Transportation quests |
| `boss_battle` | Major enemy confrontations |
| `dungeon` | Multi-area explorations |

## Objective Types

| Type | Description |
|------|-------------|
| `kill` | Defeat enemies or targets |
| `collect` | Gather items or resources |
| `explore` | Discover locations or areas |
| `talk_to` | Interact with NPCs |
| `craft` | Create specific items |
| `social_interaction` | Complete social challenges |
| `escort` | Protect NPCs during travel |
| `defend` | Protect locations or objects |
| `survive` | Endure for set duration |
| `use_item` | Use specific items |
| `reach_location` | Travel to destinations |
| `complete_dungeon` | Finish dungeon challenges |
| `defeat_boss` | Defeat boss enemies |
| `skill_check` | Pass skill challenges |
| `choice` | Make narrative choices |

## Reward Types

| Type | Description |
|------|-------------|
| `experience` | Character experience points |
| `gold` | Currency rewards |
| `reputation` | Faction standing changes |
| `skill_point` | Character skill improvements |
| `ability` | New character abilities |
| `title` | Character titles |
| `item` | General items and equipment |
| `equipment` | Weapons and armor |
| `access` | New areas or features |
| `custom` | Special unique rewards |

For more detailed implementation examples and integration guides, see the main README.md file.