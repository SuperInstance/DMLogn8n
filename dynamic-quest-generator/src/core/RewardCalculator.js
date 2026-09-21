import { QUEST_CONFIG } from '../../config/quest-config.js'

export class RewardCalculator {
  constructor() {
    this.baseRewardMultipliers = {
      [QUEST_CONFIG.REWARD_TYPES.EXPERIENCE]: 100,
      [QUEST_CONFIG.REWARD_TYPES.GOLD]: 50,
      [QUEST_CONFIG.REWARD_TYPES.REPUTATION]: 25,
      [QUEST_CONFIG.REWARD_TYPES.SKILL_POINT]: 0.1,
      [QUEST_CONFIG.REWARD_TYPES.ABILITY]: 0.05,
      [QUEST_CONFIG.REWARD_TYPES.TITLE]: 0.02,
      [QUEST_CONFIG.REWARD_TYPES.ITEM]: 0.3,
      [QUEST_CONFIG.REWARD_TYPES.EQUIPMENT]: 0.2
    }

    this.difficultyMultipliers = {
      1: 0.5,
      2: 0.75,
      3: 1.0,
      4: 1.5,
      5: 2.0,
      6: 3.0,
      7: 5.0
    }

    this.questTypeMultipliers = {
      [QUEST_CONFIG.QUEST_TYPES.TUTORIAL]: 0.5,
      [QUEST_CONFIG.QUEST_TYPES.DAILY]: 0.8,
      [QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST]: 1.0,
      [QUEST_CONFIG.QUEST_TYPES.MAIN_STORY]: 1.5,
      [QUEST_CONFIG.QUEST_TYPES.WEEKLY]: 1.3,
      [QUEST_CONFIG.QUEST_TYPES.EVENT]: 1.8,
      [QUEST_CONFIG.QUEST_TYPES.GUILD]: 1.4,
      [QUEST_CONFIG.QUEST_TYPES.RAID]: 2.5,
      [QUEST_CONFIG.QUEST_TYPES.PLAYER_GENERATED]: 0.9
    }

    this.categoryMultipliers = {
      [QUEST_CONFIG.CATEGORIES.COLLECTION]: 0.8,
      [QUEST_CONFIG.CATEGORIES.DELIVERY]: 0.7,
      [QUEST_CONFIG.CATEGORIES.SOCIAL]: 0.9,
      [QUEST_CONFIG.CATEGORIES.EXPLORATION]: 1.0,
      [QUEST_CONFIG.CATEGORIES.ESCORT]: 1.1,
      [QUEST_CONFIG.CATEGORIES.CRAFTING]: 1.0,
      [QUEST_CONFIG.CATEGORIES.MYSTERY]: 1.2,
      [QUEST_CONFIG.CATEGORIES.COMBAT]: 1.1,
      [QUEST_CONFIG.CATEGORIES.DUNGEON]: 1.3,
      [QUEST_CONFIG.CATEGORIES.BOSS_BATTLE]: 1.5
    }

    this.rarityChances = {
      common: 0.6,
      uncommon: 0.25,
      rare: 0.1,
      epic: 0.04,
      legendary: 0.008,
      mythic: 0.002
    }
  }

  /**
   * Calculate rewards for a quest completion
   */
  calculateRewards(quest, player, performance = {}) {
    try {
      const rewards = {
        base: [],
        bonus: [],
        choice: quest.rewards.choice || { enabled: false, options: [] }
      }

      // Calculate base rewards
      rewards.base = this.calculateBaseRewards(quest, player)

      // Calculate bonus rewards based on performance
      rewards.bonus = this.calculateBonusRewards(quest, player, performance)

      // Apply multipliers
      rewards = this.applyRewardMultipliers(rewards, quest, player)

      // Add random rewards based on luck
      rewards = this.addRandomRewards(rewards, quest, player)

      // Normalize rewards
      rewards = this.normalizeRewards(rewards, quest)

      return rewards

    } catch (error) {
      console.error('Error calculating rewards:', error)
      return {
        base: [],
        bonus: [],
        choice: { enabled: false, options: [] }
      }
    }
  }

  /**
   * Calculate base rewards
   */
  calculateBaseRewards(quest, player) {
    const baseRewards = []
    const baseMultiplier = this.getBaseRewardMultiplier(quest)

    // Experience reward
    const experienceReward = this.calculateExperienceReward(quest, player, baseMultiplier)
    if (experienceReward.amount > 0) {
      baseRewards.push(experienceReward)
    }

    // Gold reward
    const goldReward = this.calculateGoldReward(quest, player, baseMultiplier)
    if (goldReward.amount > 0) {
      baseRewards.push(goldReward)
    }

    // Reputation reward
    const reputationReward = this.calculateReputationReward(quest, player, baseMultiplier)
    if (reputationReward.amount > 0) {
      baseRewards.push(reputationReward)
    }

    // Skill point rewards
    const skillReward = this.calculateSkillReward(quest, player, baseMultiplier)
    if (skillReward.amount > 0) {
      baseRewards.push(skillReward)
    }

    // Item/equipment rewards
    const itemRewards = this.calculateItemRewards(quest, player, baseMultiplier)
    baseRewards.push(...itemRewards)

    return baseRewards
  }

  /**
   * Calculate bonus rewards based on performance
   */
  calculateBonusRewards(quest, player, performance) {
    const bonusRewards = []

    // Speed bonus
    if (performance.speedBonus) {
      bonusRewards.push({
        type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE,
        amount: Math.round(quest.difficulty * 20),
        description: 'Speed completion bonus'
      })
    }

    // Perfect completion bonus
    if (performance.perfectCompletion) {
      bonusRewards.push({
        type: QUEST_CONFIG.REWARD_TYPES.GOLD,
        amount: Math.round(quest.difficulty * 15),
        description: 'Perfect completion bonus'
      })
    }

    // No death bonus
    if (performance.noDeath) {
      bonusRewards.push({
        type: QUEST_CONFIG.REWARD_TYPES.REPUTATION,
        amount: 25,
        faction: 'Adventurers Guild',
        description: 'Flawless victory bonus'
      })
    }

    // High difficulty bonus
    if (quest.difficulty >= 5) {
      bonusRewards.push({
        type: QUEST_CONFIG.REWARD_TYPES.TITLE,
        amount: 1,
        name: this.generateDifficultyTitle(quest.difficulty),
        description: `${quest.difficulty >= 6 ? 'Legendary' : 'Expert'} Adventurer`
      })
    }

    // Choice-based bonus
    if (performance.choiceBonus) {
      bonusRewards.push({
        type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE,
        amount: Math.round(quest.difficulty * 30),
        description: 'Wise choice bonus'
      })
    }

    return bonusRewards
  }

  /**
   * Apply reward multipliers
   */
  applyRewardMultipliers(rewards, quest, player) {
    const totalMultiplier = this.getTotalMultiplier(quest, player)

    const applyMultiplier = (rewardArray) => {
      return rewardArray.map(reward => {
        if (typeof reward.amount === 'number') {
          return {
            ...reward,
            amount: Math.round(reward.amount * totalMultiplier)
          }
        }
        return reward
      })
    }

    rewards.base = applyMultiplier(rewards.base)
    rewards.bonus = applyMultiplier(rewards.bonus)

    if (rewards.choice.options) {
      rewards.choice.options = rewards.choice.options.map(option => ({
        ...option,
        rewards: applyMultiplier(option.rewards)
      }))
    }

    return rewards
  }

  /**
   * Add random rewards based on luck
   */
  addRandomRewards(rewards, quest, player) {
    const luckFactor = this.calculateLuckFactor(player)
    const randomRewards = []

    // Chance for bonus loot
    if (Math.random() < luckFactor * 0.1) {
      randomRewards.push({
        type: QUEST_CONFIG.REWARD_TYPES.ITEM,
        amount: 1,
        rarity: this.getRandomRarity(luckFactor),
        description: 'Lucky find bonus'
      })
    }

    // Chance for bonus experience
    if (Math.random() < luckFactor * 0.15) {
      randomRewards.push({
        type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE,
        amount: Math.round(quest.difficulty * 50 * luckFactor),
        description: 'Experience surge bonus'
      })
    }

    // Chance for bonus gold
    if (Math.random() < luckFactor * 0.2) {
      randomRewards.push({
        type: QUEST_CONFIG.REWARD_TYPES.GOLD,
        amount: Math.round(quest.difficulty * 30 * luckFactor),
        description: 'Fortune favor bonus'
      })
    }

    rewards.bonus.push(...randomRewards)
    return rewards
  }

  /**
   * Normalize rewards to ensure they're balanced
   */
  normalizeRewards(rewards, quest) {
    const allRewards = [...rewards.base, ...rewards.bonus]

    // Group rewards by type
    const groupedRewards = allRewards.reduce((groups, reward) => {
      if (!groups[reward.type]) {
        groups[reward.type] = []
      }
      groups[reward.type].push(reward)
      return groups
    }, {})

    // Consolidate numeric rewards
    Object.keys(groupedRewards).forEach(type => {
      const rewardsOfType = groupedRewards[type]

      if (this.isNumericRewardType(type)) {
        const totalAmount = rewardsOfType.reduce((sum, reward) => sum + reward.amount, 0)
        const consolidatedReward = {
          type,
          amount: Math.round(totalAmount),
          description: this.getConsolidatedDescription(rewardsOfType)
        }

        // Add special properties if present
        const specialReward = rewardsOfType.find(r => r.faction || r.rarity || r.name)
        if (specialReward) {
          if (specialReward.faction) consolidatedReward.faction = specialReward.faction
          if (specialReward.rarity) consolidatedReward.rarity = specialReward.rarity
          if (specialReward.name) consolidatedReward.name = specialReward.name
        }

        groupedRewards[type] = [consolidatedReward]
      }
    })

    // Rebuild rewards arrays
    rewards.base = []
    rewards.bonus = []

    Object.values(groupedRewards).forEach(rewardArray => {
      rewardArray.forEach(reward => {
        if (reward.description?.includes('bonus')) {
          rewards.bonus.push(reward)
        } else {
          rewards.base.push(reward)
        }
      })
    })

    return rewards
  }

  /**
   * Calculate base reward multiplier
   */
  getBaseRewardMultiplier(quest) {
    const difficultyMultiplier = this.difficultyMultipliers[quest.difficulty] || 1
    const typeMultiplier = this.questTypeMultipliers[quest.type] || 1
    const categoryMultiplier = this.categoryMultipliers[quest.category] || 1

    return difficultyMultiplier * typeMultiplier * categoryMultiplier
  }

  /**
   * Calculate total multiplier
   */
  getTotalMultiplier(quest, player) {
    const baseMultiplier = this.getBaseRewardMultiplier(quest)
    const playerMultiplier = this.getPlayerMultiplier(player)
    const partyMultiplier = this.getPartyMultiplier(quest)

    return baseMultiplier * playerMultiplier * partyMultiplier
  }

  /**
   * Calculate experience reward
   */
  calculateExperienceReward(quest, player, multiplier) {
    const baseExperience = this.baseRewardMultipliers[QUEST_CONFIG.REWARD_TYPES.EXPERIENCE]
    const levelAdjusted = baseExperience * (1 + player.stats.level * 0.1)
    const difficultyAdjusted = levelAdjusted * quest.difficulty

    return {
      type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE,
      amount: Math.round(difficultyAdjusted * multiplier),
      description: 'Quest completion experience'
    }
  }

  /**
   * Calculate gold reward
   */
  calculateGoldReward(quest, player, multiplier) {
    const baseGold = this.baseRewardMultipliers[QUEST_CONFIG.REWARD_TYPES.GOLD]
    const difficultyAdjusted = baseGold * quest.difficulty
    const questLengthBonus = quest.objectives.length * 10

    return {
      type: QUEST_CONFIG.REWARD_TYPES.GOLD,
      amount: Math.round((difficultyAdjusted + questLengthBonus) * multiplier),
      description: 'Quest completion reward'
    }
  }

  /**
   * Calculate reputation reward
   */
  calculateReputationReward(quest, player, multiplier) {
    // Determine relevant faction based on quest type or location
    const faction = this.getQuestFaction(quest)
    const baseReputation = this.baseRewardMultipliers[QUEST_CONFIG.REWARD_TYPES.REPUTATION]
    const difficultyAdjusted = baseReputation * quest.difficulty

    return {
      type: QUEST_CONFIG.REWARD_TYPES.REPUTATION,
      amount: Math.round(difficultyAdjusted * multiplier),
      faction,
      description: `Reputation gain with ${faction}`
    }
  }

  /**
   * Calculate skill reward
   */
  calculateSkillReward(quest, player, multiplier) {
    const skillChance = this.baseRewardMultipliers[QUEST_CONFIG.REWARD_TYPES.SKILL_POINT]

    // Higher chance for crafting, mystery, and social quests
    const categoryBonus = {
      [QUEST_CONFIG.CATEGORIES.CRAFTING]: 2,
      [QUEST_CONFIG.CATEGORIES.MYSTERY]: 1.5,
      [QUEST_CONFIG.CATEGORIES.SOCIAL]: 1.3
    }[quest.category] || 1

    const finalChance = skillChance * multiplier * categoryBonus

    if (Math.random() < finalChance) {
      return {
        type: QUEST_CONFIG.REWARD_TYPES.SKILL_POINT,
        amount: 1,
        description: 'Skill point earned'
      }
    }

    return { type: QUEST_CONFIG.REWARD_TYPES.SKILL_POINT, amount: 0 }
  }

  /**
   * Calculate item/equipment rewards
   */
  calculateItemRewards(quest, player, multiplier) {
    const itemRewards = []
    const baseItemChance = this.baseRewardMultipliers[QUEST_CONFIG.REWARD_TYPES.ITEM]

    // Chance for equipment reward
    if (quest.difficulty >= 3 && Math.random() < baseItemChance * multiplier) {
      const rarity = this.getRandomRarity(this.calculateLuckFactor(player), quest.difficulty)
      itemRewards.push({
        type: QUEST_CONFIG.REWARD_TYPES.EQUIPMENT,
        amount: 1,
        rarity,
        description: `${rarity} equipment reward`
      })
    }

    // Chance for consumable items
    if (quest.difficulty >= 2 && Math.random() < baseItemChance * 1.5 * multiplier) {
      itemRewards.push({
        type: QUEST_CONFIG.REWARD_TYPES.ITEM,
        amount: Math.floor(Math.random() * 3) + 1,
        rarity: 'common',
        description: 'Useful items'
      })
    }

    return itemRewards
  }

  /**
   * Get quest faction
   */
  getQuestFaction(quest) {
    const factionMap = {
      [QUEST_CONFIG.CATEGORIES.COMBAT]: 'Adventurers Guild',
      [QUEST_CONFIG.CATEGORIES.CRAFTING]: 'Crafters Union',
      [QUEST_CONFIG.CATEGORIES.SOCIAL]: 'Council of Elders',
      [QUEST_CONFIG.CATEGORIES.EXPLORATION]: 'Explorers Society',
      [QUEST_CONFIG.CATEGORIES.MYSTERY]: 'Scholars Circle',
      [QUEST_CONFIG.CATEGORIES.DUNGEON]: 'Dungeon Delvers Guild',
      [QUEST_CONFIG.CATEGORIES.BOSS_BATTLE]: 'Heroes League'
    }

    return factionMap[quest.category] || 'Local Community'
  }

  /**
   * Get player multiplier
   */
  getPlayerMultiplier(player) {
    // Based on player's performance and level
    const levelBonus = 1 + (player.stats.level / 100) * 0.5
    const completionRateBonus = this.getCompletionRateBonus(player)
    const preferenceBonus = this.getPreferenceBonus(player)

    return levelBonus * completionRateBonus * preferenceBonus
  }

  /**
   * Get party multiplier
   */
  getPartyMultiplier(quest) {
    // Slightly reduce rewards for party quests to prevent abuse
    const partySize = quest.assignedTo.length
    if (partySize > 1) {
      return Math.max(0.8, 1 / Math.sqrt(partySize))
    }
    return 1
  }

  /**
   * Calculate luck factor
   */
  calculateLuckFactor(player) {
    // Base luck from player attributes (charisma)
    const charismaLuck = player.stats.attributes.charisma / 20

    // Luck from recent performance
    const recentQuests = player.questHistory.slice(-5)
    const highRatings = recentQuests.filter(q => q.rating >= 4).length
    const performanceLuck = highRatings / 5

    // Random luck component
    const randomLuck = Math.random()

    return Math.max(0.1, Math.min(2.0, charismaLuck + performanceLuck + randomLuck))
  }

  /**
   * Get random rarity based on luck and difficulty
   */
  getRandomRarity(luckFactor, difficulty = 3) {
    const adjustedChances = { ...this.rarityChances }

    // Adjust chances based on luck
    Object.keys(adjustedChances).forEach(rarity => {
      const rarityLevel = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic'].indexOf(rarity)
      const adjustment = 1 + (luckFactor - 1) * (rarityLevel / 5)
      adjustedChances[rarity] = Math.min(1, adjustedChances[rarity] * adjustment)
    })

    // Adjust for difficulty
    if (difficulty >= 5) {
      adjustedChances.legendary += 0.02
      adjustedChances.epic += 0.05
    }
    if (difficulty >= 6) {
      adjustedChances.mythic += 0.01
      adjustedChances.legendary += 0.03
    }

    // Normalize chances
    const totalChance = Object.values(adjustedChances).reduce((sum, chance) => sum + chance, 0)
    Object.keys(adjustedChances).forEach(rarity => {
      adjustedChances[rarity] = adjustedChances[rarity] / totalChance
    })

    // Select rarity
    const random = Math.random()
    let cumulative = 0
    for (const [rarity, chance] of Object.entries(adjustedChances)) {
      cumulative += chance
      if (random <= cumulative) {
        return rarity
      }
    }

    return 'common'
  }

  /**
   * Generate difficulty title
   */
  generateDifficultyTitle(difficulty) {
    const titles = {
      5: 'Expert',
      6: 'Master',
      7: 'Legendary'
    }

    return titles[difficulty] || 'Adventurer'
  }

  /**
   * Get completion rate bonus
   */
  getCompletionRateBonus(player) {
    const completedQuests = player.questHistory.filter(q => q.completed).length
    const totalQuests = player.questHistory.length

    if (totalQuests === 0) return 1

    const completionRate = completedQuests / totalQuests

    if (completionRate > 0.9) return 1.2
    if (completionRate > 0.8) return 1.1
    if (completionRate > 0.6) return 1.0
    if (completionRate > 0.4) return 0.9
    return 0.8
  }

  /**
   * Get preference bonus
   */
  getPreferenceBonus(player) {
    const preferences = player.questPreferences.types
    const maxPreference = Math.max(...Object.values(preferences))

    if (maxPreference > 0.8) return 1.1
    if (maxPreference > 0.6) return 1.05
    return 1.0
  }

  /**
   * Check if reward type is numeric
   */
  isNumericRewardType(type) {
    return [
      QUEST_CONFIG.REWARD_TYPES.EXPERIENCE,
      QUEST_CONFIG.REWARD_TYPES.GOLD,
      QUEST_CONFIG.REWARD_TYPES.REPUTATION
    ].includes(type)
  }

  /**
   * Get consolidated description for grouped rewards
   */
  getConsolidatedDescription(rewards) {
    if (rewards.length === 1) return rewards[0].description

    const types = rewards.map(r => r.type).join(', ')
    return `Consolidated ${types} rewards`
  }

  /**
   * Calculate reward forecast for quest preview
   */
  calculateRewardForecast(quest, player) {
    const forecast = this.calculateRewards(quest, player)

    return {
      estimatedExperience: this.getTotalRewardAmount(forecast, QUEST_CONFIG.REWARD_TYPES.EXPERIENCE),
      estimatedGold: this.getTotalRewardAmount(forecast, QUEST_CONFIG.REWARD_TYPES.GOLD),
      estimatedReputation: this.getTotalRewardAmount(forecast, QUEST_CONFIG.REWARD_TYPES.REPUTATION),
      possibleItems: this.getPossibleItems(forecast),
      rarities: this.getPossibleRarities(forecast),
      totalValue: this.calculateTotalRewardValue(forecast)
    }
  }

  /**
   * Get total amount for specific reward type
   */
  getTotalRewardAmount(rewards, type) {
    const allRewards = [...rewards.base, ...rewards.bonus]
    return allRewards
      .filter(r => r.type === type && typeof r.amount === 'number')
      .reduce((sum, r) => sum + r.amount, 0)
  }

  /**
   * Get possible items from rewards
   */
  getPossibleItems(rewards) {
    const allRewards = [...rewards.base, ...rewards.bonus]
    return allRewards
      .filter(r => [QUEST_CONFIG.REWARD_TYPES.ITEM, QUEST_CONFIG.REWARD_TYPES.EQUIPMENT].includes(r.type))
      .map(r => ({
        type: r.type,
        rarity: r.rarity || 'common',
        amount: r.amount
      }))
  }

  /**
   * Get possible rarities from rewards
   */
  getPossibleRarities(rewards) {
    const items = this.getPossibleItems(rewards)
    return [...new Set(items.map(item => item.rarity))]
  }

  /**
   * Calculate total reward value
   */
  calculateTotalRewardValue(rewards) {
    const allRewards = [...rewards.base, ...rewards.bonus]
    let totalValue = 0

    allRewards.forEach(reward => {
      switch (reward.type) {
        case QUEST_CONFIG.REWARD_TYPES.EXPERIENCE:
          totalValue += reward.amount * 0.1 // 1 XP = 0.1 gold value
          break
        case QUEST_CONFIG.REWARD_TYPES.GOLD:
          totalValue += reward.amount
          break
        case QUEST_CONFIG.REWARD_TYPES.REPUTATION:
          totalValue += reward.amount * 2 // 1 rep = 2 gold value
          break
        case QUEST_CONFIG.REWARD_TYPES.ITEM:
        case QUEST_CONFIG.REWARD_TYPES.EQUIPMENT:
          const rarityMultiplier = {
            common: 10,
            uncommon: 25,
            rare: 50,
            epic: 100,
            legendary: 250,
            mythic: 500
          }
          totalValue += (rarityMultiplier[reward.rarity] || 10) * reward.amount
          break
        case QUEST_CONFIG.REWARD_TYPES.SKILL_POINT:
          totalValue += 100
          break
        case QUEST_CONFIG.REWARD_TYPES.ABILITY:
          totalValue += 200
          break
        case QUEST_CONFIG.REWARD_TYPES.TITLE:
          totalValue += 50
          break
      }
    })

    return Math.round(totalValue)
  }

  /**
   * Get reward calculator statistics
   */
  getStatistics() {
    return {
      baseMultipliers: this.baseRewardMultipliers,
      difficultyMultipliers: this.difficultyMultipliers,
      questTypeMultipliers: this.questTypeMultipliers,
      categoryMultipliers: this.categoryMultipliers,
      rarityChances: this.rarityChances
    }
  }

  /**
   * Update multiplier
   */
  updateMultiplier(type, key, value) {
    const multipliers = {
      base: this.baseRewardMultipliers,
      difficulty: this.difficultyMultipliers,
      questType: this.questTypeMultipliers,
      category: this.categoryMultipliers
    }

    if (multipliers[type] && multipliers[type].hasOwnProperty(key)) {
      multipliers[type][key] = value
      return true
    }

    return false
  }

  /**
   * Update rarity chance
   */
  updateRarityChance(rarity, chance) {
    if (this.rarityChances.hasOwnProperty(rarity)) {
      this.rarityChances[rarity] = Math.max(0, Math.min(1, chance))
      return true
    }
    return false
  }
}

export default RewardCalculator