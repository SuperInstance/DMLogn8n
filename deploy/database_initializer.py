#!/usr/bin/env python3
"""
Database Initializer for DMLogn8n
Sets up and initializes all databases with schemas and sample data
"""

import os
import sys
import json
import time
import logging
import subprocess
import pymysql
import redis
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import hashlib


class DatabaseType(Enum):
    MYSQL = "mysql"
    REDIS = "redis"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"


@dataclass
class DatabaseConfig:
    name: str
    type: DatabaseType
    host: str
    port: int
    username: str
    password: str
    database: str
    charset: str = "utf8mb4"


@dataclass
class SchemaConfig:
    database: str
    schema_file: str
    dependencies: List[str]


class DatabaseInitializer:
    """Database setup and initialization manager"""

    def __init__(self, environment: str):
        self.environment = environment
        self.logger = logging.getLogger(__name__)

        # Paths
        self.schemas_dir = Path(__file__).parent / "schemas"
        self.seeds_dir = Path(__file__).parent / "seeds"
        self.migrations_dir = Path(__file__).parent / "migrations"

        # Database configurations
        self.databases = self.get_database_configurations()

        # Schema configurations
        self.schemas = self.get_schema_configurations()

    def get_database_configurations(self) -> Dict[str, DatabaseConfig]:
        """Get database configurations based on environment"""
        base_config = {
            "development": {
                "mysql_host": "localhost",
                "redis_host": "localhost",
                "mysql_password": "dev_password",
                "redis_password": None,
            },
            "staging": {
                "mysql_host": "staging-db.dmlogn8n.com",
                "redis_host": "staging-redis.dmlogn8n.com",
                "mysql_password": "staging_password",
                "redis_password": "staging_redis_password",
            },
            "production": {
                "mysql_host": "prod-db.dmlogn8n.com",
                "redis_host": "prod-redis.dmlogn8n.com",
                "mysql_password": os.getenv("MYSQL_PASSWORD", "secure_prod_password"),
                "redis_password": os.getenv("REDIS_PASSWORD", "secure_redis_password"),
            }
        }

        env_config = base_config[self.environment]

        return {
            "dmlogn8n": DatabaseConfig(
                name="dmlogn8n",
                type=DatabaseType.MYSQL,
                host=env_config["mysql_host"],
                port=3306,
                username="dmlogn8n_user",
                password=env_config["mysql_password"],
                database="dmlogn8n"
            ),
            "n8n": DatabaseConfig(
                name="n8n",
                type=DatabaseType.MYSQL,
                host=env_config["mysql_host"],
                port=3306,
                username="n8n_user",
                password=env_config["mysql_password"],
                database="n8n"
            ),
            "cache": DatabaseConfig(
                name="cache",
                type=DatabaseType.REDIS,
                host=env_config["redis_host"],
                port=6379,
                username="",
                password=env_config["redis_password"],
                database=""
            )
        }

    def get_schema_configurations(self) -> List[SchemaConfig]:
        """Get schema configuration files"""
        return [
            SchemaConfig(
                database="dmlogn8n",
                schema_file="dmlogn8n_schema.sql",
                dependencies=[]
            ),
            SchemaConfig(
                database="dmlogn8n",
                schema_file="dmlogn8n_indexes.sql",
                dependencies=["dmlogn8n_schema.sql"]
            ),
            SchemaConfig(
                database="n8n",
                schema_file="n8n_schema.sql",
                dependencies=[]
            )
        ]

    def test_mysql_connection(self, config: DatabaseConfig) -> bool:
        """Test MySQL database connection"""
        try:
            connection = pymysql.connect(
                host=config.host,
                port=config.port,
                user=config.username,
                password=config.password,
                database=config.database,
                charset=config.charset
            )
            connection.close()
            self.logger.info(f"MySQL connection to {config.database} successful")
            return True
        except Exception as e:
            self.logger.error(f"MySQL connection failed: {e}")
            return False

    def test_redis_connection(self, config: DatabaseConfig) -> bool:
        """Test Redis connection"""
        try:
            r = redis.Redis(
                host=config.host,
                port=config.port,
                password=config.password if config.password else None,
                decode_responses=True
            )
            r.ping()
            self.logger.info(f"Redis connection to {config.host}:{config.port} successful")
            return True
        except Exception as e:
            self.logger.error(f"Redis connection failed: {e}")
            return False

    def create_mysql_database(self, config: DatabaseConfig) -> bool:
        """Create MySQL database if it doesn't exist"""
        try:
            # Connect without specifying database
            connection = pymysql.connect(
                host=config.host,
                port=config.port,
                user="root",
                password=self.databases["dmlogn8n"].password,  # Use root password from config
                charset=config.charset
            )

            cursor = connection.cursor()

            # Create database if not exists
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{config.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")

            # Create user if not exists and grant privileges
            cursor.execute(f"CREATE USER IF NOT EXISTS '{config.username}'@'%' IDENTIFIED BY '{config.password}'")
            cursor.execute(f"GRANT ALL PRIVILEGES ON `{config.database}`.* TO '{config.username}'@'%'")
            cursor.execute("FLUSH PRIVILEGES")

            connection.commit()
            connection.close()

            self.logger.info(f"MySQL database {config.database} created successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create MySQL database {config.database}: {e}")
            return False

    def execute_mysql_script(self, config: DatabaseConfig, script_file: str) -> bool:
        """Execute MySQL script file"""
        try:
            script_path = self.schemas_dir / script_file

            if not script_path.exists():
                self.logger.error(f"Script file not found: {script_path}")
                return False

            # Read script file
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()

            # Connect to database
            connection = pymysql.connect(
                host=config.host,
                port=config.port,
                user=config.username,
                password=config.password,
                database=config.database,
                charset=config.charset
            )

            cursor = connection.cursor()

            # Split script into individual statements
            statements = [stmt.strip() for stmt in script_content.split(';') if stmt.strip()]

            for statement in statements:
                if statement:
                    cursor.execute(statement)

            connection.commit()
            connection.close()

            self.logger.info(f"Executed script {script_file} successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to execute script {script_file}: {e}")
            return False

    def create_dmlogn8n_schema(self) -> str:
        """Generate DMLogn8n database schema"""
        schema = """
-- DMLogn8n Database Schema

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'dm', 'player') DEFAULT 'player',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP NULL,
    preferences JSON
);

-- Characters table
CREATE TABLE IF NOT EXISTS characters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    class VARCHAR(50) NOT NULL,
    level INT DEFAULT 1,
    experience INT DEFAULT 0,
    attributes JSON,
    inventory JSON,
    background TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dm_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    setting VARCHAR(100),
    status ENUM('planning', 'active', 'paused', 'completed') DEFAULT 'planning',
    max_players INT DEFAULT 4,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (dm_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Campaign_players table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS campaign_players (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campaign_id INT NOT NULL,
    player_id INT NOT NULL,
    character_id INT,
    status ENUM('invited', 'joined', 'declined', 'removed') DEFAULT 'invited',
    joined_at TIMESTAMP NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
    FOREIGN KEY (player_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE SET NULL,
    UNIQUE KEY unique_campaign_player (campaign_id, player_id)
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campaign_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    session_number INT NOT NULL,
    status ENUM('planned', 'in_progress', 'completed', 'cancelled') DEFAULT 'planned',
    scheduled_at TIMESTAMP NULL,
    started_at TIMESTAMP NULL,
    ended_at TIMESTAMP NULL,
    transcript TEXT,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
);

-- Characters_in_sessions table
CREATE TABLE IF NOT EXISTS characters_in_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    character_id INT NOT NULL,
    player_notes TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
    UNIQUE KEY unique_session_character (session_id, character_id)
);

-- NPC table
CREATE TABLE IF NOT EXISTS npcs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campaign_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    attributes JSON,
    personality JSON,
    background TEXT,
    location VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
);

-- Story_elements table
CREATE TABLE IF NOT EXISTS story_elements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campaign_id INT NOT NULL,
    element_type ENUM('plot_hook', 'location', 'item', 'event', 'secret') NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    details JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
);

-- N8n_workflows table
CREATE TABLE IF NOT EXISTS n8n_workflows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    campaign_id INT NULL,
    workflow_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    workflow_data JSON,
    triggers JSON,
    status ENUM('active', 'inactive', 'error') DEFAULT 'inactive',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL
);

-- Workflow_executions table
CREATE TABLE IF NOT EXISTS workflow_executions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    workflow_id INT NOT NULL,
    execution_id VARCHAR(100) NOT NULL,
    status ENUM('running', 'success', 'error', 'cancelled') NOT NULL,
    input_data JSON,
    output_data JSON,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (workflow_id) REFERENCES n8n_workflows(id) ON DELETE CASCADE
);

-- Activity_log table
CREATE TABLE IF NOT EXISTS activity_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    campaign_id INT NULL,
    session_id INT NULL,
    action VARCHAR(100) NOT NULL,
    details JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_campaign_id (campaign_id),
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
);
"""
        return schema

    def create_dmlogn8n_indexes(self) -> str:
        """Generate DMLogn8n database indexes"""
        indexes = """
-- DMLogn8n Database Indexes

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Characters table indexes
CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id);
CREATE INDEX IF NOT EXISTS idx_characters_name ON characters(name);
CREATE INDEX IF NOT EXISTS idx_characters_class ON characters(class);
CREATE INDEX IF NOT EXISTS idx_characters_level ON characters(level);
CREATE INDEX IF NOT EXISTS idx_characters_created_at ON characters(created_at);

-- Campaigns table indexes
CREATE INDEX IF NOT EXISTS idx_campaigns_dm_id ON campaigns(dm_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_setting ON campaigns(setting);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON campaigns(created_at);
CREATE INDEX IF NOT EXISTS idx_campaigns_is_public ON campaigns(is_public);

-- Sessions table indexes
CREATE INDEX IF NOT EXISTS idx_sessions_campaign_id ON sessions(campaign_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_scheduled_at ON sessions(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at);

-- NPC table indexes
CREATE INDEX IF NOT EXISTS idx_npcs_campaign_id ON npcs(campaign_id);
CREATE INDEX IF NOT EXISTS idx_npcs_name ON npcs(name);
CREATE INDEX IF NOT EXISTS idx_npcs_location ON npcs(location);
CREATE INDEX IF NOT EXISTS idx_npcs_is_active ON npcs(is_active);

-- Story_elements table indexes
CREATE INDEX IF NOT EXISTS idx_story_elements_campaign_id ON story_elements(campaign_id);
CREATE INDEX IF NOT EXISTS idx_story_elements_element_type ON story_elements(element_type);
CREATE INDEX IF NOT EXISTS idx_story_elements_is_active ON story_elements(is_active);

-- N8n_workflows table indexes
CREATE INDEX IF NOT EXISTS idx_n8n_workflows_campaign_id ON n8n_workflows(campaign_id);
CREATE INDEX IF NOT EXISTS idx_n8n_workflows_workflow_id ON n8n_workflows(workflow_id);
CREATE INDEX IF NOT EXISTS idx_n8n_workflows_status ON n8n_workflows(status);

-- Workflow_executions table indexes
CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_execution_id ON workflow_executions(execution_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_started_at ON workflow_executions(started_at);
"""
        return indexes

    def create_n8n_schema(self) -> str:
        """Generate N8N database schema"""
        schema = """
-- N8N Database Schema

-- N8N will create its own tables, but we can create additional ones for our integration

CREATE TABLE IF NOT EXISTS n8n_custom_workflows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    workflow_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    campaign_id INT NULL,
    workflow_type ENUM('character_generation', 'scene_creation', 'dialogue_generation', 'story_progression') NOT NULL,
    template_data JSON,
    is_template BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_campaign_id (campaign_id),
    INDEX idx_workflow_type (workflow_type),
    INDEX idx_is_template (is_template)
);

CREATE TABLE IF NOT EXISTS n8n_workflow_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    workflow_data JSON NOT NULL,
    parameters_schema JSON,
    is_public BOOLEAN DEFAULT TRUE,
    usage_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_is_public (is_public),
    INDEX idx_usage_count (usage_count)
);
"""
        return schema

    def insert_sample_data(self) -> bool:
        """Insert sample data for development and testing"""
        if self.environment == "production":
            self.logger.info("Skipping sample data insertion in production")
            return True

        try:
            self.logger.info("Inserting sample data...")

            # Connect to DMLogn8n database
            config = self.databases["dmlogn8n"]
            connection = pymysql.connect(
                host=config.host,
                port=config.port,
                user=config.username,
                password=config.password,
                database=config.database,
                charset=config.charset
            )

            cursor = connection.cursor()

            # Insert sample users
            sample_users = [
                ('admin', 'admin@dmlogn8n.com', 'hashed_password_admin', 'admin'),
                ('dungeon_master', 'dm@dmlogn8n.com', 'hashed_password_dm', 'dm'),
                ('player1', 'player1@dmlogn8n.com', 'hashed_password_player1', 'player'),
                ('player2', 'player2@dmlogn8n.com', 'hashed_password_player2', 'player'),
            ]

            insert_user_query = """
            INSERT IGNORE INTO users (username, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
            """

            cursor.executemany(insert_user_query, sample_users)

            # Insert sample campaign
            insert_campaign_query = """
            INSERT IGNORE INTO campaigns (dm_id, title, description, setting, status, max_players, is_public)
            VALUES (2, 'The Dancing Dog Mystery', 'A mysterious tale of a dog that dances to the mathematics of music', 'Coastal Town', 'active', 4, TRUE)
            """
            cursor.execute(insert_campaign_query)

            # Get campaign ID
            cursor.execute("SELECT id FROM campaigns WHERE title = 'The Dancing Dog Mystery'")
            campaign_result = cursor.fetchone()
            if campaign_result:
                campaign_id = campaign_result[0]

                # Insert sample characters
                sample_characters = [
                    (3, 'Anna', 'Mathematician', 5, '{"intelligence": 18, "wisdom": 14, "charisma": 16}', 'A brilliant mathematician who sees patterns in music'),
                    (4, 'Finn', 'Musician', 4, '{"intelligence": 12, "wisdom": 16, "dexterity": 17}', 'A talented musician who can play any instrument'),
                ]

                insert_character_query = """
                INSERT IGNORE INTO characters (user_id, name, class, level, attributes, background)
                VALUES (%s, %s, %s, %s, %s, %s)
                """

                cursor.executemany(insert_character_query, sample_characters)

                # Add players to campaign
                cursor.execute("SELECT id FROM characters WHERE name IN ('Anna', 'Finn')")
                character_ids = [row[0] for row in cursor.fetchall()]

                player_inserts = [(campaign_id, 3, character_ids[0]), (campaign_id, 4, character_ids[1])]

                insert_player_query = """
                INSERT IGNORE INTO campaign_players (campaign_id, player_id, character_id, status, joined_at)
                VALUES (%s, %s, %s, 'joined', NOW())
                """

                cursor.executemany(insert_player_query, player_inserts)

            connection.commit()
            connection.close()

            self.logger.info("Sample data inserted successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to insert sample data: {e}")
            return False

    def initialize_databases(self) -> bool:
        """Initialize all databases"""
        self.logger.info(f"Initializing databases for {self.environment} environment...")

        # Create schemas directory
        self.schemas_dir.mkdir(parents=True, exist_ok=True)

        # Generate schema files
        dmlogn8n_schema = self.create_dmlogn8n_schema()
        dmlogn8n_indexes = self.create_dmlogn8n_indexes()
        n8n_schema = self.create_n8n_schema()

        with open(self.schemas_dir / "dmlogn8n_schema.sql", "w") as f:
            f.write(dmlogn8n_schema)

        with open(self.schemas_dir / "dmlogn8n_indexes.sql", "w") as f:
            f.write(dmlogn8n_indexes)

        with open(self.schemas_dir / "n8n_schema.sql", "w") as f:
            f.write(n8n_schema)

        # Initialize MySQL databases
        mysql_databases = [db for db in self.databases.values() if db.type == DatabaseType.MYSQL]

        for db_config in mysql_databases:
            # Create database
            if not self.create_mysql_database(db_config):
                return False

            # Test connection
            if not self.test_mysql_connection(db_config):
                return False

        # Initialize Redis
        redis_databases = [db for db in self.databases.values() if db.type == DatabaseType.REDIS]

        for db_config in redis_databases:
            if not self.test_redis_connection(db_config):
                return False

        # Execute schemas in dependency order
        for schema_config in self.schemas:
            db_config = self.databases[schema_config.database]

            self.logger.info(f"Executing schema {schema_config.schema_file} for {schema_config.database}")

            if not self.execute_mysql_script(db_config, schema_config.schema_file):
                return False

        # Insert sample data for non-production environments
        if self.environment != "production":
            if not self.insert_sample_data():
                return False

        self.logger.info("Database initialization completed successfully")
        return True


def main():
    """Main entry point for database initialization"""
    import argparse

    parser = argparse.ArgumentParser(description="DMLogn8n Database Initializer")
    parser.add_argument("environment", choices=["development", "staging", "production"],
                       help="Target environment")
    parser.add_argument("--test-only", action="store_true",
                       help="Only test database connections")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize database initializer
    initializer = DatabaseInitializer(args.environment)

    if args.test_only:
        # Test connections only
        success = True
        for db_config in initializer.databases.values():
            if db_config.type == DatabaseType.MYSQL:
                if not initializer.test_mysql_connection(db_config):
                    success = False
            elif db_config.type == DatabaseType.REDIS:
                if not initializer.test_redis_connection(db_config):
                    success = False
    else:
        # Full initialization
        success = initializer.initialize_databases()

    if success:
        print("✅ Database operation completed successfully!")
        sys.exit(0)
    else:
        print("❌ Database operation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()