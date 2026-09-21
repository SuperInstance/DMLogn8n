const winston = require('winston');

class ContentDiscoveryService {
    constructor(hybridRecommender, contentService, redisClient) {
        this.hybridRecommender = hybridRecommender;
        this.contentService = contentService;
        this.redisClient = redisClient;
        this.trendingAlgorithms = this.initializeTrendingAlgorithms();
        this.popularityMetrics = this.initializePopularityMetrics();
        this.discoveryStrategies = this.initializeDiscoveryStrategies();
        this.communityFeatures = this.initializeCommunityFeatures();
    }

    // Initialize trending algorithms
    initializeTrendingAlgorithms() {
        return {
            timeDecay: {
                name: 'Time Decay Scoring',
                description: 'Content relevance decreases over time',
                halflife: 7 * 24 * 60 * 60 * 1000, // 7 days in milliseconds
                minDecay: 0.1,
                formula: 'score * exp(-delta_time / halflife)'
            },
            velocity: {
                name: 'Velocity Tracking',
                description: 'Track rate of engagement change',
                timeWindows: [1, 24, 168], // 1 hour, 1 day, 1 week in hours
                velocityWeight: 0.3,
                baselineWeight: 0.7
            },
            momentum: {
                name: 'Momentum Calculation',
                description: 'Combines velocity with acceleration',
                lookbackPeriod: 14, // days
                momentumThreshold: 0.1,
                sustainedBoost: 1.5
            },
            socialProof: {
                name: 'Social Proof Scoring',
                description: 'Incorporates social signals',
                likeWeight: 1,
                shareWeight: 2,
                commentWeight: 3,
                ratingWeight: 4,
                diversityBonus: 1.2
            },
            seasonal: {
                name: 'Seasonal Adjustments',
                description: 'Accounts for seasonal patterns',
                monthlyMultipliers: this.getMonthlyMultipliers(),
                weeklyPatterns: this.getWeeklyPatterns(),
                holidayBoosts: this.getHolidayBoosts()
            }
        };
    }

    // Initialize popularity metrics
    initializePopularityMetrics() {
        return {
            engagement: {
                views: { weight: 1, normalization: 'log' },
                likes: { weight: 3, normalization: 'log' },
                shares: { weight: 5, normalization: 'log' },
                comments: { weight: 4, normalization: 'log' },
                downloads: { weight: 6, normalization: 'log' },
                bookmarks: { weight: 3, normalization: 'log' }
            },
            quality: {
                rating: { weight: 5, normalization: 'linear' },
                reviews: { weight: 2, normalization: 'sqrt' },
                completion: { weight: 3, normalization: 'linear' },
                retention: { weight: 4, normalization: 'linear' }
            },
            reach: {
                uniqueUsers: { weight: 2, normalization: 'log' },
                returnUsers: { weight: 3, normalization: 'log' },
                referralTraffic: { weight: 1.5, normalization: 'log' },
                searchTraffic: { weight: 2, normalization: 'log' }
            }
        };
    }

    // Initialize discovery strategies
    initializeDiscoveryStrategies() {
        return {
            personalized: {
                name: 'Personalized Discovery',
                description: 'Content tailored to user preferences',
                weights: { collaborative: 0.4, contentBased: 0.3, social: 0.2, trending: 0.1 },
                diversityFactor: 0.3,
                serendipityFactor: 0.1
            },
            trending: {
                name: 'Trending Content',
                description: 'Currently popular content',
                timeWindow: 24 * 60 * 60 * 1000, // 24 hours
                categoryBalancing: true,
                freshnessBonus: 1.2
            },
            curated: {
                name: 'Curated Collections',
                description: 'Hand-picked high-quality content',
                curatorWeights: { expert: 1.5, community: 1.2, automated: 1.0 },
                qualityThreshold: 4.0,
                updateFrequency: 'daily'
            },
            emerging: {
                name: 'Emerging Content',
                description: 'Newly discovered quality content',
                maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
                growthThreshold: 0.5,
                qualityThreshold: 3.5
            },
            seasonal: {
                name: 'Seasonal Content',
                description: 'Timely and relevant content',
                seasonalityWindow: 30 * 24 * 60 * 60 * 1000, // 30 days
                contextMatching: true,
                eventBoosts: true
            }
        };
    }

    // Initialize community features
    initializeCommunityFeatures() {
        return {
            userGenerated: {
                campaigns: { weight: 1.2, qualityThreshold: 3.5 },
                characters: { weight: 1.0, qualityThreshold: 3.0 },
                homebrew: { weight: 1.5, qualityThreshold: 4.0 },
                tools: { weight: 1.3, qualityThreshold: 3.5 }
            },
            collaborative: {
                reviews: { weight: 1.1, helpfulnessThreshold: 0.7 },
                recommendations: { weight: 1.2, endorsementThreshold: 0.8 },
                collections: { weight: 1.0, curationScore: 0.6 },
                discussions: { weight: 0.8, participationThreshold: 3 }
            },
            social: {
                shares: { weight: 1.3, viralThreshold: 100 },
                mentions: { weight: 1.1, influenceThreshold: 0.8 },
            reactions: { weight: 1.0, sentimentThreshold: 0.7 },
                follows: { weight: 1.2, creatorThreshold: 1000 }
            }
        };
    }

    // Get monthly multipliers for seasonal adjustments
    getMonthlyMultipliers() {
        return {
            1: 0.9,  // January - Post-holiday lull
            2: 0.8,  // February - Low activity
            3: 1.0,  // March - Spring awakening
            4: 1.1,  // April - Spring campaigns
            5: 1.2,  // May - Start of summer
            6: 1.3,  // June - Summer gaming
            7: 1.4,  // July - Peak summer
            8: 1.3,  // August - Late summer
            9: 1.2,  // September - Back to school
            10: 1.4, // October - Halloween season
            11: 1.3, // November - Pre-holiday
            12: 1.5  // December - Holiday season
        };
    }

    // Get weekly patterns
    getWeeklyPatterns() {
        return {
            0: 1.2, // Sunday - Gaming day
            1: 0.9, // Monday - Low activity
            2: 0.8, // Tuesday - Low activity
            3: 0.9, // Wednesday - Mid-week
            4: 1.0, // Thursday - Pre-weekend
            5: 1.3, // Friday - Start of weekend
            6: 1.4  // Saturday - Peak gaming
        };
    }

    // Get holiday boosts
    getHolidayBoosts() {
        return {
            'halloween': { month: 10, day: 31, boost: 2.0, duration: 7 },
            'christmas': { month: 12, day: 25, boost: 1.8, duration: 12 },
            'newyear': { month: 1, day: 1, boost: 1.5, duration: 3 },
            'summer_solstice': { month: 6, day: 21, boost: 1.3, duration: 7 },
            'tabletop_day': { month: 4, day: 30, boost: 2.5, duration: 3 }
        };
    }

    // Generate trending content recommendations
    async generateTrendingContent(userId, filters = {}, numRecommendations = 20) {
        try {
            const cacheKey = `trending:${JSON.stringify(filters)}:${numRecommendations}`;
            const cached = await this.redisClient.getTrendingContent(cacheKey);

            if (cached) {
                return cached;
            }

            const trendingContent = await this.calculateTrendingScores(filters);
            const personalizedTrending = await this.personalizeTrendingContent(trendingContent, userId);

            const recommendations = {
                content: personalizedTrending.slice(0, numRecommendations),
                categories: this.getTrendingCategories(personalizedTrending),
                insights: this.generateTrendingInsights(personalizedTrending),
                lastUpdated: new Date().toISOString()
            };

            // Cache for 30 minutes
            await this.redisClient.cacheTrendingContent(cacheKey, recommendations, 1800);

            return recommendations;

        } catch (error) {
            winston.error('Error generating trending content:', error);
            return { content: [], categories: [], insights: [], lastUpdated: null };
        }
    }

    // Calculate trending scores
    async calculateTrendingScores(filters = {}) {
        try {
            // Get recent content data
            const recentContent = await this.contentService.getRecentContent(filters.timeWindow || 7);

            const trendingScores = await Promise.all(
                recentContent.map(async content => {
                    const score = await this.calculateContentTrendingScore(content);
                    return {
                        contentId: content._id,
                        score: score.total,
                        breakdown: score.breakdown,
                        velocity: score.velocity,
                        momentum: score.momentum,
                        socialProof: score.socialProof,
                        content: content
                    };
                })
            );

            // Sort by trending score
            return trendingScores.sort((a, b) => b.score - a.score);

        } catch (error) {
            winston.error('Error calculating trending scores:', error);
            return [];
        }
    }

    // Calculate content trending score
    async calculateContentTrendingScore(content) {
        const now = Date.now();
        const createdAt = new Date(content.createdAt).getTime();
        const updatedAt = new Date(content.updatedAt || content.createdAt).getTime();

        const score = {
            total: 0,
            breakdown: {},
            velocity: 0,
            momentum: 0,
            socialProof: 0
        };

        // Time decay score
        const timeDecayScore = this.calculateTimeDecayScore(content, now);
        score.breakdown.timeDecay = timeDecayScore;

        // Velocity score
        const velocityScore = await this.calculateVelocityScore(content);
        score.velocity = velocityScore;
        score.breakdown.velocity = velocityScore;

        // Momentum score
        const momentumScore = await this.calculateMomentumScore(content);
        score.momentum = momentumScore;
        score.breakdown.momentum = momentumScore;

        // Social proof score
        const socialProofScore = this.calculateSocialProofScore(content);
        score.socialProof = socialProofScore;
        score.breakdown.socialProof = socialProofScore;

        // Quality score
        const qualityScore = this.calculateQualityScore(content);
        score.breakdown.quality = qualityScore;

        // Engagement score
        const engagementScore = this.calculateEngagementScore(content);
        score.breakdown.engagement = engagementScore;

        // Seasonal adjustment
        const seasonalMultiplier = this.calculateSeasonalMultiplier(now);
        score.breakdown.seasonal = seasonalMultiplier;

        // Combine scores with weights
        const weights = {
            timeDecay: 0.15,
            velocity: 0.25,
            momentum: 0.20,
            socialProof: 0.20,
            quality: 0.10,
            engagement: 0.10
        };

        score.total = Object.entries(weights).reduce((total, [component, weight]) => {
            const componentScore = score.breakdown[component] || 0;
            return total + (componentScore * weight);
        }, 0) * seasonalMultiplier;

        return score;
    }

    // Calculate time decay score
    calculateTimeDecayScore(content, now) {
        const { halflife, minDecay } = this.trendingAlgorithms.timeDecay;
        const createdAt = new Date(content.createdAt).getTime();
        const deltaTime = now - createdAt;

        const decay = Math.exp(-deltaTime / halflife);
        return Math.max(minDecay, decay);
    }

    // Calculate velocity score
    async calculateVelocityScore(content) {
        const { timeWindows, velocityWeight, baselineWeight } = this.trendingAlgorithms.velocity;

        // Get engagement metrics for different time windows
        const velocities = await Promise.all(
            timeWindows.map(async window => {
                const metrics = await this.getEngagementMetrics(content._id, window);
                return this.calculateVelocity(metrics, window);
            })
        );

        // Weight recent velocity more heavily
        const recentVelocity = velocities[0] || 0;
        const averageVelocity = velocities.reduce((sum, v) => sum + v, 0) / velocities.length;

        return (recentVelocity * velocityWeight) + (averageVelocity * baselineWeight);
    }

    // Get engagement metrics for time window
    async getEngagementMetrics(contentId, timeWindowHours) {
        // This would typically query a database or analytics system
        // For now, return simulated data
        const baseEngagement = {
            views: Math.floor(Math.random() * 1000) + 100,
            likes: Math.floor(Math.random() * 100) + 10,
            shares: Math.floor(Math.random() * 50) + 5,
            comments: Math.floor(Math.random() * 30) + 3,
            downloads: Math.floor(Math.random() * 20) + 2
        };

        // Adjust based on time window (shorter windows get less engagement)
        const windowMultiplier = Math.min(1, timeWindowHours / 24);

        return Object.entries(baseEngagement).reduce((metrics, [key, value]) => {
            metrics[key] = Math.floor(value * windowMultiplier);
            return metrics;
        }, {});
    }

    // Calculate velocity
    calculateVelocity(metrics, timeWindowHours) {
        const totalEngagement = Object.values(metrics).reduce((sum, value) => sum + value, 0);
        const velocity = totalEngagement / Math.max(1, timeWindowHours);

        // Normalize velocity (adjust based on typical engagement rates)
        return Math.min(1, velocity / 50); // Assume 50 engagements per hour is max velocity
    }

    // Calculate momentum score
    async calculateMomentumScore(content) {
        const { lookbackPeriod, momentumThreshold, sustainedBoost } = this.trendingAlgorithms.momentum;

        // Get velocity over time
        const currentVelocity = await this.calculateVelocityScore(content);
        const previousVelocity = await this.getPreviousVelocity(content._id, lookbackPeriod);

        if (!previousVelocity) return currentVelocity;

        const velocityChange = currentVelocity - previousVelocity;
        const momentum = velocityChange > momentumThreshold ? sustainedBoost : 1 + velocityChange;

        return Math.max(0, momentum);
    }

    // Get previous velocity
    async getPreviousVelocity(contentId, daysAgo) {
        // This would query historical engagement data
        // For now, return simulated previous velocity
        return Math.random() * 0.5;
    }

    // Calculate social proof score
    calculateSocialProofScore(content) {
        const { likeWeight, shareWeight, commentWeight, ratingWeight, diversityBonus } = this.trendingAlgorithms.socialProof;

        const engagement = content.engagement || {};
        const rating = content.rating || 0;

        // Calculate weighted social score
        const socialScore =
            (engagement.likes || 0) * likeWeight +
            (engagement.shares || 0) * shareWeight +
            (engagement.comments || 0) * commentWeight +
            rating * ratingWeight * 10; // Scale rating to match other metrics

        // Apply diversity bonus if content has varied engagement
        const engagementTypes = Object.values(engagement).filter(value => value > 0).length;
        const diversityMultiplier = engagementTypes > 2 ? diversityBonus : 1;

        return socialScore * diversityMultiplier;
    }

    // Calculate quality score
    calculateQualityScore(content) {
        const quality = this.popularityMetrics.quality;
        let score = 0;
        let totalWeight = 0;

        Object.entries(quality).forEach(([metric, config]) => {
            const value = content[metric] || 0;
            const normalizedValue = this.normalizeValue(value, config.normalization);
            score += normalizedValue * config.weight;
            totalWeight += config.weight;
        });

        return totalWeight > 0 ? score / totalWeight : 0;
    }

    // Calculate engagement score
    calculateEngagementScore(content) {
        const engagement = this.popularityMetrics.engagement;
        let score = 0;
        let totalWeight = 0;

        Object.entries(engagement).forEach(([metric, config]) => {
            const value = content.engagement?.[metric] || 0;
            const normalizedValue = this.normalizeValue(value, config.normalization);
            score += normalizedValue * config.weight;
            totalWeight += config.weight;
        });

        return totalWeight > 0 ? score / totalWeight : 0;
    }

    // Normalize value based on normalization method
    normalizeValue(value, method) {
        switch (method) {
            case 'log':
                return Math.log1p(value) / Math.log1p(1000); // Normalize to 0-1
            case 'sqrt':
                return Math.sqrt(value) / Math.sqrt(1000);
            case 'linear':
                return Math.min(1, value / 100); // Assume 100 is max
            default:
                return Math.min(1, value / 100);
        }
    }

    // Calculate seasonal multiplier
    calculateSeasonalMultiplier(timestamp) {
        const date = new Date(timestamp);
        const month = date.getMonth() + 1;
        const dayOfWeek = date.getDay();
        const dayOfMonth = date.getDate();

        const monthlyMultiplier = this.trendingAlgorithms.seasonal.monthlyMultipliers[month] || 1.0;
        const weeklyMultiplier = this.trendingAlgorithms.seasonal.weeklyPatterns[dayOfWeek] || 1.0;

        let holidayMultiplier = 1.0;
        Object.values(this.trendingAlgorithms.seasonal.holidayBoosts).forEach(holiday => {
            if (holiday.month === month && Math.abs(dayOfMonth - holiday.day) <= holiday.duration) {
                holidayMultiplier = Math.max(holidayMultiplier, holiday.boost);
            }
        });

        return monthlyMultiplier * weeklyMultiplier * holidayMultiplier;
    }

    // Personalize trending content
    async personalizeTrendingContent(trendingContent, userId) {
        if (!userId) return trendingContent;

        // Get user preferences
        const userPreferences = await this.getUserPreferences(userId);

        // Apply personalization weights
        const personalizedContent = trendingContent.map(item => {
            const personalizationScore = this.calculatePersonalizationScore(
                item.content, userPreferences
            );

            return {
                ...item,
                personalizedScore: item.score * (1 + personalizationScore * 0.3),
                personalizationFactors: this.getPersonalizationFactors(item.content, userPreferences)
            };
        });

        // Re-sort by personalized scores
        return personalizedContent.sort((a, b) => b.personalizedScore - a.personalizedScore);
    }

    // Get user preferences
    async getUserPreferences(userId) {
        // This would typically query user profile data
        // For now, return simulated preferences
        return {
            categories: ['adventure', 'character', 'tools'],
            contentTypes: ['spell', 'item', 'monster'],
            difficulty: 'medium',
            tags: ['beginner', 'combat', 'exploration'],
            engagement: {
                averageSessionDuration: 30, // minutes
                preferredContentLength: 'medium',
                interactionRate: 0.7
            }
        };
    }

    // Calculate personalization score
    calculatePersonalizationScore(content, userPreferences) {
        let score = 0;

        // Category matching
        if (userPreferences.categories.includes(content.category)) {
            score += 0.3;
        }

        // Content type matching
        if (userPreferences.contentTypes.includes(content.type)) {
            score += 0.3;
        }

        // Tag matching
        const matchingTags = (content.tags || []).filter(tag =>
            userPreferences.tags.includes(tag)
        ).length;
        score += Math.min(0.4, matchingTags * 0.1);

        return Math.min(1, score);
    }

    // Get personalization factors
    getPersonalizationFactors(content, userPreferences) {
        const factors = [];

        if (userPreferences.categories.includes(content.category)) {
            factors.push('category_match');
        }

        if (userPreferences.contentTypes.includes(content.type)) {
            factors.push('content_type_match');
        }

        const matchingTags = (content.tags || []).filter(tag =>
            userPreferences.tags.includes(tag)
        );
        if (matchingTags.length > 0) {
            factors.push(`tag_match_${matchingTags.length}`);
        }

        return factors;
    }

    // Get trending categories
    getTrendingCategories(trendingContent) {
        const categoryScores = {};

        trendingContent.forEach(item => {
            const category = item.content.category || 'unknown';
            categoryScores[category] = (categoryScores[category] || 0) + item.score;
        });

        return Object.entries(categoryScores)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10)
            .map(([category, score]) => ({
                category,
                score: Math.round(score * 100) / 100,
                contentCount: trendingContent.filter(item =>
                    (item.content.category || 'unknown') === category
                ).length
            }));
    }

    // Generate trending insights
    generateTrendingInsights(trendingContent) {
        const insights = [];

        // Top performer
        if (trendingContent.length > 0) {
            const topContent = trendingContent[0];
            insights.push({
                type: 'top_performer',
                title: 'Top Trending Content',
                description: `${topContent.content.title} is trending with a score of ${Math.round(topContent.score * 100) / 100}`,
                contentId: topContent.contentId,
                data: {
                    score: topContent.score,
                    category: topContent.content.category,
                    velocity: topContent.velocity
                }
            });
        }

        // Fastest growing
        const fastestGrowing = trendingContent.reduce((fastest, item) => {
            return (item.velocity > (fastest?.velocity || 0)) ? item : fastest;
        }, null);

        if (fastestGrowing) {
            insights.push({
                type: 'fastest_growing',
                title: 'Fastest Growing Content',
                description: `${fastestGrowing.content.title} has the highest velocity score`,
                contentId: fastestGrowing.contentId,
                data: {
                    velocity: fastestGrowing.velocity,
                    momentum: fastestGrowing.momentum
                }
            });
        }

        // Category trends
        const categories = this.getTrendingCategories(trendingContent);
        if (categories.length > 0) {
            insights.push({
                type: 'category_trend',
                title: 'Trending Category',
                description: `${categories[0].category} is the most trending category`,
                data: {
                    category: categories[0].category,
                    score: categories[0].score,
                    contentCount: categories[0].contentCount
                }
            });
        }

        return insights;
    }

    // Generate content discovery recommendations
    async generateDiscoveryRecommendations(userId, discoveryType, options = {}) {
        try {
            const strategy = this.discoveryStrategies[discoveryType];
            if (!strategy) {
                throw new Error(`Unknown discovery strategy: ${discoveryType}`);
            }

            let recommendations;

            switch (discoveryType) {
                case 'personalized':
                    recommendations = await this.generatePersonalizedDiscovery(userId, options);
                    break;
                case 'trending':
                    recommendations = await this.generateTrendingDiscovery(options);
                    break;
                case 'curated':
                    recommendations = await this.generateCuratedDiscovery(userId, options);
                    break;
                case 'emerging':
                    recommendations = await this.generateEmergingDiscovery(options);
                    break;
                case 'seasonal':
                    recommendations = await this.generateSeasonalDiscovery(options);
                    break;
                default:
                    recommendations = [];
            }

            return {
                strategy: discoveryType,
                strategyName: strategy.name,
                description: strategy.description,
                content: recommendations,
                insights: this.generateDiscoveryInsights(recommendations, discoveryType),
                lastUpdated: new Date().toISOString()
            };

        } catch (error) {
            winston.error(`Error generating ${discoveryType} discovery:`, error);
            return { strategy: discoveryType, content: [], insights: [], lastUpdated: null };
        }
    }

    // Generate personalized discovery
    async generatePersonalizedDiscovery(userId, options) {
        const { numRecommendations = 20, filters = {} } = options;
        const { weights, diversityFactor, serendipityFactor } = this.discoveryStrategies.personalized;

        // Get base recommendations from hybrid system
        const baseRecommendations = await this.hybridRecommender.generateRecommendations(userId, {
            numRecommendations: numRecommendations * 2,
            filters
        });

        // Apply diversity and serendipity
        const diversified = this.applyDiversity(baseRecommendations, diversityFactor);
        const serendipitous = this.applySerendipity(diversified, serendipityFactor, userId);

        return serendipitous.slice(0, numRecommendations);
    }

    // Generate trending discovery
    async generateTrendingDiscovery(options) {
        const { numRecommendations = 20, filters = {} } = options;
        const { timeWindow, categoryBalancing, freshnessBonus } = this.discoveryStrategies.trending;

        const trending = await this.generateTrendingContent(null, filters, numRecommendations * 2);

        if (categoryBalancing) {
            return this.balanceCategories(trending.content, numRecommendations);
        }

        return trending.content.slice(0, numRecommendations);
    }

    // Generate curated discovery
    async generateCuratedDiscovery(userId, options) {
        const { numRecommendations = 20, filters = {} } = options;
        const { curatorWeights, qualityThreshold, updateFrequency } = this.discoveryStrategies.curated;

        // Get high-quality content
        const qualityContent = await this.contentService.getQualityContent(qualityThreshold, filters);

        // Apply curator weights
        const weightedContent = qualityContent.map(content => ({
            ...content,
            curatorScore: this.calculateCuratorScore(content, curatorWeights)
        }));

        // Sort by curator score
        weightedContent.sort((a, b) => b.curatorScore - a.curatorScore);

        return weightedContent.slice(0, numRecommendations);
    }

    // Generate emerging discovery
    async generateEmergingDiscovery(options) {
        const { numRecommendations = 20, filters = {} } = options;
        const { maxAge, growthThreshold, qualityThreshold } = this.discoveryStrategies.emerging;

        // Get recent content with growth potential
        const recentContent = await this.contentService.getRecentContentByAge(maxAge, filters);

        // Filter for content with growth above threshold and minimum quality
        const emergingContent = recentContent.filter(content => {
            const growth = this.calculateGrowthRate(content);
            const quality = this.calculateQualityScore(content);
            return growth > growthThreshold && quality > qualityThreshold;
        });

        // Sort by growth rate
        emergingContent.sort((a, b) => this.calculateGrowthRate(b) - this.calculateGrowthRate(a));

        return emergingContent.slice(0, numRecommendations);
    }

    // Generate seasonal discovery
    async generateSeasonalDiscovery(options) {
        const { numRecommendations = 20, filters = {} } = options;
        const { seasonalityWindow, contextMatching, eventBoosts } = this.discoveryStrategies.seasonal;

        // Get current seasonal context
        const seasonalContext = this.getCurrentSeasonalContext();

        // Get content matching seasonal context
        const seasonalContent = await this.contentService.getSeasonalContent(
            seasonalContext, seasonalityWindow, filters
        );

        // Apply event boosts if applicable
        if (eventBoosts && seasonalContext.currentEvents.length > 0) {
            seasonalContent.forEach(content => {
                content.seasonalBoost = this.calculateEventBoost(content, seasonalContext.currentEvents);
            });
        }

        // Sort by seasonal relevance
        seasonalContent.sort((a, b) => (b.seasonalBoost || 1) - (a.seasonalBoost || 1));

        return seasonalContent.slice(0, numRecommendations);
    }

    // Apply diversity to recommendations
    applyDiversity(recommendations, diversityFactor) {
        if (diversityFactor <= 0) return recommendations;

        const diversified = [];
        const categoryCount = {};
        const typeCount = {};

        recommendations.forEach(rec => {
            const category = rec.content?.category || 'unknown';
            const type = rec.content?.type || 'unknown';

            // Track diversity
            categoryCount[category] = (categoryCount[category] || 0) + 1;
            typeCount[type] = (typeCount[type] || 0) + 1;

            // Adjust score based on diversity
            const categoryDiversity = 1 / (categoryCount[category] || 1);
            const typeDiversity = 1 / (typeCount[type] || 1);
            const diversityBonus = (categoryDiversity + typeDiversity) / 2 * diversityFactor;

            diversified.push({
                ...rec,
                diversityScore: rec.score * (1 + diversityBonus)
            });
        });

        // Re-sort by diversity-adjusted scores
        return diversified.sort((a, b) => b.diversityScore - a.diversityScore);
    }

    // Apply serendipity to recommendations
    applySerendipity(recommendations, serendipityFactor, userId) {
        if (serendipityFactor <= 0) return recommendations;

        return recommendations.map(rec => {
            // Calculate serendipity score based on how unexpected the content is for the user
            const serendipityScore = this.calculateSerendipityScore(rec, userId);
            const serendipityBonus = serendipityScore * serendipityFactor;

            return {
                ...rec,
                serendipitousScore: (rec.diversityScore || rec.score) * (1 + serendipityBonus),
                serendipityFactors: this.getSerendipityFactors(rec, userId)
            };
        }).sort((a, b) => b.serendipitousScore - a.serendipitousScore);
    }

    // Calculate serendipity score
    calculateSerendipityScore(recommendation, userId) {
        // Serendipity is higher for content that's different from user's usual preferences
        // but still potentially interesting
        return Math.random() * 0.5; // Simplified for now
    }

    // Get serendipity factors
    getSerendipityFactors(recommendation, userId) {
        // Return factors that contribute to serendipity
        return ['novel_category', 'unexpected_tag', 'creative_approach'];
    }

    // Balance categories in recommendations
    balanceCategories(content, targetCount) {
        const categories = {};
        const balanced = [];

        // Count content per category
        content.forEach(item => {
            const category = item.content?.category || 'unknown';
            categories[category] = (categories[category] || 0) + 1;
        });

        // Calculate target per category
        const numCategories = Object.keys(categories).length;
        const targetPerCategory = Math.ceil(targetCount / numCategories);

        // Select content balancing categories
        Object.keys(categories).forEach(category => {
            const categoryContent = content.filter(item =>
                (item.content?.category || 'unknown') === category
            ).slice(0, targetPerCategory);
            balanced.push(...categoryContent);
        });

        // Fill remaining slots with highest scoring content
        if (balanced.length < targetCount) {
            const remaining = content
                .filter(item => !balanced.includes(item))
                .slice(0, targetCount - balanced.length);
            balanced.push(...remaining);
        }

        return balanced.slice(0, targetCount);
    }

    // Calculate curator score
    calculateCuratorScore(content, curatorWeights) {
        let score = 0;

        // Expert curation
        if (content.expertApproved) {
            score += curatorWeights.expert;
        }

        // Community curation
        if (content.communityRating > 4.0) {
            score += curatorWeights.community;
        }

        // Automated quality metrics
        const automatedScore = this.calculateAutomatedQualityScore(content);
        score += automatedScore * curatorWeights.automated;

        return score;
    }

    // Calculate automated quality score
    calculateAutomatedQualityScore(content) {
        // Simple automated quality assessment
        let score = 0;

        if (content.rating > 4.0) score += 0.3;
        if (content.engagement?.views > 1000) score += 0.2;
        if (content.engagement?.likes > 100) score += 0.2;
        if (content.completeness > 0.8) score += 0.2;
        if (content.lastUpdated > new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)) {
            score += 0.1;
        }

        return Math.min(1, score);
    }

    // Calculate growth rate
    calculateGrowthRate(content) {
        // Calculate engagement growth rate over time
        const currentEngagement = (content.engagement?.views || 0) +
                                (content.engagement?.likes || 0) +
                                (content.engagement?.shares || 0);

        // For simplicity, assume linear growth based on content age
        const contentAge = (Date.now() - new Date(content.createdAt).getTime()) /
                          (24 * 60 * 60 * 1000); // days

        return contentAge > 0 ? currentEngagement / contentAge : 0;
    }

    // Get current seasonal context
    getCurrentSeasonalContext() {
        const now = new Date();
        const month = now.getMonth() + 1;
        const day = now.getDate();
        const dayOfWeek = now.getDay();

        const currentEvents = [];

        // Check for holidays/events
        Object.entries(this.getHolidayBoosts()).forEach(([name, holiday]) => {
            if (holiday.month === month && Math.abs(day - holiday.day) <= holiday.duration) {
                currentEvents.push({
                    name,
                    boost: holiday.boost,
                    type: 'holiday'
                });
            }
        });

        return {
            month,
            day,
            dayOfWeek,
            season: this.getSeason(month),
            currentEvents,
            weeklyPattern: this.getWeeklyPatterns()[dayOfWeek]
        };
    }

    // Get season
    getSeason(month) {
        if (month >= 3 && month <= 5) return 'spring';
        if (month >= 6 && month <= 8) return 'summer';
        if (month >= 9 && month <= 11) return 'fall';
        return 'winter';
    }

    // Calculate event boost
    calculateEventBoost(content, currentEvents) {
        let boost = 1.0;

        currentEvents.forEach(event => {
            if (this.isContentRelevantToEvent(content, event)) {
                boost *= event.boost;
            }
        });

        return boost;
    }

    // Check if content is relevant to event
    isContentRelevantToEvent(content, event) {
        // Simple relevance check - in reality this would be more sophisticated
        const contentTags = (content.tags || []).map(tag => tag.toLowerCase());
        const eventName = event.name.toLowerCase();

        return contentTags.some(tag => eventName.includes(tag)) ||
               content.title?.toLowerCase().includes(eventName);
    }

    // Generate discovery insights
    generateDiscoveryInsights(recommendations, discoveryType) {
        const insights = [];

        if (recommendations.length === 0) {
            insights.push({
                type: 'no_content',
                title: 'No Content Available',
                description: `No content found for ${discoveryType} discovery`
            });
            return insights;
        }

        // Top content insight
        const topContent = recommendations[0];
        insights.push({
            type: 'top_content',
            title: `Top ${discoveryType} Content`,
            description: `Highest rated: ${topContent.content?.title || 'Unknown'}`,
            contentId: topContent.contentId
        });

        // Category distribution
        const categories = {};
        recommendations.forEach(rec => {
            const category = rec.content?.category || 'unknown';
            categories[category] = (categories[category] || 0) + 1;
        });

        const topCategory = Object.entries(categories)
            .sort((a, b) => b[1] - a[1])[0];

        if (topCategory) {
            insights.push({
                type: 'category_focus',
                title: 'Category Focus',
                description: `${topCategory[0]} represents ${Math.round(topCategory[1] / recommendations.length * 100)}% of recommendations`
            });
        }

        // Quality assessment
        const avgRating = recommendations.reduce((sum, rec) =>
            sum + (rec.content?.rating || 0), 0) / recommendations.length;

        if (avgRating > 4.0) {
            insights.push({
                type: 'high_quality',
                title: 'High Quality Content',
                description: `Average rating: ${avgRating.toFixed(1)}/5.0`
            });
        }

        return insights;
    }

    // Generate popular campaigns and scenarios
    async generatePopularCampaigns(numCampaigns = 10) {
        try {
            const cacheKey = `popular_campaigns:${numCampaigns}`;
            const cached = await this.redisClient.get(`cache:${cacheKey}`);

            if (cached) {
                return JSON.parse(cached);
            }

            // Get campaigns with high engagement
            const campaigns = await this.contentService.getTopCampaigns(numCampaigns * 2);

            // Calculate popularity scores
            const scoredCampaigns = campaigns.map(campaign => ({
                ...campaign,
                popularityScore: this.calculatePopularityScore(campaign),
                trendingScore: this.calculateCampaignTrendingScore(campaign)
            }));

            // Sort by combined score
            scoredCampaigns.sort((a, b) => {
                const scoreA = a.popularityScore * 0.7 + a.trendingScore * 0.3;
                const scoreB = b.popularityScore * 0.7 + b.trendingScore * 0.3;
                return scoreB - scoreA;
            });

            const result = scoredCampaigns.slice(0, numCampaigns);

            // Cache for 1 hour
            await this.redisClient.setEx(`cache:${cacheKey}`, 3600, JSON.stringify(result));

            return result;

        } catch (error) {
            winston.error('Error generating popular campaigns:', error);
            return [];
        }
    }

    // Calculate popularity score
    calculatePopularityScore(content) {
        const engagement = content.engagement || {};
        const rating = content.rating || 0;

        // Weighted engagement score
        const engagementScore =
            (engagement.views || 0) * 0.1 +
            (engagement.likes || 0) * 1 +
            (engagement.shares || 0) * 2 +
            (engagement.comments || 0) * 1.5 +
            (engagement.downloads || 0) * 3;

        // Quality bonus
        const qualityBonus = rating > 0 ? Math.pow(rating / 5, 2) : 0;

        // Time decay (older content gets lower scores)
        const ageInDays = (Date.now() - new Date(content.createdAt).getTime()) /
                         (24 * 60 * 60 * 1000);
        const timeDecay = Math.exp(-ageInDays / 90); // 90-day half-life

        return (engagementScore + qualityBonus * 100) * timeDecay;
    }

    // Calculate campaign trending score
    calculateCampaignTrendingScore(campaign) {
        // Simplified trending calculation for campaigns
        const recentEngagement = (campaign.engagement?.recentViews || 0) * 0.5 +
                                (campaign.engagement?.recentLikes || 0) * 1 +
                                (campaign.engagement?.recentShares || 0) * 2;

        const growthRate = this.calculateGrowthRate(campaign);

        return recentEngagement * (1 + growthRate);
    }

    // Generate community-created content highlights
    async generateCommunityHighlights(numHighlights = 10) {
        try {
            const cacheKey = `community_highlights:${numHighlights}`;
            const cached = await this.redisClient.get(`cache:${cacheKey}`);

            if (cached) {
                return JSON.parse(cached);
            }

            // Get community content
            const communityContent = await this.contentService.getCommunityContent(numHighlights * 2);

            // Calculate community scores
            const scoredContent = communityContent.map(content => ({
                ...content,
                communityScore: this.calculateCommunityScore(content),
                originalityScore: this.calculateOriginalityScore(content),
                collaborationScore: this.calculateCollaborationScore(content)
            }));

            // Sort by community engagement
            scoredContent.sort((a, b) => {
                const scoreA = a.communityScore * 0.5 +
                              a.originalityScore * 0.3 +
                              a.collaborationScore * 0.2;
                const scoreB = b.communityScore * 0.5 +
                              b.originalityScore * 0.3 +
                              b.collaborationScore * 0.2;
                return scoreB - scoreA;
            });

            const result = scoredContent.slice(0, numHighlights);

            // Cache for 2 hours
            await this.redisClient.setEx(`cache:${cacheKey}`, 7200, JSON.stringify(result));

            return result;

        } catch (error) {
            winston.error('Error generating community highlights:', error);
            return [];
        }
    }

    // Calculate community score
    calculateCommunityScore(content) {
        const community = this.communityFeatures;

        let score = 0;

        // User-generated content features
        if (content.isUserGenerated) {
            const contentType = content.type;
            const typeConfig = community.userGenerated[contentType];
            if (typeConfig) {
                score += typeConfig.weight * (content.rating >= typeConfig.qualityThreshold ? 1 : 0.5);
            }
        }

        // Collaborative features
        if (content.reviews?.length > 0) {
            const avgHelpfulness = content.reviews.reduce((sum, review) =>
                sum + (review.helpfulness || 0), 0) / content.reviews.length;
            score += community.collaborative.reviews.weight *
                     (avgHelpfulness >= community.collaborative.reviews.helpfulnessThreshold ? 1 : 0.5);
        }

        // Social features
        const socialEngagement = (content.engagement?.shares || 0) * community.social.shares.weight +
                                (content.engagement?.mentions || 0) * community.social.mentions.weight;
        score += socialEngagement / 100; // Normalize

        return score;
    }

    // Calculate originality score
    calculateOriginalityScore(content) {
        // Assess content originality based on various factors
        let score = 0;

        // Unique tags/combinations
        if (content.tags && content.tags.length > 3) {
            score += 0.3;
        }

        // Creative approach
        if (content.creativityScore > 0.7) {
            score += 0.4;
        }

        // Innovative mechanics
        if (content.innovativeFeatures) {
            score += 0.3;
        }

        return Math.min(1, score);
    }

    // Calculate collaboration score
    calculateCollaborationScore(content) {
        // Assess collaborative nature of content
        let score = 0;

        // Multiple authors/contributors
        if (content.contributors && content.contributors.length > 1) {
            score += 0.4;
        }

        // Community feedback integration
        if (content.communityFeedback) {
            score += 0.3;
        }

        // Remix/derivative work credit
        if (content.derivedFrom && content.attribution) {
            score += 0.3;
        }

        return Math.min(1, score);
    }

    // Generate seasonal event suggestions
    async generateSeasonalEventSuggestions() {
        try {
            const seasonalContext = this.getCurrentSeasonalContext();
            const suggestions = [];

            // Holiday-themed content
            seasonalContext.currentEvents.forEach(event => {
                suggestions.push({
                    type: 'holiday_campaign',
                    title: `${event.name} Campaign Event`,
                    description: `Special campaign themed around ${event.name}`,
                    eventBoost: event.boost,
                    suggestedContent: this.getEventSpecificContentSuggestions(event.name),
                    duration: this.getEventDuration(event.name)
                });
            });

            // Seasonal campaigns
            suggestions.push({
                type: 'seasonal_campaign',
                title: `${seasonalContext.season} Adventure Series`,
                description: `Campaign series tailored for ${seasonalContext.season}`,
                season: seasonalContext.season,
                suggestedThemes: this.getSeasonalThemes(seasonalContext.season),
                environmentSuggestions: this.getSeasonalEnvironments(seasonalContext.season)
            });

            // Weekly game suggestions
            suggestions.push({
                type: 'weekly_game',
                title: `${this.getWeeklyActivityName(seasonalContext.dayOfWeek)} Game Night`,
                description: `Perfect content for ${this.getWeeklyActivityName(seasonalContext.dayOfWeek)} gaming`,
                dayOfWeek: seasonalContext.dayOfWeek,
                activityLevel: seasonalContext.weeklyPattern,
                suggestedFormat: this.getGameFormatForDay(seasonalContext.dayOfWeek)
            });

            return suggestions;

        } catch (error) {
            winston.error('Error generating seasonal event suggestions:', error);
            return [];
        }
    }

    // Get event-specific content suggestions
    getEventSpecificContentSuggestions(eventName) {
        const eventContent = {
            'halloween': ['horror_adventures', 'spooky_monsters', 'gothic_characters'],
            'christmas': ['festive_adventures', 'winter_wonderlands', 'holiday_magic'],
            'newyear': ['new_beginnings', 'fortune_telling', 'celebration_festivals'],
            'summer_solstice': ['fey_wilds', 'nature_magic', 'outdoor_adventures'],
            'tabletop_day': ['introductory_adventures', 'community_events', 'game_mechanics']
        };

        return eventContent[eventName.toLowerCase()] || ['themed_adventures', 'seasonal_content'];
    }

    // Get event duration
    getEventDuration(eventName) {
        const durations = {
            'halloween': '1 week',
            'christmas': '2 weeks',
            'newyear': '3 days',
            'summer_solstice': '1 week',
            'tabletop_day': '1 week'
        };

        return durations[eventName.toLowerCase()] || '1 week';
    }

    // Get seasonal themes
    getSeasonalThemes(season) {
        const themes = {
            spring: ['renewal', 'growth', 'new_beginnings', 'nature_awakening'],
            summer: ['adventure', 'exploration', 'festivals', 'outdoor_life'],
            fall: ['harvest', 'mystery', 'transformation', 'preparation'],
            winter: ['survival', 'introspection', 'community', 'endurance']
        };

        return themes[season] || ['adventure', 'discovery'];
    }

    // Get seasonal environments
    getSeasonalEnvironments(season) {
        const environments = {
            spring: ['blooming_forests', 'river_valleys', 'spring_festivals'],
            summer: ['tropical_islands', 'desert_oases', 'mountain_peaks'],
            fall: ['harvest_fields', 'haunted_forests', 'autumn_festivals'],
            winter: ['snowy_mountains', 'frozen_wastes', 'cozy_taverns']
        };

        return environments[season] || ['fantasy_worlds'];
    }

    // Get weekly activity name
    getWeeklyActivityName(dayOfWeek) {
        const names = ['Sunday_Funday', 'Monday_Mission', 'Tactical_Tuesday',
                      'Wednesday_Whimsy', 'Thursday_Theory', 'Friday_Frenzy', 'Saturday_Spectacle'];
        return names[dayOfWeek] || 'Game_Day';
    }

    // Get game format for day
    getGameFormatForDay(dayOfWeek) {
        const formats = {
            0: 'one_shot', // Sunday - shorter games
            1: 'campaign_continuation', // Monday - ongoing stories
            2: 'tactical_challenge', // Tuesday - combat focused
            3: 'creative_session', // Wednesday - roleplaying heavy
            4: 'planning_session', // Thursday - campaign prep
            5: 'climactic_battle', // Friday - big encounters
            6: 'epic_adventure' // Saturday - long sessions
        };

        return formats[dayOfWeek] || 'flexible';
    }

    // Generate cross-server content sharing recommendations
    async generateCrossServerRecommendations(userId, serverContext) {
        try {
            const { currentServer, serverType, memberCount, activityLevel } = serverContext;

            // Get popular content from similar servers
            const similarServers = await this.findSimilarServers(currentServer, serverType);
            const crossServerContent = await this.getContentFromSimilarServers(similarServers);

            // Filter and rank content based on server context
            const rankedContent = crossServerContent.map(content => ({
                ...content,
                serverRelevanceScore: this.calculateServerRelevance(content, serverContext),
                crossServerPopularity: this.calculateCrossServerPopularity(content, similarServers)
            }));

            // Sort by combined relevance and popularity
            rankedContent.sort((a, b) => {
                const scoreA = a.serverRelevanceScore * 0.6 + a.crossServerPopularity * 0.4;
                const scoreB = b.serverRelevanceScore * 0.6 + b.crossServerPopularity * 0.4;
                return scoreB - scoreA;
            });

            return {
                content: rankedContent.slice(0, 20),
                serverInsights: this.generateServerInsights(similarServers, serverContext),
                collaborationOpportunities: this.identifyCollaborationOpportunities(similarServers),
                trendingInSimilarServers: this.getTrendingInSimilarServers(similarServers)
            };

        } catch (error) {
            winston.error('Error generating cross-server recommendations:', error);
            return { content: [], serverInsights: [], collaborationOpportunities: [], trendingInSimilarServers: [] };
        }
    }

    // Find similar servers
    async findSimilarServers(currentServer, serverType) {
        // This would typically query a database of servers
        // For now, return simulated similar servers
        return [
            { id: 'server_1', name: 'Dungeon Masters Guild', type: serverType, memberCount: 5000 },
            { id: 'server_2', name: 'Adventurers League', type: serverType, memberCount: 3000 },
            { id: 'server_3', name: 'Critical Role Fans', type: serverType, memberCount: 8000 }
        ];
    }

    // Get content from similar servers
    async getContentFromSimilarServers(similarServers) {
        // This would aggregate content from multiple servers
        // For now, return simulated cross-server content
        return [
            {
                id: 'cross_content_1',
                title: 'The Lost Mine of Phandelver - Community Remix',
                type: 'adventure',
                sourceServer: 'Dungeon Masters Guild',
                tags: ['beginner', 'exploration', 'community'],
                rating: 4.5,
                engagement: { views: 2500, likes: 300, shares: 50 }
            },
            {
                id: 'cross_content_2',
                title: 'Homebrew Monster Collection',
                type: 'monster',
                sourceServer: 'Adventurers League',
                tags: ['monsters', 'homebrew', 'combat'],
                rating: 4.2,
                engagement: { views: 1800, likes: 200, shares: 40 }
            }
        ];
    }

    // Calculate server relevance score
    calculateServerRelevance(content, serverContext) {
        let score = 0;

        // Member count appropriateness
        if (serverContext.memberCount < 1000 && content.tags.includes('beginner')) {
            score += 0.3;
        } else if (serverContext.memberCount > 5000 && content.tags.includes('advanced')) {
            score += 0.3;
        }

        // Activity level matching
        if (serverContext.activityLevel === 'high' && content.type === 'adventure') {
            score += 0.2;
        } else if (serverContext.activityLevel === 'low' && content.type === 'tools') {
            score += 0.2;
        }

        // Content type appropriateness for server type
        if (serverContext.serverType === 'beginner_friendly' && content.rating > 4.0) {
            score += 0.2;
        } else if (serverContext.serverType === 'veteran' && content.tags.includes('complex')) {
            score += 0.2;
        }

        return Math.min(1, score);
    }

    // Calculate cross-server popularity
    calculateCrossServerPopularity(content, similarServers) {
        // Normalize engagement metrics across servers
        const totalViews = content.engagement.views || 0;
        const totalLikes = content.engagement.likes || 0;
        const totalShares = content.engagement.shares || 0;

        // Weight different engagement types
        const popularityScore = (totalViews * 0.1 + totalLikes * 1 + totalShares * 2) /
                               similarServers.length;

        return Math.min(1, popularityScore / 100); // Normalize to 0-1
    }

    // Generate server insights
    generateServerInsights(similarServers, serverContext) {
        const insights = [];

        const avgMemberCount = similarServers.reduce((sum, server) =>
            sum + server.memberCount, 0) / similarServers.length;

        if (serverContext.memberCount < avgMemberCount) {
            insights.push({
                type: 'growth_opportunity',
                title: 'Growth Potential',
                description: 'Your server has room to grow compared to similar servers'
            });
        }

        const popularContentTypes = this.getPopularContentTypes(similarServers);
        insights.push({
            type: 'content_trends',
            title: 'Popular Content Types',
            description: `Most popular content in similar servers: ${popularContentTypes.join(', ')}`
        });

        return insights;
    }

    // Get popular content types from similar servers
    getPopularContentTypes(similarServers) {
        // This would analyze actual content data
        // For now, return simulated popular types
        return ['adventures', 'characters', 'monsters'];
    }

    // Identify collaboration opportunities
    identifyCollaborationOpportunities(similarServers) {
        return [
            {
                type: 'cross_server_event',
                title: 'Joint Campaign Event',
                description: 'Organize a multi-server campaign event',
                potentialServers: similarServers.slice(0, 2)
            },
            {
                type: 'content_sharing',
                title: 'Content Exchange Program',
                description: 'Share and adapt content between servers',
                potentialServers: similarServers
            },
            {
                type: 'community_collaboration',
                title: 'Community Project',
                description: 'Work together on a large community project',
                potentialServers: similarServers
            }
        ];
    }

    // Get trending in similar servers
    getTrendingInSimilarServers(similarServers) {
        // This would get actual trending data from similar servers
        // For now, return simulated trending content
        return [
            {
                title: 'Summer Campaign Marathon',
                type: 'event',
                servers: 3,
                engagement: 'high'
            },
            {
                title: 'Homebrew Contest Winners',
                type: 'contest',
                servers: 2,
                engagement: 'medium'
            }
        ];
    }
}

module.exports = ContentDiscoveryService;