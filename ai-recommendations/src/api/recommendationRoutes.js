const express = require('express');
const winston = require('winston');
const rateLimit = require('express-rate-limit');

const router = express.Router();

// Rate limiting for recommendation endpoints
const recommendationLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // limit each IP to 100 requests per windowMs
    message: {
        error: 'Too many recommendation requests, please try again later.',
        retryAfter: '15 minutes'
    },
    standardHeaders: true,
    legacyHeaders: false
});

// Behavior tracking rate limiting (more lenient)
const behaviorLimiter = rateLimit({
    windowMs: 1 * 60 * 1000, // 1 minute
    max: 200, // limit each IP to 200 behavior tracking requests per minute
    message: {
        error: 'Too many behavior tracking requests, please try again later.',
        retryAfter: '1 minute'
    }
});

/**
 * @route   POST /api/recommendations/behavior
 * @desc    Track user behavior for personalization
 * @access  Private
 */
router.post('/behavior', behaviorLimiter, async (req, res) => {
    try {
        const { userId, action, contentId, contentType, metadata, context, sessionId } = req.body;

        // Validate required fields
        if (!userId || !action || !contentId) {
            return res.status(400).json({
                error: 'Missing required fields: userId, action, contentId',
                required: ['userId', 'action', 'contentId']
            });
        }

        // Track behavior
        const success = await req.personalizationEngine.trackUserBehavior({
            userId,
            action,
            contentId,
            contentType,
            metadata,
            context,
            sessionId
        });

        if (success) {
            res.status(200).json({
                success: true,
                message: 'Behavior tracked successfully',
                timestamp: new Date().toISOString()
            });
        } else {
            res.status(400).json({
                error: 'Failed to track behavior',
                message: 'Invalid behavior data or tracking error'
            });
        }

    } catch (error) {
        winston.error('Error tracking behavior:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Failed to track user behavior'
        });
    }
});

/**
 * @route   GET /api/recommendations/personal/:userId
 * @desc    Get personalized recommendations for a user
 * @access  Private
 */
router.get('/personal/:userId', recommendationLimiter, async (req, res) => {
    try {
        const { userId } = req.params;
        const {
            numRecommendations = 20,
            filters = {},
            context = {},
            includeExplanation = false
        } = req.query;

        // Parse filters and context
        const parsedFilters = typeof filters === 'string' ? JSON.parse(filters) : filters;
        const parsedContext = typeof context === 'string' ? JSON.parse(context) : context;

        // Get personalized recommendations
        const result = await req.personalizationEngine.getPersonalizedRecommendations(
            userId,
            {
                numRecommendations: parseInt(numRecommendations),
                filters: parsedFilters,
                context: parsedContext
            }
        );

        // Include detailed explanations if requested
        if (includeExplanation === 'true') {
            result.explanations = await generateRecommendationExplanations(
                result.recommendations, userId
            );
        }

        res.status(200).json({
            success: true,
            userId,
            recommendations: result.recommendations,
            personalization: result.personalizationData,
            metadata: {
                requestedAt: new Date().toISOString(),
                numRecommendations: result.recommendations.length,
                filters: parsedFilters,
                context: parsedContext
            }
        });

    } catch (error) {
        winston.error('Error getting personalized recommendations:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Failed to get personalized recommendations'
        });
    }
});

/**
 * @route   GET /api/recommendations/player/:userId
 * @desc    Get player-specific recommendations (builds, equipment, spells)
 * @access  Private
 */
router.get('/player/:userId', recommendationLimiter, async (req, res) => {
    try {
        const { userId } = req.params;
        const {
            type,
            characterInfo,
            currentEquipment,
            knownSpells,
            numRecommendations = 10
        } = req.query;

        // Parse character information
        const parsedCharacterInfo = characterInfo ? JSON.parse(characterInfo) : null;
        const parsedEquipment = currentEquipment ? JSON.parse(currentEquipment) : {};
        const parsedSpells = knownSpells ? JSON.parse(knownSpells) : [];

        let result = {};

        switch (type) {
            case 'builds':
                if (!parsedCharacterInfo) {
                    return res.status(400).json({
                        error: 'Character information required for build recommendations',
                        required: ['class', 'level']
                    });
                }
                result = await req.playerRecommendationService.generateCharacterBuildRecommendations(
                    userId, parsedCharacterInfo, parseInt(numRecommendations)
                );
                break;

            case 'equipment':
                if (!parsedCharacterInfo) {
                    return res.status(400).json({
                        error: 'Character information required for equipment recommendations'
                    });
                }
                result = await req.playerRecommendationService.generateEquipmentRecommendations(
                    userId, parsedCharacterInfo, parsedEquipment, parseInt(numRecommendations)
                );
                break;

            case 'spells':
                if (!parsedCharacterInfo) {
                    return res.status(400).json({
                        error: 'Character information required for spell recommendations'
                    });
                }
                result = await req.playerRecommendationService.generateSpellRecommendations(
                    userId, parsedCharacterInfo, parsedSpells, parseInt(numRecommendations)
                );
                break;

            default:
                // Get all types
                if (parsedCharacterInfo) {
                    result.builds = await req.playerRecommendationService.generateCharacterBuildRecommendations(
                        userId, parsedCharacterInfo, Math.ceil(numRecommendations / 3)
                    );
                    result.equipment = await req.playerRecommendationService.generateEquipmentRecommendations(
                        userId, parsedCharacterInfo, parsedEquipment, Math.ceil(numRecommendations / 3)
                    );
                    result.spells = await req.playerRecommendationService.generateSpellRecommendations(
                        userId, parsedCharacterInfo, parsedSpells, Math.ceil(numRecommendations / 3)
                    );
                } else {
                    return res.status(400).json({
                        error: 'Character information required for player recommendations',
                        required: ['class', 'level']
                    });
                }
        }

        res.status(200).json({
            success: true,
            userId,
            type: type || 'all',
            recommendations: result,
            metadata: {
                requestedAt: new Date().toISOString(),
                characterClass: parsedCharacterInfo?.class,
                characterLevel: parsedCharacterInfo?.level
            }
        });

    } catch (error) {
        winston.error('Error getting player recommendations:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Failed to get player recommendations'
        });
    }
});

/**
 * @route   GET /api/recommendations/dm/:userId
 * @desc    Get DM-specific recommendations (encounters, story hooks, NPCs)
 * @access  Private
 */
router.get('/dm/:userId', recommendationLimiter, async (req, res) => {
    try {
        const { userId } = req.params;
        const {
            type,
            partyInfo,
            campaignContext,
            npcRequest,
            encounterInfo,
            numRecommendations = 10
        } = req.query;

        // Parse input data
        const parsedPartyInfo = partyInfo ? JSON.parse(partyInfo) : null;
        const parsedCampaignContext = campaignContext ? JSON.parse(campaignContext) : {};
        const parsedNpcRequest = npcRequest ? JSON.parse(npcRequest) : {};
        const parsedEncounterInfo = encounterInfo ? JSON.parse(encounterInfo) : {};

        let result = {};

        switch (type) {
            case 'encounters':
                if (!parsedPartyInfo) {
                    return res.status(400).json({
                        error: 'Party information required for encounter recommendations',
                        required: ['level', 'size', 'composition']
                    });
                }
                result = await req.dmRecommendationService.generateEncounterRecommendations(
                    userId, parsedPartyInfo, parsedCampaignContext, parseInt(numRecommendations)
                );
                break;

            case 'storyhooks':
                result = await req.dmRecommendationService.generateStoryHookRecommendations(
                    userId, parsedCampaignContext, parsedPartyInfo, parseInt(numRecommendations)
                );
                break;

            case 'npcs':
                result = await req.dmRecommendationService.generateNPCRecommendations(
                    userId, parsedNpcRequest, parseInt(numRecommendations)
                );
                break;

            case 'treasure':
                if (!parsedEncounterInfo || !parsedPartyInfo) {
                    return res.status(400).json({
                        error: 'Encounter and party information required for treasure recommendations'
                    });
                }
                result = await req.dmRecommendationService.generateTreasureRecommendations(
                    userId, parsedEncounterInfo, parsedPartyInfo, parseInt(numRecommendations)
                );
                break;

            default:
                // Get comprehensive DM recommendations
                if (parsedPartyInfo) {
                    result.encounters = await req.dmRecommendationService.generateEncounterRecommendations(
                        userId, parsedPartyInfo, parsedCampaignContext, Math.ceil(numRecommendations / 4)
                    );
                }
                result.storyhooks = await req.dmRecommendationService.generateStoryHookRecommendations(
                    userId, parsedCampaignContext, parsedPartyInfo, Math.ceil(numRecommendations / 4)
                );
                result.npcs = await req.dmRecommendationService.generateNPCRecommendations(
                    userId, parsedNpcRequest, Math.ceil(numRecommendations / 4)
                );
                if (parsedEncounterInfo && parsedPartyInfo) {
                    result.treasure = await req.dmRecommendationService.generateTreasureRecommendations(
                        userId, parsedEncounterInfo, parsedPartyInfo, Math.ceil(numRecommendations / 4)
                    );
                }
        }

        res.status(200).json({
            success: true,
            userId,
            type: type || 'all',
            recommendations: result,
            metadata: {
                requestedAt: new Date().toISOString(),
                partyLevel: parsedPartyInfo?.level,
                partySize: parsedPartyInfo?.size
            }
        });

    } catch (error) {
        winston.error('Error getting DM recommendations:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Failed to get DM recommendations'
        });
    }
});

/**
 * @route   GET /api/recommendations/discover
 * @desc    Get content discovery recommendations
 * @access  Public (with rate limiting)
 */
router.get('/discover', recommendationLimiter, async (req, res) => {
    try {
        const {
            userId,
            discoveryType = 'personalized',
            filters = {},
            numRecommendations = 20
        } = req.query;

        // Parse filters
        const parsedFilters = typeof filters === 'string' ? JSON.parse(filters) : filters;

        // Get discovery recommendations
        const result = await req.contentDiscoveryService.generateDiscoveryRecommendations(
            userId || null, discoveryType, {
                numRecommendations: parseInt(numRecommendations),
                filters: parsedFilters
            }
        );

        res.status(200).json({
            success: true,
            userId: userId || 'anonymous',
            discoveryType,
            recommendations: result.content,
            insights: result.insights,
            metadata: {
                requestedAt: new Date().toISOString(),
                strategy: result.strategyName,
                description: result.description
            }
        });

    } catch (error) {
        winston.error('Error getting discovery recommendations:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Failed to get discovery recommendations'
        });
    }
});

/**
 * @route   GET /api/recommendations/trending
 * @desc    Get trending content recommendations
 * @access  Public (with rate limiting)
 */
router.get('/trending', recommendationLimiter, async (req, res) => {
    try {
        const {
            userId,
            filters = {},
            numRecommendations = 20
        } = req.query;

        // Parse filters
        const parsedFilters = typeof filters === 'string' ? JSON.parse(filters) : filters;

        // Get trending content
        const result = await req.contentDiscoveryService.generateTrendingContent(
            userId || null, parsedFilters, parseInt(numRecommendations)
        );

        res.status(200).json({
            success: true,
            userId: userId || 'anonymous',
            trending: result.content,
            categories: result.categories,
            insights: result.insights,
            metadata: {
                requestedAt: new Date().toISOString(),
                lastUpdated: result.lastUpdated,
                numItems: result.content.length
            }
        });

    } catch (error) {
        winston.error('Error getting trending recommendations:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Failed to get trending recommendations'
        });
    }
});

/**
 * @route   GET /api/recommendations/popular/campaigns
 * @desc    Get popular campaign recommendations
 * @access  Public (with rate limiting)
 */
router.get('/popular/campaigns', recommendationLimiter, async (req, res) => {
    try {
        const { numCampaigns = 10 } = req.query;

        const campaigns = await req.contentDiscoveryService.generatePopularCampaigns(
            parseInt(numCampaigns)
        );

        res.status(200).json({
            success: true,
            campaigns,
            metadata: {
                requestedAt: new Date().toISOString(),
                numCampaigns: campaigns.length
            }
        });

    } catch (error) {
        winston.error('Error getting popular campaigns:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Failed to get popular campaigns'
        });
    }
});

/**
 * @route   GET /api/recommendations/community/highlights
 * @desc    Get community-created content highlights
 * @access  Public (with rate limiting)
 */
router.get('/community/highlights', recommendationLimiter, async (req, res) => {
    try {
        const { numHighlights = 10 } = req.query;

        const highlights = await req.contentDiscoveryService.generateCommunityHighlights(
            parseInt(numHighlights)
        );

        res.status(200).json({
            success: true,
            highlights,
            metadata: {
                requestedAt: new Date().toISOString(),
                numHighlights: highlights.length
            }
        });

    } catch (error) {
        winston.error('Error getting community highlights:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Failed to get community highlights'
        });
    }
});

/**
 * @route   GET /api/recommendations/seasonal
 * @desc    Get seasonal event suggestions
 * @access  Public (with rate limiting)
 */
router.get('/seasonal', recommendationLimiter, async (req, res) => {
    try {
        const suggestions = await req.contentDiscoveryService.generateSeasonalEventSuggestions();

        res.status(200).json({
            success: true,
            suggestions,
            metadata: {
                requestedAt: new Date().toISOString(),
                season: suggestions.find(s => s.type === 'seasonal_campaign')?.season || 'unknown'
            }
        });

    } catch (error) {
        winston.error('Error getting seasonal suggestions:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Failed to get seasonal suggestions'
        });
    }
});

/**
 * @route   GET /api/recommendations/cross-server/:userId
 * @desc    Get cross-server content sharing recommendations
 * @access  Private
 */
router.get('/cross-server/:userId', recommendationLimiter, async (req, res) => {
    try {
        const { userId } = req.params;
        const { serverContext } = req.query;

        const parsedServerContext = serverContext ? JSON.parse(serverContext) : {};

        if (!parsedServerContext.currentServer) {
            return res.status(400).json({
                error: 'Server context required',
                required: ['currentServer', 'serverType']
            });
        }

        const result = await req.contentDiscoveryService.generateCrossServerRecommendations(
            userId, parsedServerContext
        );

        res.status(200).json({
            success: true,
            userId,
            crossServer: result.content,
            insights: result.serverInsights,
            collaboration: result.collaborationOpportunities,
            metadata: {
                requestedAt: new Date().toISOString(),
                currentServer: parsedServerContext.currentServer
            }
        });

    } catch (error) {
        winston.error('Error getting cross-server recommendations:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Failed to get cross-server recommendations'
        });
    }
});

/**
 * @route   GET /api/recommendations/insights/:userId
 * @desc    Get user insights and analytics
 * @access  Private
 */
router.get('/insights/:userId', recommendationLimiter, async (req, res) => {
    try {
        const { userId } = req.params;

        const result = await req.personalizationEngine.getUserInsights(userId);

        res.status(200).json({
            success: true,
            userId,
            insights: result.insights,
            segmentation: result.segmentation,
            stats: result.stats,
            adaptationState: result.adaptationState,
            metadata: {
                requestedAt: new Date().toISOString()
            }
        });

    } catch (error) {
        winston.error('Error getting user insights:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Failed to get user insights'
        });
    }
});

/**
 * @route   POST /api/recommendations/ab-test/:userId
 * @desc    Run A/B test for recommendation algorithms
 * @access  Private
 */
router.post('/ab-test/:userId', recommendationLimiter, async (req, res) => {
    try {
        const { userId } = req.params;
        const { testName, variants, trafficSplit } = req.body;

        if (!testName || !variants || !trafficSplit) {
            return res.status(400).json({
                error: 'Missing required A/B test parameters',
                required: ['testName', 'variants', 'trafficSplit']
            });
        }

        const result = await req.personalizationEngine.runABTest(userId, {
            testName,
            variants,
            trafficSplit
        });

        if (result) {
            res.status(200).json({
                success: true,
                test: result.test,
                variant: result.variant,
                recommendations: result.recommendations,
                metadata: result.testMetadata
            });
        } else {
            res.status(500).json({
                error: 'Failed to run A/B test'
            });
        }

    } catch (error) {
        winston.error('Error running A/B test:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Failed to run A/B test'
        });
    }
});

/**
 * @route   GET /api/recommendations/similar/:contentId
 * @desc    Get content similar to specified content
 * @access  Public (with rate limiting)
 */
router.get('/similar/:contentId', recommendationLimiter, async (req, res) => {
    try {
        const { contentId } = req.params;
        const { userId, numSimilar = 10 } = req.query;

        // Get similar content using content-based filtering
        const similarContent = await req.hybridRecommender.contentBasedFiltering.getSimilarContent(
            contentId, parseInt(numSimilar)
        );

        res.status(200).json({
            success: true,
            contentId,
            userId: userId || 'anonymous',
            similarContent,
            metadata: {
                requestedAt: new Date().toISOString(),
                numSimilar: similarContent.length
            }
        });

    } catch (error) {
        winston.error('Error getting similar content:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Failed to get similar content'
        });
    }
});

/**
 * @route   GET /api/recommendations/feedback/:userId
 * @desc    Get recommendation feedback interface
 * @access  Private
 */
router.get('/feedback/:userId', recommendationLimiter, async (req, res) => {
    try {
        const { userId } = req.params;
        const { recommendationId, contentId } = req.query;

        // Generate feedback form based on recommendation context
        const feedbackForm = {
            userId,
            recommendationId,
            contentId,
            feedbackOptions: [
                { type: 'rating', label: 'How relevant was this recommendation?', scale: 1-5 },
                { type: 'checkbox', label: 'Why was this helpful?', options: ['accurate', 'new', 'timely', 'well_explained'] },
                { type: 'checkbox', label: 'Why was this not helpful?', options: ['irrelevant', 'outdated', 'inaccurate', 'poorly_explained'] },
                { type: 'text', label: 'Additional feedback (optional)', maxLength: 500 }
            ],
            timestamp: new Date().toISOString()
        };

        res.status(200).json({
            success: true,
            feedbackForm,
            metadata: {
                requestedAt: new Date().toISOString()
            }
        });

    } catch (error) {
        winston.error('Error generating feedback form:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Failed to generate feedback form'
        });
    }
});

/**
 * @route   POST /api/recommendations/feedback/:userId
 * @desc    Submit recommendation feedback
 * @access  Private
 */
router.post('/feedback/:userId', recommendationLimiter, async (req, res) => {
    try {
        const { userId } = req.params;
        const {
            recommendationId,
            contentId,
            rating,
            helpfulReasons,
            unhelpfulReasons,
            additionalFeedback
        } = req.body;

        // Validate feedback data
        if (!recommendationId || !contentId || !rating) {
            return res.status(400).json({
                error: 'Missing required feedback fields',
                required: ['recommendationId', 'contentId', 'rating']
            });
        }

        // Track feedback as behavior
        const behaviorData = {
            userId,
            action: rating >= 4 ? 'positive_feedback' : 'negative_feedback',
            contentId,
            contentType: 'recommendation',
            metadata: {
                recommendationId,
                rating,
                helpfulReasons,
                unhelpfulReasons,
                additionalFeedback
            },
            context: {
                source: 'recommendation_feedback',
                timestamp: new Date().toISOString()
            }
        };

        const success = await req.personalizationEngine.trackUserBehavior(behaviorData);

        if (success) {
            res.status(200).json({
                success: true,
                message: 'Feedback submitted successfully',
                feedbackId: `${recommendationId}_${userId}_${Date.now()}`,
                timestamp: new Date().toISOString()
            });
        } else {
            res.status(400).json({
                error: 'Failed to submit feedback'
            });
        }

    } catch (error) {
        winston.error('Error submitting feedback:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Failed to submit feedback'
        });
    }
});

/**
 * @route   GET /api/recommendations/health
 * @desc    Health check for recommendation system
 * @access  Public
 */
router.get('/health', async (req, res) => {
    try {
        const health = {
            status: 'healthy',
            timestamp: new Date().toISOString(),
            services: {
                personalizationEngine: await checkServiceHealth(req.personalizationEngine),
                hybridRecommender: await checkServiceHealth(req.hybridRecommender),
                playerRecommendations: await checkServiceHealth(req.playerRecommendationService),
                dmRecommendations: await checkServiceHealth(req.dmRecommendationService),
                contentDiscovery: await checkServiceHealth(req.contentDiscoveryService),
                redis: await checkRedisHealth(req.redisClient)
            },
            metrics: {
                uptime: process.uptime(),
                memoryUsage: process.memoryUsage(),
                activeUsers: await getActiveUsersCount(req.redisClient)
            }
        };

        // Check if any service is unhealthy
        const unhealthyServices = Object.entries(health.services)
            .filter(([name, status]) => status !== 'healthy')
            .map(([name]) => name);

        if (unhealthyServices.length > 0) {
            health.status = 'degraded';
            return res.status(503).json(health);
        }

        res.status(200).json(health);

    } catch (error) {
        winston.error('Health check failed:', error);
        res.status(500).json({
            status: 'unhealthy',
            timestamp: new Date().toISOString(),
            error: error.message
        });
    }
});

/**
 * @route   GET /api/recommendations/metrics
 * @desc    Get recommendation system metrics
 * @access  Private (admin only)
 */
router.get('/metrics', async (req, res) => {
    try {
        // Verify admin access (implement your own auth logic)
        if (!req.user || !req.user.isAdmin) {
            return res.status(403).json({
                error: 'Admin access required'
            });
        }

        const metrics = {
            timestamp: new Date().toISOString(),
            recommendationStats: await getRecommendationStats(req.redisClient),
            userStats: await getUserStats(req.redisClient),
            contentStats: await getContentStats(req.contentService),
            performanceStats: await getPerformanceStats(req.redisClient),
            modelStats: req.hybridRecommender.getModelStats()
        };

        res.status(200).json({
            success: true,
            metrics
        });

    } catch (error) {
        winston.error('Error getting metrics:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: 'Failed to get metrics'
        });
    }
});

// Helper functions

async function generateRecommendationExplanations(recommendations, userId) {
    // Generate human-readable explanations for why items were recommended
    return recommendations.map(rec => ({
        contentId: rec.contentId,
        explanation: `Recommended based on your interest in ${rec.metadata?.category || 'similar content'}`,
        factors: rec.methods || ['collaborative_filtering'],
        confidence: rec.score ? Math.min(1, rec.score / 10) : 0.5
    }));
}

async function checkServiceHealth(service) {
    try {
        // Basic health check - try to access a property or method
        if (typeof service === 'object' && service !== null) {
            return 'healthy';
        }
        return 'unhealthy';
    } catch (error) {
        return 'unhealthy';
    }
}

async function checkRedisHealth(redisClient) {
    try {
        await redisClient.ping();
        return 'healthy';
    } catch (error) {
        return 'unhealthy';
    }
}

async function getActiveUsersCount(redisClient) {
    try {
        // Get count of users active in last hour
        const activeUsers = await redisClient.sCard('active_users:hour');
        return activeUsers;
    } catch (error) {
        return 0;
    }
}

async function getRecommendationStats(redisClient) {
    try {
        // Get various recommendation statistics
        const stats = {
            totalRecommendations: await redisClient.get('stats:total_recommendations') || 0,
            dailyRecommendations: await redisClient.get('stats:daily_recommendations') || 0,
            averageRating: await redisClient.get('stats:average_rating') || 0,
            clickThroughRate: await redisClient.get('stats:ctr') || 0
        };
        return stats;
    } catch (error) {
        return {};
    }
}

async function getUserStats(redisClient) {
    try {
        return {
            totalUsers: await redisClient.get('stats:total_users') || 0,
            activeUsers: await getActiveUsersCount(redisClient),
            newUsersToday: await redisClient.get('stats:new_users_today') || 0
        };
    } catch (error) {
        return {};
    }
}

async function getContentStats(contentService) {
    try {
        return {
            totalContent: await contentService.getTotalContentCount(),
            newContentToday: await contentService.getNewContentCount('today'),
            averageRating: await contentService.getAverageRating()
        };
    } catch (error) {
        return {};
    }
}

async function getPerformanceStats(redisClient) {
    try {
        return {
            averageResponseTime: await redisClient.get('stats:avg_response_time') || 0,
            cacheHitRate: await redisClient.get('stats:cache_hit_rate') || 0,
            errorRate: await redisClient.get('stats:error_rate') || 0
        };
    } catch (error) {
        return {};
    }
}

module.exports = router;