export const QUEST_CONFIG = {
  // Quest Types
  QUEST_TYPES: {
    MAIN_STORY: 'main_story',
    SIDE_QUEST: 'side_quest',
    DAILY: 'daily',
    WEEKLY: 'weekly',
    EVENT: 'event',
    PLAYER_GENERATED: 'player_generated',
    GUILD: 'guild',
    RAID: 'raid',
    TUTORIAL: 'tutorial',
    HIDDEN: 'hidden'
  },

  // Quest Categories
  CATEGORIES: {
    COMBAT: 'combat',
    EXPLORATION: 'exploration',
    SOCIAL: 'social',
    CRAFTING: 'crafting',
    MYSTERY: 'mystery',
    COLLECTION: 'collection',
    ESCORT: 'escort',
    DELIVERY: 'delivery',
    BOSS_BATTLE: 'boss_battle',
    DUNGEON: 'dungeon'
  },

  // Difficulty Levels
  DIFFICULTY: {
    TRIVIAL: 1,
    EASY: 2,
    NORMAL: 3,
    HARD: 4,
    EXPERT: 5,
    LEGENDARY: 6,
    MYTHIC: 7
  },

  // Quest States
  STATES: {
    DRAFT: 'draft',
    ACTIVE: 'active',
    IN_PROGRESS: 'in_progress',
    COMPLETED: 'completed',
    FAILED: 'failed',
    ABANDONED: 'abandoned',
    EXPIRED: 'expired',
    CANCELLED: 'cancelled'
  },

  // Objective Types
  OBJECTIVE_TYPES: {
    KILL: 'kill',
    COLLECT: 'collect',
    DELIVER: 'deliver',
    TALK_TO: 'talk_to',
    EXPLORE: 'explore',
    ESCORT: 'escort',
    DEFEND: 'defend',
    SURVIVE: 'survive',
    CRAFT: 'craft',
    USE_ITEM: 'use_item',
    REACH_LOCATION: 'reach_location',
    COMPLETE_DUNGEON: 'complete_dungeon',
    DEFEAT_BOSS: 'defeat_boss',
    SOCIAL_INTERACTION: 'social_interaction',
    SKILL_CHECK: 'skill_check',
    CHOICE: 'choice'
  },

  // Reward Types
  REWARD_TYPES: {
    EXPERIENCE: 'experience',
    GOLD: 'gold',
    ITEM: 'item',
    EQUIPMENT: 'equipment',
    REPUTATION: 'reputation',
    SKILL_POINT: 'skill_point',
    ABILITY: 'ability',
    TITLE: 'title',
    ACCESS: 'access',
    CUSTOM: 'custom'
  },

  // Quest Generation Parameters
  GENERATION: {
    MAX_OBJECTIVES_PER_QUEST: 10,
    MIN_OBJECTIVES_PER_QUEST: 1,
    MAX_REWARDS_PER_QUEST: 8,
    MIN_REWARDS_PER_QUEST: 1,
    QUEST_DURATION_DAYS: {
      DAILY: 1,
      WEEKLY: 7,
      MONTHLY: 30,
      EVENT: 14,
      NORMAL: 30
    },
    COOLDOWN_HOURS: {
      DAILY: 22,
      WEEKLY: 166,
      GENERATION: 1
    }
  },

  // Personalization Weights
  PERSONALIZATION_WEIGHTS: {
    PLAYER_HISTORY: 0.3,
    CHARACTER_CLASS: 0.2,
    PREFERENCES: 0.25,
    PARTY_COMPOSITION: 0.15,
    WORLD_STATE: 0.1
  },

  // AI Generation Settings
  AI_GENERATION: {
    TEMPERATURE: 0.7,
    MAX_TOKENS: 4000,
    TOP_P: 0.9,
    FREQUENCY_PENALTY: 0.5,
    PRESENCE_PENALTY: 0.3,
    STORY_TEMPLATES: [
      'hero_journey',
      'mystery_investigation',
      'rescue_mission',
      'exploration_discovery',
      'political_intrigue',
      'personal_redemption',
      'revenge_justice',
      'protection_defense'
    ]
  },

  // Branching Narrative Settings
  NARRATIVE: {
    MAX_BRANCHES_PER_QUEST: 8,
    MAX_CHOICES_PER_OBJECTIVE: 4,
    CONSEQUENCE_DEPTH: 3,
    MORAL_ALIGNMENT_IMPACT: true,
    RELATIONSHIP_IMPACT: true,
    WORLD_STATE_IMPACT: true
  },

  // Social Features
  SOCIAL: {
    MAX_PARTY_SIZE: 6,
    SHARED_PROGRESS_WEIGHT: 0.8,
    GUILD_QUEST_REQUIREMENT: 3,
    LEADERBOARD_ENTRIES: 100,
    SOCIAL_SHARE_BONUS: 1.1
  },

  // Achievement Integration
  ACHIEVEMENTS: {
    QUEST_COMPLETED_POINTS: 10,
    DIFFICULTY_MULTIPLIER: {
      1: 0.5,
      2: 0.75,
      3: 1.0,
      4: 1.5,
      5: 2.0,
      6: 3.0,
      7: 5.0
    },
    BONUS_CONDITIONS: [
      'perfect_completion',
      'speed_run',
      'minimal_casualties',
      'all_side_objectives',
      'special_choice_path'
    ]
  }
}

export const VALIDATION_RULES = {
  QUEST_TITLE: {
    MIN_LENGTH: 5,
    MAX_LENGTH: 100,
    PATTERN: /^[a-zA-Z0-9\s\-_.,!?']+$/
  },
  QUEST_DESCRIPTION: {
    MIN_LENGTH: 50,
    MAX_LENGTH: 2000,
    PATTERN: /^[a-zA-Z0-9\s\-_.,!?'"():;]+$/
  },
  OBJECTIVE_DESCRIPTION: {
    MIN_LENGTH: 10,
    MAX_LENGTH: 500
  },
  REWARD_AMOUNT: {
    MIN: 1,
    MAX: 1000000
  },
  LEVEL_REQUIREMENT: {
    MIN: 1,
    MAX: 100
  }
}