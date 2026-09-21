/**
 * Arena Manager - Central coordination system for all arena operations
 * Provides high-level management interface for the multiplayer arena system
 */

class ArenaManager {
    constructor() {
        this.arenaSystem = null;
        this.matchmakingSystem = null;
        this.spectatorSystem = null;
        this.rankingSystem = null;
        this.gameModeManager = null;
        this.antiCheatSystem = null;
        this.netcodeOptimizer = null;

        this.activeArenas = new Map();
        this.activeMatches = new Map();
        this.connectedPlayers = new Map();
        this.systemMetrics = new Map();
        this.eventEmitter = new EventEmitter();

        this.isInitialized = false;
        this.startTime = null;

        this.initialize();
    }

    /**
     * Initialize all arena systems
     */
    async initialize() {
        try {
            console.log('Initializing DMlogn8n Multiplayer Arena System...');

            // Initialize core systems
            await this.initializeCoreSystems();
            await this.initializeSupportingSystems();
            await this.setupEventHandlers();
            await this.startSystemMonitoring();

            this.isInitialized = true;
            this.startTime = Date.now();

            console.log('Arena Manager initialization complete!');
            this.eventEmitter.emit('systemInitialized', { timestamp: this.startTime });

        } catch (error) {
            console.error('Failed to initialize Arena Manager:', error);
            throw error;
        }
    }

    /**
     * Initialize core arena systems
     */
    async initializeCoreSystems() {
        // Load modules
        const { ArenaSystem } = require('./ArenaSystem');
        const { MatchmakingSystem } = require('../matchmaking/MatchmakingSystem');
        const { SpectatorSystem } = require('../spectators/SpectatorSystem');
        const { RankingSystem } = require('../ranking/RankingSystem');
        const { GameModeManager } = require('../gamemodes/GameModeManager');

        // Initialize systems
        this.arenaSystem = new ArenaSystem();
        this.matchmakingSystem = new MatchmakingSystem();
        this.spectatorSystem = new SpectatorSystem();
        this.rankingSystem = new RankingSystem();
        this.gameModeManager = new GameModeManager();

        console.log('Core systems initialized');
    }

    /**
     * Initialize supporting systems
     */
    async initializeSupportingSystems() {
        const { AntiCheatSystem } = require('../anticheat/AntiCheatSystem');
        const { NetcodeOptimizer } = require('../netcode/NetcodeOptimizer');

        this.antiCheatSystem = new AntiCheatSystem();
        this.netcodeOptimizer = new NetcodeOptimizer();

        console.log('Supporting systems initialized');
    }

    /**
     * Create a new arena match
     */
    async createMatch(request) {
        if (!this.isInitialized) {
            throw new Error('Arena Manager not initialized');
        }

        try {
            console.log(`Creating match: ${request.arenaType} for ${request.players?.length || 0} players`);

            // Validate request
            const validation = this.validateMatchRequest(request);
            if (!validation.valid) {
                throw new Error(`Invalid match request: ${validation.errors.join(', ')}`);
            }

            // Create arena instance
            const arena = this.arenaSystem.createArena(request.arenaType, request.config);

            // Create match session
            const match = this.arenaSystem.startMatch(arena.id, request.players, request.rules);

            // Store match data
            this.activeMatches.set(match.id, {
                id: match.id,
                arena: arena,
                session: match,
                createdAt: Date.now(),
                status: 'active',
                players: request.players,
                spectators: new Set(),
                config: request.config
            });

            // Initialize netcode for all players
            request.players.forEach(player => {
                this.netcodeOptimizer.registerConnection(player.id, {
                    socket: player.socket,
                    endpoint: player.endpoint,
                    bandwidth: player.bandwidth
                });
            });

            // Start anti-cheat monitoring
            request.players.forEach(player => {
                this.antiCheatSystem.startPlayerMonitoring(player.id, {
                    sessionId: match.id,
                    clientInfo: player.clientInfo,
                    networkInfo: player.networkInfo
                });
            });

            // Setup spectator system if enabled
            if (request.allowSpectators) {
                await this.setupSpectatorSystem(match.id, request.spectatorConfig);
            }

            console.log(`Match created successfully: ${match.id}`);
            this.eventEmitter.emit('matchCreated', { matchId: match.id, arena: arena });

            return {
                matchId: match.id,
                arenaId: arena.id,
                status: 'active',
                players: request.players.map(p => ({ id: p.id, name: p.name })),
                spectatorEnabled: request.allowSpectators,
                estimatedDuration: arena.estimatedDuration
            };

        } catch (error) {
            console.error('Failed to create match:', error);
            throw error;
        }
    }

    /**
     * End a match and process results
     */
    async endMatch(matchId, results) {
        const matchData = this.activeMatches.get(matchId);
        if (!matchData) {
            throw new Error(`Match ${matchId} not found`);
        }

        try {
            console.log(`Ending match: ${matchId}`);

            // Process match completion
            const finalResults = this.arenaSystem.endMatch(matchData.session.id);

            // Update player rankings
            const rankingUpdates = [];
            for (const playerResult of finalResults.players) {
                const rankingUpdate = this.rankingSystem.updatePlayerRanking(
                    playerResult.playerId,
                    playerResult
                );
                rankingUpdates.push(rankingUpdate);
            }

            // Stop anti-cheat monitoring
            matchData.players.forEach(player => {
                this.antiCheatSystem.stopPlayerMonitoring(player.id);
            });

            // Cleanup netcode connections
            matchData.players.forEach(player => {
                this.netcodeOptimizer.unregisterConnection(player.id);
            });

            // Stop spectator system
            if (matchData.spectators.size > 0) {
                this.spectatorSystem.destroyStream(matchId);
            }

            // Update match status
            matchData.status = 'completed';
            matchData.completedAt = Date.now();
            matchData.results = finalResults;
            matchData.rankingUpdates = rankingUpdates;

            // Generate match report
            const matchReport = this.generateMatchReport(matchData);

            // Remove from active matches after delay
            setTimeout(() => {
                this.activeMatches.delete(matchId);
            }, 300000); // Keep for 5 minutes for queries

            console.log(`Match ended successfully: ${matchId}`);
            this.eventEmitter.emit('matchEnded', { matchId: matchId, results: finalResults });

            return {
                matchId: matchId,
                status: 'completed',
                results: finalResults,
                rankingUpdates: rankingUpdates,
                report: matchReport
            };

        } catch (error) {
            console.error('Failed to end match:', error);
            throw error;
        }
    }

    /**
     * Get match status
     */
    getMatchStatus(matchId) {
        const matchData = this.activeMatches.get(matchId);
        if (!matchData) {
            return { error: 'Match not found' };
        }

        return {
            matchId: matchId,
            arenaType: matchData.arena.type,
            status: matchData.status,
            createdAt: matchData.createdAt,
            playerCount: matchData.players.length,
            spectatorCount: matchData.spectators.size,
            duration: Date.now() - matchData.createdAt,
            gameState: matchData.session?.getCurrentState?.() || null
        };
    }

    /**
     * Join matchmaking
     */
    async joinMatchmaking(playerId, preferences) {
        if (!this.connectedPlayers.has(playerId)) {
            throw new Error('Player not connected');
        }

        try {
            const queueEntry = this.matchmakingSystem.addToQueue(playerId, preferences);

            this.eventEmitter.emit('playerJoinedMatchmaking', {
                playerId: playerId,
                preferences: preferences,
                queueEntry: queueEntry
            });

            return {
                success: true,
                queueId: queueEntry.preferences.arenaType,
                position: this.matchmakingSystem.getQueuePosition(playerId),
                estimatedWaitTime: this.matchmakingSystem.getEstimatedWaitTime(playerId)
            };

        } catch (error) {
            console.error('Failed to join matchmaking:', error);
            throw error;
        }
    }

    /**
     * Leave matchmaking
     */
    async leaveMatchmaking(playerId) {
        try {
            const success = this.matchmakingSystem.removeFromQueue(playerId);

            if (success) {
                this.eventEmitter.emit('playerLeftMatchmaking', { playerId: playerId });
            }

            return { success: success };

        } catch (error) {
            console.error('Failed to leave matchmaking:', error);
            throw error;
        }
    }

    /**
     * Add spectator to match
     */
    async addSpectator(spectatorId, matchId, options = {}) {
        const matchData = this.activeMatches.get(matchId);
        if (!matchData) {
            throw new Error('Match not found');
        }

        try {
            const spectator = this.spectatorSystem.addSpectator(spectatorId, matchId, options);
            matchData.spectators.add(spectatorId);

            this.eventEmitter.emit('spectatorJoined', {
                spectatorId: spectatorId,
                matchId: matchId,
                options: options
            });

            return {
                success: true,
                spectatorId: spectatorId,
                matchId: matchId,
                streamUrl: this.spectatorSystem.getStreamUrl(matchId),
                spectatorCount: matchData.spectators.size
            };

        } catch (error) {
            console.error('Failed to add spectator:', error);
            throw error;
        }
    }

    /**
     * Remove spectator from match
     */
    async removeSpectator(spectatorId, matchId) {
        const matchData = this.activeMatches.get(matchId);
        if (!matchData) {
            throw new Error('Match not found');
        }

        try {
            const success = this.spectatorSystem.removeSpectator(spectatorId);
            if (success) {
                matchData.spectators.delete(spectatorId);
            }

            this.eventEmitter.emit('spectatorLeft', {
                spectatorId: spectatorId,
                matchId: matchId
            });

            return { success: success };

        } catch (error) {
            console.error('Failed to remove spectator:', error);
            throw error;
        }
    }

    /**
     * Process game tick
     */
    processGameTick(deltaTime) {
        if (!this.isInitialized) return;

        try {
            // Process arena system ticks
            this.arenaSystem.processTick(deltaTime);

            // Process matchmaking
            this.matchmakingSystem.processMatchmaking();

            // Process spectator frames
            this.activeMatches.forEach((matchData, matchId) => {
                if (matchData.spectators.size > 0) {
                    this.spectatorSystem.processFrame(matchId, deltaTime);
                }
            });

            // Process netcode optimization
            this.netcodeOptimizer.serverTick(deltaTime);

            // Update system metrics
            this.updateSystemMetrics();

        } catch (error) {
            console.error('Error in game tick processing:', error);
        }
    }

    /**
     * Get system statistics
     */
    getSystemStats() {
        const now = Date.now();
        const uptime = this.isInitialized ? now - this.startTime : 0;

        return {
            system: {
                initialized: this.isInitialized,
                uptime: uptime,
                version: this.getVersion(),
                nodeVersion: process.version,
                memoryUsage: process.memoryUsage()
            },
            arenas: {
                activeMatches: this.activeMatches.size,
                totalArenas: this.arenaSystem?.arenas.size || 0,
                availableArenaTypes: this.gameModeManager?.getAvailableGameModes() || []
            },
            players: {
                connected: this.connectedPlayers.size,
                inMatchmaking: this.matchmakingSystem?.getTotalPlayersInQueue() || 0,
                inMatches: this.getTotalPlayersInMatches(),
                spectating: this.getTotalSpectators()
            },
            matchmaking: this.matchmakingSystem?.getQueueStatus() || {},
            networking: this.netcodeOptimizer?.getSystemStats() || {},
            antiCheat: {
                monitoring: this.antiCheatSystem?.getMonitoringCount() || 0,
                violations: this.antiCheatSystem?.getTotalViolations() || 0
            }
        };
    }

    /**
     * Get player information
     */
    getPlayerInfo(playerId) {
        const player = this.connectedPlayers.get(playerId);
        if (!player) {
            return { error: 'Player not found' };
        }

        return {
            playerId: playerId,
            name: player.name,
            connectedAt: player.connectedAt,
            currentMatch: this.getPlayerMatch(playerId),
            matchmakingStatus: this.matchmakingSystem?.getPlayerQueueStatus(playerId) || null,
            ranking: this.rankingSystem?.getPlayerRanking(playerId) || null,
            connectionStats: this.netcodeOptimizer?.getConnectionStats(playerId) || null,
            antiCheatStatus: this.antiCheatSystem?.getPlayerStatus(playerId) || null
        };
    }

    /**
     * Handle player connection
     */
    handlePlayerConnection(playerData) {
        const player = {
            id: playerData.id,
            name: playerData.name,
            socket: playerData.socket,
            endpoint: playerData.endpoint,
            connectedAt: Date.now(),
            lastActivity: Date.now(),
            clientInfo: playerData.clientInfo,
            networkInfo: playerData.networkInfo
        };

        this.connectedPlayers.set(player.id, player);

        this.eventEmitter.emit('playerConnected', { playerId: player.id, player: player });

        console.log(`Player connected: ${player.name} (${player.id})`);
        return player;
    }

    /**
     * Handle player disconnection
     */
    handlePlayerDisconnection(playerId) {
        const player = this.connectedPlayers.get(playerId);
        if (!player) return;

        // Leave matchmaking
        try {
            this.matchmakingSystem.removeFromQueue(playerId);
        } catch (error) {
            console.error('Error leaving matchmaking on disconnect:', error);
        }

        // Leave current match
        try {
            const matchId = this.getPlayerMatch(playerId);
            if (matchId) {
                this.handlePlayerLeftMatch(playerId, matchId);
            }
        } catch (error) {
            console.error('Error leaving match on disconnect:', error);
        }

        // Stop anti-cheat monitoring
        try {
            this.antiCheatSystem.stopPlayerMonitoring(playerId);
        } catch (error) {
            console.error('Error stopping anti-cheat on disconnect:', error);
        }

        // Cleanup netcode
        try {
            this.netcodeOptimizer.unregisterConnection(playerId);
        } catch (error) {
            console.error('Error cleaning up netcode on disconnect:', error);
        }

        // Remove from connected players
        this.connectedPlayers.delete(playerId);

        this.eventEmitter.emit('playerDisconnected', { playerId: playerId, player: player });

        console.log(`Player disconnected: ${player.name} (${playerId})`);
    }

    // Private helper methods
    validateMatchRequest(request) {
        const errors = [];

        if (!request.arenaType) {
            errors.push('Arena type is required');
        }

        if (!request.players || !Array.isArray(request.players) || request.players.length === 0) {
            errors.push('Players array is required and must not be empty');
        }

        // Validate arena type
        const availableArenaTypes = this.arenaSystem?.arenaTypes.keys() || [];
        if (!availableArenaTypes.has(request.arenaType)) {
            errors.push(`Invalid arena type: ${request.arenaType}`);
        }

        // Validate players
        if (request.players) {
            request.players.forEach((player, index) => {
                if (!player.id || !player.name) {
                    errors.push(`Player at index ${index} missing id or name`);
                }
            });
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    setupSpectatorSystem(matchId, config) {
        // Initialize spectator system for the match
        const streamConfig = {
            matchId: matchId,
            quality: config?.quality || '1080p',
            commentaryEnabled: config?.commentaryEnabled !== false,
            allowReactions: config?.allowReactions !== false
        };

        this.spectatorSystem.createStream(streamConfig);
    }

    generateMatchReport(matchData) {
        return {
            matchId: matchData.id,
            arenaType: matchData.arena.type,
            duration: matchData.completedAt - matchData.createdAt,
            playerCount: matchData.players.length,
            spectatorCount: matchData.spectators.size,
            results: matchData.results,
            rankingUpdates: matchData.rankingUpdates,
            systemMetrics: this.getSystemStats()
        };
    }

    updateSystemMetrics() {
        const now = Date.now();
        this.systemMetrics.set('lastUpdate', now);
        this.systemMetrics.set('activeMatches', this.activeMatches.size);
        this.systemMetrics.set('connectedPlayers', this.connectedPlayers.size);
        this.systemMetrics.set('memoryUsage', process.memoryUsage());
    }

    getPlayerMatch(playerId) {
        for (const [matchId, matchData] of this.activeMatches) {
            if (matchData.players.some(p => p.id === playerId)) {
                return matchId;
            }
        }
        return null;
    }

    getTotalPlayersInMatches() {
        let total = 0;
        this.activeMatches.forEach(matchData => {
            total += matchData.players.length;
        });
        return total;
    }

    getTotalSpectators() {
        let total = 0;
        this.activeMatches.forEach(matchData => {
            total += matchData.spectators.size;
        });
        return total;
    }

    getVersion() {
        return require('../../package.json').version || '1.0.0';
    }

    handlePlayerLeftMatch(playerId, matchId) {
        const matchData = this.activeMatches.get(matchId);
        if (matchData) {
            // Remove player from match
            matchData.players = matchData.players.filter(p => p.id !== playerId);

            // Notify arena system
            this.arenaSystem?.removePlayerFromMatch(playerId, matchId);
        }
    }

    // Event handling
    async setupEventHandlers() {
        this.arenaSystem?.on?.('matchStarted', (data) => {
            this.eventEmitter.emit('matchStarted', data);
        });

        this.matchmakingSystem?.on?.('matchFound', (data) => {
            this.eventEmitter.emit('matchmakingMatchFound', data);
        });

        this.antiCheatSystem?.on?.('cheatingDetected', (data) => {
            this.eventEmitter.emit('antiCheatViolation', data);
        });
    }

    async startSystemMonitoring() {
        // Start monitoring interval
        setInterval(() => {
            this.updateSystemMetrics();
        }, 10000); // Update every 10 seconds

        // Start performance monitoring
        setInterval(() => {
            this.checkSystemPerformance();
        }, 60000); // Check every minute
    }

    checkSystemPerformance() {
        const memUsage = process.memoryUsage();
        const memUsageMB = memUsage.heapUsed / 1024 / 1024;

        if (memUsageMB > 1000) { // More than 1GB
            console.warn(`High memory usage: ${memUsageMB.toFixed(2)}MB`);
            this.eventEmitter.emit('highMemoryUsage', { usage: memUsageMB });
        }

        // Check for long-running operations
        const activeMatchCount = this.activeMatches.size;
        if (activeMatchCount > 100) {
            console.warn(`High match count: ${activeMatchCount}`);
            this.eventEmitter.emit('highMatchCount', { count: activeMatchCount });
        }
    }

    // Event emitter methods
    on(event, callback) {
        this.eventEmitter.on(event, callback);
    }

    emit(event, data) {
        this.eventEmitter.emit(event, data);
    }
}

/**
 * Simple EventEmitter implementation
 */
class EventEmitter {
    constructor() {
        this.events = new Map();
    }

    on(event, callback) {
        if (!this.events.has(event)) {
            this.events.set(event, []);
        }
        this.events.get(event).push(callback);
    }

    emit(event, data) {
        const callbacks = this.events.get(event);
        if (callbacks) {
            callbacks.forEach(callback => callback(data));
        }
    }
}

module.exports = ArenaManager;