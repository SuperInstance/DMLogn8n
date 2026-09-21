const winston = require('winston');

class PerformanceOptimizer {
    constructor(redisClient) {
        this.redisClient = redisClient;
        this.cacheStats = {
            hits: 0,
            misses: 0,
            sets: 0,
            deletes: 0
        };
        this.performanceMetrics = {
            averageResponseTime: 0,
            totalRequests: 0,
            slowQueries: 0,
            errorRate: 0
        };
        this.optimizationStrategies = this.initializeOptimizationStrategies();
    }

    // Initialize optimization strategies
    initializeOptimizationStrategies() {
        return {
            caching: {
                enabled: true,
                defaultTTL: 3600, // 1 hour
                keyPrefix: 'rec_cache:',
                compression: true,
                serialization: 'json'
            },
            batchProcessing: {
                enabled: true,
                batchSize: 100,
                maxWaitTime: 50, // ms
                priorityQueue: true
            },
            connectionPooling: {
                enabled: true,
                maxConnections: 10,
                minConnections: 2,
                acquireTimeout: 30000,
                idleTimeout: 30000
            },
            queryOptimization: {
                enabled: true,
                indexHints: true,
                queryPlanCache: true,
                resultSizeLimit: 1000
            },
            memoryManagement: {
                enabled: true,
                maxCacheSize: '500MB',
                evictionPolicy: 'lru',
                cleanupInterval: 300000 // 5 minutes
            }
        };
    }

    // Cache management
    async get(key, options = {}) {
        try {
            const cacheKey = this.buildCacheKey(key);
            const cached = await this.redisClient.get(cacheKey);

            if (cached) {
                this.cacheStats.hits++;

                // Decompress if needed
                const data = options.compression !== false && this.optimizationStrategies.caching.compression
                    ? JSON.parse(this.decompress(cached))
                    : JSON.parse(cached);

                winston.debug(`Cache hit for key: ${key}`);
                return data;
            } else {
                this.cacheStats.misses++;
                winston.debug(`Cache miss for key: ${key}`);
                return null;
            }
        } catch (error) {
            winston.error('Cache get error:', error);
            return null;
        }
    }

    async set(key, value, options = {}) {
        try {
            const cacheKey = this.buildCacheKey(key);
            const ttl = options.ttl || this.optimizationStrategies.caching.defaultTTL;

            // Compress if needed
            const serialized = options.compression !== false && this.optimizationStrategies.caching.compression
                ? this.compress(JSON.stringify(value))
                : JSON.stringify(value);

            await this.redisClient.setEx(cacheKey, ttl, serialized);
            this.cacheStats.sets++;

            winston.debug(`Cache set for key: ${key}, TTL: ${ttl}s`);
            return true;
        } catch (error) {
            winston.error('Cache set error:', error);
            return false;
        }
    }

    async delete(key) {
        try {
            const cacheKey = this.buildCacheKey(key);
            await this.redisClient.del(cacheKey);
            this.cacheStats.deletes++;

            winston.debug(`Cache delete for key: ${key}`);
            return true;
        } catch (error) {
            winston.error('Cache delete error:', error);
            return false;
        }
    }

    // Batch operations
    async batchGet(keys, options = {}) {
        try {
            const cacheKeys = keys.map(key => this.buildCacheKey(key));
            const results = await this.redisClient.mGet(cacheKeys);

            const mappedResults = {};
            keys.forEach((key, index) => {
                const value = results[index];
                if (value) {
                    this.cacheStats.hits++;
                    mappedResults[key] = options.compression !== false && this.optimizationStrategies.caching.compression
                        ? JSON.parse(this.decompress(value))
                        : JSON.parse(value);
                } else {
                    this.cacheStats.misses++;
                    mappedResults[key] = null;
                }
            });

            return mappedResults;
        } catch (error) {
            winston.error('Batch cache get error:', error);
            return {};
        }
    }

    async batchSet(items, options = {}) {
        try {
            const ttl = options.ttl || this.optimizationStrategies.caching.defaultTTL;
            const operations = [];

            Object.entries(items).forEach(([key, value]) => {
                const cacheKey = this.buildCacheKey(key);
                const serialized = options.compression !== false && this.optimizationStrategies.caching.compression
                    ? this.compress(JSON.stringify(value))
                    : JSON.stringify(value);

                operations.push(['setEx', cacheKey, ttl, serialized]);
            });

            await this.redisClient.multi(operations);
            this.cacheStats.sets += items.length;

            winston.debug(`Batch cache set for ${items.length} items`);
            return true;
        } catch (error) {
            winston.error('Batch cache set error:', error);
            return false;
        }
    }

    // Performance monitoring
    startTimer(label) {
        return {
            label,
            startTime: process.hrtime.bigint(),
            end: () => this.endTimer(this)
        };
    }

    endTimer(timer) {
        const endTime = process.hrtime.bigint();
        const duration = Number(endTime - timer.startTime) / 1000000; // Convert to milliseconds

        this.updatePerformanceMetrics(timer.label, duration);

        if (duration > 1000) { // Log slow queries (> 1s)
            this.performanceMetrics.slowQueries++;
            winston.warn(`Slow query detected: ${timer.label} took ${duration.toFixed(2)}ms`);
        }

        return duration;
    }

    updatePerformanceMetrics(label, duration) {
        this.performanceMetrics.totalRequests++;

        // Calculate rolling average response time
        const alpha = 0.1; // Smoothing factor
        this.performanceMetrics.averageResponseTime =
            (this.performanceMetrics.averageResponseTime * (1 - alpha)) + (duration * alpha);

        // Update error rate (would be called from error handlers)
        // this.performanceMetrics.errorRate = errorCount / totalRequests;
    }

    // Memory management
    async cleanupExpiredCache() {
        try {
            const pattern = this.optimizationStrategies.caching.keyPrefix + '*';
            const keys = await this.redisClient.keys(pattern);

            if (keys.length > 10000) { // If cache is too large
                winston.info(`Cache cleanup: ${keys.length} keys found, implementing aggressive cleanup`);

                // Sample and remove old keys
                const sampleKeys = keys.slice(0, 1000);
                await this.redisClient.del(sampleKeys);

                return {
                    cleaned: sampleKeys.length,
                    remaining: keys.length - sampleKeys.length
                };
            }

            return { cleaned: 0, remaining: keys.length };
        } catch (error) {
            winston.error('Cache cleanup error:', error);
            return { cleaned: 0, remaining: 0, error: error.message };
        }
    }

    // Query optimization
    optimizeQuery(query, options = {}) {
        if (!this.optimizationStrategies.queryOptimization.enabled) {
            return query;
        }

        let optimizedQuery = query;

        // Add limit if not present
        if (!optimizedQuery.includes('LIMIT') && this.optimizationStrategies.queryOptimization.resultSizeLimit) {
            optimizedQuery += ` LIMIT ${this.optimizationStrategies.queryOptimization.resultSizeLimit}`;
        }

        // Add index hints if enabled
        if (this.optimizationStrategies.queryOptimization.indexHints && options.index) {
            optimizedQuery = optimizedQuery.replace(/FROM\s+(\w+)/i, `FROM $1 USE INDEX (${options.index})`);
        }

        return optimizedQuery;
    }

    // Compression utilities
    compress(data) {
        // Simple compression for demonstration
        // In production, use proper compression libraries like zlib
        return Buffer.from(data).toString('base64');
    }

    decompress(compressedData) {
        // Simple decompression for demonstration
        // In production, use proper decompression libraries
        return Buffer.from(compressedData, 'base64').toString();
    }

    // Cache key generation
    buildCacheKey(key) {
        const prefix = this.optimizationStrategies.caching.keyPrefix;
        const hash = this.hashKey(key);
        return `${prefix}${hash}`;
    }

    hashKey(key) {
        // Simple hash function - in production use crypto module
        let hash = 0;
        const str = JSON.stringify(key);
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return Math.abs(hash).toString(36);
    }

    // Cache statistics
    getCacheStats() {
        const total = this.cacheStats.hits + this.cacheStats.misses;
        return {
            ...this.cacheStats,
            hitRate: total > 0 ? (this.cacheStats.hits / total) : 0,
            missRate: total > 0 ? (this.cacheStats.misses / total) : 0,
            total
        };
    }

    getPerformanceMetrics() {
        return {
            ...this.performanceMetrics,
            requestsPerSecond: this.performanceMetrics.totalRequests / (process.uptime() || 1),
            cacheHitRate: this.getCacheStats().hitRate
        };
    }

    // Health check
    async healthCheck() {
        try {
            const timer = this.startTimer('cache_health_check');

            // Test cache operations
            const testKey = 'health_check_' + Date.now();
            const testValue = { timestamp: Date.now() };

            await this.set(testKey, testValue, { ttl: 10 });
            const retrieved = await this.get(testKey);
            await this.delete(testKey);

            const duration = timer.end();

            const isHealthy = retrieved && retrieved.timestamp === testValue.timestamp;
            const stats = this.getCacheStats();

            return {
                status: isHealthy ? 'healthy' : 'unhealthy',
                responseTime: duration,
                cacheStats: stats,
                performanceMetrics: this.getPerformanceMetrics(),
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            winston.error('Cache health check failed:', error);
            return {
                status: 'unhealthy',
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    // Recommendation-specific optimizations
    async cacheRecommendations(userId, recommendations, type = 'general', options = {}) {
        const key = {
            userId,
            type,
            filters: options.filters || {},
            timestamp: Date.now()
        };

        const ttl = options.ttl || this.getRecommendationTTL(type);
        return await this.set(key, recommendations, { ttl });
    }

    async getCachedRecommendations(userId, type = 'general', options = {}) {
        const key = {
            userId,
            type,
            filters: options.filters || {}
        };

        return await this.get(key);
    }

    getRecommendationTTL(type) {
        const ttls = {
            'personalized': 1800, // 30 minutes
            'trending': 600,      // 10 minutes
            'popular': 3600,      // 1 hour
            'builds': 7200,       // 2 hours
            'equipment': 7200,    // 2 hours
            'spells': 7200,       // 2 hours
            'encounters': 3600,   // 1 hour
            'npcs': 7200,         // 2 hours
            'general': 1800       // 30 minutes
        };

        return ttls[type] || ttls.general;
    }

    // Batch recommendation processing
    async processBatchRecommendations(requests) {
        if (!this.optimizationStrategies.batchProcessing.enabled) {
            // Process sequentially
            const results = [];
            for (const request of requests) {
                try {
                    const result = await this.processSingleRecommendation(request);
                    results.push({ success: true, data: result, id: request.id });
                } catch (error) {
                    results.push({ success: false, error: error.message, id: request.id });
                }
            }
            return results;
        }

        // Process in batches
        const batchSize = this.optimizationStrategies.batchProcessing.batchSize;
        const batches = [];

        for (let i = 0; i < requests.length; i += batchSize) {
            batches.push(requests.slice(i, i + batchSize));
        }

        const results = [];
        for (const batch of batches) {
            const batchResults = await Promise.allSettled(
                batch.map(request => this.processSingleRecommendation(request))
            );

            batchResults.forEach((result, index) => {
                if (result.status === 'fulfilled') {
                    results.push({ success: true, data: result.value, id: batch[index].id });
                } else {
                    results.push({ success: false, error: result.reason.message, id: batch[index].id });
                }
            });
        }

        return results;
    }

    async processSingleRecommendation(request) {
        // This would integrate with the actual recommendation services
        // For now, return a mock result
        return {
            recommendations: [],
            userId: request.userId,
            type: request.type,
            timestamp: Date.now()
        };
    }

    // Warm up cache
    async warmUpCache() {
        try {
            winston.info('Starting cache warm-up...');

            const warmUpData = [
                { key: 'trending_content', data: [], ttl: 600 },
                { key: 'popular_campaigns', data: [], ttl: 3600 },
                { key: 'community_highlights', data: [], ttl: 1800 }
            ];

            for (const item of warmUpData) {
                await this.set(item.key, item.data, { ttl: item.ttl });
            }

            winston.info('Cache warm-up completed');
            return true;
        } catch (error) {
            winston.error('Cache warm-up failed:', error);
            return false;
        }
    }

    // Invalidate cache patterns
    async invalidatePattern(pattern) {
        try {
            const fullPattern = this.optimizationStrategies.caching.keyPrefix + pattern;
            const keys = await this.redisClient.keys(fullPattern);

            if (keys.length > 0) {
                await this.redisClient.del(keys);
                winston.info(`Invalidated ${keys.length} cache keys matching pattern: ${pattern}`);
            }

            return keys.length;
        } catch (error) {
            winston.error('Cache invalidation error:', error);
            return 0;
        }
    }

    // Start background tasks
    startBackgroundTasks() {
        // Cache cleanup task
        setInterval(async () => {
            await this.cleanupExpiredCache();
        }, this.optimizationStrategies.memoryManagement.cleanupInterval);

        // Cache statistics logging
        setInterval(() => {
            const stats = this.getCacheStats();
            const metrics = this.getPerformanceMetrics();

            winston.info('Performance Stats:', {
                cache: stats,
                performance: {
                    avgResponseTime: metrics.averageResponseTime.toFixed(2) + 'ms',
                    requestsPerSecond: metrics.requestsPerSecond.toFixed(2),
                    slowQueries: metrics.slowQueries,
                    errorRate: (metrics.errorRate * 100).toFixed(2) + '%'
                }
            });
        }, 60000); // Log every minute
    }
}

module.exports = PerformanceOptimizer;