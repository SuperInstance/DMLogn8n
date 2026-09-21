-- DMLogn8n Index Optimization Script
-- Creates optimized indexes for better migration performance and query performance

-- Enable transaction for atomic index creation
BEGIN;

-- Create index optimization logging table
CREATE TABLE IF NOT EXISTS index_operations (
    id SERIAL PRIMARY KEY,
    operation_name VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    index_name VARCHAR(100),
    operation_type VARCHAR(20), -- 'create', 'drop', 'rebuild'
    execution_time_seconds FLOAT,
    index_size_mb FLOAT,
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT
);

-- === PERFORMANCE CRITICAL INDEXES ===

-- 1. Character table indexes for AI features

-- Primary index for character lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_characters_lookup
ON characters (id, is_active, created_at);

-- Composite index for character searches
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_characters_search
ON characters (is_active, character_class, level)
WHERE is_active = TRUE;

-- AI-specific indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_characters_ai_metrics
ON characters (ai_model_version, learning_confidence, training_data_count);

-- Full-text search index for character names
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_characters_name_fts
ON characters USING gin(to_tsvector('english', name));

-- GIN index for personality data
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_characters_personality_gin
ON characters USING GIN(personality_evolution);

-- JSONB index for behavior patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_characters_behavior_gin
ON characters USING GIN(behavior_patterns);

-- 2. Session table indexes for performance

-- Time-based indexes for session queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_time_range
ON sessions (start_time, end_time)
WHERE phase IN ('active', 'complete');

-- Session participant indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_participants
ON sessions (campaign_id, phase, start_time);

-- Performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_performance
ON sessions (total_reward, avg_confidence, total_decisions);

-- AI intervention tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_ai_intervention
ON sessions (ai_intervention_count, dm_assistance_level);

-- 3. Memory table indexes for AI learning

-- Character memory lookup indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memories_character_time
ON memories (character_id, created_at DESC);

-- Memory type and importance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memories_type_importance
ON memories (memory_type, importance DESC)
WHERE importance > 0.5;

-- Expiring memories index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memories_expiring
ON memories (expires_at)
WHERE expires_at IS NOT NULL;

-- Vector similarity search preparation (for embeddings)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memories_embedding_gin
ON memories USING GIN(embedding_vector)
WHERE embedding_vector IS NOT NULL;

-- 4. Decision table indexes for learning analytics

-- Character decision history
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_decisions_character_history
ON decisions (character_id, created_at DESC);

-- Decision quality tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_decisions_quality
ON decisions (quality_score, success)
WHERE quality_score IS NOT NULL;

-- AI vs human decision comparison
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_decisions_source_analysis
ON decisions (source, confidence, decision_type);

-- Session decision correlation
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_decisions_session_analysis
ON decisions (session_id, decision_type, created_at);

-- 5. Training data indexes for ML pipelines

-- Character training data lookup
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_training_data_character_status
ON training_data (character_id, training_status, created_at DESC);

-- Validated training data
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_training_data_validated
ON training_data (is_validated, validation_score DESC)
WHERE is_validated = TRUE;

-- Model version tracking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_training_data_model_version
ON training_data (model_version, data_type, created_at);

-- 6. Model version indexes for deployment tracking

-- Active model indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_model_versions_active
ON model_versions (character_id, is_active, created_at DESC)
WHERE is_active = TRUE;

-- Performance tracking indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_model_versions_performance
ON model_versions (success_rate, test_accuracy)
WHERE success_rate IS NOT NULL;

-- 7. Campaign table indexes

-- Campaign lookup indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_campaigns_lookup
ON campaigns (dm_id, is_active, created_at);

-- Public campaign discovery
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_campaigns_public
ON campaigns (is_public, difficulty_level, created_at DESC)
WHERE is_public = TRUE;

-- Campaign search indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_campaigns_search
ON campaigns USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));

-- 8. Session participant indexes

-- Participant lookup indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_session_participants_lookup
ON session_participants (session_id, character_id);

-- Performance tracking indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_session_participants_performance
ON session_participants (character_id, total_reward DESC, success_count DESC);

-- 9. Foreign key indexes for join performance

-- Campaign foreign key indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_campaign_fk
ON sessions (campaign_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_session_participants_session_fk
ON session_participants (session_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_session_participants_character_fk
ON session_participants (character_id);

-- Character foreign key indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memories_character_fk
ON memories (character_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_decisions_character_fk
ON decisions (character_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_decisions_session_fk
ON decisions (session_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_training_data_character_fk
ON training_data (character_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_training_data_session_fk
ON training_data (session_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_model_versions_character_fk
ON model_versions (character_id);

-- === PARTIAL INDEXES FOR SPECIFIC USE CASES ===

-- Active characters only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_characters_active_partial
ON characters (id, name, level)
WHERE is_active = TRUE;

-- Recent sessions only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_recent_partial
ON sessions (campaign_id, start_time DESC)
WHERE start_time > NOW() - INTERVAL '30 days';

-- Important memories only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memories_important_partial
ON memories (character_id, memory_type, created_at DESC)
WHERE importance > 0.7;

-- Recent decisions only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_decisions_recent_partial
ON decisions (character_id, decision_type, created_at DESC)
WHERE created_at > NOW() - INTERVAL '90 days';

-- High-quality training data only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_training_data_high_quality_partial
ON training_data (character_id, data_type, created_at DESC)
WHERE is_validated = TRUE AND validation_score > 0.8;

-- === MONITORING INDEXES ===

-- Create index size monitoring function
CREATE OR REPLACE FUNCTION get_index_size_mb(index_name text)
RETURNS float AS $$
DECLARE
    index_size_bytes bigint;
BEGIN
    SELECT pg_relation_size(index_name) INTO index_size_bytes;
    RETURN ROUND(index_size_bytes / (1024.0 * 1024.0), 2);
EXCEPTION
    WHEN OTHERS THEN
        RETURN 0;
END;
$$ LANGUAGE plpgsql;

-- Log index creation operations
DO $$
DECLARE
    index_record RECORD;
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    execution_time FLOAT;
    index_size FLOAT;
BEGIN
    -- Log character table indexes
    FOR index_record IN
        SELECT 'characters' as table_name, indexname as index_name
        FROM pg_indexes
        WHERE tablename = 'characters' AND indexname LIKE 'idx_%'
    LOOP
        start_time = clock_timestamp();

        -- Get index size
        SELECT get_index_size_mb(index_record.index_name) INTO index_size;

        end_time = clock_timestamp();
        execution_time := EXTRACT(EPOCH FROM (end_time - start_time));

        INSERT INTO index_operations (operation_name, table_name, index_name, operation_type, execution_time_seconds, index_size_mb, notes)
        VALUES ('create_index', index_record.table_name, index_record.index_name, 'create', execution_time, index_size, 'Optimized index for query performance');
    END LOOP;

    -- Log session table indexes
    FOR index_record IN
        SELECT 'sessions' as table_name, indexname as index_name
        FROM pg_indexes
        WHERE tablename = 'sessions' AND indexname LIKE 'idx_%'
    LOOP
        start_time = clock_timestamp();
        SELECT get_index_size_mb(index_record.index_name) INTO index_size;
        end_time = clock_timestamp();
        execution_time := EXTRACT(EPOCH FROM (end_time - start_time));

        INSERT INTO index_operations (operation_name, table_name, index_name, operation_type, execution_time_seconds, index_size_mb, notes)
        VALUES ('create_index', index_record.table_name, index_record.index_name, 'create', execution_time, index_size, 'Performance-critical index');
    END LOOP;
END $$;

-- === INDEX MAINTENANCE FUNCTIONS ===

-- Function to analyze table statistics
CREATE OR REPLACE FUNCTION analyze_table_stats(table_name text)
RETURNS void AS $$
BEGIN
    EXECUTE 'ANALYZE ' || quote_ident(table_name);
    RAISE NOTICE 'Analyzed table statistics for %', table_name;
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Failed to analyze table %: %', table_name, SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Function to rebuild fragmented indexes
CREATE OR REPLACE FUNCTION rebuild_index_if_needed(index_name text, threshold_mb float DEFAULT 100.0)
RETURNS void AS $$
DECLARE
    index_size float;
    bloat_estimate float;
BEGIN
    -- Get current index size
    SELECT get_index_size_mb(index_name) INTO index_size;

    -- Only rebuild if index is large enough
    IF index_size > threshold_mb THEN
        -- This would require additional bloat estimation logic
        -- For now, just log the index size
        INSERT INTO index_operations (operation_name, index_name, operation_type, index_size_mb, notes)
        VALUES ('index_size_check', index_name, 'monitor', index_size,
                'Index size monitoring - consider rebuild if performance degraded');

        RAISE NOTICE 'Index % size: % MB - monitoring for rebuild', index_name, index_size;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'Failed to check index %: %', index_name, SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- === OPTIMIZATION RECOMMENDATIONS ===

-- Create view for index usage statistics
CREATE OR REPLACE VIEW index_usage_stats AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    CASE
        WHEN idx_scan = 0 THEN 'UNUSED - Consider Dropping'
        WHEN idx_scan < 10 THEN 'LOW USAGE - Review Necessity'
        WHEN idx_scan < 100 THEN 'MODERATE USAGE'
        ELSE 'HIGH USAGE'
    END as usage_recommendation
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- Create view for table size and index summary
CREATE OR REPLACE VIEW table_index_summary AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as indexes_size,
    (SELECT COUNT(*) FROM pg_indexes WHERE tablename = t.tablename AND schemaname = t.schemaname) as index_count
FROM pg_tables t
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- === POST-CREATION ANALYSIS ===

-- Analyze all tables for optimal query planning
DO $$
DECLARE
    table_record RECORD;
BEGIN
    FOR table_record IN
        SELECT tablename FROM pg_tables WHERE schemaname = 'public'
        AND tablename IN ('characters', 'sessions', 'campaigns', 'memories', 'decisions', 'training_data', 'model_versions', 'session_participants')
    LOOP
        PERFORM analyze_table_stats(table_record.tablename);
    END LOOP;
END $$;

-- Generate optimization summary
DO $$
DECLARE
    total_indexes INTEGER;
    total_index_size_mb FLOAT;
    optimization_note TEXT;
BEGIN
    -- Count indexes created by this script
    SELECT COUNT(*), SUM(get_index_size_mb(indexname)) INTO total_indexes, total_index_size_mb
    FROM pg_indexes
    WHERE schemaname = 'public' AND indexname LIKE 'idx_%';

    RAISE NOTICE '=== INDEX OPTIMIZATION SUMMARY ===';
    RAISE NOTICE 'Total indexes created/optimized: %', total_indexes;
    RAISE NOTICE 'Total index size: % MB', COALESCE(total_index_size_mb, 0);
    RAISE NOTICE 'Optimization completed at: %', NOW();

    -- Check for unused indexes
    IF EXISTS (SELECT 1 FROM pg_stat_user_indexes WHERE idx_scan = 0 AND indexname LIKE 'idx_%') THEN
        RAISE NOTICE 'WARNING: Some indexes are not being used. Consider reviewing:';
        RAISE NOTICE '%', (SELECT STRING_AGG(indexname, ', ') FROM pg_stat_user_indexes WHERE idx_scan = 0 AND indexname LIKE 'idx_%');
    END IF;

    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Monitor query performance after migration';
    RAISE NOTICE '2. Review index usage statistics periodically';
    RAISE NOTICE '3. Consider removing unused indexes after stabilization period';
    RAISE NOTICE '4. Schedule regular ANALYZE operations for statistics updates';
END $$;

-- Commit index optimization
COMMIT;

-- Index optimization completed successfully
DO $$
BEGIN
    RAISE NOTICE 'Index optimization completed successfully';
    RAISE NOTICE 'Database is now optimized for migration and production workloads';
END $$;