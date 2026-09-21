import { Player } from '../database/models/Player.js'
import { Quest } from '../database/models/Quest.js'
import { QUEST_CONFIG } from '../../config/quest-config.js'

export class ContextAnalyzer {
  constructor() {
    this.contextCache = new Map()
    this.cacheTimeout = 5 * 60 * 1000 // 5 minutes
  }

  /**
   * Analyze player context for quest generation
   */
  async analyzePlayerContext(player) {
    try {
      // Check cache first
      const cacheKey = `player_${player._id}`
      const cached = this.contextCache.get(cacheKey)
      if (cached && (Date.now() - cached.timestamp) < this.cacheTimeout) {
        return cached.context
      }

      const context = {
        // Basic player information
        playerId: player._id,
        playerLevel: player.stats.level,
        playerClass: player.character.class,
        playerRace: player.character.race,
        playerBackground: player.character.background,
        playerAlignment: player.character.alignment,

        // Quest preferences
        preferences: player.questPreferences.types,
        questHistory: await this.analyzeQuestHistory(player),
        recentQuestTypes: this.getRecentQuestTypes(player),
        completionRate: this.calculateCompletionRate(player),

        // Skills and abilities
        skills: player.stats.skills,
        abilities: player.stats.abilities,
        attributes: player.stats.attributes,

        // Social context
        guildContext: await this.getGuildContext(player),
        partyContext: await this.getPartyContext(player),
        relationships: player.stats.relationships,
        reputation: player.stats.reputation,

        // Location and world state
        currentLocation: player.questContext.currentLocation || 'unknown',
        worldState: player.questContext.worldState || 'neutral',
        recentChoices: player.questContext.recentChoices || [],

        // Performance metrics
        averageCompletionTime: this.calculateAverageCompletionTime(player),
        averageRating: this.calculateAverageRating(player),
        favoriteQuestType: this.getFavoriteQuestType(player),
        favoriteDifficulty: this.getFavoriteDifficulty(player),

        // Personalization factors
        difficultyAdaptation: this.calculateDifficultyAdaptation(player),
        lengthAdaptation: this.calculateLengthAdaptation(player),
        complexityAdaptation: this.calculateComplexityAdaptation(player),

        // Behavioral patterns
        playPatterns: this.analyzePlayPatterns(player),
        timePatterns: this.analyzeTimePatterns(player),
        activityLevel: this.calculateActivityLevel(player),

        // Avoidances and preferences
        avoidContent: player.questPreferences.avoidContent || [],
        preferContent: player.questPreferences.preferContent || [],

        // Quest generation context
        generationCount: player.questContext.questGenerationCount || 0,
        lastGeneratedQuest: player.questContext.lastGeneratedQuest,
        preferredThemes: player.questContext.preferredThemes || [],
        avoidedThemes: player.questContext.avoidedThemes || []
      }

      // Cache the context
      this.contextCache.set(cacheKey, {
        context,
        timestamp: Date.now()
      })

      return context

    } catch (error) {
      console.error('Error analyzing player context:', error)
      return this.getDefaultContext(player)
    }
  }

  /**
   * Analyze guild context for group quests
   */
  async analyzeGuildContext(guildMembers) {
    try {
      if (!guildMembers || guildMembers.length === 0) {
        return this.getDefaultGuildContext()
      }

      const guildContext = {
        memberCount: guildMembers.length,
        averageLevel: guildMembers.reduce((sum, member) => sum + member.stats.level, 0) / guildMembers.length,
        classDistribution: this.calculateClassDistribution(guildMembers),
        raceDistribution: this.calculateRaceDistribution(guildMembers),
        totalExperience: guildMembers.reduce((sum, member) => sum + member.stats.experience.total, 0),
        combinedSkills: this.combineSkills(guildMembers),
        guildPreferences: this.calculateGuildPreferences(guildMembers),
        guildPlayStyle: this.determineGuildPlayStyle(guildMembers),
        availableRoles: this.calculateAvailableRoles(guildMembers),
        synergyScore: this.calculateGuildSynergy(guildMembers),
        recentGuildQuests: await this.getRecentGuildQuests(guildMembers),
        guildReputation: this.calculateGuildReputation(guildMembers)
      }

      return guildContext

    } catch (error) {
      console.error('Error analyzing guild context:', error)
      return this.getDefaultGuildContext()
    }
  }

  /**
   * Analyze player's quest history
   */
  async analyzeQuestHistory(player) {
    const history = player.questHistory || []
    const recentHistory = history.slice(-20) // Last 20 quests

    return {
      totalQuests: history.length,
      completedQuests: history.filter(q => q.completed).length,
      abandonedQuests: history.filter(q => q.abandoned).length,
      averageDifficulty: this.calculateAverageDifficulty(history),
      typeDistribution: this.calculateTypeDistribution(history),
      categoryDistribution: this.calculateCategoryDistribution(history),
      performanceTrends: this.analyzePerformanceTrends(recentHistory),
      ratingTrends: this.analyzeRatingTrends(recentHistory),
      timeTrends: this.analyzeTimeTrends(recentHistory),
      preferredLengths: this.getPreferredQuestLengths(history),
      successPatterns: this.identifySuccessPatterns(history),
      failurePatterns: this.identifyFailurePatterns(history)
    }
  }

  /**
   * Get recent quest types
   */
  getRecentQuestTypes(player) {
    const recentQuests = player.questHistory.slice(-10)
    return recentQuests.map(quest => quest.type).filter(Boolean)
  }

  /**
   * Calculate completion rate
   */
  calculateCompletionRate(player) {
    const history = player.questHistory || []
    if (history.length === 0) return 0.5 // Default for new players

    const completed = history.filter(q => q.completed).length
    return completed / history.length
  }

  /**
   * Get guild context
   */
  async getGuildContext(player) {
    if (!player.guildId) return null

    try {
      // This would typically fetch guild data from database
      return {
        id: player.guildId,
        rank: player.guildRank,
        memberCount: 0, // Would be fetched from guild collection
        activeMembers: [],
        guildLevel: 1,
        guildPerks: [],
        guildQuests: []
      }
    } catch (error) {
      console.error('Error getting guild context:', error)
      return null
    }
  }

  /**
   * Get party context
   */
  async getPartyContext(player) {
    if (!player.partyId) return null

    try {
      // This would typically fetch party data from database
      return {
        id: player.partyId,
        members: [],
        leader: null,
        activeQuests: [],
        partyLevel: 1
      }
    } catch (error) {
      console.error('Error getting party context:', error)
      return null
    }
  }

  /**
   * Calculate average completion time
   */
  calculateAverageCompletionTime(player) {
    const completedQuests = player.questHistory.filter(q => q.completed && q.completionTime)
    if (completedQuests.length === 0) return 30 // Default 30 minutes

    const totalTime = completedQuests.reduce((sum, quest) => sum + quest.completionTime, 0)
    return Math.round(totalTime / completedQuests.length / (1000 * 60)) // Convert to minutes
  }

  /**
   * Calculate average rating
   */
  calculateAverageRating(player) {
    const ratedQuests = player.questHistory.filter(q => q.rating)
    if (ratedQuests.length === 0) return 3 // Default rating

    const totalRating = ratedQuests.reduce((sum, quest) => sum + quest.rating, 0)
    return totalRating / ratedQuests.length
  }

  /**
   * Get favorite quest type
   */
  getFavoriteQuestType(player) {
    const typeCounts = {}
    player.questHistory.forEach(quest => {
      if (quest.type && quest.completed) {
        typeCounts[quest.type] = (typeCounts[quest.type] || 0) + 1
      }
    })

    let maxCount = 0
    let favoriteType = null
    Object.entries(typeCounts).forEach(([type, count]) => {
      if (count > maxCount) {
        maxCount = count
        favoriteType = type
      }
    })

    return favoriteType
  }

  /**
   * Get favorite difficulty
   */
  getFavoriteDifficulty(player) {
    const difficultyCounts = {}
    player.questHistory.forEach(quest => {
      if (quest.difficulty && quest.completed && quest.rating >= 4) {
        difficultyCounts[quest.difficulty] = (difficultyCounts[quest.difficulty] || 0) + 1
      }
    })

    let maxCount = 0
    let favoriteDifficulty = 3 // Default
    Object.entries(difficultyCounts).forEach(([difficulty, count]) => {
      if (count > maxCount) {
        maxCount = count
        favoriteDifficulty = parseInt(difficulty)
      }
    })

    return favoriteDifficulty
  }

  /**
   * Calculate difficulty adaptation
   */
  calculateDifficultyAdaptation(player) {
    const completionRate = this.calculateCompletionRate(player)
    const averageRating = this.calculateAverageRating(player)
    const recentPerformance = this.getRecentPerformance(player)

    // Adapt difficulty based on performance
    let adaptation = 1.0

    if (completionRate > 0.8 && averageRating > 4) {
      adaptation = 1.2 // Player is doing well, increase difficulty
    } else if (completionRate < 0.5 || averageRating < 2.5) {
      adaptation = 0.8 // Player is struggling, decrease difficulty
    } else if (recentPerformance > 0.7) {
      adaptation = 1.1 // Slight increase for good recent performance
    } else if (recentPerformance < 0.3) {
      adaptation = 0.9 // Slight decrease for poor recent performance
    }

    return Math.max(0.5, Math.min(1.5, adaptation))
  }

  /**
   * Calculate length adaptation
   */
  calculateLengthAdaptation(player) {
    const averageTime = this.calculateAverageCompletionTime(player)
    const preferredLength = player.questPreferences.questLength

    const lengthMultipliers = {
      'short': 0.6,
      'medium': 1.0,
      'long': 1.4,
      'epic': 1.8
    }

    let adaptation = lengthMultipliers[preferredLength] || 1.0

    // Adjust based on actual completion times
    if (averageTime < 15) {
      adaptation *= 0.8 // Player prefers shorter quests
    } else if (averageTime > 60) {
      adaptation *= 1.2 // Player can handle longer quests
    }

    return Math.max(0.4, Math.min(2.0, adaptation))
  }

  /**
   * Calculate complexity adaptation
   */
  calculateComplexityAdaptation(player) {
    const skillLevel = player.stats.level
    const questExperience = player.questHistory.length

    // New players get simpler quests
    if (skillLevel < 10 || questExperience < 5) {
      return 0.7
    }

    // Experienced players can handle complexity
    if (skillLevel > 30 && questExperience > 50) {
      return 1.3
    }

    return 1.0
  }

  /**
   * Analyze play patterns
   */
  analyzePlayPatterns(player) {
    const sessions = player.sessions || []
    const recentSessions = sessions.slice(-10)

    return {
      sessionFrequency: this.calculateSessionFrequency(recentSessions),
      averageSessionLength: this.calculateAverageSessionLength(recentSessions),
      preferredPlayTimes: this.getPreferredPlayTimes(recentSessions),
      questPerSession: this.calculateQuestsPerSession(recentSessions),
      socialActivity: this.analyzeSocialActivity(player),
      explorationTendency: this.calculateExplorationTendency(player),
      combatEngagement: this.calculateCombatEngagement(player),
      craftingInterest: this.calculateCraftingInterest(player)
    }
  }

  /**
   * Analyze time patterns
   */
  analyzeTimePatterns(player) {
    const sessions = player.sessions || []
    const timeAnalysis = {
      peakHours: [],
      peakDays: [],
      seasonalPatterns: [],
      timeSinceLastSession: 0,
      totalPlayTime: player.totalPlayTime || 0
    }

    if (sessions.length > 0) {
      const lastSession = sessions[sessions.length - 1]
      timeAnalysis.timeSinceLastSession = Date.now() - new Date(lastSession.endTime).getTime()

      // Analyze peak hours
      const hourCounts = new Array(24).fill(0)
      sessions.forEach(session => {
        const hour = new Date(session.startTime).getHours()
        hourCounts[hour]++
      })

      const maxCount = Math.max(...hourCounts)
      timeAnalysis.peakHours = hourCounts
        .map((count, hour) => ({ hour, count }))
        .filter(item => item.count >= maxCount * 0.8)
        .map(item => item.hour)
    }

    return timeAnalysis
  }

  /**
   * Calculate activity level
   */
  calculateActivityLevel(player) {
    const sessions = player.sessions || []
    const recentSessions = sessions.filter(session => {
      const sessionTime = new Date(session.startTime).getTime()
      const weekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000)
      return sessionTime > weekAgo
    })

    if (recentSessions.length === 0) return 'inactive'

    const totalRecentTime = recentSessions.reduce((sum, session) => sum + session.duration, 0)
    const averageDailyTime = totalRecentTime / 7

    if (averageDailyTime > 120 * 60) return 'very_active' // > 2 hours per day
    if (averageDailyTime > 60 * 60) return 'active' // > 1 hour per day
    if (averageDailyTime > 30 * 60) return 'moderately_active' // > 30 minutes per day
    return 'casually_active'
  }

  /**
   * Calculate class distribution
   */
  calculateClassDistribution(members) {
    const distribution = {}
    members.forEach(member => {
      const cls = member.character.class
      distribution[cls] = (distribution[cls] || 0) + 1
    })
    return distribution
  }

  /**
   * Calculate race distribution
   */
  calculateRaceDistribution(members) {
    const distribution = {}
    members.forEach(member => {
      const race = member.character.race
      distribution[race] = (distribution[race] || 0) + 1
    })
    return distribution
  }

  /**
   * Combine skills from all guild members
   */
  combineSkills(members) {
    const combinedSkills = {}
    members.forEach(member => {
      member.stats.skills.forEach(skill => {
        if (!combinedSkills[skill.id]) {
          combinedSkills[skill.id] = {
            name: skill.name,
            totalLevel: 0,
            maxLevel: 0,
            members: []
          }
        }
        combinedSkills[skill.id].totalLevel += skill.level
        combinedSkills[skill.id].maxLevel = Math.max(combinedSkills[skill.id].maxLevel, skill.level)
        combinedSkills[skill.id].members.push({
          id: member._id,
          name: member.character.name,
          level: skill.level
        })
      })
    })
    return combinedSkills
  }

  /**
   * Calculate guild preferences
   */
  calculateGuildPreferences(members) {
    const preferences = {
      combat: 0,
      exploration: 0,
      social: 0,
      mystery: 0,
      crafting: 0
    }

    members.forEach(member => {
      const prefs = member.questPreferences.types
      Object.keys(preferences).forEach(key => {
        preferences[key] += prefs[key] || 0.5
      })
    })

    // Average the preferences
    Object.keys(preferences).forEach(key => {
      preferences[key] = preferences[key] / members.length
    })

    return preferences
  }

  /**
   * Determine guild play style
   */
  determineGuildPlayStyle(members) {
    const playStyles = members.map(member => member.questPreferences.playStyle)
    const styleCounts = {}

    playStyles.forEach(style => {
      styleCounts[style] = (styleCounts[style] || 0) + 1
    })

    let maxCount = 0
    let dominantStyle = 'mixed'
    Object.entries(styleCounts).forEach(([style, count]) => {
      if (count > maxCount) {
        maxCount = count
        dominantStyle = style
      }
    })

    return dominantStyle
  }

  /**
   * Calculate available roles in guild
   */
  calculateAvailableRoles(members) {
    const roles = {
      tank: 0,
      healer: 0,
      damage: 0,
      support: 0,
      utility: 0
    }

    members.forEach(member => {
      const cls = member.character.class
      switch (cls) {
        case 'warrior':
        case 'paladin':
          roles.tank++
          roles.damage++
          break
        case 'cleric':
        case 'druid':
          roles.healer++
          roles.support++
          break
        case 'mage':
        case 'warlock':
        case 'ranger':
          roles.damage++
          break
        case 'rogue':
        case 'monk':
          roles.damage++
          roles.utility++
          break
        case 'bard':
          roles.support++
          roles.utility++
          break
      }
    })

    return roles
  }

  /**
   * Calculate guild synergy score
   */
  calculateGuildSynergy(members) {
    let synergyScore = 0

    // Class diversity bonus
    const uniqueClasses = new Set(members.map(m => m.character.class)).size
    synergyScore += uniqueClasses * 0.1

    // Role balance bonus
    const roles = this.calculateAvailableRoles(members)
    const roleBalance = Math.min(...Object.values(roles)) / Math.max(...Object.values(roles))
    synergyScore += roleBalance * 0.3

    // Average level coordination bonus
    const levels = members.map(m => m.stats.level)
    const avgLevel = levels.reduce((sum, level) => sum + level, 0) / levels.length
    const levelVariance = levels.reduce((sum, level) => sum + Math.pow(level - avgLevel, 2), 0) / levels.length
    synergyScore += Math.max(0, 0.2 - levelVariance / 100) // Lower variance = higher score

    // Guild activity bonus
    const activeMembers = members.filter(m => this.calculateActivityLevel(m) !== 'inactive').length
    synergyScore += (activeMembers / members.length) * 0.2

    return Math.min(1.0, synergyScore)
  }

  /**
   * Get recent guild quests
   */
  async getRecentGuildQuests(members) {
    // This would typically query the database for recent guild quests
    return []
  }

  /**
   * Calculate guild reputation
   */
  calculateGuildReputation(members) {
    const reputation = {}
    members.forEach(member => {
      member.stats.reputation.forEach(rep => {
        if (!reputation[rep.faction]) {
          reputation[rep.faction] = 0
        }
        reputation[rep.faction] += rep.standing
      })
    })

    // Average the reputation
    Object.keys(reputation).forEach(faction => {
      reputation[faction] = reputation[faction] / members.length
    })

    return reputation
  }

  /**
   * Calculate average difficulty from quest history
   */
  calculateAverageDifficulty(history) {
    if (history.length === 0) return 3

    const totalDifficulty = history.reduce((sum, quest) => sum + (quest.difficulty || 3), 0)
    return totalDifficulty / history.length
  }

  /**
   * Calculate type distribution from quest history
   */
  calculateTypeDistribution(history) {
    const distribution = {}
    history.forEach(quest => {
      if (quest.type) {
        distribution[quest.type] = (distribution[quest.type] || 0) + 1
      }
    })
    return distribution
  }

  /**
   * Calculate category distribution from quest history
   */
  calculateCategoryDistribution(history) {
    const distribution = {}
    history.forEach(quest => {
      if (quest.category) {
        distribution[quest.category] = (distribution[quest.category] || 0) + 1
      }
    })
    return distribution
  }

  /**
   * Analyze performance trends
   */
  analyzePerformanceTrends(recentHistory) {
    if (recentHistory.length < 5) return 'insufficient_data'

    const recent = recentHistory.slice(-5)
    const older = recentHistory.slice(-10, -5)

    const recentCompletionRate = recent.filter(q => q.completed).length / recent.length
    const olderCompletionRate = older.filter(q => q.completed).length / older.length

    if (recentCompletionRate > olderCompletionRate + 0.1) return 'improving'
    if (recentCompletionRate < olderCompletionRate - 0.1) return 'declining'
    return 'stable'
  }

  /**
   * Analyze rating trends
   */
  analyzeRatingTrends(recentHistory) {
    const ratedQuests = recentHistory.filter(q => q.rating)
    if (ratedQuests.length < 5) return 'insufficient_data'

    const recent = ratedQuests.slice(-3)
    const older = ratedQuests.slice(-6, -3)

    const recentAvg = recent.reduce((sum, q) => sum + q.rating, 0) / recent.length
    const olderAvg = older.reduce((sum, q) => sum + q.rating, 0) / older.length

    if (recentAvg > olderAvg + 0.5) return 'improving'
    if (recentAvg < olderAvg - 0.5) return 'declining'
    return 'stable'
  }

  /**
   * Analyze time trends
   */
  analyzeTimeTrends(recentHistory) {
    const completedQuests = recentHistory.filter(q => q.completed && q.completionTime)
    if (completedQuests.length < 5) return 'insufficient_data'

    const recent = completedQuests.slice(-3)
    const older = completedQuests.slice(-6, -3)

    const recentAvg = recent.reduce((sum, q) => sum + q.completionTime, 0) / recent.length
    const olderAvg = older.reduce((sum, q) => sum + q.completionTime, 0) / older.length

    if (recentAvg < olderAvg * 0.8) return 'getting_faster'
    if (recentAvg > olderAvg * 1.2) return 'getting_slower'
    return 'stable'
  }

  /**
   * Get preferred quest lengths
   */
  getPreferredQuestLengths(history) {
    const lengths = {
      short: 0,
      medium: 0,
      long: 0,
      epic: 0
    }

    history.forEach(quest => {
      if (!quest.completionTime) return

      const timeMinutes = quest.completionTime / (1000 * 60)
      if (timeMinutes < 20) lengths.short++
      else if (timeMinutes < 45) lengths.medium++
      else if (timeMinutes < 90) lengths.long++
      else lengths.epic++
    })

    return lengths
  }

  /**
   * Identify success patterns
   */
  identifySuccessPatterns(history) {
    const patterns = []

    // Analyze successful quest characteristics
    const successfulQuests = history.filter(q => q.completed && q.rating >= 4)

    if (successfulQuests.length > 0) {
      const types = {}
      const categories = {}
      const difficulties = {}

      successfulQuests.forEach(quest => {
        types[quest.type] = (types[quest.type] || 0) + 1
        categories[quest.category] = (categories[quest.category] || 0) + 1
        difficulties[quest.difficulty] = (difficulties[quest.difficulty] || 0) + 1
      })

      // Find most successful patterns
      const topType = Object.entries(types).sort(([,a], [,b]) => b - a)[0]
      const topCategory = Object.entries(categories).sort(([,a], [,b]) => b - a)[0]
      const topDifficulty = Object.entries(difficulties).sort(([,a], [,b]) => b - a)[0]

      if (topType) patterns.push({ type: 'quest_type', value: topType[0], confidence: topType[1] / successfulQuests.length })
      if (topCategory) patterns.push({ type: 'category', value: topCategory[0], confidence: topCategory[1] / successfulQuests.length })
      if (topDifficulty) patterns.push({ type: 'difficulty', value: parseInt(topDifficulty[0]), confidence: topDifficulty[1] / successfulQuests.length })
    }

    return patterns
  }

  /**
   * Identify failure patterns
   */
  identifyFailurePatterns(history) {
    const patterns = []

    // Analyze failed quest characteristics
    const failedQuests = history.filter(q => q.abandoned || (q.completed && q.rating <= 2))

    if (failedQuests.length > 0) {
      const types = {}
      const categories = {}
      const difficulties = {}

      failedQuests.forEach(quest => {
        types[quest.type] = (types[quest.type] || 0) + 1
        categories[quest.category] = (categories[quest.category] || 0) + 1
        difficulties[quest.difficulty] = (difficulties[quest.difficulty] || 0) + 1
      })

      // Find patterns in failures
      const topType = Object.entries(types).sort(([,a], [,b]) => b - a)[0]
      const topCategory = Object.entries(categories).sort(([,a], [,b]) => b - a)[0]
      const topDifficulty = Object.entries(difficulties).sort(([,a], [,b]) => b - a)[0]

      if (topType && topType[1] > failedQuests.length * 0.5) {
        patterns.push({ type: 'quest_type', value: topType[0], confidence: topType[1] / failedQuests.length })
      }
      if (topCategory && topCategory[1] > failedQuests.length * 0.5) {
        patterns.push({ type: 'category', value: topCategory[0], confidence: topCategory[1] / failedQuests.length })
      }
      if (topDifficulty && topDifficulty[1] > failedQuests.length * 0.5) {
        patterns.push({ type: 'difficulty', value: parseInt(topDifficulty[0]), confidence: topDifficulty[1] / failedQuests.length })
      }
    }

    return patterns
  }

  /**
   * Get recent performance score
   */
  getRecentPerformance(player) {
    const recentQuests = player.questHistory.slice(-5)
    if (recentQuests.length === 0) return 0.5

    let score = 0
    recentQuests.forEach(quest => {
      if (quest.completed) {
        score += 0.5
        if (quest.rating) {
          score += (quest.rating - 3) * 0.1
        }
      }
    })

    return Math.max(0, Math.min(1, score / recentQuests.length))
  }

  /**
   * Calculate session frequency
   */
  calculateSessionFrequency(sessions) {
    if (sessions.length < 2) return 0

    const intervals = []
    for (let i = 1; i < sessions.length; i++) {
      const interval = new Date(sessions[i].startTime).getTime() - new Date(sessions[i-1].startTime).getTime()
      intervals.push(interval)
    }

    const avgInterval = intervals.reduce((sum, interval) => sum + interval, 0) / intervals.length
    return avgInterval // Return average time between sessions in milliseconds
  }

  /**
   * Calculate average session length
   */
  calculateAverageSessionLength(sessions) {
    if (sessions.length === 0) return 0

    const totalLength = sessions.reduce((sum, session) => sum + session.duration, 0)
    return totalLength / sessions.length
  }

  /**
   * Get preferred play times
   */
  getPreferredPlayTimes(sessions) {
    const hourCounts = new Array(24).fill(0)
    sessions.forEach(session => {
      const hour = new Date(session.startTime).getHours()
      hourCounts[hour]++
    })

    const maxCount = Math.max(...hourCounts)
    return hourCounts
      .map((count, hour) => ({ hour, count }))
      .filter(item => item.count >= maxCount * 0.7)
      .map(item => item.hour)
  }

  /**
   * Calculate quests per session
   */
  calculateQuestsPerSession(sessions) {
    if (sessions.length === 0) return 0

    const totalQuests = sessions.reduce((sum, session) => sum + (session.questsCompleted || 0), 0)
    return totalQuests / sessions.length
  }

  /**
   * Analyze social activity
   */
  analyzeSocialActivity(player) {
    const guildActivity = player.guildId ? 1 : 0
    const partyActivity = player.partyId ? 1 : 0
    const friendActivity = Math.min(1, (player.friends || []).length / 10)

    return (guildActivity + partyActivity + friendActivity) / 3
  }

  /**
   * Calculate exploration tendency
   */
  calculateExplorationTendency(player) {
    const explorationQuests = player.questHistory.filter(q =>
      q.category === 'exploration' && q.completed
    ).length

    const totalQuests = player.questHistory.filter(q => q.completed).length
    if (totalQuests === 0) return 0.5

    return Math.min(1, explorationQuests / (totalQuests * 0.3))
  }

  /**
   * Calculate combat engagement
   */
  calculateCombatEngagement(player) {
    const combatQuests = player.questHistory.filter(q =>
      q.category === 'combat' && q.completed
    ).length

    const totalQuests = player.questHistory.filter(q => q.completed).length
    if (totalQuests === 0) return 0.5

    return Math.min(1, combatQuests / (totalQuests * 0.3))
  }

  /**
   * Calculate crafting interest
   */
  calculateCraftingInterest(player) {
    const craftingQuests = player.questHistory.filter(q =>
      q.category === 'crafting' && q.completed
    ).length

    const totalQuests = player.questHistory.filter(q => q.completed).length
    if (totalQuests === 0) return 0.5

    return Math.min(1, craftingQuests / (totalQuests * 0.2))
  }

  /**
   * Get default context for player
   */
  getDefaultContext(player) {
    return {
      playerId: player._id,
      playerLevel: player.stats.level,
      playerClass: player.character.class,
      playerRace: player.character.race,
      preferences: {
        combat: 0.5,
        exploration: 0.5,
        social: 0.5,
        mystery: 0.5,
        crafting: 0.5
      },
      questHistory: { totalQuests: 0 },
      recentQuestTypes: [],
      completionRate: 0.5,
      difficultyAdaptation: 1.0,
      lengthAdaptation: 1.0,
      complexityAdaptation: 1.0,
      activityLevel: 'moderately_active'
    }
  }

  /**
   * Get default guild context
   */
  getDefaultGuildContext() {
    return {
      memberCount: 1,
      averageLevel: 10,
      classDistribution: {},
      raceDistribution: {},
      combinedSkills: {},
      guildPreferences: {
        combat: 0.5,
        exploration: 0.5,
        social: 0.5,
        mystery: 0.5,
        crafting: 0.5
      },
      guildPlayStyle: 'mixed',
      availableRoles: {
        tank: 0,
        healer: 0,
        damage: 0,
        support: 0,
        utility: 0
      },
      synergyScore: 0.5
    }
  }

  /**
   * Clear context cache
   */
  clearCache() {
    this.contextCache.clear()
  }

  /**
   * Clean expired cache entries
   */
  cleanCache() {
    const now = Date.now()
    for (const [key, value] of this.contextCache.entries()) {
      if (now - value.timestamp > this.cacheTimeout) {
        this.contextCache.delete(key)
      }
    }
  }
}

export default ContextAnalyzer