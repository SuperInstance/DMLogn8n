/**
 * Data Seeder for Test Environment
 *
 * Generates realistic test data for all DMlogn8n systems including:
 * - Users and characters
 * - Guilds and alliances
 * - Quests and templates
 * - Crafting recipes and materials
 * - Arena matches and rankings
 * - AI conversations and emotions
 */

const faker = require('@faker-js/faker').faker
const { chance } = require('chance')
const bcrypt = require('bcryptjs')
const { ObjectId } = require('mongodb')
const { config } = require('../../config/test-config')
const logger = require('../utils/logger')

class DataSeeder {
  constructor(databases) {
    this.databases = databases
    this.rng = new chance()

    // Predefined data arrays for realistic generation
    this.dndData = {
      races: config.testData.characters.races,
      classes: config.testData.characters.classes,
      backgrounds: config.testData.characters.backgrounds,
      alignments: config.testData.characters.alignments,

      skills: [
        'acrobatics', 'animal-handling', 'arcana', 'athletics', 'deception',
        'history', 'insight', 'intimidation', 'investigation', 'medicine',
        'nature', 'perception', 'performance', 'persuasion', 'religion',
        'sleight-of-hand', 'stealth', 'survival'
      ],

      abilities: ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'],

      equipment: [
        'longsword', 'shortsword', 'greatsword', 'dagger', 'bow', 'crossbow',
        'leather-armor', 'chain-mail', 'plate-armor', 'shield', 'helmet',
        'healing-potion', 'mana-potion', 'poison', 'antidote', 'rations',
        'torch', 'rope', 'grappling-hook', 'lockpicks', 'spellbook'
      ],

      spells: [
        'fireball', 'lightning-bolt', 'magic-missile', 'cure-wounds', 'heal',
        'shield', 'mage-armor', 'invisibility', 'fly', 'teleport',
        'detect-magic', 'dispel-magic', 'counterspell', 'identify', 'scry'
      ],

      locations: [
        'Stormwind City', 'Orgrimmar', 'Ironforge', 'Darnassus', 'Undercity',
        'Thunder Bluff', 'Silvermoon City', 'Exodar', 'Shattrath', 'Dalaran',
        'Blackrock Mountain', 'Molten Core', 'Naxxramas', 'Icecrown Citadel'
      ],

      factions: [
        'Alliance', 'Horde', 'Kirin Tor', 'Silver Hand', 'Cenarion Circle',
        'Argent Dawn', 'Brotherhood of Light', 'Shattered Sun Offensive'
      ]
    }
  }

  /**
   * Generate random ability scores
   */
  generateAbilityScores(method = 'standard') {
    switch (method) {
      case 'standard':
        // 4d6 drop lowest
        return this.dndData.abilities.reduce((scores, ability) => {
          const rolls = Array.from({ length: 4 }, () => this.rng.d6())
          rolls.sort((a, b) => b - a)
          scores[ability] = rolls.slice(0, 3).reduce((sum, roll) => sum + roll, 0)
          return scores
        }, {})

      case 'point-buy':
        // 27 point buy system
        const scores = {}
        let points = 27
        const costs = { 8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9 }

        for (const ability of this.dndData.abilities) {
          const availableScores = Object.entries(costs)
            .filter(([_, cost]) => cost <= points)
            .map(([score, _]) => parseInt(score))

          if (availableScores.length === 0) {
            scores[ability] = 8
          } else {
            scores[ability] = this.rng.pickone(availableScores)
            points -= costs[scores[ability]]
          }
        }
        return scores

      default:
        return this.dndData.abilities.reduce((scores, ability) => {
          scores[ability] = this.rng.integer({ min: 8, max: 18 })
          return scores
        }, {})
    }
  }

  /**
   * Generate skills based on abilities and class
   */
  generateSkills(abilities, characterClass) {
    const skills = {}

    for (const skill of this.dndData.skills) {
      let baseAbility = this.getSkillAbility(skill)
      let modifier = Math.floor((abilities[baseAbility] - 10) / 2)

      // Class skill bonus
      if (this.isClassSkill(skill, characterClass)) {
        modifier += this.rng.integer({ min: 2, max: 5 })
      }

      // Random proficiency
      if (this.rng.bool({ likelihood: 30 })) {
        modifier += this.rng.integer({ min: 1, max: 3 })
      }

      skills[skill] = modifier
    }

    return skills
  }

  /**
   * Get the primary ability for a skill
   */
  getSkillAbility(skill) {
    const skillAbilities = {
      'acrobatics': 'dexterity',
      'animal-handling': 'wisdom',
      'arcana': 'intelligence',
      'athletics': 'strength',
      'deception': 'charisma',
      'history': 'intelligence',
      'insight': 'wisdom',
      'intimidation': 'charisma',
      'investigation': 'intelligence',
      'medicine': 'wisdom',
      'nature': 'intelligence',
      'perception': 'wisdom',
      'performance': 'charisma',
      'persuasion': 'charisma',
      'religion': 'intelligence',
      'sleight-of-hand': 'dexterity',
      'stealth': 'dexterity',
      'survival': 'wisdom'
    }

    return skillAbilities[skill] || 'intelligence'
  }

  /**
   * Check if a skill is a class skill
   */
  isClassSkill(skill, characterClass) {
    const classSkills = {
      'fighter': ['athletics', 'intimidation', 'survival'],
      'wizard': ['arcana', 'history', 'investigation', 'religion'],
      'cleric': ['medicine', 'insight', 'religion'],
      'rogue': ['acrobatics', 'deception', 'insight', 'intimidation', 'investigation', 'perception', 'performance', 'persuasion', 'sleight-of-hand', 'stealth'],
      'ranger': ['animal-handling', 'athletics', 'insight', 'investigation', 'nature', 'perception', 'stealth', 'survival'],
      'paladin': ['athletics', 'insight', 'intimidation', 'medicine', 'persuasion', 'religion']
    }

    return classSkills[characterClass]?.includes(skill) || false
  }

  /**
   * Seed users
   */
  async seedUsers(count = 10) {
    logger.debug(`Seeding ${count} users...`)
    const users = []

    for (let i = 0; i < count; i++) {
      const user = {
        _id: new ObjectId(),
        username: faker.internet.userName(),
        email: faker.internet.email(),
        password: await bcrypt.hash('password123', 10),
        profile: {
          firstName: faker.person.firstName(),
          lastName: faker.person.lastName(),
          avatar: faker.internet.avatar(),
          bio: faker.lorem.paragraph(),
          timezone: faker.location.timeZone(),
          language: faker.helpers.arrayElement(['en', 'es', 'fr', 'de', 'ja']),
          country: faker.location.countryCode(),
          birthDate: faker.date.birthdate({ min: 13, max: 70 })
        },
        preferences: {
          theme: this.rng.pickone(['light', 'dark', 'auto']),
          notifications: {
            email: this.rng.bool(),
            push: this.rng.bool(),
            inGame: this.rng.bool()
          },
          privacy: {
            profilePublic: this.rng.bool(),
            showOnlineStatus: this.rng.bool(),
            allowFriendRequests: this.rng.bool()
          },
          gameplay: {
            autoSave: true,
            showDiceRolls: true,
            combatAnimations: this.rng.bool(),
            soundEffects: this.rng.bool()
          }
        },
        stats: {
          totalPlayTime: this.rng.integer({ min: 0, max: 10000 }),
          sessionsPlayed: this.rng.integer({ min: 0, max: 500 }),
          charactersCreated: this.rng.integer({ min: 1, max: 20 }),
          achievements: this.rng.integer({ min: 0, max: 100 }),
          lastLogin: faker.date.recent(),
          joinDate: faker.date.past()
        },
        roles: this.rng.pickone(['player', 'dm', 'admin']),
        status: this.rng.pickone(['active', 'inactive', 'suspended', 'banned']),
        createdAt: faker.date.past(),
        updatedAt: faker.date.recent()
      }

      users.push(user)
    }

    // Insert into database
    if (this.databases.mongodb) {
      await this.databases.mongodb.collection('users').insertMany(users)
    }

    logger.info(`Seeded ${users.length} users`)
    return users
  }

  /**
   * Seed characters
   */
  async seedCharacters(count = 20) {
    logger.debug(`Seeding ${count} characters...`)
    const characters = []

    // Get user IDs for association
    let userIds = []
    if (this.databases.mongodb) {
      const users = await this.databases.mongodb.collection('users').find({}, { _id: 1 }).toArray()
      userIds = users.map(u => u._id)
    }

    if (userIds.length === 0) {
      // Create fake user IDs if no users exist
      userIds = Array.from({ length: 10 }, () => new ObjectId())
    }

    for (let i = 0; i < count; i++) {
      const race = this.rng.pickone(this.dndData.races)
      const characterClass = this.rng.pickone(this.dndData.classes)
      const background = this.rng.pickone(this.dndData.backgrounds)
      const alignment = this.rng.pickone(this.dndData.alignments)
      const level = this.rng.pickone(config.testData.characters.levels)

      const abilities = this.generateAbilityScores()
      const skills = this.generateSkills(abilities, characterClass)

      const character = {
        _id: new ObjectId(),
        userId: this.rng.pickone(userIds),
        name: `${faker.person.firstName()} ${faker.person.lastName()}`,
        nickname: faker.word.adjective(),
        race,
        class: characterClass,
        background,
        alignment,
        level,
        experience: this.calculateExperience(level),

        abilities,
        skills,

        combat: {
          hitPoints: this.calculateHitPoints(characterClass, level, abilities.constitution),
          maxHitPoints: this.calculateHitPoints(characterClass, level, abilities.constitution),
          temporaryHitPoints: this.rng.integer({ min: 0, max: 20 }),
          armorClass: 10 + Math.floor((abilities.dexterity - 10) / 2) + this.rng.integer({ min: 0, max: 6 }),
          initiative: Math.floor((abilities.dexterity - 10) / 2),
          speed: this.rng.pickone([25, 30, 35, 40]),
          deathSaves: {
            successes: this.rng.integer({ min: 0, max: 3 }),
            failures: this.rng.integer({ min: 0, max: 3 })
          }
        },

        equipment: this.rng.pickset(this.dndData.equipment, this.rng.integer({ min: 3, max: 10 })),
        gold: this.rng.integer({ min: 0, max: 10000 }),

        spells: characterClass === 'wizard' ? this.rng.pickset(this.dndData.spells, this.rng.integer({ min: 1, max: 8 })) : [],

        appearance: {
          height: `${this.rng.integer({ min: 48, max: 84 })} inches`,
          weight: `${this.rng.integer({ min: 80, max: 300 })} lbs`,
          eyeColor: faker.color.human(),
          hairColor: faker.color.human(),
          skinTone: faker.color.human(),
          distinguishingFeatures: faker.lorem.sentence(),
          portrait: faker.image.url()
        },

        personality: {
          traits: [faker.word.adjective(), faker.word.adjective()],
          ideals: [faker.word.noun(), faker.word.noun()],
          bonds: [faker.lorem.sentence()],
          flaws: [faker.lorem.sentence()]
        },

        backstory: faker.lorem.paragraphs(3),

        stats: {
          sessionsPlayed: this.rng.integer({ min: 0, max: 100 }),
          totalPlayTime: this.rng.integer({ min: 0, max: 5000 }),
          monstersDefeated: this.rng.integer({ min: 0, max: 1000 }),
          damageDealt: this.rng.integer({ min: 0, max: 50000 }),
          damageTaken: this.rng.integer({ min: 0, max: 30000 }),
          healingDone: this.rng.integer({ min: 0, max: 20000 }),
          goldEarned: this.rng.integer({ min: 0, max: 50000 }),
          itemsLooted: this.rng.integer({ min: 0, max: 500 }),
          questsCompleted: this.rng.integer({ min: 0, max: 100 }),
          deaths: this.rng.integer({ min: 0, max: 10 })
        },

        status: this.rng.pickone(['active', 'inactive', 'dead', 'retired']),
        createdAt: faker.date.past(),
        updatedAt: faker.date.recent()
      }

      characters.push(character)
    }

    // Insert into database
    if (this.databases.mongodb) {
      await this.databases.mongodb.collection('characters').insertMany(characters)
    }

    logger.info(`Seeded ${characters.length} characters`)
    return characters
  }

  /**
   * Calculate experience needed for level
   */
  calculateExperience(level) {
    // D&D 5e experience table
    const expTable = {
      1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500, 6: 14000, 7: 23000,
      8: 34000, 9: 48000, 10: 64000, 11: 85000, 12: 100000,
      13: 120000, 14: 140000, 15: 165000, 16: 195000, 17: 225000,
      18: 265000, 19: 305000, 20: 355000
    }

    return expTable[level] || 0
  }

  /**
   * Calculate hit points
   */
  calculateHitPoints(characterClass, level, constitution) {
    const hitDice = {
      'fighter': 10,
      'wizard': 6,
      'cleric': 8,
      'rogue': 8,
      'ranger': 10,
      'paladin': 10
    }

    const conMod = Math.floor((constitution - 10) / 2)
    const hitDie = hitDice[characterClass] || 8

    // First level: maximum hit die + con modifier
    // Additional levels: average roll + con modifier
    return hitDie + conMod + ((level - 1) * (Math.floor(hitDie / 2) + 1 + conMod))
  }

  /**
   * Seed guilds
   */
  async seedGuilds(count = 5) {
    logger.debug(`Seeding ${count} guilds...`)
    const guilds = []

    // Get character IDs for members
    let characterIds = []
    if (this.databases.mongodb) {
      const characters = await this.databases.mongodb.collection('characters').find({}, { _id: 1 }).toArray()
      characterIds = characters.map(c => c._id)
    }

    if (characterIds.length === 0) {
      characterIds = Array.from({ length: 50 }, () => new ObjectId())
    }

    for (let i = 0; i < count; i++) {
      const guildType = this.rng.pickone(config.testData.guilds.types)
      const size = config.testData.guilds.sizes[this.rng.pickone(['small', 'medium', 'large'])]
      const memberCount = this.rng.integer({ min: size.min, max: Math.min(size.max, characterIds.length) })

      const guild = {
        _id: new ObjectId(),
        name: `${faker.word.adjective()} ${this.rng.pickone(['Brotherhood', 'Sisterhood', 'Company', 'Guild', 'Order', 'Alliance'])}`,
        tag: faker.string.alphanumeric({ length: 5 }).toUpperCase(),
        description: faker.lorem.paragraphs(2),
        type: guildType,

        leadership: {
          guildMaster: this.rng.pickone(characterIds),
          officers: this.rng.pickset(characterIds, this.rng.integer({ min: 1, max: 5 }))
        },

        members: this.rng.pickset(characterIds, memberCount).map(characterId => ({
          characterId,
          rank: this.rng.pickone(['member', 'veteran', 'officer', 'guild-master']),
          joinDate: faker.date.past(),
          contribution: this.rng.integer({ min: 0, max: 10000 })
        })),

        hall: {
          name: `${this.rng.pickone(['Grand', 'Mystical', 'Ancient', 'Sacred'])} ${this.rng.pickone(['Hall', 'Keep', 'Tower', 'Citadel'])}`,
          location: this.rng.pickone(this.dndData.locations),
          level: this.rng.integer({ min: 1, max: 10 }),
          rooms: this.rng.pickset([
            'throne-room', 'barracks', 'armory', 'library', 'kitchen',
            'training-ground', 'treasury', 'portal-room', 'meeting-hall'
          ], this.rng.integer({ min: 3, max: 7 })),
          decorations: this.rng.integer({ min: 0, max: 100 })
        },

        bank: {
          gold: this.rng.integer({ min: 1000, max: 100000 }),
          items: this.generateLoot(this.rng.integer({ min: 5, max: 50 })),
          accessLevel: this.rng.pickone(['all', 'officers', 'guild-master'])
        },

        stats: {
          totalMembers: memberCount,
          activeMembers: this.rng.integer({ min: Math.floor(memberCount * 0.3), max: memberCount }),
          totalGold: this.rng.integer({ min: 5000, max: 500000 }),
          totalItems: this.rng.integer({ min: 50, max: 1000 }),
          questsCompleted: this.rng.integer({ min: 0, max: 500 }),
          warsWon: this.rng.integer({ min: 0, max: 50 }),
          foundingDate: faker.date.past({ years: 5 })
        },

        settings: {
          recruitmentOpen: this.rng.bool(),
          recruitmentLevel: this.rng.integer({ min: 1, max: 20 }),
          memberApproval: this.rng.bool(),
          allianceRequests: this.rng.bool(),
          description: faker.lorem.paragraph(),
          recruitmentText: faker.lorem.paragraph()
        },

        status: this.rng.pickone(['active', 'inactive', 'disbanded']),
        createdAt: faker.date.past(),
        updatedAt: faker.date.recent()
      }

      guilds.push(guild)
    }

    // Insert into database
    if (this.databases.mongodb) {
      await this.databases.mongodb.collection('guilds').insertMany(guilds)
    }

    logger.info(`Seeded ${guilds.length} guilds`)
    return guilds
  }

  /**
   * Generate loot items
   */
  generateLoot(count) {
    const loot = []
    const rarities = ['common', 'uncommon', 'rare', 'epic', 'legendary']
    const itemTypes = ['weapon', 'armor', 'accessory', 'consumable', 'material', 'recipe']

    for (let i = 0; i < count; i++) {
      loot.push({
        id: new ObjectId().toString(),
        name: `${this.rng.pickone(['Flaming', 'Frost', 'Shadow', 'Divine', 'Arcane'])} ${this.rng.pickone(this.dndData.equipment)}`,
        type: this.rng.pickone(itemTypes),
        rarity: this.rng.weighted(['common', 'uncommon', 'rare', 'epic', 'legendary'], [50, 30, 15, 4, 1]),
        level: this.rng.integer({ min: 1, max: 20 }),
        stats: this.generateItemStats(),
        quantity: this.rng.integer({ min: 1, max: 10 }),
        value: this.rng.integer({ min: 10, max: 10000 })
      })
    }

    return loot
  }

  /**
   * Generate item stats
   */
  generateItemStats() {
    const stats = {}
    const statCount = this.rng.integer({ min: 1, max: 4 })

    for (let i = 0; i < statCount; i++) {
      const stat = this.rng.pickone(['attack-power', 'defense', 'magic-power', 'health', 'mana', 'crit-chance', 'haste'])
      stats[stat] = this.rng.integer({ min: 1, max: 50 })
    }

    return stats
  }

  /**
   * Seed quests
   */
  async seedQuests(count = 15) {
    logger.debug(`Seeding ${count} quests...`)
    const quests = []

    for (let i = 0; i < count; i++) {
      const questType = this.rng.pickone(config.testData.quests.types)
      const difficulty = this.rng.pickone(config.testData.quests.difficulties)

      const quest = {
        _id: new ObjectId(),
        title: `${this.rng.pickone(['The', 'A', 'An'])} ${this.rng.pickone(['Lost', 'Ancient', 'Cursed', 'Blessed', 'Hidden'])} ${this.rng.pickone(['Sword', 'Crown', 'Tome', 'Artifact', 'Relic'])}`,
        description: faker.lorem.paragraphs(3),
        type: questType,
        difficulty,
        recommendedLevel: this.rng.integer({ min: 1, max: 20 }),

        objectives: this.generateQuestObjectives(questType),

        rewards: {
          gold: this.rng.integer(config.testData.quests.rewards.gold),
          experience: this.rng.integer(config.testData.quests.rewards.xp),
          items: this.generateLoot(this.rng.integer(config.testData.quests.rewards.items)),
          reputation: {
            faction: this.rng.pickone(this.dndData.factions),
            amount: this.rng.integer({ min: 50, max: 1000 })
          }
        },

        location: {
          zone: this.rng.pickone(this.dndData.locations),
          coordinates: {
            x: this.rng.integer({ min: -1000, max: 1000 }),
            y: this.rng.integer({ min: -1000, max: 1000 })
          }
        },

        requirements: {
          level: this.rng.integer({ min: 1, max: 20 }),
          classes: this.rng.pickset(this.dndData.classes, this.rng.integer({ min: 0, max: 3 })),
          races: this.rng.pickset(this.dndData.races, this.rng.integer({ min: 0, max: 3 })),
          prerequisites: this.rng.pickset([`quest_${this.rng.integer({ min: 1, max: 100 })}`], this.rng.integer({ min: 0, max: 2 }))
        },

        timeline: {
          estimatedTime: this.rng.integer({ min: 15, max: 180 }), // minutes
          timeLimit: this.rng.integer({ min: 0, max: 7 * 24 }), // hours, 0 = no limit
          repeatable: this.rng.bool(),
          cooldown: this.rng.integer({ min: 0, max: 7 * 24 }) // hours
        },

        status: this.rng.pickone(['available', 'in-progress', 'completed', 'failed', 'cancelled']),
        createdBy: this.rng.pickone(['system', 'dm_1', 'guild_quest']),
        createdAt: faker.date.past(),
        updatedAt: faker.date.recent()
      }

      quests.push(quest)
    }

    // Insert into database
    if (this.databases.mongodb) {
      await this.databases.mongodb.collection('quests').insertMany(quests)
    }

    logger.info(`Seeded ${quests.length} quests`)
    return quests
  }

  /**
   * Generate quest objectives based on type
   */
  generateQuestObjectives(type) {
    const objectives = []
    const count = this.rng.integer({ min: 1, max: 4 })

    for (let i = 0; i < count; i++) {
      let objective = {}

      switch (type) {
        case 'kill':
          objective = {
            type: 'kill',
            target: `${this.rng.pickone(['Goblin', 'Orc', 'Dragon', 'Demon', 'Undead'])} ${this.rng.pickone(['Warrior', 'Shaman', 'Lord', 'King'])}`,
            current: 0,
            required: this.rng.integer({ min: 1, max: 20 })
          }
          break

        case 'fetch':
          objective = {
            type: 'collect',
            item: `${this.rng.pickone(['Ancient', 'Cursed', 'Blessed', 'Magical'])} ${this.rng.pickone(['Sword', 'Shield', 'Ring', 'Amulet', 'Scroll'])}`,
            current: 0,
            required: this.rng.integer({ min: 1, max: 10 })
          }
          break

        case 'explore':
          objective = {
            type: 'explore',
            location: `${this.rng.pickone(['Dark', 'Sunken', 'Ancient', 'Hidden'])} ${this.rng.pickone(['Cave', 'Temple', 'Dungeon', 'Ruins'])}`,
            discovered: false
          }
          break

        case 'escort':
          objective = {
            type: 'escort',
            npc: `${faker.person.firstName()} ${this.rng.pickone(['the Merchant', 'the Scholar', 'the Noble', 'the Priest'])}`,
            current: 0,
            required: 1,
            safe: false
          }
          break

        default:
          objective = {
            type: 'misc',
            description: faker.lorem.sentence(),
            completed: false
          }
      }

      objectives.push(objective)
    }

    return objectives
  }

  /**
   * Seed all data types
   */
  async seedAll() {
    logger.info('Starting complete database seeding...')

    try {
      // Clear existing data
      await this.clearAllData()

      // Seed in order of dependencies
      const users = await this.seedUsers(50)
      const characters = await this.seedCharacters(100)
      const guilds = await this.seedGuilds(10)
      const quests = await this.seedQuests(30)

      logger.info('Complete database seeding finished')

      return {
        users: users.length,
        characters: characters.length,
        guilds: guilds.length,
        quests: quests.length
      }
    } catch (error) {
      logger.error('Database seeding failed:', error)
      throw error
    }
  }

  /**
   * Clear all data
   */
  async clearAllData() {
    logger.debug('Clearing all test data...')

    if (this.databases.mongodb) {
      const db = this.databases.mongodb.db
      const collections = await db.collections()

      for (const collection of collections) {
        await collection.deleteMany({})
      }
    }

    if (this.databases.postgresql) {
      const client = await this.databases.postgresql.connect()
      try {
        await client.query('TRUNCATE TABLE users, characters, guilds, quests, guild_members, quest_progress RESTART IDENTITY CASCADE')
      } finally {
        client.release()
      }
    }

    if (this.databases.redis) {
      await this.databases.redis.flushdb()
    }

    logger.info('All test data cleared')
  }
}

module.exports = DataSeeder