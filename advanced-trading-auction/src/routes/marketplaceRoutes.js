const express = require('express');
const { body, param, query } = require('express-validator');
const MarketplaceController = require('../controllers/MarketplaceController');
const auth = require('../middleware/auth');

const createMarketplaceRoutes = (knex, redis) => {
  const router = express.Router();
  const marketplaceController = new MarketplaceController(knex, redis);

  // Middleware to add database instance to request
  router.use((req, res, next) => {
    req.db = knex;
    next();
  });

  /**
   * @route   POST /api/marketplace/listings
   * @desc    Create a new marketplace listing
   * @access  Private
   */
  router.post('/listings',
    auth,
    [
      body('itemId')
        .notEmpty()
        .withMessage('Item ID is required'),
      body('quantity')
        .isInt({ min: 1 })
        .withMessage('Quantity must be at least 1'),
      body('price')
        .isFloat({ min: 0.01 })
        .withMessage('Price must be greater than 0'),
      body('regionId')
        .optional()
        .isIn(['global', 'north', 'south', 'east', 'west'])
        .withMessage('Invalid region ID'),
      body('listingType')
        .optional()
        .isIn(['fixed', 'negotiable'])
        .withMessage('Listing type must be fixed or negotiable'),
      body('minimumOffer')
        .optional()
        .isFloat({ min: 0 })
        .withMessage('Minimum offer must be non-negative'),
      body('autoAcceptPrice')
        .optional()
        .isFloat({ min: 0 })
        .withMessage('Auto accept price must be non-negative'),
      body('duration')
        .optional()
        .isInt({ min: 3600000, max: 30 * 24 * 60 * 60 * 1000 }) // 1 hour to 30 days
        .withMessage('Duration must be between 1 hour and 30 days'),
      body('description')
        .optional()
        .isLength({ max: 1000 })
        .withMessage('Description must be less than 1000 characters'),
      body('tags')
        .optional()
        .isArray()
        .withMessage('Tags must be an array')
    ],
    marketplaceController.createListing.bind(marketplaceController)
  );

  /**
   * @route   POST /api/marketplace/listings/:listingId/purchase
   * @desc    Purchase an item from a listing
   * @access  Private
   */
  router.post('/listings/:listingId/purchase',
    auth,
    [
      param('listingId')
        .isUUID()
        .withMessage('Invalid listing ID'),
      body('quantity')
        .optional()
        .isInt({ min: 1 })
        .withMessage('Quantity must be at least 1')
    ],
    marketplaceController.purchaseListing.bind(marketplaceController)
  );

  /**
   * @route   POST /api/marketplace/listings/:listingId/offer
   * @desc    Make an offer on a negotiable listing
   * @access  Private
   */
  router.post('/listings/:listingId/offer',
    auth,
    [
      param('listingId')
        .isUUID()
        .withMessage('Invalid listing ID'),
      body('amount')
        .isFloat({ min: 0.01 })
        .withMessage('Offer amount must be greater than 0'),
      body('message')
        .optional()
        .isLength({ max: 500 })
        .withMessage('Message must be less than 500 characters')
    ],
    marketplaceController.makeOffer.bind(marketplaceController)
  );

  /**
   * @route   PUT /api/marketplace/offers/:offerId/respond
   * @desc    Respond to an offer
   * @access  Private
   */
  router.put('/offers/:offerId/respond',
    auth,
    [
      param('offerId')
        .isUUID()
        .withMessage('Invalid offer ID'),
      body('response')
        .isIn(['accept', 'reject', 'counter'])
        .withMessage('Response must be accept, reject, or counter'),
      body('counterAmount')
        .optional()
        .isFloat({ min: 0.01 })
        .withMessage('Counter amount must be greater than 0'),
      body('message')
        .optional()
        .isLength({ max: 500 })
        .withMessage('Message must be less than 500 characters')
    ],
    marketplaceController.respondToOffer.bind(marketplaceController)
  );

  /**
   * @route   GET /api/marketplace/listings
   * @desc    Search marketplace listings
   * @access  Public
   */
  router.get('/listings',
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
      query('categoryIds')
        .optional()
        .custom(value => {
          if (typeof value === 'string') {
            const ids = value.split(',');
            return ids.every(id => /^[0-9a-f-]{36}$/i.test(id.trim()));
          }
          return true;
        })
        .withMessage('Invalid category IDs format'),
      query('minPrice')
        .optional()
        .isFloat({ min: 0 })
        .withMessage('Minimum price must be non-negative'),
      query('maxPrice')
        .optional()
        .isFloat({ min: 0 })
        .withMessage('Maximum price must be non-negative'),
      query('listingType')
        .optional()
        .isIn(['fixed', 'negotiable'])
        .withMessage('Listing type must be fixed or negotiable'),
      query('tags')
        .optional()
        .custom(value => {
          if (typeof value === 'string') {
            return value.split(',').every(tag => tag.trim().length > 0);
          }
          return true;
        })
        .withMessage('Invalid tags format'),
      query('sortBy')
        .optional()
        .isIn(['created_at', 'price', 'views', 'updated_at'])
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
        .withMessage('Offset must be non-negative'),
      query('includeExpired')
        .optional()
        .isBoolean()
        .withMessage('Include expired must be a boolean')
    ],
    marketplaceController.searchListings.bind(marketplaceController)
  );

  /**
   * @route   GET /api/marketplace/listings/:listingId
   * @desc    Get listing details
   * @access  Public
   */
  router.get('/listings/:listingId',
    [
      param('listingId')
        .isUUID()
        .withMessage('Invalid listing ID')
    ],
    marketplaceController.getListing.bind(marketplaceController)
  );

  /**
   * @route   GET /api/marketplace/listings/player
   * @desc    Get player's listings
   * @access  Private
   */
  router.get('/listings/player',
    auth,
    [
      query('status')
        .optional()
        .isIn(['active', 'sold', 'expired', 'cancelled', 'all'])
        .withMessage('Invalid status')
    ],
    marketplaceController.getPlayerListings.bind(marketplaceController)
  );

  /**
   * @route   DELETE /api/marketplace/listings/:listingId
   * @desc    Cancel a listing
   * @access  Private
   */
  router.delete('/listings/:listingId',
    auth,
    [
      param('listingId')
        .isUUID()
        .withMessage('Invalid listing ID')
    ],
    marketplaceController.cancelListing.bind(marketplaceController)
  );

  /**
   * @route   POST /api/marketplace/trades
   * @desc    Create a trade request
   * @access  Private
   */
  router.post('/trades',
    auth,
    [
      body('targetId')
        .notEmpty()
        .withMessage('Target player ID is required'),
      body('requesterItems')
        .isArray()
        .withMessage('Requester items must be an array'),
      body('targetItems')
        .isArray()
        .withMessage('Target items must be an array'),
      body('requesterCurrency')
        .optional()
        .isFloat({ min: 0 })
        .withMessage('Requester currency must be non-negative'),
      body('targetCurrency')
        .optional()
        .isFloat({ min: 0 })
        .withMessage('Target currency must be non-negative'),
      body('message')
        .optional()
        .isLength({ max: 500 })
        .withMessage('Message must be less than 500 characters'),
      body('duration')
        .optional()
        .isInt({ min: 3600000, max: 7 * 24 * 60 * 60 * 1000 }) // 1 hour to 7 days
        .withMessage('Duration must be between 1 hour and 7 days')
    ],
    marketplaceController.createTradeRequest.bind(marketplaceController)
  );

  /**
   * @route   PUT /api/marketplace/trades/:tradeId/accept
   * @desc    Accept a trade request
   * @access  Private
   */
  router.put('/trades/:tradeId/accept',
    auth,
    [
      param('tradeId')
        .isUUID()
        .withMessage('Invalid trade ID')
    ],
    marketplaceController.acceptTradeRequest.bind(marketplaceController)
  );

  /**
   * @route   GET /api/marketplace/stats
   * @desc    Get marketplace statistics
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
    marketplaceController.getMarketplaceStats.bind(marketplaceController)
  );

  /**
   * @route   GET /api/marketplace/activity
   * @desc    Get player's marketplace activity
   * @access  Private
   */
  router.get('/activity',
    auth,
    [
      query('timeRange')
        .optional()
        .isInt({ min: 1, max: 365 })
        .withMessage('Time range must be between 1 and 365 days')
    ],
    marketplaceController.getPlayerMarketplaceActivity.bind(marketplaceController)
  );

  /**
   * @route   GET /api/marketplace/categories
   * @desc    Get marketplace categories
   * @access  Public
   */
  router.get('/categories',
    marketplaceController.getMarketplaceCategories.bind(marketplaceController)
  );

  /**
   * @route   GET /api/marketplace/featured
   * @desc    Get featured listings
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
    marketplaceController.getFeaturedListings.bind(marketplaceController)
  );

  /**
   * @route   GET /api/marketplace/trends
   * @desc    Get market trends
   * @access  Public
   */
  router.get('/trends',
    [
      query('regionId')
        .optional()
        .isIn(['global', 'north', 'south', 'east', 'west'])
        .withMessage('Invalid region ID'),
      query('timeRange')
        .optional()
        .isInt({ min: 1, max: 365 })
        .withMessage('Time range must be between 1 and 365 days'),
      query('categoryId')
        .optional()
        .isUUID()
        .withMessage('Invalid category ID')
    ],
    marketplaceController.getMarketTrends.bind(marketplaceController)
  );

  /**
   * @route   GET /api/marketplace/items/:itemId/price-history
   * @desc    Get price history for an item
   * @access  Public
   */
  router.get('/items/:itemId/price-history',
    [
      param('itemId')
        .isUUID()
        .withMessage('Invalid item ID'),
      query('regionId')
        .optional()
        .isIn(['global', 'north', 'south', 'east', 'west'])
        .withMessage('Invalid region ID'),
      query('timeRange')
        .optional()
        .isInt({ min: 1, max: 365 })
        .withMessage('Time range must be between 1 and 365 days')
    ],
    marketplaceController.getPriceHistory.bind(marketplaceController)
  );

  /**
   * @route   GET /api/marketplace/listings/:listingId/similar
   * @desc    Get similar listings
   * @access  Public
   */
  router.get('/listings/:listingId/similar',
    [
      param('listingId')
        .isUUID()
        .withMessage('Invalid listing ID'),
      query('limit')
        .optional()
        .isInt({ min: 1, max: 20 })
        .withMessage('Limit must be between 1 and 20')
    ],
    marketplaceController.getSimilarListings.bind(marketplaceController)
  );

  return router;
};

module.exports = createMarketplaceRoutes;