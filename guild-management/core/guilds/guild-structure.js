/**
 * Guild Structure System
 * Handles guild creation, hierarchy, ranks, and basic structure
 */

class GuildStructure {
    constructor(databaseClient, communicationService) {
        this.db = databaseClient;
        this.comm = communicationService;
        this.guildCache = new Map();
        this.memberCache = new Map();
    }

    /**
     * Create a new guild with charter and requirements
     */
    async createGuild(guildData) {
        const {
            name,
            tag,
            description,
            charter,
            leaderId,
            requirements,
            settings = {}
        } = guildData;

        try {
            // Validate guild name and tag
            await this.validateGuildName(name, tag);

            // Check if leader meets requirements
            await this.validateLeaderRequirements(leaderId, requirements);

            // Create guild record
            const guild = {
                id: this.generateGuildId(),
                name: name,
                tag: tag,
                description: description,
                charter: charter,
                leaderId: leaderId,
                requirements: {
                    minLevel: requirements.minLevel || 1,
                    classRequirements: requirements.classRequirements || [],
                    approvalRequired: requirements.approvalRequired || false,
                    applicationForm: requirements.applicationForm || null,
                    trialPeriod: requirements.trialPeriod || 7
                },
                settings: {
                    memberLimit: settings.memberLimit || 100,
                    bankAccess: settings.bankAccess || 'officers',
                    inviteOnly: settings.inviteOnly || false,
                    voiceChatRequired: settings.voiceChatRequired || false,
                    activityRequirement: settings.activityRequirement || 0,
                    ...settings
                },
                status: 'active',
                level: 1,
                experience: 0,
                created: new Date().toISOString(),
                lastModified: new Date().toISOString()
            };

            // Save to database
            await this.db.collection('guilds').insertOne(guild);

            // Create leader as first member
            await this.addMember(guild.id, leaderId, 'Leader', {
                joined: new Date().toISOString(),
                note: 'Guild Founder'
            });

            // Initialize guild bank
            await this.initializeGuildBank(guild.id);

            // Create default ranks
            await this.createDefaultRanks(guild.id);

            // Cache guild
            this.guildCache.set(guild.id, guild);

            // Notify system
            await this.comm.sendSystemNotification({
                type: 'guild_created',
                guildId: guild.id,
                guildName: guild.name,
                leaderId: leaderId
            });

            return {
                success: true,
                guild: guild
            };

        } catch (error) {
            console.error('Error creating guild:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Add member to guild with specific rank
     */
    async addMember(guildId, playerId, rank = 'Member', options = {}) {
        try {
            // Validate guild exists and has space
            const guild = await this.getGuild(guildId);
            if (!guild) {
                throw new Error('Guild not found');
            }

            const memberCount = await this.getMemberCount(guildId);
            if (memberCount >= guild.settings.memberLimit) {
                throw new Error('Guild is full');
            }

            // Check if player is already in a guild
            const currentGuild = await this.getPlayerGuild(playerId);
            if (currentGuild) {
                throw new Error('Player is already in a guild');
            }

            // Create member record
            const member = {
                guildId: guildId,
                playerId: playerId,
                rank: rank,
                status: 'active',
                joined: options.joined || new Date().toISOString(),
                contribution: {
                    experience: 0,
                    gold: 0,
                    items: [],
                    activities: 0
                },
                permissions: await this.getRankPermissions(guildId, rank),
                notes: options.note || '',
                lastActivity: new Date().toISOString(),
                trialEnds: rank === 'Initiate' ?
                    new Date(Date.now() + (guild.requirements.trialPeriod * 24 * 60 * 60 * 1000)).toISOString() :
                    null
            };

            // Save to database
            await this.db.collection('guild_members').insertOne(member);

            // Update cache
            this.memberCache.set(`${guildId}_${playerId}`, member);

            // Notify guild members
            await this.comm.sendGuildNotification(guildId, {
                type: 'member_joined',
                playerId: playerId,
                rank: rank,
                message: `New member joined: ${playerId}`
            });

            return {
                success: true,
                member: member
            };

        } catch (error) {
            console.error('Error adding member:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Remove member from guild
     */
    async removeMember(guildId, playerId, reason = '') {
        try {
            const member = await this.getMember(guildId, playerId);
            if (!member) {
                throw new Error('Member not found');
            }

            // Check permissions (can't remove leader without transferring leadership)
            if (member.rank === 'Leader') {
                throw new Error('Cannot remove guild leader. Transfer leadership first.');
            }

            // Remove from database
            await this.db.collection('guild_members').deleteOne({
                guildId: guildId,
                playerId: playerId
            });

            // Clear cache
            this.memberCache.delete(`${guildId}_${playerId}`);

            // Handle guild bank access
            await this.revokeBankAccess(guildId, playerId);

            // Notify guild members
            await this.comm.sendGuildNotification(guildId, {
                type: 'member_left',
                playerId: playerId,
                rank: member.rank,
                reason: reason,
                message: `Member ${playerId} has left the guild${reason ? ` (${reason})` : ''}`
            });

            return {
                success: true
            };

        } catch (error) {
            console.error('Error removing member:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Change member rank
     */
    async changeRank(guildId, playerId, newRank, changedBy) {
        try {
            const member = await this.getMember(guildId, playerId);
            if (!member) {
                throw new Error('Member not found');
            }

            const oldRank = member.rank;

            // Validate rank change permissions
            await this.validateRankChange(guildId, changedBy, oldRank, newRank);

            // Update member rank
            await this.db.collection('guild_members').updateOne(
                { guildId: guildId, playerId: playerId },
                {
                    $set: {
                        rank: newRank,
                        permissions: await this.getRankPermissions(guildId, newRank),
                        lastModified: new Date().toISOString()
                    }
                }
            );

            // Update cache
            member.rank = newRank;
            member.permissions = await this.getRankPermissions(guildId, newRank);
            this.memberCache.set(`${guildId}_${playerId}`, member);

            // Handle leader transfer
            if (newRank === 'Leader') {
                await this.transferLeadership(guildId, playerId, changedBy);
            }

            // Notify guild members
            await this.comm.sendGuildNotification(guildId, {
                type: 'rank_changed',
                playerId: playerId,
                oldRank: oldRank,
                newRank: newRank,
                changedBy: changedBy,
                message: `${playerId} has been promoted from ${oldRank} to ${newRank}`
            });

            return {
                success: true,
                oldRank: oldRank,
                newRank: newRank
            };

        } catch (error) {
            console.error('Error changing rank:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Create custom guild rank
     */
    async createCustomRank(guildId, rankData) {
        try {
            const {
                name,
                level,
                permissions,
                color,
                icon,
                description
            } = rankData;

            // Validate rank creation permissions
            const guild = await this.getGuild(guildId);
            if (!guild) {
                throw new Error('Guild not found');
            }

            // Create rank record
            const rank = {
                guildId: guildId,
                name: name,
                level: level,
                permissions: permissions,
                color: color || '#ffffff',
                icon: icon || '⭐',
                description: description || '',
                isCustom: true,
                created: new Date().toISOString()
            };

            // Save to database
            await this.db.collection('guild_ranks').insertOne(rank);

            // Update rank hierarchy cache
            await this.updateRankHierarchy(guildId);

            return {
                success: true,
                rank: rank
            };

        } catch (error) {
            console.error('Error creating custom rank:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Get guild information
     */
    async getGuild(guildId) {
        // Check cache first
        if (this.guildCache.has(guildId)) {
            return this.guildCache.get(guildId);
        }

        try {
            const guild = await this.db.collection('guilds').findOne({ id: guildId });
            if (guild) {
                this.guildCache.set(guildId, guild);
            }
            return guild;
        } catch (error) {
            console.error('Error fetching guild:', error);
            return null;
        }
    }

    /**
     * Get member information
     */
    async getMember(guildId, playerId) {
        // Check cache first
        const cacheKey = `${guildId}_${playerId}`;
        if (this.memberCache.has(cacheKey)) {
            return this.memberCache.get(cacheKey);
        }

        try {
            const member = await this.db.collection('guild_members').findOne({
                guildId: guildId,
                playerId: playerId
            });
            if (member) {
                this.memberCache.set(cacheKey, member);
            }
            return member;
        } catch (error) {
            console.error('Error fetching member:', error);
            return null;
        }
    }

    /**
     * Get all guild members
     */
    async getGuildMembers(guildId, options = {}) {
        try {
            const {
                rank = null,
                status = 'active',
                sortBy = 'rank',
                sortOrder = 'asc',
                limit = null,
                offset = 0
            } = options;

            let query = { guildId: guildId };

            if (rank) {
                query.rank = rank;
            }

            if (status) {
                query.status = status;
            }

            let members = await this.db.collection('guild_members')
                .find(query)
                .sort({ [sortBy]: sortOrder === 'asc' ? 1 : -1 })
                .skip(offset)
                .limit(limit || 999)
                .toArray();

            return members;
        } catch (error) {
            console.error('Error fetching guild members:', error);
            return [];
        }
    }

    /**
     * Initialize guild bank
     */
    async initializeGuildBank(guildId) {
        const bank = {
            guildId: guildId,
            gold: 0,
            tabs: [
                {
                    id: 'tab1',
                    name: 'General',
                    icon: '📦',
                    permissions: 'members',
                    items: [],
                    maxSlots: 50
                },
                {
                    id: 'tab2',
                    name: 'Equipment',
                    icon: '⚔️',
                    permissions: 'officers',
                    items: [],
                    maxSlots: 50
                },
                {
                    id: 'tab3',
                    name: 'Materials',
                    icon: '🔨',
                    permissions: 'members',
                    items: [],
                    maxSlots: 50
                }
            ],
            transactionLog: [],
            settings: {
                depositPermissions: 'members',
                withdrawPermissions: 'officers',
                maxDailyWithdrawals: 10,
                logTransactions: true
            },
            created: new Date().toISOString()
        };

        await this.db.collection('guild_banks').insertOne(bank);
        return bank;
    }

    /**
     * Create default ranks for new guild
     */
    async createDefaultRanks(guildId) {
        const defaultRanks = [
            {
                guildId: guildId,
                name: 'Leader',
                level: 100,
                permissions: [
                    'invite_members',
                    'kick_members',
                    'promote_members',
                    'demote_members',
                    'manage_ranks',
                    'manage_bank',
                    'manage_settings',
                    'disband_guild',
                    'start_wars',
                    'accept_alliances'
                ],
                color: '#FFD700',
                icon: '👑',
                description: 'Guild Leader - Full control',
                isCustom: false,
                created: new Date().toISOString()
            },
            {
                guildId: guildId,
                name: 'Officer',
                level: 75,
                permissions: [
                    'invite_members',
                    'kick_members',
                    'promote_members',
                    'manage_bank',
                    'start_events',
                    'accept_applications'
                ],
                color: '#C0C0C0',
                icon: '⭐',
                description: 'Guild Officer - Management role',
                isCustom: false,
                created: new Date().toISOString()
            },
            {
                guildId: guildId,
                name: 'Veteran',
                level: 50,
                permissions: [
                    'invite_members',
                    'access_bank',
                    'start_events',
                    'moderate_chat'
                ],
                color: '#CD7F32',
                icon: '🏆',
                description: 'Veteran Member - Trusted role',
                isCustom: false,
                created: new Date().toISOString()
            },
            {
                guildId: guildId,
                name: 'Member',
                level: 25,
                permissions: [
                    'access_bank',
                    'participate_events',
                    'guild_chat'
                ],
                color: '#00FF00',
                icon: '✓',
                description: 'Regular Guild Member',
                isCustom: false,
                created: new Date().toISOString()
            },
            {
                guildId: guildId,
                name: 'Initiate',
                level: 10,
                permissions: [
                    'guild_chat',
                    'participate_events'
                ],
                color: '#808080',
                icon: '🌱',
                description: 'New Member - Trial period',
                isCustom: false,
                created: new Date().toISOString()
            }
        ];

        await this.db.collection('guild_ranks').insertMany(defaultRanks);
        return defaultRanks;
    }

    /**
     * Helper methods
     */
    generateGuildId() {
        return 'guild_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
    }

    async validateGuildName(name, tag) {
        // Check if name or tag already exists
        const existing = await this.db.collection('guilds').findOne({
            $or: [
                { name: name },
                { tag: tag }
            ]
        });

        if (existing) {
            throw new Error('Guild name or tag already exists');
        }

        // Validate format
        if (!/^[a-zA-Z0-9\s]{3,32}$/.test(name)) {
            throw new Error('Guild name must be 3-32 characters, alphanumeric and spaces only');
        }

        if (!/^[A-Z0-9]{2,5}$/.test(tag)) {
            throw new Error('Guild tag must be 2-5 characters, uppercase letters and numbers only');
        }
    }

    async validateLeaderRequirements(leaderId, requirements) {
        // Get player data
        const player = await this.getPlayerData(leaderId);
        if (!player) {
            throw new Error('Leader not found');
        }

        // Check minimum level
        if (player.level < (requirements.minLevel || 1)) {
            throw new Error('Leader does not meet minimum level requirement');
        }

        // Check class requirements
        if (requirements.classRequirements && requirements.classRequirements.length > 0) {
            if (!requirements.classRequirements.includes(player.class)) {
                throw new Error('Leader class does not meet requirements');
            }
        }
    }

    async getMemberCount(guildId) {
        return await this.db.collection('guild_members').countDocuments({
            guildId: guildId,
            status: 'active'
        });
    }

    async getPlayerGuild(playerId) {
        const member = await this.db.collection('guild_members').findOne({
            playerId: playerId,
            status: 'active'
        });
        return member ? member.guildId : null;
    }

    async getRankPermissions(guildId, rankName) {
        const rank = await this.db.collection('guild_ranks').findOne({
            guildId: guildId,
            name: rankName
        });
        return rank ? rank.permissions : [];
    }

    async validateRankChange(guildId, changedBy, oldRank, newRank) {
        // Get permissions of person making the change
        const changer = await this.getMember(guildId, changedBy);
        if (!changer) {
            throw new Error('Permission denied');
        }

        const changerPermissions = changer.permissions;

        // Check if changer has permission to manage ranks
        if (!changerPermissions.includes('promote_members')) {
            throw new Error('Permission denied - Cannot manage ranks');
        }

        // Get rank levels to ensure proper hierarchy
        const ranks = await this.db.collection('guild_ranks')
            .find({ guildId: guildId })
            .sort({ level: -1 })
            .toArray();

        const oldRankLevel = ranks.find(r => r.name === oldRank)?.level || 0;
        const newRankLevel = ranks.find(r => r.name === newRank)?.level || 0;
        const changerLevel = ranks.find(r => r.name === changer.rank)?.level || 0;

        // Can only promote/demote to lower ranks than yourself
        if (newRankLevel >= changerLevel && changer.rank !== 'Leader') {
            throw new Error('Cannot promote to rank equal or higher than your own');
        }
    }

    async transferLeadership(guildId, newLeaderId, oldLeaderId) {
        // Demote old leader to Officer
        await this.db.collection('guild_members').updateOne(
            { guildId: guildId, playerId: oldLeaderId },
            { $set: { rank: 'Officer', lastModified: new Date().toISOString() } }
        );

        // Update guild leader
        await this.db.collection('guilds').updateOne(
            { id: guildId },
            { $set: { leaderId: newLeaderId, lastModified: new Date().toISOString() } }
        );
    }

    async revokeBankAccess(guildId, playerId) {
        await this.db.collection('guild_banks').updateOne(
            { guildId: guildId },
            { $pull: { 'tabs.$[].access': playerId } }
        );
    }

    async getPlayerData(playerId) {
        // This would integrate with the player system
        return await this.db.collection('players').findOne({ id: playerId });
    }

    async updateRankHierarchy(guildId) {
        // Clear rank cache for this guild
        const keys = Array.from(this.memberCache.keys()).filter(key => key.startsWith(guildId));
        keys.forEach(key => this.memberCache.delete(key));
    }
}

module.exports = GuildStructure;