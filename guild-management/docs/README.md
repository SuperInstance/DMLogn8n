# DMlogn8n Guild Management System

A comprehensive guild and alliance management system for DMlogn8n that provides extensive guild features, alliance coordination, and automated workflows.

## Overview

The Guild Management System offers a complete solution for managing guilds and alliances within your DMlogn8n instance. It includes hierarchical guild structures, alliance systems, activity coordination, and automated n8n workflows for seamless operations.

## Features

### Guild Structure
- **Guild Creation**: Create guilds with custom charters and requirements
- **Hierarchical Ranks**: Leader, Officer, Veteran, Member, Initiate with custom permissions
- **Custom Roles**: Create unlimited custom roles with specific permissions
- **Guild Banks**: Multi-tab storage with permissions and transaction logging
- **Guild Halls**: Upgradeable halls with facilities and decorations

### Guild Features
- **Shared Storage**: Organized guild bank with role-based access
- **Communication**: Guild chat, voice channels, and announcements
- **Group Activities**: Events, quests, and social gatherings
- **Guild Services**: Vendors, training facilities, and member services
- **Customization**: Emblems, banners, and guild identity

### Alliance System
- **Multi-Guild Alliances**: Form alliances with shared goals and resources
- **Diplomatic Relations**: Complex relationship management between alliances
- **Coordination**: Shared chat, events, and resource trading
- **Alliance Wars**: Large-scale conflicts between alliances
- **Leadership**: Alliance councils and voting systems

### Guild Activities
- **Dynamic Quests**: Guild-specific quests with objectives and rewards
- **Group Dungeons**: Organized raid and dungeon runs
- **PvP Tournaments**: Guild and alliance competitions
- **Social Events**: Ceremonies, meetings, and gatherings
- **Achievement System**: Guild milestones and recognition

### Management Tools
- **Member Management**: Comprehensive member administration tools
- **Activity Tracking**: Detailed member contribution and activity monitoring
- **Treasury Management**: Guild bank management with taxes and contributions
- **Recruitment**: Application processing and onboarding workflows
- **Conflict Resolution**: Dispute management and voting systems

## Installation

### Prerequisites
- Node.js 16 or higher
- MongoDB 4.4 or higher
- n8n instance
- Discord or voice chat integration (optional)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd DMlogn8n/guild-management
```

2. **Install dependencies**
```bash
npm install
```

3. **Database Setup**
```bash
# Run database migration
node database/migrations/initial-setup.js
```

4. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your database and service configurations
```

5. **Import n8n Workflows**
- Import workflows from `/workflows/` directory into your n8n instance
- Configure webhook endpoints and service connections

6. **Start the Services**
```bash
npm start
```

## Configuration

### Environment Variables

```env
# Database Configuration
MONGODB_URI=mongodb://localhost:27017/dmln8n
MONGODB_DB_NAME=dmln8n

# Service Configuration
GUILD_SERVICE_PORT=3001
ALLIANCE_SERVICE_PORT=3002
NOTIFICATION_SERVICE_PORT=3003

# External Services
DISCORD_BOT_TOKEN=your_discord_token
VOICE_SERVICE_URL=http://localhost:3010
INVENTORY_SERVICE_URL=http://localhost:3011

# n8n Configuration
N8N_WEBHOOK_URL=http://localhost:5678/webhook
N8N_API_KEY=your_n8n_api_key

# Security
JWT_SECRET=your_jwt_secret
API_RATE_LIMIT=1000
```

### Guild Settings

Configure default guild settings in `/config/guild-settings.json`:

```json
{
  "defaultSettings": {
    "memberLimit": 100,
    "bankAccess": "officers",
    "inviteOnly": false,
    "voiceChatRequired": false,
    "activityRequirement": 0
  },
  "rankHierarchy": {
    "Leader": 100,
    "Officer": 75,
    "Veteran": 50,
    "Member": 25,
    "Initiate": 10
  },
  "permissions": {
    "invite_members": ["Leader", "Officer"],
    "kick_members": ["Leader", "Officer"],
    "promote_members": ["Leader", "Officer"],
    "manage_bank": ["Leader", "Officer"],
    "manage_settings": ["Leader"]
  }
}
```

## API Reference

### Guild Management

#### Create Guild
```http
POST /api/guilds/create
Content-Type: application/json

{
  "name": "Dragon Slayers",
  "tag": "DRGN",
  "description": "A guild dedicated to dragon hunting",
  "charter": "Our charter text here...",
  "leaderId": "player_123",
  "requirements": {
    "minLevel": 10,
    "approvalRequired": true
  }
}
```

#### Get Guild Information
```http
GET /api/guilds/{guildId}
```

#### Add Member
```http
POST /api/guilds/{guildId}/members
Content-Type: application/json

{
  "playerId": "player_456",
  "rank": "Member",
  "note": "Recruited through application"
}
```

#### Get Guild Members
```http
GET /api/guilds/{guildId}/members?rank=Officer&status=active&limit=50
```

### Alliance Management

#### Create Alliance
```http
POST /api/alliances/create
Content-Type: application/json

{
  "name": "United Front",
  "tag": "UNITED",
  "description": "Alliance for mutual defense",
  "creatorGuildId": "guild_123",
  "requirements": {
    "minGuildLevel": 5,
    "maxGuilds": 8,
    "votingRequired": true
  }
}
```

#### Apply to Alliance
```http
POST /api/alliances/{allianceId}/apply
Content-Type: application/json

{
  "guildId": "guild_456",
  "message": "We wish to join your alliance",
  "contribution": {
    "military": "strong",
    "resources": "moderate"
  }
}
```

### Guild Bank Operations

#### Deposit Gold
```http
POST /api/guild-banks/{guildId}/deposit/gold
Content-Type: application/json

{
  "playerId": "player_123",
  "amount": 1000,
  "note": "Donation for guild upgrades"
}
```

#### Withdraw Item
```http
POST /api/guild-banks/{guildId}/withdraw/item
Content-Type: application/json

{
  "playerId": "player_123",
  "itemId": "item_456",
  "quantity": 5,
  "tabId": "equipment",
  "reason": "For raid preparation"
}
```

### Guild Events

#### Create Event
```http
POST /api/guild-events/create
Content-Type: application/json

{
  "guildId": "guild_123",
  "title": "Weekly Raid Night",
  "description": "Join us for our weekly raid",
  "type": "raid",
  "startTime": "2024-01-15T20:00:00Z",
  "duration": 180,
  "maxParticipants": 25
}
```

## n8n Workflows

### Available Workflows

1. **Guild Member Onboarding**
   - Processes new member applications
   - Validates requirements
   - Handles approvals and rejections
   - Automated welcome sequences

2. **Guild Activity Monitoring**
   - Monitors guild activity levels
   - Generates alerts for inactivity
   - Creates activity reports
   - Suggests engagement activities

3. **Guild Bank Automation**
   - Weekly maintenance processing
   - Tax collection
   - Low balance alerts
   - Automated reporting

4. **Alliance Application Processing**
   - Handles alliance applications
   - Manages voting processes
   - Auto-approval for qualified applicants
   - Notifications and follow-ups

5. **Alliance War Coordination**
   - War declaration processing
   - Force organization
   - Resource allocation
   - Communication setup

### Workflow Configuration

Each workflow includes:
- Webhook triggers for external systems
- Database operations for data persistence
- Notification systems for user communication
- Error handling and retry logic
- Logging and audit trails

## Database Schema

### Core Collections

- **guilds**: Guild information and settings
- **guild_members**: Member data and status
- **guild_ranks**: Custom rank definitions
- **guild_banks**: Guild bank storage
- **guild_halls**: Guild hall information
- **alliances**: Alliance data
- **alliance_applications**: Membership applications
- **guild_events**: Event information
- **guild_quests**: Quest data
- **guild_chat**: Chat message logs

### Relationships

```
guilds (1) → (n) guild_members
guilds (1) → (1) guild_banks
guilds (1) → (1) guild_halls
alliances (1) → (n) guilds
guilds (1) → (n) guild_events
guilds (1) → (n) guild_quests
```

## Security Considerations

### Authentication
- JWT-based authentication for API access
- Role-based permissions for guild operations
- Secure webhook validation for n8n workflows

### Authorization
- Granular permission system for guild ranks
- Alliance-level permissions for cross-guild operations
- Audit logging for sensitive operations

### Data Protection
- Input validation and sanitization
- Rate limiting on API endpoints
- Encrypted sensitive data storage
- Regular security audits

## Performance Optimization

### Database Optimization
- Properly indexed collections
- Query optimization for common operations
- Caching for frequently accessed data
- Connection pooling

### Application Performance
- Asynchronous operations where possible
- Efficient data structures
- Lazy loading for large datasets
- Background processing for intensive tasks

### Monitoring
- Performance metrics collection
- Error tracking and alerting
- Database query performance monitoring
- API response time tracking

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check MongoDB connection string
   - Verify database is running
   - Check network connectivity

2. **Permission Errors**
   - Verify user has appropriate guild rank
   - Check role permissions configuration
   - Review audit logs for permission issues

3. **Workflow Failures**
   - Check n8n webhook configuration
   - Verify service endpoints are accessible
   - Review workflow execution logs

4. **Performance Issues**
   - Monitor database query performance
   - Check for missing indexes
   - Review application logs for bottlenecks

### Debug Mode

Enable debug logging by setting:
```env
DEBUG=*
LOG_LEVEL=debug
```

### Support

For support and bug reports:
- Create an issue in the project repository
- Include relevant logs and error messages
- Provide steps to reproduce the issue
- Include system information (Node.js version, MongoDB version, etc.)

## Contributing

We welcome contributions to the Guild Management System! Please read our contributing guidelines and submit pull requests for any improvements.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Style

- Follow ESLint configuration
- Use meaningful variable names
- Add comments for complex logic
- Include JSDoc for functions and classes

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Changelog

See CHANGELOG.md for a detailed history of changes and updates.

## Credits

Developed for the DMlogn8n project with contributions from the community.