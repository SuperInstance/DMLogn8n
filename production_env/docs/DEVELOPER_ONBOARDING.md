# DMLog Developer Onboarding Guide

## Welcome to DMLog!

DMLog is an AI-powered D&D character learning system that enables NPCs to genuinely improve from gameplay experiences. This guide will help you get set up and productive quickly.

## Table of Contents

1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Development Setup](#development-setup)
4. [Architecture Deep Dive](#architecture-deep-dive)
5. [Daily Workflow](#daily-workflow)
6. [Testing Guidelines](#testing-guidelines)
7. [Code Standards](#code-standards)
8. [Deployment Process](#deployment-process)
9. [Troubleshooting](#troubleshooting)
10. [Resources](#resources)

## System Overview

DMLog consists of multiple services working together:

- **API Server** (FastAPI): Main application logic and REST endpoints
- **ML Training Service**: LoRA fine-tuning for character learning
- **PostgreSQL**: Primary data store for all application data
- **Redis**: Caching and job queue management
- **Qdrant**: Vector database for semantic search and memory
- **Nginx**: Load balancer and reverse proxy
- **Monitoring Stack**: Prometheus, Grafana, ELK for observability

## Prerequisites

### Hardware Requirements

**Minimum Requirements:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 20GB free space
- OS: Ubuntu 20.04+, macOS 12+, Windows 11 with WSL2

**Recommended for ML Development:**
- CPU: 8+ cores
- RAM: 16GB+
- GPU: NVIDIA RTX 4050 or better (with 8GB+ VRAM)
- CUDA 11.8+ installed

### Software Requirements

1. **Docker & Docker Compose**
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Python 3.11** (if not using Docker)
   ```bash
   # Using pyenv recommended
   pyenv install 3.11.7
   pyenv global 3.11.7
   ```

3. **Git**
   ```bash
   sudo apt-get install git  # Ubuntu/Debian
   brew install git          # macOS
   ```

4. **VS Code** (recommended) with extensions:
   - Python
   - Docker
   - Pylance
   - GitLens
   - Thunder Client (API testing)

### Account Setup

1. **GitHub Account**
   - Request access to the repository
   - Set up SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

2. **API Keys** (request from team)
   - OpenAI API Key
   - Anthropic API Key

## Development Setup

### 1. Clone the Repository

```bash
git clone git@github.com:yourorg/dmlog.git
cd dmlog
```

### 2. Environment Configuration

```bash
# Copy environment template
cp production_env/config/.env.template .env

# Edit with your configuration
vim .env
```

Required environment variables:
```bash
# API Keys
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Database (for development)
DATABASE_URL=postgresql://dmlog_user:dmlog_password@localhost:5432/dmlog_dev
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333

# Development Settings
ENVIRONMENT=development
LOG_LEVEL=debug
DEBUG=true
```

### 3. Start Development Environment

```bash
# Start all services
docker-compose -f production_env/docker/docker-compose.dev.yml up -d

# View logs
docker-compose -f production_env/docker/docker-compose.dev.yml logs -f

# Stop services
docker-compose -f production_env/docker/docker-compose.dev.yml down
```

### 4. Verify Setup

Open your browser and navigate to:
- API Documentation: http://localhost:8000/docs
- Grafana Dashboard: http://localhost:3001 (admin/admin)
- PgAdmin: http://localhost:8080 (admin@dmlog.dev/admin)
- Redis Commander: http://localhost:8081

### 5. Run First Test

```bash
# Run unit tests
docker-compose -f production_env/docker/docker-compose.dev.yml exec api pytest tests/unit/ -v

# Run integration tests
docker-compose -f production_env/docker/docker-compose.dev.yml exec api pytest tests/integration/ -v
```

## Architecture Deep Dive

### Code Structure

```
dmlog/
├── source_code/backend/
│   ├── api_server.py          # FastAPI application entry
│   ├── game_mechanics.py      # D&D 5e rules engine
│   ├── character_brain.py     # Character logic
│   ├── llm_api_integration.py # LLM provider interfaces
│   ├── memory_system.py       # Episodic memory
│   ├── training_data_collector.py # Data collection
│   ├── vector_memory.py       # Semantic search
│   └── tests/                 # Test suite
├── production_env/
│   ├── docker/               # Docker configurations
│   ├── scripts/              # Utility scripts
│   ├── config/               # Configuration files
│   └── terraform/            # Infrastructure as code
└── docs/                     # Documentation
```

### Key Components

1. **Layer 1: Foundation**
   - Game mechanics implementation
   - Character definitions
   - Basic NPC management

2. **Layer 2: Intelligence**
   - Decision-making engines
   - LLM integration
   - Model routing logic

3. **Layer 3: Consolidation**
   - Memory systems
   - Pattern extraction
   - Behavior analysis

4. **Phase 7: Learning Pipeline**
   - Training data collection
   - LoRA fine-tuning
   - Model deployment

### Data Flow

```mermaid
graph LR
    A[Game Action] --> B[Decision Engine]
    B --> C[LLM API]
    C --> D[Action Taken]
    D --> E[Outcome Tracker]
    E --> F[Training Data]
    F --> G[ML Training]
    G --> H[Improved Model]
    H --> B
```

## Daily Workflow

### 1. Start Your Day

```bash
# Pull latest changes
git pull origin main

# Start dev environment (if not running)
docker-compose -f production_env/docker/docker-compose.dev.yml up -d

# Check service status
docker-compose -f production_env/docker/docker-compose.dev.yml ps

# View recent logs
docker-compose -f production_env/docker/docker-compose.dev.yml logs --tail=100 api
```

### 2. Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Edit code with hot-reload enabled
   - Changes automatically reflect without restart

3. **Run tests frequently**
   ```bash
   # Quick test run
   docker-compose -f production_env/docker/docker-compose.dev.yml exec api pytest tests/unit/test_your_feature.py -v
   ```

4. **Commit your changes**
   ```bash
   # Check formatting
   docker-compose -f production_env/docker/docker-compose.dev.yml exec api black .
   docker-compose -f production_env/docker/docker-compose.dev.yml exec api isort .

   # Run linting
   docker-compose -f production_env/docker/docker-compose.dev.yml exec api flake8 .

   # Commit
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub
   ```

### 3. Debugging

```bash
# Attach debugger to API
docker-compose -f production_env/docker/docker-compose.dev.yml exec api bash

# View real-time logs
docker-compose -f production_env/docker/docker-compose.dev.yml logs -f api

# Check database
docker-compose -f production_env/docker/docker-compose.dev.yml exec postgres psql -U dmlog_user -d dmlog_dev

# Redis CLI
docker-compose -f production_env/docker/docker-compose.dev.yml exec redis redis-cli
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Fast, isolated tests
│   ├── test_game_mechanics.py
│   ├── test_character_brain.py
│   └── test_memory_system.py
├── integration/    # Service integration tests
│   ├── test_api_endpoints.py
│   ├── test_llm_integration.py
│   └── test_database_integration.py
├── e2e/           # End-to-end tests
│   ├── test_full_character_flow.py
│   └── test_training_pipeline.py
└── fixtures/      # Test data
    ├── characters.json
    └── scenarios.json
```

### Writing Tests

```python
# unit/test_character_brain.py
import pytest
from backend.character_brain import CharacterBrain

@pytest.fixture
def character():
    return CharacterBrain(name="Test Character", class="Fighter", level=5)

@pytest.fixture
def brain(character):
    return CharacterBrain(character=character)

def test_character_decision(brain):
    """Test that character can make valid decisions"""
    context = {"situation": "combat", "enemies": ["goblin"]}
    decision = brain.make_decision(context)

    assert decision is not None
    assert "action" in decision
    assert decision["action"] in ["attack", "defend", "flee"]

@pytest.mark.asyncio
async def test_async_llm_call(brain):
    """Test async LLM integration"""
    response = await brain.query_llm("What should I do?")
    assert response is not None
    assert len(response) > 0
```

### Running Tests

```bash
# All unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/ --cov=backend --cov-report=html

# Specific test file
pytest tests/unit/test_character_brain.py::test_character_decision -v

# Integration tests
pytest tests/integration/ -v

# E2E tests (slower)
pytest tests/e2e/ -v -s
```

## Code Standards

### Python Style Guide

We follow PEP 8 with some modifications:

1. **Line Length**: 100 characters
2. **Imports**: Group and sort (isort handles this)
3. **Docstrings**: Google style
4. **Type Hints**: Required for all functions

```python
"""Example of code style."""

from typing import Dict, List, Optional

class CharacterBrain:
    """Manages character decision-making and learning.

    Attributes:
        character: The character instance
        memory: Episodic memory storage
        model: Current decision model
    """

    def __init__(self, character: Character, memory: Optional[Memory] = None):
        """Initialize the character brain.

        Args:
            character: Character instance
            memory: Optional memory storage
        """
        self.character = character
        self.memory = memory or Memory()
        self.model = self._load_model()

    async def make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make a decision based on context.

        Args:
            context: Current game situation

        Returns:
            Decision dictionary with action and reasoning
        """
        # Implementation here
        pass
```

### Git Commit Messages

We use Conventional Commits:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(api): add character decision endpoint

- Add POST /characters/{id}/decisions
- Include validation and error handling
- Update API documentation

Closes #123
```

### Code Review Process

1. **Self-Review Checklist**
   - [ ] Code is formatted (black, isort)
   - [ ] Tests pass locally
   - [ ] Documentation updated
   - [ ] No TODO comments left
   - [ ] No hardcoded values
   - [ ] Error handling implemented

2. **Review Focus Areas**
   - Logic correctness
   - Performance implications
   - Security considerations
   - Test coverage
   - Documentation clarity

## Deployment Process

### Local Deployment

```bash
# Build production images
docker-compose -f production_env/docker/docker-compose.prod.yml build

# Deploy locally
docker-compose -f production_env/docker/docker-compose.prod.yml up -d
```

### Staging Deployment

Staging is automatically deployed on merge to `develop` branch.

### Production Deployment

Production deployment requires:
1. Approval from at least 2 team members
2. All tests passing
3. Manual verification on staging
4. Create GitHub release with version number

### Rollback Procedure

```bash
# View deployment history
kubectl rollout history deployment/api

# Rollback to previous version
kubectl rollout undo deployment/api

# Verify rollback
kubectl get pods -l app=api
```

## Troubleshooting

### Common Issues

**1. Docker container won't start**
```bash
# Check logs
docker-compose logs service_name

# Check resource usage
docker stats

# Rebuild container
docker-compose build --no-cache service_name
```

**2. Database connection errors**
```bash
# Check if PostgreSQL is running
docker-compose exec postgres pg_isready

# Check connection string
echo $DATABASE_URL

# Reset database (development only)
docker-compose down -v
docker-compose up -d postgres
```

**3. GPU not accessible**
```bash
# Check NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Check CUDA version
nvidia-smi

# Verify Docker runtime
docker info | grep nvidia
```

**4. High memory usage**
```bash
# Check container memory
docker stats

# Limit memory in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G
```

**5. Tests failing**
```bash
# Run with verbose output
pytest -v -s tests/failing_test.py

# Run with debugger
pytest --pdb tests/failing_test.py

# Check test database
docker-compose exec postgres psql -U dmlog_user -d dmlog_test
```

### Performance Debugging

```bash
# Profile Python code
python -m cProfile -o profile.stats your_script.py

# Memory profiling
pip install memory-profiler
python -m memory_profiler your_script.py

# Database slow queries
SELECT query, mean_time, calls
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### Getting Help

1. **Slack Channels**
   - #dev-team: General development
   - #alerts: Production issues
   - #architecture: Design discussions

2. **Documentation**
   - Architecture docs: `/docs/`
   - API docs: http://localhost:8000/docs
   - Runbook: `/docs/runbook.md`

3. **Code Review**
   - Request review on GitHub PR
   - Tag relevant team members
   - Provide context in PR description

## Resources

### Internal Documentation

- [System Architecture](../DEVELOPMENT_ENVIRONMENT_ARCHITECTURE.md)
- [Database Schema](../DATABASE_MIGRATION_STRATEGY.md)
- [API Reference](http://localhost:8000/docs)
- [Monitoring Guide](../MONITORING_SETUP.md)

### External Tools

- **Grafana**: https://grafana.dmlog.com
- **Kibana**: https://logs.dmlog.com
- **Prometheus**: https://prometheus.dmlog.com
- **Model Registry**: https://models.dmlog.com

### Learning Resources

1. **FastAPI Documentation**: https://fastapi.tiangolo.com
2. **PostgreSQL Tutorial**: https://www.postgresqltutorial.com
3. **Redis Guide**: https://redis.io/documentation
4. **Docker Best Practices**: https://docs.docker.com/develop/dev-best-practices

### Team Contacts

- **Tech Lead**: [Name] - [email]
- **DevOps**: [Name] - [email]
- **ML Team**: [Name] - [email]

---

## Quick Start Checklist

- [ ] Hardware meets requirements
- [ ] Software installed (Docker, Git)
- [ ] Repository cloned
- [ ] Environment configured
- [ ] Development environment running
- [ ] Tests passing
- [ ] IDE configured with extensions
- [ ] Slack access requested
- [ ] API keys obtained
- [ ] Documentation read

Welcome aboard! We're excited to have you on the DMLog team. 🎲