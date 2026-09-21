const winston = require('winston');

class PersonalizationEngine {
    constructor(redisClient, hybridRecommender) {
        this.redisClient = redisClient;
        this.hybridRecommender = hybridRecommender;
        this.userProfiles = new Map();
        this.behaviorTracking = this.initializeBehaviorTracking();
        this.learningAlgorithms = this.initializeLearningAlgorithms();
        this.adaptationStrategies = this.initializeAdaptationStrategies();
        this.segmentationModel = this.initializeSegmentationModel();
    }

    // Initialize behavior tracking
    initializeBehaviorTracking() {
        return {
            trackedActions: [
                'view', 'like', 'dislike', 'save', 'unsave', 'share',
                'download', 'comment', 'rating', 'purchase', 'play',
                'bookmark', 'report', 'recommend', 'follow', 'unsubscribe'
            ],
            engagementMetrics: {
                sessionDuration: 'time_on_page',
                scrollDepth: 'scroll_completion',
                interactionFrequency: 'actions_per_session',
                returnVisits: 'return_rate',
                contentCompletion: 'completion_rate'
            },
            contextData: {
                timeOfDay: 'hour_of_day',
                dayOfWeek: 'day_of_week',
                deviceType: 'device_type',
                location: 'geographic_region',
                referrer: 'traffic_source',
                campaign: 'marketing_campaign'
            },
            weightDecay: {
                hourly: 0.95,
                daily: 0.8,
                weekly: 0.6,
                monthly: 0.3
            }
        };
    }

    // Initialize learning algorithms
    initializeLearningAlgorithms() {
        return {
            multiArmedBandit: {
                algorithm: 'thompson_sampling',
                explorationRate: 0.15,
                updateFrequency: 'real_time',
                confidenceInterval: 0.95
            },
            onlineLearning: {
                algorithm: 'stochastic_gradient_descent',
                learningRate: 0.01,
                momentum: 0.9,
                batchSize: 32,
                adaptationWindow: 1000
            },
            reinforcementLearning: {
                algorithm: 'q_learning',
                discountFactor: 0.95,
                explorationRate: 0.1,
                learningRate: 0.001,
                memoryReplay: true,
                experienceReplaySize: 10000
            },
            collaborativeUpdate: {
                algorithm: 'incremental_svd',
                regularization: 0.01,
                learningRate: 0.001,
                updateThreshold: 10,
                forgetFactor: 0.99
            }
        };
    }

    // Initialize adaptation strategies
    initializeAdaptationStrategies() {
        return {
            coldStart: {
                strategy: 'popularity_based',
                fallbackMechanisms: ['demographic', 'content_based', 'global_trends'],
                bootstrapMethods: ['onboarding_survey', 'initial_interactions', 'social_connections']
            },
            newItem: {
                strategy: 'content_based',
                featureExtraction: 'nlp_analysis',
                similarityThreshold: 0.3,
                promotionStrategy: 'gradual_exposure'
            },
            userDrift: {
                detectionMethod: 'behavior_change_analysis',
                adaptationSpeed: 'gradual',
                driftThreshold: 0.25,
                resetStrategy: 'partial_profile_update'
            },
            feedbackLoop: {
                positiveFeedback: ['like', 'save', 'share', 'high_rating'],
                negativeFeedback: ['dislike', 'report', 'unsave', 'low_rating'],
                implicitSignals: ['time_spent', 'return_visits', 'completion_rate'],
                adaptationSpeed: 'immediate_for_strong_signals'
            }
        };
    }

    // Initialize segmentation model
    initializeSegmentationModel() {
        return {
            behavioral: {
                powerUsers: { criteria: { sessions_per_week: 5, avg_session_duration: 60 } },
                casualUsers: { criteria: { sessions_per_week: 1, avg_session_duration: 20 } },
                newUsers: { criteria: { account_age_days: 30 } },
                dormantUsers: { criteria: { days_since_last_activity: 90 } }
            },
            content: {
                adventureLovers: { preferences: ['adventure', 'campaign', 'story'] },
                characterBuilders: { preferences: ['character', 'build', 'optimization'] },
                dms: { preferences: ['dm_tools', 'encounters', 'npcs'] },
                homebrewers: { preferences: ['homebrew', 'custom_content', 'tools'] }
            },
            engagement: {
                highlyEngaged: { criteria: { interaction_rate: 0.8, return_rate: 0.9 } },
                moderatelyEngaged: { criteria: { interaction_rate: 0.4, return_rate: 0.6 } },
                lowlyEngaged: { criteria: { interaction_rate: 0.1, return_rate: 0.2 } }
            },
            temporal: {
                weekendWarriors: { peak_times: ['saturday', 'sunday'] },
                weekdayPlayers: { peak_times: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'] },
                nightOwls: { peak_hours: [20, 21, 22, 23, 0, 1, 2] },
                earlyBirds: { peak_hours: [6, 7, 8, 9, 10, 11] }
            }
        };
    }

    // Track user behavior
    async trackUserBehavior(userId, behaviorData) {
        try {
            const timestamp = new Date().toISOString();
            const behavior = {
                userId,
                timestamp,
                action: behaviorData.action,
                contentId: behaviorData.contentId,
                contentType: behaviorData.contentType,
                metadata: behaviorData.metadata || {},
                context: this.captureContext(behaviorData.context),
                sessionId: behaviorData.sessionId
            };

            // Validate behavior
            if (!this.isValidBehavior(behavior)) {
                winston.warn(`Invalid behavior data for user ${userId}:`, behavior);
                return false;
            }

            // Store behavior in Redis for real-time processing
            await this.redisClient.trackBehavior(userId, behavior);

            // Update user profile
            await this.updateUserProfile(userId, behavior);

            // Update bandit statistics if applicable
            if (behaviorData.armId) {
                await this.updateBanditStats(behaviorData.armId, behavior);
            }

            // Trigger real-time adaptations
            await this.triggerRealTimeAdaptations(userId, behavior);

            winston.debug(`Tracked behavior for user ${userId}: ${behavior.action} on ${behavior.contentId}`);
            return true;

        } catch (error) {
            winston.error('Error tracking user behavior:', error);
            return false;
        }
    }

    // Validate behavior data
    isValidBehavior(behavior) {
        return this.behaviorTracking.trackedActions.includes(behavior.action) &&
               behavior.userId &&
               behavior.contentId &&
               behavior.timestamp;
    }

    // Capture context information
    captureContext(contextData = {}) {
        const context = {
            timestamp: new Date(),
            timeOfDay: new Date().getHours(),
            dayOfWeek: new Date().getDay(),
            userAgent: contextData.userAgent,
            ipAddress: contextData.ipAddress,
            referrer: contextData.referrer,
            sessionId: contextData.sessionId
        };

        // Extract device type from user agent
        if (context.userAgent) {
            context.deviceType = this.detectDeviceType(context.userAgent);
        }

        return context;
    }

    // Detect device type from user agent
    detectDeviceType(userAgent) {
        const ua = userAgent.toLowerCase();
        if (ua.includes('mobile') || ua.includes('android') || ua.includes('iphone')) {
            return 'mobile';
        } else if (ua.includes('tablet') || ua.includes('ipad')) {
            return 'tablet';
        } else {
            return 'desktop';
        }
    }

    // Update user profile
    async updateUserProfile(userId, behavior) {
        try {
            let profile = await this.getUserProfile(userId);

            if (!profile) {
                profile = this.createInitialProfile(userId, behavior);
            }

            // Update behavior history
            profile.behaviorHistory.push(behavior);
            if (profile.behaviorHistory.length > 1000) {
                profile.behaviorHistory = profile.behaviorHistory.slice(-1000);
            }

            // Update preferences based on behavior
            await this.updatePreferences(profile, behavior);

            // Update interaction patterns
            await this.updateInteractionPatterns(profile, behavior);

            // Update temporal patterns
            await this.updateTemporalPatterns(profile, behavior);

            // Update segmentation
            await this.updateUserSegmentation(profile);

            // Save updated profile
            await this.saveUserProfile(userId, profile);

            // Update in-memory cache
            this.userProfiles.set(userId, profile);

        } catch (error) {
            winston.error('Error updating user profile:', error);
        }
    }

    // Get user profile
    async getUserProfile(userId) {
        // Check in-memory cache first
        if (this.userProfiles.has(userId)) {
            return this.userProfiles.get(userId);
        }

        // Load from Redis or database
        const cachedProfile = await this.redisClient.get(`profile:${userId}`);
        if (cachedProfile) {
            const profile = JSON.parse(cachedProfile);
            this.userProfiles.set(userId, profile);
            return profile;
        }

        return null;
    }

    // Create initial profile
    createInitialProfile(userId, behavior) {
        return {
            userId,
            createdAt: new Date().toISOString(),
            lastUpdated: new Date().toISOString(),
            behaviorHistory: [],
            preferences: {
                categories: {},
                contentTypes: {},
                tags: {},
                difficulty: 'medium',
                sessionLength: 'medium',
                interactionStyle: 'moderate'
            },
            interactionPatterns: {
                peakHours: {},
                peakDays: {},
                devicePreferences: {},
                sessionDuration: [],
                actionsPerSession: []
            },
            temporalPatterns: {
                weeklyActivity: new Array(7).fill(0),
                hourlyActivity: new Array(24).fill(0),
                monthlyTrends: {}
            },
            segmentation: {
                behavioral: 'new_user',
                content: 'undetermined',
                engagement: 'low',
                temporal: 'undetermined'
            },
            stats: {
                totalSessions: 0,
                totalInteractions: 0,
                averageSessionDuration: 0,
                returnRate: 0,
                interactionRate: 0
            },
            adaptationState: {
                coldStartCompleted: false,
                lastAdaptation: null,
                adaptationHistory: []
            }
        };
    }

    // Update preferences based on behavior
    async updatePreferences(profile, behavior) {
        const weight = this.getBehaviorWeight(behavior.action);
        const decay = this.getTimeDecay(behavior.timestamp);

        // Update category preferences
        if (behavior.metadata?.category) {
            const category = behavior.metadata.category;
            profile.preferences.categories[category] =
                (profile.preferences.categories[category] || 0) + (weight * decay);
        }

        // Update content type preferences
        if (behavior.contentType) {
            profile.preferences.contentTypes[behavior.contentType] =
                (profile.preferences.contentTypes[behavior.contentType] || 0) + (weight * decay);
        }

        // Update tag preferences
        if (behavior.metadata?.tags) {
            behavior.metadata.tags.forEach(tag => {
                profile.preferences.tags[tag] =
                    (profile.preferences.tags[tag] || 0) + (weight * decay);
            });
        }

        // Update difficulty preference based on content difficulty
        if (behavior.metadata?.difficulty) {
            profile.preferences.difficulty = this.adjustDifficultyPreference(
                profile.preferences.difficulty, behavior.metadata.difficulty, behavior.action
            );
        }

        // Update session length preference
        const sessionDuration = behavior.metadata?.sessionDuration;
        if (sessionDuration) {
            profile.interactionPatterns.sessionDuration.push(sessionDuration);
            if (profile.interactionPatterns.sessionDuration.length > 50) {
                profile.interactionPatterns.sessionDuration =
                    profile.interactionPatterns.sessionDuration.slice(-50);
            }
        }

        profile.lastUpdated = new Date().toISOString();
    }

    // Get behavior weight
    getBehaviorWeight(action) {
        const weights = {
            view: 1,
            like: 5,
            dislike: -3,
            save: 8,
            unsave: -5,
            share: 10,
            download: 7,
            comment: 6,
            rating_5: 10,
            rating_4: 8,
            rating_3: 5,
            rating_2: 2,
            rating_1: -5,
            purchase: 12,
            play: 9,
            bookmark: 7,
            report: -10,
            recommend: 15,
            follow: 8,
            unsubscribe: -12
        };

        return weights[action] || 1;
    }

    // Get time decay factor
    getTimeDecay(timestamp) {
        const now = new Date();
        const behaviorTime = new Date(timestamp);
        const hoursDiff = (now - behaviorTime) / (1000 * 60 * 60);

        if (hoursDiff < 1) return this.behaviorTracking.weightDecay.hourly;
        if (hoursDiff < 24) return this.behaviorTracking.weightDecay.daily;
        if (hoursDiff < 168) return this.behaviorTracking.weightDecay.weekly;
        return this.behaviorTracking.weightDecay.monthly;
    }

    // Adjust difficulty preference
    adjustDifficultyPreference(currentPreference, contentDifficulty, action) {
        const isPositiveAction = ['like', 'save', 'share', 'rating_4', 'rating_5'].includes(action);
        const isNegativeAction = ['dislike', 'report', 'rating_1', 'rating_2'].includes(action);

        if (!isPositiveAction && !isNegativeAction) return currentPreference;

        const difficultyLevels = ['easy', 'medium', 'hard', 'expert'];
        const currentIndex = difficultyLevels.indexOf(currentPreference);
        const contentIndex = difficultyLevels.indexOf(contentDifficulty);

        if (isPositiveAction && Math.abs(currentIndex - contentIndex) <= 1) {
            // User likes content at or near their current level
            return currentPreference;
        } else if (isPositiveAction && contentIndex > currentIndex) {
            // User likes harder content, consider increasing
            return difficultyLevels[Math.min(currentIndex + 1, difficultyLevels.length - 1)];
        } else if (isNegativeAction && contentIndex > currentIndex) {
            // User dislikes harder content, consider decreasing
            return difficultyLevels[Math.max(currentIndex - 1, 0)];
        }

        return currentPreference;
    }

    // Update interaction patterns
    async updateInteractionPatterns(profile, behavior) {
        const hour = behavior.context?.timeOfDay || new Date(behavior.timestamp).getHours();
        const dayOfWeek = behavior.context?.dayOfWeek || new Date(behavior.timestamp).getDay();
        const deviceType = behavior.context?.deviceType || 'unknown';

        // Update peak hours
        profile.interactionPatterns.peakHours[hour] =
            (profile.interactionPatterns.peakHours[hour] || 0) + 1;

        // Update peak days
        profile.interactionPatterns.peakDays[dayOfWeek] =
            (profile.interactionPatterns.peakDays[dayOfWeek] || 0) + 1;

        // Update device preferences
        profile.interactionPatterns.devicePreferences[deviceType] =
            (profile.interactionPatterns.devicePreferences[deviceType] || 0) + 1;

        // Update actions per session
        if (behavior.sessionId) {
            if (!profile.currentSessionActions) {
                profile.currentSessionActions = 0;
            }
            profile.currentSessionActions += 1;
        }
    }

    // Update temporal patterns
    async updateTemporalPatterns(profile, behavior) {
        const date = new Date(behavior.timestamp);
        const hour = date.getHours();
        const dayOfWeek = date.getDay();
        const month = date.getMonth();

        // Update hourly activity
        profile.temporalPatterns.hourlyActivity[hour] += 1;

        // Update weekly activity
        profile.temporalPatterns.weeklyActivity[dayOfWeek] += 1;

        // Update monthly trends
        const monthKey = `${date.getFullYear()}-${month}`;
        profile.temporalPatterns.monthlyTrends[monthKey] =
            (profile.temporalPatterns.monthlyTrends[monthKey] || 0) + 1;
    }

    // Update user segmentation
    async updateUserSegmentation(profile) {
        // Behavioral segmentation
        profile.segmentation.behavioral = this.classifyBehavioralSegment(profile);

        // Content segmentation
        profile.segmentation.content = this.classifyContentSegment(profile);

        // Engagement segmentation
        profile.segmentation.engagement = this.classifyEngagementSegment(profile);

        // Temporal segmentation
        profile.segmentation.temporal = this.classifyTemporalSegment(profile);
    }

    // Classify behavioral segment
    classifyBehavioralSegment(profile) {
        const daysSinceCreation = (Date.now() - new Date(profile.createdAt).getTime()) /
                                (1000 * 60 * 60 * 24);

        if (daysSinceCreation < 7) return 'new_user';
        if (daysSinceCreation < 30) return 'returning_user';

        const avgSessionsPerWeek = this.calculateAvgSessionsPerWeek(profile);
        if (avgSessionsPerWeek >= 5) return 'power_user';
        if (avgSessionsPerWeek >= 2) return 'regular_user';
        if (avgSessionsPerWeek >= 0.5) return 'casual_user';

        return 'dormant_user';
    }

    // Classify content segment
    classifyContentSegment(profile) {
        const preferences = profile.preferences;
        const contentTypes = Object.entries(preferences.contentTypes || {});

        if (contentTypes.length === 0) return 'undetermined';

        // Find dominant content type
        const dominantType = contentTypes.sort((a, b) => b[1] - a[1])[0][0];

        const typeMappings = {
            'adventure': 'adventure_lover',
            'character': 'character_builder',
            'spell': 'spell_collector',
            'monster': 'monster_hunter',
            'item': 'equipment_enthusiast',
            'npc': 'dm_helper',
            'homebrew': 'homebrewer'
        };

        return typeMappings[dominantType] || 'general_enthusiast';
    }

    // Classify engagement segment
    classifyEngagementSegment(profile) {
        const interactionRate = this.calculateInteractionRate(profile);
        const returnRate = this.calculateReturnRate(profile);

        if (interactionRate > 0.8 && returnRate > 0.8) return 'highly_engaged';
        if (interactionRate > 0.4 && returnRate > 0.5) return 'moderately_engaged';
        if (interactionRate > 0.1 && returnRate > 0.2) return 'lowly_engaged';
        return 'minimally_engaged';
    }

    // Classify temporal segment
    classifyTemporalSegment(profile) {
        const hourlyActivity = profile.temporalPatterns.hourlyActivity;
        const weeklyActivity = profile.temporalPatterns.weeklyActivity;

        // Find peak hours
        const peakHours = hourlyActivity
            .map((activity, hour) => ({ hour, activity }))
            .sort((a, b) => b.activity - a.activity)
            .slice(0, 3)
            .map(item => item.hour);

        // Find peak days
        const peakDays = weeklyActivity
            .map((activity, day) => ({ day, activity }))
            .sort((a, b) => b.activity - a.activity)
            .slice(0, 2)
            .map(item => item.day);

        // Classify based on patterns
        const hasWeekendPeak = peakDays.some(day => day === 0 || day === 6);
        const hasNightPeak = peakHours.some(hour => hour >= 20 || hour <= 2);
        const hasMorningPeak = peakHours.some(hour => hour >= 6 && hour <= 11);

        if (hasWeekendPeak) return 'weekend_warrior';
        if (hasNightPeak) return 'night_owl';
        if (hasMorningPeak) return 'early_bird';
        return 'regular_scheduler';
    }

    // Calculate average sessions per week
    calculateAvgSessionsPerWeek(profile) {
        const daysSinceCreation = Math.max(1, (Date.now() - new Date(profile.createdAt).getTime()) /
                                           (1000 * 60 * 60 * 24));
        const weeksSinceCreation = daysSinceCreation / 7;

        return (profile.stats.totalSessions || 0) / weeksSinceCreation;
    }

    // Calculate interaction rate
    calculateInteractionRate(profile) {
        const totalPossible = profile.stats.totalSessions * 10; // Assume 10 interactions per session
        return totalPossible > 0 ? (profile.stats.totalInteractions || 0) / totalPossible : 0;
    }

    // Calculate return rate
    calculateReturnRate(profile) {
        // Simplified calculation based on session patterns
        const uniqueDays = new Set(profile.behaviorHistory.map(b =>
            new Date(b.timestamp).toDateString()
        )).size;

        const totalDays = Math.max(1, (Date.now() - new Date(profile.createdAt).getTime()) /
                                 (1000 * 60 * 60 * 24));

        return uniqueDays / totalDays;
    }

    // Save user profile
    async saveUserProfile(userId, profile) {
        try {
            // Save to Redis with 24 hour expiration
            await this.redisClient.setEx(`profile:${userId}`, 86400, JSON.stringify(profile));

            // Update in-memory cache
            this.userProfiles.set(userId, profile);

        } catch (error) {
            winston.error('Error saving user profile:', error);
        }
    }

    // Update bandit statistics
    async updateBanditStats(armId, behavior) {
        const reward = this.calculateReward(behavior);
        await this.redisClient.updateBanditStats(armId, reward);
    }

    // Calculate reward for bandit
    calculateReward(behavior) {
        const positiveActions = ['like', 'save', 'share', 'rating_4', 'rating_5', 'purchase'];
        const negativeActions = ['dislike', 'report', 'rating_1', 'rating_2'];

        if (positiveActions.includes(behavior.action)) {
            return 1.0;
        } else if (negativeActions.includes(behavior.action)) {
            return -1.0;
        } else {
            return 0.1; // Small positive reward for neutral actions
        }
    }

    // Trigger real-time adaptations
    async triggerRealTimeAdaptations(userId, behavior) {
        try {
            const profile = await this.getUserProfile(userId);
            if (!profile) return;

            // Check for cold start completion
            if (!profile.adaptationState.coldStartCompleted) {
                await this.checkColdStartCompletion(userId, profile);
            }

            // Check for user drift
            await this.checkUserDrift(userId, profile, behavior);

            // Update personalization parameters
            await this.updatePersonalizationParameters(userId, profile, behavior);

        } catch (error) {
            winston.error('Error triggering real-time adaptations:', error);
        }
    }

    // Check cold start completion
    async checkColdStartCompletion(userId, profile) {
        const minInteractions = 20;
        const minDays = 7;

        const interactionsCount = profile.behaviorHistory.length;
        const daysSinceCreation = (Date.now() - new Date(profile.createdAt).getTime()) /
                                 (1000 * 60 * 60 * 24);

        if (interactionsCount >= minInteractions && daysSinceCreation >= minDays) {
            profile.adaptationState.coldStartCompleted = true;
            await this.saveUserProfile(userId, profile);

            winston.info(`Cold start completed for user ${userId}`);
        }
    }

    // Check for user drift
    async checkUserDrift(userId, profile, behavior) {
        const recentBehavior = profile.behaviorHistory.slice(-10);
        const olderBehavior = profile.behaviorHistory.slice(-50, -10);

        if (recentBehavior.length < 5 || olderBehavior.length < 5) return;

        const recentPattern = this.extractBehaviorPattern(recentBehavior);
        const olderPattern = this.extractBehaviorPattern(olderBehavior);

        const drift = this.calculateBehaviorDrift(recentPattern, olderPattern);

        if (drift > this.adaptationStrategies.userDrift.driftThreshold) {
            await this.adaptToUserDrift(userId, profile, drift);
        }
    }

    // Extract behavior pattern
    extractBehaviorPattern(behaviors) {
        const pattern = {
            actionDistribution: {},
            categoryDistribution: {},
            timeDistribution: {},
            averageRating: 0,
            interactionFrequency: 0
        };

        behaviors.forEach(behavior => {
            // Action distribution
            pattern.actionDistribution[behavior.action] =
                (pattern.actionDistribution[behavior.action] || 0) + 1;

            // Category distribution
            if (behavior.metadata?.category) {
                pattern.categoryDistribution[behavior.metadata.category] =
                    (pattern.categoryDistribution[behavior.metadata.category] || 0) + 1;
            }

            // Time distribution
            const hour = new Date(behavior.timestamp).getHours();
            pattern.timeDistribution[hour] = (pattern.timeDistribution[hour] || 0) + 1;

            // Rating
            if (behavior.action.startsWith('rating_')) {
                const rating = parseInt(behavior.action.split('_')[1]);
                pattern.averageRating = (pattern.averageRating + rating) / 2;
            }
        });

        pattern.interactionFrequency = behaviors.length;

        return pattern;
    }

    // Calculate behavior drift
    calculateBehaviorDrift(recentPattern, olderPattern) {
        let drift = 0;
        let factors = 0;

        // Compare action distributions
        const allActions = new Set([
            ...Object.keys(recentPattern.actionDistribution),
            ...Object.keys(olderPattern.actionDistribution)
        ]);

        allActions.forEach(action => {
            const recentCount = recentPattern.actionDistribution[action] || 0;
            const olderCount = olderPattern.actionDistribution[action] || 0;
            const recentTotal = Object.values(recentPattern.actionDistribution).reduce((a, b) => a + b, 0);
            const olderTotal = Object.values(olderPattern.actionDistribution).reduce((a, b) => a + b, 0);

            if (recentTotal > 0 && olderTotal > 0) {
                const recentFreq = recentCount / recentTotal;
                const olderFreq = olderCount / olderTotal;
                drift += Math.abs(recentFreq - olderFreq);
                factors++;
            }
        });

        // Compare rating changes
        const ratingDiff = Math.abs(recentPattern.averageRating - olderPattern.averageRating);
        drift += ratingDiff / 5; // Normalize by max rating
        factors++;

        return factors > 0 ? drift / factors : 0;
    }

    // Adapt to user drift
    async adaptToUserDrift(userId, profile, drift) {
        // Create adaptation record
        const adaptation = {
            timestamp: new Date().toISOString(),
            type: 'user_drift',
            drift: drift,
            strategy: this.adaptationStrategies.userDrift.resetStrategy
        };

        profile.adaptationState.adaptationHistory.push(adaptation);
        profile.adaptationState.lastAdaptation = adaptation.timestamp;

        // Apply partial profile update
        if (this.adaptationStrategies.userDrift.resetStrategy === 'partial_profile_update') {
            // Decay older preferences
            await this.decayOlderPreferences(profile);
        }

        await this.saveUserProfile(userId, profile);
        winston.info(`User drift adaptation applied for user ${userId}, drift: ${drift}`);
    }

    // Decay older preferences
    async decayOlderPreferences(profile) {
        const decayFactor = 0.7;

        // Decay category preferences
        Object.keys(profile.preferences.categories).forEach(category => {
            profile.preferences.categories[category] *= decayFactor;
        });

        // Decay content type preferences
        Object.keys(profile.preferences.contentTypes).forEach(type => {
            profile.preferences.contentTypes[type] *= decayFactor;
        });

        // Decay tag preferences
        Object.keys(profile.preferences.tags).forEach(tag => {
            profile.preferences.tags[tag] *= decayFactor;
        });
    }

    // Update personalization parameters
    async updatePersonalizationParameters(userId, profile, behavior) {
        // Update learning algorithm parameters based on user behavior
        const learningRate = this.calculateAdaptiveLearningRate(profile);
        const explorationRate = this.calculateAdaptiveExplorationRate(profile);

        // Store adaptive parameters for use in recommendations
        profile.adaptiveParameters = {
            learningRate,
            explorationRate,
            lastUpdated: new Date().toISOString()
        };
    }

    // Calculate adaptive learning rate
    calculateAdaptiveLearningRate(profile) {
        const interactionRate = this.calculateInteractionRate(profile);
        const daysSinceCreation = (Date.now() - new Date(profile.createdAt).getTime()) /
                                 (1000 * 60 * 60 * 24);

        // Higher learning rate for new users and highly engaged users
        if (daysSinceCreation < 30 || interactionRate > 0.8) {
            return 0.01;
        } else if (interactionRate > 0.5) {
            return 0.005;
        } else {
            return 0.001;
        }
    }

    // Calculate adaptive exploration rate
    calculateAdaptiveExplorationRate(profile) {
        const behavioralSegment = profile.segmentation.behavioral;
        const contentSegment = profile.segmentation.content;

        // Higher exploration for new users and diverse content consumers
        if (behavioralSegment === 'new_user' || contentSegment === 'general_enthusiast') {
            return 0.2;
        } else if (behavioralSegment === 'power_user') {
            return 0.1;
        } else {
            return 0.15;
        }
    }

    // Get personalized recommendations
    async getPersonalizedRecommendations(userId, options = {}) {
        try {
            const profile = await this.getUserProfile(userId);
            if (!profile) {
                return this.getColdStartRecommendations(userId, options);
            }

            // Get adaptive parameters
            const adaptiveParams = profile.adaptiveParameters || {};
            const explorationRate = adaptiveParams.explorationRate || 0.15;

            // Generate base recommendations
            const baseRecommendations = await this.hybridRecommender.generateRecommendations(
                userId, {
                    ...options,
                    userProfile: profile
                }
            );

            // Apply personalization layers
            const personalized = await this.applyPersonalizationLayers(
                baseRecommendations, profile, explorationRate
            );

            return {
                recommendations: personalized,
                personalizationData: {
                    segment: profile.segmentation,
                    adaptationLevel: this.getAdaptationLevel(profile),
                    confidence: this.calculateRecommendationConfidence(profile),
                    lastUpdated: profile.lastUpdated
                }
            };

        } catch (error) {
            winston.error('Error getting personalized recommendations:', error);
            return { recommendations: [], personalizationData: {} };
        }
    }

    // Get cold start recommendations
    async getColdStartRecommendations(userId, options) {
        // Use popularity and demographic-based recommendations
        const strategies = this.adaptationStrategies.coldStart.fallbackMechanisms;

        // Try different strategies in order
        for (const strategy of strategies) {
            try {
                switch (strategy) {
                    case 'popularity_based':
                        return await this.getPopularityBasedRecommendations(options);
                    case 'content_based':
                        return await this.getContentBasedRecommendations(userId, options);
                    case 'global_trends':
                        return await this.getGlobalTrendRecommendations(options);
                }
            } catch (error) {
                winston.warn(`Cold start strategy ${strategy} failed:`, error);
                continue;
            }
        }

        return { recommendations: [], personalizationData: { adaptationLevel: 'cold_start' } };
    }

    // Apply personalization layers
    async applyPersonalizationLayers(recommendations, profile, explorationRate) {
        // Apply temporal personalization
        const temporalPersonalized = this.applyTemporalPersonalization(recommendations, profile);

        // Apply device personalization
        const devicePersonalized = this.applyDevicePersonalization(temporalPersonalized, profile);

        // Apply exploration-exploitation balance
        const explorationBalanced = this.applyExplorationBalance(
            devicePersonalized, explorationRate
        );

        // Apply diversity constraints
        const diversityConstrained = this.applyDiversityConstraints(explorationBalanced, profile);

        return diversityConstrained;
    }

    // Apply temporal personalization
    applyTemporalPersonalization(recommendations, profile) {
        const currentHour = new Date().getHours();
        const currentDay = new Date().getDay();

        return recommendations.map(rec => {
            let temporalScore = rec.score || 0;

            // Boost content preferred at current time
            const hourlyPreference = profile.interactionPatterns.peakHours[currentHour] || 0;
            const dailyPreference = profile.interactionPatterns.peakDays[currentDay] || 0;

            if (hourlyPreference > 0) {
                temporalScore *= 1 + (hourlyPreference / 100);
            }
            if (dailyPreference > 0) {
                temporalScore *= 1 + (dailyPreference / 100);
            }

            return { ...rec, temporalScore };
        }).sort((a, b) => b.temporalScore - a.temporalScore);
    }

    // Apply device personalization
    applyDevicePersonalization(recommendations, profile) {
        // Get most used device type
        const devicePreferences = profile.interactionPatterns.devicePreferences || {};
        const primaryDevice = Object.entries(devicePreferences)
            .sort((a, b) => b[1] - a[1])[0]?.[0];

        if (!primaryDevice) return recommendations;

        return recommendations.map(rec => {
            let deviceScore = rec.temporalScore || rec.score || 0;

            // Boost content suitable for primary device
            if (rec.metadata?.deviceOptimization?.includes(primaryDevice)) {
                deviceScore *= 1.2;
            }

            return { ...rec, deviceScore };
        }).sort((a, b) => b.deviceScore - a.deviceScore);
    }

    // Apply exploration-exploitation balance
    applyExplorationBalance(recommendations, explorationRate) {
        const exploitationCount = Math.floor(recommendations.length * (1 - explorationRate));
        const explorationCount = recommendations.length - exploitationCount;

        // Top items for exploitation
        const exploitationItems = recommendations.slice(0, exploitationCount);

        // Random items for exploration (from remaining items)
        const remainingItems = recommendations.slice(exploitationCount);
        const explorationItems = this.shuffleArray(remainingItems).slice(0, explorationCount);

        // Combine and assign exploration/exploitation flags
        const balanced = [
            ...exploitationItems.map(item => ({ ...item, strategy: 'exploitation' })),
            ...explorationItems.map(item => ({ ...item, strategy: 'exploration' }))
        ];

        return balanced;
    }

    // Apply diversity constraints
    applyDiversityConstraints(recommendations, profile) {
        const maxItemsPerCategory = Math.ceil(recommendations.length / 3);
        const categoryCounts = {};
        const diverse = [];

        recommendations.forEach(rec => {
            const category = rec.metadata?.category || 'unknown';
            const currentCount = categoryCounts[category] || 0;

            if (currentCount < maxItemsPerCategory) {
                diverse.push(rec);
                categoryCounts[category] = currentCount + 1;
            }
        });

        return diverse;
    }

    // Get adaptation level
    getAdaptationLevel(profile) {
        if (!profile.adaptationState.coldStartCompleted) return 'cold_start';
        if (profile.adaptationState.adaptationHistory.length === 0) return 'baseline';
        if (profile.adaptationState.adaptationHistory.length < 5) return 'early_adaptation';
        return 'fully_adapted';
    }

    // Calculate recommendation confidence
    calculateRecommendationConfidence(profile) {
        const interactionCount = profile.behaviorHistory.length;
        const daysSinceCreation = (Date.now() - new Date(profile.createdAt).getTime()) /
                                 (1000 * 60 * 60 * 24);

        // Base confidence from interaction count
        let confidence = Math.min(1, interactionCount / 100);

        // Adjust for account age
        if (daysSinceCreation < 7) {
            confidence *= 0.5;
        } else if (daysSinceCreation < 30) {
            confidence *= 0.8;
        }

        // Adjust for engagement level
        const engagementLevel = profile.segmentation.engagement;
        if (engagementLevel === 'highly_engaged') {
            confidence = Math.min(1, confidence * 1.2);
        } else if (engagementLevel === 'minimally_engaged') {
            confidence *= 0.7;
        }

        return Math.round(confidence * 100) / 100;
    }

    // Get user insights
    async getUserInsights(userId) {
        try {
            const profile = await this.getUserProfile(userId);
            if (!profile) {
                return { insights: [], recommendations: [], segmentation: {} };
            }

            const insights = this.generateUserInsights(profile);
            const recommendations = this.generateUserRecommendations(profile);
            const segmentation = profile.segmentation;

            return {
                insights,
                recommendations,
                segmentation,
                stats: profile.stats,
                adaptationState: profile.adaptationState
            };

        } catch (error) {
            winston.error('Error generating user insights:', error);
            return { insights: [], recommendations: [], segmentation: {}, stats: {}, adaptationState: {} };
        }
    }

    // Generate user insights
    generateUserInsights(profile) {
        const insights = [];

        // Behavioral insights
        const behavioralSegment = profile.segmentation.behavioral;
        insights.push({
            type: 'behavioral',
            title: 'User Behavior Pattern',
            description: `This user is classified as a ${behavioralSegment.replace('_', ' ')}`,
            confidence: 0.85
        });

        // Content preference insights
        const topCategories = Object.entries(profile.preferences.categories || {})
            .sort((a, b) => b[1] - a[1])
            .slice(0, 3);

        if (topCategories.length > 0) {
            insights.push({
                type: 'content',
                title: 'Top Content Categories',
                description: `Prefers: ${topCategories.map(([cat]) => cat).join(', ')}`,
                data: topCategories
            });
        }

        // Temporal insights
        const peakHours = Object.entries(profile.interactionPatterns.peakHours || {})
            .sort((a, b) => b[1] - a[1])
            .slice(0, 3)
            .map(([hour]) => `${hour}:00`);

        if (peakHours.length > 0) {
            insights.push({
                type: 'temporal',
                title: 'Peak Activity Hours',
                description: `Most active at: ${peakHours.join(', ')}`,
                data: peakHours
            });
        }

        // Engagement insights
        const engagementLevel = profile.segmentation.engagement;
        insights.push({
            type: 'engagement',
            title: 'Engagement Level',
            description: `${engagementLevel.replace('_', ' ')} user`,
            confidence: 0.9
        });

        return insights;
    }

    // Generate user recommendations
    generateUserRecommendations(profile) {
        const recommendations = [];

        // Content recommendations
        const contentSegment = profile.segmentation.content;
        if (contentSegment === 'undetermined') {
            recommendations.push({
                type: 'onboarding',
                title: 'Complete Your Profile',
                description: 'Interact with more content to get personalized recommendations',
                priority: 'high'
            });
        }

        // Engagement recommendations
        const engagementLevel = profile.segmentation.engagement;
        if (engagementLevel === 'lowly_engaged' || engagementLevel === 'minimally_engaged') {
            recommendations.push({
                type: 'engagement',
                title: 'Discover Popular Content',
                description: 'Try trending content to find what interests you',
                priority: 'medium'
            });
        }

        // Temporal recommendations
        const temporalSegment = profile.segmentation.temporal;
        if (temporalSegment === 'night_owl') {
            recommendations.push({
                type: 'temporal',
                title: 'Late Night Content',
                description: 'We have great content for your late night sessions',
                priority: 'low'
            });
        }

        return recommendations;
    }

    // A/B testing for recommendation quality
    async runABTest(userId, testConfig) {
        try {
            const { testName, variants, trafficSplit } = testConfig;

            // Assign user to variant
            const variant = this.assignTestVariant(userId, trafficSplit);

            // Get recommendations using variant strategy
            const recommendations = await this.getVariantRecommendations(
                userId, variant, variants[variant]
            );

            // Record test assignment
            await this.recordTestAssignment(userId, testName, variant);

            return {
                test: testName,
                variant,
                recommendations,
                testMetadata: {
                    assignedAt: new Date().toISOString(),
                }
            };

        } catch (error) {
            winston.error('Error running A/B test:', error);
            return null;
        }
    }

    // Assign test variant
    assignTestVariant(userId, trafficSplit) {
        // Use user ID hash for consistent assignment
        const hash = this.hashUserId(userId);
        const random = (hash % 100) / 100;

        let cumulative = 0;
        for (const [variant, split] of Object.entries(trafficSplit)) {
            cumulative += split;
            if (random < cumulative) {
                return variant;
            }
        }

        return Object.keys(trafficSplit)[0]; // Fallback
    }

    // Hash user ID for consistent assignment
    hashUserId(userId) {
        let hash = 0;
        const str = userId.toString();
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return Math.abs(hash);
    }

    // Get variant recommendations
    async getVariantRecommendations(userId, variant, config) {
        switch (config.strategy) {
            case 'increased_exploration':
                return await this.getPersonalizedRecommendations(userId, {
                    explorationRate: 0.3
                });
            case 'diversity_focused':
                return await this.getPersonalizedRecommendations(userId, {
                    diversityWeight: 0.4
                });
            case 'popularity_boost':
                return await this.getPersonalizedRecommendations(userId, {
                    popularityWeight: 0.3
                });
            default:
                return await this.getPersonalizedRecommendations(userId, {});
        }
    }

    // Record test assignment
    async recordTestAssignment(userId, testName, variant) {
        const assignment = {
            userId,
            testName,
            variant,
            assignedAt: new Date().toISOString()
        };

        await this.redisClient.lPush(`ab_test:${testName}:${variant}`, JSON.stringify(assignment));
    }

    // Utility method to shuffle array
    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }
}

module.exports = PersonalizationEngine;