# Guild Management System API Documentation

Complete API reference for the DMlogn8n Guild Management System.

## Base URL

```
Production: https://your-domain.com/api/guild-management
Development: http://localhost:3001/api
```

## Authentication

All API requests require authentication using JWT tokens:

```http
Authorization: Bearer <your-jwt-token>
```

## Response Format

All responses follow this standard format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Error responses:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": { ... }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Guild Management Endpoints

### Guilds

#### Create Guild
```http
POST /api/guilds/create
```

Creates a new guild with specified settings.

**Request Body:**
```json
{
  "name": "Dragon Slayers",
  "tag": "DRGN",
  "description": "A guild dedicated to dragon hunting",
  "charter": "Our charter text here...",
  "leaderId": "player_123",
  "requirements": {
    "minLevel": 10,
    "classRequirements": ["Warrior", "Paladin"],
    "approvalRequired": true,
    "trialPeriod": 7
  },
  "settings": {
    "memberLimit": 100,
    "bankAccess": "officers",
    "inviteOnly": false,
    "voiceChatRequired": false,
    "activityRequirement": 5
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "guild_abc123",
    "name": "Dragon Slayers",
    "tag": "DRGN",
    "leaderId": "player_123",
    "status": "active",
    "created": "2024-01-15T10:30:00Z"
  }
}
```

#### Get Guild
```http
GET /api/guilds/{guildId}
```

Retrieves detailed information about a specific guild.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "guild_abc123",
    "name": "Dragon Slayers",
    "tag": "DRGN",
    "description": "A guild dedicated to dragon hunting",
    "leaderId": "player_123",
    "level": 5,
    "experience": 12500,
    "memberCount": 25,
    "status": "active",
    "created": "2024-01-01T00:00:00Z",
    "settings": { ... },
    "statistics": { ... }
  }
}
```

#### Update Guild Settings
```http
PUT /api/guilds/{guildId}/settings
```

Updates guild configuration settings.

**Request Body:**
```json
{
  "description": "Updated guild description",
  "settings": {
    "memberLimit": 150,
    "bankAccess": "members",
    "activityRequirement": 10
  }
}
```

#### Delete Guild
```http
DELETE /api/guilds/{guildId}
```

Disbands a guild (requires leader permissions).

### Guild Members

#### Add Member
```http
POST /api/guilds/{guildId}/members
```

Adds a new member to the guild.

**Request Body:**
```json
{
  "playerId": "player_456",
  "rank": "Member",
  "note": "Recruited through application"
}
```

#### Remove Member
```http
DELETE /api/guilds/{guildId}/members/{playerId}
```

Removes a member from the guild.

#### Change Member Rank
```http
PUT /api/guilds/{guildId}/members/{playerId}/rank
```

Changes a member's rank.

**Request Body:**
```json
{
  "newRank": "Officer",
  "changedBy": "player_123"
}
```

#### Get Guild Members
```http
GET /api/guilds/{guildId}/members
```

Retrieves a list of guild members with filtering options.

**Query Parameters:**
- `rank` (optional): Filter by rank
- `status` (optional): Filter by status (active, inactive, suspended)
- `limit` (optional): Maximum number of results (default: 50)
- `offset` (optional): Number of results to skip (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "members": [
      {
        "playerId": "player_123",
        "playerName": "DragonKing",
        "rank": "Leader",
        "status": "active",
        "joined": "2024-01-01T00:00:00Z",
        "contribution": { ... },
        "lastActivity": "2024-01-15T09:30:00Z"
      }
    ],
    "total": 25,
    "page": 1,
    "limit": 50
  }
}
```

### Guild Ranks

#### Create Custom Rank
```http
POST /api/guilds/{guildId}/ranks
```

Creates a custom guild rank.

**Request Body:**
```json
{
  "name": "Elite Guard",
  "level": 60,
  "permissions": [
    "invite_members",
    "access_bank",
    "start_events"
  ],
  "color": "#FF6B6B",
  "icon": "🛡️",
  "description": "Elite defenders of the guild"
}
```

#### Get Guild Ranks
```http
GET /api/guilds/{guildId}/ranks
```

Retrieves all ranks for a guild.

#### Update Rank
```http
PUT /api/guilds/{guildId}/ranks/{rankId}
```

Updates rank properties.

#### Delete Rank
```http
DELETE /api/guilds/{guildId}/ranks/{rankId}
```

Deletes a custom rank (cannot delete default ranks).

### Guild Bank

#### Get Guild Bank
```http
GET /api/guild-banks/{guildId}
```

Retrieves guild bank information.

**Response:**
```json
{
  "success": true,
  "data": {
    "guildId": "guild_abc123",
    "gold": 50000,
    "tabs": [
      {
        "id": "tab1",
        "name": "General",
        "icon": "📦",
        "permissions": "members",
        "items": [
          {
            "itemId": "potion_001",
            "quantity": 100,
            "added": "2024-01-10T15:30:00Z",
            "addedBy": "player_456"
          }
        ],
        "maxSlots": 50
      }
    ],
    "settings": { ... }
  }
}
```

#### Deposit Gold
```http
POST /api/guild-banks/{guildId}/deposit/gold
```

Deposits gold to the guild bank.

**Request Body:**
```json
{
  "playerId": "player_123",
  "amount": 1000,
  "note": "Guild contribution"
}
```

#### Withdraw Gold
```http
POST /api/guild-banks/{guildId}/withdraw/gold
```

Withdraws gold from the guild bank.

**Request Body:**
```json
{
  "playerId": "player_123",
  "amount": 500,
  "reason": "Equipment repair"
}
```

#### Deposit Item
```http
POST /api/guild-banks/{guildId}/deposit/item
```

Deposits an item to the guild bank.

**Request Body:**
```json
{
  "playerId": "player_123",
  "itemId": "sword_001",
  "quantity": 1,
  "tabId": "equipment",
  "note": "Upgraded sword donation"
}
```

#### Withdraw Item
```http
POST /api/guild-banks/{guildId}/withdraw/item
```

Withdraws an item from the guild bank.

#### Get Transaction History
```http
GET /api/guild-banks/{guildId}/transactions
```

Retrieves guild bank transaction history.

**Query Parameters:**
- `type` (optional): Filter by transaction type (deposit, withdrawal, move)
- `playerId` (optional): Filter by player
- `startDate` (optional): Filter by start date
- `endDate` (optional): Filter by end date
- `limit` (optional): Maximum results (default: 50)

### Guild Halls

#### Get Guild Hall
```http
GET /api/guild-halls/{guildId}
```

Retrieves guild hall information.

#### Create Guild Hall
```http
POST /api/guild-halls/create
```

Creates a new guild hall.

**Request Body:**
```json
{
  "guildId": "guild_abc123",
  "location": "Stormwind",
  "hallType": "basic"
}
```

#### Upgrade Guild Hall
```http
POST /api/guild-halls/{hallId}/upgrade
```

Upgrades the guild hall.

**Request Body:**
```json
{
  "upgradeType": "expand_hall",
  "playerId": "player_123"
}
```

#### Add Decoration
```http
POST /api/guild-halls/{hallId}/decorations
```

Adds decoration to guild hall.

**Request Body:**
```json
{
  "playerId": "player_123",
  "itemId": "banner_001",
  "position": { "x": 10, "y": 15, "z": 5 },
  "rotation": { "x": 0, "y": 45, "z": 0 },
  "room": "main",
  "description": "Guild banner"
}
```

#### Add Facility
```http
POST /api/guild-halls/{hallId}/facilities
```

Adds a facility to the guild hall.

**Request Body:**
```json
{
  "playerId": "player_123",
  "facilityType": "training_dummy",
  "position": { "x": 20, "y": 10, "z": 0 }
}
```

## Alliance Management Endpoints

### Alliances

#### Create Alliance
```http
POST /api/alliances/create
```

Creates a new alliance.

**Request Body:**
```json
{
  "name": "United Front",
  "tag": "UNITED",
  "description": "Alliance for mutual defense",
  "charter": "We stand together...",
  "creatorGuildId": "guild_abc123",
  "requirements": {
    "minGuildLevel": 5,
    "minMemberCount": 20,
    "maxGuilds": 8,
    "approvalRequired": true,
    "votingRequired": true,
    "voteThreshold": 0.6
  },
  "settings": {
    "sharedChat": true,
    "sharedEvents": true,
    "sharedBank": false,
    "allianceWars": true
  }
}
```

#### Get Alliance
```http
GET /api/alliances/{allianceId}
```

Retrieves alliance information.

#### Join Alliance (Application)
```http
POST /api/alliances/{allianceId}/apply
```

Applies to join an alliance.

**Request Body:**
```json
{
  "guildId": "guild_456",
  "message": "We wish to join your alliance",
  "contribution": {
    "military": "strong",
    "resources": "moderate"
  },
  "expectations": {
    "support": "military_aid",
    "trade": "resource_sharing"
  }
}
```

#### Accept Application
```http
POST /api/alliances/{allianceId}/applications/{applicationId}/accept
```

Accepts a guild application to the alliance.

#### Reject Application
```http
POST /api/alliances/{allianceId}/applications/{applicationId}/reject
```

Rejects a guild application.

#### Send Invitation
```http
POST /api/alliances/{allianceId}/invite
```

Sends an invitation to a guild.

**Request Body:**
```json
{
  "targetGuildId": "guild_789",
  "message": "We'd like to invite your guild to join our alliance"
}
```

### Alliance Wars

#### Declare War
```http
POST /api/alliances/{allianceId}/declare-war
```

Declares war on another alliance.

**Request Body:**
```json
{
  "targetAllianceId": "alliance_def789",
  "warType": "territory",
  "objectives": [
    {
      "id": 1,
      "description": "Control 3 territories",
      "type": "territory_control",
      "required": 3
    }
  ],
  "rules": [
    "No targeting low-level players",
    "Honor surrender requests"
  ],
  "duration": 604800000,
  "stakes": {
    "territory": true,
    "resources": 10000,
    "influence": 500
  }
}
```

#### Get War Information
```http
GET /api/alliance-wars/{warId}
```

Retrieves war details and current status.

### Alliance Chat

#### Send Message
```http
POST /api/alliance-chat/{allianceId}/send
```

Sends a message to alliance chat.

**Request Body:**
```json
{
  "senderId": "player_123",
  "channel": "general",
  "content": "Hello alliance members!"
}
```

#### Get Chat History
```http
GET /api/alliance-chat/{allianceId}/history
```

Retrieves alliance chat history.

**Query Parameters:**
- `channel` (optional): Filter by channel
- `limit` (optional): Maximum messages (default: 50)
- `before` (optional): Get messages before this timestamp

## Guild Activities Endpoints

### Guild Events

#### Create Event
```http
POST /api/guild-events/create
```

Creates a new guild event.

**Request Body:**
```json
{
  "guildId": "guild_abc123",
  "title": "Weekly Raid Night",
  "description": "Join us for our weekly raid on Icecrown Citadel",
  "type": "raid",
  "startTime": "2024-01-20T20:00:00Z",
  "duration": 180,
  "maxParticipants": 25,
  "requirements": {
    "minLevel": 60,
    "gearScore": 5000
  },
  "rewards": {
    "experience": 1000,
    "gold": 500,
    "items": ["epic_gem_001"]
  }
}
```

#### Register for Event
```http
POST /api/guild-events/{eventId}/register
```

Registers a player for an event.

**Request Body:**
```json
{
  "playerId": "player_123",
  "teamData": {
    "teamId": "team_alpha",
    "role": "tank"
  }
}
```

#### Update Event Progress
```http
POST /api/guild-events/{eventId}/progress
```

Updates progress for an active event.

**Request Body:**
```json
{
  "playerId": "player_123",
  "progressData": [
    {
      "objectiveId": 1,
      "progress": 5,
      "completed": true
    }
  ],
  "timeSpent": 3600
}
```

#### Get Guild Events
```http
GET /api/guild-events/guild/{guildId}
```

Retrieves events for a guild.

### Guild Quests

#### Create Quest
```http
POST /api/guild-quests/create
```

Creates a new guild quest.

**Request Body:**
```json
{
  "guildId": "guild_abc123",
  "title": "Dragon Slaying Challenge",
  "description": "Defeat 5 dragons as a guild",
  "type": "defeat",
  "difficulty": "hard",
  "objectives": [
    {
      "type": "defeat",
      "description": "Defeat dragons",
      "target": "dragon_001",
      "required": 5
    }
  ],
  "requirements": {
    "minLevel": 50,
    "minRank": "Member"
  },
  "rewards": {
    "experience": 2000,
    "gold": 1000,
    "guildContribution": 100
  },
  "timeLimit": 604800000,
  "maxParticipants": 50,
  "repeatable": true
}
```

#### Accept Quest
```http
POST /api/guild-quests/{questId}/accept
```

Accepts a guild quest.

**Request Body:**
```json
{
  "playerId": "player_123"
}
```

#### Update Quest Progress
```http
POST /api/guild-quests/{questId}/progress
```

Updates quest progress.

**Request Body:**
```json
{
  "playerId": "player_123",
  "progressData": [
    {
      "objectiveId": 1,
      "progress": 2,
      "completed": false,
      "data": {
        "enemiesDefeated": ["dragon_001", "dragon_002"]
      }
    }
  ],
  "timeSpent": 7200
}
```

## Management Endpoints

### Guild Dashboard

#### Get Dashboard
```http
GET /api/guild-management/{guildId}/dashboard
```

Retrieves comprehensive guild dashboard data.

**Query Parameters:**
- `timeRange` (optional): Time range for analytics (1h, 24h, 7d, 30d)

### Member Management

#### Bulk Member Operations
```http
POST /api/guild-management/{guildId}/members/bulk
```

Performs bulk operations on members.

**Request Body:**
```json
{
  "operation": "promote",
  "targets": ["player_456", "player_789"],
  "newRank": "Veteran",
  "reason": "Activity and contribution"
}
```

#### Get Activity Report
```http
GET /api/guild-management/{guildId}/activity-report
```

Generates member activity report.

### Treasury Management

#### Collect Taxes
```http
POST /api/guild-management/{guildId}/treasury/collect-taxes
```

Collects guild taxes from members.

#### Generate Treasury Report
```http
GET /api/guild-management/{guildId}/treasury/report
```

Generates treasury report.

**Query Parameters:**
- `period` (optional): Report period (weekly, monthly, quarterly)

### Export Data

#### Export Guild Data
```http
POST /api/guild-management/{guildId}/export
```

Exports guild data.

**Request Body:**
```json
{
  "format": "json",
  "sections": ["members", "bank", "events"],
  "dateRange": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  },
  "includeSensitive": false
}
```

## Error Codes

| Code | Description |
|------|-------------|
| VALIDATION_ERROR | Invalid input data |
| PERMISSION_DENIED | Insufficient permissions |
| NOT_FOUND | Resource not found |
| ALREADY_EXISTS | Resource already exists |
| GUILD_FULL | Guild has reached member limit |
| INSUFFICIENT_FUNDS | Insufficient funds for operation |
| RATE_LIMITED | Too many requests |
| INTERNAL_ERROR | Server error |

## Rate Limits

API requests are rate-limited to prevent abuse:

- **Standard endpoints**: 1000 requests per hour
- **Upload/Modification endpoints**: 100 requests per hour
- **Export endpoints**: 10 requests per hour

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248600
```

## Webhooks

### Guild Events

The system can send webhook notifications for various guild events:

**Member Joined**
```json
{
  "event": "member_joined",
  "guildId": "guild_abc123",
  "data": {
    "playerId": "player_456",
    "playerName": "NewPlayer",
    "rank": "Member"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Guild Level Up**
```json
{
  "event": "guild_level_up",
  "guildId": "guild_abc123",
  "data": {
    "oldLevel": 4,
    "newLevel": 5
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Configure webhooks in your guild settings or via the API:
```http
POST /api/guilds/{guildId}/webhooks
```

## SDKs and Libraries

### JavaScript/Node.js
```bash
npm install @dmln8n/guild-management-sdk
```

```javascript
const GuildManagement = require('@dmln8n/guild-management-sdk');

const client = new GuildManagement({
  apiKey: 'your-api-key',
  baseUrl: 'https://your-domain.com/api'
});

// Create a guild
const guild = await client.guilds.create({
  name: 'My Guild',
  tag: 'MYGD',
  leaderId: 'player_123'
});
```

### Python
```bash
pip install dmln8n-guild-management
```

```python
from dmln8n_guild_management import GuildManagementClient

client = GuildManagementClient(
    api_key='your-api-key',
    base_url='https://your-domain.com/api'
)

# Get guild members
members = client.guilds.get_members('guild_abc123')
```

For more detailed examples and advanced usage, see the SDK documentation.