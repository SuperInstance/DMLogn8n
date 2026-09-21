import { v4 as uuidv4 } from 'uuid'
import { QUEST_CONFIG } from '../../config/quest-config.js'
import { Quest } from '../database/models/Quest.js'
import { Player } from '../database/models/Player.js'
import { AIQuestGenerator } from '../ai/AIQuestGenerator.js'
import { QuestTemplateEngine } from './QuestTemplateEngine.js'
import { ContextAnalyzer } from '../context/ContextAnalyzer.js'
import { DifficultyScaler } from './DifficultyScaler.js'
import { RewardCalculator } from './RewardCalculator.js'

export class QuestGenerationEngine {
  constructor() {
    this.aiGenerator = new AIQuestGenerator()
    this.templateEngine = new QuestTemplateEngine()
    this.contextAnalyzer = new ContextAnalyzer()
    this.difficultyScaler = new DifficultyScaler()
    this.rewardCalculator = new RewardCalculator()
    this.generationCache = new Map()
  }

  /**
   * Generate a personalized quest for a player
   */
  async generateQuest(player, options = {}) {
    try {
      // Validate player
      if (!player || !player._id) {
        throw new Error('Valid player required for quest generation')
      }

      // Extract generation context
      const context = await this.contextAnalyzer.analyzePlayerContext(player)

      // Determine quest type and category
      const questType = options.type || this.determineQuestType(context)
      const category = options.category || this.determineQuestCategory(context)

      // Calculate difficulty
      const difficulty = options.difficulty ||
        this.difficultyScaler.calculateDifficulty(player, questType, category)

      // Check generation cooldown
      if (!this.checkGenerationCooldown(player)) {
        throw new Error('Quest generation cooldown not met')
      }

      // Generate quest using AI or templates
      const questData = await this.generateQuestContent({
        player,
        context,
        type: questType,
        category,
        difficulty,
        ...options
      })

      // Create quest object
      const quest = await this.createQuestObject(questData, player, context)

      // Save quest to database
      await quest.save()

      // Update player context
      await this.updatePlayerContext(player, quest)

      // Trigger n8n workflow for quest generation
      await this.triggerQuestGenerationWorkflow(quest, player)

      return quest

    } catch (error) {
      console.error('Error generating quest:', error)
      throw error
    }
  }

  /**
   * Generate multiple quests for batch operations
   */
  async generateMultipleQuests(player, count = 3, options = {}) {
    const quests = []
    const usedTypes = new Set()

    for (let i = 0; i < count; i++) {
      try {
        // Ensure variety in quest types
        const availableTypes = Object.values(QUEST_CONFIG.QUEST_TYPES)
          .filter(type => !usedTypes.has(type))

        const questType = availableTypes.length > 0
          ? availableTypes[Math.floor(Math.random() * availableTypes.length)]
          : Object.values(QUEST_CONFIG.QUEST_TYPES)[Math.floor(Math.random() * Object.values(QUEST_CONFIG.QUEST_TYPES).length)]

        usedTypes.add(questType)

        const quest = await this.generateQuest(player, {
          ...options,
          type: questType,
          batchGeneration: true
        })

        quests.push(quest)
      } catch (error) {
        console.error(`Error generating quest ${i + 1}:`, error)
        continue
      }
    }

    return quests
  }

  /**
   * Generate daily quests for players
   */
  async generateDailyQuests(player) {
    const dailyQuests = []
    const dailyOptions = {
      type: QUEST_CONFIG.QUEST_TYPES.DAILY,
      difficulty: Math.min(player.stats.level / 10 + 2, 5),
      personalized: true
    }

    // Generate 2-3 daily quests
    const questCount = Math.floor(Math.random() * 2) + 2

    for (let i = 0; i < questCount; i++) {
      try {
        const quest = await this.generateQuest(player, {
          ...dailyOptions,
          category: this.getWeightedCategory(player.questPreferences.types)
        })
        dailyQuests.push(quest)
      } catch (error) {
        console.error(`Error generating daily quest ${i + 1}:`, error)
      }
    }

    return dailyQuests
  }

  /**
   * Generate guild quests
   */
  async generateGuildQuest(guildId, guildMembers, options = {}) {
    try {
      // Analyze guild composition
      const guildContext = await this.contextAnalyzer.analyzeGuildContext(guildMembers)

      // Determine appropriate difficulty for guild
      const avgLevel = guildMembers.reduce((sum, member) => sum + member.stats.level, 0) / guildMembers.length
      const difficulty = Math.min(Math.floor(avgLevel / 10 + 1), 6)

      // Generate guild quest
      const questData = await this.generateQuestContent({
        type: QUEST_CONFIG.QUEST_TYPES.GUILD,
        category: this.getWeightedCategory(guildContext.preferences),
        difficulty,
        guildContext,
        partySize: guildMembers.length,
        ...options
      })

      // Create quest object
      const quest = await this.createQuestObject(questData, null, guildContext)
      quest.guildId = guildId
      quest.assignedTo = guildMembers.map(member => member._id)

      await quest.save()
      return quest

    } catch (error) {
      console.error('Error generating guild quest:', error)
      throw error
    }
  }

  /**
   * Determine quest type based on context
   */
  determineQuestType(context) {
    const weights = {
      [QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST]: 0.4,
      [QUEST_CONFIG.QUEST_TYPES.EXPLORATION]: 0.2,
      [QUEST_CONFIG.QUEST_TYPES.COMBAT]: 0.15,
      [QUEST_CONFIG.QUEST_TYPES.SOCIAL]: 0.1,
      [QUEST_CONFIG.QUEST_TYPES.MYSTERY]: 0.1,
      [QUEST_CONFIG.QUEST_TYPES.CRAFTING]: 0.05
    }

    // Adjust weights based on player preferences
    if (context.preferences) {
      if (context.preferences.combat > 0.7) {
        weights[QUEST_CONFIG.QUEST_TYPES.COMBAT] += 0.2
      }
      if (context.preferences.exploration > 0.7) {
        weights[QUEST_CONFIG.QUEST_TYPES.EXPLORATION] += 0.2
      }
      if (context.preferences.social > 0.7) {
        weights[QUEST_CONFIG.QUEST_TYPES.SOCIAL] += 0.2
      }
      if (context.preferences.mystery > 0.7) {
        weights[QUEST_CONFIG.QUEST_TYPES.MYSTERY] += 0.2
      }
      if (context.preferences.crafting > 0.7) {
        weights[QUEST_CONFIG.QUEST_TYPES.CRAFTING] += 0.2
      }
    }

    // Adjust weights based on recent quest history
    if (context.recentQuestTypes) {
      const recentTypes = context.recentQuestTypes.slice(-5)
      recentTypes.forEach(type => {
        weights[type] = (weights[type] || 0) * 0.7 // Reduce weight for recently completed types
      })
    }

    // Normalize weights
    const totalWeight = Object.values(weights).reduce((sum, weight) => sum + weight, 0)
    Object.keys(weights).forEach(key => {
      weights[key] = weights[key] / totalWeight
    })

    // Select random type based on weights
    const random = Math.random()
    let cumulative = 0
    for (const [type, weight] of Object.entries(weights)) {
      cumulative += weight
      if (random <= cumulative) {
        return type
      }
    }

    return QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST
  }

  /**
   * Determine quest category based on context
   */
  determineQuestCategory(context) {
    return this.getWeightedCategory(context.preferences || {})
  }

  /**
   * Get weighted category based on preferences
   */
  getWeightedCategory(preferences) {
    const categories = Object.values(QUEST_CONFIG.CATEGORIES)
    const weights = categories.map(category => {
      switch (category) {
        case QUEST_CONFIG.CATEGORIES.COMBAT:
          return preferences.combat || 0.5
        case QUEST_CONFIG.CATEGORIES.EXPLORATION:
          return preferences.exploration || 0.5
        case QUEST_CONFIG.CATEGORIES.SOCIAL:
          return preferences.social || 0.5
        case QUEST_CONFIG.CATEGORIES.MYSTERY:
          return preferences.mystery || 0.5
        case QUEST_CONFIG.CATEGORIES.CRAFTING:
          return preferences.crafting || 0.5
        default:
          return 0.5
      }
    })

    // Add some randomness
    weights.forEach((weight, index) => {
      weights[index] = weight * 0.7 + Math.random() * 0.3
    })

    // Select category based on weights
    const totalWeight = weights.reduce((sum, weight) => sum + weight, 0)
    const random = Math.random() * totalWeight
    let cumulative = 0

    for (let i = 0; i < categories.length; i++) {
      cumulative += weights[i]
      if (random <= cumulative) {
        return categories[i]
      }
    }

    return categories[0]
  }

  /**
   * Generate quest content using AI or templates
   */
  async generateQuestContent(params) {
    const { player, context, type, category, difficulty, guildContext, partySize } = params

    // Try to generate with AI first
    try {
      if (this.shouldUseAI(params)) {
        const aiContent = await this.aiGenerator.generateQuest({
          player,
          context,
          type,
          category,
          difficulty,
          guildContext,
          partySize
        })
        return aiContent
      }
    } catch (error) {
      console.warn('AI generation failed, falling back to templates:', error.message)
    }

    // Fall back to template-based generation
    return await this.templateEngine.generateQuest({
      player,
      context,
      type,
      category,
      difficulty,
      guildContext,
      partySize
    })
  }

  /**
   * Determine if AI should be used for generation
   */
  shouldUseAI(params) {
    // Use AI for personalized quests
    if (params.personalized) return true

    // Use AI for complex quest types
    if ([QUEST_CONFIG.QUEST_TYPES.MAIN_STORY, QUEST_CONFIG.QUEST_TYPES.EVENT].includes(params.type)) {
      return true
    }

    // Use AI for high difficulty quests
    if (params.difficulty >= 5) return true

    // Use AI based on configuration
    return process.env.AI_GENERATION_ENABLED !== 'false'
  }

  /**
   * Create quest object from generated content
   */
  async createQuestObject(questData, player, context) {
    const questId = Quest.generateId()

    const quest = new Quest({
      id: questId,
      title: questData.title,
      description: questData.description,
      summary: questData.summary,
      type: questData.type,
      category: questData.category,
      difficulty: questData.difficulty,
      levelRequirement: questData.levelRequirement,

      // Story content
      story: questData.story,
      dialogue: questData.dialogue,
      lore: questData.lore,

      // Objectives
      objectives: questData.objectives || [],

      // Rewards
      rewards: {
        base: questData.rewards || [],
        bonus: questData.bonusRewards || [],
        choice: questData.rewardChoice || { enabled: false, options: [] }
      },

      // State
      state: QUEST_CONFIG.STATES.ACTIVE,
      active: true,

      // Prerequisites
      prerequisites: questData.prerequisites || [],

      // Player assignment
      assignedTo: player ? [player._id] : [],

      // Generation metadata
      generatedBy: questData.generatedBy || 'ai',
      generationContext: {
        playerLevel: player ? player.stats.level : null,
        playerClass: player ? player.character.class : null,
        partyComposition: context.partyComposition || [],
        worldState: context.worldState || 'neutral',
        preferences: context.preferences || {},
        seed: questData.seed || uuidv4(),
        template: questData.template || null
      },

      // Personalization
      personalized: !!player,
      personalizationData: {
        playerHistory: player ? player.questHistory.map(q => q.questId) : [],
        preferences: player ? player.questPreferences.types : {},
        adaptations: {
          difficulty: context.difficultyAdaptation || 1.0,
          length: context.lengthAdaptation || 1.0,
          complexity: context.complexityAdaptation || 1.0
        }
      },

      // Branching
      branching: {
        enabled: questData.branching || false,
        currentPath: null,
        completedPaths: [],
        availablePaths: questData.availablePaths || [],
        pathHistory: []
      },

      // Social features
      social: {
        shareable: true,
        leaderboard: questData.leaderboard || false,
        achievements: questData.achievements || [],
        milestones: []
      },

      // World impact
      worldImpact: questData.worldImpact || {
        reputation: [],
        relationships: [],
        worldState: [],
        unlocks: []
      },

      // Quality control
      review: {
        status: 'pending',
        reviewedBy: null,
        reviewedAt: null,
        feedback: null,
        flags: []
      },

      // Metadata
      tags: questData.tags || [],
      source: questData.source || 'generated',
      template: questData.template || null,
      aiGenerated: questData.aiGenerated || false,
      aiModel: questData.aiModel || null,
      aiPrompt: questData.aiPrompt || null,
      aiConfidence: questData.aiConfidence || null
    })

    return quest
  }

  /**
   * Check if player can generate new quest (cooldown)
   */
  checkGenerationCooldown(player) {
    const lastGeneration = player.questContext.lastGeneratedQuest
    if (!lastGeneration) return true

    const cooldownHours = QUEST_CONFIG.GENERATION.COOLDOWN_HOURS.GENERATION
    const cooldownMs = cooldownHours * 60 * 60 * 1000
    const timeSinceLastGeneration = Date.now() - new Date(lastGeneration).getTime()

    return timeSinceLastGeneration >= cooldownMs
  }

  /**
   * Update player context after quest generation
   */
  async updatePlayerContext(player, quest) {
    player.questContext.lastGeneratedQuest = new Date()

    // Add to preferred themes if quest was well-received (simplified logic)
    if (Math.random() > 0.7) {
      if (!player.questContext.preferredThemes.includes(quest.category)) {
        player.questContext.preferredThemes.push(quest.category)
      }
    }

    await player.save()
  }

  /**
   * Trigger n8n workflow for quest generation
   */
  async triggerQuestGenerationWorkflow(quest, player) {
    if (!process.env.N8N_WEBHOOK_URL) return

    try {
      const response = await fetch(`${process.env.N8N_WEBHOOK_URL}/quest-generated`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.N8N_API_KEY || ''}`
        },
        body: JSON.stringify({
          questId: quest.id,
          playerId: player._id,
          questType: quest.type,
          difficulty: quest.difficulty,
          timestamp: new Date().toISOString(),
          aiGenerated: quest.aiGenerated
        })
      })

      if (!response.ok) {
        console.warn('Failed to trigger n8n workflow:', response.statusText)
      }
    } catch (error) {
      console.error('Error triggering n8n workflow:', error)
    }
  }

  /**
   * Generate personalized quest recommendations
   */
  async generateQuestRecommendations(player, count = 5) {
    const context = await this.contextAnalyzer.analyzePlayerContext(player)
    const recommendations = []

    // Analyze quest history for patterns
    const completedQuests = player.questHistory.filter(q => q.completed)
    const preferences = this.analyzeQuestPreferences(completedQuests)

    for (let i = 0; i < count; i++) {
      try {
        const recommendation = {
          type: this.determineQuestType(context),
          category: this.getWeightedCategory(preferences),
          difficulty: this.difficultyScaler.recommendDifficulty(player, context),
          estimatedTime: this.estimateQuestCompletionTime(context),
          reasons: this.generateRecommendationReasons(context, preferences)
        }
        recommendations.push(recommendation)
      } catch (error) {
        console.error(`Error generating recommendation ${i + 1}:`, error)
      }
    }

    return recommendations
  }

  /**
   * Analyze player quest preferences from history
   */
  analyzeQuestPreferences(questHistory) {
    if (!questHistory || questHistory.length === 0) {
      return {
        combat: 0.5,
        exploration: 0.5,
        social: 0.5,
        mystery: 0.5,
        crafting: 0.5
      }
    }

    const preferences = {
      combat: 0,
      exploration: 0,
      social: 0,
      mystery: 0,
      crafting: 0
    }

    const typeCounts = {}
    let totalQuests = 0

    questHistory.forEach(quest => {
      if (quest.type) {
        typeCounts[quest.type] = (typeCounts[quest.type] || 0) + 1
        totalQuests++
      }

      // Also consider rating if available
      if (quest.rating && quest.rating >= 4) {
        // Weight preferred types higher
        if (quest.type) {
          typeCounts[quest.type] = (typeCounts[quest.type] || 0) + 1
        }
      }
    })

    // Map quest types to preferences
    const typeToPreference = {
      [QUEST_CONFIG.QUEST_TYPES.COMBAT]: 'combat',
      [QUEST_CONFIG.QUEST_TYPES.EXPLORATION]: 'exploration',
      [QUEST_CONFIG.QUEST_TYPES.SOCIAL]: 'social',
      [QUEST_CONFIG.QUEST_TYPES.MYSTERY]: 'mystery',
      [QUEST_CONFIG.QUEST_TYPES.CRAFTING]: 'crafting'
    }

    // Calculate preference scores
    Object.entries(typeCounts).forEach(([type, count]) => {
      const preference = typeToPreference[type]
      if (preference) {
        preferences[preference] += count
      }
    })

    // Normalize and add default values
    Object.keys(preferences).forEach(key => {
      preferences[key] = (preferences[key] / totalQuests) || 0.5
    })

    return preferences
  }

  /**
   * Estimate quest completion time based on context
   */
  estimateQuestCompletionTime(context) {
    const baseTime = 30 // minutes
    const difficultyMultiplier = context.difficultyLevel || 1
    const complexityMultiplier = context.complexityAdaptation || 1
    const playerSkillMultiplier = Math.max(0.5, 2 - (context.playerLevel / 50))

    return Math.floor(baseTime * difficultyMultiplier * complexityMultiplier * playerSkillMultiplier)
  }

  /**
   * Generate reasons for quest recommendations
   */
  generateRecommendationReasons(context, preferences) {
    const reasons = []

    // Find highest preference
    const highestPreference = Object.entries(preferences)
      .sort(([,a], [,b]) => b - a)[0]

    if (highestPreference && highestPreference[1] > 0.6) {
      reasons.push(`Matches your preference for ${highestPreference[0]} quests`)
    }

    // Check player level
    if (context.playerLevel) {
      if (context.playerLevel < 10) {
        reasons.push('Suitable for new adventurers')
      } else if (context.playerLevel > 50) {
        reasons.push('Challenging content for experienced players')
      }
    }

    // Check recent activity
    if (context.recentActivity) {
      if (context.recentActivity.includes('combat')) {
        reasons.push('Good balance with your recent activities')
      }
    }

    return reasons.length > 0 ? reasons : ['Personalized for your playstyle']
  }

  /**
   * Clear generation cache
   */
  clearCache() {
    this.generationCache.clear()
  }

  /**
   * Get generation statistics
   */
  getGenerationStats() {
    return {
      cacheSize: this.generationCache.size,
      aiEnabled: process.env.AI_GENERATION_ENABLED !== 'false',
      supportedTypes: Object.values(QUEST_CONFIG.QUEST_TYPES),
      supportedCategories: Object.values(QUEST_CONFIG.CATEGORIES)
    }
  }
}

export default QuestGenerationEngine