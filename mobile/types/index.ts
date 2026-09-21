// User and Authentication Types
export interface User {
  id: string;
  username: string;
  email: string;
  displayName: string;
  avatar?: string;
  level: number;
  experience: number;
  achievements: Achievement[];
  createdAt: string;
  lastLoginAt: string;
  preferences: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  notifications: NotificationPreferences;
  privacy: PrivacyPreferences;
  accessibility: AccessibilityPreferences;
}

export interface NotificationPreferences {
  gameEvents: boolean;
  socialUpdates: boolean;
  systemMessages: boolean;
  pushEnabled: boolean;
  emailEnabled: boolean;
}

export interface PrivacyPreferences {
  profileVisibility: 'public' | 'friends' | 'private';
  locationSharing: boolean;
  activityStatus: boolean;
  dataCollection: boolean;
}

export interface AccessibilityPreferences {
  fontSize: 'small' | 'medium' | 'large';
  highContrast: boolean;
  reduceMotion: boolean;
  screenReader: boolean;
}

// Game Types
export interface Character {
  id: string;
  name: string;
  class: CharacterClass;
  level: number;
  experience: number;
  health: number;
  maxHealth: number;
  mana: number;
  maxMana: number;
  stats: CharacterStats;
  equipment: Equipment[];
  inventory: InventoryItem[];
  skills: Skill[];
  appearance: CharacterAppearance;
  backstory: string;
  createdAt: string;
  updatedAt: string;
}

export interface CharacterClass {
  id: string;
  name: string;
  description: string;
  baseStats: CharacterStats;
  skills: Skill[];
  equipment: Equipment[];
}

export interface CharacterStats {
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
}

export interface CharacterAppearance {
  gender: 'male' | 'female' | 'non-binary';
  race: string;
  height: string;
  weight: string;
  hairColor: string;
  eyeColor: string;
  skinTone: string;
  features: string[];
  avatar?: string;
}

export interface Equipment {
  id: string;
  name: string;
  type: EquipmentType;
  slot: EquipmentSlot;
  rarity: 'common' | 'uncommon' | 'rare' | 'epic' | 'legendary';
  stats: Partial<CharacterStats>;
  description: string;
  icon: string;
  requirements?: EquipmentRequirement[];
}

export interface EquipmentRequirement {
  type: 'level' | 'class' | 'stat';
  value: string | number;
}

export interface InventoryItem {
  id: string;
  itemId: string;
  name: string;
  description: string;
  quantity: number;
  rarity: 'common' | 'uncommon' | 'rare' | 'epic' | 'legendary';
  icon: string;
  stackable: boolean;
  usable: boolean;
  effects?: ItemEffect[];
}

export interface ItemEffect {
  type: 'heal' | 'buff' | 'debuff' | 'restore';
  target: 'health' | 'mana' | 'stat';
  value: number;
  duration?: number;
}

export interface Skill {
  id: string;
  name: string;
  description: string;
  level: number;
  maxLevel: number;
  experience: number;
  cooldown: number;
  manaCost: number;
  damage?: number;
  effects?: SkillEffect[];
  icon: string;
  requirements?: SkillRequirement[];
}

export interface SkillEffect {
  type: 'damage' | 'heal' | 'buff' | 'debuff' | 'status';
  value: number;
  duration?: number;
  target: 'self' | 'enemy' | 'ally' | 'all';
}

export interface SkillRequirement {
  type: 'level' | 'skill' | 'stat';
  value: string | number;
}

export type EquipmentType = 'weapon' | 'armor' | 'accessory' | 'consumable';
export type EquipmentSlot = 'weapon' | 'shield' | 'helmet' | 'chest' | 'gloves' | 'boots' | 'ring' | 'necklace' | 'accessory';

// Game Session Types
export interface GameSession {
  id: string;
  name: string;
  description: string;
  dungeonMasterId: string;
  players: Player[];
  status: 'waiting' | 'active' | 'paused' | 'completed';
  settings: GameSettings;
  currentScene?: GameScene;
  createdAt: string;
  updatedAt: string;
}

export interface Player {
  userId: string;
  characterId: string;
  character: Character;
  isReady: boolean;
  isOnline: boolean;
  joinedAt: string;
}

export interface GameSettings {
  maxPlayers: number;
  isPrivate: boolean;
  password?: string;
  allowSpectators: boolean;
  voiceChatEnabled: boolean;
  cameraEnabled: boolean;
  autoSave: boolean;
  difficulty: 'easy' | 'normal' | 'hard' | 'nightmare';
}

export interface GameScene {
  id: string;
  name: string;
  description: string;
  type: 'combat' | 'exploration' | 'dialogue' | 'puzzle' | 'cutscene';
  environment: SceneEnvironment;
  npcs: NPC[];
  objects: SceneObject[];
  transitions: SceneTransition[];
  music?: string;
  soundEffects?: string[];
}

export interface SceneEnvironment {
  background: string;
  lighting: 'bright' | 'normal' | 'dark' | 'very_dark';
  weather?: 'clear' | 'rain' | 'snow' | 'fog' | 'storm';
  timeOfDay: 'dawn' | 'morning' | 'noon' | 'afternoon' | 'dusk' | 'night';
  ambience: string;
}

export interface NPC {
  id: string;
  name: string;
  description: string;
  appearance: string;
  personality: string[];
  dialogue: DialogueTree;
  stats?: CharacterStats;
  equipment?: Equipment[];
  faction?: string;
  attitude: 'friendly' | 'neutral' | 'hostile';
  isQuestGiver: boolean;
  isMerchant: boolean;
  inventory?: InventoryItem[];
}

export interface DialogueTree {
  id: string;
  rootNode: DialogueNode;
  nodes: DialogueNode[];
}

export interface DialogueNode {
  id: string;
  text: string;
  speaker: string;
  options: DialogueOption[];
  conditions?: DialogueCondition[];
  actions?: DialogueAction[];
}

export interface DialogueOption {
  id: string;
  text: string;
  nextNodeId?: string;
  requirements?: DialogueRequirement[];
  consequences?: DialogueConsequence[];
}

export interface DialogueCondition {
  type: 'stat' | 'item' | 'quest' | 'reputation';
  value: string | number;
  operator: '==' | '!=' | '>' | '<' | '>=' | '<=';
}

export interface DialogueAction {
  type: 'give_item' | 'remove_item' | 'start_quest' | 'complete_quest' | 'change_stat' | 'damage' | 'heal';
  value: any;
}

export interface DialogueRequirement {
  type: 'level' | 'stat' | 'item' | 'quest' | 'skill';
  value: string | number;
}

export interface DialogueConsequence {
  type: 'reputation' | 'quest_status' | 'relationship';
  value: any;
}

export interface SceneObject {
  id: string;
  name: string;
  description: string;
  type: 'container' | 'door' | 'switch' | 'decoration' | 'interactive';
  position: Position;
  size: Size;
  isInteractable: boolean;
  isLocked?: boolean;
  requires?: string[];
  contains?: InventoryItem[];
  actions?: ObjectAction[];
}

export interface Position {
  x: number;
  y: number;
  z?: number;
}

export interface Size {
  width: number;
  height: number;
  depth?: number;
}

export interface ObjectAction {
  id: string;
  name: string;
  description: string;
  requirements?: ObjectActionRequirement[];
  effects?: ObjectActionEffect[];
}

export interface ObjectActionRequirement {
  type: 'item' | 'skill' | 'stat' | 'key';
  value: string | number;
}

export interface ObjectActionEffect {
  type: 'open' | 'close' | 'unlock' | 'damage' | 'give_item' | 'trigger_event';
  value: any;
}

export interface SceneTransition {
  id: string;
  name: string;
  targetSceneId: string;
  targetPosition: Position;
  requirements?: TransitionRequirement[];
  isTwoWay: boolean;
}

export interface TransitionRequirement {
  type: 'item' | 'key' | 'quest' | 'level';
  value: string | number;
}

// Chat and Social Types
export interface ChatMessage {
  id: string;
  senderId: string;
  senderName: string;
  senderAvatar?: string;
  content: string;
  type: 'text' | 'image' | 'audio' | 'system' | 'dice_roll' | 'game_event';
  timestamp: string;
  channelId: string;
  reactions?: MessageReaction[];
  replyTo?: string;
  attachments?: MessageAttachment[];
}

export interface MessageReaction {
  emoji: string;
  userIds: string[];
  count: number;
}

export interface MessageAttachment {
  id: string;
  type: 'image' | 'audio' | 'document' | 'character_sheet' | 'dice_result';
  url: string;
  name: string;
  size?: number;
  thumbnail?: string;
}

export interface ChatChannel {
  id: string;
  name: string;
  description?: string;
  type: 'public' | 'private' | 'direct' | 'game' | 'system';
  members: string[];
  admins: string[];
  isReadonly: boolean;
  maxMembers?: number;
  createdAt: string;
  lastActivity: string;
}

export interface Friend {
  id: string;
  userId: string;
  username: string;
  displayName: string;
  avatar?: string;
  status: 'online' | 'offline' | 'away' | 'busy' | 'invisible';
  lastSeen: string;
  isFavorite: boolean;
  isBlocked: boolean;
  mutualFriends: number;
  gamesPlayed: number;
  addedAt: string;
}

export interface FriendRequest {
  id: string;
  senderId: string;
  receiverId: string;
  senderName: string;
  senderAvatar?: string;
  message?: string;
  status: 'pending' | 'accepted' | 'declined' | 'cancelled';
  createdAt: string;
  respondedAt?: string;
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  rarity: 'common' | 'uncommon' | 'rare' | 'epic' | 'legendary';
  category: 'combat' | 'exploration' | 'social' | 'creativity' | 'system';
  progress: number;
  maxProgress: number;
  isCompleted: boolean;
  completedAt?: string;
  rewards?: AchievementReward[];
  requirements?: AchievementRequirement[];
}

export interface AchievementReward {
  type: 'experience' | 'item' | 'title' | 'badge' | 'currency';
  value: any;
}

export interface AchievementRequirement {
  type: 'stat' | 'action' | 'item' | 'location' | 'time';
  value: string | number;
  operator: '==' | '!=' | '>' | '<' | '>=' | '<=';
}

// API and Service Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

export interface NotificationData {
  id: string;
  title: string;
  body: string;
  data?: Record<string, any>;
  type: 'game_invite' | 'friend_request' | 'achievement' | 'system' | 'chat' | 'game_event';
  priority: 'low' | 'normal' | 'high' | 'critical';
  sound?: string;
  badge?: number;
  imageUrl?: string;
  actions?: NotificationAction[];
}

export interface NotificationAction {
  id: string;
  title: string;
  icon?: string;
  input?: boolean;
}

// Offline and Sync Types
export interface OfflineData {
  characters: Character[];
  inventory: InventoryItem[];
  achievements: Achievement[];
  gameSessions: Partial<GameSession>[];
  chatMessages: ChatMessage[];
  lastSyncTime: string;
  pendingActions: PendingAction[];
}

export interface PendingAction {
  id: string;
  type: 'create' | 'update' | 'delete';
  resource: string;
  data: any;
  timestamp: string;
  retryCount: number;
  maxRetries: number;
}

// Biometric Authentication Types
export interface BiometricConfig {
  allowDeviceCredentials: boolean;
  authenticateTimeout: number;
  maxAttempts: number;
  resetOnFailure: boolean;
}

export interface BiometricResult {
  success: boolean;
  error?: string;
  biometryType?: 'touchid' | 'faceid' | 'fingerprint' | 'biometrics';
}

// Navigation Types
export type RootStackParamList = {
  Auth: undefined;
  Main: undefined;
  Game: { sessionId: string };
  Character: { characterId?: string };
  Chat: { channelId: string };
  Profile: { userId?: string };
  Settings: undefined;
};

export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
  BiometricSetup: undefined;
};

export type MainStackParamList = {
  Dashboard: undefined;
  Characters: undefined;
  Sessions: undefined;
  Friends: undefined;
  Chat: undefined;
  Profile: undefined;
  Settings: undefined;
};

export type GameStackParamList = {
  GameLobby: { sessionId: string };
  GameBoard: { sessionId: string };
  CharacterSheet: { characterId: string };
  DiceRoller: undefined;
  Notes: undefined;
};

// Component Props Types
export interface CharacterCardProps {
  character: Character;
  onPress: (character: Character) => void;
  onEdit?: (character: Character) => void;
  onDelete?: (character: Character) => void;
  showActions?: boolean;
  compact?: boolean;
}

export interface GameMapProps {
  scene: GameScene;
  onPlayerMove: (position: Position) => void;
  onObjectInteract: (object: SceneObject) => void;
  currentPlayerId: string;
  isDM?: boolean;
}

export interface ChatBubbleProps {
  message: ChatMessage;
  isOwn: boolean;
  onPress?: (message: ChatMessage) => void;
  onLongPress?: (message: ChatMessage) => void;
  showAvatar?: boolean;
  showTimestamp?: boolean;
}

export interface ActionButtonProps {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  loading?: boolean;
  variant?: 'primary' | 'secondary' | 'danger' | 'success';
  size?: 'small' | 'medium' | 'large';
  icon?: string;
  fullWidth?: boolean;
}

// Error Types
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
  stack?: string;
}

export interface NetworkError extends AppError {
  statusCode?: number;
  url?: string;
}

export interface ValidationError extends AppError {
  field: string;
  value: any;
}

// Utility Types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;