export enum UserRole {
  DM = 'dm',
  PLAYER = 'player',
  CODER = 'coder',
  SPECTATOR = 'spectator',
  SYSTEM = 'system'
}

export enum PortalType {
  DM_PORTAL = 'dm-portal',
  PLAYER_PORTAL = 'player-portal',
  CODER_PORTAL = 'coder-portal',
  COMBAT_PORTAL = 'combat-portal',
  CHARACTER_PORTAL = 'character-portal'
}

export enum ChannelType {
  PARTY = 'party',
  DM_WHISPER = 'dm-whisper',
  CODER = 'coder',
  SYSTEM = 'system',
  OOC = 'ooc',
  COMBAT = 'combat',
  CHARACTER = 'character'
}

export enum MessageType {
  CHAT = 'chat',
  GAME_EVENT = 'game-event',
  COMBAT_EVENT = 'combat-event',
  CHARACTER_UPDATE = 'character-update',
  WORLD_UPDATE = 'world-update',
  SYSTEM_NOTIFICATION = 'system-notification',
  DM_DIRECTIVE = 'dm-directive',
  DATA_SYNC = 'data-sync',
  HEARTBEAT = 'heartbeat'
}

export enum MessagePriority {
  LOW = 0,
  NORMAL = 1,
  HIGH = 2,
  CRITICAL = 3,
  EMERGENCY = 4
}

export interface User {
  id: string;
  username: string;
  role: UserRole;
  portal: PortalType;
  characterId?: string;
  permissions: string[];
  isOnline: boolean;
  lastSeen: Date;
  sessionId: string;
}

export interface Message {
  id: string;
  type: MessageType;
  priority: MessagePriority;
  channel: ChannelType;
  sender: string;
  recipients: string[];
  content: string;
  metadata: Record<string, any>;
  timestamp: Date;
  encrypted: boolean;
  encryptedContent?: string;
  ttl?: number;
}

export interface ChatMessage extends Message {
  type: MessageType.CHAT;
  content: string;
  mentions?: string[];
  isOOC?: boolean;
}

export interface GameEventMessage extends Message {
  type: MessageType.GAME_EVENT;
  eventType: string;
  eventData: any;
  affectedCharacters: string[];
}

export interface CombatEventMessage extends Message {
  type: MessageType.COMBAT_EVENT;
  combatType: string;
  combatData: any;
  participants: string[];
}

export interface CharacterUpdateMessage extends Message {
  type: MessageType.CHARACTER_UPDATE;
  characterId: string;
  updateType: 'stats' | 'inventory' | 'position' | 'status' | 'effects';
  updateData: any;
}

export interface WorldUpdateMessage extends Message {
  type: MessageType.WORLD_UPDATE;
  worldId: string;
  updateType: 'environment' | 'weather' | 'time' | 'location';
  updateData: any;
}

export interface SystemNotificationMessage extends Message {
  type: MessageType.SYSTEM_NOTIFICATION;
  notificationType: 'info' | 'warning' | 'error' | 'success';
  title: string;
  description: string;
  actionable?: boolean;
}

export interface DMDirectiveMessage extends Message {
  type: MessageType.DM_DIRECTIVE;
  directiveType: 'command' | 'suggestion' | 'ruling' | 'announcement';
  targetPlayers?: string[];
  directive: string;
}

export interface DataSyncMessage extends Message {
  type: MessageType.DATA_SYNC;
  syncType: 'full' | 'incremental';
  dataType: string;
  syncData: any;
  version: number;
}

export interface Channel {
  id: string;
  name: string;
  type: ChannelType;
  members: string[];
  permissions: {
    read: UserRole[];
    write: UserRole[];
    moderate: UserRole[];
  };
  isPrivate: boolean;
  isEncrypted: boolean;
  metadata: Record<string, any>;
}

export interface WebSocketClient {
  id: string;
  userId: string;
  user: User;
  socket: any;
  isAlive: boolean;
  lastPing: Date;
  subscriptions: string[];
  rateLimitCount: number;
  rateLimitReset: Date;
}

export interface MessageQueue {
  priority: MessagePriority;
  messages: Message[];
  maxSize: number;
  processing: boolean;
}

export interface AuditLog {
  id: string;
  userId: string;
  action: string;
  resource: string;
  details: Record<string, any>;
  timestamp: Date;
  ip?: string;
  userAgent?: string;
  success: boolean;
  errorMessage?: string;
}

export interface RateLimitInfo {
  count: number;
  remaining: number;
  resetTime: Date;
  windowMs: number;
}

export interface EncryptionKeys {
  publicKey: string;
  privateKey: string;
  keyId: string;
  createdAt: Date;
  expiresAt: Date;
}

export interface PortalConnection {
  portalId: string;
  portalType: PortalType;
  url: string;
  status: 'connected' | 'disconnected' | 'error';
  lastPing: Date;
  messageCount: number;
  errorCount: number;
}

export interface SyncState {
  version: number;
  lastSync: Date;
  pendingSyncs: number;
  conflicts: Array<{
    id: string;
    type: string;
    data: any;
    timestamp: Date;
  }>;
}

export interface BroadcastOptions {
  channels?: ChannelType[];
  roles?: UserRole[];
  portals?: PortalType[];
  excludeUsers?: string[];
  priority?: MessagePriority;
  encrypted?: boolean;
}

export interface MessageFilter {
  userId?: string;
  role?: UserRole;
  channel?: ChannelType;
  type?: MessageType;
  priority?: MessagePriority;
  dateRange?: {
    start: Date;
    end: Date;
  };
  keywords?: string[];
  limit?: number;
  offset?: number;
}

export interface MessageStatistics {
  totalMessages: number;
  messagesByType: Record<MessageType, number>;
  messagesByChannel: Record<ChannelType, number>;
  messagesByUser: Record<string, number>;
  averageMessageSize: number;
  peakMessagesPerMinute: number;
  activeChannels: number;
  activeUsers: number;
}