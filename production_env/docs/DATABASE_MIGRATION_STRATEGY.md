# Database Migration Strategy: SQLite to PostgreSQL

## Overview

This document outlines the comprehensive strategy for migrating DMLog from SQLite to PostgreSQL to support production workloads, concurrent access, and scaling requirements.

## Migration Phases

### Phase 1: Assessment and Preparation (Week 1)

#### 1.1 Current SQLite Schema Analysis
```sql
-- Analyze existing SQLite tables
.tables
.schema characters
.schema sessions
.schema decisions
.schema training_data

-- Check data volumes
SELECT COUNT(*) FROM characters;
SELECT COUNT(*) FROM sessions;
SELECT COUNT(*) FROM decisions;
SELECT COUNT(*) FROM training_data;

-- Identify indexes
PRAGMA index_list('characters');
PRAGMA index_list('sessions');
PRAGMA index_list('decisions');
PRAGMA index_list('training_data');
```

#### 1.2 PostgreSQL Schema Design
```sql
-- Enhanced PostgreSQL schema with proper types, indexes, and constraints

-- Characters table with enhanced fields
CREATE TABLE characters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    class VARCHAR(100) NOT NULL,
    level INTEGER DEFAULT 1,
    experience_points INTEGER DEFAULT 0,
    player_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',

    CONSTRAINT characters_level_check CHECK (level >= 1 AND level <= 20),
    CONSTRAINT characters_xp_check CHECK (experience_points >= 0)
);

-- Sessions table with relationships
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    campaign_id UUID,
    session_number INTEGER NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'paused', 'cancelled')),
    dm_notes TEXT,
    summary TEXT,
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Decisions table with enhanced tracking
CREATE TABLE decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    decision_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    decision_type VARCHAR(100) NOT NULL,
    decision_data JSONB NOT NULL,
    context JSONB DEFAULT '{}',
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    processing_time_ms INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Training data table with versioning
CREATE TABLE training_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id) ON DELETE SET NULL,
    data_type VARCHAR(50) NOT NULL,
    input_sequence TEXT NOT NULL,
    target_output TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',

    -- Data validation
    is_validated BOOLEAN DEFAULT false,
    validation_score DECIMAL(3,2),
    validator_id UUID,

    -- Model training metadata
    model_version VARCHAR(50),
    training_status VARCHAR(50) DEFAULT 'pending',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Model versions table
CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    model_path VARCHAR(500) NOT NULL,

    -- Training metrics
    training_loss DECIMAL(10,6),
    validation_loss DECIMAL(10,6),
    accuracy DECIMAL(5,4),

    -- Training metadata
    training_data_count INTEGER,
    hyperparameters JSONB DEFAULT '{}',
    training_duration_seconds INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT false
);

-- Create indexes for performance
CREATE INDEX idx_characters_player_id ON characters(player_id);
CREATE INDEX idx_characters_class ON characters(class);
CREATE INDEX idx_sessions_character_id ON sessions(character_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_start_time ON sessions(start_time);
CREATE INDEX idx_decisions_session_id ON decisions(session_id);
CREATE INDEX idx_decisions_character_id ON decisions(character_id);
CREATE INDEX idx_decisions_timestamp ON decisions(decision_timestamp);
CREATE INDEX idx_decisions_type ON decisions(decision_type);
CREATE INDEX idx_training_data_character_id ON training_data(character_id);
CREATE INDEX idx_training_data_session_id ON training_data(session_id);
CREATE INDEX idx_training_data_type ON training_data(data_type);
CREATE INDEX idx_training_data_status ON training_data(training_status);
CREATE INDEX idx_model_versions_character_id ON model_versions(character_id);
CREATE INDEX idx_model_versions_active ON model_versions(is_active) WHERE is_active = true;

-- Create triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_characters_updated_at BEFORE UPDATE ON characters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_training_data_updated_at BEFORE UPDATE ON training_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Phase 2: Migration Tools Development (Week 2)

#### 2.1 Migration Script
```python
#!/usr/bin/env python3
"""
SQLite to PostgreSQL migration script for DMLog
"""

import sqlite3
import psycopg2
from psycopg2 import sql, extras
import json
import uuid
from datetime import datetime
import logging
from typing import Dict, List, Any
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, sqlite_path: str, postgres_config: Dict[str, str]):
        self.sqlite_conn = sqlite3.connect(sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row

        self.postgres_conn = psycopg2.connect(**postgres_config)
        self.postgres_conn.autocommit = False

    def migrate_all(self):
        """Execute full migration"""
        try:
            # Start transaction
            with self.postgres_conn.cursor() as cur:
                logger.info("Starting migration transaction")

                # Migrate in dependency order
                self.migrate_characters(cur)
                self.migrate_sessions(cur)
                self.migrate_decisions(cur)
                self.migrate_training_data(cur)

                # Commit transaction
                self.postgres_conn.commit()
                logger.info("Migration completed successfully")

        except Exception as e:
            self.postgres_conn.rollback()
            logger.error(f"Migration failed: {str(e)}")
            raise

    def migrate_characters(self, cur):
        """Migrate characters table"""
        logger.info("Migrating characters...")

        sqlite_cursor = self.sqlite_conn.execute("SELECT * FROM characters")
        characters = sqlite_cursor.fetchall()

        if not characters:
            logger.warning("No characters found in SQLite database")
            return

        # Prepare batch insert
        insert_query = sql.SQL("""
            INSERT INTO characters (
                id, name, class, level, experience_points, player_id,
                created_at, updated_at, is_active, metadata
            ) VALUES %s
            ON CONFLICT (id) DO NOTHING
        """)

        batch_data = []
        for char in characters:
            batch_data.append((
                str(uuid.uuid4()),  # Generate new UUID
                char['name'],
                char.get('class', 'Unknown'),
                char.get('level', 1),
                char.get('experience_points', 0),
                char.get('player_id'),
                self.parse_timestamp(char.get('created_at')),
                self.parse_timestamp(char.get('updated_at')),
                char.get('is_active', True),
                self.parse_json(char.get('metadata', '{}'))
            ))

        # Execute batch insert
        extras.execute_values(cur, insert_query, batch_data)
        logger.info(f"Migrated {len(batch_data)} characters")

    def migrate_sessions(self, cur):
        """Migrate sessions table"""
        logger.info("Migrating sessions...")

        # Get character mapping (old_id -> new_uuid)
        char_mapping = self.get_character_mapping(cur)

        sqlite_cursor = self.sqlite_conn.execute("SELECT * FROM sessions")
        sessions = sqlite_cursor.fetchall()

        if not sessions:
            logger.warning("No sessions found in SQLite database")
            return

        insert_query = sql.SQL("""
            INSERT INTO sessions (
                id, character_id, campaign_id, session_number,
                start_time, end_time, status, dm_notes, summary,
                metadata, created_at, updated_at
            ) VALUES %s
            ON CONFLICT (id) DO NOTHING
        """)

        batch_data = []
        for session in sessions:
            old_char_id = session.get('character_id')
            new_char_id = char_mapping.get(old_char_id)

            if not new_char_id:
                logger.warning(f"No character mapping found for session {session['id']}")
                continue

            batch_data.append((
                str(uuid.uuid4()),
                new_char_id,
                session.get('campaign_id'),
                session.get('session_number', 1),
                self.parse_timestamp(session.get('start_time')),
                self.parse_timestamp(session.get('end_time')),
                session.get('status', 'active'),
                session.get('dm_notes'),
                session.get('summary'),
                self.parse_json(session.get('metadata', '{}')),
                self.parse_timestamp(session.get('created_at')),
                self.parse_timestamp(session.get('updated_at'))
            ))

        extras.execute_values(cur, insert_query, batch_data)
        logger.info(f"Migrated {len(batch_data)} sessions")

    def migrate_decisions(self, cur):
        """Migrate decisions table"""
        logger.info("Migrating decisions...")

        # Get mappings
        char_mapping = self.get_character_mapping(cur)
        session_mapping = self.get_session_mapping(cur)

        sqlite_cursor = self.sqlite_conn.execute("SELECT * FROM decisions")
        decisions = sqlite_cursor.fetchall()

        if not decisions:
            logger.warning("No decisions found in SQLite database")
            return

        insert_query = sql.SQL("""
            INSERT INTO decisions (
                id, session_id, character_id, decision_timestamp,
                decision_type, decision_data, context, confidence_score,
                processing_time_ms, created_at
            ) VALUES %s
            ON CONFLICT (id) DO NOTHING
        """)

        batch_data = []
        for decision in decisions:
            old_char_id = decision.get('character_id')
            old_session_id = decision.get('session_id')

            new_char_id = char_mapping.get(old_char_id)
            new_session_id = session_mapping.get(old_session_id)

            if not new_char_id or not new_session_id:
                logger.warning(f"Missing mapping for decision {decision['id']}")
                continue

            batch_data.append((
                str(uuid.uuid4()),
                new_session_id,
                new_char_id,
                self.parse_timestamp(decision.get('decision_timestamp')),
                decision.get('decision_type'),
                self.parse_json(decision.get('decision_data')),
                self.parse_json(decision.get('context', '{}')),
                decision.get('confidence_score'),
                decision.get('processing_time_ms'),
                self.parse_timestamp(decision.get('created_at'))
            ))

        extras.execute_values(cur, insert_query, batch_data)
        logger.info(f"Migrated {len(batch_data)} decisions")

    def migrate_training_data(self, cur):
        """Migrate training data table"""
        logger.info("Migrating training data...")

        char_mapping = self.get_character_mapping(cur)
        session_mapping = self.get_session_mapping(cur)

        sqlite_cursor = self.sqlite_conn.execute("SELECT * FROM training_data")
        training_data = sqlite_cursor.fetchall()

        if not training_data:
            logger.warning("No training data found in SQLite database")
            return

        insert_query = sql.SQL("""
            INSERT INTO training_data (
                id, character_id, session_id, data_type,
                input_sequence, target_output, metadata,
                is_validated, validation_score, validator_id,
                model_version, training_status, created_at, updated_at
            ) VALUES %s
            ON CONFLICT (id) DO NOTHING
        """)

        batch_data = []
        for data in training_data:
            old_char_id = data.get('character_id')
            old_session_id = data.get('session_id')

            new_char_id = char_mapping.get(old_char_id)
            new_session_id = session_mapping.get(old_session_id) if old_session_id else None

            if not new_char_id:
                logger.warning(f"No character mapping for training data {data['id']}")
                continue

            batch_data.append((
                str(uuid.uuid4()),
                new_char_id,
                new_session_id,
                data.get('data_type'),
                data.get('input_sequence'),
                data.get('target_output'),
                self.parse_json(data.get('metadata', '{}')),
                data.get('is_validated', False),
                data.get('validation_score'),
                data.get('validator_id'),
                data.get('model_version'),
                data.get('training_status', 'pending'),
                self.parse_timestamp(data.get('created_at')),
                self.parse_timestamp(data.get('updated_at'))
            ))

        extras.execute_values(cur, insert_query, batch_data)
        logger.info(f"Migrated {len(batch_data)} training records")

    def get_character_mapping(self, cur) -> Dict[str, str]:
        """Get mapping from SQLite character names to PostgreSQL UUIDs"""
        cur.execute("SELECT id, name FROM characters")
        return {row[1]: str(row[0]) for row in cur.fetchall()}

    def get_session_mapping(self, cur) -> Dict[str, str]:
        """Get mapping from SQLite session IDs to PostgreSQL UUIDs"""
        # This would need to be based on a unique identifier
        # For simplicity, using session_number and character_id
        cur.execute("""
            SELECT s.id, c.name, s.session_number
            FROM sessions s
            JOIN characters c ON s.character_id = c.id
        """)
        return {f"{row[1]}_{row[2]}": str(row[0]) for row in cur.fetchall()}

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> datetime:
        """Parse timestamp from SQLite format"""
        if not timestamp_str:
            return datetime.now()
        try:
            return datetime.fromisoformat(timestamp_str)
        except:
            return datetime.now()

    @staticmethod
    def parse_json(json_str: str) -> Dict[str, Any]:
        """Parse JSON string safely"""
        if not json_str:
            return {}
        try:
            return json.loads(json_str)
        except:
            return {}

    def close(self):
        """Close database connections"""
        self.sqlite_conn.close()
        self.postgres_conn.close()

def main():
    if len(sys.argv) != 3:
        print("Usage: python migrate.py <sqlite_path> <postgres_config_json>")
        sys.exit(1)

    sqlite_path = sys.argv[1]
    postgres_config = json.loads(sys.argv[2])

    migrator = DatabaseMigrator(sqlite_path, postgres_config)

    try:
        migrator.migrate_all()
        print("✅ Migration completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)
    finally:
        migrator.close()

if __name__ == "__main__":
    main()
```

#### 2.2 Validation Script
```python
#!/usr/bin/env python3
"""
Post-migration validation script
"""

import sqlite3
import psycopg2
import json
import sys
from typing import Dict, List, Tuple

class MigrationValidator:
    def __init__(self, sqlite_path: str, postgres_config: Dict[str, str]):
        self.sqlite_conn = sqlite3.connect(sqlite_path)
        self.postgres_conn = psycopg2.connect(**postgres_config)

    def validate_all(self) -> bool:
        """Run all validation checks"""
        validations = [
            ("Characters", self.validate_characters),
            ("Sessions", self.validate_sessions),
            ("Decisions", self.validate_decisions),
            ("Training Data", self.validate_training_data),
            ("Foreign Keys", self.validate_foreign_keys),
            ("Data Integrity", self.validate_data_integrity)
        ]

        all_passed = True

        for name, validator in validations:
            print(f"\n🔍 Validating {name}...")
            try:
                if validator():
                    print(f"✅ {name} validation passed")
                else:
                    print(f"❌ {name} validation failed")
                    all_passed = False
            except Exception as e:
                print(f"❌ {name} validation error: {str(e)}")
                all_passed = False

        return all_passed

    def validate_characters(self) -> bool:
        """Validate characters migration"""
        sqlite_count = self.sqlite_conn.execute("SELECT COUNT(*) FROM characters").fetchone()[0]
        pg_count = self.postgres_conn.execute("SELECT COUNT(*) FROM characters").fetchone()[0]

        print(f"   SQLite: {sqlite_count} records")
        print(f"   PostgreSQL: {pg_count} records")

        if sqlite_count != pg_count:
            print(f"   ⚠️  Count mismatch: {sqlite_count} vs {pg_count}")
            return False

        # Check data integrity
        sqlite_sample = self.sqlite_conn.execute("SELECT * FROM characters LIMIT 10").fetchall()
        for record in sqlite_sample:
            pg_record = self.postgres_conn.execute(
                "SELECT name, class, level FROM characters WHERE name = %s",
                (record['name'],)
            ).fetchone()

            if not pg_record or pg_record[0] != record['name']:
                print(f"   ⚠️  Data mismatch for character: {record['name']}")
                return False

        return True

    def validate_sessions(self) -> bool:
        """Validate sessions migration"""
        sqlite_count = self.sqlite_conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        pg_count = self.postgres_conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]

        print(f"   SQLite: {sqlite_count} records")
        print(f"   PostgreSQL: {pg_count} records")

        return sqlite_count == pg_count

    def validate_decisions(self) -> bool:
        """Validate decisions migration"""
        sqlite_count = self.sqlite_conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        pg_count = self.postgres_conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]

        print(f"   SQLite: {sqlite_count} records")
        print(f"   PostgreSQL: {pg_count} records")

        return sqlite_count == pg_count

    def validate_training_data(self) -> bool:
        """Validate training data migration"""
        sqlite_count = self.sqlite_conn.execute("SELECT COUNT(*) FROM training_data").fetchone()[0]
        pg_count = self.postgres_conn.execute("SELECT COUNT(*) FROM training_data").fetchone()[0]

        print(f"   SQLite: {sqlite_count} records")
        print(f"   PostgreSQL: {pg_count} records")

        return sqlite_count == pg_count

    def validate_foreign_keys(self) -> bool:
        """Validate foreign key constraints"""
        # Check for orphaned records
        orphaned_decisions = self.postgres_conn.execute("""
            SELECT COUNT(*) FROM decisions d
            LEFT JOIN characters c ON d.character_id = c.id
            WHERE c.id IS NULL
        """).fetchone()[0]

        orphaned_sessions = self.postgres_conn.execute("""
            SELECT COUNT(*) FROM sessions s
            LEFT JOIN characters c ON s.character_id = c.id
            WHERE c.id IS NULL
        """).fetchone()[0]

        if orphaned_decisions > 0:
            print(f"   ⚠️  {orphaned_decisions} orphaned decisions found")
            return False

        if orphaned_sessions > 0:
            print(f"   ⚠️  {orphaned_sessions} orphaned sessions found")
            return False

        return True

    def validate_data_integrity(self) -> bool:
        """Validate data integrity checks"""
        # Check for required fields
        null_names = self.postgres_conn.execute(
            "SELECT COUNT(*) FROM characters WHERE name IS NULL"
        ).fetchone()[0]

        if null_names > 0:
            print(f"   ⚠️  {null_names} characters with NULL names")
            return False

        # Check constraint violations
        invalid_levels = self.postgres_conn.execute(
            "SELECT COUNT(*) FROM characters WHERE level < 1 OR level > 20"
        ).fetchone()[0]

        if invalid_levels > 0:
            print(f"   ⚠️  {invalid_levels} characters with invalid levels")
            return False

        return True

    def close(self):
        """Close database connections"""
        self.sqlite_conn.close()
        self.postgres_conn.close()

def main():
    if len(sys.argv) != 3:
        print("Usage: python validate.py <sqlite_path> <postgres_config_json>")
        sys.exit(1)

    sqlite_path = sys.argv[1]
    postgres_config = json.loads(sys.argv[2])

    validator = MigrationValidator(sqlite_path, postgres_config)

    if validator.validate_all():
        print("\n🎉 All validations passed! Migration is successful.")
        sys.exit(0)
    else:
        print("\n💥 Validation failed! Please review the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Phase 3: Zero-Downtime Migration (Week 3)

#### 3.1 Double-Write Strategy Implementation
```python
# Database manager with double-write capability
class DoubleWriteDatabaseManager:
    """
    Database manager that writes to both SQLite and PostgreSQL during migration
    """

    def __init__(self, sqlite_path: str, postgres_config: Dict[str, str]):
        self.sqlite_conn = sqlite3.connect(sqlite_path)
        self.postgres_conn = psycopg2.connect(**postgres_config)
        self.migration_mode = "sqlite"  # sqlite, double-write, postgres

    def set_mode(self, mode: str):
        """Set the database mode"""
        if mode not in ["sqlite", "double-write", "postgres"]:
            raise ValueError("Invalid mode. Must be: sqlite, double-write, postgres")
        self.migration_mode = mode

    def insert_character(self, character_data: Dict):
        """Insert character with appropriate write strategy"""
        if self.migration_mode in ["sqlite", "double-write"]:
            # Write to SQLite
            self._insert_character_sqlite(character_data)

        if self.migration_mode in ["postgres", "double-write"]:
            # Write to PostgreSQL
            self._insert_character_postgres(character_data)

    def _insert_character_sqlite(self, data: Dict):
        """Insert into SQLite"""
        # SQLite implementation
        pass

    def _insert_character_postgres(self, data: Dict):
        """Insert into PostgreSQL"""
        # PostgreSQL implementation
        pass
```

#### 3.2 Migration Execution Plan
```bash
#!/bin/bash
# migration_execution.sh

set -e

echo "=== DMLog Database Migration Execution ==="

# Configuration
SQLITE_PATH="./data/dmlog.db"
POSTGRES_CONFIG_FILE="./config/postgres.json"

# Step 1: Backup existing data
echo "Step 1: Creating backup..."
cp $SQLITE_PATH "${SQLITE_PATH}.backup.$(date +%Y%m%d_%H%M%S)"

# Step 2: Run migration script
echo "Step 2: Running migration..."
python migrate.py $SQLITE_PATH "$(cat $POSTGRES_CONFIG_FILE)"

# Step 3: Validate migration
echo "Step 3: Validating migration..."
python validate.py $SQLITE_PATH "$(cat $POSTGRES_CONFIG_FILE)"

# Step 4: Update application configuration
echo "Step 4: Updating configuration..."
sed -i.bak 's/sqlite:\/\///postgresql:\/\//' config/database.yml

# Step 5: Restart services with read-only mode
echo "Step 5: Restarting services..."
docker-compose -f docker-compose.prod.yml up -d

# Step 6: Final validation
echo "Step 6: Final validation..."
python health_check.py

echo "✅ Migration completed successfully!"
```

### Phase 4: Post-Migration Optimization (Week 4)

#### 4.1 Performance Optimization
```sql
-- Create partitioned tables for large datasets
CREATE TABLE decisions_partitioned (
    LIKE decisions INCLUDING ALL
) PARTITION BY RANGE (decision_timestamp);

CREATE TABLE decisions_2024_01 PARTITION OF decisions_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE decisions_2024_02 PARTITION OF decisions_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Create materialized views for analytics
CREATE MATERIALIZED VIEW character_stats AS
SELECT
    c.id,
    c.name,
    c.class,
    c.level,
    COUNT(s.id) as session_count,
    COUNT(d.id) as decision_count,
    AVG(d.confidence_score) as avg_confidence,
    MAX(s.start_time) as last_session
FROM characters c
LEFT JOIN sessions s ON c.id = s.character_id
LEFT JOIN decisions d ON s.id = d.session_id
GROUP BY c.id, c.name, c.class, c.level;

-- Create indexes for materialized view
CREATE INDEX idx_character_stats_class ON character_stats(class);
CREATE INDEX idx_character_stats_level ON character_stats(level);

-- Refresh materialized view
CREATE OR REPLACE FUNCTION refresh_character_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY character_stats;
END;
$$ LANGUAGE plpgsql;

-- Schedule refresh
CREATE EXTENSION IF NOT EXISTS pg_cron;
SELECT cron.schedule('refresh-character-stats', '*/5 * * * *', 'SELECT refresh_character_stats();');
```

#### 4.2 Monitoring Queries
```sql
-- Monitor database performance
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY tablename, attname;

-- Monitor query performance
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Monitor table sizes
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC;
```

## Rollback Strategy

### 1. Immediate Rollback
```bash
#!/bin/bash
# rollback.sh

echo "=== Database Rollback Procedure ==="

# Stop PostgreSQL services
docker-compose -f docker-compose.prod.yml stop postgres

# Restore SQLite backup
LATEST_BACKUP=$(ls -t ./data/dmlog.db.backup.* | head -1)
cp $LATEST_BACKUP ./data/dmlog.db

# Update configuration back to SQLite
sed -i 's/postgresql:\/\///sqlite:\/\//' config/database.yml

# Restart services
docker-compose -f docker-compose.prod.yml up -d

echo "✅ Rollback completed"
```

### 2. Point-in-Time Recovery (PITR)
```sql
-- Enable WAL archiving
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET archive_mode = 'on';
ALTER SYSTEM SET archive_command = 'cp %p /var/lib/postgresql/archive/%f';
SELECT pg_reload_conf();

-- Create base backup
SELECT pg_start_backup('migration_backup');
-- Copy data files
SELECT pg_stop_backup();

-- Restore to specific point
-- 1. Stop PostgreSQL
-- 2. Restore base backup
-- 3. Apply WAL logs until desired time
```

## Testing Strategy

### 1. Unit Tests
```python
def test_migration_characters():
    """Test character migration"""
    # Setup test SQLite database
    # Run migration
    # Verify PostgreSQL data
    assert True

def test_foreign_key_constraints():
    """Test foreign key constraints"""
    # Try to insert orphaned record
    # Verify constraint violation
    assert True
```

### 2. Integration Tests
```python
def test_full_application_workflow():
    """Test complete workflow after migration"""
    # Create character
    # Create session
    # Add decisions
    # Generate training data
    # Verify all operations work
    assert True
```

### 3. Performance Tests
```python
def test_query_performance():
    """Test query performance benchmarks"""
    # Run benchmark queries
    # Compare SQLite vs PostgreSQL performance
    # Verify PostgreSQL is faster
    assert True
```

## Monitoring During Migration

### 1. Database Metrics
- Connection count
- Query latency
- Transaction throughput
- Lock contention
- Replication lag

### 2. Application Metrics
- API response times
- Error rates
- User activity
- Data consistency checks

### 3. Alerting Rules
```yaml
# Prometheus alert rules
groups:
  - name: postgresql
    rules:
      - alert: PostgreSQLDown
        expr: up{job="postgresql"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"

      - alert: PostgreSQLTooManyConnections
        expr: pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Too many PostgreSQL connections"

      - alert: MigrationValidationFailed
        expr: migration_validation_success == 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Migration validation failed"
```

## Success Criteria

1. **Data Integrity**: 100% data consistency between SQLite and PostgreSQL
2. **Performance**: Queries 2-5x faster than SQLite
3. **Availability**: Zero downtime during migration
4. **Scalability**: Support for 100+ concurrent users
5. **Recovery**: RTO < 1 hour, RPO < 15 minutes

## Timeline Summary

- **Week 1**: Assessment and schema design
- **Week 2**: Migration tools development
- **Week 3**: Zero-downtime migration execution
- **Week 4**: Optimization and monitoring setup

This comprehensive migration strategy ensures a smooth transition from SQLite to PostgreSQL with minimal risk and maximum performance gains.