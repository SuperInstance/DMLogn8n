# Cross-Portal Communication System

A comprehensive real-time communication and data synchronization system that enables seamless messaging and data exchange between all D&D campaign portals.

## Features

### 🔗 Message Routing Engine
- **Real-time message distribution** between portals with WebSocket support
- **Priority-based message queuing** (Emergency, Critical, High, Normal, Low)
- **Message filtering and permissions** with role-based access control
- **Broadcast and direct messaging** capabilities
- **Message history and logging** with persistence

### 📡 Event Broadcasting System
- **Game state change notifications** for real-time updates
- **Combat event distribution** with detailed combat logging
- **Character action broadcasting** for player actions
- **DM directive propagation** for Dungeon Master commands
- **System-wide announcements** for important notifications

### 🔄 Data Synchronization
- **Character state sync** across all portals in real-time
- **World state consistency** with conflict resolution
- **Real-time inventory updates** with validation
- **Spell effect coordination** between combat and character portals
- **Combat state alignment** with automatic synchronization

### 💬 Communication Channels
- **Party chat channel** for general player communication
- **DM-to-character whispers** for private communication
- **Coder channel** for automation and technical discussions
- **System notifications channel** for important updates
- **Out-of-character discussions** for non-game talk

### 🔐 Security & Permissions
- **Role-based access control** (DM, Player, Coder, Spectator, System)
- **Message encryption** for sensitive communications
- **Comprehensive audit logging** for security monitoring
- **Rate limiting** to prevent abuse
- **Content moderation** and filtering

## Architecture

```
Cross-Portal Communication System
├── Core Components
│   ├── MessageRouter      - Routes messages between portals
│   ├── EventBroadcaster   - Broadcasts game events
│   ├── DataSyncManager    - Synchronizes data across portals
│   ├── ChannelManager     - Manages communication channels
│   └── SecurityManager    - Handles authentication and authorization
├── Handlers
│   └── WebSocketHandler   - WebSocket connection management
├── Services
│   ├── RedisService       - Pub/sub and caching
│   └── MessagePersistenceService - Database operations
└── Integration
    └── PortalIntegrationService - External portal connections
```

## Installation

### Prerequisites
- Node.js 18+
- MongoDB 4.4+
- Redis 6.0+

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd cross-portal-communication

# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env

# Configure your environment variables
nano .env

# Build the project
npm run build

# Start the system
npm start
```

### Environment Configuration
```env
# Server Configuration
PORT=3001
HOST=localhost
WS_PORT=3002

# Database Configuration
DATABASE_URI=mongodb://localhost:27017/cross-portal-comm

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Security
JWT_SECRET=your-super-secret-jwt-key
ENCRYPTION_KEY=your-32-character-encryption-key-123456

# Portal URLs
DM_PORTAL_URL=http://localhost:3000
PLAYER_PORTAL_URL=http://localhost:3001
CODER_PORTAL_URL=http://localhost:3002
COMBAT_PORTAL_URL=http://localhost:3003
CHARACTER_PORTAL_URL=http://localhost:3004
```

## API Documentation

### Authentication
```http
POST /api/auth
Content-Type: application/json

{
  "username": "dm",
  "password": "password"
}
```

### Send Message
```http
POST /api/messages
Authorization: Bearer <token>
Content-Type: application/json

{
  "channel": "party",
  "content": "Hello everyone!",
  "recipients": [],
  "metadata": {}
}
```

### Get Messages
```http
GET /api/messages?channel=party&limit=50
Authorization: Bearer <token>
```

### Get Channels
```http
GET /api/channels
Authorization: Bearer <token>
```

### Join Channel
```http
POST /api/channels/{channelId}/join
Authorization: Bearer <token>
```

### Health Check
```http
GET /health
```

### System Status
```http
GET /status
```

## WebSocket API

### Connection
```javascript
const ws = new WebSocket('ws://localhost:3002');

// Authentication challenge
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'auth_challenge') {
    // Respond with authentication
    ws.send(JSON.stringify({
      type: 'auth_response',
      data: {
        token: 'your-jwt-token',
        userId: 'user-id',
        username: 'username',
        role: 'dm',
        portal: 'dm-portal'
      }
    }));
  }
};
```

### Message Types
- `auth_response` - Authentication response
- `chat_message` - Send chat message
- `channel_join` - Join a channel
- `channel_leave` - Leave a channel
- `heartbeat` - Keep-alive ping
- `subscribe_events` - Subscribe to event types
- `get_history` - Request message history

## Configuration

### Message Priorities
- **Emergency (4)**: Critical system alerts
- **Critical (3)**: Combat events, DM directives
- **High (2)**: Character updates, important notifications
- **Normal (1)**: Regular chat messages
- **Low (0)**: Typing indicators, status updates

### Rate Limiting
- **Default**: 100 messages per 15 minutes per user
- **DMs**: 500 messages per 15 minutes
- **System**: Unlimited

### Message History
- **In-memory**: Last 100 messages per channel
- **Database**: Configurable retention (default 90 days)
- **Archive**: Messages older than 30 days are archived

## Portal Integration

### DM Portal
- Real-time campaign management
- Player communication
- Combat control
- World state management

### Player Portal
- Character sheet access
- Party chat
- Dice rolling
- Inventory management

### Coder Portal
- Automation scripting
- API documentation
- Debugging tools
- System monitoring

### Combat Portal
- Turn-based combat
- Initiative tracking
- Damage calculation
- Effect management

### Character Portal
- Character creation
- Sheet management
- Level progression
- Equipment tracking

## Security Features

### Authentication
- JWT-based authentication
- Session management
- Automatic token refresh
- Secure logout

### Authorization
- Role-based permissions
- Channel access control
- Message filtering
- Content validation

### Encryption
- Message encryption for sensitive channels
- Data-in-transit protection
- Key rotation
- Secure key storage

### Audit Logging
- Comprehensive event logging
- Security incident tracking
- User activity monitoring
- Compliance reporting

## Monitoring and Analytics

### System Metrics
- Message throughput
- Connection counts
- Response times
- Error rates

### Performance Monitoring
- Memory usage
- CPU utilization
- Database performance
- Redis statistics

### Health Checks
- Service availability
- Portal connectivity
- Database health
- Resource limits

## Development

### Running in Development
```bash
npm run dev
```

### Running Tests
```bash
npm test
npm run test:watch
```

### Building
```bash
npm run build
```

### Linting
```bash
npm run lint
npm run lint:fix
```

## Troubleshooting

### Common Issues

#### Redis Connection Failed
- Check Redis server is running
- Verify connection settings in .env
- Check network connectivity

#### MongoDB Connection Failed
- Ensure MongoDB is running
- Check database URI configuration
- Verify authentication credentials

#### WebSocket Connection Issues
- Check port availability
- Verify firewall settings
- Check WebSocket URL configuration

#### Authentication Failures
- Verify JWT secret configuration
- Check token expiration
- Validate user credentials

### Logs
- Application logs: `logs/cross-portal-comm.log`
- Error logs: `logs/error.log`
- Debug logs available in development mode

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting guide