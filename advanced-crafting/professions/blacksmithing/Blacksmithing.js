/**
 * Blacksmithing Profession
 * Handles weapon, armor, and tool crafting with advanced metallurgy
 */

class Blacksmithing {
    constructor(craftingSystem, materialSystem) {
        this.craftingSystem = craftingSystem;
        this.materialSystem = materialSystem;
        this.recipes = new Map();
        this.techniques = new Map();
        this.forgingMethods = new Map();
        this.alloys = new Map();

        this.initializeProfession();
        this.loadRecipes();
        this.loadTechniques();
        this.loadAlloys();
    }

    /**
     * Initialize Blacksmithing Profession
     */
    initializeProfession() {
        this.professionConfig = {
            name: 'Blacksmithing',
            description: 'Master the art of metalworking to create weapons, armor, and tools',
            primaryStats: ['strength', 'dexterity', 'intelligence'],
            tools: ['hammer', 'tongs', 'anvil', 'forge', 'grindstone'],
            stations: ['forge', 'workbench', 'grindstone'],
            skillModifiers: {
                weaponCrafting: 1.0,
                armorCrafting: 1.0,
                toolCrafting: 0.8,
                alloyCreation: 1.2
            }
        };

        // Register profession with crafting system
        this.craftingSystem.professions.set('BLACKSMITHING', this.professionConfig);
    }

    /**
     * Load Blacksmithing Recipes
     */
    loadRecipes() {
        // Weapon Recipes
        this.addRecipe({
            id: 'dagger_basic',
            name: 'Basic Dagger',
            type: 'weapon',
            tier: 'SIMPLE',
            requiredSkill: 10,
            materials: [
                { id: 'iron_ingot', quantity: 2 },
                { id: 'leather_strip', quantity: 1 }
            ],
            tools: ['hammer', 'tongs'],
            station: 'forge',
            craftingTime: 30,
            experience: 25,
            baseProperties: {
                damage: 15,
                durability: 100,
                weight: 1.5,
                slot: 'one_handed'
            }
        });

        this.addRecipe({
            id: 'longsword_steel',
            name: 'Steel Longsword',
            type: 'weapon',
            tier: 'ADVANCED',
            requiredSkill: 150,
            materials: [
                { id: 'steel_ingot', quantity: 3 },
                { id: 'leather_strip', quantity: 2 },
                { id: 'ruby', quantity: 1 } // Optional for bonus
            ],
            tools: ['hammer', 'tongs', 'grindstone'],
            station: 'forge',
            craftingTime: 120,
            experience: 150,
            baseProperties: {
                damage: 45,
                durability: 250,
                weight: 3.5,
                slot: 'one_handed',
                criticalChance: 0.05
            }
        });

        this.addRecipe({
            id: 'greatsword_masterwork',
            name: 'Masterwork Greatsword',
            type: 'weapon',
            tier: 'MASTER',
            requiredSkill: 400,
            materials: [
                { id: 'mithril_ingot', quantity: 4 },
                { id: 'dragon_scale', quantity: 2 },
                { id: 'enchanted_leather', quantity: 3 },
                { id: 'soul_gem', quantity: 1 }
            ],
            tools: ['master_hammer', 'tongs', 'grindstone'],
            station: 'master_forge',
            craftingTime: 300,
            experience: 500,
            baseProperties: {
                damage: 85,
                durability: 500,
                weight: 6.0,
                slot: 'two_handed',
                criticalChance: 0.10,
                magicalDamage: 15
            },
            specialEffects: ['soul_bound', 'unbreakable_edge']
        });

        // Armor Recipes
        this.addRecipe({
            id: 'chainmail_basic',
            name: 'Basic Chainmail',
            type: 'armor',
            tier: 'SIMPLE',
            requiredSkill: 25,
            materials: [
                { id: 'iron_ingot', quantity: 15 },
                { id: 'leather_strip', quantity: 5 }
            ],
            tools: ['hammer', 'tongs'],
            station: 'forge',
            craftingTime: 180,
            experience: 50,
            baseProperties: {
                defense: 20,
                durability: 200,
                weight: 15.0,
                slot: 'chest'
            }
        });

        this.addRecipe({
            id: 'plate_armor_steel',
            name: 'Steel Plate Armor',
            type: 'armor',
            tier: 'ADVANCED',
            requiredSkill: 200,
            materials: [
                { id: 'steel_ingot', quantity: 20 },
                { id: 'leather_padding', quantity: 8 },
                { id: 'iron_chain', quantity: 10 }
            ],
            tools: ['hammer', 'tongs', 'anvil'],
            station: 'forge',
            craftingTime: 480,
            experience: 200,
            baseProperties: {
                defense: 60,
                durability: 450,
                weight: 35.0,
                slot: 'chest',
                damageReduction: 0.15
            }
        });

        // Tool Recipes
        this.addRecipe({
            id: 'pickaxe_iron',
            name: 'Iron Pickaxe',
            type: 'tool',
            tier: 'SIMPLE',
            requiredSkill: 15,
            materials: [
                { id: 'iron_ingot', quantity: 3 },
                { id: 'wood_handle', quantity: 1 }
            ],
            tools: ['hammer', 'tongs'],
            station: 'forge',
            craftingTime: 45,
            experience: 20,
            baseProperties: {
                efficiency: 1.2,
                durability: 150,
                weight: 4.0,
                toolType: 'mining'
            }
        });

        // Shield Recipes
        this.addRecipe({
            id: 'tower_shield_steel',
            name: 'Steel Tower Shield',
            type: 'shield',
            tier: 'ADVANCED',
            requiredSkill: 180,
            materials: [
                { id: 'steel_ingot', quantity: 8 },
                { id: 'iron_reinforcement', quantity: 4 },
                { id: 'leather_strap', quantity: 2 }
            ],
            tools: ['hammer', 'tongs', 'anvil'],
            station: 'forge',
            craftingTime: 240,
            experience: 180,
            baseProperties: {
                defense: 40,
                blockChance: 0.25,
                durability: 350,
                weight: 12.0,
                slot: 'off_hand'
            }
        });

        // Artifact Recipes
        this.addRecipe({
            id: 'sword_of_flames',
            name: 'Sword of Eternal Flames',
            type: 'weapon',
            tier: 'ARTIFACT',
            requiredSkill: 600,
            materials: [
                { id: 'heart_of_fire', quantity: 1 },
                { id: 'phoenix_feather', quantity: 3 },
                { id: 'obsidian_ingot', quantity: 5 },
                { id: 'fire_essence', quantity: 10 },
                { id: 'ancient_rune', quantity: 2 }
            ],
            tools: ['legendary_hammer', 'mystical_tongs'],
            station: 'elemental_forge',
            craftingTime: 1440, // 24 hours
            experience: 2000,
            baseProperties: {
                damage: 120,
                fireDamage: 50,
                durability: 800,
                weight: 4.0,
                slot: 'one_handed',
                criticalChance: 0.15,
                burningDuration: 10
            },
            specialEffects: ['immolate', 'fire_resistance', 'soul_steal'],
            questRequirements: [
                'defeat_fire_elemental_lord',
                'obtain_phoenix_blessing',
                'master_elemental_forging'
            ]
        });
    }

    /**
     * Advanced Forging Techniques
     */
    loadTechniques() {
        this.techniques.set('FOLDING', {
            name: 'Pattern Welding',
            description: 'Fold metal multiple times to increase durability and sharpness',
            requiredSkill: 200,
            benefits: {
                durability: 1.3,
                damage: 1.1,
                quality: 1.2
            },
            costMultiplier: 2.5,
            timeMultiplier: 3.0
        });

        this.techniques.set('DIFFERENTIAL_HARDENING', {
            name: 'Differential Hardening',
            description: 'Create hard edge and soft spine for optimal balance',
            requiredSkill: 350,
            benefits: {
                damage: 1.4,
                durability: 1.1,
                criticalChance: 1.2
            },
            costMultiplier: 3.0,
            timeMultiplier: 2.5
        });

        this.techniques.set('CRYSTAL_INFUSION', {
            name: 'Crystal Infusion',
            description: 'Infuse magical crystals into metal for enhanced properties',
            requiredSkill: 500,
            benefits: {
                magicalDamage: 1.5,
                specialEffects: 2,
                quality: 1.3
            },
            costMultiplier: 5.0,
            timeMultiplier: 4.0
        });

        this.techniques.set('SOUL_BINDING', {
            name: 'Soul Binding',
            description: 'Bind a soul to the weapon for sentience and power',
            requiredSkill: 700,
            benefits: {
                damage: 1.8,
                specialEffects: 3,
                sentient: true
            },
            costMultiplier: 10.0,
            timeMultiplier: 8.0
        });
    }

    /**
     * Alloy Creation System
     */
    loadAlloys() {
        this.alloys.set('STEEL', {
            name: 'Steel',
            components: [
                { material: 'iron_ingot', ratio: 0.98 },
                { material: 'carbon', ratio: 0.02 }
            ],
            requiredSkill: 100,
            properties: {
                hardness: 75,
                durability: 80,
                weight: 7.8
            },
            benefits: {
                damage: 1.3,
                defense: 1.2,
                durability: 1.4
            }
        });

        this.alloys.set('BRONZE', {
            name: 'Bronze',
            components: [
                { material: 'copper_ingot', ratio: 0.88 },
                { material: 'tin_ingot', ratio: 0.12 }
            ],
            requiredSkill: 50,
            properties: {
                hardness: 60,
                durability: 70,
                weight: 8.7
            },
            benefits: {
                damage: 1.1,
                defense: 1.1,
                corrosion_resistance: 2.0
            }
        });

        this.alloys.set('MITHRIL_ALLOY', {
            name: 'Mithril Alloy',
            components: [
                { material: 'mithril_ore', ratio: 0.85 },
                { material: 'silver_ingot', ratio: 0.10 },
                { material: 'moonstone_dust', ratio: 0.05 }
            ],
            requiredSkill: 400,
            properties: {
                hardness: 90,
                durability: 95,
                weight: 3.5,
                magical_conductivity: 85
            },
            benefits: {
                damage: 1.6,
                defense: 1.4,
                weight: 0.5,
                magical_affinity: 1.5
            }
        });

        this.alloys.set('DAMASCUS', {
            name: 'Damascus Steel',
            components: [
                { material: 'wootz_iron', ratio: 0.5 },
                { material: 'pattern_steel', ratio: 0.5 }
            ],
            requiredSkill: 600,
            properties: {
                hardness: 85,
                durability: 90,
                weight: 7.2,
                pattern_beauty: 95
            },
            benefits: {
                damage: 1.7,
                durability: 1.6,
                criticalChance: 1.3,
                aesthetic_value: 2.0
            }
        });
    }

    /**
     * Custom Crafting with Techniques
     */
    async craftWithTechnique(crafterId, recipeId, materials, techniqueIds, options = {}) {
        const crafter = this.craftingSystem.getCrafter(crafterId);
        const recipe = this.getRecipe(recipeId);

        if (!crafter || !recipe) {
            throw new Error('Invalid crafter or recipe');
        }

        // Validate techniques
        const validTechniques = this.validateTechniques(crafter, techniqueIds);
        if (!validTechniques.valid) {
            throw new Error(`Technique validation failed: ${validTechniques.reason}`);
        }

        // Calculate modified requirements
        const modifiedRecipe = this.applyTechniquesToRecipe(recipe, techniqueIds);

        // Perform crafting with modified parameters
        const craftingOptions = {
            ...options,
            techniques: techniqueIds,
            modifiedRecipe: modifiedRecipe
        };

        return await this.craftingSystem.craftItem(crafterId, recipeId, materials, craftingOptions);
    }

    /**
     * Create Custom Alloy
     */
    async createAlloy(crafterId, alloyId, components, quality = null) {
        const crafter = this.craftingSystem.getCrafter(crafterId);
        const alloy = this.alloys.get(alloyId);

        if (!crafter || !alloy) {
            throw new Error('Invalid crafter or alloy');
        }

        // Check skill requirements
        if (crafter.skills.BLACKSMITHING < alloy.requiredSkill) {
            throw new Error('Insufficient skill for alloy creation');
        }

        // Validate components
        const componentValidation = this.validateAlloyComponents(components, alloy.components);
        if (!componentValidation.valid) {
            throw new Error(`Component validation failed: ${componentValidation.reason}`);
        }

        // Calculate success chance
        const successChance = this.calculateAlloySuccessChance(crafter, alloy, components);

        if (Math.random() < successChance) {
            // Create alloy material
            const alloyMaterial = this.createAlloyMaterial(alloy, components, quality);

            // Update crafter stats
            this.updateAlloyStats(crafter, alloy);

            return {
                success: true,
                material: alloyMaterial,
                experience: this.calculateAlloyExperience(alloy)
            };
        }

        return {
            success: false,
            experience: Math.floor(this.calculateAlloyExperience(alloy) * 0.3)
        };
    }

    /**
     * Weapon Tempering and Enhancement
     */
    async temperWeapon(crafterId, weaponId, temperingType, materials) {
        const crafter = this.craftingSystem.getCrafter(crafterId);
        const weapon = this.getItem(weaponId); // This would integrate with inventory system

        if (!crafter || !weapon) {
            throw new Error('Invalid crafter or weapon');
        }

        if (weapon.type !== 'weapon') {
            throw new Error('Item is not a weapon');
        }

        const temperingRecipe = this.getTemperingRecipe(temperingType);
        if (!temperingRecipe) {
            throw new Error('Invalid tempering type');
        }

        // Validate requirements
        const validation = this.validateTemperingRequirements(crafter, weapon, temperingRecipe, materials);
        if (!validation.valid) {
            throw new Error(`Tempering validation failed: ${validation.reason}`);
        }

        // Perform tempering
        const result = await this.performTempering(weapon, temperingRecipe, materials);

        return result;
    }

    /**
     * Mass Production Orders
     */
    async createProductionOrder(crafterId, orderDetails) {
        const crafter = this.craftingSystem.getCrafter(crafterId);

        if (!crafter) {
            throw new Error('Invalid crafter');
        }

        const productionOrder = {
            id: this.generateOrderId(),
            crafterId: crafterId,
            clientId: orderDetails.clientId,
            items: orderDetails.items,
            quantity: orderDetails.quantity,
            specifications: orderDetails.specifications,
            deadline: orderDetails.deadline,
            payment: orderDetails.payment,
            status: 'accepted',
            progress: 0,
            createdAt: new Date().toISOString()
        };

        // Calculate production time and requirements
        productionOrder.estimatedTime = this.calculateProductionTime(productionOrder);
        productionOrder.requiredMaterials = this.calculateRequiredMaterials(productionOrder);

        return productionOrder;
    }

    /**
     * Utility Methods
     */
    addRecipe(recipeData) {
        const recipe = {
            ...recipeData,
            profession: 'BLACKSMITHING',
            id: recipeData.id || this.generateRecipeId()
        };

        this.recipes.set(recipe.id, recipe);
        this.craftingSystem.recipes.set(recipe.id, recipe);
    }

    getRecipe(recipeId) {
        return this.recipes.get(recipeId);
    }

    validateTechniques(crafter, techniqueIds) {
        if (!techniqueIds || techniqueIds.length === 0) {
            return { valid: true, techniques: [] };
        }

        const validTechniques = [];
        const requiredSkill = crafter.skills.BLACKSMITHING || 0;

        for (const techniqueId of techniqueIds) {
            const technique = this.techniques.get(techniqueId);
            if (!technique) {
                return { valid: false, reason: `Unknown technique: ${techniqueId}` };
            }

            if (requiredSkill < technique.requiredSkill) {
                return { valid: false, reason: `Insufficient skill for ${technique.name}` };
            }

            validTechniques.push(technique);
        }

        return { valid: true, techniques: validTechniques };
    }

    applyTechniquesToRecipe(recipe, techniqueIds) {
        let modifiedRecipe = { ...recipe };

        techniqueIds.forEach(techniqueId => {
            const technique = this.techniques.get(techniqueId);
            if (technique) {
                modifiedRecipe.craftingTime *= technique.timeMultiplier;
                modifiedRecipe.experience *= 1.5;

                // Apply benefits to base properties
                Object.keys(technique.benefits).forEach(benefit => {
                    if (modifiedRecipe.baseProperties[benefit]) {
                        modifiedRecipe.baseProperties[benefit] *= technique.benefits[benefit];
                    }
                });
            }
        });

        return modifiedRecipe;
    }

    calculateAlloySuccessChance(crafter, alloy, components) {
        let baseChance = 0.4;

        // Skill influence
        const skillBonus = Math.min((crafter.skills.BLACKSMITHING - alloy.requiredSkill) / 100, 1) * 0.3;
        baseChance += skillBonus;

        // Component quality influence
        const componentQuality = this.calculateAverageComponentQuality(components);
        baseChance += (componentQuality - 50) * 0.003;

        // Tool quality bonus
        const toolBonus = this.calculateBlacksmithingToolBonus(crafter);
        baseChance += toolBonus * 0.05;

        return Math.max(0.1, Math.min(0.9, baseChance));
    }

    createAlloyMaterial(alloy, components, quality) {
        const materialQuality = quality || this.calculateAlloyQuality(components);

        return {
            id: this.generateMaterialId(),
            name: alloy.name,
            type: 'METAL',
            quality: materialQuality,
            properties: {
                ...alloy.properties,
                hardness: alloy.properties.hardness * (materialQuality / 100),
                durability: alloy.properties.durability * (materialQuality / 100)
            },
            quantity: this.calculateAlloyQuantity(components),
            value: this.calculateAlloyValue(alloy, materialQuality),
            alloy: true,
            composition: alloy.components
        };
    }

    generateRecipeId() {
        return 'bs_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    generateOrderId() {
        return 'order_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    generateMaterialId() {
        return 'alloy_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    // Additional helper methods
    calculateAverageComponentQuality(components) {
        if (!components || components.length === 0) return 50;
        return components.reduce((sum, comp) => sum + comp.quality, 0) / components.length;
    }

    calculateAlloyQuantity(components) {
        return Math.floor(components.reduce((sum, comp) => sum + comp.quantity, 0) * 0.9);
    }

    calculateAlloyValue(alloy, quality) {
        return Math.floor(alloy.benefits.damage * 100 * quality / 100);
    }

    updateAlloyStats(crafter, alloy) {
        crafter.stats = crafter.stats || {};
        crafter.stats.blacksmithing = crafter.stats.blacksmithing || {};
        crafter.stats.blacksmithing.alloysCreated = (crafter.stats.blacksmithing.alloysCreated || 0) + 1;
    }

    calculateAlloyExperience(alloy) {
        return Math.floor(alloy.requiredSkill * 2);
    }
}

module.exports = Blacksmithing;