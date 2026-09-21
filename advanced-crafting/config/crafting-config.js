/**
 * Advanced Crafting System Configuration
 * Central configuration for all crafting modules and settings
 */

const CraftingConfig = {
    // System Settings
    system: {
        maxSkillLevel: 1000,
        baseExperienceMultiplier: 1.0,
        qualityDecayEnabled: true,
        socialFeaturesEnabled: true,
        marketplaceEnabled: true,
        competitionsEnabled: true,
        guildWorkshopsEnabled: true,
        apprenticeshipSystemEnabled: true
    },

    // Crafting Tiers Configuration
    tiers: {
        SIMPLE: {
            name: 'Simple Crafting',
            requiredSkill: 0,
            maxSkill: 99,
            successBonus: 0.2,
            qualityMultiplier: 1.0,
            experienceMultiplier: 1.0,
            timeMultiplier: 1.0,
            materialCostMultiplier: 1.0,
            criticalSuccessChance: 0.05,
            criticalFailureChance: 0.02,
            description: 'Basic items with common materials and simple techniques'
        },
        ADVANCED: {
            name: 'Advanced Crafting',
            requiredSkill: 100,
            maxSkill: 299,
            successBonus: 0.0,
            qualityMultiplier: 1.25,
            experienceMultiplier: 1.5,
            timeMultiplier: 1.5,
            materialCostMultiplier: 1.5,
            criticalSuccessChance: 0.08,
            criticalFailureChance: 0.05,
            description: 'Complex items requiring rare materials and specialized skills'
        },
        MASTER: {
            name: 'Master Crafting',
            requiredSkill: 300,
            maxSkill: 499,
            successBonus: -0.1,
            qualityMultiplier: 1.5,
            experienceMultiplier: 2.0,
            timeMultiplier: 2.0,
            materialCostMultiplier: 2.0,
            criticalSuccessChance: 0.12,
            criticalFailureChance: 0.08,
            description: 'Legendary items created with master techniques and rare materials'
        },
        ARTIFACT: {
            name: 'Artifact Creation',
            requiredSkill: 500,
            maxSkill: 699,
            successBonus: -0.2,
            qualityMultiplier: 2.0,
            experienceMultiplier: 3.0,
            timeMultiplier: 4.0,
            materialCostMultiplier: 5.0,
            criticalSuccessChance: 0.15,
            criticalFailureChance: 0.15,
            description: 'Unique artifacts requiring quest completion and legendary components'
        },
        MAGICAL: {
            name: 'Magical Infusion',
            requiredSkill: 700,
            maxSkill: 1000,
            successBonus: -0.15,
            qualityMultiplier: 1.75,
            experienceMultiplier: 2.5,
            timeMultiplier: 3.0,
            materialCostMultiplier: 3.0,
            criticalSuccessChance: 0.10,
            criticalFailureChance: 0.20,
            description: 'Magical enchantment and imbuing with arcane energies'
        }
    },

    // Material Quality Tiers
    materialQuality: {
        COMMON: {
            name: 'Common',
            minQuality: 1,
            maxQuality: 40,
            color: '#808080',
            valueMultiplier: 1.0,
            abundance: 0.7,
            decayRate: 0.1
        },
        UNCOMMON: {
            name: 'Uncommon',
            minQuality: 41,
            maxQuality: 60,
            color: '#00ff00',
            valueMultiplier: 1.5,
            abundance: 0.2,
            decayRate: 0.08
        },
        RARE: {
            name: 'Rare',
            minQuality: 61,
            maxQuality: 75,
            color: '#0080ff',
            valueMultiplier: 2.5,
            abundance: 0.08,
            decayRate: 0.05
        },
        EPIC: {
            name: 'Epic',
            minQuality: 76,
            maxQuality: 90,
            color: '#8000ff',
            valueMultiplier: 4.0,
            abundance: 0.018,
            decayRate: 0.03
        },
        LEGENDARY: {
            name: 'Legendary',
            minQuality: 91,
            maxQuality: 100,
            color: '#ff8000',
            valueMultiplier: 8.0,
            abundance: 0.002,
            decayRate: 0.01
        }
    },

    // Profession Configuration
    professions: {
        BLACKSMITHING: {
            name: 'Blacksmithing',
            description: 'Craft weapons, armor, and tools from metal',
            primaryStats: ['strength', 'dexterity', 'intelligence'],
            secondaryStats: ['constitution', 'wisdom'],
            tools: ['hammer', 'tongs', 'anvil', 'forge', 'grindstone'],
            stations: ['forge', 'workbench', 'grindstone'],
            skillProgression: {
                novice: { min: 0, max: 50, bonus: 0.9 },
                apprentice: { min: 51, max: 150, bonus: 1.0 },
                journeyman: { min: 151, max: 300, bonus: 1.1 },
                expert: { min: 301, max: 500, bonus: 1.2 },
                master: { min: 501, max: 750, bonus: 1.3 },
                grandmaster: { min: 751, max: 1000, bonus: 1.5 }
            }
        },
        ALCHEMY: {
            name: 'Alchemy',
            description: 'Brew potions, elixirs, and magical substances',
            primaryStats: ['intelligence', 'wisdom', 'dexterity'],
            secondaryStats: ['constitution', 'charisma'],
            tools: ['mortar_pestle', 'alembic', 'retort', 'crucible', 'flask'],
            stations: ['alchemy_lab', 'brewing_stand', 'distillery'],
            skillProgression: {
                novice: { min: 0, max: 50, bonus: 0.9 },
                apprentice: { min: 51, max: 150, bonus: 1.0 },
                journeyman: { min: 151, max: 300, bonus: 1.1 },
                expert: { min: 301, max: 500, bonus: 1.2 },
                master: { min: 501, max: 750, bonus: 1.3 },
                grandmaster: { min: 751, max: 1000, bonus: 1.5 }
            }
        },
        ENCHANTING: {
            name: 'Enchanting',
            description: 'Add magical properties to items and create runes',
            primaryStats: ['intelligence', 'wisdom', 'charisma'],
            secondaryStats: ['dexterity', 'perception'],
            tools: ['enchanting_table', 'soul_gems', 'rune_carving_tools'],
            stations: ['enchanting_lab', 'arcane_circle', 'rune_forge'],
            skillProgression: {
                novice: { min: 0, max: 50, bonus: 0.9 },
                apprentice: { min: 51, max: 150, bonus: 1.0 },
                journeyman: { min: 151, max: 300, bonus: 1.1 },
                expert: { min: 301, max: 500, bonus: 1.2 },
                master: { min: 501, max: 750, bonus: 1.3 },
                grandmaster: { min: 751, max: 1000, bonus: 1.5 }
            }
        },
        TAILORING: {
            name: 'Tailoring',
            description: 'Create clothing, robes, bags, and textile items',
            primaryStats: ['dexterity', 'intelligence', 'perception'],
            secondaryStats: ['charisma', 'agility'],
            tools: ['needle', 'thread', 'scissors', 'loom', 'dye'],
            stations: ['tailoring_workshop', 'loom', 'dye_station'],
            skillProgression: {
                novice: { min: 0, max: 50, bonus: 0.9 },
                apprentice: { min: 51, max: 150, bonus: 1.0 },
                journeyman: { min: 151, max: 300, bonus: 1.1 },
                expert: { min: 301, max: 500, bonus: 1.2 },
                master: { min: 501, max: 750, bonus: 1.3 },
                grandmaster: { min: 751, max: 1000, bonus: 1.5 }
            }
        },
        JEWELCRAFTING: {
            name: 'Jewelcrafting',
            description: 'Cut gems and create jewelry with magical properties',
            primaryStats: ['dexterity', 'perception', 'intelligence'],
            secondaryStats: ['wisdom', 'charisma'],
            tools: ['jewelers_tools', 'gem_cutting_equipment', 'setting_tools'],
            stations: ['jewelers_bench', 'gem_cutting_station', 'forge'],
            skillProgression: {
                novice: { min: 0, max: 50, bonus: 0.9 },
                apprentice: { min: 51, max: 150, bonus: 1.0 },
                journeyman: { min: 151, max: 300, bonus: 1.1 },
                expert: { min: 301, max: 500, bonus: 1.2 },
                master: { min: 501, max: 750, bonus: 1.3 },
                grandmaster: { min: 751, max: 1000, bonus: 1.5 }
            }
        },
        WOODWORKING: {
            name: 'Woodworking',
            description: 'Craft bows, staves, furniture, and wooden items',
            primaryStats: ['strength', 'dexterity', 'perception'],
            secondaryStats: ['constitution', 'wisdom'],
            tools: ['carving_knife', 'saw', 'plane', 'lathe', 'sandpaper'],
            stations: ['woodworking_shop', 'sawmill', 'carving_bench'],
            skillProgression: {
                novice: { min: 0, max: 50, bonus: 0.9 },
                apprentice: { min: 51, max: 150, bonus: 1.0 },
                journeyman: { min: 151, max: 300, bonus: 1.1 },
                expert: { min: 301, max: 500, bonus: 1.2 },
                master: { min: 501, max: 750, bonus: 1.3 },
                grandmaster: { min: 751, max: 1000, bonus: 1.5 }
            }
        },
        COOKING: {
            name: 'Cooking',
            description: 'Prepare food and buff items with various effects',
            primaryStats: ['wisdom', 'dexterity', 'constitution'],
            secondaryStats: ['intelligence', 'charisma'],
            tools: ['knife', 'cutting_board', 'pot', 'pan', 'oven'],
            stations: ['kitchen', 'campfire', 'bakery', 'brewery'],
            skillProgression: {
                novice: { min: 0, max: 50, bonus: 0.9 },
                apprentice: { min: 51, max: 150, bonus: 1.0 },
                journeyman: { min: 151, max: 300, bonus: 1.1 },
                expert: { min: 301, max: 500, bonus: 1.2 },
                master: { min: 501, max: 750, bonus: 1.3 },
                grandmaster: { min: 751, max: 1000, bonus: 1.5 }
            }
        },
        INSCRIPTION: {
            name: 'Inscription',
            description: 'Create scrolls, tomes, and written magical items',
            primaryStats: ['intelligence', 'wisdom', 'dexterity'],
            secondaryStats: ['charisma', 'perception'],
            tools: ['quill', 'ink', 'parchment', 'binding_tools'],
            stations: ['scribes_desk', 'library', 'archive'],
            skillProgression: {
                novice: { min: 0, max: 50, bonus: 0.9 },
                apprentice: { min: 51, max: 150, bonus: 1.0 },
                journeyman: { min: 151, max: 300, bonus: 1.1 },
                expert: { min: 301, max: 500, bonus: 1.2 },
                master: { min: 501, max: 750, bonus: 1.3 },
                grandmaster: { min: 751, max: 1000, bonus: 1.5 }
            }
        }
    },

    // Social Features Configuration
    social: {
        orders: {
            maxActiveOrders: 10,
            orderTimeout: 7 * 24 * 60 * 60 * 1000, // 7 days
            escrowFee: 0.05, // 5%
            minReputationForOrders: 3.0,
            cancellationPenalty: 0.1
        },
        guildWorkshops: {
            maxMembers: 50,
            upgradeCostMultiplier: 1.5,
            maintenanceCost: 100, // per day
            maxLevel: 10,
            sharingBonus: 0.2
        },
        competitions: {
            maxParticipants: 100,
            minReputationToHost: 4.0,
            entryFeeRange: { min: 10, max: 10000 },
            prizePoolMultiplier: 0.8, // 80% of entry fees go to prizes
            judgingPeriod: 3 * 24 * 60 * 60 * 1000 // 3 days
        },
        apprenticeships: {
            maxDuration: 365, // days
            minMasterLevel: 300,
            maxApprenticesPerMaster: 3,
            graduationRequirements: {
                minSkillLevel: 200,
                itemsCrafted: 100,
                qualityAverage: 70,
                lessonsCompleted: 20
            }
        },
        marketplace: {
            listingFee: 0.02, // 2%
            saleFee: 0.05, // 5%
            maxListingDuration: 30 * 24 * 60 * 60 * 1000, // 30 days
            minReputationToSell: 2.0,
            maxActiveListings: 50
        }
    },

    // Economy Configuration
    economy: {
        baseCurrency: 'gold',
        exchangeRates: {
            gold: { silver: 100, copper: 10000 },
            silver: { gold: 0.01, copper: 100 },
            copper: { gold: 0.0001, silver: 0.01 }
        },
        materialBaseValues: {
            // Base values per unit (multiplied by quality and rarity)
            iron: 10,
            steel: 25,
            mithril: 100,
            herb_common: 5,
            herb_rare: 20,
            gem_common: 15,
            gem_rare: 75,
            wood_common: 3,
            wood_rare: 15
        },
        craftingCosts: {
            laborMultiplier: 0.1, // 10% of material value
            toolWearMultiplier: 0.05, // 5% of material value
            stationFeeMultiplier: 0.02 // 2% of material value
        },
        priceInflation: {
            enabled: true,
            baseRate: 0.001, // 0.1% per day
            supplyDemandFactor: 0.1,
            qualityMultiplier: 1.5
        }
    },

    // Harvesting Configuration
    harvesting: {
        zones: {
            forest: {
                materials: ['wood', 'herbs', 'resin'],
                difficulty: 1,
                abundance: 0.8,
                qualityModifier: 0,
                dangerLevel: 1
            },
            mountains: {
                materials: ['metal', 'gems', 'stone'],
                difficulty: 3,
                abundance: 0.5,
                qualityModifier: 10,
                dangerLevel: 3
            },
            swamp: {
                materials: ['herbs', 'alchemical', 'rare_components'],
                difficulty: 2,
                abundance: 0.6,
                qualityModifier: 5,
                dangerLevel: 2
            },
            desert: {
                materials: ['gems', 'rare_metal', 'magical'],
                difficulty: 4,
                abundance: 0.3,
                qualityModifier: 15,
                dangerLevel: 4
            },
            magical_realm: {
                materials: ['magical', 'essences', 'rare_gems'],
                difficulty: 5,
                abundance: 0.2,
                qualityModifier: 25,
                dangerLevel: 5
            }
        },
        tools: {
            basic: { efficiency: 1.0, durability: 100, bonusChance: 0 },
            iron: { efficiency: 1.2, durability: 150, bonusChance: 0.05 },
            steel: { efficiency: 1.4, durability: 200, bonusChance: 0.1 },
            masterwork: { efficiency: 1.6, durability: 300, bonusChance: 0.15 },
            legendary: { efficiency: 2.0, durability: 500, bonusChance: 0.25 }
        },
        environmentalFactors: {
            weather: {
                clear: { modifier: 1.0 },
                rain: { modifier: 0.9 },
                storm: { modifier: 0.7 },
                snow: { modifier: 0.8 }
            },
            timeOfDay: {
                dawn: { modifier: 1.1 },
                day: { modifier: 1.0 },
                dusk: { modifier: 1.05 },
                night: { modifier: 0.95 }
            },
            season: {
                spring: { modifier: 1.1 },
                summer: { modifier: 1.0 },
                autumn: { modifier: 1.05 },
                winter: { modifier: 0.9 }
            }
        }
    },

    // Experience and Progression
    experience: {
        baseCraftingExp: 25,
        levelUpBonus: 100,
        guildBonus: 1.2,
        toolQualityBonus: 0.1,
        materialQualityBonus: 0.2,
        criticalSuccessBonus: 2.0,
        firstTimeBonus: 5.0,
        experimentationBonus: 1.5,
        teachingBonus: 0.5
    },

    // Quality and Durability
    quality: {
        baseDurability: 100,
        qualityDurabilityMultiplier: 2,
        criticalDurabilityBonus: 1.5,
        repairCostMultiplier: 0.3,
        degradationRate: 0.01, // per use
        minimumRepairQuality: 20
    },

    // Integration Settings
    integration: {
        n8n: {
            enabled: true,
            webhookUrl: 'http://localhost:5678/webhook',
            timeout: 30000,
            retryAttempts: 3,
            apiKey: process.env.N8N_API_KEY
        },
        database: {
            type: 'mongodb',
            url: process.env.DATABASE_URL,
            collectionPrefix: 'crafting_',
            indexes: ['crafterId', 'recipeId', 'materialId', 'timestamp']
        },
        inventory: {
            enabled: true,
            autoUpdate: true,
            stackSizes: {
                materials: 999,
                consumables: 99,
                equipment: 1,
                artifacts: 1
            }
        },
        notifications: {
            enabled: true,
            channels: ['in_game', 'email', 'webhook'],
            events: ['crafting_completed', 'order_received', 'competition_started']
        }
    },

    // Performance and Scaling
    performance: {
        maxConcurrentCrafts: 100,
        cacheSize: 10000,
        cacheTimeout: 300000, // 5 minutes
        batchSize: 50,
        cleanupInterval: 3600000, // 1 hour
        maxDatabaseConnections: 20
    },

    // Debugging and Logging
    debugging: {
        enabled: process.env.NODE_ENV === 'development',
        logLevel: 'info',
        detailedLogging: false,
        performanceMonitoring: true,
        errorTracking: true
    }
};

module.exports = CraftingConfig;