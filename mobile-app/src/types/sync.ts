export interface SyncQueueItem {
  id: string;
  entityType: 'character' | 'campaign' | 'session' | 'user' | 'message' | 'dice_roll';
  entityId: string;
  operation: 'create' | 'update' | 'delete';
  data?: any;
  priority: 'critical' | 'high' | 'normal' | 'low' | 'background';
  timestamp: string;
  retryCount?: number;
  maxRetries?: number;
  conflictResolution?: 'client_wins' | 'server_wins' | 'merge' | 'prompt_user';
}

export interface SyncResult {
  itemId: string;
  success: boolean;
  error?: string;
  resolvedData?: any;
}

export type ConflictResolution = 'client_wins' | 'server_wins' | 'merge' | 'prompt_user';

export interface SyncStatus {
  isOnline: boolean;
  isSyncing: boolean;
  queueLength: number;
  lastSyncTime?: string;
  pendingConflicts: number;
  syncErrors: string[];
}

export interface ConflictInfo {
  itemId: string;
  entityType: string;
  entityId: string;
  clientData: any;
  serverData: any;
  conflictFields: string[];
  timestamp: string;
}

export interface OfflineStorage {
  characters: any[];
  campaigns: any[];
  sessions: any[];
  messages: any[];
  diceRolls: any[];
  lastSyncTime: string;
  pendingOperations: SyncQueueItem[];
}

export interface SyncProgress {
  totalItems: number;
  processedItems: number;
  currentItem?: string;
  currentEntity?: string;
  percentage: number;
}