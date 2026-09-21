import {
  DataSyncMessage,
  CharacterUpdateMessage,
  WorldUpdateMessage,
  MessageType,
  MessagePriority,
  SyncState
} from '@/types';
import { v4 as uuidv4 } from 'uuid';
import { EventEmitter } from 'events';
import { Logger } from '@/utils/logger';

export interface SyncData {
  id: string;
  type: string;
  version: number;
  data: any;
  timestamp: Date;
  source: string;
  checksum: string;
}

export interface ConflictResolution {
  strategy: 'latest' | 'merge' | 'manual' | 'source_priority';
  resolver?: string; // ID of resolver (usually DM)
}

export interface SyncTarget {
  id: string;
  type: 'character' | 'world' | 'inventory' | 'effects' | 'stats';
  lastSyncVersion: number;
  isDirty: boolean;
  pendingChanges: SyncData[];
}

export class DataSyncManager extends EventEmitter {
  private syncTargets: Map<string, SyncTarget>;
  private syncStates: Map<string, SyncState>;
  private syncQueue: DataSyncMessage[];
  private conflictResolutions: Map<string, ConflictResolution>;
  private syncInterval: NodeJS.Timeout;
  private logger: Logger;
  private isProcessing: boolean;

  constructor() {
    super();
    this.syncTargets = new Map();
    this.syncStates = new Map();
    this.syncQueue = [];
    this.conflictResolutions = new Map();
    this.logger = new Logger('DataSyncManager');
    this.isProcessing = false;

    this.startSyncProcessor();
    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    this.on('characterUpdate', this.handleCharacterUpdate.bind(this));
    this.on('worldUpdate', this.handleWorldUpdate.bind(this));
    this.on('inventoryUpdate', this.handleInventoryUpdate.bind(this));
    this.on('effectsUpdate', this.handleEffectsUpdate.bind(this));
    this.on('conflictDetected', this.handleConflict.bind(this));
  }

  private startSyncProcessor(): void {
    this.syncInterval = setInterval(() => {
      this.processSyncQueue();
    }, 1000); // Process sync queue every second
  }

  // Character State Synchronization
  public syncCharacterState(
    characterId: string,
    updateType: 'stats' | 'position' | 'status' | 'effects' | 'inventory',
    data: any,
    source: string = 'unknown'
  ): void {
    const syncData: SyncData = {
      id: uuidv4(),
      type: `character_${updateType}`,
      version: this.getNextVersion(characterId),
      data: {
        characterId,
        updateType,
        ...data
      },
      timestamp: new Date(),
      source,
      checksum: this.calculateChecksum(data)
    };

    this.addToSyncQueue(syncData, 'character');
    this.updateSyncTarget(characterId, 'character', syncData);

    this.emit('characterUpdate', { characterId, updateType, data, source });
  }

  private handleCharacterUpdate(event: any): Promise<void> {
    const message: CharacterUpdateMessage = {
      id: uuidv4(),
      type: MessageType.CHARACTER_UPDATE,
      priority: MessagePriority.HIGH,
      channel: 'character' as any,
      sender: 'system',
      recipients: [], // Will be determined by routing
      content: `Character ${event.characterId} ${event.updateType} updated`,
      metadata: {
        source: event.source,
        updateType: event.updateType
      },
      timestamp: new Date(),
      encrypted: false,
      characterId: event.characterId,
      updateType: event.updateType as any,
      updateData: event.data
    };

    this.emit('messageCreated', message);
    return Promise.resolve();
  }

  // World State Synchronization
  public syncWorldState(
    worldId: string,
    updateType: 'environment' | 'weather' | 'time' | 'location' | 'global_state',
    data: any,
    source: string = 'system'
  ): void {
    const syncData: SyncData = {
      id: uuidv4(),
      type: `world_${updateType}`,
      version: this.getNextVersion(worldId),
      data: {
        worldId,
        updateType,
        ...data
      },
      timestamp: new Date(),
      source,
      checksum: this.calculateChecksum(data)
    };

    this.addToSyncQueue(syncData, 'world');
    this.updateSyncTarget(worldId, 'world', syncData);

    this.emit('worldUpdate', { worldId, updateType, data, source });
  }

  private handleWorldUpdate(event: any): Promise<void> {
    const message: WorldUpdateMessage = {
      id: uuidv4(),
      type: MessageType.WORLD_UPDATE,
      priority: MessagePriority.NORMAL,
      channel: 'party' as any,
      sender: 'system',
      recipients: [], // Will be determined by routing
      content: `World ${event.worldId} ${event.updateType} updated`,
      metadata: {
        source: event.source,
        updateType: event.updateType
      },
      timestamp: new Date(),
      encrypted: false,
      worldId: event.worldId,
      updateType: event.updateType as any,
      updateData: event.data
    };

    this.emit('messageCreated', message);
    return Promise.resolve();
  }

  // Inventory Synchronization
  public syncInventory(
    characterId: string,
    inventoryData: any,
    source: string = 'character'
  ): void {
    const syncData: SyncData = {
      id: uuidv4(),
      type: 'inventory',
      version: this.getNextVersion(`${characterId}_inventory`),
      data: {
        characterId,
        inventory: inventoryData
      },
      timestamp: new Date(),
      source,
      checksum: this.calculateChecksum(inventoryData)
    };

    this.addToSyncQueue(syncData, 'inventory');
    this.updateSyncTarget(characterId, 'inventory', syncData);

    this.emit('inventoryUpdate', { characterId, inventoryData, source });
  }

  private handleInventoryUpdate(event: any): void {
    this.syncCharacterState(
      event.characterId,
      'inventory',
      event.inventory,
      event.source
    );
  }

  // Spell Effects Synchronization
  public syncSpellEffects(
    characterId: string,
    effects: any[],
    source: string = 'combat'
  ): void {
    const syncData: SyncData = {
      id: uuidv4(),
      type: 'effects',
      version: this.getNextVersion(`${characterId}_effects`),
      data: {
        characterId,
        effects
      },
      timestamp: new Date(),
      source,
      checksum: this.calculateChecksum(effects)
    };

    this.addToSyncQueue(syncData, 'effects');
    this.updateSyncTarget(characterId, 'effects', syncData);

    this.emit('effectsUpdate', { characterId, effects, source });
  }

  private handleEffectsUpdate(event: any): void {
    this.syncCharacterState(
      event.characterId,
      'effects',
      { effects: event.effects },
      event.source
    );
  }

  // Combat State Alignment
  public syncCombatState(
    combatId: string,
    combatData: any,
    source: string = 'combat'
  ): void {
    const syncData: SyncData = {
      id: uuidv4(),
      type: 'combat_state',
      version: this.getNextVersion(combatId),
      data: {
        combatId,
        ...combatData
      },
      timestamp: new Date(),
      source,
      checksum: this.calculateChecksum(combatData)
    };

    this.addToSyncQueue(syncData, 'combat');
    this.updateSyncTarget(combatId, 'combat', syncData);

    this.emit('combatUpdate', { combatId, combatData, source });
  }

  // Sync Queue Management
  private addToSyncQueue(syncData: SyncData, dataType: string): void {
    const message: DataSyncMessage = {
      id: uuidv4(),
      type: MessageType.DATA_SYNC,
      priority: MessagePriority.HIGH,
      channel: 'system' as any,
      sender: 'sync_manager',
      recipients: [], // Will be determined by routing logic
      content: `Data sync for ${dataType}`,
      metadata: {
        syncId: syncData.id,
        dataType,
        source: syncData.source
      },
      timestamp: syncData.timestamp,
      encrypted: false,
      syncType: 'incremental',
      dataType,
      syncData: syncData.data,
      version: syncData.version
    };

    this.syncQueue.push(message);
    this.logger.debug(`Added to sync queue: ${syncData.type} v${syncData.version}`);
  }

  private async processSyncQueue(): Promise<void> {
    if (this.isProcessing || this.syncQueue.length === 0) {
      return;
    }

    this.isProcessing = true;

    try {
      const messages = [...this.syncQueue];
      this.syncQueue = [];

      for (const message of messages) {
        await this.processSyncMessage(message);
      }
    } catch (error) {
      this.logger.error(`Error processing sync queue: ${error.message}`);
    } finally {
      this.isProcessing = false;
    }
  }

  private async processSyncMessage(message: DataSyncMessage): Promise<void> {
    try {
      // Detect conflicts
      const conflict = await this.detectConflict(message);
      if (conflict) {
        await this.resolveConflict(message, conflict);
      } else {
        // Apply sync
        await this.applySync(message);
        this.emit('messageCreated', message);
      }
    } catch (error) {
      this.logger.error(`Error processing sync message ${message.id}: ${error.message}`);
    }
  }

  private async detectConflict(message: DataSyncMessage): Promise<SyncData | null> {
    const targetId = this.getTargetId(message);
    const target = this.syncTargets.get(targetId);

    if (!target) {
      return null;
    }

    // Check if there's a newer version
    if (message.version < target.lastSyncVersion) {
      // Conflict detected - retrieve the conflicting data
      const conflictingData = target.pendingChanges.find(
        change => change.version > message.version
      );

      if (conflictingData) {
        this.emit('conflictDetected', { message, conflictingData });
        return conflictingData;
      }
    }

    return null;
  }

  private async resolveConflict(message: DataSyncMessage, conflict: SyncData): Promise<void> {
    const targetId = this.getTargetId(message);
    const resolution = this.conflictResolutions.get(targetId) || {
      strategy: 'latest' as const
    };

    let resolvedData: SyncData;

    switch (resolution.strategy) {
      case 'latest':
        resolvedData = message.version > conflict.version ?
          message.syncData as SyncData : conflict;
        break;

      case 'merge':
        resolvedData = await this.mergeData(message.syncData as SyncData, conflict);
        break;

      case 'source_priority':
        resolvedData = this.resolveBySourcePriority(message.syncData as SyncData, conflict);
        break;

      case 'manual':
        // Emit conflict for manual resolution
        this.emit('manualConflictRequired', { message, conflict });
        return;

      default:
        resolvedData = message.syncData as SyncData;
    }

    // Apply resolved data
    await this.applyResolvedSync(resolvedData);
    this.logger.info(`Conflict resolved for ${targetId} using ${resolution.strategy} strategy`);
  }

  private async mergeData(data1: SyncData, data2: SyncData): Promise<SyncData> {
    // Simple merge strategy - can be enhanced based on data type
    const mergedData = {
      ...data1.data,
      ...data2.data
    };

    return {
      ...data1,
      data: mergedData,
      version: Math.max(data1.version, data2.version) + 1,
      checksum: this.calculateChecksum(mergedData)
    };
  }

  private resolveBySourcePriority(data1: SyncData, data2: SyncData): SyncData {
    const sourcePriority = {
      'dm': 4,
      'system': 3,
      'combat': 2,
      'character': 1
    };

    const priority1 = sourcePriority[data1.source as keyof typeof sourcePriority] || 0;
    const priority2 = sourcePriority[data2.source as keyof typeof sourcePriority] || 0;

    return priority1 >= priority2 ? data1 : data2;
  }

  private async applySync(message: DataSyncMessage): Promise<void> {
    const targetId = this.getTargetId(message);
    const target = this.syncTargets.get(targetId);

    if (target) {
      target.lastSyncVersion = message.version;
      target.isDirty = false;
      target.pendingChanges = target.pendingChanges.filter(
        change => change.version !== message.version
      );
    }

    this.logger.debug(`Applied sync for ${targetId}, version ${message.version}`);
  }

  private async applyResolvedSync(syncData: SyncData): Promise<void> {
    // Create and apply resolved sync message
    const message: DataSyncMessage = {
      id: uuidv4(),
      type: MessageType.DATA_SYNC,
      priority: MessagePriority.HIGH,
      channel: 'system' as any,
      sender: 'sync_manager',
      recipients: [],
      content: 'Resolved data sync',
      metadata: {
        resolved: true,
        originalVersion: syncData.version
      },
      timestamp: new Date(),
      encrypted: false,
      syncType: 'incremental',
      dataType: syncData.type,
      syncData: syncData.data,
      version: syncData.version
    };

    await this.applySync(message);
    this.emit('messageCreated', message);
  }

  private handleConflict(event: any): void {
    this.logger.warn(`Conflict detected for sync: ${event.message.id}`);
  }

  // Sync Target Management
  private updateSyncTarget(targetId: string, type: string, syncData: SyncData): void {
    let target = this.syncTargets.get(targetId);

    if (!target) {
      target = {
        id: targetId,
        type: type as any,
        lastSyncVersion: 0,
        isDirty: false,
        pendingChanges: []
      };
      this.syncTargets.set(targetId, target);
    }

    target.pendingChanges.push(syncData);
    target.isDirty = true;

    // Keep only recent pending changes
    if (target.pendingChanges.length > 50) {
      target.pendingChanges = target.pendingChanges.slice(-50);
    }
  }

  private getTargetId(message: DataSyncMessage): string {
    const data = message.syncData;
    if (data.characterId) {
      return data.characterId;
    }
    if (data.worldId) {
      return data.worldId;
    }
    if (data.combatId) {
      return data.combatId;
    }
    return 'unknown';
  }

  private getNextVersion(targetId: string): number {
    const target = this.syncTargets.get(targetId);
    return target ? target.lastSyncVersion + 1 : 1;
  }

  private calculateChecksum(data: any): string {
    // Simple checksum implementation - in production, use crypto
    const str = JSON.stringify(data);
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return hash.toString(36);
  }

  // Full Synchronization
  public async requestFullSync(targetId: string): Promise<void> {
    const target = this.syncTargets.get(targetId);
    if (!target) {
      this.logger.warn(`Target ${targetId} not found for full sync`);
      return;
    }

    const fullSyncMessage: DataSyncMessage = {
      id: uuidv4(),
      type: MessageType.DATA_SYNC,
      priority: MessagePriority.CRITICAL,
      channel: 'system' as any,
      sender: 'sync_manager',
      recipients: [targetId],
      content: `Full sync requested for ${targetId}`,
      metadata: {
        fullSync: true,
        targetId
      },
      timestamp: new Date(),
      encrypted: false,
      syncType: 'full',
      dataType: target.type,
      syncData: {
        targetId,
        type: target.type,
        fullSync: true
      },
      version: target.lastSyncVersion
    };

    this.emit('messageCreated', fullSyncMessage);
    this.logger.info(`Full sync requested for ${targetId}`);
  }

  // Conflict Resolution Management
  public setConflictResolution(targetId: string, resolution: ConflictResolution): void {
    this.conflictResolutions.set(targetId, resolution);
    this.logger.info(`Conflict resolution set for ${targetId}: ${resolution.strategy}`);
  }

  public getConflictResolution(targetId: string): ConflictResolution | undefined {
    return this.conflictResolutions.get(targetId);
  }

  // State Management
  public getSyncState(targetId: string): SyncState | undefined {
    return this.syncStates.get(targetId);
  }

  public getAllSyncStates(): Map<string, SyncState> {
    return new Map(this.syncStates);
  }

  public getSyncTargets(): Map<string, SyncTarget> {
    return new Map(this.syncTargets);
  }

  public clearSyncHistory(targetId?: string): void {
    if (targetId) {
      const target = this.syncTargets.get(targetId);
      if (target) {
        target.pendingChanges = [];
        target.isDirty = false;
      }
      this.syncStates.delete(targetId);
    } else {
      this.syncTargets.clear();
      this.syncStates.clear();
      this.syncQueue = [];
    }
    this.logger.info(`Sync history cleared${targetId ? ` for ${targetId}` : ''}`);
  }

  public getStatistics(): {
    totalTargets: number;
    dirtyTargets: number;
    pendingSyncs: number;
    queueSize: number;
    conflicts: number;
  } {
    const targets = Array.from(this.syncTargets.values());
    return {
      totalTargets: targets.length,
      dirtyTargets: targets.filter(t => t.isDirty).length,
      pendingSyncs: targets.reduce((sum, t) => sum + t.pendingChanges.length, 0),
      queueSize: this.syncQueue.length,
      conflicts: this.conflictResolutions.size
    };
  }

  public shutdown(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }

    // Clear all data
    this.syncTargets.clear();
    this.syncStates.clear();
    this.syncQueue = [];
    this.conflictResolutions.clear();

    this.logger.info('DataSyncManager shutdown complete');
  }
}