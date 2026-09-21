/**
 * 1v1 Dueling Arena - Class-specific competitive duels
 */

const BaseArena = require('../core/ArenaSystem').BaseArena;

class DuelingArena extends BaseArena {
    constructor(id, config = {}) {
        super(id, config);
        this.type = '1v1_duel';
        this.name = 'Honor Duel';
        this.description = 'Classic one-on-one combat with class-specific rules';
        this.minPlayers = 2;
        this.maxPlayers = 2;

        // Class-specific rules
        this.classRules = {
            fighter: {
                allowedWeapons: ['longsword', 'greatsword', 'shield'],
                spellRestrictions: [],
                maxSpellLevel: 0,
                specialAbilities: ['action_surge', 'second_wind']
            },
            wizard: {
                allowedWeapons: ['staff', 'dagger', 'wand'],
                spellRestrictions: ['time_stop', 'wish'],
                maxSpellLevel: 8,
                specialAbilities: ['arcane_recovery', 'spell_mastery']
            },
            cleric: {
                allowedWeapons: ['mace', 'warhammer', 'holy_symbol'],
                spellRestrictions: ['divine_intervention'],
                maxSpellLevel: 8,
                specialAbilities: ['channel_divinity', 'divine_intervention']
            },
            rogue: {
                allowedWeapons: ['dagger', 'shortsword', 'bow', 'crossbow'],
                spellRestrictions: [],
                maxSpellLevel: 4,
                specialAbilities: ['sneak_attack', 'cunning_action']
            },
            ranger: {
                allowedWeapons: ['longbow', 'shortbow', 'dual_swords'],
                spellRestrictions: [],
                maxSpellLevel: 5,
                specialAbilities: ['favored_enemy', 'natural_explorer']
            }
        };

        // Duel-specific settings
        this.duelSettings = {
            timeLimit: config.timeLimit || 300, // 5 minutes default
            healthRegeneration: false,
            manaRegeneration: true,
            environmentalHazards: false,
            spectatorMode: true
        };
    }

    validatePlayers(players) {
        if (!super.validatePlayers(players)) return false;

        // Ensure players have compatible classes for fair dueling
        const class1 = players[0].character.class.toLowerCase();
        const class2 = players[1].character.class.toLowerCase();

        // Check for class balance (some classes have advantages against others)
        return this.isBalancedMatchup(class1, class2);
    }

    isBalancedMatchup(class1, class2) {
        // Define class advantage/disadvantage matrix
        const balanceMatrix = {
            'fighter': { 'wizard': 0.8, 'rogue': 1.1, 'cleric': 1.0, 'ranger': 0.9 },
            'wizard': { 'fighter': 1.2, 'rogue': 0.9, 'cleric': 1.0, 'ranger': 1.1 },
            'cleric': { 'fighter': 1.0, 'rogue': 1.1, 'wizard': 1.0, 'ranger': 0.9 },
            'rogue': { 'fighter': 0.9, 'wizard': 1.1, 'cleric': 0.9, 'ranger': 1.0 },
            'ranger': { 'fighter': 1.1, 'wizard': 0.9, 'cleric': 1.1, 'rogue': 1.0 }
        };

        const balanceFactor = balanceMatrix[class1]?.[class2] || 1.0;
        return Math.abs(balanceFactor - 1.0) <= 0.2; // Allow 20% imbalance
    }

    setupEnvironment() {
        // Create duel-specific arena environment
        this.environment = {
            type: 'dueling_circle',
            size: 'medium',
            terrain: 'stone_platform',
            obstacles: [],
            spawnPoints: [
                { x: 0, y: 0, z: 5 },
                { x: 0, y: 0, z: -5 }
            ],
            boundaries: {
                shape: 'circle',
                radius: 10
            }
        };

        // Apply class-specific modifications
        this.applyClassModifications();
    }

    applyClassModifications() {
        const session = this.currentSession;
        const players = session.players;

        players.forEach(player => {
            const playerClass = player.character.class.toLowerCase();
            const rules = this.classRules[playerClass];

            if (rules) {
                player.duelRestrictions = rules;
                player.allowedAbilities = rules.specialAbilities;
            }
        });
    }

    getGameRules() {
        return {
            ...super.getGameRules(),
            ...this.duelSettings,
            victoryConditions: {
                knockout: true,
                timeout: true,
                surrender: true,
                disqualification: true
            },
            scoring: {
                damageDealt: true,
                damageReceived: true,
                spellsCast: true,
                abilitiesUsed: true,
                timeAlive: true
            }
        };
    }

    calculateMatchResult(session) {
        const players = session.players;
        const results = [];

        players.forEach(player => {
            const stats = session.getPlayerStats(player.id);
            const score = this.calculateDuelScore(stats);

            results.push({
                playerId: player.id,
                playerName: player.name,
                characterClass: player.character.class,
                score: score,
                winner: this.determineWinner(session, player.id),
                stats: stats
            });
        });

        return results;
    }

    calculateDuelScore(stats) {
        // Complex scoring formula for duels
        const weights = {
            damageDealt: 10,
            damageReceived: -5,
            spellsEffective: 8,
            abilitiesEffective: 6,
            timeAlive: 2,
            finishingBlow: 50
        };

        let score = 0;
        score += stats.damageDealt * weights.damageDealt;
        score += stats.damageReceived * weights.damageReceived;
        score += stats.spellsEffective * weights.spellsEffective;
        score += stats.abilitiesEffective * weights.abilitiesEffective;
        score += stats.timeAlive * weights.timeAlive;

        if (stats.finishingBlow) {
            score += weights.finishingBlow;
        }

        return Math.max(0, score);
    }

    determineWinner(session, playerId) {
        const stats = session.getPlayerStats(playerId);
        const opponentStats = session.getOpponentStats(playerId);

        // Check for knockout
        if (opponentStats.health <= 0 && stats.health > 0) {
            return true;
        }

        // Check for timeout
        if (session.timeExpired) {
            return stats.health > opponentStats.health;
        }

        return false;
    }

    getSpectatorData() {
        return {
            arenaType: this.type,
            environment: this.environment,
            currentMatch: this.currentSession ? {
                players: this.currentSession.players.map(p => ({
                    id: p.id,
                    name: p.name,
                    class: p.character.class,
                    health: p.currentHealth,
                    mana: p.currentMana,
                    position: p.position
                })),
                timeRemaining: this.currentSession.getTimeRemaining(),
                round: this.currentSession.currentRound
            } : null
        };
    }
}

module.exports = DuelingArena;