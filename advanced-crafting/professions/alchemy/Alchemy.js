/**
 * Alchemy Profession
 * Handles potion brewing, elixir creation, and magical substance preparation
 */

class Alchemy {
    constructor(craftingSystem, materialSystem) {
        this.craftingSystem = craftingSystem;
        this.materialSystem = materialSystem;
        this.recipes = new Map();
        this.formulas = new Map();
        this.reagents = new Map();
        this.laboratories = new Map();
        this.transmutations = new Map();

        this.initializeProfession();
        this.loadRecipes();
        this.loadFormulas();
        this.loadReagents();
        this.loadTransmutations();
    }

    /**
     * Initialize Alchemy Profession
     */
    initializeProfession() {
        this.professionConfig = {
            name: 'Alchemy',
            description: 'Master the art of potion brewing and magical substance creation',
            primaryStats: ['intelligence', 'wisdom', 'dexterity'],
            tools: ['mortar_pestle', 'alembic', 'retort', 'crucible', 'flask'],
            stations: ['alchemy_lab', 'brewing_stand', 'distillery'],
            skillModifiers: {
                potionBrewing: 1.0,
                elixirCreation: 1.2,
                poisonCrafting: 0.9,
                transmutation: 1.5
            }
        };

        this.craftingSystem.professions.set('ALCHEMY', this.professionConfig);
    }

    /**
     * Potion Properties System
     */
    static get POTION_PROPERTIES() {
        return {
            HEALING: {
                basePower: 50,
                duration: 'instant',
                effects: ['restore_health'],
                color: '#ff6b6b',
                viscosity: 'medium'
            },
            MANA: {
                basePower: 40,
                duration: 'instant',
                effects: ['restore_mana'],
                color: '#4dabf7',
                viscosity: 'thin'
            },
            STRENGTH: {
                basePower: 25,
                duration: 'temporal',
                effects: ['increase_strength'],
                color: '#fa5252',
                viscosity: 'thick'
            },
            INVISIBILITY: {
                basePower: 100,
                duration: 'temporal',
                effects: ['invisibility'],
                color: '#868e96',
                viscosity: 'ethereal'
            },
            POISON: {
                basePower: 30,
                duration: 'damage_over_time',
                effects: ['damage_health', 'reduce_stats'],
                color: '#495057',
                viscosity: 'thin'
            },
            ANTIDOTE: {
                basePower: 80,
                duration: 'instant',
                effects: ['cure_poison', 'remove_debuffs'],
                color: '#69db7c',
                viscosity: 'medium'
            }
        };
    }

    /**
     * Load Alchemy Recipes
     */
    loadRecipes() {
        // Basic Potions
        this.addRecipe({
            id: 'healing_potion_minor',
            name: 'Minor Healing Potion',
            type: 'potion',
            tier: 'SIMPLE',
            requiredSkill: 15,
            materials: [
                { id: 'herb_healing', quantity: 2 },
                { id: 'water_pure', quantity: 1 },
                { id: 'crystal_dust', quantity: 1 }
            ],
            tools: ['mortar_pestle', 'flask'],
            station: 'brewing_stand',
            craftingTime: 20,
            experience: 30,
            baseProperties: {
                healAmount: 50,
                effectDuration: 0,
                stackSize: 5,
                toxicity: 5
            },
            potionProperties: 'HEALING'
        });

        this.addRecipe({
            id: 'mana_potion',
            name: 'Mana Potion',
            type: 'potion',
            tier: 'SIMPLE',
            requiredSkill: 20,
            materials: [
                { id: 'herb_mana', quantity: 3 },
                { id: 'water_arcane', quantity: 1 },
                { id: 'moonstone_fragment', quantity: 1 }
            ],
            tools: ['mortar_pestle', 'alembic', 'flask'],
            station: 'alchemy_lab',
            craftingTime: 30,
            experience: 35,
            baseProperties: {
                manaAmount: 60,
                effectDuration: 0,
                stackSize: 5,
                toxicity: 3
            },
            potionProperties: 'MANA'
        });

        // Advanced Elixirs
        this.addRecipe({
            id: 'elixir_giant_strength',
            name: 'Elixir of Giant Strength',
            type: 'elixir',
            tier: 'ADVANCED',
            requiredSkill: 180,
            materials: [
                { id: 'giant_toe', quantity: 1 },
                { id: 'dragon_blood', quantity: 2 },
                { id: 'mountain_herb', quantity: 3 },
                { id: 'fire_essence', quantity: 1 }
            ],
            tools: ['mortar_pestle', 'alembic', 'crucible', 'flask'],
            station: 'alchemy_lab',
            craftingTime: 120,
            experience: 200,
            baseProperties: {
                strengthBonus: 15,
                effectDuration: 3600, // 1 hour
                stackSize: 3,
                toxicity: 15
            },
            potionProperties: 'STRENGTH'
        });

        this.addRecipe({
            id: 'potion_invisibility',
            name: 'Potion of Invisibility',
            type: 'potion',
            tier: 'ADVANCED',
            requiredSkill: 250,
            materials: [
                { id: 'shadow_moss', quantity: 4 },
                { id: 'moon_petal', quantity: 2 },
                { id: 'phantom_dust', quantity: 1 },
                { id: 'still_water', quantity: 1 }
            ],
            tools: ['mortar_pestle', 'alembic', 'retort', 'flask'],
            station: 'distillery',
            craftingTime: 180,
            experience: 250,
            baseProperties: {
                invisibilityDuration: 300, // 5 minutes
                effectDuration: 300,
                stackSize: 2,
                toxicity: 20
            },
            potionProperties: 'INVISIBILITY'
        });

        // Master Level Potions
        this.addRecipe({
            id: 'philosophers_stone',
            name: 'Philosopher\'s Stone',
            type: 'artifact',
            tier: 'MASTER',
            requiredSkill: 500,
            materials: [
                { id: 'prime_matter', quantity: 1 },
                { id: 'quintessence', quantity: 1 },
                { id: 'dragon_heart', quantity: 1 },
                { id: 'phoenix_tear', quantity: 3 },
                { id: 'universal_solvent', quantity: 1 }
            ],
            tools: ['mystical_alembic', 'golden_crucible'],
            station: 'grand_laboratory',
            craftingTime: 2880, // 48 hours
            experience: 1500,
            baseProperties: {
                transmutationPower: 1000,
                creationPower: 500,
                purificationPower: 800,
                stackSize: 1,
                toxicity: 0,
                legendary: true
            },
            specialEffects: ['transmutation', 'life_extension', 'purification'],
            questRequirements: [
                'master_alchemical_theory',
                'gather_legendary_components',
                'solve_riddle_of_elements'
            ]
        });

        // Poisons
        this.addRecipe({
            id: 'poison_deadly',
            name: 'Deadly Poison',
            type: 'poison',
            tier: 'ADVANCED',
            requiredSkill: 200,
            materials: [
                { id: 'death_cap', quantity: 3 },
                { id: 'spider_venom', quantity: 2 },
                { id: 'nightshade', quantity: 1 },
                { id: 'acid_gland', quantity: 1 }
            ],
            tools: ['mortar_pestle', 'retort', 'vial'],
            station: 'poison_lab',
            craftingTime: 90,
            experience: 180,
            baseProperties: {
                damagePerSecond: 25,
                effectDuration: 60,
                stackSize: 3,
                toxicity: 80
            },
            potionProperties: 'POISON'
        });

        // Experimental Formulas
        this.addRecipe({
            id: 'potion_mutation',
            name: 'Experimental Mutation Potion',
            type: 'experimental',
            tier: 'MASTER',
            requiredSkill: 450,
            materials: [
                { id: 'mutagen', quantity: 1 },
                { id: 'chimera_blood', quantity: 2 },
                { id: 'chaos_essence', quantity: 1 },
                { id: 'random_herb', quantity: 3 }
            ],
            tools: ['experimental_apparatus', 'safety_gear'],
            station: 'experimental_lab',
            craftingTime: 300,
            experience: 400,
            baseProperties: {
                randomEffect: true,
                effectDuration: 'variable',
                stackSize: 1,
                toxicity: 95,
                unpredictable: true
            },
            specialEffects: ['random_mutation', 'chaotic_magic']
        });
    }

    /**
     * Advanced Alchemical Formulas
     */
    loadFormulas() {
        this.formulas.set('ELEMENTAL_SYNERGY', {
            name: 'Elemental Synergy Formula',
            description: 'Combine elemental essences for amplified effects',
            requiredSkill: 300,
            complexity: 8,
            unstable: true,
            benefits: {
                effectPower: 2.0,
                durationMultiplier: 1.5,
                specialEffects: ['elemental_resonance']
            },
            risks: {
                explosionChance: 0.15,
                corruptionChance: 0.10,
                backfireChance: 0.20
            }
        });

        this.formulas.set('TIME_DISTILLATION', {
            name: 'Time Distillation Process',
            description: 'Distill temporal properties for extended duration effects',
            requiredSkill: 400,
            complexity: 10,
            unstable: false,
            benefits: {
                durationMultiplier: 3.0,
                effectPower: 1.2,
                specialEffects: ['time dilation']
            },
            risks: {
                agingEffect: 0.05,
                paradoxChance: 0.02
            }
        });

        this.formulas.set('SOUL_EXTRACTION', {
            name: 'Soul Extraction Formula',
            description: 'Extract soul essence for powerful enchantments',
            requiredSkill: 600,
            complexity: 12,
            unstable: true,
            benefits: {
                effectPower: 3.0,
                soulBound: true,
                specialEffects: ['sentient_potion', 'spirit_bind']
            },
            risks: {
                soulCorruption: 0.25,
                hauntings: 0.15,
                curseChance: 0.30
            }
        });
    }

    /**
     * Custom Potion Brewing
     */
    async brewCustomPotion(alchemistId, formula, reagents, modifications = {}) {
        const alchemist = this.craftingSystem.getCrafter(alchemistId);

        if (!alchemist) {
            throw new Error('Invalid alchemist');
        }

        // Validate formula
        const formulaData = this.formulas.get(formula);
        if (!formulaData) {
            throw new Error('Invalid formula');
        }

        if (alchemist.skills.ALCHEMY < formulaData.requiredSkill) {
            throw new Error('Insufficient skill for formula');
        }

        // Validate reagents
        const reagentValidation = this.validateReagents(reagents, formula);
        if (!reagentValidation.valid) {
            throw new Error(`Reagent validation failed: ${reagentValidation.reason}`);
        }

        // Calculate brewing success
        const successChance = this.calculateBrewingSuccess(alchemist, formulaData, reagents, modifications);

        if (Math.random() < successChance) {
            // Brew the potion
            const potion = await this.performCustomBrewing(formulaData, reagents, modifications);

            // Update alchemist statistics
            this.updateAlchemistStats(alchemist, 'custom_brewing', 1);

            return {
                success: true,
                potion: potion,
                experience: this.calculateBrewingExperience(formulaData),
                sideEffects: this.calculateSideEffects(formulaData, modifications)
            };
        }

        // Handle brewing failure
        const failure = this.handleBrewingFailure(formulaData, reagents);

        return {
            success: false,
            failure: failure,
            experience: Math.floor(this.calculateBrewingExperience(formulaData) * 0.3)
        };
    }

    /**
     * Potion Refinement and Enhancement
     */
    async refinePotion(alchemistId, potionId, refinementType, catalysts) {
        const alchemist = this.craftingSystem.getCrafter(alchemistId);
        const potion = this.getPotion(potionId); // Integrate with inventory system

        if (!alchemist || !potion) {
            throw new Error('Invalid alchemist or potion');
        }

        const refinement = this.getRefinementProcess(refinementType);
        if (!refinement) {
            throw new Error('Invalid refinement type');
        }

        // Validate requirements
        const validation = this.validateRefinementRequirements(alchemist, potion, refinement, catalysts);
        if (!validation.valid) {
            throw new Error(`Refinement validation failed: ${validation.reason}`);
        }

        // Perform refinement
        const result = await this.performRefinement(potion, refinement, catalysts);

        return result;
    }

    /**
     * Transmutation System
     */
    async performTransmutation(alchemistId, targetMaterial, catalyst, transmutationCircle) {
        const alchemist = this.craftingSystem.getCrafter(alchemistId);

        if (!alchemist) {
            throw new Error('Invalid alchemist');
        }

        const transmutation = this.transmutations.get(targetMaterial.type);
        if (!transmutation) {
            throw new Error('Material cannot be transmuted');
        }

        // Validate transmutation circle
        if (!this.validateTransmutationCircle(transmutationCircle, transmutation)) {
            throw new Error('Invalid transmutation circle');
        }

        // Calculate transmutation success
        const successChance = this.calculateTransmutationSuccess(alchemist, targetMaterial, catalyst, transmutation);

        if (Math.random() < successChance) {
            // Perform transmutation
            const transmutedMaterial = await this.executeTransmutation(targetMaterial, catalyst, transmutation);

            // Update alchemist stats
            this.updateAlchemistStats(alchemist, 'transmutations', 1);

            return {
                success: true,
                originalMaterial: targetMaterial,
                transmutedMaterial: transmutedMaterial,
                experience: this.calculateTransmutationExperience(transmutation)
            };
        }

        return {
            success: false,
            failure: this.handleTransmutationFailure(targetMaterial, transmutation),
            experience: Math.floor(this.calculateTransmutationExperience(transmutation) * 0.2)
        };
    }

    /**
     * Mass Production and Distribution
     */
    async setupMassProduction(alchemistId, productionPlan) {
        const alchemist = this.craftingSystem.getCrafter(alchemistId);

        if (!alchemist) {
            throw new Error('Invalid alchemist');
        }

        const massProduction = {
            id: this.generateProductionId(),
            alchemistId: alchemistId,
            plan: productionPlan,
            status: 'setup',
            efficiency: this.calculateProductionEfficiency(alchemist, productionPlan),
            qualityControl: this.setupQualityControl(alchemist, productionPlan),
            createdAt: new Date().toISOString()
        };

        // Calculate required materials and time
        massProduction.totalMaterials = this.calculateTotalMaterials(productionPlan);
        massProduction.estimatedTime = this.calculateProductionTime(productionPlan, massProduction.efficiency);
        massProduction.costAnalysis = this.analyzeProductionCosts(productionPlan);

        return massProduction;
    }

    /**
     * Alchemical Research and Discovery
     */
    async conductResearch(alchemistId, researchTopic, resources, hypothesis) {
        const alchemist = this.craftingSystem.getCrafter(alchemistId);

        if (!alchemist) {
            throw new Error('Invalid alchemist');
        }

        const research = {
            id: this.generateResearchId(),
            alchemistId: alchemistId,
            topic: researchTopic,
            hypothesis: hypothesis,
            resources: resources,
            progress: 0,
            discoveries: [],
            status: 'in_progress',
            startedAt: new Date().toISOString()
        };

        // Calculate research success probability
        const successChance = this.calculateResearchSuccess(alchemist, researchTopic, resources);

        // Simulate research process
        const researchResult = await this.simulateResearch(research, successChance);

        return researchResult;
    }

    /**
     * Utility Methods
     */
    addRecipe(recipeData) {
        const recipe = {
            ...recipeData,
            profession: 'ALCHEMY',
            id: recipeData.id || this.generateRecipeId()
        };

        this.recipes.set(recipe.id, recipe);
        this.craftingSystem.recipes.set(recipe.id, recipe);
    }

    getRecipe(recipeId) {
        return this.recipes.get(recipeId);
    }

    calculateBrewingSuccess(alchemist, formula, reagents, modifications) {
        let baseChance = 0.4;

        // Skill influence
        const skillBonus = Math.min((alchemist.skills.ALCHEMY - formula.requiredSkill) / 100, 1) * 0.3;
        baseChance += skillBonus;

        // Reagent quality influence
        const reagentQuality = this.calculateAverageReagentQuality(reagents);
        baseChance += (reagentQuality - 50) * 0.004;

        // Laboratory bonuses
        const labBonus = this.getLaboratoryBonus(alchemist);
        baseChance += labBonus * 0.1;

        // Formula complexity penalty
        baseChance -= formula.complexity * 0.02;

        // Stability penalty
        if (formula.unstable) {
            baseChance -= 0.1;
        }

        // Modification risks
        if (modifications.risky) {
            baseChance -= 0.15;
        }

        return Math.max(0.05, Math.min(0.95, baseChance));
    }

    performCustomBrewing(formula, reagents, modifications) {
        const basePower = this.calculateBasePower(reagents);
        const quality = this.calculatePotionQuality(formula, reagents);

        let potion = {
            id: this.generatePotionId(),
            name: this.generatePotionName(formula, modifications),
            type: 'custom_potion',
            quality: quality,
            effects: this.generatePotionEffects(formula, reagents, modifications),
            duration: this.calculatePotionDuration(formula, quality),
            toxicity: this.calculateToxicity(formula, reagents, modifications),
            stackSize: this.calculateStackSize(formula, quality),
            value: this.calculatePotionValue(formula, quality),
            properties: {
                unstable: formula.unstable,
                complexity: formula.complexity,
                custom: true
            }
        };

        // Apply special effects from formula
        if (formula.benefits.specialEffects) {
            potion.specialEffects = [...formula.benefits.specialEffects];
        }

        // Apply modifications
        if (modifications.enhancements) {
            potion = this.applyModifications(potion, modifications);
        }

        return potion;
    }

    handleBrewingFailure(formula, reagents) {
        const failureTypes = ['explosion', 'corruption', 'mutation', 'waste', 'backfire'];
        const failureType = failureTypes[Math.floor(Math.random() * failureTypes.length)];

        const failure = {
            type: failureType,
            severity: this.calculateFailureSeverity(formula),
            consequences: this.generateFailureConsequences(failureType, formula),
            lostMaterials: this.calculateLostMaterials(reagents, failureType)
        };

        return failure;
    }

    generateRecipeId() {
        return 'alc_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    generatePotionId() {
        return 'pot_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    generateProductionId() {
        return 'prod_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    generateResearchId() {
        return 'res_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    // Additional helper methods
    calculateAverageReagentQuality(reagents) {
        if (!reagents || reagents.length === 0) return 50;
        return reagents.reduce((sum, reg) => sum + reg.quality, 0) / reagents.length;
    }

    calculateBasePower(reagents) {
        return reagents.reduce((sum, reg) => sum + (reg.power || reg.quality), 0);
    }

    calculatePotionQuality(formula, reagents) {
        const baseQuality = this.calculateAverageReagentQuality(reagents);
        const complexityModifier = (100 - formula.complexity * 2) / 100;
        return Math.floor(baseQuality * complexityModifier);
    }

    updateAlchemistStats(alchemist, activity, amount) {
        alchemist.stats = alchemist.stats || {};
        alchemist.stats.alchemy = alchemist.stats.alchemy || {};
        alchemist.stats.alchemy[activity] = (alchemist.stats.alchemy[activity] || 0) + amount;
    }

    calculateBrewingExperience(formula) {
        return Math.floor(formula.requiredSkill * 1.5 + formula.complexity * 20);
    }
}

module.exports = Alchemy;