const express = require('express');
const { body, param, query } = require('express-validator');
const AuctionController = require('../controllers/AuctionController');
const auth = require('../middleware/auth');

const createAuctionRoutes = (knex, redis) => {
  const router = express.Router();
  const auctionController = new AuctionController(knex, redis);

  // Middleware to add database instance to request
  router.use((req, res, next) => {
    req.db = knex;
    next();
  });

  /**
   * @route   POST /api/auctions
   * @desc    Create a new auction
   * @access  Private
   */
  router.post('/',
    auth,
    [
      body('itemId')
        .notEmpty()
        .withMessage('Item ID is required'),
      body('quantity')
        .isInt({ min: 1 })
        .withMessage('Quantity must be at least 1'),
      body('startingPrice')
        .isFloat({ min: 0.01 })
        .withMessage('Starting price must be greater than 0'),
      body('reservePrice')
        .optional()
        .isFloat({ min: 0 })
        .withMessage('Reserve price must be non-negative'),
      body('buyoutPrice')
        .optional()
        .isFloat({ min: 0 })
        .withMessage('Buyout price must be non-negative'),
      body('duration')
        .optional()
        .isInt({ min: 3600000, max: 30 * 24 * 60 * 60 * 1000 }) // 1 hour to 30 days
        .withMessage('Duration must be between 1 hour and 30 days'),
      body('regionId')
        .optional()
        .isIn(['global', 'north', 'south', 'east', 'west'])
        .withMessage('Invalid region ID'),
      body('anonymous')
        .optional()
        .isBoolean()
        .withMessage('Anonymous must be a boolean'),
      body('autoRelist')
        .optional()
        .isBoolean()
        .withMessage('Auto relist must be a boolean')
    ],
    auctionController.createAuction.bind(auctionController)
  );

  /**
   * @route   POST /api/auctions/:auctionId/bid
   * @desc    Place a bid on an auction
   * @access  Private
   */
  router.post('/:auctionId/bid',
    auth,
    [
      param('auctionId')
        .isUUID()
        .withMessage('Invalid auction ID'),
      body('amount')
        .isFloat({ min: 0.01 })
        .withMessage('Bid amount must be greater than 0'),
      body('anonymous')
        .optional()
        .isBoolean()
        .withMessage('Anonymous must be a boolean')
    ],
    auctionController.placeBid.bind(auctionController)
  );

  /**
   * @route   GET /api/auctions/:auctionId
   * @desc    Get auction details
   * @access  Public
   */
  router.get('/:auctionId',
    [
      param('auctionId')
        .isUUID()
        .withMessage('Invalid auction ID'),
      query('includeBids')
        .optional()
        .isBoolean()
        .withMessage('Include bids must be a boolean')
    ],
    auctionController.getAuction.bind(auctionController)
  );

  /**
   * @route   GET /api/auctions
   * @desc    Search auctions
   * @access  Public
   */
  router.get('/',
    [
      query('itemId')
        .optional()
        .isUUID()
        .withMessage('Invalid item ID'),
      query('sellerId')
        .optional()
        .isUUID()
        .withMessage('Invalid seller ID'),
      query('regionId')
        .optional()
        .isIn(['global', 'north', 'south', 'east', 'west'])
        .withMessage('Invalid region ID'),
      query('minPrice')
        .optional()
        .isFloat({ min: 0 })
        .withMessage('Minimum price must be non-negative'),
      query('maxPrice')
        .optional()
        .isFloat({ min: 0 })
        .withMessage('Maximum price must be non-negative'),
      query('sortBy')
        .optional()
        .isIn(['end_time', 'current_bid', 'starting_price', 'created_at'])
        .withMessage('Invalid sort field'),
      query('sortOrder')
        .optional()
        .isIn(['asc', 'desc'])
        .withMessage('Sort order must be asc or desc'),
      query('limit')
        .optional()
        .isInt({ min: 1, max: 100 })
        .withMessage('Limit must be between 1 and 100'),
      query('offset')
        .optional()
        .isInt({ min: 0 })
        .withMessage('Offset must be non-negative')
    ],
    auctionController.searchAuctions.bind(auctionController)
  );

  /**
   * @route   GET /api/auctions/player/:type
   * @desc    Get player's auctions
   * @access  Private
   */
  router.get('/player/:type',
    auth,
    [
      param('type')
        .isIn(['selling', 'bidding'])
        .withMessage('Type must be selling or bidding')
    ],
    auctionController.getPlayerAuctions.bind(auctionController)
  );

  /**
   * @route   DELETE /api/auctions/:auctionId
   * @desc    Cancel an auction
   * @access  Private
   */
  router.delete('/:auctionId',
    auth,
    [
      param('auctionId')
        .isUUID()
        .withMessage('Invalid auction ID'),
      body('reason')
        .optional()
        .isIn(['seller_cancel', 'admin_cancel'])
        .withMessage('Invalid cancellation reason')
    ],
    auctionController.cancelAuction.bind(auctionController)
  );

  /**
   * @route   GET /api/auctions/stats
   * @desc    Get auction statistics
   * @access  Public
   */
  router.get('/stats',
    [
      query('regionId')
        .optional()
        .isIn(['global', 'north', 'south', 'east', 'west'])
        .withMessage('Invalid region ID'),
      query('timeRange')
        .optional()
        .isInt({ min: 1, max: 365 })
        .withMessage('Time range must be between 1 and 365 days')
    ],
    auctionController.getAuctionStats.bind(auctionController)
  );

  /**
   * @route   GET /api/auctions/:auctionId/bids
   * @desc    Get bid history for an auction
   * @access  Public
   */
  router.get('/:auctionId/bids',
    [
      param('auctionId')
        .isUUID()
        .withMessage('Invalid auction ID'),
      query('limit')
        .optional()
        .isInt({ min: 1, max: 100 })
        .withMessage('Limit must be between 1 and 100')
    ],
    auctionController.getBidHistory.bind(auctionController)
  );

  /**
   * @route   GET /api/auctions/categories
   * @desc    Get auction categories
   * @access  Public
   */
  router.get('/categories',
    auctionController.getAuctionCategories.bind(auctionController)
  );

  /**
   * @route   GET /api/auctions/featured
   * @desc    Get featured auctions
   * @access  Public
   */
  router.get('/featured',
    [
      query('regionId')
        .optional()
        .isIn(['global', 'north', 'south', 'east', 'west'])
        .withMessage('Invalid region ID'),
      query('limit')
        .optional()
        .isInt({ min: 1, max: 50 })
        .withMessage('Limit must be between 1 and 50')
    ],
    auctionController.getFeaturedAuctions.bind(auctionController)
  );

  /**
   * @route   GET /api/auctions/analytics
   * @desc    Get auction analytics
   * @access  Public
   */
  router.get('/analytics',
    [
      query('regionId')
        .optional()
        .isIn(['global', 'north', 'south', 'east', 'west'])
        .withMessage('Invalid region ID'),
      query('timeRange')
        .optional()
        .isInt({ min: 1, max: 365 })
        .withMessage('Time range must be between 1 and 365 days'),
      query('itemId')
        .optional()
        .isUUID()
        .withMessage('Invalid item ID')
    ],
    auctionController.getAuctionAnalytics.bind(auctionController)
  );

  return router;
};

module.exports = createAuctionRoutes;