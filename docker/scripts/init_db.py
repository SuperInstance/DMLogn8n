#!/usr/bin/env python3
"""
DMLog Database Initialization Script for Docker Containers
This script initializes the DMLog database with all required tables, indexes,
and initial data when containers are started.

Features:
- Table creation with proper constraints and indexes
- Initial data seeding
- Admin user setup
- Validation data creation
- Error handling and logging
- Transaction management

Usage:
    This script is automatically executed by Docker when the PostgreSQL
    container starts for the first time.

Author: DMLog Development Team
Version: 1.0.0
"""

import os
import sys
import logging
import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from passlib.context import CryptContext
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/postgres/init_db.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'dmlog_db'),
    'user': os.getenv('POSTGRES_USER', 'dmlog_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'dmlog_password')
}

# Admin user configuration
ADMIN_CONFIG = {
    'username': os.getenv('ADMIN_USERNAME', 'admin'),
    'email': os.getenv('ADMIN_EMAIL', 'admin@dmlog.local'),
    'password': os.getenv('ADMIN_PASSWORD', 'admin123'),
    'is_admin': True
}

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class DatabaseInitializer:
    """Database initialization class for DMLog"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.initialized = False

    async def initialize(self) -> bool:
        """Initialize the complete database"""
        try:
            logger.info("Starting DMLog database initialization...")

            # Wait for database to be ready
            await self._wait_for_database()

            # Connect to database
            with self._get_connection() as conn:
                self.connection = conn

                # Create database structure
                await self._create_extensions()
                await self._create_tables()
                await self._create_indexes()
                await self._create_constraints()
                await self._create_triggers()
                await self._seed_initial_data()
                await self._create_admin_user()
                await self._seed_validation_data()

                self.initialized = True
                logger.info("DMLog database initialization completed successfully!")
                return True

        except Exception as e:
            logger.error(f"Database initialization failed: {e}", exc_info=True)
            return False

    async def _wait_for_database(self, max_retries: int = 30, retry_interval: int = 2):
        """Wait for database to be ready"""
        logger.info("Waiting for database to be ready...")

        for attempt in range(max_retries):
            try:
                # Test connection without specifying database
                test_config = self.config.copy()
                test_config.pop('database', None)

                with psycopg2.connect(**test_config) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        result = cursor.fetchone()
                        if result and result[0] == 1:
                            logger.info("Database is ready!")
                            return
            except psycopg2.OperationalError as e:
                logger.warning(f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
                await asyncio.sleep(retry_interval)

        raise Exception("Database is not ready after maximum retries")

    @asynccontextmanager
    def _get_connection(self):
        """Get database connection with proper error handling"""
        try:
            conn = psycopg2.connect(**self.config)
            conn.autocommit = False
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                yield conn, cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    async def _create_extensions(self):
        """Create required PostgreSQL extensions"""
        logger.info("Creating PostgreSQL extensions...")

        extensions = [
            "uuid-ossp",
            "pg_trgm",
            "btree_gin",
            "btree_gist",
            "unaccent",
            "pgcrypto"
        ]

        with self._get_connection() as (conn, cursor):
            for extension in extensions:
                try:
                    cursor.execute(f'CREATE EXTENSION IF NOT EXISTS "{extension}";')
                    logger.info(f"Extension '{extension}' created or already exists")
                except Exception as e:
                    logger.warning(f"Failed to create extension '{extension}': {e}")

    async def _create_tables(self):
        """Create all database tables"""
        logger.info("Creating database tables...")

        with self._get_connection() as (conn, cursor):
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    first_name VARCHAR(50),
                    last_name VARCHAR(50),
                    is_active BOOLEAN DEFAULT TRUE,
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_verified BOOLEAN DEFAULT FALSE,
                    last_login TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    preferences JSONB DEFAULT '{}',
                    metadata JSONB DEFAULT '{}'
                );
            """)

            # Game sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_sessions (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    system VARCHAR(50) DEFAULT 'D&D 5e',
                    status VARCHAR(20) DEFAULT 'planning' CHECK (status IN ('planning', 'active', 'paused', 'completed', 'cancelled')),
                    visibility VARCHAR(20) DEFAULT 'private' CHECK (visibility IN ('public', 'private', 'invite_only')),
                    max_players INTEGER DEFAULT 6,
                    current_players INTEGER DEFAULT 0,
                    session_date TIMESTAMP WITH TIME ZONE,
                    location VARCHAR(200),
                    settings JSONB DEFAULT '{}',
                    tags TEXT[],
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)

            # Characters table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    game_session_id UUID REFERENCES game_sessions(id) ON DELETE SET NULL,
                    name VARCHAR(100) NOT NULL,
                    race VARCHAR(50),
                    class VARCHAR(50),
                    level INTEGER DEFAULT 1,
                    experience INTEGER DEFAULT 0,
                    background TEXT,
                    personality TEXT,
                    appearance TEXT,
                    stats JSONB DEFAULT '{}',
                    inventory JSONB DEFAULT '[]',
                    spells JSONB DEFAULT '[]',
                    abilities JSONB DEFAULT '[]',
                    notes TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)

            # Campaigns table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    game_session_id UUID NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    story_arc VARCHAR(100),
                    current_chapter INTEGER DEFAULT 1,
                    total_chapters INTEGER,
                    world_settings JSONB DEFAULT '{}',
                    npcs JSONB DEFAULT '[]',
                    locations JSONB DEFAULT '[]',
                    items JSONB DEFAULT '[]',
                    lore JSONB DEFAULT '{}',
                    timeline JSONB DEFAULT '[]',
                    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'on_hold')),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)

            # Session logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_logs (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    game_session_id UUID NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    session_number INTEGER NOT NULL,
                    title VARCHAR(200),
                    summary TEXT,
                    content TEXT,
                    events JSONB DEFAULT '[]',
                    participants UUID[] DEFAULT '{}',
                    duration_minutes INTEGER,
                    date_played TIMESTAMP WITH TIME ZONE,
                    dm_notes TEXT,
                    player_notes TEXT,
                    is_public BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    game_session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
                    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
                    sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    character_id UUID REFERENCES characters(id) ON DELETE SET NULL,
                    content TEXT NOT NULL,
                    message_type VARCHAR(20) DEFAULT 'chat' CHECK (message_type IN ('chat', 'dm_note', 'ooc', 'system', 'dice_roll')),
                    is_public BOOLEAN DEFAULT TRUE,
                    metadata JSONB DEFAULT '{}',
                    reply_to_id UUID REFERENCES messages(id) ON DELETE SET NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)

            # Dice rolls table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dice_rolls (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    game_session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    character_id UUID REFERENCES characters(id) ON DELETE SET NULL,
                    roll_type VARCHAR(50) NOT NULL,
                    dice_expression VARCHAR(100) NOT NULL,
                    result INTEGER NOT NULL,
                    individual_rolls INTEGER[],
                    modifier INTEGER DEFAULT 0,
                    critical_hit BOOLEAN DEFAULT FALSE,
                    critical_fumble BOOLEAN DEFAULT FALSE,
                    context TEXT,
                    is_private BOOLEAN DEFAULT FALSE,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)

            # Attachments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attachments (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    game_session_id UUID REFERENCES game_sessions(id) ON DELETE CASCADE,
                    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    filename VARCHAR(255) NOT NULL,
                    original_filename VARCHAR(255) NOT NULL,
                    file_type VARCHAR(50) NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    mime_type VARCHAR(100),
                    description TEXT,
                    is_public BOOLEAN DEFAULT FALSE,
                    download_count INTEGER DEFAULT 0,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)

            # Audit logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    action VARCHAR(100) NOT NULL,
                    resource_type VARCHAR(50) NOT NULL,
                    resource_id UUID,
                    old_values JSONB,
                    new_values JSONB,
                    ip_address INET,
                    user_agent TEXT,
                    session_id VARCHAR(255),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)

            # System settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    key VARCHAR(100) UNIQUE NOT NULL,
                    value JSONB NOT NULL,
                    description TEXT,
                    category VARCHAR(50) DEFAULT 'general',
                    is_public BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)

            logger.info("All tables created successfully")

    async def _create_indexes(self):
        """Create database indexes for performance"""
        logger.info("Creating database indexes...")

        indexes = [
            # Users indexes
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
            "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);",

            # Game sessions indexes
            "CREATE INDEX IF NOT EXISTS idx_game_sessions_user_id ON game_sessions(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_game_sessions_status ON game_sessions(status);",
            "CREATE INDEX IF NOT EXISTS idx_game_sessions_visibility ON game_sessions(visibility);",
            "CREATE INDEX IF NOT EXISTS idx_game_sessions_created_at ON game_sessions(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_game_sessions_tags ON game_sessions USING GIN(tags);",

            # Characters indexes
            "CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_characters_game_session_id ON characters(game_session_id);",
            "CREATE INDEX IF NOT EXISTS idx_characters_name ON characters(name);",
            "CREATE INDEX IF NOT EXISTS idx_characters_is_active ON characters(is_active);",

            # Campaigns indexes
            "CREATE INDEX IF NOT EXISTS idx_campaigns_game_session_id ON campaigns(game_session_id);",
            "CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);",
            "CREATE INDEX IF NOT EXISTS idx_campaigns_story_arc ON campaigns(story_arc);",

            # Session logs indexes
            "CREATE INDEX IF NOT EXISTS idx_session_logs_game_session_id ON session_logs(game_session_id);",
            "CREATE INDEX IF NOT EXISTS idx_session_logs_user_id ON session_logs(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_session_logs_date_played ON session_logs(date_played);",
            "CREATE INDEX IF NOT EXISTS idx_session_logs_session_number ON session_logs(session_number);",

            # Messages indexes
            "CREATE INDEX IF NOT EXISTS idx_messages_game_session_id ON messages(game_session_id);",
            "CREATE INDEX IF NOT EXISTS idx_messages_campaign_id ON messages(campaign_id);",
            "CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);",
            "CREATE INDEX IF NOT EXISTS idx_messages_character_id ON messages(character_id);",
            "CREATE INDEX IF NOT EXISTS idx_messages_message_type ON messages(message_type);",
            "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_messages_reply_to_id ON messages(reply_to_id);",

            # Dice rolls indexes
            "CREATE INDEX IF NOT EXISTS idx_dice_rolls_game_session_id ON dice_rolls(game_session_id);",
            "CREATE INDEX IF NOT EXISTS idx_dice_rolls_user_id ON dice_rolls(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_dice_rolls_roll_type ON dice_rolls(roll_type);",
            "CREATE INDEX IF NOT EXISTS idx_dice_rolls_created_at ON dice_rolls(created_at);",

            # Attachments indexes
            "CREATE INDEX IF NOT EXISTS idx_attachments_game_session_id ON attachments(game_session_id);",
            "CREATE INDEX IF NOT EXISTS idx_attachments_campaign_id ON attachments(campaign_id);",
            "CREATE INDEX IF NOT EXISTS idx_attachments_user_id ON attachments(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_attachments_file_type ON attachments(file_type);",
            "CREATE INDEX IF NOT EXISTS idx_attachments_is_public ON attachments(is_public);",

            # Audit logs indexes
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_type ON audit_logs(resource_type);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource_id ON audit_logs(resource_id);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);",

            # System settings indexes
            "CREATE INDEX IF NOT EXISTS idx_system_settings_key ON system_settings(key);",
            "CREATE INDEX IF NOT EXISTS idx_system_settings_category ON system_settings(category);",
            "CREATE INDEX IF NOT EXISTS idx_system_settings_is_public ON system_settings(is_public);",

            # Full-text search indexes
            "CREATE INDEX IF NOT EXISTS idx_users_search ON users USING GIN(to_tsvector('english', username || ' ' || COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')));",
            "CREATE INDEX IF NOT EXISTS idx_game_sessions_search ON game_sessions USING GIN(to_tsvector('english', title || ' ' || COALESCE(description, '')));",
            "CREATE INDEX IF NOT EXISTS idx_characters_search ON characters USING GIN(to_tsvector('english', name || ' ' || COALESCE(background, '')));",
        ]

        with self._get_connection() as (conn, cursor):
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")

        logger.info("Database indexes created successfully")

    async def _create_constraints(self):
        """Create database constraints"""
        logger.info("Creating database constraints...")

        constraints = [
            # Check constraints
            "ALTER TABLE game_sessions ADD CONSTRAINT chk_game_sessions_players CHECK (current_players <= max_players);",
            "ALTER TABLE game_sessions ADD CONSTRAINT chk_game_sessions_level CHECK (level >= 1);",
            "ALTER TABLE characters ADD CONSTRAINT chk_characters_level CHECK (level >= 1 AND level <= 20);",
            "ALTER TABLE characters ADD CONSTRAINT chk_characters_experience CHECK (experience >= 0);",
            "ALTER TABLE session_logs ADD CONSTRAINT chk_session_logs_duration CHECK (duration_minutes >= 0);",
            "ALTER TABLE attachments ADD CONSTRAINT chk_attachments_file_size CHECK (file_size >= 0);",
            "ALTER TABLE attachments ADD CONSTRAINT chk_attachments_download_count CHECK (download_count >= 0);",

            # Unique constraints
            "ALTER TABLE session_logs ADD CONSTRAINT uniq_session_logs_session_number UNIQUE(game_session_id, session_number);",
            "ALTER TABLE dice_rolls ADD CONSTRAINT uniq_dice_rolls_no_duplicates UNIQUE(game_session_id, user_id, created_at, roll_type);",
        ]

        with self._get_connection() as (conn, cursor):
            for constraint_sql in constraints:
                try:
                    cursor.execute(f"ALTER TABLE DROP CONSTRAINT IF EXISTS {constraint_sql.split()[5]};")
                    cursor.execute(constraint_sql)
                except Exception as e:
                    logger.warning(f"Failed to create constraint: {e}")

        logger.info("Database constraints created successfully")

    async def _create_triggers(self):
        """Create database triggers"""
        logger.info("Creating database triggers...")

        # Function to update updated_at timestamp
        trigger_function = """
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """

        # Triggers for updated_at columns
        triggers = [
            ("users", update_updated_at_column, "BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();"),
            ("game_sessions", update_updated_at_column, "BEFORE UPDATE ON game_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();"),
            ("characters", update_updated_at_column, "BEFORE UPDATE ON characters FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();"),
            ("campaigns", update_updated_at_column, "BEFORE UPDATE ON campaigns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();"),
            ("session_logs", update_updated_at_column, "BEFORE UPDATE ON session_logs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();"),
            ("messages", update_updated_at_column, "BEFORE UPDATE ON messages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();"),
            ("system_settings", update_updated_at_column, "BEFORE UPDATE ON system_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();"),
        ]

        with self._get_connection() as (conn, cursor):
            # Create the trigger function
            cursor.execute(trigger_function)

            # Create triggers
            for table_name, _, trigger_sql in triggers:
                try:
                    cursor.execute(f"DROP TRIGGER IF EXISTS trigger_update_{table_name}_updated_at ON {table_name};")
                    cursor.execute(f"CREATE TRIGGER trigger_update_{table_name}_updated_at {trigger_sql}")
                except Exception as e:
                    logger.warning(f"Failed to create trigger for {table_name}: {e}")

        logger.info("Database triggers created successfully")

    async def _seed_initial_data(self):
        """Seed initial data for the application"""
        logger.info("Seeding initial data...")

        # Game systems
        game_systems = [
            ("D&D 5e", "Dungeons & Dragons 5th Edition"),
            ("Pathfinder 2e", "Pathfinder Second Edition"),
            ("Call of Cthulhu", "Call of Cthulhu 7th Edition"),
            ("World of Darkness", "Vampire: The Masquerade 5th Edition"),
            ("Shadowrun", "Shadowrun 6th Edition"),
            ("GURPS", "Generic Universal RolePlaying System"),
            ("FATE", "FATE Core/Accelerated"),
            ("Custom", "Custom RPG System")
        ]

        # Default system settings
        settings_data = [
            ("app_name", "DMLog", "Application name", "general", True),
            ("app_version", "1.0.0", "Application version", "general", True),
            ("max_file_size", 10485760, "Maximum file upload size in bytes", "uploads", False),
            ("allowed_file_types", '["jpg", "jpeg", "png", "gif", "pdf", "txt", "md"]', "Allowed file types for uploads", "uploads", False),
            ("max_game_sessions", 100, "Maximum number of game sessions per user", "limits", False),
            ("max_characters_per_session", 20, "Maximum characters per game session", "limits", False),
            ("session_retention_days", 365, "Number of days to retain session logs", "maintenance", False),
            ("enable_public_sessions", True, "Allow public game sessions", "features", False),
            ("enable_anonymous_access", False, "Allow anonymous access to public sessions", "features", False),
            ("default_timezone", "UTC", "Default timezone for the application", "general", False),
        ]

        with self._get_connection() as (conn, cursor):
            # Insert game systems (these could be in a separate table if needed)
            # For now, they're referenced as strings in the game_sessions table

            # Insert system settings
            for key, value, description, category, is_public in settings_data:
                cursor.execute("""
                    INSERT INTO system_settings (key, value, description, category, is_public)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (key) DO NOTHING;
                """, (key, json.dumps(value), description, category, is_public))

        logger.info("Initial data seeded successfully")

    async def _create_admin_user(self):
        """Create default admin user"""
        logger.info("Creating admin user...")

        with self._get_connection() as (conn, cursor):
            # Hash the admin password
            password_hash = pwd_context.hash(ADMIN_CONFIG['password'])

            # Insert admin user
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, is_admin, is_verified, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (username) DO NOTHING;
            """, (
                ADMIN_CONFIG['username'],
                ADMIN_CONFIG['email'],
                password_hash,
                ADMIN_CONFIG['is_admin'],
                True  # Mark as verified
            ))

            # Log the creation
            cursor.execute("""
                INSERT INTO audit_logs (action, resource_type, resource_id, ip_address, user_agent, created_at)
                VALUES ('ADMIN_USER_CREATED', 'users', (SELECT id FROM users WHERE username = %s), '127.0.0.1', 'Database Init Script', NOW());
            """, (ADMIN_CONFIG['username'],))

        logger.info(f"Admin user '{ADMIN_CONFIG['username']}' created successfully")

    async def _seed_validation_data(self):
        """Seed data for validation and testing"""
        logger.info("Seeding validation data...")

        # Create sample users for testing
        sample_users = [
            ("game_master", "gm@dmlog.local", "gm123", "Game", "Master"),
            ("player1", "player1@dmlog.local", "player123", "Player", "One"),
            ("spectator", "spectator@dmlog.local", "spec123", "Spectator", "User"),
        ]

        # Create sample game sessions
        sample_sessions = [
            ("The Dragon's Lair", "A thrilling adventure through dangerous caves filled with treasure and monsters.", "D&D 5e", "active"),
            ("Mystery of the Ancient Temple", "Explore forgotten ruins and uncover ancient secrets hidden for millennia.", "Pathfinder 2e", "planning"),
            ("City Intrigue", "Political maneuvering and espionage in the capital city's shadowy underworld.", "D&D 5e", "completed"),
            ("Space Odyssey", "A sci-fi adventure across the galaxy in search of lost technology.", "Custom", "planning"),
        ]

        with self._get_connection() as (conn, cursor):
            # Create sample users
            for username, email, password, first_name, last_name in sample_users:
                password_hash = pwd_context.hash(password)
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, first_name, last_name, is_verified, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (username) DO NOTHING;
                """, (username, email, password_hash, first_name, last_name, True))

            # Create sample game sessions
            game_master_id = None
            cursor.execute("SELECT id FROM users WHERE username = 'game_master';")
            result = cursor.fetchone()
            if result:
                game_master_id = result['id']

            if game_master_id:
                for title, description, system, status in sample_sessions:
                    cursor.execute("""
                        INSERT INTO game_sessions (user_id, title, description, system, status, visibility, max_players, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        ON CONFLICT DO NOTHING;
                    """, (game_master_id, title, description, system, status, 'private', 6))

        logger.info("Validation data seeded successfully")

    def validate_initialization(self) -> bool:
        """Validate that the database was initialized correctly"""
        logger.info("Validating database initialization...")

        try:
            with self._get_connection() as (conn, cursor):
                # Check that all tables exist
                expected_tables = [
                    'users', 'game_sessions', 'characters', 'campaigns',
                    'session_logs', 'messages', 'dice_rolls', 'attachments',
                    'audit_logs', 'system_settings'
                ]

                for table in expected_tables:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = %s
                        );
                    """, (table,))
                    exists = cursor.fetchone()['exists']
                    if not exists:
                        logger.error(f"Table '{table}' does not exist")
                        return False

                # Check that admin user exists
                cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_admin = TRUE;")
                admin_count = cursor.fetchone()['count']
                if admin_count == 0:
                    logger.error("Admin user not found")
                    return False

                # Check system settings
                cursor.execute("SELECT COUNT(*) as count FROM system_settings;")
                settings_count = cursor.fetchone()['count']
                if settings_count == 0:
                    logger.error("System settings not found")
                    return False

            logger.info("Database initialization validation passed")
            return True

        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            return False


async def main():
    """Main initialization function"""
    logger.info("=" * 60)
    logger.info("DMLog Database Initialization Script")
    logger.info("=" * 60)

    try:
        # Create database initializer
        initializer = DatabaseInitializer(DB_CONFIG)

        # Initialize database
        success = await initializer.initialize()

        if success:
            # Validate initialization
            if initializer.validate_initialization():
                logger.info("✅ Database initialization completed successfully!")
                logger.info("🎮 DMLog is ready to use!")
                logger.info("")
                logger.info("Default admin credentials:")
                logger.info(f"  Username: {ADMIN_CONFIG['username']}")
                logger.info(f"  Email: {ADMIN_CONFIG['email']}")
                logger.info(f"  Password: {ADMIN_CONFIG['password']}")
                logger.info("")
                logger.info("⚠️  Please change the default admin password after first login!")
            else:
                logger.error("❌ Database initialization validation failed!")
                sys.exit(1)
        else:
            logger.error("❌ Database initialization failed!")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Fatal error during database initialization: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Run initialization
    asyncio.run(main())