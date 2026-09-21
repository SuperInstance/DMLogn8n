const Decimal = require('decimal.js');
const _ = require('lodash');
const EventEmitter = require('events');

class MarketAnalyzer extends EventEmitter {
  constructor(knex, redis) {
    super();
    this.db = knex;
    this.redis = redis;
    this.analysisCache = new Map();
    this.trendAnalysis = new Map();
  }

  /**
   * Analyze market trends for specific item categories
   */
  async analyzeCategoryTrends(categoryId, regionId = 'global', timeRange = 7) {
    const cacheKey = `category_trends:${categoryId}:${regionId}:${timeRange}`;

    if (this.analysisCache.has(cacheKey)) {
      const cached = this.analysisCache.get(cacheKey);
      if (Date.now() - cached.timestamp < 3600000) { // 1 hour cache
        return cached.data;
      }
    }

    const startDate = new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000);

    // Get all items in category
    const items = await this.db('items')
      .where('category_id', categoryId)
      .select('id', 'name', 'rarity');

    const analysis = {
      category: categoryId,
      region: regionId,
      timeRange: timeRange,
      items: [],
      summary: {
        totalVolume: new Decimal(0),
        avgPriceChange: new Decimal(0),
        volatilityIndex: 0,
        hotItems: [],
        coldItems: [],
        topMovers: []
      }
    };

    let totalPriceChange = new Decimal(0);
    let priceChanges = [];
    const itemAnalyses = [];

    for (const item of items) {
      const itemAnalysis = await this.analyzeItemPerformance(item.id, regionId, timeRange);
      itemAnalyses.push(itemAnalysis);

      analysis.items.push({
        id: item.id,
        name: item.name,
        rarity: item.rarity,
        ...itemAnalysis
      });

      totalPriceChange = totalPriceChange.add(itemAnalysis.priceChangePercent);
      priceChanges.push(itemAnalysis.priceChangePercent.toNumber());
    }

    // Calculate category summary
    if (items.length > 0) {
      analysis.summary.avgPriceChange = totalPriceChange.div(items.length);

      // Calculate volatility index (standard deviation of price changes)
      const mean = priceChanges.reduce((sum, change) => sum + change, 0) / priceChanges.length;
      const variance = priceChanges.reduce((sum, change) => sum + Math.pow(change - mean, 2), 0) / priceChanges.length;
      analysis.summary.volatilityIndex = Math.sqrt(variance);

      // Identify hot items (top 20% by volume)
      const sortedByVolume = [...itemAnalyses].sort((a, b) => b.totalVolume.cmp(a.totalVolume));
      analysis.summary.hotItems = sortedByVolume.slice(0, Math.ceil(items.length * 0.2))
        .map(item => ({ id: item.itemId, name: item.itemName, volume: item.totalVolume }));

      // Identify cold items (bottom 20% by volume)
      analysis.summary.coldItems = sortedByVolume.slice(-Math.ceil(items.length * 0.2))
        .map(item => ({ id: item.itemId, name: item.itemName, volume: item.totalVolume }));

      // Identify top movers (biggest price changes)
      const sortedByChange = [...itemAnalyses].sort((a, b) =>
        Math.abs(b.priceChangePercent.toNumber()) - Math.abs(a.priceChangePercent.toNumber())
      );
      analysis.summary.topMovers = sortedByChange.slice(0, 5)
        .map(item => ({
          id: item.itemId,
          name: item.itemName,
          change: item.priceChangePercent
        }));

      analysis.summary.totalVolume = itemAnalyses.reduce((sum, item) => sum.add(item.totalVolume), new Decimal(0));
    }

    // Cache the result
    this.analysisCache.set(cacheKey, {
      data: analysis,
      timestamp: Date.now()
    });

    return analysis;
  }

  /**
   * Analyze individual item performance
   */
  async analyzeItemPerformance(itemId, regionId = 'global', timeRange = 7) {
    const startDate = new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000);

    // Get price history
    const priceHistory = await this.db('market_prices')
      .where('item_id', itemId)
      .where('region_id', regionId)
      .where('created_at', '>=', startDate)
      .orderBy('created_at', 'asc')
      .select('price', 'created_at');

    // Get transaction data
    const transactions = await this.db('market_transactions')
      .where('item_id', itemId)
      .where('region_id', regionId)
      .where('created_at', '>=', startDate)
      .select('quantity', 'price', 'transaction_type', 'created_at');

    const item = await this.db('items').where('id', itemId).first();

    let analysis = {
      itemId,
      itemName: item?.name || 'Unknown',
      priceHistory: priceHistory.map(p => ({ price: new Decimal(p.price), timestamp: p.created_at })),
      transactions: transactions.map(t => ({
        quantity: t.quantity,
        price: new Decimal(t.price),
        type: t.transaction_type,
        timestamp: t.created_at
      }))
    };

    // Calculate price change
    if (priceHistory.length >= 2) {
      const startPrice = new Decimal(priceHistory[0].price);
      const endPrice = new Decimal(priceHistory[priceHistory.length - 1].price);
      analysis.priceChangePercent = endPrice.sub(startPrice).div(startPrice).mul(100);
      analysis.startPrice = startPrice;
      analysis.endPrice = endPrice;
    } else {
      analysis.priceChangePercent = new Decimal(0);
      analysis.startPrice = new Decimal(0);
      analysis.endPrice = new Decimal(0);
    }

    // Calculate volume and liquidity
    analysis.totalVolume = transactions.reduce((sum, tx) =>
      sum.add(tx.price.mul(tx.quantity)), new Decimal(0)
    );
    analysis.totalQuantity = transactions.reduce((sum, tx) => sum + tx.quantity, 0);
    analysis.transactionCount = transactions.length;

    // Calculate average price
    if (analysis.totalQuantity > 0) {
      analysis.avgPrice = analysis.totalVolume.div(analysis.totalQuantity);
    } else {
      analysis.avgPrice = new Decimal(0);
    }

    // Calculate price volatility
    if (priceHistory.length > 1) {
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

      analysis.volatility = Math.sqrt(variance.toNumber());
    } else {
      analysis.volatility = 0;
    }

    // Calculate liquidity score (transactions per day)
    analysis.liquidityScore = analysis.transactionCount / timeRange;

    // Identify support and resistance levels
    analysis.supportLevels = await this.findSupportLevels(itemId, regionId, timeRange);
    analysis.resistanceLevels = await this.findResistanceLevels(itemId, regionId, timeRange);

    return analysis;
  }

  /**
   * Find support levels (price floors)
   */
  async findSupportLevels(itemId, regionId, timeRange) {
    const transactions = await this.db('market_transactions')
      .where('item_id', itemId)
      .where('region_id', regionId)
      .where('created_at', '>', new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000))
      .where('transaction_type', 'sale')
      .orderBy('price', 'asc')
      .select('price', 'quantity');

    if (transactions.length < 5) return [];

    // Group prices into bins and find volume concentrations
    const priceBins = {};
    const binSize = 50; // Configurable bin size

    transactions.forEach(tx => {
      const bin = Math.floor(tx.price / binSize) * binSize;
      priceBins[bin] = (priceBins[bin] || 0) + tx.quantity;
    });

    // Find levels with high volume (potential support)
    const supportLevels = Object.entries(priceBins)
      .map(([price, volume]) => ({ price: parseFloat(price), volume }))
      .sort((a, b) => b.volume - a.volume)
      .slice(0, 3);

    return supportLevels;
  }

  /**
   * Find resistance levels (price ceilings)
   */
  async findResistanceLevels(itemId, regionId, timeRange) {
    const listings = await this.db('market_listings')
      .where('item_id', itemId)
      .where('region_id', regionId)
      .where('status', 'active')
      .where('created_at', '>', new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000))
      .orderBy('price', 'desc')
      .select('price', 'quantity');

    if (listings.length < 5) return [];

    // Similar to support levels but for sell orders
    const priceBins = {};
    const binSize = 50;

    listings.forEach(listing => {
      const bin = Math.floor(listing.price / binSize) * binSize;
      priceBins[bin] = (priceBins[bin] || 0) + listing.quantity;
    });

    const resistanceLevels = Object.entries(priceBins)
      .map(([price, volume]) => ({ price: parseFloat(price), volume }))
      .sort((a, b) => b.volume - a.volume)
      .slice(0, 3);

    return resistanceLevels;
  }

  /**
   * Generate investment recommendations
   */
  async generateInvestmentRecommendations(regionId = 'global', riskTolerance = 'medium') {
    const recommendations = {
      region: regionId,
      riskTolerance,
      timestamp: new Date(),
      recommendations: []
    };

    // Get all items with sufficient trading data
    const items = await this.db('items')
      .join('market_transactions', 'items.id', 'market_transactions.item_id')
      .where('market_transactions.region_id', regionId)
      .where('market_transactions.created_at', '>', new Date(Date.now() - 30 * 24 * 60 * 60 * 1000))
      .groupBy('items.id')
      .havingRaw('COUNT(market_transactions.id) > 10')
      .select('items.id', 'items.name', 'items.category_id', 'items.rarity')
      .distinct();

    for (const item of items) {
      const analysis = await this.analyzeItemPerformance(item.id, regionId, 30);
      const score = this.calculateInvestmentScore(analysis, riskTolerance);

      if (score.totalScore > 60) { // Only include items with decent scores
        recommendations.recommendations.push({
          id: item.id,
          name: item.name,
          category: item.category_id,
          rarity: item.rarity,
          score: score,
          currentPrice: analysis.endPrice,
          predictedPrice: await this.predictShortTermPrice(item.id, regionId),
          reasoning: score.reasoning
        });
      }
    }

    // Sort by total score
    recommendations.recommendations.sort((a, b) => b.score.totalScore - a.score.totalScore);

    return recommendations;
  }

  /**
   * Calculate investment score for an item
   */
  calculateInvestmentScore(analysis, riskTolerance) {
    let score = {
      totalScore: 0,
      momentum: 0,
      volume: 0,
      volatility: 0,
      liquidity: 0,
      reasoning: []
    };

    // Momentum score (price trend)
    const priceChangePercent = analysis.priceChangePercent.toNumber();
    if (priceChangePercent > 5) {
      score.momentum = Math.min(30, priceChangePercent * 2);
      score.reasoning.push('Strong positive price momentum');
    } else if (priceChangePercent < -5) {
      score.momentum = Math.max(-20, priceChangePercent);
      score.reasoning.push('Negative price trend');
    } else {
      score.momentum = 10;
      score.reasoning.push('Stable price action');
    }

    // Volume score
    const volumeScore = Math.min(25, Math.log10(analysis.totalVolume.toNumber() + 1) * 5);
    score.volume = volumeScore;
    if (volumeScore > 15) {
      score.reasoning.push('High trading volume');
    }

    // Volatility score (adjusted by risk tolerance)
    let volatilityScore;
    if (riskTolerance === 'high') {
      volatilityScore = Math.min(20, analysis.volatility * 100);
      score.reasoning.push('High volatility - opportunity for gains');
    } else if (riskTolerance === 'low') {
      volatilityScore = Math.max(-15, -analysis.volatility * 100);
      score.reasoning.push('Low volatility - stable investment');
    } else {
      volatilityScore = Math.max(-10, Math.min(10, (0.05 - analysis.volatility) * 100));
      score.reasoning.push('Moderate volatility');
    }
    score.volatility = volatilityScore;

    // Liquidity score
    const liquidityScore = Math.min(25, analysis.liquidityScore * 5);
    score.liquidity = liquidityScore;
    if (liquidityScore > 15) {
      score.reasoning.push('High liquidity - easy to trade');
    }

    // Calculate total score
    score.totalScore = Math.max(0, Math.min(100,
      score.momentum + score.volume + score.volatility + score.liquidity + 20
    ));

    return score;
  }

  /**
   * Predict short-term price movement
   */
  async predictShortTermPrice(itemId, regionId, hoursAhead = 24) {
    // This is a simplified prediction model
    // In production, you'd use more sophisticated ML models

    const currentPrice = await this.getCurrentPrice(itemId, regionId);
    const analysis = await this.analyzeItemPerformance(itemId, regionId, 7);

    // Use recent trend and momentum
    const momentum = analysis.priceChangePercent.div(7); // Daily change
    const volatilityAdjustment = Decimal(analysis.volatility).mul(Decimal.random().sub(0.5));

    const predictedPrice = currentPrice
      .mul(Decimal(1).add(momentum.div(100).mul(hoursAhead / 24)))
      .mul(Decimal(1).add(volatilityAdjustment));

    return {
      currentPrice,
      predictedPrice,
      confidence: Math.max(0.1, 1 - analysis.volatility), // Lower volatility = higher confidence
      timeHorizon: hoursAhead
    };
  }

  /**
   * Get current market price
   */
  async getCurrentPrice(itemId, regionId) {
    const latestPrice = await this.db('market_prices')
      .where('item_id', itemId)
      .where('region_id', regionId)
      .orderBy('created_at', 'desc')
      .first();

    return latestPrice ? new Decimal(latestPrice.price) : new Decimal(0);
  }

  /**
   * Detect market anomalies
   */
  async detectMarketAnomalies(regionId = 'global') {
    const anomalies = [];

    // Get recent transactions for analysis
    const recentTransactions = await this.db('market_transactions')
      .where('region_id', regionId)
      .where('created_at', '>', new Date(Date.now() - 24 * 60 * 60 * 1000))
      .select('item_id', 'quantity', 'price', 'player_id');

    // Group by item and player
    const itemStats = {};
    const playerStats = {};

    recentTransactions.forEach(tx => {
      // Item statistics
      if (!itemStats[tx.item_id]) {
        itemStats[tx.item_id] = {
          totalVolume: new Decimal(0),
          totalQuantity: 0,
          transactionCount: 0,
          avgPrice: new Decimal(0),
          priceHistory: []
        };
      }

      itemStats[tx.item_id].totalVolume = itemStats[tx.item_id].totalVolume.add(
        new Decimal(tx.price).mul(tx.quantity)
      );
      itemStats[tx.item_id].totalQuantity += tx.quantity;
      itemStats[tx.item_id].transactionCount++;
      itemStats[tx.item_id].priceHistory.push(new Decimal(tx.price));

      // Player statistics
      if (!playerStats[tx.player_id]) {
        playerStats[tx.player_id] = {
          totalSpent: new Decimal(0),
          transactionCount: 0,
          items: new Set()
        };
      }

      playerStats[tx.player_id].totalSpent = playerStats[tx.player_id].totalSpent.add(
        new Decimal(tx.price).mul(tx.quantity)
      );
      playerStats[tx.player_id].transactionCount++;
      playerStats[tx.player_id].items.add(tx.item_id);
    });

    // Detect price anomalies
    for (const [itemId, stats] of Object.entries(itemStats)) {
      if (stats.priceHistory.length > 5) {
        const avgPrice = stats.totalVolume.div(stats.totalQuantity);
        const priceVariance = this.calculatePriceVariance(stats.priceHistory);

        // Flag if variance is too high (potential manipulation)
        if (priceVariance > 0.3) {
          anomalies.push({
            type: 'price_volatility',
            itemId,
            severity: 'high',
            description: `Unusual price volatility detected for item ${itemId}`,
            data: {
              avgPrice: avgPrice.toString(),
              variance: priceVariance,
              transactionCount: stats.transactionCount
            }
          });
        }
      }
    }

    // Detect player behavior anomalies
    for (const [playerId, stats] of Object.entries(playerStats)) {
      // Check for unusual high volume trading
      if (stats.totalSpent.greaterThan(100000)) {
        anomalies.push({
          type: 'high_volume_trading',
          playerId,
          severity: 'medium',
          description: `Player ${playerId} has unusually high trading volume`,
          data: {
            totalSpent: stats.totalSpent.toString(),
            transactionCount: stats.transactionCount,
            uniqueItems: stats.items.size
          }
        });
      }

      // Check for potential wash trading
      if (stats.transactionCount > 50 && stats.items.size < 5) {
        anomalies.push({
          type: 'potential_wash_trading',
          playerId,
          severity: 'high',
          description: `Player ${playerId} shows potential wash trading patterns`,
          data: {
            transactionCount: stats.transactionCount,
            uniqueItems: stats.items.size,
            avgTransactionsPerItem: stats.transactionCount / stats.items.size
          }
        });
      }
    }

    return anomalies;
  }

  /**
   * Calculate price variance
   */
  calculatePriceVariance(prices) {
    if (prices.length < 2) return 0;

    const mean = prices.reduce((sum, price) => sum.add(price), new Decimal(0))
      .div(prices.length);

    const variance = prices.reduce((sum, price) => {
      const diff = price.sub(mean);
      return sum.add(diff.mul(diff));
    }, new Decimal(0)).div(prices.length);

    return Math.sqrt(variance.toNumber()) / mean.toNumber();
  }

  /**
   * Generate market report
   */
  async generateMarketReport(regionId = 'global', timeRange = 7) {
    const report = {
      region: regionId,
      timeRange,
      generatedAt: new Date(),
      overview: {},
      categories: [],
      topItems: [],
      anomalies: [],
      predictions: []
    };

    // Market overview
    const overview = await this.getMarketOverview(regionId, timeRange);
    report.overview = overview;

    // Category analysis
    const categories = await this.db('item_categories').select('id', 'name');
    for (const category of categories) {
      const categoryAnalysis = await this.analyzeCategoryTrends(category.id, regionId, timeRange);
      report.categories.push({
        id: category.id,
        name: category.name,
        ...categoryAnalysis.summary
      });
    }

    // Top performing items
    const topItems = await this.getTopPerformingItems(regionId, timeRange);
    report.topItems = topItems;

    // Market anomalies
    const anomalies = await this.detectMarketAnomalies(regionId);
    report.anomalies = anomalies;

    // Predictions for top items
    for (const item of topItems.slice(0, 5)) {
      const prediction = await this.predictShortTermPrice(item.id, regionId);
      report.predictions.push({
        itemId: item.id,
        itemName: item.name,
        ...prediction
      });
    }

    return report;
  }

  /**
   * Get market overview statistics
   */
  async getMarketOverview(regionId, timeRange) {
    const startDate = new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000);

    const stats = await this.db('market_transactions')
      .where('region_id', regionId)
      .where('created_at', '>=', startDate)
      .select(
        this.db.raw('COUNT(*) as transaction_count'),
        this.db.raw('SUM(quantity) as total_quantity'),
        this.db.raw('SUM(total_price) as total_volume'),
        this.db.raw('AVG(price) as avg_price')
      )
      .first();

    const activeListings = await this.db('market_listings')
      .where('region_id', regionId)
      .where('status', 'active')
      .count('* as count')
      .first();

    const uniqueItems = await this.db('market_transactions')
      .where('region_id', regionId)
      .where('created_at', '>=', startDate)
      .distinct('item_id')
      .count('* as count')
      .first();

    return {
      totalTransactions: parseInt(stats.transaction_count) || 0,
      totalVolume: stats.total_volume || new Decimal(0),
      totalQuantity: parseInt(stats.total_quantity) || 0,
      averagePrice: stats.avg_price || new Decimal(0),
      activeListings: parseInt(activeListings.count) || 0,
      uniqueItemsTraded: parseInt(uniqueItems.count) || 0
    };
  }

  /**
   * Get top performing items
   */
  async getTopPerformingItems(regionId, timeRange) {
    const startDate = new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000);

    return await this.db('items')
      .join('market_transactions', 'items.id', 'market_transactions.item_id')
      .where('market_transactions.region_id', regionId)
      .where('market_transactions.created_at', '>=', startDate)
      .groupBy('items.id', 'items.name', 'items.rarity')
      .select(
        'items.id',
        'items.name',
        'items.rarity',
        this.db.raw('SUM(market_transactions.quantity) as total_quantity'),
        this.db.raw('SUM(market_transactions.total_price) as total_volume'),
        this.db.raw('COUNT(*) as transaction_count')
      )
      .orderBy('total_volume', 'desc')
      .limit(20);
  }
}

module.exports = MarketAnalyzer;