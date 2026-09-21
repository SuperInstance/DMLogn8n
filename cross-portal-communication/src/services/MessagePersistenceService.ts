import mongoose, { Schema, Document, Model } from 'mongoose';
import {
  Message,
  AuditLog,
  Channel,
  User,
  MessageFilter,
  MessageStatistics
} from '@/types';
import { Logger } from '@/utils/logger';
import config from '@/config/config';

// MongoDB Schemas
interface IMessageDocument extends Document {
  id: string;
  type: string;
  priority: number;
  channel: string;
  sender: string;
  recipients: string[];
  content: string;
  metadata: Record<string, any>;
  timestamp: Date;
  encrypted: boolean;
  encryptedContent?: string;
  ttl?: number;
  archivedAt?: Date;
  deletedAt?: Date;
}

interface IAuditLogDocument extends Document {
  id: string;
  userId: string;
  action: string;
  resource: string;
  details: Record<string, any>;
  timestamp: Date;
  ip?: string;
  userAgent?: string;
  success: boolean;
  errorMessage?: string;
}

interface IChannelDocument extends Document {
  id: string;
  name: string;
  type: string;
  members: string[];
  permissions: {
    read: string[];
    write: string[];
    moderate: string[];
  };
  isPrivate: boolean;
  isEncrypted: boolean;
  metadata: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
  archivedAt?: Date;
}

interface IUserDocument extends Document {
  id: string;
  username: string;
  role: string;
  portal: string;
  characterId?: string;
  permissions: string[];
  isOnline: boolean;
  lastSeen: Date;
  sessionId: string;
  createdAt: Date;
  updatedAt: Date;
}

// Schema Definitions
const MessageSchema = new Schema<IMessageDocument>({
  id: { type: String, required: true, unique: true },
  type: { type: String, required: true, index: true },
  priority: { type: Number, required: true, index: true },
  channel: { type: String, required: true, index: true },
  sender: { type: String, required: true, index: true },
  recipients: [{ type: String, index: true }],
  content: { type: String, required: true },
  metadata: { type: Schema.Types.Mixed, default: {} },
  timestamp: { type: Date, required: true, index: true },
  encrypted: { type: Boolean, default: false },
  encryptedContent: { type: String },
  ttl: { type: Number },
  archivedAt: { type: Date },
  deletedAt: { type: Date }
}, {
  timestamps: true,
  collection: 'messages'
});

const AuditLogSchema = new Schema<IAuditLogDocument>({
  id: { type: String, required: true, unique: true },
  userId: { type: String, required: true, index: true },
  action: { type: String, required: true, index: true },
  resource: { type: String, required: true, index: true },
  details: { type: Schema.Types.Mixed, default: {} },
  timestamp: { type: Date, required: true, index: true },
  ip: { type: String },
  userAgent: { type: String },
  success: { type: Boolean, required: true },
  errorMessage: { type: String }
}, {
  timestamps: true,
  collection: 'audit_logs'
});

const ChannelSchema = new Schema<IChannelDocument>({
  id: { type: String, required: true, unique: true },
  name: { type: String, required: true },
  type: { type: String, required: true, index: true },
  members: [{ type: String, index: true }],
  permissions: {
    read: [{ type: String }],
    write: [{ type: String }],
    moderate: [{ type: String }]
  },
  isPrivate: { type: Boolean, default: false },
  isEncrypted: { type: Boolean, default: false },
  metadata: { type: Schema.Types.Mixed, default: {} },
  archivedAt: { type: Date }
}, {
  timestamps: true,
  collection: 'channels'
});

const UserSchema = new Schema<IUserDocument>({
  id: { type: String, required: true, unique: true },
  username: { type: String, required: true, index: true },
  role: { type: String, required: true, index: true },
  portal: { type: String, required: true, index: true },
  characterId: { type: String, index: true },
  permissions: [{ type: String }],
  isOnline: { type: Boolean, default: false, index: true },
  lastSeen: { type: Date, required: true },
  sessionId: { type: String, required: true, index: true }
}, {
  timestamps: true,
  collection: 'users'
});

// Indexes for performance optimization
MessageSchema.index({ channel: 1, timestamp: -1 });
MessageSchema.index({ sender: 1, timestamp: -1 });
MessageSchema.index({ recipients: 1, timestamp: -1 });
MessageSchema.index({ type: 1, timestamp: -1 });
MessageSchema.index({ priority: 1, timestamp: -1 });

AuditLogSchema.index({ userId: 1, timestamp: -1 });
AuditLogSchema.index({ action: 1, timestamp: -1 });
AuditLogSchema.index({ resource: 1, timestamp: -1 });
AuditLogSchema.index({ timestamp: -1 });

ChannelSchema.index({ type: 1 });
ChannelSchema.index({ members: 1 });

UserSchema.index({ username: 1 });
UserSchema.index({ role: 1, portal: 1 });
UserSchema.index({ isOnline: 1 });
UserSchema.index({ lastSeen: -1 });

export class MessagePersistenceService {
  private messageModel: Model<IMessageDocument>;
  private auditLogModel: Model<IAuditLogDocument>;
  private channelModel: Model<IChannelDocument>;
  private userModel: Model<IUserDocument>;
  private logger: Logger;
  private isConnected: boolean = false;

  constructor() {
    this.logger = new Logger('MessagePersistenceService');
    this.initializeModels();
    this.connect();
  }

  private initializeModels(): void {
    this.messageModel = mongoose.model<IMessageDocument>('Message', MessageSchema);
    this.auditLogModel = mongoose.model<IAuditLogDocument>('AuditLog', AuditLogSchema);
    this.channelModel = mongoose.model<IChannelDocument>('Channel', ChannelSchema);
    this.userModel = mongoose.model<IUserDocument>('User', UserSchema);
  }

  private async connect(): Promise<void> {
    try {
      await mongoose.connect(config.database.uri, config.database.options);
      this.isConnected = true;
      this.logger.info('Connected to MongoDB successfully');

      // Setup event handlers
      mongoose.connection.on('error', (error) => {
        this.logger.error(`MongoDB connection error: ${error.message}`);
        this.isConnected = false;
      });

      mongoose.connection.on('disconnected', () => {
        this.logger.warn('MongoDB disconnected');
        this.isConnected = false;
      });

      mongoose.connection.on('reconnected', () => {
        this.logger.info('MongoDB reconnected');
        this.isConnected = true;
      });

    } catch (error) {
      this.logger.error(`Failed to connect to MongoDB: ${error.message}`);
      this.isConnected = false;
    }
  }

  // Message Operations
  public async saveMessage(message: Message): Promise<boolean> {
    if (!this.isConnected) {
      this.logger.warn('MongoDB not connected, cannot save message');
      return false;
    }

    try {
      const messageDoc = new this.messageModel({
        id: message.id,
        type: message.type,
        priority: message.priority,
        channel: message.channel,
        sender: message.sender,
        recipients: message.recipients,
        content: message.content,
        metadata: message.metadata,
        timestamp: message.timestamp,
        encrypted: message.encrypted,
        encryptedContent: message.encryptedContent,
        ttl: message.ttl
      });

      await messageDoc.save();
      this.logger.debug(`Message saved: ${message.id}`);
      return true;

    } catch (error) {
      this.logger.error(`Failed to save message ${message.id}: ${error.message}`);
      return false;
    }
  }

  public async getMessage(messageId: string): Promise<Message | null> {
    if (!this.isConnected) {
      return null;
    }

    try {
      const messageDoc = await this.messageModel.findOne({ id: messageId });
      if (!messageDoc) {
        return null;
      }

      return this.documentToMessage(messageDoc);

    } catch (error) {
      this.logger.error(`Failed to get message ${messageId}: ${error.message}`);
      return null;
    }
  }

  public async getChannelMessages(
    channelId: string,
    limit: number = 50,
    before?: Date,
    after?: Date
  ): Promise<Message[]> {
    if (!this.isConnected) {
      return [];
    }

    try {
      const query: any = { channel: channelId, deletedAt: { $exists: false } };

      if (before) {
        query.timestamp = { $lt: before };
      }

      if (after) {
        query.timestamp = query.timestamp || {};
        query.timestamp.$gt = after;
      }

      const messages = await this.messageModel
        .find(query)
        .sort({ timestamp: -1 })
        .limit(limit)
        .exec();

      return messages.map(doc => this.documentToMessage(doc));

    } catch (error) {
      this.logger.error(`Failed to get channel messages for ${channelId}: ${error.message}`);
      return [];
    }
  }

  public async getUserMessages(
    userId: string,
    limit: number = 100,
    before?: Date,
    after?: Date
  ): Promise<Message[]> {
    if (!this.isConnected) {
      return [];
    }

    try {
      const query: any = {
        $or: [
          { sender: userId },
          { recipients: userId }
        ],
        deletedAt: { $exists: false }
      };

      if (before) {
        query.timestamp = { $lt: before };
      }

      if (after) {
        query.timestamp = query.timestamp || {};
        query.timestamp.$gt = after;
      }

      const messages = await this.messageModel
        .find(query)
        .sort({ timestamp: -1 })
        .limit(limit)
        .exec();

      return messages.map(doc => this.documentToMessage(doc));

    } catch (error) {
      this.logger.error(`Failed to get user messages for ${userId}: ${error.message}`);
      return [];
    }
  }

  public async searchMessages(filter: MessageFilter): Promise<Message[]> {
    if (!this.isConnected) {
      return [];
    }

    try {
      const query: any = { deletedAt: { $exists: false } };

      if (filter.userId) {
        query.$or = [
          { sender: filter.userId },
          { recipients: filter.userId }
        ];
      }

      if (filter.channel) {
        query.channel = filter.channel;
      }

      if (filter.type) {
        query.type = filter.type;
      }

      if (filter.priority !== undefined) {
        query.priority = filter.priority;
      }

      if (filter.dateRange) {
        query.timestamp = {};
        if (filter.dateRange.start) {
          query.timestamp.$gte = filter.dateRange.start;
        }
        if (filter.dateRange.end) {
          query.timestamp.$lte = filter.dateRange.end;
        }
      }

      if (filter.keywords && filter.keywords.length > 0) {
        const keywordRegexes = filter.keywords.map(keyword =>
          new RegExp(keyword, 'i')
        );
        query.$and = keywordRegexes.map(regex => ({ content: { $regex: regex } }));
      }

      const offset = filter.offset || 0;
      const limit = filter.limit || 100;

      const messages = await this.messageModel
        .find(query)
        .sort({ timestamp: -1 })
        .skip(offset)
        .limit(limit)
        .exec();

      return messages.map(doc => this.documentToMessage(doc));

    } catch (error) {
      this.logger.error(`Failed to search messages: ${error.message}`);
      return [];
    }
  }

  public async deleteMessage(messageId: string, userId?: string): Promise<boolean> {
    if (!this.isConnected) {
      return false;
    }

    try {
      const updateData: any = { deletedAt: new Date() };
      if (userId) {
        updateData.deletedBy = userId;
      }

      const result = await this.messageModel.updateOne(
        { id: messageId },
        updateData
      );

      return result.modifiedCount > 0;

    } catch (error) {
      this.logger.error(`Failed to delete message ${messageId}: ${error.message}`);
      return false;
    }
  }

  public async archiveMessages(olderThan: Date): Promise<number> {
    if (!this.isConnected) {
      return 0;
    }

    try {
      const result = await this.messageModel.updateMany(
        {
          timestamp: { $lt: olderThan },
          archivedAt: { $exists: false },
          deletedAt: { $exists: false }
        },
        { archivedAt: new Date() }
      );

      this.logger.info(`Archived ${result.modifiedCount} messages older than ${olderThan}`);
      return result.modifiedCount;

    } catch (error) {
      this.logger.error(`Failed to archive messages: ${error.message}`);
      return 0;
    }
  }

  // Audit Log Operations
  public async saveAuditLog(auditLog: AuditLog): Promise<boolean> {
    if (!this.isConnected) {
      return false;
    }

    try {
      const auditDoc = new this.auditLogModel({
        id: auditLog.id,
        userId: auditLog.userId,
        action: auditLog.action,
        resource: auditLog.resource,
        details: auditLog.details,
        timestamp: auditLog.timestamp,
        ip: auditLog.ip,
        userAgent: auditLog.userAgent,
        success: auditLog.success,
        errorMessage: auditLog.errorMessage
      });

      await auditDoc.save();
      return true;

    } catch (error) {
      this.logger.error(`Failed to save audit log: ${error.message}`);
      return false;
    }
  }

  public async getAuditLogs(
    userId?: string,
    action?: string,
    resource?: string,
    startTime?: Date,
    endTime?: Date,
    limit: number = 100
  ): Promise<AuditLog[]> {
    if (!this.isConnected) {
      return [];
    }

    try {
      const query: any = {};

      if (userId) {
        query.userId = userId;
      }

      if (action) {
        query.action = action;
      }

      if (resource) {
        query.resource = { $regex: resource, $options: 'i' };
      }

      if (startTime || endTime) {
        query.timestamp = {};
        if (startTime) {
          query.timestamp.$gte = startTime;
        }
        if (endTime) {
          query.timestamp.$lte = endTime;
        }
      }

      const logs = await this.auditLogModel
        .find(query)
        .sort({ timestamp: -1 })
        .limit(limit)
        .exec();

      return logs.map(doc => this.documentToAuditLog(doc));

    } catch (error) {
      this.logger.error(`Failed to get audit logs: ${error.message}`);
      return [];
    }
  }

  // Channel Operations
  public async saveChannel(channel: Channel): Promise<boolean> {
    if (!this.isConnected) {
      return false;
    }

    try {
      const channelDoc = new this.channelModel({
        id: channel.id,
        name: channel.name,
        type: channel.type,
        members: channel.members,
        permissions: channel.permissions,
        isPrivate: channel.isPrivate,
        isEncrypted: channel.isEncrypted,
        metadata: channel.metadata
      });

      await channelDoc.save();
      return true;

    } catch (error) {
      this.logger.error(`Failed to save channel ${channel.id}: ${error.message}`);
      return false;
    }
  }

  public async getChannel(channelId: string): Promise<Channel | null> {
    if (!this.isConnected) {
      return null;
    }

    try {
      const channelDoc = await this.channelModel.findOne({
        id: channelId,
        archivedAt: { $exists: false }
      });

      if (!channelDoc) {
        return null;
      }

      return this.documentToChannel(channelDoc);

    } catch (error) {
      this.logger.error(`Failed to get channel ${channelId}: ${error.message}`);
      return null;
    }
  }

  // User Operations
  public async saveUser(user: User): Promise<boolean> {
    if (!this.isConnected) {
      return false;
    }

    try {
      await this.userModel.findOneAndUpdate(
        { id: user.id },
        {
          username: user.username,
          role: user.role,
          portal: user.portal,
          characterId: user.characterId,
          permissions: user.permissions,
          isOnline: user.isOnline,
          lastSeen: user.lastSeen,
          sessionId: user.sessionId
        },
        { upsert: true, new: true }
      );

      return true;

    } catch (error) {
      this.logger.error(`Failed to save user ${user.id}: ${error.message}`);
      return false;
    }
  }

  public async getUser(userId: string): Promise<User | null> {
    if (!this.isConnected) {
      return null;
    }

    try {
      const userDoc = await this.userModel.findOne({ id: userId });
      if (!userDoc) {
        return null;
      }

      return this.documentToUser(userDoc);

    } catch (error) {
      this.logger.error(`Failed to get user ${userId}: ${error.message}`);
      return null;
    }
  }

  // Statistics
  public async getMessageStatistics(
    startTime?: Date,
    endTime?: Date
  ): Promise<MessageStatistics> {
    if (!this.isConnected) {
      return this.getEmptyStatistics();
    }

    try {
      const matchStage: any = { deletedAt: { $exists: false } };

      if (startTime || endTime) {
        matchStage.timestamp = {};
        if (startTime) {
          matchStage.timestamp.$gte = startTime;
        }
        if (endTime) {
          matchStage.timestamp.$lte = endTime;
        }
      }

      const pipeline = [
        { $match: matchStage },
        {
          $group: {
            _id: null,
            totalMessages: { $sum: 1 },
            avgSize: { $avg: { $strLenCP: '$content' } },
            typeStats: {
              $push: {
                type: '$type',
                count: 1
              }
            },
            channelStats: {
              $push: {
                channel: '$channel',
                count: 1
              }
            },
            userStats: {
              $push: {
                sender: '$sender',
                count: 1
              }
            }
          }
        }
      ];

      const result = await this.messageModel.aggregate(pipeline).exec();

      if (result.length === 0) {
        return this.getEmptyStatistics();
      }

      const data = result[0];
      const messagesByType = {} as any;
      const messagesByChannel = {} as any;
      const messagesByUser = {} as any;

      // Process type statistics
      data.typeStats.forEach((stat: any) => {
        messagesByType[stat.type] = (messagesByType[stat.type] || 0) + stat.count;
      });

      // Process channel statistics
      data.channelStats.forEach((stat: any) => {
        messagesByChannel[stat.channel] = (messagesByChannel[stat.channel] || 0) + stat.count;
      });

      // Process user statistics
      data.userStats.forEach((stat: any) => {
        messagesByUser[stat.sender] = (messagesByUser[stat.sender] || 0) + stat.count;
      });

      // Get active channels and users count
      const activeChannels = await this.messageModel.distinct('channel', matchStage);
      const activeUsers = await this.messageModel.distinct('sender', matchStage);

      return {
        totalMessages: data.totalMessages,
        messagesByType,
        messagesByChannel,
        messagesByUser,
        averageMessageSize: Math.round(data.avgSize),
        peakMessagesPerMinute: 0, // Would need more complex aggregation
        activeChannels: activeChannels.length,
        activeUsers: activeUsers.length
      };

    } catch (error) {
      this.logger.error(`Failed to get message statistics: ${error.message}`);
      return this.getEmptyStatistics();
    }
  }

  private getEmptyStatistics(): MessageStatistics {
    return {
      totalMessages: 0,
      messagesByType: {} as any,
      messagesByChannel: {} as any,
      messagesByUser: {},
      averageMessageSize: 0,
      peakMessagesPerMinute: 0,
      activeChannels: 0,
      activeUsers: 0
    };
  }

  // Cleanup Operations
  public async cleanupOldMessages(olderThan: Date): Promise<number> {
    if (!this.isConnected) {
      return 0;
    }

    try {
      const result = await this.messageModel.deleteMany({
        timestamp: { $lt: olderThan }
      });

      this.logger.info(`Cleaned up ${result.deletedCount} messages older than ${olderThan}`);
      return result.deletedCount;

    } catch (error) {
      this.logger.error(`Failed to cleanup old messages: ${error.message}`);
      return 0;
    }
  }

  public async cleanupOldAuditLogs(olderThan: Date): Promise<number> {
    if (!this.isConnected) {
      return 0;
    }

    try {
      const result = await this.auditLogModel.deleteMany({
        timestamp: { $lt: olderThan }
      });

      this.logger.info(`Cleaned up ${result.deletedCount} audit logs older than ${olderThan}`);
      return result.deletedCount;

    } catch (error) {
      this.logger.error(`Failed to cleanup old audit logs: ${error.message}`);
      return 0;
    }
  }

  // Utility Methods
  private documentToMessage(doc: IMessageDocument): Message {
    return {
      id: doc.id,
      type: doc.type as any,
      priority: doc.priority as any,
      channel: doc.channel as any,
      sender: doc.sender,
      recipients: doc.recipients,
      content: doc.content,
      metadata: doc.metadata,
      timestamp: doc.timestamp,
      encrypted: doc.encrypted,
      encryptedContent: doc.encryptedContent,
      ttl: doc.ttl
    };
  }

  private documentToAuditLog(doc: IAuditLogDocument): AuditLog {
    return {
      id: doc.id,
      userId: doc.userId,
      action: doc.action,
      resource: doc.resource,
      details: doc.details,
      timestamp: doc.timestamp,
      ip: doc.ip,
      userAgent: doc.userAgent,
      success: doc.success,
      errorMessage: doc.errorMessage
    };
  }

  private documentToChannel(doc: IChannelDocument): Channel {
    return {
      id: doc.id,
      name: doc.name,
      type: doc.type as any,
      members: doc.members,
      permissions: doc.permissions as any,
      isPrivate: doc.isPrivate,
      isEncrypted: doc.isEncrypted,
      metadata: doc.metadata
    };
  }

  private documentToUser(doc: IUserDocument): User {
    return {
      id: doc.id,
      username: doc.username,
      role: doc.role as any,
      portal: doc.portal as any,
      characterId: doc.characterId,
      permissions: doc.permissions,
      isOnline: doc.isOnline,
      lastSeen: doc.lastSeen,
      sessionId: doc.sessionId
    };
  }

  // Connection Status
  public isReady(): boolean {
    return this.isConnected;
  }

  public async disconnect(): Promise<void> {
    if (this.isConnected) {
      await mongoose.disconnect();
      this.isConnected = false;
      this.logger.info('Disconnected from MongoDB');
    }
  }
}