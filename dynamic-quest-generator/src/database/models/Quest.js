import mongoose from 'mongoose'
import { QUEST_CONFIG } from '../../../config/quest-config.js'

const { Schema, SchemaTypes } = mongoose

const objectiveSchema = new Schema({
  id: {
    type: String,
    required: true,
    unique: true
  },
  title: {
    type: String,
    required: true,
    trim: true,
    minlength: 5,
    maxlength: 100
  },
  description: {
    type: String,
    required: true,
    trim: true,
    minlength: 10,
    maxlength: 500
  },
  type: {
    type: String,
    enum: Object.values(QUEST_CONFIG.OBJECTIVE_TYPES),
    required: true
  },
  target: {
    type: Schema.Types.Mixed,
    required: true
  },
  current: {
    type: Number,
    default: 0,
    min: 0
  },
  required: {
    type: Number,
    required: true,
    min: 1
  },
  completed: {
    type: Boolean,
    default: false
  },
  optional: {
    type: Boolean,
    default: false
  },
  hidden: {
    type: Boolean,
    default: false
  },
  timeLimit: {
    type: Number,
    min: 0
  },
  location: {
    type: {
      type: String,
      enum: ['Point'],
      default: 'Point'
    },
    coordinates: {
      type: [Number],
      validate: {
        validator: function(coordinates) {
          return coordinates.length === 2
        },
        message: 'Location must have exactly 2 coordinates [longitude, latitude]'
      }
    },
    radius: {
      type: Number,
      min: 0
    }
  },
  requirements: [{
    type: String,
    enum: ['level', 'class', 'item', 'skill', 'faction']
  }],
  rewards: [{
    type: {
      type: String,
      enum: Object.values(QUEST_CONFIG.REWARD_TYPES),
      required: true
    },
    amount: {
      type: Number,
      required: true,
      min: 1
    },
    id: String,
    name: String,
    description: String,
    rarity: {
      type: String,
      enum: ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic']
    }
  }],
  choices: [{
    id: {
      type: String,
      required: true
    },
    text: {
      type: String,
      required: true,
      maxlength: 200
    },
    consequences: [{
      type: {
        type: String,
        enum: ['reputation', 'relationship', 'world_state', 'alignment', 'unlock']
      },
      target: String,
      value: Schema.Types.Mixed,
      description: String
    }],
    nextObjective: String,
    requirements: [{
      type: String,
      value: Schema.Types.Mixed
    }]
  }],
  branches: [{
    condition: {
      type: String,
      required: true
    },
    value: Schema.Types.Mixed,
    nextObjective: String,
    description: String
  }]
}, { _id: false })

const rewardSchema = new Schema({
  type: {
    type: String,
    enum: Object.values(QUEST_CONFIG.REWARD_TYPES),
    required: true
  },
  amount: {
    type: Number,
    required: true,
    min: 1
  },
  id: String,
  name: String,
  description: String,
  rarity: {
    type: String,
    enum: ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic']
  },
  probability: {
    type: Number,
    min: 0,
    max: 1,
    default: 1
  },
  conditions: [{
    type: String,
    value: Schema.Types.Mixed
  }]
}, { _id: false })

const prerequisiteSchema = new Schema({
  type: {
    type: String,
    enum: ['quest', 'level', 'class', 'skill', 'item', 'faction', 'achievement'],
    required: true
  },
  id: String,
  value: Schema.Types.Mixed,
  operator: {
    type: String,
    enum: ['>=', '<=', '=', '>', '<', 'includes'],
    default: '>='
  },
  description: String
}, { _id: false })

const questSchema = new Schema({
  // Basic Information
  id: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  title: {
    type: String,
    required: true,
    trim: true,
    minlength: 5,
    maxlength: 100
  },
  description: {
    type: String,
    required: true,
    trim: true,
    minlength: 50,
    maxlength: 2000
  },
  summary: {
    type: String,
    trim: true,
    maxlength: 300
  },

  // Quest Classification
  type: {
    type: String,
    enum: Object.values(QUEST_CONFIG.QUEST_TYPES),
    required: true,
    index: true
  },
  category: {
    type: String,
    enum: Object.values(QUEST_CONFIG.CATEGORIES),
    required: true,
    index: true
  },
  difficulty: {
    type: Number,
    min: 1,
    max: 7,
    required: true,
    index: true
  },
  levelRequirement: {
    type: Number,
    required: true,
    min: 1,
    max: 100
  },
  maxLevel: {
    type: Number,
    min: 1,
    max: 100
  },

  // Story Content
  story: {
    introduction: String,
    background: String,
    climax: String,
    resolution: String,
    epilogue: String
  },
  dialogue: [{
    character: String,
    text: String,
    emotion: String,
    conditions: [String]
  }],
  lore: [{
    topic: String,
    content: String,
    importance: {
      type: Number,
      min: 1,
      max: 5
    }
  }],

  // Objectives and Progress
  objectives: [objectiveSchema],
  currentObjective: {
    type: String,
    default: null
  },
  progress: {
    type: Number,
    default: 0,
    min: 0,
    max: 100
  },

  // Rewards
  rewards: {
    base: [rewardSchema],
    bonus: [rewardSchema],
    choice: {
      enabled: {
        type: Boolean,
        default: false
      },
      options: [{
        name: String,
        description: String,
        rewards: [rewardSchema]
      }]
    }
  },

  // Quest State
  state: {
    type: String,
    enum: Object.values(QUEST_CONFIG.STATES),
    default: QUEST_CONFIG.STATES.DRAFT
  },
  active: {
    type: Boolean,
    default: false
  },
  repeatable: {
    type: Boolean,
    default: false
  },
  cooldown: {
    type: Number,
    min: 0,
    default: 0
  },
  timeLimit: {
    type: Number,
    min: 0
  },
  startTime: Date,
  endTime: Date,

  // Prerequisites and Requirements
  prerequisites: [prerequisiteSchema],
  requirements: [{
    type: String,
    enum: ['party', 'guild', 'items', 'skills', 'time', 'location'],
    description: String,
    value: Schema.Types.Mixed
  }],

  // Player Assignment
  assignedTo: [{
    type: Schema.Types.ObjectId,
    ref: 'Player',
    index: true
  }],
  partyId: {
    type: String,
    index: true
  },
  guildId: {
    type: String,
    index: true
  },

  // Generation Metadata
  generatedBy: {
    type: String,
    enum: ['ai', 'dm', 'system', 'player'],
    default: 'ai'
  },
  generationContext: {
    playerLevel: Number,
    playerClass: String,
    partyComposition: [String],
    worldState: String,
    preferences: [String],
    seed: String,
    template: String
  },

  // Personalization
  personalized: {
    type: Boolean,
    default: false
  },
  personalizationData: {
    playerHistory: [String],
    preferences: {
      combat: Number,
      exploration: Number,
      social: Number,
      mystery: Number,
      crafting: Number
    },
    adaptations: {
      difficulty: Number,
      length: Number,
      complexity: Number
    }
  },

  // Branching and Choices
  branching: {
    enabled: {
      type: Boolean,
      default: false
    },
    currentPath: String,
    completedPaths: [String],
    availablePaths: [String],
    pathHistory: [{
      objectiveId: String,
      choice: String,
      timestamp: {
        type: Date,
        default: Date.now
      }
    }]
  },

  // Social Features
  social: {
    shareable: {
      type: Boolean,
      default: true
    },
    leaderboard: {
      type: Boolean,
      default: false
    },
    achievements: [String],
    milestones: [{
      type: String,
      value: Schema.Types.Mixed,
      unlocked: {
        type: Boolean,
        default: false
      },
      timestamp: Date
    }]
  },

  // World Impact
  worldImpact: {
    reputation: [{
      faction: String,
      change: Number
    }],
    relationships: [{
      character: String,
      change: Number
    }],
    worldState: [{
      key: String,
      value: Schema.Types.Mixed
    }],
    unlocks: [{
      type: String,
      id: String,
      description: String
    }]
  },

  // Tracking and Analytics
  stats: {
    created: {
      type: Date,
      default: Date.now
    },
    modified: {
      type: Date,
      default: Date.now
    },
    started: Date,
    completed: Date,
    attempts: {
      type: Number,
      default: 0
    },
    completionTime: Number,
    rating: {
      average: {
        type: Number,
        min: 1,
        max: 5,
        default: 0
      },
      count: {
        type: Number,
        default: 0
      }
    },
    abandonment: {
      count: {
        type: Number,
        default: 0
      },
      reasons: [String]
    }
  },

  // Quality Control
  review: {
    status: {
      type: String,
      enum: ['pending', 'approved', 'rejected', 'flagged'],
      default: 'pending'
    },
    reviewedBy: String,
    reviewedAt: Date,
    feedback: String,
    flags: [{
      type: String,
      description: String,
      severity: {
        type: String,
        enum: ['low', 'medium', 'high', 'critical']
      }
    }]
  },

  // Version Control
  version: {
    type: Number,
    default: 1
  },
  parentQuest: String,
  childQuests: [String],
  linkedQuests: [String],

  // Metadata
  tags: [String],
  source: {
    type: String,
    enum: ['generated', 'template', 'custom', 'imported'],
    default: 'generated'
  },
  template: String,
  aiGenerated: {
    type: Boolean,
    default: false
  },
  aiModel: String,
  aiPrompt: String,
  aiConfidence: {
    type: Number,
    min: 0,
    max: 1
  }
}, {
  timestamps: true,
  index: [
    { id: 1 },
    { type: 1 },
    { difficulty: 1 },
    { levelRequirement: 1 },
    { state: 1 },
    { assignedTo: 1 },
    { 'stats.created': -1 }
  ]
})

// Indexes for performance optimization
questSchema.index({ 'generationContext.playerLevel': 1, difficulty: 1 })
questSchema.index({ type: 1, state: 1 })
questSchema.index({ category: 1, levelRequirement: 1 })
questSchema.index({ assignedTo: 1, state: 1 })
questSchema.index({ guildId: 1, type: 1 })
questSchema.index({ 'stats.created': -1 })
questSchema.index({ 'worldImpact.reputation.faction': 1 })
questSchema.index({ tags: 1 })
questSchema.index({ 'review.status': 1 })

// Virtual fields
questSchema.virtual('isAvailable').get(function() {
  return this.state === QUEST_CONFIG.STATES.ACTIVE &&
         !this.endTime || this.endTime > new Date()
})

questSchema.virtual('isCompleted').get(function() {
  return this.state === QUEST_CONFIG.STATES.COMPLETED
})

questSchema.virtual('completionPercentage').get(function() {
  if (this.objectives.length === 0) return 0
  const completed = this.objectives.filter(obj => obj.completed).length
  return Math.round((completed / this.objectives.length) * 100)
})

questSchema.virtual('totalRewards').get(function() {
  const rewards = [...(this.rewards.base || []), ...(this.rewards.bonus || [])]
  return rewards.reduce((total, reward) => total + reward.amount, 0)
})

// Instance methods
questSchema.methods.canBeAssigned = function(player) {
  // Check level requirement
  if (player.level < this.levelRequirement) return false
  if (this.maxLevel && player.level > this.maxLevel) return false

  // Check prerequisites
  for (const prereq of this.prerequisites) {
    if (!player.meetsPrerequisite(prereq)) return false
  }

  // Check if already assigned
  if (this.assignedTo.includes(player._id)) return false

  // Check cooldown
  if (this.cooldown > 0) {
    const lastCompletion = player.getLastCompletion(this.id)
    if (lastCompletion && Date.now() - lastCompletion < this.cooldown * 60 * 60 * 1000) {
      return false
    }
  }

  return true
}

questSchema.methods.updateProgress = function(objectiveId, progress) {
  const objective = this.objectives.find(obj => obj.id === objectiveId)
  if (!objective) return false

  objective.current = Math.min(progress, objective.required)
  objective.completed = objective.current >= objective.required

  // Update overall progress
  const totalObjectives = this.objectives.filter(obj => !obj.optional).length
  const completedObjectives = this.objectives.filter(obj => !obj.optional && obj.completed).length
  this.progress = Math.round((completedObjectives / totalObjectives) * 100)

  // Check for quest completion
  if (completedObjectives === totalObjectives) {
    this.state = QUEST_CONFIG.STATES.COMPLETED
    this.stats.completed = new Date()
  }

  this.stats.modified = new Date()
  return true
}

questSchema.methods.getCurrentObjective = function() {
  if (this.currentObjective) {
    return this.objectives.find(obj => obj.id === this.currentObjective)
  }

  // Find first incomplete non-optional objective
  return this.objectives.find(obj => !obj.completed && !obj.optional)
}

questSchema.methods.makeChoice = function(objectiveId, choiceId, player) {
  const objective = this.objectives.find(obj => obj.id === objectiveId)
  if (!objective || !objective.choices) return false

  const choice = objective.choices.find(c => c.id === choiceId)
  if (!choice) return false

  // Apply consequences
  for (const consequence of choice.consequences) {
    player.applyConsequence(consequence)
  }

  // Record choice in branching history
  if (this.branching.enabled) {
    this.branching.pathHistory.push({
      objectiveId,
      choice: choiceId,
      timestamp: new Date()
    })
  }

  // Update next objective if specified
  if (choice.nextObjective) {
    this.currentObjective = choice.nextObjective
  }

  this.stats.modified = new Date()
  return true
}

// Static methods
questSchema.statics.findByPlayer = function(playerId, filters = {}) {
  const query = { assignedTo: playerId, ...filters }
  return this.find(query).sort({ 'stats.created': -1 })
}

questSchema.statics.findAvailable = function(player, options = {}) {
  const query = {
    state: QUEST_CONFIG.STATES.ACTIVE,
    levelRequirement: { $lte: player.level },
    $or: [
      { maxLevel: { $exists: false } },
      { maxLevel: { $gte: player.level } }
    ]
  }

  if (options.type) query.type = options.type
  if (options.category) query.category = options.category
  if (options.difficulty) query.difficulty = options.difficulty

  return this.find(query)
}

questSchema.statics.generateId = function() {
  return `quest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

// Pre-save middleware
questSchema.pre('save', function(next) {
  if (this.isModified('objectives')) {
    // Recalculate progress
    const totalObjectives = this.objectives.filter(obj => !obj.optional).length
    const completedObjectives = this.objectives.filter(obj => !obj.optional && obj.completed).length
    this.progress = totalObjectives > 0 ? Math.round((completedObjectives / totalObjectives) * 100) : 0
  }

  if (this.isNew && !this.id) {
    this.id = this.constructor.generateId()
  }

  this.stats.modified = new Date()
  next()
})

// Post-save middleware
questSchema.post('save', function(doc) {
  // Trigger n8n webhook for quest updates
  if (process.env.N8N_WEBHOOK_URL) {
    fetch(`${process.env.N8N_WEBHOOK_URL}/quest-updated`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        questId: doc.id,
        state: doc.state,
        progress: doc.progress,
        assignedTo: doc.assignedTo
      })
    }).catch(console.error)
  }
})

export const Quest = mongoose.model('Quest', questSchema)
export default Quest