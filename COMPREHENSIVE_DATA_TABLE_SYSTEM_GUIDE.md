# DMlogn8n Comprehensive Data Table System Guide

## Overview

This guide provides complete documentation for the DMlogn8n comprehensive data table system, which includes real-time character management, scene state tracking, campaign world management, and multi-client synchronization with conflict resolution.

## System Architecture

### Core Components

1. **Character State Tables** - Dynamic character data management
2. **Game Scene Management** - Scene data and description system
3. **Campaign World State** - Persistent world data management
4. **Real-Time Sync System** - Multi-client state broadcasting and conflict resolution
5. **Google Sheets Backend** - Data persistence and validation
6. **WebSocket Communication** - Real-time updates to connected clients

### Data Flow

```
Client Applications → n8n Workflows → Google Sheets → WebSocket Broadcast → All Connected Clients
```

## Installation and Setup

### Prerequisites

1. **n8n Instance** - Running on http://localhost:5678
2. **Python 3.8+** - For setup and management scripts
3. **Google Cloud Project** - With Google Sheets API enabled
4. **Service Account Credentials** - For Google Sheets access

### Step 1: Google Sheets Setup

1. Create a Google Cloud Project
2. Enable Google Sheets API
3. Create a service account
4. Download JSON credentials file
5. Place credentials at `~/.config/gspread/credentials.json`

```bash
# Run the Google Sheets setup script
cd /home/activeloguser/DMLogn8n
python scripts/setup-google-sheets.py
```

This will create:
- **Character_State** table with HP/MP tracking, inventory, spells, XP
- **Scene_State** table with lighting, weather, objects, environmental effects
- **Campaign_State** table with locations, NPCs, factions, quests
- **Relationship_Matrix** table for NPC/faction relationships
- **Sync_Queue**, **Sync_History**, **Rollback_History** tables
- **Dashboard** with real-time statistics

### Step 2: Environment Configuration

Create environment variables:

```bash
export N8N_BASE_URL="http://localhost:5678"
export N8N_API_KEY="your-n8n-api-key"
export GOOGLE_SHEETS_CHARACTER_SHEET_ID="your-character-sheet-id"
export GOOGLE_SHEETS_SCENE_SHEET_ID="your-scene-sheet-id"
export GOOGLE_SHEETS_WORLD_SHEET_ID="your-world-sheet-id"
export GOOGLE_SHEETS_SYNC_SHEET_ID="your-sync-sheet-id"
```

### Step 3: Workflow Deployment

```bash
# Deploy all workflows to n8n
python /home/activeloguser/DMLogn8n/n8n-api-client.py
```

This will import and activate:
- `character-state-tables.json`
- `game-scene-management.json`
- `campaign-world-state.json`
- `real-time-sync-system.json`

## API Documentation

### Character Management

#### Create/Update Character
```http
POST /webhook/character/update
Content-Type: application/json

{
  "characterId": "char_001",
  "action": "create", // create, update, get, delete
  "name": "Character Name",
  "level": 5,
  "class": "Fighter",
  "hpCurrent": 45,
  "hpMax": 50,
  "mpCurrent": 20,
  "mpMax": 25,
  "xpCurrent": 3500,
  "xpToNext": 5000,
  "conditionChanges": [
    {
      "condition": "poisoned",
      "action": "add" // add, remove
    }
  ],
  "inventoryChanges": [
    {
      "action": "add", // add, remove
      "weight": 5.5,
      "value": 100.0
    }
  ],
  "spellUsage": [
    {
      "action": "cast", // cast, restore
      "slots": 1
    }
  ]
}
```

#### Character Regeneration
```http
POST /webhook/character/regeneration
Content-Type: application/json

{
  "characterId": "char_001",
  "hpRegenRate": 0.05, // 5% of max HP per interval
  "mpRegenRate": 0.10, // 10% of max MP per interval
  "intervalMinutes": 5
}
```

### Scene Management

#### Create/Update Scene
```http
POST /webhook/scene/update
Content-Type: application/json

{
  "sceneId": "scene_001",
  "action": "create", // create, update, get, delete
  "name": "Tavern Common Room",
  "baseDescription": "A warm, cozy tavern with wooden tables.",
  "lightingChanges": {
    "type": "dim"
  },
  "weatherChanges": {
    "type": "rain"
  },
  "objectStateChanges": [
    {
      "objectId": "fireplace",
      "state": "lit",
      "description": "A crackling fire burns in the hearth",
      "interactive": true
    }
  ],
  "environmentalEffects": [
    {
      "type": "magical_aura",
      "intensity": "moderate",
      "description": "A faint magical energy permeates the area"
    }
  ]
}
```

#### Scene Transition
```http
POST /webhook/scene/transition
Content-Type: application/json

{
  "fromSceneId": "scene_001",
  "toSceneId": "scene_002",
  "transitionType": "normal", // normal, combat, dramatic, subtle
  "duration": 5, // seconds
  "transitionDescription": "The party moves from the tavern to the dark forest.",
  "partyMembers": ["char_001", "char_002"],
  "preserveState": true
}
```

### Campaign World Management

#### Update World State
```http
POST /webhook/world/update
Content-Type: application/json

{
  "campaignId": "campaign_001",
  "action": "update", // update, create, get, delete
  "locationChanges": [
    {
      "locationId": "loc_001",
      "action": "add", // add, update, delete
      "data": {
        "name": "Greendale Village",
        "description": "A peaceful village in the valley",
        "type": "settlement",
        "coordinates": { "x": 100, "y": 200 },
        "discovered": true
      }
    }
  ],
  "npcChanges": [
    {
      "npcId": "npc_001",
      "action": "add",
      "data": {
        "name": "Barkeep Tom",
        "race": "human",
        "class": "commoner",
        "level": 1,
        "location": "loc_001",
        "faction": "neutral",
        "status": "alive"
      }
    }
  ],
  "factionChanges": [
    {
      "factionId": "fac_001",
      "action": "add",
      "data": {
        "name": "Merchants Guild",
        "type": "organization",
        "alignment": "neutral",
        "reputation": 0
      }
    }
  ],
  "questChanges": [
    {
      "questId": "quest_001",
      "action": "add",
      "data": {
        "name": "Missing Merchant",
        "description": "Find the missing merchant",
        "type": "main",
        "status": "available",
        "difficulty": "normal"
      }
    }
  ]
}
```

#### Update Relationships
```http
POST /webhook/world/relationships
Content-Type: application/json

{
  "campaignId": "campaign_001",
  "relationshipType": "npc-npc", // npc-npc, npc-faction, faction-faction, character-npc
  "entityId1": "npc_001",
  "entityId2": "char_001",
  "relationshipChange": "improve", // improve, deteriorate, set
  "value": 25, // -100 (hostile) to 100 (friendly)
  "reason": "Character helped the NPC"
}
```

### Real-Time Sync System

#### Sync Update
```http
POST /webhook/sync/update
Content-Type: application/json

{
  "clientId": "client_001",
  "sessionId": "session_001",
  "dataType": "character", // character, scene, world, campaign
  "entityId": "char_001",
  "updateData": {
    "hpCurrent": 30,
    "conditions": "injured,poisoned"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "priority": "normal", // low, normal, high, critical
  "conflictResolution": "timestamp" // timestamp, manual, merge
}
```

#### Rollback Update
```http
POST /webhook/sync/rollback
Content-Type: application/json

{
  "updateId": "update_123",
  "sessionId": "session_001",
  "reason": "Manual rollback requested by DM",
  "rollbackTo": "update_122" // timestamp or updateId to rollback to
}
```

#### Audit Trail
```http
POST /webhook/sync/audit
Content-Type: application/json

{
  "sessionId": "session_001",
  "clientId": "client_001",
  "timeRange": "24h", // 1h, 24h, 7d, 30d
  "dataType": "character", // optional filter
  "entityId": "char_001" // optional filter
}
```

## WebSocket Integration

### Connection URL
```
ws://localhost:5678/websocket
```

### Message Format
```json
{
  "type": "character_update|scene_update|world_update|scene_transition|sync_rollback",
  "data": {
    // Update-specific data
  },
  "channels": ["character_char_001", "game_updates", "dm_updates"],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Channel Subscriptions
- `character_{characterId}` - Character-specific updates
- `scene_{sceneId}` - Scene-specific updates
- `campaign_{campaignId}` - Campaign-specific updates
- `game_updates` - All game updates
- `dm_updates` - DM-only updates
- `sync_broadcast` - Sync system notifications
- `rollback_notifications` - Rollback notifications

## Data Validation

### Character Validation Rules
- **characterId**: Alphanumeric, 3-50 characters
- **name**: 1-100 characters, letters and spaces only
- **level**: Integer between 1 and 100
- **hpCurrent/hpMax**: Non-negative integers
- **mpCurrent/mpMax**: Non-negative integers
- **xpCurrent/xpToNext**: Non-negative integers

### Scene Validation Rules
- **sceneId**: Alphanumeric, 3-50 characters
- **name**: 1-200 characters
- **lighting**: One of: bright, normal, dim, dark, magical, flickering
- **weather**: One of: clear, rain, storm, fog, snow, wind, mist
- **visibility**: One of: excellent, good, moderate, poor
- **mood**: One of: peaceful, neutral, tense, mysterious, dramatic, ominous

### World Validation Rules
- **campaignId**: Alphanumeric, 3-50 characters
- **worldStatus**: One of: active, paused, completed, archived

## Automated Calculations

### Character Calculations
- **HP Percentage**: (current HP / max HP) × 100
- **MP Percentage**: (current MP / max MP) × 100
- **XP Percentage**: (current XP / XP to next) × 100
- **Encumbrance Status**: Based on inventory weight vs. carry capacity
- **Spell Recovery Rate**: Based on character level and class

### Scene Calculations
- **Visibility Modifier**: Based on lighting and weather conditions
- **Perception Difficulty**: Base difficulty + visibility modifier
- **Stealth Difficulty**: Base difficulty - visibility modifier
- **Mood Effects**: Bonuses/penalties based on scene mood and lighting

### Campaign Calculations
- **Discovery Percentage**: (discovered locations / total locations) × 100
- **Quest Completion Rate**: (completed quests / total quests) × 100
- **Campaign Progress**: Combined exploration and quest progress

## Import/Export Capabilities

### Export Campaign Data
```python
from scripts.import_export_capabilities import DataImportExportManager

manager = DataImportExportManager()
result = manager.export_campaign_data(
    campaign_id="campaign_001",
    data=campaign_data,
    format_type="json", // json, csv, xml, yaml
    compression="zip" // none, zip, gzip
)
```

### Import Campaign Data
```python
result = manager.import_campaign_data(
    file_path="exports/campaign_001_export.json",
    validate_data=True
)
```

### Create Backup
```python
result = manager.create_backup(
    campaign_id="campaign_001",
    data=campaign_data,
    backup_type="full" // full, incremental, differential
)
```

### Restore Backup
```python
result = manager.restore_backup(
    backup_file_path="exports/backups/backup_campaign_001_full_20240101_120000.json"
)
```

## Testing

### Run Integration Tests
```bash
cd /home/activeloguser/DMLogn8n
python scripts/test-integration.py
```

### Test Coverage
- ✅ n8n connection
- ✅ Workflow import
- ✅ Google Sheets integration
- ✅ Character workflow
- ✅ Scene workflow
- ✅ World workflow
- ✅ Sync workflow
- ✅ WebSocket communication
- ✅ Conflict resolution
- ✅ Data validation
- ✅ Rollback functionality
- ✅ Audit trail
- ✅ End-to-end flow

## Monitoring and Maintenance

### Dashboard Access
- **Google Sheets Dashboard**: Real-time statistics and metrics
- **n8n Monitoring**: Workflow execution logs and performance
- **WebSocket Monitoring**: Connected clients and message throughput

### Regular Maintenance Tasks
1. **Backup Campaigns**: Weekly automated backups
2. **Clean Old Data**: Archive old sync history and rollbacks
3. **Update Workflows**: Deploy workflow updates as needed
4. **Monitor Performance**: Check for bottlenecks and optimization opportunities

### Troubleshooting

#### Common Issues

**1. n8n Connection Failed**
```bash
# Check if n8n is running
curl http://localhost:5678/healthz

# Restart n8n if needed
n8n start
```

**2. Google Sheets Access Denied**
```bash
# Check credentials file
ls -la ~/.config/gspread/credentials.json

# Verify API access
python scripts/setup-google-sheets.py
```

**3. WebSocket Connection Issues**
```bash
# Check WebSocket endpoint
curl http://localhost:5678/webhook/websocket/test

# Verify n8n WebSocket workflow is active
```

**4. Data Validation Errors**
- Check data format against validation rules
- Verify required fields are present
- Ensure data types are correct

**5. Sync Conflicts**
- Review conflict resolution strategy
- Check timestamp consistency
- Verify client IDs are unique

## Performance Optimization

### Database Optimization
- Use appropriate data types in Google Sheets
- Implement data archiving for old records
- Optimize query patterns for large datasets

### WebSocket Optimization
- Implement message batching for high-frequency updates
- Use appropriate channels to reduce unnecessary broadcasts
- Monitor connection limits and implement connection pooling

### Workflow Optimization
- Use parallel processing where possible
- Implement caching for frequently accessed data
- Optimize Google Sheets API calls

## Security Considerations

### Data Protection
- Encrypt sensitive data at rest
- Use HTTPS for all API communications
- Implement proper authentication and authorization

### Access Control
- Role-based access to different data types
- Audit trail for all data modifications
- Rate limiting for API endpoints

### Backup Security
- Encrypt backup files
- Store backups in secure locations
- Regular backup integrity verification

## Extending the System

### Adding New Data Types
1. Create validation rules in `data-validation-calculations.py`
2. Add Google Sheets table structure
3. Create corresponding n8n workflow
4. Update import/export functionality
5. Add tests for new functionality

### Custom Conflict Resolution
1. Implement new resolution strategies
2. Update conflict detection logic
3. Add corresponding API endpoints
4. Test with various conflict scenarios

### Additional Notification Channels
1. Add new WebSocket channels
2. Implement external notification services
3. Create filtering and routing logic
4. Update client integration examples

## Support and Contributing

### Getting Help
- Review the troubleshooting section
- Check test results for guidance
- Examine workflow logs in n8n
- Review Google Sheets for data issues

### Contributing
1. Follow the existing code patterns
2. Add comprehensive tests
3. Update documentation
4. Test thoroughly before submitting

---

For additional support or questions, refer to the test reports and logs generated during setup and operation.