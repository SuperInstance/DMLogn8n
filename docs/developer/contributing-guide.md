# DMLog Contributing Guide

## Table of Contents

1. [Welcome to DMLog!](#welcome-to-dmlog)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Standards](#code-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Documentation Requirements](#documentation-requirements)
7. [Pull Request Process](#pull-request-process)
8. [Code Review Guidelines](#code-review-guidelines)
9. [Community Guidelines](#community-guidelines)
10. [Resources and Support](#resources-and-support)

---

## Welcome to DMLog!

Thank you for your interest in contributing to DMLog! We're a community of developers, Dungeon Masters, and D&D enthusiasts working together to build the best campaign management system possible.

### Our Mission

DMLog aims to provide comprehensive tools for Dungeons & Dragons campaigns that enhance the tabletop experience while preserving the human creativity and social interaction that make D&D special.

### Contribution Areas

We welcome contributions in many areas:

- **Frontend Development**: Web interface, mobile apps, user experience
- **Backend Development**: API, database, services, infrastructure
- **AI/ML Features**: Character personalities, decision systems, memory management
- **Documentation**: Guides, tutorials, API documentation
- **Testing**: Unit tests, integration tests, user testing
- **Design**: UI/UX, graphic design, character art
- **Community**: Support, moderation, event organization

### Our Values

- **Inclusivity**: Welcome contributors from all backgrounds and experience levels
- **Quality**: Maintain high standards for code, documentation, and user experience
- **Collaboration**: Work together respectfully and constructively
- **Learning**: Help each other grow and improve
- **Fun**: Remember that we're building tools for a game!

---

## Getting Started

### Prerequisites

**Required Skills:**
- Basic understanding of Python (for backend contributions)
- Familiarity with JavaScript/CSS (for frontend contributions)
- Git version control
- Understanding of D&D 5e rules (helpful but not required)

**Technical Requirements:**
- Python 3.11+
- Node.js 16+ (for frontend development)
- Docker and Docker Compose
- Git
- Code editor (VS Code recommended)

### First Steps

1. **Set Up Your Development Environment**
   ```bash
   # Clone the repository
   git clone https://github.com/dmlog/dmlog.git
   cd dmlog

   # Set up Python environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements/development.txt
   npm install  # For frontend development
   ```

2. **Explore the Codebase**
   - Read the project README
   - Review the architecture documentation
   - Explore the directory structure
   - Run the application locally

3. **Join Our Community**
   - Join our Discord server
   - Introduce yourself in #introductions
   - Review open issues and discussions
   - Find a good first issue to work on

### Development Setup

#### Backend Development

```bash
# Start development services
docker-compose -f docker-compose.dev.yml up -d

# Run database migrations
alembic upgrade head

# Start development server
uvicorn source_code.backend.api_server_new:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/
```

#### Frontend Development

```bash
# Start frontend development server
cd source_code/frontend
python -m http.server 3000

# Or use Node.js if available
npm run dev
```

#### Database Setup

```bash
# Create database
createdb dmlog_dev

# Run migrations
alembic upgrade head

# Load sample data
python scripts/load_sample_data.py
```

---

## Development Workflow

### Git Workflow

We use a feature branch workflow with GitHub Flow principles:

```
main (protected)
├── feature/character-ai-personalities
├── bugfix/dice-roller-animations
├── hotfix/security-patch
└── docs/update-api-documentation
```

### Branch Naming Conventions

- `feature/description`: New features and functionality
- `bugfix/description`: Bug fixes and issue resolution
- `hotfix/description`: Urgent fixes for production issues
- `docs/description`: Documentation updates
- `refactor/description`: Code refactoring without functional changes
- `test/description`: Test additions or improvements

### Commit Message Guidelines

We follow the Conventional Commits specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(api): add character personality AI system
fix(dice): resolve critical hit calculation error
docs(readme): update installation instructions
test(character): add validation tests for character creation
```

### Issue Management

1. **Create Issues** for significant changes or bug reports
2. **Assign Issues** to yourself when you start working on them
3. **Reference Issues** in pull requests with `Fixes #123` or `Closes #123`
4. **Update Issues** with progress and questions

---

## Code Standards

### Python Code Style

We follow PEP 8 with additional guidelines:

#### Formatting

```python
# Use Black for formatting
black source_code/backend/

# Use isort for import sorting
isort source_code/backend/

# Line length: 88 characters
# Use double quotes for strings
# Use f-strings for string formatting
```

#### Type Hints

```python
from typing import List, Optional, Dict, Any
from uuid import UUID

async def get_character(
    character_id: UUID,
    include_memories: bool = False
) -> Optional[CharacterResponse]:
    """Retrieve a character by ID.

    Args:
        character_id: UUID of the character to retrieve
        include_memories: Whether to include character memories

    Returns:
        Character response object or None if not found
    """
    pass
```

#### Documentation

```python
def calculate_damage(roll_result: int, modifier: int, is_critical: bool = False) -> int:
    """Calculate damage for a dice roll.

    Args:
        roll_result: The result of the dice roll
        modifier: Damage modifier to apply
        is_critical: Whether this is a critical hit

    Returns:
        Total damage calculated

    Raises:
        ValueError: If roll_result is negative

    Example:
        >>> calculate_damage(8, 3, is_critical=True)
        19
    """
    if roll_result < 0:
        raise ValueError("Roll result cannot be negative")

    base_damage = roll_result + modifier
    return base_damage * 2 if is_critical else base_damage
```

#### Error Handling

```python
# Use specific exceptions
try:
    character = await repository.get_by_id(character_id)
except DatabaseConnectionError as e:
    logger.error(f"Database connection failed: {e}")
    raise CharacterNotFoundError(f"Could not retrieve character {character_id}") from e

# Use context managers for resources
async with get_database_session() as session:
    result = await session.execute(query)
    return result.scalars().all()
```

### JavaScript/TypeScript Code Style

#### Formatting

```javascript
// Use Prettier for formatting
npm run format

// Use ESLint for linting
npm run lint

// Use semicolons
// Use single quotes for strings
// Use const/let, avoid var
```

#### Modern JavaScript Features

```javascript
// Use arrow functions
const calculateTotal = (items) => {
    return items.reduce((sum, item) => sum + item.price, 0);
};

// Use destructuring
const { name, level, abilities } = character;

// Use async/await
const fetchCharacter = async (id) => {
    try {
        const response = await fetch(`/api/characters/${id}`);
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch character:', error);
        throw error;
    }
};
```

### Database Standards

#### Model Design

```python
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

class Character(Base):
    __tablename__ = "characters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, index=True)
    level = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="characters")
    memories = relationship("CharacterMemory", back_populates="character", cascade="all, delete-orphan")

    # Constraints and indexes
    __table_args__ = (
        Index('idx_characters_name_active', 'name', 'is_active'),
        Index('idx_characters_user_level', 'user_id', 'level'),
    )
```

#### Migration Guidelines

```python
"""Add character personalities

Revision ID: 001_add_character_personalities
Revises: 000_initial_migration
Create Date: 2024-01-22 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001_add_character_personalities'
down_revision = '000_initial_migration'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns
    op.add_column('characters', sa.Column('personality_traits', sa.JSON(), nullable=True))
    op.add_column('characters', sa.Column('alignment', sa.String(50), nullable=True))

    # Add indexes
    op.create_index('idx_characters_alignment', 'characters', ['alignment'])

def downgrade():
    # Remove indexes
    op.drop_index('idx_characters_alignment', table_name='characters')

    # Remove columns
    op.drop_column('characters', 'alignment')
    op.drop_column('characters', 'personality_traits')
```

### API Design Standards

#### RESTful API Guidelines

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

router = APIRouter(prefix="/api/v1/characters", tags=["characters"])

@router.get("/", response_model=List[CharacterResponse])
async def list_characters(
    skip: int = Query(0, ge=0, description="Number of characters to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum characters to return"),
    search: Optional[str] = Query(None, description="Search term for character names"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_database_session)
) -> List[CharacterResponse]:
    """List characters with optional filtering and pagination."""
    service = CharacterService(db)
    return await service.list_characters(skip=skip, limit=limit, search=search, is_active=is_active)

@router.post("/", response_model=CharacterResponse, status_code=201)
async def create_character(
    character_data: CharacterCreate,
    db: AsyncSession = Depends(get_database_session)
) -> CharacterResponse:
    """Create a new character."""
    service = CharacterService(db)
    return await service.create_character(character_data.dict())
```

#### Error Handling

```python
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

class DMLogException(Exception):
    """Base exception for DMLog application."""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class CharacterNotFoundError(DMLogException):
    """Raised when a character is not found."""
    def __init__(self, character_id: str):
        super().__init__(f"Character {character_id} not found", "CHARACTER_NOT_FOUND")

# Exception handler
@router.exception_handler(CharacterNotFoundError)
async def character_not_found_handler(request: Request, exc: CharacterNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "detail": exc.message,
            "error_code": exc.error_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

---

## Testing Guidelines

### Testing Strategy

We use a multi-layered testing approach:

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test component interactions
3. **API Tests**: Test API endpoints
4. **End-to-End Tests**: Test complete user workflows
5. **Performance Tests**: Test system performance under load

### Test Structure

```
tests/
├── unit/
│   ├── test_character_service.py
│   ├── test_dice_roller.py
│   └── test_memory_system.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_database_operations.py
│   └── test_cache_integration.py
├── e2e/
│   ├── test_character_creation_flow.py
│   └── test_session_management.py
└── performance/
    ├── test_load_testing.py
    └── test_database_performance.py
```

### Writing Tests

#### Unit Tests

```python
import pytest
from unittest.mock import Mock, AsyncMock
from source_code.backend.services.character_service import CharacterService
from source_code.backend.schemas.character import CharacterCreate

@pytest.fixture
def mock_database():
    return AsyncMock()

@pytest.fixture
def character_service(mock_database):
    return CharacterService(mock_database)

@pytest.fixture
def sample_character_data():
    return CharacterCreate(
        name="Aragorn",
        race="Human",
        character_class="Ranger",
        level=5
    )

class TestCharacterService:

    @pytest.mark.asyncio
    async def test_create_character_success(self, character_service, sample_character_data):
        # Arrange
        expected_character = Mock(id="123", **sample_character_data.dict())
        character_service.repository.create = AsyncMock(return_value=expected_character)

        # Act
        result = await character_service.create_character(sample_character_data.dict())

        # Assert
        assert result.id == "123"
        assert result.name == "Aragorn"
        character_service.repository.create.assert_called_once_with(sample_character_data.dict())

    @pytest.mark.asyncio
    async def test_create_character_duplicate_name(self, character_service, sample_character_data):
        # Arrange
        character_service.repository.get_by_name = AsyncMock(return_value=Mock())

        # Act & Assert
        with pytest.raises(ValueError, match="Character name already exists"):
            await character_service.create_character(sample_character_data.dict())

    def test_calculate_level_5_character_hp(self, character_service):
        # Arrange
        constitution_score = 14

        # Act
        hp = character_service._calculate_hit_points(5, 10, constitution_score)

        # Assert
        expected_hp = 10 + 4 * 7 + 5 * 2  # First level roll + average rolls + CON mod
        assert hp == expected_hp
```

#### Integration Tests

```python
import pytest
from httpx import AsyncClient
from source_code.backend.api_server_new import create_application

@pytest.mark.asyncio
async def test_create_character_endpoint():
    app = create_application()

    async with AsyncClient(app=app, base_url="http://test") as client:
        character_data = {
            "name": "Test Character",
            "race": "Human",
            "character_class": "Fighter",
            "level": 1
        }

        response = await client.post("/api/v1/characters/", json=character_data)

        assert response.status_code == 201
        assert response.json()["name"] == "Test Character"
        assert "id" in response.json()

@pytest.mark.asyncio
async def test_get_character_not_found():
    app = create_application()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/characters/00000000-0000-0000-0000-000000000000")

        assert response.status_code == 404
        assert response.json()["error_code"] == "CHARACTER_NOT_FOUND"
```

#### API Tests

```python
import pytest
from fastapi.testclient import TestClient
from source_code.backend.api_server_new import create_application

@pytest.fixture
def client():
    app = create_application()
    return TestClient(app)

@pytest.fixture
def auth_headers():
    # Setup authentication headers
    return {"Authorization": "Bearer test_token"}

class TestCharacterAPI:

    def test_list_characters_empty(self, client, auth_headers):
        response = client.get("/api/v1/characters/", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["characters"] == []
        assert response.json()["total"] == 0

    def test_list_characters_with_data(self, client, auth_headers, sample_character):
        # Setup: Create character first
        create_response = client.post("/api/v1/characters/",
                                    json=sample_character,
                                    headers=auth_headers)
        assert create_response.status_code == 201

        # Test: List characters
        response = client.get("/api/v1/characters/", headers=auth_headers)

        assert response.status_code == 200
        assert len(response.json()["characters"]) == 1
        assert response.json()["characters"][0]["name"] == sample_character["name"]

    def test_create_character_invalid_data(self, client, auth_headers):
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "race": "Human",
            "character_class": "Fighter"
        }

        response = client.post("/api/v1/characters/",
                             json=invalid_data,
                             headers=auth_headers)

        assert response.status_code == 422
        assert "name" in response.json()["detail"][0]["loc"]
```

### Test Data Management

#### Fixtures

```python
@pytest.fixture
async def sample_character():
    """Create a sample character for testing."""
    return {
        "name": "Test Character",
        "race": "Human",
        "character_class": "Fighter",
        "level": 1,
        "ability_scores": {
            "strength": 16,
            "dexterity": 14,
            "constitution": 15,
            "intelligence": 12,
            "wisdom": 13,
            "charisma": 10
        }
    }

@pytest.fixture
async def database_with_data():
    """Setup database with test data."""
    async with create_test_database() as db:
        # Load test fixtures
        await load_test_fixtures(db)
        yield db
        # Cleanup automatically handled
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=source_code/backend --cov-report=html

# Run specific test file
pytest tests/unit/test_character_service.py

# Run with verbose output
pytest -v

# Run only fast tests
pytest -m "not slow"

# Run performance tests
pytest tests/performance/ --benchmark-only
```

### Test Quality Guidelines

- **Test Coverage**: Aim for 80%+ coverage on new code
- **Test Independence**: Tests should not depend on each other
- **Clear Assertions**: Use descriptive assertion messages
- **Mock Appropriately**: Mock external dependencies, not internal logic
- **Test Edge Cases**: Test error conditions and boundary cases
- **Performance Testing**: Test critical paths for performance

---

## Documentation Requirements

### Code Documentation

#### Docstrings

All public functions, classes, and methods must have docstrings following the Google style:

```python
class CharacterService:
    """Service layer for character management operations.

    This service provides high-level operations for creating, retrieving,
    updating, and deleting characters. It handles business logic and
    coordinates between the API layer and data repositories.

    Attributes:
        repository: Character repository for data access
        cache_manager: Cache manager for performance optimization

    Example:
        >>> service = CharacterService(repository, cache_manager)
        >>> character = await service.create_character({"name": "Aragorn"})
        >>> print(character.name)
        Aragorn
    """

    def __init__(self, repository: CharacterRepository, cache_manager: CacheManager):
        """Initialize the character service.

        Args:
            repository: Repository for character data access
            cache_manager: Cache manager for performance optimization
        """
        self.repository = repository
        self.cache_manager = cache_manager

    async def create_character(self, character_data: Dict[str, Any]) -> Character:
        """Create a new character with validation and caching.

        This method validates the input data, checks for duplicate names,
        creates the character in the database, and caches the result.

        Args:
            character_data: Dictionary containing character information

        Returns:
            Created character object

        Raises:
            ValueError: If character name already exists
            ValidationError: If character data is invalid

        Example:
            >>> data = {"name": "Aragorn", "race": "Human", "class": "Ranger"}
            >>> character = await service.create_character(data)
            >>> print(character.id)
            12345-abcd
        """
        # Implementation...
        pass
```

#### Comments

Use comments to explain complex logic, business rules, or temporary workarounds:

```python
# Calculate hit points using D&D 5e rules:
# - First level: Maximum hit die + Constitution modifier
# - Subsequent levels: Average hit die + Constitution modifier
# This differs from standard averaging to maintain game balance
if level == 1:
    hit_points = hit_die + constitution_modifier
else:
    hit_points = (hit_die // 2 + 1) * (level - 1) + constitution_modifier * level
```

### API Documentation

#### OpenAPI/Swagger

Use FastAPI's automatic OpenAPI generation with custom descriptions:

```python
@router.post(
    "/",
    response_model=CharacterResponse,
    status_code=201,
    summary="Create a new character",
    description="Create a new D&D character with full stats and background. "
                "The character will be validated according to D&D 5e rules and "
                "assigned a unique identifier.",
    responses={
        201: {
            "description": "Character created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Aragorn",
                        "race": "Human",
                        "character_class": "Ranger",
                        "level": 5
                    }
                }
            }
        },
        400: {
            "description": "Invalid character data",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Character name is required",
                        "error_code": "INVALID_CHARACTER_DATA"
                    }
                }
            }
        }
    }
)
async def create_character(
    character_data: CharacterCreate,
    db: AsyncSession = Depends(get_database_session)
) -> CharacterResponse:
    """Create a new character."""
    pass
```

### README Files

Each major module should have a README.md explaining its purpose and usage:

```markdown
# Character Service

The character service provides business logic for character management operations.

## Features

- Character creation with validation
- Character updates and level progression
- Memory and decision tracking
- AI personality integration

## Usage

```python
from source_code.backend.services.character_service import CharacterService

service = CharacterService(repository, cache_manager)
character = await service.create_character({
    "name": "Aragorn",
    "race": "Human",
    "character_class": "Ranger"
})
```

## API Endpoints

- `POST /api/v1/characters/` - Create character
- `GET /api/v1/characters/{id}` - Get character
- `PUT /api/v1/characters/{id}` - Update character
```

---

## Pull Request Process

### Preparing Your Pull Request

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Follow code style guidelines
   - Write tests for new functionality
   - Update documentation
   - Commit with clear messages

3. **Test Your Changes**
   ```bash
   # Run all tests
   pytest

   # Check code style
   black --check .
   flake8 .
   mypy .

   # Run security checks
   bandit -r source_code/backend/
   ```

4. **Update Documentation**
   - Update relevant documentation files
   - Add changelog entry if needed
   - Update API documentation

5. **Submit Pull Request**
   - Push your branch to GitHub
   - Create pull request with clear description
   - Link relevant issues
   - Request appropriate reviewers

### Pull Request Template

```markdown
## Description
Brief description of changes and purpose.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Performance testing (if applicable)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] Changelog updated (if applicable)

## Issues
Closes #123
Related to #456
```

### Review Process

1. **Automated Checks**
   - Code style validation
   - Test suite execution
   - Security scanning
   - Documentation generation

2. **Code Review**
   - At least one maintainer approval required
   - Focus on logic, design, and maintainability
   - Suggestions and improvements discussed
   - Iterative updates based on feedback

3. **Integration Testing**
   - Test with main branch
   - Verify no regressions
   - Performance impact assessment

4. **Merge**
   - Squash and merge commits
   - Delete feature branch
   - Update changelog
   - Deploy to staging environment

---

## Code Review Guidelines

### For Reviewers

#### Review Focus Areas

1. **Correctness**
   - Does the code work as intended?
   - Are there edge cases not handled?
   - Are error conditions properly managed?

2. **Design**
   - Is the architecture sound?
   - Are there better approaches?
   - Is the code maintainable and extensible?

3. **Performance**
   - Are there performance bottlenecks?
   - Are database queries optimized?
   - Is memory usage appropriate?

4. **Security**
   - Are there security vulnerabilities?
   - Is input validation adequate?
   - Are sensitive data handled properly?

#### Review Best Practices

- **Be Constructive**: Focus on improving the code, not criticizing the author
- **Explain Reasoning**: Help the author understand your suggestions
- **Ask Questions**: If something is unclear, ask for clarification
- **Recognize Good Work**: Acknowledge well-written code and clever solutions
- **Be Timely**: Review pull requests promptly to maintain momentum

#### Example Review Comments

```markdown
**Good:**
"This looks great! I have a couple of suggestions for improvement:

1. Consider using a context manager for the database connection to ensure it's properly closed even if an exception occurs.
2. The validation logic here could be extracted into a separate method to improve testability.

Overall, solid work! 🎉"

**Less Good:**
"This is wrong. You should use a context manager."

**Constructive Alternative:**
"I noticed the database connection isn't using a context manager. This could lead to connection leaks if an exception occurs. Would you consider wrapping it in a `async with` block?"
```

### For Authors

#### Receiving Feedback

- **Be Open**: Consider all feedback thoughtfully
- **Ask for Clarification**: If feedback is unclear, ask questions
- **Explain Your Reasoning**: Help reviewers understand your approach
- **Make Incremental Changes**: Address feedback in focused updates
- **Thank Reviewers**: Appreciate the time and effort reviewers contribute

#### Responding to Review Comments

```markdown
**Good Response:**
"Great point about the context manager! I've updated the code to use `async with` for better resource management. I also extracted the validation logic as suggested - this makes it much more testable.

For the performance concern, I ran some benchmarks and the current implementation handles our expected load well, but I added a TODO for future optimization if needed.

Thanks for the thorough review! 🙏"
```

---

## Community Guidelines

### Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please read our [Code of Conduct](CODE_OF_CONDUCT.md) and follow it in all interactions.

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests, technical discussions
- **Discord**: Real-time chat, general discussion, help
- **Email**: Private questions, security issues (security@dmlog.com)
- **Documentation**: Contributions to guides and tutorials

### Getting Help

1. **Start with Documentation**: Check existing docs and guides
2. **Search Issues**: Look for similar problems or questions
3. **Ask in Discord**: Get help from community members
4. **Create Issue**: For bugs or feature requests
5. **Contact Maintainers**: For personal or sensitive matters

### Recognition

We appreciate all contributions! Contributors are recognized through:

- **Contributor List**: Acknowledged in project documentation
- **Release Notes**: Featured in release announcements
- **Community Highlights**: Showcased in blog posts and social media
- **Swag**: Contributors may receive DMLog merchandise
- **Special Roles**: Active contributors may be invited to join maintenance teams

---

## Resources and Support

### Development Resources

- **Architecture Documentation**: Comprehensive system design
- **API Reference**: Complete API documentation
- **Database Schema**: Database structure and relationships
- **Style Guides**: Code style and formatting guidelines
- **Testing Guide**: Testing strategies and best practices

### Learning Resources

- **D&D 5e Rules**: Official rules documentation
- **Python Async Programming**: Async/await patterns and best practices
- **FastAPI Documentation**: Web framework documentation
- **PostgreSQL Guide**: Database optimization and queries
- **Docker Best Practices**: Containerization and deployment

### Support Contacts

- **Technical Support**: support@dmlog.com
- **Security Issues**: security@dmlog.com
- **Community Manager**: community@dmlog.com
- **Project Maintainer**: maintainers@dmlog.com

### Contributing Timeline

- **Small Changes**: 1-3 days review and merge
- **Medium Features**: 1-2 weeks development and review
- **Large Features**: 2-6 weeks development and review
- **Breaking Changes**: Requires extensive discussion and planning

Thank you for contributing to DMLog! Your efforts help make D&D better for everyone. 🎲✨