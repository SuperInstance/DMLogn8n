/**
 * Queue Manager for handling multiple matchmaking queues
 * Supports different queue types, priorities, and queue jumping
 */

class QueueManager {
    constructor() {
        this.queues = new Map();
        this.playerQueues = new Map(); // Track which queues a player is in
        this.queueHistory = new Map(); // Track queue history for analytics
        this.priorityPasses = new Map(); // Premium queue passes

        this.initializeQueues();
    }

    /**
     * Initialize default queue types
     */
    initializeQueues() {
        // 1v1 Duel Queue
        this.queues.set('duel_ranked', new MatchmakingQueue({
            id: 'duel_ranked',
            name: 'Ranked Duel',
            type: '1v1_duel',
            minPlayers: 2,
            maxWaitTime: 300,
            skillRange: 150,
            restrictions: {
                minLevel: 10,
                maxLevel: null,
                requiredRank: 'Bronze',
                regionLocked: false
            },
            rewards: {
                eloMultiplier: 1.0,
                goldMultiplier: 1.0,
                xpMultiplier: 1.0
            }
        }));

        // Casual Duel Queue
        this.queues.set('duel_casual', new MatchmakingQueue({
            id: 'duel_casual',
            name: 'Casual Duel',
            type: '1v1_duel',
            minPlayers: 2,
            maxWaitTime: 180,
            skillRange: 300,
            restrictions: {
                minLevel: 1,
                maxLevel: null,
                requiredRank: null,
                regionLocked: false
            },
            rewards: {
                eloMultiplier: 0.5,
                goldMultiplier: 0.8,
                xpMultiplier: 0.7
            }
        }));

        // Team Arena - 3v3
        this.queues.set('team_3v3_ranked', new MatchmakingQueue({
            id: 'team_3v3_ranked',
            name: 'Ranked 3v3',
            type: 'team_competition',
            teamSize: '3v3',
            minPlayers: 6,
            maxWaitTime: 420,
            skillRange: 200,
            restrictions: {
                minLevel: 15,
                maxLevel: null,
                requiredRank: 'Silver',
                regionLocked: true,
                teamRequired: false
            },
            rewards: {
                eloMultiplier: 1.2,
                goldMultiplier: 1.5,
                xpMultiplier: 1.3
            }
        }));

        // Battle Royale Queue
        this.queues.set('battle_royale', new MatchmakingQueue({
            id: 'battle_royale',
            name: 'Battle Royale',
            type: 'battle_royale',
            minPlayers: 20,
            maxPlayers: 50,
            maxWaitTime: 240,
            skillRange: 400,
            restrictions: {
                minLevel: 5,
                maxLevel: null,
                requiredRank: null,
                regionLocked: false
            },
            rewards: {
                eloMultiplier: 0.8,
                goldMultiplier: 2.0,
                xpMultiplier: 1.5
            }
        }));

        // Tournament Queue
        this.queues.set('tournament', new MatchmakingQueue({
            id: 'tournament',
            name: 'Tournament',
            type: 'tournament',
            minPlayers: 8,
            maxWaitTime: 1800, // 30 minutes
            skillRange: 100,
            restrictions: {
                minLevel: 20,
                maxLevel: null,
                requiredRank: 'Gold',
                regionLocked: true,
                entryFee: 1000
            },
            rewards: {
                eloMultiplier: 2.0,
                goldMultiplier: 5.0,
                xpMultiplier: 3.0
            }
        }));
    }

    /**
     * Add player to specific queue
     */
    addToQueue(playerId, queueId, options = {}) {
        // Check if queue exists
        const queue = this.queues.get(queueId);
        if (!queue) {
            throw new Error(`Queue ${queueId} does not exist`);
        }

        // Check player restrictions
        if (!this.checkPlayerRestrictions(playerId, queue)) {
            throw new Error(`Player ${playerId} does not meet queue restrictions`);
        }

        // Check if player is already in a queue of the same type
        if (this.isPlayerInSimilarQueue(playerId, queue.type)) {
            throw new Error(`Player ${playerId} is already in a ${queue.type} queue`);
        }

        // Check if player has premium queue pass
        const hasPriorityPass = this.priorityPasses.has(playerId);

        // Create queue entry
        const queueEntry = queue.addPlayer(playerId, {
            ...options,
            hasPriorityPass
        });

        // Track player queues
        if (!this.playerQueues.has(playerId)) {
            this.playerQueues.set(playerId, new Set());
        }
        this.playerQueues.get(playerId).add(queueId);

        // Log queue entry
        this.logQueueEntry(playerId, queueId, options);

        return queueEntry;
    }

    /**
     * Remove player from queue
     */
    removeFromQueue(playerId, queueId = null) {
        if (queueId) {
            // Remove from specific queue
            const queue = this.queues.get(queueId);
            if (queue) {
                queue.removePlayer(playerId);
            }

            // Update player queue tracking
            const playerQueueSet = this.playerQueues.get(playerId);
            if (playerQueueSet) {
                playerQueueSet.delete(queueId);
                if (playerQueueSet.size === 0) {
                    this.playerQueues.delete(playerId);
                }
            }
        } else {
            // Remove from all queues
            const playerQueueSet = this.playerQueues.get(playerId);
            if (playerQueueSet) {
                playerQueueSet.forEach(qId => {
                    const queue = this.queues.get(qId);
                    if (queue) {
                        queue.removePlayer(playerId);
                    }
                });
                this.playerQueues.delete(playerId);
            }
        }
    }

    /**
     * Move player between queues (queue jumping)
     */
    moveBetweenQueues(playerId, fromQueueId, toQueueId) {
        // Check if player is in source queue
        const fromQueue = this.queues.get(fromQueueId);
        if (!fromQueue || !fromQueue.hasPlayer(playerId)) {
            throw new Error(`Player ${playerId} is not in queue ${fromQueueId}`);
        }

        // Get current position and wait time
        const currentEntry = fromQueue.getPlayerEntry(playerId);
        const waitTimeBonus = currentEntry.waitTime * 0.5; // 50% wait time bonus

        // Remove from current queue
        this.removeFromQueue(playerId, fromQueueId);

        // Add to new queue with priority bonus
        this.addToQueue(playerId, toQueueId, {
            waitTimeBonus,
            previousQueue: fromQueueId
        });
    }

    /**
     * Check if player meets queue restrictions
     */
    checkPlayerRestrictions(playerId, queue) {
        const player = this.getPlayerData(playerId);
        const restrictions = queue.restrictions;

        // Level restrictions
        if (restrictions.minLevel && player.level < restrictions.minLevel) {
            return false;
        }
        if (restrictions.maxLevel && player.level > restrictions.maxLevel) {
            return false;
        }

        // Rank restrictions
        if (restrictions.requiredRank && !this.meetsRankRequirement(player.rank, restrictions.requiredRank)) {
            return false;
        }

        // Entry fee
        if (restrictions.entryFee && player.gold < restrictions.entryFee) {
            return false;
        }

        return true;
    }

    /**
     * Check if player meets rank requirement
     */
    meetsRankRequirement(currentRank, requiredRank) {
        const rankHierarchy = [
            'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Mythic'
        ];

        const currentIndex = rankHierarchy.indexOf(currentRank);
        const requiredIndex = rankHierarchy.indexOf(requiredRank);

        return currentIndex >= requiredIndex;
    }

    /**
     * Check if player is in similar queue type
     */
    isPlayerInSimilarQueue(playerId, queueType) {
        const playerQueueSet = this.playerQueues.get(playerId);
        if (!playerQueueSet) return false;

        for (const queueId of playerQueueSet) {
            const queue = this.queues.get(queueId);
            if (queue && queue.type === queueType) {
                return true;
            }
        }

        return false;
    }

    /**
     * Get queue status for player
     */
    getPlayerQueueStatus(playerId) {
        const playerQueueSet = this.playerQueues.get(playerId);
        if (!playerQueueSet) {
            return {
                inQueue: false,
                queues: []
            };
        }

        const queues = [];
        for (const queueId of playerQueueSet) {
            const queue = this.queues.get(queueId);
            if (queue) {
                const entry = queue.getPlayerEntry(playerId);
                queues.push({
                    queueId: queueId,
                    queueName: queue.name,
                    position: queue.getPlayerPosition(playerId),
                    estimatedWaitTime: queue.getEstimatedWaitTime(playerId),
                    queueTime: Date.now() - entry.queueTime,
                    skillRange: entry.expandedSkillRange
                });
            }
        }

        return {
            inQueue: true,
            queues: queues
        };
    }

    /**
     * Get all queue statistics
     */
    getAllQueueStats() {
        const stats = {};

        this.queues.forEach((queue, queueId) => {
            stats[queueId] = {
                name: queue.name,
                type: queue.type,
                playersWaiting: queue.size(),
                averageWaitTime: queue.getAverageWaitTime(),
                matchesFound: queue.matchesFound,
                averageMatchQuality: queue.getAverageMatchQuality(),
                skillRange: queue.getCurrentSkillRange(),
                status: queue.isActive() ? 'active' : 'inactive'
            };
        });

        return stats;
    }

    /**
     * Process queue events and statistics
     */
    processQueueEvents() {
        this.queues.forEach(queue => {
            // Update queue statistics
            queue.updateStatistics();

            // Check for stale players (long wait times)
            queue.removeStalePlayers();

            // Update skill ranges
            queue.updateSkillRanges();
        });
    }

    /**
     * Award priority pass to player
     */
    awardPriorityPass(playerId, duration = 3600000) { // 1 hour default
        this.priorityPasses.set(playerId, {
            awardedAt: Date.now(),
            expiresAt: Date.now() + duration
        });
    }

    /**
     * Check if player has active priority pass
     */
    hasPriorityPass(playerId) {
        const pass = this.priorityPasses.get(playerId);
        if (!pass) return false;

        if (Date.now() > pass.expiresAt) {
            this.priorityPasses.delete(playerId);
            return false;
        }

        return true;
    }

    /**
     * Get player data (mock implementation)
     */
    getPlayerData(playerId) {
        // In production, this would fetch from database
        return {
            id: playerId,
            name: `Player_${playerId}`,
            level: 15,
            rank: 'Gold',
            gold: 5000,
            elo: 1650,
            region: 'us-east'
        };
    }

    /**
     * Log queue entry for analytics
     */
    logQueueEntry(playerId, queueId, options) {
        const timestamp = Date.now();
        if (!this.queueHistory.has(playerId)) {
            this.queueHistory.set(playerId, []);
        }

        this.queueHistory.get(playerId).push({
            timestamp,
            queueId,
            options
        });
    }

    /**
     * Get queue analytics
     */
    getQueueAnalytics() {
        const analytics = {
            totalPlayersQueued: 0,
            queueDistribution: {},
            averageWaitTimes: {},
            popularQueues: [],
            queueHealth: {}
        };

        this.queues.forEach((queue, queueId) => {
            const size = queue.size();
            analytics.totalPlayersQueued += size;
            analytics.queueDistribution[queueId] = size;
            analytics.averageWaitTimes[queueId] = queue.getAverageWaitTime();

            // Queue health assessment
            const health = this.assessQueueHealth(queue);
            analytics.queueHealth[queueId] = health;
        });

        // Find most popular queues
        analytics.popularQueues = Object.entries(analytics.queueDistribution)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 5)
            .map(([queueId, players]) => ({
                queueId,
                players,
                name: this.queues.get(queueId).name
            }));

        return analytics;
    }

    /**
     * Assess queue health
     */
    assessQueueHealth(queue) {
        const size = queue.size();
        const avgWaitTime = queue.getAverageWaitTime();
        const avgMatchQuality = queue.getAverageMatchQuality();
        const matchesFound = queue.matchesFound;

        let health = 'good';
        let issues = [];

        // Check player count
        if (size === 0) {
            health = 'empty';
            issues.push('No players in queue');
        } else if (size < queue.minPlayers) {
            health = 'low_population';
            issues.push('Not enough players for matches');
        }

        // Check wait times
        if (avgWaitTime > 300) { // 5 minutes
            health = 'slow';
            issues.push('Long wait times');
        }

        // Check match quality
        if (avgMatchQuality < 60) {
            health = 'poor_quality';
            issues.push('Low match quality');
        }

        return {
            status: health,
            issues,
            metrics: {
                playerCount: size,
                averageWaitTime: avgWaitTime,
                averageMatchQuality: avgMatchQuality,
                matchesFound
            }
        };
    }
}

/**
 * Individual Matchmaking Queue
 */
class MatchmakingQueue {
    constructor(config) {
        this.id = config.id;
        this.name = config.name;
        this.type = config.type;
        this.teamSize = config.teamSize || null;
        this.minPlayers = config.minPlayers;
        this.maxPlayers = config.maxPlayers || config.minPlayers;
        this.maxWaitTime = config.maxWaitTime;
        this.baseSkillRange = config.skillRange;
        this.restrictions = config.restrictions;
        this.rewards = config.rewards;

        this.players = [];
        this.matchesFound = 0;
        this.totalMatchQuality = 0;
        this.lastMatchTime = Date.now();
        this.isActive = true;
    }

    /**
     * Add player to queue
     */
    addPlayer(playerId, options = {}) {
        const player = {
            id: playerId,
            queueTime: Date.now(),
            expandedSkillRange: this.baseSkillRange,
            priority: options.hasPriorityPass ? 100 : 0,
            waitTimeBonus: options.waitTimeBonus || 0,
            previousQueue: options.previousQueue || null
        };

        // Insert player maintaining priority order
        const insertIndex = this.findInsertPosition(player);
        this.players.splice(insertIndex, 0, player);

        return player;
    }

    /**
     * Remove player from queue
     */
    removePlayer(playerId) {
        const index = this.players.findIndex(p => p.id === playerId);
        if (index !== -1) {
            this.players.splice(index, 1);
            return true;
        }
        return false;
    }

    /**
     * Check if player is in queue
     */
    hasPlayer(playerId) {
        return this.players.some(p => p.id === playerId);
    }

    /**
     * Get player entry
     */
    getPlayerEntry(playerId) {
        return this.players.find(p => p.id === playerId);
    }

    /**
     * Get player position in queue
     */
    getPlayerPosition(playerId) {
        const index = this.players.findIndex(p => p.id === playerId);
        return index !== -1 ? index + 1 : -1;
    }

    /**
     * Find insertion position based on priority
     */
    findInsertPosition(newPlayer) {
        for (let i = 0; i < this.players.length; i++) {
            if (this.players[i].priority < newPlayer.priority) {
                return i;
            }
        }
        return this.players.length;
    }

    /**
     * Get estimated wait time for player
     */
    getEstimatedWaitTime(playerId) {
        const position = this.getPlayerPosition(playerId);
        if (position === -1) return 0;

        // Simple estimation based on position and historical data
        const avgTimePerPosition = this.getAverageTimePerPosition();
        return Math.ceil(position * avgTimePerPosition);
    }

    /**
     * Get average time per position
     */
    getAverageTimePerPosition() {
        // This would be calculated from historical data
        return 30; // 30 seconds per position as default
    }

    /**
     * Get average wait time for all players
     */
    getAverageWaitTime() {
        if (this.players.length === 0) return 0;

        const now = Date.now();
        const totalWaitTime = this.players.reduce((sum, player) =>
            sum + (now - player.queueTime), 0
        );

        return Math.floor(totalWaitTime / this.players.length / 1000);
    }

    /**
     * Update skill ranges based on wait time
     */
    updateSkillRanges() {
        const now = Date.now();

        this.players.forEach(player => {
            const waitTime = (now - player.queueTime) / 1000;
            const expansionFactor = Math.min(3, 1 + Math.floor(waitTime / 30) * 0.1);
            player.expandedSkillRange = Math.floor(this.baseSkillRange * expansionFactor);
        });
    }

    /**
     * Remove stale players (waited too long)
     */
    removeStalePlayers() {
        const now = Date.now();
        const toRemove = [];

        this.players.forEach(player => {
            const waitTime = (now - player.queueTime) / 1000;
            if (waitTime > this.maxWaitTime) {
                toRemove.push(player.id);
            }
        });

        toRemove.forEach(playerId => this.removePlayer(playerId));
        return toRemove.length;
    }

    /**
     * Update queue statistics
     */
    updateStatistics() {
        // Update various statistics for analytics
        this.lastMatchTime = Date.now();
    }

    /**
     * Record match found
     */
    recordMatch(matchQuality) {
        this.matchesFound++;
        this.totalMatchQuality += matchQuality;
    }

    /**
     * Get average match quality
     */
    getAverageMatchQuality() {
        if (this.matchesFound === 0) return 0;
        return Math.floor(this.totalMatchQuality / this.matchesFound);
    }

    /**
     * Get current skill range
     */
    getCurrentSkillRange() {
        if (this.players.length === 0) {
            return { min: 0, max: 0, average: 0 };
        }

        // This would get actual ELO ratings from player data
        const elos = this.players.map(() => 1500 + Math.random() * 500 - 250);

        return {
            min: Math.min(...elos),
            max: Math.max(...elos),
            average: elos.reduce((sum, elo) => sum + elo, 0) / elos.length
        };
    }

    /**
     * Get queue size
     */
    size() {
        return this.players.length;
    }

    /**
     * Check if queue is active
     */
    isActive() {
        return this.isActive && this.size() > 0;
    }

    /**
     * Deactivate queue
     */
    deactivate() {
        this.isActive = false;
    }

    /**
     * Activate queue
     */
    activate() {
        this.isActive = true;
    }
}

module.exports = {
    QueueManager,
    MatchmakingQueue
};