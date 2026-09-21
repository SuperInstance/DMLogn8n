/**
 * Guild Events System
 * Manages guild activities, events, tournaments, and social gatherings
 */

class GuildEvents {
    constructor(databaseClient, rewardService, notificationService) {
        this.db = databaseClient;
        this.rewards = rewardService;
        this.notifications = notificationService;
        this.activeEvents = new Map();
        this.eventScheduler = new Map();
    }

    /**
     * Create new guild event
     */
    async createEvent(guildId, creatorId, eventData) {
        try {
            const {
                title,
                description,
                type,
                startTime,
                duration,
                maxParticipants,
                requirements = {},
                rewards = {},
                settings = {}
            } = eventData;

            // Validate permissions
            const member = await this.getGuildMember(guildId, creatorId);
            if (!this.hasPermission(member, 'create_events')) {
                throw new Error('No permission to create events');
            }

            // Validate event data
            const validation = this.validateEventData(eventData);
            if (!validation.valid) {
                throw new Error(validation.errors.join(', '));
            }

            // Create event
            const event = {
                id: this.generateEventId(),
                guildId: guildId,
                title: title,
                description: description,
                type: type,
                creatorId: creatorId,
                creatorName: member.playerName,
                startTime: new Date(startTime).toISOString(),
                endTime: new Date(new Date(startTime).getTime() + duration * 60 * 1000).toISOString(),
                duration: duration,
                maxParticipants: maxParticipants || null,
                currentParticipants: 0,
                requirements: {
                    minLevel: requirements.minLevel || 1,
                    minRank: requirements.minRank || 'Initiate',
                    classRequirements: requirements.classRequirements || [],
                    gearScore: requirements.gearScore || 0,
                    ...requirements
                },
                rewards: {
                    experience: rewards.experience || 0,
                    gold: rewards.gold || 0,
                    items: rewards.items || [],
                    guildContribution: rewards.guildContribution || 0,
                    achievement: rewards.achievement || null,
                    ...rewards
                },
                settings: {
                    autoStart: settings.autoStart || false,
                    allowLateJoin: settings.allowLateJoin || false,
                    requiresRegistration: settings.requiresRegistration || true,
                    voiceChannel: settings.voiceChannel || false,
                    ...settings
                },
                status: 'scheduled',
                participants: [],
                waitlist: [],
                results: null,
                metadata: {
                    created: new Date().toISOString(),
                    lastModified: new Date().toISOString()
                }
            };

            // Save to database
            await this.db.collection('guild_events').insertOne(event);

            // Schedule event start
            await this.scheduleEventStart(event);

            // Notify guild members
            await this.notifyEventCreated(guildId, event);

            // Cache active event
            this.activeEvents.set(event.id, event);

            return {
                success: true,
                event: event
            };

        } catch (error) {
            console.error('Error creating event:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Register for event
     */
    async registerForEvent(eventId, playerId, registrationData = {}) {
        try {
            // Get event
            const event = await this.getEvent(eventId);
            if (!event) {
                throw new Error('Event not found');
            }

            // Check if event allows registration
            if (!event.settings.requiresRegistration) {
                throw new Error('This event does not require registration');
            }

            // Check registration window
            if (new Date() > new Date(event.startTime)) {
                throw new Error('Registration period has ended');
            }

            // Get guild member
            const member = await this.getGuildMember(event.guildId, playerId);
            if (!member) {
                throw new Error('Member not found');
            }

            // Check requirements
            const requirementsCheck = await this.checkEventRequirements(event, member, registrationData);
            if (!requirementsCheck.met) {
                throw new Error(requirementsCheck.reason);
            }

            // Check if already registered
            if (event.participants.some(p => p.playerId === playerId)) {
                throw new Error('Already registered for this event');
            }

            // Check capacity
            if (event.maxParticipants && event.participants.length >= event.maxParticipants) {
                // Add to waitlist
                const waitlistEntry = {
                    playerId: playerId,
                    playerName: member.playerName,
                    registeredAt: new Date().toISOString(),
                    notes: registrationData.notes || ''
                };

                await this.db.collection('guild_events').updateOne(
                    { id: eventId },
                    {
                        $push: { waitlist: waitlistEntry },
                        $set: { 'metadata.lastModified': new Date().toISOString() }
                    }
                );

                // Update cache
                event.waitlist.push(waitlistEntry);
                this.activeEvents.set(eventId, event);

                return {
                    success: true,
                    status: 'waitlisted',
                    position: event.waitlist.length
                };
            }

            // Register participant
            const participant = {
                playerId: playerId,
                playerName: member.playerName,
                rank: member.rank,
                registeredAt: new Date().toISOString(),
                status: 'registered',
                notes: registrationData.notes || '',
                team: registrationData.team || null,
                role: registrationData.role || null
            };

            await this.db.collection('guild_events').updateOne(
                { id: eventId },
                {
                    $push: { participants: participant },
                    $inc: { currentParticipants: 1 },
                    $set: { 'metadata.lastModified': new Date().toISOString() }
                }
            );

            // Update cache
            event.participants.push(participant);
            event.currentParticipants++;
            this.activeEvents.set(eventId, event);

            // Notify event creator
            await this.notifyEventRegistration(event, participant);

            return {
                success: true,
                status: 'registered',
                event: event
            };

        } catch (error) {
            console.error('Error registering for event:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Start event
     */
    async startEvent(eventId, startedBy) {
        try {
            const event = await this.getEvent(eventId);
            if (!event) {
                throw new Error('Event not found');
            }

            // Check permissions
            const member = await this.getGuildMember(event.guildId, startedBy);
            if (!this.canStartEvent(member, event)) {
                throw new Error('No permission to start this event');
            }

            // Check if event can start
            if (event.status !== 'scheduled') {
                throw new Error('Event has already started or ended');
            }

            // Initialize event based on type
            const eventInstance = await this.initializeEventInstance(event);

            // Update event status
            await this.db.collection('guild_events').updateOne(
                { id: eventId },
                {
                    $set: {
                        status: 'active',
                        startTime: new Date().toISOString(),
                        instance: eventInstance,
                        'metadata.lastModified': new Date().toISOString()
                    }
                }
            );

            // Update cache
            event.status = 'active';
            event.instance = eventInstance;
            this.activeEvents.set(eventId, event);

            // Notify participants
            await this.notifyEventStarted(event);

            // Start event monitoring
            await this.startEventMonitoring(event);

            return {
                success: true,
                event: event,
                instance: eventInstance
            };

        } catch (error) {
            console.error('Error starting event:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Record event participation/action
     */
    async recordEventAction(eventId, playerId, action, data = {}) {
        try {
            const event = await this.getEvent(eventId);
            if (!event) {
                throw new Error('Event not found');
            }

            if (event.status !== 'active') {
                throw new Error('Event is not active');
            }

            // Validate participant
            const participant = event.participants.find(p => p.playerId === playerId);
            if (!participant) {
                throw new Error('Not registered for this event');
            }

            // Record action based on event type
            const actionResult = await this.processEventAction(event, participant, action, data);

            // Update participant progress
            await this.updateParticipantProgress(event, participant, actionResult);

            // Log action
            const actionLog = {
                eventId: eventId,
                playerId: playerId,
                action: action,
                data: data,
                result: actionResult,
                timestamp: new Date().toISOString()
            };

            await this.db.collection('guild_event_actions').insertOne(actionLog);

            // Check if event should end
            if (actionResult.eventComplete) {
                await this.completeEvent(eventId, actionResult.results);
            }

            return {
                success: true,
                result: actionResult
            };

        } catch (error) {
            console.error('Error recording event action:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Complete event and distribute rewards
     */
    async completeEvent(eventId, results = {}) {
        try {
            const event = await this.getEvent(eventId);
            if (!event) {
                throw new Error('Event not found');
            }

            // Calculate final results if not provided
            const finalResults = results || await this.calculateEventResults(event);

            // Distribute rewards
            const rewardDistributions = await this.distributeEventRewards(event, finalResults);

            // Update event with results
            await this.db.collection('guild_events').updateOne(
                { id: eventId },
                {
                    $set: {
                        status: 'completed',
                        endTime: new Date().toISOString(),
                        results: finalResults,
                        rewardDistributions: rewardDistributions,
                        'metadata.lastModified': new Date().toISOString()
                    }
                }
            );

            // Update cache
            event.status = 'completed';
            event.results = finalResults;
            event.rewardDistributions = rewardDistributions;
            this.activeEvents.set(eventId, event);

            // Notify participants
            await this.notifyEventCompleted(event, finalResults, rewardDistributions);

            // Clean up monitoring
            await this.stopEventMonitoring(eventId);

            return {
                success: true,
                results: finalResults,
                rewards: rewardDistributions
            };

        } catch (error) {
            console.error('Error completing event:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Create tournament
     */
    async createTournament(guildId, creatorId, tournamentData) {
        try {
            const {
                title,
                description,
                type,
                format,
                startTime,
                registrationDeadline,
                maxTeams,
                teamSize,
                entryFee,
                prizePool,
                rules = []
            } = tournamentData;

            // Validate permissions
            const member = await this.getGuildMember(guildId, creatorId);
            if (!this.hasPermission(member, 'create_tournaments')) {
                throw new Error('No permission to create tournaments');
            }

            // Create tournament
            const tournament = {
                id: this.generateTournamentId(),
                guildId: guildId,
                title: title,
                description: description,
                type: type, // 'pvp', 'pve', 'mixed'
                format: format, // 'single_elimination', 'double_elimination', 'round_robin', 'swiss'
                creatorId: creatorId,
                creatorName: member.playerName,
                startTime: new Date(startTime).toISOString(),
                registrationDeadline: new Date(registrationDeadline).toISOString(),
                maxTeams: maxTeams || 16,
                teamSize: teamSize || 4,
                entryFee: entryFee || 0,
                prizePool: prizePool || 0,
                rules: rules,
                status: 'registration',
                teams: [],
                brackets: null,
                currentRound: 0,
                matches: [],
                results: null,
                metadata: {
                    created: new Date().toISOString(),
                    lastModified: new Date().toISOString()
                }
            };

            // Save to database
            await this.db.collection('guild_tournaments').insertOne(tournament);

            // Notify guild
            await this.notifyTournamentCreated(guildId, tournament);

            return {
                success: true,
                tournament: tournament
            };

        } catch (error) {
            console.error('Error creating tournament:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Register team for tournament
     */
    async registerTournamentTeam(tournamentId, teamData) {
        try {
            const tournament = await this.getTournament(tournamentId);
            if (!tournament) {
                throw new Error('Tournament not found');
            }

            if (tournament.status !== 'registration') {
                throw new Error('Tournament registration is closed');
            }

            if (new Date() > new Date(tournament.registrationDeadline)) {
                throw new Error('Registration deadline has passed');
            }

            // Validate team
            const validation = this.validateTournamentTeam(tournament, teamData);
            if (!validation.valid) {
                throw new Error(validation.errors.join(', '));
            }

            // Create team
            const team = {
                id: this.generateTeamId(),
                name: teamData.name,
                captainId: teamData.captainId,
                members: teamData.members,
                registeredAt: new Date().toISOString(),
                status: 'registered',
                stats: {
                    wins: 0,
                    losses: 0,
                    draws: 0,
                    points: 0
                },
                paidEntryFee: false
            };

            // Process entry fee
            if (tournament.entryFee > 0) {
                const paymentResult = await this.processTournamentEntryFee(
                    tournament.guildId,
                    team.captainId,
                    tournament.entryFee
                );

                if (!paymentResult.success) {
                    throw new Error('Failed to process entry fee: ' + paymentResult.error);
                }

                team.paidEntryFee = true;
                tournament.prizePool += tournament.entryFee;
            }

            // Add team to tournament
            await this.db.collection('guild_tournaments').updateOne(
                { id: tournamentId },
                {
                    $push: { teams: team },
                    $set: {
                        'metadata.lastModified': new Date().toISOString(),
                        prizePool: tournament.prizePool
                    }
                }
            );

            // Notify tournament
            await this.notifyTournamentTeamRegistered(tournament, team);

            return {
                success: true,
                team: team
            };

        } catch (error) {
            console.error('Error registering tournament team:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Get guild events
     */
    async getGuildEvents(guildId, options = {}) {
        try {
            const {
                status = null,
                type = null,
                limit = 20,
                offset = 0,
                startDate = null,
                endDate = null
            } = options;

            let query = { guildId: guildId };

            if (status) {
                query.status = status;
            }

            if (type) {
                query.type = type;
            }

            if (startDate || endDate) {
                query.startTime = {};
                if (startDate) {
                    query.startTime.$gte = new Date(startDate).toISOString();
                }
                if (endDate) {
                    query.startTime.$lte = new Date(endDate).toISOString();
                }
            }

            const events = await this.db.collection('guild_events')
                .find(query)
                .sort({ startTime: -1 })
                .skip(offset)
                .limit(limit)
                .toArray();

            return {
                success: true,
                events: events
            };

        } catch (error) {
            console.error('Error fetching guild events:', error);
            return {
                success: false,
                error: error.message,
                events: []
            };
        }
    }

    /**
     * Get event details
     */
    async getEvent(eventId) {
        // Check cache first
        if (this.activeEvents.has(eventId)) {
            return this.activeEvents.get(eventId);
        }

        try {
            const event = await this.db.collection('guild_events').findOne({ id: eventId });
            if (event && (event.status === 'scheduled' || event.status === 'active')) {
                this.activeEvents.set(eventId, event);
            }
            return event;
        } catch (error) {
            console.error('Error fetching event:', error);
            return null;
        }
    }

    /**
     * Helper methods
     */
    generateEventId() {
        return 'evt_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    generateTournamentId() {
        return 'tourn_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    generateTeamId() {
        return 'team_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    validateEventData(eventData) {
        const errors = [];

        if (!eventData.title || eventData.title.trim().length === 0) {
            errors.push('Event title is required');
        }

        if (!eventData.type || !this.isValidEventType(eventData.type)) {
            errors.push('Invalid event type');
        }

        if (!eventData.startTime || new Date(eventData.startTime) <= new Date()) {
            errors.push('Event start time must be in the future');
        }

        if (!eventData.duration || eventData.duration <= 0) {
            errors.push('Event duration must be positive');
        }

        if (eventData.maxParticipants && eventData.maxParticipants <= 0) {
            errors.push('Max participants must be positive');
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    isValidEventType(type) {
        const validTypes = [
            'dungeon_run',
            'raid',
            'pvp_tournament',
            'social_gathering',
            'guild_meeting',
            'training_session',
            'contest',
            'scavenger_hunt',
            'boss_battle'
        ];

        return validTypes.includes(type);
    }

    validateTournamentTeam(tournament, teamData) {
        const errors = [];

        if (!teamData.name || teamData.name.trim().length === 0) {
            errors.push('Team name is required');
        }

        if (!teamData.captainId) {
            errors.push('Team captain is required');
        }

        if (!teamData.members || teamData.members.length === 0) {
            errors.push('Team must have at least one member');
        }

        if (teamData.members.length > tournament.teamSize) {
            errors.push(`Team size cannot exceed ${tournament.teamSize}`);
        }

        // Check if all members are guild members
        // This would require database validation

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    hasPermission(member, permission) {
        return member && member.permissions && member.permissions.includes(permission);
    }

    canStartEvent(member, event) {
        // Event creator can always start
        if (member.playerId === event.creatorId) {
            return true;
        }

        // Officers and leaders can start any event
        return ['Leader', 'Officer'].includes(member.rank);
    }

    async checkEventRequirements(event, member, registrationData) {
        // Check minimum level
        if (member.level < event.requirements.minLevel) {
            return {
                met: false,
                reason: `Minimum level ${event.requirements.minLevel} required`
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
        const requiredRankLevel = rankLevels[event.requirements.minRank] || 0;

        if (memberRankLevel < requiredRankLevel) {
            return {
                met: false,
                reason: `Minimum rank ${event.requirements.minRank} required`
            };
        }

        // Check class requirements
        if (event.requirements.classRequirements.length > 0) {
            if (!event.requirements.classRequirements.includes(member.class)) {
                return {
                    met: false,
                    reason: `Class ${member.class} not allowed for this event`
                };
            }
        }

        // Check gear score
        if (member.gearScore < event.requirements.gearScore) {
            return {
                met: false,
                reason: `Minimum gear score ${event.requirements.gearScore} required`
            };
        }

        return { met: true };
    }

    async scheduleEventStart(event) {
        const startTime = new Date(event.startTime).getTime();
        const now = Date.now();
        const delay = startTime - now;

        if (delay > 0) {
            const timeoutId = setTimeout(async () => {
                await this.startEvent(event.id, 'system');
            }, delay);

            this.eventScheduler.set(event.id, timeoutId);
        }
    }

    async initializeEventInstance(event) {
        const eventTypes = {
            'dungeon_run': () => this.initializeDungeonRun(event),
            'pvp_tournament': () => this.initializePVPTournament(event),
            'social_gathering': () => this.initializeSocialGathering(event),
            'contest': () => this.initializeContest(event),
            'scavenger_hunt': () => this.initializeScavengerHunt(event),
            'boss_battle': () => this.initializeBossBattle(event)
        };

        const initializer = eventTypes[event.type];
        return initializer ? await initializer() : {};
    }

    async initializeDungeonRun(event) {
        return {
            type: 'dungeon',
            dungeonId: 'dungeon_' + Date.now(),
            difficulty: 'normal',
            objectives: [
                { id: 1, description: 'Defeat the final boss', completed: false },
                { id: 2, description: 'Collect 3 treasure chests', completed: false },
                { id: 3, description: 'Complete within time limit', completed: false }
            ],
            startTime: new Date().toISOString(),
            timeLimit: 60 * 60 * 1000 // 1 hour
        };
    }

    async initializePVPTournament(event) {
        const participants = event.participants;
        const brackets = this.createTournamentBrackets(participants);

        return {
            type: 'pvp',
            format: 'single_elimination',
            brackets: brackets,
            currentRound: 1,
            matches: []
        };
    }

    async initializeSocialGathering(event) {
        return {
            type: 'social',
            activities: [
                { id: 1, name: 'Guild Photo', participants: [] },
                { id: 2, name: 'Storytelling', participants: [] },
                { id: 3, name: 'Feast', participants: [] }
            ],
            location: 'guild_hall'
        };
    }

    createTournamentBrackets(participants) {
        const shuffled = [...participants].sort(() => Math.random() - 0.5);
        const brackets = [];

        for (let i = 0; i < shuffled.length; i += 2) {
            if (i + 1 < shuffled.length) {
                brackets.push({
                    round: 1,
                    match: Math.floor(i / 2) + 1,
                    player1: shuffled[i],
                    player2: shuffled[i + 1],
                    winner: null,
                    completed: false
                });
            }
        }

        return brackets;
    }

    async processEventAction(event, participant, action, data) {
        // Process action based on event type and instance
        switch (event.type) {
            case 'dungeon_run':
                return await this.processDungeonAction(event, participant, action, data);
            case 'pvp_tournament':
                return await this.processPVPAction(event, participant, action, data);
            case 'social_gathering':
                return await this.processSocialAction(event, participant, action, data);
            case 'contest':
                return await this.processContestAction(event, participant, action, data);
            default:
                return { success: true, message: 'Action recorded' };
        }
    }

    async processDungeonAction(event, participant, action, data) {
        const instance = event.instance;

        switch (action) {
            case 'defeat_enemy':
                return {
                    success: true,
                    experience: 100,
                    progress: { enemiesDefeated: 1 }
                };
            case 'collect_treasure':
                return {
                    success: true,
                    items: data.items || [],
                    progress: { treasuresCollected: 1 }
                };
            case 'complete_objective':
                const objective = instance.objectives.find(o => o.id === data.objectiveId);
                if (objective) {
                    objective.completed = true;
                }
                return {
                    success: true,
                    progress: { objectivesCompleted: 1 }
                };
            default:
                return { success: true };
        }
    }

    async processPVPAction(event, participant, action, data) {
        // Handle PvP tournament actions
        return {
            success: true,
            result: data.result || 'victory'
        };
    }

    async processSocialAction(event, participant, action, data) {
        // Handle social event actions
        return {
            success: true,
            socialPoints: 10,
            interaction: data.interaction
        };
    }

    async processContestAction(event, participant, action, data) {
        // Handle contest submissions
        return {
            success: true,
            score: data.score || 0,
            submission: data.submission
        };
    }

    async updateParticipantProgress(event, participant, actionResult) {
        // Update participant's progress in the event
        const participantIndex = event.participants.findIndex(p => p.playerId === participant.playerId);
        if (participantIndex !== -1) {
            const updatedParticipant = {
                ...event.participants[participantIndex],
                progress: {
                    ...event.participants[participantIndex].progress,
                    ...actionResult.progress
                },
                score: (event.participants[participantIndex].score || 0) + (actionResult.score || 0),
                lastAction: new Date().toISOString()
            };

            event.participants[participantIndex] = updatedParticipant;

            await this.db.collection('guild_events').updateOne(
                { id: event.id, 'participants.playerId': participant.playerId },
                {
                    $set: {
                        'participants.$': updatedParticipant,
                        'metadata.lastModified': new Date().toISOString()
                    }
                }
            );
        }
    }

    async calculateEventResults(event) {
        // Calculate final results based on event type
        switch (event.type) {
            case 'dungeon_run':
                return await this.calculateDungeonResults(event);
            case 'pvp_tournament':
                return await this.calculatePVPResults(event);
            case 'contest':
                return await this.calculateContestResults(event);
            default:
                return {
                    success: true,
                    participants: event.participants,
                    completed: true
                };
        }
    }

    async calculateDungeonResults(event) {
        // Sort participants by score/objectives completed
        const rankedParticipants = event.participants
            .map(p => ({
                ...p,
                totalScore: p.score || 0,
                objectivesCompleted: p.progress?.objectivesCompleted || 0
            }))
            .sort((a, b) => {
                if (b.objectivesCompleted !== a.objectivesCompleted) {
                    return b.objectivesCompleted - a.objectivesCompleted;
                }
                return b.totalScore - a.totalScore;
            });

        return {
            type: 'dungeon',
            rankings: rankedParticipants,
            winners: rankedParticipants.slice(0, 3),
            statistics: {
                totalParticipants: event.participants.length,
                averageScore: rankedParticipants.reduce((sum, p) => sum + p.totalScore, 0) / rankedParticipants.length,
                completionRate: rankedParticipants.filter(p => p.objectivesCompleted > 0).length / rankedParticipants.length
            }
        };
    }

    async calculatePVPResults(event) {
        // Calculate PvP tournament results
        const instance = event.instance;
        const finalStandings = instance.brackets
            .filter(match => match.completed)
            .reduce((standings, match) => {
                // Process tournament standings
                return standings;
            }, []);

        return {
            type: 'pvp',
            winner: finalStandings[0] || null,
            standings: finalStandings,
            statistics: {
                totalMatches: instance.brackets.length,
                totalParticipants: event.participants.length
            }
        };
    }

    async calculateContestResults(event) {
        // Sort participants by contest score
        const rankedParticipants = event.participants
            .sort((a, b) => (b.score || 0) - (a.score || 0));

        return {
            type: 'contest',
            rankings: rankedParticipants,
            winners: rankedParticipants.slice(0, 3),
            submissions: event.participants.map(p => ({
                playerId: p.playerId,
                playerName: p.playerName,
                score: p.score || 0,
                submission: p.submission
            }))
        };
    }

    async distributeEventRewards(event, results) {
        const distributions = [];

        for (const participant of event.participants) {
            const rewards = await this.calculateParticipantRewards(event, participant, results);

            if (Object.keys(rewards).length > 0) {
                // Distribute rewards to participant
                await this.rewards.grantRewards(participant.playerId, rewards);

                distributions.push({
                    playerId: participant.playerId,
                    playerName: participant.playerName,
                    rewards: rewards
                });
            }
        }

        return distributions;
    }

    async calculateParticipantRewards(event, participant, results) {
        const rewards = {};
        const baseRewards = event.rewards;

        // Determine reward multiplier based on performance
        let multiplier = 1.0;
        if (results.rankings) {
            const rank = results.rankings.findIndex(p => p.playerId === participant.playerId);
            if (rank === 0) multiplier = 2.0; // 1st place
            else if (rank === 1) multiplier = 1.5; // 2nd place
            else if (rank === 2) multiplier = 1.25; // 3rd place
        }

        // Apply rewards
        if (baseRewards.experience > 0) {
            rewards.experience = Math.floor(baseRewards.experience * multiplier);
        }

        if (baseRewards.gold > 0) {
            rewards.gold = Math.floor(baseRewards.gold * multiplier);
        }

        if (baseRewards.items && baseRewards.items.length > 0) {
            rewards.items = baseRewards.items;
        }

        if (baseRewards.guildContribution > 0) {
            rewards.guildContribution = Math.floor(baseRewards.guildContribution * multiplier);
        }

        // Add achievement for top performers
        if (multiplier >= 1.5 && baseRewards.achievement) {
            rewards.achievement = baseRewards.achievement;
        }

        return rewards;
    }

    async getGuildMember(guildId, playerId) {
        return await this.db.collection('guild_members').findOne({
            guildId: guildId,
            playerId: playerId
        });
    }

    async getTournament(tournamentId) {
        return await this.db.collection('guild_tournaments').findOne({ id: tournamentId });
    }

    async processTournamentEntryFee(guildId, playerId, amount) {
        // Process entry fee from guild bank or player
        const guildBank = await this.db.collection('guild_banks').findOne({ guildId: guildId });

        if (guildBank && guildBank.gold >= amount) {
            await this.db.collection('guild_banks').updateOne(
                { guildId: guildId },
                { $inc: { gold: -amount } }
            );
            return { success: true };
        }

        // Try player's personal gold
        const player = await this.db.collection('players').findOne({ id: playerId });
        if (player && player.gold >= amount) {
            await this.db.collection('players').updateOne(
                { id: playerId },
                { $inc: { gold: -amount } }
            );
            return { success: true };
        }

        return { success: false, error: 'Insufficient funds' };
    }

    async startEventMonitoring(event) {
        // Start monitoring for event completion, timeouts, etc.
        console.log(`Started monitoring for event ${event.id}`);
    }

    async stopEventMonitoring(eventId) {
        // Stop event monitoring
        console.log(`Stopped monitoring for event ${eventId}`);
    }

    // Notification methods
    async notifyEventCreated(guildId, event) {
        await this.notifications.sendGuildNotification(guildId, {
            type: 'event_created',
            event: event
        });
    }

    async notifyEventRegistration(event, participant) {
        await this.notifications.sendPlayerNotification(event.creatorId, {
            type: 'event_registration',
            event: event,
            participant: participant
        });
    }

    async notifyEventStarted(event) {
        for (const participant of event.participants) {
            await this.notifications.sendPlayerNotification(participant.playerId, {
                type: 'event_started',
                event: event
            });
        }
    }

    async notifyEventCompleted(event, results, rewards) {
        for (const distribution of rewards) {
            await this.notifications.sendPlayerNotification(distribution.playerId, {
                type: 'event_completed',
                event: event,
                results: results,
                rewards: distribution.rewards
            });
        }
    }

    async notifyTournamentCreated(guildId, tournament) {
        await this.notifications.sendGuildNotification(guildId, {
            type: 'tournament_created',
            tournament: tournament
        });
    }

    async notifyTournamentTeamRegistered(tournament, team) {
        await this.notifications.sendGuildNotification(tournament.guildId, {
            type: 'tournament_team_registered',
            tournament: tournament,
            team: team
        });
    }
}

module.exports = GuildEvents;