import mongoose from 'mongoose'
import bcrypt from 'bcryptjs'

const { Schema, SchemaTypes } = mongoose

const playerStatsSchema = new Schema({
  // Basic Stats
  level: {
    type: Number,
    required: true,
    min: 1,
    max: 100,
    default: 1
  },
  experience: {
    current: {
      type: Number,
      default: 0,
      min: 0
    },
    total: {
      type: Number,
      default: 0,
      min: 0
    },
    toNext: {
      type: Number,
      default: 1000
    }
  },

  // Character Attributes
  attributes: {
    strength: {
      type: Number,
      default: 10,
      min: 1,
      max: 100
    },
    dexterity: {
      type: Number,
      default: 10,
      min: 1,
      max: 100
    },
    constitution: {
      type: Number,
      default: 10,
      min: 1,
      max: 100
    },
    intelligence: {
      type: Number,
      default: 10,
      min: 1,
      max: 100
    },
    wisdom: {
      type: Number,
      default: 10,
      min: 1,
      max: 100
    },
    charisma: {
      type: Number,
      default: 10,
      min: 1,
      max: 100
    }
  },

  // Combat Stats
  health: {
    current: {
      type: Number,
      min: 0
    },
    maximum: {
      type: Number,
      min: 1
    }
  },
  mana: {
    current: {
      type: Number,
      min: 0
    },
    maximum: {
      type: Number,
      min: 0
    }
  },
  resources: {
    gold: {
      type: Number,
      default: 100,
      min: 0
    },
    silver: {
      type: Number,
      default: 0,
      min: 0
    },
    copper: {
      type: Number,
      default: 0,
      min: 0
    },
    gems: {
      type: Number,
      default: 0,
      min: 0
    }
  },

  // Skills and Abilities
  skills: [{
    id: String,
    name: String,
    level: {
      type: Number,
      min: 0,
      max: 100,
      default: 0
    },
    experience: {
      type: Number,
      default: 0,
      min: 0
    },
    category: String
  }],
  abilities: [{
    id: String,
    name: String,
    unlocked: {
      type: Boolean,
      default: false
    },
    level: {
      type: Number,
      min: 1,
      max: 5,
      default: 1
    },
    cooldown: Number,
    uses: Number,
    maxUses: Number
  }],

  // Reputation and Relationships
  reputation: [{
    faction: String,
    standing: {
      type: Number,
      default: 0,
      min: -1000,
      max: 1000
    },
    rank: String
  }],
  relationships: [{
    character: String,
    attitude: {
      type: Number,
      default: 0,
      min: -100,
      max: 100
    },
    status: {
      type: String,
      enum: ['stranger', 'acquaintance', 'friend', 'close_friend', 'enemy', 'rival', 'ally'],
      default: 'stranger'
    }
  }],

  // Equipment and Inventory
  equipment: {
    head: String,
    chest: String,
    legs: String,
    feet: String,
    weapon: String,
    shield: String,
    accessories: [String]
  },
  inventory: [{
    id: String,
    name: String,
    quantity: {
      type: Number,
      min: 1,
      default: 1
    },
    rarity: String,
    category: String,
    value: Number,
    properties: Schema.Types.Mixed
  }]
}, { _id: false })

const questPreferencesSchema = new Schema({
  // Quest Type Preferences
  types: {
    combat: {
      type: Number,
      default: 0.5,
      min: 0,
      max: 1
    },
    exploration: {
      type: Number,
      default: 0.5,
      min: 0,
      max: 1
    },
    social: {
      type: Number,
      default: 0.5,
      min: 0,
      max: 1
    },
    mystery: {
      type: Number,
      default: 0.5,
      min: 0,
      max: 1
    },
    crafting: {
      type: Number,
      default: 0.5,
      min: 0,
      max: 1
    }
  },

  // Difficulty Preference
  difficulty: {
    preferred: {
      type: Number,
      default: 3,
      min: 1,
      max: 7
    },
    adaptive: {
      type: Boolean,
      default: true
    }
  },

  // Length Preference
  questLength: {
    type: String,
    enum: ['short', 'medium', 'long', 'epic'],
    default: 'medium'
  },

  // Content Preferences
  avoidContent: [{
    type: String,
    reason: String
  }],
  preferContent: [{
    type: String,
    reason: String
  }],

  // Social Preferences
  playStyle: {
    type: String,
    enum: ['solo', 'duo', 'small_group', 'large_group', 'guild'],
    default: 'solo'
  },
  partySize: {
    min: {
      type: Number,
      default: 1,
      min: 1,
      max: 6
    },
    max: {
      type: Number,
      default: 6,
      min: 1,
      max: 6
    }
  }
}, { _id: false })

const playerQuestHistorySchema = new Schema({
  questId: {
    type: String,
    required: true
  },
  title: String,
  type: String,
  difficulty: Number,
  completed: {
    type: Boolean,
    default: false
  },
  abandoned: {
    type: Boolean,
    default: false
  },
  startTime: Date,
  endTime: Date,
  completionTime: Number,
  rating: {
    type: Number,
    min: 1,
    max: 5
  },
  feedback: String,
  choices: [{
    objectiveId: String,
    choiceId: String,
    timestamp: Date
  }],
  performance: {
    deaths: {
      type: Number,
      default: 0
    },
    resourcesUsed: {
      type: Number,
      default: 0
    },
    efficiency: {
      type: Number,
      min: 0,
      max: 1
    }
  }
}, { _id: false })

const playerSchema = new Schema({
  // Basic Information
  userId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  username: {
    type: String,
    required: true,
    unique: true,
    trim: true,
    minlength: 3,
    maxlength: 30
  },
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true,
    trim: true
  },
  password: {
    type: String,
    required: true,
    minlength: 8
  },

  // Character Information
  character: {
    name: {
      type: String,
      required: true,
      trim: true,
      maxlength: 50
    },
    class: {
      type: String,
      required: true,
      enum: ['warrior', 'mage', 'rogue', 'cleric', 'ranger', 'paladin', 'warlock', 'bard', 'monk', 'druid']
    },
    race: {
      type: String,
      required: true,
      enum: ['human', 'elf', 'dwarf', 'orc', 'halfling', 'gnome', 'dragonborn', 'tiefling']
    },
    background: {
      type: String,
      enum: ['noble', 'commoner', 'scholar', 'merchant', 'soldier', 'criminal', 'artist', 'farmer'],
      default: 'commoner'
    },
    alignment: {
      type: String,
      enum: ['lawful_good', 'neutral_good', 'chaotic_good', 'lawful_neutral', 'true_neutral', 'chaotic_neutral', 'lawful_evil', 'neutral_evil', 'chaotic_evil'],
      default: 'true_neutral'
    },
    avatar: String,
    biography: {
      type: String,
      maxlength: 1000
    }
  },

  // Game Statistics
  stats: playerStatsSchema,

  // Quest Preferences
  questPreferences: questPreferencesSchema,

  // Quest History
  questHistory: [playerQuestHistorySchema],

  // Current Quests
  activeQuests: [{
    questId: {
      type: String,
      required: true
    },
    startTime: {
      type: Date,
      default: Date.now
    },
    progress: {
      type: Number,
      default: 0,
      min: 0,
      max: 100
    },
    currentObjective: String,
    lastAccessed: {
      type: Date,
      default: Date.now
    }
  }],

  // Achievements and Milestones
  achievements: [{
    id: String,
    name: String,
    description: String,
    unlockedAt: Date,
    category: String,
    rarity: String
  }],
  milestones: [{
    type: String,
    value: Schema.Types.Mixed,
    achieved: {
      type: Boolean,
      default: false
    },
    achievedAt: Date
  }],

  // Social Information
  guildId: String,
  guildRank: String,
  partyId: String,
  friends: [String],
  blocked: [String],

  // Settings and Preferences
  settings: {
    notifications: {
      questUpdates: {
        type: Boolean,
        default: true
      },
      partyInvites: {
        type: Boolean,
        default: true
      },
      guildEvents: {
        type: Boolean,
        default: true
      },
      dailyQuests: {
        type: Boolean,
        default: true
      }
    },
    privacy: {
      profilePublic: {
        type: Boolean,
        default: true
      },
      questHistoryPublic: {
        type: Boolean,
        default: false
      },
      achievementsPublic: {
        type: Boolean,
        default: true
      }
    },
    gameplay: {
      autoAcceptQuests: {
        type: Boolean,
        default: false
      },
      showQuestMarkers: {
        type: Boolean,
        default: true
      },
      difficultyScaling: {
        type: Boolean,
        default: true
      }
    }
  },

  // Session Information
  lastLogin: Date,
  lastLogout: Date,
  totalPlayTime: {
    type: Number,
    default: 0
  },
  sessions: [{
    startTime: Date,
    endTime: Date,
    duration: Number,
    questsCompleted: Number,
    experienceGained: Number
  }],

  // Quest Generation Context
  questContext: {
    lastGeneratedQuest: Date,
    questGenerationCount: {
      type: Number,
      default: 0
    },
    preferredThemes: [String],
    avoidedThemes: [String],
    currentLocation: String,
    worldState: {
      type: String,
      default: 'neutral'
    },
    recentChoices: [{
      type: String,
      value: Schema.Types.Mixed,
      timestamp: Date
    }]
  },

  // Analytics and Metrics
  analytics: {
    questsGenerated: {
      type: Number,
      default: 0
    },
    questsCompleted: {
      type: Number,
      default: 0
    },
    questsAbandoned: {
      type: Number,
      default: 0
    },
    averageCompletionTime: {
      type: Number,
      default: 0
    },
    averageRating: {
      type: Number,
      default: 0
    },
    favoriteQuestType: String,
    favoriteDifficulty: Number,
    completionRate: {
      type: Number,
      default: 0
    }
  },

  // Moderation and Status
  status: {
    type: String,
    enum: ['active', 'inactive', 'suspended', 'banned'],
    default: 'active'
  },
  warnings: [{
    type: String,
    reason: String,
    date: Date,
    severity: {
      type: String,
      enum: ['low', 'medium', 'high']
    }
  }],
  notes: String,

  // Metadata
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  },
  version: {
    type: Number,
    default: 1
  }
}, {
  timestamps: true,
  index: [
    { userId: 1 },
    { username: 1 },
    { email: 1 },
    { 'character.class': 1 },
    { 'stats.level': 1 },
    { guildId: 1 },
    { status: 1 },
    { 'questContext.lastGeneratedQuest': -1 }
  ]
})

// Virtual fields
playerSchema.virtual('level').get(function() {
  return this.stats.level
})

playerSchema.virtual('currentQuests').get(function() {
  return this.activeQuests.length
})

playerSchema.virtual('completedQuests').get(function() {
  return this.questHistory.filter(quest => quest.completed).length
})

playerSchema.virtual('abandonedQuests').get(function() {
  return this.questHistory.filter(quest => quest.abandoned).length
})

playerSchema.virtual('completionRate').get(function() {
  const total = this.questHistory.length
  if (total === 0) return 0
  const completed = this.questHistory.filter(quest => quest.completed).length
  return Math.round((completed / total) * 100)
})

playerSchema.virtual('averageQuestRating').get(function() {
  const ratedQuests = this.questHistory.filter(quest => quest.rating)
  if (ratedQuests.length === 0) return 0
  const totalRating = ratedQuests.reduce((sum, quest) => sum + quest.rating, 0)
  return totalRating / ratedQuests.length
})

// Instance methods
playerSchema.methods.addExperience = function(amount) {
  this.stats.experience.current += amount
  this.stats.experience.total += amount

  // Check for level up
  while (this.stats.experience.current >= this.stats.experience.toNext) {
    this.stats.experience.current -= this.stats.experience.toNext
    this.levelUp()
  }
}

playerSchema.methods.levelUp = function() {
  this.stats.level += 1
  this.stats.experience.toNext = Math.floor(this.stats.experience.toNext * 1.1)

  // Increase health
  const healthIncrease = Math.floor(10 + this.stats.attributes.constitution * 0.5)
  this.stats.health.maximum += healthIncrease
  this.stats.health.current = this.stats.health.maximum

  // Increase mana if applicable
  if (this.character.class === 'mage' || this.character.class === 'cleric' || this.character.class === 'warlock' || this.character.class === 'bard' || this.character.class === 'druid') {
    const manaIncrease = Math.floor(5 + this.stats.attributes.intelligence * 0.3)
    this.stats.health.maximum += manaIncrease
    this.stats.mana.current = this.stats.mana.maximum
  }

  // Increase attributes slightly
  this.stats.attributes.strength += 1
  this.stats.attributes.dexterity += 1
  this.stats.attributes.constitution += 1
  this.stats.attributes.intelligence += 1
  this.stats.attributes.wisdom += 1
  this.stats.attributes.charisma += 1
}

playerSchema.methods.meetsPrerequisite = function(prerequisite) {
  switch (prerequisite.type) {
    case 'level':
      return this.stats.level >= prerequisite.value
    case 'class':
      return this.character.class === prerequisite.value
    case 'skill':
      const skill = this.stats.skills.find(s => s.id === prerequisite.id)
      return skill && skill.level >= prerequisite.value
    case 'faction':
      const faction = this.stats.reputation.find(r => r.faction === prerequisite.id)
      return faction && faction.standing >= prerequisite.value
    case 'achievement':
      return this.achievements.some(a => a.id === prerequisite.id)
    case 'quest':
      const quest = this.questHistory.find(q => q.questId === prerequisite.id)
      return quest && quest.completed
    default:
      return false
  }
}

playerSchema.methods.getLastCompletion = function(questId) {
  const quest = this.questHistory
    .filter(q => q.questId === questId && q.completed)
    .sort((a, b) => new Date(b.endTime) - new Date(a.endTime))[0]

  return quest ? new Date(quest.endTime).getTime() : null
}

playerSchema.methods.addQuest = function(quest) {
  // Check if quest is already active
  if (this.activeQuests.some(q => q.questId === quest.id)) {
    return false
  }

  this.activeQuests.push({
    questId: quest.id,
    startTime: new Date(),
    lastAccessed: new Date()
  })

  this.questContext.questGenerationCount++
  this.analytics.questsGenerated++
  return true
}

playerSchema.methods.updateQuestProgress = function(questId, progress, objectiveId) {
  const quest = this.activeQuests.find(q => q.questId === questId)
  if (!quest) return false

  quest.progress = progress
  quest.lastAccessed = new Date()

  if (objectiveId) {
    quest.currentObjective = objectiveId
  }

  return true
}

playerSchema.methods.completeQuest = function(questId, rating, feedback) {
  const questIndex = this.activeQuests.findIndex(q => q.questId === questId)
  if (questIndex === -1) return false

  const quest = this.activeQuests[questIndex]
  const completionTime = Date.now() - new Date(quest.startTime).getTime()

  // Remove from active quests
  this.activeQuests.splice(questIndex, 1)

  // Add to history
  this.questHistory.push({
    questId,
    title: quest.title,
    type: quest.type,
    difficulty: quest.difficulty,
    completed: true,
    startTime: quest.startTime,
    endTime: new Date(),
    completionTime,
    rating,
    feedback
  })

  // Update analytics
  this.analytics.questsCompleted++
  this.updateQuestAnalytics()

  return true
}

playerSchema.methods.abandonQuest = function(questId, reason) {
  const questIndex = this.activeQuests.findIndex(q => q.questId === questId)
  if (questIndex === -1) return false

  const quest = this.activeQuests[questIndex]

  // Remove from active quests
  this.activeQuests.splice(questIndex, 1)

  // Add to history
  this.questHistory.push({
    questId,
    title: quest.title,
    type: quest.type,
    difficulty: quest.difficulty,
    abandoned: true,
    startTime: quest.startTime,
    endTime: new Date()
  })

  // Update analytics
  this.analytics.questsAbandoned++
  this.updateQuestAnalytics()

  return true
}

playerSchema.methods.updateQuestAnalytics = function() {
  const totalQuests = this.questHistory.length
  if (totalQuests === 0) return

  this.analytics.completionRate = this.completionRate
  this.analytics.averageRating = this.averageQuestRating

  const completedQuests = this.questHistory.filter(q => q.completed)
  if (completedQuests.length > 0) {
    const totalTime = completedQuests.reduce((sum, q) => sum + (q.completionTime || 0), 0)
    this.analytics.averageCompletionTime = totalTime / completedQuests.length
  }
}

playerSchema.methods.applyConsequence = function(consequence) {
  switch (consequence.type) {
    case 'reputation':
      const faction = this.stats.reputation.find(r => r.faction === consequence.target)
      if (faction) {
        faction.standing += consequence.value
      } else {
        this.stats.reputation.push({
          faction: consequence.target,
          standing: consequence.value
        })
      }
      break
    case 'relationship':
      const relationship = this.stats.relationships.find(r => r.character === consequence.target)
      if (relationship) {
        relationship.attitude += consequence.value
      } else {
        this.stats.relationships.push({
          character: consequence.target,
          attitude: consequence.value
        })
      }
      break
    case 'experience':
      this.addExperience(consequence.value)
      break
    case 'gold':
      this.stats.resources.gold += consequence.value
      break
    case 'alignment':
      this.character.alignment = consequence.value
      break
  }

  // Add to recent choices for context
  this.questContext.recentChoices.push({
    type: consequence.type,
    value: consequence.value,
    timestamp: new Date()
  })

  // Keep only last 10 choices
  if (this.questContext.recentChoices.length > 10) {
    this.questContext.recentChoices.shift()
  }
}

playerSchema.methods.updateQuestPreferences = function(preferences) {
  if (preferences.types) {
    Object.assign(this.questPreferences.types, preferences.types)
  }
  if (preferences.difficulty) {
    Object.assign(this.questPreferences.difficulty, preferences.difficulty)
  }
  if (preferences.questLength) {
    this.questPreferences.questLength = preferences.questLength
  }
  if (preferences.avoidContent) {
    this.questPreferences.avoidContent = preferences.avoidContent
  }
  if (preferences.preferContent) {
    this.questPreferences.preferContent = preferences.preferContent
  }
  if (preferences.playStyle) {
    this.questPreferences.playStyle = preferences.playStyle
  }
  if (preferences.partySize) {
    Object.assign(this.questPreferences.partySize, preferences.partySize)
  }
}

// Static methods
playerSchema.statics.findByClass = function(className) {
  return this.find({ 'character.class': className, status: 'active' })
}

playerSchema.statics.findByLevelRange = function(minLevel, maxLevel) {
  return this.find({
    'stats.level': { $gte: minLevel, $lte: maxLevel },
    status: 'active'
  })
}

playerSchema.statics.findByGuild = function(guildId) {
  return this.find({ guildId, status: 'active' })
}

// Pre-save middleware
playerSchema.pre('save', async function(next) {
  if (this.isModified('password')) {
    this.password = await bcrypt.hash(this.password, 12)
  }

  if (this.isModified('stats.experience')) {
    this.updateQuestAnalytics()
  }

  next()
})

// Indexes for performance
playerSchema.index({ 'questContext.recentChoices.timestamp': -1 })
playerSchema.index({ 'analytics.completionRate': -1 })
playerSchema.index({ 'stats.level': 1, 'character.class': 1 })
playerSchema.index({ 'questHistory.endTime': -1 })

export const Player = mongoose.model('Player', playerSchema)
export default Player