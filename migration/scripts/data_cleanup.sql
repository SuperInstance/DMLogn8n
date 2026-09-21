-- DMLogn8n Data Cleanup Script
-- Cleans up and normalizes data before migration

-- Enable transaction for atomic cleanup
BEGIN;

-- Create cleanup logging table
CREATE TABLE IF NOT EXISTS cleanup_operations (
    id SERIAL PRIMARY KEY,
    operation_name VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    records_affected INTEGER,
    operation_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'completed',
    notes TEXT
);

-- === DATA CLEANUP OPERATIONS ===

-- 1. Remove duplicate records

-- Log cleanup operation
INSERT INTO cleanup_operations (operation_name, table_name, notes)
VALUES ('remove_duplicate_characters', 'characters', 'Removing duplicate characters based on name and class');

-- Remove duplicate characters (keep newest)
DELETE FROM characters
WHERE id NOT IN (
    SELECT DISTINCT ON (name, character_class) id
    FROM characters
    ORDER BY name, character_class, created_at DESC
);

-- Log result
UPDATE cleanup_operations
SET records_affected = (
    SELECT COUNT(*) FROM (
        SELECT id FROM characters GROUP BY name, character_class HAVING COUNT(*) > 1
    ) dupes
)
WHERE operation_name = 'remove_duplicate_characters' AND table_name = 'characters';

-- 2. Clean up invalid data

-- Fix invalid character levels
INSERT INTO cleanup_operations (operation_name, table_name, notes)
VALUES ('fix_invalid_levels', 'characters', 'Setting invalid levels to default value of 1');

UPDATE characters
SET level = 1
WHERE level < 1 OR level > 20 OR level IS NULL;

UPDATE cleanup_operations
SET records_affected = (
    SELECT COUNT(*) FROM characters WHERE level = 1
)
WHERE operation_name = 'fix_invalid_levels';

-- Fix invalid email formats in user data (if users table exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users') THEN
        INSERT INTO cleanup_operations (operation_name, table_name, notes)
        VALUES ('fix_invalid_emails', 'users', 'Removing invalid email addresses');

        -- This would need to be adapted based on actual user table structure
        -- UPDATE users SET email = NULL WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';

        UPDATE cleanup_operations
        SET records_affected = 0
        WHERE operation_name = 'fix_invalid_emails';
    END IF;
END $$;

-- 3. Normalize data formats

-- Standardize character names (title case)
INSERT INTO cleanup_operations (operation_name, table_name, notes)
VALUES ('normalize_character_names', 'characters', 'Converting character names to title case');

UPDATE characters
SET name = INITCAP(TRIM(name))
WHERE name != INITCAP(TRIM(name));

UPDATE cleanup_operations
SET records_affected = (
    SELECT COUNT(*) FROM characters WHERE name = INITCAP(TRIM(name))
)
WHERE operation_name = 'normalize_character_names';

-- Standardize character class names
INSERT INTO cleanup_operations (operation_name, table_name, notes)
VALUES ('normalize_class_names', 'characters', 'Converting character class names to lowercase');

UPDATE characters
SET character_class = LOWER(TRIM(character_class))
WHERE character_class != LOWER(TRIM(character_class));

UPDATE cleanup_operations
SET records_affected = (
    SELECT COUNT(*) FROM characters WHERE character_class = LOWER(TRIM(character_class))
)
WHERE operation_name = 'normalize_class_names';

-- 4. Clean up orphaned records

-- Remove session participants without valid sessions
INSERT INTO cleanup_operations (operation_name, table_name, notes)
VALUES ('remove_orphaned_participants', 'session_participants', 'Removing participants for non-existent sessions');

DELETE FROM session_participants
WHERE session_id NOT IN (SELECT id FROM sessions);

UPDATE cleanup_operations
SET records_affected = (
    SELECT COUNT(*) FROM session_participants
    WHERE session_id NOT IN (SELECT id FROM sessions)
)
WHERE operation_name = 'remove_orphaned_participants';

-- Remove memories without valid characters
INSERT INTO cleanup_operations (operation_name, table_name, notes)
VALUES ('remove_orphaned_memories', 'memories', 'Removing memories for non-existent characters');

DELETE FROM memories
WHERE character_id NOT IN (SELECT id FROM characters);

UPDATE cleanup_operations
SET records_affected = (
    SELECT COUNT(*) FROM memories
    WHERE character_id NOT IN (SELECT id FROM characters)
)
WHERE operation_name = 'remove_orphaned_memories';

-- Remove decisions without valid characters
INSERT INTO cleanup_operations (operation_name, table_name, notes)
VALUES ('remove_orphaned_decisions', 'decisions', 'Removing decisions for non-existent characters');

DELETE FROM decisions
WHERE character_id NOT IN (SELECT id FROM characters);

UPDATE cleanup_operations
SET records_affected = (
    SELECT COUNT(*) FROM decisions
    WHERE character_id NOT IN (SELECT id FROM characters)
)
WHERE operation_name = 'remove_orphaned_decisions';

-- 5. Fix data consistency issues

-- Ensure all sessions have valid start times
INSERT INTO cleanup_operations (operation_name, table_name, notes)
VALUES ('fix_session_timestamps', 'sessions', 'Setting missing start times to creation time');

UPDATE sessions
SET start_time = created_at
WHERE start_time IS NULL;

UPDATE cleanup_operations
SET records_affected = (
    SELECT COUNT(*) FROM sessions WHERE start_time = created_at
)
WHERE operation_name = 'fix_session_timestamps';

-- Fix session end times that are before start times
INSERT INTO cleanup_operations (operation_name, table_name, notes)
VALUES ('fix_session_end_times', 'sessions', 'Removing invalid end times');

UPDATE sessions
SET end_time = NULL
WHERE end_time IS NOT NULL AND end_time < start_time;

UPDATE cleanup_operations
SET records_affected = (
    SELECT COUNT(*) FROM sessions WHERE end_time IS NULL
)
WHERE operation_name = 'fix_session_end_times';

-- 6. Clean up text fields

-- Remove excessive whitespace from text fields
INSERT INTO cleanup_operations (operation_name, table_name, notes)
VALUES ('clean_text_whitespace', 'characters', 'Removing excessive whitespace from text fields');

UPDATE characters
SET
    backstory = TRIM(REGEXP_REPLACE(backstory, '\s+', ' ', 'g')),
    personality_traits = COALESCE(personality_traits, '[]'::json),
    ideals = COALESCE(ideals, '[]'::json),
    bonds = COALESCE(bonds, '[]'::json),
    flaws = COALESCE(flaws, '[]'::json)
WHERE backstory IS NOT NULL;

UPDATE cleanup_operations
SET records_affected = (
    SELECT COUNT(*) FROM characters WHERE backstory IS NOT NULL
)
WHERE operation_name = 'clean_text_whitespace';

-- 7. Update statistics and metadata

-- Update character statistics
INSERT INTO cleanup_operations (operation_name, table_name, notes)
VALUES ('update_character_stats', 'characters', 'Recalculating character statistics');

UPDATE characters
SET training_data_count = (
    SELECT COUNT(*)
    FROM training_data
    WHERE training_data.character_id = characters.id
)
WHERE training_data_count IS NULL;

UPDATE cleanup_operations
SET records_affected = (
    SELECT COUNT(*) FROM characters WHERE training_data_count IS NOT NULL
)
WHERE operation_name = 'update_character_stats';

-- Update session statistics
INSERT INTO cleanup_operations (operation_name, table_name, notes)
VALUES ('update_session_stats', 'sessions', 'Recalculating session statistics');

UPDATE sessions
SET total_decisions = (
    SELECT COUNT(*)
    FROM decisions
    WHERE decisions.session_id = sessions.id
)
WHERE total_decisions IS NULL OR total_decisions = 0;

UPDATE cleanup_operations
SET records_affected = (
    SELECT COUNT(*) FROM sessions WHERE total_decisions > 0
)
WHERE operation_name = 'update_session_stats';

-- 8. Remove expired temporary data

-- Remove expired memories (if expires_at exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'memories' AND column_name = 'expires_at') THEN
        INSERT INTO cleanup_operations (operation_name, table_name, notes)
        VALUES ('remove_expired_memories', 'memories', 'Removing expired memory records');

        DELETE FROM memories
        WHERE expires_at IS NOT NULL AND expires_at < NOW();

        UPDATE cleanup_operations
        SET records_affected = (
            SELECT COUNT(*) FROM memories
            WHERE expires_at IS NOT NULL AND expires_at < NOW()
        )
        WHERE operation_name = 'remove_expired_memories';
    END IF;
END $$;

-- 9. Optimize table sizes (VACUUM ANALYZE)
INSERT INTO cleanup_operations (operation_name, table_name, notes)
VALUES ('vacuum_analyze_tables', 'multiple', 'Running VACUUM ANALYZE on all tables');

-- Note: VACUUM ANALYZE would be run separately as it requires specific permissions
-- ANALYZE characters;
-- ANALYZE sessions;
-- ANALYZE campaigns;
-- ANALYZE memories;
-- ANALYZE decisions;
-- ANALYZE training_data;

UPDATE cleanup_operations
SET records_affected = 0
WHERE operation_name = 'vacuum_analyze_tables';

-- === CLEANUP SUMMARY ===

-- Generate cleanup summary report
DO $$
DECLARE
    total_operations INTEGER;
    total_records_affected INTEGER;
BEGIN
    SELECT COUNT(*), SUM(records_affected) INTO total_operations, total_records_affected
    FROM cleanup_operations;

    RAISE NOTICE '=== DATA CLEANUP SUMMARY ===';
    RAISE NOTICE 'Total cleanup operations: %', total_operations;
    RAISE NOTICE 'Total records affected: %', COALESCE(total_records_affected, 0);
    RAISE NOTICE 'Cleanup completed at: %', NOW();

    -- Show operation details
    RAISE NOTICE '';
    RAISE NOTICE '=== OPERATION DETAILS ===';

    FOR op_record IN
        SELECT operation_name, table_name, records_affected, status, notes
        FROM cleanup_operations
        ORDER BY operation_time
    LOOP
        RAISE NOTICE 'Operation: %', op_record.operation_name;
        RAISE NOTICE '  Table: %', COALESCE(op_record.table_name, 'N/A');
        RAISE NOTICE '  Records affected: %', COALESCE(op_record.records_affected, 0);
        RAISE NOTICE '  Status: %', op_record.status;
        RAISE NOTICE '  Notes: %', op_record.notes;
        RAISE NOTICE '';
    END LOOP;
END $$;

-- Commit the cleanup
COMMIT;

-- Cleanup completed successfully
DO $$
BEGIN
    RAISE NOTICE 'Data cleanup completed successfully';
    RAISE NOTICE 'Database is now ready for migration';
END $$;