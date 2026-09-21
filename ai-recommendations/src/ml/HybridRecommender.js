const CollaborativeFiltering = require('./CollaborativeFiltering');
const ContentBasedFiltering = require('./ContentBasedFiltering');
const winston = require('winston');

class HybridRecommender {
    constructor(options = {}) {
        this.collaborativeFiltering = new CollaborativeFiltering(options.collaborative || {});
        this.contentBasedFiltering = new ContentBasedFiltering(options.contentBased || {});

        // Hybrid parameters
        this.weights = {
            collaborative: options.collaborativeWeight || 0.5,
            contentBased: options.contentBasedWeight || 0.3,
            popularity: options.popularityWeight || 0.1,
            diversity: options.diversityWeight || 0.1
        };

        this.recommendationTypes = {
            COLLABORATIVE_USER_BASED: 'collaborative_user_based',
            COLLABORATIVE_ITEM_BASED: 'collaborative_item_based',
            COLLABORATIVE_HYBRID: 'collaborative_hybrid',
            CONTENT_BASED: 'content_based',
            POPULARITY_BASED: 'popularity_based',
            DIVERSITY_BASED: 'diversity_based',
            TRENDING: 'trending'
        };

        this.minInteractionsForCollaborative = options.minInteractionsForCollaborative || 5;
        this.diversityThreshold = options.diversityThreshold || 0.3;
        this.maxRecommendations = options.maxRecommendations || 50;
    }

    // Initialize all recommendation models
    async initialize(interactions, contents) {
        try {
            winston.info('Initializing hybrid recommendation system...');

            // Initialize collaborative filtering
            this.collaborativeFiltering.buildMatrix(interactions);
            this.collaborativeFiltering.calculateUserSimilarities();
            this.collaborativeFiltering.calculateItemSimilarities();

            // Initialize content-based filtering
            this.contentBasedFiltering.buildContentProfiles(contents);

            // Build user profiles for content-based recommendations
            const userInteractions = this.groupInteractionsByUser(interactions);
            for (const [userId, userInteractionList] of userInteractions) {
                this.contentBasedFiltering.buildUserProfile(userId, userInteractionList);
            }

            // Store content and interaction data
            this.contents = new Map(contents.map(c => [c._id.toString(), c]));
            this.interactions = interactions;

            winston.info('Hybrid recommendation system initialized successfully');
            return true;
        } catch (error) {
            winston.error('Error initializing hybrid recommender:', error);
            throw error;
        }
    }

    // Group interactions by user
    groupInteractionsByUser(interactions) {
        const userInteractions = new Map();

        interactions.forEach(interaction => {
            const userId = interaction.userId;
            if (!userInteractions.has(userId)) {
                userInteractions.set(userId, []);
            }
            userInteractions.get(userId).push(interaction);
        });

        return userInteractions;
    }

    // Generate hybrid recommendations
    async generateRecommendations(userId, options = {}) {
        try {
            const numRecommendations = options.numRecommendations || 10;
            const context = options.context || {};
            const filters = options.filters || {};

            winston.debug(`Generating ${numRecommendations} recommendations for user ${userId}`);

            // Get user interaction count
            const userInteractions = this.getUserInteractions(userId);
            const interactionCount = userInteractions.length;

            // Determine which methods to use based on user interaction count
            const methods = this.selectRecommendationMethods(interactionCount, context);

            // Generate recommendations from each method
            const methodResults = await Promise.all(
                methods.map(method => this.generateMethodRecommendations(userId, method, numRecommendations * 2, filters))
            );

            // Combine and rank recommendations
            const combinedRecommendations = this.combineRecommendations(methodResults, userId);

            // Apply diversity and business rules
            const finalRecommendations = this.applyBusinessRules(combinedRecommendations, userId, numRecommendations, filters);

            // Log recommendation generation
            this.logRecommendationGeneration(userId, finalRecommendations, methods);

            return finalRecommendations;
        } catch (error) {
            winston.error('Error generating hybrid recommendations:', error);
            return this.getFallbackRecommendations(numRecommendations);
        }
    }

    // Select recommendation methods based on user interaction count and context
    selectRecommendationMethods(interactionCount, context) {
        const methods = [];

        if (interactionCount >= this.minInteractionsForCollaborative) {
            // User has enough interactions for collaborative filtering
            methods.push({
                type: this.recommendationTypes.COLLABORATIVE_HYBRID,
                weight: this.weights.collaborative
            });
            methods.push({
                type: this.recommendationTypes.COLLABORATIVE_USER_BASED,
                weight: this.weights.collaborative * 0.5
            });
            methods.push({
                type: this.recommendationTypes.COLLABORATIVE_ITEM_BASED,
                weight: this.weights.collaborative * 0.5
            });
        }

        // Always include content-based recommendations
        methods.push({
            type: this.recommendationTypes.CONTENT_BASED,
            weight: this.weights.contentBased
        });

        // Include popularity-based for cold start
        if (interactionCount < this.minInteractionsForCollaborative) {
            methods.push({
                type: this.recommendationTypes.POPULARITY_BASED,
                weight: this.weights.popularity * 2
            });
        }

        // Include trending if context suggests it
        if (context.includeTrending) {
            methods.push({
                type: this.recommendationTypes.TRENDING,
                weight: this.weights.popularity
            });
        }

        // Include diversity-based recommendations
        methods.push({
            type: this.recommendationTypes.DIVERSITY_BASED,
            weight: this.weights.diversity
        });

        return methods;
    }

    // Generate recommendations using specific method
    async generateMethodRecommendations(userId, method, numRecommendations, filters) {
        try {
            let recommendations = [];

            switch (method.type) {
                case this.recommendationTypes.COLLABORATIVE_USER_BASED:
                    recommendations = this.collaborativeFiltering.userBasedRecommendations(userId, numRecommendations);
                    break;

                case this.recommendationTypes.COLLABORATIVE_ITEM_BASED:
                    recommendations = this.collaborativeFiltering.itemBasedRecommendations(userId, numRecommendations);
                    break;

                case this.recommendationTypes.COLLABORATIVE_HYBRID:
                    recommendations = this.collaborativeFiltering.hybridRecommendations(userId, numRecommendations);
                    break;

                case this.recommendationTypes.CONTENT_BASED:
                    recommendations = this.contentBasedFiltering.generateRecommendations(userId, numRecommendations);
                    break;

                case this.recommendationTypes.POPULARITY_BASED:
                    recommendations = this.getPopularRecommendations(userId, numRecommendations, filters);
                    break;

                case this.recommendationTypes.DIVERSITY_BASED:
                    recommendations = this.getDiverseRecommendations(userId, numRecommendations, filters);
                    break;

                case this.recommendationTypes.TRENDING:
                    recommendations = this.getTrendingRecommendations(userId, numRecommendations, filters);
                    break;

                default:
                    recommendations = [];
            }

            // Apply filters
            recommendations = this.applyFilters(recommendations, filters);

            // Add method metadata
            return recommendations.map(rec => ({
                ...rec,
                method: method.type,
                methodWeight: method.weight,
                originalScore: rec.score
            }));

        } catch (error) {
            winston.error(`Error generating recommendations for method ${method.type}:`, error);
            return [];
        }
    }

    // Combine recommendations from multiple methods
    combineRecommendations(methodResults, userId) {
        const combined = new Map();

        methodResults.forEach(methodResult => {
            methodResult.forEach(recommendation => {
                const contentId = recommendation.contentId;

                if (combined.has(contentId)) {
                    // Update existing recommendation
                    const existing = combined.get(contentId);
                    existing.score += recommendation.score * recommendation.methodWeight;
                    existing.methods.push({
                        type: recommendation.method,
                        weight: recommendation.methodWeight,
                        score: recommendation.originalScore
                    });
                } else {
                    // Add new recommendation
                    combined.set(contentId, {
                        contentId,
                        score: recommendation.score * recommendation.methodWeight,
                        methods: [{
                            type: recommendation.method,
                            weight: recommendation.methodWeight,
                            score: recommendation.originalScore
                        }],
                        type: recommendation.type || 'hybrid',
                        originalRecommendation: recommendation
                    });
                }
            });
        });

        // Convert to array and sort by score
        return Array.from(combined.values())
            .sort((a, b) => b.score - a.score)
            .slice(0, this.maxRecommendations);
    }

    // Apply business rules and diversity
    applyBusinessRules(recommendations, userId, numRecommendations, filters) {
        try {
            // Remove already interacted content
            const userInteractions = this.getUserInteractions(userId);
            const interactedIds = new Set(userInteractions.map(i => i.contentId));

            let filtered = recommendations.filter(rec => !interactedIds.has(rec.contentId));

            // Apply diversity rules
            filtered = this.applyDiversityRules(filtered, numRecommendations);

            // Apply content variety rules
            filtered = this.applyContentVarietyRules(filtered, numRecommendations);

            // Apply business constraints
            filtered = this.applyBusinessConstraints(filtered, filters);

            return filtered.slice(0, numRecommendations);
        } catch (error) {
            winston.error('Error applying business rules:', error);
            return recommendations.slice(0, numRecommendations);
        }
    }

    // Apply diversity rules to ensure variety in recommendations
    applyDiversityRules(recommendations, targetCount) {
        const diverse = [];
        const categoriesUsed = new Set();
        const typesUsed = new Set();

        // First pass: ensure category diversity
        for (const rec of recommendations) {
            const content = this.contents.get(rec.contentId);
            if (!content) continue;

            const category = content.category || 'unknown';
            const type = content.type || 'unknown';

            // If we haven't used this category much, include it
            const categoryCount = Array.from(categoriesUsed).filter(c => c === category).length;
            const typeCount = Array.from(typesUsed).filter(t => t === type).length;

            if (categoryCount < Math.ceil(targetCount * 0.3) && typeCount < Math.ceil(targetCount * 0.4)) {
                diverse.push(rec);
                categoriesUsed.add(category);
                typesUsed.add(type);
            }
        }

        // Second pass: fill remaining slots with highest scoring
        for (const rec of recommendations) {
            if (diverse.length >= targetCount) break;
            if (!diverse.some(d => d.contentId === rec.contentId)) {
                diverse.push(rec);
            }
        }

        return diverse;
    }

    // Apply content variety rules
    applyContentVarietyRules(recommendations, targetCount) {
        // Ensure mix of different content types
        const types = ['spell', 'item', 'monster', 'adventure', 'character', 'rule'];
        const typeDistribution = {};

        // Calculate desired distribution
        types.forEach(type => {
            typeDistribution[type] = Math.ceil(targetCount / types.length);
        });

        const varied = [];
        const typeCounts = {};

        // Distribute by type
        for (const rec of recommendations) {
            const content = this.contents.get(rec.contentId);
            if (!content) continue;

            const contentType = content.type || 'other';
            typeCounts[contentType] = (typeCounts[contentType] || 0) + 1;

            if (typeCounts[contentType] <= (typeDistribution[contentType] || Math.ceil(targetCount / types.length))) {
                varied.push(rec);
            }
        }

        // Fill remaining with highest scoring
        for (const rec of recommendations) {
            if (varied.length >= targetCount) break;
            if (!varied.some(v => v.contentId === rec.contentId)) {
                varied.push(rec);
            }
        }

        return varied;
    }

    // Apply business constraints
    applyBusinessConstraints(recommendations, filters) {
        return recommendations.filter(rec => {
            const content = this.contents.get(rec.contentId);
            if (!content) return false;

            // Apply filters
            if (filters.category && content.category !== filters.category) return false;
            if (filters.type && content.type !== filters.type) return false;
            if (filters.levelMin && content.level < filters.levelMin) return false;
            if (filters.levelMax && content.level > filters.levelMax) return false;
            if (filters.difficultyMin && content.difficulty < filters.difficultyMin) return false;
            if (filters.difficultyMax && content.difficulty > filters.difficultyMax) return false;

            // Business rules
            if (content.status !== 'published') return false;
            if (content.rating < 2.0) return false; // Filter out very low-rated content

            return true;
        });
    }

    // Get popular recommendations
    getPopularRecommendations(userId, numRecommendations, filters) {
        const popular = Array.from(this.contents.values())
            .filter(content => content.status === 'published')
            .sort((a, b) => {
                const scoreA = (a.rating || 0) * 0.7 + (a.downloads || 0) * 0.0003;
                const scoreB = (b.rating || 0) * 0.7 + (b.downloads || 0) * 0.0003;
                return scoreB - scoreA;
            })
            .slice(0, numRecommendations)
            .map(content => ({
                contentId: content._id.toString(),
                score: (content.rating || 0) * 0.7 + (content.downloads || 0) * 0.0003,
                type: 'popularity_based',
                method: 'global_popularity'
            }));

        return this.applyFilters(popular, filters);
    }

    // Get diverse recommendations
    getDiverseRecommendations(userId, numRecommendations, filters) {
        // Get recommendations from different categories
        const categories = [...new Set(
            Array.from(this.contents.values())
                .filter(c => c.status === 'published')
                .map(c => c.category)
                .filter(Boolean)
        )];

        const diverse = [];
        const itemsPerCategory = Math.ceil(numRecommendations / Math.max(categories.length, 1));

        categories.forEach(category => {
            const categoryItems = Array.from(this.contents.values())
                .filter(content => content.category === category && content.status === 'published')
                .sort((a, b) => (b.rating || 0) - (a.rating || 0))
                .slice(0, itemsPerCategory)
                .map(content => ({
                    contentId: content._id.toString(),
                    score: content.rating || 0,
                    type: 'diversity_based',
                    method: 'category_diversity',
                    category: category
                }));

            diverse.push(...categoryItems);
        });

        return this.applyFilters(diverse, filters);
    }

    // Get trending recommendations
    getTrendingRecommendations(userId, numRecommendations, filters) {
        const now = new Date();
        const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

        const trending = Array.from(this.contents.values())
            .filter(content => {
                const createdAt = new Date(content.createdAt);
                return content.status === 'published' && createdAt > oneWeekAgo;
            })
            .sort((a, b) => {
                const scoreA = (a.rating || 0) * 0.5 + (a.downloads || 0) * 0.0005 + (a.likes || 0) * 0.001;
                const scoreB = (b.rating || 0) * 0.5 + (b.downloads || 0) * 0.0005 + (b.likes || 0) * 0.001;
                return scoreB - scoreA;
            })
            .slice(0, numRecommendations)
            .map(content => ({
                contentId: content._id.toString(),
                score: (content.rating || 0) * 0.5 + (content.downloads || 0) * 0.0005 + (content.likes || 0) * 0.001,
                type: 'trending',
                method: 'recent_popularity'
            }));

        return this.applyFilters(trending, filters);
    }

    // Apply filters to recommendations
    applyFilters(recommendations, filters) {
        if (!filters || Object.keys(filters).length === 0) {
            return recommendations;
        }

        return recommendations.filter(rec => {
            const content = this.contents.get(rec.contentId);
            if (!content) return false;

            // Apply each filter
            if (filters.category && content.category !== filters.category) return false;
            if (filters.type && content.type !== filters.type) return false;
            if (filters.levelMin && (content.level || 0) < filters.levelMin) return false;
            if (filters.levelMax && (content.level || 0) > filters.levelMax) return false;
            if (filters.difficultyMin && (content.difficulty || 0) < filters.difficultyMin) return false;
            if (filters.difficultyMax && (content.difficulty || 0) > filters.difficultyMax) return false;
            if (filters.class && (!content.class || !content.class.includes(filters.class))) return false;
            if (filters.school && content.school !== filters.school) return false;
            if (filters.rarity && content.rarity !== filters.rarity) return false;

            return true;
        });
    }

    // Get user interactions
    getUserInteractions(userId) {
        return this.interactions.filter(interaction => interaction.userId === userId);
    }

    // Get fallback recommendations
    getFallbackRecommendations(numRecommendations = 10) {
        return this.getPopularRecommendations(null, numRecommendations, {});
    }

    // Update models with new data
    async updateModels(newInteractions, newContents) {
        try {
            winston.info('Updating hybrid recommendation models...');

            // Update interaction data
            if (newInteractions && newInteractions.length > 0) {
                this.interactions = [...this.interactions, ...newInteractions];

                // Update collaborative filtering
                this.collaborativeFiltering.updateModel(this.interactions);

                // Update content-based user profiles
                const userInteractions = this.groupInteractionsByUser(newInteractions);
                for (const [userId, userInteractionList] of userInteractions) {
                    const existingProfile = this.contentBasedFiltering.userProfiles.get(userId);
                    if (existingProfile) {
                        // Update existing profile
                        const allInteractions = this.getUserInteractions(userId);
                        this.contentBasedFiltering.buildUserProfile(userId, allInteractions);
                    } else {
                        // Create new profile
                        this.contentBasedFiltering.buildUserProfile(userId, userInteractionList);
                    }
                }
            }

            // Update content data
            if (newContents && newContents.length > 0) {
                newContents.forEach(content => {
                    this.contents.set(content._id.toString(), content);
                    this.contentBasedFiltering.updateContentFeatures(content);
                });
            }

            winston.info('Hybrid recommendation models updated successfully');
        } catch (error) {
            winston.error('Error updating hybrid models:', error);
            throw error;
        }
    }

    // Log recommendation generation for analytics
    logRecommendationGeneration(userId, recommendations, methods) {
        const logData = {
            userId,
            timestamp: new Date().toISOString(),
            recommendationCount: recommendations.length,
            methods: methods.map(m => m.type),
            averageScore: recommendations.reduce((sum, rec) => sum + rec.score, 0) / recommendations.length,
            contentTypes: [...new Set(recommendations.map(rec => {
                const content = this.contents.get(rec.contentId);
                return content ? content.type : 'unknown';
            }))]
        };

        winston.debug('Recommendation generation log:', logData);
    }

    // Get recommendation statistics
    getRecommendationStats(userId) {
        const userProfile = this.contentBasedFiltering.userProfiles.get(userId);
        const userInteractions = this.getUserInteractions(userId);

        return {
            interactionCount: userInteractions.length,
            lastInteraction: userInteractions.length > 0 ?
                Math.max(...userInteractions.map(i => new Date(i.timestamp))) : null,
            profileFeatures: userProfile ? userProfile.positiveFeatures.size : 0,
            favoriteCategories: userProfile ?
                Array.from(userProfile.categoryPreferences.entries())
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 3) : [],
            preferredClasses: userProfile ?
                Array.from(userProfile.classPreferences.entries())
                    .sort((a, b) => b[1] - a[1])
                    .slice(0, 3) : []
        };
    }

    // Get model statistics
    getModelStats() {
        return {
            collaborative: this.collaborativeFiltering.getModelStats(),
            contentBased: {
                totalContent: this.contentFeatures.size,
                totalUsers: this.contentBasedFiltering.userProfiles.size,
                averageFeaturesPerContent: Array.from(this.contentBasedFiltering.contentVectors.values())
                    .reduce((sum, vec) => sum + vec.size, 0) / this.contentBasedFiltering.contentVectors.size
            },
            hybrid: {
                totalInteractions: this.interactions.length,
                totalContent: this.contents.size,
                weights: this.weights
            }
        };
    }
}

module.exports = HybridRecommender;