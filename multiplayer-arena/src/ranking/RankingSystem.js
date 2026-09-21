/**
 * Comprehensive Ranking and Rewards System for DMlogn8n Multiplayer Arena
 * Features leagues, seasonal rankings, achievements, and cosmetic rewards
 */

class RankingSystem {
    constructor() {
        this.playerRatings = new Map();
        this.leagueSystem = new LeagueSystem();
        this.seasonManager = new SeasonManager();
        this.achievementSystem = new AchievementSystem();
        this.rewardManager = new RewardManager();
        this.tournamentQualification = new TournamentQualification();

        this.initializeSystems();
    }

    /**
     * Initialize ranking systems
     */
    initializeSystems() {
        this.leagueSystem.initialize();
        this.seasonManager.initialize();
        this.achievementSystem.initialize();
        this.rewardManager.initialize();

        // Set up event listeners
        this.setupEventListeners();
    }

    /**
     * Update player ranking after match
     */
    updatePlayerRanking(playerId, matchResult) {
        // Get current player data
        const playerData = this.getPlayerData(playerId);
        if (!playerData) {
            throw new Error(`Player ${playerId} not found`);
        }

        // Calculate rating changes
        const ratingChanges = this.calculateRatingChanges(playerData, matchResult);

        // Update player's ELO rating
        playerData.elo += ratingChanges.eloChange;

        // Update league and division
        const leagueUpdate = this.leagueSystem.updatePlayerLeague(playerData, playerData.elo);

        // Update season progress
        const seasonProgress = this.seasonManager.updatePlayerProgress(playerId, matchResult);

        // Check for new achievements
        const newAchievements = this.achievementSystem.checkAchievements(playerId, matchResult, playerData);

        // Calculate rewards
        const rewards = this.rewardManager.calculateRewards(playerId, matchResult, leagueUpdate, newAchievements);

        // Update tournament qualification
        const tournamentStatus = this.tournamentQualification.updateQualification(playerId, playerData);

        // Compile ranking update
        const rankingUpdate = {
            playerId: playerId,
            previousElo: playerData.elo - ratingChanges.eloChange,
            newElo: playerData.elo,
            eloChange: ratingChanges.eloChange,
            leagueUpdate: leagueUpdate,
            seasonProgress: seasonProgress,
            newAchievements: newAchievements,
            rewards: rewards,
            tournamentStatus: tournamentStatus,
            matchStatistics: this.calculateMatchStatistics(matchResult),
            timestamp: Date.now()
        };

        // Save updated player data
        this.savePlayerData(playerId, playerData);

        // Send notifications
        this.sendRankingNotifications(playerId, rankingUpdate);

        return rankingUpdate;
    }

    /**
     * Calculate ELO rating changes
     */
    calculateRatingChanges(playerData, matchResult) {
        const opponentRating = matchResult.opponentAverageElo || 1500;
        const expectedScore = this.calculateExpectedScore(playerData.elo, opponentRating);
        const actualScore = this.calculateActualScore(matchResult);

        // K-factor varies based on player level and match type
        const kFactor = this.calculateKFactor(playerData, matchResult);

        const eloChange = Math.round(kFactor * (actualScore - expectedScore));

        // Apply bonus modifiers
        const bonusModifiers = this.calculateBonusModifiers(playerData, matchResult);
        const finalEloChange = Math.round(eloChange * bonusModifiers.multiplier) + bonusModifiers.flat;

        return {
            eloChange: finalEloChange,
            baseChange: eloChange,
            kFactor: kFactor,
            expectedScore: expectedScore,
            actualScore: actualScore,
            modifiers: bonusModifiers
        };
    }

    /**
     * Calculate expected score using ELO formula
     */
    calculateExpectedScore(playerRating, opponentRating) {
        return 1 / (1 + Math.pow(10, (opponentRating - playerRating) / 400));
    }

    /**
     * Calculate actual score from match result
     */
    calculateActualScore(matchResult) {
        if (matchResult.placement === 1) return 1.0;
        if (matchResult.placement === 2) return 0.75;
        if (matchResult.placement === 3) return 0.5;
        if (matchResult.placement <= 5) return 0.25;
        return 0.0;
    }

    /**
     * Calculate K-factor for ELO changes
     */
    calculateKFactor(playerData, matchResult) {
        let kFactor = 32; // Base K-factor

        // Adjust based on player level
        if (playerData.level < 10) kFactor = 48;
        else if (playerData.level < 20) kFactor = 40;
        else if (playerData.level < 30) kFactor = 32;
        else if (playerData.elo > 2000) kFactor = 24;
        else if (playerData.elo > 2500) kFactor = 16;

        // Adjust based on match type
        if (matchResult.arenaType === 'tournament') kFactor *= 1.5;
        if (matchResult.arenaType === 'ranked') kFactor *= 1.2;

        return kFactor;
    }

    /**
     * Calculate bonus modifiers
     */
    calculateBonusModifiers(playerData, matchResult) {
        let multiplier = 1.0;
        let flat = 0;

        // Performance bonus
        if (matchResult.kda > 3.0) multiplier += 0.2;
        if (matchResult.kda > 5.0) multiplier += 0.3;
        if (matchResult.mvp) multiplier += 0.1;

        // Streak bonus
        if (playerData.currentStreak > 3) flat += 15;
        if (playerData.currentStreak > 5) flat += 25;

        // Upset bonus
        if (matchResult.upset) flat += 20;

        // First win of the day bonus
        if (this.isFirstWinOfDay(playerData)) flat += 30;

        // Premium member bonus
        if (playerData.premium) multiplier += 0.15;

        return { multiplier, flat };
    }

    /**
     * Get player ranking information
     */
    getPlayerRanking(playerId) {
        const playerData = this.getPlayerData(playerId);
        if (!playerData) return null;

        return {
            playerId: playerId,
            playerName: playerData.name,
            elo: playerData.elo,
            league: this.leagueSystem.getPlayerLeague(playerData.elo),
            division: this.leagueSystem.getPlayerDivision(playerData.elo),
            seasonRank: this.seasonManager.getPlayerSeasonRank(playerId),
            globalRank: this.getGlobalRank(playerId),
            regionalRank: this.getRegionalRank(playerId, playerData.region),
            statistics: {
                wins: playerData.wins,
                losses: playerData.losses,
                winRate: playerData.wins / Math.max(1, playerData.wins + playerData.losses),
                currentStreak: playerData.currentStreak,
                bestStreak: playerData.bestStreak,
                matchesPlayed: playerData.matchesPlayed
            },
            achievements: this.achievementSystem.getPlayerAchievements(playerId),
            rewards: this.rewardManager.getPlayerRewards(playerId),
            tournamentQualified: this.tournamentQualification.isQualified(playerId)
        };
    }

    /**
     * Get leaderboard rankings
     */
    getLeaderboard(type = 'global', filters = {}) {
        let rankings;

        switch (type) {
            case 'global':
                rankings = this.getGlobalLeaderboard(filters);
                break;
            case 'regional':
                rankings = this.getRegionalLeaderboard(filters.region, filters);
                break;
            case 'league':
                rankings = this.getLeagueLeaderboard(filters.league, filters);
                break;
            case 'seasonal':
                rankings = this.getSeasonalLeaderboard(filters.season, filters);
                break;
            case 'class':
                rankings = this.getClassLeaderboard(filters.class, filters);
                break;
            default:
                rankings = this.getGlobalLeaderboard(filters);
        }

        return rankings;
    }

    /**
     * Get global leaderboard
     */
    getGlobalLeaderboard(filters = {}) {
        const limit = filters.limit || 100;
        const offset = filters.offset || 0;

        // Get all players sorted by ELO
        const allPlayers = Array.from(this.playerRatings.entries())
            .map(([playerId, data]) => ({
                playerId: playerId,
                playerName: data.name,
                elo: data.elo,
                league: this.leagueSystem.getPlayerLeague(data.elo),
                division: this.leagueSystem.getPlayerDivision(data.elo),
                wins: data.wins,
                matchesPlayed: data.matchesPlayed,
                winRate: data.wins / Math.max(1, data.matchesPlayed)
            }))
            .sort((a, b) => b.elo - a.elo)
            .slice(offset, offset + limit);

        return {
            type: 'global',
            players: allPlayers.map((player, index) => ({
                ...player,
                rank: offset + index + 1
            })),
            totalPlayers: this.playerRatings.size,
            lastUpdated: Date.now()
        };
    }

    /**
     * Get seasonal leaderboard
     */
    getSeasonalLeaderboard(seasonId = null, filters = {}) {
        const currentSeason = seasonId || this.seasonManager.getCurrentSeason().id;
        const limit = filters.limit || 100;
        const offset = filters.offset || 0;

        const seasonRankings = this.seasonManager.getSeasonLeaderboard(currentSeason, limit, offset);

        return {
            type: 'seasonal',
            seasonId: currentSeason,
            players: seasonRankings,
            lastUpdated: Date.now()
        };
    }

    /**
     * Get global rank for player
     */
    getGlobalRank(playerId) {
        const sortedPlayers = Array.from(this.playerRatings.entries())
            .sort(([,a], [,b]) => b.elo - a.elo);

        const rank = sortedPlayers.findIndex(([id]) => id === playerId);
        return rank !== -1 ? rank + 1 : null;
    }

    /**
     * Get regional rank for player
     */
    getRegionalRank(playerId, region) {
        const regionalPlayers = Array.from(this.playerRatings.entries())
            .filter(([,data]) => data.region === region)
            .sort(([,a], [,b]) => b.elo - a.elo);

        const rank = regionalPlayers.findIndex(([id]) => id === playerId);
        return rank !== -1 ? rank + 1 : null;
    }

    /**
     * Calculate match statistics
     */
    calculateMatchStatistics(matchResult) {
        return {
            kills: matchResult.kills || 0,
            deaths: matchResult.deaths || 0,
            assists: matchResult.assists || 0,
            kda: matchResult.kda || 0,
            damageDealt: matchResult.damageDealt || 0,
            healingDone: matchResult.healingDone || 0,
            objectiveScore: matchResult.objectiveScore || 0,
            survivalTime: matchResult.survivalTime || 0,
            placement: matchResult.placement,
            mvp: matchResult.mvp || false
        };
    }

    /**
     * Send ranking notifications
     */
    sendRankingNotifications(playerId, rankingUpdate) {
        const notifications = [];

        // League promotion notification
        if (rankingUpdate.leagueUpdate.promoted) {
            notifications.push({
                type: 'league_promotion',
                title: 'League Promotion!',
                message: `Congratulations! You've been promoted to ${rankingUpdate.leagueUpdate.newLeague} ${rankingUpdate.leagueUpdate.newDivision}!`,
                rewards: rankingUpdate.leagueUpdate.promotionRewards
            });
        }

        // Achievement notifications
        rankingUpdate.newAchievements.forEach(achievement => {
            notifications.push({
                type: 'achievement_unlocked',
                title: 'Achievement Unlocked!',
                message: achievement.name,
                description: achievement.description,
                icon: achievement.icon
            });
        });

        // New personal best
        if (rankingUpdate.newElo > (this.getPlayerData(playerId).peakElo || 0)) {
            notifications.push({
                type: 'personal_best',
                title: 'New Personal Best!',
                message: `New peak ELO rating: ${rankingUpdate.newElo}!`
            });
        }

        // Send notifications to player
        this.sendNotifications(playerId, notifications);
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Listen for season changes
        this.seasonManager.on('seasonEnd', (seasonData) => {
            this.handleSeasonEnd(seasonData);
        });

        // Listen for achievement unlocks
        this.achievementSystem.on('achievementUnlocked', (data) => {
            this.handleAchievementUnlock(data);
        });
    }

    /**
     * Handle season end
     */
    handleSeasonEnd(seasonData) {
        // Distribute season end rewards
        this.distributeSeasonRewards(seasonData);

        // Reset seasonal rankings
        this.resetSeasonalRankings(seasonData);

        // Update tournament qualifications
        this.tournamentQualification.processSeasonEnd(seasonData);
    }

    /**
     * Handle achievement unlock
     */
    handleAchievementUnlock(data) {
        // Award achievement rewards
        this.rewardManager.awardAchievementRewards(data.playerId, data.achievement);
    }

    // Helper methods
    getPlayerData(playerId) {
        return this.playerRatings.get(playerId);
    }

    savePlayerData(playerId, playerData) {
        this.playerRatings.set(playerId, playerData);
    }

    isFirstWinOfDay(playerData) {
        const today = new Date().toDateString();
        return playerData.lastWinDate !== today;
    }

    sendNotifications(playerId, notifications) {
        // Send notifications to player
        console.log(`Sending notifications to player ${playerId}:`, notifications);
    }

    distributeSeasonRewards(seasonData) {
        // Distribute rewards based on final season rankings
    }

    resetSeasonalRankings(seasonData) {
        // Reset seasonal progression for new season
    }
}

/**
 * League System with divisions and promotions
 */
class LeagueSystem {
    constructor() {
        this.leagues = new Map();
        this.divisions = ['IV', 'III', 'II', 'I'];
    }

    initialize() {
        this.setupLeagues();
    }

    setupLeagues() {
        this.leagues.set('Bronze', { minElo: 0, maxElo: 1399, color: '#CD7F32' });
        this.leagues.set('Silver', { minElo: 1400, maxElo: 1699, color: '#C0C0C0' });
        this.leagues.set('Gold', { minElo: 1700, maxElo: 1999, color: '#FFD700' });
        this.leagues.set('Platinum', { minElo: 2000, maxElo: 2299, color: '#E5E4E2' });
        this.leagues.set('Diamond', { minElo: 2300, maxElo: 2599, color: '#B9F2FF' });
        this.leagues.set('Master', { minElo: 2600, maxElo: 2899, color: '#D946EF' });
        this.leagues.set('Mythic', { minElo: 2900, maxElo: Infinity, color: '#FF6B35' });
    }

    updatePlayerLeague(playerData, newElo) {
        const currentLeague = this.getPlayerLeague(playerData.elo);
        const newLeague = this.getPlayerLeague(newElo);
        const currentDivision = this.getPlayerDivision(playerData.elo);
        const newDivision = this.getPlayerDivision(newElo);

        const promoted = newElo > playerData.elo &&
            (this.getLeagueTier(newLeague) > this.getLeagueTier(currentLeague) ||
             (newLeague === currentLeague && this.getDivisionTier(newDivision) > this.getDivisionTier(currentDivision)));

        const demoted = newElo < playerData.elo &&
            (this.getLeagueTier(newLeague) < this.getLeagueTier(currentLeague) ||
             (newLeague === currentLeague && this.getDivisionTier(newDivision) < this.getDivisionTier(currentDivision)));

        const update = {
            previousLeague: currentLeague,
            previousDivision: currentDivision,
            newLeague: newLeague,
            newDivision: newDivision,
            promoted: promoted,
            demoted: demoted
        };

        if (promoted) {
            update.promotionRewards = this.calculatePromotionRewards(newLeague, newDivision);
        }

        return update;
    }

    getPlayerLeague(elo) {
        for (const [leagueName, leagueData] of this.leagues.entries()) {
            if (elo >= leagueData.minElo && elo <= leagueData.maxElo) {
                return leagueName;
            }
        }
        return 'Bronze';
    }

    getPlayerDivision(elo) {
        const league = this.getPlayerLeague(elo);
        const leagueData = this.leagues.get(league);
        const leagueRange = leagueData.maxElo - leagueData.minElo;
        const divisionSize = leagueRange / this.divisions.length;

        const positionInLeague = elo - leagueData.minElo;
        const divisionIndex = Math.min(
            Math.floor(positionInLeague / divisionSize),
            this.divisions.length - 1
        );

        return this.divisions[divisionIndex];
    }

    getLeagueTier(league) {
        const leagueOrder = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Mythic'];
        return leagueOrder.indexOf(league);
    }

    getDivisionTier(division) {
        return this.divisions.indexOf(division);
    }

    calculatePromotionRewards(league, division) {
        const baseRewards = {
            'Bronze': { gold: 100, gems: 10 },
            'Silver': { gold: 250, gems: 25 },
            'Gold': { gold: 500, gems: 50 },
            'Platinum': { gold: 1000, gems: 100 },
            'Diamond': { gold: 2000, gems: 200 },
            'Master': { gold: 5000, gems: 500 },
            'Mythic': { gold: 10000, gems: 1000 }
        };

        return baseRewards[league] || { gold: 50, gems: 5 };
    }
}

/**
 * Season Manager for seasonal rankings and rewards
 */
class SeasonManager {
    constructor() {
        this.currentSeason = null;
        this.seasonHistory = new Map();
        this.playerSeasonData = new Map();
        this.eventEmitter = new EventEmitter();
    }

    initialize() {
        this.startNewSeason();
        this.setupSeasonSchedule();
    }

    startNewSeason() {
        const seasonId = this.generateSeasonId();
        const season = {
            id: seasonId,
            name: `Season ${this.seasonHistory.size + 1}`,
            startTime: Date.now(),
            endTime: Date.now() + (30 * 24 * 60 * 60 * 1000), // 30 days
            theme: this.generateSeasonTheme(),
            rewards: this.generateSeasonRewards(),
            status: 'active'
        };

        this.currentSeason = season;
        this.seasonHistory.set(seasonId, season);
    }

    updatePlayerProgress(playerId, matchResult) {
        const seasonId = this.currentSeason.id;

        if (!this.playerSeasonData.has(seasonId)) {
            this.playerSeasonData.set(seasonId, new Map());
        }

        const seasonPlayers = this.playerSeasonData.get(seasonId);

        if (!seasonPlayers.has(playerId)) {
            seasonPlayers.set(playerId, {
                playerId: playerId,
                seasonId: seasonId,
                seasonElo: 1500,
                matchesPlayed: 0,
                wins: 0,
                losses: 0,
                seasonPoints: 0,
                rank: null
            });
        }

        const playerSeasonData = seasonPlayers.get(playerId);
        playerSeasonData.matchesPlayed++;
        playerSeasonData.wins += matchResult.placement === 1 ? 1 : 0;
        playerSeasonData.losses += matchResult.placement !== 1 ? 1 : 0;
        playerSeasonData.seasonPoints += this.calculateSeasonPoints(matchResult);

        return playerSeasonData;
    }

    getPlayerSeasonRank(playerId) {
        const seasonId = this.currentSeason.id;
        const seasonPlayers = this.playerSeasonData.get(seasonId);

        if (!seasonPlayers) return null;

        const sortedPlayers = Array.from(seasonPlayers.values())
            .sort((a, b) => b.seasonPoints - a.seasonPoints);

        const rank = sortedPlayers.findIndex(player => player.playerId === playerId);
        return rank !== -1 ? rank + 1 : null;
    }

    getSeasonLeaderboard(seasonId, limit = 100, offset = 0) {
        const seasonPlayers = this.playerSeasonData.get(seasonId);

        if (!seasonPlayers) return [];

        return Array.from(seasonPlayers.values())
            .sort((a, b) => b.seasonPoints - a.seasonPoints)
            .slice(offset, offset + limit)
            .map((player, index) => ({
                ...player,
                rank: offset + index + 1
            }));
    }

    getCurrentSeason() {
        return this.currentSeason;
    }

    calculateSeasonPoints(matchResult) {
        let points = 0;

        // Placement points
        const placementPoints = {
            1: 100,
            2: 80,
            3: 65,
            4: 50,
            5: 40,
            6: 30,
            7: 20,
            8: 15,
            9: 10,
            10: 5
        };

        points += placementPoints[matchResult.placement] || 0;

        // Performance points
        points += matchResult.kills * 10;
        points += matchResult.assists * 5;
        points += Math.floor(matchResult.damageDealt / 100);

        // Bonus points
        if (matchResult.mvp) points += 50;
        if (matchResult.kda > 5.0) points += 30;

        return points;
    }

    generateSeasonId() {
        return `season_${Date.now()}`;
    }

    generateSeasonTheme() {
        const themes = ['Dragon's Fury', 'Arcane Ascension', 'Shadow Wars', 'Divine Champions', 'Chaos Rising'];
        return themes[Math.floor(Math.random() * themes.length)];
    }

    generateSeasonRewards() {
        return {
            rank1: { title: 'Season Champion', cosmetic: 'crown_of_champions', currency: 5000 },
            top10: { title: 'Elite Warrior', cosmetic: 'elite_banner', currency: 2000 },
            top100: { title: 'Season Veteran', cosmetic: 'veteran_badge', currency: 1000 },
            participation: { title: 'Season Competitor', currency: 500 }
        };
    }

    setupSeasonSchedule() {
        // Check for season end every hour
        setInterval(() => {
            if (Date.now() >= this.currentSeason.endTime) {
                this.endSeason();
            }
        }, 60 * 60 * 1000);
    }

    endSeason() {
        const endingSeason = this.currentSeason;
        endingSeason.status = 'ended';
        endingSeason.actualEndTime = Date.now();

        // Emit season end event
        this.eventEmitter.emit('seasonEnd', endingSeason);

        // Start new season
        this.startNewSeason();
    }

    on(event, callback) {
        this.eventEmitter.on(event, callback);
    }
}

/**
 * Achievement System for tracking player accomplishments
 */
class AchievementSystem {
    constructor() {
        this.achievements = new Map();
        this.playerAchievements = new Map();
        this.eventEmitter = new EventEmitter();
    }

    initialize() {
        this.setupAchievements();
    }

    setupAchievements() {
        // Combat achievements
        this.achievements.set('first_blood', {
            id: 'first_blood',
            name: 'First Blood',
            description: 'Get your first kill in an arena match',
            icon: 'sword',
            category: 'combat',
            rarity: 'common',
            requirements: { kills: 1 },
            rewards: { xp: 100, gold: 50 }
        });

        this.achievements.set('killer_instinct', {
            id: 'killer_instinct',
            name: 'Killer Instinct',
            description: 'Get 10 kills in a single match',
            icon: 'skull',
            category: 'combat',
            rarity: 'rare',
            requirements: { kills: 10, singleMatch: true },
            rewards: { xp: 500, gold: 250 }
        });

        this.achievements.set('untouchable', {
            id: 'untouchable',
            name: 'Untouchable',
            description: 'Win a match without taking any damage',
            icon: 'shield',
            category: 'combat',
            rarity: 'epic',
            requirements: { win: true, damageTaken: 0 },
            rewards: { xp: 1000, gold: 500, cosmetic: 'untouchable_title' }
        });

        // Streak achievements
        this.achievements.set('on_fire', {
            id: 'on_fire',
            name: 'On Fire',
            description: 'Win 5 matches in a row',
            icon: 'fire',
            category: 'streak',
            rarity: 'rare',
            requirements: { winStreak: 5 },
            rewards: { xp: 750, gold: 400 }
        });

        this.achievements.set('unstoppable', {
            id: 'unstoppable',
            name: 'Unstoppable',
            description: 'Win 10 matches in a row',
            icon: 'crown',
            category: 'streak',
            rarity: 'legendary',
            requirements: { winStreak: 10 },
            rewards: { xp: 2000, gold: 1000, cosmetic: 'unstoppable_banner' }
        });

        // Ranking achievements
        this.achievements.set('rank_up', {
            id: 'rank_up',
            name: 'Climbing the Ranks',
            description: 'Reach Silver league',
            icon: 'arrow_up',
            category: 'ranking',
            rarity: 'common',
            requirements: { league: 'Silver' },
            rewards: { xp: 300, gold: 150 }
        });

        this.achievements.set('elite_warrior', {
            id: 'elite_warrior',
            name: 'Elite Warrior',
            description: 'Reach Diamond league',
            icon: 'diamond',
            category: 'ranking',
            rarity: 'epic',
            requirements: { league: 'Diamond' },
            rewards: { xp: 1500, gold: 750, cosmetic: 'diamond_badge' }
        });
    }

    checkAchievements(playerId, matchResult, playerData) {
        const newAchievements = [];
        const playerCurrentAchievements = this.playerAchievements.get(playerId) || new Set();

        this.achievements.forEach((achievement, achievementId) => {
            if (!playerCurrentAchievements.has(achievementId)) {
                if (this.checkAchievementRequirements(achievement, matchResult, playerData)) {
                    this.unlockAchievement(playerId, achievementId);
                    newAchievements.push(achievement);
                }
            }
        });

        return newAchievements;
    }

    checkAchievementRequirements(achievement, matchResult, playerData) {
        const requirements = achievement.requirements;

        // Check basic requirements
        if (requirements.kills && matchResult.kills < requirements.kills) return false;
        if (requirements.win && matchResult.placement !== 1) return false;
        if (requirements.winStreak && playerData.currentStreak < requirements.winStreak) return false;
        if (requirements.league && playerData.league !== requirements.league) return false;
        if (requirements.damageTaken !== undefined && matchResult.damageTaken > requirements.damageTaken) return false;
        if (requirements.singleMatch && matchResult.kills < requirements.kills) return false;

        return true;
    }

    unlockAchievement(playerId, achievementId) {
        if (!this.playerAchievements.has(playerId)) {
            this.playerAchievements.set(playerId, new Set());
        }

        const playerAchievementSet = this.playerAchievements.get(playerId);
        playerAchievementSet.add(achievementId);

        const achievement = this.achievements.get(achievementId);

        // Emit achievement unlock event
        this.eventEmitter.emit('achievementUnlocked', {
            playerId: playerId,
            achievement: achievement,
            timestamp: Date.now()
        });
    }

    getPlayerAchievements(playerId) {
        const playerAchievementSet = this.playerAchievements.get(playerId) || new Set();
        return Array.from(playerAchievementSet).map(id => this.achievements.get(id));
    }

    on(event, callback) {
        this.eventEmitter.on(event, callback);
    }
}

/**
 * Reward Manager for calculating and distributing rewards
 */
class RewardManager {
    constructor() {
        this.rewardPools = new Map();
        this.playerInventory = new Map();
    }

    initialize() {
        this.setupRewardPools();
    }

    setupRewardPools() {
        this.rewardPools.set('match_victory', {
            baseXP: 100,
            baseGold: 50,
            leagueMultipliers: {
                'Bronze': 1.0,
                'Silver': 1.2,
                'Gold': 1.5,
                'Platinum': 2.0,
                'Diamond': 3.0,
                'Master': 5.0,
                'Mythic': 10.0
            }
        });

        this.rewardPools.set('daily_bonus', {
            firstWin: { xp: 200, gold: 100 },
            threeWins: { xp: 500, gold: 250 },
            fiveWins: { xp: 1000, gold: 500 }
        });
    }

    calculateRewards(playerId, matchResult, leagueUpdate, newAchievements) {
        const rewards = {
            xp: 0,
            gold: 0,
            gems: 0,
            cosmetics: [],
            inventory: []
        };

        // Base match rewards
        const matchRewards = this.calculateMatchRewards(matchResult, leagueUpdate);
        rewards.xp += matchRewards.xp;
        rewards.gold += matchRewards.gold;

        // Achievement rewards
        newAchievements.forEach(achievement => {
            if (achievement.rewards) {
                rewards.xp += achievement.rewards.xp || 0;
                rewards.gold += achievement.rewards.gold || 0;
                if (achievement.rewards.cosmetic) {
                    rewards.cosmetics.push(achievement.rewards.cosmetic);
                }
            }
        });

        // League promotion rewards
        if (leagueUpdate.promoted && leagueUpdate.promotionRewards) {
            rewards.gold += leagueUpdate.promotionRewards.gold || 0;
            rewards.gems += leagueUpdate.promotionRewards.gems || 0;
        }

        // Streak bonuses
        const streakBonus = this.calculateStreakBonus(playerId, matchResult);
        rewards.xp += streakBonus.xp;
        rewards.gold += streakBonus.gold;

        return rewards;
    }

    calculateMatchRewards(matchResult, leagueUpdate) {
        const rewardPool = this.rewardPools.get('match_victory');
        const leagueMultiplier = rewardPool.leagueMultipliers[leagueUpdate.newLeague] || 1.0;

        let xp = rewardPool.baseXP;
        let gold = rewardPool.baseGold;

        // Apply placement multiplier
        const placementMultiplier = this.getPlacementMultiplier(matchResult.placement);
        xp *= placementMultiplier;
        gold *= placementMultiplier;

        // Apply league multiplier
        xp *= leagueMultiplier;
        gold *= leagueMultiplier;

        // Performance bonus
        const performanceBonus = this.calculatePerformanceBonus(matchResult);
        xp += performanceBonus.xp;
        gold += performanceBonus.gold;

        return {
            xp: Math.floor(xp),
            gold: Math.floor(gold)
        };
    }

    getPlacementMultiplier(placement) {
        const multipliers = {
            1: 2.0,
            2: 1.5,
            3: 1.2,
            4: 1.0,
            5: 0.8,
            6: 0.6,
            7: 0.4,
            8: 0.3,
            9: 0.2,
            10: 0.1
        };

        return multipliers[placement] || 0.1;
    }

    calculatePerformanceBonus(matchResult) {
        let xpBonus = 0;
        let goldBonus = 0;

        // KDA bonus
        if (matchResult.kda > 2.0) {
            xpBonus += 50;
            goldBonus += 25;
        }
        if (matchResult.kda > 3.0) {
            xpBonus += 100;
            goldBonus += 50;
        }

        // MVP bonus
        if (matchResult.mvp) {
            xpBonus += 150;
            goldBonus += 75;
        }

        // Damage bonus
        if (matchResult.damageDealt > 1000) {
            xpBonus += 25;
            goldBonus += 10;
        }

        return { xp: xpBonus, gold: goldBonus };
    }

    calculateStreakBonus(playerId, matchResult) {
        // Calculate streak bonus based on current win streak
        return { xp: 0, gold: 0 }; // Implementation would fetch player streak data
    }

    getPlayerRewards(playerId) {
        return this.playerInventory.get(playerId) || {
            cosmetics: [],
            currency: { gold: 0, gems: 0 },
            inventory: []
        };
    }

    awardAchievementRewards(playerId, achievement) {
        const playerInventory = this.getPlayerRewards(playerId);

        if (achievement.rewards) {
            playerInventory.currency.gold += achievement.rewards.gold || 0;
            if (achievement.rewards.cosmetic) {
                playerInventory.cosmetics.push(achievement.rewards.cosmetic);
            }
        }

        this.playerInventory.set(playerId, playerInventory);
    }
}

/**
 * Tournament Qualification System
 */
class TournamentQualification {
    constructor() {
        this.qualifiedPlayers = new Map();
        this.tournamentThresholds = new Map();
        this.setupTournamentThresholds();
    }

    setupTournamentThresholds() {
        this.tournamentThresholds.set('regional', {
            minElo: 1500,
            minMatches: 50,
            topPlayersPerRegion: 100
        });

        this.tournamentThresholds.set('national', {
            minElo: 1800,
            minMatches: 100,
            topPlayersPerRegion: 50
        });

        this.tournamentThresholds.set('world', {
            minElo: 2200,
            minMatches: 200,
            topPlayersGlobal: 64
        });
    }

    updateQualification(playerId, playerData) {
        const qualificationStatus = {
            regional: this.checkRegionalQualification(playerId, playerData),
            national: this.checkNationalQualification(playerId, playerData),
            world: this.checkWorldQualification(playerId, playerData)
        };

        this.qualifiedPlayers.set(playerId, qualificationStatus);

        return qualificationStatus;
    }

    checkRegionalQualification(playerId, playerData) {
        const threshold = this.tournamentThresholds.get('regional');
        return {
            qualified: playerData.elo >= threshold.minElo &&
                      playerData.matchesPlayed >= threshold.minMatches,
            requirements: threshold
        };
    }

    checkNationalQualification(playerId, playerData) {
        const threshold = this.tournamentThresholds.get('national');
        return {
            qualified: playerData.elo >= threshold.minElo &&
                      playerData.matchesPlayed >= threshold.minMatches,
            requirements: threshold
        };
    }

    checkWorldQualification(playerId, playerData) {
        const threshold = this.tournamentThresholds.get('world');
        return {
            qualified: playerData.elo >= threshold.minElo &&
                      playerData.matchesPlayed >= threshold.minMatches,
            requirements: threshold
        };
    }

    isQualified(playerId, tournamentType = 'regional') {
        const qualification = this.qualifiedPlayers.get(playerId);
        return qualification && qualification[tournamentType]?.qualified;
    }

    processSeasonEnd(seasonData) {
        // Update tournament qualifications based on season performance
        this.updateSeasonalQualifications(seasonData);
    }

    updateSeasonalQualifications(seasonData) {
        // Implementation would update qualifications based on season rankings
    }
}

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

module.exports = {
    RankingSystem,
    LeagueSystem,
    SeasonManager,
    AchievementSystem,
    RewardManager,
    TournamentQualification
};