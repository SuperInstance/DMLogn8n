/**
 * DMlogn8n Cross-Platform Sync WebSocket Gateway
 * Real-time synchronization server for multi-platform save game synchronization
 */

const WebSocket = require('ws');
const Redis = require('ioredis');
const jwt = require('jsonwebtoken');
const uuid = require('uuid');
const crypto = require('crypto');

class WebSocketGateway {
    constructor(config = {}) {
        this.config = {
            port: config.port || 8080,
            redis: {
                host: config.redis?.host || 'localhost',
                port: config.redis?.port || 6379,
                password: config.redis?.password || null,
                db: config.redis?.db || 0
            },
            jwt: {
                secret: config.jwt?.secret || process.env.JWT_SECRET,
                algorithm: config.jwt?.algorithm || 'HS256'
            },
            heartbeat: {
                interval: config.heartbeat?.interval || 30000,
                timeout: config.heartbeat?.timeout || 60000
            },
            maxConnections: config.maxConnections || 10000,
            messageQueueSize: config.messageQueueSize || 1000
        };

        // WebSocket server instance
        this.wss = null;

        // Redis connections
        this.redis = new Redis(this.config.redis);
        this.redisSubscriber = new Redis(this.config.redis);
        this.redisPublisher = new Redis(this.config.redis);

        // Active connections management
        this.connections = new Map(); // sessionId -> connection info
        this.userSessions = new Map(); // userId -> Set of sessionIds
        this.saveSubscriptions = new Map(); // saveId -> Set of sessionIds

        // Message queues for offline users
        this.messageQueues = new Map(); // userId -> Array of messages

        // Statistics and monitoring
        this.stats = {
            totalConnections: 0,
            activeConnections: 0,
            messagesSent: 0,
            messagesReceived: 0,
            conflictsDetected: 0,
            syncOperations: 0,
            errors: 0
        };

        // Initialize the server
        this.initialize();
    }

    async initialize() {
        try {
            // Create WebSocket server
            this.wss = new WebSocket.Server({
                port: this.config.port,
                verifyClient: this.verifyClient.bind(this)
            });

            // Setup WebSocket event handlers
            this.wss.on('connection', this.handleConnection.bind(this));
            this.wss.on('error', this.handleServerError.bind(this));

            // Setup Redis pub/sub for cross-instance communication
            await this.setupRedisPubSub();

            // Start heartbeat monitoring
            this.startHeartbeatMonitoring();

            // Start cleanup tasks
            this.startCleanupTasks();

            console.log(`WebSocket Gateway started on port ${this.config.port}`);
        } catch (error) {
            console.error('Failed to initialize WebSocket Gateway:', error);
            throw error;
        }
    }

    /**
     * Verify client authentication before establishing WebSocket connection
     */
    async verifyClient(info) {
        try {
            const token = this.extractToken(info.req);
            if (!token) {
                return false;
            }

            // Verify JWT token
            const decoded = jwt.verify(token, this.config.jwt.secret, {
                algorithms: [this.config.jwt.algorithm]
            });

            // Add user info to request object
            info.req.user = decoded;
            info.req.sessionId = uuid.v4();

            return true;
        } catch (error) {
            console.error('Client verification failed:', error.message);
            return false;
        }
    }

    extractToken(req) {
        const authHeader = req.headers['authorization'];
        if (authHeader && authHeader.startsWith('Bearer ')) {
            return authHeader.substring(7);
        }

        // Also check query parameter for fallback
        const url = new URL(req.url, `http://${req.headers.host}`);
        return url.searchParams.get('token');
    }

    /**
     * Handle new WebSocket connection
     */
    async handleConnection(ws, req) {
        const user = req.user;
        const sessionId = req.sessionId;
        const platform = req.headers['x-platform'] || 'unknown';
        const deviceId = req.headers['x-device-id'] || 'unknown';

        // Check connection limits
        if (this.stats.activeConnections >= this.config.maxConnections) {
            ws.close(1013, 'Server overloaded');
            return;
        }

        // Create connection info object
        const connectionInfo = {
            ws,
            user,
            sessionId,
            platform,
            deviceId,
            connectedAt: new Date(),
            lastPing: new Date(),
            messageCount: 0,
            subscriptions: new Set(),
            isAlive: true,
            ip: req.socket.remoteAddress,
            userAgent: req.headers['user-agent']
        };

        // Store connection
        this.connections.set(sessionId, connectionInfo);

        // Add to user's sessions
        if (!this.userSessions.has(user.id)) {
            this.userSessions.set(user.id, new Set());
        }
        this.userSessions.get(user.id).add(sessionId);

        // Update statistics
        this.stats.totalConnections++;
        this.stats.activeConnections++;

        // Register session in Redis
        await this.registerSession(connectionInfo);

        // Setup WebSocket event handlers
        ws.on('message', (data) => this.handleMessage(sessionId, data));
        ws.on('pong', () => this.handlePong(sessionId));
        ws.on('close', () => this.handleClose(sessionId));
        ws.on('error', (error) => this.handleError(sessionId, error));

        // Send welcome message
        this.sendMessage(sessionId, {
            type: 'welcome',
            sessionId,
            timestamp: new Date().toISOString(),
            serverTime: Date.now()
        });

        // Process any queued messages
        await this.processQueuedMessages(user.id);

        console.log(`User ${user.username} connected from ${platform} (${deviceId})`);
    }

    /**
     * Register session in Redis for cross-instance communication
     */
    async registerSession(connectionInfo) {
        const { user, sessionId, platform, deviceId } = connectionInfo;

        await this.redis.hmset(`ws:session:${sessionId}`, {
            user_id: user.id,
            platform,
            device_id: deviceId,
            connected_at: connectionInfo.connectedAt.toISOString(),
            last_ping: connectionInfo.lastPing.toISOString(),
            subscriptions: JSON.stringify([]),
            sync_queue: JSON.stringify([])
        });

        await this.redis.sadd(`ws:user:${user.id}`, sessionId);
        await this.redis.expire(`ws:session:${sessionId}`, 3600); // 1 hour TTL
    }

    /**
     * Handle incoming WebSocket messages
     */
    async handleMessage(sessionId, data) {
        try {
            const connectionInfo = this.connections.get(sessionId);
            if (!connectionInfo) return;

            connectionInfo.messageCount++;
            this.stats.messagesReceived++;

            let message;
            try {
                message = JSON.parse(data.toString());
            } catch (error) {
                this.sendError(sessionId, 'Invalid JSON message format');
                return;
            }

            // Update last activity
            connectionInfo.lastPing = new Date();
            await this.redis.hset(`ws:session:${sessionId}`, 'last_ping', connectionInfo.lastPing.toISOString());

            // Route message based on type
            switch (message.type) {
                case 'subscribe':
                    await this.handleSubscribe(sessionId, message);
                    break;
                case 'unsubscribe':
                    await this.handleUnsubscribe(sessionId, message);
                    break;
                case 'sync_request':
                    await this.handleSyncRequest(sessionId, message);
                    break;
                case 'sync_data':
                    await this.handleSyncData(sessionId, message);
                    break;
                case 'conflict_resolution':
                    await this.handleConflictResolution(sessionId, message);
                    break;
                case 'heartbeat':
                    this.handleHeartbeat(sessionId, message);
                    break;
                default:
                    this.sendError(sessionId, `Unknown message type: ${message.type}`);
            }
        } catch (error) {
            console.error('Error handling message:', error);
            this.stats.errors++;
            this.sendError(sessionId, 'Internal server error');
        }
    }

    /**
     * Handle subscription to save game updates
     */
    async handleSubscribe(sessionId, message) {
        const connectionInfo = this.connections.get(sessionId);
        if (!connectionInfo) return;

        const { saveId } = message;
        if (!saveId) {
            this.sendError(sessionId, 'Missing saveId in subscription request');
            return;
        }

        // Add to connection's subscriptions
        connectionInfo.subscriptions.add(saveId);

        // Add to global subscriptions
        if (!this.saveSubscriptions.has(saveId)) {
            this.saveSubscriptions.set(saveId, new Set());
        }
        this.saveSubscriptions.get(saveId).add(sessionId);

        // Update Redis
        const subscriptions = Array.from(connectionInfo.subscriptions);
        await this.redis.hset(`ws:session:${sessionId}`, 'subscriptions', JSON.stringify(subscriptions));

        // Send confirmation
        this.sendMessage(sessionId, {
            type: 'subscription_confirmed',
            saveId,
            timestamp: new Date().toISOString()
        });

        console.log(`Session ${sessionId} subscribed to save ${saveId}`);
    }

    /**
     * Handle unsubscription from save game updates
     */
    async handleUnsubscribe(sessionId, message) {
        const connectionInfo = this.connections.get(sessionId);
        if (!connectionInfo) return;

        const { saveId } = message;
        if (!saveId) return;

        // Remove from connection's subscriptions
        connectionInfo.subscriptions.delete(saveId);

        // Remove from global subscriptions
        if (this.saveSubscriptions.has(saveId)) {
            this.saveSubscriptions.get(saveId).delete(sessionId);
            if (this.saveSubscriptions.get(saveId).size === 0) {
                this.saveSubscriptions.delete(saveId);
            }
        }

        // Update Redis
        const subscriptions = Array.from(connectionInfo.subscriptions);
        await this.redis.hset(`ws:session:${sessionId}`, 'subscriptions', JSON.stringify(subscriptions));

        this.sendMessage(sessionId, {
            type: 'unsubscription_confirmed',
            saveId,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Handle sync request from client
     */
    async handleSyncRequest(sessionId, message) {
        const connectionInfo = this.connections.get(sessionId);
        if (!connectionInfo) return;

        const { saveId, platform, deviceId, lastSyncVersion } = message;

        try {
            // Check for distributed lock
            const lockKey = `lock:save:${saveId}`;
            const lockOwner = await this.redis.get(lockKey);

            if (lockOwner && lockOwner !== `${platform}:${deviceId}`) {
                this.sendMessage(sessionId, {
                    type: 'sync_denied',
                    saveId,
                    reason: 'Save is currently locked by another device',
                    timestamp: new Date().toISOString()
                });
                return;
            }

            // Get current save state from Redis
            const saveState = await this.redis.hgetall(`sync:save:${saveId}`);

            if (!saveState || !saveState.current_version) {
                this.sendError(sessionId, 'Save not found or not synchronized');
                return;
            }

            const currentVersion = parseInt(saveState.current_version);

            // Check if client needs update
            if (lastSyncVersion && currentVersion > lastSyncVersion) {
                // Client needs to download latest version
                this.sendMessage(sessionId, {
                    type: 'sync_update_available',
                    saveId,
                    currentVersion,
                    lastModified: saveState.last_modified,
                    timestamp: new Date().toISOString()
                });
            } else if (lastSyncVersion === currentVersion) {
                // Client is up to date
                this.sendMessage(sessionId, {
                    type: 'sync_up_to_date',
                    saveId,
                    version: currentVersion,
                    timestamp: new Date().toISOString()
                });
            }

            this.stats.syncOperations++;

        } catch (error) {
            console.error('Error handling sync request:', error);
            this.sendError(sessionId, 'Sync request failed');
        }
    }

    /**
     * Handle sync data from client
     */
    async handleSyncData(sessionId, message) {
        const connectionInfo = this.connections.get(sessionId);
        if (!connectionInfo) return;

        const { saveId, platform, deviceId, data, version, checksum } = message;

        try {
            // Verify checksum
            const calculatedChecksum = crypto.createHash('sha256').update(JSON.stringify(data)).digest('hex');
            if (checksum && checksum !== calculatedChecksum) {
                this.sendError(sessionId, 'Data checksum mismatch');
                return;
            }

            // Get current save state
            const saveState = await this.redis.hgetall(`sync:save:${saveId}`);

            if (!saveState) {
                this.sendError(sessionId, 'Save not found');
                return;
            }

            const currentVersion = parseInt(saveState.current_version);

            // Check for conflicts
            if (version && version < currentVersion) {
                // Conflict detected
                await this.handleConflictDetection(sessionId, {
                    saveId,
                    platform,
                    deviceId,
                    clientData: data,
                    clientVersion: version,
                    serverVersion: currentVersion
                });
                return;
            }

            // Acquire lock for save operation
            const lockAcquired = await this.acquireSaveLock(saveId, `${platform}:${deviceId}`);
            if (!lockAcquired) {
                this.sendError(sessionId, 'Failed to acquire save lock');
                return;
            }

            // Store new version
            const newVersion = currentVersion + 1;
            await this.redis.hmset(`sync:save:${saveId}`, {
                current_version: newVersion,
                last_modified: new Date().toISOString(),
                checksum: calculatedChecksum,
                locked_by: `${platform}:${deviceId}`,
                locked_until: (Date.now() + 30000).toString() // 30 seconds
            });

            // Store versioned data
            await this.redis.set(`sync:data:${saveId}:${newVersion}`, JSON.stringify(data));
            await this.redis.expire(`sync:data:${saveId}:${newVersion}`, 86400 * 7); // 7 days

            // Update device sync state
            const deviceKey = `sync:device:${connectionInfo.user.id}:${platform}:${deviceId}`;
            await this.redis.hmset(deviceKey, {
                sync_version: newVersion,
                last_seen: new Date().toISOString(),
                status: 'synced'
            });

            // Publish update to all subscribed clients
            await this.redisPublisher.publish(`sync:save:${saveId}`, JSON.stringify({
                type: 'save_updated',
                saveId,
                version: newVersion,
                updatedBy: `${platform}:${deviceId}`,
                timestamp: new Date().toISOString()
            }));

            // Update user's overall sync state
            await this.redis.hmset(`sync:user:${connectionInfo.user.id}`, {
                last_sync: new Date().toISOString(),
                sync_version: newVersion
            });

            // Send confirmation to client
            this.sendMessage(sessionId, {
                type: 'sync_confirmed',
                saveId,
                version: newVersion,
                timestamp: new Date().toISOString()
            });

            this.stats.syncOperations++;

            // Release lock
            await this.releaseSaveLock(saveId);

        } catch (error) {
            console.error('Error handling sync data:', error);
            this.sendError(sessionId, 'Sync data processing failed');
        }
    }

    /**
     * Handle conflict resolution from client
     */
    async handleConflictResolution(sessionId, message) {
        const connectionInfo = this.connections.get(sessionId);
        if (!connectionInfo) return;

        const { conflictId, resolution, resolvedData } = message;

        try {
            // Get conflict details
            const conflict = await this.redis.hgetall(`sync:conflict:${conflictId}`);

            if (!conflict) {
                this.sendError(sessionId, 'Conflict not found');
                return;
            }

            // Apply resolution
            if (resolution === 'use_client') {
                // Use client's resolved data
                await this.applyConflictResolution(conflict, resolvedData, connectionInfo);
            } else if (resolution === 'use_server') {
                // Keep server data
                await this.redis.del(`sync:conflict:${conflictId}`);
            } else if (resolution === 'merge') {
                // Apply merged data
                await this.applyConflictResolution(conflict, resolvedData, connectionInfo);
            }

            // Update conflict status
            await this.redis.hset(`sync:conflict:${conflictId}`, 'is_resolved', 'true', 'resolved_at', new Date().toISOString());

            // Send confirmation
            this.sendMessage(sessionId, {
                type: 'conflict_resolved',
                conflictId,
                resolution,
                timestamp: new Date().toISOString()
            });

            // Notify other devices
            await this.notifyConflictResolved(conflict.save_game_id, conflictId, resolution);

        } catch (error) {
            console.error('Error handling conflict resolution:', error);
            this.sendError(sessionId, 'Conflict resolution failed');
        }
    }

    /**
     * Handle heartbeat messages
     */
    handleHeartbeat(sessionId, message) {
        const connectionInfo = this.connections.get(sessionId);
        if (connectionInfo) {
            connectionInfo.lastPing = new Date();
            connectionInfo.isAlive = true;

            this.sendMessage(sessionId, {
                type: 'heartbeat_response',
                timestamp: new Date().toISOString(),
                serverTime: Date.now()
            });
        }
    }

    /**
     * Handle WebSocket pong (heartbeat response)
     */
    handlePong(sessionId) {
        const connectionInfo = this.connections.get(sessionId);
        if (connectionInfo) {
            connectionInfo.isAlive = true;
            connectionInfo.lastPing = new Date();
        }
    }

    /**
     * Handle WebSocket connection close
     */
    async handleClose(sessionId) {
        const connectionInfo = this.connections.get(sessionId);
        if (!connectionInfo) return;

        const { user, sessionId: sid, platform, deviceId } = connectionInfo;

        // Remove from active connections
        this.connections.delete(sessionId);
        this.stats.activeConnections--;

        // Remove from user sessions
        if (this.userSessions.has(user.id)) {
            this.userSessions.get(user.id).delete(sessionId);
            if (this.userSessions.get(user.id).size === 0) {
                this.userSessions.delete(user.id);
            }
        }

        // Remove from subscriptions
        connectionInfo.subscriptions.forEach(saveId => {
            if (this.saveSubscriptions.has(saveId)) {
                this.saveSubscriptions.get(saveId).delete(sessionId);
                if (this.saveSubscriptions.get(saveId).size === 0) {
                    this.saveSubscriptions.delete(saveId);
                }
            }
        });

        // Cleanup Redis session
        await this.redis.srem(`ws:user:${user.id}`, sessionId);
        await this.redis.del(`ws:session:${sessionId}`);

        // Update device state
        const deviceKey = `sync:device:${user.id}:${platform}:${deviceId}`;
        await this.redis.hset(deviceKey, 'status', 'offline', 'last_seen', new Date().toISOString());

        console.log(`User ${user.username} disconnected from ${platform} (${deviceId})`);
    }

    /**
     * Handle WebSocket errors
     */
    handleError(sessionId, error) {
        console.error(`WebSocket error for session ${sessionId}:`, error);
        this.stats.errors++;
        this.handleClose(sessionId);
    }

    /**
     * Handle server errors
     */
    handleServerError(error) {
        console.error('WebSocket server error:', error);
        this.stats.errors++;
    }

    /**
     * Setup Redis pub/sub for cross-instance communication
     */
    async setupRedisPubSub() {
        // Subscribe to sync updates
        await this.redisSubscriber.psubscribe('sync:*');
        this.redisSubscriber.on('pmessage', async (pattern, channel, message) => {
            try {
                const data = JSON.parse(message);
                await this.handleRedisMessage(channel, data);
            } catch (error) {
                console.error('Error processing Redis message:', error);
            }
        });

        // Subscribe to conflict notifications
        await this.redisSubscriber.psubscribe('conflict:*');

        // Subscribe to system messages
        await this.redisSubscriber.subscribe('system:sync:status');
    }

    /**
     * Handle Redis pub/sub messages
     */
    async handleRedisMessage(channel, data) {
        try {
            if (channel.startsWith('sync:save:')) {
                const saveId = channel.replace('sync:save:', '');
                await this.broadcastToSubscribers(saveId, data);
            } else if (channel.startsWith('conflict:user:')) {
                const userId = channel.replace('conflict:user:', '');
                await this.broadcastToUser(userId, data);
            } else if (channel === 'system:sync:status') {
                await this.broadcastSystemStatus(data);
            }
        } catch (error) {
            console.error('Error handling Redis message:', error);
        }
    }

    /**
     * Send message to specific WebSocket session
     */
    sendMessage(sessionId, message) {
        const connectionInfo = this.connections.get(sessionId);
        if (connectionInfo && connectionInfo.ws.readyState === WebSocket.OPEN) {
            try {
                connectionInfo.ws.send(JSON.stringify(message));
                this.stats.messagesSent++;
            } catch (error) {
                console.error(`Failed to send message to session ${sessionId}:`, error);
            }
        }
    }

    /**
     * Send error message to client
     */
    sendError(sessionId, error) {
        this.sendMessage(sessionId, {
            type: 'error',
            error,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Broadcast message to all subscribers of a save game
     */
    async broadcastToSubscribers(saveId, message) {
        const subscribers = this.saveSubscriptions.get(saveId);
        if (!subscribers) return;

        const messageData = typeof message === 'string' ? message : JSON.stringify(message);

        subscribers.forEach(sessionId => {
            this.sendMessage(sessionId, JSON.parse(messageData));
        });
    }

    /**
     * Broadcast message to all sessions of a user
     */
    async broadcastToUser(userId, message) {
        const userSessions = this.userSessions.get(userId);
        if (!userSessions) return;

        userSessions.forEach(sessionId => {
            this.sendMessage(sessionId, message);
        });
    }

    /**
     * Queue message for offline user
     */
    async queueMessageForUser(userId, message) {
        if (!this.messageQueues.has(userId)) {
            this.messageQueues.set(userId, []);
        }

        const queue = this.messageQueues.get(userId);
        queue.push({
            id: uuid.v4(),
            message,
            timestamp: new Date(),
            ttl: Date.now() + (24 * 60 * 60 * 1000) // 24 hours
        });

        // Limit queue size
        if (queue.length > this.config.messageQueueSize) {
            queue.shift();
        }

        // Also store in Redis for persistence
        await this.redis.lpush(`queue:user:${userId}`, JSON.stringify({
            id: uuid.v4(),
            message,
            timestamp: new Date().toISOString()
        }));
        await this.redis.ltrim(`queue:user:${userId}`, 0, this.config.messageQueueSize - 1);
        await this.redis.expire(`queue:user:${userId}`, 86400); // 24 hours
    }

    /**
     * Process queued messages for user when they come online
     */
    async processQueuedMessages(userId) {
        // Process in-memory queue
        const queue = this.messageQueues.get(userId);
        if (queue) {
            const now = Date.now();
            const validMessages = queue.filter(item => item.ttl > now);

            validMessages.forEach(item => {
                this.broadcastToUser(userId, item.message);
            });

            this.messageQueues.set(userId, validMessages.filter(item => item.ttl > now));
        }

        // Process Redis queue
        const redisQueue = await this.redis.lrange(`queue:user:${userId}`, 0, -1);
        for (const messageData of redisQueue) {
            try {
                const item = JSON.parse(messageData);
                this.broadcastToUser(userId, item.message);
            } catch (error) {
                console.error('Error processing queued message:', error);
            }
        }

        // Clear Redis queue
        await this.redis.del(`queue:user:${userId}`);
    }

    /**
     * Acquire distributed lock for save operation
     */
    async acquireSaveLock(saveId, requester) {
        const lockKey = `lock:save:${saveId}`;
        const lockId = `${requester}:${Date.now()}`;

        const result = await this.redis.set(lockKey, lockId, 'PX', 30000, 'NX'); // 30 seconds
        return result === 'OK';
    }

    /**
     * Release distributed lock for save operation
     */
    async releaseSaveLock(saveId) {
        const lockKey = `lock:save:${saveId}`;
        await this.redis.del(lockKey);
    }

    /**
     * Handle conflict detection
     */
    async handleConflictDetection(sessionId, conflictData) {
        const connectionInfo = this.connections.get(sessionId);
        if (!connectionInfo) return;

        const conflictId = uuid.v4();

        // Store conflict in Redis
        await this.redis.hmset(`sync:conflict:${conflictId}`, {
            user_id: connectionInfo.user.id,
            save_game_id: conflictData.saveId,
            conflict_type: 'version_conflict',
            platform_a: conflictData.platform,
            platform_b: 'server',
            data_a: JSON.stringify(conflictData.clientData),
            data_b: '{}', // Would fetch server data
            detected_at: new Date().toISOString(),
            expires_at: new Date(Date.now() + 86400000).toISOString() // 24 hours
        });

        // Increment conflict counters
        await this.redis.hincrby(`sync:save:${conflictData.saveId}`, 'conflict_count', 1);
        await this.redis.hincrby(`sync:user:${connectionInfo.user.id}`, 'conflict_count', 1);

        this.stats.conflictsDetected++;

        // Notify client about conflict
        this.sendMessage(sessionId, {
            type: 'conflict_detected',
            conflictId,
            saveId: conflictData.saveId,
            conflictType: 'version_conflict',
            clientVersion: conflictData.clientVersion,
            serverVersion: conflictData.serverVersion,
            timestamp: new Date().toISOString()
        });

        // Publish conflict notification
        await this.redisPublisher.publish(`conflict:user:${connectionInfo.user.id}`, JSON.stringify({
            type: 'conflict_detected',
            conflictId,
            saveId: conflictData.saveId
        }));
    }

    /**
     * Apply conflict resolution
     */
    async applyConflictResolution(conflict, resolvedData, connectionInfo) {
        const saveId = conflict.save_game_id;
        const newVersion = parseInt(await this.redis.hget(`sync:save:${saveId}`, 'current_version')) + 1;

        // Store resolved data
        await this.redis.set(`sync:data:${saveId}:${newVersion}`, JSON.stringify(resolvedData));

        // Update save state
        await this.redis.hmset(`sync:save:${saveId}`, {
            current_version: newVersion,
            last_modified: new Date().toISOString(),
            checksum: crypto.createHash('sha256').update(JSON.stringify(resolvedData)).digest('hex')
        });

        // Notify all subscribers
        await this.redisPublisher.publish(`sync:save:${saveId}`, JSON.stringify({
            type: 'conflict_resolved',
            saveId,
            version: newVersion,
            resolvedBy: connectionInfo.platform,
            timestamp: new Date().toISOString()
        }));
    }

    /**
     * Notify about conflict resolution
     */
    async notifyConflictResolved(saveId, conflictId, resolution) {
        const notification = {
            type: 'conflict_resolved_notification',
            saveId,
            conflictId,
            resolution,
            timestamp: new Date().toISOString()
        };

        await this.redisPublisher.publish(`sync:save:${saveId}`, JSON.stringify(notification));
    }

    /**
     * Broadcast system status
     */
    async broadcastSystemStatus(status) {
        const message = {
            type: 'system_status',
            status,
            timestamp: new Date().toISOString()
        };

        this.connections.forEach((connectionInfo, sessionId) => {
            this.sendMessage(sessionId, message);
        });
    }

    /**
     * Start heartbeat monitoring
     */
    startHeartbeatMonitoring() {
        setInterval(() => {
            this.connections.forEach((connectionInfo, sessionId) => {
                if (!connectionInfo.isAlive) {
                    console.log(`Terminating inactive session: ${sessionId}`);
                    connectionInfo.ws.terminate();
                    this.handleClose(sessionId);
                } else {
                    connectionInfo.isAlive = false;
                    connectionInfo.ws.ping();
                }
            });
        }, this.config.heartbeat.interval);
    }

    /**
     * Start cleanup tasks
     */
    startCleanupTasks() {
        // Clean up expired conflicts every hour
        setInterval(async () => {
            try {
                const keys = await this.redis.keys('sync:conflict:*');
                for (const key of keys) {
                    const expiresAt = await this.redis.hget(key, 'expires_at');
                    if (expiresAt && new Date(expiresAt) < new Date()) {
                        await this.redis.del(key);
                    }
                }
            } catch (error) {
                console.error('Error cleaning up expired conflicts:', error);
            }
        }, 60 * 60 * 1000); // 1 hour

        // Clean up old sync data every day
        setInterval(async () => {
            try {
                const keys = await this.redis.keys('sync:data:*');
                for (const key of keys) {
                    const ttl = await this.redis.ttl(key);
                    if (ttl === -1) { // No expiry set
                        await this.redis.expire(key, 86400 * 7); // 7 days
                    }
                }
            } catch (error) {
                console.error('Error cleaning up old sync data:', error);
            }
        }, 24 * 60 * 60 * 1000); // 24 hours
    }

    /**
     * Get server statistics
     */
    getStats() {
        return {
            ...this.stats,
            activeConnections: this.connections.size,
            totalUsers: this.userSessions.size,
            totalSubscriptions: Array.from(this.saveSubscriptions.values())
                .reduce((sum, set) => sum + set.size, 0)
        };
    }

    /**
     * Graceful shutdown
     */
    async shutdown() {
        console.log('Shutting down WebSocket Gateway...');

        // Close all connections
        this.connections.forEach((connectionInfo, sessionId) => {
            connectionInfo.ws.close(1001, 'Server shutdown');
        });

        // Close Redis connections
        await this.redis.quit();
        await this.redisSubscriber.quit();
        await this.redisPublisher.quit();

        // Close WebSocket server
        this.wss.close();

        console.log('WebSocket Gateway shutdown complete');
    }
}

module.exports = WebSocketGateway;