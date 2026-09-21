const Marketplace = require('../models/Marketplace');
const EconomicEngine = require('../models/EconomicEngine');
const MarketAnalyzer = require('../models/MarketAnalyzer');
const { validationResult } = require('express-validator');

class MarketplaceController {
  constructor(knex, redis) {
    this.economicEngine = new EconomicEngine(redis, knex);
    this.marketAnalyzer = new MarketAnalyzer(knex, redis);
    this.marketplace = new Marketplace(knex, redis, this.economicEngine);
  }

  /**
   * Create a new marketplace listing
   */
  async createListing(req, res) {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({
          success: false,
          errors: errors.array()
        });
      }

      const listingData = {
        ...req.body,
        sellerId: req.user.id
      };

      const listing = await this.marketplace.createListing(listingData);

      res.status(201).json({
        success: true,
        data: listing,
        message: 'Listing created successfully'
      });
    } catch (error) {
      console.error('Error creating listing:', error);
      res.status(500).json({
        success: false,
        message: error.message || 'Failed to create listing'
      });
    }
  }

  /**
   * Purchase an item from a listing
   */
  async purchaseListing(req, res) {
    try {
      const { listingId } = req.params;
      const { quantity } = req.body;

      const result = await this.marketplace.purchaseListing(
        listingId,
        req.user.id,
        quantity
      );

      res.json({
        success: true,
        data: result,
        message: 'Item purchased successfully'
      });
    } catch (error) {
      console.error('Error purchasing listing:', error);
      res.status(500).json({
        success: false,
        message: error.message || 'Failed to purchase item'
      });
    }
  }

  /**
   * Make an offer on a negotiable listing
   */
  async makeOffer(req, res) {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({
          success: false,
          errors: errors.array()
        });
      }

      const { listingId } = req.params;
      const { amount, message } = req.body;

      const result = await this.marketplace.makeOffer(
        listingId,
        req.user.id,
        amount,
        message
      );

      res.status(201).json({
        success: true,
        data: result,
        message: 'Offer sent successfully'
      });
    } catch (error) {
      console.error('Error making offer:', error);
      res.status(500).json({
        success: false,
        message: error.message || 'Failed to make offer'
      });
    }
  }

  /**
   * Respond to an offer
   */
  async respondToOffer(req, res) {
    try {
      const { offerId } = req.params;
      const { response, counterAmount, message } = req.body;

      const result = await this.marketplace.respondToOffer(
        offerId,
        req.user.id,
        response,
        counterAmount,
        message
      );

      res.json({
        success: true,
        data: result,
        message: `Offer ${response} successfully`
      });
    } catch (error) {
      console.error('Error responding to offer:', error);
      res.status(500).json({
        success: false,
        message: error.message || 'Failed to respond to offer'
      });
    }
  }

  /**
   * Search marketplace listings
   */
  async searchListings(req, res) {
    try {
      const filters = {
        itemId: req.query.itemId,
        sellerId: req.query.sellerId,
        regionId: req.query.regionId,
        categoryIds: req.query.categoryIds ? req.query.categoryIds.split(',') : undefined,
        minPrice: req.query.minPrice ? parseFloat(req.query.minPrice) : undefined,
        maxPrice: req.query.maxPrice ? parseFloat(req.query.maxPrice) : undefined,
        listingType: req.query.listingType,
        tags: req.query.tags ? req.query.tags.split(',') : undefined,
        sortBy: req.query.sortBy || 'created_at',
        sortOrder: req.query.sortOrder || 'desc',
        limit: parseInt(req.query.limit) || 50,
        offset: parseInt(req.query.offset) || 0,
        includeExpired: req.query.includeExpired === 'true'
      };

      const listings = await this.marketplace.searchListings(filters);

      res.json({
        success: true,
        data: listings,
        pagination: {
          limit: filters.limit,
          offset: filters.offset,
          total: listings.length
        }
      });
    } catch (error) {
      console.error('Error searching listings:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to search listings'
      });
    }
  }

  /**
   * Get listing details
   */
  async getListing(req, res) {
    try {
      const { listingId } = req.params;
      const listing = await this.marketplace.getListing(listingId);

      if (!listing) {
        return res.status(404).json({
          success: false,
          message: 'Listing not found'
        });
      }

      // Increment view count
      await req.db('market_listings')
        .where('id', listingId)
        .increment('views', 1);

      res.json({
        success: true,
        data: listing
      });
    } catch (error) {
      console.error('Error getting listing:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get listing details'
      });
    }
  }

  /**
   * Get player's listings
   */
  async getPlayerListings(req, res) {
    try {
      const { status = 'active' } = req.query;
      const listings = await this.marketplace.searchListings({
        sellerId: req.user.id,
        sortBy: 'created_at',
        sortOrder: 'desc',
        limit: 100
      });

      // Filter by status if specified
      const filteredListings = status === 'all'
        ? listings
        : listings.filter(listing => listing.status === status);

      res.json({
        success: true,
        data: filteredListings
      });
    } catch (error) {
      console.error('Error getting player listings:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get player listings'
      });
    }
  }

  /**
   * Cancel a listing
   */
  async cancelListing(req, res) {
    try {
      const { listingId } = req.params;
      const listing = await this.marketplace.getListing(listingId);

      if (!listing) {
        return res.status(404).json({
          success: false,
          message: 'Listing not found'
        });
      }

      if (listing.seller_id !== req.user.id) {
        return res.status(403).json({
          success: false,
          message: 'You can only cancel your own listings'
        });
      }

      await this.marketplace.completeListing(listingId, 'cancelled');

      res.json({
        success: true,
        message: 'Listing cancelled successfully'
      });
    } catch (error) {
      console.error('Error cancelling listing:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to cancel listing'
      });
    }
  }

  /**
   * Create a trade request
   */
  async createTradeRequest(req, res) {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({
          success: false,
          errors: errors.array()
        });
      }

      const tradeData = {
        ...req.body,
        requesterId: req.user.id
      };

      const tradeRequest = await this.marketplace.createTradeRequest(tradeData);

      res.status(201).json({
        success: true,
        data: tradeRequest,
        message: 'Trade request sent successfully'
      });
    } catch (error) {
      console.error('Error creating trade request:', error);
      res.status(500).json({
        success: false,
        message: error.message || 'Failed to create trade request'
      });
    }
  }

  /**
   * Accept a trade request
   */
  async acceptTradeRequest(req, res) {
    try {
      const { tradeId } = req.params;

      const result = await this.marketplace.acceptTradeRequest(tradeId, req.user.id);

      res.json({
        success: true,
        data: result,
        message: 'Trade accepted successfully'
      });
    } catch (error) {
      console.error('Error accepting trade request:', error);
      res.status(500).json({
        success: false,
        message: error.message || 'Failed to accept trade request'
      });
    }
  }

  /**
   * Get marketplace statistics
   */
  async getMarketplaceStats(req, res) {
    try {
      const { regionId = 'global', timeRange = 7 } = req.query;
      const stats = await this.marketplace.getMarketplaceStats(regionId, parseInt(timeRange));

      res.json({
        success: true,
        data: stats
      });
    } catch (error) {
      console.error('Error getting marketplace stats:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get marketplace statistics'
      });
    }
  }

  /**
   * Get player's marketplace activity
   */
  async getPlayerMarketplaceActivity(req, res) {
    try {
      const { timeRange = 30 } = req.query;
      const activity = await this.marketplace.getPlayerMarketplaceActivity(
        req.user.id,
        parseInt(timeRange)
      );

      res.json({
        success: true,
        data: activity
      });
    } catch (error) {
      console.error('Error getting player marketplace activity:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get marketplace activity'
      });
    }
  }

  /**
   * Get marketplace categories
   */
  async getMarketplaceCategories(req, res) {
    try {
      const categories = await req.db('item_categories')
        .where('active', true)
        .orderBy('sort_order', 'asc')
        .select('*');

      // Add item counts for each category
      const categoriesWithCounts = await Promise.all(
        categories.map(async (category) => {
          const itemCount = await req.db('items')
            .where('category_id', category.id)
            .count('* as count')
            .first();

          return {
            ...category,
            itemCount: parseInt(itemCount.count)
          };
        })
      );

      res.json({
        success: true,
        data: categoriesWithCounts
      });
    } catch (error) {
      console.error('Error getting marketplace categories:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get marketplace categories'
      });
    }
  }

  /**
   * Get featured listings
   */
  async getFeaturedListings(req, res) {
    try {
      const { regionId = 'global', limit = 10 } = req.query;

      const featuredListings = await this.marketplace.searchListings({
        regionId,
        sortBy: 'views',
        sortOrder: 'desc',
        limit: parseInt(limit)
      });

      res.json({
        success: true,
        data: featuredListings
      });
    } catch (error) {
      console.error('Error getting featured listings:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get featured listings'
      });
    }
  }

  /**
   * Get market trends
   */
  async getMarketTrends(req, res) {
    try {
      const { regionId = 'global', timeRange = 7, categoryId } = req.query;

      let trends;

      if (categoryId) {
        trends = await this.marketAnalyzer.analyzeCategoryTrends(
          categoryId,
          regionId,
          parseInt(timeRange)
        );
      } else {
        trends = await this.getOverallMarketTrends(regionId, parseInt(timeRange));
      }

      res.json({
        success: true,
        data: trends
      });
    } catch (error) {
      console.error('Error getting market trends:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get market trends'
      });
    }
  }

  /**
   * Get price history for an item
   */
  async getPriceHistory(req, res) {
    try {
      const { itemId } = req.params;
      const { regionId = 'global', timeRange = 30 } = req.query;

      const priceHistory = await req.db('market_prices')
        .where('item_id', itemId)
        .where('region_id', regionId)
        .where('created_at', '>=', new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000))
        .orderBy('created_at', 'asc')
        .select('*');

      res.json({
        success: true,
        data: priceHistory
      });
    } catch (error) {
      console.error('Error getting price history:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get price history'
      });
    }
  }

  /**
   * Get similar listings
   */
  async getSimilarListings(req, res) {
    try {
      const { listingId } = req.params;
      const { limit = 5 } = req.query;

      const listing = await this.marketplace.getListing(listingId);
      if (!listing) {
        return res.status(404).json({
          success: false,
          message: 'Listing not found'
        });
      }

      const similarListings = await this.marketplace.searchListings({
        itemId: listing.item_id,
        regionId: listing.region_id,
        limit: parseInt(limit) + 1, // +1 to exclude the original
        sortBy: 'price',
        sortOrder: 'asc'
      });

      // Exclude the original listing
      const filteredListings = similarListings.filter(l => l.id !== listingId);

      res.json({
        success: true,
        data: filteredListings.slice(0, parseInt(limit))
      });
    } catch (error) {
      console.error('Error getting similar listings:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get similar listings'
      });
    }
  }

  /**
   * Helper methods
   */
  async getOverallMarketTrends(regionId, timeRange) {
    const trends = await req.db('market_prices')
      .join('items', 'market_prices.item_id', 'items.id')
      .join('item_categories', 'items.category_id', 'item_categories.id')
      .where('market_prices.region_id', regionId)
      .where('market_prices.created_at', '>=', new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000))
      .groupBy('item_categories.id', 'item_categories.name')
      .select(
        'item_categories.id',
        'item_categories.name',
        req.db.raw('AVG(market_prices.price) as avg_price'),
        req.db.raw('MIN(market_prices.price) as min_price'),
        req.db.raw('MAX(market_prices.price) as max_price'),
        req.db.raw('COUNT(*) as data_points')
      )
      .orderBy('avg_price', 'desc');

    return {
      summary: {
        totalCategories: trends.length,
        avgPrice: trends.reduce((sum, t) => sum + parseFloat(t.avg_price), 0) / trends.length || 0,
        priceRange: {
          min: Math.min(...trends.map(t => parseFloat(t.min_price))),
          max: Math.max(...trends.map(t => parseFloat(t.max_price)))
        }
      },
      categoryTrends: trends
    };
  }
}

module.exports = MarketplaceController;