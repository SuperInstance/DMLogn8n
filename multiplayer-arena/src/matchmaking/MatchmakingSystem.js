/**
 * Advanced Matchmaking System for DMlogn8n Multiplayer Arena
 * Features ELO ratings, skill-based matching, and role balancing
 */

class MatchmakingSystem {
    constructor() {
        this.playerQueue = new Map();
        this.waitingPlayers = [];
        this.activeMatches = new Map();
        this.playerStats = new Map();
        this.roleBalance = new RoleBalance();
        this.eloCalculator = new ELOCalculator();
        this.geoMatcher = new GeoMatcher();

        // Queue configurations
        this.queueConfig = {
            '1v1_duel': {
                minPlayers: 2,
                maxWaitTime: 300, // 5 minutes
                skillRange: 150, // ELO range
                regionPriority: true
            },
            'team_competition': {
                minPlayers: 4,
                teamSizes: ['2v2', '3v3', '5v5'],
                maxWaitTime: 600, // 10 minutes
                skillRange: 200,
                roleBalance: true
            },
            'battle_royale': {
                minPlayers: 10,
                maxPlayers: 50,
                maxWaitTime: 180, // 3 minutes
                skillRange: 300,
                fastFill: true
            }
        };

        this.matchmakingInterval = null;
        this.startMatchmaking();
    }

    /**
     * Add player to matchmaking queue
     */
    addToQueue(playerId, preferences = {}) {
        const player = this.getPlayerData(playerId);
        if (!player) {
            throw new Error(`Player ${playerId} not found`);
        }

        // Check if player is already in queue
        if (this.playerQueue.has(playerId)) {
            throw new Error(`Player ${playerId} is already in queue`);
        }

        const queueEntry = {
            playerId: playerId,
            preferences: {
                arenaType: preferences.arenaType || '1v1_duel',
                teamSize: preferences.teamSize || null,
                region: preferences.region || player.region,
                maxWaitTime: preferences.maxWaitTime || this.queueConfig[preferences.arenaType]?.maxWaitTime || 300,
                skillRange: preferences.skillRange || this.queueConfig[preferences.arenaType]?.skillRange || 150
            },
            queueTime: Date.now(),
            expandedSkillRange: this.queueConfig[preferences.arenaType]?.skillRange || 150,
            priority: this.calculatePlayerPriority(player)
        };

        this.playerQueue.set(playerId, queueEntry);
        this.waitingPlayers.push(queueEntry);

        console.log(`Player ${playerId} added to ${preferences.arenaType} queue`);
        return queueEntry;
    }

    /**
     * Remove player from matchmaking queue
     */
    removeFromQueue(playerId) {
        const queueEntry = this.playerQueue.get(playerId);
        if (!queueEntry) return false;

        this.playerQueue.delete(playerId);
        const index = this.waitingPlayers.findIndex(p => p.playerId === playerId);
        if (index !== -1) {
            this.waitingPlayers.splice(index, 1);
        }

        console.log(`Player ${playerId} removed from queue`);
        return true;
    }

    /**
     * Start matchmaking process
     */
    startMatchmaking() {
        this.matchmakingInterval = setInterval(() => {
            this.processMatchmaking();
        }, 1000); // Process every second
    }

    /**
     * Main matchmaking process
     */
    processMatchmaking() {
        const now = Date.now();

        // Group players by arena type
        const queueGroups = this.groupPlayersByArenaType();

        Object.entries(queueGroups).forEach(([arenaType, players]) => {
            this.processQueueForArenaType(arenaType, players, now);
        });
    }

    /**
     * Group waiting players by arena type
     */
    groupPlayersByArenaType() {
        const groups = {};

        this.waitingPlayers.forEach(player => {
            const arenaType = player.preferences.arenaType;
            if (!groups[arenaType]) {
                groups[arenaType] = [];
            }
            groups[arenaType].push(player);
        });

        return groups;
    }

    /**
     * Process queue for specific arena type
     */
    processQueueForArenaType(arenaType, players, now) {
        const config = this.queueConfig[arenaType];
        if (!config) return;

        // Expand skill range over time
        this.expandSkillRanges(players, now);

        // Sort by priority and queue time
        players.sort((a, b) => {
            if (a.priority !== b.priority) {
                return b.priority - a.priority;
            }
            return a.queueTime - b.queueTime;
        });

        switch (arenaType) {
            case '1v1_duel':
                this.processDuelQueue(players, config);
                break;
            case 'team_competition':
                this.processTeamQueue(players, config);
                break;
            case 'battle_royale':
                this.processBattleRoyaleQueue(players, config);
                break;
        }
    }

    /**
     * Process 1v1 duel matchmaking
     */
    processDuelQueue(players, config) {
        if (players.length < config.minPlayers) return;

        // Find compatible pairs
        for (let i = 0; i < players.length - 1; i++) {
            const player1 = players[i];
            const player1Data = this.getPlayerData(player1.playerId);

            for (let j = i + 1; j < players.length; j++) {
                const player2 = players[j];
                const player2Data = this.getPlayerData(player2.playerId);

                if (this.areCompatibleForDuel(player1Data, player2Data, player1, player2)) {
                    this.createMatch('1v1_duel', [player1.playerId, player2.playerId]);
                    this.removeFromQueue(player1.playerId);
                    this.removeFromQueue(player2.playerId);
                    return; // Process one match per cycle
                }
            }
        }
    }

    /**
     * Process team matchmaking
     */
    processTeamQueue(players, config) {
        if (players.length < config.minPlayers) return;

        // Try to create balanced teams
        const teamCandidates = this.findTeamCandidates(players, config);

        if (teamCandidates.length >= config.minPlayers) {
            this.createMatch('team_competition', teamCandidates);
            teamCandidates.forEach(candidate => {
                this.removeFromQueue(candidate.playerId);
            });
        }
    }

    /**
     * Process battle royale matchmaking
     */
    processBattleRoyaleQueue(players, config) {
        if (players.length < config.minPlayers) return;

        // Take available players up to max
        const matchPlayers = players.slice(0, Math.min(config.maxPlayers, players.length));

        if (matchPlayers.length >= config.minPlayers) {
            this.createMatch('battle_royale', matchPlayers.map(p => p.playerId));
            matchPlayers.forEach(player => {
                this.removeFromQueue(player.playerId);
            });
        }
    }

    /**
     * Check if two players are compatible for dueling
     */
    areCompatibleForDuel(player1, player2, queueEntry1, queueEntry2) {
        // Check skill range compatibility
        const skillDiff = Math.abs(player1.elo - player2.elo);
        const maxSkillDiff = Math.max(queueEntry1.expandedSkillRange, queueEntry2.expandedSkillRange);

        if (skillDiff > maxSkillDiff) return false;

        // Check level compatibility
        const levelDiff = Math.abs(player1.level - player2.level);
        if (levelDiff > 10) return false;

        // Check class balance
        if (!this.isBalancedClassMatchup(player1.character.class, player2.character.class)) {
            return false;
        }

        // Check region compatibility
        if (queueEntry1.preferences.region && queueEntry2.preferences.region) {
            if (queueEntry1.preferences.region !== queueEntry2.preferences.region) {
                const regionCompatibility = this.geoMatcher.getRegionCompatibility(
                    queueEntry1.preferences.region,
                    queueEntry2.preferences.region
                );
                if (regionCompatibility < 0.5) return false;
            }
        }

        return true;
    }

    /**
     * Find balanced team candidates
     */
    findTeamCandidates(players, config) {
        const candidates = [];

        // Try each team size configuration
        for (const teamSize of config.teamSizes) {
            const teamConfig = this.getTeamConfig(teamSize);
            if (players.length < teamConfig.totalPlayers) continue;

            // Find balanced team composition
            const balancedTeams = this.roleBalance.findBalancedTeams(
                players,
                teamConfig
            );

            if (balancedTeams && balancedTeams.length >= teamConfig.totalPlayers) {
                return balancedTeams.slice(0, teamConfig.totalPlayers);
            }
        }

        return candidates;
    }

    /**
     * Check if class matchup is balanced
     */
    isBalancedClassMatchup(class1, class2) {
        // Class balance matrix (same as in DuelingArena)
        const balanceMatrix = {
            'fighter': { 'wizard': 0.8, 'rogue': 1.1, 'cleric': 1.0, 'ranger': 0.9 },
            'wizard': { 'fighter': 1.2, 'rogue': 0.9, 'cleric': 1.0, 'ranger': 1.1 },
            'cleric': { 'fighter': 1.0, 'rogue': 1.1, 'wizard': 1.0, 'ranger': 0.9 },
            'rogue': { 'fighter': 0.9, 'wizard': 1.1, 'cleric': 0.9, 'ranger': 1.0 },
            'ranger': { 'fighter': 1.1, 'wizard': 0.9, 'cleric': 1.1, 'rogue': 1.0 }
        };

        const balanceFactor = balanceMatrix[class1.toLowerCase()]?.[class2.toLowerCase()] || 1.0;
        return Math.abs(balanceFactor - 1.0) <= 0.3; // Allow 30% imbalance for faster matchmaking
    }

    /**
     * Expand skill ranges based on wait time
     */
    expandSkillRanges(players, now) {
        players.forEach(player => {
            const waitTime = (now - player.queueTime) / 1000; // seconds
            const baseRange = this.queueConfig[player.preferences.arenaType]?.skillRange || 150;

            // Expand range by 10% every 30 seconds, up to 3x base range
            const expansionFactor = Math.min(3, 1 + Math.floor(waitTime / 30) * 0.1);
            player.expandedSkillRange = Math.floor(baseRange * expansionFactor);
        });
    }

    /**
     * Calculate player priority for matchmaking
     */
    calculatePlayerPriority(player) {
        let priority = 0;

        // Premium members get higher priority
        if ( player.premium) priority += 100;

        // Good connection quality
        if (player.connectionQuality >= 0.9) priority += 50;

        // Recent activity bonus
        const lastActive = Date.now() - player.lastActive;
        if (lastActive < 3600000) priority += 25; // Active in last hour

        return priority;
    }

    /**
     * Create a new match
     */
    createMatch(arenaType, playerIds) {
        const matchId = this.generateMatchId();
        const players = playerIds.map(id => this.getPlayerData(id));

        const match = {
            id: matchId,
            arenaType: arenaType,
            players: players,
            createdAt: Date.now(),
            status: 'forming',
            predictedQuality: this.predictMatchQuality(players, arenaType)
        };

        this.activeMatches.set(matchId, match);

        console.log(`Created ${arenaType} match ${matchId} with ${players.length} players`);
        return match;
    }

    /**
     * Predict match quality based on player compatibility
     */
    predictMatchQuality(players, arenaType) {
        if (players.length < 2) return 0;

        let totalSkillDiff = 0;
        let comparisons = 0;

        for (let i = 0; i < players.length; i++) {
            for (let j = i + 1; j < players.length; j++) {
                totalSkillDiff += Math.abs(players[i].elo - players[j].elo);
                comparisons++;
            }
        }

        const avgSkillDiff = totalSkillDiff / comparisons;
        const skillScore = Math.max(0, 100 - avgSkillDiff / 5);

        // Add bonus factors
        let bonus = 0;

        // Region compatibility
        if (this.checkRegionCompatibility(players)) bonus += 10;

        // Level balance
        const levelVariance = this.calculateLevelVariance(players);
        bonus += Math.max(0, 10 - levelVariance);

        return Math.min(100, skillScore + bonus);
    }

    /**
     * Check if all players are from compatible regions
     */
    checkRegionCompatibility(players) {
        const regions = players.map(p => p.region).filter(r => r);
        if (regions.length === 0) return true;

        const primaryRegion = regions[0];
        return regions.every(region =>
            this.geoMatcher.getRegionCompatibility(primaryRegion, region) >= 0.7
        );
    }

    /**
     * Calculate level variance among players
     */
    calculateLevelVariance(players) {
        const levels = players.map(p => p.level);
        const avg = levels.reduce((sum, level) => sum + level, 0) / levels.length;
        const variance = levels.reduce((sum, level) => sum + Math.pow(level - avg, 2), 0) / levels.length;
        return Math.sqrt(variance);
    }

    /**
     * Get team configuration
     */
    getTeamConfig(teamSize) {
        const configs = {
            '2v2': { teams: 2, playersPerTeam: 2, totalPlayers: 4 },
            '3v3': { teams: 2, playersPerTeam: 3, totalPlayers: 6 },
            '5v5': { teams: 2, playersPerTeam: 5, totalPlayers: 10 }
        };
        return configs[teamSize];
    }

    /**
     * Get player data
     */
    getPlayerData(playerId) {
        // In a real implementation, this would fetch from database
        // For now, return mock data
        return this.playerStats.get(playerId) || {
            id: playerId,
            name: `Player_${playerId}`,
            elo: 1500,
            level: 10,
            region: 'us-east',
            character: {
                class: 'fighter'
            },
            premium: false,
            connectionQuality: 0.9,
            lastActive: Date.now()
        };
    }

    /**
     * Update player statistics after match
     */
    updatePlayerStats(matchResults) {
        matchResults.players.forEach(playerResult => {
            const playerData = this.getPlayerData(playerResult.playerId);

            // Update ELO rating
            const newElo = this.eloCalculator.calculateNewElo(
                playerData.elo,
                matchResults.averageElo,
                playerResult.placement === 1 ? 1 : 0,
                playerResult.kda
            );

            playerData.elo = newElo;
            playerData.matchesPlayed = (playerData.matchesPlayed || 0) + 1;
            playerData.wins = (playerData.wins || 0) + (playerResult.placement === 1 ? 1 : 0);

            this.playerStats.set(playerResult.playerId, playerData);
        });
    }

    /**
     * Generate unique match ID
     */
    generateMatchId() {
        return `match_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Get queue status
     */
    getQueueStatus() {
        const status = {};

        Object.keys(this.queueConfig).forEach(arenaType => {
            const playersInQueue = this.waitingPlayers.filter(p =>
                p.preferences.arenaType === arenaType
            );

            status[arenaType] = {
                playersWaiting: playersInQueue.length,
                averageWaitTime: this.calculateAverageWaitTime(playersInQueue),
                skillRange: this.getCurrentSkillRange(playersInQueue)
            };
        });

        return status;
    }

    /**
     * Calculate average wait time for players in queue
     */
    calculateAverageWaitTime(players) {
        if (players.length === 0) return 0;

        const now = Date.now();
        const totalWaitTime = players.reduce((sum, player) =>
            sum + (now - player.queueTime), 0
        );

        return Math.floor(totalWaitTime / players.length / 1000); // seconds
    }

    /**
     * Get current skill range for queue
     */
    getCurrentSkillRange(players) {
        if (players.length === 0) return { min: 0, max: 0 };

        const elos = players.map(p => this.getPlayerData(p.playerId).elo);
        return {
            min: Math.min(...elos),
            max: Math.max(...elos),
            average: elos.reduce((sum, elo) => sum + elo, 0) / elos.length
        };
    }

    /**
     * Stop matchmaking system
     */
    stopMatchmaking() {
        if (this.matchmakingInterval) {
            clearInterval(this.matchmakingInterval);
            this.matchmakingInterval = null;
        }
    }
}

/**
 * ELO Calculator for skill ratings
 */
class ELOCalculator {
    constructor() {
        this.kFactor = 32; // Standard K-factor for ELO calculations
    }

    calculateNewElo(currentElo, opponentElo, result, kda = null) {
        const expectedScore = this.calculateExpectedScore(currentElo, opponentElo);
        const actualScore = result;

        // Adjust K-factor based on KDA if provided
        let kFactor = this.kFactor;
        if (kda) {
            // Higher KDA gives slightly higher K-factor for faster adjustment
            kFactor = Math.min(48, Math.max(16, this.kFactor * (1 + kda * 0.1)));
        }

        const newElo = currentElo + kFactor * (actualScore - expectedScore);
        return Math.round(newElo);
    }

    calculateExpectedScore(elo1, elo2) {
        return 1 / (1 + Math.pow(10, (elo2 - elo1) / 400));
    }
}

/**
 * Role Balance for team matchmaking
 */
class RoleBalance {
    constructor() {
        this.roles = {
            tank: ['fighter', 'paladin', 'barbarian'],
            healer: ['cleric', 'druid', 'bard'],
            damage: ['rogue', 'ranger', 'wizard', 'sorcerer'],
            support: ['bard', 'warlock', 'artificer']
        };
    }

    findBalancedTeams(players, teamConfig) {
        // Simple implementation - in production this would be more sophisticated
        const sortedPlayers = players.sort((a, b) =>
            this.getPlayerData(b.playerId).elo - this.getPlayerData(a.playerId).elo
        );

        return sortedPlayers.slice(0, teamConfig.totalPlayers);
    }

    getPlayerRole(playerClass) {
        for (const [role, classes] of Object.entries(this.roles)) {
            if (classes.includes(playerClass.toLowerCase())) {
                return role;
            }
        }
        return 'damage';
    }

    getPlayerData(playerId) {
        // Mock implementation
        return { elo: 1500, class: 'fighter' };
    }
}

/**
 * Geographic matcher for region-based matchmaking
 */
class GeoMatcher {
    constructor() {
        this.regionLatency = {
            'us-east': { 'us-east': 20, 'us-west': 60, 'eu-west': 100, 'asia-east': 180 },
            'us-west': { 'us-east': 60, 'us-west': 20, 'eu-west': 120, 'asia-east': 150 },
            'eu-west': { 'us-east': 100, 'us-west': 120, 'eu-west': 20, 'asia-east': 140 },
            'asia-east': { 'us-east': 180, 'us-west': 150, 'eu-west': 140, 'asia-east': 20 }
        };
    }

    getRegionCompatibility(region1, region2) {
        if (!region1 || !region2) return 0.5;
        if (region1 === region2) return 1.0;

        const latency = this.regionLatency[region1]?.[region2] || 200;
        return Math.max(0, 1 - (latency / 200));
    }
}

module.exports = {
    MatchmakingSystem,
    ELOCalculator,
    RoleBalance,
    GeoMatcher
};