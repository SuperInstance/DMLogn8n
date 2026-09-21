# DMLog Code Style Guide

## Table of Contents

1. [Overview](#overview)
2. [Python Style Guide](#python-style-guide)
3. [JavaScript/TypeScript Style Guide](#javascripttypescript-style-guide)
4. [Database Standards](#database-standards)
5. [API Design Guidelines](#api-design-guidelines)
6. [Frontend Style Guide](#frontend-style-guide)
7. [Documentation Standards](#documentation-standards)
8. [Testing Style Guide](#testing-style-guide)
9. [Git and Commit Standards](#git-and-commit-standards)
10. [Code Review Guidelines](#code-review-guidelines)

---

## Overview

This style guide ensures consistency across the DMLog codebase, making it easier to read, maintain, and collaborate on. Following these guidelines helps produce clean, professional, and maintainable code.

### Core Principles

1. **Readability First**: Code should be self-documenting and easy to understand
2. **Consistency**: Follow established patterns throughout the codebase
3. **Simplicity**: Favor simple solutions over complex ones
4. **Maintainability**: Write code that future developers can easily modify
5. **Performance**: Consider performance implications without premature optimization

### Tooling

We use the following tools to enforce style guidelines:

- **Black**: Python code formatting
- **isort**: Python import sorting
- **flake8**: Python linting
- **mypy**: Python type checking
- **Prettier**: JavaScript/TypeScript formatting
- **ESLint**: JavaScript/TypeScript linting
- **pre-commit**: Git hooks for automated checks

---

## Python Style Guide

### Code Formatting

We use **Black** for automatic Python code formatting with the following configuration:

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  migrations
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["source_code"]
```

#### Line Length and Formatting

```python
# ✅ Good: Follows Black formatting
async def get_character_with_memories(
    character_id: UUID,
    include_deleted: bool = False,
    limit: int = 50
) -> Optional[CharacterResponse]:
    """Retrieve a character with their associated memories."""
    pass

# ❌ Bad: Manually formatted, inconsistent with Black
async def get_character_with_memories(character_id: UUID, include_deleted: bool = False, limit: int = 50) -> Optional[CharacterResponse]:
    """Retrieve a character with their associated memories."""
    pass
```

#### Import Organization

```python
# ✅ Good: Properly organized imports
from typing import List, Optional, Dict, Any
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from source_code.backend.database.connection import get_database_session
from source_code.backend.schemas.character import CharacterResponse
from source_code.backend.services.character_service import CharacterService

# ❌ Bad: Unorganized imports
from fastapi import APIRouter, Depends
import asyncpg
from typing import List
from uuid import UUID
from source_code.backend.database.connection import get_database_session
from sqlalchemy.ext.asyncio import AsyncSession
```

### Naming Conventions

#### Variables and Functions

```python
# ✅ Good: Descriptive, snake_case names
def calculate_character_hp(level: int, hit_die: int, con_modifier: int) -> int:
    """Calculate hit points for a character."""
    if level == 1:
        return hit_die + con_modifier
    return hit_die + (level - 1) * (hit_die // 2 + 1) + level * con_modifier

player_name = "Aragorn"
current_hp = 45
max_hit_points = 52

# ❌ Bad: Unclear or incorrect naming
def calc_hp(l, hd, cm):
    """Calculate HP."""
    return l * hd + cm

pn = "Aragorn"
hp = 45
mhp = 52
```

#### Classes and Constants

```python
# ✅ Good: PascalCase for classes, UPPER_CASE for constants
class CharacterService:
    """Service for managing character operations."""

class CharacterMemory:
    """Represents a character's memory."""

MAX_CHARACTER_LEVEL = 20
DEFAULT_HIT_DIE = 8
API_BASE_URL = "https://api.dmlog.com"

# ❌ Bad: Incorrect casing
class characterService:
    """Service for managing character operations."""

max_character_level = 20
api_base_url = "https://api.dmlog.com"
```

#### Private and Protected Members

```python
# ✅ Good: Single underscore for protected, double for private
class CharacterRepository:
    def __init__(self):
        self._cache = {}  # Protected member
        self.__connection = None  # Private member

    def _validate_character_data(self, data: Dict) -> bool:
        """Protected method for validation."""
        return len(data.get("name", "")) > 0

    def __internal_method(self):
        """Private method for internal use."""
        pass

# ❌ Bad: No indication of visibility
class CharacterRepository:
    def __init__(self):
        self.cache = {}  # Should be protected
        self.connection = None  # Should be private

    def validate_character_data(self, data: Dict) -> bool:
        """Should be protected."""
        return len(data.get("name", "")) > 0
```

### Type Hints

#### Function Signatures

```python
# ✅ Good: Complete type hints with clear parameter names
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

async def create_character(
    character_data: Dict[str, Any],
    user_id: UUID,
    validate: bool = True
) -> CharacterResponse:
    """Create a new character with optional validation."""
    pass

def get_character_stats(
    character: Union[Character, CharacterResponse]
) -> Dict[str, int]:
    """Extract combat statistics from a character."""
    pass

# ❌ Bad: Missing or unclear type hints
async def create_character(data, user_id, validate=True):
    """Create a new character."""
    pass

def get_character_stats(character):
    """Extract combat statistics."""
    pass
```

#### Complex Types

```python
# ✅ Good: Use TypedDict for complex dictionaries
from typing import TypedDict, List

class CharacterCreateData(TypedDict):
    name: str
    race: str
    character_class: str
    level: int
    ability_scores: Dict[str, int]

def process_character_creation(data: CharacterCreateData) -> UUID:
    """Process character creation data."""
    pass

# ✅ Good: Use TypeVar for generic types
from typing import TypeVar, Generic

T = TypeVar('T')

class PaginatedResponse(Generic[T]):
    def __init__(self, items: List[T], total: int, page: int):
        self.items = items
        self.total = total
        self.page = page

# ❌ Bad: Using Any for everything
def process_character_creation(data: Any) -> Any:
    """Process character creation data."""
    pass
```

### Error Handling

#### Exception Classes

```python
# ✅ Good: Specific exception classes with clear hierarchy
class DMLogError(Exception):
    """Base exception for DMLog application."""
    pass

class ValidationError(DMLogError):
    """Raised when input validation fails."""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message)

class CharacterNotFoundError(DMLogError):
    """Raised when a character cannot be found."""
    def __init__(self, character_id: UUID):
        self.character_id = character_id
        super().__init__(f"Character {character_id} not found")

# ❌ Bad: Generic exceptions
class Error(Exception):
    """Generic error."""
    pass

raise Error("Something went wrong")
```

#### Exception Handling

```python
# ✅ Good: Specific exception handling with proper logging
import logging

logger = logging.getLogger(__name__)

async def get_character(character_id: UUID) -> Optional[Character]:
    """Retrieve a character by ID."""
    try:
        return await character_repository.get_by_id(character_id)
    except DatabaseConnectionError as e:
        logger.error(f"Database connection failed for character {character_id}: {e}")
        raise CharacterServiceError("Unable to connect to database") from e
    except ValidationError as e:
        logger.warning(f"Invalid character ID {character_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving character {character_id}: {e}")
        raise CharacterServiceError("An unexpected error occurred") from e

# ❌ Bad: Bare except and silent failures
async def get_character(character_id: UUID):
    """Retrieve a character by ID."""
    try:
        return await character_repository.get_by_id(character_id)
    except:
        return None  # Silent failure
```

### Async/Await Patterns

#### Proper Async Usage

```python
# ✅ Good: Proper async/await with error handling
async def get_character_with_memories(character_id: UUID) -> CharacterResponse:
    """Retrieve character with their memories."""
    # Fetch character and memories concurrently
    character_task = get_character(character_id)
    memories_task = get_character_memories(character_id)

    try:
        character, memories = await asyncio.gather(
            character_task,
            memories_task,
            return_exceptions=True
        )
    except Exception as e:
        logger.error(f"Failed to fetch character data: {e}")
        raise CharacterServiceError("Unable to retrieve character data") from e

    if isinstance(character, Exception):
        raise character
    if isinstance(memories, Exception):
        logger.warning(f"Failed to fetch memories: {memories}")
        memories = []

    return CharacterResponse(
        **character.dict(),
        memories=memories
    )

# ❌ Bad: Inefficient sequential calls
async def get_character_with_memories(character_id: UUID) -> CharacterResponse:
    """Retrieve character with their memories."""
    character = await get_character(character_id)  # Sequential
    memories = await get_character_memories(character_id)  # Sequential
    return CharacterResponse(**character.dict(), memories=memories)
```

### Documentation Standards

#### Docstrings

```python
# ✅ Good: Comprehensive Google-style docstring
def calculate_attack_bonus(
    character_level: int,
    proficiency_bonus: int,
    ability_modifier: int,
    magic_bonus: int = 0
) -> int:
    """Calculate the total attack bonus for a character.

    This function follows D&D 5e rules for calculating attack bonuses,
    combining proficiency, ability scores, and magical enhancements.

    Args:
        character_level: The character's current level
        proficiency_bonus: Proficiency bonus based on character level
        ability_modifier: Relevant ability score modifier (STR/DEX)
        magic_bonus: Magical bonus from weapons or effects

    Returns:
        Total attack bonus as an integer

    Raises:
        ValueError: If any parameter is negative

    Example:
        >>> calculate_attack_bonus(5, 3, 3, 1)
        7
        >>> calculate_attack_bonus(1, 2, 0, 0)
        2
    """
    if any(param < 0 for param in [character_level, proficiency_bonus, ability_modifier, magic_bonus]):
        raise ValueError("All parameters must be non-negative")

    return proficiency_bonus + ability_modifier + magic_bonus

# ❌ Bad: Minimal or missing docstring
def calculate_attack_bonus(level, prof, mod, magic=0):
    """Calculate attack bonus."""
    return prof + mod + magic
```

---

## JavaScript/TypeScript Style Guide

### Code Formatting

We use **Prettier** for automatic JavaScript/TypeScript formatting:

```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false
}
```

#### Variable Declarations

```javascript
// ✅ Good: Use const/let, proper naming
const API_BASE_URL = 'https://api.dmlog.com';
let currentCharacter = null;
const characterList = [];

// ❌ Bad: Using var, unclear naming
var api = 'https://api.dmlog.com';
var char = null;
var chars = [];
```

#### Function Declarations

```javascript
// ✅ Good: Arrow functions, clear parameter names
const calculateTotalDamage = (baseDamage, modifier, isCritical = false) => {
  const totalDamage = baseDamage + modifier;
  return isCritical ? totalDamage * 2 : totalDamage;
};

const fetchCharacter = async (characterId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/characters/${characterId}`);
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch character:', error);
    throw error;
  }
};

// ❌ Bad: Function declarations, unclear names
function calculateDamage(d, m, critical) {
  return critical ? (d + m) * 2 : d + m;
}

async function getChar(id) {
  const r = await fetch(`${API_BASE_URL}/characters/${id}`);
  return r.json();
}
```

### Object and Array Patterns

#### Destructuring

```javascript
// ✅ Good: Use destructuring for clarity
const character = {
  name: 'Aragorn',
  level: 5,
  abilities: { strength: 16, dexterity: 14 }
};

const { name, level } = character;
const { strength, dexterity } = character.abilities;

const processCharacter = ({ name, level, abilities: { strength, dexterity } }) => {
  return `${name} (Level ${level}) - STR: ${strength}, DEX: ${dexterity}`;
};

// ❌ Bad: Manual property access
const characterName = character.name;
const characterLevel = character.level;
const strength = character.abilities.strength;
```

#### Array Methods

```javascript
// ✅ Good: Use functional array methods
const activeCharacters = characters.filter(char => char.isActive);
const characterNames = activeCharacters.map(char => char.name);
const totalLevel = activeCharacters.reduce((sum, char) => sum + char.level, 0);

const highLevelCharacters = characters
  .filter(char => char.level >= 10)
  .map(char => ({ name: char.name, class: char.class }));

// ❌ Bad: Manual loops
const activeCharacters = [];
for (let i = 0; i < characters.length; i++) {
  if (characters[i].isActive) {
    activeCharacters.push(characters[i]);
  }
}
```

### Async/Await Patterns

```javascript
// ✅ Good: Proper async/await with error handling
const loadCharacterData = async (characterId) => {
  try {
    const [character, memories, decisions] = await Promise.all([
      fetchCharacter(characterId),
      fetchCharacterMemories(characterId),
      fetchCharacterDecisions(characterId)
    ]);

    return {
      ...character,
      memories,
      decisions
    };
  } catch (error) {
    console.error('Failed to load character data:', error);
    throw new Error('Unable to load character data');
  }
};

// ✅ Good: Async IIFE for module-level initialization
const initializeApp = async () => {
  try {
    await authenticateUser();
    const userData = await loadUserData();
    initializeUI(userData);
  } catch (error) {
    showErrorMessage('Failed to initialize application');
  }
};

// ❌ Bad: Promise chains or callback hell
fetchCharacter(characterId)
  .then(character => {
    return fetchCharacterMemories(characterId).then(memories => {
      return { ...character, memories };
    });
  })
  .catch(error => {
    console.error('Error:', error);
  });
```

### Error Handling

```javascript
// ✅ Good: Custom error classes and proper error handling
class DMLogError extends Error {
  constructor(message, code = null) {
    super(message);
    this.name = 'DMLogError';
    this.code = code;
  }
}

class CharacterNotFoundError extends DMLogError {
  constructor(characterId) {
    super(`Character ${characterId} not found`, 'CHARACTER_NOT_FOUND');
    this.characterId = characterId;
  }
}

const handleAPICall = async (apiCall) => {
  try {
    const response = await apiCall();
    if (!response.ok) {
      throw new DMLogError(`API call failed: ${response.statusText}`, 'API_ERROR');
    }
    return await response.json();
  } catch (error) {
    if (error instanceof DMLogError) {
      throw error;
    }
    throw new DMLogError('Unexpected error occurred', 'UNKNOWN_ERROR');
  }
};

// ❌ Bad: Generic error handling
const fetchData = async (url) => {
  try {
    const response = await fetch(url);
    return response.json();
  } catch (e) {
    console.log('Error');
    return null;
  }
};
```

---

## Database Standards

### Model Design

#### SQLAlchemy Models

```python
# ✅ Good: Well-structured model with relationships and constraints
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

class Character(Base):
    """Character model representing D&D player characters."""

    __tablename__ = "characters"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for the character"
    )

    # Basic attributes
    name = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Character name"
    )

    level = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Character level (1-20)"
    )

    # D&D attributes
    race = Column(
        String(50),
        nullable=False,
        comment="Character race"
    )

    character_class = Column(
        String(50),
        nullable=False,
        comment="Character class"
    )

    # Status flags
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the character is currently active"
    )

    # Timestamps
    created_at = Column(
        DateTime,
        default=func.now(),
        nullable=False,
        comment="When the character was created"
    )

    updated_at = Column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="When the character was last updated"
    )

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="ID of the user who owns this character"
    )

    # Relationships
    user = relationship("User", back_populates="characters")
    memories = relationship(
        "CharacterMemory",
        back_populates="character",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    decisions = relationship(
        "CharacterDecision",
        back_populates="character",
        cascade="all, delete-orphan"
    )

    # Table constraints and indexes
    __table_args__ = (
        Index('idx_characters_name_active', 'name', 'is_active'),
        Index('idx_characters_user_level', 'user_id', 'level'),
        Index('idx_characters_class', 'character_class'),
        Index('idx_characters_created', 'created_at'),
        {"comment": "Player character data"}
    )

    def __repr__(self) -> str:
        return f"<Character(id={self.id}, name='{self.name}', level={self.level})>"

# ❌ Bad: Minimal model, lacking relationships and constraints
class Character(Base):
    __tablename__ = "characters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100))
    level = Column(Integer, default=1)
    race = Column(String(50))
    character_class = Column(String(50))
    is_active = Column(Boolean, default=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
```

#### Database Migrations

```python
# ✅ Good: Well-documented migration with proper rollback
"""Add character memories system

Revision ID: 002_add_character_memories
Revises: 001_add_character_personalities
Create Date: 2024-01-22 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_add_character_memories'
down_revision = '001_add_character_personalities'
branch_labels = None
depends_on = None

def upgrade():
    # Create memories table
    op.create_table(
        'character_memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('character_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('importance_score', sa.Float(), nullable=False, default=0.5),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('consolidated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('importance_score >= 0 AND importance_score <= 1', 'ck_memory_importance_range')
    )

    # Create indexes
    op.create_index('idx_memories_character_importance', 'character_memories', ['character_id', 'importance_score'])
    op.create_index('idx_memories_created', 'character_memories', ['created_at'])

    # Create decisions table
    op.create_table(
        'character_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('character_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('decision', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('outcome', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['character_id'], ['characters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', 'ck_decision_confidence_range')
    )

    # Create indexes
    op.create_index('idx_decisions_character', 'character_decisions', ['character_id'])
    op.create_index('idx_decisions_confidence', 'character_decisions', ['confidence_score'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_decisions_confidence', table_name='character_decisions')
    op.drop_index('idx_decisions_character', table_name='character_decisions')
    op.drop_index('idx_memories_created', table_name='character_memories')
    op.drop_index('idx_memories_character_importance', table_name='character_memories')

    # Drop tables
    op.drop_table('character_decisions')
    op.drop_table('character_memories')
```

### Query Patterns

#### Repository Pattern

```python
# ✅ Good: Clean repository with proper error handling
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload

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
        """Get characters by user with pagination and filtering."""
        query = select(Character).where(Character.user_id == user_id)

        if is_active is not None:
            query = query.where(Character.is_active == is_active)

        query = query.offset(skip).limit(limit).order_by(Character.created_at.desc())

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

    async def delete(self, character_id: UUID) -> bool:
        """Delete character by ID."""
        stmt = delete(Character).where(Character.id == character_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def search(
        self,
        query: str,
        user_id: Optional[UUID] = None,
        limit: int = 20
    ) -> List[Character]:
        """Search characters by name or other attributes."""
        search_filter = or_(
            Character.name.ilike(f"%{query}%"),
            Character.race.ilike(f"%{query}%"),
            Character.character_class.ilike(f"%{query}%")
        )

        stmt = select(Character).where(search_filter)

        if user_id:
            stmt = stmt.where(Character.user_id == user_id)

        stmt = stmt.limit(limit).order_by(Character.name)

        result = await self.session.execute(stmt)
        return result.scalars().all()

# ❌ Bad: Direct database access without abstraction
async def create_character(data):
    character = Character(**data)
    session.add(character)
    await session.commit()
    return character
```

---

## API Design Guidelines

### RESTful API Standards

#### Endpoint Design

```python
# ✅ Good: RESTful endpoints with proper HTTP methods
router = APIRouter(prefix="/api/v1/characters", tags=["characters"])

@router.get("/", response_model=List[CharacterResponse])
async def list_characters(
    skip: int = Query(0, ge=0, description="Number of characters to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum characters to return"),
    search: Optional[str] = Query(None, description="Search term"),
    db: AsyncSession = Depends(get_database_session)
) -> List[CharacterResponse]:
    """List characters with pagination and search."""
    service = CharacterService(db)
    return await service.list_characters(skip=skip, limit=limit, search=search)

@router.post("/", response_model=CharacterResponse, status_code=201)
async def create_character(
    character_data: CharacterCreate,
    db: AsyncSession = Depends(get_database_session)
) -> CharacterResponse:
    """Create a new character."""
    service = CharacterService(db)
    return await service.create_character(character_data.dict())

@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: UUID,
    include_memories: bool = Query(False, description="Include character memories"),
    db: AsyncSession = Depends(get_database_session)
) -> CharacterResponse:
    """Get character by ID."""
    service = CharacterService(db)
    return await service.get_character(character_id, include_memories=include_memories)

@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: UUID,
    character_data: CharacterUpdate,
    db: AsyncSession = Depends(get_database_session)
) -> CharacterResponse:
    """Update character."""
    service = CharacterService(db)
    return await service.update_character(character_id, character_data.dict(exclude_unset=True))

@router.delete("/{character_id}", status_code=204)
async def delete_character(
    character_id: UUID,
    db: AsyncSession = Depends(get_database_session)
) -> None:
    """Delete character."""
    service = CharacterService(db)
    await service.delete_character(character_id)

# ❌ Bad: Non-RESTful endpoints
@router.post("/characters/get")
async def get_character(character_id: str):
    """Get character."""
    pass

@router.post("/characters/update")
async def update_character(character_id: str, data: dict):
    """Update character."""
    pass
```

#### Response Models

```python
# ✅ Good: Proper Pydantic models with validation
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class AbilityScores(BaseModel):
    """Character ability scores."""

    strength: int = Field(..., ge=1, le=20, description="Strength score")
    dexterity: int = Field(..., ge=1, le=20, description="Dexterity score")
    constitution: int = Field(..., ge=1, le=20, description="Constitution score")
    intelligence: int = Field(..., ge=1, le=20, description="Intelligence score")
    wisdom: int = Field(..., ge=1, le=20, description="Wisdom score")
    charisma: int = Field(..., ge=1, le=20, description="Charisma score")

    @validator('*')
    def validate_ability_score(cls, v):
        if v < 1 or v > 20:
            raise ValueError("Ability scores must be between 1 and 20")
        return v

class CharacterCreate(BaseModel):
    """Model for creating a new character."""

    name: str = Field(..., min_length=1, max_length=100, description="Character name")
    race: str = Field(..., description="Character race")
    character_class: str = Field(..., description="Character class")
    level: int = Field(1, ge=1, le=20, description="Character level")
    ability_scores: AbilityScores = Field(..., description="Ability scores")
    background: Optional[str] = Field(None, max_length=1000, description="Character background")
    alignment: Optional[str] = Field(None, description="Character alignment")

    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Character name cannot be empty")
        return v.strip()

class CharacterResponse(BaseModel):
    """Model for character response."""

    id: UUID
    name: str
    race: str
    character_class: str
    level: int
    ability_scores: AbilityScores
    background: Optional[str]
    alignment: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CharacterListResponse(BaseModel):
    """Model for character list response."""

    characters: List[CharacterResponse]
    total: int = Field(..., ge=0, description="Total number of characters")
    skip: int = Field(..., ge=0, description="Number of characters skipped")
    limit: int = Field(..., ge=1, le=100, description="Maximum characters returned")

# ❌ Bad: Using dict instead of proper models
async def create_character(character_data: dict) -> dict:
    """Create character."""
    # No validation, no typing
    pass
```

#### Error Handling

```python
# ✅ Good: Consistent error responses with proper status codes
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

class DMLogException(Exception):
    """Base exception for DMLog API."""
    def __init__(self, message: str, error_code: str = None, status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(DMLogException):
    """Raised when input validation fails."""
    def __init__(self, message: str, field: str = None):
        super().__init__(message, "VALIDATION_ERROR", 400)
        self.field = field

class NotFoundError(DMLogException):
    """Raised when a resource is not found."""
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} {resource_id} not found"
        super().__init__(message, "NOT_FOUND", 404)
        self.resource_type = resource_type
        self.resource_id = resource_id

# Exception handler
@router.exception_handler(DMLogException)
async def dmlog_exception_handler(request: Request, exc: DMLogException):
    """Handle DMLog exceptions consistently."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "code": exc.error_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

# Usage in endpoints
@router.get("/{character_id}")
async def get_character(character_id: UUID):
    """Get character by ID."""
    character = await character_service.get_by_id(character_id)
    if not character:
        raise NotFoundError("Character", str(character_id))
    return character

# ❌ Bad: Inconsistent error handling
@router.get("/{character_id}")
async def get_character(character_id: UUID):
    """Get character by ID."""
    character = await character_service.get_by_id(character_id)
    if not character:
        return {"error": "Character not found"}, 404
    return character
```

---

## Testing Style Guide

### Test Structure

#### Test Organization

```python
# ✅ Good: Well-organized test file with clear sections
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from source_code.backend.services.character_service import CharacterService
from source_code.backend.schemas.character import CharacterCreate
from source_code.backend.models.character import Character
from source_code.backend.exceptions import CharacterNotFoundError, ValidationError

class TestCharacterService:
    """Test suite for CharacterService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock character repository."""
        return AsyncMock()

    @pytest.fixture
    def character_service(self, mock_repository):
        """Create character service with mock repository."""
        return CharacterService(mock_repository)

    @pytest.fixture
    def sample_character_data(self):
        """Create sample character data for testing."""
        return CharacterCreate(
            name="Test Character",
            race="Human",
            character_class="Fighter",
            level=1,
            ability_scores={
                "strength": 16,
                "dexterity": 12,
                "constitution": 14,
                "intelligence": 10,
                "wisdom": 12,
                "charisma": 8
            }
        )

    @pytest.fixture
    def sample_character(self, sample_character_data):
        """Create sample character model."""
        return Character(
            id=uuid4(),
            **sample_character_data.dict()
        )

class TestCharacterCreation:
    """Tests for character creation functionality."""

    @pytest.mark.asyncio
    async def test_create_character_success(self, character_service, sample_character_data):
        """Test successful character creation."""
        # Arrange
        expected_character = Character(
            id=uuid4(),
            **sample_character_data.dict()
        )
        character_service.repository.create = AsyncMock(return_value=expected_character)

        # Act
        result = await character_service.create_character(sample_character_data.dict())

        # Assert
        assert result.id == expected_character.id
        assert result.name == sample_character_data.name
        assert result.race == sample_character_data.race
        character_service.repository.create.assert_called_once_with(sample_character_data.dict())

    @pytest.mark.asyncio
    async def test_create_character_duplicate_name(self, character_service, sample_character_data):
        """Test character creation with duplicate name."""
        # Arrange
        character_service.repository.get_by_name = AsyncMock(return_value=Mock())

        # Act & Assert
        with pytest.raises(ValidationError, match="Character name already exists"):
            await character_service.create_character(sample_character_data.dict())

    @pytest.mark.asyncio
    async def test_create_character_invalid_level(self, character_service, sample_character_data):
        """Test character creation with invalid level."""
        # Arrange
        invalid_data = sample_character_data.dict()
        invalid_data["level"] = 25  # Invalid level

        # Act & Assert
        with pytest.raises(ValidationError, match="Level must be between 1 and 20"):
            await character_service.create_character(invalid_data)

# ❌ Bad: Poorly organized tests
def test_character():
    # Multiple test cases in one function
    service = CharacterService()
    # Test creation
    # Test validation
    # Test errors
    pass
```

#### Test Data Management

```python
# ✅ Good: Proper test fixtures and data management
@pytest.fixture
async def database_with_test_data():
    """Create test database with sample data."""
    # Setup test database
    async with create_test_database() as db:
        # Load test fixtures
        await load_character_fixtures(db)
        await load_campaign_fixtures(db)
        yield db
        # Cleanup automatically handled

@pytest.fixture
def mock_character_response():
    """Create mock character response for API testing."""
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "Test Character",
        "race": "Human",
        "character_class": "Fighter",
        "level": 1,
        "is_active": True,
        "created_at": "2024-01-22T10:30:00Z",
        "updated_at": "2024-01-22T10:30:00Z"
    }

# ❌ Bad: Hardcoded test data
def test_api():
    character_data = {
        "id": "123",
        "name": "Test"
    }
    # Test with hardcoded data
    pass
```

### Test Naming and Documentation

```python
# ✅ Good: Descriptive test names with docstrings
@pytest.mark.asyncio
async def test_create_character_with_valid_data_returns_character_with_id():
    """Test that creating a character with valid data returns a character with an ID."""
    # Test implementation
    pass

@pytest.mark.asyncio
async def test_get_character_by_nonexistent_id_raises_character_not_found_error():
    """Test that retrieving a non-existent character raises appropriate error."""
    # Test implementation
    pass

@pytest.mark.asyncio
async def test_update_character_level_increases_level_and_updates_abilities():
    """Test that updating character level correctly modifies level and related abilities."""
    # Test implementation
    pass

# ❌ Bad: Unclear test names
def test_character_1():
    """Test character."""
    pass

def test_api_works():
    """Test API."""
    pass
```

---

## Git and Commit Standards

### Branch Naming

```bash
# ✅ Good: Clear, descriptive branch names
feature/character-ai-personalities
bugfix/dice-roller-critical-calculation
hotfix/security-vulnerability-fix
docs/api-documentation-update
refactor/database-connection-pooling
test/character-validation-tests

# ❌ Bad: Unclear branch names
feature/char-ai
fix/dice
stuff
temp-branch
```

### Commit Messages

```bash
# ✅ Good: Clear, conventional commits
feat(api): add character personality AI system
- Implement personality trait modeling
- Add decision-making engine
- Create memory consolidation system
- Update API endpoints with new features

fix(dice): resolve critical hit calculation error
- Fix double application of critical modifier
- Add proper validation for damage calculations
- Update test cases for edge conditions

docs(readme): update installation and setup instructions
- Add Docker Compose setup
- Update Python version requirements
- Fix broken links in documentation

refactor(database): improve connection pooling
- Implement connection pool with proper sizing
- Add connection health checks
- Optimize query performance with prepared statements

# ❌ Bad: Poor commit messages
fixed stuff
update
wip
bug fix
```

### Pull Request Titles

```markdown
# ✅ Good: Clear PR titles that describe the change
feat: Add character AI personality system
fix: Resolve dice roller critical hit calculation
docs: Update API documentation with new endpoints
refactor: Improve database connection pooling

# ❌ Bad: Unclear PR titles
Update code
Fixes
WIP
Changes
```

---

This comprehensive style guide ensures consistency across the DMLog codebase and helps maintain high-quality, readable, and maintainable code. All contributors should follow these guidelines to ensure a cohesive development experience.