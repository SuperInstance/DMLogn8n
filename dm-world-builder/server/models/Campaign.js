const mongoose = require('mongoose');

const characterSchema = new mongoose.Schema({
  id: { type: String, required: true },
  name: { type: String, required: true },
  type: { type: String, enum: ['player', 'npc', 'monster'], required: true },
  level: { type: Number, default: 1 },
  class: String,
  race: String,
  stats: {
    strength: { type: Number, default: 10 },
    dexterity: { type: Number, default: 10 },
    constitution: { type: Number, default: 10 },
    intelligence: { type: Number, default: 10 },
    wisdom: { type: Number, default: 10 },
    charisma: { type: Number, default: 10 }
  },
  health: {
    current: { type: Number, required: true },
    max: { type: Number, required: true },
    temp: { type: Number, default: 0 }
  },
  position: {
    x: { type: Number, default: 0 },
    y: { type: Number, default: 0 },
    locationId: String,
    zoneId: String
  },
  status: { type: String, enum: ['alive', 'dead', 'unconscious', 'stable'], default: 'alive' },
  conditions: [String],
  inventory: [{
    id: String,
    name: String,
    quantity: Number,
    description: String
  }],
  equipment: {
    weapon: String,
    armor: String,
    shield: String,
    accessories: [String]
  },
  spells: [{
    name: String,
    level: Number,
    prepared: Boolean,
    used: Boolean
  }],
  abilities: [{
    name: String,
    description: String,
    uses: Number,
    maxUses: Number
  }],
  backstory: String,
  personality: String,
  goals: [String],
  relationships: [{
    characterId: String,
    relationship: String,
    description: String
  }],
  playerId: String,
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now }
});

const locationSchema = new mongoose.Schema({
  id: { type: String, required: true },
  name: { type: String, required: true },
  type: {
    type: String,
    enum: ['city', 'dungeon', 'forest', 'mountain', 'desert', 'ocean', 'building', 'room', 'wilderness', 'custom'],
    required: true
  },
  description: { type: String, required: true },
  detailedDescription: String,
  position: {
    x: { type: Number, default: 0 },
    y: { type: Number, default: 0 },
    z: { type: Number, default: 0 }
  },
  size: {
    width: { type: Number, default: 10 },
    height: { type: Number, default: 10 },
    length: { type: Number, default: 10 }
  },
  connections: [{
    locationId: String,
    direction: String,
    description: String,
    locked: Boolean,
    keyRequired: String
  }],
  npcs: [characterSchema],
  items: [{
    id: String,
    name: String,
    quantity: Number,
    description: String,
    rarity: String,
    value: Number
  }],
  traps: [{
    id: String,
    name: String,
    description: String,
    difficulty: Number,
    damage: String,
    triggered: Boolean
  }],
  secrets: [{
    description: String,
    discovered: Boolean,
    discoveredBy: String,
    discoveredAt: Date
  }],
  atmosphere: String,
  lighting: { type: String, enum: ['bright', 'normal', 'dim', 'dark'], default: 'normal' },
  weather: {
    type: String,
    enum: ['clear', 'cloudy', 'rain', 'storm', 'snow', 'fog', 'windy', 'magical'],
    default: 'clear'
  },
  sounds: [String],
  smells: [String],
  customProperties: mongoose.Schema.Types.Mixed,
  mapImage: String,
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now }
});

const questSchema = new mongoose.Schema({
  id: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
  type: {
    type: String,
    enum: ['main', 'side', 'personal', 'faction', 'exploration', 'combat', 'social', 'mystery'],
    default: 'side'
  },
  status: {
    type: String,
    enum: ['available', 'active', 'completed', 'failed', 'paused'],
    default: 'available'
  },
  objectives: [{
    id: String,
    description: String,
    completed: Boolean,
    completedBy: String,
    completedAt: Date,
    required: Boolean
  }],
  rewards: {
    experience: { type: Number, default: 0 },
    gold: { type: Number, default: 0 },
    items: [String],
    renown: { type: Number, default: 0 },
    custom: String
  },
  requirements: {
    level: { type: Number, default: 1 },
    prerequisites: [String],
    classes: [String],
    skills: [String],
    items: [String]
  },
  giverId: String,
  giverName: String,
  locationId: String,
  timeLimit: Date,
  difficulty: { type: String, enum: ['easy', 'medium', 'hard', 'deadly'], default: 'medium' },
  assignedTo: [String],
  createdAt: { type: Date, default: Date.now },
  completedAt: Date
});

const sessionSchema = new mongoose.Schema({
  id: { type: String, required: true },
  campaignId: { type: String, required: true },
  title: { type: String, required: true },
  description: String,
  notes: String,
  startTime: { type: Date, required: true },
  endTime: Date,
  events: [{
    type: { type: String, required: true },
    description: String,
    timestamp: { type: Date, default: Date.now },
    characters: [String],
    location: String,
    outcome: String
  }],
  characters: [String],
  locations: [String],
  combatLog: [{
    round: Number,
    character: String,
    action: String,
    target: String,
    result: String,
    timestamp: { type: Date, default: Date.now }
  }],
  experienceAwarded: {
    [characterId: String]: Number
  },
  treasureFound: [{
    name: String,
    value: Number,
    foundBy: String,
    foundAt: { type: Date, default: Date.now }
  }],
  decisions: [{
    description: String,
    madeBy: String,
    consequences: String,
    timestamp: { type: Date, default: Date.now }
  }],
  nextSessionPreview: String,
  createdAt: { type: Date, default: Date.now }
});

const campaignSchema = new mongoose.Schema({
  id: { type: String, required: true, unique: true },
  name: { type: String, required: true },
  description: String,
  dmId: { type: String, required: true },
  players: [{
    id: String,
    name: String,
    email: String,
    joinedAt: { type: Date, default: Date.now }
  }],
  characters: [characterSchema],
  locations: [locationSchema],
  npcs: [characterSchema],
  items: [{
    id: String,
    name: String,
    type: String,
    rarity: String,
    description: String,
    value: Number,
    properties: mongoose.Schema.Types.Mixed,
    imageUrl: String
  }],
  quests: [questSchema],
  sessions: [sessionSchema],
  houseRules: [{
    name: String,
    description: String,
    category: String,
    active: { type: Boolean, default: true }
  }],
  worldSettings: {
    magicLevel: {
      type: String,
      enum: ['none', 'low', 'standard', 'high', 'epic'],
      default: 'standard'
    },
    technologyLevel: {
      type: String,
      enum: ['stone_age', 'ancient', 'medieval', 'renaissance', 'industrial', 'modern'],
      default: 'medieval'
    },
    tone: {
      type: String,
      enum: ['dark', 'serious', 'balanced', 'lighthearted', 'comical'],
      default: 'balanced'
    },
    difficulty: {
      type: String,
      enum: ['easy', 'normal', 'hard', 'deadly'],
      default: 'normal'
    },
    pacing: {
      type: String,
      enum: ['slow', 'normal', 'fast', 'episodic'],
      default: 'normal'
    }
  },
  currentState: {
    sessionActive: { type: Boolean, default: false },
    currentLocation: String,
    inCombat: { type: Boolean, default: false },
    timeOfDay: {
      type: String,
      enum: ['dawn', 'morning', 'noon', 'afternoon', 'evening', 'dusk', 'night', 'midnight'],
      default: 'morning'
    },
    dayCount: { type: Number, default: 1 },
    weather: {
      type: String,
      enum: ['clear', 'cloudy', 'rain', 'storm', 'snow', 'fog', 'windy', 'magical'],
      default: 'clear'
    },
    season: {
      type: String,
      enum: ['spring', 'summer', 'fall', 'winter'],
      default: 'spring'
    }
  },
  calendar: {
    currentYear: { type: Number, default: 1 },
    currentMonth: { type: Number, default: 1 },
    currentDay: { type: Number, default: 1 },
    months: [{
      name: String,
      days: Number,
      season: String
    }],
    holidays: [{
      name: String,
      month: Number,
      day: Number,
      description: String
    }]
  },
  customContent: {
    races: [mongoose.Schema.Types.Mixed],
    classes: [mongoose.Schema.Types.Mixed],
    spells: [mongoose.Schema.Types.Mixed],
    monsters: [mongoose.Schema.Types.Mixed],
    items: [mongoose.Schema.Types.Mixed]
  },
  permissions: {
    public: { type: Boolean, default: false },
    allowJoin: { type: Boolean, default: false },
    requireApproval: { type: Boolean, default: true }
  },
  tags: [String],
  imageUrl: String,
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now },
  lastSessionDate: Date,
  totalSessions: { type: Number, default: 0 }
});

// Indexes for better query performance
campaignSchema.index({ dmId: 1 });
campaignSchema.index({ 'players.id': 1 });
campaignSchema.index({ tags: 1 });
campaignSchema.index({ createdAt: -1 });
campaignSchema.index({ updatedAt: -1 });

// Middleware to update updatedAt field
campaignSchema.pre('save', function(next) {
  this.updatedAt = new Date();
  next();
});

// Virtual for campaign duration
campaignSchema.virtual('duration').get(function() {
  if (this.sessions.length === 0) return 0;
  const firstSession = this.sessions.sort((a, b) => new Date(a.startTime) - new Date(b.startTime))[0];
  const lastSession = this.sessions.sort((a, b) => new Date(b.endTime || b.startTime) - new Date(a.endTime || a.startTime))[0];
  return Math.floor((new Date(lastSession.endTime || lastSession.startTime) - new Date(firstSession.startTime)) / (1000 * 60 * 60 * 24));
});

// Method to get active characters
campaignSchema.methods.getActiveCharacters = function() {
  return this.characters.filter(char => char.status === 'alive' && char.playerId);
};

// Method to get current location
campaignSchema.methods.getCurrentLocation = function() {
  if (!this.currentState.currentLocation) return null;
  return this.locations.find(loc => loc.id === this.currentState.currentLocation);
};

// Method to add session
campaignSchema.methods.addSession = function(sessionData) {
  const session = {
    ...sessionData,
    id: new mongoose.Types.ObjectId().toString(),
    campaignId: this.id,
    createdAt: new Date()
  };
  this.sessions.push(session);
  this.totalSessions = this.sessions.length;
  this.lastSessionDate = session.startTime;
  return session;
};

// Static method to find campaigns by DM
campaignSchema.statics.findByDM = function(dmId) {
  return this.find({ dmId }).sort({ updatedAt: -1 });
};

// Static method to find campaigns player is in
campaignSchema.statics.findByPlayer = function(playerId) {
  return this.find({ 'players.id': playerId }).sort({ updatedAt: -1 });
};

module.exports = mongoose.model('Campaign', campaignSchema);