# DMLog - Dungeons & Dragons Campaign Management System

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-15+-blue.svg" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Redis-7+-red.svg" alt="Redis">
  <img src="https://img.shields.io/badge/Docker-20+-blue.svg" alt="Docker">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

DMLog is a comprehensive Dungeons & Dragons campaign management system with AI-powered character automation. Built with modern Python async patterns, it provides real-time session tracking, character management, and campaign organization tools for both Dungeon Masters and players.

## ✨ Features

### 🎭 Character Management
- Create and manage D&D characters with full stats and background
- Track character memories with importance scoring
- Log and analyze character decisions with confidence metrics
- Character leveling and progression tracking
- Support for all D&D 5e classes and races

### 📚 Campaign Organization
- Create and manage multiple campaigns
- Session scheduling and tracking
- Campaign world building and lore management
- Player character assignment to campaigns
- Campaign statistics and analytics

### 🎲 Real-Time Sessions
- WebSocket-based real-time session updates
- Live dice rolling and skill checks
- Combat tracking and initiative management
- Session transcripts and summaries
- Multi-user support for players and DMs

### 🤖 AI Integration (Planned)
- AI-powered character decision making
- Automatic memory consolidation
- Cultural transmission between characters
- Dynamic narrative generation
- Character personality evolution

### 📊 Monitoring & Analytics
- Prometheus metrics collection
- Grafana dashboards for visualization
- Performance monitoring
- Resource usage tracking
- Custom analytics and reporting

## 🏗️ Architecture

DMLog is built with a modern, scalable architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   PostgreSQL    │
│   (Dashboard)   │◄──►│   Backend       │◄──►│   Database      │
│                 │    │                 │    │                 │
│ - HTML/JS/CSS  │    │ - Async/await   │    │ - Async Driver  │
│ - Bootstrap 5   │    │ - Pydantic      │    │ - Migrations    │
│ - WebSocket     │    │ - Middleware    │    │ - Connection    │
│                 │    │ - Validation    │    │   Pooling       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Redis       │    │    Qdrant       │
                       │     Cache       │    │  Vector DB      │
                       │                 │    │                 │
                       │ - Session Store │    │ - Memory        │
                       │ - Query Cache   │    │   Embeddings    │
                       │ - Pub/Sub       │    │ - Similarity    │
                       │                 │    │   Search        │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- Git for cloning the repository
- 4GB+ RAM and 20GB+ storage recommended

### One-Command Deployment

```bash
# Clone and deploy in one command
git clone https://github.com/dmlog/dmlog.git && cd dmlog && ./deploy.sh development
```

That's it! DMLog will automatically:
- ✅ Set up all services (PostgreSQL, Redis, API, Frontend)
- ✅ Run database migrations
- ✅ Start monitoring tools
- ✅ Open your browser to the application

**🎉 Access Points:**
- **🎮 Main Dashboard**: http://localhost:3000
- **📚 API Documentation**: http://localhost:8000/docs
- **📊 Monitoring**: http://localhost:3001 (admin/admin)

**📖 Need help?** Check our [Quick Start Guide](docs/QUICK_START.md) for detailed instructions.

## 📁 Project Structure

```
DMLog/
├── source_code/
│   ├── backend/               # FastAPI backend
│   │   ├── api/              # API routes and schemas
│   │   ├── cache/            # Redis caching layer
│   │   ├── database/         # Database models and repos
│   │   ├── monitoring/       # Metrics collection
│   │   └── config/           # Configuration
│   └── frontend/             # Web dashboard
│       ├── index.html        # Main dashboard
│       └── app.js            # Frontend logic
├── production_env/
│   ├── docker/               # Docker configurations
│   ├── grafana/              # Monitoring dashboards
│   └── nginx/                # Reverse proxy config
├── scripts/                  # Utility scripts
├── tests/                    # Test suite
├── migrations/               # Database migrations
└── docs/                     # Documentation
```

## 🔧 Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and customize:

```env
# Application
APP_NAME=DMLog
APP_VERSION=1.0.0
DEBUG=false
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dmlog

# Redis
REDIS_URL=redis://host:6379/0

# AI Services
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=https://yourdomain.com
```

## 📚 Documentation

**📖 Complete Documentation**: [Documentation Suite](docs/README.md)

### Quick Links

| Audience | Document | Description |
|----------|----------|-------------|
| 👥 **Users** | [User Manual](docs/user/user-manual.md) | Learn how to use DMLog |
| 🚀 **Quick Start** | [Quick Start Guide](docs/QUICK_START.md) | Get running in minutes |
| 🛠️ **Developers** | [Contributing Guide](docs/developer/contributing-guide.md) | Contribute to DMLog |
| 🏗️ **Technical** | [Technical Architecture](docs/technical/architecture.md) | System design and architecture |
| 🚀 **Deployment** | [Deployment Guide](docs/technical/deployment-guide.md) | Deploy to production |
| 🔍 **API Reference** | [API Documentation](docs/technical/openapi.yaml) | Complete API reference |
| 🐛 **Troubleshooting** | [Troubleshooting Guide](docs/technical/troubleshooting.md) | Common issues and solutions |
| 🔒 **Security** | [Security Policy](SECURITY.md) | Security information and reporting |
| 📋 **Changelog** | [CHANGELOG.md](CHANGELOG.md) | Version history and changes |

### API Overview

**🎯 Interactive API Docs**: http://localhost:8000/docs (after deployment)

#### Core Endpoints

| Resource | Endpoints | Description |
|----------|-----------|-------------|
| **Characters** | `/api/v1/characters/` | Manage D&D characters |
| **Campaigns** | `/api/v1/campaigns/` | Campaign organization |
| **Sessions** | `/api/v1/sessions/` | Session management |
| **Health** | `/api/v1/health/` | System health checks |

#### WebSocket API

```javascript
// Connect to real-time updates
const ws = new WebSocket('ws://localhost:8000/ws/connect?user_id=your_id');

// Join a session
ws.send(JSON.stringify({
    type: 'join',
    data: { session_id: 'session-123' }
}));
```

**🔍 Try the API**: After deployment, visit http://localhost:8000/docs for interactive API documentation.

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=source_code/backend --cov-report=html

# Run specific tests
pytest tests/test_characters.py
```

## 📊 Monitoring

### Prometheus Metrics

Metrics are exposed at `/metrics`:

- HTTP request count and duration
- Database query performance
- Cache hit rates
- Active WebSocket connections
- System resource usage

### Grafana Dashboards

Pre-configured dashboards include:
- Application Overview
- Database Performance
- Cache Analytics
- System Resources

Access: http://localhost:3001 (admin/admin)

## 🚀 Deployment

### Development

```bash
./deploy.sh development
```

### Production

```bash
./deploy.sh production
```

### AWS EC2

```bash
./deploy.sh aws-ec2 latest ec2-user@your-instance.com
```

### NVIDIA Jetson

```bash
./deploy.sh jetson
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 🔄 Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🛠️ Development

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r source_code/backend/requirements_full.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn source_code/backend.api_server_new:app --reload
```

### Code Style

The project uses:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

```bash
# Format code
black source_code/backend/
isort source_code/backend/

# Lint code
flake8 source_code/backend/

# Type check
mypy source_code/backend/
```

## 📈 Roadmap

### Week 1-2: Foundation ✅
- [x] Database schema and models
- [x] API server with FastAPI
- [x] Basic CRUD operations
- [x] Caching layer with Redis
- [x] Monitoring with Prometheus/Grafana
- [x] WebSocket support
- [x] Basic frontend dashboard

### Week 3-4: Core Features
- [ ] Advanced character management
- [ ] Session recording and playback
- [ ] Dice rolling system
- [ ] Combat tracking
- [ ] Skill challenges

### Week 5-6: AI Integration
- [ ] QLoRA model training
- [ ] Character personality AI
- [ ] Decision-making engine
- [ ] Memory consolidation
- [ ] Cultural transmission

### Week 7-8: Advanced Features
- [ ] Campaign templates
- [ ] Custom homebrew content
- [ ] Integration with D&D Beyond
- [ ] Voice chat support
- [ ] Mobile app

### Week 9-10: Polish & Launch
- [ ] Performance optimization
- [ ] Security audit
- [ ] Documentation
- [ ] User testing
- [ ] Production deployment

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** - Modern, fast web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **PostgreSQL** - Powerful relational database
- **Redis** - In-memory data structure store
- **Docker** - Container platform
- **Bootstrap** - Frontend UI framework

## 📞 Support

For support:
- Create an issue on GitHub
- Check the [documentation](docs/)
- Join our Discord community

## 🗺️ Changelog

### v1.0.0 (2024-01-22)
- Initial release
- Core CRUD operations
- WebSocket support
- Basic monitoring
- Deployment scripts

---

Made with ❤️ by the DMLog team