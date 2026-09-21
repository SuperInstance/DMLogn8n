"""
Database models for the Multi-Portal Gateway System.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, Dict, Any
from .database import Base

class PortalType(PyEnum):
    """Enumeration for portal types."""
    CHARACTER = "character"
    DM = "dm"
    CODER = "coder"

class PortalStatus(PyEnum):
    """Enumeration for portal status."""
    CREATING = "creating"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DESTROYED = "destroyed"

class ConnectionType(PyEnum):
    """Enumeration for connection types."""
    WEBSOCKET = "websocket"
    HTTP = "http"
    BRIDGE = "bridge"

class Portal(Base):
    """Portal model representing a portal instance."""
    __tablename__ = "portals"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    portal_type = Column(Enum(PortalType), nullable=False)
    status = Column(Enum(PortalStatus), default=PortalStatus.CREATING)

    # Network configuration
    port = Column(Integer, nullable=False, unique=True)
    host = Column(String, default="localhost")
    url = Column(String, nullable=False)

    # Associated entity (for character portals)
    character_id = Column(String, ForeignKey("characters.id"), nullable=True)

    # Configuration and metadata
    config = Column(JSON, default={})
    metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_heartbeat = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    character = relationship("Character", back_populates="portal")
    sessions = relationship("PortalSession", back_populates="portal", cascade="all, delete-orphan")
    messages = relationship("PortalMessage", back_populates="portal", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Portal(id={self.id}, type={self.portal_type}, status={self.status}, port={self.port})>"

class Character(Base):
    """Character model for character-specific portals."""
    __tablename__ = "characters"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    level = Column(Integer, default=1)
    class_name = Column(String)
    race = Column(String)

    # Character state
    current_hp = Column(Integer)
    max_hp = Column(Integer)
    current_mp = Column(Integer)
    max_mp = Column(Integer)
    status = Column(String, default="active")

    # Character data
    attributes = Column(JSON, default={})
    inventory = Column(JSON, default={})
    spells = Column(JSON, default={})
    abilities = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    portal = relationship("Portal", back_populates="character", uselist=False)

    def __repr__(self):
        return f"<Character(id={self.id}, name={self.name}, level={self.level})>"

class PortalSession(Base):
    """Portal session model for tracking connections."""
    __tablename__ = "portal_sessions"

    id = Column(String, primary_key=True, index=True)
    portal_id = Column(String, ForeignKey("portals.id"), nullable=False)

    # Connection details
    connection_type = Column(Enum(ConnectionType), nullable=False)
    client_ip = Column(String)
    user_agent = Column(Text)
    session_token = Column(String, unique=True, index=True)

    # Session state
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())

    # Session data
    session_data = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    terminated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    portal = relationship("Portal", back_populates="sessions")

    def __repr__(self):
        return f"<PortalSession(id={self.id}, portal={self.portal_id}, active={self.is_active})>"

class PortalMessage(Base):
    """Message model for inter-portal communication."""
    __tablename__ = "portal_messages"

    id = Column(String, primary_key=True, index=True)
    portal_id = Column(String, ForeignKey("portals.id"), nullable=False)

    # Message content
    message_type = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    data = Column(JSON, nullable=False)

    # Message routing
    source_portal = Column(String, nullable=True)
    target_portals = Column(JSON, default=[])  # List of target portal IDs

    # Message state
    is_delivered = Column(Boolean, default=False)
    delivery_attempts = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    portal = relationship("Portal", back_populates="messages")

    def __repr__(self):
        return f"<PortalMessage(id={self.id}, type={self.message_type}, event={self.event_type})>"

class WorldState(Base):
    """World state model for tracking game state."""
    __tablename__ = "world_states"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)

    # World data
    current_location = Column(String)
    game_time = Column(String)
    weather = Column(String)
    environment_state = Column(JSON, default={})

    # Active encounters and events
    active_encounters = Column(JSON, default=[])
    pending_events = Column(JSON, default=[])
    world_events = Column(JSON, default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<WorldState(id={self.id}, name={self.name})>"

class SystemMetrics(Base):
    """System metrics model for monitoring."""
    __tablename__ = "system_metrics"

    id = Column(String, primary_key=True, index=True)

    # Metrics data
    metric_name = Column(String, nullable=False, index=True)
    metric_value = Column(String, nullable=False)
    metric_unit = Column(String)

    # Additional context
    portal_id = Column(String, ForeignKey("portals.id"), nullable=True)
    metadata = Column(JSON, default={})

    # Timestamp
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<SystemMetrics(id={self.id}, name={self.metric_name}, value={self.metric_value})>"