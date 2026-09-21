/**
 * Capture the Flag Game Mode - Team-based objective gameplay
 */

const BaseGameMode = require('./GameModeManager').BaseGameMode;

class CaptureTheFlagMode extends BaseGameMode {
    constructor() {
        super({
            id: 'capture_the_flag',
            name: 'Capture the Flag',
            description: 'Team-based objective mode. Capture the enemy flag while defending your own!',
            minPlayers: 4,
            maxPlayers: 16,
            estimatedDuration: 900, // 15 minutes
            complexity: 'medium',
            tags: ['team', 'objective', 'ctf', 'strategy'],
            supportsCustomRules: true,
            defaultMap: 'ctf_valley'
        });

        // Default CTF settings
        this.defaultSettings = {
            captureLimit: 3,
            timeLimit: 900, // 15 minutes
            respawnTime: 8,
            flagReturnTime: 30,
            captureTime: 5,
            friendlyFire: false,
            classRestrictions: false,
            powerUps: true,
            vehicleSupport: false
        };
    }

    initialize(game) {
        // Apply game mode settings
        game.settings = { ...this.defaultSettings, ...game.config };

        // Initialize game state
        game.gameState = {
            leadingTeam: null,
            flagStatus: {
                team1: { home: true, carrier: null, position: null },
                team2: { home: true, carrier: null, position: null }
            },
            captures: {
                team1: 0,
                team2: 0
            },
            gameTime: 0,
            lastCaptureTime: 0,
            suddenDeath: false
        };

        // Initialize teams
        this.initializeTeams(game);

        // Initialize player stats
        this.initializePlayerStats(game);

        // Set up flags
        this.setupFlags(game);

        // Set up spawn points
        this.setupSpawnPoints(game);

        // Set up power-ups if enabled
        if (game.settings.powerUps) {
            this.setupPowerUps(game);
        }
    }

    initializeTeams(game) {
        // Create two balanced teams
        const team1Players = [];
        const team2Players = [];

        // Simple team balancing - in production would be more sophisticated
        game.players.forEach((player, index) => {
            if (index % 2 === 0) {
                team1Players.push(player);
                player.teamId = 'team1';
            } else {
                team2Players.push(player);
                player.teamId = 'team2';
            }
        });

        game.teams.set('team1', {
            id: 'team1',
            name: 'Blue Team',
            players: team1Players,
            score: 0,
            flag: null,
            base: { position: { x: -40, y: 0, z: 0 }, radius: 10 },
            color: '#4169E1'
        });

        game.teams.set('team2', {
            id: 'team2',
            name: 'Red Team',
            players: team2Players,
            score: 0,
            flag: null,
            base: { position: { x: 40, y: 0, z: 0 }, radius: 10 },
            color: '#DC143C'
        });
    }

    initializePlayerStats(game) {
        game.players.forEach(player => {
            player.stats = {
                kills: 0,
                deaths: 0,
                assists: 0,
                damageDealt: 0,
                damageReceived: 0,
                healingDone: 0,
                flagCaptures: 0,
                flagReturns: 0,
                flagPickups: 0,
                flagCarrierKills: 0,
                defenseKills: 0,
                objectiveTime: 0
            };

            player.score = 0;
            player.isCarryingFlag = false;
            player.hasEnemyFlag = false;
            player.hasFriendlyFlag = false;
        });
    }

    setupFlags(game) {
        const team1 = game.teams.get('team1');
        const team2 = game.teams.get('team2');

        // Set up flags
        game.flags = {
            team1: {
                id: 'flag_team1',
                teamId: 'team1',
                position: { x: team1.base.position.x, y: 0, z: team1.base.position.z + 5 },
                homePosition: { x: team1.base.position.x, y: 0, z: team1.base.position.z + 5 },
                isHome: true,
                carrier: null,
                pickupRadius: 3,
                returnTime: game.settings.flagReturnTime
            },
            team2: {
                id: 'flag_team2',
                teamId: 'team2',
                position: { x: team2.base.position.x, y: 0, z: team2.base.position.z - 5 },
                homePosition: { x: team2.base.position.x, y: 0, z: team2.base.position.z - 5 },
                isHome: true,
                carrier: null,
                pickupRadius: 3,
                returnTime: game.settings.flagReturnTime
            }
        };

        // Link flags to teams
        team1.flag = game.flags.team1;
        team2.flag = game.flags.team2;
    }

    setupSpawnPoints(game) {
        const team1 = game.teams.get('team1');
        const team2 = game.teams.get('team2');

        // Team spawn points
        game.spawnPoints = {
            team1: [
                { x: team1.base.position.x - 5, y: 0, z: team1.base.position.z - 5 },
                { x: team1.base.position.x + 5, y: 0, z: team1.base.position.z - 5 },
                { x: team1.base.position.x, y: 0, z: team1.base.position.z - 10 }
            ],
            team2: [
                { x: team2.base.position.x - 5, y: 0, z: team2.base.position.z + 5 },
                { x: team2.base.position.x + 5, y: 0, z: team2.base.position.z + 5 },
                { x: team2.base.position.x, y: 0, z: team2.base.position.z + 10 }
            ]
        };

        // Assign initial spawn positions
        game.teams.forEach((team, teamId) => {
            team.players.forEach((player, index) => {
                const spawnPoints = game.spawnPoints[teamId];
                const spawnPoint = spawnPoints[index % spawnPoints.length];
                player.position = { ...spawnPoint };
                player.respawnPosition = { ...spawnPoint };
            });
        });
    }

    setupPowerUps(game) {
        game.powerUps = [
            { id: 'powerup_speed', type: 'speed_boost', position: { x: 0, y: 0, z: 20 }, duration: 10, respawnTime: 60 },
            { id: 'powerup_shield', type: 'shield_boost', position: { x: -20, y: 0, z: 0 }, duration: 15, respawnTime: 90 },
            { id: 'powerup_damage', type: 'damage_boost', position: { x: 20, y: 0, z: 0 }, duration: 10, respawnTime: 90 },
            { id: 'powerup_health', type: 'health_restore', position: { x: 0, y: 0, z: -20 }, respawnTime: 45 }
        ];
    }

    processTick(game, deltaTime) {
        game.gameState.gameTime += deltaTime;

        // Update flag positions
        this.updateFlags(game, deltaTime);

        // Process flag captures
        this.processFlagCaptures(game, deltaTime);

        // Process flag returns
        this.processFlagReturns(game, deltaTime);

        // Process respawns
        this.processRespawns(game, deltaTime);

        // Process power-ups
        if (game.settings.powerUps) {
            this.processPowerUps(game, deltaTime);
        }

        // Update game state
        this.updateGameState(game);

        // Check for sudden death
        this.checkSuddenDeath(game);

        // Generate game events
        this.generateGameEvents(game);
    }

    checkWinCondition(game) {
        const settings = game.settings;

        // Check capture limit
        if (game.gameState.captures.team1 >= settings.captureLimit) {
            return {
                type: 'capture_limit_reached',
                winner: 'team1',
                description: 'Blue Team captured the flag enough times to win!',
                stats: {
                    finalCaptures: game.gameState.captures.team1,
                    gameTime: game.gameState.gameTime
                }
            };
        }

        if (game.gameState.captures.team2 >= settings.captureLimit) {
            return {
                type: 'capture_limit_reached',
                winner: 'team2',
                description: 'Red Team captured the flag enough times to win!',
                stats: {
                    finalCaptures: game.gameState.captures.team2,
                    gameTime: game.gameState.gameTime
                }
            };
        }

        // Check time limit
        if (game.gameState.gameTime >= settings.timeLimit) {
            const winner = game.gameState.captures.team1 > game.gameState.captures.team2 ? 'team1' :
                          game.gameState.captures.team2 > game.gameState.captures.team1 ? 'team2' : null;

            return {
                type: 'time_limit_reached',
                winner: winner,
                description: winner ? `${winner === 'team1' ? 'Blue' : 'Red'} Team wins by captures!` : 'The match ends in a draw!',
                stats: {
                    finalCaptures: game.gameState.captures,
                    gameTime: game.gameState.gameTime
                }
            };
        }

        return null;
    }

    finalize(game, result) {
        // Calculate final statistics
        this.calculateFinalStatistics(game);

        // Determine MVPs for each team
        game.mvp = this.determineMVPs(game);

        // Generate highlights
        game.highlights = this.generateHighlights(game);
    }

    updateFlags(game, deltaTime) {
        Object.values(game.flags).forEach(flag => {
            if (flag.carrier) {
                // Update flag position to carrier position
                const carrier = game.players.find(p => p.id === flag.carrier);
                if (carrier) {
                    flag.position = {
                        x: carrier.position.x,
                        y: carrier.position.y + 2,
                        z: carrier.position.z
                    };
                } else {
                    // Carrier disconnected or died, drop flag
                    this.dropFlag(game, flag);
                }
            } else if (!flag.isHome && flag.dropTime) {
                // Check if flag should return home
                flag.dropTime -= deltaTime;
                if (flag.dropTime <= 0) {
                    this.returnFlagHome(game, flag);
                }
            }
        });
    }

    processFlagCaptures(game, deltaTime) {
        game.players.forEach(player => {
            if (player.hasEnemyFlag) {
                // Check if player is at their base with enemy flag
                const team = game.teams.get(player.teamId);
                const enemyFlag = game.flags[player.teamId === 'team1' ? 'team2' : 'team1'];

                const distanceToBase = this.calculateDistance(player.position, team.base.position);
                if (distanceToBase <= team.base.radius) {
                    // Check if team flag is home
                    const teamFlag = game.flags[player.teamId];
                    if (teamFlag.isHome) {
                        this.captureFlag(game, player, enemyFlag);
                    }
                }
            }
        });
    }

    processFlagReturns(game, deltaTime) {
        Object.values(game.flags).forEach(flag => {
            if (!flag.isHome && !flag.carrier) {
                // Check if friendly player is near dropped flag
                game.players.forEach(player => {
                    if (player.teamId === flag.teamId) {
                        const distance = this.calculateDistance(player.position, flag.position);
                        if (distance <= flag.pickupRadius) {
                            this.returnFlagToPlayer(game, flag, player);
                        }
                    }
                });
            }
        });
    }

    captureFlag(game, player, flag) {
        const scoringTeam = game.teams.get(player.teamId);
        const enemyTeam = game.teams.get(flag.teamId);

        // Update captures
        game.gameState.captures[player.teamId]++;
        scoringTeam.score = game.gameState.captures[player.teamId];

        // Update player stats
        player.stats.flagCaptures++;
        player.score += 100;

        // Return flags
        this.returnFlagHome(game, flag);
        const teamFlag = game.flags[player.teamId];
        this.returnFlagHome(game, teamFlag);

        // Clear player flag status
        player.hasEnemyFlag = false;
        player.isCarryingFlag = false;

        // Update game state
        game.gameState.lastCaptureTime = Date.now();

        // Emit capture event
        this.emitGameEvent(game, {
            type: 'flag_captured',
            playerId: player.id,
            playerName: player.name,
            teamId: player.teamId,
            captures: game.gameState.captures[player.teamId],
            description: `${player.name} captured the flag!`
        });
    }

    dropFlag(game, flag) {
        if (!flag.carrier) return;

        const carrier = game.players.find(p => p.id === flag.carrier);
        if (carrier) {
            carrier.hasEnemyFlag = false;
            carrier.isCarryingFlag = false;
        }

        flag.carrier = null;
        flag.dropTime = flag.returnTime * 1000; // Convert to milliseconds

        this.emitGameEvent(game, {
            type: 'flag_dropped',
            flagId: flag.id,
            teamId: flag.teamId,
            position: flag.position,
            description: `${flag.teamId === 'team1' ? 'Blue' : 'Red'} flag dropped!`
        });
    }

    returnFlagHome(game, flag) {
        flag.position = { ...flag.homePosition };
        flag.isHome = true;
        flag.carrier = null;
        flag.dropTime = null;

        this.emitGameEvent(game, {
            type: 'flag_returned',
            flagId: flag.id,
            teamId: flag.teamId,
            description: `${flag.teamId === 'team1' ? 'Blue' : 'Red'} flag returned!`
        });
    }

    returnFlagToPlayer(game, flag, player) {
        flag.position = { ...flag.homePosition };
        flag.isHome = true;
        flag.dropTime = null;

        // Update player stats
        player.stats.flagReturns++;
        player.score += 25;

        this.emitGameEvent(game, {
            type: 'flag_returned_by_player',
            playerId: player.id,
            playerName: player.name,
            flagId: flag.id,
            teamId: flag.teamId,
            description: `${player.name} returned the flag!`
        });
    }

    calculatePlayerPlacement(player, game, winCondition) {
        // Team-based placement - all players on winning team get top placement
        if (winCondition.winner === player.teamId) {
            return 1;
        } else if (winCondition.winner) {
            return game.teams.get(winCondition).players.length + 1;
        } else {
            // Draw - all players get same placement
            return 1;
        }
    }

    calculatePlayerScore(player, game) {
        let score = 0;

        // Combat points
        score += player.stats.kills * 10;
        score += player.stats.assists * 5;
        score -= player.stats.deaths * 3;

        // Objective points
        score += player.stats.flagCaptures * 100;
        score += player.stats.flagReturns * 25;
        score += player.stats.flagCarrierKills * 30;
        score += player.stats.defenseKills * 15;

        // Support points
        score += player.stats.healingDone * 0.5;
        score += player.stats.damageDealt * 0.1;

        return Math.max(0, score);
    }

    calculatePlayerRewards(player, game, winCondition) {
        const baseRewards = super.calculatePlayerRewards(player, game, winCondition);

        // CTF-specific reward calculations
        const isWinner = winCondition.winner === player.teamId;
        const winnerMultiplier = isWinner ? 2.0 : 1.0;

        baseRewards.xp = Math.floor(baseRewards.xp * winnerMultiplier);
        baseRewards.gold = Math.floor(baseRewards.gold * winnerMultiplier);

        // Objective bonuses
        if (player.stats.flagCaptures > 0) {
            baseRewards.xp += player.stats.flagCaptures * 150;
            baseRewards.gold += player.stats.flagCaptures * 75;
        }

        if (player.stats.flagReturns > 2) {
            baseRewards.xp += 100;
            baseRewards.gold += 50;
        }

        return baseRewards;
    }

    updateGameState(game) {
        // Update leading team
        if (game.gameState.captures.team1 > game.gameState.captures.team2) {
            game.gameState.leadingTeam = 'team1';
        } else if (game.gameState.captures.team2 > game.gameState.captures.team1) {
            game.gameState.leadingTeam = 'team2';
        } else {
            game.gameState.leadingTeam = null;
        }
    }

    checkSuddenDeath(game) {
        const timeRemaining = game.settings.timeLimit - game.gameState.gameTime;
        if (timeRemaining <= 60 && !game.gameState.suddenDeath) {
            game.gameState.suddenDeath = true;
            this.emitGameEvent(game, {
                type: 'sudden_death',
                description: 'Sudden Death! Next capture wins!'
            });
        }
    }

    generateGameEvents(game) {
        // Check for close captures
        Object.values(game.flags).forEach(flag => {
            if (flag.carrier) {
                const carrier = game.players.find(p => p.id === flag.carrier);
                if (carrier) {
                    const enemyTeam = game.teams.get(flag.teamId);
                    const distanceToEnemyBase = this.calculateDistance(carrier.position, enemyTeam.base.position);

                    if (distanceToEnemyBase <= 15) {
                        this.emitGameEvent(game, {
                            type: 'close_capture',
                            playerId: carrier.id,
                            playerName: carrier.name,
                            teamId: carrier.teamId,
                            description: `${carrier.name} is approaching the enemy base!`
                        });
                    }
                }
            }
        });
    }

    emitGameEvent(game, event) {
        event.timestamp = Date.now();
        game.events.push(event);

        if (game.events.length > 100) {
            game.events.shift();
        }
    }

    calculateFinalStatistics(game) {
        game.players.forEach(player => {
            player.stats.kda = player.stats.deaths > 0 ?
                (player.stats.kills + player.stats.assists * 0.5) / player.stats.deaths :
                player.stats.kills;

            player.stats.objectiveScore = player.stats.flagCaptures * 100 +
                                         player.stats.flagReturns * 25 +
                                         player.stats.flagCarrierKills * 30;
        });
    }

    determineMVPs(game) {
        const mvps = {};

        game.teams.forEach((team, teamId) => {
            const teamMVP = team.players.reduce((mvp, player) => {
                if (!mvp || player.score > mvp.score) {
                    return player;
                }
                return mvp;
            }, null);

            if (teamMVP) {
                mvps[teamId] = teamMVP;
            }
        });

        return mvps;
    }

    generateHighlights(game) {
        const highlights = [];

        // Flag capture highlights
        game.events.filter(event => event.type === 'flag_captured').forEach(capture => {
            highlights.push({
                type: 'flag_capture',
                description: capture.description,
                importance: 'high',
                timestamp: capture.timestamp
            });
        });

        // Find players with high flag capture counts
        game.players.forEach(player => {
            if (player.stats.flagCaptures >= 2) {
                highlights.push({
                    type: 'objective_master',
                    description: `${player.name} captured ${player.stats.flagCaptures} flags!`,
                    importance: 'medium'
                });
            }
        });

        return highlights;
    }

    getAvailableMaps() {
        return [
            'ctf_valley',
            'twin_forts',
            'dagger_pass',
            'sandy_basin',
            'stone_bridge'
        ];
    }

    getRulePresets() {
        return {
            'quick_ctf': {
                captureLimit: 2,
                timeLimit: 600,
                respawnTime: 5,
                powerUps: false
            },
            'standard_ctf': {
                captureLimit: 3,
                timeLimit: 900,
                respawnTime: 8,
                powerUps: true
            },
            'pro_ctf': {
                captureLimit: 5,
                timeLimit: 1200,
                respawnTime: 10,
                powerUps: true,
                classRestrictions: true
            },
            'chaos_ctf': {
                captureLimit: 10,
                timeLimit: 900,
                respawnTime: 3,
                powerUps: true,
                friendlyFire: true
            }
        };
    }

    processRespawns(game, deltaTime) {
        game.players.forEach(player => {
            if (player.isDead && player.respawnTimer) {
                player.respawnTimer -= deltaTime;

                if (player.respawnTimer <= 0) {
                    this.respawnPlayer(player, game);
                }
            }
        });
    }

    respawnPlayer(player, game) {
        const team = game.teams.get(player.teamId);
        const spawnPoints = game.spawnPoints[player.teamId];

        // Find safe spawn point
        const safeSpawn = this.findSafeSpawnPoint(spawnPoints, player, game);
        player.position = { ...safeSpawn };
        player.respawnPosition = { ...safeSpawn };

        // Reset player state
        player.isDead = false;
        player.currentHealth = player.maxHealth;
        player.currentMana = player.maxMana;
        player.respawnTimer = null;

        // Clear flag status if carrying
        if (player.hasEnemyFlag) {
            const enemyFlag = game.flags[player.teamId === 'team1' ? 'team2' : 'team1'];
            this.dropFlag(game, enemyFlag);
        }

        // Clear negative status effects
        player.statusEffects = player.statusEffects.filter(effect => !effect.negative);

        this.emitGameEvent(game, {
            type: 'player_respawned',
            playerId: player.id,
            playerName: player.name,
            teamId: player.teamId,
            position: safeSpawn
        });
    }

    findSafeSpawnPoint(spawnPoints, player, game) {
        let safestSpawn = spawnPoints[0];
        let minEnemyDistance = 0;

        spawnPoints.forEach(spawn => {
            let totalEnemyDistance = 0;

            game.players.forEach(otherPlayer => {
                if (otherPlayer.teamId !== player.teamId && !otherPlayer.isDead) {
                    const distance = this.calculateDistance(spawn, otherPlayer.position);
                    totalEnemyDistance += distance;
                }
            });

            if (totalEnemyDistance > minEnemyDistance) {
                minEnemyDistance = totalEnemyDistance;
                safestSpawn = spawn;
            }
        });

        return safestSpawn;
    }

    processPowerUps(game, deltaTime) {
        // Similar to deathmatch power-up processing
        // Implementation would be very similar to DeathmatchMode
    }

    calculateDistance(pos1, pos2) {
        return Math.sqrt(
            Math.pow(pos1.x - pos2.x, 2) +
            Math.pow(pos1.y - pos2.y, 2) +
            Math.pow(pos1.z - pos2.z, 2)
        );
    }
}

module.exports = CaptureTheFlagMode;