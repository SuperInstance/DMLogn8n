/**
 * DMLogn8n Feature Flag JavaScript SDK
 * JavaScript client SDK for interacting with the feature flag service
 */

class DMLogn8nSDK {
    constructor(options = {}) {
        this.apiBaseUrl = options.apiBaseUrl || 'http://localhost:8001';
        this.sdkKey = options.sdkKey || null;
        this.userId = options.userId || null;
        this.context = options.context || {};
        this.cacheTtl = options.cacheTtl || 300000; // 5 minutes in milliseconds
        this.enableStreaming = options.enableStreaming || false;
        this.debug = options.debug || false;

        // Local cache
        this.flagCache = new Map();
        this.experimentCache = new Map();
        this.cacheTimestamps = new Map();

        // Event handlers
        this.flagChangeHandlers = new Map();
        this.experimentHandlers = [];

        // WebSocket connection
        this.websocket = null;

        // HTTP headers
        this.headers = {};
        if (this.sdkKey) {
            this.headers['Authorization'] = `Bearer ${this.sdkKey}`;
        }

        // Bind methods
        this.getUserSegments = this.getUserSegments.bind(this);
        this._handleWebSocketMessage = this._handleWebSocketMessage.bind(this);

        // Initialize
        this._initialize();
    }

    /**
     * Initialize the SDK
     * @private
     */
    _initialize() {
        if (this.enableStreaming) {
            this._setupStreaming();
        }

        this._log('SDK initialized');
    }

    /**
     * Set the current user and context
     * @param {string} userId - User ID
     * @param {Object} context - Additional context
     */
    setUser(userId, context = {}) {
        this.userId = userId;
        this.context = { ...this.context, ...context };

        // Clear user-specific cache
        this._clearUserCache();

        this._log(`User set: ${userId}`);
    }

    /**
     * Update user context
     * @param {Object} context - Context updates
     */
    updateContext(context) {
        this.context = { ...this.context, ...context };
        this._clearUserCache();
        this._log('Context updated');
    }

    /**
     * Get a feature flag value
     * @param {string} flagName - Name of the flag
     * @param {*} defaultValue - Default value if flag is not found
     * @param {string} userId - Optional user ID override
     * @param {Object} context - Additional context
     * @returns {Promise<FeatureFlagValue>}
     */
    async getFlag(flagName, defaultValue = null, userId = null, context = {}) {
        const effectiveUserId = userId || this.userId;
        const effectiveContext = { ...this.context, ...context };

        if (!effectiveUserId) {
            this._log('Warning: No user_id provided for flag evaluation');
            return this._createFlagValue('error', defaultValue);
        }

        // Check cache first
        const cacheKey = `flag:${effectiveUserId}:${flagName}`;
        const cachedValue = this._getFromCache(cacheKey);
        if (cachedValue && !this._isCacheExpired(cacheKey)) {
            this._log(`Cache hit for flag: ${flagName}`);
            return cachedValue;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/evaluate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.headers
                },
                body: JSON.stringify({
                    user_id: effectiveUserId,
                    flag_name: flagName,
                    context: effectiveContext
                })
            });

            if (response.ok) {
                const data = await response.json();
                const flagValue = this._createFlagValue(
                    data.flag_id,
                    data.value,
                    data.variant,
                    data.experiment_id,
                    new Date(data.timestamp)
                );

                // Cache the result
                this._setCache(cacheKey, flagValue);
                this._log(`Retrieved flag: ${flagName} = ${data.value}`);
                return flagValue;
            } else {
                this._log(`Failed to get flag ${flagName}: ${response.status}`);
                return this._createFlagValue('error', defaultValue);
            }
        } catch (error) {
            this._log(`Error getting flag ${flagName}: ${error.message}`);
            return this._createFlagValue('error', defaultValue);
        }
    }

    /**
     * Check if a boolean flag is enabled
     * @param {string} flagName - Name of the flag
     * @param {boolean} defaultValue - Default value
     * @param {string} userId - Optional user ID override
     * @param {Object} context - Additional context
     * @returns {Promise<boolean>}
     */
    async isEnabled(flagName, defaultValue = false, userId = null, context = {}) {
        const flagValue = await this.getFlag(flagName, defaultValue, userId, context);
        return Boolean(flagValue.value);
    }

    /**
     * Get string flag value
     * @param {string} flagName - Name of the flag
     * @param {string} defaultValue - Default value
     * @param {string} userId - Optional user ID override
     * @param {Object} context - Additional context
     * @returns {Promise<string>}
     */
    async getStringValue(flagName, defaultValue = '', userId = null, context = {}) {
        const flagValue = await this.getFlag(flagName, defaultValue, userId, context);
        return String(flagValue.value);
    }

    /**
     * Get number flag value
     * @param {string} flagName - Name of the flag
     * @param {number} defaultValue - Default value
     * @param {string} userId - Optional user ID override
     * @param {Object} context - Additional context
     * @returns {Promise<number>}
     */
    async getNumberValue(flagName, defaultValue = 0, userId = null, context = {}) {
        const flagValue = await this.getFlag(flagName, defaultValue, userId, context);
        const numValue = Number(flagValue.value);
        return isNaN(numValue) ? defaultValue : numValue;
    }

    /**
     * Get JSON flag value
     * @param {string} flagName - Name of the flag
     * @param {Object} defaultValue - Default value
     * @param {string} userId - Optional user ID override
     * @param {Object} context - Additional context
     * @returns {Promise<Object>}
     */
    async getJsonValue(flagName, defaultValue = {}, userId = null, context = {}) {
        const flagValue = await this.getFlag(flagName, defaultValue, userId, context);

        if (typeof flagValue.value === 'object' && flagValue.value !== null) {
            return flagValue.value;
        } else if (typeof flagValue.value === 'string') {
            try {
                return JSON.parse(flagValue.value);
            } catch (e) {
                return defaultValue;
            }
        } else {
            return defaultValue;
        }
    }

    /**
     * Get experiment assignment for a user
     * @param {string} experimentId - Experiment ID
     * @param {string} userId - Optional user ID override
     * @param {Object} context - Additional context
     * @returns {Promise<ExperimentAssignment|null>}
     */
    async getExperimentAssignment(experimentId, userId = null, context = {}) {
        const effectiveUserId = userId || this.userId;
        const effectiveContext = { ...this.context, ...context };

        if (!effectiveUserId) {
            this._log('Warning: No user_id provided for experiment assignment');
            return null;
        }

        // Check cache first
        const cacheKey = `experiment:${effectiveUserId}:${experimentId}`;
        const cachedAssignment = this._getFromCache(cacheKey);
        if (cachedAssignment && !this._isCacheExpired(cacheKey)) {
            this._log(`Cache hit for experiment: ${experimentId}`);
            return cachedAssignment;
        }

        try {
            // This would integrate with the experiment manager
            // For now, return a placeholder
            const assignment = {
                experimentId: experimentId,
                variant: {
                    variantId: 'control',
                    variantName: 'Control',
                    config: {},
                    isControl: true
                },
                timestamp: new Date()
            };

            // Cache the assignment
            this._setCache(cacheKey, assignment);
            this._log(`Retrieved experiment assignment: ${experimentId}`);
            return assignment;
        } catch (error) {
            this._log(`Error getting experiment assignment: ${error.message}`);
            return null;
        }
    }

    /**
     * Track a metric for an experiment
     * @param {string} experimentId - Experiment ID
     * @param {string} metricName - Metric name
     * @param {number} value - Metric value
     * @param {string} userId - Optional user ID override
     */
    async trackMetric(experimentId, metricName, value, userId = null) {
        const effectiveUserId = userId || this.userId;

        if (!effectiveUserId) {
            this._log('Warning: No user_id provided for metric tracking');
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/metrics`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.headers
                },
                body: JSON.stringify({
                    experiment_id: experimentId,
                    metric_name: metricName,
                    value: value,
                    user_id: effectiveUserId,
                    timestamp: new Date().toISOString()
                })
            });

            if (!response.ok) {
                this._log(`Failed to track metric: ${response.status}`);
            } else {
                this._log(`Tracked metric: ${metricName} = ${value}`);
            }
        } catch (error) {
            this._log(`Error tracking metric: ${error.message}`);
        }
    }

    /**
     * Add a handler for flag changes
     * @param {string} flagName - Flag name
     * @param {Function} handler - Handler function
     */
    addFlagChangeHandler(flagName, handler) {
        if (!this.flagChangeHandlers.has(flagName)) {
            this.flagChangeHandlers.set(flagName, []);
        }
        this.flagChangeHandlers.get(flagName).push(handler);
        this._log(`Added handler for flag: ${flagName}`);
    }

    /**
     * Add a handler for experiment assignments
     * @param {Function} handler - Handler function
     */
    addExperimentHandler(handler) {
        this.experimentHandlers.push(handler);
        this._log('Added experiment handler');
    }

    /**
     * Set up WebSocket streaming for real-time updates
     * @private
     */
    _setupStreaming() {
        try {
            const wsUrl = this.apiBaseUrl.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws';
            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                this._log('WebSocket connection established');
            };

            this.websocket.onmessage = this._handleWebSocketMessage;

            this.websocket.onerror = (error) => {
                this._log(`WebSocket error: ${error}`);
            };

            this.websocket.onclose = () => {
                this._log('WebSocket connection closed');
                // Attempt to reconnect after 5 seconds
                setTimeout(() => {
                    this._setupStreaming();
                }, 5000);
            };
        } catch (error) {
            this._log(`Failed to setup streaming: ${error.message}`);
        }
    }

    /**
     * Handle WebSocket messages
     * @param {MessageEvent} event - WebSocket message event
     * @private
     */
    _handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);

            if (data.type === 'flag_change') {
                this._handleFlagChange(data);
            } else if (data.type === 'experiment_update') {
                this._handleExperimentUpdate(data);
            }
        } catch (error) {
            this._log(`Error handling WebSocket message: ${error.message}`);
        }
    }

    /**
     * Handle flag change notifications
     * @param {Object} data - Flag change data
     * @private
     */
    _handleFlagChange(data) {
        try {
            const flagData = data.flag || {};
            const flagName = flagData.name;

            if (flagName && this.flagChangeHandlers.has(flagName)) {
                // Invalidate cache for this flag
                const cacheKeysToRemove = [];
                for (const key of this.flagCache.keys()) {
                    if (key.endsWith(`:${flagName}`)) {
                        cacheKeysToRemove.push(key);
                    }
                }

                for (const key of cacheKeysToRemove) {
                    this.flagCache.delete(key);
                    this.cacheTimestamps.delete(key);
                }

                // Call handlers
                const flagValue = this._createFlagValue(
                    flagData.id,
                    flagData.current_value,
                    null,
                    null,
                    new Date(data.timestamp)
                );

                for (const handler of this.flagChangeHandlers.get(flagName)) {
                    try {
                        handler(flagValue);
                    } catch (error) {
                        this._log(`Error in flag change handler: ${error.message}`);
                    }
                }
            }
        } catch (error) {
            this._log(`Error handling flag change: ${error.message}`);
        }
    }

    /**
     * Handle experiment update notifications
     * @param {Object} data - Experiment update data
     * @private
     */
    _handleExperimentUpdate(data) {
        try {
            // Clear experiment cache
            const cacheKeysToRemove = [];
            for (const key of this.experimentCache.keys()) {
                if (key.startsWith('experiment:')) {
                    cacheKeysToRemove.push(key);
                }
            }

            for (const key of cacheKeysToRemove) {
                this.experimentCache.delete(key);
                this.cacheTimestamps.delete(key);
            }

            // Call experiment handlers
            for (const handler of this.experimentHandlers) {
                try {
                    handler(data);
                } catch (error) {
                    this._log(`Error in experiment handler: ${error.message}`);
                }
            }
        } catch (error) {
            this._log(`Error handling experiment update: ${error.message}`);
        }
    }

    /**
     * Get value from cache
     * @param {string} key - Cache key
     * @returns {*}
     * @private
     */
    _getFromCache(key) {
        if (this.flagCache.has(key)) {
            return this.flagCache.get(key);
        } else if (this.experimentCache.has(key)) {
            return this.experimentCache.get(key);
        }

        // Check localStorage for persistence
        try {
            const cached = localStorage.getItem(`dmlogn8n:${key}`);
            if (cached) {
                const data = JSON.parse(cached);
                if (data.expires > Date.now()) {
                    return data.value;
                } else {
                    localStorage.removeItem(`dmlogn8n:${key}`);
                }
            }
        } catch (error) {
            this._log(`Error getting from localStorage: ${error.message}`);
        }

        return null;
    }

    /**
     * Set value in cache
     * @param {string} key - Cache key
     * @param {*} value - Value to cache
     * @private
     */
    _setCache(key, value) {
        // Set in memory cache
        if (value.flagId) {
            this.flagCache.set(key, value);
        } else if (value.experimentId) {
            this.experimentCache.set(key, value);
        }

        this.cacheTimestamps.set(key, Date.now());

        // Set in localStorage for persistence
        try {
            const data = {
                value: value,
                expires: Date.now() + this.cacheTtl
            };
            localStorage.setItem(`dmlogn8n:${key}`, JSON.stringify(data));
        } catch (error) {
            this._log(`Error setting localStorage: ${error.message}`);
        }
    }

    /**
     * Check if cache entry is expired
     * @param {string} key - Cache key
     * @returns {boolean}
     * @private
     */
    _isCacheExpired(key) {
        if (!this.cacheTimestamps.has(key)) {
            return true;
        }

        return Date.now() - this.cacheTimestamps.get(key) > this.cacheTtl;
    }

    /**
     * Clear user-specific cache entries
     * @private
     */
    _clearUserCache() {
        if (!this.userId) return;

        // Clear flag cache for this user
        const flagKeysToRemove = [];
        for (const key of this.flagCache.keys()) {
            if (key.startsWith(`flag:${this.userId}:`)) {
                flagKeysToRemove.push(key);
            }
        }

        for (const key of flagKeysToRemove) {
            this.flagCache.delete(key);
            this.cacheTimestamps.delete(key);
        }

        // Clear experiment cache for this user
        const experimentKeysToRemove = [];
        for (const key of this.experimentCache.keys()) {
            if (key.startsWith(`experiment:${this.userId}:`)) {
                experimentKeysToRemove.push(key);
            }
        }

        for (const key of experimentKeysToRemove) {
            this.experimentCache.delete(key);
            this.cacheTimestamps.delete(key);
        }
    }

    /**
     * Flush all cache entries
     */
    flushCache() {
        this.flagCache.clear();
        this.experimentCache.clear();
        this.cacheTimestamps.clear();

        // Clear localStorage
        try {
            for (let i = localStorage.length - 1; i >= 0; i--) {
                const key = localStorage.key(i);
                if (key && key.startsWith('dmlogn8n:')) {
                    localStorage.removeItem(key);
                }
            }
        } catch (error) {
            this._log(`Error clearing localStorage: ${error.message}`);
        }

        this._log('Cache flushed');
    }

    /**
     * Create a flag value object
     * @param {string} flagId - Flag ID
     * @param {*} value - Flag value
     * @param {string} variant - Variant (optional)
     * @param {string} experimentId - Experiment ID (optional)
     * @param {Date} timestamp - Timestamp
     * @returns {FeatureFlagValue}
     * @private
     */
    _createFlagValue(flagId, value, variant = null, experimentId = null, timestamp = new Date()) {
        return {
            flagId,
            value,
            variant,
            experimentId,
            timestamp
        };
    }

    /**
     * Log message if debug is enabled
     * @param {string} message - Log message
     * @private
     */
    _log(message) {
        if (this.debug) {
            console.log(`[DMLogn8n SDK] ${message}`);
        }
    }

    /**
     * Destroy the SDK and clean up resources
     */
    destroy() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }

        this.flushCache();
        this.flagChangeHandlers.clear();
        this.experimentHandlers = [];

        this._log('SDK destroyed');
    }
}

/**
 * Convenience wrapper for common feature flag operations
 */
class FeatureFlags {
    constructor(sdk) {
        this.sdk = sdk;
    }

    /**
     * Check if enhanced AI model is enabled for user
     * @param {string} userId - Optional user ID
     * @returns {Promise<boolean>}
     */
    async isAIModelEnhanced(userId = null) {
        return await this.sdk.isEnabled('ai_model_enhanced', false, userId);
    }

    /**
     * Get AI model to use for user
     * @param {string} userId - Optional user ID
     * @returns {Promise<string>}
     */
    async getAIModel(userId = null) {
        return await this.sdk.getStringValue('ai_model_selection', 'gpt-4', userId);
    }

    /**
     * Check if voice chat is enabled for user
     * @param {string} userId - Optional user ID
     * @returns {Promise<boolean>}
     */
    async isVoiceChatEnabled(userId = null) {
        return await this.sdk.isEnabled('voice_chat_enabled', false, userId);
    }

    /**
     * Get combat damage calculation method
     * @param {string} userId - Optional user ID
     * @returns {Promise<string>}
     */
    async getCombatDamageMethod(userId = null) {
        return await this.sdk.getStringValue('combat_damage_calculation', 'standard', userId);
    }

    /**
     * Check if enhanced UI is enabled for user
     * @param {string} userId - Optional user ID
     * @returns {Promise<boolean>}
     */
    async isEnhancedUIEnabled(userId = null) {
        return await this.sdk.isEnabled('enhanced_ui_animations', false, userId);
    }

    /**
     * Get AI creativity level for user
     * @param {string} userId - Optional user ID
     * @returns {Promise<number>}
     */
    async getAICreativityLevel(userId = null) {
        return await this.sdk.getNumberValue('ai_response_creativity', 0.7, userId);
    }
}

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DMLogn8nSDK, FeatureFlags };
} else if (typeof window !== 'undefined') {
    window.DMLogn8nSDK = DMLogn8nSDK;
    window.FeatureFlags = FeatureFlags;
}

// Example usage
if (typeof window !== 'undefined') {
    // Initialize SDK
    const sdk = new DMLogn8nSDK({
        apiBaseUrl: 'http://localhost:8001',
        userId: 'user123',
        context: {
            level: 25,
            is_premium: true,
            platform: 'web'
        },
        enableStreaming: true,
        debug: true
    });

    // Use convenience wrapper
    const flags = new FeatureFlags(sdk);

    // Example functions
    async function checkFeatures() {
        try {
            // Check if voice chat is enabled
            const voiceEnabled = await flags.isVoiceChatEnabled();
            console.log('Voice chat enabled:', voiceEnabled);

            // Get AI model
            const aiModel = await flags.getAIModel();
            console.log('Using AI model:', aiModel);

            // Get AI creativity level
            const creativity = await flags.getAICreativityLevel();
            console.log('AI creativity level:', creativity);

            // Check enhanced UI
            const enhancedUI = await flags.isEnhancedUIEnabled();
            console.log('Enhanced UI enabled:', enhancedUI);

        } catch (error) {
            console.error('Error checking features:', error);
        }
    }

    // Set up real-time updates
    sdk.addFlagChangeHandler('voice_chat_enabled', (flagValue) => {
        console.log('Voice chat flag changed:', flagValue.value);
        // Update UI accordingly
        updateVoiceChatUI(flagValue.value);
    });

    // Set user when they log in
    function setUser(userId, userContext) {
        sdk.setUser(userId, userContext);
        checkFeatures();
    }

    // Update UI based on voice chat flag
    function updateVoiceChatUI(enabled) {
        const voiceButton = document.getElementById('voice-chat-button');
        if (voiceButton) {
            voiceButton.style.display = enabled ? 'block' : 'none';
        }
    }

    // Track metrics
    async function trackUserEngagement(engagementScore) {
        await sdk.trackMetric('user_engagement_experiment', 'engagement_score', engagementScore);
    }

    // Initialize when page loads
    document.addEventListener('DOMContentLoaded', () => {
        checkFeatures();
    });

    // Clean up when page unloads
    window.addEventListener('beforeunload', () => {
        sdk.destroy();
    });
}