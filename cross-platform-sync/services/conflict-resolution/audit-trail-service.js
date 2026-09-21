/**
 * DMlogn8n Cross-Platform Sync - Audit Trail Service
 * Comprehensive audit logging and compliance tracking for save synchronization
 */

const { Pool } = require('pg');
const Redis = require('ioredis');
const crypto = require('crypto');
const fs = require('fs').promises;
const path = require('path');
const zlib = require('zlib');
const { promisify } = require('util');

const gzip = promisify(zlib.gzip);
const gunzip = promisify(zlib.gunzip);

class AuditTrailService {
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
            audit: {
                logLevel: config.logLevel || 'info', // debug, info, warn, error
                retentionDays: config.retentionDays || 365,
                compressionEnabled: config.compressionEnabled !== false,
                fileLogging: config.fileLogging !== false,
                logDirectory: config.logDirectory || './audit-logs',
                enableRealTimeAlerts: config.enableRealTimeAlerts || false,
                alertThresholds: config.alertThresholds || {
                    failedSyncs: 5,
                    conflicts: 10,
                    suspiciousActivity: 3
                }
            }
        };

        // Database connection
        this.pool = new Pool(this.config.database);
        this.redis = new Redis(this.config.redis);

        // Audit buffers
        this.logBuffer = [];
        this.bufferSize = 100;
        this.flushInterval = 5000; // 5 seconds

        // Metrics
        this.metrics = {
            totalLogs: 0,
            logsToday: 0,
            errorsToday: 0,
            warningsToday: 0,
            alertsTriggered: 0
        };

        // Initialize
        this.initialize();
    }

    /**
     * Initialize the audit trail service
     */
    async initialize() {
        try {
            // Test database connection
            await this.pool.query('SELECT NOW()');
            await this.redis.ping();

            // Create log directory if file logging is enabled
            if (this.config.audit.fileLogging) {
                await this.ensureLogDirectory();
            }

            // Start buffer flush interval
            this.startBufferFlush();

            // Start daily metrics reset
            this.startDailyMetricsReset();

            // Load today's metrics
            await this.loadTodayMetrics();

            console.log('Audit Trail Service initialized');
        } catch (error) {
            console.error('Failed to initialize Audit Trail Service:', error);
            throw error;
        }
    }

    /**
     * Log an audit event
     */
    async logEvent(eventData) {
        try {
            const auditEvent = this.createAuditEvent(eventData);

            // Add to buffer
            this.logBuffer.push(auditEvent);

            // Update metrics
            this.updateMetrics(auditEvent);

            // Real-time alerts if enabled
            if (this.config.audit.enableRealTimeAlerts) {
                await this.checkAlertConditions(auditEvent);
            }

            // Immediate flush for critical events
            if (auditEvent.level === 'error' || auditEvent.level === 'critical') {
                await this.flushBuffer();
            }

            return auditEvent.id;

        } catch (error) {
            console.error('Failed to log audit event:', error);
            throw error;
        }
    }

    /**
     * Create a standardized audit event
     */
    createAuditEvent(eventData) {
        const event = {
            id: crypto.randomUUID(),
            timestamp: new Date().toISOString(),
            level: eventData.level || this.config.audit.logLevel,
            category: eventData.category || 'general',
            action: eventData.action,
            resourceType: eventData.resourceType,
            resourceId: eventData.resourceId,
            userId: eventData.userId,
            platform: eventData.platform,
            deviceId: eventData.deviceId,
            ipAddress: eventData.ipAddress,
            userAgent: eventData.userAgent,
            oldValues: eventData.oldValues,
            newValues: eventData.newValues,
            metadata: eventData.metadata || {},
            sessionId: eventData.sessionId,
            requestId: eventData.requestId,
            duration: eventData.duration,
            result: eventData.result,
            error: eventData.error,
            stackTrace: eventData.stackTrace
        };

        // Add hash for integrity verification
        event.hash = this.calculateEventHash(event);

        return event;
    }

    /**
     * Log sync operation
     */
    async logSyncOperation(data) {
        return this.logEvent({
            category: 'sync',
            action: data.action, // 'upload', 'download', 'merge'
            resourceType: 'save_game',
            resourceId: data.saveGameId,
            userId: data.userId,
            platform: data.platform,
            deviceId: data.deviceId,
            oldValues: data.oldVersion ? { version: data.oldVersion } : null,
            newValues: data.newVersion ? { version: data.newVersion } : null,
            metadata: {
                bytesTransferred: data.bytesTransferred,
                syncVersion: data.syncVersion,
                checksum: data.checksum,
                conflictDetected: data.conflictDetected
            },
            duration: data.duration,
            result: data.success ? 'success' : 'failure',
            error: data.error
        });
    }

    /**
     * Log conflict detection and resolution
     */
    async logConflict(data) {
        return this.logEvent({
            category: 'conflict',
            action: data.action, // 'detected', 'resolved', 'escalated'
            resourceType: 'sync_conflict',
            resourceId: data.conflictId,
            userId: data.userId,
            platform: data.platform,
            deviceId: data.deviceId,
            oldValues: data.oldData,
            newValues: data.newData,
            metadata: {
                conflictType: data.conflictType,
                fieldPath: data.fieldPath,
                platformA: data.platformA,
                platformB: data.platformB,
                resolutionStrategy: data.resolutionStrategy,
                autoResolved: data.autoResolved,
                severity: data.severity
            },
            duration: data.resolutionTime,
            result: data.success ? 'resolved' : 'failed',
            error: data.error
        });
    }

    /**
     * Log user authentication events
     */
    async logAuthentication(data) {
        return this.logEvent({
            category: 'auth',
            action: data.action, // 'login', 'logout', 'token_refresh', 'failed_login'
            resourceType: 'user',
            resourceId: data.userId,
            userId: data.userId,
            platform: data.platform,
            deviceId: data.deviceId,
            ipAddress: data.ipAddress,
            userAgent: data.userAgent,
            metadata: {
                authMethod: data.authMethod,
                mfaUsed: data.mfaUsed,
                sessionId: data.sessionId,
                tokenExpiry: data.tokenExpiry
            },
            result: data.success ? 'success' : 'failure',
            error: data.error
        });
    }

    /**
     * Log data access events
     */
    async logDataAccess(data) {
        return this.logEvent({
            category: 'data_access',
            action: data.action, // 'read', 'write', 'delete', 'export'
            resourceType: data.resourceType,
            resourceId: data.resourceId,
            userId: data.userId,
            platform: data.platform,
            deviceId: data.deviceId,
            oldValues: data.oldValues,
            newValues: data.newValues,
            metadata: {
                accessMethod: data.accessMethod,
                query: data.query,
                filter: data.filter,
                limit: data.limit,
                exportFormat: data.exportFormat
            },
            duration: data.duration,
            result: data.success ? 'success' : 'failure',
            error: data.error
        });
    }

    /**
     * Log system events
     */
    async logSystemEvent(data) {
        return this.logEvent({
            category: 'system',
            action: data.action, // 'startup', 'shutdown', 'error', 'maintenance'
            resourceType: data.resourceType || 'system',
            resourceId: data.resourceId,
            metadata: {
                component: data.component,
                version: data.version,
                environment: data.environment,
                metrics: data.metrics,
                config: data.config
            },
            level: data.level || 'info',
            error: data.error,
            stackTrace: data.stackTrace
        });
    }

    /**
     * Log security events
     */
    async logSecurityEvent(data) {
        return this.logEvent({
            category: 'security',
            action: data.action, // 'suspicious_activity', 'brute_force', 'data_breach_attempt'
            resourceType: data.resourceType,
            resourceId: data.resourceId,
            userId: data.userId,
            platform: data.platform,
            deviceId: data.deviceId,
            ipAddress: data.ipAddress,
            userAgent: data.userAgent,
            metadata: {
                threatType: data.threatType,
                riskScore: data.riskScore,
                blocked: data.blocked,
                ruleTriggered: data.ruleTriggered,
                additionalInfo: data.additionalInfo
            },
            level: 'warn',
            result: data.blocked ? 'blocked' : 'allowed',
            error: data.error
        });
    }

    /**
     * Flush the audit buffer to persistent storage
     */
    async flushBuffer() {
        if (this.logBuffer.length === 0) return;

        const events = [...this.logBuffer];
        this.logBuffer = [];

        try {
            // Store in database
            await this.storeEventsInDatabase(events);

            // Store in Redis for quick access
            await this.storeEventsInRedis(events);

            // Write to file if enabled
            if (this.config.audit.fileLogging) {
                await this.writeEventsToFile(events);
            }

            console.log(`Flushed ${events.length} audit events`);
        } catch (error) {
            console.error('Failed to flush audit buffer:', error);
            // Re-add events to buffer for retry
            this.logBuffer.unshift(...events);
        }
    }

    /**
     * Store events in PostgreSQL database
     */
    async storeEventsInDatabase(events) {
        const client = await this.pool.connect();

        try {
            await client.query('BEGIN');

            for (const event of events) {
                await client.query(`
                    INSERT INTO audit_log (
                        id, action, resource_type, resource_id, user_id,
                        old_values, new_values, platform, device_id,
                        ip_address, user_agent, created_at, metadata,
                        level, session_id, request_id, duration,
                        result, error, stack_trace, event_hash
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21)
                `, [
                    event.id,
                    event.action,
                    event.resourceType,
                    event.resourceId,
                    event.userId,
                    event.oldValues ? JSON.stringify(event.oldValues) : null,
                    event.newValues ? JSON.stringify(event.newValues) : null,
                    event.platform,
                    event.deviceId,
                    event.ipAddress,
                    event.userAgent,
                    event.timestamp,
                    JSON.stringify(event.metadata),
                    event.level,
                    event.sessionId,
                    event.requestId,
                    event.duration,
                    event.result,
                    event.error,
                    event.stackTrace,
                    event.hash
                ]);
            }

            await client.query('COMMIT');
        } catch (error) {
            await client.query('ROLLBACK');
            throw error;
        } finally {
            client.release();
        }
    }

    /**
     * Store events in Redis for quick access
     */
    async storeEventsInRedis(events) {
        const pipe = this.redis.pipeline();

        for (const event of events) {
            // Store by ID
            pipe.setex(`audit:event:${event.id}`, 86400, JSON.stringify(event)); // 24 hours

            // Store in daily list
            const dayKey = `audit:day:${event.timestamp.split('T')[0]}`;
            pipe.lpush(dayKey, event.id);
            pipe.expire(dayKey, 86400 * this.config.audit.retentionDays);

            // Store in user's daily list
            if (event.userId) {
                const userDayKey = `audit:user:${event.userId}:${event.timestamp.split('T')[0]}`;
                pipe.lpush(userDayKey, event.id);
                pipe.expire(userDayKey, 86400 * this.config.audit.retentionDays);
            }

            // Store by category
            const categoryKey = `audit:category:${event.category}`;
            pipe.lpush(categoryKey, event.id);
            pipe.expire(categoryKey, 86400 * 7); // 7 days

            // Store recent events for dashboard
            pipe.lpush('audit:recent', event.id);
            pipe.ltrim('audit:recent', 0, 999); // Keep last 1000
        }

        await pipe.exec();
    }

    /**
     * Write events to file
     */
    async writeEventsToFile(events) {
        const today = new Date().toISOString().split('T')[0];
        const logFile = path.join(this.config.audit.logDirectory, `audit-${today}.jsonl`);

        let logData = events.map(event => JSON.stringify(event)).join('\n') + '\n';

        // Compress if enabled
        if (this.config.audit.compressionEnabled) {
            logData = await gzip(logData);
            await fs.writeFile(`${logFile}.gz`, logData);
        } else {
            await fs.appendFile(logFile, logData);
        }
    }

    /**
     * Calculate event hash for integrity verification
     */
    calculateEventHash(event) {
        const hashData = {
            id: event.id,
            timestamp: event.timestamp,
            action: event.action,
            resourceType: event.resourceType,
            resourceId: event.resourceId,
            userId: event.userId,
            result: event.result
        };

        const dataString = JSON.stringify(hashData, Object.keys(hashData).sort());
        return crypto.createHash('sha256').update(dataString).digest('hex');
    }

    /**
     * Verify event integrity
     */
    async verifyEventIntegrity(eventId) {
        try {
            // Get event from Redis or database
            let event = await this.redis.get(`audit:event:${eventId}`);
            if (!event) {
                const result = await this.pool.query(
                    'SELECT * FROM audit_log WHERE id = $1',
                    [eventId]
                );
                if (result.rowCount === 0) {
                    return { valid: false, error: 'Event not found' };
                }
                event = result.rows[0];
            } else {
                event = JSON.parse(event);
            }

            // Recalculate hash
            const calculatedHash = this.calculateEventHash(event);
            const isValid = calculatedHash === event.hash;

            return {
                valid: isValid,
                originalHash: event.hash,
                calculatedHash,
                event
            };

        } catch (error) {
            console.error('Failed to verify event integrity:', error);
            return { valid: false, error: error.message };
        }
    }

    /**
     * Query audit events
     */
    async queryEvents(filters = {}, pagination = {}) {
        try {
            let query = `
                SELECT * FROM audit_log
                WHERE 1=1
            `;
            const params = [];
            let paramIndex = 1;

            // Apply filters
            if (filters.userId) {
                query += ` AND user_id = $${paramIndex}`;
                params.push(filters.userId);
                paramIndex++;
            }

            if (filters.category) {
                query += ` AND action LIKE $${paramIndex}`;
                params.push(`${filters.category}%`);
                paramIndex++;
            }

            if (filters.action) {
                query += ` AND action = $${paramIndex}`;
                params.push(filters.action);
                paramIndex++;
            }

            if (filters.resourceType) {
                query += ` AND resource_type = $${paramIndex}`;
                params.push(filters.resourceType);
                paramIndex++;
            }

            if (filters.resourceId) {
                query += ` AND resource_id = $${paramIndex}`;
                params.push(filters.resourceId);
                paramIndex++;
            }

            if (filters.level) {
                query += ` AND level = $${paramIndex}`;
                params.push(filters.level);
                paramIndex++;
            }

            if (filters.startDate) {
                query += ` AND created_at >= $${paramIndex}`;
                params.push(filters.startDate);
                paramIndex++;
            }

            if (filters.endDate) {
                query += ` AND created_at <= $${paramIndex}`;
                params.push(filters.endDate);
                paramIndex++;
            }

            if (filters.ipAddress) {
                query += ` AND ip_address = $${paramIndex}`;
                params.push(filters.ipAddress);
                paramIndex++;
            }

            // Add ordering
            query += ` ORDER BY created_at DESC`;

            // Add pagination
            const limit = pagination.limit || 100;
            const offset = pagination.offset || 0;

            query += ` LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
            params.push(limit, offset);

            const result = await this.pool.query(query, params);

            // Parse JSON fields
            const events = result.rows.map(row => ({
                ...row,
                oldValues: row.old_values ? JSON.parse(row.old_values) : null,
                newValues: row.new_values ? JSON.parse(row.new_values) : null,
                metadata: row.metadata ? JSON.parse(row.metadata) : null
            }));

            return {
                events,
                total: events.length,
                limit,
                offset
            };

        } catch (error) {
            console.error('Failed to query audit events:', error);
            throw error;
        }
    }

    /**
     * Get audit statistics
     */
    async getStatistics(filters = {}) {
        try {
            let query = `
                SELECT
                    COUNT(*) as total_events,
                    COUNT(*) FILTER (WHERE level = 'error') as error_count,
                    COUNT(*) FILTER (WHERE level = 'warn') as warning_count,
                    COUNT(*) FILTER (WHERE result = 'success') as success_count,
                    COUNT(*) FILTER (WHERE result = 'failure') as failure_count,
                    DATE_TRUNC('day', created_at) as date
                FROM audit_log
                WHERE created_at >= NOW() - INTERVAL '30 days'
            `;
            const params = [];
            let paramIndex = 1;

            // Apply filters
            if (filters.userId) {
                query += ` AND user_id = $${paramIndex}`;
                params.push(filters.userId);
                paramIndex++;
            }

            if (filters.category) {
                query += ` AND action LIKE $${paramIndex}`;
                params.push(`${filters.category}%`);
                paramIndex++;
            }

            query += ` GROUP BY DATE_TRUNC('day', created_at) ORDER BY date DESC`;

            const result = await this.pool.query(query, params);

            return {
                dailyStats: result.rows,
                totalEvents: result.rows.reduce((sum, row) => sum + parseInt(row.total_events), 0),
                totalErrors: result.rows.reduce((sum, row) => sum + parseInt(row.error_count), 0),
                totalWarnings: result.rows.reduce((sum, row) => sum + parseInt(row.warning_count), 0),
                successRate: result.rows.reduce((sum, row) => sum + parseInt(row.success_count), 0) /
                           result.rows.reduce((sum, row) => sum + parseInt(row.total_events), 0) * 100
            };

        } catch (error) {
            console.error('Failed to get audit statistics:', error);
            throw error;
        }
    }

    /**
     * Get user activity timeline
     */
    async getUserActivityTimeline(userId, days = 7) {
        try {
            const result = await this.pool.query(`
                SELECT
                    action,
                    resource_type,
                    resource_id,
                    created_at,
                    level,
                    result,
                    metadata
                FROM audit_log
                WHERE user_id = $1
                AND created_at >= NOW() - INTERVAL '${days} days'
                ORDER BY created_at DESC
            `, [userId]);

            return result.rows.map(row => ({
                action: row.action,
                resourceType: row.resource_type,
                resourceId: row.resource_id,
                timestamp: row.created_at,
                level: row.level,
                result: row.result,
                metadata: row.metadata ? JSON.parse(row.metadata) : null
            }));

        } catch (error) {
            console.error('Failed to get user activity timeline:', error);
            throw error;
        }
    }

    /**
     * Check for suspicious activity patterns
     */
    async detectSuspiciousActivity(userId) {
        try {
            const suspiciousPatterns = [];

            // Check for multiple failed logins
            const failedLogins = await this.pool.query(`
                SELECT COUNT(*) as count
                FROM audit_log
                WHERE user_id = $1
                AND action = 'failed_login'
                AND created_at >= NOW() - INTERVAL '1 hour'
            `, [userId]);

            if (parseInt(failedLogins.rows[0].count) >= 5) {
                suspiciousPatterns.push({
                    type: 'multiple_failed_logins',
                    count: failedLogins.rows[0].count,
                    severity: 'high'
                });
            }

            // Check for access from multiple IP addresses
            const uniqueIPs = await this.pool.query(`
                SELECT COUNT(DISTINCT ip_address) as ip_count
                FROM audit_log
                WHERE user_id = $1
                AND ip_address IS NOT NULL
                AND created_at >= NOW() - INTERVAL '24 hours'
            `, [userId]);

            if (parseInt(uniqueIPs.rows[0].ip_count) >= 3) {
                suspiciousPatterns.push({
                    type: 'multiple_ip_addresses',
                    count: uniqueIPs.rows[0].ip_count,
                    severity: 'medium'
                });
            }

            // Check for unusual access patterns (odd hours)
            const oddHourAccess = await this.pool.query(`
                SELECT COUNT(*) as count
                FROM audit_log
                WHERE user_id = $1
                AND EXTRACT(HOUR FROM created_at) BETWEEN 0 AND 5
                AND created_at >= NOW() - INTERVAL '7 days'
            `, [userId]);

            if (parseInt(oddHourAccess.rows[0].count) >= 10) {
                suspiciousPatterns.push({
                    type: 'unusual_access_hours',
                    count: oddHourAccess.rows[0].count,
                    severity: 'low'
                });
            }

            return suspiciousPatterns;

        } catch (error) {
            console.error('Failed to detect suspicious activity:', error);
            return [];
        }
    }

    /**
     * Generate compliance report
     */
    async generateComplianceReport(reportType, filters = {}) {
        try {
            switch (reportType) {
                case 'data_access':
                    return await this.generateDataAccessReport(filters);
                case 'user_activity':
                    return await this.generateUserActivityReport(filters);
                case 'security_incidents':
                    return await this.generateSecurityReport(filters);
                case 'sync_operations':
                    return await this.generateSyncReport(filters);
                default:
                    throw new Error(`Unknown report type: ${reportType}`);
            }
        } catch (error) {
            console.error('Failed to generate compliance report:', error);
            throw error;
        }
    }

    /**
     * Generate data access compliance report
     */
    async generateDataAccessReport(filters = {}) {
        const query = `
            SELECT
                user_id,
                COUNT(*) as access_count,
                COUNT(DISTINCT resource_id) as unique_resources,
                COUNT(*) FILTER (WHERE action = 'read') as reads,
                COUNT(*) FILTER (WHERE action = 'write') as writes,
                COUNT(*) FILTER (WHERE action = 'delete') as deletes,
                MIN(created_at) as first_access,
                MAX(created_at) as last_access
            FROM audit_log
            WHERE category = 'data_access'
            AND created_at >= $1
            AND created_at <= $2
            GROUP BY user_id
            ORDER BY access_count DESC
        `;

        const result = await this.pool.query(query, [
            filters.startDate || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
            filters.endDate || new Date()
        ]);

        return {
            reportType: 'data_access',
            period: { startDate: filters.startDate, endDate: filters.endDate },
            summary: {
                totalUsers: result.rowCount,
                totalAccess: result.rows.reduce((sum, row) => sum + parseInt(row.access_count), 0),
                totalReads: result.rows.reduce((sum, row) => sum + parseInt(row.reads), 0),
                totalWrites: result.rows.reduce((sum, row) => sum + parseInt(row.writes), 0),
                totalDeletes: result.rows.reduce((sum, row) => sum + parseInt(row.deletes), 0)
            },
            users: result.rows
        };
    }

    /**
     * Check alert conditions and trigger alerts
     */
    async checkAlertConditions(event) {
        const alerts = [];

        // Check failed sync threshold
        if (event.category === 'sync' && event.result === 'failure') {
            const recentFailures = await this.getRecentEventCount({
                category: 'sync',
                result: 'failure',
                minutes: 60
            });

            if (recentFailures >= this.config.audit.alertThresholds.failedSyncs) {
                alerts.push({
                    type: 'sync_failures',
                    severity: 'high',
                    message: `${recentFailures} sync failures in the last hour`,
                    count: recentFailures
                });
            }
        }

        // Check conflict threshold
        if (event.category === 'conflict') {
            const recentConflicts = await this.getRecentEventCount({
                category: 'conflict',
                minutes: 60
            });

            if (recentConflicts >= this.config.audit.alertThresholds.conflicts) {
                alerts.push({
                    type: 'conflicts',
                    severity: 'medium',
                    message: `${recentConflicts} conflicts detected in the last hour`,
                    count: recentConflicts
                });
            }
        }

        // Check for suspicious activity
        if (event.category === 'security') {
            const suspiciousActivity = await this.getRecentEventCount({
                category: 'security',
                minutes: 60
            });

            if (suspiciousActivity >= this.config.audit.alertThresholds.suspiciousActivity) {
                alerts.push({
                    type: 'security',
                    severity: 'critical',
                    message: `${suspiciousActivity} security events in the last hour`,
                    count: suspiciousActivity
                });
            }
        }

        // Trigger alerts
        for (const alert of alerts) {
            await this.triggerAlert(alert);
            this.metrics.alertsTriggered++;
        }
    }

    /**
     * Get recent event count
     */
    async getRecentEventCount(filters) {
        let query = `
            SELECT COUNT(*) as count
            FROM audit_log
            WHERE created_at >= NOW() - INTERVAL '${filters.minutes} minutes'
        `;
        const params = [];
        let paramIndex = 1;

        if (filters.category) {
            query += ` AND action LIKE $${paramIndex}`;
            params.push(`${filters.category}%`);
            paramIndex++;
        }

        if (filters.result) {
            query += ` AND result = $${paramIndex}`;
            params.push(filters.result);
            paramIndex++;
        }

        const result = await this.pool.query(query, params);
        return parseInt(result.rows[0].count);
    }

    /**
     * Trigger alert
     */
    async triggerAlert(alert) {
        try {
            // Store alert in database
            await this.pool.query(`
                INSERT INTO audit_alerts (type, severity, message, metadata, created_at)
                VALUES ($1, $2, $3, $4, NOW())
            `, [alert.type, alert.severity, alert.message, JSON.stringify(alert)]);

            // Publish to Redis for real-time notifications
            await this.redis.publish('audit:alert', JSON.stringify({
                ...alert,
                timestamp: new Date().toISOString()
            }));

            console.log(`ALERT: ${alert.severity.toUpperCase()} - ${alert.message}`);

        } catch (error) {
            console.error('Failed to trigger alert:', error);
        }
    }

    /**
     * Update metrics
     */
    updateMetrics(event) {
        this.metrics.totalLogs++;
        this.metrics.logsToday++;

        if (event.level === 'error') {
            this.metrics.errorsToday++;
        } else if (event.level === 'warn') {
            this.metrics.warningsToday++;
        }
    }

    /**
     * Load today's metrics from Redis
     */
    async loadTodayMetrics() {
        try {
            const today = new Date().toISOString().split('T')[0];
            const metrics = await this.redis.hgetall(`audit:metrics:${today}`);

            if (Object.keys(metrics).length > 0) {
                this.metrics.logsToday = parseInt(metrics.logsToday) || 0;
                this.metrics.errorsToday = parseInt(metrics.errorsToday) || 0;
                this.metrics.warningsToday = parseInt(metrics.warningsToday) || 0;
                this.metrics.alertsTriggered = parseInt(metrics.alertsTriggered) || 0;
            }
        } catch (error) {
            console.error('Failed to load today\'s metrics:', error);
        }
    }

    /**
     * Start buffer flush interval
     */
    startBufferFlush() {
        setInterval(() => {
            if (this.logBuffer.length > 0) {
                this.flushBuffer();
            }
        }, this.config.flushInterval);
    }

    /**
     * Start daily metrics reset
     */
    startDailyMetricsReset() {
        const now = new Date();
        const tomorrow = new Date(now);
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(0, 0, 0, 0);

        const msUntilMidnight = tomorrow - now;

        setTimeout(() => {
            this.resetDailyMetrics();
            // Schedule to run every day at midnight
            setInterval(this.resetDailyMetrics.bind(this), 24 * 60 * 60 * 1000);
        }, msUntilMidnight);
    }

    /**
     * Reset daily metrics
     */
    resetDailyMetrics() {
        const today = new Date().toISOString().split('T')[0];

        // Save today's metrics to Redis
        this.redis.hmset(`audit:metrics:${today}`, {
            logsToday: this.metrics.logsToday,
            errorsToday: this.metrics.errorsToday,
            warningsToday: this.metrics.warningsToday,
            alertsTriggered: this.metrics.alertsTriggered
        });

        // Reset metrics
        this.metrics.logsToday = 0;
        this.metrics.errorsToday = 0;
        this.metrics.warningsToday = 0;
        this.metrics.alertsTriggered = 0;

        console.log('Daily audit metrics reset');
    }

    /**
     * Ensure log directory exists
     */
    async ensureLogDirectory() {
        try {
            await fs.mkdir(this.config.audit.logDirectory, { recursive: true });
        } catch (error) {
            console.error('Failed to create log directory:', error);
            throw error;
        }
    }

    /**
     * Cleanup old audit logs
     */
    async cleanupOldLogs() {
        try {
            const cutoffDate = new Date();
            cutoffDate.setDate(cutoffDate.getDate() - this.config.audit.retentionDays);

            // Clean up database
            const result = await this.pool.query(`
                DELETE FROM audit_log
                WHERE created_at < $1
            `, [cutoffDate]);

            console.log(`Cleaned up ${result.rowCount} old audit records from database`);

            // Clean up Redis
            const keys = await this.redis.keys('audit:*');
            for (const key of keys) {
                const ttl = await this.redis.ttl(key);
                if (ttl === -1) { // No expiry set
                    await this.redis.expire(key, 86400 * 7); // 7 days
                }
            }

            // Clean up old log files
            if (this.config.audit.fileLogging) {
                const files = await fs.readdir(this.config.audit.logDirectory);
                for (const file of files) {
                    const filePath = path.join(this.config.audit.logDirectory, file);
                    const stats = await fs.stat(filePath);
                    if (stats.mtime < cutoffDate) {
                        await fs.unlink(filePath);
                        console.log(`Deleted old audit log file: ${file}`);
                    }
                }
            }

        } catch (error) {
            console.error('Failed to cleanup old audit logs:', error);
        }
    }

    /**
     * Get current metrics
     */
    getMetrics() {
        return { ...this.metrics };
    }

    /**
     * Export audit data
     */
    async exportData(filters = {}, format = 'json') {
        try {
            const events = await this.queryEvents(filters, { limit: 10000 });

            switch (format.toLowerCase()) {
                case 'json':
                    return JSON.stringify(events, null, 2);
                case 'csv':
                    return this.convertToCSV(events.events);
                case 'xml':
                    return this.convertToXML(events.events);
                default:
                    throw new Error(`Unsupported export format: ${format}`);
            }
        } catch (error) {
            console.error('Failed to export audit data:', error);
            throw error;
        }
    }

    /**
     * Convert events to CSV format
     */
    convertToCSV(events) {
        const headers = [
            'id', 'timestamp', 'level', 'category', 'action', 'resourceType',
            'resourceId', 'userId', 'platform', 'deviceId', 'result'
        ];

        const csvLines = [headers.join(',')];

        for (const event of events) {
            const row = [
                event.id,
                event.created_at,
                event.level,
                event.action,
                event.resource_type,
                event.resource_id,
                event.user_id,
                event.platform,
                event.device_id,
                event.result
            ];

            csvLines.push(row.map(field => `"${field || ''}"`).join(','));
        }

        return csvLines.join('\n');
    }

    /**
     * Convert events to XML format
     */
    convertToXML(events) {
        let xml = '<?xml version="1.0" encoding="UTF-8"?>\n<audit_events>\n';

        for (const event of events) {
            xml += '  <event>\n';
            xml += `    <id>${event.id}</id>\n`;
            xml += `    <timestamp>${event.created_at}</timestamp>\n`;
            xml += `    <level>${event.level}</level>\n`;
            xml += `    <action>${event.action}</action>\n`;
            xml += `    <resource_type>${event.resource_type}</resource_type>\n`;
            xml += `    <resource_id>${event.resource_id}</resource_id>\n`;
            xml += `    <user_id>${event.user_id}</user_id>\n`;
            xml += `    <platform>${event.platform}</platform>\n`;
            xml += `    <device_id>${event.device_id}</device_id>\n`;
            xml += `    <result>${event.result}</result>\n`;
            xml += '  </event>\n';
        }

        xml += '</audit_events>';
        return xml;
    }

    /**
     * Shutdown the audit trail service
     */
    async shutdown() {
        console.log('Shutting down Audit Trail Service...');

        // Flush remaining buffer
        await this.flushBuffer();

        await this.pool.end();
        await this.redis.quit();

        console.log('Audit Trail Service shutdown complete');
    }
}

module.exports = AuditTrailService;