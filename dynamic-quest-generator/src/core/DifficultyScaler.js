import { QUEST_CONFIG } from '../../config/quest-config.js'

export class DifficultyScaler {
  constructor() {
    this.scalingFactors = {
      // Base difficulty multipliers
      healthMultiplier: 1.0,
      damageMultiplier: 1.0,
      rewardMultiplier: 1.0,
      experienceMultiplier: 1.0,
      objectiveMultiplier: 1.0,

      // Player skill scaling
      playerSkillWeight: 0.3,
      playerHistoryWeight: 0.2,
      playerPreferenceWeight: 0.2,

      // Dynamic scaling
      adaptiveThreshold: 0.8,
      maxDifficultyAdjustment: 2.0,
      minDifficultyAdjustment: 0.5
    }

    this.difficultyCurves = {
      linear: (level) => level,
      exponential: (level) => Math.pow(level, 1.5),
      logarithmic: (level) => Math.log(level + 1) * 10,
      sigmoid: (level) => 100 / (1 + Math.exp(-0.1 * (level - 50)))
    }
  }

  /**
   * Calculate quest difficulty based on player and context
   */
  calculateDifficulty(player, questType, questCategory, context = {}) {
    const baseDifficulty = this.getBaseDifficulty(player.stats.level, questType)
    const playerAdjustment = this.calculatePlayerDifficultyAdjustment(player, context)
    const contextAdjustment = this.calculateContextDifficultyAdjustment(context)
    const questTypeAdjustment = this.getQuestTypeDifficulty(questType)
    const categoryAdjustment = this.getCategoryDifficulty(questCategory)

    // Combine all factors
    let adjustedDifficulty = baseDifficulty +
      playerAdjustment +
      contextAdjustment +
      questTypeAdjustment +
      categoryAdjustment

    // Apply adaptive scaling
    adjustedDifficulty = this.applyAdaptiveScaling(adjustedDifficulty, player, context)

    // Clamp to valid range
    adjustedDifficulty = Math.max(1, Math.min(7, Math.round(adjustedDifficulty)))

    return adjustedDifficulty
  }

  /**
   * Calculate recommended difficulty for quest generation
   */
  recommendDifficulty(player, context) {
    const playerLevel = player.stats.level
    const completionRate = this.calculateCompletionRate(player)
    const averageRating = this.calculateAverageRating(player)
    const recentPerformance = this.getRecentPerformance(player, 5)

    // Base difficulty on player level
    let recommendedDifficulty = Math.floor(playerLevel / 15) + 1

    // Adjust based on performance
    if (completionRate > 0.8 && averageRating > 4) {
      recommendedDifficulty += 1
    } else if (completionRate < 0.5 || averageRating < 2.5) {
      recommendedDifficulty -= 1
    }

    // Adjust based on recent performance
    if (recentPerformance > 0.8) {
      recommendedDifficulty += 1
    } else if (recentPerformance < 0.3) {
      recommendedDifficulty -= 1
    }

    // Consider player preferences
    const preferredDifficulty = player.questPreferences.difficulty.preferred
    if (player.questPreferences.difficulty.adaptive) {
      // Blend recommended with preferred
      recommendedDifficulty = Math.round(
        recommendedDifficulty * 0.7 + preferredDifficulty * 0.3
      )
    }

    // Apply context adjustments
    if (context.partySize && context.partySize > 1) {
      recommendedDifficulty += Math.min(1, Math.floor(context.partySize / 3))
    }

    if (context.guildContext && context.guildContext.memberCount > 5) {
      recommendedDifficulty += 1
    }

    // Clamp to valid range
    return Math.max(1, Math.min(7, recommendedDifficulty))
  }

  /**
   * Scale quest parameters based on difficulty
   */
  scaleQuestParameters(quest, targetDifficulty) {
    const currentDifficulty = quest.difficulty
    const scalingRatio = targetDifficulty / currentDifficulty

    // Scale objectives
    quest.objectives = quest.objectives.map(objective => {
      const scaledObjective = { ...objective }

      if (typeof objective.required === 'number') {
        // Scale numeric requirements
        if (objective.type === QUEST_CONFIG.OBJECTIVE_TYPES.KILL) {
          scaledObjective.required = Math.max(1, Math.round(objective.required * scalingRatio))
        } else if (objective.type === QUEST_CONFIG.OBJECTIVE_TYPES.COLLECT) {
          scaledObjective.required = Math.max(1, Math.round(objective.required * scalingRatio))
        } else if (objective.type === QUEST_CONFIG.OBJECTIVE_TYPES.EXPLORE) {
          scaledObjective.required = Math.max(1, Math.round(objective.required * scalingRatio))
        }
      }

      // Add time pressure for higher difficulty
      if (targetDifficulty >= 5 && !objective.timeLimit) {
        scaledObjective.timeLimit = this.calculateTimeLimit(objective, targetDifficulty)
      }

      // Add hidden objectives for higher difficulty
      if (targetDifficulty >= 6 && Math.random() > 0.5) {
        scaledObjective.hidden = true
      }

      return scaledObjective
    })

    // Scale rewards
    quest.rewards = this.scaleRewards(quest.rewards, scalingRatio, targetDifficulty)

    // Update quest metadata
    quest.difficulty = targetDifficulty
    quest.levelRequirement = this.calculateLevelRequirement(targetDifficulty, quest.assignedTo)

    return quest
  }

  /**
   * Scale enemy parameters based on difficulty
   */
  scaleEnemyParameters(baseEnemy, targetDifficulty, playerLevel) {
    const scalingRatio = this.getEnemyScalingRatio(targetDifficulty, playerLevel)

    return {
      ...baseEnemy,
      health: Math.round(baseEnemy.health * scalingRatio.health),
      damage: Math.round(baseEnemy.damage * scalingRatio.damage),
      defense: Math.round(baseEnemy.defense * scalingRatio.defense),
      speed: Math.round(baseEnemy.speed * scalingRatio.speed),
      accuracy: Math.min(0.95, baseEnemy.accuracy * scalingRatio.accuracy),
      experienceReward: Math.round(baseEnemy.experienceReward * scalingRatio.experience),
      goldReward: Math.round(baseEnemy.goldReward * scalingRatio.gold),

      // Add special abilities for higher difficulty
      abilities: targetDifficulty >= 4
        ? [...(baseEnemy.abilities || []), ...this.generateEnemyAbilities(targetDifficulty)]
        : baseEnemy.abilities || [],

      // Add resistance for higher difficulty
      resistances: targetDifficulty >= 5
        ? this.generateEnemyResistances(targetDifficulty)
        : baseEnemy.resistances || []
    }
  }

  /**
   * Scale dungeon parameters based on difficulty
   */
  scaleDungeonParameters(baseDungeon, targetDifficulty, partySize = 1) {
    const scalingRatio = this.getDungeonScalingRatio(targetDifficulty, partySize)

    return {
      ...baseDungeon,
      numberOfRooms: Math.round(baseDungeon.numberOfRooms * scalingRatio.size),
      numberOfEnemies: Math.round(baseDungeon.numberOfEnemies * scalingRatio.enemies),
      numberOfTraps: Math.round(baseDungeon.numberOfTraps * scalingRatio.traps),
      numberOfPuzzles: Math.round(baseDungeon.numberOfPuzzles * scalingRatio.puzzles),

      // Scale enemy difficulty
      enemyDifficultyMultiplier: scalingRatio.enemyDifficulty,

      // Scale treasure
      treasureFrequency: Math.min(1.0, baseDungeon.treasureFrequency * scalingRatio.treasure),
      treasureQuality: Math.min(1.0, baseDungeon.treasureQuality * scalingRatio.quality),

      // Add environmental hazards for higher difficulty
      environmentalHazards: targetDifficulty >= 3
        ? this.generateEnvironmentalHazards(targetDifficulty)
        : [],

      // Add time limit for higher difficulty
      timeLimit: targetDifficulty >= 5
        ? this.calculateDungeonTimeLimit(baseDungeon, targetDifficulty, partySize)
        : null
    }
  }

  /**
   * Get base difficulty based on player level
   */
  getBaseDifficulty(playerLevel, questType) {
    const levelDifficulty = Math.floor(playerLevel / 10) + 1

    // Adjust for quest type
    const typeAdjustments = {
      [QUEST_CONFIG.QUEST_TYPES.TUTORIAL]: -2,
      [QUEST_CONFIG.QUEST_TYPES.DAILY]: -1,
      [QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST]: 0,
      [QUEST_CONFIG.QUEST_TYPES.MAIN_STORY]: 1,
      [QUEST_CONFIG.QUEST_TYPES.WEEKLY]: 1,
      [QUEST_CONFIG.QUEST_TYPES.EVENT]: 2,
      [QUEST_CONFIG.QUEST_TYPES.GUILD]: 1,
      [QUEST_CONFIG.QUEST_TYPES.RAID]: 3,
      [QUEST_CONFIG.QUEST_TYPES.PLAYER_GENERATED]: 0
    }

    const adjustment = typeAdjustments[questType] || 0
    return Math.max(1, Math.min(7, levelDifficulty + adjustment))
  }

  /**
   * Calculate player difficulty adjustment
   */
  calculatePlayerDifficultyAdjustment(player, context) {
    let adjustment = 0

    // Skill-based adjustment
    const skillScore = this.calculatePlayerSkillScore(player)
    adjustment += (skillScore - 0.5) * 2

    // History-based adjustment
    const performanceScore = this.calculatePerformanceScore(player)
    adjustment += (performanceScore - 0.5) * 1.5

    // Preference-based adjustment
    const preferenceScore = this.calculatePreferenceScore(player)
    adjustment += (preferenceScore - 0.5) * 1

    return adjustment
  }

  /**
   * Calculate context difficulty adjustment
   */
  calculateContextDifficultyAdjustment(context) {
    let adjustment = 0

    // Party size adjustment
    if (context.partySize) {
      if (context.partySize >= 4) {
        adjustment += 1
      } else if (context.partySize >= 2) {
        adjustment += 0.5
      }
    }

    // Guild context adjustment
    if (context.guildContext && context.guildContext.memberCount > 10) {
      adjustment += 0.5
    }

    // Time of day adjustment (players might be tired at night)
    const hour = new Date().getHours()
    if (hour >= 23 || hour <= 6) {
      adjustment -= 0.2
    }

    // World state adjustment
    if (context.worldState === 'crisis') {
      adjustment += 1
    } else if (context.worldState === 'peace') {
      adjustment -= 0.5
    }

    return adjustment
  }

  /**
   * Get quest type difficulty modifier
   */
  getQuestTypeDifficulty(questType) {
    const typeDifficulties = {
      [QUEST_CONFIG.QUEST_TYPES.TUTORIAL]: -2,
      [QUEST_CONFIG.QUEST_TYPES.DAILY]: -0.5,
      [QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST]: 0,
      [QUEST_CONFIG.QUEST_TYPES.MAIN_STORY]: 0.5,
      [QUEST_CONFIG.QUEST_TYPES.WEEKLY]: 0.5,
      [QUEST_CONFIG.QUEST_TYPES.EVENT]: 1,
      [QUEST_CONFIG.QUEST_TYPES.GUILD]: 0.5,
      [QUEST_CONFIG.QUEST_TYPES.RAID]: 2,
      [QUEST_CONFIG.QUEST_TYPES.PLAYER_GENERATED]: 0,
      [QUEST_CONFIG.QUEST_TYPES.HIDDEN]: 1
    }

    return typeDifficulties[questType] || 0
  }

  /**
   * Get category difficulty modifier
   */
  getCategoryDifficulty(category) {
    const categoryDifficulties = {
      [QUEST_CONFIG.CATEGORIES.TUTORIAL]: -2,
      [QUEST_CONFIG.CATEGORIES.COLLECTION]: -0.5,
      [QUEST_CONFIG.CATEGORIES.DELIVERY]: -0.5,
      [QUEST_CONFIG.CATEGORIES.SOCIAL]: 0,
      [QUEST_CONFIG.CATEGORIES.EXPLORATION]: 0,
      [QUEST_CONFIG.CATEGORIES.ESCORT]: 0.5,
      [QUEST_CONFIG.CATEGORIES.CRAFTING]: 0.5,
      [QUEST_CONFIG.CATEGORIES.MYSTERY]: 0.5,
      [QUEST_CONFIG.CATEGORIES.COMBAT]: 1,
      [QUEST_CONFIG.CATEGORIES.DUNGEON]: 1,
      [QUEST_CONFIG.CATEGORIES.BOSS_BATTLE]: 2
    }

    return categoryDifficulties[category] || 0
  }

  /**
   * Apply adaptive scaling
   */
  applyAdaptiveScaling(difficulty, player, context) {
    const recentPerformance = this.getRecentPerformance(player, 5)
    const completionRate = this.calculateCompletionRate(player)

    // If player is struggling, reduce difficulty
    if (recentPerformance < 0.3 || completionRate < 0.4) {
      difficulty *= 0.8
    }
    // If player is excelling, increase difficulty
    else if (recentPerformance > 0.8 && completionRate > 0.8) {
      difficulty *= 1.2
    }

    return difficulty
  }

  /**
   * Calculate player skill score
   */
  calculatePlayerSkillScore(player) {
    const levelScore = Math.min(1, player.stats.level / 100)
    const experienceScore = Math.min(1, player.stats.experience.total / 100000)
    const achievementsScore = Math.min(1, player.achievements.length / 50)

    return (levelScore + experienceScore + achievementsScore) / 3
  }

  /**
   * Calculate performance score
   */
  calculatePerformanceScore(player) {
    const completionRate = this.calculateCompletionRate(player)
    const averageRating = this.calculateAverageRating(player)
    const recentPerformance = this.getRecentPerformance(player, 10)

    return (completionRate + (averageRating / 5) + recentPerformance) / 3
  }

  /**
   * Calculate preference score
   */
  calculatePreferenceScore(player) {
    const preferences = player.questPreferences.types
    const avgPreference = Object.values(preferences).reduce((sum, pref) => sum + pref, 0) / Object.values(preferences).length
    return avgPreference
  }

  /**
   * Calculate completion rate
   */
  calculateCompletionRate(player) {
    const history = player.questHistory || []
    if (history.length === 0) return 0.5

    const completed = history.filter(q => q.completed).length
    return completed / history.length
  }

  /**
   * Calculate average rating
   */
  calculateAverageRating(player) {
    const ratedQuests = player.questHistory.filter(q => q.rating)
    if (ratedQuests.length === 0) return 3

    const totalRating = ratedQuests.reduce((sum, quest) => sum + quest.rating, 0)
    return totalRating / ratedQuests.length
  }

  /**
   * Get recent performance
   */
  getRecentPerformance(player, count = 5) {
    const recentQuests = player.questHistory.slice(-count)
    if (recentQuests.length === 0) return 0.5

    let performance = 0
    recentQuests.forEach(quest => {
      if (quest.completed) {
        performance += 0.5
        if (quest.rating) {
          performance += (quest.rating - 3) * 0.1
        }
      }
    })

    return Math.max(0, Math.min(1, performance / recentQuests.length))
  }

  /**
   * Scale rewards based on difficulty
   */
  scaleRewards(rewards, scalingRatio, difficulty) {
    const scaledRewards = { ...rewards }

    const scaleRewardArray = (rewardArray) => {
      return (rewardArray || []).map(reward => {
        const scaledReward = { ...reward }

        if (typeof reward.amount === 'number') {
          scaledReward.amount = Math.round(reward.amount * scalingRatio)
        }

        // Increase rarity chance for higher difficulty
        if (difficulty >= 5 && reward.rarity) {
          const rarityLevels = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic']
          const currentIndex = rarityLevels.indexOf(reward.rarity)
          if (currentIndex > 0 && Math.random() < (difficulty - 4) * 0.2) {
            scaledReward.rarity = rarityLevels[currentIndex - 1]
          }
        }

        return scaledReward
      })
    }

    scaledRewards.base = scaleRewardArray(rewards.base)
    scaledRewards.bonus = scaleRewardArray(rewards.bonus)

    if (rewards.choice && rewards.choice.options) {
      scaledRewards.choice = {
        ...rewards.choice,
        options: rewards.choice.options.map(option => ({
          ...option,
          rewards: scaleRewardArray(option.rewards)
        }))
      }
    }

    return scaledRewards
  }

  /**
   * Calculate time limit for objectives
   */
  calculateTimeLimit(objective, difficulty) {
    const baseTime = {
      [QUEST_CONFIG.OBJECTIVE_TYPES.KILL]: 10, // minutes
      [QUEST_CONFIG.OBJECTIVE_TYPES.COLLECT]: 15,
      [QUEST_CONFIG.OBJECTIVE_TYPES.EXPLORE]: 20,
      [QUEST_CONFIG.OBJECTIVE_TYPES.DELIVER]: 8,
      [QUEST_CONFIG.OBJECTIVE_TYPES.ESCORT]: 25,
      [QUEST_CONFIG.OBJECTIVE_TYPES.DEFEND]: 12,
      [QUEST_CONFIG.OBJECTIVE_TYPES.CRAFT]: 30,
      [QUEST_CONFIG.OBJECTIVE_TYPES.SOCIAL_INTERACTION]: 5
    }

    const baseMinutes = baseTime[objective.type] || 15
    const requiredMultiplier = Math.sqrt(objective.required || 1)
    const difficultyMultiplier = 1 + (difficulty - 3) * 0.1

    const totalMinutes = baseMinutes * requiredMultiplier * difficultyMultiplier
    return Math.round(totalMinutes * 60) // Convert to seconds
  }

  /**
   * Calculate level requirement for quest
   */
  calculateLevelRequirement(difficulty, assignedTo) {
    const baseLevel = Math.max(1, (difficulty - 1) * 10)

    if (assignedTo && assignedTo.length > 0) {
      // This would typically fetch player data
      // For now, use base level
    }

    return baseLevel
  }

  /**
   * Get enemy scaling ratio
   */
  getEnemyScalingRatio(targetDifficulty, playerLevel) {
    const difficultyMultiplier = 0.5 + (targetDifficulty / 7) * 1.5
    const levelMultiplier = 0.5 + (playerLevel / 100) * 1.5

    return {
      health: difficultyMultiplier * levelMultiplier,
      damage: difficultyMultiplier * levelMultiplier,
      defense: difficultyMultiplier * 0.8,
      speed: 1 + (targetDifficulty - 3) * 0.1,
      accuracy: Math.min(1.0, 0.5 + (targetDifficulty / 7) * 0.5),
      experience: difficultyMultiplier * levelMultiplier,
      gold: difficultyMultiplier * levelMultiplier
    }
  }

  /**
   * Get dungeon scaling ratio
   */
  getDungeonScalingRatio(targetDifficulty, partySize) {
    const difficultyMultiplier = 0.5 + (targetDifficulty / 7) * 1.5
    const partyMultiplier = Math.max(1, partySize * 0.8)

    return {
      size: 0.8 + difficultyMultiplier * 0.4,
      enemies: difficultyMultiplier * partyMultiplier,
      traps: 0.5 + difficultyMultiplier * 0.5,
      puzzles: 0.5 + difficultyMultiplier * 0.5,
      enemyDifficulty: difficultyMultiplier,
      treasure: 0.5 + difficultyMultiplier * 0.5,
      quality: 0.5 + difficultyMultiplier * 0.5
    }
  }

  /**
   * Generate enemy abilities based on difficulty
   */
  generateEnemyAbilities(difficulty) {
    const abilityPools = {
      4: ['enhanced_damage', 'defensive_stance', 'call_backup'],
      5: ['area_attack', 'debuff_attack', 'regeneration'],
      6: ['ultimate_attack', 'immune_to_damage', 'summon_minions'],
      7: ['unstoppable_rage', 'time_warp', 'instant_kill']
    }

    const pool = abilityPools[difficulty] || []
    const numAbilities = Math.min(2, Math.floor(difficulty / 3))

    return this.selectRandomItems(pool, numAbilities)
  }

  /**
   * Generate enemy resistances based on difficulty
   */
  generateEnemyResistances(difficulty) {
    const resistanceTypes = ['fire', 'ice', 'lightning', 'poison', 'holy', 'shadow', 'physical']
    const numResistances = Math.min(3, Math.floor(difficulty / 2))

    return this.selectRandomItems(resistanceTypes, numResistances).map(type => ({
      type,
      amount: Math.min(0.75, 0.25 + difficulty * 0.1)
    }))
  }

  /**
   * Generate environmental hazards based on difficulty
   */
  generateEnvironmentalHazards(difficulty) {
    const hazardPools = {
      3: ['spike_traps', 'pressure_plates'],
      4: ['poison_gas', 'falling_rocks', 'magic_barriers'],
      5: ['lava_pits', 'ice_storms', 'curses'],
      6: ['dimensional_rifts', 'time_anomalies', 'reality_distortions'],
      7: ['soul_drain', 'instant_death_traps', 'reality_collapses']
    }

    const pool = hazardPools[difficulty] || []
    const numHazards = Math.min(3, Math.floor(difficulty / 2))

    return this.selectRandomItems(pool, numHazards)
  }

  /**
   * Calculate dungeon time limit
   */
  calculateDungeonTimeLimit(dungeon, difficulty, partySize) {
    const baseTime = dungeon.numberOfRooms * 5 // 5 minutes per room
    const partyMultiplier = Math.max(0.7, 1 / (partySize * 0.8))
    const difficultyMultiplier = 1 + (difficulty - 3) * 0.2

    const totalMinutes = baseTime * partyMultiplier * difficultyMultiplier
    return Math.round(totalMinutes * 60) // Convert to seconds
  }

  /**
   * Select random items from array
   */
  selectRandomItems(array, count) {
    const shuffled = [...array].sort(() => Math.random() - 0.5)
    return shuffled.slice(0, Math.min(count, array.length))
  }

  /**
   * Get scaling statistics
   */
  getScalingStats() {
    return {
      scalingFactors: this.scalingFactors,
      difficultyCurves: Object.keys(this.difficultyCurves),
      maxDifficulty: 7,
      minDifficulty: 1,
      adaptiveThreshold: this.scalingFactors.adaptiveThreshold
    }
  }

  /**
   * Set scaling factor
   */
  setScalingFactor(factor, value) {
    if (this.scalingFactors.hasOwnProperty(factor)) {
      this.scalingFactors[factor] = value
      return true
    }
    return false
  }

  /**
   * Get difficulty curve
   */
  getDifficultyCurve(type = 'linear') {
    return this.difficultyCurves[type] || this.difficultyCurves.linear
  }

  /**
   * Set difficulty curve
   */
  setDifficultyCurve(type, formula) {
    if (typeof formula === 'function') {
      this.difficultyCurves[type] = formula
      return true
    }
    return false
  }
}

export default DifficultyScaler