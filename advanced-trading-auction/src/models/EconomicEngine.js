const Decimal = require('decimal.js');
const _ = require('lodash');
const EventEmitter = require('events');

class EconomicEngine extends EventEmitter {
  constructor(redisClient, knex) {
    super();
    this.redis = redisClient;
    this.db = knex;
    this.priceCache = new Map();
    this.supplyDemandData = new Map();
    this.marketTrends = new Map();
    this.regionalPrices = new Map();

    // Economic parameters
    this.elasticityCoefficient = 0.5;
    this.baseVolatility = 0.02;
    this.trendSmoothingFactor = 0.3;
    this.supplyDecayRate = 0.001;
    this.demandDecayRate = 0.002;
  }

  /**
   * Calculate dynamic price based on supply and demand
   */
  async calculateDynamicPrice(itemId, regionId = 'global', quantity = 1) {
    const cacheKey = `price:${itemId}:${regionId}`;

    // Check cache first
    if (this.priceCache.has(cacheKey)) {
      const cached = this.priceCache.get(cacheKey);
      if (Date.now() - cached.timestamp < 30000) { // 30 seconds cache
        return cached.price.mul(quantity);
      }
    }

    const basePrice = await this.getBasePrice(itemId);
    const supplyDemand = await this.getSupplyDemandRatio(itemId, regionId);
    const marketTrend = await this.getMarketTrend(itemId, regionId);
    const volatility = await this.calculateVolatility(itemId, regionId);

    // Apply supply-demand elasticity
    const priceModifier = this.calculateSupplyDemandModifier(supplyDemand);

    // Apply trend factor
    const trendFactor = Decimal(1).add(marketTrend);

    // Apply volatility
    const volatilityFactor = Decimal(1).add(Decimal(volatility).mul(Decimal.random().sub(0.5)));

    // Regional modifier
    const regionalModifier = await this.getRegionalModifier(itemId, regionId);

    // Calculate final price
    const finalPrice = basePrice
      .mul(priceModifier)
      .mul(trendFactor)
      .mul(volatilityFactor)
      .mul(regionalModifier)
      .mul(quantity);

    // Cache the result
    this.priceCache.set(cacheKey, {
      price: finalPrice.div(quantity), // Store per-unit price
      timestamp: Date.now()
    });

    return finalPrice;
  }

  /**
   * Calculate price modification based on supply-demand ratio
   */
  calculateSupplyDemandModifier(supplyDemand) {
    if (supplyDemand.eq(0)) return Decimal(10); // Very high demand, no supply

    // Price elasticity formula: P = P0 * (D/S)^elasticity
    const modifier = Decimal(1).div(supplyDemand.pow(this.elasticityCoefficient));

    // Clamp modifier to prevent extreme prices
    return Decimal.max(0.1, Decimal.min(10, modifier));
  }

  /**
   * Get supply-demand ratio for an item
   */
  async getSupplyDemandRatio(itemId, regionId) {
    const cacheKey = `sd:${itemId}:${regionId}`;

    if (this.supplyDemandData.has(cacheKey)) {
      const cached = this.supplyDemandData.get(cacheKey);
      if (Date.now() - cached.timestamp < 60000) {
        return cached.ratio;
      }
    }

    // Get current supply (listings, inventory)
    const supply = await this.calculateSupply(itemId, regionId);

    // Get current demand (active searches, recent sales velocity)
    const demand = await this.calculateDemand(itemId, regionId);

    const ratio = demand.gt(0) ? supply.div(demand) : Decimal(0);

    // Cache the result
    this.supplyDemandData.set(cacheKey, {
      ratio,
      timestamp: Date.now()
    });

    return ratio;
  }

  /**
   * Calculate current supply for an item
   */
  async calculateSupply(itemId, regionId) {
    let totalSupply = new Decimal(0);

    // Get active listings
    const listings = await this.db('market_listings')
      .where('item_id', itemId)
      .where('status', 'active')
      .where(function() {
        if (regionId !== 'global') {
          this.where('region_id', regionId)
            .orWhere('region_id', 'global');
        }
      })
      .sum('quantity as total');

    if (listings[0]?.total) {
      totalSupply = totalSupply.add(listings[0].total);
    }

    // Get inventory estimates from active players
    const inventory = await this.redis.get(`supply:inventory:${itemId}:${regionId}`);
    if (inventory) {
      totalSupply = totalSupply.add(new Decimal(inventory));
    }

    // Apply supply decay over time
    const lastUpdate = await this.redis.get(`supply:last_update:${itemId}:${regionId}`);
    if (lastUpdate) {
      const hoursSinceUpdate = (Date.now() - parseInt(lastUpdate)) / (1000 * 60 * 60);
      const decayFactor = Decimal(1 - this.supplyDecayRate).pow(hoursSinceUpdate);
      totalSupply = totalSupply.mul(decayFactor);
    }

    return totalSupply;
  }

  /**
   * Calculate current demand for an item
   */
  async calculateDemand(itemId, regionId) {
    let totalDemand = new Decimal(0);

    // Get recent sales velocity (last 24 hours)
    const recentSales = await this.db('market_sales')
      .where('item_id', itemId)
      .where('created_at', '>', new Date(Date.now() - 24 * 60 * 60 * 1000))
      .where(function() {
        if (regionId !== 'global') {
          this.where('region_id', regionId)
            .orWhere('region_id', 'global');
        }
      })
      .sum('quantity as total');

    if (recentSales[0]?.total) {
      totalDemand = totalDemand.add(recentSales[0].total);
    }

    // Get active search queries
    const searches = await this.redis.get(`demand:searches:${itemId}:${regionId}`);
    if (searches) {
      totalDemand = totalDemand.add(new Decimal(searches).mul(0.1)); // Weight searches less than actual sales
    }

    // Get watchlist count
    const watchlists = await this.redis.get(`demand:watchlists:${itemId}:${regionId}`);
    if (watchlists) {
      totalDemand = totalDemand.add(new Decimal(watchlists).mul(0.05));
    }

    // Apply demand decay
    const lastUpdate = await this.redis.get(`demand:last_update:${itemId}:${regionId}`);
    if (lastUpdate) {
      const hoursSinceUpdate = (Date.now() - parseInt(lastUpdate)) / (1000 * 60 * 60);
      const decayFactor = Decimal(1 - this.demandDecayRate).pow(hoursSinceUpdate);
      totalDemand = totalDemand.mul(decayFactor);
    }

    return totalDemand;
  }

  /**
   * Get market trend for an item
   */
  async getMarketTrend(itemId, regionId) {
    const cacheKey = `trend:${itemId}:${regionId}`;

    if (this.marketTrends.has(cacheKey)) {
      const cached = this.marketTrends.get(cacheKey);
      if (Date.now() - cached.timestamp < 300000) { // 5 minutes cache
        return cached.trend;
      }
    }

    // Get price history for the last 7 days
    const priceHistory = await this.db('market_prices')
      .where('item_id', itemId)
      .where('region_id', regionId)
      .where('created_at', '>', new Date(Date.now() - 7 * 24 * 60 * 60 * 1000))
      .orderBy('created_at', 'asc')
      .select('price', 'created_at');

    if (priceHistory.length < 2) {
      return Decimal(0);
    }

    // Calculate trend using linear regression
    const trend = this.calculateLinearTrend(priceHistory);

    // Smooth the trend
    const smoothedTrend = this.smoothTrend(trend, cacheKey);

    // Cache the result
    this.marketTrends.set(cacheKey, {
      trend: smoothedTrend,
      timestamp: Date.now()
    });

    return smoothedTrend;
  }

  /**
   * Calculate linear trend from price history
   */
  calculateLinearTrend(priceHistory) {
    const n = priceHistory.length;
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;

    priceHistory.forEach((entry, index) => {
      const x = index;
      const y = new Decimal(entry.price);
      sumX += x;
      sumY = sumY.add(y);
      sumXY += x * y.toNumber();
      sumX2 += x * x;
    });

    const slope = (n * sumXY - sumX * sumY.toNumber()) / (n * sumX2 - sumX * sumX);
    const avgPrice = sumY.div(n);

    // Return trend as percentage change per day
    return Decimal(slope * 24).div(avgPrice);
  }

  /**
   * Smooth trend using exponential moving average
   */
  smoothTrend(newTrend, cacheKey) {
    const previousTrend = this.marketTrends.get(cacheKey)?.trend || Decimal(0);

    return previousTrend
      .mul(Decimal(1).sub(this.trendSmoothingFactor))
      .add(newTrend.mul(this.trendSmoothingFactor));
  }

  /**
   * Calculate volatility for an item
   */
  async calculateVolatility(itemId, regionId) {
    // Get price history for the last 24 hours
    const priceHistory = await this.db('market_prices')
      .where('item_id', itemId)
      .where('region_id', regionId)
      .where('created_at', '>', new Date(Date.now() - 24 * 60 * 60 * 1000))
      .orderBy('created_at', 'asc')
      .select('price');

    if (priceHistory.length < 10) {
      return this.baseVolatility;
    }

    // Calculate standard deviation of price changes
    const prices = priceHistory.map(p => new Decimal(p.price));
    const priceChanges = [];

    for (let i = 1; i < prices.length; i++) {
      const change = prices[i].div(prices[i - 1]).sub(1);
      priceChanges.push(change);
    }

    const meanChange = priceChanges.reduce((sum, change) => sum.add(change), Decimal(0))
      .div(priceChanges.length);

    const variance = priceChanges.reduce((sum, change) => {
      const diff = change.sub(meanChange);
      return sum.add(diff.mul(diff));
    }, Decimal(0)).div(priceChanges.length);

    const volatility = Math.sqrt(variance.toNumber());

    return Math.max(this.baseVolatility, Math.min(0.5, volatility));
  }

  /**
   * Get regional price modifier
   */
  async getRegionalModifier(itemId, regionId) {
    if (regionId === 'global') return Decimal(1);

    const cacheKey = `regional:${itemId}:${regionId}`;

    // Check cache
    let modifier = await this.redis.get(cacheKey);
    if (modifier) {
      return Decimal(modifier);
    }

    // Calculate regional modifier based on:
    // 1. Regional supply/demand balance
    // 2. Local economic events
    // 3. Regional prosperity index

    const supplyDemand = await this.getSupplyDemandRatio(itemId, regionId);
    const globalSupplyDemand = await this.getSupplyDemandRatio(itemId, 'global');

    const regionalRatio = supplyDemand.div(globalSupplyDemand);

    // Base modifier from supply/demand difference
    let baseModifier = Decimal(1).div(regionalRatio.pow(0.2));

    // Check for regional events
    const events = await this.getActiveRegionalEvents(regionId);
    events.forEach(event => {
      if (event.type === 'prosperity') {
        baseModifier = baseModifier.mul(Decimal(event.impact));
      } else if (event.type === 'shortage') {
        baseModifier = baseModifier.mul(Decimal(event.impact));
      }
    });

    // Clamp modifier to reasonable range
    modifier = Decimal.max(0.5, Decimal.min(2, baseModifier));

    // Cache for 1 hour
    await this.redis.setex(cacheKey, 3600, modifier.toString());

    return modifier;
  }

  /**
   * Get base price for an item
   */
  async getBasePrice(itemId) {
    const item = await this.db('items').where('id', itemId).first();
    if (!item) {
      throw new Error(`Item ${itemId} not found`);
    }

    return new Decimal(item.base_price || 100);
  }

  /**
   * Get active regional events
   */
  async getActiveRegionalEvents(regionId) {
    return await this.db('regional_events')
      .where('region_id', regionId)
      .where('starts_at', '<=', new Date())
      .where('ends_at', '>', new Date())
      .where('active', true);
  }

  /**
   * Update supply/demand data
   */
  async updateSupplyDemand(itemId, regionId, supplyChange = 0, demandChange = 0) {
    const supplyKey = `supply:inventory:${itemId}:${regionId}`;
    const demandKey = `demand:searches:${itemId}:${regionId}`;

    if (supplyChange !== 0) {
      await this.redis.incrby(supplyKey, supplyChange);
      await this.redis.set(`supply:last_update:${itemId}:${regionId}`, Date.now());
    }

    if (demandChange !== 0) {
      await this.redis.incrby(demandKey, demandChange);
      await this.redis.set(`demand:last_update:${itemId}:${regionId}`, Date.now());
    }

    // Clear relevant caches
    const cacheKey = `sd:${itemId}:${regionId}`;
    this.supplyDemandData.delete(cacheKey);

    // Emit event for real-time updates
    this.emit('supplyDemandUpdated', { itemId, regionId, supplyChange, demandChange });
  }

  /**
   * Record a transaction for market analysis
   */
  async recordTransaction(itemId, regionId, quantity, price, transactionType) {
    await this.db('market_transactions').insert({
      item_id: itemId,
      region_id: regionId,
      quantity,
      price,
      total_price: price.mul(quantity),
      transaction_type: transactionType,
      created_at: new Date()
    });

    // Update price history
    await this.db('market_prices').insert({
      item_id: itemId,
      region_id: regionId,
      price,
      created_at: new Date()
    });

    // Clear price cache
    const priceCacheKey = `price:${itemId}:${regionId}`;
    this.priceCache.delete(priceCacheKey);
  }

  /**
   * Predict future price using time series analysis
   */
  async predictPrice(itemId, regionId, hoursAhead = 24) {
    const priceHistory = await this.db('market_prices')
      .where('item_id', itemId)
      .where('region_id', regionId)
      .where('created_at', '>', new Date(Date.now() - 7 * 24 * 60 * 60 * 1000))
      .orderBy('created_at', 'desc')
      .limit(168) // Last week of hourly data
      .select('price', 'created_at');

    if (priceHistory.length < 24) {
      // Not enough data, return current price
      return await this.calculateDynamicPrice(itemId, regionId);
    }

    // Simple time series prediction using weighted moving average
    const currentPrice = await this.calculateDynamicPrice(itemId, regionId);
    const trend = await this.getMarketTrend(itemId, regionId);
    const volatility = await this.calculateVolatility(itemId, regionId);

    // Predict price with trend and uncertainty
    const predictedPrice = currentPrice
      .mul(Decimal(1).add(trend.mul(hoursAhead / 24)))
      .mul(Decimal(1).add(Decimal(volatility * 0.5).mul(Decimal.random().sub(0.5))));

    return predictedPrice;
  }

  /**
   * Detect market manipulation
   */
  async detectMarketManipulation(itemId, regionId, playerId) {
    const recentTransactions = await this.db('market_transactions')
      .where('item_id', itemId)
      .where('region_id', regionId)
      .where('player_id', playerId)
      .where('created_at', '>', new Date(Date.now() - 24 * 60 * 60 * 1000));

    const totalVolume = recentTransactions.reduce((sum, tx) =>
      sum + tx.total_price.toNumber(), 0
    );

    const avgPrice = recentTransactions.length > 0
      ? totalVolume / recentTransactions.reduce((sum, tx) => sum + tx.quantity, 0)
      : 0;

    const marketAvgPrice = await this.calculateDynamicPrice(itemId, regionId);

    // Suspicious if:
    // 1. Very high volume (> threshold)
    // 2. Price significantly different from market average
    // 3. Many small transactions (wash trading)

    const highVolume = totalVolume > 100000; // Configurable threshold
    const priceAnomaly = marketAvgPrice.gt(0) &&
      Math.abs(avgPrice - marketAvgPrice.toNumber()) / marketAvgPrice.toNumber() > 0.3;
    const manySmallTransactions = recentTransactions.length > 50 &&
      recentTransactions.reduce((sum, tx) => sum + tx.quantity, 0) / recentTransactions.length < 5;

    return {
      suspicious: highVolume || priceAnomaly || manySmallTransactions,
      reasons: {
        highVolume,
        priceAnomaly,
        manySmallTransactions
      },
      score: (highVolume ? 0.4 : 0) + (priceAnomaly ? 0.4 : 0) + (manySmallTransactions ? 0.2 : 0)
    };
  }
}

module.exports = EconomicEngine;