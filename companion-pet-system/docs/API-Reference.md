# DMlogn8n Companion Pet System API Reference

## Overview

The Companion Pet System provides a comprehensive REST API for managing pets, their behaviors, evolution, training, and care. This reference document details all available endpoints, request/response formats, and usage examples.

## Base URL

```
http://localhost:3000/api
```

## Authentication

All API requests require authentication using API keys or session tokens:

```javascript
headers: {
  'Authorization': 'Bearer YOUR_API_KEY',
  'Content-Type': 'application/json'
}
```

## Core Pet Management

### Get All Pets

```http
GET /pets
```

**Query Parameters:**
- `ownerId` (string, optional): Filter by owner ID
- `type` (string, optional): Filter by pet type
- `rarity` (string, optional): Filter by rarity tier
- `page` (integer, optional): Page number (default: 1)
- `limit` (integer, optional): Items per page (default: 20)

**Response:**
```json
{
  "success": true,
  "data": {
    "pets": [
      {
        "id": "pet_abc123",
        "typeId": "wolf",
        "name": "Shadow",
        "level": 15,
        "bonding": 75,
        "currentHealth": 120,
        "maxHealth": 120,
        "energy": 85,
        "happiness": 80,
        "evolutionStage": 2,
        "abilities": ["bite", "howl", "pack_hunt"],
        "traits": ["loyal", "territorial"],
        "isActive": true,
        "lastActive": "2024-01-15T10:30:00.000Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 1,
      "totalPages": 1
    }
  }
}
```

### Get Pet by ID

```http
GET /pets/{petId}
```

**Path Parameters:**
- `petId` (string): Unique pet identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "pet_abc123",
    "typeId": "wolf",
    "name": "Shadow",
    "ownerId": "player_456",
    "level": 15,
    "experience": 750,
    "bonding": 75,
    "happiness": 80,
    "hunger": 65,
    "cleanliness": 90,
    "energy": 85,
    "stats": {
      "health": 120,
      "attack": 25,
      "defense": 20,
      "speed": 18,
      "intelligence": 12
    },
    "currentHealth": 120,
    "maxHealth": 120,
    "evolutionStage": 2,
    "personality": {
      "primary": "loyal",
      "secondary": "protective",
      "quirks": ["tail_chaser", "door_guardian"],
      "preferences": {
        "favoriteFood": "meat",
        "favoriteActivity": "playing",
        "preferredWeather": ["sunny", "cloudy"]
      }
    },
    "abilities": ["bite", "howl", "pack_hunt"],
    "traits": ["loyal", "territorial", "tamed"],
    "equipment": {
      "collar": { "id": "leather_collar", "stats": { "defense": 2 } },
      "armor": null,
      "accessory": null,
      "weapon": null
    },
    "lastFed": "2024-01-15T08:00:00.000Z",
    "lastGroomed": "2024-01-15T07:30:00.000Z",
    "lastTrained": "2024-01-14T15:00:00.000Z",
    "createdAt": "2024-01-10T12:00:00.000Z",
    "lastActive": "2024-01-15T10:30:00.000Z"
  }
}
```

### Create New Pet

```http
POST /pets
```

**Request Body:**
```json
{
  "typeId": "wolf",
  "ownerId": "player_456",
  "name": "Shadow",
  "customTraits": ["brave"],
  "initialEquipment": {
    "collar": "leather_collar"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "pet_abc123",
    "typeId": "wolf",
    "name": "Shadow",
    "ownerId": "player_456",
    "level": 1,
    "evolutionStage": 0,
    "createdAt": "2024-01-15T10:30:00.000Z"
  },
  "message": "Pet created successfully"
}
```

### Update Pet

```http
PUT /pets/{petId}
```

**Request Body:**
```json
{
  "name": "Shadow Fang",
  "equipment": {
    "collar": "enchanted_collar",
    "armor": "leather_armor"
  }
}
```

### Delete Pet

```http
DELETE /pets/{petId}
```

**Response:**
```json
{
  "success": true,
  "message": "Pet deleted successfully"
}
```

## Pet Care Actions

### Perform Care Action

```http
POST /pets/{petId}/care
```

**Request Body:**
```json
{
  "actionType": "feed",
  "performer": "player_456",
  "location": "home",
  "food": "meat",
  "amount": "large"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "action": "feed",
    "hungerRestored": 35,
    "happinessIncrease": 8,
    "bondingIncrease": 3,
    "petStatus": {
      "hunger": 95,
      "happiness": 88,
      "bonding": 78
    }
  },
  "message": "Pet fed successfully"
}
```

### Available Care Actions

#### Feed
```json
{
  "actionType": "feed",
  "food": "meat|fish|vegetables|custom_meal",
  "amount": "small|medium|large|auto"
}
```

#### Groom
```json
{
  "actionType": "groom",
  "method": "brush|bath|full_groom|auto",
  "tools": "brush|shampoo|towel|auto"
}
```

#### Train
```json
{
  "actionType": "train",
  "skill": "sit|stay|come|attack|defense",
  "method": "positive_reinforcement|clicker_training|play_training",
  "intensity": "light|moderate|intense"
}
```

#### Play
```json
{
  "actionType": "play",
  "activity": "fetch|chase|puzzle_games|social_play",
  "duration": 15
}
```

#### Heal
```json
{
  "actionType": "heal",
  "method": "rest|potion|magic|medical",
  "items": ["healing_potion"]
}
```

## Pet Training

### Get Available Training

```http
GET /pets/{petId}/training/available
```

**Response:**
```json
{
  "success": true,
  "data": {
    "skills": [
      {
        "id": "sit",
        "name": "Sit",
        "category": "obedience",
        "difficulty": 1,
        "prerequisites": [],
        "status": "available",
        "canLearn": true,
        "estimatedTime": "5 minutes",
        "successRate": 0.9
      },
      {
        "id": "attack",
        "name": "Attack Command",
        "category": "combat",
        "difficulty": 4,
        "prerequisites": ["sit", "come"],
        "status": "locked",
        "reason": "prerequisite_not_met",
        "prerequisite": "come"
      }
    ]
  }
}
```

### Train Pet

```http
POST /pets/{petId}/train
```

**Request Body:**
```json
{
  "skillId": "sit",
  "method": "positive_reinforcement",
  "intensity": "moderate",
  "options": {
    "location": "training_ground",
    "equipment": ["treats", "clicker"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "sessionId": "training_xyz789",
    "skill": "sit",
    "method": "positive_reinforcement",
    "results": {
      "success": true,
      "skillLearned": true,
      "skillImproved": false,
      "experienceGained": 25,
      "bondingGained": 8,
      "energyConsumed": 15,
      "duration": 300000
    }
  },
  "message": "Training completed successfully"
}
```

### Get Training History

```http
GET /pets/{petId}/training/history
```

**Query Parameters:**
- `limit` (integer, optional): Number of records to return
- `skill` (string, optional): Filter by specific skill

## Evolution System

### Check Evolution Readiness

```http
GET /pets/{petId}/evolution/readiness
```

**Response:**
```json
{
  "success": true,
  "data": {
    "ready": false,
    "requirements": {
      "allMet": false,
      "progress": 0.85,
      "level": {
        "met": true,
        "required": 25,
        "current": 25,
        "progress": 1.0
      },
      "bonding": {
        "met": false,
        "required": 60,
        "current": 55,
        "progress": 0.92
      },
      "experience": {
        "met": true,
        "required": 500,
        "current": 620,
        "progress": 1.0
      }
    },
    "nextStage": {
      "name": "Alpha Wolf",
      "level": 25,
      "requirements": {
        "level": 25,
        "bonding": 60,
        "skills": ["pack_leader"]
      },
      "visualChanges": ["alpha_mane", "enhanced_eyes"]
    },
    "currentProgress": 0.85
  }
}
```

### Perform Evolution

```http
POST /pets/{petId}/evolution
```

**Request Body:**
```json
{
  "forced": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "previousStage": 1,
    "newStage": 2,
    "changes": {
      "statIncreases": {
        "health": 15,
        "attack": 8,
        "defense": 6,
        "speed": 4,
        "intelligence": 5
      },
      "newAbilities": ["alpha_presence", "pack_coordination"],
      "traitChanges": ["alpha_potential"],
      "visualChanges": ["alpha_mane", "enhanced_eyes"],
      "skillPointsAwarded": 2
    },
    "evolutionName": "Alpha Wolf"
  },
  "message": "Evolution completed successfully"
}
```

### Get Special Evolutions

```http
GET /pets/{petId}/special-evolutions
```

**Response:**
```json
{
  "success": true,
  "data": {
    "possibleEvolutions": [
      {
        "id": "shadow_wolf_evolution",
        "name": "Shadow Wolf Alpha",
        "description": "Evolve into a shadow wolf alpha through dark magic",
        "requirements": {
          "shadow_crystals": 5,
          "dark_ritual_complete": true,
          "shadow_bonding": 80
        },
        "requirementsMet": false
      }
    ]
  }
}
```

## Combat System

### Enter Battle

```http
POST /pets/{petId}/combat/enter
```

**Request Body:**
```json
{
  "battleType": "normal|tournament|boss|pvp",
  "opponents": ["pet_def456", "pet_ghi789"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "battleId": "battle_abc123",
    "turnOrder": [
      {
        "id": "pet_abc123",
        "name": "Shadow",
        "speed": 18
      },
      {
        "id": "pet_def456",
        "name": "Fang",
        "speed": 16
      }
    ],
    "opponentCount": 1
  },
  "message": "Entered battle successfully"
}
```

### Perform Combat Action

```http
POST /pets/{petId}/combat/action
```

**Request Body:**
```json
{
  "action": "bite",
  "target": "pet_def456"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "action": "bite",
    "target": "pet_def456",
    "effects": ["dealt 18 damage"],
    "damage": 18,
    "healing": 0,
    "statusEffects": [],
    "critical": false,
    "missed": false
  },
  "message": "Action performed successfully"
}
```

### Get Combat Abilities

```http
GET /pets/{petId}/combat/abilities
```

**Response:**
```json
{
  "success": true,
  "data": {
    "abilities": [
      {
        "id": "bite",
        "name": "Bite",
        "type": "attack",
        "energyCost": 10,
        "cooldown": 2000,
        "range": 1,
        "damage": { "base": 15, "type": "physical" },
        "accuracy": 0.9,
        "criticalBonus": 0.05,
        "unlocked": true
      },
      {
        "id": "howl",
        "name": "Howl",
        "type": "support",
        "energyCost": 20,
        "cooldown": 10000,
        "range": 5,
        "effects": ["buffs allies"],
        "unlocked": true
      }
    ]
  }
}
```

## Pet Acquisition

### Start Taming

```http
POST /acquisition/tame
```

**Request Body:**
```json
{
  "playerId": "player_456",
  "creatureId": "wolf_001",
  "tamingMethod": "standard|food_bait|magical_aid|ritual|master_tamer"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "sessionId": "taming_session_123",
    "estimatedTime": 120000,
    "successChance": 0.75
  },
  "message": "Taming session started"
}
```

### Complete Taming

```http
POST /acquisition/tame/{sessionId}/complete
```

**Response:**
```json
{
  "success": true,
  "data": {
    "pet": {
      "id": "pet_new789",
      "typeId": "wolf",
      "name": "Wind",
      "ownerId": "player_456"
    },
    "tamingMethod": "standard",
    "bondingBonus": 5
  },
  "message": "Taming completed successfully"
}
```

### Start Summoning

```http
POST /acquisition/summon
```

**Request Body:**
```json
{
  "playerId": "player_456",
  "summoningType": "basic_familiar|elemental_binding|dark_pact|celestial_summoning",
  "offerings": [
    { "id": "mana_crystal", "quantity": 2 },
    { "id": "essence_of_magic", "quantity": 1 }
  ]
}
```

### Request Breeding

```http
POST /acquisition/breed
```

**Request Body:**
```json
{
  "playerId": "player_456",
  "pet1Id": "pet_abc123",
  "pet2Id": "pet_def456"
}
```

## Analytics and Reports

### Get Care Report

```http
GET /pets/{petId}/care/report
```

**Query Parameters:**
- `timeRange` (integer, optional): Number of days (default: 7)

**Response:**
```json
{
  "success": true,
  "data": {
    "timeRangeDays": 7,
    "totalActions": 24,
    "actionBreakdown": {
      "feed": 7,
      "play": 5,
      "groom": 3,
      "train": 4,
      "rest": 5
    },
    "successRate": 95.8,
    "careStreaks": {
      "feed": { "current": 7, "best": 12 },
      "groom": { "current": 3, "best": 8 }
    },
    "recommendations": [
      {
        "type": "happiness",
        "priority": "medium",
        "message": "Pet happiness could be improved",
        "suggestedAction": "play"
      }
    ],
    "moodTrends": {
      "improving": true,
      "stable": false
    }
  }
}
```

### Get Training Report

```http
GET /pets/{petId}/training/report
```

**Response:**
```json
{
  "success": true,
  "data": {
    "overview": {
      "totalSessions": 15,
      "successfulSessions": 13,
      "successRate": 86.7,
      "skillsLearned": 4
    },
    "favoriteMethods": [
      {
        "method": "positive_reinforcement",
        "usage": 8,
        "percentage": 53.3
      }
    ],
    "skillMastery": {
      "sit": {
        "attempts": 5,
        "successes": 5,
        "successRate": 100,
        "masteryLevel": "mastered"
      }
    },
    "trainingTrends": {
      "improving": true,
      "recentSuccessRate": 90.0,
      "trend": "improving"
    }
  }
}
```

## Housing System

### Create Habitat

```http
POST /housing/habitat
```

**Request Body:**
```json
{
  "petId": "pet_abc123",
  "habitatType": "basic_den|enchanted_forest|volcanic_lair|arctic_cave",
  "location": "player_house"
}
```

### Get Habitat Status

```http
GET /housing/habitat/{habitatId}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "habitat_xyz789",
    "type": "enchanted_forest",
    "level": 2,
    "comfort": 75,
    "cleanliness": 90,
    "space": {
      "total": 150,
      "used": 45,
      "available": 105
    },
    "occupants": 1,
    "decorations": 3,
    "amenities": ["feeding_station", "grooming_area"]
  }
}
```

### Upgrade Habitat

```http
POST /housing/habitat/{habitatId}/upgrade
```

**Request Body:**
```json
{
  "upgradeType": "comfort|space|cleanliness|amenities"
}
```

## Utility Skills

### Get Utility Skills

```http
GET /pets/{petId}/utility/skills
```

**Response:**
```json
{
  "success": true,
  "data": {
    "tracking": {
      "name": "Tracking",
      "type": "utility",
      "description": "Can track enemies and find hidden paths",
      "effectiveness": 65,
      "available": true
    },
    "scouting": {
      "name": "Scouting",
      "type": "utility",
      "description": "Can scout areas and reveal hidden dangers",
      "effectiveness": 45,
      "available": true
    }
  }
}
```

### Perform Utility Action

```http
POST /pets/{petId}/utility/action
```

**Request Body:**
```json
{
  "skillId": "tracking",
  "context": {
    "target": "enemy_001",
    "area": "forest_01"
  }
}
```

## Error Responses

All endpoints may return error responses:

```json
{
  "success": false,
  "error": {
    "code": "PET_NOT_FOUND",
    "message": "Pet with ID 'pet_invalid' not found",
    "details": {
      "petId": "pet_invalid"
    }
  }
}
```

### Common Error Codes

- `PET_NOT_FOUND`: Pet does not exist
- `INSUFFICIENT_PERMISSIONS`: User doesn't own the pet
- `INVALID_ACTION`: Action type not recognized
- `INSUFFICIENT_ENERGY`: Pet doesn't have enough energy
- `REQUIREMENTS_NOT_MET`: Prerequisites not satisfied
- `COOLDOWN_ACTIVE`: Action is on cooldown
- `INVALID_PARAMETERS`: Request parameters are invalid

## Rate Limiting

API endpoints are rate-limited to prevent abuse:

- **Standard endpoints**: 100 requests per minute
- **Care actions**: 10 requests per minute per pet
- **Combat actions**: 5 requests per minute per battle
- **Evolution**: 1 request per hour per pet

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642234567
```

## Webhooks

### Configure Webhooks

```http
POST /webhooks
```

**Request Body:**
```json
{
  "url": "https://your-server.com/webhooks",
  "events": ["pet_evolution", "pet_level_up", "pet_defeated"],
  "secret": "your_webhook_secret"
}
```

### Webhook Events

#### Pet Evolution
```json
{
  "event": "pet_evolution",
  "petId": "pet_abc123",
  "data": {
    "previousStage": 1,
    "newStage": 2,
    "evolutionName": "Alpha Wolf"
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

#### Pet Level Up
```json
{
  "event": "pet_level_up",
  "petId": "pet_abc123",
  "data": {
    "previousLevel": 14,
    "newLevel": 15,
    "skillPointsAwarded": 1
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## SDK Examples

### JavaScript/Node.js

```javascript
const PetAPI = require('dmlogn8n-pet-sdk');

const client = new PetAPI({
  baseURL: 'http://localhost:3000/api',
  apiKey: 'your-api-key'
});

// Get pet information
const pet = await client.pets.get('pet_abc123');

// Feed pet
const feedResult = await client.pets.care('pet_abc123', {
  actionType: 'feed',
  food: 'meat',
  amount: 'medium'
});

// Check evolution readiness
const evolutionStatus = await client.pets.evolution.readiness('pet_abc123');
```

### Python

```python
from dmn8n_pet_api import PetClient

client = PetClient(
    base_url='http://localhost:3000/api',
    api_key='your-api-key'
)

# Get pet information
pet = client.pets.get('pet_abc123')

# Train pet
training_result = client.pets.train('pet_abc123', {
    'skill_id': 'sit',
    'method': 'positive_reinforcement'
})
```

## Testing

### Test Endpoints

For testing and development, use the test endpoints:

```http
POST /test/create-pet
```

**Request Body:**
```json
{
  "typeId": "wolf",
  "ownerId": "test_player",
  "name": "Test Wolf"
}
```

### Mock Data

Use the mock endpoints for development without affecting live data:

```http
GET /test/mock-pets
```

## Support

For API support and questions:

- **Documentation**: https://docs.dmlogn8n-pets.com
- **API Status**: https://status.dmlogn8n-pets.com
- **Support Email**: api-support@dmlogn8n-pets.com
- **Discord**: https://discord.gg/dmlogn8n-pets

---

**DMlogn8n Companion Pet System API** - Complete integration for intelligent pet companions! 🐾✨