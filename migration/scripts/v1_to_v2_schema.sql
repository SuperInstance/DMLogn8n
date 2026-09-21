-- DMLogn8n Schema Migration v1 to v2
-- This script migrates the database schema from version 1 to version 2
-- Includes new tables, column additions, and constraint updates

-- Enable transaction for atomic migration
BEGIN;

-- Create migration tracking table if not exists
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT,
    checksum VARCHAR(64)
);

-- Check if migration already applied
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM schema_migrations WHERE version = 'v2.0.0') THEN
        RAISE EXCEPTION 'Migration v2.0.0 already applied';
    END IF;
END $$;

-- === VERSION 2.0.0 SCHEMA CHANGES ===

-- 1. Add new columns to existing tables

-- Update characters table with new AI learning fields
ALTER TABLE characters
ADD COLUMN IF NOT EXISTS last_training_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS training_data_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS model_accuracy_score FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS personality_embedding JSONB,
ADD COLUMN IF NOT EXISTS behavior_clusters TEXT[],
ADD COLUMN IF NOT EXISTS ai_model_version VARCHAR(50) DEFAULT 'v1.0',
ADD COLUMN IF NOT EXISTS learning_confidence FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS adaptation_history JSONB DEFAULT '[]'::jsonb;

-- Update sessions table with enhanced tracking
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS ai_participants TEXT[],
ADD COLUMN IF NOT EXISTS dm_assistance_level INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS session_metadata JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS performance_metrics JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS player_satisfaction INTEGER CHECK (player_satisfaction >= 1 AND player_satisfaction <= 5),
ADD COLUMN IF NOT EXISTS ai_intervention_count INTEGER DEFAULT 0;

-- Update campaigns table with new features
ALTER TABLE campaigns
ADD COLUMN IF NOT EXISTS difficulty_level INTEGER DEFAULT 1 CHECK (difficulty_level >= 1 AND difficulty_level <= 10),
ADD COLUMN IF NOT EXISTS estimated_sessions INTEGER,
ADD COLUMN IF NOT EXISTS campaign_tags TEXT[],
ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS template_id VARCHAR(50),
ADD COLUMN IF NOT EXISTS campaign_setting JSONB DEFAULT '{}'::jsonb;

-- 2. Create new tables for v2.0.0 features

-- User preferences and settings
CREATE TABLE IF NOT EXISTS user_preferences (
    id VARCHAR(12) PRIMARY KEY DEFAULT (SUBSTRING(MD5(RANDOM()::TEXT), 1, 12)),
    user_id VARCHAR(50) NOT NULL,
    preference_key VARCHAR(100) NOT NULL,
    preference_value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, preference_key)
);

-- AI model configurations
CREATE TABLE IF NOT EXISTS ai_model_configs (
    id VARCHAR(12) PRIMARY KEY DEFAULT (SUBSTRING(MD5(RANDOM()::TEXT), 1, 12)),
    name VARCHAR(100) NOT NULL UNIQUE,
    model_type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    version VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(50)
);

-- Character relationships
CREATE TABLE IF NOT EXISTS character_relationships (
    id VARCHAR(12) PRIMARY KEY DEFAULT (SUBSTRING(MD5(RANDOM()::TEXT), 1, 12)),
    character_id_1 VARCHAR(12) NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    character_id_2 VARCHAR(12) NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    relationship_strength FLOAT DEFAULT 0.0 CHECK (relationship_strength >= -1.0 AND relationship_strength <= 1.0),
    relationship_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(character_id_1, character_id_2, relationship_type)
);

-- Session recordings and replays
CREATE TABLE IF NOT EXISTS session_recordings (
    id VARCHAR(12) PRIMARY KEY DEFAULT (SUBSTRING(MD5(RANDOM()::TEXT), 1, 12)),
    session_id VARCHAR(12) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    recording_data JSONB NOT NULL,
    recording_format VARCHAR(20) DEFAULT 'json',
    file_size_bytes INTEGER,
    duration_seconds INTEGER,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance analytics
CREATE TABLE IF NOT EXISTS performance_analytics (
    id VARCHAR(12) PRIMARY KEY DEFAULT (SUBSTRING(MD5(RANDOM()::TEXT), 1, 12)),
    entity_type VARCHAR(50) NOT NULL, -- 'character', 'session', 'campaign', etc.
    entity_id VARCHAR(12) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(20),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    context_data JSONB DEFAULT '{}'::jsonb
);

-- Content moderation and flags
CREATE TABLE IF NOT EXISTS content_flags (
    id VARCHAR(12) PRIMARY KEY DEFAULT (SUBSTRING(MD5(RANDOM()::TEXT), 1, 12)),
    content_type VARCHAR(50) NOT NULL,
    content_id VARCHAR(12) NOT NULL,
    flag_reason VARCHAR(200) NOT NULL,
    flag_type VARCHAR(50) NOT NULL, -- 'inappropriate', 'bug', 'quality', etc.
    flagged_by VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'reviewed', 'resolved', 'dismissed'
    admin_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- API keys and authentication tokens
CREATE TABLE IF NOT EXISTS api_keys (
    id VARCHAR(12) PRIMARY KEY DEFAULT (SUBSTRING(MD5(RANDOM()::TEXT), 1, 12)),
    key_hash VARCHAR(64) NOT NULL UNIQUE,
    key_name VARCHAR(100) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create new indexes for performance

-- Indexes for new character columns
CREATE INDEX IF NOT EXISTS idx_characters_ai_model_version ON characters(ai_model_version);
CREATE INDEX IF NOT EXISTS idx_characters_last_training_at ON characters(last_training_at);
CREATE INDEX IF NOT EXISTS idx_characters_learning_confidence ON characters(learning_confidence);
CREATE INDEX IF NOT EXISTS idx_characters_behavior_clusters ON characters USING GIN(behavior_clusters);

-- Indexes for new session columns
CREATE INDEX IF NOT EXISTS idx_sessions_ai_participants ON sessions USING GIN(ai_participants);
CREATE INDEX IF NOT EXISTS idx_sessions_dm_assistance_level ON sessions(dm_assistance_level);
CREATE INDEX IF NOT EXISTS idx_sessions_player_satisfaction ON sessions(player_satisfaction);

-- Indexes for new campaign columns
CREATE INDEX IF NOT EXISTS idx_campaigns_difficulty_level ON campaigns(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_campaigns_is_public ON campaigns(is_public);
CREATE INDEX IF NOT EXISTS idx_campaigns_tags ON campaigns USING GIN(campaign_tags);

-- Indexes for new tables
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_key ON user_preferences(preference_key);
CREATE INDEX IF NOT EXISTS idx_ai_model_configs_active ON ai_model_configs(is_active);
CREATE INDEX IF NOT EXISTS idx_character_relationships_char1 ON character_relationships(character_id_1);
CREATE INDEX IF NOT EXISTS idx_character_relationships_char2 ON character_relationships(character_id_2);
CREATE INDEX IF NOT EXISTS idx_character_relationships_type ON character_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_session_recordings_session_id ON session_recordings(session_id);
CREATE INDEX IF NOT EXISTS idx_session_recordings_public ON session_recordings(is_public);
CREATE INDEX IF NOT EXISTS idx_performance_analytics_entity ON performance_analytics(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_performance_analytics_recorded_at ON performance_analytics(recorded_at);
CREATE INDEX IF NOT EXISTS idx_content_flags_content ON content_flags(content_type, content_id);
CREATE INDEX IF NOT EXISTS idx_content_flags_status ON content_flags(status);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);

-- 4. Update existing constraints

-- Add check constraints for new columns
ALTER TABLE characters
ADD CONSTRAINT IF NOT EXISTS chk_characters_learning_confidence
    CHECK (learning_confidence >= 0.0 AND learning_confidence <= 1.0),
ADD CONSTRAINT IF NOT EXISTS chk_characters_training_count
    CHECK (training_data_count >= 0);

ALTER TABLE sessions
ADD CONSTRAINT IF NOT EXISTS chk_sessions_dm_assistance
    CHECK (dm_assistance_level >= 0 AND dm_assistance_level <= 5),
ADD CONSTRAINT IF NOT EXISTS chk_sessions_intervention_count
    CHECK (ai_intervention_count >= 0);

ALTER TABLE campaigns
ADD CONSTRAINT IF NOT EXISTS chk_campaigns_difficulty
    CHECK (difficulty_level >= 1 AND difficulty_level <= 10),
ADD CONSTRAINT IF NOT EXISTS chk_campaigns_estimated_sessions
    CHECK (estimated_sessions IS NULL OR estimated_sessions > 0);

-- 5. Create triggers for automatic timestamp updates

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables with updated_at columns
CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_model_configs_updated_at
    BEFORE UPDATE ON ai_model_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_character_relationships_updated_at
    BEFORE UPDATE ON character_relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 6. Create views for common queries

-- Character summary view with AI metrics
CREATE OR REPLACE VIEW character_summary AS
SELECT
    c.id,
    c.name,
    c.character_class,
    c.level,
    c.learning_rate,
    c.adaptation_score,
    c.training_data_count,
    c.model_accuracy_score,
    c.ai_model_version,
    c.learning_confidence,
    c.created_at,
    c.updated_at,
    COUNT(DISTINCT s.id) as session_count,
    COUNT(DISTINCT m.id) as memory_count,
    COUNT(DISTINCT d.id) as decision_count
FROM characters c
LEFT JOIN session_participants sp ON c.id = sp.character_id
LEFT JOIN sessions s ON sp.session_id = s.id
LEFT JOIN memories m ON c.id = m.character_id
LEFT JOIN decisions d ON c.id = d.character_id
GROUP BY c.id, c.name, c.character_class, c.level, c.learning_rate,
         c.adaptation_score, c.training_data_count, c.model_accuracy_score,
         c.ai_model_version, c.learning_confidence, c.created_at, c.updated_at;

-- Session performance view
CREATE OR REPLACE VIEW session_performance AS
SELECT
    s.id,
    s.title,
    s.phase,
    s.start_time,
    s.end_time,
    s.total_decisions,
    s.total_reward,
    s.avg_confidence,
    s.player_satisfaction,
    s.ai_intervention_count,
    s.dm_assistance_level,
    COUNT(DISTINCT sp.character_id) as participant_count,
    EXTRACT(EPOCH FROM (s.end_time - s.start_time)) as duration_seconds
FROM sessions s
LEFT JOIN session_participants sp ON s.id = sp.session_id
GROUP BY s.id, s.title, s.phase, s.start_time, s.end_time,
         s.total_decisions, s.total_reward, s.avg_confidence,
         s.player_satisfaction, s.ai_intervention_count, s.dm_assistance_level;

-- 7. Insert default data

-- Insert default AI model configurations
INSERT INTO ai_model_configs (name, model_type, config, version, created_by) VALUES
('Default Character Model', 'character_ai', '{"temperature": 0.7, "max_tokens": 1000, "response_format": "dnd"}', 'v2.0', 'system'),
('Combat AI Model', 'combat_ai', '{"strategy_aggression": 0.5, "team_coordination": true}', 'v2.0', 'system'),
('Dialogue AI Model', 'dialogue_ai', '{"personality_strength": 0.8, "memory_integration": true}', 'v2.0', 'system')
ON CONFLICT (name) DO NOTHING;

-- 8. Update existing data

-- Set default values for existing records
UPDATE characters SET
    ai_model_version = 'v1.0',
    learning_confidence = 0.5,
    training_data_count = COALESCE(
        (SELECT COUNT(*) FROM training_data WHERE training_data.character_id = characters.id), 0
    )
WHERE ai_model_version IS NULL;

UPDATE sessions SET
    player_satisfaction = 3,
    ai_intervention_count = 0
WHERE player_satisfaction IS NULL;

UPDATE campaigns SET
    difficulty_level = 1,
    is_public = false
WHERE difficulty_level IS NULL;

-- 9. Record migration completion

INSERT INTO schema_migrations (version, description, checksum) VALUES
('v2.0.0', 'Add AI learning features, performance analytics, and content moderation', MD5('v2.0.0_migration_complete'));

-- Commit the migration
COMMIT;

-- Migration completed successfully
DO $$
BEGIN
    RAISE NOTICE 'Migration v2.0.0 completed successfully';
    RAISE NOTICE 'Added % new tables', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('user_preferences', 'ai_model_configs', 'character_relationships', 'session_recordings', 'performance_analytics', 'content_flags', 'api_keys'));
    RAISE NOTICE 'Added % new indexes', (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE 'idx_%' AND indexname NOT LIKE '%_pkey');
END $$;