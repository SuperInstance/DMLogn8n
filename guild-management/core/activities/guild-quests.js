/**
 * Guild Quests System
 * Manages guild-specific quests, missions, and objectives
 */

class GuildQuests {
    constructor(databaseClient, rewardService, notificationService) {
        this.db = databaseClient;
        this.rewards = rewardService;
        this.notifications = notificationService;
        this.activeQuests = new Map();
        this.questTemplates = new Map();
        this.questProgress = new Map();
    }

    /**
     * Create guild quest
     */
    async createGuildQuest(guildId, creatorId, questData) {
        try {
            const {
                title,
                description,
                type,
                difficulty,
                objectives = [],
                requirements = {},
                rewards = {},
                timeLimit = null,
                maxParticipants = null,
                repeatable = false,
                settings = {}
            } = questData;

            // Validate permissions
            const member = await this.getGuildMember(guildId, creatorId);
            if (!this.hasPermission(member, 'create_quests')) {
                throw new Error('No permission to create guild quests');
            }

            // Validate quest data
            const validation = this.validateQuestData(questData);
            if (!validation.valid) {
                throw new Error(validation.errors.join(', '));
            }

            // Create quest
            const quest = {
                id: this.generateQuestId(),
                guildId: guildId,
                title: title,
                description: description,
                type: type, // 'collect', 'defeat', 'explore', 'craft', 'social', 'raid', 'pvp'
                difficulty: difficulty, // 'easy', 'medium', 'hard', 'epic', 'legendary'
                creatorId: creatorId,
                creatorName: member.playerName,
                objectives: objectives.map((obj, index) => ({
                    id: index + 1,
                    ...obj,
                    completed: false,
                    progress: 0
                })),
                requirements: {
                    minLevel: requirements.minLevel || 1,
                    minRank: requirements.minRank || 'Initiate',
                    classRequirements: requirements.classRequirements || [],
                    prerequisites: requirements.prerequisites || [],
                    ...requirements
                },
                rewards: {
                    experience: rewards.experience || 0,
                    gold: rewards.gold || 0,
                    guildContribution: rewards.guildContribution || 0,
                    items: rewards.items || [],
                    achievements: rewards.achievements || [],
                    reputation: rewards.reputation || 0,
                    ...rewards
                },
                settings: {
                    autoAccept: settings.autoAccept || false,
                    shareProgress: settings.shareProgress || true,
                    allowLateJoin: settings.allowLateJoin || false,
                    requiredParticipants: settings.requiredParticipants || 1,
                    ...settings
                },
                timeLimit: timeLimit,
                maxParticipants: maxParticipants,
                repeatable: repeatable,
                status: 'active',
                participants: [],
                progress: {},
                completions: [],
                statistics: {
                    totalAttempts: 0,
                    successfulCompletions: 0,
                    averageCompletionTime: 0
                },
                metadata: {
                    created: new Date().toISOString(),
                    lastModified: new Date().toISOString()
                }
            };

            // Save to database
            await this.db.collection('guild_quests').insertOne(quest);

            // Cache quest
            this.activeQuests.set(quest.id, quest);

            // Notify guild members
            await this.notifyQuestCreated(guildId, quest);

            return {
                success: true,
                quest: quest
            };

        } catch (error) {
            console.error('Error creating guild quest:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Accept guild quest
     */
    async acceptQuest(questId, playerId, teamData = null) {
        try {
            const quest = await this.getQuest(questId);
            if (!quest) {
                throw new Error('Quest not found');
            }

            // Validate participant
            const member = await this.getGuildMember(quest.guildId, playerId);
            if (!member) {
                throw new Error('Member not found');
            }

            // Check requirements
            const requirementsCheck = await this.checkQuestRequirements(quest, member);
            if (!requirementsCheck.met) {
                throw new Error(requirementsCheck.reason);
            }

            // Check if already accepted
            const existingParticipant = quest.participants.find(p => p.playerId === playerId);
            if (existingParticipant) {
                throw new Error('Already accepted this quest');
            }

            // Check participant limit
            if (quest.maxParticipants && quest.participants.length >= quest.maxParticipants) {
                throw new Error('Quest is full');
            }

            // Create participant entry
            const participant = {
                playerId: playerId,
                playerName: member.playerName,
                rank: member.rank,
                acceptedAt: new Date().toISOString(),
                status: 'active',
                progress: quest.objectives.map(obj => ({
                    objectiveId: obj.id,
                    progress: 0,
                    completed: false,
                    data: {}
                })),
                teamId: teamData?.teamId || null,
                contributions: {
                    timeSpent: 0,
                    resourcesUsed: 0,
                    enemiesDefeated: 0
                },
                lastActivity: new Date().toISOString()
            };

            // Add participant
            await this.db.collection('guild_quests').updateOne(
                { id: questId },
                {
                    $push: { participants: participant },
                    $inc: { 'statistics.totalAttempts': 1 },
                    $set: { 'metadata.lastModified': new Date().toISOString() }
                }
            );

            // Update cache
            quest.participants.push(participant);
            this.activeQuests.set(questId, quest);

            // Initialize progress tracking
            this.questProgress.set(`${questId}_${playerId}`, {
                questId: questId,
                playerId: playerId,
                progress: participant.progress,
                startTime: new Date().toISOString()
            });

            // Notify participant
            await this.notifyQuestAccepted(playerId, quest);

            return {
                success: true,
                participant: participant
            };

        } catch (error) {
            console.error('Error accepting quest:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Update quest progress
     */
    async updateQuestProgress(questId, playerId, progressData) {
        try {
            const quest = await this.getQuest(questId);
            if (!quest) {
                throw new Error('Quest not found');
            }

            // Find participant
            const participant = quest.participants.find(p => p.playerId === playerId);
            if (!participant) {
                throw new Error('Not participating in this quest');
            }

            if (participant.status !== 'active') {
                throw new Error('Quest participation is not active');
            }

            // Update progress for objectives
            let questCompleted = true;
            const updatedProgress = [];

            for (const objective of quest.objectives) {
                const objectiveProgress = progressData.find(p => p.objectiveId === objective.id);
                if (objectiveProgress) {
                    const validatedProgress = await this.validateObjectiveProgress(
                        objective,
                        objectiveProgress,
                        playerId
                    );

                    // Update participant progress
                    const participantObjective = participant.progress.find(
                        p => p.objectiveId === objective.id
                    );

                    if (participantObjective) {
                        participantObjective.progress = Math.max(
                            participantObjective.progress,
                            validatedProgress.progress
                        );
                        participantObjective.completed = validatedProgress.completed;
                        participantObjective.data = validatedProgress.data;

                        updatedProgress.push(participantObjective);

                        if (!validatedProgress.completed) {
                            questCompleted = false;
                        }
                    }
                } else if (!participant.progress.find(p => p.objectiveId === objective.id).completed) {
                    questCompleted = false;
                }
            }

            // Update participant activity
            participant.lastActivity = new Date().toISOString();
            participant.contributions.timeSpent += progressData.timeSpent || 0;

            // Save to database
            await this.db.collection('guild_quests').updateOne(
                {
                    id: questId,
                    'participants.playerId': playerId
                },
                {
                    $set: {
                        'participants.$.progress': participant.progress,
                        'participants.$.lastActivity': new Date().toISOString(),
                        'participants.$.contributions': participant.contributions,
                        'metadata.lastModified': new Date().toISOString()
                    }
                }
            );

            // Update cache
            this.activeQuests.set(questId, quest);

            // Check if quest is completed
            if (questCompleted) {
                return await this.completeQuest(questId, playerId);
            }

            // Share progress if enabled
            if (quest.settings.shareProgress) {
                await this.shareProgressWithTeam(quest, participant, updatedProgress);
            }

            return {
                success: true,
                progress: updatedProgress,
                questCompleted: false
            };

        } catch (error) {
            console.error('Error updating quest progress:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Complete quest and distribute rewards
     */
    async completeQuest(questId, playerId) {
        try {
            const quest = await this.getQuest(questId);
            if (!quest) {
                throw new Error('Quest not found');
            }

            const participant = quest.participants.find(p => p.playerId === playerId);
            if (!participant) {
                throw new Error('Not participating in this quest');
            }

            if (participant.status === 'completed') {
                throw new Error('Quest already completed');
            }

            // Calculate completion time
            const completionTime = new Date().getTime() - new Date(participant.acceptedAt).getTime();

            // Update participant status
            participant.status = 'completed';
            participant.completedAt = new Date().toISOString();
            participant.completionTime = completionTime;

            // Calculate rewards
            const earnedRewards = await this.calculateQuestRewards(quest, participant);

            // Distribute rewards
            await this.distributeQuestRewards(playerId, earnedRewards);

            // Create completion record
            const completion = {
                playerId: playerId,
                playerName: participant.playerName,
                completedAt: new Date().toISOString(),
                completionTime: completionTime,
                rewards: earnedRewards,
                contributions: participant.contributions,
                rating: null // To be filled by quest creator or participants
            };

            // Update quest statistics
            await this.db.collection('guild_quests').updateOne(
                { id: questId },
                {
                    $set: {
                        'participants.$[participant].status': 'completed',
                        'participants.$[participant].completedAt': new Date().toISOString(),
                        'participants.$[participant].completionTime': completionTime,
                        'metadata.lastModified': new Date().toISOString()
                    },
                    $push: { completions: completion },
                    $inc: { 'statistics.successfulCompletions': 1 },
                    $min: { 'statistics.averageCompletionTime': completionTime },
                    $max: { 'statistics.averageCompletionTime': completionTime },
                    arrayFilters: [{ 'participant.playerId': playerId }]
                }
            );

            // Update cache
            this.activeQuests.set(questId, quest);

            // Notify participant
            await this.notifyQuestCompleted(playerId, quest, earnedRewards);

            // Notify quest creator
            await this.notifyQuestCreatorCompletion(quest, participant);

            // Check if quest should repeat
            if (quest.repeatable) {
                await this.resetParticipantForRepeat(questId, playerId);
            }

            return {
                success: true,
                rewards: earnedRewards,
                completion: completion
            };

        } catch (error) {
            console.error('Error completing quest:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Create dynamic quest based on guild activity
     */
    async createDynamicQuest(guildId, triggerData) {
        try {
            const {
                trigger, // 'guild_level_up', 'member_count_milestone', 'achievement_unlocked', 'weekly_activity'
                parameters = {}
            } = triggerData;

            // Generate quest based on trigger
            const questTemplate = await this.generateQuestFromTrigger(trigger, parameters, guildId);
            if (!questTemplate) {
                return { success: false, error: 'No quest template for trigger' };
            }

            // Create system-generated quest
            const quest = {
                id: this.generateQuestId(),
                guildId: guildId,
                ...questTemplate,
                creatorId: 'system',
                creatorName: 'System',
                systemGenerated: true,
                status: 'active',
                metadata: {
                    created: new Date().toISOString(),
                    trigger: trigger,
                    triggerParameters: parameters
                }
            };

            // Save quest
            await this.db.collection('guild_quests').insertOne(quest);
            this.activeQuests.set(quest.id, quest);

            // Notify guild
            await this.notifyDynamicQuestCreated(guildId, quest);

            return {
                success: true,
                quest: quest
            };

        } catch (error) {
            console.error('Error creating dynamic quest:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Create guild achievement quest
     */
    async createAchievementQuest(guildId, achievementId, creatorId) {
        try {
            // Get achievement data
            const achievement = await this.getAchievement(achievementId);
            if (!achievement) {
                throw new Error('Achievement not found');
            }

            // Validate permissions
            const member = await this.getGuildMember(guildId, creatorId);
            if (!this.hasPermission(member, 'create_achievement_quests')) {
                throw new Error('No permission to create achievement quests');
            }

            // Create achievement-based quest
            const quest = {
                id: this.generateQuestId(),
                guildId: guildId,
                title: `Achievement: ${achievement.name}`,
                description: `Complete the "${achievement.name}" achievement as a guild.`,
                type: 'achievement',
                difficulty: achievement.difficulty || 'medium',
                creatorId: creatorId,
                creatorName: member.playerName,
                objectives: [
                    {
                        id: 1,
                        type: 'achievement',
                        description: achievement.description,
                        target: achievement.id,
                        required: 1,
                        progress: 0,
                        completed: false
                    }
                ],
                requirements: {
                    minLevel: achievement.minLevel || 1,
                    minRank: achievement.minRank || 'Member'
                },
                rewards: {
                    experience: achievement.rewardExperience || 1000,
                    gold: achievement.rewardGold || 500,
                    guildContribution: achievement.rewardContribution || 100,
                    achievements: [achievement.id],
                    reputation: achievement.rewardReputation || 50
                },
                status: 'active',
                participants: [],
                isAchievementQuest: true,
                achievementId: achievementId,
                metadata: {
                    created: new Date().toISOString(),
                    type: 'achievement_quest'
                }
            };

            // Save quest
            await this.db.collection('guild_quests').insertOne(quest);
            this.activeQuests.set(quest.id, quest);

            return {
                success: true,
                quest: quest
            };

        } catch (error) {
            console.error('Error creating achievement quest:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Get available guild quests
     */
    async getGuildQuests(guildId, options = {}) {
        try {
            const {
                status = 'active',
                type = null,
                difficulty = null,
                limit = 20,
                offset = 0,
                forPlayer = null
            } = options;

            let query = { guildId: guildId };

            if (status !== 'all') {
                query.status = status;
            }

            if (type) {
                query.type = type;
            }

            if (difficulty) {
                query.difficulty = difficulty;
            }

            // Filter by player requirements if specified
            if (forPlayer) {
                const player = await this.getPlayerData(forPlayer);
                if (player) {
                    query.$and = [
                        query,
                        {
                            $or: [
                                { 'requirements.minLevel': { $lte: player.level } },
                                { 'requirements.minLevel': { $exists: false } }
                            ]
                        }
                    ];
                }
            }

            const quests = await this.db.collection('guild_quests')
                .find(query)
                .sort({ 'metadata.created': -1 })
                .skip(offset)
                .limit(limit)
                .toArray();

            // Add participant counts and availability info
            for (const quest of quests) {
                quest.participantCount = quest.participants.length;
                quest.isAvailable = !quest.maxParticipants ||
                                   quest.participants.length < quest.maxParticipants;
                quest.isFull = quest.maxParticipants &&
                              quest.participants.length >= quest.maxParticipants;
            }

            return {
                success: true,
                quests: quests
            };

        } catch (error) {
            console.error('Error fetching guild quests:', error);
            return {
                success: false,
                error: error.message,
                quests: []
            };
        }
    }

    /**
     * Get player's active quests
     */
    async getPlayerQuests(playerId) {
        try {
            // Get all quests where player is participant
            const quests = await this.db.collection('guild_quests')
                .find({
                    'participants.playerId': playerId,
                    'participants.status': 'active'
                })
                .toArray();

            // Add player's progress for each quest
            for (const quest of quests) {
                const participant = quest.participants.find(p => p.playerId === playerId);
                quest.playerProgress = participant.progress;
                quest.playerContributions = participant.contributions;
                quest.acceptedAt = participant.acceptedAt;
            }

            return {
                success: true,
                quests: quests
            };

        } catch (error) {
            console.error('Error fetching player quests:', error);
            return {
                success: false,
                error: error.message,
                quests: []
            };
        }
    }

    /**
     * Abandon quest
     */
    async abandonQuest(questId, playerId, reason = '') {
        try {
            const quest = await this.getQuest(questId);
            if (!quest) {
                throw new Error('Quest not found');
            }

            const participant = quest.participants.find(p => p.playerId === playerId);
            if (!participant) {
                throw new Error('Not participating in this quest');
            }

            if (participant.status === 'completed') {
                throw new Error('Cannot abandon completed quest');
            }

            // Update participant status
            await this.db.collection('guild_quests').updateOne(
                {
                    id: questId,
                    'participants.playerId': playerId
                },
                {
                    $set: {
                        'participants.$.status': 'abandoned',
                        'participants.$.abandonedAt': new Date().toISOString(),
                        'participants.$.abandonReason': reason,
                        'metadata.lastModified': new Date().toISOString()
                    }
                }
            );

            // Update cache
            participant.status = 'abandoned';
            participant.abandonedAt = new Date().toISOString();
            participant.abandonReason = reason;
            this.activeQuests.set(questId, quest);

            // Clear progress tracking
            this.questProgress.delete(`${questId}_${playerId}`);

            // Notify quest creator
            await this.notifyQuestAbandoned(quest, participant, reason);

            return {
                success: true
            };

        } catch (error) {
            console.error('Error abandoning quest:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Rate quest completion
     */
    async rateQuestCompletion(questId, playerId, rating, feedback = '') {
        try {
            const quest = await this.getQuest(questId);
            if (!quest) {
                throw new Error('Quest not found');
            }

            const participant = quest.participants.find(p => p.playerId === playerId);
            if (!participant || participant.status !== 'completed') {
                throw new Error('Can only rate completed quests');
            }

            // Update completion rating
            await this.db.collection('guild_quests').updateOne(
                {
                    id: questId,
                    'completions.playerId': playerId
                },
                {
                    $set: {
                        'completions.$.rating': rating,
                        'completions.$.feedback': feedback,
                        'completions.$.ratedAt': new Date().toISOString(),
                        'metadata.lastModified': new Date().toISOString()
                    }
                }
            );

            return {
                success: true
            };

        } catch (error) {
            console.error('Error rating quest:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Helper methods
     */
    generateQuestId() {
        return 'quest_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    validateQuestData(questData) {
        const errors = [];

        if (!questData.title || questData.title.trim().length === 0) {
            errors.push('Quest title is required');
        }

        if (!questData.description || questData.description.trim().length === 0) {
            errors.push('Quest description is required');
        }

        if (!questData.type || !this.isValidQuestType(questData.type)) {
            errors.push('Invalid quest type');
        }

        if (!questData.difficulty || !this.isValidDifficulty(questData.difficulty)) {
            errors.push('Invalid quest difficulty');
        }

        if (!questData.objectives || questData.objectives.length === 0) {
            errors.push('At least one objective is required');
        }

        // Validate objectives
        if (questData.objectives) {
            questData.objectives.forEach((obj, index) => {
                if (!obj.type || !obj.description) {
                    errors.push(`Objective ${index + 1} is incomplete`);
                }
                if (obj.required <= 0) {
                    errors.push(`Objective ${index + 1} requires a positive target`);
                }
            });
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    isValidQuestType(type) {
        const validTypes = [
            'collect', 'defeat', 'explore', 'craft', 'social',
            'raid', 'pvp', 'achievement', 'mystery', 'timed'
        ];

        return validTypes.includes(type);
    }

    isValidDifficulty(difficulty) {
        const validDifficulties = ['easy', 'medium', 'hard', 'epic', 'legendary'];
        return validDifficulties.includes(difficulty);
    }

    async validateObjectiveProgress(objective, progressData, playerId) {
        let validatedProgress = { ...progressData };

        switch (objective.type) {
            case 'collect':
                validatedProgress = await this.validateCollectionProgress(
                    objective, progressData, playerId
                );
                break;
            case 'defeat':
                validatedProgress = await this.validateDefeatProgress(
                    objective, progressData, playerId
                );
                break;
            case 'explore':
                validatedProgress = await this.validateExplorationProgress(
                    objective, progressData, playerId
                );
                break;
            case 'craft':
                validatedProgress = await this.validateCraftingProgress(
                    objective, progressData, playerId
                );
                break;
            case 'social':
                validatedProgress = await this.validateSocialProgress(
                    objective, progressData, playerId
                );
                break;
            default:
                // Generic validation
                validatedProgress.progress = Math.min(progressData.progress, objective.required);
                validatedProgress.completed = validatedProgress.progress >= objective.required;
                break;
        }

        return validatedProgress;
    }

    async validateCollectionProgress(objective, progressData, playerId) {
        // Validate that player actually collected the items
        const playerInventory = await this.getPlayerInventory(playerId);
        const collectedItems = progressData.collectedItems || [];

        let validCount = 0;
        for (const item of collectedItems) {
            const inventoryItem = playerInventory.find(i => i.itemId === item.itemId);
            if (inventoryItem && inventoryItem.quantity >= item.quantity) {
                validCount += item.quantity;
            }
        }

        const progress = Math.min(validCount, objective.required);
        return {
            progress: progress,
            completed: progress >= objective.required,
            data: { validatedItems: collectedItems }
        };
    }

    async validateDefeatProgress(objective, progressData, playerId) {
        // Validate defeat progress through combat logs or achievements
        const defeatedEnemies = progressData.defeatedEnemies || [];
        let validDefeats = 0;

        // This would integrate with combat system to validate defeats
        for (const enemy of defeatedEnemies) {
            if (await this.validateEnemyDefeat(playerId, enemy)) {
                validDefeats++;
            }
        }

        const progress = Math.min(validDefeats, objective.required);
        return {
            progress: progress,
            completed: progress >= objective.required,
            data: { validatedDefeats: validDefeats }
        };
    }

    async validateExplorationProgress(objective, progressData, playerId) {
        // Validate exploration through location tracking
        const exploredLocations = progressData.exploredLocations || [];
        let validExplorations = 0;

        for (const location of exploredLocations) {
            if (await this.validateLocationExploration(playerId, location)) {
                validExplorations++;
            }
        }

        const progress = Math.min(validExplorations, objective.required);
        return {
            progress: progress,
            completed: progress >= objective.required,
            data: { validatedLocations: exploredLocations }
        };
    }

    async validateCraftingProgress(objective, progressData, playerId) {
        // Validate crafting through crafting logs
        const craftedItems = progressData.craftedItems || [];
        let validCrafts = 0;

        for (const item of craftedItems) {
            if (await this.validateItemCrafting(playerId, item)) {
                validCrafts++;
            }
        }

        const progress = Math.min(validCrafts, objective.required);
        return {
            progress: progress,
            completed: progress >= objective.required,
            data: { validatedCrafts: validCrafts }
        };
    }

    async validateSocialProgress(objective, progressData, playerId) {
        // Validate social interactions
        const interactions = progressData.interactions || [];
        let validInteractions = 0;

        for (const interaction of interactions) {
            if (await this.validateSocialInteraction(playerId, interaction)) {
                validInteractions++;
            }
        }

        const progress = Math.min(validInteractions, objective.required);
        return {
            progress: progress,
            completed: progress >= objective.required,
            data: { validatedInteractions: validInteractions }
        };
    }

    async calculateQuestRewards(quest, participant) {
        const baseRewards = { ...quest.rewards };
        const calculatedRewards = {};

        // Calculate time bonus
        const timeBonusMultiplier = this.calculateTimeBonus(quest, participant);

        // Calculate contribution bonus
        const contributionBonus = this.calculateContributionBonus(participant);

        // Apply multipliers
        if (baseRewards.experience) {
            calculatedRewards.experience = Math.floor(
                baseRewards.experience * timeBonusMultiplier * contributionBonus
            );
        }

        if (baseRewards.gold) {
            calculatedRewards.gold = Math.floor(
                baseRewards.gold * timeBonusMultiplier * contributionBonus
            );
        }

        if (baseRewards.guildContribution) {
            calculatedRewards.guildContribution = Math.floor(
                baseRewards.guildContribution * contributionBonus
            );
        }

        // Items and achievements are not multiplied
        if (baseRewards.items) {
            calculatedRewards.items = baseRewards.items;
        }

        if (baseRewards.achievements) {
            calculatedRewards.achievements = baseRewards.achievements;
        }

        if (baseRewards.reputation) {
            calculatedRewards.reputation = Math.floor(
                baseRewards.reputation * contributionBonus
            );
        }

        return calculatedRewards;
    }

    calculateTimeBonus(quest, participant) {
        if (!quest.timeLimit) return 1.0;

        const timeUsed = participant.completionTime || 0;
        const timeLimit = quest.timeLimit * 60 * 1000; // Convert minutes to milliseconds

        if (timeUsed <= timeLimit * 0.5) return 1.5; // Completed in half time
        if (timeUsed <= timeLimit * 0.75) return 1.25; // Completed in 75% time
        if (timeUsed <= timeLimit) return 1.1; // Completed within time limit
        return 1.0; // Over time limit
    }

    calculateContributionBonus(participant) {
        const contributions = participant.contributions;

        // Base bonus based on activity level
        let bonus = 1.0;

        if (contributions.timeSpent > 60 * 60 * 1000) bonus += 0.2; // Spent more than 1 hour
        if (contributions.enemiesDefeated > 50) bonus += 0.15;
        if (contributions.resourcesUsed > 1000) bonus += 0.1;

        return Math.min(bonus, 1.5); // Cap at 50% bonus
    }

    async distributeQuestRewards(playerId, rewards) {
        await this.rewards.grantRewards(playerId, rewards);
    }

    async generateQuestFromTrigger(trigger, parameters, guildId) {
        const templates = {
            'guild_level_up': {
                title: `Celebrate Guild Level ${parameters.newLevel}!`,
                description: `Complete activities to celebrate the guild reaching level ${parameters.newLevel}!`,
                type: 'social',
                difficulty: 'medium',
                objectives: [
                    {
                        type: 'social',
                        description: 'Participate in guild celebration',
                        required: 1
                    },
                    {
                        type: 'defeat',
                        description: 'Defeat monsters together',
                        required: 10
                    }
                ],
                rewards: {
                    experience: 500 * parameters.newLevel,
                    gold: 200 * parameters.newLevel,
                    guildContribution: 50 * parameters.newLevel
                }
            },
            'member_count_milestone': {
                title: `Welcome Our ${parameters.memberCount}th Member!`,
                description: `Help the guild grow and integrate new members.`,
                type: 'social',
                difficulty: 'easy',
                objectives: [
                    {
                        type: 'social',
                        description: 'Welcome new guild members',
                        required: 3
                    }
                ],
                rewards: {
                    experience: 300,
                    guildContribution: 25
                }
            },
            'weekly_activity': {
                title: 'Weekly Guild Challenge',
                description: 'Complete various guild activities this week.',
                type: 'mixed',
                difficulty: 'medium',
                objectives: [
                    {
                        type: 'social',
                        description: 'Participate in guild chat',
                        required: 5
                    },
                    {
                        type: 'defeat',
                        description: 'Complete guild activities',
                        required: 3
                    }
                ],
                rewards: {
                    experience: 1000,
                    gold: 500,
                    guildContribution: 100
                }
            }
        };

        return templates[trigger] || null;
    }

    async resetParticipantForRepeat(questId, playerId) {
        const quest = await this.getQuest(questId);
        if (!quest || !quest.repeatable) return;

        // Reset participant for repeat attempt
        const resetProgress = quest.objectives.map(obj => ({
            objectiveId: obj.id,
            progress: 0,
            completed: false,
            data: {}
        }));

        await this.db.collection('guild_quests').updateOne(
            {
                id: questId,
                'participants.playerId': playerId
            },
            {
                $set: {
                    'participants.$.status': 'active',
                    'participants.$.progress': resetProgress,
                    'participants.$.acceptedAt': new Date().toISOString(),
                    'participants.$.contributions': {
                        timeSpent: 0,
                        resourcesUsed: 0,
                        enemiesDefeated: 0
                    }
                }
            }
        );
    }

    async shareProgressWithTeam(quest, participant, updatedProgress) {
        // Share progress with team members if enabled
        if (!quest.settings.shareProgress) return;

        const teamMembers = quest.participants.filter(p =>
            p.teamId === participant.teamId && p.playerId !== participant.playerId
        );

        for (const teamMember of teamMembers) {
            await this.notifications.sendPlayerNotification(teamMember.playerId, {
                type: 'quest_progress_shared',
                questId: quest.id,
                playerId: participant.playerId,
                progress: updatedProgress
            });
        }
    }

    // Database access methods
    async getQuest(questId) {
        if (this.activeQuests.has(questId)) {
            return this.activeQuests.get(questId);
        }

        try {
            const quest = await this.db.collection('guild_quests').findOne({ id: questId });
            if (quest) {
                this.activeQuests.set(questId, quest);
            }
            return quest;
        } catch (error) {
            console.error('Error fetching quest:', error);
            return null;
        }
    }

    async getGuildMember(guildId, playerId) {
        return await this.db.collection('guild_members').findOne({
            guildId: guildId,
            playerId: playerId
        });
    }

    async getPlayerData(playerId) {
        return await this.db.collection('players').findOne({ id: playerId });
    }

    async getPlayerInventory(playerId) {
        return await this.db.collection('player_inventory').find({ playerId: playerId }).toArray();
    }

    async getAchievement(achievementId) {
        return await this.db.collection('achievements').findOne({ id: achievementId });
    }

    hasPermission(member, permission) {
        const permissions = {
            'Leader': ['create_quests', 'create_achievement_quests'],
            'Officer': ['create_quests'],
            'Veteran': [],
            'Member': [],
            'Initiate': []
        };

        return member && permissions[member.rank]?.includes(permission) || false;
    }

    async checkQuestRequirements(quest, member) {
        // Check minimum level
        if (member.level < quest.requirements.minLevel) {
            return {
                met: false,
                reason: `Minimum level ${quest.requirements.minLevel} required`
            };
        }

        // Check rank requirement
        const rankLevels = {
            'Initiate': 1,
            'Member': 2,
            'Veteran': 3,
            'Officer': 4,
            'Leader': 5
        };

        const memberRankLevel = rankLevels[member.rank] || 0;
        const requiredRankLevel = rankLevels[quest.requirements.minRank] || 0;

        if (memberRankLevel < requiredRankLevel) {
            return {
                met: false,
                reason: `Minimum rank ${quest.requirements.minRank} required`
            };
        }

        // Check prerequisites
        if (quest.requirements.prerequisites && quest.requirements.prerequisites.length > 0) {
            const completedQuests = await this.db.collection('guild_quests').countDocuments({
                guildId: quest.guildId,
                'completions.playerId': member.playerId,
                'completions.playerId': { $in: quest.requirements.prerequisites }
            });

            if (completedQuests < quest.requirements.prerequisites.length) {
                return {
                    met: false,
                    reason: 'Prerequisite quests not completed'
                };
            }
        }

        return { met: true };
    }

    // Validation helper methods (would integrate with other systems)
    async validateEnemyDefeat(playerId, enemy) {
        // Integrate with combat system
        return true; // Placeholder
    }

    async validateLocationExploration(playerId, location) {
        // Integrate with exploration system
        return true; // Placeholder
    }

    async validateItemCrafting(playerId, item) {
        // Integrate with crafting system
        return true; // Placeholder
    }

    async validateSocialInteraction(playerId, interaction) {
        // Integrate with social system
        return true; // Placeholder
    }

    // Notification methods
    async notifyQuestCreated(guildId, quest) {
        await this.notifications.sendGuildNotification(guildId, {
            type: 'quest_created',
            quest: quest
        });
    }

    async notifyQuestAccepted(playerId, quest) {
        await this.notifications.sendPlayerNotification(playerId, {
            type: 'quest_accepted',
            quest: quest
        });
    }

    async notifyQuestCompleted(playerId, quest, rewards) {
        await this.notifications.sendPlayerNotification(playerId, {
            type: 'quest_completed',
            quest: quest,
            rewards: rewards
        });
    }

    async notifyQuestCreatorCompletion(quest, participant) {
        await this.notifications.sendPlayerNotification(quest.creatorId, {
            type: 'quest_participant_completed',
            quest: quest,
            participant: participant
        });
    }

    async notifyQuestAbandoned(quest, participant, reason) {
        await this.notifications.sendPlayerNotification(quest.creatorId, {
            type: 'quest_abandoned',
            quest: quest,
            participant: participant,
            reason: reason
        });
    }

    async notifyDynamicQuestCreated(guildId, quest) {
        await this.notifications.sendGuildNotification(guildId, {
            type: 'dynamic_quest_created',
            quest: quest
        });
    }
}

module.exports = GuildQuests;