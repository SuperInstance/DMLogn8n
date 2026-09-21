/**
 * DMlogn8n Cross-Platform Sync - Web Client
 * Universal save synchronization for web-based game instances
 */

class WebSyncClient {
    constructor(config = {}) {
        this.config = {
            apiEndpoint: config.apiEndpoint || 'https://api.dmlogn8n.com/sync',
            wsEndpoint: config.wsEndpoint || 'wss://ws.dmlogn8n.com',
            authToken: config.authToken || null,
            platform: 'web',
            deviceId: this.generateDeviceId(),
            autoSync: config.autoSync !== false,
            syncInterval: config.syncInterval || 30000, // 30 seconds
            retryAttempts: config.retryAttempts || 3,
            retryDelay: config.retryDelay || 1000,
            compressionEnabled: config.compressionEnabled !== false,
            encryptionEnabled: config.encryptionEnabled || false
        };

        // Connection state
        this.isConnected = false;
        this.wsConnection = null;
        this.reconnectTimer = null;
        this.syncTimer = null;

        // Data state
        this.currentSaveData = null;
        this.lastSyncVersion = null;
        this.pendingSync = false;
        this.conflictResolver = null;

        // Event listeners
        this.eventListeners = new Map();

        // Sync queue
        this.syncQueue = [];

        // Initialize
        this.initialize();
    }

    /**
     * Initialize the web sync client
     */
    async initialize() {
        try {
            // Load saved state from localStorage
            this.loadLocalState();

            // Validate authentication
            if (!this.config.authToken) {
                throw new Error('Authentication token required');
            }

            // Establish WebSocket connection
            await this.connectWebSocket();

            // Start auto-sync if enabled
            if (this.config.autoSync) {
                this.startAutoSync();
            }

            // Setup page visibility handling
            this.setupVisibilityHandling();

            // Setup online/offline handling
            this.setupNetworkHandling();

            console.log('Web Sync Client initialized');
            this.emit('initialized');

        } catch (error) {
            console.error('Failed to initialize Web Sync Client:', error);
            this.emit('error', error);
        }
    }

    /**
     * Connect to WebSocket server
     */
    async connectWebSocket() {
        return new Promise((resolve, reject) => {
            try {
                const wsUrl = `${this.config.wsEndpoint}?token=${this.config.authToken}`;
                this.wsConnection = new WebSocket(wsUrl);

                // Set connection timeout
                const timeout = setTimeout(() => {
                    reject(new Error('WebSocket connection timeout'));
                }, 10000);

                this.wsConnection.onopen = () => {
                    clearTimeout(timeout);
                    this.isConnected = true;
                    console.log('WebSocket connected');
                    this.emit('connected');

                    // Send platform info
                    this.sendWebSocketMessage({
                        type: 'platform_info',
                        platform: this.config.platform,
                        deviceId: this.config.deviceId,
                        userAgent: navigator.userAgent,
                        screenResolution: `${screen.width}x${screen.height}`,
                        language: navigator.language
                    });

                    resolve();
                };

                this.wsConnection.onmessage = (event) => {
                    this.handleWebSocketMessage(JSON.parse(event.data));
                };

                this.wsConnection.onclose = () => {
                    clearTimeout(timeout);
                    this.isConnected = false;
                    console.log('WebSocket disconnected');
                    this.emit('disconnected');

                    // Attempt reconnection
                    this.scheduleReconnect();
                };

                this.wsConnection.onerror = (error) => {
                    clearTimeout(timeout);
                    console.error('WebSocket error:', error);
                    reject(error);
                };

            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Handle WebSocket messages
     */
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'welcome':
                console.log('Received welcome message:', message.sessionId);
                this.sessionId = message.sessionId;
                break;

            case 'sync_update_available':
                this.handleSyncUpdate(message);
                break;

            case 'sync_up_to_date':
                console.log('Save data is up to date');
                this.emit('sync_up_to_date', message);
                break;

            case 'conflict_detected':
                this.handleConflictDetected(message);
                break;

            case 'conflict_resolved_notification':
                this.handleConflictResolved(message);
                break;

            case 'save_updated':
                this.handleSaveUpdated(message);
                break;

            case 'heartbeat_request':
                this.sendWebSocketMessage({
                    type: 'heartbeat_response',
                    timestamp: new Date().toISOString()
                });
                break;

            case 'error':
                console.error('Server error:', message.error);
                this.emit('server_error', message.error);
                break;

            default:
                console.log('Unknown message type:', message.type);
        }
    }

    /**
     * Save game data with synchronization
     */
    async saveGame(saveData, options = {}) {
        try {
            // Validate save data
            if (!saveData || typeof saveData !== 'object') {
                throw new Error('Invalid save data');
            }

            // Add metadata
            const enhancedSaveData = {
                ...saveData,
                metadata: {
                    ...saveData.metadata,
                    platform: this.config.platform,
                    deviceId: this.config.deviceId,
                    timestamp: new Date().toISOString(),
                    version: saveData.metadata?.version || '1.0.0'
                }
            };

            // Store locally first
            await this.saveLocally(enhancedSaveData);

            // Update current state
            this.currentSaveData = enhancedSaveData;

            // Queue for sync if online
            if (navigator.onLine) {
                return await this.syncToServer(enhancedSaveData, options);
            } else {
                console.log('Offline - save queued for later sync');
                this.syncQueue.push({
                    type: 'save',
                    data: enhancedSaveData,
                    options,
                    timestamp: Date.now()
                });
                return { success: true, queued: true };
            }

        } catch (error) {
            console.error('Save failed:', error);
            this.emit('save_error', error);
            throw error;
        }
    }

    /**
     * Load game data with synchronization
     */
    async loadGame(saveGameId, options = {}) {
        try {
            // Try local storage first
            const localData = await this.loadLocally(saveGameId);

            if (localData && !options.forceRemote) {
                // Check if we need to sync
                const syncNeeded = await this.checkSyncNeeded(saveGameId, localData.metadata?.version);

                if (!syncNeeded) {
                    this.currentSaveData = localData;
                    this.emit('loaded', localData);
                    return localData;
                }
            }

            // Fetch from server
            const remoteData = await this.loadFromServer(saveGameId, options);

            if (remoteData) {
                this.currentSaveData = remoteData;
                await this.saveLocally(remoteData);
                this.emit('loaded', remoteData);
                return remoteData;
            }

            // Fallback to local data if available
            if (localData) {
                this.currentSaveData = localData;
                this.emit('loaded', localData);
                return localData;
            }

            throw new Error('Save game not found');

        } catch (error) {
            console.error('Load failed:', error);
            this.emit('load_error', error);
            throw error;
        }
    }

    /**
     * Sync data to server
     */
    async syncToServer(saveData, options = {}) {
        try {
            const payload = {
                type: 'sync_data',
                saveGameId: saveData.saveGameId,
                data: saveData,
                platform: this.config.platform,
                deviceId: this.config.deviceId,
                version: this.lastSyncVersion,
                checksum: this.calculateChecksum(saveData),
                compression: this.config.compressionEnabled,
                timestamp: new Date().toISOString()
            };

            // Send via WebSocket if connected
            if (this.isConnected) {
                this.sendWebSocketMessage(payload);
                return { success: true, method: 'websocket' };
            }

            // Fallback to HTTP API
            const response = await this.makeApiRequest('/sync', 'POST', payload);

            if (response.success) {
                this.lastSyncVersion = response.version;
                this.saveLocalState();
                this.emit('synced', response);
                return response;
            } else {
                throw new Error(response.error || 'Sync failed');
            }

        } catch (error) {
            console.error('Sync to server failed:', error);

            // Queue for retry
            if (!options.noQueue) {
                this.syncQueue.push({
                    type: 'sync',
                    data: saveData,
                    options,
                    timestamp: Date.now(),
                    retries: 0
                });
            }

            throw error;
        }
    }

    /**
     * Load data from server
     */
    async loadFromServer(saveGameId, options = {}) {
        try {
            const response = await this.makeApiRequest(`/saves/${saveGameId}`, 'GET', {
                platform: this.config.platform,
                deviceId: this.config.deviceId,
                lastSyncVersion: this.lastSyncVersion
            });

            if (response.success) {
                if (response.upToDate) {
                    return null; // No update needed
                }

                this.lastSyncVersion = response.version;
                this.saveLocalState();
                return response.data;
            } else {
                throw new Error(response.error || 'Load failed');
            }

        } catch (error) {
            console.error('Load from server failed:', error);
            throw error;
        }
    }

    /**
     * Handle sync update notification
     */
    async handleSyncUpdate(message) {
        try {
            console.log('Sync update available:', message);

            const updatedData = await this.loadFromServer(message.saveId, {
                forceRemote: true
            });

            if (updatedData) {
                this.currentSaveData = updatedData;
                await this.saveLocally(updatedData);
                this.emit('data_updated', updatedData);
            }

        } catch (error) {
            console.error('Failed to handle sync update:', error);
            this.emit('sync_update_error', error);
        }
    }

    /**
     * Handle conflict detection
     */
    handleConflictDetected(message) {
        console.log('Conflict detected:', message);

        const conflict = {
            id: message.conflictId,
            saveId: message.saveId,
            type: message.conflictType,
            clientVersion: message.clientVersion,
            serverVersion: message.serverVersion
        };

        this.emit('conflict_detected', conflict);

        // Auto-resolve if resolver is configured
        if (this.conflictResolver) {
            this.resolveConflict(conflict.id, this.conflictResolver(conflict));
        }
    }

    /**
     * Handle conflict resolution
     */
    async resolveConflict(conflictId, resolution) {
        try {
            const response = await this.makeApiRequest(`/conflicts/${conflictId}/resolve`, 'POST', {
                resolution,
                platform: this.config.platform,
                deviceId: this.config.deviceId
            });

            if (response.success) {
                this.emit('conflict_resolved', { conflictId, resolution });
                return response;
            } else {
                throw new Error(response.error || 'Conflict resolution failed');
            }

        } catch (error) {
            console.error('Conflict resolution failed:', error);
            this.emit('conflict_resolution_error', error);
            throw error;
        }
    }

    /**
     * Handle save updated notification
     */
    async handleSaveUpdated(message) {
        console.log('Save updated by another platform:', message);

        if (message.updatedBy !== `${this.config.platform}:${this.config.deviceId}`) {
            // Load the updated data
            try {
                const updatedData = await this.loadFromServer(message.saveId, {
                    forceRemote: true
                });

                if (updatedData) {
                    this.currentSaveData = updatedData;
                    await this.saveLocally(updatedData);
                    this.emit('external_update', updatedData);
                }
            } catch (error) {
                console.error('Failed to load updated data:', error);
            }
        }
    }

    /**
     * Save data to localStorage
     */
    async saveLocally(saveData) {
        try {
            const key = `dmlogn8n_save_${saveData.saveGameId}`;
            const compressed = this.config.compressionEnabled ?
                await this.compressData(JSON.stringify(saveData)) :
                JSON.stringify(saveData);

            localStorage.setItem(key, compressed);

            // Also save metadata for quick access
            const metadataKey = `dmlogn8n_meta_${saveData.saveGameId}`;
            localStorage.setItem(metadataKey, JSON.stringify({
                saveGameId: saveData.saveGameId,
                campaignName: saveData.campaignName,
                characterName: saveData.characterName,
                lastModified: saveData.metadata?.timestamp,
                version: saveData.metadata?.version,
                platform: saveData.metadata?.platform,
                deviceId: saveData.metadata?.deviceId
            }));

        } catch (error) {
            console.error('Failed to save locally:', error);
            // Might be quota exceeded
            this.cleanupLocalStorage();
            throw error;
        }
    }

    /**
     * Load data from localStorage
     */
    async loadLocally(saveGameId) {
        try {
            const key = `dmlogn8n_save_${saveGameId}`;
            const data = localStorage.getItem(key);

            if (!data) {
                return null;
            }

            let parsedData;
            if (this.config.compressionEnabled) {
                const decompressed = await this.decompressData(data);
                parsedData = JSON.parse(decompressed);
            } else {
                parsedData = JSON.parse(data);
            }

            return parsedData;

        } catch (error) {
            console.error('Failed to load locally:', error);
            return null;
        }
    }

    /**
     * Check if sync is needed
     */
    async checkSyncNeeded(saveGameId, localVersion) {
        try {
            const response = await this.makeApiRequest(`/saves/${saveGameId}/check`, 'GET', {
                platform: this.config.platform,
                deviceId: this.config.deviceId,
                version: localVersion
            });

            return response.syncNeeded;

        } catch (error) {
            console.error('Failed to check sync status:', error);
            return false; // Assume no sync needed on error
        }
    }

    /**
     * Start automatic synchronization
     */
    startAutoSync() {
        if (this.syncTimer) {
            clearInterval(this.syncTimer);
        }

        this.syncTimer = setInterval(async () => {
            if (this.currentSaveData && !this.pendingSync && navigator.onLine) {
                try {
                    this.pendingSync = true;
                    await this.syncToServer(this.currentSaveData);
                } catch (error) {
                    console.error('Auto-sync failed:', error);
                } finally {
                    this.pendingSync = false;
                }
            }
        }, this.config.syncInterval);
    }

    /**
     * Stop automatic synchronization
     */
    stopAutoSync() {
        if (this.syncTimer) {
            clearInterval(this.syncTimer);
            this.syncTimer = null;
        }
    }

    /**
     * Process sync queue when coming online
     */
    async processSyncQueue() {
        while (this.syncQueue.length > 0) {
            const item = this.syncQueue.shift();

            try {
                if (item.type === 'save') {
                    await this.syncToServer(item.data, item.options);
                } else if (item.type === 'sync') {
                    await this.syncToServer(item.data, item.options);
                }
            } catch (error) {
                console.error('Failed to process queued sync:', error);

                // Re-queue if retries remaining
                if ((item.retries || 0) < this.config.retryAttempts) {
                    item.retries = (item.retries || 0) + 1;
                    item.timestamp = Date.now();
                    this.syncQueue.unshift(item);

                    // Wait before retry
                    await new Promise(resolve => setTimeout(resolve, this.config.retryDelay));
                } else {
                    console.error('Max retries exceeded for sync item:', item);
                    this.emit('sync_failed', item);
                }
            }
        }
    }

    /**
     * Setup page visibility handling
     */
    setupVisibilityHandling() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Page hidden - pause auto-sync
                this.stopAutoSync();
            } else {
                // Page visible - resume auto-sync and sync queue
                if (this.config.autoSync) {
                    this.startAutoSync();
                }
                if (navigator.onLine) {
                    this.processSyncQueue();
                }
            }
        });
    }

    /**
     * Setup network status handling
     */
    setupNetworkHandling() {
        window.addEventListener('online', () => {
            console.log('Network connection restored');
            this.emit('online');

            // Reconnect WebSocket if needed
            if (!this.isConnected) {
                this.connectWebSocket();
            }

            // Process sync queue
            this.processSyncQueue();
        });

        window.addEventListener('offline', () => {
            console.log('Network connection lost');
            this.emit('offline');

            // WebSocket will handle reconnection automatically
        });
    }

    /**
     * Schedule WebSocket reconnection
     */
    scheduleReconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }

        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts || 0), 30000);
        this.reconnectAttempts = (this.reconnectAttempts || 0) + 1;

        this.reconnectTimer = setTimeout(async () => {
            try {
                await this.connectWebSocket();
                this.reconnectAttempts = 0;
            } catch (error) {
                console.error('Reconnection failed:', error);
                this.scheduleReconnect();
            }
        }, delay);
    }

    /**
     * Send WebSocket message
     */
    sendWebSocketMessage(message) {
        if (this.isConnected && this.wsConnection) {
            this.wsConnection.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected - message not sent:', message);
        }
    }

    /**
     * Make HTTP API request
     */
    async makeApiRequest(endpoint, method = 'GET', data = null) {
        const url = `${this.config.apiEndpoint}${endpoint}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.config.authToken}`,
                'X-Platform': this.config.platform,
                'X-Device-ID': this.config.deviceId
            }
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Load local state from localStorage
     */
    loadLocalState() {
        try {
            const state = localStorage.getItem('dmlogn8n_sync_state');
            if (state) {
                const parsed = JSON.parse(state);
                this.lastSyncVersion = parsed.lastSyncVersion;
                this.deviceId = parsed.deviceId || this.config.deviceId;
            }
        } catch (error) {
            console.error('Failed to load local state:', error);
        }
    }

    /**
     * Save local state to localStorage
     */
    saveLocalState() {
        try {
            const state = {
                lastSyncVersion: this.lastSyncVersion,
                deviceId: this.config.deviceId,
                timestamp: new Date().toISOString()
            };
            localStorage.setItem('dmlogn8n_sync_state', JSON.stringify(state));
        } catch (error) {
            console.error('Failed to save local state:', error);
        }
    }

    /**
     * Cleanup localStorage to free space
     */
    cleanupLocalStorage() {
        try {
            // Remove old save data
            const keys = Object.keys(localStorage);
            const saveKeys = keys.filter(key => key.startsWith('dmlogn8n_save_'));

            // Sort by timestamp and keep only the most recent 10 saves
            saveKeys.sort((a, b) => {
                const dataA = localStorage.getItem(a);
                const dataB = localStorage.getItem(b);
                // This is a simplified cleanup - in production, store timestamps separately
                return a.localeCompare(b);
            });

            // Remove all but the 10 most recent
            saveKeys.slice(10).forEach(key => {
                localStorage.removeItem(key);
            });

        } catch (error) {
            console.error('Failed to cleanup localStorage:', error);
        }
    }

    /**
     * Generate unique device ID
     */
    generateDeviceId() {
        // Try to get existing ID from localStorage
        const existing = localStorage.getItem('dmlogn8n_device_id');
        if (existing) {
            return existing;
        }

        // Generate new ID
        const id = `web_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        localStorage.setItem('dmlogn8n_device_id', id);
        return id;
    }

    /**
     * Calculate data checksum
     */
    calculateChecksum(data) {
        const dataString = JSON.stringify(data, Object.keys(data).sort());
        return this.simpleHash(dataString);
    }

    /**
     * Simple hash function
     */
    simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return hash.toString(36);
    }

    /**
     * Compress data
     */
    async compressData(data) {
        // Simple compression placeholder - in production, use proper compression
        return data;
    }

    /**
     * Decompress data
     */
    async decompressData(data) {
        // Simple decompression placeholder
        return data;
    }

    /**
     * Event handling
     */
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.eventListeners.has(event)) {
            const listeners = this.eventListeners.get(event);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    emit(event, data = null) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    /**
     * Get current status
     */
    getStatus() {
        return {
            connected: this.isConnected,
            sessionId: this.sessionId,
            deviceId: this.config.deviceId,
            platform: this.config.platform,
            lastSyncVersion: this.lastSyncVersion,
            pendingSync: this.pendingSync,
            queueSize: this.syncQueue.length,
            autoSyncEnabled: this.config.autoSync
        };
    }

    /**
     * Get all local saves
     */
    getLocalSaves() {
        const saves = [];
        const keys = Object.keys(localStorage);

        keys.forEach(key => {
            if (key.startsWith('dmlogn8n_meta_')) {
                try {
                    const metadata = JSON.parse(localStorage.getItem(key));
                    saves.push(metadata);
                } catch (error) {
                    console.error('Failed to parse metadata:', key, error);
                }
            }
        });

        return saves.sort((a, b) => new Date(b.lastModified) - new Date(a.lastModified));
    }

    /**
     * Delete local save
     */
    deleteLocalSave(saveGameId) {
        localStorage.removeItem(`dmlogn8n_save_${saveGameId}`);
        localStorage.removeItem(`dmlogn8n_meta_${saveGameId}`);
    }

    /**
     * Clear all local data
     */
    clearLocalData() {
        const keys = Object.keys(localStorage);
        keys.forEach(key => {
            if (key.startsWith('dmlogn8n_')) {
                localStorage.removeItem(key);
            }
        });
    }

    /**
     * Disconnect and cleanup
     */
    disconnect() {
        this.stopAutoSync();

        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }

        if (this.wsConnection) {
            this.wsConnection.close();
        }

        this.isConnected = false;
        this.emit('disconnected');
    }
}

// Export for use in browser
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSyncClient;
} else if (typeof window !== 'undefined') {
    window.DMLogn8nWebSync = WebSyncClient;
}