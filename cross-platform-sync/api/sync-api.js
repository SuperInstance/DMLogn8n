/**
 * DMlogn8n Cross-Platform Sync API
 * RESTful API endpoints for save game synchronization
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const multer = require('multer');
const { body, param, query, validationResult } = require('express-validator');
const SyncService = require('../services/sync-server/sync-service');
const ConflictResolver = require('../services/conflict-resolution/conflict-resolver');
const AuditTrailService = require('../services/conflict-resolution/audit-trail-service');
const authMiddleware = require('../middleware/auth');
const { validateSyncData, validateConflictResolution } = require('../middleware/validation');

class SyncAPI {
    constructor(config = {}) {
        this.app = express();
        this.config = {
            port: config.port || process.env.PORT || 3000,
            environment: config.environment || process.env.NODE_ENV || 'development',
            cors: config.cors || {
                origin: process.env.CORS_ORIGIN || '*',
                credentials: true
            },
            rateLimit: config.rateLimit || {
                windowMs: 15 * 60 * 1000, // 15 minutes
                max: 100 // limit each IP to 100 requests per windowMs
            }
        };

        // Initialize services
        this.syncService = new SyncService(config);
        this.conflictResolver = new ConflictResolver(config);
        this.auditService = new AuditTrailService(config);

        // Setup middleware
        this.setupMiddleware();

        // Setup routes
        this.setupRoutes();

        // Setup error handling
        this.setupErrorHandling();
    }

    /**
     * Setup Express middleware
     */
    setupMiddleware() {
        // Security middleware
        this.app.use(helmet());
        this.app.use(cors(this.config.cors));

        // Rate limiting
        this.app.use(rateLimit(this.config.rateLimit));

        // Body parsing
        this.app.use(express.json({ limit: '50mb' }));
        this.app.use(express.urlencoded({ extended: true, limit: '50mb' }));

        // File upload handling
        const upload = multer({
            storage: multer.memoryStorage(),
            limits: {
                fileSize: 100 * 1024 * 1024 // 100MB
            }
        });
        this.upload = upload;

        // Request logging
        this.app.use((req, res, next) => {
            console.log(`${new Date().toISOString()} - ${req.method} ${req.path} - ${req.ip}`);
            next();
        });
    }

    /**
     * Setup API routes
     */
    setupRoutes() {
        const router = express.Router();

        // Health check
        router.get('/health', this.healthCheck.bind(this));

        // Authentication endpoints
        router.post('/auth/login', this.login.bind(this));
        router.post('/auth/refresh', this.refreshToken.bind(this));
        router.post('/auth/logout', authMiddleware, this.logout.bind(this));

        // Save game synchronization
        router.post('/sync',
            authMiddleware,
            validateSyncData,
            this.syncSaveGame.bind(this)
        );

        router.get('/saves/:saveGameId',
            authMiddleware,
            this.getSaveGame.bind(this)
        );

        router.post('/saves',
            authMiddleware,
            validateSyncData,
            this.createSaveGame.bind(this)
        );

        router.delete('/saves/:saveGameId',
            authMiddleware,
            this.deleteSaveGame.bind(this)
        );

        router.get('/saves',
            authMiddleware,
            this.listSaveGames.bind(this)
        );

        router.get('/saves/:saveGameId/check',
            authMiddleware,
            this.checkSyncStatus.bind(this)
        );

        // Conflict management
        router.get('/conflicts',
            authMiddleware,
            this.getConflicts.bind(this)
        );

        router.get('/conflicts/:conflictId',
            authMiddleware,
            this.getConflict.bind(this)
        );

        router.post('/conflicts/:conflictId/resolve',
            authMiddleware,
            validateConflictResolution,
            this.resolveConflict.bind(this)
        );

        router.get('/conflicts/:conflictId/history',
            authMiddleware,
            this.getConflictHistory.bind(this)
        );

        // Analytics and monitoring
        router.get('/analytics/sync',
            authMiddleware,
            this.getSyncAnalytics.bind(this)
        );

        router.get('/analytics/conflicts',
            authMiddleware,
            this.getConflictAnalytics.bind(this)
        );

        router.get('/status',
            authMiddleware,
            this.getSyncStatus.bind(this)
        );

        // Audit and compliance
        router.get('/audit/events',
            authMiddleware,
            this.getAuditEvents.bind(this)
        );

        router.get('/audit/export',
            authMiddleware,
            this.exportAuditData.bind(this)
        );

        router.get('/audit/statistics',
            authMiddleware,
            this.getAuditStatistics.bind(this)
        );

        // Real-time sync webhooks
        router.post('/webhook/sync-completed',
            this.syncCompletedWebhook.bind(this)
        );

        router.post('/webhook/conflict-detected',
            this.conflictDetectedWebhook.bind(this)
        );

        // Asset management
        router.post('/assets',
            authMiddleware,
            this.upload.single('asset'),
            this.uploadAsset.bind(this)
        );

        router.get('/assets/:assetId',
            authMiddleware,
            this.getAsset.bind(this)
        );

        router.delete('/assets/:assetId',
            authMiddleware,
            this.deleteAsset.bind(this)
        );

        // Platform-specific endpoints
        router.get('/platforms',
            authMiddleware,
            this.getPlatforms.bind(this)
        );

        router.post('/platforms/register',
            authMiddleware,
            this.registerPlatform.bind(this)
        );

        router.put('/platforms/:platformId',
            authMiddleware,
            this.updatePlatform.bind(this)
        );

        // Batch operations
        router.post('/batch/sync',
            authMiddleware,
            this.batchSync.bind(this)
        );

        router.post('/batch/resolve-conflicts',
            authMiddleware,
            this.batchResolveConflicts.bind(this)
        );

        // Apply routes
        this.app.use('/api/v1/sync', router);

        // Root endpoint
        this.app.get('/', (req, res) => {
            res.json({
                service: 'DMlogn8n Cross-Platform Sync API',
                version: '1.0.0',
                status: 'running',
                timestamp: new Date().toISOString()
            });
        });
    }

    /**
     * Health check endpoint
     */
    async healthCheck(req, res) {
        try {
            const health = {
                status: 'healthy',
                timestamp: new Date().toISOString(),
                services: {
                    database: 'unknown',
                    redis: 'unknown'
                }
            };

            // Check database connection
            try {
                await this.syncService.pool.query('SELECT NOW()');
                health.services.database = 'healthy';
            } catch (error) {
                health.services.database = 'unhealthy';
                health.status = 'degraded';
            }

            // Check Redis connection
            try {
                await this.syncService.redis.ping();
                health.services.redis = 'healthy';
            } catch (error) {
                health.services.redis = 'unhealthy';
                health.status = 'degraded';
            }

            const statusCode = health.status === 'healthy' ? 200 : 503;
            res.status(statusCode).json(health);

        } catch (error) {
            res.status(500).json({
                status: 'unhealthy',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }

    /**
     * Authentication endpoints
     */
    async login(req, res) {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) {
                return res.status(400).json({
                    success: false,
                    errors: errors.array()
                });
            }

            const { email, password, platform, deviceId } = req.body;

            // Authenticate user (implement your auth logic here)
            const user = await this.authenticateUser(email, password);
            if (!user) {
                return res.status(401).json({
                    success: false,
                    error: 'Invalid credentials'
                });
            }

            // Generate JWT token
            const token = this.generateJWT(user);

            // Log authentication
            await this.auditService.logAuthentication({
                userId: user.id,
                action: 'login',
                platform,
                deviceId,
                ipAddress: req.ip,
                userAgent: req.get('User-Agent'),
                success: true
            });

            res.json({
                success: true,
                token,
                user: {
                    id: user.id,
                    username: user.username,
                    email: user.email
                }
            });

        } catch (error) {
            console.error('Login error:', error);
            res.status(500).json({
                success: false,
                error: 'Internal server error'
            });
        }
    }

    async refreshToken(req, res) {
        try {
            const { refreshToken } = req.body;

            // Verify and refresh token (implement your logic here)
            const newToken = await this.refreshJWT(refreshToken);

            res.json({
                success: true,
                token: newToken
            });

        } catch (error) {
            res.status(401).json({
                success: false,
                error: 'Invalid refresh token'
            });
        }
    }

    async logout(req, res) {
        try {
            // Log logout
            await this.auditService.logAuthentication({
                userId: req.user.id,
                action: 'logout',
                platform: req.get('X-Platform'),
                deviceId: req.get('X-Device-ID'),
                ipAddress: req.ip,
                userAgent: req.get('User-Agent'),
                success: true
            });

            res.json({
                success: true,
                message: 'Logged out successfully'
            });

        } catch (error) {
            res.status(500).json({
                success: false,
                error: 'Internal server error'
            });
        }
    }

    /**
     * Save game synchronization endpoints
     */
    async syncSaveGame(req, res) {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) {
                return res.status(400).json({
                    success: false,
                    errors: errors.array()
                });
            }

            const { saveGameId, data, platform, deviceId, version, checksum } = req.body;
            const userId = req.user.id;

            // Log sync attempt
            await this.auditService.logSyncOperation({
                action: 'upload',
                saveGameId,
                userId,
                platform,
                deviceId,
                oldVersion: version,
                newVersion: null,
                success: false
            });

            // Perform sync
            const result = await this.syncService.syncSaveGame(
                userId,
                saveGameId,
                platform,
                deviceId,
                data,
                {
                    checksum,
                    clientVersion: version
                }
            );

            // Log successful sync
            await this.auditService.logSyncOperation({
                action: 'upload',
                saveGameId,
                userId,
                platform,
                deviceId,
                oldVersion: version,
                newVersion: result.version,
                success: true,
                bytesTransferred: result.bytesTransferred
            });

            res.json(result);

        } catch (error) {
            console.error('Sync error:', error);

            // Log failed sync
            await this.auditService.logSyncOperation({
                action: 'upload',
                saveGameId: req.body.saveGameId,
                userId: req.user.id,
                platform: req.body.platform,
                deviceId: req.body.deviceId,
                oldVersion: req.body.version,
                success: false,
                error: error.message
            });

            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async getSaveGame(req, res) {
        try {
            const { saveGameId } = req.params;
            const { version, platform, deviceId } = req.query;
            const userId = req.user.id;

            const result = await this.syncService.getSaveGame(
                userId,
                saveGameId,
                platform,
                deviceId,
                version
            );

            // Log data access
            await this.auditService.logDataAccess({
                action: 'read',
                resourceType: 'save_game',
                resourceId: saveGameId,
                userId,
                platform,
                deviceId,
                success: true
            });

            res.json(result);

        } catch (error) {
            console.error('Get save game error:', error);

            // Log failed access
            await this.auditService.logDataAccess({
                action: 'read',
                resourceType: 'save_game',
                resourceId: req.params.saveGameId,
                userId: req.user.id,
                platform: req.query.platform,
                deviceId: req.query.deviceId,
                success: false,
                error: error.message
            });

            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async createSaveGame(req, res) {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) {
                return res.status(400).json({
                    success: false,
                    errors: errors.array()
                });
            }

            const { campaignName, data, platform, deviceId } = req.body;
            const userId = req.user.id;

            const result = await this.syncService.createSaveGame(
                userId,
                campaignName,
                data,
                platform,
                deviceId
            );

            // Log save creation
            await this.auditService.logDataAccess({
                action: 'write',
                resourceType: 'save_game',
                resourceId: result.saveGameId,
                userId,
                platform,
                deviceId,
                success: true
            });

            res.status(201).json(result);

        } catch (error) {
            console.error('Create save game error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async deleteSaveGame(req, res) {
        try {
            const { saveGameId } = req.params;
            const userId = req.user.id;

            await this.syncService.deleteSaveGame(userId, saveGameId);

            // Log deletion
            await this.auditService.logDataAccess({
                action: 'delete',
                resourceType: 'save_game',
                resourceId: saveGameId,
                userId,
                success: true
            });

            res.json({
                success: true,
                message: 'Save game deleted successfully'
            });

        } catch (error) {
            console.error('Delete save game error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async listSaveGames(req, res) {
        try {
            const { limit = 50, offset = 0, platform } = req.query;
            const userId = req.user.id;

            const result = await this.syncService.listSaveGames(
                userId,
                parseInt(limit),
                parseInt(offset),
                platform
            );

            res.json(result);

        } catch (error) {
            console.error('List save games error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async checkSyncStatus(req, res) {
        try {
            const { saveGameId } = req.params;
            const { version, platform, deviceId } = req.query;
            const userId = req.user.id;

            const syncNeeded = await this.syncService.checkSyncNeeded(
                userId,
                saveGameId,
                version
            );

            res.json({
                syncNeeded,
                saveGameId,
                currentVersion: version,
                platform,
                deviceId
            });

        } catch (error) {
            console.error('Check sync status error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    /**
     * Conflict management endpoints
     */
    async getConflicts(req, res) {
        try {
            const { status = 'active', limit = 50, offset = 0 } = req.query;
            const userId = req.user.id;

            const conflicts = await this.conflictResolver.getActiveConflicts(userId);

            res.json({
                conflicts,
                total: conflicts.length,
                limit: parseInt(limit),
                offset: parseInt(offset)
            });

        } catch (error) {
            console.error('Get conflicts error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async getConflict(req, res) {
        try {
            const { conflictId } = req.params;
            const userId = req.user.id;

            const conflict = await this.conflictResolver.getConflictDetails(conflictId);

            if (!conflict || conflict.user_id !== userId) {
                return res.status(404).json({
                    success: false,
                    error: 'Conflict not found'
                });
            }

            res.json(conflict);

        } catch (error) {
            console.error('Get conflict error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async resolveConflict(req, res) {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) {
                return res.status(400).json({
                    success: false,
                    errors: errors.array()
                });
            }

            const { conflictId } = req.params;
            const { resolution, customData } = req.body;
            const userId = req.user.id;

            const result = await this.conflictResolver.resolveConflict(
                conflictId,
                resolution,
                customData
            );

            // Log conflict resolution
            await this.auditService.logConflict({
                action: 'resolved',
                conflictId,
                userId,
                platform: req.get('X-Platform'),
                deviceId: req.get('X-Device-ID'),
                conflictType: result.conflictType,
                resolutionStrategy: resolution,
                success: true,
                resolutionTime: result.resolutionTime
            });

            res.json(result);

        } catch (error) {
            console.error('Resolve conflict error:', error);

            // Log failed resolution
            await this.auditService.logConflict({
                action: 'resolve_failed',
                conflictId: req.params.conflictId,
                userId: req.user.id,
                platform: req.get('X-Platform'),
                deviceId: req.get('X-Device-ID'),
                success: false,
                error: error.message
            });

            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async getConflictHistory(req, res) {
        try {
            const { conflictId } = req.params;
            const userId = req.user.id;

            const history = await this.conflictResolver.getConflictHistory(conflictId);

            res.json({ history });

        } catch (error) {
            console.error('Get conflict history error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    /**
     * Analytics endpoints
     */
    async getSyncAnalytics(req, res) {
        try {
            const { startDate, endDate, platform } = req.query;
            const userId = req.user.id;

            const analytics = await this.syncService.getAnalytics(userId, {
                startDate,
                endDate,
                platform
            });

            res.json(analytics);

        } catch (error) {
            console.error('Get sync analytics error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async getConflictAnalytics(req, res) {
        try {
            const { startDate, endDate } = req.query;
            const userId = req.user.id;

            const analytics = await this.conflictResolver.getConflictStatistics(
                userId,
                startDate,
                endDate
            );

            res.json(analytics);

        } catch (error) {
            console.error('Get conflict analytics error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async getSyncStatus(req, res) {
        try {
            const userId = req.user.id;

            const status = {
                userId,
                timestamp: new Date().toISOString(),
                services: {
                    sync: this.syncService.getMetrics(),
                    conflict: this.conflictResolver.getMetrics(),
                    audit: this.auditService.getMetrics()
                }
            };

            res.json(status);

        } catch (error) {
            console.error('Get sync status error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    /**
     * Audit endpoints
     */
    async getAuditEvents(req, res) {
        try {
            const {
                startDate,
                endDate,
                category,
                level,
                limit = 100,
                offset = 0
            } = req.query;
            const userId = req.user.id;

            const events = await this.auditService.queryEvents({
                userId,
                startDate,
                endDate,
                category,
                level
            }, {
                limit: parseInt(limit),
                offset: parseInt(offset)
            });

            res.json(events);

        } catch (error) {
            console.error('Get audit events error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async exportAuditData(req, res) {
        try {
            const { format = 'json', startDate, endDate, category } = req.query;
            const userId = req.user.id;

            const data = await this.auditService.exportData({
                userId,
                startDate,
                endDate,
                category
            }, format);

            const filename = `audit-export-${new Date().toISOString().split('T')[0]}.${format}`;

            res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
            res.setHeader('Content-Type', format === 'csv' ? 'text/csv' : 'application/json');
            res.send(data);

        } catch (error) {
            console.error('Export audit data error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async getAuditStatistics(req, res) {
        try {
            const { startDate, endDate } = req.query;
            const userId = req.user.id;

            const statistics = await this.auditService.getStatistics({
                userId,
                startDate,
                endDate
            });

            res.json(statistics);

        } catch (error) {
            console.error('Get audit statistics error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    /**
     * Webhook endpoints
     */
    async syncCompletedWebhook(req, res) {
        try {
            const webhookData = req.body;

            // Process sync completion
            console.log('Sync completed webhook:', webhookData);

            // Trigger real-time notifications
            await this.triggerRealTimeNotifications(webhookData);

            res.json({ success: true });

        } catch (error) {
            console.error('Sync completed webhook error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async conflictDetectedWebhook(req, res) {
        try {
            const webhookData = req.body;

            // Process conflict detection
            console.log('Conflict detected webhook:', webhookData);

            // Trigger conflict resolution workflow
            await this.triggerConflictResolution(webhookData);

            res.json({ success: true });

        } catch (error) {
            console.error('Conflict detected webhook error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    /**
     * Asset management endpoints
     */
    async uploadAsset(req, res) {
        try {
            if (!req.file) {
                return res.status(400).json({
                    success: false,
                    error: 'No file uploaded'
                });
            }

            const { assetType, saveGameId } = req.body;
            const userId = req.user.id;

            const asset = await this.syncService.uploadAsset(
                userId,
                saveGameId,
                assetType,
                req.file
            );

            res.json(asset);

        } catch (error) {
            console.error('Upload asset error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async getAsset(req, res) {
        try {
            const { assetId } = req.params;
            const userId = req.user.id;

            const asset = await this.syncService.getAsset(userId, assetId);

            if (!asset) {
                return res.status(404).json({
                    success: false,
                    error: 'Asset not found'
                });
            }

            res.redirect(asset.url);

        } catch (error) {
            console.error('Get asset error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async deleteAsset(req, res) {
        try {
            const { assetId } = req.params;
            const userId = req.user.id;

            await this.syncService.deleteAsset(userId, assetId);

            res.json({
                success: true,
                message: 'Asset deleted successfully'
            });

        } catch (error) {
            console.error('Delete asset error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    /**
     * Platform management endpoints
     */
    async getPlatforms(req, res) {
        try {
            const userId = req.user.id;

            const platforms = await this.syncService.getUserPlatforms(userId);

            res.json({ platforms });

        } catch (error) {
            console.error('Get platforms error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async registerPlatform(req, res) {
        try {
            const { platform, deviceId, deviceName } = req.body;
            const userId = req.user.id;

            const result = await this.syncService.registerPlatform(
                userId,
                platform,
                deviceId,
                deviceName
            );

            res.json(result);

        } catch (error) {
            console.error('Register platform error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async updatePlatform(req, res) {
        try {
            const { platformId } = req.params;
            const { deviceName } = req.body;
            const userId = req.user.id;

            const result = await this.syncService.updatePlatform(
                userId,
                platformId,
                deviceName
            );

            res.json(result);

        } catch (error) {
            console.error('Update platform error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    /**
     * Batch operation endpoints
     */
    async batchSync(req, res) {
        try {
            const { operations } = req.body;
            const userId = req.user.id;

            const results = await this.syncService.batchSync(userId, operations);

            res.json(results);

        } catch (error) {
            console.error('Batch sync error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async batchResolveConflicts(req, res) {
        try {
            const { resolutions } = req.body;
            const userId = req.user.id;

            const results = await this.conflictResolver.batchResolveConflicts(
                userId,
                resolutions
            );

            res.json(results);

        } catch (error) {
            console.error('Batch resolve conflicts error:', error);
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    /**
     * Helper methods
     */
    setupErrorHandling() {
        // 404 handler
        this.app.use('*', (req, res) => {
            res.status(404).json({
                success: false,
                error: 'Endpoint not found'
            });
        });

        // Global error handler
        this.app.use((error, req, res, next) => {
            console.error('Global error handler:', error);

            // Log system error
            this.auditService.logSystemEvent({
                action: 'api_error',
                component: 'sync-api',
                level: 'error',
                error: error.message,
                stackTrace: error.stack
            }).catch(console.error);

            if (this.config.environment === 'development') {
                res.status(500).json({
                    success: false,
                    error: error.message,
                    stack: error.stack
                });
            } else {
                res.status(500).json({
                    success: false,
                    error: 'Internal server error'
                });
            }
        });
    }

    async authenticateUser(email, password) {
        // Implement your authentication logic here
        // This is a placeholder - integrate with your user management system
        return {
            id: 'user-123',
            username: 'testuser',
            email: email
        };
    }

    generateJWT(user) {
        // Implement JWT generation
        return 'jwt-token-placeholder';
    }

    async refreshJWT(refreshToken) {
        // Implement JWT refresh logic
        return 'new-jwt-token';
    }

    async triggerRealTimeNotifications(data) {
        // Trigger real-time notifications via WebSocket or other mechanisms
    }

    async triggerConflictResolution(data) {
        // Trigger conflict resolution workflow
    }

    /**
     * Start the API server
     */
    async start() {
        try {
            // Initialize services
            await this.syncService.initialize();
            await this.conflictResolver.initialize();
            await this.auditService.initialize();

            // Start server
            this.server = this.app.listen(this.config.port, () => {
                console.log(`DMlogn8n Sync API listening on port ${this.config.port}`);
                console.log(`Environment: ${this.config.environment}`);
            });

            return this.server;

        } catch (error) {
            console.error('Failed to start API server:', error);
            throw error;
        }
    }

    /**
     * Stop the API server
     */
    async stop() {
        if (this.server) {
            return new Promise((resolve) => {
                this.server.close(resolve);
            });
        }
    }
}

module.exports = SyncAPI;