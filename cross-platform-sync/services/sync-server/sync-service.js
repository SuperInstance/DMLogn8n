/**
 * DMlogn8n Cross-Platform Sync Service
 * Core synchronization logic for save games across multiple platforms
 */

const { Pool } = require('pg');
const Redis = require('ioredis');
const AWS = require('aws-sdk');
const crypto = require('crypto');
const zlib = require('zlib');
const { promisify } = require('util');

const gzip = promisify(zlib.gzip);
const gunzip = promisify(zlib.gunzip);

class SyncService {
    constructor(config = {}) {
        this.config = {
            database: {
                host: config.database?.host || process.env.DB_HOST,
                port: config.database?.port || process.env.DB_PORT || 5432,
                database: config.database?.database || process.env.DB_NAME,
                user: config.database?.user || process.env.DB_USER,
                password: config.database?.password || process.env.DB_PASSWORD,
                ssl: config.database?.ssl || false,
                max: config.database?.maxConnections || 20
            },
            redis: {
                host: config.redis?.host || process.env.REDIS_HOST,
                port: config.redis?.port || process.env.REDIS_PORT || 6379,
                password: config.redis?.password || process.env.REDIS_PASSWORD,
                db: config.redis?.db || 0
            },
            aws: {
                accessKeyId: config.aws?.accessKeyId || process.env.AWS_ACCESS_KEY_ID,
                secretAccessKey: config.aws?.secretAccessKey || process.env.AWS_SECRET_ACCESS_KEY,
                region: config.aws?.region || process.env.AWS_REGION || 'us-east-1',
                s3Bucket: config.aws?.s3Bucket || process.env.AWS_S3_BUCKET
            },
            sync: {
                maxRetries: config.sync?.maxRetries || 3,
                retryDelay: config.sync?.retryDelay || 1000,
                compressionThreshold: config.sync?.compressionThreshold || 10240,
                encryptionEnabled: config.sync?.encryptionEnabled || false,
                maxFileSize: config.sync?.maxFileSize || 100 * 1024 * 1024 // 100MB
            }
        };

        // Initialize database connections
        this.pool = new Pool(this.config.database);
        this.redis = new Redis(this.config.redis);

        // Initialize AWS S3
        this.s3 = new AWS.S3({
            accessKeyId: this.config.aws.accessKeyId,
            secretAccessKey: this.config.aws.secretAccessKey,
            region: this.config.aws.region
        });

        // Sync operation queue
        this.syncQueue = [];
        this.processingSync = false;

        // Metrics
        this.metrics = {
            syncOperations: 0,
            conflictsDetected: 0,
            conflictsResolved: 0,
            bytesTransferred: 0,
            averageSyncTime: 0,
            errorCount: 0
        };
    }

    /**
     * Initialize the sync service
     */
    async initialize() {
        try {
            // Test database connection
            await this.pool.query('SELECT NOW()');
            console.log('Database connection established');

            // Test Redis connection
            await this.redis.ping();
            console.log('Redis connection established');

            // Start processing sync queue
            this.startSyncQueueProcessor();

            // Start metrics collection
            this.startMetricsCollection();

            console.log('Sync Service initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Sync Service:', error);
            throw error;
        }
    }

    /**
     * Synchronize save game data from a platform
     */
    async syncSaveGame(userId, saveGameId, platform, deviceId, gameData, options = {}) {
        const startTime = Date.now();
        let syncOperation;

        try {
            // Create sync operation record
            syncOperation = await this.createSyncOperation({
                userId,
                saveGameId,
                operationType: 'upload',
                sourcePlatform: platform,
                sourceDeviceId: deviceId,
                status: 'syncing'
            });

            // Validate input data
            await this.validateSyncData(userId, saveGameId, gameData);

            // Get current save state
            const currentState = await this.getSaveGameState(saveGameId);

            // Check for conflicts
            const conflict = await this.detectConflicts(currentState, gameData, platform, deviceId);

            if (conflict) {
                await this.handleConflict(syncOperation.id, conflict);
                this.metrics.conflictsDetected++;
                return {
                    success: false,
                    conflict: conflict.id,
                    message: 'Conflict detected, resolution required'
                };
            }

            // Process the sync
            const result = await this.processSync(
                userId,
                saveGameId,
                platform,
                deviceId,
                gameData,
                currentState,
                options
            );

            // Update sync operation
            await this.updateSyncOperation(syncOperation.id, {
                status: 'synced',
                syncVersionEnd: result.newVersion,
                bytesTransferred: result.bytesTransferred,
                completedAt: new Date()
            });

            // Update metrics
            this.updateMetrics(startTime, result.bytesTransferred);

            // Notify other platforms
            await this.notifyPlatformSync(userId, saveGameId, platform, result.newVersion);

            return {
                success: true,
                version: result.newVersion,
                timestamp: new Date().toISOString(),
                bytesTransferred: result.bytesTransferred
            };

        } catch (error) {
            console.error('Sync operation failed:', error);

            if (syncOperation) {
                await this.updateSyncOperation(syncOperation.id, {
                    status: 'error',
                    errorMessage: error.message,
                    completedAt: new Date()
                });
            }

            this.metrics.errorCount++;
            throw error;
        }
    }

    /**
     * Get save game data for a platform
     */
    async getSaveGame(userId, saveGameId, platform, deviceId, lastSyncVersion = null) {
        try {
            // Check if user has access to this save game
            const saveGame = await this.getSaveGameAccess(userId, saveGameId);
            if (!saveGame) {
                throw new Error('Save game not found or access denied');
            }

            // Get current sync state
            const syncState = await this.redis.hgetall(`sync:save:${saveGameId}`);

            if (!syncState.current_version) {
                throw new Error('Save game not synchronized');
            }

            const currentVersion = parseInt(syncState.current_version);

            // Check if client needs update
            if (lastSyncVersion && lastSyncVersion >= currentVersion) {
                return {
                    upToDate: true,
                    version: currentVersion,
                    timestamp: syncState.last_modified
                };
            }

            // Get the latest save data
            let saveData;

            // Try Redis first
            const cachedData = await this.redis.get(`sync:data:${saveGameId}:${currentVersion}`);
            if (cachedData) {
                saveData = JSON.parse(cachedData);
            } else {
                // Fallback to database
                saveData = await this.getSaveDataFromDB(saveGameId, currentVersion);
            }

            // Update device sync state
            await this.updateDeviceSyncState(userId, platform, deviceId, currentVersion);

            return {
                upToDate: false,
                version: currentVersion,
                timestamp: syncState.last_modified,
                data: saveData,
                checksum: syncState.checksum
            };

        } catch (error) {
            console.error('Failed to get save game:', error);
            throw error;
        }
    }

    /**
     * Create a new save game
     */
    async createSaveGame(userId, campaignName, gameData, platform, deviceId) {
        const client = await this.pool.connect();

        try {
            await client.query('BEGIN');

            // Create save game record
            const saveGameResult = await client.query(`
                INSERT INTO save_games (user_id, campaign_name, game_version, sync_status)
                VALUES ($1, $2, $3, 'synced')
                RETURNING id, created_at, updated_at
            `, [userId, campaignName, gameData.gameVersion || '1.0.0']);

            const saveGame = saveGameResult.rows[0];

            // Extract character and campaign data
            if (gameData.characters) {
                for (const character of gameData.characters) {
                    await client.query(`
                        INSERT INTO characters (
                            save_game_id, character_name, character_class, level,
                            experience_points, health_current, health_max,
                            mana_current, mana_max, stats, inventory,
                            equipment, abilities, appearance
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    `, [
                        saveGame.id,
                        character.name,
                        character.class || null,
                        character.level || 1,
                        character.experiencePoints || 0,
                        character.health?.current || 100,
                        character.health?.max || 100,
                        character.mana?.current || 50,
                        character.mana?.max || 50,
                        JSON.stringify(character.stats || {}),
                        JSON.stringify(character.inventory || []),
                        JSON.stringify(character.equipment || []),
                        JSON.stringify(character.abilities || []),
                        JSON.stringify(character.appearance || {})
                    ]);
                }
            }

            if (gameData.campaignState) {
                await client.query(`
                    INSERT INTO campaign_state (
                        save_game_id, chapter_number, scene_name, state_data,
                        flags, variables, completed_quests, active_quests,
                        npc_states, world_state
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                `, [
                    saveGame.id,
                    gameData.campaignState.chapter || 1,
                    gameData.campaignState.scene || 'start',
                    JSON.stringify(gameData.campaignState.state || {}),
                    JSON.stringify(gameData.campaignState.flags || {}),
                    JSON.stringify(gameData.campaignState.variables || {}),
                    JSON.stringify(gameData.campaignState.completedQuests || []),
                    JSON.stringify(gameData.campaignState.activeQuests || []),
                    JSON.stringify(gameData.campaignState.npcStates || {}),
                    JSON.stringify(gameData.campaignState.worldState || {})
                ]);
            }

            // Store save game data
            const dataHash = this.calculateDataHash(gameData);
            const compressedData = await this.compressData(gameData);

            await client.query(`
                INSERT INTO save_game_data (
                    save_game_id, platform, device_id, data_json, sync_version,
                    is_current, data_hash, compressed_data
                ) VALUES ($1, $2, $3, $4, 1, true, $5, $6)
            `, [saveGame.id, platform, deviceId, JSON.stringify(gameData), dataHash, compressedData]);

            // Initialize sync state in Redis
            await this.redis.hmset(`sync:save:${saveGame.id}`, {
                current_version: 1,
                last_modified: new Date().toISOString(),
                checksum: dataHash,
                sync_status: 'synced'
            });

            await client.query('COMMIT');

            return {
                success: true,
                saveGameId: saveGame.id,
                version: 1,
                timestamp: saveGame.created_at
            };

        } catch (error) {
            await client.query('ROLLBACK');
            console.error('Failed to create save game:', error);
            throw error;
        } finally {
            client.release();
        }
    }

    /**
     * Resolve a conflict between platforms
     */
    async resolveConflict(userId, conflictId, resolution, resolvedBy = null) {
        try {
            // Get conflict details
            const conflict = await this.getConflict(conflictId);
            if (!conflict) {
                throw new Error('Conflict not found');
            }

            // Verify user ownership
            if (conflict.userId !== userId) {
                throw new Error('Access denied');
            }

            let resolvedData;

            // Apply resolution strategy
            switch (resolution.strategy) {
                case 'use_platform_a':
                    resolvedData = conflict.dataA;
                    break;
                case 'use_platform_b':
                    resolvedData = conflict.dataB;
                    break;
                case 'merge':
                    resolvedData = await this.mergeGameData(conflict.dataA, conflict.dataB, resolution.mergeRules);
                    break;
                case 'custom':
                    resolvedData = resolution.customData;
                    break;
                default:
                    throw new Error('Unknown resolution strategy');
            }

            // Get current sync state
            const syncState = await this.redis.hgetall(`sync:save:${conflict.saveGameId}`);
            const newVersion = parseInt(syncState.current_version) + 1;

            // Store resolved data
            const dataHash = this.calculateDataHash(resolvedData);
            const compressedData = await this.compressData(resolvedData);

            // Update database
            const client = await this.pool.connect();
            try {
                await client.query('BEGIN');

                // Create new save data version
                await client.query(`
                    UPDATE save_game_data
                    SET is_current = false
                    WHERE save_game_id = $1
                `, [conflict.saveGameId]);

                await client.query(`
                    INSERT INTO save_game_data (
                        save_game_id, platform, device_id, data_json, sync_version,
                        is_current, data_hash, compressed_data
                    ) VALUES ($1, $2, $3, $4, $5, true, $6, $7)
                `, [
                    conflict.saveGameId,
                    'resolved',
                    'conflict_resolution',
                    JSON.stringify(resolvedData),
                    newVersion,
                    dataHash,
                    compressedData
                ]);

                // Update conflict record
                await client.query(`
                    UPDATE sync_conflicts
                    SET resolution_strategy = $1,
                        resolved_data = $2,
                        resolved_at = NOW(),
                        resolved_by = $3,
                        is_resolved = true
                    WHERE id = $4
                `, [resolution.strategy, JSON.stringify(resolvedData), resolvedBy, conflictId]);

                await client.query('COMMIT');
            } finally {
                client.release();
            }

            // Update Redis sync state
            await this.redis.hmset(`sync:save:${conflict.saveGameId}`, {
                current_version: newVersion,
                last_modified: new Date().toISOString(),
                checksum: dataHash
            });

            // Clear conflict from Redis
            await this.redis.del(`sync:conflict:${conflictId}`);

            // Update metrics
            this.metrics.conflictsResolved++;

            // Notify all platforms
            await this.notifyConflictResolved(conflict.saveGameId, conflictId, newVersion);

            return {
                success: true,
                version: newVersion,
                timestamp: new Date().toISOString()
            };

        } catch (error) {
            console.error('Failed to resolve conflict:', error);
            throw error;
        }
    }

    /**
     * Get sync history for a save game
     */
    async getSyncHistory(userId, saveGameId, limit = 50, offset = 0) {
        try {
            // Verify access
            const saveGame = await this.getSaveGameAccess(userId, saveGameId);
            if (!saveGame) {
                throw new Error('Save game not found or access denied');
            }

            const result = await this.pool.query(`
                SELECT
                    so.id,
                    so.operation_type,
                    so.source_platform,
                    so.source_device_id,
                    so.status,
                    so.started_at,
                    so.completed_at,
                    so.sync_version_start,
                    so.sync_version_end,
                    so.bytes_transferred,
                    so.error_message
                FROM sync_operations so
                WHERE so.user_id = $1 AND so.save_game_id = $2
                ORDER BY so.started_at DESC
                LIMIT $3 OFFSET $4
            `, [userId, saveGameId, limit, offset]);

            return {
                history: result.rows,
                total: result.rowCount
            };

        } catch (error) {
            console.error('Failed to get sync history:', error);
            throw error;
        }
    }

    /**
     * Get active conflicts for a user
     */
    async getActiveConflicts(userId) {
        try {
            const result = await this.pool.query(`
                SELECT
                    sc.id,
                    sc.conflict_type,
                    sc.platform_a,
                    sc.platform_b,
                    sc.field_path,
                    sc.detected_at,
                    sg.campaign_name
                FROM sync_conflicts sc
                JOIN save_games sg ON sc.save_game_id = sg.id
                WHERE sc.user_id = $1 AND sc.is_resolved = false
                ORDER BY sc.detected_at DESC
            `, [userId]);

            return result.rows;

        } catch (error) {
            console.error('Failed to get active conflicts:', error);
            throw error;
        }
    }

    /**
     * Delete a save game and all associated data
     */
    async deleteSaveGame(userId, saveGameId) {
        const client = await this.pool.connect();

        try {
            await client.query('BEGIN');

            // Verify ownership
            const saveGame = await client.query(
                'SELECT id FROM save_games WHERE id = $1 AND user_id = $2',
                [saveGameId, userId]
            );

            if (saveGame.rowCount === 0) {
                throw new Error('Save game not found or access denied');
            }

            // Delete in proper order (respecting foreign keys)
            await client.query('DELETE FROM save_game_data WHERE save_game_id = $1', [saveGameId]);
            await client.query('DELETE FROM campaign_state WHERE save_game_id = $1', [saveGameId]);
            await client.query('DELETE FROM characters WHERE save_game_id = $1', [saveGameId]);
            await client.query('DELETE FROM sync_operations WHERE save_game_id = $1', [saveGameId]);
            await client.query('DELETE FROM sync_conflicts WHERE save_game_id = $1', [saveGameId]);
            await client.query('DELETE FROM game_assets WHERE save_game_id = $1', [saveGameId]);
            await client.query('DELETE FROM save_games WHERE id = $1', [saveGameId]);

            // Cleanup Redis
            await this.redis.del(`sync:save:${saveGameId}`);

            const keys = await this.redis.keys(`sync:data:${saveGameId}:*`);
            if (keys.length > 0) {
                await this.redis.del(...keys);
            }

            await client.query('COMMIT');

            return { success: true };

        } catch (error) {
            await client.query('ROLLBACK');
            console.error('Failed to delete save game:', error);
            throw error;
        } finally {
            client.release();
        }
    }

    /**
     * Private helper methods
     */

    async createSyncOperation(data) {
        const result = await this.pool.query(`
            INSERT INTO sync_operations (
                user_id, save_game_id, operation_type, source_platform,
                source_device_id, sync_version_start, status, started_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            RETURNING id, sync_version_start
        `, [
            data.userId,
            data.saveGameId,
            data.operationType,
            data.sourcePlatform,
            data.sourceDeviceId,
            data.syncVersionStart || 0,
            data.status
        ]);

        return {
            id: result.rows[0].id,
            syncVersionStart: result.rows[0].sync_version_start
        };
    }

    async updateSyncOperation(operationId, data) {
        const setClause = [];
        const values = [];
        let paramIndex = 1;

        Object.keys(data).forEach(key => {
            setClause.push(`${key} = $${paramIndex}`);
            values.push(data[key]);
            paramIndex++;
        });

        values.push(operationId);

        await this.pool.query(`
            UPDATE sync_operations
            SET ${setClause.join(', ')}
            WHERE id = $${paramIndex}
        `, values);
    }

    async validateSyncData(userId, saveGameId, gameData) {
        // Check file size
        const dataSize = JSON.stringify(gameData).length;
        if (dataSize > this.config.sync.maxFileSize) {
            throw new Error(`Save data too large: ${dataSize} bytes`);
        }

        // Verify user access
        const access = await this.getSaveGameAccess(userId, saveGameId);
        if (!access) {
            throw new Error('Access denied to save game');
        }

        // Validate data structure
        if (!gameData || typeof gameData !== 'object') {
            throw new Error('Invalid save data format');
        }

        return true;
    }

    async getSaveGameState(saveGameId) {
        const state = await this.redis.hgetall(`sync:save:${saveGameId}`);

        if (!state.current_version) {
            // Fallback to database
            const result = await this.pool.query(`
                SELECT
                    sg.sync_status,
                    sg.last_synced,
                    sgd.sync_version,
                    sgd.data_hash
                FROM save_games sg
                JOIN save_game_data sgd ON sg.id = sgd.save_game_id
                WHERE sg.id = $1 AND sgd.is_current = true
            `, [saveGameId]);

            if (result.rowCount > 0) {
                const row = result.rows[0];
                return {
                    version: row.sync_version,
                    status: row.sync_status,
                    lastModified: row.last_synced,
                    checksum: row.data_hash
                };
            }
        }

        return {
            version: parseInt(state.current_version) || 0,
            status: state.sync_status || 'unknown',
            lastModified: state.last_modified,
            checksum: state.checksum
        };
    }

    async detectConflicts(currentState, newData, platform, deviceId) {
        const newChecksum = this.calculateDataHash(newData);

        if (currentState.checksum && currentState.checksum !== newChecksum) {
            // Potential conflict detected
            const conflictId = crypto.randomUUID();

            await this.redis.hmset(`sync:conflict:${conflictId}`, {
                user_id: newData.userId,
                save_game_id: newData.saveGameId,
                conflict_type: 'data_mismatch',
                platform_a: platform,
                device_a: deviceId,
                platform_b: 'existing',
                data_a: JSON.stringify(newData),
                detected_at: new Date().toISOString(),
                expires_at: new Date(Date.now() + 86400000).toISOString()
            });

            return { id: conflictId, type: 'data_mismatch' };
        }

        return null;
    }

    async processSync(userId, saveGameId, platform, deviceId, gameData, currentState, options) {
        const client = await this.pool.connect();

        try {
            await client.query('BEGIN');

            const newVersion = currentState.version + 1;
            const dataHash = this.calculateDataHash(gameData);
            const compressedData = await this.compressData(gameData);

            // Update save game record
            await client.query(`
                UPDATE save_games
                SET updated_at = NOW(), last_synced = NOW(), sync_status = 'synced'
                WHERE id = $1
            `, [saveGameId]);

            // Mark previous version as not current
            await client.query(`
                UPDATE save_game_data
                SET is_current = false
                WHERE save_game_id = $1
            `, [saveGameId]);

            // Insert new version
            await client.query(`
                INSERT INTO save_game_data (
                    save_game_id, platform, device_id, data_json, sync_version,
                    is_current, data_hash, compressed_data
                ) VALUES ($1, $2, $3, $4, $5, true, $6, $7)
            `, [saveGameId, platform, deviceId, JSON.stringify(gameData), newVersion, dataHash, compressedData]);

            // Update structured data if provided
            if (gameData.characters) {
                await this.updateCharacterData(client, saveGameId, gameData.characters);
            }

            if (gameData.campaignState) {
                await this.updateCampaignState(client, saveGameId, gameData.campaignState);
            }

            await client.query('COMMIT');

            // Update Redis
            await this.redis.hmset(`sync:save:${saveGameId}`, {
                current_version: newVersion,
                last_modified: new Date().toISOString(),
                checksum: dataHash,
                sync_status: 'synced'
            });

            // Cache data in Redis
            await this.redis.setex(
                `sync:data:${saveGameId}:${newVersion}`,
                86400, // 24 hours
                JSON.stringify(gameData)
            );

            return {
                newVersion,
                bytesTransferred: compressedData.length
            };

        } catch (error) {
            await client.query('ROLLBACK');
            throw error;
        } finally {
            client.release();
        }
    }

    async updateCharacterData(client, saveGameId, characters) {
        for (const character of characters) {
            await client.query(`
                INSERT INTO characters (
                    save_game_id, character_name, character_class, level,
                    experience_points, health_current, health_max,
                    mana_current, mana_max, stats, inventory,
                    equipment, abilities, appearance
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (save_game_id, character_name)
                DO UPDATE SET
                    character_class = EXCLUDED.character_class,
                    level = EXCLUDED.level,
                    experience_points = EXCLUDED.experience_points,
                    health_current = EXCLUDED.health_current,
                    health_max = EXCLUDED.health_max,
                    mana_current = EXCLUDED.mana_current,
                    mana_max = EXCLUDED.mana_max,
                    stats = EXCLUDED.stats,
                    inventory = EXCLUDED.inventory,
                    equipment = EXCLUDED.equipment,
                    abilities = EXCLUDED.abilities,
                    appearance = EXCLUDED.appearance,
                    updated_at = NOW()
            `, [
                saveGameId,
                character.name,
                character.class || null,
                character.level || 1,
                character.experiencePoints || 0,
                character.health?.current || 100,
                character.health?.max || 100,
                character.mana?.current || 50,
                character.mana?.max || 50,
                JSON.stringify(character.stats || {}),
                JSON.stringify(character.inventory || []),
                JSON.stringify(character.equipment || []),
                JSON.stringify(character.abilities || []),
                JSON.stringify(character.appearance || {})
            ]);
        }
    }

    async updateCampaignState(client, saveGameId, campaignState) {
        await client.query(`
            INSERT INTO campaign_state (
                save_game_id, chapter_number, scene_name, state_data,
                flags, variables, completed_quests, active_quests,
                npc_states, world_state
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (save_game_id, chapter_number, scene_name)
            DO UPDATE SET
                state_data = EXCLUDED.state_data,
                flags = EXCLUDED.flags,
                variables = EXCLUDED.variables,
                completed_quests = EXCLUDED.completed_quests,
                active_quests = EXCLUDED.active_quests,
                npc_states = EXCLUDED.npc_states,
                world_state = EXCLUDED.world_state,
                updated_at = NOW()
        `, [
            saveGameId,
            campaignState.chapter || 1,
            campaignState.scene || 'start',
            JSON.stringify(campaignState.state || {}),
            JSON.stringify(campaignState.flags || {}),
            JSON.stringify(campaignState.variables || {}),
            JSON.stringify(campaignState.completedQuests || []),
            JSON.stringify(campaignState.activeQuests || []),
            JSON.stringify(campaignState.npcStates || {}),
            JSON.stringify(campaignState.worldState || {})
        ]);
    }

    async updateDeviceSyncState(userId, platform, deviceId, version) {
        const deviceKey = `sync:device:${userId}:${platform}:${deviceId}`;

        await this.redis.hmset(deviceKey, {
            sync_version: version,
            last_seen: new Date().toISOString(),
            status: 'synced'
        });

        await this.redis.expire(deviceKey, 86400 * 7); // 7 days
    }

    async getSaveGameAccess(userId, saveGameId) {
        const result = await this.pool.query(
            'SELECT id FROM save_games WHERE id = $1 AND user_id = $2',
            [saveGameId, userId]
        );

        return result.rowCount > 0;
    }

    async getSaveDataFromDB(saveGameId, version) {
        const result = await this.pool.query(`
            SELECT data_json, compressed_data
            FROM save_game_data
            WHERE save_game_id = $1 AND sync_version = $2
        `, [saveGameId, version]);

        if (result.rowCount === 0) {
            throw new Error(`Save data not found for version ${version}`);
        }

        const row = result.rows[0];

        if (row.compressed_data) {
            const decompressed = await gunzip(row.compressed_data);
            return JSON.parse(decompressed.toString());
        } else {
            return JSON.parse(row.data_json);
        }
    }

    async getConflict(conflictId) {
        const result = await this.pool.query(`
            SELECT
                sc.*,
                sg.campaign_name
            FROM sync_conflicts sc
            JOIN save_games sg ON sc.save_game_id = sg.id
            WHERE sc.id = $1
        `, [conflictId]);

        if (result.rowCount === 0) {
            return null;
        }

        const conflict = result.rows[0];
        return {
            id: conflict.id,
            userId: conflict.user_id,
            saveGameId: conflict.save_game_id,
            campaignName: conflict.campaign_name,
            conflictType: conflict.conflict_type,
            platformA: conflict.platform_a,
            platformB: conflict.platform_b,
            dataA: conflict.data_a ? JSON.parse(conflict.data_a) : null,
            dataB: conflict.data_b ? JSON.parse(conflict.data_b) : null,
            fieldPath: conflict.field_path,
            detectedAt: conflict.detected_at
        };
    }

    async mergeGameData(dataA, dataB, mergeRules = {}) {
        // Simple merge strategy - can be enhanced based on game-specific requirements
        const merged = { ...dataA };

        // Merge characters
        if (dataA.characters && dataB.characters) {
            merged.characters = dataA.characters.map(charA => {
                const charB = dataB.characters.find(c => c.name === charA.name);
                if (charB) {
                    // Merge character data, preferring newer timestamps
                    return {
                        ...charA,
                        ...charB,
                        experiencePoints: Math.max(charA.experiencePoints || 0, charB.experiencePoints || 0),
                        level: Math.max(charA.level || 1, charB.level || 1)
                    };
                }
                return charA;
            });

            // Add characters from B that don't exist in A
            dataB.characters.forEach(charB => {
                if (!merged.characters.find(c => c.name === charB.name)) {
                    merged.characters.push(charB);
                }
            });
        }

        // Merge campaign state
        if (dataA.campaignState && dataB.campaignState) {
            merged.campaignState = {
                ...dataA.campaignState,
                ...dataB.campaignState,
                chapter: Math.max(dataA.campaignState.chapter || 1, dataB.campaignState.chapter || 1),
                // Merge flags
                flags: { ...dataA.campaignState.flags, ...dataB.campaignState.flags },
                // Merge variables
                variables: { ...dataA.campaignState.variables, ...dataB.campaignState.variables },
                // Merge quests (union of both)
                completedQuests: [...new Set([
                    ...(dataA.campaignState.completedQuests || []),
                    ...(dataB.campaignState.completedQuests || [])
                ])],
                activeQuests: [...new Set([
                    ...(dataA.campaignState.activeQuests || []),
                    ...(dataB.campaignState.activeQuests || [])
                ])]
            };
        }

        return merged;
    }

    calculateDataHash(data) {
        const dataString = JSON.stringify(data, Object.keys(data).sort());
        return crypto.createHash('sha256').update(dataString).digest('hex');
    }

    async compressData(data) {
        const jsonString = JSON.stringify(data);

        if (jsonString.length < this.config.sync.compressionThreshold) {
            return null;
        }

        return await gzip(jsonString);
    }

    async notifyPlatformSync(userId, saveGameId, platform, version) {
        const notification = {
            type: 'save_updated',
            saveGameId,
            platform,
            version,
            timestamp: new Date().toISOString()
        };

        await this.redis.publish(`sync:user:${userId}`, JSON.stringify(notification));
        await this.redis.publish(`sync:save:${saveGameId}`, JSON.stringify(notification));
    }

    async notifyConflictResolved(saveGameId, conflictId, version) {
        const notification = {
            type: 'conflict_resolved',
            saveGameId,
            conflictId,
            version,
            timestamp: new Date().toISOString()
        };

        await this.redis.publish(`sync:save:${saveGameId}`, JSON.stringify(notification));
    }

    updateMetrics(startTime, bytesTransferred) {
        const duration = Date.now() - startTime;

        this.metrics.syncOperations++;
        this.metrics.bytesTransferred += bytesTransferred;

        // Update average sync time
        this.metrics.averageSyncTime =
            (this.metrics.averageSyncTime * (this.metrics.syncOperations - 1) + duration) /
            this.metrics.syncOperations;
    }

    startSyncQueueProcessor() {
        setInterval(async () => {
            if (this.syncQueue.length > 0 && !this.processingSync) {
                this.processingSync = true;

                while (this.syncQueue.length > 0) {
                    const syncTask = this.syncQueue.shift();
                    try {
                        await this.processSyncTask(syncTask);
                    } catch (error) {
                        console.error('Sync task failed:', error);
                    }
                }

                this.processingSync = false;
            }
        }, 1000);
    }

    async processSyncTask(task) {
        // Process queued sync tasks
        // Implementation depends on specific task types
    }

    startMetricsCollection() {
        setInterval(() => {
            // Store metrics in Redis for monitoring
            this.redis.hmset('sync:metrics', {
                sync_operations: this.metrics.syncOperations,
                conflicts_detected: this.metrics.conflictsDetected,
                conflicts_resolved: this.metrics.conflictsResolved,
                bytes_transferred: this.metrics.bytesTransferred,
                average_sync_time: Math.round(this.metrics.averageSyncTime),
                error_count: this.metrics.errorCount,
                updated_at: new Date().toISOString()
            });
        }, 60000); // Every minute
    }

    getMetrics() {
        return { ...this.metrics };
    }

    async shutdown() {
        console.log('Shutting down Sync Service...');

        await this.pool.end();
        await this.redis.quit();

        console.log('Sync Service shutdown complete');
    }
}

module.exports = SyncService;