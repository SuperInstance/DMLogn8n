/**
 * Deathmatch Game Mode - Classic combat-focused gameplay
 */

const BaseGameMode = require('./GameModeManager').BaseGameMode;

class DeathmatchMode extends BaseGameMode {
    constructor() {
        super({
            id: 'deathmatch',
            name: 'Deathmatch',
            description: 'Classic free-for-all combat. First to reach the kill limit wins!',
            minPlayers: 2,
            maxPlayers: 16,
            estimatedDuration: 600, // 10 minutes
            complexity: 'low',
            tags: ['combat', 'free_for_all', 'classic'],
            supportsCustomRules: true,
            defaultMap: 'arena_deathmatch'
        });

        // Default deathmatch settings
        this.defaultSettings = {
            killLimit: 20,
            timeLimit: 600, // 10 minutes
            respawnTime: 5,
            weaponPickups: true,
            powerUps: true,
            friendlyFire: false,
            scoreAssists: true
        };
    }

    initialize(game) {
        // Apply game mode settings
        game.settings = { ...this.defaultSettings, ...game.config };

        // Initialize game state
        game.gameState = {
            leadingPlayer: null,
            killLeader: null,
            highestKillStreak: 0,
            totalKills: 0,
            gameTime: 0,
            roundNumber: 1,
            inOvertime: false
        };

        // Initialize player scores
        game.players.forEach(player => {
            player.score = 0;
            player.killStreak = 0;
            player.deathStreak = 0;
            player.stats = {
                kills: 0,
                deaths: 0,
                assists: 0,
                damageDealt: 0,
                damageReceived: 0,
                healingDone: 0,
                objectives: 0
            };
        });

        // Set up spawn points
        this.setupSpawnPoints(game);

        // Set up weapon pickups if enabled
        if (game.settings.weaponPickups) {
            this.setupWeaponPickups(game);
        }

        // Set up power-ups if enabled
        if (game.settings.powerUps) {
            this.setupPowerUps(game);
        }
    }

    processTick(game, deltaTime) {
        game.gameState.gameTime += deltaTime;

        // Update kill leader
        this.updateKillLeader(game);

        // Process respawns
        this.processRespawns(game, deltaTime);

        // Process weapon pickups
        if (game.settings.weaponPickups) {
            this.processWeaponPickups(game, deltaTime);
        }

        // Process power-ups
        if (game.settings.powerUps) {
            this.processPowerUps(game, deltaTime);
        }

        // Check for overtime
        this.checkOvertime(game);

        // Generate game events
        this.generateGameEvents(game);
    }

    checkWinCondition(game) {
        const settings = game.settings;

        // Check kill limit
        const killLeader = this.getKillLeader(game);
        if (killLeader && killLeader.stats.kills >= settings.killLimit) {
            return {
                type: 'kill_limit_reached',
                winner: killLeader.id,
                description: `${killLeader.name} reached ${settings.killLimit} kills!`,
                stats: {
                    finalKills: killLeader.stats.kills,
                    gameTime: game.gameState.gameTime
                }
            };
        }

        // Check time limit
        if (game.gameState.gameTime >= settings.timeLimit) {
            const winner = this.getWinnerByScore(game);
            return {
                type: 'time_limit_reached',
                winner: winner.id,
                description: `Time's up! ${winner.name} wins with ${winner.score} points!`,
                stats: {
                    finalScore: winner.score,
                    gameTime: game.gameState.gameTime
                }
            };
        }

        return null;
    }

    finalize(game, result) {
        // Calculate final statistics
        this.calculateFinalStatistics(game);

        // Determine MVP
        const mvp = this.determineMVP(game);
        game.mvp = mvp;

        // Generate highlights
        game.highlights = this.generateHighlights(game);
    }

    calculatePlayerPlacement(player, game, winCondition) {
        // Sort players by score, then by kills, then by assists
        const sortedPlayers = [...game.players].sort((a, b) => {
            if (b.score !== a.score) return b.score - a.score;
            if (b.stats.kills !== a.stats.kills) return b.stats.kills - a.stats.kills;
            return b.stats.assists - a.stats.assists;
        });

        return sortedPlayers.findIndex(p => p.id === player.id) + 1;
    }

    calculatePlayerScore(player, game) {
        const baseScore = super.calculatePlayerScore(player, game);

        // Deathmatch-specific scoring
        let deathmatchScore = baseScore;

        // Kill streak bonuses
        if (player.killStreak >= 3) deathmatchScore += player.killStreak * 5;
        if (player.killStreak >= 5) deathmatchScore += 50; // Dominating
        if (player.killStreak >= 10) deathmatchScore += 100; // Unstoppable

        // First blood bonus
        if (game.gameState.totalKills === 1 && player.stats.kills === 1) {
            deathmatchScore += 25;
        }

        // Revenge bonus (killing someone who killed you recently)
        // This would require tracking recent deaths

        return Math.max(0, deathmatchScore);
    }

    calculatePlayerRewards(player, game, winCondition) {
        const baseRewards = super.calculatePlayerRewards(player, game, winCondition);

        // Deathmatch-specific reward calculations
        const placement = this.calculatePlayerPlacement(player, game, winCondition);
        const placementMultiplier = this.getPlacementMultiplier(placement);

        baseRewards.xp = Math.floor(baseRewards.xp * placementMultiplier);
        baseRewards.gold = Math.floor(baseRewards.gold * placementMultiplier);

        // Performance bonuses
        if (player.stats.kills >= 20) {
            baseRewards.xp += 200;
            baseRewards.gold += 100;
        }

        if (player.killStreak >= 10) {
            baseRewards.xp += 150;
            baseRewards.gold += 75;
        }

        return baseRewards;
    }

    getPlacementMultiplier(placement) {
        const multipliers = {
            1: 3.0,
            2: 2.0,
            3: 1.5,
            4: 1.2,
            5: 1.0
        };

        return multipliers[placement] || 0.8;
    }

    // Helper methods
    setupSpawnPoints(game) {
        // Generate spawn points based on map
        game.spawnPoints = [
            { x: -20, y: 0, z: -20 },
            { x: 20, y: 0, z: -20 },
            { x: -20, y: 0, z: 20 },
            { x: 20, y: 0, z: 20 },
            { x: 0, y: 0, z: -30 },
            { x: 0, y: 0, z: 30 },
            { x: -30, y: 0, z: 0 },
            { x: 30, y: 0, z: 0 }
        ];

        // Assign initial spawn positions
        game.players.forEach((player, index) => {
            const spawnPoint = game.spawnPoints[index % game.spawnPoints.length];
            player.position = { ...spawnPoint };
            player.respawnPosition = { ...spawnPoint };
        });
    }

    setupWeaponPickups(game) {
        game.weaponPickups = [
            { id: 'pickup_sword_1', type: 'sword', position: { x: 0, y: 0, z: 0 }, respawnTime: 30 },
            { id: 'pickup_bow_1', type: 'bow', position: { x: 10, y: 0, z: 10 }, respawnTime: 45 },
            { id: 'pickup_staff_1', type: 'staff', position: { x: -10, y: 0, z: -10 }, respawnTime: 45 },
            { id: 'pickup_shield_1', type: 'shield', position: { x: 15, y: 0, z: -15 }, respawnTime: 60 }
        ];
    }

    setupPowerUps(game) {
        game.powerUps = [
            { id: 'powerup_speed_1', type: 'speed_boost', position: { x: 5, y: 0, z: 5 }, duration: 10, respawnTime: 90 },
            { id: 'powerup_damage_1', type: 'damage_boost', position: { x: -5, y: 0, z: 5 }, duration: 15, respawnTime: 120 },
            { id: 'powerup_health_1', type: 'health_restore', position: { x: 0, y: 0, z: -10 }, respawnTime: 60 }
        ];
    }

    updateKillLeader(game) {
        const killLeader = this.getKillLeader(game);
        if (killLeader !== game.gameState.killLeader) {
            game.gameState.killLeader = killLeader;
            if (killLeader) {
                this.emitGameEvent(game, {
                    type: 'new_kill_leader',
                    playerId: killLeader.id,
                    playerName: killLeader.name,
                    kills: killLeader.stats.kills
                });
            }
        }
    }

    getKillLeader(game) {
        return game.players.reduce((leader, player) => {
            if (!leader || player.stats.kills > leader.stats.kills) {
                return player;
            }
            return leader;
        }, null);
    }

    getWinnerByScore(game) {
        return game.players.reduce((winner, player) => {
            if (!winner || player.score > winner.score) {
                return player;
            }
            return winner;
        }, null);
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
        // Find safe spawn point
        const safeSpawn = this.findSafeSpawnPoint(player, game);
        player.position = { ...safeSpawn };
        player.respawnPosition = { ...safeSpawn };

        // Reset player state
        player.isDead = false;
        player.currentHealth = player.maxHealth;
        player.currentMana = player.maxMana;
        player.respawnTimer = null;

        // Clear negative status effects
        player.statusEffects = player.statusEffects.filter(effect => !effect.negative);

        this.emitGameEvent(game, {
            type: 'player_respawned',
            playerId: player.id,
            playerName: player.name,
            position: safeSpawn
        });
    }

    findSafeSpawnPoint(player, game) {
        // Find spawn point farthest from enemies
        let safestSpawn = game.spawnPoints[0];
        let maxDistance = 0;

        game.spawnPoints.forEach(spawn => {
            let minEnemyDistance = Infinity;

            game.players.forEach(otherPlayer => {
                if (otherPlayer.id !== player.id && !otherPlayer.isDead) {
                    const distance = this.calculateDistance(spawn, otherPlayer.position);
                    minEnemyDistance = Math.min(minEnemyDistance, distance);
                }
            });

            if (minEnemyDistance > maxDistance) {
                maxDistance = minEnemyDistance;
                safestSpawn = spawn;
            }
        });

        return safestSpawn;
    }

    processWeaponPickups(game, deltaTime) {
        game.weaponPickups.forEach(pickup => {
            if (!pickup.available) {
                pickup.respawnTimer -= deltaTime;
                if (pickup.respawnTimer <= 0) {
                    pickup.available = true;
                    this.emitGameEvent(game, {
                        type: 'weapon_pickup_spawned',
                        pickupId: pickup.id,
                        type: pickup.type,
                        position: pickup.position
                    });
                }
            }
        });
    }

    processPowerUps(game, deltaTime) {
        game.powerUps.forEach(powerUp => {
            if (!powerUp.available) {
                powerUp.respawnTimer -= deltaTime;
                if (powerUp.respawnTimer <= 0) {
                    powerUp.available = true;
                    this.emitGameEvent(game, {
                        type: 'powerup_spawned',
                        powerUpId: powerUp.id,
                        type: powerUp.type,
                        position: powerUp.position
                    });
                }
            }
        });

        // Process active power-up effects on players
        game.players.forEach(player => {
            if (player.activePowerUps) {
                player.activePowerUps.forEach(powerUp => {
                    powerUp.remainingTime -= deltaTime;
                    if (powerUp.remainingTime <= 0) {
                        this.removePowerUpEffect(player, powerUp);
                    }
                });
                player.activePowerUps = player.activePowerUps.filter(p => p.remainingTime > 0);
            }
        });
    }

    checkOvertime(game) {
        if (game.gameState.gameTime >= game.settings.timeLimit && !game.gameState.inOvertime) {
            game.gameState.inOvertime = true;
            this.emitGameEvent(game, {
                type: 'overtime_started',
                description: 'Overtime! First to score wins!'
            });
        }
    }

    generateGameEvents(game) {
        // Generate periodic events like kill streaks, etc.
        game.players.forEach(player => {
            if (player.killStreak === 5 && !player.announcedStreaks?.includes(5)) {
                this.emitGameEvent(game, {
                    type: 'kill_streak',
                    playerId: player.id,
                    playerName: player.name,
                    streak: 5,
                    description: `${player.name} is on a 5-kill streak!`
                });
                player.announcedStreaks = player.announcedStreaks || [];
                player.announcedStreaks.push(5);
            }

            if (player.killStreak === 10 && !player.announcedStreaks?.includes(10)) {
                this.emitGameEvent(game, {
                    type: 'kill_streak',
                    playerId: player.id,
                    playerName: player.name,
                    streak: 10,
                    description: `${player.name} is UNSTOPPABLE with a 10-kill streak!`
                });
                player.announcedStreaks = player.announcedStreaks || [];
                player.announcedStreaks.push(10);
            }
        });
    }

    emitGameEvent(game, event) {
        event.timestamp = Date.now();
        game.events.push(event);

        // Keep events manageable
        if (game.events.length > 100) {
            game.events.shift();
        }
    }

    calculateFinalStatistics(game) {
        // Calculate additional final statistics
        game.players.forEach(player => {
            player.stats.kda = player.stats.deaths > 0 ?
                (player.stats.kills + player.stats.assists * 0.5) / player.stats.deaths :
                player.stats.kills;

            player.stats.averageDamagePerKill = player.stats.kills > 0 ?
                player.stats.damageDealt / player.stats.kills : 0;
        });
    }

    determineMVP(game) {
        return game.players.reduce((mvp, player) => {
            if (!mvp || player.score > mvp.score) {
                return player;
            }
            return mvp;
        }, null);
    }

    generateHighlights(game) {
        const highlights = [];

        // Find longest kill streak
        const longestStreak = game.players.reduce((longest, player) => {
            return !longest || player.killStreak > longest.streak ?
                { player: player.name, streak: player.killStreak } : longest;
        }, { player: null, streak: 0 });

        if (longestStreak.streak >= 5) {
            highlights.push({
                type: 'kill_streak',
                description: `${longestStreak.player} achieved a ${longestStreak.streak}-kill streak!`,
                importance: longestStreak.streak >= 10 ? 'high' : 'medium'
            });
        }

        // Find highest damage dealer
        const highestDamage = game.players.reduce((highest, player) => {
            return !highest || player.stats.damageDealt > highest.damage ?
                { player: player.name, damage: player.stats.damageDealt } : highest;
        }, { player: null, damage: 0 });

        if (highestDamage.damage > 2000) {
            highlights.push({
                type: 'damage_dealer',
                description: `${highestDamage.player} dealt ${highestDamage.damage} total damage!`,
                importance: 'medium'
            });
        }

        return highlights;
    }

    getAvailableMaps() {
        return [
            'arena_deathmatch',
            'coliseum_classic',
            'chaos_pit',
            'sky_bridge',
            'underground_caverns'
        ];
    }

    getRulePresets() {
        return {
            'quick_play': {
                killLimit: 10,
                timeLimit: 300,
                respawnTime: 3,
                powerUps: false
            },
            'standard': {
                killLimit: 20,
                timeLimit: 600,
                respawnTime: 5,
                powerUps: true
            },
            'extended': {
                killLimit: 50,
                timeLimit: 1200,
                respawnTime: 8,
                powerUps: true,
                weaponPickups: true
            },
            'instagib': {
                killLimit: 30,
                timeLimit: 300,
                respawnTime: 1,
                weaponPickups: false,
                startingWeapon: 'instagib_rifle',
                oneHitKills: true
            }
        };
    }

    calculateDistance(pos1, pos2) {
        return Math.sqrt(
            Math.pow(pos1.x - pos2.x, 2) +
            Math.pow(pos1.y - pos2.y, 2) +
            Math.pow(pos1.z - pos2.z, 2)
        );
    }

    removePowerUpEffect(player, powerUp) {
        // Remove power-up effects from player
        switch (powerUp.type) {
            case 'speed_boost':
                player.speedMultiplier = 1.0;
                break;
            case 'damage_boost':
                player.damageMultiplier = 1.0;
                break;
        }
    }
}

module.exports = DeathmatchMode;