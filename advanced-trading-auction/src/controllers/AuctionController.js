const AuctionSystem = require('../models/AuctionSystem');
const EconomicEngine = require('../models/EconomicEngine');
const { validationResult } = require('express-validator');

class AuctionController {
  constructor(knex, redis) {
    this.economicEngine = new EconomicEngine(redis, knex);
    this.auctionSystem = new AuctionSystem(knex, redis, this.economicEngine);
  }

  /**
   * Create a new auction
   */
  async createAuction(req, res) {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({
          success: false,
          errors: errors.array()
        });
      }

      const auctionData = {
        ...req.body,
        sellerId: req.user.id
      };

      const auction = await this.auctionSystem.createAuction(auctionData);

      res.status(201).json({
        success: true,
        data: auction,
        message: 'Auction created successfully'
      });
    } catch (error) {
      console.error('Error creating auction:', error);
      res.status(500).json({
        success: false,
        message: error.message || 'Failed to create auction'
      });
    }
  }

  /**
   * Place a bid on an auction
   */
  async placeBid(req, res) {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({
          success: false,
          errors: errors.array()
        });
      }

      const { auctionId } = req.params;
      const { amount, anonymous = false } = req.body;

      const result = await this.auctionSystem.placeBid(
        auctionId,
        req.user.id,
        amount,
        anonymous
      );

      res.json({
        success: true,
        data: result,
        message: result.buyout ? 'Auction purchased with buyout!' : 'Bid placed successfully'
      });
    } catch (error) {
      console.error('Error placing bid:', error);
      res.status(500).json({
        success: false,
        message: error.message || 'Failed to place bid'
      });
    }
  }

  /**
   * Get auction details
   */
  async getAuction(req, res) {
    try {
      const { auctionId } = req.params;
      const auction = await this.auctionSystem.getAuction(auctionId);

      if (!auction) {
        return res.status(404).json({
          success: false,
          message: 'Auction not found'
        });
      }

      // Get bid history if requested
      let bidHistory = [];
      if (req.query.includeBids === 'true') {
        bidHistory = await this.auctionSystem.getBidHistory(auctionId, 20);
      }

      res.json({
        success: true,
        data: {
          auction,
          bidHistory
        }
      });
    } catch (error) {
      console.error('Error getting auction:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get auction details'
      });
    }
  }

  /**
   * Search auctions
   */
  async searchAuctions(req, res) {
    try {
      const filters = {
        itemId: req.query.itemId,
        sellerId: req.query.sellerId,
        regionId: req.query.regionId,
        minPrice: req.query.minPrice ? parseFloat(req.query.minPrice) : undefined,
        maxPrice: req.query.maxPrice ? parseFloat(req.query.maxPrice) : undefined,
        sortBy: req.query.sortBy || 'end_time',
        sortOrder: req.query.sortOrder || 'asc',
        limit: parseInt(req.query.limit) || 50,
        offset: parseInt(req.query.offset) || 0
      };

      const auctions = await this.auctionSystem.searchAuctions(filters);

      res.json({
        success: true,
        data: auctions,
        pagination: {
          limit: filters.limit,
          offset: filters.offset,
          total: auctions.length
        }
      });
    } catch (error) {
      console.error('Error searching auctions:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to search auctions'
      });
    }
  }

  /**
   * Get player's auctions
   */
  async getPlayerAuctions(req, res) {
    try {
      const { type = 'selling' } = req.query;
      const auctions = await this.auctionSystem.getPlayerAuctions(req.user.id, type);

      res.json({
        success: true,
        data: auctions
      });
    } catch (error) {
      console.error('Error getting player auctions:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get player auctions'
      });
    }
  }

  /**
   * Cancel an auction
   */
  async cancelAuction(req, res) {
    try {
      const { auctionId } = req.params;
      const { reason = 'seller_cancel' } = req.body;

      const auction = await this.auctionSystem.cancelAuction(
        auctionId,
        req.user.id,
        reason
      );

      res.json({
        success: true,
        data: auction,
        message: 'Auction cancelled successfully'
      });
    } catch (error) {
      console.error('Error cancelling auction:', error);
      res.status(500).json({
        success: false,
        message: error.message || 'Failed to cancel auction'
      });
    }
  }

  /**
   * Get auction statistics
   */
  async getAuctionStats(req, res) {
    try {
      const { regionId = 'global', timeRange = 7 } = req.query;
      const stats = await this.auctionSystem.getAuctionStats(regionId, parseInt(timeRange));

      res.json({
        success: true,
        data: stats
      });
    } catch (error) {
      console.error('Error getting auction stats:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get auction statistics'
      });
    }
  }

  /**
   * Get bid history for an auction
   */
  async getBidHistory(req, res) {
    try {
      const { auctionId } = req.params;
      const { limit = 50 } = req.query;

      const bidHistory = await this.auctionSystem.getBidHistory(auctionId, parseInt(limit));

      res.json({
        success: true,
        data: bidHistory
      });
    } catch (error) {
      console.error('Error getting bid history:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get bid history'
      });
    }
  }

  /**
   * Get auction categories (from items)
   */
  async getAuctionCategories(req, res) {
    try {
      const categories = await req.db('item_categories')
        .where('active', true)
        .orderBy('sort_order', 'asc')
        .select('*');

      res.json({
        success: true,
        data: categories
      });
    } catch (error) {
      console.error('Error getting auction categories:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get auction categories'
      });
    }
  }

  /**
   * Get featured auctions
   */
  async getFeaturedAuctions(req, res) {
    try {
      const { regionId = 'global', limit = 10 } = req.query;

      const featuredAuctions = await this.auctionSystem.searchAuctions({
        regionId,
        sortBy: 'current_bid',
        sortOrder: 'desc',
        limit: parseInt(limit)
      });

      res.json({
        success: true,
        data: featuredAuctions
      });
    } catch (error) {
      console.error('Error getting featured auctions:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get featured auctions'
      });
    }
  }

  /**
   * Get auction analytics data
   */
  async getAuctionAnalytics(req, res) {
    try {
      const { regionId = 'global', timeRange = 7, itemId } = req.query;

      let analytics = {};

      if (itemId) {
        // Item-specific analytics
        analytics = await this.getItemAuctionAnalytics(itemId, regionId, parseInt(timeRange));
      } else {
        // General auction analytics
        analytics = await this.getGeneralAuctionAnalytics(regionId, parseInt(timeRange));
      }

      res.json({
        success: true,
        data: analytics
      });
    } catch (error) {
      console.error('Error getting auction analytics:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to get auction analytics'
      });
    }
  }

  /**
   * Get item-specific auction analytics
   */
  async getItemAuctionAnalytics(itemId, regionId, timeRange) {
    const startDate = new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000);

    // Get auction data for this item
    const auctionData = await req.db('auctions')
      .where('item_id', itemId)
      .where('region_id', regionId)
      .where('created_at', '>=', startDate)
      .select('*');

    // Get bid data
    const bidData = await req.db('auction_bids')
      .join('auctions', 'auction_bids.auction_id', 'auctions.id')
      .where('auctions.item_id', itemId)
      .where('auctions.region_id', regionId)
      .where('auction_bids.timestamp', '>=', startDate)
      .select('auction_bids.*');

    // Calculate analytics
    const totalAuctions = auctionData.length;
    const soldAuctions = auctionData.filter(a => a.status === 'sold').length;
    const totalBids = bidData.length;
    const avgFinalPrice = auctionData
      .filter(a => a.status === 'sold')
      .reduce((sum, a) => sum + parseFloat(a.current_bid), 0) / soldAuctions || 0;

    return {
      totalAuctions,
      soldAuctions,
      successRate: totalAuctions > 0 ? (soldAuctions / totalAuctions) * 100 : 0,
      totalBids,
      avgBidsPerAuction: totalAuctions > 0 ? totalBids / totalAuctions : 0,
      avgFinalPrice,
      priceDistribution: this.calculatePriceDistribution(auctionData),
      bidDistribution: this.calculateBidDistribution(bidData)
    };
  }

  /**
   * Get general auction analytics
   */
  async getGeneralAuctionAnalytics(regionId, timeRange) {
    const stats = await this.auctionSystem.getAuctionStats(regionId, timeRange);

    // Get additional analytics
    const hotCategories = await this.getHotCategories(regionId, timeRange);
    const topBidders = await this.getTopBidders(regionId, timeRange);

    return {
      ...stats,
      hotCategories,
      topBidders,
      hourlyActivity: await this.getHourlyAuctionActivity(regionId, timeRange)
    };
  }

  /**
   * Helper methods for analytics
   */
  calculatePriceDistribution(auctions) {
    const prices = auctions
      .filter(a => a.status === 'sold')
      .map(a => parseFloat(a.current_bid))
      .sort((a, b) => a - b);

    if (prices.length === 0) return {};

    const quartiles = {
      min: prices[0],
      q1: prices[Math.floor(prices.length * 0.25)],
      median: prices[Math.floor(prices.length * 0.5)],
      q3: prices[Math.floor(prices.length * 0.75)],
      max: prices[prices.length - 1]
    };

    return quartiles;
  }

  calculateBidDistribution(bids) {
    const bidCounts = {};
    bids.forEach(bid => {
      const auctionId = bid.auction_id;
      bidCounts[auctionId] = (bidCounts[auctionId] || 0) + 1;
    });

    const distribution = Object.values(bidCounts);
    return {
      avg: distribution.reduce((sum, count) => sum + count, 0) / distribution.length,
      max: Math.max(...distribution),
      min: Math.min(...distribution)
    };
  }

  async getHotCategories(regionId, timeRange) {
    const startDate = new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000);

    return await req.db('auctions')
      .join('items', 'auctions.item_id', 'items.id')
      .join('item_categories', 'items.category_id', 'item_categories.id')
      .where('auctions.region_id', regionId)
      .where('auctions.created_at', '>=', startDate)
      .groupBy('item_categories.id', 'item_categories.name')
      .select(
        'item_categories.id',
        'item_categories.name',
        req.db.raw('COUNT(*) as auction_count'),
        req.db.raw('SUM(auctions.current_bid) as total_volume')
      )
      .orderBy('total_volume', 'desc')
      .limit(5);
  }

  async getTopBidders(regionId, timeRange) {
    const startDate = new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000);

    return await req.db('auction_bids')
      .join('auctions', 'auction_bids.auction_id', 'auctions.id')
      .join('players', 'auction_bids.bidder_id', 'players.id')
      .where('auctions.region_id', regionId)
      .where('auction_bids.timestamp', '>=', startDate)
      .groupBy('players.id', 'players.username')
      .select(
        'players.id',
        'players.username',
        req.db.raw('COUNT(*) as bid_count'),
        req.db.raw('SUM(auction_bids.amount) as total_bid_amount')
      )
      .orderBy('total_bid_amount', 'desc')
      .limit(10);
  }

  async getHourlyAuctionActivity(regionId, timeRange) {
    const startDate = new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000);
    const hourlyData = {};

    for (let i = 0; i < 24; i++) {
      hourlyData[i] = {
        auctionsCreated: 0,
        bidsPlaced: 0,
        auctionsEnded: 0
      };
    }

    // Get hourly activity data
    const createdAuctions = await req.db('auctions')
      .where('region_id', regionId)
      .where('created_at', '>=', startDate)
      .select(req.db.raw('EXTRACT(HOUR FROM created_at) as hour, COUNT(*) as count'));

    const placedBids = await req.db('auction_bids')
      .join('auctions', 'auction_bids.auction_id', 'auctions.id')
      .where('auctions.region_id', regionId)
      .where('auction_bids.timestamp', '>=', startDate)
      .select(req.db.raw('EXTRACT(HOUR FROM auction_bids.timestamp) as hour, COUNT(*) as count'));

    const endedAuctions = await req.db('auctions')
      .where('region_id', regionId)
      .where('end_time', '>=', startDate)
      .where('end_time', '<=', new Date())
      .select(req.db.raw('EXTRACT(HOUR FROM end_time) as hour, COUNT(*) as count'));

    // Populate hourly data
    createdAuctions.forEach(row => {
      hourlyData[Math.floor(row.hour)].auctionsCreated = parseInt(row.count);
    });

    placedBids.forEach(row => {
      hourlyData[Math.floor(row.hour)].bidsPlaced = parseInt(row.count);
    });

    endedAuctions.forEach(row => {
      hourlyData[Math.floor(row.hour)].auctionsEnded = parseInt(row.count);
    });

    return hourlyData;
  }
}

module.exports = AuctionController;