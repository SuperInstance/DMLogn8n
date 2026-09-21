import express from 'express'
import { body, param, query, validationResult } from 'express-validator'
import { Player } from '../database/models/index.js'
import { QUEST_CONFIG } from '../../config/quest-config.js'

const router = express.Router()

// Validation middleware
const handleValidationErrors = (req, res, next) => {
  const errors = validationResult(req)
  if (!errors.isEmpty()) {
    return res.status(400).json({
      success: false,
      errors: errors.array(),
      message: 'Validation failed'
    })
  }
  next()
}

/**
 * @route   GET /api/players
 * @desc    Get players with filtering and pagination
 * @access  Private
 */
router.get('/', [
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 }),
  query('level').optional().isInt({ min: 1, max: 100 }),
  query('class').optional().isString(),
  query('guildId').optional().isString(),
  query('status').optional().isIn(['active', 'inactive', 'suspended', 'banned']),
  query('sortBy').optional().isIn(['createdAt', 'updatedAt', 'stats.level', 'username']),
  query('sortOrder').optional().isIn(['asc', 'desc'])
], handleValidationErrors, async (req, res) => {
  try {
    const {
      page = 1,
      limit = 20,
      level,
      class: playerClass,
      guildId,
      status,
      sortBy = 'createdAt',
      sortOrder = 'desc'
    } = req.query

    // Build query
    const query = {}

    if (level) query['stats.level'] = parseInt(level)
    if (playerClass) query['character.class'] = playerClass
    if (guildId) query.guildId = guildId
    if (status) query.status = status

    // Build sort object
    const sort = {}
    sort[sortBy] = sortOrder === 'asc' ? 1 : -1

    // Execute query with pagination
    const skip = (parseInt(page) - 1) * parseInt(limit)

    const [players, total] = await Promise.all([
      Player.find(query)
        .select('-password') // Exclude password
        .sort(sort)
        .skip(skip)
        .limit(parseInt(limit))
        .lean(),
      Player.countDocuments(query)
    ])

    // Return paginated results
    res.json({
      success: true,
      data: {
        players,
        pagination: {
          currentPage: parseInt(page),
          totalPages: Math.ceil(total / parseInt(limit)),
          totalPlayers: total,
          hasNext: page * limit < total,
          hasPrev: page > 1
        }
      },
      message: 'Players retrieved successfully'
    })

  } catch (error) {
    console.error('Error getting players:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   GET /api/players/:playerId
 * @desc    Get player by ID
 * @access  Private
 */
router.get('/:playerId', [
  param('playerId').isMongoId().withMessage('Invalid player ID')
], handleValidationErrors, async (req, res) => {
  try {
    const { playerId } = req.params

    const player = await Player.findOne({ _id: playerId })
      .select('-password') // Exclude password
      .lean()

    if (!player) {
      return res.status(404).json({
        success: false,
        message: 'Player not found'
      })
    }

    res.json({
      success: true,
      data: player,
      message: 'Player retrieved successfully'
    })

  } catch (error) {
    console.error('Error getting player:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   POST /api/players
 * @desc    Create a new player
 * @access  Public
 */
router.post('/', [
  body('userId').notEmpty().withMessage('User ID is required'),
  body('username').isLength({ min: 3, max: 30 }).matches(/^[a-zA-Z0-9_]+$/)
    .withMessage('Username must be 3-30 characters, alphanumeric and underscore only'),
  body('email').isEmail().normalizeEmail()
    .withMessage('Valid email is required'),
  body('password').isLength({ min: 8 })
    .withMessage('Password must be at least 8 characters'),
  body('character.name').notEmpty().isLength({ min: 2, max: 50 })
    .withMessage('Character name must be between 2 and 50 characters'),
  body('character.class').isIn(['warrior', 'mage', 'rogue', 'cleric', 'ranger', 'paladin', 'warlock', 'bard', 'monk', 'druid'])
    .withMessage('Invalid character class'),
  body('character.race').isIn(['human', 'elf', 'dwarf', 'orc', 'halfling', 'gnome', 'dragonborn', 'tiefling'])
    .withMessage('Invalid character race')
], handleValidationErrors, async (req, res) => {
  try {
    const playerData = req.body

    // Check if user ID or username already exists
    const existingPlayer = await Player.findOne({
      $or: [
        { userId: playerData.userId },
        { username: playerData.username },
        { email: playerData.email }
      ]
    })

    if (existingPlayer) {
      return res.status(409).json({
        success: false,
        message: 'User ID, username, or email already exists'
      })
    }

    // Create player
    const player = new Player(playerData)
    await player.save()

    // Remove password from response
    const playerResponse = player.toObject()
    delete playerResponse.password

    res.status(201).json({
      success: true,
      data: playerResponse,
      message: 'Player created successfully'
    })

  } catch (error) {
    console.error('Error creating player:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   PUT /api/players/:playerId
 * @desc    Update player
 * @access  Private
 */
router.put('/:playerId', [
  param('playerId').isMongoId().withMessage('Invalid player ID'),
  body('username').optional().isLength({ min: 3, max: 30 }).matches(/^[a-zA-Z0-9_]+$/),
  body('character.name').optional().isLength({ min: 2, max: 50 }),
  body('stats.level').optional().isInt({ min: 1, max: 100 }),
  body('questPreferences.types').optional().isObject()
], handleValidationErrors, async (req, res) => {
  try {
    const { playerId } = req.params
    const updateData = req.body

    // Don't allow password updates through this route
    delete updateData.password

    // Check if username is being updated and if it already exists
    if (updateData.username) {
      const existingPlayer = await Player.findOne({
        _id: { $ne: playerId },
        username: updateData.username
      })

      if (existingPlayer) {
        return res.status(409).json({
          success: false,
          message: 'Username already exists'
        })
      }
    }

    const player = await Player.findByIdAndUpdate(
      playerId,
      { ...updateData, updatedAt: new Date() },
      { new: true, runValidators: true }
    ).select('-password')

    if (!player) {
      return res.status(404).json({
        success: false,
        message: 'Player not found'
      })
    }

    res.json({
      success: true,
      data: player,
      message: 'Player updated successfully'
    })

  } catch (error) {
    console.error('Error updating player:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   DELETE /api/players/:playerId
 * @desc    Delete player
 * @access  Private
 */
router.delete('/:playerId', [
  param('playerId').isMongoId().withMessage('Invalid player ID')
], handleValidationErrors, async (req, res) => {
  try {
    const { playerId } = req.params

    const player = await Player.findByIdAndDelete(playerId)

    if (!player) {
      return res.status(404).json({
        success: false,
        message: 'Player not found'
      })
    }

    res.json({
      success: true,
      data: player,
      message: 'Player deleted successfully'
    })

  } catch (error) {
    console.error('Error deleting player:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   GET /api/players/:playerId/quests/recommendations
 * @desc    Get personalized quest recommendations for player
 * @access  Private
 */
router.get('/:playerId/quests/recommendations', [
  param('playerId').isMongoId().withMessage('Invalid player ID'),
  query('count').optional().isInt({ min: 1, max: 10 })
], handleValidationErrors, async (req, res) => {
  try {
    const { playerId } = req.params
    const { count = 5 } = req.query

    const player = await Player.findOne({ _id: playerId })
    if (!player) {
      return res.status(404).json({
        success: false,
        message: 'Player not found'
      })
    }

    // Get quest recommendations (this would use QuestGenerationEngine)
    const recommendations = await generateQuestRecommendations(player, parseInt(count))

    res.json({
      success: true,
      data: recommendations,
      message: 'Quest recommendations retrieved successfully'
    })

  } catch (error) {
    console.error('Error getting quest recommendations:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   GET /api/players/:playerId/analytics
 * @desc    Get player quest analytics
 * @access  Private
 */
router.get('/:playerId/analytics', [
  param('playerId').isMongoId().withMessage('Invalid player ID'),
  query('timeframe').optional().isIn(['24h', '7d', '30d', 'all'])
], handleValidationErrors, async (req, res) => {
  try {
    const { playerId } = req.params
    const { timeframe = '30d' } = req.query

    const player = await Player.findOne({ _id: playerId })
    if (!player) {
      return res.status(404).json({
        success: false,
        message: 'Player not found'
      })
    }

    const analytics = await generatePlayerAnalytics(player, timeframe)

    res.json({
      success: true,
      data: analytics,
      message: 'Player analytics retrieved successfully'
    })

  } catch (error) {
    console.error('Error getting player analytics:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   POST /api/players/:playerId/preferences
 * @desc    Update player quest preferences
 * @access  Private
 */
router.post('/:playerId/preferences', [
  param('playerId').isMongoId().withMessage('Invalid player ID'),
  body('types').optional().isObject(),
  body('difficulty').optional().isObject(),
  body('questLength').optional().isIn(['short', 'medium', 'long', 'epic']),
  body('playStyle').optional().isIn(['solo', 'duo', 'small_group', 'large_group', 'guild']),
  body('partySize').optional().isObject()
], handleValidationErrors, async (req, res) => {
  try {
    const { playerId } = req.params
    const preferences = req.body

    const player = await Player.findOne({ _id: playerId })
    if (!player) {
      return res.status(404).json({
        success: false,
        message: 'Player not found'
      })
    }

    // Update preferences
    player.updateQuestPreferences(preferences)
    await player.save()

    res.json({
      success: true,
      data: player.questPreferences,
      message: 'Player preferences updated successfully'
    })

  } catch (error) {
    console.error('Error updating player preferences:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   GET /api/players/:playerId/achievements
 * @desc    Get player achievements
 * @access  Private
 */
router.get('/:playerId/achievements', [
  param('playerId').isMongoId().withMessage('Invalid player ID')
], handleValidationErrors, async (req, res) => {
  try {
    const { playerId } = req.params

    const player = await Player.findOne({ _id: playerId })
      .select('achievements stats.level stats.experience questHistory')
      .lean()

    if (!player) {
      return res.status(404).json({
        success: false,
        message: 'Player not found'
      })
    }

    const achievements = await generatePlayerAchievements(player)

    res.json({
      success: true,
      data: achievements,
      message: 'Player achievements retrieved successfully'
    })

  } catch (error) {
    console.error('Error getting player achievements:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   POST /api/players/:playerId/achievements
 * @desc    Add achievement to player
 * @access  Private
 */
router.post('/:playerId/achievements', [
  param('playerId').isMongoId().withMessage('Invalid player ID'),
  body('id').notEmpty().withMessage('Achievement ID is required'),
  body('name').notEmpty().withMessage('Achievement name is required'),
  body('description').notEmpty().withMessage('Achievement description is required'),
  body('category').notEmpty().withMessage('Achievement category is required'),
  body('rarity').isIn(['common', 'uncommon', 'rare', 'epic', 'legendary'])
    .withMessage('Invalid achievement rarity')
], handleValidationErrors, async (req, res) => {
  try {
    const { playerId } = req.params
    const achievementData = req.body

    const player = await Player.findOne({ _id: playerId })
    if (!player) {
      return res.status(404).json({
        success: false,
        message: 'Player not found'
      })
    }

    // Check if player already has this achievement
    const existingAchievement = player.achievements.find(a => a.id === achievementData.id)
    if (existingAchievement) {
      return res.status(409).json({
        success: false,
        message: 'Player already has this achievement'
      })
    }

    // Add achievement
    player.achievements.push({
      ...achievementData,
      unlockedAt: new Date()
    })

    await player.save()

    res.status(201).json({
      success: true,
      data: achievementData,
      message: 'Achievement added successfully'
    })

  } catch (error) {
    console.error('Error adding achievement:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   GET /api/players/search
 * @desc    Search players
 * @access  Private
 */
router.get('/search', [
  query('q').notEmpty().withMessage('Search query is required'),
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 50 })
], handleValidationErrors, async (req, res) => {
  try {
    const { q, page = 1, limit = 20 } = req.query

    // Build search query
    const searchQuery = {
      $or: [
        { username: { $regex: q, $options: 'i' } },
        { 'character.name': { $regex: q, $options: 'i' } },
        { email: { $regex: q, $options: 'i' } }
      ]
    }

    const skip = (parseInt(page) - 1) * parseInt(limit)

    const [players, total] = await Promise.all([
      Player.find(searchQuery)
        .select('-password') // Exclude password
        .sort({ username: 1 })
        .skip(skip)
        .limit(parseInt(limit))
        .lean(),
      Player.countDocuments(searchQuery)
    ])

    res.json({
      success: true,
      data: {
        players,
        pagination: {
          currentPage: parseInt(page),
          totalPages: Math.ceil(total / parseInt(limit)),
          totalPlayers: total,
          hasNext: page * limit < total,
          hasPrev: page > 1
        },
        searchQuery: q
      },
      message: 'Player search completed'
    })

  } catch (error) {
    console.error('Error searching players:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

// Helper functions (these would typically be in a service layer)

async function generateQuestRecommendations(player, count) {
  // This would integrate with QuestGenerationEngine
  return {
    recommendations: [
      {
        type: 'combat',
        category: 'dungeon',
        difficulty: player.stats.level / 10 + 2,
        estimatedTime: 45,
        reasons: ['Matches your combat preference', 'Suitable for your level']
      }
    ]
  }
}

async function generatePlayerAnalytics(player, timeframe) {
  // Generate analytics based on quest history
  const completedQuests = player.questHistory.filter(q => q.completed)
  const totalQuests = player.questHistory.length

  return {
    overview: {
      totalQuests,
      completedQuests: completedQuests.length,
      completionRate: totalQuests > 0 ? (completedQuests.length / totalQuests) * 100 : 0,
      averageRating: player.analytics.averageRating || 0,
      totalPlayTime: player.totalPlayTime || 0
    },
    performance: {
      averageCompletionTime: player.analytics.averageCompletionTime || 0,
      favoriteQuestType: player.analytics.favoriteQuestType || 'side_quest',
      favoriteDifficulty: player.analytics.favoriteDifficulty || 3
    },
    progression: {
      currentLevel: player.stats.level,
      totalExperience: player.stats.experience.total,
      achievements: player.achievements.length
    }
  }
}

async function generatePlayerAchievements(player) {
  // Generate achievement list including unlocked and available
  return {
    unlocked: player.achievements,
    available: [
      {
        id: 'first_quest',
        name: 'First Steps',
        description: 'Complete your first quest',
        category: 'progression',
        rarity: 'common',
        progress: player.questHistory.length > 0 ? 100 : 0,
        unlocked: player.questHistory.length > 0
      }
    ]
  }
}

export default router