const redis = require('redis');
const winston = require('winston');

class RedisConfig {
    constructor() {
        this.client = null;
        this.isConnected = false;
    }

    async connect() {
        try {
            const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';

            this.client = redis.createClient({
                url: redisUrl,
                retry_strategy: (options) => {
                    if (options.error && options.error.code === 'ECONNREFUSED') {
                        winston.error('Redis server connection refused');
                        return new Error('Redis server connection refused');
                    }
                    if (options.total_retry_time > 1000 * 60 * 60) {
                        winston.error('Redis retry time exhausted');
                        return new Error('Retry time exhausted');
                    }
                    if (options.attempt > 10) {
                        winston.error('Redis max retry attempts reached');
                        return undefined;
                    }
                    return Math.min(options.attempt * 100, 3000);
                }
            });

            this.client.on('error', (err) => {
                winston.error('Redis client error:', err);
                this.isConnected = false;
            });

            this.client.on('connect', () => {
                winston.info('Redis client connected');
                this.isConnected = true;
            });

            this.client.on('ready', () => {
                winston.info('Redis client ready');
            });

            this.client.on('end', () => {
                winston.warn('Redis client disconnected');
                this.isConnected = false;
            });

            await this.client.connect();

        } catch (error) {
            winston.error('Failed to connect to Redis:', error);
            this.isConnected = false;
        }
    }

    async disconnect() {
        if (this.client) {
            await this.client.disconnect();
            winston.info('Redis client disconnected');
        }
    }

    // Recommendation caching methods
    async cacheRecommendations(userId, type, recommendations, ttl = 3600) {
        if (!this.isConnected) return false;

        try {
            const key = `recommendations:${userId}:${type}`;
            await this.client.setEx(key, ttl, JSON.stringify(recommendations));
            return true;
        } catch (error) {
            winston.error('Error caching recommendations:', error);
            return false;
        }
    }

    async getCachedRecommendations(userId, type) {
        if (!this.isConnected) return null;

        try {
            const key = `recommendations:${userId}:${type}`;
            const cached = await this.client.get(key);
            return cached ? JSON.parse(cached) : null;
        } catch (error) {
            winston.error('Error getting cached recommendations:', error);
            return null;
        }
    }

    // User behavior tracking
    async trackBehavior(userId, behavior) {
        if (!this.isConnected) return false;

        try {
            const key = `behavior:${userId}`;
            await this.client.lPush(key, JSON.stringify(behavior));
            await this.client.lTrim(key, 0, 999); // Keep last 1000 behaviors
            await this.client.expire(key, 86400 * 30); // 30 days expiry
            return true;
        } catch (error) {
            winston.error('Error tracking behavior:', error);
            return false;
        }
    }

    async getBehaviorHistory(userId, limit = 100) {
        if (!this.isConnected) return [];

        try {
            const key = `behavior:${userId}`;
            const behaviors = await this.client.lRange(key, 0, limit - 1);
            return behaviors.map(b => JSON.parse(b));
        } catch (error) {
            winston.error('Error getting behavior history:', error);
            return [];
        }
    }

    // Trending content caching
    async cacheTrendingContent(category, content, ttl = 1800) {
        if (!this.isConnected) return false;

        try {
            const key = `trending:${category}`;
            await this.client.setEx(key, ttl, JSON.stringify(content));
            return true;
        } catch (error) {
            winston.error('Error caching trending content:', error);
            return false;
        }
    }

    async getTrendingContent(category) {
        if (!this.isConnected) return null;

        try {
            const key = `trending:${category}`;
            const cached = await this.client.get(key);
            return cached ? JSON.parse(cached) : null;
        } catch (error) {
            winston.error('Error getting trending content:', error);
            return null;
        }
    }

    // Similarity cache
    async cacheSimilarity(contentId1, contentId2, similarity, ttl = 86400) {
        if (!this.isConnected) return false;

        try {
            const key = `similarity:${contentId1}:${contentId2}`;
            await this.client.setEx(key, ttl, similarity.toString());
            return true;
        } catch (error) {
            winston.error('Error caching similarity:', error);
            return false;
        }
    }

    async getSimilarity(contentId1, contentId2) {
        if (!this.isConnected) return null;

        try {
            const key = `similarity:${contentId1}:${contentId2}`;
            const similarity = await this.client.get(key);
            return similarity ? parseFloat(similarity) : null;
        } catch (error) {
            winston.error('Error getting similarity:', error);
            return null;
        }
    }

    // Multi-armed bandit statistics
    async updateBanditStats(armId, reward) {
        if (!this.isConnected) return false;

        try {
            const key = `bandit:${armId}`;
            await this.client.hIncrBy(key, 'pulls', 1);
            await this.client.hIncrByFloat(key, 'total_reward', reward);
            await this.client.expire(key, 86400 * 7); // 7 days expiry
            return true;
        } catch (error) {
            winston.error('Error updating bandit stats:', error);
            return false;
        }
    }

    async getBanditStats(armId) {
        if (!this.isConnected) return null;

        try {
            const key = `bandit:${armId}`;
            const stats = await this.client.hGetAll(key);
            if (Object.keys(stats).length === 0) return null;

            return {
                pulls: parseInt(stats.pulls) || 0,
                total_reward: parseFloat(stats.total_reward) || 0,
                average_reward: stats.pulls ? parseFloat(stats.total_reward) / parseInt(stats.pulls) : 0
            };
        } catch (error) {
            winston.error('Error getting bandit stats:', error);
            return null;
        }
    }

    getClient() {
        return this.client;
    }

    isReady() {
        return this.isConnected;
    }
}

module.exports = new RedisConfig();