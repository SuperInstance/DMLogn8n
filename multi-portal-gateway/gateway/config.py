"""
Configuration settings for the Multi-Portal Gateway System.
"""

from pydantic import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings."""

    # Gateway Configuration
    GATEWAY_HOST: str = "0.0.0.0"
    GATEWAY_PORT: int = 8000
    DEBUG: bool = True

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./portal_gateway.db"

    # Portal Port Ranges
    CHARACTER_PORT_START: int = 9000
    CHARACTER_PORT_END: int = 9500
    DM_PORT: int = 9501
    CODER_PORT: int = 9502

    # Portal Configuration
    MAX_PORTALS_PER_TYPE: int = 100
    PORTAL_HEARTBEAT_INTERVAL: int = 30  # seconds
    PORTAL_TIMEOUT: int = 300  # seconds
    MAX_CONNECTIONS_PER_PORTAL: int = 10

    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_SIZE: int = 1024 * 1024  # 1MB
    WS_PING_TIMEOUT: int = 10

    # Communication Bridge Configuration
    BRIDGE_BUFFER_SIZE: int = 1000
    MESSAGE_HISTORY_SIZE: int = 100

    # Security Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/portal_gateway.log"

    # AI Integration Configuration
    AI_SERVICE_URL: str = "http://localhost:11434"  # Ollama
    AI_MODEL: str = "llama2"

    # Redis Configuration (for distributed systems)
    REDIS_URL: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Portal type configurations
PORTAL_TYPES = {
    "character": {
        "port_range": (settings.CHARACTER_PORT_START, settings.CHARACTER_PORT_END),
        "max_instances": settings.MAX_PORTALS_PER_TYPE,
        "description": "Character portal for individual players"
    },
    "dm": {
        "port": settings.DM_PORT,
        "max_instances": 1,
        "description": "Dungeon Master portal for game management"
    },
    "coder": {
        "port": settings.CODER_PORT,
        "max_instances": 1,
        "description": "Coder workshop portal for development"
    }
}

# Event types for inter-portal communication
EVENT_TYPES = {
    "character": [
        "character_update",
        "character_action",
        "character_message",
        "character_status_change"
    ],
    "dm": [
        "world_update",
        "encounter_start",
        "encounter_end",
        "event_injection",
        "world_edit"
    ],
    "coder": [
        "code_update",
        "script_execute",
        "test_run",
        "deploy_change"
    ],
    "system": [
        "portal_created",
        "portal_destroyed",
        "connection_established",
        "connection_lost"
    ]
}