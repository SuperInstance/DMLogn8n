-- DMlogn8n Cross-Platform Sync Database Schema
-- Universal Save System for Multi-Platform Synchronization

-- ========================================
-- Core User and Platform Management
-- ========================================

-- Platform types enumeration
CREATE TYPE platform_type AS ENUM (
    'web',
    'mobile_ios',
    'mobile_android',
    'desktop_windows',
    'desktop_macos',
    'desktop_linux',
    'vr_oculus',
    'vr_htc',
    'ar_ios',
    'ar_android'
);

-- Sync status enumeration
CREATE TYPE sync_status AS ENUM (
    'pending',
    'syncing',
    'synced',
    'conflict',
    'error',
    'offline'
);

-- Conflict resolution strategy
CREATE TYPE conflict_resolution AS ENUM (
    'last_write_wins',
    'manual_review',
    'merge_auto',
    'merge_manual',
    'platform_priority'
);

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    subscription_tier VARCHAR(20) DEFAULT 'free',
    storage_quota_mb INTEGER DEFAULT 1024,
    current_storage_mb INTEGER DEFAULT 0
);

-- User platform registrations
CREATE TABLE user_platforms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform platform_type NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    device_name VARCHAR(100),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    sync_version BIGINT DEFAULT 1,
    UNIQUE(user_id, platform, device_id)
);

-- ========================================
-- Save Data Architecture
-- ========================================

-- Save games master table
CREATE TABLE save_games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    campaign_name VARCHAR(200) NOT NULL,
    character_name VARCHAR(100),
    game_version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_synced TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sync_status sync_status DEFAULT 'synced',
    is_active BOOLEAN DEFAULT true,
    total_playtime_minutes INTEGER DEFAULT 0,
    current_chapter INTEGER DEFAULT 1,
    current_scene VARCHAR(100),
    completion_percentage DECIMAL(5,2) DEFAULT 0.00,
    checksum VARCHAR(64),
    file_size_bytes BIGINT DEFAULT 0,
    UNIQUE(user_id, campaign_name)
);

-- Save game data JSONB storage
CREATE TABLE save_game_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    save_game_id UUID NOT NULL REFERENCES save_games(id) ON DELETE CASCADE,
    platform platform_type NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    data_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sync_version BIGINT NOT NULL,
    is_current BOOLEAN DEFAULT true,
    data_hash VARCHAR(64),
    compressed_data BYTEA,
    encryption_key_id UUID,
    UNIQUE(save_game_id, platform, device_id)
);

-- Character-specific data
CREATE TABLE characters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    save_game_id UUID NOT NULL REFERENCES save_games(id) ON DELETE CASCADE,
    character_name VARCHAR(100) NOT NULL,
    character_class VARCHAR(50),
    level INTEGER DEFAULT 1,
    experience_points BIGINT DEFAULT 0,
    health_current INTEGER DEFAULT 100,
    health_max INTEGER DEFAULT 100,
    mana_current INTEGER DEFAULT 50,
    mana_max INTEGER DEFAULT 50,
    stats JSONB,
    inventory JSONB,
    equipment JSONB,
    abilities JSONB,
    appearance JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(save_game_id, character_name)
);

-- Campaign state tracking
CREATE TABLE campaign_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    save_game_id UUID NOT NULL REFERENCES save_games(id) ON DELETE CASCADE,
    chapter_number INTEGER NOT NULL,
    scene_name VARCHAR(100) NOT NULL,
    state_data JSONB NOT NULL,
    flags JSONB DEFAULT '{}',
    variables JSONB DEFAULT '{}',
    completed_quests JSONB DEFAULT '[]',
    active_quests JSONB DEFAULT '[]',
    npc_states JSONB DEFAULT '{}',
    world_state JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(save_game_id, chapter_number, scene_name)
);

-- ========================================
-- Synchronization System
-- ========================================

-- Sync operations log
CREATE TABLE sync_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    save_game_id UUID REFERENCES save_games(id) ON DELETE CASCADE,
    operation_type VARCHAR(20) NOT NULL, -- 'upload', 'download', 'merge', 'resolve'
    source_platform platform_type,
    source_device_id VARCHAR(255),
    target_platform platform_type,
    target_device_id VARCHAR(255),
    sync_version_start BIGINT,
    sync_version_end BIGINT,
    status sync_status DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    bytes_transferred BIGINT DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);

-- Conflict tracking
CREATE TABLE sync_conflicts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    save_game_id UUID NOT NULL REFERENCES save_games(id) ON DELETE CASCADE,
    conflict_type VARCHAR(50) NOT NULL, -- 'data_mismatch', 'version_conflict', 'simultaneous_edit'
    platform_a platform_type NOT NULL,
    device_a VARCHAR(255) NOT NULL,
    platform_b platform_type NOT NULL,
    device_b VARCHAR(255) NOT NULL,
    data_a JSONB NOT NULL,
    data_b JSONB NOT NULL,
    field_path TEXT, -- JSON path to conflicted field
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolution_strategy conflict_resolution,
    resolved_data JSONB,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id),
    is_resolved BOOLEAN DEFAULT false
);

-- Sync tokens for optimistic locking
CREATE TABLE sync_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    save_game_id UUID NOT NULL REFERENCES save_games(id) ON DELETE CASCADE,
    platform platform_type NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    token_value VARCHAR(128) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_revoked BOOLEAN DEFAULT false
);

-- ========================================
-- Asset Management
-- ========================================

-- Game assets stored in S3
CREATE TABLE game_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    save_game_id UUID REFERENCES save_games(id) ON DELETE CASCADE,
    asset_type VARCHAR(50) NOT NULL, -- 'screenshot', 'character_portrait', 'custom_asset'
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    s3_bucket VARCHAR(100) NOT NULL,
    s3_key VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100),
    file_size_bytes BIGINT NOT NULL,
    checksum VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Asset sync status
CREATE TABLE asset_sync_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES game_assets(id) ON DELETE CASCADE,
    platform platform_type NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    sync_status sync_status DEFAULT 'pending',
    local_path VARCHAR(500),
    last_synced TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    UNIQUE(asset_id, platform, device_id)
);

-- ========================================
-- Audit and Analytics
-- ========================================

-- Comprehensive audit log
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL, -- 'save_game', 'character', 'campaign', 'asset'
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    platform platform_type,
    device_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Sync analytics
CREATE TABLE sync_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    platform platform_type NOT NULL,
    total_syncs INTEGER DEFAULT 0,
    successful_syncs INTEGER DEFAULT 0,
    failed_syncs INTEGER DEFAULT 0,
    conflicts_detected INTEGER DEFAULT 0,
    avg_sync_time_ms INTEGER DEFAULT 0,
    total_bytes_synced BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date, platform)
);

-- ========================================
-- Performance Optimization
-- ========================================

-- Indexes for frequently queried fields
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_user_platforms_user_id ON user_platforms(user_id);
CREATE INDEX idx_save_games_user_id ON save_games(user_id);
CREATE INDEX idx_save_games_updated_at ON save_games(updated_at);
CREATE INDEX idx_save_game_data_save_game_id ON save_game_data(save_game_id);
CREATE INDEX idx_save_game_data_platform_device ON save_game_data(platform, device_id);
CREATE INDEX idx_save_game_data_sync_version ON save_game_data(sync_version);
CREATE INDEX idx_characters_save_game_id ON characters(save_game_id);
CREATE INDEX idx_campaign_state_save_game_id ON campaign_state(save_game_id);
CREATE INDEX idx_sync_operations_user_id ON sync_operations(user_id);
CREATE INDEX idx_sync_operations_status ON sync_operations(status);
CREATE INDEX idx_sync_conflicts_user_id ON sync_conflicts(user_id);
CREATE INDEX idx_sync_conflicts_resolved ON sync_conflicts(is_resolved);
CREATE INDEX idx_game_assets_user_id ON game_assets(user_id);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_sync_analytics_user_date ON sync_analytics(user_id, date);

-- GIN indexes for JSONB columns
CREATE INDEX idx_save_game_data_jsonb ON save_game_data USING GIN(data_json);
CREATE INDEX idx_characters_stats ON characters USING GIN(stats);
CREATE INDEX idx_characters_inventory ON characters USING GIN(inventory);
CREATE INDEX idx_campaign_state_state_data ON campaign_state USING GIN(state_data);
CREATE INDEX idx_campaign_state_flags ON campaign_state USING GIN(flags);

-- ========================================
-- Triggers and Functions
-- ========================================

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_save_games_updated_at BEFORE UPDATE ON save_games
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_save_game_data_updated_at BEFORE UPDATE ON save_game_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_characters_updated_at BEFORE UPDATE ON characters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaign_state_updated_at BEFORE UPDATE ON campaign_state
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Audit logging trigger
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (action, resource_type, resource_id, new_values, created_at)
        VALUES ('CREATE', TG_TABLE_NAME, NEW.id, row_to_json(NEW), NOW());
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (action, resource_type, resource_id, old_values, new_values, created_at)
        VALUES ('UPDATE', TG_TABLE_NAME, NEW.id, row_to_json(OLD), row_to_json(NEW), NOW());
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (action, resource_type, resource_id, old_values, created_at)
        VALUES ('DELETE', TG_TABLE_NAME, OLD.id, row_to_json(OLD), NOW());
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to key tables
CREATE TRIGGER audit_save_games AFTER INSERT OR UPDATE OR DELETE ON save_games
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_characters AFTER INSERT OR UPDATE OR DELETE ON characters
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_campaign_state AFTER INSERT OR UPDATE OR DELETE ON campaign_state
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Sync analytics aggregation function
CREATE OR REPLACE FUNCTION update_sync_analytics()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO sync_analytics (user_id, date, platform, total_syncs, successful_syncs, failed_syncs, conflicts_detected)
    VALUES (
        NEW.user_id,
        CURRENT_DATE,
        NEW.source_platform,
        1,
        CASE WHEN NEW.status = 'synced' THEN 1 ELSE 0 END,
        CASE WHEN NEW.status = 'error' THEN 1 ELSE 0 END,
        0
    )
    ON CONFLICT (user_id, date, platform)
    DO UPDATE SET
        total_syncs = sync_analytics.total_syncs + 1,
        successful_syncs = sync_analytics.successful_syncs +
            CASE WHEN NEW.status = 'synced' THEN 1 ELSE 0 END,
        failed_syncs = sync_analytics.failed_syncs +
            CASE WHEN NEW.status = 'error' THEN 1 ELSE 0 END;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_sync_analytics_trigger AFTER INSERT ON sync_operations
    FOR EACH ROW EXECUTE FUNCTION update_sync_analytics();

-- ========================================
-- Views for Common Queries
-- ========================================

-- User save games summary view
CREATE VIEW user_save_games_summary AS
SELECT
    u.id as user_id,
    u.username,
    sg.id as save_game_id,
    sg.campaign_name,
    sg.character_name,
    sg.game_version,
    sg.last_synced,
    sg.sync_status,
    sg.total_playtime_minutes,
    sg.completion_percentage,
    COUNT(DISTINCT ch.id) as character_count,
    MAX(cs.chapter_number) as current_chapter
FROM users u
JOIN save_games sg ON u.id = sg.user_id
LEFT JOIN characters ch ON sg.id = ch.save_game_id
LEFT JOIN campaign_state cs ON sg.id = cs.save_game_id
WHERE sg.is_active = true
GROUP BY u.id, u.username, sg.id, sg.campaign_name, sg.character_name, sg.game_version, sg.last_synced, sg.sync_status, sg.total_playtime_minutes, sg.completion_percentage;

-- Recent sync activity view
CREATE VIEW recent_sync_activity AS
SELECT
    u.username,
    sg.campaign_name,
    so.operation_type,
    so.source_platform,
    so.status,
    so.started_at,
    so.completed_at,
    EXTRACT(EPOCH FROM (so.completed_at - so.started_at)) * 1000 as sync_duration_ms,
    so.bytes_transferred
FROM sync_operations so
JOIN users u ON so.user_id = u.id
LEFT JOIN save_games sg ON so.save_game_id = sg.id
ORDER BY so.started_at DESC;

-- Active conflicts view
CREATE VIEW active_conflicts AS
SELECT
    u.username,
    sg.campaign_name,
    sc.conflict_type,
    sc.platform_a,
    sc.platform_b,
    sc.field_path,
    sc.detected_at,
    sc.resolution_strategy
FROM sync_conflicts sc
JOIN users u ON sc.user_id = u.id
JOIN save_games sg ON sc.save_game_id = sg.id
WHERE sc.is_resolved = false
ORDER BY sc.detected_at DESC;

-- ========================================
-- Security and Cleanup
-- ========================================

-- Function to clean up expired sync tokens
CREATE OR REPLACE FUNCTION cleanup_expired_sync_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sync_tokens WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old audit logs (keep last 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_log WHERE created_at < NOW() - INTERVAL '90 days';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Row Level Security (RLS) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE save_games ENABLE ROW LEVEL SECURITY;
ALTER TABLE characters ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_operations ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_conflicts ENABLE ROW LEVEL SECURITY;
ALTER TABLE game_assets ENABLE ROW LEVEL SECURITY;

-- Users can only access their own data
CREATE POLICY user_data_policy ON users
    FOR ALL TO authenticated_user
    USING (id = current_setting('app.current_user_id')::UUID);

CREATE POLICY save_game_policy ON save_games
    FOR ALL TO authenticated_user
    USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY character_policy ON characters
    FOR ALL TO authenticated_user
    USING (save_game_id IN (
        SELECT id FROM save_games WHERE user_id = current_setting('app.current_user_id')::UUID
    ));

CREATE POLICY campaign_state_policy ON campaign_state
    FOR ALL TO authenticated_user
    USING (save_game_id IN (
        SELECT id FROM save_games WHERE user_id = current_setting('app.current_user_id')::UUID
    ));

CREATE POLICY sync_operations_policy ON sync_operations
    FOR ALL TO authenticated_user
    USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY sync_conflicts_policy ON sync_conflicts
    FOR ALL TO authenticated_user
    USING (user_id = current_setting('app.current_user_id')::UUID);

CREATE POLICY game_assets_policy ON game_assets
    FOR ALL TO authenticated_user
    USING (user_id = current_setting('app.current_user_id')::UUID);

-- ========================================
-- Sample Data for Testing
-- ========================================

-- Note: Remove this section in production
-- This is just for development and testing purposes

-- Sample user (password: 'test123')
INSERT INTO users (username, email, password_hash) VALUES
('testuser', 'test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5e')
ON CONFLICT (email) DO NOTHING;