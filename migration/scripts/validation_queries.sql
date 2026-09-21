-- DMLogn8n Migration Validation Queries
-- Comprehensive SQL queries to validate data integrity after migration

-- ================================================================================
-- DATA INTEGRITY VALIDATION QUERIES
-- ================================================================================

-- 1. Row Count Validation
-- Verify that row counts match between expected and actual values

-- Character table validation
SELECT 'characters' as table_name,
       COUNT(*) as actual_count,
       1000 as expected_count,  -- Replace with actual expected count
       CASE
           WHEN COUNT(*) = 1000 THEN 'PASS'
           ELSE 'FAIL'
       END as validation_status,
       ABS(COUNT(*) - 1000) as difference,
       ROUND(ABS(COUNT(*) - 1000.0) / 1000 * 100, 2) as percentage_diff
FROM characters;

-- Session table validation
SELECT 'sessions' as table_name,
       COUNT(*) as actual_count,
       500 as expected_count,  -- Replace with actual expected count
       CASE
           WHEN COUNT(*) = 500 THEN 'PASS'
           ELSE 'FAIL'
       END as validation_status,
       ABS(COUNT(*) - 500) as difference,
       ROUND(ABS(COUNT(*) - 500.0) / 500 * 100, 2) as percentage_diff
FROM sessions;

-- Campaign table validation
SELECT 'campaigns' as table_name,
       COUNT(*) as actual_count,
       50 as expected_count,  -- Replace with actual expected count
       CASE
           WHEN COUNT(*) = 50 THEN 'PASS'
           ELSE 'FAIL'
       END as validation_status,
       ABS(COUNT(*) - 50) as difference,
       ROUND(ABS(COUNT(*) - 50.0) / 50 * 100, 2) as percentage_diff
FROM campaigns;

-- Memory table validation
SELECT 'memories' as table_name,
       COUNT(*) as actual_count,
       2000 as expected_count,  -- Replace with actual expected count
       CASE
           WHEN COUNT(*) = 2000 THEN 'PASS'
           ELSE 'FAIL'
       END as validation_status,
       ABS(COUNT(*) - 2000) as difference,
       ROUND(ABS(COUNT(*) - 2000.0) / 2000 * 100, 2) as percentage_diff
FROM memories;

-- Decision table validation
SELECT 'decisions' as table_name,
       COUNT(*) as actual_count,
       1500 as expected_count,  -- Replace with actual expected count
       CASE
           WHEN COUNT(*) = 1500 THEN 'PASS'
           ELSE 'FAIL'
       END as validation_status,
       ABS(COUNT(*) - 1500) as difference,
       ROUND(ABS(COUNT(*) - 1500.0) / 1500 * 100, 2) as percentage_diff
FROM decisions;

-- ================================================================================
-- DATA CONSISTENCY VALIDATION
-- ================================================================================

-- 2. Foreign Key Integrity Validation

-- Check for orphaned session participants
SELECT 'orphaned_session_participants' as validation_name,
       COUNT(*) as orphaned_count,
       CASE
           WHEN COUNT(*) = 0 THEN 'PASS'
           ELSE 'FAIL'
       END as validation_status
FROM session_participants sp
LEFT JOIN sessions s ON sp.session_id = s.id
WHERE s.id IS NULL;

-- Check for orphaned memories
SELECT 'orphaned_memories' as validation_name,
       COUNT(*) as orphaned_count,
       CASE
           WHEN COUNT(*) = 0 THEN 'PASS'
           ELSE 'FAIL'
       END as validation_status
FROM memories m
LEFT JOIN characters c ON m.character_id = c.id
WHERE c.id IS NULL;

-- Check for orphaned decisions
SELECT 'orphaned_decisions' as validation_name,
       COUNT(*) as orphaned_count,
       CASE
           WHEN COUNT(*) = 0 THEN 'PASS'
           ELSE 'FAIL'
       END as validation_status
FROM decisions d
LEFT JOIN characters c ON d.character_id = c.id
WHERE c.id IS NULL;

-- Check for orphaned training data
SELECT 'orphaned_training_data' as validation_name,
       COUNT(*) as orphaned_count,
       CASE
           WHEN COUNT(*) = 0 THEN 'PASS'
           ELSE 'FAIL'
       END as validation_status
FROM training_data td
LEFT JOIN characters c ON td.character_id = c.id
WHERE c.id IS NULL;

-- ================================================================================
-- DATA QUALITY VALIDATION
-- ================================================================================

-- 3. Data Type and Format Validation

-- Check for invalid character levels
SELECT 'invalid_character_levels' as validation_name,
       COUNT(*) as invalid_count,
       CASE
           WHEN COUNT(*) = 0 THEN 'PASS'
           ELSE 'FAIL'
       END as validation_status
FROM characters
WHERE level < 1 OR level > 20 OR level IS NULL;

-- Check for invalid confidence scores
SELECT 'invalid_confidence_scores' as validation_name,
       COUNT(*) as invalid_count,
       CASE
           WHEN COUNT(*) = 0 THEN 'PASS'
           ELSE 'FAIL'
       END as validation_status
FROM decisions
WHERE confidence < 0 OR confidence > 1 OR confidence IS NULL;

-- Check for invalid memory importance scores
SELECT 'invalid_memory_importance' as validation_name,
       COUNT(*) as invalid_count,
       CASE
           WHEN COUNT(*) = 0 THEN 'PASS'
           ELSE 'FAIL'
       END as validation_status
FROM memories
WHERE importance < 0 OR importance > 1 OR importance IS NULL;

-- Check for null required fields
SELECT 'null_required_character_fields' as validation_name,
       COUNT(*) as invalid_count,
       CASE
           WHEN COUNT(*) = 0 THEN 'PASS'
           ELSE 'FAIL'
       END as validation_status
FROM characters
WHERE name IS NULL OR character_class IS NULL OR level IS NULL;

-- ================================================================================
-- BUSINESS RULE VALIDATION
-- ================================================================================

-- 4. Business Logic Validation

-- Check sessions with end time before start time
SELECT 'invalid_session_times' as validation_name,
       COUNT(*) as invalid_count,
       CASE
           WHEN COUNT(*) = 0 THEN 'PASS'
           ELSE 'FAIL'
       END as validation_status
FROM sessions
WHERE end_time IS NOT NULL AND start_time > end_time;

-- Check sessions without participants
SELECT 'sessions_without_participants' as validation_name,
       COUNT(*) as invalid_count,
       CASE
           WHEN COUNT(*) = 0 THEN 'PASS'
           ELSE 'FAIL'
       END as validation_status
FROM sessions s
LEFT JOIN session_participants sp ON s.id = sp.session_id
WHERE sp.session_id IS NULL;

-- Check characters without campaigns (if all should have campaigns)
SELECT 'characters_without_campaigns' as validation_name,
       COUNT(*) as count,
       CASE
           WHEN COUNT(*) = 0 THEN 'PASS'
           ELSE 'REVIEW'
       END as validation_status
FROM characters c
LEFT JOIN session_participants sp ON c.id = sp.character_id
LEFT JOIN sessions s ON sp.session_id = s.id
WHERE s.id IS NULL AND c.is_active = TRUE;

-- Check for duplicate character names (should be unique per campaign)
SELECT 'duplicate_character_names' as validation_name,
       COUNT(*) as duplicate_count,
       CASE
           WHEN COUNT(*) = 0 THEN 'PASS'
           ELSE 'FAIL'
       END as validation_status
FROM (
    SELECT name, character_class, COUNT(*) as dup_count
    FROM characters
    GROUP BY name, character_class
    HAVING COUNT(*) > 1
) duplicates;

-- ================================================================================
-- PERFORMANCE VALIDATION
-- ================================================================================

-- 5. Performance Metrics Validation

-- Check average decision confidence (should be reasonable)
SELECT 'average_decision_confidence' as validation_name,
       ROUND(AVG(confidence), 3) as avg_confidence,
       CASE
           WHEN AVG(confidence) BETWEEN 0.3 AND 0.9 THEN 'PASS'
           WHEN AVG(confidence) IS NULL THEN 'FAIL'
           ELSE 'REVIEW'
       END as validation_status
FROM decisions;

-- Check memory importance distribution
SELECT 'memory_importance_distribution' as validation_name,
       importance_level,
       COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM (
    SELECT
        CASE
            WHEN importance >= 0.8 THEN 'high'
            WHEN importance >= 0.5 THEN 'medium'
            ELSE 'low'
        END as importance_level
    FROM memories
) importance_groups
GROUP BY importance_level
ORDER BY importance_level DESC;

-- Check character level distribution
SELECT 'character_level_distribution' as validation_name,
       level_range,
       COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM (
    SELECT
        CASE
            WHEN level <= 5 THEN 'beginner (1-5)'
            WHEN level <= 10 THEN 'intermediate (6-10)'
            WHEN level <= 15 THEN 'advanced (11-15)'
            ELSE 'expert (16-20)'
        END as level_range
    FROM characters
    WHERE is_active = TRUE
) level_groups
GROUP BY level_range
ORDER BY
    CASE
        WHEN level_range = 'beginner (1-5)' THEN 1
        WHEN level_range = 'intermediate (6-10)' THEN 2
        WHEN level_range = 'advanced (11-15)' THEN 3
        ELSE 4
    END;

-- ================================================================================
-- DATA COMPLETENESS VALIDATION
-- ================================================================================

-- 6. Completeness Validation

-- Check for empty JSON fields
SELECT 'empty_personality_traits' as validation_name,
       COUNT(*) as count,
       CASE
           WHEN COUNT(*) = 0 THEN 'PASS'
           ELSE 'REVIEW'
       END as validation_status
FROM characters
WHERE personality_traits = '{}'::json OR personality_traits = '[]'::json OR personality_traits IS NULL;

-- Check for missing backstory on active characters
SELECT 'missing_backstory' as validation_name,
       COUNT(*) as count,
       CASE
           WHEN COUNT(*) = 0 THEN 'PASS'
           ELSE 'REVIEW'
       END as validation_status
FROM characters
WHERE (backstory IS NULL OR TRIM(backstory) = '') AND is_active = TRUE;

-- Check for sessions without transcripts
SELECT 'sessions_without_transcripts' as validation_name,
       COUNT(*) as count,
       CASE
           WHEN COUNT(*) = 0 THEN 'PASS'
           ELSE 'REVIEW'
       END as validation_status
FROM sessions
WHERE transcript = '{}'::json OR transcript IS NULL;

-- ================================================================================
-- STATISTICAL VALIDATION
-- ================================================================================

-- 7. Statistical Anomaly Detection

-- Check for unusually high decision counts
SELECT 'high_decision_count_characters' as validation_name,
       COUNT(*) as character_count,
       AVG(decision_count) as avg_decisions,
       MAX(decision_count) as max_decisions
FROM (
    SELECT c.id, COUNT(d.id) as decision_count
    FROM characters c
    LEFT JOIN decisions d ON c.id = d.character_id
    GROUP BY c.id
    HAVING COUNT(d.id) > 100  -- Threshold for unusually high count
) high_decision_chars;

-- Check for characters with no decisions (might indicate issues)
SELECT 'characters_without_decisions' as validation_name,
       COUNT(*) as count,
       CASE
           WHEN COUNT(*) < 10 THEN 'PASS'  -- Allow a few without decisions
           ELSE 'REVIEW'
       END as validation_status
FROM characters c
LEFT JOIN decisions d ON c.id = d.character_id
WHERE d.id IS NULL AND c.is_active = TRUE;

-- Check memory retention patterns
SELECT 'memory_retention_analysis' as validation_name,
       character_id,
       memory_count,
       days_since_last_memory,
       CASE
           WHEN days_since_last_memory > 30 AND memory_count > 0 THEN 'POTENTIAL_ISSUE'
           ELSE 'NORMAL'
       END as status
FROM (
    SELECT
        c.id as character_id,
        COUNT(m.id) as memory_count,
        EXTRACT(DAYS FROM NOW() - MAX(m.created_at)) as days_since_last_memory
    FROM characters c
    LEFT JOIN memories m ON c.id = m.character_id
    WHERE c.is_active = TRUE
    GROUP BY c.id
    HAVING COUNT(m.id) > 0
) memory_analysis
WHERE days_since_last_memory > 30;

-- ================================================================================
-- COMPREHENSIVE VALIDATION SUMMARY
-- ================================================================================

-- 8. Overall Validation Summary

CREATE OR REPLACE TEMPORARY VIEW validation_summary AS
SELECT 'Data Integrity' as category,
       SUM(CASE WHEN validation_status = 'PASS' THEN 1 ELSE 0 END) as passed,
       SUM(CASE WHEN validation_status = 'FAIL' THEN 1 ELSE 0 END) as failed,
       SUM(CASE WHEN validation_status = 'REVIEW' THEN 1 ELSE 0 END) as needs_review,
       COUNT(*) as total_checks
FROM (
    -- Row count validations
    SELECT * FROM (
        SELECT validation_status FROM (
            SELECT CASE WHEN COUNT(*) = 1000 THEN 'PASS' ELSE 'FAIL' END as validation_status FROM characters
            UNION ALL
            SELECT CASE WHEN COUNT(*) = 500 THEN 'PASS' ELSE 'FAIL' END as validation_status FROM sessions
            UNION ALL
            SELECT CASE WHEN COUNT(*) = 50 THEN 'PASS' ELSE 'FAIL' END as validation_status FROM campaigns
        ) row_counts
    ) integrity_checks

    UNION ALL

    -- Foreign key validations
    SELECT * FROM (
        SELECT CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END as validation_status
        FROM session_participants sp LEFT JOIN sessions s ON sp.session_id = s.id WHERE s.id IS NULL

        UNION ALL

        SELECT CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END as validation_status
        FROM memories m LEFT JOIN characters c ON m.character_id = c.id WHERE c.id IS NULL
    ) fk_checks
) all_validations;

-- Final validation report
SELECT
    category,
    passed,
    failed,
    needs_review,
    total_checks,
    ROUND(passed * 100.0 / total_checks, 2) as pass_rate,
    CASE
        WHEN failed = 0 AND needs_review = 0 THEN 'EXCELLENT'
        WHEN failed = 0 AND needs_review <= 2 THEN 'GOOD'
        WHEN failed <= 2 THEN 'ACCEPTABLE'
        ELSE 'NEEDS_ATTENTION'
    END as overall_status
FROM validation_summary;

-- ================================================================================
-- AUTOMATED VALIDATION FUNCTIONS
-- ================================================================================

-- Function to run all validations and return summary
CREATE OR REPLACE FUNCTION run_migration_validation()
RETURNS TABLE(
    validation_name TEXT,
    validation_type TEXT,
    result TEXT,
    details TEXT
) AS $$
BEGIN
    -- This would contain calls to all validation queries above
    -- Returning structured results for automated processing

    RETURN QUERY
    SELECT 'row_count_validation'::TEXT, 'integrity'::TEXT,
           (SELECT CASE WHEN COUNT(*) = 1000 THEN 'PASS' ELSE 'FAIL' END FROM characters)::TEXT,
           ('Characters: ' || COUNT(*)::TEXT)::TEXT
    FROM characters;

    -- Add more validation queries here...

END;
$$ LANGUAGE plpgsql;

-- Function to validate specific table
CREATE OR REPLACE FUNCTION validate_table(table_name TEXT)
RETURNS TABLE(
    check_name TEXT,
    status TEXT,
    count BIGINT,
    details TEXT
) AS $$
BEGIN
    -- Dynamic table validation based on table name
    IF table_name = 'characters' THEN
        RETURN QUERY
        SELECT 'row_count'::TEXT,
               CASE WHEN COUNT(*) = 1000 THEN 'PASS' ELSE 'FAIL' END::TEXT,
               COUNT(*)::BIGINT,
               'Expected: 1000, Actual: ' || COUNT(*)::TEXT
        FROM characters;

    ELSIF table_name = 'sessions' THEN
        RETURN QUERY
        SELECT 'row_count'::TEXT,
               CASE WHEN COUNT(*) = 500 THEN 'PASS' ELSE 'FAIL' END::TEXT,
               COUNT(*)::BIGINT,
               'Expected: 500, Actual: ' || COUNT(*)::TEXT
        FROM sessions;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Usage example:
-- SELECT * FROM run_migration_validation();
-- SELECT * FROM validate_table('characters');

-- ================================================================================
-- POST-MIGRATION CLEANUP
-- ================================================================================

-- Cleanup validation results table if it exists
DROP TABLE IF EXISTS migration_validation_results;

-- Create validation results table for tracking
CREATE TABLE migration_validation_results (
    id SERIAL PRIMARY KEY,
    validation_name TEXT NOT NULL,
    validation_type TEXT NOT NULL,
    status TEXT NOT NULL,
    count BIGINT,
    details TEXT,
    validation_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    migration_id TEXT DEFAULT 'v1_to_v2'
);

-- Insert validation results for record keeping
-- (This would be populated by the validation functions above)

-- Validation completed successfully
DO $$
BEGIN
    RAISE NOTICE 'Migration validation queries executed successfully';
    RAISE NOTICE 'Review the results above to ensure data integrity';
    RAISE NOTICE 'Run validation functions for automated checking: SELECT * FROM run_migration_validation()';
END $$;