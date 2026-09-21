/**
 * Alliance System
 * Manages multi-guild alliances, diplomatic relations, and coordinated activities
 */

class AllianceSystem {
    constructor(databaseClient, guildService, notificationService) {
        this.db = databaseClient;
        this.guilds = guildService;
        this.notifications = notificationService;
        this.allianceCache = new Map();
        this.diplomaticRelations = new Map();
        this.allianceChat = new Map();
    }

    /**
     * Create new alliance
     */
    async createAlliance(creatorGuildId, creatorId, allianceData) {
        try {
            const {
                name,
                tag,
                description,
                charter,
                requirements = {},
                settings = {}
            } = allianceData;

            // Validate creator permissions
            const creatorGuild = await this.guilds.getGuild(creatorGuildId);
            if (!creatorGuild) {
                throw new Error('Creator guild not found');
            }

            const creatorMember = await this.guilds.getGuildMember(creatorGuildId, creatorId);
            if (!this.hasAlliancePermission(creatorMember, 'create_alliance')) {
                throw new Error('No permission to create alliance');
            }

            // Check if guild is already in an alliance
            const existingAlliance = await this.getGuildAlliance(creatorGuildId);
            if (existingAlliance) {
                throw new Error('Guild is already in an alliance');
            }

            // Validate alliance name and tag
            await this.validateAllianceName(name, tag);

            // Create alliance
            const alliance = {
                id: this.generateAllianceId(),
                name: name,
                tag: tag,
                description: description,
                charter: charter,
                creatorGuildId: creatorGuildId,
                leaderGuildId: creatorGuildId,
                memberGuilds: [creatorGuildId],
                requirements: {
                    minGuildLevel: requirements.minGuildLevel || 1,
                    minMemberCount: requirements.minMemberCount || 10,
                    maxGuilds: requirements.maxGuilds || 8,
                    approvalRequired: requirements.approvalRequired || true,
                    votingRequired: requirements.votingRequired || false,
                    voteThreshold: requirements.voteThreshold || 0.6,
                    ...requirements
                },
                settings: {
                    sharedChat: settings.sharedChat || true,
                    sharedEvents: settings.sharedEvents || true,
                    sharedBank: settings.sharedBank || false,
                    sharedResources: settings.sharedResources || false,
                    allianceWars: settings.allianceWars || true,
                    autoAcceptRequests: settings.autoAcceptRequests || false,
                    memberContribution: settings.memberContribution || 0,
                    ...settings
                },
                resources: {
                    allianceBank: 0,
                    sharedStorage: [],
                    territories: [],
                    influence: 0
                },
                status: 'active',
                level: 1,
                experience: 0,
                created: new Date().toISOString(),
                lastModified: new Date().toISOString()
            };

            // Save to database
            await this.db.collection('alliances').insertOne(alliance);

            // Update guild's alliance status
            await this.updateGuildAllianceStatus(creatorGuildId, alliance.id, 'founder');

            // Initialize alliance chat
            await this.initializeAllianceChat(alliance.id);

            // Cache alliance
            this.allianceCache.set(alliance.id, alliance);

            // Notify all guild members
            await this.notifyAllianceCreated(creatorGuildId, alliance);

            return {
                success: true,
                alliance: alliance
            };

        } catch (error) {
            console.error('Error creating alliance:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Apply to join alliance
     */
    async applyToAlliance(allianceId, guildId, applicantId, applicationData = {}) {
        try {
            const {
                message = '',
                contribution = {},
                expectations = {}
            } = applicationData;

            // Get alliance and guild
            const alliance = await this.getAlliance(allianceId);
            if (!alliance) {
                throw new Error('Alliance not found');
            }

            const guild = await this.guilds.getGuild(guildId);
            if (!guild) {
                throw new Error('Guild not found');
            }

            // Check if guild is already in an alliance
            const existingAlliance = await this.getGuildAlliance(guildId);
            if (existingAlliance) {
                throw new Error('Guild is already in an alliance');
            }

            // Validate applicant permissions
            const applicant = await this.guilds.getGuildMember(guildId, applicantId);
            if (!this.hasAlliancePermission(applicant, 'apply_alliance')) {
                throw new Error('No permission to apply to alliances');
            }

            // Check requirements
            const requirementsCheck = await this.checkAllianceRequirements(alliance, guild);
            if (!requirementsCheck.met) {
                throw new Error(requirementsCheck.reason);
            }

            // Check if already applied
            const existingApplication = await this.db.collection('alliance_applications').findOne({
                allianceId: allianceId,
                guildId: guildId,
                status: 'pending'
            });

            if (existingApplication) {
                throw new Error('Application already submitted');
            }

            // Create application
            const application = {
                id: this.generateApplicationId(),
                allianceId: allianceId,
                guildId: guildId,
                guildName: guild.name,
                guildTag: guild.tag,
                applicantId: applicantId,
                applicantName: applicant.playerName,
                message: message,
                contribution: contribution,
                expectations: expectations,
                guildData: {
                    level: guild.level,
                    memberCount: await this.guilds.getMemberCount(guildId),
                    achievements: guild.achievements || [],
                    resources: guild.resources || {}
                },
                status: 'pending',
                votes: [],
                submittedAt: new Date().toISOString(),
                reviewedAt: null,
                reviewedBy: null,
                response: null
            };

            // Save application
            await this.db.collection('alliance_applications').insertOne(application);

            // Notify alliance leadership
            await this.notifyAllianceApplication(alliance, application);

            // Auto-accept if enabled
            if (alliance.settings.autoAcceptRequests && requirementsCheck.met) {
                return await this.acceptApplication(allianceId, application.id, 'system');
            }

            return {
                success: true,
                application: application
            };

        } catch (error) {
            console.error('Error applying to alliance:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Accept alliance application
     */
    async acceptApplication(allianceId, applicationId, acceptedBy) {
        try {
            const alliance = await this.getAlliance(allianceId);
            if (!alliance) {
                throw new Error('Alliance not found');
            }

            const application = await this.db.collection('alliance_applications').findOne({
                id: applicationId,
                allianceId: allianceId
            });

            if (!application) {
                throw new Error('Application not found');
            }

            if (application.status !== 'pending') {
                throw new Error('Application already processed');
            }

            // Validate permissions
            const acceptor = await this.getAcceptingMember(allianceId, acceptedBy);
            if (!acceptor) {
                throw new Error('No permission to accept applications');
            }

            // Check alliance capacity
            if (alliance.memberGuilds.length >= alliance.requirements.maxGuilds) {
                throw new Error('Alliance is at maximum capacity');
            }

            // Handle voting if required
            if (alliance.requirements.votingRequired) {
                return await this.processApplicationVote(allianceId, applicationId, acceptedBy, 'accept');
            }

            // Accept application
            await this.db.collection('alliance_applications').updateOne(
                { id: applicationId },
                {
                    $set: {
                        status: 'accepted',
                        reviewedAt: new Date().toISOString(),
                        reviewedBy: acceptedBy,
                        response: 'Application accepted'
                    }
                }
            );

            // Add guild to alliance
            await this.addGuildToAlliance(allianceId, application.guildId);

            // Update alliance
            alliance.memberGuilds.push(application.guildId);
            alliance.lastModified = new Date().toISOString();
            this.allianceCache.set(allianceId, alliance);

            // Notify all parties
            await this.notifyApplicationAccepted(alliance, application, acceptedBy);

            return {
                success: true,
                alliance: alliance
            };

        } catch (error) {
            console.error('Error accepting application:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Reject alliance application
     */
    async rejectApplication(allianceId, applicationId, rejectedBy, reason = '') {
        try {
            const alliance = await this.getAlliance(allianceId);
            if (!alliance) {
                throw new Error('Alliance not found');
            }

            const application = await this.db.collection('alliance_applications').findOne({
                id: applicationId,
                allianceId: allianceId
            });

            if (!application) {
                throw new Error('Application not found');
            }

            if (application.status !== 'pending') {
                throw new Error('Application already processed');
            }

            // Validate permissions
            const rejector = await this.getAcceptingMember(allianceId, rejectedBy);
            if (!rejector) {
                throw new Error('No permission to reject applications');
            }

            // Handle voting if required
            if (alliance.requirements.votingRequired) {
                return await this.processApplicationVote(allianceId, applicationId, rejectedBy, 'reject');
            }

            // Reject application
            await this.db.collection('alliance_applications').updateOne(
                { id: applicationId },
                {
                    $set: {
                        status: 'rejected',
                        reviewedAt: new Date().toISOString(),
                        reviewedBy: rejectedBy,
                        response: reason || 'Application rejected'
                    }
                }
            );

            // Notify applicant
            await this.notifyApplicationRejected(application, rejectedBy, reason);

            return {
                success: true
            };

        } catch (error) {
            console.error('Error rejecting application:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Send alliance invitation
     */
    async sendAllianceInvitation(allianceId, inviterId, targetGuildId, message = '') {
        try {
            const alliance = await this.getAlliance(allianceId);
            if (!alliance) {
                throw new Error('Alliance not found');
            }

            // Validate inviter permissions
            const inviter = await this.getInvitingMember(allianceId, inviterId);
            if (!inviter) {
                throw new Error('No permission to send invitations');
            }

            // Check target guild
            const targetGuild = await this.guilds.getGuild(targetGuildId);
            if (!targetGuild) {
                throw new Error('Target guild not found');
            }

            // Check if target guild is already in an alliance
            const targetAlliance = await this.getGuildAlliance(targetGuildId);
            if (targetAlliance) {
                throw new Error('Target guild is already in an alliance');
            }

            // Check if already invited
            const existingInvitation = await this.db.collection('alliance_invitations').findOne({
                allianceId: allianceId,
                guildId: targetGuildId,
                status: 'pending'
            });

            if (existingInvitation) {
                throw new Error('Invitation already sent');
            }

            // Create invitation
            const invitation = {
                id: this.generateInvitationId(),
                allianceId: allianceId,
                allianceName: alliance.name,
                guildId: targetGuildId,
                guildName: targetGuild.name,
                inviterId: inviterId,
                inviterName: inviter.playerName,
                message: message,
                status: 'pending',
                expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days
                sentAt: new Date().toISOString(),
                respondedAt: null,
                respondedBy: null
            };

            // Save invitation
            await this.db.collection('alliance_invitations').insertOne(invitation);

            // Notify target guild leadership
            await this.notifyAllianceInvitation(targetGuildId, invitation);

            return {
                success: true,
                invitation: invitation
            };

        } catch (error) {
            console.error('Error sending alliance invitation:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Respond to alliance invitation
     */
    async respondToInvitation(invitationId, guildId, responderId, response) {
        try {
            const invitation = await this.db.collection('alliance_invitations').findOne({
                id: invitationId,
                guildId: guildId
            });

            if (!invitation) {
                throw new Error('Invitation not found');
            }

            if (invitation.status !== 'pending') {
                throw new Error('Invitation already processed');
            }

            if (new Date() > new Date(invitation.expiresAt)) {
                throw new Error('Invitation has expired');
            }

            // Validate responder permissions
            const responder = await this.guilds.getGuildMember(guildId, responderId);
            if (!this.hasAlliancePermission(responder, 'accept_alliance')) {
                throw new Error('No permission to respond to alliance invitations');
            }

            const alliance = await this.getAlliance(invitation.allianceId);
            if (!alliance) {
                throw new Error('Alliance no longer exists');
            }

            // Update invitation
            await this.db.collection('alliance_invitations').updateOne(
                { id: invitationId },
                {
                    $set: {
                        status: response,
                        respondedAt: new Date().toISOString(),
                        respondedBy: responderId
                    }
                }
            );

            if (response === 'accepted') {
                // Add guild to alliance
                await this.addGuildToAlliance(invitation.allianceId, guildId);

                // Update alliance
                alliance.memberGuilds.push(guildId);
                alliance.lastModified = new Date().toISOString();
                this.allianceCache.set(invitation.allianceId, alliance);

                // Notify alliance members
                await this.notifyInvitationAccepted(alliance, invitation, responder);

                return {
                    success: true,
                    alliance: alliance
                };
            } else {
                // Notify alliance of rejection
                await this.notifyInvitationRejected(alliance, invitation, responder);

                return {
                    success: true,
                    message: 'Invitation declined'
                };
            }

        } catch (error) {
            console.error('Error responding to invitation:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Leave alliance
     */
    async leaveAlliance(guildId, memberId, reason = '') {
        try {
            const alliance = await this.getGuildAlliance(guildId);
            if (!alliance) {
                throw new Error('Guild is not in an alliance');
            }

            // Validate permissions
            const member = await this.guilds.getGuildMember(guildId, memberId);
            if (!this.hasAlliancePermission(member, 'leave_alliance')) {
                throw new Error('No permission to leave alliance');
            }

            // Cannot leave if founder (must transfer leadership first)
            if (alliance.leaderGuildId === guildId && alliance.memberGuilds.length > 1) {
                throw new Error('Alliance leader must transfer leadership before leaving');
            }

            // Remove guild from alliance
            await this.removeGuildFromAlliance(alliance.id, guildId);

            // Update alliance
            alliance.memberGuilds = alliance.memberGuilds.filter(id => id !== guildId);
            alliance.lastModified = new Date().toISOString();

            // Handle alliance dissolution if only one guild left
            if (alliance.memberGuilds.length <= 1) {
                await this.dissolveAlliance(alliance.id);
                return {
                    success: true,
                    allianceDissolved: true
                };
            }

            // Transfer leadership if leader left
            if (alliance.leaderGuildId === guildId) {
                alliance.leaderGuildId = alliance.memberGuilds[0];
                await this.db.collection('alliances').updateOne(
                    { id: alliance.id },
                    { $set: { leaderGuildId: alliance.memberGuilds[0] } }
                );
            }

            // Update cache
            this.allianceCache.set(alliance.id, alliance);

            // Notify all alliance members
            await this.notifyAllianceMemberLeft(alliance, guildId, reason);

            return {
                success: true,
                alliance: alliance
            };

        } catch (error) {
            console.error('Error leaving alliance:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Transfer alliance leadership
     */
    async transferAllianceLeadership(allianceId, currentLeaderId, newLeaderGuildId) {
        try {
            const alliance = await this.getAlliance(allianceId);
            if (!alliance) {
                throw new Error('Alliance not found');
            }

            if (alliance.leaderGuildId !== currentLeaderId) {
                throw new Error('Not the current alliance leader');
            }

            if (!alliance.memberGuilds.includes(newLeaderGuildId)) {
                throw new Error('Target guild is not in the alliance');
            }

            // Validate permissions
            const currentLeader = await this.guilds.getGuildMember(currentLeaderId, currentLeaderId);
            if (!this.hasAlliancePermission(currentLeader, 'transfer_leadership')) {
                throw new Error('No permission to transfer leadership');
            }

            // Update alliance leader
            await this.db.collection('alliances').updateOne(
                { id: allianceId },
                {
                    $set: {
                        leaderGuildId: newLeaderGuildId,
                        lastModified: new Date().toISOString()
                    }
                }
            );

            // Update cache
            alliance.leaderGuildId = newLeaderGuildId;
            alliance.lastModified = new Date().toISOString();
            this.allianceCache.set(allianceId, alliance);

            // Notify alliance members
            await this.notifyLeadershipTransferred(alliance, currentLeaderId, newLeaderGuildId);

            return {
                success: true,
                alliance: alliance
            };

        } catch (error) {
            console.error('Error transferring alliance leadership:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Create alliance-wide event
     */
    async createAllianceEvent(allianceId, creatorId, eventData) {
        try {
            const alliance = await this.getAlliance(allianceId);
            if (!alliance) {
                throw new Error('Alliance not found');
            }

            // Validate permissions
            const creator = await this.getEventCreatorMember(allianceId, creatorId);
            if (!creator) {
                throw new Error('No permission to create alliance events');
            }

            // Check if alliance events are enabled
            if (!alliance.settings.sharedEvents) {
                throw new Error('Alliance events are disabled');
            }

            // Create alliance event
            const allianceEvent = {
                id: this.generateEventId(),
                allianceId: allianceId,
                ...eventData,
                creatorId: creatorId,
                creatorGuildId: creator.guildId,
                participatingGuilds: alliance.memberGuilds,
                status: 'scheduled',
                created: new Date().toISOString()
            };

            // Save event
            await this.db.collection('alliance_events').insertOne(allianceEvent);

            // Notify all member guilds
            await this.notifyAllianceEventCreated(alliance, allianceEvent);

            return {
                success: true,
                event: allianceEvent
            };

        } catch (error) {
            console.error('Error creating alliance event:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Send alliance chat message
     */
    async sendAllianceChat(allianceId, senderId, message, channel = 'general') {
        try {
            const alliance = await this.getAlliance(allianceId);
            if (!alliance) {
                throw new Error('Alliance not found');
            }

            // Check if alliance chat is enabled
            if (!alliance.settings.sharedChat) {
                throw new Error('Alliance chat is disabled');
            }

            // Validate sender
            const sender = await this.getAllianceMember(allianceId, senderId);
            if (!sender) {
                throw new Error('Not a member of this alliance');
            }

            // Check chat permissions
            if (!this.hasAlliancePermission(sender, 'alliance_chat')) {
                throw new Error('No permission to use alliance chat');
            }

            // Create chat message
            const chatMessage = {
                id: this.generateMessageId(),
                allianceId: allianceId,
                senderId: senderId,
                senderName: sender.playerName,
                senderGuild: sender.guildName,
                senderGuildTag: sender.guildTag,
                senderRank: sender.rank,
                channel: channel,
                content: message.trim(),
                timestamp: new Date().toISOString(),
                reactions: []
            };

            // Save message
            await this.db.collection('alliance_chat').insertOne(chatMessage);

            // Broadcast to all alliance members
            await this.broadcastToAlliance(allianceId, chatMessage);

            return {
                success: true,
                message: chatMessage
            };

        } catch (error) {
            console.error('Error sending alliance chat:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Declare alliance war
     */
    async declareAllianceWar(allianceId, declarerId, targetAllianceId, warData) {
        try {
            const alliance = await this.getAlliance(allianceId);
            const targetAlliance = await this.getAlliance(targetAllianceId);

            if (!alliance || !targetAlliance) {
                throw new Error('Alliance not found');
            }

            // Validate permissions
            const declarer = await this.getWarDeclarerMember(allianceId, declarerId);
            if (!declarer) {
                throw new Error('No permission to declare alliance wars');
            }

            // Check if alliance wars are enabled
            if (!alliance.settings.allianceWars) {
                throw new Error('Alliance wars are disabled');
            }

            // Check for existing war
            const existingWar = await this.db.collection('alliance_wars').findOne({
                $or: [
                    { alliance1Id: allianceId, alliance2Id: targetAllianceId, status: 'active' },
                    { alliance1Id: targetAllianceId, alliance2Id: allianceId, status: 'active' }
                ]
            });

            if (existingWar) {
                throw new Error('War already exists between these alliances');
            }

            // Create war declaration
            const war = {
                id: this.generateWarId(),
                alliance1Id: allianceId,
                alliance2Id: targetAllianceId,
                declaredBy: declarerId,
                declaredByAlliance: allianceId,
                warType: warData.warType || 'territory',
                objectives: warData.objectives || [],
                rules: warData.rules || [],
                duration: warData.duration || 7 * 24 * 60 * 60 * 1000, // 7 days
                stakes: warData.stakes || {},
                status: 'active',
                startedAt: new Date().toISOString(),
                endsAt: new Date(Date.now() + (warData.duration || 7 * 24 * 60 * 60 * 1000)).toISOString(),
                statistics: {
                    battles: [],
                    casualties: { [allianceId]: 0, [targetAllianceId]: 0 },
                    territoryChanges: [],
                    victories: { [allianceId]: 0, [targetAllianceId]: 0 }
                }
            };

            // Save war
            await this.db.collection('alliance_wars').insertOne(war);

            // Update diplomatic relations
            await this.updateDiplomaticRelation(allianceId, targetAllianceId, 'war');

            // Notify both alliances
            await this.notifyAllianceWarDeclared(alliance, targetAlliance, war);

            return {
                success: true,
                war: war
            };

        } catch (error) {
            console.error('Error declaring alliance war:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Helper methods
     */
    generateAllianceId() {
        return 'alliance_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    generateApplicationId() {
        return 'app_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    generateInvitationId() {
        return 'inv_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    generateEventId() {
        return 'aevt_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    generateMessageId() {
        return 'amsg_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    generateWarId() {
        return 'war_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    async validateAllianceName(name, tag) {
        // Check if name or tag already exists
        const existing = await this.db.collection('alliances').findOne({
            $or: [
                { name: name },
                { tag: tag }
            ]
        });

        if (existing) {
            throw new Error('Alliance name or tag already exists');
        }

        // Validate format
        if (!/^[a-zA-Z0-9\s]{3,32}$/.test(name)) {
            throw new Error('Alliance name must be 3-32 characters, alphanumeric and spaces only');
        }

        if (!/^[A-Z0-9]{2,5}$/.test(tag)) {
            throw new Error('Alliance tag must be 2-5 characters, uppercase letters and numbers only');
        }
    }

    async checkAllianceRequirements(alliance, guild) {
        // Check minimum guild level
        if (guild.level < alliance.requirements.minGuildLevel) {
            return {
                met: false,
                reason: `Guild level ${alliance.requirements.minGuildLevel} required`
            };
        }

        // Check minimum member count
        const memberCount = await this.guilds.getMemberCount(guild.id);
        if (memberCount < alliance.requirements.minMemberCount) {
            return {
                met: false,
                reason: `Minimum ${alliance.requirements.minMemberCount} members required`
            };
        }

        return { met: true };
    }

    hasAlliancePermission(member, permission) {
        if (!member) return false;

        const permissions = {
            'Leader': [
                'create_alliance', 'apply_alliance', 'accept_alliance', 'leave_alliance',
                'transfer_leadership', 'create_events', 'declare_wars', 'alliance_chat',
                'manage_alliance', 'invite_guilds', 'kick_guilds'
            ],
            'Officer': [
                'apply_alliance', 'accept_alliance', 'create_events', 'alliance_chat',
                'invite_guilds'
            ],
            'Veteran': [
                'apply_alliance', 'create_events', 'alliance_chat'
            ],
            'Member': [
                'alliance_chat'
            ]
        };

        return permissions[member.rank]?.includes(permission) || false;
    }

    async getAlliance(allianceId) {
        // Check cache first
        if (this.allianceCache.has(allianceId)) {
            return this.allianceCache.get(allianceId);
        }

        try {
            const alliance = await this.db.collection('alliances').findOne({ id: allianceId });
            if (alliance) {
                this.allianceCache.set(allianceId, alliance);
            }
            return alliance;
        } catch (error) {
            console.error('Error fetching alliance:', error);
            return null;
        }
    }

    async getGuildAlliance(guildId) {
        try {
            return await this.db.collection('alliances').findOne({
                memberGuilds: guildId
            });
        } catch (error) {
            console.error('Error fetching guild alliance:', error);
            return null;
        }
    }

    async getAllianceMember(allianceId, playerId) {
        try {
            const alliance = await this.getAlliance(allianceId);
            if (!alliance) return null;

            // Check each guild in the alliance
            for (const guildId of alliance.memberGuilds) {
                const member = await this.guilds.getGuildMember(guildId, playerId);
                if (member) {
                    const guild = await this.guilds.getGuild(guildId);
                    return {
                        ...member,
                        guildId: guildId,
                        guildName: guild.name,
                        guildTag: guild.tag
                    };
                }
            }

            return null;
        } catch (error) {
            console.error('Error fetching alliance member:', error);
            return null;
        }
    }

    async getAcceptingMember(allianceId, playerId) {
        const member = await this.getAllianceMember(allianceId, playerId);
        if (!member) return null;

        const permissions = ['Leader', 'Officer'];
        return permissions.includes(member.rank) ? member : null;
    }

    async getInvitingMember(allianceId, playerId) {
        return await this.getAcceptingMember(allianceId, playerId);
    }

    async getEventCreatorMember(allianceId, playerId) {
        const member = await this.getAllianceMember(allianceId, playerId);
        if (!member) return null;

        const permissions = ['Leader', 'Officer', 'Veteran'];
        return permissions.includes(member.rank) ? member : null;
    }

    async getWarDeclarerMember(allianceId, playerId) {
        const member = await this.getAllianceMember(allianceId, playerId);
        if (!member) return null;

        const permissions = ['Leader'];
        return permissions.includes(member.rank) ? member : null;
    }

    async updateGuildAllianceStatus(guildId, allianceId, role) {
        await this.db.collection('guilds').updateOne(
            { id: guildId },
            {
                $set: {
                    allianceId: allianceId,
                    allianceRole: role,
                    allianceJoined: new Date().toISOString()
                }
            }
        );
    }

    async addGuildToAlliance(allianceId, guildId) {
        await this.updateGuildAllianceStatus(guildId, allianceId, 'member');
    }

    async removeGuildFromAlliance(allianceId, guildId) {
        await this.db.collection('guilds').updateOne(
            { id: guildId },
            {
                $unset: {
                    allianceId: '',
                    allianceRole: '',
                    allianceJoined: ''
                }
            }
        );
    }

    async dissolveAlliance(allianceId) {
        // Remove alliance status from all member guilds
        const alliance = await this.getAlliance(allianceId);
        if (alliance) {
            for (const guildId of alliance.memberGuilds) {
                await this.removeGuildFromAlliance(allianceId, guildId);
            }
        }

        // Delete alliance
        await this.db.collection('alliances').deleteOne({ id: allianceId });
        this.allianceCache.delete(allianceId);

        // Notify former members
        await this.notifyAllianceDissolved(alliance);
    }

    async updateDiplomaticRelation(alliance1Id, alliance2Id, status) {
        const relation = {
            alliance1Id: alliance1Id,
            alliance2Id: alliance2Id,
            status: status, // 'friendly', 'neutral', 'hostile', 'war'
            established: new Date().toISOString(),
            lastModified: new Date().toISOString()
        };

        await this.db.collection('alliance_relations').replaceOne(
            {
                $or: [
                    { alliance1Id: alliance1Id, alliance2Id: alliance2Id },
                    { alliance1Id: alliance2Id, alliance2Id: alliance1Id }
                ]
            },
            relation,
            { upsert: true }
        );

        this.diplomaticRelations.set(`${alliance1Id}_${alliance2Id}`, relation);
    }

    async processApplicationVote(allianceId, applicationId, voterId, vote) {
        // Implementation for voting system
        // This would handle the voting logic for alliance applications
        return { success: true, vote: vote };
    }

    async initializeAllianceChat(allianceId) {
        // Initialize alliance chat channels
        const channels = [
            { id: 'general', name: 'General', type: 'text' },
            { id: 'leadership', name: 'Leadership', type: 'restricted' },
            { id: 'events', name: 'Events', type: 'text' },
            { id: 'strategy', name: 'Strategy', type: 'restricted' }
        ];

        for (const channel of channels) {
            await this.db.collection('alliance_chat_channels').insertOne({
                allianceId: allianceId,
                ...channel,
                created: new Date().toISOString()
            });
        }
    }

    async broadcastToAlliance(allianceId, message) {
        const alliance = await this.getAlliance(allianceId);
        if (!alliance) return;

        for (const guildId of alliance.memberGuilds) {
            await this.notifications.sendGuildNotification(guildId, {
                type: 'alliance_message',
                message: message
            });
        }
    }

    // Notification methods
    async notifyAllianceCreated(guildId, alliance) {
        await this.notifications.sendGuildNotification(guildId, {
            type: 'alliance_created',
            alliance: alliance
        });
    }

    async notifyAllianceApplication(alliance, application) {
        for (const guildId of alliance.memberGuilds) {
            await this.notifications.sendGuildNotification(guildId, {
                type: 'alliance_application',
                application: application
            });
        }
    }

    async notifyApplicationAccepted(alliance, application, acceptedBy) {
        // Notify applicant guild
        await this.notifications.sendGuildNotification(application.guildId, {
            type: 'alliance_application_accepted',
            alliance: alliance,
            acceptedBy: acceptedBy
        });

        // Notify alliance members
        for (const guildId of alliance.memberGuilds) {
            await this.notifications.sendGuildNotification(guildId, {
                type: 'alliance_new_member',
                newGuild: application.guildId
            });
        }
    }

    async notifyApplicationRejected(application, rejectedBy, reason) {
        await this.notifications.sendGuildNotification(application.guildId, {
            type: 'alliance_application_rejected',
            rejectedBy: rejectedBy,
            reason: reason
        });
    }

    async notifyAllianceInvitation(guildId, invitation) {
        await this.notifications.sendGuildNotification(guildId, {
            type: 'alliance_invitation',
            invitation: invitation
        });
    }

    async notifyInvitationAccepted(alliance, invitation, responder) {
        // Notify alliance members
        for (const guildId of alliance.memberGuilds) {
            await this.notifications.sendGuildNotification(guildId, {
                type: 'alliance_new_member',
                newGuild: invitation.guildId
            });
        }
    }

    async notifyInvitationRejected(alliance, invitation, responder) {
        // Notify alliance leadership
        for (const guildId of alliance.memberGuilds) {
            await this.notifications.sendGuildNotification(guildId, {
                type: 'alliance_invitation_rejected',
                invitation: invitation,
                rejectedBy: responder
            });
        }
    }

    async notifyAllianceMemberLeft(alliance, guildId, reason) {
        for (const memberId of alliance.memberGuilds) {
            if (memberId !== guildId) {
                await this.notifications.sendGuildNotification(memberId, {
                    type: 'alliance_member_left',
                    guildId: guildId,
                    reason: reason
                });
            }
        }
    }

    async notifyLeadershipTransferred(alliance, oldLeaderId, newLeaderId) {
        for (const guildId of alliance.memberGuilds) {
            await this.notifications.sendGuildNotification(guildId, {
                type: 'alliance_leadership_transferred',
                oldLeaderId: oldLeaderId,
                newLeaderId: newLeaderId
            });
        }
    }

    async notifyAllianceEventCreated(alliance, event) {
        for (const guildId of alliance.memberGuilds) {
            await this.notifications.sendGuildNotification(guildId, {
                type: 'alliance_event_created',
                event: event
            });
        }
    }

    async notifyAllianceWarDeclared(alliance, targetAlliance, war) {
        // Notify attacking alliance
        for (const guildId of alliance.memberGuilds) {
            await this.notifications.sendGuildNotification(guildId, {
                type: 'alliance_war_declared',
                war: war,
                side: 'attacker'
            });
        }

        // Notify defending alliance
        for (const guildId of targetAlliance.memberGuilds) {
            await this.notifications.sendGuildNotification(guildId, {
                type: 'alliance_war_declared',
                war: war,
                side: 'defender'
            });
        }
    }

    async notifyAllianceDissolved(alliance) {
        for (const guildId of alliance.memberGuilds) {
            await this.notifications.sendGuildNotification(guildId, {
                type: 'alliance_dissolved',
                alliance: alliance
            });
        }
    }
}

module.exports = AllianceSystem;