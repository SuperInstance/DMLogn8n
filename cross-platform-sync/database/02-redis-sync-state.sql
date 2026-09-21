-- Redis Configuration for DMlogn8n Cross-Platform Sync Real-time State Management
-- This file contains Redis data structures and patterns for real-time synchronization

-- ========================================
-- Redis Key Naming Conventions
-- ========================================

/*
Key Patterns:
- sync:user:{user_id}                     - User's sync state
- sync:save:{save_game_id}               - Save game sync state
- sync:device:{user_id}:{platform}:{device_id} - Device sync state
- sync:conflict:{conflict_id}            - Conflict resolution state
- sync:token:{token_value}               - Sync token validation
- ws:session:{session_id}                - WebSocket session
- ws:user:{user_id}                      - User's active sessions
- cache:save:{save_game_id}              - Cached save game data
- lock:save:{save_game_id}               - Distributed lock for save operations
- queue:sync:{priority}                  - Sync operation queues
- metrics:sync:user:{user_id}:date:{date} - Daily sync metrics
*/

-- ========================================
-- Data Structures and Operations
-- ========================================

/*
User Sync State Hash (sync:user:{user_id})
Fields:
- last_sync: timestamp
- sync_version: integer
- status: string (pending/syncing/synced/error)
- active_devices: JSON array of active platforms/devices
- total_saves: integer
- conflict_count: integer
- storage_used_mb: integer
- quota_mb: integer
*/

/*
Save Game Sync State Hash (sync:save:{save_game_id})
Fields:
- owner_id: UUID
- current_version: integer
- last_modified: timestamp
- sync_status: string
- locked_by: device_id (if locked)
- locked_until: timestamp
- conflict_count: integer
- checksum: string
- size_bytes: integer
- platforms_synced: JSON array
*/

/*
Device Sync State Hash (sync:device:{user_id}:{platform}:{device_id})
Fields:
- last_seen: timestamp
- sync_version: integer
- status: string
- pending_uploads: integer
- pending_downloads: integer
- last_error: string (if any)
- battery_level: integer (for mobile)
- network_type: string (wifi/cellular)
- storage_available_mb: integer
*/

/*
WebSocket Session Hash (ws:session:{session_id})
Fields:
- user_id: UUID
- platform: string
- device_id: string
- connected_at: timestamp
- last_ping: timestamp
- subscriptions: JSON array of subscribed save_game_ids
- sync_queue: list of pending operations
*/

/*
Conflict Resolution Hash (sync:conflict:{conflict_id})
Fields:
- user_id: UUID
- save_game_id: UUID
- conflict_type: string
- platform_a: string
- platform_b: string
- data_a: JSON string
- data_b: JSON string
- field_path: string
- resolution_strategy: string
- detected_at: timestamp
- expires_at: timestamp
*/

-- ========================================
-- Lua Scripts for Atomic Operations
-- ========================================

/*

-- 1. Atomic Sync Version Increment
-- KEYS[1]: sync:save:{save_game_id}
-- KEYS[2]: sync:device:{user_id}:{platform}:{device_id}
-- ARGV[1]: user_id
-- ARGV[2]: new_version
-- ARGV[3]: timestamp

local save_key = KEYS[1]
local device_key = KEYS[2]
local user_id = ARGV[1]
local new_version = tonumber(ARGV[2])
local timestamp = ARGV[3]

-- Check if save is locked
local lock_key = "lock:save:" .. string.match(save_key, "sync:save:(.+)")
local lock_owner = redis.call("GET", lock_key)
if lock_owner and lock_owner ~= device_key then
    return {error = "Save is locked by another device"}
end

-- Update save game version
redis.call("HSET", save_key, "current_version", new_version, "last_modified", timestamp)

-- Update device version
redis.call("HSET", device_key, "sync_version", new_version, "last_seen", timestamp)

-- Update user's overall sync state
local user_key = "sync:user:" .. user_id
redis.call("HINCRBY", user_key, "sync_version", 1)
redis.call("HSET", user_key, "last_sync", timestamp)

return {success = true, version = new_version}
*/

/*

-- 2. Conflict Detection and Creation
-- KEYS[1]: sync:save:{save_game_id}
-- KEYS[2]: sync:device:{user_id}:{platform_a}:{device_id}
-- KEYS[3]: sync:device:{user_id}:{platform_b}:{device_id}
-- ARGV[1]: conflict_id
-- ARGV[2]: conflict_data_a (JSON)
-- ARGV[3]: conflict_data_b (JSON)
-- ARGV[4]: field_path
-- ARGV[5]: conflict_type

local save_key = KEYS[1]
local device_a_key = KEYS[2]
local device_b_key = KEYS[3]
local conflict_id = ARGV[1]
local data_a = ARGV[2]
local data_b = ARGV[3]
local field_path = ARGV[4]
local conflict_type = ARGV[5]

-- Extract user_id from device key
local user_id = string.match(device_a_key, "sync:device:([^:]+):")

-- Create conflict record
local conflict_key = "sync:conflict:" .. conflict_id
redis.call("HMSET", conflict_key,
    "user_id", user_id,
    "save_game_id", string.match(save_key, "sync:save:(.+)"),
    "conflict_type", conflict_type,
    "platform_a", string.match(device_a_key, "sync:device:[^:]+:([^:]+):"),
    "platform_b", string.match(device_b_key, "sync:device:[^:]+:([^:]+):"),
    "data_a", data_a,
    "data_b", data_b,
    "field_path", field_path,
    "detected_at", tostring(redis.call("TIME")[1]),
    "expires_at", tostring(tonumber(redis.call("TIME")[1]) + 86400) -- 24 hours
)

-- Increment conflict counts
redis.call("HINCRBY", save_key, "conflict_count", 1)
redis.call("HINCRBY", "sync:user:" .. user_id, "conflict_count", 1)

-- Mark both devices as having conflicts
redis.call("HSET", device_a_key, "status", "conflict")
redis.call("HSET", device_b_key, "status", "conflict")

-- Notify via pub/sub
redis.call("PUBLISH", "conflict:" .. user_id, conflict_id)

return {success = true, conflict_id = conflict_id}
*/

/*

-- 3. Distributed Lock Acquisition
-- KEYS[1]: lock:save:{save_game_id}
-- ARGV[1]: device_id
-- ARGV[2]: timeout_seconds
-- ARGV[3]: current_timestamp

local lock_key = KEYS[1]
local device_id = ARGV[1]
local timeout = tonumber(ARGV[2])
local current_time = tonumber(ARGV[3])

-- Check if lock exists and is not expired
local existing_lock = redis.call("GET", lock_key)
if existing_lock then
    local lock_data = redis.call("HGETALL", "lock_data:" .. existing_lock)
    if lock_data and #lock_data > 0 then
        local expires_at = tonumber(lock_data[4]) -- expires_at field
        if expires_at > current_time then
            return {success = false, reason = "Lock already held"}
        end
    end
end

-- Acquire lock
local lock_id = device_id .. ":" .. current_time
redis.call("SET", lock_key, lock_id, "EX", timeout)

-- Store lock metadata
redis.call("HMSET", "lock_data:" .. lock_id,
    "device_id", device_id,
    "acquired_at", current_time,
    "expires_at", current_time + timeout
)

return {success = true, lock_id = lock_id, expires_at = current_time + timeout}
*/

/*

-- 4. WebSocket Session Management
-- KEYS[1]: ws:session:{session_id}
-- KEYS[2]: ws:user:{user_id}
-- ARGV[1]: user_id
-- ARGV[2]: platform
-- ARGV[3]: device_id
-- ARGV[4]: timestamp

local session_key = KEYS[1]
local user_sessions_key = KEYS[2]
local user_id = ARGV[1]
local platform = ARGV[2]
local device_id = ARGV[3]
local timestamp = ARGV[4]

local session_id = string.match(session_key, "ws:session:(.+)")

-- Create session record
redis.call("HMSET", session_key,
    "user_id", user_id,
    "platform", platform,
    "device_id", device_id,
    "connected_at", timestamp,
    "last_ping", timestamp,
    "subscriptions", "[]",
    "sync_queue", "[]"
)

-- Add to user's active sessions
redis.call("SADD", user_sessions_key, session_id)

-- Set session expiration
redis.call("EXPIRE", session_key, 3600) -- 1 hour

return {success = true, session_id = session_id}
*/

-- ========================================
-- Pub/Sub Channels
-- ========================================

/*
Channel Patterns:
- sync:user:{user_id}                     - User-specific sync notifications
- sync:save:{save_game_id}               - Save game-specific notifications
- conflict:user:{user_id}                - Conflict notifications
- ws:heartbeat:{session_id}              - WebSocket heartbeat
- platform:{platform}:updates            - Platform-specific updates
- system:sync:status                     - System-wide sync status
*/

-- ========================================
-- Sorted Sets for Time Series Data
-- ========================================

/*
sync_metrics:daily:{user_id} - Sorted set with timestamp as score
Members: JSON strings containing daily sync metrics
TTL: 90 days

sync_operations:pending - Priority queue for sync operations
Score: priority (lower = higher priority)
Member: JSON operation data

device_activity:{user_id} - Sorted set tracking device activity
Score: timestamp
Member: device_id
TTL: 7 days
*/

-- ========================================
-- Configuration and Setup
-- ========================================

/*
Redis Configuration Recommendations:

# Memory Settings
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Network
timeout 300
tcp-keepalive 300

# Security
requirepass your_secure_password
rename-command FLUSHDB ""
rename-command FLUSHALL ""

# Notifications
notify-keyspace-events Ex

# Clients
maxclients 10000

# Memory Optimization
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
*/

-- ========================================
-- Monitoring and Health Checks
-- ========================================

/*
Health Check Keys:
- health:redis:timestamp - Last health check timestamp
- health:redis:status - Overall system status
- health:redis:active_users - Number of active users
- health:redis:active_sessions - Number of active WebSocket sessions
- health:redis:pending_syncs - Number of pending sync operations
- health:redis:active_conflicts - Number of active conflicts

Monitoring Commands:
INFO memory
INFO stats
INFO clients
INFO persistence
SLOWLOG GET 10
CLIENT LIST
*/

-- ========================================
-- Example Redis CLI Commands for Testing
-- ========================================

/*
# Set user sync state
HSET sync:user:123e4567-e89b-12d3-a456-426614174000 \
    last_sync "2024-01-15T10:30:00Z" \
    sync_version 42 \
    status "synced" \
    active_devices '["web:desktop1", "mobile:phone1"]' \
    total_saves 5 \
    conflict_count 0

# Set save game sync state
HSET sync:save:456e7890-e12b-34d5-a678-901234567890 \
    owner_id "123e4567-e89b-12d3-a456-426614174000" \
    current_version 42 \
    last_modified "2024-01-15T10:30:00Z" \
    sync_status "synced" \
    checksum "abc123def456" \
    size_bytes 1024000

# Create WebSocket session
HMSET ws:session:session_abc123 \
    user_id "123e4567-e89b-12d3-a456-426614174000" \
    platform "web" \
    device_id "desktop1" \
    connected_at "2024-01-15T10:30:00Z" \
    last_ping "2024-01-15T10:35:00Z"

# Add session to user's active sessions
SADD ws:user:123e4567-e89b-12d3-a456-426614174000 session_abc123

# Publish sync notification
PUBLISH sync:user:123e4567-e89b-12d3-a456-426614174000 '{"type":"sync_complete","save_id":"456e7890-e12b-34d5-a678-901234567890"}'

# Create distributed lock
SET lock:save:456e7890-e12b-34d5-a678-901234567890 web:desktop1:1642248600 EX 30

# Monitor Redis operations
MONITOR
INFO stats
SLOWLOG GET 10
*/