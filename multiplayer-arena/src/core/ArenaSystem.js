/**
 * Core Arena System for DMlogn8n Multiplayer Arena
 * Handles arena creation, management, and basic game loop
 */

class ArenaSystem {
    constructor() {
        this.arenas = new Map();
        this.activeSessions = new Map();
        this.playerRegistry = new Map();
        this.eventEmitter = new EventEmitter();

        // Initialize arena types
        this.arenaTypes = new Map();
        this.registerArenaTypes();
    }

    registerArenaTypes() {
        this.arenaTypes.set('1v1_duel', new DuelingArena());
        this.arenaTypes.set('team_competition', new TeamArena());
        this.arenaTypes.set('battle_royale', new BattleRoyaleArena());
        this.arenaTypes.set('monster_hunt', new MonsterHuntArena());
        this.arenaTypes.set('puzzle_race', new PuzzleRaceArena());
        this.arenaTypes.set('siege_warfare', new SiegeArena());
    }

    /**
     * Create a new arena instance
     */
    createArena(type, config = {}) {
        if (!this.arenaTypes.has(type)) {
            throw new Error(`Unknown arena type: ${type}`);
        }

        const arenaId = this.generateArenaId();
        const arenaClass = this.arenaTypes.get(type);
        const arena = new arenaClass(arenaId, config);

        this.arenas.set(arenaId, arena);
        this.eventEmitter.emit('arenaCreated', { arenaId, type, config });

        return arena;
    }

    /**
     * Start a new match session
     */
    startMatch(arenaId, players, rules = {}) {
        const arena = this.arenas.get(arenaId);
        if (!arena) {
            throw new Error(`Arena ${arenaId} not found`);
        }

        if (!arena.validatePlayers(players)) {
            throw new Error('Invalid player configuration for this arena type');
        }

        const sessionId = this.generateSessionId();
        const session = new MatchSession(sessionId, arenaId, players, rules);

        // Register players
        players.forEach(player => {
            this.playerRegistry.set(player.id, {
                ...player,
                currentSession: sessionId,
                arenaType: arena.type
            });
        });

        this.activeSessions.set(sessionId, session);
        arena.initializeSession(session);

        this.eventEmitter.emit('matchStarted', { sessionId, arenaId, players });

        return session;
    }

    /**
     * Process game state updates
     */
    processTick(deltaTime) {
        this.activeSessions.forEach(session => {
            if (session.isActive()) {
                session.processTick(deltaTime);

                // Check for session completion
                if (session.isComplete()) {
                    this.endMatch(session.id);
                }
            }
        });
    }

    /**
     * End a match session
     */
    endMatch(sessionId) {
        const session = this.activeSessions.get(sessionId);
        if (!session) return;

        const results = session.getResults();
        const arena = this.arenas.get(session.arenaId);

        // Unregister players
        session.players.forEach(player => {
            this.playerRegistry.delete(player.id);
        });

        this.activeSessions.delete(sessionId);

        this.eventEmitter.emit('matchEnded', { sessionId, results });

        return results;
    }

    /**
     * Get arena information
     */
    getArenaInfo(arenaId) {
        const arena = this.arenas.get(arenaId);
        if (!arena) return null;

        return {
            id: arena.id,
            type: arena.type,
            name: arena.name,
            description: arena.description,
            maxPlayers: arena.maxPlayers,
            currentSession: arena.currentSession
        };
    }

    /**
     * Get player's current match
     */
    getPlayerMatch(playerId) {
        const player = this.playerRegistry.get(playerId);
        if (!player) return null;

        return this.activeSessions.get(player.currentSession);
    }

    /**
     * Generate unique arena ID
     */
    generateArenaId() {
        return `arena_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Generate unique session ID
     */
    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
}

/**
 * Base Arena Class
 */
class BaseArena {
    constructor(id, config = {}) {
        this.id = id;
        this.config = config;
        this.currentSession = null;
        this.environment = null;
    }

    validatePlayers(players) {
        return players.length >= this.minPlayers && players.length <= this.maxPlayers;
    }

    initializeSession(session) {
        this.currentSession = session;
        this.setupEnvironment();
    }

    setupEnvironment() {
        // Override in subclasses
    }

    getGameRules() {
        return this.config.rules || {};
    }
}

module.exports = { ArenaSystem, BaseArena };