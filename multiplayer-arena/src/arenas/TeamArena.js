/**
 * Team Arena - Supports 2v2, 3v3, and 5v5 team competitions
 */

const BaseArena = require('../core/ArenaSystem').BaseArena;

class TeamArena extends BaseArena {
    constructor(id, config = {}) {
        super(id, config);
        this.type = 'team_competition';
        this.name = 'Team Battle Arena';
        this.description = 'Cooperative team-based combat with strategic positioning';

        // Team configurations
        this.teamConfig = {
            '2v2': { teams: 2, playersPerTeam: 2, totalPlayers: 4 },
            '3v3': { teams: 2, playersPerTeam: 3, totalPlayers: 6 },
            '5v5': { teams: 2, playersPerTeam: 5, totalPlayers: 10 }
        };

        // Default to 3v3 if not specified
        this.teamSize = config.teamSize || '3v3';
        this.minPlayers = this.teamConfig[this.teamSize].totalPlayers;
        this.maxPlayers = this.minPlayers;

        // Team-specific settings
        this.teamSettings = {
            timeLimit: config.timeLimit || 600, // 10 minutes
            respawnEnabled: config.respawnEnabled || false,
            respawnTime: config.respawnTime || 10,
            friendlyFire: config.friendlyFire || false,
            teamCommunication: true,
            sharedResources: config.sharedResources || false
        };

        // Role requirements for balanced teams
        this.roleRequirements = {
            'tank': { minPerTeam: 0, maxPerTeam: 2, classes: ['fighter', 'paladin', 'barbarian'] },
            'healer': { minPerTeam: 1, maxPerTeam: 2, classes: ['cleric', 'druid', 'bard'] },
            'damage': { minPerTeam: 1, maxPerTeam: 3, classes: ['rogue', 'ranger', 'wizard', 'sorcerer'] },
            'support': { minPerTeam: 0, maxPerTeam: 2, classes: ['bard', 'warlock', 'artificer'] }
        };
    }

    validatePlayers(players) {
        if (!super.validatePlayers(players)) return false;

        // Check if we can form balanced teams
        return this.canFormBalancedTeams(players);
    }

    canFormBalancedTeams(players) {
        const config = this.teamConfig[this.teamSize];
        const teamAssignments = this.assignPlayersToTeams(players);

        if (!teamAssignments) return false;

        // Check role balance for each team
        for (const [teamId, teamPlayers] of Object.entries(teamAssignments)) {
            if (!this.hasBalancedRoles(teamPlayers)) {
                return false;
            }
        }

        return true;
    }

    assignPlayersToTeams(players) {
        const config = this.teamConfig[this.teamSize];
        const teams = {};

        // Initialize teams
        for (let i = 0; i < config.teams; i++) {
            teams[`team_${i}`] = [];
        }

        // Sort players by skill rating for balanced matchmaking
        const sortedPlayers = [...players].sort((a, b) =>
            (b.skillRating || 0) - (a.skillRating || 0)
        );

        // Assign players using snake draft pattern
        let teamIndex = 0;
        let direction = 1;

        sortedPlayers.forEach(player => {
            const teamKey = `team_${teamIndex}`;
            teams[teamKey].push(player);

            teamIndex += direction;
            if (teamIndex >= config.teams || teamIndex < 0) {
                direction *= -1;
                teamIndex += direction;
            }
        });

        return teams;
    }

    hasBalancedRoles(teamPlayers) {
        const roleCount = {};
        const config = this.teamConfig[this.teamSize];

        // Count roles in team
        teamPlayers.forEach(player => {
            const role = this.getPlayerRole(player);
            roleCount[role] = (roleCount[role] || 0) + 1;
        });

        // Check role requirements
        for (const [role, requirements] of Object.entries(this.roleRequirements)) {
            const count = roleCount[role] || 0;
            if (count < requirements.minPerTeam || count > requirements.maxPerTeam) {
                return false;
            }
        }

        return true;
    }

    getPlayerRole(player) {
        const playerClass = player.character.class.toLowerCase();

        for (const [role, config] of Object.entries(this.roleRequirements)) {
            if (config.classes.includes(playerClass)) {
                return role;
            }
        }

        return 'damage'; // Default fallback
    }

    setupEnvironment() {
        const config = this.teamConfig[this.teamSize];

        // Environment size scales with team size
        const arenaSize = {
            '2v2': 'small',
            '3v3': 'medium',
            '5v5': 'large'
        }[this.teamSize];

        this.environment = {
            type: 'team_battlefield',
            size: arenaSize,
            terrain: 'varied',
            obstacles: this.generateObstacles(arenaSize),
            spawnPoints: this.generateSpawnPoints(config.teams),
            objectives: this.generateObjectives(),
            boundaries: {
                shape: 'rectangle',
                width: arenaSize === 'large' ? 50 : arenaSize === 'medium' ? 35 : 25,
                height: arenaSize === 'large' ? 50 : arenaSize === 'medium' ? 35 : 25
            }
        };

        // Create teams and assign players
        this.createTeams();
    }

    generateObstacles(size) {
        const obstacleDensity = {
            'small': 3,
            'medium': 6,
            'large': 10
        }[size];

        const obstacles = [];
        for (let i = 0; i < obstacleDensity; i++) {
            obstacles.push({
                id: `obstacle_${i}`,
                type: ['cover', 'barrier', 'elevation'][Math.floor(Math.random() * 3)],
                position: {
                    x: Math.random() * 40 - 20,
                    y: 0,
                    z: Math.random() * 40 - 20
                },
                size: {
                    width: 3 + Math.random() * 2,
                    height: 2 + Math.random() * 3,
                    depth: 3 + Math.random() * 2
                }
            });
        }

        return obstacles;
    }

    generateSpawnPoints(teamCount) {
        const spawnPoints = [];
        const angleStep = (2 * Math.PI) / teamCount;
        const radius = 15;

        for (let i = 0; i < teamCount; i++) {
            const angle = i * angleStep;
            spawnPoints.push({
                teamId: i,
                positions: [{
                    x: Math.cos(angle) * radius,
                    y: 0,
                    z: Math.sin(angle) * radius
                }]
            });
        }

        return spawnPoints;
    }

    generateObjectives() {
        return [
            {
                id: 'central_point',
                type: 'capture_point',
                position: { x: 0, y: 0, z: 0 },
                radius: 5,
                captureTime: 10,
                pointsPerSecond: 1
            }
        ];
    }

    createTeams() {
        const session = this.currentSession;
        const players = session.players;
        const teamAssignments = this.assignPlayersToTeams(players);

        session.teams = {};

        Object.entries(teamAssignments).forEach(([teamKey, teamPlayers]) => {
            const teamId = teamKey.replace('team_', '');
            session.teams[teamId] = {
                id: teamId,
                players: teamPlayers,
                score: 0,
                objectives: [],
                communication: {
                    enabled: this.teamSettings.teamCommunication,
                    channels: ['team', 'global']
                }
            };

            // Assign team to players
            teamPlayers.forEach(player => {
                player.teamId = teamId;
                player.role = this.getPlayerRole(player);
            });
        });
    }

    getGameRules() {
        return {
            ...super.getGameRules(),
            ...this.teamSettings,
            victoryConditions: {
                eliminateEnemyTeam: true,
                scoreLimit: true,
                timeLimit: true,
                objectiveControl: true
            },
            scoring: {
                kills: 10,
                assists: 5,
                deaths: -2,
                objectiveCapture: 50,
                teamPlay: 15,
                survivalTime: 1
            },
            teamFeatures: {
                sharedVision: false,
                resourceSharing: this.teamSettings.sharedResources,
                reviveAllies: true,
                combinedUltimates: false
            }
        };
    }

    calculateMatchResult(session) {
        const results = {
            teams: {},
            individualPlayers: [],
            winner: null
        };

        // Calculate team results
        Object.entries(session.teams).forEach(([teamId, team]) => {
            const teamScore = this.calculateTeamScore(team, session);
            results.teams[teamId] = {
                teamId: teamId,
                score: teamScore,
                players: team.players.map(p => p.id),
                stats: this.getTeamStats(team, session)
            };

            // Track highest score for winner determination
            if (!results.winner || teamScore > results.teams[results.winner].score) {
                results.winner = teamId;
            }
        });

        // Calculate individual results
        session.players.forEach(player => {
            const playerStats = session.getPlayerStats(player.id);
            const individualScore = this.calculateIndividualScore(playerStats, player.teamId);

            results.individualPlayers.push({
                playerId: player.id,
                playerName: player.name,
                teamId: player.teamId,
                role: player.role,
                score: individualScore,
                stats: playerStats,
                mvp: this.determineMVP(player, session)
            });
        });

        return results;
    }

    calculateTeamScore(team, session) {
        let score = 0;

        team.players.forEach(player => {
            const stats = session.getPlayerStats(player.id);
            score += this.calculateIndividualScore(stats, team.id);
        });

        // Add team bonuses
        const teamStats = this.getTeamStats(team, session);
        score += teamStats.objectiveControl * 50;
        score += teamStats.teamworkBonus * 25;

        return score;
    }

    calculateIndividualScore(stats, teamId) {
        const weights = {
            kills: 10,
            assists: 5,
            deaths: -2,
            damageDealt: 0.5,
            healingDone: 1,
            objectiveScore: 2,
            timeAlive: 0.1
        };

        let score = 0;
        score += stats.kills * weights.kills;
        score += stats.assists * weights.assists;
        score += stats.deaths * weights.deaths;
        score += stats.damageDealt * weights.damageDealt;
        score += stats.healingDone * weights.healingDone;
        score += stats.objectiveScore * weights.objectiveScore;
        score += stats.timeAlive * weights.timeAlive;

        return Math.max(0, score);
    }

    getTeamStats(team, session) {
        const stats = {
            totalKills: 0,
            totalDeaths: 0,
            totalAssists: 0,
            totalDamage: 0,
            totalHealing: 0,
            objectiveControl: 0,
            teamworkBonus: 0
        };

        team.players.forEach(player => {
            const playerStats = session.getPlayerStats(player.id);
            stats.totalKills += playerStats.kills;
            stats.totalDeaths += playerStats.deaths;
            stats.totalAssists += playerStats.assists;
            stats.totalDamage += playerStats.damageDealt;
            stats.totalHealing += playerStats.healingDone;
            stats.objectiveControl += playerStats.objectiveScore;
        });

        // Calculate teamwork bonus based on K/D ratio and coordination
        const kdRatio = stats.totalKills / Math.max(1, stats.totalDeaths);
        stats.teamworkBonus = Math.floor(kdRatio * 10);

        return stats;
    }

    determineMVP(player, session) {
        const team = session.teams[player.teamId];
        const playerStats = session.getPlayerStats(player.id);
        const playerScore = this.calculateIndividualScore(playerStats, player.teamId);

        // Compare with teammates
        let isMVP = true;
        team.players.forEach(teammate => {
            if (teammate.id !== player.id) {
                const teammateStats = session.getPlayerStats(teammate.id);
                const teammateScore = this.calculateIndividualScore(teammateStats, teammate.teamId);
                if (teammateScore > playerScore) {
                    isMVP = false;
                }
            }
        });

        return isMVP;
    }

    getSpectatorData() {
        return {
            arenaType: this.type,
            environment: this.environment,
            teamSize: this.teamSize,
            currentMatch: this.currentSession ? {
                teams: Object.entries(this.currentSession.teams).map(([id, team]) => ({
                    teamId: id,
                    score: team.score,
                    players: team.players.map(p => ({
                        id: p.id,
                        name: p.name,
                        class: p.character.class,
                        role: p.role,
                        health: p.currentHealth,
                        position: p.position
                    }))
                })),
                objectives: this.environment.objectives,
                timeRemaining: this.currentSession.getTimeRemaining()
            } : null
        };
    }
}

module.exports = TeamArena;