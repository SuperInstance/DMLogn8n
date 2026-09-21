/**
 * Game Mode Manager for DMlogn8n Multiplayer Arena
 * Handles different game modes, rules, and custom game configurations
 */

class GameModeManager {
    constructor() {
        this.gameModes = new Map();
        this.ruleEngine = new RuleEngine();
        this.customRules = new Map();
        this.activeGameModes = new Map();
        this.gameModeHistory = new Map();

        this.initializeGameModes();
    }

    /**
     * Initialize all game modes
     */
    initializeGameModes() {
        // Core game modes
        this.registerGameMode('deathmatch', new DeathmatchMode());
        this.registerGameMode('capture_the_flag', new CaptureTheFlagMode());
        this.registerGameMode('king_of_the_hill', new KingOfTheHillMode());
        this.registerGameMode('escort', new EscortMode());
        this.registerGameMode('survival', new SurvivalMode());

        // Arena-specific modes
        this.registerGameMode('domination', new DominationMode());
        this.registerGameMode('assault', new AssaultMode());
        this.registerGameMode('defend', new DefendMode());

        // Special event modes
        this.registerGameMode('boss_battle', new BossBattleMode());
        this.registerGameMode('race', new RaceMode());
        this.registerGameMode('puzzle_challenge', new PuzzleChallengeMode());
    }

    /**
     * Register a new game mode
     */
    registerGameMode(modeId, gameMode) {
        this.gameModes.set(modeId, gameMode);
        console.log(`Registered game mode: ${modeId}`);
    }

    /**
     * Create a new game instance
     */
    createGame(modeId, config = {}) {
        const gameMode = this.gameModes.get(modeId);
        if (!gameMode) {
            throw new Error(`Game mode ${modeId} not found`);
        }

        const gameId = this.generateGameId();
        const game = new GameInstance(gameId, gameMode, config);

        // Apply custom rules if specified
        if (config.customRules) {
            this.applyCustomRules(game, config.customRules);
        }

        // Initialize game mode
        gameMode.initialize(game);

        this.activeGameModes.set(gameId, game);

        console.log(`Created game instance ${gameId} with mode ${modeId}`);
        return game;
    }

    /**
     * Apply custom rules to game
     */
    applyCustomRules(game, customRules) {
        const ruleSet = new RuleSet(customRules);
        game.customRuleSet = ruleSet;

        // Validate rules
        const validation = this.ruleEngine.validateRules(ruleSet, game.gameMode);
        if (!validation.valid) {
            throw new Error(`Invalid custom rules: ${validation.errors.join(', ')}`);
        }
    }

    /**
     * Get available game modes
     */
    getAvailableGameModes() {
        const modes = {};

        this.gameModes.forEach((gameMode, modeId) => {
            modes[modeId] = {
                id: modeId,
                name: gameMode.name,
                description: gameMode.description,
                minPlayers: gameMode.minPlayers,
                maxPlayers: gameMode.maxPlayers,
                estimatedDuration: gameMode.estimatedDuration,
                complexity: gameMode.complexity,
                tags: gameMode.tags,
                customRulesSupported: gameMode.supportsCustomRules
            };
        });

        return modes;
    }

    /**
     * Get game mode details
     */
    getGameModeDetails(modeId) {
        const gameMode = this.gameModes.get(modeId);
        if (!gameMode) return null;

        return {
            ...gameMode.getConfig(),
            availableMaps: gameMode.getAvailableMaps(),
            rulePresets: gameMode.getRulePresets(),
            statistics: this.getGameModeStatistics(modeId)
        };
    }

    /**
     * Process game tick
     */
    processGameTick(gameId, deltaTime) {
        const game = this.activeGameModes.get(gameId);
        if (!game || game.status !== 'active') return;

        // Process game mode logic
        game.gameMode.processTick(game, deltaTime);

        // Apply custom rules
        if (game.customRuleSet) {
            this.ruleEngine.processRules(game, deltaTime);
        }

        // Check win conditions
        const winCondition = game.gameMode.checkWinCondition(game);
        if (winCondition) {
            this.endGame(gameId, winCondition);
        }
    }

    /**
     * End game instance
     */
    endGame(gameId, result) {
        const game = this.activeGameModes.get(gameId);
        if (!game) return;

        // Finalize game mode
        game.gameMode.finalize(game, result);

        // Calculate results
        const finalResults = this.calculateGameResults(game, result);

        // Update game mode history
        this.updateGameModeHistory(game, finalResults);

        // Clean up
        this.activeGameModes.delete(gameId);

        return finalResults;
    }

    /**
     * Calculate final game results
     */
    calculateGameResults(game, winCondition) {
        const results = {
            gameId: game.id,
            gameMode: game.gameMode.id,
            duration: Date.now() - game.startTime,
            winner: winCondition.winner,
            winCondition: winCondition.type,
            playerResults: [],
            teamResults: [],
            statistics: {
                totalKills: 0,
                totalDeaths: 0,
                totalDamage: 0,
                objectivesCompleted: 0
            }
        };

        // Calculate individual player results
        game.players.forEach(player => {
            const playerResult = {
                playerId: player.id,
                playerName: player.name,
                teamId: player.teamId,
                placement: this.calculatePlayerPlacement(player, game, winCondition),
                statistics: {
                    kills: player.stats.kills,
                    deaths: player.stats.deaths,
                    assists: player.stats.assists,
                    damageDealt: player.stats.damageDealt,
                    damageReceived: player.stats.damageReceived,
                    healingDone: player.stats.healingDone,
                    objectives: player.stats.objectives,
                    score: this.calculatePlayerScore(player, game)
                },
                rewards: this.calculatePlayerRewards(player, game, winCondition)
            };

            results.playerResults.push(playerResult);

            // Aggregate statistics
            results.statistics.totalKills += playerResult.statistics.kills;
            results.statistics.totalDeaths += playerResult.statistics.deaths;
            results.statistics.totalDamage += playerResult.statistics.damageDealt;
            results.statistics.objectivesCompleted += playerResult.statistics.objectives;
        });

        // Sort players by placement
        results.playerResults.sort((a, b) => a.placement - b.placement);

        // Calculate team results if applicable
        if (game.teams) {
            results.teamResults = this.calculateTeamResults(game, results.playerResults);
        }

        return results;
    }

    /**
     * Create custom game mode
     */
    createCustomGameMode(modeConfig) {
        const customMode = new CustomGameMode(modeConfig);
        const modeId = this.generateCustomModeId();

        this.registerGameMode(modeId, customMode);
        this.customRules.set(modeId, modeConfig);

        return modeId;
    }

    /**
     * Get game mode statistics
     */
    getGameModeStatistics(modeId) {
        const history = this.gameModeHistory.get(modeId) || [];
        const totalGames = history.length;

        if (totalGames === 0) {
            return {
                totalGames: 0,
                averageDuration: 0,
                popularMaps: [],
                winRateByClass: {}
            };
        }

        const totalDuration = history.reduce((sum, game) => sum + game.duration, 0);
        const mapCounts = {};
        const classWins = {};

        history.forEach(game => {
            // Track map popularity
            mapCounts[game.map] = (mapCounts[game.map] || 0) + 1;

            // Track class win rates
            game.playerResults.forEach(player => {
                if (player.placement === 1) {
                    const playerClass = player.characterClass;
                    classWins[playerClass] = (classWins[playerClass] || 0) + 1;
                }
            });
        });

        return {
            totalGames,
            averageDuration: Math.floor(totalDuration / totalGames / 1000), // seconds
            popularMaps: Object.entries(mapCounts)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 5)
                .map(([map, count]) => ({ map, count, percentage: (count / totalGames * 100).toFixed(1) })),
            winRateByClass: classWins
        };
    }

    // Helper methods
    generateGameId() {
        return `game_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    generateCustomModeId() {
        return `custom_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    calculatePlayerPlacement(player, game, winCondition) {
        // Implementation varies by game mode
        return game.gameMode.calculatePlayerPlacement(player, game, winCondition);
    }

    calculatePlayerScore(player, game) {
        return game.gameMode.calculatePlayerScore(player, game);
    }

    calculatePlayerRewards(player, game, winCondition) {
        return game.gameMode.calculatePlayerRewards(player, game, winCondition);
    }

    calculateTeamResults(game, playerResults) {
        // Calculate team-based results
        return [];
    }

    updateGameModeHistory(game, results) {
        if (!this.gameModeHistory.has(game.gameMode.id)) {
            this.gameModeHistory.set(game.gameMode.id, []);
        }

        const history = this.gameModeHistory.get(game.gameMode.id);
        history.push({
            gameId: game.id,
            timestamp: Date.now(),
            duration: results.duration,
            map: game.map,
            playerCount: game.players.length,
            winner: results.winner,
            playerResults: results.playerResults
        });

        // Keep history manageable
        if (history.length > 1000) {
            history.shift();
        }
    }
}

/**
 * Game Instance class
 */
class GameInstance {
    constructor(id, gameMode, config) {
        this.id = id;
        this.gameMode = gameMode;
        this.config = config;
        this.players = [];
        this.teams = new Map();
        this.status = 'initializing';
        this.startTime = null;
        this.endTime = null;
        this.map = config.map || gameMode.defaultMap;
        this.customRuleSet = null;
        this.gameState = {};
        this.objectives = [];
        this.events = [];
    }

    addPlayer(player) {
        this.players.push(player);
    }

    addTeam(teamId, players) {
        this.teams.set(teamId, {
            id: teamId,
            players: players,
            score: 0,
            objectives: []
        });

        players.forEach(player => {
            player.teamId = teamId;
        });
    }

    start() {
        this.status = 'active';
        this.startTime = Date.now();
        this.gameMode.onStart(this);
    }

    pause() {
        this.status = 'paused';
        this.gameMode.onPause(this);
    }

    resume() {
        this.status = 'active';
        this.gameMode.onResume(this);
    }

    stop() {
        this.status = 'stopped';
        this.endTime = Date.now();
        this.gameMode.onStop(this);
    }
}

/**
 * Base Game Mode class
 */
class BaseGameMode {
    constructor(config) {
        this.id = config.id;
        this.name = config.name;
        this.description = config.description;
        this.minPlayers = config.minPlayers;
        this.maxPlayers = config.maxPlayers;
        this.estimatedDuration = config.estimatedDuration;
        this.complexity = config.complexity || 'medium';
        this.tags = config.tags || [];
        this.supportsCustomRules = config.supportsCustomRules || false;
        this.defaultMap = config.defaultMap;
    }

    initialize(game) {
        // Override in subclasses
    }

    processTick(game, deltaTime) {
        // Override in subclasses
    }

    checkWinCondition(game) {
        // Override in subclasses
        return null;
    }

    finalize(game, result) {
        // Override in subclasses
    }

    calculatePlayerPlacement(player, game, winCondition) {
        // Override in subclasses
        return 1;
    }

    calculatePlayerScore(player, game) {
        // Default scoring calculation
        let score = 0;
        score += player.stats.kills * 10;
        score += player.stats.assists * 5;
        score += player.stats.damageDealt * 0.1;
        score += player.stats.objectives * 50;
        score -= player.stats.deaths * 5;

        return Math.max(0, score);
    }

    calculatePlayerRewards(player, game, winCondition) {
        const baseRewards = {
            xp: 100,
            gold: 50,
            score: this.calculatePlayerScore(player, game)
        };

        // Apply placement multipliers
        const placementMultiplier = this.getPlacementMultiplier(player, game);
        baseRewards.xp = Math.floor(baseRewards.xp * placementMultiplier);
        baseRewards.gold = Math.floor(baseRewards.gold * placementMultiplier);

        return baseRewards;
    }

    getPlacementMultiplier(player, game) {
        // Override in subclasses for mode-specific multipliers
        return 1.0;
    }

    getConfig() {
        return {
            id: this.id,
            name: this.name,
            description: this.description,
            minPlayers: this.minPlayers,
            maxPlayers: this.maxPlayers,
            estimatedDuration: this.estimatedDuration,
            complexity: this.complexity,
            tags: this.tags,
            supportsCustomRules: this.supportsCustomRules,
            defaultMap: this.defaultMap
        };
    }

    getAvailableMaps() {
        // Override in subclasses
        return [this.defaultMap];
    }

    getRulePresets() {
        // Override in subclasses
        return {};
    }

    // Lifecycle hooks
    onStart(game) {}
    onPause(game) {}
    onResume(game) {}
    onStop(game) {}
}

module.exports = {
    GameModeManager,
    GameInstance,
    BaseGameMode
};