/**
 * Advanced Spectator System for DMlogn8n Multiplayer Arena
 * Features live streaming, multiple camera angles, and AI commentary
 */

class SpectatorSystem {
    constructor() {
        this.activeStreams = new Map();
        this.spectators = new Map();
        this.cameraControllers = new Map();
        this.commentaryEngine = new CommentaryEngine();
        this.streamManager = new StreamManager();
        this.highlightReel = new HighlightReel();

        // Spectator settings
        this.maxSpectators = 1000;
        this.streamQuality = ['720p', '1080p', '1440p', '4k'];
        this.cameraAngles = ['free', 'follow', 'overview', 'action', 'cinematic'];

        this.initializeSystem();
    }

    /**
     * Initialize spectator system
     */
    initializeSystem() {
        // Set up stream endpoints
        this.setupStreamEndpoints();

        // Initialize camera system
        this.initializeCameraSystem();

        // Start commentary engine
        this.commentaryEngine.initialize();

        // Connect to streaming platforms
        this.connectStreamingPlatforms();
    }

    /**
     * Add spectator to match
     */
    addSpectator(spectatorId, matchId, options = {}) {
        // Check match exists and allows spectators
        const match = this.getMatch(matchId);
        if (!match || !match.allowsSpectators) {
            throw new Error(`Match ${matchId} does not allow spectators`);
        }

        // Check spectator limit
        if (this.getSpectatorCount(matchId) >= this.maxSpectators) {
            throw new Error(`Match ${matchId} has reached maximum spectator limit`);
        }

        // Create spectator session
        const spectator = {
            id: spectatorId,
            matchId: matchId,
            joinTime: Date.now(),
            preferences: {
                cameraAngle: options.cameraAngle || 'free',
                streamQuality: options.streamQuality || '1080p',
                commentaryEnabled: options.commentaryEnabled !== false,
                showStats: options.showStats !== false,
                showMinimap: options.showMinimap !== false,
                delay: options.delay || 30 // 30 second delay for competitive integrity
            },
            stats: {
                watchTime: 0,
                cameraChanges: 0,
                reactions: []
            }
        };

        this.spectators.set(spectatorId, spectator);

        // Create or join stream
        this.joinOrCreateStream(spectatorId, matchId, spectator.preferences);

        // Initialize camera controller for spectator
        this.createCameraController(spectatorId, matchId);

        console.log(`Spectator ${spectatorId} joined match ${matchId}`);
        return spectator;
    }

    /**
     * Remove spectator from match
     */
    removeSpectator(spectatorId) {
        const spectator = this.spectators.get(spectatorId);
        if (!spectator) return false;

        // Remove from stream
        this.leaveStream(spectatorId, spectator.matchId);

        // Clean up camera controller
        this.cleanupCameraController(spectatorId);

        // Update statistics
        this.updateSpectatorStatistics(spectator);

        this.spectators.delete(spectatorId);
        console.log(`Spectator ${spectatorId} left match ${spectator.matchId}`);
        return true;
    }

    /**
     * Join or create stream for spectator
     */
    joinOrCreateStream(spectatorId, matchId, preferences) {
        // Check if stream exists for match
        let stream = this.activeStreams.get(matchId);

        if (!stream) {
            // Create new stream
            stream = this.streamManager.createStream({
                matchId: matchId,
                quality: preferences.streamQuality,
                commentaryEnabled: preferences.commentaryEnabled,
                delay: preferences.delay
            });
            this.activeStreams.set(matchId, stream);
        }

        // Add spectator to stream
        stream.addSpectator(spectatorId, preferences);

        return stream;
    }

    /**
     * Create camera controller for spectator
     */
    createCameraController(spectatorId, matchId) {
        const controller = new CameraController({
            spectatorId: spectatorId,
            matchId: matchId,
            defaultAngle: 'free'
        });

        this.cameraControllers.set(spectatorId, controller);
        return controller;
    }

    /**
     * Change camera angle for spectator
     */
    changeCameraAngle(spectatorId, angle) {
        const controller = this.cameraControllers.get(spectatorId);
        if (!controller) return false;

        if (!this.cameraAngles.includes(angle)) {
            throw new Error(`Invalid camera angle: ${angle}`);
        }

        controller.setAngle(angle);

        // Update spectator statistics
        const spectator = this.spectators.get(spectatorId);
        if (spectator) {
            spectator.stats.cameraChanges++;
        }

        return true;
    }

    /**
     * Switch camera to follow specific player
     */
    followPlayer(spectatorId, playerId) {
        const controller = this.cameraControllers.get(spectatorId);
        if (!controller) return false;

        const spectator = this.spectators.get(spectatorId);
        const match = this.getMatch(spectator.matchId);

        if (!match || !match.players.find(p => p.id === playerId)) {
            throw new Error(`Player ${playerId} not found in match`);
        }

        controller.followPlayer(playerId);
        return true;
    }

    /**
     * Get spectator data for broadcasting
     */
    getSpectatorData(matchId) {
        const match = this.getMatch(matchId);
        if (!match) return null;

        const spectators = Array.from(this.spectators.values())
            .filter(s => s.matchId === matchId);

        const stream = this.activeStreams.get(matchId);

        return {
            matchId: matchId,
            spectatorCount: spectators.length,
            streamActive: !!stream,
            streamQuality: stream ? stream.quality : null,
            popularCameraAngles: this.getPopularCameraAngles(spectators),
            averageWatchTime: this.calculateAverageWatchTime(spectators),
            commentary: this.commentaryEngine.getCurrentCommentary(matchId)
        };
    }

    /**
     * Process spectator frame update
     */
    processFrame(matchId, deltaTime) {
        const stream = this.activeStreams.get(matchId);
        if (!stream) return;

        // Update camera controllers
        this.updateCameraControllers(matchId, deltaTime);

        // Generate commentary
        this.commentaryEngine.processMatchUpdate(matchId, deltaTime);

        // Check for highlights
        this.highlightReel.processFrame(matchId, deltaTime);

        // Broadcast to all spectators in match
        this.broadcastToSpectators(matchId);
    }

    /**
     * Update camera controllers for match
     */
    updateCameraControllers(matchId, deltaTime) {
        this.cameraControllers.forEach((controller, spectatorId) => {
            if (controller.matchId === matchId) {
                controller.update(deltaTime);
            }
        });
    }

    /**
     * Broadcast frame data to spectators
     */
    broadcastToSpectators(matchId) {
        const match = this.getMatch(matchId);
        const stream = this.activeStreams.get(matchId);

        if (!match || !stream) return;

        // Generate frame data
        const frameData = this.generateFrameData(match);

        // Broadcast to all spectators
        stream.broadcast(frameData);
    }

    /**
     * Generate frame data for broadcasting
     */
    generateFrameData(match) {
        const frameData = {
            timestamp: Date.now(),
            matchState: {
                players: match.players.map(player => ({
                    id: player.id,
                    name: player.name,
                    position: player.position,
                    health: player.currentHealth,
                    mana: player.currentMana,
                    status: player.status,
                    actions: player.recentActions
                })),
                environment: match.environment,
                timeRemaining: match.getTimeRemaining(),
                round: match.currentRound
            },
            commentary: this.commentaryEngine.getCurrentCommentary(match.id),
            statistics: this.generateLiveStatistics(match),
            highlights: this.highlightReel.getRecentHighlights(match.id, 5)
        };

        return frameData;
    }

    /**
     * Generate live statistics
     */
    generateLiveStatistics(match) {
        const stats = {
            damageLeaders: this.getDamageLeaders(match),
            killLeaders: this.getKillLeaders(match),
            objectiveControl: this.getObjectiveControl(match),
            teamScores: this.getTeamScores(match),
            momentum: this.calculateMomentum(match)
        };

        return stats;
    }

    /**
     * Get damage leaders
     */
    getDamageLeaders(match) {
        const players = match.players.map(player => ({
            id: player.id,
            name: player.name,
            damage: match.getPlayerStats(player.id).damageDealt
        }));

        return players.sort((a, b) => b.damage - a.damage).slice(0, 3);
    }

    /**
     * Get kill leaders
     */
    getKillLeaders(match) {
        const players = match.players.map(player => ({
            id: player.id,
            name: player.name,
            kills: match.getPlayerStats(player.id).kills
        }));

        return players.sort((a, b) => b.kills - a.kills).slice(0, 3);
    }

    /**
     * Get objective control
     */
    getObjectiveControl(match) {
        if (!match.objectives) return {};

        return match.objectives.map(objective => ({
            id: objective.id,
            name: objective.name,
            controller: objective.controller,
            captureProgress: objective.captureProgress,
            contested: objective.contested
        }));
    }

    /**
     * Get team scores
     */
    getTeamScores(match) {
        if (!match.teams) return {};

        const scores = {};
        Object.entries(match.teams).forEach(([teamId, team]) => {
            scores[teamId] = {
                score: team.score,
                players: team.players.length,
                status: team.status
            };
        });

        return scores;
    }

    /**
     * Calculate match momentum
     */
    calculateMomentum(match) {
        // Simple momentum calculation based on recent actions
        const recentActions = match.getRecentActions(30); // Last 30 seconds
        const momentum = {};

        match.players.forEach(player => {
            const playerActions = recentActions.filter(action => action.playerId === player.id);
            const positiveActions = playerActions.filter(action =>
                action.type === 'kill' || action.type === 'objective_capture'
            ).length;
            const negativeActions = playerActions.filter(action =>
                action.type === 'death' || action.type === 'objective_lost'
            ).length;

            momentum[player.id] = positiveActions - negativeActions;
        });

        return momentum;
    }

    /**
     * Handle spectator reaction
     */
    handleSpectatorReaction(spectatorId, reaction) {
        const spectator = this.spectators.get(spectatorId);
        if (!spectator) return false;

        spectator.stats.reactions.push({
            type: reaction.type,
            timestamp: Date.now(),
            target: reaction.target
        });

        // Broadcast reaction to other spectators
        this.broadcastReaction(spectatorId, reaction);

        return true;
    }

    /**
     * Get popular camera angles
     */
    getPopularCameraAngles(spectators) {
        const angleCounts = {};

        spectators.forEach(spectator => {
            const controller = this.cameraControllers.get(spectator.id);
            if (controller) {
                const angle = controller.currentAngle;
                angleCounts[angle] = (angleCounts[angle] || 0) + 1;
            }
        });

        return Object.entries(angleCounts)
            .sort(([,a], [,b]) => b - a)
            .map(([angle, count]) => ({ angle, count }));
    }

    /**
     * Calculate average watch time
     */
    calculateAverageWatchTime(spectators) {
        if (spectators.length === 0) return 0;

        const now = Date.now();
        const totalWatchTime = spectators.reduce((sum, spectator) => {
            return sum + (now - spectator.joinTime);
        }, 0);

        return Math.floor(totalWatchTime / spectators.length / 1000);
    }

    /**
     * Update spectator statistics
     */
    updateSpectatorStatistics(spectator) {
        spectator.stats.watchTime = Date.now() - spectator.joinTime;

        // Store in analytics
        this.storeSpectatorAnalytics(spectator);
    }

    /**
     * Store spectator analytics data
     */
    storeSpectatorAnalytics(spectator) {
        // In production, this would store in database
        console.log(`Storing analytics for spectator ${spectator.id}:`, spectator.stats);
    }

    /**
     * Get spectator count for match
     */
    getSpectatorCount(matchId) {
        return Array.from(this.spectators.values())
            .filter(s => s.matchId === matchId).length;
    }

    /**
     * Get match data (mock implementation)
     */
    getMatch(matchId) {
        // In production, this would fetch from match system
        return {
            id: matchId,
            allowsSpectators: true,
            players: [],
            environment: {},
            getTimeRemaining: () => 300,
            currentRound: 1,
            getPlayerStats: () => ({}),
            getRecentActions: () => []
        };
    }

    /**
     * Setup stream endpoints
     */
    setupStreamEndpoints() {
        // Setup WebSocket endpoints for real-time streaming
        // Setup HTTP endpoints for VOD and replay access
    }

    /**
     * Initialize camera system
     */
    initializeCameraSystem() {
        // Setup camera presets and behaviors
    }

    /**
     * Connect to streaming platforms
     */
    connectStreamingPlatforms() {
        // Connect to Twitch, YouTube, etc.
    }

    /**
     * Leave stream
     */
    leaveStream(spectatorId, matchId) {
        const stream = this.activeStreams.get(matchId);
        if (stream) {
            stream.removeSpectator(spectatorId);

            // Clean up empty streams
            if (stream.spectatorCount === 0) {
                this.streamManager.destroyStream(matchId);
                this.activeStreams.delete(matchId);
            }
        }
    }

    /**
     * Cleanup camera controller
     */
    cleanupCameraController(spectatorId) {
        const controller = this.cameraControllers.get(spectatorId);
        if (controller) {
            controller.cleanup();
            this.cameraControllers.delete(spectatorId);
        }
    }

    /**
     * Broadcast reaction to spectators
     */
    broadcastReaction(spectatorId, reaction) {
        const spectator = this.spectators.get(spectatorId);
        if (!spectator) return;

        const stream = this.activeStreams.get(spectator.matchId);
        if (stream) {
            stream.broadcastReaction(spectatorId, reaction);
        }
    }
}

/**
 * Camera Controller for individual spectator
 */
class CameraController {
    constructor(options) {
        this.spectatorId = options.spectatorId;
        this.matchId = options.matchId;
        this.currentAngle = options.defaultAngle;
        this.targetPlayer = null;
        this.position = { x: 0, y: 20, z: 0 };
        this.rotation = { x: 0, y: 0, z: 0 };
        this.zoom = 1.0;
        this.smoothing = 0.1;
    }

    setAngle(angle) {
        this.currentAngle = angle;
        this.adjustCameraForAngle(angle);
    }

    followPlayer(playerId) {
        this.targetPlayer = playerId;
        this.currentAngle = 'follow';
    }

    update(deltaTime) {
        switch (this.currentAngle) {
            case 'follow':
                this.updateFollowCamera(deltaTime);
                break;
            case 'action':
                this.updateActionCamera(deltaTime);
                break;
            case 'cinematic':
                this.updateCinematicCamera(deltaTime);
                break;
            case 'overview':
                this.updateOverviewCamera(deltaTime);
                break;
            case 'free':
            default:
                // Free camera doesn't auto-update
                break;
        }
    }

    updateFollowCamera(deltaTime) {
        if (!this.targetPlayer) return;

        const player = this.getPlayerPosition(this.targetPlayer);
        if (!player) return;

        // Smooth camera follow
        const targetPosition = {
            x: player.x,
            y: player.y + 10,
            z: player.z + 15
        };

        this.position = this.lerp(this.position, targetPosition, this.smoothing);
        this.rotation = {
            x: -0.3,
            y: Math.atan2(player.x - this.position.x, player.z - this.position.z),
            z: 0
        };
    }

    updateActionCamera(deltaTime) {
        // Focus on area with most action
        const actionCenter = this.findActionCenter();
        if (actionCenter) {
            const targetPosition = {
                x: actionCenter.x,
                y: actionCenter.y + 25,
                z: actionCenter.z + 20
            };

            this.position = this.lerp(this.position, targetPosition, this.smoothing * 2);
            this.rotation = {
                x: -0.4,
                y: Math.atan2(actionCenter.x - this.position.x, actionCenter.z - this.position.z),
                z: 0
            };
        }
    }

    updateCinematicCamera(deltaTime) {
        // Dynamic cinematic shots
        const cinematicShot = this.selectCinematicShot();
        if (cinematicShot) {
            this.position = this.lerp(this.position, cinematicShot.position, this.smoothing * 0.5);
            this.rotation = this.lerp(this.rotation, cinematicShot.rotation, this.smoothing * 0.5);
        }
    }

    updateOverviewCamera(deltaTime) {
        // Top-down view of entire arena
        const arena = this.getArenaInfo();
        if (arena) {
            this.position = {
                x: arena.center.x,
                y: arena.height + 50,
                z: arena.center.z
            };
            this.rotation = { x: -Math.PI / 2, y: 0, z: 0 };
            this.zoom = 0.8;
        }
    }

    adjustCameraForAngle(angle) {
        switch (angle) {
            case 'overview':
                this.zoom = 0.8;
                break;
            case 'cinematic':
                this.zoom = 1.2;
                break;
            case 'action':
                this.zoom = 1.0;
                break;
            default:
                this.zoom = 1.0;
        }
    }

    findActionCenter() {
        // Find center of recent combat activity
        // This would analyze recent actions to find hotspots
        return { x: 0, y: 0, z: 0 };
    }

    selectCinematicShot() {
        // Select dramatic camera shot based on game state
        const shots = [
            { position: { x: 10, y: 15, z: 10 }, rotation: { x: -0.3, y: 0.8, z: 0 } },
            { position: { x: -10, y: 20, z: -10 }, rotation: { x: -0.4, y: -0.8, z: 0 } },
            { position: { x: 0, y: 25, z: 15 }, rotation: { x: -0.5, y: 0, z: 0 } }
        ];

        return shots[Math.floor(Math.random() * shots.length)];
    }

    getPlayerPosition(playerId) {
        // Get player position from match data
        return { x: 0, y: 0, z: 0 };
    }

    getArenaInfo() {
        // Get arena information
        return { center: { x: 0, y: 0, z: 0 }, height: 20 };
    }

    lerp(start, end, factor) {
        const result = {};
        Object.keys(start).forEach(key => {
            result[key] = start[key] + (end[key] - start[key]) * factor;
        });
        return result;
    }

    cleanup() {
        // Clean up camera resources
    }
}

module.exports = {
    SpectatorSystem,
    CameraController
};