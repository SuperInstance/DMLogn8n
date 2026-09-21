import { Quest } from '../database/models/Quest.js'
import { Player } from '../database/models/Player.js'
import { QUEST_CONFIG } from '../../config/quest-config.js'
import { QuestGenerationEngine } from '../core/QuestGenerationEngine.js'
import { DifficultyScaler } from '../core/DifficultyScaler.js'
import { RewardCalculator } from '../core/RewardCalculator.js'
import { EventEmitter } from 'events'

export class QuestManager extends EventEmitter {
  constructor() {
    super()
    this.generationEngine = new QuestGenerationEngine()
    this.difficultyScaler = new DifficultyScaler()
    this.rewardCalculator = new RewardCalculator()
    this.questCache = new Map()
    this.playerQuestCache = new Map()
    this.achievementTracker = new Map()

    // Initialize quest tracking
    this.activeQuests = new Map()
    this.questTimers = new Map()

    // Set up event handlers
    this.setupEventHandlers()

    // Start maintenance tasks
    this.startMaintenanceTasks()
  }

  /**
   * Assign a quest to a player
   */
  async assignQuestToPlayer(questId, playerId, options = {}) {
    try {
      // Get quest and player
      const quest = await Quest.findOne({ id: questId })
      const player = await Player.findOne({ _id: playerId })

      if (!quest) {
        throw new Error(`Quest ${questId} not found`)
      }

      if (!player) {
        throw new Error(`Player ${playerId} not found`)
      }

      // Check if player can accept quest
      if (!quest.canBeAssigned(player)) {
        throw new Error('Player does not meet quest requirements')
      }

      // Check if player already has this quest
      if (quest.assignedTo.includes(player._id)) {
        throw new Error('Player already has this quest')
      }

      // Check player's active quest limit
      const activeQuests = await this.getPlayerActiveQuests(playerId)
      if (activeQuests.length >= QUEST_CONFIG.GENERATION.MAX_QUESTS_PER_PLAYER) {
        throw new Error('Player has reached maximum active quest limit')
      }

      // Assign quest to player
      quest.assignedTo.push(player._id)
      quest.state = QUEST_CONFIG.STATES.IN_PROGRESS
      quest.startTime = new Date()

      // Add to player's active quests
      player.addQuest(quest)

      // Update quest tracking
      this.activeQuests.set(`${questId}_${playerId}`, {
        questId,
        playerId,
        startTime: new Date(),
        progress: 0,
        lastActivity: new Date()
      })

      // Save changes
      await quest.save()
      await player.save()

      // Update cache
      this.updateQuestCache(quest)
      this.updatePlayerQuestCache(playerId, quest)

      // Set up quest timers if needed
      this.setupQuestTimers(quest, playerId)

      // Emit events
      this.emit('questAssigned', { quest, player })
      this.emit('playerActivity', { playerId, activity: 'quest_assigned', questId })

      // Trigger n8n workflow
      await this.triggerQuestAssignedWorkflow(quest, player)

      return {
        success: true,
        quest,
        message: 'Quest assigned successfully'
      }

    } catch (error) {
      console.error('Error assigning quest to player:', error)
      this.emit('questAssignmentError', { questId, playerId, error })
      throw error
    }
  }

  /**
   * Update quest progress
   */
  async updateQuestProgress(questId, playerId, objectiveId, progress, data = {}) {
    try {
      const cacheKey = `${questId}_${playerId}`
      const questProgress = this.activeQuests.get(cacheKey)

      if (!questProgress) {
        throw new Error('Quest not found in active tracking')
      }

      // Get quest from database
      const quest = await Quest.findOne({ id: questId, assignedTo: playerId })
      if (!quest) {
        throw new Error('Quest not found')
      }

      // Update objective progress
      const updated = quest.updateProgress(objectiveId, progress)
      if (!updated) {
        throw new Error('Failed to update quest progress')
      }

      // Update player quest progress
      const player = await Player.findOne({ _id: playerId })
      player.updateQuestProgress(questId, quest.progress, objectiveId)

      // Update tracking
      questProgress.progress = quest.progress
      questProgress.lastActivity = new Date()

      // Check for quest completion
      if (quest.state === QUEST_CONFIG.STATES.COMPLETED) {
        await this.completeQuest(questId, playerId, data)
      } else {
        // Save progress
        await quest.save()
        await player.save()

        // Update cache
        this.updateQuestCache(quest)
        this.updatePlayerQuestCache(playerId, quest)

        // Emit progress event
        this.emit('questProgressUpdated', { quest, player, objectiveId, progress })
        this.emit('playerActivity', { playerId, activity: 'quest_progress', questId, progress })
      }

      return {
        success: true,
        quest,
        progress: quest.progress,
        completed: quest.state === QUEST_CONFIG.STATES.COMPLETED
      }

    } catch (error) {
      console.error('Error updating quest progress:', error)
      this.emit('questProgressError', { questId, playerId, error })
      throw error
    }
  }

  /**
   * Complete a quest
   */
  async completeQuest(questId, playerId, completionData = {}) {
    try {
      const quest = await Quest.findOne({ id: questId, assignedTo: playerId })
      const player = await Player.findOne({ _id: playerId })

      if (!quest || !player) {
        throw new Error('Quest or player not found')
      }

      // Calculate completion time
      const cacheKey = `${questId}_${playerId}`
      const questProgress = this.activeQuests.get(cacheKey)
      const completionTime = questProgress
        ? Date.now() - questProgress.startTime.getTime()
        : 0

      // Complete quest
      quest.state = QUEST_CONFIG.STATES.COMPLETED
      quest.endTime = new Date()
      quest.stats.completed = new Date()
      quest.stats.completionTime = completionTime
      quest.stats.attempts += 1

      // Update player
      const rating = completionData.rating || 0
      const feedback = completionData.feedback || ''
      player.completeQuest(questId, rating, feedback)

      // Calculate and distribute rewards
      const rewards = await this.calculateAndDistributeRewards(quest, player, completionData)

      // Update achievements
      await this.updateAchievements(player, quest, rewards)

      // Remove from active tracking
      this.activeQuests.delete(cacheKey)
      if (this.questTimers.has(cacheKey)) {
        clearTimeout(this.questTimers.get(cacheKey))
        this.questTimers.delete(cacheKey)
      }

      // Save changes
      await quest.save()
      await player.save()

      // Update cache
      this.updateQuestCache(quest)
      this.updatePlayerQuestCache(playerId, quest, true) // true = remove from active

      // Emit completion events
      this.emit('questCompleted', { quest, player, rewards, completionTime })
      this.emit('playerActivity', { playerId, activity: 'quest_completed', questId, rewards })
      this.emit('rewardsDistributed', { player, rewards, questId })

      // Trigger n8n workflow
      await this.triggerQuestCompletedWorkflow(quest, player, rewards)

      // Clean up cache
      this.cleanupQuestData(questId, playerId)

      return {
        success: true,
        quest,
        rewards,
        completionTime,
        message: 'Quest completed successfully'
      }

    } catch (error) {
      console.error('Error completing quest:', error)
      this.emit('questCompletionError', { questId, playerId, error })
      throw error
    }
  }

  /**
   * Abandon a quest
   */
  async abandonQuest(questId, playerId, reason = '') {
    try {
      const quest = await Quest.findOne({ id: questId, assignedTo: playerId })
      const player = await Player.findOne({ _id: playerId })

      if (!quest || !player) {
        throw new Error('Quest or player not found')
      }

      // Update quest state
      quest.state = QUEST_CONFIG.STATES.ABANDONED
      quest.endTime = new Date()
      quest.stats.abandonment.count += 1
      if (reason) {
        quest.stats.abandonment.reasons.push(reason)
      }

      // Update player
      player.abandonQuest(questId, reason)

      // Remove from active tracking
      const cacheKey = `${questId}_${playerId}`
      this.activeQuests.delete(cacheKey)
      if (this.questTimers.has(cacheKey)) {
        clearTimeout(this.questTimers.get(cacheKey))
        this.questTimers.delete(cacheKey)
      }

      // Save changes
      await quest.save()
      await player.save()

      // Update cache
      this.updateQuestCache(quest)
      this.updatePlayerQuestCache(playerId, quest, true)

      // Emit events
      this.emit('questAbandoned', { quest, player, reason })
      this.emit('playerActivity', { playerId, activity: 'quest_abandoned', questId, reason })

      // Trigger n8n workflow
      await this.triggerQuestAbandonedWorkflow(quest, player, reason)

      // Clean up cache
      this.cleanupQuestData(questId, playerId)

      return {
        success: true,
        quest,
        message: 'Quest abandoned successfully'
      }

    } catch (error) {
      console.error('Error abandoning quest:', error)
      this.emit('questAbandonmentError', { questId, playerId, error })
      throw error
    }
  }

  /**
   * Make a choice in a branching quest
   */
  async makeQuestChoice(questId, playerId, objectiveId, choiceId) {
    try {
      const quest = await Quest.findOne({ id: questId, assignedTo: playerId })
      const player = await Player.findOne({ _id: playerId })

      if (!quest || !player) {
        throw new Error('Quest or player not found')
      }

      // Make the choice
      const success = quest.makeChoice(objectiveId, choiceId, player)
      if (!success) {
        throw new Error('Failed to make quest choice')
      }

      // Update quest tracking
      const cacheKey = `${questId}_${playerId}`
      const questProgress = this.activeQuests.get(cacheKey)
      if (questProgress) {
        questProgress.lastActivity = new Date()
      }

      // Save changes
      await quest.save()
      await player.save()

      // Update cache
      this.updateQuestCache(quest)

      // Emit events
      this.emit('questChoiceMade', { quest, player, objectiveId, choiceId })
      this.emit('playerActivity', { playerId, activity: 'quest_choice', questId, objectiveId, choiceId })

      return {
        success: true,
        quest,
        choice: choiceId,
        nextObjective: quest.currentObjective,
        consequences: quest.branching.pathHistory[quest.branching.pathHistory.length - 1]
      }

    } catch (error) {
      console.error('Error making quest choice:', error)
      this.emit('questChoiceError', { questId, playerId, error })
      throw error
    }
  }

  /**
   * Get player's active quests
   */
  async getPlayerActiveQuests(playerId) {
    try {
      // Check cache first
      const cached = this.playerQuestCache.get(playerId)
      if (cached && Date.now() - cached.timestamp < 60000) { // 1 minute cache
        return cached.quests
      }

      // Fetch from database
      const quests = await Quest.find({
        assignedTo: playerId,
        state: { $in: [QUEST_CONFIG.STATES.ACTIVE, QUEST_CONFIG.STATES.IN_PROGRESS] }
      }).sort({ 'stats.created': -1 })

      // Update cache
      this.playerQuestCache.set(playerId, {
        quests,
        timestamp: Date.now()
      })

      return quests

    } catch (error) {
      console.error('Error getting player active quests:', error)
      return []
    }
  }

  /**
   * Get player's quest history
   */
  async getPlayerQuestHistory(playerId, options = {}) {
    try {
      const { limit = 20, offset = 0, type, state, sortBy = 'endTime', sortOrder = -1 } = options

      const query = { assignedTo: playerId }

      if (type) query.type = type
      if (state) query.state = state

      const quests = await Quest.find(query)
        .sort({ [sortBy]: sortOrder })
        .limit(limit)
        .skip(offset)
        .lean()

      return quests

    } catch (error) {
      console.error('Error getting player quest history:', error)
      return []
    }
  }

  /**
   * Get available quests for player
   */
  async getAvailableQuests(playerId, options = {}) {
    try {
      const player = await Player.findOne({ _id: playerId })
      if (!player) {
        throw new Error('Player not found')
      }

      const { type, category, difficulty, limit = 10 } = options

      const query = {
        state: QUEST_CONFIG.STATES.ACTIVE,
        levelRequirement: { $lte: player.stats.level },
        $or: [
          { maxLevel: { $exists: false } },
          { maxLevel: { $gte: player.stats.level } }
        ]
      }

      if (type) query.type = type
      if (category) query.category = category
      if (difficulty) query.difficulty = difficulty

      // Filter out quests player already has
      const playerQuestIds = player.questHistory.map(q => q.questId)
      const activeQuestIds = player.activeQuests.map(q => q.questId)
      const excludedIds = [...playerQuestIds, ...activeQuestIds]

      query._id = { $nin: excludedIds }

      const quests = await Quest.find(query)
        .limit(limit)
        .sort({ 'stats.created': -1 })
        .lean()

      // Filter by prerequisites
      const availableQuests = quests.filter(quest => {
        return quest.prerequisites.every(prereq => player.meetsPrerequisite(prereq))
      })

      return availableQuests

    } catch (error) {
      console.error('Error getting available quests:', error)
      return []
    }
  }

  /**
   * Generate personalized quest for player
   */
  async generatePersonalizedQuest(playerId, options = {}) {
    try {
      const player = await Player.findOne({ _id: playerId })
      if (!player) {
        throw new Error('Player not found')
      }

      // Check cooldown
      if (!this.generationEngine.checkGenerationCooldown(player)) {
        throw new Error('Quest generation cooldown not met')
      }

      // Generate quest
      const quest = await this.generationEngine.generateQuest(player, options)

      return {
        success: true,
        quest,
        message: 'Personalized quest generated successfully'
      }

    } catch (error) {
      console.error('Error generating personalized quest:', error)
      throw error
    }
  }

  /**
   * Calculate and distribute rewards
   */
  async calculateAndDistributeRewards(quest, player, completionData) {
    try {
      // Calculate base rewards
      const rewards = this.rewardCalculator.calculateRewards(quest, player)

      // Apply bonuses based on performance
      const performanceBonus = this.calculatePerformanceBonus(quest, player, completionData)
      rewards.bonus.push(...performanceBonus)

      // Apply choice rewards if applicable
      if (quest.rewards.choice.enabled && completionData.choice) {
        const choiceReward = quest.rewards.choice.options.find(option => option.id === completionData.choice)
        if (choiceReward) {
          rewards.choice = choiceReward.rewards
        }
      }

      // Distribute rewards to player
      await this.distributeRewards(player, rewards)

      return rewards

    } catch (error) {
      console.error('Error calculating and distributing rewards:', error)
      throw error
    }
  }

  /**
   * Calculate performance bonus
   */
  calculatePerformanceBonus(quest, player, completionData) {
    const bonuses = []

    // Speed bonus
    if (quest.stats.completionTime && quest.stats.completionTime < 30 * 60 * 1000) { // Less than 30 minutes
      bonuses.push({
        type: QUEST_CONFIG.REWARD_TYPES.GOLD,
        amount: Math.round(quest.totalRewards * 0.1),
        description: 'Speed completion bonus'
      })
    }

    // Perfect completion bonus
    if (quest.completionPercentage === 100) {
      bonuses.push({
        type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE,
        amount: Math.round(quest.totalRewards * 0.15),
        description: 'Perfect completion bonus'
      })
    }

    // High difficulty bonus
    if (quest.difficulty >= 5) {
      bonuses.push({
        type: QUEST_CONFIG.REWARD_TYPES.REPUTATION,
        amount: 50,
        faction: 'Adventurers Guild',
        description: 'High difficulty achievement bonus'
      })
    }

    // Rating bonus
    if (completionData.rating >= 5) {
      bonuses.push({
        type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE,
        amount: Math.round(quest.totalRewards * 0.2),
        description: 'Excellent rating bonus'
      })
    }

    return bonuses
  }

  /**
   * Distribute rewards to player
   */
  async distributeRewards(player, rewards) {
    const allRewards = [
      ...(rewards.base || []),
      ...(rewards.bonus || []),
      ...(rewards.choice || [])
    ]

    for (const reward of allRewards) {
      switch (reward.type) {
        case QUEST_CONFIG.REWARD_TYPES.EXPERIENCE:
          player.addExperience(reward.amount)
          break

        case QUEST_CONFIG.REWARD_TYPES.GOLD:
          player.stats.resources.gold += reward.amount
          break

        case QUEST_CONFIG.REWARD_TYPES.REPUTATION:
          const existingRep = player.stats.reputation.find(r => r.faction === reward.faction)
          if (existingRep) {
            existingRep.standing += reward.amount
          } else {
            player.stats.reputation.push({
              faction: reward.faction,
              standing: reward.amount
            })
          }
          break

        case QUEST_CONFIG.REWARD_TYPES.ITEM:
        case QUEST_CONFIG.REWARD_TYPES.EQUIPMENT:
          player.stats.inventory.push({
            id: reward.id || `item_${Date.now()}`,
            name: reward.name,
            quantity: reward.amount || 1,
            rarity: reward.rarity || 'common',
            category: reward.category || 'misc',
            value: reward.value || 0
          })
          break

        case QUEST_CONFIG.REWARD_TYPES.SKILL_POINT:
          // This would depend on the skill system implementation
          break

        case QUEST_CONFIG.REWARD_TYPES.TITLE:
          // This would depend on the title system implementation
          break

        case QUEST_CONFIG.REWARD_TYPES.ABILITY:
          // This would depend on the ability system implementation
          break
      }
    }
  }

  /**
   * Update achievements
   */
  async updateAchievements(player, quest, rewards) {
    // This would integrate with an achievement system
    // For now, just emit events
    this.emit('achievementCheck', { player, quest, rewards })
  }

  /**
   * Setup quest timers
   */
  setupQuestTimers(quest, playerId) {
    if (!quest.timeLimit) return

    const cacheKey = `${quest.id}_${playerId}`
    const timeLimitMs = quest.timeLimit * 60 * 1000 // Convert minutes to milliseconds

    const timer = setTimeout(async () => {
      try {
        // Quest has expired
        await this.expireQuest(quest.id, playerId)
      } catch (error) {
        console.error('Error expiring quest:', error)
      }
    }, timeLimitMs)

    this.questTimers.set(cacheKey, timer)
  }

  /**
   * Expire a quest
   */
  async expireQuest(questId, playerId) {
    try {
      const quest = await Quest.findOne({ id: questId, assignedTo: playerId })
      const player = await Player.findOne({ _id: playerId })

      if (!quest || !player) return

      // Update quest state
      quest.state = QUEST_CONFIG.STATES.EXPIRED
      quest.endTime = new Date()

      // Update player
      player.abandonQuest(questId, 'expired')

      // Remove from active tracking
      const cacheKey = `${questId}_${playerId}`
      this.activeQuests.delete(cacheKey)
      this.questTimers.delete(cacheKey)

      // Save changes
      await quest.save()
      await player.save()

      // Emit events
      this.emit('questExpired', { quest, player })

    } catch (error) {
      console.error('Error expiring quest:', error)
    }
  }

  /**
   * Update quest cache
   */
  updateQuestCache(quest) {
    this.questCache.set(quest.id, {
      quest,
      timestamp: Date.now()
    })
  }

  /**
   * Update player quest cache
   */
  updatePlayerQuestCache(playerId, quest, remove = false) {
    const cached = this.playerQuestCache.get(playerId)
    if (!cached) return

    if (remove) {
      cached.quests = cached.quests.filter(q => q.id !== quest.id)
    } else {
      const existingIndex = cached.quests.findIndex(q => q.id === quest.id)
      if (existingIndex >= 0) {
        cached.quests[existingIndex] = quest.toObject ? quest.toObject() : quest
      } else {
        cached.quests.push(quest.toObject ? quest.toObject() : quest)
      }
    }

    cached.timestamp = Date.now()
  }

  /**
   * Clean up quest data
   */
  cleanupQuestData(questId, playerId) {
    const cacheKey = `${questId}_${playerId}`
    this.activeQuests.delete(cacheKey)
    this.questTimers.delete(cacheKey)
  }

  /**
   * Setup event handlers
   */
  setupEventHandlers() {
    // Quest state changes
    this.on('questAssigned', (data) => {
      console.log(`Quest ${data.quest.id} assigned to player ${data.player._id}`)
    })

    this.on('questCompleted', (data) => {
      console.log(`Quest ${data.quest.id} completed by player ${data.player._id}`)
    })

    this.on('questAbandoned', (data) => {
      console.log(`Quest ${data.quest.id} abandoned by player ${data.player._id}`)
    })

    // Player activity
    this.on('playerActivity', (data) => {
      // This could be used for analytics or logging
    })

    // Error handling
    this.on('questAssignmentError', (data) => {
      console.error('Quest assignment error:', data.error)
    })

    this.on('questProgressError', (data) => {
      console.error('Quest progress error:', data.error)
    })

    this.on('questCompletionError', (data) => {
      console.error('Quest completion error:', data.error)
    })
  }

  /**
   * Start maintenance tasks
   */
  startMaintenanceTasks() {
    // Clean up expired quests every minute
    setInterval(async () => {
      await this.cleanupExpiredQuests()
    }, 60 * 1000)

    // Clean up cache every 5 minutes
    setInterval(() => {
      this.cleanupCache()
    }, 5 * 60 * 1000)

    // Update analytics every hour
    setInterval(async () => {
      await this.updateAnalytics()
    }, 60 * 60 * 1000)
  }

  /**
   * Clean up expired quests
   */
  async cleanupExpiredQuests() {
    try {
      const expiredQuests = await Quest.find({
        state: QUEST_CONFIG.STATES.IN_PROGRESS,
        endTime: { $lt: new Date() }
      })

      for (const quest of expiredQuests) {
        for (const playerId of quest.assignedTo) {
          await this.expireQuest(quest.id, playerId.toString())
        }
      }
    } catch (error) {
      console.error('Error cleaning up expired quests:', error)
    }
  }

  /**
   * Clean up cache
   */
  cleanupCache() {
    const now = Date.now()
    const cacheTimeout = 5 * 60 * 1000 // 5 minutes

    // Clean quest cache
    for (const [key, value] of this.questCache.entries()) {
      if (now - value.timestamp > cacheTimeout) {
        this.questCache.delete(key)
      }
    }

    // Clean player quest cache
    for (const [key, value] of this.playerQuestCache.entries()) {
      if (now - value.timestamp > cacheTimeout) {
        this.playerQuestCache.delete(key)
      }
    }
  }

  /**
   * Update analytics
   */
  async updateAnalytics() {
    try {
      // This would update quest analytics and statistics
      console.log('Updating quest analytics...')
    } catch (error) {
      console.error('Error updating analytics:', error)
    }
  }

  /**
   * Trigger n8n workflows
   */
  async triggerQuestAssignedWorkflow(quest, player) {
    if (!process.env.N8N_WEBHOOK_URL) return

    try {
      await fetch(`${process.env.N8N_WEBHOOK_URL}/quest-assigned`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          questId: quest.id,
          playerId: player._id,
          questType: quest.type,
          timestamp: new Date().toISOString()
        })
      })
    } catch (error) {
      console.error('Error triggering quest assigned workflow:', error)
    }
  }

  async triggerQuestCompletedWorkflow(quest, player, rewards) {
    if (!process.env.N8N_WEBHOOK_URL) return

    try {
      await fetch(`${process.env.N8N_WEBHOOK_URL}/quest-completed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          questId: quest.id,
          playerId: player._id,
          questType: quest.type,
          difficulty: quest.difficulty,
          completionTime: quest.stats.completionTime,
          rewards: rewards,
          timestamp: new Date().toISOString()
        })
      })
    } catch (error) {
      console.error('Error triggering quest completed workflow:', error)
    }
  }

  async triggerQuestAbandonedWorkflow(quest, player, reason) {
    if (!process.env.N8N_WEBHOOK_URL) return

    try {
      await fetch(`${process.env.N8N_WEBHOOK_URL}/quest-abandoned`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          questId: quest.id,
          playerId: player._id,
          questType: quest.type,
          reason,
          timestamp: new Date().toISOString()
        })
      })
    } catch (error) {
      console.error('Error triggering quest abandoned workflow:', error)
    }
  }

  /**
   * Get quest statistics
   */
  async getQuestStatistics(options = {}) {
    try {
      const { timeframe = '24h', playerId } = options

      const timeFilter = this.getTimeFilter(timeframe)
      const matchQuery = { 'stats.created': { $gte: timeFilter } }
      if (playerId) {
        matchQuery.assignedTo = playerId
      }

      const stats = await Quest.aggregate([
        { $match: matchQuery },
        {
          $group: {
            _id: null,
            totalQuests: { $sum: 1 },
            completedQuests: {
              $sum: { $cond: [{ $eq: ['$state', QUEST_CONFIG.STATES.COMPLETED] }, 1, 0] }
            },
            abandonedQuests: {
              $sum: { $cond: [{ $eq: ['$state', QUEST_CONFIG.STATES.ABANDONED] }, 1, 0] }
            },
            averageDifficulty: { $avg: '$difficulty' },
            averageCompletionTime: { $avg: '$stats.completionTime' },
            totalRewards: { $sum: { $sum: ['$rewards.base.amount', '$rewards.bonus.amount'] } }
          }
        }
      ])

      return stats[0] || {
        totalQuests: 0,
        completedQuests: 0,
        abandonedQuests: 0,
        averageDifficulty: 0,
        averageCompletionTime: 0,
        totalRewards: 0
      }

    } catch (error) {
      console.error('Error getting quest statistics:', error)
      return null
    }
  }

  /**
   * Get time filter for statistics
   */
  getTimeFilter(timeframe) {
    const now = new Date()
    switch (timeframe) {
      case '1h':
        return new Date(now.getTime() - 60 * 60 * 1000)
      case '24h':
        return new Date(now.getTime() - 24 * 60 * 60 * 1000)
      case '7d':
        return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      case '30d':
        return new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      default:
        return new Date(now.getTime() - 24 * 60 * 60 * 1000)
    }
  }

  /**
   * Get active quest tracking data
   */
  getActiveQuestData() {
    return {
      totalActiveQuests: this.activeQuests.size,
      activeTimers: this.questTimers.size,
      questCacheSize: this.questCache.size,
      playerCacheSize: this.playerQuestCache.size
    }
  }

  /**
   * Shutdown quest manager
   */
  async shutdown() {
    // Clear all timers
    for (const timer of this.questTimers.values()) {
      clearTimeout(timer)
    }
    this.questTimers.clear()

    // Clear caches
    this.questCache.clear()
    this.playerQuestCache.clear()
    this.activeQuests.clear()

    // Remove all listeners
    this.removeAllListeners()

    console.log('Quest Manager shutdown complete')
  }
}

export default QuestManager