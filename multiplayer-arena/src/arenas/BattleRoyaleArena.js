/**
 * Battle Royale Arena - Free-for-all survival competition
 */

const BaseArena = require('../core/ArenaSystem').BaseArena;

class BattleRoyaleArena extends BaseArena {
    constructor(id, config = {}) {
        super(id, config);
        this.type = 'battle_royale';
        this.name = 'Royal Rumble';
        this.description = 'Last player standing in a shrinking arena';

        // Battle Royale specific settings
        this.minPlayers = 10;
        this.maxPlayers = 50;

        this.brSettings = {
            maxPlayers: config.maxPlayers || 20,
            shrinkingZone: {
                enabled: true,
                initialRadius: 100,
                finalRadius: 10,
                shrinkDuration: 600, // 10 minutes
                damagePerSecond: 10
            },
            lootSystem: {
                enabled: true,
                rarity: ['common', 'uncommon', 'rare', 'epic', 'legendary'],
                dropRate: 0.3,
                supplyDrops: true,
                supplyDropInterval: 120 // seconds
            },
            respawn: {
                enabled: false,
                spectateMode: true
            },
            storm: {
                damage: 15,
                movementSpeed: 0.5
            }
        };

        // Player states
        this.playerStates = new Map();
        this.zonePosition = { x: 0, y: 0, z: 0 };
        this.zoneRadius = this.brSettings.shrinkingZone.initialRadius;
        this.shrinkStartTime = null;
        this.supplyDropSchedule = [];
    }

    validatePlayers(players) {
        if (!super.validatePlayers(players)) return false;

        // Battle Royale requires minimum players for good experience
        if (players.length < 10) {
            return false;
        }

        // Check for character variety (avoid too many of same class)
        return this.hasGoodClassVariety(players);
    }

    hasGoodClassVariety(players) {
        const classCount = {};

        players.forEach(player => {
            const cls = player.character.class.toLowerCase();
            classCount[cls] = (classCount[cls] || 0) + 1;
        });

        // No class should be more than 30% of total players
        const maxAllowed = Math.floor(players.length * 0.3);
        return Object.values(classCount).every(count => count <= maxAllowed);
    }

    setupEnvironment() {
        // Generate large, diverse battlefield
        this.environment = {
            type: 'battlefield',
            size: 'massive',
            terrain: this.generateTerrain(),
            pointsOfInterest: this.generatePointsOfInterest(),
            lootContainers: this.generateLootContainers(),
            spawnPoints: this.generateSpawnPoints(),
            boundaries: {
                shape: 'circle',
                initialRadius: this.brSettings.shrinkingZone.initialRadius,
                currentRadius: this.zoneRadius
            }
        };

        // Initialize player states
        this.initializePlayerStates();

        // Start zone shrinking timer
        this.startZoneShrinking();

        // Schedule supply drops
        this.scheduleSupplyDrops();
    }

    generateTerrain() {
        const terrainTypes = ['plains', 'forest', 'hills', 'mountains', 'swamp', 'ruins'];
        const terrain = [];

        // Generate 9 terrain sectors (3x3 grid)
        for (let i = 0; i < 3; i++) {
            for (let j = 0; j < 3; j++) {
                terrain.push({
                    id: `sector_${i}_${j}`,
                    type: terrainTypes[Math.floor(Math.random() * terrainTypes.length)],
                    position: {
                        x: (i - 1) * 60,
                        z: (j - 1) * 60
                    },
                    size: 50,
                    cover: Math.random() * 0.7 + 0.3,
                    obstacles: this.generateTerrainObstacles()
                });
            }
        }

        return terrain;
    }

    generateTerrainObstacles() {
        const obstacles = [];
        const obstacleCount = Math.floor(Math.random() * 5) + 3;

        for (let i = 0; i < obstacleCount; i++) {
            obstacles.push({
                type: ['tree', 'rock', 'building', 'wall'][Math.floor(Math.random() * 4)],
                position: {
                    x: Math.random() * 40 - 20,
                    z: Math.random() * 40 - 20
                },
                size: Math.random() * 3 + 1,
                cover: Math.random() * 0.5 + 0.5
            });
        }

        return obstacles;
    }

    generatePointsOfInterest() {
        const poiTypes = ['town', 'fortress', 'temple', 'cave', 'tower', 'camp'];
        const poi = [];

        // Generate 6-8 points of interest
        const poiCount = Math.floor(Math.random() * 3) + 6;
        const usedPositions = [];

        for (let i = 0; i < poiCount; i++) {
            let position;
            do {
                position = {
                    x: Math.random() * 160 - 80,
                    z: Math.random() * 160 - 80
                };
            } while (this.isTooCloseToExisting(position, usedPositions, 20));

            usedPositions.push(position);

            poi.push({
                id: `poi_${i}`,
                name: `${poiTypes[Math.floor(Math.random() * poiTypes.length)]}_${i}`,
                type: poiTypes[Math.floor(Math.random() * poiTypes.length)],
                position: position,
                lootTier: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)],
                description: `Point of interest with ${Math.floor(Math.random() * 5) + 2} loot containers`
            });
        }

        return poi;
    }

    generateLootContainers() {
        const containers = [];
        const containerTypes = ['chest', 'barrel', 'crate', 'corpse'];

        this.environment.pointsOfInterest.forEach(poi => {
            const containerCount = Math.floor(Math.random() * 5) + 2;

            for (let i = 0; i < containerCount; i++) {
                containers.push({
                    id: `container_${poi.id}_${i}`,
                    type: containerTypes[Math.floor(Math.random() * containerTypes.length)],
                    position: {
                        x: poi.position.x + Math.random() * 20 - 10,
                        z: poi.position.z + Math.random() * 20 - 10
                    },
                    lootTable: this.getLootTable(poi.lootTier),
                    opened: false
                });
            }
        });

        return containers;
    }

    getLootTable(tier) {
        const lootTables = {
            low: {
                weapons: ['dagger', 'club', 'sling'],
                armor: ['leather', 'padded'],
                potions: ['minor_healing'],
                gold: { min: 10, max: 50 }
            },
            medium: {
                weapons: ['shortsword', 'longbow', 'handaxe'],
                armor: ['chain_shirt', 'scale_mail'],
                potions: ['healing', 'minor_stamina'],
                gold: { min: 50, max: 200 }
            },
            high: {
                weapons: ['longsword', 'greatsword', 'warhammer'],
                armor: ['plate', 'breastplate'],
                potions: ['greater_healing', 'stamina', 'invisibility'],
                gold: { min: 200, max: 1000 }
            }
        };

        return lootTables[tier] || lootTables.medium;
    }

    generateSpawnPoints() {
        const spawnPoints = [];
        const angleStep = (2 * Math.PI) / this.maxPlayers;
        const spawnRadius = this.zoneRadius - 10;

        for (let i = 0; i < this.maxPlayers; i++) {
            const angle = i * angleStep + (Math.random() * 0.5 - 0.25);
            spawnPoints.push({
                id: `spawn_${i}`,
                position: {
                    x: Math.cos(angle) * spawnRadius,
                    y: 0,
                    z: Math.sin(angle) * spawnRadius
                }
            });
        }

        return spawnPoints;
    }

    initializePlayerStates() {
        const session = this.currentSession;

        session.players.forEach((player, index) => {
            const spawnPoint = this.environment.spawnPoints[index];

            this.playerStates.set(player.id, {
                alive: true,
                position: spawnPoint.position,
                inventory: this.generateStartingInventory(),
                kills: 0,
                damageDealt: 0,
                distanceTraveled: 0,
                timeInZone: 0,
                statusEffects: []
            });

            player.position = spawnPoint.position;
            player.inventory = this.playerStates.get(player.id).inventory;
        });
    }

    generateStartingInventory() {
        return {
            weapons: ['dagger'],
            armor: ['clothing'],
            potions: ['minor_healing'],
            gold: 50,
            spells: [],
            equipment: []
        };
    }

    startZoneShrinking() {
        this.shrinkStartTime = Date.now();

        // Set up zone shrink interval
        this.zoneShrinkInterval = setInterval(() => {
            this.updateZone();
        }, 1000);
    }

    updateZone() {
        if (!this.shrinkStartTime) return;

        const elapsed = (Date.now() - this.shrinkStartTime) / 1000;
        const shrinkDuration = this.brSettings.shrinkingZone.shrinkDuration;
        const initialRadius = this.brSettings.shrinkingZone.initialRadius;
        const finalRadius = this.brSettings.shrinkingZone.finalRadius;

        if (elapsed >= shrinkDuration) {
            this.zoneRadius = finalRadius;
            clearInterval(this.zoneShrinkInterval);
        } else {
            const progress = elapsed / shrinkDuration;
            this.zoneRadius = initialRadius - (initialRadius - finalRadius) * progress;
        }

        // Update environment boundaries
        this.environment.boundaries.currentRadius = this.zoneRadius;

        // Check players outside zone
        this.checkPlayersInZone();
    }

    checkPlayersInZone() {
        const session = this.currentSession;

        session.players.forEach(player => {
            const state = this.playerStates.get(player.id);
            if (!state.alive) return;

            const distance = Math.sqrt(
                Math.pow(player.position.x - this.zonePosition.x, 2) +
                Math.pow(player.position.z - this.zonePosition.z, 2)
            );

            if (distance > this.zoneRadius) {
                // Player is outside the zone
                this.damagePlayerInStorm(player);
            }
        });
    }

    damagePlayerInStorm(player) {
        const damage = this.brSettings.storm.damage;

        // Apply storm damage
        player.currentHealth = Math.max(0, player.currentHealth - damage);

        // Update player state
        const state = this.playerStates.get(player.id);
        state.statusEffects.push({
            type: 'storm',
            damage: damage,
            duration: 1
        });

        // Check if player died
        if (player.currentHealth <= 0) {
            this.eliminatePlayer(player);
        }
    }

    eliminatePlayer(player) {
        const state = this.playerStates.get(player.id);
        state.alive = false;

        // Drop player's inventory
        if (this.brSettings.lootSystem.enabled) {
            this.dropPlayerInventory(player);
        }

        // Notify elimination
        this.onPlayerEliminated(player);

        // Check win condition
        this.checkWinCondition();
    }

    dropPlayerInventory(player) {
        const state = this.playerStates.get(player.id);

        // Create death crate at player position
        const deathCrate = {
            id: `death_crate_${player.id}`,
            type: 'death_chest',
            position: { ...player.position },
            lootTable: {
                weapons: state.inventory.weapons,
                armor: state.inventory.armor,
                potions: state.inventory.potions,
                gold: { min: state.inventory.gold, max: state.inventory.gold }
            },
            opened: false
        };

        this.environment.lootContainers.push(deathCrate);
    }

    onPlayerEliminated(player) {
        const session = this.currentSession;
        const state = this.playerStates.get(player.id);

        // Update elimination stats
        session.eliminations = session.eliminations || [];
        session.eliminations.push({
            playerId: player.id,
            playerName: player.name,
            placement: this.getPlacement(player.id),
            kills: state.kills,
            survivalTime: (Date.now() - session.startTime) / 1000
        });
    }

    getPlacement(playerId) {
        let aliveCount = 0;
        this.playerStates.forEach(state => {
            if (state.alive) aliveCount++;
        });

        return this.maxPlayers - aliveCount + 1;
    }

    checkWinCondition() {
        let aliveCount = 0;
        let lastAlivePlayer = null;

        this.playerStates.forEach((state, playerId) => {
            if (state.alive) {
                aliveCount++;
                lastAlivePlayer = playerId;
            }
        });

        if (aliveCount <= 1) {
            this.endMatch(lastAlivePlayer);
        }
    }

    scheduleSupplyDrops() {
        if (!this.brSettings.lootSystem.supplyDrops) return;

        const interval = this.brSettings.lootSystem.supplyDropInterval;
        this.supplyDropInterval = setInterval(() => {
            this.createSupplyDrop();
        }, interval * 1000);
    }

    createSupplyDrop() {
        // Random position within current zone
        const angle = Math.random() * 2 * Math.PI;
        const distance = Math.random() * (this.zoneRadius - 10);

        const position = {
            x: Math.cos(angle) * distance,
            y: 50, // Drop from sky
            z: Math.sin(angle) * distance
        };

        const supplyDrop = {
            id: `supply_drop_${Date.now()}`,
            type: 'supply_crate',
            position: position,
            landingTime: Date.now() + 5000, // 5 seconds to land
            lootTable: this.getLootTable('high'),
            status: 'falling'
        };

        this.environment.lootContainers.push(supplyDrop);

        // Notify players of supply drop
        this.notifySupplyDrop(supplyDrop);
    }

    notifySupplyDrop(supplyDrop) {
        const session = this.currentSession;

        session.players.forEach(player => {
            const state = this.playerStates.get(player.id);
            if (state.alive) {
                // Send supply drop notification
                player.notifications = player.notifications || [];
                player.notifications.push({
                    type: 'supply_drop',
                    position: supplyDrop.position,
                    timeRemaining: 5000,
                    message: 'Supply drop incoming!'
                });
            }
        });
    }

    getGameRules() {
        return {
            ...super.getGameRules(),
            ...this.brSettings,
            victoryConditions: {
                lastPlayerStanding: true,
                timeLimit: false
            },
            scoring: {
                placement: 100, // High value for placement
                kills: 25,
                damageDealt: 0.5,
                survivalTime: 0.1,
                lootCollected: 5
            },
            mechanics: {
                shrinkingZone: this.brSettings.shrinkingZone,
                lootSystem: this.brSettings.lootSystem,
                environmentalDamage: true,
                friendlyFire: true
            }
        };
    }

    calculateMatchResult(session) {
        const results = {
            players: [],
            winner: null,
            statistics: {}
        };

        // Sort players by placement
        const sortedPlayers = session.eliminations.sort((a, b) => a.placement - b.placement);

        sortedPlayers.forEach((elimination, index) => {
            const player = session.players.find(p => p.id === elimination.playerId);
            const state = this.playerStates.get(player.id);
            const score = this.calculateBattleRoyaleScore(elimination, state);

            results.players.push({
                playerId: elimination.playerId,
                playerName: elimination.playerName,
                placement: elimination.placement,
                kills: elimination.kills,
                survivalTime: elimination.survivalTime,
                score: score,
                rewards: this.calculateRewards(elimination.placement)
            });

            if (elimination.placement === 1) {
                results.winner = elimination.playerId;
            }
        });

        // Calculate match statistics
        results.statistics = {
            totalPlayers: session.players.length,
            matchDuration: (Date.now() - session.startTime) / 1000,
            totalKills: sortedPlayers.reduce((sum, p) => sum + p.kills, 0),
            zoneShrinks: Math.floor((Date.now() - this.shrinkStartTime) / 1000 / 60),
            supplyDrops: this.supplyDropSchedule.length
        };

        return results;
    }

    calculateBattleRoyaleScore(elimination, state) {
        const weights = {
            placement: 100,
            kills: 25,
            damageDealt: 0.5,
            survivalTime: 0.1,
            lootCollected: 5
        };

        let score = 0;
        score += (this.maxPlayers - elimination.placement + 1) * weights.placement;
        score += elimination.kills * weights.kills;
        score += state.damageDealt * weights.damageDealt;
        score += elimination.survivalTime * weights.survivalTime;
        score += (state.lootCollected || 0) * weights.lootCollected;

        return Math.max(0, score);
    }

    calculateRewards(placement) {
        const rewardTiers = {
            1: { gold: 1000, xp: 500, cosmetics: ['victory_crown'] },
            2: { gold: 500, xp: 250, cosmetics: [] },
            3: { gold: 250, xp: 125, cosmetics: [] },
            'top5': { gold: 100, xp: 50, cosmetics: [] },
            'top10': { gold: 50, xp: 25, cosmetics: [] }
        };

        if (placement === 1) return rewardTiers[1];
        if (placement === 2) return rewardTiers[2];
        if (placement === 3) return rewardTiers[3];
        if (placement <= 5) return rewardTiers['top5'];
        if (placement <= 10) return rewardTiers['top10'];

        return { gold: 10, xp: 5, cosmetics: [] };
    }

    getSpectatorData() {
        return {
            arenaType: this.type,
            environment: this.environment,
            zone: {
                position: this.zonePosition,
                radius: this.zoneRadius,
                shrinking: this.zoneShrinkInterval !== null
            },
            currentMatch: this.currentSession ? {
                playersAlive: Array.from(this.playerStates.entries())
                    .filter(([id, state]) => state.alive)
                    .map(([id, state]) => {
                        const player = this.currentSession.players.find(p => p.id === id);
                        return {
                            id: id,
                            name: player.name,
                            position: state.position,
                            health: player.currentHealth,
                            kills: state.kills
                        };
                    }),
                totalPlayers: this.currentSession.players.length,
                timeRemaining: this.zoneShrinkInterval ?
                    Math.max(0, this.brSettings.shrinkingZone.shrinkDuration -
                    (Date.now() - this.shrinkStartTime) / 1000) : 0
            } : null
        };
    }

    cleanup() {
        // Clear intervals
        if (this.zoneShrinkInterval) {
            clearInterval(this.zoneShrinkInterval);
        }
        if (this.supplyDropInterval) {
            clearInterval(this.supplyDropInterval);
        }

        // Clear player states
        this.playerStates.clear();
    }
}

module.exports = BattleRoyaleArena;