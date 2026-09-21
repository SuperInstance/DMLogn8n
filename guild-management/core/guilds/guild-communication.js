/**
 * Guild Communication System
 * Handles guild chat, voice channels, announcements, and messaging
 */

class GuildCommunication {
    constructor(databaseClient, voiceService, notificationService) {
        this.db = databaseClient;
        this.voice = voiceService;
        this.notifications = notificationService;
        this.activeChannels = new Map();
        this.onlineMembers = new Map();
    }

    /**
     * Send guild chat message
     */
    async sendGuildChat(guildId, playerId, message, options = {}) {
        try {
            const {
                channel = 'general',
                type = 'text',
                metadata = {}
            } = options;

            // Validate member
            const member = await this.getGuildMember(guildId, playerId);
            if (!member) {
                throw new Error('Member not found in guild');
            }

            // Check chat permissions
            if (!this.hasChatPermission(member, channel)) {
                throw new Error('No permission to chat in this channel');
            }

            // Validate message
            if (!message || message.trim().length === 0) {
                throw new Error('Message cannot be empty');
            }

            if (message.length > 500) {
                throw new Error('Message too long (max 500 characters)');
            }

            // Check for spam/flood
            const floodCheck = await this.checkFloodProtection(playerId, channel);
            if (!floodCheck.allowed) {
                throw new Error(floodCheck.reason);
            }

            // Create chat message
            const chatMessage = {
                id: this.generateMessageId(),
                guildId: guildId,
                playerId: playerId,
                playerName: member.playerName,
                playerRank: member.rank,
                channel: channel,
                type: type,
                content: message.trim(),
                timestamp: new Date().toISOString(),
                edited: false,
                metadata: {
                    ...metadata,
                    channelType: this.getChannelType(channel)
                },
                reactions: []
            };

            // Save to database
            await this.db.collection('guild_chat').insertOne(chatMessage);

            // Broadcast to online guild members
            await this.broadcastToGuild(guildId, chatMessage, channel);

            // Log chat activity
            await this.logChatActivity(chatMessage);

            return {
                success: true,
                message: chatMessage
            };

        } catch (error) {
            console.error('Error sending guild chat:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Edit guild chat message
     */
    async editGuildMessage(guildId, playerId, messageId, newContent) {
        try {
            // Get original message
            const originalMessage = await this.db.collection('guild_chat').findOne({
                id: messageId,
                guildId: guildId
            });

            if (!originalMessage) {
                throw new Error('Message not found');
            }

            // Check permissions (only sender or officers can edit)
            const member = await this.getGuildMember(guildId, playerId);
            const canEdit = originalMessage.playerId === playerId ||
                          this.hasPermission(member, 'moderate_chat');

            if (!canEdit) {
                throw new Error('No permission to edit this message');
            }

            // Check time limit for editing (5 minutes)
            const editTimeLimit = 5 * 60 * 1000; // 5 minutes
            const messageAge = Date.now() - new Date(originalMessage.timestamp).getTime();
            if (messageAge > editTimeLimit) {
                throw new Error('Message can no longer be edited');
            }

            // Update message
            await this.db.collection('guild_chat').updateOne(
                { id: messageId },
                {
                    $set: {
                        content: newContent.trim(),
                        edited: true,
                        editedAt: new Date().toISOString(),
                        editedBy: playerId
                    }
                }
            );

            // Broadcast edit notification
            await this.broadcastMessageEdit(guildId, messageId, newContent);

            return {
                success: true,
                editedAt: new Date().toISOString()
            };

        } catch (error) {
            console.error('Error editing message:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Delete guild chat message
     */
    async deleteGuildMessage(guildId, playerId, messageId) {
        try {
            // Get message
            const message = await this.db.collection('guild_chat').findOne({
                id: messageId,
                guildId: guildId
            });

            if (!message) {
                throw new Error('Message not found');
            }

            // Check permissions
            const member = await this.getGuildMember(guildId, playerId);
            const canDelete = message.playerId === playerId ||
                            this.hasPermission(member, 'moderate_chat');

            if (!canDelete) {
                throw new Error('No permission to delete this message');
            }

            // Delete message
            await this.db.collection('guild_chat').deleteOne({ id: messageId });

            // Broadcast deletion notification
            await this.broadcastMessageDeletion(guildId, messageId);

            return {
                success: true
            };

        } catch (error) {
            console.error('Error deleting message:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Create guild announcement
     */
    async createAnnouncement(guildId, playerId, announcementData) {
        try {
            const {
                title,
                content,
                priority = 'normal',
                expiresAt = null,
                channels = ['general'],
                pinned = false
            } = announcementData;

            // Validate permissions
            const member = await this.getGuildMember(guildId, playerId);
            if (!this.hasPermission(member, 'create_announcements')) {
                throw new Error('No permission to create announcements');
            }

            // Validate content
            if (!title || !content) {
                throw new Error('Title and content are required');
            }

            // Create announcement
            const announcement = {
                id: this.generateAnnouncementId(),
                guildId: guildId,
                title: title,
                content: content,
                authorId: playerId,
                authorName: member.playerName,
                authorRank: member.rank,
                priority: priority,
                channels: channels,
                pinned: pinned,
                expiresAt: expiresAt,
                createdAt: new Date().toISOString(),
                readBy: [],
                reactions: []
            };

            // Save to database
            await this.db.collection('guild_announcements').insertOne(announcement);

            // Broadcast to guild
            await this.broadcastAnnouncement(guildId, announcement);

            // Send notifications to offline members
            await this.notifyOfflineMembers(guildId, announcement);

            return {
                success: true,
                announcement: announcement
            };

        } catch (error) {
            console.error('Error creating announcement:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Create and manage voice channels
     */
    async createVoiceChannel(guildId, playerId, channelData) {
        try {
            const {
                name,
                type = 'temporary',
                maxUsers = 10,
                password = null,
                permissions = 'members'
            } = channelData;

            // Validate permissions
            const member = await this.getGuildMember(guildId, playerId);
            if (!this.hasPermission(member, 'manage_voice_channels')) {
                throw new Error('No permission to create voice channels');
            }

            // Create voice channel
            const voiceChannel = {
                id: this.generateChannelId(),
                guildId: guildId,
                name: name,
                type: type,
                maxUsers: maxUsers,
                password: password,
                permissions: permissions,
                createdBy: playerId,
                createdAt: new Date().toISOString(),
                activeUsers: [],
                settings: {
                    allowGuests: false,
                    autoDelete: type === 'temporary',
                    recordingEnabled: false
                }
            };

            // Save to database
            await this.db.collection('guild_voice_channels').insertOne(voiceChannel);

            // Initialize voice channel
            await this.voice.createChannel(voiceChannel);

            // Cache active channel
            this.activeChannels.set(voiceChannel.id, voiceChannel);

            // Notify guild
            await this.broadcastVoiceChannelCreated(guildId, voiceChannel);

            return {
                success: true,
                channel: voiceChannel
            };

        } catch (error) {
            console.error('Error creating voice channel:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Join voice channel
     */
    async joinVoiceChannel(guildId, playerId, channelId, password = null) {
        try {
            // Validate member
            const member = await this.getGuildMember(guildId, playerId);
            if (!member) {
                throw new Error('Member not found in guild');
            }

            // Get channel
            const channel = await this.getVoiceChannel(channelId);
            if (!channel) {
                throw new Error('Voice channel not found');
            }

            if (channel.guildId !== guildId) {
                throw new Error('Channel not in this guild');
            }

            // Check permissions
            if (!this.canJoinVoiceChannel(member, channel)) {
                throw new Error('No permission to join this voice channel');
            }

            // Check if channel is full
            if (channel.activeUsers.length >= channel.maxUsers) {
                throw new Error('Voice channel is full');
            }

            // Check password if required
            if (channel.password && channel.password !== password) {
                throw new Error('Incorrect password');
            }

            // Check if user is already in another channel
            await this.leaveAllVoiceChannels(playerId);

            // Join channel
            await this.voice.joinChannel(channelId, playerId);

            // Update channel
            await this.db.collection('guild_voice_channels').updateOne(
                { id: channelId },
                {
                    $push: { activeUsers: playerId },
                    $set: { lastActivity: new Date().toISOString() }
                }
            );

            // Update cache
            channel.activeUsers.push(playerId);
            this.activeChannels.set(channelId, channel);

            // Update online status
            this.onlineMembers.set(playerId, {
                guildId: guildId,
                status: 'in_voice',
                channelId: channelId,
                since: new Date().toISOString()
            });

            // Notify channel members
            await this.notifyVoiceChannelMembers(channelId, {
                type: 'user_joined',
                playerId: playerId,
                playerName: member.playerName
            });

            return {
                success: true,
                channel: channel
            };

        } catch (error) {
            console.error('Error joining voice channel:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Leave voice channel
     */
    async leaveVoiceChannel(playerId) {
        try {
            // Find active channel for user
            const activeChannel = await this.findUserVoiceChannel(playerId);
            if (!activeChannel) {
                return { success: true }; // Not in any channel
            }

            // Leave voice channel
            await this.voice.leaveChannel(activeChannel.id, playerId);

            // Update channel
            await this.db.collection('guild_voice_channels').updateOne(
                { id: activeChannel.id },
                {
                    $pull: { activeUsers: playerId },
                    $set: { lastActivity: new Date().toISOString() }
                }
            );

            // Update cache
            activeChannel.activeUsers = activeChannel.activeUsers.filter(id => id !== playerId);
            this.activeChannels.set(activeChannel.id, activeChannel);

            // Update online status
            this.onlineMembers.set(playerId, {
                status: 'online',
                guildId: activeChannel.guildId,
                since: new Date().toISOString()
            });

            // Notify channel members
            await this.notifyVoiceChannelMembers(activeChannel.id, {
                type: 'user_left',
                playerId: playerId
            });

            // Check if temporary channel should be deleted
            if (activeChannel.type === 'temporary' && activeChannel.activeUsers.length === 0) {
                await this.deleteVoiceChannel(activeChannel.id);
            }

            return {
                success: true
            };

        } catch (error) {
            console.error('Error leaving voice channel:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Get chat history
     */
    async getChatHistory(guildId, options = {}) {
        try {
            const {
                channel = 'general',
                limit = 50,
                before = null,
                after = null,
                search = null
            } = options;

            let query = {
                guildId: guildId,
                channel: channel
            };

            // Date range
            if (before) {
                query.timestamp = { $lt: before };
            }
            if (after) {
                query.timestamp = { ...query.timestamp, $gt: after };
            }

            // Search filter
            if (search) {
                query.$text = { $search: search };
            }

            const messages = await this.db.collection('guild_chat')
                .find(query)
                .sort({ timestamp: -1 })
                .limit(limit)
                .toArray();

            // Mark messages as read for requesting user
            // (if user is provided)

            return {
                success: true,
                messages: messages.reverse() // Return in chronological order
            };

        } catch (error) {
            console.error('Error fetching chat history:', error);
            return {
                success: false,
                error: error.message,
                messages: []
            };
        }
    }

    /**
     * Get active voice channels
     */
    async getActiveVoiceChannels(guildId) {
        try {
            const channels = await this.db.collection('guild_voice_channels')
                .find({ guildId: guildId })
                .sort({ createdAt: -1 })
                .toArray();

            // Add user details to active users
            for (const channel of channels) {
                channel.userDetails = await this.getChannelUserDetails(channel.activeUsers);
            }

            return {
                success: true,
                channels: channels
            };

        } catch (error) {
            console.error('Error fetching voice channels:', error);
            return {
                success: false,
                error: error.message,
                channels: []
            };
        }
    }

    /**
     * Set member online status
     */
    async setOnlineStatus(guildId, playerId, status, metadata = {}) {
        try {
            const member = await this.getGuildMember(guildId, playerId);
            if (!member) {
                throw new Error('Member not found');
            }

            const statusData = {
                guildId: guildId,
                playerId: playerId,
                status: status,
                metadata: metadata,
                lastSeen: new Date().toISOString()
            };

            // Update online status
            this.onlineMembers.set(playerId, statusData);

            // Save to database
            await this.db.collection('guild_online_status').updateOne(
                { playerId: playerId },
                {
                    $set: statusData,
                    $setOnInsert: { firstSeen: new Date().toISOString() }
                },
                { upsert: true }
            );

            // Broadcast status change to guild
            await this.broadcastStatusChange(guildId, playerId, status, member);

            return {
                success: true,
                status: statusData
            };

        } catch (error) {
            console.error('Error setting online status:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Add reaction to message
     */
    async addMessageReaction(guildId, playerId, messageId, emoji) {
        try {
            const member = await this.getGuildMember(guildId, playerId);
            if (!member) {
                throw new Error('Member not found');
            }

            // Add reaction
            await this.db.collection('guild_chat').updateOne(
                {
                    id: messageId,
                    guildId: guildId,
                    'reactions.emoji': { $ne: emoji }
                },
                {
                    $push: {
                        reactions: {
                            emoji: emoji,
                            userIds: [playerId],
                            count: 1
                        }
                    }
                }
            );

            // If emoji already exists, add user to it
            const result = await this.db.collection('guild_chat').updateOne(
                {
                    id: messageId,
                    guildId: guildId,
                    'reactions.emoji': emoji
                },
                {
                    $addToSet: { 'reactions.$.userIds': playerId },
                    $inc: { 'reactions.$.count': 1 }
                }
            );

            // Broadcast reaction update
            await this.broadcastReactionUpdate(guildId, messageId, emoji, playerId, 'add');

            return {
                success: true
            };

        } catch (error) {
            console.error('Error adding reaction:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Helper methods
     */
    generateMessageId() {
        return 'msg_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    generateAnnouncementId() {
        return 'ann_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    generateChannelId() {
        return 'vc_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    hasPermission(member, permission) {
        return member && member.permissions && member.permissions.includes(permission);
    }

    hasChatPermission(member, channel) {
        // All guild members can chat in general channels
        if (['general', 'recruitment'].includes(channel)) {
            return true;
        }

        // Officer-only channels
        if (['officers', 'leadership'].includes(channel)) {
            return ['Leader', 'Officer'].includes(member.rank);
        }

        // Veteran channels
        if (channel === 'veterans') {
            return ['Leader', 'Officer', 'Veteran'].includes(member.rank);
        }

        return member.permissions && member.permissions.includes('guild_chat');
    }

    getChannelType(channel) {
        const channelTypes = {
            'general': 'public',
            'officers': 'private',
            'veterans': 'restricted',
            'recruitment': 'public',
            'leadership': 'private'
        };

        return channelTypes[channel] || 'public';
    }

    async checkFloodProtection(playerId, channel) {
        const key = `${playerId}_${channel}`;
        const now = Date.now();
        const messageWindow = 60000; // 1 minute
        const maxMessages = 10;

        // Get recent messages from player
        const recentCount = await this.db.collection('guild_chat').countDocuments({
            playerId: playerId,
            channel: channel,
            timestamp: {
                $gte: new Date(now - messageWindow).toISOString()
            }
        });

        if (recentCount >= maxMessages) {
            return {
                allowed: false,
                reason: 'Too many messages. Please wait before sending more.'
            };
        }

        return { allowed: true };
    }

    async broadcastToGuild(guildId, message, channel) {
        // Get online guild members
        const onlineMembers = await this.getOnlineGuildMembers(guildId);

        for (const member of onlineMembers) {
            // Send message to each online member
            await this.notifications.sendGuildChatMessage(member.playerId, message, channel);
        }
    }

    async broadcastMessageEdit(guildId, messageId, newContent) {
        const onlineMembers = await this.getOnlineGuildMembers(guildId);
        const editNotification = {
            type: 'message_edited',
            messageId: messageId,
            newContent: newContent,
            timestamp: new Date().toISOString()
        };

        for (const member of onlineMembers) {
            await this.notifications.sendGuildNotification(member.playerId, editNotification);
        }
    }

    async broadcastMessageDeletion(guildId, messageId) {
        const onlineMembers = await this.getOnlineGuildMembers(guildId);
        const deletionNotification = {
            type: 'message_deleted',
            messageId: messageId,
            timestamp: new Date().toISOString()
        };

        for (const member of onlineMembers) {
            await this.notifications.sendGuildNotification(member.playerId, deletionNotification);
        }
    }

    async broadcastAnnouncement(guildId, announcement) {
        const allMembers = await this.getAllGuildMembers(guildId);

        for (const member of allMembers) {
            await this.notifications.sendGuildAnnouncement(member.playerId, announcement);
        }
    }

    async broadcastVoiceChannelCreated(guildId, channel) {
        const onlineMembers = await this.getOnlineGuildMembers(guildId);
        const notification = {
            type: 'voice_channel_created',
            channel: channel
        };

        for (const member of onlineMembers) {
            await this.notifications.sendGuildNotification(member.playerId, notification);
        }
    }

    async notifyVoiceChannelMembers(channelId, notification) {
        const channel = await this.getVoiceChannel(channelId);
        if (!channel) return;

        for (const userId of channel.activeUsers) {
            await this.notifications.sendVoiceChannelNotification(userId, notification);
        }
    }

    async broadcastStatusChange(guildId, playerId, status, member) {
        const onlineMembers = await this.getOnlineGuildMembers(guildId);
        const statusNotification = {
            type: 'status_change',
            playerId: playerId,
            playerName: member.playerName,
            status: status,
            timestamp: new Date().toISOString()
        };

        for (const onlineMember of onlineMembers) {
            if (onlineMember.playerId !== playerId) {
                await this.notifications.sendGuildNotification(onlineMember.playerId, statusNotification);
            }
        }
    }

    async broadcastReactionUpdate(guildId, messageId, emoji, userId, action) {
        const onlineMembers = await this.getOnlineGuildMembers(guildId);
        const reactionNotification = {
            type: 'reaction_update',
            messageId: messageId,
            emoji: emoji,
            userId: userId,
            action: action,
            timestamp: new Date().toISOString()
        };

        for (const member of onlineMembers) {
            await this.notifications.sendGuildNotification(member.playerId, reactionNotification);
        }
    }

    async notifyOfflineMembers(guildId, announcement) {
        // Get offline members who should receive notification
        const offlineMembers = await this.db.collection('guild_members').find({
            guildId: guildId,
            status: 'active',
            lastActivity: {
                $lt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString() // Offline for more than 24 hours
            }
        }).toArray();

        for (const member of offlineMembers) {
            // Send email/push notification based on user preferences
            await this.notifications.sendOfflineNotification(member.playerId, announcement);
        }
    }

    async getOnlineGuildMembers(guildId) {
        const onlineIds = Array.from(this.onlineMembers.entries())
            .filter(([_, status]) => status.guildId === guildId)
            .map(([id, _]) => id);

        if (onlineIds.length === 0) return [];

        return await this.db.collection('guild_members').find({
            guildId: guildId,
            playerId: { $in: onlineIds }
        }).toArray();
    }

    async getAllGuildMembers(guildId) {
        return await this.db.collection('guild_members').find({
            guildId: guildId,
            status: 'active'
        }).toArray();
    }

    async getVoiceChannel(channelId) {
        // Check cache first
        if (this.activeChannels.has(channelId)) {
            return this.activeChannels.get(channelId);
        }

        const channel = await this.db.collection('guild_voice_channels').findOne({ id: channelId });
        if (channel) {
            this.activeChannels.set(channelId, channel);
        }
        return channel;
    }

    async getGuildMember(guildId, playerId) {
        return await this.db.collection('guild_members').findOne({
            guildId: guildId,
            playerId: playerId
        });
    }

    canJoinVoiceChannel(member, channel) {
        const permissionLevels = {
            'Leader': ['all', 'officers', 'veterans', 'members'],
            'Officer': ['all', 'officers', 'veterans', 'members'],
            'Veteran': ['all', 'veterans', 'members'],
            'Member': ['all', 'members'],
            'Initiate': ['all']
        };

        const allowedPermissions = permissionLevels[member.rank] || [];
        return allowedPermissions.includes(channel.permissions);
    }

    async leaveAllVoiceChannels(playerId) {
        const activeChannel = await this.findUserVoiceChannel(playerId);
        if (activeChannel) {
            await this.leaveVoiceChannel(playerId);
        }
    }

    async findUserVoiceChannel(playerId) {
        for (const [channelId, channel] of this.activeChannels.entries()) {
            if (channel.activeUsers.includes(playerId)) {
                return channel;
            }
        }

        // Check database if not in cache
        const channel = await this.db.collection('guild_voice_channels').findOne({
            activeUsers: playerId
        });

        if (channel) {
            this.activeChannels.set(channel.id, channel);
        }

        return channel;
    }

    async deleteVoiceChannel(channelId) {
        await this.voice.deleteChannel(channelId);
        await this.db.collection('guild_voice_channels').deleteOne({ id: channelId });
        this.activeChannels.delete(channelId);
    }

    async getChannelUserDetails(userIds) {
        if (userIds.length === 0) return [];

        const members = await this.db.collection('guild_members').find({
            playerId: { $in: userIds }
        }).toArray();

        return members.map(member => ({
            playerId: member.playerId,
            playerName: member.playerName,
            rank: member.rank,
            isOnline: this.onlineMembers.has(member.playerId)
        }));
    }

    async logChatActivity(message) {
        const activity = {
            guildId: message.guildId,
            playerId: message.playerId,
            channel: message.channel,
            type: 'chat_message',
            timestamp: message.timestamp
        };

        await this.db.collection('guild_activity_log').insertOne(activity);
    }
}

module.exports = GuildCommunication;