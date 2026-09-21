const mongoose = require('mongoose');
const winston = require('winston');

class DatabaseConfig {
    constructor() {
        this.connectionOptions = {
            useNewUrlParser: true,
            useUnifiedTopology: true,
            maxPoolSize: 10,
            serverSelectionTimeoutMS: 5000,
            socketTimeoutMS: 45000,
            bufferCommands: false,
            bufferMaxEntries: 0
        };
    }

    async connect() {
        try {
            const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/dmlogn8n-recommendations';

            await mongoose.connect(mongoUri, this.connectionOptions);

            winston.info('Connected to MongoDB successfully');

            // Handle connection events
            mongoose.connection.on('error', (err) => {
                winston.error('MongoDB connection error:', err);
            });

            mongoose.connection.on('disconnected', () => {
                winston.warn('MongoDB disconnected');
            });

            mongoose.connection.on('reconnected', () => {
                winston.info('MongoDB reconnected');
            });

        } catch (error) {
            winston.error('Failed to connect to MongoDB:', error);
            process.exit(1);
        }
    }

    async disconnect() {
        try {
            await mongoose.disconnect();
            winston.info('Disconnected from MongoDB');
        } catch (error) {
            winston.error('Error disconnecting from MongoDB:', error);
        }
    }

    // Indexes for recommendation queries
    static async createIndexes() {
        try {
            const db = mongoose.connection.db;

            // User behavior indexes
            await db.collection('userbehaviors').createIndex({ userId: 1, timestamp: -1 });
            await db.collection('userbehaviors').createIndex({ contentType: 1, action: 1 });
            await db.collection('userbehaviors').createIndex({ contentId: 1, rating: -1 });

            // Content similarity indexes
            await db.collection('contentsimilarities').createIndex({ contentId1: 1, contentId2: 1 });
            await db.collection('contentsimilarities').createIndex({ similarity: -1 });

            // Recommendation caches
            await db.collection('recommendationcaches').createIndex({ userId: 1, type: 1 });
            await db.collection('recommendationcaches').createIndex({ expiresAt: 1 });

            // Trending content indexes
            await db.collection('trendingcontents').createIndex({ category: 1, score: -1 });
            await db.collection('trendingcontents').createIndex({ updatedAt: -1 });

            winston.info('Database indexes created successfully');
        } catch (error) {
            winston.error('Error creating database indexes:', error);
        }
    }
}

module.exports = DatabaseConfig;