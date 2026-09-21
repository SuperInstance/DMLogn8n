import { v4 as uuidv4 } from 'uuid'
import { QUEST_CONFIG } from '../../config/quest-config.js'
import { RewardCalculator } from './RewardCalculator.js'

export class QuestTemplateEngine {
  constructor() {
    this.templates = new Map()
    this.loadTemplates()
    this.rewardCalculator = new RewardCalculator()
  }

  /**
   * Load quest templates
   */
  loadTemplates() {
    // Combat Templates
    this.templates.set('monster_hunt', {
      type: QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST,
      category: QUEST_CONFIG.CATEGORIES.COMBAT,
      titleTemplate: 'Hunt the {monster_type}',
      descriptionTemplate: 'A dangerous {monster_type} has been terrorizing {location}. The locals are offering a reward for its elimination.',
      objectives: [
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.KILL,
          target: '{monster_type}',
          required: 1,
          description: 'Defeat the {monster_type}'
        },
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.REACH_LOCATION,
          target: '{location}',
          required: 1,
          description: 'Travel to {location}'
        }
      ],
      rewards: {
        base: [
          { type: QUEST_CONFIG.REWARD_TYPES.GOLD, amount: 100 },
          { type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE, amount: 500 }
        ]
      },
      difficulty: 3,
      tags: ['combat', 'monster', 'hunting']
    })

    this.templates.set('dungeon_crawl', {
      type: QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST,
      category: QUEST_CONFIG.CATEGORIES.DUNGEON,
      titleTemplate: 'Explore the {dungeon_name}',
      descriptionTemplate: 'Ancient treasures and deadly creatures await in the depths of {dungeon_name}. Brave adventurers are needed to clear the dungeon.',
      objectives: [
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.COMPLETE_DUNGEON,
          target: '{dungeon_name}',
          required: 1,
          description: 'Clear {dungeon_name} of all threats'
        },
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.COLLECT,
          target: 'artifact',
          required: 3,
          description: 'Collect 3 ancient artifacts'
        }
      ],
      rewards: {
        base: [
          { type: QUEST_CONFIG.REWARD_TYPES.GOLD, amount: 300 },
          { type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE, amount: 1000 },
          { type: QUEST_CONFIG.REWARD_TYPES.EQUIPMENT, amount: 1, rarity: 'rare' }
        ]
      },
      difficulty: 4,
      tags: ['dungeon', 'exploration', 'treasure']
    })

    // Exploration Templates
    this.templates.set('lost_ruins', {
      type: QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST,
      category: QUEST_CONFIG.CATEGORIES.EXPLORATION,
      titleTemplate: 'Discover the {ruin_type} Ruins',
      descriptionTemplate: 'Rumors speak of ancient {ruin_type} ruins hidden in the {region}. Scholars believe they contain valuable historical artifacts and forgotten knowledge.',
      objectives: [
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.EXPLORE,
          target: '{ruin_name}',
          required: 1,
          description: 'Find and explore the {ruin_type} ruins'
        },
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.COLLECT,
          target: 'ancient_scroll',
          required: 5,
          description: 'Collect 5 ancient scrolls'
        }
      ],
      rewards: {
        base: [
          { type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE, amount: 750 },
          { type: QUEST_CONFIG.REWARD_TYPES.SKILL_POINT, amount: 1 }
        ]
      },
      difficulty: 3,
      tags: ['exploration', 'history', 'discovery']
    })

    this.templates.set('mapping_expedition', {
      type: QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST,
      category: QUEST_CONFIG.CATEGORIES.EXPLORATION,
      titleTemplate: 'Map the {area_name}',
      descriptionTemplate: 'The Cartographers Guild needs accurate maps of the {area_name}. Venture into the unknown and chart the terrain.',
      objectives: [
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.EXPLORE,
          target: '{area_name}',
          required: 5,
          description: 'Discover 5 new locations in {area_name}'
        },
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.USE_ITEM,
          target: 'mapping_tools',
          required: 5,
          description: 'Use mapping tools at each location'
        }
      ],
      rewards: {
        base: [
          { type: QUEST_CONFIG.REWARD_TYPES.GOLD, amount: 200 },
          { type: QUEST_CONFIG.REWARD_TYPES.REPUTATION, amount: 50, faction: 'Cartographers Guild' }
        ]
      },
      difficulty: 2,
      tags: ['exploration', 'mapping', 'discovery']
    })

    // Social Templates
    this.templates.set('diplomatic_mission', {
      type: QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST,
      category: QUEST_CONFIG.CATEGORIES.SOCIAL,
      titleTemplate: 'Negotiate with {faction_name}',
      descriptionTemplate: 'Tensions are rising between {faction_name} and the local council. A skilled diplomat is needed to negotiate peace.',
      objectives: [
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.TALK_TO,
          target: '{faction_leader}',
          required: 1,
          description: 'Speak with {faction_leader}'
        },
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.SOCIAL_INTERACTION,
          target: 'negotiation',
          required: 3,
          description: 'Successfully complete 3 negotiation checks'
        }
      ],
      rewards: {
        base: [
          { type: QUEST_CONFIG.REWARD_TYPES.REPUTATION, amount: 100, faction: '{faction_name}' },
          { type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE, amount: 400 }
        ]
      },
      difficulty: 3,
      tags: ['social', 'diplomacy', 'negotiation']
    })

    this.templates.set('escort_mission', {
      type: QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST,
      category: QUEST_CONFIG.CATEGORIES.ESCORT,
      titleTemplate: 'Escort {npc_name} to {destination}',
      descriptionTemplate: '{npc_name} needs safe passage to {destination}. The journey is dangerous and requires skilled protection.',
      objectives: [
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.ESCORT,
          target: '{npc_name}',
          required: 1,
          description: 'Safely escort {npc_name} to {destination}'
        },
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.DEFEND,
          target: '{npc_name}',
          required: 3,
          description: 'Protect {npc_name} from 3 attacks'
        }
      ],
      rewards: {
        base: [
          { type: QUEST_CONFIG.REWARD_TYPES.GOLD, amount: 150 },
          { type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE, amount: 350 }
        ]
      },
      difficulty: 3,
      tags: ['escort', 'protection', 'travel']
    })

    // Mystery Templates
    this.templates.set('missing_person', {
      type: QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST,
      category: QUEST_CONFIG.CATEGORIES.MYSTERY,
      titleTemplate: 'Find the Missing {person_type}',
      descriptionTemplate: '{person_name}, a local {person_type}, has gone missing under mysterious circumstances. Investigate their disappearance.',
      objectives: [
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.EXPLORE,
          target: 'crime_scene',
          required: 1,
          description: 'Investigate the {person_type}\'s last known location'
        },
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.TALK_TO,
          target: 'witness',
          required: 3,
          description: 'Question 3 witnesses'
        },
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.COLLECT,
          target: 'clue',
          required: 5,
          description: 'Gather 5 clues about the disappearance'
        }
      ],
      rewards: {
        base: [
          { type: QUEST_CONFIG.REWARD_TYPES.GOLD, amount: 250 },
          { type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE, amount: 600 }
        ]
      },
      difficulty: 4,
      tags: ['mystery', 'investigation', 'missing_person']
    })

    this.templates.set('ancient_prophecy', {
      type: QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST,
      category: QUEST_CONFIG.CATEGORIES.MYSTERY,
      titleTemplate: 'Fulfill the {prophecy_type} Prophecy',
      descriptionTemplate: 'An ancient prophecy speaks of a {prophecy_type} event. Your actions may determine its outcome.',
      objectives: [
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.EXPLORE,
          target: 'prophecy_site',
          required: 1,
          description: 'Visit the ancient prophecy site'
        },
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.SKILL_CHECK,
          target: 'ancient_knowledge',
          required: 1,
          description: 'Decipher the prophecy text'
        },
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.CHOICE,
          target: 'prophecy_fulfillment',
          required: 1,
          description: 'Choose how to fulfill the prophecy'
        }
      ],
      rewards: {
        base: [
          { type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE, amount: 800 },
          { type: QUEST_CONFIG.REWARD_TYPES.ABILITY, amount: 1 }
        ]
      },
      difficulty: 5,
      tags: ['mystery', 'prophecy', 'ancient'],
      branching: true
    })

    // Crafting Templates
    this.templates.set('masterwork_crafting', {
      type: QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST,
      category: QUEST_CONFIG.CATEGORIES.CRAFTING,
      titleTemplate: 'Craft {item_name}',
      descriptionTemplate: 'A legendary {item_name} is needed for an important ritual. Only the finest materials and craftsmanship will suffice.',
      objectives: [
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.COLLECT,
          target: 'rare_material',
          required: 10,
          description: 'Gather 10 rare materials'
        },
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.CRAFT,
          target: '{item_name}',
          required: 1,
          description: 'Craft the {item_name}'
        }
      ],
      rewards: {
        base: [
          { type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE, amount: 500 },
          { type: QUEST_CONFIG.REWARD_TYPES.SKILL_POINT, amount: 2 }
        ],
        bonus: [
          { type: QUEST_CONFIG.REWARD_TYPES.EQUIPMENT, amount: 1, rarity: 'epic' }
        ]
      },
      difficulty: 4,
      tags: ['crafting', 'materials', 'creation']
    })

    // Collection Templates
    this.templates.set('rare_collection', {
      type: QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST,
      category: QUEST_CONFIG.CATEGORIES.COLLECTION,
      titleTemplate: 'Collect {collection_name}',
      descriptionTemplate: 'A collector is seeking rare {collection_type} items for their collection. Bring back the finest specimens.',
      objectives: [
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.COLLECT,
          target: '{collection_type}',
          required: 8,
          description: 'Collect 8 rare {collection_type} items'
        }
      ],
      rewards: {
        base: [
          { type: QUEST_CONFIG.REWARD_TYPES.GOLD, amount: 400 },
          { type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE, amount: 450 }
        ]
      },
      difficulty: 2,
      tags: ['collection', 'rare_items', 'gathering']
    })

    // Delivery Templates
    this.templates.set('urgent_delivery', {
      type: QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST,
      category: QUEST_CONFIG.CATEGORIES.DELIVERY,
      titleTemplate: 'Deliver {package_type} to {recipient}',
      descriptionTemplate: 'An urgent {package_type} must be delivered to {recipient} in {destination}. Time is of the essence!',
      objectives: [
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.DELIVER,
          target: '{package_type}',
          required: 1,
          description: 'Deliver the {package_type} to {recipient}'
        },
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.REACH_LOCATION,
          target: '{destination}',
          required: 1,
          description: 'Reach {destination} quickly'
        }
      ],
      rewards: {
        base: [
          { type: QUEST_CONFIG.REWARD_TYPES.GOLD, amount: 120 },
          { type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE, amount: 250 }
        ]
      },
      difficulty: 2,
      tags: ['delivery', 'urgent', 'travel']
    })

    // Boss Battle Templates
    this.templates.set('dragon_slayer', {
      type: QUEST_CONFIG.QUEST_TYPES.SIDE_QUEST,
      category: QUEST_CONFIG.CATEGORIES.BOSS_BATTLE,
      titleTemplate: 'Slay the {dragon_type} Dragon',
      descriptionTemplate: 'A fearsome {dragon_type} dragon has established its lair in {dragon_lair}. The realm needs heroes to confront this threat.',
      objectives: [
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.DEFEAT_BOSS,
          target: '{dragon_type}_dragon',
          required: 1,
          description: 'Defeat the {dragon_type} dragon'
        },
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.COLLECT,
          target: 'dragon_scale',
          required: 5,
          description: 'Collect 5 dragon scales as proof'
        }
      ],
      rewards: {
        base: [
          { type: QUEST_CONFIG.REWARD_TYPES.GOLD, amount: 1000 },
          { type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE, amount: 2000 },
          { type: QUEST_CONFIG.REWARD_TYPES.TITLE, amount: 1, name: 'Dragon Slayer' }
        ],
        choice: {
          enabled: true,
          options: [
            {
              name: 'Dragon\'s Hoard',
              description: 'Choose from the dragon\'s treasure collection',
              rewards: [
                { type: QUEST_CONFIG.REWARD_TYPES.EQUIPMENT, amount: 1, rarity: 'legendary' }
              ]
            },
            {
              name: 'Dragon\'s Power',
              description: 'Absorb some of the dragon\'s power',
              rewards: [
                { type: QUEST_CONFIG.REWARD_TYPES.ABILITY, amount: 2 }
              ]
            }
          ]
        }
      },
      difficulty: 6,
      tags: ['boss', 'dragon', 'legendary']
    })

    // Daily Quest Templates
    this.templates.set('daily_patrol', {
      type: QUEST_CONFIG.QUEST_TYPES.DAILY,
      category: QUEST_CONFIG.CATEGORIES.COMBAT,
      titleTemplate: 'Daily Patrol: {area_name}',
      descriptionTemplate: 'Patrol the {area_name} and deal with any threats to maintain safety in the region.',
      objectives: [
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.KILL,
          target: 'hostile_creature',
          required: 5,
          description: 'Defeat 5 hostile creatures'
        }
      ],
      rewards: {
        base: [
          { type: QUEST_CONFIG.REWARD_TYPES.GOLD, amount: 50 },
          { type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE, amount: 150 }
        ]
      },
      difficulty: 2,
      tags: ['daily', 'patrol', 'combat'],
      repeatable: true,
      cooldown: 22 * 60 * 60 // 22 hours
    })

    this.templates.set('daily_gathering', {
      type: QUEST_CONFIG.QUEST_TYPES.DAILY,
      category: QUEST_CONFIG.CATEGORIES.COLLECTION,
      titleTemplate: 'Daily Gathering: {resource_type}',
      descriptionTemplate: 'Gather {resource_type} for the local community. These resources are essential for daily life.',
      objectives: [
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.COLLECT,
          target: '{resource_type}',
          required: 10,
          description: 'Gather 10 {resource_type}'
        }
      ],
      rewards: {
        base: [
          { type: QUEST_CONFIG.REWARD_TYPES.GOLD, amount: 30 },
          { type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE, amount: 100 }
        ]
      },
      difficulty: 1,
      tags: ['daily', 'gathering', 'collection'],
      repeatable: true,
      cooldown: 22 * 60 * 60 // 22 hours
    })

    // Weekly Quest Templates
    this.templates.set('weekly_dungeon', {
      type: QUEST_CONFIG.QUEST_TYPES.WEEKLY,
      category: QUEST_CONFIG.CATEGORIES.DUNGEON,
      titleTemplate: 'Weekly Challenge: {dungeon_name}',
      descriptionTemplate: 'A new challenge awaits in {dungeon_name}. Test your skills against enhanced enemies and traps.',
      objectives: [
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.COMPLETE_DUNGEON,
          target: '{dungeon_name}',
          required: 1,
          description: 'Complete {dungeon_name} on challenging difficulty'
        }
      ],
      rewards: {
        base: [
          { type: QUEST_CONFIG.REWARD_TYPES.GOLD, amount: 500 },
          { type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE, amount: 1500 },
          { type: QUEST_CONFIG.REWARD_TYPES.EQUIPMENT, amount: 1, rarity: 'rare' }
        ]
      },
      difficulty: 4,
      tags: ['weekly', 'dungeon', 'challenge'],
      repeatable: true,
      cooldown: 7 * 24 * 60 * 60 // 7 days
    })

    // Guild Quest Templates
    this.templates.set('guild_campaign', {
      type: QUEST_CONFIG.QUEST_TYPES.GUILD,
      category: QUEST_CONFIG.CATEGORIES.COMBAT,
      titleTemplate: 'Guild Campaign: {campaign_name}',
      descriptionTemplate: 'The guild has launched a campaign against {enemy_faction}. All available members are needed for this important operation.',
      objectives: [
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.KILL,
          target: '{enemy_type}',
          required: 25,
          description: 'Guild members must defeat 25 {enemy_type} enemies'
        },
        {
          type: QUEST_CONFIG.OBJECTIVE_TYPES.DEFEAT_BOSS,
          target: '{enemy_leader}',
          required: 1,
          description: 'Defeat the {enemy_leader}'
        }
      ],
      rewards: {
        base: [
          { type: QUEST_CONFIG.REWARD_TYPES.GOLD, amount: 2000 },
          { type: QUEST_CONFIG.REWARD_TYPES.EXPERIENCE, amount: 3000 },
          { type: QUEST_CONFIG.REWARD_TYPES.REPUTATION, amount: 200, faction: 'Guild' }
        ]
      },
      difficulty: 5,
      tags: ['guild', 'campaign', 'group'],
      requiresParty: true,
      minPartySize: 3
    })
  }

  /**
   * Generate quest from template
   */
  async generateQuest(params) {
    const { player, context, type, category, difficulty, guildContext, partySize } = params

    // Select appropriate template
    const template = this.selectTemplate(type, category, difficulty, context)
    if (!template) {
      throw new Error(`No template found for type: ${type}, category: ${category}, difficulty: ${difficulty}`)
    }

    // Generate quest data from template
    const questData = this.fillTemplate(template, {
      player,
      context,
      difficulty,
      guildContext,
      partySize
    })

    // Apply difficulty scaling
    this.scaleQuestDifficulty(questData, difficulty, template.difficulty)

    // Apply personalization
    if (player) {
      this.personalizeQuest(questData, player, context)
    }

    // Generate rewards
    questData.rewards = await this.generateRewards(template, difficulty, player, partySize)

    // Generate story content
    questData.story = this.generateStoryContent(template, context)

    // Add branching if template supports it
    if (template.branching) {
      questData.branching = true
      questData.availablePaths = this.generateBranchingPaths(template, context)
    }

    // Set generation metadata
    questData.template = template.name || 'custom'
    questData.generatedBy = 'template'
    questData.source = 'template'
    questData.aiGenerated = false

    return questData
  }

  /**
   * Select appropriate template based on parameters
   */
  selectTemplate(type, category, difficulty, context) {
    // Get templates matching type and category
    const matchingTemplates = Array.from(this.templates.values()).filter(template => {
      return template.type === type && template.category === category
    })

    if (matchingTemplates.length === 0) {
      // Fallback to category only
      const categoryTemplates = Array.from(this.templates.values()).filter(template => {
        return template.category === category
      })
      if (categoryTemplates.length > 0) {
        return categoryTemplates[Math.floor(Math.random() * categoryTemplates.length)]
      }
      return null
    }

    // Filter by difficulty range
    const difficultyRange = 1
    const suitableTemplates = matchingTemplates.filter(template => {
      return Math.abs(template.difficulty - difficulty) <= difficultyRange
    })

    const templatesToUse = suitableTemplates.length > 0 ? suitableTemplates : matchingTemplates

    // Add some randomness but prefer templates closer to target difficulty
    const weights = templatesToUse.map(template => {
      const diffScore = Math.abs(template.difficulty - difficulty)
      return Math.max(0.1, 1 - (diffScore / 3))
    })

    // Select template based on weights
    const totalWeight = weights.reduce((sum, weight) => sum + weight, 0)
    let random = Math.random() * totalWeight
    let cumulative = 0

    for (let i = 0; i < templatesToUse.length; i++) {
      cumulative += weights[i]
      if (random <= cumulative) {
        return templatesToUse[i]
      }
    }

    return templatesToUse[0]
  }

  /**
   * Fill template with dynamic content
   */
  fillTemplate(template, params) {
    const { context, difficulty } = params
    const variables = this.generateVariables(template, context, difficulty)

    const questData = {
      type: template.type,
      category: template.category,
      difficulty: difficulty,
      levelRequirement: this.calculateLevelRequirement(difficulty, params.player),
      title: this.replaceVariables(template.titleTemplate, variables),
      description: this.replaceVariables(template.descriptionTemplate, variables),
      summary: this.generateSummary(template, variables),
      objectives: this.generateObjectives(template.objectives, variables),
      prerequisites: template.prerequisites || [],
      tags: template.tags || [],
      branching: template.branching || false,
      repeatable: template.repeatable || false,
      cooldown: template.cooldown || 0,
      requiresParty: template.requiresParty || false,
      minPartySize: template.minPartySize || 1,
      maxPartySize: template.maxPartySize || 6
    }

    return questData
  }

  /**
   * Generate variables for template substitution
   */
  generateVariables(template, context, difficulty) {
    const variables = {}

    // Monster types
    const monsterTypes = [
      'goblin', 'orc', 'troll', 'dragon', 'demon', 'undead', 'beast', 'elemental',
      'giant', 'construct', 'aberration', 'monstrosity', 'fey', 'celestial'
    ]
    variables.monster_type = monsterTypes[Math.floor(Math.random() * monsterTypes.length)]

    // Locations
    const locations = [
      'Darkwood Forest', 'Crystal Mountains', 'Shadow Swamp', 'Golden Plains',
      'Ancient Ruins', 'Frozen Wastes', 'Burning Desert', 'Mystic Valley'
    ]
    variables.location = locations[Math.floor(Math.random() * locations.length)]

    // Dungeon names
    const dungeonNames = [
      'Lost Crypt', 'Shadow Tower', 'Crystal Caverns', 'Abandoned Mine',
      'Sunken Temple', 'Haunted Mansion', 'Dragon\'s Lair', 'Forgotten Fortress'
    ]
    variables.dungeon_name = dungeonNames[Math.floor(Math.random() * dungeonNames.length)]

    // NPC names
    const npcNames = [
      'Eldrin the Wise', 'Lyra Swiftfoot', 'Thorin Ironforge', 'Aria Moonwhisper',
      'Gareth the Bold', 'Seraphina Brightstar', 'Marcus Steelheart', 'Iris Shadowmere'
    ]
    variables.npc_name = npcNames[Math.floor(Math.random() * npcNames.length)]

    // Factions
    const factions = [
      'Merchants Guild', 'Mages Council', 'Warriors Brotherhood', 'Rangers Union',
      'Thieves Syndicate', 'Temple of Light', 'Shadow Cabal', 'Nature\'s Guardians'
    ]
    variables.faction_name = factions[Math.floor(Math.random() * factions.length)]

    // Items and materials
    const itemTypes = [
      'ancient sword', 'mystic staff', 'enchanted armor', 'rare gem',
      'magical scroll', 'legendary shield', 'mystic amulet', 'ancient tome'
    ]
    variables.item_name = itemTypes[Math.floor(Math.random() * itemTypes.length)]

    // Resources
    const resources = [
      'iron ore', 'herbs', 'wood', 'crystals', 'leather', 'cloth',
      'rare metals', 'magical components', 'ancient artifacts'
    ]
    variables.resource_type = resources[Math.floor(Math.random() * resources.length)]

    // Add context-specific variables
    if (context && context.playerClass) {
      variables.player_class = context.playerClass
    }

    if (context && context.playerLevel) {
      variables.player_level = context.playerLevel
    }

    // Difficulty-based variables
    if (difficulty >= 5) {
      variables.ruin_type = 'ancient'
      variables.prophecy_type = 'doom'
      variables.dragon_type = 'ancient'
    } else if (difficulty >= 3) {
      variables.ruin_type = 'mysterious'
      variables.prophecy_type = 'mystical'
      variables.dragon_type = 'fierce'
    } else {
      variables.ruin_type = 'old'
      variables.prophecy_type = 'local'
      variables.dragon_type = 'young'
    }

    return variables
  }

  /**
   * Replace variables in template strings
   */
  replaceVariables(template, variables) {
    let result = template

    Object.entries(variables).forEach(([key, value]) => {
      const pattern = new RegExp(`\\{${key}\\}`, 'g')
      result = result.replace(pattern, value)
    })

    return result
  }

  /**
   * Generate quest summary
   */
  generateSummary(template, variables) {
    const summaries = [
      `A challenging ${template.category} adventure with moderate rewards.`,
      `An exciting quest perfect for ${template.difficulty >= 4 ? 'experienced' : 'new'} adventurers.`,
      `A memorable journey that will test your skills and courage.`,
      `An opportunity to prove your worth and earn valuable rewards.`
    ]

    return summaries[Math.floor(Math.random() * summaries.length)]
  }

  /**
   * Generate objectives from template
   */
  generateObjectives(templateObjectives, variables) {
    return templateObjectives.map(objTemplate => ({
      id: uuidv4(),
      title: this.replaceVariables(objTemplate.description, variables),
      description: this.replaceVariables(objTemplate.description, variables),
      type: objTemplate.type,
      target: this.replaceVariables(objTemplate.target.toString(), variables),
      current: 0,
      required: objTemplate.required,
      completed: false,
      optional: objTemplate.optional || false,
      hidden: objTemplate.hidden || false,
      rewards: objTemplate.rewards || [],
      choices: objTemplate.choices || [],
      branches: objTemplate.branches || []
    }))
  }

  /**
   * Calculate level requirement based on difficulty
   */
  calculateLevelRequirement(difficulty, player) {
    const baseLevel = Math.max(1, (difficulty - 1) * 10)

    if (player) {
      // Adjust based on player level
      const playerLevel = player.stats.level
      const diff = Math.abs(playerLevel - baseLevel)

      if (diff > 5) {
        // If player level is very different, adjust requirement
        return Math.max(1, playerLevel - (difficulty > player.stats.level ? 5 : 2))
      }
    }

    return baseLevel
  }

  /**
   * Scale quest difficulty
   */
  scaleQuestDifficulty(questData, targetDifficulty, templateDifficulty) {
    const scaleFactor = targetDifficulty / templateDifficulty

    // Scale objective requirements
    questData.objectives.forEach(obj => {
      if (typeof obj.required === 'number' && obj.type !== QUEST_CONFIG.OBJECTIVE_TYPES.KILL) {
        obj.required = Math.max(1, Math.round(obj.required * scaleFactor))
      }
    })

    // Add additional objectives for higher difficulty
    if (scaleFactor > 1.2 && questData.objectives.length < 5) {
      const additionalObjective = {
        id: uuidv4(),
        title: 'Overcome additional challenges',
        description: 'Face extra obstacles due to increased difficulty',
        type: QUEST_CONFIG.OBJECTIVE_TYPES.KILL,
        target: 'elite_enemy',
        current: 0,
        required: Math.ceil(scaleFactor),
        completed: false,
        optional: false,
        hidden: false
      }
      questData.objectives.push(additionalObjective)
    }
  }

  /**
   * Personalize quest for player
   */
  personalizeQuest(questData, player, context) {
    // Add player-specific references
    if (player.character.class) {
      const classReferences = {
        warrior: 'strength and combat prowess',
        mage: 'magical abilities and arcane knowledge',
        rogue: 'stealth and cunning',
        cleric: 'divine powers and healing abilities',
        ranger: 'tracking skills and wilderness knowledge',
        paladin: 'holy strength and unwavering devotion',
        warlock: 'dark powers and forbidden knowledge',
        bard: 'charismatic influence and artistic talents',
        monk: 'inner discipline and martial mastery',
        druid: 'connection to nature and shapeshifting abilities'
      }

      const classRef = classReferences[player.character.class] || 'unique abilities'
      questData.description += ` Your ${classRef} will be particularly valuable for this task.`
    }

    // Add personalization flags
    questData.personalized = true

    // Adjust based on player preferences
    if (player.questPreferences) {
      const prefs = player.questPreferences.types
      const maxPref = Math.max(...Object.values(prefs))

      if (maxPref > 0.7) {
        const topPref = Object.entries(prefs).find(([, value]) => value === maxPref)[0]
        questData.tags.push(`personalized_${topPref}`)
      }
    }
  }

  /**
   * Generate rewards for quest
   */
  async generateRewards(template, difficulty, player, partySize) {
    const rewards = { base: [], bonus: [], choice: { enabled: false, options: [] } }

    // Generate base rewards from template
    if (template.rewards && template.rewards.base) {
      rewards.base = this.scaleRewards(template.rewards.base, difficulty, partySize)
    }

    // Generate bonus rewards for higher difficulty
    if (difficulty >= 4 && template.rewards && template.rewards.bonus) {
      rewards.bonus = this.scaleRewards(template.rewards.bonus, difficulty, partySize)
    }

    // Generate choice rewards if template supports it
    if (template.rewards && template.rewards.choice && template.rewards.choice.enabled) {
      rewards.choice = {
        enabled: true,
        options: template.rewards.choice.options.map(option => ({
          ...option,
          rewards: this.scaleRewards(option.rewards, difficulty, partySize)
        }))
      }
    }

    // Add difficulty bonus rewards
    if (difficulty >= 5) {
      rewards.bonus.push({
        type: QUEST_CONFIG.REWARD_TYPES.TITLE,
        amount: 1,
        name: this.generateTitle(difficulty)
      })
    }

    return rewards
  }

  /**
   * Scale rewards based on difficulty and party size
   */
  scaleRewards(baseRewards, difficulty, partySize = 1) {
    return baseRewards.map(reward => {
      const scaledReward = { ...reward }

      // Scale amount based on difficulty
      const difficultyMultiplier = 0.5 + (difficulty * 0.3)

      // Scale amount based on party size
      const partyMultiplier = Math.max(0.5, 1 / partySize)

      if (typeof reward.amount === 'number') {
        scaledReward.amount = Math.round(reward.amount * difficultyMultiplier * partyMultiplier)
      }

      return scaledReward
    })
  }

  /**
   * Generate title based on difficulty
   */
  generateTitle(difficulty) {
    const titles = {
      5: ['Veteran Adventurer', 'Seasoned Explorer', 'Expert Hero'],
      6: ['Master Quester', 'Legendary Hero', 'Champion of the Realm'],
      7: ['Mythic Champion', 'Godslayer', 'World Defender']
    }

    const titleList = titles[difficulty] || titles[5]
    return titleList[Math.floor(Math.random() * titleList.length)]
  }

  /**
   * Generate story content for quest
   */
  generateStoryContent(template, context) {
    const story = {
      introduction: this.generateIntroduction(template, context),
      background: this.generateBackground(template, context),
      climax: this.generateClimax(template, context),
      resolution: this.generateResolution(template, context),
      epilogue: this.generateEpilogue(template, context)
    }

    return story
  }

  /**
   * Generate story introduction
   */
  generateIntroduction(template, context) {
    const introductions = {
      combat: 'The call to adventure echoes through the land. Brave warriors are needed to face the growing threats.',
      exploration: 'Uncharted territories await discovery. Ancient secrets lie hidden in the wilderness.',
      social: 'The fate of many hangs in the balance. Diplomatic solutions must be found.',
      mystery: 'Strange occurrences trouble the peaceful realm. An investigator is needed to uncover the truth.',
      crafting: 'Great works require rare materials and skilled craftsmanship. A master craftsman is sought.',
      collection: 'Valuable items scattered across the land call to dedicated collectors.',
      escort: 'Important journeys require skilled protection. Lives depend on safe passage.',
      delivery: 'Urgent messages must reach their destination. Time is of the essence.',
      boss_battle: 'A great evil threatens the realm. Only the mightiest heroes can stand against it.',
      dungeon: 'Ancient dungeons hold both danger and treasure. Brave adventurers are needed to explore their depths.'
    }

    return introductions[template.category] || 'Adventure calls to those brave enough to answer.'
  }

  /**
   * Generate story background
   */
  generateBackground(template, context) {
    return 'The circumstances that led to this current situation are complex and multifaceted, involving the actions of many individuals and the passage of time.'
  }

  /**
   * Generate story climax
   */
  generateClimax(template, context) {
    return 'The moment of truth arrives. All preparations lead to this critical juncture where courage and skill will be tested.'
  }

  /**
   * Generate story resolution
   */
  generateResolution(template, context) {
    return 'With the challenges overcome, a new chapter begins. The immediate threats have been dealt with, but adventures continue.'
  }

  /**
   * Generate story epilogue
   */
  generateEpilogue(template, context) {
    return 'The tales of this adventure will be told for generations, inspiring future heroes to follow in these footsteps.'
  }

  /**
   * Generate branching paths for quests
   */
  generateBranchingPaths(template, context) {
    if (!template.branching) return []

    const paths = [
      {
        id: 'peaceful_resolution',
        name: 'Peaceful Resolution',
        description: 'Resolve conflicts through diplomacy and understanding',
        requirements: ['high_charisma', 'peaceful_approach']
      },
      {
        id: 'direct_confrontation',
        name: 'Direct Confrontation',
        description: 'Face challenges head-on with strength and courage',
        requirements: ['high_strength', 'combat_focus']
      },
      {
        id: 'cunning_solution',
        name: 'Cunning Solution',
        description: 'Use wit and stealth to overcome obstacles',
        requirements: ['high_dexterity', 'stealth_approach']
      }
    ]

    return paths
  }

  /**
   * Get available templates
   */
  getAvailableTemplates() {
    return Array.from(this.templates.entries()).map(([key, template]) => ({
      key,
      type: template.type,
      category: template.category,
      difficulty: template.difficulty,
      tags: template.tags || []
    }))
  }

  /**
   * Get template by key
   */
  getTemplate(key) {
    return this.templates.get(key)
  }

  /**
   * Add custom template
   */
  addTemplate(key, template) {
    this.templates.set(key, template)
  }

  /**
   * Remove template
   */
  removeTemplate(key) {
    return this.templates.delete(key)
  }
}

export default QuestTemplateEngine