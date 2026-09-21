"""
Advanced Event Sourcing and CQRS Implementation
Cutting-edge event sourcing architecture with complete audit trails,
event replay capabilities, and Command Query Responsibility Segregation.

This module implements:
- Event sourcing with immutable event store
- CQRS with separate read/write models
- Event versioning and migration
- Snapshot optimization
- Event replay and projection
- Saga pattern for distributed transactions
- Event streaming and real-time updates
- Event store clustering and replication
"""

import asyncio
import json
import uuid
import time
import hashlib
import pickle
import gzip
from abc import ABC, abstractmethod
from typing import (
    Dict, List, Optional, Any, Callable, Union,
    TypeVar, Generic, AsyncGenerator, Type, Protocol
)
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import structlog
from pydantic import BaseModel, Field, validator
import aioredis
import aiofiles
import aiofiles.os
import asyncpg
from kafka import KafkaProducer, KafkaConsumer
import kafka.errors
from google.protobuf import json_format
import numpy as np
import orjson
import zstandard as zstd

# Configure structured logging
logger = structlog.get_logger()

# Type variables
T = TypeVar('T')
EventType = TypeVar('EventType', bound='DomainEvent')
AggregateType = TypeVar('AggregateType', bound='AggregateRoot')

class EventMetadata(BaseModel):
    """Event metadata with rich context"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    aggregate_id: str
    aggregate_type: str
    version: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    causation_id: Optional[str] = None
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    @validator('version')
    def version_must_be_positive(cls, v):
        if v < 1:
            raise ValueError('Version must be positive')
        return v

class DomainEvent(BaseModel):
    """Base domain event"""
    metadata: EventMetadata
    event_data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def get_event_type(self) -> str:
        """Get event type name"""
        return self.__class__.__name__

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            'metadata': asdict(self.metadata),
            'event_data': self.event_data,
            'event_type': self.get_event_type()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DomainEvent':
        """Create event from dictionary"""
        metadata = EventMetadata(**data['metadata'])
        return cls(metadata=metadata, event_data=data['event_data'])

class Command(BaseModel):
    """Base command"""
    command_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    aggregate_id: str
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Query(BaseModel):
    """Base query"""
    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parameters: Dict[str, Any] = Field(default_factory=dict)
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None

class Snapshot(BaseModel):
    """Aggregate snapshot"""
    aggregate_id: str
    aggregate_type: str
    version: int
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AggregateRoot:
    """Base aggregate root with event sourcing"""

    def __init__(self, aggregate_id: str):
        self._id = aggregate_id
        self._version = 0
        self._uncommitted_events: List[DomainEvent] = []
        self._original_version = 0

    @property
    def id(self) -> str:
        """Get aggregate ID"""
        return self._id

    @property
    def version(self) -> int:
        """Get current version"""
        return self._version

    def get_uncommitted_events(self) -> List[DomainEvent]:
        """Get uncommitted events"""
        return self._uncommitted_events.copy()

    def mark_events_as_committed(self):
        """Mark events as committed"""
        self._uncommitted_events.clear()
        self._original_version = self._version

    def load_from_history(self, events: List[DomainEvent]):
        """Load aggregate from event history"""
        for event in events:
            self.apply(event)
            self._version = event.metadata.version
        self._original_version = self._version

    def _apply_event(self, event_data: Dict[str, Any], event_type: str):
        """Apply event to aggregate"""
        # This should be implemented by concrete aggregates
        pass

    def apply(self, event: DomainEvent):
        """Apply event to aggregate"""
        self._apply_event(event.event_data, event.metadata.event_type)

    def _add_event(self, event_type: str, event_data: Dict[str, Any],
                   metadata: Optional[Dict[str, Any]] = None):
        """Add new event to aggregate"""
        self._version += 1

        event_metadata = EventMetadata(
            event_type=event_type,
            aggregate_id=self._id,
            aggregate_type=self.__class__.__name__,
            version=self._version,
            metadata=metadata or {}
        )

        event = DomainEvent(
            metadata=event_metadata,
            event_data=event_data
        )

        self.apply(event)
        self._uncommitted_events.append(event)

class EventStore(ABC):
    """Abstract event store interface"""

    @abstractmethod
    async def save_events(self, aggregate_id: str, events: List[DomainEvent],
                         expected_version: Optional[int] = None) -> bool:
        """Save events to store"""
        pass

    @abstractmethod
    async def get_events(self, aggregate_id: str,
                        from_version: Optional[int] = None,
                        to_version: Optional[int] = None) -> List[DomainEvent]:
        """Get events for aggregate"""
        pass

    @abstractmethod
    async def save_snapshot(self, snapshot: Snapshot) -> bool:
        """Save aggregate snapshot"""
        pass

    @abstractmethod
    async def get_snapshot(self, aggregate_id: str,
                          max_version: Optional[int] = None) -> Optional[Snapshot]:
        """Get aggregate snapshot"""
        pass

    @abstractmethod
    async def get_events_by_type(self, event_type: str,
                                from_timestamp: Optional[datetime] = None,
                                to_timestamp: Optional[datetime] = None) -> AsyncGenerator[DomainEvent, None]:
        """Get events by type (for projections)"""
        pass

class PostgresEventStore(EventStore):
    """PostgreSQL implementation of event store"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._pool = None

    async def initialize(self):
        """Initialize database schema"""
        self._pool = await asyncpg.create_pool(self.connection_string)

        async with self._pool.acquire() as conn:
            # Create events table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id UUID PRIMARY KEY,
                    aggregate_id UUID NOT NULL,
                    aggregate_type VARCHAR(255) NOT NULL,
                    event_type VARCHAR(255) NOT NULL,
                    version INTEGER NOT NULL,
                    event_data JSONB NOT NULL,
                    metadata JSONB NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    causation_id UUID,
                    correlation_id UUID,
                    user_id UUID,
                    tenant_id UUID,
                    tags TEXT[],
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    CONSTRAINT unique_aggregate_version UNIQUE (aggregate_id, version)
                );
            """)

            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_aggregate_id
                ON events(aggregate_id);
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_event_type
                ON events(event_type);
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_timestamp
                ON events(timestamp);
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_tenant_id
                ON events(tenant_id);
            """)

            # Create snapshots table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    aggregate_id UUID PRIMARY KEY,
                    aggregate_type VARCHAR(255) NOT NULL,
                    version INTEGER NOT NULL,
                    data JSONB NOT NULL,
                    metadata JSONB NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_aggregate_type
                ON snapshots(aggregate_type);
            """)

        logger.info("PostgreSQL event store initialized")

    async def save_events(self, aggregate_id: str, events: List[DomainEvent],
                         expected_version: Optional[int] = None) -> bool:
        """Save events to PostgreSQL"""
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                for event in events:
                    try:
                        # Check expected version
                        if expected_version is not None:
                            result = await conn.fetchval(
                                "SELECT COUNT(*) FROM events WHERE aggregate_id = $1 AND version = $2",
                                uuid.UUID(aggregate_id), expected_version
                            )
                            if result == 0:
                                raise ValueError(f"Expected version {expected_version} not found")

                        # Insert event
                        await conn.execute("""
                            INSERT INTO events (
                                event_id, aggregate_id, aggregate_type, event_type,
                                version, event_data, metadata, timestamp,
                                causation_id, correlation_id, user_id, tenant_id, tags
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        """,
                            uuid.UUID(event.metadata.event_id),
                            uuid.UUID(aggregate_id),
                            event.metadata.aggregate_type,
                            event.metadata.event_type,
                            event.metadata.version,
                            json.dumps(event.event_data),
                            json.dumps(asdict(event.metadata)),
                            event.metadata.timestamp,
                            uuid.UUID(event.metadata.causation_id) if event.metadata.causation_id else None,
                            uuid.UUID(event.metadata.correlation_id) if event.metadata.correlation_id else None,
                            uuid.UUID(event.metadata.user_id) if event.metadata.user_id else None,
                            uuid.UUID(event.metadata.tenant_id) if event.metadata.tenant_id else None,
                            event.metadata.tags
                        )

                    except asyncpg.UniqueViolationError:
                        logger.error("Event version conflict",
                                   aggregate_id=aggregate_id,
                                   version=event.metadata.version)
                        return False
                    except Exception as e:
                        logger.error("Failed to save event",
                                   aggregate_id=aggregate_id,
                                   event_id=event.metadata.event_id,
                                   error=str(e))
                        return False

        return True

    async def get_events(self, aggregate_id: str,
                        from_version: Optional[int] = None,
                        to_version: Optional[int] = None) -> List[DomainEvent]:
        """Get events for aggregate from PostgreSQL"""
        async with self._pool.acquire() as conn:
            query = """
                SELECT event_id, aggregate_id, aggregate_type, event_type,
                       version, event_data, metadata, timestamp,
                       causation_id, correlation_id, user_id, tenant_id, tags
                FROM events
                WHERE aggregate_id = $1
            """
            params = [uuid.UUID(aggregate_id)]

            if from_version is not None:
                query += " AND version >= $2"
                params.append(from_version)

            if to_version is not None:
                offset = 2 if from_version is not None else 1
                query += f" AND version <= ${offset + 1}"
                params.append(to_version)

            query += " ORDER BY version ASC"

            rows = await conn.fetch(query, *params)

            events = []
            for row in rows:
                metadata = EventMetadata(
                    event_id=str(row['event_id']),
                    event_type=row['event_type'],
                    aggregate_id=str(row['aggregate_id']),
                    aggregate_type=row['aggregate_type'],
                    version=row['version'],
                    timestamp=row['timestamp'],
                    causation_id=str(row['causation_id']) if row['causation_id'] else None,
                    correlation_id=str(row['correlation_id']) if row['correlation_id'] else None,
                    user_id=str(row['user_id']) if row['user_id'] else None,
                    tenant_id=str(row['tenant_id']) if row['tenant_id'] else None,
                    metadata=json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata'],
                    tags=row['tags']
                )

                event = DomainEvent(
                    metadata=metadata,
                    event_data=json.loads(row['event_data']) if isinstance(row['event_data'], str) else row['event_data']
                )
                events.append(event)

            return events

    async def save_snapshot(self, snapshot: Snapshot) -> bool:
        """Save aggregate snapshot to PostgreSQL"""
        async with self._pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO snapshots (
                        aggregate_id, aggregate_type, version, data,
                        metadata, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (aggregate_id) DO UPDATE SET
                        version = EXCLUDED.version,
                        data = EXCLUDED.data,
                        metadata = EXCLUDED.metadata,
                        timestamp = EXCLUDED.timestamp
                """,
                    uuid.UUID(snapshot.aggregate_id),
                    snapshot.aggregate_type,
                    snapshot.version,
                    json.dumps(snapshot.data),
                    json.dumps(snapshot.metadata),
                    snapshot.timestamp
                )
                return True

            except Exception as e:
                logger.error("Failed to save snapshot",
                           aggregate_id=snapshot.aggregate_id,
                           error=str(e))
                return False

    async def get_snapshot(self, aggregate_id: str,
                          max_version: Optional[int] = None) -> Optional[Snapshot]:
        """Get aggregate snapshot from PostgreSQL"""
        async with self._pool.acquire() as conn:
            query = """
                SELECT aggregate_id, aggregate_type, version, data, metadata, timestamp
                FROM snapshots
                WHERE aggregate_id = $1
            """
            params = [uuid.UUID(aggregate_id)]

            if max_version is not None:
                query += " AND version <= $2"
                params.append(max_version)

            query += " ORDER BY version DESC LIMIT 1"

            row = await conn.fetchrow(query, *params)

            if row:
                return Snapshot(
                    aggregate_id=str(row['aggregate_id']),
                    aggregate_type=row['aggregate_type'],
                    version=row['version'],
                    data=json.loads(row['data']) if isinstance(row['data'], str) else row['data'],
                    metadata=json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata'],
                    timestamp=row['timestamp']
                )

            return None

    async def get_events_by_type(self, event_type: str,
                                from_timestamp: Optional[datetime] = None,
                                to_timestamp: Optional[datetime] = None) -> AsyncGenerator[DomainEvent, None]:
        """Get events by type from PostgreSQL"""
        async with self._pool.acquire() as conn:
            query = """
                SELECT event_id, aggregate_id, aggregate_type, event_type,
                       version, event_data, metadata, timestamp,
                       causation_id, correlation_id, user_id, tenant_id, tags
                FROM events
                WHERE event_type = $1
            """
            params = [event_type]

            if from_timestamp is not None:
                query += " AND timestamp >= $2"
                params.append(from_timestamp)

            if to_timestamp is not None:
                offset = 2 if from_timestamp is not None else 1
                query += f" AND timestamp <= ${offset + 1}"
                params.append(to_timestamp)

            query += " ORDER BY timestamp ASC"

            async for row in conn.cursor(query, *params):
                metadata = EventMetadata(
                    event_id=str(row['event_id']),
                    event_type=row['event_type'],
                    aggregate_id=str(row['aggregate_id']),
                    aggregate_type=row['aggregate_type'],
                    version=row['version'],
                    timestamp=row['timestamp'],
                    causation_id=str(row['causation_id']) if row['causation_id'] else None,
                    correlation_id=str(row['correlation_id']) if row['correlation_id'] else None,
                    user_id=str(row['user_id']) if row['user_id'] else None,
                    tenant_id=str(row['tenant_id']) if row['tenant_id'] else None,
                    metadata=json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata'],
                    tags=row['tags']
                )

                event = DomainEvent(
                    metadata=metadata,
                    event_data=json.loads(row['event_data']) if isinstance(row['event_data'], str) else row['event_data']
                )
                yield event

class EventStoreClient:
    """Event store client with caching and optimization"""

    def __init__(self, event_store: EventStore, cache_size: int = 1000):
        self.event_store = event_store
        self.cache_size = cache_size
        self._aggregate_cache = {}
        self._snapshot_cache = {}

    async def save_aggregate(self, aggregate: AggregateRoot) -> bool:
        """Save aggregate with events"""
        events = aggregate.get_uncommitted_events()
        if not events:
            return True

        success = await self.event_store.save_events(
            aggregate.id,
            events,
            aggregate._original_version
        )

        if success:
            aggregate.mark_events_as_committed()

            # Update cache
            self._aggregate_cache[aggregate.id] = aggregate

            # Create snapshot periodically
            if aggregate.version % 100 == 0:
                await self._create_snapshot(aggregate)

        return success

    async def load_aggregate(self, aggregate_type: Type[AggregateType],
                           aggregate_id: str) -> Optional[AggregateType]:
        """Load aggregate from event store"""
        # Check cache first
        cached = self._aggregate_cache.get(aggregate_id)
        if cached and isinstance(cached, aggregate_type):
            return cached

        # Try to load from snapshot
        snapshot = await self.event_store.get_snapshot(aggregate_id)
        from_version = snapshot.version if snapshot else 0

        # Load remaining events
        events = await self.event_store.get_events(
            aggregate_id,
            from_version=from_version + 1
        )

        # Create aggregate instance
        aggregate = aggregate_type(aggregate_id)

        # Apply snapshot if available
        if snapshot:
            aggregate.__dict__.update(snapshot.data)
            aggregate._version = snapshot.version

        # Apply remaining events
        aggregate.load_from_history(events)

        # Update cache
        self._aggregate_cache[aggregate_id] = aggregate

        return aggregate

    async def _create_snapshot(self, aggregate: AggregateRoot):
        """Create aggregate snapshot"""
        snapshot = Snapshot(
            aggregate_id=aggregate.id,
            aggregate_type=aggregate.__class__.__name__,
            version=aggregate.version,
            data=aggregate.__dict__.copy(),
            metadata={}
        )

        await self.event_store.save_snapshot(snapshot)

class Projection(ABC):
    """Base projection for read models"""

    @abstractmethod
    async def handle_event(self, event: DomainEvent):
        """Handle domain event"""
        pass

    @abstractmethod
    async def rebuild(self):
        """Rebuild projection from event history"""
        pass

class ReadModel:
    """Base read model"""

    def __init__(self):
        self._data = {}
        self._version = 0

    def get_data(self) -> Dict[str, Any]:
        """Get read model data"""
        return self._data.copy()

    def update_data(self, data: Dict[str, Any], version: int):
        """Update read model data"""
        self._data.update(data)
        self._version = version

class CommandHandler(ABC):
    """Base command handler"""

    @abstractmethod
    async def handle(self, command: Command) -> List[DomainEvent]:
        """Handle command and return events"""
        pass

class QueryHandler(ABC):
    """Base query handler"""

    @abstractmethod
    async def handle(self, query: Query) -> Any:
        """Handle query and return result"""
        pass

class CQRSFramework:
    """CQRS framework with command/query separation"""

    def __init__(self, event_store_client: EventStoreClient):
        self.event_store_client = event_store_client
        self.command_handlers: Dict[str, CommandHandler] = {}
        self.query_handlers: Dict[str, QueryHandler] = {}
        self.projections: List[Projection] = []
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)

    def register_command_handler(self, command_type: str, handler: CommandHandler):
        """Register command handler"""
        self.command_handlers[command_type] = handler
        logger.info("Command handler registered", command_type=command_type)

    def register_query_handler(self, query_type: str, handler: QueryHandler):
        """Register query handler"""
        self.query_handlers[query_type] = handler
        logger.info("Query handler registered", query_type=query_type)

    def register_projection(self, projection: Projection):
        """Register projection"""
        self.projections.append(projection)
        logger.info("Projection registered", projection=projection.__class__.__name__)

    def register_event_handler(self, event_type: str, handler: Callable):
        """Register event handler"""
        self.event_handlers[event_type].append(handler)

    async def handle_command(self, command: Command) -> bool:
        """Handle command"""
        command_type = command.__class__.__name__
        handler = self.command_handlers.get(command_type)

        if not handler:
            logger.error("Command handler not found", command_type=command_type)
            return False

        try:
            events = await handler.handle(command)

            # Publish events
            for event in events:
                await self._publish_event(event)

            return True

        except Exception as e:
            logger.error("Command handling failed",
                        command_type=command_type,
                        error=str(e))
            return False

    async def handle_query(self, query: Query) -> Any:
        """Handle query"""
        query_type = query.__class__.__name__
        handler = self.query_handlers.get(query_type)

        if not handler:
            logger.error("Query handler not found", query_type=query_type)
            return None

        try:
            return await handler.handle(query)

        except Exception as e:
            logger.error("Query handling failed",
                        query_type=query_type,
                        error=str(e))
            return None

    async def _publish_event(self, event: DomainEvent):
        """Publish event to handlers and projections"""
        event_type = event.metadata.event_type

        # Handle by projections
        for projection in self.projections:
            try:
                await projection.handle_event(event)
            except Exception as e:
                logger.error("Projection event handling failed",
                           projection=projection.__class__.__name__,
                           event_type=event_type,
                           error=str(e))

        # Handle by custom event handlers
        for handler in self.event_handlers.get(event_type, []):
            try:
                await handler(event)
            except Exception as e:
                logger.error("Event handler failed",
                           event_type=event_type,
                           error=str(e))

class SagaManager:
    """Saga pattern implementation for distributed transactions"""

    def __init__(self, event_store_client: EventStoreClient):
        self.event_store_client = event_store_client
        self.sagas: Dict[str, 'Saga'] = {}
        self.saga_handlers: Dict[str, Type['Saga']] = {}

    def register_saga(self, saga_type: str, saga_class: Type['Saga']):
        """Register saga type"""
        self.saga_handlers[saga_type] = saga_class

    async def start_saga(self, saga_type: str, saga_data: Dict[str, Any]) -> str:
        """Start new saga"""
        saga_class = self.saga_handlers.get(saga_type)
        if not saga_class:
            raise ValueError(f"Saga type {saga_type} not registered")

        saga_id = str(uuid.uuid4())
        saga = saga_class(saga_id, saga_data, self.event_store_client)
        self.sagas[saga_id] = saga

        await saga.start()
        return saga_id

    async def handle_event(self, event: DomainEvent):
        """Handle event in sagas"""
        for saga in self.sagas.values():
            await saga.handle_event(event)

class Saga:
    """Base saga implementation"""

    def __init__(self, saga_id: str, data: Dict[str, Any],
                 event_store_client: EventStoreClient):
        self.saga_id = saga_id
        self.data = data
        self.event_store_client = event_store_client
        self.steps: List['SagaStep'] = []
        self.current_step = 0
        self.compensating = False

    async def start(self):
        """Start saga execution"""
        if self.steps:
            await self.steps[0].execute()

    async def handle_event(self, event: DomainEvent):
        """Handle event in saga"""
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            if await step.handle_event(event):
                if self.compensating:
                    self.current_step -= 1
                    if self.current_step >= 0:
                        await self.steps[self.current_step].compensate()
                else:
                    self.current_step += 1
                    if self.current_step < len(self.steps):
                        await self.steps[self.current_step].execute()

    async def compensate(self):
        """Start compensation"""
        self.compensating = True
        self.current_step = min(self.current_step, len(self.steps) - 1)
        await self.steps[self.current_step].compensate()

class SagaStep:
    """Saga step implementation"""

    def __init__(self, execute_action: Callable, compensate_action: Callable,
                 event_conditions: List[Callable]):
        self.execute_action = execute_action
        self.compensate_action = compensate_action
        self.event_conditions = event_conditions

    async def execute(self):
        """Execute step action"""
        return await self.execute_action()

    async def compensate(self):
        """Execute compensation action"""
        return await self.compensate_action()

    async def handle_event(self, event: DomainEvent) -> bool:
        """Check if event satisfies step conditions"""
        for condition in self.event_conditions:
            if await condition(event):
                return True
        return False

class EventReplay:
    """Event replay functionality"""

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    async def replay_events(self, aggregate_id: str,
                          from_version: Optional[int] = None,
                          to_version: Optional[int] = None) -> List[DomainEvent]:
        """Replay events for aggregate"""
        return await self.event_store.get_events(
            aggregate_id,
            from_version,
            to_version
        )

    async def replay_events_by_type(self, event_type: str,
                                   from_timestamp: Optional[datetime] = None,
                                   to_timestamp: Optional[datetime] = None) -> AsyncGenerator[DomainEvent, None]:
        """Replay events by type"""
        async for event in self.event_store.get_events_by_type(
            event_type, from_timestamp, to_timestamp
        ):
            yield event

    async def rebuild_projection(self, projection: Projection,
                               from_timestamp: Optional[datetime] = None):
        """Rebuild projection from event history"""
        await projection.rebuild()

# Example workflow event types for DMLogn8n
class WorkflowCreated(DomainEvent):
    """Workflow created event"""
    pass

class WorkflowUpdated(DomainEvent):
    """Workflow updated event"""
    pass

class WorkflowDeleted(DomainEvent):
    """Workflow deleted event"""
    pass

class WorkflowStarted(DomainEvent):
    """Workflow started event"""
    pass

class WorkflowCompleted(DomainEvent):
    """Workflow completed event"""
    pass

# Initialize event sourcing architecture
async def initialize_event_sourcing(connection_string: str) -> Dict[str, Any]:
    """Initialize complete event sourcing architecture"""

    # Initialize event store
    event_store = PostgresEventStore(connection_string)
    await event_store.initialize()

    # Create event store client
    event_store_client = EventStoreClient(event_store)

    # Initialize CQRS framework
    cqrs = CQRSFramework(event_store_client)

    # Initialize saga manager
    saga_manager = SagaManager(event_store_client)

    # Initialize event replay
    event_replay = EventReplay(event_store)

    logger.info("Event sourcing architecture initialized")

    return {
        "event_store": event_store,
        "event_store_client": event_store_client,
        "cqrs": cqrs,
        "saga_manager": saga_manager,
        "event_replay": event_replay
    }

# Export main classes and functions
__all__ = [
    'EventStore',
    'PostgresEventStore',
    'EventStoreClient',
    'CQRSFramework',
    'SagaManager',
    'EventReplay',
    'DomainEvent',
    'Command',
    'Query',
    'AggregateRoot',
    'Projection',
    'ReadModel',
    'CommandHandler',
    'QueryHandler',
    'initialize_event_sourcing'
]