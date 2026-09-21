const { Matrix } = require('ml-matrix');
const winston = require('winston');

class CollaborativeFiltering {
    constructor(options = {}) {
        this.minInteractions = options.minInteractions || 5;
        this.similarityThreshold = options.similarityThreshold || 0.1;
        this.maxNeighbors = options.maxNeighbors || 50;
        this.decayFactor = options.decayFactor || 0.9;
        this.userItemMatrix = null;
        this.userSimilarities = new Map();
        this.itemSimilarities = new Map();
    }

    // Build user-item interaction matrix
    buildMatrix(interactions) {
        try {
            const users = [...new Set(interactions.map(i => i.userId))];
            const items = [...new Set(interactions.map(i => i.contentId))];

            this.userIndex = new Map(users.map((user, i) => [user, i]));
            this.itemIndex = new Map(items.map((item, i) => [item, i]));

            const matrix = new Matrix(users.length, items.length);

            interactions.forEach(interaction => {
                const userIdx = this.userIndex.get(interaction.userId);
                const itemIdx = this.itemIndex.get(interaction.contentId);

                // Weight interactions by type and recency
                const weight = this.getInteractionWeight(interaction);
                matrix.set(userIdx, itemIdx, weight);
            });

            this.userItemMatrix = matrix;
            this.users = users;
            this.items = items;

            winston.info(`Built user-item matrix: ${users.length} users, ${items.length} items`);
            return matrix;

        } catch (error) {
            winston.error('Error building user-item matrix:', error);
            throw error;
        }
    }

    // Calculate interaction weight based on type and recency
    getInteractionWeight(interaction) {
        const typeWeights = {
            'view': 1,
            'like': 2,
            'save': 3,
            'share': 4,
            'comment': 3,
            'rating_5': 5,
            'rating_4': 4,
            'rating_3': 3,
            'rating_2': 2,
            'rating_1': 1,
            'purchase': 5,
            'play': 4
        };

        let weight = typeWeights[interaction.action] || 1;

        // Apply time decay
        if (interaction.timestamp) {
            const daysSinceInteraction = (Date.now() - new Date(interaction.timestamp).getTime()) / (1000 * 60 * 60 * 24);
            weight *= Math.pow(this.decayFactor, daysSinceInteraction / 30); // Monthly decay
        }

        return weight;
    }

    // Calculate user similarity using cosine similarity
    calculateUserSimilarities() {
        try {
            const numUsers = this.users.length;
            this.userSimilarities.clear();

            for (let i = 0; i < numUsers; i++) {
                const similarities = [];
                const userVector = this.userItemMatrix.getRow(i);

                for (let j = 0; j < numUsers; j++) {
                    if (i === j) continue;

                    const otherVector = this.userItemMatrix.getRow(j);
                    const similarity = this.cosineSimilarity(userVector, otherVector);

                    if (similarity > this.similarityThreshold) {
                        similarities.push({
                            userId: this.users[j],
                            similarity: similarity
                        });
                    }
                }

                // Sort by similarity and keep top neighbors
                similarities.sort((a, b) => b.similarity - a.similarity);
                this.userSimilarities.set(this.users[i], similarities.slice(0, this.maxNeighbors));
            }

            winston.info(`Calculated similarities for ${numUsers} users`);
        } catch (error) {
            winston.error('Error calculating user similarities:', error);
            throw error;
        }
    }

    // Calculate item similarity using adjusted cosine similarity
    calculateItemSimilarities() {
        try {
            const numItems = this.items.length;
            this.itemSimilarities.clear();

            for (let i = 0; i < numItems; i++) {
                const similarities = [];
                const itemColumn = this.userItemMatrix.getColumn(i);

                for (let j = 0; j < numItems; j++) {
                    if (i === j) continue;

                    const otherColumn = this.userItemMatrix.getColumn(j);
                    const similarity = this.adjustedCosineSimilarity(itemColumn, otherColumn);

                    if (similarity > this.similarityThreshold) {
                        similarities.push({
                            itemId: this.items[j],
                            similarity: similarity
                        });
                    }
                }

                similarities.sort((a, b) => b.similarity - a.similarity);
                this.itemSimilarities.set(this.items[i], similarities.slice(0, this.maxNeighbors));
            }

            winston.info(`Calculated similarities for ${numItems} items`);
        } catch (error) {
            winston.error('Error calculating item similarities:', error);
            throw error;
        }
    }

    // Cosine similarity between two vectors
    cosineSimilarity(vec1, vec2) {
        let dotProduct = 0;
        let norm1 = 0;
        let norm2 = 0;

        for (let i = 0; i < vec1.length; i++) {
            dotProduct += vec1[i] * vec2[i];
            norm1 += vec1[i] * vec1[i];
            norm2 += vec2[i] * vec2[i];
        }

        if (norm1 === 0 || norm2 === 0) return 0;

        return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
    }

    // Adjusted cosine similarity (accounts for user rating bias)
    adjustedCosineSimilarity(col1, col2) {
        let numerator = 0;
        let sumSq1 = 0;
        let sumSq2 = 0;
        let commonUsers = 0;

        for (let i = 0; i < col1.length; i++) {
            if (col1[i] > 0 && col2[i] > 0) {
                const userMean = this.getUserMean(i);
                const diff1 = col1[i] - userMean;
                const diff2 = col2[i] - userMean;

                numerator += diff1 * diff2;
                sumSq1 += diff1 * diff1;
                sumSq2 += diff2 * diff2;
                commonUsers++;
            }
        }

        if (commonUsers < 2 || sumSq1 === 0 || sumSq2 === 0) return 0;

        return numerator / (Math.sqrt(sumSq1) * Math.sqrt(sumSq2));
    }

    // Get mean rating for a user
    getUserMean(userIdx) {
        const userVector = this.userItemMatrix.getRow(userIdx);
        const ratedItems = userVector.filter(rating => rating > 0);

        if (ratedItems.length === 0) return 0;
        return ratedItems.reduce((sum, rating) => sum + rating, 0) / ratedItems.length;
    }

    // User-based collaborative filtering recommendations
    userBasedRecommendations(userId, numRecommendations = 10) {
        try {
            if (!this.userIndex.has(userId)) {
                return this.getColdStartRecommendations(numRecommendations);
            }

            const userSimilarities = this.userSimilarities.get(userId);
            if (!userSimilarities || userSimilarities.length === 0) {
                return this.getPopularItemsRecommendations(userId, numRecommendations);
            }

            const userIdx = this.userIndex.get(userId);
            const userVector = this.userItemMatrix.getRow(userIdx);
            const recommendations = new Map();

            userSimilarities.forEach(({ userId: similarUserId, similarity }) => {
                const similarUserIdx = this.userIndex.get(similarUserId);
                const similarUserVector = this.userItemMatrix.getRow(similarUserIdx);

                for (let itemIdx = 0; itemIdx < userVector.length; itemIdx++) {
                    if (userVector[itemIdx] === 0 && similarUserVector[itemIdx] > 0) {
                        const itemId = this.items[itemIdx];
                        const weightedRating = similarity * similarUserVector[itemIdx];

                        recommendations.set(itemId,
                            (recommendations.get(itemId) || 0) + weightedRating);
                    }
                }
            });

            // Sort by score and return top recommendations
            const sortedRecommendations = Array.from(recommendations.entries())
                .sort((a, b) => b[1] - a[1])
                .slice(0, numRecommendations)
                .map(([itemId, score]) => ({
                    contentId: itemId,
                    score: score,
                    type: 'collaborative_filtering',
                    method: 'user_based'
                }));

            return sortedRecommendations;

        } catch (error) {
            winston.error('Error generating user-based recommendations:', error);
            return this.getColdStartRecommendations(numRecommendations);
        }
    }

    // Item-based collaborative filtering recommendations
    itemBasedRecommendations(userId, numRecommendations = 10) {
        try {
            if (!this.userIndex.has(userId)) {
                return this.getColdStartRecommendations(numRecommendations);
            }

            const userIdx = this.userIndex.get(userId);
            const userVector = this.userItemMatrix.getRow(userIdx);
            const recommendations = new Map();

            // For each item the user has interacted with
            for (let itemIdx = 0; itemIdx < userVector.length; itemIdx++) {
                if (userVector[itemIdx] > 0) {
                    const itemId = this.items[itemIdx];
                    const itemSimilarities = this.itemSimilarities.get(itemId);

                    if (itemSimilarities) {
                        itemSimilarities.forEach(({ itemId: similarItemId, similarity }) => {
                            const similarItemIdx = this.itemIndex.get(similarItemId);

                            if (userVector[similarItemIdx] === 0) {
                                const weightedScore = similarity * userVector[itemIdx];

                                recommendations.set(similarItemId,
                                    (recommendations.get(similarItemId) || 0) + weightedScore);
                            }
                        });
                    }
                }
            }

            const sortedRecommendations = Array.from(recommendations.entries())
                .sort((a, b) => b[1] - a[1])
                .slice(0, numRecommendations)
                .map(([itemId, score]) => ({
                    contentId: itemId,
                    score: score,
                    type: 'collaborative_filtering',
                    method: 'item_based'
                }));

            return sortedRecommendations;

        } catch (error) {
            winston.error('Error generating item-based recommendations:', error);
            return this.getColdStartRecommendations(numRecommendations);
        }
    }

    // Hybrid approach combining user-based and item-based
    hybridRecommendations(userId, numRecommendations = 10, userWeight = 0.6) {
        try {
            const userBased = this.userBasedRecommendations(userId, numRecommendations * 2);
            const itemBased = this.itemBasedRecommendations(userId, numRecommendations * 2);

            const combined = new Map();

            // Add user-based recommendations
            userBased.forEach(rec => {
                combined.set(rec.contentId, {
                    ...rec,
                    score: rec.score * userWeight
                });
            });

            // Add item-based recommendations
            itemBased.forEach(rec => {
                if (combined.has(rec.contentId)) {
                    const existing = combined.get(rec.contentId);
                    existing.score += rec.score * (1 - userWeight);
                    existing.method = 'hybrid';
                } else {
                    combined.set(rec.contentId, {
                        ...rec,
                        score: rec.score * (1 - userWeight)
                    });
                }
            });

            return Array.from(combined.values())
                .sort((a, b) => b.score - a.score)
                .slice(0, numRecommendations);

        } catch (error) {
            winston.error('Error generating hybrid recommendations:', error);
            return this.getColdStartRecommendations(numRecommendations);
        }
    }

    // Cold start problem solution
    getColdStartRecommendations(numRecommendations = 10) {
        // Return popular items as default
        return this.getPopularItemsRecommendations(null, numRecommendations);
    }

    getPopularItemsRecommendations(userId, numRecommendations = 10) {
        try {
            const itemPopularity = new Map();

            // Calculate popularity based on total interactions
            for (let itemIdx = 0; itemIdx < this.items.length; itemIdx++) {
                const column = this.userItemMatrix.getColumn(itemIdx);
                const totalScore = column.reduce((sum, val) => sum + val, 0);
                const interactionCount = column.filter(val => val > 0).length;

                itemPopularity.set(this.items[itemIdx], {
                    totalScore,
                    interactionCount,
                    avgScore: interactionCount > 0 ? totalScore / interactionCount : 0
                });
            }

            return Array.from(itemPopularity.entries())
                .sort((a, b) => {
                    // Sort by combination of total score and average score
                    const scoreA = a[1].totalScore * 0.7 + a[1].avgScore * a[1].interactionCount * 0.3;
                    const scoreB = b[1].totalScore * 0.7 + b[1].avgScore * b[1].interactionCount * 0.3;
                    return scoreB - scoreA;
                })
                .slice(0, numRecommendations)
                .map(([itemId, stats]) => ({
                    contentId: itemId,
                    score: stats.totalScore,
                    type: 'popularity_based',
                    method: 'cold_start',
                    stats: stats
                }));

        } catch (error) {
            winston.error('Error generating popularity-based recommendations:', error);
            return [];
        }
    }

    // Update model with new interactions
    updateModel(newInteractions) {
        try {
            // Rebuild matrix periodically or use incremental updates
            // For now, rebuild completely
            this.buildMatrix(newInteractions);
            this.calculateUserSimilarities();
            this.calculateItemSimilarities();

            winston.info('Model updated with new interactions');
        } catch (error) {
            winston.error('Error updating model:', error);
            throw error;
        }
    }

    // Get model statistics
    getModelStats() {
        if (!this.userItemMatrix) return null;

        const stats = {
            totalUsers: this.users.length,
            totalItems: this.items.length,
            totalInteractions: 0,
            sparsity: 0,
            avgInteractionsPerUser: 0,
            avgInteractionsPerItem: 0
        };

        let interactionCount = 0;
        for (let i = 0; i < this.userItemMatrix.rows; i++) {
            for (let j = 0; j < this.userItemMatrix.columns; j++) {
                if (this.userItemMatrix.get(i, j) > 0) {
                    interactionCount++;
                }
            }
        }

        stats.totalInteractions = interactionCount;
        stats.sparsity = 1 - (interactionCount / (this.users.length * this.items.length));
        stats.avgInteractionsPerUser = interactionCount / this.users.length;
        stats.avgInteractionsPerItem = interactionCount / this.items.length;

        return stats;
    }
}

module.exports = CollaborativeFiltering;