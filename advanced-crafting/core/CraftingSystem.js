/**
 * Advanced Crafting System Core
 * Handles multi-tier crafting with complex mechanics and social features
 */

class CraftingSystem {
    constructor(config) {
        this.config = {
            maxSkillLevel: 1000,
            baseCritChance: 0.05,
            baseCritFailureChance: 0.02,
            qualityDecayRate: 0.1,
            experimentCostMultiplier: 2,
            guildBonusMultiplier: 1.2,
            toolQualityMultiplier: 1.15,
            ...config
        };

        this.professions = new Map();
        this.recipes = new Map();
        this.materials = new Map();
        this.crafters = new Map();
        this.guilds = new Map();
        this.orders = new Map();
        this.competitions = new Map();

        this.initializeSystem();
    }

    initializeSystem() {
        this.loadProfessions();
        this.loadMaterials();
        this.loadRecipes();
        this.initializeCraftingTiers();
        this.setupEventHandlers();
    }

    /**
     * Crafting Tiers System
     */
    initializeCraftingTiers() {
        this.craftingTiers = {
            SIMPLE: {
                name: 'Simple Crafting',
                requiredSkill: 0,
                successBonus: 0.2,
                qualityMultiplier: 1.0,
                expMultiplier: 1.0,
                description: 'Basic items with common materials'
            },
            ADVANCED: {
                name: 'Advanced Crafting',
                requiredSkill: 100,
                successBonus: 0.0,
                qualityMultiplier: 1.25,
                expMultiplier: 1.5,
                description: 'Rare materials and skill checks required'
            },
            MASTER: {
                name: 'Master Crafting',
                requiredSkill: 300,
                successBonus: -0.1,
                qualityMultiplier: 1.5,
                expMultiplier: 2.0,
                description: 'Legendary items with special techniques'
            },
            ARTIFACT: {
                name: 'Artifact Creation',
                requiredSkill: 500,
                successBonus: -0.2,
                qualityMultiplier: 2.0,
                expMultiplier: 3.0,
                description: 'Unique items requiring quest completion'
            },
            MAGICAL: {
                name: 'Magical Infusion',
                requiredSkill: 700,
                successBonus: -0.15,
                qualityMultiplier: 1.75,
                expMultiplier: 2.5,
                description: 'Enchanting and magical imbuing'
            }
        };
    }

    /**
     * Main Crafting Method
     */
    async craftItem(crafterId, recipeId, materials, options = {}) {
        const crafter = this.getCrafter(crafterId);
        const recipe = this.getRecipe(recipeId);

        if (!crafter || !recipe) {
            throw new Error('Invalid crafter or recipe');
        }

        // Validate crafting requirements
        const validation = await this.validateCraftingRequirements(crafter, recipe, materials, options);
        if (!validation.valid) {
            throw new Error(`Crafting validation failed: ${validation.reason}`);
        }

        // Calculate success chances
        const successChance = this.calculateSuccessChance(crafter, recipe, materials, options);

        // Perform crafting attempt
        const result = await this.performCraftingAttempt(crafter, recipe, materials, successChance, options);

        // Update crafter statistics
        this.updateCrafterStats(crafter, result);

        // Handle social features
        await this.handleSocialFeatures(crafter, recipe, result, options);

        return result;
    }

    /**
     * Validate Crafting Requirements
     */
    async validateCraftingRequirements(crafter, recipe, materials, options) {
        // Check skill requirements
        if (crafter.skills[recipe.profession] < recipe.requiredSkill) {
            return { valid: false, reason: 'Insufficient skill level' };
        }

        // Check materials
        const materialValidation = this.validateMaterials(recipe, materials);
        if (!materialValidation.valid) {
            return materialValidation;
        }

        // Check tool requirements
        if (!this.validateTools(crafter, recipe.requiredTools)) {
            return { valid: false, reason: 'Required tools not available' };
        }

        // Check station requirements
        if (!this.validateStation(crafter, recipe.requiredStation)) {
            return { valid: false, reason: 'Required crafting station not available' };
        }

        // Check quest requirements for artifact creation
        if (recipe.tier === 'ARTIFACT') {
            if (!this.validateQuestRequirements(crafter, recipe.questRequirements)) {
                return { valid: false, reason: 'Quest requirements not met' };
            }
        }

        return { valid: true };
    }

    /**
     * Calculate Success Chance
     */
    calculateSuccessChance(crafter, recipe, materials, options) {
        let baseChance = 0.5; // 50% base chance

        // Skill level influence
        const skillLevel = crafter.skills[recipe.profession];
        const skillBonus = Math.min(skillLevel / recipe.requiredSkill, 2.0) * 0.3;
        baseChance += skillBonus;

        // Tier modifier
        const tier = this.craftingTiers[recipe.tier];
        baseChance += tier.successBonus;

        // Material quality bonus
        const materialQuality = this.calculateAverageMaterialQuality(materials);
        baseChance += (materialQuality - 50) * 0.002; // 0.2% per quality point above 50

        // Tool quality bonus
        const toolBonus = this.calculateToolBonus(crafter, recipe.requiredTools);
        baseChance += toolBonus;

        // Guild bonus
        if (crafter.guildId) {
            baseChance += this.config.guildBonusMultiplier * 0.05;
        }

        // Experimentation penalty
        if (options.isExperiment) {
            baseChance -= 0.2;
        }

        // Environmental factors
        baseChance += this.calculateEnvironmentalBonus(crafter, recipe);

        return Math.max(0.1, Math.min(0.95, baseChance)); // Clamp between 10% and 95%
    }

    /**
     * Perform Crafting Attempt
     */
    async performCraftingAttempt(crafter, recipe, materials, successChance, options) {
        const roll = Math.random();
        const isCritSuccess = roll < successChance - this.config.baseCritChance;
        const isCritFailure = roll > successChance + this.config.baseCritFailureChance;
        const isSuccess = roll < successChance && !isCritFailure;

        const result = {
            crafterId: crafter.id,
            recipeId: recipe.id,
            timestamp: new Date().toISOString(),
            success: isSuccess,
            criticalSuccess: isCritSuccess,
            criticalFailure: isCritFailure,
            materials: materials,
            options: options,
            experience: 0,
            quality: 0,
            durability: 0,
            properties: {},
            bonuses: {}
        };

        if (isSuccess) {
            // Calculate item quality
            result.quality = this.calculateItemQuality(crafter, recipe, materials, isCritSuccess);
            result.durability = this.calculateItemDurability(recipe, result.quality, isCritSuccess);
            result.properties = this.generateItemProperties(recipe, result.quality, isCritSuccess);

            // Handle critical success bonuses
            if (isCritSuccess) {
                result.bonuses = this.generateCriticalSuccessBonuses(recipe, result.quality);
                result.experience = recipe.experience * 2;
            } else {
                result.experience = recipe.experience;
            }

            // Create the actual item
            result.item = await this.createItem(recipe, result);
        } else {
            // Handle failure
            if (isCritFailure) {
                result.failureType = 'critical';
                result.penalties = this.generateCriticalFailurePenalties(recipe, materials);
                result.experience = Math.floor(recipe.experience * 0.1);
            } else {
                result.failureType = 'normal';
                result.experience = Math.floor(recipe.experience * 0.3);
            }
        }

        return result;
    }

    /**
     * Calculate Item Quality
     */
    calculateItemQuality(crafter, recipe, materials, isCritSuccess) {
        let baseQuality = 50; // Average quality

        // Skill influence
        const skillLevel = crafter.skills[recipe.profession];
        const skillQuality = Math.min(skillLevel / 100, 5) * 10;
        baseQuality += skillQuality;

        // Material quality influence
        const materialQuality = this.calculateAverageMaterialQuality(materials);
        baseQuality += (materialQuality - 50) * 0.5;

        // Tool quality influence
        const toolQuality = this.calculateAverageToolQuality(crafter, recipe.requiredTools);
        baseQuality += (toolQuality - 50) * 0.3;

        // Tier multiplier
        const tier = this.craftingTiers[recipe.tier];
        baseQuality *= tier.qualityMultiplier;

        // Critical success bonus
        if (isCritSuccess) {
            baseQuality += 25;
        }

        // Random variation
        baseQuality += (Math.random() - 0.5) * 20;

        return Math.max(1, Math.min(100, Math.floor(baseQuality)));
    }

    /**
     * Generate Item Properties
     */
    generateItemProperties(recipe, quality, isCritSuccess) {
        const properties = {};

        // Base properties from recipe
        Object.assign(properties, recipe.baseProperties);

        // Quality-based enhancements
        if (quality >= 90) {
            // Legendary quality
            properties.legendary = true;
            properties.bonusStats = this.calculateBonusStats(quality, 1.5);
        } else if (quality >= 75) {
            // Epic quality
            properties.epic = true;
            properties.bonusStats = this.calculateBonusStats(quality, 1.25);
        } else if (quality >= 60) {
            // Rare quality
            properties.rare = true;
            properties.bonusStats = this.calculateBonusStats(quality, 1.1);
        }

        // Critical success properties
        if (isCritSuccess) {
            properties.crafted = true;
            properties.masterwork = true;
            properties.additionalSlots = this.generateAdditionalSlots(recipe.type);
        }

        // Special properties based on materials
        properties.materialProperties = this.generateMaterialProperties(recipe.materials);

        return properties;
    }

    /**
     * Handle Discovery and Experimentation
     */
    async discoverRecipe(crafterId, baseRecipeId, experimentMaterials) {
        const crafter = this.getCrafter(crafterId);
        const baseRecipe = this.getRecipe(baseRecipeId);

        if (!crafter || !baseRecipe) {
            throw new Error('Invalid crafter or recipe');
        }

        // Experimentation cost
        const cost = this.calculateExperimentationCost(baseRecipe, experimentMaterials);
        if (crafter.resources.gold < cost) {
            throw new Error('Insufficient resources for experimentation');
        }

        // Chance of discovery based on skill and materials
        const discoveryChance = this.calculateDiscoveryChance(crafter, baseRecipe, experimentMaterials);

        if (Math.random() < discoveryChance) {
            // Create new recipe variant
            const newRecipe = await this.createRecipeVariant(baseRecipe, experimentMaterials);
            this.recipes.set(newRecipe.id, newRecipe);

            // Grant discovery experience
            crafter.experience[baseRecipe.profession] += baseRecipe.experimentationExperience;

            return {
                success: true,
                recipe: newRecipe,
                experience: baseRecipe.experimentationExperience
            };
        }

        return {
            success: false,
            cost: cost,
            experience: Math.floor(baseRecipe.experimentationExperience * 0.2)
        };
    }

    /**
     * Social Features - Crafting Orders
     */
    async createCraftingOrder(clientId, specifications, payment, deadline) {
        const order = {
            id: this.generateId(),
            clientId: clientId,
            specifications: specifications,
            payment: payment,
            deadline: deadline,
            status: 'open',
            createdAt: new Date().toISOString(),
            applicants: []
        };

        this.orders.set(order.id, order);
        this.notifyAvailableCrafters(order);

        return order;
    }

    /**
     * Guild Workshop Management
     */
    async createGuildWorkshop(guildId, workshopType, level, resources) {
        const workshop = {
            id: this.generateId(),
            guildId: guildId,
            type: workshopType,
            level: level,
            resources: resources,
            bonuses: this.calculateWorkshopBonuses(workshopType, level),
            members: [],
            upgrades: [],
            createdAt: new Date().toISOString()
        };

        if (!this.guilds.has(guildId)) {
            this.guilds.set(guildId, { workshops: [] });
        }

        this.guilds.get(guildId).workshops.push(workshop);
        return workshop;
    }

    /**
     * Master-Apprentice System
     */
    async createApprenticeship(masterId, apprenticeId, terms) {
        const apprenticeship = {
            id: this.generateId(),
            masterId: masterId,
            apprenticeId: apprenticeId,
            terms: terms,
            startDate: new Date().toISOString(),
            status: 'active',
            progress: {
                lessonsCompleted: 0,
                itemsCrafted: 0,
                skillIncrease: 0
            }
        };

        // Update crafter records
        const master = this.getCrafter(masterId);
        const apprentice = this.getCrafter(apprenticeId);

        if (master && apprentice) {
            master.apprentices = master.apprentices || [];
            master.apprentices.push(apprenticeId);

            apprentice.master = masterId;
            apprentice.apprenticeship = apprenticeship.id;
        }

        return apprenticeship;
    }

    /**
     * Crafting Competition System
     */
    async createCompetition(organizerId, competitionDetails) {
        const competition = {
            id: this.generateId(),
            organizerId: organizerId,
            ...competitionDetails,
            status: 'registration',
            participants: [],
            submissions: {},
            judges: [],
            prizes: competitionDetails.prizes,
            rules: competitionDetails.rules,
            startDate: competitionDetails.startDate,
            endDate: competitionDetails.endDate,
            createdAt: new Date().toISOString()
        };

        this.competitions.set(competition.id, competition);
        return competition;
    }

    /**
     * Utility Methods
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    getCrafter(crafterId) {
        return this.crafters.get(crafterId);
    }

    getRecipe(recipeId) {
        return this.recipes.get(recipeId);
    }

    getMaterial(materialId) {
        return this.materials.get(materialId);
    }

    calculateAverageMaterialQuality(materials) {
        if (!materials || materials.length === 0) return 50;

        const totalQuality = materials.reduce((sum, mat) => {
            const material = this.getMaterial(mat.id);
            return sum + (material ? material.quality : 50);
        }, 0);

        return totalQuality / materials.length;
    }

    calculateAverageToolQuality(crafter, requiredTools) {
        // Implementation for tool quality calculation
        return 70; // Placeholder
    }

    calculateBonusStats(quality, multiplier) {
        return {
            damage: Math.floor(quality * multiplier),
            durability: Math.floor(quality * multiplier * 1.2),
            specialEffect: quality >= 90 ? this.generateSpecialEffect() : null
        };
    }

    generateSpecialEffect() {
        const effects = [
            'fiery_enchantment',
            'frost_protection',
            'lightning_strike',
            'healing_aura',
            'stealth_boost',
            'strength_enhancement'
        ];
        return effects[Math.floor(Math.random() * effects.length)];
    }

    updateCrafterStats(crafter, result) {
        // Update experience
        const profession = this.getRecipe(result.recipeId).profession;
        crafter.experience[profession] = (crafter.experience[profession] || 0) + result.experience;

        // Check for level up
        this.checkSkillLevelUp(crafter, profession);

        // Update statistics
        crafter.stats = crafter.stats || {};
        crafter.stats.totalCrafts = (crafter.stats.totalCrafts || 0) + 1;

        if (result.success) {
            crafter.stats.successfulCrafts = (crafter.stats.successfulCrafts || 0) + 1;
        }

        if (result.criticalSuccess) {
            crafter.stats.criticalSuccesses = (crafter.stats.criticalSuccesses || 0) + 1;
        }
    }

    checkSkillLevelUp(crafter, profession) {
        const currentLevel = crafter.skills[profession] || 0;
        const experience = crafter.experience[profession] || 0;
        const requiredExp = this.calculateRequiredExperience(currentLevel);

        if (experience >= requiredExp && currentLevel < this.config.maxSkillLevel) {
            crafter.skills[profession] = currentLevel + 1;
            crafter.experience[profession] = experience - requiredExp;

            // Trigger level up event
            this.emit('skillLevelUp', {
                crafterId: crafter.id,
                profession: profession,
                newLevel: crafter.skills[profession]
            });
        }
    }

    calculateRequiredExperience(level) {
        return Math.floor(100 * Math.pow(1.1, level));
    }

    setupEventHandlers() {
        this.eventHandlers = new Map();
    }

    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    emit(event, data) {
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            handlers.forEach(handler => handler(data));
        }
    }
}

module.exports = CraftingSystem;