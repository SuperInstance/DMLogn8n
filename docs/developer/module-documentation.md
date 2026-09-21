# DMLog Module Documentation

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Backend Modules](#backend-modules)
3. [Frontend Modules](#frontend-modules)
4. [Database Modules](#database-modules)
5. [Service Layer](#service-layer)
6. [API Layer](#api-layer)
7. [AI/ML Modules](#ai-ml-modules)
8. [Utility Modules](#utility-modules)
9. [Testing Modules](#testing-modules)
10. [Module Dependencies](#module-dependencies)

---

## Architecture Overview

DMLog follows a modular architecture with clear separation of concerns. Each module has a specific responsibility and well-defined interfaces.

```
source_code/backend/
├── api/                    # API layer - HTTP endpoints and routing
├── services/               # Business logic layer
├── database/               # Data access layer
├── cache/                  # Caching layer
├── ai/                     # AI/ML functionality
├── monitoring/             # Metrics and logging
├── config/                 # Configuration management
└── utils/                  # Utility functions
```

### Module Principles

1. **Single Responsibility**: Each module has one clear purpose
2. **Loose Coupling**: Modules interact through well-defined interfaces
3. **High Cohesion**: Related functionality is grouped together
4. **Dependency Injection**: Dependencies are injected rather than hard-coded
5. **Async/Await**: All I/O operations use async patterns

---

## Backend Modules

### API Layer (`api/`)

The API layer handles HTTP requests, validation, and response formatting.

#### `api_server_new.py`

Main FastAPI application with middleware, routing, and configuration.

```python
"""
FastAPI Application Server for DMLog
Production-ready server with proper architecture
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="DMLog API",
        version="1.0.0",
        description="D&D campaign management system"
    )

    # Setup middleware, routes, exception handlers
    setup_middleware(app)
    setup_routers(app)
    setup_exception_handlers(app)

    return app
```

**Key Responsibilities:**
- Application lifecycle management
- Middleware configuration
- Route registration
- Global exception handling

#### `routers/`

API endpoint definitions organized by domain.

##### `characters.py`

Character management endpoints.

```python
"""
Character management endpoints
Handles CRUD operations for D&D characters
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

router = APIRouter(prefix="/characters", tags=["characters"])

@router.get("/", response_model=List[CharacterResponse])
async def list_characters(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    service: CharacterService = Depends(get_character_service)
) -> List[CharacterResponse]:
    """List characters with pagination and search."""
    return await service.list_characters(skip=skip, limit=limit, search=search)
```

**Key Responsibilities:**
- HTTP request handling
- Input validation with Pydantic
- Response formatting
- Error handling and status codes

#### `schemas/`

Pydantic models for request/response validation.

##### `character.py`

Character-related data models.

```python
"""
Character schemas for API validation and serialization
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from uuid import UUID

class CharacterCreate(BaseModel):
    """Schema for creating new characters."""

    name: str = Field(..., min_length=1, max_length=100)
    race: str = Field(..., description="Character race")
    character_class: str = Field(..., description="Character class")
    level: int = Field(1, ge=1, le=20)
    ability_scores: Dict[str, int]

    @validator('ability_scores')
    def validate_ability_scores(cls, v):
        required_scores = ['strength', 'dexterity', 'constitution',
                          'intelligence', 'wisdom', 'charisma']
        if not all(score in v for score in required_scores):
            raise ValueError("Missing required ability scores")
        return v
```

**Key Responsibilities:**
- Data validation
- Serialization/deserialization
- API documentation generation
- Type safety

### Service Layer (`services/`)

Business logic layer that coordinates between API and data layers.

#### `character_service.py`

Core character business logic.

```python
"""
Character service for managing character operations
"""

from typing import List, Optional, Dict, Any
from uuid import UUID

class CharacterService:
    """Service for character CRUD operations and business logic."""

    def __init__(self, repository: CharacterRepository, cache_manager: CacheManager):
        self.repository = repository
        self.cache_manager = cache_manager

    async def create_character(self, character_data: Dict[str, Any]) -> Character:
        """Create a new character with validation."""
        # Validate character data
        await self._validate_character_data(character_data)

        # Check for duplicate names
        existing = await self.repository.get_by_name(character_data['name'])
        if existing:
            raise ValidationError("Character name already exists")

        # Create character
        character = await self.repository.create(character_data)

        # Cache the character
        await self.cache_manager.set_character(character.id, character.to_dict())

        return character

    async def _validate_character_data(self, data: Dict[str, Any]) -> None:
        """Validate character data according to D&D rules."""
        # Level validation
        if not 1 <= data.get('level', 1) <= 20:
            raise ValidationError("Level must be between 1 and 20")

        # Ability score validation
        abilities = data.get('ability_scores', {})
        for score, value in abilities.items():
            if not 1 <= value <= 20:
                raise ValidationError(f"Ability score {score} must be between 1 and 20")
```

**Key Responsibilities:**
- Business rule enforcement
- Data validation
- Coordination between repositories
- Caching management
- Transaction management

#### `campaign_service.py`

Campaign management business logic.

```python
"""
Campaign service for managing D&D campaigns
"""

class CampaignService:
    """Service for campaign operations and management."""

    async def create_campaign(self, campaign_data: Dict[str, Any], dm_id: UUID) -> Campaign:
        """Create a new campaign."""
        # Validate DM permissions
        await self._validate_dm_permissions(dm_id)

        # Create campaign
        campaign = await self.repository.create({
            **campaign_data,
            'dm_id': dm_id,
            'is_active': True
        })

        # Initialize campaign settings
        await self._initialize_campaign_settings(campaign.id)

        return campaign

    async def add_player_to_campaign(self, campaign_id: UUID, character_id: UUID, user_id: UUID) -> None:
        """Add a player's character to a campaign."""
        # Validate permissions
        await self._validate_character_ownership(character_id, user_id)
        await self._validate_campaign_access(campaign_id, user_id)

        # Add character to campaign
        await self.repository.add_character_to_campaign(campaign_id, character_id)

        # Clear cache
        await self.cache_manager.delete_campaign_cache(campaign_id)
```

**Key Responsibilities:**
- Campaign lifecycle management
- Player permission validation
- Campaign settings management
- Session scheduling coordination

### Database Layer (`database/`)

Data access layer with models, repositories, and connection management.

#### `models/`

SQLAlchemy ORM models.

##### `character.py`

Character database model.

```python
"""
Character model for database representation
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class Character(Base):
    """Character model representing D&D player characters."""

    __tablename__ = "characters"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic attributes
    name = Column(String(100), nullable=False, index=True)
    level = Column(Integer, nullable=False, default=1)
    race = Column(String(50), nullable=False)
    character_class = Column(String(50), nullable=False)

    # D&D specific data
    ability_scores = Column(JSON, nullable=False)
    hit_points = Column(Integer, nullable=False)
    max_hit_points = Column(Integer, nullable=False)
    armor_class = Column(Integer, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    memories = relationship("CharacterMemory", back_populates="character", cascade="all, delete-orphan")

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_characters_name_active', 'name', 'is_active'),
        Index('idx_characters_user_level', 'user_id', 'level'),
        {'comment': 'Player character data'}
    )
```

**Key Responsibilities:**
- Database schema definition
- Relationship mapping
- Data type specification
- Index and constraint definition

#### `repositories/`

Data access objects implementing repository pattern.

##### `character_repository.py`

Character data access operations.

```python
"""
Character repository for database operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_

class CharacterRepository:
    """Repository for character database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, character_data: Dict[str, Any]) -> Character:
        """Create a new character."""
        character = Character(**character_data)
        self.session.add(character)
        await self.session.flush()
        await self.session.refresh(character)
        return character

    async def get_by_id(self, character_id: UUID) -> Optional[Character]:
        """Get character by ID."""
        stmt = select(Character).where(Character.id == character_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        is_active: Optional[bool] = None
    ) -> List[Character]:
        """Get characters by user with pagination."""
        query = select(Character).where(Character.user_id == user_id)

        if is_active is not None:
            query = query.where(Character.is_active == is_active)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, character_id: UUID, updates: Dict[str, Any]) -> Optional[Character]:
        """Update character with given data."""
        stmt = (
            update(Character)
            .where(Character.id == character_id)
            .values(**updates)
            .returning(Character)
        )

        result = await self.session.execute(stmt)
        character = result.scalar_one_or_none()

        if character:
            await self.session.refresh(character)

        return character
```

**Key Responsibilities:**
- Database query execution
- Data persistence and retrieval
- Transaction management
- Query optimization

#### `connection.py`

Database connection and session management.

```python
"""
Database connection management
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import asyncio

Base = declarative_base()

class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.session_factory = None

    async def initialize(self):
        """Initialize database engine and session factory."""
        self.engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600
        )

        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        return self.session_factory()

    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()

# Dependency injection for FastAPI
async def get_database_session() -> AsyncSession:
    """FastAPI dependency for database session."""
    async with database_manager.get_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

**Key Responsibilities:**
- Connection pool management
- Session lifecycle management
- Database configuration
- Connection health monitoring

### Cache Layer (`cache/`)

Caching system for performance optimization.

#### `cache_manager.py`

Main cache management interface.

```python
"""
Cache manager for performance optimization
"""

from typing import Optional, Dict, Any, List
import json
import redis.asyncio as redis

class CacheManager:
    """Manages caching operations with Redis."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None

    async def initialize(self):
        """Initialize Redis connection."""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)

    async def get_character(self, character_id: UUID) -> Optional[Dict[str, Any]]:
        """Get character from cache."""
        key = f"character:{character_id}"
        data = await self.redis_client.get(key)
        return json.loads(data) if data else None

    async def set_character(self, character_id: UUID, character_data: Dict[str, Any], ttl: int = 3600):
        """Set character in cache."""
        key = f"character:{character_id}"
        await self.redis_client.setex(key, ttl, json.dumps(character_data))

    async def delete_character(self, character_id: UUID):
        """Delete character from cache."""
        key = f"character:{character_id}"
        await self.redis_client.delete(key)

    async def get_campaign_characters(self, campaign_id: UUID) -> List[Dict[str, Any]]:
        """Get all characters in a campaign."""
        key = f"campaign:{campaign_id}:characters"
        data = await self.redis_client.get(key)
        return json.loads(data) if data else []

    async def invalidate_user_cache(self, user_id: UUID):
        """Invalidate all cache entries for a user."""
        pattern = f"user:{user_id}:*"
        keys = await self.redis_client.keys(pattern)
        if keys:
            await self.redis_client.delete(*keys)
```

**Key Responsibilities:**
- Cache key management
- TTL (Time To Live) handling
- Cache invalidation
- Performance optimization

---

## Frontend Modules

### Main Application (`frontend/`)

Web interface built with vanilla JavaScript and Bootstrap.

#### `app.js`

Main application logic and routing.

```javascript
/**
 * Main application controller
 * Handles routing, state management, and UI interactions
 */

class DMLogApp {
    constructor() {
        this.currentUser = null;
        this.currentCampaign = null;
        this.router = new Router();
        this.api = new APIClient();
        this.eventBus = new EventBus();

        this.initialize();
    }

    async initialize() {
        // Initialize authentication
        await this.authenticate();

        // Setup routing
        this.setupRoutes();

        // Initialize UI components
        this.initializeComponents();

        // Start router
        this.router.start();
    }

    setupRoutes() {
        this.router.addRoute('/', () => this.showDashboard());
        this.router.addRoute('/characters', () => this.showCharacters());
        this.router.addRoute('/campaigns', () => this.showCampaigns());
        this.router.addRoute('/campaigns/:id', (params) => this.showCampaign(params.id));
    }

    async showDashboard() {
        const dashboard = new DashboardView(this.api, this.eventBus);
        await dashboard.render();
    }
}
```

**Key Responsibilities:**
- Application initialization
- Route management
- State management
- Component coordination

#### `character-manager.js`

Character management interface.

```javascript
/**
 * Character management interface
 * Handles character CRUD operations and UI interactions
 */

class CharacterManager {
    constructor(api, eventBus) {
        this.api = api;
        this.eventBus = eventBus;
        this.currentCharacter = null;
        this.isEditing = false;
    }

    async loadCharacters() {
        try {
            const characters = await this.api.get('/characters');
            this.renderCharacterList(characters);
        } catch (error) {
            this.showError('Failed to load characters');
        }
    }

    async createCharacter(characterData) {
        try {
            const character = await this.api.post('/characters', characterData);
            this.addCharacterToList(character);
            this.showSuccess('Character created successfully');
            this.eventBus.emit('character:created', character);
        } catch (error) {
            this.showError('Failed to create character');
        }
    }

    async updateCharacter(characterId, updates) {
        try {
            const character = await this.api.put(`/characters/${characterId}`, updates);
            this.updateCharacterInList(character);
            this.showSuccess('Character updated successfully');
        } catch (error) {
            this.showError('Failed to update character');
        }
    }

    renderCharacterSheet(character) {
        const sheet = new CharacterSheet(character);
        sheet.render();

        // Setup event handlers
        sheet.on('edit', () => this.enterEditMode(character));
        sheet.on('save', (updates) => this.updateCharacter(character.id, updates));
        sheet.on('delete', () => this.deleteCharacter(character.id));
    }
}
```

**Key Responsibilities:**
- Character CRUD operations
- Character sheet rendering
- Form validation
- Event handling

---

## AI/ML Modules

### Personality System (`ai/personality.py`)

Character personality modeling and decision making.

```python
"""
Character personality system
Models personality traits and generates character decisions
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from enum import Enum

class PersonalityTrait(Enum):
    """Big Five personality traits."""
    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    NEUROTICISM = "neuroticism"

class CharacterPersonality:
    """Models a character's personality using the Big Five framework."""

    def __init__(self, character_id: UUID, traits: Dict[PersonalityTrait, float]):
        self.character_id = character_id
        self.traits = traits  # Values from 0.0 to 1.0
        self.decision_history = []

    def assess_situation(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Assess a situation and return action preferences."""
        preferences = {}

        # Combat situations
        if context.get('is_combat', False):
            preferences['attack'] = self._calculate_combat_preference(context)
            preferences['defend'] = self._calculate_defensive_preference(context)
            preferences['flee'] = self._calculate_flee_preference(context)

        # Social situations
        if context.get('is_social', False):
            preferences['diplomacy'] = self._calculate_diplomacy_preference(context)
            preferences['intimidation'] = self._calculate_intimidation_preference(context)
            preferences['deception'] = self._calculate_deception_preference(context)

        return preferences

    def _calculate_combat_preference(self, context: Dict[str, Any]) -> float:
        """Calculate preference for combat actions."""
        # High openness and low neuroticism favor combat
        openness_bonus = self.traits[PersonalityTrait.OPENNESS] * 0.3
        neuroticism_penalty = self.traits[PersonalityTrait.NEUROTICISM] * 0.2

        # Consider character's combat capabilities
        combat_strength = context.get('combat_strength', 0.5)

        return min(1.0, combat_strength + openness_bonus - neuroticism_penalty)

    def make_decision(self, situation: Dict[str, Any], options: List[str]) -> Tuple[str, float]:
        """Make a decision based on personality and context."""
        preferences = self.assess_situation(situation)

        # Score each option
        option_scores = []
        for option in options:
            score = self._score_option(option, preferences, situation)
            option_scores.append((option, score))

        # Select best option
        best_option, confidence = max(option_scores, key=lambda x: x[1])

        # Record decision for learning
        self.decision_history.append({
            'situation': situation,
            'options': options,
            'decision': best_option,
            'confidence': confidence
        })

        return best_option, confidence
```

**Key Responsibilities:**
- Personality trait modeling
- Decision making based on personality
- Learning from character experiences
- Context-aware behavior generation

### Memory System (`ai/memory.py`)

Character memory formation and management.

```python
"""
Character memory system
Manages memory formation, consolidation, and retrieval
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np

class Memory:
    """Represents a single character memory."""

    def __init__(self,
                 character_id: UUID,
                 content: str,
                 importance_score: float,
                 memory_type: str = 'episodic',
                 tags: List[str] = None):
        self.id = uuid.uuid4()
        self.character_id = character_id
        self.content = content
        self.importance_score = importance_score
        self.memory_type = memory_type
        self.tags = tags or []
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        self.access_count = 0
        self.consolidation_count = 0

    def access(self):
        """Record memory access."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1

class MemorySystem:
    """Manages character memory formation and retrieval."""

    def __init__(self, character_id: UUID):
        self.character_id = character_id
        self.memories: List[Memory] = []
        self.working_memory: List[Memory] = []
        self.consolidation_threshold = 0.7

    async def form_memory(self,
                         event: Dict[str, Any],
                         emotional_impact: float = 0.0) -> Memory:
        """Form a new memory from an event."""
        # Calculate importance score
        importance = self._calculate_importance(event, emotional_impact)

        # Generate memory content
        content = self._generate_memory_content(event)

        # Determine memory type
        memory_type = self._classify_memory_type(event)

        # Generate tags
        tags = self._generate_tags(event)

        # Create memory
        memory = Memory(
            character_id=self.character_id,
            content=content,
            importance_score=importance,
            memory_type=memory_type,
            tags=tags
        )

        # Add to working memory
        self.working_memory.append(memory)

        # Consolidate if working memory is full
        if len(self.working_memory) > 10:
            await self._consolidate_memories()

        return memory

    async def retrieve_memories(self,
                               query: str,
                               limit: int = 10) -> List[Memory]:
        """Retrieve memories relevant to a query."""
        relevant_memories = []

        # Search for relevant memories
        for memory in self.memories:
            relevance = self._calculate_relevance(memory, query)
            if relevance > 0.3:  # Threshold for relevance
                memory.access()
                relevant_memories.append((memory, relevance))

        # Sort by relevance and limit
        relevant_memories.sort(key=lambda x: x[1], reverse=True)
        return [memory for memory, _ in relevant_memories[:limit]]

    async def _consolidate_memories(self):
        """Consolidate working memory into long-term memory."""
        # Find important memories
        important_memories = [
            memory for memory in self.working_memory
            if memory.importance_score >= self.consolidation_threshold
        ]

        # Transfer to long-term memory
        for memory in important_memories:
            memory.consolidation_count += 1
            self.memories.append(memory)

        # Clear working memory
        self.working_memory = []

        # Perform memory maintenance
        await self._memory_maintenance()

    def _calculate_importance(self, event: Dict[str, Any], emotional_impact: float) -> float:
        """Calculate the importance score of an event."""
        base_importance = 0.5

        # Emotional impact
        base_importance += emotional_impact * 0.3

        # Event type importance
        event_type = event.get('type', 'neutral')
        type_importance = {
            'combat': 0.8,
            'death': 1.0,
            'discovery': 0.6,
            'social': 0.4,
            'neutral': 0.2
        }.get(event_type, 0.2)

        base_importance += type_importance * 0.2

        return min(1.0, base_importance)
```

**Key Responsibilities:**
- Memory formation from events
- Importance scoring
- Memory consolidation
- Retrieval and relevance matching
- Memory maintenance and forgetting

---

## Utility Modules

### Logging (`monitoring/logging_system.py`)

Structured logging configuration and utilities.

```python
"""
Logging system for DMLog
Provides structured logging with multiple handlers and levels
"""

import logging
import logging.config
import json
from datetime import datetime
from typing import Dict, Any

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add extra fields
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'character_id'):
            log_entry['character_id'] = record.character_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id

        # Add exception info
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

class DMLogLogger:
    """Main logger class for DMLog application."""

    def __init__(self):
        self.loggers = {}
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration."""
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'json': {
                    '()': StructuredFormatter
                },
                'standard': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'standard',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'json',
                    'filename': 'logs/dmlog.log',
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5
                },
                'error_file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'ERROR',
                    'formatter': 'json',
                    'filename': 'logs/errors.log',
                    'maxBytes': 10485760,
                    'backupCount': 5
                }
            },
            'loggers': {
                'dmlog': {
                    'handlers': ['console', 'file', 'error_file'],
                    'level': 'DEBUG',
                    'propagate': False
                },
                'uvicorn': {
                    'handlers': ['console'],
                    'level': 'INFO',
                    'propagate': False
                }
            },
            'root': {
                'level': 'INFO',
                'handlers': ['console']
            }
        }

        logging.config.dictConfig(config)

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance."""
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(f'dmlog.{name}')
        return self.loggers[name]

    def log_api_request(self, method: str, path: str, user_id: str = None,
                        status_code: int = None, duration: float = None):
        """Log API request information."""
        logger = self.get_logger('api')
        logger.info(
            f"API {method} {path}",
            extra={
                'method': method,
                'path': path,
                'user_id': user_id,
                'status_code': status_code,
                'duration_ms': duration * 1000 if duration else None
            }
        )

# Global logger instance
dmlog_logger = DMLogLogger()

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return dmlog_logger.get_logger(name)
```

**Key Responsibilities:**
- Structured logging setup
- Multiple log handlers and formatters
- Log rotation and management
- Context-aware logging

### Metrics (`monitoring/metrics.py`)

Performance metrics collection and reporting.

```python
"""
Metrics collection system for DMLog
Provides performance monitoring and analytics
"""

import time
import asyncio
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class MetricValue:
    """Represents a single metric value."""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """Collects and manages application metrics."""

    def __init__(self):
        self.counters = defaultdict(float)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        self.timers = defaultdict(list)
        self.max_history = 1000  # Keep last 1000 values per metric

    def increment_counter(self, name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """Increment a counter metric."""
        key = self._make_key(name, tags)
        self.counters[key] += value

    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric value."""
        key = self._make_key(name, tags)
        self.gauges[key] = value

    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram value."""
        key = self._make_key(name, tags)
        histogram = self.histograms[key]
        histogram.append(value)

        # Keep only recent values
        if len(histogram) > self.max_history:
            self.histograms[key] = histogram[-self.max_history:]

    def record_timer(self, name: str, duration: float, tags: Dict[str, str] = None):
        """Record a timer value."""
        key = self._make_key(name, tags)
        timer = self.timers[key]
        timer.append(duration)

        # Keep only recent values
        if len(timer) > self.max_history:
            self.timers[key] = timer[-self.max_history:]

    def get_metric_stats(self, name: str, metric_type: str, tags: Dict[str, str] = None) -> Dict[str, float]:
        """Get statistics for a metric."""
        key = self._make_key(name, tags)

        if metric_type == 'counter':
            return {'value': self.counters.get(key, 0.0)}
        elif metric_type == 'gauge':
            return {'value': self.gauges.get(key, 0.0)}
        elif metric_type == 'histogram':
            values = self.histograms.get(key, [])
            if not values:
                return {}
            return {
                'count': len(values),
                'sum': sum(values),
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'p50': self._percentile(values, 50),
                'p95': self._percentile(values, 95),
                'p99': self._percentile(values, 99)
            }
        elif metric_type == 'timer':
            durations = self.timers.get(key, [])
            if not durations:
                return {}
            return {
                'count': len(durations),
                'sum': sum(durations),
                'min': min(durations),
                'max': max(durations),
                'avg': sum(durations) / len(durations),
                'p50': self._percentile(durations, 50),
                'p95': self._percentile(durations, 95),
                'p99': self._percentile(durations, 99)
            }

        return {}

    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Create a metric key from name and tags."""
        if not tags:
            return name

        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name},{tag_str}"

    def _percentile(self, values: list, percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

class APIMetrics:
    """API-specific metrics collection."""

    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.start_times = {}

    def start_request(self, request_id: str, method: str, path: str):
        """Start timing an API request."""
        self.start_times[request_id] = time.time()
        self.collector.increment_counter('api_requests_total', tags={
            'method': method,
            'path': path
        })

    def end_request(self, request_id: str, status_code: int):
        """End timing an API request."""
        if request_id not in self.start_times:
            return

        duration = time.time() - self.start_times[request_id]
        del self.start_times[request_id]

        self.collector.record_timer('api_request_duration', duration, tags={
            'status_code': str(status_code)
        })

        self.collector.increment_counter('api_responses_total', tags={
            'status_code': str(status_code)
        })

# Global metrics collector
metrics_collector = MetricsCollector()
api_metrics = APIMetrics(metrics_collector)
```

**Key Responsibilities:**
- Performance metrics collection
- API request tracking
- Statistical analysis
- Metrics export for monitoring

---

## Module Dependencies

### Dependency Graph

```
API Layer
├── Service Layer
│   ├── Repository Layer
│   │   └── Database Models
│   ├── Cache Layer
│   └── AI/ML Modules
├── Utility Modules
│   ├── Logging
│   ├── Metrics
│   └── Configuration
└── Frontend Modules
    └── API Client
```

### Key Dependencies

1. **API Layer** depends on:
   - Service Layer (business logic)
   - Schemas (validation)
   - Utility modules (logging, metrics)

2. **Service Layer** depends on:
   - Repository Layer (data access)
   - Cache Layer (performance)
   - AI/ML Modules (intelligence)
   - Utility modules (logging)

3. **Repository Layer** depends on:
   - Database Models (schema)
   - Database connection management
   - Utility modules (logging)

4. **Frontend Modules** depend on:
   - API Client (communication)
   - UI Components (presentation)
   - State Management (application state)

### Circular Dependencies

The architecture avoids circular dependencies through:
- Clear layered architecture
- Dependency injection
- Event-driven communication
- Interface-based design

---

## Module Testing

Each module includes comprehensive tests covering:

### Unit Tests
- Individual function testing
- Mock external dependencies
- Edge case validation
- Performance testing

### Integration Tests
- Module interaction testing
- Database integration
- Cache layer testing
- API endpoint testing

### End-to-End Tests
- Complete user workflows
- Cross-module functionality
- Performance under load
- Error handling validation

---

This module documentation provides a comprehensive overview of DMLog's architecture and implementation. Each module is designed with clear responsibilities, well-defined interfaces, and comprehensive testing to ensure maintainability and reliability.