# DMLog Developer Onboarding Guide

*Everything a professional developer needs to know to service, improve, and extend the DMLog platform*

---

## 🎯 Welcome to DMLog!

DMLog is a comprehensive Dungeons & Dragons campaign management platform that combines traditional TTRPG mechanics with cutting-edge AI technology. As a developer joining our team, you'll be working with a sophisticated system that includes:

- **Backend**: FastAPI + SQLAlchemy + Redis + PostgreSQL
- **AI/ML**: QLoRA training, character personalities, cultural transmission
- **Frontend**: Modern JavaScript with PWA capabilities
- **Infrastructure**: Kubernetes, Docker, Terraform, CI/CD
- **Real-time Features**: WebSockets, voice chat, live sessions

This guide will help you get productive quickly and understand how to work with our codebase effectively.

---

## 🚀 Quick Start (15 minutes)

### 1. Local Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/dmlog.git
cd dmlog

# One-command setup
./scripts/setup.sh

# Start all services
./deploy.sh development

# You're running! Check:
curl http://localhost:8000/api/v1/health/simple
```

### 2. Your First Task

1. **Explore the codebase**:
   ```bash
   # Backend structure
   tree source_code/backend -L 2
   ```

2. **Run the test suite**:
   ```bash
   cd source_code/backend
   pytest tests/ -v
   ```

3. **Make your first improvement**:
   - Fix any failing tests
   - Add a new test case
   - Submit your first PR!

---

## 📚 Codebase Architecture Overview

### High-Level Architecture

```
┌─────────────────┐
│    Frontend      │    ← Static assets, PWA, WebSocket client
├─────────────────┤
│    FastAPI       │    ← Async Python API server
├─────────────────┤
│    Services      │    ← Business logic, AI/ML, caching
├─────────────────┤
│    Data Layer    │    ← PostgreSQL, Redis, Vector DB
└─────────────────┘
```

### Key Directories

```
source_code/backend/
├── api/              # API endpoints and schemas
│   ├── routers/       # FastAPI routers
│   ├── schemas/        # Pydantic models
│   └── middleware/     # Custom middleware
├── services/         # Business logic
│   ├── character/      # Character management
│   ├── ai/            # AI/ML components
│   └── security/       # Security features
├── database/         # Data layer
│   ├── models.py       # SQLAlchemy models
│   ├── repositories.py # Data access layer
│   └── connection.py   # Database connection
├── cache/            # Caching layer
│   ├── cache_manager.py # Redis management
│   └── serializers.py  # Data serialization
└── performance/      # Performance optimizations
    ├── database/      # DB performance
    ├── ai_optimization/ # AI/ML performance
    └── monitoring/     # Metrics and APM
```

---

## 🛠️ Development Workflow

### 1. Branch Strategy

- `main`: Production-ready code (always stable)
- `develop`: Integration and feature development
- `feature/*`: Individual feature branches
- `hotfix/*`: Critical fixes (fast-tracked to main)

### 2. PR Process

1. **Create branch**: `git checkout -b feature/amazing-feature`
2. **Make changes**: Follow coding standards
3. **Run tests**: `pytest` and `black`
4. **Submit PR**: With description and tests
5. **Code Review**: At least one approval required
6. **Merge**: After passing all checks

### 3. Coding Standards

```python
# Use type hints
def create_character(name: str, character_class: str) -> Character:
    """Create a new D&D character."""
    pass

# Follow PEP 8
class CharacterService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_character(self, character_id: str) -> Optional[Character]:
        """Retrieve character by ID."""
        pass
```

### 4. Testing Requirements

```python
# Write tests for all new code
async def test_character_creation():
    """Test character creation flow."""
    service = CharacterService(test_db)
    character = await service.create_character(
        name="Gandalf",
        character_class="wizard"
    )
    assert character.name == "Gandalf"
    assert character.level == 1
```

---

## 🔧 Core Systems Deep Dive

### 1. Database Layer

**Models (`database/models.py`)**

```python
class Character(Base):
    """Character model with relationships."""
    __tablename__ = "characters"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4())[:12])
    name = Column(String(100), nullable=False, index=True)
    # ... other fields

    # Relationships
    memories = relationship("Memory", back_populates="character")
    decisions = relationship("Decision", back_populates="character")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            # ... other fields
        }
```

**Repositories (`database/repositories.py`)**

```python
class CharacterRepository:
    """Data access layer for characters."""

    async def create(self, character_data: dict) -> Character:
        """Create a new character."""
        character = Character(**character_data)
        self.db.add(character)
        await self.db.commit()
        await self.db.refresh(character)
        return character

    async def get_with_memories(
        self,
        character_id: str,
        limit: int = 50
    ) -> List[Character]:
        """Get character with their memories."""
        # Use selectin for efficient loading
        stmt = (
            select(Character)
            .options(selectinload(Character.memories))
            .where(Character.id == character_id)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalars().all()
```

### 2. API Layer

**Routers (`api/routers/`)**

```python
@router.post("/characters/", response_model=CharacterResponse)
async def create_character(
    character_data: CharacterCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new character endpoint."""
    service = CharacterService(db)

    # Validate data
    if not character_data.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Character name cannot be empty"
        )

    # Create character
    character = await service.create_character(character_data.dict())

    # Invalidate cache
    cache_manager = await get_cache_manager()
    await cache_manager.invalidate_character(character.id)

    return character.to_dict()
```

**Schemas (`api/schemas/`)**

```python
class CharacterBase(BaseModel):
    """Base character schema with validation."""

    name: str = Field(..., min_length=1, max_length=100)
    character_class: CharacterClass = Field(...)
    level: int = Field(..., ge=1, le=20)

    @validator('level')
    def validate_level(cls, v):
        if v < 1 or v > 20:
            raise ValueError("Level must be between 1 and 20")
        return v
```

### 3. AI/ML System

**Character Personality (`ai/personality/personality_engine.py`)**

```python
class PersonalityEngine:
    """Manages character personality and behavior."""

    def __init__(self):
        self.traits = PersonalityTraits()
        self.decision_maker = DecisionMaker()
        self.evolution = PersonalityEvolution()

    async def make_decision(
        self,
        character_id: str,
        context: str,
        options: List[str]
    ) -> Decision:
        """Make a personality-driven decision."""
        # Get current personality
        personality = await self.get_personality(character_id)

        # Use appropriate decision model
        if self.is_critical_decision(context):
            decision = await self.decision_maker.critical_mode(
                personality, context, options
            )
        else:
            decision = await self.decision_maker.standard_mode(
                personality, context, options
            )

        # Update personality based on decision
        await self.update_from_decision(character_id, decision)

        return decision
```

### 4. Caching System

**Cache Manager (`cache/cache_manager.py`)**

```python
class CacheManager:
    """Multi-layer caching with Redis backend."""

    def __init__(self):
        self.redis_client = None
        self.json_serializer = JSONSerializer()
        self.l1_cache = {}  # In-memory cache

    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: int = 3600
    ) -> Any:
        """Get from cache or compute and cache."""
        # L1: In-memory cache
        if key in self.l1_cache:
            return self.l1_cache[key]

        # L2: Redis cache
        cached = await self.redis_client.get(key)
        if cached:
            # Promote to L1 if hot
            self.l1_cache[key] = cached
            return cached

        # Compute and cache
        value = await factory()
        serialized = self.json_serializer.serialize(value)
        await self.redis_client.set(key, serialized, ex=ttl)

        # Store in L1
        self.l1_cache[key] = value
        return value
```

---

## 🤖 Advanced Development Topics

### 1. Performance Optimization

**Query Optimization**

```python
# Use async generators for large datasets
async def stream_characters(
    self,
    filters: Dict[str, Any]
) -> AsyncGenerator[Character, None]:
    """Stream characters efficiently."""
    offset = 0
    batch_size = 100

    while True:
        # Use async generator
        async with self.db.execute(
            select(Character)
            .where(**filters)
            .offset(offset)
            .limit(batch_size)
        ) as result:
            batch = result.scalars().all()
            if not batch:
                break

            for character in batch:
                yield character

            offset += batch_size
```

**Batch Operations**

```python
async def bulk_update_characters(
    self,
    updates: List[Dict[str, Any]]
) -> int:
    """Update multiple characters efficiently."""
    # Use bulk update
    stmt = update(Character)
    batch_size = 50

    updated = 0
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i + batch_size]

        # Execute batch update
        result = await self.db.execute(
            stmt,
            batch
        )
        updated += result.rowcount

        await self.db.commit()

    return updated
```

### 2. AI/ML Performance

**Model Quantization**

```python
class ModelQuantizer:
    """Optimize AI models for faster inference."""

    def __init__(self):
        self.quantization_config = {
            "weight_quantization": {
                "per_channel": True,
                "dtype": "int8"
            },
            "torch_dtype": "float16"
        }

    async def quantize_model(
        self,
        model_path: str,
        output_path: str
    ) -> QuantizedModel:
        """Quantize a model for production."""
        from optimum.intel import quantization

        # Load model
        model = await self.load_model(model_path)

        # Quantize
        quantized = quantization.quantization_dynamic(
            model,
            **self.quantization_config
        )

        # Save quantized model
        quantized.save_pretrained(output_path)

        return quantized
```

**Batch Inference**

```python
class BatchInferenceEngine:
    """Batch AI requests for efficiency."""

    def __init__(self):
        self.batch_collector = BatchCollector(
            max_wait_time=0.1,
            max_batch_size=32
        )
        self.inference_pool = ProcessPoolExecutor(max_workers=4)

    async def infer(
        self,
        requests: List[InferenceRequest]
    ) -> List[InferenceResponse]:
        """Batch inference for multiple requests."""
        # Group by model
        batches = self.batch_collector.group_by_model(requests)

        results = []
        for model_type, model_requests in batches.items():
            # Process batch
            batch_results = await self.process_batch(
                model_type, model_requests
            )
            results.extend(batch_results)

        return results
```

### 3. WebSocket Real-time

**Connection Management**

```python
class ConnectionManager:
    """Manages WebSocket connections efficiently."""

    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.session_subscriptions: Dict[str, Set[str]] = {}
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}

    async def handle_message(
        self,
        connection_id: str,
        message: dict
    ) -> None:
        """Handle incoming WebSocket message."""
        try:
            message_type = message.get("type")

            # Route to appropriate handler
            if message_type == "character_action":
                await self.handle_character_action(
                    connection_id, message
                )
            elif message_type == "dice_roll":
                await self.handle_dice_roll(
                    connection_id, message
                )
            # ... other message types

            # Update heartbeat
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id][
                    "last_heartbeat"
                ] = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error(connection_id, str(e))
```

---

## 🔧 Debugging and Troubleshooting

### 1. Common Issues

**Database Connection Issues**

```python
# Check database health
async def check_database_health() -> bool:
    """Verify database connectivity."""
    try:
        await database.ping()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

# Check Redis health
async def check_redis_health() -> bool:
    """Verify Redis connectivity."""
    try:
        cache_manager = await get_cache_manager()
        return await cache_manager.redis_client.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False
```

**Performance Issues**

```python
# Monitor query performance
@performance_monitor.monitor_query
async def get_character_with_performance(
    character_id: str
) -> Optional[Character]:
    """Get character with performance tracking."""
    start_time = time.time()

    character = await self.character_repository.get_by_id(character_id)

    # Log slow queries
    if time.time() - start_time > 0.5:  # 500ms threshold
        logger.warning(
            f"Slow query detected: get_character({character_id}) "
            f"took {time.time() - start_time:.2f}s"
        )

    return character
```

### 2. Debug Mode

**Enable Debug Logging**

```python
# In config/settings.py
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Add debug middleware
if settings.DEBUG:
    app.add_middleware(DebugMiddleware)
```

**SQL Query Debugging**

```python
# Log all SQL queries
import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

# Or use echo=True in connection string
engine = create_async_engine(
    DATABASE_URL,
    echo=True  # Logs all SQL queries
)
```

### 3. Performance Profiling

**Python Profiler**

```python
# Add to endpoints for profiling
@cProfile
async def slow_endpoint():
    """Profile this endpoint."""
    # ... expensive operation
    return result
```

**Memory Profiling**

```python
# Track memory usage
import tracemalloc

tracemalloc.start()

# ... your code

# Get memory snapshot
snapshot = tracemalloc.take_snapshot()
snapshot = tracemalloc.compare_to(snapshot1)
```

---

## 🧪 Testing Guidelines

### 1. Unit Testing

```python
# Test file: test_character_service.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_create_character():
    """Test character creation."""
    # Arrange
    mock_db = AsyncMock()
    service = CharacterService(mock_db)

    character_data = {
        "name": "Test Character",
        "character_class": "fighter",
        "level": 1
    }

    # Act
    character = await service.create_character(character_data)

    # Assert
    assert character.name == "Test Character"
    assert character.level == 1
    assert character.id is not None
```

### 2. Integration Testing

```python
# Test file: test_api_endpoints.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_character_api_flow():
    """Test complete character API flow."""
    async with AsyncClient(app) as client:
        # Create character
        response = await client.post(
            "/api/v1/characters/",
            json={
                "name": "Test",
                "character_class": "wizard",
                "level": 1
            }
        )
        assert response.status_code == 201

        character_id = response.json()["id"]

        # Get character
        response = await client.get(
            f"/api/v1/characters/{character_id}"
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Test"

        # Update character
        response = await client.put(
            f"/api/v1/characters/{character_id}",
            json={"level": 2}
        )
        assert response.status_code == 200
        assert response.json()["level"] == 2

        # Delete character
        response = await client.delete(
            f"/api/v1/characters/{character_id}"
        )
        assert response.status_code == 204
```

### 3. Load Testing

```python
# test_load.py
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

@task
def load_api_endpoint(user):
    """Load test for API endpoints."""
    response = user.client.get("/api/v1/characters/")
    if response.status_code == 200:
        response.success()
    else:
        response.failure(f"Status: {response.status_code}")
```

---

## 📚 Monitoring and Observability

### 1. Metrics Collection

```python
# In monitoring/metrics.py
from prometheus_client import Counter, Histogram

class MetricsCollector:
    """Collect application metrics."""

    def __init__(self):
        # Counters
        self.http_requests_total = Counter(
            'dmlog_http_requests_total',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )

        # Histograms
        self.request_duration = Histogram(
            'dmlog_request_duration_seconds',
            ['method', 'endpoint'],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
```

### 2. Health Checks

```python
# In api/routers/health.py
@router.get("/api/v1/health/detailed")
async def detailed_health():
    """Comprehensive health check."""
    health_info = {
        "status": "healthy",
        "checks": {}
    }

    # Database health
    try:
        db_healthy = await database.health_check()
        health_info["checks"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "response_time_ms": await get_db_response_time()
        }
    except Exception as e:
        health_info["checks"]["database"] = {
            "status": "error",
            "error": str(e)
        }

    return health_info
```

### 3. Error Tracking

```python
# In api/middleware/error_handler.py
class ErrorHandlingMiddleware:
    """Global error handling middleware."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            # Log full context
            logger.error(
                f"Unhandled error: {exc}",
                extra={
                    "request_id": getattr(
                        request.state,
                        "request_id",
                        "unknown"
                    ),
                    "traceback": traceback.format_exc()
                },
                exc_info=True
            )

            # Return user-friendly error
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": getattr(
                        request.state,
                        "request_id",
                        "unknown"
                    )
                }
            )
```

---

## 📋 Performance Best Practices

### 1. Database Optimization

```python
# Use selectin for related data
stmt = (
    select(Character)
    .options(selectinload(Character.memories))
    .where(Character.level > 5)
)

# Use indexes
class Character(Base):
    __table__table_args__ = {
        "indexes": [
            Index("idx_character_level", "level"),
            Index("idx_character_name", "name"),
            Index("idx_character_class", "character_class"),
        ]
    }
```

### 2. Async Patterns

```python
# Use asyncio.gather for concurrent operations
async def get_characters_with_memories(
    character_ids: List[str]
) -> List[Character]:
    """Get characters and their memories concurrently."""
    tasks = [
        self.get_character_with_memories(cid)
        for cid in character_ids
    ]

    characters = await asyncio.gather(*tasks)
    return characters
```

### 3. Caching Strategy

```python
# Cache at multiple levels
@lru_cache(maxsize=1000)
def get_cached_character(character_id: str):
    """L1: In-memory cache."""
    pass

@cache(ttl=300)
async def get_database_character(character_id: str):
    """L2: Redis cache."""
    pass

# Use cache-aside pattern
async def get_character_stats(
    character_id: str
) -> Dict:
    """Get character statistics with caching."""
    cache_key = f"character_stats:{character_id}"

    # Try cache first
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached

    # Compute and cache
    stats = await self.compute_stats(character_id)
    await cache_manager.set(cache_key, stats, ttl=300)
    return stats
```

---

## 🚀 Deployment and Operations

### 1. Development

```bash
# Quick setup
./scripts/setup.sh

# Start development
./deploy.sh development

# Run tests
pytest
```

### 2. Staging

```bash
# Deploy to staging
./deploy.sh staging

# Run integration tests
pytest tests/integration/

# Run performance tests
pytest tests/load/
```

### 3. Production

```bash
# Deploy to production
./deploy.sh production

# Monitor health
curl https://api.dmlog.com/api/v1/health

# Check logs
kubectl logs -f deployment/dmlog-api
```

---

## 🔐 Security Best Practices

### 1. Input Validation

```python
# Always validate input
@router.post("/characters/")
async def create_character(
    character_data: CharacterCreate,
    db: AsyncSession = Depends(get_db_session)
):
    # Pydantic handles validation automatically
    # No manual validation needed

    # Service layer validation
    if not character_data.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Name cannot be empty"
        )

    # Process request
    character = await service.create_character(character_data.dict())
    return character
```

### 2. SQL Injection Prevention

```python
# Use parameterized queries
query = text("SELECT * FROM characters WHERE level > :level")
await db.execute(query, {"level": 5})

# Never format queries with user input
# BAD: f"SELECT * FROM characters WHERE name = '{name}'"
# GOOD: Using parameterized queries above
```

### 3. Authentication

```python
# Use JWT for authentication
@router.get("/me")
async def get_current_user(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user."""
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "permissions": current_user.permissions
    }
```

---

## 🎯 Continuous Improvement

### 1. Code Quality

```bash
# Format code
black source_code/backend/
isort source_code/backend/

# Lint code
flake8 source_code/backend/

# Type check
mypy source_code/backend/
```

### 2. Documentation

```python
# Docstrings for all public methods
def create_character(self, name: str) -> Character:
    """
    Create a new D&D character.

    Args:
        name: Character name (1-100 characters)

    Returns:
        Created character object

    Raises:
        ValidationError: If name is invalid
    """
    pass

# Type hints everywhere
def process_decision(
    self,
    character_id: str,
    context: str
) -> Decision:
    """Process character decision with AI."""
    pass
```

### 3. Monitoring

```python
# Set up alerts for critical metrics
- High error rate (>5%)
- Slow response time (>1s)
- Database connections (>80%)
- Memory usage (>90%)
```

---

## 🤝 Getting Help

### 1. Documentation

- **Technical Docs**: `/docs/technical/`
- **API Reference**: http://localhost:8000/docs
- **Troubleshooting**: `/docs/technical/troubleshooting.md`

### 2. Team Communication

- **Slack**: #devs for development help
- **Issues**: GitHub issues for bugs
- **Discussions**: GitHub discussions for questions

### 3. Code Review

- All PRs require review
- Use constructive feedback
- Focus on code quality and design

---

## 🎓 Your First Week Goals

### Day 1-2: Environment Setup
- [ ] Set up local development environment
- [ ] Run the test suite successfully
- [ ] Make your first commit
- [ ] Introduce yourself on Slack

### Day 3-4: First Contribution
- [ ] Fix any existing issues
- [ ] Add a new test case
- [ ] Document a feature
- [ ] Submit your first PR

### Day 5: Deep Dive
- [ ] Understand the AI system
- [ ] Add a small feature
- [] Optimize a query
- [ ] Review a peer's PR

---

## 🚀 Success Metrics

### What Success Looks Like

- **Code Quality**: Clean, tested, documented code
- **Performance**: Efficient, scalable solutions
- **Collaboration**: Helpful reviews and feedback
- **Learning**: Continuous improvement and growth

### Career Growth

- **Junior → Mid-level**: Master core systems
- **Mid-level → Senior**: Architecture and leadership
- **Senior → Lead**: Technical vision and mentoring

---

## 🎓 Next Steps

1. **Choose an area** to specialize:
   - Backend development
   - AI/ML engineering
   - Frontend development
   - DevOps/Infrastructure
   - Security engineering

2. **Deepen expertise** in your chosen area
3. **Mentor others** as you grow
4. **Lead projects** and drive innovation
5. **Shape the future** of DMLog

---

## 👥 We're Excited to Have You!

Welcome to the DMLog team! You're joining a project at the intersection of traditional gaming and cutting-edge AI. We're building something truly special here, and your contributions will help shape the future of digital D&D.

Don't hesitate to ask questions, request help, or suggest improvements. We value diverse perspectives and believe great ideas can come from anywhere.

**Let's build something amazing together!** 🎲✨

---

*This guide is a living document. Please suggest improvements to help future developers.*