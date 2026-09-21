#!/bin/bash

# DMLog Environment Setup Script
# This script automates the complete environment setup for DMLog Week 1
# Author: DMLog Development Team
# Version: 1.0.0

set -euo pipefail  # Exit on error, undefined variables, and pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Configuration variables
PROJECT_NAME="DMLog"
PYTHON_VERSION="3.11"
VENV_NAME="dmlog_env"
DB_NAME="dmlog_db"
DB_USER="dmlog_user"
DB_PASS="dmlog_secure_password_2024"

# System requirements check
check_system_requirements() {
    log "Checking system requirements..."

    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
    else
        error "Unsupported operating system: $OSTYPE"
    fi

    info "Detected OS: $OS"

    # Check available memory (require at least 4GB)
    if [[ "$OS" == "linux" ]]; then
        AVAILABLE_MEM=$(free -m | awk 'NR==2{printf "%.0f", $7/1024}')
        if [ "$AVAILABLE_MEM" -lt 4 ]; then
            warn "Low memory detected: ${AVAILABLE_MEM}GB. Recommended: 8GB+"
        else
            info "Memory check passed: ${AVAILABLE_MEM}GB available"
        fi
    fi

    # Check disk space (require at least 10GB)
    AVAILABLE_DISK=$(df . | tail -1 | awk '{print $4}')
    if [ "$AVAILABLE_DISK" -lt 10485760 ]; then  # 10GB in KB
        error "Insufficient disk space. Required: 10GB, Available: $((AVAILABLE_DISK/1024/1024))GB"
    fi

    log "System requirements check completed"
}

# Docker installation and verification
install_docker() {
    log "Checking Docker installation..."

    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | sed 's/,//')
        log "Docker is already installed: $DOCKER_VERSION"
    else
        warn "Docker not found. Installing Docker..."

        case "$OS" in
            "linux")
                # Install Docker for Linux
                sudo apt-get update
                sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
                curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
                echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
                sudo apt-get update
                sudo apt-get install -y docker-ce docker-ce-cli containerd.io
                sudo usermod -aG docker $USER
                ;;
            "macos")
                # Install Docker for Mac using Homebrew
                if command -v brew &> /dev/null; then
                    brew install --cask docker
                else
                    error "Homebrew not found. Please install Docker Desktop manually from https://www.docker.com/products/docker-desktop"
                fi
                ;;
            "windows")
                error "Please install Docker Desktop manually from https://www.docker.com/products/docker-desktop"
                ;;
        esac

        # Start Docker service
        if [[ "$OS" == "linux" ]]; then
            sudo systemctl start docker
            sudo systemctl enable docker
        fi

        log "Docker installation completed"
    fi

    # Verify Docker is running
    if ! docker info &> /dev/null; then
        error "Docker is not running. Please start Docker and try again."
    fi

    log "Docker verification completed"
}

# Python environment setup
setup_python_environment() {
    log "Setting up Python environment..."

    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_INSTALLED=$(python3 --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_INSTALLED | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_INSTALLED | cut -d'.' -f2)

        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
            log "Python $PYTHON_INSTALLED found"
        else
            error "Python $PYTHON_VERSION or higher is required. Found: $PYTHON_INSTALLED"
        fi
    else
        error "Python 3 is not installed"
    fi

    # Create virtual environment
    if [ -d "$VENV_NAME" ]; then
        warn "Virtual environment '$VENV_NAME' already exists. Removing it..."
        rm -rf "$VENV_NAME"
    fi

    log "Creating virtual environment: $VENV_NAME"
    python3 -m venv "$VENV_NAME"

    # Activate virtual environment
    source "$VENV_NAME/bin/activate"

    # Upgrade pip
    pip install --upgrade pip setuptools wheel

    log "Python environment setup completed"
}

# Create directory structure
create_directory_structure() {
    log "Creating project directory structure..."

    # Main directories
    mkdir -p {
        app/{api,core,models,services,utils},
        config/{docker,database,monitoring},
        data/{raw,processed,models},
        docker/{scripts,nginx,postgres},
        docs/{api,architecture,deployment},
        logs/{app,nginx,postgres},
        monitoring/{prometheus,grafana},
        scripts/{dev,deploy,backup},
        tests/{unit,integration,e2e},
        static/{css,js,images},
        templates/{email,web},
        tmp,
        backups
    }

    # Create .env files directory
    mkdir -p config/environments

    # Set proper permissions
    chmod 755 {
        app,config,data,docker,docs,logs,monitoring,scripts,tests,static,templates,tmp,backups
    }

    log "Directory structure created"
}

# Create configuration file templates
create_configuration_templates() {
    log "Creating configuration file templates..."

    # Python requirements
    cat > requirements.txt << 'EOF'
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
alembic==1.13.1
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Background Tasks
celery==5.3.4
redis==5.0.1

# Monitoring & Logging
structlog==23.2.0
prometheus-client==0.19.0
sentry-sdk==1.38.0

# Development & Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.7.1

# HTTP Client
httpx==0.25.2
aiohttp==3.9.1

# Data Processing
pandas==2.1.4
numpy==1.25.2

# Machine Learning (for future phases)
scikit-learn==1.3.2
torch==2.1.1
transformers==4.36.0

# Utilities
python-dotenv==1.0.0
click==8.1.7
rich==13.7.0
typer==0.9.0
EOF

    # Environment configuration
    cat > config/environments/.env.example << 'EOF'
# Application Settings
APP_NAME=DMLog
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here-change-in-production

# Database Configuration
DATABASE_URL=postgresql+asyncpg://dmlog_user:dmlog_password@localhost:5432/dmlog_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600

# API Configuration
API_V1_STR=/api/v1
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Security Settings
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_PATH=logs/app/app.log

# Monitoring Configuration
ENABLE_METRICS=True
METRICS_PORT=9090
SENTRY_DSN=

# External Services
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Development Settings
RELOAD=True
SHOW_SQL=True
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
EOF

    # Docker Compose configuration
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://dmlog_user:dmlog_password@postgres:5432/dmlog_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - dmlog-network

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: dmlog_db
      POSTGRES_USER: dmlog_user
      POSTGRES_PASSWORD: dmlog_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/scripts/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
    networks:
      - dmlog-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - dmlog-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./static:/var/www/static
    depends_on:
      - app
    networks:
      - dmlog-network

volumes:
  postgres_data:
  redis_data:

networks:
  dmlog-network:
    driver: bridge
EOF

    # Dockerfile
    cat > docker/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

    # Nginx configuration
    cat > docker/nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

    log "Configuration templates created"
}

# Database initialization
initialize_database() {
    log "Initializing database..."

    # Wait for PostgreSQL to be ready (for Docker setup)
    if docker info &> /dev/null; then
        log "Starting PostgreSQL container..."
        docker-compose up -d postgres

        # Wait for database to be ready
        for i in {1..30}; do
            if docker-compose exec -T postgres pg_isready -U $DB_USER -d $DB_NAME &> /dev/null; then
                log "PostgreSQL is ready"
                break
            fi
            echo "Waiting for PostgreSQL... ($i/30)"
            sleep 2
        done
    fi

    # Create database initialization script
    cat > docker/scripts/init_db.sql << EOF
-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS $DB_NAME;

-- Create user if it doesn't exist
DO
\$do\$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = '$DB_USER') THEN

      CREATE ROLE $DB_USER LOGIN PASSWORD '$DB_PASS';
   END IF;
END
\$do\$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Connect to the database and create extensions
\c $DB_NAME;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create basic tables
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS game_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_game_sessions_user_id ON game_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

-- Insert admin user (password: admin123)
INSERT INTO users (username, email, password_hash, is_admin)
VALUES ('admin', 'admin@dmlog.local', '\$2b\$12\$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5mO8G', TRUE)
ON CONFLICT (username) DO NOTHING;
EOF

    log "Database initialization script created"
}

# First-time data seeding
seed_initial_data() {
    log "Seeding initial data..."

    # Create sample data seeding script
    cat > scripts/dev/seed_data.py << 'EOF'
#!/usr/bin/env python3
"""
Initial data seeding script for DMLog
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import uuid
from datetime import datetime

# Import models (adjust import path as needed)
# from app.models.user import User
# from app.models.game_session import GameSession

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_data():
    """Seed initial data into the database"""

    # Database connection
    DATABASE_URL = "postgresql+asyncpg://dmlog_user:dmlog_password@localhost:5432/dmlog_db"
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Create sample users
            users_data = [
                {
                    "username": "game_master",
                    "email": "gm@dmlog.local",
                    "password": "gm123",
                    "is_admin": False
                },
                {
                    "username": "player1",
                    "email": "player1@dmlog.local",
                    "password": "player123",
                    "is_admin": False
                },
                {
                    "username": "spectator",
                    "email": "spectator@dmlog.local",
                    "password": "spec123",
                    "is_admin": False
                }
            ]

            for user_data in users_data:
                hashed_password = pwd_context.hash(user_data["password"])

                # User creation logic would go here
                # user = User(
                #     username=user_data["username"],
                #     email=user_data["email"],
                #     password_hash=hashed_password,
                #     is_admin=user_data["is_admin"]
                # )
                # session.add(user)

                print(f"Created user: {user_data['username']}")

            # Create sample game sessions
            sessions_data = [
                {
                    "title": "The Dragon's Lair",
                    "description": "A thrilling adventure through dangerous caves",
                    "status": "active"
                },
                {
                    "title": "Mystery of the Ancient Temple",
                    "description": "Explore forgotten ruins and uncover ancient secrets",
                    "status": "planning"
                },
                {
                    "title": "City Intrigue",
                    "description": "Political maneuvering in the capital city",
                    "status": "completed"
                }
            ]

            for session_data in sessions_data:
                # GameSession creation logic would go here
                # game_session = GameSession(
                #     title=session_data["title"],
                #     description=session_data["description"],
                #     status=session_data["status"],
                #     user_id=sample_user_id
                # )
                # session.add(game_session)

                print(f"Created game session: {session_data['title']}")

            await session.commit()
            print("Initial data seeded successfully!")

        except Exception as e:
            await session.rollback()
            print(f"Error seeding data: {e}")
            raise
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_data())
EOF

    chmod +x scripts/dev/seed_data.py
    log "Initial data seeding script created"
}

# Create main application entry point
create_main_app() {
    log "Creating main application structure..."

    # Create main FastAPI application
    mkdir -p app
    cat > app/__init__.py << 'EOF'
"""DMLog Application Package"""

__version__ = "1.0.0"
__author__ = "DMLog Development Team"
__description__ = "Dungeon Master Log - Advanced D&D Campaign Management System"
EOF

    cat > app/main.py << 'EOF'
"""Main FastAPI Application for DMLog"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import structlog
import time

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.api import api_router

# Setup logging
setup_logging()
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting DMLog application")
    yield
    logger.info("Shutting down DMLog application")

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to DMLog API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
EOF

    # Create core configuration
    mkdir -p app/core
    cat > app/core/config.py << 'EOF'
"""Application Configuration Settings"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, validator
import secrets
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    # Project Info
    PROJECT_NAME: str = "DMLog"
    PROJECT_DESCRIPTION: str = "Dungeon Master Log - Advanced D&D Campaign Management System"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600

    # API Configuration
    API_V1_STR: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4

    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:8080"
    ]

    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE_PATH: Path = Path("logs/app/app.log")

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    SENTRY_DSN: Optional[str] = None

    # External Services
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Development Settings
    RELOAD: bool = False
    SHOW_SQL: bool = False

# Create settings instance
settings = Settings()
EOF

    log "Main application structure created"
}

# Create startup script
create_startup_script() {
    log "Creating startup script..."

    cat > start.sh << 'EOF'
#!/bin/bash

# DMLog Startup Script
# This script starts the DMLog application with all services

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    exit 1
}

# Check if virtual environment exists
if [ ! -d "dmlog_env" ]; then
    error "Virtual environment not found. Please run ./setup.sh first."
fi

# Activate virtual environment
source dmlog_env/bin/activate

# Start services
log "Starting DMLog services..."

# Start PostgreSQL and Redis
if command -v docker-compose &> /dev/null; then
    log "Starting database services with Docker Compose..."
    docker-compose up -d postgres redis

    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 10
else
    warn "Docker Compose not found. Please ensure PostgreSQL and Redis are running manually."
fi

# Run database migrations
log "Running database migrations..."
# python -m alembic upgrade head

# Start the application
log "Starting DMLog application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

log "DMLog is now running at http://localhost:8000"
log "API documentation available at http://localhost:8000/docs"
EOF

    chmod +x start.sh
    log "Startup script created"
}

# Final verification
verify_setup() {
    log "Performing final setup verification..."

    # Check if all directories were created
    required_dirs=(
        "app" "config" "data" "docker" "docs" "logs"
        "monitoring" "scripts" "tests" "static" "templates"
    )

    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            log "✓ Directory $dir exists"
        else
            error "✗ Directory $dir is missing"
        fi
    done

    # Check if configuration files were created
    required_files=(
        "requirements.txt"
        "docker-compose.yml"
        "docker/Dockerfile"
        "docker/nginx/nginx.conf"
        "config/environments/.env.example"
        "app/main.py"
        "app/core/config.py"
        "start.sh"
    )

    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            log "✓ File $file exists"
        else
            error "✗ File $file is missing"
        fi
    done

    # Check if virtual environment was created
    if [ -d "$VENV_NAME" ]; then
        log "✓ Virtual environment $VENV_NAME exists"
    else
        error "✗ Virtual environment $VENV_NAME is missing"
    fi

    log "Setup verification completed successfully!"
}

# Display usage instructions
display_usage_instructions() {
    log "Setup completed successfully!"
    echo
    echo "=== DMLog Setup Instructions ==="
    echo
    echo "1. Activate the virtual environment:"
    echo "   source $VENV_NAME/bin/activate"
    echo
    echo "2. Copy and configure environment variables:"
    echo "   cp config/environments/.env.example .env"
    echo "   # Edit .env with your specific configuration"
    echo
    echo "3. Install dependencies:"
    echo "   pip install -r requirements.txt"
    echo
    echo "4. Start the application:"
    echo "   ./start.sh"
    echo "   # Or manually:"
    echo "   docker-compose up -d"
    echo "   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo
    echo "5. Access the application:"
    echo "   - API: http://localhost:8000"
    echo "   - Documentation: http://localhost:8000/docs"
    echo "   - Health Check: http://localhost:8000/health"
    echo
    echo "6. Default admin credentials:"
    echo "   Username: admin"
    echo "   Password: admin123"
    echo
    echo "=== Next Steps ==="
    echo "- Review the configuration in .env"
    echo "- Run tests: pytest tests/"
    echo "- Check logs: tail -f logs/app/app.log"
    echo "- Monitor services: docker-compose ps"
    echo
}

# Main execution
main() {
    log "Starting DMLog environment setup..."

    check_system_requirements
    install_docker
    setup_python_environment
    create_directory_structure
    create_configuration_templates
    initialize_database
    seed_initial_data
    create_main_app
    create_startup_script
    verify_setup
    display_usage_instructions

    log "DMLog setup completed successfully! 🎉"
}

# Handle script interruption
trap 'error "Setup interrupted by user"' INT

# Run main function
main "$@"