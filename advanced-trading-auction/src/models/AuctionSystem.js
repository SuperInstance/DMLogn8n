const Decimal = require('decimal.js');
const EventEmitter = require('events');
const { v4: uuidv4 } = require('uuid');

class AuctionSystem extends EventEmitter {
  constructor(knex, redis, economicEngine) {
    super();
    this.db = knex;
    this.redis = redis;
    this.economicEngine = economicEngine;
    this.activeAuctions = new Map();
    this.auctionTimers = new Map();
    this.bidHistory = new Map();

    // Auction configuration
    this.auctionExtensionTime = 300000; // 5 minutes
    this.minBidIncrement = 0.05; // 5% minimum increment
    this.maxBidIncrement = 0.50; // 50% maximum increment
    this.reservePriceVisibility = false; // Hide reserve price
    this.anonymousBidding = true;
    this.antiSnipingEnabled = true;
  }

  /**
   * Create a new auction
   */
  async createAuction(auctionData) {
    const {
      sellerId,
      itemId,
      quantity,
      startingPrice,
      reservePrice = null,
      buyoutPrice = null,
      duration = 24 * 60 * 60 * 1000, // 24 hours default
      regionId = 'global',
      anonymous = false,
      autoRelist = false,
      minBidIncrement = this.minBidIncrement
    } = auctionData;

    // Validate auction data
    await this.validateAuctionData(auctionData);

    const auctionId = uuidv4();
    const now = new Date();
    const endTime = new Date(now.getTime() + duration);

    const auction = {
      id: auctionId,
      seller_id: sellerId,
      item_id: itemId,
      quantity,
      starting_price: new Decimal(startingPrice),
      current_bid: new Decimal(startingPrice),
      reserve_price: reservePrice ? new Decimal(reservePrice) : null,
      buyout_price: buyoutPrice ? new Decimal(buyoutPrice) : null,
      start_time: now,
      end_time: endTime,
      status: 'active',
      region_id: regionId,
      anonymous,
      auto_relist: auto_relist,
      min_bid_increment: minBidIncrement,
      bid_count: 0,
      bidder_id: null,
      created_at: now,
      updated_at: now
    };

    // Insert auction into database
    await this.db('auctions').insert({
      id: auction.id,
      seller_id: auction.seller_id,
      item_id: auction.item_id,
      quantity: auction.quantity,
      starting_price: auction.starting_price.toString(),
      current_bid: auction.current_bid.toString(),
      reserve_price: auction.reserve_price?.toString() || null,
      buyout_price: auction.buyout_price?.toString() || null,
      start_time: auction.start_time,
      end_time: auction.end_time,
      status: auction.status,
      region_id: auction.region_id,
      anonymous: auction.anonymous,
      auto_relist: auction.auto_relist,
      min_bid_increment: auction.min_bid_increment,
      bid_count: auction.bid_count,
      bidder_id: auction.bidder_id,
      created_at: auction.created_at,
      updated_at: auction.updated_at
    });

    // Store in memory for quick access
    this.activeAuctions.set(auctionId, auction);

    // Set up auction end timer
    this.setAuctionTimer(auctionId, endTime);

    // Update supply/demand
    await this.economicEngine.updateSupplyDemand(itemId, regionId, quantity, 0);

    // Emit event
    this.emit('auctionCreated', { auction });

    return auction;
  }

  /**
   * Place a bid on an auction
   */
  async placeBid(auctionId, bidderId, bidAmount, anonymous = false) {
    const auction = await this.getAuction(auctionId);

    if (!auction) {
      throw new Error('Auction not found');
    }

    if (auction.status !== 'active') {
      throw new Error('Auction is not active');
    }

    if (auction.seller_id === bidderId) {
      throw new Error('Cannot bid on your own auction');
    }

    const bid = new Decimal(bidAmount);

    // Validate bid amount
    if (bid.lessThan(auction.current_bid)) {
      throw new Error('Bid must be higher than current bid');
    }

    // Calculate minimum bid
    const minBid = auction.current_bid.mul(
      Decimal(1).add(auction.min_bid_increment)
    );

    if (bid.lessThan(minBid)) {
      throw new Error(`Bid must be at least ${minBid.toString()}`);
    }

    // Check if buyout price is met
    if (auction.buyout_price && bid.greaterThanOrEqualTo(auction.buyout_price)) {
      return await this.processBuyout(auction, bidderId, bid);
    }

    // Check for anti-sniping
    const timeRemaining = auction.end_time.getTime() - Date.now();
    if (this.antiSnipingEnabled && timeRemaining < this.auctionExtensionTime) {
      // Extend auction
      const newEndTime = new Date(Date.now() + this.auctionExtensionTime);
      await this.extendAuction(auctionId, newEndTime);
    }

    // Record the bid
    const bidRecord = {
      id: uuidv4(),
      auction_id: auctionId,
      bidder_id: bidderId,
      amount: bid.toString(),
      timestamp: new Date(),
      anonymous
    };

    await this.db('auction_bids').insert(bidRecord);

    // Update auction
    auction.current_bid = bid;
    auction.bidder_id = bidderId;
    auction.bid_count += 1;
    auction.updated_at = new Date();

    await this.db('auctions')
      .where('id', auctionId)
      .update({
        current_bid: auction.current_bid.toString(),
        bidder_id: auction.bidder_id,
        bid_count: auction.bid_count,
        updated_at: auction.updated_at
      });

    // Store bid history
    if (!this.bidHistory.has(auctionId)) {
      this.bidHistory.set(auctionId, []);
    }
    this.bidHistory.get(auctionId).push(bidRecord);

    // Update in memory
    this.activeAuctions.set(auctionId, auction);

    // Emit events
    this.emit('bidPlaced', {
      auctionId,
      bidderId,
      amount: bid.toString(),
      timestamp: bidRecord.timestamp
    });

    // Notify previous bidder if outbid
    if (auction.bid_count > 1) {
      const previousBids = await this.getBidHistory(auctionId);
      const previousBid = previousBids[previousBids.length - 2];
      if (previousBid && previousBid.bidder_id !== bidderId) {
        this.emit('outbid', {
          auctionId,
          previousBidderId: previousBid.bidder_id,
          newBid: bid.toString()
        });
      }
    }

    return {
      success: true,
      auction,
      bid: bidRecord,
      outbid: auction.bid_count > 1
    };
  }

  /**
   * Process buyout
   */
  async processBuyout(auction, buyerId, bidAmount) {
    const buyoutPrice = auction.buyout_price;

    // End auction immediately
    auction.status = 'sold';
    auction.end_time = new Date();
    auction.current_bid = buyoutPrice;
    auction.bidder_id = buyerId;
    auction.bid_count += 1;
    auction.updated_at = new Date();

    await this.db('auctions')
      .where('id', auction.id)
      .update({
        status: 'sold',
        end_time: auction.end_time,
        current_bid: auction.current_bid.toString(),
        bidder_id: auction.bidder_id,
        bid_count: auction.bid_count,
        updated_at: auction.updated_at
      });

    // Record final bid
    const bidRecord = {
      id: uuidv4(),
      auction_id: auction.id,
      bidder_id: buyerId,
      amount: buyoutPrice.toString(),
      timestamp: new Date(),
      anonymous: auction.anonymous
    };

    await this.db('auction_bids').insert(bidRecord);

    // Clear timer
    if (this.auctionTimers.has(auction.id)) {
      clearTimeout(this.auctionTimers.get(auction.id));
      this.auctionTimers.delete(auction.id);
    }

    // Update supply/demand
    await this.economicEngine.updateSupplyDemand(
      auction.item_id,
      auction.region_id,
      -auction.quantity,
      auction.quantity
    );

    // Record transaction
    await this.economicEngine.recordTransaction(
      auction.item_id,
      auction.region_id,
      auction.quantity,
      buyoutPrice,
      'auction_sale'
    );

    // Process payment and transfer
    await this.processAuctionCompletion(auction, buyerId);

    // Remove from active auctions
    this.activeAuctions.delete(auction.id);

    // Emit events
    this.emit('auctionSold', {
      auctionId: auction.id,
      sellerId: auction.seller_id,
      buyerId,
      price: buyoutPrice.toString(),
      quantity: auction.quantity,
      buyout: true
    });

    return {
      success: true,
      auction,
      bid: bidRecord,
      buyout: true
    };
  }

  /**
   * End an auction
   */
  async endAuction(auctionId) {
    const auction = this.activeAuctions.get(auctionId);

    if (!auction || auction.status !== 'active') {
      return;
    }

    auction.status = auction.bidder_id ? 'sold' : 'expired';
    auction.end_time = new Date();
    auction.updated_at = new Date();

    await this.db('auctions')
      .where('id', auctionId)
      .update({
        status: auction.status,
        end_time: auction.end_time,
        updated_at: auction.updated_at
      });

    // Clear timer
    this.auctionTimers.delete(auctionId);

    if (auction.status === 'sold') {
      // Process successful auction
      await this.processAuctionCompletion(auction, auction.bidder_id);

      // Update supply/demand
      await this.economicEngine.updateSupplyDemand(
        auction.item_id,
        auction.region_id,
        -auction.quantity,
        auction.quantity
      );

      // Record transaction
      await this.economicEngine.recordTransaction(
        auction.item_id,
        auction.region_id,
        auction.quantity,
        auction.current_bid,
        'auction_sale'
      );

      this.emit('auctionSold', {
        auctionId,
        sellerId: auction.seller_id,
        buyerId: auction.bidder_id,
        price: auction.current_bid.toString(),
        quantity: auction.quantity,
        buyout: false
      });
    } else {
      // Handle expired auction
      await this.handleExpiredAuction(auction);

      this.emit('auctionExpired', {
        auctionId,
        sellerId: auction.seller_id
      });
    }

    // Remove from active auctions
    this.activeAuctions.delete(auctionId);
  }

  /**
   * Process auction completion (payment and item transfer)
   */
  async processAuctionCompletion(auction, winnerId) {
    // Calculate fees
    const auctionFee = auction.current_bid.mul(0.02); // 2% auction fee
    const sellerProceeds = auction.current_bid.sub(auctionFee);

    // Create transaction record
    await this.db('transactions').insert({
      id: uuidv4(),
      type: 'auction_purchase',
      from_player_id: winnerId,
      to_player_id: auction.seller_id,
      amount: auction.current_bid.toString(),
      fee: auctionFee.toString(),
      description: `Auction purchase: ${auction.item_id} x${auction.quantity}`,
      status: 'completed',
      created_at: new Date()
    });

    // Transfer items (this would integrate with inventory system)
    await this.transferItems(
      auction.seller_id,
      winnerId,
      auction.item_id,
      auction.quantity,
      'auction'
    );

    // Handle auto-relist if configured
    if (auction.auto_relist && auction.status === 'expired') {
      await this.autoRelistAuction(auction);
    }
  }

  /**
   * Handle expired auction
   */
  async handleExpiredAuction(auction) {
    // Return items to seller if no bids
    if (!auction.bidder_id) {
      // Items remain with seller (no action needed if items weren't removed)
      this.emit('itemsReturned', {
        auctionId: auction.id,
        sellerId: auction.seller_id,
        itemId: auction.item_id,
        quantity: auction.quantity
      });
    }

    // Handle auto-relist if configured
    if (auction.auto_relist) {
      await this.autoRelistAuction(auction);
    }
  }

  /**
   * Auto-relist auction
   */
  async autoRelistAuction(originalAuction) {
    const relistData = {
      sellerId: originalAuction.seller_id,
      itemId: originalAuction.item_id,
      quantity: originalAuction.quantity,
      startingPrice: originalAuction.starting_price.mul(0.9), // 10% lower starting price
      reservePrice: originalAuction.reserve_price?.mul(0.9),
      buyoutPrice: originalAuction.buyout_price?.mul(0.9),
      duration: 24 * 60 * 60 * 1000,
      regionId: originalAuction.region_id,
      anonymous: originalAuction.anonymous,
      autoRelist: originalAuction.auto_relist,
      minBidIncrement: originalAuction.min_bid_increment
    };

    const newAuction = await this.createAuction(relistData);

    this.emit('auctionRelisted', {
      originalAuctionId: originalAuction.id,
      newAuctionId: newAuction.id,
      sellerId: originalAuction.seller_id
    });

    return newAuction;
  }

  /**
   * Extend auction time (for anti-sniping)
   */
  async extendAuction(auctionId, newEndTime) {
    const auction = this.activeAuctions.get(auctionId);

    if (!auction) return;

    // Clear existing timer
    if (this.auctionTimers.has(auctionId)) {
      clearTimeout(this.auctionTimers.get(auctionId));
    }

    // Update auction
    auction.end_time = newEndTime;
    auction.updated_at = new Date();

    await this.db('auctions')
      .where('id', auctionId)
      .update({
        end_time: newEndTime,
        updated_at: auction.updated_at
      });

    // Set new timer
    this.setAuctionTimer(auctionId, newEndTime);

    // Update in memory
    this.activeAuctions.set(auctionId, auction);

    // Emit extension event
    this.emit('auctionExtended', {
      auctionId,
      newEndTime,
      extensionReason: 'anti_sniping'
    });
  }

  /**
   * Cancel an auction
   */
  async cancelAuction(auctionId, cancelerId, reason = 'seller_cancel') {
    const auction = this.activeAuctions.get(auctionId);

    if (!auction) {
      throw new Error('Auction not found');
    }

    if (auction.seller_id !== cancelerId) {
      throw new Error('Only the seller can cancel the auction');
    }

    if (auction.bidder_id) {
      throw new Error('Cannot cancel auction with active bids');
    }

    auction.status = 'cancelled';
    auction.end_time = new Date();
    auction.updated_at = new Date();

    await this.db('auctions')
      .where('id', auctionId)
      .update({
        status: 'cancelled',
        end_time: auction.end_time,
        updated_at: auction.updated_at
      });

    // Clear timer
    if (this.auctionTimers.has(auctionId)) {
      clearTimeout(this.auctionTimers.get(auctionId));
      this.auctionTimers.delete(auctionId);
    }

    // Return items to seller
    this.emit('auctionCancelled', {
      auctionId,
      sellerId: auction.seller_id,
      reason
    });

    // Remove from active auctions
    this.activeAuctions.delete(auctionId);

    return auction;
  }

  /**
   * Get auction details
   */
  async getAuction(auctionId) {
    // Check memory first
    if (this.activeAuctions.has(auctionId)) {
      return this.activeAuctions.get(auctionId);
    }

    // Check database
    const auction = await this.db('auctions')
      .where('id', auctionId)
      .first();

    if (!auction) {
      return null;
    }

    // Convert Decimal fields
    auction.starting_price = new Decimal(auction.starting_price);
    auction.current_bid = new Decimal(auction.current_bid);
    if (auction.reserve_price) {
      auction.reserve_price = new Decimal(auction.reserve_price);
    }
    if (auction.buyout_price) {
      auction.buyout_price = new Decimal(auction.buyout_price);
    }

    return auction;
  }

  /**
   * Get bid history for an auction
   */
  async getBidHistory(auctionId, limit = 50) {
    const bids = await this.db('auction_bids')
      .where('auction_id', auctionId)
      .orderBy('timestamp', 'desc')
      .limit(limit)
      .select('*');

    return bids.map(bid => ({
      ...bid,
      amount: new Decimal(bid.amount)
    }));
  }

  /**
   * Search auctions
   */
  async searchAuctions(filters = {}) {
    const {
      itemId,
      sellerId,
      regionId,
      status = 'active',
      minPrice,
      maxPrice,
      sortBy = 'end_time',
      sortOrder = 'asc',
      limit = 50,
      offset = 0
    } = filters;

    let query = this.db('auctions')
      .join('items', 'auctions.item_id', 'items.id')
      .where('auctions.status', status);

    if (itemId) {
      query = query.where('auctions.item_id', itemId);
    }

    if (sellerId) {
      query = query.where('auctions.seller_id', sellerId);
    }

    if (regionId) {
      query = query.where('auctions.region_id', regionId);
    }

    if (minPrice) {
      query = query.where('auctions.current_bid', '>=', minPrice);
    }

    if (maxPrice) {
      query = query.where('auctions.current_bid', '<=', maxPrice);
    }

    const auctions = await query
      .orderBy(`auctions.${sortBy}`, sortOrder)
      .limit(limit)
      .offset(offset)
      .select(
        'auctions.*',
        'items.name as item_name',
        'items.rarity as item_rarity',
        'items.icon as item_icon'
      );

    return auctions.map(auction => ({
      ...auction,
      starting_price: new Decimal(auction.starting_price),
      current_bid: new Decimal(auction.current_bid),
      reserve_price: auction.reserve_price ? new Decimal(auction.reserve_price) : null,
      buyout_price: auction.buyout_price ? new Decimal(auction.buyout_price) : null
    }));
  }

  /**
   * Get active auctions for a player
   */
  async getPlayerAuctions(playerId, type = 'selling') {
    let query = this.db('auctions')
      .join('items', 'auctions.item_id', 'items.id');

    if (type === 'selling') {
      query = query.where('auctions.seller_id', playerId);
    } else if (type === 'bidding') {
      query = query.where('auctions.bidder_id', playerId);
    }

    const auctions = await query
      .where('auctions.status', 'active')
      .orderBy('auctions.end_time', 'asc')
      .select(
        'auctions.*',
        'items.name as item_name',
        'items.rarity as item_rarity',
        'items.icon as item_icon'
      );

    return auctions.map(auction => ({
      ...auction,
      starting_price: new Decimal(auction.starting_price),
      current_bid: new Decimal(auction.current_bid),
      reserve_price: auction.reserve_price ? new Decimal(auction.reserve_price) : null,
      buyout_price: auction.buyout_price ? new Decimal(auction.buyout_price) : null
    }));
  }

  /**
   * Set auction timer
   */
  setAuctionTimer(auctionId, endTime) {
    const timeUntilEnd = endTime.getTime() - Date.now();

    if (timeUntilEnd <= 0) {
      // End auction immediately
      setImmediate(() => this.endAuction(auctionId));
      return;
    }

    const timer = setTimeout(() => {
      this.endAuction(auctionId);
    }, timeUntilEnd);

    this.auctionTimers.set(auctionId, timer);
  }

  /**
   * Validate auction data
   */
  async validateAuctionData(auctionData) {
    const {
      sellerId,
      itemId,
      quantity,
      startingPrice,
      reservePrice,
      buyoutPrice
    } = auctionData;

    // Validate player exists and has items
    const player = await this.db('players').where('id', sellerId).first();
    if (!player) {
      throw new Error('Player not found');
    }

    // Validate item exists
    const item = await this.db('items').where('id', itemId).first();
    if (!item) {
      throw new Error('Item not found');
    }

    // Validate quantity
    if (quantity <= 0) {
      throw new Error('Quantity must be positive');
    }

    // Validate prices
    if (new Decimal(startingPrice).lessThanOrEqualTo(0)) {
      throw new Error('Starting price must be positive');
    }

    if (reservePrice && new Decimal(reservePrice).lessThan(startingPrice)) {
      throw new Error('Reserve price cannot be lower than starting price');
    }

    if (buyoutPrice && new Decimal(buyoutPrice).lessThan(startingPrice)) {
      throw new Error('Buyout price cannot be lower than starting price');
    }

    // Check if player has sufficient items in inventory
    const inventory = await this.checkPlayerInventory(sellerId, itemId, quantity);
    if (!inventory) {
      throw new Error('Insufficient items in inventory');
    }
  }

  /**
   * Check player inventory
   */
  async checkPlayerInventory(playerId, itemId, quantity) {
    // This would integrate with the actual inventory system
    // For now, we'll assume it exists
    return true;
  }

  /**
   * Transfer items between players
   */
  async transferItems(fromPlayerId, toPlayerId, itemId, quantity, reason) {
    // This would integrate with the actual inventory system
    // For now, we'll just log the transfer
    console.log(`Transferring ${quantity}x ${itemId} from ${fromPlayerId} to ${toPlayerId} (${reason})`);
  }

  /**
   * Get auction statistics
   */
  async getAuctionStats(regionId = 'global', timeRange = 7) {
    const startDate = new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000);

    const stats = await this.db('auctions')
      .where('region_id', regionId)
      .where('created_at', '>=', startDate)
      .select(
        this.db.raw('COUNT(*) as total_auctions'),
        this.db.raw('SUM(CASE WHEN status = \'sold\' THEN 1 ELSE 0 END) as sold_auctions'),
        this.db.raw('SUM(CASE WHEN status = \'expired\' THEN 1 ELSE 0 END) as expired_auctions'),
        this.db.raw('SUM(CASE WHEN status = \'cancelled\' THEN 1 ELSE 0 END) as cancelled_auctions'),
        this.db.raw('SUM(current_bid) as total_volume'),
        this.db.raw('AVG(current_bid) as avg_final_price'),
        this.db.raw('AVG(bid_count) as avg_bids_per_auction')
      )
      .first();

    const successRate = stats.total_auctions > 0
      ? (stats.sold_auctions / stats.total_auctions) * 100
      : 0;

    return {
      totalAuctions: parseInt(stats.total_auctions) || 0,
      soldAuctions: parseInt(stats.sold_auctions) || 0,
      expiredAuctions: parseInt(stats.expired_auctions) || 0,
      cancelledAuctions: parseInt(stats.cancelled_auctions) || 0,
      successRate,
      totalVolume: stats.total_volume || new Decimal(0),
      avgFinalPrice: stats.avg_final_price || new Decimal(0),
      avgBidsPerAuction: parseFloat(stats.avg_bids_per_auction) || 0
    };
  }

  /**
   * Cleanup expired auctions (run periodically)
   */
  async cleanupExpiredAuctions() {
    const now = new Date();

    const expiredAuctions = await this.db('auctions')
      .where('status', 'active')
      .where('end_time', '<=', now)
      .select('id');

    for (const auction of expiredAuctions) {
      await this.endAuction(auction.id);
    }
  }

  /**
   * Initialize active auctions from database
   */
  async initializeActiveAuctions() {
    const activeAuctions = await this.db('auctions')
      .where('status', 'active')
      .where('end_time', '>', new Date())
      .select('*');

    for (const auctionData of activeAuctions) {
      const auction = {
        ...auctionData,
        starting_price: new Decimal(auctionData.starting_price),
        current_bid: new Decimal(auctionData.current_bid),
        reserve_price: auctionData.reserve_price ? new Decimal(auctionData.reserve_price) : null,
        buyout_price: auctionData.buyout_price ? new Decimal(auctionData.buyout_price) : null
      };

      this.activeAuctions.set(auction.id, auction);
      this.setAuctionTimer(auction.id, auction.end_time);
    }
  }
}

module.exports = AuctionSystem;