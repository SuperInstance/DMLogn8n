const Decimal = require('decimal.js');
const EventEmitter = require('events');
const { v4: uuidv4 } = require('uuid');

class Marketplace extends EventEmitter {
  constructor(knex, redis, economicEngine) {
    super();
    this.db = knex;
    this.redis = redis;
    this.economicEngine = economicEngine;
    this.activeListings = new Map();
    this.tradeRequests = new Map();
    this.reputationSystem = new ReputationSystem(knex);

    // Marketplace configuration
    this.maxListingDuration = 30 * 24 * 60 * 60 * 1000; // 30 days
    this.defaultListingDuration = 7 * 24 * 60 * 60 * 1000; // 7 days
    this.maxListingsPerPlayer = 100;
    this.minListingPrice = 1;
    this.marketplaceFee = 0.03; // 3% marketplace fee
  }

  /**
   * Create a new market listing
   */
  async createListing(listingData) {
    const {
      sellerId,
      itemId,
      quantity,
      price,
      regionId = 'global',
      duration = this.defaultListingDuration,
      listingType = 'fixed', // 'fixed' or 'negotiable'
      minimumOffer = null,
      autoAcceptPrice = null,
      description = '',
      tags = []
    } = listingData;

    // Validate listing data
    await this.validateListingData(listingData);

    const listingId = uuidv4();
    const now = new Date();
    const endTime = new Date(now.getTime() + duration);

    const listing = {
      id: listingId,
      seller_id: sellerId,
      item_id: itemId,
      quantity,
      price: new Decimal(price),
      region_id: regionId,
      listing_type: listingType,
      minimum_offer: minimumOffer ? new Decimal(minimumOffer) : null,
      auto_accept_price: autoAcceptPrice ? new Decimal(autoAcceptPrice) : null,
      description,
      tags: JSON.stringify(tags),
      status: 'active',
      views: 0,
      created_at: now,
      updated_at: now,
      expires_at: endTime
    };

    // Insert into database
    await this.db('market_listings').insert({
      id: listing.id,
      seller_id: listing.seller_id,
      item_id: listing.item_id,
      quantity: listing.quantity,
      price: listing.price.toString(),
      region_id: listing.region_id,
      listing_type: listing.listing_type,
      minimum_offer: listing.minimum_offer?.toString() || null,
      auto_accept_price: listing.auto_accept_price?.toString() || null,
      description: listing.description,
      tags: listing.tags,
      status: listing.status,
      views: listing.views,
      created_at: listing.created_at,
      updated_at: listing.updated_at,
      expires_at: listing.expires_at
    });

    // Store in memory
    this.activeListings.set(listingId, listing);

    // Update supply/demand
    await this.economicEngine.updateSupplyDemand(itemId, regionId, quantity, 0);

    // Set expiration timer
    this.setListingTimer(listingId, endTime);

    // Emit event
    this.emit('listingCreated', { listing });

    return listing;
  }

  /**
   * Purchase an item from a listing
   */
  async purchaseListing(listingId, buyerId, quantity = null) {
    const listing = await this.getListing(listingId);

    if (!listing) {
      throw new Error('Listing not found');
    }

    if (listing.status !== 'active') {
      throw new Error('Listing is not active');
    }

    if (listing.seller_id === buyerId) {
      throw new Error('Cannot purchase your own listing');
    }

    const purchaseQuantity = quantity || listing.quantity;

    if (purchaseQuantity > listing.quantity) {
      throw new Error('Insufficient quantity available');
    }

    const totalPrice = listing.price.mul(purchaseQuantity);

    // Check buyer's funds
    const hasFunds = await this.checkPlayerFunds(buyerId, totalPrice);
    if (!hasFunds) {
      throw new Error('Insufficient funds');
    }

    // Process payment
    await this.processPayment(buyerId, listing.seller_id, totalPrice, this.marketplaceFee);

    // Transfer items
    await this.transferItems(listing.seller_id, buyerId, listing.item_id, purchaseQuantity, 'marketplace');

    // Update listing
    const remainingQuantity = listing.quantity - purchaseQuantity;
    if (remainingQuantity > 0) {
      listing.quantity = remainingQuantity;
      listing.updated_at = new Date();

      await this.db('market_listings')
        .where('id', listingId)
        .update({
          quantity: remainingQuantity,
          updated_at: listing.updated_at
        });

      // Update in memory
      this.activeListings.set(listingId, listing);
    } else {
      // Listing completed
      await this.completeListing(listingId, 'sold');
    }

    // Record transaction
    await this.economicEngine.recordTransaction(
      listing.item_id,
      listing.region_id,
      purchaseQuantity,
      listing.price,
      'marketplace_sale'
    );

    // Update reputation
    await this.reputationSystem.updateReputation(listing.seller_id, 'successful_sale');
    await this.reputationSystem.updateReputation(buyerId, 'successful_purchase');

    // Update supply/demand
    await this.economicEngine.updateSupplyDemand(
      listing.item_id,
      listing.region_id,
      -purchaseQuantity,
      purchaseQuantity
    );

    // Emit events
    this.emit('itemPurchased', {
      listingId,
      sellerId: listing.seller_id,
      buyerId,
      quantity: purchaseQuantity,
      totalPrice: totalPrice.toString()
    });

    return {
      success: true,
      listing,
      buyerId,
      quantity: purchaseQuantity,
      totalPrice: totalPrice.toString()
    };
  }

  /**
   * Make an offer on a negotiable listing
   */
  async makeOffer(listingId, buyerId, offerAmount, message = '') {
    const listing = await this.getListing(listingId);

    if (!listing) {
      throw new Error('Listing not found');
    }

    if (listing.status !== 'active') {
      throw new Error('Listing is not active');
    }

    if (listing.listing_type !== 'negotiable') {
      throw new Error('This listing does not accept offers');
    }

    if (listing.seller_id === buyerId) {
      throw new Error('Cannot make an offer on your own listing');
    }

    const offer = new Decimal(offerAmount);

    // Check minimum offer
    if (listing.minimum_offer && offer.lessThan(listing.minimum_offer)) {
      throw new Error(`Offer must be at least ${listing.minimum_offer.toString()}`);
    }

    // Check for auto-accept
    if (listing.auto_accept_price && offer.greaterThanOrEqualTo(listing.auto_accept_price)) {
      return await this.purchaseListing(listingId, buyerId);
    }

    // Create offer record
    const offerId = uuidv4();
    const offerRecord = {
      id: offerId,
      listing_id: listingId,
      buyer_id: buyerId,
      amount: offer.toString(),
      message,
      status: 'pending',
      created_at: new Date()
    };

    await this.db('listing_offers').insert(offerRecord);

    // Emit event
    this.emit('offerMade', {
      offerId,
      listingId,
      buyerId,
      sellerId: listing.seller_id,
      amount: offer.toString(),
      message
    });

    return {
      success: true,
      offer: offerRecord
    };
  }

  /**
   * Respond to an offer (accept, reject, counter)
   */
  async respondToOffer(offerId, sellerId, response, counterAmount = null, message = '') {
    const offer = await this.db('listing_offers')
      .where('id', offerId)
      .first();

    if (!offer) {
      throw new Error('Offer not found');
    }

    const listing = await this.getListing(offer.listing_id);

    if (listing.seller_id !== sellerId) {
      throw new Error('Only the seller can respond to offers');
    }

    if (offer.status !== 'pending') {
      throw new Error('Offer is no longer pending');
    }

    let result;

    switch (response) {
      case 'accept':
        // Accept the offer
        result = await this.acceptOffer(offer, listing);
        break;

      case 'reject':
        // Reject the offer
        await this.db('listing_offers')
          .where('id', offerId)
          .update({
            status: 'rejected',
            seller_response: message,
            updated_at: new Date()
          });

        this.emit('offerRejected', {
          offerId,
          buyerId: offer.buyer_id,
          sellerId,
          message
        });

        result = { success: true, action: 'rejected' };
        break;

      case 'counter':
        // Make a counter-offer
        if (!counterAmount) {
          throw new Error('Counter amount is required for counter-offers');
        }

        result = await this.makeCounterOffer(offer, sellerId, counterAmount, message);
        break;

      default:
        throw new Error('Invalid response type');
    }

    return result;
  }

  /**
   * Accept an offer
   */
  async acceptOffer(offer, listing) {
    const totalPrice = new Decimal(offer.amount);

    // Process payment
    await this.processPayment(offer.buyer_id, listing.seller_id, totalPrice, this.marketplaceFee);

    // Transfer items
    await this.transferItems(listing.seller_id, offer.buyer_id, listing.item_id, listing.quantity, 'marketplace');

    // Update offer status
    await this.db('listing_offers')
      .where('id', offer.id)
      .update({
        status: 'accepted',
        updated_at: new Date()
      });

    // Complete listing
    await this.completeListing(listing.id, 'sold');

    // Record transaction
    await this.economicEngine.recordTransaction(
      listing.item_id,
      listing.region_id,
      listing.quantity,
      totalPrice.div(listing.quantity),
      'marketplace_sale'
    );

    // Update reputation
    await this.reputationSystem.updateReputation(listing.seller_id, 'successful_sale');
    await this.reputationSystem.updateReputation(offer.buyer_id, 'successful_purchase');

    // Update supply/demand
    await this.economicEngine.updateSupplyDemand(
      listing.item_id,
      listing.region_id,
      -listing.quantity,
      listing.quantity
    );

    // Emit events
    this.emit('offerAccepted', {
      offerId: offer.id,
      listingId: listing.id,
      sellerId: listing.seller_id,
      buyerId: offer.buyer_id,
      amount: offer.amount
    });

    return {
      success: true,
      action: 'accepted',
      listingId: listing.id,
      amount: offer.amount
    };
  }

  /**
   * Make a counter-offer
   */
  async makeCounterOffer(originalOffer, sellerId, counterAmount, message) {
    const counterOfferId = uuidv4();
    const counterOffer = {
      id: counterOfferId,
      original_offer_id: originalOffer.id,
      listing_id: originalOffer.listing_id,
      seller_id: sellerId,
      buyer_id: originalOffer.buyer_id,
      amount: counterAmount.toString(),
      message,
      status: 'pending',
      created_at: new Date()
    };

    await this.db('counter_offers').insert(counterOffer);

    // Update original offer status
    await this.db('listing_offers')
      .where('id', originalOffer.id)
      .update({
        status: 'countered',
        updated_at: new Date()
      });

    // Emit event
    this.emit('counterOfferMade', {
      counterOfferId,
      originalOfferId: originalOffer.id,
      listingId: originalOffer.listing_id,
      sellerId,
      buyerId: originalOffer.buyer_id,
      amount: counterAmount.toString(),
      message
    });

    return {
      success: true,
      action: 'countered',
      counterOffer
    };
  }

  /**
   * Create a direct trade request
   */
  async createTradeRequest(tradeData) {
    const {
      requesterId,
      targetId,
      requesterItems,
      targetItems,
      requesterCurrency,
      targetCurrency,
      message = '',
      duration = 24 * 60 * 60 * 1000 // 24 hours
    } = tradeData;

    // Validate trade data
    await this.validateTradeData(tradeData);

    const tradeId = uuidv4();
    const now = new Date();
    const expiresAt = new Date(now.getTime() + duration);

    const tradeRequest = {
      id: tradeId,
      requester_id: requesterId,
      target_id: targetId,
      requester_items: JSON.stringify(requesterItems),
      target_items: JSON.stringify(targetItems),
      requester_currency: requesterCurrency ? new Decimal(requesterCurrency).toString() : null,
      target_currency: targetCurrency ? new Decimal(targetCurrency).toString() : null,
      message,
      status: 'pending',
      created_at: now,
      expires_at: expiresAt
    };

    await this.db('trade_requests').insert(tradeRequest);

    // Store in memory
    this.tradeRequests.set(tradeId, tradeRequest);

    // Set expiration timer
    this.setTradeTimer(tradeId, expiresAt);

    // Emit event
    this.emit('tradeRequestCreated', {
      tradeId,
      requesterId,
      targetId,
      message
    });

    return tradeRequest;
  }

  /**
   * Accept a trade request
   */
  async acceptTradeRequest(tradeId, targetId) {
    const trade = this.tradeRequests.get(tradeId) ||
                  await this.db('trade_requests').where('id', tradeId).first();

    if (!trade) {
      throw new Error('Trade request not found');
    }

    if (trade.target_id !== targetId) {
      throw new Error('You are not the target of this trade');
    }

    if (trade.status !== 'pending') {
      throw new Error('Trade request is no longer pending');
    }

    const requesterItems = JSON.parse(trade.requester_items);
    const targetItems = JSON.parse(trade.target_items);
    const requesterCurrency = trade.requester_currency ? new Decimal(trade.requester_currency) : null;
    const targetCurrency = trade.target_currency ? new Decimal(trade.target_currency) : null;

    // Validate both parties have the items/currency
    const hasRequesterItems = await this.validateTradeItems(trade.requester_id, requesterItems, requesterCurrency);
    const hasTargetItems = await this.validateTradeItems(trade.target_id, targetItems, targetCurrency);

    if (!hasRequesterItems || !hasTargetItems) {
      throw new Error('Trade validation failed - missing items or currency');
    }

    // Process the trade
    await this.processTrade(trade);

    // Update trade status
    await this.db('trade_requests')
      .where('id', tradeId)
      .update({
        status: 'accepted',
        completed_at: new Date()
      });

    // Clear timer
    if (this.tradeTimers && this.tradeTimers.has(tradeId)) {
      clearTimeout(this.tradeTimers.get(tradeId));
      this.tradeTimers.delete(tradeId);
    }

    // Remove from memory
    this.tradeRequests.delete(tradeId);

    // Update reputation
    await this.reputationSystem.updateReputation(trade.requester_id, 'successful_trade');
    await this.reputationSystem.updateReputation(trade.target_id, 'successful_trade');

    // Emit event
    this.emit('tradeAccepted', {
      tradeId,
      requesterId: trade.requester_id,
      targetId: trade.target_id
    });

    return {
      success: true,
      tradeId
    };
  }

  /**
   * Process a trade (transfer items and currency)
   */
  async processTrade(trade) {
    const requesterItems = JSON.parse(trade.requester_items);
    const targetItems = JSON.parse(trade.target_items);

    // Transfer items from requester to target
    for (const item of requesterItems) {
      await this.transferItems(
        trade.requester_id,
        trade.target_id,
        item.item_id,
        item.quantity,
        'trade'
      );
    }

    // Transfer items from target to requester
    for (const item of targetItems) {
      await this.transferItems(
        trade.target_id,
        trade.requester_id,
        item.item_id,
        item.quantity,
        'trade'
      );
    }

    // Transfer currency
    if (trade.requester_currency) {
      await this.transferCurrency(
        trade.requester_id,
        trade.target_id,
        new Decimal(trade.requester_currency),
        'trade'
      );
    }

    if (trade.target_currency) {
      await this.transferCurrency(
        trade.target_id,
        trade.requester_id,
        new Decimal(trade.target_currency),
        'trade'
      );
    }
  }

  /**
   * Search marketplace listings
   */
  async searchListings(filters = {}) {
    const {
      itemId,
      sellerId,
      regionId,
      categoryIds,
      minPrice,
      maxPrice,
      listingType,
      tags,
      sortBy = 'created_at',
      sortOrder = 'desc',
      limit = 50,
      offset = 0,
      includeExpired = false
    } = filters;

    let query = this.db('market_listings')
      .join('items', 'market_listings.item_id', 'items.id')
      .join('players', 'market_listings.seller_id', 'players.id');

    if (!includeExpired) {
      query = query.where('market_listings.status', 'active')
                   .where('market_listings.expires_at', '>', new Date());
    }

    if (itemId) {
      query = query.where('market_listings.item_id', itemId);
    }

    if (sellerId) {
      query = query.where('market_listings.seller_id', sellerId);
    }

    if (regionId) {
      query = query.where('market_listings.region_id', regionId);
    }

    if (categoryIds && categoryIds.length > 0) {
      query = query.whereIn('items.category_id', categoryIds);
    }

    if (minPrice) {
      query = query.where('market_listings.price', '>=', minPrice);
    }

    if (maxPrice) {
      query = query.where('market_listings.price', '<=', maxPrice);
    }

    if (listingType) {
      query = query.where('market_listings.listing_type', listingType);
    }

    if (tags && tags.length > 0) {
      query = query.whereRaw('JSON_CONTAINS(market_listings.tags, ?)', JSON.stringify(tags));
    }

    const listings = await query
      .orderBy(`market_listings.${sortBy}`, sortOrder)
      .limit(limit)
      .offset(offset)
      .select(
        'market_listings.*',
        'items.name as item_name',
        'items.rarity as item_rarity',
        'items.icon as item_icon',
        'items.category_id as item_category_id',
        'players.username as seller_username'
      );

    return listings.map(listing => ({
      ...listing,
      price: new Decimal(listing.price),
      minimum_offer: listing.minimum_offer ? new Decimal(listing.minimum_offer) : null,
      auto_accept_price: listing.auto_accept_price ? new Decimal(listing.auto_accept_price) : null,
      tags: JSON.parse(listing.tags)
    }));
  }

  /**
   * Get marketplace statistics
   */
  async getMarketplaceStats(regionId = 'global', timeRange = 7) {
    const startDate = new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000);

    const stats = await this.db('market_listings')
      .where('region_id', regionId)
      .where('created_at', '>=', startDate)
      .select(
        this.db.raw('COUNT(*) as total_listings'),
        this.db.raw('SUM(CASE WHEN status = \'sold\' THEN 1 ELSE 0 END) as sold_listings'),
        this.db.raw('SUM(CASE WHEN status = \'expired\' THEN 1 ELSE 0 END) as expired_listings'),
        this.db.raw('SUM(CASE WHEN status = \'cancelled\' THEN 1 ELSE 0 END) as cancelled_listings'),
        this.db.raw('SUM(price * quantity) as total_volume'),
        this.db.raw('AVG(price) as avg_price'),
        this.db.raw('SUM(views) as total_views')
      )
      .first();

    const successRate = stats.total_listings > 0
      ? (stats.sold_listings / stats.total_listings) * 100
      : 0;

    // Get top categories
    const topCategories = await this.db('market_listings')
      .join('items', 'market_listings.item_id', 'items.id')
      .join('item_categories', 'items.category_id', 'item_categories.id')
      .where('market_listings.region_id', regionId)
      .where('market_listings.created_at', '>=', startDate)
      .groupBy('item_categories.id', 'item_categories.name')
      .select(
        'item_categories.id',
        'item_categories.name',
        this.db.raw('COUNT(*) as listing_count'),
        this.db.raw('SUM(market_listings.price * market_listings.quantity) as volume')
      )
      .orderBy('volume', 'desc')
      .limit(5);

    return {
      totalListings: parseInt(stats.total_listings) || 0,
      soldListings: parseInt(stats.sold_listings) || 0,
      expiredListings: parseInt(stats.expired_listings) || 0,
      cancelledListings: parseInt(stats.cancelled_listings) || 0,
      successRate,
      totalVolume: stats.total_volume || new Decimal(0),
      avgPrice: stats.avg_price || new Decimal(0),
      totalViews: parseInt(stats.total_views) || 0,
      topCategories
    };
  }

  /**
   * Get player's marketplace activity
   */
  async getPlayerMarketplaceActivity(playerId, timeRange = 30) {
    const startDate = new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000);

    const sales = await this.db('market_listings')
      .where('seller_id', playerId)
      .where('status', 'sold')
      .where('updated_at', '>=', startDate)
      .select(
        this.db.raw('COUNT(*) as total_sales'),
        this.db.raw('SUM(price * quantity) as total_revenue'),
        this.db.raw('AVG(price) as avg_sale_price')
      )
      .first();

    const purchases = await this.db('market_transactions')
      .where('from_player_id', playerId)
      .where('transaction_type', 'marketplace_sale')
      .where('created_at', '>=', startDate)
      .select(
        this.db.raw('COUNT(*) as total_purchases'),
        this.db.raw('SUM(total_price) as total_spent'),
        this.db.raw('AVG(price) as avg_purchase_price')
      )
      .first();

    const activeListings = await this.db('market_listings')
      .where('seller_id', playerId)
      .where('status', 'active')
      .count('* as count')
      .first();

    const reputation = await this.reputationSystem.getPlayerReputation(playerId);

    return {
      totalSales: parseInt(sales.total_sales) || 0,
      totalRevenue: sales.total_revenue || new Decimal(0),
      avgSalePrice: sales.avg_sale_price || new Decimal(0),
      totalPurchases: parseInt(purchases.total_purchases) || 0,
      totalSpent: purchases.total_spent || new Decimal(0),
      avgPurchasePrice: purchases.avg_purchase_price || new Decimal(0),
      activeListings: parseInt(activeListings.count) || 0,
      reputation
    };
  }

  /**
   * Helper methods
   */
  async getListing(listingId) {
    if (this.activeListings.has(listingId)) {
      return this.activeListings.get(listingId);
    }

    const listing = await this.db('market_listings')
      .where('id', listingId)
      .first();

    if (!listing) return null;

    listing.price = new Decimal(listing.price);
    if (listing.minimum_offer) {
      listing.minimum_offer = new Decimal(listing.minimum_offer);
    }
    if (listing.auto_accept_price) {
      listing.auto_accept_price = new Decimal(listing.auto_accept_price);
    }

    return listing;
  }

  async completeListing(listingId, status) {
    await this.db('market_listings')
      .where('id', listingId)
      .update({
        status,
        updated_at: new Date()
      });

    // Clear timer
    if (this.listingTimers && this.listingTimers.has(listingId)) {
      clearTimeout(this.listingTimers.get(listingId));
      this.listingTimers.delete(listingId);
    }

    // Remove from active listings
    this.activeListings.delete(listingId);
  }

  setListingTimer(listingId, endTime) {
    const timeUntilExpiry = endTime.getTime() - Date.now();

    if (timeUntilExpiry <= 0) {
      setImmediate(() => this.expireListing(listingId));
      return;
    }

    if (!this.listingTimers) {
      this.listingTimers = new Map();
    }

    const timer = setTimeout(() => {
      this.expireListing(listingId);
    }, timeUntilExpiry);

    this.listingTimers.set(listingId, timer);
  }

  async expireListing(listingId) {
    const listing = this.activeListings.get(listingId);
    if (!listing) return;

    await this.completeListing(listingId, 'expired');

    this.emit('listingExpired', {
      listingId,
      sellerId: listing.seller_id
    });
  }

  setTradeTimer(tradeId, expiresAt) {
    const timeUntilExpiry = expiresAt.getTime() - Date.now();

    if (timeUntilExpiry <= 0) {
      setImmediate(() => this.expireTradeRequest(tradeId));
      return;
    }

    if (!this.tradeTimers) {
      this.tradeTimers = new Map();
    }

    const timer = setTimeout(() => {
      this.expireTradeRequest(tradeId);
    }, timeUntilExpiry);

    this.tradeTimers.set(tradeId, timer);
  }

  async expireTradeRequest(tradeId) {
    await this.db('trade_requests')
      .where('id', tradeId)
      .update({
        status: 'expired',
        updated_at: new Date()
      });

    this.tradeRequests.delete(tradeId);

    this.emit('tradeRequestExpired', { tradeId });
  }

  async validateListingData(listingData) {
    // Implementation would validate all aspects of the listing
    return true;
  }

  async validateTradeData(tradeData) {
    // Implementation would validate trade data
    return true;
  }

  async checkPlayerFunds(playerId, amount) {
    // Implementation would check player's currency balance
    return true;
  }

  async checkPlayerInventory(playerId, itemId, quantity) {
    // Implementation would check player's inventory
    return true;
  }

  async validateTradeItems(playerId, items, currency) {
    // Implementation would validate player has the items/currency for trade
    return true;
  }

  async processPayment(buyerId, sellerId, amount, fee) {
    // Implementation would process the payment with fee deduction
  }

  async transferItems(fromPlayerId, toPlayerId, itemId, quantity, reason) {
    // Implementation would transfer items between players
  }

  async transferCurrency(fromPlayerId, toPlayerId, amount, reason) {
    // Implementation would transfer currency between players
  }
}

class ReputationSystem {
  constructor(knex) {
    this.db = knex;
  }

  async updateReputation(playerId, action) {
    const reputationChanges = {
      successful_sale: 5,
      successful_purchase: 3,
      successful_trade: 4,
      cancelled_sale: -2,
      rejected_trade: -1
    };

    const change = reputationChanges[action] || 0;

    if (change === 0) return;

    await this.db('player_reputation')
      .insert({
        player_id: playerId,
        reputation_change: change,
        action,
        created_at: new Date()
      })
      .onConflict('player_id')
      .merge({
        reputation: this.db.raw('reputation + ?', change),
        updated_at: new Date()
      });
  }

  async getPlayerReputation(playerId) {
    const reputation = await this.db('player_reputation')
      .where('player_id', playerId)
      .first();

    return {
      score: reputation?.reputation || 0,
      level: this.calculateReputationLevel(reputation?.reputation || 0),
      totalActions: reputation?.total_actions || 0
    };
  }

  calculateReputationLevel(score) {
    if (score >= 100) return 'Legendary';
    if (score >= 50) return 'Esteemed';
    if (score >= 25) return 'Trusted';
    if (score >= 10) return 'Reliable';
    if (score >= 0) return 'Neutral';
    if (score >= -10) return 'Unreliable';
    return 'Dishonorable';
  }
}

module.exports = Marketplace;