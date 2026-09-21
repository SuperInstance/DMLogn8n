/**
 * Advanced Crafting System - Main Entry Point
 * Integrates all crafting modules and provides unified API
 */

const CraftingSystem = require('./core/CraftingSystem');
const MaterialSystem = require('./materials/MaterialSystem');
const SocialFeatures = require('./core/SocialFeatures');
const CraftingConfig = require('./config/crafting-config');

// Import professions
const Blacksmithing = require('./professions/blacksmithing/Blacksmithing');
const Alchemy = require('./professions/alchemy/Alchemy');

class AdvancedCraftingSystem {
    constructor(config = {}) {
        // Merge configuration with defaults
        this.config = { ...CraftingConfig, ...config };

        // Initialize core systems
        this.craftingSystem = new CraftingSystem(this.config.system);
        this.materialSystem = new MaterialSystem(this.craftingSystem);
        this.socialFeatures = new SocialFeatures(this.craftingSystem, this.materialSystem);

        // Initialize professions
        this.professions = new Map();
        this.initializeProfessions();

        // Setup event handlers
        this.setupEventHandlers();

        // Initialize integrations
        this.initializeIntegrations();

        console.log('Advanced Crafting System initialized successfully');
    }

    /**
     * Initialize Crafting Professions
     */
    initializeProfessions() {
        // Core professions
        this.professions.set('BLACKSMITHING', new Blacksmithing(this.craftingSystem, this.materialSystem));
        this.professions.set('ALCHEMY', new Alchemy(this.craftingSystem, this.materialSystem));

        // Additional professions would be initialized here
        // this.professions.set('ENCHANTING', new Enchanting(this.craftingSystem, this.materialSystem));
        // this.professions.set('TAILORING', new Tailoring(this.craftingSystem, this.materialSystem));
        // this.professions.set('JEWELCRAFTING', new Jewelcrafting(this.craftingSystem, this.materialSystem));
        // this.professions.set('WOODWORKING', new Woodworking(this.craftingSystem, this.materialSystem));
        // this.professions.set('COOKING', new Cooking(this.craftingSystem, this.materialSystem));
        // this.professions.set('INSCRIPTION', new Inscription(this.craftingSystem, this.materialSystem));
    }

    /**
     * Setup Event Handlers
     */
    setupEventHandlers() {
        // Crafting events
        this.craftingSystem.on('craftingCompleted', (data) => {
            this.handleCraftingCompleted(data);
        });

        this.craftingSystem.on('skillLevelUp', (data) => {
            this.handleSkillLevelUp(data);
        });

        this.craftingSystem.on('materialDecay', (data) => {
            this.handleMaterialDecay(data);
        });

        // Social events
        this.socialFeatures.on('orderCreated', (data) => {
            this.handleOrderCreated(data);
        });

        this.socialFeatures.on('competitionStarted', (data) => {
            this.handleCompetitionStarted(data);
        });

        // Material events
        this.materialSystem.on('materialHarvested', (data) => {
            this.handleMaterialHarvested(data);
        });

        this.materialSystem.on('materialProcessed', (data) => {
            this.handleMaterialProcessed(data);
        });
    }

    /**
     * Initialize External Integrations
     */
    initializeIntegrations() {
        if (this.config.integration.n8n.enabled) {
            this.initializeN8nIntegration();
        }

        if (this.config.integration.database.enabled) {
            this.initializeDatabaseIntegration();
        }

        if (this.config.integration.inventory.enabled) {
            this.initializeInventoryIntegration();
        }

        if (this.config.integration.notifications.enabled) {
            this.initializeNotificationSystem();
        }
    }

    /**
     * Main Crafting API Methods
     */

    // Individual Crafting
    async craftItem(crafterId, recipeId, materials, options = {}) {
        try {
            const result = await this.craftingSystem.craftItem(crafterId, recipeId, materials, options);

            // Log crafting activity
            await this.logActivity('crafting', 'item_crafted', {
                crafterId,
                recipeId,
                success: result.success,
                quality: result.quality,
                timestamp: new Date().toISOString()
            });

            return result;
        } catch (error) {
            console.error('Crafting error:', error);
            throw error;
        }
    }

    // Material Harvesting
    async harvestMaterial(harvesterId, location, materialType, toolId, skill) {
        try {
            const result = await this.materialSystem.harvestMaterial(harvesterId, location, materialType, toolId, skill);

            await this.logActivity('harvesting', 'material_harvested', {
                harvesterId,
                location,
                materialType,
                success: result.success,
                quantity: result.materials ? result.materials.length : 0,
                timestamp: new Date().toISOString()
            });

            return result;
        } catch (error) {
            console.error('Harvesting error:', error);
            throw error;
        }
    }

    // Create Crafting Order
    async createCraftingOrder(clientId, orderDetails) {
        try {
            const order = await this.socialFeatures.createCraftingOrder(clientId, orderDetails);

            await this.logActivity('social', 'order_created', {
                clientId,
                orderId: order.id,
                itemCount: order.specifications.items.length,
                timestamp: new Date().toISOString()
            });

            return order;
        } catch (error) {
            console.error('Order creation error:', error);
            throw error;
        }
    }

    // Guild Workshop Management
    async createGuildWorkshop(guildId, workshopDetails) {
        try {
            const workshop = await this.socialFeatures.createGuildWorkshop(guildId, workshopDetails);

            await this.logActivity('social', 'workshop_created', {
                guildId,
                workshopId: workshop.id,
                workshopType: workshop.type,
                timestamp: new Date().toISOString()
            });

            return workshop;
        } catch (error) {
            console.error('Workshop creation error:', error);
            throw error;
        }
    }

    // Competition Management
    async createCompetition(organizerId, competitionDetails) {
        try {
            const competition = await this.socialFeatures.createCompetition(organizerId, competitionDetails);

            await this.logActivity('social', 'competition_created', {
                organizerId,
                competitionId: competition.id,
                competitionType: competition.type,
                timestamp: new Date().toISOString()
            });

            return competition;
        } catch (error) {
            console.error('Competition creation error:', error);
            throw error;
        }
    }

    // Master-Apprentice System
    async createApprenticeship(masterId, apprenticeId, terms) {
        try {
            const apprenticeship = await this.socialFeatures.createApprenticeship(masterId, apprenticeId, terms);

            await this.logActivity('social', 'apprenticeship_created', {
                masterId,
                apprenticeId,
                apprenticeshipId: apprenticeship.id,
                duration: terms.duration,
                timestamp: new Date().toISOString()
            });

            return apprenticeship;
        } catch (error) {
            console.error('Apprenticeship creation error:', error);
            throw error;
        }
    }

    // Custom Profession Methods
    async craftWithTechnique(crafterId, profession, recipeId, materials, techniqueIds, options = {}) {
        const professionInstance = this.professions.get(profession.toUpperCase());
        if (!professionInstance) {
            throw new Error(`Profession ${profession} not found`);
        }

        if (professionInstance.craftWithTechnique) {
            return await professionInstance.craftWithTechnique(crafterId, recipeId, materials, techniqueIds, options);
        } else {
            // Fallback to regular crafting
            return await this.craftItem(crafterId, recipeId, materials, options);
        }
    }

    async brewCustomPotion(alchemistId, formula, reagents, modifications = {}) {
        const alchemy = this.professions.get('ALCHEMY');
        if (!alchemy) {
            throw new Error('Alchemy profession not available');
        }

        return await alchemy.brewCustomPotion(alchemistId, formula, reagents, modifications);
    }

    async createAlloy(crafterId, alloyId, components, quality = null) {
        const blacksmithing = this.professions.get('BLACKSMITHING');
        if (!blacksmithing) {
            throw new Error('Blacksmithing profession not available');
        }

        return await blacksmithing.createAlloy(crafterId, alloyId, components, quality);
    }

    /**
     * Query and Analytics Methods
     */

    // Get Crafter Statistics
    getCrafterStats(crafterId) {
        const crafter = this.craftingSystem.getCrafter(crafterId);
        if (!crafter) {
            throw new Error('Crafter not found');
        }

        const reputation = this.socialFeatures.reputations.get(crafterId) || { overall: 5.0 };
        const materials = Array.from(this.materialSystem.materials.values()).filter(m => m.harvestedBy === crafterId);

        return {
            crafter: crafter,
            reputation: reputation,
            materials: {
                count: materials.length,
                totalValue: materials.reduce((sum, m) => sum + m.value, 0),
                averageQuality: materials.length > 0 ? materials.reduce((sum, m) => sum + m.quality, 0) / materials.length : 0
            },
            stats: crafter.stats || {},
            skills: crafter.skills || {}
        };
    }

    // Get Market Analytics
    getMarketAnalytics() {
        const orders = Array.from(this.socialFeatures.craftingOrders.values());
        const listings = Array.from(this.socialFeatures.marketplace.values());
        const materials = Array.from(this.materialSystem.materials.values());

        return {
            orders: {
                total: orders.length,
                active: orders.filter(o => o.status === 'open').length,
                inProgress: orders.filter(o => o.status === 'in_progress').length,
                completed: orders.filter(o => o.status === 'completed').length,
                averageValue: orders.length > 0 ? orders.reduce((sum, o) => sum + o.payment.amount, 0) / orders.length : 0
            },
            marketplace: {
                activeListings: listings.filter(l => l.status === 'active').length,
                totalValue: listings.reduce((sum, l) => sum + (l.pricing.currentBid || l.pricing.startingPrice), 0),
                averagePrice: listings.length > 0 ? listings.reduce((sum, l) => sum + (l.pricing.currentBid || l.pricing.startingPrice), 0) / listings.length : 0
            },
            materials: {
                total: materials.length,
                averageQuality: materials.length > 0 ? materials.reduce((sum, m) => sum + m.quality, 0) / materials.length : 0,
                totalValue: materials.reduce((sum, m) => sum + m.value, 0),
                byType: this.groupMaterialsByType(materials)
            }
        };
    }

    // Get Competition Leaderboard
    getCompetitionLeaderboard(competitionId) {
        const competition = this.socialFeatures.competitions.get(competitionId);
        if (!competition) {
            throw new Error('Competition not found');
        }

        const submissions = Object.values(competition.submissions);
        const leaderboard = submissions
            .filter(s => s.finalScore !== null)
            .sort((a, b) => b.finalScore - a.finalScore)
            .map((submission, index) => ({
                rank: index + 1,
                participantId: submission.participantId,
                score: submission.finalScore,
                submissionTime: submission.submittedAt
            }));

        return {
            competition: competition,
            leaderboard: leaderboard,
            totalParticipants: competition.participants.length,
            totalSubmissions: submissions.length
        };
    }

    /**
     * Event Handlers
     */
    handleCraftingCompleted(data) {
        // Update statistics, achievements, etc.
        console.log(`Crafting completed for crafter ${data.crafterId}: ${data.success ? 'SUCCESS' : 'FAILURE'}`);

        if (this.config.integration.notifications.enabled) {
            this.sendNotification(data.crafterId, 'crafting_completed', data);
        }
    }

    handleSkillLevelUp(data) {
        console.log(`Skill level up: ${data.crafterId} - ${data.profession} - Level ${data.newLevel}`);

        // Award achievements, unlock new recipes, etc.
        this.unlockRecipesForSkillLevel(data.crafterId, data.profession, data.newLevel);
    }

    handleMaterialDecay(data) {
        console.log(`Material decay: ${data.materialId} - Durability: ${data.durability}`);

        // Notify crafter if material is about to be completely decayed
        if (data.durability < 20) {
            const material = this.materialSystem.materials.get(data.materialId);
            if (material && material.harvestedBy) {
                this.sendNotification(material.harvestedBy, 'material_decay_warning', data);
            }
        }
    }

    handleOrderCreated(data) {
        console.log(`New crafting order created: ${data.orderId}`);

        // Notify potential crafters based on their skills and reputation
        this.notifyPotentialCraftersForOrder(data);
    }

    handleCompetitionStarted(data) {
        console.log(`Competition started: ${data.competitionId}`);

        // Broadcast competition announcement
        this.broadcastCompetition(data);
    }

    handleMaterialHarvested(data) {
        console.log(`Material harvested: ${data.materials.length} items by ${data.harvesterId}`);

        // Update harvester statistics
        this.updateHarvestingStatistics(data);
    }

    handleMaterialProcessed(data) {
        console.log(`Material processed: ${data.processedMaterial.id}`);

        // Update processor statistics
        this.updateProcessingStatistics(data);
    }

    /**
     * Utility Methods
     */
    groupMaterialsByType(materials) {
        const grouped = {};
        materials.forEach(material => {
            if (!grouped[material.type]) {
                grouped[material.type] = { count: 0, totalValue: 0, averageQuality: 0 };
            }
            grouped[material.type].count++;
            grouped[material.type].totalValue += material.value;
        });

        // Calculate averages
        Object.keys(grouped).forEach(type => {
            const typeMaterials = materials.filter(m => m.type === type);
            grouped[type].averageQuality = typeMaterials.reduce((sum, m) => sum + m.quality, 0) / typeMaterials.length;
        });

        return grouped;
    }

    async logActivity(category, action, data) {
        if (this.config.debugging.enabled) {
            console.log(`Activity logged: [${category}] ${action}`, data);
        }

        // Here you would log to database or external service
        // await this.database.logActivity({ category, action, data, timestamp: new Date() });
    }

    sendNotification(userId, type, data) {
        if (this.config.integration.notifications.enabled) {
            // Implementation would depend on notification system
            console.log(`Notification sent to ${userId}: ${type}`, data);
        }
    }

    initializeN8nIntegration() {
        console.log('N8n integration initialized');
        // Set up webhooks and workflows
    }

    initializeDatabaseIntegration() {
        console.log('Database integration initialized');
        // Connect to database and setup collections
    }

    initializeInventoryIntegration() {
        console.log('Inventory integration initialized');
        // Setup inventory system connections
    }

    initializeNotificationSystem() {
        console.log('Notification system initialized');
        // Setup notification channels and handlers
    }

    // Additional helper methods would be implemented here
    unlockRecipesForSkillLevel(crafterId, profession, level) {
        console.log(`Unlocking recipes for ${crafterId} in ${profession} at level ${level}`);
    }

    notifyPotentialCraftersForOrder(order) {
        console.log(`Notifying potential crafters for order ${order.id}`);
    }

    broadcastCompetition(competition) {
        console.log(`Broadcasting competition ${competition.id}`);
    }

    updateHarvestingStatistics(data) {
        console.log(`Updating harvesting statistics for ${data.harvesterId}`);
    }

    updateProcessingStatistics(data) {
        console.log(`Updating processing statistics for ${data.processorId}`);
    }
}

module.exports = AdvancedCraftingSystem;

// Export individual modules for advanced usage
module.exports.CraftingSystem = CraftingSystem;
module.exports.MaterialSystem = MaterialSystem;
module.exports.SocialFeatures = SocialFeatures;
module.exports.CraftingConfig = CraftingConfig;