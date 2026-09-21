#!/usr/bin/env bash

# DMLog Development Environment Setup Script
# This script sets up the complete development environment for DMLog

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="DMLog"
PYTHON_VERSION="3.11"
MIN_DOCKER_VERSION="20.10.0"
MIN_NODE_VERSION="18.0.0"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if running on supported OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi

    log_success "Operating system: $OS"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi

    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | sed 's/,//')
    if ! printf '%s\n%s\n' "$MIN_DOCKER_VERSION" "$DOCKER_VERSION" | sort -V -C; then
        log_error "Docker version $DOCKER_VERSION is too old. Please upgrade to $MIN_DOCKER_VERSION or later."
        exit 1
    fi

    log_success "Docker version: $DOCKER_VERSION"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose."
        exit 1
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python $PYTHON_VERSION or later."
        exit 1
    fi

    PYTHON_VER=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if ! printf '%s\n%s\n' "$MIN_PYTHON_VERSION" "$PYTHON_VER" | sort -V -C; then
        log_error "Python version $PYTHON_VER is too old. Please upgrade to $MIN_PYTHON_VERSION or later."
        exit 1
    fi

    log_success "Python version: $PYTHON_VER"

    # Check Node.js (optional, for frontend)
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version | cut -d'v' -f2)
        log_success "Node.js version: $NODE_VERSION (optional for frontend)"
    else
        log_warning "Node.js is not installed. You'll need it for frontend development."
    fi

    # Check git
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed. Please install Git."
        exit 1
    fi

    log_success "Git version: $(git --version)"
}

create_project_structure() {
    log_info "Creating project directory structure..."

    # Main directories
    mkdir -p {
        source_code/{backend/{api,routers,database,cache,monitoring,config,ml,tests},frontend},
        production_env/{docker,scripts,config,terraform,monitoring,docs,tests},
        data/{characters,sessions,models,backups,logs},
        docs/{api,user,dev,deployment},
        scripts/{dev,deploy,migration},
        tests/{unit,integration,e2e,fixtures}
    }

    # Create .env files
    cat > source_code/backend/.env.template << 'EOF'
# Application Configuration
APP_NAME=DMLog API
APP_VERSION=1.0.0
DEBUG=true
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://dmlog_user:dmlog_password@localhost:5432/dmlog_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant Vector Database
QDRANT_URL=http://localhost:6333

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM API Keys (REQUIRED)
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Logging
LOG_LEVEL=debug
LOG_FILE=./logs/dmlog.log

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760

# Performance
MAX_CONNECTIONS=100
CONNECTION_TIMEOUT=30
EOF

    # Create development environment file
    cp source_code/backend/.env.template source_code/backend/.env.development

    # Create test environment file
    cat > source_code/backend/.env.test << 'EOF'
APP_NAME=DMLog Test
DEBUG=true
ENVIRONMENT=test
DATABASE_URL=sqlite+aiosqlite:///:memory:
REDIS_URL=redis://localhost:6379/15
QDRANT_URL=http://localhost:6334
SECRET_KEY=test-secret-key
LOG_LEVEL=debug
OPENAI_API_KEY=test-key
ANTHROPIC_API_KEY=test-key
EOF

    # Create requirements.txt
    cat > source_code/backend/requirements.txt << 'EOF'
# Core Dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.13.0

# Redis
redis[hiredis]==5.0.1
aioredis==2.0.1

# Vector Database
qdrant-client==1.7.0

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# HTTP Client
httpx==0.25.2
aiohttp==3.9.1

# Monitoring & Metrics
prometheus-client==0.19.0
psutil==5.9.6

# Development & Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.7.1

# Machine Learning
torch==2.1.1
transformers==4.36.0
peft==0.7.1
bitsandbytes==0.41.3
accelerate==0.25.0
datasets==2.15.0
sentence-transformers==2.2.2
scikit-learn==1.3.2
numpy==1.25.2
pandas==2.1.4

# Utilities
python-dotenv==1.0.0
structlog==23.2.0
rich==13.7.0
typer==0.9.0
EOF

    # Create pytest configuration
    cat > source_code/backend/pytest.ini << 'EOF'
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=.
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
asyncio_mode = auto
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    redis: marks tests that require Redis
    database: marks tests that require database
EOF

    # Create .gitignore
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# poetry
poetry.lock

# celery beat schedule file
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
logs/
data/
uploads/
models/
backups/
*.db
*.sqlite3

# Docker
docker-compose.override.yml
.env.local
.env.production

# Node.js (if using)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.eslintcache
EOF

    log_success "Project structure created"
}

setup_python_environment() {
    log_info "Setting up Python environment..."

    cd source_code/backend

    # Create virtual environment
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    log_info "Activating virtual environment..."
    source venv/bin/activate

    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel

    # Install dependencies
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt

    # Install pre-commit hooks
    log_info "Installing pre-commit hooks..."
    pip install pre-commit

    # Create pre-commit configuration
    cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=100, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports]
EOF

    pre-commit install

    log_success "Python environment setup complete"
}

setup_docker_environment() {
    log_info "Setting up Docker environment..."

    cd ../../production_env/docker

    # Create development docker-compose file
    cat > docker-compose.dev.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: dmlog_postgres_dev
    environment:
      POSTGRES_DB: dmlog_dev
      POSTGRES_USER: dmlog_user
      POSTGRES_PASSWORD: dmlog_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data_dev:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    networks:
      - dmlog_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dmlog_user -d dmlog_dev"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: dmlog_redis_dev
    ports:
      - "6379:6379"
    volumes:
      - redis_data_dev:/data
    networks:
      - dmlog_network
    restart: unless-stopped
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:v1.6.0
    container_name: dmlog_qdrant_dev
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data_dev:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__LOG_LEVEL=DEBUG
    networks:
      - dmlog_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:6333/health || exit 1"]
      interval: 5s
      timeout: 5s
      retries: 5

  # API Server
  api:
    build:
      context: ../../source_code
      dockerfile: production_env/docker/Dockerfile.dev
    container_name: dmlog_api_dev
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://dmlog_user:dmlog_password@postgres:5432/dmlog_dev
      - REDIS_URL=redis://redis:6379/0
      - QDRANT_URL=http://qdrant:6333
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ENVIRONMENT=development
      - LOG_LEVEL=debug
      - RELOAD=true
    volumes:
      - ../../source_code:/app
      - api_logs_dev:/app/logs
    networks:
      - dmlog_network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_healthy
    restart: unless-stopped
    command: uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload --log-level debug

networks:
  dmlog_network:
    driver: bridge

volumes:
  postgres_data_dev:
  redis_data_dev:
  qdrant_data_dev:
  api_logs_dev:
EOF

    # Create development Dockerfile
    cat > Dockerfile.dev << 'EOF'
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r dmlog && useradd -r -g dmlog dmlog

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY ../../source_code/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=dmlog:dmlog ../../source_code/backend /app

# Create logs directory
RUN mkdir -p /app/logs && chown dmlog:dmlog /app/logs

# Switch to non-root user
USER dmlog

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    log_success "Docker environment configured"
}

initialize_database() {
    log_info "Initializing database..."

    cd ../../source_code/backend

    # Create database initialization script
    cat > scripts/init_db.py << 'EOF'
#!/usr/bin/env python3
"""
Database initialization script
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from database.connection import get_database
from database.migrations import MigrationManager

async def init_database():
    """Initialize database with migrations"""
    print("🚀 Initializing database...")

    # Get database connection
    database = get_database()
    database.initialize()

    # Create migration manager
    migration_manager = MigrationManager(database)

    # Run migrations
    await migration_manager.migrate_up()

    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_database())
EOF

    chmod +x scripts/init_db.py

    # Create scripts directory if it doesn't exist
    mkdir -p scripts

    log_success "Database initialization script created"
}

create_sample_data() {
    log_info "Creating sample data scripts..."

    cd source_code/backend

    # Create sample data script
    cat > scripts/create_sample_data.py << 'EOF'
#!/usr/bin/env python3
"""
Create sample data for development
"""
import asyncio
import sys
from pathlib import Path
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from database.connection import get_database
from database.models import Character, Campaign, Session, Memory, Decision

async def create_sample_data():
    """Create sample characters, campaigns, and sessions"""
    print("🎲 Creating sample D&D data...")

    database = get_database()
    database.initialize()

    async with database.get_session() as session:
        # Create sample campaign
        campaign = Campaign(
            name="The Lost Mine of Phandelver",
            description="A beginner's adventure in the Forgotten Realms",
            dm_id="dm_001",
            world_lore={
                "setting": "Forgotten Realms",
                "region": "Sword Coast",
                "starting_location": "Neverwinter"
            },
            house_rules=[
                "No evil characters",
                "Collaborative storytelling encouraged"
            ]
        )
        session.add(campaign)
        await session.commit()
        await session.refresh(campaign)

        print(f"✅ Created campaign: {campaign.name}")

        # Create sample characters
        characters_data = [
            {
                "name": "Thorin Ironforge",
                "race": "dwarf",
                "character_class": "fighter",
                "level": 1,
                "strength": 16,
                "dexterity": 12,
                "constitution": 14,
                "intelligence": 10,
                "wisdom": 13,
                "charisma": 8,
                "personality_traits": ["Brave", "Loyal", "Honorable"],
                "backstory": "A dwarven warrior from the clan Ironforge, seeking glory and treasure.",
                "alignment": "Lawful Good"
            },
            {
                "name": "Elena Starweaver",
                "race": "elf",
                "character_class": "wizard",
                "level": 1,
                "strength": 8,
                "dexterity": 14,
                "constitution": 12,
                "intelligence": 16,
                "wisdom": 13,
                "charisma": 11,
                "personality_traits": ["Curious", "Studious", "Eccentric"],
                "backstory": "An elven mage from the High Forest, studying ancient magic.",
                "alignment": "Neutral Good"
            },
            {
                "name": "Rook Shadowstep",
                "race": "human",
                "character_class": "rogue",
                "level": 1,
                "strength": 10,
                "dexterity": 16,
                "constitution": 12,
                "intelligence": 12,
                "wisdom": 11,
                "charisma": 14,
                "personality_traits": "Sly", "Charming", "Opportunistic",
                "backstory": "A charismatic rogue from the streets of Waterdeep.",
                "alignment": "Chaotic Neutral"
            }
        ]

        created_characters = []
        for char_data in characters_data:
            character = Character(**char_data)
            session.add(character)
            await session.commit()
            await session.refresh(character)
            created_characters.append(character)
            print(f"✅ Created character: {character.name} ({character.race} {character.character_class})")

        # Create sample session
        session_obj = Session(
            campaign_id=campaign.id,
            session_number=1,
            title="Into the Unknown",
            phase="active",
            start_time=datetime.utcnow(),
            session_notes="The party meets in Neverwinter and accepts a job to escort supplies to Phandalin."
        )
        session.add(session_obj)
        await session.commit()
        await session.refresh(session_obj)

        print(f"✅ Created session: {session_obj.title}")

        # Add characters to session
        for character in created_characters:
            from database.models import SessionParticipant
            participant = SessionParticipant(
                session_id=session_obj.id,
                character_id=character.id,
                joined_at=datetime.utcnow()
            )
            session.add(participant)

        await session.commit()

        # Create sample memories for each character
        for character in created_characters:
            memories = [
                Memory(
                    character_id=character.id,
                    memory_type="episodic",
                    content=f"Met the party in Neverwinter's Yawning Portal inn",
                    context={"location": "Neverwinter", "event": "party_meeting"},
                    importance=0.8,
                    emotional_valence=0.5
                ),
                Memory(
                    character_id=character.id,
                    memory_type="semantic",
                    content="Gundren Rockseeker hired us to escort supplies to Phandalin",
                    context={"quest_giver": "Gundren Rockseeker", "destination": "Phandalin"},
                    importance=0.9,
                    emotional_valence=0.3
                )
            ]

            for memory in memories:
                session.add(memory)

            print(f"✅ Created memories for {character.name}")

        # Create sample decisions
        decisions = [
            {
                "character": created_characters[0],  # Thorin
                "description": "Offered to take first watch during the night",
                "reasoning": "As a dwarf, I'm naturally vigilant and protective of the group",
                "source": "human",
                "confidence": 0.9,
                "success": True,
                "quality_score": 0.8
            },
            {
                "character": created_characters[1],  # Elena
                "description": "Identified mysterious magical runes on an old chest",
                "reasoning": "My magical training allows me to recognize ancient script",
                "source": "bot",
                "confidence": 0.85,
                "success": True,
                "quality_score": 0.9
            },
            {
                "character": created_characters[2],  # Rook
                "description": "Successfully pickpocketed a key from the suspicious merchant",
                "reasoning": "The merchant was hiding something and I needed to find out what",
                "source": "bot",
                "confidence": 0.75,
                "success": True,
                "quality_score": 0.7
            }
        ]

        for decision_data in decisions:
            decision = Decision(
                character_id=decision_data["character"].id,
                session_id=session_obj.id,
                decision_type="social",
                description=decision_data["description"],
                reasoning=decision_data["reasoning"],
                source=decision_data["source"],
                confidence=decision_data["confidence"],
                success=decision_data["success"],
                quality_score=decision_data["quality_score"],
                created_at=datetime.utcnow()
            )
            session.add(decision)
            print(f"✅ Created decision for {decision_data['character'].name}")

        await session.commit()

        print("\n🎉 Sample data creation complete!")
        print(f"Created {len(created_characters)} characters, 1 campaign, 1 session, and multiple memories/decisions")

if __name__ == "__main__":
    asyncio.run(create_sample_data())
EOF

    chmod +x scripts/create_sample_data.py

    log_success "Sample data script created"
}

run_health_checks() {
    log_info "Running health checks..."

    # Check if all services are running
    cd ../../production_env/docker

    if docker-compose -f docker-compose.dev.yml ps | grep -q "Up"; then
        log_success "Docker services are running"
    else
        log_warning "Docker services are not running. Start them with:"
        echo "  cd production_env/docker"
        echo "  docker-compose -f docker-compose.dev.yml up -d"
    fi

    # Check if API is accessible
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        log_success "API is accessible at http://localhost:8000"
    else
        log_warning "API is not accessible. Start it with:"
        echo "  cd source_code/backend"
        echo "  source venv/bin/activate"
        echo "  uvicorn api_server:app --reload"
    fi
}

print_next_steps() {
    log_success "Setup complete! 🎉"
    echo
    echo "Next steps:"
    echo "1. Configure your API keys in source_code/backend/.env.development"
    echo "2. Start the development environment:"
    echo "   cd production_env/docker"
    echo "   docker-compose -f docker-compose.dev.yml up -d"
    echo "3. Initialize the database:"
    echo "   cd ../../source_code/backend"
    echo "   source venv/bin/activate"
    echo "   python scripts/init_db.py"
    echo "4. Create sample data (optional):"
    echo "   python scripts/create_sample_data.py"
    echo "5. Access the API documentation: http://localhost:8000/docs"
    echo "6. Run tests: pytest"
    echo
    echo "For development commands, see:"
    echo "- make help (in project root)"
    echo "- python scripts/dev_tools.py --help"
    echo
    echo "Happy coding! 🚀"
}

# Main execution
main() {
    echo "🎲 DMLog Development Environment Setup"
    echo "====================================="
    echo

    check_prerequisites
    create_project_structure
    setup_python_environment
    setup_docker_environment
    initialize_database
    create_sample_data
    run_health_checks
    print_next_steps
}

# Run main function
main "$@"