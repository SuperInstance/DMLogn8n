# Multi-Portal Gateway System for DMlogn8n

A comprehensive multi-portal gateway system that creates dedicated portals for each character, DM, and developer, providing real-time communication, state management, and automation capabilities.

## System Architecture

The system consists of several key components:

### 1. Portal Gateway Service (Port 8000)
- **FastAPI backend** managing all portal connections
- **Dynamic port allocation** (9000-9500 for characters, 9501 for DM, 9502 for coder workshop)
- **WebSocket routing** to each portal
- **Portal lifecycle management** (create, monitor, destroy)
- **Load balancing and failover**
- **Cross-portal communication bridge**

### 2. Character Portal Servers (Ports 9000-9500)
- **Individual port for each character**
- **Terminal emulation with status bars**
- **Real-time character state display**
- **Command input/output handling**
- **Human control override capability**
- **AI personality and decision making**

### 3. DM Portal Server (Port 9501)
- **Real-time game monitoring**
- **World editing interface**
- **Encounter designer**
- **Event injection system**
- **Character management**
- **Game state control**

### 4. Coder Workshop Portal (Port 9502)
- **Code editing interface**
- **AI code generation integration**
- **Script management system**
- **Testing sandbox**
- **Deployment system**
- **Real-time collaboration**

### 5. Portal Communication Bridge
- **Inter-portal messaging**
- **Event broadcasting**
- **State synchronization**
- **Cross-portal actions**
- **Security and permissions**

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- At least 8GB RAM
- 20GB free disk space

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd DMlogn8n/multi-portal-gateway
```

2. **Make the startup script executable:**
```bash
chmod +x scripts/start-system.sh
chmod +x scripts/stop-system.sh
chmod +x scripts/restart-system.sh
```

3. **Start the system:**
```bash
./scripts/start-system.sh --build
```

This will:
- Build all Docker images
- Start PostgreSQL, Redis, and Ollama services
- Pull AI models (llama2, codellama)
- Start the gateway and portal services
- Start the frontend and monitoring tools

### Access Points

Once the system is running, you can access:

- **Frontend Dashboard**: http://localhost:3000
- **Gateway API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **DM Portal**: http://localhost:9501
- **Coder Workshop**: http://localhost:9502
- **N8N Workflows**: http://localhost:5678 (admin/password)
- **Prometheus Monitoring**: http://localhost:9090
- **Grafana Dashboards**: http://localhost:3001 (admin/admin)

## Features

### Character Portals
- **Dynamic Character Management**: Each character gets their own dedicated portal
- **Terminal Emulation**: Command-line interface with game-specific commands
- **Real-time State Display**: HP, MP, status, inventory, and abilities
- **AI Personality**: Characters have unique behaviors and decision-making patterns
- **Human Override**: DMs or players can take direct control at any time
- **Port Range**: 9000-9500 (up to 500 character portals)

### DM Portal
- **World Management**: Create and edit game locations, environments, and settings
- **Encounter Designer**: Build complex encounters with creatures, objectives, and rewards
- **Event Injection**: Inject story events, weather changes, and world events
- **Character Monitoring**: Real-time view of all character states and activities
- **Game Control**: Pause, resume, save, and restore game sessions
- **Real-time Updates**: All changes immediately reflected across all portals

### Coder Workshop
- **AI Code Generation**: Generate code using LLMs (Ollama integration)
- **Script Management**: Create, schedule, and execute custom scripts
- **Testing Sandbox**: Safe environment for testing code changes
- **Deployment System**: Deploy changes to live system with rollback capability
- **Collaborative Editing**: Real-time code collaboration features
- **Version Control**: Track changes and maintain code history

### Communication Bridge
- **Event Broadcasting**: Send events to specific portals or all portals
- **Message Routing**: Intelligent routing of messages between portals
- **State Synchronization**: Keep all portals in sync
- **Security Controls**: Role-based access and permissions
- **Message History**: Track all inter-portal communications

## API Documentation

### Gateway Endpoints

#### Portal Management
- `GET /portals` - List all active portals
- `POST /portals/{portal_type}` - Create a new portal
- `DELETE /portals/{portal_id}` - Destroy a portal
- `GET /portals/{portal_id}/status` - Get portal status

#### Communication
- `POST /bridge/broadcast` - Broadcast message to portals
- `GET /stats` - Get system statistics
- `GET /health` - Health check endpoint

#### WebSocket Connections
- `WS /ws/{portal_id}` - Portal-specific WebSocket connection
- `WS /ws/bridge` - Communication bridge WebSocket

### Character Portal Endpoints

#### Character Management
- `GET /character` - Get character information
- `POST /character/action` - Perform character action
- `POST /character/state` - Update character state
- `POST /character/chat` - Send chat message

#### Terminal Interface
- `POST /terminal/command` - Execute terminal command
- `GET /terminal/history` - Get command history

#### Control
- `POST /override/human` - Enable human override
- `POST /override/disable` - Disable human override

### DM Portal Endpoints

#### World Management
- `GET /world` - Get current world state
- `POST /world/update` - Update world state
- `POST /world/location/create` - Create new location
- `GET /world/locations` - List all locations

#### Encounter System
- `GET /encounters` - List all encounters
- `POST /encounters/create` - Create new encounter
- `POST /encounters/{id}/start` - Start encounter
- `POST /encounters/{id}/end` - End encounter

#### Events
- `POST /events/inject` - Inject game event
- `GET /events/pending` - Get pending events
- `POST /events/{id}/resolve` - Resolve event

### Coder Portal Endpoints

#### Code Editor
- `GET /editor/files` - List editable files
- `GET /editor/file/{path}` - Get file content
- `POST /editor/file/{path}` - Save file

#### AI Integration
- `POST /ai/generate` - Generate code with AI
- `POST /ai/improve` - Improve existing code
- `POST /ai/explain` - Explain code

#### Scripts
- `GET /scripts` - List all scripts
- `POST /scripts/create` - Create new script
- `POST /scripts/{id}/execute` - Execute script
- `POST /scripts/{id}/schedule` - Schedule script

## N8N Workflows

The system includes pre-built n8n workflows for automation:

### Portal Automation
- **Character Portal Creation**: Automatically creates and configures character portals
- **Portal Health Monitoring**: Monitors portal health and restarts failed portals
- **Dynamic Scaling**: Automatically scales resources based on demand

### Event Handling
- **Character Action Router**: Routes character actions to appropriate handlers
- **World Event Processor**: Processes and distributes world events
- **Combat Manager**: Handles combat mechanics and state updates

### System Monitoring
- **Health Checks**: Continuous health monitoring of all services
- **Performance Metrics**: Collects and analyzes performance data
- **Alert System**: Sends alerts for system issues

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database Configuration
DATABASE_URL=postgresql://dmlogn8n:password@localhost:5432/portal_gateway

# Redis Configuration
REDIS_URL=redis://localhost:6379

# AI Service Configuration
AI_SERVICE_URL=http://localhost:11434
AI_MODEL=llama2

# Gateway Configuration
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8000
DEBUG=false

# Portal Port Ranges
CHARACTER_PORT_START=9000
CHARACTER_PORT_END=9500
DM_PORT=9501
CODER_PORT=9502

# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/portal_gateway.log
```

### Docker Configuration

The system uses Docker Compose for orchestration. Key services:

- **gateway**: Main FastAPI application
- **postgres**: PostgreSQL database
- **redis**: Redis for caching and sessions
- **ollama**: AI service for code generation
- **dm-portal**: Dungeon Master portal
- **coder-portal**: Coder workshop portal
- **frontend**: React frontend application
- **n8n**: Workflow automation
- **nginx**: Reverse proxy
- **prometheus**: Monitoring
- **grafana**: Visualization

## Development

### Local Development

1. **Set up Python environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Start databases:**
```bash
docker-compose up -d postgres redis ollama
```

3. **Run the gateway:**
```bash
cd gateway
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. **Run frontend:**
```bash
cd frontend
npm install
npm start
```

### Running Tests

```bash
# Python tests
pytest tests/

# Frontend tests
cd frontend
npm test

# Integration tests
pytest tests/integration/
```

### Code Style

The project uses:
- **Black** for Python code formatting
- **ESLint** for JavaScript code formatting
- **Flake8** for Python linting
- **MyPy** for Python type checking

## Monitoring and Logging

### Logs
- **Gateway logs**: `logs/portal_gateway.log`
- **Portal logs**: Individual portal logs in respective directories
- **System logs**: Docker container logs

### Metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001

Key metrics tracked:
- Portal count and status
- Active connections
- Message throughput
- Response times
- Error rates
- Resource usage

### Health Checks

- **Gateway**: `GET /health`
- **Individual portals**: `GET /status`
- **System overall**: Check all services via Docker

## Security

### Authentication
- JWT tokens for API access
- Session management for WebSocket connections
- Role-based access control

### Network Security
- Rate limiting on all endpoints
- CORS configuration
- SSL/TLS support (configurable)
- Firewall rules for port access

### Data Protection
- Encrypted data storage
- Secure WebSocket connections
- Environment variable protection
- Audit logging

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8000, 9501, 9502, and 9000-9500 are available
2. **Memory issues**: Ollama requires significant RAM for AI models
3. **Database connection**: Check PostgreSQL is running and accessible
4. **WebSocket connections**: Verify firewall allows WebSocket traffic

### Debug Commands

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f [service_name]

# Restart services
docker-compose restart [service_name]

# Check resource usage
docker stats

# Test API connectivity
curl http://localhost:8000/health
```

## Support

For support and issues:
1. Check the logs for error messages
2. Review the troubleshooting section
3. Check system health endpoints
4. Review Grafana dashboards for system metrics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Version History

- **v1.0.0**: Initial release with complete multi-portal system
- **v1.1.0**: Added AI code generation and enhanced automation
- **v1.2.0**: Improved monitoring and performance optimizations

---

Built for the DMlogn8n project - enabling immersive multi-character D&D experiences with advanced automation and AI integration.