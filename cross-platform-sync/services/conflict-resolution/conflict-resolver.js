/**
 * DMlogn8n Cross-Platform Sync - Conflict Resolution Service
 * Advanced conflict detection and resolution strategies for save game synchronization
 */

const { Pool } = require('pg');
const Redis = require('ioredis');
const crypto = require('crypto');
const { diff } = require('deep-object-diff');
const jsonpatch = require('fast-json-patch');

class ConflictResolver {
    constructor(config = {}) {
        this.config = {
            database: {
                host: config.database?.host || process.env.DB_HOST,
                port: config.database?.port || process.env.DB_PORT || 5432,
                database: config.database?.database || process.env.DB_NAME,
                user: config.database?.user || process.env.DB_USER,
                password: config.database?.password || process.env.DB_PASSWORD,
                max: config.database?.maxConnections || 10
            },
            redis: {
                host: config.redis?.host || process.env.REDIS_HOST,
                port: config.redis?.port || process.env.REDIS_PORT || 6379,
                password: config.redis?.password || process.env.REDIS_PASSWORD,
                db: config.redis?.db || 0
            },
            resolution: {
                defaultStrategy: config.defaultStrategy || 'manual_review',
                autoResolveThreshold: config.autoResolveThreshold || 0.8,
                maxConflictAge: config.maxConflictAge || 86400000, // 24 hours
                enableLearning: config.enableLearning || false
            }
        };

        // Database connection
        this.pool = new Pool(this.config.database);
        this.redis = new Redis(this.config.redis);

        // Resolution strategies
        this.strategies = new Map();
        this.setupDefaultStrategies();

        // Conflict patterns for learning
        this.conflictPatterns = new Map();

        // Metrics
        this.metrics = {
            conflictsDetected: 0,
            conflictsResolved: 0,
            autoResolved: 0,
            manualResolved: 0,
            averageResolutionTime: 0
        };
    }

    /**
     * Initialize the conflict resolver
     */
    async initialize() {
        try {
            // Test connections
            await this.pool.query('SELECT NOW()');
            await this.redis.ping();

            // Load existing conflict patterns if learning is enabled
            if (this.config.resolution.enableLearning) {
                await this.loadConflictPatterns();
            }

            console.log('Conflict Resolver initialized');
        } catch (error) {
            console.error('Failed to initialize Conflict Resolver:', error);
            throw error;
        }
    }

    /**
     * Setup default resolution strategies
     */
    setupDefaultStrategies() {
        // Last Write Wins strategy
        this.strategies.set('last_write_wins', {
            name: 'Last Write Wins',
            description: 'Uses the most recent modification as the resolution',
            autoResolve: true,
            apply: (conflict, dataA, dataB) => {
                const timestampA = new Date(dataA.metadata?.timestamp || 0);
                const timestampB = new Date(dataB.metadata?.timestamp || 0);
                return timestampA > timestampB ? dataA : dataB;
            }
        });

        // Platform Priority strategy
        this.strategies.set('platform_priority', {
            name: 'Platform Priority',
            description: 'Resolves based on predefined platform hierarchy',
            autoResolve: true,
            apply: (conflict, dataA, dataB) => {
                const priority = {
                    'desktop': 1,
                    'mobile_ios': 2,
                    'mobile_android': 3,
                    'web': 4,
                    'vr_oculus': 5,
                    'vr_htc': 6
                };

                const priorityA = priority[dataA.metadata?.platform] || 999;
                const priorityB = priority[dataB.metadata?.platform] || 999;

                return priorityA < priorityB ? dataA : dataB;
            }
        });

        // Smart Merge strategy
        this.strategies.set('smart_merge', {
            name: 'Smart Merge',
            description: 'Intelligently merges data based on field types and patterns',
            autoResolve: true,
            apply: (conflict, dataA, dataB) => {
                return this.smartMerge(dataA, dataB, conflict.fieldPath);
            }
        });

        // Numeric Max strategy
        this.strategies.set('numeric_max', {
            name: 'Numeric Maximum',
            description: 'Uses the highest value for numeric fields',
            autoResolve: true,
            apply: (conflict, dataA, dataB) => {
                return this.resolveNumericMax(dataA, dataB, conflict.fieldPath);
            }
        });

        // Union strategy
        this.strategies.set('union_merge', {
            name: 'Union Merge',
            description: 'Combines arrays and objects using union operation',
            autoResolve: true,
            apply: (conflict, dataA, dataB) => {
                return this.unionMerge(dataA, dataB, conflict.fieldPath);
            }
        });

        // Manual Review strategy
        this.strategies.set('manual_review', {
            name: 'Manual Review Required',
            description: 'Requires manual intervention to resolve',
            autoResolve: false,
            apply: (conflict, dataA, dataB) => {
                throw new Error('Manual resolution required');
            }
        });
    }

    /**
     * Detect and analyze conflicts between save data versions
     */
    async detectConflict(userId, saveGameId, newData, existingData, platform, deviceId) {
        const startTime = Date.now();
        let conflict = null;

        try {
            // Calculate data differences
            const differences = this.calculateDifferences(existingData, newData);

            if (differences.length === 0) {
                return null; // No conflict
            }

            // Analyze conflict severity and type
            const conflictAnalysis = await this.analyzeConflict(differences, existingData, newData);

            // Create conflict record
            const conflictId = crypto.randomUUID();

            // Store in database
            const client = await this.pool.connect();
            try {
                await client.query('BEGIN');

                await client.query(`
                    INSERT INTO sync_conflicts (
                        id, user_id, save_game_id, conflict_type,
                        platform_a, device_a, platform_b, device_b,
                        data_a, data_b, field_path, detected_at,
                        resolution_strategy, conflict_analysis
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), $12, $13)
                `, [
                    conflictId,
                    userId,
                    saveGameId,
                    conflictAnalysis.type,
                    platform,
                    deviceId,
                    existingData.metadata?.platform || 'unknown',
                    existingData.metadata?.deviceId || 'unknown',
                    JSON.stringify(newData),
                    JSON.stringify(existingData),
                    conflictAnalysis.primaryFieldPath,
                    this.config.resolution.defaultStrategy,
                    JSON.stringify(conflictAnalysis)
                ]);

                await client.query('COMMIT');
            } finally {
                client.release();
            }

            // Cache in Redis for quick access
            await this.redis.hmset(`sync:conflict:${conflictId}`, {
                user_id: userId,
                save_game_id: saveGameId,
                conflict_type: conflictAnalysis.type,
                platform_a: platform,
                platform_b: existingData.metadata?.platform || 'unknown',
                detected_at: new Date().toISOString(),
                expires_at: new Date(Date.now() + this.config.resolution.maxConflictAge).toISOString(),
                conflict_analysis: JSON.stringify(conflictAnalysis)
            });

            await this.redis.expire(`sync:conflict:${conflictId}`, this.config.resolution.maxConflictAge / 1000);

            // Update conflict counts
            await this.redis.hincrby(`sync:save:${saveGameId}`, 'conflict_count', 1);
            await this.redis.hincrby(`sync:user:${userId}`, 'conflict_count', 1);

            // Publish conflict notification
            await this.redis.publish(`conflict:user:${userId}`, JSON.stringify({
                type: 'conflict_detected',
                conflictId,
                saveGameId,
                conflictType: conflictAnalysis.type,
                severity: conflictAnalysis.severity,
                timestamp: new Date().toISOString()
            }));

            // Update metrics
            this.metrics.conflictsDetected++;

            // Learn from this conflict pattern
            if (this.config.resolution.enableLearning) {
                await this.learnFromConflict(conflictAnalysis, differences);
            }

            conflict = {
                id: conflictId,
                type: conflictAnalysis.type,
                severity: conflictAnalysis.severity,
                differences,
                fieldPath: conflictAnalysis.primaryFieldPath,
                detectedAt: new Date().toISOString()
            };

        } catch (error) {
            console.error('Conflict detection failed:', error);
            throw error;
        }

        return conflict;
    }

    /**
     * Calculate differences between two data objects
     */
    calculateDifferences(dataA, dataB) {
        const differences = [];
        const diffResult = diff(dataA, dataB);

        this.flattenDifferences(diffResult, '', differences);
        return differences;
    }

    /**
     * Flatten nested differences into a list of field paths
     */
    flattenDifferences(diffObj, prefix, differences) {
        for (const [key, value] of Object.entries(diffObj)) {
            const fullPath = prefix ? `${prefix}.${key}` : key;

            if (value && typeof value === 'object' && !Array.isArray(value)) {
                this.flattenDifferences(value, fullPath, differences);
            } else {
                differences.push({
                    path: fullPath,
                    oldValue: value?.oldValue,
                    newValue: value?.newValue,
                    type: this.getDifferenceType(value)
                });
            }
        }
    }

    /**
     * Get the type of difference
     */
    getDifferenceType(diff) {
        if (diff.oldValue === undefined) return 'added';
        if (diff.newValue === undefined) return 'removed';
        if (typeof diff.oldValue !== typeof diff.newValue) return 'type_changed';
        return 'modified';
    }

    /**
     * Analyze conflict to determine type and severity
     */
    async analyzeConflict(differences, dataA, dataB) {
        const analysis = {
            type: 'data_mismatch',
            severity: 'medium',
            primaryFieldPath: null,
            conflictingFields: [],
            autoResolvable: false,
            suggestedStrategy: this.config.resolution.defaultStrategy
        };

        // Analyze each difference
        for (const diff of differences) {
            analysis.conflictingFields.push(diff.path);

            // Determine conflict type based on field paths
            if (diff.path.includes('characters.') && diff.path.includes('.experiencePoints')) {
                analysis.type = 'experience_mismatch';
                analysis.severity = 'low';
                analysis.autoResolvable = true;
                analysis.suggestedStrategy = 'numeric_max';
            } else if (diff.path.includes('characters.') && diff.path.includes('.level')) {
                analysis.type = 'level_mismatch';
                analysis.severity = 'medium';
                analysis.autoResolvable = true;
                analysis.suggestedStrategy = 'numeric_max';
            } else if (diff.path.includes('campaignState.') && diff.path.includes('.chapter')) {
                analysis.type = 'progress_mismatch';
                analysis.severity = 'high';
                analysis.autoResolvable = false;
                analysis.suggestedStrategy = 'manual_review';
            } else if (diff.path.includes('characters.') && diff.path.includes('.inventory')) {
                analysis.type = 'inventory_mismatch';
                analysis.severity = 'medium';
                analysis.autoResolvable = true;
                analysis.suggestedStrategy = 'union_merge';
            } else if (diff.path.includes('metadata.timestamp')) {
                analysis.type = 'timestamp_mismatch';
                analysis.severity = 'low';
                analysis.autoResolvable = true;
                analysis.suggestedStrategy = 'last_write_wins';
            }

            // Set primary field path (most important conflict)
            if (!analysis.primaryFieldPath || this.getFieldPriority(diff.path) > this.getFieldPriority(analysis.primaryFieldPath)) {
                analysis.primaryFieldPath = diff.path;
            }
        }

        // Determine overall severity
        if (analysis.conflictingFields.length > 10) {
            analysis.severity = 'high';
            analysis.autoResolvable = false;
        } else if (analysis.conflictingFields.length > 3) {
            analysis.severity = 'medium';
        } else {
            analysis.severity = 'low';
        }

        // Check if conflict can be auto-resolved based on patterns
        const confidence = await this.getResolutionConfidence(analysis);
        if (confidence > this.config.resolution.autoResolveThreshold && analysis.autoResolvable) {
            analysis.autoResolvable = true;
        } else {
            analysis.autoResolvable = false;
        }

        return analysis;
    }

    /**
     * Get field priority for conflict resolution
     */
    getFieldPriority(fieldPath) {
        const priorities = {
            'campaignState.chapter': 10,
            'campaignState.scene': 9,
            'characters': 8,
            'campaignState.variables': 7,
            'campaignState.flags': 6,
            'campaignState.worldState': 5,
            'metadata': 1
        };

        for (const [path, priority] of Object.entries(priorities)) {
            if (fieldPath.startsWith(path)) {
                return priority;
            }
        }

        return 0;
    }

    /**
     * Get confidence score for automatic resolution
     */
    async getResolutionConfidence(analysis) {
        // Base confidence on conflict type and field patterns
        let confidence = 0.5;

        // Check for learned patterns
        const patternKey = this.getPatternKey(analysis);
        const learnedPattern = this.conflictPatterns.get(patternKey);

        if (learnedPattern) {
            confidence = learnedPattern.successRate;
        }

        // Adjust based on conflict type
        switch (analysis.type) {
            case 'timestamp_mismatch':
            case 'experience_mismatch':
                confidence = Math.max(confidence, 0.9);
                break;
            case 'level_mismatch':
                confidence = Math.max(confidence, 0.8);
                break;
            case 'inventory_mismatch':
                confidence = Math.max(confidence, 0.7);
                break;
            case 'progress_mismatch':
                confidence = Math.min(confidence, 0.3);
                break;
        }

        return confidence;
    }

    /**
     * Get pattern key for conflict analysis
     */
    getPatternKey(analysis) {
        const fieldPaths = analysis.conflictingFields.map(path => {
            const parts = path.split('.');
            return parts.slice(0, 2).join('.'); // Only use top-level field paths
        }).sort().join(',');

        return `${analysis.type}:${fieldPaths}`;
    }

    /**
     * Learn from conflict resolution outcomes
     */
    async learnFromConflict(analysis, resolution) {
        if (!this.config.resolution.enableLearning) return;

        const patternKey = this.getPatternKey(analysis);
        const pattern = this.conflictPatterns.get(patternKey) || {
            type: analysis.type,
            fieldPaths: analysis.conflictingFields,
            attempts: 0,
            successes: 0,
            suggestedStrategy: analysis.suggestedStrategy
        };

        pattern.attempts++;

        if (resolution.success) {
            pattern.successes++;
            pattern.successRate = pattern.successes / pattern.attempts;
            pattern.suggestedStrategy = resolution.strategy;
        }

        this.conflictPatterns.set(patternKey, pattern);

        // Persist to Redis periodically
        if (pattern.attempts % 10 === 0) {
            await this.redis.hset(
                'conflict_patterns',
                patternKey,
                JSON.stringify(pattern)
            );
        }
    }

    /**
     * Resolve conflict using specified strategy
     */
    async resolveConflict(conflictId, strategy, customResolver = null) {
        const startTime = Date.now();
        let result = null;

        try {
            // Get conflict details
            const conflict = await this.getConflictDetails(conflictId);
            if (!conflict) {
                throw new Error('Conflict not found');
            }

            // Parse data
            const dataA = JSON.parse(conflict.data_a);
            const dataB = JSON.parse(conflict.data_b);

            let resolvedData;
            let appliedStrategy;

            // Apply resolution strategy
            if (customResolver) {
                resolvedData = await customResolver(conflict, dataA, dataB);
                appliedStrategy = 'custom';
            } else {
                const strategyHandler = this.strategies.get(strategy);
                if (!strategyHandler) {
                    throw new Error(`Unknown resolution strategy: ${strategy}`);
                }

                resolvedData = strategyHandler.apply(conflict, dataA, dataB);
                appliedStrategy = strategy;
            }

            // Validate resolved data
            await this.validateResolvedData(resolvedData);

            // Create new save version with resolved data
            const newVersion = await this.createResolvedVersion(
                conflict.save_game_id,
                resolvedData,
                appliedStrategy
            );

            // Update conflict record
            await this.updateConflictRecord(conflictId, {
                resolution_strategy: strategy,
                resolved_data: JSON.stringify(resolvedData),
                resolved_at: new Date(),
                resolution_version: newVersion
            });

            // Clear conflict from cache
            await this.redis.del(`sync:conflict:${conflictId}`);

            // Update conflict counts
            await this.redis.hincrby(`sync:save:${conflict.save_game_id}`, 'conflict_count', -1);
            await this.redis.hincrby(`sync:user:${conflict.user_id}`, 'conflict_count', -1);

            // Publish resolution notification
            await this.redis.publish(`conflict:user:${conflict.user_id}`, JSON.stringify({
                type: 'conflict_resolved',
                conflictId,
                saveGameId: conflict.save_game_id,
                strategy: appliedStrategy,
                version: newVersion,
                timestamp: new Date().toISOString()
            }));

            // Update metrics
            const resolutionTime = Date.now() - startTime;
            this.updateResolutionMetrics(resolutionTime, strategy !== 'manual_review');

            // Learn from resolution
            if (this.config.resolution.enableLearning) {
                await this.learnFromResolution(conflict, strategy, true);
            }

            result = {
                success: true,
                conflictId,
                saveGameId: conflict.save_game_id,
                version: newVersion,
                strategy: appliedStrategy,
                resolutionTime
            };

        } catch (error) {
            console.error('Conflict resolution failed:', error);

            // Learn from failure
            if (this.config.resolution.enableLearning) {
                await this.learnFromResolution({ id: conflictId }, strategy, false);
            }

            throw error;
        }

        return result;
    }

    /**
     * Get conflict details from database
     */
    async getConflictDetails(conflictId) {
        const result = await this.pool.query(
            'SELECT * FROM sync_conflicts WHERE id = $1',
            [conflictId]
        );

        return result.rows[0] || null;
    }

    /**
     * Validate resolved data
     */
    async validateResolvedData(data) {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid resolved data format');
        }

        // Required fields validation
        if (!data.saveGameId) {
            throw new Error('Missing saveGameId in resolved data');
        }

        if (!data.metadata) {
            throw new Error('Missing metadata in resolved data');
        }

        // Data consistency validation
        if (data.characters && Array.isArray(data.characters)) {
            for (const character of data.characters) {
                if (!character.name) {
                    throw new Error('Character missing required name field');
                }
                if (character.level && (character.level < 1 || character.level > 100)) {
                    throw new Error('Invalid character level');
                }
            }
        }

        return true;
    }

    /**
     * Create new save version with resolved data
     */
    async createResolvedVersion(saveGameId, resolvedData, strategy) {
        const client = await this.pool.connect();

        try {
            await client.query('BEGIN');

            // Get current version
            const currentVersionResult = await client.query(
                'SELECT MAX(sync_version) as max_version FROM save_game_data WHERE save_game_id = $1',
                [saveGameId]
            );

            const newVersion = (currentVersionResult.rows[0].max_version || 0) + 1;

            // Mark previous versions as not current
            await client.query(
                'UPDATE save_game_data SET is_current = false WHERE save_game_id = $1',
                [saveGameId]
            );

            // Insert resolved version
            const checksum = crypto.createHash('sha256')
                .update(JSON.stringify(resolvedData))
                .digest('hex');

            await client.query(`
                INSERT INTO save_game_data (
                    save_game_id, platform, device_id, data_json, sync_version,
                    is_current, data_hash, metadata
                ) VALUES ($1, $2, $3, $4, $5, true, $6, $7)
            `, [
                saveGameId,
                'resolved',
                'conflict_resolution',
                JSON.stringify(resolvedData),
                newVersion,
                checksum,
                JSON.stringify({
                    resolved: true,
                    strategy,
                    resolvedAt: new Date().toISOString()
                })
            ]);

            // Update save game record
            await client.query(`
                UPDATE save_games
                SET updated_at = NOW(), last_synced = NOW(), sync_status = 'synced'
                WHERE id = $1
            `, [saveGameId]);

            await client.query('COMMIT');

            // Update Redis
            await this.redis.hmset(`sync:save:${saveGameId}`, {
                current_version: newVersion,
                last_modified: new Date().toISOString(),
                checksum: checksum,
                sync_status: 'synced'
            });

            return newVersion;

        } catch (error) {
            await client.query('ROLLBACK');
            throw error;
        } finally {
            client.release();
        }
    }

    /**
     * Update conflict record
     */
    async updateConflictRecord(conflictId, updates) {
        const setClause = [];
        const values = [];
        let paramIndex = 1;

        Object.keys(updates).forEach(key => {
            setClause.push(`${key} = $${paramIndex}`);
            values.push(updates[key]);
            paramIndex++;
        });

        values.push(conflictId);

        await this.pool.query(`
            UPDATE sync_conflicts
            SET ${setClause.join(', ')}, is_resolved = true
            WHERE id = $${paramIndex}
        `, values);
    }

    /**
     * Smart merge implementation
     */
    smartMerge(dataA, dataB, fieldPath) {
        const result = { ...dataA };

        // Merge strategy based on field types
        if (fieldPath?.includes('experiencePoints') || fieldPath?.includes('level')) {
            // Use max for numeric progress fields
            this.mergeNumericMax(result, dataB, fieldPath);
        } else if (fieldPath?.includes('inventory') || fieldPath?.includes('abilities')) {
            // Use union for collection fields
            this.mergeUnion(result, dataB, fieldPath);
        } else if (fieldPath?.includes('flags') || fieldPath?.includes('variables')) {
            // Merge objects recursively
            this.mergeDeep(result, dataB);
        } else {
            // Default to last write wins for other fields
            return this.lastWriteWins(dataA, dataB);
        }

        return result;
    }

    /**
     * Last write wins implementation
     */
    lastWriteWins(dataA, dataB) {
        const timestampA = new Date(dataA.metadata?.timestamp || 0);
        const timestampB = new Date(dataB.metadata?.timestamp || 0);
        return timestampA > timestampB ? dataA : dataB;
    }

    /**
     * Numeric max resolution
     */
    resolveNumericMax(dataA, dataB, fieldPath) {
        const result = { ...dataA };
        this.mergeNumericMax(result, dataB, fieldPath);
        return result;
    }

    /**
     * Merge numeric fields using max
     */
    mergeNumericMax(target, source, fieldPath) {
        if (fieldPath) {
            const valueA = this.getNestedValue(target, fieldPath);
            const valueB = this.getNestedValue(source, fieldPath);

            if (typeof valueA === 'number' && typeof valueB === 'number') {
                this.setNestedValue(target, fieldPath, Math.max(valueA, valueB));
            }
        } else {
            // Apply to all numeric fields
            this.mergeNumericFields(target, source);
        }
    }

    /**
     * Merge all numeric fields using max
     */
    mergeNumericFields(target, source) {
        for (const [key, value] of Object.entries(source)) {
            if (typeof value === 'number' && typeof target[key] === 'number') {
                target[key] = Math.max(target[key], value);
            } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                if (!target[key] || typeof target[key] !== 'object') {
                    target[key] = {};
                }
                this.mergeNumericFields(target[key], value);
            }
        }
    }

    /**
     * Union merge implementation
     */
    unionMerge(dataA, dataB, fieldPath) {
        const result = { ...dataA };
        this.mergeUnion(result, dataB, fieldPath);
        return result;
    }

    /**
     * Merge collections using union
     */
    mergeUnion(target, source, fieldPath) {
        if (fieldPath) {
            const valueA = this.getNestedValue(target, fieldPath);
            const valueB = this.getNestedValue(source, fieldPath);

            if (Array.isArray(valueA) && Array.isArray(valueB)) {
                // Union of arrays
                const union = new Set([...valueA, ...valueB]);
                this.setNestedValue(target, fieldPath, Array.from(union));
            } else if (typeof valueA === 'object' && typeof valueB === 'object') {
                // Merge objects
                const merged = { ...valueA, ...valueB };
                this.setNestedValue(target, fieldPath, merged);
            }
        } else {
            this.mergeUnionCollections(target, source);
        }
    }

    /**
     * Merge union collections
     */
    mergeUnionCollections(target, source) {
        for (const [key, value] of Object.entries(source)) {
            if (Array.isArray(value) && Array.isArray(target[key])) {
                target[key] = [...new Set([...target[key], ...value])];
            } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                if (!target[key] || typeof target[key] !== 'object') {
                    target[key] = {};
                }
                this.mergeUnionCollections(target[key], value);
            } else {
                target[key] = value;
            }
        }
    }

    /**
     * Deep merge implementation
     */
    mergeDeep(target, source) {
        for (const [key, value] of Object.entries(source)) {
            if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
                if (!target[key] || typeof target[key] !== 'object') {
                    target[key] = {};
                }
                this.mergeDeep(target[key], value);
            } else {
                target[key] = value;
            }
        }
    }

    /**
     * Get nested value from object
     */
    getNestedValue(obj, path) {
        return path.split('.').reduce((current, key) => current?.[key], obj);
    }

    /**
     * Set nested value in object
     */
    setNestedValue(obj, path, value) {
        const keys = path.split('.');
        const lastKey = keys.pop();
        const target = keys.reduce((current, key) => {
            if (!current[key] || typeof current[key] !== 'object') {
                current[key] = {};
            }
            return current[key];
        }, obj);
        target[lastKey] = value;
    }

    /**
     * Learn from resolution outcome
     */
    async learnFromResolution(conflict, strategy, success) {
        if (!this.config.resolution.enableLearning) return;

        // This would be called with the actual conflict data when resolution completes
        const patternKey = `${strategy}:${success ? 'success' : 'failure'}`;

        // Update learning metrics
        await this.redis.hincrby('resolution_learning', patternKey, 1);
    }

    /**
     * Load conflict patterns from Redis
     */
    async loadConflictPatterns() {
        try {
            const patterns = await this.redis.hgetall('conflict_patterns');
            for (const [key, value] of Object.entries(patterns)) {
                this.conflictPatterns.set(key, JSON.parse(value));
            }
            console.log(`Loaded ${this.conflictPatterns.size} conflict patterns`);
        } catch (error) {
            console.error('Failed to load conflict patterns:', error);
        }
    }

    /**
     * Update resolution metrics
     */
    updateResolutionMetrics(resolutionTime, wasAuto) {
        this.metrics.conflictsResolved++;
        if (wasAuto) {
            this.metrics.autoResolved++;
        } else {
            this.metrics.manualResolved++;
        }

        // Update average resolution time
        this.metrics.averageResolutionTime =
            (this.metrics.averageResolutionTime * (this.metrics.conflictsResolved - 1) + resolutionTime) /
            this.metrics.conflictsResolved;
    }

    /**
     * Get conflict statistics
     */
    async getConflictStatistics(userId = null, saveGameId = null) {
        try {
            let query = `
                SELECT
                    conflict_type,
                    COUNT(*) as count,
                    AVG(EXTRACT(EPOCH FROM (resolved_at - detected_at)) * 1000) as avg_resolution_time_ms,
                    resolution_strategy,
                    COUNT(*) FILTER (WHERE is_resolved = true) as resolved_count
                FROM sync_conflicts
                WHERE 1=1
            `;
            const params = [];
            let paramIndex = 1;

            if (userId) {
                query += ` AND user_id = $${paramIndex}`;
                params.push(userId);
                paramIndex++;
            }

            if (saveGameId) {
                query += ` AND save_game_id = $${paramIndex}`;
                params.push(saveGameId);
                paramIndex++;
            }

            query += ` GROUP BY conflict_type, resolution_strategy ORDER BY count DESC`;

            const result = await this.pool.query(query, params);
            return result.rows;
        } catch (error) {
            console.error('Failed to get conflict statistics:', error);
            return [];
        }
    }

    /**
     * Get active conflicts
     */
    async getActiveConflicts(userId = null) {
        try {
            let query = `
                SELECT
                    sc.*,
                    sg.campaign_name
                FROM sync_conflicts sc
                JOIN save_games sg ON sc.save_game_id = sg.id
                WHERE sc.is_resolved = false
            `;
            const params = [];
            let paramIndex = 1;

            if (userId) {
                query += ` AND sc.user_id = $${paramIndex}`;
                params.push(userId);
                paramIndex++;
            }

            query += ` ORDER BY sc.detected_at DESC`;

            const result = await this.pool.query(query, params);
            return result.rows.map(row => ({
                id: row.id,
                saveGameId: row.save_game_id,
                campaignName: row.campaign_name,
                conflictType: row.conflict_type,
                platformA: row.platform_a,
                platformB: row.platform_b,
                fieldPath: row.field_path,
                detectedAt: row.detected_at,
                resolutionStrategy: row.resolution_strategy
            }));
        } catch (error) {
            console.error('Failed to get active conflicts:', error);
            return [];
        }
    }

    /**
     * Get resolution metrics
     */
    getMetrics() {
        return {
            ...this.metrics,
            learnedPatterns: this.conflictPatterns.size,
            availableStrategies: Array.from(this.strategies.keys())
        };
    }

    /**
     * Cleanup old conflicts
     */
    async cleanupOldConflicts() {
        try {
            const expiredDate = new Date(Date.now() - this.config.resolution.maxConflictAge);

            const result = await this.pool.query(`
                DELETE FROM sync_conflicts
                WHERE detected_at < $1 AND is_resolved = false
            `, [expiredDate]);

            console.log(`Cleaned up ${result.rowCount} expired conflicts`);

            // Also clean up Redis
            const keys = await this.redis.keys('sync:conflict:*');
            for (const key of keys) {
                const expiresAt = await this.redis.hget(key, 'expires_at');
                if (expiresAt && new Date(expiresAt) < new Date()) {
                    await this.redis.del(key);
                }
            }

        } catch (error) {
            console.error('Failed to cleanup old conflicts:', error);
        }
    }

    /**
     * Shutdown the conflict resolver
     */
    async shutdown() {
        console.log('Shutting down Conflict Resolver...');

        await this.pool.end();
        await this.redis.quit();

        console.log('Conflict Resolver shutdown complete');
    }
}

module.exports = ConflictResolver;