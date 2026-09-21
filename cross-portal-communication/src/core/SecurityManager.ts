import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import crypto from 'crypto';
import {
  User,
  UserRole,
  Message,
  AuditLog,
  RateLimitInfo,
  EncryptionKeys
} from '@/types';
import { EventEmitter } from 'events';
import { Logger } from '@/utils/logger';
import config from '@/config/config';

export interface Permission {
  id: string;
  name: string;
  description: string;
  resource: string;
  action: string;
  roles: UserRole[];
}

export interface SecurityPolicy {
  maxLoginAttempts: number;
  lockoutDuration: number;
  sessionTimeout: number;
  passwordMinLength: number;
  requireSpecialChars: boolean;
  encryptionAlgorithm: string;
  keyRotationInterval: number;
  auditLogRetention: number;
}

export interface RateLimitConfig {
  windowMs: number;
  maxRequests: number;
  skipSuccessfulRequests: boolean;
  skipFailedRequests: boolean;
}

export interface SecurityContext {
  userId: string;
  role: UserRole;
  permissions: string[];
  sessionId: string;
  ipAddress: string;
  userAgent: string;
  timestamp: Date;
}

export class SecurityManager extends EventEmitter {
  private encryptionKeys: Map<string, EncryptionKeys>;
  private rateLimits: Map<string, RateLimitInfo>;
  private auditLogs: AuditLog[];
  private loginAttempts: Map<string, { count: number; lastAttempt: Date; lockedUntil?: Date }>;
  private activeSessions: Map<string, SecurityContext>;
  private permissions: Map<string, Permission>;
  private policy: SecurityPolicy;
  private logger: Logger;
  private currentKeyId: string;

  constructor() {
    super();
    this.encryptionKeys = new Map();
    this.rateLimits = new Map();
    this.auditLogs = [];
    this.loginAttempts = new Map();
    this.activeSessions = new Map();
    this.permissions = new Map();
    this.logger = new Logger('SecurityManager');
    this.currentKeyId = '';

    this.policy = {
      maxLoginAttempts: 5,
      lockoutDuration: 15 * 60 * 1000, // 15 minutes
      sessionTimeout: 24 * 60 * 60 * 1000, // 24 hours
      passwordMinLength: 8,
      requireSpecialChars: true,
      encryptionAlgorithm: 'aes-256-gcm',
      keyRotationInterval: 30 * 24 * 60 * 60 * 1000, // 30 days
      auditLogRetention: 90 * 24 * 60 * 60 * 1000 // 90 days
    };

    this.initializePermissions();
    this.generateInitialKey();
    this.startKeyRotation();
    this.startSessionCleanup();
    this.startAuditLogCleanup();
  }

  // Authentication & Authorization
  public async authenticateUser(
    username: string,
    password: string,
    ipAddress: string,
    userAgent: string
  ): Promise<{ success: boolean; token?: string; user?: User; error?: string }> {
    try {
      // Check login attempts
      const attemptInfo = this.loginAttempts.get(username);
      if (attemptInfo && attemptInfo.lockedUntil && attemptInfo.lockedUntil > new Date()) {
        this.logSecurityEvent('login_blocked', 'user', username, {
          reason: 'account_locked',
          ipAddress,
          userAgent
        });
        return { success: false, error: 'Account temporarily locked due to too many failed attempts' };
      }

      // This would typically query a database - for demo purposes we'll simulate
      const user = await this.getUserByUsername(username);
      if (!user) {
        this.recordFailedAttempt(username);
        return { success: false, error: 'Invalid credentials' };
      }

      const isPasswordValid = await bcrypt.compare(password, user.password || '');
      if (!isPasswordValid) {
        this.recordFailedAttempt(username);
        this.logSecurityEvent('login_failed', 'user', username, {
          ipAddress,
          userAgent
        });
        return { success: false, error: 'Invalid credentials' };
      }

      // Clear failed attempts on successful login
      this.loginAttempts.delete(username);

      // Generate JWT token
      const token = this.generateToken(user);

      // Create security context
      const securityContext: SecurityContext = {
        userId: user.id,
        role: user.role,
        permissions: this.getUserPermissions(user.role),
        sessionId: user.sessionId,
        ipAddress,
        userAgent,
        timestamp: new Date()
      };

      this.activeSessions.set(user.sessionId, securityContext);

      this.logSecurityEvent('login_success', 'user', username, {
        ipAddress,
        userAgent,
        sessionId: user.sessionId
      });

      return { success: true, token, user };
    } catch (error) {
      this.logger.error(`Authentication error: ${error.message}`);
      return { success: false, error: 'Authentication failed' };
    }
  }

  public async validateToken(token: string): Promise<SecurityContext | null> {
    try {
      const decoded = jwt.verify(token, config.security.jwtSecret) as any;
      const session = this.activeSessions.get(decoded.sessionId);

      if (!session) {
        this.logSecurityEvent('session_not_found', 'session', decoded.sessionId);
        return null;
      }

      // Check session timeout
      const now = new Date();
      const sessionAge = now.getTime() - session.timestamp.getTime();
      if (sessionAge > this.policy.sessionTimeout) {
        this.activeSessions.delete(decoded.sessionId);
        this.logSecurityEvent('session_expired', 'session', decoded.sessionId);
        return null;
      }

      // Update session timestamp
      session.timestamp = now;
      this.activeSessions.set(decoded.sessionId, session);

      return session;
    } catch (error) {
      this.logSecurityEvent('token_validation_failed', 'token', 'unknown', {
        error: error.message
      });
      return null;
    }
  }

  public hasPermission(context: SecurityContext, resource: string, action: string): boolean {
    // System role has all permissions
    if (context.role === UserRole.SYSTEM) {
      return true;
    }

    // Check direct permissions
    if (context.permissions.includes(`${resource}:${action}`)) {
      return true;
    }

    // Check role-based permissions
    for (const [permissionId, permission] of this.permissions.entries()) {
      if (permission.resource === resource &&
          permission.action === action &&
          permission.roles.includes(context.role)) {
        return true;
      }
    }

    this.logSecurityEvent('permission_denied', 'user', context.userId, {
      resource,
      action,
      role: context.role
    });

    return false;
  }

  public async authorizeMessage(context: SecurityContext, message: Message): Promise<boolean> {
    // Check if user can send to this channel
    if (!this.hasPermission(context, 'channel', `write:${message.channel}`)) {
      return false;
    }

    // Check message content for security issues
    if (this.containsMaliciousContent(message.content)) {
      this.logSecurityEvent('malicious_message_blocked', 'user', context.userId, {
        messageId: message.id,
        content: message.content.substring(0, 100)
      });
      return false;
    }

    // Check rate limiting
    if (this.isRateLimited(context.userId)) {
      this.logSecurityEvent('rate_limit_exceeded', 'user', context.userId);
      return false;
    }

    // Check message size
    const messageSize = JSON.stringify(message).length;
    if (messageSize > config.messaging.maxMessageSize) {
      this.logSecurityEvent('message_too_large', 'user', context.userId, {
        messageId: message.id,
        size: messageSize
      });
      return false;
    }

    return true;
  }

  // Encryption & Decryption
  public async encryptMessage(message: Message, channelId: string): Promise<Message> {
    const channelKey = this.getChannelEncryptionKey(channelId);
    if (!channelKey) {
      return message;
    }

    const cipher = crypto.createCipher(this.policy.encryptionAlgorithm, channelKey.publicKey);
    let encryptedContent = cipher.update(message.content, 'utf8', 'hex');
    encryptedContent += cipher.final('hex');

    const encryptedMessage: Message = {
      ...message,
      content: '[Encrypted]',
      encrypted: true,
      encryptedContent
    };

    this.logSecurityEvent('message_encrypted', 'message', message.id, {
      channelId
    });

    return encryptedMessage;
  }

  public async decryptMessage(message: Message, channelId: string): Promise<Message> {
    if (!message.encrypted || !message.encryptedContent) {
      return message;
    }

    const channelKey = this.getChannelEncryptionKey(channelId);
    if (!channelKey) {
      return message;
    }

    try {
      const decipher = crypto.createDecipher(this.policy.encryptionAlgorithm, channelKey.publicKey);
      let decryptedContent = decipher.update(message.encryptedContent, 'hex', 'utf8');
      decryptedContent += decipher.final('utf8');

      const decryptedMessage: Message = {
        ...message,
        content: decryptedContent,
        encryptedContent: undefined
      };

      return decryptedMessage;
    } catch (error) {
      this.logger.error(`Decryption failed for message ${message.id}: ${error.message}`);
      return message;
    }
  }

  // Rate Limiting
  public isRateLimited(userId: string): boolean {
    const rateLimit = this.rateLimits.get(userId);
    if (!rateLimit) {
      return false;
    }

    const now = new Date();
    if (now > rateLimit.resetTime) {
      this.rateLimits.delete(userId);
      return false;
    }

    return rateLimit.remaining <= 0;
  }

  public checkRateLimit(userId: string): RateLimitInfo {
    let rateLimit = this.rateLimits.get(userId);

    if (!rateLimit || new Date() > rateLimit.resetTime) {
      rateLimit = {
        count: 0,
        remaining: config.security.rateLimitMax,
        resetTime: new Date(Date.now() + config.security.rateLimitWindowMs),
        windowMs: config.security.rateLimitWindowMs
      };
      this.rateLimits.set(userId, rateLimit);
    }

    rateLimit.count++;
    rateLimit.remaining = Math.max(0, rateLimit.remaining - 1);

    return rateLimit;
  }

  // Audit Logging
  public logSecurityEvent(
    action: string,
    resourceType: string,
    resourceId: string,
    details: Record<string, any> = {},
    success: boolean = true,
    errorMessage?: string
  ): void {
    const auditLog: AuditLog = {
      id: crypto.randomUUID(),
      userId: details.userId || 'system',
      action,
      resource: `${resourceType}:${resourceId}`,
      details,
      timestamp: new Date(),
      ip: details.ipAddress,
      userAgent: details.userAgent,
      success,
      errorMessage
    };

    this.auditLogs.push(auditLog);

    // Maintain log retention limit
    if (this.auditLogs.length > 10000) {
      this.auditLogs = this.auditLogs.slice(-5000);
    }

    this.logger.info(`Security event: ${action} on ${resourceType}:${resourceId}`, {
      success,
      details
    });

    this.emit('securityEvent', auditLog);
  }

  public getAuditLogs(filter: {
    userId?: string;
    action?: string;
    resource?: string;
    startTime?: Date;
    endTime?: Date;
    limit?: number;
  } = {}): AuditLog[] {
    let logs = [...this.auditLogs];

    if (filter.userId) {
      logs = logs.filter(log => log.userId === filter.userId);
    }

    if (filter.action) {
      logs = logs.filter(log => log.action === filter.action);
    }

    if (filter.resource) {
      logs = logs.filter(log => log.resource.includes(filter.resource));
    }

    if (filter.startTime) {
      logs = logs.filter(log => log.timestamp >= filter.startTime!);
    }

    if (filter.endTime) {
      logs = logs.filter(log => log.timestamp <= filter.endTime!);
    }

    // Sort by timestamp (newest first)
    logs.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

    const limit = filter.limit || 100;
    return logs.slice(0, limit);
  }

  // Key Management
  private generateInitialKey(): void {
    const keyPair = this.generateKeyPair();
    this.currentKeyId = keyPair.keyId;
    this.encryptionKeys.set(keyPair.keyId, keyPair);

    this.logSecurityEvent('key_generated', 'encryption', keyPair.keyId);
  }

  private generateKeyPair(): EncryptionKeys {
    const keyPair = crypto.generateKeyPairSync('rsa', {
      modulusLength: 2048,
      publicKeyEncoding: { type: 'spki', format: 'pem' },
      privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
    });

    return {
      publicKey: keyPair.publicKey,
      privateKey: keyPair.privateKey,
      keyId: crypto.randomUUID(),
      createdAt: new Date(),
      expiresAt: new Date(Date.now() + this.policy.keyRotationInterval)
    };
  }

  private startKeyRotation(): void {
    setInterval(() => {
      this.rotateKeys();
    }, this.policy.keyRotationInterval);
  }

  private rotateKeys(): void {
    const newKeyPair = this.generateKeyPair();
    const oldKeyId = this.currentKeyId;

    this.currentKeyId = newKeyPair.keyId;
    this.encryptionKeys.set(newKeyPair.keyId, newKeyPair);

    this.logSecurityEvent('key_rotated', 'encryption', oldKeyId, {
      newKeyId: newKeyPair.keyId
    });

    // Archive old key (don't delete immediately for decryption of old messages)
    setTimeout(() => {
      this.encryptionKeys.delete(oldKeyId);
      this.logSecurityEvent('key_retired', 'encryption', oldKeyId);
    }, this.policy.keyRotationInterval);
  }

  private getChannelEncryptionKey(channelId: string): EncryptionKeys | null {
    // For demo purposes, return current key
    // In production, this would be channel-specific
    return this.encryptionKeys.get(this.currentKeyId) || null;
  }

  // Permission Management
  private initializePermissions(): void {
    const defaultPermissions: Permission[] = [
      {
        id: 'channel:read:party',
        name: 'Read Party Channel',
        description: 'Read messages in the party chat channel',
        resource: 'channel',
        action: 'read:party',
        roles: [UserRole.DM, UserRole.PLAYER, UserRole.CODER, UserRole.SPECTATOR]
      },
      {
        id: 'channel:write:party',
        name: 'Write to Party Channel',
        description: 'Send messages to the party chat channel',
        resource: 'channel',
        action: 'write:party',
        roles: [UserRole.DM, UserRole.PLAYER, UserRole.CODER]
      },
      {
        id: 'channel:read:dm',
        name: 'Read DM Channel',
        description: 'Read messages in the DM-only channel',
        resource: 'channel',
        action: 'read:dm-whisper',
        roles: [UserRole.DM]
      },
      {
        id: 'channel:write:dm',
        name: 'Write to DM Channel',
        description: 'Send messages to the DM-only channel',
        resource: 'channel',
        action: 'write:dm-whisper',
        roles: [UserRole.DM]
      },
      {
        id: 'channel:read:coder',
        name: 'Read Coder Channel',
        description: 'Read messages in the coder channel',
        resource: 'channel',
        action: 'read:coder',
        roles: [UserRole.DM, UserRole.CODER]
      },
      {
        id: 'channel:write:coder',
        name: 'Write to Coder Channel',
        description: 'Send messages to the coder channel',
        resource: 'channel',
        action: 'write:coder',
        roles: [UserRole.DM, UserRole.CODER]
      },
      {
        id: 'message:delete',
        name: 'Delete Messages',
        description: 'Delete messages from channels',
        resource: 'message',
        action: 'delete',
        roles: [UserRole.DM]
      },
      {
        id: 'user:manage',
        name: 'Manage Users',
        description: 'Manage user accounts and permissions',
        resource: 'user',
        action: 'manage',
        roles: [UserRole.DM]
      },
      {
        id: 'system:configure',
        name: 'Configure System',
        description: 'Configure system settings and policies',
        resource: 'system',
        action: 'configure',
        roles: [UserRole.DM]
      }
    ];

    for (const permission of defaultPermissions) {
      this.permissions.set(permission.id, permission);
    }
  }

  private getUserPermissions(role: UserRole): string[] {
    const permissions: string[] = [];

    for (const [permissionId, permission] of this.permissions.entries()) {
      if (permission.roles.includes(role)) {
        permissions.push(permissionId);
      }
    }

    return permissions;
  }

  // Helper Methods
  private generateToken(user: User): string {
    const payload = {
      userId: user.id,
      username: user.username,
      role: user.role,
      sessionId: user.sessionId,
      iat: Math.floor(Date.now() / 1000)
    };

    return jwt.sign(payload, config.security.jwtSecret, {
      expiresIn: config.security.jwtExpiration
    });
  }

  private async getUserByUsername(username: string): Promise<User | null> {
    // This would typically query a database
    // For demo purposes, return a mock user
    if (username === 'dm' || username === 'player' || username === 'coder') {
      const role = username === 'dm' ? UserRole.DM :
                   username === 'player' ? UserRole.PLAYER : UserRole.CODER;

      return {
        id: crypto.randomUUID(),
        username,
        role,
        portal: 'dm-portal' as any,
        permissions: this.getUserPermissions(role),
        isOnline: true,
        lastSeen: new Date(),
        sessionId: crypto.randomUUID(),
        password: await bcrypt.hash('password', config.security.bcryptRounds)
      };
    }

    return null;
  }

  private recordFailedAttempt(username: string): void {
    const attempt = this.loginAttempts.get(username) || { count: 0, lastAttempt: new Date() };
    attempt.count++;
    attempt.lastAttempt = new Date();

    if (attempt.count >= this.policy.maxLoginAttempts) {
      attempt.lockedUntil = new Date(Date.now() + this.policy.lockoutDuration);
      this.logSecurityEvent('account_locked', 'user', username, {
        attempts: attempt.count,
        lockedUntil: attempt.lockedUntil
      });
    }

    this.loginAttempts.set(username, attempt);
  }

  private containsMaliciousContent(content: string): boolean {
    const maliciousPatterns = [
      /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
      /javascript:/gi,
      /on\w+\s*=/gi,
      /eval\s*\(/gi,
      /document\.cookie/gi,
      /window\.location/gi
    ];

    return maliciousPatterns.some(pattern => pattern.test(content));
  }

  private startSessionCleanup(): void {
    setInterval(() => {
      this.cleanupExpiredSessions();
    }, 60 * 60 * 1000); // Every hour
  }

  private cleanupExpiredSessions(): void {
    const now = new Date();
    let cleanedCount = 0;

    for (const [sessionId, session] of this.activeSessions.entries()) {
      const sessionAge = now.getTime() - session.timestamp.getTime();
      if (sessionAge > this.policy.sessionTimeout) {
        this.activeSessions.delete(sessionId);
        cleanedCount++;
      }
    }

    if (cleanedCount > 0) {
      this.logSecurityEvent('sessions_cleaned', 'system', 'session_cleanup', {
        cleanedCount
      });
    }
  }

  private startAuditLogCleanup(): void {
    setInterval(() => {
      this.cleanupOldAuditLogs();
    }, 24 * 60 * 60 * 1000); // Daily
  }

  private cleanupOldAuditLogs(): void {
    const cutoffDate = new Date(Date.now() - this.policy.auditLogRetention);
    const initialCount = this.auditLogs.length;

    this.auditLogs = this.auditLogs.filter(log => log.timestamp > cutoffDate);

    const cleanedCount = initialCount - this.auditLogs.length;
    if (cleanedCount > 0) {
      this.logSecurityEvent('audit_logs_cleaned', 'system', 'audit_cleanup', {
        cleanedCount,
        cutoffDate
      });
    }
  }

  // Statistics and Monitoring
  public getSecurityStatistics(): {
    activeSessions: number;
    rateLimitedUsers: number;
    lockedAccounts: number;
    auditLogCount: number;
    activeEncryptionKeys: number;
    recentSecurityEvents: number;
  } {
    const now = new Date();
    const recentThreshold = new Date(now.getTime() - 24 * 60 * 60 * 1000); // 24 hours

    return {
      activeSessions: this.activeSessions.size,
      rateLimitedUsers: Array.from(this.rateLimits.values()).filter(
        rl => rl.remaining <= 0
      ).length,
      lockedAccounts: Array.from(this.loginAttempts.values()).filter(
        attempt => attempt.lockedUntil && attempt.lockedUntil > now
      ).length,
      auditLogCount: this.auditLogs.length,
      activeEncryptionKeys: this.encryptionKeys.size,
      recentSecurityEvents: this.auditLogs.filter(
        log => log.timestamp > recentThreshold
      ).length
    };
  }

  public invalidateSession(sessionId: string): boolean {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      return false;
    }

    this.activeSessions.delete(sessionId);
    this.logSecurityEvent('session_invalidated', 'session', sessionId, {
      userId: session.userId
    });

    return true;
  }

  public invalidateAllUserSessions(userId: string): number {
    let invalidatedCount = 0;

    for (const [sessionId, session] of this.activeSessions.entries()) {
      if (session.userId === userId) {
        this.activeSessions.delete(sessionId);
        invalidatedCount++;
      }
    }

    if (invalidatedCount > 0) {
      this.logSecurityEvent('user_sessions_invalidated', 'user', userId, {
        invalidatedCount
      });
    }

    return invalidatedCount;
  }
}