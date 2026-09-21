/**
 * DMlogn8n Cross-Platform Sync - Electron Client
 * Universal save synchronization for desktop platforms (Windows, macOS, Linux)
 */

const { app, ipcMain, dialog, powerMonitor } = require('electron');
const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');
const WebSocket = require('ws');
const fetch = require('node-fetch');

class ElectronSyncClient {
    constructor(config = {}) {
        this.config = {
            apiEndpoint: config.apiEndpoint || 'https://api.dmlogn8n.com/sync',
            wsEndpoint: config.wsEndpoint || 'wss://ws.dmlogn8n.com',
            authToken: config.authToken || null,
            platform: process.platform,
            deviceId: this.generateDeviceId(),
            saveDirectory: config.saveDirectory || path.join(app.getPath('userData'), 'saves'),
            autoSync: config.autoSync !== false,
            syncInterval: config.syncInterval || 30000, // 30 seconds
            syncOnFileChange: config.syncOnFileChange !== false,
            retryAttempts: config.retryAttempts || 3,
            retryDelay: config.retryDelay || 1000,
            compressionEnabled: config.compressionEnabled !== false,
            encryptionEnabled: config.encryptionEnabled || false,
            maxBackupCount: config.maxBackupCount || 10,
            watchFileChanges: config.watchFileChanges !== false
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

        // File watchers
        this.fileWatchers = new Map();

        // System info
        this.systemInfo = this.getSystemInfo();

        // Initialize
        this.initialize();
    }

    /**
     * Initialize the Electron sync client
     */
    async initialize() {
        try {
            // Create save directory if it doesn't exist
            await this.ensureSaveDirectory();

            // Load saved state from file
            await this.loadLocalState();

            // Validate authentication
            if (!this.config.authToken) {
                throw new Error('Authentication token required');
            }

            // Setup IPC handlers for renderer process
            this.setupIPCHandlers();

            // Setup file watchers if enabled
            if (this.config.watchFileChanges) {
                this.setupFileWatchers();
            }

            // Setup power monitoring
            this.setupPowerMonitoring();

            // Establish WebSocket connection
            await this.connectWebSocket();

            // Start auto-sync if enabled
            if (this.config.autoSync) {
                this.startAutoSync();
            }

            console.log('Electron Sync Client initialized');
            this.emit('initialized');

        } catch (error) {
            console.error('Failed to initialize Electron Sync Client:', error);
            this.emit('error', error);
        }
    }

    /**
     * Get system information
     */
    getSystemInfo() {
        const os = require('os');
        return {
            platform: process.platform,
            arch: process.arch,
            nodeVersion: process.version,
            electronVersion: process.versions.electron,
            appVersion: app.getVersion(),
            hostname: os.hostname(),
            totalMemory: os.totalmem(),
            freeMemory: os.freemem(),
            cpuCount: os.cpus().length,
            uptime: os.uptime()
        };
    }

    /**
     * Setup IPC handlers for communication with renderer process
     */
    setupIPCHandlers() {
        // Save game
        ipcMain.handle('sync:save-game', async (event, saveData, options) => {
            try {
                return await this.saveGame(saveData, options);
            } catch (error) {
                console.error('IPC save-game error:', error);
                throw error;
            }
        });

        // Load game
        ipcMain.handle('sync:load-game', async (event, saveGameId, options) => {
            try {
                return await this.loadGame(saveGameId, options);
            } catch (error) {
                console.error('IPC load-game error:', error);
                throw error;
            }
        });

        // Get local saves
        ipcMain.handle('sync:get-local-saves', async () => {
            try {
                return await this.getLocalSaves();
            } catch (error) {
                console.error('IPC get-local-saves error:', error);
                throw error;
            }
        });

        // Delete save
        ipcMain.handle('sync:delete-save', async (event, saveGameId) => {
            try {
                return await this.deleteLocalSave(saveGameId);
            } catch (error) {
                console.error('IPC delete-save error:', error);
                throw error;
            }
        });

        // Resolve conflict
        ipcMain.handle('sync:resolve-conflict', async (event, conflictId, resolution) => {
            try {
                return await this.resolveConflict(conflictId, resolution);
            } catch (error) {
                console.error('IPC resolve-conflict error:', error);
                throw error;
            }
        });

        // Get status
        ipcMain.handle('sync:get-status', () => {
            return this.getStatus();
        });

        // Sync now
        ipcMain.handle('sync:sync-now', async () => {
            try {
                if (this.currentSaveData) {
                    return await this.syncToServer(this.currentSaveData);
                }
                return { success: false, error: 'No save data to sync' };
            } catch (error) {
                console.error('IPC sync-now error:', error);
                throw error;
            }
        });

        // Get conflicts
        ipcMain.handle('sync:get-conflicts', async () => {
            try {
                return await this.getActiveConflicts();
            } catch (error) {
                console.error('IPC get-conflicts error:', error);
                throw error;
            }
        });
    }

    /**
     * Setup file watchers for automatic sync on file changes
     */
    setupFileWatchers() {
        const chokidar = require('chokidar');

        const watcher = chokidar.watch(path.join(this.config.saveDirectory, '*.json'), {
            ignored: /(^|[\/\\])\../, // ignore dotfiles
            persistent: true,
            ignoreInitial: true
        });

        watcher.on('change', async (filePath) => {
            console.log('Save file changed:', filePath);
            try {
                const saveData = await this.loadSaveFile(filePath);
                if (saveData) {
                    await this.saveGame(saveData, { source: 'file_change' });
                }
            } catch (error) {
                console.error('Error handling file change:', error);
            }
        });

        this.fileWatchers.set('saves', watcher);
    }

    /**
     * Setup power monitoring
     */
    setupPowerMonitoring() {
        // Suspend handling
        powerMonitor.on('suspend', () => {
            console.log('System suspending - pausing sync');
            this.stopAutoSync();
            this.emit('system_suspend');
        });

        // Resume handling
        powerMonitor.on('resume', () => {
            console.log('System resumed - resuming sync');
            this.emit('system_resume');

            // Reconnect and resume sync
            this.connectWebSocket().catch(error => {
                console.error('Failed to reconnect after resume:', error);
            });

            if (this.config.autoSync) {
                this.startAutoSync();
            }
        });

        // Battery level changes
        powerMonitor.on('on-battery', () => {
            console.log('On battery power - reducing sync frequency');
            this.emit('on_battery');

            // Reduce sync frequency when on battery
            if (this.syncTimer) {
                clearInterval(this.syncTimer);
                this.syncTimer = setInterval(() => {
                    if (this.currentSaveData && !this.pendingSync) {
                        this.syncToServer(this.currentSaveData);
                    }
                }, this.config.syncInterval * 2); // Double the interval
            }
        });

        powerMonitor.on('on-ac', () => {
            console.log('On AC power - normal sync frequency');
            this.emit('on_ac');

            // Restore normal sync frequency
            if (this.config.autoSync) {
                this.startAutoSync();
            }
        });
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
                        systemInfo: this.systemInfo,
                        saveDirectory: this.config.saveDirectory
                    });

                    resolve();
                };

                this.wsConnection.onmessage = (event) => {
                    try {
                        this.handleWebSocketMessage(JSON.parse(event.data));
                    } catch (error) {
                        console.error('Failed to parse WebSocket message:', error);
                    }
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
     * Save game data with synchronization
     */
    async saveGame(saveData, options = {}) {
        try {
            // Validate save data
            if (!saveData || typeof saveData !== 'object') {
                throw new Error('Invalid save data');
            }

            // Add desktop-specific metadata
            const enhancedSaveData = {
                ...saveData,
                metadata: {
                    ...saveData.metadata,
                    platform: this.config.platform,
                    deviceId: this.config.deviceId,
                    systemInfo: this.systemInfo,
                    timestamp: new Date().toISOString(),
                    version: saveData.metadata?.version || '1.0.0',
                    source: options.source || 'manual'
                }
            };

            // Save to file system
            await this.saveToFile(enhancedSaveData);

            // Update current state
            this.currentSaveData = enhancedSaveData;

            // Create backup
            if (!options.skipBackup) {
                await this.createBackup(enhancedSaveData);
            }

            // Queue for sync
            if (options.immediateSync) {
                return await this.syncToServer(enhancedSaveData, options);
            } else {
                // Queue for background sync
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

            // Show error dialog if this is a user-initiated save
            if (options.source !== 'file_change') {
                dialog.showErrorBox('Save Failed', `Failed to save game: ${error.message}`);
            }

            throw error;
        }
    }

    /**
     * Load game data with synchronization
     */
    async loadGame(saveGameId, options = {}) {
        try {
            // Try file system first
            const localData = await this.loadFromFile(saveGameId);

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
                await this.saveToFile(remoteData);
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
     * Save data to file system
     */
    async saveToFile(saveData) {
        try {
            const filename = `${saveData.saveGameId}.json`;
            const filePath = path.join(this.config.saveDirectory, filename);

            // Create temporary file first
            const tempPath = `${filePath}.tmp`;
            const dataString = JSON.stringify(saveData, null, 2);

            if (this.config.compressionEnabled) {
                const compressed = await this.compressData(dataString);
                await fs.writeFile(tempPath + '.gz', compressed);
                await fs.rename(tempPath + '.gz', filePath + '.gz');
            } else {
                await fs.writeFile(tempPath, dataString);
                await fs.rename(tempPath, filePath);
            }

            console.log('Save data written to:', filePath);
        } catch (error) {
            console.error('Failed to save to file:', error);
            throw error;
        }
    }

    /**
     * Load data from file system
     */
    async loadFromFile(saveGameId) {
        try {
            const filename = `${saveGameId}.json`;
            const filePath = path.join(this.config.saveDirectory, filename);

            let data;

            if (this.config.compressionEnabled) {
                const compressedPath = filePath + '.gz';
                try {
                    const compressed = await fs.readFile(compressedPath);
                    const decompressed = await this.decompressData(compressed);
                    data = JSON.parse(decompressed.toString());
                } catch (error) {
                    // Fallback to uncompressed file
                    const fileContent = await fs.readFile(filePath);
                    data = JSON.parse(fileContent.toString());
                }
            } else {
                const fileContent = await fs.readFile(filePath);
                data = JSON.parse(fileContent.toString());
            }

            return data;
        } catch (error) {
            console.error('Failed to load from file:', error);
            return null;
        }
    }

    /**
     * Load save file from path (for file watcher)
     */
    async loadSaveFile(filePath) {
        try {
            const fileContent = await fs.readFile(filePath);
            const data = JSON.parse(fileContent.toString());
            return data;
        } catch (error) {
            console.error('Failed to load save file:', filePath, error);
            return null;
        }
    }

    /**
     * Create backup of save data
     */
    async createBackup(saveData) {
        try {
            const backupDir = path.join(this.config.saveDirectory, 'backups');
            await this.ensureDirectory(backupDir);

            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const backupFilename = `${saveData.saveGameId}_${timestamp}.json`;
            const backupPath = path.join(backupDir, backupFilename);

            const dataString = JSON.stringify(saveData, null, 2);
            await fs.writeFile(backupPath, dataString);

            // Clean old backups
            await this.cleanOldBackups(saveData.saveGameId);

            console.log('Backup created:', backupPath);
        } catch (error) {
            console.error('Failed to create backup:', error);
        }
    }

    /**
     * Clean old backup files
     */
    async cleanOldBackups(saveGameId) {
        try {
            const backupDir = path.join(this.config.saveDirectory, 'backups');
            const files = await fs.readdir(backupDir);

            const backupFiles = files
                .filter(file => file.startsWith(`${saveGameId}_`) && file.endsWith('.json'))
                .map(file => ({
                    name: file,
                    path: path.join(backupDir, file),
                    time: fs.stat(path.join(backupDir, file)).then(stats => stats.mtime)
                }));

            // Sort by time (newest first)
            const sortedFiles = await Promise.all(
                backupFiles.map(async file => ({
                    ...file,
                    time: await file.time
                }))
            ).then(files => files.sort((a, b) => b.time - a.time));

            // Delete old backups, keeping only the most recent ones
            if (sortedFiles.length > this.config.maxBackupCount) {
                const filesToDelete = sortedFiles.slice(this.config.maxBackupCount);
                for (const file of filesToDelete) {
                    await fs.unlink(file.path);
                    console.log('Deleted old backup:', file.name);
                }
            }
        } catch (error) {
            console.error('Failed to clean old backups:', error);
        }
    }

    /**
     * Ensure directory exists
     */
    async ensureDirectory(dirPath) {
        try {
            await fs.access(dirPath);
        } catch (error) {
            await fs.mkdir(dirPath, { recursive: true });
        }
    }

    /**
     * Ensure save directory exists
     */
    async ensureSaveDirectory() {
        await this.ensureDirectory(this.config.saveDirectory);
        await this.ensureDirectory(path.join(this.config.saveDirectory, 'backups'));
    }

    /**
     * Get local saves
     */
    async getLocalSaves() {
        try {
            const files = await fs.readdir(this.config.saveDirectory);
            const saveFiles = files.filter(file =>
                file.endsWith('.json') && !file.startsWith('.') && !file.includes('.tmp')
            );

            const saves = [];
            for (const file of saveFiles) {
                try {
                    const filePath = path.join(this.config.saveDirectory, file);
                    const stats = await fs.stat(filePath);
                    const saveData = await this.loadFromFile(file.replace('.json', ''));

                    if (saveData) {
                        saves.push({
                            saveGameId: saveData.saveGameId,
                            campaignName: saveData.campaignName,
                            characterName: saveData.characterName,
                            lastModified: saveData.metadata?.timestamp || stats.mtime.toISOString(),
                            version: saveData.metadata?.version,
                            platform: saveData.metadata?.platform,
                            deviceId: saveData.metadata?.deviceId,
                            fileSize: stats.size
                        });
                    }
                } catch (error) {
                    console.error('Error reading save file:', file, error);
                }
            }

            return saves.sort((a, b) => new Date(b.lastModified) - new Date(a.lastModified));
        } catch (error) {
            console.error('Failed to get local saves:', error);
            return [];
        }
    }

    /**
     * Delete local save
     */
    async deleteLocalSave(saveGameId) {
        try {
            const filename = `${saveGameId}.json`;
            const filePath = path.join(this.config.saveDirectory, filename);

            await fs.unlink(filePath);

            // Also delete compressed version if it exists
            const compressedPath = filePath + '.gz';
            try {
                await fs.unlink(compressedPath);
            } catch (error) {
                // Compressed file doesn't exist, ignore
            }

            console.log('Deleted local save:', saveGameId);
            return { success: true };
        } catch (error) {
            console.error('Failed to delete local save:', error);
            throw error;
        }
    }

    /**
     * Compress data
     */
    async compressData(data) {
        const zlib = require('zlib');
        return new Promise((resolve, reject) => {
            zlib.gzip(data, (error, compressed) => {
                if (error) reject(error);
                else resolve(compressed);
            });
        });
    }

    /**
     * Decompress data
     */
    async decompressData(compressed) {
        const zlib = require('zlib');
        return new Promise((resolve, reject) => {
            zlib.gunzip(compressed, (error, decompressed) => {
                if (error) reject(error);
                else resolve(decompressed);
            });
        });
    }

    /**
     * Generate unique device ID
     */
    generateDeviceId() {
        const crypto = require('crypto');
        const machineId = require('os').hostname() + require('os').totalmem();
        return `desktop_${crypto.createHash('md5').update(machineId).digest('hex').substr(0, 12)}`;
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
                'X-Device-ID': this.config.deviceId,
                'User-Agent': `DMlogn8n-Desktop/${app.getVersion()} (${this.config.platform})`
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

    // Include other methods from web client that are also needed
    // (sendWebSocketMessage, handleWebSocketMessage, syncToServer, etc.)

    sendWebSocketMessage(message) {
        if (this.isConnected && this.wsConnection) {
            this.wsConnection.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected - message not sent:', message);
        }
    }

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

    async handleSyncUpdate(message) {
        try {
            console.log('Sync update available:', message);

            const updatedData = await this.loadFromServer(message.saveId, {
                forceRemote: true
            });

            if (updatedData) {
                this.currentSaveData = updatedData;
                await this.saveToFile(updatedData);
                this.emit('data_updated', updatedData);
            }

        } catch (error) {
            console.error('Failed to handle sync update:', error);
            this.emit('sync_update_error', error);
        }
    }

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

        // Show conflict dialog
        dialog.showMessageBox({
            type: 'warning',
            title: 'Sync Conflict Detected',
            message: 'A conflict was detected between your local save data and the server.',
            detail: 'Would you like to resolve this conflict now?',
            buttons: ['Resolve Now', 'Later'],
            defaultId: 0
        }).then((result) => {
            if (result.response === 0) {
                // User wants to resolve now
                this.emit('resolve_conflict_requested', conflict);
            }
        });

        // Auto-resolve if resolver is configured
        if (this.conflictResolver) {
            this.resolveConflict(conflict.id, this.conflictResolver(conflict));
        }
    }

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
                await this.saveLocalState();
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
                await this.saveLocalState();
                return response.data;
            } else {
                throw new Error(response.error || 'Load failed');
            }

        } catch (error) {
            console.error('Load from server failed:', error);
            throw error;
        }
    }

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

    calculateChecksum(data) {
        const dataString = JSON.stringify(data, Object.keys(data).sort());
        return crypto.createHash('sha256').update(dataString).digest('hex');
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
            const statePath = path.join(this.config.saveDirectory, 'sync_state.json');
            const state = {
                lastSyncVersion: this.lastSyncVersion,
                deviceId: this.config.deviceId,
                timestamp: new Date().toISOString()
            };
            await fs.writeFile(statePath, JSON.stringify(state, null, 2));
        } catch (error) {
            console.error('Failed to save local state:', error);
        }
    }

    async loadLocalState() {
        try {
            const statePath = path.join(this.config.saveDirectory, 'sync_state.json');
            const stateData = await fs.readFile(statePath);
            const state = JSON.parse(stateData.toString());
            this.lastSyncVersion = state.lastSyncVersion;
            this.deviceId = state.deviceId || this.config.deviceId;
        } catch (error) {
            console.error('Failed to load local state:', error);
        }
    }

    startAutoSync() {
        if (this.syncTimer) {
            clearInterval(this.syncTimer);
        }

        this.syncTimer = setInterval(async () => {
            if (this.currentSaveData && !this.pendingSync) {
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

    stopAutoSync() {
        if (this.syncTimer) {
            clearInterval(this.syncTimer);
            this.syncTimer = null;
        }
    }

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

    handleSaveUpdated(message) {
        console.log('Save updated by another platform:', message);

        if (message.updatedBy !== `${this.config.platform}:${this.config.deviceId}`) {
            // Load the updated data
            this.loadFromServer(message.saveId, {
                forceRemote: true
            }).then(updatedData => {
                if (updatedData) {
                    this.currentSaveData = updatedData;
                    this.saveToFile(updatedData);
                    this.emit('external_update', updatedData);
                }
            }).catch(error => {
                console.error('Failed to load updated data:', error);
            });
        }
    }

    handleConflictResolved(message) {
        console.log('Conflict resolved:', message);
        this.emit('conflict_resolved', message);
    }

    handleSyncUpdate(message) {
        // Implementation from above
        this.handleSyncUpdate(message);
    }

    async getActiveConflicts() {
        try {
            const response = await this.makeApiRequest('/conflicts', 'GET');
            return response.conflicts || [];
        } catch (error) {
            console.error('Failed to get active conflicts:', error);
            return [];
        }
    }

    getStatus() {
        return {
            connected: this.isConnected,
            sessionId: this.sessionId,
            deviceId: this.config.deviceId,
            platform: this.config.platform,
            lastSyncVersion: this.lastSyncVersion,
            pendingSync: this.pendingSync,
            queueSize: this.syncQueue.length,
            autoSyncEnabled: this.config.autoSync,
            saveDirectory: this.config.saveDirectory,
            systemInfo: this.systemInfo
        };
    }

    async clearLocalData() {
        try {
            const files = await fs.readdir(this.config.saveDirectory);
            for (const file of files) {
                if (file.startsWith('dmlogn8n_') || file.endsWith('.json') || file.endsWith('.gz')) {
                    await fs.unlink(path.join(this.config.saveDirectory, file));
                }
            }
            console.log('Local data cleared');
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

        // Close file watchers
        this.fileWatchers.forEach(watcher => {
            watcher.close();
        });
        this.fileWatchers.clear();

        this.isConnected = false;
        this.emit('disconnected');
    }
}

module.exports = ElectronSyncClient;