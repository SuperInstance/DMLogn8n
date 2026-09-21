const Decimal = require('decimal.js');
const _ = require('lodash');
const EventEmitter = require('events');

class MarketInsights extends EventEmitter {
  constructor(knex, redis, marketAnalyzer, economicEngine) {
    super();
    this.db = knex;
    this.redis = redis;
    this.marketAnalyzer = marketAnalyzer;
    this.economicEngine = economicEngine;
    this.insightCache = new Map();
    this.alertSubscriptions = new Map();
  }

  /**
   * Generate comprehensive market insights
   */
  async generateMarketInsights(regionId = 'global', timeRange = 7) {
    const cacheKey = `insights:${regionId}:${timeRange}`;

    if (this.insightCache.has(cacheKey)) {
      const cached = this.insightCache.get(cacheKey);
      if (Date.now() - cached.timestamp < 1800000) { // 30 minutes cache
        return cached.data;
      }
    }

    const insights = {
      region: regionId,
      timeRange,
      generatedAt: new Date(),
      overview: await this.generateOverview(regionId, timeRange),
      trends: await this.generateTrendAnalysis(regionId, timeRange),
      opportunities: await this.identifyOpportunities(regionId, timeRange),
      risks: await this.identifyRisks(regionId, timeRange),
      predictions: await this.generatePredictions(regionId),
      recommendations: await this.generateRecommendations(regionId, timeRange),
      marketHealth: await this.assessMarketHealth(regionId, timeRange)
    };

    // Cache the result
    this.insightCache.set(cacheKey, {
      data: insights,
      timestamp: Date.now()
    });

    return insights;
  }

  /**
   * Generate market overview
   */
  async generateOverview(regionId, timeRange) {
    const marketplaceStats = await this.marketAnalyzer.getMarketOverview(regionId, timeRange);
    const auctionStats = await this.getAuctionOverview(regionId, timeRange);

    // Calculate market sentiment
    const sentiment = await this.calculateMarketSentiment(regionId, timeRange);

    // Get top performing items
    const topItems = await this.getTopPerformingItems(regionId, timeRange);

    // Get market activity breakdown
    const activityBreakdown = await this.getActivityBreakdown(regionId, timeRange);

    return {
      volume: marketplaceStats.totalVolume,
      transactions: marketplaceStats.totalTransactions,
      uniqueItems: marketplaceStats.uniqueItemsTraded,
      activeListings: marketplaceStats.activeListings,
      auctionActivity: auctionStats,
      sentiment,
      topItems: topItems.slice(0, 10),
      activityBreakdown
    };
  }

  /**
   * Generate trend analysis
   */
  async generateTrendAnalysis(regionId, timeRange) {
    const trends = {
      priceTrends: await this.analyzePriceTrends(regionId, timeRange),
      volumeTrends: await this.analyzeVolumeTrends(regionId, timeRange),
      categoryTrends: await this.analyzeCategoryTrends(regionId, timeRange),
      regionalTrends: await this.analyzeRegionalTrends(timeRange),
      seasonalPatterns: await this.identifySeasonalPatterns(regionId),
      emergingTrends: await this.identifyEmergingTrends(regionId, timeRange)
    };

    return trends;
  }

  /**
   * Identify investment opportunities
   */
  async identifyOpportunities(regionId, timeRange) {
    const opportunities = [];

    // Undervalued items
    const undervaluedItems = await this.findUndervaluedItems(regionId, timeRange);
    opportunities.push(...undervaluedItems.map(item => ({
      type: 'undervalued',
      ...item,
      reasoning: `Item ${item.itemName} appears undervalued based on historical trends and current market conditions`
    })));

    // High growth potential
    const growthItems = await this.findHighGrowthItems(regionId, timeRange);
    opportunities.push(...growthItems.map(item => ({
      type: 'growth_potential',
      ...item,
      reasoning: `Strong growth indicators for ${item.itemName} with increasing demand`
    })));

    // Arbitrage opportunities
    const arbitrageOpportunities = await this.findArbitrageOpportunities(regionId);
    opportunities.push(...arbitrageOpportunities);

    // Bulk trading opportunities
    const bulkOpportunities = await this.findBulkTradingOpportunities(regionId, timeRange);
    opportunities.push(...bulkOpportunities);

    return opportunities.sort((a, b) => b.score - a.score).slice(0, 20);
  }

  /**
   * Identify market risks
   */
  async identifyRisks(regionId, timeRange) {
    const risks = [];

    // Price manipulation risks
    const manipulationRisks = await this.detectManipulationRisks(regionId, timeRange);
    risks.push(...manipulationRisks);

    // Market volatility risks
    const volatilityRisks = await this.identifyVolatilityRisks(regionId, timeRange);
    risks.push(...volatilityRisks);

    // Supply chain risks
    const supplyRisks = await this.identifySupplyRisks(regionId, timeRange);
    risks.push(...supplyRisks);

    // Economic bubble risks
    const bubbleRisks = await this.identifyBubbleRisks(regionId, timeRange);
    risks.push(...bubbleRisks);

    return risks.sort((a, b) => b.severityScore - a.severityScore).slice(0, 10);
  }

  /**
   * Generate market predictions
   */
  async generatePredictions(regionId) {
    const predictions = {
      shortTerm: await this.generateShortTermPredictions(regionId, 24), // 24 hours
      mediumTerm: await this.generateShortTermPredictions(regionId, 168), // 1 week
      longTerm: await this.generateLongTermPredictions(regionId, 720), // 1 month
      categoryPredictions: await this.generateCategoryPredictions(regionId),
      marketSentimentPrediction: await this.predictMarketSentiment(regionId)
    };

    return predictions;
  }

  /**
   * Generate actionable recommendations
   */
  async generateRecommendations(regionId, timeRange) {
    const recommendations = [];

    // Buy recommendations
    const buyRecommendations = await this.generateBuyRecommendations(regionId, timeRange);
    recommendations.push(...buyRecommendations);

    // Sell recommendations
    const sellRecommendations = await this.generateSellRecommendations(regionId, timeRange);
    recommendations.push(...sellRecommendations);

    // Hold recommendations
    const holdRecommendations = await this.generateHoldRecommendations(regionId, timeRange);
    recommendations.push(...holdRecommendations);

    // Portfolio recommendations
    const portfolioRecommendations = await this.generatePortfolioRecommendations(regionId, timeRange);
    recommendations.push(...portfolioRecommendations);

    return recommendations;
  }

  /**
   * Assess overall market health
   */
  async assessMarketHealth(regionId, timeRange) {
    const healthMetrics = {
      liquidity: await this.assessLiquidity(regionId, timeRange),
      volatility: await this.assessVolatility(regionId, timeRange),
      efficiency: await this.assessMarketEfficiency(regionId, timeRange),
      participation: await this.assessParticipation(regionId, timeRange),
      stability: await this.assessStability(regionId, timeRange)
    };

    // Calculate overall health score
    const overallScore = Object.values(healthMetrics).reduce((sum, metric) => sum + metric.score, 0) / Object.keys(healthMetrics).length;

    return {
      overallScore,
      grade: this.getHealthGrade(overallScore),
      metrics: healthMetrics,
      timestamp: new Date()
    };
  }

  /**
   * Find undervalued items
   */
  async findUndervaluedItems(regionId, timeRange) {
    const items = await this.db('items')
      .join('market_prices', 'items.id', 'market_prices.item_id')
      .where('market_prices.region_id', regionId)
      .where('market_prices.created_at', '>', new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000))
      .distinct('items.id')
      .select('items.*');

    const undervaluedItems = [];

    for (const item of items) {
      const analysis = await this.marketAnalyzer.analyzeItemPerformance(item.id, regionId, timeRange);
      const prediction = await this.economicEngine.predictPrice(item.id, regionId, 168);

      if (prediction && prediction.greaterThan(analysis.endPrice.mul(1.15))) { // 15% potential gain
        undervaluedItems.push({
          itemId: item.id,
          itemName: item.name,
          currentPrice: analysis.endPrice,
          predictedPrice: prediction,
          potentialGain: prediction.sub(analysis.endPrice).div(analysis.endPrice).mul(100),
          confidence: this.calculatePredictionConfidence(analysis),
          score: this.calculateOpportunityScore(analysis, prediction)
        });
      }
    }

    return undervaluedItems.sort((a, b) => b.score - a.score);
  }

  /**
   * Find high growth items
   */
  async findHighGrowthItems(regionId, timeRange) {
    const recentGrowth = await this.db('market_transactions')
      .join('items', 'market_transactions.item_id', 'items.id')
      .where('market_transactions.region_id', regionId)
      .where('market_transactions.created_at', '>', new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000))
      .groupBy('items.id', 'items.name')
      .select(
        'items.id',
        'items.name',
        this.db.raw('COUNT(*) as transaction_count'),
        this.db.raw('SUM(quantity) as total_quantity'),
        this.db.raw('SUM(total_price) as total_volume'),
        this.db.raw('AVG(price) as avg_price')
      )
      .orderBy('total_volume', 'desc')
      .limit(50);

    const highGrowthItems = [];

    for (const item of recentGrowth) {
      const analysis = await this.marketAnalyzer.analyzeItemPerformance(item.id, regionId, timeRange);
      const demandGrowth = await this.calculateDemandGrowth(item.id, regionId, timeRange);

      if (demandGrowth > 0.2 && analysis.priceChangePercent.greaterThan(0)) { // 20% demand growth
        highGrowthItems.push({
          itemId: item.id,
          itemName: item.name,
          demandGrowth,
          priceChangePercent: analysis.priceChangePercent,
          volume: new Decimal(item.total_volume),
          score: this.calculateGrowthScore(demandGrowth, analysis.priceChangePercent.toNumber())
        });
      }
    }

    return highGrowthItems.sort((a, b) => b.score - a.score);
  }

  /**
   * Find arbitrage opportunities
   */
  async findArbitrageOpportunities(regionId) {
    const opportunities = [];

    // Get same item in different regions
    const items = await this.db('market_prices')
      .join('items', 'market_prices.item_id', 'items.id')
      .where('market_prices.created_at', '>', new Date(Date.now() - 24 * 60 * 60 * 1000))
      .groupBy('items.id', 'items.name')
      .havingRaw('COUNT(DISTINCT market_prices.region_id) > 1')
      .select('items.id', 'items.name');

    for (const item of items) {
      const regionalPrices = await this.db('market_prices')
        .where('item_id', item.id)
        .where('created_at', '>', new Date(Date.now() - 24 * 60 * 60 * 1000))
        .orderBy('price', 'desc')
        .select('region_id', 'price');

      if (regionalPrices.length >= 2) {
        const highestPrice = new Decimal(regionalPrices[0].price);
        const lowestPrice = new Decimal(regionalPrices[regionalPrices.length - 1].price);
        const profitMargin = highestPrice.sub(lowestPrice).div(lowestPrice).mul(100);

        if (profitMargin.greaterThan(10)) { // 10% profit margin
          opportunities.push({
            type: 'regional_arbitrage',
            itemId: item.id,
            itemName: item.name,
            buyRegion: regionalPrices[regionalPrices.length - 1].region_id,
            sellRegion: regionalPrices[0].region_id,
            buyPrice: lowestPrice,
            sellPrice: highestPrice,
            profitMargin,
            score: profitMargin.toNumber()
          });
        }
      }
    }

    return opportunities.sort((a, b) => b.score - a.score).slice(0, 10);
  }

  /**
   * Create price alerts
   */
  async createPriceAlert(alertData) {
    const {
      playerId,
      itemId,
      regionId = 'global',
      alertType, // 'above', 'below', 'percentage_change'
      threshold,
      duration = 7 * 24 * 60 * 60 * 1000, // 7 days
      notificationMethod = 'in_game' // 'in_game', 'email', 'push'
    } = alertData;

    const alertId = uuidv4();
    const alert = {
      id: alertId,
      player_id: playerId,
      item_id: itemId,
      region_id: regionId,
      alert_type: alertType,
      threshold: threshold.toString(),
      status: 'active',
      created_at: new Date(),
      expires_at: new Date(Date.now() + duration),
      notification_method: notificationMethod
    };

    await this.db('price_alerts').insert(alert);

    // Store in memory for quick access
    if (!this.alertSubscriptions.has(itemId)) {
      this.alertSubscriptions.set(itemId, new Map());
    }
    this.alertSubscriptions.get(itemId).set(alertId, alert);

    this.emit('alertCreated', { alert });

    return alert;
  }

  /**
   * Check and trigger price alerts
   */
  async checkPriceAlerts(itemId, regionId, currentPrice) {
    const alerts = this.alertSubscriptions.get(itemId);
    if (!alerts) return;

    for (const [alertId, alert] of alerts) {
      if (alert.region_id !== regionId || alert.status !== 'active') continue;

      const threshold = new Decimal(alert.threshold);
      let triggered = false;

      switch (alert.alert_type) {
        case 'above':
          triggered = currentPrice.greaterThan(threshold);
          break;
        case 'below':
          triggered = currentPrice.lessThan(threshold);
          break;
        case 'percentage_change':
          // Would need historical price to calculate this
          break;
      }

      if (triggered) {
        await this.triggerAlert(alert, currentPrice);
      }
    }
  }

  /**
   * Trigger a price alert
   */
  async triggerAlert(alert, currentPrice) {
    // Update alert status
    await this.db('price_alerts')
      .where('id', alert.id)
      .update({
        status: 'triggered',
        triggered_at: new Date(),
        triggered_price: currentPrice.toString()
      });

    // Remove from active subscriptions
    const itemAlerts = this.alertSubscriptions.get(alert.item_id);
    if (itemAlerts) {
      itemAlerts.delete(alert.id);
    }

    // Send notification
    await this.sendAlertNotification(alert, currentPrice);

    this.emit('alertTriggered', {
      alertId: alert.id,
      playerId: alert.player_id,
      itemId: alert.item_id,
      currentPrice: currentPrice.toString()
    });
  }

  /**
   * Generate player portfolio insights
   */
  async generatePortfolioInsights(playerId, regionId = 'global') {
    const portfolio = await this.getPlayerPortfolio(playerId, regionId);
    const insights = {
      portfolio,
      valuation: await this.calculatePortfolioValue(portfolio, regionId),
      performance: await this.calculatePortfolioPerformance(portfolio, regionId),
      recommendations: await this.generatePortfolioRecommendations(playerId, regionId),
      riskAssessment: await this.assessPortfolioRisk(portfolio, regionId),
      diversification: await this.analyzeDiversification(portfolio)
    };

    return insights;
  }

  /**
   * Get player portfolio
   */
  async getPlayerPortfolio(playerId, regionId) {
    // This would integrate with the inventory system
    // For now, return a mock structure
    return {
      items: [],
      currency: new Decimal(0),
      lastUpdated: new Date()
    };
  }

  /**
   * Calculate portfolio value
   */
  async calculatePortfolioValue(portfolio, regionId) {
    let totalValue = new Decimal(0);
    const itemValues = [];

    for (const item of portfolio.items) {
      const currentValue = await this.economicEngine.calculateDynamicPrice(
        item.item_id,
        regionId,
        item.quantity
      );
      totalValue = totalValue.add(currentValue);
      itemValues.push({
        itemId: item.item_id,
        quantity: item.quantity,
        value: currentValue
      });
    }

    return {
      totalValue,
      itemValues,
      currency: portfolio.currency,
      netWorth: totalValue.add(portfolio.currency)
    };
  }

  /**
   * Generate market sentiment analysis
   */
  async calculateMarketSentiment(regionId, timeRange) {
    // Get recent transaction data
    const transactions = await this.db('market_transactions')
      .where('region_id', regionId)
      .where('created_at', '>', new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000))
      .select('price', 'quantity', 'created_at');

    if (transactions.length === 0) {
      return { sentiment: 'neutral', score: 0, confidence: 0 };
    }

    // Calculate price momentum
    const prices = transactions.map(t => new Decimal(t.price));
    const priceMomentum = this.calculateMomentum(prices);

    // Calculate volume trend
    const volumeTrend = this.calculateVolumeTrend(transactions);

    // Calculate transaction frequency
    const frequency = transactions.length / timeRange;

    // Combine into sentiment score
    let sentimentScore = (priceMomentum * 0.4) + (volumeTrend * 0.3) + (Math.min(frequency / 10, 1) * 0.3);

    // Determine sentiment category
    let sentiment;
    if (sentimentScore > 0.2) sentiment = 'bullish';
    else if (sentimentScore < -0.2) sentiment = 'bearish';
    else sentiment = 'neutral';

    // Calculate confidence based on data volume
    const confidence = Math.min(transactions.length / 100, 1);

    return {
      sentiment,
      score: sentimentScore,
      confidence,
      factors: {
        priceMomentum,
        volumeTrend,
        transactionFrequency: frequency
      }
    };
  }

  /**
   * Helper methods
   */
  calculateMomentum(prices) {
    if (prices.length < 2) return 0;

    const recent = prices.slice(-Math.min(10, prices.length));
    const older = prices.slice(0, Math.min(10, prices.length));

    const recentAvg = recent.reduce((sum, p) => sum.add(p), new Decimal(0)).div(recent.length);
    const olderAvg = older.reduce((sum, p) => sum.add(p), new Decimal(0)).div(older.length);

    return recentAvg.sub(olderAvg).div(olderAvg).toNumber();
  }

  calculateVolumeTrend(transactions) {
    if (transactions.length < 2) return 0;

    const midpoint = Math.floor(transactions.length / 2);
    const firstHalf = transactions.slice(0, midpoint);
    const secondHalf = transactions.slice(midpoint);

    const firstHalfVolume = firstHalf.reduce((sum, t) => sum + t.quantity, 0);
    const secondHalfVolume = secondHalf.reduce((sum, t) => sum + t.quantity, 0);

    if (firstHalfVolume === 0) return 0;

    return (secondHalfVolume - firstHalfVolume) / firstHalfVolume;
  }

  calculateOpportunityScore(analysis, prediction) {
    const potentialGain = prediction.sub(analysis.endPrice).div(analysis.endPrice).toNumber();
    const liquidityScore = Math.min(analysis.liquidityScore / 10, 1);
    const volatilityPenalty = Math.max(0, 1 - analysis.volatility * 2);

    return (potentialGain * 0.5) + (liquidityScore * 0.3) + (volatilityPenalty * 0.2);
  }

  calculateGrowthScore(demandGrowth, priceChange) {
    return (demandGrowth * 0.6) + (Math.min(priceChange / 20, 1) * 0.4);
  }

  calculatePredictionConfidence(analysis) {
    // Higher confidence with more data points and lower volatility
    const dataPoints = analysis.transactions.length;
    const volatility = analysis.volatility;

    return Math.min(dataPoints / 50, 1) * Math.max(0, 1 - volatility * 2);
  }

  getHealthGrade(score) {
    if (score >= 90) return 'A+';
    if (score >= 80) return 'A';
    if (score >= 70) return 'B+';
    if (score >= 60) return 'B';
    if (score >= 50) return 'C+';
    if (score >= 40) return 'C';
    if (score >= 30) return 'D';
    return 'F';
  }

  async sendAlertNotification(alert, currentPrice) {
    // Implementation would send notifications based on method
    console.log(`Alert triggered for player ${alert.player_id}: ${alert.item_id} price is ${currentPrice.toString()}`);
  }

  async getAuctionOverview(regionId, timeRange) {
    // Get auction statistics
    const auctionStats = await this.db('auctions')
      .where('region_id', regionId)
      .where('created_at', '>', new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000))
      .select(
        this.db.raw('COUNT(*) as total_auctions'),
        this.db.raw('SUM(CASE WHEN status = \'sold\' THEN 1 ELSE 0 END) as sold_auctions'),
        this.db.raw('SUM(current_bid) as total_volume')
      )
      .first();

    return {
      totalAuctions: parseInt(auctionStats.total_auctions) || 0,
      soldAuctions: parseInt(auctionStats.sold_auctions) || 0,
      successRate: auctionStats.total_auctions > 0
        ? (auctionStats.sold_auctions / auctionStats.total_auctions) * 100
        : 0,
      totalVolume: auctionStats.total_volume || new Decimal(0)
    };
  }

  async getTopPerformingItems(regionId, timeRange) {
    return await this.db('market_transactions')
      .join('items', 'market_transactions.item_id', 'items.id')
      .where('market_transactions.region_id', regionId)
      .where('market_transactions.created_at', '>', new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000))
      .groupBy('items.id', 'items.name')
      .select(
        'items.id',
        'items.name',
        this.db.raw('SUM(market_transactions.total_price) as total_volume'),
        this.db.raw('COUNT(*) as transaction_count')
      )
      .orderBy('total_volume', 'desc')
      .limit(20);
  }

  async getActivityBreakdown(regionId, timeRange) {
    const breakdown = {
      marketplace: 0,
      auctions: 0,
      directTrades: 0
    };

    // Get marketplace activity
    const marketplaceActivity = await this.db('market_transactions')
      .where('region_id', regionId)
      .where('transaction_type', 'marketplace_sale')
      .where('created_at', '>', new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000))
      .count('* as count')
      .first();

    breakdown.marketplace = parseInt(marketplaceActivity.count) || 0;

    // Get auction activity
    const auctionActivity = await this.db('market_transactions')
      .where('region_id', regionId)
      .where('transaction_type', 'auction_sale')
      .where('created_at', '>', new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000))
      .count('* as count')
      .first();

    breakdown.auctions = parseInt(auctionActivity.count) || 0;

    // Get direct trade activity
    const tradeActivity = await this.db('market_transactions')
      .where('region_id', regionId)
      .where('transaction_type', 'trade')
      .where('created_at', '>', new Date(Date.now() - timeRange * 24 * 60 * 60 * 1000))
      .count('* as count')
      .first();

    breakdown.directTrades = parseInt(tradeActivity.count) || 0;

    return breakdown;
  }

  // Additional helper methods for various analyses would be implemented here
  async analyzePriceTrends(regionId, timeRange) { /* implementation */ }
  async analyzeVolumeTrends(regionId, timeRange) { /* implementation */ }
  async analyzeCategoryTrends(regionId, timeRange) { /* implementation */ }
  async analyzeRegionalTrends(timeRange) { /* implementation */ }
  async identifySeasonalPatterns(regionId) { /* implementation */ }
  async identifyEmergingTrends(regionId, timeRange) { /* implementation */ }
  async findBulkTradingOpportunities(regionId, timeRange) { /* implementation */ }
  async detectManipulationRisks(regionId, timeRange) { /* implementation */ }
  async identifyVolatilityRisks(regionId, timeRange) { /* implementation */ }
  async identifySupplyRisks(regionId, timeRange) { /* implementation */ }
  async identifyBubbleRisks(regionId, timeRange) { /* implementation */ }
  async generateShortTermPredictions(regionId, hours) { /* implementation */ }
  async generateLongTermPredictions(regionId, hours) { /* implementation */ }
  async generateCategoryPredictions(regionId) { /* implementation */ }
  async predictMarketSentiment(regionId) { /* implementation */ }
  async generateBuyRecommendations(regionId, timeRange) { /* implementation */ }
  async generateSellRecommendations(regionId, timeRange) { /* implementation */ }
  async generateHoldRecommendations(regionId, timeRange) { /* implementation */ }
  async generatePortfolioRecommendations(playerId, regionId, timeRange) { /* implementation */ }
  async assessLiquidity(regionId, timeRange) { /* implementation */ }
  async assessVolatility(regionId, timeRange) { /* implementation */ }
  async assessMarketEfficiency(regionId, timeRange) { /* implementation */ }
  async assessParticipation(regionId, timeRange) { /* implementation */ }
  async assessStability(regionId, timeRange) { /* implementation */ }
  async calculateDemandGrowth(itemId, regionId, timeRange) { /* implementation */ }
  async calculatePortfolioPerformance(portfolio, regionId) { /* implementation */ }
  async assessPortfolioRisk(portfolio, regionId) { /* implementation */ }
  async analyzeDiversification(portfolio) { /* implementation */ }
}

module.exports = MarketInsights;