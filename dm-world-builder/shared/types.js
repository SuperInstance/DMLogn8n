// Shared types and interfaces for the DM World Builder

// Core game entities
export const CharacterType = {
  PLAYER: 'player',
  NPC: 'npc',
  MONSTER: 'monster'
};

export const CharacterStatus = {
  ALIVE: 'alive',
  DEAD: 'dead',
  UNCONSCIOUS: 'unconscious',
  STABLE: 'stable'
};

export const CombatStatus = {
  ACTIVE: 'active',
  HIDING: 'hiding',
  PRONE: 'prone',
  RESTRAINED: 'restrained',
  GRAPPLED: 'grappled',
  STUNNED: 'stunned',
  POISONED: 'poisoned',
  CHARMED: 'charmed',
  FRIGHTENED: 'frightened'
};

// Location and world entities
export const LocationType = {
  CITY: 'city',
  DUNGEON: 'dungeon',
  FOREST: 'forest',
  MOUNTAIN: 'mountain',
  DESERT: 'desert',
  OCEAN: 'ocean',
  BUILDING: 'building',
  ROOM: 'room',
  WILDERNESS: 'wilderness',
  CUSTOM: 'custom'
};

export const WeatherType = {
  CLEAR: 'clear',
  CLOUDY: 'cloudy',
  RAIN: 'rain',
  STORM: 'storm',
  SNOW: 'snow',
  FOG: 'fog',
  WINDY: 'windy',
  MAGICAL: 'magical'
};

// Item and equipment
export const ItemType = {
  WEAPON: 'weapon',
  ARMOR: 'armor',
  POTION: 'potion',
  SCROLL: 'scroll',
  WAND: 'wand',
  MISC: 'misc',
  TREASURE: 'treasure',
  TOOL: 'tool',
  CONTAINER: 'container'
};

export const ItemRarity = {
  COMMON: 'common',
  UNCOMMON: 'uncommon',
  RARE: 'rare',
  VERY_RARE: 'very_rare',
  LEGENDARY: 'legendary',
  ARTIFACT: 'artifact'
};

// Quest and story
export const QuestType = {
  MAIN: 'main',
  SIDE: 'side',
  PERSONAL: 'personal',
  Faction: 'faction',
  EXPLORATION: 'exploration',
  COMBAT: 'combat',
  SOCIAL: 'social',
  MYSTERY: 'mystery'
};

export const QuestStatus = {
  AVAILABLE: 'available',
  ACTIVE: 'active',
  COMPLETED: 'completed',
  FAILED: 'failed',
  PAUSED: 'paused'
};

// Event system
export const EventType = {
  COMBAT: 'combat',
  DIALOGUE: 'dialogue',
  DISCOVERY: 'discovery',
  TRAP: 'trap',
  PUZZLE: 'puzzle',
  SKILL_CHECK: 'skill_check',
  ENVIRONMENTAL: 'environmental',
  CUSTOM: 'custom'
};

// Socket events
export const SocketEvents = {
  // Connection events
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  JOIN_CAMPAIGN: 'join_campaign',
  LEAVE_CAMPAIGN: 'leave_campaign',

  // Game state events
  GAME_STATE_UPDATE: 'game_state_update',
  CHARACTER_UPDATE: 'character_update',
  LOCATION_UPDATE: 'location_update',
  COMBAT_UPDATE: 'combat_update',

  // Real-time events
  CHARACTER_ACTION: 'character_action',
  COMBAT_START: 'combat_start',
  COMBAT_END: 'combat_end',
  INITIATIVE_ROLL: 'initiative_roll',

  // DM events
  INJECT_EVENT: 'inject_event',
  SPAWN_CREATURE: 'spawn_creature',
  MODIFY_ENVIRONMENT: 'modify_environment',

  // Campaign management
  CAMPAIGN_SAVE: 'campaign_save',
  CAMPAIGN_LOAD: 'campaign_load',
  SESSION_START: 'session_start',
  SESSION_END: 'session_end'
};

// Base schemas
export const createCharacterSchema = () => ({
  id: '',
  name: '',
  type: CharacterType.PLAYER,
  level: 1,
  class: '',
  race: '',
  stats: {
    strength: 10,
    dexterity: 10,
    constitution: 10,
    intelligence: 10,
    wisdom: 10,
    charisma: 10
  },
  health: {
    current: 10,
    max: 10,
    temp: 0
  },
  position: {
    x: 0,
    y: 0,
    locationId: '',
    zoneId: ''
  },
  status: CharacterStatus.ALIVE,
  conditions: [],
  inventory: [],
  equipment: {},
  spells: [],
  abilities: [],
  backstory: '',
  personality: '',
  goals: [],
  relationships: [],
  createdAt: new Date(),
  updatedAt: new Date()
});

export const createLocationSchema = () => ({
  id: '',
  name: '',
  type: LocationType.ROOM,
  description: '',
  detailedDescription: '',
  position: {
    x: 0,
    y: 0,
    z: 0
  },
  size: {
    width: 10,
    height: 10,
    length: 10
  },
  connections: [],
  npcs: [],
  items: [],
  traps: [],
  secrets: [],
  atmosphere: '',
  lighting: 'normal',
  weather: WeatherType.CLEAR,
  sounds: [],
  smells: [],
  customProperties: {},
  mapImage: '',
  createdAt: new Date(),
  updatedAt: new Date()
});

export const createCampaignSchema = () => ({
  id: '',
  name: '',
  description: '',
  dmId: '',
  players: [],
  characters: [],
  locations: [],
  npcs: [],
  items: [],
  quests: [],
  encounters: [],
  sessions: [],
  houseRules: [],
  worldSettings: {
    magicLevel: 'standard',
    technologyLevel: 'medieval',
    tone: 'fantasy'
  },
  currentState: {
    sessionActive: false,
    currentLocation: '',
    inCombat: false,
    timeOfDay: 'morning',
    dayCount: 1
  },
  createdAt: new Date(),
  updatedAt: new Date()
});

export const createEventSchema = () => ({
  id: '',
  type: EventType.CUSTOM,
  title: '',
  description: '',
  trigger: '',
  effects: [],
  conditions: [],
  once: false,
  active: true,
  createdAt: new Date(),
  triggeredAt: null
});

export const createQuestSchema = () => ({
  id: '',
  title: '',
  description: '',
  type: QuestType.SIDE,
  status: QuestStatus.AVAILABLE,
  objectives: [],
  rewards: {
    experience: 0,
    gold: 0,
    items: [],
    renown: 0
  },
  requirements: {
    level: 1,
    prerequisites: [],
    classes: [],
    skills: []
  },
  giverId: '',
  locationId: '',
  timeLimit: null,
  difficulty: 'medium',
  createdAt: new Date(),
  completedAt: null
});

export const createCombatSchema = () => ({
  id: '',
  locationId: '',
  participants: [],
  initiative: [],
  currentTurn: 0,
  round: 1,
  status: 'active',
  environment: {},
  startedAt: new Date(),
  endedAt: null
});

export const createSessionSchema = () => ({
  id: '',
  campaignId: '',
  title: '',
  notes: '',
  startTime: new Date(),
  endTime: null,
  events: [],
  characters: [],
  locations: [],
  combatLog: [],
  experienceAwarded: {},
  treasureFound: [],
  decisions: [],
  nextSessionPreview: '',
  createdAt: new Date()
});