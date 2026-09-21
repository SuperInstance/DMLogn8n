/**
 * Advanced Material System
 * Handles material properties, quality, harvesting, and decay mechanics
 */

class MaterialSystem {
    constructor(craftingSystem) {
        this.craftingSystem = craftingSystem;
        this.materials = new Map();
        this.materialTypes = new Map();
        this.harvestingZones = new Map();
        this.decayTimers = new Map();

        this.initializeMaterialTypes();
        this.initializeHarvestingSystem();
        this.setupDecaySystem();
    }

    /**
     * Material Quality Tiers
     */
    static get QUALITY_TIERS() {
        return {
            COMMON: { min: 1, max: 40, color: '#808080', name: 'Common' },
            UNCOMMON: { min: 41, max: 60, color: '#00ff00', name: 'Uncommon' },
            RARE: { min: 61, max: 75, color: '#0080ff', name: 'Rare' },
            EPIC: { min: 76, max: 90, color: '#8000ff', name: 'Epic' },
            LEGENDARY: { min: 91, max: 100, color: '#ff8000', name: 'Legendary' }
        };
    }

    /**
     * Initialize Material Types
     */
    initializeMaterialTypes() {
        this.materialTypes.set('METAL', {
            name: 'Metal',
            properties: ['hardness', 'malleability', 'conductivity', 'weight'],
            decayRate: 0.05,
            storageRequirements: ['dry', 'cool'],
            processable: true
        });

        this.materialTypes.set('HERB', {
            name: 'Herb',
            properties: ['potency', 'freshness', 'rarity', 'magical_affinity'],
            decayRate: 0.15,
            storageRequirements: ['cool', 'dark'],
            processable: true
        });

        this.materialTypes.set('GEM', {
            name: 'Gem',
            properties: ['clarity', 'hardness', 'magical_resonance', 'size'],
            decayRate: 0.01,
            storageRequirements: ['dry', 'stable'],
            processable: false
        });

        this.materialTypes.set('WOOD', {
            name: 'Wood',
            properties: ['density', 'flexibility', 'grain_quality', 'age'],
            decayRate: 0.08,
            storageRequirements: ['dry', 'ventilated'],
            processable: true
        });

        this.materialTypes.set('LEATHER', {
            name: 'Leather',
            properties: ['thickness', 'flexibility', 'durability', 'tanning_quality'],
            decayRate: 0.06,
            storageRequirements: ['dry', 'cool'],
            processable: true
        });

        this.materialTypes.set('CLOTH', {
            name: 'Cloth',
            properties: ['thread_count', 'softness', 'durability', 'weave_quality'],
            decayRate: 0.04,
            storageRequirements: ['dry', 'cool'],
            processable: true
        });

        this.materialTypes.set('MAGICAL', {
            name: 'Magical',
            properties: ['power', 'stability', 'affinity', 'purity'],
            decayRate: 0.12,
            storageRequirements: ['magical_ward', 'stable'],
            processable: false
        });

        this.materialTypes.set('FOOD', {
            name: 'Food',
            properties: ['freshness', 'nutrition', 'flavor', 'rarity'],
            decayRate: 0.25,
            storageRequirements: ['cool', 'sealed'],
            processable: true
        });
    }

    /**
     * Create New Material
     */
    createMaterial(materialData) {
        const material = {
            id: this.generateMaterialId(),
            name: materialData.name,
            type: materialData.type,
            quality: materialData.quality || this.calculateInitialQuality(materialData),
            properties: this.generateMaterialProperties(materialData),
            quantity: materialData.quantity || 1,
            stackSize: materialData.stackSize || this.getDefaultStackSize(materialData.type),
            harvestedAt: new Date().toISOString(),
            harvestedBy: materialData.harvestedBy,
            location: materialData.location,
            durability: 100,
            value: this.calculateMaterialValue(materialData),
            storageRequirements: this.getStorageRequirements(materialData.type),
            processable: this.isProcessable(materialData.type),
            specialEffects: materialData.specialEffects || [],
            tags: materialData.tags || []
        };

        this.materials.set(material.id, material);
        this.setupDecayTimer(material);

        return material;
    }

    /**
     * Calculate Initial Material Quality
     */
    calculateInitialQuality(materialData) {
        let baseQuality = 50;

        // Location-based quality modifier
        if (materialData.location) {
            const location = this.harvestingZones.get(materialData.location);
            if (location) {
                baseQuality += location.qualityModifier || 0;
            }
        }

        // Harvester skill influence
        if (materialData.harvestedBy && materialData.harvestingSkill) {
            const skillBonus = Math.min(materialData.harvestingSkill / 100, 2) * 15;
            baseQuality += skillBonus;
        }

        // Tool quality influence
        if (materialData.toolQuality) {
            const toolBonus = (materialData.toolQuality - 50) * 0.3;
            baseQuality += toolBonus;
        }

        // Random variation
        baseQuality += (Math.random() - 0.5) * 30;

        // Rarity chance
        const rarityRoll = Math.random();
        if (rarityRoll < 0.01) { // 1% chance for legendary
            baseQuality += 30;
        } else if (rarityRoll < 0.05) { // 4% chance for epic
            baseQuality += 20;
        } else if (rarityRoll < 0.15) { // 10% chance for rare
            baseQuality += 10;
        }

        return Math.max(1, Math.min(100, Math.floor(baseQuality)));
    }

    /**
     * Generate Material Properties
     */
    generateMaterialProperties(materialData) {
        const materialType = this.materialTypes.get(materialData.type);
        if (!materialType) return {};

        const properties = {};

        materialType.properties.forEach(prop => {
            let baseValue = 50;

            // Quality influence on properties
            const qualityInfluence = (materialData.quality - 50) * 0.8;
            baseValue += qualityInfluence;

            // Random variation
            baseValue += (Math.random() - 0.5) * 20;

            properties[prop] = Math.max(1, Math.min(100, Math.floor(baseValue)));
        });

        return properties;
    }

    /**
     * Harvesting System
     */
    async harvestMaterial(harvesterId, location, materialType, toolId, harvestingSkill) {
        const harvester = this.craftingSystem.getCrafter(harvesterId);
        const zone = this.harvestingZones.get(location);

        if (!harvester || !zone) {
            throw new Error('Invalid harvester or location');
        }

        // Check if material type is available in this zone
        if (!zone.availableMaterials.includes(materialType)) {
            throw new Error(`${materialType} not available in ${location}`);
        }

        // Calculate harvesting success chance
        const successChance = this.calculateHarvestingSuccess(harvester, zone, materialType, toolId, harvestingSkill);

        if (Math.random() < successChance) {
            // Determine quantity harvested
            const quantity = this.calculateHarvestQuantity(harvester, zone, materialType, toolId);

            // Create harvested materials
            const harvestedMaterials = [];
            for (let i = 0; i < quantity; i++) {
                const materialData = {
                    name: this.generateMaterialName(materialType, location),
                    type: materialType,
                    quality: null, // Will be calculated in createMaterial
                    harvestedBy: harvesterId,
                    location: location,
                    harvestingSkill: harvestingSkill,
                    toolQuality: toolId ? this.getToolQuality(toolId) : 50
                };

                const material = this.createMaterial(materialData);
                harvestedMaterials.push(material);
            }

            // Update harvester statistics
            this.updateHarvestingStats(harvester, materialType, quantity);

            return {
                success: true,
                materials: harvestedMaterials,
                experience: this.calculateHarvestingExperience(zone, materialType, quantity)
            };
        }

        return {
            success: false,
            experience: Math.floor(this.calculateHarvestingExperience(zone, materialType, 1) * 0.2)
        };
    }

    /**
     * Calculate Harvesting Success Chance
     */
    calculateHarvestingSuccess(harvester, zone, materialType, toolId, skill) {
        let baseChance = 0.3; // 30% base chance

        // Zone difficulty modifier
        baseChance += (zone.difficultyModifier || 0);

        // Skill influence
        const skillBonus = Math.min(skill / 100, 2) * 0.3;
        baseChance += skillBonus;

        // Tool quality influence
        if (toolId) {
            const toolQuality = this.getToolQuality(toolId);
            baseChance += (toolQuality - 50) * 0.004;
        }

        // Material rarity modifier
        const materialRarity = this.getMaterialRarity(materialType);
        baseChance -= materialRarity * 0.1;

        // Environmental conditions
        baseChance += this.calculateEnvironmentalBonus(zone, materialType);

        return Math.max(0.05, Math.min(0.95, baseChance));
    }

    /**
     * Material Processing
     */
    async processMaterial(processorId, materialId, processType, targetQuality) {
        const processor = this.craftingSystem.getCrafter(processorId);
        const material = this.materials.get(materialId);

        if (!processor || !material) {
            throw new Error('Invalid processor or material');
        }

        if (!material.processable) {
            throw new Error('Material cannot be processed');
        }

        // Check processing requirements
        const requirements = this.getProcessingRequirements(processType);
        if (!this.validateProcessingRequirements(processor, requirements)) {
            throw new Error('Processing requirements not met');
        }

        // Calculate success chance
        const successChance = this.calculateProcessingSuccess(processor, material, processType, targetQuality);

        if (Math.random() < successChance) {
            // Process the material
            const processedMaterial = await this.performMaterialProcessing(material, processType, targetQuality);

            // Update processor statistics
            this.updateProcessingStats(processor, processType);

            return {
                success: true,
                originalMaterial: material,
                processedMaterial: processedMaterial,
                experience: this.calculateProcessingExperience(processType, material.quality)
            };
        }

        return {
            success: false,
            originalMaterial: material,
            experience: Math.floor(this.calculateProcessingExperience(processType, material.quality) * 0.3)
        };
    }

    /**
     * Decay System
     */
    setupDecaySystem() {
        // Set up periodic decay checks
        setInterval(() => {
            this.checkMaterialDecay();
        }, 60000); // Check every minute
    }

    setupDecayTimer(material) {
        const materialType = this.materialTypes.get(material.type);
        if (!materialType || materialType.decayRate === 0) return;

        const decayInterval = setInterval(() => {
            this.applyMaterialDecay(material);
        }, 300000); // Apply decay every 5 minutes

        this.decayTimers.set(material.id, decayInterval);
    }

    applyMaterialDecay(material) {
        const materialType = this.materialTypes.get(material.type);
        if (!materialType) return;

        // Calculate decay amount
        let decayAmount = materialType.decayRate;

        // Storage condition modifiers
        decayAmount *= this.calculateStorageDecayModifier(material);

        // Apply decay
        material.durability = Math.max(0, material.durability - decayAmount);

        // Update quality based on durability
        if (material.durability < 100) {
            material.quality = Math.floor(material.quality * (material.durability / 100));
        }

        // Check if material is completely decayed
        if (material.durability <= 0) {
            this.removeMaterial(material.id);
        }

        // Emit decay event
        this.craftingSystem.emit('materialDecay', {
            materialId: material.id,
            durability: material.durability,
            quality: material.quality
        });
    }

    /**
     * Material Trading and Market Integration
     */
    async createMaterialListing(sellerId, materialId, quantity, price, listingType) {
        const seller = this.craftingSystem.getCrafter(sellerId);
        const material = this.materials.get(materialId);

        if (!seller || !material) {
            throw new Error('Invalid seller or material');
        }

        if (material.quantity < quantity) {
            throw new Error('Insufficient material quantity');
        }

        const listing = {
            id: this.generateListingId(),
            sellerId: sellerId,
            materialId: materialId,
            quantity: quantity,
            price: price,
            listingType: listingType, // 'auction', 'fixed_price', 'trade'
            createdAt: new Date().toISOString(),
            expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days
            status: 'active',
            bids: []
        };

        // Reserve materials
        material.quantity -= quantity;

        return listing;
    }

    async purchaseMaterial(buyerId, listingId, quantity) {
        const listing = this.getListing(listingId);
        const buyer = this.craftingSystem.getCrafter(buyerId);

        if (!listing || !buyer) {
            throw new Error('Invalid listing or buyer');
        }

        if (listing.status !== 'active') {
            throw new Error('Listing is no longer active');
        }

        if (listing.quantity < quantity) {
            throw new Error('Insufficient quantity available');
        }

        const totalPrice = listing.price * quantity;

        // Check buyer's resources
        if (buyer.resources.gold < totalPrice) {
            throw new Error('Insufficient funds');
        }

        // Process transaction
        buyer.resources.gold -= totalPrice;

        const seller = this.craftingSystem.getCrafter(listing.sellerId);
        if (seller) {
            seller.resources.gold += totalPrice;
        }

        // Transfer materials
        const material = this.materials.get(listing.materialId);
        if (material) {
            material.quantity += quantity;
        }

        // Update listing
        listing.quantity -= quantity;
        if (listing.quantity <= 0) {
            listing.status = 'completed';
        }

        return {
            success: true,
            material: material,
            quantity: quantity,
            price: totalPrice
        };
    }

    /**
     * Utility Methods
     */
    generateMaterialId() {
        return 'mat_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    generateListingId() {
        return 'list_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    generateMaterialName(materialType, location) {
        const prefixes = {
            METAL: ['Iron', 'Steel', 'Copper', 'Silver', 'Gold', 'Mithril', 'Adamantite'],
            HERB: ['Glimmering', 'Shadow', 'Sun', 'Moon', 'Star', 'Dawn', 'Dusk'],
            GEM: ['Flawed', 'Perfect', 'Brilliant', 'Radiant', 'Dark', 'Light', 'Pure'],
            WOOD: ['Oak', 'Pine', 'Mahogany', 'Ebony', 'Ironwood', 'Dreamwood', 'Spiritwood'],
            LEATHER: ['Hardened', 'Supple', 'Thick', 'Reinforced', 'Enchanted', 'Dragon', 'Demon'],
            CLOTH: ['Silk', 'Cotton', 'Wool', 'Linen', 'Velvet', 'Shadow', 'Starlight'],
            MAGICAL: ['Arcane', 'Divine', 'Infernal', 'Celestial', 'Abyssal', 'Elemental', 'Primal'],
            FOOD: ['Fresh', 'Exotic', 'Rare', 'Magical', 'Enchanted', 'Divine', 'Legendary']
        };

        const suffixes = {
            METAL: ['Ore', 'Ingot', 'Plate', 'Fragment', 'Shard', 'Nugget'],
            HERB: ['Leaf', 'Root', 'Flower', 'Stem', 'Petal', 'Seed'],
            GEM: ['Stone', 'Crystal', 'Shard', 'Fragment', 'Dust', 'Cluster'],
            WOOD: ['Log', 'Plank', 'Branch', 'Heartwood', 'Bark', 'Sapling'],
            LEATHER: ['Hide', 'Pelt', 'Scale', 'Chitin', 'Carapace'],
            CLOTH: ['Bolt', 'Spool', 'Thread', 'Yarn', 'Fabric'],
            MAGICAL: ['Essence', 'Dust', 'Shard', 'Crystal', 'Orb', 'Rune'],
            FOOD: ['Berry', 'Mushroom', 'Root', 'Fruit', 'Nut', 'Herb']
        };

        const locationPrefix = location.split('_')[0];
        const prefixList = prefixes[materialType] || ['Unknown'];
        const suffixList = suffixes[materialType] || ['Material'];

        const prefix = prefixList[Math.floor(Math.random() * prefixList.length)];
        const suffix = suffixList[Math.floor(Math.random() * suffixList.length)];

        return `${locationPrefix} ${prefix} ${suffix}`;
    }

    getMaterialRarity(materialType) {
        const rarities = {
            METAL: 1,
            HERB: 2,
            GEM: 4,
            WOOD: 1,
            LEATHER: 2,
            CLOTH: 1,
            MAGICAL: 5,
            FOOD: 1
        };
        return rarities[materialType] || 1;
    }

    calculateMaterialValue(materialData) {
        let baseValue = 10;

        // Quality influence
        baseValue += materialData.quality * 2;

        // Type rarity
        baseValue *= this.getMaterialRarity(materialData.type);

        // Special effects
        if (materialData.specialEffects) {
            baseValue += materialData.specialEffects.length * 50;
        }

        return Math.floor(baseValue);
    }

    getDefaultStackSize(materialType) {
        const stackSizes = {
            METAL: 99,
            HERB: 50,
            GEM: 20,
            WOOD: 50,
            LEATHER: 25,
            CLOTH: 99,
            MAGICAL: 10,
            FOOD: 20
        };
        return stackSizes[materialType] || 50;
    }

    getStorageRequirements(materialType) {
        const type = this.materialTypes.get(materialType);
        return type ? type.storageRequirements : ['dry'];
    }

    isProcessable(materialType) {
        const type = this.materialTypes.get(materialType);
        return type ? type.processable : false;
    }

    removeMaterial(materialId) {
        const material = this.materials.get(materialId);
        if (material) {
            // Clear decay timer
            const timer = this.decayTimers.get(materialId);
            if (timer) {
                clearInterval(timer);
                this.decayTimers.delete(materialId);
            }

            // Remove material
            this.materials.delete(materialId);

            // Emit removal event
            this.craftingSystem.emit('materialRemoved', { materialId: materialId });
        }
    }

    // Additional methods for specific mechanics
    calculateHarvestingExperience(zone, materialType, quantity) {
        const baseExp = 10;
        const zoneBonus = zone.difficultyModifier || 0;
        const rarityBonus = this.getMaterialRarity(materialType) * 5;

        return Math.floor((baseExp + zoneBonus + rarityBonus) * quantity);
    }

    updateHarvestingStats(harvester, materialType, quantity) {
        harvester.stats = harvester.stats || {};
        harvester.stats.harvesting = harvester.stats.harvesting || {};
        harvester.stats.harvesting[materialType] = (harvester.stats.harvesting[materialType] || 0) + quantity;
        harvester.stats.totalHarvested = (harvester.stats.totalHarvested || 0) + quantity;
    }
}

module.exports = MaterialSystem;