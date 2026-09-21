const Joi = require('joi');

// User validation schemas
const validateUser = (user) => {
  const schema = Joi.object({
    name: Joi.string().min(2).max(50).required(),
    email: Joi.string().email().required(),
    password: Joi.string().min(8).required().pattern(new RegExp('^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#\$%\^&\*])')),
    avatar: Joi.string().uri().optional()
  });

  return schema.validate(user);
};

const validateLogin = (login) => {
  const schema = Joi.object({
    email: Joi.string().email().required(),
    password: Joi.string().required()
  });

  return schema.validate(login);
};

// Campaign validation schemas
const validateCampaign = (campaign) => {
  const schema = Joi.object({
    name: Joi.string().min(1).max(100).required(),
    description: Joi.string().max(1000).optional(),
    worldSettings: Joi.object({
      magicLevel: Joi.string().valid('none', 'low', 'standard', 'high', 'epic').default('standard'),
      technologyLevel: Joi.string().valid('stone_age', 'ancient', 'medieval', 'renaissance', 'industrial', 'modern').default('medieval'),
      tone: Joi.string().valid('dark', 'serious', 'balanced', 'lighthearted', 'comical').default('balanced'),
      difficulty: Joi.string().valid('easy', 'normal', 'hard', 'deadly').default('normal'),
      pacing: Joi.string().valid('slow', 'normal', 'fast', 'episodic').default('normal')
    }).optional(),
    permissions: Joi.object({
      public: Joi.boolean().default(false),
      allowJoin: Joi.boolean().default(false),
      requireApproval: Joi.boolean().default(true)
    }).optional(),
    tags: Joi.array().items(Joi.string().max(20)).max(10).optional()
  });

  return schema.validate(campaign);
};

// Character validation schemas
const validateCharacter = (character) => {
  const schema = Joi.object({
    name: Joi.string().min(1).max(50).required(),
    type: Joi.string().valid('player', 'npc', 'monster').required(),
    level: Joi.number().integer().min(1).max(20).default(1),
    class: Joi.string().max(30).optional(),
    race: Joi.string().max(30).optional(),
    stats: Joi.object({
      strength: Joi.number().integer().min(1).max(20).default(10),
      dexterity: Joi.number().integer().min(1).max(20).default(10),
      constitution: Joi.number().integer().min(1).max(20).default(10),
      intelligence: Joi.number().integer().min(1).max(20).default(10),
      wisdom: Joi.number().integer().min(1).max(20).default(10),
      charisma: Joi.number().integer().min(1).max(20).default(10)
    }).optional(),
    health: Joi.object({
      current: Joi.number().integer().min(0).required(),
      max: Joi.number().integer().min(1).required(),
      temp: Joi.number().integer().min(0).default(0)
    }).optional(),
    position: Joi.object({
      x: Joi.number().default(0),
      y: Joi.number().default(0),
      locationId: Joi.string().optional(),
      zoneId: Joi.string().optional()
    }).optional(),
    backstory: Joi.string().max(2000).optional(),
    personality: Joi.string().max(500).optional(),
    goals: Joi.array().items(Joi.string().max(200)).max(10).optional()
  });

  return schema.validate(character);
};

// Location validation schemas
const validateLocation = (location) => {
  const schema = Joi.object({
    name: Joi.string().min(1).max(100).required(),
    type: Joi.string().valid(
      'city', 'dungeon', 'forest', 'mountain', 'desert', 'ocean',
      'building', 'room', 'wilderness', 'custom'
    ).required(),
    description: Joi.string().min(1).max(1000).required(),
    detailedDescription: Joi.string().max(5000).optional(),
    position: Joi.object({
      x: Joi.number().default(0),
      y: Joi.number().default(0),
      z: Joi.number().default(0)
    }).optional(),
    size: Joi.object({
      width: Joi.number().integer().min(1).default(10),
      height: Joi.number().integer().min(1).default(10),
      length: Joi.number().integer().min(1).default(10)
    }).optional(),
    atmosphere: Joi.string().max(500).optional(),
    lighting: Joi.string().valid('bright', 'normal', 'dim', 'dark').default('normal'),
    weather: Joi.string().valid(
      'clear', 'cloudy', 'rain', 'storm', 'snow', 'fog', 'windy', 'magical'
    ).default('clear'),
    sounds: Joi.array().items(Joi.string().max(100)).max(10).optional(),
    smells: Joi.array().items(Joi.string().max(100)).max(10).optional()
  });

  return schema.validate(location);
};

// Quest validation schemas
const validateQuest = (quest) => {
  const schema = Joi.object({
    title: Joi.string().min(1).max(100).required(),
    description: Joi.string().min(1).max(2000).required(),
    type: Joi.string().valid(
      'main', 'side', 'personal', 'faction', 'exploration',
      'combat', 'social', 'mystery'
    ).default('side'),
    difficulty: Joi.string().valid('easy', 'medium', 'hard', 'deadly').default('medium'),
    objectives: Joi.array().items(
      Joi.object({
        id: Joi.string().required(),
        description: Joi.string().min(1).max(500).required(),
        completed: Joi.boolean().default(false),
        required: Joi.boolean().default(true)
      })
    ).min(1).required(),
    rewards: Joi.object({
      experience: Joi.number().integer().min(0).default(0),
      gold: Joi.number().integer().min(0).default(0),
      items: Joi.array().items(Joi.string()).max(20).default([]),
      renown: Joi.number().integer().min(0).default(0),
      custom: Joi.string().max(500).optional()
    }).optional(),
    requirements: Joi.object({
      level: Joi.number().integer().min(1).default(1),
      prerequisites: Joi.array().items(Joi.string()).max(10).default([]),
      classes: Joi.array().items(Joi.string()).max(10).default([]),
      skills: Joi.array().items(Joi.string()).max(10).default([]),
      items: Joi.array().items(Joi.string()).max(10).default([])
    }).optional(),
    timeLimit: Joi.date().optional(),
    giverId: Joi.string().optional(),
    giverName: Joi.string().max(50).optional(),
    locationId: Joi.string().optional()
  });

  return schema.validate(quest);
};

// Session validation schemas
const validateSession = (session) => {
  const schema = Joi.object({
    title: Joi.string().min(1).max(100).required(),
    description: Joi.string().max(1000).optional(),
    notes: Joi.string().max(5000).optional(),
    startTime: Joi.date().required(),
    endTime: Joi.date().optional(),
    characters: Joi.array().items(Joi.string()).max(10).optional(),
    locations: Joi.array().items(Joi.string()).max(20).optional(),
    nextSessionPreview: Joi.string().max(1000).optional()
  });

  return schema.validate(session);
};

// Item validation schemas
const validateItem = (item) => {
  const schema = Joi.object({
    name: Joi.string().min(1).max(100).required(),
    type: Joi.string().valid(
      'weapon', 'armor', 'potion', 'scroll', 'wand',
      'misc', 'treasure', 'tool', 'container'
    ).required(),
    rarity: Joi.string().valid(
      'common', 'uncommon', 'rare', 'very_rare', 'legendary', 'artifact'
    ).default('common'),
    description: Joi.string().max(1000).optional(),
    value: Joi.number().integer().min(0).default(0),
    properties: Joi.object().optional()
  });

  return schema.validate(item);
};

module.exports = {
  validateUser,
  validateLogin,
  validateCampaign,
  validateCharacter,
  validateLocation,
  validateQuest,
  validateSession,
  validateItem
};