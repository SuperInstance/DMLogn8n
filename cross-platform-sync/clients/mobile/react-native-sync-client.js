/**
 * DMlogn8n Cross-Platform Sync - React Native Client
 * Universal save synchronization for mobile platforms (iOS/Android)
 */

import { AsyncStorage } from 'react-native';
import NetInfo from '@react-native-community/netinfo';
import { Platform } from 'react-native';
import DeviceInfo from 'react-native-device-info';
import BackgroundJob from 'react-native-background-job';
import PushNotification from 'react-native-push-notification';

class ReactNativeSyncClient {
    constructor(config = {}) {
        this.config = {
            apiEndpoint: config.apiEndpoint || 'https://api.dmlogn8n.com/sync',
            wsEndpoint: config.wsEndpoint || 'wss://ws.dmlogn8n.com',
            authToken: config.authToken || null,
            platform: Platform.OS, // 'ios' or 'android'
            deviceId: null, // Will be generated
            autoSync: config.autoSync !== false,
            syncInterval: config.syncInterval || 60000, // 1 minute
            backgroundSync: config.backgroundSync !== false,
            pushNotifications: config.pushNotifications !== false,
            retryAttempts: config.retryAttempts || 3,
            retryDelay: config.retryDelay || 2000,
            compressionEnabled: config.compressionEnabled !== false,
            encryptionEnabled: config.encryptionEnabled || false,
            maxLocalStorageSize: config.maxLocalStorageSize || 50 * 1024 * 1024 // 50MB
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

        // Background job ID
        this.backgroundJobId = 'dmlogn8n_sync';

        // Initialize
        this.initialize();
    }

    /**
     * Initialize the React Native sync client
     */
    async initialize() {
        try {
            // Get device information
            await this.setupDeviceInfo();

            // Load saved state from AsyncStorage
            await this.loadLocalState();

            // Validate authentication
            if (!this.config.authToken) {
                throw new Error('Authentication token required');
            }

            // Setup push notifications if enabled
            if (this.config.pushNotifications) {
                await this.setupPushNotifications();
            }

            // Setup background sync if enabled
            if (this.config.backgroundSync) {
                await this.setupBackgroundSync();
            }

            // Establish WebSocket connection
            await this.connectWebSocket();

            // Start auto-sync if enabled
            if (this.config.autoSync) {
                this.startAutoSync();
            }

            // Setup network status handling
            this.setupNetworkHandling();

            // Setup app state handling
            this.setupAppStateHandling();

            console.log('React Native Sync Client initialized');
            this.emit('initialized');

        } catch (error) {
            console.error('Failed to initialize React Native Sync Client:', error);
            this.emit('error', error);
        }
    }

    /**
     * Setup device information
     */
    async setupDeviceInfo() {
        try {
            const deviceId = await DeviceInfo.getUniqueId();
            this.config.deviceId = `${this.config.platform}_${deviceId}`;

            // Store additional device info
            this.deviceInfo = {
                model: await DeviceInfo.getModel(),
                brand: await DeviceInfo.getBrand(),
                systemVersion: await DeviceInfo.getSystemVersion(),
                buildNumber: await DeviceInfo.getBuildNumber(),
                bundleId: await DeviceInfo.getBundleId(),
                isEmulator: await DeviceInfo.isEmulator(),
                tablet: await DeviceInfo.isTablet()
            };

        } catch (error) {
            console.error('Failed to setup device info:', error);
            // Fallback to simple device ID
            this.config.deviceId = `${this.config.platform}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        }
    }

    /**
     * Setup push notifications
     */
    async setupPushNotifications() {
        try {
            PushNotification.configure({
                onRegister: (token) => {
                    console.log('Push notification token:', token);
                    this.pushToken = token;
                    this.registerPushToken();
                },
                onNotification: (notification) => {
                    console.log('Push notification received:', notification);
                    this.handlePushNotification(notification);
                },
                permissions: {
                    alert: true,
                    badge: true,
                    sound: true
                },
                popInitialNotification: true,
                requestPermissions: Platform.OS === 'ios'
            });

        } catch (error) {
            console.error('Failed to setup push notifications:', error);
        }
    }

    /**
     * Register push token with server
     */
    async registerPushToken() {
        if (!this.pushToken) return;

        try {
            await this.makeApiRequest('/push/register', 'POST', {
                token: this.pushToken,
                platform: this.config.platform,
                deviceId: this.config.deviceId
            });
        } catch (error) {
            console.error('Failed to register push token:', error);
        }
    }

    /**
     * Setup background sync
     */
    async setupBackgroundSync() {
        try {
            BackgroundJob.on('background', async () => {
                console.log('Background sync job started');
                await this.performBackgroundSync();
            });

            BackgroundJob.register({
                jobKey: this.backgroundJobId,
                period: this.config.syncInterval * 2, // Less frequent than foreground sync
                exact: true,
                allowExecutionInForeground: true,
                requiredNetworkType: BackgroundJob.NETWORK_TYPE_ANY,
                requiresCharging: false,
                requiresDeviceIdle: false,
                requiresStorageNotLow: true
            });

            console.log('Background sync configured');
        } catch (error) {
            console.error('Failed to setup background sync:', error);
        }
    }

    /**
     * Perform background sync
     */
    async performBackgroundSync() {
        try {
            // Check if we have pending sync operations
            if (this.syncQueue.length > 0 && this.currentSaveData) {
                // Process only the first item to avoid long-running background tasks
                const item = this.syncQueue[0];

                try {
                    if (item.type === 'save') {
                        await this.syncToServer(item.data, { ...item.options, background: true });
                    } else if (item.type === 'sync') {
                        await this.syncToServer(item.data, { ...item.options, background: true });
                    }

                    // Remove processed item
                    this.syncQueue.shift();

                    console.log('Background sync completed successfully');
                } catch (error) {
                    console.error('Background sync failed:', error);
                }
            }
        } catch (error) {
            console.error('Background sync error:', error);
        }
    }

    /**
     * Setup app state handling
     */
    setupAppStateHandling() {
        import('react-native').then(({ AppState }) => {
            AppState.addEventListener('change', (nextAppState) => {
                if (nextAppState === 'active') {
                    console.log('App came to foreground');
                    this.emit('app_active');

                    // Resume sync and process queue
                    if (this.config.autoSync) {
                        this.startAutoSync();
                    }
                    this.processSyncQueue();
                } else if (nextAppState === 'background') {
                    console.log('App went to background');
                    this.emit('app_background');

                    // Pause intensive sync operations
                    this.stopAutoSync();
                }
            });
        }).catch(error => {
            console.error('Failed to setup app state handling:', error);
        });
    }

    /**
     * Connect to WebSocket server
     */
    async connectWebSocket() {
        return new Promise((resolve, reject) => {
            try {
                import('react-native').then(({ WebSocket }) => {
                    const wsUrl = `${this.config.wsEndpoint}?token=${this.config.authToken}`;
                    this.wsConnection = new WebSocket(wsUrl);

                    // Set connection timeout
                    const timeout = setTimeout(() => {
                        reject(new Error('WebSocket connection timeout'));
                    }, 15000);

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
                            deviceInfo: this.deviceInfo,
                            appVersion: DeviceInfo.getVersion(),
                            buildNumber: DeviceInfo.getBuildNumber()
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
                }).catch(reject);

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

            // Add mobile-specific metadata
            const enhancedSaveData = {
                ...saveData,
                metadata: {
                    ...saveData.metadata,
                    platform: this.config.platform,
                    deviceId: this.config.deviceId,
                    deviceInfo: this.deviceInfo,
                    timestamp: new Date().toISOString(),
                    version: saveData.metadata?.version || '1.0.0',
                    batteryLevel: await this.getBatteryLevel(),
                    networkType: await this.getNetworkType()
                }
            };

            // Store locally first
            await this.saveLocally(enhancedSaveData);

            // Update current state
            this.currentSaveData = enhancedSaveData;

            // Queue for sync if online
            const netInfo = await NetInfo.fetch();
            if (netInfo.isConnected) {
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
            // Try AsyncStorage first
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

            // Check network connectivity
            const netInfo = await NetInfo.fetch();
            if (!netInfo.isConnected) {
                // Offline - use local data
                if (localData) {
                    this.currentSaveData = localData;
                    this.emit('loaded', localData);
                    return localData;
                }
                throw new Error('No network connection and no local data available');
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
     * Get battery level
     */
    async getBatteryLevel() {
        try {
            const { level } = await import('react-native-device-info').then(m => m.getBatteryLevel());
            return level;
        } catch (error) {
            return null;
        }
    }

    /**
     * Get network type
     */
    async getNetworkType() {
        try {
            const netInfo = await NetInfo.fetch();
            return netInfo.type;
        } catch (error) {
            return 'unknown';
        }
    }

    /**
     * Save data to AsyncStorage
     */
    async saveLocally(saveData) {
        try {
            const key = `dmlogn8n_save_${saveData.saveGameId}`;
            const dataString = JSON.stringify(saveData);

            // Check storage size
            await this.checkStorageSpace(dataString.length);

            const compressed = this.config.compressionEnabled ?
                await this.compressData(dataString) :
                dataString;

            await AsyncStorage.setItem(key, compressed);

            // Also save metadata for quick access
            const metadataKey = `dmlogn8n_meta_${saveData.saveGameId}`;
            const metadata = {
                saveGameId: saveData.saveGameId,
                campaignName: saveData.campaignName,
                characterName: saveData.characterName,
                lastModified: saveData.metadata?.timestamp,
                version: saveData.metadata?.version,
                platform: saveData.metadata?.platform,
                deviceId: saveData.metadata?.deviceId,
                size: dataString.length
            };
            await AsyncStorage.setItem(metadataKey, JSON.stringify(metadata));

        } catch (error) {
            console.error('Failed to save locally:', error);

            if (error.message.includes('Quota exceeded')) {
                await this.cleanupAsyncStorage();
                // Retry once after cleanup
                await this.saveLocally(saveData);
            } else {
                throw error;
            }
        }
    }

    /**
     * Load data from AsyncStorage
     */
    async loadLocally(saveGameId) {
        try {
            const key = `dmlogn8n_save_${saveGameId}`;
            const data = await AsyncStorage.getItem(key);

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
     * Check AsyncStorage space
     */
    async checkStorageSpace(dataSize) {
        try {
            const keys = await AsyncStorage.getAllKeys();
            const totalSize = await AsyncStorage.multiGet(keys)
                .then(keyValuePairs =>
                    keyValuePairs.reduce((total, [, value]) => total + (value?.length || 0), 0)
                );

            if (totalSize + dataSize > this.config.maxLocalStorageSize) {
                throw new Error('Quota exceeded');
            }
        } catch (error) {
            if (error.message !== 'Quota exceeded') {
                console.error('Failed to check storage space:', error);
            }
            throw error;
        }
    }

    /**
     * Cleanup AsyncStorage
     */
    async cleanupAsyncStorage() {
        try {
            const keys = await AsyncStorage.getAllKeys();
            const saveKeys = keys.filter(key => key.startsWith('dmlogn8n_save_'));

            // Get metadata for all saves
            const metadataKeys = saveKeys.map(key => key.replace('dmlogn8n_save_', 'dmlogn8n_meta_'));
            const metadataResults = await AsyncStorage.multiGet(metadataKeys);
            const metadata = metadataResults
                .filter(([, value]) => value)
                .map(([, value]) => JSON.parse(value))
                .sort((a, b) => new Date(b.lastModified) - new Date(a.lastModified));

            // Keep only the 10 most recent saves
            const savesToKeep = new Set(metadata.slice(0, 10).map(m => `dmlogn8n_save_${m.saveGameId}`));
            const savesToDelete = saveKeys.filter(key => !savesToKeep.has(key));

            // Delete old saves and their metadata
            const keysToDelete = [
                ...savesToDelete,
                ...savesToDelete.map(key => key.replace('dmlogn8n_save_', 'dmlogn8n_meta_'))
            ];

            if (keysToDelete.length > 0) {
                await AsyncStorage.multiRemove(keysToDelete);
                console.log(`Cleaned up ${keysToDelete.length} old save files`);
            }

        } catch (error) {
            console.error('Failed to cleanup AsyncStorage:', error);
        }
    }

    /**
     * Setup network status handling
     */
    setupNetworkHandling() {
        NetInfo.addEventListener(state => {
            if (state.isConnected) {
                console.log('Network connection restored');
                this.emit('online');

                // Reconnect WebSocket if needed
                if (!this.isConnected) {
                    this.connectWebSocket();
                }

                // Process sync queue
                this.processSyncQueue();
            } else {
                console.log('Network connection lost');
                this.emit('offline');
            }
        });
    }

    /**
     * Handle push notifications
     */
    handlePushNotification(notification) {
        if (notification.userInteraction) {
            // User tapped the notification
            console.log('User interacted with push notification');

            if (notification.data?.type === 'sync_conflict') {
                this.emit('push_conflict', notification.data);
            } else if (notification.data?.type === 'sync_complete') {
                this.emit('push_sync_complete', notification.data);
            }
        } else {
            // App was in foreground
            console.log('Push notification received in foreground');

            if (notification.data?.type === 'sync_conflict') {
                this.showConflictNotification(notification.data);
            }
        }
    }

    /**
     * Show conflict notification
     */
    showConflictNotification(conflictData) {
        PushNotification.localNotification({
            title: 'Sync Conflict Detected',
            message: 'Your save data conflicts with another device. Tap to resolve.',
            userInfo: conflictData,
            playSound: true,
            soundName: 'default',
            actions: ['Resolve', 'Ignore']
        });
    }

    // Include other methods from the web client that are also needed here
    // (syncToServer, loadFromServer, conflict handling, etc.)

    async syncToServer(saveData, options = {}) {
        // Implementation similar to web client but with mobile-specific features
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
                background: options.background || false,
                timestamp: new Date().toISOString()
            };

            // Send via WebSocket if connected and not in background
            if (this.isConnected && !options.background) {
                this.sendWebSocketMessage(payload);
                return { success: true, method: 'websocket' };
            }

            // Fallback to HTTP API
            const response = await this.makeApiRequest('/sync', 'POST', payload);

            if (response.success) {
                this.lastSyncVersion = response.version;
                await this.saveLocalState();
                this.emit('synced', response);
                return response;
            } else {
                throw new Error(response.error || 'Sync failed');
            }

        } catch (error) {
            console.error('Sync to server failed:', error);

            // Queue for retry if not a background operation
            if (!options.noQueue && !options.background) {
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

    async makeApiRequest(endpoint, method = 'GET', data = null) {
        const url = `${this.config.apiEndpoint}${endpoint}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.config.authToken}`,
                'X-Platform': this.config.platform,
                'X-Device-ID': this.config.deviceId,
                'X-App-Version': DeviceInfo.getVersion(),
                'X-Build-Number': DeviceInfo.getBuildNumber()
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

    calculateChecksum(data) {
        const dataString = JSON.stringify(data, Object.keys(data).sort());
        return this.simpleHash(dataString);
    }

    simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return hash.toString(36);
    }

    async compressData(data) {
        // Compression placeholder - implement with proper compression library
        return data;
    }

    async decompressData(data) {
        // Decompression placeholder
        return data;
    }

    // Event handling and other utility methods...
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

    async saveLocalState() {
        try {
            const state = {
                lastSyncVersion: this.lastSyncVersion,
                deviceId: this.config.deviceId,
                timestamp: new Date().toISOString()
            };
            await AsyncStorage.setItem('dmlogn8n_sync_state', JSON.stringify(state));
        } catch (error) {
            console.error('Failed to save local state:', error);
        }
    }

    async loadLocalState() {
        try {
            const state = await AsyncStorage.getItem('dmlogn8n_sync_state');
            if (state) {
                const parsed = JSON.parse(state);
                this.lastSyncVersion = parsed.lastSyncVersion;
                this.deviceId = parsed.deviceId || this.config.deviceId;
            }
        } catch (error) {
            console.error('Failed to load local state:', error);
        }
    }

    // Include other necessary methods from web client...
    // (handleSyncUpdate, handleConflictDetected, resolveConflict, etc.)

    async getLocalSaves() {
        try {
            const keys = await AsyncStorage.getAllKeys();
            const metadataKeys = keys.filter(key => key.startsWith('dmlogn8n_meta_'));
            const metadataResults = await AsyncStorage.multiGet(metadataKeys);

            return metadataResults
                .filter(([, value]) => value)
                .map(([, value]) => JSON.parse(value))
                .sort((a, b) => new Date(b.lastModified) - new Date(a.lastModified));
        } catch (error) {
            console.error('Failed to get local saves:', error);
            return [];
        }
    }

    async deleteLocalSave(saveGameId) {
        try {
            await AsyncStorage.multiRemove([
                `dmlogn8n_save_${saveGameId}`,
                `dmlogn8n_meta_${saveGameId}`
            ]);
        } catch (error) {
            console.error('Failed to delete local save:', error);
        }
    }

    async clearLocalData() {
        try {
            const keys = await AsyncStorage.getAllKeys();
            const dmlogn8nKeys = keys.filter(key => key.startsWith('dmlogn8n_'));
            if (dmlogn8nKeys.length > 0) {
                await AsyncStorage.multiRemove(dmlogn8nKeys);
            }
        } catch (error) {
            console.error('Failed to clear local data:', error);
        }
    }

    disconnect() {
        this.stopAutoSync();

        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }

        if (this.wsConnection) {
            this.wsConnection.close();
        }

        // Cancel background job
        BackgroundJob.cancel({ jobKey: this.backgroundJobId });

        this.isConnected = false;
        this.emit('disconnected');
    }
}

export default ReactNativeSyncClient;