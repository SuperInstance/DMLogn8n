import {
  Channel,
  ChannelType,
  User,
  UserRole,
  WebSocketClient,
  Message,
  MessageFilter
} from '@/types';
import { v4 as uuidv4 } from 'uuid';
import { EventEmitter } from 'events';
import { Logger } from '@/utils/logger';

export interface ChannelConfig {
  name: string;
  type: ChannelType;
  isPrivate: boolean;
  isEncrypted: boolean;
  permissions: {
    read: UserRole[];
    write: UserRole[];
    moderate: UserRole[];
  };
  metadata?: Record<string, any>;
  maxMembers?: number;
}

export interface ChannelMember {
  userId: string;
  role: 'member' | 'moderator' | 'admin';
  joinedAt: Date;
  permissions: string[];
  isMuted: boolean;
  lastActivity: Date;
}

export interface ChannelMessage extends Message {
  channelId: string;
  edited?: boolean;
  editedAt?: Date;
  deleted?: boolean;
  deletedAt?: Date;
  reactions?: Record<string, string[]>; // emoji -> [userIds]
  replies?: string[]; // message IDs
  replyTo?: string; // parent message ID
}

export class ChannelManager extends EventEmitter {
  private channels: Map<string, Channel>;
  private channelMembers: Map<string, Map<string, ChannelMember>>;
  private channelMessages: Map<string, ChannelMessage[]>;
  private defaultChannels: Channel[];
  private logger: Logger;
  private maxMessagesPerChannel: number;

  constructor() {
    super();
    this.channels = new Map();
    this.channelMembers = new Map();
    this.channelMessages = new Map();
    this.defaultChannels = [];
    this.logger = new Logger('ChannelManager');
    this.maxMessagesPerChannel = 1000;

    this.createDefaultChannels();
    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    this.on('messageSent', this.handleMessageSent.bind(this));
    this.on('userJoined', this.handleUserJoined.bind(this));
    this.on('userLeft', this.handleUserLeft.bind(this));
    this.on('channelCreated', this.handleChannelCreated.bind(this));
    this.on('channelDeleted', this.handleChannelDeleted.bind(this));
  }

  private createDefaultChannels(): void {
    const defaultConfigs: ChannelConfig[] = [
      {
        name: 'Party Chat',
        type: ChannelType.PARTY,
        isPrivate: false,
        isEncrypted: false,
        permissions: {
          read: [UserRole.DM, UserRole.PLAYER, UserRole.CODER, UserRole.SPECTATOR],
          write: [UserRole.DM, UserRole.PLAYER, UserRole.CODER],
          moderate: [UserRole.DM]
        },
        metadata: {
          description: 'Main party communication channel',
          persistent: true
        }
      },
      {
        name: 'DM Directives',
        type: ChannelType.DM_WHISPER,
        isPrivate: true,
        isEncrypted: true,
        permissions: {
          read: [UserRole.DM],
          write: [UserRole.DM],
          moderate: [UserRole.DM]
        },
        metadata: {
          description: 'DM-only channel for directives and planning',
          persistent: true
        }
      },
      {
        name: 'Coder Channel',
        type: ChannelType.CODER,
        isPrivate: false,
        isEncrypted: false,
        permissions: {
          read: [UserRole.DM, UserRole.CODER],
          write: [UserRole.DM, UserRole.CODER],
          moderate: [UserRole.DM]
        },
        metadata: {
          description: 'Technical discussion and automation',
          persistent: true
        }
      },
      {
        name: 'System Notifications',
        type: ChannelType.SYSTEM,
        isPrivate: false,
        isEncrypted: false,
        permissions: {
          read: [UserRole.DM, UserRole.PLAYER, UserRole.CODER, UserRole.SPECTATOR],
          write: [UserRole.SYSTEM],
          moderate: [UserRole.DM, UserRole.SYSTEM]
        },
        metadata: {
          description: 'System notifications and announcements',
          persistent: false
        }
      },
      {
        name: 'Out of Character',
        type: ChannelType.OOC,
        isPrivate: false,
        isEncrypted: false,
        permissions: {
          read: [UserRole.DM, UserRole.PLAYER, UserRole.CODER, UserRole.SPECTATOR],
          write: [UserRole.DM, UserRole.PLAYER, UserRole.CODER, UserRole.SPECTATOR],
          moderate: [UserRole.DM]
        },
        metadata: {
          description: 'Out of character discussions',
          persistent: true
        }
      },
      {
        name: 'Combat Log',
        type: ChannelType.COMBAT,
        isPrivate: false,
        isEncrypted: false,
        permissions: {
          read: [UserRole.DM, UserRole.PLAYER, UserRole.CODER, UserRole.SPECTATOR],
          write: [UserRole.SYSTEM],
          moderate: [UserRole.DM]
        },
        metadata: {
          description: 'Combat events and actions',
          persistent: true
        }
      },
      {
        name: 'Character Sheets',
        type: ChannelType.CHARACTER,
        isPrivate: false,
        isEncrypted: false,
        permissions: {
          read: [UserRole.DM, UserRole.PLAYER, UserRole.CODER],
          write: [UserRole.SYSTEM],
          moderate: [UserRole.DM]
        },
        metadata: {
          description: 'Character updates and changes',
          persistent: true
        }
      }
    ];

    for (const config of defaultConfigs) {
      const channel = this.createChannel(config);
      this.defaultChannels.push(channel);
    }

    this.logger.info(`Created ${this.defaultChannels.length} default channels`);
  }

  // Channel Management
  public createChannel(config: ChannelConfig): Channel {
    const channel: Channel = {
      id: uuidv4(),
      name: config.name,
      type: config.type,
      members: [],
      permissions: config.permissions,
      isPrivate: config.isPrivate,
      isEncrypted: config.isEncrypted,
      metadata: config.metadata || {}
    };

    this.channels.set(channel.id, channel);
    this.channelMembers.set(channel.id, new Map());
    this.channelMessages.set(channel.id, []);

    this.logger.info(`Channel created: ${channel.name} (${channel.id})`);
    this.emit('channelCreated', channel);

    return channel;
  }

  public deleteChannel(channelId: string, userId: string): boolean {
    const channel = this.channels.get(channelId);
    if (!channel) {
      return false;
    }

    // Check if user has permission to delete
    if (!this.hasPermission(userId, channelId, 'moderate')) {
      this.logger.warn(`User ${userId} attempted to delete channel ${channelId} without permission`);
      return false;
    }

    // Remove all members
    this.channelMembers.delete(channelId);
    this.channelMessages.delete(channelId);
    this.channels.delete(channelId);

    this.logger.info(`Channel deleted: ${channel.name} (${channelId})`);
    this.emit('channelDeleted', { channelId, deletedBy: userId });

    return true;
  }

  public getChannel(channelId: string): Channel | undefined {
    return this.channels.get(channelId);
  }

  public getAllChannels(): Channel[] {
    return Array.from(this.channels.values());
  }

  public getChannelsByType(type: ChannelType): Channel[] {
    return Array.from(this.channels.values()).filter(channel => channel.type === type);
  }

  public getAccessibleChannels(userId: string, userRole: UserRole): Channel[] {
    return Array.from(this.channels.values()).filter(channel =>
      this.hasReadPermission(userRole, channel)
    );
  }

  // Channel Member Management
  public joinChannel(channelId: string, user: User): boolean {
    const channel = this.channels.get(channelId);
    if (!channel) {
      this.logger.warn(`Channel ${channelId} not found`);
      return false;
    }

    // Check if user has read permission
    if (!this.hasReadPermission(user.role, channel)) {
      this.logger.warn(`User ${user.id} does not have read permission for channel ${channelId}`);
      return false;
    }

    // Check if channel is full
    if (channel.metadata.maxMembers) {
      const currentMembers = this.channelMembers.get(channelId)?.size || 0;
      if (currentMembers >= channel.metadata.maxMembers) {
        this.logger.warn(`Channel ${channelId} is full`);
        return false;
      }
    }

    const members = this.channelMembers.get(channelId)!;
    const existingMember = members.get(user.id);

    if (existingMember) {
      // User is already a member, update last activity
      existingMember.lastActivity = new Date();
      return true;
    }

    const member: ChannelMember = {
      userId: user.id,
      role: this.determineMemberRole(user.role, channel),
      joinedAt: new Date(),
      permissions: this.calculateUserPermissions(user.role, channel),
      isMuted: false,
      lastActivity: new Date()
    };

    members.set(user.id, member);
    channel.members.push(user.id);

    this.logger.info(`User ${user.id} joined channel ${channelId}`);
    this.emit('userJoined', { channelId, userId: user.id, user });

    return true;
  }

  public leaveChannel(channelId: string, userId: string): boolean {
    const channel = this.channels.get(channelId);
    if (!channel) {
      return false;
    }

    const members = this.channelMembers.get(channelId);
    if (!members || !members.has(userId)) {
      return false;
    }

    members.delete(userId);
    const memberIndex = channel.members.indexOf(userId);
    if (memberIndex > -1) {
      channel.members.splice(memberIndex, 1);
    }

    this.logger.info(`User ${userId} left channel ${channelId}`);
    this.emit('userLeft', { channelId, userId });

    return true;
  }

  public getChannelMembers(channelId: string): ChannelMember[] {
    const members = this.channelMembers.get(channelId);
    return members ? Array.from(members.values()) : [];
  }

  public isMember(channelId: string, userId: string): boolean {
    const members = this.channelMembers.get(channelId);
    return members ? members.has(userId) : false;
  }

  // Message Management
  public sendMessage(
    channelId: string,
    sender: User,
    content: string,
    metadata: Record<string, any> = {},
    replyTo?: string
  ): ChannelMessage | null {
    const channel = this.channels.get(channelId);
    if (!channel) {
      this.logger.warn(`Channel ${channelId} not found`);
      return null;
    }

    // Check permissions
    if (!this.hasWritePermission(sender.role, channel)) {
      this.logger.warn(`User ${sender.id} does not have write permission for channel ${channelId}`);
      return null;
    }

    // Check if user is muted
    const member = this.channelMembers.get(channelId)?.get(sender.id);
    if (member?.isMuted) {
      this.logger.warn(`User ${sender.id} is muted in channel ${channelId}`);
      return null;
    }

    const message: ChannelMessage = {
      id: uuidv4(),
      type: 'chat' as any,
      priority: 1 as any,
      channel: channel.type,
      sender: sender.id,
      recipients: channel.members.filter(id => id !== sender.id),
      content,
      metadata: {
        ...metadata,
        channelId,
        senderName: sender.username,
        senderRole: sender.role
      },
      timestamp: new Date(),
      encrypted: channel.isEncrypted,
      channelId,
      replyTo
    };

    // Store message
    this.storeMessage(channelId, message);

    // Update member activity
    if (member) {
      member.lastActivity = new Date();
    }

    this.logger.debug(`Message sent to channel ${channelId} by ${sender.id}`);
    this.emit('messageSent', { channelId, message });

    return message;
  }

  public editMessage(
    channelId: string,
    messageId: string,
    userId: string,
    newContent: string
  ): boolean {
    const messages = this.channelMessages.get(channelId);
    if (!messages) {
      return false;
    }

    const message = messages.find(m => m.id === messageId);
    if (!message) {
      return false;
    }

    // Check if user can edit (only sender or moderators)
    const member = this.channelMembers.get(channelId)?.get(userId);
    if (!member || (message.sender !== userId && member.role !== 'moderator' && member.role !== 'admin')) {
      return false;
    }

    message.content = newContent;
    message.edited = true;
    message.editedAt = new Date();

    this.logger.debug(`Message ${messageId} edited by ${userId}`);
    this.emit('messageEdited', { channelId, messageId, userId, newContent });

    return true;
  }

  public deleteMessage(
    channelId: string,
    messageId: string,
    userId: string
  ): boolean {
    const messages = this.channelMessages.get(channelId);
    if (!messages) {
      return false;
    }

    const messageIndex = messages.findIndex(m => m.id === messageId);
    if (messageIndex === -1) {
      return false;
    }

    const message = messages[messageIndex];

    // Check if user can delete (only sender or moderators)
    const member = this.channelMembers.get(channelId)?.get(userId);
    if (!member || (message.sender !== userId && member.role !== 'moderator' && member.role !== 'admin')) {
      return false;
    }

    message.deleted = true;
    message.deletedAt = new Date();

    this.logger.debug(`Message ${messageId} deleted by ${userId}`);
    this.emit('messageDeleted', { channelId, messageId, userId });

    return true;
  }

  public addReaction(
    channelId: string,
    messageId: string,
    userId: string,
    emoji: string
  ): boolean {
    const messages = this.channelMessages.get(channelId);
    if (!messages) {
      return false;
    }

    const message = messages.find(m => m.id === messageId);
    if (!message) {
      return false;
    }

    if (!message.reactions) {
      message.reactions = {};
    }

    if (!message.reactions[emoji]) {
      message.reactions[emoji] = [];
    }

    // Remove existing reaction from this user if present
    Object.keys(message.reactions).forEach(e => {
      const index = message.reactions![e].indexOf(userId);
      if (index > -1) {
        message.reactions![e].splice(index, 1);
      }
    });

    // Add new reaction
    message.reactions[emoji].push(userId);

    this.logger.debug(`Reaction ${emoji} added to message ${messageId} by ${userId}`);
    this.emit('reactionAdded', { channelId, messageId, userId, emoji });

    return true;
  }

  public getChannelMessages(
    channelId: string,
    limit: number = 50,
    before?: Date,
    after?: Date
  ): ChannelMessage[] {
    const messages = this.channelMessages.get(channelId) || [];
    let filtered = messages.filter(m => !m.deleted);

    if (before) {
      filtered = filtered.filter(m => m.timestamp < before);
    }

    if (after) {
      filtered = filtered.filter(m => m.timestamp > after);
    }

    // Sort by timestamp (newest first)
    filtered.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

    return filtered.slice(0, limit);
  }

  public searchChannelMessages(
    channelId: string,
    query: string,
    userId?: string,
    limit: number = 100
  ): ChannelMessage[] {
    const messages = this.channelMessages.get(channelId) || [];
    const filtered = messages
      .filter(m => !m.deleted)
      .filter(m => m.content.toLowerCase().includes(query.toLowerCase()))
      .filter(m => !userId || m.sender === userId);

    return filtered.slice(0, limit);
  }

  // Permission Management
  public hasPermission(userId: string, channelId: string, permission: 'read' | 'write' | 'moderate'): boolean {
    const channel = this.channels.get(channelId);
    if (!channel) {
      return false;
    }

    const member = this.channelMembers.get(channelId)?.get(userId);
    if (!member) {
      return false;
    }

    switch (permission) {
      case 'read':
        return channel.permissions.read.includes(member.role as UserRole);
      case 'write':
        return channel.permissions.write.includes(member.role as UserRole) && !member.isMuted;
      case 'moderate':
        return channel.permissions.moderate.includes(member.role as UserRole);
      default:
        return false;
    }
  }

  private hasReadPermission(role: UserRole, channel: Channel): boolean {
    return channel.permissions.read.includes(role);
  }

  private hasWritePermission(role: UserRole, channel: Channel): boolean {
    return channel.permissions.write.includes(role);
  }

  private determineMemberRole(userRole: UserRole, channel: Channel): 'member' | 'moderator' | 'admin' {
    if (channel.permissions.moderate.includes(userRole)) {
      return 'moderator';
    }
    return 'member';
  }

  private calculateUserPermissions(userRole: UserRole, channel: Channel): string[] {
    const permissions: string[] = [];

    if (channel.permissions.read.includes(userRole)) {
      permissions.push('read');
    }

    if (channel.permissions.write.includes(userRole)) {
      permissions.push('write');
    }

    if (channel.permissions.moderate.includes(userRole)) {
      permissions.push('moderate');
      permissions.push('delete_messages');
      permissions.push('mute_users');
    }

    return permissions;
  }

  public muteUser(channelId: string, targetUserId: string, moderatorId: string, duration?: number): boolean {
    const channel = this.channels.get(channelId);
    if (!channel) {
      return false;
    }

    const moderator = this.channelMembers.get(channelId)?.get(moderatorId);
    if (!moderator || moderator.role !== 'moderator' && moderator.role !== 'admin') {
      return false;
    }

    const targetMember = this.channelMembers.get(channelId)?.get(targetUserId);
    if (!targetMember) {
      return false;
    }

    targetMember.isMuted = true;

    // Schedule unmute if duration is specified
    if (duration) {
      setTimeout(() => {
        this.unmuteUser(channelId, targetUserId, moderatorId);
      }, duration);
    }

    this.logger.info(`User ${targetUserId} muted in channel ${channelId} by ${moderatorId}`);
    this.emit('userMuted', { channelId, targetUserId, moderatorId, duration });

    return true;
  }

  public unmuteUser(channelId: string, targetUserId: string, moderatorId: string): boolean {
    const channel = this.channels.get(channelId);
    if (!channel) {
      return false;
    }

    const moderator = this.channelMembers.get(channelId)?.get(moderatorId);
    if (!moderator || moderator.role !== 'moderator' && moderator.role !== 'admin') {
      return false;
    }

    const targetMember = this.channelMembers.get(channelId)?.get(targetUserId);
    if (!targetMember) {
      return false;
    }

    targetMember.isMuted = false;

    this.logger.info(`User ${targetUserId} unmuted in channel ${channelId} by ${moderatorId}`);
    this.emit('userUnmuted', { channelId, targetUserId, moderatorId });

    return true;
  }

  // Private Methods
  private storeMessage(channelId: string, message: ChannelMessage): void {
    const messages = this.channelMessages.get(channelId);
    if (messages) {
      messages.push(message);

      // Maintain message limit
      if (messages.length > this.maxMessagesPerChannel) {
        const removed = messages.splice(0, messages.length - this.maxMessagesPerChannel);
        this.logger.debug(`Removed ${removed.length} old messages from channel ${channelId}`);
      }
    }
  }

  // Event Handlers
  private handleMessageSent(event: any): void {
    this.logger.debug(`Message sent event handled: ${event.message.id}`);
  }

  private handleUserJoined(event: any): void {
    this.logger.debug(`User joined event handled: ${event.userId} to ${event.channelId}`);
  }

  private handleUserLeft(event: any): void {
    this.logger.debug(`User left event handled: ${event.userId} from ${event.channelId}`);
  }

  private handleChannelCreated(event: any): void {
    this.logger.debug(`Channel created event handled: ${event.name}`);
  }

  private handleChannelDeleted(event: any): void {
    this.logger.debug(`Channel deleted event handled: ${event.channelId}`);
  }

  // Statistics and Cleanup
  public getChannelStatistics(channelId: string): {
    memberCount: number;
    messageCount: number;
    activeMembers: number;
    mutedMembers: number;
  } | null {
    const channel = this.channels.get(channelId);
    const members = this.channelMembers.get(channelId);
    const messages = this.channelMessages.get(channelId);

    if (!channel || !members || !messages) {
      return null;
    }

    const now = new Date();
    const activeThreshold = new Date(now.getTime() - 30 * 60 * 1000); // 30 minutes

    return {
      memberCount: members.size,
      messageCount: messages.filter(m => !m.deleted).length,
      activeMembers: Array.from(members.values()).filter(m => m.lastActivity > activeThreshold).length,
      mutedMembers: Array.from(members.values()).filter(m => m.isMuted).length
    };
  }

  public getOverallStatistics(): {
    totalChannels: number;
    totalMembers: number;
    totalMessages: number;
    activeChannels: number;
    channelsByType: Record<ChannelType, number>;
  } {
    const channels = Array.from(this.channels.values());
    const now = new Date();
    const activeThreshold = new Date(now.getTime() - 60 * 60 * 1000); // 1 hour

    const channelsByType = {} as Record<ChannelType, number>;
    let totalMembers = 0;
    let totalMessages = 0;
    let activeChannels = 0;

    for (const channel of channels) {
      channelsByType[channel.type] = (channelsByType[channel.type] || 0) + 1;
      totalMembers += channel.members.length;

      const messages = this.channelMessages.get(channel.id) || [];
      totalMessages += messages.filter(m => !m.deleted).length;

      // Check if channel had recent activity
      const hasRecentActivity = messages.some(m =>
        !m.deleted && m.timestamp > activeThreshold
      );
      if (hasRecentActivity) {
        activeChannels++;
      }
    }

    return {
      totalChannels: channels.length,
      totalMembers,
      totalMessages,
      activeChannels,
      channelsByType
    };
  }

  public cleanupOldMessages(maxAge: number = 7 * 24 * 60 * 60 * 1000): void { // 7 days
    const cutoffDate = new Date(Date.now() - maxAge);
    let totalRemoved = 0;

    for (const [channelId, messages] of this.channelMessages.entries()) {
      const initialLength = messages.length;
      const filtered = messages.filter(m =>
        !m.deleted && m.timestamp > cutoffDate
      );

      this.channelMessages.set(channelId, filtered);
      totalRemoved += initialLength - filtered.length;
    }

    this.logger.info(`Cleaned up ${totalRemoved} old messages`);
    this.emit('cleanupCompleted', { totalRemoved, cutoffDate });
  }
}