import express from 'express'
import { body, param, query, validationResult } from 'express-validator'
import QuestManager from '../management/QuestManager.js'
import { Quest, Player } from '../database/models/index.js'
import { QUEST_CONFIG } from '../../config/quest-config.js'

const router = express.Router()
const questManager = new QuestManager()

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
 * @route   GET /api/quests
 * @desc    Get quests with filtering and pagination
 * @access  Public
 */
router.get('/', [
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 }),
  query('type').optional().isIn(Object.values(QUEST_CONFIG.QUEST_TYPES)),
  query('category').optional().isIn(Object.values(QUEST_CONFIG.CATEGORIES)),
  query('difficulty').optional().isInt({ min: 1, max: 7 }),
  query('state').optional().isIn(Object.values(QUEST_CONFIG.STATES)),
  query('playerId').optional().isMongoId(),
  query('guildId').optional().isString(),
  query('tags').optional().isString(),
  query('sortBy').optional().isIn(['createdAt', 'updatedAt', 'difficulty', 'title']),
  query('sortOrder').optional().isIn(['asc', 'desc'])
], handleValidationErrors, async (req, res) => {
  try {
    const {
      page = 1,
      limit = 20,
      type,
      category,
      difficulty,
      state,
      playerId,
      guildId,
      tags,
      sortBy = 'createdAt',
      sortOrder = 'desc'
    } = req.query

    // Build query
    const query = {}

    if (type) query.type = type
    if (category) query.category = category
    if (difficulty) query.difficulty = parseInt(difficulty)
    if (state) query.state = state
    if (playerId) query.assignedTo = playerId
    if (guildId) query.guildId = guildId

    if (tags) {
      const tagArray = tags.split(',').map(tag => tag.trim())
      query.tags = { $in: tagArray }
    }

    // Build sort object
    const sort = {}
    sort[sortBy] = sortOrder === 'asc' ? 1 : -1

    // Execute query with pagination
    const skip = (parseInt(page) - 1) * parseInt(limit)

    const [quests, total] = await Promise.all([
      Quest.find(query)
        .sort(sort)
        .skip(skip)
        .limit(parseInt(limit))
        .lean(),
      Quest.countDocuments(query)
    ])

    // Return paginated results
    res.json({
      success: true,
      data: {
        quests,
        pagination: {
          currentPage: parseInt(page),
          totalPages: Math.ceil(total / parseInt(limit)),
          totalQuests: total,
          hasNext: page * limit < total,
          hasPrev: page > 1
        }
      },
      message: 'Quests retrieved successfully'
    })

  } catch (error) {
    console.error('Error getting quests:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   GET /api/quests/:questId
 * @desc    Get quest by ID
 * @access  Public
 */
router.get('/:questId', [
  param('questId').notEmpty().withMessage('Quest ID is required')
], handleValidationErrors, async (req, res) => {
  try {
    const { questId } = req.params

    const quest = await Quest.findOne({ id: questId }).lean()

    if (!quest) {
      return res.status(404).json({
        success: false,
        message: 'Quest not found'
      })
    }

    res.json({
      success: true,
      data: quest,
      message: 'Quest retrieved successfully'
    })

  } catch (error) {
    console.error('Error getting quest:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   POST /api/quests
 * @desc    Create a new quest
 * @access  Private
 */
router.post('/', [
  body('title').notEmpty().isLength({ min: 5, max: 100 })
    .withMessage('Title must be between 5 and 100 characters'),
  body('description').notEmpty().isLength({ min: 50, max: 2000 })
    .withMessage('Description must be between 50 and 2000 characters'),
  body('type').isIn(Object.values(QUEST_CONFIG.QUEST_TYPES))
    .withMessage('Invalid quest type'),
  body('category').isIn(Object.values(QUEST_CONFIG.CATEGORIES))
    .withMessage('Invalid quest category'),
  body('difficulty').isInt({ min: 1, max: 7 })
    .withMessage('Difficulty must be between 1 and 7'),
  body('levelRequirement').optional().isInt({ min: 1, max: 100 })
    .withMessage('Level requirement must be between 1 and 100'),
  body('objectives').isArray({ min: 1 })
    .withMessage('At least one objective is required'),
  body('rewards.base').optional().isArray()
    .withMessage('Base rewards must be an array')
], handleValidationErrors, async (req, res) => {
  try {
    const questData = req.body

    // Create quest
    const quest = new Quest(questData)
    await quest.save()

    res.status(201).json({
      success: true,
      data: quest,
      message: 'Quest created successfully'
    })

  } catch (error) {
    console.error('Error creating quest:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   PUT /api/quests/:questId
 * @desc    Update quest
 * @access  Private
 */
router.put('/:questId', [
  param('questId').notEmpty().withMessage('Quest ID is required'),
  body('title').optional().isLength({ min: 5, max: 100 }),
  body('description').optional().isLength({ min: 50, max: 2000 }),
  body('difficulty').optional().isInt({ min: 1, max: 7 })
], handleValidationErrors, async (req, res) => {
  try {
    const { questId } = req.params
    const updateData = req.body

    const quest = await Quest.findOneAndUpdate(
      { id: questId },
      { ...updateData, updatedAt: new Date() },
      { new: true, runValidators: true }
    )

    if (!quest) {
      return res.status(404).json({
        success: false,
        message: 'Quest not found'
      })
    }

    res.json({
      success: true,
      data: quest,
      message: 'Quest updated successfully'
    })

  } catch (error) {
    console.error('Error updating quest:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   DELETE /api/quests/:questId
 * @desc    Delete quest
 * @access  Private
 */
router.delete('/:questId', [
  param('questId').notEmpty().withMessage('Quest ID is required')
], handleValidationErrors, async (req, res) => {
  try {
    const { questId } = req.params

    const quest = await Quest.findOneAndDelete({ id: questId })

    if (!quest) {
      return res.status(404).json({
        success: false,
        message: 'Quest not found'
      })
    }

    res.json({
      success: true,
      data: quest,
      message: 'Quest deleted successfully'
    })

  } catch (error) {
    console.error('Error deleting quest:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   POST /api/quests/generate
 * @desc    Generate a new quest using AI or templates
 * @access  Private
 */
router.post('/generate', [
  body('playerId').notEmpty().withMessage('Player ID is required'),
  body('questType').optional().isIn(Object.values(QUEST_CONFIG.QUEST_TYPES)),
  body('category').optional().isIn(Object.values(QUEST_CONFIG.CATEGORIES)),
  body('difficulty').optional().isInt({ min: 1, max: 7 }),
  body('personalized').optional().isBoolean(),
  body('forceAI').optional().isBoolean()
], handleValidationErrors, async (req, res) => {
  try {
    const {
      playerId,
      questType,
      category,
      difficulty,
      personalized = true,
      forceAI = false
    } = req.body

    // Get player
    const player = await Player.findOne({ _id: playerId })
    if (!player) {
      return res.status(404).json({
        success: false,
        message: 'Player not found'
      })
    }

    // Generate quest
    const options = {
      type: questType,
      category,
      difficulty,
      personalized,
      forceAI,
      ...req.body.options
    }

    const result = await questManager.generatePersonalizedQuest(playerId, options)

    res.status(201).json(result)

  } catch (error) {
    console.error('Error generating quest:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   POST /api/quests/:questId/assign
 * @desc    Assign quest to player
 * @access  Private
 */
router.post('/:questId/assign', [
  param('questId').notEmpty().withMessage('Quest ID is required'),
  body('playerId').notEmpty().withMessage('Player ID is required')
], handleValidationErrors, async (req, res) => {
  try {
    const { questId } = req.params
    const { playerId } = req.body

    const result = await questManager.assignQuestToPlayer(questId, playerId)

    res.json(result)

  } catch (error) {
    console.error('Error assigning quest:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   POST /api/quests/:questId/progress
 * @desc    Update quest progress
 * @access  Private
 */
router.post('/:questId/progress', [
  param('questId').notEmpty().withMessage('Quest ID is required'),
  body('playerId').notEmpty().withMessage('Player ID is required'),
  body('objectiveId').optional().isString(),
  body('progress').isInt({ min: 0 }),
  body('data').optional().isObject()
], handleValidationErrors, async (req, res) => {
  try {
    const { questId } = req.params
    const { playerId, objectiveId, progress, data = {} } = req.body

    const result = await questManager.updateQuestProgress(questId, playerId, objectiveId, progress, data)

    res.json(result)

  } catch (error) {
    console.error('Error updating quest progress:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   POST /api/quests/:questId/complete
 * @desc    Complete quest
 * @access  Private
 */
router.post('/:questId/complete', [
  param('questId').notEmpty().withMessage('Quest ID is required'),
  body('playerId').notEmpty().withMessage('Player ID is required'),
  body('rating').optional().isInt({ min: 1, max: 5 }),
  body('feedback').optional().isString(),
  body('choice').optional().isString()
], handleValidationErrors, async (req, res) => {
  try {
    const { questId } = req.params
    const { playerId, rating, feedback, choice } = req.body

    const completionData = { rating, feedback, choice }
    const result = await questManager.completeQuest(questId, playerId, completionData)

    res.json(result)

  } catch (error) {
    console.error('Error completing quest:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   POST /api/quests/:questId/abandon
 * @desc    Abandon quest
 * @access  Private
 */
router.post('/:questId/abandon', [
  param('questId').notEmpty().withMessage('Quest ID is required'),
  body('playerId').notEmpty().withMessage('Player ID is required'),
  body('reason').optional().isString()
], handleValidationErrors, async (req, res) => {
  try {
    const { questId } = req.params
    const { playerId, reason } = req.body

    const result = await questManager.abandonQuest(questId, playerId, reason)

    res.json(result)

  } catch (error) {
    console.error('Error abandoning quest:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   POST /api/quests/:questId/choice
 * @desc    Make a choice in a branching quest
 * @access  Private
 */
router.post('/:questId/choice', [
  param('questId').notEmpty().withMessage('Quest ID is required'),
  body('playerId').notEmpty().withMessage('Player ID is required'),
  body('objectiveId').notEmpty().withMessage('Objective ID is required'),
  body('choiceId').notEmpty().withMessage('Choice ID is required')
], handleValidationErrors, async (req, res) => {
  try {
    const { questId } = req.params
    const { playerId, objectiveId, choiceId } = req.body

    const result = await questManager.makeQuestChoice(questId, playerId, objectiveId, choiceId)

    res.json(result)

  } catch (error) {
    console.error('Error making quest choice:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   GET /api/quests/player/:playerId/active
 * @desc    Get player's active quests
 * @access  Private
 */
router.get('/player/:playerId/active', [
  param('playerId').isMongoId().withMessage('Invalid player ID')
], handleValidationErrors, async (req, res) => {
  try {
    const { playerId } = req.params

    const quests = await questManager.getPlayerActiveQuests(playerId)

    res.json({
      success: true,
      data: quests,
      message: 'Active quests retrieved successfully'
    })

  } catch (error) {
    console.error('Error getting active quests:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   GET /api/quests/player/:playerId/history
 * @desc    Get player's quest history
 * @access  Private
 */
router.get('/player/:playerId/history', [
  param('playerId').isMongoId().withMessage('Invalid player ID'),
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 50 }),
  query('type').optional().isIn(Object.values(QUEST_CONFIG.QUEST_TYPES)),
  query('state').optional().isIn(Object.values(QUEST_CONFIG.STATES))
], handleValidationErrors, async (req, res) => {
  try {
    const { playerId } = req.params
    const { page = 1, limit = 20, type, state } = req.query

    const options = {
      page: parseInt(page),
      limit: parseInt(limit),
      type,
      state
    }

    const quests = await questManager.getPlayerQuestHistory(playerId, options)

    res.json({
      success: true,
      data: quests,
      message: 'Quest history retrieved successfully'
    })

  } catch (error) {
    console.error('Error getting quest history:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   GET /api/quests/player/:playerId/available
 * @desc    Get available quests for player
 * @access  Private
 */
router.get('/player/:playerId/available', [
  param('playerId').isMongoId().withMessage('Invalid player ID'),
  query('type').optional().isIn(Object.values(QUEST_CONFIG.QUEST_TYPES)),
  query('category').optional().isIn(Object.values(QUEST_CONFIG.CATEGORIES)),
  query('difficulty').optional().isInt({ min: 1, max: 7 }),
  query('limit').optional().isInt({ min: 1, max: 20 })
], handleValidationErrors, async (req, res) => {
  try {
    const { playerId } = req.params
    const { type, category, difficulty, limit = 10 } = req.query

    const options = { type, category, difficulty, limit }
    const quests = await questManager.getAvailableQuests(playerId, options)

    res.json({
      success: true,
      data: quests,
      message: 'Available quests retrieved successfully'
    })

  } catch (error) {
    console.error('Error getting available quests:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   GET /api/quests/statistics
 * @desc    Get quest statistics
 * @access  Private
 */
router.get('/statistics', [
  query('timeframe').optional().isIn(['1h', '24h', '7d', '30d']),
  query('playerId').optional().isMongoId()
], handleValidationErrors, async (req, res) => {
  try {
    const { timeframe = '24h', playerId } = req.query

    const stats = await questManager.getQuestStatistics({ timeframe, playerId })

    res.json({
      success: true,
      data: stats,
      message: 'Quest statistics retrieved successfully'
    })

  } catch (error) {
    console.error('Error getting quest statistics:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

/**
 * @route   GET /api/quests/search
 * @desc    Search quests
 * @access  Public
 */
router.get('/search', [
  query('q').notEmpty().withMessage('Search query is required'),
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 50 }),
  query('type').optional().isIn(Object.values(QUEST_CONFIG.QUEST_TYPES)),
  query('category').optional().isIn(Object.values(QUEST_CONFIG.CATEGORIES))
], handleValidationErrors, async (req, res) => {
  try {
    const { q, page = 1, limit = 20, type, category } = req.query

    // Build search query
    const searchQuery = {
      $and: []
    }

    // Text search
    searchQuery.$and.push({
      $or: [
        { title: { $regex: q, $options: 'i' } },
        { description: { $regex: q, $options: 'i' } },
        { tags: { $in: [new RegExp(q, 'i')] } }
      ]
    })

    // Add filters
    if (type) searchQuery.$and.push({ type })
    if (category) searchQuery.$and.push({ category })

    const skip = (parseInt(page) - 1) * parseInt(limit)

    const [quests, total] = await Promise.all([
      Quest.find(searchQuery)
        .sort({ createdAt: -1 })
        .skip(skip)
        .limit(parseInt(limit))
        .lean(),
      Quest.countDocuments(searchQuery)
    ])

    res.json({
      success: true,
      data: {
        quests,
        pagination: {
          currentPage: parseInt(page),
          totalPages: Math.ceil(total / parseInt(limit)),
          totalQuests: total,
          hasNext: page * limit < total,
          hasPrev: page > 1
        },
        searchQuery: q
      },
      message: 'Quest search completed'
    })

  } catch (error) {
    console.error('Error searching quests:', error)
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error.message
    })
  }
})

export default router