// Core types for the DMlogn8n mobile app

export interface User {
  id: string;
  username: string;
  email: string;
  displayName: string;
  avatar?: string;
  createdAt: string;
  updatedAt: string;
  preferences: UserPreferences;
  subscription: UserSubscription;
}

export interface UserPreferences {
  theme: 'dark' | 'light' | 'auto';
  notifications: NotificationPreferences;
  accessibility: AccessibilityPreferences;
  dice: DicePreferences;
  voice: VoicePreferences;
}

export interface NotificationPreferences {
  sessionReminders: boolean;
  turnAlerts: boolean;
  levelUpNotifications: boolean;
  partyMessages: boolean;
  dmMessages: boolean;
  soundEnabled: boolean;
  vibrationEnabled: boolean;
}

export interface AccessibilityPreferences {
  largeText: boolean;
  highContrast: boolean;
  screenReader: boolean;
  hapticFeedback: boolean;
  reducedMotion: boolean;
}

export interface DicePreferences {
  soundEnabled: boolean;
  hapticFeedback: boolean;
  animationSpeed: 'slow' | 'normal' | 'fast';
  diceSkin: string;
  showTotal: boolean;
}

export interface VoicePreferences {
  enabled: boolean;
  language: string;
  voiceCommandEnabled: boolean;
  textToSpeechEnabled: boolean;
  voiceModel?: string;
}

export interface UserSubscription {
  tier: 'free' | 'premium' | 'dm_pro';
  status: 'active' | 'cancelled' | 'expired' | 'trial';
  expiresAt?: string;
  features: string[];
}

export interface Campaign {
  id: string;
  name: string;
  description: string;
  dmId: string;
  dm: User;
  players: Player[];
  characters: Character[];
  sessions: Session[];
  settings: CampaignSettings;
  worldLore: WorldLore[];
  isArchived: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface Player {
  id: string;
  userId: string;
  user: User;
  role: 'player' | 'dm' | 'co-dm';
  joinedAt: string;
  isActive: boolean;
}

export interface CampaignSettings {
  visibility: 'public' | 'private' | 'invite_only';
  maxPlayers: number;
  level: number;
  startingGold: number;
  allowedSources: string[];
  homebrewAllowed: boolean;
  voiceChatEnabled: boolean;
  videoChatEnabled: boolean;
  sessionFrequency: 'weekly' | 'biweekly' | 'monthly' | 'custom';
}

export interface WorldLore {
  id: string;
  title: string;
  content: string;
  category: 'history' | 'geography' | 'politics' | 'religion' | 'culture' | 'custom';
  tags: string[];
  isPublic: boolean;
  authorId: string;
  createdAt: string;
  updatedAt: string;
}

export interface Character {
  id: string;
  name: string;
  race: string;
  class: string;
  subclass?: string;
  level: number;
  experience: number;
  proficiencyBonus: number;
  userId: string;
  campaignId?: string;
  stats: CharacterStats;
  abilities: CharacterAbility[];
  skills: CharacterSkill[];
  equipment: Equipment[];
  spells: Spell[];
  features: CharacterFeature[];
  background: CharacterBackground;
  personality: CharacterPersonality;
  health: CharacterHealth;
  resources: CharacterResource[];
  memories: CharacterMemory[];
  aiModel?: string;
  learningEnabled: boolean;
  portrait?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CharacterStats {
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
  strengthMod: number;
  dexterityMod: number;
  constitutionMod: number;
  intelligenceMod: number;
  wisdomMod: number;
  charismaMod: number;
}

export interface CharacterAbility {
  name: string;
  score: number;
  modifier: number;
  savingThrow: boolean;
  savingThrowMod: number;
}

export interface CharacterSkill {
  name: string;
  ability: string;
  proficiency: boolean;
  expertise: boolean;
  bonus: number;
  mod: number;
}

export interface CharacterHealth {
  max: number;
  current: number;
  temp: number;
  hitDice: string;
  hitDiceUsed: number;
  deathSaves: {
    successes: number;
    failures: number;
  };
}

export interface CharacterResource {
  name: string;
  current: number;
  max: number;
  resetType: 'short_rest' | 'long_rest' | 'dawn' | 'custom';
  description?: string;
}

export interface Equipment {
  id: string;
  name: string;
  type: string;
  rarity: string;
  quantity: number;
  weight: number;
  value: number;
  description: string;
  properties: string[];
  attuned: boolean;
  equipped: boolean;
}

export interface Spell {
  id: string;
  name: string;
  level: number;
  school: string;
  castingTime: string;
  range: string;
  components: string;
  duration: string;
  concentration: boolean;
  description: string;
  prepared: boolean;
  ritual: boolean;
  classes: string[];
}

export interface CharacterFeature {
  id: string;
  name: string;
  description: string;
  source: string;
  level: number;
  uses?: {
    current: number;
    max: number;
    resetType: string;
  };
}

export interface CharacterBackground {
  name: string;
  trait: string;
  ideal: string;
  bond: string;
  flaw: string;
  personalityTraits: string[];
}

export interface CharacterPersonality {
  alignment: string;
  age: number;
  height: string;
  weight: string;
  eyes: string;
  skin: string;
  hair: string;
  appearance: string;
  backstory: string;
  allies: string;
  enemies: string;
  organization: string;
  additionalInfo: string;
}

export interface CharacterMemory {
  id: string;
  title: string;
  content: string;
  importance: number;
  tags: string[];
  session?: string;
  createdAt: string;
  isPrivate: boolean;
}

export interface Session {
  id: string;
  campaignId: string;
  name: string;
  description?: string;
  sessionNumber: number;
  startTime: string;
  endTime?: string;
  status: 'planned' | 'active' | 'paused' | 'completed' | 'cancelled';
  participants: SessionParticipant[];
  transcript: SessionTranscriptEntry[];
  combat: Combat;
  diceRolls: DiceRoll[];
  decisions: Decision[];
  location?: string;
  notes: string;
  createdAt: string;
  updatedAt: string;
}

export interface SessionParticipant {
  userId: string;
  user: User;
  characterId?: string;
  character?: Character;
  joinedAt: string;
  isConnected: boolean;
}

export interface SessionTranscriptEntry {
  id: string;
  timestamp: string;
  type: 'speech' | 'action' | 'dice_roll' | 'combat' | 'system';
  userId?: string;
  characterId?: string;
  content: string;
  metadata?: any;
}

export interface Combat {
  isActive: boolean;
  round: number;
  turn: number;
  initiative: Combatant[];
  effects: CombatEffect[];
  environment: CombatEnvironment;
}

export interface Combatant {
  id: string;
  name: string;
  type: 'player' | 'npc' | 'monster';
  userId?: string;
  characterId?: string;
  initiative: number;
  health: {
    current: number;
    max: number;
    temp: number;
  };
  ac: number;
  speed: number;
  conditions: string[];
  effects: CombatEffect[];
  position?: {
    x: number;
    y: number;
  };
}

export interface CombatEffect {
  id: string;
  name: string;
  type: string;
  duration?: {
    rounds: number;
    turns: number;
  };
  description: string;
  source: string;
  createdAt: string;
}

export interface CombatEnvironment {
  name: string;
  description: string;
  size: {
    width: number;
    height: number;
  };
  terrain: string;
  lighting: string;
  weather?: string;
  effects: string[];
}

export interface DiceRoll {
  id: string;
  userId: string;
  characterId?: string;
  type: string;
  formula: string;
  rolls: DiceRollResult[];
  total: number;
  modifier: number;
  reason: string;
  timestamp: string;
  isCritical: boolean;
  isFumble: boolean;
}

export interface DiceRollResult {
  type: string;
  value: number;
  rolled: number;
}

export interface Decision {
  id: string;
  characterId: string;
  sessionId: string;
  situation: string;
  context: any;
  choice: string;
  outcome?: any;
  reflection?: string;
  teachingMoment: boolean;
  timestamp: string;
}

export interface VoiceChannel {
  id: string;
  campaignId: string;
  name: string;
  type: 'voice' | 'video';
  participants: VoiceParticipant[];
  isActive: boolean;
  quality: number;
  createdAt: string;
}

export interface VoiceParticipant {
  userId: string;
  user: User;
  isMuted: boolean;
  isDeafened: boolean;
  isSpeaking: boolean;
  volume: number;
  joinedAt: string;
}

export interface ChatMessage {
  id: string;
  campaignId: string;
  userId: string;
  user: User;
  characterId?: string;
  character?: Character;
  content: string;
  type: 'text' | 'dice' | 'image' | 'system';
  timestamp: string;
  editedAt?: string;
  reactions: MessageReaction[];
  replyTo?: string;
  isPrivate: boolean;
  recipients?: string[];
}

export interface MessageReaction {
  emoji: string;
  userIds: string[];
}

export interface Notification {
  id: string;
  userId: string;
  type: 'session_reminder' | 'turn_alert' | 'level_up' | 'message' | 'invite' | 'system';
  title: string;
  body: string;
  data?: any;
  isRead: boolean;
  createdAt: string;
  expiresAt?: string;
}

export interface ARMarker {
  id: string;
  name: string;
  type: 'miniature' | 'terrain' | 'prop' | 'effect';
  model?: string;
  image?: string;
  size: {
    width: number;
    height: number;
    depth: number;
  };
  position?: {
    x: number;
    y: number;
    z: number;
  };
  rotation?: {
    x: number;
    y: number;
    z: number;
  };
  scale: number;
  animation?: string;
}

export interface AppState {
  isLoading: boolean;
  isInitialized: boolean;
  isOnline: boolean;
  currentUser: User | null;
  activeCampaign: Campaign | null;
  activeSession: Session | null;
  error: string | null;
  syncStatus: 'synced' | 'syncing' | 'offline' | 'error';
}

export interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginationParams {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}